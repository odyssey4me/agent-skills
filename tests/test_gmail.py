"""Tests for gmail.py skill."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest

# Import from skills module
from skills.gmail.scripts.gmail import (
    AuthenticationError,
    GmailAPIError,
    build_gmail_service,
    build_parser,
    check_gmail_connectivity,
    cmd_auth_setup,
    cmd_check,
    cmd_drafts_create,
    cmd_drafts_list,
    cmd_drafts_send,
    cmd_labels_create,
    cmd_labels_list,
    cmd_messages_get,
    cmd_messages_list,
    cmd_send,
    create_draft,
    create_label,
    delete_credential,
    format_label,
    format_message_summary,
    get_credential,
    get_google_credentials,
    get_message,
    get_oauth_client_config,
    handle_api_error,
    list_drafts,
    list_labels,
    list_messages,
    load_config,
    modify_message_labels,
    save_config,
    send_draft,
    send_message,
    set_credential,
)

# ============================================================================
# KEYRING CREDENTIAL TESTS
# ============================================================================


class TestKeyringFunctions:
    """Tests for keyring credential functions."""

    @patch("skills.gmail.scripts.gmail.keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch("skills.gmail.scripts.gmail.keyring")
    def test_get_credential_not_found(self, mock_keyring):
        """Test getting non-existent credential."""
        mock_keyring.get_password.return_value = None
        result = get_credential("nonexistent")
        assert result is None

    @patch("skills.gmail.scripts.gmail.keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch("skills.gmail.scripts.gmail.keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")

    @patch("skills.gmail.scripts.gmail.keyring")
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
        monkeypatch.setattr("skills.gmail.scripts.gmail.CONFIG_DIR", tmp_path / "nonexistent")
        config = load_config("gmail")
        assert config is None

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        config_dir = tmp_path / "config"
        monkeypatch.setattr("skills.gmail.scripts.gmail.CONFIG_DIR", config_dir)

        test_config = {
            "oauth_client": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
            }
        }

        save_config("gmail", test_config)
        loaded = load_config("gmail")

        assert loaded == test_config


# ============================================================================
# OAUTH CLIENT CONFIG TESTS
# ============================================================================


class TestOAuthClientConfig:
    """Tests for OAuth client configuration."""

    @patch("skills.gmail.scripts.gmail.load_config")
    def test_get_oauth_client_config_from_service_file(self, mock_load_config):
        """Test getting OAuth config from service-specific file."""
        mock_load_config.return_value = {
            "oauth_client": {
                "client_id": "file-client-id",
                "client_secret": "file-client-secret",
            }
        }

        config = get_oauth_client_config("gmail")

        assert config["installed"]["client_id"] == "file-client-id"
        assert config["installed"]["client_secret"] == "file-client-secret"

    @patch("skills.gmail.scripts.gmail.load_config")
    def test_get_oauth_client_config_from_service_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from service-specific environment."""
        mock_load_config.return_value = None
        monkeypatch.setenv("GMAIL_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "env-client-secret")

        config = get_oauth_client_config("gmail")

        assert config["installed"]["client_id"] == "env-client-id"
        assert config["installed"]["client_secret"] == "env-client-secret"

    @patch("skills.gmail.scripts.gmail.load_config")
    def test_get_oauth_client_config_from_shared_file(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared google.yaml file."""
        # No service-specific config or env vars
        monkeypatch.delenv("GMAIL_CLIENT_ID", raising=False)
        monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)

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

        config = get_oauth_client_config("gmail")

        assert config["installed"]["client_id"] == "shared-file-client-id"
        assert config["installed"]["client_secret"] == "shared-file-client-secret"

    @patch("skills.gmail.scripts.gmail.load_config")
    def test_get_oauth_client_config_from_shared_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared environment variables."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GMAIL_CLIENT_ID", raising=False)
        monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "shared-env-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shared-env-client-secret")

        config = get_oauth_client_config("gmail")

        assert config["installed"]["client_id"] == "shared-env-client-id"
        assert config["installed"]["client_secret"] == "shared-env-client-secret"

    @patch("skills.gmail.scripts.gmail.load_config")
    def test_get_oauth_client_config_priority_service_over_shared(
        self, mock_load_config, monkeypatch
    ):
        """Test service-specific config takes priority over shared."""
        # Set both service-specific and shared env vars
        monkeypatch.setenv("GMAIL_CLIENT_ID", "service-env-id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "service-env-secret")
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "shared-env-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shared-env-secret")
        mock_load_config.return_value = None

        config = get_oauth_client_config("gmail")

        # Service-specific should take priority
        assert config["installed"]["client_id"] == "service-env-id"
        assert config["installed"]["client_secret"] == "service-env-secret"

    @patch("skills.gmail.scripts.gmail.load_config")
    def test_get_oauth_client_config_not_found(self, mock_load_config, monkeypatch):
        """Test OAuth config not found raises error."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GMAIL_CLIENT_ID", raising=False)
        monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        with pytest.raises(AuthenticationError, match="OAuth client credentials not found"):
            get_oauth_client_config("gmail")


# ============================================================================
# GOOGLE CREDENTIALS TESTS
# ============================================================================


class TestGoogleCredentials:
    """Tests for Google credentials acquisition."""

    @patch("skills.gmail.scripts.gmail.get_credential")
    @patch("google.oauth2.credentials.Credentials.from_authorized_user_info")
    def test_get_google_credentials_from_keyring(self, mock_from_user_info, mock_get_credential):
        """Test getting credentials from keyring."""
        # Keyring has token
        token_data = {"token": "access-token", "refresh_token": "refresh-token"}
        mock_get_credential.return_value = json.dumps(token_data)

        # Mock credentials object
        mock_creds = Mock()
        mock_creds.valid = True
        mock_from_user_info.return_value = mock_creds

        creds = get_google_credentials("gmail", ["scope1"])

        assert creds == mock_creds
        mock_get_credential.assert_called_with("gmail-token-json")

    @patch("skills.gmail.scripts.gmail.get_credential")
    @patch("google.oauth2.credentials.Credentials.from_authorized_user_info")
    @patch("google.auth.transport.requests.Request")
    @patch("skills.gmail.scripts.gmail.set_credential")
    def test_get_google_credentials_refresh_expired(
        self,
        mock_set_credential,
        _mock_request,
        mock_from_user_info,
        mock_get_credential,
    ):
        """Test refreshing expired credentials."""
        # Keyring has expired token
        token_data = {"token": "access-token", "refresh_token": "refresh-token"}
        mock_get_credential.return_value = json.dumps(token_data)

        # Mock expired credentials
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh-token"
        mock_creds.to_json.return_value = json.dumps({"refreshed": "token"})
        mock_from_user_info.return_value = mock_creds

        get_google_credentials("gmail", ["scope1"])

        # Should refresh
        mock_creds.refresh.assert_called_once()
        # Should save refreshed token
        mock_set_credential.assert_called_once()

    @patch("skills.gmail.scripts.gmail.get_credential")
    @patch("skills.gmail.scripts.gmail.get_oauth_client_config")
    def test_get_google_credentials_auth_error(self, mock_get_oauth_config, mock_get_credential):
        """Test authentication error when no credentials available."""
        # No keyring token
        mock_get_credential.return_value = None

        # OAuth config not found
        mock_get_oauth_config.side_effect = AuthenticationError(
            "OAuth client credentials not found"
        )

        # Should raise AuthenticationError when OAuth config also not found
        with pytest.raises(
            AuthenticationError, match="OAuth flow failed|OAuth client credentials not found"
        ):
            get_google_credentials("gmail", ["scope1"])


# ============================================================================
# API ERROR HANDLING TESTS
# ============================================================================


class TestAPIErrorHandling:
    """Tests for Gmail API error handling."""

    def test_handle_api_error_with_json(self):
        """Test handling API error with JSON response."""
        mock_error = Mock()
        mock_error.resp.status = 404
        mock_error.resp.reason = "Not Found"
        mock_error.content = b'{"error": {"message": "Message not found"}}'

        with pytest.raises(GmailAPIError) as exc_info:
            handle_api_error(mock_error)

        assert exc_info.value.status_code == 404
        assert "Message not found" in str(exc_info.value)

    def test_handle_api_error_without_json(self):
        """Test handling API error without JSON response."""
        mock_error = Mock()
        mock_error.resp.status = 500
        mock_error.resp.reason = "Internal Server Error"
        mock_error.content = b"Invalid JSON"

        with pytest.raises(GmailAPIError) as exc_info:
            handle_api_error(mock_error)

        assert exc_info.value.status_code == 500
        assert "Internal Server Error" in str(exc_info.value)

    def test_handle_api_error_insufficient_scope(self):
        """Test handling insufficient scope error (403)."""
        mock_error = Mock()
        mock_error.resp.status = 403
        mock_error.resp.reason = "Forbidden"
        mock_error.content = (
            b'{"error": {"message": "Request had insufficient authentication scopes"}}'
        )

        with pytest.raises(GmailAPIError) as exc_info:
            handle_api_error(mock_error)

        assert exc_info.value.status_code == 403
        assert "insufficient" in str(exc_info.value).lower()
        assert "re-authenticate" in str(exc_info.value).lower()
        assert "oauth-setup.md" in str(exc_info.value)


# ============================================================================
# MESSAGE OPERATIONS TESTS
# ============================================================================


class TestMessageOperations:
    """Tests for Gmail message operations."""

    def test_list_messages(self):
        """Test listing messages."""
        mock_service = Mock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}]
        }

        messages = list_messages(mock_service, query="is:unread", max_results=10)

        assert len(messages) == 1
        assert messages[0]["id"] == "msg1"

    def test_list_messages_with_labels(self):
        """Test listing messages with label filter."""
        mock_service = Mock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}]
        }

        list_messages(mock_service, label_ids=["INBOX", "UNREAD"])

        # Verify label_ids were passed
        call_kwargs = mock_service.users().messages().list.call_args[1]
        assert call_kwargs["labelIds"] == ["INBOX", "UNREAD"]

    def test_get_message(self):
        """Test getting a message."""
        mock_service = Mock()
        mock_service.users().messages().get().execute.return_value = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                ]
            },
        }

        message = get_message(mock_service, "msg123")

        assert message["id"] == "msg123"
        # Check that get was called with the right parameters
        mock_service.users().messages().get.assert_called_with(
            userId="me", id="msg123", format="full"
        )

    def test_send_message(self):
        """Test sending a message."""
        mock_service = Mock()
        mock_service.users().messages().send().execute.return_value = {
            "id": "sent123",
            "threadId": "thread123",
        }

        result = send_message(
            mock_service,
            to="recipient@example.com",
            subject="Test",
            body="Test body",
            cc="cc@example.com",
        )

        assert result["id"] == "sent123"
        # Check that send was called (verifying the body would be fragile due to base64 encoding)
        assert mock_service.users().messages().send.called


