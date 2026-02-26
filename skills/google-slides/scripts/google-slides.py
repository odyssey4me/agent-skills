#!/usr/bin/env python3
"""Google Slides integration skill for AI agents.

This is a self-contained script that provides Google Slides functionality.

Usage:
    python google-slides.py check
    python google-slides.py auth setup --client-id ID --client-secret SECRET
    python google-slides.py presentations create --title "My Presentation"
    python google-slides.py presentations get PRESENTATION_ID
    python google-slides.py slides create PRESENTATION_ID --layout BLANK
    python google-slides.py slides delete PRESENTATION_ID --slide-id SLIDE_ID
    python google-slides.py text insert PRESENTATION_ID --slide-id SLIDE_ID --text "Hello"
    python google-slides.py shapes create PRESENTATION_ID --slide-id SLIDE_ID --shape-type RECTANGLE

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

# Google Slides API scopes - granular scopes for different operations
SLIDES_SCOPES_READONLY = ["https://www.googleapis.com/auth/presentations.readonly"]
SLIDES_SCOPES = ["https://www.googleapis.com/auth/presentations"]

# Minimal read-only scope (default)
SLIDES_SCOPES_DEFAULT = SLIDES_SCOPES_READONLY

# Drive API scope needed for PDF export
DRIVE_SCOPES_READONLY = ["https://www.googleapis.com/auth/drive.readonly"]

# EMU (English Metric Units) conversion - Slides uses EMUs
# 1 inch = 914400 EMUs
# 1 point = 12700 EMUs
EMU_PER_INCH = 914400
EMU_PER_PT = 12700


# ============================================================================
# KEYRING CREDENTIAL STORAGE
# ============================================================================


def get_credential(key: str) -> str | None:
    """Get a credential from the system keyring.

    Args:
        key: The credential key (e.g., "google-slides-token-json").

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
        service: Service name (e.g., "google-slides").

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
        f"  1. Service config: Run python google-slides.py auth setup --client-id YOUR_ID --client-secret YOUR_SECRET\n"
        f"  2. Service env vars: Set GOOGLE_SLIDES_CLIENT_ID and GOOGLE_SLIDES_CLIENT_SECRET\n"
        f"  3. Shared config: Create ~/.config/agent-skills/google.yaml with oauth_client credentials\n"
        f"  4. Shared env vars: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    )


def _run_oauth_flow(service: str, scopes: list[str]) -> Credentials:
    """Run OAuth browser flow and store resulting token.

    Args:
        service: Service name (e.g., "google-slides").
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
        service: Service name (e.g., "google-slides").
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


def build_slides_service(scopes: list[str] | None = None):
    """Build and return Google Slides API service.

    Args:
        scopes: List of OAuth scopes to request. Defaults to read-only.

    Returns:
        Google Slides API service object.

    Raises:
        AuthenticationError: If authentication fails.
    """
    if scopes is None:
        scopes = SLIDES_SCOPES_DEFAULT
    creds = get_google_credentials("google-slides", scopes)
    return build("slides", "v1", credentials=creds)


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
    creds = get_google_credentials("google-slides", scopes)
    return build("drive", "v3", credentials=creds)


# ============================================================================
# GOOGLE SLIDES API ERROR HANDLING
# ============================================================================


class SlidesAPIError(Exception):
    """Exception raised for Google Slides API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def handle_api_error(error: HttpError) -> None:
    """Convert Google API HttpError to SlidesAPIError.

    Args:
        error: HttpError from Google API.

    Raises:
        SlidesAPIError: With appropriate message and status code.
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
            "  1. Reset token: python scripts/google-slides.py auth reset\n"
            "  2. Re-run: python scripts/google-slides.py check\n\n"
            "For setup help, see: docs/google-oauth-setup.md\n"
        )
        message = f"{message}{scope_help}"

    raise SlidesAPIError(
        f"Google Slides API error: {message} (HTTP {status_code})",
        status_code=status_code,
        details=details,
    )


# ============================================================================
# PRESENTATION OPERATIONS
# ============================================================================


def create_presentation(service, title: str) -> dict[str, Any]:
    """Create a new Google Slides presentation.

    Args:
        service: Google Slides API service object.
        title: Presentation title.

    Returns:
        Created presentation dictionary with presentationId.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    try:
        body = {"title": title}
        presentation = service.presentations().create(body=body).execute()
        return presentation
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def get_presentation(service, presentation_id: str) -> dict[str, Any]:
    """Get a presentation by ID.

    Args:
        service: Google Slides API service object.
        presentation_id: The presentation ID.

    Returns:
        Presentation dictionary with metadata and slides.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    try:
        presentation = service.presentations().get(presentationId=presentation_id).execute()
        return presentation
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def read_presentation_content(service, presentation_id: str) -> str:
    """Extract text content from all slides in a presentation.

    Args:
        service: Google Slides API service object.
        presentation_id: The presentation ID.

    Returns:
        Text content from all slides, with slide separators.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    presentation = get_presentation(service, presentation_id)
    slides = presentation.get("slides", [])

    output_parts = []
    for idx, slide in enumerate(slides):
        slide_text = _extract_slide_text(slide)
        if slide_text.strip():
            output_parts.append(f"--- Slide {idx + 1} ---\n{slide_text}")

    return "\n\n".join(output_parts)


