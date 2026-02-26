# Claude Code Instructions

Refer to [AGENTS.md](./AGENTS.md) for skill usage instructions.

Refer to [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## Before Committing

Pre-commit hooks are a failsafe, not a first pass. Always run checks before
committing to avoid wasting tokens on hook failures and re-commits.

Delegate pre-commit checks to a **haiku** subagent (via the Task tool with
`model: "haiku"`) to minimise token cost. The subagent should:

1. Run `ruff check --fix . && ruff format .`
2. Run `python scripts/validate_skill.py skills/*` (if any skill was modified)
3. Run `tessl skill lint skills/*/tile.json` (if any skill was modified)
4. Fix any issues found and report back.

After the subagent completes, stage everything and commit. The `tessl-sync`
hook will auto-update `tile.json` files — if it modifies any, stage them and
re-commit.

## TODO.md

When completing items from TODO.md, **remove** the finished entries entirely
rather than marking them `[x]`. If an entire section becomes empty, remove the
section heading too. Only pending work belongs in TODO.md.

## Skill Invocation

Use `/jira` to invoke the Jira skill, or describe what you want naturally:
- "Search Jira for my open issues"
- "Create a bug in PROJECT about login failures"
