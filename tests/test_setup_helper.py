"""Tests for setup_helper script."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.setup_helper import (
    ClaudeMdConfig,
    SkillInfo,
    find_skill_installations,
    generate_claude_md_content,
    parse_claude_md,
    parse_skill_description,
    update_claude_md_section,
)


class TestSkillInfo:
    """Tests for SkillInfo dataclass."""

    def test_skill_info_creation(self, tmp_path):
        """Test creating a SkillInfo instance."""
        skill_path = tmp_path / "jira"
        skill_path.mkdir()
        skill_md = skill_path / "SKILL.md"
        skill_script = skill_path / "jira.py"

        skill_info = SkillInfo(
            name="jira",
            path=skill_path,
            skill_md=skill_md,
            script=skill_script,
            description="Jira integration",
        )

        assert skill_info.name == "jira"
        assert skill_info.path == skill_path
        assert skill_info.skill_md == skill_md
        assert skill_info.script == skill_script
        assert skill_info.description == "Jira integration"


class TestClaudeMdConfig:
    """Tests for ClaudeMdConfig dataclass."""

    def test_claude_md_config_creation(self, tmp_path):
        """Test creating a ClaudeMdConfig instance."""
        claude_md = tmp_path / "CLAUDE.md"

        config = ClaudeMdConfig(
            path=claude_md,
            exists=True,
            content="# Global Agent Skills",
            configured_skills=["jira"],
        )

        assert config.path == claude_md
        assert config.exists is True
        assert "Global Agent Skills" in config.content
        assert "jira" in config.configured_skills


class TestParseSkillDescription:
    """Tests for parse_skill_description function."""

    def test_parse_description_basic(self, tmp_path):
        """Test parsing basic skill description."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(
            """# Jira Integration

Interact with Jira for issue tracking and workflow management.

## Authentication
"""
        )

        description = parse_skill_description(skill_md)

        assert description == "Interact with Jira for issue tracking and workflow management."

    def test_parse_description_with_empty_lines(self, tmp_path):
        """Test parsing description with empty lines after heading."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(
            """# Jira Integration


Manage Jira issues and workflows.

## Authentication
"""
        )

        description = parse_skill_description(skill_md)

        assert description == "Manage Jira issues and workflows."

    def test_parse_description_fallback(self, tmp_path):
        """Test fallback when parsing fails."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("# Title\n\n## Section\n")

        description = parse_skill_description(skill_md)

        # Should return fallback
        assert description == "Agent skill"

    def test_parse_description_missing_file(self, tmp_path):
        """Test parsing when file doesn't exist."""
        skill_md = tmp_path / "nonexistent.md"

        description = parse_skill_description(skill_md)

        assert description == "Agent skill"


