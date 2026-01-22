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
import html
import json
import os
import re
import sys
import time
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

# Module-level cache for deployment type detection
# Key: Confluence URL, Value: {"deployment_type": str, "api_version": str}
_deployment_cache: dict[str, dict[str, str]] = {}

# Rate limit retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0


class ConfluenceDetectionError(Exception):
    """Exception raised when Confluence deployment type detection fails."""

    pass


def _make_detection_request(
    url: str,
    endpoint: str,
    email: str | None = None,
    token: str | None = None,
    username: str | None = None,
    password: str | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    """Make a request to Confluence for deployment detection with rate limit handling.

    Tries unauthenticated first, then falls back to authenticated if needed.

    Args:
        url: Base Confluence URL.
        endpoint: API endpoint.
        email: User email for Cloud auth.
        token: API token.
        username: Username for basic auth.
        password: Password for basic auth.
        timeout: Request timeout.

    Returns:
        Parsed JSON response.

    Raises:
        ConfluenceDetectionError: If request fails after retries.
    """
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"Accept": "application/json"}

    # Build auth tuple for fallback
    auth = None
    if token and email:
        auth = (email, token)
    elif username and password:
        auth = (username, password)

    retry_delay = INITIAL_RETRY_DELAY

    # Try unauthenticated first (some endpoints are public)
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                full_url,
                headers=headers,
                timeout=timeout,
            )

            # If unauthenticated fails with 401/403, try with auth
            if response.status_code in (401, 403) and auth:
                response = requests.get(
                    full_url,
                    headers=headers,
                    auth=auth,
                    timeout=timeout,
                )

            # Handle rate limiting (429 Too Many Requests)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    wait_time = float(retry_after)
                else:
                    wait_time = retry_delay
                    retry_delay *= RETRY_BACKOFF_MULTIPLIER

                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    raise ConfluenceDetectionError(f"Rate limited after {MAX_RETRIES} attempts")

            if not response.ok:
                raise ConfluenceDetectionError(
                    f"Request failed: {response.status_code} {response.reason}"
                )

            return response.json()

        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(retry_delay)
                retry_delay *= RETRY_BACKOFF_MULTIPLIER
                continue
            raise ConfluenceDetectionError(f"Request failed: {e}") from e

    raise ConfluenceDetectionError("Request failed after all retries")


def detect_deployment_type(force_refresh: bool = False) -> str:
    """Detect the Confluence deployment type (Cloud or DataCenter/Server).

    Uses URL pattern detection and API responses to determine deployment type.
    Results are cached per-session to avoid repeated API calls.

    Args:
        force_refresh: If True, bypass the cache and make a new request.

    Returns:
        Deployment type string: "Cloud" or "Server".

    Raises:
        ConfluenceDetectionError: If detection fails.
    """
    creds = get_credentials("confluence")
    if not creds.url:
        raise ConfluenceDetectionError("No Confluence URL configured")

    # Check cache unless force refresh requested
    if not force_refresh and creds.url in _deployment_cache:
        return _deployment_cache[creds.url]["deployment_type"]

    try:
        # First, check URL pattern - Cloud instances typically have atlassian.net domain
        if "atlassian.net" in creds.url:
            deployment_type = "Cloud"
            api_base = "/wiki/rest/api"
        else:
            # For self-hosted, try to verify by checking API endpoints
            deployment_type = "Server"
            api_base = "/rest/api"

        # Try to verify by making a simple API call
        try:
            _make_detection_request(
                url=creds.url,
                endpoint=f"{api_base}/space",
                email=creds.email,
                token=creds.token,
                username=creds.username,
                password=creds.password,
            )
        except ConfluenceDetectionError:
            # If the first attempt fails, try the alternate API base
            if deployment_type == "Cloud":
                api_base = "/rest/api"
                deployment_type = "Server"
            else:
                api_base = "/wiki/rest/api"
                deployment_type = "Cloud"

            # Verify with alternate base
            _make_detection_request(
                url=creds.url,
                endpoint=f"{api_base}/space",
                email=creds.email,
                token=creds.token,
                username=creds.username,
                password=creds.password,
            )

        # Cache the result
        _deployment_cache[creds.url] = {
            "deployment_type": deployment_type,
            "api_base": api_base,
        }

        return deployment_type

    except Exception as e:
        raise ConfluenceDetectionError(f"Failed to detect deployment type: {e}") from e


