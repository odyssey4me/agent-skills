"""OAuth2 flow utilities for Google services."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from shared.auth.keyring_store import get_credential, set_credential

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials as GoogleCredentials

# Scopes for Google services
GOOGLE_SCOPES = {
    "gmail": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
    ],
    "drive": [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",
    ],
    "calendar": [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ],
}


def get_google_credentials(
    service: str, credentials_file: Path | None = None
) -> GoogleCredentials | None:
    """Get Google OAuth credentials for a service.

    Args:
        service: Google service name (gmail, drive, calendar).
        credentials_file: Path to client credentials JSON file.

    Returns:
        Google credentials object or None if not available.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return None

    scopes = GOOGLE_SCOPES.get(service, [])
    if not scopes:
        return None

    # Try to load existing token from keyring
    token = get_credential(f"google-{service}-token")
    refresh_token = get_credential(f"google-{service}-refresh-token")

    if token and refresh_token:
        creds = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=get_credential("google-client-id"),
            client_secret=get_credential("google-client-secret"),
            scopes=scopes,
        )
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
            set_credential(f"google-{service}-token", creds.token)
            return creds

    # Need to run OAuth flow
    if not credentials_file or not credentials_file.exists():
        return None

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes)
    creds = flow.run_local_server(port=0)

    # Store tokens in keyring
    set_credential(f"google-{service}-token", creds.token)
    set_credential(f"google-{service}-refresh-token", creds.refresh_token)
    set_credential("google-client-id", creds.client_id)
    set_credential("google-client-secret", creds.client_secret)

    return creds