# ============================================================================
# DRAFT OPERATIONS TESTS
# ============================================================================


class TestDraftOperations:
    """Tests for Gmail draft operations."""

    def test_create_draft(self):
        """Test creating a draft."""
        mock_service = Mock()
        mock_service.users().drafts().create().execute.return_value = {
            "id": "draft123",
            "message": {"id": "msg123"},
        }

        result = create_draft(
            mock_service,
            to="recipient@example.com",
            subject="Draft",
            body="Draft body",
        )

        assert result["id"] == "draft123"
        assert mock_service.users().drafts().create.called

    def test_list_drafts(self):
        """Test listing drafts."""
        mock_service = Mock()
        mock_service.users().drafts().list().execute.return_value = {
            "drafts": [{"id": "draft1"}, {"id": "draft2"}]
        }

        drafts = list_drafts(mock_service, max_results=10)

        assert len(drafts) == 2
        assert drafts[0]["id"] == "draft1"

    def test_send_draft(self):
        """Test sending a draft."""
        mock_service = Mock()
        mock_service.users().drafts().send().execute.return_value = {
            "id": "sent123",
            "threadId": "thread123",
        }

        result = send_draft(mock_service, "draft123")

        assert result["id"] == "sent123"
        mock_service.users().drafts().send.assert_called_with(userId="me", body={"id": "draft123"})