class TestFindSkillInstallations:
    """Tests for find_skill_installations function."""

    def test_find_no_skills(self, tmp_path, monkeypatch):
        """Test when no skills are found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Change to tmp_path so ./skills/ doesn't interfere
        monkeypatch.chdir(tmp_path)

        discovered = find_skill_installations([str(empty_dir)])

        assert len(discovered) == 0

    def test_find_single_skill(self, tmp_path, monkeypatch):
        """Test finding a single skill."""
        # Change to tmp_path so ./skills/ doesn't interfere
        monkeypatch.chdir(tmp_path)

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        jira_dir = skills_dir / "jira"
        jira_dir.mkdir()

        skill_md = jira_dir / "SKILL.md"
        skill_md.write_text("# Jira\n\nJira integration skill.")

        skill_script = jira_dir / "jira.py"
        skill_script.write_text("# Jira skill script")

        discovered = find_skill_installations([str(skills_dir)])

        assert len(discovered) == 1
        assert skills_dir in discovered
        assert len(discovered[skills_dir]) == 1
        assert discovered[skills_dir][0].name == "jira"
        assert discovered[skills_dir][0].description == "Jira integration skill."

    def test_find_multiple_skills(self, tmp_path, monkeypatch):
        """Test finding multiple skills."""
        # Change to tmp_path so ./skills/ doesn't interfere
        monkeypatch.chdir(tmp_path)

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create jira skill
        jira_dir = skills_dir / "jira"
        jira_dir.mkdir()
        (jira_dir / "SKILL.md").write_text("# Jira\n\nJira skill.")
        (jira_dir / "jira.py").write_text("# Script")

        # Create github skill
        github_dir = skills_dir / "github"
        github_dir.mkdir()
        (github_dir / "SKILL.md").write_text("# GitHub\n\nGitHub skill.")
        (github_dir / "github.py").write_text("# Script")

        discovered = find_skill_installations([str(skills_dir)])

        assert len(discovered) == 1
        assert len(discovered[skills_dir]) == 2

        skill_names = {s.name for s in discovered[skills_dir]}
        assert skill_names == {"jira", "github"}

    def test_find_skill_missing_script(self, tmp_path, monkeypatch):
        """Test that skills without scripts are skipped."""
        # Change to tmp_path so ./skills/ doesn't interfere
        monkeypatch.chdir(tmp_path)

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        incomplete_dir = skills_dir / "incomplete"
        incomplete_dir.mkdir()
        (incomplete_dir / "SKILL.md").write_text("# Incomplete\n\nNo script.")
        # No .py script created

        discovered = find_skill_installations([str(skills_dir)])

        # Should not find the incomplete skill
        assert len(discovered) == 0

    def test_find_skill_wrong_script_name(self, tmp_path, monkeypatch):
        """Test that skills with wrong script name are skipped."""
        # Change to tmp_path so ./skills/ doesn't interfere
        monkeypatch.chdir(tmp_path)

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        wrong_dir = skills_dir / "myskill"
        wrong_dir.mkdir()
        (wrong_dir / "SKILL.md").write_text("# Skill\n\nDescription.")
        (wrong_dir / "wrong_name.py").write_text("# Wrong name")
        # Script should be myskill.py, not wrong_name.py

        discovered = find_skill_installations([str(skills_dir)])

        assert len(discovered) == 0


class TestParseClaudeMd:
    """Tests for parse_claude_md function."""

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing non-existent CLAUDE.md."""
        claude_md = tmp_path / "CLAUDE.md"

        config = parse_claude_md(claude_md)

        assert config.path == claude_md
        assert config.exists is False
        assert config.content == ""
        assert config.configured_skills == []

    def test_parse_permission_error(self, tmp_path):
        """Test parsing when file cannot be read."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("content")
        claude_md.chmod(0o000)  # Remove all permissions

        try:
            config = parse_claude_md(claude_md)

            # Should handle permission error gracefully
            assert config.exists is True
            assert config.content == ""
            assert config.configured_skills == []
        finally:
            claude_md.chmod(0o644)  # Restore permissions for cleanup

    def test_parse_empty_file(self, tmp_path):
        """Test parsing empty CLAUDE.md."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("")

        config = parse_claude_md(claude_md)

        assert config.exists is True
        assert config.content == ""
        assert config.configured_skills == []

    def test_parse_with_skills(self, tmp_path):
        """Test parsing CLAUDE.md with configured skills."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            """# Global Agent Skills

## Available Skills

- **Jira**: Issue tracking - read ~/.claude/skills/jira/SKILL.md
- **GitHub**: Repository management - read ~/.claude/skills/github/SKILL.md
"""
        )

        config = parse_claude_md(claude_md)

        assert config.exists is True
        assert len(config.configured_skills) == 2
        assert "jira" in config.configured_skills
        assert "github" in config.configured_skills

    def test_parse_case_insensitive(self, tmp_path):
        """Test that parsing is case-insensitive."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            """# Skills

- **JIRA**: Issue tracking - READ ~/.claude/skills/jira/skill.md
"""
        )

        config = parse_claude_md(claude_md)

        assert "jira" in config.configured_skills

    def test_parse_with_varied_formatting(self, tmp_path):
        """Test parsing with different formatting variations."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            """# Skills

