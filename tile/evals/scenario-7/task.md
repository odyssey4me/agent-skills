# Jira Restricted Comment Publisher

A utility that adds a comment to a Jira issue with configurable visibility, making the comment visible only to members of a named security level or role when one is specified.

## Capabilities

### Post a Comment with Visibility Restriction
- Adding a comment while specifying a security level name posts the comment such that it is restricted to members of that security level [@test](./tests/test_restricted_comment_posted.py)
- A comment posted with a security level restriction is not visible to users outside that security level group [@test](./tests/test_restricted_comment_not_visible.py)
- When no security level is specified, the comment is posted as a standard public comment visible to all users with access to the issue [@test](./tests/test_public_comment_default.py)
- Specifying a security level name that does not exist in the Jira instance produces an error message describing the failure [@test](./tests/test_invalid_security_level.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
