"""HTTP/REST utilities for API interactions."""

from __future__ import annotations

from typing import Any

import requests

from shared.auth import get_credentials


class APIError(Exception):
    """Exception raised for API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


def _get_jira_auth_method(creds: Any) -> tuple[tuple[str, str] | None, dict[str, str]]:
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

    try:
        from skills.jira.api import is_cloud
        if is_cloud():
            # Cloud: email + API token as basic auth
            if creds.email and creds.token:
                auth = (creds.email, creds.token)
        else:
            # DC/Server: Bearer token
            if creds.token:
                headers["Authorization"] = f"Bearer {creds.token}"
    except ImportError:
        # Fallback if jira.api not available: use basic auth
        if creds.email and creds.token:
            auth = (creds.email, creds.token)

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
        service: Service name (e.g., "jira", "github").
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
        raise APIError(
            f"No valid credentials found for {service}. Run: python scripts/setup_auth.py {service}"
        )

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
            # Bearer token style (GitHub, GitLab)
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