def get_api_base() -> str:
    """Get the appropriate API base path for the current Confluence instance.

    Returns:
        "/wiki/rest/api" for Cloud, "/rest/api" for Server/DataCenter.
    """
    creds = get_credentials("confluence")
    if creds.url and creds.url in _deployment_cache:
        return _deployment_cache[creds.url]["api_base"]

    # Trigger detection to populate cache
    detect_deployment_type()

    if creds.url and creds.url in _deployment_cache:
        return _deployment_cache[creds.url]["api_base"]

    # Default to server path if detection fails (more compatible)
    return "/rest/api"


def api_path(endpoint: str) -> str:
    """Construct the full API path with the correct base.

    Args:
        endpoint: API endpoint without base prefix (e.g., "content/search", "space").

    Returns:
        Full path (e.g., "/wiki/rest/api/content/search" or "/rest/api/content/search").
    """
    base = get_api_base()
    return f"{base}/{endpoint.lstrip('/')}"


def is_cloud() -> bool:
    """Check if the current Confluence instance is Cloud.

    Returns:
        True if Cloud, False otherwise.
    """
    try:
        return detect_deployment_type() == "Cloud"
    except ConfluenceDetectionError:
        return False


def clear_cache() -> None:
    """Clear the deployment type cache.

    Useful for testing or when switching between Confluence instances.
    """
    _deployment_cache.clear()


# ============================================================================
# MARKDOWN CONVERSION UTILITIES
# ============================================================================


def markdown_to_storage(markdown: str) -> str:
    """Convert Markdown to Confluence storage format (XHTML).

    Supports:
    - Headers (# → <h1>, ## → <h2>, etc.)
    - Paragraphs
    - Bold (**text** or __text__ → <strong>)
    - Italic (*text* or _text_ → <em>)
    - Lists (- or * → <ul><li>)
    - Numbered lists (1. → <ol><li>)
    - Code blocks (``` → <ac:structured-macro>)
    - Inline code (`code` → <code>)
    - Links ([text](url) → <a>)

    Args:
        markdown: Markdown string.

    Returns:
        XHTML string for storage format.
    """
    lines = markdown.split("\n")
    result = []
    in_code_block = False
    code_block_lines = []
    code_lang = ""
    in_list = False
    in_ordered_list = False
    list_items = []

    for line in lines:
        # Code block detection
        if line.strip().startswith("```"):
            if not in_code_block:
                # Starting code block
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                code_block_lines = []
            else:
                # Ending code block
                in_code_block = False
                code_content = "\n".join(code_block_lines)
                code_content = html.escape(code_content)
                if code_lang:
                    result.append(
                        f'<ac:structured-macro ac:name="code">'
                        f'<ac:parameter ac:name="language">{html.escape(code_lang)}</ac:parameter>'
                        f"<ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body>"
                        f"</ac:structured-macro>"
                    )
                else:
                    result.append(f"<pre><code>{code_content}</code></pre>")
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # Flush list if we're no longer in one
        if in_list and not (line.strip().startswith("- ") or line.strip().startswith("* ")):
            list_html = "<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>"
            result.append(list_html)
            list_items = []
            in_list = False

        if in_ordered_list and not re.match(r"^\d+\.\s", line.strip()):
            list_html = "<ol>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ol>"
            result.append(list_html)
            list_items = []
            in_ordered_list = False

        # Headers
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if header_match:
            level = len(header_match.group(1))
            text = _inline_markdown_to_html(header_match.group(2))
            result.append(f"<h{level}>{text}</h{level}>")
            continue

        # Unordered lists
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            in_list = True
            item_text = line.strip()[2:]
            list_items.append(_inline_markdown_to_html(item_text))
            continue

        # Ordered lists
        ordered_match = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
        if ordered_match:
            in_ordered_list = True
            item_text = ordered_match.group(2)
            list_items.append(_inline_markdown_to_html(item_text))
            continue

        # Empty lines
        if not line.strip():
            result.append("")
            continue

        # Paragraphs
        para_text = _inline_markdown_to_html(line)
        result.append(f"<p>{para_text}</p>")

    # Flush any remaining list
    if in_list:
        list_html = "<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>"
        result.append(list_html)
    if in_ordered_list:
        list_html = "<ol>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ol>"
        result.append(list_html)

    return "\n".join(result)


