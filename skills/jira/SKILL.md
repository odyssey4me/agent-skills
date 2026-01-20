# Jira

Interact with Jira for issue tracking, search, and workflow management.

## Authentication

Configure Jira authentication:

```bash
python scripts/setup_auth.py jira
```

Required credentials:
- **URL**: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
- **Email**: Your Atlassian account email
- **API Token**: Create at https://id.atlassian.com/manage-profile/security/api-tokens

## Commands

### search

Search for issues using JQL (Jira Query Language).

```bash
python skills/jira/scripts/search.py "project = DEMO AND status = Open"
python skills/jira/scripts/search.py "assignee = currentUser() ORDER BY updated DESC" --max-results 20
```

**Arguments:**
- `jql`: JQL query string (required)
- `--max-results`: Maximum number of results (default: 50)
- `--fields`: Comma-separated list of fields to include

### issue

Get, create, or update an issue.

```bash
# Get issue details
python skills/jira/scripts/issue.py get DEMO-123

# Create new issue
python skills/jira/scripts/issue.py create --project DEMO --type Task --summary "New task"

# Update issue
python skills/jira/scripts/issue.py update DEMO-123 --summary "Updated summary"

# Add comment
python skills/jira/scripts/issue.py comment DEMO-123 "This is a comment"
```

### transitions

Manage issue workflow transitions.

```bash
# List available transitions
python skills/jira/scripts/transitions.py list DEMO-123

# Transition issue
python skills/jira/scripts/transitions.py do DEMO-123 "In Progress"
python skills/jira/scripts/transitions.py do DEMO-123 "Done" --comment "Completed"
```

## Examples

### Find my open issues

```bash
python skills/jira/scripts/search.py "assignee = currentUser() AND status != Done ORDER BY priority DESC"
```

### Create a bug report

```bash
python skills/jira/scripts/issue.py create \
  --project DEMO \
  --type Bug \
  --summary "Login button not working" \
  --description "The login button on the homepage does not respond to clicks."
```

### Move issue through workflow

```bash
# Start work on an issue
python skills/jira/scripts/transitions.py do DEMO-123 "In Progress"

# Complete the issue
python skills/jira/scripts/transitions.py do DEMO-123 "Done" --comment "Implemented and tested"
```

### Search with specific fields

```bash
python skills/jira/scripts/search.py \
  "project = DEMO AND created >= -7d" \
  --fields "key,summary,status,assignee,created"
```

## JQL Reference

Common JQL queries:

| Query | Description |
|-------|-------------|
| `project = DEMO` | Issues in DEMO project |
| `assignee = currentUser()` | Issues assigned to you |
| `status = "In Progress"` | Issues in progress |
| `created >= -7d` | Created in last 7 days |
| `updated >= startOfDay()` | Updated today |
| `priority = High` | High priority issues |
| `labels = "bug"` | Issues with "bug" label |

Combine with `AND`, `OR`, and use `ORDER BY` for sorting.

## Troubleshooting

### Authentication failed

1. Verify your API token is correct
2. Ensure you're using your email (not username)
3. Check your Jira URL includes `/rest/api/3`

### Permission denied

You may not have access to the requested project or issue. Contact your Jira administrator.

### JQL syntax error

Use the Jira web interface to test your JQL query before using it in scripts.
