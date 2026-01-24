"""Tests for confluence.py skill."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

# Import from skills module
from skills.confluence.scripts.confluence import (
    ConfluenceDefaults,
    Credentials,
    SpaceDefaults,
    _html_to_markdown,
    _inline_markdown_to_html,
    _truncate,
    adf_to_markdown,
    delete_credential,
    format_json,
    get_credential,
    load_config,
    markdown_to_adf,
    markdown_to_storage,
    merge_cql_with_scope,
    save_config,
    set_credential,
    storage_to_markdown,
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

    @patch("skills.confluence.scripts.confluence.keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch("skills.confluence.scripts.confluence.keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch("skills.confluence.scripts.confluence.keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")


class TestConfigManagement:
    """Tests for configuration management."""

    def test_load_config_success(self, tmp_path):
        """Test loading configuration from file."""
        config_dir = tmp_path / ".config" / "agent-skills"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "confluence.yaml"
        config_file.write_text("url: https://example.com\ntoken: abc123")

        with patch("skills.confluence.scripts.confluence.CONFIG_DIR", config_dir):
            config = load_config("confluence")
            assert config == {"url": "https://example.com", "token": "abc123"}

    def test_load_config_not_found(self, tmp_path):
        """Test loading non-existent config returns None."""
        config_dir = tmp_path / ".config" / "agent-skills"
        with patch("skills.confluence.scripts.confluence.CONFIG_DIR", config_dir):
            assert load_config("confluence") is None

    def test_save_config(self, tmp_path):
        """Test saving configuration to file."""
        config_dir = tmp_path / ".config" / "agent-skills"
        with patch("skills.confluence.scripts.confluence.CONFIG_DIR", config_dir):
            config = {"url": "https://example.com", "token": "abc123"}
            save_config("confluence", config)

            # Verify file was created
            config_file = config_dir / "confluence.yaml"
            assert config_file.exists()
            content = config_file.read_text()
            assert "url: https://example.com" in content
            assert "token: abc123" in content


class TestDefaults:
    """Tests for defaults dataclasses."""

    def test_confluence_defaults_empty(self):
        """Test ConfluenceDefaults from empty config."""
        defaults = ConfluenceDefaults.from_config({})
        assert defaults.cql_scope is None
        assert defaults.max_results is None

    def test_confluence_defaults_full(self):
        """Test ConfluenceDefaults from full config."""
        config = {
            "defaults": {
                "cql_scope": "type=page AND space=DEMO",
                "max_results": 25,
                "fields": ["title", "space"],
                "default_space": "DEMO",
            }
        }
        defaults = ConfluenceDefaults.from_config(config)
        assert defaults.cql_scope == "type=page AND space=DEMO"
        assert defaults.max_results == 25
        assert defaults.fields == ["title", "space"]
        assert defaults.default_space == "DEMO"

    def test_space_defaults_empty(self):
        """Test SpaceDefaults from empty config."""
        defaults = SpaceDefaults.from_config({}, "DEMO")
        assert defaults.default_parent is None
        assert defaults.default_labels is None

    def test_space_defaults_configured(self):
        """Test SpaceDefaults from configured space."""
        config = {
            "spaces": {
                "DEMO": {
                    "default_parent": "Parent Page",
                    "default_labels": ["docs", "test"],
                }
            }
        }
        defaults = SpaceDefaults.from_config(config, "DEMO")
        assert defaults.default_parent == "Parent Page"
        assert defaults.default_labels == ["docs", "test"]


class TestMarkdownConversion:
    """Tests for markdown/storage/ADF conversion."""

    def test_markdown_to_storage_basic(self):
        """Test basic markdown to storage format conversion."""
        markdown = "# Heading\n\nSome **bold** text."
        storage = markdown_to_storage(markdown)

        assert "<h1>Heading</h1>" in storage
        assert "<strong>bold</strong>" in storage

    def test_storage_to_markdown_basic(self):
        """Test basic storage format to markdown conversion."""
        storage = "<h1>Heading</h1><p>Some <strong>bold</strong> text.</p>"
        markdown = storage_to_markdown(storage)

        assert "# Heading" in markdown
        assert "**bold**" in markdown

    def test_markdown_to_adf_heading(self):
        """Test markdown to ADF format conversion."""
        markdown = "# Heading 1\n\n## Heading 2"
        adf = markdown_to_adf(markdown)

        assert adf["type"] == "doc"
        assert adf["version"] == 1
        # Check for heading nodes
        headings = [node for node in adf["content"] if node.get("type") == "heading"]
        assert len(headings) == 2
        assert headings[0]["attrs"]["level"] == 1
        assert headings[1]["attrs"]["level"] == 2

    def test_adf_to_markdown_heading(self):
        """Test ADF to markdown conversion."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Heading 1"}],
                }
            ],
        }
        markdown = adf_to_markdown(adf)
        assert "# Heading 1" in markdown

    def test_inline_markdown_bold(self):
        """Test inline markdown bold conversion."""
        text = "This is **bold** text"
        html = _inline_markdown_to_html(text)
        assert "<strong>bold</strong>" in html

    def test_inline_markdown_italic(self):
        """Test inline markdown italic conversion."""
        text = "This is *italic* text"
        html = _inline_markdown_to_html(text)
        assert "<em>italic</em>" in html

    def test_inline_markdown_code(self):
        """Test inline markdown code conversion."""
        text = "This is `code` text"
        html = _inline_markdown_to_html(text)
        assert "<code>code</code>" in html

    def test_html_to_markdown_bold(self):
        """Test HTML bold to markdown conversion."""
        html = "This is <strong>bold</strong> text"
        markdown = _html_to_markdown(html)
        assert "**bold**" in markdown

    def test_html_to_markdown_link(self):
        """Test HTML link to markdown conversion."""
        html = '<a href="https://example.com">link</a>'
        markdown = _html_to_markdown(html)
        assert "[link](https://example.com)" in markdown

    def test_markdown_to_storage_list(self):
        """Test markdown list to storage conversion."""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        storage = markdown_to_storage(markdown)
        assert "<ul>" in storage or "<li>" in storage

    def test_markdown_to_adf_paragraph(self):
        """Test markdown paragraph to ADF conversion."""
        markdown = "This is a paragraph."
        adf = markdown_to_adf(markdown)
        assert adf["type"] == "doc"
        paragraphs = [node for node in adf["content"] if node.get("type") == "paragraph"]
        assert len(paragraphs) >= 1

    def test_adf_to_markdown_paragraph(self):
        """Test ADF paragraph to markdown conversion."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "This is a paragraph."}],
                }
            ],
        }
        markdown = adf_to_markdown(adf)
        assert "This is a paragraph" in markdown


class TestCQLScope:
    """Tests for CQL scope merging."""

    def test_merge_cql_with_scope_both_present(self):
        """Test merging user CQL with scope."""
        user_cql = "type=page"
        scope = "space=DEMO"
        result = merge_cql_with_scope(user_cql, scope)
        assert result == "(space=DEMO) AND (type=page)"

    def test_merge_cql_no_scope(self):
        """Test CQL without scope."""
        user_cql = "type=page"
        result = merge_cql_with_scope(user_cql, None)
        assert result == "type=page"

    def test_merge_cql_empty_user_cql(self):
        """Test scope only, no user CQL."""
        scope = "space=DEMO"
        result = merge_cql_with_scope("", scope)
        assert result == "space=DEMO"

    def test_merge_cql_both_empty(self):
        """Test both empty."""
        result = merge_cql_with_scope("", None)
        assert result == ""

    def test_merge_cql_whitespace_scope(self):
        """Test whitespace-only scope."""
        result = merge_cql_with_scope("type=page", "   ")
        assert result == "type=page"

    def test_merge_cql_preserves_or(self):
        """Test that OR precedence is preserved."""
        user_cql = "type=page OR type=blogpost"
        scope = "space=DEMO"
        result = merge_cql_with_scope(user_cql, scope)
        expected = "(space=DEMO) AND (type=page OR type=blogpost)"
        assert result == expected


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_json(self):
        """Test JSON formatting."""
        data = {"key": "value", "number": 123}
        result = format_json(data)
        assert '"key": "value"' in result
        assert '"number": 123' in result

    def test_truncate_short_text(self):
        """Test truncating text shorter than limit."""
        text = "Short text"
        result = _truncate(text, 50)
        assert result == "Short text"

    def test_truncate_long_text(self):
        """Test truncating long text."""
        text = "A" * 100
        result = _truncate(text, 50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_truncate_exact_length(self):
        """Test truncating text exactly at limit."""
        text = "A" * 50
        result = _truncate(text, 50)
        assert result == text

    def test_format_json_pretty(self):
        """Test JSON formatting with indentation."""
        data = {"nested": {"key": "value"}}
        result = format_json(data, indent=2)
        assert "  " in result  # Check for indentation
        assert "nested" in result


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_markdown_conversion_roundtrip(self):
        """Test markdown -> storage -> markdown conversion."""
        original = "# Heading\n\nSome **bold** text with a [link](https://example.com)."
        storage = markdown_to_storage(original)
        converted = storage_to_markdown(storage)

        # Check key elements are preserved
        assert "Heading" in converted
        assert "bold" in converted or "<strong>bold</strong>" in storage

    def test_adf_conversion_roundtrip(self):
        """Test markdown -> ADF -> markdown conversion."""
        original = "# Heading\n\nParagraph text."
        adf = markdown_to_adf(original)
        converted = adf_to_markdown(adf)

        # Check key elements are preserved
        assert "Heading" in converted
        assert "Paragraph text" in converted or "Paragraph" in converted


class TestCredentialRetrieval:
    """Tests for credential retrieval priority chain."""

    @patch("skills.confluence.scripts.confluence.get_credential")
    @patch("skills.confluence.scripts.confluence.os.getenv")
    @patch("skills.confluence.scripts.confluence.load_config")
    def test_get_credentials_keyring_priority(
        self, mock_load_config, mock_getenv, mock_get_credential
    ):
        """Test that keyring has highest priority."""
        from skills.confluence.scripts.confluence import get_credentials

        mock_get_credential.side_effect = lambda key: {
            "confluence-url": "https://keyring.example.com",
            "confluence-token": "keyring-token",
        }.get(key)
        mock_getenv.return_value = None
        mock_load_config.return_value = None

        creds = get_credentials("confluence")
        assert creds.url == "https://keyring.example.com"
        assert creds.token == "keyring-token"

    @patch("skills.confluence.scripts.confluence.get_credential")
    @patch.dict("os.environ", {}, clear=True)
    @patch("skills.confluence.scripts.confluence.load_config")
    def test_get_credentials_env_fallback(self, mock_load_config, mock_get_credential):
        """Test environment variable fallback."""
        import os

        from skills.confluence.scripts.confluence import get_credentials

        mock_get_credential.return_value = None
        mock_load_config.return_value = None

        # Set test environment variables
        os.environ["CONFLUENCE_URL"] = "https://env.example.com"
        os.environ["CONFLUENCE_API_TOKEN"] = "env-token"

        creds = get_credentials("confluence")
        assert creds.url == "https://env.example.com"
        assert creds.token == "env-token"

    @patch("skills.confluence.scripts.confluence.get_credential")
    @patch.dict("os.environ", {}, clear=True)
    @patch("skills.confluence.scripts.confluence.load_config")
    def test_get_credentials_config_file(self, mock_load_config, mock_get_credential):
        """Test config file as last resort."""
        from skills.confluence.scripts.confluence import get_credentials

        mock_get_credential.return_value = None
        mock_load_config.return_value = {
            "url": "https://config.example.com",
            "token": "config-token",
        }

        creds = get_credentials("confluence")
        assert creds.url == "https://config.example.com"
        assert creds.token == "config-token"


class TestDeploymentDetection:
    """Tests for deployment type detection."""

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_detect_cloud_deployment(self, mock_creds, mock_request):
        """Test detecting Confluence Cloud."""
        from skills.confluence.scripts.confluence import clear_cache, detect_deployment_type

        mock_creds.return_value = Credentials(url="https://example.atlassian.net", token="test")
        mock_request.return_value = {
            "baseUrl": "https://example.atlassian.net",
            "deploymentType": "Cloud",
        }
        clear_cache()

        deployment = detect_deployment_type(force_refresh=True)
        assert deployment.lower() == "cloud"

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_detect_server_deployment(self, mock_creds, mock_request):
        """Test detecting Confluence Server."""
        from skills.confluence.scripts.confluence import clear_cache, detect_deployment_type

        mock_creds.return_value = Credentials(url="https://example.com/confluence", token="test")
        mock_request.return_value = {
            "baseUrl": "https://example.com/confluence",
            "deploymentType": "Server",
        }
        clear_cache()

        deployment = detect_deployment_type(force_refresh=True)
        assert deployment.lower() == "server"

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_detect_datacenter_deployment(self, mock_creds, mock_request):
        """Test detecting Confluence Data Center."""
        from skills.confluence.scripts.confluence import clear_cache, detect_deployment_type

        mock_creds.return_value = Credentials(url="https://example.com/confluence", token="test")
        mock_request.return_value = {
            "baseUrl": "https://example.com/confluence",
            "deploymentType": "Data Center",
        }
        clear_cache()

        deployment = detect_deployment_type(force_refresh=True)
        # Confluence treats Data Center same as Server
        assert deployment.lower() in ["datacenter", "data center", "server"]


class TestAPIFunctions:
    """Tests for API wrapper functions."""

    @patch("skills.confluence.scripts.confluence.get")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_search_content_success(self, mock_get_api_base, mock_get):
        """Test successful content search."""
        from skills.confluence.scripts.confluence import search_content

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_get.return_value = {
            "results": [
                {"id": "1", "title": "Page 1", "type": "page"},
                {"id": "2", "title": "Page 2", "type": "page"},
            ],
            "size": 2,
        }

        results = search_content("type=page", max_results=10)
        assert len(results) == 2
        assert results[0]["title"] == "Page 1"

    @patch("skills.confluence.scripts.confluence.get")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_get_page_by_id(self, mock_get_api_base, mock_get):
        """Test getting page by ID."""
        from skills.confluence.scripts.confluence import get_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_get.return_value = {
            "id": "123",
            "title": "Test Page",
            "body": {"storage": {"value": "<p>Content</p>"}},
        }

        page = get_page("123")
        assert page["id"] == "123"
        assert page["title"] == "Test Page"

    @patch("skills.confluence.scripts.confluence.get")
    @patch("skills.confluence.scripts.confluence.search_content")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_get_page_by_title(self, mock_get_api_base, mock_search, mock_get):
        """Test getting page by title."""
        from skills.confluence.scripts.confluence import get_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_search.return_value = [{"id": "456", "title": "Test Page"}]
        mock_get.return_value = {
            "id": "456",
            "title": "Test Page",
            "body": {"storage": {"value": "<p>Content</p>"}},
        }

        page = get_page("Test Page")
        assert page["id"] == "456"
        assert page["title"] == "Test Page"

    @patch("skills.confluence.scripts.confluence.post")
    @patch("skills.confluence.scripts.confluence.is_cloud")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_create_page_cloud(self, mock_get_api_base, mock_is_cloud, mock_post):
        """Test creating page on Cloud."""
        from skills.confluence.scripts.confluence import create_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_is_cloud.return_value = True
        mock_post.return_value = {
            "id": "789",
            "title": "New Page",
            "type": "page",
        }

        page = create_page("DEMO", "New Page", "# Content")
        assert page["id"] == "789"
        assert page["title"] == "New Page"

    @patch("skills.confluence.scripts.confluence.put")
    @patch("skills.confluence.scripts.confluence.get_page")
    @patch("skills.confluence.scripts.confluence.is_cloud")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_update_page(self, mock_get_api_base, mock_is_cloud, mock_get_page, mock_put):
        """Test updating a page."""
        from skills.confluence.scripts.confluence import update_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_is_cloud.return_value = True
        mock_get_page.return_value = {
            "id": "123",
            "title": "Old Title",
            "version": {"number": 1},
            "space": {"key": "DEMO"},
        }
        mock_put.return_value = {
            "id": "123",
            "title": "New Title",
            "version": {"number": 2},
        }

        page = update_page("123", title="New Title")
        assert page["title"] == "New Title"
        assert page["version"]["number"] == 2


class TestFormatFunctions:
    """Tests for page formatting functions."""

    def test_format_page(self):
        """Test page formatting."""
        from skills.confluence.scripts.confluence import format_page

        page = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "space": {"key": "DEMO", "name": "Demo Space"},
            "version": {"number": 5, "when": "2024-01-01T12:00:00Z"},
            "body": {"storage": {"value": "<p>Content</p>"}},
        }

        result = format_page(page)
        assert "Test Page" in result
        assert "DEMO" in result
        assert "123" in result

    def test_format_pages_list(self):
        """Test formatting list of pages."""
        from skills.confluence.scripts.confluence import format_pages_list

        pages = [
            {
                "id": "1",
                "title": "Page 1",
                "type": "page",
                "space": {"key": "DEMO"},
            },
            {
                "id": "2",
                "title": "Page 2",
                "type": "page",
                "space": {"key": "DEMO"},
            },
        ]

        result = format_pages_list(pages)
        assert "Page 1" in result
        assert "Page 2" in result

    def test_format_content_markdown_to_storage(self):
        """Test format_content conversion."""
        from skills.confluence.scripts.confluence import format_content

        result = format_content("# Heading", input_format="markdown", output_format="storage")
        assert "Heading" in str(result)

    def test_format_content_markdown_to_editor(self):
        """Test format_content conversion to editor format."""
        from skills.confluence.scripts.confluence import format_content

        result = format_content("# Heading", input_format="markdown", output_format="editor")
        assert isinstance(result, dict)
        assert result.get("type") == "doc"


class TestGetConfluenceDefaults:
    """Tests for get_confluence_defaults and get_space_defaults."""

    @patch("skills.confluence.scripts.confluence.load_config")
    def test_get_confluence_defaults(self, mock_load_config):
        """Test getting confluence defaults."""
        from skills.confluence.scripts.confluence import get_confluence_defaults

        mock_load_config.return_value = {
            "defaults": {
                "cql_scope": "space=DEMO",
                "max_results": 50,
            }
        }

        defaults = get_confluence_defaults()
        assert defaults.cql_scope == "space=DEMO"
        assert defaults.max_results == 50

    @patch("skills.confluence.scripts.confluence.load_config")
    def test_get_space_defaults(self, mock_load_config):
        """Test getting space-specific defaults."""
        from skills.confluence.scripts.confluence import get_space_defaults

        mock_load_config.return_value = {
            "spaces": {
                "DEMO": {
                    "default_parent": "Parent Page",
                    "default_labels": ["docs"],
                }
            }
        }

        defaults = get_space_defaults("DEMO")
        assert defaults.default_parent == "Parent Page"
        assert defaults.default_labels == ["docs"]


class TestAPIPathAndBase:
    """Tests for API path generation."""

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_get_api_base_cloud(self, mock_creds, mock_request):
        """Test API base for Cloud."""
        from skills.confluence.scripts.confluence import clear_cache, get_api_base

        mock_creds.return_value = Credentials(url="https://example.atlassian.net", token="test")
        mock_request.return_value = {
            "baseUrl": "https://example.atlassian.net",
            "deploymentType": "Cloud",
        }
        clear_cache()

        base = get_api_base()
        assert base == "/wiki/rest/api"

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_get_api_base_server(self, mock_creds, mock_request):
        """Test API base for Server."""
        from skills.confluence.scripts.confluence import clear_cache, get_api_base

        mock_creds.return_value = Credentials(url="https://example.com/confluence", token="test")
        mock_request.return_value = {
            "baseUrl": "https://example.com/confluence",
            "deploymentType": "Server",
        }
        clear_cache()

        base = get_api_base()
        assert base == "/rest/api"

    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_api_path(self, mock_get_api_base):
        """Test API path generation."""
        from skills.confluence.scripts.confluence import api_path

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"

        path = api_path("/rest/api/content")
        assert path == "https://example.atlassian.net/wiki/rest/api/content"

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_is_cloud_true(self, mock_creds, mock_request):
        """Test is_cloud returns True for Cloud."""
        from skills.confluence.scripts.confluence import clear_cache, is_cloud

        mock_creds.return_value = Credentials(url="https://example.atlassian.net", token="test")
        mock_request.return_value = {
            "baseUrl": "https://example.atlassian.net",
            "deploymentType": "Cloud",
        }
        clear_cache()

        assert is_cloud() is True

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_is_cloud_false(self, mock_creds, mock_request):
        """Test is_cloud returns False for Server."""
        from skills.confluence.scripts.confluence import clear_cache, is_cloud

        mock_creds.return_value = Credentials(url="https://example.com/confluence", token="test")
        mock_request.return_value = {
            "baseUrl": "https://example.com/confluence",
            "deploymentType": "Server",
        }
        clear_cache()

        assert is_cloud() is False


class TestCommandHandlers:
    """Tests for CLI command handlers."""

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.detect_deployment_type")
    @patch("skills.confluence.scripts.confluence.get")
    def test_cmd_check_success(self, mock_get, mock_detect, mock_creds):
        """Test successful check command."""

        from skills.confluence.scripts.confluence import cmd_check

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
        mock_detect.return_value = "Cloud"
        mock_get.return_value = {"results": []}

        result = cmd_check()
        assert result == 0

    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_cmd_check_no_url(self, mock_creds):
        """Test check command with missing URL."""
        from skills.confluence.scripts.confluence import cmd_check

        mock_creds.return_value = Credentials(token="test123")
        result = cmd_check()
        assert result == 1

    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_cmd_check_no_token(self, mock_creds):
        """Test check command with missing token."""
        from skills.confluence.scripts.confluence import cmd_check

        mock_creds.return_value = Credentials(url="https://example.atlassian.net")
        result = cmd_check()
        assert result == 1

    @patch("skills.confluence.scripts.confluence.search_content")
    @patch("skills.confluence.scripts.confluence.get_confluence_defaults")
    def test_cmd_search_text_output(self, mock_defaults, mock_search):
        """Test search command with text output."""
        import argparse

        from skills.confluence.scripts.confluence import ConfluenceDefaults, cmd_search

        mock_defaults.return_value = ConfluenceDefaults()
        mock_search.return_value = [
            {"id": "1", "title": "Page 1", "type": "page", "space": {"key": "DEMO"}},
            {"id": "2", "title": "Page 2", "type": "page", "space": {"key": "DEMO"}},
        ]

        args = argparse.Namespace(
            cql="type=page",
            max_results=None,
            type=None,
            space=None,
            json=False,
        )

        result = cmd_search(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.search_content")
    @patch("skills.confluence.scripts.confluence.get_confluence_defaults")
    def test_cmd_search_json_output(self, mock_defaults, mock_search):
        """Test search command with JSON output."""
        import argparse

        from skills.confluence.scripts.confluence import ConfluenceDefaults, cmd_search

        mock_defaults.return_value = ConfluenceDefaults()
        mock_search.return_value = [
            {"id": "1", "title": "Page 1", "type": "page"},
        ]

        args = argparse.Namespace(
            cql="type=page",
            max_results=10,
            type=None,
            space=None,
            json=True,
        )

        result = cmd_search(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.search_content")
    @patch("skills.confluence.scripts.confluence.get_confluence_defaults")
    def test_cmd_search_with_scope(self, mock_defaults, mock_search):
        """Test search command with configured scope."""
        import argparse

        from skills.confluence.scripts.confluence import ConfluenceDefaults, cmd_search

        mock_defaults.return_value = ConfluenceDefaults(
            cql_scope="space=DEMO", max_results=25, default_space="DEMO"
        )
        mock_search.return_value = []

        args = argparse.Namespace(
            cql="type=page",
            max_results=None,
            type=None,
            space=None,
            json=False,
        )

        result = cmd_search(args)
        assert result == 0
        # Verify merged CQL was passed
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[0][0] == "(space=DEMO) AND (type=page)"

    @patch("skills.confluence.scripts.confluence.get_page")
    def test_cmd_page_get_text(self, mock_get_page):
        """Test page get command with text output."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_get_page.return_value = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {"storage": {"value": "<p>Content</p>"}},
        }

        args = argparse.Namespace(
            page_command="get",
            page_identifier="123",
            json=False,
            markdown=False,
            raw=False,
            no_body=False,
            expand=None,
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.get_page")
    def test_cmd_page_get_json(self, mock_get_page):
        """Test page get command with JSON output."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_get_page.return_value = {
            "id": "123",
            "title": "Test Page",
        }

        args = argparse.Namespace(
            page_command="get",
            page_identifier="Test Page",
            json=True,
            markdown=False,
            raw=False,
            no_body=False,
            expand="body.storage,version",
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.create_page")
    @patch("skills.confluence.scripts.confluence.get_space_defaults")
    def test_cmd_page_create(self, mock_space_defaults, mock_create):
        """Test page create command."""
        import argparse

        from skills.confluence.scripts.confluence import SpaceDefaults, cmd_page

        mock_space_defaults.return_value = SpaceDefaults()
        mock_create.return_value = {
            "id": "456",
            "title": "New Page",
            "_links": {"webui": "/wiki/spaces/DEMO/pages/456"},
        }

        args = argparse.Namespace(
            page_command="create",
            space="DEMO",
            title="New Page",
            body="# Content",
            body_file=None,
            format="markdown",
            parent=None,
            labels=None,
            json=False,
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.create_page")
    @patch("skills.confluence.scripts.confluence.get_space_defaults")
    def test_cmd_page_create_with_file(self, mock_space_defaults, mock_create, tmp_path):
        """Test page create command with body from file."""
        import argparse

        from skills.confluence.scripts.confluence import SpaceDefaults, cmd_page

        mock_space_defaults.return_value = SpaceDefaults()
        mock_create.return_value = {"id": "456", "title": "New Page", "_links": {"webui": "/"}}

        # Create temp file
        body_file = tmp_path / "content.md"
        body_file.write_text("# Test Content")

        args = argparse.Namespace(
            page_command="create",
            space="DEMO",
            title="New Page",
            body=None,
            body_file=str(body_file),
            format="markdown",
            parent="123",
            labels="docs,test",
            json=True,
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.update_page")
    def test_cmd_page_update(self, mock_update):
        """Test page update command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_update.return_value = {
            "id": "123",
            "version": {"number": 2},
        }

        args = argparse.Namespace(
            page_command="update",
            page_id="123",
            title="Updated Title",
            body="# Updated content",
            body_file=None,
            format="markdown",
            version=None,
            json=False,
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.list_spaces")
    def test_cmd_space_list(self, mock_list):
        """Test space list command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_list.return_value = [
            {"key": "DEMO", "name": "Demo Space", "type": "global"},
            {"key": "TEST", "name": "Test Space", "type": "global"},
        ]

        args = argparse.Namespace(
            space_command="list",
            type=None,
            max_results=None,
            json=False,
        )

        result = cmd_space(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.list_spaces")
    def test_cmd_space_list_empty(self, mock_list):
        """Test space list command with no results."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_list.return_value = []

        args = argparse.Namespace(
            space_command="list",
            type="personal",
            max_results=10,
            json=False,
        )

        result = cmd_space(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.get_space")
    def test_cmd_space_get(self, mock_get):
        """Test space get command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_get.return_value = {
            "key": "DEMO",
            "name": "Demo Space",
            "type": "global",
            "description": {"plain": {"value": "Test description"}},
        }

        args = argparse.Namespace(
            space_command="get",
            space_key="DEMO",
            expand=None,
            json=False,
        )

        result = cmd_space(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.create_space")
    def test_cmd_space_create(self, mock_create):
        """Test space create command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_create.return_value = {
            "key": "NEW",
            "name": "New Space",
        }

        args = argparse.Namespace(
            space_command="create",
            key="NEW",
            name="New Space",
            description="Test description",
            type="global",
            json=False,
        )

        result = cmd_space(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.load_config")
    def test_cmd_config_show_no_config(self, mock_load):
        """Test config show with no config file."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_config

        mock_load.return_value = None

        args = argparse.Namespace(
            config_command="show",
            space=None,
        )

        result = cmd_config(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.load_config")
    def test_cmd_config_show_full(self, mock_load):
        """Test config show with full config."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_config

        mock_load.return_value = {
            "url": "https://example.atlassian.net",
            "email": "test@example.com",
            "token": "secret123",
            "defaults": {
                "cql_scope": "space=DEMO",
                "max_results": 50,
                "fields": ["title", "space"],
                "default_space": "DEMO",
            },
            "spaces": {
                "DEMO": {
                    "default_parent": "Parent",
                    "default_labels": ["docs"],
                }
            },
        }

        args = argparse.Namespace(
            config_command="show",
            space=None,
        )

        result = cmd_config(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.load_config")
    def test_cmd_config_show_specific_space(self, mock_load):
        """Test config show with specific space."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_config

        mock_load.return_value = {
            "url": "https://example.atlassian.net",
            "spaces": {
                "DEMO": {
                    "default_parent": "Parent",
                    "default_labels": ["docs", "test"],
                }
            },
        }

        args = argparse.Namespace(
            config_command="show",
            space="DEMO",
        )

        result = cmd_config(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.search_content")
    @patch("skills.confluence.scripts.confluence.get_confluence_defaults")
    def test_cmd_search_error(self, mock_defaults, mock_search):
        """Test search command with error."""
        import argparse

        from skills.confluence.scripts.confluence import ConfluenceDefaults, cmd_search

        mock_defaults.return_value = ConfluenceDefaults()
        mock_search.side_effect = Exception("API error")

        args = argparse.Namespace(
            cql="type=page",
            max_results=None,
            type=None,
            space=None,
            json=False,
        )

        result = cmd_search(args)
        assert result == 1

    @patch("skills.confluence.scripts.confluence.get_page")
    def test_cmd_page_get_error(self, mock_get_page):
        """Test page get command with error."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_get_page.side_effect = Exception("Page not found")

        args = argparse.Namespace(
            page_command="get",
            page_identifier="999",
            json=False,
            markdown=False,
            raw=False,
            no_body=False,
            expand=None,
        )

        result = cmd_page(args)
        assert result == 1

    @patch("skills.confluence.scripts.confluence.update_page")
    def test_cmd_page_update_with_file(self, mock_update, tmp_path):
        """Test page update with body from file."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_update.return_value = {
            "id": "123",
            "version": {"number": 2},
        }

        body_file = tmp_path / "update.md"
        body_file.write_text("# Updated Content")

        args = argparse.Namespace(
            page_command="update",
            page_id="123",
            title=None,
            body=None,
            body_file=str(body_file),
            format="markdown",
            version=1,
            json=True,
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.list_spaces")
    def test_cmd_space_list_json(self, mock_list):
        """Test space list with JSON output."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_list.return_value = [
            {"key": "DEMO", "name": "Demo Space", "type": "global"},
        ]

        args = argparse.Namespace(
            space_command="list",
            type=None,
            max_results=None,
            json=True,
        )

        result = cmd_space(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.get_space")
    def test_cmd_space_get_json(self, mock_get):
        """Test space get with JSON output."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_get.return_value = {
            "key": "DEMO",
            "name": "Demo Space",
        }

        args = argparse.Namespace(
            space_command="get",
            space_key="DEMO",
            expand="description",
            json=True,
        )

        result = cmd_space(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.create_space")
    def test_cmd_space_create_json(self, mock_create):
        """Test space create with JSON output."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_create.return_value = {
            "key": "NEW",
            "name": "New Space",
        }

        args = argparse.Namespace(
            space_command="create",
            key="NEW",
            name="New Space",
            description=None,
            type=None,
            json=True,
        )

        result = cmd_space(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.list_spaces")
    def test_cmd_space_error(self, mock_list):
        """Test space command with error."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_list.side_effect = Exception("API error")

        args = argparse.Namespace(
            space_command="list",
            type=None,
            max_results=None,
            json=False,
        )

        result = cmd_space(args)
        assert result == 1

    @patch("skills.confluence.scripts.confluence.load_config")
    def test_cmd_config_error(self, mock_load):
        """Test config command with error."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_config

        mock_load.side_effect = Exception("Config error")

        args = argparse.Namespace(
            config_command="show",
            space=None,
        )

        result = cmd_config(args)
        assert result == 1


class TestMarkdownEdgeCases:
    """Tests for markdown conversion edge cases."""

    def test_markdown_to_storage_ordered_list(self):
        """Test ordered list conversion."""
        from skills.confluence.scripts.confluence import markdown_to_storage

        markdown = "1. First\n2. Second\n3. Third"
        storage = markdown_to_storage(markdown)
        assert "<ol>" in storage
        assert "<li>First</li>" in storage
        assert "<li>Second</li>" in storage

    def test_markdown_to_storage_mixed_lists(self):
        """Test mixed ordered and unordered lists."""
        from skills.confluence.scripts.confluence import markdown_to_storage

        markdown = "- Bullet\n\n1. Number"
        storage = markdown_to_storage(markdown)
        assert "<ul>" in storage
        assert "<ol>" in storage

    def test_markdown_to_storage_code_with_language(self):
        """Test code block with language."""
        from skills.confluence.scripts.confluence import markdown_to_storage

        markdown = "```python\nprint('hello')\n```"
        storage = markdown_to_storage(markdown)
        assert "python" in storage
        assert "print" in storage

    def test_markdown_to_storage_code_no_language(self):
        """Test code block without language."""
        from skills.confluence.scripts.confluence import markdown_to_storage

        markdown = "```\ncode here\n```"
        storage = markdown_to_storage(markdown)
        assert "<pre>" in storage or "<code>" in storage

    def test_markdown_to_storage_nested_formatting(self):
        """Test nested formatting."""
        from skills.confluence.scripts.confluence import markdown_to_storage

        markdown = "**bold with *italic* inside**"
        storage = markdown_to_storage(markdown)
        assert "<strong>" in storage
        assert "<em>" in storage

    def test_storage_to_markdown_ordered_list(self):
        """Test ordered list from storage."""
        from skills.confluence.scripts.confluence import storage_to_markdown

        storage = "<ol><li>First</li><li>Second</li></ol>"
        markdown = storage_to_markdown(storage)
        assert "1. First" in markdown
        assert "2. Second" in markdown

    def test_storage_to_markdown_code_macro_with_language(self):
        """Test code macro with language."""
        from skills.confluence.scripts.confluence import storage_to_markdown

        storage = '<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">python</ac:parameter><ac:plain-text-body><![CDATA[print("hi")]]></ac:plain-text-body></ac:structured-macro>'
        markdown = storage_to_markdown(storage)
        assert "```python" in markdown
        assert 'print("hi")' in markdown

    def test_adf_to_markdown_ordered_list(self):
        """Test ordered list from ADF."""
        from skills.confluence.scripts.confluence import adf_to_markdown

        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "orderedList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "First"}],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Second"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        markdown = adf_to_markdown(adf)
        assert "1. First" in markdown
        assert "2. Second" in markdown

    def test_adf_to_markdown_code_block(self):
        """Test code block from ADF."""
        from skills.confluence.scripts.confluence import adf_to_markdown

        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "codeBlock",
                    "attrs": {"language": "javascript"},
                    "content": [{"type": "text", "text": "console.log('test');"}],
                }
            ],
        }
        markdown = adf_to_markdown(adf)
        assert "```javascript" in markdown
        assert "console.log" in markdown

    def test_adf_to_markdown_empty(self):
        """Test empty ADF."""
        from skills.confluence.scripts.confluence import adf_to_markdown

        adf = {}
        markdown = adf_to_markdown(adf)
        assert markdown == ""

    def test_adf_to_markdown_no_content(self):
        """Test ADF with no content."""
        from skills.confluence.scripts.confluence import adf_to_markdown

        adf = {"version": 1, "type": "doc", "content": []}
        markdown = adf_to_markdown(adf)
        assert markdown == ""

    def test_inline_markdown_link(self):
        """Test inline markdown link."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_adf

        result = _inline_markdown_to_adf("[example](https://example.com)")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "example"
        assert result[0]["marks"][0]["type"] == "link"
        assert result[0]["marks"][0]["attrs"]["href"] == "https://example.com"

    def test_inline_markdown_multiple_marks(self):
        """Test multiple inline marks."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_adf

        result = _inline_markdown_to_adf("**bold** and *italic* and `code`")
        assert len(result) == 5  # bold, text, italic, text, code

    def test_format_content_storage_to_editor(self):
        """Test storage to editor conversion."""
        from skills.confluence.scripts.confluence import format_content

        storage = "<p>Test content</p>"
        result = format_content(storage, input_format="storage", output_format="editor")
        assert isinstance(result, dict)
        assert result.get("type") == "doc"

    def test_markdown_to_adf_bullet_list(self):
        """Test bullet list to ADF."""
        from skills.confluence.scripts.confluence import markdown_to_adf

        markdown = "- Item 1\n- Item 2"
        adf = markdown_to_adf(markdown)
        bullet_lists = [node for node in adf["content"] if node.get("type") == "bulletList"]
        assert len(bullet_lists) > 0

    def test_markdown_to_adf_ordered_list(self):
        """Test ordered list to ADF."""
        from skills.confluence.scripts.confluence import markdown_to_adf

        markdown = "1. First\n2. Second"
        adf = markdown_to_adf(markdown)
        ordered_lists = [node for node in adf["content"] if node.get("type") == "orderedList"]
        assert len(ordered_lists) > 0

    def test_markdown_to_adf_code_block(self):
        """Test code block to ADF."""
        from skills.confluence.scripts.confluence import markdown_to_adf

        markdown = "```python\ncode\n```"
        adf = markdown_to_adf(markdown)
        code_blocks = [node for node in adf["content"] if node.get("type") == "codeBlock"]
        assert len(code_blocks) == 1
        assert code_blocks[0]["attrs"]["language"] == "python"

    def test_markdown_to_adf_code_block_no_language(self):
        """Test code block without language to ADF."""
        from skills.confluence.scripts.confluence import markdown_to_adf

        markdown = "```\ncode\n```"
        adf = markdown_to_adf(markdown)
        code_blocks = [node for node in adf["content"] if node.get("type") == "codeBlock"]
        assert len(code_blocks) == 1


class TestHTTPWrappers:
    """Tests for HTTP request wrapper functions."""

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.requests.request")
    @patch("skills.confluence.scripts.confluence.is_cloud")
    def test_make_request_success(self, mock_is_cloud, mock_request, mock_creds):
        """Test successful HTTP request."""
        from skills.confluence.scripts.confluence import make_request

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
        mock_is_cloud.return_value = True
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        result = make_request("confluence", "GET", "/rest/api/space")
        assert result == {"result": "success"}

    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_make_request_invalid_credentials(self, mock_creds):
        """Test request with invalid credentials."""
        from skills.confluence.scripts.confluence import APIError, make_request

        mock_creds.return_value = Credentials(url=None, token=None)

        with pytest.raises(APIError):
            make_request("confluence", "GET", "/rest/api/space")

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.requests.request")
    @patch("skills.confluence.scripts.confluence.is_cloud")
    def test_make_request_404_error(self, mock_is_cloud, mock_request, mock_creds):
        """Test request with 404 error."""
        from skills.confluence.scripts.confluence import APIError, make_request

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
        mock_is_cloud.return_value = True
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Page not found"
        mock_request.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            make_request("confluence", "GET", "/rest/api/content/999")
        assert exc_info.value.status_code == 404

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.requests.request")
    @patch("skills.confluence.scripts.confluence.is_cloud")
    def test_make_request_204_no_content(self, mock_is_cloud, mock_request, mock_creds):
        """Test request with 204 No Content."""
        from skills.confluence.scripts.confluence import make_request

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
        mock_is_cloud.return_value = True
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        result = make_request("confluence", "DELETE", "/rest/api/content/123")
        assert result == {}

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.requests.request")
    @patch("skills.confluence.scripts.confluence.is_cloud")
    def test_make_request_bearer_token_server(self, mock_is_cloud, mock_request, mock_creds):
        """Test request with bearer token for server."""
        from skills.confluence.scripts.confluence import make_request

        mock_creds.return_value = Credentials(url="https://example.com/confluence", token="test123")
        mock_is_cloud.return_value = False
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        result = make_request("confluence", "GET", "/rest/api/space")
        assert result == {"result": "success"}
        # Verify Bearer token was used
        call_kwargs = mock_request.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer test123"

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.requests.request")
    @patch("skills.confluence.scripts.confluence.is_cloud")
    def test_make_request_basic_auth_server(self, mock_is_cloud, mock_request, mock_creds):
        """Test request with username/password for server."""
        from skills.confluence.scripts.confluence import make_request

        mock_creds.return_value = Credentials(
            url="https://example.com/confluence", username="user", password="pass"
        )
        mock_is_cloud.return_value = False
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        result = make_request("confluence", "GET", "/rest/api/space")
        assert result == {"result": "success"}
        # Verify basic auth was used
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["auth"] == ("user", "pass")


class TestFormatPageVariations:
    """Tests for format_page with various scenarios."""

    def test_format_page_with_editor_body(self):
        """Test formatting page with editor (ADF) body."""
        from skills.confluence.scripts.confluence import format_page

        page = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {
                "editor": {
                    "value": {
                        "version": 1,
                        "type": "doc",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Test content"}],
                            }
                        ],
                    }
                }
            },
        }

        result = format_page(page, include_body=True, as_markdown=True)
        assert "Test Page" in result
        assert "Test content" in result

    def test_format_page_with_editor_body_string(self):
        """Test formatting page with editor body as JSON string."""
        import json

        from skills.confluence.scripts.confluence import format_page

        page = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {
                "editor": {
                    "value": json.dumps(
                        {
                            "version": 1,
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Test"}],
                                }
                            ],
                        }
                    )
                }
            },
        }

        result = format_page(page, include_body=True, as_markdown=True)
        assert "Test Page" in result

    def test_format_page_no_body_available(self):
        """Test formatting page with no body content."""
        from skills.confluence.scripts.confluence import format_page

        page = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {},
        }

        result = format_page(page, include_body=True, as_markdown=True)
        assert "Test Page" in result
        assert "(No content available)" in result

    def test_format_page_raw_body(self):
        """Test formatting page with raw body."""
        from skills.confluence.scripts.confluence import format_page

        page = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {"storage": {"value": "<p>Content</p>"}},
        }

        result = format_page(page, include_body=True, as_markdown=False)
        assert "Test Page" in result
        assert '"storage"' in result


