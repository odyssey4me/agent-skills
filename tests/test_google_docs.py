"""Tests for google-docs.py skill."""

from __future__ import annotations

# Import from skills module - use importlib to handle hyphenated module name
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Load the module with hyphenated name
spec = importlib.util.spec_from_file_location(
    "google_docs",
    Path(__file__).parent.parent / "skills" / "google-docs" / "scripts" / "google-docs.py",
)
google_docs = importlib.util.module_from_spec(spec)
sys.modules["google_docs"] = google_docs
spec.loader.exec_module(google_docs)

# Now import from the loaded module
AuthenticationError = google_docs.AuthenticationError
DocsAPIError = google_docs.DocsAPIError
DOCS_SCOPES = google_docs.DOCS_SCOPES
DOCS_SCOPES_DEFAULT = google_docs.DOCS_SCOPES_DEFAULT
DRIVE_SCOPES_READONLY = google_docs.DRIVE_SCOPES_READONLY
_parse_inline = google_docs._parse_inline
apply_formatting = google_docs.apply_formatting
append_text = google_docs.append_text
build_insert_requests = google_docs.build_insert_requests
build_docs_service = google_docs.build_docs_service
build_drive_service = google_docs.build_drive_service
build_parser = google_docs.build_parser
check_docs_connectivity = google_docs.check_docs_connectivity
cmd_auth_setup = google_docs.cmd_auth_setup
cmd_auth_reset = google_docs.cmd_auth_reset
cmd_auth_status = google_docs.cmd_auth_status
cmd_check = google_docs.cmd_check
cmd_content_append = google_docs.cmd_content_append
cmd_content_delete = google_docs.cmd_content_delete
cmd_content_insert = google_docs.cmd_content_insert
cmd_content_insert_after_anchor = google_docs.cmd_content_insert_after_anchor
cmd_documents_create = google_docs.cmd_documents_create
cmd_documents_get = google_docs.cmd_documents_get
cmd_documents_read = google_docs.cmd_documents_read
cmd_formatting_apply = google_docs.cmd_formatting_apply
create_document = google_docs.create_document
delete_content = google_docs.delete_content
delete_credential = google_docs.delete_credential
format_document_summary = google_docs.format_document_summary
get_credential = google_docs.get_credential
get_document = google_docs.get_document
get_google_credentials = google_docs.get_google_credentials
_run_oauth_flow = google_docs._run_oauth_flow
get_oauth_client_config = google_docs.get_oauth_client_config
export_document_as_markdown = google_docs.export_document_as_markdown
export_document_as_pdf = google_docs.export_document_as_pdf
find_anchor_index = google_docs.find_anchor_index
handle_api_error = google_docs.handle_api_error
insert_after_anchor = google_docs.insert_after_anchor
insert_text = google_docs.insert_text
load_config = google_docs.load_config
parse_markdown = google_docs.parse_markdown
read_document_content = google_docs.read_document_content
save_config = google_docs.save_config
set_credential = google_docs.set_credential

# ============================================================================
# KEYRING CREDENTIAL TESTS
# ============================================================================


