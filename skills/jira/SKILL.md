---
name: jira
description: Search and manage Jira issues using JQL queries, create/update tickets, and manage workflows. Use when asked to find Jira tickets, check the backlog, manage sprints, track bugs, or work with Atlassian project management.
metadata:
  author: odyssey4me
  version: "0.10.2"
  category: project-management
  tags: "issues, agile, sprints"
  complexity: standard
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/jira.py:*)
---

# Jira

Interact with Jira for issue tracking, search, and workflow management.

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install --user requests keyring pyyaml
   ```

2. **Download the skill** from [Releases](https://github.com/odyssey4me/agent-skills/releases) or use directly from this repository.

## Setup Verification

After installation, verify the skill configuration by running:

```bash
$SKILL_DIR/scripts/jira.py check
```

This will check:
- Python dependencies (requests, keyring, pyyaml)
- Authentication configuration
- Connectivity to Jira

If anything is missing, the check command will provide setup instructions.

## Authentication

Configure Jira authentication using one of these methods:

### Option 1: Environment Variables (Recommended)

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="your-token"
```

Add these to your `~/.bashrc` or `~/.zshrc` for persistence.

### Option 2: Config File

Create `~/.config/agent-skills/jira.yaml`:

```yaml
url: https://yourcompany.atlassian.net
email: you@example.com
token: your-token
```

### Required Credentials

- **URL**: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
- **Email**: Your Atlassian account email
- **API Token**: Create at https://id.atlassian.com/manage-profile/security/api-tokens

## Configuration Defaults

Optionally configure defaults (JQL scope, fields, custom fields, project defaults) in `~/.config/agent-skills/jira.yaml`. CLI arguments always override config defaults. See [configuration.md](references/configuration.md) for the full config format and defaults behavior.

```bash
# Show all configuration
$SKILL_DIR/scripts/jira.py config show

# Show project-specific defaults
$SKILL_DIR/scripts/jira.py config show --project DEMO
```

## Commands

See [permissions.md](references/permissions.md) for read/write classification of each command.

### check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/jira.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Jira
- API version is detected and compatible

### search

Search for issues using JQL (Jira Query Language).

```bash
$SKILL_DIR/scripts/jira.py search "project = DEMO AND status = Open"
$SKILL_DIR/scripts/jira.py search "assignee = currentUser() ORDER BY updated DESC" --max-results 20
```

**Arguments:**
- `jql`: JQL query string (required unless `--contributor` is used)
- `--contributor`: Search for issues where this user is a contributor (reporter, assignee, or commenter). On Jira Cloud, automatically resolves email/name to accountId.
- `--project`: Project key to scope a `--contributor` search
- `--max-results`: Maximum number of results (default: 50)
- `--fields`: Comma-separated list of fields to include

**Deployment-specific queries:**

The available JQL functions depend on your Jira deployment type. Run
`check` to see your deployment type and ScriptRunner availability.

- **All deployments**: See [jql-reference.md](references/jql-reference.md)
  for standard JQL patterns (status, dates, fields, ordering).
- **Data Center/Server with ScriptRunner**: See
  [scriptrunner.md](references/scriptrunner.md) for advanced functions
  like `linkedIssuesOf()`, `subtasksOf()`, `commentedByUser()`.
- **Jira Cloud**: ScriptRunner functions are **not available**. Use the
  Cloud-native alternatives documented in
  [jql-reference.md](references/jql-reference.md#cloud-alternatives).

### issue

Get, create, update, or comment on issues.

```bash
# Get issue details (--fields, --contributors)
$SKILL_DIR/scripts/jira.py issue get DEMO-123
$SKILL_DIR/scripts/jira.py issue get DEMO-123 --fields "summary,status,assignee" --contributors

# List comments
$SKILL_DIR/scripts/jira.py issue comments DEMO-123

# Create (--project, --type, --summary required; --description, --priority, --labels, --assignee, --set-field, --link, --from-file, --json)
$SKILL_DIR/scripts/jira.py issue create --project DEMO --type Task --summary "New task"
$SKILL_DIR/scripts/jira.py issue create --from-file issue.md --priority Critical

# Update (--summary, --description, --priority, --labels, --assignee, --set-field, --link, --from-file)
$SKILL_DIR/scripts/jira.py issue update DEMO-123 --summary "Updated" --set-field story_points=5
$SKILL_DIR/scripts/jira.py issue update DEMO-123 --link "Blocks:DEMO-456"

# Comment (--security-level for private comments)
$SKILL_DIR/scripts/jira.py issue comment DEMO-123 "This is a comment"
```

See [from-file-format.md](references/from-file-format.md) for the `--from-file` markdown format and [examples.md](references/examples.md) for more patterns.

### transitions

Manage issue workflow transitions.

```bash
# List available transitions
$SKILL_DIR/scripts/jira.py transitions list DEMO-123

# Transition issue
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "In Progress"
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "Done" --comment "Completed"

# Transition with private comment
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "Done" --comment "Internal resolution notes" --security-level "Internal"
```

### Additional Commands

See [advanced-commands.md](references/advanced-commands.md) for full documentation of these commands:

- **config** — view/manage configuration defaults and discover custom field mappings
- **fields** — list available fields (global or per project/issue type)
- **statuses** — list statuses and status categories
- **user** — search users by email/name (returns accountId on Cloud)
- **collaboration** — discover cross-team collaboration patterns in epics
- **automations** — list and inspect Jira automation rules (Cloud-only)

## JQL Reference

Common JQL queries and patterns: see [jql-reference.md](references/jql-reference.md).

Quick reference — combine with `AND`, `OR`, and `ORDER BY`:

```jql
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC
```

Use `statusCategory` (`"To Do"`, `"In Progress"`, `Done`) for queries that work across projects.

## Examples

Common Jira workflows:

**Search and view:**
```bash
# Find all open tasks assigned to you
jira search "assignee = currentUser() AND status = Open"

# Get issue details
jira issue get DEMO-123 --fields "summary,status,assignee"

# List issue comments
jira issue comments DEMO-123
```

**Create and update:**
```bash
# Create a new bug
jira issue create --project DEMO --type Bug --summary "Login page broken"

# Update an issue and add a comment
jira issue update DEMO-123 --priority High --assignee "user@example.com"
jira issue comment DEMO-123 "Assigned to review"
```

**Workflow:**
```bash
# List available transitions
jira transitions list DEMO-123

# Move issue to Done
jira transitions do DEMO-123 "Done" --comment "Completed"
```

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

