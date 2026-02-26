# Jira Issue Search

A utility that searches for Jira issues using JQL (Jira Query Language) and displays a formatted list of matching results.

## Capabilities

### Search Issues with JQL
- Providing a valid JQL query returns a list of matching issues where each entry shows the issue key, summary, and current status [@test](./tests/test_basic_jql_search.py)
- Specifying a maximum result count limits the returned list to at most that number of issues [@test](./tests/test_max_results_limit.py)
- When the query string is empty or absent, any configured default JQL scope is applied and its matching issues are returned [@test](./tests/test_default_scope_fallback.py)
- A JQL query that matches no issues returns an empty result set with a message indicating no issues were found [@test](./tests/test_no_matching_issues.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