def _inline_markdown_to_html(text: str) -> str:
    """Convert inline Markdown to HTML.

    Handles: bold, italic, inline code, links.
    """
    # Escape HTML first
    text = html.escape(text)

    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)

    # Italic: *text* or _text_ (not inside word boundaries)
    text = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", text)

    # Inline code: `code`
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)

    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', text)

    return text


def storage_to_markdown(storage: str) -> str:
    """Convert Confluence storage format (XHTML) to Markdown.

    Best-effort conversion of common XHTML elements.

    Args:
        storage: XHTML storage format string.

    Returns:
        Markdown string.
    """
    text = storage

    # Code blocks (Confluence macros)
    def replace_code_macro(match):
        lang = match.group(1) if match.group(1) else ""
        code = match.group(2)
        # Unescape CDATA content
        code = code.replace("<![CDATA[", "").replace("]]>", "")
        code = html.unescape(code)
        return f"```{lang}\n{code}\n```"

    text = re.sub(
        r'<ac:structured-macro ac:name="code">.*?<ac:parameter ac:name="language">([^<]*)</ac:parameter>.*?<ac:plain-text-body>(.*?)</ac:plain-text-body>.*?</ac:structured-macro>',
        replace_code_macro,
        text,
        flags=re.DOTALL,
    )

    # Simple code blocks
    text = re.sub(
        r"<pre><code>(.*?)</code></pre>",
        lambda m: f"```\n{html.unescape(m.group(1))}\n```",
        text,
        flags=re.DOTALL,
    )

    # Headers
    for i in range(6, 0, -1):
        text = re.sub(
            f"<h{i}>(.*?)</h{i}>",
            lambda m, level=i: f"{'#' * level} {_html_to_markdown(m.group(1))}\n",
            text,
        )

    # Lists
    text = re.sub(
        r"<ul>(.*?)</ul>", lambda m: _convert_list(m.group(1), ordered=False), text, flags=re.DOTALL
    )
    text = re.sub(
        r"<ol>(.*?)</ol>", lambda m: _convert_list(m.group(1), ordered=True), text, flags=re.DOTALL
    )

    # Paragraphs
    text = re.sub(
        r"<p>(.*?)</p>", lambda m: _html_to_markdown(m.group(1)) + "\n", text, flags=re.DOTALL
    )

    # Clean up extra newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _html_to_markdown(html_text: str) -> str:
    """Convert inline HTML to Markdown."""
    text = html_text

    # Bold
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text)

    # Italic
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text)
    text = re.sub(r"<i>(.*?)</i>", r"*\1*", text)

    # Code
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text)

    # Links
    text = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r"[\2](\1)", text)

    # Unescape HTML entities
    text = html.unescape(text)

    return text.strip()


def _convert_list(list_content: str, ordered: bool = False) -> str:
    """Convert HTML list items to Markdown."""
    items = re.findall(r"<li>(.*?)</li>", list_content, flags=re.DOTALL)
    result = []
    for idx, item in enumerate(items, 1):
        item_text = _html_to_markdown(item.strip())
        if ordered:
            result.append(f"{idx}. {item_text}")
        else:
            result.append(f"- {item_text}")
    return "\n".join(result) + "\n"


