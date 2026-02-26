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

5. **Default to markdown output format**:
   - All skill scripts must output markdown by default for immediate agent consumability
   - Use `### {title}` for item headings, `- **Label:** value` for metadata fields
   - Use `## {Section}` for top-level grouping (e.g., list results header)
   - Preserve `--json` flag as an alternative for raw JSON output on all commands
   - Reference `skills/gmail/scripts/gmail.py` as the canonical example
   - CLI-wrapping skills should provide a wrapper script when the CLI doesn't natively produce markdown

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
skills/<skill>/scripts/<skill>.py [command] [arguments]

# Verify setup
skills/<skill>/scripts/<skill>.py check
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

3. **Update README.md** (if you added or removed a skill):
   Ensure the [Available Skills](README.md#available-skills) table includes an entry for every skill. New skills must be added to the table before committing.

4. **Run tests with coverage for changed files**:
   ```bash
   pytest tests/ -q --cov=skills --cov=scripts --cov-report=xml:coverage.xml
   diff-cover coverage.xml --compare-branch=HEAD --fail-under=80
   ```
   Changed lines must have at least 80% test coverage. If you added or modified Python code, write or update tests before committing.

### TODO.md maintenance

[TODO.md](TODO.md) tracks only **pending** work. Completed items must not remain in the file. When committing a feature or fix that addresses a TODO item, remove that item from TODO.md as part of the same commit.

### Atomic commits

Solve one problem or implement one feature at a time. Commit as soon as that unit of work is complete before moving on to the next. This keeps changes small, reviewable, and easy to revert if needed. Do not bundle unrelated changes into a single commit.

### Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages. For the content and spirit of good commit messages, follow [How to Write a Git Commit Message](https://cbea.ms/git-commit/) — where the two guides conflict, Conventional Commits takes precedence (e.g. lowercase subject after the prefix).

**Prefixes**:

- `feat:` — a new feature
- `fix:` — a bug fix
- `docs:` — documentation-only changes
- `refactor:` — code changes that neither fix a bug nor add a feature
- `test:` — adding or updating tests
- `chore:` — maintenance tasks (dependencies, CI, tooling)

Include a scope when it adds clarity, e.g. `feat(jira):`, `fix(gmail):`, `docs(agents):`. Use the body to explain *what* and *why*, not *how*.

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

Skills that wrap official CLI tools (like `glab` for GitLab) are documentation-only and don't require a `scripts/` directory or Python implementation. These skills:

- Provide comprehensive documentation in SKILL.md
- Guide users to use the official CLI directly
- Include practical examples in references/common-workflows.md
- Don't need custom Python scripts or a scripts/ directory

**Examples**: `gitlab`, `gerrit`

**When to use this approach**:
- An official CLI exists that covers all needed functionality
- The CLI is well-maintained by the service provider
- The CLI handles authentication, API changes, and edge cases
- The CLI natively produces markdown-compatible output, or the skill is purely documentation

**When to add a wrapper script**: If an official CLI exists but doesn't produce markdown output by default, provide a thin wrapper script that calls the CLI with `--json` and formats results as markdown. This ensures consistent agent-consumable output across all skills (see Development Principle #5).

## Repository Structure

For the complete project structure, see [docs/developer-guide.md](docs/developer-guide.md#repository-structure).
