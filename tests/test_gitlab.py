"""Tests for gitlab.py skill."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest

from skills.gitlab.scripts.gitlab import (
    _get_labels,
    _get_username,
    _get_usernames,
    build_parser,
    cmd_check,
    cmd_issues_list,
    cmd_issues_view,
    cmd_mrs_list,
    cmd_mrs_view,
    cmd_pipelines_list,
    cmd_pipelines_view,
    cmd_repos_list,
    cmd_repos_view,
    format_date,
    format_issue_row,
    format_issue_summary,
    format_mr_row,
    format_mr_summary,
    format_pipeline_row,
    format_pipeline_summary,
    format_repo_row,
    format_repo_summary,
    run_glab,
)

# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestHelpers:
    """Tests for helper functions."""

    def test_format_date_full(self):
        """Test formatting full ISO date."""
        assert format_date("2024-01-15T10:30:00Z") == "2024-01-15 10:30"

    def test_format_date_none(self):
        """Test formatting None date."""
        assert format_date(None) == "N/A"

    def test_format_date_empty(self):
        """Test formatting empty date."""
        assert format_date("") == "N/A"

    def test_format_date_short(self):
        """Test formatting short date string."""
        assert format_date("2024-01-15") == "2024-01-15"

    def test_get_username_dict(self):
        """Test extracting username from dict."""
        assert _get_username({"username": "alice"}) == "alice"

    def test_get_username_none(self):
        """Test extracting username from None."""
        assert _get_username(None) == "Unknown"

    def test_get_username_missing_key(self):
        """Test extracting username with missing key."""
        assert _get_username({}) == "Unknown"

    def test_get_usernames_multiple(self):
        """Test extracting multiple usernames."""
        users = [{"username": "alice"}, {"username": "bob"}]
        assert _get_usernames(users) == "alice, bob"

    def test_get_usernames_empty(self):
        """Test extracting usernames from empty list."""
        assert _get_usernames([]) == ""

    def test_get_labels_strings(self):
        """Test extracting labels from plain strings (GitLab format)."""
        labels = ["bug", "enhancement"]
        assert _get_labels(labels) == "bug, enhancement"

    def test_get_labels_dicts(self):
        """Test extracting labels from dicts (compatibility)."""
        labels = [{"name": "bug"}, {"name": "feature"}]
        assert _get_labels(labels) == "bug, feature"

    def test_get_labels_empty(self):
        """Test extracting labels from empty list."""
        assert _get_labels([]) == ""


# ============================================================================
# RUN_GLAB TESTS
# ============================================================================


class TestRunGlab:
    """Tests for run_glab helper."""

    @patch("skills.gitlab.scripts.gitlab.subprocess.run")
    def test_run_glab_json(self, mock_run):
        """Test running glab with JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='[{"iid": 1, "title": "Test"}]',
            stderr="",
        )

        result = run_glab(["issue", "list"], output_json=True)

        assert result == [{"iid": 1, "title": "Test"}]
        mock_run.assert_called_once_with(
            ["glab", "issue", "list", "--output", "json"],
            capture_output=True,
            text=True,
        )

    @patch("skills.gitlab.scripts.gitlab.subprocess.run")
    def test_run_glab_no_json(self, mock_run):
        """Test running glab without JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="some output",
            stderr="",
        )

        result = run_glab(["auth", "status"])

        assert result == "some output"

    @patch("skills.gitlab.scripts.gitlab.subprocess.run")
    def test_run_glab_error(self, mock_run):
        """Test running glab with error."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="not authenticated",
        )

        with pytest.raises(SystemExit):
            run_glab(["issue", "list"], output_json=True)

    @patch("skills.gitlab.scripts.gitlab.subprocess.run")
    def test_run_glab_empty_json(self, mock_run):
        """Test running glab with empty JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = run_glab(["issue", "list"], output_json=True)

        assert result == ""


# ============================================================================
# FORMAT FUNCTION TESTS
# ============================================================================


class TestFormatFunctions:
    """Tests for format functions."""

    def test_format_issue_summary(self):
        """Test formatting issue summary as markdown."""
        issue = {
            "iid": 42,
            "title": "Fix the login bug",
            "state": "opened",
            "author": {"username": "alice"},
            "assignees": [{"username": "bob"}],
            "labels": ["bug"],
            "created_at": "2024-01-15T10:30:00Z",
            "description": "This is the description.",
            "web_url": "https://gitlab.com/group/repo/-/issues/42",
        }

        result = format_issue_summary(issue)

        assert result.startswith("### #42: Fix the login bug\n")
        assert "- **State:** opened" in result
        assert "- **Author:** alice" in result
        assert "- **Assignees:** bob" in result
        assert "- **Labels:** bug" in result
        assert "- **Created:** 2024-01-15 10:30" in result
        assert "This is the description." in result
        assert "- **URL:** https://gitlab.com/group/repo/-/issues/42" in result

    def test_format_issue_summary_minimal(self):
        """Test formatting issue with minimal fields."""
        issue = {"iid": 1, "title": "Simple", "state": "opened"}

        result = format_issue_summary(issue)

        assert "### #1: Simple" in result
        assert "- **State:** opened" in result

    def test_format_issue_row(self):
        """Test formatting issue row."""
        issue = {
            "iid": 10,
            "title": "A bug",
            "state": "opened",
            "author": {"username": "alice"},
            "labels": [],
            "created_at": "2024-01-15T10:30:00Z",
        }

        result = format_issue_row(issue)

        assert result.startswith("### #10: A bug\n")
        assert "Labels" not in result

    def test_format_mr_summary(self):
        """Test formatting MR summary as markdown."""
        mr = {
            "iid": 99,
            "title": "Add new feature",
            "state": "opened",
            "draft": True,
            "author": {"username": "alice"},
            "assignees": [],
            "labels": ["feature"],
            "source_branch": "feature-branch",
            "target_branch": "main",
            "merge_status": "can_be_merged",
            "created_at": "2024-06-01T08:00:00Z",
            "description": "MR description here.",
            "web_url": "https://gitlab.com/group/repo/-/merge_requests/99",
        }

        result = format_mr_summary(mr)

        assert result.startswith("### !99: Add new feature (Draft)\n")
        assert "- **State:** opened" in result
        assert "- **Branch:** feature-branch \u2192 main" in result
        assert "- **Merge Status:** can_be_merged" in result
        assert "MR description here." in result

    def test_format_mr_row(self):
        """Test formatting MR row."""
        mr = {
            "iid": 5,
            "title": "Fix",
            "state": "merged",
            "draft": False,
            "author": {"username": "bob"},
            "labels": [],
            "created_at": "2024-03-01T00:00:00Z",
        }

        result = format_mr_row(mr)

        assert "### !5: Fix\n" in result
        assert "(Draft)" not in result

    def test_format_pipeline_summary(self):
        """Test formatting pipeline summary."""
        pipeline = {
            "id": 12345,
            "status": "success",
            "ref": "main",
            "sha": "abc123def456",
            "created_at": "2024-01-15T10:30:00Z",
            "source": "push",
            "web_url": "https://gitlab.com/group/repo/-/pipelines/12345",
        }

        result = format_pipeline_summary(pipeline)

        assert "### Pipeline #12345" in result
        assert "- **Status:** success" in result
        assert "- **Ref:** main" in result
        assert "- **Commit:** abc123de" in result
        assert "- **Source:** push" in result
        assert "- **URL:** https://gitlab.com/group/repo/-/pipelines/12345" in result

    def test_format_pipeline_row(self):
        """Test formatting pipeline row."""
        pipeline = {
            "id": 1,
            "status": "running",
            "ref": "feature",
            "created_at": "2024-01-01T00:00:00Z",
        }

        result = format_pipeline_row(pipeline)

        assert "### Pipeline #1" in result
        assert "- **Status:** running" in result
        assert "- **Ref:** feature" in result

    def test_format_repo_summary(self):
        """Test formatting repo summary."""
        repo = {
            "path_with_namespace": "group/agent-skills",
            "description": "Agent skills repo",
            "visibility": "public",
            "star_count": 42,
            "forks_count": 10,
            "default_branch": "main",
            "updated_at": "2024-06-01T00:00:00Z",
            "web_url": "https://gitlab.com/group/agent-skills",
        }

        result = format_repo_summary(repo)

        assert "### group/agent-skills" in result
        assert "- **Description:** Agent skills repo" in result
        assert "- **Visibility:** public" in result
        assert "- **Stars:** 42" in result
        assert "- **Forks:** 10" in result
        assert "- **Default Branch:** main" in result

    def test_format_repo_summary_fallback_name(self):
        """Test formatting repo summary with fallback name."""
        repo = {
            "name": "test",
            "namespace": {"full_path": "alice"},
            "description": "A test repo",
            "visibility": "private",
            "star_count": 0,
        }

        result = format_repo_summary(repo)

        assert "### alice/test" in result
        assert "- **Visibility:** private" in result

    def test_format_repo_row(self):
        """Test formatting repo row."""
        repo = {
            "path_with_namespace": "alice/test",
            "description": "A test repo",
            "visibility": "private",
            "star_count": 0,
        }

        result = format_repo_row(repo)

        assert "### alice/test" in result
        assert "- **Visibility:** private" in result


# ============================================================================
# COMMAND HANDLER TESTS
# ============================================================================


class TestCmdCheck:
    """Tests for check command."""

    @patch("skills.gitlab.scripts.gitlab.subprocess.run")
    @patch("skills.gitlab.scripts.gitlab.shutil.which")
    def test_check_success(self, mock_which, mock_run, capsys):
        """Test check when glab is installed and authenticated."""
        mock_which.return_value = "/usr/bin/glab"
        mock_run.return_value = Mock(returncode=0, stderr="Logged in to gitlab.com")

        args = Mock()
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "glab CLI is installed and authenticated" in captured.out

    @patch("skills.gitlab.scripts.gitlab.shutil.which")
    def test_check_not_installed(self, mock_which):
        """Test check when glab is not installed."""
        mock_which.return_value = None

        args = Mock()
        result = cmd_check(args)

        assert result == 1

    @patch("skills.gitlab.scripts.gitlab.subprocess.run")
    @patch("skills.gitlab.scripts.gitlab.shutil.which")
    def test_check_not_authenticated(self, mock_which, mock_run):
        """Test check when glab is not authenticated."""
        mock_which.return_value = "/usr/bin/glab"
        mock_run.return_value = Mock(returncode=1, stderr="not logged in")

        args = Mock()
        result = cmd_check(args)

        assert result == 1


class TestCmdIssues:
    """Tests for issue commands."""

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_issues_list_markdown(self, mock_run_glab, capsys):
        """Test issues list with markdown output."""
        mock_run_glab.return_value = [
            {
                "iid": 1,
                "title": "Bug",
                "state": "opened",
                "author": {"username": "alice"},
                "labels": [],
                "created_at": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(repo="group/repo", limit=30, json=False)
        result = cmd_issues_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Issues" in captured.out
        assert "### #1: Bug" in captured.out

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_issues_list_json(self, mock_run_glab, capsys):
        """Test issues list with JSON output."""
        data = [{"iid": 1, "title": "Bug"}]
        mock_run_glab.return_value = data

        args = Mock(repo=None, limit=30, json=True)
        result = cmd_issues_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_issues_list_empty(self, mock_run_glab, capsys):
        """Test issues list with no results."""
        mock_run_glab.return_value = []

        args = Mock(repo=None, limit=30, json=False)
        result = cmd_issues_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_issues_view(self, mock_run_glab, capsys):
        """Test viewing a single issue."""
        mock_run_glab.return_value = {
            "iid": 42,
            "title": "Bug",
            "state": "opened",
            "author": {"username": "alice"},
            "created_at": "2024-01-01T00:00:00Z",
        }

        args = Mock(number=42, repo=None, json=False)
        result = cmd_issues_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### #42: Bug" in captured.out


class TestCmdMrs:
    """Tests for MR commands."""

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_mrs_list_markdown(self, mock_run_glab, capsys):
        """Test MRs list with markdown output."""
        mock_run_glab.return_value = [
            {
                "iid": 1,
                "title": "Feature",
                "state": "opened",
                "draft": False,
                "author": {"username": "alice"},
                "labels": [],
                "created_at": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(repo=None, limit=30, json=False)
        result = cmd_mrs_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Merge Requests" in captured.out
        assert "### !1: Feature" in captured.out

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_mrs_view(self, mock_run_glab, capsys):
        """Test viewing a single MR."""
        mock_run_glab.return_value = {
            "iid": 5,
            "title": "Fix",
            "state": "merged",
            "draft": False,
            "author": {"username": "bob"},
            "created_at": "2024-01-01T00:00:00Z",
        }

        args = Mock(number=5, repo=None, json=False)
        result = cmd_mrs_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### !5: Fix" in captured.out


class TestCmdPipelines:
    """Tests for pipeline commands."""

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_pipelines_list(self, mock_run_glab, capsys):
        """Test pipelines list."""
        mock_run_glab.return_value = [
            {
                "id": 1,
                "status": "success",
                "ref": "main",
                "created_at": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(repo=None, limit=30, json=False)
        result = cmd_pipelines_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Pipelines" in captured.out

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_pipelines_view(self, mock_run_glab, capsys):
        """Test viewing a pipeline."""
        mock_run_glab.return_value = {
            "id": 1,
            "status": "success",
            "ref": "main",
            "created_at": "2024-01-01T00:00:00Z",
        }

        args = Mock(pipeline_id=1, repo=None, json=False)
        result = cmd_pipelines_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### Pipeline #1" in captured.out


class TestCmdRepos:
    """Tests for repos commands."""

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_repos_list(self, mock_run_glab, capsys):
        """Test repos list."""
        mock_run_glab.return_value = [
            {
                "path_with_namespace": "alice/test",
                "description": "A test",
                "visibility": "public",
                "star_count": 5,
            },
        ]

        args = Mock(limit=30, json=False)
        result = cmd_repos_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Repositories" in captured.out

    @patch("skills.gitlab.scripts.gitlab.run_glab")
    def test_repos_view(self, mock_run_glab, capsys):
        """Test viewing a repo."""
        mock_run_glab.return_value = {
            "path_with_namespace": "alice/test",
            "description": "A test",
            "visibility": "public",
            "star_count": 5,
            "updated_at": "2024-01-01T00:00:00Z",
        }

        args = Mock(repo="alice/test", json=False)
        result = cmd_repos_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### alice/test" in captured.out


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

    def test_parser_issues_list(self):
        """Test parser for issues list command."""
        parser = build_parser()
        args = parser.parse_args(["issues", "list", "--repo", "group/repo", "--limit", "10"])
        assert args.command == "issues"
        assert args.issues_command == "list"
        assert args.repo == "group/repo"
        assert args.limit == 10

    def test_parser_issues_view(self):
        """Test parser for issues view command."""
        parser = build_parser()
        args = parser.parse_args(["issues", "view", "42", "-R", "group/repo"])
        assert args.issues_command == "view"
        assert args.number == 42

    def test_parser_mrs_list(self):
        """Test parser for mrs list command."""
        parser = build_parser()
        args = parser.parse_args(["mrs", "list"])
        assert args.command == "mrs"
        assert args.mrs_command == "list"

    def test_parser_mrs_view(self):
        """Test parser for mrs view command."""
        parser = build_parser()
        args = parser.parse_args(["mrs", "view", "99"])
        assert args.mrs_command == "view"
        assert args.number == 99

    def test_parser_pipelines_list(self):
        """Test parser for pipelines list command."""
        parser = build_parser()
        args = parser.parse_args(["pipelines", "list"])
        assert args.command == "pipelines"
        assert args.pipelines_command == "list"

    def test_parser_pipelines_view(self):
        """Test parser for pipelines view command."""
        parser = build_parser()
        args = parser.parse_args(["pipelines", "view", "12345"])
        assert args.pipelines_command == "view"
        assert args.pipeline_id == 12345

    def test_parser_repos_list(self):
        """Test parser for repos list command."""
        parser = build_parser()
        args = parser.parse_args(["repos", "list"])
        assert args.command == "repos"
        assert args.repos_command == "list"

    def test_parser_repos_view(self):
        """Test parser for repos view command."""
        parser = build_parser()
        args = parser.parse_args(["repos", "view", "group/repo"])
        assert args.repos_command == "view"
        assert args.repo == "group/repo"

    def test_parser_json_flag(self):
        """Test that --json flag works on list commands."""
        parser = build_parser()
        args = parser.parse_args(["issues", "list", "--json"])
        assert args.json is True

    def test_parser_default_limit(self):
        """Test default limit value."""
        parser = build_parser()
        args = parser.parse_args(["issues", "list"])
        assert args.limit == 30
