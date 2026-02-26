---
name: jira
description: Search and manage Jira issues using JQL queries, create/update tickets, and manage workflows. Use when asked to find Jira tickets, check the backlog, manage sprints, track bugs, or work with Atlassian project management.
metadata:
  author: odyssey4me
  version: "0.3.0"
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

After installation, verify the skill is properly configured:

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

Optionally configure defaults in `~/.config/agent-skills/jira.yaml` to reduce repetitive typing:

```yaml
# Authentication (optional if using environment variables)
url: https://yourcompany.atlassian.net
email: you@example.com
token: your-token

# Optional defaults
defaults:
  jql_scope: "project = DEMO AND assignee = currentUser()"
  security_level: "Red Hat Internal"
  max_results: 25
  fields: ["summary", "status", "assignee", "priority", "created"]

# Optional project-specific defaults
projects:
  DEMO:
    issue_type: "Task"
    priority: "Medium"
  PROD:
    issue_type: "Bug"
    priority: "High"
```

### How Defaults Work

- **CLI arguments always override** config defaults
- **JQL scope** is prepended to all searches: `(scope) AND (your_query)`
- **Security level** applies to comments and transitions with comments
- **Project defaults** apply when creating issues in that project

### View Configuration

```bash
# Show all configuration
$SKILL_DIR/scripts/jira.py config show

# Show project-specific defaults
$SKILL_DIR/scripts/jira.py config show --project DEMO
```

## Commands

### check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/jira.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Jira
- API version is detected correctly

### search

Search for issues using JQL (Jira Query Language).

```bash
# Standard JQL
$SKILL_DIR/scripts/jira.py search "project = DEMO AND status = Open"
$SKILL_DIR/scripts/jira.py search "assignee = currentUser() ORDER BY updated DESC" --max-results 20

# ScriptRunner Enhanced Search (if available)
# Find issues linked to a specific issue
$SKILL_DIR/scripts/jira.py search 'issue in linkedIssuesOf("DEMO-123")'

# Find parent/child relationships
$SKILL_DIR/scripts/jira.py search 'issue in parentsOf("DEMO-123")'
$SKILL_DIR/scripts/jira.py search 'issue in subtasksOf("DEMO-123")'

# Find issues commented on by a specific user
$SKILL_DIR/scripts/jira.py search 'issue in commentedByUser("username")'

# Find epics and their issues
$SKILL_DIR/scripts/jira.py search 'issue in epicsOf("DEMO-123")'
$SKILL_DIR/scripts/jira.py search 'issue in issuesInEpics("EPIC-123")'

# Find issues with specific link types (dependencies, blocks, etc.)
$SKILL_DIR/scripts/jira.py search 'issue in hasLinkType("Dependency")'
```

**Arguments:**
- `jql`: JQL query string (required unless `--contributor` is used) - supports ScriptRunner functions if installed
- `--contributor`: Search for issues where this user is a contributor (reporter, assignee, or commenter). Requires ScriptRunner for comment-based matching.
- `--project`: Project key to scope a `--contributor` search
- `--max-results`: Maximum number of results (default: 50)
- `--fields`: Comma-separated list of fields to include

**ScriptRunner Support:**

The skill automatically detects if ScriptRunner Enhanced Search is installed and validates queries that use advanced JQL functions. If ScriptRunner functions are detected but the plugin is not available, you'll receive a warning.

Common ScriptRunner functions include:
- `linkedIssuesOf()`, `hasLinkType()` - Link and dependency queries
- `subtasksOf()`, `parentsOf()`, `epicsOf()` - Hierarchy navigation
- `commentedByUser()`, `transitionedBy()` - User activity tracking
- And many more...

**For complete ScriptRunner guidance** including user lookups, practical examples, and troubleshooting, read [scriptrunner.md](references/scriptrunner.md).

Note: ScriptRunner works differently on Cloud vs Data Center/Server instances. The skill handles both automatically.

### issue

Get, create, update, or comment on issues.

```bash
# Get issue details
$SKILL_DIR/scripts/jira.py issue get DEMO-123

# Get issue with specific fields only
$SKILL_DIR/scripts/jira.py issue get DEMO-123 --fields "summary,status,assignee"

# Get issue with contributors listed
$SKILL_DIR/scripts/jira.py issue get DEMO-123 --contributors

# List comments on an issue
$SKILL_DIR/scripts/jira.py issue comments DEMO-123
$SKILL_DIR/scripts/jira.py issue comments DEMO-123 --max-results 10

# Create new issue
$SKILL_DIR/scripts/jira.py issue create --project DEMO --type Task --summary "New task"

# Update issue
$SKILL_DIR/scripts/jira.py issue update DEMO-123 --summary "Updated summary"

# Add comment
$SKILL_DIR/scripts/jira.py issue comment DEMO-123 "This is a comment"

# Add private comment with security level
$SKILL_DIR/scripts/jira.py issue comment DEMO-123 "Internal note" --security-level "Red Hat Internal"
```

