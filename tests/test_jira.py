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
    _format_component,
    _format_scope_ari,
    _format_timestamp,
    _humanise_component_type,
    _make_detection_request,
    _parse_inline,
    _parse_link_args,
    _parse_markdown_to_adf,
    _summarise_value,
    _truncate,
    add_comment,
    api_path,
    automation_path,
    clear_cache,
    cmd_automations,
    cmd_check,
    cmd_collaboration,
    cmd_config,
    cmd_fields,
    cmd_issue,
    cmd_search,
    cmd_statuses,
    cmd_transitions,
    cmd_user,
    coerce_field_value,
    create_issue,
    create_link,
    delete_credential,
    detect_deployment_type,
    discover_custom_field,
    do_transition,
    ensure_field_included,
    extract_contributors,
    find_collaborative_epics,
    format_automation_detail,
    format_automation_summary,
    format_collaborative_epics,
    format_comments,
    format_issue,
    format_issues_list,
    format_json,
    format_rich_text,
    format_table,
    get_api_version,
    get_automation_rule,
    get_cloud_id,
    get_comments,
    get_credential,
    get_credentials,
    get_epic_children,
    get_issue,
    get_jira_defaults,
    get_link_types,
    get_project_defaults,
    get_transitions,
    is_cloud,
    list_automation_rules,
    list_fields,
    list_status_categories,
    list_statuses,
    load_config,
    parse_issue_file,
    resolve_custom_field,
    resolve_or_discover_field,
    resolve_user,
    resolve_user_for_jql,
    save_config,
    search_by_contributor,
    search_issues,
    set_credential,
    update_issue,
    validate_custom_fields,
    validate_jql_for_scriptrunner,
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
                "security_level": "Internal",
                "max_results": 100,
                "fields": ["summary", "status"],
            }
        }

        defaults = get_jira_defaults()

        assert defaults.jql_scope == "project = DEMO"
        assert defaults.security_level == "Internal"
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

    def test_format_rich_text_heading(self):
        """Test heading markdown produces ADF heading node."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("## My Title")

            node = result["content"][0]
            assert node["type"] == "heading"
            assert node["attrs"]["level"] == 2
            assert node["content"][0]["text"] == "My Title"

    def test_format_rich_text_bold(self):
        """Test bold markdown produces text node with strong mark."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("Some **bold** text")

            content = result["content"][0]["content"]
            assert len(content) == 3
            assert content[0] == {"type": "text", "text": "Some "}
            assert content[1]["text"] == "bold"
            assert content[1]["marks"] == [{"type": "strong"}]
            assert content[2] == {"type": "text", "text": " text"}

    def test_format_rich_text_link(self):
        """Test link markdown produces text node with link mark."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("Click [here](https://example.com)")

            content = result["content"][0]["content"]
            assert len(content) == 2
            assert content[0] == {"type": "text", "text": "Click "}
            assert content[1]["text"] == "here"
            assert content[1]["marks"] == [
                {"type": "link", "attrs": {"href": "https://example.com"}}
            ]

    def test_format_rich_text_bullet_list(self):
        """Test bullet list markdown produces ADF bulletList."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("- one\n- two\n- three")

            node = result["content"][0]
            assert node["type"] == "bulletList"
            assert len(node["content"]) == 3
            assert node["content"][0]["type"] == "listItem"
            para = node["content"][0]["content"][0]
            assert para["content"][0]["text"] == "one"

    def test_format_rich_text_horizontal_rule(self):
        """Test horizontal rule produces ADF rule node."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("above\n---\nbelow")

            assert result["content"][0]["type"] == "paragraph"
            assert result["content"][1]["type"] == "rule"
            assert result["content"][2]["type"] == "paragraph"

    def test_format_rich_text_table(self):
        """Test Jira wiki table syntax produces ADF table."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("|| H1 || H2 ||\n| c1 | c2 |")

            table = result["content"][0]
            assert table["type"] == "table"
            assert len(table["content"]) == 2
            header_row = table["content"][0]
            assert header_row["content"][0]["type"] == "tableHeader"
            body_row = table["content"][1]
            assert body_row["content"][0]["type"] == "tableCell"

    def test_format_rich_text_paragraphs(self):
        """Test blank lines separate paragraphs."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("para one\n\npara two")

            assert len(result["content"]) == 2
            assert result["content"][0]["type"] == "paragraph"
            assert result["content"][0]["content"][0]["text"] == "para one"
            assert result["content"][1]["type"] == "paragraph"
            assert result["content"][1]["content"][0]["text"] == "para two"

    def test_format_rich_text_mixed(self):
        """Test mixed markdown produces correct sequence of ADF nodes."""
        with patch("skills.jira.scripts.jira.get_api_version") as mock_version:
            mock_version.return_value = "3"
            result = format_rich_text("## Heading\n\nSome text\n\n- item one\n- item two")

            assert result["content"][0]["type"] == "heading"
            assert result["content"][1]["type"] == "paragraph"
            assert result["content"][2]["type"] == "bulletList"

    def test_parse_inline_plain(self):
        """Test parse_inline with no formatting."""
        nodes = _parse_inline("plain text")
        assert nodes == [{"type": "text", "text": "plain text"}]

    def test_parse_inline_multiple_marks(self):
        """Test parse_inline with bold and link in same line."""
        nodes = _parse_inline("**bold** and [link](http://x.com)")
        assert len(nodes) == 3
        assert nodes[0]["marks"] == [{"type": "strong"}]
        assert nodes[1] == {"type": "text", "text": " and "}
        assert nodes[2]["marks"][0]["type"] == "link"

    def test_parse_markdown_to_adf_empty(self):
        """Test empty string produces a single empty paragraph."""
        blocks = _parse_markdown_to_adf("")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"


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

    def test_format_issue_with_custom_fields(self):
        """Test issue formatting includes custom fields when configured."""
        issue = {
            "key": "DEMO-123",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "Open"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "High"},
                "customfield_10028": 5.0,
            },
        }

        result = format_issue(issue, custom_fields={"story_points": "customfield_10028"})

        assert "- **Story Points:** 5" in result

    def test_format_issue_with_fractional_custom_field(self):
        """Test issue formatting preserves fractional custom field values."""
        issue = {
            "key": "DEMO-123",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "assignee": None,
                "priority": None,
                "customfield_10028": 0.5,
            },
        }

        result = format_issue(issue, custom_fields={"story_points": "customfield_10028"})

        assert "- **Story Points:** 0.5" in result

    def test_format_issue_without_custom_fields(self):
        """Test custom fields omitted when not configured."""
        issue = {
            "key": "DEMO-123",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "assignee": None,
                "priority": None,
            },
        }

        result = format_issue(issue)

        assert "Story Points" not in result

    def test_format_issue_custom_field_none_value(self):
        """Test custom fields omitted when field value is None."""
        issue = {
            "key": "DEMO-123",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "assignee": None,
                "priority": None,
                "customfield_10028": None,
            },
        }

        result = format_issue(issue, custom_fields={"story_points": "customfield_10028"})

        assert "Story Points" not in result

    def test_format_issue_multiple_custom_fields(self):
        """Test issue formatting with multiple custom fields."""
        issue = {
            "key": "DEMO-123",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "assignee": None,
                "priority": None,
                "customfield_10028": 3.0,
                "customfield_12345": {"value": "Platform"},
            },
        }

        result = format_issue(
            issue,
            custom_fields={
                "story_points": "customfield_10028",
                "assigned_team": "customfield_12345",
            },
        )

        assert "- **Story Points:** 3" in result
        assert "- **Assigned Team:** Platform" in result

    def test_format_issues_list_with_custom_fields(self):
        """Test list formatting includes custom fields when configured."""
        issues = [
            {
                "key": "DEMO-1",
                "fields": {
                    "summary": "With points",
                    "status": {"name": "Open"},
                    "assignee": None,
                    "customfield_10028": 3.0,
                },
            },
            {
                "key": "DEMO-2",
                "fields": {
                    "summary": "Without points",
                    "status": {"name": "Open"},
                    "assignee": None,
                },
            },
        ]

        result = format_issues_list(issues, custom_fields={"story_points": "customfield_10028"})

        assert "- **Story Points:** 3" in result
        assert result.count("Story Points") == 1

    def test_format_issues_list_empty(self):
        """Test formatting empty issue list."""
        result = format_issues_list([])
        assert result == "No issues found"


class TestEnsureFieldIncluded:
    """Tests for ensure_field_included helper."""

    def test_adds_field_to_existing_list(self):
        result = ensure_field_included(["summary", "status"], "customfield_10028")
        assert "customfield_10028" in result
        assert "summary" in result

    def test_does_not_duplicate_existing_field(self):
        result = ensure_field_included(["summary", "customfield_10028"], "customfield_10028")
        assert result.count("customfield_10028") == 1

    def test_none_fields_uses_defaults(self):
        result = ensure_field_included(None, "customfield_10028")
        assert "customfield_10028" in result
        assert "summary" in result
        assert "status" in result


class TestCustomFieldResolution:
    """Tests for custom field resolution and discovery."""

    def test_resolve_custom_field_found(self):
        """Test resolving a configured custom field."""
        result = resolve_custom_field("story_points", {"story_points": "customfield_10028"})
        assert result == "customfield_10028"

    def test_resolve_custom_field_display_name(self):
        """Test resolving with display name normalizes to snake_case key."""
        result = resolve_custom_field("Story Points", {"story_points": "customfield_10028"})
        assert result == "customfield_10028"

    def test_resolve_custom_field_not_found(self):
        """Test resolving an unconfigured custom field."""
        result = resolve_custom_field("unknown", {"story_points": "customfield_10028"})
        assert result is None

    def test_resolve_custom_field_none_mapping(self):
        """Test resolving with no custom fields configured."""
        result = resolve_custom_field("story_points", None)
        assert result is None

    @patch("skills.jira.scripts.jira.list_fields")
    def test_discover_custom_field_single_match(self, mock_list_fields):
        """Test discovering a field with exactly one match."""
        mock_list_fields.return_value = [
            {
                "id": "customfield_10028",
                "name": "Story Points",
                "custom": True,
                "schema": {"type": "number"},
            },
            {"id": "summary", "name": "Summary", "custom": False},
        ]
        result = discover_custom_field("story_points")
        assert result == ("customfield_10028", "number")

    @patch("skills.jira.scripts.jira.list_fields")
    def test_discover_custom_field_no_match(self, mock_list_fields):
        """Test discovering a field with no matches."""
        mock_list_fields.return_value = [
            {"id": "summary", "name": "Summary", "custom": False},
        ]
        result = discover_custom_field("story_points")
        assert result is None

    @patch("skills.jira.scripts.jira.list_fields")
    def test_discover_custom_field_multiple_matches(self, mock_list_fields):
        """Test discovering a field with multiple matches returns None."""
        mock_list_fields.return_value = [
            {"id": "customfield_10028", "name": "Story Points", "custom": True},
            {"id": "customfield_20028", "name": "Story Points", "custom": True},
        ]
        result = discover_custom_field("story_points")
        assert result is None

    @patch("skills.jira.scripts.jira.save_config")
    @patch("skills.jira.scripts.jira.load_config")
    @patch("skills.jira.scripts.jira.list_fields")
    def test_resolve_or_discover_saves_to_config(
        self, mock_list_fields, mock_load_config, mock_save_config
    ):
        """Test resolve_or_discover saves discovered mapping and schema to config."""
        mock_list_fields.return_value = [
            {
                "id": "customfield_10028",
                "name": "Story Points",
                "custom": True,
                "schema": {"type": "number"},
            },
        ]
        mock_load_config.return_value = {"defaults": {}}

        result = resolve_or_discover_field("story_points", None)

        assert result == "customfield_10028"
        mock_save_config.assert_called_once()
        saved_config = mock_save_config.call_args[0][1]
        assert saved_config["defaults"]["custom_fields"]["story_points"] == "customfield_10028"
        assert saved_config["defaults"]["custom_field_schemas"]["story_points"] == "number"

    @patch("skills.jira.scripts.jira.save_config")
    @patch("skills.jira.scripts.jira.load_config")
    @patch("skills.jira.scripts.jira.list_fields")
    def test_resolve_or_discover_normalizes_display_name(
        self, mock_list_fields, mock_load_config, mock_save_config
    ):
        """Test resolve_or_discover normalizes display name to snake_case key."""
        mock_list_fields.return_value = [
            {
                "id": "customfield_10028",
                "name": "Story Points",
                "custom": True,
                "schema": {"type": "number"},
            },
        ]
        mock_load_config.return_value = {"defaults": {}}

        result = resolve_or_discover_field("Story Points", None)

        assert result == "customfield_10028"
        saved_config = mock_save_config.call_args[0][1]
        assert "story_points" in saved_config["defaults"]["custom_fields"]
        assert saved_config["defaults"]["custom_field_schemas"]["story_points"] == "number"

    @patch("skills.jira.scripts.jira.list_fields")
    def test_validate_custom_fields_all_valid(self, mock_list_fields):
        """Test validation passes when all fields exist."""
        mock_list_fields.return_value = [
            {"id": "customfield_10028", "name": "Story Points"},
            {"id": "customfield_12345", "name": "Assigned Team"},
        ]
        errors = validate_custom_fields(
            {
                "story_points": "customfield_10028",
                "assigned_team": "customfield_12345",
            }
        )
        assert errors == []

    @patch("skills.jira.scripts.jira.list_fields")
    def test_validate_custom_fields_invalid(self, mock_list_fields):
        """Test validation catches missing fields."""
        mock_list_fields.return_value = [
            {"id": "customfield_10028", "name": "Story Points"},
        ]
        errors = validate_custom_fields(
            {
                "story_points": "customfield_10028",
                "assigned_team": "customfield_99999",
            }
        )
        assert len(errors) == 1
        assert "assigned_team" in errors[0]


class TestCoerceFieldValue:
    """Tests for coerce_field_value schema-aware value wrapping."""

    @patch("skills.jira.scripts.jira.list_fields")
    def test_option_field(self, mock_list_fields):
        """Test option field wraps value in dict."""
        mock_list_fields.return_value = [
            {"id": "customfield_12345", "schema": {"type": "option"}},
        ]
        result = coerce_field_value("customfield_12345", "Platform Team")
        assert result == {"value": "Platform Team"}

    @patch("skills.jira.scripts.jira.list_fields")
    def test_security_level_field(self, mock_list_fields):
        """Test security level field wraps value with name key."""
        mock_list_fields.return_value = [
            {"id": "customfield_10030", "schema": {"type": "securitylevel"}},
        ]
        result = coerce_field_value("customfield_10030", "Internal")
        assert result == {"name": "Internal"}

    @patch("skills.jira.scripts.jira.list_fields")
    def test_number_field(self, mock_list_fields):
        """Test number field converts to float."""
        mock_list_fields.return_value = [
            {"id": "customfield_10028", "schema": {"type": "number"}},
        ]
        result = coerce_field_value("customfield_10028", "5")
        assert result == 5.0

    @patch("skills.jira.scripts.jira.list_fields")
    def test_string_field(self, mock_list_fields):
        """Test string field returns raw value."""
        mock_list_fields.return_value = [
            {"id": "customfield_99999", "schema": {"type": "string"}},
        ]
        result = coerce_field_value("customfield_99999", "hello")
        assert result == "hello"

    @patch("skills.jira.scripts.jira.list_fields")
    def test_array_of_options(self, mock_list_fields):
        """Test array of options splits and wraps each value."""
        mock_list_fields.return_value = [
            {"id": "customfield_11111", "schema": {"type": "array", "items": "option"}},
        ]
        result = coerce_field_value("customfield_11111", "foo, bar")
        assert result == [{"value": "foo"}, {"value": "bar"}]

    @patch("skills.jira.scripts.jira.list_fields")
    def test_unknown_field_returns_raw(self, mock_list_fields):
        """Test unknown field ID returns raw value."""
        mock_list_fields.return_value = []
        result = coerce_field_value("customfield_00000", "whatever")
        assert result == "whatever"

    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.list_fields")
    def test_user_field_cloud(self, mock_list_fields, mock_is_cloud):
        """Test user field wraps as accountId on Cloud."""
        mock_list_fields.return_value = [
            {"id": "customfield_22222", "schema": {"type": "user"}},
        ]
        mock_is_cloud.return_value = True
        result = coerce_field_value("customfield_22222", "abc123")
        assert result == {"accountId": "abc123"}

    def test_cached_schema_option(self):
        """Test option coercion via cached schema type (no API call)."""
        result = coerce_field_value("customfield_12345", "Platform Team", schema_type="option")
        assert result == {"value": "Platform Team"}

    def test_cached_schema_securitylevel(self):
        """Test security level coercion via cached schema type (no API call)."""
        result = coerce_field_value("customfield_10030", "Internal", schema_type="securitylevel")
        assert result == {"name": "Internal"}

    def test_cached_schema_number(self):
        """Test number coercion via cached schema type (no API call)."""
        result = coerce_field_value("customfield_10028", "5", schema_type="number")
        assert result == 5.0


class TestJiraDefaultsBackwardCompat:
    """Tests for backward compatibility of story_points_field config."""

    def test_story_points_field_migrated_to_custom_fields(self):
        """Test old story_points_field config is migrated."""
        config = {"defaults": {"story_points_field": "customfield_10028"}}
        defaults = JiraDefaults.from_config(config)
        assert defaults.custom_fields == {"story_points": "customfield_10028"}

    def test_custom_fields_takes_precedence(self):
        """Test custom_fields entry takes precedence over story_points_field."""
        config = {
            "defaults": {
                "story_points_field": "customfield_OLD",
                "custom_fields": {"story_points": "customfield_NEW"},
            }
        }
        defaults = JiraDefaults.from_config(config)
        assert defaults.custom_fields["story_points"] == "customfield_NEW"

    def test_no_custom_fields_returns_none(self):
        """Test no custom fields configured returns None."""
        config = {"defaults": {"max_results": 25}}
        defaults = JiraDefaults.from_config(config)
        assert defaults.custom_fields is None


class TestApiOperations:
    """Tests for API operations."""

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues_cloud(self, mock_api_path, mock_post, mock_is_cloud, mock_scriptrunner):
        """Test searching issues on Cloud (POST /search/jql)."""
        mock_api_path.return_value = "rest/api/3/search/jql"
        mock_is_cloud.return_value = True
        mock_post.return_value = {
            "issues": [
                {"key": "DEMO-1", "fields": {"summary": "Test"}},
            ]
        }
        mock_scriptrunner.return_value = {"available": False}

        result = search_issues("project = DEMO", max_results=10)

        assert len(result) == 1
        assert result[0]["key"] == "DEMO-1"

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues_datacenter(
        self, mock_api_path, mock_get, mock_is_cloud, mock_scriptrunner
    ):
        """Test searching issues on Data Center (GET /search)."""
        mock_api_path.return_value = "rest/api/2/search"
        mock_is_cloud.return_value = False
        mock_get.return_value = {
            "issues": [
                {"key": "DEMO-1", "fields": {"summary": "Test"}},
            ]
        }
        mock_scriptrunner.return_value = {"available": False}

        result = search_issues("project = DEMO", max_results=10)

        assert len(result) == 1
        assert result[0]["key"] == "DEMO-1"

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues_cloud_pagination(
        self, mock_api_path, mock_post, mock_is_cloud, mock_scriptrunner
    ):
        """Test Cloud search paginates using nextPageToken."""
        mock_api_path.return_value = "rest/api/3/search/jql"
        mock_is_cloud.return_value = True
        mock_scriptrunner.return_value = {"available": False}
        mock_post.side_effect = [
            {
                "issues": [{"key": "DEMO-1", "fields": {"summary": "First"}}],
                "nextPageToken": "token123",
            },
            {
                "issues": [{"key": "DEMO-2", "fields": {"summary": "Second"}}],
            },
        ]

        result = search_issues("project = DEMO", max_results=10)

        assert len(result) == 2
        assert result[0]["key"] == "DEMO-1"
        assert result[1]["key"] == "DEMO-2"

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues_cloud_non_dict_response(
        self, mock_api_path, mock_post, mock_is_cloud, mock_scriptrunner
    ):
        """Test Cloud search handles non-dict response."""
        mock_api_path.return_value = "rest/api/3/search/jql"
        mock_is_cloud.return_value = True
        mock_scriptrunner.return_value = {"available": False}
        mock_post.return_value = "unexpected"

        result = search_issues("project = DEMO", max_results=10)

        assert result == []

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues_datacenter_pagination(
        self, mock_api_path, mock_get, mock_is_cloud, mock_scriptrunner
    ):
        """Test Data Center search paginates using startAt/total."""
        mock_api_path.return_value = "rest/api/2/search"
        mock_is_cloud.return_value = False
        mock_scriptrunner.return_value = {"available": False}
        mock_get.side_effect = [
            {
                "issues": [{"key": "DEMO-1", "fields": {"summary": "First"}}],
                "total": 2,
            },
            {
                "issues": [{"key": "DEMO-2", "fields": {"summary": "Second"}}],
                "total": 2,
            },
        ]

        result = search_issues("project = DEMO", max_results=10)

        assert len(result) == 2
        assert result[1]["key"] == "DEMO-2"

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues_cloud_truncation_warning(
        self, mock_api_path, mock_post, mock_is_cloud, mock_scriptrunner, capsys
    ):
        """Test Cloud search warns when results are truncated at API limit."""
        mock_api_path.return_value = "rest/api/3/search/jql"
        mock_is_cloud.return_value = True
        mock_scriptrunner.return_value = {"available": False}
        batch = [{"key": f"DEMO-{i}", "fields": {"summary": f"Issue {i}"}} for i in range(100)]
        mock_post.side_effect = [
            {"issues": batch, "nextPageToken": f"token{p}"} for p in range(10)
        ] + [{"issues": batch, "nextPageToken": "more"}]

        result = search_issues("project = DEMO", max_results=1000)

        assert len(result) == 1000
        captured = capsys.readouterr()
        assert "Results may be truncated" in captured.err
        assert "1000 results returned" in captured.err

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_issues_datacenter_truncation_warning(
        self, mock_api_path, mock_get, mock_is_cloud, mock_scriptrunner, capsys
    ):
        """Test Data Center search warns when results are truncated at API limit."""
        mock_api_path.return_value = "rest/api/2/search"
        mock_is_cloud.return_value = False
        mock_scriptrunner.return_value = {"available": False}
        batch = [{"key": f"DEMO-{i}", "fields": {"summary": f"Issue {i}"}} for i in range(100)]
        mock_get.side_effect = [{"issues": batch, "total": 1500} for _ in range(10)]

        result = search_issues("project = DEMO", max_results=1000)

        assert len(result) == 1000
        captured = capsys.readouterr()
        assert "Results may be truncated" in captured.err
        assert "1000 results returned" in captured.err

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
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.get_cloud_id")
    @patch("skills.jira.scripts.jira.automation_path")
    def test_cmd_check_success(
        self,
        mock_auto_path,
        mock_cloud_id,
        mock_scriptrunner,
        mock_get,
        mock_post,
        mock_is_cloud,
        mock_api_version,
        mock_detect,
        mock_creds,
        capsys,
    ):
        """Test check command success."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            email="test@example.com",
            token="secret",
        )
        mock_detect.return_value = "Cloud"
        mock_api_version.return_value = "3"
        mock_is_cloud.return_value = True
        mock_post.return_value = {"issues": []}
        mock_scriptrunner.return_value = {
            "available": False,
            "version": None,
            "type": "cloud",
            "enhanced_search": False,
        }
        mock_cloud_id.return_value = "cloud-123"
        mock_auto_path.return_value = "gateway/path"

        def get_side_effect(_service, endpoint, **_kwargs):
            if "mypermissions" in endpoint:
                return {"permissions": {"ADMINISTER": {"havePermission": True}}}
            if "gateway" in endpoint:
                return {"data": [{"name": "Rule 1"}]}
            return {}

        mock_get.side_effect = get_side_effect

        result = cmd_check()

        assert result == 0
        captured = capsys.readouterr()
        assert "All checks passed" in captured.out
        assert "search/jql" in captured.out
        assert "Automation API: OK" in captured.out

    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.detect_deployment_type")
    @patch("skills.jira.scripts.jira.get_api_version")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get")
    def test_cmd_check_success_datacenter(
        self, mock_get, mock_is_cloud, mock_api_version, mock_detect, mock_creds, capsys
    ):
        """Test check command success on Data Center (GET /search)."""
        mock_creds.return_value = Credentials(
            url="https://jira.example.com",
            token="secret",
        )
        mock_detect.return_value = "DataCenter"
        mock_api_version.return_value = "2"
        mock_is_cloud.return_value = False
        mock_get.return_value = {"issues": []}

        result = cmd_check()

        assert result == 0
        captured = capsys.readouterr()
        assert "All checks passed" in captured.out
        assert "rest/api/2/search" in captured.out

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
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.post")
    def test_cmd_check_api_error(
        self, mock_post, mock_is_cloud, mock_api_version, mock_detect, mock_creds, capsys
    ):
        """Test check command with API error."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="token",
        )
        mock_detect.return_value = "Cloud"
        mock_api_version.return_value = "3"
        mock_is_cloud.return_value = True
        mock_post.side_effect = APIError("API call failed")

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
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_create(self, mock_jira_defaults, mock_defaults, mock_create):
        """Test issue create command."""
        mock_jira_defaults.return_value = JiraDefaults()
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
            from_file=None,
            set_field=None,
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
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_update(self, mock_jira_defaults, mock_update, capsys):
        """Test issue update command."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_update.return_value = {}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary="Updated",
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            from_file=None,
            set_field=None,
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
            security_level="Internal",
        )

        result = cmd_issue(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Added private comment to DEMO-123" in captured.out
        assert "Internal" in captured.out

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
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_create_missing_type(
        self, mock_jira_defaults, mock_defaults, _mock_create, capsys
    ):
        """Test issue create without type."""
        mock_jira_defaults.return_value = JiraDefaults()
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
            from_file=None,
            set_field=None,
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

    @patch("skills.jira.scripts.jira.resolve_or_discover_field")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_config_discover_found(self, mock_defaults, mock_resolve, capsys):
        """Test config discover when field is found."""
        mock_defaults.return_value = JiraDefaults(custom_fields={})
        mock_resolve.return_value = "customfield_10028"

        args = argparse.Namespace(
            config_command="discover",
            field_name="story_points",
        )
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "story_points -> customfield_10028" in captured.out
        mock_resolve.assert_called_once_with("story_points", {})

    @patch("skills.jira.scripts.jira.resolve_or_discover_field")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_config_discover_not_found(self, mock_defaults, mock_resolve, capsys):
        """Test config discover when field is not found."""
        mock_defaults.return_value = JiraDefaults(custom_fields={})
        mock_resolve.return_value = None

        args = argparse.Namespace(
            config_command="discover",
            field_name="nonexistent_field",
        )
        result = cmd_config(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Could not resolve field" in captured.out

    @patch("skills.jira.scripts.jira.load_config")
    def test_cmd_config_show_custom_fields(self, mock_load, capsys):
        """Test config show displays custom fields."""
        mock_load.return_value = {
            "url": "https://example.atlassian.net",
            "defaults": {
                "custom_fields": {
                    "story_points": "customfield_10028",
                    "security_level": "customfield_10030",
                }
            },
        }
        args = argparse.Namespace(config_command="show", project=None)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Custom Fields:" in captured.out
        assert "story_points: customfield_10028" in captured.out
        assert "security_level: customfield_10030" in captured.out

    @patch("skills.jira.scripts.jira.coerce_field_value")
    @patch("skills.jira.scripts.jira.load_config")
    @patch("skills.jira.scripts.jira.resolve_or_discover_field")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.create_issue")
    def test_cmd_issue_create_with_set_field(
        self, mock_create, mock_proj_defaults, mock_defaults, mock_resolve, mock_load, mock_coerce
    ):
        """Test issue create with --set-field."""
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_defaults.return_value = JiraDefaults(
            custom_fields={},
            custom_field_schemas={"story_points": "number"},
        )
        mock_resolve.return_value = "customfield_10028"
        mock_load.return_value = {
            "defaults": {
                "custom_fields": {"story_points": "customfield_10028"},
                "custom_field_schemas": {"story_points": "number"},
            }
        }
        mock_create.return_value = {"key": "DEMO-123"}
        mock_coerce.return_value = 5.0

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
            set_field=["story_points=5"],
            from_file=None,
        )
        result = cmd_issue(args)

        assert result == 0
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args
        assert call_kwargs[1]["extra_fields"] == {"customfield_10028": 5.0}
        mock_coerce.assert_called_once_with("customfield_10028", "5", schema_type="number")

    @patch("skills.jira.scripts.jira.coerce_field_value")
    @patch("skills.jira.scripts.jira.load_config")
    @patch("skills.jira.scripts.jira.resolve_or_discover_field")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.update_issue")
    def test_cmd_issue_update_with_set_field(
        self, mock_update, mock_defaults, mock_resolve, mock_load, mock_coerce
    ):
        """Test issue update with --set-field."""
        mock_defaults.return_value = JiraDefaults(
            custom_fields={},
            custom_field_schemas={"assigned_team": "option"},
        )
        mock_resolve.return_value = "customfield_12345"
        mock_load.return_value = {
            "defaults": {
                "custom_fields": {"assigned_team": "customfield_12345"},
                "custom_field_schemas": {"assigned_team": "option"},
            }
        }
        mock_update.return_value = {}
        mock_coerce.return_value = {"value": "Platform Team"}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            set_field=["assigned_team=Platform Team"],
            from_file=None,
        )
        result = cmd_issue(args)

        assert result == 0
        mock_update.assert_called_once()
        call_kwargs = mock_update.call_args
        assert call_kwargs[1]["extra_fields"] == {"customfield_12345": {"value": "Platform Team"}}
        mock_coerce.assert_called_once_with(
            "customfield_12345", "Platform Team", schema_type="option"
        )

    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_create_set_field_bad_format(self, mock_defaults, mock_proj_defaults, capsys):
        """Test issue create with badly formatted --set-field."""
        mock_defaults.return_value = JiraDefaults(custom_fields={})
        mock_proj_defaults.return_value = ProjectDefaults()

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
            set_field=["bad_format"],
            from_file=None,
        )
        result = cmd_issue(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "NAME=VALUE" in captured.err

    @patch("skills.jira.scripts.jira.validate_custom_fields")
    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get_api_version")
    @patch("skills.jira.scripts.jira.detect_deployment_type")
    @patch("skills.jira.scripts.jira.get_credentials")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_check_custom_fields_ok(
        self,
        mock_defaults,
        mock_creds,
        mock_detect,
        mock_api_version,
        mock_is_cloud,
        mock_post,
        mock_scriptrunner,
        mock_validate,
        capsys,
    ):
        """Test check command with valid custom fields."""
        mock_defaults.return_value = JiraDefaults(
            custom_fields={"story_points": "customfield_10028"},
            custom_field_schemas={"story_points": "number"},
        )
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", email="test@test.com", token="tok"
        )
        mock_detect.return_value = ("cloud", "3")
        mock_api_version.return_value = "2"
        mock_is_cloud.return_value = True
        mock_post.return_value = {"issues": []}
        mock_scriptrunner.return_value = {"available": False}
        mock_validate.return_value = []

        result = cmd_check()

        assert result == 0
        captured = capsys.readouterr()
        assert "story_points: customfield_10028 (type: number, OK)" in captured.out

    @patch("skills.jira.scripts.jira.search_issues")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_issues_list")
    def test_cmd_search_includes_custom_fields(self, mock_format, mock_defaults, mock_search):
        """Test search command includes custom field IDs in requested fields."""
        mock_defaults.return_value = JiraDefaults(
            custom_fields={"story_points": "customfield_10028"}
        )
        mock_search.return_value = []
        mock_format.return_value = ""

        args = argparse.Namespace(
            jql="project = DEMO",
            contributor=None,
            max_results=None,
            fields=None,
            json=False,
        )
        cmd_search(args)

        call_args = mock_search.call_args
        fields = call_args[0][2]
        assert "customfield_10028" in fields

    @patch("skills.jira.scripts.jira.get_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_issue")
    def test_cmd_issue_get_includes_custom_fields(self, mock_format, mock_defaults, mock_get_issue):
        """Test issue get command includes custom field IDs in requested fields."""
        mock_defaults.return_value = JiraDefaults(
            custom_fields={"story_points": "customfield_10028"}
        )
        mock_get_issue.return_value = {"key": "DEMO-123", "fields": {}}
        mock_format.return_value = ""

        args = argparse.Namespace(
            issue_command="get",
            issue_key="DEMO-123",
            fields=None,
            json=False,
            contributors=False,
        )
        cmd_issue(args)

        call_args = mock_get_issue.call_args
        fields = call_args[1]["fields"]
        assert "customfield_10028" in fields

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_issue_create_json_output(
        self, mock_format_json, mock_jira_defaults, mock_defaults, mock_create, capsys
    ):
        """Test issue create with JSON output."""
        mock_jira_defaults.return_value = JiraDefaults()
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
            from_file=None,
            set_field=None,
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
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_cmd_issue_update_with_labels(self, mock_jira_defaults, mock_update):
        """Test issue update with labels."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_update.return_value = {}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary=None,
            description=None,
            priority=None,
            labels="test,bug",
            assignee=None,
            from_file=None,
            set_field=None,
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
            security_level="Internal",
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

    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.get")
    def test_get_comments(self, mock_get, mock_api_path):
        """Test fetching comments from an issue."""
        mock_api_path.return_value = "/rest/api/2/issue/DEMO-123/comment"
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

    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.get")
    def test_get_comments_empty(self, mock_get, mock_api_path):
        """Test fetching comments when there are none."""
        mock_api_path.return_value = "/rest/api/2/issue/DEMO-123/comment"
        mock_get.return_value = {"comments": []}

        result = get_comments("DEMO-123")

        assert result == []

    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.get")
    def test_get_comments_pagination(self, mock_get, mock_api_path):
        """Test fetching comments paginates through results."""
        mock_api_path.return_value = "/rest/api/2/issue/DEMO-123/comment"
        mock_get.side_effect = [
            {
                "comments": [{"id": "1", "body": "First"}],
                "total": 2,
            },
            {
                "comments": [{"id": "2", "body": "Second"}],
                "total": 2,
            },
        ]

        result = get_comments("DEMO-123", max_results=10)

        assert len(result) == 2
        assert result[1]["body"] == "Second"
        assert mock_get.call_count == 2

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


class TestUserResolution:
    """Tests for user resolution functions."""

    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_resolve_user_cloud(self, mock_api_path, mock_get, mock_is_cloud):
        """Test resolving user on Cloud."""
        mock_is_cloud.return_value = True
        mock_api_path.return_value = "rest/api/3/user/search"
        mock_get.return_value = [
            {
                "accountId": "abc123",
                "emailAddress": "jdoe@example.com",
                "displayName": "Jane Doe",
                "active": True,
            }
        ]

        result = resolve_user("jdoe@example.com")

        assert len(result) == 1
        assert result[0]["accountId"] == "abc123"
        assert result[0]["emailAddress"] == "jdoe@example.com"

    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_datacenter(self, mock_is_cloud):
        """Test resolving user on Data Center (passthrough)."""
        mock_is_cloud.return_value = False

        result = resolve_user("jsmith")

        assert len(result) == 1
        assert result[0]["username"] == "jsmith"

    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_for_jql_datacenter(self, mock_is_cloud):
        """Test JQL resolution on Data Center returns input unchanged."""
        mock_is_cloud.return_value = False

        assert resolve_user_for_jql("jsmith") == "jsmith"

    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_for_jql_accountid_passthrough(self, mock_is_cloud):
        """Test JQL resolution with an accountId passes through."""
        mock_is_cloud.return_value = True

        result = resolve_user_for_jql("5ecff4d72490cf0c09e48bd5")

        assert result == "5ecff4d72490cf0c09e48bd5"

    @patch("skills.jira.scripts.jira.resolve_user")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_for_jql_email(self, mock_is_cloud, mock_resolve):
        """Test JQL resolution resolves email to accountId on Cloud."""
        mock_is_cloud.return_value = True
        mock_resolve.return_value = [
            {
                "accountId": "abc123",
                "emailAddress": "jdoe@example.com",
                "displayName": "Jane Doe",
                "active": True,
            }
        ]

        result = resolve_user_for_jql("jdoe@example.com")

        assert result == "abc123"

    @patch("skills.jira.scripts.jira.resolve_user")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_for_jql_not_found(self, mock_is_cloud, mock_resolve):
        """Test JQL resolution raises ValueError when user not found."""
        mock_is_cloud.return_value = True
        mock_resolve.return_value = []

        with pytest.raises(ValueError, match="Could not find Jira Cloud user"):
            resolve_user_for_jql("nobody@example.com")

    @patch("skills.jira.scripts.jira.resolve_user")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_for_jql_prefers_email_match(self, mock_is_cloud, mock_resolve):
        """Test JQL resolution prefers exact email match."""
        mock_is_cloud.return_value = True
        mock_resolve.return_value = [
            {
                "accountId": "other",
                "emailAddress": "jdoe2@example.com",
                "displayName": "Jane Doe 2",
                "active": True,
            },
            {
                "accountId": "exact",
                "emailAddress": "jdoe@example.com",
                "displayName": "Jane Doe",
                "active": True,
            },
        ]

        result = resolve_user_for_jql("jdoe@example.com")

        assert result == "exact"

    @patch("skills.jira.scripts.jira.resolve_user")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_for_jql_falls_back_to_active(self, mock_is_cloud, mock_resolve):
        """Test JQL resolution falls back to first active user when no email match."""
        mock_is_cloud.return_value = True
        mock_resolve.return_value = [
            {
                "accountId": "inactive1",
                "emailAddress": "",
                "displayName": "Old User",
                "active": False,
            },
            {
                "accountId": "active1",
                "emailAddress": "",
                "displayName": "Jane Doe",
                "active": True,
            },
        ]

        result = resolve_user_for_jql("Jane Doe")

        assert result == "active1"

    @patch("skills.jira.scripts.jira.resolve_user")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_resolve_user_for_jql_falls_back_to_first(self, mock_is_cloud, mock_resolve):
        """Test JQL resolution falls back to first user when none active."""
        mock_is_cloud.return_value = True
        mock_resolve.return_value = [
            {
                "accountId": "only1",
                "emailAddress": "",
                "displayName": "Deactivated",
                "active": False,
            },
        ]

        result = resolve_user_for_jql("Deactivated")

        assert result == "only1"

    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_resolve_user_cloud_empty_response(self, mock_api_path, mock_get, mock_is_cloud):
        """Test resolve_user returns empty list when API returns non-list."""
        mock_is_cloud.return_value = True
        mock_api_path.return_value = "rest/api/3/user/search"
        mock_get.return_value = {}

        result = resolve_user("nobody")

        assert result == []


class TestContributorSearch:
    """Tests for contributor search."""

    @patch("skills.jira.scripts.jira.resolve_user_for_jql")
    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_search_by_contributor_with_scriptrunner(self, mock_search, mock_sr, mock_resolve):
        """Test contributor search with ScriptRunner available."""
        mock_resolve.return_value = "jsmith"
        mock_sr.return_value = {"available": True, "enhanced_search": True}
        mock_search.return_value = [{"key": "DEMO-1"}]

        result = search_by_contributor("jsmith")

        assert len(result) == 1
        jql = mock_search.call_args[0][0]
        assert 'reporter = "jsmith"' in jql
        assert 'assignee = "jsmith"' in jql
        assert 'commentedByUser("jsmith")' in jql

    @patch("skills.jira.scripts.jira.resolve_user_for_jql")
    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_search_by_contributor_without_scriptrunner(
        self, mock_search, mock_sr, mock_resolve, capsys
    ):
        """Test contributor search without ScriptRunner."""
        mock_resolve.return_value = "jsmith"
        mock_sr.return_value = {"available": False, "enhanced_search": False}
        mock_search.return_value = []

        search_by_contributor("jsmith")

        captured = capsys.readouterr()
        assert "ScriptRunner" in captured.err
        jql = mock_search.call_args[0][0]
        assert "commentedByUser" not in jql

    @patch("skills.jira.scripts.jira.resolve_user_for_jql")
    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_search_by_contributor_with_project(self, mock_search, mock_sr, mock_resolve):
        """Test contributor search scoped to a project."""
        mock_resolve.return_value = "jsmith"
        mock_sr.return_value = {"available": False, "enhanced_search": False}
        mock_search.return_value = []

        search_by_contributor("jsmith", project="DEMO")

        jql = mock_search.call_args[0][0]
        assert "project = DEMO" in jql

    @patch("skills.jira.scripts.jira.resolve_user_for_jql")
    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.search_issues")
    def test_search_by_contributor_resolves_email(self, mock_search, mock_sr, mock_resolve):
        """Test contributor search resolves email to accountId on Cloud."""
        mock_resolve.return_value = "abc123"
        mock_sr.return_value = {"available": False, "enhanced_search": False}
        mock_search.return_value = []

        search_by_contributor("jdoe@example.com")

        mock_resolve.assert_called_once_with("jdoe@example.com")
        jql = mock_search.call_args[0][0]
        assert 'reporter = "abc123"' in jql
        assert 'assignee = "abc123"' in jql

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


class TestCmdUser:
    """Tests for cmd_user handler."""

    @patch("skills.jira.scripts.jira.resolve_user")
    def test_cmd_user_search(self, mock_resolve, capsys):
        """Test user search command."""
        mock_resolve.return_value = [
            {
                "accountId": "abc123",
                "emailAddress": "jdoe@example.com",
                "displayName": "Jane Doe",
                "active": True,
            }
        ]

        args = argparse.Namespace(
            user_command="search",
            query="jdoe@example.com",
            json=False,
        )

        result = cmd_user(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "abc123" in captured.out
        assert "Jane Doe" in captured.out

    @patch("skills.jira.scripts.jira.resolve_user")
    def test_cmd_user_search_empty(self, mock_resolve, capsys):
        """Test user search with no results."""
        mock_resolve.return_value = []

        args = argparse.Namespace(
            user_command="search",
            query="nobody",
            json=False,
        )

        result = cmd_user(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No users found" in captured.out

    @patch("skills.jira.scripts.jira.resolve_user")
    @patch("skills.jira.scripts.jira.format_json")
    def test_cmd_user_search_json(self, mock_format_json, mock_resolve, capsys):
        """Test user search with JSON output."""
        mock_resolve.return_value = [{"accountId": "abc123"}]
        mock_format_json.return_value = '[{"accountId": "abc123"}]'

        args = argparse.Namespace(
            user_command="search",
            query="jdoe",
            json=True,
        )

        result = cmd_user(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "abc123" in captured.out

    @patch("skills.jira.scripts.jira.resolve_user")
    def test_cmd_user_search_error(self, mock_resolve, capsys):
        """Test user search with error."""
        mock_resolve.side_effect = Exception("API error")

        args = argparse.Namespace(
            user_command="search",
            query="jdoe",
            json=False,
        )

        result = cmd_user(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "API error" in captured.err


class TestScriptRunnerQueryGating:
    """Tests for ScriptRunner query rejection behavior."""

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_search_rejects_scriptrunner_on_cloud(self, mock_is_cloud, mock_scriptrunner, capsys):
        """ScriptRunner queries on Cloud should be rejected with a clear error."""
        mock_is_cloud.return_value = True
        mock_scriptrunner.return_value = {
            "available": False,
            "enhanced_search": False,
            "type": "cloud",
        }

        result = search_issues('issue in linkedIssuesOf("DEMO-123")', max_results=10)

        assert result == []
        captured = capsys.readouterr()
        assert "not supported on Jira Cloud" in captured.err
        assert "linkedIssuesOf" in captured.err

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_search_allows_scriptrunner_on_dc_with_plugin(
        self, mock_api_path, mock_get, mock_is_cloud, mock_scriptrunner
    ):
        """ScriptRunner queries on DC with plugin installed should proceed."""
        mock_is_cloud.return_value = False
        mock_scriptrunner.return_value = {
            "available": True,
            "enhanced_search": True,
            "type": "datacenter",
        }
        mock_api_path.return_value = "rest/api/2/search"
        mock_get.return_value = {
            "issues": [{"key": "DEMO-1", "fields": {"summary": "Test"}}],
            "total": 1,
        }

        result = search_issues('issue in linkedIssuesOf("DEMO-123")', max_results=10)

        assert len(result) == 1
        assert result[0]["key"] == "DEMO-1"

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    @patch("skills.jira.scripts.jira.is_cloud")
    def test_search_rejects_scriptrunner_on_dc_without_plugin(
        self, mock_is_cloud, mock_scriptrunner, capsys
    ):
        """ScriptRunner queries on DC without plugin should be rejected."""
        mock_is_cloud.return_value = False
        mock_scriptrunner.return_value = {
            "available": False,
            "enhanced_search": False,
            "type": "datacenter",
        }

        result = search_issues('issue in subtasksOf("DEMO-456")', max_results=10)

        assert result == []
        captured = capsys.readouterr()
        assert "not available on this instance" in captured.err
        assert "subtasksOf" in captured.err

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    def test_validate_jql_no_scriptrunner_functions(self, mock_scriptrunner):
        """Standard JQL should not trigger ScriptRunner validation."""
        mock_scriptrunner.return_value = {
            "available": False,
            "enhanced_search": False,
            "type": "cloud",
        }

        result = validate_jql_for_scriptrunner("project = DEMO AND status = Open")

        assert result["uses_scriptrunner"] is False
        assert result["functions_detected"] == []

    @patch("skills.jira.scripts.jira.detect_scriptrunner_support")
    def test_validate_jql_warning_does_not_recommend_install(self, mock_scriptrunner):
        """Warning message should not recommend installing ScriptRunner."""
        mock_scriptrunner.return_value = {
            "available": False,
            "enhanced_search": False,
            "type": "datacenter",
        }

        result = validate_jql_for_scriptrunner('issue in linkedIssuesOf("DEMO-123")')

        assert result["uses_scriptrunner"] is True
        assert not result["supported"]
        assert "Install" not in (result["warning"] or "")
        assert "Marketplace" not in (result["warning"] or "")


class TestParseIssueFile:
    """Tests for parse_issue_file()."""

    def test_full_frontmatter_and_body(self, tmp_path):
        """Test file with all frontmatter keys and a body."""
        f = tmp_path / "issue.md"
        f.write_text(
            "---\n"
            "summary: My issue\n"
            "project: DEMO\n"
            "type: Task\n"
            "priority: High\n"
            "labels:\n"
            "  - bug\n"
            "  - urgent\n"
            "assignee: abc123\n"
            "fields:\n"
            "  story_points: 5\n"
            "---\n"
            "This is the description.\n"
            "\n"
            "It has **multiple** paragraphs.\n"
        )
        fields, body = parse_issue_file(str(f))
        assert fields["summary"] == "My issue"
        assert fields["project"] == "DEMO"
        assert fields["type"] == "Task"
        assert fields["priority"] == "High"
        assert fields["labels"] == ["bug", "urgent"]
        assert fields["assignee"] == "abc123"
        assert fields["fields"] == {"story_points": 5}
        assert "multiple" in body

    def test_minimal_frontmatter(self, tmp_path):
        """Test file with only summary in frontmatter."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Just a title\n---\nBody text.\n")
        fields, body = parse_issue_file(str(f))
        assert fields["summary"] == "Just a title"
        assert body == "Body text."

    def test_no_body(self, tmp_path):
        """Test file with frontmatter only, no body."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: No body\n---\n")
        fields, body = parse_issue_file(str(f))
        assert fields["summary"] == "No body"
        assert body is None

    def test_labels_as_string(self, tmp_path):
        """Test labels as comma-separated string are converted to list."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Test\nlabels: bug, urgent, fix\n---\n")
        fields, _ = parse_issue_file(str(f))
        assert fields["labels"] == ["bug", "urgent", "fix"]

    def test_labels_as_list(self, tmp_path):
        """Test labels as YAML list are preserved."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Test\nlabels:\n  - bug\n  - urgent\n---\n")
        fields, _ = parse_issue_file(str(f))
        assert fields["labels"] == ["bug", "urgent"]

    def test_custom_fields(self, tmp_path):
        """Test frontmatter with fields mapping."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Test\nfields:\n  story_points: 8\n---\n")
        fields, _ = parse_issue_file(str(f))
        assert fields["fields"] == {"story_points": 8}

    def test_file_not_found(self):
        """Test non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_issue_file("/nonexistent/path/issue.md")

    def test_no_frontmatter(self, tmp_path):
        """Test file without frontmatter delimiters raises ValueError."""
        f = tmp_path / "issue.md"
        f.write_text("Just plain text, no frontmatter.\n")
        with pytest.raises(ValueError, match="must start with"):
            parse_issue_file(str(f))

    def test_invalid_yaml(self, tmp_path):
        """Test malformed YAML in frontmatter raises ValueError."""
        f = tmp_path / "issue.md"
        f.write_text("---\n: invalid: yaml: {{{\n---\n")
        with pytest.raises(ValueError, match="invalid YAML"):
            parse_issue_file(str(f))

    def test_empty_frontmatter(self, tmp_path):
        """Test empty frontmatter raises ValueError."""
        f = tmp_path / "issue.md"
        f.write_text("---\n---\nBody text.\n")
        with pytest.raises(ValueError, match="frontmatter is empty"):
            parse_issue_file(str(f))

    def test_missing_closing_delimiter(self, tmp_path):
        """Test missing closing --- raises ValueError."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Test\nno closing delimiter\n")
        with pytest.raises(ValueError, match="missing closing"):
            parse_issue_file(str(f))

    def test_unrecognized_keys_warn(self, tmp_path, capsys):
        """Test unrecognized frontmatter keys produce a warning."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Test\nunknown_key: value\n---\n")
        fields, _ = parse_issue_file(str(f))
        assert fields["summary"] == "Test"
        captured = capsys.readouterr()
        assert "unrecognized frontmatter keys" in captured.err
        assert "unknown_key" in captured.err

    def test_numeric_summary_coerced_to_string(self, tmp_path):
        """Test numeric values in string fields are coerced to strings."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: 12345\npriority: 1\n---\n")
        fields, _ = parse_issue_file(str(f))
        assert fields["summary"] == "12345"
        assert fields["priority"] == "1"


