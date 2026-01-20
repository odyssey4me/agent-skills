#!/usr/bin/env python3
"""Get a specific resource from {{SKILL_NAME}}.

Usage:
    python skills/{{SERVICE_NAME}}/scripts/get.py RESOURCE_ID
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from shared.http import get as http_get
from shared.output import format_json

# Update these constants for your skill
SERVICE_NAME = "{{SERVICE_NAME}}"
API_ENDPOINT = "api/v1/resources"


def get_resource(resource_id: str) -> dict[str, Any]:
    """Get a resource by ID.

    Args:
        resource_id: The resource identifier.

    Returns:
        Resource dictionary.
    """
    response = http_get(SERVICE_NAME, f"{API_ENDPOINT}/{resource_id}")
    if isinstance(response, dict):
        return response
    return {}


def format_resource(resource: dict[str, Any]) -> str:
    """Format a resource for display.

    Args:
        resource: Resource dictionary.

    Returns:
        Formatted string.
    """
    # Adjust based on your resource structure
    return f"""ID: {resource.get("id", "N/A")}
Name: {resource.get("name", "N/A")}
Status: {resource.get("status", "N/A")}
Created: {resource.get("created", "N/A")}"""


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Get resource details")
    parser.add_argument("resource_id", help="Resource ID")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        resource = get_resource(args.resource_id)

        if args.json:
            print(format_json(resource))
        else:
            print(format_resource(resource))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
