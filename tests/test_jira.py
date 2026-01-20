"""Tests for Jira skill scripts."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import responses

from skills.jira.api import clear_cache
from skills.jira.scripts.issue import (
    add_comment,
    create_issue,
    get_issue,
    update_issue,
)
from skills.jira.scripts.search import search_issues
from skills.jira.scripts.transitions import do_transition, get_transitions


@pytest.fixture(autouse=True)
def _clear_api_cache():
    """Clear the API detection cache before and after each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def _mock_jira_auth():
    """Mock Jira authentication."""
    with patch("shared.http.get_credentials") as http_mock, \
         patch("skills.jira.api.get_credentials") as api_mock:
        creds = MagicMock()
        creds.url = "https://test.atlassian.net"
        creds.email = "test@example.com"
        creds.token = "test-token"
        creds.username = None
        creds.password = None
        creds.is_valid.return_value = True
        http_mock.return_value = creds
        api_mock.return_value = creds
        yield creds


@pytest.fixture
def _mock_cloud_detection():
    """Mock serverInfo endpoint for Cloud detection."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/rest/api/2/serverInfo",
        json={"deploymentType": "Cloud"},
        status=200,
    )


class TestSearchIssues:
    """Tests for search_issues function."""

    @responses.activate
    def test_search_issues_basic(self, _mock_jira_auth, _mock_cloud_detection, sample_jira_search_response):
        """Test basic issue search."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/search",
            json=sample_jira_search_response,
            status=200,
        )

        issues = search_issues("project = DEMO")

        assert len(issues) == 1
        assert issues[0]["key"] == "DEMO-123"

    @responses.activate
    def test_search_issues_with_max_results(self, _mock_jira_auth, _mock_cloud_detection):
        """Test search with max results parameter."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/search",
            json={"issues": []},
            status=200,
        )

        search_issues("project = DEMO", max_results=10)

        # Second call is the search (first is serverInfo)
        assert "maxResults=10" in responses.calls[1].request.url

    @responses.activate
    def test_search_issues_with_fields(self, _mock_jira_auth, _mock_cloud_detection):
        """Test search with custom fields."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/search",
            json={"issues": []},
            status=200,
        )

        search_issues("project = DEMO", fields=["summary", "status"])

        # Second call is the search (first is serverInfo)
        assert "fields=summary%2Cstatus" in responses.calls[1].request.url


class TestGetIssue:
    """Tests for get_issue function."""

    @responses.activate
    def test_get_issue_success(self, _mock_jira_auth, _mock_cloud_detection, sample_jira_issue):
        """Test getting an issue."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123",
            json=sample_jira_issue,
            status=200,
        )

        issue = get_issue("DEMO-123")

        assert issue["key"] == "DEMO-123"
        assert issue["fields"]["summary"] == "Test issue summary"


class TestCreateIssue:
    """Tests for create_issue function."""

    @responses.activate
    def test_create_issue_basic(self, _mock_jira_auth, _mock_cloud_detection):
        """Test creating a basic issue."""
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/issue",
            json={"id": "12345", "key": "DEMO-124", "self": "..."},
            status=201,
        )

        result = create_issue(
            project="DEMO",
            issue_type="Task",
            summary="New task",
        )

        assert result["key"] == "DEMO-124"

        # Second call is the create (first is serverInfo)
        request_body = responses.calls[1].request.body
        assert b"DEMO" in request_body
        assert b"Task" in request_body
        assert b"New task" in request_body

    @responses.activate
    def test_create_issue_with_description(self, _mock_jira_auth, _mock_cloud_detection):
        """Test creating an issue with description."""
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/issue",
            json={"id": "12345", "key": "DEMO-124"},
            status=201,
        )

        create_issue(
            project="DEMO",
            issue_type="Bug",
            summary="Bug report",
            description="Detailed description",
        )

        # Second call is the create (first is serverInfo)
        request_body = responses.calls[1].request.body
        assert b"Detailed description" in request_body


class TestUpdateIssue:
    """Tests for update_issue function."""

    @responses.activate
    def test_update_issue_summary(self, _mock_jira_auth, _mock_cloud_detection):
        """Test updating issue summary."""
        responses.add(
            responses.PUT,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123",
            body="",
            status=204,
        )

        update_issue("DEMO-123", summary="Updated summary")

        # Second call is the update (first is serverInfo)
        request_body = responses.calls[1].request.body
        assert b"Updated summary" in request_body

    def test_update_issue_no_changes(self, _mock_jira_auth):
        """Test update with no changes."""
        result = update_issue("DEMO-123")
        assert result == {}


class TestAddComment:
    """Tests for add_comment function."""

    @responses.activate
    def test_add_comment_success(self, _mock_jira_auth, _mock_cloud_detection):
        """Test adding a comment."""
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123/comment",
            json={"id": "10000", "body": {}},
            status=201,
        )

        result = add_comment("DEMO-123", "This is a comment")

        assert result["id"] == "10000"
        # Second call is the comment (first is serverInfo)
        request_body = responses.calls[1].request.body
        assert b"This is a comment" in request_body


class TestGetTransitions:
    """Tests for get_transitions function."""

    @responses.activate
    def test_get_transitions_success(self, _mock_jira_auth, _mock_cloud_detection, sample_jira_transitions):
        """Test getting available transitions."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123/transitions",
            json=sample_jira_transitions,
            status=200,
        )

        transitions = get_transitions("DEMO-123")

        assert len(transitions) == 3
        assert transitions[0]["name"] == "In Progress"


class TestDoTransition:
    """Tests for do_transition function."""

    @responses.activate
    def test_do_transition_success(self, _mock_jira_auth, _mock_cloud_detection, sample_jira_transitions):
        """Test performing a transition."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123/transitions",
            json=sample_jira_transitions,
            status=200,
        )
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123/transitions",
            body="",
            status=204,
        )

        do_transition("DEMO-123", "In Progress")

        # Third call is the POST (first is serverInfo, second is GET transitions)
        request_body = responses.calls[2].request.body
        assert b'"id": "11"' in request_body

    @responses.activate
    def test_do_transition_with_comment(self, _mock_jira_auth, _mock_cloud_detection, sample_jira_transitions):
        """Test transition with comment."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123/transitions",
            json=sample_jira_transitions,
            status=200,
        )
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123/transitions",
            body="",
            status=204,
        )

        do_transition("DEMO-123", "Done", comment="Completed!")

        # Third call is the POST (first is serverInfo, second is GET transitions)
        request_body = responses.calls[2].request.body
        assert b"Completed!" in request_body

    @responses.activate
    def test_do_transition_not_available(self, _mock_jira_auth, _mock_cloud_detection, sample_jira_transitions):
        """Test transition that's not available."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/DEMO-123/transitions",
            json=sample_jira_transitions,
            status=200,
        )

        with pytest.raises(ValueError) as exc_info:
            do_transition("DEMO-123", "Invalid Transition")

        assert "Invalid Transition" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)
