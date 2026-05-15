# Claude Code Instructions

Refer to [AGENTS.md](./AGENTS.md) for skill usage instructions.

Refer to [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## Repository Layout

- `skills/` — Self-contained agent skills (jira, github, gmail, etc.)
- `scripts/` — Development utilities (validation, versioning, pre-commit)
- `templates/` — Starter templates for new skills (api, cli, workflow)
- `tests/` — Pytest suite (one file per skill, 80% coverage required)
- `docs/` — User guide, developer guide, OAuth setup
- `.github/workflows/` — CI (lint/test/validate) and release pipelines

## Before Committing

Pre-commit hooks are a failsafe, not a first pass. Always run checks before
committing to avoid wasting tokens on hook failures and re-commits.

Delegate pre-commit checks to a **haiku** subagent (via the Task tool with
`model: "haiku"`) to minimise token cost. The subagent should:

1. Run `scripts/pre_commit_checks.sh` (or `--skills` if only skills changed).
2. Fix any issues found and report back.

After the subagent completes, stage everything and commit. The `tessl-sync`
hook will auto-update `tile.json` files — if it modifies any, stage them and
re-commit.

## Skill Versioning

Each skill has a `metadata.version` field in its `SKILL.md` frontmatter.
Follow [Semantic Versioning](https://semver.org/) when updating it:

- **Patch** (0.1.0 → 0.1.1): Bug fixes, typo corrections, minor doc tweaks
  that don't change behaviour.
- **Minor** (0.1.1 → 0.2.0): New commands, new options, expanded
  functionality — anything additive and backward-compatible.
- **Major** (0.2.0 → 1.0.0): Breaking changes — removed or renamed commands,
  changed default behaviour, restructured arguments.

A Claude Code hook enforces this — commits with unbumped skill changes are
blocked automatically. Run `scripts/check_versions.sh` to check manually.

## Releasing

See [docs/developer-guide.md](docs/developer-guide.md#releasing) for the
full release procedure.

## TODO.md

When completing items from TODO.md, **remove** the finished entries entirely
rather than marking them `[x]`. If an entire section becomes empty, remove the
section heading too. Only pending work belongs in TODO.md.

## Skill Invocation

Use `/jira` to invoke the Jira skill, or describe what you want naturally:
- "Search Jira for my open issues"
- "Create a bug in PROJECT about login failures"