def _extract_slide_text(slide: dict) -> str:
    """Extract all text from a slide's page elements.

    Args:
        slide: Slide dictionary from the API.

    Returns:
        Combined text from all elements on the slide.
    """
    text_parts = []

    for element in slide.get("pageElements", []):
        # Handle shapes with text (including text boxes)
        if "shape" in element:
            shape = element["shape"]
            if "text" in shape:
                text = _extract_text_from_text_content(shape["text"])
                if text.strip():
                    text_parts.append(text.strip())

        # Handle tables
        if "table" in element:
            table_text = _extract_table_text(element["table"])
            if table_text.strip():
                text_parts.append(table_text)

    return "\n".join(text_parts)


def _extract_text_from_text_content(text_content: dict) -> str:
    """Extract text from a textContent structure.

    Args:
        text_content: Text content dictionary from the API.

    Returns:
        Combined text string.
    """
    parts = []
    for text_elem in text_content.get("textElements", []):
        if "textRun" in text_elem:
            parts.append(text_elem["textRun"].get("content", ""))
    return "".join(parts)


def _extract_table_text(table: dict) -> str:
    """Extract text from a table element as markdown.

    Args:
        table: Table dictionary from the API.

    Returns:
        Markdown-formatted table string.
    """
    rows_text = []
    for row_idx, row in enumerate(table.get("tableRows", [])):
        cell_texts = []
        for cell in row.get("tableCells", []):
            if "text" in cell:
                cell_texts.append(_extract_text_from_text_content(cell["text"]).strip())
            else:
                cell_texts.append("")
        if cell_texts:
            rows_text.append("| " + " | ".join(cell_texts) + " |")
            if row_idx == 0:
                rows_text.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")
    return "\n".join(rows_text)


def export_presentation_as_pdf(presentation_id: str) -> bytes:
    """Export presentation as PDF using Google's native export.

    Uses the Drive API to export the presentation in PDF format.

    Args:
        presentation_id: The Google Slides presentation ID.

    Returns:
        PDF content as bytes.

    Raises:
        SlidesAPIError: If the export fails.
    """
    try:
        service = build_drive_service()
        response = (
            service.files().export(fileId=presentation_id, mimeType="application/pdf").execute()
        )
        return response
    except HttpError as e:
        handle_api_error(e)
        return b""  # Unreachable


# ============================================================================
# SLIDE OPERATIONS
# ============================================================================


