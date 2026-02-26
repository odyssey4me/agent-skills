# Setup Helper

The setup helper (`scripts/setup_helper.py`) is a utility script that helps configure AI agent environments (CLAUDE.md) to discover and use installed agent skills.

## Usage

```bash
python scripts/setup_helper.py                          # Interactive setup
python scripts/setup_helper.py --show                   # Show current config
python scripts/setup_helper.py --dry-run                # Preview changes
python scripts/setup_helper.py --auto                   # Non-interactive mode
python scripts/setup_helper.py --skill-path /custom/path  # Custom skill location
```

## CLI Interface

```python { .api }
python scripts/setup_helper.py
  [--skill-path PATH]    # Custom path to search for skills (repeatable)
  [--claude-md PATH]     # Path to CLAUDE.md (default: ~/.claude/CLAUDE.md)
  [--show]               # Show current configuration and exit
  [--dry-run]            # Preview changes without writing
  [--auto]               # Non-interactive, skip confirmation prompts
```

## Capabilities

### Interactive Setup

Discovers installed skills and creates/updates `CLAUDE.md` to reference them.

Search locations (in priority order):
1. `--skill-path` arguments
2. `$AGENT_SKILLS_PATH` environment variable
3. `~/.claude/skills/` (Claude Code default)
4. `~/.local/share/agent-skills/skills/` (XDG standard)
5. `./skills/` (current directory)

### Show Configuration

Displays current `CLAUDE.md` state, discovered skills, and any configuration warnings.

Validates existing `CLAUDE.md` for:
- Outdated venv activation patterns
- Old `cd` command patterns
- Outdated `skills/*/scripts/*.py` path references

## Python API

```python { .api }
from scripts.setup_helper import (
    # Skill discovery
    get_search_locations,       # get_search_locations(custom_paths=None) -> list[Path]
    parse_skill_description,    # parse_skill_description(skill_md: Path) -> str
    find_skill_installations,   # find_skill_installations(custom_paths=None) -> dict[Path, list[SkillInfo]]

    # CLAUDE.md parsing
    parse_claude_md,            # parse_claude_md(path: Path) -> ClaudeMdConfig
    validate_claude_md_content, # validate_claude_md_content(content: str) -> list[str]

    # CLAUDE.md generation
    generate_claude_md_content, # generate_claude_md_content(base_path, skills) -> str
    update_claude_md_section,   # update_claude_md_section(existing_content, skills) -> str
    update_claude_md,           # update_claude_md(config, skills, dry_run, auto) -> bool

    # Setup flow
    show_current_config,        # show_current_config(discovered, config) -> None
    interactive_setup,          # interactive_setup(custom_paths, claude_md_path, dry_run, auto) -> int

    # Data classes
    SkillInfo,
    ClaudeMdConfig,
)
```

### Data Classes

```python { .api }
@dataclass
class SkillInfo:
    """Information about a discovered skill."""
    name: str         # Skill name (e.g., "jira")
    path: Path        # Absolute path to skill directory
    skill_md: Path    # Path to SKILL.md
    script: Path      # Path to skill Python script
    description: str  # Parsed from SKILL.md first paragraph

@dataclass
class ClaudeMdConfig:
    """CLAUDE.md configuration state."""
    path: Path
    exists: bool
    content: str
    configured_skills: list[str]  # Skill names already referenced
```

### Functions

```python { .api }
def get_search_locations(custom_paths: list[str] | None = None) -> list[Path]:
    """
    Get list of locations to search for skills.

    Args:
        custom_paths: Custom paths from CLI (highest priority).

    Returns:
        List of Path objects in priority order.
    """

def parse_skill_description(skill_md: Path) -> str:
    """
    Extract description from SKILL.md first paragraph after heading.

    Args:
        skill_md: Path to SKILL.md file.

    Returns:
        Description string, or "Agent skill" if parsing fails.
    """

def find_skill_installations(
    custom_paths: list[str] | None = None
) -> dict[Path, list[SkillInfo]]:
    """
    Search for installed skills (SKILL.md + matching .py script).

    A skill is recognized when a directory contains both a `SKILL.md` file
    and a Python script named `<skill_name>.py` at the same directory level.
    The expected installed layout is:
        <location>/<skill_name>/SKILL.md
        <location>/<skill_name>/<skill_name>.py   ← script at root of skill dir

    Note: This differs from the development source layout (where the script
    is in a `scripts/` subdirectory). This function only finds skills in
    the *installed* layout.

    Args:
        custom_paths: Optional custom paths to search.

    Returns:
        Dict mapping location path to list of SkillInfo objects (sorted by name).
    """

def parse_claude_md(path: Path) -> ClaudeMdConfig:
    """
    Parse existing CLAUDE.md to detect configured skills.

    Detects skill references matching pattern:
    - **SkillName**: ... - read /path/to/SKILL.md

    Args:
        path: Path to CLAUDE.md file.

    Returns:
        ClaudeMdConfig with current state.
    """

def validate_claude_md_content(content: str) -> list[str]:
    """
    Validate CLAUDE.md for outdated patterns.

    Checks for:
    - Venv activation patterns (outdated)
    - cd command patterns (outdated)
    - skills/*/scripts/*.py references (old structure)

    Args:
        content: CLAUDE.md file content.

    Returns:
        List of warning message strings (empty if no issues).
    """

def generate_claude_md_content(base_path: Path, skills: list[SkillInfo]) -> str:
    """
    Generate complete CLAUDE.md content for discovered skills.

    Args:
        base_path: Base path where skills are installed.
        skills: List of SkillInfo objects.

    Returns:
        Generated CLAUDE.md content string.
    """

def update_claude_md_section(existing_content: str, skills: list[SkillInfo]) -> str:
    """
    Update the Available Skills section in existing CLAUDE.md.

    Replaces existing ## Available Skills section or appends if not found.

    Args:
        existing_content: Current CLAUDE.md content.
        skills: List of SkillInfo objects.

    Returns:
        Updated CLAUDE.md content string.
    """

def update_claude_md(
    config: ClaudeMdConfig,
    skills: list[SkillInfo],
    dry_run: bool = False,
    auto: bool = False,
) -> bool:
    """
    Create or update CLAUDE.md with skill references.

    Args:
        config: Current CLAUDE.md state.
        skills: Skills to configure.
        dry_run: Only preview, don't write.
        auto: Skip confirmation prompts.

    Returns:
        True on success, False on failure/cancellation.
    """

def show_current_config(
    discovered: dict[Path, list[SkillInfo]],
    config: ClaudeMdConfig,
) -> None:
    """
    Print current configuration status (skills discovered, CLAUDE.md state).

    Args:
        discovered: Discovered skills by location.
        config: Current CLAUDE.md configuration.
    """

def interactive_setup(
    custom_paths: list[str] | None = None,
    claude_md_path: Path | None = None,
    dry_run: bool = False,
    auto: bool = False,
) -> int:
    """
    Run full setup flow: discover skills, check CLAUDE.md, prompt to update.

    Args:
        custom_paths: Custom skill paths.
        claude_md_path: Custom CLAUDE.md path (default: ~/.claude/CLAUDE.md).
        dry_run: Preview only.
        auto: Skip confirmations.

    Returns:
        Exit code (0=success, 1=failure).
    """
```
