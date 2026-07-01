#!/usr/bin/env python3
"""Jira integration skill for AI agents.

This is a self-contained script that consolidates all Jira functionality.

Usage:
    python jira.py check
    python jira.py search "project = DEMO"
    python jira.py issue get DEMO-123
    python jira.py issue create --project DEMO --type Task --summary "New task"
    python jira.py transitions list DEMO-123

Requirements:
    pip install --user requests keyring pyyaml
"""

from __future__ import annotations

# Standard library imports
import argparse
import contextlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import UTC
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
        key: The credential key (e.g., "jira-token", "jira-email").

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
class JiraDefaults:
    """Container for Jira user defaults."""

    jql_scope: str | None = None
    security_level: str | None = None
    max_results: int | None = None
    fields: list[str] | None = None
    custom_fields: dict[str, str] | None = None
    custom_field_schemas: dict[str, str] | None = None

    @staticmethod
    def from_config(config: dict[str, Any]) -> JiraDefaults:
        """Load defaults from config dict.

        Args:
            config: Configuration dictionary.

        Returns:
            JiraDefaults object with available values.
        """
        defaults_dict = config.get("defaults", {})
        custom_fields = dict(defaults_dict.get("custom_fields") or {})
        custom_field_schemas = dict(defaults_dict.get("custom_field_schemas") or {})

        # Backward compat: migrate story_points_field to custom_fields
        if defaults_dict.get("story_points_field") and "story_points" not in custom_fields:
            custom_fields["story_points"] = defaults_dict["story_points_field"]

        return JiraDefaults(
            jql_scope=defaults_dict.get("jql_scope"),
            security_level=defaults_dict.get("security_level"),
            max_results=defaults_dict.get("max_results"),
            fields=defaults_dict.get("fields"),
            custom_fields=custom_fields or None,
            custom_field_schemas=custom_field_schemas or None,
        )


@dataclass
class ProjectDefaults:
    """Container for project-specific defaults."""

    issue_type: str | None = None
    priority: str | None = None

    @staticmethod
    def from_config(config: dict[str, Any], project: str) -> ProjectDefaults:
        """Load project defaults from config dict.

        Args:
            config: Configuration dictionary.
            project: Project key.

        Returns:
            ProjectDefaults object with available values.
        """
        projects = config.get("projects", {})
        project_dict = projects.get(project, {})
        return ProjectDefaults(
            issue_type=project_dict.get("issue_type"),
            priority=project_dict.get("priority"),
        )


def get_credentials(service: str) -> Credentials:
    """Get credentials for a service using priority order.

    Priority:
    1. System keyring
    2. Environment variables
    3. Config file

    Args:
        service: Service name (e.g., "jira").

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
        # Support both SERVICE_URL and SERVICE_BASE_URL (common for Jira)
        creds.url = os.environ.get(f"{prefix}_BASE_URL") or os.environ.get(f"{prefix}_URL")
    if not creds.email:
        creds.email = os.environ.get(f"{prefix}_EMAIL")
    if not creds.token:
        # Support both SERVICE_API_TOKEN and SERVICE_TOKEN (common for Jira)
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


def get_jira_defaults() -> JiraDefaults:
    """Get Jira defaults from config file.

    Returns:
        JiraDefaults object with available values, or empty defaults if not configured.
    """
    config = load_config("jira")
    if not config:
        return JiraDefaults()
    return JiraDefaults.from_config(config)


def get_project_defaults(project: str) -> ProjectDefaults:
    """Get project-specific defaults from config file.

    Args:
        project: Project key.

    Returns:
        ProjectDefaults object with available values.
    """
    config = load_config("jira")
    if not config:
        return ProjectDefaults()
    return ProjectDefaults.from_config(config, project)


def merge_jql_with_scope(user_jql: str, scope: str | None) -> str:
    """Merge user JQL with configured scope.

    Strategy: Prepend scope as a filter that's always applied.
    - If scope is None or empty, return user_jql unchanged
    - If user_jql is empty, return scope
    - Otherwise: "({scope}) AND ({user_jql})"

    Args:
        user_jql: JQL provided by user.
        scope: Configured JQL scope from defaults.

    Returns:
        Merged JQL query.
    """
    if not scope or not scope.strip():
        return user_jql

    if not user_jql or not user_jql.strip():
        return scope

    # Wrap both in parentheses to ensure correct precedence
    return f"({scope}) AND ({user_jql})"


# ============================================================================
# JIRA API HELPERS
# ============================================================================

# Module-level cache for deployment type detection
# Key: Jira URL, Value: {"deployment_type": str, "api_version": str, "scriptrunner": bool}
_deployment_cache: dict[str, dict[str, str | bool]] = {}

# Rate limit retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0


class JiraDetectionError(Exception):
    """Exception raised when Jira deployment type detection fails."""

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
    """Make a request to Jira for deployment detection with rate limit handling.

    Tries unauthenticated first (serverInfo is often public), then falls back
    to authenticated if needed.

    Args:
        url: Base Jira URL.
        endpoint: API endpoint.
        email: User email for Cloud auth.
        token: API token.
        username: Username for basic auth.
        password: Password for basic auth.
        timeout: Request timeout.

    Returns:
        Parsed JSON response.

    Raises:
        JiraDetectionError: If request fails after retries.
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

    # Try unauthenticated first (serverInfo is typically public)
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
                    raise JiraDetectionError(f"Rate limited after {MAX_RETRIES} attempts")

            if not response.ok:
                raise JiraDetectionError(
                    f"Request failed: {response.status_code} {response.reason}"
                )

            return response.json()

        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(retry_delay)
                retry_delay *= RETRY_BACKOFF_MULTIPLIER
                continue
            raise JiraDetectionError(f"Request failed: {e}") from e

    raise JiraDetectionError("Request failed after all retries")


def detect_deployment_type(force_refresh: bool = False) -> str:
    """Detect the Jira deployment type (Cloud, DataCenter, or Server).

    Uses /rest/api/2/serverInfo which works on all Jira versions.
    Results are cached per-session to avoid repeated API calls.

    Args:
        force_refresh: If True, bypass the cache and make a new request.

    Returns:
        Deployment type string: "Cloud", "DataCenter", or "Server".

    Raises:
        JiraDetectionError: If detection fails.
    """
    creds = get_credentials("jira")
    if not creds.url:
        raise JiraDetectionError("No Jira URL configured")

    # Check cache unless force refresh requested
    if not force_refresh and creds.url in _deployment_cache:
        return _deployment_cache[creds.url]["deployment_type"]

    try:
        server_info = _make_detection_request(
            url=creds.url,
            endpoint="rest/api/2/serverInfo",
            email=creds.email,
            token=creds.token,
            username=creds.username,
            password=creds.password,
        )

        # Extract deployment type from response
        # Cloud: {"deploymentType": "Cloud", ...}
        # DC:    {"deploymentType": "DataCenter", ...}
        # Server: {"deploymentType": "Server", ...}
        deployment_type = server_info.get("deploymentType", "Server")

        # Determine API version
        api_version = "3" if deployment_type == "Cloud" else "2"

        # Cache the result
        _deployment_cache[creds.url] = {
            "deployment_type": deployment_type,
            "api_version": api_version,
        }

        return deployment_type

    except Exception as e:
        raise JiraDetectionError(f"Failed to detect deployment type: {e}") from e


def get_api_version() -> str:
    """Get the appropriate API version for the current Jira instance.

    Returns:
        "3" for Cloud, "2" for DataCenter/Server.
    """
    creds = get_credentials("jira")
    if creds.url and creds.url in _deployment_cache:
        return _deployment_cache[creds.url]["api_version"]

    # Trigger detection to populate cache
    detect_deployment_type()

    if creds.url and creds.url in _deployment_cache:
        return _deployment_cache[creds.url]["api_version"]

    # Default to v2 if detection fails (more compatible)
    return "2"


def api_path(endpoint: str) -> str:
    """Construct the full API path with the correct version.

    Args:
        endpoint: API endpoint without version prefix (e.g., "search", "issue/DEMO-123").

    Returns:
        Full path with version (e.g., "rest/api/3/search" or "rest/api/2/search").
    """
    version = get_api_version()
    return f"rest/api/{version}/{endpoint.lstrip('/')}"


def automation_path(endpoint: str) -> str:
    """Construct the gateway path for the Automation Rule Management API.

    Uses the gateway path (``{site}/gateway/api/automation/...``) so
    existing Jira Cloud credentials (email + API token) work without a
    separate auth flow.  Cloud-only.

    Args:
        endpoint: Automation API endpoint (e.g., ``rule/summary``).

    Returns:
        Full gateway path string.

    Raises:
        APIError: If the instance is not Cloud or the Cloud ID cannot
            be determined.
    """
    cloud_id = get_cloud_id()
    return f"gateway/api/automation/public/jira/{cloud_id}/rest/v1/{endpoint.lstrip('/')}"


_INLINE_RE = re.compile(r"(\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)]+)\))")


def _parse_inline(text: str) -> list[dict[str, Any]]:
    """Parse inline markdown (bold, links) into ADF text nodes."""
    nodes: list[dict[str, Any]] = []
    pos = 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > pos:
            nodes.append({"type": "text", "text": text[pos : m.start()]})
        if m.group(2) is not None:
            nodes.append({"type": "text", "text": m.group(2), "marks": [{"type": "strong"}]})
        elif m.group(3) is not None:
            nodes.append(
                {
                    "type": "text",
                    "text": m.group(3),
                    "marks": [{"type": "link", "attrs": {"href": m.group(4)}}],
                }
            )
        pos = m.end()
    if pos < len(text):
        nodes.append({"type": "text", "text": text[pos:]})
    return nodes or [{"type": "text", "text": ""}]


def _parse_markdown_to_adf(text: str) -> list[dict[str, Any]]:
    """Parse markdown text into a list of ADF block nodes."""
    lines = text.split("\n")
    blocks: list[dict[str, Any]] = []
    pending_lines: list[str] = []
    list_items: list[dict[str, Any]] = []
    table_rows: list[dict[str, Any]] = []
    i = 0

    def _flush_pending() -> None:
        if pending_lines:
            joined = " ".join(pending_lines)
            blocks.append({"type": "paragraph", "content": _parse_inline(joined)})
            pending_lines.clear()

    def _flush_list() -> None:
        if list_items:
            blocks.append({"type": "bulletList", "content": list(list_items)})
            list_items.clear()

    def _flush_table() -> None:
        if table_rows:
            blocks.append(
                {
                    "type": "table",
                    "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                    "content": list(table_rows),
                }
            )
            table_rows.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Blank line — paragraph separator
        if not stripped:
            _flush_pending()
            _flush_list()
            _flush_table()
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$", stripped):
            _flush_pending()
            _flush_list()
            _flush_table()
            blocks.append({"type": "rule"})
            i += 1
            continue

        # Heading
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            _flush_pending()
            _flush_list()
            _flush_table()
            level = len(heading_match.group(1))
            blocks.append(
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": _parse_inline(heading_match.group(2)),
                }
            )
            i += 1
            continue

        # Bullet list item
        list_match = re.match(r"^[-*]\s+(.+)$", stripped)
        if list_match:
            _flush_pending()
            _flush_table()
            list_items.append(
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": _parse_inline(list_match.group(1)),
                        }
                    ],
                }
            )
            i += 1
            continue

        # Table header row (|| cell || cell ||)
        if stripped.startswith("||"):
            _flush_pending()
            _flush_list()
            cells = [c.strip() for c in stripped.strip("|").split("||") if c.strip()]
            row_content = [
                {
                    "type": "tableHeader",
                    "content": [{"type": "paragraph", "content": _parse_inline(c)}],
                }
                for c in cells
            ]
            table_rows.append({"type": "tableRow", "content": row_content})
            i += 1
            continue

        # Table body row (| cell | cell |)
        if stripped.startswith("|") and not stripped.startswith("||"):
            _flush_pending()
            _flush_list()
            cells = [c.strip() for c in stripped.strip("|").split("|") if c.strip()]
            row_content = [
                {
                    "type": "tableCell",
                    "content": [{"type": "paragraph", "content": _parse_inline(c)}],
                }
                for c in cells
            ]
            table_rows.append({"type": "tableRow", "content": row_content})
            i += 1
            continue

        # Plain text line — accumulate for paragraph
        _flush_list()
        _flush_table()
        pending_lines.append(stripped)
        i += 1

    _flush_pending()
    _flush_list()
    _flush_table()

    return blocks or [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]


def format_rich_text(text: str) -> dict[str, Any] | str:
    """Format text for the appropriate Jira API version.

    Cloud API (v3) requires Atlassian Document Format (ADF).
    Parses markdown (headings, bold, links, lists, tables, rules)
    into proper ADF nodes.

    Data Center/Server API (v2) uses plain text.

    Args:
        text: Markdown or plain text content.

    Returns:
        ADF document dict for Cloud, plain string for DC/Server.
    """
    version = get_api_version()

    if version == "3":
        return {
            "type": "doc",
            "version": 1,
            "content": _parse_markdown_to_adf(text),
        }
    else:
        return text


def is_cloud() -> bool:
    """Check if the current Jira instance is Cloud.

    Returns:
        True if Cloud, False otherwise.
    """
    try:
        return detect_deployment_type() == "Cloud"
    except JiraDetectionError:
        return False


def clear_cache() -> None:
    """Clear the deployment type cache.

    Useful for testing or when switching between Jira instances.
    """
    _deployment_cache.clear()


