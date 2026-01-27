"""Tests for google-drive.py skill."""

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
    "google_drive",
    Path(__file__).parent.parent / "skills" / "google-drive" / "scripts" / "google-drive.py",
)
google_drive = importlib.util.module_from_spec(spec)
sys.modules["google_drive"] = google_drive
spec.loader.exec_module(google_drive)

# Now import from the loaded module
AuthenticationError = google_drive.AuthenticationError
DriveAPIError = google_drive.DriveAPIError
build_drive_service = google_drive.build_drive_service
build_parser = google_drive.build_parser
check_drive_connectivity = google_drive.check_drive_connectivity
cmd_auth_setup = google_drive.cmd_auth_setup
cmd_check = google_drive.cmd_check
cmd_files_download = google_drive.cmd_files_download
cmd_files_get = google_drive.cmd_files_get
cmd_files_list = google_drive.cmd_files_list
cmd_files_search = google_drive.cmd_files_search
cmd_files_upload = google_drive.cmd_files_upload
cmd_folders_create = google_drive.cmd_folders_create
cmd_folders_list = google_drive.cmd_folders_list
cmd_permissions_delete = google_drive.cmd_permissions_delete
cmd_permissions_list = google_drive.cmd_permissions_list
cmd_share = google_drive.cmd_share
create_folder = google_drive.create_folder
delete_credential = google_drive.delete_credential
delete_permission = google_drive.delete_permission
download_file = google_drive.download_file
format_file_summary = google_drive.format_file_summary
format_permission = google_drive.format_permission
get_credential = google_drive.get_credential
get_file_metadata = google_drive.get_file_metadata
get_google_credentials = google_drive.get_google_credentials
get_oauth_client_config = google_drive.get_oauth_client_config
handle_api_error = google_drive.handle_api_error
list_files = google_drive.list_files
list_folder_contents = google_drive.list_folder_contents
list_permissions = google_drive.list_permissions
load_config = google_drive.load_config
save_config = google_drive.save_config
search_files = google_drive.search_files
set_credential = google_drive.set_credential
share_file = google_drive.share_file
upload_file = google_drive.upload_file


# ============================================================================
# KEYRING CREDENTIAL TESTS
# ============================================================================


