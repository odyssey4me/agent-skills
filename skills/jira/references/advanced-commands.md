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

Discover collaboration patterns across issues and epics.

```bash
# Find epics with multiple contributors (assignees)
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO

# Require at least 3 contributors
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO --min-contributors 3

# Limit number of epics checked
$SKILL_DIR/scripts/jira.py collaboration epics --max-results 20
```

**Arguments:**
- `--project`: Project key to scope the search
- `--min-contributors`: Minimum unique assignees to qualify (default: 2)
- `--max-results`: Maximum epics to check (default: 50)

**Note:** This makes N+1 API calls (1 for epics + 1 per epic for children). Use `--max-results` to control cost.

## automations

List and inspect Jira automation rules. Uses the Automation Rule Management API via the gateway path, reusing existing Jira Cloud credentials. **Cloud-only** — Data Center and Server instances will receive a clear error.

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
