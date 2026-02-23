#!/usr/bin/env python3
"""Google Docs integration skill for AI agents.

This is a self-contained script that provides Google Docs functionality.

Usage:
    python google-docs.py check
    python google-docs.py auth setup --client-id ID --client-secret SECRET
    python google-docs.py documents create --title "My Document"
    python google-docs.py documents get DOCUMENT_ID
    python google-docs.py documents read DOCUMENT_ID
    python google-docs.py content append DOCUMENT_ID --text "Hello World"
    python google-docs.py content insert DOCUMENT_ID --text "Insert this" --index 1
    python google-docs.py content delete DOCUMENT_ID --start-index 1 --end-index 10

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

# Google Docs API scopes - granular scopes for different operations
DOCS_SCOPES_READONLY = ["https://www.googleapis.com/auth/documents.readonly"]
DOCS_SCOPES = ["https://www.googleapis.com/auth/documents"]

# Drive API scope needed for markdown export
DRIVE_SCOPES_READONLY = ["https://www.googleapis.com/auth/drive.readonly"]

# Minimal read-only scope (default)
DOCS_SCOPES_DEFAULT = DOCS_SCOPES_READONLY


# ============================================================================
# KEYRING CREDENTIAL STORAGE
# ============================================================================


def get_credential(key: str) -> str | None:
    """Get a credential from the system keyring.

    Args:
        key: The credential key (e.g., "google-docs-token-json").

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
        service: Service name (e.g., "google-docs").

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
        f"  1. Service config: Run python google-docs.py auth setup --client-id YOUR_ID --client-secret YOUR_SECRET\n"
        f"  2. Service env vars: Set GOOGLE_DOCS_CLIENT_ID and GOOGLE_DOCS_CLIENT_SECRET\n"
        f"  3. Shared config: Create ~/.config/agent-skills/google.yaml with oauth_client credentials\n"
        f"  4. Shared env vars: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    )


def _run_oauth_flow(service: str, scopes: list[str]) -> Credentials:
    """Run OAuth browser flow and store resulting token.

    Args:
        service: Service name (e.g., "google-docs").
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
        service: Service name (e.g., "google-docs").
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


def build_docs_service(scopes: list[str] | None = None):
    """Build and return Google Docs API service.

    Args:
        scopes: List of OAuth scopes to request. Defaults to read-only.

    Returns:
        Google Docs API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    if scopes is None:
        scopes = DOCS_SCOPES_DEFAULT
    creds = get_google_credentials("google-docs", scopes)
    return build("docs", "v1", credentials=creds)