def get_cloud_id() -> str:
    """Get the Atlassian Cloud ID for the current Jira instance.

    Fetches from ``{base_url}/_edge/tenant_info`` and caches the result
    in ``_deployment_cache``.

    Returns:
        The Cloud ID string.

    Raises:
        APIError: If the instance is not Cloud or the request fails.
    """
    if not is_cloud():
        raise APIError("Automation rules are only available on Jira Cloud")

    creds = get_credentials("jira")
    if not creds.url:
        raise APIError("No Jira URL configured")

    cached = _deployment_cache.get(creds.url, {})
    if "cloud_id" in cached:
        return cached["cloud_id"]

    url = f"{creds.url.rstrip('/')}/_edge/tenant_info"
    response = requests.get(url, timeout=10)
    if not response.ok:
        raise APIError(
            f"Failed to fetch Cloud ID: {response.status_code} {response.reason}",
            status_code=response.status_code,
            response=response.text,
        )

    cloud_id = response.json().get("cloudId")
    if not cloud_id:
        raise APIError("Could not determine Cloud ID from tenant info")

    _deployment_cache.setdefault(creds.url, {})["cloud_id"] = cloud_id
    return cloud_id


def detect_scriptrunner_support(force_refresh: bool = False) -> dict[str, Any]:
    """Detect if ScriptRunner is available and which features are supported.

    ScriptRunner Enhanced Search provides advanced JQL functions like:
    - issueFunction in linkedIssuesOf()
    - issueFunction in subtasksOf()
    - issueFunction in parentsOf()
    - issueFunction in hasSubtasks()
    - issueFunction in hasLinks()
    And many more...

    Note: ScriptRunner works differently on Cloud vs Data Center/Server:
    - Cloud: Uses Atlassian Marketplace app with REST API endpoints
    - DC/Server: Self-hosted plugin with different API structure

    Args:
        force_refresh: If True, bypass the cache and make a new request.

    Returns:
        Dictionary with keys:
        - "available": bool - Whether ScriptRunner is installed
        - "version": str | None - ScriptRunner version if detected
        - "type": str - "cloud", "datacenter", or "unknown"
        - "enhanced_search": bool - Whether Enhanced Search is available

    Raises:
        APIError: If the detection request fails.
    """
    creds = get_credentials("jira")
    if not creds.url:
        return {
            "available": False,
            "version": None,
            "type": "unknown",
            "enhanced_search": False,
        }

    # Check cache unless force refresh requested
    if not force_refresh and creds.url in _deployment_cache:
        cached = _deployment_cache[creds.url]
        if "scriptrunner" in cached:
            return cached["scriptrunner"]  # type: ignore

    deployment_type = detect_deployment_type()
    result = {
        "available": False,
        "version": None,
        "type": deployment_type.lower() if deployment_type else "unknown",
        "enhanced_search": False,
    }

    try:
        if deployment_type == "Cloud":
            # Cloud: Try to access ScriptRunner Enhanced Search REST API
            # Endpoint: /rest/scriptrunner/latest/canned/com.onresolve.scriptrunner.canned.jira.utils.IssuePickerService
            try:
                # Try a simple test query to see if the endpoint exists
                endpoint = "rest/scriptrunner/latest/canned/com.onresolve.scriptrunner.canned.jira.utils.IssuePickerService"
                response = get("jira", endpoint, params={"query": ""})

                # If we get here without error, ScriptRunner is available
                result["available"] = True
                result["enhanced_search"] = True

                # Try to get version info from installed apps API
                try:
                    apps_response = get("jira", "rest/plugins/1.0/")
                    if isinstance(apps_response, dict):
                        plugins = apps_response.get("plugins", [])
                        for plugin in plugins:
                            if "scriptrunner" in plugin.get("key", "").lower():
                                result["version"] = plugin.get("version")
                                break
                except Exception:
                    # Version detection is optional
                    pass

            except APIError:
                # ScriptRunner not available on Cloud
                pass

        else:  # DataCenter or Server
            # DC/Server: Check for ScriptRunner plugin via UPM (Universal Plugin Manager)
            # Endpoint: /rest/plugins/1.0/
            try:
                response = get("jira", "rest/plugins/1.0/")
                if isinstance(response, dict):
                    plugins = response.get("plugins", [])
                    for plugin in plugins:
                        plugin_key = plugin.get("key", "")
                        if "scriptrunner" in plugin_key.lower():
                            result["available"] = True
                            result["version"] = plugin.get("version")
                            result["enhanced_search"] = plugin.get("enabled", False)
                            break
            except APIError:
                # Plugin API not accessible
                pass

    except Exception:
        # Any error means ScriptRunner is not reliably available
        pass

    # Cache the result
    if creds.url in _deployment_cache:
        _deployment_cache[creds.url]["scriptrunner"] = result
    else:
        _deployment_cache[creds.url] = {"scriptrunner": result}  # type: ignore

    return result


def validate_jql_for_scriptrunner(jql: str) -> dict[str, Any]:
    """Validate if a JQL query uses ScriptRunner functions and if they're supported.

    Args:
        jql: JQL query string to validate.

    Returns:
        Dictionary with keys:
        - "uses_scriptrunner": bool - Whether query uses ScriptRunner functions
        - "functions_detected": list[str] - List of ScriptRunner functions found
        - "supported": bool - Whether ScriptRunner is available for this query
        - "warning": str | None - Warning message if unsupported functions are used

    Example:
        >>> validate_jql_for_scriptrunner('issue in linkedIssuesOf("PROJ-123")')
        {
            "uses_scriptrunner": True,
            "functions_detected": ["linkedIssuesOf"],
            "supported": True,
            "warning": None
        }
    """
    # Common ScriptRunner Enhanced Search functions
    scriptrunner_functions = [
        # Link-related functions
        "linkedIssuesOf",
        "linkedIssuesOfAll",
        "linkedIssuesOfRecursive",
        "hasLinks",
        "hasLinkType",
        "issuesWithRemoteLinks",
        "hasRemoteLinks",
        # Hierarchy functions
        "subtasksOf",
        "parentsOf",
        "hasSubtasks",
        "epicsOf",
        "issuesInEpics",
        # Comment and user activity
        "commentedByUser",
        "issuesWithComments",
        "lastUpdatedBy",
        # Transitions and workflow
        "transitionedIssues",
        "transitionedBy",
        "transitionedFrom",
        "transitionedTo",
        # Field-based functions
        "issuesWithFieldValue",
        "hasFieldValue",
        "lastUpdated",
        # General purpose
        "expression",
        "searchIssues",
    ]

    # Detect which functions are used
    functions_detected = []
    jql_lower = jql.lower()

    for func in scriptrunner_functions:
        if func.lower() in jql_lower:
            functions_detected.append(func)

    uses_scriptrunner = len(functions_detected) > 0

    # Check if ScriptRunner is available
    scriptrunner_info = detect_scriptrunner_support()
    supported = scriptrunner_info["available"] and scriptrunner_info["enhanced_search"]

    warning = None
    if uses_scriptrunner and not supported:
        deployment_type = scriptrunner_info["type"]
        warning = (
            f"This JQL query uses ScriptRunner functions ({', '.join(functions_detected)}) "
            f"but ScriptRunner Enhanced Search is not detected on this {deployment_type} instance. "
            "The query may fail."
        )

    return {
        "uses_scriptrunner": uses_scriptrunner,
        "functions_detected": functions_detected,
        "supported": supported,
        "warning": warning,
    }


# ============================================================================
# HTTP/REST UTILITIES
# ============================================================================


class APIError(Exception):
    """Exception raised for API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


def _get_jira_auth_method(creds: Credentials) -> tuple[tuple[str, str] | None, dict[str, str]]:
    """Determine the appropriate Jira authentication method.

    Cloud uses email + API token as basic auth.
    Data Center/Server uses Bearer token authentication.

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
        # DC/Server: Bearer token
        if creds.token:
            headers["Authorization"] = f"Bearer {creds.token}"

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
        service: Service name (e.g., "jira").
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
        raise APIError(f"No valid credentials found for {service}. Run: python jira.py check")

    url = f"{creds.url.rstrip('/')}/{endpoint.lstrip('/')}"

    # Build headers with authentication
    request_headers = headers.copy() if headers else {}
    request_headers.setdefault("Content-Type", "application/json")
    request_headers.setdefault("Accept", "application/json")

    # Add authentication based on service type
    auth = None
    if service == "jira" and creds.token:
        # Use Jira-specific auth detection
        auth, auth_headers = _get_jira_auth_method(creds)
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

    if response.status_code == 204 or not response.text.strip():
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


def ensure_field_included(fields: list[str] | None, field: str) -> list[str]:
    """Ensure a field is included in the fields list.

    If fields is None, starts from DEFAULT_FIELDS.
    Appends the field if not already present.
    """
    if fields is None:
        fields = list(DEFAULT_FIELDS)
    if field not in fields:
        return [*fields, field]
    return fields


_ISSUE_FILE_KNOWN_KEYS = frozenset(
    {"summary", "project", "type", "priority", "labels", "assignee", "fields", "links"}
)