class TestDeploymentDetectionDetails:
    """Tests for deployment detection internals."""

    @patch("skills.confluence.scripts.confluence.requests.get")
    def test_make_detection_request_unauthenticated_success(self, mock_get):
        """Test detection request succeeds without auth."""
        from skills.confluence.scripts.confluence import _make_detection_request

        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"deploymentType": "Cloud"}
        mock_get.return_value = mock_response

        result = _make_detection_request("https://example.atlassian.net", "/rest/api/space")
        assert result == {"deploymentType": "Cloud"}

    @patch("skills.confluence.scripts.confluence.requests.get")
    def test_make_detection_request_requires_auth(self, mock_get):
        """Test detection request falls back to auth."""
        from skills.confluence.scripts.confluence import _make_detection_request

        # First call returns 401, second call with auth succeeds
        unauth_response = Mock()
        unauth_response.ok = False
        unauth_response.status_code = 401

        auth_response = Mock()
        auth_response.ok = True
        auth_response.status_code = 200
        auth_response.json.return_value = {"deploymentType": "Server"}

        mock_get.side_effect = [unauth_response, auth_response]

        result = _make_detection_request(
            "https://example.com/confluence",
            "/rest/api/space",
            username="user",
            password="pass",
        )
        assert result == {"deploymentType": "Server"}

    @patch("skills.confluence.scripts.confluence.requests.get")
    @patch("skills.confluence.scripts.confluence.time.sleep")
    def test_make_detection_request_rate_limit_with_retry_after(self, mock_sleep, mock_get):
        """Test detection request handles rate limit with Retry-After header."""
        from skills.confluence.scripts.confluence import _make_detection_request

        # First call returns 429 with Retry-After, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "2"}

        success_response = Mock()
        success_response.ok = True
        success_response.status_code = 200
        success_response.json.return_value = {"deploymentType": "Cloud"}

        mock_get.side_effect = [rate_limit_response, success_response]

        result = _make_detection_request("https://example.atlassian.net", "/rest/api/space")
        assert result == {"deploymentType": "Cloud"}
        mock_sleep.assert_called_once_with(2.0)

    @patch("skills.confluence.scripts.confluence.requests.get")
    @patch("skills.confluence.scripts.confluence.time.sleep")
    def test_make_detection_request_rate_limit_max_retries(self, _mock_sleep, mock_get):
        """Test detection request fails after max retries."""
        from skills.confluence.scripts.confluence import (
            ConfluenceDetectionError,
            _make_detection_request,
        )

        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {}

        mock_get.return_value = rate_limit_response

        with pytest.raises(ConfluenceDetectionError):
            _make_detection_request("https://example.atlassian.net", "/rest/api/space")

    @patch("skills.confluence.scripts.confluence.requests.get")
    def test_make_detection_request_network_error(self, mock_get):
        """Test detection request handles network error."""
        import requests

        from skills.confluence.scripts.confluence import (
            ConfluenceDetectionError,
            _make_detection_request,
        )

        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(ConfluenceDetectionError):
            _make_detection_request("https://example.atlassian.net", "/rest/api/space")

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_detect_deployment_type_cloud_url_fails_tries_server(self, mock_creds, mock_request):
        """Test detection tries server API if cloud fails."""
        from skills.confluence.scripts.confluence import (
            ConfluenceDetectionError,
            clear_cache,
            detect_deployment_type,
        )

        mock_creds.return_value = Credentials(url="https://example.atlassian.net", token="test")

        # First request (cloud API) fails, second request (server API) succeeds
        mock_request.side_effect = [
            ConfluenceDetectionError("Failed"),
            {"deploymentType": "Server"},
        ]

        clear_cache()
        result = detect_deployment_type()
        assert result == "Server"

    @patch("skills.confluence.scripts.confluence._make_detection_request")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_detect_deployment_type_server_url_fails_tries_cloud(self, mock_creds, mock_request):
        """Test detection tries cloud API if server fails."""
        from skills.confluence.scripts.confluence import (
            ConfluenceDetectionError,
            clear_cache,
            detect_deployment_type,
        )

        mock_creds.return_value = Credentials(url="https://example.com/confluence", token="test")

        # First request (server API) fails, second request (cloud API) succeeds
        mock_request.side_effect = [
            ConfluenceDetectionError("Failed"),
            {"deploymentType": "Cloud"},
        ]

        clear_cache()
        result = detect_deployment_type()
        assert result == "Cloud"


