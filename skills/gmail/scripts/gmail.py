#!/usr/bin/env python3
"""Gmail integration skill for AI agents.

This is a self-contained script that provides Gmail functionality.

Usage:
    python gmail.py check
    python gmail.py auth setup --client-id ID --client-secret SECRET
    python gmail.py messages list --query "is:unread" --max-results 10
    python gmail.py messages get MESSAGE_ID
    python gmail.py send --to user@example.com --subject "Hello" --body "World"
    python gmail.py drafts list
    python gmail.py labels list

Requirements:
    pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
"""

from __future__ import annotations

# Standard library imports
import argparse
import base64
import contextlib
import json
import os
import sys
from email.mime.text import MIMEText
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

# Gmail API scopes - granular scopes for different operations
GMAIL_SCOPES_READONLY = ["https://www.googleapis.com/auth/gmail.readonly"]
GMAIL_SCOPES_SEND = ["https://www.googleapis.com/auth/gmail.send"]
GMAIL_SCOPES_MODIFY = ["https://www.googleapis.com/auth/gmail.modify"]
GMAIL_SCOPES_LABELS = ["https://www.googleapis.com/auth/gmail.labels"]

# Full scope set for maximum functionality
GMAIL_SCOPES_FULL = (
    GMAIL_SCOPES_READONLY + GMAIL_SCOPES_SEND + GMAIL_SCOPES_MODIFY + GMAIL_SCOPES_LABELS
)

# Minimal read-only scope (default)
GMAIL_SCOPES_DEFAULT = GMAIL_SCOPES_READONLY


# ============================================================================
# KEYRING CREDENTIAL STORAGE
# ============================================================================


def get_credential(key: str) -> str | None:
    """Get a credential from the system keyring.

    Args:
        key: The credential key (e.g., "gmail-token-json").

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
        service: Service name (e.g., "gmail").

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
        f"  1. Service config: Run python gmail.py auth setup --client-id YOUR_ID --client-secret YOUR_SECRET\n"
        f"  2. Service env vars: Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET\n"
        f"  3. Shared config: Create ~/.config/agent-skills/google.yaml with oauth_client credentials\n"
        f"  4. Shared env vars: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    )


def get_google_credentials(service: str, scopes: list[str]) -> Credentials:
    """Get Google credentials for human-in-the-loop use cases.

    Priority:
    1. Saved OAuth tokens from keyring - from previous OAuth flow
    2. OAuth 2.0 flow - opens browser for user consent

    Note: Service account authentication is NOT supported - this is
    designed for interactive human use cases only.

    Args:
        service: Service name (e.g., "gmail").
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

    # 2. Initiate OAuth flow - human interaction required
    try:
        client_config = get_oauth_client_config(service)
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        creds = flow.run_local_server(port=0)  # Opens browser for consent
        # Save token to keyring for future use
        set_credential(f"{service}-token-json", creds.to_json())
        return creds
    except Exception as e:
        raise AuthenticationError(f"OAuth flow failed: {e}") from e


