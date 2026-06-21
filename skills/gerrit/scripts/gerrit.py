#!/usr/bin/env python3
"""Gerrit wrapper skill for AI agents.

Wraps Gerrit SSH query commands to produce markdown-formatted output for
read/view operations. Action commands (review, abandon, submit) should use
SSH gerrit commands directly.

Usage:
    python gerrit.py check
    python gerrit.py changes list
    python gerrit.py changes view 12345
    python gerrit.py changes search "status:open project:myproject"
    python gerrit.py projects list

Requirements:
    SSH access to a Gerrit server (typically configured via .gitreview)
"""

from __future__ import annotations

import argparse
import base64
import configparser
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================================
# SSH / GERRIT HELPERS
# ============================================================================


def _read_gitreview(path: str | None = None) -> dict[str, str]:
    """Parse .gitreview file for Gerrit connection details.

    Args:
        path: Path to .gitreview file. Defaults to .gitreview in cwd.

    Returns:
        Dict with host, port, project, username keys (values may be empty).
    """
    gitreview_path = Path(path) if path else Path(".gitreview")
    result: dict[str, str] = {"host": "", "port": "29418", "project": "", "username": ""}

    if not gitreview_path.exists():
        return result

    config = configparser.ConfigParser()
    config.read(str(gitreview_path))

    if config.has_section("gerrit"):
        result["host"] = config.get("gerrit", "host", fallback="")
        result["port"] = config.get("gerrit", "port", fallback="29418")
        result["project"] = config.get("gerrit", "project", fallback="")

    return result


def _get_ssh_cmd(host: str, port: str = "29418", username: str | None = None) -> list[str]:
    """Build SSH command prefix for Gerrit.

    Args:
        host: Gerrit server hostname.
        port: SSH port (default 29418).
        username: SSH username (optional).

    Returns:
        List of command parts for SSH connection.
    """
    cmd = ["ssh", "-p", port]
    if username:
        cmd.append(f"{username}@{host}")
    else:
        cmd.append(host)
    return cmd