- **Jira**: Description - read /path/to/SKILL.md
- **GitHub**: No spaces - read /other/SKILL.md
"""
        )

        config = parse_claude_md(claude_md)

        assert len(config.configured_skills) == 2
        assert "jira" in config.configured_skills
        assert "github" in config.configured_skills


class TestValidateClaudeMdContent:
    """Tests for validate_claude_md_content function."""

    def test_validate_venv_activation(self):
        """Test detection of venv activation patterns."""
        from scripts.setup_helper import validate_claude_md_content

        content = """# Skills

## Running Scripts

```bash
source .venv/bin/activate
python skills/jira/jira.py check
```
"""
        warnings = validate_claude_md_content(content)

        assert len(warnings) > 0
        assert any("venv activation" in w for w in warnings)

    def test_validate_cd_commands(self):
        """Test detection of cd commands."""
        from scripts.setup_helper import validate_claude_md_content

        content = """# Skills

## Running Scripts

```bash
cd /path/to/agent-skills && python skills/jira/jira.py
```
"""
        warnings = validate_claude_md_content(content)

        assert len(warnings) > 0
        assert any("'cd' commands" in w for w in warnings)

    def test_validate_scripts_subdirectory(self):
        """Test detection of old scripts/ subdirectory structure."""
        from scripts.setup_helper import validate_claude_md_content

        content = """# Skills

```bash
python skills/jira/scripts/search.py
```
"""
        warnings = validate_claude_md_content(content)

        assert len(warnings) > 0
        assert any("scripts/" in w for w in warnings)

    def test_validate_missing_guidance(self):
        """Test detection of missing 'run directly' guidance."""
        from scripts.setup_helper import validate_claude_md_content

        content = """# Skills

## Running Scripts

Some other instructions here.
"""
        warnings = validate_claude_md_content(content)

        assert len(warnings) > 0
        assert any("Always run skill scripts directly" in w for w in warnings)

    def test_validate_correct_content(self):
        """Test that correct content has no warnings."""
        from scripts.setup_helper import validate_claude_md_content

        content = """# Global Agent Skills

Skills are available at ~/.claude/skills

## Available Skills

- **Jira**: Issue tracking - read ~/.claude/skills/jira/SKILL.md

## Running Scripts

Always run skill scripts directly:

```bash
python ~/.claude/skills/jira/jira.py check
```

## Skill Invocation

Use `/jira` or describe naturally:
- "Search Jira for my open issues"
"""
        warnings = validate_claude_md_content(content)

        assert len(warnings) == 0

    def test_validate_multiple_issues(self):
        """Test detection of multiple issues."""
        from scripts.setup_helper import validate_claude_md_content

        content = """# Skills

## Running Scripts