def build_gmail_service(scopes: list[str] | None = None):
    """Build and return Gmail API service.

    Args:
        scopes: List of OAuth scopes to request. Defaults to read-only.

    Returns:
        Gmail API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    if scopes is None:
        scopes = GMAIL_SCOPES_DEFAULT
    creds = get_google_credentials("gmail", scopes)
    return build("gmail", "v1", credentials=creds)


# ============================================================================
# GMAIL API ERROR HANDLING
# ============================================================================


class GmailAPIError(Exception):
    """Exception raised for Gmail API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def handle_api_error(error: HttpError) -> None:
    """Convert Google API HttpError to GmailAPIError.

    Args:
        error: HttpError from Google API.

    Raises:
        GmailAPIError: With appropriate message and status code.
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
            "To grant full access, revoke your current token and re-authenticate:\n\n"
            "  1. Revoke: Go to https://myaccount.google.com/permissions and remove 'Agent Skills'\n"
            "  2. Clear token: keyring del agent-skills gmail-token-json\n"
            "  3. Re-run: python scripts/gmail.py check\n\n"
            "For setup help, see: docs/google-oauth-setup.md\n"
        )
        message = f"{message}{scope_help}"

    raise GmailAPIError(
        f"Gmail API error: {message} (HTTP {status_code})",
        status_code=status_code,
        details=details,
    )


# ============================================================================
# MESSAGE OPERATIONS
# ============================================================================


def list_messages(
    service, query: str = "", max_results: int = 10, label_ids: list[str] | None = None
) -> list[dict[str, Any]]:
    """List Gmail messages matching query.

    Args:
        service: Gmail API service object.
        query: Gmail search query (e.g., "is:unread", "from:user@example.com").
        max_results: Maximum number of messages to return.
        label_ids: List of label IDs to filter by.

    Returns:
        List of message dictionaries with id and threadId.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        params: dict[str, Any] = {"userId": "me", "maxResults": max_results}
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids

        result = service.users().messages().list(**params).execute()
        messages = result.get("messages", [])
        return messages
    except HttpError as e:
        handle_api_error(e)
        return []  # Unreachable, but satisfies type checker


def get_message(service, message_id: str, format: str = "full") -> dict[str, Any]:
    """Get a Gmail message by ID.

    Args:
        service: Gmail API service object.
        message_id: The message ID.
        format: Message format (full, minimal, raw, metadata).

    Returns:
        Message dictionary with full details.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        message = (
            service.users().messages().get(userId="me", id=message_id, format=format).execute()
        )
        return message
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def send_message(
    service,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
) -> dict[str, Any]:
    """Send an email message.

    Args:
        service: Gmail API service object.
        to: Recipient email address.
        subject: Email subject.
        body: Email body (plain text).
        cc: CC recipients (comma-separated).
        bcc: BCC recipients (comma-separated).

    Returns:
        Sent message dictionary.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        message = MIMEText(body)
        message["To"] = to
        message["Subject"] = subject
        if cc:
            message["Cc"] = cc
        if bcc:
            message["Bcc"] = bcc

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        result = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# DRAFT OPERATIONS
# ============================================================================


def create_draft(
    service,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
) -> dict[str, Any]:
    """Create a draft email.

    Args:
        service: Gmail API service object.
        to: Recipient email address.
        subject: Email subject.
        body: Email body (plain text).
        cc: CC recipients (comma-separated).
        bcc: BCC recipients (comma-separated).

    Returns:
        Draft dictionary.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        message = MIMEText(body)
        message["To"] = to
        message["Subject"] = subject
        if cc:
            message["Cc"] = cc
        if bcc:
            message["Bcc"] = bcc

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw_message}})
            .execute()
        )
        return draft
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def list_drafts(service, max_results: int = 10) -> list[dict[str, Any]]:
    """List Gmail drafts.

    Args:
        service: Gmail API service object.
        max_results: Maximum number of drafts to return.

    Returns:
        List of draft dictionaries.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        result = service.users().drafts().list(userId="me", maxResults=max_results).execute()
        drafts = result.get("drafts", [])
        return drafts
    except HttpError as e:
        handle_api_error(e)
        return []  # Unreachable


def send_draft(service, draft_id: str) -> dict[str, Any]:
    """Send a draft email.

    Args:
        service: Gmail API service object.
        draft_id: The draft ID to send.

    Returns:
        Sent message dictionary.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        result = service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# LABEL OPERATIONS
# ============================================================================


def list_labels(service) -> list[dict[str, Any]]:
    """List all Gmail labels.

    Args:
        service: Gmail API service object.

    Returns:
        List of label dictionaries.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        result = service.users().labels().list(userId="me").execute()
        labels = result.get("labels", [])
        return labels
    except HttpError as e:
        handle_api_error(e)
        return []  # Unreachable


