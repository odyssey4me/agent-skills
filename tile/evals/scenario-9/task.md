# Atlassian Content Format Converter

A utility that converts Markdown text to the appropriate Atlassian content format for the target deployment type: Atlassian Document Format (ADF) JSON for Cloud instances, or XHTML storage format for Data Center and Server instances.

## Capabilities

### Convert Markdown to Atlassian Format
- Converting a Markdown document with headers and paragraphs for a Cloud deployment produces a valid ADF JSON object with the expected node types [@test](./tests/test_markdown_to_adf_structure.py)
- Converting the same Markdown document for a Data Center or Server deployment produces an XHTML storage format string containing the equivalent HTML elements [@test](./tests/test_markdown_to_storage_output.py)
- Inline Markdown elements including bold text, italic text, and inline code are faithfully represented in both output formats [@test](./tests/test_inline_elements_converted.py)
- A fenced code block with a language specifier in Markdown is converted to the structured code representation in the target format, preserving the language annotation [@test](./tests/test_code_block_with_language.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