class TestKeyringFunctions:
    """Tests for keyring credential functions."""

    @patch.object(google_drive, "keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch.object(google_drive, "keyring")
    def test_get_credential_not_found(self, mock_keyring):
        """Test getting non-existent credential."""
        mock_keyring.get_password.return_value = None
        result = get_credential("nonexistent")
        assert result is None

    @patch.object(google_drive, "keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch.object(google_drive, "keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")

    @patch.object(google_drive, "keyring")
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
        monkeypatch.setattr(google_drive, "CONFIG_DIR", tmp_path / "nonexistent")
        config = load_config("google-drive")
        assert config is None

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        config_dir = tmp_path / "config"
        monkeypatch.setattr(google_drive, "CONFIG_DIR", config_dir)

        test_config = {
            "oauth_client": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
            }
        }

        save_config("google-drive", test_config)
        loaded = load_config("google-drive")

        assert loaded == test_config


# ============================================================================
# OAUTH CLIENT CONFIG TESTS
# ============================================================================


class TestOAuthClientConfig:
    """Tests for OAuth client configuration."""

    @patch.object(google_drive, "load_config")
    def test_get_oauth_client_config_from_service_file(self, mock_load_config):
        """Test getting OAuth config from service-specific file."""
        mock_load_config.return_value = {
            "oauth_client": {
                "client_id": "file-client-id",
                "client_secret": "file-client-secret",
            }
        }

        config = get_oauth_client_config("google-drive")

        assert config["installed"]["client_id"] == "file-client-id"
        assert config["installed"]["client_secret"] == "file-client-secret"

    @patch.object(google_drive, "load_config")
    def test_get_oauth_client_config_from_service_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from service-specific environment."""
        mock_load_config.return_value = None
        monkeypatch.setenv("GOOGLE_DRIVE_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("GOOGLE_DRIVE_CLIENT_SECRET", "env-client-secret")

        config = get_oauth_client_config("google-drive")

        assert config["installed"]["client_id"] == "env-client-id"
        assert config["installed"]["client_secret"] == "env-client-secret"

    @patch.object(google_drive, "load_config")
    def test_get_oauth_client_config_from_shared_file(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared google.yaml file."""
        # No service-specific config or env vars
        monkeypatch.delenv("GOOGLE_DRIVE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_DRIVE_CLIENT_SECRET", raising=False)

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

        config = get_oauth_client_config("google-drive")

        assert config["installed"]["client_id"] == "shared-file-client-id"
        assert config["installed"]["client_secret"] == "shared-file-client-secret"

    @patch.object(google_drive, "load_config")
    def test_get_oauth_client_config_from_shared_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared environment variables."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_DRIVE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_DRIVE_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "shared-env-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shared-env-client-secret")

        config = get_oauth_client_config("google-drive")

        assert config["installed"]["client_id"] == "shared-env-client-id"
        assert config["installed"]["client_secret"] == "shared-env-client-secret"

    @patch.object(google_drive, "load_config")
    def test_get_oauth_client_config_priority_service_over_shared(
        self, mock_load_config, monkeypatch
    ):
        """Test service-specific config takes priority over shared."""
        # Set both service-specific and shared env vars
        monkeypatch.setenv("GOOGLE_DRIVE_CLIENT_ID", "service-env-id")
        monkeypatch.setenv("GOOGLE_DRIVE_CLIENT_SECRET", "service-env-secret")
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "shared-env-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shared-env-secret")
        mock_load_config.return_value = None

        config = get_oauth_client_config("google-drive")

        # Service-specific should take priority
        assert config["installed"]["client_id"] == "service-env-id"
        assert config["installed"]["client_secret"] == "service-env-secret"

    @patch.object(google_drive, "load_config")
    def test_get_oauth_client_config_not_found(self, mock_load_config, monkeypatch):
        """Test OAuth config not found raises error."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_DRIVE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_DRIVE_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        with pytest.raises(AuthenticationError, match="OAuth client credentials not found"):
            get_oauth_client_config("google-drive")


# ============================================================================
# GOOGLE CREDENTIALS TESTS
# ============================================================================


class TestGoogleCredentials:
    """Tests for Google credentials acquisition."""

    @patch.object(google_drive, "get_credential")
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

        creds = get_google_credentials("google-drive", ["scope1"])

        assert creds == mock_creds
        mock_get_credential.assert_called_with("google-drive-token-json")

    @patch.object(google_drive, "get_credential")
    @patch("google.oauth2.credentials.Credentials.from_authorized_user_info")
    @patch("google.auth.transport.requests.Request")
    @patch.object(google_drive, "set_credential")
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

        get_google_credentials("google-drive", ["scope1"])

        # Should refresh
        mock_creds.refresh.assert_called_once()
        # Should save refreshed token
        mock_set_credential.assert_called_once()

    @patch.object(google_drive, "get_credential")
    @patch.object(google_drive, "get_oauth_client_config")
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
            get_google_credentials("google-drive", ["scope1"])


# ============================================================================
# API ERROR HANDLING TESTS
# ============================================================================


class TestAPIErrorHandling:
    """Tests for Drive API error handling."""

    def test_handle_api_error_with_json(self):
        """Test handling API error with JSON response."""
        mock_error = Mock()
        mock_error.resp.status = 404
        mock_error.resp.reason = "Not Found"
        mock_error.content = b'{"error": {"message": "File not found"}}'

        with pytest.raises(DriveAPIError) as exc_info:
            handle_api_error(mock_error)

        assert exc_info.value.status_code == 404
        assert "File not found" in str(exc_info.value)

    def test_handle_api_error_without_json(self):
        """Test handling API error without JSON response."""
        mock_error = Mock()
        mock_error.resp.status = 500
        mock_error.resp.reason = "Internal Server Error"
        mock_error.content = b"Invalid JSON"

        with pytest.raises(DriveAPIError) as exc_info:
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

        with pytest.raises(DriveAPIError) as exc_info:
            handle_api_error(mock_error)

        assert exc_info.value.status_code == 403
        assert "insufficient" in str(exc_info.value).lower()
        assert "re-authenticate" in str(exc_info.value).lower()
        assert "oauth-setup.md" in str(exc_info.value)


# ============================================================================
# FILE OPERATIONS TESTS
# ============================================================================


class TestFileOperations:
    """Tests for Drive file operations."""

    def test_list_files(self):
        """Test listing files."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            "files": [{"id": "file1", "name": "Test.pdf", "mimeType": "application/pdf"}]
        }

        files = list_files(mock_service, query="name contains 'Test'", max_results=10)

        assert len(files) == 1
        assert files[0]["id"] == "file1"
        assert files[0]["name"] == "Test.pdf"

    def test_list_files_empty(self):
        """Test listing files when no files found."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {"files": []}

        files = list_files(mock_service)

        assert len(files) == 0

    def test_search_files(self):
        """Test searching files."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            "files": [{"id": "file1", "name": "Report.pdf"}]
        }

        files = search_files(mock_service, name="Report", mime_type="application/pdf")

        assert len(files) == 1
        # Verify query was built correctly
        call_kwargs = mock_service.files().list.call_args[1]
        assert "name contains 'Report'" in call_kwargs["q"]
        assert "mimeType = 'application/pdf'" in call_kwargs["q"]
        assert "trashed = false" in call_kwargs["q"]

    def test_search_files_by_folder(self):
        """Test searching files in a specific folder."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {"files": []}

        search_files(mock_service, folder_id="folder123")

        call_kwargs = mock_service.files().list.call_args[1]
        assert "'folder123' in parents" in call_kwargs["q"]

    def test_get_file_metadata(self):
        """Test getting file metadata."""
        mock_service = Mock()
        mock_service.files().get().execute.return_value = {
            "id": "file123",
            "name": "Test.pdf",
            "mimeType": "application/pdf",
            "modifiedTime": "2024-01-15T10:00:00Z",
        }

        file = get_file_metadata(mock_service, "file123")

        assert file["id"] == "file123"
        assert file["name"] == "Test.pdf"

    def test_download_file(self, tmp_path):
        """Test downloading a file."""
        mock_service = Mock()
        mock_request = Mock()
        mock_service.files().get_media.return_value = mock_request

        # Mock MediaIoBaseDownload
        with patch.object(google_drive, "MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = Mock()
            mock_downloader.next_chunk.side_effect = [(None, False), (None, True)]
            mock_downloader_class.return_value = mock_downloader

            output_path = str(tmp_path / "downloaded.pdf")
            download_file(mock_service, "file123", output_path)

            mock_service.files().get_media.assert_called_with(fileId="file123")

    def test_upload_file(self, tmp_path):
        """Test uploading a file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        mock_service = Mock()
        mock_service.files().create().execute.return_value = {
            "id": "newfile123",
            "name": "test.txt",
            "mimeType": "text/plain",
            "webViewLink": "https://drive.google.com/file/d/newfile123",
        }

        with patch.object(google_drive, "MediaFileUpload") as mock_media:
            mock_media.return_value = Mock()
            result = upload_file(mock_service, str(test_file))

        assert result["id"] == "newfile123"
        assert result["name"] == "test.txt"

    def test_upload_file_with_parent(self, tmp_path):
        """Test uploading a file to a specific folder."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        mock_service = Mock()
        mock_service.files().create().execute.return_value = {
            "id": "newfile123",
            "name": "test.txt",
        }

        with patch.object(google_drive, "MediaFileUpload"):
            upload_file(mock_service, str(test_file), parent_folder_id="folder123")

        call_kwargs = mock_service.files().create.call_args[1]
        assert call_kwargs["body"]["parents"] == ["folder123"]

    def test_upload_file_not_found(self):
        """Test uploading non-existent file raises error."""
        mock_service = Mock()

        with pytest.raises(DriveAPIError, match="File not found"):
            upload_file(mock_service, "/nonexistent/file.txt")


# ============================================================================
# FOLDER OPERATIONS TESTS
# ============================================================================


class TestFolderOperations:
    """Tests for Drive folder operations."""

    def test_create_folder(self):
        """Test creating a folder."""
        mock_service = Mock()
        mock_service.files().create().execute.return_value = {
            "id": "folder123",
            "name": "New Folder",
            "mimeType": "application/vnd.google-apps.folder",
        }

        result = create_folder(mock_service, "New Folder")

        assert result["id"] == "folder123"
        assert result["name"] == "New Folder"
        call_kwargs = mock_service.files().create.call_args[1]
        assert call_kwargs["body"]["mimeType"] == "application/vnd.google-apps.folder"

    def test_create_folder_with_parent(self):
        """Test creating a folder inside another folder."""
        mock_service = Mock()
        mock_service.files().create().execute.return_value = {
            "id": "subfolder123",
            "name": "Subfolder",
        }

        create_folder(mock_service, "Subfolder", parent_folder_id="parent123")

        call_kwargs = mock_service.files().create.call_args[1]
        assert call_kwargs["body"]["parents"] == ["parent123"]

    def test_list_folder_contents(self):
        """Test listing folder contents."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {"id": "file1", "name": "Doc.pdf"},
                {"id": "file2", "name": "Image.png"},
            ]
        }

        files = list_folder_contents(mock_service, "folder123")

        assert len(files) == 2
        call_kwargs = mock_service.files().list.call_args[1]
        assert "'folder123' in parents" in call_kwargs["q"]
        assert "trashed = false" in call_kwargs["q"]


