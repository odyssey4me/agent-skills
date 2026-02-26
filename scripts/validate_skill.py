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
        errors.extend(validate_skill_md(skill_md, skill_name))

    # Check for scripts/ directory
    # Documentation-only skills (like github, gitlab) that wrap official CLIs don't need scripts
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        if not scripts_dir.is_dir():
            errors.append(ValidationError(str(scripts_dir), "scripts/ is not a directory"))
        else:
            # Check for skill script in scripts/ directory
            skill_script = scripts_dir / f"{skill_name}.py"
            if not skill_script.exists():
                errors.append(
                    ValidationError(str(skill_script), f"scripts/{skill_name}.py not found")
                )
            else:
                errors.extend(validate_skill_script(skill_script))

    # Check for references/ directory (optional, but warn if missing)
    references_dir = skill_dir / "references"
    if not references_dir.exists():
        errors.append(
            ValidationError(
                str(references_dir),
                "references/ directory not found (optional, but recommended for additional docs)",
                "warning",
            )
        )

    return errors


def validate_skill_md(skill_md: Path, skill_name: str) -> list[ValidationError]:
    """Validate SKILL.md content.

    Args:
        skill_md: Path to SKILL.md file.
        skill_name: Name of the skill.

    Returns:
        List of validation errors.
    """
    errors: list[ValidationError] = []
    content = skill_md.read_text()

    # Check for YAML frontmatter
    if not content.startswith("---\n"):
        errors.append(
            ValidationError(str(skill_md), "Missing YAML frontmatter (must start with '---')")
        )
    else:
        # Parse frontmatter
        try:
            import yaml

            # Find the end of frontmatter
            end_marker = content.find("\n---\n", 4)
            if end_marker == -1:
                errors.append(
                    ValidationError(
                        str(skill_md), "Invalid YAML frontmatter (missing closing '---')"
                    )
                )
            else:
                frontmatter = content[4:end_marker]
                try:
                    metadata = yaml.safe_load(frontmatter)

                    # Check required fields
                    if not isinstance(metadata, dict):
                        errors.append(
                            ValidationError(str(skill_md), "Frontmatter must be a YAML dictionary")
                        )
                    else:
                        # Check for required fields
                        if "name" not in metadata:
                            errors.append(
                                ValidationError(
                                    str(skill_md), "Frontmatter missing required field: 'name'"
                                )
                            )
                        elif metadata["name"] != skill_name:
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    f"Frontmatter 'name' ({metadata['name']}) doesn't match skill directory name ({skill_name})",
                                    "warning",
                                )
                            )

                        if "description" not in metadata:
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    "Frontmatter missing required field: 'description'",
                                )
                            )
                        elif not metadata["description"] or not isinstance(
                            metadata["description"], str
                        ):
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    "Frontmatter 'description' must be a non-empty string",
                                )
                            )

                        # Check for metadata and version
                        if "metadata" not in metadata:
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    "Frontmatter missing recommended field: 'metadata'",
                                    "warning",
                                )
                            )
                        elif not isinstance(metadata["metadata"], dict):
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    "Frontmatter 'metadata' must be a dictionary",
                                )
                            )
                        elif "version" not in metadata["metadata"]:
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    "Frontmatter metadata missing required field: 'version'",
                                )
                            )
                        elif (
                            not isinstance(metadata["metadata"]["version"], str)
                            or not metadata["metadata"]["version"]
                        ):
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    "Frontmatter metadata 'version' must be a non-empty string",
                                )
                            )
                        if "license" not in metadata:
                            errors.append(
                                ValidationError(
                                    str(skill_md),
                                    "Frontmatter missing recommended field: 'license'",
                                    "warning",
                                )
                            )

                except yaml.YAMLError as e:
                    errors.append(
                        ValidationError(str(skill_md), f"Invalid YAML in frontmatter: {e}")
                    )
        except ImportError:
            errors.append(
                ValidationError(
                    str(skill_md), "pyyaml not installed - cannot validate frontmatter", "warning"
                )
            )

    # Check for required sections
    required_sections = ["# ", "## Authentication"]
    for section in required_sections:
        if section not in content:
            errors.append(ValidationError(str(skill_md), f"Missing required section: {section}"))
    if "## Commands" not in content and "## Script Usage" not in content:
        errors.append(
            ValidationError(
                str(skill_md), "Missing required section: ## Commands or ## Script Usage"
            )
        )

    # Check for examples section (warning only)
    if "## Examples" not in content:
        errors.append(ValidationError(str(skill_md), "Missing ## Examples section", "warning"))

    # Check for Setup Verification section documenting check command (warning only)
    if "## Setup Verification" not in content and "check" not in content.lower():
        errors.append(
            ValidationError(
                str(skill_md),
                "Missing ## Setup Verification section or check command documentation",
                "warning",
            )
        )

    return errors


def validate_skill_script(skill_script: Path) -> list[ValidationError]:
    """Validate a skill Python script.

    Args:
        skill_script: Path to skill script file.

    Returns:
        List of validation errors.
    """
    errors: list[ValidationError] = []
    content = skill_script.read_text()

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
            errors.append(ValidationError(str(skill_script), "Missing module docstring", "warning"))

    # Check for main guard
    if "__name__" in content and "__main__" in content:
        pass  # Has main guard
    elif "def main" in content:
        errors.append(
            ValidationError(str(skill_script), "Has main function but no __name__ guard", "warning")
        )

    # Check for required imports
    required_imports = ["argparse", "sys"]
    for imp in required_imports:
        if f"import {imp}" not in content:
            errors.append(
                ValidationError(str(skill_script), f"Missing required import: {imp}", "warning")
            )

    # Check for check command (should have cmd_check or check subcommand)
    if "cmd_check" not in content and '"check"' not in content and "'check'" not in content:
        errors.append(
            ValidationError(str(skill_script), "Missing 'check' command implementation", "warning")
        )

    # Check for subparser pattern (argparse with subcommands)
    if "subparsers" not in content and "add_subparsers" not in content:
        errors.append(
            ValidationError(
                str(skill_script),
                "Should use argparse with subcommands (add_subparsers)",
                "warning",
            )
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