def markdown_to_adf(markdown: str) -> dict[str, Any]:
    """Convert Markdown to ADF (Atlassian Document Format).

    Args:
        markdown: Markdown string.

    Returns:
        ADF JSON structure.
    """
    lines = markdown.split("\n")
    content = []
    in_code_block = False
    code_block_lines = []
    code_lang = ""

    for line in lines:
        # Code block detection
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                code_block_lines = []
            else:
                in_code_block = False
                code_content = "\n".join(code_block_lines)
                code_node = {
                    "type": "codeBlock",
                    "content": [{"type": "text", "text": code_content}],
                }
                if code_lang:
                    code_node["attrs"] = {"language": code_lang}
                content.append(code_node)
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # Headers
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if header_match:
            level = len(header_match.group(1))
            text_content = _inline_markdown_to_adf(header_match.group(2))
            content.append({"type": "heading", "attrs": {"level": level}, "content": text_content})
            continue

        # Unordered lists
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            # Simple list item
            item_text = line.strip()[2:]
            list_content = _inline_markdown_to_adf(item_text)
            content.append(
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [{"type": "paragraph", "content": list_content}],
                        }
                    ],
                }
            )
            continue

        # Ordered lists
        ordered_match = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
        if ordered_match:
            item_text = ordered_match.group(2)
            list_content = _inline_markdown_to_adf(item_text)
            content.append(
                {
                    "type": "orderedList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [{"type": "paragraph", "content": list_content}],
                        }
                    ],
                }
            )
            continue

        # Empty lines
        if not line.strip():
            continue

        # Paragraphs
        para_content = _inline_markdown_to_adf(line)
        if para_content:
            content.append({"type": "paragraph", "content": para_content})

    return {"version": 1, "type": "doc", "content": content}


def _inline_markdown_to_adf(text: str) -> list[dict[str, Any]]:
    """Convert inline Markdown to ADF nodes.

    Handles: bold, italic, inline code, links, plain text.
    """
    result = []
    current_text = ""
    i = 0

    while i < len(text):
        # Bold: **text**
        if text[i : i + 2] == "**":
            if current_text:
                result.append({"type": "text", "text": current_text})
                current_text = ""
            end = text.find("**", i + 2)
            if end != -1:
                bold_text = text[i + 2 : end]
                result.append({"type": "text", "text": bold_text, "marks": [{"type": "strong"}]})
                i = end + 2
                continue

        # Italic: *text*
        if text[i] == "*" and (i == 0 or not text[i - 1].isalnum()) and text[i : i + 2] != "**":
            if current_text:
                result.append({"type": "text", "text": current_text})
                current_text = ""
            end = text.find("*", i + 1)
            if end != -1 and (end == len(text) - 1 or not text[end + 1].isalnum()):
                italic_text = text[i + 1 : end]
                result.append({"type": "text", "text": italic_text, "marks": [{"type": "em"}]})
                i = end + 1
                continue

        # Inline code: `code`
        if text[i] == "`":
            if current_text:
                result.append({"type": "text", "text": current_text})
                current_text = ""
            end = text.find("`", i + 1)
            if end != -1:
                code_text = text[i + 1 : end]
                result.append({"type": "text", "text": code_text, "marks": [{"type": "code"}]})
                i = end + 1
                continue

        # Links: [text](url)
        if text[i] == "[":
            link_match = re.match(r"\[([^\]]+)\]\(([^\)]+)\)", text[i:])
            if link_match:
                if current_text:
                    result.append({"type": "text", "text": current_text})
                    current_text = ""
                link_text = link_match.group(1)
                link_url = link_match.group(2)
                result.append(
                    {
                        "type": "text",
                        "text": link_text,
                        "marks": [{"type": "link", "attrs": {"href": link_url}}],
                    }
                )
                i += len(link_match.group(0))
                continue

        current_text += text[i]
        i += 1

    if current_text:
        result.append({"type": "text", "text": current_text})

    return result


