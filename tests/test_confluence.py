"""Tests for confluence.py skill."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import from skills module
from skills.confluence.scripts import confluence
from skills.confluence.scripts.confluence import (
    APIError,
    ConfluenceDefaults,
    Credentials,
    SpaceDefaults,
    _truncate,
    adf_to_markdown,
    delete_credential,
    format_json,
    get_credential,
    load_config,
    markdown_to_adf,
    merge_cql_with_scope,
    save_config,
    set_credential,
)

extract_local_images = confluence.extract_local_images
upload_attachment = confluence.upload_attachment
replace_image_paths = confluence.replace_image_paths
_upload_images_and_build_urls = confluence._upload_images_and_build_urls

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
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
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_create_page_cloud(self, mock_get_api_base, mock_post):
        """Test creating page on Cloud."""
        from skills.confluence.scripts.confluence import create_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
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
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_update_page(self, mock_get_api_base, mock_get_page, mock_put):
        """Test updating a page."""
        from skills.confluence.scripts.confluence import update_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
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

    @patch("skills.confluence.scripts.confluence.put")
    @patch("skills.confluence.scripts.confluence.get_page")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_move_page(self, mock_get_api_base, mock_get_page, mock_put):
        """Test moving a page under a new parent."""
        from skills.confluence.scripts.confluence import move_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_get_page.return_value = {
            "id": "123",
            "title": "My Page",
            "version": {"number": 3},
        }
        mock_put.return_value = {"id": "123", "title": "My Page", "version": {"number": 4}}

        result = move_page("123", "456")
        assert result["version"]["number"] == 4
        payload = mock_put.call_args[0][2]
        assert payload["ancestors"] == [{"id": "456"}]
        assert payload["title"] == "My Page"
        assert payload["version"]["number"] == 4

    @patch("skills.confluence.scripts.confluence.put")
    @patch("skills.confluence.scripts.confluence.get_page")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_move_page_to_root(self, mock_get_api_base, mock_get_page, mock_put):
        """Test moving a page to space root."""
        from skills.confluence.scripts.confluence import move_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_get_page.return_value = {
            "id": "123",
            "title": "My Page",
            "version": {"number": 1},
        }
        mock_put.return_value = {"id": "123", "version": {"number": 2}}

        move_page("123", None)
        payload = mock_put.call_args[0][2]
        assert payload["ancestors"] == []

    @patch("skills.confluence.scripts.confluence.delete")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_delete_page(self, mock_get_api_base, mock_delete):
        """Test deleting a page."""
        from skills.confluence.scripts.confluence import delete_page

        mock_get_api_base.return_value = "https://example.atlassian.net/wiki"
        mock_delete.return_value = {}

        result = delete_page("123")
        assert result == {}
        mock_delete.assert_called_once()
        call_args = mock_delete.call_args
        assert "content/123" in call_args[0][1]


class TestFormatFunctions:
    """Tests for page formatting functions."""

    def test_format_page(self):
        """Test page formatting as markdown."""
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
        assert result.startswith("### Test Page\n")
        assert "- **Page ID:** 123" in result
        assert "- **Space:** DEMO" in result

    def test_format_pages_list(self):
        """Test formatting list of pages as markdown."""
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
        assert "### Page 1" in result
        assert "### Page 2" in result
        assert "- **Page ID:** 1" in result
        assert "- **Page ID:** 2" in result

    def test_format_content_markdown_to_adf(self):
        """Test format_content converts markdown to ADF."""
        from skills.confluence.scripts.confluence import format_content

        result = format_content("# Heading", input_format="markdown")
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

    def test_get_api_base(self):
        """Test API base always returns Cloud path."""
        from skills.confluence.scripts.confluence import get_api_base

        base = get_api_base()
        assert base == "/wiki/rest/api"

    def test_api_path(self):
        """Test API path generation."""
        from skills.confluence.scripts.confluence import api_path

        path = api_path("content")
        assert path == "/wiki/rest/api/content"


class TestCommandHandlers:
    """Tests for CLI command handlers."""

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.get")
    def test_cmd_check_success(self, mock_get, mock_creds):
        """Test successful check command."""

        from skills.confluence.scripts.confluence import cmd_check

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
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

    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_cmd_check_url_with_wiki_suffix(self, mock_creds):
        """Test check command rejects URL with /wiki suffix."""
        from skills.confluence.scripts.confluence import cmd_check

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net/wiki", token="test123"
        )
        result = cmd_check()
        assert result == 1

    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_cmd_check_url_with_wiki_trailing_slash(self, mock_creds):
        """Test check command rejects URL with /wiki/ suffix."""
        from skills.confluence.scripts.confluence import cmd_check

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net/wiki/", token="test123"
        )
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
            frontmatter=False,
            expand=None,
            output=None,
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
            frontmatter=False,
            expand="body.storage,version",
            output=None,
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
            toc=False,
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
            toc=False,
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
            toc=False,
            json=False,
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.move_page")
    def test_cmd_page_move(self, mock_move):
        """Test page move command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_move.return_value = {"id": "123", "version": {"number": 3}}

        args = argparse.Namespace(
            page_command="move",
            page_id="123",
            parent="456",
            json=False,
        )

        result = cmd_page(args)
        assert result == 0
        mock_move.assert_called_once_with("123", "456")

    @patch("skills.confluence.scripts.confluence.delete_page")
    def test_cmd_page_delete(self, mock_delete):
        """Test page delete command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_delete.return_value = {}

        args = argparse.Namespace(
            page_command="delete",
            page_id="123",
        )

        result = cmd_page(args)
        assert result == 0
        mock_delete.assert_called_once_with("123")

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
            output=None,
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
            toc=False,
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
    def test_make_request_success(self, mock_request, mock_creds):
        """Test successful HTTP request."""
        from skills.confluence.scripts.confluence import make_request

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
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
    def test_make_request_404_error(self, mock_request, mock_creds):
        """Test request with 404 error."""
        from skills.confluence.scripts.confluence import APIError, make_request

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
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
    def test_make_request_204_no_content(self, mock_request, mock_creds):
        """Test request with 204 No Content."""
        from skills.confluence.scripts.confluence import make_request

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net", token="test123", email="test@example.com"
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        result = make_request("confluence", "DELETE", "/rest/api/content/123")
        assert result == {}


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
                "atlas_doc_format": {
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
                "atlas_doc_format": {
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


class TestAdditionalCoverage:
    """Additional tests to push coverage over 80%."""

    def test_format_table_no_data(self):
        """Test format_table with empty data."""
        from skills.confluence.scripts.confluence import format_table

        result = format_table([], ["col1", "col2"])
        assert result == "No data"

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

    def test_format_content_editor_as_string(self):
        """Test format_content with editor format as string."""
        import json

        from skills.confluence.scripts.confluence import format_content

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

        result = format_content(adf_str, input_format="editor")
        assert isinstance(result, dict)
        assert result["type"] == "doc"

    def test_format_content_passthrough(self):
        """Test format_content with unrecognized input format passes through."""
        from skills.confluence.scripts.confluence import format_content

        content = "test content"
        result = format_content(content, input_format="other")
        assert result == content


class TestAPIErrorVerboseMessage:
    """Tests for APIError.verbose_message()."""

    def test_verbose_with_json_response(self):
        err = APIError("failed", status_code=400, response='{"message": "bad"}')
        msg = err.verbose_message()
        assert "failed" in msg
        assert '"message": "bad"' in msg
        assert "Response:" in msg

    def test_verbose_with_plain_response(self):
        err = APIError("failed", status_code=500, response="Server error text")
        msg = err.verbose_message()
        assert "Server error text" in msg

    def test_verbose_with_request_body(self):
        err = APIError("failed", request_body={"type": "page", "title": "Test"})
        msg = err.verbose_message()
        assert "Request body:" in msg
        assert '"title": "Test"' in msg

    def test_verbose_no_extras(self):
        err = APIError("simple error")
        msg = err.verbose_message()
        assert msg == "simple error"

    def test_verbose_non_serializable_request_body(self):
        err = APIError("failed", request_body=object())
        msg = err.verbose_message()
        assert "Request body:" in msg


class TestUpdatePageTitleFallback:
    """Tests for update_page title auto-fetch."""

    @patch("skills.confluence.scripts.confluence.put")
    @patch("skills.confluence.scripts.confluence.get_page")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_update_page_without_title(self, mock_base, mock_get, mock_put):
        """update_page includes current title when --title not provided."""
        from skills.confluence.scripts.confluence import update_page

        mock_base.return_value = "https://example.atlassian.net/wiki"
        mock_get.return_value = {
            "id": "123",
            "title": "Existing Title",
            "version": {"number": 5},
        }
        mock_put.return_value = {"id": "123", "title": "Existing Title", "version": {"number": 6}}

        update_page("123", body="# Updated content")
        call_args = mock_put.call_args
        payload = call_args[0][2]
        assert payload["title"] == "Existing Title"
        assert payload["version"]["number"] == 6

    @patch("skills.confluence.scripts.confluence.put")
    @patch("skills.confluence.scripts.confluence.get_page")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_update_page_with_body_cloud(self, mock_base, mock_get, mock_put):
        """update_page sends ADF as JSON string on Cloud."""
        import json

        from skills.confluence.scripts.confluence import update_page

        mock_base.return_value = "https://example.atlassian.net/wiki"
        mock_get.return_value = {
            "id": "456",
            "title": "Page",
            "version": {"number": 1},
        }
        mock_put.return_value = {"id": "456", "version": {"number": 2}}

        update_page("456", body="Hello")
        payload = mock_put.call_args[0][2]
        value = payload["body"]["editor"]["value"]
        assert isinstance(value, str)
        parsed = json.loads(value)
        assert parsed["type"] == "doc"


class TestSpacePermissions:
    """Tests for space permission functions."""

    @patch("skills.confluence.scripts.confluence.get_space")
    def test_get_space_permissions(self, mock_get_space):
        """Test listing space permissions."""
        from skills.confluence.scripts.confluence import get_space_permissions

        mock_get_space.return_value = {
            "key": "DEMO",
            "permissions": [
                {
                    "id": 1,
                    "subject": {"type": "user", "identifier": "abc123"},
                    "operation": {"key": "read", "target": "space"},
                },
                {
                    "id": 2,
                    "subject": {"type": "group", "identifier": "developers"},
                    "operation": {"key": "create", "target": "page"},
                },
            ],
        }

        perms = get_space_permissions("DEMO")
        assert len(perms) == 2
        assert perms[0]["subject"]["type"] == "user"
        mock_get_space.assert_called_once_with("DEMO", expand=["permissions"])

    @patch("skills.confluence.scripts.confluence.post")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_add_space_permission(self, mock_base, mock_post):
        """Test adding a space permission."""
        from skills.confluence.scripts.confluence import add_space_permission

        mock_base.return_value = "https://example.atlassian.net/wiki"
        mock_post.return_value = {
            "id": 42,
            "subject": {"type": "user", "identifier": "abc123"},
            "operation": {"key": "read", "target": "space"},
        }

        result = add_space_permission("DEMO", "user", "abc123", "read", "space")
        assert result["id"] == 42
        payload = mock_post.call_args[0][2]
        assert payload["subject"]["type"] == "user"
        assert payload["subject"]["identifier"] == "abc123"
        assert payload["operation"]["key"] == "read"
        assert payload["operation"]["target"] == "space"

    @patch("skills.confluence.scripts.confluence.delete")
    @patch("skills.confluence.scripts.confluence.get_api_base")
    def test_remove_space_permission(self, mock_base, mock_delete):
        """Test removing a space permission."""
        from skills.confluence.scripts.confluence import remove_space_permission

        mock_base.return_value = "https://example.atlassian.net/wiki"
        mock_delete.return_value = {}

        result = remove_space_permission("DEMO", 42)
        assert result == {}
        call_args = mock_delete.call_args
        assert "space/DEMO/permission/42" in call_args[0][1]

    @patch("skills.confluence.scripts.confluence.cmd_space_permissions")
    def test_cmd_space_dispatches_permissions(self, mock_perm_cmd):
        """Test cmd_space dispatches to cmd_space_permissions."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space

        mock_perm_cmd.return_value = 0

        args = argparse.Namespace(space_command="permissions")

        result = cmd_space(args)
        assert result == 0
        mock_perm_cmd.assert_called_once_with(args)

    @patch("skills.confluence.scripts.confluence.get_space_permissions")
    def test_cmd_space_permissions_list(self, mock_perms):
        """Test space permissions list command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space_permissions

        mock_perms.return_value = [
            {
                "id": 1,
                "subject": {"type": "user", "identifier": "abc123"},
                "operation": {"key": "read", "target": "space"},
            },
        ]

        args = argparse.Namespace(
            perm_command="list",
            space_key="DEMO",
            subject_type=None,
            json=False,
        )

        result = cmd_space_permissions(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.get_space_permissions")
    def test_cmd_space_permissions_list_filter_by_type(self, mock_perms):
        """Test space permissions list filtered by subject type."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space_permissions

        mock_perms.return_value = [
            {
                "id": 1,
                "subject": {"type": "user", "identifier": "abc123"},
                "operation": {"key": "read", "target": "space"},
            },
            {
                "id": 2,
                "subject": {"type": "group", "identifier": "devs"},
                "operation": {"key": "create", "target": "page"},
            },
        ]

        args = argparse.Namespace(
            perm_command="list",
            space_key="DEMO",
            subject_type="user",
            json=False,
        )

        result = cmd_space_permissions(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.get_space_permissions")
    def test_cmd_space_permissions_list_empty(self, mock_perms):
        """Test space permissions list with no results."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space_permissions

        mock_perms.return_value = []

        args = argparse.Namespace(
            perm_command="list",
            space_key="DEMO",
            subject_type=None,
            json=False,
        )

        result = cmd_space_permissions(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.get_space_permissions")
    def test_cmd_space_permissions_list_json(self, mock_perms):
        """Test space permissions list with JSON output."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space_permissions

        mock_perms.return_value = [
            {
                "id": 1,
                "subject": {"type": "user", "identifier": "abc123"},
                "operation": {"key": "read", "target": "space"},
            },
        ]

        args = argparse.Namespace(
            perm_command="list",
            space_key="DEMO",
            subject_type=None,
            json=True,
        )

        result = cmd_space_permissions(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.add_space_permission")
    def test_cmd_space_permissions_add(self, mock_add):
        """Test space permissions add command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space_permissions

        mock_add.return_value = {"id": 42}

        args = argparse.Namespace(
            perm_command="add",
            space_key="DEMO",
            subject_type="user",
            subject="abc123",
            operation="read",
            target="space",
            json=False,
        )

        result = cmd_space_permissions(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.add_space_permission")
    def test_cmd_space_permissions_add_json(self, mock_add):
        """Test space permissions add with JSON output."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space_permissions

        mock_add.return_value = {"id": 42}

        args = argparse.Namespace(
            perm_command="add",
            space_key="DEMO",
            subject_type="user",
            subject="abc123",
            operation="read",
            target="space",
            json=True,
        )

        result = cmd_space_permissions(args)
        assert result == 0
        mock_add.assert_called_once_with(
            space_key="DEMO",
            subject_type="user",
            subject_id="abc123",
            operation_key="read",
            target="space",
        )

    @patch("skills.confluence.scripts.confluence.remove_space_permission")
    def test_cmd_space_permissions_remove(self, mock_remove):
        """Test space permissions remove command."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_space_permissions

        mock_remove.return_value = {}

        args = argparse.Namespace(
            perm_command="remove",
            space_key="DEMO",
            id=42,
        )

        result = cmd_space_permissions(args)
        assert result == 0
        mock_remove.assert_called_once_with("DEMO", 42)


class TestInternalLinksAndToc:
    """Tests for internal link conversion and TOC macro."""

    def test_extract_page_id_cloud_url(self):
        from skills.confluence.scripts.confluence import _extract_page_id_from_url

        url = "https://example.atlassian.net/wiki/spaces/DEMO/pages/123456/My+Page"
        assert _extract_page_id_from_url(url, "https://example.atlassian.net") == "123456"

    def test_extract_page_id_cloud_no_title(self):
        from skills.confluence.scripts.confluence import _extract_page_id_from_url

        url = "https://example.atlassian.net/wiki/spaces/DEMO/pages/789"
        assert _extract_page_id_from_url(url, "https://example.atlassian.net") == "789"

    def test_extract_page_id_different_instance(self):
        from skills.confluence.scripts.confluence import _extract_page_id_from_url

        url = "https://other.atlassian.net/wiki/spaces/DEMO/pages/123"
        assert _extract_page_id_from_url(url, "https://example.atlassian.net") is None

    def test_extract_page_id_non_confluence_url(self):
        from skills.confluence.scripts.confluence import _extract_page_id_from_url

        assert (
            _extract_page_id_from_url("https://google.com", "https://example.atlassian.net") is None
        )

    def test_prepend_toc_adf(self):
        from skills.confluence.scripts.confluence import _prepend_toc_adf

        adf = {"version": 1, "type": "doc", "content": [{"type": "paragraph"}]}
        result = _prepend_toc_adf(adf)
        assert result["content"][0]["type"] == "extension"
        assert result["content"][0]["attrs"]["extensionKey"] == "toc"
        assert result["content"][1]["type"] == "paragraph"

    def test_markdown_to_adf_with_toc(self):
        result = markdown_to_adf("# Hello", include_toc=True)
        assert result["content"][0]["type"] == "extension"
        assert result["content"][0]["attrs"]["extensionKey"] == "toc"

    def test_adf_has_toc_true(self):
        from skills.confluence.scripts.confluence import _adf_has_toc

        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "extension",
                    "attrs": {
                        "extensionType": "com.atlassian.confluence.macro.core",
                        "extensionKey": "toc",
                    },
                },
                {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]},
            ],
        }
        assert _adf_has_toc(adf) is True

    def test_adf_has_toc_false(self):
        from skills.confluence.scripts.confluence import _adf_has_toc

        adf = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]},
            ],
        }
        assert _adf_has_toc(adf) is False


class TestFrontmatter:
    """Tests for frontmatter extraction and round-tripping."""

    def test_extract_frontmatter_yaml(self):
        from skills.confluence.scripts.confluence import extract_frontmatter

        text = "---\ntitle: My Page\nspace: DEMO\nlabels: docs, api\ntoc: true\n---\n\n# Content"
        body, meta = extract_frontmatter(text)
        assert meta["title"] == "My Page"
        assert meta["space"] == "DEMO"
        assert meta["labels"] == "docs, api"
        assert meta["toc"] == "true"
        assert "---" not in body
        assert "Content" in body

    def test_extract_frontmatter_none(self):
        from skills.confluence.scripts.confluence import extract_frontmatter

        body, meta = extract_frontmatter("# Just content")
        assert meta == {}
        assert "Just content" in body

    def test_strip_frontmatter(self):
        from skills.confluence.scripts.confluence import _strip_frontmatter

        text = "---\ntitle: Test\n---\n\nBody here"
        assert "Body here" in _strip_frontmatter(text)
        assert "title" not in _strip_frontmatter(text)

    def test_strip_frontmatter_no_frontmatter(self):
        from skills.confluence.scripts.confluence import _strip_frontmatter

        text = "# No frontmatter"
        assert _strip_frontmatter(text) == text

    def test_format_page_with_frontmatter(self):
        import json

        from skills.confluence.scripts.confluence import format_page_with_frontmatter

        page = {
            "id": "123",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 3},
            "ancestors": [{"id": "100"}, {"id": "200"}],
            "metadata": {
                "labels": {
                    "results": [{"name": "docs"}, {"name": "api"}],
                }
            },
            "body": {
                "atlas_doc_format": {
                    "value": json.dumps(
                        {
                            "version": 1,
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Hello world"}],
                                }
                            ],
                        }
                    )
                },
            },
        }

        result = format_page_with_frontmatter(page)
        assert result.startswith("---")
        assert "title: Test Page" in result
        assert "space: DEMO" in result
        assert "page_id: 123" in result
        assert "version: 3" in result
        assert "parent: 200" in result
        assert "labels: docs, api" in result
        assert "Hello world" in result

    def test_format_page_with_frontmatter_no_parent(self):
        from skills.confluence.scripts.confluence import format_page_with_frontmatter

        page = {
            "id": "456",
            "title": "Root Page",
            "space": {"key": "TEST"},
            "version": {"number": 1},
            "ancestors": [],
            "metadata": {"labels": {"results": []}},
            "body": {},
        }

        result = format_page_with_frontmatter(page)
        assert "parent:" not in result
        assert "labels:" not in result

    def test_format_page_with_frontmatter_toc(self):
        import json

        from skills.confluence.scripts.confluence import format_page_with_frontmatter

        page = {
            "id": "789",
            "title": "TOC Page",
            "space": {"key": "DEMO"},
            "version": {"number": 2},
            "ancestors": [],
            "metadata": {"labels": {"results": []}},
            "body": {
                "atlas_doc_format": {
                    "value": json.dumps(
                        {
                            "version": 1,
                            "type": "doc",
                            "content": [
                                {
                                    "type": "extension",
                                    "attrs": {
                                        "extensionType": "com.atlassian.confluence.macro.core",
                                        "extensionKey": "toc",
                                        "parameters": {"macroParams": {"maxLevel": {"value": "3"}}},
                                    },
                                },
                                {
                                    "type": "heading",
                                    "attrs": {"level": 1},
                                    "content": [{"type": "text", "text": "Intro"}],
                                },
                            ],
                        }
                    )
                }
            },
        }

        result = format_page_with_frontmatter(page)
        assert "toc: true" in result
        assert result.startswith("---")

    def test_format_page_with_frontmatter_no_toc(self):
        import json

        from skills.confluence.scripts.confluence import format_page_with_frontmatter

        page = {
            "id": "790",
            "title": "No TOC Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "ancestors": [],
            "metadata": {"labels": {"results": []}},
            "body": {
                "atlas_doc_format": {
                    "value": json.dumps(
                        {
                            "version": 1,
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "No TOC here"}],
                                },
                            ],
                        }
                    )
                }
            },
        }

        result = format_page_with_frontmatter(page)
        assert "toc:" not in result

    @patch("skills.confluence.scripts.confluence.get_page")
    def test_cmd_page_get_frontmatter(self, mock_get):
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_get.return_value = {
            "id": "123",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "ancestors": [],
            "metadata": {"labels": {"results": []}},
            "body": {"storage": {"value": "<p>Hello</p>"}},
        }

        args = argparse.Namespace(
            page_command="get",
            page_identifier="123",
            json=False,
            markdown=False,
            raw=False,
            no_body=False,
            frontmatter=True,
            expand=None,
            output=None,
        )

        result = cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.download_attachment")
    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_page")
    def test_cmd_page_get_output_file(self, mock_get, mock_list_att, mock_dl, tmp_path):
        """Test page get with --output writes file and downloads images."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_get.return_value = {
            "id": "123",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {"storage": {"value": "<p>Hello</p>"}},
        }
        mock_list_att.return_value = {
            "att-1": {
                "title": "photo.png",
                "download": "/dl/photo.png",
                "mediaType": "image/png",
            }
        }
        mock_dl.return_value = tmp_path / "test-page" / "photo.png"

        output_file = tmp_path / "test-page.md"
        args = argparse.Namespace(
            page_command="get",
            page_identifier="123",
            json=False,
            markdown=True,
            raw=False,
            no_body=False,
            frontmatter=False,
            expand=None,
            output=str(output_file),
        )

        result = cmd_page(args)
        assert result == 0
        assert output_file.exists()
        mock_dl.assert_called_once_with("/dl/photo.png", "photo.png", tmp_path / "test-page")

    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_page")
    def test_cmd_page_get_no_output_skips_images(self, mock_get, mock_list_att):
        """Test page get without --output does not download images."""
        import argparse

        from skills.confluence.scripts.confluence import cmd_page

        mock_get.return_value = {
            "id": "123",
            "title": "Test Page",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {"storage": {"value": "<p>Hello</p>"}},
        }

        args = argparse.Namespace(
            page_command="get",
            page_identifier="123",
            json=False,
            markdown=True,
            raw=False,
            no_body=False,
            frontmatter=False,
            expand=None,
            output=None,
        )

        result = cmd_page(args)
        assert result == 0
        mock_list_att.assert_not_called()


class TestExtractLocalImages:
    """Tests for extract_local_images function."""

    def test_extracts_single_image(self, tmp_path):
        """Create a small file, parse markdown with ![alt](file.png), verify extraction."""
        img = tmp_path / "photo.png"
        img.write_bytes(MINIMAL_PNG)

        body = "Some text\n![my alt](photo.png)\nMore text"
        stripped, images = extract_local_images(body, tmp_path)

        assert len(images) == 1
        assert images[0]["alt"] == "my alt"
        assert images[0]["path"] == img.resolve()
        assert images[0]["original_ref"] == "photo.png"
        assert "![my alt]" not in stripped
        assert "Some text" in stripped
        assert "More text" in stripped

    def test_skips_url_images(self, tmp_path):
        """URL-based images stay in body unchanged."""
        body = "![alt](https://example.com/img.png)"
        stripped, images = extract_local_images(body, tmp_path)

        assert images == []
        assert stripped == body

    def test_missing_file_warns(self, tmp_path, capsys):
        """Nonexistent file produces a warning and stays in body."""
        body = "![alt](nonexistent.png)"
        stripped, images = extract_local_images(body, tmp_path)

        assert images == []
        assert stripped == body
        captured = capsys.readouterr()
        assert "Warning: image not found" in captured.err

    def test_no_images_returns_unchanged(self, tmp_path):
        """No images in body returns body unchanged and empty list."""
        body = "Just some plain text with no images."
        stripped, images = extract_local_images(body, tmp_path)

        assert stripped == body
        assert images == []


class TestReplaceImagePaths:
    """Tests for replace_image_paths function."""

    def test_replaces_paths(self):
        """Local path is replaced with download URL."""
        body = "![alt](local.png)"
        replacements = {
            "local.png": "https://confluence.example.com/download/attachments/123/local.png",
        }
        result = replace_image_paths(body, replacements)
        assert result == "![alt](https://confluence.example.com/download/attachments/123/local.png)"


class TestUploadAttachment:
    """Tests for upload_attachment function."""

    @patch("skills.confluence.scripts.confluence.make_request")
    def test_upload_calls_make_request(self, mock_make_request, tmp_path):
        """Verify make_request is called with files and X-Atlassian-Token header."""
        img = tmp_path / "diagram.png"
        img.write_bytes(MINIMAL_PNG)

        mock_make_request.return_value = {"results": [{"id": "att1"}]}

        upload_attachment("12345", img)

        mock_make_request.assert_called_once()
        call_kwargs = mock_make_request.call_args
        # Check positional args: service, method, endpoint
        assert call_kwargs[0][0] == "confluence"
        assert call_kwargs[0][1] == "POST"
        assert "12345/child/attachment" in call_kwargs[0][2]
        # Check keyword args
        assert "files" in call_kwargs[1]
        assert call_kwargs[1]["headers"]["X-Atlassian-Token"] == "nocheck"


class TestUploadImagesAndBuildUrls:
    """Tests for _upload_images_and_build_urls function."""

    @patch("skills.confluence.scripts.confluence.get_api_base", return_value="/wiki/rest/api")
    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.upload_attachment")
    def test_uploads_images_and_builds_urls(
        self, mock_upload, mock_creds, mock_list_att, mock_api_base
    ):
        """Verify function uploads new images and builds replacement URLs."""
        mock_creds.return_value = Credentials(
            url="https://confluence.example.com",
            token="test123",
            email="test@example.com",
        )
        mock_upload.return_value = None
        mock_list_att.return_value = {}

        images = [
            {
                "path": Path("image1.png"),
                "original_ref": "image1.png",
            },
            {
                "path": Path("image2.jpg"),
                "original_ref": "subdir/image2.jpg",
            },
        ]

        result = _upload_images_and_build_urls("12345", images)

        assert result == {
            "image1.png": "https://confluence.example.com/wiki/download/attachments/12345/image1.png",
            "subdir/image2.jpg": "https://confluence.example.com/wiki/download/attachments/12345/image2.jpg",
        }
        assert mock_upload.call_count == 2

    @patch("skills.confluence.scripts.confluence.get_api_base", return_value="/wiki/rest/api")
    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.upload_attachment")
    def test_reuses_existing_attachments(
        self, mock_upload, mock_creds, mock_list_att, mock_api_base
    ):
        """Verify function reuses existing attachments without re-uploading."""
        mock_creds.return_value = Credentials(
            url="https://confluence.example.com",
            token="test123",
            email="test@example.com",
        )
        mock_list_att.return_value = {
            "att1": {
                "title": "image1.png",
                "download": "/download/attachments/12345/image1.png",
                "mediaType": "image/png",
            },
        }

        images = [
            {"path": Path("image1.png"), "original_ref": "imgs/image1.png"},
            {"path": Path("image2.jpg"), "original_ref": "imgs/image2.jpg"},
        ]

        result = _upload_images_and_build_urls("12345", images)

        assert result == {
            "imgs/image1.png": "https://confluence.example.com/wiki/download/attachments/12345/image1.png",
            "imgs/image2.jpg": "https://confluence.example.com/wiki/download/attachments/12345/image2.jpg",
        }
        mock_upload.assert_called_once()

    @patch("skills.confluence.scripts.confluence.get_api_base", return_value="/wiki/rest/api")
    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.upload_attachment")
    def test_handles_upload_failures(self, mock_upload, mock_creds, mock_list_att, mock_api_base):
        """Verify function handles upload failures gracefully with detail."""
        mock_creds.return_value = Credentials(
            url="https://confluence.example.com",
            token="test123",
            email="test@example.com",
        )
        mock_list_att.return_value = {}
        mock_upload.side_effect = [
            None,
            APIError("Upload failed", response='{"message": "Quota exceeded"}'),
        ]

        images = [
            {"path": Path("image1.png"), "original_ref": "image1.png"},
            {"path": Path("image2.jpg"), "original_ref": "image2.jpg"},
        ]

        result = _upload_images_and_build_urls("12345", images)

        assert "image1.png" in result
        assert "image2.jpg" not in result
        assert len(result) == 1


class TestMakeRequestMultipart:
    """Tests for make_request when files parameter is passed."""

    @patch("skills.confluence.scripts.confluence.get_credentials")
    @patch("skills.confluence.scripts.confluence.requests.request")
    def test_skips_content_type_for_files(self, mock_request, mock_creds):
        """When files is passed, Content-Type should NOT be set to application/json."""
        from skills.confluence.scripts.confluence import make_request

        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="test123",
            email="test@example.com",
        )
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_request.return_value = mock_response

        make_request(
            "confluence",
            "POST",
            "/rest/api/content/123/child/attachment",
            files={"file": ("test.png", b"data", "image/png")},
            headers={"X-Atlassian-Token": "nocheck"},
        )

        call_kwargs = mock_request.call_args
        headers = call_kwargs[1].get("headers", call_kwargs.kwargs.get("headers", {}))
        assert headers.get("Content-Type") != "application/json"


