# Advanced Commands

## config

Manage configuration and view effective defaults.

```bash
# Show all configuration and defaults
$SKILL_DIR/scripts/jira.py config show

# Show project-specific defaults
$SKILL_DIR/scripts/jira.py config show --project DEMO

# Discover and save a custom field mapping
$SKILL_DIR/scripts/jira.py config discover story_points
$SKILL_DIR/scripts/jira.py config discover security_level
```

`config show` displays authentication settings (masked token), default JQL scope, security level, max results, fields, and project-specific defaults.

`config discover` takes a snake_case friendly name, queries the Jira API for a matching field (underscores become spaces for matching, case-insensitive), and saves the mapping to `~/.config/agent-skills/jira.yaml` under `defaults.custom_fields`.

## fields

List available fields in your Jira instance.

```bash
# List all global fields
$SKILL_DIR/scripts/jira.py fields

# List fields for specific project and issue type
$SKILL_DIR/scripts/jira.py fields --project DEMO --issue-type Task
```

Fields vary by project and issue type. Use `--project` and `--issue-type` to see only the fields available in that context.

Custom fields appear under their API ID. The Team field is commonly
`customfield_10001` and named `Team`. Pass its exact value with `--team`, or
let `--team-name` resolve a shared team name to that value.

## statuses

List available statuses and status categories.

```bash
# List all statuses
$SKILL_DIR/scripts/jira.py statuses

# List status categories (To Do, In Progress, Done)
$SKILL_DIR/scripts/jira.py statuses --categories
```

Use `statusCategory` in JQL queries for portable queries that work across projects:
- `statusCategory = "To Do"` — matches all statuses in the To Do category
- `statusCategory = "In Progress"` — matches all in-progress statuses
- `statusCategory = Done` — matches all completed statuses

## user

Search for Jira users by email, name, or username. On Jira Cloud, returns accountId values needed for JQL queries.

```bash
$SKILL_DIR/scripts/jira.py user search "jdoe@example.com"
$SKILL_DIR/scripts/jira.py user search "Jane Doe"
```

## collaboration

Discover collaboration patterns across issues. Any issue type can be
inspected with `--issuetype`; this replaces the former `collaboration epics`
subcommand.

```bash
# Find epics with multiple contributors
$SKILL_DIR/scripts/jira.py collaboration --project DEMO

# Require at least 3 contributors
$SKILL_DIR/scripts/jira.py collaboration --project DEMO --min-contributors 3

# Scope by team ID (from `fields` or the team profile URL)
$SKILL_DIR/scripts/jira.py collaboration \
  --team "ec74d716-af36-4b3c-950f-f79213d08f71-2249" --include-done

# Or resolve a shared team name to its ID
$SKILL_DIR/scripts/jira.py collaboration \
  --team-name "rhos-product-reldel" --include-done

# Which epics a person drove this quarter, with their peers
$SKILL_DIR/scripts/jira.py collaboration --project DEMO \
  --contributor "jane@example.com" --since 2026-07-01 --until 2026-09-30

# Retrospective: epics resolved in Q3, including completed ones
$SKILL_DIR/scripts/jira.py collaboration --project DEMO \
  --contributor "jane@example.com" --date-field resolved \
  --since 2026-07-01 --until 2026-09-30 --include-done

# Execution-level ownership: stories and tasks across the team
$SKILL_DIR/scripts/jira.py collaboration --team-name "rhos-product-reldel" \
  --issuetype Story,Task

# Higher levels too: feature, initiative, outcome or subtask
$SKILL_DIR/scripts/jira.py collaboration --team-name "rhos-product-reldel" \
  --issuetype Initiative,Outcome --include-done

# Stop at direct children instead of walking the whole hierarchy
$SKILL_DIR/scripts/jira.py collaboration --project DEMO --direct-children-only
```

**Arguments:**
- `--project`: Project key to scope the search. Use `--team` or
  `--team-name` instead when work spans several projects.
- `--team`: Team ID to scope by, trusted as supplied. Copy the exact value
  from `fields` or the team profile URL; some sites suffix the UUID. Repeat
  the flag for several teams.
- `--team-name`: Team name to resolve to its ID. Names use the JQL
  autocomplete endpoint, which only returns shared teams; repeat the flag
  for several. Unknown or ambiguous names fail with suggestions rather than
  returning an empty result.
- `--issuetype`: Comma-separated issue types (default: `Epic`). Any level
  works: `Feature`, `Initiative`, `Outcome`, `Story,Task`, or `Subtask`.
- `--direct-children-only`: Match contributors from direct children only.
  By default the whole descendant hierarchy is walked.
- `--contributor`: Only items this user contributed to (item reporter or
  assignee, or assignee of a descendant). Accepts an accountId, an exact
  email, or a display name; display names are resolved through Jira user
  search and can be ambiguous, so prefer an accountId or email. Peer
  contributors are still listed.
