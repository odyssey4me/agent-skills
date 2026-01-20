"""Jira API version detection and helpers.

This module automatically detects whether the Jira instance is Cloud or Data Center,
then uses the correct REST API version (v3 for Cloud, v2 for DC/Server).
"""

from __future__ import annotations

import time
from typing import Any

import requests

from shared.auth import get_credentials

# Module-level cache for deployment type detection
# Key: Jira URL, Value: {"deployment_type": str, "api_version": str}
_deployment_cache: dict[str, dict[str, str]] = {}

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
                    raise JiraDetectionError(
                        f"Rate limited after {MAX_RETRIES} attempts"
                    )

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