# ============================================================================
# ADF IMAGE NODE CONVERSION TESTS
# ============================================================================


class TestMediaNodeToMarkdown:
    """Tests for _media_node_to_markdown and adf_to_markdown with images."""

    def test_media_single_with_attachments(self):
        """Test mediaSingle node converts to markdown image."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "mediaSingle",
                    "attrs": {"layout": "center"},
                    "content": [
                        {
                            "type": "media",
                            "attrs": {
                                "type": "file",
                                "id": "att-123",
                                "collection": "contentId-456",
                                "alt": "diagram",
                            },
                        }
                    ],
                }
            ],
        }
        attachments = {
            "att-123": {
                "title": "diagram.png",
                "download": "/wiki/download/attachments/456/diagram.png",
                "mediaType": "image/png",
            }
        }
        result = adf_to_markdown(adf, attachments=attachments)
        assert "![diagram](/wiki/download/attachments/456/diagram.png)" in result

    def test_media_single_with_image_dir(self):
        """Test mediaSingle uses relative path when image_dir is set."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {
                            "type": "media",
                            "attrs": {"type": "file", "id": "att-1", "alt": "photo"},
                        }
                    ],
                }
            ],
        }
        attachments = {
            "att-1": {"title": "photo.jpg", "download": "/dl", "mediaType": "image/jpeg"}
        }
        result = adf_to_markdown(adf, attachments=attachments, image_dir=Path("images"))
        assert "![photo](images/photo.jpg)" in result

    def test_media_single_no_attachments(self):
        """Test fallback when no attachment metadata available."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {
                            "type": "media",
                            "attrs": {"type": "file", "id": "att-unknown", "alt": "img"},
                        }
                    ],
                }
            ],
        }
        result = adf_to_markdown(adf)
        assert "![img](attachment:att-unknown)" in result

    def test_media_group_multiple_images(self):
        """Test mediaGroup with multiple images."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "mediaGroup",
                    "content": [
                        {"type": "media", "attrs": {"type": "file", "id": "a1", "alt": "one"}},
                        {"type": "media", "attrs": {"type": "file", "id": "a2", "alt": "two"}},
                    ],
                }
            ],
        }
        attachments = {
            "a1": {"title": "one.png", "download": "/dl/one.png", "mediaType": "image/png"},
            "a2": {"title": "two.png", "download": "/dl/two.png", "mediaType": "image/png"},
        }
        result = adf_to_markdown(adf, attachments=attachments)
        assert "![one](/dl/one.png)" in result
        assert "![two](/dl/two.png)" in result

    def test_inline_media_in_paragraph(self):
        """Test inline media node within a paragraph."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "See "},
                        {
                            "type": "mediaInline",
                            "attrs": {"type": "file", "id": "att-x", "alt": "icon"},
                        },
                        {"type": "text", "text": " for details."},
                    ],
                }
            ],
        }
        attachments = {
            "att-x": {"title": "icon.png", "download": "/dl/icon.png", "mediaType": "image/png"}
        }
        result = adf_to_markdown(adf, attachments=attachments)
        assert "See ![icon](/dl/icon.png) for details." in result

    def test_mixed_content_with_images(self):
        """Test ADF with text and images together."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Title"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Some text."}],
                },
                {
                    "type": "mediaSingle",
                    "content": [
                        {"type": "media", "attrs": {"type": "file", "id": "img1", "alt": "chart"}},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "More text."}],
                },
            ],
        }
        attachments = {
            "img1": {"title": "chart.png", "download": "/dl/chart.png", "mediaType": "image/png"}
        }
        result = adf_to_markdown(adf, attachments=attachments)
        assert "# Title" in result
        assert "Some text." in result
        assert "![chart](/dl/chart.png)" in result
        assert "More text." in result


