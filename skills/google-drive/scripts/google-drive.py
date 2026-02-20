#!/usr/bin/env python3
"""Google Drive integration skill for AI agents.

This is a self-contained script that provides Google Drive functionality.

Usage:
    python google-drive.py check
    python google-drive.py auth setup --client-id ID --client-secret SECRET
    python google-drive.py files list --query "name contains 'report'" --max-results 10
    python google-drive.py files get FILE_ID
    python google-drive.py files download FILE_ID --output /path/to/file
    python google-drive.py files upload /path/to/file --parent FOLDER_ID
    python google-drive.py folders create "New Folder" --parent FOLDER_ID
    python google-drive.py share FILE_ID --email user@example.com --role writer
    python google-drive.py permissions list FILE_ID

Requirements:
    pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
"""

from __future__ import annotations

# Standard library imports
import argparse
import contextlib
import json
import mimetypes
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
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

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

# Google Drive API scopes - granular scopes for different operations
DRIVE_SCOPES_READONLY = ["https://www.googleapis.com/auth/drive.readonly"]
DRIVE_SCOPES_FILE = ["https://www.googleapis.com/auth/drive.file"]
DRIVE_SCOPES_METADATA = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

# Full scope set for maximum functionality
DRIVE_SCOPES_FULL = DRIVE_SCOPES_READONLY + DRIVE_SCOPES_FILE + DRIVE_SCOPES_METADATA

# Minimal read-only scope (default)
DRIVE_SCOPES_DEFAULT = DRIVE_SCOPES_READONLY

# Common MIME types
MIME_TYPE_FOLDER = "application/vnd.google-apps.folder"


# ============================================================================
# KEYRING CREDENTIAL STORAGE
# ============================================================================


def get_credential(key: str) -> str | None:
    """Get a credential from the system keyring.

    Args:
        key: The credential key (e.g., "google-drive-token-json").

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
        service: Service name (e.g., "google-drive").

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
        f"  1. Service config: Run python google-drive.py auth setup --client-id YOUR_ID --client-secret YOUR_SECRET\n"
        f"  2. Service env vars: Set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET\n"
        f"  3. Shared config: Create ~/.config/agent-skills/google.yaml with oauth_client credentials\n"
        f"  4. Shared env vars: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    )


def _run_oauth_flow(service: str, scopes: list[str]) -> Credentials:
    """Run OAuth browser flow and store resulting token.

    Args:
        service: Service name (e.g., "google-drive").
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
        service: Service name (e.g., "google-drive").
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


def build_drive_service(scopes: list[str] | None = None):
    """Build and return Google Drive API service.

    Args:
        scopes: List of OAuth scopes to request. Defaults to read-only.

    Returns:
        Google Drive API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    if scopes is None:
        scopes = DRIVE_SCOPES_DEFAULT
    creds = get_google_credentials("google-drive", scopes)
    return build("drive", "v3", credentials=creds)


# ============================================================================
# DRIVE API ERROR HANDLING
# ============================================================================


class DriveAPIError(Exception):
    """Exception raised for Google Drive API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def handle_api_error(error: HttpError) -> None:
    """Convert Google API HttpError to DriveAPIError.

    Args:
        error: HttpError from Google API.

    Raises:
        DriveAPIError: With appropriate message and status code.
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
            "  1. Reset token: python scripts/google-drive.py auth reset\n"
            "  2. Re-run: python scripts/google-drive.py check\n\n"
            "For setup help, see: docs/google-oauth-setup.md\n"
        )
        message = f"{message}{scope_help}"

    raise DriveAPIError(
        f"Drive API error: {message} (HTTP {status_code})",
        status_code=status_code,
        details=details,
    )


# ============================================================================
# FILE OPERATIONS
# ============================================================================


def list_files(
    service,
    query: str = "",
    max_results: int = 10,
    order_by: str = "modifiedTime desc",
) -> list[dict[str, Any]]:
    """List files in Google Drive.

    Args:
        service: Google Drive API service object.
        query: Drive search query (e.g., "name contains 'report'").
        max_results: Maximum number of files to return.
        order_by: Sort order (e.g., "modifiedTime desc", "name").

    Returns:
        List of file dictionaries.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        params: dict[str, Any] = {
            "pageSize": max_results,
            "fields": "files(id, name, mimeType, modifiedTime, size, owners, webViewLink)",
            "orderBy": order_by,
        }
        if query:
            params["q"] = query

        result = service.files().list(**params).execute()
        files = result.get("files", [])
        return files
    except HttpError as e:
        handle_api_error(e)
        return []  # Unreachable, but satisfies type checker


