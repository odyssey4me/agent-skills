"""Tests for google-docs.py skill."""

from __future__ import annotations

# Import from skills module - use importlib to handle hyphenated module name
import importlib.util
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
apply_formatting = google_docs.apply_formatting
append_text = google_docs.append_text
build_docs_service = google_docs.build_docs_service
build_drive_service = google_docs.build_drive_service
build_parser = google_docs.build_parser
check_docs_connectivity = google_docs.check_docs_connectivity
cmd_auth_setup = google_docs.cmd_auth_setup
cmd_check = google_docs.cmd_check
cmd_content_append = google_docs.cmd_content_append
cmd_content_delete = google_docs.cmd_content_delete
cmd_content_insert = google_docs.cmd_content_insert
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
get_oauth_client_config = google_docs.get_oauth_client_config
export_document_as_markdown = google_docs.export_document_as_markdown
export_document_as_pdf = google_docs.export_document_as_pdf
handle_api_error = google_docs.handle_api_error
insert_text = google_docs.insert_text
load_config = google_docs.load_config
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
        """Test formatting document summary."""
        doc = {
            "documentId": "abc123",
            "title": "Test Doc",
            "revisionId": "rev456",
            "body": {
                "content": [{"paragraph": {"elements": [{"textRun": {"content": "Hello World"}}]}}]
            },
        }

        result = format_document_summary(doc)

        assert "Test Doc" in result
        assert "abc123" in result
        assert "rev456" in result
        assert "11" in result  # character count


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
        """Test parser for documents read defaults to text format."""
        parser = build_parser()
        args = parser.parse_args(["documents", "read", "doc-123"])
        assert args.format == "text"

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