class TestKeyringFunctions:
    """Tests for keyring credential functions."""

    @patch("google_docs.keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch("google_docs.keyring")
    def test_get_credential_not_found(self, mock_keyring):
        """Test getting non-existent credential."""
        mock_keyring.get_password.return_value = None
        result = get_credential("nonexistent")
        assert result is None

    @patch("google_docs.keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch("google_docs.keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")

    @patch("google_docs.keyring")
    def test_delete_credential_not_exists(self, mock_keyring):
        """Test deleting non-existent credential doesn't raise error."""
        import keyring.errors

        mock_keyring.errors.PasswordDeleteError = keyring.errors.PasswordDeleteError
        mock_keyring.delete_password.side_effect = keyring.errors.PasswordDeleteError("Not found")
        # Should not raise
        delete_credential("test-key")


# ============================================================================
# CONFIG MANAGEMENT TESTS
# ============================================================================


class TestConfigManagement:
    """Tests for config file management."""

    def test_load_config_nonexistent(self, tmp_path, monkeypatch):
        """Test loading config when file doesn't exist."""
        monkeypatch.setattr("google_docs.CONFIG_DIR", tmp_path / "nonexistent")
        config = load_config("google-docs")
        assert config is None

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        config_dir = tmp_path / "config"
        monkeypatch.setattr("google_docs.CONFIG_DIR", config_dir)

        test_config = {
            "oauth_client": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
            }
        }

        save_config("google-docs", test_config)
        loaded = load_config("google-docs")

        assert loaded == test_config


# ============================================================================
# OAUTH CLIENT CONFIG TESTS
# ============================================================================


class TestOAuthClientConfig:
    """Tests for OAuth client configuration."""

    @patch("google_docs.load_config")
    def test_get_oauth_client_config_from_service_file(self, mock_load_config):
        """Test getting OAuth config from service-specific file."""
        mock_load_config.return_value = {
            "oauth_client": {
                "client_id": "file-client-id",
                "client_secret": "file-client-secret",
            }
        }

        config = get_oauth_client_config("google-docs")

        assert config["installed"]["client_id"] == "file-client-id"
        assert config["installed"]["client_secret"] == "file-client-secret"

    @patch("google_docs.load_config")
    def test_get_oauth_client_config_from_service_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from service-specific environment."""
        mock_load_config.return_value = None
        monkeypatch.setenv("GOOGLE_DOCS_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("GOOGLE_DOCS_CLIENT_SECRET", "env-client-secret")

        config = get_oauth_client_config("google-docs")

        assert config["installed"]["client_id"] == "env-client-id"
        assert config["installed"]["client_secret"] == "env-client-secret"

    @patch("google_docs.load_config")
    def test_get_oauth_client_config_from_shared_file(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared google.yaml file."""
        # No service-specific config or env vars
        monkeypatch.delenv("GOOGLE_DOCS_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_DOCS_CLIENT_SECRET", raising=False)

        def side_effect(service):
            if service == "google":
                return {
                    "oauth_client": {
                        "client_id": "shared-file-client-id",
                        "client_secret": "shared-file-client-secret",
                    }
                }
            return None

        mock_load_config.side_effect = side_effect

        config = get_oauth_client_config("google-docs")

        assert config["installed"]["client_id"] == "shared-file-client-id"
        assert config["installed"]["client_secret"] == "shared-file-client-secret"

    @patch("google_docs.load_config")
    def test_get_oauth_client_config_from_shared_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared environment variables."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_DOCS_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_DOCS_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "shared-env-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shared-env-client-secret")

        config = get_oauth_client_config("google-docs")

        assert config["installed"]["client_id"] == "shared-env-client-id"
        assert config["installed"]["client_secret"] == "shared-env-client-secret"

    @patch("google_docs.load_config")
    def test_get_oauth_client_config_not_found(self, mock_load_config, monkeypatch):
        """Test error when OAuth config not found anywhere."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_DOCS_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_DOCS_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        with pytest.raises(AuthenticationError, match="OAuth client credentials not found"):
            get_oauth_client_config("google-docs")


# ============================================================================
# DOCUMENT OPERATION TESTS
# ============================================================================


class TestDocumentOperations:
    """Tests for document operations."""

    def test_create_document(self):
        """Test creating a document."""
        mock_service = Mock()
        mock_service.documents().create().execute.return_value = {
            "documentId": "test-doc-id",
            "title": "Test Document",
        }

        result = create_document(mock_service, "Test Document")

        assert result["documentId"] == "test-doc-id"
        assert result["title"] == "Test Document"

    def test_get_document(self):
        """Test getting a document."""
        mock_service = Mock()
        mock_service.documents().get().execute.return_value = {
            "documentId": "test-doc-id",
            "title": "Test Document",
            "body": {"content": []},
        }

        result = get_document(mock_service, "test-doc-id")

        assert result["documentId"] == "test-doc-id"

    def test_read_document_content(self):
        """Test reading document content."""
        mock_service = Mock()
        mock_service.documents().get().execute.return_value = {
            "documentId": "test-doc-id",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Hello "}},
                                {"textRun": {"content": "World"}},
                            ]
                        }
                    }
                ]
            },
        }

        result = read_document_content(mock_service, "test-doc-id")

        assert result == "Hello World"

    def test_append_text(self):
        """Test appending text to document."""
        mock_service = Mock()
        mock_service.documents().get().execute.return_value = {
            "body": {"content": [{}, {"endIndex": 10}]}
        }
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = append_text(mock_service, "test-doc-id", "New text")

        assert result == {}
        # Verify the correct request was made
        call_args = mock_service.documents().batchUpdate.call_args
        assert call_args[1]["documentId"] == "test-doc-id"
        assert call_args[1]["body"]["requests"][0]["insertText"]["text"] == "New text"
        assert call_args[1]["body"]["requests"][0]["insertText"]["location"]["index"] == 9

    def test_insert_text(self):
        """Test inserting text at specific position."""
        mock_service = Mock()
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = insert_text(mock_service, "test-doc-id", "Insert this", 5)

        assert result == {}
        call_args = mock_service.documents().batchUpdate.call_args
        assert call_args[1]["documentId"] == "test-doc-id"
        assert call_args[1]["body"]["requests"][0]["insertText"]["text"] == "Insert this"
        assert call_args[1]["body"]["requests"][0]["insertText"]["location"]["index"] == 5

    def test_delete_content(self):
        """Test deleting content range."""
        mock_service = Mock()
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = delete_content(mock_service, "test-doc-id", 10, 50)

        assert result == {}
        call_args = mock_service.documents().batchUpdate.call_args
        assert call_args[1]["documentId"] == "test-doc-id"
        request = call_args[1]["body"]["requests"][0]["deleteContentRange"]["range"]
        assert request["startIndex"] == 10
        assert request["endIndex"] == 50

    def test_apply_formatting(self):
        """Test applying text formatting."""
        mock_service = Mock()
        mock_service.documents().batchUpdate().execute.return_value = {}

        result = apply_formatting(
            mock_service, "test-doc-id", 1, 20, bold=True, italic=True, font_size=14
        )

        assert result == {}
        call_args = mock_service.documents().batchUpdate.call_args
        assert call_args[1]["documentId"] == "test-doc-id"
        request = call_args[1]["body"]["requests"][0]["updateTextStyle"]
        assert request["range"]["startIndex"] == 1
        assert request["range"]["endIndex"] == 20
        assert request["textStyle"]["bold"] is True
        assert request["textStyle"]["italic"] is True
        assert request["textStyle"]["fontSize"]["magnitude"] == 14

    @patch("google_docs.build_drive_service")
    def test_export_document_as_markdown(self, mock_build_drive):
        """Test exporting document as markdown."""
        mock_service = Mock()
        mock_build_drive.return_value = mock_service
        mock_service.files().export().execute.return_value = b"# Heading\n\nParagraph text"

        result = export_document_as_markdown("test-doc-id")

        assert result == "# Heading\n\nParagraph text"
        # Verify export was called with correct parameters
        call_args = mock_service.files().export.call_args
        assert call_args[1]["fileId"] == "test-doc-id"
        assert call_args[1]["mimeType"] == "text/markdown"

    @patch("google_docs.build_drive_service")
    def test_export_document_as_pdf(self, mock_build_drive):
        """Test exporting document as PDF."""
        mock_service = Mock()
        mock_build_drive.return_value = mock_service
        mock_service.files().export().execute.return_value = b"%PDF-1.4 mock content"

        result = export_document_as_pdf("test-doc-id")

        assert result == b"%PDF-1.4 mock content"
        # Verify export was called with correct parameters
        call_args = mock_service.files().export.call_args
        assert call_args[1]["fileId"] == "test-doc-id"
        assert call_args[1]["mimeType"] == "application/pdf"


# ============================================================================
# OUTPUT FORMATTING TESTS
# ============================================================================


class TestOutputFormatting:
    """Tests for output formatting functions."""

    def test_format_document_summary(self):
        """Test formatting document summary as markdown."""
        doc = {
            "documentId": "abc123",
            "title": "Test Doc",
            "revisionId": "rev456",
            "body": {
                "content": [{"paragraph": {"elements": [{"textRun": {"content": "Hello World"}}]}}]
            },
        }

        result = format_document_summary(doc)

        assert result.startswith("### Test Doc\n")
        assert "- **Document ID:** abc123" in result
        assert "- **Characters:** 11" in result
        assert "- **Revision ID:** rev456" in result


# ============================================================================
# CLI COMMAND HANDLER TESTS
# ============================================================================


class TestCLICommands:
    """Tests for CLI command handlers."""

    @patch("google_docs.check_docs_connectivity")
    def test_cmd_check_success(self, mock_check, capsys):
        """Test check command when authenticated."""
        mock_check.return_value = {
            "authenticated": True,
            "test_document_id": "test-doc-123",
            "scopes": {"readonly": True, "write": True, "all_scopes": []},
        }

        args = Mock()
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Successfully authenticated" in captured.out

    @patch("google_docs.check_docs_connectivity")
    def test_cmd_check_failure(self, mock_check, capsys):
        """Test check command when authentication fails."""
        mock_check.return_value = {
            "authenticated": False,
            "error": "No credentials found",
        }

        args = Mock()
        result = cmd_check(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Authentication failed" in captured.out

    @patch("google_docs.save_config")
    @patch("google_docs.load_config")
    def test_cmd_auth_setup(self, mock_load, mock_save, capsys):
        """Test auth setup command."""
        mock_load.return_value = None
        args = Mock(client_id="test-id", client_secret="test-secret")

        result = cmd_auth_setup(args)

        assert result == 0
        mock_save.assert_called_once()
        captured = capsys.readouterr()
        assert "OAuth client credentials saved" in captured.out

    @patch("google_docs.build_docs_service")
    @patch("google_docs.create_document")
    def test_cmd_documents_create(self, mock_create, _mock_build_service, capsys):
        """Test documents create command."""
        mock_create.return_value = {
            "documentId": "new-doc-123",
            "title": "New Document",
        }

        args = Mock(title="New Document", json=False)
        result = cmd_documents_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Document created successfully" in captured.out
        assert "new-doc-123" in captured.out

    @patch("google_docs.build_docs_service")
    @patch("google_docs.get_document")
    def test_cmd_documents_get(self, mock_get, _mock_build_service, capsys):
        """Test documents get command."""
        mock_get.return_value = {
            "documentId": "doc-123",
            "title": "Test Document",
            "revisionId": "rev-456",
            "body": {"content": []},
        }

        args = Mock(document_id="doc-123", json=False)
        result = cmd_documents_get(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Test Document" in captured.out

    @patch("google_docs.build_docs_service")
    @patch("google_docs.read_document_content")
    def test_cmd_documents_read(self, mock_read, _mock_build_service, capsys):
        """Test documents read command."""
        mock_read.return_value = "Document content here"

        args = Mock(document_id="doc-123", format="text", json=False)
        result = cmd_documents_read(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Document content here" in captured.out

    @patch("google_docs.export_document_as_markdown")
    def test_cmd_documents_read_markdown_format(self, mock_export, capsys):
        """Test documents read command with markdown format."""
        mock_export.return_value = "# Title\n\nMarkdown content"

        args = Mock(document_id="doc-123", format="markdown", json=False)
        result = cmd_documents_read(args)

        assert result == 0
        mock_export.assert_called_once_with("doc-123")
        captured = capsys.readouterr()
        assert "# Title" in captured.out
        assert "Markdown content" in captured.out

    @patch("google_docs.export_document_as_pdf")
    def test_cmd_documents_read_pdf_format(self, mock_export, tmp_path, capsys):
        """Test documents read command with PDF format."""
        mock_export.return_value = b"%PDF-1.4 mock content"
        output_file = tmp_path / "test.pdf"

        args = Mock(document_id="doc-123", format="pdf", output=str(output_file), json=False)
        result = cmd_documents_read(args)

        assert result == 0
        assert output_file.exists()
        assert output_file.read_bytes() == b"%PDF-1.4 mock content"
        captured = capsys.readouterr()
        assert "PDF saved to:" in captured.out

    @patch("google_docs.export_document_as_pdf")
    def test_cmd_documents_read_pdf_format_default_output(
        self, mock_export, tmp_path, capsys, monkeypatch
    ):
        """Test documents read command with PDF format using default output filename."""
        mock_export.return_value = b"%PDF-1.4 mock content"
        # Change to tmp_path so default file is created there
        monkeypatch.chdir(tmp_path)

        args = Mock(document_id="doc-123", format="pdf", output=None, json=False)
        result = cmd_documents_read(args)

        assert result == 0
        default_file = tmp_path / "doc-123.pdf"
        assert default_file.exists()
        assert default_file.read_bytes() == b"%PDF-1.4 mock content"
        captured = capsys.readouterr()
        assert "PDF saved to: doc-123.pdf" in captured.out

    @patch("google_docs.delete_credential")
    @patch("builtins.print")
    def test_cmd_auth_reset(self, _mock_print, mock_delete):
        """Test auth reset command."""
        args = Mock()
        exit_code = cmd_auth_reset(args)

        assert exit_code == 0
        mock_delete.assert_called_once_with("google-docs-token-json")

    @patch("google_docs.get_credential")
    @patch("builtins.print")
    def test_cmd_auth_status_with_token(self, _mock_print, mock_get_credential):
        """Test auth status command with stored token."""
        token_data = {
            "token": "access-token",
            "refresh_token": "refresh-token",
            "scopes": ["https://www.googleapis.com/auth/documents.readonly"],
            "expiry": "2025-01-01T00:00:00Z",
            "client_id": "1234567890abcdef.apps.googleusercontent.com",
        }
        mock_get_credential.return_value = json.dumps(token_data)

        args = Mock()
        exit_code = cmd_auth_status(args)

        assert exit_code == 0

    @patch("google_docs.get_credential")
    @patch("builtins.print")
    def test_cmd_auth_status_no_token(self, _mock_print, mock_get_credential):
        """Test auth status command with no stored token."""
        mock_get_credential.return_value = None

        args = Mock()
        exit_code = cmd_auth_status(args)

        assert exit_code == 1


# ============================================================================
# ARGUMENT PARSER TESTS
# ============================================================================


class TestArgumentParser:
    """Tests for CLI argument parser."""

    def test_parser_check_command(self):
        """Test parser for check command."""
        parser = build_parser()
        args = parser.parse_args(["check"])
        assert args.command == "check"

    def test_parser_auth_setup(self):
        """Test parser for auth setup command."""
        parser = build_parser()
        args = parser.parse_args(
            ["auth", "setup", "--client-id", "id", "--client-secret", "secret"]
        )
        assert args.command == "auth"
        assert args.auth_command == "setup"
        assert args.client_id == "id"
        assert args.client_secret == "secret"

    def test_parser_auth_reset(self):
        """Test parser for auth reset command."""
        parser = build_parser()

        # Test auth reset
        args = parser.parse_args(["auth", "reset"])
        assert args.command == "auth"
        assert args.auth_command == "reset"

    def test_parser_auth_status(self):
        """Test parser for auth status command."""
        parser = build_parser()

        # Test auth status
        args = parser.parse_args(["auth", "status"])
        assert args.command == "auth"
        assert args.auth_command == "status"

    def test_parser_documents_create(self):
        """Test parser for documents create command."""
        parser = build_parser()
        args = parser.parse_args(["documents", "create", "--title", "Test"])
        assert args.command == "documents"
        assert args.documents_command == "create"
        assert args.title == "Test"

    def test_parser_documents_read_with_format(self):
        """Test parser for documents read with format option."""
        parser = build_parser()
        args = parser.parse_args(["documents", "read", "doc-123", "--format", "markdown"])
        assert args.command == "documents"
        assert args.documents_command == "read"
        assert args.document_id == "doc-123"
        assert args.format == "markdown"

    def test_parser_documents_read_default_format(self):
        """Test parser for documents read defaults to markdown format."""
        parser = build_parser()
        args = parser.parse_args(["documents", "read", "doc-123"])
        assert args.format == "markdown"

    def test_parser_documents_read_pdf_format(self):
        """Test parser for documents read with pdf format and output."""
        parser = build_parser()
        args = parser.parse_args(
            ["documents", "read", "doc-123", "--format", "pdf", "--output", "output.pdf"]
        )
        assert args.format == "pdf"
        assert args.output == "output.pdf"

    def test_parser_documents_read_output_short_flag(self):
        """Test parser for documents read with -o short flag."""
        parser = build_parser()
        args = parser.parse_args(
            ["documents", "read", "doc-123", "--format", "pdf", "-o", "doc.pdf"]
        )
        assert args.output == "doc.pdf"

    def test_parser_content_append(self):
        """Test parser for content append command."""
        parser = build_parser()
        args = parser.parse_args(["content", "append", "doc-id", "--text", "Hello"])
        assert args.command == "content"
        assert args.content_command == "append"
        assert args.document_id == "doc-id"
        assert args.text == "Hello"

    def test_parser_formatting_apply(self):
        """Test parser for formatting apply command."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "formatting",
                "apply",
                "doc-id",
                "--start-index",
                "1",
                "--end-index",
                "10",
                "--bold",
                "--italic",
                "--font-size",
                "14",
            ]
        )
        assert args.command == "formatting"
        assert args.formatting_command == "apply"
        assert args.document_id == "doc-id"
        assert args.start_index == 1
        assert args.end_index == 10
        assert args.bold is True
        assert args.italic is True
        assert args.font_size == 14


