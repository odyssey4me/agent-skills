"""Tests for Jira API detection module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import responses

from skills.jira.api import (
    JiraDetectionError,
    api_path,
    clear_cache,
    detect_deployment_type,
    format_rich_text,
    get_api_version,
    is_cloud,
)


@pytest.fixture
def mock_jira_creds():
    """Mock Jira credentials."""
    with patch("skills.jira.api.get_credentials") as mock:
        creds = MagicMock()
        creds.url = "https://test.atlassian.net"
        creds.email = "test@example.com"
        creds.token = "test-token"
        creds.username = None
        creds.password = None
        mock.return_value = creds
        yield creds


@pytest.fixture(autouse=True)
def clear_detection_cache():
    """Clear the detection cache before each test."""
    clear_cache()
    yield
    clear_cache()


class TestDetectDeploymentType:
    """Tests for detect_deployment_type function."""

    @responses.activate
    def test_detect_cloud(self, mock_jira_creds):
        """Test detection of Jira Cloud."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={
                "baseUrl": "https://test.atlassian.net",
                "version": "1001.0.0",
                "deploymentType": "Cloud",
                "scmInfo": "N/A",
            },
            status=200,
        )

        result = detect_deployment_type()

        assert result == "Cloud"
        assert len(responses.calls) == 1

    @responses.activate
    def test_detect_datacenter(self, mock_jira_creds):
        """Test detection of Jira Data Center."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={
                "baseUrl": "https://jira.company.com",
                "version": "9.4.0",
                "deploymentType": "DataCenter",
                "serverTitle": "Jira",
            },
            status=200,
        )

        result = detect_deployment_type()

        assert result == "DataCenter"

    @responses.activate
    def test_detect_server(self, mock_jira_creds):
        """Test detection of Jira Server (legacy)."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={
                "baseUrl": "https://jira.company.com",
                "version": "8.22.0",
                "deploymentType": "Server",
            },
            status=200,
        )

        result = detect_deployment_type()

        assert result == "Server"

    @responses.activate
    def test_caching_prevents_repeated_requests(self, mock_jira_creds):
        """Test that detection results are cached."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        # First call should make a request
        result1 = detect_deployment_type()
        assert len(responses.calls) == 1

        # Second call should use cache
        result2 = detect_deployment_type()
        assert len(responses.calls) == 1  # Still only 1 request
        assert result1 == result2

    @responses.activate
    def test_force_refresh_bypasses_cache(self, mock_jira_creds):
        """Test that force_refresh bypasses the cache."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "DataCenter"},
            status=200,
        )

        result1 = detect_deployment_type()
        assert result1 == "Cloud"
        assert len(responses.calls) == 1

        result2 = detect_deployment_type(force_refresh=True)
        assert result2 == "DataCenter"
        assert len(responses.calls) == 2

    @responses.activate
    def test_rate_limit_retry(self, mock_jira_creds):
        """Test retry logic on rate limit (429)."""
        # First request returns 429, second succeeds
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            status=429,
            headers={"Retry-After": "0.1"},
        )
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        result = detect_deployment_type()

        assert result == "Cloud"
        assert len(responses.calls) == 2

    def test_no_url_configured(self):
        """Test error when no URL is configured."""
        with patch("skills.jira.api.get_credentials") as mock:
            creds = MagicMock()
            creds.url = None
            mock.return_value = creds

            with pytest.raises(JiraDetectionError) as exc_info:
                detect_deployment_type()

            assert "No Jira URL configured" in str(exc_info.value)


class TestGetApiVersion:
    """Tests for get_api_version function."""

    @responses.activate
    def test_version_3_for_cloud(self, mock_jira_creds):
        """Test that Cloud returns API version 3."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        version = get_api_version()

        assert version == "3"

    @responses.activate
    def test_version_2_for_datacenter(self, mock_jira_creds):
        """Test that Data Center returns API version 2."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "DataCenter"},
            status=200,
        )

        version = get_api_version()

        assert version == "2"

    @responses.activate
    def test_version_2_for_server(self, mock_jira_creds):
        """Test that Server returns API version 2."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Server"},
            status=200,
        )

        version = get_api_version()

        assert version == "2"


class TestApiPath:
    """Tests for api_path function."""

    @responses.activate
    def test_api_path_cloud(self, mock_jira_creds):
        """Test API path construction for Cloud."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        path = api_path("search")

        assert path == "rest/api/3/search"

    @responses.activate
    def test_api_path_datacenter(self, mock_jira_creds):
        """Test API path construction for Data Center."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "DataCenter"},
            status=200,
        )

        path = api_path("search")

        assert path == "rest/api/2/search"

    @responses.activate
    def test_api_path_with_nested_endpoint(self, mock_jira_creds):
        """Test API path with nested endpoint."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        path = api_path("issue/DEMO-123/comment")

        assert path == "rest/api/3/issue/DEMO-123/comment"

    @responses.activate
    def test_api_path_strips_leading_slash(self, mock_jira_creds):
        """Test that leading slash is handled correctly."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        path = api_path("/search")

        assert path == "rest/api/3/search"


class TestFormatRichText:
    """Tests for format_rich_text function."""

    @responses.activate
    def test_format_rich_text_cloud_returns_adf(self, mock_jira_creds):
        """Test that Cloud returns ADF format."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        result = format_rich_text("Hello world")

        assert isinstance(result, dict)
        assert result["type"] == "doc"
        assert result["version"] == 1
        assert result["content"][0]["type"] == "paragraph"
        assert result["content"][0]["content"][0]["text"] == "Hello world"

    @responses.activate
    def test_format_rich_text_datacenter_returns_string(self, mock_jira_creds):
        """Test that Data Center returns plain string."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "DataCenter"},
            status=200,
        )

        result = format_rich_text("Hello world")

        assert isinstance(result, str)
        assert result == "Hello world"

    @responses.activate
    def test_format_rich_text_server_returns_string(self, mock_jira_creds):
        """Test that Server returns plain string."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Server"},
            status=200,
        )

        result = format_rich_text("Hello world")

        assert isinstance(result, str)
        assert result == "Hello world"


class TestIsCloud:
    """Tests for is_cloud function."""

    @responses.activate
    def test_is_cloud_true(self, mock_jira_creds):
        """Test is_cloud returns True for Cloud."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )

        assert is_cloud() is True

    @responses.activate
    def test_is_cloud_false_for_datacenter(self, mock_jira_creds):
        """Test is_cloud returns False for Data Center."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "DataCenter"},
            status=200,
        )

        assert is_cloud() is False

    def test_is_cloud_false_on_error(self):
        """Test is_cloud returns False on detection error."""
        with patch("skills.jira.api.get_credentials") as mock:
            creds = MagicMock()
            creds.url = None
            mock.return_value = creds

            assert is_cloud() is False


class TestClearCache:
    """Tests for clear_cache function."""

    @responses.activate
    def test_clear_cache_allows_new_detection(self, mock_jira_creds):
        """Test that clearing cache allows new detection."""
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "Cloud"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/2/serverInfo",
            json={"deploymentType": "DataCenter"},
            status=200,
        )

        result1 = detect_deployment_type()
        assert result1 == "Cloud"
        assert len(responses.calls) == 1

        clear_cache()

        result2 = detect_deployment_type()
        assert result2 == "DataCenter"
        assert len(responses.calls) == 2
