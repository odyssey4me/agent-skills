"""Tests for validate_skill script."""

from __future__ import annotations

from scripts.validate_skill import (
    ValidationError,
    validate_skill,
    validate_skill_md,
    validate_skill_script,
)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_str_representation(self):
        """Test string representation of error."""
        error = ValidationError("/path/to/file", "Error message", "error")
        assert str(error) == "[ERROR] /path/to/file: Error message"

    def test_warning_severity(self):
        """Test warning severity."""
        error = ValidationError("/path/to/file", "Warning message", "warning")
        assert "[WARNING]" in str(error)


class TestValidateSkill:
    """Tests for validate_skill function."""

    def test_validate_skill_not_directory(self, tmp_path):
        """Test validation of non-directory."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("content")

        errors = validate_skill(file_path)

        assert len(errors) == 1
        assert "Not a directory" in errors[0].message

    def test_validate_skill_missing_skill_md(self, tmp_path):
        """Test validation with missing SKILL.md."""
        skill_dir = tmp_path / "myskill"
        skill_dir.mkdir()

        errors = validate_skill(skill_dir)

        assert any("SKILL.md not found" in e.message for e in errors)
        assert any("myskill.py not found" in e.message for e in errors)

    def test_validate_skill_valid(self, tmp_path):
        """Test validation of valid skill."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("""# Test Skill

A test skill.

## Authentication

Use a token.

## Setup Verification

Run `python test-skill.py check`

## Commands

### list
List items.

### check
Check requirements.

## Examples

Example usage here.
""")

        # Create skill script
        script = skill_dir / "test-skill.py"
        script.write_text('''#!/usr/bin/env python3
"""Test skill."""

import argparse
import sys


def cmd_check(args):
    """Check requirements."""
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("check", help="Check requirements")
    args = parser.parse_args()
    return 0


if __name__ == "__main__":
    sys.exit(main())
''')

        errors = validate_skill(skill_dir)

        # Should have no errors, possibly some warnings
        error_count = sum(1 for e in errors if e.severity == "error")
        assert error_count == 0


class TestValidateSkillMd:
    """Tests for validate_skill_md function."""

    def test_validate_skill_md_missing_sections(self, tmp_path):
        """Test validation with missing sections."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("# Test\n\nNo sections here.")

        errors = validate_skill_md(skill_md)

        assert any("## Authentication" in e.message for e in errors)
        assert any("## Commands" in e.message for e in errors)

    def test_validate_skill_md_valid(self, tmp_path):
        """Test validation of valid SKILL.md."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""# Test Skill

## Authentication

Token based.

## Commands

### cmd
Do something.

## Examples

Example here.
""")

        errors = validate_skill_md(skill_md)

        error_count = sum(1 for e in errors if e.severity == "error")
        assert error_count == 0

    def test_validate_skill_md_missing_examples_warning(self, tmp_path):
        """Test warning for missing examples section."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""# Test

## Authentication

Token.

## Commands

### cmd
Command.
""")

        errors = validate_skill_md(skill_md)

        assert any("## Examples" in e.message and e.severity == "warning" for e in errors)


class TestValidateSkillScript:
    """Tests for validate_skill_script function."""

    def test_validate_skill_script_missing_docstring(self, tmp_path):
        """Test warning for missing docstring."""
        py_file = tmp_path / "skill.py"
        py_file.write_text("def main():\n    pass\n")

        errors = validate_skill_script(py_file)

        assert any("docstring" in e.message.lower() for e in errors)

    def test_validate_skill_script_missing_check(self, tmp_path):
        """Test warning for missing check command."""
        py_file = tmp_path / "skill.py"
        py_file.write_text('''#!/usr/bin/env python3
"""Module docstring."""

import argparse
import sys


def main() -> None:
    pass
''')

        errors = validate_skill_script(py_file)

        assert any("check" in e.message.lower() for e in errors)

    def test_validate_skill_script_with_shebang(self, tmp_path):
        """Test file with shebang and docstring."""
        py_file = tmp_path / "skill.py"
        py_file.write_text('''#!/usr/bin/env python3
"""Module docstring."""

import argparse
import sys


def cmd_check(args):
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparsers.add_parser("check")
    pass


if __name__ == "__main__":
    main()
''')

        errors = validate_skill_script(py_file)

        # Should not complain about missing docstring
        assert not any("docstring" in e.message.lower() and e.severity == "error" for e in errors)
