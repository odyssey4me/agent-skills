"""Tests for jira.py skill."""

from __future__ import annotations

import argparse
from unittest.mock import Mock, patch

import pytest

# Import from skills module
from skills.jira.scripts.jira import (
    APIError,
    Credentials,
    JiraDefaults,
    JiraDetectionError,
    ProjectDefaults,
    _deployment_cache,
    _make_detection_request,
    _truncate,
    add_comment,
    api_path,
    clear_cache,
    cmd_check,
    cmd_config,
    cmd_issue,
    cmd_search,
    cmd_transitions,
    create_issue,
    delete_credential,
    detect_deployment_type,
    do_transition,
    format_issue,
    format_issues_list,
    format_json,
    format_rich_text,
    format_table,
    get_api_version,
    get_credential,
    get_credentials,
    get_issue,
    get_jira_defaults,
    get_project_defaults,
    get_transitions,
    is_cloud,
    load_config,
    save_config,
    search_issues,
    set_credential,
    update_issue,
)


class TestCredentials:
    """Tests for Credentials dataclass."""

    def test_is_valid_with_token(self):
        """Test is_valid with token authentication."""
        creds = Credentials(url="https://example.atlassian.net", token="token123")
        assert creds.is_valid()

    def test_is_valid_with_username_password(self):
        """Test is_valid with username/password authentication."""
        creds = Credentials(
            url="https://example.atlassian.net",
            username="user",
            password="pass",
        )
        assert creds.is_valid()

    def test_is_valid_missing_url(self):
        """Test is_valid fails without URL."""
        creds = Credentials(token="token123")
        assert not creds.is_valid()

    def test_is_valid_missing_token_and_password(self):
        """Test is_valid fails without token or password."""
        creds = Credentials(url="https://example.atlassian.net", username="user")
        assert not creds.is_valid()


