"""Token and configuration management for authentication."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from shared.auth.keyring_store import get_credential

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
        # Token-based auth (Jira, GitHub, GitLab)
        if self.token and self.url:
            return True
        # Username/password auth (Gerrit)
        return bool(self.username and self.password and self.url)


def get_credentials(service: str) -> Credentials:
    """Get credentials for a service using priority order.

    Priority:
    1. System keyring
    2. Environment variables
    3. Config file

    Args:
        service: Service name (e.g., "jira", "github").

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