# ============================================================================
# AUTHENTICATION FLOW TESTS
# ============================================================================


class TestAuthenticationFlow:
    """Tests for authentication flow edge cases."""

    @patch("google_docs.InstalledAppFlow")
    @patch("google_docs.get_oauth_client_config")
    @patch("google_docs.set_credential")
    @patch("google_docs.get_credential")
    def test_get_google_credentials_oauth_flow(
        self, mock_get_cred, mock_set_cred, mock_get_config, mock_flow_class
    ):
        """Test OAuth flow when no token exists."""
        mock_get_cred.return_value = None
        mock_config = {"installed": {"client_id": "id", "client_secret": "secret"}}
        mock_get_config.return_value = mock_config

        mock_flow_instance = Mock()
        mock_flow_class.from_client_config.return_value = mock_flow_instance
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "new"}'
        mock_flow_instance.run_local_server.return_value = mock_creds

        result = get_google_credentials("google-docs", ["https://scope"])

        assert result == mock_creds
        mock_set_cred.assert_called_once_with("google-docs-token-json", '{"token": "new"}')

    @patch("google_docs.Request")
    @patch("google_docs.Credentials")
    @patch("google_docs.set_credential")
    @patch("google_docs.get_credential")
    def test_get_google_credentials_refresh_token(
        self, mock_get_cred, mock_set_cred, mock_creds_class, _mock_request_class
    ):
        """Test token refresh when expired."""
        token_json = '{"token": "expired", "refresh_token": "refresh"}'
        mock_get_cred.return_value = token_json

        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh"
        mock_creds.to_json.return_value = '{"token": "refreshed"}'
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        result = get_google_credentials("google-docs", ["https://scope"])

        mock_creds.refresh.assert_called_once()
        mock_set_cred.assert_called_once_with("google-docs-token-json", '{"token": "refreshed"}')
        assert result == mock_creds

    @patch("google_docs.InstalledAppFlow")
    @patch("google_docs.get_oauth_client_config")
    @patch("google_docs.Credentials")
    @patch("google_docs.get_credential")
    def test_get_google_credentials_corrupted_token(
        self, mock_get_cred, mock_creds_class, mock_get_config, _mock_flow_class
    ):
        """Test handling of corrupted token."""
        mock_get_cred.return_value = "invalid json"
        mock_creds_class.from_authorized_user_info.side_effect = Exception("Parse error")

        # Mock OAuth flow to raise error
        mock_get_config.side_effect = AuthenticationError("No credentials")

        # Should fall through to OAuth flow, which will fail
        with pytest.raises(AuthenticationError):
            get_google_credentials("google-docs", ["https://scope"])

    @patch("google_docs.InstalledAppFlow")
    @patch("google_docs.get_oauth_client_config")
    @patch("google_docs.get_credential")
    def test_get_google_credentials_oauth_flow_failure(
        self, mock_get_cred, mock_get_config, mock_flow_class
    ):
        """Test OAuth flow failure."""
        mock_get_cred.return_value = None
        mock_config = {"installed": {"client_id": "id", "client_secret": "secret"}}
        mock_get_config.return_value = mock_config

        mock_flow_instance = Mock()
        mock_flow_class.from_client_config.return_value = mock_flow_instance
        mock_flow_instance.run_local_server.side_effect = Exception("Flow failed")

        with pytest.raises(AuthenticationError, match="OAuth flow failed"):
            get_google_credentials("google-docs", ["https://scope"])

    @patch("google_docs.delete_credential")
    @patch("google_docs._run_oauth_flow")
    @patch("google_docs.get_credential")
    @patch("google_docs.Credentials")
    def test_get_google_credentials_scope_mismatch(
        self,
        mock_creds_class,
        mock_get_credential,
        mock_run_oauth,
        mock_delete_credential,
    ):
        """Test re-auth triggers when token lacks requested scopes."""
        token_data = {
            "token": "access-token",
            "refresh_token": "refresh-token",
            "scopes": ["https://www.googleapis.com/auth/documents.readonly"],
        }
        mock_get_credential.return_value = json.dumps(token_data)

        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        mock_new_creds = Mock()
        mock_run_oauth.return_value = mock_new_creds

        result = get_google_credentials(
            "google-docs",
            [
                "https://www.googleapis.com/auth/documents.readonly",
                "https://www.googleapis.com/auth/documents",
            ],
        )

        assert result == mock_new_creds
        mock_delete_credential.assert_called_once_with("google-docs-token-json")
        call_args = mock_run_oauth.call_args[0]
        merged_scopes = set(call_args[1])
        assert "https://www.googleapis.com/auth/documents.readonly" in merged_scopes
        assert "https://www.googleapis.com/auth/documents" in merged_scopes

    @patch("google_docs.get_credential")
    @patch("google_docs.Credentials")
    def test_get_google_credentials_no_scopes_in_token(self, mock_creds_class, mock_get_credential):
        """Test backward compatibility when token has no scopes field."""
        token_data = {"token": "access-token", "refresh_token": "refresh-token"}
        mock_get_credential.return_value = json.dumps(token_data)

        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        result = get_google_credentials("google-docs", ["https://scope"])

        assert result == mock_creds