def search_files(
    service,
    name: str = "",
    mime_type: str = "",
    folder_id: str = "",
) -> list[dict[str, Any]]:
    """Search for files in Google Drive.

    Args:
        service: Google Drive API service object.
        name: File name to search for (partial match).
        mime_type: MIME type to filter by.
        folder_id: Parent folder ID to search within.

    Returns:
        List of matching file dictionaries.

    Raises:
        DriveAPIError: If the API call fails.
    """
    query_parts = []
    if name:
        query_parts.append(f"name contains '{name}'")
    if mime_type:
        query_parts.append(f"mimeType = '{mime_type}'")
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")

    # Exclude trashed files
    query_parts.append("trashed = false")

    query = " and ".join(query_parts)
    return list_files(service, query=query)


def get_file_metadata(service, file_id: str) -> dict[str, Any]:
    """Get metadata for a file.

    Args:
        service: Google Drive API service object.
        file_id: The file ID.

    Returns:
        File metadata dictionary.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        file = (
            service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, createdTime, size, owners, webViewLink, parents, description",
            )
            .execute()
        )
        return file
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def download_file(service, file_id: str, output_path: str) -> None:
    """Download a file from Google Drive.

    Args:
        service: Google Drive API service object.
        file_id: The file ID to download.
        output_path: Local path to save the file.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        request = service.files().get_media(fileId=file_id)
        with open(output_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
    except HttpError as e:
        handle_api_error(e)


def upload_file(
    service,
    file_path: str,
    parent_folder_id: str | None = None,
    mime_type: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Upload a file to Google Drive.

    Args:
        service: Google Drive API service object.
        file_path: Local path of file to upload.
        parent_folder_id: Parent folder ID (optional).
        mime_type: MIME type of the file (auto-detected if not provided).
        name: Name for the file in Drive (uses local filename if not provided).

    Returns:
        Created file metadata dictionary.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise DriveAPIError(f"File not found: {file_path}")

        file_name = name or path.name
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"

        file_metadata: dict[str, Any] = {"name": file_name}
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, mimeType, modifiedTime, size, webViewLink",
            )
            .execute()
        )
        return file
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# FOLDER OPERATIONS
# ============================================================================


