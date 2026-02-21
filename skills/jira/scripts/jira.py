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

    @staticmethod
    def from_config(config: dict[str, Any]) -> JiraDefaults:
        """Load defaults from config dict.

        Args:
            config: Configuration dictionary.

        Returns:
            JiraDefaults object with available values.
        """
        defaults_dict = config.get("defaults", {})
        return JiraDefaults(
            jql_scope=defaults_dict.get("jql_scope"),
            security_level=defaults_dict.get("security_level"),
            max_results=defaults_dict.get("max_results"),
            fields=defaults_dict.get("fields"),
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


def format_rich_text(text: str) -> dict[str, Any] | str:
    """Format text for the appropriate Jira API version.

    Cloud API (v3) requires Atlassian Document Format (ADF).
    Data Center/Server API (v2) uses plain text.

    Args:
        text: Plain text content.

    Returns:
        ADF document dict for Cloud, plain string for DC/Server.
    """
    version = get_api_version()

    if version == "3":
        # Return Atlassian Document Format (ADF)
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }
    else:
        # Return plain text for API v2
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
            "The query may fail. Install ScriptRunner from Atlassian Marketplace to use these functions."
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


def format_issue(issue: dict[str, Any]) -> str:
    """Format a Jira issue for display.

    Args:
        issue: Jira issue dictionary.

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

    return (
        f"### {key}: {summary}\n"
        f"- **Status:** {status}\n"
        f"- **Assignee:** {assignee_name}\n"
        f"- **Priority:** {priority_name}"
    )


def format_issues_list(issues: list[dict[str, Any]]) -> str:
    """Format a list of Jira issues for display.

    Args:
        issues: List of Jira issue dictionaries.

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
        parts.append(
            f"### {key}: {summary}\n- **Status:** {status}\n- **Assignee:** {assignee_name}"
        )

    return "\n\n".join(parts)


# ============================================================================
# SEARCH FUNCTIONALITY
# ============================================================================

DEFAULT_FIELDS = [
    "summary",
    "status",
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
    """Search for issues using JQL.

    Supports standard JQL and ScriptRunner Enhanced Search functions.
    If ScriptRunner functions are detected in the query, the function
    will validate that ScriptRunner is available on the Jira instance
    and warn if it's not.

    Args:
        jql: JQL query string (supports ScriptRunner functions).
        max_results: Maximum number of results to return.
        fields: List of fields to include in response.

    Returns:
        List of issue dictionaries.

    Raises:
        APIError: If the search fails.

    Example:
        >>> # Standard JQL
        >>> search_issues("project = DEMO AND status = Open")

        >>> # ScriptRunner Enhanced Search
        >>> search_issues('issue in linkedIssuesOf("DEMO-123")')
    """
    fields = fields or DEFAULT_FIELDS

    # Validate JQL for ScriptRunner functions
    validation = validate_jql_for_scriptrunner(jql)
    if validation["warning"]:
        print(f"Warning: {validation['warning']}", file=sys.stderr)

    response = get(
        "jira",
        api_path("search"),
        params={
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields),
        },
    )

    if isinstance(response, dict):
        return response.get("issues", [])
    return []


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


def create_issue(
    project: str,
    issue_type: str,
    summary: str,
    description: str | None = None,
    priority: str | None = None,
    labels: list[str] | None = None,
    assignee: str | None = None,
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
) -> dict[str, Any]:
    """Update an existing issue.

    Args:
        issue_key: The issue key.
        summary: New summary.
        description: New description.
        priority: New priority name.
        labels: New labels.
        assignee: New assignee account ID.

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

    if not fields:
        return {}

    response = put("jira", api_path(f"issue/{issue_key}"), {"fields": fields})
    if isinstance(response, dict):
        return response
    return {}


def add_comment(issue_key: str, body: str, security_level: str | None = None) -> dict[str, Any]:
    """Add a comment to an issue.

    Args:
        issue_key: The issue key.
        body: Comment text.
        security_level: Optional security level name (e.g., "Red Hat Internal", "Employees").
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
        response = get(
            "jira",
            api_path("search"),
            params={"jql": "order by created DESC", "maxResults": 1},
        )
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

    print()
    print("All checks passed!")
    print("\nYou can now use commands like:")
    print('  python jira.py search "project = YOUR_PROJECT"')
    print("  python jira.py issue get DEMO-123")
    print("  python jira.py transitions list DEMO-123")

    return 0


