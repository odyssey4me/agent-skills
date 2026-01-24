"""Tests for google-calendar.py skill."""

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
    "google_calendar",
    Path(__file__).parent.parent / "skills" / "google-calendar" / "scripts" / "google-calendar.py",
)
google_calendar = importlib.util.module_from_spec(spec)
sys.modules["google_calendar"] = google_calendar
spec.loader.exec_module(google_calendar)

# Now import from the loaded module
AuthenticationError = google_calendar.AuthenticationError
CalendarAPIError = google_calendar.CalendarAPIError
build_calendar_service = google_calendar.build_calendar_service
build_parser = google_calendar.build_parser
check_calendar_connectivity = google_calendar.check_calendar_connectivity
check_freebusy = google_calendar.check_freebusy
cmd_auth_setup = google_calendar.cmd_auth_setup
cmd_calendars_get = google_calendar.cmd_calendars_get
cmd_calendars_list = google_calendar.cmd_calendars_list
cmd_check = google_calendar.cmd_check
cmd_events_create = google_calendar.cmd_events_create
cmd_events_delete = google_calendar.cmd_events_delete
cmd_events_get = google_calendar.cmd_events_get
cmd_events_list = google_calendar.cmd_events_list
cmd_events_update = google_calendar.cmd_events_update
cmd_freebusy = google_calendar.cmd_freebusy
create_event = google_calendar.create_event
delete_credential = google_calendar.delete_credential
delete_event = google_calendar.delete_event
format_calendar = google_calendar.format_calendar
format_event = google_calendar.format_event
get_calendar = google_calendar.get_calendar
get_credential = google_calendar.get_credential
get_event = google_calendar.get_event
get_google_credentials = google_calendar.get_google_credentials
get_oauth_client_config = google_calendar.get_oauth_client_config
handle_api_error = google_calendar.handle_api_error
list_calendars = google_calendar.list_calendars
list_events = google_calendar.list_events
load_config = google_calendar.load_config
save_config = google_calendar.save_config
set_credential = google_calendar.set_credential
update_event = google_calendar.update_event


# ============================================================================
# KEYRING CREDENTIAL TESTS
# ============================================================================


