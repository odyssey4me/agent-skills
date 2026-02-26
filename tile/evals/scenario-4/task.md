# Jira Issue Creator

A utility that creates a new Jira issue in a specified project and returns the key of the newly created issue.

## Capabilities

### Create a New Issue
- Creating an issue with a project key, issue type, and summary returns the key of the newly created issue (e.g. PROJECT-42) [@test](./tests/test_create_minimal.py)
- When a description is provided alongside the required fields, the created issue stores and returns the description in its details [@test](./tests/test_create_with_description.py)
- When a priority value is supplied, the created issue reflects that priority in its fields upon retrieval [@test](./tests/test_create_with_priority.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
