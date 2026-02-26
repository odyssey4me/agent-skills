# Jira Comment Publisher

A utility that adds a new, publicly visible comment to an existing Jira issue.

## Capabilities

### Add a Public Comment to an Issue
- Submitting a comment text for a valid issue key posts the comment and returns a confirmation containing the new comment's identifier [@test](./tests/test_add_comment_success.py)
- A comment added via this utility can subsequently be found in the issue's comment list when the issue is retrieved [@test](./tests/test_comment_visible_on_issue.py)
- Attempting to comment on a key that does not exist produces an informative error message without raising an unhandled exception [@test](./tests/test_comment_invalid_key.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