class TestFromFileIntegration:
    """Tests for --from-file integration in cmd_issue()."""

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_from_file(
        self, mock_parse, mock_jira_defaults, mock_proj_defaults, mock_create
    ):
        """Test issue create from file with all required fields."""
        mock_parse.return_value = (
            {"summary": "From file", "project": "DEMO", "type": "Story"},
            "File description",
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-456"}

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 0
        mock_create.assert_called_once_with(
            project="DEMO",
            issue_type="Story",
            summary="From file",
            description="File description",
            priority=None,
            labels=None,
            assignee=None,
            extra_fields=None,
        )

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_from_file_cli_override(
        self, mock_parse, mock_jira_defaults, mock_proj_defaults, mock_create
    ):
        """Test CLI args override frontmatter values."""
        mock_parse.return_value = (
            {"summary": "File summary", "project": "DEMO", "type": "Story"},
            "File desc",
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-789"}

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary="CLI summary",
            description=None,
            priority="Critical",
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 0
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["summary"] == "CLI summary"
        assert call_kwargs["priority"] == "Critical"

    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_from_file_missing_project(
        self, mock_parse, mock_jira_defaults, mock_proj_defaults, capsys
    ):
        """Test error when project missing from both CLI and frontmatter."""
        mock_parse.return_value = (
            {"summary": "No project", "type": "Task"},
            "Body",
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "--project is required" in captured.err

    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_from_file_missing_summary(
        self, mock_parse, mock_jira_defaults, mock_proj_defaults, capsys
    ):
        """Test error when summary missing from both CLI and frontmatter."""
        mock_parse.return_value = (
            {"project": "DEMO", "type": "Task"},
            None,
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "--summary is required" in captured.err

    def test_create_from_file_conflict_description(self, capsys):
        """Test error when both --from-file and --description provided."""
        args = argparse.Namespace(
            issue_command="create",
            project="DEMO",
            issue_type="Task",
            summary="Test",
            description="Inline desc",
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "--from-file and --description cannot be used together" in captured.err

    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_from_file_not_found(self, mock_parse, capsys):
        """Test error when --from-file path does not exist."""
        mock_parse.side_effect = FileNotFoundError("File not found: missing.md")

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
            from_file="missing.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "file not found" in captured.err

    @patch("skills.jira.scripts.jira.update_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_update_from_file(self, mock_parse, mock_jira_defaults, mock_update, capsys):
        """Test issue update from file."""
        mock_parse.return_value = (
            {"summary": "Updated title", "priority": "Low"},
            "New description",
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_update.return_value = {}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            from_file="update.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 0
        mock_update.assert_called_once_with(
            issue_key="DEMO-123",
            summary="Updated title",
            description="New description",
            priority="Low",
            labels=None,
            assignee=None,
            extra_fields=None,
        )
        captured = capsys.readouterr()
        assert "Updated issue: DEMO-123" in captured.out

    @patch("skills.jira.scripts.jira.update_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_update_from_file_ignores_project_type(
        self, mock_parse, mock_jira_defaults, mock_update
    ):
        """Test update silently ignores project and type from frontmatter."""
        mock_parse.return_value = (
            {"summary": "Test", "project": "IGNORED", "type": "IGNORED"},
            None,
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_update.return_value = {}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            from_file="update.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 0
        call_kwargs = mock_update.call_args[1]
        assert "project" not in call_kwargs
        assert "type" not in call_kwargs

    def test_update_from_file_conflict_description(self, capsys):
        """Test error when both --from-file and --description on update."""
        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary=None,
            description="Inline",
            priority=None,
            labels=None,
            assignee=None,
            from_file="update.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "--from-file and --description cannot be used together" in captured.err

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_from_file_with_labels(
        self, mock_parse, mock_jira_defaults, mock_proj_defaults, mock_create
    ):
        """Test labels from frontmatter are passed correctly."""
        mock_parse.return_value = (
            {
                "summary": "Test",
                "project": "DEMO",
                "type": "Task",
                "labels": ["bug", "urgent"],
            },
            None,
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-100"}

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 0
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["labels"] == ["bug", "urgent"]

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_create_no_file_no_project_errors(
        self, mock_jira_defaults, mock_proj_defaults, _mock_create, capsys
    ):
        """Test that required fields are still enforced without --from-file."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type="Task",
            summary="Test",
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file=None,
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "--project is required" in captured.err

    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_create_no_file_no_summary_errors(
        self, mock_jira_defaults, mock_proj_defaults, _mock_create, capsys
    ):
        """Test that summary is still required without --from-file."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()

        args = argparse.Namespace(
            issue_command="create",
            project="DEMO",
            issue_type="Task",
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file=None,
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "--summary is required" in captured.err


class TestCreateErrorHints:
    """Tests for helpful error messages on create failures."""

    @patch("skills.jira.scripts.jira.get_project_issue_types")
    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_400_shows_valid_issue_types(
        self, mock_jira_defaults, mock_proj_defaults, mock_create, mock_types, capsys
    ):
        """Test that a 400 error on create shows valid issue types."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.side_effect = APIError(
            "POST failed: 400 Bad Request", status_code=400, response='{"errors":{}}'
        )
        mock_types.return_value = ["Task", "Bug", "Epic", "Feature"]

        args = argparse.Namespace(
            issue_command="create",
            project="DEMO",
            issue_type="Story",
            summary="Test",
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file=None,
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "Valid issue types for DEMO" in captured.err
        assert "Task" in captured.err
        assert "Feature" in captured.err

    @patch("skills.jira.scripts.jira.get_project_issue_types")
    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_from_file_400_shows_valid_issue_types(
        self,
        mock_parse,
        mock_jira_defaults,
        mock_proj_defaults,
        mock_create,
        mock_types,
        capsys,
    ):
        """Test that a 400 error on create from file shows valid issue types."""
        mock_parse.return_value = (
            {"summary": "Test", "project": "PROJ", "type": "InvalidType"},
            "Body",
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.side_effect = APIError(
            "POST failed: 400 Bad Request", status_code=400, response='{"errors":{}}'
        )
        mock_types.return_value = ["Task", "Bug"]

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
        )

        result = cmd_issue(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "Valid issue types for PROJ" in captured.err


class TestIssueLinking:
    """Tests for issue link functions."""

    SAMPLE_LINK_TYPES = [
        {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
        {"name": "Relates", "inward": "relates to", "outward": "relates to"},
        {"name": "Cloners", "inward": "is cloned by", "outward": "clones"},
    ]

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.api_path")
    def test_get_link_types(self, mock_api_path, mock_get):
        """Test fetching link types."""
        mock_api_path.return_value = "rest/api/3/issueLinkType"
        mock_get.return_value = {
            "issueLinkTypes": [
                {"name": "Blocks", "inward": "is blocked by", "outward": "blocks", "id": "1"},
            ]
        }
        result = get_link_types()
        assert len(result) == 1
        assert result[0]["name"] == "Blocks"
        assert result[0]["outward"] == "blocks"
        assert result[0]["inward"] == "is blocked by"

    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.get_link_types")
    def test_create_link_outward(self, mock_types, mock_api_path, mock_post):
        """Test creating a link using outward name."""
        mock_types.return_value = self.SAMPLE_LINK_TYPES
        mock_api_path.return_value = "rest/api/3/issueLink"
        mock_post.return_value = {}

        create_link("SRC-1", "blocks", "TGT-2")

        mock_post.assert_called_once()
        payload = mock_post.call_args[0][2]
        assert payload["type"]["name"] == "Blocks"
        assert payload["outwardIssue"]["key"] == "SRC-1"
        assert payload["inwardIssue"]["key"] == "TGT-2"

    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.get_link_types")
    def test_create_link_inward_swaps_direction(self, mock_types, mock_api_path, mock_post):
        """Test that using inward name swaps issue direction."""
        mock_types.return_value = self.SAMPLE_LINK_TYPES
        mock_api_path.return_value = "rest/api/3/issueLink"
        mock_post.return_value = {}

        create_link("SRC-1", "is blocked by", "TGT-2")

        payload = mock_post.call_args[0][2]
        assert payload["type"]["name"] == "Blocks"
        assert payload["outwardIssue"]["key"] == "TGT-2"
        assert payload["inwardIssue"]["key"] == "SRC-1"

    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.get_link_types")
    def test_create_link_by_type_name(self, mock_types, mock_api_path, mock_post):
        """Test creating a link using the type name directly."""
        mock_types.return_value = self.SAMPLE_LINK_TYPES
        mock_api_path.return_value = "rest/api/3/issueLink"
        mock_post.return_value = {}

        create_link("SRC-1", "Blocks", "TGT-2")

        payload = mock_post.call_args[0][2]
        assert payload["type"]["name"] == "Blocks"
        assert payload["outwardIssue"]["key"] == "SRC-1"

    @patch("skills.jira.scripts.jira.get_link_types")
    def test_create_link_invalid_type(self, mock_types):
        """Test that unknown link type raises ValueError with valid types."""
        mock_types.return_value = self.SAMPLE_LINK_TYPES

        with pytest.raises(ValueError, match="Unknown link type 'InvalidType'") as exc_info:
            create_link("SRC-1", "InvalidType", "TGT-2")
        assert "Blocks" in str(exc_info.value)
        assert "Relates" in str(exc_info.value)

    @patch("skills.jira.scripts.jira.post")
    @patch("skills.jira.scripts.jira.api_path")
    @patch("skills.jira.scripts.jira.get_link_types")
    def test_create_link_case_insensitive(self, mock_types, mock_api_path, mock_post):
        """Test that link type matching is case-insensitive."""
        mock_types.return_value = self.SAMPLE_LINK_TYPES
        mock_api_path.return_value = "rest/api/3/issueLink"
        mock_post.return_value = {}

        create_link("SRC-1", "BLOCKS", "TGT-2")

        payload = mock_post.call_args[0][2]
        assert payload["type"]["name"] == "Blocks"


class TestParseLinkArgs:
    """Tests for _parse_link_args()."""

    def test_valid_links(self):
        """Test parsing valid link args."""
        result = _parse_link_args(["Blocks:DEMO-456", "Relates:DEMO-789"])
        assert result == [("Blocks", "DEMO-456"), ("Relates", "DEMO-789")]

    def test_none_returns_empty(self):
        """Test None input returns empty list."""
        assert _parse_link_args(None) == []

    def test_empty_list_returns_empty(self):
        """Test empty list returns empty list."""
        assert _parse_link_args([]) == []

    def test_missing_colon_returns_error(self):
        """Test missing colon returns error string."""
        result = _parse_link_args(["BadFormat"])
        assert isinstance(result, str)
        assert "TYPE:ISSUE" in result

    def test_empty_type_returns_error(self):
        """Test empty type part returns error."""
        result = _parse_link_args([":DEMO-456"])
        assert isinstance(result, str)

    def test_empty_issue_returns_error(self):
        """Test empty issue part returns error."""
        result = _parse_link_args(["Blocks:"])
        assert isinstance(result, str)

    def test_colon_in_value_preserved(self):
        """Test that only first colon is split on."""
        result = _parse_link_args(["Blocks:DEMO-456:extra"])
        assert result == [("Blocks", "DEMO-456:extra")]


class TestParseIssueFileLinks:
    """Tests for links in parse_issue_file() frontmatter."""

    def test_links_parsed(self, tmp_path):
        """Test links are normalized to tuples."""
        f = tmp_path / "issue.md"
        f.write_text(
            "---\nsummary: Test\nlinks:\n  - blocks: DEMO-456\n  - relates to: DEMO-789\n---\n"
        )
        fields, _ = parse_issue_file(str(f))
        assert fields["links"] == [("blocks", "DEMO-456"), ("relates to", "DEMO-789")]

    def test_links_not_list_raises(self, tmp_path):
        """Test non-list links value raises ValueError."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Test\nlinks: not-a-list\n---\n")
        with pytest.raises(ValueError, match="must be a list"):
            parse_issue_file(str(f))

    def test_links_bad_entry_raises(self, tmp_path):
        """Test link entry with multiple keys raises ValueError."""
        f = tmp_path / "issue.md"
        f.write_text(
            "---\nsummary: Test\nlinks:\n  - blocks: DEMO-1\n    relates to: DEMO-2\n---\n"
        )
        with pytest.raises(ValueError, match="single-key mapping"):
            parse_issue_file(str(f))

    def test_links_string_entry_raises(self, tmp_path):
        """Test link entry that is a plain string raises ValueError."""
        f = tmp_path / "issue.md"
        f.write_text("---\nsummary: Test\nlinks:\n  - just-a-string\n---\n")
        with pytest.raises(ValueError, match="single-key mapping"):
            parse_issue_file(str(f))


class TestCmdIssueLinkIntegration:
    """Tests for --link integration in cmd_issue()."""

    @patch("skills.jira.scripts.jira.create_link")
    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_create_with_links(
        self, mock_jira_defaults, mock_proj_defaults, mock_create, mock_link, capsys
    ):
        """Test issue create with --link args."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-100"}

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
            from_file=None,
            set_field=None,
            link=["Blocks:DEMO-456", "Relates:DEMO-789"],
        )

        result = cmd_issue(args)
        assert result == 0
        assert mock_link.call_count == 2
        mock_link.assert_any_call("DEMO-100", "Blocks", "DEMO-456")
        mock_link.assert_any_call("DEMO-100", "Relates", "DEMO-789")
        captured = capsys.readouterr()
        assert "Linked DEMO-100" in captured.out

    @patch("skills.jira.scripts.jira.create_link")
    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_from_file_with_links(
        self, mock_parse, mock_jira_defaults, mock_proj_defaults, mock_create, mock_link
    ):
        """Test issue create from file with links in frontmatter."""
        mock_parse.return_value = (
            {
                "summary": "Test",
                "project": "DEMO",
                "type": "Task",
                "links": [("blocks", "DEMO-456")],
            },
            None,
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-200"}

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
            link=None,
        )

        result = cmd_issue(args)
        assert result == 0
        mock_link.assert_called_once_with("DEMO-200", "blocks", "DEMO-456")

    @patch("skills.jira.scripts.jira.create_link")
    @patch("skills.jira.scripts.jira.update_issue")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_update_with_links(self, mock_jira_defaults, mock_update, mock_link, capsys):
        """Test issue update with --link args."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_update.return_value = {}

        args = argparse.Namespace(
            issue_command="update",
            issue_key="DEMO-123",
            summary="Updated",
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            from_file=None,
            set_field=None,
            link=["Blocks:DEMO-456"],
        )

        result = cmd_issue(args)
        assert result == 0
        mock_link.assert_called_once_with("DEMO-123", "Blocks", "DEMO-456")
        captured = capsys.readouterr()
        assert "Linked DEMO-123" in captured.out

    @patch("skills.jira.scripts.jira.create_link")
    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    def test_create_link_failure_continues(
        self, mock_jira_defaults, mock_proj_defaults, mock_create, mock_link, capsys
    ):
        """Test that a link failure doesn't fail the whole create."""
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-300"}
        mock_link.side_effect = [None, ValueError("Unknown link type 'Bad'")]

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
            from_file=None,
            set_field=None,
            link=["Blocks:DEMO-456", "Bad:DEMO-789"],
        )

        result = cmd_issue(args)
        assert result == 0
        assert mock_link.call_count == 2
        captured = capsys.readouterr()
        assert "Warning: failed to link to DEMO-789" in captured.err

    @patch("skills.jira.scripts.jira.create_link")
    @patch("skills.jira.scripts.jira.create_issue")
    @patch("skills.jira.scripts.jira.get_project_defaults")
    @patch("skills.jira.scripts.jira.get_jira_defaults")
    @patch("skills.jira.scripts.jira.parse_issue_file")
    def test_create_file_and_cli_links_additive(
        self, mock_parse, mock_jira_defaults, mock_proj_defaults, mock_create, mock_link
    ):
        """Test that frontmatter and CLI links are both applied."""
        mock_parse.return_value = (
            {
                "summary": "Test",
                "project": "DEMO",
                "type": "Task",
                "links": [("blocks", "DEMO-1")],
            },
            None,
        )
        mock_jira_defaults.return_value = JiraDefaults()
        mock_proj_defaults.return_value = ProjectDefaults()
        mock_create.return_value = {"key": "DEMO-400"}

        args = argparse.Namespace(
            issue_command="create",
            project=None,
            issue_type=None,
            summary=None,
            description=None,
            priority=None,
            labels=None,
            assignee=None,
            json=False,
            from_file="issue.md",
            set_field=None,
            link=["Relates:DEMO-2"],
        )

        result = cmd_issue(args)
        assert result == 0
        assert mock_link.call_count == 2
        mock_link.assert_any_call("DEMO-400", "blocks", "DEMO-1")
        mock_link.assert_any_call("DEMO-400", "Relates", "DEMO-2")


# ============================================================================
# AUTOMATION RULES
# ============================================================================


class TestGetCloudId:
    """Tests for get_cloud_id function."""

    @patch("skills.jira.scripts.jira.requests.get")
    @patch("skills.jira.scripts.jira.is_cloud", return_value=True)
    @patch("skills.jira.scripts.jira.get_credentials")
    def test_fetches_and_caches_cloud_id(self, mock_creds, _mock_is_cloud, mock_get):
        """Test successful Cloud ID fetch and caching."""
        mock_creds.return_value = Credentials(
            url="https://test.atlassian.net", token="tok", email="a@b.com"
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"cloudId": "abc-123"}
        mock_get.return_value = mock_response

        clear_cache()
        result = get_cloud_id()

        assert result == "abc-123"
        mock_get.assert_called_once_with("https://test.atlassian.net/_edge/tenant_info", timeout=10)

        # Second call should use cache
        mock_get.reset_mock()
        result2 = get_cloud_id()
        assert result2 == "abc-123"
        mock_get.assert_not_called()
        clear_cache()

    @patch("skills.jira.scripts.jira.is_cloud", return_value=False)
    def test_raises_on_dc(self, _mock_is_cloud):
        """Test that DC/Server raises APIError."""
        with pytest.raises(APIError, match="only available on Jira Cloud"):
            get_cloud_id()

    @patch("skills.jira.scripts.jira.requests.get")
    @patch("skills.jira.scripts.jira.is_cloud", return_value=True)
    @patch("skills.jira.scripts.jira.get_credentials")
    def test_raises_on_http_error(self, mock_creds, _mock_is_cloud, mock_get):
        """Test HTTP error raises APIError."""
        mock_creds.return_value = Credentials(
            url="https://test.atlassian.net", token="tok", email="a@b.com"
        )
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "access denied"
        mock_get.return_value = mock_response

        clear_cache()
        with pytest.raises(APIError, match="Failed to fetch Cloud ID"):
            get_cloud_id()
        clear_cache()


class TestAutomationPath:
    """Tests for automation_path function."""

    @patch("skills.jira.scripts.jira.get_cloud_id", return_value="cloud-xyz")
    def test_constructs_gateway_path(self, _mock_cloud_id):
        """Test correct gateway path construction."""
        result = automation_path("rule/summary")
        assert result == "gateway/api/automation/public/jira/cloud-xyz/rest/v1/rule/summary"

    @patch("skills.jira.scripts.jira.get_cloud_id", return_value="cloud-xyz")
    def test_strips_leading_slash(self, _mock_cloud_id):
        """Test leading slash is stripped from endpoint."""
        result = automation_path("/rule/summary")
        assert result == "gateway/api/automation/public/jira/cloud-xyz/rest/v1/rule/summary"


class TestListAutomationRules:
    """Tests for list_automation_rules function."""

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.automation_path")
    def test_list_all_rules(self, mock_path, mock_get):
        """Test listing all rules."""
        mock_path.return_value = "gateway/api/automation/public/jira/cid/rest/v1/rule/summary"
        mock_get.return_value = {
            "data": [
                {"name": "Rule 1", "state": "ENABLED", "uuid": "u1", "ruleScopeARIs": []},
                {"name": "Rule 2", "state": "DISABLED", "uuid": "u2", "ruleScopeARIs": []},
            ],
            "links": {},
        }

        rules = list_automation_rules()
        assert len(rules) == 2
        assert rules[0]["name"] == "Rule 1"

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.automation_path")
    def test_filter_by_state(self, mock_path, mock_get):
        """Test filtering by state."""
        mock_path.return_value = "gateway/path"
        mock_get.return_value = {
            "data": [
                {"name": "Rule 1", "state": "ENABLED", "uuid": "u1", "ruleScopeARIs": []},
                {"name": "Rule 2", "state": "DISABLED", "uuid": "u2", "ruleScopeARIs": []},
            ],
            "links": {},
        }

        rules = list_automation_rules(state="ENABLED")
        assert len(rules) == 1
        assert rules[0]["name"] == "Rule 1"

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.automation_path")
    @patch("skills.jira.scripts.jira.api_path")
    def test_filter_by_project(self, mock_api_path, mock_auto_path, mock_get):
        """Test filtering by project key."""
        mock_auto_path.return_value = "gateway/path"
        mock_api_path.return_value = "rest/api/3/project/DEMO"

        def side_effect(_service, endpoint, **_kwargs):
            if "project/DEMO" in endpoint:
                return {"id": "10001"}
            return {
                "data": [
                    {
                        "name": "Rule 1",
                        "state": "ENABLED",
                        "uuid": "u1",
                        "ruleScopeARIs": ["ari:cloud:jira:site:project/10001"],
                    },
                    {
                        "name": "Rule 2",
                        "state": "ENABLED",
                        "uuid": "u2",
                        "ruleScopeARIs": ["ari:cloud:jira:site:project/99999"],
                    },
                ],
                "links": {},
            }

        mock_get.side_effect = side_effect

        rules = list_automation_rules(project_key="DEMO")
        assert len(rules) == 1
        assert rules[0]["name"] == "Rule 1"


class TestGetAutomationRule:
    """Tests for get_automation_rule function."""

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.automation_path")
    def test_fetches_rule_by_uuid(self, mock_path, mock_get):
        """Test fetching a single rule by UUID."""
        mock_path.return_value = "gateway/path/rule/test-uuid"
        mock_get.return_value = {
            "rule": {"uuid": "test-uuid", "name": "My Rule"},
            "connections": [],
        }

        result = get_automation_rule("test-uuid")
        assert result["rule"]["name"] == "My Rule"
        mock_path.assert_called_once_with("rule/test-uuid")


class TestFormatAutomationSummary:
    """Tests for format_automation_summary function."""

    def test_basic_summary(self):
        """Test basic summary formatting."""
        rule = {
            "name": "Auto-assign bugs",
            "state": "ENABLED",
            "authorAccountId": "user-123",
            "labels": ["bugs", "triage"],
            "uuid": "abc-def",
            "ruleScopeARIs": ["ari:cloud:jira:site:project/10001"],
        }

        result = format_automation_summary(rule)
        assert "### Auto-assign bugs" in result
        assert "ON (ENABLED)" in result
        assert "user-123" in result
        assert "bugs, triage" in result
        assert "`abc-def`" in result

    def test_disabled_state(self):
        """Test disabled state shows OFF."""
        rule = {
            "name": "Old rule",
            "state": "DISABLED",
            "authorAccountId": "user-1",
            "uuid": "xyz",
            "ruleScopeARIs": [],
        }

        result = format_automation_summary(rule)
        assert "OFF (DISABLED)" in result


class TestFormatAutomationDetail:
    """Tests for format_automation_detail function."""

    def test_full_rule_formatting(self):
        """Test formatting a complete rule definition."""
        rule_config = {
            "rule": {
                "name": "Assign critical bugs",
                "description": "Auto-assigns critical bugs to the on-call engineer.",
                "state": "ENABLED",
                "authorAccountId": "user-123",
                "labels": ["triage"],
                "ruleScopeARIs": ["ari:cloud:jira:site:project/10001"],
                "created": 1705305600.0,
                "updated": 1717977600.0,
                "notifyOnError": "FIRSTERROR",
                "writeAccessType": "OWNER_ONLY",
                "canOtherRuleTrigger": True,
                "collaborators": [],
                "trigger": {
                    "type": "jira.issue.event.trigger:created",
                    "value": '{"issueType": "Bug"}',
                    "component": "TRIGGER",
                    "conditions": [
                        {
                            "type": "jira.condition.field",
                            "value": '{"fieldId": "priority", "compareValue": "Critical"}',
                            "component": "CONDITION",
                        }
                    ],
                },
                "components": [
                    {
                        "type": "jira.issue.assign.action",
                        "value": '{"accountId": "oncall-user"}',
                        "component": "ACTION",
                        "conditions": [],
                        "children": [],
                    },
                    {
                        "type": "jira.issue.comment.action",
                        "value": '{"body": "Auto-triaged as critical"}',
                        "component": "ACTION",
                        "conditions": [],
                        "children": [],
                    },
                ],
            },
            "connections": [],
        }

        result = format_automation_detail(rule_config)
        assert "## Assign critical bugs" in result
        assert "ON (ENABLED)" in result
        assert "user-123" in result
        assert "### Trigger" in result
        assert "Issue created" in result
        assert "### Actions" in result
        assert "Assign issue" in result
        assert "Add comment" in result
        assert "Auto-triaged as critical" in result

    def test_empty_rule(self):
        """Test formatting a minimal rule."""
        rule_config = {"rule": {"name": "Empty", "state": "DISABLED"}, "connections": []}

        result = format_automation_detail(rule_config)
        assert "## Empty" in result
        assert "OFF (DISABLED)" in result


class TestFormatTimestamp:
    """Tests for _format_timestamp helper."""

    def test_seconds_timestamp(self):
        """Test Unix timestamp in seconds."""
        result = _format_timestamp(1705305600.0)
        assert "2024-01-15" in result

    def test_milliseconds_timestamp(self):
        """Test Unix timestamp in milliseconds."""
        result = _format_timestamp(1705305600000.0)
        assert "2024-01-15" in result


class TestFormatComponent:
    """Tests for _format_component helper."""

    def test_known_type(self):
        """Test component with a known type key."""
        comp = {"type": "jira.issue.event.trigger:created", "value": None}
        result = _format_component(comp, prefix="**When:**")
        assert "**When:** Issue created" in result

    def test_value_parsing(self):
        """Test JSON value is parsed and summarised."""
        comp = {
            "type": "jira.condition.jql",
            "value": '{"jql": "priority = Critical"}',
        }
        result = _format_component(comp)
        assert "JQL condition" in result
        assert "priority = Critical" in result

    def test_unknown_type_fallback(self):
        """Test unknown type gets human-readable fallback."""
        comp = {"type": "com.example.custom.action", "value": None}
        result = _format_component(comp)
        assert result  # should not crash


class TestHumaniseComponentType:
    """Tests for _humanise_component_type function."""

    def test_known_types(self):
        """Test known type mappings."""
        assert _humanise_component_type("jira.issue.event.trigger:created") == "Issue created"
        assert _humanise_component_type("jira.issue.create.action") == "Create issue"
        assert _humanise_component_type("jira.condition.jql") == "JQL condition"

    def test_unknown_type_fallback(self):
        """Test fallback formatting for unknown types."""
        result = _humanise_component_type("jira.custom.thing.action:fired")
        assert isinstance(result, str)
        assert len(result) > 0


class TestSummariseValue:
    """Tests for _summarise_value function."""

    def test_string_value(self):
        """Test string passthrough."""
        assert _summarise_value("hello") == "hello"

    def test_dict_with_jql(self):
        """Test dict with JQL field."""
        result = _summarise_value({"jql": "project = DEMO"})
        assert "project = DEMO" in result

    def test_dict_with_nested_display(self):
        """Test dict with nested displayName."""
        result = _summarise_value({"fieldValue": {"displayName": "Critical"}})
        assert "Critical" in result

    def test_empty_dict_fallback(self):
        """Test empty dict gets JSON fallback."""
        result = _summarise_value({"unknownKey": 42})
        assert "42" in result


class TestFormatScopeAri:
    """Tests for _format_scope_ari function."""

    def test_project_scope(self):
        """Test project ARI formatting."""
        result = _format_scope_ari("ari:cloud:jira:site-id:project/10001")
        assert "Project #10001" in result

    def test_global_scope(self):
        """Test global scope ARI."""
        result = _format_scope_ari("ari:cloud:jira:site-id:site")
        assert "Global (site)" in result

    def test_unknown_scope(self):
        """Test unknown ARI returns as-is."""
        result = _format_scope_ari("ari:cloud:jira:site-id:other/thing")
        assert result == "ari:cloud:jira:site-id:other/thing"


class TestCmdAutomations:
    """Tests for cmd_automations handler."""

    @patch("skills.jira.scripts.jira.list_automation_rules")
    def test_list_rules(self, mock_list, capsys):
        """Test automations list command."""
        mock_list.return_value = [
            {
                "name": "Rule 1",
                "state": "ENABLED",
                "authorAccountId": "user-1",
                "uuid": "u1",
                "ruleScopeARIs": [],
            }
        ]

        args = argparse.Namespace(
            automations_command="list",
            project=None,
            state=None,
            limit=100,
            json=False,
        )

        result = cmd_automations(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Rule 1" in captured.out
        assert "1 automation rule(s)" in captured.out

    @patch("skills.jira.scripts.jira.list_automation_rules")
    def test_list_empty(self, mock_list, capsys):
        """Test automations list with no results."""
        mock_list.return_value = []

        args = argparse.Namespace(
            automations_command="list",
            project=None,
            state=None,
            limit=100,
            json=False,
        )

        result = cmd_automations(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "No automation rules found" in captured.out

    @patch("skills.jira.scripts.jira.get_automation_rule")
    def test_get_rule(self, mock_get, capsys):
        """Test automations get command."""
        mock_get.return_value = {
            "rule": {
                "name": "Test Rule",
                "state": "ENABLED",
                "authorAccountId": "user-1",
                "trigger": {
                    "type": "jira.issue.event.trigger:created",
                    "component": "TRIGGER",
                    "conditions": [],
                },
                "components": [],
            },
            "connections": [],
        }

        args = argparse.Namespace(
            automations_command="get",
            uuid="test-uuid",
            json=False,
        )

        result = cmd_automations(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Test Rule" in captured.out
        assert "Issue created" in captured.out

    @patch("skills.jira.scripts.jira.list_automation_rules")
    def test_list_error(self, mock_list, capsys):
        """Test automations list with API error."""
        mock_list.side_effect = APIError("Automation rules are only available on Jira Cloud")

        args = argparse.Namespace(
            automations_command="list",
            project=None,
            state=None,
            limit=100,
            json=False,
        )

        result = cmd_automations(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "only available on Jira Cloud" in captured.err


class TestListAutomationRulesPagination:
    """Tests for list_automation_rules pagination."""

    @patch("skills.jira.scripts.jira.get")
    @patch("skills.jira.scripts.jira.automation_path")
    def test_pagination(self, mock_path, mock_get):
        """Test automatic pagination through results."""
        mock_path.return_value = "gateway/path"
        mock_get.side_effect = [
            {
                "data": [{"name": "Rule 1", "state": "ENABLED", "uuid": "u1", "ruleScopeARIs": []}],
                "links": {"next": "?cursor=abc123&limit=100"},
            },
            {
                "data": [{"name": "Rule 2", "state": "ENABLED", "uuid": "u2", "ruleScopeARIs": []}],
                "links": {},
            },
        ]

        rules = list_automation_rules()
        assert len(rules) == 2
        assert rules[0]["name"] == "Rule 1"
        assert rules[1]["name"] == "Rule 2"


class TestFormatAutomationDetailComplex:
    """Tests for format_automation_detail with complex rule structures."""

    def test_branches_and_connections(self):
        """Test formatting rules with branches and connections."""
        rule_config = {
            "rule": {
                "name": "Complex Rule",
                "state": "ENABLED",
                "authorAccountId": "user-1",
                "trigger": {
                    "type": "jira.issue.event.trigger:updated",
                    "component": "TRIGGER",
                    "conditions": [],
                },
                "components": [
                    {
                        "type": "jira.condition.jql",
                        "value": '{"jql": "priority = High"}',
                        "component": "CONDITION",
                        "conditions": [
                            {
                                "type": "jira.condition.field",
                                "value": '{"fieldId": "status"}',
                                "component": "CONDITION",
                            }
                        ],
                    },
                    {
                        "type": "jira.branch.action",
                        "value": None,
                        "component": "BRANCH",
                        "children": [
                            {
                                "type": "jira.issue.assign.action",
                                "value": '{"accountId": "user-2"}',
                                "component": "ACTION",
                            }
                        ],
                        "conditions": [
                            {
                                "type": "jira.condition.field",
                                "value": '{"fieldId": "issuetype"}',
                                "component": "CONDITION",
                            }
                        ],
                    },
                    {
                        "type": "custom.unknown.component",
                        "value": None,
                        "component": "CUSTOM",
                    },
                ],
            },
            "connections": [
                {
                    "connectionTargetKey": "com.atlassian.confluence.native",
                    "authType": "OAUTH_3LO",
                }
            ],
        }

        result = format_automation_detail(rule_config)
        assert "### Conditions" in result
        assert "### Branches" in result
        assert "### Connections" in result
        assert "### Other Components" in result
        assert "confluence.native" in result
        assert "OAUTH_3LO" in result
        assert "**And:**" in result

    def test_actions_with_conditions_and_children(self):
        """Test actions that have nested conditions and children."""
        rule_config = {
            "rule": {
                "name": "Nested Actions",
                "state": "ENABLED",
                "authorAccountId": "user-1",
                "components": [
                    {
                        "type": "jira.issue.edit.action",
                        "value": '{"summary": "Updated"}',
                        "component": "ACTION",
                        "conditions": [
                            {
                                "type": "jira.condition.field",
                                "value": '{"fieldId": "priority"}',
                                "component": "CONDITION",
                            }
                        ],
                        "children": [
                            {
                                "type": "jira.issue.comment.action",
                                "value": '{"body": "Sub-action"}',
                                "component": "ACTION",
                            }
                        ],
                    },
                ],
            },
            "connections": [],
        }

        result = format_automation_detail(rule_config)
        assert "### Actions" in result
        assert "Edit issue" in result
        assert "**If:**" in result
        assert "**→**" in result


class TestSummariseValueEdgeCases:
    """Tests for _summarise_value edge cases."""

    def test_list_value(self):
        """Test list input."""
        result = _summarise_value(["a", "b", "c"])
        assert "a" in result
        assert "b" in result

    def test_non_dict_non_string(self):
        """Test numeric input."""
        result = _summarise_value(42)
        assert "42" in result

    def test_dict_with_nested_no_display(self):
        """Test dict with nested object lacking displayName."""
        result = _summarise_value({"value": {"custom": "data"}})
        assert "custom" in result

    def test_dict_with_list_field(self):
        """Test dict with list-typed value field."""
        result = _summarise_value({"value": [{"displayName": "A"}, {"name": "B"}]})
        assert "A" in result


class TestGetCloudIdNoUrl:
    """Test get_cloud_id when no URL is configured."""

    @patch("skills.jira.scripts.jira.is_cloud", return_value=True)
    @patch("skills.jira.scripts.jira.get_credentials")
    def test_raises_no_url(self, mock_creds, _mock_is_cloud):
        """Test error when no URL is configured."""
        mock_creds.return_value = Credentials()

        clear_cache()
        with pytest.raises(APIError, match="No Jira URL configured"):
            get_cloud_id()

    @patch("skills.jira.scripts.jira.requests.get")
    @patch("skills.jira.scripts.jira.is_cloud", return_value=True)
    @patch("skills.jira.scripts.jira.get_credentials")
    def test_raises_no_cloud_id_in_response(self, mock_creds, _mock_is_cloud, mock_get):
        """Test error when tenant_info returns no cloudId."""
        mock_creds.return_value = Credentials(
            url="https://test.atlassian.net", token="tok", email="a@b.com"
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        clear_cache()
        with pytest.raises(APIError, match="Could not determine Cloud ID"):
            get_cloud_id()
        clear_cache()


class TestCmdAutomationsGet:
    """Tests for cmd_automations get with JSON output."""

    @patch("skills.jira.scripts.jira.get_automation_rule")
    @patch("skills.jira.scripts.jira.format_json")
    def test_get_json_output(self, mock_format_json, mock_get, capsys):
        """Test automations get with JSON output."""
        mock_get.return_value = {"rule": {"name": "R"}, "connections": []}
        mock_format_json.return_value = '{"rule": {"name": "R"}}'

        args = argparse.Namespace(
            automations_command="get",
            uuid="test-uuid",
            json=True,
        )

        result = cmd_automations(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "R" in captured.out

    @patch("skills.jira.scripts.jira.get_automation_rule")
    def test_get_error(self, mock_get, capsys):
        """Test automations get with error and response body."""
        err = APIError("Not found", status_code=404, response="rule not found")
        mock_get.side_effect = err

        args = argparse.Namespace(
            automations_command="get",
            uuid="bad-uuid",
            json=False,
        )

        result = cmd_automations(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "Not found" in captured.err