def adf_to_markdown(adf: dict[str, Any]) -> str:
    """Convert ADF (Atlassian Document Format) to Markdown.

    Args:
        adf: ADF JSON structure.

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
            para_text = _adf_content_to_text(node.get("content", []))
            if para_text:
                result.append(para_text)

        elif node_type == "heading":
            level = node.get("attrs", {}).get("level", 1)
            heading_text = _adf_content_to_text(node.get("content", []))
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
                            item_text = _adf_content_to_text(item_content.get("content", []))
                    result.append(f"- {item_text}")

        elif node_type == "orderedList":
            for idx, item in enumerate(node.get("content", []), 1):
                if item.get("type") == "listItem":
                    item_text = ""
                    for item_content in item.get("content", []):
                        if item_content.get("type") == "paragraph":
                            item_text = _adf_content_to_text(item_content.get("content", []))
                    result.append(f"{idx}. {item_text}")

    return "\n\n".join(result)


def _adf_content_to_text(content: list[dict[str, Any]]) -> str:
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

    return "".join(result)


def format_content(
    content: str, input_format: str = "markdown", output_format: str = "auto"
) -> dict[str, Any] | str:
    """Main content formatting function.

    Args:
        content: Content string.
        input_format: "markdown", "storage", "editor".
        output_format: "auto", "storage", "editor".

    Returns:
        Formatted content for API.
    """
    # Determine output format
    if output_format == "auto":
        output_format = "editor" if is_cloud() else "storage"

    # Convert input to output format
    if input_format == "markdown":
        if output_format == "storage":
            return markdown_to_storage(content)
        elif output_format == "editor":
            return markdown_to_adf(content)
        else:
            return content
    elif input_format == "storage":
        if output_format == "editor":
            # Convert storage → markdown → ADF
            md = storage_to_markdown(content)
            return markdown_to_adf(md)
        else:
            return content
    elif input_format == "editor":
        # Assume content is already ADF dict
        if isinstance(content, str):
            content = json.loads(content)
        if output_format == "storage":
            # Convert ADF → markdown → storage
            md = adf_to_markdown(content)
            return markdown_to_storage(md)
        else:
            return content

    return content


# ============================================================================
# HTTP/REST UTILITIES
# ============================================================================


class APIError(Exception):
    """Exception raised for API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


def _get_confluence_auth_method(
    creds: Credentials,
) -> tuple[tuple[str, str] | None, dict[str, str]]:
    """Determine the appropriate Confluence authentication method.

    Cloud uses email + API token as basic auth.
    Data Center/Server typically uses Bearer token or username/password.

    Args:
        creds: Credentials object with token and email.

    Returns:
        Tuple of (auth, headers_dict) for requests.
    """
    headers: dict[str, str] = {}
    auth = None

    if is_cloud():
        # Cloud: email + API token as basic auth
        if creds.email and creds.token:
            auth = (creds.email, creds.token)
    else:
        # DC/Server: Can use Bearer token or username/password
        if creds.token:
            headers["Authorization"] = f"Bearer {creds.token}"
        elif creds.username and creds.password:
            auth = (creds.username, creds.password)

    return auth, headers


