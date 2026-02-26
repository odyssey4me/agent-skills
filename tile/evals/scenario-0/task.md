# Jira Configuration Inspector

A utility that reads and displays the active Jira skill configuration, including the server connection details and any user-defined defaults.

## Capabilities

### Display Active Configuration
- Running the configuration display outputs the Jira server URL and the email address of the authenticated user [@test](./tests/test_show_base_config.py)
- When a default JQL scope is stored in the configuration, it is printed as part of the configuration output [@test](./tests/test_jql_scope_shown.py)
- When project-specific defaults are configured, each project key is listed alongside its stored default issue type and priority values [@test](./tests/test_project_defaults_shown.py)
- When no project-specific defaults exist, the output includes a message indicating that no project defaults are configured [@test](./tests/test_no_project_defaults.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