# ============================================================================
# LABEL OPERATIONS TESTS
# ============================================================================


class TestLabelOperations:
    """Tests for Gmail label operations."""

    def test_list_labels(self):
        """Test listing labels."""
        mock_service = Mock()
        mock_service.users().labels().list().execute.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "label1", "name": "Work", "type": "user"},
            ]
        }

        labels = list_labels(mock_service)

        assert len(labels) == 2
        assert labels[0]["name"] == "INBOX"

    def test_create_label(self):
        """Test creating a label."""
        mock_service = Mock()
        mock_service.users().labels().create().execute.return_value = {
            "id": "label123",
            "name": "MyLabel",
            "type": "user",
        }

        result = create_label(mock_service, "MyLabel")

        assert result["id"] == "label123"
        assert result["name"] == "MyLabel"

    def test_modify_message_labels(self):
        """Test modifying message labels."""
        mock_service = Mock()
        mock_service.users().messages().modify().execute.return_value = {
            "id": "msg123",
            "labelIds": ["INBOX", "label1"],
        }

        result = modify_message_labels(
            mock_service, "msg123", add_labels=["label1"], remove_labels=["UNREAD"]
        )

        assert result["id"] == "msg123"
        call_kwargs = mock_service.users().messages().modify.call_args[1]
        assert call_kwargs["body"]["addLabelIds"] == ["label1"]
        assert call_kwargs["body"]["removeLabelIds"] == ["UNREAD"]


