#!/usr/bin/env python3
"""List resources from {{SKILL_NAME}}.

Usage:
    python skills/{{SERVICE_NAME}}/scripts/list.py
    python skills/{{SERVICE_NAME}}/scripts/list.py --limit 20
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from shared.http import get
from shared.output import format_json, format_table

# Update these constants for your skill
SERVICE_NAME = "{{SERVICE_NAME}}"
API_ENDPOINT = "api/v1/resources"


def list_resources(limit: int = 50) -> list[dict[str, Any]]:
    """List resources.

    Args:
        limit: Maximum number of results.

    Returns:
        List of resource dictionaries.
    """
    response = get(
        SERVICE_NAME,
        API_ENDPOINT,
        params={"limit": limit},
    )

    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        # Adjust based on actual API response structure
        return response.get("items", response.get("data", []))
    return []


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="List resources")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of results (default: 50)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    try:
        resources = list_resources(args.limit)

        if args.json:
            print(format_json(resources))
        else:
            # Adjust columns based on your resource structure
            print(
                format_table(
                    resources,
                    ["id", "name", "status"],
                    headers={"id": "ID", "name": "Name", "status": "Status"},
                )
            )

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