def parse_issue_file(file_path: str) -> tuple[dict[str, Any], str | None]:
    """Parse a markdown file with YAML frontmatter into issue fields and description.

    Args:
        file_path: Path to the markdown file.

    Returns:
        Tuple of (fields_dict, body_text_or_none).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If frontmatter is missing, empty, or contains invalid YAML.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        raise ValueError("file must start with '---' frontmatter delimiter")

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("missing closing '---' frontmatter delimiter")

    fm_text = "\n".join(lines[1:end_idx])
    if not fm_text.strip():
        raise ValueError("frontmatter is empty")

    try:
        fields = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in frontmatter: {exc}") from exc

    if not isinstance(fields, dict):
        raise ValueError("frontmatter must be a YAML mapping")

    unknown = set(fields.keys()) - _ISSUE_FILE_KNOWN_KEYS
    if unknown:
        print(
            f"Warning: unrecognized frontmatter keys: {', '.join(sorted(unknown))}",
            file=sys.stderr,
        )

    for key in ("summary", "project", "type", "priority", "assignee"):
        if key in fields and fields[key] is not None:
            fields[key] = str(fields[key])

    if "labels" in fields and isinstance(fields["labels"], str):
        fields["labels"] = [lbl.strip() for lbl in fields["labels"].split(",")]

    if "links" in fields:
        raw_links = fields["links"]
        if not isinstance(raw_links, list):
            raise ValueError("'links' must be a list")
        normalized: list[tuple[str, str]] = []
        for i, entry in enumerate(raw_links):
            if not isinstance(entry, dict) or len(entry) != 1:
                raise ValueError(
                    f"links[{i}]: each entry must be a single-key mapping (e.g. 'blocks: DEMO-456')"
                )
            link_type, target = next(iter(entry.items()))
            normalized.append((str(link_type), str(target)))
        fields["links"] = normalized

    body = "\n".join(lines[end_idx + 1 :]).strip() or None

    return fields, body


def _normalize_field_name(name: str) -> str:
    """Normalize a field name to snake_case for use as a config key."""
    return name.strip().lower().replace(" ", "_")


def resolve_custom_field(
    friendly_name: str,
    custom_fields: dict[str, str] | None,
) -> str | None:
    """Look up a custom field ID from the configured mapping."""
    if custom_fields:
        key = _normalize_field_name(friendly_name)
        return custom_fields.get(key)
    return None


def discover_custom_field(friendly_name: str) -> tuple[str, str | None] | None:
    """Discover a custom field ID by querying the Jira fields endpoint.

    Searches for a field whose name matches the friendly name
    (case-insensitive, spaces/underscores interchangeable).

    Returns (field_id, schema_type) if exactly one match is found, None otherwise.
    """
    search_name = _normalize_field_name(friendly_name)
    all_fields = list_fields()
    matches = [f for f in all_fields if _normalize_field_name(f.get("name", "")) == search_name]

    if len(matches) == 1:
        field_id = matches[0].get("id", matches[0].get("fieldId"))
        field_name = matches[0].get("name")
        schema_type = matches[0].get("schema", {}).get("type")
        print(
            f"Discovered field: {friendly_name} -> {field_id} ({field_name}, type: {schema_type})"
        )
        return field_id, schema_type

    if len(matches) > 1:
        print(f"Multiple fields match '{friendly_name}':", file=sys.stderr)
        for m in matches:
            print(f"  {m.get('id', m.get('fieldId'))}: {m.get('name')}", file=sys.stderr)
        return None

    print(f"No field found matching '{friendly_name}'", file=sys.stderr)
    return None


def resolve_or_discover_field(
    friendly_name: str,
    custom_fields: dict[str, str] | None,
) -> str | None:
    """Resolve a custom field ID, discovering and saving it if needed."""
    field_id = resolve_custom_field(friendly_name, custom_fields)
    if field_id:
        return field_id

    result = discover_custom_field(friendly_name)
    if not result:
        return None

    field_id, schema_type = result
    key = _normalize_field_name(friendly_name)
    config = load_config("jira") or {}
    defaults = config.setdefault("defaults", {})
    cf = defaults.setdefault("custom_fields", {})
    cf[key] = field_id
    if schema_type:
        schemas = defaults.setdefault("custom_field_schemas", {})
        schemas[key] = schema_type
    save_config("jira", config)
    print(f"Saved mapping: {key} -> {field_id} in ~/.config/agent-skills/jira.yaml")
    return field_id


def validate_custom_fields(custom_fields: dict[str, str]) -> list[str]:
    """Validate that all configured custom field IDs exist in Jira.

    Returns a list of error messages for fields that don't exist.
    """
    all_fields = list_fields()
    known_ids = {f.get("id", f.get("fieldId")) for f in all_fields}
    errors = []
    for friendly_name, field_id in custom_fields.items():
        if field_id not in known_ids:
            errors.append(f"  {friendly_name}: {field_id} (not found in Jira)")
    return errors


def _coerce_by_type(field_type: str, value: str, items_type: str = "") -> Any:
    """Wrap a string value based on the Jira field schema type."""
    if field_type == "option":
        return {"value": value}
    if field_type in ("securitylevel", "security-level"):
        return {"name": value}
    if field_type == "number":
        try:
            return float(value)
        except ValueError:
            return value
    if field_type == "array" and items_type == "option":
        return [{"value": v.strip()} for v in value.split(",")]
    if field_type == "user":
        if is_cloud():
            return {"accountId": value}
        return {"name": value}
    return value


def coerce_field_value(
    field_id: str,
    value: str,
    schema_type: str | None = None,
) -> Any:
    """Coerce a string value to the correct type for a Jira field.

    Uses the cached schema_type if available (from custom_field_schemas config).
    Falls back to querying the fields API if no schema type is provided.
    """
    if schema_type:
        return _coerce_by_type(schema_type, value)

    all_fields = list_fields()
    field_meta = next((f for f in all_fields if f.get("id", f.get("fieldId")) == field_id), None)
    if not field_meta:
        return value

    schema = field_meta.get("schema", {})
    return _coerce_by_type(schema.get("type", ""), value, schema.get("items", ""))


def _format_custom_field_value(value: Any) -> str:
    """Format a custom field value for display."""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    if isinstance(value, dict):
        return value.get("value", value.get("name", str(value)))
    return str(value)


def _append_custom_fields(text: str, fields: dict, custom_fields: dict[str, str] | None) -> str:
    """Append configured custom field values to formatted output."""
    if not custom_fields:
        return text
    for friendly_name, field_id in custom_fields.items():
        value = fields.get(field_id)
        if value is not None:
            label = friendly_name.replace("_", " ").title()
            text += f"\n- **{label}:** {_format_custom_field_value(value)}"
    return text


def format_issue(issue: dict[str, Any], custom_fields: dict[str, str] | None = None) -> str:
    """Format a Jira issue for display.

    Args:
        issue: Jira issue dictionary.
        custom_fields: Mapping of friendly names to custom field IDs.

    Returns:
        Formatted issue string.
    """
    fields = issue.get("fields", {})
    key = issue.get("key", "N/A")
    summary = fields.get("summary", "No summary")
    status = fields.get("status", {}).get("name", "Unknown")
    assignee = fields.get("assignee", {})
    assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
    priority = fields.get("priority", {})
    priority_name = priority.get("name", "None") if priority else "None"

    resolution_obj = fields.get("resolution")
    resolution_name = resolution_obj.get("name") if resolution_obj else None

    issue_type = fields.get("issuetype", {})
    issue_type_name = issue_type.get("name") if issue_type else None

    result = f"### {key}: {summary}\n"
    if issue_type_name:
        result += f"- **Type:** {issue_type_name}\n"
    result += f"- **Status:** {status}\n"
    if resolution_name:
        result += f"- **Resolution:** {resolution_name}\n"
    result += f"- **Assignee:** {assignee_name}\n- **Priority:** {priority_name}"

    return _append_custom_fields(result, fields, custom_fields)


def format_issues_list(
    issues: list[dict[str, Any]], custom_fields: dict[str, str] | None = None
) -> str:
    """Format a list of Jira issues for display.

    Args:
        issues: List of Jira issue dictionaries.
        custom_fields: Mapping of friendly names to custom field IDs.

    Returns:
        Formatted table string.
    """
    if not issues:
        return "No issues found"

    parts = []
    for issue in issues:
        fields = issue.get("fields", {})
        assignee = fields.get("assignee", {})
        key = issue.get("key", "N/A")
        summary = fields.get("summary", "No summary")
        status = fields.get("status", {}).get("name", "Unknown")
        assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
        resolution_obj = fields.get("resolution")
        resolution_name = resolution_obj.get("name") if resolution_obj else None
        issue_type = fields.get("issuetype", {})
        issue_type_name = issue_type.get("name") if issue_type else None
        entry = f"### {key}: {summary}\n"
        if issue_type_name:
            entry += f"- **Type:** {issue_type_name}\n"
        entry += f"- **Status:** {status}\n"
        if resolution_name:
            entry += f"- **Resolution:** {resolution_name}\n"
        entry += f"- **Assignee:** {assignee_name}"
        entry = _append_custom_fields(entry, fields, custom_fields)
        parts.append(entry)

    return "\n\n".join(parts)


# ============================================================================
# AUTOMATION RULES (Cloud-only)
# ============================================================================


def list_automation_rules(
    *,
    project_key: str | None = None,
    state: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List automation rule summaries with optional filtering.

    Args:
        project_key: Filter to rules scoped to this project.
        state: Filter by state (``ENABLED`` or ``DISABLED``).
        limit: Maximum rules to return (paginates automatically).

    Returns:
        List of rule summary dicts.
    """
    endpoint = automation_path("rule/summary")
    results: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        params: dict[str, Any] = {"limit": min(limit - len(results), 100)}
        if cursor:
            params["cursor"] = cursor

        response = get("jira", endpoint, params=params)
        data = response.get("data", [])
        results.extend(data)

        links = response.get("links", {})
        next_link = links.get("next")
        if not next_link or len(results) >= limit:
            break
        # The next link contains query params; extract cursor value
        import urllib.parse

        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(next_link).query)
        cursor = parsed.get("cursor", [None])[0]
        if not cursor:
            break

    # Filter by project scope if requested
    if project_key:
        filtered = []
        project_key_upper = project_key.upper()
        for rule in results:
            scope_aris = rule.get("ruleScopeARIs", [])
            if _rule_matches_project(scope_aris, project_key_upper):
                filtered.append(rule)
        results = filtered

    # Filter by state if requested
    if state:
        state_upper = state.upper()
        results = [r for r in results if r.get("state", "").upper() == state_upper]

    return results


def _rule_matches_project(scope_aris: list[str], project_key: str) -> bool:
    """Check whether any scope ARI matches the given project key.

    Scope ARIs look like ``ari:cloud:jira:{siteId}:project/{projectId}``
    but can also be global.  We also resolve the project key to its ID
    when possible.
    """
    if not scope_aris:
        return True  # global rules match all projects

    for ari in scope_aris:
        if "project/" in ari:
            # Try to resolve project key to id for matching
            try:
                project = get("jira", api_path(f"project/{project_key}"))
                project_id = str(project.get("id", ""))
                if project_id and f"project/{project_id}" in ari:
                    return True
            except APIError:
                pass
    return False


# Cache for project key → id lookups used by automation scope matching
_project_id_cache: dict[str, str] = {}


def _resolve_project_id(project_key: str) -> str | None:
    """Resolve a project key to its numeric ID, with caching."""
    if project_key in _project_id_cache:
        return _project_id_cache[project_key]
    try:
        project = get("jira", api_path(f"project/{project_key}"))
        pid = str(project.get("id", ""))
        if pid:
            _project_id_cache[project_key] = pid
        return pid or None
    except APIError:
        return None


def get_automation_rule(rule_uuid: str) -> dict[str, Any]:
    """Fetch the full definition of an automation rule.

    Args:
        rule_uuid: The rule UUID.

    Returns:
        The ``RuleConfigResponse`` dict with ``rule`` and ``connections`` keys.
    """
    endpoint = automation_path(f"rule/{rule_uuid}")
    return get("jira", endpoint)


def format_automation_summary(rule: dict[str, Any]) -> str:
    """Format a rule summary for list output.

    Args:
        rule: A rule summary dict from the list endpoint.

    Returns:
        Markdown string.
    """
    name = rule.get("name", "Untitled")
    state = rule.get("state", "UNKNOWN")
    author = rule.get("authorAccountId", "unknown")
    labels = rule.get("labels", [])
    uuid = rule.get("uuid", "")
    scope_aris = rule.get("ruleScopeARIs", [])

    state_icon = "ON" if state == "ENABLED" else "OFF"

    parts = [f"### {name}"]
    parts.append(f"- **State:** {state_icon} ({state})")
    parts.append(f"- **Author:** {author}")
    if labels:
        parts.append(f"- **Labels:** {', '.join(labels)}")
    if scope_aris:
        scopes = [_format_scope_ari(ari) for ari in scope_aris]
        parts.append(f"- **Scope:** {', '.join(scopes)}")
    parts.append(f"- **UUID:** `{uuid}`")

    return "\n".join(parts)


def _format_scope_ari(ari: str) -> str:
    """Extract a human-readable scope from an ARI string."""
    if "project/" in ari:
        project_id = ari.rsplit("project/", 1)[-1]
        return f"Project #{project_id}"
    if ari.endswith(":site"):
        return "Global (site)"
    return ari


def format_automation_detail(rule_config: dict[str, Any]) -> str:
    """Format a full rule definition as a readable markdown document.

    Args:
        rule_config: The ``RuleConfigResponse`` from the get endpoint.

    Returns:
        Markdown string describing the rule step by step.
    """
    rule = rule_config.get("rule", {})
    name = rule.get("name", "Untitled")
    description = rule.get("description", "")
    state = rule.get("state", "UNKNOWN")
    author = rule.get("authorAccountId", "unknown")
    labels = rule.get("labels", [])
    scope_aris = rule.get("ruleScopeARIs", [])
    created = rule.get("created")
    updated = rule.get("updated")
    notify = rule.get("notifyOnError", "")
    write_access = rule.get("writeAccessType", "")
    collaborators = rule.get("collaborators", [])
    can_other_trigger = rule.get("canOtherRuleTrigger", False)

    parts = [f"## {name}"]

    # Metadata
    state_icon = "ON" if state == "ENABLED" else "OFF"
    parts.append(f"\n- **State:** {state_icon} ({state})")
    parts.append(f"- **Author:** {author}")
    if collaborators:
        parts.append(f"- **Collaborators:** {', '.join(collaborators)}")
    if labels:
        parts.append(f"- **Labels:** {', '.join(labels)}")
    if scope_aris:
        scopes = [_format_scope_ari(ari) for ari in scope_aris]
        parts.append(f"- **Scope:** {', '.join(scopes)}")
    if created:
        parts.append(f"- **Created:** {_format_timestamp(created)}")
    if updated:
        parts.append(f"- **Updated:** {_format_timestamp(updated)}")
    if notify:
        parts.append(f"- **Notify on error:** {notify}")
    if write_access:
        parts.append(f"- **Write access:** {write_access}")
    if can_other_trigger:
        parts.append("- **Can be triggered by other rules:** yes")
    if description:
        parts.append(f"\n{description}")

    # Trigger
    trigger = rule.get("trigger")
    if trigger:
        parts.append("\n### Trigger")
        parts.append(_format_component(trigger, prefix="**When:**"))
        trigger_conditions = trigger.get("conditions", [])
        if trigger_conditions:
            for cond in trigger_conditions:
                parts.append(_format_component(cond, prefix="  - **If:**"))

    # Components (conditions, actions, branches)
    components = rule.get("components", [])
    if components:
        conditions = [c for c in components if c.get("component") == "CONDITION"]
        actions = [c for c in components if c.get("component") == "ACTION"]
        branches = [c for c in components if c.get("component") == "BRANCH"]
        other = [
            c for c in components if c.get("component") not in ("CONDITION", "ACTION", "BRANCH")
        ]

        if conditions:
            parts.append("\n### Conditions")
            for i, cond in enumerate(conditions, 1):
                parts.append(f"{i}. {_format_component(cond, prefix='**If:**')}")
                for sub in cond.get("conditions", []):
                    parts.append(f"   - {_format_component(sub, prefix='**And:**')}")

        if actions:
            parts.append("\n### Actions")
            for i, action in enumerate(actions, 1):
                parts.append(f"{i}. {_format_component(action, prefix='**Then:**')}")
                for sub_cond in action.get("conditions", []):
                    parts.append(f"   - {_format_component(sub_cond, prefix='**If:**')}")
                for child in action.get("children", []):
                    parts.append(f"   - {_format_component(child, prefix='**→**')}")

        if branches:
            parts.append("\n### Branches")
            for i, branch in enumerate(branches, 1):
                parts.append(f"{i}. {_format_component(branch, prefix='**Branch:**')}")
                for child in branch.get("children", []):
                    parts.append(f"   - {_format_component(child, prefix='**→**')}")
                for sub_cond in branch.get("conditions", []):
                    parts.append(f"   - {_format_component(sub_cond, prefix='**If:**')}")

        if other:
            parts.append("\n### Other Components")
            for i, comp in enumerate(other, 1):
                component_type = comp.get("component", "UNKNOWN")
                parts.append(f"{i}. {_format_component(comp, prefix=f'**{component_type}:**')}")

    # Connections
    connections = rule_config.get("connections", [])
    if connections:
        parts.append("\n### Connections")
        for conn in connections:
            target = conn.get("connectionTargetKey", "unknown")
            auth_type = conn.get("authType", "unknown")
            parts.append(f"- **{target}** (auth: {auth_type})")

    return "\n".join(parts)


def _format_timestamp(ts: float | int) -> str:
    """Format a Unix timestamp (seconds or milliseconds) as ISO date."""
    from datetime import datetime

    if ts > 1e12:
        ts = ts / 1000.0
    dt = datetime.fromtimestamp(ts, tz=UTC)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _format_component(component: dict[str, Any], *, prefix: str = "") -> str:
    """Format a single automation component (trigger, condition, or action).

    Parses the ``type`` and ``value`` fields to produce a human-readable
    description.
    """
    comp_type = component.get("type", "unknown")
    value_raw = component.get("value")

    # Make the type key human-readable
    readable_type = _humanise_component_type(comp_type)

    # Parse value JSON if present
    value_detail = ""
    if value_raw:
        try:
            value_obj = json.loads(value_raw) if isinstance(value_raw, str) else value_raw
            value_detail = _summarise_value(value_obj)
        except (json.JSONDecodeError, TypeError):
            value_detail = str(value_raw)

    line = f"{prefix} {readable_type}" if prefix else readable_type
    if value_detail:
        line += f" — {value_detail}"
    return line.strip()