# ============================================================================
# SHARING OPERATIONS TESTS
# ============================================================================


class TestSharingOperations:
    """Tests for Drive sharing operations."""

    def test_share_file(self):
        """Test sharing a file."""
        mock_service = Mock()
        mock_service.permissions().create().execute.return_value = {
            "id": "perm123",
            "type": "user",
            "role": "reader",
            "emailAddress": "user@example.com",
        }

        result = share_file(mock_service, "file123", "user@example.com")

        assert result["emailAddress"] == "user@example.com"
        assert result["role"] == "reader"

    def test_share_file_as_writer(self):
        """Test sharing a file with write access."""
        mock_service = Mock()
        mock_service.permissions().create().execute.return_value = {
            "id": "perm123",
            "role": "writer",
        }

        share_file(mock_service, "file123", "user@example.com", role="writer")

        call_kwargs = mock_service.permissions().create.call_args[1]
        assert call_kwargs["body"]["role"] == "writer"

    def test_share_file_no_notification(self):
        """Test sharing without email notification."""
        mock_service = Mock()
        mock_service.permissions().create().execute.return_value = {"id": "perm123"}

        share_file(mock_service, "file123", "user@example.com", notify=False)

        call_kwargs = mock_service.permissions().create.call_args[1]
        assert call_kwargs["sendNotificationEmail"] is False

    def test_list_permissions(self):
        """Test listing permissions."""
        mock_service = Mock()
        mock_service.permissions().list().execute.return_value = {
            "permissions": [
                {"id": "perm1", "type": "user", "role": "owner"},
                {"id": "perm2", "type": "user", "role": "reader"},
            ]
        }

        permissions = list_permissions(mock_service, "file123")

        assert len(permissions) == 2
        assert permissions[0]["role"] == "owner"

    def test_delete_permission(self):
        """Test deleting a permission."""
        mock_service = Mock()

        delete_permission(mock_service, "file123", "perm123")

        mock_service.permissions().delete.assert_called_with(
            fileId="file123", permissionId="perm123"
        )