# ============================================================================
# API ERROR HANDLING TESTS
# ============================================================================


class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_handle_api_error_basic(self):
        """Test basic API error handling."""
        from googleapiclient.errors import HttpError

        error = Mock(spec=HttpError)
        error.resp = Mock()
        error.resp.status = 404
        error.resp.reason = "Not found"
        error.content = b'{"error": {"message": "Document not found"}}'

        with pytest.raises(DocsAPIError, match="Document not found.*404"):
            handle_api_error(error)

    def test_handle_api_error_insufficient_scope(self):
        """Test insufficient scope error with helpful message."""
        from googleapiclient.errors import HttpError

        error = Mock(spec=HttpError)
        error.resp = Mock()
        error.resp.status = 403
        error.resp.reason = "Forbidden"
        error.content = b'{"error": {"message": "Insufficient permissions"}}'

        with pytest.raises(DocsAPIError, match="Insufficient OAuth scope"):
            handle_api_error(error)

    def test_handle_api_error_malformed_response(self):
        """Test error with malformed JSON response."""
        from googleapiclient.errors import HttpError

        error = Mock(spec=HttpError)
        error.resp = Mock()
        error.resp.status = 500
        error.resp.reason = "Internal Server Error"
        error.content = b"not json"

        with pytest.raises(DocsAPIError, match="Internal Server Error.*500"):
            handle_api_error(error)

    def test_docs_api_error_attributes(self):
        """Test DocsAPIError attributes."""
        error = DocsAPIError("Test error", status_code=404, details={"key": "value"})
        assert str(error) == "Test error"
        assert error.status_code == 404
        assert error.details == {"key": "value"}


