# Configuration

Configure defaults in `~/.config/agent-skills/jira.yaml` to reduce repetitive typing.

## Full Config Example

```yaml
# Authentication (optional if using environment variables)
url: https://yourcompany.atlassian.net
email: you@example.com
token: your-token

# Optional defaults
defaults:
  jql_scope: "project = DEMO AND assignee = currentUser()"
  security_level: "Internal"
  max_results: 25
  fields: ["summary", "status", "resolution", "assignee", "priority", "created", "updated"]
  custom_fields:
    story_points: "customfield_10028"
    assigned_team: "customfield_12345"
  custom_field_schemas:
    story_points: "number"
    assigned_team: "option"

# Optional project-specific defaults
projects:
  DEMO:
    issue_type: "Task"
    priority: "Medium"
  PROD:
    issue_type: "Bug"
    priority: "High"
```

## How Defaults Work

- **CLI arguments always override** config defaults
- **JQL scope** is prepended to all searches: `(scope) AND (your_query)`
- **Security level** applies to comments and transitions with comments
- **Project defaults** apply when creating issues in that project
- **Custom fields** map friendly names to instance-specific custom field IDs.
  These fields are automatically included in API requests and displayed in
  formatted output. If a mapping is not configured, the skill auto-discovers
  the field ID and schema type from the Jira API and saves both to the config.
  Use `--set-field NAME=VALUE` on `issue create` and `issue update` to set
  custom field values using the friendly name.
- **Custom field schemas** store the Jira schema type for each custom field
  (e.g. `number`, `option`, `securitylevel`). This lets `--set-field` format
  values with the appropriate structure (e.g. `{"value": "..."}` for options) without extra API
  calls. Schemas are saved automatically during discovery. If missing, run
  `config discover <field_name>` to populate them.
