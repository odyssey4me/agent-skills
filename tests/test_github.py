"""Tests for github.py skill."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest

from skills.github.scripts.github import (
    _get_label_names,
    _get_login,
    _get_logins,
    build_parser,
    cmd_check,
    cmd_issues_list,
    cmd_issues_view,
    cmd_prs_checks,
    cmd_prs_list,
    cmd_prs_status,
    cmd_prs_view,
    cmd_repos_list,
    cmd_repos_view,
    cmd_runs_list,
    cmd_runs_view,
    cmd_search_issues,
    cmd_search_prs,
    cmd_search_repos,
    format_check,
    format_date,
    format_issue_row,
    format_issue_summary,
    format_pr_row,
    format_pr_status,
    format_pr_summary,
    format_repo_row,
    format_repo_summary,
    format_run_row,
    format_run_summary,
    format_search_issue,
    format_search_repo,
    run_gh,
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

    def test_get_login_dict(self):
        """Test extracting login from dict."""
        assert _get_login({"login": "alice"}) == "alice"

    def test_get_login_none(self):
        """Test extracting login from None."""
        assert _get_login(None) == "Unknown"

    def test_get_login_missing_key(self):
        """Test extracting login with missing key."""
        assert _get_login({}) == "Unknown"

    def test_get_logins_multiple(self):
        """Test extracting multiple logins."""
        users = [{"login": "alice"}, {"login": "bob"}]
        assert _get_logins(users) == "alice, bob"

    def test_get_logins_empty(self):
        """Test extracting logins from empty list."""
        assert _get_logins([]) == ""

    def test_get_label_names(self):
        """Test extracting label names."""
        labels = [{"name": "bug"}, {"name": "enhancement"}]
        assert _get_label_names(labels) == "bug, enhancement"

    def test_get_label_names_empty(self):
        """Test extracting label names from empty list."""
        assert _get_label_names([]) == ""


# ============================================================================
# RUN_GH TESTS
# ============================================================================


class TestRunGh:
    """Tests for run_gh helper."""

    @patch("skills.github.scripts.github.subprocess.run")
    def test_run_gh_json(self, mock_run):
        """Test running gh with JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='[{"number": 1, "title": "Test"}]',
            stderr="",
        )

        result = run_gh(["issue", "list"], "number,title")

        assert result == [{"number": 1, "title": "Test"}]
        mock_run.assert_called_once_with(
            ["gh", "issue", "list", "--json", "number,title"],
            capture_output=True,
            text=True,
        )

    @patch("skills.github.scripts.github.subprocess.run")
    def test_run_gh_no_json(self, mock_run):
        """Test running gh without JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="some output",
            stderr="",
        )

        result = run_gh(["auth", "status"])

        assert result == "some output"

    @patch("skills.github.scripts.github.subprocess.run")
    def test_run_gh_error(self, mock_run):
        """Test running gh with error."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="not authenticated",
        )

        with pytest.raises(SystemExit):
            run_gh(["issue", "list"], "number")

    @patch("skills.github.scripts.github.subprocess.run")
    def test_run_gh_empty_json(self, mock_run):
        """Test running gh with empty JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = run_gh(["issue", "list"], "number")

        assert result == ""


# ============================================================================
# FORMAT FUNCTION TESTS
# ============================================================================


class TestFormatFunctions:
    """Tests for format functions."""

    def test_format_issue_summary(self):
        """Test formatting issue summary as markdown."""
        issue = {
            "number": 42,
            "title": "Fix the login bug",
            "state": "OPEN",
            "author": {"login": "alice"},
            "assignees": [{"login": "bob"}],
            "labels": [{"name": "bug"}],
            "createdAt": "2024-01-15T10:30:00Z",
            "body": "This is the description.",
            "url": "https://github.com/owner/repo/issues/42",
        }

        result = format_issue_summary(issue)

        assert result.startswith("### #42: Fix the login bug\n")
        assert "- **State:** OPEN" in result
        assert "- **Author:** alice" in result
        assert "- **Assignees:** bob" in result
        assert "- **Labels:** bug" in result
        assert "- **Created:** 2024-01-15 10:30" in result
        assert "This is the description." in result
        assert "- **URL:** https://github.com/owner/repo/issues/42" in result

    def test_format_issue_summary_minimal(self):
        """Test formatting issue with minimal fields."""
        issue = {"number": 1, "title": "Simple", "state": "OPEN"}

        result = format_issue_summary(issue)

        assert "### #1: Simple" in result
        assert "- **State:** OPEN" in result

    def test_format_issue_row(self):
        """Test formatting issue row."""
        issue = {
            "number": 10,
            "title": "A bug",
            "state": "OPEN",
            "author": {"login": "alice"},
            "labels": [],
            "createdAt": "2024-01-15T10:30:00Z",
        }

        result = format_issue_row(issue)

        assert result.startswith("### #10: A bug\n")
        assert "Labels" not in result

    def test_format_pr_summary(self):
        """Test formatting PR summary as markdown."""
        pr = {
            "number": 99,
            "title": "Add new feature",
            "state": "OPEN",
            "isDraft": True,
            "author": {"login": "alice"},
            "assignees": [],
            "labels": [{"name": "feature"}],
            "headRefName": "feature-branch",
            "baseRefName": "main",
            "reviewDecision": "APPROVED",
            "additions": 100,
            "deletions": 20,
            "changedFiles": 5,
            "createdAt": "2024-06-01T08:00:00Z",
            "body": "PR body here.",
            "url": "https://github.com/owner/repo/pull/99",
        }

        result = format_pr_summary(pr)

        assert result.startswith("### #99: Add new feature (Draft)\n")
        assert "- **State:** OPEN" in result
        assert "- **Branch:** feature-branch → main" in result
        assert "- **Review:** APPROVED" in result
        assert "- **Changes:** +100 -20 (5 files)" in result
        assert "PR body here." in result

    def test_format_pr_row(self):
        """Test formatting PR row."""
        pr = {
            "number": 5,
            "title": "Fix",
            "state": "MERGED",
            "isDraft": False,
            "author": {"login": "bob"},
            "labels": [],
            "createdAt": "2024-03-01T00:00:00Z",
        }

        result = format_pr_row(pr)

        assert "### #5: Fix\n" in result
        assert "(Draft)" not in result

    def test_format_check(self):
        """Test formatting a check."""
        check = {
            "name": "CI / build",
            "status": "completed",
            "conclusion": "success",
            "startedAt": "2024-01-15T10:30:00Z",
        }

        result = format_check(check)

        assert "- **CI / build:** success" in result
        assert "started 2024-01-15 10:30" in result

    def test_format_check_no_conclusion(self):
        """Test formatting a check without conclusion."""
        check = {"name": "CI", "status": "in_progress", "conclusion": ""}

        result = format_check(check)

        assert "- **CI:** in_progress" in result

    def test_format_pr_status_full(self):
        """Test formatting pr status with all sections populated."""
        data = {
            "currentBranch": {
                "number": 10,
                "title": "Current PR",
                "state": "OPEN",
                "isDraft": False,
                "reviewDecision": "REVIEW_REQUIRED",
                "url": "https://github.com/owner/repo/pull/10",
            },
            "createdBy": [
                {
                    "number": 5,
                    "title": "My PR",
                    "state": "OPEN",
                    "isDraft": True,
                    "headRefName": "feature",
                    "baseRefName": "main",
                    "reviewDecision": "APPROVED",
                },
            ],
            "needsReview": [
                {
                    "number": 8,
                    "title": "Review me",
                    "state": "OPEN",
                    "isDraft": False,
                    "headRefName": "fix",
                    "baseRefName": "main",
                    "reviewDecision": "",
                },
            ],
        }

        result = format_pr_status(data)

        assert "## PR Status" in result
        assert "### Current Branch" in result
        assert "**#10: Current PR**" in result
        assert "Review: REVIEW_REQUIRED" in result
        assert "### Created by You" in result
        assert "**#5: My PR** (Draft)" in result
        assert "(feature → main)" in result
        assert "Review: APPROVED" in result
        assert "### Requesting Your Review" in result
        assert "**#8: Review me**" in result

    def test_format_pr_status_empty(self):
        """Test formatting pr status with no PRs."""
        data = {
            "currentBranch": None,
            "createdBy": [],
            "needsReview": [],
        }

        result = format_pr_status(data)

        assert "No PR for current branch" in result
        assert "None" in result

    def test_format_run_summary(self):
        """Test formatting run summary."""
        run = {
            "databaseId": 12345,
            "displayTitle": "CI Pipeline",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "createdAt": "2024-01-15T10:30:00Z",
            "workflowName": "Build",
            "headBranch": "main",
            "headSha": "abc123def456",
            "url": "https://github.com/owner/repo/actions/runs/12345",
            "jobs": [{"name": "build", "conclusion": "success"}],
        }

        result = format_run_summary(run)

        assert "### CI Pipeline (#12345)" in result
        assert "- **Status:** success" in result
        assert "- **Event:** push" in result
        assert "- **Workflow:** Build" in result
        assert "- **Branch:** main" in result
        assert "- **Commit:** abc123de" in result
        assert "- **build:** success" in result

    def test_format_run_row(self):
        """Test formatting run row."""
        run = {
            "databaseId": 1,
            "displayTitle": "Test",
            "status": "in_progress",
            "conclusion": "",
            "event": "pull_request",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        result = format_run_row(run)

        assert "### Test (#1)" in result
        assert "- **Status:** in_progress" in result

    def test_format_repo_summary(self):
        """Test formatting repo summary."""
        repo = {
            "name": "agent-skills",
            "owner": {"login": "odyssey4me"},
            "description": "Agent skills repo",
            "isPrivate": False,
            "stargazerCount": 42,
            "forkCount": 10,
            "primaryLanguage": {"name": "Python"},
            "licenseInfo": {"name": "MIT License"},
            "defaultBranchRef": {"name": "main"},
            "updatedAt": "2024-06-01T00:00:00Z",
            "url": "https://github.com/odyssey4me/agent-skills",
        }

        result = format_repo_summary(repo)

        assert "### odyssey4me/agent-skills" in result
        assert "- **Description:** Agent skills repo" in result
        assert "- **Visibility:** Public" in result
        assert "- **Stars:** 42" in result
        assert "- **Forks:** 10" in result
        assert "- **Language:** Python" in result
        assert "- **License:** MIT License" in result
        assert "- **Default Branch:** main" in result

    def test_format_repo_row(self):
        """Test formatting repo row."""
        repo = {
            "name": "test",
            "owner": {"login": "alice"},
            "description": "A test repo",
            "isPrivate": True,
            "stargazerCount": 0,
        }

        result = format_repo_row(repo)

        assert "### alice/test" in result
        assert "- **Visibility:** Private" in result

    def test_format_search_repo(self):
        """Test formatting search result repo."""
        repo = {
            "fullName": "alice/project",
            "description": "Cool project",
            "isPrivate": False,
            "stargazersCount": 100,
            "updatedAt": "2024-01-01T00:00:00Z",
            "url": "https://github.com/alice/project",
        }

        result = format_search_repo(repo)

        assert "### alice/project" in result
        assert "- **Stars:** 100" in result

    def test_format_search_issue(self):
        """Test formatting search result issue."""
        issue = {
            "repository": {"nameWithOwner": "alice/repo"},
            "number": 5,
            "title": "Bug report",
            "state": "open",
            "author": {"login": "bob"},
            "labels": [{"name": "bug"}],
            "createdAt": "2024-01-01T00:00:00Z",
        }

        result = format_search_issue(issue)

        assert "### alice/repo#5: Bug report" in result
        assert "- **Labels:** bug" in result


# ============================================================================
# COMMAND HANDLER TESTS
# ============================================================================


class TestCmdCheck:
    """Tests for check command."""

    @patch("skills.github.scripts.github.subprocess.run")
    @patch("skills.github.scripts.github.shutil.which")
    def test_check_success(self, mock_which, mock_run, capsys):
        """Test check when gh is installed and authenticated."""
        mock_which.return_value = "/usr/bin/gh"
        mock_run.return_value = Mock(returncode=0, stderr="Logged in to github.com")

        args = Mock()
        result = cmd_check(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "gh CLI is installed and authenticated" in captured.out

    @patch("skills.github.scripts.github.shutil.which")
    def test_check_not_installed(self, mock_which):
        """Test check when gh is not installed."""
        mock_which.return_value = None

        args = Mock()
        result = cmd_check(args)

        assert result == 1

    @patch("skills.github.scripts.github.subprocess.run")
    @patch("skills.github.scripts.github.shutil.which")
    def test_check_not_authenticated(self, mock_which, mock_run):
        """Test check when gh is not authenticated."""
        mock_which.return_value = "/usr/bin/gh"
        mock_run.return_value = Mock(returncode=1, stderr="not logged in")

        args = Mock()
        result = cmd_check(args)

        assert result == 1


class TestCmdIssues:
    """Tests for issue commands."""

    @patch("skills.github.scripts.github.run_gh")
    def test_issues_list_markdown(self, mock_run_gh, capsys):
        """Test issues list with markdown output."""
        mock_run_gh.return_value = [
            {
                "number": 1,
                "title": "Bug",
                "state": "OPEN",
                "author": {"login": "alice"},
                "labels": [],
                "createdAt": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(repo="owner/repo", limit=30, json=False)
        result = cmd_issues_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Issues" in captured.out
        assert "### #1: Bug" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_issues_list_json(self, mock_run_gh, capsys):
        """Test issues list with JSON output."""
        data = [{"number": 1, "title": "Bug"}]
        mock_run_gh.return_value = data

        args = Mock(repo=None, limit=30, json=True)
        result = cmd_issues_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data

    @patch("skills.github.scripts.github.run_gh")
    def test_issues_list_empty(self, mock_run_gh, capsys):
        """Test issues list with no results."""
        mock_run_gh.return_value = []

        args = Mock(repo=None, limit=30, json=False)
        result = cmd_issues_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_issues_view(self, mock_run_gh, capsys):
        """Test viewing a single issue."""
        mock_run_gh.return_value = {
            "number": 42,
            "title": "Bug",
            "state": "OPEN",
            "author": {"login": "alice"},
            "createdAt": "2024-01-01T00:00:00Z",
        }

        args = Mock(number=42, repo=None, json=False)
        result = cmd_issues_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### #42: Bug" in captured.out


class TestCmdPrs:
    """Tests for PR commands."""

    @patch("skills.github.scripts.github.run_gh")
    def test_prs_list_markdown(self, mock_run_gh, capsys):
        """Test PRs list with markdown output."""
        mock_run_gh.return_value = [
            {
                "number": 1,
                "title": "Feature",
                "state": "OPEN",
                "isDraft": False,
                "author": {"login": "alice"},
                "labels": [],
                "createdAt": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(repo=None, limit=30, json=False)
        result = cmd_prs_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Pull Requests" in captured.out
        assert "### #1: Feature" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_prs_view(self, mock_run_gh, capsys):
        """Test viewing a single PR."""
        mock_run_gh.return_value = {
            "number": 5,
            "title": "Fix",
            "state": "MERGED",
            "isDraft": False,
            "author": {"login": "bob"},
            "createdAt": "2024-01-01T00:00:00Z",
        }

        args = Mock(number=5, repo=None, json=False)
        result = cmd_prs_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### #5: Fix" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_prs_checks(self, mock_run_gh, capsys):
        """Test PR checks."""
        mock_run_gh.return_value = [
            {
                "name": "CI",
                "status": "completed",
                "conclusion": "success",
                "startedAt": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(number=5, repo=None, json=False)
        result = cmd_prs_checks(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "- **CI:** success" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_prs_status_markdown(self, mock_run_gh, capsys):
        """Test PR status with markdown output."""
        mock_run_gh.return_value = {
            "currentBranch": {
                "number": 10,
                "title": "My PR",
                "state": "OPEN",
                "isDraft": False,
                "reviewDecision": "",
                "url": "https://github.com/owner/repo/pull/10",
            },
            "createdBy": [],
            "needsReview": [],
        }

        args = Mock(repo=None, json=False)
        result = cmd_prs_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## PR Status" in captured.out
        assert "**#10: My PR**" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_prs_status_json(self, mock_run_gh, capsys):
        """Test PR status with JSON output."""
        data = {"currentBranch": None, "createdBy": [], "needsReview": []}
        mock_run_gh.return_value = data

        args = Mock(repo="owner/repo", json=True)
        result = cmd_prs_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data


class TestCmdRuns:
    """Tests for runs commands."""

    @patch("skills.github.scripts.github.run_gh")
    def test_runs_list(self, mock_run_gh, capsys):
        """Test runs list."""
        mock_run_gh.return_value = [
            {
                "databaseId": 1,
                "displayTitle": "Build",
                "status": "completed",
                "conclusion": "success",
                "event": "push",
                "createdAt": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(repo=None, limit=30, json=False)
        result = cmd_runs_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Workflow Runs" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_runs_view(self, mock_run_gh, capsys):
        """Test viewing a run."""
        mock_run_gh.return_value = {
            "databaseId": 1,
            "displayTitle": "Build",
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "createdAt": "2024-01-01T00:00:00Z",
        }

        args = Mock(run_id=1, repo=None, json=False)
        result = cmd_runs_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### Build (#1)" in captured.out


class TestCmdRepos:
    """Tests for repos commands."""

    @patch("skills.github.scripts.github.run_gh")
    def test_repos_list(self, mock_run_gh, capsys):
        """Test repos list."""
        mock_run_gh.return_value = [
            {
                "name": "test",
                "owner": {"login": "alice"},
                "description": "A test",
                "isPrivate": False,
                "stargazerCount": 5,
            },
        ]

        args = Mock(limit=30, json=False)
        result = cmd_repos_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Repositories" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_repos_view(self, mock_run_gh, capsys):
        """Test viewing a repo."""
        mock_run_gh.return_value = {
            "name": "test",
            "owner": {"login": "alice"},
            "description": "A test",
            "isPrivate": False,
            "stargazerCount": 5,
            "updatedAt": "2024-01-01T00:00:00Z",
        }

        args = Mock(repo="alice/test", json=False)
        result = cmd_repos_view(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "### alice/test" in captured.out


class TestCmdSearch:
    """Tests for search commands."""

    @patch("skills.github.scripts.github.run_gh")
    def test_search_repos(self, mock_run_gh, capsys):
        """Test searching repos."""
        mock_run_gh.return_value = [
            {
                "fullName": "alice/ml",
                "description": "ML project",
                "isPrivate": False,
                "stargazersCount": 100,
                "updatedAt": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(query="machine learning", limit=30, json=False)
        result = cmd_search_repos(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Search Results" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_search_issues(self, mock_run_gh, capsys):
        """Test searching issues."""
        mock_run_gh.return_value = [
            {
                "repository": {"nameWithOwner": "alice/repo"},
                "number": 1,
                "title": "Bug",
                "state": "open",
                "author": {"login": "bob"},
                "labels": [],
                "createdAt": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(query="label:bug", limit=30, json=False)
        result = cmd_search_issues(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Search Results" in captured.out

    @patch("skills.github.scripts.github.run_gh")
    def test_search_prs(self, mock_run_gh, capsys):
        """Test searching PRs."""
        mock_run_gh.return_value = [
            {
                "repository": {"nameWithOwner": "alice/repo"},
                "number": 1,
                "title": "Feature",
                "state": "open",
                "author": {"login": "bob"},
                "labels": [],
                "createdAt": "2024-01-01T00:00:00Z",
            },
        ]

        args = Mock(query="is:open", limit=30, json=False)
        result = cmd_search_prs(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "## Search Results" in captured.out


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
        args = parser.parse_args(["issues", "list", "--repo", "owner/repo", "--limit", "10"])
        assert args.command == "issues"
        assert args.issues_command == "list"
        assert args.repo == "owner/repo"
        assert args.limit == 10

    def test_parser_issues_view(self):
        """Test parser for issues view command."""
        parser = build_parser()
        args = parser.parse_args(["issues", "view", "42", "-R", "owner/repo"])
        assert args.issues_command == "view"
        assert args.number == 42

    def test_parser_prs_list(self):
        """Test parser for prs list command."""
        parser = build_parser()
        args = parser.parse_args(["prs", "list"])
        assert args.command == "prs"
        assert args.prs_command == "list"

    def test_parser_prs_view(self):
        """Test parser for prs view command."""
        parser = build_parser()
        args = parser.parse_args(["prs", "view", "99"])
        assert args.prs_command == "view"
        assert args.number == 99

    def test_parser_prs_checks(self):
        """Test parser for prs checks command."""
        parser = build_parser()
        args = parser.parse_args(["prs", "checks", "5"])
        assert args.prs_command == "checks"
        assert args.number == 5

    def test_parser_prs_status(self):
        """Test parser for prs status command."""
        parser = build_parser()
        args = parser.parse_args(["prs", "status", "--repo", "owner/repo"])
        assert args.prs_command == "status"
        assert args.repo == "owner/repo"

    def test_parser_runs_list(self):
        """Test parser for runs list command."""
        parser = build_parser()
        args = parser.parse_args(["runs", "list"])
        assert args.command == "runs"
        assert args.runs_command == "list"

    def test_parser_runs_view(self):
        """Test parser for runs view command."""
        parser = build_parser()
        args = parser.parse_args(["runs", "view", "12345"])
        assert args.runs_command == "view"
        assert args.run_id == 12345

    def test_parser_repos_list(self):
        """Test parser for repos list command."""
        parser = build_parser()
        args = parser.parse_args(["repos", "list"])
        assert args.command == "repos"
        assert args.repos_command == "list"

    def test_parser_repos_view(self):
        """Test parser for repos view command."""
        parser = build_parser()
        args = parser.parse_args(["repos", "view", "owner/repo"])
        assert args.repos_command == "view"
        assert args.repo == "owner/repo"

    def test_parser_search_repos(self):
        """Test parser for search repos command."""
        parser = build_parser()
        args = parser.parse_args(["search", "repos", "machine learning"])
        assert args.command == "search"
        assert args.search_command == "repos"
        assert args.query == "machine learning"

    def test_parser_search_issues(self):
        """Test parser for search issues command."""
        parser = build_parser()
        args = parser.parse_args(["search", "issues", "label:bug"])
        assert args.search_command == "issues"

    def test_parser_search_prs(self):
        """Test parser for search prs command."""
        parser = build_parser()
        args = parser.parse_args(["search", "prs", "is:open"])
        assert args.search_command == "prs"

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
