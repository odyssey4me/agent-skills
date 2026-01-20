#!/usr/bin/env python3
"""Validate skill structure and requirements.

Usage:
    python scripts/validate_skill.py skills/*
    python scripts/validate_skill.py skills/jira

Examples:
    python scripts/validate_skill.py skills/jira
    python scripts/validate_skill.py skills/*
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


class ValidationError:
    """Represents a validation error."""

    def __init__(self, path: str, message: str, severity: str = "error"):
        self.path = path
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.path}: {self.message}"


def validate_skill(skill_dir: Path) -> list[ValidationError]:
    """Validate a skill directory structure.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        List of validation errors.
    """
    errors: list[ValidationError] = []

    if not skill_dir.is_dir():
        errors.append(ValidationError(str(skill_dir), "Not a directory"))
        return errors

    skill_name = skill_dir.name

    # Check SKILL.md exists
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(ValidationError(str(skill_md), "SKILL.md not found"))
    else:
        errors.extend(validate_skill_md(skill_md))

    # Check scripts directory exists
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        errors.append(ValidationError(str(scripts_dir), "scripts/ directory not found", "warning"))
    elif not scripts_dir.is_dir():
        errors.append(ValidationError(str(scripts_dir), "scripts/ is not a directory"))
    else:
        errors.extend(validate_scripts(scripts_dir, skill_name))

    return errors


def validate_skill_md(skill_md: Path) -> list[ValidationError]:
    """Validate SKILL.md content.

    Args:
        skill_md: Path to SKILL.md file.

    Returns:
        List of validation errors.
    """
    errors: list[ValidationError] = []
    content = skill_md.read_text()

    # Check for required sections
    required_sections = ["# ", "## Authentication", "## Commands"]
    for section in required_sections:
        if section not in content:
            errors.append(ValidationError(str(skill_md), f"Missing required section: {section}"))

    # Check for examples section (warning only)
    if "## Examples" not in content:
        errors.append(ValidationError(str(skill_md), "Missing ## Examples section", "warning"))

    return errors


def validate_scripts(scripts_dir: Path, _skill_name: str) -> list[ValidationError]:
    """Validate scripts in a skill.

    Args:
        scripts_dir: Path to scripts directory.
        _skill_name: Name of the skill (reserved for future use).

    Returns:
        List of validation errors.
    """
    errors: list[ValidationError] = []

    python_files = list(scripts_dir.glob("*.py"))
    if not python_files:
        errors.append(ValidationError(str(scripts_dir), "No Python scripts found", "warning"))
        return errors

    for py_file in python_files:
        if py_file.name == "__init__.py":
            continue
        errors.extend(validate_python_file(py_file))

    return errors


def validate_python_file(py_file: Path) -> list[ValidationError]:
    """Validate a Python script file.

    Args:
        py_file: Path to Python file.

    Returns:
        List of validation errors.
    """
    errors: list[ValidationError] = []
    content = py_file.read_text()

    # Check for docstring
    if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
        # Could have shebang or encoding first
        lines = content.split("\n")
        has_docstring = False
        for line in lines[:5]:  # Check first 5 lines
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                has_docstring = True
                break
        if not has_docstring:
            errors.append(ValidationError(str(py_file), "Missing module docstring", "warning"))

    # Check for main guard
    if "__name__" in content and "__main__" in content:
        pass  # Has main guard
    elif "def main" in content or "def run" in content:
        errors.append(
            ValidationError(str(py_file), "Has main/run function but no __name__ guard", "warning")
        )

    # Check for type hints (basic check)
    if "def " in content and ") ->" not in content and ") -> None" not in content:
        # Simple heuristic: if there are function definitions without return type hints
        errors.append(
            ValidationError(str(py_file), "Some functions may be missing type hints", "warning")
        )

    return errors


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate skill structure")
    parser.add_argument("skills", nargs="+", help="Skill directories to validate")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    all_errors: list[ValidationError] = []

    for skill_path in args.skills:
        skill_dir = Path(skill_path)
        if not skill_dir.exists():
            print(f"Skipping {skill_path}: does not exist")
            continue

        print(f"Validating {skill_dir.name}...")
        errors = validate_skill(skill_dir)
        all_errors.extend(errors)

        for error in errors:
            print(f"  {error}")

        if not errors:
            print("  OK")

    # Summary
    print()
    error_count = sum(1 for e in all_errors if e.severity == "error")
    warning_count = sum(1 for e in all_errors if e.severity == "warning")

    print(f"Validation complete: {error_count} errors, {warning_count} warnings")

    if error_count > 0:
        return 1
    if args.strict and warning_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
