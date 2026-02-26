# Claude Code Instructions

Refer to [AGENTS.md](./AGENTS.md) for skill usage instructions.

Refer to [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

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

**When to bump:** before committing changes to a skill, delegate a version
check to a **haiku** subagent (via the Task tool with `model: "haiku"`). The
subagent should run the script, read its stdout directly, and report back
to the parent agent — **never write output to files**. Specifically:

1. Run `scripts/check_versions.sh` and report which skills need a bump.
2. For skills that already have a bump, **validate the bump level** is
   appropriate for the combined changes since the release tag. Review the
   diff (`git diff <tag> -- skills/<name>/`) and confirm the level matches:
   patch for doc/bug fixes, minor for new features, major for breaking changes.
3. Report any skills where the bump level looks wrong (e.g. a new command was
   added but only a patch bump was applied).

## Releasing

Follow these steps to cut a release. Delegate the version check to a
single **haiku** subagent that performs **all** steps and reports back.

### 1. Validate versions

Delegate to a **haiku** subagent (via the Task tool with `model: "haiku"`).
The subagent should — in a single invocation:

1. Run `scripts/check_versions.sh` and report which skills need a bump.
2. For skills that already have a bump, validate the bump level by reviewing
   `git diff <tag> -- skills/<name>/` and confirming patch/minor/major is
   appropriate for the changes.
3. Report any skills where the bump level looks wrong.

Fix any issues before proceeding.

### 2. Push, tag, and create the release

1. Push all commits to `origin/main`.
2. Choose the next semver tag: use **minor** if any skill has a minor bump,
   **patch** if all bumps are patch-only.
3. Create the tag locally: `git tag <version>`.
4. Create the GitHub release **before pushing the tag** using
   `gh release create <version> --target main` with a hand-written summary
   including:
   - Grouped changes (features, infrastructure, refactoring, fixes).
   - A skill versions table showing each changed skill's old → new version.
5. Push the tag: `git push origin <version>`.

**Order matters:** the release must exist before the tag is pushed because
the release workflow uploads assets to the existing release. If the tag is
pushed first, the workflow will fail with "release not found".

## TODO.md

When completing items from TODO.md, **remove** the finished entries entirely
rather than marking them `[x]`. If an entire section becomes empty, remove the
section heading too. Only pending work belongs in TODO.md.

## Skill Invocation

Use `/jira` to invoke the Jira skill, or describe what you want naturally:
- "Search Jira for my open issues"
- "Create a bug in PROJECT about login failures"
