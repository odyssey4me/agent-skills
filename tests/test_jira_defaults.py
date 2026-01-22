"""Tests for Jira defaults functionality."""

from __future__ import annotations

from skills.jira.scripts.jira import (
    JiraDefaults,
    ProjectDefaults,
    merge_jql_with_scope,
)


class TestJiraDefaults:
    """Tests for JiraDefaults dataclass."""

    def test_from_config_empty(self):
        """Test loading from empty config."""
        defaults = JiraDefaults.from_config({})
        assert defaults.jql_scope is None
        assert defaults.security_level is None
        assert defaults.max_results is None
        assert defaults.fields is None

    def test_from_config_full(self):
        """Test loading from full config."""
        config = {
            "defaults": {
                "jql_scope": "project = DEMO",
                "security_level": "Internal",
                "max_results": 25,
                "fields": ["summary", "status"],
            }
        }
        defaults = JiraDefaults.from_config(config)
        assert defaults.jql_scope == "project = DEMO"
        assert defaults.security_level == "Internal"
        assert defaults.max_results == 25
        assert defaults.fields == ["summary", "status"]

    def test_from_config_partial(self):
        """Test loading with only some defaults configured."""
        config = {
            "defaults": {
                "jql_scope": "project = DEMO",
                "max_results": 10,
            }
        }
        defaults = JiraDefaults.from_config(config)
        assert defaults.jql_scope == "project = DEMO"
        assert defaults.security_level is None
        assert defaults.max_results == 10
        assert defaults.fields is None

    def test_from_config_no_defaults_section(self):
        """Test loading when config has no defaults section."""
        config = {"url": "https://example.com"}
        defaults = JiraDefaults.from_config(config)
        assert defaults.jql_scope is None
        assert defaults.security_level is None
        assert defaults.max_results is None
        assert defaults.fields is None


class TestProjectDefaults:
    """Tests for ProjectDefaults dataclass."""

    def test_from_config_empty(self):
        """Test loading from empty config."""
        defaults = ProjectDefaults.from_config({}, "DEMO")
        assert defaults.issue_type is None
        assert defaults.priority is None

    def test_from_config_missing_project(self):
        """Test loading for unconfigured project."""
        config = {"projects": {"OTHER": {"issue_type": "Bug"}}}
        defaults = ProjectDefaults.from_config(config, "DEMO")
        assert defaults.issue_type is None
        assert defaults.priority is None

    def test_from_config_configured_project(self):
        """Test loading for configured project."""
        config = {
            "projects": {
                "DEMO": {
                    "issue_type": "Task",
                    "priority": "High",
                }
            }
        }
        defaults = ProjectDefaults.from_config(config, "DEMO")
        assert defaults.issue_type == "Task"
        assert defaults.priority == "High"

    def test_from_config_partial_project_defaults(self):
        """Test loading with only some project defaults configured."""
        config = {
            "projects": {
                "DEMO": {
                    "issue_type": "Task",
                }
            }
        }
        defaults = ProjectDefaults.from_config(config, "DEMO")
        assert defaults.issue_type == "Task"
        assert defaults.priority is None

    def test_from_config_no_projects_section(self):
        """Test loading when config has no projects section."""
        config = {"url": "https://example.com"}
        defaults = ProjectDefaults.from_config(config, "DEMO")
        assert defaults.issue_type is None
        assert defaults.priority is None


class TestMergeJql:
    """Tests for JQL merging with scope."""

    def test_merge_no_scope(self):
        """Test merge with no scope configured."""
        result = merge_jql_with_scope("status = Open", None)
        assert result == "status = Open"

    def test_merge_empty_scope(self):
        """Test merge with empty string scope."""
        result = merge_jql_with_scope("status = Open", "")
        assert result == "status = Open"

    def test_merge_whitespace_scope(self):
        """Test merge with whitespace-only scope."""
        result = merge_jql_with_scope("status = Open", "   ")
        assert result == "status = Open"

    def test_merge_no_user_jql(self):
        """Test merge with no user JQL."""
        result = merge_jql_with_scope("", "project = DEMO")
        assert result == "project = DEMO"

    def test_merge_whitespace_user_jql(self):
        """Test merge with whitespace-only user JQL."""
        result = merge_jql_with_scope("   ", "project = DEMO")
        assert result == "project = DEMO"

    def test_merge_both_present(self):
        """Test merge with both scope and user JQL."""
        result = merge_jql_with_scope(
            "status = Open",
            "project = DEMO AND assignee = currentUser()"
        )
        expected = "(project = DEMO AND assignee = currentUser()) AND (status = Open)"
        assert result == expected

    def test_merge_preserves_or_precedence(self):
        """Test that parentheses preserve OR operator precedence."""
        result = merge_jql_with_scope(
            "status = Open OR status = 'In Progress'",
            "project = DEMO"
        )
        expected = "(project = DEMO) AND (status = Open OR status = 'In Progress')"
        assert result == expected

    def test_merge_complex_user_query(self):
        """Test with complex user query."""
        result = merge_jql_with_scope(
            "priority = High AND (status = Open OR status = 'In Progress')",
            "project = DEMO"
        )
        expected = "(project = DEMO) AND (priority = High AND (status = Open OR status = 'In Progress'))"
        assert result == expected

    def test_merge_complex_scope(self):
        """Test with complex scope."""
        result = merge_jql_with_scope(
            "status = Open",
            "project = DEMO AND assignee = currentUser() AND created >= -30d"
        )
        expected = "(project = DEMO AND assignee = currentUser() AND created >= -30d) AND (status = Open)"
        assert result == expected

    def test_merge_both_none(self):
        """Test with both None (edge case)."""
        result = merge_jql_with_scope("", None)
        assert result == ""

    def test_merge_both_empty(self):
        """Test with both empty strings (edge case)."""
        result = merge_jql_with_scope("", "")
        assert result == ""