def create_folder(
    service,
    name: str,
    parent_folder_id: str | None = None,
) -> dict[str, Any]:
    """Create a folder in Google Drive.

    Args:
        service: Google Drive API service object.
        name: Folder name.
        parent_folder_id: Parent folder ID (optional).

    Returns:
        Created folder metadata dictionary.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        file_metadata: dict[str, Any] = {
            "name": name,
            "mimeType": MIME_TYPE_FOLDER,
        }
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        folder = (
            service.files()
            .create(
                body=file_metadata,
                fields="id, name, mimeType, modifiedTime, webViewLink",
            )
            .execute()
        )
        return folder
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def list_folder_contents(
    service,
    folder_id: str,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """List contents of a folder.

    Args:
        service: Google Drive API service object.
        folder_id: The folder ID.
        max_results: Maximum number of items to return.

    Returns:
        List of file/folder dictionaries.

    Raises:
        DriveAPIError: If the API call fails.
    """
    query = f"'{folder_id}' in parents and trashed = false"
    return list_files(service, query=query, max_results=max_results)


# ============================================================================
# SHARING OPERATIONS
# ============================================================================


def share_file(
    service,
    file_id: str,
    email: str,
    role: str = "reader",
    notify: bool = True,
) -> dict[str, Any]:
    """Share a file with a user.

    Args:
        service: Google Drive API service object.
        file_id: The file ID to share.
        email: Email address of the user to share with.
        role: Permission role (reader, writer, commenter, owner).
        notify: Whether to send an email notification.

    Returns:
        Created permission dictionary.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        permission = {
            "type": "user",
            "role": role,
            "emailAddress": email,
        }
        result = (
            service.permissions()
            .create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=notify,
                fields="id, type, role, emailAddress",
            )
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def list_permissions(service, file_id: str) -> list[dict[str, Any]]:
    """List permissions for a file.

    Args:
        service: Google Drive API service object.
        file_id: The file ID.

    Returns:
        List of permission dictionaries.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        result = (
            service.permissions()
            .list(
                fileId=file_id,
                fields="permissions(id, type, role, emailAddress, displayName)",
            )
            .execute()
        )
        permissions = result.get("permissions", [])
        return permissions
    except HttpError as e:
        handle_api_error(e)
        return []  # Unreachable


def delete_permission(service, file_id: str, permission_id: str) -> None:
    """Delete a permission from a file.

    Args:
        service: Google Drive API service object.
        file_id: The file ID.
        permission_id: The permission ID to delete.

    Raises:
        DriveAPIError: If the API call fails.
    """
    try:
        service.permissions().delete(fileId=file_id, permissionId=permission_id).execute()
    except HttpError as e:
        handle_api_error(e)


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_file_summary(file: dict[str, Any]) -> str:
    """Format a file for display.

    Args:
        file: File dictionary from Drive API.

    Returns:
        Formatted string.
    """
    name = file.get("name", "(Unknown)")
    file_id = file.get("id", "(Unknown)")
    mime_type = file.get("mimeType", "(Unknown)")
    modified = file.get("modifiedTime", "(Unknown)")
    size = file.get("size", "N/A")
    link = file.get("webViewLink", "")

    # Format size
    if size != "N/A" and size:
        size_int = int(size)
        if size_int >= 1024 * 1024 * 1024:
            size = f"{size_int / (1024 * 1024 * 1024):.1f} GB"
        elif size_int >= 1024 * 1024:
            size = f"{size_int / (1024 * 1024):.1f} MB"
        elif size_int >= 1024:
            size = f"{size_int / 1024:.1f} KB"
        else:
            size = f"{size_int} B"

    # Indicate if it's a folder
    if mime_type == MIME_TYPE_FOLDER:
        type_indicator = "[Folder]"
        size = "-"
    else:
        type_indicator = ""

    return f"""ID: {file_id}
