#!/usr/bin/env python3
"""Search for Jira issues using JQL.

Usage:
    python skills/jira/scripts/search.py "project = DEMO"
    python skills/jira/scripts/search.py "assignee = currentUser()" --max-results 20
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from shared.http import get
from shared.output import format_issues_list, format_json
from skills.jira.api import api_path

DEFAULT_FIELDS = [
    "summary",
    "status",
    "assignee",
    "priority",
    "created",
    "updated",
]


def search_issues(
    jql: str,
    max_results: int = 50,
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search for issues using JQL.

    Args:
        jql: JQL query string.
        max_results: Maximum number of results to return.
        fields: List of fields to include in response.

    Returns:
        List of issue dictionaries.
    """
    fields = fields or DEFAULT_FIELDS

    response = get(
        "jira",
        api_path("search"),
        params={
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields),
        },
    )

    if isinstance(response, dict):
        return response.get("issues", [])
    return []


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Search for Jira issues using JQL")
    parser.add_argument("jql", help="JQL query string")
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of results (default: 50)",
    )
    parser.add_argument(
        "--fields",
        help="Comma-separated list of fields to include",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    fields = args.fields.split(",") if args.fields else None

    try:
        issues = search_issues(args.jql, args.max_results, fields)

        if args.json:
            print(format_json(issues))
        else:
            print(format_issues_list(issues))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
