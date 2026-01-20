"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def mock_jira_credentials():
    """Mock Jira credentials for testing."""
    with patch("shared.auth.token.get_credential") as mock_get:

        def side_effect(key: str) -> str | None:
            credentials = {
                "jira-url": "https://test.atlassian.net",
                "jira-email": "test@example.com",
                "jira-token": "test-token",
            }
            return credentials.get(key)

        mock_get.side_effect = side_effect
        yield mock_get


@pytest.fixture
def mock_github_credentials():
    """Mock GitHub credentials for testing."""
    with patch("shared.auth.token.get_credential") as mock_get:

        def side_effect(key: str) -> str | None:
            credentials = {
                "github-url": "https://api.github.com",
                "github-token": "test-token",
            }
            return credentials.get(key)

        mock_get.side_effect = side_effect
        yield mock_get


@pytest.fixture
def sample_jira_issue():
    """Sample Jira issue response."""
    return {
        "key": "DEMO-123",
        "id": "12345",
        "self": "https://test.atlassian.net/rest/api/3/issue/12345",
        "fields": {
            "summary": "Test issue summary",
            "status": {"name": "Open", "id": "1"},
            "assignee": {
                "accountId": "user123",
                "displayName": "Test User",
                "emailAddress": "test@example.com",
            },
            "priority": {"name": "Medium", "id": "3"},
            "created": "2024-01-15T10:00:00.000+0000",
            "updated": "2024-01-15T12:00:00.000+0000",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Test description"}],
                    }
                ],
            },
        },
    }


@pytest.fixture
def sample_jira_search_response(sample_jira_issue):
    """Sample Jira search response."""
    return {
        "expand": "names,schema",
        "startAt": 0,
        "maxResults": 50,
        "total": 1,
        "issues": [sample_jira_issue],
    }


@pytest.fixture
def sample_jira_transitions():
    """Sample Jira transitions response."""
    return {
        "transitions": [
            {
                "id": "11",
                "name": "In Progress",
                "to": {"id": "3", "name": "In Progress"},
            },
            {
                "id": "21",
                "name": "Done",
                "to": {"id": "4", "name": "Done"},
            },
            {
                "id": "31",
                "name": "Reopen",
                "to": {"id": "1", "name": "Open"},
            },
        ]
    }