# ============================================================================
# FORMATTING TESTS
# ============================================================================


class TestFormatting:
    """Tests for output formatting functions."""

    def test_format_message_summary(self):
        """Test formatting message summary."""
        message = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ]
            },
            "snippet": "This is a preview of the message content",
        }

        formatted = format_message_summary(message)

        assert "msg123" in formatted
        assert "sender@example.com" in formatted
        assert "Test Subject" in formatted
        assert "This is a preview" in formatted

    def test_format_label(self):
        """Test formatting label."""
        label = {"id": "label123", "name": "Work", "type": "user"}

        formatted = format_label(label)

        assert "Work" in formatted
        assert "label123" in formatted
        assert "user" in formatted


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


class TestHealthCheck:
    """Tests for Gmail connectivity check."""

    @patch("skills.gmail.scripts.gmail.build")
    @patch("skills.gmail.scripts.gmail.get_google_credentials")
    def test_check_gmail_connectivity_success(self, mock_get_creds, mock_build):
        """Test successful connectivity check."""
        # Mock credentials
        mock_creds = Mock()
        mock_creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_get_creds.return_value = mock_creds

        # Mock service
        mock_service = Mock()
        mock_service.users().getProfile().execute.return_value = {
            "emailAddress": "user@example.com",
            "messagesTotal": 1234,
            "threadsTotal": 567,
        }
        mock_build.return_value = mock_service

        result = check_gmail_connectivity()

        assert result["authenticated"] is True
        assert result["profile"]["email"] == "user@example.com"
        assert result["profile"]["messages_total"] == 1234
        assert result["error"] is None

    @patch("skills.gmail.scripts.gmail.get_google_credentials")
    def test_check_gmail_connectivity_failure(self, mock_get_creds):
        """Test failed connectivity check."""
        mock_get_creds.side_effect = Exception("Auth failed")

        result = check_gmail_connectivity()

        assert result["authenticated"] is False
        assert result["profile"] is None
        assert "Auth failed" in result["error"]


# ============================================================================
# CLI COMMAND TESTS
# ============================================================================


