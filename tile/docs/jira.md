# Jira Skill

The Jira skill (`jira.py`) is a self-contained Python CLI script for Jira issue tracking, search, and workflow management. It supports both Jira Cloud and Data Center/Server deployments.

## Installation & Setup

```bash
# Install runtime dependencies
pip install --user requests keyring pyyaml

# Verify setup
python jira.py check
```

The `check` command validates credentials, connectivity, API version detection, and ScriptRunner availability.

## Authentication Configuration

### Environment Variables (Recommended)

```bash
# Jira Cloud
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="your-api-token"

# Jira Data Center / Server (token auth)
export JIRA_URL="https://jira.yourcompany.com"
export JIRA_API_TOKEN="your-personal-access-token"

# Jira Data Center / Server (basic auth)
export JIRA_URL="https://jira.yourcompany.com"
export JIRA_USERNAME="your-username"
export JIRA_PASSWORD="your-password"
```

**Note**: `JIRA_BASE_URL` and `JIRA_URL` are both accepted for the URL. `JIRA_API_TOKEN` and `JIRA_TOKEN` are both accepted for the token.

### Config File

Create `~/.config/agent-skills/jira.yaml`:

```yaml
url: https://yourcompany.atlassian.net
email: you@example.com
token: your-api-token

# Optional defaults (reduce repetitive arguments)
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

**Credential priority**: keyring > environment variables > config file. CLI arguments always override defaults.

**Note**: In environments without a keyring backend (CI, containers), several functions that perform deployment detection (`get_api_version`, `format_rich_text`, `validate_jql_for_scriptrunner`) will raise `keyring.errors.NoKeyringError` if no credentials are otherwise configured. Set credentials via environment variables (`JIRA_BASE_URL`, `JIRA_API_TOKEN`, etc.) before calling these functions in keyring-less environments.

## Capabilities

### Check — Validate Configuration

```python { .api }
python jira.py check
```

Validates:
- Python dependencies (requests, keyring, pyyaml)
- Credentials (URL, token/email configured)
- Connectivity to Jira (deployment type detection)
- API version detected
- ScriptRunner availability

Returns exit code 0 on success, 1 on failure.

### Search — Find Issues with JQL

```python { .api }
python jira.py search <jql> [--max-results N] [--fields f1,f2,...] [--json]
```

Parameters:
- `jql` (required): JQL query string. Supports standard JQL and ScriptRunner Enhanced Search functions.
- `--max-results N`: Maximum results (default: 50, or configured default)
- `--fields f1,f2`: Comma-separated field list (default: summary, status, assignee, priority, created, updated)
- `--json`: Output raw JSON instead of formatted table

If a configured `jql_scope` default exists, it is prepended: `({scope}) AND ({your_jql})`.

**Output**: Table with Key, Summary, Status, Assignee columns. With `--json`: list of Jira issue objects.

```bash
# Standard JQL
python jira.py search "project = DEMO AND status = Open"
python jira.py search "assignee = currentUser() ORDER BY updated DESC" --max-results 20
python jira.py search "priority = High" --fields "key,summary,status,priority" --json

# ScriptRunner Enhanced Search (requires ScriptRunner plugin)
python jira.py search 'issue in linkedIssuesOf("DEMO-123")'
python jira.py search 'issue in subtasksOf("EPIC-1")'
python jira.py search 'issue in parentsOf("DEMO-123")'
python jira.py search 'issue in commentedByUser("accountId")'
python jira.py search 'issue in epicsOf("DEMO-123")'
python jira.py search 'issue in issuesInEpics("EPIC-123")'
python jira.py search 'issue in hasLinkType("Dependency")'
```

### Issue Get — Retrieve Issue Details

```python { .api }
python jira.py issue get <issue_key> [--json]
```

Parameters:
- `issue_key` (required): Issue key (e.g., `DEMO-123`)
- `--json`: Output raw JSON

**Output**: Formatted text with Issue, Summary, Status, Assignee, Priority. With `--json`: full Jira issue object.

```bash
python jira.py issue get DEMO-123
python jira.py issue get DEMO-123 --json
```

### Issue Create — Create New Issue

```python { .api }
python jira.py issue create \
  --project <project_key> \
  --summary <summary> \
  [--type <issue_type>] \
  [--description <description>] \
  [--priority <priority>] \
  [--labels <label1,label2>] \
  [--assignee <account_id>] \
  [--json]
