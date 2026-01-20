#!/usr/bin/env python3
"""Create a new resource in {{SKILL_NAME}}.

Usage:
    python skills/{{SERVICE_NAME}}/scripts/create.py --name "New Resource"
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from shared.http import post
from shared.output import format_json

# Update these constants for your skill
SERVICE_NAME = "{{SERVICE_NAME}}"
API_ENDPOINT = "api/v1/resources"


def create_resource(
    name: str,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a new resource.

    Args:
        name: Resource name.
        description: Resource description.

    Returns:
        Created resource dictionary.
    """
    data: dict[str, Any] = {"name": name}

    if description:
        data["description"] = description

    response = post(SERVICE_NAME, API_ENDPOINT, data)
    if isinstance(response, dict):
        return response
    return {}


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create a new resource")
    parser.add_argument("--name", required=True, help="Resource name")
    parser.add_argument("--description", help="Resource description")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        resource = create_resource(args.name, args.description)

        if args.json:
            print(format_json(resource))
        else:
            print(f"Created resource: {resource.get('id', 'N/A')}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
