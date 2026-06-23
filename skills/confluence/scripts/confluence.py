#!/usr/bin/env python3
"""Confluence integration skill for AI agents.

This is a self-contained script that consolidates all Confluence functionality.

Usage:
    python confluence.py check
    python confluence.py search "type=page AND space = DEMO"
    python confluence.py page get "My Page Title"
    python confluence.py page create --space DEMO --title "New Page" --body "# Content"
    python confluence.py space list

Requirements:
    pip install --user requests keyring pyyaml
"""

from __future__ import annotations

# Standard library imports
import argparse
import contextlib
import json
import mimetypes
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ============================================================================
# DEPENDENCY CHECKS
# ============================================================================

try:
    import requests
except ImportError:
    print(
        "Error: 'requests' library not found. Install with: pip install --user requests",
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

try:
    from marklassian import markdown_to_adf as _marklassian_md_to_adf
except ImportError:
    print(
        "Error: 'marklassian' library not found. Install with: pip install --user marklassian",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import markdown as md_lib
except ImportError:
    print(
        "Error: 'markdown' library not found. Install with: pip install --user markdown",
        file=sys.stderr,
    )
    sys.exit(1)


# ============================================================================
# KEYRING CREDENTIAL STORAGE
# ============================================================================

SERVICE_NAME = "agent-skills"


def get_credential(key: str) -> str | None:
    """Get a credential from the system keyring.

    Args:
        key: The credential key (e.g., "confluence-token", "confluence-email").

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
# CREDENTIAL MANAGEMENT
# ============================================================================

CONFIG_DIR = Path.home() / ".config" / "agent-skills"


@dataclass
class Credentials:
    """Container for service credentials."""

    url: str | None = None
    email: str | None = None
    token: str | None = None
    username: str | None = None
    password: str | None = None

    def is_valid(self) -> bool:
        """Check if credentials are sufficient for authentication."""
        # Token-based auth
        if self.token and self.url:
            return True
        # Username/password auth
        return bool(self.username and self.password and self.url)


@dataclass
class ConfluenceDefaults:
    """Container for Confluence user defaults."""

    cql_scope: str | None = None
    max_results: int | None = None
    fields: list[str] | None = None
    default_space: str | None = None

    @staticmethod
    def from_config(config: dict[str, Any]) -> ConfluenceDefaults:
        """Load defaults from config dict.

        Args:
            config: Configuration dictionary.

        Returns:
            ConfluenceDefaults object with available values.
        """
        defaults_dict = config.get("defaults", {})
        return ConfluenceDefaults(
            cql_scope=defaults_dict.get("cql_scope"),
            max_results=defaults_dict.get("max_results"),
            fields=defaults_dict.get("fields"),
            default_space=defaults_dict.get("default_space"),
        )


@dataclass
class SpaceDefaults:
    """Container for space-specific defaults."""

    default_parent: str | None = None
    default_labels: list[str] | None = None

    @staticmethod
    def from_config(config: dict[str, Any], space: str) -> SpaceDefaults:
        """Load space defaults from config dict.

        Args:
            config: Configuration dictionary.
            space: Space key.

        Returns:
            SpaceDefaults object with available values.
        """
        spaces = config.get("spaces", {})
        space_dict = spaces.get(space, {})
        return SpaceDefaults(
            default_parent=space_dict.get("default_parent"),
            default_labels=space_dict.get("default_labels"),
        )


def get_credentials(service: str) -> Credentials:
    """Get credentials for a service using priority order.

    Priority:
    1. System keyring
    2. Environment variables
    3. Config file

    Args:
        service: Service name (e.g., "confluence").

    Returns:
        Credentials object with available values.
    """
    creds = Credentials()

    # 1. Try keyring first
    creds.url = get_credential(f"{service}-url")
    creds.email = get_credential(f"{service}-email")
    creds.token = get_credential(f"{service}-token")
    creds.username = get_credential(f"{service}-username")
    creds.password = get_credential(f"{service}-password")

    # 2. Fall back to environment variables
    prefix = service.upper().replace("-", "_")
    if not creds.url:
        creds.url = os.environ.get(f"{prefix}_URL")
    if not creds.email:
        creds.email = os.environ.get(f"{prefix}_EMAIL")
    if not creds.token:
        creds.token = os.environ.get(f"{prefix}_API_TOKEN") or os.environ.get(f"{prefix}_TOKEN")
    if not creds.username:
        creds.username = os.environ.get(f"{prefix}_USERNAME")
    if not creds.password:
        creds.password = os.environ.get(f"{prefix}_PASSWORD")

    # 3. Fall back to config file
    config = load_config(service)
    if config:
        if not creds.url:
            creds.url = config.get("url")
        if not creds.email:
            creds.email = config.get("email")
        if not creds.token:
            creds.token = config.get("token")
        if not creds.username:
            creds.username = config.get("username")
        if not creds.password:
            creds.password = config.get("password")

    return creds


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


def get_confluence_defaults() -> ConfluenceDefaults:
    """Get Confluence defaults from config file.

    Returns:
        ConfluenceDefaults object with available values, or empty defaults if not configured.
    """
    config = load_config("confluence")
    if not config:
        return ConfluenceDefaults()
    return ConfluenceDefaults.from_config(config)


def get_space_defaults(space: str) -> SpaceDefaults:
    """Get space-specific defaults from config file.

    Args:
        space: Space key.

    Returns:
        SpaceDefaults object with available values.
    """
    config = load_config("confluence")
    if not config:
        return SpaceDefaults()
    return SpaceDefaults.from_config(config, space)


def merge_cql_with_scope(user_cql: str, scope: str | None) -> str:
    """Merge user CQL with configured scope.

    Strategy: Prepend scope as a filter that's always applied.
    - If scope is None or empty, return user_cql unchanged
    - If user_cql is empty, return scope
    - Otherwise: "({scope}) AND ({user_cql})"

    Args:
        user_cql: CQL provided by user.
        scope: Configured CQL scope from defaults.

    Returns:
        Merged CQL query.
    """
    if not scope or not scope.strip():
        return user_cql

    if not user_cql or not user_cql.strip():
        return scope

    # Wrap both in parentheses to ensure correct precedence
    return f"({scope}) AND ({user_cql})"


# ============================================================================
# CONFLUENCE API HELPERS
# ============================================================================


def get_api_base() -> str:
    """Get the API base path for Confluence Cloud.

    Returns:
        "/wiki/rest/api" for Confluence Cloud.
    """
    return "/wiki/rest/api"


def api_path(endpoint: str) -> str:
    """Construct the full API path.

    Args:
        endpoint: API endpoint without base prefix (e.g., "content/search", "space").

    Returns:
        Full path (e.g., "/wiki/rest/api/content/search").
    """
    return f"/wiki/rest/api/{endpoint.lstrip('/')}"


# ============================================================================
# MARKDOWN CONVERSION UTILITIES
# ============================================================================

_TOC_ADF_NODE: dict[str, Any] = {
    "type": "extension",
    "attrs": {
        "extensionType": "com.atlassian.confluence.macro.core",
        "extensionKey": "toc",
        "parameters": {"macroParams": {"maxLevel": {"value": "3"}}},
    },
}

_CLOUD_PAGE_URL_RE = re.compile(r"/wiki/spaces/[^/]+/pages/(\d+)")


def _extract_page_id_from_url(url: str, confluence_url: str) -> str | None:
    """Extract a page ID from a Confluence URL if it belongs to this instance."""
    base = confluence_url.rstrip("/")
    if not url.startswith(base):
        return None

    match = _CLOUD_PAGE_URL_RE.search(url)
    if match:
        return match.group(1)

    return None


def _validate_page_exists(page_id: str) -> dict[str, Any] | None:
    """Check if a page exists, returning the page dict or None."""
    try:
        return get_page(page_id)
    except APIError:
        return None


def _adf_has_toc(adf: dict[str, Any]) -> bool:
    """Check whether ADF content contains a TOC extension macro."""
    for node in adf.get("content", []):
        if node.get("type") == "extension" and node.get("attrs", {}).get("extensionKey") == "toc":
            return True
    return False


def _prepend_toc_adf(adf: dict[str, Any]) -> dict[str, Any]:
    """Insert a TOC extension node at the start of ADF content."""
    adf["content"] = [_TOC_ADF_NODE, *adf["content"]]
    return adf


def extract_frontmatter(text: str) -> tuple[str, dict[str, str]]:
    """Extract frontmatter metadata from markdown text.

    Supports both ``---`` delimited YAML frontmatter and the Python-Markdown
    meta extension format (``Key: Value`` lines at the start).

    Args:
        text: Markdown text, possibly with frontmatter.

    Returns:
        Tuple of (body without frontmatter, metadata dict).
        Metadata values are strings (lists joined with commas).
    """
    md = md_lib.Markdown(extensions=["meta"])
    md.convert(text)
    meta_raw: dict[str, list[str]] = getattr(md, "Meta", {})
    meta = {k: ", ".join(v) for k, v in meta_raw.items()}
    stripped = _strip_frontmatter(text)
    return stripped, meta


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (``---`` delimited) from text."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :].lstrip("\n")
    return text


def markdown_to_adf(markdown: str, *, include_toc: bool = False) -> dict[str, Any]:
    """Convert Markdown to ADF (Atlassian Document Format).

    Args:
        markdown: Markdown string.
        include_toc: Prepend a table of contents macro.

    Returns:
        ADF JSON structure.
    """
    adf = dict(_marklassian_md_to_adf(markdown))
    if include_toc:
        _prepend_toc_adf(adf)
    return adf


def adf_to_markdown(
    adf: dict[str, Any],
    *,
    attachments: dict[str, dict[str, Any]] | None = None,
    image_dir: Path | None = None,
) -> str:
    """Convert ADF (Atlassian Document Format) to Markdown.

    Args:
        adf: ADF JSON structure.
        attachments: Attachment ID → metadata mapping for resolving images.
        image_dir: Local directory where images were downloaded (for relative paths).

    Returns:
        Markdown string.
    """
    if not adf or adf.get("type") != "doc":
        return ""

    result = []
    content = adf.get("content", [])

    for node in content:
        node_type = node.get("type")

        if node_type == "paragraph":
            para_text = _adf_content_to_text(
                node.get("content", []), attachments=attachments, image_dir=image_dir
            )
            if para_text:
                result.append(para_text)

        elif node_type == "heading":
            level = node.get("attrs", {}).get("level", 1)
            heading_text = _adf_content_to_text(
                node.get("content", []), attachments=attachments, image_dir=image_dir
            )
            result.append(f"{'#' * level} {heading_text}")

        elif node_type == "codeBlock":
            lang = node.get("attrs", {}).get("language", "")
            code_text = _adf_content_to_text(node.get("content", []))
            result.append(f"```{lang}\n{code_text}\n```")

        elif node_type == "bulletList":
            for item in node.get("content", []):
                if item.get("type") == "listItem":
                    item_text = ""
                    for item_content in item.get("content", []):
                        if item_content.get("type") == "paragraph":
                            item_text = _adf_content_to_text(
                                item_content.get("content", []),
                                attachments=attachments,
                                image_dir=image_dir,
                            )
                    result.append(f"- {item_text}")

        elif node_type == "orderedList":
            for idx, item in enumerate(node.get("content", []), 1):
                if item.get("type") == "listItem":
                    item_text = ""
                    for item_content in item.get("content", []):
                        if item_content.get("type") == "paragraph":
                            item_text = _adf_content_to_text(
                                item_content.get("content", []),
                                attachments=attachments,
                                image_dir=image_dir,
                            )
                    result.append(f"{idx}. {item_text}")

        elif node_type in ("mediaSingle", "mediaGroup"):
            for child in node.get("content", []):
                img_md = _media_node_to_markdown(
                    child, attachments=attachments, image_dir=image_dir
                )
                if img_md:
                    result.append(img_md)

    return "\n\n".join(result)


def _media_node_to_markdown(
    node: dict[str, Any],
    *,
    attachments: dict[str, dict[str, Any]] | None = None,
    image_dir: Path | None = None,
) -> str:
    """Convert an ADF media node to markdown image syntax."""
    if node.get("type") not in ("media", "mediaInline"):
        return ""

    attrs = node.get("attrs", {})
    alt = attrs.get("alt", "")
    media_type = attrs.get("type", "")

    if media_type == "external":
        url = attrs.get("url", "")
        if image_dir and url:
            filename = url.rsplit("/", 1)[-1] if "/" in url else ""
            if filename:
                return f"![{alt}]({image_dir / filename})"
        return f"![{alt}]({url})" if url else ""

    att_id = attrs.get("id", "")
    att_meta = (attachments or {}).get(att_id, {})
    filename = att_meta.get("title", "")

    if image_dir and filename:
        return f"![{alt}]({image_dir / filename})"
    elif att_meta.get("download"):
        return f"![{alt}]({att_meta['download']})"
    elif filename:
        return f"![{alt}]({filename})"
    return f"![{alt}](attachment:{att_id})"


def _adf_content_to_text(
    content: list[dict[str, Any]],
    *,
    attachments: dict[str, dict[str, Any]] | None = None,
    image_dir: Path | None = None,
) -> str:
    """Convert ADF content nodes to text with Markdown formatting."""
    result = []

    for node in content:
        if node.get("type") == "text":
            text = node.get("text", "")
            marks = node.get("marks", [])

            for mark in marks:
                mark_type = mark.get("type")
                if mark_type == "strong":
                    text = f"**{text}**"
                elif mark_type == "em":
                    text = f"*{text}*"
                elif mark_type == "code":
                    text = f"`{text}`"
                elif mark_type == "link":
                    href = mark.get("attrs", {}).get("href", "")
                    text = f"[{text}]({href})"

            result.append(text)

        elif node.get("type") in ("media", "mediaInline"):
            img_md = _media_node_to_markdown(node, attachments=attachments, image_dir=image_dir)
            if img_md:
                result.append(img_md)

    return "".join(result)


def format_content(
    content: str, input_format: str = "markdown", *, include_toc: bool = False
) -> dict[str, Any] | str:
    """Main content formatting function.

    Args:
        content: Content string.
        input_format: "markdown" or "editor".
        include_toc: Prepend a table of contents macro.

    Returns:
        Formatted content for API.
    """
    if input_format == "markdown":
        return markdown_to_adf(content, include_toc=include_toc)
    elif input_format == "editor":
        if isinstance(content, str):
            content = json.loads(content)
        return content

    return content


# ============================================================================
# HTTP/REST UTILITIES
# ============================================================================


class APIError(Exception):
    """Exception raised for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: Any = None,
        request_body: Any = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        self.request_body = request_body

    def verbose_message(self) -> str:
        parts = [str(self)]
        if self.response:
            try:
                body = (
                    json.loads(self.response) if isinstance(self.response, str) else self.response
                )
                parts.append(f"Response: {json.dumps(body, indent=2)}")
            except (json.JSONDecodeError, TypeError):
                parts.append(f"Response: {self.response}")
        if self.request_body:
            try:
                parts.append(f"Request body: {json.dumps(self.request_body, indent=2)}")
            except (TypeError, ValueError):
                parts.append(f"Request body: {self.request_body}")
        return "\n".join(parts)


def make_request(
    service: str,
    method: str,
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any] | list[Any]:
    """Make an authenticated HTTP request to a service.

    Args:
        service: Service name (e.g., "confluence").
        method: HTTP method (GET, POST, PUT, DELETE).
        endpoint: API endpoint path (will be appended to base URL).
        params: Query parameters.
        json_data: JSON body data.
        files: Files for multipart/form-data upload.
        headers: Additional headers.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response.

    Raises:
        APIError: If the request fails or credentials are missing.
    """
    creds = get_credentials(service)
    if not creds.is_valid():
        raise APIError(f"No valid credentials found for {service}. Run: python confluence.py check")

    url = f"{creds.url.rstrip('/')}/{endpoint.lstrip('/')}"

    # Build headers with authentication
    request_headers = headers.copy() if headers else {}
    if not files:
        request_headers.setdefault("Content-Type", "application/json")
    request_headers.setdefault("Accept", "application/json")

    # Add authentication
    auth = None
    if creds.email and creds.token:
        auth = (creds.email, creds.token)
    elif creds.token:
        request_headers["Authorization"] = f"Bearer {creds.token}"
    elif creds.username and creds.password:
        auth = (creds.username, creds.password)

    response = requests.request(
        method=method.upper(),
        url=url,
        params=params,
        json=json_data if not files else None,
        files=files,
        headers=request_headers,
        auth=auth,
        timeout=timeout,
    )

    if not response.ok:
        raise APIError(
            f"{method.upper()} {endpoint} failed: {response.status_code} {response.reason}",
            status_code=response.status_code,
            response=response.text,
            request_body=json_data,
        )

    if response.status_code == 204:
        return {}

    return response.json()


def get(service: str, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
    """Make a GET request to a service."""
    return make_request(service, "GET", endpoint, **kwargs)


def post(
    service: str, endpoint: str, data: dict[str, Any], **kwargs: Any
) -> dict[str, Any] | list[Any]:
    """Make a POST request to a service."""
    return make_request(service, "POST", endpoint, json_data=data, **kwargs)


def put(
    service: str, endpoint: str, data: dict[str, Any], **kwargs: Any
) -> dict[str, Any] | list[Any]:
    """Make a PUT request to a service."""
    return make_request(service, "PUT", endpoint, json_data=data, **kwargs)


def delete(service: str, endpoint: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
    """Make a DELETE request to a service."""
    return make_request(service, "DELETE", endpoint, **kwargs)


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_json(data: Any, *, indent: int = 2) -> str:
    """Format data as JSON string.

    Args:
        data: Data to format.
        indent: Indentation level.

    Returns:
        Formatted JSON string.
    """
    return json.dumps(data, indent=indent, default=str)


def format_table(
    rows: list[dict[str, Any]],
    columns: list[str],
    *,
    headers: dict[str, str] | None = None,
    max_width: int = 50,
) -> str:
    """Format data as a text table.

    Args:
        rows: List of dictionaries containing row data.
        columns: List of column keys to display.
        headers: Optional mapping of column keys to display headers.
        max_width: Maximum width for any column.

    Returns:
        Formatted table string.
    """
    if not rows:
        return "No data"

    headers = headers or {}

    # Calculate column widths
    widths: dict[str, int] = {}
    for col in columns:
        header = headers.get(col, col)
        max_val_width = max(len(_truncate(str(row.get(col, "")), max_width)) for row in rows)
        widths[col] = min(max(len(header), max_val_width), max_width)

    # Build header row
    header_parts = []
    for col in columns:
        header = headers.get(col, col)
        header_parts.append(header.ljust(widths[col]))
    header_line = " | ".join(header_parts)

    # Build separator
    separator = "-+-".join("-" * widths[col] for col in columns)

    # Build data rows
    data_lines = []
    for row in rows:
        parts = []
        for col in columns:
            value = _truncate(str(row.get(col, "")), widths[col])
            parts.append(value.ljust(widths[col]))
        data_lines.append(" | ".join(parts))

    return "\n".join([header_line, separator, *data_lines])


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_page(
    page: dict[str, Any],
    *,
    include_body: bool = False,
    as_markdown: bool = True,
    attachments: dict[str, dict[str, Any]] | None = None,
    image_dir: Path | None = None,
) -> str:
    """Format a Confluence page for display.

    Args:
        page: Confluence page dictionary.
        include_body: Whether to include page body.
        as_markdown: If True, convert body to Markdown.
        attachments: Attachment ID → metadata mapping for resolving images.
        image_dir: Local directory where images were downloaded.

    Returns:
        Formatted page string.
    """
    page_id = page.get("id", "N/A")
    title = page.get("title", "No title")
    page_type = page.get("type", "page")
    status = page.get("status", "current")

    space = page.get("space", {})
    space_key = space.get("key", "Unknown") if space else "Unknown"

    version_info = page.get("version", {})
    version = version_info.get("number", "1") if version_info else "1"

    result = (
        f"### {title}\n"
        f"- **Page ID:** {page_id}\n"
        f"- **Type:** {page_type}\n"
        f"- **Space:** {space_key}\n"
        f"- **Status:** {status}\n"
        f"- **Version:** {version}"
    )

    if include_body:
        body = page.get("body", {})
        if as_markdown:
            if "atlas_doc_format" in body:
                editor_value = body["atlas_doc_format"].get("value", {})
                if isinstance(editor_value, str):
                    editor_value = json.loads(editor_value)
                markdown_body = adf_to_markdown(
                    editor_value, attachments=attachments, image_dir=image_dir
                )
            else:
                markdown_body = "(No content available)"

            result += f"\n\n---\n\n{markdown_body}"
        else:
            # Raw format
            result += f"\n\nBody: {json.dumps(body, indent=2)}"

    return result


def format_page_with_frontmatter(
    page: dict[str, Any],
    *,
    attachments: dict[str, dict[str, Any]] | None = None,
    image_dir: Path | None = None,
) -> str:
    """Format a page as markdown with YAML frontmatter for round-tripping."""
    page_id = page.get("id", "")
    title = page.get("title", "")
    space = page.get("space", {})
    space_key = space.get("key", "") if space else ""
    version_info = page.get("version", {})
    version = version_info.get("number", 1) if version_info else 1

    # Extract labels if expanded
    labels_list = []
    metadata = page.get("metadata", {})
    if metadata:
        label_objs = metadata.get("labels", {}).get("results", [])
        labels_list = [lb.get("name", "") for lb in label_objs if lb.get("name")]

    # Extract ancestors (parent)
    ancestors = page.get("ancestors", [])
    parent_id = ancestors[-1].get("id", "") if ancestors else ""

    # Build frontmatter
    fm_lines = ["---"]
    fm_lines.append(f"title: {title}")
    fm_lines.append(f"space: {space_key}")
    fm_lines.append(f"page_id: {page_id}")
    fm_lines.append(f"version: {version}")
    if parent_id:
        fm_lines.append(f"parent: {parent_id}")
    if labels_list:
        fm_lines.append(f"labels: {', '.join(labels_list)}")
    fm_lines.append("---")

    # Extract body as markdown and detect TOC macro
    body = page.get("body", {})
    if "atlas_doc_format" in body:
        editor_value = body["atlas_doc_format"].get("value", {})
        if isinstance(editor_value, str):
            editor_value = json.loads(editor_value)
        if _adf_has_toc(editor_value):
            fm_lines.insert(-1, "toc: true")
        md_body = adf_to_markdown(editor_value, attachments=attachments, image_dir=image_dir)
    else:
        md_body = ""

    return "\n".join(fm_lines) + "\n\n" + md_body


def format_pages_list(pages: list[dict[str, Any]]) -> str:
    """Format a list of Confluence pages for display.

    Args:
        pages: List of Confluence page dictionaries.

    Returns:
        Formatted table string.
    """
    if not pages:
        return "No pages found"

    parts = []
    for page in pages:
        space = page.get("space", {})
        space_key = space.get("key", "Unknown") if space else "Unknown"
        page_id = page.get("id", "N/A")
        title = page.get("title", "No title")
        page_type = page.get("type", "page")

        parts.append(
            f"### {title}\n"
            f"- **Page ID:** {page_id}\n"
            f"- **Type:** {page_type}\n"
            f"- **Space:** {space_key}"
        )

    return "\n\n".join(parts)


# ============================================================================
# SEARCH FUNCTIONALITY
# ============================================================================

DEFAULT_FIELDS = ["id", "type", "status", "title", "space"]


def search_content(
    cql: str,
    max_results: int = 50,
    content_type: str | None = None,
    space: str | None = None,
) -> list[dict[str, Any]]:
    """Search for content using CQL (Confluence Query Language).

    Args:
        cql: CQL query string.
        max_results: Maximum number of results to return.
        content_type: Filter by type (page, blogpost, comment).
        space: Limit search to specific space.

    Returns:
        List of content dictionaries.

    Raises:
        APIError: If the search fails.

    Example:
        >>> search_content("type=page AND space=DEMO")
        >>> search_content("title~login", space="DEMO")
    """
    # Build query with filters
    query_parts = []
    if space:
        query_parts.append(f"space={space}")
    if content_type:
        query_parts.append(f"type={content_type}")
    if cql:
        query_parts.append(cql)

    final_cql = " AND ".join(f"({part})" for part in query_parts) if query_parts else ""

    params = {
        "cql": final_cql,
        "limit": max_results,
    }

    response = get(
        "confluence",
        api_path("content/search"),
        params=params,
    )

    if isinstance(response, dict):
        return response.get("results", [])
    return []


# ============================================================================
# PAGE MANAGEMENT
# ============================================================================


def get_page(
    page_identifier: str,
    *,
    expand: list[str] | None = None,
) -> dict[str, Any]:
    """Get a page by ID or title.

    Args:
        page_identifier: Page ID or title.
        expand: Fields to expand (e.g., ["body.storage", "version"]).

    Returns:
        Page dictionary.

    Raises:
        APIError: If page not found or request fails.
    """
    # Check if it's a numeric ID
    if page_identifier.isdigit():
        # Get by ID
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        response = get("confluence", api_path(f"content/{page_identifier}"), params=params)
        if isinstance(response, dict):
            return response
        return {}
    else:
        # Search by title
        cql = f'title="{page_identifier}"'
        results = search_content(cql, max_results=1)
        if not results:
            raise APIError(f"Page not found: {page_identifier}")

        page_id = results[0]["id"]
        # Get full page data with expansions
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        response = get("confluence", api_path(f"content/{page_id}"), params=params)
        if isinstance(response, dict):
            return response
        return {}


_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def extract_local_images(body: str, base_dir: Path) -> tuple[str, list[dict[str, Any]]]:
    """Extract local image references from markdown.

    URL-based images are left as-is. Missing files produce a warning
    and are left unchanged.

    Args:
        body: Markdown text.
        base_dir: Directory to resolve relative image paths against.

    Returns:
        Tuple of (body with local images removed, list of image dicts).
    """
    images: list[dict[str, Any]] = []

    def _replace(match: re.Match) -> str:
        alt = match.group(1)
        raw_path = match.group(2)

        if raw_path.startswith(("http://", "https://")):
            return match.group(0)

        resolved = (base_dir / raw_path).resolve()
        if not resolved.is_file():
            print(f"Warning: image not found: {resolved}", file=sys.stderr)
            return match.group(0)

        images.append(
            {
                "alt": alt,
                "path": resolved,
                "original_ref": raw_path,
                "original": match.group(0),
            }
        )
        return ""

    stripped = _IMAGE_RE.sub(_replace, body)
    return stripped, images


def upload_attachment(page_id: str, file_path: Path) -> dict[str, Any]:
    """Upload a file as a page attachment.

    Args:
        page_id: Confluence page ID.
        file_path: Local path to the file.

    Returns:
        Attachment metadata from the API response.

    Raises:
        APIError: If the upload fails.
    """
    endpoint = api_path(f"content/{page_id}/child/attachment")
    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "application/octet-stream"

    return make_request(
        "confluence",
        "POST",
        endpoint,
        files={"file": (file_path.name, open(file_path, "rb"), mime_type)},
        headers={"X-Atlassian-Token": "nocheck"},
    )


def replace_image_paths(body: str, replacements: dict[str, str]) -> str:
    """Replace local image paths with download URLs in markdown.

    Args:
        body: Original markdown text.
        replacements: Mapping of original path to download URL.

    Returns:
        Modified markdown with paths replaced.
    """
    for original_ref, url in replacements.items():
        body = body.replace(f"]({original_ref})", f"]({url})")
    return body


def _upload_images_and_build_urls(page_id: str, images: list[dict[str, Any]]) -> dict[str, str]:
    """Upload images as attachments and return path-to-URL mapping.

    Args:
        page_id: Confluence page ID.
        images: Image dicts from extract_local_images.

    Returns:
        Dict mapping original_ref to download URL.
    """
    creds = get_credentials("confluence")
    base_url = creds.url.rstrip("/")
    replacements: dict[str, str] = {}

    for img in images:
        try:
            upload_attachment(page_id, img["path"])
            download_url = f"{base_url}/wiki/download/attachments/{page_id}/{img['path'].name}"
            replacements[img["original_ref"]] = download_url
        except APIError as e:
            print(f"Warning: failed to upload {img['path'].name}: {e}", file=sys.stderr)

    return replacements


_IMAGE_MIME_PREFIXES = ("image/",)


def list_attachments(page_id: str) -> dict[str, dict[str, Any]]:
    """Fetch attachments for a page, keyed by attachment ID.

    Args:
        page_id: Confluence page ID.

    Returns:
        Dict mapping attachment ID to metadata (title, download link, mediaType).
    """
    endpoint = api_path(f"content/{page_id}/child/attachment")
    response = get("confluence", endpoint, params={"limit": 100})
    results = response.get("results", []) if isinstance(response, dict) else response
    attachments: dict[str, dict[str, Any]] = {}
    for att in results:
        att_id = att.get("extensions", {}).get("fileId", "") or att.get("id", "")
        attachments[att_id] = {
            "title": att.get("title", ""),
            "download": att.get("_links", {}).get("download", ""),
            "mediaType": att.get("extensions", {}).get("mediaType", ""),
        }
    return attachments


def download_attachment(download_path: str, filename: str, output_dir: Path) -> Path:
    """Download a page attachment to a local directory.

    Args:
        download_path: Relative download path from attachment metadata.
        filename: Filename to save as.
        output_dir: Directory to save the file.

    Returns:
        Path to the downloaded file.
    """
    creds = get_credentials("confluence")
    base_url = creds.url.rstrip("/")
    api_base = get_api_base()
    prefix = api_base.rsplit("/rest/api", 1)[0]
    download_url = f"{base_url}{prefix}{download_path}"

    auth = None
    if creds.email and creds.token:
        auth = (creds.email, creds.token)
    elif creds.username and creds.password:
        auth = (creds.username, creds.password)

    headers: dict[str, str] = {}
    if creds.token and not (creds.email or creds.username):
        headers["Authorization"] = f"Bearer {creds.token}"

    response = requests.get(download_url, auth=auth, headers=headers, timeout=30)
    response.raise_for_status()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_bytes(response.content)
    return output_path


def _download_external_images(
    adf: dict[str, Any],
    output_dir: Path,
    att_map: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Download external images referenced in ADF content.

    Matches external URLs to attachments by filename and uses the
    authenticated REST API download path.
    """
    att_by_name: dict[str, dict[str, Any]] = {}
    for att in (att_map or {}).values():
        att_by_name[att.get("title", "")] = att

    for node in adf.get("content", []):
        if node.get("type") not in ("mediaSingle", "mediaGroup"):
            continue
        for child in node.get("content", []):
            attrs = child.get("attrs", {})
            if attrs.get("type") != "external":
                continue
            url = attrs.get("url", "")
            if not url:
                continue
            filename = url.rsplit("/", 1)[-1] if "/" in url else ""
            if not filename:
                continue
            att = att_by_name.get(filename)
            if att and att.get("download"):
                try:
                    download_attachment(att["download"], filename, output_dir)
                except Exception as exc:
                    print(f"Warning: failed to download {filename}: {exc}", file=sys.stderr)
            else:
                print(
                    f"Warning: no attachment match for external image {filename}", file=sys.stderr
                )


def create_page(
    space: str,
    title: str,
    body: str,
    *,
    parent_id: str | None = None,
    body_format: str = "markdown",
    labels: list[str] | None = None,
    include_toc: bool = False,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Create a new page.

    Args:
        space: Space key.
        title: Page title.
        body: Page content.
        parent_id: Parent page ID for hierarchy.
        body_format: Format of body content ("markdown" or "editor").
        labels: List of labels to add.
        include_toc: Prepend a table of contents macro.
        base_dir: Directory for resolving local image paths.

    Returns:
        Created page dictionary with ``image_count`` key if images were uploaded.

    Raises:
        APIError: If creation fails.
    """
    images: list[dict[str, Any]] = []
    original_body = body
    if base_dir and body_format == "markdown":
        body, images = extract_local_images(body, base_dir)

    # Convert body to appropriate format
    if body_format == "markdown":
        body_content = json.dumps(markdown_to_adf(body, include_toc=include_toc))
        body_representation = "atlas_doc_format"
        body_key = "editor"
    elif body_format == "editor":
        body_content = body if isinstance(body, str) else json.dumps(body)
        body_representation = "atlas_doc_format"
        body_key = "editor"
    else:
        raise APIError(f"Unknown body format: {body_format}")

    # Build page data
    page_data: dict[str, Any] = {
        "type": "page",
        "title": title,
        "space": {"key": space},
        "body": {
            body_key: {
                "value": body_content,
                "representation": body_representation,
            }
        },
    }

    if parent_id:
        page_data["ancestors"] = [{"id": parent_id}]

    if labels:
        page_data["metadata"] = {"labels": [{"name": label} for label in labels]}

    response = post("confluence", api_path("content"), page_data)
    page = response if isinstance(response, dict) else {}

    if images and page.get("id"):
        replacements = _upload_images_and_build_urls(page["id"], images)
        if replacements:
            full_body = replace_image_paths(original_body, replacements)
            update_page(
                page["id"],
                body=full_body,
                body_format="markdown",
                include_toc=include_toc,
            )
        page["image_count"] = len(images)

    return page


def update_page(
    page_id: str,
    *,
    title: str | None = None,
    body: str | None = None,
    body_format: str = "markdown",
    version: int | None = None,
    include_toc: bool = False,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Update an existing page.

    Args:
        page_id: Page ID to update.
        title: New title (optional).
        body: New content (optional).
        body_format: Format of body content ("markdown" or "editor").
        version: Current version number (will auto-detect if not provided).
        include_toc: Prepend a table of contents macro.
        base_dir: Directory for resolving local image paths.

    Returns:
        Updated page dictionary with ``image_count`` key if images were uploaded.

    Raises:
        APIError: If update fails or version conflict.
    """
    image_count = 0
    if base_dir and body and body_format == "markdown":
        _, images = extract_local_images(body, base_dir)
        if images:
            replacements = _upload_images_and_build_urls(page_id, images)
            body = replace_image_paths(body, replacements)
            image_count = len(images)

    # Fetch current page for version and title when not explicitly provided
    if version is None or title is None:
        current_page = get_page(page_id, expand=["version"])
        if version is None:
            version = current_page.get("version", {}).get("number", 1)
        if title is None:
            title = current_page.get("title", "")

    # Build update data
    update_data: dict[str, Any] = {
        "version": {"number": version + 1},
        "type": "page",
        "title": title,
    }

    if body:
        # Convert body to appropriate format
        if body_format == "markdown":
            body_content = json.dumps(markdown_to_adf(body, include_toc=include_toc))
            body_representation = "atlas_doc_format"
            body_key = "editor"
        elif body_format == "editor":
            body_content = body if isinstance(body, str) else json.dumps(body)
            body_representation = "atlas_doc_format"
            body_key = "editor"
        else:
            raise APIError(f"Unknown body format: {body_format}")

        update_data["body"] = {
            body_key: {
                "value": body_content,
                "representation": body_representation,
            }
        }

    response = put("confluence", api_path(f"content/{page_id}"), update_data)
    page = response if isinstance(response, dict) else {}
    if image_count:
        page["image_count"] = image_count
    return page


def move_page(page_id: str, parent_id: str | None) -> dict[str, Any]:
    """Move a page under a new parent (or to the space root).

    Args:
        page_id: Page ID to move.
        parent_id: New parent page ID, or None to move to the space root.

    Returns:
        Updated page dictionary.

    Raises:
        APIError: If move fails.
    """
    current_page = get_page(page_id, expand=["version"])
    version = current_page.get("version", {}).get("number", 1)
    title = current_page.get("title", "")

    update_data: dict[str, Any] = {
        "version": {"number": version + 1},
        "type": "page",
        "title": title,
        "ancestors": [{"id": parent_id}] if parent_id else [],
    }

    response = put("confluence", api_path(f"content/{page_id}"), update_data)
    if isinstance(response, dict):
        return response
    return {}


def delete_page(page_id: str) -> dict[str, Any]:
    """Delete a page (moves to trash on Cloud).

    Args:
        page_id: Page ID to delete.

    Returns:
        Empty dict on success (204 No Content).

    Raises:
        APIError: If deletion fails.
    """
    return delete("confluence", api_path(f"content/{page_id}"))


# ============================================================================
# SPACE MANAGEMENT
# ============================================================================


def list_spaces(
    *,
    space_type: str | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List spaces.

    Args:
        space_type: Filter by space type ("global", "personal").
        max_results: Maximum results to return.

    Returns:
        List of space dictionaries.
    """
    params: dict[str, Any] = {
        "limit": max_results,
    }

    if space_type:
        params["type"] = space_type

    response = get("confluence", api_path("space"), params=params)

    if isinstance(response, dict):
        return response.get("results", [])
    return []


def get_space(space_key: str, *, expand: list[str] | None = None) -> dict[str, Any]:
    """Get space details.

    Args:
        space_key: Space key.
        expand: Fields to expand.

    Returns:
        Space dictionary.
    """
    params = {}
    if expand:
        params["expand"] = ",".join(expand)

    response = get("confluence", api_path(f"space/{space_key}"), params=params)
    if isinstance(response, dict):
        return response
    return {}


def create_space(
    key: str,
    name: str,
    *,
    description: str | None = None,
    space_type: str = "global",
) -> dict[str, Any]:
    """Create a new space.

    Args:
        key: Space key (short identifier).
        name: Space name.
        description: Space description.
        space_type: Space type ("global" or "personal").

    Returns:
        Created space dictionary.

    Raises:
        APIError: If creation fails (may require permissions).
    """
    space_data: dict[str, Any] = {
        "key": key,
        "name": name,
        "type": space_type,
    }

    if description:
        space_data["description"] = {
            "plain": {
                "value": description,
                "representation": "plain",
            }
        }

    response = post("confluence", api_path("space"), space_data)
    if isinstance(response, dict):
        return response
    return {}


def get_space_permissions(space_key: str) -> list[dict[str, Any]]:
    """Get permissions for a space.

    Args:
        space_key: Space key.

    Returns:
        List of permission dictionaries.
    """
    space = get_space(space_key, expand=["permissions"])
    return space.get("permissions", [])


def add_space_permission(
    space_key: str,
    subject_type: str,
    subject_id: str,
    operation_key: str,
    target: str,
) -> dict[str, Any]:
    """Add a permission to a space.

    Args:
        space_key: Space key.
        subject_type: "user" or "group".
        subject_id: User account ID or group name/ID.
        operation_key: Operation key (read, create, delete, administer, etc.).
        target: Target type (space, page, blogpost, comment, attachment).

    Returns:
        Created permission dictionary.

    Raises:
        APIError: If creation fails.
    """
    permission_data = {
        "subject": {
            "type": subject_type,
            "identifier": subject_id,
        },
        "operation": {
            "key": operation_key,
            "target": target,
        },
    }

    response = post("confluence", api_path(f"space/{space_key}/permission"), permission_data)
    if isinstance(response, dict):
        return response
    return {}


def remove_space_permission(space_key: str, permission_id: int) -> dict[str, Any]:
    """Remove a permission from a space.

    Args:
        space_key: Space key.
        permission_id: Permission ID to remove.

    Returns:
        Empty dict on success (204 No Content).

    Raises:
        APIError: If deletion fails.
    """
    return delete("confluence", api_path(f"space/{space_key}/permission/{permission_id}"))


# ============================================================================
# CHECK COMMAND - Validates configuration and connectivity
# ============================================================================


def cmd_check() -> int:
    """Validate Confluence configuration and connectivity.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Checking Confluence configuration...\n")

    # 1. Check credentials
    print("1. Checking credentials...")
    creds = get_credentials("confluence")

    if not creds.url:
        print("   ERROR: No Confluence URL configured")
        print("\n   Configure using one of these methods:")
        print("   - Environment: export CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki")
        print("   - Config file: ~/.config/agent-skills/confluence.yaml")
        print("   - Keyring: Use a setup script to store in system keyring")
        return 1

    print(f"   URL: {creds.url}")

    if creds.url.rstrip("/").endswith("/wiki"):
        base = creds.url.rstrip("/")[: -len("/wiki")]
        print("   ERROR: URL must not include the /wiki path suffix.")
        print("   The skill adds the correct API path automatically.")
        print(f"   Update your configuration to use: {base}")
        return 1

    if not creds.token:
        print("   ERROR: No API token configured")
        print("\n   Configure using one of these methods:")
        print("   - Environment: export CONFLUENCE_API_TOKEN=your-token-here")
        if "atlassian.net" in creds.url:
            print("   - Also set: export CONFLUENCE_EMAIL=your-email@example.com")
        print("   - Config file: ~/.config/agent-skills/confluence.yaml")
        print("   - Keyring: Use a setup script to store in system keyring")
        return 1

    print(f"   Token: {'*' * 8} (configured)")

    if creds.email:
        print(f"   Email: {creds.email}")

    if not creds.is_valid():
        print("   ERROR: Invalid credentials")
        return 1

    print("   Credentials: OK\n")

    # 2. Test API access
    print("2. Testing API access...")
    try:
        # Try to list spaces
        response = get(
            "confluence",
            api_path("space"),
            params={"limit": 1},
        )
        if isinstance(response, dict) and "results" in response:
            print("   API access: OK\n")
        else:
            print("   WARNING: Unexpected response format")
    except APIError as e:
        print(f"   ERROR: {e.verbose_message()}")
        return 1
    except Exception as e:
        print(f"   ERROR: {e}")
        return 1

    print()
    print("All checks passed!")
    print("\nYou can now use commands like:")
    print('  python confluence.py search "type=page AND space=DEMO"')
    print('  python confluence.py page get "Page Title"')
    print("  python confluence.py space list")

    return 0


# ============================================================================
# COMMAND HANDLERS
# ============================================================================


def cmd_search(args: argparse.Namespace) -> int:
    """Handle search command."""
    try:
        # Load defaults
        defaults = get_confluence_defaults()

        # Apply CQL scope
        cql = merge_cql_with_scope(args.cql, defaults.cql_scope)

        # Apply max_results
        max_results = (
            args.max_results if args.max_results is not None else (defaults.max_results or 50)
        )

        # Apply space filter
        space = args.space or defaults.default_space

        results = search_content(cql, max_results, args.type, space)

        if args.json:
            print(format_json(results))
        else:
            print(format_pages_list(results))

        return 0

    except Exception as e:
        msg = e.verbose_message() if isinstance(e, APIError) else str(e)
        print(f"Error: {msg}", file=sys.stderr)
        return 1


def cmd_page(args: argparse.Namespace) -> int:
    """Handle page command."""
    try:
        if args.page_command == "get":
            # Determine what to expand
            expand = ["body.atlas_doc_format", "version", "space"]
            if args.expand:
                expand = args.expand.split(",")

            if args.frontmatter:
                expand = [
                    "body.atlas_doc_format",
                    "version",
                    "space",
                    "metadata.labels",
                    "ancestors",
                ]

            page = get_page(args.page_identifier, expand=expand)
            page_id = page.get("id", "")

            att_map: dict[str, dict[str, Any]] | None = None
            image_dir: Path | None = None
            wants_markdown = not args.json and (args.frontmatter or args.markdown or not args.raw)

            # Download images only when writing to a file
            if page_id and wants_markdown and args.output:
                output_path = Path(args.output)
                image_dir = output_path.parent / output_path.stem
                try:
                    att_map = list_attachments(page_id)
                    image_atts = {
                        k: v
                        for k, v in att_map.items()
                        if v.get("mediaType", "").startswith("image/")
                    }
                    for att in image_atts.values():
                        filename = att.get("title", "")
                        dl_path = att.get("download", "")
                        if filename and dl_path:
                            try:
                                download_attachment(dl_path, filename, image_dir)
                            except Exception as exc:
                                print(
                                    f"Warning: failed to download {filename}: {exc}",
                                    file=sys.stderr,
                                )
                except APIError as exc:
                    print(f"Warning: failed to fetch attachments: {exc}", file=sys.stderr)

                body = page.get("body", {})
                adf_body = body.get("atlas_doc_format", {}).get("value", "")
                if isinstance(adf_body, str) and adf_body:
                    try:
                        adf = json.loads(adf_body)
                        _download_external_images(adf, image_dir, att_map=att_map)
                    except (json.JSONDecodeError, Exception):
                        pass

            if args.frontmatter:
                output = format_page_with_frontmatter(
                    page, attachments=att_map, image_dir=image_dir
                )
            elif args.json:
                output = format_json(page)
            else:
                include_body = not args.no_body
                as_markdown = args.markdown or not args.raw
                output = format_page(
                    page,
                    include_body=include_body,
                    as_markdown=as_markdown,
                    attachments=att_map,
                    image_dir=image_dir,
                )

            if args.output:
                Path(args.output).write_text(output)
                print(f"Saved to: {args.output}")
            else:
                print(output)

        elif args.page_command == "create":
            # Get body content
            base_dir = None
            if args.body_file:
                body_path = Path(args.body_file)
                base_dir = body_path.parent
                with open(body_path) as f:
                    body = f.read()
            elif args.body:
                body = args.body
            else:
                body = ""

            # Extract frontmatter metadata (CLI flags take precedence)
            meta: dict[str, str] = {}
            if args.format == "markdown":
                body, meta = extract_frontmatter(body)

            space = args.space or meta.get("space", "")
            title = args.title or meta.get("title", "")
            include_toc = args.toc or meta.get("toc", "").lower() in ("true", "yes", "1")

            # Load space defaults
            space_defaults = get_space_defaults(space)

            # Apply defaults
            parent_id = args.parent or meta.get("parent") or space_defaults.default_parent
            labels = None
            if args.labels:
                labels = args.labels.split(",")
            elif meta.get("labels"):
                labels = [lb.strip() for lb in meta["labels"].split(",")]
            elif space_defaults.default_labels:
                labels = space_defaults.default_labels

            page = create_page(
                space=space,
                title=title,
                body=body,
                parent_id=parent_id,
                body_format=args.format,
                labels=labels,
                include_toc=include_toc,
                base_dir=base_dir,
            )

            if args.json:
                print(format_json(page))
            else:
                print(f"Created page: {page.get('id', 'N/A')}")
                print(f"Title: {page.get('title', 'N/A')}")
                print(f"URL: {page.get('_links', {}).get('webui', 'N/A')}")
                if page.get("image_count"):
                    print(f"Images: {page['image_count']} uploaded")

        elif args.page_command == "update":
            # Get body content
            body = None
            base_dir = None
            if args.body_file:
                body_path = Path(args.body_file)
                base_dir = body_path.parent
                with open(body_path) as f:
                    body = f.read()
            elif args.body:
                body = args.body

            # Extract frontmatter metadata (CLI flags take precedence)
            meta = {}
            if body and args.format == "markdown":
                body, meta = extract_frontmatter(body)

            title = args.title or meta.get("title")
            include_toc = args.toc or meta.get("toc", "").lower() in (
                "true",
                "yes",
                "1",
            )

            page = update_page(
                page_id=args.page_id,
                title=title,
                body=body,
                body_format=args.format,
                version=args.version,
                include_toc=include_toc,
                base_dir=base_dir,
            )

            if args.json:
                print(format_json(page))
            else:
                print(f"Updated page: {page.get('id', 'N/A')}")
                print(f"New version: {page.get('version', {}).get('number', 'N/A')}")
                if page.get("image_count"):
                    print(f"Images: {page['image_count']} uploaded")

        elif args.page_command == "move":
            parent_id = args.parent if args.parent else None
            page = move_page(args.page_id, parent_id)
            if args.json:
                print(format_json(page))
            else:
                dest = f"under page {parent_id}" if parent_id else "to space root"
                print(f"Moved page: {page.get('id', 'N/A')} {dest}")

        elif args.page_command == "delete":
            delete_page(args.page_id)
            print(f"Deleted page: {args.page_id}")

        return 0

    except Exception as e:
        msg = e.verbose_message() if isinstance(e, APIError) else str(e)
        print(f"Error: {msg}", file=sys.stderr)
        return 1


def cmd_space(args: argparse.Namespace) -> int:
    """Handle space command."""
    try:
        if args.space_command == "list":
            spaces = list_spaces(space_type=args.type, max_results=args.max_results or 50)

            if args.json:
                print(format_json(spaces))
            else:
                if not spaces:
                    print("No spaces found")
                    return 0

                rows = []
                for space in spaces:
                    rows.append(
                        {
                            "key": space.get("key", "N/A"),
                            "name": space.get("name", "No name"),
                            "type": space.get("type", "global"),
                        }
                    )

                print(
                    format_table(
                        rows,
                        ["key", "name", "type"],
                        headers={"key": "Key", "name": "Name", "type": "Type"},
                    )
                )

        elif args.space_command == "get":
            expand = args.expand.split(",") if args.expand else None
            space = get_space(args.space_key, expand=expand)

            if args.json:
                print(format_json(space))
            else:
                print(f"Key: {space.get('key', 'N/A')}")
                print(f"Name: {space.get('name', 'No name')}")
                print(f"Type: {space.get('type', 'global')}")
                desc = space.get("description", {})
                if desc:
                    plain_desc = desc.get("plain", {}).get("value", "")
                    if plain_desc:
                        print(f"Description: {plain_desc}")

        elif args.space_command == "create":
            space = create_space(
                key=args.key,
                name=args.name,
                description=args.description,
                space_type=args.type or "global",
            )

            if args.json:
                print(format_json(space))
            else:
                print(f"Created space: {space.get('key', 'N/A')}")
                print(f"Name: {space.get('name', 'N/A')}")

        elif args.space_command == "permissions":
            return cmd_space_permissions(args)

        return 0

    except Exception as e:
        msg = e.verbose_message() if isinstance(e, APIError) else str(e)
        print(f"Error: {msg}", file=sys.stderr)
        return 1


def cmd_space_permissions(args: argparse.Namespace) -> int:
    """Handle space permissions command."""
    if args.perm_command == "list":
        permissions = get_space_permissions(args.space_key)

        if args.subject_type:
            permissions = [
                p
                for p in permissions
                if p.get("subjects", {}).get(args.subject_type)
                or p.get("subject", {}).get("type") == args.subject_type
            ]

        if args.json:
            print(format_json(permissions))
        else:
            if not permissions:
                print("No permissions found")
                return 0

            rows = []
            for perm in permissions:
                subject = perm.get("subject", {})
                operation = perm.get("operation", {})
                rows.append(
                    {
                        "id": str(perm.get("id", "N/A")),
                        "subject_type": subject.get("type", "N/A"),
                        "subject_id": subject.get("identifier", "N/A"),
                        "operation": operation.get("key", "N/A"),
                        "target": operation.get("target", "N/A"),
                    }
                )

            print(
                format_table(
                    rows,
                    ["id", "subject_type", "subject_id", "operation", "target"],
                    headers={
                        "id": "ID",
                        "subject_type": "Subject Type",
                        "subject_id": "Subject",
                        "operation": "Operation",
                        "target": "Target",
                    },
                )
            )

    elif args.perm_command == "add":
        perm = add_space_permission(
            space_key=args.space_key,
            subject_type=args.subject_type,
            subject_id=args.subject,
            operation_key=args.operation,
            target=args.target,
        )

        if args.json:
            print(format_json(perm))
        else:
            print(f"Added permission: {perm.get('id', 'N/A')}")
            print(f"  {args.subject_type} '{args.subject}' can {args.operation} {args.target}")

    elif args.perm_command == "remove":
        remove_space_permission(args.space_key, args.id)
        print(f"Removed permission: {args.id}")

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Handle config command."""
    try:
        if args.config_command == "show":
            config = load_config("confluence")
            if not config:
                print("No configuration file found at ~/.config/agent-skills/confluence.yaml")
                return 0

            print("Configuration: ~/.config/agent-skills/confluence.yaml\n")

            # Show auth (masked)
            print("Authentication:")
            print(f"  URL: {config.get('url', 'Not configured')}")
            print(f"  Email: {config.get('email', 'Not configured')}")
            print(f"  Token: {'*' * 8 if config.get('token') else 'Not configured'}")
            print()

            # Show defaults
            defaults = ConfluenceDefaults.from_config(config)
            print("Defaults:")
            print(f"  CQL Scope: {defaults.cql_scope or 'Not configured'}")
            print(f"  Max Results: {defaults.max_results or 'Not configured (default: 50)'}")
            print(f"  Default Space: {defaults.default_space or 'Not configured'}")
            if defaults.fields:
                print(f"  Fields: {', '.join(defaults.fields)}")
            print()

            # Show space defaults
            if args.space:
                space_defaults = SpaceDefaults.from_config(config, args.space)
                print(f"Space Defaults for {args.space}:")
                print(f"  Default Parent: {space_defaults.default_parent or 'Not configured'}")
                if space_defaults.default_labels:
                    print(f"  Default Labels: {', '.join(space_defaults.default_labels)}")
            else:
                spaces = config.get("spaces", {})
                if spaces:
                    print("Space-Specific Defaults:")
                    for space, settings in spaces.items():
                        print(f"  {space}:")
                        print(
                            f"    Default Parent: {settings.get('default_parent', 'Not configured')}"
                        )
                        if settings.get("default_labels"):
                            print(f"    Default Labels: {', '.join(settings['default_labels'])}")
                else:
                    print("No space-specific defaults configured")

            return 0

    except Exception as e:
        msg = e.verbose_message() if isinstance(e, APIError) else str(e)
        print(f"Error: {msg}", file=sys.stderr)
        return 1


# ============================================================================
# MAIN CLI
# ============================================================================


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Confluence integration for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ========================================================================
    # CHECK COMMAND
    # ========================================================================
    subparsers.add_parser(
        "check",
        help="Check configuration and connectivity",
    )

    # ========================================================================
    # SEARCH COMMAND
    # ========================================================================
    search_parser = subparsers.add_parser(
        "search",
        help="Search for content using CQL",
    )
    search_parser.add_argument("cql", help="CQL query string")
    search_parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum number of results (default: 50, or use configured default)",
    )
    search_parser.add_argument(
        "--type",
        help="Content type filter (page, blogpost, comment)",
    )
    search_parser.add_argument(
        "--space",
        help="Limit to specific space",
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # ========================================================================
    # PAGE COMMAND
    # ========================================================================
    page_parser = subparsers.add_parser(
        "page",
        help="Manage pages",
    )
    page_subparsers = page_parser.add_subparsers(dest="page_command", required=True)

    # Get subcommand
    get_parser = page_subparsers.add_parser("get", help="Get page details")
    get_parser.add_argument("page_identifier", help="Page ID or title")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")
    get_parser.add_argument(
        "--markdown", action="store_true", help="Output body as Markdown (default)"
    )
    get_parser.add_argument("--raw", action="store_true", help="Output in original format")
    get_parser.add_argument("--no-body", action="store_true", help="Don't include body content")
    get_parser.add_argument(
        "--frontmatter",
        action="store_true",
        help="Output as markdown with YAML frontmatter (for round-tripping)",
    )
    get_parser.add_argument("--expand", help="Fields to expand (comma-separated)")
    get_parser.add_argument(
        "--output", "-o", help="Write output to file (images downloaded to sibling directory)"
    )

    # Create subcommand
    create_parser = page_subparsers.add_parser("create", help="Create new page")
    create_parser.add_argument("--space", help="Space key (or set in frontmatter)")
    create_parser.add_argument("--title", help="Page title (or set in frontmatter)")
    create_parser.add_argument("--body", help="Page content (Markdown by default)")
    create_parser.add_argument("--body-file", help="Read content from file (Markdown)")
    create_parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "editor"],
        help="Input format (default: markdown)",
    )
    create_parser.add_argument("--parent", help="Parent page ID")
    create_parser.add_argument("--labels", help="Comma-separated labels")
    create_parser.add_argument("--toc", action="store_true", help="Prepend table of contents macro")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Update subcommand
    update_parser = page_subparsers.add_parser("update", help="Update existing page")
    update_parser.add_argument("page_id", help="Page ID")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--body", help="New content (Markdown by default)")
    update_parser.add_argument("--body-file", help="Read content from file (Markdown)")
    update_parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "editor"],
        help="Input format (default: markdown)",
    )
    update_parser.add_argument(
        "--version", type=int, help="Current version (auto-detect if not provided)"
    )
    update_parser.add_argument("--toc", action="store_true", help="Prepend table of contents macro")
    update_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Move subcommand
    move_parser = page_subparsers.add_parser("move", help="Move a page under a new parent")
    move_parser.add_argument("page_id", help="Page ID to move")
    move_parser.add_argument("--parent", help="New parent page ID (omit to move to space root)")
    move_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Delete subcommand
    delete_parser = page_subparsers.add_parser("delete", help="Delete a page")
    delete_parser.add_argument("page_id", help="Page ID to delete")

    # ========================================================================
    # SPACE COMMAND
    # ========================================================================
    space_parser = subparsers.add_parser(
        "space",
        help="Manage spaces",
    )
    space_subparsers = space_parser.add_subparsers(dest="space_command", required=True)

    # List subcommand
    list_parser = space_subparsers.add_parser("list", help="List spaces")
    list_parser.add_argument("--type", help="Space type filter (global, personal)")
    list_parser.add_argument("--max-results", type=int, help="Maximum results")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Get subcommand
    space_get_parser = space_subparsers.add_parser("get", help="Get space details")
    space_get_parser.add_argument("space_key", help="Space key")
    space_get_parser.add_argument("--expand", help="Fields to expand (comma-separated)")
    space_get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Create subcommand
    space_create_parser = space_subparsers.add_parser("create", help="Create new space")
    space_create_parser.add_argument("--key", required=True, help="Space key")
    space_create_parser.add_argument("--name", required=True, help="Space name")
    space_create_parser.add_argument("--description", help="Space description")
    space_create_parser.add_argument(
        "--type", choices=["global", "personal"], help="Space type (default: global)"
    )
    space_create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Permissions subcommand
    perm_parser = space_subparsers.add_parser("permissions", help="Manage space permissions")
    perm_subparsers = perm_parser.add_subparsers(dest="perm_command", required=True)

    # Permissions list
    perm_list_parser = perm_subparsers.add_parser("list", help="List space permissions")
    perm_list_parser.add_argument("space_key", help="Space key")
    perm_list_parser.add_argument(
        "--subject-type", choices=["user", "group"], help="Filter by subject type"
    )
    perm_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Permissions add
    perm_add_parser = perm_subparsers.add_parser("add", help="Add a space permission")
    perm_add_parser.add_argument("space_key", help="Space key")
    perm_add_parser.add_argument(
        "--subject-type", required=True, choices=["user", "group"], help="Subject type"
    )
    perm_add_parser.add_argument(
        "--subject", required=True, help="User account ID or group name/ID"
    )
    perm_add_parser.add_argument(
        "--operation",
        required=True,
        choices=["read", "create", "delete", "export", "administer", "archive", "restrict_content"],
        help="Operation to grant",
    )
    perm_add_parser.add_argument(
        "--target",
        required=True,
        choices=["space", "page", "blogpost", "comment", "attachment"],
        help="Target type",
    )
    perm_add_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Permissions remove
    perm_remove_parser = perm_subparsers.add_parser("remove", help="Remove a space permission")
    perm_remove_parser.add_argument("space_key", help="Space key")
    perm_remove_parser.add_argument("--id", required=True, type=int, help="Permission ID to remove")

    # ========================================================================
    # CONFIG COMMAND
    # ========================================================================
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration",
    )
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)

    # Show subcommand
    show_parser = config_subparsers.add_parser("show", help="Show effective configuration")
    show_parser.add_argument(
        "--space",
        help="Show space-specific defaults for this space",
    )

    # Parse and dispatch
    args = parser.parse_args()

    if args.command == "check":
        return cmd_check()
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "page":
        return cmd_page(args)
    elif args.command == "space":
        return cmd_space(args)
    elif args.command == "config":
        return cmd_config(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