def make_request(
    service: str,
    method: str,
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
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
    request_headers.setdefault("Content-Type", "application/json")
    request_headers.setdefault("Accept", "application/json")

    # Add authentication based on service type
    auth = None
    if service == "confluence" and creds.token:
        # Use Confluence-specific auth detection
        auth, auth_headers = _get_confluence_auth_method(creds)
        request_headers.update(auth_headers)
    elif creds.token:
        if creds.email:
            # Generic: email + API token as basic auth
            auth = (creds.email, creds.token)
        else:
            # Bearer token style
            request_headers["Authorization"] = f"Bearer {creds.token}"
    elif creds.username and creds.password:
        auth = (creds.username, creds.password)

    response = requests.request(
        method=method.upper(),
        url=url,
        params=params,
        json=json_data,
        headers=request_headers,
        auth=auth,
        timeout=timeout,
    )

    if not response.ok:
        raise APIError(
            f"{method.upper()} {endpoint} failed: {response.status_code} {response.reason}",
            status_code=response.status_code,
            response=response.text,
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
    page: dict[str, Any], *, include_body: bool = False, as_markdown: bool = True
) -> str:
    """Format a Confluence page for display.

    Args:
        page: Confluence page dictionary.
        include_body: Whether to include page body.
        as_markdown: If True, convert body to Markdown.

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

    result = f"""Page ID: {page_id}
Title: {title}
Type: {page_type}
Space: {space_key}
Status: {status}
Version: {version}"""

    if include_body:
        body = page.get("body", {})
        if as_markdown:
            # Try to get storage format first, then editor format
            if "storage" in body:
                storage_value = body["storage"].get("value", "")
                markdown_body = storage_to_markdown(storage_value)
            elif "editor" in body:
                editor_value = body["editor"].get("value", {})
                if isinstance(editor_value, str):
                    editor_value = json.loads(editor_value)
                markdown_body = adf_to_markdown(editor_value)
            else:
                markdown_body = "(No content available)"

            result += f"\n\n---\n\n{markdown_body}"
        else:
            # Raw format
            result += f"\n\nBody: {json.dumps(body, indent=2)}"

    return result


def format_pages_list(pages: list[dict[str, Any]]) -> str:
    """Format a list of Confluence pages for display.

    Args:
        pages: List of Confluence page dictionaries.

    Returns:
        Formatted table string.
    """
    if not pages:
        return "No pages found"

    rows = []
    for page in pages:
        space = page.get("space", {})
        space_key = space.get("key", "Unknown") if space else "Unknown"

        rows.append(
            {
                "id": page.get("id", "N/A"),
                "title": page.get("title", "No title"),
                "type": page.get("type", "page"),
                "space": space_key,
            }
        )

    return format_table(
        rows,
        ["id", "title", "type", "space"],
        headers={"id": "ID", "title": "Title", "type": "Type", "space": "Space"},
    )


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


def create_page(
    space: str,
    title: str,
    body: str,
    *,
    parent_id: str | None = None,
    body_format: str = "markdown",
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new page.

    Args:
        space: Space key.
        title: Page title.
        body: Page content.
        parent_id: Parent page ID for hierarchy.
        body_format: Format of body content ("markdown", "storage", "editor").
        labels: List of labels to add.

    Returns:
        Created page dictionary.

    Raises:
        APIError: If creation fails.
    """
    # Convert body to appropriate format
    if body_format == "markdown":
        if is_cloud():
            # Cloud: use editor format (ADF)
            body_content = markdown_to_adf(body)
            body_representation = "atlas_doc_format"
            body_key = "editor"
        else:
            # DC/Server: use storage format
            body_content = markdown_to_storage(body)
            body_representation = "storage"
            body_key = "storage"
    elif body_format == "storage":
        body_content = body
        body_representation = "storage"
        body_key = "storage"
    elif body_format == "editor":
        body_content = json.loads(body) if isinstance(body, str) else body
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
    if isinstance(response, dict):
        return response
    return {}


def update_page(
    page_id: str,
    *,
    title: str | None = None,
    body: str | None = None,
    body_format: str = "markdown",
    version: int | None = None,
) -> dict[str, Any]:
    """Update an existing page.

    Args:
        page_id: Page ID to update.
        title: New title (optional).
        body: New content (optional).
        body_format: Format of body content ("markdown", "storage", "editor").
        version: Current version number (will auto-detect if not provided).

    Returns:
        Updated page dictionary.

    Raises:
        APIError: If update fails or version conflict.
    """
    # Get current page to determine version if not provided
    if version is None:
        current_page = get_page(page_id, expand=["version"])
        version = current_page.get("version", {}).get("number", 1)

    # Build update data
    update_data: dict[str, Any] = {
        "version": {"number": version + 1},
        "type": "page",
    }

    if title:
        update_data["title"] = title

    if body:
        # Convert body to appropriate format
        if body_format == "markdown":
            if is_cloud():
                # Cloud: use editor format (ADF)
                body_content = markdown_to_adf(body)
                body_representation = "atlas_doc_format"
                body_key = "editor"
            else:
                # DC/Server: use storage format
                body_content = markdown_to_storage(body)
                body_representation = "storage"
                body_key = "storage"
        elif body_format == "storage":
            body_content = body
            body_representation = "storage"
            body_key = "storage"
        elif body_format == "editor":
            body_content = json.loads(body) if isinstance(body, str) else body
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
    if isinstance(response, dict):
        return response
    return {}


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

    # 2. Test connectivity and detect deployment type
    print("2. Testing connectivity...")
    try:
        deployment_type = detect_deployment_type(force_refresh=True)
        print(f"   Deployment: {deployment_type}")
        print(f"   API Base: {get_api_base()}")
        print("   Connection: OK\n")
    except ConfluenceDetectionError as e:
        print(f"   ERROR: {e}")
        return 1

    # 3. Test a simple API call
    print("3. Testing API access...")
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
        print(f"   ERROR: {e}")
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
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_page(args: argparse.Namespace) -> int:
    """Handle page command."""
    try:
        if args.page_command == "get":
            # Determine what to expand
            expand = ["body.storage", "body.editor", "version", "space"]
            if args.expand:
                expand = args.expand.split(",")

            page = get_page(args.page_identifier, expand=expand)

            if args.json:
                print(format_json(page))
            else:
                # Format with body as Markdown by default
                include_body = not args.no_body
                as_markdown = args.markdown or not args.raw
                print(format_page(page, include_body=include_body, as_markdown=as_markdown))

        elif args.page_command == "create":
            # Load space defaults
            space_defaults = get_space_defaults(args.space)

            # Get body content
            if args.body_file:
                with open(args.body_file) as f:
                    body = f.read()
            elif args.body:
                body = args.body
            else:
                body = ""

            # Apply defaults
            parent_id = args.parent or space_defaults.default_parent
            labels = None
            if args.labels:
                labels = args.labels.split(",")
            elif space_defaults.default_labels:
                labels = space_defaults.default_labels

            page = create_page(
                space=args.space,
                title=args.title,
                body=body,
                parent_id=parent_id,
                body_format=args.format,
                labels=labels,
            )

            if args.json:
                print(format_json(page))
            else:
                print(f"Created page: {page.get('id', 'N/A')}")
                print(f"Title: {page.get('title', 'N/A')}")
                print(f"URL: {page.get('_links', {}).get('webui', 'N/A')}")

        elif args.page_command == "update":
            # Get body content
            body = None
            if args.body_file:
                with open(args.body_file) as f:
                    body = f.read()
            elif args.body:
                body = args.body

            page = update_page(
                page_id=args.page_id,
                title=args.title,
                body=body,
                body_format=args.format,
                version=args.version,
            )

            if args.json:
                print(format_json(page))
            else:
                print(f"Updated page: {page.get('id', 'N/A')}")
                print(f"New version: {page.get('version', {}).get('number', 'N/A')}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
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

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


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
        print(f"Error: {e}", file=sys.stderr)
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
    get_parser.add_argument("--expand", help="Fields to expand (comma-separated)")

    # Create subcommand
    create_parser = page_subparsers.add_parser("create", help="Create new page")
    create_parser.add_argument("--space", required=True, help="Space key")
    create_parser.add_argument("--title", required=True, help="Page title")
    create_parser.add_argument("--body", help="Page content (Markdown by default)")
    create_parser.add_argument("--body-file", help="Read content from file (Markdown)")
    create_parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown", "storage", "editor"],
        help="Input format (default: markdown)",
    )
    create_parser.add_argument("--parent", help="Parent page ID")
    create_parser.add_argument("--labels", help="Comma-separated labels")
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
        choices=["markdown", "storage", "editor"],
        help="Input format (default: markdown)",
    )
    update_parser.add_argument(
        "--version", type=int, help="Current version (auto-detect if not provided)"
    )
    update_parser.add_argument("--json", action="store_true", help="Output as JSON")

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