def create_label(service, name: str) -> dict[str, Any]:
    """Create a new Gmail label.

    Args:
        service: Gmail API service object.
        name: Label name.

    Returns:
        Created label dictionary.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        label = service.users().labels().create(userId="me", body={"name": name}).execute()
        return label
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def modify_message_labels(
    service,
    message_id: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
) -> dict[str, Any]:
    """Modify labels on a message.

    Args:
        service: Gmail API service object.
        message_id: The message ID.
        add_labels: List of label IDs to add.
        remove_labels: List of label IDs to remove.

    Returns:
        Modified message dictionary.

    Raises:
        GmailAPIError: If the API call fails.
    """
    try:
        body: dict[str, Any] = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        result = service.users().messages().modify(userId="me", id=message_id, body=body).execute()
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_message_summary(message: dict[str, Any]) -> str:
    """Format a message for display.

    Args:
        message: Message dictionary from Gmail API.

    Returns:
        Formatted string.
    """
    headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
    subject = headers.get("Subject", "(No subject)")
    from_addr = headers.get("From", "(Unknown)")
    date = headers.get("Date", "(Unknown)")
    snippet = message.get("snippet", "")

    return f"""ID: {message["id"]}
From: {from_addr}
Date: {date}
Subject: {subject}
Preview: {snippet[:100]}..."""


def format_label(label: dict[str, Any]) -> str:
    """Format a label for display.

    Args:
        label: Label dictionary from Gmail API.

    Returns:
        Formatted string.
    """
    name = label.get("name", "(Unknown)")
    label_id = label.get("id", "(Unknown)")
    label_type = label.get("type", "user")
    return f"{name} (ID: {label_id}, Type: {label_type})"


# ============================================================================
# HEALTH CHECK
# ============================================================================


def check_gmail_connectivity() -> dict[str, Any]:
    """Check Gmail API connectivity and authentication.

    Returns:
        Dictionary with status information including available scopes.
    """
    result = {
        "authenticated": False,
        "profile": None,
        "scopes": None,
        "error": None,
    }

    try:
        # Get credentials to check scopes
        creds = get_google_credentials("gmail", GMAIL_SCOPES_DEFAULT)

        # Check which scopes are available
        available_scopes = []
        if hasattr(creds, "scopes"):
            available_scopes = creds.scopes
        elif hasattr(creds, "_scopes"):
            available_scopes = creds._scopes

        # Build service and get profile
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()

        result["authenticated"] = True
        result["profile"] = {
            "email": profile.get("emailAddress"),
            "messages_total": profile.get("messagesTotal"),
            "threads_total": profile.get("threadsTotal"),
        }
        result["scopes"] = {
            "readonly": any("gmail.readonly" in s for s in available_scopes),
            "send": any("gmail.send" in s for s in available_scopes),
            "modify": any("gmail.modify" in s for s in available_scopes),
            "labels": any("gmail.labels" in s for s in available_scopes),
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
    print("Checking Gmail connectivity...")
    result = check_gmail_connectivity()

    if result["authenticated"]:
        print("✓ Successfully authenticated to Gmail")
        profile = result["profile"]
        print(f"  Email: {profile['email']}")
        print(f"  Total messages: {profile['messages_total']}")
        print(f"  Total threads: {profile['threads_total']}")

        # Display scope information
        scopes = result.get("scopes", {})
        if scopes:
            print("\nGranted OAuth Scopes:")
            print(f"  Read-only (gmail.readonly):  {'✓' if scopes.get('readonly') else '✗'}")
            print(f"  Send (gmail.send):           {'✓' if scopes.get('send') else '✗'}")
            print(f"  Modify (gmail.modify):       {'✓' if scopes.get('modify') else '✗'}")
            print(f"  Labels (gmail.labels):       {'✓' if scopes.get('labels') else '✗'}")

            # Check if all scopes are granted
            all_granted = all(
                [
                    scopes.get("readonly"),
                    scopes.get("send"),
                    scopes.get("modify"),
                    scopes.get("labels"),
                ]
            )

            if not all_granted:
                print("\n⚠️  Not all scopes are granted. Some operations may fail.")
                print("   To grant full access, revoke and re-authenticate:")
                print()
                print("   1. Revoke: https://myaccount.google.com/permissions")
                print("   2. Clear token: keyring del agent-skills gmail-token-json")
                print("   3. Re-run: python scripts/gmail.py check")
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
        print("     python scripts/gmail.py check")
        print()
        print("For detailed setup instructions, see: docs/google-oauth-setup.md")
        return 1


def cmd_auth_setup(args):
    """Handle 'auth setup' command."""
    if not args.client_id or not args.client_secret:
        print("Error: Both --client-id and --client-secret are required", file=sys.stderr)
        return 1

    config = load_config("gmail") or {}
    config["oauth_client"] = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
    }
    save_config("gmail", config)
    print("✓ OAuth client credentials saved to config file")
    print(f"  Config location: {CONFIG_DIR / 'gmail.yaml'}")
    print("\nNext step: Run any Gmail command to initiate OAuth flow")
    return 0


def cmd_messages_list(args):
    """Handle 'messages list' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY)
    messages = list_messages(service, query=args.query or "", max_results=args.max_results)

    if args.json:
        print(json.dumps(messages, indent=2))
    else:
        if not messages:
            print("No messages found")
        else:
            print(f"Found {len(messages)} message(s):\n")
            for msg in messages:
                # Fetch full message details for display
                full_msg = get_message(service, msg["id"], format="metadata")
                print(format_message_summary(full_msg))
                print("-" * 80)

    return 0