def run_gerrit_query(
    host: str,
    query: str,
    port: str = "29418",
    username: str | None = None,
    extra_args: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Execute a Gerrit SSH query and return parsed results.

    Gerrit query returns newline-delimited JSON with a stats line at the end.

    Args:
        host: Gerrit server hostname.
        query: Gerrit query string.
        port: SSH port.
        username: SSH username.
        extra_args: Additional arguments (e.g., --current-patch-set).

    Returns:
        List of change/result dicts (stats line excluded).

    Raises:
        SystemExit: If SSH command fails.
    """
    ssh_cmd = _get_ssh_cmd(host, port, username)
    gerrit_args = ["gerrit", "query", "--format=JSON", query]
    if extra_args:
        gerrit_args.extend(extra_args)

    cmd = [*ssh_cmd, *gerrit_args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    results = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Skip the stats line (has "type": "stats")
        if obj.get("type") == "stats":
            continue
        results.append(obj)

    return results


# ============================================================================
# DATE FORMATTING
# ============================================================================


def format_timestamp(timestamp: int | None) -> str:
    """Format a Unix timestamp to YYYY-MM-DD HH:MM.

    Args:
        timestamp: Unix timestamp (seconds since epoch).

    Returns:
        Formatted date string, or "N/A" if input is None/0.
    """
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (OSError, ValueError, OverflowError):
        return "N/A"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_owner(owner: dict[str, Any] | None) -> str:
    """Extract owner name from a Gerrit owner dict.

    Args:
        owner: Owner dictionary with 'username' or 'name' key.

    Returns:
        Username/name string or "Unknown".
    """
    if not owner:
        return "Unknown"
    if isinstance(owner, dict):
        return owner.get("username", owner.get("name", "Unknown"))
    return str(owner)


# ============================================================================
# FORMAT FUNCTIONS — one per entity type (markdown output)
# ============================================================================


def format_change_summary(change: dict[str, Any]) -> str:
    """Format a Gerrit change for markdown display.

    Args:
        change: Change dictionary from Gerrit query JSON.

    Returns:
        Markdown-formatted string.
    """
    number = change.get("number", "?")
    subject = change.get("subject", "(No subject)")
    status = change.get("status", "UNKNOWN")
    owner = _get_owner(change.get("owner"))
    project = change.get("project", "")
    branch = change.get("branch", "")
    created = format_timestamp(change.get("createdOn"))

    lines = [
        f"### Change {number}: {subject}",
        f"- **Status:** {status}",
        f"- **Owner:** {owner}",
    ]
    if project:
        lines.append(f"- **Project:** {project}")
    if branch:
        lines.append(f"- **Branch:** {branch}")

    topic = change.get("topic")
    if topic:
        lines.append(f"- **Topic:** {topic}")

    lines.append(f"- **Created:** {created}")

    updated = format_timestamp(change.get("lastUpdated"))
    if updated != "N/A":
        lines.append(f"- **Updated:** {updated}")

    # Current patch set approvals
    patch_set = change.get("currentPatchSet", {})
    if isinstance(patch_set, dict):
        approvals = patch_set.get("approvals", [])
        if approvals:
            lines.append("\n**Approvals:**")
            for approval in approvals:
                if isinstance(approval, dict):
                    by = approval.get("by", {})
                    reviewer = (
                        by.get("username", by.get("name", "?")) if isinstance(by, dict) else "?"
                    )
                    a_type = approval.get("type", "?")
                    value = approval.get("value", "?")
                    lines.append(f"- **{a_type}:** {value} (by {reviewer})")

    # Comments
    comments = change.get("comments", [])
    if comments:
        lines.append(f"\n**Comments ({len(comments)}):**")
        for comment in comments[-5:]:  # Show last 5 comments
            if isinstance(comment, dict):
                reviewer = _get_owner(comment.get("reviewer"))
                message = comment.get("message", "").strip()
                ts = format_timestamp(comment.get("timestamp"))
                if message:
                    # Truncate long messages
                    if len(message) > 200:
                        message = message[:200] + "..."
                    lines.append(f"- **{reviewer}** ({ts}): {message}")

    url = change.get("url")
    if url:
        lines.append(f"\n- **URL:** {url}")

    return "\n".join(lines)


def format_change_row(change: dict[str, Any]) -> str:
    """Format a Gerrit change as a compact markdown entry for lists.

    Args:
        change: Change dictionary from Gerrit query JSON.

    Returns:
        Markdown-formatted string.
    """
    number = change.get("number", "?")
    subject = change.get("subject", "(No subject)")
    status = change.get("status", "UNKNOWN")
    owner = _get_owner(change.get("owner"))
    project = change.get("project", "")
    created = format_timestamp(change.get("createdOn"))

    lines = [
        f"### Change {number}: {subject}",
        f"- **Status:** {status}",
        f"- **Owner:** {owner}",
    ]
    if project:
        lines.append(f"- **Project:** {project}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


def format_project_row(project_name: str) -> str:
    """Format a Gerrit project name as a compact markdown entry.

    Args:
        project_name: Project name string.

    Returns:
        Markdown-formatted string.
    """
    return f"### {project_name}"


# ============================================================================
# REST API HELPERS
# ============================================================================


def fetch_change_diff(
    host: str,
    change_number: int,
    patchset: str = "current",
    scheme: str = "https",
) -> str:
    """Fetch the unified diff for a Gerrit change via the REST API.

    Uses the ``/changes/{id}/revisions/{rev}/patch`` endpoint which returns the
    diff as base64-encoded content.

    Args:
        host: Gerrit server hostname.
        change_number: Gerrit change number.
        patchset: Patchset revision — ``"current"`` (default) or a number like ``"3"``.
        scheme: URL scheme (``"https"`` or ``"http"``).

    Returns:
        Decoded unified diff as a string.

    Raises:
        SystemExit: On HTTP errors.
    """
    url = f"{scheme}://{host}/changes/{change_number}/revisions/{patchset}/patch"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/text"})
        with urllib.request.urlopen(req) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(
                f"Error: Change {change_number} (patchset {patchset}) not found.",
                file=sys.stderr,
            )
        elif exc.code == 403:
            print(
                "Error: Access denied. The change may require authentication.",
                file=sys.stderr,
            )
            print(
                "Set HTTP password in Gerrit: Settings > HTTP Credentials",
                file=sys.stderr,
            )
        else:
            print(f"Error: HTTP {exc.code} fetching diff: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Error: Cannot connect to {scheme}://{host}: {exc.reason}", file=sys.stderr)
        print("Try --scheme http if the server does not support HTTPS.", file=sys.stderr)
        sys.exit(1)

    # Gerrit returns base64-encoded patch content
    decoded = raw.decode("utf-8").strip()
    try:
        return base64.b64decode(decoded).decode("utf-8")
    except Exception:
        # Some Gerrit versions may prefix with )]}' — strip and retry
        if decoded.startswith(")]}'"):
            decoded = decoded.split("\n", 1)[1].strip()
            return base64.b64decode(decoded).decode("utf-8")
        raise


# ============================================================================
# COMMAND HANDLERS — one per subcommand, return exit code
# ============================================================================


def cmd_check(args: argparse.Namespace) -> int:
    """Verify Gerrit SSH access is working.

    Args:
        args: Parsed arguments with host, port, username.

    Returns:
        Exit code (0 success, 1 error).
    """
    gitreview = _read_gitreview()
    host = args.host or gitreview["host"]
    port = args.port or gitreview["port"]
    username = args.username or gitreview.get("username") or None

    if not host:
        print(
            "Error: No Gerrit host specified. Use --host or create a .gitreview file.",
            file=sys.stderr,
        )
        return 1

    ssh_cmd = _get_ssh_cmd(host, port, username)
    cmd = [*ssh_cmd, "gerrit", "version"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: Cannot connect to Gerrit.", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        print(f"\nCheck SSH access: ssh -p {port} {host} gerrit version", file=sys.stderr)
        return 1

    print("\u2713 Gerrit SSH access is working")
    output = result.stdout.strip() or result.stderr.strip()
    if output:
        print(f"  {output}")
    return 0


def cmd_changes_list(args: argparse.Namespace) -> int:
    """List open changes.

    Args:
        args: Parsed arguments with host, port, username, project, limit, json flags.

    Returns:
        Exit code.
    """
    gitreview = _read_gitreview()
    host = args.host or gitreview["host"]
    port = args.port or gitreview["port"]
    username = args.username or gitreview.get("username") or None
    project = gitreview.get("project", "")

    if not host:
        print("Error: No Gerrit host specified.", file=sys.stderr)
        return 1

    query = "status:open"
    if project:
        query += f" project:{project}"
    query += f" limit:{args.limit}"

    changes = run_gerrit_query(host, query, port, username)

    if args.json:
        print(json.dumps(changes, indent=2))
    else:
        if not changes:
            print("No open changes found")
        else:
            print(f"## Open Changes\n\nFound {len(changes)} change(s):\n")
            print("\n\n".join(format_change_row(c) for c in changes))
    return 0


def cmd_changes_view(args: argparse.Namespace) -> int:
    """View a single change.

    Args:
        args: Parsed arguments with change number, host, port, username, json flags.

    Returns:
        Exit code.
    """
    gitreview = _read_gitreview()
    host = args.host or gitreview["host"]
    port = args.port or gitreview["port"]
    username = args.username or gitreview.get("username") or None

    if not host:
        print("Error: No Gerrit host specified.", file=sys.stderr)
        return 1

    changes = run_gerrit_query(
        host,
        f"change:{args.number}",
        port,
        username,
        extra_args=["--current-patch-set", "--comments"],
    )

    if args.json:
        print(json.dumps(changes, indent=2))
    else:
        if not changes:
            print(f"Change {args.number} not found")
        else:
            print(format_change_summary(changes[0]))
    return 0


def cmd_changes_diff(args: argparse.Namespace) -> int:
    """Fetch and display the unified diff for a change.

    Args:
        args: Parsed arguments with change number, patchset, host, scheme, json flags.

    Returns:
        Exit code.
    """
    gitreview = _read_gitreview()
    host = args.host or gitreview["host"]

    if not host:
        print("Error: No Gerrit host specified.", file=sys.stderr)
        return 1

    scheme = args.scheme
    patchset = args.patchset

    diff_text = fetch_change_diff(host, args.number, patchset=patchset, scheme=scheme)

    if args.json:
        print(json.dumps({"change": args.number, "patchset": patchset, "diff": diff_text}))
    else:
        print(diff_text, end="")
    return 0


def cmd_changes_search(args: argparse.Namespace) -> int:
    """Search changes with a custom query.

    Args:
        args: Parsed arguments with query, host, port, username, limit, json flags.

    Returns:
        Exit code.
    """
    gitreview = _read_gitreview()
    host = args.host or gitreview["host"]
    port = args.port or gitreview["port"]
    username = args.username or gitreview.get("username") or None

    if not host:
        print("Error: No Gerrit host specified.", file=sys.stderr)
        return 1

    query = f"{args.query} limit:{args.limit}"
    changes = run_gerrit_query(host, query, port, username)

    if args.json:
        print(json.dumps(changes, indent=2))
    else:
        if not changes:
            print("No changes found")
        else:
            print(f"## Search Results\n\nFound {len(changes)} change(s):\n")
            print("\n\n".join(format_change_row(c) for c in changes))
    return 0


def cmd_projects_list(args: argparse.Namespace) -> int:
    """List projects.

    Args:
        args: Parsed arguments with host, port, username, limit, json flags.

    Returns:
        Exit code.
    """
    gitreview = _read_gitreview()
    host = args.host or gitreview["host"]
    port = args.port or gitreview["port"]
    username = args.username or gitreview.get("username") or None

    if not host:
        print("Error: No Gerrit host specified.", file=sys.stderr)
        return 1

    ssh_cmd = _get_ssh_cmd(host, port, username)
    cmd = [*ssh_cmd, "gerrit", "ls-projects", "--format", "json"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    if not output:
        if args.json:
            print("{}")
        else:
            print("No projects found")
        return 0

    try:
        projects_data = json.loads(output)
    except json.JSONDecodeError:
        # Fallback: treat as line-delimited project names
        project_names = [line.strip() for line in output.splitlines() if line.strip()]
        if args.json:
            print(json.dumps(project_names, indent=2))
        else:
            if not project_names:
                print("No projects found")
            else:
                items = project_names[: args.limit]
                print(f"## Projects\n\nFound {len(items)} project(s):\n")
                print("\n\n".join(format_project_row(p) for p in items))
        return 0

    if args.json:
        print(json.dumps(projects_data, indent=2))
    else:
        # Gerrit ls-projects --format json returns {name: {id: ...}, ...}
        project_names = sorted(projects_data.keys())[: args.limit]
        if not project_names:
            print("No projects found")
        else:
            print(f"## Projects\n\nFound {len(project_names)} project(s):\n")
            print("\n\n".join(format_project_row(p) for p in project_names))
    return 0


# ============================================================================
# ARGUMENT PARSER
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with nested subcommands.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description="Gerrit wrapper for AI agents \u2014 markdown-formatted query output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global connection args
    parser.add_argument("--host", help="Gerrit server hostname")
    parser.add_argument("--port", default="", help="SSH port (default: 29418)")
    parser.add_argument("--username", help="SSH username")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check
    subparsers.add_parser("check", help="Verify Gerrit SSH access")

    # changes
    changes_parser = subparsers.add_parser("changes", help="Change operations")
    changes_sub = changes_parser.add_subparsers(dest="changes_command")

    changes_list = changes_sub.add_parser("list", help="List open changes")
    changes_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    changes_list.add_argument("--json", action="store_true", help="Output raw JSON")

    changes_view = changes_sub.add_parser("view", help="View change details")
    changes_view.add_argument("number", type=int, help="Change number")
    changes_view.add_argument("--json", action="store_true", help="Output raw JSON")

    changes_diff = changes_sub.add_parser("diff", help="Get unified diff of a change")
    changes_diff.add_argument("number", type=int, help="Change number")
    changes_diff.add_argument(
        "--patchset", default="current", help="Patchset number (default: current)"
    )
    changes_diff.add_argument(
        "--scheme", default="https", choices=["https", "http"], help="URL scheme (default: https)"
    )
    changes_diff.add_argument("--json", action="store_true", help="Output as JSON")

    changes_search = changes_sub.add_parser("search", help="Search changes")
    changes_search.add_argument("query", help="Gerrit query string")
    changes_search.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    changes_search.add_argument("--json", action="store_true", help="Output raw JSON")

    # projects
    projects_parser = subparsers.add_parser("projects", help="Project operations")
    projects_sub = projects_parser.add_subparsers(dest="projects_command")

    projects_list = projects_sub.add_parser("list", help="List projects")
    projects_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    projects_list.add_argument("--json", action="store_true", help="Output raw JSON")

    return parser


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    """Main entry point.

    Returns:
        Exit code.
    """
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "check":
        return cmd_check(args)
    elif args.command == "changes":
        if not hasattr(args, "changes_command") or not args.changes_command:
            parser.parse_args(["changes", "--help"])
            return 1
        if args.changes_command == "list":
            return cmd_changes_list(args)
        elif args.changes_command == "view":
            return cmd_changes_view(args)
        elif args.changes_command == "diff":
            return cmd_changes_diff(args)
        elif args.changes_command == "search":
            return cmd_changes_search(args)
    elif args.command == "projects":
        if not hasattr(args, "projects_command") or not args.projects_command:
            parser.parse_args(["projects", "--help"])
            return 1
        if args.projects_command == "list":
            return cmd_projects_list(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
