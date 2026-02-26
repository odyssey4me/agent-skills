#!/usr/bin/env python3
"""GitLab wrapper skill for AI agents.

Wraps the glab CLI to produce markdown-formatted output for read/view commands.
Action commands (create, merge, close, comment) should use glab directly.

Usage:
    python gitlab.py check
    python gitlab.py issues list --repo GROUP/REPO
    python gitlab.py issues view 123 --repo GROUP/REPO
    python gitlab.py mrs list --repo GROUP/REPO
    python gitlab.py mrs view 456 --repo GROUP/REPO
    python gitlab.py pipelines list --repo GROUP/REPO
    python gitlab.py pipelines view 123456 --repo GROUP/REPO
    python gitlab.py repos list
    python gitlab.py repos view GROUP/REPO

Requirements:
    glab CLI (https://gitlab.com/gitlab-org/cli)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any

# ============================================================================
# glab CLI HELPER
# ============================================================================


def run_glab(args: list[str], output_json: bool = False) -> dict[str, Any] | list[Any] | str:
    """Run a glab CLI command and return parsed output.

    Args:
        args: Arguments to pass to glab (e.g., ["issue", "list"]).
        output_json: Whether to request JSON output via --output json.

    Returns:
        Parsed JSON data (dict or list), or raw string output.

    Raises:
        SystemExit: If glab command fails.
    """
    cmd = ["glab", *args]
    if output_json:
        cmd.extend(["--output", "json"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    if output_json and output:
        return json.loads(output)
    return output


# ============================================================================
# DATE FORMATTING
# ============================================================================


def format_date(iso_date: str | None) -> str:
    """Format ISO 8601 date to YYYY-MM-DD HH:MM.

    Args:
        iso_date: ISO 8601 date string (e.g., "2024-01-15T10:30:00Z").

    Returns:
        Formatted date string, or "N/A" if input is None/empty.
    """
    if not iso_date:
        return "N/A"
    # ISO 8601: 2024-01-15T10:30:00Z → 2024-01-15 10:30
    return iso_date[:10] + " " + iso_date[11:16] if len(iso_date) >= 16 else iso_date[:10]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_username(author: dict[str, Any] | None) -> str:
    """Extract username from an author/user dict.

    Args:
        author: User dictionary with 'username' key.

    Returns:
        Username string or "Unknown".
    """
    if not author:
        return "Unknown"
    if isinstance(author, dict):
        return author.get("username", "Unknown")
    return str(author)


def _get_usernames(users: list[dict[str, Any]]) -> str:
    """Extract comma-separated usernames from a list of user dicts.

    Args:
        users: List of user dictionaries.

    Returns:
        Comma-separated usernames, or empty string if none.
    """
    if not users:
        return ""
    names = []
    for u in users:
        if isinstance(u, dict):
            names.append(u.get("username", "?"))
        else:
            names.append(str(u))
    return ", ".join(names)


def _get_labels(labels: list[Any]) -> str:
    """Extract comma-separated label names from a list.

    GitLab returns labels as plain strings, not dicts.

    Args:
        labels: List of label strings (or dicts for compatibility).

    Returns:
        Comma-separated label names, or empty string if none.
    """
    if not labels:
        return ""
    names = []
    for label in labels:
        if isinstance(label, dict):
            names.append(label.get("name", "?"))
        else:
            names.append(str(label))
    return ", ".join(names)


# ============================================================================
# FORMAT FUNCTIONS — one per entity type (markdown output)
# ============================================================================


def format_issue_summary(issue: dict[str, Any]) -> str:
    """Format a GitLab issue for markdown display.

    Args:
        issue: Issue dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    iid = issue.get("iid", "?")
    title = issue.get("title", "(No title)")
    state = issue.get("state", "unknown")
    author = _get_username(issue.get("author"))
    assignees = _get_usernames(issue.get("assignees", []))
    labels = _get_labels(issue.get("labels", []))
    created = format_date(issue.get("created_at"))

    lines = [
        f"### #{iid}: {title}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if assignees:
        lines.append(f"- **Assignees:** {assignees}")
    if labels:
        lines.append(f"- **Labels:** {labels}")
    lines.append(f"- **Created:** {created}")

    body = issue.get("description")
    if body:
        lines.append(f"\n{body.strip()}")

    url = issue.get("web_url")
    if url:
        lines.append(f"\n- **URL:** {url}")

    return "\n".join(lines)


def format_issue_row(issue: dict[str, Any]) -> str:
    """Format a GitLab issue as a compact markdown entry for lists.

    Args:
        issue: Issue dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    iid = issue.get("iid", "?")
    title = issue.get("title", "(No title)")
    state = issue.get("state", "unknown")
    author = _get_username(issue.get("author"))
    labels = _get_labels(issue.get("labels", []))
    created = format_date(issue.get("created_at"))

    lines = [
        f"### #{iid}: {title}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if labels:
        lines.append(f"- **Labels:** {labels}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


def format_mr_summary(mr: dict[str, Any]) -> str:
    """Format a GitLab merge request for markdown display.

    Args:
        mr: MR dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    iid = mr.get("iid", "?")
    title = mr.get("title", "(No title)")
    state = mr.get("state", "unknown")
    draft = " (Draft)" if mr.get("draft") else ""
    author = _get_username(mr.get("author"))
    assignees = _get_usernames(mr.get("assignees", []))
    labels = _get_labels(mr.get("labels", []))
    created = format_date(mr.get("created_at"))

    lines = [
        f"### !{iid}: {title}{draft}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if assignees:
        lines.append(f"- **Assignees:** {assignees}")
    if labels:
        lines.append(f"- **Labels:** {labels}")

    source = mr.get("source_branch")
    target = mr.get("target_branch")
    if source and target:
        lines.append(f"- **Branch:** {source} \u2192 {target}")

    merge_status = mr.get("merge_status")
    if merge_status:
        lines.append(f"- **Merge Status:** {merge_status}")

    lines.append(f"- **Created:** {created}")

    body = mr.get("description")
    if body:
        lines.append(f"\n{body.strip()}")

    url = mr.get("web_url")
    if url:
        lines.append(f"\n- **URL:** {url}")

    return "\n".join(lines)


def format_mr_row(mr: dict[str, Any]) -> str:
    """Format a GitLab MR as a compact markdown entry for lists.

    Args:
        mr: MR dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    iid = mr.get("iid", "?")
    title = mr.get("title", "(No title)")
    state = mr.get("state", "unknown")
    draft = " (Draft)" if mr.get("draft") else ""
    author = _get_username(mr.get("author"))
    labels = _get_labels(mr.get("labels", []))
    created = format_date(mr.get("created_at"))

    lines = [
        f"### !{iid}: {title}{draft}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if labels:
        lines.append(f"- **Labels:** {labels}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


def format_pipeline_summary(pipeline: dict[str, Any]) -> str:
    """Format a GitLab pipeline for markdown display.

    Args:
        pipeline: Pipeline dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    pid = pipeline.get("id", "?")
    status = pipeline.get("status", "unknown")
    ref = pipeline.get("ref", "")
    sha = pipeline.get("sha", "")
    created = format_date(pipeline.get("created_at"))

    lines = [
        f"### Pipeline #{pid}",
        f"- **Status:** {status}",
    ]
    if ref:
        lines.append(f"- **Ref:** {ref}")
    if sha:
        lines.append(f"- **Commit:** {sha[:8]}")
    lines.append(f"- **Created:** {created}")

    source = pipeline.get("source")
    if source:
        lines.append(f"- **Source:** {source}")

    url = pipeline.get("web_url")
    if url:
        lines.append(f"- **URL:** {url}")

    return "\n".join(lines)


def format_pipeline_row(pipeline: dict[str, Any]) -> str:
    """Format a GitLab pipeline as a compact markdown entry for lists.

    Args:
        pipeline: Pipeline dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    pid = pipeline.get("id", "?")
    status = pipeline.get("status", "unknown")
    ref = pipeline.get("ref", "")
    created = format_date(pipeline.get("created_at"))

    lines = [
        f"### Pipeline #{pid}",
        f"- **Status:** {status}",
    ]
    if ref:
        lines.append(f"- **Ref:** {ref}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


def format_repo_summary(repo: dict[str, Any]) -> str:
    """Format a GitLab repository for markdown display.

    Args:
        repo: Repository dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    full_name = repo.get("path_with_namespace", "")
    if not full_name:
        name = repo.get("name", "(Unknown)")
        namespace = repo.get("namespace", {})
        ns_path = namespace.get("full_path", "") if isinstance(namespace, dict) else ""
        full_name = f"{ns_path}/{name}" if ns_path else name
    description = repo.get("description") or "(No description)"
    visibility = repo.get("visibility", "unknown")
    stars = repo.get("star_count", 0)
    forks = repo.get("forks_count", 0)
    updated = format_date(repo.get("updated_at"))

    lines = [
        f"### {full_name}",
        f"- **Description:** {description}",
        f"- **Visibility:** {visibility}",
        f"- **Stars:** {stars}",
    ]

    if forks:
        lines.append(f"- **Forks:** {forks}")

    default_branch = repo.get("default_branch")
    if default_branch:
        lines.append(f"- **Default Branch:** {default_branch}")

    lines.append(f"- **Updated:** {updated}")

    url = repo.get("web_url")
    if url:
        lines.append(f"- **URL:** {url}")

    return "\n".join(lines)


def format_repo_row(repo: dict[str, Any]) -> str:
    """Format a GitLab repository as a compact markdown entry for lists.

    Args:
        repo: Repository dictionary from glab --output json.

    Returns:
        Markdown-formatted string.
    """
    full_name = repo.get("path_with_namespace", "")
    if not full_name:
        name = repo.get("name", "(Unknown)")
        namespace = repo.get("namespace", {})
        ns_path = namespace.get("full_path", "") if isinstance(namespace, dict) else ""
        full_name = f"{ns_path}/{name}" if ns_path else name
    description = repo.get("description") or "(No description)"
    visibility = repo.get("visibility", "unknown")
    stars = repo.get("star_count", 0)

    lines = [
        f"### {full_name}",
        f"- **Description:** {description}",
        f"- **Visibility:** {visibility}",
        f"- **Stars:** {stars}",
    ]
    return "\n".join(lines)


# ============================================================================
# COMMAND HANDLERS — one per subcommand, return exit code
# ============================================================================


def cmd_check(_args: argparse.Namespace) -> int:
    """Verify glab CLI is installed and authenticated.

    Args:
        _args: Parsed arguments (unused).

    Returns:
        Exit code (0 success, 1 error).
    """
    if not shutil.which("glab"):
        print(
            "Error: glab CLI not found. Install from https://gitlab.com/gitlab-org/cli",
            file=sys.stderr,
        )
        return 1

    result = subprocess.run(["glab", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: glab CLI not authenticated.", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        print("\nRun: glab auth login", file=sys.stderr)
        return 1

    print("\u2713 glab CLI is installed and authenticated")
    # Show auth details (stderr from glab auth status contains the info)
    for line in result.stderr.strip().splitlines():
        print(f"  {line.strip()}")
    return 0


def cmd_issues_list(args: argparse.Namespace) -> int:
    """List issues for a repository.

    Args:
        args: Parsed arguments with repo, limit, json flags.

    Returns:
        Exit code.
    """
    glab_args = ["issue", "list"]
    if args.repo:
        glab_args.extend(["-R", args.repo])
    glab_args.extend(["--per-page", str(args.limit)])

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        items = data if isinstance(data, list) else []
        if not items:
            print("No issues found")
        else:
            print(f"## Issues\n\nFound {len(items)} issue(s):\n")
            print("\n\n".join(format_issue_row(i) for i in items))
    return 0


def cmd_issues_view(args: argparse.Namespace) -> int:
    """View a single issue.

    Args:
        args: Parsed arguments with issue number, repo, json flags.

    Returns:
        Exit code.
    """
    glab_args = ["issue", "view", str(args.number)]
    if args.repo:
        glab_args.extend(["-R", args.repo])

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        if isinstance(data, dict):
            print(format_issue_summary(data))
    return 0


def cmd_mrs_list(args: argparse.Namespace) -> int:
    """List merge requests for a repository.

    Args:
        args: Parsed arguments with repo, limit, json flags.

    Returns:
        Exit code.
    """
    glab_args = ["mr", "list"]
    if args.repo:
        glab_args.extend(["-R", args.repo])
    glab_args.extend(["--per-page", str(args.limit)])

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        items = data if isinstance(data, list) else []
        if not items:
            print("No merge requests found")
        else:
            print(f"## Merge Requests\n\nFound {len(items)} MR(s):\n")
            print("\n\n".join(format_mr_row(mr) for mr in items))
    return 0


def cmd_mrs_view(args: argparse.Namespace) -> int:
    """View a single merge request.

    Args:
        args: Parsed arguments with MR number, repo, json flags.

    Returns:
        Exit code.
    """
    glab_args = ["mr", "view", str(args.number)]
    if args.repo:
        glab_args.extend(["-R", args.repo])

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        if isinstance(data, dict):
            print(format_mr_summary(data))
    return 0


def cmd_pipelines_list(args: argparse.Namespace) -> int:
    """List pipelines for a repository.

    Args:
        args: Parsed arguments with repo, limit, json flags.

    Returns:
        Exit code.
    """
    glab_args = ["ci", "list"]
    if args.repo:
        glab_args.extend(["-R", args.repo])
    glab_args.extend(["--per-page", str(args.limit)])

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        items = data if isinstance(data, list) else []
        if not items:
            print("No pipelines found")
        else:
            print(f"## Pipelines\n\nFound {len(items)} pipeline(s):\n")
            print("\n\n".join(format_pipeline_row(p) for p in items))
    return 0


def cmd_pipelines_view(args: argparse.Namespace) -> int:
    """View a single pipeline.

    Args:
        args: Parsed arguments with pipeline ID, repo, json flags.

    Returns:
        Exit code.
    """
    glab_args = ["ci", "view", str(args.pipeline_id)]
    if args.repo:
        glab_args.extend(["-R", args.repo])

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        if isinstance(data, dict):
            print(format_pipeline_summary(data))
    return 0


def cmd_repos_list(args: argparse.Namespace) -> int:
    """List repositories for the authenticated user.

    Args:
        args: Parsed arguments with limit, json flags.

    Returns:
        Exit code.
    """
    glab_args = ["repo", "list"]
    glab_args.extend(["--per-page", str(args.limit)])

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        items = data if isinstance(data, list) else []
        if not items:
            print("No repositories found")
        else:
            print(f"## Repositories\n\nFound {len(items)} repository(ies):\n")
            print("\n\n".join(format_repo_row(r) for r in items))
    return 0


def cmd_repos_view(args: argparse.Namespace) -> int:
    """View a single repository.

    Args:
        args: Parsed arguments with repo name, json flag.

    Returns:
        Exit code.
    """
    glab_args = ["repo", "view", args.repo]

    if args.json:
        data = run_glab(glab_args, output_json=True)
        print(json.dumps(data, indent=2))
    else:
        data = run_glab(glab_args, output_json=True)
        if isinstance(data, dict):
            print(format_repo_summary(data))
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
        description="GitLab wrapper for AI agents \u2014 markdown-formatted glab output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check
    subparsers.add_parser("check", help="Verify glab CLI is installed and authenticated")

    # issues
    issues_parser = subparsers.add_parser("issues", help="Issue operations")
    issues_sub = issues_parser.add_subparsers(dest="issues_command")

    issues_list = issues_sub.add_parser("list", help="List issues")
    issues_list.add_argument("--repo", "-R", help="Repository (GROUP/REPO)")
    issues_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    issues_list.add_argument("--json", action="store_true", help="Output raw JSON")

    issues_view = issues_sub.add_parser("view", help="View issue details")
    issues_view.add_argument("number", type=int, help="Issue number")
    issues_view.add_argument("--repo", "-R", help="Repository (GROUP/REPO)")
    issues_view.add_argument("--json", action="store_true", help="Output raw JSON")

    # mrs
    mrs_parser = subparsers.add_parser("mrs", help="Merge request operations")
    mrs_sub = mrs_parser.add_subparsers(dest="mrs_command")

    mrs_list = mrs_sub.add_parser("list", help="List merge requests")
    mrs_list.add_argument("--repo", "-R", help="Repository (GROUP/REPO)")
    mrs_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    mrs_list.add_argument("--json", action="store_true", help="Output raw JSON")

    mrs_view = mrs_sub.add_parser("view", help="View MR details")
    mrs_view.add_argument("number", type=int, help="MR number")
    mrs_view.add_argument("--repo", "-R", help="Repository (GROUP/REPO)")
    mrs_view.add_argument("--json", action="store_true", help="Output raw JSON")

    # pipelines
    pipelines_parser = subparsers.add_parser("pipelines", help="Pipeline operations")
    pipelines_sub = pipelines_parser.add_subparsers(dest="pipelines_command")

    pipelines_list = pipelines_sub.add_parser("list", help="List pipelines")
    pipelines_list.add_argument("--repo", "-R", help="Repository (GROUP/REPO)")
    pipelines_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    pipelines_list.add_argument("--json", action="store_true", help="Output raw JSON")

    pipelines_view = pipelines_sub.add_parser("view", help="View pipeline details")
    pipelines_view.add_argument("pipeline_id", type=int, help="Pipeline ID")
    pipelines_view.add_argument("--repo", "-R", help="Repository (GROUP/REPO)")
    pipelines_view.add_argument("--json", action="store_true", help="Output raw JSON")

    # repos
    repos_parser = subparsers.add_parser("repos", help="Repository operations")
    repos_sub = repos_parser.add_subparsers(dest="repos_command")

    repos_list = repos_sub.add_parser("list", help="List repositories")
    repos_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    repos_list.add_argument("--json", action="store_true", help="Output raw JSON")

    repos_view = repos_sub.add_parser("view", help="View repository details")
    repos_view.add_argument("repo", help="Repository (GROUP/REPO)")
    repos_view.add_argument("--json", action="store_true", help="Output raw JSON")

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
    elif args.command == "issues":
        if not hasattr(args, "issues_command") or not args.issues_command:
            parser.parse_args(["issues", "--help"])
            return 1
        if args.issues_command == "list":
            return cmd_issues_list(args)
        elif args.issues_command == "view":
            return cmd_issues_view(args)
    elif args.command == "mrs":
        if not hasattr(args, "mrs_command") or not args.mrs_command:
            parser.parse_args(["mrs", "--help"])
            return 1
        if args.mrs_command == "list":
            return cmd_mrs_list(args)
        elif args.mrs_command == "view":
            return cmd_mrs_view(args)
    elif args.command == "pipelines":
        if not hasattr(args, "pipelines_command") or not args.pipelines_command:
            parser.parse_args(["pipelines", "--help"])
            return 1
        if args.pipelines_command == "list":
            return cmd_pipelines_list(args)
        elif args.pipelines_command == "view":
            return cmd_pipelines_view(args)
    elif args.command == "repos":
        if not hasattr(args, "repos_command") or not args.repos_command:
            parser.parse_args(["repos", "--help"])
            return 1
        if args.repos_command == "list":
            return cmd_repos_list(args)
        elif args.repos_command == "view":
            return cmd_repos_view(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