def cmd_messages_get(args):
    """Handle 'messages get' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY)
    message = get_message(service, args.message_id, format=args.format)

    if args.json:
        print(json.dumps(message, indent=2))
    else:
        print(format_message_summary(message))

    return 0


def cmd_send(args):
    """Handle 'send' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY + GMAIL_SCOPES_SEND)
    result = send_message(
        service, to=args.to, subject=args.subject, body=args.body, cc=args.cc, bcc=args.bcc
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Message sent successfully")
        print(f"  Message ID: {result.get('id')}")
        print(f"  Thread ID: {result.get('threadId')}")

    return 0


def cmd_drafts_list(args):
    """Handle 'drafts list' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY)
    drafts = list_drafts(service, max_results=args.max_results)

    if args.json:
        print(json.dumps(drafts, indent=2))
    else:
        if not drafts:
            print("No drafts found")
        else:
            print(f"Found {len(drafts)} draft(s):\n")
            for draft in drafts:
                print(f"Draft ID: {draft['id']}")
                if "message" in draft:
                    print(f"  Message ID: {draft['message']['id']}")
                print("-" * 40)

    return 0


def cmd_drafts_create(args):
    """Handle 'drafts create' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY + GMAIL_SCOPES_MODIFY)
    result = create_draft(
        service, to=args.to, subject=args.subject, body=args.body, cc=args.cc, bcc=args.bcc
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Draft created successfully")
        print(f"  Draft ID: {result.get('id')}")

    return 0


def cmd_drafts_send(args):
    """Handle 'drafts send' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY + GMAIL_SCOPES_SEND + GMAIL_SCOPES_MODIFY)
    result = send_draft(service, args.draft_id)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Draft sent successfully")
        print(f"  Message ID: {result.get('id')}")

    return 0


def cmd_labels_list(args):
    """Handle 'labels list' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY + GMAIL_SCOPES_LABELS)
    labels = list_labels(service)

    if args.json:
        print(json.dumps(labels, indent=2))
    else:
        if not labels:
            print("No labels found")
        else:
            print(f"Found {len(labels)} label(s):\n")
            for label in labels:
                print(format_label(label))

    return 0