# Common automation component type keys → human-readable names
_COMPONENT_TYPE_NAMES: dict[str, str] = {
    "jira.issue.event.trigger:created": "Issue created",
    "jira.issue.event.trigger:updated": "Issue updated",
    "jira.issue.event.trigger:transitioned": "Issue transitioned",
    "jira.issue.event.trigger:commented": "Comment added",
    "jira.issue.event.trigger:assigned": "Issue assigned",
    "jira.issue.event.trigger:deleted": "Issue deleted",
    "jira.issue.event.trigger:moved": "Issue moved",
    "jira.sprint.event.trigger:started": "Sprint started",
    "jira.sprint.event.trigger:completed": "Sprint completed",
    "jira.version.event.trigger:created": "Version created",
    "jira.version.event.trigger:released": "Version released",
    "jira.scheduled.trigger": "Scheduled",
    "jira.manual.trigger": "Manual trigger",
    "jira.incoming.webhook.trigger": "Incoming webhook",
    "jira.issue.field.changed.trigger": "Field value changed",
    "jira.worklog.event.trigger:created": "Work logged",
    "jira.issue.link.event.trigger:created": "Issue linked",
    "jira.issue.create.action": "Create issue",
    "jira.issue.edit.action": "Edit issue",
    "jira.issue.transition.action": "Transition issue",
    "jira.issue.assign.action": "Assign issue",
    "jira.issue.comment.action": "Add comment",
    "jira.issue.link.action": "Link issues",
    "jira.issue.delete.action": "Delete issue",
    "jira.issue.clone.action": "Clone issue",
    "jira.email.send.action": "Send email",
    "jira.webhook.action": "Send web request",
    "jira.lookup.issues.action": "Lookup issues (JQL)",
    "jira.create.variable.action": "Create variable",
    "jira.log.action": "Log action",
    "jira.branch.action": "Branch / related issues",
    "jira.condition.if.block": "If/else block",
    "jira.condition.jql": "JQL condition",
    "jira.condition.field": "Field condition",
    "jira.condition.user": "User condition",
    "jira.condition.issue.of.type": "Issue type condition",
    "jira.condition.issue.in.status": "Status condition",
    "jira.condition.issue.has.subtasks": "Has subtasks",
    "jira.condition.related.issues": "Related issues condition",
    "jira.condition.advanced": "Advanced condition",
}


def _humanise_component_type(type_key: str) -> str:
    """Convert a component type key to a human-readable label."""
    if type_key in _COMPONENT_TYPE_NAMES:
        return _COMPONENT_TYPE_NAMES[type_key]
    # Fallback: extract meaningful parts from the key
    parts = type_key.replace("jira.", "").replace(".", " ").replace(":", " — ")
    return parts.replace("_", " ").title()


def _summarise_value(value_obj: dict[str, Any] | list | str) -> str:
    """Produce a compact human-readable summary of a component's value config."""
    if isinstance(value_obj, str):
        return value_obj
    if isinstance(value_obj, list):
        return ", ".join(_summarise_value(v) for v in value_obj[:5])
    if not isinstance(value_obj, dict):
        return str(value_obj)

    # Pick the most informative fields from the value object
    interesting_keys = [
        "jql",
        "fieldId",
        "fieldValue",
        "value",
        "message",
        "body",
        "text",
        "name",
        "summary",
        "url",
        "to",
        "statusId",
        "issueType",
        "projectId",
        "accountId",
        "group",
        "schedule",
        "cron",
        "selectedFieldType",
        "compareFieldValue",
        "compareValue",
        "condition",
    ]

    snippets = []
    for key in interesting_keys:
        if key in value_obj:
            val = value_obj[key]
            if isinstance(val, dict):
                # Try to get a display value from nested objects
                display = val.get("displayName") or val.get("name") or val.get("value")
                if display:
                    snippets.append(f"{key}: {display}")
                else:
                    snippets.append(f"{key}: {json.dumps(val, ensure_ascii=False)}")
            elif isinstance(val, list):
                items = [
                    str(v.get("displayName", v.get("name", v)) if isinstance(v, dict) else v)
                    for v in val[:3]
                ]
                snippets.append(f"{key}: [{', '.join(items)}]")
            else:
                snippets.append(f"{key}: {val}")

    if snippets:
        return "; ".join(snippets)

    # Last resort: show compact JSON of first few keys
    short = {k: value_obj[k] for k in list(value_obj)[:3]}
    return json.dumps(short, ensure_ascii=False, default=str)


# ============================================================================
# SEARCH FUNCTIONALITY
# ============================================================================

DEFAULT_FIELDS = [
    "summary",
    "issuetype",
    "status",
    "resolution",
    "assignee",
    "priority",
    "created",
    "updated",
]


def search_issues(
    jql: str,
    max_results: int = 50,
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search for issues using JQL with automatic pagination.

    Supports standard JQL and ScriptRunner Enhanced Search functions.
    If ScriptRunner functions are detected in the query, the function
    will validate that ScriptRunner is available on the Jira instance
    and warn if it's not.

    Automatically paginates through results when the server returns
    fewer issues than the total matching the query, up to max_results.

    Args:
        jql: JQL query string (supports ScriptRunner functions).
        max_results: Maximum number of results to return.
        fields: List of fields to include in response.

    Returns:
        List of issue dictionaries.

    Raises:
        APIError: If the search fails.

    Example:
        >>> search_issues("project = DEMO AND status = Open")
    """
    fields = fields or DEFAULT_FIELDS

    validation = validate_jql_for_scriptrunner(jql)
    if validation["uses_scriptrunner"] and not validation["supported"]:
        funcs = ", ".join(validation["functions_detected"])
        msg = (
            f"Error: Query uses ScriptRunner functions ({funcs}) "
            f"which are not available on this Jira instance.\n"
        )
        if is_cloud():
            msg += (
                "ScriptRunner Enhanced Search is not supported on Jira Cloud.\n"
                "See references/jql-reference.md for Cloud-native alternatives."
            )
        else:
            msg += (
                "ScriptRunner Enhanced Search is not available on this instance.\n"
                "See references/jql-reference.md for standard JQL alternatives."
            )
        print(msg, file=sys.stderr)
        return []

    if is_cloud():
        return _search_issues_cloud(jql, max_results, fields)
    return _search_issues_datacenter(jql, max_results, fields)


def _warn_truncated_results(count: int) -> None:
    """Warn on stderr when results may be truncated by Jira's API limit."""
    print(
        f"Warning: Results may be truncated — Jira's API limits search to "
        f"~1000 issues. {count} results returned. Narrow your query with "
        f'date ranges (e.g. created >= "2025-01-01") or additional filters '
        f"to get complete results.",
        file=sys.stderr,
    )


def _search_issues_cloud(
    jql: str,
    max_results: int,
    fields: list[str],
) -> list[dict[str, Any]]:
    """Search with pagination for Jira Cloud (uses nextPageToken)."""
    all_issues: list[dict[str, Any]] = []
    next_page_token: str | None = None

    while len(all_issues) < max_results:
        page_size = min(max_results - len(all_issues), 100)
        data: dict[str, Any] = {
            "jql": jql,
            "maxResults": page_size,
            "fields": fields,
        }
        if next_page_token is not None:
            data["nextPageToken"] = next_page_token

        response = post("jira", api_path("search/jql"), data=data)

        if not isinstance(response, dict):
            break

        issues = response.get("issues", [])
        all_issues.extend(issues)

        next_page_token = response.get("nextPageToken")
        if not next_page_token or not issues:
            break

    result = all_issues[:max_results]
    if len(result) >= 1000 and next_page_token:
        _warn_truncated_results(len(result))
    return result


def _search_issues_datacenter(
    jql: str,
    max_results: int,
    fields: list[str],
) -> list[dict[str, Any]]:
    """Search with pagination for Jira Data Center (uses startAt/total)."""
    all_issues: list[dict[str, Any]] = []
    start_at = 0
    last_total = 0

    while len(all_issues) < max_results:
        page_size = min(max_results - len(all_issues), 100)
        response = get(
            "jira",
            api_path("search"),
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": page_size,
                "fields": ",".join(fields),
            },
        )

        if not isinstance(response, dict):
            break

        issues = response.get("issues", [])
        all_issues.extend(issues)

        last_total = response.get("total", 0)
        if not issues or start_at + len(issues) >= last_total:
            break

        start_at += len(issues)

    result = all_issues[:max_results]
    if last_total >= 1000 and len(result) < last_total:
        _warn_truncated_results(len(result))
    return result


# ============================================================================
# ISSUE MANAGEMENT
# ============================================================================


def get_issue(issue_key: str, fields: list[str] | None = None) -> dict[str, Any]:
    """Get an issue by key.

    Args:
        issue_key: The issue key (e.g., DEMO-123).
        fields: Optional list of fields to include in the response.

    Returns:
        Issue dictionary.
    """
    params = {}
    if fields:
        params["fields"] = ",".join(fields)
    response = get("jira", api_path(f"issue/{issue_key}"), params=params if params else None)
    if isinstance(response, dict):
        return response
    return {}


def get_project_issue_types(project: str) -> list[str]:
    """Get valid issue type names for a project via createmeta.

    Returns an empty list if the lookup fails.
    """
    try:
        response = get("jira", api_path(f"issue/createmeta/{project}/issuetypes"))
        if isinstance(response, dict):
            return [
                it["name"]
                for it in response.get("issueTypes", response.get("values", []))
                if isinstance(it, dict) and "name" in it
            ]
    except Exception:
        pass
    return []