# ============================================================================
# FORMATTING TESTS
# ============================================================================


class TestFormatting:
    """Tests for output formatting functions."""

    def test_format_file_summary(self):
        """Test formatting file summary."""
        file = {
            "id": "file123",
            "name": "Report.pdf",
            "mimeType": "application/pdf",
            "modifiedTime": "2024-01-15T10:00:00Z",
            "size": "1048576",
            "webViewLink": "https://drive.google.com/file/d/file123",
        }

        formatted = format_file_summary(file)

        assert "file123" in formatted
        assert "Report.pdf" in formatted
        assert "application/pdf" in formatted
        assert "1.0 MB" in formatted

    def test_format_file_summary_folder(self):
        """Test formatting folder summary."""
        folder = {
            "id": "folder123",
            "name": "Documents",
            "mimeType": "application/vnd.google-apps.folder",
            "modifiedTime": "2024-01-15T10:00:00Z",
        }

        formatted = format_file_summary(folder)

        assert "[Folder]" in formatted
        assert "Documents" in formatted

    def test_format_file_summary_sizes(self):
        """Test formatting various file sizes."""
        # KB
        file_kb = {"id": "f1", "name": "a.txt", "size": "2048"}
        assert "2.0 KB" in format_file_summary(file_kb)

        # GB
        file_gb = {"id": "f2", "name": "b.zip", "size": "2147483648"}
        assert "2.0 GB" in format_file_summary(file_gb)

        # Bytes
        file_b = {"id": "f3", "name": "c.txt", "size": "500"}
        assert "500 B" in format_file_summary(file_b)

    def test_format_permission(self):
        """Test formatting permission."""
        permission = {
            "id": "perm123",
            "type": "user",
            "role": "reader",
            "emailAddress": "user@example.com",
            "displayName": "John Doe",
        }

        formatted = format_permission(permission)

        assert "John Doe" in formatted
        assert "reader" in formatted
        assert "perm123" in formatted


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