class TestKeyringFunctions:
    """Tests for keyring credential functions."""

    @patch.object(google_calendar, "keyring")
    def test_get_credential(self, mock_keyring):
        """Test getting credential from keyring."""
        mock_keyring.get_password.return_value = "secret"
        result = get_credential("test-key")
        assert result == "secret"
        mock_keyring.get_password.assert_called_once_with("agent-skills", "test-key")

    @patch.object(google_calendar, "keyring")
    def test_get_credential_not_found(self, mock_keyring):
        """Test getting non-existent credential."""
        mock_keyring.get_password.return_value = None
        result = get_credential("nonexistent")
        assert result is None

    @patch.object(google_calendar, "keyring")
    def test_set_credential(self, mock_keyring):
        """Test setting credential in keyring."""
        set_credential("test-key", "secret")
        mock_keyring.set_password.assert_called_once_with("agent-skills", "test-key", "secret")

    @patch.object(google_calendar, "keyring")
    def test_delete_credential(self, mock_keyring):
        """Test deleting credential from keyring."""
        delete_credential("test-key")
        mock_keyring.delete_password.assert_called_once_with("agent-skills", "test-key")

    @patch.object(google_calendar, "keyring")
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

    def test_load_config_not_exists(self, tmp_path, monkeypatch):
        """Test loading non-existent config."""
        monkeypatch.setattr(google_calendar, "CONFIG_DIR", tmp_path)
        result = load_config("google-calendar")
        assert result is None

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Test saving and loading config."""
        monkeypatch.setattr(google_calendar, "CONFIG_DIR", tmp_path)
        config = {"oauth_client": {"client_id": "test-id", "client_secret": "test-secret"}}
        save_config("google-calendar", config)

        loaded = load_config("google-calendar")
        assert loaded == config


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================


class TestAuthentication:
    """Tests for authentication functions."""

    def test_get_oauth_client_config_from_config_file(self, tmp_path, monkeypatch):
        """Test getting OAuth config from config file."""
        monkeypatch.setattr(google_calendar, "CONFIG_DIR", tmp_path)
        config = {"oauth_client": {"client_id": "test-id", "client_secret": "test-secret"}}
        save_config("google-calendar", config)

        result = get_oauth_client_config("google-calendar")
        assert "installed" in result
        assert result["installed"]["client_id"] == "test-id"
        assert result["installed"]["client_secret"] == "test-secret"

    def test_get_oauth_client_config_from_env(self, monkeypatch):
        """Test getting OAuth config from environment variables."""
        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_ID", "env-id")
        monkeypatch.setenv("GOOGLE_CALENDAR_CLIENT_SECRET", "env-secret")
        # Ensure no config file
        monkeypatch.setattr(google_calendar, "load_config", lambda _: None)

        result = get_oauth_client_config("google-calendar")
        assert result["installed"]["client_id"] == "env-id"
        assert result["installed"]["client_secret"] == "env-secret"

    def test_get_oauth_client_config_from_shared_config(self, tmp_path, monkeypatch):
        """Test getting OAuth config from shared Google config."""
        monkeypatch.setattr(google_calendar, "CONFIG_DIR", tmp_path)
        config = {"oauth_client": {"client_id": "shared-id", "client_secret": "shared-secret"}}
        save_config("google", config)

        result = get_oauth_client_config("google-calendar")
        assert result["installed"]["client_id"] == "shared-id"
        assert result["installed"]["client_secret"] == "shared-secret"

    def test_get_oauth_client_config_not_found(self, monkeypatch):
        """Test error when OAuth config not found."""
        monkeypatch.setattr(google_calendar, "load_config", lambda _: None)
        with pytest.raises(AuthenticationError) as exc_info:
            get_oauth_client_config("google-calendar")
        assert "OAuth client credentials not found" in str(exc_info.value)

    @patch.object(google_calendar, "get_credential")
    @patch.object(google_calendar, "set_credential")
    @patch.object(google_calendar, "get_oauth_client_config")
    def test_get_google_credentials_from_keyring(
        self, _mock_get_config, _mock_set_cred, mock_get_cred
    ):
        """Test getting credentials from keyring."""
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = "refresh-token"

        token_json = json.dumps(
            {
                "token": "access-token",
                "refresh_token": "refresh-token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "test-id",
                "client_secret": "test-secret",
            }
        )
        mock_get_cred.return_value = token_json

        with patch("google_calendar.Credentials") as mock_credentials_class:
            mock_credentials_class.from_authorized_user_info.return_value = mock_creds
            result = get_google_credentials("google-calendar", ["calendar.readonly"])
            assert result == mock_creds


# ============================================================================
# CALENDAR OPERATIONS TESTS
# ============================================================================


class TestCalendarOperations:
    """Tests for calendar operations."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Calendar service."""
        service = Mock()
        return service

    def test_list_calendars(self, mock_service):
        """Test listing calendars."""
        mock_service.calendarList().list().execute.return_value = {
            "items": [
                {"id": "primary", "summary": "My Calendar", "primary": True},
                {"id": "cal2", "summary": "Work Calendar"},
            ]
        }

        calendars = list_calendars(mock_service)
        assert len(calendars) == 2
        assert calendars[0]["id"] == "primary"
        assert calendars[1]["summary"] == "Work Calendar"

    def test_get_calendar(self, mock_service):
        """Test getting calendar details."""
        mock_service.calendars().get().execute.return_value = {
            "id": "primary",
            "summary": "My Calendar",
            "timeZone": "America/New_York",
        }

        calendar = get_calendar(mock_service, "primary")
        assert calendar["id"] == "primary"
        assert calendar["timeZone"] == "America/New_York"


