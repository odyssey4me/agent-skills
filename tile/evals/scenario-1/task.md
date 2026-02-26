# Jira Issue Viewer

A utility that retrieves and displays the full details of a specific Jira issue identified by its key.

## Capabilities

### Retrieve Issue by Key
- Fetching an issue by its key returns the issue summary, current status, and assignee name [@test](./tests/test_get_basic_fields.py)
- When an issue has a non-empty description, the description text is included in the retrieved details [@test](./tests/test_get_with_description.py)
- When the issue has comments, at least the most recent comment body is included in the returned output [@test](./tests/test_get_with_comments.py)
- Requesting a key that does not correspond to any issue results in an error message rather than an unhandled exception [@test](./tests/test_invalid_key_error.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