def build_drive_service(scopes: list[str] | None = None):
    """Build and return Google Drive API service for export operations.

    Args:
        scopes: List of OAuth scopes to request. Defaults to drive.readonly.

    Returns:
        Google Drive API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    if scopes is None:
        scopes = DRIVE_SCOPES_READONLY
    creds = get_google_credentials("google-docs", scopes)
    return build("drive", "v3", credentials=creds)


# ============================================================================
# GOOGLE DOCS API ERROR HANDLING
# ============================================================================


class DocsAPIError(Exception):
    """Exception raised for Google Docs API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def handle_api_error(error: HttpError) -> None:
    """Convert Google API HttpError to DocsAPIError.

    Args:
        error: HttpError from Google API.

    Raises:
        DocsAPIError: With appropriate message and status code.
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
            "  1. Reset token: python scripts/google-docs.py auth reset\n"
            "  2. Re-run: python scripts/google-docs.py check\n\n"
            "For setup help, see: docs/google-oauth-setup.md\n"
        )
        message = f"{message}{scope_help}"

    raise DocsAPIError(
        f"Google Docs API error: {message} (HTTP {status_code})",
        status_code=status_code,
        details=details,
    )


# ============================================================================
# DOCUMENT OPERATIONS
# ============================================================================


def create_document(service, title: str) -> dict[str, Any]:
    """Create a new blank Google Doc.

    Args:
        service: Google Docs API service object.
        title: Document title.

    Returns:
        Created document dictionary with documentId.

    Raises:
        DocsAPIError: If the API call fails.
    """
    try:
        body = {"title": title}
        doc = service.documents().create(body=body).execute()
        return doc
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def get_document(service, document_id: str) -> dict[str, Any]:
    """Get a Google Doc by ID.

    Args:
        service: Google Docs API service object.
        document_id: The document ID.

    Returns:
        Document dictionary with full content and metadata.

    Raises:
        DocsAPIError: If the API call fails.
    """
    try:
        doc = service.documents().get(documentId=document_id).execute()
        return doc
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def read_document_content(service, document_id: str) -> str:
    """Extract plain text content from a Google Doc.

    Args:
        service: Google Docs API service object.
        document_id: The document ID.

    Returns:
        Plain text content of the document.

    Raises:
        DocsAPIError: If the API call fails.
    """
    doc = get_document(service, document_id)
    content = doc.get("body", {}).get("content", [])

    text_parts = []
    for element in content:
        if "paragraph" in element:
            para = element["paragraph"]
            for text_element in para.get("elements", []):
                if "textRun" in text_element:
                    text_parts.append(text_element["textRun"].get("content", ""))

    return "".join(text_parts)


def export_document_as_markdown(document_id: str) -> str:
    """Export document as markdown using Google's native export.

    Uses the Drive API to export the document in markdown format.
    This preserves tables, headings, formatting, and structure.

    Args:
        document_id: The Google Docs document ID.

    Returns:
        Markdown content of the document.

    Raises:
        DocsAPIError: If the export fails.
    """
    try:
        service = build_drive_service()
        # Export using Drive API with markdown MIME type
        response = service.files().export(fileId=document_id, mimeType="text/markdown").execute()

        # Response is bytes, decode to string
        if isinstance(response, bytes):
            return response.decode("utf-8")
        return response
    except HttpError as e:
        handle_api_error(e)
        return ""  # Unreachable


def export_document_as_pdf(document_id: str) -> bytes:
    """Export document as PDF using Google's native export.

    Uses the Drive API to export the document in PDF format.

    Args:
        document_id: The Google Docs document ID.

    Returns:
        PDF content as bytes.

    Raises:
        DocsAPIError: If the export fails.
    """
    try:
        service = build_drive_service()
        response = service.files().export(fileId=document_id, mimeType="application/pdf").execute()
        return response
    except HttpError as e:
        handle_api_error(e)
        return b""  # Unreachable


def append_text(service, document_id: str, text: str) -> dict[str, Any]:
    """Append text to the end of a Google Doc.

    Args:
        service: Google Docs API service object.
        document_id: The document ID.
        text: Text to append.

    Returns:
        Response from the batchUpdate API.

    Raises:
        DocsAPIError: If the API call fails.
    """
    try:
        # Get document to find the end index
        doc = get_document(service, document_id)
        end_index = doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1)

        # Insert text at the end (end_index - 1 because last char is always \n)
        requests = [
            {
                "insertText": {
                    "location": {"index": end_index - 1},
                    "text": text,
                }
            }
        ]

        result = (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def insert_text(service, document_id: str, text: str, index: int) -> dict[str, Any]:
    """Insert text at a specific position in a Google Doc.

    Args:
        service: Google Docs API service object.
        document_id: The document ID.
        text: Text to insert.
        index: Position to insert at (0-based).

    Returns:
        Response from the batchUpdate API.

    Raises:
        DocsAPIError: If the API call fails.
    """
    try:
        requests = [
            {
                "insertText": {
                    "location": {"index": index},
                    "text": text,
                }
            }
        ]

        result = (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def delete_content(service, document_id: str, start_index: int, end_index: int) -> dict[str, Any]:
    """Delete a range of content from a Google Doc.

    Args:
        service: Google Docs API service object.
        document_id: The document ID.
        start_index: Start position (inclusive).
        end_index: End position (exclusive).

    Returns:
        Response from the batchUpdate API.

    Raises:
        DocsAPIError: If the API call fails.
    """
    try:
        requests = [
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index,
                    }
                }
            }
        ]

        result = (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def apply_formatting(
    service,
    document_id: str,
    start_index: int,
    end_index: int,
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    font_size: int | None = None,
) -> dict[str, Any]:
    """Apply text formatting to a range in a Google Doc.

    Args:
        service: Google Docs API service object.
        document_id: The document ID.
        start_index: Start position (inclusive).
        end_index: End position (exclusive).
        bold: Apply bold formatting.
        italic: Apply italic formatting.
        underline: Apply underline formatting.
        font_size: Font size in points.

    Returns:
        Response from the batchUpdate API.

    Raises:
        DocsAPIError: If the API call fails.
    """
    try:
        text_style = {}
        fields = []

        if bold is not None:
            text_style["bold"] = bold
            fields.append("bold")
        if italic is not None:
            text_style["italic"] = italic
            fields.append("italic")
        if underline is not None:
            text_style["underline"] = underline
            fields.append("underline")
        if font_size is not None:
            text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
            fields.append("fontSize")

        if not fields:
            return {}

        requests = [
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index,
                    },
                    "textStyle": text_style,
                    "fields": ",".join(fields),
                }
            }
        ]

        result = (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_document_summary(doc: dict[str, Any]) -> str:
    """Format a document for display.

    Args:
        doc: Document dictionary from Google Docs API.

    Returns:
        Formatted string.
    """
    title = doc.get("title", "(Untitled)")
    doc_id = doc.get("documentId", "(Unknown)")

    # Count content elements
    content = doc.get("body", {}).get("content", [])
    char_count = 0
    for element in content:
        if "paragraph" in element:
            for text_element in element["paragraph"].get("elements", []):
                if "textRun" in text_element:
                    char_count += len(text_element["textRun"].get("content", ""))

    return (
        f"### {title}\n"
        f"- **Document ID:** {doc_id}\n"
        f"- **Characters:** {char_count}\n"
        f"- **Revision ID:** {doc.get('revisionId', 'N/A')}"
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================


def check_docs_connectivity() -> dict[str, Any]:
    """Check Google Docs API connectivity and authentication.

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
        creds = get_google_credentials("google-docs", DOCS_SCOPES_DEFAULT)

        # Check which scopes are available
        available_scopes = []
        if hasattr(creds, "scopes"):
            available_scopes = creds.scopes
        elif hasattr(creds, "_scopes"):
            available_scopes = creds._scopes

        # Build service - if this works, we're authenticated
        service = build("docs", "v1", credentials=creds)

        # Try a simple API call to verify connectivity
        # We'll create a test document and immediately get it to verify
        test_doc = service.documents().create(body={"title": "_test_connectivity"}).execute()
        test_doc_id = test_doc.get("documentId")

        result["authenticated"] = True
        result["test_document_id"] = test_doc_id
        result["scopes"] = {
            "readonly": any("documents.readonly" in s for s in available_scopes),
            "write": any("documents" in s and "readonly" not in s for s in available_scopes),
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
    print("Checking Google Docs connectivity...")
    result = check_docs_connectivity()

    if result["authenticated"]:
        print("✓ Successfully authenticated to Google Docs")

        # Display scope information
        scopes = result.get("scopes", {})
        if scopes:
            print("\nGranted OAuth Scopes:")
            print(f"  Read-only (documents.readonly): {'✓' if scopes.get('readonly') else '✗'}")
            print(f"  Write (documents):               {'✓' if scopes.get('write') else '✗'}")

            # Check if write scope is granted
            if not scopes.get("write"):
                print("\n⚠️  Write scope not granted. Some operations will fail.")
                print("   To grant full access, reset and re-authenticate:")
                print()
                print("   1. Reset token: python scripts/google-docs.py auth reset")
                print("   2. Re-run: python scripts/google-docs.py check")
                print()
                print("   See: docs/google-oauth-setup.md")

        print(f"\nTest document created: {result.get('test_document_id')}")
        print("(You can delete this test document from Google Drive)")
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
        print("     python scripts/google-docs.py check")
        print()
        print("For detailed setup instructions, see: docs/google-oauth-setup.md")
        return 1


def cmd_auth_setup(args):
    """Handle 'auth setup' command."""
    if not args.client_id or not args.client_secret:
        print("Error: Both --client-id and --client-secret are required", file=sys.stderr)
        return 1

    config = load_config("google-docs") or {}
    config["oauth_client"] = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
    }
    save_config("google-docs", config)
    print("✓ OAuth client credentials saved to config file")
    print(f"  Config location: {CONFIG_DIR / 'google-docs.yaml'}")
    print("\nNext step: Run any Google Docs command to initiate OAuth flow")
    return 0


