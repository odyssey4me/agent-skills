"""Tests for gerrit.py skill."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest

from skills.gerrit.scripts.gerrit import (
    _get_owner,
    _get_ssh_cmd,
    _read_gitreview,
    build_parser,
    cmd_changes_list,
    cmd_changes_search,
    cmd_changes_view,
    cmd_check,
    cmd_projects_list,
    format_change_row,
    format_change_summary,
    format_project_row,
    format_timestamp,
    run_gerrit_query,
)

# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestHelpers:
    """Tests for helper functions."""

    def test_format_timestamp_valid(self):
        """Test formatting valid Unix timestamp."""
        # 2024-01-15 10:30:00 UTC = 1705314600
        result = format_timestamp(1705314600)
        assert result == "2024-01-15 10:30"

    def test_format_timestamp_none(self):
        """Test formatting None timestamp."""
        assert format_timestamp(None) == "N/A"

    def test_format_timestamp_zero(self):
        """Test formatting zero timestamp."""
        assert format_timestamp(0) == "N/A"

    def test_get_owner_dict_username(self):
        """Test extracting owner with username."""
        assert _get_owner({"username": "alice"}) == "alice"

    def test_get_owner_dict_name(self):
        """Test extracting owner with name (no username)."""
        assert _get_owner({"name": "Alice Smith"}) == "Alice Smith"

    def test_get_owner_none(self):
        """Test extracting owner from None."""
        assert _get_owner(None) == "Unknown"

    def test_get_owner_empty(self):
        """Test extracting owner from empty dict."""
        assert _get_owner({}) == "Unknown"

    def test_get_ssh_cmd_basic(self):
        """Test building SSH command without username."""
        cmd = _get_ssh_cmd("review.example.com", "29418")
        assert cmd == ["ssh", "-p", "29418", "review.example.com"]

    def test_get_ssh_cmd_with_username(self):
        """Test building SSH command with username."""
        cmd = _get_ssh_cmd("review.example.com", "29418", "alice")
        assert cmd == ["ssh", "-p", "29418", "alice@review.example.com"]

    def test_read_gitreview_missing(self, tmp_path):
        """Test reading non-existent .gitreview."""
        result = _read_gitreview(str(tmp_path / ".gitreview"))
        assert result["host"] == ""
        assert result["port"] == "29418"

    def test_read_gitreview_valid(self, tmp_path):
        """Test reading valid .gitreview file."""
        gitreview = tmp_path / ".gitreview"
        gitreview.write_text("[gerrit]\nhost=review.example.com\nport=29419\nproject=myproject\n")

        result = _read_gitreview(str(gitreview))
        assert result["host"] == "review.example.com"
        assert result["port"] == "29419"
        assert result["project"] == "myproject"


# ============================================================================
# RUN_GERRIT_QUERY TESTS
# ============================================================================


class TestRunGerritQuery:
    """Tests for run_gerrit_query helper."""

    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_query_success(self, mock_run):
        """Test successful query with multiple results."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=(
                '{"number":1,"subject":"Fix bug","status":"NEW"}\n'
                '{"number":2,"subject":"Add feature","status":"NEW"}\n'
                '{"type":"stats","rowCount":2}\n'
            ),
            stderr="",
        )

        results = run_gerrit_query("review.example.com", "status:open")

        assert len(results) == 2
        assert results[0]["number"] == 1
        assert results[1]["number"] == 2

    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_query_empty(self, mock_run):
        """Test query with no results."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"type":"stats","rowCount":0}\n',
            stderr="",
        )

        results = run_gerrit_query("review.example.com", "status:open")

        assert results == []

    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_query_error(self, mock_run):
        """Test query with SSH error."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Connection refused",
        )

        with pytest.raises(SystemExit):
            run_gerrit_query("review.example.com", "status:open")

    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_query_with_extra_args(self, mock_run):
        """Test query with extra arguments."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"number":1,"subject":"Test"}\n{"type":"stats","rowCount":1}\n',
            stderr="",
        )

        results = run_gerrit_query(
            "review.example.com",
            "change:1",
            extra_args=["--current-patch-set", "--comments"],
        )

        assert len(results) == 1
        call_args = mock_run.call_args[0][0]
        assert "--current-patch-set" in call_args
        assert "--comments" in call_args


# ============================================================================
# FORMAT FUNCTION TESTS
# ============================================================================


class TestFormatFunctions:
    """Tests for format functions."""

    def test_format_change_summary(self):
        """Test formatting change summary as markdown."""
        change = {
            "number": 12345,
            "subject": "Fix authentication bug",
            "status": "NEW",
            "owner": {"username": "alice"},
            "project": "myproject",
            "branch": "main",
            "topic": "auth-fix",
            "createdOn": 1705314600,
            "lastUpdated": 1705398600,
            "url": "https://review.example.com/c/myproject/+/12345",
            "currentPatchSet": {
                "approvals": [
                    {
                        "by": {"username": "bob"},
                        "type": "Code-Review",
                        "value": "+2",
                    }
                ]
            },
        }

        result = format_change_summary(change)

        assert "### Change 12345: Fix authentication bug" in result
        assert "- **Status:** NEW" in result
        assert "- **Owner:** alice" in result
        assert "- **Project:** myproject" in result
        assert "- **Branch:** main" in result
        assert "- **Topic:** auth-fix" in result
        assert "**Approvals:**" in result
        assert "- **Code-Review:** +2 (by bob)" in result
        assert "- **URL:** https://review.example.com/c/myproject/+/12345" in result

    def test_format_change_summary_minimal(self):
        """Test formatting change with minimal fields."""
        change = {"number": 1, "subject": "Simple", "status": "NEW"}

        result = format_change_summary(change)

        assert "### Change 1: Simple" in result
        assert "- **Status:** NEW" in result

    def test_format_change_summary_with_comments(self):
        """Test formatting change with comments."""
        change = {
            "number": 1,
            "subject": "Test",
            "status": "NEW",
            "comments": [
                {
                    "reviewer": {"username": "bob"},
                    "message": "Looks good",
                    "timestamp": 1705314600,
                }
            ],
        }

        result = format_change_summary(change)

        assert "**Comments (1):**" in result
        assert "bob" in result
        assert "Looks good" in result

    def test_format_change_row(self):
        """Test formatting change row."""
        change = {
            "number": 10,
            "subject": "Fix issue",
            "status": "NEW",
            "owner": {"username": "alice"},
            "project": "myproject",
            "createdOn": 1705314600,
        }

        result = format_change_row(change)

        assert result.startswith("### Change 10: Fix issue\n")
        assert "- **Project:** myproject" in result

    def test_format_project_row(self):
        """Test formatting project row."""
        result = format_project_row("myorg/myproject")

        assert result == "### myorg/myproject"


# ============================================================================
# COMMAND HANDLER TESTS
# ============================================================================


class TestCmdCheck:
    """Tests for check command."""

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_check_success(self, mock_run, mock_gitreview, capsys):
        """Test check when Gerrit SSH is accessible."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        mock_run.return_value = Mock(returncode=0, stdout="gerrit version 3.9.0", stderr="")

        args = Mock(host=None, port="", username=None)
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Gerrit SSH access is working" in captured.out

    def test_check_no_host(self):
        """Test check with no host configured."""
        with patch(
            "skills.gerrit.scripts.gerrit._read_gitreview",
            return_value={"host": "", "port": "29418", "project": "", "username": ""},
        ):
            args = Mock(host=None, port="", username=None)
            result = cmd_check(args)

            assert result == 1

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_check_connection_error(self, mock_run, mock_gitreview):
        """Test check when SSH connection fails."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Connection refused")

        args = Mock(host=None, port="", username=None)
        result = cmd_check(args)

        assert result == 1


class TestCmdChanges:
    """Tests for change commands."""

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.run_gerrit_query")
    def test_changes_list_markdown(self, mock_query, mock_gitreview, capsys):
        """Test changes list with markdown output."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "myproject",
            "username": "",
        }
        mock_query.return_value = [
            {
                "number": 1,
                "subject": "Fix bug",
                "status": "NEW",
                "owner": {"username": "alice"},
                "project": "myproject",
                "createdOn": 1705314600,
            },
        ]

        args = Mock(host=None, port="", username=None, limit=30, json=False)
        result = cmd_changes_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Open Changes" in captured.out
        assert "### Change 1: Fix bug" in captured.out

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.run_gerrit_query")
    def test_changes_list_json(self, mock_query, mock_gitreview, capsys):
        """Test changes list with JSON output."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        data = [{"number": 1, "subject": "Fix"}]
        mock_query.return_value = data

        args = Mock(host=None, port="", username=None, limit=30, json=True)
        result = cmd_changes_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.run_gerrit_query")
    def test_changes_list_empty(self, mock_query, mock_gitreview, capsys):
        """Test changes list with no results."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        mock_query.return_value = []

        args = Mock(host=None, port="", username=None, limit=30, json=False)
        result = cmd_changes_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No open changes found" in captured.out

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.run_gerrit_query")
    def test_changes_view(self, mock_query, mock_gitreview, capsys):
        """Test viewing a single change."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        mock_query.return_value = [
            {
                "number": 12345,
                "subject": "Fix bug",
                "status": "NEW",
                "owner": {"username": "alice"},
                "createdOn": 1705314600,
            },
        ]

        args = Mock(number=12345, host=None, port="", username=None, json=False)
        result = cmd_changes_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### Change 12345: Fix bug" in captured.out

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.run_gerrit_query")
    def test_changes_search(self, mock_query, mock_gitreview, capsys):
        """Test searching changes."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        mock_query.return_value = [
            {
                "number": 1,
                "subject": "Test",
                "status": "NEW",
                "owner": {"username": "bob"},
                "createdOn": 1705314600,
            },
        ]

        args = Mock(
            query="status:open owner:bob",
            host=None,
            port="",
            username=None,
            limit=30,
            json=False,
        )
        result = cmd_changes_search(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Search Results" in captured.out


class TestCmdProjects:
    """Tests for projects commands."""

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_projects_list(self, mock_run, mock_gitreview, capsys):
        """Test projects list."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"myproject": {"id": "myproject"}, "other": {"id": "other"}}',
            stderr="",
        )

        args = Mock(host=None, port="", username=None, limit=30, json=False)
        result = cmd_projects_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Projects" in captured.out
        assert "### myproject" in captured.out

    @patch("skills.gerrit.scripts.gerrit._read_gitreview")
    @patch("skills.gerrit.scripts.gerrit.subprocess.run")
    def test_projects_list_json(self, mock_run, mock_gitreview, capsys):
        """Test projects list with JSON output."""
        mock_gitreview.return_value = {
            "host": "review.example.com",
            "port": "29418",
            "project": "",
            "username": "",
        }
        data = {"myproject": {"id": "myproject"}}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(data),
            stderr="",
        )

        args = Mock(host=None, port="", username=None, limit=30, json=True)
        result = cmd_projects_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data


# ============================================================================
# ARGUMENT PARSER TESTS
# ============================================================================


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_parser_check(self):
        """Test parser for check command."""
        parser = build_parser()
        args = parser.parse_args(["check"])
        assert args.command == "check"

    def test_parser_changes_list(self):
        """Test parser for changes list command."""
        parser = build_parser()
        args = parser.parse_args(["changes", "list", "--limit", "10"])
        assert args.command == "changes"
        assert args.changes_command == "list"
        assert args.limit == 10

    def test_parser_changes_view(self):
        """Test parser for changes view command."""
        parser = build_parser()
        args = parser.parse_args(["changes", "view", "12345"])
        assert args.changes_command == "view"
        assert args.number == 12345

    def test_parser_changes_search(self):
        """Test parser for changes search command."""
        parser = build_parser()
        args = parser.parse_args(["changes", "search", "status:open"])
        assert args.changes_command == "search"
        assert args.query == "status:open"

    def test_parser_projects_list(self):
        """Test parser for projects list command."""
        parser = build_parser()
        args = parser.parse_args(["projects", "list"])
        assert args.command == "projects"
        assert args.projects_command == "list"

    def test_parser_global_args(self):
        """Test parser global connection args."""
        parser = build_parser()
        args = parser.parse_args(
            ["--host", "review.example.com", "--port", "29419", "--username", "alice", "check"]
        )
        assert args.host == "review.example.com"
        assert args.port == "29419"
        assert args.username == "alice"

    def test_parser_json_flag(self):
        """Test that --json flag works on list commands."""
        parser = build_parser()
        args = parser.parse_args(["changes", "list", "--json"])
        assert args.json is True

    def test_parser_default_limit(self):
        """Test default limit value."""
        parser = build_parser()
        args = parser.parse_args(["changes", "list"])
        assert args.limit == 30
