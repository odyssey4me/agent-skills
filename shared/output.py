"""Output formatting utilities for consistent display."""

from __future__ import annotations

import json
from typing import Any


def format_json(data: Any, *, indent: int = 2) -> str:
    """Format data as JSON string.

    Args:
        data: Data to format.
        indent: Indentation level.

    Returns:
        Formatted JSON string.
    """
    return json.dumps(data, indent=indent, default=str)


def format_table(
    rows: list[dict[str, Any]],
    columns: list[str],
    *,
    headers: dict[str, str] | None = None,
    max_width: int = 50,
) -> str:
    """Format data as a text table.

    Args:
        rows: List of dictionaries containing row data.
        columns: List of column keys to display.
        headers: Optional mapping of column keys to display headers.
        max_width: Maximum width for any column.

    Returns:
        Formatted table string.
    """
    if not rows:
        return "No data"

    headers = headers or {}

    # Calculate column widths
    widths: dict[str, int] = {}
    for col in columns:
        header = headers.get(col, col)
        max_val_width = max(len(_truncate(str(row.get(col, "")), max_width)) for row in rows)
        widths[col] = min(max(len(header), max_val_width), max_width)

    # Build header row
    header_parts = []
    for col in columns:
        header = headers.get(col, col)
        header_parts.append(header.ljust(widths[col]))
    header_line = " | ".join(header_parts)

    # Build separator
    separator = "-+-".join("-" * widths[col] for col in columns)

    # Build data rows
    data_lines = []
    for row in rows:
        parts = []
        for col in columns:
            value = _truncate(str(row.get(col, "")), widths[col])
            parts.append(value.ljust(widths[col]))
        data_lines.append(" | ".join(parts))

    return "\n".join([header_line, separator, *data_lines])


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_issue(issue: dict[str, Any]) -> str:
    """Format a Jira issue for display.

    Args:
        issue: Jira issue dictionary.

    Returns:
        Formatted issue string.
    """
    fields = issue.get("fields", {})
    key = issue.get("key", "N/A")
    summary = fields.get("summary", "No summary")
    status = fields.get("status", {}).get("name", "Unknown")
    assignee = fields.get("assignee", {})
    assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
    priority = fields.get("priority", {})
    priority_name = priority.get("name", "None") if priority else "None"

    return f"""Issue: {key}
Summary: {summary}
Status: {status}
Assignee: {assignee_name}
Priority: {priority_name}"""


def format_issues_list(issues: list[dict[str, Any]]) -> str:
    """Format a list of Jira issues for display.

    Args:
        issues: List of Jira issue dictionaries.

    Returns:
        Formatted table string.
    """
    if not issues:
        return "No issues found"

    rows = []
    for issue in issues:
        fields = issue.get("fields", {})
        assignee = fields.get("assignee", {})
        rows.append(
            {
                "key": issue.get("key", "N/A"),
                "summary": fields.get("summary", "No summary"),
                "status": fields.get("status", {}).get("name", "Unknown"),
                "assignee": assignee.get("displayName", "Unassigned") if assignee else "Unassigned",
            }
        )

    return format_table(
        rows,
        ["key", "summary", "status", "assignee"],
        headers={"key": "Key", "summary": "Summary", "status": "Status", "assignee": "Assignee"},
    )
