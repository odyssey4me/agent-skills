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
python jira.py check
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

### Option 2: System Keyring (Interactive)

```bash
python scripts/setup_auth.py jira
```

This will prompt for your credentials and store them securely in your system keyring.

### Required Credentials

- **URL**: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
- **Email**: Your Atlassian account email
- **API Token**: Create at https://id.atlassian.com/manage-profile/security/api-tokens

## Commands

### check

Verify configuration and connectivity.

```bash
python jira.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Jira
- API version is detected correctly

### search

Search for issues using JQL (Jira Query Language).

```bash
python jira.py search "project = DEMO AND status = Open"
python jira.py search "assignee = currentUser() ORDER BY updated DESC" --max-results 20
```

**Arguments:**
- `jql`: JQL query string (required)
- `--max-results`: Maximum number of results (default: 50)
- `--fields`: Comma-separated list of fields to include
- `--json`: Output as JSON

### issue

Get, create, update, or comment on issues.

```bash
# Get issue details
python jira.py issue get DEMO-123

# Create new issue
python jira.py issue create --project DEMO --type Task --summary "New task"

# Update issue
python jira.py issue update DEMO-123 --summary "Updated summary"

# Add comment
python jira.py issue comment DEMO-123 "This is a comment"

# Add private comment with security level
python jira.py issue comment DEMO-123 "Internal note" --security-level "Red Hat Internal"
```

### transitions

Manage issue workflow transitions.

```bash
# List available transitions
python jira.py transitions list DEMO-123

# Transition issue
python jira.py transitions do DEMO-123 "In Progress"
python jira.py transitions do DEMO-123 "Done" --comment "Completed"

# Transition with private comment
python jira.py transitions do DEMO-123 "Done" --comment "Internal resolution notes" --security-level "Red Hat Internal"
```

## Examples

### Verify Setup

```bash
python jira.py check
```

### Find my open issues

```bash
python jira.py search "assignee = currentUser() AND status != Done ORDER BY priority DESC"
```

### Create a bug report

```bash
python jira.py issue create \
  --project DEMO \
  --type Bug \
  --summary "Login button not working" \
  --description "The login button on the homepage does not respond to clicks."
```

### Move issue through workflow

```bash
# Start work on an issue
python jira.py transitions do DEMO-123 "In Progress"

# Complete the issue
python jira.py transitions do DEMO-123 "Done" --comment "Implemented and tested"
```

### Add private comment

```bash
# Add comment visible only to specific security level
python jira.py issue comment DEMO-123 \
  "This is sensitive internal information" \
  --security-level "Red Hat Internal"
```

### Search with specific fields

```bash
python jira.py search \
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

### Check command fails

Run `python jira.py check` to diagnose issues. It will provide specific error messages and setup instructions.

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
