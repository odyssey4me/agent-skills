# Roadmap

This document tracks planned features for the agent-skills repository. Only pending work belongs here — remove items as they are delivered.

## Tessl Review Recommendations

Recommendations from `tessl skill review` to improve skill quality scores.
Common issues flagged across multiple skills are grouped first, followed by
per-skill items.

### Common: Description Improvements

Most skills score low on trigger term coverage. Add natural language
variations users might say to each skill's description.

- [x] **code-review** (33% → 100%) — Added `Use when...` clause with trigger
  terms: pull request, merge request, review my code, check this PR, patchset,
  code review feedback
- [x] **github** (67% → 100%) — Added action verbs and trigger terms: PR,
  repo, actions, merge
- [x] **gitlab** (57% → 100%) — Added action verbs and trigger terms: MR,
  CI/CD, merge request, code review
- [x] **gerrit** (75% → 100%) — Added amend, rebase, patchset, change
  request, CR
- [x] **google-docs** (75% → 100%) — Added insert tables, heading styles,
  gdoc, Google document
- [x] **google-slides** (77% → 100%) — Added slides, slideshow, deck,
  Google presentation
- [x] **gmail** (85% → 100%) — Added compose, reply, forward, attachments,
  mail
- [x] **google-calendar** (85% → 100%) — Added meeting, appointment,
  schedule a call, book time, gcal
- [x] **google-drive** (85% → 100%) — Added gdrive, cloud storage, share a
  file, Drive folder
- [x] **google-sheets** (85% → 100%) — Added gsheets, Google spreadsheet,
  pivot tables, charts
- [x] **jira** (85% → 100%) — Added tickets, sprints, backlog, Atlassian,
  bug tracking

### Common: Content Conciseness

Repeated across most skills — condense or deduplicate these patterns:

- [ ] **Consolidate auth reset instructions** — Several Google skills and
  Jira repeat the same auth reset steps in multiple sections. Reference a
  single troubleshooting section instead.
- [ ] **Trim installation/prerequisites** — Claude knows how to install pip
  packages and CLI tools. Reduce multi-platform installation instructions to
  a single link or one-liner.
- [ ] **Remove OAuth/rate-limit explanations** — Claude understands these
  concepts. Keep to a single line or remove entirely.

### Per-Skill Content Improvements

**code-review** (content: 85%, overall: 59%)
- [ ] Consolidate platform detection logic — explained in both Workflow and
  Commands sections
- [ ] Trim Repository Context section — YAML example is helpful but
  surrounding explanation is verbose

**github** (content: 73%, overall: 70%)
- [ ] Add validation/verification steps to workflows (e.g., verify PR created
  after creation commands)
- [ ] Remove or condense rate limits section

**gitlab** (content: 73%, overall: 65%)
- [ ] Add validation checkpoints to workflow examples
- [ ] Remove the Summary section which repeats Quick Start content

**gerrit** (content: 77%, overall: 76%)
- [ ] Move Troubleshooting section to `references/troubleshooting.md`
- [ ] Move Advanced Usage (SSH Commands, JSON Output) to a reference file

**gmail** (content: 85%, overall: 85%)
- [ ] Remove duplicate API Scopes section (already in Authentication section)

**google-calendar** (content: 77%, overall: 81%)
- [ ] Move detailed command reference to a separate reference file to reduce
  SKILL.md length (491 lines)

**google-docs** (content: 85%, overall: 80%)
- [ ] Consolidate authentication troubleshooting into a single section

**google-drive** (content: 77%, overall: 81%)
- [ ] Move MIME types table, unsupported operations table, and API scopes to
  a reference file (SKILL.md is 511 lines, over the 500-line recommendation)
- [ ] Remove duplicate OAuth scopes information

**google-sheets** (content: 85%, overall: 85%)
- [ ] Consolidate repeated troubleshooting advice across sections

