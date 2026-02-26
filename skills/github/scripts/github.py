#!/usr/bin/env python3
"""GitHub wrapper skill for AI agents.

Wraps the gh CLI to produce markdown-formatted output for read/view commands.
Action commands (create, merge, close, comment) should use gh directly.

Usage:
    python github.py check
    python github.py issues list --repo OWNER/REPO
    python github.py issues view 123 --repo OWNER/REPO
    python github.py prs list --repo OWNER/REPO
    python github.py prs view 456 --repo OWNER/REPO
    python github.py prs checks 456 --repo OWNER/REPO
    python github.py prs status --repo OWNER/REPO
    python github.py runs list --repo OWNER/REPO
    python github.py runs view 123456 --repo OWNER/REPO
    python github.py repos list
    python github.py repos view OWNER/REPO
    python github.py search repos "machine learning"
    python github.py search issues "label:bug is:open"
    python github.py search prs "is:open review:required"

Requirements:
    gh CLI (https://cli.github.com/)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any

# ============================================================================
# CONSTANTS — JSON field lists per entity type
# ============================================================================

ISSUE_LIST_FIELDS = "number,title,state,author,assignees,labels,createdAt,updatedAt"
ISSUE_VIEW_FIELDS = (
    "number,title,state,body,author,assignees,labels,milestone,createdAt,updatedAt,comments,url"
)
PR_LIST_FIELDS = "number,title,state,author,assignees,labels,createdAt,updatedAt,isDraft"
PR_VIEW_FIELDS = (
    "number,title,state,body,author,assignees,labels,milestone,"
    "createdAt,updatedAt,comments,url,isDraft,mergeable,reviewDecision,"
    "additions,deletions,changedFiles,headRefName,baseRefName"
)
PR_STATUS_FIELDS = "number,title,state,headRefName,baseRefName,isDraft,reviewDecision,author,url"
PR_CHECKS_FIELDS = "name,status,conclusion,startedAt,completedAt,detailsUrl"
RUN_LIST_FIELDS = "databaseId,displayTitle,status,conclusion,event,createdAt,updatedAt,url"
RUN_VIEW_FIELDS = (
    "databaseId,displayTitle,status,conclusion,event,"
    "createdAt,updatedAt,url,workflowName,headBranch,headSha,jobs"
)
REPO_LIST_FIELDS = "name,owner,description,isPrivate,isFork,stargazerCount,updatedAt,url"
REPO_VIEW_FIELDS = (
    "name,owner,description,isPrivate,isFork,stargazerCount,"
    "forkCount,watchers,updatedAt,url,defaultBranchRef,homepageUrl,"
    "primaryLanguage,licenseInfo,isArchived"
)
SEARCH_REPOS_FIELDS = "fullName,description,isPrivate,stargazersCount,updatedAt,url"
SEARCH_ISSUES_FIELDS = (
    "repository,number,title,state,author,assignees,labels,createdAt,updatedAt,url"
)
SEARCH_PRS_FIELDS = (
    "repository,number,title,state,author,assignees,labels,createdAt,updatedAt,url,isDraft"
)


# ============================================================================
# gh CLI HELPER
# ============================================================================


def run_gh(args: list[str], json_fields: str | None = None) -> dict[str, Any] | list[Any] | str:
    """Run a gh CLI command and return parsed output.

    Args:
        args: Arguments to pass to gh (e.g., ["issue", "list"]).
        json_fields: Comma-separated field list for --json output.

    Returns:
        Parsed JSON data (dict or list), or raw string output.

    Raises:
        SystemExit: If gh command fails.
    """
    cmd = ["gh", *args]
    if json_fields:
        cmd.extend(["--json", json_fields])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    if json_fields and output:
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
# FORMAT FUNCTIONS — one per entity type (markdown output)
# ============================================================================


def format_issue_summary(issue: dict[str, Any]) -> str:
    """Format a GitHub issue for markdown display.

    Args:
        issue: Issue dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    number = issue.get("number", "?")
    title = issue.get("title", "(No title)")
    state = issue.get("state", "UNKNOWN")
    author = _get_login(issue.get("author"))
    assignees = _get_logins(issue.get("assignees", []))
    labels = _get_label_names(issue.get("labels", []))
    created = format_date(issue.get("createdAt"))

    lines = [
        f"### #{number}: {title}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if assignees:
        lines.append(f"- **Assignees:** {assignees}")
    if labels:
        lines.append(f"- **Labels:** {labels}")
    lines.append(f"- **Created:** {created}")

    body = issue.get("body")
    if body:
        lines.append(f"\n{body.strip()}")

    url = issue.get("url")
    if url:
        lines.append(f"\n- **URL:** {url}")

    return "\n".join(lines)


def format_issue_row(issue: dict[str, Any]) -> str:
    """Format a GitHub issue as a compact markdown entry for lists.

    Args:
        issue: Issue dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    number = issue.get("number", "?")
    title = issue.get("title", "(No title)")
    state = issue.get("state", "UNKNOWN")
    author = _get_login(issue.get("author"))
    labels = _get_label_names(issue.get("labels", []))
    created = format_date(issue.get("createdAt"))

    lines = [
        f"### #{number}: {title}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if labels:
        lines.append(f"- **Labels:** {labels}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


def format_pr_summary(pr: dict[str, Any]) -> str:
    """Format a GitHub pull request for markdown display.

    Args:
        pr: PR dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    number = pr.get("number", "?")
    title = pr.get("title", "(No title)")
    state = pr.get("state", "UNKNOWN")
    draft = " (Draft)" if pr.get("isDraft") else ""
    author = _get_login(pr.get("author"))
    assignees = _get_logins(pr.get("assignees", []))
    labels = _get_label_names(pr.get("labels", []))
    created = format_date(pr.get("createdAt"))

    lines = [
        f"### #{number}: {title}{draft}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if assignees:
        lines.append(f"- **Assignees:** {assignees}")
    if labels:
        lines.append(f"- **Labels:** {labels}")

    head = pr.get("headRefName")
    base = pr.get("baseRefName")
    if head and base:
        lines.append(f"- **Branch:** {head} → {base}")

    review = pr.get("reviewDecision")
    if review:
        lines.append(f"- **Review:** {review}")

    additions = pr.get("additions")
    deletions = pr.get("deletions")
    changed = pr.get("changedFiles")
    if additions is not None:
        lines.append(f"- **Changes:** +{additions} -{deletions} ({changed} files)")

    lines.append(f"- **Created:** {created}")

    body = pr.get("body")
    if body:
        lines.append(f"\n{body.strip()}")

    url = pr.get("url")
    if url:
        lines.append(f"\n- **URL:** {url}")

    return "\n".join(lines)


def format_pr_row(pr: dict[str, Any]) -> str:
    """Format a GitHub PR as a compact markdown entry for lists.

    Args:
        pr: PR dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    number = pr.get("number", "?")
    title = pr.get("title", "(No title)")
    state = pr.get("state", "UNKNOWN")
    draft = " (Draft)" if pr.get("isDraft") else ""
    author = _get_login(pr.get("author"))
    labels = _get_label_names(pr.get("labels", []))
    created = format_date(pr.get("createdAt"))

    lines = [
        f"### #{number}: {title}{draft}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if labels:
        lines.append(f"- **Labels:** {labels}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


def format_pr_status(data: dict[str, Any]) -> str:
    """Format gh pr status output as markdown.

    Args:
        data: Dictionary with 'currentBranch', 'createdBy', 'needsReview' keys.

    Returns:
        Markdown-formatted string.
    """
    lines = ["## PR Status"]

    current = data.get("currentBranch")
    lines.append("\n### Current Branch")
    if current:
        pr = current
        number = pr.get("number", "?")
        title = pr.get("title", "(No title)")
        state = pr.get("state", "UNKNOWN")
        draft = " (Draft)" if pr.get("isDraft") else ""
        review = pr.get("reviewDecision", "")
        url = pr.get("url", "")
        lines.append(f"- **#{number}: {title}**{draft}")
        line_parts = [f"  {state}"]
        if review:
            line_parts.append(f"Review: {review}")
        lines.append(" | ".join(line_parts))
        if url:
            lines.append(f"  {url}")
    else:
        lines.append("No PR for current branch")

    for section_key, section_title in [
        ("createdBy", "Created by You"),
        ("needsReview", "Requesting Your Review"),
    ]:
        prs = data.get(section_key, [])
        lines.append(f"\n### {section_title}")
        if not prs:
            lines.append("None")
        else:
            for pr in prs:
                number = pr.get("number", "?")
                title = pr.get("title", "(No title)")
                state = pr.get("state", "UNKNOWN")
                draft = " (Draft)" if pr.get("isDraft") else ""
                head = pr.get("headRefName", "")
                base = pr.get("baseRefName", "")
                review = pr.get("reviewDecision", "")
                branch = f" ({head} → {base})" if head and base else ""
                entry = f"- **#{number}: {title}**{draft}{branch}"
                parts = [f"  {state}"]
                if review:
                    parts.append(f"Review: {review}")
                lines.append(entry)
                lines.append(" | ".join(parts))

    return "\n".join(lines)


def format_check(check: dict[str, Any]) -> str:
    """Format a PR check/status for markdown display.

    Args:
        check: Check dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    name = check.get("name", "(Unknown)")
    status = check.get("status", "UNKNOWN")
    conclusion = check.get("conclusion", "")
    started = format_date(check.get("startedAt"))

    state = conclusion if conclusion else status
    return f"- **{name}:** {state} (started {started})"


def format_run_summary(run: dict[str, Any]) -> str:
    """Format a GitHub Actions run for markdown display.

    Args:
        run: Run dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    run_id = run.get("databaseId", "?")
    title = run.get("displayTitle", "(No title)")
    status = run.get("status", "UNKNOWN")
    conclusion = run.get("conclusion", "")
    event = run.get("event", "")
    created = format_date(run.get("createdAt"))

    state = f"{status}" if not conclusion else f"{conclusion}"

    lines = [
        f"### {title} (#{run_id})",
        f"- **Status:** {state}",
    ]
    if event:
        lines.append(f"- **Event:** {event}")
    lines.append(f"- **Created:** {created}")

    workflow = run.get("workflowName")
    if workflow:
        lines.append(f"- **Workflow:** {workflow}")

    branch = run.get("headBranch")
    if branch:
        lines.append(f"- **Branch:** {branch}")

    sha = run.get("headSha")
    if sha:
        lines.append(f"- **Commit:** {sha[:8]}")

    url = run.get("url")
    if url:
        lines.append(f"- **URL:** {url}")

    jobs = run.get("jobs", [])
    if jobs:
        lines.append("\n**Jobs:**")
        for job in jobs:
            job_name = job.get("name", "?")
            job_status = job.get("conclusion") or job.get("status", "?")
            lines.append(f"- **{job_name}:** {job_status}")

    return "\n".join(lines)


def format_run_row(run: dict[str, Any]) -> str:
    """Format a GitHub Actions run as a compact markdown entry for lists.

    Args:
        run: Run dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    run_id = run.get("databaseId", "?")
    title = run.get("displayTitle", "(No title)")
    status = run.get("status", "UNKNOWN")
    conclusion = run.get("conclusion", "")
    event = run.get("event", "")
    created = format_date(run.get("createdAt"))

    state = f"{status}" if not conclusion else f"{conclusion}"

    lines = [
        f"### {title} (#{run_id})",
        f"- **Status:** {state}",
    ]
    if event:
        lines.append(f"- **Event:** {event}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


def format_repo_summary(repo: dict[str, Any]) -> str:
    """Format a GitHub repository for markdown display.

    Args:
        repo: Repository dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    owner = repo.get("owner", {})
    owner_login = owner.get("login", "") if isinstance(owner, dict) else str(owner)
    name = repo.get("name", "(Unknown)")
    full_name = f"{owner_login}/{name}" if owner_login else name
    description = repo.get("description") or "(No description)"
    private = "Private" if repo.get("isPrivate") else "Public"
    stars = repo.get("stargazerCount", 0)
    forks = repo.get("forkCount", 0)
    updated = format_date(repo.get("updatedAt"))

    lines = [
        f"### {full_name}",
        f"- **Description:** {description}",
        f"- **Visibility:** {private}",
        f"- **Stars:** {stars}",
    ]

    if forks:
        lines.append(f"- **Forks:** {forks}")

    lang = repo.get("primaryLanguage")
    if lang:
        lang_name = lang.get("name", "") if isinstance(lang, dict) else str(lang)
        if lang_name:
            lines.append(f"- **Language:** {lang_name}")

    license_info = repo.get("licenseInfo")
    if license_info:
        lic_name = license_info.get("name", "") if isinstance(license_info, dict) else ""
        if lic_name:
            lines.append(f"- **License:** {lic_name}")

    default_branch = repo.get("defaultBranchRef")
    if default_branch:
        branch_name = default_branch.get("name", "") if isinstance(default_branch, dict) else ""
        if branch_name:
            lines.append(f"- **Default Branch:** {branch_name}")

    lines.append(f"- **Updated:** {updated}")

    url = repo.get("url")
    if url:
        lines.append(f"- **URL:** {url}")

    return "\n".join(lines)


def format_repo_row(repo: dict[str, Any]) -> str:
    """Format a GitHub repository as a compact markdown entry for lists.

    Args:
        repo: Repository dictionary from gh --json output.

    Returns:
        Markdown-formatted string.
    """
    owner = repo.get("owner", {})
    owner_login = owner.get("login", "") if isinstance(owner, dict) else str(owner)
    name = repo.get("name", "(Unknown)")
    full_name = f"{owner_login}/{name}" if owner_login else name
    description = repo.get("description") or "(No description)"
    private = "Private" if repo.get("isPrivate") else "Public"
    stars = repo.get("stargazerCount", 0)

    lines = [
        f"### {full_name}",
        f"- **Description:** {description}",
        f"- **Visibility:** {private}",
        f"- **Stars:** {stars}",
    ]
    return "\n".join(lines)


def format_search_repo(repo: dict[str, Any]) -> str:
    """Format a search result repository for markdown display.

    Args:
        repo: Search result dictionary from gh search --json output.

    Returns:
        Markdown-formatted string.
    """
    full_name = repo.get("fullName", "(Unknown)")
    description = repo.get("description") or "(No description)"
    private = "Private" if repo.get("isPrivate") else "Public"
    stars = repo.get("stargazersCount", 0)
    updated = format_date(repo.get("updatedAt"))

    lines = [
        f"### {full_name}",
        f"- **Description:** {description}",
        f"- **Visibility:** {private}",
        f"- **Stars:** {stars}",
        f"- **Updated:** {updated}",
    ]

    url = repo.get("url")
    if url:
        lines.append(f"- **URL:** {url}")

    return "\n".join(lines)


def format_search_issue(issue: dict[str, Any]) -> str:
    """Format a search result issue for markdown display.

    Args:
        issue: Search result dictionary from gh search --json output.

    Returns:
        Markdown-formatted string.
    """
    repo = issue.get("repository", {})
    repo_name = repo.get("nameWithOwner", "") if isinstance(repo, dict) else str(repo)
    number = issue.get("number", "?")
    title = issue.get("title", "(No title)")
    state = issue.get("state", "UNKNOWN")
    author = _get_login(issue.get("author"))
    labels = _get_label_names(issue.get("labels", []))
    created = format_date(issue.get("createdAt"))

    prefix = f"{repo_name}#" if repo_name else "#"
    lines = [
        f"### {prefix}{number}: {title}",
        f"- **State:** {state}",
        f"- **Author:** {author}",
    ]
    if labels:
        lines.append(f"- **Labels:** {labels}")
    lines.append(f"- **Created:** {created}")
    return "\n".join(lines)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_login(author: dict[str, Any] | None) -> str:
    """Extract login name from an author/user dict.

    Args:
        author: User dictionary with 'login' key.

    Returns:
        Login string or "Unknown".
    """
    if not author:
        return "Unknown"
    if isinstance(author, dict):
        return author.get("login", "Unknown")
    return str(author)


def _get_logins(users: list[dict[str, Any]]) -> str:
    """Extract comma-separated login names from a list of user dicts.

    Args:
        users: List of user dictionaries.

    Returns:
        Comma-separated login names, or empty string if none.
    """
    if not users:
        return ""
    names = []
    for u in users:
        if isinstance(u, dict):
            names.append(u.get("login", "?"))
        else:
            names.append(str(u))
    return ", ".join(names)


def _get_label_names(labels: list[dict[str, Any]]) -> str:
    """Extract comma-separated label names from a list of label dicts.

    Args:
        labels: List of label dictionaries.

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
# COMMAND HANDLERS — one per subcommand, return exit code
# ============================================================================


def cmd_check(_args: argparse.Namespace) -> int:
    """Verify gh CLI is installed and authenticated.

    Args:
        _args: Parsed arguments (unused).

    Returns:
        Exit code (0 success, 1 error).
    """
    if not shutil.which("gh"):
        print("Error: gh CLI not found. Install from https://cli.github.com/", file=sys.stderr)
        return 1

    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: gh CLI not authenticated.", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        print("\nRun: gh auth login", file=sys.stderr)
        return 1

    print("✓ gh CLI is installed and authenticated")
    # Show auth details (stderr from gh auth status contains the info)
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
    gh_args = ["issue", "list"]
    if args.repo:
        gh_args.extend(["-R", args.repo])
    gh_args.extend(["--limit", str(args.limit)])

    if args.json:
        data = run_gh(gh_args, ISSUE_LIST_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, ISSUE_LIST_FIELDS)
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
    gh_args = ["issue", "view", str(args.number)]
    if args.repo:
        gh_args.extend(["-R", args.repo])

    if args.json:
        data = run_gh(gh_args, ISSUE_VIEW_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, ISSUE_VIEW_FIELDS)
        if isinstance(data, dict):
            print(format_issue_summary(data))
    return 0


def cmd_prs_list(args: argparse.Namespace) -> int:
    """List pull requests for a repository.

    Args:
        args: Parsed arguments with repo, limit, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["pr", "list"]
    if args.repo:
        gh_args.extend(["-R", args.repo])
    gh_args.extend(["--limit", str(args.limit)])

    if args.json:
        data = run_gh(gh_args, PR_LIST_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, PR_LIST_FIELDS)
        items = data if isinstance(data, list) else []
        if not items:
            print("No pull requests found")
        else:
            print(f"## Pull Requests\n\nFound {len(items)} PR(s):\n")
            print("\n\n".join(format_pr_row(pr) for pr in items))
    return 0


def cmd_prs_view(args: argparse.Namespace) -> int:
    """View a single pull request.

    Args:
        args: Parsed arguments with PR number, repo, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["pr", "view", str(args.number)]
    if args.repo:
        gh_args.extend(["-R", args.repo])

    if args.json:
        data = run_gh(gh_args, PR_VIEW_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, PR_VIEW_FIELDS)
        if isinstance(data, dict):
            print(format_pr_summary(data))
    return 0


def cmd_prs_checks(args: argparse.Namespace) -> int:
    """View CI checks for a pull request.

    Args:
        args: Parsed arguments with PR number, repo, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["pr", "checks", str(args.number)]
    if args.repo:
        gh_args.extend(["-R", args.repo])

    if args.json:
        data = run_gh(gh_args, PR_CHECKS_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, PR_CHECKS_FIELDS)
        items = data if isinstance(data, list) else []
        if not items:
            print("No checks found")
        else:
            print(f"## PR #{args.number} Checks\n")
            print("\n".join(format_check(c) for c in items))
    return 0


def cmd_prs_status(args: argparse.Namespace) -> int:
    """Show status of relevant pull requests.

    Args:
        args: Parsed arguments with repo, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["pr", "status"]
    if args.repo:
        gh_args.extend(["-R", args.repo])

    if args.json:
        data = run_gh(gh_args, PR_STATUS_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, PR_STATUS_FIELDS)
        if isinstance(data, dict):
            print(format_pr_status(data))
    return 0


def cmd_runs_list(args: argparse.Namespace) -> int:
    """List workflow runs for a repository.

    Args:
        args: Parsed arguments with repo, limit, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["run", "list"]
    if args.repo:
        gh_args.extend(["-R", args.repo])
    gh_args.extend(["--limit", str(args.limit)])

    if args.json:
        data = run_gh(gh_args, RUN_LIST_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, RUN_LIST_FIELDS)
        items = data if isinstance(data, list) else []
        if not items:
            print("No workflow runs found")
        else:
            print(f"## Workflow Runs\n\nFound {len(items)} run(s):\n")
            print("\n\n".join(format_run_row(r) for r in items))
    return 0


def cmd_runs_view(args: argparse.Namespace) -> int:
    """View a single workflow run.

    Args:
        args: Parsed arguments with run ID, repo, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["run", "view", str(args.run_id)]
    if args.repo:
        gh_args.extend(["-R", args.repo])

    if args.json:
        data = run_gh(gh_args, RUN_VIEW_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, RUN_VIEW_FIELDS)
        if isinstance(data, dict):
            print(format_run_summary(data))
    return 0


def cmd_repos_list(args: argparse.Namespace) -> int:
    """List repositories for the authenticated user.

    Args:
        args: Parsed arguments with limit, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["repo", "list"]
    gh_args.extend(["--limit", str(args.limit)])

    if args.json:
        data = run_gh(gh_args, REPO_LIST_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, REPO_LIST_FIELDS)
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
    gh_args = ["repo", "view", args.repo]

    if args.json:
        data = run_gh(gh_args, REPO_VIEW_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, REPO_VIEW_FIELDS)
        if isinstance(data, dict):
            print(format_repo_summary(data))
    return 0


def cmd_search_repos(args: argparse.Namespace) -> int:
    """Search repositories.

    Args:
        args: Parsed arguments with query, limit, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["search", "repos", args.query, "--limit", str(args.limit)]

    if args.json:
        data = run_gh(gh_args, SEARCH_REPOS_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, SEARCH_REPOS_FIELDS)
        items = data if isinstance(data, list) else []
        if not items:
            print("No repositories found")
        else:
            print(f"## Search Results\n\nFound {len(items)} repository(ies):\n")
            print("\n\n".join(format_search_repo(r) for r in items))
    return 0


def cmd_search_issues(args: argparse.Namespace) -> int:
    """Search issues.

    Args:
        args: Parsed arguments with query, limit, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["search", "issues", args.query, "--limit", str(args.limit)]

    if args.json:
        data = run_gh(gh_args, SEARCH_ISSUES_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, SEARCH_ISSUES_FIELDS)
        items = data if isinstance(data, list) else []
        if not items:
            print("No issues found")
        else:
            print(f"## Search Results\n\nFound {len(items)} issue(s):\n")
            print("\n\n".join(format_search_issue(i) for i in items))
    return 0


def cmd_search_prs(args: argparse.Namespace) -> int:
    """Search pull requests.

    Args:
        args: Parsed arguments with query, limit, json flags.

    Returns:
        Exit code.
    """
    gh_args = ["search", "prs", args.query, "--limit", str(args.limit)]

    if args.json:
        data = run_gh(gh_args, SEARCH_PRS_FIELDS)
        print(json.dumps(data, indent=2))
    else:
        data = run_gh(gh_args, SEARCH_PRS_FIELDS)
        items = data if isinstance(data, list) else []
        if not items:
            print("No pull requests found")
        else:
            print(f"## Search Results\n\nFound {len(items)} PR(s):\n")
            print("\n\n".join(format_search_issue(i) for i in items))
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
        description="GitHub wrapper for AI agents — markdown-formatted gh output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # check
    subparsers.add_parser("check", help="Verify gh CLI is installed and authenticated")

    # issues
    issues_parser = subparsers.add_parser("issues", help="Issue operations")
    issues_sub = issues_parser.add_subparsers(dest="issues_command")

    issues_list = issues_sub.add_parser("list", help="List issues")
    issues_list.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    issues_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    issues_list.add_argument("--json", action="store_true", help="Output raw JSON")

    issues_view = issues_sub.add_parser("view", help="View issue details")
    issues_view.add_argument("number", type=int, help="Issue number")
    issues_view.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    issues_view.add_argument("--json", action="store_true", help="Output raw JSON")

    # prs
    prs_parser = subparsers.add_parser("prs", help="Pull request operations")
    prs_sub = prs_parser.add_subparsers(dest="prs_command")

    prs_list = prs_sub.add_parser("list", help="List pull requests")
    prs_list.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    prs_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    prs_list.add_argument("--json", action="store_true", help="Output raw JSON")

    prs_view = prs_sub.add_parser("view", help="View PR details")
    prs_view.add_argument("number", type=int, help="PR number")
    prs_view.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    prs_view.add_argument("--json", action="store_true", help="Output raw JSON")

    prs_checks = prs_sub.add_parser("checks", help="View PR checks")
    prs_checks.add_argument("number", type=int, help="PR number")
    prs_checks.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    prs_checks.add_argument("--json", action="store_true", help="Output raw JSON")

    prs_status = prs_sub.add_parser("status", help="Show status of relevant PRs")
    prs_status.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    prs_status.add_argument("--json", action="store_true", help="Output raw JSON")

    # runs
    runs_parser = subparsers.add_parser("runs", help="Workflow run operations")
    runs_sub = runs_parser.add_subparsers(dest="runs_command")

    runs_list = runs_sub.add_parser("list", help="List workflow runs")
    runs_list.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    runs_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    runs_list.add_argument("--json", action="store_true", help="Output raw JSON")

    runs_view = runs_sub.add_parser("view", help="View workflow run details")
    runs_view.add_argument("run_id", type=int, help="Run ID")
    runs_view.add_argument("--repo", "-R", help="Repository (OWNER/REPO)")
    runs_view.add_argument("--json", action="store_true", help="Output raw JSON")

    # repos
    repos_parser = subparsers.add_parser("repos", help="Repository operations")
    repos_sub = repos_parser.add_subparsers(dest="repos_command")

    repos_list = repos_sub.add_parser("list", help="List repositories")
    repos_list.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    repos_list.add_argument("--json", action="store_true", help="Output raw JSON")

    repos_view = repos_sub.add_parser("view", help="View repository details")
    repos_view.add_argument("repo", help="Repository (OWNER/REPO)")
    repos_view.add_argument("--json", action="store_true", help="Output raw JSON")

    # search
    search_parser = subparsers.add_parser("search", help="Search operations")
    search_sub = search_parser.add_subparsers(dest="search_command")

    search_repos = search_sub.add_parser("repos", help="Search repositories")
    search_repos.add_argument("query", help="Search query")
    search_repos.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    search_repos.add_argument("--json", action="store_true", help="Output raw JSON")

    search_issues = search_sub.add_parser("issues", help="Search issues")
    search_issues.add_argument("query", help="Search query")
    search_issues.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    search_issues.add_argument("--json", action="store_true", help="Output raw JSON")

    search_prs = search_sub.add_parser("prs", help="Search pull requests")
    search_prs.add_argument("query", help="Search query")
    search_prs.add_argument("--limit", type=int, default=30, help="Max results (default 30)")
    search_prs.add_argument("--json", action="store_true", help="Output raw JSON")

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
    elif args.command == "prs":
        if not hasattr(args, "prs_command") or not args.prs_command:
            parser.parse_args(["prs", "--help"])
            return 1
        if args.prs_command == "list":
            return cmd_prs_list(args)
        elif args.prs_command == "view":
            return cmd_prs_view(args)
        elif args.prs_command == "checks":
            return cmd_prs_checks(args)
        elif args.prs_command == "status":
            return cmd_prs_status(args)
    elif args.command == "runs":
        if not hasattr(args, "runs_command") or not args.runs_command:
            parser.parse_args(["runs", "--help"])
            return 1
        if args.runs_command == "list":
            return cmd_runs_list(args)
        elif args.runs_command == "view":
            return cmd_runs_view(args)
    elif args.command == "repos":
        if not hasattr(args, "repos_command") or not args.repos_command:
            parser.parse_args(["repos", "--help"])
            return 1
        if args.repos_command == "list":
            return cmd_repos_list(args)
        elif args.repos_command == "view":
            return cmd_repos_view(args)
    elif args.command == "search":
        if not hasattr(args, "search_command") or not args.search_command:
            parser.parse_args(["search", "--help"])
            return 1
        if args.search_command == "repos":
            return cmd_search_repos(args)
        elif args.search_command == "issues":
            return cmd_search_issues(args)
        elif args.search_command == "prs":
            return cmd_search_prs(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
