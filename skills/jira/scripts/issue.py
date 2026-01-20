#!/usr/bin/env python3
"""Get, create, or update Jira issues.

Usage:
    python skills/jira/scripts/issue.py get DEMO-123
    python skills/jira/scripts/issue.py create --project DEMO --type Task --summary "New task"
    python skills/jira/scripts/issue.py update DEMO-123 --summary "Updated summary"
    python skills/jira/scripts/issue.py comment DEMO-123 "Comment text"
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from shared.http import get, post, put
from shared.output import format_issue, format_json
from skills.jira.api import api_path, format_rich_text


def get_issue(issue_key: str) -> dict[str, Any]:
    """Get an issue by key.

    Args:
        issue_key: The issue key (e.g., DEMO-123).

    Returns:
        Issue dictionary.
    """
    response = get("jira", api_path(f"issue/{issue_key}"))
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


def add_comment(issue_key: str, body: str) -> dict[str, Any]:
    """Add a comment to an issue.

    Args:
        issue_key: The issue key.
        body: Comment text.

    Returns:
        Created comment dictionary.
    """
    comment_body = {"body": format_rich_text(body)}

    response = post("jira", api_path(f"issue/{issue_key}/comment"), comment_body)
    if isinstance(response, dict):
        return response
    return {}


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage Jira issues")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Get command
    get_parser = subparsers.add_parser("get", help="Get issue details")
    get_parser.add_argument("issue_key", help="Issue key (e.g., DEMO-123)")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new issue")
    create_parser.add_argument("--project", required=True, help="Project key")
    create_parser.add_argument("--type", required=True, dest="issue_type", help="Issue type")
    create_parser.add_argument("--summary", required=True, help="Issue summary")
    create_parser.add_argument("--description", help="Issue description")
    create_parser.add_argument("--priority", help="Priority name")
    create_parser.add_argument("--labels", help="Comma-separated labels")
    create_parser.add_argument("--assignee", help="Assignee account ID")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update existing issue")
    update_parser.add_argument("issue_key", help="Issue key")
    update_parser.add_argument("--summary", help="New summary")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument("--priority", help="New priority")
    update_parser.add_argument("--labels", help="New labels (comma-separated)")
    update_parser.add_argument("--assignee", help="New assignee account ID")

    # Comment command
    comment_parser = subparsers.add_parser("comment", help="Add comment to issue")
    comment_parser.add_argument("issue_key", help="Issue key")
    comment_parser.add_argument("body", help="Comment text")

    args = parser.parse_args()

    try:
        if args.command == "get":
            issue = get_issue(args.issue_key)
            if args.json:
                print(format_json(issue))
            else:
                print(format_issue(issue))

        elif args.command == "create":
            labels = args.labels.split(",") if args.labels else None
            issue = create_issue(
                project=args.project,
                issue_type=args.issue_type,
                summary=args.summary,
                description=args.description,
                priority=args.priority,
                labels=labels,
                assignee=args.assignee,
            )
            if args.json:
                print(format_json(issue))
            else:
                print(f"Created issue: {issue.get('key', 'N/A')}")

        elif args.command == "update":
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

        elif args.command == "comment":
            add_comment(args.issue_key, args.body)
            print(f"Added comment to {args.issue_key}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
