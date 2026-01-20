"""Tests for shared output utilities."""

from __future__ import annotations

import json

from shared.output import (
    _truncate,
    format_issue,
    format_issues_list,
    format_json,
    format_table,
)


class TestFormatJson:
    """Tests for format_json function."""

    def test_format_json_dict(self):
        """Test formatting a dictionary."""
        data = {"key": "value", "number": 42}
        result = format_json(data)

        parsed = json.loads(result)
        assert parsed == data

    def test_format_json_list(self):
        """Test formatting a list."""
        data = [1, 2, 3]
        result = format_json(data)

        parsed = json.loads(result)
        assert parsed == data

    def test_format_json_custom_indent(self):
        """Test custom indentation."""
        data = {"key": "value"}
        result = format_json(data, indent=4)

        assert "    " in result


class TestFormatTable:
    """Tests for format_table function."""

    def test_format_table_basic(self):
        """Test basic table formatting."""
        rows = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ]
        result = format_table(rows, ["id", "name"])

        assert "id" in result
        assert "name" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_format_table_with_headers(self):
        """Test table with custom headers."""
        rows = [{"id": "1", "name": "Test"}]
        result = format_table(rows, ["id", "name"], headers={"id": "ID", "name": "Name"})

        assert "ID" in result
        assert "Name" in result

    def test_format_table_empty(self):
        """Test formatting empty table."""
        result = format_table([], ["id", "name"])

        assert result == "No data"

    def test_format_table_missing_values(self):
        """Test table with missing values."""
        rows = [{"id": "1"}]  # Missing 'name'
        result = format_table(rows, ["id", "name"])

        assert "1" in result

    def test_format_table_truncation(self):
        """Test table value truncation."""
        rows = [{"name": "A" * 100}]
        result = format_table(rows, ["name"], max_width=20)

        assert "..." in result


class TestTruncate:
    """Tests for _truncate function."""

    def test_truncate_short_text(self):
        """Test truncation of short text."""
        result = _truncate("short", 10)
        assert result == "short"

    def test_truncate_long_text(self):
        """Test truncation of long text."""
        result = _truncate("this is a long text", 10)
        assert result == "this is..."
        assert len(result) == 10

    def test_truncate_exact_length(self):
        """Test text at exact max length."""
        result = _truncate("exact", 5)
        assert result == "exact"


class TestFormatIssue:
    """Tests for format_issue function."""

    def test_format_issue_basic(self, sample_jira_issue):
        """Test formatting a Jira issue."""
        result = format_issue(sample_jira_issue)

        assert "DEMO-123" in result
        assert "Test issue summary" in result
        assert "Open" in result
        assert "Test User" in result
        assert "Medium" in result

    def test_format_issue_unassigned(self):
        """Test formatting issue with no assignee."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test",
                "status": {"name": "Open"},
                "assignee": None,
                "priority": {"name": "High"},
            },
        }
        result = format_issue(issue)

        assert "Unassigned" in result

    def test_format_issue_missing_fields(self):
        """Test formatting issue with missing fields."""
        issue = {"key": "TEST-1", "fields": {}}
        result = format_issue(issue)

        assert "TEST-1" in result


class TestFormatIssuesList:
    """Tests for format_issues_list function."""

    def test_format_issues_list_basic(self, sample_jira_issue):
        """Test formatting a list of issues."""
        issues = [sample_jira_issue]
        result = format_issues_list(issues)

        assert "DEMO-123" in result
        assert "Test issue summary" in result

    def test_format_issues_list_empty(self):
        """Test formatting empty issues list."""
        result = format_issues_list([])

        assert result == "No issues found"

    def test_format_issues_list_multiple(self, sample_jira_issue):
        """Test formatting multiple issues."""
        issue2 = sample_jira_issue.copy()
        issue2["key"] = "DEMO-456"
        issue2["fields"] = sample_jira_issue["fields"].copy()
        issue2["fields"]["summary"] = "Another issue"

        result = format_issues_list([sample_jira_issue, issue2])

        assert "DEMO-123" in result
        assert "DEMO-456" in result