def create_issue(
    project: str,
    issue_type: str,
    summary: str,
    description: str | None = None,
    priority: str | None = None,
    labels: list[str] | None = None,
    assignee: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new issue.

    Args:
        project: Project key.
        issue_type: Issue type name (e.g., Task, Bug, Story).
        summary: Issue summary.
        description: Issue description.
        priority: Priority name.
        labels: List of labels.
        assignee: Assignee account ID.
        extra_fields: Additional fields keyed by field ID.

    Returns:
        Created issue dictionary.
    """
    fields: dict[str, Any] = {
        "project": {"key": project},
        "issuetype": {"name": issue_type},
        "summary": summary,
    }

    if description:
        fields["description"] = format_rich_text(description)

    if priority:
        fields["priority"] = {"name": priority}

    if labels:
        fields["labels"] = labels

    if assignee:
        fields["assignee"] = {"accountId": assignee}

    if extra_fields:
        fields.update(extra_fields)

    response = post("jira", api_path("issue"), {"fields": fields})
    if isinstance(response, dict):
        return response
    return {}


def update_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    labels: list[str] | None = None,
    assignee: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update an existing issue.

    Args:
        issue_key: The issue key.
        summary: New summary.
        description: New description.
        priority: New priority name.
        labels: New labels.
        assignee: New assignee account ID.
        extra_fields: Additional fields keyed by field ID.

    Returns:
        Response dictionary (empty on success).
    """
    fields: dict[str, Any] = {}

    if summary:
        fields["summary"] = summary

    if description:
        fields["description"] = format_rich_text(description)

    if priority:
        fields["priority"] = {"name": priority}

    if labels is not None:
        fields["labels"] = labels

    if assignee:
        fields["assignee"] = {"accountId": assignee}

    if extra_fields:
        fields.update(extra_fields)

    if not fields:
        return {}

    response = put("jira", api_path(f"issue/{issue_key}"), {"fields": fields})
    if isinstance(response, dict):
        return response
    return {}


def get_link_types() -> list[dict[str, str]]:
    """Get available issue link types.

    Returns:
        List of dicts with 'name', 'inward', and 'outward' keys.
    """
    response = get("jira", api_path("issueLinkType"))
    if isinstance(response, dict):
        return [
            {
                "name": lt["name"],
                "inward": lt.get("inward", ""),
                "outward": lt.get("outward", ""),
            }
            for lt in response.get("issueLinkTypes", [])
            if isinstance(lt, dict) and "name" in lt
        ]
    return []


def create_link(source_key: str, link_type: str, target_key: str) -> None:
    """Create a link between two issues.

    Resolves the link type name against available types (case-insensitive),
    matching on name, inward, or outward labels to determine direction.

    Args:
        source_key: The issue being created/updated.
        link_type: Link type name (e.g. 'Blocks', 'is blocked by', 'Relates').
        target_key: The issue to link to.

    Raises:
        ValueError: If the link type is not recognized.
    """
    link_types = get_link_types()
    lt_lower = link_type.lower()

    resolved_name = None
    outward_key = source_key
    inward_key = target_key

    for lt in link_types:
        if lt_lower == lt["name"].lower():
            resolved_name = lt["name"]
            break
        if lt_lower == lt["outward"].lower():
            resolved_name = lt["name"]
            break
        if lt_lower == lt["inward"].lower():
            resolved_name = lt["name"]
            outward_key = target_key
            inward_key = source_key
            break

    if not resolved_name:
        valid = []
        for lt in link_types:
            valid.append(f"{lt['name']} (outward: {lt['outward']}, inward: {lt['inward']})")
        raise ValueError(f"Unknown link type '{link_type}'. Valid types:\n  " + "\n  ".join(valid))

    post(
        "jira",
        api_path("issueLink"),
        {
            "type": {"name": resolved_name},
            "outwardIssue": {"key": outward_key},
            "inwardIssue": {"key": inward_key},
        },
    )


def add_comment(issue_key: str, body: str, security_level: str | None = None) -> dict[str, Any]:
    """Add a comment to an issue.

    Args:
        issue_key: The issue key.
        body: Comment text.
        security_level: Optional security level name (e.g., "Internal", "Employees").
                       Makes the comment private and visible only to users with this security level.

    Returns:
        Created comment dictionary.
    """
    comment_body: dict[str, Any] = {"body": format_rich_text(body)}

    if security_level:
        comment_body["visibility"] = {"type": "group", "value": security_level}

    response = post("jira", api_path(f"issue/{issue_key}/comment"), comment_body)
    if isinstance(response, dict):
        return response
    return {}


# ============================================================================
# COMMENT RETRIEVAL
# ============================================================================


def _extract_text_from_adf(node: Any) -> str:
    """Recursively extract plain text from an ADF (Atlassian Document Format) node.

    For plain string bodies (Data Center), returns the string as-is.

    Args:
        node: ADF JSON node (dict) or plain text string.

    Returns:
        Extracted plain text.
    """
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    parts = []
    for child in node.get("content", []):
        parts.append(_extract_text_from_adf(child))
    return "".join(parts)


def get_comments(issue_key: str, max_results: int = 50) -> list[dict[str, Any]]:
    """Get comments on an issue with automatic pagination.

    Args:
        issue_key: The issue key (e.g., DEMO-123).
        max_results: Maximum number of comments to return.

    Returns:
        List of comment dictionaries.
    """
    all_comments: list[dict[str, Any]] = []
    start_at = 0

    while len(all_comments) < max_results:
        page_size = min(max_results - len(all_comments), 100)
        response = get(
            "jira",
            api_path(f"issue/{issue_key}/comment"),
            params={"startAt": start_at, "maxResults": page_size},
        )

        if not isinstance(response, dict):
            break

        comments = response.get("comments", [])
        all_comments.extend(comments)

        total = response.get("total", 0)
        if not comments or start_at + len(comments) >= total:
            break

        start_at += len(comments)

    return all_comments[:max_results]


def format_comments(comments: list[dict[str, Any]], issue_key: str) -> str:
    """Format comments for display.

    Args:
        comments: List of comment dictionaries from the Jira API.
        issue_key: The issue key for the heading.

    Returns:
        Formatted markdown string.
    """
    if not comments:
        return f"## Comments on {issue_key}\n\nNo comments found."

    parts = [f"## Comments on {issue_key}"]
    for comment in comments:
        author = comment.get("author", {})
        display_name = author.get("displayName", "Unknown")
        created = comment.get("created", "")
        # Trim to date + time (YYYY-MM-DDTHH:MM)
        if "T" in created:
            created = created[:16].replace("T", " ")
        body = _extract_text_from_adf(comment.get("body", ""))
        parts.append(f"\n### {display_name} ({created})\n{body}")

    return "\n".join(parts)


# ============================================================================
# CONTRIBUTOR EXTRACTION
# ============================================================================


def extract_contributors(issue: dict[str, Any], comments: list[dict[str, Any]]) -> set[str]:
    """Extract unique contributor display names from an issue and its comments.

    Contributors include: reporter, assignee, and comment authors.

    Args:
        issue: Jira issue dictionary.
        comments: List of comment dictionaries.

    Returns:
        Set of unique display names.
    """
    contributors: set[str] = set()
    fields = issue.get("fields", {})

    reporter = fields.get("reporter")
    if reporter and reporter.get("displayName"):
        contributors.add(reporter["displayName"])

    assignee = fields.get("assignee")
    if assignee and assignee.get("displayName"):
        contributors.add(assignee["displayName"])

    for comment in comments:
        author = comment.get("author", {})
        if author.get("displayName"):
            contributors.add(author["displayName"])

    return contributors


# ============================================================================
# USER RESOLUTION
# ============================================================================


def resolve_user(query: str) -> list[dict[str, Any]]:
    """Search for Jira users by email, name, or username.

    On Cloud, uses the user search API to find matching accounts.
    On Data Center/Server, returns the query as-is (usernames work directly in JQL).

    Args:
        query: Email address, display name, or username to search for.

    Returns:
        List of user dictionaries with keys: accountId, emailAddress, displayName, active.
    """
    if is_cloud():
        response = get("jira", api_path("user/search"), params={"query": query})
        if isinstance(response, list):
            return [
                {
                    "accountId": u.get("accountId", ""),
                    "emailAddress": u.get("emailAddress", ""),
                    "displayName": u.get("displayName", ""),
                    "active": u.get("active", True),
                }
                for u in response
            ]
        return []
    else:
        return [{"username": query, "displayName": query}]


def resolve_user_for_jql(user: str) -> str:
    """Resolve a user identifier to the appropriate JQL value.

    On Cloud: converts email/name to accountId (required for JQL).
    On DC/Server: returns the input unchanged (usernames work in JQL).

    Args:
        user: Email address, display name, or username.

    Returns:
        accountId string for Cloud, or original value for DC/Server.

    Raises:
        ValueError: If the user cannot be resolved on Cloud.
    """
    if not is_cloud():
        return user

    # If it already looks like an accountId (hex string), use as-is
    if len(user) >= 20 and all(c in "0123456789abcdef:" for c in user):
        return user

    users = resolve_user(user)
    if not users:
        raise ValueError(
            f"Could not find Jira Cloud user matching '{user}'. "
            "Use an accountId, email address, or display name."
        )

    # Prefer exact email match
    for u in users:
        if u.get("emailAddress", "").lower() == user.lower():
            return u["accountId"]

    # Fall back to first active result
    for u in users:
        if u.get("active", True):
            return u["accountId"]

    return users[0]["accountId"]


# ============================================================================
# CONTRIBUTOR SEARCH
# ============================================================================


def search_by_contributor(
    user: str,
    project: str | None = None,
    max_results: int = 50,
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search for issues where a user is a contributor.

    Always searches reporter and assignee. If ScriptRunner Enhanced Search
    is available, also searches for issues commented on by the user.

    On Jira Cloud, resolves email/name to accountId before searching.

    Args:
        user: Username, email, or accountId to search for.
        project: Optional project key to scope the search.
        max_results: Maximum number of results.
        fields: Optional list of fields to include.

    Returns:
        List of issue dictionaries.
    """
    user = resolve_user_for_jql(user)
    clauses = [f'reporter = "{user}" OR assignee = "{user}"']

    scriptrunner_info = detect_scriptrunner_support()
    if scriptrunner_info["available"] and scriptrunner_info["enhanced_search"]:
        clauses.append(f'issue in commentedByUser("{user}")')
    else:
        print(
            "Note: Comment-based contributor search requires ScriptRunner Enhanced Search. "
            "Only reporter and assignee matches are included.",
            file=sys.stderr,
        )

    jql = " OR ".join(clauses)
    if project:
        jql = f"project = {project} AND ({jql})"

    return search_issues(jql, max_results, fields)


# ============================================================================
# COLLABORATIVE EPICS
# ============================================================================


def _build_epic_children_jql(epic_key: str) -> str:
    """Build JQL to find children of an epic.

    Uses is_cloud() to build the correct JQL:
    - Cloud: "Epic Link" = KEY OR parent = KEY (covers classic and next-gen)
    - DC: "Epic Link" = KEY only

    Args:
        epic_key: The epic issue key.

    Returns:
        JQL query string.
    """
    if is_cloud():
        return f'"Epic Link" = {epic_key} OR parent = {epic_key}'
    return f'"Epic Link" = {epic_key}'


def get_epic_children(epic_key: str, fields: list[str] | None = None) -> list[dict[str, Any]]:
    """Get child issues of an epic.

    Args:
        epic_key: The epic issue key.
        fields: Optional list of fields to include.

    Returns:
        List of child issue dictionaries.
    """
    jql = _build_epic_children_jql(epic_key)
    return search_issues(jql, max_results=200, fields=fields)


def find_collaborative_epics(
    project: str | None = None,
    min_contributors: int = 2,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """Find epics with multiple contributors (assignees of child issues).

    Args:
        project: Optional project key to scope the search.
        min_contributors: Minimum number of unique assignees required.
        max_results: Maximum number of epics to check.

    Returns:
        List of dicts with keys: epic, children_count, contributors.
    """
    jql = "issuetype = Epic AND statusCategory != Done"
    if project:
        jql = f"project = {project} AND {jql}"
    jql += " ORDER BY updated DESC"

    epics = search_issues(jql, max_results, ["summary", "status", "assignee"])

    results = []
    for epic in epics:
        epic_key = epic.get("key", "")
        children = get_epic_children(epic_key, fields=["assignee"])
        assignees: set[str] = set()
        for child in children:
            child_assignee = child.get("fields", {}).get("assignee")
            if child_assignee and child_assignee.get("displayName"):
                assignees.add(child_assignee["displayName"])
        if len(assignees) >= min_contributors:
            results.append(
                {
                    "epic": epic,
                    "children_count": len(children),
                    "contributors": sorted(assignees),
                }
            )

    return results


def format_collaborative_epics(results: list[dict[str, Any]]) -> str:
    """Format collaborative epics for display.

    Args:
        results: List of result dicts from find_collaborative_epics.

    Returns:
        Formatted markdown string.
    """
    if not results:
        return "No collaborative epics found."

    parts = ["## Collaborative Epics"]
    for result in results:
        epic = result["epic"]
        key = epic.get("key", "N/A")
        summary = epic.get("fields", {}).get("summary", "No summary")
        children_count = result["children_count"]
        contributors = ", ".join(result["contributors"])
        parts.append(
            f"\n### {key}: {summary}\n"
            f"- **Children:** {children_count}\n"
            f"- **Contributors:** {contributors}"
        )

    return "\n".join(parts)


# ============================================================================
# TRANSITION MANAGEMENT
# ============================================================================


def get_transitions(issue_key: str) -> list[dict[str, Any]]:
    """Get available transitions for an issue.

    Args:
        issue_key: The issue key.

    Returns:
        List of transition dictionaries.
    """
    response = get("jira", api_path(f"issue/{issue_key}/transitions"))
    if isinstance(response, dict):
        return response.get("transitions", [])
    return []


def do_transition(
    issue_key: str,
    transition_name: str,
    comment: str | None = None,
    security_level: str | None = None,
) -> dict[str, Any]:
    """Transition an issue to a new status.

    Args:
        issue_key: The issue key.
        transition_name: Name of the transition to perform.
        comment: Optional comment to add.
        security_level: Optional security level for private comment.

    Returns:
        Response dictionary (empty on success).
    """
    # Get available transitions
    transitions = get_transitions(issue_key)

    # Find matching transition (case-insensitive)
    transition_id = None
    for t in transitions:
        if t.get("name", "").lower() == transition_name.lower():
            transition_id = t.get("id")
            break

    if not transition_id:
        available = [t.get("name") for t in transitions]
        raise ValueError(
            f"Transition '{transition_name}' not available. Available: {', '.join(available)}"
        )

    data: dict[str, Any] = {"transition": {"id": transition_id}}

    if comment:
        comment_data: dict[str, Any] = {"body": format_rich_text(comment)}
        if security_level:
            comment_data["visibility"] = {"type": "group", "value": security_level}
        data["update"] = {"comment": [{"add": comment_data}]}

    response = post("jira", api_path(f"issue/{issue_key}/transitions"), data)
    if isinstance(response, dict):
        return response
    return {}


# ============================================================================
# METADATA DISCOVERY
# ============================================================================


def list_fields(project_key: str | None = None, issue_type: str | None = None) -> list[dict]:
    """List available fields.

    If project and issue_type provided, returns fields specific to that context.
    Otherwise returns all global fields.

    Args:
        project_key: Optional project key for context-specific fields.
        issue_type: Optional issue type name (requires project_key).

    Returns:
        List of field dictionaries.
    """
    if project_key and issue_type:
        # Get project/issue-type specific fields via createmeta
        response = get("jira", api_path(f"issue/createmeta/{project_key}/issuetypes/{issue_type}"))
        if isinstance(response, dict):
            return response.get("values", [])
        return []
    else:
        # Get all global fields
        response = get("jira", api_path("field"))
        return response if isinstance(response, list) else []


def list_statuses() -> list[dict]:
    """List all available statuses.

    Returns:
        List of status dictionaries.
    """
    response = get("jira", api_path("status"))
    return response if isinstance(response, list) else []


def list_status_categories() -> list[dict]:
    """List status categories (To Do, In Progress, Done).

    Returns:
        List of status category dictionaries.
    """
    response = get("jira", api_path("statuscategory"))
    return response if isinstance(response, list) else []


# ============================================================================
# CHECK COMMAND - Validates configuration and connectivity
# ============================================================================


def cmd_check() -> int:
    """Validate Jira configuration and connectivity.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Checking Jira configuration...\n")

    # 1. Check credentials
    print("1. Checking credentials...")
    creds = get_credentials("jira")

    if not creds.url:
        print("   ERROR: No Jira URL configured")
        print("\n   Configure using one of these methods:")
        print("   - Environment: export JIRA_BASE_URL=https://your-domain.atlassian.net")
        print("   - Config file: ~/.config/agent-skills/jira.yaml")
        print("   - Keyring: Use a setup script to store in system keyring")
        return 1

    print(f"   URL: {creds.url}")

    if not creds.token:
        print("   ERROR: No API token configured")
        print("\n   Configure using one of these methods:")
        print("   - Environment: export JIRA_API_TOKEN=your-token-here")
        if is_cloud():
            print("   - Also set: export JIRA_EMAIL=your-email@example.com")
        print("   - Config file: ~/.config/agent-skills/jira.yaml")
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
        print(f"   API Version: {get_api_version()}")
        print("   Connection: OK\n")
    except JiraDetectionError as e:
        print(f"   ERROR: {e}")
        return 1

    # 3. Test a simple API call
    print("3. Testing API access...")
    try:
        # Use a simple search with limit 1 to test API access
        if is_cloud():
            search_endpoint = api_path("search/jql")
            response = post(
                "jira",
                search_endpoint,
                data={
                    "jql": "created >= -30d ORDER BY created DESC",
                    "maxResults": 1,
                    "fields": ["summary"],
                },
            )
        else:
            search_endpoint = api_path("search")
            response = get(
                "jira",
                search_endpoint,
                params={"jql": "created >= -30d ORDER BY created DESC", "maxResults": 1},
            )
        print(f"   Search endpoint: {search_endpoint}")
        if isinstance(response, dict) and "issues" in response:
            print("   API access: OK\n")
        else:
            print("   WARNING: Unexpected response format")
    except APIError as e:
        print(f"   ERROR: {e}")
        return 1
    except Exception as e:
        print(f"   ERROR: {e}")
        return 1

    # 4. Check for ScriptRunner support
    print("4. Checking ScriptRunner support...")
    try:
        scriptrunner_info = detect_scriptrunner_support(force_refresh=True)
        if scriptrunner_info["available"]:
            print(f"   ScriptRunner: Available ({scriptrunner_info['type']})")
            if scriptrunner_info["version"]:
                print(f"   Version: {scriptrunner_info['version']}")
            if scriptrunner_info["enhanced_search"]:
                print("   Enhanced Search: Enabled")
                print("   You can use advanced JQL functions like:")
                print('     issue in linkedIssuesOf("PROJ-123")')
                print('     issue in subtasksOf("PROJ-123")')
                print('     issue in commentedByUser("accountId")')
                print()
                print("   For complete guidance, see references/scriptrunner.md")
            else:
                print("   Enhanced Search: Disabled")
        else:
            print("   ScriptRunner: Not detected")
            print("   (Advanced JQL functions will not be available)")
    except Exception as e:
        print(f"   WARNING: Could not check ScriptRunner: {e}")

    # 5. Check Automation API access (Cloud-only)
    if is_cloud():
        print("\n5. Checking Automation API access...")
        try:
            # Check user permissions
            perms_response = get(
                "jira",
                api_path("mypermissions"),
                params={"permissions": "ADMINISTER"},
            )
            perms = perms_response.get("permissions", {})
            administer = perms.get("ADMINISTER", {})
            has_admin = administer.get("havePermission", False)
            if has_admin:
                print("   Jira admin permission: YES")
            else:
                print("   Jira admin permission: NO")
                print("   (Automation rules may require admin access)")

            # Try the automation endpoint
            cloud_id = get_cloud_id()
            print(f"   Cloud ID: {cloud_id}")
            endpoint = automation_path("rule/summary")
            auto_response = get("jira", endpoint, params={"limit": 1})
            rule_count = len(auto_response.get("data", []))
            print(f"   Automation API: OK (test returned {rule_count} rule(s))")
        except APIError as e:
            print(f"   Automation API: FAILED — {e}")
            print("   (Your token may lack automation access or admin permissions)")
        except Exception as e:
            print(f"   WARNING: Could not check Automation API: {e}")
    else:
        print("\n5. Automation API: Skipped (Cloud-only feature)")

    # 6. Validate custom field mappings
    defaults = get_jira_defaults()
    if defaults.custom_fields:
        print("\n6. Validating custom field mappings...")
        errors = validate_custom_fields(defaults.custom_fields)
        if errors:
            print("   WARNING: Some custom field mappings are invalid:")
            for err in errors:
                print(f"   {err}")
            print("   Update custom_fields in ~/.config/agent-skills/jira.yaml")
        else:
            schemas = defaults.custom_field_schemas or {}
            for name, fid in defaults.custom_fields.items():
                schema = schemas.get(name)
                if schema:
                    print(f"   {name}: {fid} (type: {schema}, OK)")
                else:
                    print(f"   {name}: {fid} (type: unknown — run: config discover {name})")
            print("   Custom fields: OK")

    print()
    print("All checks passed!")
    print("\nYou can now use commands like:")
    print('  python jira.py search "project = YOUR_PROJECT"')
    print("  python jira.py issue get DEMO-123")
    print("  python jira.py transitions list DEMO-123")

    return 0


# ============================================================================
# DASHBOARD, FILTER & RICH FILTER API
# ============================================================================


def list_dashboards(max_results: int = 50) -> list[dict[str, Any]]:
    """List dashboards visible to the current user."""
    service = "jira"
    result = get(service, api_path(f"dashboard?maxResults={max_results}"))
    return result.get("dashboards", []) if isinstance(result, dict) else []


def get_dashboard(dashboard_id: str) -> dict[str, Any]:
    """Get dashboard details."""
    service = "jira"
    result = get(service, api_path(f"dashboard/{dashboard_id}"))
    return result if isinstance(result, dict) else {}


def get_dashboard_gadgets(dashboard_id: str) -> list[dict[str, Any]]:
    """Get gadgets on a dashboard."""
    service = "jira"
    result = get(service, api_path(f"dashboard/{dashboard_id}/gadget"))
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("gadgets", [])
    return []


def get_filter(filter_id: str) -> dict[str, Any]:
    """Get saved filter details including JQL."""
    service = "jira"
    result = get(service, api_path(f"filter/{filter_id}"))
    return result if isinstance(result, dict) else {}


def list_filters_favourite() -> list[dict[str, Any]]:
    """List the current user's favourite filters."""
    service = "jira"
    result = get(service, api_path("filter/favourite"))
    return result if isinstance(result, list) else []


def list_filters_my() -> list[dict[str, Any]]:
    """List filters owned by the current user."""
    service = "jira"
    result = get(service, api_path("filter/my"))
    return result if isinstance(result, list) else []


def get_richfilter(filter_id: str) -> dict[str, Any]:
    """Get a Rich Filter configuration (Appfire plugin).

    Returns the filter config or raises APIError if the plugin isn't installed.
    """
    service = "jira"
    result = get(service, f"rest/richfilters/1.0/filter/{filter_id}")
    return result if isinstance(result, dict) else {}


def list_richfilters() -> list[dict[str, Any]]:
    """List available Rich Filters (Appfire plugin)."""
    service = "jira"
    result = get(service, "rest/richfilters/1.0/filter")
    return result if isinstance(result, list) else []


def format_dashboard(dashboard: dict[str, Any]) -> str:
    """Format a dashboard for display."""
    lines = [
        f"Dashboard: {dashboard.get('name', 'Unknown')}",
        f"  ID: {dashboard.get('id', '?')}",
        f"  View: {dashboard.get('view', 'N/A')}",
    ]
    owner = dashboard.get("owner", {})
    if owner:
        lines.append(f"  Owner: {owner.get('displayName', owner.get('name', '?'))}")
    return "\n".join(lines)


def format_gadget(gadget: dict[str, Any]) -> str:
    """Format a dashboard gadget for display."""
    lines = [
        f"Gadget: {gadget.get('title', 'Untitled')}",
        f"  ID: {gadget.get('id', '?')}",
        f"  Module Key: {gadget.get('moduleKey', 'N/A')}",
    ]
    uri = gadget.get("uri")
    if uri:
        lines.append(f"  URI: {uri}")
    color = gadget.get("color")
    if color:
        if isinstance(color, dict):
            lines.append(f"  Color: {color.get('key', 'N/A')}")
        else:
            lines.append(f"  Color: {color}")
    position = gadget.get("position", {})
    if position:
        lines.append(f"  Position: row={position.get('row')}, col={position.get('column')}")
    return "\n".join(lines)


def format_filter(filt: dict[str, Any]) -> str:
    """Format a saved filter for display."""
    lines = [
        f"Filter: {filt.get('name', 'Unknown')}",
        f"  ID: {filt.get('id', '?')}",
        f"  JQL: {filt.get('jql', 'N/A')}",
    ]
    owner = filt.get("owner", {})
    if owner:
        lines.append(f"  Owner: {owner.get('displayName', owner.get('name', '?'))}")
    if filt.get("description"):
        lines.append(f"  Description: {filt['description']}")
    if filt.get("favourite"):
        lines.append("  Favourite: yes")
    permissions = filt.get("sharePermissions", [])
    if permissions:
        shares = [p.get("type", "?") for p in permissions]
        lines.append(f"  Shared with: {', '.join(shares)}")
    return "\n".join(lines)


# ============================================================================
# COMMAND HANDLERS
# ============================================================================


def cmd_search(args: argparse.Namespace) -> int:
    """Handle search command."""
    try:
        # Load defaults
        defaults = get_jira_defaults()
        custom_fields = defaults.custom_fields or {}

        contributor = getattr(args, "contributor", None)
        jql = getattr(args, "jql", None)

        if not contributor and not jql:
            print("Error: either a JQL query or --contributor is required", file=sys.stderr)
            return 1

        # Apply max_results (detect if user explicitly provided it)
        max_results = (
            args.max_results if args.max_results is not None else (defaults.max_results or 50)
        )

        # Apply fields
        if args.fields:
            fields = args.fields.split(",")
        elif defaults.fields:
            fields = defaults.fields
        else:
            fields = None

        for field_id in custom_fields.values():
            fields = ensure_field_included(fields, field_id)

        if contributor:
            project = getattr(args, "project", None)
            issues = search_by_contributor(contributor, project, max_results, fields)
        else:
            # Apply JQL scope
            jql = merge_jql_with_scope(jql, defaults.jql_scope)
            issues = search_issues(jql, max_results, fields)

        if args.json:
            print(format_json(issues))
        else:
            print(format_issues_list(issues, custom_fields=custom_fields))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _resolve_set_field_pairs(
    pairs: list[str],
    custom_fields: dict[str, str],
    schemas: dict[str, str],
) -> dict[str, Any] | str:
    """Resolve --set-field NAME=VALUE pairs to field IDs with coerced values.

    Returns the extra_fields dict on success, or an error message string on failure.
    """
    extra_fields: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            return f"--set-field requires NAME=VALUE format, got: {pair}"
        name, value = pair.split("=", 1)
        key = _normalize_field_name(name)
        field_id = resolve_or_discover_field(name, custom_fields)
        if not field_id:
            return f"could not resolve field '{name}'"
        extra_fields[field_id] = coerce_field_value(
            field_id,
            value,
            schema_type=schemas.get(key),
        )
        reloaded = (load_config("jira") or {}).get("defaults", {})
        custom_fields = reloaded.get("custom_fields", {})
        schemas = reloaded.get("custom_field_schemas", {})
    return extra_fields


def _parse_link_args(link_args: list[str] | None) -> list[tuple[str, str]] | str:
    """Parse --link TYPE:ISSUE pairs from CLI args.

    Returns list of (link_type, target_key) tuples, or an error message string.
    """
    if not link_args:
        return []
    links = []
    for arg in link_args:
        if ":" not in arg:
            return f"--link requires TYPE:ISSUE format, got: {arg}"
        link_type, target = arg.split(":", 1)
        link_type = link_type.strip()
        target = target.strip()
        if not link_type or not target:
            return f"--link requires TYPE:ISSUE format, got: {arg}"
        links.append((link_type, target))
    return links


def _load_from_file(args: argparse.Namespace) -> tuple[dict[str, Any], str | None] | int:
    """Load and validate --from-file if present on args.

    Returns (file_fields, file_description) on success, or an int exit code on error.
    """
    from_file = getattr(args, "from_file", None)
    if not from_file:
        return {}, None

    if args.description:
        print("Error: --from-file and --description cannot be used together", file=sys.stderr)
        return 1

    try:
        return parse_issue_file(from_file)
    except FileNotFoundError:
        print(f"Error: file not found: {from_file}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: invalid issue file: {exc}", file=sys.stderr)
        return 1


def cmd_issue(args: argparse.Namespace) -> int:
    """Handle issue command."""
    try:
        if args.issue_command == "get":
            # Load defaults and apply fields
            defaults = get_jira_defaults()
            custom_fields = defaults.custom_fields or {}
            if args.fields:
                fields = args.fields.split(",")
            elif defaults.fields:
                fields = defaults.fields
            else:
                fields = None

            for field_id in custom_fields.values():
                fields = ensure_field_included(fields, field_id)

            issue = get_issue(args.issue_key, fields=fields)

            if getattr(args, "contributors", False):
                comments = get_comments(args.issue_key)
                contributor_names = extract_contributors(issue, comments)
                if args.json:
                    issue["_contributors"] = sorted(contributor_names)
                    print(format_json(issue))
                else:
                    output = format_issue(issue, custom_fields=custom_fields)
                    output += f"\n- **Contributors:** {', '.join(sorted(contributor_names))}"
                    print(output)
            elif args.json:
                print(format_json(issue))
            else:
                print(format_issue(issue, custom_fields=custom_fields))

        elif args.issue_command == "comments":
            max_results = getattr(args, "max_results", 50) or 50
            comments = get_comments(args.issue_key, max_results=max_results)
            if args.json:
                print(format_json(comments))
            else:
                print(format_comments(comments, args.issue_key))

        elif args.issue_command == "create":
            # Load --from-file if provided
            result = _load_from_file(args)
            if isinstance(result, int):
                return result
            file_fields, file_description = result

            # Load project-specific defaults
            defaults = get_jira_defaults()
            project = args.project or file_fields.get("project")
            project_defaults = get_project_defaults(project) if project else ProjectDefaults()

            # Merge: CLI > frontmatter > project defaults
            summary = args.summary or file_fields.get("summary")
            issue_type = args.issue_type or file_fields.get("type") or project_defaults.issue_type
            priority = args.priority or file_fields.get("priority") or project_defaults.priority
            description = args.description or file_description
            assignee = args.assignee or file_fields.get("assignee")

            if args.labels:
                labels = args.labels.split(",")
            elif file_fields.get("labels"):
                labels = file_fields["labels"]
            else:
                labels = None

            if not project:
                print(
                    "Error: --project is required (provide via CLI or frontmatter)",
                    file=sys.stderr,
                )
                return 1
            if not summary:
                print(
                    "Error: --summary is required (provide via CLI or frontmatter)",
                    file=sys.stderr,
                )
                return 1
            if not issue_type:
                print(
                    "Error: --type is required (no project default configured,"
                    " provide via CLI or frontmatter)",
                    file=sys.stderr,
                )
                return 1

            # Resolve custom fields: frontmatter fields first, then --set-field overrides
            custom_fields = defaults.custom_fields or {}
            schemas = defaults.custom_field_schemas or {}
            extra_fields: dict[str, Any] = {}

            fm_fields = file_fields.get("fields") or {}
            if fm_fields:
                fm_pairs = [f"{k}={v}" for k, v in fm_fields.items()]
                fm_result = _resolve_set_field_pairs(fm_pairs, custom_fields, schemas)
                if isinstance(fm_result, str):
                    print(f"Error: {fm_result}", file=sys.stderr)
                    return 1
                extra_fields.update(fm_result)
                reloaded = (load_config("jira") or {}).get("defaults", {})
                custom_fields = reloaded.get("custom_fields", custom_fields)
                schemas = reloaded.get("custom_field_schemas", schemas)

            cli_pairs = getattr(args, "set_field", None) or []
            if cli_pairs:
                cli_result = _resolve_set_field_pairs(cli_pairs, custom_fields, schemas)
                if isinstance(cli_result, str):
                    print(f"Error: {cli_result}", file=sys.stderr)
                    return 1
                extra_fields.update(cli_result)

            issue = create_issue(
                project=project,
                issue_type=issue_type,
                summary=summary,
                description=description,
                priority=priority,
                labels=labels,
                assignee=assignee,
                extra_fields=extra_fields or None,
            )
            new_key = issue.get("key", "N/A")
            if args.json:
                print(format_json(issue))
            else:
                print(f"Created issue: {new_key}")

            # Process links (frontmatter + CLI, additive)
            all_links: list[tuple[str, str]] = list(file_fields.get("links") or [])
            cli_links = _parse_link_args(getattr(args, "link", None))
            if isinstance(cli_links, str):
                print(f"Error: {cli_links}", file=sys.stderr)
                return 1
            all_links.extend(cli_links)
            for link_type, target_key in all_links:
                try:
                    create_link(new_key, link_type, target_key)
                    print(f"  Linked {new_key} --[{link_type}]--> {target_key}")
                except (ValueError, APIError) as link_err:
                    print(f"  Warning: failed to link to {target_key}: {link_err}", file=sys.stderr)

        elif args.issue_command == "update":
            # Load --from-file if provided
            result = _load_from_file(args)
            if isinstance(result, int):
                return result
            file_fields, file_description = result

            defaults = get_jira_defaults()

            # Merge: CLI > frontmatter (project/type silently ignored for update)
            summary = args.summary or file_fields.get("summary")
            description = args.description or file_description
            priority = args.priority or file_fields.get("priority")
            assignee = args.assignee or file_fields.get("assignee")

            if args.labels:
                labels = args.labels.split(",")
            elif file_fields.get("labels"):
                labels = file_fields["labels"]
            else:
                labels = None

            # Resolve custom fields: frontmatter fields first, then --set-field overrides
            custom_fields = defaults.custom_fields or {}
            schemas = defaults.custom_field_schemas or {}
            extra_fields: dict[str, Any] = {}

            fm_fields = file_fields.get("fields") or {}
            if fm_fields:
                fm_pairs = [f"{k}={v}" for k, v in fm_fields.items()]
                fm_result = _resolve_set_field_pairs(fm_pairs, custom_fields, schemas)
                if isinstance(fm_result, str):
                    print(f"Error: {fm_result}", file=sys.stderr)
                    return 1
                extra_fields.update(fm_result)
                reloaded = (load_config("jira") or {}).get("defaults", {})
                custom_fields = reloaded.get("custom_fields", custom_fields)
                schemas = reloaded.get("custom_field_schemas", schemas)

            cli_pairs = getattr(args, "set_field", None) or []
            if cli_pairs:
                cli_result = _resolve_set_field_pairs(cli_pairs, custom_fields, schemas)
                if isinstance(cli_result, str):
                    print(f"Error: {cli_result}", file=sys.stderr)
                    return 1
                extra_fields.update(cli_result)

            update_issue(
                issue_key=args.issue_key,
                summary=summary,
                description=description,
                priority=priority,
                labels=labels,
                assignee=assignee,
                extra_fields=extra_fields or None,
            )
            print(f"Updated issue: {args.issue_key}")

            # Process links (frontmatter + CLI, additive)
            all_links: list[tuple[str, str]] = list(file_fields.get("links") or [])
            cli_links = _parse_link_args(getattr(args, "link", None))
            if isinstance(cli_links, str):
                print(f"Error: {cli_links}", file=sys.stderr)
                return 1
            all_links.extend(cli_links)
            for link_type, target_key in all_links:
                try:
                    create_link(args.issue_key, link_type, target_key)
                    print(f"  Linked {args.issue_key} --[{link_type}]--> {target_key}")
                except (ValueError, APIError) as link_err:
                    print(
                        f"  Warning: failed to link to {target_key}: {link_err}",
                        file=sys.stderr,
                    )

        elif args.issue_command == "comment":
            defaults = get_jira_defaults()
            security_level = args.security_level or defaults.security_level
            add_comment(args.issue_key, args.body, security_level=security_level)
            if security_level:
                print(
                    f"Added private comment to {args.issue_key} (security level: {security_level})"
                )
            else:
                print(f"Added comment to {args.issue_key}")

        return 0

    except APIError as e:
        print(f"Error: {e}", file=sys.stderr)
        if e.response:
            print(f"Response: {e.response}", file=sys.stderr)
        if e.status_code == 400 and getattr(args, "issue_command", None) == "create":
            project_key = locals().get("project") or getattr(args, "project", None)
            if project_key:
                valid_types = get_project_issue_types(project_key)
                if valid_types:
                    print(
                        f"Valid issue types for {project_key}: {', '.join(valid_types)}",
                        file=sys.stderr,
                    )
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_transitions(args: argparse.Namespace) -> int:
    """Handle transitions command."""
    try:
        if args.transition_command == "list":
            transitions = get_transitions(args.issue_key)

            if args.json:
                print(format_json(transitions))
            else:
                rows = [
                    {"id": t.get("id"), "name": t.get("name"), "to": t.get("to", {}).get("name")}
                    for t in transitions
                ]
                print(
                    format_table(
                        rows,
                        ["id", "name", "to"],
                        headers={"id": "ID", "name": "Transition", "to": "To Status"},
                    )
                )

        elif args.transition_command == "do":
            defaults = get_jira_defaults()
            security_level = args.security_level or (
                defaults.security_level if args.comment else None
            )
            do_transition(args.issue_key, args.transition, args.comment, security_level)
            msg = f"Transitioned {args.issue_key} to '{args.transition}'"
            if args.comment and security_level:
                msg += f" (with private comment, security level: {security_level})"
            elif args.comment:
                msg += " (with comment)"
            print(msg)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_config(args: argparse.Namespace) -> int:
    """Handle config command."""
    try:
        if args.config_command == "show":
            config = load_config("jira")
            if not config:
                print("No configuration file found at ~/.config/agent-skills/jira.yaml")
                return 0

            print("Configuration: ~/.config/agent-skills/jira.yaml\n")

            # Show auth (masked)
            print("Authentication:")
            print(f"  URL: {config.get('url', 'Not configured')}")
            print(f"  Email: {config.get('email', 'Not configured')}")
            print(f"  Token: {'*' * 8 if config.get('token') else 'Not configured'}")
            print()

            # Show defaults
            defaults = JiraDefaults.from_config(config)
            print("Defaults:")
            print(f"  JQL Scope: {defaults.jql_scope or 'Not configured'}")
            print(f"  Security Level: {defaults.security_level or 'Not configured'}")
            print(f"  Max Results: {defaults.max_results or 'Not configured (default: 50)'}")
            print(
                f"  Fields: {', '.join(defaults.fields) if defaults.fields else 'Not configured'}"
            )
            if defaults.custom_fields:
                schemas = defaults.custom_field_schemas or {}
                print("  Custom Fields:")
                for name, fid in defaults.custom_fields.items():
                    schema = schemas.get(name)
                    if schema:
                        print(f"    {name}: {fid} (type: {schema})")
                    else:
                        print(f"    {name}: {fid} (type: unknown — run: config discover {name})")
            else:
                print("  Custom Fields: Not configured")
            print()

            # Show project defaults
            if args.project:
                project_defaults = ProjectDefaults.from_config(config, args.project)
                print(f"Project Defaults for {args.project}:")
                print(f"  Issue Type: {project_defaults.issue_type or 'Not configured'}")
                print(f"  Priority: {project_defaults.priority or 'Not configured'}")
            else:
                projects = config.get("projects", {})
                if projects:
                    print("Project-Specific Defaults:")
                    for project, settings in projects.items():
                        print(f"  {project}:")
                        print(f"    Issue Type: {settings.get('issue_type', 'Not configured')}")
                        print(f"    Priority: {settings.get('priority', 'Not configured')}")
                else:
                    print("No project-specific defaults configured")

            return 0

        elif args.config_command == "discover":
            defaults = get_jira_defaults()
            custom_fields = defaults.custom_fields or {}
            field_id = resolve_or_discover_field(args.field_name, custom_fields)
            if field_id:
                key = _normalize_field_name(args.field_name)
                reloaded = JiraDefaults.from_config(load_config("jira") or {})
                schema = (reloaded.custom_field_schemas or {}).get(key, "unknown")
                print(f"\n{key} -> {field_id} (type: {schema})")
            else:
                print(f"\nCould not resolve field '{args.field_name}'.")
                print("Use 'fields' command to list available fields.")
                return 1
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_fields(args: argparse.Namespace) -> int:
    """Handle fields command."""
    try:
        fields = list_fields(args.project, args.issue_type)
        if args.json:
            print(format_json(fields))
        else:
            rows = [
                {
                    "id": f.get("id", f.get("fieldId", "N/A")),
                    "name": f.get("name", "N/A"),
                    "custom": "Yes" if f.get("custom") else "No",
                }
                for f in fields
            ]
            print(
                format_table(
                    rows,
                    ["id", "name", "custom"],
                    headers={"id": "ID", "name": "Name", "custom": "Custom"},
                )
            )
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_statuses(args: argparse.Namespace) -> int:
    """Handle statuses command."""
    try:
        if args.categories:
            categories = list_status_categories()
            if args.json:
                print(format_json(categories))
            else:
                rows = [
                    {
                        "key": c.get("key", "N/A"),
                        "name": c.get("name", "N/A"),
                        "color": c.get("colorName", "N/A"),
                    }
                    for c in categories
                ]
                print(
                    format_table(
                        rows,
                        ["key", "name", "color"],
                        headers={"key": "Key", "name": "Name", "color": "Color"},
                    )
                )
        else:
            statuses = list_statuses()
            if args.json:
                print(format_json(statuses))
            else:
                rows = [
                    {
                        "name": s.get("name", "N/A"),
                        "category": s.get("statusCategory", {}).get("name", "Unknown"),
                    }
                    for s in statuses
                ]
                print(
                    format_table(
                        rows,
                        ["name", "category"],
                        headers={"name": "Status", "category": "Category"},
                    )
                )
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_user(args: argparse.Namespace) -> int:
    """Handle user command."""
    try:
        if args.user_command == "search":
            users = resolve_user(args.query)
            if args.json:
                print(format_json(users))
            else:
                if not users:
                    print("No users found")
                else:
                    rows = [
                        {
                            "accountId": u.get("accountId", u.get("username", "N/A")),
                            "email": u.get("emailAddress", "N/A"),
                            "name": u.get("displayName", "N/A"),
                            "active": "Yes" if u.get("active", True) else "No",
                        }
                        for u in users
                    ]
                    print(
                        format_table(
                            rows,
                            ["accountId", "email", "name", "active"],
                            headers={
                                "accountId": "Account ID",
                                "email": "Email",
                                "name": "Display Name",
                                "active": "Active",
                            },
                        )
                    )
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_collaboration(args: argparse.Namespace) -> int:
    """Handle collaboration command."""
    try:
        if args.collaboration_command == "epics":
            project = getattr(args, "project", None)
            min_contributors = getattr(args, "min_contributors", 2)
            max_results = getattr(args, "max_results", 50) or 50

            results = find_collaborative_epics(
                project=project,
                min_contributors=min_contributors,
                max_results=max_results,
            )

            if args.json:
                json_results = []
                for r in results:
                    json_results.append(
                        {
                            "epic": r["epic"],
                            "children_count": r["children_count"],
                            "contributors": r["contributors"],
                        }
                    )
                print(format_json(json_results))
            else:
                print(format_collaborative_epics(results))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_automations(args: argparse.Namespace) -> int:
    """Handle automations command (Cloud-only)."""
    try:
        if args.automations_command == "list":
            rules = list_automation_rules(
                project_key=getattr(args, "project", None),
                state=getattr(args, "state", None),
                limit=getattr(args, "limit", 100) or 100,
            )

            if not rules:
                print("No automation rules found.")
                return 0

            if args.json:
                print(format_json(rules))
            else:
                parts = [format_automation_summary(r) for r in rules]
                print(f"Found {len(rules)} automation rule(s).\n")
                print("\n\n".join(parts))

        elif args.automations_command == "get":
            rule_config = get_automation_rule(args.uuid)

            if args.json:
                print(format_json(rule_config))
            else:
                print(format_automation_detail(rule_config))

        return 0

    except APIError as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response:
            print(f"Response: {e.response}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Handle dashboard command."""
    try:
        if args.dashboard_command == "list":
            dashboards = list_dashboards(max_results=getattr(args, "max_results", 50) or 50)
            if not dashboards:
                print("No dashboards found.")
                return 0
            if getattr(args, "json", False):
                print(format_json(dashboards))
            else:
                print(f"Found {len(dashboards)} dashboard(s).\n")
                for d in dashboards:
                    print(format_dashboard(d))
                    print()

        elif args.dashboard_command == "get":
            dashboard = get_dashboard(args.dashboard_id)
            if getattr(args, "json", False):
                print(format_json(dashboard))
            else:
                print(format_dashboard(dashboard))

        elif args.dashboard_command == "gadgets":
            gadgets = get_dashboard_gadgets(args.dashboard_id)
            if not gadgets:
                print("No gadgets found on this dashboard.")
                return 0
            if getattr(args, "json", False):
                print(format_json(gadgets))
            else:
                print(f"Found {len(gadgets)} gadget(s).\n")
                for g in gadgets:
                    print(format_gadget(g))
                    print()

        return 0

    except APIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_filter(args: argparse.Namespace) -> int:
    """Handle filter command."""
    try:
        if args.filter_command == "get":
            filt = get_filter(args.filter_id)
            if getattr(args, "json", False):
                print(format_json(filt))
            else:
                print(format_filter(filt))

        elif args.filter_command == "list":
            filters = list_filters_favourite()
            if not filters:
                print("No favourite filters found.")
                return 0
            if getattr(args, "json", False):
                print(format_json(filters))
            else:
                print(f"Found {len(filters)} favourite filter(s).\n")
                for f in filters:
                    print(format_filter(f))
                    print()

        return 0

    except APIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_richfilter(args: argparse.Namespace) -> int:
    """Handle richfilter command (Appfire plugin)."""
    try:
        if args.richfilter_command == "get":
            rf = get_richfilter(args.filter_id)
            if getattr(args, "json", False):
                print(format_json(rf))
            else:
                print(format_json(rf))

        elif args.richfilter_command == "list":
            filters = list_richfilters()
            if not filters:
                print("No rich filters found.")
                return 0
            if getattr(args, "json", False):
                print(format_json(filters))
            else:
                for f in filters:
                    name = f.get("name", f.get("title", "Unknown"))
                    fid = f.get("id", "?")
                    print(f"  [{fid}] {name}")

        return 0

    except APIError as e:
        msg = str(e)
        if "404" in msg or "not found" in msg.lower():
            print(
                "Error: Rich Filters plugin not found. Is the Appfire Rich Filters app installed?",
                file=sys.stderr,
            )
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# ============================================================================
# MAIN CLI
# ============================================================================


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Jira integration for AI agents",
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
        help="Search for issues using JQL",
    )
    search_parser.add_argument("jql", nargs="?", default=None, help="JQL query string")
    search_parser.add_argument(
        "--contributor",
        help="Search for issues where this user is a contributor (reporter, assignee, or commenter)",
    )
    search_parser.add_argument(
        "--project",
        help="Project key to scope contributor search",
    )
    search_parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum number of results (default: 50, or use configured default)",
    )
    search_parser.add_argument(
        "--fields",
        help="Comma-separated list of fields to include",
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # ========================================================================
    # ISSUE COMMAND
    # ========================================================================
    issue_parser = subparsers.add_parser(
        "issue",
        help="Manage issues",
    )
    issue_subparsers = issue_parser.add_subparsers(dest="issue_command", required=True)

    # Get subcommand
    get_parser = issue_subparsers.add_parser("get", help="Get issue details")
    get_parser.add_argument("issue_key", help="Issue key (e.g., DEMO-123)")
    get_parser.add_argument(
        "--fields",
        help="Comma-separated list of fields to include",
    )
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")
    get_parser.add_argument(
        "--contributors",
        action="store_true",
        help="Show contributors (reporter, assignee, commenters) — requires extra API call",
    )

    # Comments subcommand
    comments_parser = issue_subparsers.add_parser("comments", help="List comments on an issue")
    comments_parser.add_argument("issue_key", help="Issue key (e.g., DEMO-123)")
    comments_parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of comments (default: 50)",
    )
    comments_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Create subcommand
    create_parser = issue_subparsers.add_parser("create", help="Create new issue")
    create_parser.add_argument("--project", help="Project key")
    create_parser.add_argument(
        "--type", dest="issue_type", help="Issue type (required unless project default configured)"
    )
    create_parser.add_argument("--summary", help="Issue summary")
    create_parser.add_argument("--description", help="Issue description")
    create_parser.add_argument("--priority", help="Priority name")
    create_parser.add_argument("--labels", help="Comma-separated labels")
    create_parser.add_argument("--assignee", help="Assignee account ID")
    create_parser.add_argument(
        "--set-field",
        action="append",
        metavar="NAME=VALUE",
        help="Set a custom field (e.g. --set-field story_points=5)",
    )
    create_parser.add_argument(
        "--from-file",
        dest="from_file",
        metavar="PATH",
        help="Read issue fields and description from a markdown file with YAML frontmatter",
    )
    create_parser.add_argument(
        "--link",
        action="append",
        metavar="TYPE:ISSUE",
        help="Link to another issue (e.g. --link 'Blocks:DEMO-456')",
    )
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Update subcommand
    update_parser = issue_subparsers.add_parser("update", help="Update existing issue")
    update_parser.add_argument("issue_key", help="Issue key")
    update_parser.add_argument("--summary", help="New summary")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument("--priority", help="New priority")
    update_parser.add_argument("--labels", help="New labels (comma-separated)")
    update_parser.add_argument("--assignee", help="New assignee account ID")
    update_parser.add_argument(
        "--set-field",
        action="append",
        metavar="NAME=VALUE",
        help="Set a custom field (e.g. --set-field story_points=5)",
    )
    update_parser.add_argument(
        "--from-file",
        dest="from_file",
        metavar="PATH",
        help="Read issue fields and description from a markdown file with YAML frontmatter",
    )
    update_parser.add_argument(
        "--link",
        action="append",
        metavar="TYPE:ISSUE",
        help="Link to another issue (e.g. --link 'Blocks:DEMO-456')",
    )

    # Comment subcommand
    comment_parser = issue_subparsers.add_parser("comment", help="Add comment to issue")
    comment_parser.add_argument("issue_key", help="Issue key")
    comment_parser.add_argument("body", help="Comment text")
    comment_parser.add_argument(
        "--security-level",
        help="Security level for private comment (e.g., 'Internal', 'Employees')",
    )

    # ========================================================================
    # TRANSITIONS COMMAND
    # ========================================================================
    transitions_parser = subparsers.add_parser(
        "transitions",
        help="Manage issue transitions",
    )
    transitions_subparsers = transitions_parser.add_subparsers(
        dest="transition_command", required=True
    )

    # List subcommand
    list_parser = transitions_subparsers.add_parser("list", help="List available transitions")
    list_parser.add_argument("issue_key", help="Issue key")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Do subcommand
    do_parser = transitions_subparsers.add_parser("do", help="Perform a transition")
    do_parser.add_argument("issue_key", help="Issue key")
    do_parser.add_argument("transition", help="Transition name")
    do_parser.add_argument("--comment", help="Comment to add with transition")
    do_parser.add_argument(
        "--security-level",
        help="Security level for private comment (e.g., 'Internal', 'Employees')",
    )

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
        "--project",
        help="Show project-specific defaults for this project",
    )

    # Discover subcommand
    discover_parser = config_subparsers.add_parser(
        "discover",
        help="Discover and save a custom field mapping",
    )
    discover_parser.add_argument(
        "field_name",
        help="Friendly name of the field to discover (e.g. story_points, security_level)",
    )

    # ========================================================================
    # FIELDS COMMAND
    # ========================================================================
    fields_parser = subparsers.add_parser(
        "fields",
        help="List available fields",
    )
    fields_parser.add_argument(
        "--project",
        help="Project key for context-specific fields",
    )
    fields_parser.add_argument(
        "--issue-type",
        dest="issue_type",
        help="Issue type for context-specific fields (requires --project)",
    )
    fields_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # ========================================================================
    # STATUSES COMMAND
    # ========================================================================
    statuses_parser = subparsers.add_parser(
        "statuses",
        help="List available statuses",
    )
    statuses_parser.add_argument(
        "--categories",
        action="store_true",
        help="Show status categories instead of individual statuses",
    )
    statuses_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # ========================================================================
    # USER COMMAND
    # ========================================================================
    user_parser = subparsers.add_parser(
        "user",
        help="Search for Jira users",
    )
    user_subparsers = user_parser.add_subparsers(dest="user_command", required=True)

    # Search subcommand
    user_search_parser = user_subparsers.add_parser(
        "search", help="Search for users by email, name, or username"
    )
    user_search_parser.add_argument("query", help="Email, display name, or username to search for")
    user_search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # ========================================================================
    # COLLABORATION COMMAND
    # ========================================================================
    collaboration_parser = subparsers.add_parser(
        "collaboration",
        help="Discover collaboration patterns",
    )
    collaboration_subparsers = collaboration_parser.add_subparsers(
        dest="collaboration_command", required=True
    )

    # Epics subcommand
    epics_parser = collaboration_subparsers.add_parser(
        "epics", help="Find epics with multiple contributors"
    )
    epics_parser.add_argument("--project", help="Project key to scope the search")
    epics_parser.add_argument(
        "--min-contributors",
        type=int,
        default=2,
        help="Minimum number of unique assignees (default: 2)",
    )
    epics_parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of epics to check (default: 50)",
    )
    epics_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # ========================================================================
    # AUTOMATIONS COMMAND (Cloud-only)
    # ========================================================================
    automations_parser = subparsers.add_parser(
        "automations",
        help="List and inspect automation rules (Cloud-only)",
    )
    automations_subparsers = automations_parser.add_subparsers(
        dest="automations_command", required=True
    )

    # automations list
    auto_list_parser = automations_subparsers.add_parser(
        "list", help="List automation rule summaries"
    )
    auto_list_parser.add_argument("--project", help="Filter to rules scoped to this project key")
    auto_list_parser.add_argument(
        "--state",
        choices=["ENABLED", "DISABLED"],
        help="Filter by rule state",
    )
    auto_list_parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum rules to return (default: 100)",
    )
    auto_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # automations get
    auto_get_parser = automations_subparsers.add_parser(
        "get", help="Get full details of an automation rule"
    )
    auto_get_parser.add_argument("uuid", help="Automation rule UUID")
    auto_get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # dashboard commands
    dashboard_parser = subparsers.add_parser("dashboard", help="Inspect dashboards and gadgets")
    dashboard_subparsers = dashboard_parser.add_subparsers(dest="dashboard_command", required=True)
    dash_list_parser = dashboard_subparsers.add_parser("list", help="List dashboards")
    dash_list_parser.add_argument(
        "--max-results", type=int, default=50, help="Max dashboards (default: 50)"
    )
    dash_list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    dash_get_parser = dashboard_subparsers.add_parser("get", help="Get dashboard details")
    dash_get_parser.add_argument("dashboard_id", help="Dashboard ID")
    dash_get_parser.add_argument("--json", action="store_true", help="Output as JSON")
    dash_gadgets_parser = dashboard_subparsers.add_parser(
        "gadgets", help="List gadgets on a dashboard"
    )
    dash_gadgets_parser.add_argument("dashboard_id", help="Dashboard ID")
    dash_gadgets_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # filter commands
    filter_parser = subparsers.add_parser("filter", help="Inspect saved filters")
    filter_subparsers = filter_parser.add_subparsers(dest="filter_command", required=True)
    filter_get_parser = filter_subparsers.add_parser("get", help="Get filter details")
    filter_get_parser.add_argument("filter_id", help="Filter ID")
    filter_get_parser.add_argument("--json", action="store_true", help="Output as JSON")
    filter_list_parser = filter_subparsers.add_parser("list", help="List favourite filters")
    filter_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # richfilter commands (Appfire plugin)
    rf_parser = subparsers.add_parser("richfilter", help="Inspect Rich Filters (Appfire plugin)")
    rf_subparsers = rf_parser.add_subparsers(dest="richfilter_command", required=True)
    rf_get_parser = rf_subparsers.add_parser("get", help="Get Rich Filter config")
    rf_get_parser.add_argument("filter_id", help="Rich Filter ID")
    rf_get_parser.add_argument("--json", action="store_true", help="Output as JSON")
    rf_list_parser = rf_subparsers.add_parser("list", help="List Rich Filters")
    rf_list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Parse and dispatch
    args = parser.parse_args()

    if args.command == "check":
        return cmd_check()
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "issue":
        return cmd_issue(args)
    elif args.command == "transitions":
        return cmd_transitions(args)
    elif args.command == "config":
        return cmd_config(args)
    elif args.command == "fields":
        return cmd_fields(args)
    elif args.command == "statuses":
        return cmd_statuses(args)
    elif args.command == "user":
        return cmd_user(args)
    elif args.command == "collaboration":
        return cmd_collaboration(args)
    elif args.command == "automations":
        return cmd_automations(args)
    elif args.command == "dashboard":
        return cmd_dashboard(args)
    elif args.command == "filter":
        return cmd_filter(args)
    elif args.command == "richfilter":
        return cmd_richfilter(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