class TestAdditionalCoverage:
    """Additional tests to push coverage over 80%."""

    def test_format_table_no_data(self):
        """Test format_table with empty data."""
        from skills.confluence.scripts.confluence import format_table

        result = format_table([], ["col1", "col2"])
        assert result == "No data"

    def test_inline_markdown_italic_with_underscore(self):
        """Test italic with underscore."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_html

        text = "This is _italic_ text"
        html = _inline_markdown_to_html(text)
        assert "<em>italic</em>" in html

    def test_inline_markdown_bold_with_underscore(self):
        """Test bold with double underscore."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_html

        text = "This is __bold__ text"
        html = _inline_markdown_to_html(text)
        assert "<strong>bold</strong>" in html

    def test_storage_to_markdown_simple_code_block(self):
        """Test simple code block without CDATA."""
        from skills.confluence.scripts.confluence import storage_to_markdown

        storage = "<pre><code>test code</code></pre>"
        markdown = storage_to_markdown(storage)
        assert "```" in markdown
        assert "test code" in markdown

    def test_adf_content_to_text_with_all_marks(self):
        """Test ADF content with all mark types."""
        from skills.confluence.scripts.confluence import _adf_content_to_text

        content = [
            {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
            {"type": "text", "text": " "},
            {"type": "text", "text": "italic", "marks": [{"type": "em"}]},
            {"type": "text", "text": " "},
            {"type": "text", "text": "code", "marks": [{"type": "code"}]},
            {"type": "text", "text": " "},
            {
                "type": "text",
                "text": "link",
                "marks": [{"type": "link", "attrs": {"href": "https://example.com"}}],
            },
        ]

        result = _adf_content_to_text(content)
        assert "**bold**" in result
        assert "*italic*" in result
        assert "`code`" in result
        assert "[link](https://example.com)" in result

    def test_inline_markdown_to_adf_bold(self):
        """Test bold text to ADF."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_adf

        result = _inline_markdown_to_adf("**bold text**")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "bold text"
        assert result[0]["marks"][0]["type"] == "strong"

    def test_inline_markdown_to_adf_italic(self):
        """Test italic text to ADF."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_adf

        result = _inline_markdown_to_adf("*italic text*")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "italic text"
        assert result[0]["marks"][0]["type"] == "em"

    def test_inline_markdown_to_adf_code(self):
        """Test inline code to ADF."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_adf

        result = _inline_markdown_to_adf("`code text`")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "code text"
        assert result[0]["marks"][0]["type"] == "code"

    def test_inline_markdown_to_adf_plain_text(self):
        """Test plain text to ADF."""
        from skills.confluence.scripts.confluence import _inline_markdown_to_adf

        result = _inline_markdown_to_adf("plain text")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "plain text"
        assert "marks" not in result[0]

    @patch("skills.confluence.scripts.confluence.is_cloud")
    def test_format_content_editor_as_string(self, mock_is_cloud):
        """Test format_content with editor format as string."""
        import json

        from skills.confluence.scripts.confluence import format_content

        mock_is_cloud.return_value = True

        adf_str = json.dumps(
            {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Test"}],
                    }
                ],
            }
        )

        result = format_content(adf_str, input_format="editor", output_format="storage")
        assert isinstance(result, str)

    @patch("skills.confluence.scripts.confluence.is_cloud")
    def test_format_content_passthrough(self, mock_is_cloud):
        """Test format_content with same input/output format."""
        from skills.confluence.scripts.confluence import format_content

        mock_is_cloud.return_value = True

        content = "test content"
        result = format_content(content, input_format="markdown", output_format="markdown")
        assert result == content