def create_slide(
    service, presentation_id: str, layout: str = "BLANK", insert_index: int | None = None
) -> dict[str, Any]:
    """Add a new slide to a presentation.

    Args:
        service: Google Slides API service object.
        presentation_id: The presentation ID.
        layout: Slide layout (BLANK, TITLE, TITLE_AND_BODY, etc.). Default is BLANK.
        insert_index: Optional index where to insert the slide. If None, appends to end.

    Returns:
        Batch update response from the API.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    try:
        requests = []

        # Map simple layout names to predefined layout types
        layout_map = {
            "BLANK": "BLANK",
            "TITLE": "TITLE",
            "TITLE_AND_BODY": "TITLE_AND_BODY",
            "TITLE_ONLY": "TITLE_ONLY",
            "SECTION_HEADER": "SECTION_HEADER",
            "SECTION_TITLE_AND_DESCRIPTION": "SECTION_TITLE_AND_DESCRIPTION",
            "ONE_COLUMN_TEXT": "ONE_COLUMN_TEXT",
            "MAIN_POINT": "MAIN_POINT",
            "BIG_NUMBER": "BIG_NUMBER",
        }

        predefined_layout = layout_map.get(layout.upper(), "BLANK")

        create_slide_request: dict[str, Any] = {
            "createSlide": {"slideLayoutReference": {"predefinedLayout": predefined_layout}}
        }

        if insert_index is not None:
            create_slide_request["createSlide"]["insertionIndex"] = insert_index

        requests.append(create_slide_request)

        body = {"requests": requests}
        result = (
            service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def delete_slide(service, presentation_id: str, slide_id: str) -> dict[str, Any]:
    """Delete a slide from a presentation.

    Args:
        service: Google Slides API service object.
        presentation_id: The presentation ID.
        slide_id: The slide object ID (not index).

    Returns:
        Batch update response from the API.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    try:
        requests = [{"deleteObject": {"objectId": slide_id}}]

        body = {"requests": requests}
        result = (
            service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# TEXT OPERATIONS
# ============================================================================


def insert_text(
    service,
    presentation_id: str,
    slide_id: str,
    text: str,
    x: float = 100,
    y: float = 100,
    width: float = 400,
    height: float = 100,
) -> dict[str, Any]:
    """Insert text into a slide.

    Args:
        service: Google Slides API service object.
        presentation_id: The presentation ID.
        slide_id: The slide object ID.
        text: Text to insert.
        x: X coordinate in points (default: 100).
        y: Y coordinate in points (default: 100).
        width: Text box width in points (default: 400).
        height: Text box height in points (default: 100).

    Returns:
        Batch update response from the API.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    try:
        # Convert points to EMUs
        x_emu = int(x * EMU_PER_PT)
        y_emu = int(y * EMU_PER_PT)
        width_emu = int(width * EMU_PER_PT)
        height_emu = int(height * EMU_PER_PT)

        # Generate a unique ID for the text box
        text_box_id = f"TextBox_{slide_id}_{hash(text) % 1000000}"

        requests = [
            {
                "createShape": {
                    "objectId": text_box_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": width_emu, "unit": "EMU"},
                            "height": {"magnitude": height_emu, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": x_emu,
                            "translateY": y_emu,
                            "unit": "EMU",
                        },
                    },
                }
            },
            {"insertText": {"objectId": text_box_id, "text": text, "insertionIndex": 0}},
        ]

        body = {"requests": requests}
        result = (
            service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# SHAPE OPERATIONS
# ============================================================================


def create_shape(
    service,
    presentation_id: str,
    slide_id: str,
    shape_type: str,
    x: float = 100,
    y: float = 100,
    width: float = 200,
    height: float = 200,
) -> dict[str, Any]:
    """Create a shape on a slide.

    Args:
        service: Google Slides API service object.
        presentation_id: The presentation ID.
        slide_id: The slide object ID.
        shape_type: Shape type (RECTANGLE, ELLIPSE, TRIANGLE, etc.).
        x: X coordinate in points (default: 100).
        y: Y coordinate in points (default: 100).
        width: Shape width in points (default: 200).
        height: Shape height in points (default: 200).

    Returns:
        Batch update response from the API.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    try:
        # Convert points to EMUs
        x_emu = int(x * EMU_PER_PT)
        y_emu = int(y * EMU_PER_PT)
        width_emu = int(width * EMU_PER_PT)
        height_emu = int(height * EMU_PER_PT)

        # Generate a unique ID for the shape
        shape_id = f"Shape_{slide_id}_{shape_type}_{hash(f'{x}{y}') % 1000000}"

        requests = [
            {
                "createShape": {
                    "objectId": shape_id,
                    "shapeType": shape_type.upper(),
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": width_emu, "unit": "EMU"},
                            "height": {"magnitude": height_emu, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": x_emu,
                            "translateY": y_emu,
                            "unit": "EMU",
                        },
                    },
                }
            }
        ]

        body = {"requests": requests}
        result = (
            service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


def create_image(
    service,
    presentation_id: str,
    slide_id: str,
    image_url: str,
    x: float = 100,
    y: float = 100,
    width: float = 300,
    height: float = 200,
) -> dict[str, Any]:
    """Create an image on a slide.

    Args:
        service: Google Slides API service object.
        presentation_id: The presentation ID.
        slide_id: The slide object ID.
        image_url: URL of the image to insert.
        x: X coordinate in points (default: 100).
        y: Y coordinate in points (default: 100).
        width: Image width in points (default: 300).
        height: Image height in points (default: 200).

    Returns:
        Batch update response from the API.

    Raises:
        SlidesAPIError: If the API call fails.
    """
    try:
        # Convert points to EMUs
        x_emu = int(x * EMU_PER_PT)
        y_emu = int(y * EMU_PER_PT)
        width_emu = int(width * EMU_PER_PT)
        height_emu = int(height * EMU_PER_PT)

        # Generate a unique ID for the image
        image_id = f"Image_{slide_id}_{hash(image_url) % 1000000}"

        requests = [
            {
                "createImage": {
                    "objectId": image_id,
                    "url": image_url,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": width_emu, "unit": "EMU"},
                            "height": {"magnitude": height_emu, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": x_emu,
                            "translateY": y_emu,
                            "unit": "EMU",
                        },
                    },
                }
            }
        ]

        body = {"requests": requests}
        result = (
            service.presentations().batchUpdate(presentationId=presentation_id, body=body).execute()
        )
        return result
    except HttpError as e:
        handle_api_error(e)
        return {}  # Unreachable


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_presentation_summary(presentation: dict[str, Any]) -> str:
    """Format a presentation for display.

    Args:
        presentation: Presentation dictionary from Google Slides API.

    Returns:
        Formatted string.
    """
    title = presentation.get("title", "(Untitled)")
    presentation_id = presentation.get("presentationId", "(Unknown)")
    slides = presentation.get("slides", [])

    return (
        f"### {title}\n"
        f"- **Presentation ID:** {presentation_id}\n"
        f"- **Slides:** {len(slides)}\n"
        f"- **URL:** https://docs.google.com/presentation/d/{presentation_id}/edit"
    )