```bash
cd /home/user/agent-skills && source .venv/bin/activate
python skills/jira/scripts/search.py
```
"""
        warnings = validate_claude_md_content(content)

        # Should catch venv, cd, and scripts/ subdirectory
        assert len(warnings) >= 3


class TestGenerateClaudeMdContent:
    """Tests for generate_claude_md_content function."""

    def test_generate_empty_skills(self, tmp_path):
        """Test generating content with no skills."""
        content = generate_claude_md_content(tmp_path, [])

        assert "# Global Agent Skills" in content
        assert f"Skills are available at {tmp_path}" in content

    def test_generate_single_skill(self, tmp_path):
        """Test generating content with a single skill."""
        skill_dir = tmp_path / "jira"
        skill_info = SkillInfo(
            name="jira",
            path=skill_dir,
            skill_md=skill_dir / "SKILL.md",
            script=skill_dir / "jira.py",
            description="Jira integration skill",
        )

        content = generate_claude_md_content(tmp_path, [skill_info])

        assert "# Global Agent Skills" in content
        assert "## Available Skills" in content
        assert "**Jira**: Jira integration skill" in content
        assert "## Running Scripts" in content
        assert "## Skill Invocation" in content
        assert "Use `/jira`" in content

    def test_generate_multiple_skills_sorted(self, tmp_path):
        """Test that skills are sorted alphabetically."""
        skills = [
            SkillInfo(
                name="github",
                path=tmp_path / "github",
                skill_md=tmp_path / "github" / "SKILL.md",
                script=tmp_path / "github" / "github.py",
                description="GitHub skill",
            ),
            SkillInfo(
                name="jira",
                path=tmp_path / "jira",
                skill_md=tmp_path / "jira" / "SKILL.md",
                script=tmp_path / "jira" / "jira.py",
                description="Jira skill",
            ),
            SkillInfo(
                name="confluence",
                path=tmp_path / "confluence",
                skill_md=tmp_path / "confluence" / "SKILL.md",
                script=tmp_path / "confluence" / "confluence.py",
                description="Confluence skill",
            ),
        ]

        content = generate_claude_md_content(tmp_path, skills)

        # Check that skills appear in alphabetical order
        lines = content.split("\n")
        skill_lines = [l for l in lines if l.strip().startswith("- **")]

        assert len(skill_lines) == 3
        assert "**Confluence**" in skill_lines[0]
        assert "**Github**" in skill_lines[1]  # title() makes it Github not GitHub
        assert "**Jira**" in skill_lines[2]


class TestUpdateClaudeMdSection:
    """Tests for update_claude_md_section function."""

    def test_update_existing_section(self, tmp_path):
        """Test updating existing Available Skills section."""
        existing_content = """# Global Agent Skills

## Available Skills

- **OldSkill**: Old description - read /old/SKILL.md

## Other Section

Some content here.
"""

        skill_info = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="New skill",
        )

        updated = update_claude_md_section(existing_content, [skill_info])

        assert "**Jira**: New skill" in updated
        assert "**OldSkill**" not in updated
        assert "## Other Section" in updated
        assert "Some content here." in updated

    def test_update_no_skills_section(self, tmp_path):
        """Test adding skills section when it doesn't exist."""
        existing_content = """# Global Agent Skills

Some intro text.

## Other Section

Content.
"""

        skill_info = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="Jira skill",
        )

        updated = update_claude_md_section(existing_content, [skill_info])

        assert "## Available Skills" in updated
        assert "**Jira**: Jira skill" in updated

    def test_update_preserves_other_content(self, tmp_path):
        """Test that updating preserves other content."""
        existing_content = """# Global Agent Skills

## Available Skills

- **Old**: Old - read /old/SKILL.md

## Running Scripts

Custom instructions here.

## Custom Section

Important content.
"""

        skill_info = SkillInfo(
            name="new",
            path=tmp_path / "new",
            skill_md=tmp_path / "new" / "SKILL.md",
            script=tmp_path / "new" / "new.py",
            description="New skill",
        )

        updated = update_claude_md_section(existing_content, [skill_info])

        # New skill should be present
        assert "**New**: New skill" in updated

        # Other sections should be preserved
        assert "## Running Scripts" in updated
        assert "Custom instructions here." in updated
        assert "## Custom Section" in updated
        assert "Important content." in updated

    def test_update_fallback_append(self, tmp_path):
        """Test fallback behavior when no Agent Skills header found."""
        existing_content = """# My Config

Some random content.
"""

        skill_info = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="Jira skill",
        )

        updated = update_claude_md_section(existing_content, [skill_info])

        # Should append skills section at the end
        assert "## Available Skills" in updated
        assert "**Jira**: Jira skill" in updated
        assert "# My Config" in updated