# ============================================================================
# LIST_ATTACHMENTS TESTS
# ============================================================================


class TestListAttachments:
    """Tests for list_attachments function."""

    @patch("skills.confluence.scripts.confluence.get")
    def test_list_attachments(self, mock_get):
        """Test fetching and mapping attachments."""
        mock_get.return_value = {
            "results": [
                {
                    "id": "att-100",
                    "title": "photo.png",
                    "extensions": {
                        "fileId": "file-abc",
                        "mediaType": "image/png",
                    },
                    "_links": {"download": "/wiki/download/attachments/1/photo.png"},
                },
                {
                    "id": "att-101",
                    "title": "doc.pdf",
                    "extensions": {
                        "fileId": "file-def",
                        "mediaType": "application/pdf",
                    },
                    "_links": {"download": "/wiki/download/attachments/1/doc.pdf"},
                },
            ]
        }
        result = confluence.list_attachments("12345")
        assert "file-abc" in result
        assert result["file-abc"]["title"] == "photo.png"
        assert result["file-abc"]["mediaType"] == "image/png"
        assert "file-def" in result


# ============================================================================
# DOWNLOAD_ATTACHMENT TESTS
# ============================================================================


class TestDownloadAttachment:
    """Tests for download_attachment function."""

    @patch("skills.confluence.scripts.confluence.requests.get")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_download_attachment(self, mock_creds, mock_requests_get, tmp_path):
        """Test downloading an attachment to local directory."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="test123",
            email="test@example.com",
        )
        mock_response = Mock()
        mock_response.content = MINIMAL_PNG
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        output_dir = tmp_path / "images"
        result = confluence.download_attachment(
            "/rest/api/content/456/child/attachment/att789/download",
            "photo.png",
            output_dir,
        )

        assert result == output_dir / "photo.png"
        assert result.read_bytes() == MINIMAL_PNG
        mock_requests_get.assert_called_once()

    @patch("skills.confluence.scripts.confluence.requests.get")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_download_creates_directory(self, mock_creds, mock_requests_get, tmp_path):
        """Test that download creates the output directory if needed."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="test123",
            email="test@example.com",
        )
        mock_response = Mock()
        mock_response.content = b"data"
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        output_dir = tmp_path / "nested" / "dir"
        confluence.download_attachment(
            "/rest/api/content/789/child/attachment/att999/download",
            "file.png",
            output_dir,
        )

        assert (output_dir / "file.png").exists()