def format_slide_info(slide: dict[str, Any], index: int) -> str:
    """Format slide information for display.

    Args:
        slide: Slide dictionary from Google Slides API.
        index: Slide index (0-based).

    Returns:
        Formatted string.
    """
    slide_id = slide.get("objectId", "(Unknown)")
    layout = slide.get("slideProperties", {}).get("layoutObjectId", "(Unknown)")

    # Count elements on the slide
    elements = slide.get("pageElements", [])
    element_counts = {"shapes": 0, "images": 0, "text": 0, "other": 0}

    for element in elements:
        if "shape" in element:
            if element["shape"].get("shapeType") == "TEXT_BOX":
                element_counts["text"] += 1
            else:
                element_counts["shapes"] += 1
        elif "image" in element:
            element_counts["images"] += 1
        else:
            element_counts["other"] += 1

    total = sum(element_counts.values())
    return (
        f"### Slide {index + 1}\n"
        f"- **ID:** {slide_id}\n"
        f"- **Layout:** {layout}\n"
        f"- **Elements:** {total} ({element_counts['text']} text, "
        f"{element_counts['shapes']} shapes, {element_counts['images']} images, "
        f"{element_counts['other']} other)"
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================


def check_slides_connectivity() -> dict[str, Any]:
    """Check Google Slides API connectivity and authentication.

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
        creds = get_google_credentials("google-slides", SLIDES_SCOPES_DEFAULT)

        # Check which scopes are available
        available_scopes = []
        if hasattr(creds, "scopes"):
            available_scopes = creds.scopes
        elif hasattr(creds, "_scopes"):
            available_scopes = creds._scopes

        # Build service - if this works, we're authenticated
        service = build("slides", "v1", credentials=creds)

        # Try a simple API call to verify connectivity
        # Create a test presentation
        test_pres = service.presentations().create(body={"title": "_test_connectivity"}).execute()
        test_pres_id = test_pres.get("presentationId")

        result["authenticated"] = True
        result["test_presentation_id"] = test_pres_id
        result["scopes"] = {
            "readonly": any("presentations.readonly" in s for s in available_scopes),
            "write": any("presentations" in s and "readonly" not in s for s in available_scopes),
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
    print("Checking Google Slides connectivity...")
    result = check_slides_connectivity()

    if result["authenticated"]:
        print("✓ Successfully authenticated to Google Slides")

        # Display scope information
        scopes = result.get("scopes", {})
        if scopes:
            print("\nGranted OAuth Scopes:")
            print(f"  Read-only (presentations.readonly): {'✓' if scopes.get('readonly') else '✗'}")
            print(f"  Write (presentations):               {'✓' if scopes.get('write') else '✗'}")

            # Check if write scope is granted
            if not scopes.get("write"):
                print("\n⚠️  Write scope not granted. Some operations will fail.")
                print("   To grant full access, reset and re-authenticate:")
                print()
                print("   1. Reset token: python scripts/google-slides.py auth reset")
                print("   2. Re-run: python scripts/google-slides.py check")
                print()
                print("   See: docs/google-oauth-setup.md")

        print(f"\nTest presentation created: {result.get('test_presentation_id')}")
        print("(You can delete this test presentation from Google Drive)")
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
        print("     python scripts/google-slides.py check")
        print()
        print("For detailed setup instructions, see: docs/google-oauth-setup.md")
        return 1


def cmd_auth_setup(args):
    """Handle 'auth setup' command."""
    if not args.client_id or not args.client_secret:
        print("Error: Both --client-id and --client-secret are required", file=sys.stderr)
        return 1

    config = load_config("google-slides") or {}
    config["oauth_client"] = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
    }
    save_config("google-slides", config)
    print("✓ OAuth client credentials saved to config file")
    print(f"  Config location: {CONFIG_DIR / 'google-slides.yaml'}")
    print("\nNext step: Run any Google Slides command to initiate OAuth flow")
    return 0


def cmd_auth_reset(_args):
    """Handle 'auth reset' command."""
    delete_credential("google-slides-token-json")
    print("OAuth token cleared. Next command will trigger re-authentication.")
    return 0


def cmd_auth_status(_args):
    """Handle 'auth status' command."""
    token_json = get_credential("google-slides-token-json")
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


def cmd_presentations_create(args):
    """Handle 'presentations create' command."""
    service = build_slides_service(SLIDES_SCOPES)
    presentation = create_presentation(service, args.title)

    if args.json:
        print(json.dumps(presentation, indent=2))
    else:
        print("✓ Presentation created successfully")
        print(format_presentation_summary(presentation))

    return 0


def cmd_presentations_get(args):
    """Handle 'presentations get' command."""
    service = build_slides_service(SLIDES_SCOPES_READONLY)
    presentation = get_presentation(service, args.presentation_id)

    if args.json:
        print(json.dumps(presentation, indent=2))
    else:
        print(format_presentation_summary(presentation))
        print()

        # Show slide details
        slides = presentation.get("slides", [])
        if slides:
            print("Slides:")
            for idx, slide in enumerate(slides):
                print(format_slide_info(slide, idx))

    return 0


def cmd_presentations_read(args):
    """Handle 'presentations read' command."""
    if args.format == "pdf":
        content = export_presentation_as_pdf(args.presentation_id)
        output_file = args.output or f"{args.presentation_id}.pdf"
        with open(output_file, "wb") as f:
            f.write(content)
        print(f"PDF saved to: {output_file}")
        return 0
    else:
        service = build_slides_service(SLIDES_SCOPES_READONLY)
        content = read_presentation_content(service, args.presentation_id)

    if args.json:
        print(json.dumps({"content": content}, indent=2))
    else:
        print(content)

    return 0


def cmd_slides_create(args):
    """Handle 'slides create' command."""
    service = build_slides_service(SLIDES_SCOPES)
    result = create_slide(service, args.presentation_id, args.layout, args.index)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Extract the new slide info from the reply
        reply = result.get("replies", [{}])[0]
        new_slide = reply.get("createSlide", {})
        slide_id = new_slide.get("objectId", "N/A")
        print("✓ Slide created successfully")
        print(f"  Slide ID: {slide_id}")
        print(f"  Layout: {args.layout}")

    return 0


def cmd_slides_delete(args):
    """Handle 'slides delete' command."""
    service = build_slides_service(SLIDES_SCOPES)
    result = delete_slide(service, args.presentation_id, args.slide_id)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Slide deleted successfully")

    return 0


def cmd_text_insert(args):
    """Handle 'text insert' command."""
    service = build_slides_service(SLIDES_SCOPES)
    result = insert_text(
        service,
        args.presentation_id,
        args.slide_id,
        args.text,
        args.x,
        args.y,
        args.width,
        args.height,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Text inserted successfully")
        print(f"  Text: {args.text}")
        print(f"  Position: ({args.x}, {args.y}) points")
        print(f"  Size: {args.width} x {args.height} points")

    return 0


def cmd_shapes_create(args):
    """Handle 'shapes create' command."""
    service = build_slides_service(SLIDES_SCOPES)
    result = create_shape(
        service,
        args.presentation_id,
        args.slide_id,
        args.shape_type,
        args.x,
        args.y,
        args.width,
        args.height,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Shape created successfully")
        print(f"  Type: {args.shape_type}")
        print(f"  Position: ({args.x}, {args.y}) points")
        print(f"  Size: {args.width} x {args.height} points")

    return 0


def cmd_images_create(args):
    """Handle 'images create' command."""
    service = build_slides_service(SLIDES_SCOPES)
    result = create_image(
        service,
        args.presentation_id,
        args.slide_id,
        args.image_url,
        args.x,
        args.y,
        args.width,
        args.height,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("✓ Image created successfully")
        print(f"  URL: {args.image_url}")
        print(f"  Position: ({args.x}, {args.y}) points")
        print(f"  Size: {args.width} x {args.height} points")

    return 0


# ============================================================================
# CLI ARGUMENT PARSER
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Google Slides integration for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check command
    subparsers.add_parser("check", help="Check Google Slides connectivity and authentication")

    # auth commands
    auth_parser = subparsers.add_parser("auth", help="Authentication management")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    setup_parser = auth_subparsers.add_parser("setup", help="Setup OAuth client credentials")
    setup_parser.add_argument("--client-id", required=True, help="OAuth client ID")
    setup_parser.add_argument("--client-secret", required=True, help="OAuth client secret")

    auth_subparsers.add_parser("reset", help="Clear stored OAuth token")
    auth_subparsers.add_parser("status", help="Show current token info")

    # presentations commands
    presentations_parser = subparsers.add_parser("presentations", help="Presentation operations")
    presentations_subparsers = presentations_parser.add_subparsers(dest="presentations_command")

    create_parser = presentations_subparsers.add_parser("create", help="Create a new presentation")
    create_parser.add_argument("--title", required=True, help="Presentation title")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    get_parser = presentations_subparsers.add_parser("get", help="Get presentation metadata")
    get_parser.add_argument("presentation_id", help="Presentation ID")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    read_parser = presentations_subparsers.add_parser("read", help="Read presentation text content")
    read_parser.add_argument("presentation_id", help="Presentation ID")
    read_parser.add_argument(
        "--format",
        choices=["text", "pdf"],
        default="text",
        help="Output format: text (extracted text) or pdf (native export)",
    )
    read_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (used with pdf format)",
    )
    read_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # slides commands
    slides_parser = subparsers.add_parser("slides", help="Slide operations")
    slides_subparsers = slides_parser.add_subparsers(dest="slides_command")

    slides_create_parser = slides_subparsers.add_parser("create", help="Add new slide")
    slides_create_parser.add_argument("presentation_id", help="Presentation ID")
    slides_create_parser.add_argument(
        "--layout", default="BLANK", help="Slide layout (BLANK, TITLE, TITLE_AND_BODY, etc.)"
    )
    slides_create_parser.add_argument("--index", type=int, help="Insert index (optional)")
    slides_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    slides_delete_parser = slides_subparsers.add_parser("delete", help="Delete a slide")
    slides_delete_parser.add_argument("presentation_id", help="Presentation ID")
    slides_delete_parser.add_argument("--slide-id", required=True, help="Slide object ID to delete")
    slides_delete_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # text commands
    text_parser = subparsers.add_parser("text", help="Text operations")
    text_subparsers = text_parser.add_subparsers(dest="text_command")

    text_insert_parser = text_subparsers.add_parser("insert", help="Insert text into slide")
    text_insert_parser.add_argument("presentation_id", help="Presentation ID")
    text_insert_parser.add_argument("--slide-id", required=True, help="Slide object ID")
    text_insert_parser.add_argument("--text", required=True, help="Text to insert")
    text_insert_parser.add_argument(
        "--x", type=float, default=100, help="X position in points (default: 100)"
    )
    text_insert_parser.add_argument(
        "--y", type=float, default=100, help="Y position in points (default: 100)"
    )
    text_insert_parser.add_argument(
        "--width", type=float, default=400, help="Text box width in points (default: 400)"
    )
    text_insert_parser.add_argument(
        "--height", type=float, default=100, help="Text box height in points (default: 100)"
    )
    text_insert_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # shapes commands
    shapes_parser = subparsers.add_parser("shapes", help="Shape operations")
    shapes_subparsers = shapes_parser.add_subparsers(dest="shapes_command")

    shapes_create_parser = shapes_subparsers.add_parser("create", help="Create a shape")
    shapes_create_parser.add_argument("presentation_id", help="Presentation ID")
    shapes_create_parser.add_argument("--slide-id", required=True, help="Slide object ID")
    shapes_create_parser.add_argument(
        "--shape-type", required=True, help="Shape type (RECTANGLE, ELLIPSE, TRIANGLE, etc.)"
    )
    shapes_create_parser.add_argument(
        "--x", type=float, default=100, help="X position in points (default: 100)"
    )
    shapes_create_parser.add_argument(
        "--y", type=float, default=100, help="Y position in points (default: 100)"
    )
    shapes_create_parser.add_argument(
        "--width", type=float, default=200, help="Width in points (default: 200)"
    )
    shapes_create_parser.add_argument(
        "--height", type=float, default=200, help="Height in points (default: 200)"
    )
    shapes_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # images commands
    images_parser = subparsers.add_parser("images", help="Image operations")
    images_subparsers = images_parser.add_subparsers(dest="images_command")

    images_create_parser = images_subparsers.add_parser("create", help="Create an image")
    images_create_parser.add_argument("presentation_id", help="Presentation ID")
    images_create_parser.add_argument("--slide-id", required=True, help="Slide object ID")
    images_create_parser.add_argument("--image-url", required=True, help="Image URL")
    images_create_parser.add_argument(
        "--x", type=float, default=100, help="X position in points (default: 100)"
    )
    images_create_parser.add_argument(
        "--y", type=float, default=100, help="Y position in points (default: 100)"
    )
    images_create_parser.add_argument(
        "--width", type=float, default=300, help="Width in points (default: 300)"
    )
    images_create_parser.add_argument(
        "--height", type=float, default=200, help="Height in points (default: 200)"
    )
    images_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

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
        elif args.command == "presentations":
            if args.presentations_command == "create":
                return cmd_presentations_create(args)
            elif args.presentations_command == "get":
                return cmd_presentations_get(args)
            elif args.presentations_command == "read":
                return cmd_presentations_read(args)
        elif args.command == "slides":
            if args.slides_command == "create":
                return cmd_slides_create(args)
            elif args.slides_command == "delete":
                return cmd_slides_delete(args)
        elif args.command == "text":
            if args.text_command == "insert":
                return cmd_text_insert(args)
        elif args.command == "shapes":
            if args.shapes_command == "create":
                return cmd_shapes_create(args)
        elif args.command == "images" and args.images_command == "create":
            return cmd_images_create(args)

        parser.print_help()
        return 1

    except (SlidesAPIError, AuthenticationError) as e:
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