def cmd_auth_reset(_args):
    """Handle 'auth reset' command."""
    delete_credential("google-docs-token-json")
    print("OAuth token cleared. Next command will trigger re-authentication.")
    return 0


def cmd_auth_status(_args):
    """Handle 'auth status' command."""
    token_json = get_credential("google-docs-token-json")
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


def cmd_documents_create(args):
    """Handle 'documents create' command."""
    service = build_docs_service(DOCS_SCOPES)
    doc = create_document(service, args.title)

    if args.json:
        print(json.dumps(doc, indent=2))
    else:
        print("✓ Document created successfully")
        print(f"  Title: {doc.get('title')}")
        print(f"  Document ID: {doc.get('documentId')}")
        print(f"  URL: https://docs.google.com/document/d/{doc.get('documentId')}/edit")

    return 0


def cmd_documents_get(args):
    """Handle 'documents get' command."""
    service = build_docs_service(DOCS_SCOPES_READONLY)
    doc = get_document(service, args.document_id)

    if args.json:
        print(json.dumps(doc, indent=2))
    else:
        print(format_document_summary(doc))

    return 0


def cmd_documents_read(args):
    """Handle 'documents read' command."""
    if args.format == "pdf":
        content = export_document_as_pdf(args.document_id)
        output_file = args.output or f"{args.document_id}.pdf"
        with open(output_file, "wb") as f:
            f.write(content)
        print(f"PDF saved to: {output_file}")
        return 0
    elif args.format == "markdown":
        content = export_document_as_markdown(args.document_id)
    else:
        service = build_docs_service(DOCS_SCOPES_READONLY)
        content = read_document_content(service, args.document_id)

    if args.json:
        print(json.dumps({"content": content}, indent=2))
    else:
        print(content)

    return 0