**google-slides** (content: 73%, overall: 75%)
- [ ] SKILL.md is 612 lines — move content to reference files to get under 500
- [ ] Add validation steps in multi-step workflow examples
- [ ] Remove explanatory text Claude already knows (e.g., 'Slide IDs are
  object IDs, not indices')
- [ ] Consolidate troubleshooting — several items repeat the same solution

**jira** (content: 65%, overall: 75%)
- [ ] Move JQL Reference table, Rate Limits section, and extensive examples
  to separate reference files (SKILL.md is 504 lines)
- [ ] Add validation steps to multi-step workflows
- [ ] Trim Rate Limits section significantly

## Google Drive Enhancements

- [ ] **google-drive** - Add missing Drive API operations
  - [ ] Rename files (`files.update` with name)
  - [ ] Delete files permanently (`files.delete`)
  - [ ] Trash / untrash files (`files.update` with trashed)
  - [ ] Copy files (`files.copy`)
  - [ ] Export Google Docs/Sheets/Slides (`files.export`)
  - [ ] Update existing permissions / change role (`permissions.update`)
  - [ ] Empty trash (`files.emptyTrash`)
  - [ ] File version history (`revisions.*`)
  - [ ] Comments and replies (`comments.*`, `replies.*`)
  - [ ] Watch for file changes (`files.watch`, `changes.*`)
  - [ ] Shared drive management (`drives.*`)

## Infrastructure Improvements

- [ ] Consider migrating Jira skill to use official Atlassian CLI (ACLI)
  - Official ACLI released May 2025 for Jira Cloud
  - Covers issue management, JQL search, projects, transitions
  - Would reduce maintenance burden (no custom API wrapper to maintain)
  - Current custom script works well - no urgent need to migrate
  - See: https://developer.atlassian.com/cloud/acli/guides/introduction/

## Remove skills.json Registry

- [ ] **Remove `skills.json` and `generate_registry.py`** — The registry
  duplicates SKILL.md frontmatter and is not consumed by any external tool
  (`npx add-skill` reads SKILL.md directly via `gray-matter`). Replace the
  CI drift-detection check with `tessl skill lint` or
  `python scripts/validate_skill.py` which already validate frontmatter
  against the source of truth. Remove `skills.json`,
  `scripts/generate_registry.py`, `tests/test_generate_registry.py`, and
  the pre-commit hook that runs `generate_registry.py --check`.

## Collaboration Surfacing

Add collaboration surfacing features to github, gitlab, and gerrit skills,
mirroring the patterns established in the jira skill (commit 8ccd2c1).

Each subsection below is self-contained and can be implemented in an
independent session. Reference `skills/jira/scripts/jira.py` for
implementation patterns (comments retrieval, contributor extraction,
contributor search, collaborative discovery).

### GitHub Skill

**Files:** `skills/github/scripts/github.py`, `skills/github/SKILL.md`, `tests/test_github.py`
**Version bump:** 0.2.0 → 0.3.0

- [ ] **Comments retrieval** — Add `issues comments` and `prs comments`
  subcommands to fetch and format comments on issues and pull requests.
  - Add `get_comments(owner_repo, number)` using
    `run_gh(["api", "repos/{owner}/{repo}/issues/{number}/comments", ...])`.
    GitHub uses the same endpoint for issue and PR comments.
  - Add `format_comments(comments, number)` producing markdown with author
    login, created timestamp (via `format_date`), and body.
  - Add `comments` subparser under both `issues` and `prs` with args:
    `number` (positional int), `--repo/-R`, `--max-results` (default 50),
    `--json`.
  - Add `cmd_issues_comments(args)` and `cmd_prs_comments(args)` handlers
    (or a shared handler since the API is identical).

- [ ] **Contributor extraction on view** — Add `--contributors` flag to
  `issues view` and `prs view` to show unique participants.
  - Add `extract_contributors(item, comments)` returning `set[str]` of unique
    login names from: author, assignees, comment authors, and (for PRs)
    requested reviewers.
  - In view handlers: when flag is set, fetch comments via `get_comments()`,
    call `extract_contributors()`, append "Contributors" section to markdown
    (or `_contributors` key to JSON).

- [ ] **Contributor search** — Add `--contributor` flag to `search issues`
  and `search prs` subcommands.
  - Make `query` positional optional (`nargs="?"`, `default=None`).
  - When `--contributor` is set, use `involves:USER` qualifier in search.
    Combine with any additional query text if provided.

- [ ] **Collaborative repos discovery** — Add `collaboration repos`
  subcommand to find repositories with multi-contributor pull requests.
  - Add `collaboration` top-level subparser with `repos` subcommand.
  - Add `find_collaborative_repos(org=None, min_contributors=2, max_results=50)`:
    list repos, fetch recent merged PRs per repo, collect unique participants
    (author + reviewers), filter to repos with PRs having >=
    `min_contributors` participants.
  - Add `format_collaborative_repos(results)` for markdown output.
  - Add `cmd_collaboration(args)` handler.
  - Args: `--org` (optional), `--min-contributors` (default 2),
    `--max-results` (default 50), `--json`.
  - Document N+1 API call cost in SKILL.md.

- [ ] **Documentation and tests**
  - Update SKILL.md with new command sections, examples, and flag docs.
  - Add test classes: `TestComments`, `TestContributors`,
    `TestCollaborativeRepos`, plus `TestBuildParser` updates.
  - Bump version 0.2.0 → 0.3.0.

### GitLab Skill

**Files:** `skills/gitlab/scripts/gitlab.py`, `skills/gitlab/SKILL.md`, `tests/test_gitlab.py`
**Version bump:** 0.2.0 → 0.3.0

- [ ] **Notes retrieval** — Add `issues notes` and `mrs notes` subcommands
  to fetch and format notes (GitLab's term for comments).
  - Add `get_notes(repo, entity_type, iid, max_results=50)` using
    `run_glab(["api", "projects/{repo_encoded}/{entity_type}/{iid}/notes"])`.
    URL-encode the repo path for the API.
  - Add `format_notes(notes, iid, entity_type)` producing markdown. Filter
    out system notes (`system: true`) to show only human comments.
  - Add `notes` subparser under both `issues` and `mrs` with args:
    `number` (positional int), `--repo/-R`, `--max-results` (default 50),
    `--json`.

- [ ] **Contributor extraction on view** — Add `--contributors` flag to
  `issues view` and `mrs view` to show unique participants.
  - Add `extract_contributors(item, notes)` returning `set[str]` of unique
    usernames from: author, assignees, reviewers (MRs), note authors
    (excluding system notes).
  - In view handlers: when flag is set, fetch notes via `get_notes()`, call
    `extract_contributors()`, append "Contributors" section to markdown
    (or `_contributors` key to JSON).

- [ ] **Contributor search** — Add `search` top-level subcommand with
  `issues` and `mrs` subsubcommands supporting `--contributor` flag.
  - Add `search_by_contributor(user, entity_type, project=None, max_results=50)`
    using GitLab API with `author_username` OR `assignee_username` filters,
    merging results.
  - Each search subcommand takes: `query` (optional positional),
    `--contributor`, `--repo/-R`, `--limit` (default 30), `--json`.

- [ ] **Collaborative projects discovery** — Add `collaboration projects`
  subcommand to find projects with multi-contributor merge requests.
  - Add `collaboration` top-level subparser with `projects` subcommand.
  - Add `find_collaborative_projects(group=None, min_contributors=2, max_results=50)`:
    list projects, fetch recent merged MRs per project, collect unique
    participants (author + reviewers + assignees), filter to projects with
    MRs having >= `min_contributors` participants.
  - Add `format_collaborative_projects(results)` for markdown output.
  - Add `cmd_collaboration(args)` handler.
  - Args: `--group` (optional), `--min-contributors` (default 2),
    `--max-results` (default 50), `--json`.

- [ ] **Documentation and tests**
  - Update SKILL.md with new command sections, examples, and flag docs.
  - Add test classes: `TestNotes`, `TestContributors`,
    `TestCollaborativeProjects`, plus `TestBuildParser` updates.
  - Bump version 0.2.0 → 0.3.0.

### Gerrit Skill

**Files:** `skills/gerrit/scripts/gerrit.py`, `skills/gerrit/SKILL.md`, `tests/test_gerrit.py`
**Version bump:** 0.2.0 → 0.3.0

- [ ] **Full comments retrieval** — Add `changes comments` subcommand.
  Expand existing comment display (currently limited to last 5 in
  `changes view`) with full comment listing.
  - Add `get_comments(host, port, change_number, username=None)` using
    `gerrit query change:{number} --comments --patch-sets --format=JSON`.
    Parse both file-level and change-level comments.
  - Add `format_comments(comments, change_number)` producing markdown with
    reviewer name, timestamp, message, and optionally file path for inline
    comments.
  - Add `comments` subparser under `changes` with args: `number` (positional
    int), `--patch-sets` (flag for inline comments), `--json`.

- [ ] **Contributor extraction on view** — Add `--contributors` flag to
  `changes view` to show unique participants.
  - Add `extract_contributors(change)` returning `set[str]` of unique names
    from: owner, reviewers (from `currentPatchSet.approvals[].by`), comment
    authors (from `comments[].reviewer`).
  - In `cmd_changes_view`: when flag is set, call `extract_contributors()`
    on the change data (which already includes `--comments` and
    `--current-patch-set`) and append "Contributors" section.

- [ ] **Contributor search** — Enhance `changes search` to accept
  `--contributor` flag.
  - Make `query` positional optional (`nargs="?"`, `default=None`).
  - Add `search_by_contributor(host, port, user, extra_query=None)` building
    Gerrit query: `(owner:{user} OR reviewer:{user})`. Append extra query
    terms if provided.
  - In `cmd_changes_search`: detect `--contributor` and route accordingly.

- [ ] **Collaborative topics discovery** — Add `collaboration topics`
  subcommand to find topics with changes from multiple owners.
  - Add `collaboration` top-level subparser with `topics` subcommand.
  - Add `find_collaborative_topics(host, port, min_contributors=2, max_results=50, project=None)`:
    query recent changes with topics (`status:merged -topic:""`), group by
    topic, collect unique owners per topic, filter to topics with >=
    `min_contributors` owners.
  - Add `format_collaborative_topics(results)` for markdown output.
  - Add `cmd_collaboration(args)` handler.
  - Args: `--project` (optional), `--min-contributors` (default 2),
    `--max-results` (default 50), `--json`.

- [ ] **Documentation and tests**
  - Update SKILL.md with new command sections, examples, and flag docs.
  - Add test classes: `TestComments`, `TestContributors`,
    `TestCollaborativeTopics`, plus `TestBuildParser` updates.
  - Bump version 0.2.0 → 0.3.0.