# ============================================================================
# EVENT OPERATIONS TESTS
# ============================================================================


class TestEventOperations:
    """Tests for event operations."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Calendar service."""
        service = Mock()
        return service

    def test_list_events(self, mock_service):
        """Test listing events."""
        mock_service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Meeting",
                    "start": {"dateTime": "2026-01-24T10:00:00Z"},
                    "end": {"dateTime": "2026-01-24T11:00:00Z"},
                },
                {
                    "id": "event2",
                    "summary": "Conference",
                    "start": {"date": "2026-01-25"},
                    "end": {"date": "2026-01-26"},
                },
            ]
        }

        events = list_events(mock_service, calendar_id="primary", max_results=10)
        assert len(events) == 2
        assert events[0]["summary"] == "Meeting"
        assert events[1]["summary"] == "Conference"

    def test_get_event(self, mock_service):
        """Test getting event details."""
        mock_service.events().get().execute.return_value = {
            "id": "event1",
            "summary": "Team Meeting",
            "start": {"dateTime": "2026-01-24T10:00:00Z"},
            "end": {"dateTime": "2026-01-24T11:00:00Z"},
        }

        event = get_event(mock_service, "event1", "primary")
        assert event["id"] == "event1"
        assert event["summary"] == "Team Meeting"

    def test_create_event_with_datetime(self, mock_service):
        """Test creating event with datetime."""
        mock_service.events().insert().execute.return_value = {
            "id": "new-event",
            "summary": "New Meeting",
        }

        event = create_event(
            mock_service,
            summary="New Meeting",
            start="2026-01-24T10:00:00Z",
            end="2026-01-24T11:00:00Z",
            description="Test event",
            location="Room A",
        )

        assert event["id"] == "new-event"
        # Verify the call was made with correct parameters
        call_args = mock_service.events().insert.call_args
        body = call_args[1]["body"]
        assert body["summary"] == "New Meeting"
        assert body["start"]["dateTime"] == "2026-01-24T10:00:00Z"
        assert body["description"] == "Test event"

    def test_create_event_all_day(self, mock_service):
        """Test creating all-day event."""
        mock_service.events().insert().execute.return_value = {
            "id": "all-day-event",
            "summary": "Holiday",
        }

        event = create_event(
            mock_service,
            summary="Holiday",
            start="2026-12-25",
            end="2026-12-26",
            timezone="America/New_York",
        )

        assert event["id"] == "all-day-event"
        # Verify date format was used
        call_args = mock_service.events().insert.call_args
        body = call_args[1]["body"]
        assert "date" in body["start"]
        assert body["start"]["date"] == "2026-12-25"

    def test_create_event_with_attendees(self, mock_service):
        """Test creating event with attendees."""
        mock_service.events().insert().execute.return_value = {"id": "meeting"}

        create_event(
            mock_service,
            summary="Team Meeting",
            start="2026-01-24T10:00:00Z",
            end="2026-01-24T11:00:00Z",
            attendees=["alice@example.com", "bob@example.com"],
        )

        call_args = mock_service.events().insert.call_args
        body = call_args[1]["body"]
        assert len(body["attendees"]) == 2
        assert body["attendees"][0]["email"] == "alice@example.com"

    def test_update_event(self, mock_service):
        """Test updating event."""
        # Mock get call to return existing event
        mock_service.events().get().execute.return_value = {
            "id": "event1",
            "summary": "Old Title",
            "start": {"dateTime": "2026-01-24T10:00:00Z"},
            "end": {"dateTime": "2026-01-24T11:00:00Z"},
        }
        # Mock update call
        mock_service.events().update().execute.return_value = {
            "id": "event1",
            "summary": "New Title",
        }

        event = update_event(mock_service, "event1", summary="New Title")

        assert event["summary"] == "New Title"
        # Verify update was called
        assert mock_service.events().update.called

    def test_delete_event(self, mock_service):
        """Test deleting event."""
        mock_service.events().delete().execute.return_value = None

        # Should not raise
        delete_event(mock_service, "event1", "primary")

        # Verify delete was called with correct parameters
        mock_service.events().delete.assert_called_with(calendarId="primary", eventId="event1")