class TestShowCurrentConfig:
    """Tests for show_current_config function."""

    def test_show_with_no_skills(self, tmp_path, capsys):
        """Test showing config when no skills are found."""
        from scripts.setup_helper import show_current_config

        claude_md = tmp_path / "CLAUDE.md"
        config = ClaudeMdConfig(
            path=claude_md,
            exists=False,
            content="",
            configured_skills=[],
        )

        show_current_config({}, config)

        captured = capsys.readouterr()
        assert "Current Configuration" in captured.out
        assert "not found" in captured.out
        assert "No skills found" in captured.out

    def test_show_with_skills_and_config(self, tmp_path, capsys):
        """Test showing config with skills and CLAUDE.md."""
        from scripts.setup_helper import show_current_config

        claude_md = tmp_path / "CLAUDE.md"
        skill_info = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="Jira skill",
        )

        config = ClaudeMdConfig(
            path=claude_md,
            exists=True,
            content="# Skills",
            configured_skills=["jira"],
        )

        discovered = {tmp_path: [skill_info]}

        show_current_config(discovered, config)

        captured = capsys.readouterr()
        assert "exists" in captured.out
        assert "jira" in captured.out
        assert "Configured skills" in captured.out
        assert "✓" in captured.out  # Checkmark for configured skill


class TestUpdateClaudeMd:
    """Tests for update_claude_md function."""

    def test_update_with_no_skills(self, tmp_path, capsys):
        """Test updating with no skills."""
        from scripts.setup_helper import update_claude_md

        config = ClaudeMdConfig(
            path=tmp_path / "CLAUDE.md",
            exists=False,
            content="",
            configured_skills=[],
        )

        result = update_claude_md(config, [], dry_run=True)

        assert result is False
        captured = capsys.readouterr()
        assert "No skills to configure" in captured.err

    def test_update_dry_run(self, tmp_path, capsys):
        """Test update in dry-run mode."""
        from scripts.setup_helper import update_claude_md

        skill_info = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="Jira skill",
        )

        config = ClaudeMdConfig(
            path=tmp_path / "CLAUDE.md",
            exists=False,
            content="",
            configured_skills=[],
        )

        result = update_claude_md(config, [skill_info], dry_run=True)

        assert result is True
        captured = capsys.readouterr()
        assert "Dry run" in captured.out
        assert "would write to" in captured.out
        # File should not actually be created
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_update_auto_mode(self, tmp_path, capsys):
        """Test update in auto mode (no confirmation)."""
        from scripts.setup_helper import update_claude_md

        skill_info = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="Jira skill",
        )

        config = ClaudeMdConfig(
            path=tmp_path / "CLAUDE.md",
            exists=False,
            content="",
            configured_skills=[],
        )

        result = update_claude_md(config, [skill_info], auto=True)

        assert result is True
        captured = capsys.readouterr()
        assert "Written to" in captured.out
        # File should be created
        assert (tmp_path / "CLAUDE.md").exists()
        content = (tmp_path / "CLAUDE.md").read_text()
        assert "**Jira**" in content

    def test_update_permission_error(self, tmp_path, capsys):
        """Test update when file cannot be written."""
        from scripts.setup_helper import update_claude_md

        skill_info = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="Jira skill",
        )

        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        config = ClaudeMdConfig(
            path=readonly_dir / "CLAUDE.md",
            exists=False,
            content="",
            configured_skills=[],
        )

        try:
            result = update_claude_md(config, [skill_info], auto=True)

            assert result is False
            captured = capsys.readouterr()
            assert "Error" in captured.err
            assert "Could not write" in captured.err
        finally:
            readonly_dir.chmod(0o755)  # Restore permissions for cleanup