```

Parameters:
- `--project` (required): Project key (e.g., `DEMO`)
- `--summary` (required): Issue summary
- `--type`: Issue type name (e.g., `Task`, `Bug`, `Story`). Required unless project default configured.
- `--description`: Issue description text
- `--priority`: Priority name (e.g., `High`, `Medium`, `Low`)
- `--labels`: Comma-separated labels
- `--assignee`: Assignee account ID (Cloud) or username (DC/Server)
- `--json`: Output created issue as JSON

If project defaults are configured, `--type` and `--priority` can be omitted.

**Output**: `Created issue: DEMO-456`. With `--json`: created issue object containing `key` field.

```bash
python jira.py issue create --project DEMO --type Task --summary "New feature"
python jira.py issue create --project DEMO --summary "Fix bug" \
  --type Bug --description "Steps to reproduce..." --priority High --labels "bugfix,urgent"
python jira.py issue create --project DEMO --summary "Task" --json
```

### Issue Update — Modify Existing Issue

```python { .api }
python jira.py issue update <issue_key> \
  [--summary <summary>] \
  [--description <description>] \
  [--priority <priority>] \
  [--labels <label1,label2>] \
  [--assignee <account_id>]
```

Parameters:
- `issue_key` (required): Issue key
- `--summary`: New summary
- `--description`: New description
- `--priority`: New priority name
- `--labels`: New labels (comma-separated; replaces all existing labels)
- `--assignee`: New assignee account ID

**Output**: `Updated issue: DEMO-123`

```bash
python jira.py issue update DEMO-123 --summary "Updated title"
python jira.py issue update DEMO-123 --priority High --labels "urgent,reviewed"
```

### Issue Comment — Add Comment to Issue

```python { .api }
python jira.py issue comment <issue_key> <body> [--security-level <group_name>]
```

Parameters:
- `issue_key` (required): Issue key
- `body` (required): Comment text
- `--security-level`: Group name for private comment visibility (e.g., `"Red Hat Internal"`, `"Employees"`). If a `security_level` default is configured, it is applied automatically unless overridden.

**Output**: `Added comment to DEMO-123` or `Added private comment to DEMO-123 (security level: Red Hat Internal)`

```bash
python jira.py issue comment DEMO-123 "This is a public comment"
python jira.py issue comment DEMO-123 "Internal note" --security-level "Red Hat Internal"
```

### Transitions List — View Available Workflow Transitions

```python { .api }
python jira.py transitions list <issue_key> [--json]
```

Parameters:
- `issue_key` (required): Issue key
- `--json`: Output raw JSON

**Output**: Table with ID, Transition name, To Status columns. With `--json`: list of transition objects.

```bash
python jira.py transitions list DEMO-123
```

### Transitions Do — Perform a Workflow Transition

```python { .api }
python jira.py transitions do <issue_key> <transition_name> \
  [--comment <comment>] \
  [--security-level <group_name>]
