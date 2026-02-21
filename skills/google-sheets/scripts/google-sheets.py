#!/usr/bin/env python3
"""Google Sheets integration skill for AI agents.

This is a self-contained script that provides Google Sheets functionality.

Usage:
    python google-sheets.py check
    python google-sheets.py auth setup --client-id ID --client-secret SECRET
    python google-sheets.py spreadsheets create --title "My Spreadsheet"
    python google-sheets.py spreadsheets get SPREADSHEET_ID
    python google-sheets.py values read SPREADSHEET_ID --range "Sheet1!A1:D5"
    python google-sheets.py values write SPREADSHEET_ID --range "Sheet1!A1" --values '[[1,2,3]]'
    python google-sheets.py values append SPREADSHEET_ID --range "Sheet1" --values '[[4,5,6]]'

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

    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    GOOGLE_API_CLIENT_AVAILABLE = True
except ImportError:
    GOOGLE_API_CLIENT_AVAILABLE = False

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ============================================================================
# CONSTANTS
# ============================================================================

SERVICE_NAME = "agent-skills"
CONFIG_DIR = Path.home() / ".config" / "agent-skills"

# Google Sheets API scopes - granular scopes for different operations
SHEETS_SCOPES_READONLY = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Minimal read-only scope (default)
SHEETS_SCOPES_DEFAULT = SHEETS_SCOPES_READONLY


# ============================================================================
# KEYRING CREDENTIAL STORAGE
# ============================================================================


def get_credential(key: str) -> str | None:
    """Get a credential from the system keyring.

    Args:
        key: The credential key (e.g., "google-sheets-token-json").

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
        service: Service name (e.g., "google-sheets").

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
        f"  1. Service config: Run python google-sheets.py auth setup --client-id YOUR_ID --client-secret YOUR_SECRET\n"
        f"  2. Service env vars: Set GOOGLE_SHEETS_CLIENT_ID and GOOGLE_SHEETS_CLIENT_SECRET\n"
        f"  3. Shared config: Create ~/.config/agent-skills/google.yaml with oauth_client credentials\n"
        f"  4. Shared env vars: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    )


def _run_oauth_flow(service: str, scopes: list[str]) -> Credentials:
    """Run OAuth browser flow and store resulting token.

    Args:
        service: Service name (e.g., "google-sheets").
        scopes: List of OAuth scopes required.

    Returns:
        Valid Google credentials.

    Raises:
        AuthenticationError: If OAuth flow fails.
    """
    client_config = get_oauth_client_config(service)
    flow = InstalledAppFlow.from_client_config(client_config, scopes)
    creds = flow.run_local_server(port=0)  # Opens browser for consent
    # Save token to keyring for future use
    set_credential(f"{service}-token-json", creds.to_json())
    return creds


def get_google_credentials(service: str, scopes: list[str]) -> Credentials:
    """Get Google credentials for human-in-the-loop use cases.

    Priority:
    1. Saved OAuth tokens from keyring - from previous OAuth flow
    2. OAuth 2.0 flow - opens browser for user consent

    Note: Service account authentication is NOT supported - this is
    designed for interactive human use cases only.

    Args:
        service: Service name (e.g., "google-sheets").
        scopes: List of OAuth scopes required.

    Returns:
        Valid Google credentials.

    Raises:
        AuthenticationError: If authentication fails.
    """
    # 1. Try keyring-stored OAuth token from previous flow
    token_json = get_credential(f"{service}-token-json")
    if token_json:
        try:
            token_data = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(token_data, scopes)
            if creds and creds.valid:
                # Check if stored token has all requested scopes
                granted = set(token_data.get("scopes", []))
                requested = set(scopes)
                if granted and not requested.issubset(granted):
                    # Merge scopes so user doesn't lose existing access
                    merged = list(granted | requested)
                    print(
                        "Current token lacks required scopes. "
                        "Opening browser for re-authentication...",
                        file=sys.stderr,
                    )
                    delete_credential(f"{service}-token-json")
                    return _run_oauth_flow(service, merged)
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

    # 2. Initiate OAuth flow - human interaction required
    try:
        return _run_oauth_flow(service, scopes)
    except Exception as e:
        raise AuthenticationError(f"OAuth flow failed: {e}") from e


