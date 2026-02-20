"""Tests for generate_registry script."""

from __future__ import annotations

import json
from unittest.mock import patch

from scripts.generate_registry import (
    build_registry,
    determine_auth,
    determine_dependencies,
    determine_type,
    main,
    parse_frontmatter,
)


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_valid_frontmatter(self, tmp_path):
        """Test parsing valid YAML frontmatter."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: test
description: A test skill
metadata:
  author: tester
  version: "0.1.0"
---

# Test
""")
        result = parse_frontmatter(skill_md)
        assert result is not None
        assert result["name"] == "test"
        assert result["description"] == "A test skill"

    def test_missing_frontmatter(self, tmp_path):
        """Test file without frontmatter."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("# Test\nNo frontmatter here.")
        result = parse_frontmatter(skill_md)
        assert result is None

    def test_unclosed_frontmatter(self, tmp_path):
        """Test file with unclosed frontmatter."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\nname: test\n# No closing marker")
        result = parse_frontmatter(skill_md)
        assert result is None

    def test_invalid_yaml(self, tmp_path):
        """Test file with invalid YAML in frontmatter."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\n: invalid: yaml: [unclosed\n---\n")
        result = parse_frontmatter(skill_md)
        assert result is None


class TestDetermineType:
    """Tests for determine_type function."""

    def test_api_skill_with_scripts(self, tmp_path):
        """Test detection of API skill with scripts directory."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "myskill.py").write_text("# script")
        (skill_dir / "SKILL.md").write_text("""---
name: myskill
description: test
---
""")
        assert determine_type(skill_dir) == "api"

    def test_cli_skill_without_scripts(self, tmp_path):
        """Test detection of CLI skill without scripts directory."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: myskill
description: test
---
""")
        assert determine_type(skill_dir) == "cli"

    def test_workflow_skill_from_metadata(self, tmp_path):
        """Test detection of workflow skill from metadata type field."""
        skill_dir = tmp_path / "myworkflow"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: myworkflow
description: test
metadata:
  type: workflow
---
""")
        assert determine_type(skill_dir) == "workflow"

    def test_scripts_dir_with_only_init(self, tmp_path):
        """Test scripts dir containing only __init__.py is treated as CLI."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "__init__.py").write_text("")
        (skill_dir / "SKILL.md").write_text("""---
name: myskill
description: test
---
""")
        assert determine_type(skill_dir) == "cli"


class TestDetermineAuth:
    """Tests for determine_auth function."""

    def test_oauth_detection(self, tmp_path):
        """Test OAuth detection from SKILL.md content."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\nUses OAuth for authentication.\n")
        assert determine_auth(skill_dir) == "oauth"

    def test_api_token_detection(self, tmp_path):
        """Test API token detection."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\nRequires an API token.\n")
        assert determine_auth(skill_dir) == "api-token"

    def test_cli_auth_gh(self, tmp_path):
        """Test gh auth detection."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\nRun `gh auth login`.\n")
        assert determine_auth(skill_dir) == "cli-auth"

    def test_cli_auth_glab(self, tmp_path):
        """Test glab auth detection."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\nRun `glab auth login`.\n")
        assert determine_auth(skill_dir) == "cli-auth"

    def test_no_auth(self, tmp_path):
        """Test no auth detection."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\nNo authentication needed.\n")
        assert determine_auth(skill_dir) == "none"

    def test_missing_skill_md(self, tmp_path):
        """Test missing SKILL.md returns none."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        assert determine_auth(skill_dir) == "none"