```

Parameters:
- `issue_key` (required): Issue key
- `transition_name` (required): Transition name (case-insensitive, e.g., `"In Progress"`, `"Done"`)
- `--comment`: Comment to add with the transition
- `--security-level`: Security level for private comment

Raises error with available transitions listed if transition name not found.

**Output**: `Transitioned DEMO-123 to 'In Progress'` (optionally with comment info)

```bash
python jira.py transitions do DEMO-123 "In Progress"
python jira.py transitions do DEMO-123 "Done" --comment "Implemented and tested"
python jira.py transitions do DEMO-123 "Done" --comment "Internal resolution" --security-level "Red Hat Internal"
```

### Config Show — Display Effective Configuration

```python { .api }
python jira.py config show [--project <project_key>]
```

Parameters:
- `--project`: Show project-specific defaults for this project key

**Output**: Authentication settings (with masked token), configured defaults (JQL scope, security level, max results, fields), project-specific defaults (issue type, priority).

```bash
python jira.py config show
python jira.py config show --project DEMO
```

## JQL Reference

Common JQL queries for the `search` command:

| Query | Description |
|-------|-------------|
| `project = DEMO` | All issues in project DEMO |
| `assignee = currentUser()` | Issues assigned to current user |
| `status = "In Progress"` | Issues currently in progress |
| `status != Done` | Issues not yet done |
| `created >= -7d` | Created in last 7 days |
| `updated >= startOfDay()` | Updated today |
| `priority = High` | High priority issues |
| `labels = "bugfix"` | Issues with specific label |
| `type = Bug` | All bugs |
| `reporter = currentUser()` | Issues I created |

Combine with `AND`, `OR`, `NOT`, and use `ORDER BY` for sorting:

```
project = DEMO AND status != Done AND assignee = currentUser() ORDER BY priority DESC
```

## ScriptRunner Enhanced Search Functions

When ScriptRunner is installed, additional JQL functions are available:

| Function | Description |
|----------|-------------|
| `linkedIssuesOf("ISSUE-1")` | Issues linked to ISSUE-1 |
| `linkedIssuesOfAll("ISSUE-1")` | Issues linked transitively |
| `linkedIssuesOfRecursive("ISSUE-1")` | Recursive linked issues |
| `hasLinks()` | Issues that have any links |
| `hasLinkType("Dependency")` | Issues with specific link type |
| `subtasksOf("EPIC-1")` | Subtasks of an issue |
| `parentsOf("DEMO-123")` | Parent issues |
| `hasSubtasks()` | Issues with subtasks |
| `epicsOf("DEMO-123")` | Epics containing an issue |
| `issuesInEpics("EPIC-1")` | Issues within an epic |
| `commentedByUser("accountId")` | Issues commented by user |
| `transitionedBy("accountId")` | Issues transitioned by user |
| `transitionedFrom("Open")` | Issues transitioned from status |
| `transitionedTo("Done")` | Issues transitioned to status |
| `issuesWithFieldValue("field","value")` | Issues with field value |

The skill automatically warns if ScriptRunner functions are detected but not available.

## Python API (Programmatic Use)

The skill can also be imported as a Python module for programmatic use:

```python { .api }
from skills.jira.scripts.jira import (
    # Credential management
    get_credential,        # get_credential(key: str) -> str | None
    set_credential,        # set_credential(key: str, value: str) -> None
    delete_credential,     # delete_credential(key: str) -> None
    get_credentials,       # get_credentials(service: str) -> Credentials
    load_config,           # load_config(service: str) -> dict | None
    save_config,           # save_config(service: str, config: dict) -> None
    get_jira_defaults,     # get_jira_defaults() -> JiraDefaults
    get_project_defaults,  # get_project_defaults(project: str) -> ProjectDefaults
    merge_jql_with_scope,  # merge_jql_with_scope(user_jql: str, scope: str | None) -> str

    # Deployment detection
    detect_deployment_type,      # detect_deployment_type(force_refresh=False) -> str
    get_api_version,             # get_api_version() -> str
    api_path,                    # api_path(endpoint: str) -> str
    is_cloud,                    # is_cloud() -> bool
    clear_cache,                 # clear_cache() -> None
    detect_scriptrunner_support, # detect_scriptrunner_support(force_refresh=False) -> dict
    validate_jql_for_scriptrunner, # validate_jql_for_scriptrunner(jql: str) -> dict

    # HTTP
    make_request,  # make_request(service, method, endpoint, *, params, json_data, headers, timeout) -> dict | list
    get,           # get(service, endpoint, **kwargs) -> dict | list
    post,          # post(service, endpoint, data, **kwargs) -> dict | list
    put,           # put(service, endpoint, data, **kwargs) -> dict | list
    delete,        # delete(service, endpoint, **kwargs) -> dict | list
    format_rich_text,  # format_rich_text(text: str) -> dict | str

    # Output formatting
    format_json,          # format_json(data, *, indent=2) -> str
    format_table,         # format_table(rows, columns, *, headers: dict[str,str] | None, max_width) -> str
    format_issue,         # format_issue(issue: dict) -> str
    format_issues_list,   # format_issues_list(issues: list) -> str

    # Issue operations
    search_issues,  # search_issues(jql, max_results=50, fields=None) -> list[dict]
    get_issue,      # get_issue(issue_key: str) -> dict
    create_issue,   # create_issue(project, issue_type, summary, description, priority, labels, assignee) -> dict
    update_issue,   # update_issue(issue_key, summary, description, priority, labels, assignee) -> dict
    add_comment,    # add_comment(issue_key, body, security_level=None) -> dict

    # Transition operations
    get_transitions,  # get_transitions(issue_key: str) -> list[dict]
    do_transition,    # do_transition(issue_key, transition_name, comment=None, security_level=None) -> dict

    # Data classes
    Credentials,
    JiraDefaults,
    ProjectDefaults,

    # Exceptions
    APIError,
    JiraDetectionError,
)
```

### Data Classes

```python { .api }
@dataclass
class Credentials:
    url: str | None = None
    email: str | None = None
    token: str | None = None
    username: str | None = None
    password: str | None = None

    def is_valid(self) -> bool:
        """Returns True if credentials are sufficient for authentication.
        Token-based: requires token + url.
        Basic auth: requires username + password + url.
        """