def build_sheets_service(scopes: list[str] | None = None):
    """Build and return Google Sheets API service.

    Args:
        scopes: List of OAuth scopes to request. Defaults to read-only.

    Returns:
        Google Sheets API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    if scopes is None:
        scopes = SHEETS_SCOPES_DEFAULT
    creds = get_google_credentials("google-sheets", scopes)
    return build("sheets", "v4", credentials=creds)


# ============================================================================
# GOOGLE SHEETS API ERROR HANDLING
# ============================================================================


class SheetsAPIError(Exception):
    """Exception raised for Google Sheets API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def handle_api_error(error: HttpError) -> None:
    """Convert Google API HttpError to SheetsAPIError.

    Args:
        error: HttpError from Google API.

    Raises:
        SheetsAPIError: With appropriate message and status code.
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
            "To re-authenticate with the required scopes:\n\n"
            "  1. Reset token: python scripts/google-sheets.py auth reset\n"
            "  2. Re-run: python scripts/google-sheets.py check\n\n"
            "For setup help, see: docs/google-oauth-setup.md\n"
        )
        message = f"{message}{scope_help}"

    raise SheetsAPIError(
        f"Google Sheets API error: {message} (HTTP {status_code})",
        status_code=status_code,
        details=details,
    )


# ============================================================================
# SPREADSHEET OPERATIONS
# ============================================================================


def create_spreadsheet(service, title: str, sheet_names: list[str] | None = None) -> dict[str, Any]:
    """Create a new Google Sheets spreadsheet.

    Args:
        service: Google Sheets API service object.
        title: Spreadsheet title.
        sheet_names: Optional list of sheet names. Default creates one sheet.

    Returns:
        Created spreadsheet dictionary with spreadsheetId.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        body: dict[str, Any] = {"properties": {"title": title}}

        if sheet_names:
            body["sheets"] = [{"properties": {"title": name}} for name in sheet_names]

        spreadsheet = service.spreadsheets().create(body=body).execute()
        return spreadsheet
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def get_spreadsheet(service, spreadsheet_id: str) -> dict[str, Any]:
    """Get a spreadsheet by ID.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.

    Returns:
        Spreadsheet dictionary with metadata and sheets.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return spreadsheet
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def read_values(
    service, spreadsheet_id: str, range_name: str, value_render_option: str = "FORMATTED_VALUE"
) -> dict[str, Any]:
    """Read cell values from a spreadsheet.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        range_name: The range in A1 notation (e.g., "Sheet1!A1:D5").
        value_render_option: How values should be represented (FORMATTED_VALUE, UNFORMATTED_VALUE, FORMULA).

    Returns:
        Result dictionary with values array.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueRenderOption=value_render_option,
            )
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def write_values(
    service, spreadsheet_id: str, range_name: str, values: list[list[Any]]
) -> dict[str, Any]:
    """Write values to a spreadsheet range.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        range_name: The range in A1 notation (e.g., "Sheet1!A1").
        values: 2D array of values to write.

    Returns:
        Update response from the API.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def append_values(
    service, spreadsheet_id: str, range_name: str, values: list[list[Any]]
) -> dict[str, Any]:
    """Append rows to a spreadsheet.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        range_name: The range/sheet name (e.g., "Sheet1").
        values: 2D array of values to append.

    Returns:
        Append response from the API.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def clear_values(service, spreadsheet_id: str, range_name: str) -> dict[str, Any]:
    """Clear values in a spreadsheet range.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        range_name: The range in A1 notation.

    Returns:
        Clear response from the API.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        result = (
            service.spreadsheets()
            .values()
            .clear(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def create_sheet(service, spreadsheet_id: str, title: str) -> dict[str, Any]:
    """Add a new sheet to a spreadsheet.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        title: Sheet title.

    Returns:
        Batch update response from the API.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        requests = [{"addSheet": {"properties": {"title": title}}}]

        body = {"requests": requests}
        result = (
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def delete_sheet(service, spreadsheet_id: str, sheet_id: int) -> dict[str, Any]:
    """Delete a sheet from a spreadsheet.

    Args:
        service: Google Sheets API service object.
        spreadsheet_id: The spreadsheet ID.
        sheet_id: The sheet ID (not the title).

    Returns:
        Batch update response from the API.

    Raises:
        SheetsAPIError: If the API call fails.
    """
    try:
        requests = [{"deleteSheet": {"sheetId": sheet_id}}]

        body = {"requests": requests}
        result = (
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_spreadsheet_summary(spreadsheet: dict[str, Any]) -> str:
    """Format a spreadsheet for display.

    Args:
        spreadsheet: Spreadsheet dictionary from Google Sheets API.

    Returns:
        Formatted string.
    """
    title = spreadsheet.get("properties", {}).get("title", "(Untitled)")
    spreadsheet_id = spreadsheet.get("spreadsheetId", "(Unknown)")
    sheets = spreadsheet.get("sheets", [])
    sheet_names = [s.get("properties", {}).get("title", "Unknown") for s in sheets]

    return (
        f"### {title}\n"
        f"- **Spreadsheet ID:** {spreadsheet_id}\n"
        f"- **Sheets:** {len(sheets)} ({', '.join(sheet_names)})\n"
        f"- **URL:** https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    )


def format_values_output(values: list[list[Any]]) -> str:
    """Format values for human-readable display.

    Args:
        values: 2D array of cell values.

    Returns:
        Formatted string.
    """
    if not values:
        return "(No data)"

    # Calculate column widths
    col_widths = []
    for col_idx in range(max(len(row) for row in values)):
        max_width = 0
        for row in values:
            if col_idx < len(row):
                max_width = max(max_width, len(str(row[col_idx])))
        col_widths.append(min(max_width, 30))  # Cap at 30 chars

    # Format rows
    lines = []
    for row in values:
        formatted_cells = []
        for col_idx, cell in enumerate(row):
            cell_str = str(cell) if cell else ""
            if len(cell_str) > 30:
                cell_str = cell_str[:27] + "..."
            formatted_cells.append(cell_str.ljust(col_widths[col_idx]))
        lines.append(" | ".join(formatted_cells))

    return "\n".join(lines)


# ============================================================================
# HEALTH CHECK
# ============================================================================


def check_sheets_connectivity() -> dict[str, Any]:
    """Check Google Sheets API connectivity and authentication.

    Returns:
        Dictionary with status information including available scopes.
    """
    result = {
        "authenticated": False,
        "scopes": None,
        "error": None,
    }

    try:
        # Get credentials to check scopes
        creds = get_google_credentials("google-sheets", SHEETS_SCOPES_DEFAULT)

        # Check which scopes are available
        available_scopes = []
        if hasattr(creds, "scopes"):
            available_scopes = creds.scopes
        elif hasattr(creds, "_scopes"):
            available_scopes = creds._scopes

        # Build service - if this works, we're authenticated
        service = build("sheets", "v4", credentials=creds)

        # Try a simple API call to verify connectivity
        # Create a test spreadsheet
        test_ss = (
            service.spreadsheets()
            .create(body={"properties": {"title": "_test_connectivity"}})
            .execute()
        )
        test_ss_id = test_ss.get("spreadsheetId")

        result["authenticated"] = True
        result["test_spreadsheet_id"] = test_ss_id
        result["scopes"] = {
            "readonly": any("spreadsheets.readonly" in s for s in available_scopes),
            "write": any("spreadsheets" in s and "readonly" not in s for s in available_scopes),
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
    print("Checking Google Sheets connectivity...")
    result = check_sheets_connectivity()

    if result["authenticated"]:
        print("✓ Successfully authenticated to Google Sheets")

        # Display scope information
        scopes = result.get("scopes", {})
        if scopes:
            print("\nGranted OAuth Scopes:")
            print(f"  Read-only (spreadsheets.readonly): {'✓' if scopes.get('readonly') else '✗'}")
            print(f"  Write (spreadsheets):               {'✓' if scopes.get('write') else '✗'}")

            # Check if write scope is granted
            if not scopes.get("write"):
                print("\n⚠️  Write scope not granted. Some operations will fail.")
                print("   To grant full access, reset and re-authenticate:")
                print()
                print("   1. Reset token: python scripts/google-sheets.py auth reset")
                print("   2. Re-run: python scripts/google-sheets.py check")
                print()
                print("   See: docs/google-oauth-setup.md")

        print(f"\nTest spreadsheet created: {result.get('test_spreadsheet_id')}")
        print("(You can delete this test spreadsheet from Google Drive)")
        return 0
    else:
        print(f"✗ Authentication failed: {result['error']}")
        print()
        print("Setup instructions:")
        print()
        print("  1. Set up a GCP project with OAuth credentials:")
        print("     See: docs/gcp-project-setup.md")
        print()
        print("  2. Configure your credentials:")
        print("     Create ~/.config/agent-skills/google.yaml:")
        print()
        print("     oauth_client:")
        print("       client_id: YOUR_CLIENT_ID.apps.googleusercontent.com")
        print("       client_secret: YOUR_CLIENT_SECRET")
        print()
        print("  3. Run check again to trigger OAuth flow:")
        print("     python scripts/google-sheets.py check")
        print()
        print("For detailed setup instructions, see: docs/google-oauth-setup.md")
        return 1


def cmd_auth_setup(args):
    """Handle 'auth setup' command."""
    if not args.client_id or not args.client_secret:
        print("Error: Both --client-id and --client-secret are required", file=sys.stderr)
        return 1

    config = load_config("google-sheets") or {}
    config["oauth_client"] = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
    }
    save_config("google-sheets", config)
    print("✓ OAuth client credentials saved to config file")
    print(f"  Config location: {CONFIG_DIR / 'google-sheets.yaml'}")
    print("\nNext step: Run any Google Sheets command to initiate OAuth flow")
    return 0


def cmd_auth_reset(_args):
    """Handle 'auth reset' command."""
    delete_credential("google-sheets-token-json")
    print("OAuth token cleared. Next command will trigger re-authentication.")
    return 0


def cmd_auth_status(_args):
    """Handle 'auth status' command."""
    token_json = get_credential("google-sheets-token-json")
    if not token_json:
        print("No OAuth token stored.")
        return 1

    try:
        token_data = json.loads(token_json)
    except json.JSONDecodeError:
        print("Stored token is corrupted.")
        return 1

    print("OAuth token is stored.")

    # Granted scopes
    scopes = token_data.get("scopes", [])
    if scopes:
        print("\nGranted scopes:")
        for scope in scopes:
            print(f"  - {scope}")
    else:
        print("\nGranted scopes: (unknown - legacy token)")

    # Refresh token
    has_refresh = bool(token_data.get("refresh_token"))
    print(f"\nRefresh token: {'present' if has_refresh else 'missing'}")

    # Expiry
    expiry = token_data.get("expiry")
    if expiry:
        print(f"Token expiry: {expiry}")

    # Client ID (truncated)
    client_id = token_data.get("client_id", "")
    if client_id:
        truncated = client_id[:16] + "..." if len(client_id) > 16 else client_id
        print(f"Client ID: {truncated}")

    return 0


def cmd_spreadsheets_create(args):
    """Handle 'spreadsheets create' command."""
    service = build_sheets_service(SHEETS_SCOPES)
    sheet_names = args.sheets.split(",") if args.sheets else None
    spreadsheet = create_spreadsheet(service, args.title, sheet_names)

    if args.json:
        print(json.dumps(spreadsheet, indent=2))
    else:
        print("✓ Spreadsheet created successfully")
        print(format_spreadsheet_summary(spreadsheet))

    return 0


def cmd_spreadsheets_get(args):
    """Handle 'spreadsheets get' command."""
    service = build_sheets_service(SHEETS_SCOPES_READONLY)
    spreadsheet = get_spreadsheet(service, args.spreadsheet_id)

    if args.json:
        print(json.dumps(spreadsheet, indent=2))
    else:
        print(format_spreadsheet_summary(spreadsheet))

    return 0


def cmd_values_read(args):
    """Handle 'values read' command."""
    service = build_sheets_service(SHEETS_SCOPES_READONLY)
    result = read_values(service, args.spreadsheet_id, args.range, args.format)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        values = result.get("values", [])
        if values:
            print(format_values_output(values))
        else:
            print("(No data found in range)")

    return 0


def cmd_values_write(args):
    """Handle 'values write' command."""
    service = build_sheets_service(SHEETS_SCOPES)

    # Parse JSON values
    try:
        values = json.loads(args.values)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON for --values: {e}", file=sys.stderr)
        return 1

    result = write_values(service, args.spreadsheet_id, args.range, values)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Values written successfully")
        print(f"  Updated cells: {result.get('updatedCells', 0)}")
        print(f"  Updated range: {result.get('updatedRange', 'N/A')}")

    return 0


def cmd_values_append(args):
    """Handle 'values append' command."""
    service = build_sheets_service(SHEETS_SCOPES)

    # Parse JSON values
    try:
        values = json.loads(args.values)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON for --values: {e}", file=sys.stderr)
        return 1

    result = append_values(service, args.spreadsheet_id, args.range, values)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        updates = result.get("updates", {})
        print("✓ Values appended successfully")
        print(f"  Updated cells: {updates.get('updatedCells', 0)}")
        print(f"  Updated range: {updates.get('updatedRange', 'N/A')}")

    return 0


def cmd_values_clear(args):
    """Handle 'values clear' command."""
    service = build_sheets_service(SHEETS_SCOPES)
    result = clear_values(service, args.spreadsheet_id, args.range)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Values cleared successfully")
        print(f"  Cleared range: {result.get('clearedRange', 'N/A')}")

    return 0


def cmd_sheets_create(args):
    """Handle 'sheets create' command."""
    service = build_sheets_service(SHEETS_SCOPES)
    result = create_sheet(service, args.spreadsheet_id, args.title)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Extract the new sheet info from the reply
        reply = result.get("replies", [{}])[0]
        new_sheet = reply.get("addSheet", {}).get("properties", {})
        print("✓ Sheet created successfully")
        print(f"  Title: {new_sheet.get('title', args.title)}")
        print(f"  Sheet ID: {new_sheet.get('sheetId', 'N/A')}")

    return 0


def cmd_sheets_delete(args):
    """Handle 'sheets delete' command."""
    service = build_sheets_service(SHEETS_SCOPES)
    result = delete_sheet(service, args.spreadsheet_id, args.sheet_id)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Sheet deleted successfully")

    return 0


# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Google Sheets integration for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check command
    subparsers.add_parser("check", help="Check Google Sheets connectivity and authentication")

    # auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    setup_parser = auth_subparsers.add_parser("setup", help="Setup OAuth client credentials")
    setup_parser.add_argument("--client-id", required=True, help="OAuth client ID")
    setup_parser.add_argument("--client-secret", required=True, help="OAuth client secret")

    auth_subparsers.add_parser("reset", help="Clear stored OAuth token")
    auth_subparsers.add_parser("status", help="Show current token info")

    # spreadsheets commands
    spreadsheets_parser = subparsers.add_parser("spreadsheets", help="Spreadsheet operations")
    spreadsheets_subparsers = spreadsheets_parser.add_subparsers(dest="spreadsheets_command")

    create_parser = spreadsheets_subparsers.add_parser("create", help="Create a new spreadsheet")
    create_parser.add_argument("--title", required=True, help="Spreadsheet title")
    create_parser.add_argument("--sheets", help="Comma-separated sheet names")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    get_parser = spreadsheets_subparsers.add_parser("get", help="Get spreadsheet metadata")
    get_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # values commands
    values_parser = subparsers.add_parser("values", help="Cell value operations")
    values_subparsers = values_parser.add_subparsers(dest="values_command")

    read_parser = values_subparsers.add_parser("read", help="Read cell values")
    read_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
    read_parser.add_argument(
        "--range", required=True, help="Range in A1 notation (e.g., Sheet1!A1:D5)"
    )
    read_parser.add_argument(
        "--format",
        choices=["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"],
        default="FORMATTED_VALUE",
        help="Value rendering format",
    )
    read_parser.add_argument("--json", action="store_true", help="Output as JSON")

    write_parser = values_subparsers.add_parser("write", help="Write values to cells")
    write_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
    write_parser.add_argument("--range", required=True, help="Range in A1 notation")
    write_parser.add_argument(
        "--values", required=True, help="Values as JSON array (e.g., [[1,2,3]])"
    )
    write_parser.add_argument("--json", action="store_true", help="Output as JSON")

    append_parser = values_subparsers.add_parser("append", help="Append rows to sheet")
    append_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
    append_parser.add_argument("--range", required=True, help="Sheet name or range")
    append_parser.add_argument(
        "--values", required=True, help="Values as JSON array (e.g., [[4,5,6]])"
    )
    append_parser.add_argument("--json", action="store_true", help="Output as JSON")

    clear_parser = values_subparsers.add_parser("clear", help="Clear cell values")
    clear_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
    clear_parser.add_argument("--range", required=True, help="Range in A1 notation")
    clear_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # sheets commands
    sheets_parser = subparsers.add_parser("sheets", help="Sheet management operations")
    sheets_subparsers = sheets_parser.add_subparsers(dest="sheets_command")

    sheets_create_parser = sheets_subparsers.add_parser("create", help="Add new sheet")
    sheets_create_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
    sheets_create_parser.add_argument("--title", required=True, help="Sheet title")
    sheets_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    sheets_delete_parser = sheets_subparsers.add_parser("delete", help="Delete a sheet")
    sheets_delete_parser.add_argument("spreadsheet_id", help="Spreadsheet ID")
    sheets_delete_parser.add_argument(
        "--sheet-id", type=int, required=True, help="Sheet ID to delete"
    )
    sheets_delete_parser.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main entry point."""
    # Check dependencies first (allows --help to work even if deps missing)
    parser = build_parser()
    args = parser.parse_args()

    # Now check dependencies if not just showing help
    if not GOOGLE_AUTH_AVAILABLE:
        print(
            "Error: Google auth libraries not found. Install with: "
            "pip install --user google-auth google-auth-oauthlib",
            file=sys.stderr,
        )
        return 1

    if not GOOGLE_API_CLIENT_AVAILABLE:
        print(
            "Error: 'google-api-python-client' not found. Install with: "
            "pip install --user google-api-python-client",
            file=sys.stderr,
        )
        return 1

    if not KEYRING_AVAILABLE:
        print(
            "Error: 'keyring' library not found. Install with: pip install --user keyring",
            file=sys.stderr,
        )
        return 1

    if not YAML_AVAILABLE:
        print(
            "Error: 'pyyaml' library not found. Install with: pip install --user pyyaml",
            file=sys.stderr,
        )
        return 1

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
            elif args.auth_command == "reset":
                return cmd_auth_reset(args)
            elif args.auth_command == "status":
                return cmd_auth_status(args)
        elif args.command == "spreadsheets":
            if args.spreadsheets_command == "create":
                return cmd_spreadsheets_create(args)
            elif args.spreadsheets_command == "get":
                return cmd_spreadsheets_get(args)
        elif args.command == "values":
            if args.values_command == "read":
                return cmd_values_read(args)
            elif args.values_command == "write":
                return cmd_values_write(args)
            elif args.values_command == "append":
                return cmd_values_append(args)
            elif args.values_command == "clear":
                return cmd_values_clear(args)
        elif args.command == "sheets":
            if args.sheets_command == "create":
                return cmd_sheets_create(args)
            elif args.sheets_command == "delete":
                return cmd_sheets_delete(args)

        parser.print_help()
        return 1

    except (SheetsAPIError, AuthenticationError) as e:
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