- `--since` / `--until`: Inclusive `YYYY-MM-DD` bounds on the field named by
  `--date-field`. An item counts as in range when that field falls inside it.
- `--date-field`: Field the bounds and sort order use: `created`, `updated`
  (default) or `resolved`. Use `resolved` for a period review; unresolved
  items have no resolved date and are excluded.
- `--include-done`: Include items in the Done status category.
- `--status`: Comma-separated status names (e.g. `Closed,Done`) to match
  instead of the default Done exclusion.
- `--min-contributors`: Minimum unique contributors to qualify (default: 2, or
  1 when `--contributor` is used, so items the person drove alone are kept)
- `--max-results`: Maximum items to check (default: 50)

Done items are excluded by default, which suits an in-flight view. Use
`--include-done` or `--status` when a retrospective needs completed items;
without one of them a closed item will not appear even if the person is its
reporter or assignee.

Contributors are the item's reporter and assignee plus the assignees of its
descendants. Recursive descent is the default because ownership usually sits
below the epic: an Initiative's contributors include epics, the stories under
them, and their subtasks. Traversal walks one hierarchy level per search, so
`--direct-children-only` is cheaper when only the first level matters. An
item with no children, such as a Subtask, uses only its reporter/assignee.
Descendant collection is capped at 1000 issues per item and warns when the
cap is reached.

With `--json`, each item carries `summary`, `status`, `issuetype`, `parent`,
`assignee`, `reporter`, `created` and `resolutiondate`, plus
`children_count` (direct children) and `descendants_count` (all levels).
Level, provenance and hierarchy therefore come from the same query, with no
follow-up search over the returned keys.

**Note:** This makes N+1 API calls: 1 search for the items plus one search per
hierarchy level per item. Use `--max-results` and `--direct-children-only` to
control cost.

Run `fields` to find the Team field. It is listed with its API ID (commonly
`customfield_10001`) and the name `Team`. Pass the field's value with
`--team`, or let `--team-name` resolve a shared team name to that value.

## automations

List and inspect Jira automation rules. Uses the Automation Rule Management API via the gateway path, reusing existing Jira Cloud credentials. The Automation API requires admin access.

```bash
# List all automation rules
$SKILL_DIR/scripts/jira.py automations list

# List rules scoped to a specific project
$SKILL_DIR/scripts/jira.py automations list --project OSPRH

# List only enabled rules
$SKILL_DIR/scripts/jira.py automations list --state ENABLED

# Get full details of a rule (triggers, conditions, actions)
$SKILL_DIR/scripts/jira.py automations get <rule-uuid>
```

**Arguments for `automations list`:**
- `--project`: Filter to rules scoped to this project key
- `--state`: Filter by state (`ENABLED` or `DISABLED`)
- `--limit`: Maximum rules to return (default: 100)

**Arguments for `automations get`:**
- `uuid` (positional): Automation rule UUID (shown in list output)

The `get` command renders a markdown document describing the rule step by step: metadata, trigger, conditions, actions, branches, and external connections. Component types are translated to human-readable labels (e.g., `jira.issue.event.trigger:created` → "Issue created") and value configurations are summarised inline.

**Note:** The automation API requires the Atlassian Cloud ID, which is fetched automatically from `_edge/tenant_info` and cached for the session.

## versions

List a project's versions (releases) and view release reports. A version's
numeric ID is the number in a release URL such as
`https://yourcompany.atlassian.net/projects/OSPRH/versions/106586/tab/release-report-all-issues`
(here the version ID is `106586`).

```bash
# List versions for a project (archived versions excluded by default)
$SKILL_DIR/scripts/jira.py versions list OSPRH

# Include archived versions
$SKILL_DIR/scripts/jira.py versions list OSPRH --archived

# Get details of a single version, with fixed/affected and unresolved counts
$SKILL_DIR/scripts/jira.py versions get 106586

# Release report: list issues in a version grouped by status category
$SKILL_DIR/scripts/jira.py versions issues 106586
$SKILL_DIR/scripts/jira.py versions issues 106586 --max-results 500
```

**Arguments for `versions list`:**
- `project` (positional): Project key (e.g., OSPRH) or numeric project ID
- `--archived`: Include archived versions (excluded by default)

**Arguments for `versions get`:**
- `version_id` (positional): Numeric version ID (e.g., 106586)

**Arguments for `versions issues`:**
- `version_id` (positional): Numeric version ID (e.g., 106586)
- `--max-results`: Maximum number of issues (default: 200)
- `--fields`: Comma-separated list of fields to include

The `issues` subcommand reproduces the Jira "Release report" by querying
`fixVersion = <id>` and grouping the results by status category (To Do,
In Progress, Done). Configured custom fields are included in the output.
