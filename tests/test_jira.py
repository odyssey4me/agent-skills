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
    _build_epic_children_jql,
    _deployment_cache,
    _extract_text_from_adf,
    _make_detection_request,
    _truncate,
    add_comment,
    api_path,
    clear_cache,
    cmd_check,
    cmd_collaboration,
    cmd_config,
    cmd_fields,
    cmd_issue,
    cmd_search,
    cmd_statuses,
    cmd_transitions,
    create_issue,
    delete_credential,
    detect_deployment_type,
    do_transition,
    extract_contributors,
    find_collaborative_epics,
    format_collaborative_epics,
    format_comments,
    format_issue,
    format_issues_list,
    format_json,
    format_rich_text,
    format_table,
    get_api_version,
    get_comments,
    get_credential,
    get_credentials,
    get_epic_children,
    get_issue,
    get_jira_defaults,
    get_project_defaults,
    get_transitions,
    is_cloud,
    list_fields,
    list_status_categories,
    list_statuses,
    load_config,
    save_config,
    search_by_contributor,
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
        """Test issue formatting as markdown."""
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

        assert result.startswith("### DEMO-123: Test issue\n")
        assert "- **Status:** Open" in result
        assert "- **Assignee:** Alice" in result
        assert "- **Priority:** High" in result

    def test_format_issues_list(self):
        """Test formatting issue list as markdown."""
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

        assert "### DEMO-1: First" in result
        assert "### DEMO-2: Second" in result
        assert "- **Assignee:** Alice" in result
        assert "- **Assignee:** Unassigned" in result

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
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_issue")
    def test_cmd_issue_get(self, mock_format, mock_defaults, mock_get_issue):
        """Test issue get command."""
        mock_defaults.return_value = JiraDefaults()
        mock_get_issue.return_value = {"key": "DEMO-123"}
        mock_format.return_value = "Issue: DEMO-123"

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            fields=None,
            json=False,
        )

        result = cmd_issue(args)
        assert result == 0
        mock_get_issue.assert_called_once_with("DEMO-123", fields=None)

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
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_issue_get_json_output(
        self, mock_format_json, mock_defaults, mock_get_issue, capsys
    ):
        """Test issue get with JSON output."""
        mock_defaults.return_value = JiraDefaults()
        mock_get_issue.return_value = {"key": "DEMO-123"}
        mock_format_json.return_value = '{"key": "DEMO-123"}'

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            fields=None,
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

    @patch("skills.jira.scripts.jira.get_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_issue")
    def test_cmd_issue_get_with_fields(self, mock_format, mock_defaults, mock_get_issue):
        """Test issue get with custom fields."""
        mock_defaults.return_value = JiraDefaults()
        mock_get_issue.return_value = {"key": "DEMO-123"}
        mock_format.return_value = "Issue: DEMO-123"

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            fields="summary,status",
            json=False,
        )

        result = cmd_issue(args)

        assert result == 0
        mock_get_issue.assert_called_once_with("DEMO-123", fields=["summary", "status"])

    @patch("skills.jira.scripts.jira.get_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_issue")
    def test_cmd_issue_get_with_config_defaults(self, mock_format, mock_defaults, mock_get_issue):
        """Test issue get uses config default fields."""
        mock_defaults.return_value = JiraDefaults(fields=["summary", "status", "assignee"])
        mock_get_issue.return_value = {"key": "DEMO-123"}
        mock_format.return_value = "Issue: DEMO-123"

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            fields=None,
            json=False,
        )

        result = cmd_issue(args)

        assert result == 0
        mock_get_issue.assert_called_once_with("DEMO-123", fields=["summary", "status", "assignee"])


