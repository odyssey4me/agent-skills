# Claude Code Instructions

Refer to [AGENTS.md](./AGENTS.md) for skill usage instructions.

Refer to [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## Pre-commit Hooks

When committing changes to skill SKILL.md files, pre-commit hooks enforce two
generated-file checks that may cause the first commit attempt to fail:

1. **skills.json registry** — Run `python scripts/generate_registry.py` to
   regenerate, then stage `skills.json`.
2. **tile.json sync** — The `tessl-sync` hook auto-updates `tile.json` files
   in each skill directory. Stage any modified `tile.json` files.

After regenerating and staging these files, re-run the commit. Both checks
must pass alongside `ruff`, `validate_skill`, and `tessl skill lint`.

## Skill Invocation

Use `/jira` to invoke the Jira skill, or describe what you want naturally:
- "Search Jira for my open issues"
- "Create a bug in PROJECT about login failures"
