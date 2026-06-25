# Claude Code Instructions

Refer to [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## Repository Layout

- `skills/` — Self-contained agent skills (jira, confluence, google, etc.)
- `scripts/` — Development utilities (validation, versioning, pre-commit)
- `templates/` — Starter templates for new skills (api, cli, workflow)
- `tests/` — Pytest suite (one file per skill, 80% coverage required)
- `docs/` — User guide, developer guide, OAuth setup
- `.github/workflows/` — CI (lint/test/validate) and release pipelines

## Standards Compliance

This repository implements the [Agent Skills specification](https://agentskills.io/specification). All skills follow the standard structure with YAML frontmatter in SKILL.md, scripts in `scripts/`, and additional docs in `references/`.

We use Python scripts because the specification supports multiple languages, and Python is better suited for complex API integrations. See [docs/developer-guide.md](docs/developer-guide.md#why-python) for rationale.

## Development Principles

1. **Keep documentation DRY** — reference comprehensive guides rather than duplicating content. Link to the specification rather than restating it.

2. **Use lowercase for markdown files** unless they're a de facto standard (README.md, CONTRIBUTING.md) or required by the Agent Skills specification (SKILL.md).

3. **Follow the Agent Skills specification** — all implementation decisions should reference the [specification](https://agentskills.io/specification).

4. **Prefer official CLIs over custom scripts** — when an official CLI exists, use it instead of a custom API wrapper. Skills can be documentation-only when the CLI covers all use cases (e.g. `gh` for GitHub, `glab` for GitLab, `gog` for Google).

5. **Default to markdown output format** — all skill scripts must output markdown by default. Use `### {title}` for item headings, `- **Label:** value` for metadata, `## {Section}` for top-level grouping. Preserve `--json` as an alternative. Reference `skills/jira/scripts/jira.py` as the canonical example.

## Error Handling in Skills

Skills should include an **Error Handling** section in their SKILL.md that tells agents which errors are retryable and which require user intervention:

- **Authentication/permission errors are never retryable** — they require user action.
- **Rate limiting (429) and server errors (5xx) are retryable** after a brief wait.
- **All other errors should be reported to the user** rather than retried.
- Skills that use OAuth should document the `auth reset` → `check` workflow for recovering from scope/token errors.

## Before Committing

Pre-commit hooks are a failsafe, not a first pass. Always run checks before
committing to avoid wasting tokens on hook failures and re-commits.

Delegate pre-commit checks to a **haiku** subagent (via the Task tool with
`model: "haiku"`) to minimise token cost. The subagent should:

1. Run `scripts/pre_commit_checks.sh` (or `--skills` if only skills changed).
2. Fix any issues found and report back.

After the subagent completes, stage everything and commit.

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

## Maintenance

Review this file quarterly and after major Claude model releases. Remove
rules that compensate for limitations the model or tooling no longer has —
stale instructions can actively constrain newer models.

Subdirectory CLAUDE.md files (e.g. `skills/CLAUDE.md`) follow the same
refresh cadence — include them in quarterly reviews.

## Skill Invocation

Use `/jira` to invoke the Jira skill, or describe what you want naturally:
- "Search Jira for my open issues"
- "Create a bug in PROJECT about login failures"
