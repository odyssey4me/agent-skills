# Confluence Markdown Page Publisher

A utility that creates a new Confluence page in a specified space from Markdown source content, with support for placing the new page under a designated parent page.

## Capabilities

### Create a Page from Markdown
- Creating a page with a title and Markdown body in a given space key returns the URL or ID of the newly created page [@test](./tests/test_create_page_basic.py)
- Markdown formatting in the body including headings, bullet lists, and fenced code blocks is preserved and rendered correctly in the created Confluence page [@test](./tests/test_markdown_elements_preserved.py)
- When a parent page identifier is specified, the new page is created as a child of that parent in the space hierarchy [@test](./tests/test_page_created_under_parent.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