class TestMediaNodeExternalImages:
    """Tests for _media_node_to_markdown with external media type."""

    def test_external_media_with_image_dir(self):
        """External media uses image_dir relative path when available."""
        from skills.confluence.scripts.confluence import _media_node_to_markdown

        node = {
            "type": "media",
            "attrs": {
                "type": "external",
                "url": "https://cdn.example.com/images/photo.png",
                "alt": "photo",
            },
        }
        result = _media_node_to_markdown(node, image_dir=Path("imgs"))
        assert result == "![photo](imgs/photo.png)"

    def test_external_media_without_image_dir(self):
        """External media returns URL directly without image_dir."""
        from skills.confluence.scripts.confluence import _media_node_to_markdown

        node = {
            "type": "media",
            "attrs": {
                "type": "external",
                "url": "https://cdn.example.com/photo.png",
                "alt": "pic",
            },
        }
        result = _media_node_to_markdown(node)
        assert result == "![pic](https://cdn.example.com/photo.png)"

    def test_external_media_empty_url(self):
        """External media with empty URL returns empty string."""
        from skills.confluence.scripts.confluence import _media_node_to_markdown

        node = {"type": "media", "attrs": {"type": "external", "url": "", "alt": "x"}}
        result = _media_node_to_markdown(node)
        assert result == ""

    def test_non_media_node_returns_empty(self):
        """Non-media node type returns empty string."""
        from skills.confluence.scripts.confluence import _media_node_to_markdown

        node = {"type": "paragraph"}
        assert _media_node_to_markdown(node) == ""

    def test_file_media_with_title_no_download(self):
        """File media with title but no download path uses filename."""
        from skills.confluence.scripts.confluence import _media_node_to_markdown

        node = {"type": "media", "attrs": {"type": "file", "id": "att-1", "alt": "img"}}
        attachments = {"att-1": {"title": "diagram.png", "download": "", "mediaType": "image/png"}}
        result = _media_node_to_markdown(node, attachments=attachments)
        assert result == "![img](diagram.png)"

    def test_bullet_list_with_attachments(self):
        """Bullet list items pass attachments through to _adf_content_to_text."""
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "item text"}],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = adf_to_markdown(adf, attachments={}, image_dir=Path("imgs"))
        assert "- item text" in result