@dataclass
class JiraDefaults:
    jql_scope: str | None = None
    security_level: str | None = None
    max_results: int | None = None
    fields: list[str] | None = None

    @staticmethod
    def from_config(config: dict) -> JiraDefaults:
        """Load from config dict (reads config['defaults'])."""

@dataclass
class ProjectDefaults:
    issue_type: str | None = None
    priority: str | None = None

    @staticmethod
    def from_config(config: dict, project: str) -> ProjectDefaults:
        """Load from config dict for specific project key."""
```

### Exceptions

```python { .api }
class APIError(Exception):
    """Raised for API request failures."""
    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        ...
    status_code: int | None  # HTTP status code
    response: Any            # Response body text

class JiraDetectionError(Exception):
    """Raised when Jira deployment type detection fails."""
```

### Programmatic Usage Examples

```python
from skills.jira.scripts.jira import search_issues, get_issue, create_issue, add_comment, do_transition, APIError

# Search issues
issues = search_issues("project = DEMO AND status = Open", max_results=10)
for issue in issues:
    print(issue["key"], issue["fields"]["summary"])

# Get full issue details
issue = get_issue("DEMO-123")
status = issue["fields"]["status"]["name"]
assignee = issue["fields"].get("assignee", {})

# Create an issue
new_issue = create_issue(
    project="DEMO",
    issue_type="Task",
    summary="Implement feature X",
    description="Detailed description here",
    priority="High",
    labels=["feature", "sprint-1"],
)
print(f"Created: {new_issue['key']}")

# Add a comment
add_comment("DEMO-123", "Investigation complete, see notes below")

# Private comment
add_comment("DEMO-123", "Internal escalation notes", security_level="Red Hat Internal")

# Transition an issue
do_transition("DEMO-123", "In Progress")
do_transition("DEMO-123", "Done", comment="Merged PR #456")

# Handle errors
try:
    issue = get_issue("INVALID-999")
except APIError as e:
    print(f"Error {e.status_code}: {e}")
```

### HTTP Helpers (Low-Level)

```python
from skills.jira.scripts.jira import get, post, put, delete, api_path

# Make raw API calls
response = get("jira", api_path("search"), params={"jql": "project=DEMO", "maxResults": 5})
issues = response.get("issues", [])

# Create via raw API
new = post("jira", api_path("issue"), {
    "fields": {
        "project": {"key": "DEMO"},
        "issuetype": {"name": "Task"},
        "summary": "My task"
    }
})

# Update
put("jira", api_path("issue/DEMO-123"), {"fields": {"summary": "Updated"}})

# Delete
delete("jira", api_path("issue/DEMO-123"))
```

### Deployment Detection

```python { .api }
def detect_deployment_type(force_refresh: bool = False) -> str:
    """
    Detect Jira deployment type.
    Uses GET /rest/api/2/serverInfo. Cached per URL.

    Args:
        force_refresh: Bypass cache and re-detect.

    Returns:
        "Cloud", "DataCenter", or "Server"

    Raises:
        JiraDetectionError: If detection fails.
    """

def get_api_version() -> str:
    """
    Returns:
        "3" for Cloud, "2" for DataCenter/Server.
    """

def api_path(endpoint: str) -> str:
    """
    Constructs versioned API path.

    Args:
        endpoint: Path without version (e.g., "search", "issue/DEMO-1").

    Returns:
        Full path: "rest/api/3/search" or "rest/api/2/search".
    """

def detect_scriptrunner_support(force_refresh: bool = False) -> dict:
    """
    Returns:
        {
            "available": bool,           # ScriptRunner installed
            "version": str | None,       # Version if detected
            "type": str,                 # "cloud", "datacenter", or "unknown"
            "enhanced_search": bool,     # Enhanced Search JQL available
        }
    """

def validate_jql_for_scriptrunner(jql: str) -> dict:
    """
    Returns:
        {
            "uses_scriptrunner": bool,
            "functions_detected": list[str],
            "supported": bool,
            "warning": str | None,
        }
    """
```
