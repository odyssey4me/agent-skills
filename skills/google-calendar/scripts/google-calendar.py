#!/usr/bin/env python3
"""Google Calendar integration skill for AI agents.

This is a self-contained script that provides Google Calendar functionality.

Usage:
    python google-calendar.py check
    python google-calendar.py auth setup --client-id ID --client-secret SECRET
    python google-calendar.py calendars list
    python google-calendar.py events list --calendar primary --time-min "2026-01-01T00:00:00Z"
    python google-calendar.py events get EVENT_ID --calendar primary
    python google-calendar.py events create --summary "Meeting" --start "2026-01-24T10:00:00-05:00" --end "2026-01-24T11:00:00-05:00"
    python google-calendar.py events update EVENT_ID --summary "Updated Meeting"
    python google-calendar.py events delete EVENT_ID --calendar primary
    python google-calendar.py freebusy --start "2026-01-24T00:00:00Z" --end "2026-01-25T00:00:00Z"

Requirements:
    pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
"""

from __future__ import annotations

# Standard library imports
import argparse
import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any

# ============================================================================
# DEPENDENCY CHECKS
# ============================================================================

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print(
        "Error: Google auth libraries not found. Install with: "
        "pip install --user google-auth google-auth-oauthlib",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print(
        "Error: 'google-api-python-client' not found. Install with: "
        "pip install --user google-api-python-client",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import keyring
except ImportError:
    print(
        "Error: 'keyring' library not found. Install with: pip install --user keyring",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import yaml
except ImportError:
    print(
        "Error: 'pyyaml' library not found. Install with: pip install --user pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)


# ============================================================================
# CONSTANTS
# ============================================================================

SERVICE_NAME = "agent-skills"
CONFIG_DIR = Path.home() / ".config" / "agent-skills"

# Google Calendar API scopes - granular scopes for different operations
CALENDAR_SCOPES_READONLY = ["https://www.googleapis.com/auth/calendar.readonly"]
CALENDAR_SCOPES_EVENTS = ["https://www.googleapis.com/auth/calendar.events"]

# Full scope set for maximum functionality
CALENDAR_SCOPES_FULL = CALENDAR_SCOPES_READONLY + CALENDAR_SCOPES_EVENTS

# Minimal read-only scope (default)
CALENDAR_SCOPES_DEFAULT = CALENDAR_SCOPES_READONLY


# ============================================================================
# KEYRING CREDENTIAL STORAGE
# ============================================================================


def get_credential(key: str) -> str | None:
    """Get a credential from the system keyring.

    Args:
        key: The credential key (e.g., "google-calendar-token-json").

    Returns:
        The credential value, or None if not found.
    """
    return keyring.get_password(SERVICE_NAME, key)


def set_credential(key: str, value: str) -> None:
    """Store a credential in the system keyring.

    Args:
        key: The credential key.
        value: The credential value.
    """
    keyring.set_password(SERVICE_NAME, key, value)


def delete_credential(key: str) -> None:
    """Delete a credential from the system keyring.

    Args:
        key: The credential key.
    """
    with contextlib.suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SERVICE_NAME, key)


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================


def load_config(service: str) -> dict[str, Any] | None:
    """Load configuration from file.

    Args:
        service: Service name.

    Returns:
        Configuration dictionary or None if not found.
    """
    config_file = CONFIG_DIR / f"{service}.yaml"
    if config_file.exists():
        with open(config_file) as f:
            return yaml.safe_load(f)
    return None


def save_config(service: str, config: dict[str, Any]) -> None:
    """Save configuration to file.

    Args:
        service: Service name.
        config: Configuration dictionary.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file = CONFIG_DIR / f"{service}.yaml"
    with open(config_file, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


# ============================================================================
# GOOGLE AUTHENTICATION
# ============================================================================


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""

    pass


def _build_oauth_config(client_id: str, client_secret: str) -> dict[str, Any]:
    """Build OAuth client configuration dict.

    Args:
        client_id: OAuth client ID.
        client_secret: OAuth client secret.

    Returns:
        OAuth client configuration dict.
    """
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def get_oauth_client_config(service: str) -> dict[str, Any]:
    """Get OAuth 2.0 client configuration from config file or environment.

    Priority:
    1. Service-specific config file (~/.config/agent-skills/{service}.yaml)
    2. Service-specific environment variables ({SERVICE}_CLIENT_ID, {SERVICE}_CLIENT_SECRET)
    3. Shared Google config file (~/.config/agent-skills/google.yaml)
    4. Shared environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)

    Args:
        service: Service name (e.g., "google-calendar").

    Returns:
        OAuth client configuration dict.

    Raises:
        AuthenticationError: If client configuration is not found.
    """
    # 1. Try service-specific config file first
    config = load_config(service)
    if config and "oauth_client" in config:
        client_id = config["oauth_client"].get("client_id")
        client_secret = config["oauth_client"].get("client_secret")
        if client_id and client_secret:
            return _build_oauth_config(client_id, client_secret)

    # 2. Try service-specific environment variables
    prefix = service.upper().replace("-", "_")
    client_id = os.environ.get(f"{prefix}_CLIENT_ID")
    client_secret = os.environ.get(f"{prefix}_CLIENT_SECRET")
    if client_id and client_secret:
        return _build_oauth_config(client_id, client_secret)

    # 3. Try shared Google config file
    shared_config = load_config("google")
    if shared_config and "oauth_client" in shared_config:
        client_id = shared_config["oauth_client"].get("client_id")
        client_secret = shared_config["oauth_client"].get("client_secret")
        if client_id and client_secret:
            return _build_oauth_config(client_id, client_secret)

    # 4. Try shared environment variables
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        return _build_oauth_config(client_id, client_secret)

    raise AuthenticationError(
        f"OAuth client credentials not found for {service}. "
        f"Options:\n"
        f"  1. Service config: Run python google-calendar.py auth setup --client-id YOUR_ID --client-secret YOUR_SECRET\n"
        f"  2. Service env vars: Set GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET\n"
        f"  3. Shared config: Create ~/.config/agent-skills/google.yaml with oauth_client credentials\n"
        f"  4. Shared env vars: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    )


def get_google_credentials(service: str, scopes: list[str]) -> Credentials:
    """Get Google credentials for human-in-the-loop use cases.

    Priority:
    1. Application Default Credentials (gcloud) - if configured with user OAuth
    2. Saved OAuth tokens from keyring - from previous custom OAuth flow
    3. Custom OAuth 2.0 flow - opens browser for user consent

    Note: Service account authentication is NOT supported - this is
    designed for interactive human use cases only.

    Args:
        service: Service name (e.g., "google-calendar").
        scopes: List of OAuth scopes required.

    Returns:
        Valid Google credentials.

    Raises:
        AuthenticationError: If authentication fails.
    """
    # 1. Try gcloud Application Default Credentials (user OAuth only)
    try:
        from google.auth import default

        creds, _ = default(scopes=scopes)
        # Verify these are user credentials (have refresh_token), not service account
        if creds and creds.valid and hasattr(creds, "refresh_token"):
            return creds
    except Exception:
        # ADC not available or not user credentials
        pass

    # 2. Try keyring-stored OAuth token from previous flow
    token_json = get_credential(f"{service}-token-json")
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), scopes)
            if creds and creds.valid:
                return creds
            # Refresh if expired but has refresh token
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                set_credential(f"{service}-token-json", creds.to_json())
                return creds
        except Exception:
            # Invalid or corrupted token, fall through to OAuth flow
            pass

    # 3. Initiate custom OAuth flow - human interaction required
    try:
        client_config = get_oauth_client_config(service)
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        creds = flow.run_local_server(port=0)  # Opens browser for consent
        # Save token to keyring for future use
        set_credential(f"{service}-token-json", creds.to_json())
        return creds
    except Exception as e:
        raise AuthenticationError(f"OAuth flow failed: {e}") from e


def build_calendar_service(scopes: list[str] | None = None):
    """Build and return Google Calendar API service.

    Args:
        scopes: List of OAuth scopes to request. Defaults to read-only.

    Returns:
        Calendar API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    if scopes is None:
        scopes = CALENDAR_SCOPES_DEFAULT
    creds = get_google_credentials("google-calendar", scopes)
    return build("calendar", "v3", credentials=creds)


# ============================================================================
# CALENDAR API ERROR HANDLING
# ============================================================================


class CalendarAPIError(Exception):
    """Exception raised for Calendar API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def handle_api_error(error: HttpError) -> None:
    """Convert Google API HttpError to CalendarAPIError.

    Args:
        error: HttpError from Google API.

    Raises:
        CalendarAPIError: With appropriate message and status code.
    """
    status_code = error.resp.status
    reason = error.resp.reason
    details = None

    try:
        error_content = json.loads(error.content.decode("utf-8"))
        details = error_content.get("error", {})
        message = details.get("message", reason)
    except Exception:
        message = reason

    # Check for insufficient scope error (403)
    if status_code == 403 and "insufficient" in message.lower():
        scope_help = (
            "\n\nInsufficient OAuth scope. This operation requires additional permissions.\n"
            "To grant full access, re-authenticate with all scopes:\n\n"
            "  gcloud auth application-default login \\\n"
            "    --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/calendar.events\n\n"
            "Or for custom OAuth, see: skills/google-calendar/references/oauth-setup.md\n"
        )
        message = f"{message}{scope_help}"

    raise CalendarAPIError(
        f"Calendar API error: {message} (HTTP {status_code})",
        status_code=status_code,
        details=details,
    )


# ============================================================================
# CALENDAR OPERATIONS
# ============================================================================


def list_calendars(service) -> list[dict[str, Any]]:
    """List all calendars for the authenticated user.

    Args:
        service: Calendar API service object.

    Returns:
        List of calendar dictionaries.

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        result = service.calendarList().list().execute()
        calendars = result.get("items", [])
        return calendars
    except HttpError as e:
        handle_api_error(e)
        return []  # Unreachable


def get_calendar(service, calendar_id: str = "primary") -> dict[str, Any]:
    """Get calendar details.

    Args:
        service: Calendar API service object.
        calendar_id: Calendar ID (default: "primary").

    Returns:
        Calendar dictionary.

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        return calendar
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# EVENT OPERATIONS
# ============================================================================


def list_events(
    service,
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 10,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """List calendar events.

    Args:
        service: Calendar API service object.
        calendar_id: Calendar ID (default: "primary").
        time_min: Lower bound (RFC3339 timestamp).
        time_max: Upper bound (RFC3339 timestamp).
        max_results: Maximum number of events to return.
        query: Free text search query.

    Returns:
        List of event dictionaries.

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        params: dict[str, Any] = {
            "calendarId": calendar_id,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        if query:
            params["q"] = query

        result = service.events().list(**params).execute()
        events = result.get("items", [])
        return events
    except HttpError as e:
        handle_api_error(e)
        return []  # Unreachable


def get_event(service, event_id: str, calendar_id: str = "primary") -> dict[str, Any]:
    """Get event details.

    Args:
        service: Calendar API service object.
        event_id: Event ID.
        calendar_id: Calendar ID (default: "primary").

    Returns:
        Event dictionary.

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return event
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def create_event(
    service,
    summary: str,
    start: str,
    end: str,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    timezone: str | None = None,
) -> dict[str, Any]:
    """Create a calendar event.

    Args:
        service: Calendar API service object.
        summary: Event title.
        start: Start time (RFC3339 timestamp or date).
        end: End time (RFC3339 timestamp or date).
        calendar_id: Calendar ID (default: "primary").
        description: Event description.
        location: Event location.
        attendees: List of attendee email addresses.
        timezone: Timezone for date-only events (e.g., "America/New_York").

    Returns:
        Created event dictionary.

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        # Build event body
        event_body: dict[str, Any] = {
            "summary": summary,
        }

        # Handle start/end time - support both datetime and date formats
        if "T" in start:
            event_body["start"] = {"dateTime": start}
            event_body["end"] = {"dateTime": end}
        else:
            # All-day event
            event_body["start"] = {"date": start}
            event_body["end"] = {"date": end}
            if timezone:
                event_body["start"]["timeZone"] = timezone
                event_body["end"]["timeZone"] = timezone

        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        return event
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def update_event(
    service,
    event_id: str,
    calendar_id: str = "primary",
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    """Update a calendar event.

    Args:
        service: Calendar API service object.
        event_id: Event ID.
        calendar_id: Calendar ID (default: "primary").
        summary: New event title.
        start: New start time (RFC3339 timestamp or date).
        end: New end time (RFC3339 timestamp or date).
        description: New event description.
        location: New event location.

    Returns:
        Updated event dictionary.

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        # Get existing event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Update fields
        if summary is not None:
            event["summary"] = summary
        if start is not None:
            if "T" in start:
                event["start"] = {"dateTime": start}
            else:
                event["start"] = {"date": start}
        if end is not None:
            if "T" in end:
                event["end"] = {"dateTime": end}
            else:
                event["end"] = {"date": end}
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location

        # Update event
        updated = (
            service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        )
        return updated
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def delete_event(service, event_id: str, calendar_id: str = "primary") -> None:
    """Delete a calendar event.

    Args:
        service: Calendar API service object.
        event_id: Event ID.
        calendar_id: Calendar ID (default: "primary").

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except HttpError as e:
        handle_api_error(e)


# ============================================================================
# FREEBUSY OPERATIONS
# ============================================================================


def check_freebusy(
    service,
    time_min: str,
    time_max: str,
    calendar_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Check free/busy information for calendars.

    Args:
        service: Calendar API service object.
        time_min: Start time (RFC3339 timestamp).
        time_max: End time (RFC3339 timestamp).
        calendar_ids: List of calendar IDs to check (default: ["primary"]).

    Returns:
        Freebusy query result dictionary.

    Raises:
        CalendarAPIError: If the API call fails.
    """
    try:
        if calendar_ids is None:
            calendar_ids = ["primary"]

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": cal_id} for cal_id in calendar_ids],
        }

        result = service.freebusy().query(body=body).execute()
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_calendar(calendar: dict[str, Any]) -> str:
    """Format a calendar for display.

    Args:
        calendar: Calendar dictionary from API.

    Returns:
        Formatted string.
    """
    summary = calendar.get("summary", "(No name)")
    cal_id = calendar.get("id", "(Unknown)")
    description = calendar.get("description", "")
    timezone = calendar.get("timeZone", "")
    primary = " [PRIMARY]" if calendar.get("primary", False) else ""

    output = f"{summary}{primary}\n  ID: {cal_id}"
    if timezone:
        output += f"\n  Timezone: {timezone}"
    if description:
        output += f"\n  Description: {description}"
    return output


def format_event(event: dict[str, Any]) -> str:
    """Format an event for display.

    Args:
        event: Event dictionary from API.

    Returns:
        Formatted string.
    """
    summary = event.get("summary", "(No title)")
    event_id = event.get("id", "(Unknown)")

    # Get start/end times
    start = event.get("start", {})
    end = event.get("end", {})
    start_time = start.get("dateTime", start.get("date", "(Unknown)"))
    end_time = end.get("dateTime", end.get("date", "(Unknown)"))

    output = f"{summary}\n  ID: {event_id}\n  Start: {start_time}\n  End: {end_time}"

    location = event.get("location")
    if location:
        output += f"\n  Location: {location}"

    description = event.get("description")
    if description:
        # Truncate long descriptions
        desc_preview = description[:100] + "..." if len(description) > 100 else description
        output += f"\n  Description: {desc_preview}"

    attendees = event.get("attendees", [])
    if attendees:
        emails = [a.get("email", "") for a in attendees]
        output += f"\n  Attendees: {', '.join(emails)}"

    return output


# ============================================================================
# HEALTH CHECK
# ============================================================================


def check_calendar_connectivity() -> dict[str, Any]:
    """Check Calendar API connectivity and authentication.

    Returns:
        Dictionary with status information including available scopes.
    """
    result = {
        "authenticated": False,
        "primary_calendar": None,
        "scopes": None,
        "error": None,
    }

    try:
        # Get credentials to check scopes
        creds = get_google_credentials("google-calendar", CALENDAR_SCOPES_DEFAULT)

        # Check which scopes are available
        available_scopes = []
        if hasattr(creds, "scopes"):
            available_scopes = creds.scopes
        elif hasattr(creds, "_scopes"):
            available_scopes = creds._scopes

        # Build service and get primary calendar
        service = build("calendar", "v3", credentials=creds)
        cal_list = service.calendarList().list().execute()
        primary = next((c for c in cal_list.get("items", []) if c.get("primary")), None)

        result["authenticated"] = True
        if primary:
            result["primary_calendar"] = {
                "summary": primary.get("summary"),
                "id": primary.get("id"),
                "timezone": primary.get("timeZone"),
            }
        result["scopes"] = {
            "readonly": any("calendar.readonly" in s for s in available_scopes),
            "events": any("calendar.events" in s for s in available_scopes),
            "all_scopes": available_scopes,
        }
    except Exception as e:
        result["error"] = str(e)

    return result


# ============================================================================
# CLI COMMAND HANDLERS
# ============================================================================


def cmd_check(_args):
    """Handle 'check' command."""
    print("Checking Google Calendar connectivity...")
    result = check_calendar_connectivity()

    if result["authenticated"]:
        print("✓ Successfully authenticated to Google Calendar")
        if result["primary_calendar"]:
            cal = result["primary_calendar"]
            print(f"  Primary Calendar: {cal['summary']}")
            print(f"  Calendar ID: {cal['id']}")
            print(f"  Timezone: {cal['timezone']}")

        # Display scope information
        scopes = result.get("scopes", {})
        if scopes:
            print("\nGranted OAuth Scopes:")
            print(f"  Read-only (calendar.readonly): {'✓' if scopes.get('readonly') else '✗'}")
            print(f"  Events (calendar.events):      {'✓' if scopes.get('events') else '✗'}")

            # Check if all scopes are granted
            all_granted = all([scopes.get("readonly"), scopes.get("events")])

            if not all_granted:
                print("\n⚠️  Not all scopes are granted. Some operations may fail.")
                print("   To grant full access, re-authenticate with:")
                print()
                print("   gcloud auth application-default login \\")
                print("     --scopes=https://www.googleapis.com/auth/cloud-platform,\\")
                print("https://www.googleapis.com/auth/calendar.readonly,\\")
                print("https://www.googleapis.com/auth/calendar.events")
                print()
                print("   Or see: skills/google-calendar/references/oauth-setup.md")
        return 0
    else:
        print(f"✗ Authentication failed: {result['error']}")
        print()

        # Check if gcloud is available
        import shutil

        gcloud_available = shutil.which("gcloud") is not None

        if gcloud_available:
            print("Setup instructions (gcloud CLI detected - RECOMMENDED):")
            print("  1. Authenticate with gcloud:")
            print("     gcloud auth application-default login \\")
            print("       --scopes=https://www.googleapis.com/auth/cloud-platform,\\")
            print("https://www.googleapis.com/auth/calendar.readonly,\\")
            print("https://www.googleapis.com/auth/calendar.events")
            print()
            print("  2. Run check again:")
            print("     python scripts/google-calendar.py check")
        else:
            print("Setup instructions:")
            print("  Method 1 (Recommended): Install and use gcloud CLI")
            print("    - Install from: https://cloud.google.com/sdk/docs/install")
            print("    - Then run: gcloud auth application-default login --scopes=...")
            print()
            print("  Method 2: Custom OAuth 2.0 credentials")
            print("    1. Create OAuth credentials in Google Cloud Console")
            print("    2. Store credentials:")
            print(
                "       python scripts/google-calendar.py auth setup --client-id YOUR_ID --client-secret YOUR_SECRET"
            )
            print("    3. Run any command to trigger OAuth flow")

        print()
        print(
            "For detailed setup instructions, see: skills/google-calendar/references/oauth-setup.md"
        )
        return 1


def cmd_auth_setup(args):
    """Handle 'auth setup' command."""
    if not args.client_id or not args.client_secret:
        print("Error: Both --client-id and --client-secret are required", file=sys.stderr)
        return 1

    config = load_config("google-calendar") or {}
    config["oauth_client"] = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
    }
    save_config("google-calendar", config)
    print("✓ OAuth client credentials saved to config file")
    print(f"  Config location: {CONFIG_DIR / 'google-calendar.yaml'}")
    print("\nNext step: Run any Calendar command to initiate OAuth flow")
    return 0


def cmd_calendars_list(args):
    """Handle 'calendars list' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY)
    calendars = list_calendars(service)

    if args.json:
        print(json.dumps(calendars, indent=2))
    else:
        if not calendars:
            print("No calendars found")
        else:
            print(f"Found {len(calendars)} calendar(s):\n")
            for cal in calendars:
                print(format_calendar(cal))
                print("-" * 80)

    return 0


def cmd_calendars_get(args):
    """Handle 'calendars get' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY)
    calendar = get_calendar(service, args.calendar_id)

    if args.json:
        print(json.dumps(calendar, indent=2))
    else:
        print(format_calendar(calendar))

    return 0


def cmd_events_list(args):
    """Handle 'events list' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY)
    events = list_events(
        service,
        calendar_id=args.calendar,
        time_min=args.time_min,
        time_max=args.time_max,
        max_results=args.max_results,
        query=args.query,
    )

    if args.json:
        print(json.dumps(events, indent=2))
    else:
        if not events:
            print("No events found")
        else:
            print(f"Found {len(events)} event(s):\n")
            for event in events:
                print(format_event(event))
                print("-" * 80)

    return 0


def cmd_events_get(args):
    """Handle 'events get' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY)
    event = get_event(service, args.event_id, args.calendar)

    if args.json:
        print(json.dumps(event, indent=2))
    else:
        print(format_event(event))

    return 0


def cmd_events_create(args):
    """Handle 'events create' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY + CALENDAR_SCOPES_EVENTS)

    # Parse attendees if provided
    attendees = None
    if args.attendees:
        attendees = [email.strip() for email in args.attendees.split(",")]

    result = create_event(
        service,
        summary=args.summary,
        start=args.start,
        end=args.end,
        calendar_id=args.calendar,
        description=args.description,
        location=args.location,
        attendees=attendees,
        timezone=args.timezone,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Event created successfully")
        print(f"  Event ID: {result.get('id')}")
        print(f"  Summary: {result.get('summary')}")
        html_link = result.get("htmlLink")
        if html_link:
            print(f"  Link: {html_link}")

    return 0


def cmd_events_update(args):
    """Handle 'events update' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY + CALENDAR_SCOPES_EVENTS)
    result = update_event(
        service,
        event_id=args.event_id,
        calendar_id=args.calendar,
        summary=args.summary,
        start=args.start,
        end=args.end,
        description=args.description,
        location=args.location,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Event updated successfully")
        print(f"  Event ID: {result.get('id')}")
        print(f"  Summary: {result.get('summary')}")

    return 0


def cmd_events_delete(args):
    """Handle 'events delete' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY + CALENDAR_SCOPES_EVENTS)
    delete_event(service, args.event_id, args.calendar)

    if not args.json:
        print("✓ Event deleted successfully")

    return 0


def cmd_freebusy(args):
    """Handle 'freebusy' command."""
    service = build_calendar_service(CALENDAR_SCOPES_READONLY)

    # Parse calendar IDs if provided
    calendar_ids = None
    if args.calendars:
        calendar_ids = [cal.strip() for cal in args.calendars.split(",")]

    result = check_freebusy(
        service,
        time_min=args.start,
        time_max=args.end,
        calendar_ids=calendar_ids,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Free/Busy Information:\n")
        calendars = result.get("calendars", {})
        for cal_id, cal_info in calendars.items():
            print(f"Calendar: {cal_id}")
            busy = cal_info.get("busy", [])
            if not busy:
                print("  No busy times")
            else:
                print(f"  Busy periods: {len(busy)}")
                for period in busy:
                    print(f"    {period.get('start')} - {period.get('end')}")
            print("-" * 80)

    return 0


# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Google Calendar integration for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check command
    subparsers.add_parser("check", help="Check Calendar connectivity and authentication")

    # auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    setup_parser = auth_subparsers.add_parser("setup", help="Setup OAuth client credentials")
    setup_parser.add_argument("--client-id", required=True, help="OAuth client ID")
    setup_parser.add_argument("--client-secret", required=True, help="OAuth client secret")

    # calendars commands
    calendars_parser = subparsers.add_parser("calendars", help="Calendar operations")
    calendars_subparsers = calendars_parser.add_subparsers(dest="calendars_command")

    calendars_list_parser = calendars_subparsers.add_parser("list", help="List calendars")
    calendars_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    calendars_get_parser = calendars_subparsers.add_parser("get", help="Get calendar details")
    calendars_get_parser.add_argument("calendar_id", help="Calendar ID (or 'primary')")
    calendars_get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # events commands
    events_parser = subparsers.add_parser("events", help="Event operations")
    events_subparsers = events_parser.add_subparsers(dest="events_command")

    events_list_parser = events_subparsers.add_parser("list", help="List events")
    events_list_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    events_list_parser.add_argument("--time-min", help="Start time (RFC3339)")
    events_list_parser.add_argument("--time-max", help="End time (RFC3339)")
    events_list_parser.add_argument("--max-results", type=int, default=10, help="Maximum results")
    events_list_parser.add_argument("--query", help="Search query")
    events_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    events_get_parser = events_subparsers.add_parser("get", help="Get event by ID")
    events_get_parser.add_argument("event_id", help="Event ID")
    events_get_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    events_get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    events_create_parser = events_subparsers.add_parser("create", help="Create an event")
    events_create_parser.add_argument("--summary", required=True, help="Event title")
    events_create_parser.add_argument(
        "--start", required=True, help="Start time (RFC3339 or YYYY-MM-DD)"
    )
    events_create_parser.add_argument(
        "--end", required=True, help="End time (RFC3339 or YYYY-MM-DD)"
    )
    events_create_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    events_create_parser.add_argument("--description", help="Event description")
    events_create_parser.add_argument("--location", help="Event location")
    events_create_parser.add_argument("--attendees", help="Comma-separated attendee emails")
    events_create_parser.add_argument("--timezone", help="Timezone for all-day events")
    events_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    events_update_parser = events_subparsers.add_parser("update", help="Update an event")
    events_update_parser.add_argument("event_id", help="Event ID")
    events_update_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    events_update_parser.add_argument("--summary", help="New event title")
    events_update_parser.add_argument("--start", help="New start time (RFC3339 or YYYY-MM-DD)")
    events_update_parser.add_argument("--end", help="New end time (RFC3339 or YYYY-MM-DD)")
    events_update_parser.add_argument("--description", help="New event description")
    events_update_parser.add_argument("--location", help="New event location")
    events_update_parser.add_argument("--json", action="store_true", help="Output as JSON")

    events_delete_parser = events_subparsers.add_parser("delete", help="Delete an event")
    events_delete_parser.add_argument("event_id", help="Event ID")
    events_delete_parser.add_argument("--calendar", default="primary", help="Calendar ID")
    events_delete_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # freebusy command
    freebusy_parser = subparsers.add_parser("freebusy", help="Check free/busy information")
    freebusy_parser.add_argument("--start", required=True, help="Start time (RFC3339)")
    freebusy_parser.add_argument("--end", required=True, help="End time (RFC3339)")
    freebusy_parser.add_argument(
        "--calendars", help="Comma-separated calendar IDs (default: primary)"
    )
    freebusy_parser.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Route to command handlers
        if args.command == "check":
            return cmd_check(args)
        elif args.command == "auth":
            if args.auth_command == "setup":
                return cmd_auth_setup(args)
        elif args.command == "calendars":
            if args.calendars_command == "list":
                return cmd_calendars_list(args)
            elif args.calendars_command == "get":
                return cmd_calendars_get(args)
        elif args.command == "events":
            if args.events_command == "list":
                return cmd_events_list(args)
            elif args.events_command == "get":
                return cmd_events_get(args)
            elif args.events_command == "create":
                return cmd_events_create(args)
            elif args.events_command == "update":
                return cmd_events_update(args)
            elif args.events_command == "delete":
                return cmd_events_delete(args)
        elif args.command == "freebusy":
            return cmd_freebusy(args)

        parser.print_help()
        return 1

    except (CalendarAPIError, AuthenticationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
