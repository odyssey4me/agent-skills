"""Tests for Confluence defaults functionality."""

from __future__ import annotations

from skills.confluence.scripts.confluence import (
    ConfluenceDefaults,
    SpaceDefaults,
    merge_cql_with_scope,
)


class TestConfluenceDefaults:
    """Tests for ConfluenceDefaults dataclass."""

    def test_from_config_empty(self):
        """Test loading from empty config."""
        defaults = ConfluenceDefaults.from_config({})
        assert defaults.cql_scope is None
        assert defaults.max_results is None
        assert defaults.fields is None
        assert defaults.default_space is None

    def test_from_config_full(self):
        """Test loading from full config."""
        config = {
            "defaults": {
                "cql_scope": "type=page AND space=DEMO",
                "max_results": 25,
                "fields": ["title", "space", "version"],
                "default_space": "DEMO",
            }
        }
        defaults = ConfluenceDefaults.from_config(config)
        assert defaults.cql_scope == "type=page AND space=DEMO"
        assert defaults.max_results == 25
        assert defaults.fields == ["title", "space", "version"]
        assert defaults.default_space == "DEMO"

    def test_from_config_partial(self):
        """Test loading with only some defaults configured."""
        config = {
            "defaults": {
                "cql_scope": "type=page",
                "max_results": 10,
            }
        }
        defaults = ConfluenceDefaults.from_config(config)
        assert defaults.cql_scope == "type=page"
        assert defaults.max_results == 10
        assert defaults.fields is None
        assert defaults.default_space is None

    def test_from_config_no_defaults_section(self):
        """Test loading when config has no defaults section."""
        config = {"url": "https://example.atlassian.net"}
        defaults = ConfluenceDefaults.from_config(config)
        assert defaults.cql_scope is None
        assert defaults.max_results is None
        assert defaults.fields is None
        assert defaults.default_space is None

    def test_from_config_only_max_results(self):
        """Test loading with only max_results configured."""
        config = {
            "defaults": {
                "max_results": 50,
            }
        }
        defaults = ConfluenceDefaults.from_config(config)
        assert defaults.cql_scope is None
        assert defaults.max_results == 50
        assert defaults.fields is None
        assert defaults.default_space is None

    def test_from_config_only_cql_scope(self):
        """Test loading with only cql_scope configured."""
        config = {
            "defaults": {
                "cql_scope": "space=PROD AND type=page",
            }
        }
        defaults = ConfluenceDefaults.from_config(config)
        assert defaults.cql_scope == "space=PROD AND type=page"
        assert defaults.max_results is None
        assert defaults.fields is None
        assert defaults.default_space is None


class TestSpaceDefaults:
    """Tests for SpaceDefaults dataclass."""

    def test_from_config_empty(self):
        """Test loading from empty config."""
        defaults = SpaceDefaults.from_config({}, "DEMO")
        assert defaults.default_parent is None
        assert defaults.default_labels is None

    def test_from_config_missing_space(self):
        """Test loading for unconfigured space."""
        config = {"spaces": {"OTHER": {"default_parent": "Parent"}}}
        defaults = SpaceDefaults.from_config(config, "DEMO")
        assert defaults.default_parent is None
        assert defaults.default_labels is None

    def test_from_config_configured_space(self):
        """Test loading for configured space."""
        config = {
            "spaces": {
                "DEMO": {
                    "default_parent": "Parent Page",
                    "default_labels": ["docs", "test"],
                }
            }
        }
        defaults = SpaceDefaults.from_config(config, "DEMO")
        assert defaults.default_parent == "Parent Page"
        assert defaults.default_labels == ["docs", "test"]

    def test_from_config_no_spaces_section(self):
        """Test loading when config has no spaces section."""
        config = {"url": "https://example.atlassian.net"}
        defaults = SpaceDefaults.from_config(config, "DEMO")
        assert defaults.default_parent is None
        assert defaults.default_labels is None

    def test_from_config_multiple_spaces(self):
        """Test loading with multiple spaces configured."""
        config = {
            "spaces": {
                "DEMO": {
                    "default_parent": "Demo Parent",
                    "default_labels": ["demo"],
                },
                "PROD": {
                    "default_parent": "Prod Parent",
                    "default_labels": ["production", "live"],
                },
            }
        }
        demo_defaults = SpaceDefaults.from_config(config, "DEMO")
        prod_defaults = SpaceDefaults.from_config(config, "PROD")

        assert demo_defaults.default_parent == "Demo Parent"
        assert demo_defaults.default_labels == ["demo"]
        assert prod_defaults.default_parent == "Prod Parent"
        assert prod_defaults.default_labels == ["production", "live"]

    def test_from_config_only_parent(self):
        """Test loading with only default_parent configured."""
        config = {
            "spaces": {
                "DEMO": {
                    "default_parent": "Parent Page",
                }
            }
        }
        defaults = SpaceDefaults.from_config(config, "DEMO")
        assert defaults.default_parent == "Parent Page"
        assert defaults.default_labels is None

    def test_from_config_only_labels(self):
        """Test loading with only default_labels configured."""
        config = {
            "spaces": {
                "DEMO": {
                    "default_labels": ["docs", "wiki"],
                }
            }
        }
        defaults = SpaceDefaults.from_config(config, "DEMO")
        assert defaults.default_parent is None
        assert defaults.default_labels == ["docs", "wiki"]