class TestDownloadExternalImages:
    """Tests for _download_external_images function."""

    @patch("skills.confluence.scripts.confluence.download_attachment")
    def test_downloads_matching_attachment(self, mock_dl):
        """External image matching an attachment is downloaded."""
        adf = {
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {
                            "type": "media",
                            "attrs": {
                                "type": "external",
                                "url": "https://cdn.example.com/photo.png",
                            },
                        }
                    ],
                }
            ]
        }
        att_map = {
            "a1": {"title": "photo.png", "download": "/dl/photo.png", "mediaType": "image/png"}
        }
        confluence._download_external_images(adf, Path("/tmp/imgs"), att_map=att_map)
        mock_dl.assert_called_once_with("/dl/photo.png", "photo.png", Path("/tmp/imgs"))

    @patch("skills.confluence.scripts.confluence.download_attachment")
    def test_warns_on_no_match(self, mock_dl, capsys):
        """External image with no attachment match produces warning."""
        adf = {
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {
                            "type": "media",
                            "attrs": {
                                "type": "external",
                                "url": "https://cdn.example.com/unknown.png",
                            },
                        }
                    ],
                }
            ]
        }
        confluence._download_external_images(adf, Path("/tmp/imgs"), att_map={})
        mock_dl.assert_not_called()
        assert "no attachment match" in capsys.readouterr().err

    @patch("skills.confluence.scripts.confluence.download_attachment")
    def test_warns_on_download_failure(self, mock_dl, capsys):
        """Download failure produces warning but does not raise."""
        mock_dl.side_effect = Exception("network error")
        adf = {
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {
                            "type": "media",
                            "attrs": {
                                "type": "external",
                                "url": "https://cdn.example.com/fail.png",
                            },
                        }
                    ],
                }
            ]
        }
        att_map = {
            "a1": {"title": "fail.png", "download": "/dl/fail.png", "mediaType": "image/png"}
        }
        confluence._download_external_images(adf, Path("/tmp/imgs"), att_map=att_map)
        assert "failed to download" in capsys.readouterr().err

    @patch("skills.confluence.scripts.confluence.download_attachment")
    def test_skips_non_external(self, mock_dl):
        """Non-external media nodes are skipped."""
        adf = {
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {
                            "type": "media",
                            "attrs": {"type": "file", "id": "att-1"},
                        }
                    ],
                }
            ]
        }
        confluence._download_external_images(adf, Path("/tmp/imgs"), att_map={})
        mock_dl.assert_not_called()

    @patch("skills.confluence.scripts.confluence.download_attachment")
    def test_skips_non_media_nodes(self, mock_dl):
        """Non-mediaSingle/mediaGroup nodes are skipped."""
        adf = {
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "hello"}]},
            ]
        }
        confluence._download_external_images(adf, Path("/tmp/imgs"), att_map={})
        mock_dl.assert_not_called()

    @patch("skills.confluence.scripts.confluence.download_attachment")
    def test_skips_empty_url(self, mock_dl):
        """External media with empty URL is skipped."""
        adf = {
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {"type": "media", "attrs": {"type": "external", "url": ""}},
                    ],
                }
            ]
        }
        confluence._download_external_images(adf, Path("/tmp/imgs"), att_map={})
        mock_dl.assert_not_called()

    @patch("skills.confluence.scripts.confluence.download_attachment")
    def test_skips_url_without_filename(self, mock_dl):
        """External media with URL that has no path component is skipped."""
        adf = {
            "content": [
                {
                    "type": "mediaSingle",
                    "content": [
                        {"type": "media", "attrs": {"type": "external", "url": "nopath"}},
                    ],
                }
            ]
        }
        confluence._download_external_images(adf, Path("/tmp/imgs"), att_map={})
        mock_dl.assert_not_called()