class TestCLICommands:
    """Tests for CLI command handlers."""

    @patch("skills.gmail.scripts.gmail.check_gmail_connectivity")
    @patch("builtins.print")
    def test_cmd_check_success(self, _mock_print, mock_check):
        """Test check command with successful authentication."""
        mock_check.return_value = {
            "authenticated": True,
            "profile": {
                "email": "user@example.com",
                "messages_total": 1234,
                "threads_total": 567,
            },
            "error": None,
        }

        args = Mock()
        exit_code = cmd_check(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.check_gmail_connectivity")
    @patch("builtins.print")
    def test_cmd_check_failure(self, _mock_print, mock_check):
        """Test check command with authentication failure."""
        mock_check.return_value = {
            "authenticated": False,
            "profile": None,
            "error": "No credentials",
        }

        args = Mock()
        exit_code = cmd_check(args)

        assert exit_code == 1

    @patch("skills.gmail.scripts.gmail.save_config")
    @patch("builtins.print")
    def test_cmd_auth_setup(self, _mock_print, mock_save_config):
        """Test auth setup command."""
        args = Mock()
        args.client_id = "test-id"
        args.client_secret = "test-secret"

        exit_code = cmd_auth_setup(args)

        assert exit_code == 0
        mock_save_config.assert_called_once()

    @patch("skills.gmail.scripts.gmail.save_config")
    @patch("builtins.print")
    def test_cmd_auth_setup_missing_args(self, _mock_print, _mock_save_config):
        """Test auth setup command with missing arguments."""
        args = Mock()
        args.client_id = None
        args.client_secret = "test-secret"

        exit_code = cmd_auth_setup(args)

        assert exit_code == 1

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.list_messages")
    @patch("skills.gmail.scripts.gmail.get_message")
    @patch("builtins.print")
    def test_cmd_messages_list_text(
        self, _mock_print, mock_get_message, mock_list_messages, _mock_build_service
    ):
        """Test messages list command with text output."""
        mock_list_messages.return_value = [{"id": "msg1", "threadId": "thread1"}]
        mock_get_message.return_value = {
            "id": "msg1",
            "payload": {"headers": [{"name": "Subject", "value": "Test"}]},
            "snippet": "Test snippet",
        }

        args = Mock()
        args.query = "is:unread"
        args.max_results = 10
        args.json = False

        exit_code = cmd_messages_list(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.list_messages")
    @patch("builtins.print")
    def test_cmd_messages_list_json(self, _mock_print, mock_list_messages, _mock_build_service):
        """Test messages list command with JSON output."""
        mock_list_messages.return_value = [{"id": "msg1"}]

        args = Mock()
        args.query = None
        args.max_results = 10
        args.json = True

        exit_code = cmd_messages_list(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.send_message")
    @patch("builtins.print")
    def test_cmd_send(self, _mock_print, mock_send_message, _mock_build_service):
        """Test send command."""
        mock_send_message.return_value = {"id": "sent123", "threadId": "thread123"}

        args = Mock()
        args.to = "recipient@example.com"
        args.subject = "Test"
        args.body = "Test body"
        args.cc = None
        args.bcc = None
        args.json = False

        exit_code = cmd_send(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.list_labels")
    @patch("builtins.print")
    def test_cmd_labels_list(self, _mock_print, mock_list_labels, _mock_build_service):
        """Test labels list command."""
        mock_list_labels.return_value = [{"id": "label1", "name": "Work", "type": "user"}]

        args = Mock()
        args.json = False

        exit_code = cmd_labels_list(args)

        assert exit_code == 0


# ============================================================================
# ARGUMENT PARSER TESTS
# ============================================================================


class TestArgumentParser:
    """Tests for argument parser."""

    def test_build_parser(self):
        """Test building argument parser."""
        parser = build_parser()

        # Test check command
        args = parser.parse_args(["check"])
        assert args.command == "check"

        # Test auth setup
        args = parser.parse_args(
            ["auth", "setup", "--client-id", "id", "--client-secret", "secret"]
        )
        assert args.command == "auth"
        assert args.auth_command == "setup"
        assert args.client_id == "id"

        # Test messages list
        args = parser.parse_args(
            ["messages", "list", "--query", "is:unread", "--max-results", "20"]
        )
        assert args.command == "messages"
        assert args.messages_command == "list"
        assert args.query == "is:unread"
        assert args.max_results == 20

        # Test send
        args = parser.parse_args(
            ["send", "--to", "user@example.com", "--subject", "Test", "--body", "Body"]
        )
        assert args.command == "send"
        assert args.to == "user@example.com"
        assert args.subject == "Test"

        # Test labels create
        args = parser.parse_args(["labels", "create", "MyLabel"])
        assert args.command == "labels"
        assert args.labels_command == "create"
        assert args.name == "MyLabel"


# ============================================================================
# MORE CLI TESTS FOR COVERAGE
# ============================================================================


class TestMoreCLICommands:
    """More CLI command tests for coverage."""

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.get_message")
    @patch("builtins.print")
    def test_cmd_messages_get_json(self, _mock_print, mock_get_message, _mock_build_service):
        """Test messages get command with JSON output."""
        mock_get_message.return_value = {"id": "msg123", "snippet": "test"}

        args = Mock()
        args.message_id = "msg123"
        args.format = "full"
        args.json = True

        exit_code = cmd_messages_get(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.get_message")
    @patch("builtins.print")
    def test_cmd_messages_get_text(self, _mock_print, mock_get_message, _mock_build_service):
        """Test messages get command with text output."""
        mock_get_message.return_value = {
            "id": "msg123",
            "payload": {"headers": [{"name": "Subject", "value": "Test"}]},
            "snippet": "test",
        }

        args = Mock()
        args.message_id = "msg123"
        args.format = "full"
        args.json = False

        exit_code = cmd_messages_get(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.create_draft")
    @patch("builtins.print")
    def test_cmd_drafts_create_json(self, _mock_print, mock_create_draft, _mock_build_service):
        """Test drafts create command with JSON output."""
        mock_create_draft.return_value = {"id": "draft123"}

        args = Mock()
        args.to = "test@example.com"
        args.subject = "Test"
        args.body = "Body"
        args.cc = None
        args.bcc = None
        args.json = True

        exit_code = cmd_drafts_create(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.send_draft")
    @patch("builtins.print")
    def test_cmd_drafts_send_text(self, _mock_print, mock_send_draft, _mock_build_service):
        """Test drafts send command with text output."""
        mock_send_draft.return_value = {"id": "sent123", "threadId": "thread123"}

        args = Mock()
        args.draft_id = "draft123"
        args.json = False

        exit_code = cmd_drafts_send(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.create_label")
    @patch("builtins.print")
    def test_cmd_labels_create_json(self, _mock_print, mock_create_label, _mock_build_service):
        """Test labels create command with JSON output."""
        mock_create_label.return_value = {"id": "label123", "name": "MyLabel"}

        args = Mock()
        args.name = "MyLabel"
        args.json = True

        exit_code = cmd_labels_create(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.create_label")
    @patch("builtins.print")
    def test_cmd_labels_create_text(self, _mock_print, mock_create_label, _mock_build_service):
        """Test labels create command with text output."""
        mock_create_label.return_value = {"id": "label123", "name": "MyLabel", "type": "user"}

        args = Mock()
        args.name = "MyLabel"
        args.json = False

        exit_code = cmd_labels_create(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.create_draft")
    @patch("builtins.print")
    def test_cmd_drafts_create_text(self, _mock_print, mock_create_draft, _mock_build_service):
        """Test drafts create command with text output."""
        mock_create_draft.return_value = {"id": "draft123"}

        args = Mock()
        args.to = "test@example.com"
        args.subject = "Test"
        args.body = "Body"
        args.cc = None
        args.bcc = None
        args.json = False

        exit_code = cmd_drafts_create(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.send_draft")
    @patch("builtins.print")
    def test_cmd_drafts_send_json(self, _mock_print, mock_send_draft, _mock_build_service):
        """Test drafts send command with JSON output."""
        mock_send_draft.return_value = {"id": "sent123", "threadId": "thread123"}

        args = Mock()
        args.draft_id = "draft123"
        args.json = True

        exit_code = cmd_drafts_send(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.send_message")
    @patch("builtins.print")
    def test_cmd_send_json(self, _mock_print, mock_send, _mock_build_service):
        """Test send command with JSON output."""
        mock_send.return_value = {"id": "sent123", "threadId": "thread123"}

        args = Mock()
        args.to = "test@example.com"
        args.subject = "Test"
        args.body = "Body"
        args.cc = None
        args.bcc = None
        args.json = True

        exit_code = cmd_send(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.list_drafts")
    @patch("builtins.print")
    def test_cmd_drafts_list_text(self, _mock_print, mock_list_drafts, _mock_build_service):
        """Test drafts list command with text output."""
        mock_list_drafts.return_value = [
            {"id": "draft1", "message": {"id": "msg1"}},
            {"id": "draft2", "message": {"id": "msg2"}},
        ]

        args = Mock()
        args.max_results = 10
        args.json = False

        exit_code = cmd_drafts_list(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.list_drafts")
    @patch("builtins.print")
    def test_cmd_drafts_list_json(self, _mock_print, mock_list_drafts, _mock_build_service):
        """Test drafts list command with JSON output."""
        mock_list_drafts.return_value = []

        args = Mock()
        args.max_results = 10
        args.json = True

        exit_code = cmd_drafts_list(args)

        assert exit_code == 0

    @patch("skills.gmail.scripts.gmail.build_gmail_service")
    @patch("skills.gmail.scripts.gmail.list_labels")
    @patch("builtins.print")
    def test_cmd_labels_list_json(self, _mock_print, mock_list_labels, _mock_build_service):
        """Test labels list command with JSON output."""
        mock_list_labels.return_value = []

        args = Mock()
        args.json = True

        exit_code = cmd_labels_list(args)

        assert exit_code == 0


# ============================================================================
# API ERROR HANDLING IN FUNCTIONS
# ============================================================================


class TestAPIErrorsInFunctions:
    """Test API error handling in functions."""

    def test_gmail_api_error_attributes(self):
        """Test GmailAPIError attributes."""
        error = GmailAPIError("Test message", status_code=404, details={"foo": "bar"})
        assert str(error) == "Test message"
        assert error.status_code == 404
        assert error.details == {"foo": "bar"}

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    @patch("skills.gmail.scripts.gmail.get_google_credentials")
    @patch("skills.gmail.scripts.gmail.build")
    def test_build_gmail_service(self, mock_build, mock_get_creds):
        """Test building Gmail service."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        service = build_gmail_service()

        assert service == mock_service
        mock_get_creds.assert_called_once()
        mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)

    @patch("skills.gmail.scripts.gmail.get_google_credentials")
    @patch("skills.gmail.scripts.gmail.build")
    def test_build_gmail_service_with_custom_scopes(self, mock_build, mock_get_creds):
        """Test building Gmail service with custom scopes."""
        from skills.gmail.scripts.gmail import GMAIL_SCOPES_FULL

        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        service = build_gmail_service(GMAIL_SCOPES_FULL)

        assert service == mock_service
        mock_get_creds.assert_called_once_with("gmail", GMAIL_SCOPES_FULL)
        mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)

    @patch("skills.gmail.scripts.gmail.get_google_credentials")
    @patch("skills.gmail.scripts.gmail.build")
    def test_build_gmail_service_default_readonly(self, mock_build, mock_get_creds):
        """Test building Gmail service uses read-only by default."""
        from skills.gmail.scripts.gmail import GMAIL_SCOPES_DEFAULT

        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        service = build_gmail_service()

        assert service == mock_service
        mock_get_creds.assert_called_once_with("gmail", GMAIL_SCOPES_DEFAULT)
        mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)


# ============================================================================
# MAIN FUNCTION TESTS
# ============================================================================


class TestMainFunction:
    """Tests for main() function."""

    @patch("skills.gmail.scripts.gmail.cmd_check")
    @patch("sys.argv", ["gmail.py", "check"])
    def test_main_check_command(self, mock_cmd_check):
        """Test main with check command."""
        from skills.gmail.scripts import gmail

        mock_cmd_check.return_value = 0

        # Import and call main
        exit_code = gmail.main()

        assert exit_code == 0
        mock_cmd_check.assert_called_once()

    @patch("sys.argv", ["gmail.py"])
    def test_main_no_command(self):
        """Test main with no command shows help."""
        from skills.gmail.scripts import gmail

        exit_code = gmail.main()

        assert exit_code == 1

    @patch("skills.gmail.scripts.gmail.cmd_check")
    @patch("sys.argv", ["gmail.py", "check"])
    def test_main_keyboard_interrupt(self, mock_cmd_check):
        """Test main handles KeyboardInterrupt."""
        from skills.gmail.scripts import gmail

        mock_cmd_check.side_effect = KeyboardInterrupt()

        exit_code = gmail.main()

        assert exit_code == 130

    @patch("skills.gmail.scripts.gmail.cmd_check")
    @patch("sys.argv", ["gmail.py", "check"])
    def test_main_gmail_api_error(self, mock_cmd_check):
        """Test main handles GmailAPIError."""
        from skills.gmail.scripts import gmail

        mock_cmd_check.side_effect = GmailAPIError("API Error")

        exit_code = gmail.main()

        assert exit_code == 1

    @patch("skills.gmail.scripts.gmail.cmd_check")
    @patch("sys.argv", ["gmail.py", "check"])
    def test_main_auth_error(self, mock_cmd_check):
        """Test main handles AuthenticationError."""
        from skills.gmail.scripts import gmail

        mock_cmd_check.side_effect = AuthenticationError("Auth Error")

        exit_code = gmail.main()

        assert exit_code == 1

    @patch("skills.gmail.scripts.gmail.cmd_check")
    @patch("sys.argv", ["gmail.py", "check"])
    def test_main_unexpected_error(self, mock_cmd_check):
        """Test main handles unexpected errors."""
        from skills.gmail.scripts import gmail

        mock_cmd_check.side_effect = Exception("Unexpected")

        exit_code = gmail.main()

        assert exit_code == 1