# ============================================================================
# COMMAND HANDLER TESTS (CONTENT AND FORMATTING)
# ============================================================================


class TestContentCommands:
    """Tests for content manipulation commands."""

    @patch("google_docs.build_docs_service")
    @patch("google_docs.append_text")
    def test_cmd_content_append(self, mock_append, _mock_build_service, capsys):
        """Test content append command."""
        mock_append.return_value = {}

        args = Mock(document_id="doc-123", text="New paragraph", json=False)
        result = cmd_content_append(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Text appended successfully" in captured.out

    @patch("google_docs.build_docs_service")
    @patch("google_docs.insert_text")
    def test_cmd_content_insert(self, mock_insert, _mock_build_service, capsys):
        """Test content insert command."""
        mock_insert.return_value = {}

        args = Mock(document_id="doc-123", text="Inserted text", index=10, json=False)
        result = cmd_content_insert(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Text inserted successfully" in captured.out

    @patch("google_docs.build_docs_service")
    @patch("google_docs.delete_content")
    def test_cmd_content_delete(self, mock_delete, _mock_build_service, capsys):
        """Test content delete command."""
        mock_delete.return_value = {}

        args = Mock(document_id="doc-123", start_index=10, end_index=20, json=False)
        result = cmd_content_delete(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Content deleted successfully" in captured.out

    @patch("google_docs.build_docs_service")
    @patch("google_docs.apply_formatting")
    def test_cmd_formatting_apply(self, mock_format, _mock_build_service, capsys):
        """Test formatting apply command."""
        mock_format.return_value = {}

        args = Mock(
            document_id="doc-123",
            start_index=1,
            end_index=10,
            bold=True,
            italic=True,
            underline=False,
            font_size=14,
            json=False,
        )
        result = cmd_formatting_apply(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Formatting applied successfully" in captured.out


# ============================================================================
# BUILD SERVICE TESTS
# ============================================================================


class TestBuildService:
    """Tests for build_docs_service function."""

    @patch("google_docs.get_google_credentials")
    @patch("google_docs.build")
    def test_build_docs_service_default_scopes(self, mock_build, mock_get_creds):
        """Test building service with default scopes."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        result = build_docs_service()

        mock_get_creds.assert_called_once_with("google-docs", DOCS_SCOPES_DEFAULT)
        mock_build.assert_called_once_with("docs", "v1", credentials=mock_creds)
        assert result == mock_service

    @patch("google_docs.get_google_credentials")
    @patch("google_docs.build")
    def test_build_docs_service_custom_scopes(self, mock_build, mock_get_creds):
        """Test building service with custom scopes."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        custom_scopes = ["https://custom.scope"]
        result = build_docs_service(custom_scopes)

        mock_get_creds.assert_called_once_with("google-docs", custom_scopes)
        assert result == mock_service

    @patch("google_docs.get_google_credentials")
    @patch("google_docs.build")
    def test_build_drive_service_default_scopes(self, mock_build, mock_get_creds):
        """Test building Drive service with default scopes."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        result = build_drive_service()

        mock_get_creds.assert_called_once_with("google-docs", DRIVE_SCOPES_READONLY)
        mock_build.assert_called_once_with("drive", "v3", credentials=mock_creds)
        assert result == mock_service


# ============================================================================
# MARKDOWN PARSING TESTS
# ============================================================================


class TestParseInline:
    """Tests for _parse_inline function."""

    def test_plain_text(self):
        """Test plain text without formatting."""
        runs = _parse_inline("Hello world")
        assert len(runs) == 1
        assert runs[0] == {"text": "Hello world", "bold": False, "link": None}

    def test_bold(self):
        """Test bold text."""
        runs = _parse_inline("Hello **bold** world")
        assert len(runs) == 3
        assert runs[0] == {"text": "Hello ", "bold": False, "link": None}
        assert runs[1] == {"text": "bold", "bold": True, "link": None}
        assert runs[2] == {"text": " world", "bold": False, "link": None}

    def test_link(self):
        """Test link formatting."""
        runs = _parse_inline("Click [here](https://example.com) now")
        assert len(runs) == 3
        assert runs[0] == {"text": "Click ", "bold": False, "link": None}
        assert runs[1] == {"text": "here", "bold": False, "link": "https://example.com"}
        assert runs[2] == {"text": " now", "bold": False, "link": None}

    def test_bold_and_link(self):
        """Test combined bold and link."""
        runs = _parse_inline("**Bold** and [link](https://example.com)")
        assert len(runs) == 3
        assert runs[0] == {"text": "Bold", "bold": True, "link": None}
        assert runs[1] == {"text": " and ", "bold": False, "link": None}
        assert runs[2] == {"text": "link", "bold": False, "link": "https://example.com"}

    def test_empty_string(self):
        """Test empty string."""
        runs = _parse_inline("")
        assert runs == []

    def test_unclosed_bold(self):
        """Test unclosed bold markers are treated as plain text."""
        runs = _parse_inline("Hello **unclosed")
        # All runs should be non-bold
        assert all(not r["bold"] for r in runs)
        combined = "".join(r["text"] for r in runs)
        assert combined == "Hello **unclosed"

    def test_multiple_bold(self):
        """Test multiple bold sections."""
        runs = _parse_inline("**a** and **b**")
        assert len(runs) == 3
        assert runs[0] == {"text": "a", "bold": True, "link": None}
        assert runs[1] == {"text": " and ", "bold": False, "link": None}
        assert runs[2] == {"text": "b", "bold": True, "link": None}


class TestParseMarkdown:
    """Tests for parse_markdown function."""

    def test_heading(self):
        """Test heading parsing."""
        elements = parse_markdown("## My Heading")
        assert len(elements) == 1
        assert elements[0]["type"] == "heading"
        assert elements[0]["level"] == 2
        assert elements[0]["runs"][0]["text"] == "My Heading"

    def test_heading_levels(self):
        """Test different heading levels."""
        for level in range(1, 7):
            hashes = "#" * level
            elements = parse_markdown(f"{hashes} Title")
            assert elements[0]["level"] == level

    def test_bullet(self):
        """Test bullet parsing."""
        elements = parse_markdown("- Item one\n- Item two")
        assert len(elements) == 2
        assert elements[0]["type"] == "bullet"
        assert elements[0]["level"] == 0
        assert elements[0]["runs"][0]["text"] == "Item one"
        assert elements[1]["runs"][0]["text"] == "Item two"

    def test_nested_bullets(self):
        """Test nested bullet parsing."""
        elements = parse_markdown("- Top level\n  - Nested\n    - Deep")
        assert len(elements) == 3
        assert elements[0]["level"] == 0
        assert elements[1]["level"] == 1
        assert elements[2]["level"] == 2

    def test_asterisk_bullets(self):
        """Test asterisk bullets."""
        elements = parse_markdown("* Item one")
        assert elements[0]["type"] == "bullet"
        assert elements[0]["runs"][0]["text"] == "Item one"

    def test_paragraph(self):
        """Test paragraph parsing."""
        elements = parse_markdown("Just a paragraph")
        assert len(elements) == 1
        assert elements[0]["type"] == "paragraph"
        assert elements[0]["runs"][0]["text"] == "Just a paragraph"

    def test_blank_lines_skipped(self):
        """Test that blank lines are skipped."""
        elements = parse_markdown("Line one\n\n\nLine two")
        assert len(elements) == 2

    def test_combined(self):
        """Test combined markdown."""
        md = "## Heading\n\n**Bold text:**\n- Item one\n  - Sub-item\n- [Link](https://example.com)"
        elements = parse_markdown(md)
        assert elements[0]["type"] == "heading"
        assert elements[1]["type"] == "paragraph"
        assert elements[2]["type"] == "bullet"
        assert elements[3]["type"] == "bullet"
        assert elements[3]["level"] == 1
        assert elements[4]["type"] == "bullet"

    def test_empty_input(self):
        """Test empty input."""
        elements = parse_markdown("")
        assert elements == []

    def test_inline_formatting_in_bullets(self):
        """Test inline formatting within bullets."""
        elements = parse_markdown("- **Bold** item")
        assert elements[0]["type"] == "bullet"
        assert elements[0]["runs"][0]["bold"] is True
        assert elements[0]["runs"][0]["text"] == "Bold"


# ============================================================================
# ANCHOR FINDING TESTS
# ============================================================================


class TestFindAnchorIndex:
    """Tests for find_anchor_index function."""

    def test_horizontal_rule(self):
        """Test finding horizontal rule anchor."""
        doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {"elements": [{"textRun": {"content": "Before\n"}}]},
                        "endIndex": 8,
                    },
                    {
                        "paragraph": {"elements": [{"horizontalRule": {}}]},
                        "endIndex": 10,
                    },
                    {
                        "paragraph": {"elements": [{"textRun": {"content": "After\n"}}]},
                        "endIndex": 16,
                    },
                ]
            }
        }
        assert find_anchor_index(doc, "horizontal_rule") == 10

    def test_horizontal_rule_nth_occurrence(self):
        """Test finding nth horizontal rule."""
        doc = {
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"horizontalRule": {}}]}, "endIndex": 5},
                    {"paragraph": {"elements": [{"horizontalRule": {}}]}, "endIndex": 10},
                    {"paragraph": {"elements": [{"horizontalRule": {}}]}, "endIndex": 15},
                ]
            }
        }
        assert find_anchor_index(doc, "horizontal_rule", occurrence=2) == 10
        assert find_anchor_index(doc, "horizontal_rule", occurrence=3) == 15

    def test_heading_match(self):
        """Test finding heading anchor by text."""
        doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "HEADING_2"},
                            "elements": [{"textRun": {"content": "My Section\n"}}],
                        },
                        "endIndex": 20,
                    },
                ]
            }
        }
        assert find_anchor_index(doc, "heading", "My Section") == 20

    def test_heading_case_insensitive(self):
        """Test heading match is case-insensitive."""
        doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "HEADING_1"},
                            "elements": [{"textRun": {"content": "Title Here\n"}}],
                        },
                        "endIndex": 15,
                    },
                ]
            }
        }
        assert find_anchor_index(doc, "heading", "title here") == 15

    def test_bookmark(self):
        """Test finding bookmark anchor."""
        doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"bookmarkId": "bm_abc123"}],
                        },
                        "endIndex": 5,
                    },
                ]
            }
        }
        assert find_anchor_index(doc, "bookmark", "bm_abc123") == 5

    def test_not_found_raises_error(self):
        """Test error when anchor not found."""
        doc = {"body": {"content": []}}
        with pytest.raises(DocsAPIError, match="Anchor not found"):
            find_anchor_index(doc, "horizontal_rule")

    def test_heading_requires_value(self):
        """Test heading anchor requires anchor_value."""
        doc = {"body": {"content": []}}
        with pytest.raises(DocsAPIError, match="anchor_value is required"):
            find_anchor_index(doc, "heading")

    def test_bookmark_requires_value(self):
        """Test bookmark anchor requires anchor_value."""
        doc = {"body": {"content": []}}
        with pytest.raises(DocsAPIError, match="anchor_value is required"):
            find_anchor_index(doc, "bookmark")

    def test_unknown_anchor_type(self):
        """Test unknown anchor type raises error."""
        doc = {"body": {"content": []}}
        with pytest.raises(DocsAPIError, match="Unknown anchor type"):
            find_anchor_index(doc, "unknown_type")


# ============================================================================
# BUILD INSERT REQUESTS TESTS
# ============================================================================


class TestBuildInsertRequests:
    """Tests for build_insert_requests function."""

    def test_empty_elements(self):
        """Test with no elements."""
        assert build_insert_requests([], 10) == []

    def test_simple_paragraph(self):
        """Test inserting a simple paragraph."""
        parsed = [{"type": "paragraph", "runs": [{"text": "Hello", "bold": False, "link": None}]}]
        requests = build_insert_requests(parsed, 10)
        assert len(requests) == 1
        assert requests[0]["insertText"]["text"] == "Hello\n"
        assert requests[0]["insertText"]["location"]["index"] == 10

    def test_heading_style(self):
        """Test heading generates updateParagraphStyle."""
        parsed = [
            {
                "type": "heading",
                "level": 2,
                "runs": [{"text": "Title", "bold": False, "link": None}],
            }
        ]
        requests = build_insert_requests(parsed, 5)
        assert len(requests) == 2
        assert "insertText" in requests[0]
        assert "updateParagraphStyle" in requests[1]
        style_req = requests[1]["updateParagraphStyle"]
        assert style_req["paragraphStyle"]["namedStyleType"] == "HEADING_2"
        assert style_req["range"]["startIndex"] == 5
        assert style_req["range"]["endIndex"] == 11  # 5 + len("Title\n")

    def test_bullets(self):
        """Test bullets generate createParagraphBullets."""
        parsed = [
            {
                "type": "bullet",
                "level": 0,
                "runs": [{"text": "Item 1", "bold": False, "link": None}],
            },
            {
                "type": "bullet",
                "level": 0,
                "runs": [{"text": "Item 2", "bold": False, "link": None}],
            },
        ]
        requests = build_insert_requests(parsed, 10)
        # insertText + createParagraphBullets
        assert any("createParagraphBullets" in r for r in requests)
        bullet_req = [r for r in requests if "createParagraphBullets" in r][0]
        assert bullet_req["createParagraphBullets"]["bulletPreset"] == "BULLET_DISC_CIRCLE_SQUARE"

    def test_nested_bullets_tabs(self):
        """Test nested bullets add tab prefixes."""
        parsed = [
            {"type": "bullet", "level": 0, "runs": [{"text": "Top", "bold": False, "link": None}]},
            {
                "type": "bullet",
                "level": 1,
                "runs": [{"text": "Nested", "bold": False, "link": None}],
            },
        ]
        requests = build_insert_requests(parsed, 0)
        inserted_text = requests[0]["insertText"]["text"]
        assert "\tNested\n" in inserted_text

    def test_bold_formatting(self):
        """Test bold runs generate updateTextStyle."""
        parsed = [
            {
                "type": "paragraph",
                "runs": [
                    {"text": "Normal ", "bold": False, "link": None},
                    {"text": "bold", "bold": True, "link": None},
                ],
            }
        ]
        requests = build_insert_requests(parsed, 0)
        bold_reqs = [
            r
            for r in requests
            if "updateTextStyle" in r and r["updateTextStyle"].get("textStyle", {}).get("bold")
        ]
        assert len(bold_reqs) == 1
        assert bold_reqs[0]["updateTextStyle"]["range"]["startIndex"] == 7  # len("Normal ")
        assert bold_reqs[0]["updateTextStyle"]["range"]["endIndex"] == 11  # len("Normal bold")

    def test_link_formatting(self):
        """Test link runs generate updateTextStyle with link."""
        parsed = [
            {
                "type": "paragraph",
                "runs": [
                    {"text": "Click ", "bold": False, "link": None},
                    {"text": "here", "bold": False, "link": "https://example.com"},
                ],
            }
        ]
        requests = build_insert_requests(parsed, 5)
        link_reqs = [
            r
            for r in requests
            if "updateTextStyle" in r and "link" in r["updateTextStyle"].get("textStyle", {})
        ]
        assert len(link_reqs) == 1
        assert link_reqs[0]["updateTextStyle"]["textStyle"]["link"]["url"] == "https://example.com"
        assert link_reqs[0]["updateTextStyle"]["range"]["startIndex"] == 11  # 5 + len("Click ")
        assert link_reqs[0]["updateTextStyle"]["range"]["endIndex"] == 15  # 5 + len("Click here")

    def test_index_arithmetic(self):
        """Test that all formatting indices account for insert_index offset."""
        parsed = [
            {
                "type": "heading",
                "level": 1,
                "runs": [{"text": "H", "bold": False, "link": None}],
            },
            {
                "type": "paragraph",
                "runs": [{"text": "P", "bold": True, "link": None}],
            },
        ]
        insert_at = 100
        requests = build_insert_requests(parsed, insert_at)

        # All start/end indices should be >= insert_at
        for req in requests:
            for key in ("updateParagraphStyle", "updateTextStyle", "createParagraphBullets"):
                if key in req:
                    r = req[key].get("range", {})
                    assert r.get("startIndex", insert_at) >= insert_at
                    assert r.get("endIndex", insert_at) >= insert_at


# ============================================================================
# INSERT AFTER ANCHOR TESTS
# ============================================================================


class TestInsertAfterAnchor:
    """Tests for insert_after_anchor function."""

    @patch("google_docs.get_document")
    def test_happy_path(self, mock_get_doc):
        """Test successful insert after anchor."""
        mock_service = Mock()
        mock_get_doc.return_value = {
            "body": {
                "content": [
                    {
                        "paragraph": {"elements": [{"horizontalRule": {}}]},
                        "endIndex": 10,
                    },
                ]
            }
        }
        mock_service.documents().batchUpdate().execute.return_value = {"replies": []}

        result = insert_after_anchor(
            mock_service, "doc-123", "horizontal_rule", None, "## Heading\n\n- Item"
        )

        assert result == {"replies": []}
        call_args = mock_service.documents().batchUpdate.call_args
        assert call_args[1]["documentId"] == "doc-123"
        requests = call_args[1]["body"]["requests"]
        assert any("insertText" in r for r in requests)

    @patch("google_docs.get_document")
    def test_horizontal_rule_with_occurrence(self, mock_get_doc):
        """Test horizontal_rule anchor with occurrence as anchor_value."""
        mock_service = Mock()
        mock_get_doc.return_value = {
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"horizontalRule": {}}]}, "endIndex": 5},
                    {"paragraph": {"elements": [{"horizontalRule": {}}]}, "endIndex": 15},
                ]
            }
        }
        mock_service.documents().batchUpdate().execute.return_value = {}

        insert_after_anchor(mock_service, "doc-123", "horizontal_rule", "2", "Hello")

        call_args = mock_service.documents().batchUpdate.call_args
        # The insert should be at index 15 (second horizontal rule)
        requests = call_args[1]["body"]["requests"]
        insert_req = [r for r in requests if "insertText" in r][0]
        assert insert_req["insertText"]["location"]["index"] == 15

    @patch("google_docs.get_document")
    def test_anchor_not_found(self, mock_get_doc):
        """Test error when anchor is not found."""
        mock_service = Mock()
        mock_get_doc.return_value = {"body": {"content": []}}

        with pytest.raises(DocsAPIError, match="Anchor not found"):
            insert_after_anchor(mock_service, "doc-123", "horizontal_rule", None, "## Title")

    @patch("google_docs.get_document")
    def test_empty_markdown(self, mock_get_doc):
        """Test with empty markdown produces no requests."""
        mock_service = Mock()
        mock_get_doc.return_value = {
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"horizontalRule": {}}]}, "endIndex": 10},
                ]
            }
        }

        result = insert_after_anchor(mock_service, "doc-123", "horizontal_rule", None, "")

        assert result == {}
        mock_service.documents().batchUpdate.assert_not_called()


# ============================================================================
# CMD CONTENT INSERT AFTER ANCHOR TESTS
# ============================================================================


class TestCmdContentInsertAfterAnchor:
    """Tests for cmd_content_insert_after_anchor handler."""

    @patch("google_docs.build_docs_service")
    @patch("google_docs.insert_after_anchor")
    def test_handler_output(self, mock_insert, _mock_build, capsys):
        """Test handler prints success message."""
        mock_insert.return_value = {"replies": []}

        args = Mock(
            document_id="doc-123",
            anchor_type="horizontal_rule",
            anchor_value=None,
            markdown="## Title",
            json=False,
        )
        result = cmd_content_insert_after_anchor(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Content inserted after anchor successfully" in captured.out

    @patch("google_docs.build_docs_service")
    @patch("google_docs.insert_after_anchor")
    def test_handler_json_mode(self, mock_insert, _mock_build, capsys):
        """Test handler JSON output mode."""
        mock_insert.return_value = {"replies": [{"insertText": {}}]}

        args = Mock(
            document_id="doc-123",
            anchor_type="heading",
            anchor_value="My Section",
            markdown="New content",
            json=True,
        )
        result = cmd_content_insert_after_anchor(args)

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "replies" in output

    @patch("google_docs.build_docs_service")
    @patch("google_docs.insert_after_anchor")
    def test_handler_newline_escape(self, mock_insert, _mock_build):
        """Test handler converts \\n to actual newlines."""
        mock_insert.return_value = {}

        args = Mock(
            document_id="doc-123",
            anchor_type="horizontal_rule",
            anchor_value=None,
            markdown="## Title\\n\\n- Item",
            json=False,
        )
        cmd_content_insert_after_anchor(args)

        call_args = mock_insert.call_args
        assert call_args[0][4] == "## Title\n\n- Item"


# ============================================================================
# ARGUMENT PARSER TESTS (INSERT-AFTER-ANCHOR)
# ============================================================================


class TestArgumentParserInsertAfterAnchor:
    """Tests for insert-after-anchor parser."""

    def test_parser_insert_after_anchor(self):
        """Test parser accepts insert-after-anchor command."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "content",
                "insert-after-anchor",
                "doc-123",
                "--anchor-type",
                "horizontal_rule",
                "--markdown",
                "## Title",
            ]
        )
        assert args.command == "content"
        assert args.content_command == "insert-after-anchor"
        assert args.document_id == "doc-123"
        assert args.anchor_type == "horizontal_rule"
        assert args.markdown == "## Title"

    def test_parser_insert_after_anchor_with_value(self):
        """Test parser accepts anchor-value option."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "content",
                "insert-after-anchor",
                "doc-123",
                "--anchor-type",
                "heading",
                "--anchor-value",
                "My Section",
                "--markdown",
                "New content",
            ]
        )
        assert args.anchor_type == "heading"
        assert args.anchor_value == "My Section"

    def test_parser_insert_after_anchor_choices(self):
        """Test parser rejects invalid anchor types."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                [
                    "content",
                    "insert-after-anchor",
                    "doc-123",
                    "--anchor-type",
                    "invalid_type",
                    "--markdown",
                    "Content",
                ]
            )

    def test_parser_insert_after_anchor_json_flag(self):
        """Test parser accepts --json flag."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "content",
                "insert-after-anchor",
                "doc-123",
                "--anchor-type",
                "bookmark",
                "--anchor-value",
                "bm_123",
                "--markdown",
                "Content",
                "--json",
            ]
        )
        assert args.json is True