class TestHealthCheck:
    """Tests for Drive connectivity check."""

    @patch.object(google_drive, "build")
    @patch.object(google_drive, "get_google_credentials")
    def test_check_drive_connectivity_success(self, mock_get_creds, mock_build):
        """Test successful connectivity check."""
        # Mock credentials
        mock_creds = Mock()
        mock_creds.scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        mock_get_creds.return_value = mock_creds

        # Mock service
        mock_service = Mock()
        mock_service.about().get().execute.return_value = {
            "user": {
                "emailAddress": "user@example.com",
                "displayName": "Test User",
            },
            "storageQuota": {
                "usage": "1073741824",
                "limit": "16106127360",
            },
        }
        mock_build.return_value = mock_service

        result = check_drive_connectivity()

        assert result["authenticated"] is True
        assert result["storage"]["email"] == "user@example.com"
        assert result["error"] is None

    @patch.object(google_drive, "get_google_credentials")
    def test_check_drive_connectivity_failure(self, mock_get_creds):
        """Test failed connectivity check."""
        mock_get_creds.side_effect = Exception("Auth failed")

        result = check_drive_connectivity()

        assert result["authenticated"] is False
        assert result["storage"] is None
        assert "Auth failed" in result["error"]


# ============================================================================
# CLI COMMAND TESTS
# ============================================================================