class TestDownloadAttachmentAuthBranches:
    """Tests for download_attachment auth fallback branches."""

    @patch("skills.confluence.scripts.confluence.requests.get")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_username_password_auth(self, mock_creds, mock_get, tmp_path):
        """Username/password creds use basic auth."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            username="user",
            password="pass",
        )
        mock_response = Mock()
        mock_response.content = MINIMAL_PNG
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        confluence.download_attachment("/dl/img.png", "img.png", tmp_path)

        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["auth"] == ("user", "pass")

    @patch("skills.confluence.scripts.confluence.requests.get")
    @patch("skills.confluence.scripts.confluence.get_credentials")
    def test_bearer_token_auth(self, mock_creds, mock_get, tmp_path):
        """Token-only creds (no email/username) use bearer auth header."""
        mock_creds.return_value = Credentials(
            url="https://example.atlassian.net",
            token="bearer-token-123",
        )
        mock_response = Mock()
        mock_response.content = MINIMAL_PNG
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        confluence.download_attachment("/dl/img.png", "img.png", tmp_path)

        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["headers"]["Authorization"] == "Bearer bearer-token-123"
        assert call_kwargs[1]["auth"] is None


class TestCmdPageGetErrorBranches:
    """Tests for error handling branches in cmd_page get with --output."""

    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_page")
    def test_attachment_fetch_error(self, mock_get, mock_list_att, tmp_path):
        """APIError fetching attachments logs warning and continues."""
        import argparse

        mock_get.return_value = {
            "id": "123",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {"storage": {"value": "<p>Hi</p>"}},
        }
        mock_list_att.side_effect = APIError("connection failed")

        output_file = tmp_path / "page.md"
        args = argparse.Namespace(
            page_command="get",
            page_identifier="123",
            json=False,
            markdown=True,
            raw=False,
            no_body=False,
            frontmatter=False,
            expand=None,
            output=str(output_file),
        )

        result = confluence.cmd_page(args)
        assert result == 0
        assert output_file.exists()

    @patch("skills.confluence.scripts.confluence.download_attachment")
    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_page")
    def test_image_download_error(self, mock_get, mock_list_att, mock_dl, tmp_path):
        """Failed image download logs warning and continues."""
        import argparse

        mock_get.return_value = {
            "id": "123",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {"storage": {"value": "<p>Hi</p>"}},
        }
        mock_list_att.return_value = {
            "att-1": {"title": "img.png", "download": "/dl/img.png", "mediaType": "image/png"}
        }
        mock_dl.side_effect = Exception("timeout")

        output_file = tmp_path / "page.md"
        args = argparse.Namespace(
            page_command="get",
            page_identifier="123",
            json=False,
            markdown=True,
            raw=False,
            no_body=False,
            frontmatter=False,
            expand=None,
            output=str(output_file),
        )

        result = confluence.cmd_page(args)
        assert result == 0

    @patch("skills.confluence.scripts.confluence.list_attachments")
    @patch("skills.confluence.scripts.confluence.get_page")
    def test_external_images_with_adf_body(self, mock_get, mock_list_att, tmp_path):
        """External image download path is exercised when ADF body present."""
        import argparse
        import json

        mock_get.return_value = {
            "id": "123",
            "title": "Test",
            "space": {"key": "DEMO"},
            "version": {"number": 1},
            "body": {
                "atlas_doc_format": {
                    "value": json.dumps(
                        {
                            "version": 1,
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "hello"}],
                                }
                            ],
                        }
                    )
                }
            },
        }
        mock_list_att.return_value = {}

        output_file = tmp_path / "page.md"
        args = argparse.Namespace(
            page_command="get",
            page_identifier="123",
            json=False,
            markdown=True,
            raw=False,
            no_body=False,
            frontmatter=False,
            expand=None,
            output=str(output_file),
        )

        result = confluence.cmd_page(args)
        assert result == 0
        assert output_file.exists()