class TestDetermineDependencies:
    """Tests for determine_dependencies function."""

    def test_requires_from_metadata(self, tmp_path):
        """Test dependencies from requires metadata field."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: myskill
description: test
metadata:
  requires: [github, gitlab]
---
""")
        deps = determine_dependencies(skill_dir)
        assert deps == ["github", "gitlab"]

    def test_pip_dependencies(self, tmp_path):
        """Test pip dependency detection from install instructions."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: myskill
description: test
---
pip install requests keyring pyyaml
""")
        deps = determine_dependencies(skill_dir)
        assert "requests" in deps
        assert "keyring" in deps
        assert "pyyaml" in deps

    def test_gh_dependency(self, tmp_path):
        """Test gh CLI dependency detection."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: myskill
description: test
---
brew install gh
sudo apt install gh
""")
        deps = determine_dependencies(skill_dir)
        assert "gh" in deps

    def test_missing_skill_md(self, tmp_path):
        """Test missing SKILL.md returns empty list."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()
        assert determine_dependencies(skill_dir) == []


class TestBuildRegistry:
    """Tests for build_registry function."""

    def test_build_registry_single_skill(self, tmp_path):
        """Test building registry with one skill."""
        skills_root = tmp_path / "skills"
        skills_root.mkdir()

        skill_dir = skills_root / "myskill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: myskill
description: A test skill
metadata:
  author: tester
  version: "0.1.0"
  category: testing
  tags: [test, demo]
  complexity: standard
license: MIT
---

# My Skill

## Authentication

API token.

## Commands

### check
Check.
""")

        registry = build_registry(skills_root)
        assert "$schema" in registry
        assert len(registry["skills"]) == 1

        skill = registry["skills"][0]
        assert skill["name"] == "myskill"
        assert skill["description"] == "A test skill"
        assert skill["version"] == "0.1.0"
        assert skill["category"] == "testing"
        assert skill["tags"] == ["test", "demo"]
        assert skill["complexity"] == "standard"

    def test_build_registry_skips_non_directories(self, tmp_path):
        """Test that non-directory entries are skipped."""
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        (skills_root / "README.md").write_text("# Skills")

        registry = build_registry(skills_root)
        assert len(registry["skills"]) == 0

    def test_build_registry_skips_missing_skill_md(self, tmp_path):
        """Test that directories without SKILL.md are skipped."""
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        (skills_root / "empty").mkdir()

        registry = build_registry(skills_root)
        assert len(registry["skills"]) == 0

    def test_build_registry_multiple_skills_sorted(self, tmp_path):
        """Test that skills are sorted alphabetically."""
        skills_root = tmp_path / "skills"
        skills_root.mkdir()

        for name in ["zeta", "alpha", "middle"]:
            d = skills_root / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"""---
name: {name}
description: Skill {name}
---
""")

        registry = build_registry(skills_root)
        names = [s["name"] for s in registry["skills"]]
        assert names == ["alpha", "middle", "zeta"]

    def test_build_registry_with_real_skills(self):
        """Test building registry from actual skills directory."""
        from pathlib import Path

        skills_root = Path(__file__).resolve().parent.parent / "skills"
        if not skills_root.exists():
            return  # Skip if running outside repo

        registry = build_registry(skills_root)
        assert len(registry["skills"]) >= 11  # At least the original 11 skills

        # Verify all skills have required fields
        for skill in registry["skills"]:
            assert "name" in skill
            assert "description" in skill
            assert "version" in skill
            assert "category" in skill
            assert "type" in skill

    def test_registry_matches_committed_file(self):
        """Test that generated registry matches the committed skills.json."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        skills_json = repo_root / "skills.json"
        skills_root = repo_root / "skills"

        if not skills_json.exists() or not skills_root.exists():
            return  # Skip if running outside repo

        registry = build_registry(skills_root)
        generated = json.dumps(registry, indent=2) + "\n"
        committed = skills_json.read_text()

        assert (
            generated == committed
        ), "skills.json is out of date. Run 'python scripts/generate_registry.py' to update."


class TestMain:
    """Tests for main entry point."""

    def test_main_check_up_to_date(self):
        """Test --check mode when skills.json is up to date."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        if not (repo_root / "skills.json").exists():
            return

        with patch("sys.argv", ["generate_registry.py", "--check"]):
            exit_code = main()
        assert exit_code == 0

    def test_main_check_out_of_date(self, tmp_path):
        """Test --check mode when skills.json is out of date."""
        # Create a minimal repo structure
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "generate_registry.py").write_text("")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill = skills_dir / "testskill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("""---
name: testskill
description: A test
---
""")

        # Create an outdated skills.json
        (tmp_path / "skills.json").write_text('{"old": "data"}\n')

        import scripts.generate_registry as mod

        original_file = mod.__file__
        try:
            mod.__file__ = str(scripts_dir / "generate_registry.py")
            with patch("sys.argv", ["generate_registry.py", "--check"]):
                exit_code = main()
            assert exit_code == 1
        finally:
            mod.__file__ = original_file

    def test_main_check_missing_file(self, tmp_path):
        """Test --check mode when skills.json does not exist."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "generate_registry.py").write_text("")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        import scripts.generate_registry as mod

        original_file = mod.__file__
        try:
            mod.__file__ = str(scripts_dir / "generate_registry.py")
            with patch("sys.argv", ["generate_registry.py", "--check"]):
                exit_code = main()
            assert exit_code == 1
        finally:
            mod.__file__ = original_file

    def test_main_missing_skills_dir(self, tmp_path):
        """Test main when skills directory does not exist."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "generate_registry.py").write_text("")

        import scripts.generate_registry as mod

        original_file = mod.__file__
        try:
            mod.__file__ = str(scripts_dir / "generate_registry.py")
            with patch("sys.argv", ["generate_registry.py"]):
                exit_code = main()
            assert exit_code == 1
        finally:
            mod.__file__ = original_file

    def test_main_generate_output(self, tmp_path):
        """Test generating skills.json to custom output path."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "generate_registry.py").write_text("")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill = skills_dir / "testskill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("""---
name: testskill
description: Test skill
metadata:
  version: "0.1.0"
  category: testing
  tags: [test]
  complexity: standard
---
""")

        import scripts.generate_registry as mod

        original_file = mod.__file__
        try:
            mod.__file__ = str(scripts_dir / "generate_registry.py")
            with patch(
                "sys.argv",
                ["generate_registry.py", "--output", "skills.json"],
            ):
                exit_code = main()
            assert exit_code == 0
            assert (tmp_path / "skills.json").exists()
        finally:
            mod.__file__ = original_file