# ============================================================================
# FREEBUSY TESTS
# ============================================================================


class TestFreebusy:
    """Tests for freebusy operations."""

    @pytest.fixture
    def mock_service(self):
        """Create mock Calendar service."""
        service = Mock()
        return service

    def test_check_freebusy(self, mock_service):
        """Test checking freebusy information."""
        mock_service.freebusy().query().execute.return_value = {
            "calendars": {
                "primary": {
                    "busy": [
                        {
                            "start": "2026-01-24T10:00:00Z",
                            "end": "2026-01-24T11:00:00Z",
                        }
                    ]
                }
            }
        }

        result = check_freebusy(
            mock_service,
            time_min="2026-01-24T00:00:00Z",
            time_max="2026-01-24T23:59:59Z",
            calendar_ids=["primary"],
        )

        assert "calendars" in result
        assert "primary" in result["calendars"]
        assert len(result["calendars"]["primary"]["busy"]) == 1


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_handle_api_error_403_insufficient_scope(self):
        """Test handling 403 insufficient scope error."""
        from googleapiclient.errors import HttpError

        mock_response = Mock()
        mock_response.status = 403
        mock_response.reason = "Forbidden"

        error_content = {
            "error": {
                "code": 403,
                "message": "Request had insufficient authentication scopes.",
            }
        }

        mock_error = HttpError(
            resp=mock_response, content=json.dumps(error_content).encode("utf-8")
        )

        with pytest.raises(CalendarAPIError) as exc_info:
            handle_api_error(mock_error)

        assert "insufficient" in str(exc_info.value).lower()
        assert "re-authenticate" in str(exc_info.value).lower()

    def test_handle_api_error_404(self):
        """Test handling 404 not found error."""
        from googleapiclient.errors import HttpError

        mock_response = Mock()
        mock_response.status = 404
        mock_response.reason = "Not Found"

        error_content = {"error": {"code": 404, "message": "Event not found"}}

        mock_error = HttpError(
            resp=mock_response, content=json.dumps(error_content).encode("utf-8")
        )

        with pytest.raises(CalendarAPIError) as exc_info:
            handle_api_error(mock_error)

        assert exc_info.value.status_code == 404
        assert "Event not found" in str(exc_info.value)


# ============================================================================
# OUTPUT FORMATTING TESTS
# ============================================================================


class TestOutputFormatting:
    """Tests for output formatting functions."""

    def test_format_calendar(self):
        """Test calendar formatting."""
        calendar = {
            "id": "primary",
            "summary": "My Calendar",
            "description": "Personal calendar",
            "timeZone": "America/New_York",
            "primary": True,
        }

        formatted = format_calendar(calendar)
        assert "My Calendar" in formatted
        assert "[PRIMARY]" in formatted
        assert "America/New_York" in formatted

    def test_format_event(self):
        """Test event formatting."""
        event = {
            "id": "event1",
            "summary": "Team Meeting",
            "start": {"dateTime": "2026-01-24T10:00:00Z"},
            "end": {"dateTime": "2026-01-24T11:00:00Z"},
            "location": "Room A",
            "description": "Weekly team sync",
            "attendees": [{"email": "alice@example.com"}, {"email": "bob@example.com"}],
        }

        formatted = format_event(event)
        assert "Team Meeting" in formatted
        assert "event1" in formatted
        assert "Room A" in formatted
        assert "alice@example.com" in formatted


# ============================================================================
# CLI COMMAND TESTS
# ============================================================================