class TestGetIssueWithFields:
    """Tests for get_issue with fields parameter."""

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_get_issue_without_fields(self, mock_api_path, mock_get):
        """Test getting issue without fields."""
        mock_api_path.return_value = "rest/api/3/issue/DEMO-123"
        mock_get.return_value = {"key": "DEMO-123", "fields": {"summary": "Test"}}

        result = get_issue("DEMO-123")

        assert result["key"] == "DEMO-123"
        mock_get.assert_called_once_with("jira", "rest/api/3/issue/DEMO-123", params=None)

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_get_issue_with_fields(self, mock_api_path, mock_get):
        """Test getting issue with specific fields."""
        mock_api_path.return_value = "rest/api/3/issue/DEMO-123"
        mock_get.return_value = {"key": "DEMO-123", "fields": {"summary": "Test"}}

        result = get_issue("DEMO-123", fields=["summary", "status"])

        assert result["key"] == "DEMO-123"
        mock_get.assert_called_once_with(
            "jira", "rest/api/3/issue/DEMO-123", params={"fields": "summary,status"}
        )


class TestMetadataDiscovery:
    """Tests for metadata discovery functions."""

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_list_fields_global(self, mock_api_path, mock_get):
        """Test listing all global fields."""
        mock_api_path.return_value = "rest/api/3/field"
        mock_get.return_value = [
            {"id": "summary", "name": "Summary", "custom": False},
            {"id": "customfield_10001", "name": "Story Points", "custom": True},
        ]

        result = list_fields()

        assert len(result) == 2
        assert result[0]["id"] == "summary"
        assert result[1]["custom"] is True

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_list_fields_project_context(self, mock_api_path, mock_get):
        """Test listing fields for project/issue-type context."""
        mock_api_path.return_value = "rest/api/3/issue/createmeta/DEMO/issuetypes/Task"
        mock_get.return_value = {
            "values": [
                {"fieldId": "summary", "name": "Summary"},
                {"fieldId": "description", "name": "Description"},
            ]
        }

        result = list_fields(project_key="DEMO", issue_type="Task")

        assert len(result) == 2
        assert result[0]["fieldId"] == "summary"

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_list_statuses(self, mock_api_path, mock_get):
        """Test listing all statuses."""
        mock_api_path.return_value = "rest/api/3/status"
        mock_get.return_value = [
            {"name": "Open", "statusCategory": {"name": "To Do"}},
            {"name": "In Progress", "statusCategory": {"name": "In Progress"}},
            {"name": "Done", "statusCategory": {"name": "Done"}},
        ]

        result = list_statuses()

        assert len(result) == 3
        assert result[0]["name"] == "Open"
        assert result[1]["statusCategory"]["name"] == "In Progress"

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_list_status_categories(self, mock_api_path, mock_get):
        """Test listing status categories."""
        mock_api_path.return_value = "rest/api/3/statuscategory"
        mock_get.return_value = [
            {"key": "new", "name": "To Do", "colorName": "blue-gray"},
            {"key": "indeterminate", "name": "In Progress", "colorName": "yellow"},
            {"key": "done", "name": "Done", "colorName": "green"},
        ]

        result = list_status_categories()

        assert len(result) == 3
        assert result[0]["key"] == "new"
        assert result[2]["colorName"] == "green"

    @patch("skills.jira.scripts.jira.list_fields")
    def test_cmd_fields_table_output(self, mock_list_fields, capsys):
        """Test fields command with table output."""
        mock_list_fields.return_value = [
            {"id": "summary", "name": "Summary", "custom": False},
            {"id": "customfield_10001", "name": "Story Points", "custom": True},
        ]

        args = argparse.Namespace(
            project=None,
            issue_type=None,
            json=False,
        )

        result = cmd_fields(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Summary" in captured.out
        assert "Story Points" in captured.out

    @patch("skills.jira.scripts.jira.list_fields")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_fields_json_output(self, mock_format_json, mock_list_fields, capsys):
        """Test fields command with JSON output."""
        mock_list_fields.return_value = [{"id": "summary", "name": "Summary"}]
        mock_format_json.return_value = '[{"id": "summary", "name": "Summary"}]'

        args = argparse.Namespace(
            project=None,
            issue_type=None,
            json=True,
        )

        result = cmd_fields(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '[{"id": "summary"' in captured.out

    @patch("skills.jira.scripts.jira.list_statuses")
    def test_cmd_statuses_table_output(self, mock_list_statuses, capsys):
        """Test statuses command with table output."""
        mock_list_statuses.return_value = [
            {"name": "Open", "statusCategory": {"name": "To Do"}},
            {"name": "Done", "statusCategory": {"name": "Done"}},
        ]

        args = argparse.Namespace(
            categories=False,
            json=False,
        )

        result = cmd_statuses(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Open" in captured.out
        assert "To Do" in captured.out

    @patch("skills.jira.scripts.jira.list_status_categories")
    def test_cmd_statuses_categories_output(self, mock_list_categories, capsys):
        """Test statuses command with categories flag."""
        mock_list_categories.return_value = [
            {"key": "new", "name": "To Do", "colorName": "blue-gray"},
            {"key": "done", "name": "Done", "colorName": "green"},
        ]

        args = argparse.Namespace(
            categories=True,
            json=False,
        )

        result = cmd_statuses(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "To Do" in captured.out
        assert "blue-gray" in captured.out

    @patch("skills.jira.scripts.jira.list_statuses")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_statuses_json_output(self, mock_format_json, mock_list_statuses, capsys):
        """Test statuses command with JSON output."""
        mock_list_statuses.return_value = [{"name": "Open"}]
        mock_format_json.return_value = '[{"name": "Open"}]'

        args = argparse.Namespace(
            categories=False,
            json=True,
        )

        result = cmd_statuses(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '[{"name": "Open"}]' in captured.out


class TestComments:
    """Tests for comment retrieval and formatting."""

    @patch("skills.jira.scripts.jira.get")
    def test_get_comments(self, mock_get):
        """Test fetching comments from an issue."""
        mock_get.return_value = {
            "comments": [
                {"id": "1", "body": "Hello", "author": {"displayName": "Jane"}},
                {"id": "2", "body": "World", "author": {"displayName": "John"}},
            ]
        }

        result = get_comments("DEMO-123", max_results=10)

        assert len(result) == 2
        assert result[0]["body"] == "Hello"
        mock_get.assert_called_once()

    @patch("skills.jira.scripts.jira.get")
    def test_get_comments_empty(self, mock_get):
        """Test fetching comments when there are none."""
        mock_get.return_value = {"comments": []}

        result = get_comments("DEMO-123")

        assert result == []

    def test_extract_text_from_adf_plain_string(self):
        """Test ADF extraction with a plain text string (DC format)."""
        assert _extract_text_from_adf("Hello world") == "Hello world"

    def test_extract_text_from_adf_dict(self):
        """Test ADF extraction with an ADF document node."""
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Hello "},
                        {"type": "text", "text": "world"},
                    ],
                }
            ],
        }

        assert _extract_text_from_adf(adf) == "Hello world"

    def test_extract_text_from_adf_nested(self):
        """Test ADF extraction with nested content."""
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Line 1"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Line 2"}],
                },
            ],
        }

        assert _extract_text_from_adf(adf) == "Line 1Line 2"

    def test_extract_text_from_adf_non_dict(self):
        """Test ADF extraction with non-dict, non-string input."""
        assert _extract_text_from_adf(42) == ""
        assert _extract_text_from_adf(None) == ""

    def test_format_comments(self):
        """Test formatting comments as markdown."""
        comments = [
            {
                "author": {"displayName": "Jane Doe"},
                "created": "2026-02-20T14:30:00.000+0000",
                "body": "Great work!",
            },
        ]

        result = format_comments(comments, "DEMO-123")

        assert "## Comments on DEMO-123" in result
        assert "### Jane Doe (2026-02-20 14:30)" in result
        assert "Great work!" in result

    def test_format_comments_empty(self):
        """Test formatting when no comments exist."""
        result = format_comments([], "DEMO-123")

        assert "No comments found" in result

    def test_format_comments_adf_body(self):
        """Test formatting comments with ADF body."""
        comments = [
            {
                "author": {"displayName": "Bot"},
                "created": "2026-01-01T00:00:00.000+0000",
                "body": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "ADF content"}],
                        }
                    ],
                },
            },
        ]

        result = format_comments(comments, "DEMO-123")

        assert "ADF content" in result


