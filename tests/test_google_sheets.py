"""Tests for google-sheets.py skill."""

from __future__ import annotations

# Import from skills module - use importlib to handle hyphenated module name
import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Load the module with hyphenated name
spec = importlib.util.spec_from_file_location(
    "google_sheets",
    Path(__file__).parent.parent / "skills" / "google-sheets" / "scripts" / "google-sheets.py",
)
google_sheets = importlib.util.module_from_spec(spec)
sys.modules["google_sheets"] = google_sheets
spec.loader.exec_module(google_sheets)

# Now import from the loaded module
AuthenticationError = google_sheets.AuthenticationError
SheetsAPIError = google_sheets.SheetsAPIError
append_values = google_sheets.append_values
build_parser = google_sheets.build_parser
build_sheets_service = google_sheets.build_sheets_service
check_sheets_connectivity = google_sheets.check_sheets_connectivity
clear_values = google_sheets.clear_values
cmd_auth_setup = google_sheets.cmd_auth_setup
cmd_check = google_sheets.cmd_check
cmd_sheets_create = google_sheets.cmd_sheets_create
cmd_sheets_delete = google_sheets.cmd_sheets_delete
cmd_spreadsheets_create = google_sheets.cmd_spreadsheets_create
cmd_spreadsheets_get = google_sheets.cmd_spreadsheets_get
cmd_values_append = google_sheets.cmd_values_append
cmd_values_clear = google_sheets.cmd_values_clear
cmd_values_read = google_sheets.cmd_values_read
cmd_values_write = google_sheets.cmd_values_write
create_sheet = google_sheets.create_sheet
create_spreadsheet = google_sheets.create_spreadsheet
delete_credential = google_sheets.delete_credential
delete_sheet = google_sheets.delete_sheet
format_spreadsheet_summary = google_sheets.format_spreadsheet_summary
format_values_output = google_sheets.format_values_output
get_credential = google_sheets.get_credential
get_google_credentials = google_sheets.get_google_credentials
get_oauth_client_config = google_sheets.get_oauth_client_config
get_spreadsheet = google_sheets.get_spreadsheet
handle_api_error = google_sheets.handle_api_error
load_config = google_sheets.load_config
read_values = google_sheets.read_values
save_config = google_sheets.save_config
set_credential = google_sheets.set_credential
write_values = google_sheets.write_values

# ============================================================================
# KEYRING CREDENTIAL TESTS
# ============================================================================


