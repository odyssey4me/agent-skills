#!/usr/bin/env python3
"""Generate skills.json registry from SKILL.md frontmatter.

Reads all skills/*/SKILL.md files and produces a structured index
at skills.json. Used for drift detection in CI.

Usage:
    python scripts/generate_registry.py
    python scripts/generate_registry.py --check  # Exit 1 if skills.json differs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def _parse_csv(value: str | list) -> list[str]:
    """Parse a comma-separated string into a list of trimmed values.

    Also accepts a list for backwards compatibility.

    Args:
        value: Comma-separated string or list.

    Returns:
        List of stripped, non-empty strings.
    """
    if isinstance(value, list):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_frontmatter(skill_md: Path) -> dict | None:
    """Parse YAML frontmatter from a SKILL.md file.

    Args:
        skill_md: Path to SKILL.md file.

    Returns:
        Parsed frontmatter dict, or None on error.
    """
    content = skill_md.read_text()
    if not content.startswith("---\n"):
        print(f"WARNING: {skill_md} has no YAML frontmatter", file=sys.stderr)
        return None

    end_marker = content.find("\n---\n", 4)
    if end_marker == -1:
        print(f"WARNING: {skill_md} has unclosed frontmatter", file=sys.stderr)
        return None

    frontmatter_text = content[4:end_marker]
    try:
        return yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        print(f"WARNING: {skill_md} has invalid YAML: {e}", file=sys.stderr)
        return None


def determine_type(skill_dir: Path) -> str:
    """Determine skill type based on directory structure.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        Skill type string: 'api', 'cli', or 'workflow'.
    """
    metadata_type = None
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        fm = parse_frontmatter(skill_md)
        if fm and isinstance(fm.get("metadata"), dict):
            metadata_type = fm["metadata"].get("type")

    if metadata_type:
        return metadata_type

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists() and scripts_dir.is_dir():
        py_files = [
            f for f in scripts_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"
        ]
        if py_files:
            return "api"

    return "cli"


def determine_auth(skill_dir: Path) -> str:
    """Determine authentication method from skill structure.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        Auth method string.
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return "none"

    content = skill_md.read_text().lower()

    if "oauth" in content:
        return "oauth"
    if "api token" in content or "api-token" in content or "personal access token" in content:
        return "api-token"
    if "gh auth" in content or "glab auth" in content or "git-review" in content:
        return "cli-auth"

    return "none"


def determine_dependencies(skill_dir: Path) -> list[str]:
    """Determine runtime dependencies from skill structure.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        List of dependency strings.
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return []

    fm = parse_frontmatter(skill_md)
    if fm and isinstance(fm.get("metadata"), dict):
        requires = fm["metadata"].get("requires")
        if requires is not None:
            return _parse_csv(requires)

    content = skill_md.read_text()

    deps = []
    if "pip install" in content:
        if "google-auth" in content:
            deps.append("google-auth")
            deps.append("google-auth-oauthlib")
            deps.append("google-api-python-client")
        if "requests" in content:
            deps.append("requests")
        if "keyring" in content:
            deps.append("keyring")
        if "pyyaml" in content:
            deps.append("pyyaml")
    if "brew install gh" in content or "apt install gh" in content:
        deps.append("gh")
    if "brew install glab" in content or "apt install glab" in content:
        deps.append("glab")
    if "pip install git-review" in content or "apt install git-review" in content:
        deps.append("git-review")

    return deps


def build_registry(skills_root: Path) -> dict:
    """Build the complete skills registry.

    Args:
        skills_root: Path to the skills/ directory.

    Returns:
        Registry dict ready for JSON serialization.
    """
    skills = []

    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        fm = parse_frontmatter(skill_md)
        if not fm:
            continue

        metadata = fm.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        skill_type = determine_type(skill_dir)
        auth_method = determine_auth(skill_dir)
        dependencies = determine_dependencies(skill_dir)

        entry = {
            "name": fm.get("name", skill_dir.name),
            "description": fm.get("description", ""),
            "version": metadata.get("version", "0.1.0"),
            "category": metadata.get("category", ""),
            "tags": _parse_csv(metadata.get("tags", "")),
            "type": skill_type,
            "complexity": metadata.get("complexity", "standard"),
            "auth": auth_method,
            "dependencies": dependencies,
        }

        skills.append(entry)

    return {
        "$schema": "https://agentskills.io/registry/v1",
        "skills": skills,
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate skills.json registry")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if committed skills.json matches generated output",
    )
    parser.add_argument(
        "--output",
        default="skills.json",
        help="Output file path (default: skills.json)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    skills_root = repo_root / "skills"

    if not skills_root.exists():
        print(f"ERROR: {skills_root} not found", file=sys.stderr)
        return 1

    registry = build_registry(skills_root)
    generated = json.dumps(registry, indent=2) + "\n"

    output_path = repo_root / args.output

    if args.check:
        if not output_path.exists():
            print(f"ERROR: {output_path} does not exist. Run without --check to generate it.")
            return 1

        committed = output_path.read_text()
        if committed != generated:
            print(f"ERROR: {output_path} is out of date.")
            print("Run 'python scripts/generate_registry.py' and commit the result.")
            return 1

        print(f"OK: {output_path} is up to date.")
        return 0

    output_path.write_text(generated)
    print(f"Generated {output_path} with {len(registry['skills'])} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