def cmd_labels_create(args):
    """Handle 'labels create' command."""
    service = build_gmail_service(GMAIL_SCOPES_READONLY + GMAIL_SCOPES_LABELS)
    result = create_label(service, args.name)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Label created successfully")
        print(f"  Name: {result.get('name')}")
        print(f"  ID: {result.get('id')}")

    return 0


# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Gmail integration for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check command
    subparsers.add_parser("check", help="Check Gmail connectivity and authentication")

    # auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    setup_parser = auth_subparsers.add_parser("setup", help="Setup OAuth client credentials")
    setup_parser.add_argument("--client-id", required=True, help="OAuth client ID")
    setup_parser.add_argument("--client-secret", required=True, help="OAuth client secret")

    # messages commands
    messages_parser = subparsers.add_parser("messages", help="Message operations")
    messages_subparsers = messages_parser.add_subparsers(dest="messages_command")

    list_parser = messages_subparsers.add_parser("list", help="List messages")
    list_parser.add_argument("--query", help="Gmail search query")
    list_parser.add_argument("--max-results", type=int, default=10, help="Maximum results")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    get_parser = messages_subparsers.add_parser("get", help="Get message by ID")
    get_parser.add_argument("message_id", help="Message ID")
    get_parser.add_argument(
        "--format", choices=["full", "minimal", "raw", "metadata"], default="full"
    )
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # send command
    send_parser = subparsers.add_parser("send", help="Send an email")
    send_parser.add_argument("--to", required=True, help="Recipient email address")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")
    send_parser.add_argument("--cc", help="CC recipients (comma-separated)")
    send_parser.add_argument("--bcc", help="BCC recipients (comma-separated)")
    send_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # drafts commands
    drafts_parser = subparsers.add_parser("drafts", help="Draft operations")
    drafts_subparsers = drafts_parser.add_subparsers(dest="drafts_command")

    drafts_list_parser = drafts_subparsers.add_parser("list", help="List drafts")
    drafts_list_parser.add_argument("--max-results", type=int, default=10, help="Maximum results")
    drafts_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    drafts_create_parser = drafts_subparsers.add_parser("create", help="Create a draft")
    drafts_create_parser.add_argument("--to", required=True, help="Recipient email address")
    drafts_create_parser.add_argument("--subject", required=True, help="Email subject")
    drafts_create_parser.add_argument("--body", required=True, help="Email body")
    drafts_create_parser.add_argument("--cc", help="CC recipients (comma-separated)")
    drafts_create_parser.add_argument("--bcc", help="BCC recipients (comma-separated)")
    drafts_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    drafts_send_parser = drafts_subparsers.add_parser("send", help="Send a draft")
    drafts_send_parser.add_argument("draft_id", help="Draft ID to send")
    drafts_send_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # labels commands
    labels_parser = subparsers.add_parser("labels", help="Label operations")
    labels_subparsers = labels_parser.add_subparsers(dest="labels_command")

    labels_list_parser = labels_subparsers.add_parser("list", help="List labels")
    labels_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    labels_create_parser = labels_subparsers.add_parser("create", help="Create a label")
    labels_create_parser.add_argument("name", help="Label name")
    labels_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

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
        elif args.command == "messages":
            if args.messages_command == "list":
                return cmd_messages_list(args)
            elif args.messages_command == "get":
                return cmd_messages_get(args)
        elif args.command == "send":
            return cmd_send(args)
        elif args.command == "drafts":
            if args.drafts_command == "list":
                return cmd_drafts_list(args)
            elif args.drafts_command == "create":
                return cmd_drafts_create(args)
            elif args.drafts_command == "send":
                return cmd_drafts_send(args)
        elif args.command == "labels":
            if args.labels_command == "list":
                return cmd_labels_list(args)
            elif args.labels_command == "create":
                return cmd_labels_create(args)

        parser.print_help()
        return 1

    except (GmailAPIError, AuthenticationError) as e:
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