class TestKeyringFunctions:
    """Tests for keyring credential functions."""

    @patch("google_sheets.keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch("google_sheets.keyring")
    def test_get_credential_not_found(self, mock_keyring):
        """Test getting non-existent credential."""
        mock_keyring.get_password.return_value = None
        result = get_credential("nonexistent")
        assert result is None

    @patch("google_sheets.keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch("google_sheets.keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")

    @patch("google_sheets.keyring")
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
        monkeypatch.setattr("google_sheets.CONFIG_DIR", tmp_path / "nonexistent")
        config = load_config("google-sheets")
        assert config is None

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        config_dir = tmp_path / "config"
        monkeypatch.setattr("google_sheets.CONFIG_DIR", config_dir)

        test_config = {
            "oauth_client": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
            }
        }

        save_config("google-sheets", test_config)
        loaded = load_config("google-sheets")

        assert loaded == test_config


# ============================================================================
# OAUTH CLIENT CONFIG TESTS
# ============================================================================


class TestOAuthClientConfig:
    """Tests for OAuth client configuration."""

    @patch("google_sheets.load_config")
    def test_get_oauth_client_config_from_service_file(self, mock_load_config):
        """Test getting OAuth config from service-specific file."""
        mock_load_config.return_value = {
            "oauth_client": {
                "client_id": "file-client-id",
                "client_secret": "file-client-secret",
            }
        }

        config = get_oauth_client_config("google-sheets")

        assert config["installed"]["client_id"] == "file-client-id"
        assert config["installed"]["client_secret"] == "file-client-secret"

    @patch("google_sheets.load_config")
    def test_get_oauth_client_config_from_service_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from service-specific environment."""
        mock_load_config.return_value = None
        monkeypatch.setenv("GOOGLE_SHEETS_CLIENT_ID", "env-client-id")
        monkeypatch.setenv("GOOGLE_SHEETS_CLIENT_SECRET", "env-client-secret")

        config = get_oauth_client_config("google-sheets")

        assert config["installed"]["client_id"] == "env-client-id"
        assert config["installed"]["client_secret"] == "env-client-secret"

    @patch("google_sheets.load_config")
    def test_get_oauth_client_config_from_shared_file(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared google.yaml file."""
        # No service-specific config or env vars
        monkeypatch.delenv("GOOGLE_SHEETS_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_SHEETS_CLIENT_SECRET", raising=False)

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

        config = get_oauth_client_config("google-sheets")

        assert config["installed"]["client_id"] == "shared-file-client-id"
        assert config["installed"]["client_secret"] == "shared-file-client-secret"

    @patch("google_sheets.load_config")
    def test_get_oauth_client_config_from_shared_env(self, mock_load_config, monkeypatch):
        """Test getting OAuth config from shared environment variables."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_SHEETS_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_SHEETS_CLIENT_SECRET", raising=False)
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "shared-env-client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shared-env-client-secret")

        config = get_oauth_client_config("google-sheets")

        assert config["installed"]["client_id"] == "shared-env-client-id"
        assert config["installed"]["client_secret"] == "shared-env-client-secret"

    @patch("google_sheets.load_config")
    def test_get_oauth_client_config_not_found(self, mock_load_config, monkeypatch):
        """Test error when OAuth config not found anywhere."""
        mock_load_config.return_value = None
        monkeypatch.delenv("GOOGLE_SHEETS_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_SHEETS_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        with pytest.raises(AuthenticationError, match="OAuth client credentials not found"):
            get_oauth_client_config("google-sheets")


# ============================================================================
# SPREADSHEET OPERATION TESTS
# ============================================================================


class TestSpreadsheetOperations:
    """Tests for spreadsheet operations."""

    def test_create_spreadsheet(self):
        """Test creating a spreadsheet."""
        mock_service = Mock()
        mock_service.spreadsheets().create().execute.return_value = {
            "spreadsheetId": "test-ss-id",
            "properties": {"title": "Test Spreadsheet"},
            "sheets": [{"properties": {"title": "Sheet1", "sheetId": 0}}],
        }

        result = create_spreadsheet(mock_service, "Test Spreadsheet")

        assert result["spreadsheetId"] == "test-ss-id"
        assert result["properties"]["title"] == "Test Spreadsheet"

    def test_create_spreadsheet_with_custom_sheets(self):
        """Test creating spreadsheet with custom sheet names."""
        mock_service = Mock()
        mock_service.spreadsheets().create().execute.return_value = {
            "spreadsheetId": "test-ss-id",
            "properties": {"title": "Test Spreadsheet"},
            "sheets": [
                {"properties": {"title": "Summary", "sheetId": 0}},
                {"properties": {"title": "Data", "sheetId": 1}},
            ],
        }

        result = create_spreadsheet(mock_service, "Test Spreadsheet", ["Summary", "Data"])

        assert result["spreadsheetId"] == "test-ss-id"
        # Verify custom sheets were requested
        call_args = mock_service.spreadsheets().create.call_args
        assert call_args[1]["body"]["sheets"][0]["properties"]["title"] == "Summary"
        assert call_args[1]["body"]["sheets"][1]["properties"]["title"] == "Data"

    def test_get_spreadsheet(self):
        """Test getting a spreadsheet."""
        mock_service = Mock()
        mock_service.spreadsheets().get().execute.return_value = {
            "spreadsheetId": "test-ss-id",
            "properties": {"title": "Test Spreadsheet"},
            "sheets": [{"properties": {"title": "Sheet1", "sheetId": 0}}],
        }

        result = get_spreadsheet(mock_service, "test-ss-id")

        assert result["spreadsheetId"] == "test-ss-id"

    def test_read_values(self):
        """Test reading cell values."""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            "range": "Sheet1!A1:B2",
            "values": [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]],
        }

        result = read_values(mock_service, "test-ss-id", "Sheet1!A1:B2")

        assert result["values"] == [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]

    def test_read_values_with_format_option(self):
        """Test reading values with format option."""
        mock_service = Mock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            "range": "Sheet1!D2:D5",
            "values": [["=A2+B2"], ["=A3+B3"], ["=A4+B4"]],
        }

        result = read_values(mock_service, "test-ss-id", "Sheet1!D2:D5", "FORMULA")

        assert result["values"] == [["=A2+B2"], ["=A3+B3"], ["=A4+B4"]]
        call_args = mock_service.spreadsheets().values().get.call_args
        assert call_args[1]["valueRenderOption"] == "FORMULA"

    def test_write_values(self):
        """Test writing values to cells."""
        mock_service = Mock()
        mock_service.spreadsheets().values().update().execute.return_value = {
            "updatedCells": 6,
            "updatedRange": "Sheet1!A1:C2",
        }

        values = [["Product", "Price", "Qty"], ["Widget", 9.99, 100]]
        result = write_values(mock_service, "test-ss-id", "Sheet1!A1", values)

        assert result["updatedCells"] == 6
        assert result["updatedRange"] == "Sheet1!A1:C2"
        call_args = mock_service.spreadsheets().values().update.call_args
        assert call_args[1]["body"]["values"] == values
        assert call_args[1]["valueInputOption"] == "USER_ENTERED"

    def test_append_values(self):
        """Test appending rows to sheet."""
        mock_service = Mock()
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {
                "updatedCells": 3,
                "updatedRange": "Sheet1!A4:C4",
            }
        }

        values = [["Charlie", 35, "Chicago"]]
        result = append_values(mock_service, "test-ss-id", "Sheet1", values)

        assert result["updates"]["updatedCells"] == 3
        call_args = mock_service.spreadsheets().values().append.call_args
        assert call_args[1]["body"]["values"] == values
        assert call_args[1]["valueInputOption"] == "USER_ENTERED"

    def test_clear_values(self):
        """Test clearing cell values."""
        mock_service = Mock()
        mock_service.spreadsheets().values().clear().execute.return_value = {
            "clearedRange": "Sheet1!A1:Z100"
        }

        result = clear_values(mock_service, "test-ss-id", "Sheet1!A1:Z100")

        assert result["clearedRange"] == "Sheet1!A1:Z100"

    def test_create_sheet(self):
        """Test adding a new sheet."""
        mock_service = Mock()
        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            "replies": [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Q2 Data",
                            "sheetId": 123456789,
                        }
                    }
                }
            ]
        }

        result = create_sheet(mock_service, "test-ss-id", "Q2 Data")

        assert result["replies"][0]["addSheet"]["properties"]["title"] == "Q2 Data"
        call_args = mock_service.spreadsheets().batchUpdate.call_args
        assert call_args[1]["body"]["requests"][0]["addSheet"]["properties"]["title"] == "Q2 Data"

    def test_delete_sheet(self):
        """Test deleting a sheet."""
        mock_service = Mock()
        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = delete_sheet(mock_service, "test-ss-id", 123456789)

        assert result == {}
        call_args = mock_service.spreadsheets().batchUpdate.call_args
        assert call_args[1]["body"]["requests"][0]["deleteSheet"]["sheetId"] == 123456789


# ============================================================================
# OUTPUT FORMATTING TESTS
# ============================================================================


class TestOutputFormatting:
    """Tests for output formatting functions."""

    def test_format_spreadsheet_summary(self):
        """Test formatting spreadsheet summary."""
        spreadsheet = {
            "spreadsheetId": "abc123",
            "properties": {"title": "Test Spreadsheet"},
            "sheets": [
                {"properties": {"title": "Sheet1"}},
                {"properties": {"title": "Summary"}},
            ],
        }

        result = format_spreadsheet_summary(spreadsheet)

        assert "Test Spreadsheet" in result
        assert "abc123" in result
        assert "2" in result  # sheet count
        assert "Sheet1" in result
        assert "Summary" in result

    def test_format_values_output(self):
        """Test formatting values for display."""
        values = [["Name", "Age", "City"], ["Alice", "30", "NYC"], ["Bob", "25", "LA"]]

        result = format_values_output(values)

        assert "Name" in result
        assert "Alice" in result
        assert "NYC" in result
        assert "|" in result  # Column separator

    def test_format_values_output_empty(self):
        """Test formatting empty values."""
        result = format_values_output([])
        assert "(No data)" in result

    def test_format_values_output_truncation(self):
        """Test formatting with long cell values."""
        values = [["A" * 50, "B" * 50]]

        result = format_values_output(values)

        # Should truncate long values
        assert "..." in result


# ============================================================================
# CLI COMMAND HANDLER TESTS
# ============================================================================


class TestCLICommands:
    """Tests for CLI command handlers."""

    @patch("google_sheets.check_sheets_connectivity")
    def test_cmd_check_success(self, mock_check, capsys):
        """Test check command when authenticated."""
        mock_check.return_value = {
            "authenticated": True,
            "test_spreadsheet_id": "test-ss-123",
            "scopes": {"readonly": True, "write": True, "all_scopes": []},
        }

        args = Mock()
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Successfully authenticated" in captured.out

    @patch("google_sheets.check_sheets_connectivity")
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

    @patch("google_sheets.check_sheets_connectivity")
    def test_cmd_check_warning_no_write_scope(self, mock_check, capsys):
        """Test check command warns when write scope not granted."""
        mock_check.return_value = {
            "authenticated": True,
            "test_spreadsheet_id": "test-ss-123",
            "scopes": {"readonly": True, "write": False, "all_scopes": []},
        }

        args = Mock()
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Write scope not granted" in captured.out

    @patch("google_sheets.save_config")
    @patch("google_sheets.load_config")
    def test_cmd_auth_setup(self, mock_load, mock_save, capsys):
        """Test auth setup command."""
        mock_load.return_value = None
        args = Mock(client_id="test-id", client_secret="test-secret")

        result = cmd_auth_setup(args)

        assert result == 0
        mock_save.assert_called_once()
        captured = capsys.readouterr()
        assert "OAuth client credentials saved" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.create_spreadsheet")
    def test_cmd_spreadsheets_create(self, mock_create, _mock_build_service, capsys):
        """Test spreadsheets create command."""
        mock_create.return_value = {
            "spreadsheetId": "new-ss-123",
            "properties": {"title": "New Spreadsheet"},
            "sheets": [{"properties": {"title": "Sheet1"}}],
        }

        args = Mock(title="New Spreadsheet", sheets=None, json=False)
        result = cmd_spreadsheets_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Spreadsheet created successfully" in captured.out
        assert "new-ss-123" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.get_spreadsheet")
    def test_cmd_spreadsheets_get(self, mock_get, _mock_build_service, capsys):
        """Test spreadsheets get command."""
        mock_get.return_value = {
            "spreadsheetId": "ss-123",
            "properties": {"title": "Test Spreadsheet"},
            "sheets": [{"properties": {"title": "Sheet1"}}],
        }

        args = Mock(spreadsheet_id="ss-123", json=False)
        result = cmd_spreadsheets_get(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Test Spreadsheet" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.read_values")
    def test_cmd_values_read(self, mock_read, _mock_build_service, capsys):
        """Test values read command."""
        mock_read.return_value = {"values": [["Name", "Age"], ["Alice", "30"]]}

        args = Mock(
            spreadsheet_id="ss-123", range="Sheet1!A1:B2", format="FORMATTED_VALUE", json=False
        )
        result = cmd_values_read(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Name" in captured.out
        assert "Alice" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.write_values")
    def test_cmd_values_write(self, mock_write, _mock_build_service, capsys):
        """Test values write command."""
        mock_write.return_value = {
            "updatedCells": 6,
            "updatedRange": "Sheet1!A1:C2",
        }

        args = Mock(
            spreadsheet_id="ss-123",
            range="Sheet1!A1",
            values='[["Product","Price","Qty"],["Widget",9.99,100]]',
            json=False,
        )
        result = cmd_values_write(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Values written successfully" in captured.out
        assert "6" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.append_values")
    def test_cmd_values_append(self, mock_append, _mock_build_service, capsys):
        """Test values append command."""
        mock_append.return_value = {
            "updates": {
                "updatedCells": 3,
                "updatedRange": "Sheet1!A4:C4",
            }
        }

        args = Mock(
            spreadsheet_id="ss-123", range="Sheet1", values='[["Charlie",35,"Chicago"]]', json=False
        )
        result = cmd_values_append(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Values appended successfully" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.clear_values")
    def test_cmd_values_clear(self, mock_clear, _mock_build_service, capsys):
        """Test values clear command."""
        mock_clear.return_value = {"clearedRange": "Sheet1!A1:Z100"}

        args = Mock(spreadsheet_id="ss-123", range="Sheet1!A1:Z100", json=False)
        result = cmd_values_clear(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Values cleared successfully" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.create_sheet")
    def test_cmd_sheets_create(self, mock_create, _mock_build_service, capsys):
        """Test sheets create command."""
        mock_create.return_value = {
            "replies": [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Q2 Data",
                            "sheetId": 123456789,
                        }
                    }
                }
            ]
        }

        args = Mock(spreadsheet_id="ss-123", title="Q2 Data", json=False)
        result = cmd_sheets_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Sheet created successfully" in captured.out
        assert "Q2 Data" in captured.out

    @patch("google_sheets.build_sheets_service")
    @patch("google_sheets.delete_sheet")
    def test_cmd_sheets_delete(self, mock_delete, _mock_build_service, capsys):
        """Test sheets delete command."""
        mock_delete.return_value = {}

        args = Mock(spreadsheet_id="ss-123", sheet_id=123456789, json=False)
        result = cmd_sheets_delete(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Sheet deleted successfully" in captured.out

    def test_cmd_values_write_invalid_json(self, capsys):
        """Test values write with invalid JSON."""
        args = Mock(spreadsheet_id="ss-123", range="Sheet1!A1", values="invalid json", json=False)

        with patch("google_sheets.build_sheets_service"):
            result = cmd_values_write(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err


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

    def test_parser_spreadsheets_create(self):
        """Test parser for spreadsheets create command."""
        parser = build_parser()
        args = parser.parse_args(["spreadsheets", "create", "--title", "Test"])
        assert args.command == "spreadsheets"
        assert args.spreadsheets_command == "create"
        assert args.title == "Test"

    def test_parser_spreadsheets_create_with_sheets(self):
        """Test parser for spreadsheets create with custom sheets."""
        parser = build_parser()
        args = parser.parse_args(["spreadsheets", "create", "--title", "Test", "--sheets", "A,B,C"])
        assert args.sheets == "A,B,C"

    def test_parser_spreadsheets_get(self):
        """Test parser for spreadsheets get command."""
        parser = build_parser()
        args = parser.parse_args(["spreadsheets", "get", "ss-123"])
        assert args.command == "spreadsheets"
        assert args.spreadsheets_command == "get"
        assert args.spreadsheet_id == "ss-123"

    def test_parser_values_read(self):
        """Test parser for values read command."""
        parser = build_parser()
        args = parser.parse_args(["values", "read", "ss-123", "--range", "Sheet1!A1:D5"])
        assert args.command == "values"
        assert args.values_command == "read"
        assert args.spreadsheet_id == "ss-123"
        assert args.range == "Sheet1!A1:D5"

    def test_parser_values_read_with_format(self):
        """Test parser for values read with format option."""
        parser = build_parser()
        args = parser.parse_args(
            ["values", "read", "ss-123", "--range", "Sheet1!A1", "--format", "FORMULA"]
        )
        assert args.format == "FORMULA"

    def test_parser_values_write(self):
        """Test parser for values write command."""
        parser = build_parser()
        args = parser.parse_args(
            ["values", "write", "ss-123", "--range", "Sheet1!A1", "--values", "[[1,2,3]]"]
        )
        assert args.command == "values"
        assert args.values_command == "write"
        assert args.values == "[[1,2,3]]"

    def test_parser_values_append(self):
        """Test parser for values append command."""
        parser = build_parser()
        args = parser.parse_args(
            ["values", "append", "ss-123", "--range", "Sheet1", "--values", "[[4,5,6]]"]
        )
        assert args.command == "values"
        assert args.values_command == "append"

    def test_parser_values_clear(self):
        """Test parser for values clear command."""
        parser = build_parser()
        args = parser.parse_args(["values", "clear", "ss-123", "--range", "Sheet1!A1:Z100"])
        assert args.command == "values"
        assert args.values_command == "clear"

    def test_parser_sheets_create(self):
        """Test parser for sheets create command."""
        parser = build_parser()
        args = parser.parse_args(["sheets", "create", "ss-123", "--title", "New Sheet"])
        assert args.command == "sheets"
        assert args.sheets_command == "create"
        assert args.title == "New Sheet"

    def test_parser_sheets_delete(self):
        """Test parser for sheets delete command."""
        parser = build_parser()
        args = parser.parse_args(["sheets", "delete", "ss-123", "--sheet-id", "12345"])
        assert args.command == "sheets"
        assert args.sheets_command == "delete"
        assert args.sheet_id == 12345

    def test_parser_json_flag(self):
        """Test parser handles --json flag."""
        parser = build_parser()
        args = parser.parse_args(["spreadsheets", "get", "ss-123", "--json"])
        assert args.json is True