class TestCLICommands:
    """Tests for CLI command handlers."""

    @patch.object(google_drive, "check_drive_connectivity")
    @patch("builtins.print")
    def test_cmd_check_success(self, _mock_print, mock_check):
        """Test check command with successful authentication."""
        mock_check.return_value = {
            "authenticated": True,
            "storage": {
                "email": "user@example.com",
                "display_name": "Test User",
                "usage": "1073741824",
                "limit": "16106127360",
            },
            "scopes": {
                "readonly": True,
                "file": True,
                "metadata": True,
            },
            "error": None,
        }

        args = Mock()
        exit_code = cmd_check(args)

        assert exit_code == 0

    @patch.object(google_drive, "check_drive_connectivity")
    @patch("builtins.print")
    def test_cmd_check_failure(self, _mock_print, mock_check):
        """Test check command with authentication failure."""
        mock_check.return_value = {
            "authenticated": False,
            "storage": None,
            "error": "No credentials",
        }

        args = Mock()
        exit_code = cmd_check(args)

        assert exit_code == 1

    @patch.object(google_drive, "save_config")
    @patch("builtins.print")
    def test_cmd_auth_setup(self, _mock_print, mock_save_config):
        """Test auth setup command."""
        args = Mock()
        args.client_id = "test-id"
        args.client_secret = "test-secret"

        exit_code = cmd_auth_setup(args)

        assert exit_code == 0
        mock_save_config.assert_called_once()

    @patch.object(google_drive, "save_config")
    @patch("builtins.print")
    def test_cmd_auth_setup_missing_args(self, _mock_print, _mock_save_config):
        """Test auth setup command with missing arguments."""
        args = Mock()
        args.client_id = None
        args.client_secret = "test-secret"

        exit_code = cmd_auth_setup(args)

        assert exit_code == 1

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_files")
    @patch("builtins.print")
    def test_cmd_files_list_text(self, _mock_print, mock_list_files, __mock_build_service):
        """Test files list command with text output."""
        mock_list_files.return_value = [
            {"id": "file1", "name": "Test.pdf", "mimeType": "application/pdf"}
        ]

        args = Mock()
        args.query = "name contains 'Test'"
        args.max_results = 10
        args.order_by = None
        args.json = False

        exit_code = cmd_files_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_files")
    @patch("builtins.print")
    def test_cmd_files_list_json(self, _mock_print, mock_list_files, __mock_build_service):
        """Test files list command with JSON output."""
        mock_list_files.return_value = [{"id": "file1"}]

        args = Mock()
        args.query = None
        args.max_results = 10
        args.order_by = None
        args.json = True

        exit_code = cmd_files_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_files")
    @patch("builtins.print")
    def test_cmd_files_list_empty(self, _mock_print, mock_list_files, __mock_build_service):
        """Test files list command with no files."""
        mock_list_files.return_value = []

        args = Mock()
        args.query = None
        args.max_results = 10
        args.order_by = None
        args.json = False

        exit_code = cmd_files_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "search_files")
    @patch("builtins.print")
    def test_cmd_files_search(self, _mock_print, mock_search_files, __mock_build_service):
        """Test files search command."""
        mock_search_files.return_value = [{"id": "file1", "name": "Report.pdf"}]

        args = Mock()
        args.name = "Report"
        args.mime_type = None
        args.folder = None
        args.json = False

        exit_code = cmd_files_search(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "get_file_metadata")
    @patch("builtins.print")
    def test_cmd_files_get(self, _mock_print, mock_get_file, __mock_build_service):
        """Test files get command."""
        mock_get_file.return_value = {"id": "file123", "name": "Test.pdf"}

        args = Mock()
        args.file_id = "file123"
        args.json = False

        exit_code = cmd_files_get(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "get_file_metadata")
    @patch.object(google_drive, "download_file")
    @patch("builtins.print")
    def test_cmd_files_download(
        self, _mock_print, mock_download, mock_get_file, __mock_build_service
    ):
        """Test files download command."""
        mock_get_file.return_value = {
            "id": "file123",
            "name": "Test.pdf",
            "mimeType": "application/pdf",
        }

        args = Mock()
        args.file_id = "file123"
        args.output = "/tmp/downloaded.pdf"

        exit_code = cmd_files_download(args)

        assert exit_code == 0
        mock_download.assert_called_once()

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "get_file_metadata")
    @patch("builtins.print")
    def test_cmd_files_download_google_doc(self, _mock_print, mock_get_file, __mock_build_service):
        """Test files download command fails for Google Docs."""
        mock_get_file.return_value = {
            "id": "file123",
            "name": "Test Doc",
            "mimeType": "application/vnd.google-apps.document",
        }

        args = Mock()
        args.file_id = "file123"
        args.output = "/tmp/downloaded.doc"

        exit_code = cmd_files_download(args)

        assert exit_code == 1

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "upload_file")
    @patch("builtins.print")
    def test_cmd_files_upload(self, _mock_print, mock_upload, __mock_build_service):
        """Test files upload command."""
        mock_upload.return_value = {
            "id": "newfile123",
            "name": "uploaded.pdf",
            "webViewLink": "https://drive.google.com/file/d/newfile123",
        }

        args = Mock()
        args.path = "/tmp/file.pdf"
        args.parent = None
        args.mime_type = None
        args.name = None
        args.json = False

        exit_code = cmd_files_upload(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "create_folder")
    @patch("builtins.print")
    def test_cmd_folders_create(self, _mock_print, mock_create_folder, __mock_build_service):
        """Test folders create command."""
        mock_create_folder.return_value = {
            "id": "folder123",
            "name": "New Folder",
            "webViewLink": "https://drive.google.com/drive/folders/folder123",
        }

        args = Mock()
        args.name = "New Folder"
        args.parent = None
        args.json = False

        exit_code = cmd_folders_create(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_folder_contents")
    @patch("builtins.print")
    def test_cmd_folders_list(self, _mock_print, mock_list_folder, __mock_build_service):
        """Test folders list command."""
        mock_list_folder.return_value = [{"id": "file1", "name": "Doc.pdf"}]

        args = Mock()
        args.folder_id = "folder123"
        args.max_results = 100
        args.json = False

        exit_code = cmd_folders_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "share_file")
    @patch("builtins.print")
    def test_cmd_share(self, _mock_print, mock_share, __mock_build_service):
        """Test share command."""
        mock_share.return_value = {
            "emailAddress": "user@example.com",
            "role": "reader",
        }

        args = Mock()
        args.file_id = "file123"
        args.email = "user@example.com"
        args.role = "reader"
        args.no_notify = False
        args.json = False

        exit_code = cmd_share(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_permissions")
    @patch("builtins.print")
    def test_cmd_permissions_list(self, _mock_print, mock_list_perms, __mock_build_service):
        """Test permissions list command."""
        mock_list_perms.return_value = [{"id": "perm1", "role": "owner"}]

        args = Mock()
        args.file_id = "file123"
        args.json = False

        exit_code = cmd_permissions_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "delete_permission")
    @patch("builtins.print")
    def test_cmd_permissions_delete(self, _mock_print, mock_delete_perm, __mock_build_service):
        """Test permissions delete command."""
        args = Mock()
        args.file_id = "file123"
        args.permission_id = "perm123"

        exit_code = cmd_permissions_delete(args)

        assert exit_code == 0
        mock_delete_perm.assert_called_once()


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

        # Test files list
        args = parser.parse_args(
            ["files", "list", "--query", "name contains 'test'", "--max-results", "20"]
        )
        assert args.command == "files"
        assert args.files_command == "list"
        assert args.query == "name contains 'test'"
        assert args.max_results == 20

        # Test files upload
        args = parser.parse_args(["files", "upload", "/path/to/file.pdf", "--parent", "folder123"])
        assert args.command == "files"
        assert args.files_command == "upload"
        assert args.path == "/path/to/file.pdf"
        assert args.parent == "folder123"

        # Test folders create
        args = parser.parse_args(["folders", "create", "New Folder"])
        assert args.command == "folders"
        assert args.folders_command == "create"
        assert args.name == "New Folder"

        # Test share
        args = parser.parse_args(
            ["share", "file123", "--email", "user@example.com", "--role", "writer"]
        )
        assert args.command == "share"
        assert args.file_id == "file123"
        assert args.email == "user@example.com"
        assert args.role == "writer"


