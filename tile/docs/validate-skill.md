# Validate Skill

The validate skill script (`scripts/validate_skill.py`) is a utility CLI tool for validating agent skill directory structure and requirements. It checks that skills conform to the expected layout and coding standards.

## Usage

```bash
# Validate a single skill directory
python scripts/validate_skill.py skills/jira

# Validate all skills
python scripts/validate_skill.py skills/*

# Treat warnings as errors (strict mode)
python scripts/validate_skill.py skills/jira --strict
```

## CLI Interface

```python { .api }
python scripts/validate_skill.py <skills...> [--strict]
```

Parameters:
- `skills` (required, one or more): Paths to skill directories to validate
- `--strict`: Treat warnings as errors (exit code 1 if any warnings exist)

**Output**: Per-skill validation results with `[ERROR]` and `[WARNING]` lines, followed by a summary count.

**Exit codes**: `0` on success (no errors), `1` on validation errors (or warnings in strict mode).

## Capabilities

### validate_skill — Validate Skill Directory

Validates a complete skill directory structure, checking for required files and subdirectories.

```python { .api }
def validate_skill(skill_dir: Path) -> list[ValidationError]:
    """
    Validate a skill directory structure.

    Checks:
    - skill_dir is a directory
    - SKILL.md exists and is valid (via validate_skill_md)
    - scripts/ subdirectory exists
    - scripts/<skill_name>.py script exists and is valid (via validate_skill_script)
    - references/ subdirectory exists (warning only if missing)

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        List of ValidationError objects (empty if valid).
    """
```

### validate_skill_md — Validate SKILL.md Content

Validates the content of a SKILL.md file for required YAML frontmatter and sections.

```python { .api }
def validate_skill_md(skill_md: Path, skill_name: str) -> list[ValidationError]:
    """
    Validate SKILL.md content.

    Checks (errors):
    - YAML frontmatter present (starts with '---')
    - Frontmatter has closing '---'
    - Valid YAML syntax in frontmatter
    - Frontmatter contains 'name' field
    - Frontmatter contains 'description' field (non-empty string)
    - Required sections present: '# ' (heading), '## Authentication', '## Commands'

    Checks (warnings):
    - Frontmatter 'name' matches skill directory name
    - Frontmatter contains 'metadata' field
    - Frontmatter contains 'license' field
    - '## Examples' section present
    - '## Setup Verification' or check command documented

    Args:
        skill_md: Path to SKILL.md file.
        skill_name: Name of the skill (from directory name).

    Returns:
        List of ValidationError objects.

    Raises:
        FileNotFoundError: If skill_md does not exist. This function does not
            gracefully handle missing files. Use validate_skill() instead when
            the file may not exist — it checks existence and returns a
            ValidationError rather than raising.
    """
```

### validate_skill_script — Validate Skill Python Script

Validates a skill Python script for structural requirements.

```python { .api }
def validate_skill_script(skill_script: Path) -> list[ValidationError]:
    """
    Validate a skill Python script.

    Checks (warnings):
    - Module docstring present (in first 5 lines)
    - If main() function exists, __name__ == '__main__' guard is present
    - 'argparse' imported
    - 'sys' imported
    - 'check' command implemented (cmd_check or 'check' in content)
    - Uses add_subparsers() pattern for subcommand routing

    Args:
        skill_script: Path to skill script (.py file).

    Returns:
        List of ValidationError objects.
    """
```

## Types

```python { .api }
class ValidationError:
    """Represents a validation error or warning."""

    def __init__(self, path: str, message: str, severity: str = "error"):
        """
        Args:
            path: File path where the error occurred.
            message: Human-readable description of the error.
            severity: "error" (default) or "warning".
        """

    path: str       # File path where the error occurred
    message: str    # Error description
    severity: str   # "error" or "warning"

    def __str__(self) -> str:
        """Returns '[ERROR] path: message' or '[WARNING] path: message'."""
```

## Python API (Programmatic Use)

```python { .api }
from scripts.validate_skill import (
    validate_skill,        # validate_skill(skill_dir: Path) -> list[ValidationError]
    validate_skill_md,     # validate_skill_md(skill_md: Path, skill_name: str) -> list[ValidationError]
    validate_skill_script, # validate_skill_script(skill_script: Path) -> list[ValidationError]
    ValidationError,
)
```

### Programmatic Usage Examples

```python
from pathlib import Path
from scripts.validate_skill import validate_skill, ValidationError

# Validate a skill directory
errors = validate_skill(Path("skills/jira"))

# Filter by severity
real_errors = [e for e in errors if e.severity == "error"]
warnings = [e for e in errors if e.severity == "warning"]

if real_errors:
    for e in real_errors:
        print(f"ERROR: {e.path}: {e.message}")
else:
    print("Skill is valid")

# Validate multiple skills
from scripts.validate_skill import validate_skill_md, validate_skill_script

md_errors = validate_skill_md(Path("skills/jira/SKILL.md"), "jira")
script_errors = validate_skill_script(Path("skills/jira/scripts/jira.py"))
```