class TestInteractiveSetup:
    """Tests for interactive_setup function."""

    def test_interactive_no_skills(self, tmp_path, monkeypatch, capsys):
        """Test interactive setup when no skills are found."""
        from scripts.setup_helper import interactive_setup

        # Change to tmp_path so ./skills/ doesn't interfere
        monkeypatch.chdir(tmp_path)

        result = interactive_setup(custom_paths=[str(tmp_path / "empty")])

        assert result == 1  # Exit code for no skills found
        captured = capsys.readouterr()
        assert "No skills found" in captured.out
        assert "Install skills first" in captured.out

    def test_interactive_skills_already_configured(self, tmp_path, monkeypatch, capsys):
        """Test when all skills are already configured."""
        from scripts.setup_helper import interactive_setup

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        # Create a skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        jira_dir = skills_dir / "jira"
        jira_dir.mkdir()
        (jira_dir / "SKILL.md").write_text("# Jira\n\nJira skill.")
        (jira_dir / "jira.py").write_text("# Script")

        # Create CLAUDE.md with skill already configured
        claude_md = tmp_path / "test_claude.md"
        claude_md.write_text(
            """# Global Agent Skills

## Available Skills

- **Jira**: Jira skill - read /path/to/SKILL.md
"""
        )

        result = interactive_setup(
            custom_paths=[str(skills_dir)],
            claude_md_path=claude_md,
        )

        assert result == 0
        captured = capsys.readouterr()
        assert "All discovered skills are already configured" in captured.out


class TestGetSearchLocations:
    """Tests for get_search_locations function."""

    def test_get_search_locations_with_custom_paths(self):
        """Test search locations with custom paths."""
        from scripts.setup_helper import get_search_locations

        custom = ["/custom/path1", "/custom/path2"]
        locations = get_search_locations(custom)

        # Custom paths should be first
        assert str(locations[0]) == "/custom/path1"
        assert str(locations[1]) == "/custom/path2"

    def test_get_search_locations_with_env_var(self, monkeypatch):
        """Test search locations with environment variable."""
        from scripts.setup_helper import get_search_locations

        monkeypatch.setenv("AGENT_SKILLS_PATH", "/env/path")

        locations = get_search_locations()

        # Env var should be included
        assert any(str(loc) == "/env/path" for loc in locations)

    def test_get_search_locations_default(self):
        """Test default search locations."""
        from scripts.setup_helper import get_search_locations

        locations = get_search_locations()

        # Should have standard locations
        assert any(".claude/skills" in str(loc) for loc in locations)
        assert any(".local/share/agent-skills/skills" in str(loc) for loc in locations)


class TestIntegration:
    """Integration tests for setup_helper."""

    def test_end_to_end_skill_discovery_and_generation(self, tmp_path, monkeypatch):
        """Test complete workflow from discovery to generation."""
        # Change to tmp_path so ./skills/ doesn't interfere
        monkeypatch.chdir(tmp_path)

        # Setup: Create skills directory with skills
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        jira_dir = skills_dir / "jira"
        jira_dir.mkdir()
        (jira_dir / "SKILL.md").write_text("# Jira\n\nJira integration.")
        (jira_dir / "jira.py").write_text("#!/usr/bin/env python3\n")

        # Discover skills
        discovered = find_skill_installations([str(skills_dir)])

        assert len(discovered) == 1
        assert len(discovered[skills_dir]) == 1

        # Generate CLAUDE.md content
        skills = discovered[skills_dir]
        content = generate_claude_md_content(skills_dir, skills)

        # Verify generated content
        assert "# Global Agent Skills" in content
        assert "**Jira**: Jira integration." in content
        assert str(jira_dir / "SKILL.md") in content

    def test_parse_and_update_workflow(self, tmp_path):
        """Test parsing existing CLAUDE.md and updating it."""
        # Create existing CLAUDE.md
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            """# Global Agent Skills

## Available Skills

- **Jira**: Old description - read /old/jira/SKILL.md

## Custom Section

Keep this content.
"""
        )

        # Parse existing
        config = parse_claude_md(claude_md)
        assert "jira" in config.configured_skills

        # Create new skill info
        new_skill = SkillInfo(
            name="jira",
            path=tmp_path / "jira",
            skill_md=tmp_path / "jira" / "SKILL.md",
            script=tmp_path / "jira" / "jira.py",
            description="Updated Jira skill",
        )

        # Update content
        updated = update_claude_md_section(config.content, [new_skill])

        # Verify update
        assert "Updated Jira skill" in updated
        assert "Old description" not in updated
        assert "## Custom Section" in updated
        assert "Keep this content." in updated