class TestKeyringFunctions:
    """Tests for keyring functions."""

    @patch("skills.jira.scripts.jira.keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch("skills.jira.scripts.jira.keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch("skills.jira.scripts.jira.keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")


class TestConfigManagement:
    """Tests for config file management."""

    def test_load_config_nonexistent(self, tmp_path, monkeypatch):
        """Test loading config when file doesn't exist."""
        monkeypatch.setattr("skills.jira.scripts.jira.CONFIG_DIR", tmp_path / "nonexistent")
        config = load_config("jira")
        assert config is None

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        config_dir = tmp_path / "config"
        monkeypatch.setattr("skills.jira.scripts.jira.CONFIG_DIR", config_dir)

        test_config = {
            "url": "https://example.atlassian.net",
            "email": "test@example.com",
            "token": "secret",
        }

        save_config("jira", test_config)
        loaded = load_config("jira")

        assert loaded == test_config


class TestGetCredentials:
    """Tests for get_credentials function."""

    @patch("skills.jira.scripts.jira.get_credential")
    @patch("skills.jira.scripts.jira.load_config")
    def test_get_credentials_from_keyring(self, mock_load_config, mock_get_credential):
        """Test getting credentials from keyring."""
        mock_get_credential.side_effect = lambda key: {
            "jira-url": "https://keyring.atlassian.net",
            "jira-email": "keyring@example.com",
            "jira-token": "keyring-token",
        }.get(key)
        mock_load_config.return_value = None

        creds = get_credentials("jira")

        assert creds.url == "https://keyring.atlassian.net"
        assert creds.email == "keyring@example.com"
        assert creds.token == "keyring-token"

    @patch("skills.jira.scripts.jira.get_credential")
    @patch("skills.jira.scripts.jira.load_config")
    def test_get_credentials_from_env(self, mock_load_config, mock_get_credential, monkeypatch):
        """Test getting credentials from environment variables."""
        mock_get_credential.return_value = None
        mock_load_config.return_value = None

        monkeypatch.setenv("JIRA_BASE_URL", "https://env.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "env@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "env-token")

        creds = get_credentials("jira")

        assert creds.url == "https://env.atlassian.net"
        assert creds.email == "env@example.com"
        assert creds.token == "env-token"

    @patch("skills.jira.scripts.jira.get_credential")
    @patch("skills.jira.scripts.jira.load_config")
    def test_get_credentials_from_config(self, mock_load_config, mock_get_credential, monkeypatch):
        """Test getting credentials from config file."""
        # Clear environment variables
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)
        monkeypatch.delenv("JIRA_URL", raising=False)
        monkeypatch.delenv("JIRA_EMAIL", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.delenv("JIRA_TOKEN", raising=False)

        mock_get_credential.return_value = None
        mock_load_config.return_value = {
            "url": "https://config.atlassian.net",
            "email": "config@example.com",
            "token": "config-token",
        }

        creds = get_credentials("jira")

        assert creds.url == "https://config.atlassian.net"
        assert creds.email == "config@example.com"
        assert creds.token == "config-token"


class TestDefaultsManagement:
    """Tests for JiraDefaults and ProjectDefaults."""

    def test_get_jira_defaults_no_config(self, monkeypatch):
        """Test getting defaults when no config exists."""
        monkeypatch.setattr("skills.jira.scripts.jira.load_config", lambda _service: None)
        defaults = get_jira_defaults()

        assert defaults.jql_scope is None
        assert defaults.security_level is None
        assert defaults.max_results is None
        assert defaults.fields is None

    @patch("skills.jira.scripts.jira.load_config")
    def test_get_jira_defaults_with_config(self, mock_load_config):
        """Test getting defaults from config."""
        mock_load_config.return_value = {
            "defaults": {
                "jql_scope": "project = DEMO",
                "security_level": "Red Hat Internal",
                "max_results": 100,
                "fields": ["summary", "status"],
            }
        }

        defaults = get_jira_defaults()

        assert defaults.jql_scope == "project = DEMO"
        assert defaults.security_level == "Red Hat Internal"
        assert defaults.max_results == 100
        assert defaults.fields == ["summary", "status"]

    @patch("skills.jira.scripts.jira.load_config")
    def test_get_project_defaults(self, mock_load_config):
        """Test getting project-specific defaults."""
        mock_load_config.return_value = {
            "projects": {
                "DEMO": {
                    "issue_type": "Task",
                    "priority": "High",
                }
            }
        }

        defaults = get_project_defaults("DEMO")

        assert defaults.issue_type == "Task"
        assert defaults.priority == "High"


class TestDeploymentDetection:
    """Tests for deployment type detection."""

    def test_detect_deployment_type_cloud(self):
        """Test detecting Cloud deployment."""
        with patch("skills.jira.scripts.jira._make_detection_request") as mock_request:
            mock_request.return_value = {"deploymentType": "Cloud"}

            with patch("skills.jira.scripts.jira.get_credentials") as mock_creds:
                mock_creds.return_value = Credentials(
                    url="https://example.atlassian.net",
                    email="test@example.com",
                    token="token",
                )

                clear_cache()
                deployment_type = detect_deployment_type()

                assert deployment_type == "Cloud"
                assert _deployment_cache["https://example.atlassian.net"] == {
                    "deployment_type": "Cloud",
                    "api_version": "3",
                }

    def test_detect_deployment_type_server(self):
        """Test detecting Server deployment."""
        with patch("skills.jira.scripts.jira._make_detection_request") as mock_request:
            mock_request.return_value = {"deploymentType": "Server"}

            with patch("skills.jira.scripts.jira.get_credentials") as mock_creds:
                mock_creds.return_value = Credentials(
                    url="https://jira.example.com",
                    username="user",
                    password="pass",
                )

                clear_cache()
                deployment_type = detect_deployment_type()

                assert deployment_type == "Server"
                assert _deployment_cache["https://jira.example.com"] == {
                    "deployment_type": "Server",
                    "api_version": "2",
                }

    def test_detect_deployment_type_no_url(self):
        """Test detection fails when no URL configured."""
        with patch("skills.jira.scripts.jira.get_credentials") as mock_creds:
            mock_creds.return_value = Credentials()

            clear_cache()

            with pytest.raises(JiraDetectionError, match="No Jira URL configured"):
                detect_deployment_type()

    def test_get_api_version_cloud(self):
        """Test getting API version for Cloud."""
        with patch("skills.jira.scripts.jira.detect_deployment_type") as mock_detect:
            mock_detect.return_value = "Cloud"

            with patch("skills.jira.scripts.jira.get_credentials") as mock_creds:
                mock_creds.return_value = Credentials(url="https://example.atlassian.net")

                clear_cache()
                _deployment_cache["https://example.atlassian.net"] = {
                    "deployment_type": "Cloud",
                    "api_version": "3",
                }

                version = get_api_version()
                assert version == "3"

    def test_is_cloud(self):
        """Test is_cloud helper."""
        with patch("skills.jira.scripts.jira.detect_deployment_type") as mock_detect:
            mock_detect.return_value = "Cloud"
            assert is_cloud() is True

            mock_detect.return_value = "Server"
            clear_cache()
            assert is_cloud() is False

    def test_clear_cache(self):
        """Test clearing deployment cache."""
        _deployment_cache["https://example.com"] = {"deployment_type": "Cloud"}
        clear_cache()
        assert len(_deployment_cache) == 0


class TestApiHelpers:
    """Tests for API helper functions."""

    def test_api_path(self):
        """Test API path construction."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            assert api_path("search") == "rest/api/3/search"
            assert api_path("/issue/DEMO-123") == "rest/api/3/issue/DEMO-123"

    def test_format_rich_text_cloud(self):
        """Test formatting rich text for Cloud (ADF)."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("Hello world")

            assert result["type"] == "doc"
            assert result["version"] == 1
            assert result["content"][0]["type"] == "paragraph"
            assert result["content"][0]["content"][0]["text"] == "Hello world"

    def test_format_rich_text_server(self):
        """Test formatting rich text for Server (plain text)."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "2"
            result = format_rich_text("Hello world")

            assert result == "Hello world"


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_json(self):
        """Test JSON formatting."""
        data = {"key": "value", "number": 42}
        result = format_json(data)
        assert '"key": "value"' in result
        assert '"number": 42' in result

    def test_truncate(self):
        """Test text truncation."""
        assert _truncate("short", 10) == "short"
        assert _truncate("this is a long text", 10) == "this is..."

    def test_format_table(self):
        """Test table formatting."""
        rows = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = format_table(
            rows,
            ["name", "age"],
            headers={"name": "Name", "age": "Age"},
        )

        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_format_table_empty(self):
        """Test formatting empty table."""
        result = format_table([], ["col1", "col2"])
        assert result == "No data"

    def test_format_issue(self):
        """Test issue formatting."""
        issue = {
            "key": "DEMO-123",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "Open"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "High"},
            },
        }

        result = format_issue(issue)

        assert "DEMO-123" in result
        assert "Test issue" in result
        assert "Open" in result
        assert "Alice" in result
        assert "High" in result

    def test_format_issues_list(self):
        """Test formatting issue list."""
        issues = [
            {
                "key": "DEMO-1",
                "fields": {
                    "summary": "First",
                    "status": {"name": "Open"},
                    "assignee": {"displayName": "Alice"},
                },
            },
            {
                "key": "DEMO-2",
                "fields": {
                    "summary": "Second",
                    "status": {"name": "Closed"},
                    "assignee": None,
                },
            },
        ]

        result = format_issues_list(issues)

        assert "DEMO-1" in result
        assert "DEMO-2" in result
        assert "First" in result
        assert "Second" in result
        assert "Unassigned" in result

    def test_format_issues_list_empty(self):
        """Test formatting empty issue list."""
        result = format_issues_list([])
        assert result == "No issues found"


class TestApiOperations:
    """Tests for API operations."""

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues(self, mock_api_path, mock_get, mock_scriptrunner):
        """Test searching issues."""
        mock_api_path.return_value = "rest/api/3/search"
        mock_get.return_value = {
            "issues": [
                {"key": "DEMO-1", "fields": {"summary": "Test"}},
            ]
        }
        mock_scriptrunner.return_value = {"available": False}

        result = search_issues("project = DEMO", max_results=10)

        assert len(result) == 1
        assert result[0]["key"] == "DEMO-1"

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_get_issue(self, mock_api_path, mock_get):
        """Test getting a single issue."""
        mock_api_path.return_value = "rest/api/3/issue/DEMO-123"
        mock_get.return_value = {
            "key": "DEMO-123",
            "fields": {"summary": "Test issue"},
        }

        result = get_issue("DEMO-123")

        assert result["key"] == "DEMO-123"
        assert result["fields"]["summary"] == "Test issue"

    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.format_rich_text")
    def test_create_issue(self, mock_format_text, mock_api_path, mock_post):
        """Test creating an issue."""
        mock_api_path.return_value = "rest/api/3/issue"
        mock_format_text.return_value = {"type": "doc"}
        mock_post.return_value = {"key": "DEMO-123"}

        result = create_issue(
            project="DEMO",
            issue_type="Task",
            summary="New task",
            description="Description here",
            priority="High",
        )

        assert result["key"] == "DEMO-123"

    @patch("skills.jira.scripts.jira.put")
    @patch("skills.jira.scripts.jira.api_path")
    def test_update_issue(self, mock_api_path, mock_put):
        """Test updating an issue."""
        mock_api_path.return_value = "rest/api/3/issue/DEMO-123"
        mock_put.return_value = {}

        result = update_issue("DEMO-123", summary="Updated summary")

        assert result == {}

    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.format_rich_text")
    def test_add_comment(self, mock_format_text, mock_api_path, mock_post):
        """Test adding a comment."""
        mock_api_path.return_value = "rest/api/3/issue/DEMO-123/comment"
        mock_format_text.return_value = {"type": "doc"}
        mock_post.return_value = {"id": "12345"}

        result = add_comment("DEMO-123", "Test comment")

        assert result["id"] == "12345"

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_get_transitions(self, mock_api_path, mock_get):
        """Test getting transitions."""
        mock_api_path.return_value = "rest/api/3/issue/DEMO-123/transitions"
        mock_get.return_value = {
            "transitions": [
                {"id": "1", "name": "In Progress", "to": {"name": "In Progress"}},
            ]
        }

        result = get_transitions("DEMO-123")

        assert len(result) == 1
        assert result[0]["name"] == "In Progress"

    @patch("skills.jira.scripts.jira.get_transitions")
    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    def test_do_transition(self, mock_api_path, mock_post, mock_get_transitions):
        """Test performing a transition."""
        mock_api_path.return_value = "rest/api/3/issue/DEMO-123/transitions"
        mock_get_transitions.return_value = [
            {"id": "11", "name": "In Progress"},
            {"id": "21", "name": "Done"},
        ]
        mock_post.return_value = {}

        result = do_transition("DEMO-123", "Done")

        assert result == {}

    @patch("skills.jira.scripts.jira.get_transitions")
    def test_do_transition_invalid(self, mock_get_transitions):
        """Test transition with invalid name."""
        mock_get_transitions.return_value = [
            {"id": "11", "name": "In Progress"},
        ]

        with pytest.raises(ValueError, match="not available"):
            do_transition("DEMO-123", "NonExistent")


class TestHttpRequests:
    """Tests for HTTP request functions."""

    @patch("skills.jira.scripts.jira.requests.get")
    @patch("skills.jira.scripts.jira.get_credentials")
    def test_make_detection_request_success(self, mock_creds, mock_get):
        """Test successful detection request."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="token",
            email="test@example.com",
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"deploymentType": "Cloud"}
        mock_get.return_value = mock_response

        result = _make_detection_request(
            "https://example.atlassian.net",
            "rest/api/2/serverInfo",
            email="test@example.com",
            token="token",
        )

        assert result["deploymentType"] == "Cloud"

    @patch("skills.jira.scripts.jira.requests.get")
    @patch("skills.jira.scripts.jira.time.sleep")
    def test_make_detection_request_rate_limit(self, mock_sleep, mock_get):
        """Test detection request with rate limiting."""
        # First two attempts return 429, third succeeds
        response_429 = Mock()
        response_429.status_code = 429
        response_429.ok = False
        response_429.headers = {"Retry-After": "1"}

        response_ok = Mock()
        response_ok.ok = True
        response_ok.status_code = 200
        response_ok.json.return_value = {"deploymentType": "Cloud"}

        mock_get.side_effect = [response_429, response_429, response_ok]

        result = _make_detection_request(
            "https://example.atlassian.net",
            "rest/api/2/serverInfo",
        )

        assert result["deploymentType"] == "Cloud"
        assert mock_sleep.call_count == 2

    @patch("skills.jira.scripts.jira.requests.get")
    @patch("skills.jira.scripts.jira.time.sleep")
    def test_make_detection_request_failure(self, _mock_sleep, mock_get):
        """Test detection request failure."""
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(JiraDetectionError, match="Request failed"):
            _make_detection_request(
                "https://example.atlassian.net",
                "rest/api/2/serverInfo",
            )

    @patch("skills.jira.scripts.jira.requests.request")
    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_make_request_cloud(self, mock_is_cloud, mock_creds, mock_request):
        """Test making a request to Cloud."""
        from skills.jira.scripts.jira import make_request

        mock_is_cloud.return_value = True
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            email="test@example.com",
            token="token",
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        result = make_request("jira", "GET", "rest/api/3/search")

        assert result["result"] == "success"

    @patch("skills.jira.scripts.jira.requests.request")
    @patch("skills.jira.scripts.jira.get_credentials")
    def test_make_request_invalid_credentials(self, mock_creds, _mock_request):
        """Test making a request with invalid credentials."""
        from skills.jira.scripts.jira import make_request

        mock_creds.return_value = Credentials(url="https://example.com")

        with pytest.raises(APIError, match="No valid credentials"):
            make_request("jira", "GET", "rest/api/3/search")

    @patch("skills.jira.scripts.jira.requests.request")
    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_make_request_error(self, mock_is_cloud, mock_creds, mock_request):
        """Test making a request that fails."""
        from skills.jira.scripts.jira import make_request

        mock_is_cloud.return_value = False
        mock_creds.return_value = Credentials(
            url="https://example.com",
            token="token",
        )
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_request.return_value = mock_response

        with pytest.raises(APIError, match="failed: 404 Not Found"):
            make_request("jira", "GET", "rest/api/2/issue/MISSING")

    @patch("skills.jira.scripts.jira.requests.request")
    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_make_request_204_no_content(self, mock_is_cloud, mock_creds, mock_request):
        """Test making a request that returns 204 No Content."""
        from skills.jira.scripts.jira import make_request

        mock_is_cloud.return_value = True
        mock_creds.return_value = Credentials(
            url="https://example.com",
            email="test@example.com",
            token="token",
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        result = make_request("jira", "DELETE", "rest/api/3/issue/DEMO-123")

        assert result == {}

    @patch("skills.jira.scripts.jira.make_request")
    def test_get_wrapper(self, mock_make_request):
        """Test get wrapper function."""
        from skills.jira.scripts.jira import get

        mock_make_request.return_value = {"result": "success"}

        result = get("jira", "rest/api/3/search")

        assert result["result"] == "success"
        mock_make_request.assert_called_once_with("jira", "GET", "rest/api/3/search")

    @patch("skills.jira.scripts.jira.make_request")
    def test_post_wrapper(self, mock_make_request):
        """Test post wrapper function."""
        from skills.jira.scripts.jira import post

        mock_make_request.return_value = {"key": "DEMO-123"}

        result = post("jira", "rest/api/3/issue", {"fields": {}})

        assert result["key"] == "DEMO-123"

    @patch("skills.jira.scripts.jira.make_request")
    def test_put_wrapper(self, mock_make_request):
        """Test put wrapper function."""
        from skills.jira.scripts.jira import put

        mock_make_request.return_value = {}

        result = put("jira", "rest/api/3/issue/DEMO-123", {"fields": {}})

        assert result == {}

    @patch("skills.jira.scripts.jira.make_request")
    def test_delete_wrapper(self, mock_make_request):
        """Test delete wrapper function."""
        from skills.jira.scripts.jira import delete

        mock_make_request.return_value = {}

        result = delete("jira", "rest/api/3/issue/DEMO-123")

        assert result == {}


class TestCommandHandlers:
    """Tests for command handlers."""

    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.detect_deployment_type")
    @patch("skills.jira.scripts.jira.get_api_version")
    @patch("skills.jira.scripts.jira.get")
    def test_cmd_check_success(self, mock_get, mock_api_version, mock_detect, mock_creds, capsys):
        """Test check command success."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            email="test@example.com",
            token="secret",
        )
        mock_detect.return_value = "Cloud"
        mock_api_version.return_value = "3"
        mock_get.return_value = {"issues": []}

        result = cmd_check()

        assert result == 0
        captured = capsys.readouterr()
        assert "All checks passed" in captured.out

    @patch("skills.jira.scripts.jira.get_credentials")
    def test_cmd_check_no_url(self, mock_creds, capsys):
        """Test check command with no URL."""
        mock_creds.return_value = Credentials()

        result = cmd_check()

        assert result == 1
        captured = capsys.readouterr()
        assert "No Jira URL configured" in captured.out

    @patch("skills.jira.scripts.jira.detect_deployment_type")
    @patch("skills.jira.scripts.jira.get_credentials")
    def test_cmd_check_no_token(self, mock_creds, mock_detect, capsys):
        """Test check command with no token."""
        mock_creds.return_value = Credentials(url="https://example.atlassian.net")
        mock_detect.return_value = "Cloud"

        result = cmd_check()

        assert result == 1
        captured = capsys.readouterr()
        assert "No API token configured" in captured.out

    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.detect_deployment_type")
    def test_cmd_check_connection_error(self, mock_detect, mock_creds, capsys):
        """Test check command with connection error."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="token",
        )
        mock_detect.side_effect = JiraDetectionError("Connection failed")

        result = cmd_check()

        assert result == 1
        captured = capsys.readouterr()
        assert "Connection failed" in captured.out

    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.detect_deployment_type")
    @patch("skills.jira.scripts.jira.get_api_version")
    @patch("skills.jira.scripts.jira.get")
    def test_cmd_check_api_error(self, mock_get, mock_api_version, mock_detect, mock_creds, capsys):
        """Test check command with API error."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="token",
        )
        mock_detect.return_value = "Cloud"
        mock_api_version.return_value = "3"
        mock_get.side_effect = APIError("API call failed")

        result = cmd_check()

        assert result == 1
        captured = capsys.readouterr()
        assert "API call failed" in captured.out

    @patch("skills.jira.scripts.jira.search_issues")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_issues_list")
    def test_cmd_search(self, mock_format, mock_defaults, mock_search):
        """Test search command."""
        mock_defaults.return_value = JiraDefaults()
        mock_search.return_value = [{"key": "DEMO-1"}]
        mock_format.return_value = "DEMO-1 | Test"

        args = argparse.Namespace(
            jql="project = DEMO",
            max_results=None,
            fields=None,
            json=False,
        )

        result = cmd_search(args)
        assert result == 0

    @patch("skills.jira.scripts.jira.get_issue")
    @patch("skills.jira.scripts.jira.format_issue")
    def test_cmd_issue_get(self, mock_format, mock_get_issue):
        """Test issue get command."""
        mock_get_issue.return_value = {"key": "DEMO-123"}
        mock_format.return_value = "Issue: DEMO-123"

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            json=False,
        )

        result = cmd_issue(args)
        assert result == 0

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    def test_cmd_issue_create(self, mock_defaults, mock_create):
        """Test issue create command."""
        mock_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-123"}

        args = argparse.Namespace(
            issue_command="create",
            project="DEMO",
            issue_type="Task",
            summary="Test",
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
        )

        result = cmd_issue(args)
        assert result == 0

    @patch("skills.jira.scripts.jira.get_transitions")
    @patch("skills.jira.scripts.jira.format_table")
    def test_cmd_transitions_list(self, mock_format, mock_get_transitions):
        """Test transitions list command."""
        mock_get_transitions.return_value = [
            {"id": "11", "name": "In Progress", "to": {"name": "In Progress"}},
        ]
        mock_format.return_value = "ID | Transition"

        args = argparse.Namespace(
            transition_command="list",
            issue_key="DEMO-123",
            json=False,
        )

        result = cmd_transitions(args)
        assert result == 0

    @patch("skills.jira.scripts.jira.load_config")
    def test_cmd_config_show_no_config(self, mock_load, capsys):
        """Test config show with no config file."""
        mock_load.return_value = None

        args = argparse.Namespace(
            config_command="show",
            project=None,
        )

        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No configuration file found" in captured.out

    @patch("skills.jira.scripts.jira.load_config")
    def test_cmd_config_show_with_config(self, mock_load, capsys):
        """Test config show with config file."""
        mock_load.return_value = {
            "url": "https://example.atlassian.net",
            "email": "test@example.com",
            "token": "secret",
            "defaults": {
                "jql_scope": "project = DEMO",
            },
        }

        args = argparse.Namespace(
            config_command="show",
            project=None,
        )

        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "https://example.atlassian.net" in captured.out
        assert "test@example.com" in captured.out

    @patch("skills.jira.scripts.jira.update_issue")
    def test_cmd_issue_update(self, mock_update, capsys):
        """Test issue update command."""
        mock_update.return_value = {}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary="Updated",
            description=None,
            priority=None,
            labels=None,
            assignee=None,
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Updated issue: DEMO-123" in captured.out

    @patch("skills.jira.scripts.jira.add_comment")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_comment(self, mock_defaults, mock_add_comment, capsys):
        """Test issue comment command."""
        mock_defaults.return_value = JiraDefaults()
        mock_add_comment.return_value = {"id": "12345"}

        args = argparse.Namespace(
            issue_command="comment",
            issue_key="DEMO-123",
            body="Test comment",
            security_level=None,
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Added comment to DEMO-123" in captured.out

    @patch("skills.jira.scripts.jira.add_comment")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_comment_with_security(self, mock_defaults, mock_add_comment, capsys):
        """Test issue comment with security level."""
        mock_defaults.return_value = JiraDefaults()
        mock_add_comment.return_value = {"id": "12345"}

        args = argparse.Namespace(
            issue_command="comment",
            issue_key="DEMO-123",
            body="Private comment",
            security_level="Red Hat Internal",
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Added private comment to DEMO-123" in captured.out
        assert "Red Hat Internal" in captured.out

    @patch("skills.jira.scripts.jira.do_transition")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_transitions_do(self, mock_defaults, mock_do_transition, capsys):
        """Test transitions do command."""
        mock_defaults.return_value = JiraDefaults()
        mock_do_transition.return_value = {}

        args = argparse.Namespace(
            transition_command="do",
            issue_key="DEMO-123",
            transition="In Progress",
            comment=None,
            security_level=None,
        )

        result = cmd_transitions(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Transitioned DEMO-123 to 'In Progress'" in captured.out

    @patch("skills.jira.scripts.jira.do_transition")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_transitions_do_with_comment(self, mock_defaults, mock_do_transition, capsys):
        """Test transitions do with comment."""
        mock_defaults.return_value = JiraDefaults()
        mock_do_transition.return_value = {}

        args = argparse.Namespace(
            transition_command="do",
            issue_key="DEMO-123",
            transition="Done",
            comment="Completed work",
            security_level=None,
        )

        result = cmd_transitions(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Transitioned DEMO-123 to 'Done'" in captured.out
        assert "(with comment)" in captured.out

    @patch("skills.jira.scripts.jira.search_issues")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_search_error(self, mock_defaults, mock_search, capsys):
        """Test search command with error."""
        mock_defaults.return_value = JiraDefaults()
        mock_search.side_effect = Exception("Search failed")

        args = argparse.Namespace(
            jql="project = DEMO",
            max_results=None,
            fields=None,
            json=False,
        )

        result = cmd_search(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Search failed" in captured.err

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    def test_cmd_issue_create_missing_type(self, mock_defaults, _mock_create, capsys):
        """Test issue create without type."""
        mock_defaults.return_value = ProjectDefaults()

        args = argparse.Namespace(
            issue_command="create",
            project="DEMO",
            issue_type=None,
            summary="Test",
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
        )

        result = cmd_issue(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "--type is required" in captured.err

    @patch("skills.jira.scripts.jira.search_issues")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_search_json_output(self, mock_format_json, mock_defaults, mock_search, capsys):
        """Test search command with JSON output."""
        mock_defaults.return_value = JiraDefaults()
        mock_search.return_value = [{"key": "DEMO-1"}]
        mock_format_json.return_value = '[{"key": "DEMO-1"}]'

        args = argparse.Namespace(
            jql="project = DEMO",
            max_results=None,
            fields=None,
            json=True,
        )

        result = cmd_search(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '[{"key": "DEMO-1"}]' in captured.out

    @patch("skills.jira.scripts.jira.load_config")
    def test_cmd_config_show_with_project(self, mock_load, capsys):
        """Test config show with specific project."""
        mock_load.return_value = {
            "url": "https://example.atlassian.net",
            "projects": {
                "DEMO": {
                    "issue_type": "Task",
                    "priority": "High",
                }
            },
        }

        args = argparse.Namespace(
            config_command="show",
            project="DEMO",
        )

        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Project Defaults for DEMO" in captured.out
        assert "Task" in captured.out
        assert "High" in captured.out

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_issue_create_json_output(
        self, mock_format_json, mock_defaults, mock_create, capsys
    ):
        """Test issue create with JSON output."""
        mock_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-123", "id": "10001"}
        mock_format_json.return_value = '{"key": "DEMO-123"}'

        args = argparse.Namespace(
            issue_command="create",
            project="DEMO",
            issue_type="Task",
            summary="Test",
            description="Desc",
            priority="High",
            labels="test,bug",
            assignee="123",
            json=True,
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '{"key": "DEMO-123"}' in captured.out

    @patch("skills.jira.scripts.jira.get_issue")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_issue_get_json_output(self, mock_format_json, mock_get_issue, capsys):
        """Test issue get with JSON output."""
        mock_get_issue.return_value = {"key": "DEMO-123"}
        mock_format_json.return_value = '{"key": "DEMO-123"}'

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            json=True,
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '{"key": "DEMO-123"}' in captured.out

    @patch("skills.jira.scripts.jira.get_transitions")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_transitions_list_json_output(self, mock_format_json, mock_get_transitions, capsys):
        """Test transitions list with JSON output."""
        mock_get_transitions.return_value = [
            {"id": "11", "name": "In Progress"},
        ]
        mock_format_json.return_value = '[{"id": "11"}]'

        args = argparse.Namespace(
            transition_command="list",
            issue_key="DEMO-123",
            json=True,
        )

        result = cmd_transitions(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '[{"id": "11"}]' in captured.out

    @patch("skills.jira.scripts.jira.search_issues")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_search_with_fields(self, mock_defaults, mock_search):
        """Test search with custom fields."""
        mock_defaults.return_value = JiraDefaults()
        mock_search.return_value = [{"key": "DEMO-1"}]

        args = argparse.Namespace(
            jql="project = DEMO",
            max_results=10,
            fields="summary,status,assignee",
            json=False,
        )

        result = cmd_search(args)

        assert result == 0
        mock_search.assert_called_once()
        # Verify fields were parsed
        call_args = mock_search.call_args
        assert call_args[0][2] == ["summary", "status", "assignee"]

    @patch("skills.jira.scripts.jira.update_issue")
    def test_cmd_issue_update_with_labels(self, mock_update):
        """Test issue update with labels."""
        mock_update.return_value = {}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary=None,
            description=None,
            priority=None,
            labels="test,bug",
            assignee=None,
        )

        result = cmd_issue(args)

        assert result == 0
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[1]["labels"] == ["test", "bug"]

    @patch("skills.jira.scripts.jira.do_transition")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_transitions_do_with_security(self, mock_defaults, mock_do_transition, capsys):
        """Test transition with security level."""
        mock_defaults.return_value = JiraDefaults()
        mock_do_transition.return_value = {}

        args = argparse.Namespace(
            transition_command="do",
            issue_key="DEMO-123",
            transition="Done",
            comment="Completed",
            security_level="Red Hat Internal",
        )

        result = cmd_transitions(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "private comment" in captured.out
