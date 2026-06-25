#!/usr/bin/env python3
"""Google Workspace skill setup and legacy cleanup.

Provides check and cleanup commands for the consolidated Google skill
that uses gogcli (gog) as the backend.

Usage:
    google.py check
    google.py cleanup
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "agent-skills"
LEGACY_SERVICES = [
    "gmail",
    "google-calendar",
    "google-docs",
    "google-drive",
    "google-sheets",
    "google-slides",
]
LEGACY_CONFIG_FILES = [
    "gmail.yaml",
    "google-calendar.yaml",
    "google-docs.yaml",
    "google-drive.yaml",
    "google-sheets.yaml",
    "google-slides.yaml",
]
KEYRING_SERVICE = "agent-skills"


def find_gog() -> str | None:
    """Find the gog binary in PATH."""
    return shutil.which("gog")


def run_gog(args: list[str], capture: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a gog command."""
    gog = find_gog()
    if not gog:
        print("Error: gog not found in PATH", file=sys.stderr)
        print("Install from: https://github.com/openclaw/gogcli/releases", file=sys.stderr)
        sys.exit(1)
    cmd = [gog, *args]
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True)
    return subprocess.run(cmd, text=True)


def _load_pinned_version() -> dict | None:
    """Load pinned gogcli version from dependencies.json."""
    deps_file = Path(__file__).resolve().parent.parent / "dependencies.json"
    if not deps_file.exists():
        return None
    with open(deps_file) as f:
        data = json.load(f)
    return data.get("gogcli")


def cmd_check(_args: argparse.Namespace) -> None:
    """Verify gog is available, authenticated, and can reach Google APIs."""
    print("## Google Workspace Skill Check\n")

    gog = find_gog()
    if not gog:
        print("- **gog binary:** not found")
        print("\nInstall from: https://github.com/openclaw/gogcli/releases")
        sys.exit(1)

    result = run_gog(["--version"])
    version = result.stdout.strip() if result.returncode == 0 else "unknown"
    print(f"- **gog binary:** {gog}")
    print(f"- **gog version:** {version}")

    pinned = _load_pinned_version()
    if pinned:
        pinned_ver = pinned.get("version", "unknown")
        installed_ver = version.split()[0].lstrip("v") if version != "unknown" else "unknown"
        if installed_ver == pinned_ver:
            print(f"- **pinned version:** {pinned_ver} (match)")
        else:
            print(f"- **pinned version:** {pinned_ver} (MISMATCH — installed {installed_ver})")
        validated = pinned.get("validated")
        if validated:
            print(f"- **last validated:** {validated}")
        else:
            print("- **last validated:** not yet validated")

    result = run_gog(["auth", "doctor", "--no-input"])
    if result.returncode == 0:
        print("- **auth:** healthy")
    else:
        print("- **auth:** not configured")
        print(f"\n{result.stderr.strip()}" if result.stderr else "")
        print("\nRun `gog auth setup` to configure authentication.")
        sys.exit(4)

    result = run_gog(["gmail", "labels", "list", "--json", "--results-only", "--no-input"])
    if result.returncode == 0:
        print("- **API connectivity:** verified (Gmail)")
    elif result.returncode == 7:
        print("- **API connectivity:** rate limited (try again later)")
    else:
        print("- **API connectivity:** failed")
        if result.stderr:
            print(f"  {result.stderr.strip()}")

    print("\n**Status:** ready" if result.returncode == 0 else "\n**Status:** needs attention")


def _cleanup_legacy() -> None:
    """Remove legacy keyring tokens and config files."""
    removed = []

    try:
        import keyring

        for service in LEGACY_SERVICES:
            key = f"{service}-token-json"
            token = keyring.get_password(KEYRING_SERVICE, key)
            if token:
                keyring.delete_password(KEYRING_SERVICE, key)
                removed.append(f"keyring: {KEYRING_SERVICE}/{key}")
    except ImportError:
        print("Warning: keyring not installed, skipping keyring cleanup", file=sys.stderr)
    except Exception as e:
        print(f"Warning: keyring cleanup error: {e}", file=sys.stderr)

    for config_name in LEGACY_CONFIG_FILES:
        config_file = CONFIG_DIR / config_name
        if config_file.exists():
            config_file.unlink()
            removed.append(f"config: {config_file}")

    google_yaml = CONFIG_DIR / "google.yaml"
    if google_yaml.exists():
        try:
            import yaml

            with open(google_yaml) as f:
                data = yaml.safe_load(f)
            if data and "oauth_client" in data:
                if len(data) == 1:
                    google_yaml.unlink()
                    removed.append(f"config: {google_yaml} (removed entirely)")
                else:
                    del data["oauth_client"]
                    with open(google_yaml, "w") as f:
                        yaml.safe_dump(data, f, default_flow_style=False)
                    google_yaml.chmod(0o600)
                    removed.append(f"config: {google_yaml} (removed oauth_client section)")
        except ImportError:
            print("Warning: pyyaml not installed, skipping google.yaml cleanup", file=sys.stderr)

    if removed:
        print(f"Cleaned up {len(removed)} legacy artifact(s):")
        for item in removed:
            print(f"  - {item}")
    else:
        print("No legacy artifacts found to clean up.")


def cmd_cleanup(_args: argparse.Namespace) -> None:
    """Remove legacy Python OAuth tokens and config files."""
    print("## Legacy Cleanup\n")
    _cleanup_legacy()
    print()
    print("To set up fresh authentication with gog:")
    print()
    print("  1. Download credentials.json from Google Cloud Console")
    print("     https://console.cloud.google.com/apis/credentials")
    print()
    print("  2. Import credentials and authorize:")
    print("     gog auth credentials set /path/to/credentials.json")
    print("     gog auth add your@email.com --services gmail,calendar,drive,docs,sheets,slides")
    print()
    print("  3. Verify:")
    print("     gog auth doctor")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Google Workspace skill setup and legacy cleanup")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check", help="Verify gog setup, auth, and connectivity")
    subparsers.add_parser("cleanup", help="Remove legacy Python OAuth tokens and config files")

    args = parser.parse_args()
    if args.command == "check":
        cmd_check(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)


if __name__ == "__main__":
    main()