# ============================================================================
# API ERROR HANDLING IN FUNCTIONS
# ============================================================================


class TestAPIErrorsInFunctions:
    """Test API error handling in functions."""

    def test_drive_api_error_attributes(self):
        """Test DriveAPIError attributes."""
        error = DriveAPIError("Test message", status_code=404, details={"foo": "bar"})
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

    @patch.object(google_drive, "get_google_credentials")
    @patch.object(google_drive, "build")
    def test_build_drive_service(self, mock_build, mock_get_creds):
        """Test building Drive service."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        service = build_drive_service()

        assert service == mock_service
        mock_get_creds.assert_called_once()
        mock_build.assert_called_once_with("drive", "v3", credentials=mock_creds)

    @patch.object(google_drive, "get_google_credentials")
    @patch.object(google_drive, "build")
    def test_build_drive_service_with_custom_scopes(self, mock_build, mock_get_creds):
        """Test building Drive service with custom scopes."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds

        mock_service = Mock()
        mock_build.return_value = mock_service

        custom_scopes = ["https://www.googleapis.com/auth/drive"]
        service = build_drive_service(custom_scopes)

        assert service == mock_service
        mock_get_creds.assert_called_once_with("google-drive", custom_scopes)


# ============================================================================
# MAIN FUNCTION TESTS
# ============================================================================


class TestMainFunction:
    """Tests for main() function."""

    @patch.object(google_drive, "cmd_check")
    @patch("sys.argv", ["google-drive.py", "check"])
    def test_main_check_command(self, mock_cmd_check):
        """Test main with check command."""
        mock_cmd_check.return_value = 0

        exit_code = google_drive.main()

        assert exit_code == 0
        mock_cmd_check.assert_called_once()

    @patch("sys.argv", ["google-drive.py"])
    def test_main_no_command(self):
        """Test main with no command shows help."""
        exit_code = google_drive.main()

        assert exit_code == 1

    @patch.object(google_drive, "cmd_check")
    @patch("sys.argv", ["google-drive.py", "check"])
    def test_main_keyboard_interrupt(self, mock_cmd_check):
        """Test main handles KeyboardInterrupt."""
        mock_cmd_check.side_effect = KeyboardInterrupt()

        exit_code = google_drive.main()

        assert exit_code == 130

    @patch.object(google_drive, "cmd_check")
    @patch("sys.argv", ["google-drive.py", "check"])
    def test_main_drive_api_error(self, mock_cmd_check):
        """Test main handles DriveAPIError."""
        mock_cmd_check.side_effect = DriveAPIError("API Error")

        exit_code = google_drive.main()

        assert exit_code == 1

    @patch.object(google_drive, "cmd_check")
    @patch("sys.argv", ["google-drive.py", "check"])
    def test_main_auth_error(self, mock_cmd_check):
        """Test main handles AuthenticationError."""
        mock_cmd_check.side_effect = AuthenticationError("Auth Error")

        exit_code = google_drive.main()

        assert exit_code == 1

    @patch.object(google_drive, "cmd_check")
    @patch("sys.argv", ["google-drive.py", "check"])
    def test_main_unexpected_error(self, mock_cmd_check):
        """Test main handles unexpected errors."""
        mock_cmd_check.side_effect = Exception("Unexpected")

        exit_code = google_drive.main()

        assert exit_code == 1