class TestCLICommands:
    """Tests for CLI command handlers."""

    @patch.object(google_calendar, "check_calendar_connectivity")
    def test_cmd_check_success(self, mock_check, capsys):
        """Test check command with successful connection."""
        mock_check.return_value = {
            "authenticated": True,
            "primary_calendar": {
                "summary": "My Calendar",
                "id": "primary",
                "timezone": "America/New_York",
            },
            "scopes": {
                "readonly": True,
                "events": True,
            },
        }

        result = cmd_check(Mock())
        assert result == 0

        captured = capsys.readouterr()
        assert "Successfully authenticated" in captured.out

    @patch.object(google_calendar, "check_calendar_connectivity")
    def test_cmd_check_failure(self, mock_check, capsys):
        """Test check command with failed connection."""
        mock_check.return_value = {
            "authenticated": False,
            "error": "Authentication failed",
        }

        result = cmd_check(Mock())
        assert result == 1

        captured = capsys.readouterr()
        assert "Authentication failed" in captured.out

    @patch.object(google_calendar, "save_config")
    def test_cmd_auth_setup(self, mock_save, capsys):
        """Test auth setup command."""
        args = Mock()
        args.client_id = "test-client-id"
        args.client_secret = "test-client-secret"

        result = cmd_auth_setup(args)
        assert result == 0
        assert mock_save.called

        captured = capsys.readouterr()
        assert "saved to config file" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "list_calendars")
    def test_cmd_calendars_list(self, mock_list, _mock_service, capsys):
        """Test calendars list command."""
        mock_list.return_value = [
            {"id": "primary", "summary": "My Calendar"},
            {"id": "cal2", "summary": "Work Calendar"},
        ]

        args = Mock()
        args.json = False

        result = cmd_calendars_list(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "My Calendar" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "list_events")
    def test_cmd_events_list_json(self, mock_list, _mock_service, capsys):
        """Test events list command with JSON output."""
        mock_list.return_value = [
            {"id": "event1", "summary": "Meeting"},
        ]

        args = Mock()
        args.json = True
        args.calendar = "primary"
        args.time_min = None
        args.time_max = None
        args.max_results = 10
        args.query = None

        result = cmd_events_list(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert len(output) == 1
        assert output[0]["id"] == "event1"

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "get_calendar")
    def test_cmd_calendars_get(self, mock_get, _mock_service, capsys):
        """Test calendars get command."""
        mock_get.return_value = {
            "id": "primary",
            "summary": "My Calendar",
            "timeZone": "America/New_York",
        }

        args = Mock()
        args.calendar_id = "primary"
        args.json = False

        result = cmd_calendars_get(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "My Calendar" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "get_event")
    def test_cmd_events_get(self, mock_get, _mock_service, capsys):
        """Test events get command."""
        mock_get.return_value = {
            "id": "event1",
            "summary": "Meeting",
            "start": {"dateTime": "2026-01-24T10:00:00Z"},
            "end": {"dateTime": "2026-01-24T11:00:00Z"},
        }

        args = Mock()
        args.event_id = "event1"
        args.calendar = "primary"
        args.json = False

        result = cmd_events_get(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Meeting" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "create_event")
    def test_cmd_events_create(self, mock_create, _mock_service, capsys):
        """Test events create command."""
        mock_create.return_value = {
            "id": "new-event",
            "summary": "New Meeting",
            "htmlLink": "https://calendar.google.com/event?id=new-event",
        }

        args = Mock()
        args.summary = "New Meeting"
        args.start = "2026-01-24T10:00:00Z"
        args.end = "2026-01-24T11:00:00Z"
        args.calendar = "primary"
        args.description = None
        args.location = None
        args.attendees = None
        args.timezone = None
        args.json = False

        result = cmd_events_create(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Event created successfully" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "update_event")
    def test_cmd_events_update(self, mock_update, _mock_service, capsys):
        """Test events update command."""
        mock_update.return_value = {
            "id": "event1",
            "summary": "Updated Meeting",
        }

        args = Mock()
        args.event_id = "event1"
        args.calendar = "primary"
        args.summary = "Updated Meeting"
        args.start = None
        args.end = None
        args.description = None
        args.location = None
        args.json = False

        result = cmd_events_update(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Event updated successfully" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "delete_event")
    def test_cmd_events_delete(self, _mock_delete, _mock_service, capsys):
        """Test events delete command."""
        args = Mock()
        args.event_id = "event1"
        args.calendar = "primary"
        args.json = False

        result = cmd_events_delete(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Event deleted successfully" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "check_freebusy")
    def test_cmd_freebusy(self, mock_freebusy, _mock_service, capsys):
        """Test freebusy command."""
        mock_freebusy.return_value = {
            "calendars": {
                "primary": {
                    "busy": [{"start": "2026-01-24T10:00:00Z", "end": "2026-01-24T11:00:00Z"}]
                }
            }
        }

        args = Mock()
        args.start = "2026-01-24T00:00:00Z"
        args.end = "2026-01-24T23:59:59Z"
        args.calendars = None
        args.json = False

        result = cmd_freebusy(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Free/Busy" in captured.out

    @patch.object(google_calendar, "get_google_credentials")
    @patch("google_calendar.build")
    def test_build_calendar_service(self, mock_build, mock_get_creds):
        """Test building calendar service."""
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        service = build_calendar_service()
        assert service == mock_service
        mock_get_creds.assert_called_once()
        mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)

    @patch.object(google_calendar, "get_google_credentials")
    @patch("google_calendar.build")
    def test_check_calendar_connectivity_success(self, mock_build, mock_get_creds):
        """Test checking calendar connectivity successfully."""
        mock_creds = Mock()
        mock_creds.scopes = ["calendar.readonly", "calendar.events"]
        mock_get_creds.return_value = mock_creds

        mock_service = Mock()
        mock_service.calendarList().list().execute.return_value = {
            "items": [
                {
                    "primary": True,
                    "summary": "My Calendar",
                    "id": "primary",
                    "timeZone": "America/New_York",
                }
            ]
        }
        mock_build.return_value = mock_service

        result = check_calendar_connectivity()
        assert result["authenticated"] is True
        assert result["primary_calendar"]["summary"] == "My Calendar"

    @patch.object(google_calendar, "get_google_credentials")
    def test_check_calendar_connectivity_failure(self, mock_get_creds):
        """Test checking calendar connectivity with failure."""
        mock_get_creds.side_effect = Exception("Auth failed")

        result = check_calendar_connectivity()
        assert result["authenticated"] is False
        assert "Auth failed" in result["error"]


# ============================================================================
# PARSER TESTS
# ============================================================================


class TestParser:
    """Tests for argument parser."""

    def test_build_parser(self):
        """Test building argument parser."""
        parser = build_parser()
        assert parser is not None

        # Test check command
        args = parser.parse_args(["check"])
        assert args.command == "check"

        # Test auth setup command
        args = parser.parse_args(
            ["auth", "setup", "--client-id", "id", "--client-secret", "secret"]
        )
        assert args.command == "auth"
        assert args.auth_command == "setup"
        assert args.client_id == "id"

        # Test events create command
        args = parser.parse_args(
            [
                "events",
                "create",
                "--summary",
                "Meeting",
                "--start",
                "2026-01-24T10:00:00Z",
                "--end",
                "2026-01-24T11:00:00Z",
            ]
        )
        assert args.command == "events"
        assert args.events_command == "create"
        assert args.summary == "Meeting"

        # Test freebusy command
        args = parser.parse_args(
            [
                "freebusy",
                "--start",
                "2026-01-24T00:00:00Z",
                "--end",
                "2026-01-24T23:59:59Z",
            ]
        )
        assert args.command == "freebusy"
        assert args.start == "2026-01-24T00:00:00Z"


# ============================================================================
# MAIN FUNCTION TESTS
# ============================================================================


class TestMain:
    """Tests for main function."""

    def test_main_no_command(self, monkeypatch):
        """Test main with no command."""
        monkeypatch.setattr(sys, "argv", ["google-calendar.py"])

        import google_calendar

        result = google_calendar.main()
        assert result == 1

    @patch.object(google_calendar, "cmd_check")
    def test_main_check_command(self, mock_cmd, monkeypatch):
        """Test main with check command."""
        mock_cmd.return_value = 0
        monkeypatch.setattr(sys, "argv", ["google-calendar.py", "check"])

        import google_calendar

        result = google_calendar.main()
        assert result == 0
        assert mock_cmd.called

    def test_main_keyboard_interrupt(self, monkeypatch):
        """Test main with keyboard interrupt."""
        monkeypatch.setattr(sys, "argv", ["google-calendar.py", "check"])

        with patch("google_calendar.cmd_check", side_effect=KeyboardInterrupt()):
            import google_calendar

            result = google_calendar.main()
            assert result == 130

    def test_main_calendar_api_error(self, monkeypatch):
        """Test main with CalendarAPIError."""
        monkeypatch.setattr(sys, "argv", ["google-calendar.py", "check"])

        with patch("google_calendar.cmd_check", side_effect=CalendarAPIError("API Error", 500)):
            import google_calendar

            result = google_calendar.main()
            assert result == 1

    def test_main_authentication_error(self, monkeypatch):
        """Test main with AuthenticationError."""
        monkeypatch.setattr(sys, "argv", ["google-calendar.py", "check"])

        with patch("google_calendar.cmd_check", side_effect=AuthenticationError("Auth Error")):
            import google_calendar

            result = google_calendar.main()
            assert result == 1

    def test_main_unexpected_error(self, monkeypatch):
        """Test main with unexpected error."""
        monkeypatch.setattr(sys, "argv", ["google-calendar.py", "check"])

        with patch("google_calendar.cmd_check", side_effect=RuntimeError("Unexpected")):
            import google_calendar

            result = google_calendar.main()
            assert result == 1


# ============================================================================
# ADDITIONAL EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and additional coverage."""

    def test_cmd_auth_setup_missing_params(self, capsys):
        """Test auth setup with missing parameters."""
        args = Mock()
        args.client_id = None
        args.client_secret = "secret"

        result = cmd_auth_setup(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "required" in captured.err

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "list_events")
    def test_cmd_events_list_no_results(self, mock_list, _mock_service, capsys):
        """Test events list with no results."""
        mock_list.return_value = []

        args = Mock()
        args.json = False
        args.calendar = "primary"
        args.time_min = None
        args.time_max = None
        args.max_results = 10
        args.query = None

        result = cmd_events_list(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "No events found" in captured.out

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "create_event")
    def test_cmd_events_create_with_attendees(self, mock_create, _mock_service, _capsys):
        """Test events create with attendees."""
        mock_create.return_value = {
            "id": "new-event",
            "summary": "Meeting",
        }

        args = Mock()
        args.summary = "Meeting"
        args.start = "2026-01-24T10:00:00Z"
        args.end = "2026-01-24T11:00:00Z"
        args.calendar = "primary"
        args.description = "Test description"
        args.location = "Room A"
        args.attendees = "alice@example.com,bob@example.com"
        args.timezone = "America/New_York"
        args.json = False

        result = cmd_events_create(args)
        assert result == 0

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "check_freebusy")
    def test_cmd_freebusy_with_calendars(self, mock_freebusy, _mock_service, capsys):
        """Test freebusy with specific calendars."""
        mock_freebusy.return_value = {
            "calendars": {
                "primary": {"busy": []},
                "cal2": {"busy": []},
            }
        }

        args = Mock()
        args.start = "2026-01-24T00:00:00Z"
        args.end = "2026-01-24T23:59:59Z"
        args.calendars = "primary,cal2"
        args.json = True

        result = cmd_freebusy(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "calendars" in output

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "list_calendars")
    def test_cmd_calendars_list_json(self, mock_list, _mock_service, capsys):
        """Test calendars list with JSON output."""
        mock_list.return_value = [
            {"id": "primary", "summary": "My Calendar"},
        ]

        args = Mock()
        args.json = True

        result = cmd_calendars_list(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert len(output) == 1

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "list_calendars")
    def test_cmd_calendars_list_no_results(self, mock_list, _mock_service, capsys):
        """Test calendars list with no results."""
        mock_list.return_value = []

        args = Mock()
        args.json = False

        result = cmd_calendars_list(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "No calendars found" in captured.out

    def test_format_event_minimal(self):
        """Test formatting event with minimal data."""
        event = {
            "id": "event1",
            "summary": "Meeting",
            "start": {"dateTime": "2026-01-24T10:00:00Z"},
            "end": {"dateTime": "2026-01-24T11:00:00Z"},
        }

        formatted = format_event(event)
        assert "Meeting" in formatted
        assert "event1" in formatted

    def test_format_calendar_minimal(self):
        """Test formatting calendar with minimal data."""
        calendar = {
            "id": "primary",
            "summary": "My Calendar",
        }

        formatted = format_calendar(calendar)
        assert "My Calendar" in formatted
        assert "primary" in formatted

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "get_calendar")
    def test_cmd_calendars_get_json(self, mock_get, _mock_service, capsys):
        """Test calendars get with JSON output."""
        mock_get.return_value = {
            "id": "primary",
            "summary": "My Calendar",
        }

        args = Mock()
        args.calendar_id = "primary"
        args.json = True

        result = cmd_calendars_get(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["id"] == "primary"

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "get_event")
    def test_cmd_events_get_json(self, mock_get, _mock_service, capsys):
        """Test events get with JSON output."""
        mock_get.return_value = {
            "id": "event1",
            "summary": "Meeting",
        }

        args = Mock()
        args.event_id = "event1"
        args.calendar = "primary"
        args.json = True

        result = cmd_events_get(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["id"] == "event1"

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "create_event")
    def test_cmd_events_create_json(self, mock_create, _mock_service, capsys):
        """Test events create with JSON output."""
        mock_create.return_value = {
            "id": "new-event",
            "summary": "Meeting",
        }

        args = Mock()
        args.summary = "Meeting"
        args.start = "2026-01-24T10:00:00Z"
        args.end = "2026-01-24T11:00:00Z"
        args.calendar = "primary"
        args.description = None
        args.location = None
        args.attendees = None
        args.timezone = None
        args.json = True

        result = cmd_events_create(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["id"] == "new-event"

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "update_event")
    def test_cmd_events_update_json(self, mock_update, _mock_service, capsys):
        """Test events update with JSON output."""
        mock_update.return_value = {
            "id": "event1",
            "summary": "Updated",
        }

        args = Mock()
        args.event_id = "event1"
        args.calendar = "primary"
        args.summary = "Updated"
        args.start = None
        args.end = None
        args.description = None
        args.location = None
        args.json = True

        result = cmd_events_update(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["summary"] == "Updated"

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "delete_event")
    def test_cmd_events_delete_json(self, _mock_delete, _mock_service):
        """Test events delete with JSON output."""
        args = Mock()
        args.event_id = "event1"
        args.calendar = "primary"
        args.json = True

        result = cmd_events_delete(args)
        assert result == 0

    @patch.object(google_calendar, "build_calendar_service")
    @patch.object(google_calendar, "check_freebusy")
    def test_cmd_freebusy_json(self, mock_freebusy, _mock_service, capsys):
        """Test freebusy with JSON output."""
        mock_freebusy.return_value = {"calendars": {"primary": {"busy": []}}}

        args = Mock()
        args.start = "2026-01-24T00:00:00Z"
        args.end = "2026-01-24T23:59:59Z"
        args.calendars = None
        args.json = True

        result = cmd_freebusy(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "calendars" in output
