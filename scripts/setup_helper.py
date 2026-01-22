#!/usr/bin/env python3
"""Agent Skills setup helper for AI agents (Claude Code).

This script helps users configure their AI agent to discover and use installed
agent skills by managing the CLAUDE.md configuration file.

Usage:
    python scripts/setup_helper.py
    python scripts/setup_helper.py --show
    python scripts/setup_helper.py --dry-run
    python scripts/setup_helper.py --skill-path ~/.local/share/agent-skills/skills

Examples:
    # Interactive setup (default)
    python scripts/setup_helper.py

    # Show current configuration
    python scripts/setup_helper.py --show

    # Preview changes without writing
    python scripts/setup_helper.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class SkillInfo:
    """Information about a discovered skill."""

    name: str  # e.g., "jira"
    path: Path  # Absolute path to skill directory
    skill_md: Path  # Path to SKILL.md
    script: Path  # Path to skill.py script
    description: str  # Parsed from SKILL.md


@dataclass
class ClaudeMdConfig:
    """CLAUDE.md configuration state."""

    path: Path
    exists: bool
    content: str
    configured_skills: list[str]  # Skill names already referenced


# ============================================================================
# SKILL DISCOVERY
# ============================================================================


def get_search_locations(custom_paths: list[str] | None = None) -> list[Path]:
    """Get list of locations to search for skills.

    Args:
        custom_paths: Optional list of custom paths from CLI.

    Returns:
        List of Path objects to search, in priority order.
    """
    locations = []

    # 1. Custom paths from CLI (highest priority)
    if custom_paths:
        locations.extend([Path(p).expanduser() for p in custom_paths])

    # 2. Environment variable
    env_path = os.getenv("AGENT_SKILLS_PATH")
    if env_path:
        locations.append(Path(env_path).expanduser())

    # 3. Claude Code default
    locations.append(Path.home() / ".claude" / "skills")

    # 4. XDG standard location
    locations.append(Path.home() / ".local" / "share" / "agent-skills" / "skills")

    # 5. Current repository (for developers)
    locations.append(Path.cwd() / "skills")

    return locations


def parse_skill_description(skill_md: Path) -> str:
    """Extract description from SKILL.md.

    Args:
        skill_md: Path to SKILL.md file.

    Returns:
        Description string, or generic description if parsing fails.
    """
    try:
        content = skill_md.read_text()

        # Look for first paragraph after the main heading
        # Pattern: # SkillName\n\nDescription text
        lines = content.split("\n")
        in_description = False

        for line in lines:
            line = line.strip()

            # Skip the main heading
            if line.startswith("# "):
                in_description = True
                continue

            # Found the description (first non-empty line after heading)
            if in_description and line and not line.startswith("#"):
                return line

        # Fallback: use skill name
        return "Agent skill"

    except Exception:
        return "Agent skill"


def find_skill_installations(
    custom_paths: list[str] | None = None,
) -> dict[Path, list[SkillInfo]]:
    """Search for installed skills in standard locations.

    Args:
        custom_paths: Optional list of custom paths from CLI.

    Returns:
        Dictionary mapping location paths to lists of SkillInfo objects.
    """
    discovered: dict[Path, list[SkillInfo]] = {}
    locations = get_search_locations(custom_paths)

    for location in locations:
        if not location.exists() or not location.is_dir():
            continue

        skills = []

        # Find all SKILL.md files
        for skill_md in location.rglob("SKILL.md"):
            skill_dir = skill_md.parent
            skill_name = skill_dir.name
            skill_script = skill_dir / f"{skill_name}.py"

            # Only include if the script exists
            if skill_script.exists():
                description = parse_skill_description(skill_md)
                skills.append(
                    SkillInfo(
                        name=skill_name,
                        path=skill_dir,
                        skill_md=skill_md,
                        script=skill_script,
                        description=description,
                    )
                )

        if skills:
            discovered[location] = sorted(skills, key=lambda s: s.name)

    return discovered


# ============================================================================
# CLAUDE.md PARSING
# ============================================================================


def parse_claude_md(path: Path) -> ClaudeMdConfig:
    """Parse existing CLAUDE.md to detect configured skills.

    Args:
        path: Path to CLAUDE.md file.

    Returns:
        ClaudeMdConfig object with current state.
    """
    if not path.exists():
        return ClaudeMdConfig(
            path=path,
            exists=False,
            content="",
            configured_skills=[],
        )

    try:
        content = path.read_text()
    except Exception as e:
        print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
        return ClaudeMdConfig(
            path=path,
            exists=True,
            content="",
            configured_skills=[],
        )

    # Look for skill references:
    # Pattern: - **SkillName**: ... - read /path/to/SKILL.md
    configured_skills = []
    pattern = r"-\s*\*\*(\w+)\*\*:.*?read\s+.*?SKILL\.md"

    for match in re.finditer(pattern, content, re.IGNORECASE):
        skill_name = match.group(1).lower()
        configured_skills.append(skill_name)

    return ClaudeMdConfig(
        path=path,
        exists=True,
        content=content,
        configured_skills=configured_skills,
    )


def validate_claude_md_content(content: str) -> list[str]:
    """Validate CLAUDE.md content for outdated or problematic patterns.

    Args:
        content: CLAUDE.md file content to validate.

    Returns:
        List of warning messages (empty if no issues).
    """
    warnings = []

    # Check for venv activation patterns (outdated)
    venv_patterns = [
        r"source\s+\.venv/bin/activate",
        r"source\s+venv/bin/activate",
        r"\.\s+\.venv/bin/activate",
        r"activate\s+venv",
    ]

    for pattern in venv_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(
                "Found venv activation instructions. Skills should be installed "
                "with 'pip install --user' and run directly without venv activation."
            )
            break

    # Check for cd commands (should run scripts directly)
    if re.search(r"cd\s+.*agent-skills.*&&", content):
        warnings.append(
            "Found 'cd' commands before running scripts. Scripts should be run "
            "directly with absolute paths (e.g., 'python ~/.claude/skills/jira/jira.py check')."
        )

    # Check for scripts/ subdirectory references (old structure)
    if re.search(r"skills/\w+/scripts/\w+\.py", content):
        warnings.append(
            "Found references to 'skills/*/scripts/*.py'. The new structure has "
            "the main script directly in the skill directory (e.g., 'skills/jira/jira.py')."
        )

    # Check for expected patterns
    if "## Running Scripts" in content:
        if "Always run skill scripts directly:" not in content:
            warnings.append(
                "Running Scripts section exists but missing recommended guidance: "
                "'Always run skill scripts directly:'"
            )

    return warnings


# ============================================================================
# CLAUDE.md GENERATION
# ============================================================================


def generate_claude_md_content(base_path: Path, skills: list[SkillInfo]) -> str:
    """Generate CLAUDE.md content for discovered skills.

    Args:
        base_path: Base path where skills are installed.
        skills: List of SkillInfo objects.

    Returns:
        Generated CLAUDE.md content as string.
    """
    lines = [
        "# Global Agent Skills",
        "",
        f"Skills are available at {base_path}",
        "",
        "## Available Skills",
        "",
    ]

    # Add skill entries
    for skill in sorted(skills, key=lambda s: s.name):
        title = skill.name.title()
        lines.append(f"- **{title}**: {skill.description} - read {skill.skill_md}")

    lines.extend(
        [
            "",
            "## Running Scripts",
            "",
            "Always run skill scripts directly:",
            "",
            "```bash",
        ]
    )

    # Add example with first skill
    if skills:
        example_skill = skills[0]
        lines.append(f"python {example_skill.script} check")

    lines.extend(
        [
            "```",
            "",
            "## Skill Invocation",
            "",
        ]
    )

    # Add invocation examples
    for skill in sorted(skills, key=lambda s: s.name):
        lines.append(f"Use `/{skill.name}` or describe naturally:")
        lines.append(f'- "Search {skill.name.title()} for open issues"')
        lines.append("")

    return "\n".join(lines)


def update_claude_md_section(
    existing_content: str,
    skills: list[SkillInfo],
) -> str:
    """Update the Available Skills section in existing CLAUDE.md.

    Args:
        existing_content: Current CLAUDE.md content.
        skills: List of SkillInfo objects.

    Returns:
        Updated CLAUDE.md content.
    """
    # Generate new skills section
    new_skills_section = []
    new_skills_section.append("## Available Skills")
    new_skills_section.append("")

    for skill in sorted(skills, key=lambda s: s.name):
        title = skill.name.title()
        new_skills_section.append(f"- **{title}**: {skill.description} - read {skill.skill_md}")

    new_skills_text = "\n".join(new_skills_section)

    # Try to replace existing Available Skills section
    # Pattern: ## Available Skills ... (up to next ## or end)
    pattern = r"##\s*Available\s*Skills.*?(?=\n##|\Z)"
    if re.search(pattern, existing_content, re.DOTALL | re.IGNORECASE):
        # Replace existing section
        updated = re.sub(
            pattern,
            new_skills_text,
            existing_content,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return updated

    # If no Available Skills section exists, append it
    # Try to insert after "# Global Agent Skills" section
    if "# Global Agent Skills" in existing_content or "# Agent Skills" in existing_content:
        lines = existing_content.split("\n")
        result = []
        inserted = False

        for i, line in enumerate(lines):
            result.append(line)

            # Insert after the header and any immediate content
            if (
                not inserted
                and line.strip().startswith("# ")
                and ("Agent" in line and "Skills" in line)
            ):
                # Skip empty lines
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    result.append(lines[j])
                    j += 1

                # Add the skills section
                result.append("")
                result.append(new_skills_text)
                result.append("")
                inserted = True

                # Skip to next section or continue
                while j < len(lines) and not lines[j].strip().startswith("##"):
                    if lines[j].strip():  # Skip lines until next section
                        result.append(lines[j])
                    j += 1

                # Continue from where we left off
                lines = lines[: i + 1] + lines[j:]
                break

        return "\n".join(result)

    # Fallback: Just append at the end
    return existing_content + "\n\n" + new_skills_text


# ============================================================================
# INTERACTIVE SETUP
# ============================================================================


def show_current_config(
    discovered: dict[Path, list[SkillInfo]],
    config: ClaudeMdConfig,
) -> None:
    """Display current configuration status.

    Args:
        discovered: Discovered skills by location.
        config: Current CLAUDE.md configuration.
    """
    print("Current Configuration")
    print("=" * 70)
    print()

    # CLAUDE.md status
    status = "exists" if config.exists else "not found"
    print(f"CLAUDE.md: {config.path} ({status})")
    print()

    # Validate existing content
    if config.exists and config.content:
        validation_warnings = validate_claude_md_content(config.content)
        if validation_warnings:
            print("⚠️  Configuration Warnings:")
            for warning in validation_warnings:
                print(f"  - {warning}")
            print()

    if config.configured_skills:
        print("Configured skills:")
        for skill_name in sorted(config.configured_skills):
            print(f"  - {skill_name}")
        print()

    # Available skill locations
    if discovered:
        print("Available skill locations:")
        for location, skills in discovered.items():
            print(f"  - {location} ({len(skills)} skill{'s' if len(skills) != 1 else ''})")
        print()

        print("All discovered skills:")
        for _location, skills in discovered.items():
            for skill in skills:
                configured = "✓" if skill.name in config.configured_skills else " "
                print(f"  [{configured}] {skill.name} ({skill.path})")
                print(f"      {skill.description}")
                print(f"      Script: {skill.script}")
        print()
    else:
        print("No skills found in standard locations.")
        print()


def update_claude_md(
    config: ClaudeMdConfig,
    skills: list[SkillInfo],
    dry_run: bool = False,
    auto: bool = False,
) -> bool:
    """Create or update CLAUDE.md with skill references.

    Args:
        config: Current CLAUDE.md configuration.
        skills: List of skills to configure.
        dry_run: If True, only show preview without writing.
        auto: If True, skip confirmation prompt.

    Returns:
        True if successful, False otherwise.
    """
    if not skills:
        print("No skills to configure.", file=sys.stderr)
        return False

    # Determine base path (use the most common parent)
    base_path = skills[0].path.parent

    # Generate content
    if not config.exists:
        content = generate_claude_md_content(base_path, skills)
    else:
        content = update_claude_md_section(config.content, skills)

    # Show preview
    print()
    print("Preview of changes:")
    print("=" * 70)
    print(content)
    print("=" * 70)
    print()

    if dry_run:
        print(f"Dry run - would write to {config.path}")
        return True

    # Confirm
    if not auto:
        response = input(f"Write to {config.path}? [Y/n]: ").strip().lower()
        if response not in ("", "y", "yes"):
            print("Cancelled.")
            return False

    # Write file
    try:
        config.path.parent.mkdir(parents=True, exist_ok=True)
        config.path.write_text(content)
        print(f"✓ Written to {config.path}")
        return True
    except Exception as e:
        print(f"Error: Could not write to {config.path}: {e}", file=sys.stderr)
        return False


def interactive_setup(
    custom_paths: list[str] | None = None,
    claude_md_path: Path | None = None,
    dry_run: bool = False,
    auto: bool = False,
) -> int:
    """Run interactive setup flow.

    Args:
        custom_paths: Optional custom skill paths.
        claude_md_path: Optional custom CLAUDE.md path.
        dry_run: If True, preview only.
        auto: If True, skip confirmations.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Agent Skills Setup Helper")
    print("=" * 70)
    print()

    # 1. Detect installations
    print("Searching for installed skills...")
    discovered = find_skill_installations(custom_paths)

    if not discovered:
        print()
        print("No skills found in common locations:")
        print("  - ~/.claude/skills/")
        print("  - ~/.local/share/agent-skills/skills/")
        print("  - ./skills/ (current directory)")
        print()
        print("Install skills first following: docs/user-guide.md")
        print()
        print("To install a skill:")
        print("  mkdir -p ~/.claude/skills")
        print("  cd ~/.claude/skills")
        print(
            "  curl -L https://github.com/odyssey4me/agent-skills/releases/latest/download/jira.tar.gz | tar xz"
        )
        return 1

    # 2. Show discovered skills
    print()
    print("Discovered skills:")
    all_skills = []
    for location, skills in discovered.items():
        print(f"\n  Location: {location}")
        for skill in skills:
            print(f"    - {skill.name}: {skill.description}")
            all_skills.append(skill)

    # 3. Check CLAUDE.md
    print()
    if claude_md_path is None:
        claude_md_path = Path.home() / ".claude" / "CLAUDE.md"

    config = parse_claude_md(claude_md_path)

    if config.exists:
        print(f"✓ CLAUDE.md exists: {claude_md_path}")
        configured_str = ", ".join(config.configured_skills) if config.configured_skills else "none"
        print(f"  Currently configured skills: {configured_str}")

        # Find unconfigured skills
        unconfigured = [s for s in all_skills if s.name not in config.configured_skills]

        if unconfigured:
            unconfigured_names = ", ".join(s.name for s in unconfigured)
            print(f"\n  Unconfigured skills: {unconfigured_names}")
            print()

            if not auto:
                response = input("Update CLAUDE.md to include all skills? [Y/n]: ").strip().lower()
                if response not in ("", "y", "yes"):
                    print("Skipping update.")
                    return 0

            success = update_claude_md(config, all_skills, dry_run, auto)
            if not success:
                return 1
        else:
            print("\n  ✓ All discovered skills are already configured!")
    else:
        print(f"✗ CLAUDE.md not found: {claude_md_path}")
        print()

        if not auto:
            response = input("Create CLAUDE.md with discovered skills? [Y/n]: ").strip().lower()
            if response not in ("", "y", "yes"):
                print("Cancelled.")
                return 0

        success = update_claude_md(config, all_skills, dry_run, auto)
        if not success:
            return 1

    # 4. Show next steps
    print()
    print("=" * 70)
    print("Next Steps:")
    print()
    print("1. Verify each skill's setup by running its check command:")
    for skill in all_skills[:3]:  # Show first 3 as examples
        print(f"   python {skill.script} check")
    if len(all_skills) > 3:
        print(f"   ... and {len(all_skills) - 3} more")
    print()
    print("2. Configure authentication for each skill (if needed):")
    print("   - Use environment variables (recommended)")
    print("   - Or follow skill-specific instructions in SKILL.md")
    print()
    print("3. Start using skills with Claude Code!")

    return 0


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup helper for Agent Skills with Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_helper.py                  # Interactive setup
  python scripts/setup_helper.py --show           # Show current config
  python scripts/setup_helper.py --dry-run        # Preview changes
  python scripts/setup_helper.py --auto           # Non-interactive mode
        """,
    )

    parser.add_argument(
        "--skill-path",
        action="append",
        help="Custom path to search for skills (can be used multiple times)",
    )

    parser.add_argument(
        "--claude-md",
        type=Path,
        help="Path to CLAUDE.md file (default: ~/.claude/CLAUDE.md)",
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current configuration and exit",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Non-interactive mode (skip confirmations)",
    )

    args = parser.parse_args()

    # Handle --show mode
    if args.show:
        discovered = find_skill_installations(args.skill_path)
        claude_md_path = args.claude_md or Path.home() / ".claude" / "CLAUDE.md"
        config = parse_claude_md(claude_md_path)
        show_current_config(discovered, config)
        return 0

    # Run interactive setup
    return interactive_setup(
        custom_paths=args.skill_path,
        claude_md_path=args.claude_md,
        dry_run=args.dry_run,
        auto=args.auto,
    )


if __name__ == "__main__":
    sys.exit(main())