# ============================================================================
# ADDITIONAL CLI TESTS FOR COVERAGE
# ============================================================================


class TestAdditionalCLICommands:
    """Additional CLI command tests for coverage."""

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "search_files")
    @patch("builtins.print")
    def test_cmd_files_search_json(self, _mock_print, mock_search, __mock_build_service):
        """Test files search command with JSON output."""
        mock_search.return_value = []

        args = Mock()
        args.name = None
        args.mime_type = None
        args.folder = None
        args.json = True

        exit_code = cmd_files_search(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "get_file_metadata")
    @patch("builtins.print")
    def test_cmd_files_get_json(self, _mock_print, mock_get_file, __mock_build_service):
        """Test files get command with JSON output."""
        mock_get_file.return_value = {"id": "file123"}

        args = Mock()
        args.file_id = "file123"
        args.json = True

        exit_code = cmd_files_get(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "upload_file")
    @patch("builtins.print")
    def test_cmd_files_upload_json(self, _mock_print, mock_upload, __mock_build_service):
        """Test files upload command with JSON output."""
        mock_upload.return_value = {"id": "newfile123"}

        args = Mock()
        args.path = "/tmp/file.pdf"
        args.parent = None
        args.mime_type = None
        args.name = None
        args.json = True

        exit_code = cmd_files_upload(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "create_folder")
    @patch("builtins.print")
    def test_cmd_folders_create_json(self, _mock_print, mock_create, __mock_build_service):
        """Test folders create command with JSON output."""
        mock_create.return_value = {"id": "folder123"}

        args = Mock()
        args.name = "New Folder"
        args.parent = None
        args.json = True

        exit_code = cmd_folders_create(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_folder_contents")
    @patch("builtins.print")
    def test_cmd_folders_list_json(self, _mock_print, mock_list, __mock_build_service):
        """Test folders list command with JSON output."""
        mock_list.return_value = []

        args = Mock()
        args.folder_id = "folder123"
        args.max_results = 100
        args.json = True

        exit_code = cmd_folders_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_folder_contents")
    @patch("builtins.print")
    def test_cmd_folders_list_empty(self, _mock_print, mock_list, __mock_build_service):
        """Test folders list command with empty folder."""
        mock_list.return_value = []

        args = Mock()
        args.folder_id = "folder123"
        args.max_results = 100
        args.json = False

        exit_code = cmd_folders_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "share_file")
    @patch("builtins.print")
    def test_cmd_share_json(self, _mock_print, mock_share, __mock_build_service):
        """Test share command with JSON output."""
        mock_share.return_value = {"id": "perm123"}

        args = Mock()
        args.file_id = "file123"
        args.email = "user@example.com"
        args.role = "reader"
        args.no_notify = False
        args.json = True

        exit_code = cmd_share(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_permissions")
    @patch("builtins.print")
    def test_cmd_permissions_list_json(self, _mock_print, mock_list, __mock_build_service):
        """Test permissions list command with JSON output."""
        mock_list.return_value = []

        args = Mock()
        args.file_id = "file123"
        args.json = True

        exit_code = cmd_permissions_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "list_permissions")
    @patch("builtins.print")
    def test_cmd_permissions_list_empty(self, _mock_print, mock_list, __mock_build_service):
        """Test permissions list command with no permissions."""
        mock_list.return_value = []

        args = Mock()
        args.file_id = "file123"
        args.json = False

        exit_code = cmd_permissions_list(args)

        assert exit_code == 0

    @patch.object(google_drive, "build_drive_service")
    @patch.object(google_drive, "search_files")
    @patch("builtins.print")
    def test_cmd_files_search_empty(self, _mock_print, mock_search, __mock_build_service):
        """Test files search command with no results."""
        mock_search.return_value = []

        args = Mock()
        args.name = "nonexistent"
        args.mime_type = None
        args.folder = None
        args.json = False

        exit_code = cmd_files_search(args)

        assert exit_code == 0