class TestContributors:
    """Tests for contributor extraction."""

    def test_extract_contributors_full(self):
        """Test extracting contributors from issue and comments."""
        issue = {
            "fields": {
                "reporter": {"displayName": "Alice"},
                "assignee": {"displayName": "Bob"},
            }
        }
        comments = [
            {"author": {"displayName": "Charlie"}},
            {"author": {"displayName": "Alice"}},  # duplicate
        ]

        result = extract_contributors(issue, comments)

        assert result == {"Alice", "Bob", "Charlie"}

    def test_extract_contributors_no_assignee(self):
        """Test extracting contributors when assignee is None."""
        issue = {
            "fields": {
                "reporter": {"displayName": "Alice"},
                "assignee": None,
            }
        }

        result = extract_contributors(issue, [])

        assert result == {"Alice"}

    def test_extract_contributors_empty_comments(self):
        """Test extracting contributors with no comments."""
        issue = {
            "fields": {
                "reporter": {"displayName": "Alice"},
                "assignee": {"displayName": "Bob"},
            }
        }

        result = extract_contributors(issue, [])

        assert result == {"Alice", "Bob"}

    def test_extract_contributors_no_reporter(self):
        """Test extracting contributors with no reporter."""
        issue = {"fields": {"assignee": {"displayName": "Bob"}}}

        result = extract_contributors(issue, [])

        assert result == {"Bob"}

    @patch("skills.jira.scripts.jira.get_comments")
    @patch("skills.jira.scripts.jira.get_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_get_with_contributors(self, mock_defaults, mock_get, mock_comments, capsys):
        """Test issue get with --contributors flag."""
        mock_defaults.return_value = JiraDefaults()
        mock_get.return_value = {
            "key": "DEMO-123",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "assignee": {"displayName": "Bob"},
                "priority": {"name": "High"},
                "reporter": {"displayName": "Alice"},
            },
        }
        mock_comments.return_value = [{"author": {"displayName": "Charlie"}}]

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            fields=None,
            json=False,
            contributors=True,
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Contributors:" in captured.out
        assert "Alice" in captured.out
        assert "Bob" in captured.out
        assert "Charlie" in captured.out

    @patch("skills.jira.scripts.jira.get_comments")
    @patch("skills.jira.scripts.jira.get_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_issue_get_with_contributors_json(
        self, mock_format_json, mock_defaults, mock_get, mock_comments
    ):
        """Test issue get with --contributors and --json."""
        mock_defaults.return_value = JiraDefaults()
        mock_get.return_value = {
            "key": "DEMO-123",
            "fields": {
                "reporter": {"displayName": "Alice"},
                "assignee": None,
            },
        }
        mock_comments.return_value = []
        mock_format_json.return_value = "{}"

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            fields=None,
            json=True,
            contributors=True,
        )

        result = cmd_issue(args)

        assert result == 0
        # Verify _contributors key was added to the issue dict
        call_args = mock_format_json.call_args[0][0]
        assert "_contributors" in call_args
        assert "Alice" in call_args["_contributors"]