**Arguments for `issue get`:**
- `issue_key`: Issue key (required)
- `--fields`: Comma-separated list of fields to include (uses config default if not specified)
- `--contributors`: Show unique contributors (reporter, assignee, comment authors). Opt-in; requires an extra API call.

**Arguments for `issue comments`:**
- `issue_key`: Issue key (required)
- `--max-results`: Maximum number of comments (default: 50)

### transitions

Manage issue workflow transitions.

```bash
# List available transitions
$SKILL_DIR/scripts/jira.py transitions list DEMO-123

# Transition issue
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "In Progress"
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "Done" --comment "Completed"

# Transition with private comment
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "Done" --comment "Internal resolution notes" --security-level "Red Hat Internal"
```

### config

Manage configuration and view effective defaults.

```bash
# Show all configuration and defaults
$SKILL_DIR/scripts/jira.py config show

# Show project-specific defaults
$SKILL_DIR/scripts/jira.py config show --project DEMO
```

This displays:
- Authentication settings (with masked token)
- Default JQL scope, security level, max results, and fields
- Project-specific defaults for issue type and priority

### fields

List available fields in your Jira instance.

```bash
# List all global fields
$SKILL_DIR/scripts/jira.py fields

# List fields for specific project and issue type
$SKILL_DIR/scripts/jira.py fields --project DEMO --issue-type Task
```

**Arguments:**
- `--project`: Project key for context-specific fields
- `--issue-type`: Issue type name (requires --project)

**Note:** Fields vary by project and issue type. When creating or searching issues, use `--project` and `--issue-type` to see only the fields available in that context.

### statuses

List available statuses and status categories.

```bash
# List all statuses
$SKILL_DIR/scripts/jira.py statuses

# List status categories (To Do, In Progress, Done)
$SKILL_DIR/scripts/jira.py statuses --categories
```

**Arguments:**
- `--categories`: Show status categories instead of individual statuses

**Recommendation:** Use `statusCategory` in JQL queries for more portable queries:
- `statusCategory = "To Do"` - matches all statuses in the To Do category
- `statusCategory = "In Progress"` - matches all in-progress statuses
- `statusCategory = Done` - matches all completed statuses

This is more reliable than using specific status names, which vary between projects.

### collaboration

Discover collaboration patterns across issues and epics.

```bash
# Find epics with multiple contributors (assignees)
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO

# Require at least 3 contributors
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO --min-contributors 3

# Limit number of epics checked
$SKILL_DIR/scripts/jira.py collaboration epics --max-results 20
```

**Arguments for `collaboration epics`:**
- `--project`: Project key to scope the search
- `--min-contributors`: Minimum unique assignees to qualify (default: 2)
- `--max-results`: Maximum epics to check (default: 50)

**Note:** This makes N+1 API calls (1 for epics + 1 per epic for children). Use `--max-results` to control cost.

## Examples

### Create and verify an issue

```bash
# Create the issue
$SKILL_DIR/scripts/jira.py issue create \
  --project DEMO \
  --type Bug \
  --summary "Login button not working" \
  --description "The login button on the homepage does not respond to clicks."

# Verify it was created correctly
$SKILL_DIR/scripts/jira.py issue get DEMO-456
```

### Move issue through workflow

```bash
# Check available transitions first
$SKILL_DIR/scripts/jira.py transitions list DEMO-123

# Start work on an issue
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "In Progress"

# Verify the transition
$SKILL_DIR/scripts/jira.py issue get DEMO-123 --fields "summary,status"
```

See [examples.md](references/examples.md) for more usage patterns.

## JQL Reference

Common JQL queries and patterns: see [jql-reference.md](references/jql-reference.md).

Quick reference — combine with `AND`, `OR`, and `ORDER BY`:

```jql
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC
```

Use `statusCategory` (`"To Do"`, `"In Progress"`, `Done`) for queries that work across projects.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Check command fails

Run `$SKILL_DIR/scripts/jira.py check` to diagnose issues. It will provide specific error messages and setup instructions.

### Authentication failed

1. Verify your API token is correct
2. Ensure you're using your email (not username)
3. For Jira Cloud, use your Atlassian account email
4. For Jira Data Center/Server, use your username

### Permission denied

You may not have access to the requested project or issue. Contact your Jira administrator.

### JQL syntax error

Use the Jira web interface to test your JQL query before using it in scripts.

### Import errors

Ensure dependencies are installed:
```bash
pip install --user requests keyring pyyaml
```