class TestMergeCql:
    """Tests for CQL merging with scope."""

    def test_merge_no_scope(self):
        """Test merge with no scope configured."""
        result = merge_cql_with_scope("type=page", None)
        assert result == "type=page"

    def test_merge_empty_scope(self):
        """Test merge with empty string scope."""
        result = merge_cql_with_scope("type=page", "")
        assert result == "type=page"

    def test_merge_whitespace_scope(self):
        """Test merge with whitespace-only scope."""
        result = merge_cql_with_scope("type=page", "   ")
        assert result == "type=page"

    def test_merge_no_user_cql(self):
        """Test merge with no user CQL."""
        result = merge_cql_with_scope("", "space=DEMO")
        assert result == "space=DEMO"

    def test_merge_whitespace_user_cql(self):
        """Test merge with whitespace-only user CQL."""
        result = merge_cql_with_scope("   ", "space=DEMO")
        assert result == "space=DEMO"

    def test_merge_both_present(self):
        """Test merge with both scope and user CQL."""
        result = merge_cql_with_scope("type=page", "space=DEMO AND creator=currentUser()")
        expected = "(space=DEMO AND creator=currentUser()) AND (type=page)"
        assert result == expected

    def test_merge_preserves_or_precedence(self):
        """Test that parentheses preserve OR operator precedence."""
        result = merge_cql_with_scope("type=page OR type=blogpost", "space=DEMO")
        expected = "(space=DEMO) AND (type=page OR type=blogpost)"
        assert result == expected

    def test_merge_complex_user_query(self):
        """Test with complex user query."""
        result = merge_cql_with_scope("type=page AND (title~draft OR title~test)", "space=DEMO")
        expected = "(space=DEMO) AND (type=page AND (title~draft OR title~test))"
        assert result == expected

    def test_merge_complex_scope(self):
        """Test with complex scope."""
        result = merge_cql_with_scope(
            "type=page",
            "space=DEMO AND creator=currentUser() AND created >= now('-30d')",
        )
        expected = (
            "(space=DEMO AND creator=currentUser() AND created >= now('-30d')) " "AND (type=page)"
        )
        assert result == expected

    def test_merge_both_none(self):
        """Test with both None (edge case)."""
        result = merge_cql_with_scope("", None)
        assert result == ""

    def test_merge_both_empty(self):
        """Test with both empty strings (edge case)."""
        result = merge_cql_with_scope("", "")
        assert result == ""

    def test_merge_case_sensitive(self):
        """Test that CQL merging preserves case."""
        result = merge_cql_with_scope("Type=Page", "Space=DEMO")
        expected = "(Space=DEMO) AND (Type=Page)"
        assert result == expected

    def test_merge_with_special_characters(self):
        """Test merge with special characters in queries."""
        result = merge_cql_with_scope('title~"test page"', "space=DEMO")
        expected = '(space=DEMO) AND (title~"test page")'
        assert result == expected

    def test_merge_with_functions(self):
        """Test merge with CQL functions."""
        result = merge_cql_with_scope(
            "created >= now('-7d')", "space=DEMO AND creator=currentUser()"
        )
        expected = "(space=DEMO AND creator=currentUser()) AND (created >= now('-7d'))"
        assert result == expected

    def test_merge_simple_queries(self):
        """Test merge with simple queries."""
        result = merge_cql_with_scope("title~login", "space=DEMO")
        expected = "(space=DEMO) AND (title~login)"
        assert result == expected
