#!/usr/bin/env python3
"""Installation and setup helper for agent-skills.

Usage:
    python scripts/install.py check
    python scripts/install.py setup --agents claude,gemini
    python scripts/install.py setup --all-agents
    python scripts/install.py setup --all-agents --dry-run

Examples:
    # Check current installation status
    python scripts/install.py check

    # Set up Claude and Gemini configs (show what would be created)
    python scripts/install.py setup --agents claude,gemini --dry-run

    # Set up all agent configs
    python scripts/install.py setup --all-agents

    # Also configure authentication
    python scripts/install.py setup --all-agents --auth jira
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Standard installation path
STANDARD_PATH = Path.home() / ".local" / "share" / "agent-skills"
PATH_POINTER_FILE = Path.home() / ".config" / "agent-skills" / "path"

SUPPORTED_AGENTS = ["claude", "codex", "gemini", "cursor", "continue", "copilot"]
SUPPORTED_SERVICES = ["jira", "confluence", "github", "gitlab", "gerrit", "google"]


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent.resolve()


def get_install_path() -> Path | None:
    """Get the current installation path, checking standard locations."""
    repo_root = get_repo_root()

    # Check if we're in the standard location
    if repo_root == STANDARD_PATH:
        return repo_root

    # Check if path pointer exists
    if PATH_POINTER_FILE.exists():
        pointer_path = Path(PATH_POINTER_FILE.read_text().strip())
        if pointer_path.exists() and pointer_path == repo_root:
            return repo_root

    return repo_root


# =============================================================================
# Check functions
# =============================================================================


def check_location() -> tuple[bool, str, str]:
    """Check if installed in standard location or has path pointer.

    Returns:
        Tuple of (ok, status_message, detail).
    """
    repo_root = get_repo_root()

    if repo_root == STANDARD_PATH:
        return True, "Standard location", str(STANDARD_PATH)

    if PATH_POINTER_FILE.exists():
        pointer_content = PATH_POINTER_FILE.read_text().strip()
        if Path(pointer_content) == repo_root:
            return True, "Path pointer configured", str(repo_root)
        return (
            False,
            "Path pointer mismatch",
            f"Points to {pointer_content}, running from {repo_root}",
        )

    return False, "Non-standard location", f"{repo_root} (no path pointer)"


def check_venv() -> tuple[bool, str, str]:
    """Check if virtual environment exists.

    Returns:
        Tuple of (ok, status_message, detail).
    """
    repo_root = get_repo_root()
    venv_path = repo_root / ".venv"

    if not venv_path.exists():
        return False, "Not found", "Run: python3 -m venv .venv"

    # Check if venv has Python
    python_path = venv_path / "bin" / "python"
    if not python_path.exists():
        python_path = venv_path / "Scripts" / "python.exe"  # Windows

    if not python_path.exists():
        return False, "Invalid venv", "Missing Python executable"

    return True, "Found", str(venv_path)


def check_dependencies() -> tuple[bool, str, str]:
    """Check if dependencies are installed.

    Returns:
        Tuple of (ok, status_message, detail).
    """
    repo_root = get_repo_root()
    venv_python = repo_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = repo_root / ".venv" / "Scripts" / "python.exe"

    if not venv_python.exists():
        return False, "No venv", "Create venv first"

    # Check if shared module is importable
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import shared; import requests"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        if result.returncode == 0:
            return True, "Installed", "shared and requests available"
        return False, "Missing", "Run: pip install -e ."
    except Exception as e:
        return False, "Error", str(e)


def check_agent_config(agent: str) -> tuple[bool, str, str]:
    """Check if agent config exists.

    Args:
        agent: Agent name (claude, gemini, cursor, continue, copilot).

    Returns:
        Tuple of (ok, status_message, detail).
    """
    config_paths = {
        "claude": [
            Path.home() / ".claude" / "CLAUDE.md",
            Path.home() / "CLAUDE.md",
        ],
        "codex": [
            Path.home() / ".vscode" / "settings.json",
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json",  # macOS
        ],
        "gemini": [
            Path.home() / ".gemini" / "GEMINI.md",
        ],
        "cursor": [
            Path.home() / ".cursor" / "rules" / "agent-skills.mdc",
        ],
        "continue": [
            Path.home() / ".continue" / "config.json",
        ],
        "copilot": [
            Path.home() / ".git-templates" / "template" / ".github" / "copilot-instructions.md",
        ],
    }

    paths = config_paths.get(agent, [])
    for path in paths:
        if path.exists():
            # For continue, codex, and claude, check if it contains agent-skills reference
            if agent in ("continue", "codex", "claude"):
                content = path.read_text()
                if "agent-skills" in content:
                    return True, "Configured", str(path)
                return False, "Exists but not configured", str(path)
            return True, "Found", str(path)

    if paths:
        return False, "Not found", f"Expected: {paths[0]}"
    return False, "Unknown agent", agent


def check_auth(service: str) -> tuple[bool, str, str]:
    """Check if authentication is configured for a service.

    Args:
        service: Service name (jira, github, etc.).

    Returns:
        Tuple of (ok, status_message, detail).
    """
    try:
        from shared.auth import get_credentials

        # Use the same credential loading as the skills do
        creds = get_credentials(service)

        if creds.is_valid():
            return True, "Configured", f"URL: {creds.url[:30] if creds.url else 'N/A'}..."
        if creds.url:
            return False, "Partial", "URL set, token/credentials missing"
        return False, "Not configured", f"Run: python scripts/setup_auth.py {service}"
    except Exception as e:
        return False, "Error", str(e)


def check_skills() -> tuple[bool, str, str]:
    """Check if skills are valid.

    Returns:
        Tuple of (ok, status_message, detail).
    """
    repo_root = get_repo_root()
    skills_dir = repo_root / "skills"

    if not skills_dir.exists():
        return False, "No skills directory", str(skills_dir)

    skills = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

    if not skills:
        return False, "No skills found", "No SKILL.md files in skills/"

    return True, f"{len(skills)} skill(s)", ", ".join(s.name for s in skills)


# =============================================================================
# Agent config content
# =============================================================================


def load_config_sample(agent: str) -> tuple[Path, str] | None:
    """Load config sample file for an agent.

    Args:
        agent: Agent name.

    Returns:
        Tuple of (relative_sample_path, content) or None if not found.
    """
    repo_root = get_repo_root()

    # Map agent to sample file
    sample_files = {
        "claude": "docs/config-samples/.claude/CLAUDE.md.sample",
        "codex": "docs/config-samples/.vscode/codex-settings.json.sample",
        "gemini": "docs/config-samples/.gemini/GEMINI.md.sample",
        "cursor": "docs/config-samples/.cursor/rules/agent-skills.mdc.sample",
        "continue": "docs/config-samples/.continue/config.json.sample",
        "copilot": "docs/config-samples/.github/copilot-instructions.md",
    }

    sample_path_str = sample_files.get(agent)
    if not sample_path_str:
        return None

    sample_path = repo_root / sample_path_str
    if not sample_path.exists():
        return None

    try:
        content = sample_path.read_text()
        return (Path(sample_path_str), content)
    except Exception:
        return None


def get_agent_config_content(agent: str, install_path: Path) -> tuple[Path, str]:
    """Get the config file path and content for an agent.

    Args:
        agent: Agent name.
        install_path: Path to agent-skills installation.

    Returns:
        Tuple of (config_path, content).
    """
    # Load sample file
    sample_result = load_config_sample(agent)
    if not sample_result:
        return (Path(), "")

    _sample_path, sample_content = sample_result

    # Replace placeholder paths with actual install path
    content = sample_content.replace("~/.local/share/agent-skills", str(install_path))

    # Map agent to target config path
    target_paths = {
        "claude": Path.home() / ".claude" / "CLAUDE.md",
        "codex": Path.home() / ".vscode" / "settings.json",
        "gemini": Path.home() / ".gemini" / "GEMINI.md",
        "cursor": Path.home() / ".cursor" / "rules" / "agent-skills.mdc",
        "continue": Path.home() / ".continue" / "config.json",
        "copilot": Path.home() / ".git-templates" / "template" / ".github" / "copilot-instructions.md",
    }

    target_path = target_paths.get(agent, Path())
    return (target_path, content)


# =============================================================================
# Setup functions
# =============================================================================


def setup_path_pointer(dry_run: bool = False) -> bool:
    """Create path pointer file if not in standard location.

    Args:
        dry_run: If True, only print what would be done.

    Returns:
        True if successful or not needed.
    """
    repo_root = get_repo_root()

    if repo_root == STANDARD_PATH:
        print("  Already in standard location, no pointer needed")
        return True

    if dry_run:
        print(f"  Would create: {PATH_POINTER_FILE}")
        print(f"  Content: {repo_root}")
        return True

    PATH_POINTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    PATH_POINTER_FILE.write_text(str(repo_root))
    print(f"  Created: {PATH_POINTER_FILE}")
    return True


def setup_venv(dry_run: bool = False) -> bool:
    """Create virtual environment if it doesn't exist.

    Args:
        dry_run: If True, only print what would be done.

    Returns:
        True if successful.
    """
    repo_root = get_repo_root()
    venv_path = repo_root / ".venv"

    if venv_path.exists():
        print("  Virtual environment already exists")
        return True

    if dry_run:
        print(f"  Would create: {venv_path}")
        return True

    print(f"  Creating virtual environment at {venv_path}...")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(venv_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return False

    print("  Virtual environment created")
    return True


def setup_dependencies(dry_run: bool = False) -> bool:
    """Install dependencies.

    Args:
        dry_run: If True, only print what would be done.

    Returns:
        True if successful.
    """
    repo_root = get_repo_root()
    venv_pip = repo_root / ".venv" / "bin" / "pip"
    if not venv_pip.exists():
        venv_pip = repo_root / ".venv" / "Scripts" / "pip.exe"

    if not venv_pip.exists():
        print("  Error: Virtual environment not found")
        return False

    if dry_run:
        print(f"  Would run: {venv_pip} install -e .")
        return True

    print("  Installing dependencies...")
    result = subprocess.run(
        [str(venv_pip), "install", "-e", "."],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return False

    print("  Dependencies installed")
    return True


def setup_agent_config(agent: str, dry_run: bool = False) -> bool:
    """Set up configuration for an agent.

    Args:
        agent: Agent name.
        dry_run: If True, only print what would be done.

    Returns:
        True if successful.
    """
    install_path = get_install_path()
    if not install_path:
        print("  Error: Could not determine installation path")
        return False

    config_path, content = get_agent_config_content(agent, install_path)

    if not config_path or not content:
        print(f"  Error: Unknown agent '{agent}'")
        return False

    # Check if config already exists
    if config_path.exists():
        existing_content = config_path.read_text()

        # Check if it already contains agent-skills reference
        if "agent-skills" in existing_content:
            print(f"  {config_path} already configured for agent-skills")
            return True

        # Special handling for JSON configs (continue, codex) - need manual merge
        if agent in ("continue", "codex"):
            print(f"  {config_path} exists but doesn't reference agent-skills")
            print("  Manual merge required - add this to your existing config:")
            print("  ---")
            if agent == "continue":
                # Print just the customCommands part
                for line in content.split("\n")[2:-3]:
                    print(f"  {line}")
            else:  # codex
                print(content)
            print("  ---")
            return True

        # For other configs, offer to back up and replace
        if dry_run:
            print(f"  {config_path} exists - would backup to {config_path}.backup")
            print(f"  Would create new config from sample")
        else:
            # Backup existing
            backup_path = Path(str(config_path) + ".backup")
            config_path.rename(backup_path)
            print(f"  Backed up existing config to: {backup_path}")

            # Create new config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(content)
            print(f"  Created: {config_path}")

        return True

    # Config doesn't exist - create it
    if dry_run:
        print(f"  Would create: {config_path}")
        print("  Content from sample:")
        print("  ---")
        for line in content.split("\n")[:10]:
            print(f"  {line}")
        if len(content.split("\n")) > 10:
            print("  ...")
        print("  ---")
        return True

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content)
    print(f"  Created: {config_path}")
    return True


# =============================================================================
# Commands
# =============================================================================


def cmd_check(_args: argparse.Namespace) -> int:
    """Run all checks and report status.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code (0 = all ok, 1 = issues found).
    """
    print("Agent Skills Installation Check")
    print("=" * 40)

    all_ok = True

    # Core checks
    print("\nCore:")
    for name, check_fn in [
        ("Location", check_location),
        ("Virtual env", check_venv),
        ("Dependencies", check_dependencies),
        ("Skills", check_skills),
    ]:
        ok, status, detail = check_fn()
        symbol = "[ok]" if ok else "[!!]"
        print(f"  {symbol} {name}: {status}")
        if not ok:
            print(f"      {detail}")
            all_ok = False

    # Agent configs
    print("\nAgent Configs:")
    for agent in SUPPORTED_AGENTS:
        ok, status, detail = check_agent_config(agent)
        symbol = "[ok]" if ok else "[--]"
        print(f"  {symbol} {agent}: {status}")

    # Auth (only check common ones)
    print("\nAuthentication:")
    for service in ["jira", "github", "gitlab"]:
        ok, status, detail = check_auth(service)
        symbol = "[ok]" if ok else "[--]"
        print(f"  {symbol} {service}: {status}")

    print()
    if all_ok:
        print("Core installation OK")
        return 0
    else:
        print("Issues found - run 'install.py setup' to fix")
        return 1


def cmd_setup(args: argparse.Namespace) -> int:
    """Set up agent-skills installation.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    dry_run = args.dry_run
    mode = "Dry run" if dry_run else "Setup"

    print(f"Agent Skills {mode}")
    print("=" * 40)

    # Determine which agents to configure
    agents = []
    if args.all_agents:
        agents = SUPPORTED_AGENTS.copy()
    elif args.agents:
        agents = [a.strip() for a in args.agents.split(",")]
        invalid = [a for a in agents if a not in SUPPORTED_AGENTS]
        if invalid:
            print(f"Error: Unknown agent(s): {', '.join(invalid)}")
            print(f"Supported: {', '.join(SUPPORTED_AGENTS)}")
            return 1

    # Core setup
    print("\nCore setup:")

    print("  Path pointer...")
    if not setup_path_pointer(dry_run):
        return 1

    print("  Virtual environment...")
    if not setup_venv(dry_run):
        return 1

    print("  Dependencies...")
    if not setup_dependencies(dry_run):
        return 1

    # Agent configs
    if agents:
        print(f"\nAgent configs ({', '.join(agents)}):")
        for agent in agents:
            print(f"  {agent}...")
            setup_agent_config(agent, dry_run)

    # Auth setup
    if args.auth:
        services = [s.strip() for s in args.auth.split(",")]
        invalid = [s for s in services if s not in SUPPORTED_SERVICES]
        if invalid:
            print(f"Error: Unknown service(s): {', '.join(invalid)}")
            print(f"Supported: {', '.join(SUPPORTED_SERVICES)}")
            return 1

        if dry_run:
            print("\nAuthentication (would prompt for):")
            for service in services:
                print(f"  - {service}")
        else:
            print("\nAuthentication:")
            for service in services:
                print(f"\nConfiguring {service}...")
                # Import and run setup function
                from setup_auth import SETUP_FUNCTIONS

                if service in SETUP_FUNCTIONS:
                    SETUP_FUNCTIONS[service]()

    print()
    if dry_run:
        print("Dry run complete - no changes made")
        print("Run without --dry-run to apply changes")
    else:
        print("Setup complete!")
        print("Run 'python scripts/install.py check' to verify")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Installation and setup helper for agent-skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/install.py check
  python scripts/install.py setup --agents claude,gemini --dry-run
  python scripts/install.py setup --all-agents
  python scripts/install.py setup --all-agents --auth jira
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # check command
    check_parser = subparsers.add_parser("check", help="Check installation status")
    check_parser.set_defaults(func=cmd_check)

    # setup command
    setup_parser = subparsers.add_parser("setup", help="Set up agent-skills")
    setup_parser.add_argument(
        "--agents",
        metavar="LIST",
        help=f"Comma-separated list of agents to configure ({', '.join(SUPPORTED_AGENTS)})",
    )
    setup_parser.add_argument(
        "--all-agents",
        action="store_true",
        help="Configure all supported agents",
    )
    setup_parser.add_argument(
        "--auth",
        metavar="LIST",
        help=f"Comma-separated list of services to authenticate ({', '.join(SUPPORTED_SERVICES)})",
    )
    setup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    setup_parser.set_defaults(func=cmd_setup)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
