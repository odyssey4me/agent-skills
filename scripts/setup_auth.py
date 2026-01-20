#!/usr/bin/env python3
"""Interactive authentication setup for agent skills.

Usage:
    python scripts/setup_auth.py <service> [--force]

Examples:
    python scripts/setup_auth.py jira
    python scripts/setup_auth.py github --force
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from collections.abc import Callable

from shared.auth import get_credentials
from shared.auth.keyring_store import get_credential, set_credential
from shared.auth.token import CONFIG_DIR


def get_env_var_name(service: str, field: str) -> str | None:
    """Get the environment variable name for a service field.

    Args:
        service: Service name (e.g., "jira", "github").
        field: Field name (e.g., "url", "token").

    Returns:
        Environment variable name that is actually set, or the preferred name if none set.
    """
    prefix = service.upper().replace("-", "_")

    # Check for multiple possible env var names and return the one that's set
    if field == "url":
        # Check both BASE_URL and URL variants
        base_url = f"{prefix}_BASE_URL"
        url = f"{prefix}_URL"
        if os.environ.get(base_url):
            return base_url
        elif os.environ.get(url):
            return url
        # Default to preferred name for display
        return base_url if service == "jira" else url

    elif field == "token":
        # Check both API_TOKEN and TOKEN variants
        api_token = f"{prefix}_API_TOKEN"
        token = f"{prefix}_TOKEN"
        if os.environ.get(api_token):
            return api_token
        elif os.environ.get(token):
            return token
        # Default to preferred name for display
        return api_token if service == "jira" else token

    else:
        # Simple mapping for other fields
        return f"{prefix}_{field.upper()}"


def show_existing_config(service: str) -> dict[str, tuple[str, str]]:
    """Show existing configuration and return credential sources.

    Args:
        service: Service name.

    Returns:
        Dictionary mapping field names to (value, source) tuples.
    """
    print(f"\n{service.title()} Configuration Status")
    print("=" * 60)

    creds = get_credentials(service)
    fields_to_check = {
        "url": creds.url,
        "email": creds.email,
        "token": creds.token,
        "username": creds.username,
        "password": creds.password,
    }

    credential_sources = {}
    has_any_config = False

    for field, value in fields_to_check.items():
        if value is None:
            continue

        has_any_config = True

        # Determine source
        env_var = get_env_var_name(service, field)
        keyring_key = f"{service}-{field}"

        if os.environ.get(env_var):
            source = f"environment ({env_var})"
        elif get_credential(keyring_key):
            source = f"keyring (service: agent-skills, key: {keyring_key})"
        else:
            config_file = CONFIG_DIR / f"{service}.yaml"
            source = f"config file ({config_file})"

        # Mask sensitive values
        if field in ("token", "password"):
            display_value = "***" + value[-4:] if len(value) > 4 else "***"
        else:
            display_value = value

        print(f"  {field:12} {display_value:30} [{source}]")
        credential_sources[field] = (value, source)

    if not has_any_config:
        print("  No existing configuration found.")
        print()
        print("Credentials will be stored in: system keyring (service: agent-skills)")
        print(f"Config file location (if needed): {CONFIG_DIR / f'{service}.yaml'}")

    print()
    return credential_sources


def has_complete_env_config(service: str, required_fields: list[str]) -> bool:
    """Check if all required fields are set via environment variables.

    Args:
        service: Service name.
        required_fields: List of required field names.

    Returns:
        True if all required fields are set via environment variables.
    """
    for field in required_fields:
        env_var = get_env_var_name(service, field)
        if not os.environ.get(env_var):
            return False
    return True


def prompt_for_field(
    field_name: str,
    current_value: str | None = None,
    is_secret: bool = False,
    default: str | None = None,
) -> str | None:
    """Prompt user for a field value.

    Args:
        field_name: Display name of the field.
        current_value: Current value if any.
        is_secret: Whether to hide input (password/token).
        default: Default value to use if user just presses enter.

    Returns:
        New value, or None to keep current value.
    """
    prompt_text = f"{field_name}"

    if current_value:
        masked = "***" + current_value[-4:] if is_secret and len(current_value) > 4 else current_value
        prompt_text += f" [current: {masked}]"
    elif default:
        prompt_text += f" [{default}]"

    prompt_text += ": "

    value = getpass.getpass(prompt_text).strip() if is_secret else input(prompt_text).strip()

    if not value:
        return current_value or default

    return value


def verify_jira_credentials(url: str, email: str, token: str) -> bool:
    """Test Jira credentials by fetching current user.

    Args:
        url: Jira server URL.
        email: User email.
        token: API token.

    Returns:
        True if credentials are valid, False otherwise.
    """
    try:
        import requests

        response = requests.get(
            f"{url.rstrip('/')}/rest/api/2/myself",
            auth=(email, token),
            timeout=10,
        )
        return response.status_code == 200
    except Exception:
        return False


def verify_github_credentials(url: str, token: str) -> bool:
    """Test GitHub credentials by fetching current user.

    Args:
        url: GitHub API URL.
        token: Personal access token.

    Returns:
        True if credentials are valid, False otherwise.
    """
    try:
        import requests

        response = requests.get(
            f"{url.rstrip('/')}/user",
            headers={"Authorization": f"token {token}"},
            timeout=10,
        )
        return response.status_code == 200
    except Exception:
        return False


def verify_gitlab_credentials(url: str, token: str) -> bool:
    """Test GitLab credentials by fetching current user.

    Args:
        url: GitLab URL.
        token: Personal access token.

    Returns:
        True if credentials are valid, False otherwise.
    """
    try:
        import requests

        response = requests.get(
            f"{url.rstrip('/')}/api/v4/user",
            headers={"PRIVATE-TOKEN": token},
            timeout=10,
        )
        return response.status_code == 200
    except Exception:
        return False


def setup_jira() -> bool:
    """Set up Jira authentication."""
    print("\nJira Authentication Setup")
    print("=" * 60)

    # Check if all required env vars are set
    required_fields = ["url", "email", "token"]
    if has_complete_env_config("jira", required_fields):
        print("Complete configuration found in environment variables:")
        for field in required_fields:
            env_var = get_env_var_name("jira", field)
            print(f"  {env_var} is set")
        print()
        print("When all credentials are provided via environment variables,")
        print("no keyring or config file storage is needed.")
        print()
        response = input("Continue anyway to override with keyring storage? [y/N]: ").strip().lower()
        if response != "y":
            print("Using environment variables. No changes made.")
            return True

    # Show existing configuration
    existing = show_existing_config("jira")

    # Check if any credentials are from environment
    env_sources = {
        field: source
        for field, (_, source) in existing.items()
        if "environment" in source
    }

    if env_sources:
        print("Note: The following fields are set via environment variables:")
        for field, source in env_sources.items():
            print(f"  {field}: {source}")
        print()
        print("Saving to keyring will NOT override environment variables.")
        print("Environment variables always take precedence.")
        print()

    # Ask what to configure
    if existing:
        print("What would you like to do?")
        print("  1. Update all fields")
        print("  2. Update specific fields")
        print("  3. Cancel")
        choice = input("Choice [3]: ").strip() or "3"

        if choice == "3":
            print("Cancelled.")
            return True
        elif choice == "2":
            print()
            print("Select fields to update (press Enter to skip):")
            fields_to_update = []
            for field in required_fields:
                current_value, _ = existing.get(field, (None, None))
                if field in env_sources:
                    print(f"  Skipping {field} (set via environment variable)")
                    continue
                update = input(f"  Update {field}? [y/N]: ").strip().lower()
                if update == "y":
                    fields_to_update.append(field)
            if not fields_to_update:
                print("No fields selected. Cancelled.")
                return True
        else:
            fields_to_update = [f for f in required_fields if f not in env_sources]
    else:
        fields_to_update = required_fields
        print("You'll need:")
        print("  1. Your Jira server URL (e.g., https://yourcompany.atlassian.net)")
        print("  2. Your email address")
        print("  3. An API token (create at https://id.atlassian.com/manage-profile/security/api-tokens)")
        print()

    # Get current values
    url = existing.get("url", (None, None))[0]
    email = existing.get("email", (None, None))[0]
    token = existing.get("token", (None, None))[0]

    # Prompt for fields
    if "url" in fields_to_update:
        url = prompt_for_field("Jira URL", url)
        if not url:
            print("Error: URL is required")
            return False

    if "email" in fields_to_update:
        email = prompt_for_field("Email", email)
        if not email:
            print("Error: Email is required")
            return False

    if "token" in fields_to_update:
        token = prompt_for_field("API Token", token, is_secret=True)
        if not token:
            print("Error: API token is required")
            return False

    # Save to keyring
    print()
    print("Saving credentials to system keyring (service: agent-skills)...")
    set_credential("jira-url", url)
    set_credential("jira-email", email)
    set_credential("jira-token", token)

    print("Jira credentials stored successfully!")

    # Test credentials
    verify = input("Test credentials now? [Y/n]: ").strip().lower()
    if verify != "n":
        print("Verifying credentials...")
        if verify_jira_credentials(url, email, token):
            print("Credentials verified successfully!")
        else:
            print("Warning: Could not verify credentials.")
            print("This may be due to network issues or invalid credentials.")

    return True


def setup_confluence() -> bool:
    """Set up Confluence authentication."""
    print("Confluence Authentication Setup")
    print("-" * 40)
    print("Confluence uses the same authentication as Jira.")
    print("You'll need:")
    print("  1. Your Confluence server URL")
    print("  2. Your email address")
    print("  3. An API token")
    print()

    url = input("Confluence URL: ").strip()
    if not url:
        print("Error: URL is required")
        return False

    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required")
        return False

    token = getpass.getpass("API Token: ").strip()
    if not token:
        print("Error: API token is required")
        return False

    set_credential("confluence-url", url)
    set_credential("confluence-email", email)
    set_credential("confluence-token", token)

    print("\nConfluence credentials stored successfully!")
    return True


def setup_github() -> bool:
    """Set up GitHub authentication."""
    print("GitHub Authentication Setup")
    print("-" * 40)
    print("You'll need a Personal Access Token (PAT)")
    print("Create one at: https://github.com/settings/tokens")
    print("Required scopes: repo, read:org")
    print()

    url = input("GitHub URL [https://api.github.com]: ").strip()
    if not url:
        url = "https://api.github.com"

    token = getpass.getpass("Personal Access Token: ").strip()
    if not token:
        print("Error: Token is required")
        return False

    set_credential("github-url", url)
    set_credential("github-token", token)

    print("\nGitHub credentials stored successfully!")

    verify = input("Test credentials now? [Y/n]: ").strip().lower()
    if verify != "n":
        print("Verifying credentials...")
        if verify_github_credentials(url, token):
            print("Credentials verified successfully!")
        else:
            print("Warning: Could not verify credentials.")
            print("This may be due to network issues or invalid credentials.")

    return True


def setup_gitlab() -> bool:
    """Set up GitLab authentication."""
    print("GitLab Authentication Setup")
    print("-" * 40)
    print("You'll need a Personal Access Token")
    print("Create one at: https://gitlab.com/-/profile/personal_access_tokens")
    print("Required scopes: api, read_api")
    print()

    url = input("GitLab URL [https://gitlab.com]: ").strip()
    if not url:
        url = "https://gitlab.com"

    token = getpass.getpass("Personal Access Token: ").strip()
    if not token:
        print("Error: Token is required")
        return False

    set_credential("gitlab-url", url)
    set_credential("gitlab-token", token)

    print("\nGitLab credentials stored successfully!")

    verify = input("Test credentials now? [Y/n]: ").strip().lower()
    if verify != "n":
        print("Verifying credentials...")
        if verify_gitlab_credentials(url, token):
            print("Credentials verified successfully!")
        else:
            print("Warning: Could not verify credentials.")
            print("This may be due to network issues or invalid credentials.")

    return True


def setup_gerrit() -> bool:
    """Set up Gerrit authentication."""
    print("Gerrit Authentication Setup")
    print("-" * 40)
    print("You'll need:")
    print("  1. Your Gerrit server URL")
    print("  2. Your username")
    print("  3. Your HTTP password (from Gerrit settings)")
    print()

    url = input("Gerrit URL: ").strip()
    if not url:
        print("Error: URL is required")
        return False

    username = input("Username: ").strip()
    if not username:
        print("Error: Username is required")
        return False

    password = getpass.getpass("HTTP Password: ").strip()
    if not password:
        print("Error: Password is required")
        return False

    set_credential("gerrit-url", url)
    set_credential("gerrit-username", username)
    set_credential("gerrit-password", password)

    print("\nGerrit credentials stored successfully!")
    return True


def setup_google() -> bool:
    """Set up Google OAuth authentication."""
    print("Google OAuth Authentication Setup")
    print("-" * 40)
    print("This will set up OAuth for all Google services (Gmail, Drive, Calendar).")
    print()
    print("Prerequisites:")
    print("  1. A GCP project with required APIs enabled")
    print("  2. OAuth 2.0 client credentials (Desktop app type)")
    print("  3. The credentials JSON file downloaded")
    print()
    print("For help creating a GCP project, see the documentation.")
    print()

    creds_path = input("Path to credentials.json: ").strip()
    if not creds_path:
        print("Error: Credentials file path is required")
        return False

    try:
        from pathlib import Path

        from shared.auth.oauth import get_google_credentials

        creds_file = Path(creds_path).expanduser()
        if not creds_file.exists():
            print(f"Error: File not found: {creds_file}")
            return False

        print("\nSetting up Gmail...")
        get_google_credentials("gmail", creds_file)

        print("Setting up Drive...")
        get_google_credentials("drive", creds_file)

        print("Setting up Calendar...")
        get_google_credentials("calendar", creds_file)

        print("\nGoogle credentials stored successfully!")
        return True

    except ImportError:
        print("Error: Google auth libraries not installed.")
        print("Install with: pip install -e '.[google]'")
        return False


SETUP_FUNCTIONS: dict[str, Callable[[], bool]] = {
    "jira": setup_jira,
    "confluence": setup_confluence,
    "github": setup_github,
    "gitlab": setup_gitlab,
    "gerrit": setup_gerrit,
    "google": setup_google,
}


def check_existing(service: str) -> bool:
    """Check if credentials already exist for a service.

    Checks keyring, environment variables, and config files.

    Args:
        service: Service name.

    Returns:
        True if any credentials are found.
    """
    creds = get_credentials(service)
    return creds.url is not None or creds.token is not None or creds.username is not None


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Set up authentication for agent skills")
    parser.add_argument(
        "service",
        choices=list(SETUP_FUNCTIONS.keys()),
        help="Service to configure",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reconfiguration (skip environment variable check)",
    )
    args = parser.parse_args()

    # The setup functions now handle existing credentials more gracefully
    # --force is passed to context but each function handles it appropriately
    setup_fn = SETUP_FUNCTIONS[args.service]
    success = setup_fn()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