Name: {name} {type_indicator}
Type: {mime_type}
Size: {size}
Modified: {modified}
Link: {link}"""


def format_permission(permission: dict[str, Any]) -> str:
    """Format a permission for display.

    Args:
        permission: Permission dictionary from Drive API.

    Returns:
        Formatted string.
    """
    perm_type = permission.get("type", "(Unknown)")
    role = permission.get("role", "(Unknown)")
    email = permission.get("emailAddress", "")
    display_name = permission.get("displayName", "")
    perm_id = permission.get("id", "(Unknown)")

    user_info = display_name or email or perm_type
    return f"{user_info} ({role}) - ID: {perm_id}"


# ============================================================================
# HEALTH CHECK
# ============================================================================


def check_drive_connectivity() -> dict[str, Any]:
    """Check Google Drive API connectivity and authentication.

    Returns:
        Dictionary with status information including available scopes.
    """
    result = {
        "authenticated": False,
        "storage": None,
        "scopes": None,
        "error": None,
    }

    try:
        # Get credentials to check scopes
        creds = get_google_credentials("google-drive", DRIVE_SCOPES_DEFAULT)

        # Check which scopes are available
        available_scopes = []
        if hasattr(creds, "scopes"):
            available_scopes = creds.scopes
        elif hasattr(creds, "_scopes"):
            available_scopes = creds._scopes

        # Build service and get about info
        service = build("drive", "v3", credentials=creds)
        about = service.about().get(fields="user, storageQuota").execute()

        result["authenticated"] = True
        result["storage"] = {
            "email": about.get("user", {}).get("emailAddress"),
            "display_name": about.get("user", {}).get("displayName"),
            "usage": about.get("storageQuota", {}).get("usage"),
            "limit": about.get("storageQuota", {}).get("limit"),
        }
        result["scopes"] = {
            "readonly": any("drive.readonly" in s for s in available_scopes),
            "file": any("drive.file" in s for s in available_scopes),
            "metadata": any("drive.metadata" in s for s in available_scopes),
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
    print("Checking Google Drive connectivity...")
    result = check_drive_connectivity()

    if result["authenticated"]:
        print("Successfully authenticated to Google Drive")
        storage = result["storage"]
        print(f"  Email: {storage['email']}")
        print(f"  Name: {storage['display_name']}")

        # Display storage info
        usage = storage.get("usage")
        limit = storage.get("limit")
        if usage and limit:
            usage_gb = int(usage) / (1024 * 1024 * 1024)
            limit_gb = int(limit) / (1024 * 1024 * 1024)
            print(f"  Storage: {usage_gb:.2f} GB / {limit_gb:.2f} GB")

        # Display scope information
        scopes = result.get("scopes", {})
        if scopes:
            print("\nGranted OAuth Scopes:")
            print(f"  Read-only (drive.readonly):    {'Yes' if scopes.get('readonly') else 'No'}")
            print(f"  File access (drive.file):      {'Yes' if scopes.get('file') else 'No'}")
            print(f"  Metadata (drive.metadata):     {'Yes' if scopes.get('metadata') else 'No'}")

            # Check if all scopes are granted
            all_granted = all(
                [
                    scopes.get("readonly"),
                    scopes.get("file"),
                    scopes.get("metadata"),
                ]
            )

            if not all_granted:
                print("\n⚠️  Not all scopes are granted. Some operations may fail.")
                print("   To grant full access, reset and re-authenticate:")
                print()
                print("   1. Reset token: python scripts/google-drive.py auth reset")
                print("   2. Re-run: python scripts/google-drive.py check")
                print()
                print("   See: docs/google-oauth-setup.md")
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
        print("     python scripts/google-drive.py check")
        print()
        print("For detailed setup instructions, see: docs/google-oauth-setup.md")
        return 1


def cmd_auth_setup(args):
    """Handle 'auth setup' command."""
    if not args.client_id or not args.client_secret:
        print("Error: Both --client-id and --client-secret are required", file=sys.stderr)
        return 1

    config = load_config("google-drive") or {}
    config["oauth_client"] = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
    }
    save_config("google-drive", config)
    print("OAuth client credentials saved to config file")
    print(f"  Config location: {CONFIG_DIR / 'google-drive.yaml'}")
    print("\nNext step: Run any Google Drive command to initiate OAuth flow")
    return 0


def cmd_auth_reset(_args):
    """Handle 'auth reset' command."""
    delete_credential("google-drive-token-json")
    print("OAuth token cleared. Next command will trigger re-authentication.")
    return 0


def cmd_auth_status(_args):
    """Handle 'auth status' command."""
    token_json = get_credential("google-drive-token-json")
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


def cmd_files_list(args):
    """Handle 'files list' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY)
    files = list_files(
        service,
        query=args.query or "",
        max_results=args.max_results,
        order_by=args.order_by or "modifiedTime desc",
    )

    if args.json:
        print(json.dumps(files, indent=2))
    else:
        if not files:
            print("No files found")
        else:
            print(f"Found {len(files)} file(s):\n")
            for f in files:
                print(format_file_summary(f))
                print("-" * 80)

    return 0


