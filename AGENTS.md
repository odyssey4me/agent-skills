# Agent Skills

Instructions for AI coding assistants working with this repository.

## Standards Compliance

This repository implements the [Agent Skills specification](https://agentskills.io/specification). All skills follow the standard structure with:
- YAML frontmatter in SKILL.md
- Scripts in `scripts/` subdirectory
- Additional docs in `references/` subdirectory

**Implementation choice**: We use Python scripts instead of Bash because the specification supports multiple languages ("Common options include Python, Bash, and JavaScript"), and Python is better suited for complex API integrations.

See [docs/developer-guide.md](docs/developer-guide.md) for detailed architecture documentation.

## Development Principles

When working on this repository:

1. **Keep documentation DRY** (Don't Repeat Yourself):
   - Reference comprehensive guides rather than duplicating content
   - Link to the specification rather than restating it
   - Point to examples in code rather than describing them inline

2. **Use lowercase for markdown files** unless they're part of a spec or de facto standard:
   - ✅ `readme.md`, `contributing.md`, `developer-guide.md`
   - ❌ `README.md`, `CONTRIBUTING.md` (exception: these are de facto standards)
   - ✅ `skill.md` in skill directories
   - ❌ `SKILL.md` (exception: required by Agent Skills specification)

3. **Follow the Agent Skills specification**:
   - All implementation decisions should reference the [specification](https://agentskills.io/specification)
   - SKILL.md format is defined by the spec
   - Directory structure (scripts/, references/) is defined by the spec

4. **Prefer official CLIs over custom scripts**:
   - When an official command-line tool exists, use it instead of implementing custom API wrappers
   - Official CLIs are maintained by the service provider and guaranteed to work with API changes
   - Official CLIs often have richer functionality than we would implement
   - Skills can be documentation-only when the official CLI covers all use cases
   - Examples:
     - ✅ GitHub skill uses `gh` CLI with documentation
     - ❌ Don't create custom GitHub API wrapper when `gh` exists
     - ✅ Jira skill uses custom script (no official CLI with full API coverage)
     - ✅ Google skills use custom scripts (gcloud is infrastructure-focused, not API-focused)

## Quick Reference

**For users**: See [docs/user-guide.md](docs/user-guide.md)
**For developers**: See [docs/developer-guide.md](docs/developer-guide.md)
**For contributors**: See [contributing.md](contributing.md)

## Available Skills

See [README.md](README.md#available-skills) for the complete list of skills.

## Testing Skills

When developing or testing skills, you can run them directly:

```bash
# Run a skill command
python skills/<skill>/scripts/<skill>.py [command] [arguments]

# Verify setup
python skills/<skill>/scripts/<skill>.py check
```

For user-focused testing, authentication, and troubleshooting, see the skill's SKILL.md file and [docs/user-guide.md](docs/user-guide.md).

## Error Handling in Skills

Skills should include an **Error Handling** section in their SKILL.md that tells agents which errors are retryable and which require user intervention. Key principles:

- **Authentication/permission errors are never retryable** — they require user action (re-entering credentials, granting OAuth consent, etc.)
- **Rate limiting (429) and server errors (5xx) are retryable** after a brief wait
- **All other errors should be reported to the user** rather than retried
- Skills that use OAuth should document the `auth reset` → `check` workflow for recovering from scope/token errors

## Before Committing

Pre-commit hooks enforce code quality checks. To avoid failed commits, run these steps before committing:

1. **Format and lint Python code**:
   ```bash
   ruff check --fix .
   ruff format .
   ```

2. **Validate skill structure** (if you modified any skill):
   ```bash
   python scripts/validate_skill.py skills/*
   ```
   Checks: SKILL.md frontmatter, required sections (Authentication, Commands, Examples), script structure (argparse, check subcommand, main guard, docstring).

3. **Regenerate the skills registry** (if you added/removed a skill or changed SKILL.md frontmatter):
   ```bash
   python scripts/generate_registry.py
   ```
   This updates `skills.json`. The pre-commit hook runs `--check` mode and will reject commits where the registry is stale.

4. **Run tests with coverage for changed files**:
   ```bash
   pytest tests/ -q --cov=skills --cov=scripts --cov-report=xml:coverage.xml
   diff-cover coverage.xml --compare-branch=HEAD --fail-under=80
   ```
   Changed lines must have at least 80% test coverage. If you added or modified Python code, write or update tests before committing.

### Additional guidance

- **Type hints** are required for all function signatures.
- **Google-style docstrings** are required for modules, classes, and public functions.
- **Line length** is 100 characters (configured in `pyproject.toml`).
- **Import sorting** is handled by ruff (`isort` rules) — do not manually reorder imports.
- When adding a new skill script, ensure it has: a module docstring, `if __name__ == "__main__":` guard, argparse with subcommands, and a `check` subcommand.

## Creating New Skills

To create a new skill, use the template:

```bash
cp -r templates/api-skill skills/myskill
```

See [templates/api-skill/README.md](templates/api-skill/README.md) for complete instructions on:
- Skill structure and required files
- YAML frontmatter format
- Script implementation guidelines
- Testing and validation

For detailed development guidelines, see [docs/developer-guide.md](docs/developer-guide.md).

### Documentation-Only Skills

Skills that wrap official CLI tools (like `gh` for GitHub or `glab` for GitLab) are documentation-only and don't require a `scripts/` directory or Python implementation. These skills:

- Provide comprehensive documentation in SKILL.md
- Guide users to use the official CLI directly
- Include practical examples in references/common-workflows.md
- Don't need custom Python scripts or a scripts/ directory

**Examples**: `github`, `gitlab`

**When to use this approach**:
- An official CLI exists that covers all needed functionality
- The CLI is well-maintained by the service provider
- The CLI handles authentication, API changes, and edge cases
- Users benefit more from learning the official tool than a custom wrapper

## Repository Structure

For the complete project structure, see [docs/developer-guide.md](docs/developer-guide.md#repository-structure).