# ============================================================================
# COMMAND HANDLERS
# ============================================================================


def cmd_search(args: argparse.Namespace) -> int:
    """Handle search command."""
    try:
        # Load defaults
        defaults = get_jira_defaults()

        # Apply JQL scope
        jql = merge_jql_with_scope(args.jql, defaults.jql_scope)

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

        issues = search_issues(jql, max_results, fields)

        if args.json:
            print(format_json(issues))
        else:
            print(format_issues_list(issues))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_issue(args: argparse.Namespace) -> int:
    """Handle issue command."""
    try:
        if args.issue_command == "get":
            # Load defaults and apply fields
            defaults = get_jira_defaults()
            if args.fields:
                fields = args.fields.split(",")
            elif defaults.fields:
                fields = defaults.fields
            else:
                fields = None
            issue = get_issue(args.issue_key, fields=fields)
            if args.json:
                print(format_json(issue))
            else:
                print(format_issue(issue))

        elif args.issue_command == "create":
            # Load project-specific defaults
            project_defaults = get_project_defaults(args.project)

            # Apply defaults with CLI precedence
            issue_type = args.issue_type or project_defaults.issue_type
            priority = args.priority or project_defaults.priority

            if not issue_type:
                print("Error: --type is required (no project default configured)", file=sys.stderr)
                return 1

            labels = args.labels.split(",") if args.labels else None
            issue = create_issue(
                project=args.project,
                issue_type=issue_type,
                summary=args.summary,
                description=args.description,
                priority=priority,
                labels=labels,
                assignee=args.assignee,
            )
            if args.json:
                print(format_json(issue))
            else:
                print(f"Created issue: {issue.get('key', 'N/A')}")

        elif args.issue_command == "update":
            labels = args.labels.split(",") if args.labels else None
            update_issue(
                issue_key=args.issue_key,
                summary=args.summary,
                description=args.description,
                priority=args.priority,
                labels=labels,
                assignee=args.assignee,
            )
            print(f"Updated issue: {args.issue_key}")

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
    search_parser.add_argument("jql", help="JQL query string")
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

    # Create subcommand
    create_parser = issue_subparsers.add_parser("create", help="Create new issue")
    create_parser.add_argument("--project", required=True, help="Project key")
    create_parser.add_argument(
        "--type", dest="issue_type", help="Issue type (required unless project default configured)"
    )
    create_parser.add_argument("--summary", required=True, help="Issue summary")
    create_parser.add_argument("--description", help="Issue description")
    create_parser.add_argument("--priority", help="Priority name")
    create_parser.add_argument("--labels", help="Comma-separated labels")
    create_parser.add_argument("--assignee", help="Assignee account ID")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Update subcommand
    update_parser = issue_subparsers.add_parser("update", help="Update existing issue")
    update_parser.add_argument("issue_key", help="Issue key")
    update_parser.add_argument("--summary", help="New summary")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument("--priority", help="New priority")
    update_parser.add_argument("--labels", help="New labels (comma-separated)")
    update_parser.add_argument("--assignee", help="New assignee account ID")

    # Comment subcommand
    comment_parser = issue_subparsers.add_parser("comment", help="Add comment to issue")
    comment_parser.add_argument("issue_key", help="Issue key")
    comment_parser.add_argument("body", help="Comment text")
    comment_parser.add_argument(
        "--security-level",
        help="Security level for private comment (e.g., 'Red Hat Internal', 'Employees')",
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
        help="Security level for private comment (e.g., 'Red Hat Internal', 'Employees')",
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

    return 1


if __name__ == "__main__":
    sys.exit(main())
