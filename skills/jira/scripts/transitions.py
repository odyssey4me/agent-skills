#!/usr/bin/env python3
"""Manage Jira issue workflow transitions.

Usage:
    python skills/jira/scripts/transitions.py list DEMO-123
    python skills/jira/scripts/transitions.py do DEMO-123 "In Progress"
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from shared.http import get, post
from shared.output import format_json, format_table
from skills.jira.api import api_path, format_rich_text


def get_transitions(issue_key: str) -> list[dict[str, Any]]:
    """Get available transitions for an issue.

    Args:
        issue_key: The issue key.

    Returns:
        List of transition dictionaries.
    """
    response = get("jira", api_path(f"issue/{issue_key}/transitions"))
    if isinstance(response, dict):
        return response.get("transitions", [])
    return []


def do_transition(
    issue_key: str,
    transition_name: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """Transition an issue to a new status.

    Args:
        issue_key: The issue key.
        transition_name: Name of the transition to perform.
        comment: Optional comment to add.

    Returns:
        Response dictionary (empty on success).
    """
    # Get available transitions
    transitions = get_transitions(issue_key)

    # Find matching transition (case-insensitive)
    transition_id = None
    for t in transitions:
        if t.get("name", "").lower() == transition_name.lower():
            transition_id = t.get("id")
            break

    if not transition_id:
        available = [t.get("name") for t in transitions]
        raise ValueError(
            f"Transition '{transition_name}' not available. Available: {', '.join(available)}"
        )

    data: dict[str, Any] = {"transition": {"id": transition_id}}

    if comment:
        data["update"] = {
            "comment": [
                {
                    "add": {
                        "body": format_rich_text(comment)
                    }
                }
            ]
        }

    response = post("jira", api_path(f"issue/{issue_key}/transitions"), data)
    if isinstance(response, dict):
        return response
    return {}


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage issue transitions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List available transitions")
    list_parser.add_argument("issue_key", help="Issue key")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Do command
    do_parser = subparsers.add_parser("do", help="Perform a transition")
    do_parser.add_argument("issue_key", help="Issue key")
    do_parser.add_argument("transition", help="Transition name")
    do_parser.add_argument("--comment", help="Comment to add with transition")

    args = parser.parse_args()

    try:
        if args.command == "list":
            transitions = get_transitions(args.issue_key)

            if args.json:
                print(format_json(transitions))
            else:
                rows = [
                    {"id": t.get("id"), "name": t.get("name"), "to": t.get("to", {}).get("name")}
                    for t in transitions
                ]
                print(
                    format_table(
                        rows,
                        ["id", "name", "to"],
                        headers={"id": "ID", "name": "Transition", "to": "To Status"},
                    )
                )

        elif args.command == "do":
            do_transition(args.issue_key, args.transition, args.comment)
            print(f"Transitioned {args.issue_key} to '{args.transition}'")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