def cmd_content_append(args):
    """Handle 'content append' command."""
    service = build_docs_service(DOCS_SCOPES)
    result = append_text(service, args.document_id, args.text)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Text appended successfully")

    return 0


def cmd_content_insert(args):
    """Handle 'content insert' command."""
    service = build_docs_service(DOCS_SCOPES)
    result = insert_text(service, args.document_id, args.text, args.index)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Text inserted successfully")

    return 0


def cmd_content_delete(args):
    """Handle 'content delete' command."""
    service = build_docs_service(DOCS_SCOPES)
    result = delete_content(service, args.document_id, args.start_index, args.end_index)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Content deleted successfully")

    return 0


def cmd_formatting_apply(args):
    """Handle 'formatting apply' command."""
    service = build_docs_service(DOCS_SCOPES)
    result = apply_formatting(
        service,
        args.document_id,
        args.start_index,
        args.end_index,
        bold=args.bold,
        italic=args.italic,
        underline=args.underline,
        font_size=args.font_size,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Formatting applied successfully")

    return 0


# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Google Docs integration for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check command
    subparsers.add_parser("check", help="Check Google Docs connectivity and authentication")

    # auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    setup_parser = auth_subparsers.add_parser("setup", help="Setup OAuth client credentials")
    setup_parser.add_argument("--client-id", required=True, help="OAuth client ID")
    setup_parser.add_argument("--client-secret", required=True, help="OAuth client secret")

    auth_subparsers.add_parser("reset", help="Clear stored OAuth token")
    auth_subparsers.add_parser("status", help="Show current token info")

    # documents commands
    documents_parser = subparsers.add_parser("documents", help="Document operations")
    documents_subparsers = documents_parser.add_subparsers(dest="documents_command")

    create_parser = documents_subparsers.add_parser("create", help="Create a new document")
    create_parser.add_argument("--title", required=True, help="Document title")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    get_parser = documents_subparsers.add_parser("get", help="Get document metadata")
    get_parser.add_argument("document_id", help="Document ID")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    read_parser = documents_subparsers.add_parser("read", help="Read document content as text")
    read_parser.add_argument("document_id", help="Document ID")
    read_parser.add_argument(
        "--format",
        choices=["text", "markdown", "pdf"],
        default="markdown",
        help="Output format: markdown (default, preserves tables and headings), text (plain text), or pdf",
    )
    read_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (used with pdf format)",
    )
    read_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # content commands
    content_parser = subparsers.add_parser("content", help="Content operations")
    content_subparsers = content_parser.add_subparsers(dest="content_command")

    append_parser = content_subparsers.add_parser("append", help="Append text to document")
    append_parser.add_argument("document_id", help="Document ID")
    append_parser.add_argument("--text", required=True, help="Text to append")
    append_parser.add_argument("--json", action="store_true", help="Output as JSON")

    insert_parser = content_subparsers.add_parser("insert", help="Insert text at position")
    insert_parser.add_argument("document_id", help="Document ID")
    insert_parser.add_argument("--text", required=True, help="Text to insert")
    insert_parser.add_argument("--index", type=int, required=True, help="Position to insert at")
    insert_parser.add_argument("--json", action="store_true", help="Output as JSON")

    delete_parser = content_subparsers.add_parser("delete", help="Delete content range")
    delete_parser.add_argument("document_id", help="Document ID")
    delete_parser.add_argument("--start-index", type=int, required=True, help="Start position")
    delete_parser.add_argument("--end-index", type=int, required=True, help="End position")
    delete_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # formatting commands
    formatting_parser = subparsers.add_parser("formatting", help="Formatting operations")
    formatting_subparsers = formatting_parser.add_subparsers(dest="formatting_command")

    apply_parser = formatting_subparsers.add_parser("apply", help="Apply text formatting")
    apply_parser.add_argument("document_id", help="Document ID")
    apply_parser.add_argument("--start-index", type=int, required=True, help="Start position")
    apply_parser.add_argument("--end-index", type=int, required=True, help="End position")
    apply_parser.add_argument("--bold", action="store_true", help="Apply bold")
    apply_parser.add_argument("--italic", action="store_true", help="Apply italic")
    apply_parser.add_argument("--underline", action="store_true", help="Apply underline")
    apply_parser.add_argument("--font-size", type=int, help="Font size in points")
    apply_parser.add_argument("--json", action="store_true", help="Output as JSON")

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
        elif args.command == "documents":
            if args.documents_command == "create":
                return cmd_documents_create(args)
            elif args.documents_command == "get":
                return cmd_documents_get(args)
            elif args.documents_command == "read":
                return cmd_documents_read(args)
        elif args.command == "content":
            if args.content_command == "append":
                return cmd_content_append(args)
            elif args.content_command == "insert":
                return cmd_content_insert(args)
            elif args.content_command == "delete":
                return cmd_content_delete(args)
        elif args.command == "formatting" and args.formatting_command == "apply":
            return cmd_formatting_apply(args)

        parser.print_help()
        return 1

    except (DocsAPIError, AuthenticationError) as e:
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