class TestContributorSearch:
    """Tests for contributor search."""

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_search_by_contributor_with_scriptrunner(self, mock_search, mock_sr):
        """Test contributor search with ScriptRunner available."""
        mock_sr.return_value = {"available": True, "enhanced_search": True}
        mock_search.return_value = [{"key": "DEMO-1"}]

        result = search_by_contributor("jsmith")

        assert len(result) == 1
        jql = mock_search.call_args[0][0]
        assert 'reporter = "jsmith"' in jql
        assert 'assignee = "jsmith"' in jql
        assert 'commentedByUser("jsmith")' in jql

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_search_by_contributor_without_scriptrunner(self, mock_search, mock_sr, capsys):
        """Test contributor search without ScriptRunner."""
        mock_sr.return_value = {"available": False, "enhanced_search": False}
        mock_search.return_value = []

        search_by_contributor("jsmith")

        captured = capsys.readouterr()
        assert "ScriptRunner" in captured.err
        jql = mock_search.call_args[0][0]
        assert "commentedByUser" not in jql

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_search_by_contributor_with_project(self, mock_search, mock_sr):
        """Test contributor search scoped to a project."""
        mock_sr.return_value = {"available": False, "enhanced_search": False}
        mock_search.return_value = []

        search_by_contributor("jsmith", project="DEMO")

        jql = mock_search.call_args[0][0]
        assert "project = DEMO" in jql

    @patch("skills.jira.scripts.jira.search_by_contributor")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_search_contributor(self, mock_defaults, mock_contrib):
        """Test cmd_search with --contributor."""
        mock_defaults.return_value = JiraDefaults()
        mock_contrib.return_value = [
            {
                "key": "DEMO-1",
                "fields": {
                    "summary": "Test",
                    "status": {"name": "Open"},
                    "assignee": {"displayName": "Bob"},
                },
            }
        ]

        args = argparse.Namespace(
            jql=None,
            contributor="jsmith",
            project="DEMO",
            max_results=None,
            fields=None,
            json=False,
        )

        result = cmd_search(args)

        assert result == 0
        mock_contrib.assert_called_once_with("jsmith", "DEMO", 50, None)

    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_search_no_jql_no_contributor(self, mock_defaults, capsys):
        """Test cmd_search with neither jql nor --contributor."""
        mock_defaults.return_value = JiraDefaults()

        args = argparse.Namespace(
            jql=None,
            contributor=None,
            project=None,
            max_results=None,
            fields=None,
            json=False,
        )

        result = cmd_search(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "either a JQL query or --contributor is required" in captured.err


class TestCollaborativeEpics:
    """Tests for collaborative epics discovery."""

    @patch("skills.jira.scripts.jira.is_cloud")
    def test_build_epic_children_jql_cloud(self, mock_cloud):
        """Test epic children JQL for Cloud."""
        mock_cloud.return_value = True

        jql = _build_epic_children_jql("EPIC-1")

        assert '"Epic Link" = EPIC-1' in jql
        assert "parent = EPIC-1" in jql

    @patch("skills.jira.scripts.jira.is_cloud")
    def test_build_epic_children_jql_dc(self, mock_cloud):
        """Test epic children JQL for Data Center."""
        mock_cloud.return_value = False

        jql = _build_epic_children_jql("EPIC-1")

        assert '"Epic Link" = EPIC-1' in jql
        assert "parent" not in jql

    @patch("skills.jira.scripts.jira.search_issues")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_get_epic_children(self, mock_cloud, mock_search):
        """Test fetching epic children."""
        mock_cloud.return_value = False
        mock_search.return_value = [{"key": "TASK-1"}, {"key": "TASK-2"}]

        result = get_epic_children("EPIC-1", fields=["assignee"])

        assert len(result) == 2
        mock_search.assert_called_once()

    @patch("skills.jira.scripts.jira.get_epic_children")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_find_collaborative_epics(self, mock_search, mock_children):
        """Test finding collaborative epics."""
        mock_search.return_value = [
            {"key": "EPIC-1", "fields": {"summary": "Epic 1", "status": {"name": "Open"}}},
            {"key": "EPIC-2", "fields": {"summary": "Epic 2", "status": {"name": "Open"}}},
        ]
        mock_children.side_effect = [
            # EPIC-1: two different assignees
            [
                {"fields": {"assignee": {"displayName": "Alice"}}},
                {"fields": {"assignee": {"displayName": "Bob"}}},
            ],
            # EPIC-2: one assignee
            [
                {"fields": {"assignee": {"displayName": "Alice"}}},
            ],
        ]

        result = find_collaborative_epics(project="DEMO", min_contributors=2)

        assert len(result) == 1
        assert result[0]["epic"]["key"] == "EPIC-1"
        assert result[0]["children_count"] == 2
        assert sorted(result[0]["contributors"]) == ["Alice", "Bob"]

    @patch("skills.jira.scripts.jira.get_epic_children")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_find_collaborative_epics_none_found(self, mock_search, mock_children):
        """Test when no collaborative epics are found."""
        mock_search.return_value = [
            {"key": "EPIC-1", "fields": {"summary": "Solo epic"}},
        ]
        mock_children.return_value = [
            {"fields": {"assignee": {"displayName": "Alice"}}},
        ]

        result = find_collaborative_epics(min_contributors=2)

        assert result == []

    def test_format_collaborative_epics(self):
        """Test formatting collaborative epics."""
        results = [
            {
                "epic": {"key": "EPIC-1", "fields": {"summary": "My Epic"}},
                "children_count": 5,
                "contributors": ["Alice", "Bob"],
            }
        ]

        output = format_collaborative_epics(results)

        assert "## Collaborative Epics" in output
        assert "EPIC-1: My Epic" in output
        assert "Children:** 5" in output
        assert "Alice, Bob" in output

    def test_format_collaborative_epics_empty(self):
        """Test formatting when no results."""
        output = format_collaborative_epics([])

        assert "No collaborative epics found" in output


class TestCmdCollaboration:
    """Tests for cmd_collaboration handler."""

    @patch("skills.jira.scripts.jira.find_collaborative_epics")
    def test_cmd_collaboration_epics(self, mock_find, capsys):
        """Test collaboration epics command."""
        mock_find.return_value = [
            {
                "epic": {"key": "EPIC-1", "fields": {"summary": "Epic"}},
                "children_count": 3,
                "contributors": ["Alice", "Bob"],
            }
        ]

        args = argparse.Namespace(
            collaboration_command="epics",
            project="DEMO",
            min_contributors=2,
            max_results=50,
            json=False,
        )

        result = cmd_collaboration(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "EPIC-1" in captured.out

    @patch("skills.jira.scripts.jira.find_collaborative_epics")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_collaboration_epics_json(self, mock_format_json, mock_find, capsys):
        """Test collaboration epics with JSON output."""
        mock_find.return_value = [
            {
                "epic": {"key": "EPIC-1", "fields": {"summary": "Epic"}},
                "children_count": 3,
                "contributors": ["Alice", "Bob"],
            }
        ]
        mock_format_json.return_value = '[{"epic": {"key": "EPIC-1"}}]'

        args = argparse.Namespace(
            collaboration_command="epics",
            project=None,
            min_contributors=2,
            max_results=50,
            json=True,
        )

        result = cmd_collaboration(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "EPIC-1" in captured.out

    @patch("skills.jira.scripts.jira.find_collaborative_epics")
    def test_cmd_collaboration_epics_error(self, mock_find, capsys):
        """Test collaboration epics with error."""
        mock_find.side_effect = Exception("API error")

        args = argparse.Namespace(
            collaboration_command="epics",
            project=None,
            min_contributors=2,
            max_results=50,
            json=False,
        )

        result = cmd_collaboration(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "API error" in captured.err


class TestCmdIssueComments:
    """Tests for the issue comments subcommand handler."""

    @patch("skills.jira.scripts.jira.get_comments")
    def test_cmd_issue_comments(self, mock_comments, capsys):
        """Test issue comments subcommand."""
        mock_comments.return_value = [
            {
                "author": {"displayName": "Jane"},
                "created": "2026-02-20T10:00:00.000+0000",
                "body": "Test comment",
            }
        ]

        args = argparse.Namespace(
            issue_command="comments",
            issue_key="DEMO-123",
            max_results=50,
            json=False,
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Comments on DEMO-123" in captured.out
        assert "Test comment" in captured.out

    @patch("skills.jira.scripts.jira.get_comments")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_issue_comments_json(self, mock_format_json, mock_comments, capsys):
        """Test issue comments with JSON output."""
        mock_comments.return_value = [{"id": "1", "body": "Hello"}]
        mock_format_json.return_value = '[{"id": "1"}]'

        args = argparse.Namespace(
            issue_command="comments",
            issue_key="DEMO-123",
            max_results=50,
            json=True,
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert '[{"id": "1"}]' in captured.out
