# Confluence Content Search

A utility that searches Confluence content using CQL (Confluence Query Language) and displays a list of matching results with their titles and spaces.

## Capabilities

### Search Content with CQL
- Providing a valid CQL query returns matching content items each showing the page title, space key, and a text excerpt [@test](./tests/test_basic_cql_search.py)
- Filtering the search by content type (such as page or blogpost) returns only items of that type [@test](./tests/test_type_filter.py)
- Filtering the search by space key limits results to content residing in that space [@test](./tests/test_space_filter.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