def cmd_files_search(args):
    """Handle 'files search' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY)
    files = search_files(
        service,
        name=args.name or "",
        mime_type=args.mime_type or "",
        folder_id=args.folder or "",
    )

    if args.json:
        print(json.dumps(files, indent=2))
    else:
        if not files:
            print("No files found matching criteria")
        else:
            print(f"Found {len(files)} file(s):\n")
            for f in files:
                print(format_file_summary(f))
                print("-" * 80)

    return 0


def cmd_files_get(args):
    """Handle 'files get' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY)
    file = get_file_metadata(service, args.file_id)

    if args.json:
        print(json.dumps(file, indent=2))
    else:
        print(format_file_summary(file))

    return 0


def cmd_files_download(args):
    """Handle 'files download' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY)

    # Get file metadata first to show name
    file = get_file_metadata(service, args.file_id)

    # Check if it's a Google Doc type (needs export)
    if file.get("mimeType", "").startswith("application/vnd.google-apps"):
        print(
            f"Error: Cannot download Google {file.get('mimeType')} directly. "
            "Use Google Drive web interface to export.",
            file=sys.stderr,
        )
        return 1

    print(f"Downloading '{file.get('name')}'...")
    download_file(service, args.file_id, args.output)
    print(f"Saved to: {args.output}")
    return 0


def cmd_files_upload(args):
    """Handle 'files upload' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY + DRIVE_SCOPES_FILE)
    result = upload_file(
        service,
        file_path=args.path,
        parent_folder_id=args.parent,
        mime_type=args.mime_type,
        name=args.name,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("File uploaded successfully")
        print(f"  ID: {result.get('id')}")
        print(f"  Name: {result.get('name')}")
        print(f"  Link: {result.get('webViewLink')}")

    return 0


def cmd_folders_create(args):
    """Handle 'folders create' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY + DRIVE_SCOPES_FILE)
    result = create_folder(service, name=args.name, parent_folder_id=args.parent)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Folder created successfully")
        print(f"  ID: {result.get('id')}")
        print(f"  Name: {result.get('name')}")
        print(f"  Link: {result.get('webViewLink')}")

    return 0


def cmd_folders_list(args):
    """Handle 'folders list' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY)
    files = list_folder_contents(service, folder_id=args.folder_id, max_results=args.max_results)

    if args.json:
        print(json.dumps(files, indent=2))
    else:
        if not files:
            print("Folder is empty")
        else:
            print(f"Found {len(files)} item(s):\n")
            for f in files:
                print(format_file_summary(f))
                print("-" * 80)

    return 0


def cmd_share(args):
    """Handle 'share' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY + DRIVE_SCOPES_FILE)
    result = share_file(
        service,
        file_id=args.file_id,
        email=args.email,
        role=args.role,
        notify=not args.no_notify,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("File shared successfully")
        print(f"  Email: {result.get('emailAddress')}")
        print(f"  Role: {result.get('role')}")

    return 0


def cmd_permissions_list(args):
    """Handle 'permissions list' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY)
    permissions = list_permissions(service, args.file_id)

    if args.json:
        print(json.dumps(permissions, indent=2))
    else:
        if not permissions:
            print("No permissions found")
        else:
            print(f"Found {len(permissions)} permission(s):\n")
            for perm in permissions:
                print(format_permission(perm))

    return 0


def cmd_permissions_delete(args):
    """Handle 'permissions delete' command."""
    service = build_drive_service(DRIVE_SCOPES_READONLY + DRIVE_SCOPES_FILE)
    delete_permission(service, args.file_id, args.permission_id)
    print("Permission deleted successfully")
    return 0


# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Google Drive integration for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check command
    subparsers.add_parser("check", help="Check Google Drive connectivity and authentication")

    # auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    setup_parser = auth_subparsers.add_parser("setup", help="Setup OAuth client credentials")
    setup_parser.add_argument("--client-id", required=True, help="OAuth client ID")
    setup_parser.add_argument("--client-secret", required=True, help="OAuth client secret")

    auth_subparsers.add_parser("reset", help="Clear stored OAuth token")
    auth_subparsers.add_parser("status", help="Show current token info")

    # files commands
    files_parser = subparsers.add_parser("files", help="File operations")
    files_subparsers = files_parser.add_subparsers(dest="files_command")

    list_parser = files_subparsers.add_parser("list", help="List files")
    list_parser.add_argument("--query", help="Drive search query")
    list_parser.add_argument("--max-results", type=int, default=10, help="Maximum results")
    list_parser.add_argument("--order-by", help="Sort order (e.g., 'modifiedTime desc')")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    search_parser = files_subparsers.add_parser("search", help="Search files")
    search_parser.add_argument("--name", help="File name to search for")
    search_parser.add_argument("--mime-type", help="MIME type filter")
    search_parser.add_argument("--folder", help="Parent folder ID")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    get_parser = files_subparsers.add_parser("get", help="Get file metadata")
    get_parser.add_argument("file_id", help="File ID")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    download_parser = files_subparsers.add_parser("download", help="Download a file")
    download_parser.add_argument("file_id", help="File ID")
    download_parser.add_argument("--output", "-o", required=True, help="Output file path")

    upload_parser = files_subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument("path", help="Local file path")
    upload_parser.add_argument("--parent", help="Parent folder ID")
    upload_parser.add_argument("--mime-type", help="MIME type (auto-detected if not provided)")
    upload_parser.add_argument("--name", help="Name for the file in Drive")
    upload_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # folders commands
    folders_parser = subparsers.add_parser("folders", help="Folder operations")
    folders_subparsers = folders_parser.add_subparsers(dest="folders_command")

    create_folder_parser = folders_subparsers.add_parser("create", help="Create a folder")
    create_folder_parser.add_argument("name", help="Folder name")
    create_folder_parser.add_argument("--parent", help="Parent folder ID")
    create_folder_parser.add_argument("--json", action="store_true", help="Output as JSON")

    list_folder_parser = folders_subparsers.add_parser("list", help="List folder contents")
    list_folder_parser.add_argument("folder_id", help="Folder ID")
    list_folder_parser.add_argument("--max-results", type=int, default=100, help="Maximum results")
    list_folder_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # share command
    share_parser = subparsers.add_parser("share", help="Share a file")
    share_parser.add_argument("file_id", help="File ID to share")
    share_parser.add_argument("--email", required=True, help="Email address to share with")
    share_parser.add_argument(
        "--role",
        choices=["reader", "writer", "commenter", "owner"],
        default="reader",
        help="Permission role",
    )
    share_parser.add_argument(
        "--no-notify", action="store_true", help="Don't send notification email"
    )
    share_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # permissions commands
    permissions_parser = subparsers.add_parser("permissions", help="Permission operations")
    permissions_subparsers = permissions_parser.add_subparsers(dest="permissions_command")

    perm_list_parser = permissions_subparsers.add_parser("list", help="List permissions")
    perm_list_parser.add_argument("file_id", help="File ID")
    perm_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    perm_delete_parser = permissions_subparsers.add_parser("delete", help="Delete a permission")
    perm_delete_parser.add_argument("file_id", help="File ID")
    perm_delete_parser.add_argument("permission_id", help="Permission ID to delete")

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
        elif args.command == "files":
            if args.files_command == "list":
                return cmd_files_list(args)
            elif args.files_command == "search":
                return cmd_files_search(args)
            elif args.files_command == "get":
                return cmd_files_get(args)
            elif args.files_command == "download":
                return cmd_files_download(args)
            elif args.files_command == "upload":
                return cmd_files_upload(args)
        elif args.command == "folders":
            if args.folders_command == "create":
                return cmd_folders_create(args)
            elif args.folders_command == "list":
                return cmd_folders_list(args)
        elif args.command == "share":
            return cmd_share(args)
        elif args.command == "permissions":
            if args.permissions_command == "list":
                return cmd_permissions_list(args)
            elif args.permissions_command == "delete":
                return cmd_permissions_delete(args)

        parser.print_help()
        return 1

    except (DriveAPIError, AuthenticationError) as e:
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
