# Google Docs Formatting Guide

This guide covers text formatting options available in the Google Docs skill.

## Text Style Properties

### Basic Formatting

The `formatting apply` command supports these basic text properties:

| Property | Flag | Values | Description |
|----------|------|--------|-------------|
| Bold | `--bold` | true/false (flag) | Makes text bold |
| Italic | `--italic` | true/false (flag) | Makes text italic |
| Underline | `--underline` | true/false (flag) | Underlines text |
| Font Size | `--font-size N` | Number (points) | Sets font size |

### Usage Examples

```bash
# Make text bold
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 1 --end-index 20 --bold

# Make text italic
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 50 --end-index 100 --italic

# Combine multiple formats
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 1 --end-index 50 --bold --italic --underline

# Change font size
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 1 --end-index 20 --font-size 18

# Create a heading (bold + larger font)
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 1 --end-index 15 --bold --font-size 16
```

## Understanding Indices

Google Docs uses character-based indices for positioning:

```
Index: 0    1    2    3    4    5    6    7    8    9
Text:     H    e    l    l    o         W    o    r    l    d
```

### Key Points

1. **Index 0** - Before any content
2. **Index 1** - Start of document body (after title)
3. **End index is exclusive** - Range `[1, 5)` includes characters at indices 1, 2, 3, 4 but not 5
4. **Newlines count as characters** - `\n` takes one index position

### Finding Indices

To see document structure and indices, use:

```bash
python scripts/google-docs.py documents get DOC_ID --json
```

This shows the full document structure including:
- Start and end indices for each element
- Paragraph boundaries
- Text runs with their content

## Formatting Patterns

### Document Titles

```bash
# Format as a title (bold, size 18)
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 1 --end-index 20 --bold --font-size 18
```

### Section Headers

```bash
# Format as a heading (bold, size 14)
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 50 --end-index 70 --bold --font-size 14
```

### Emphasis

```bash
# Emphasize with italic
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 100 --end-index 150 --italic

# Strong emphasis with bold
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 200 --end-index 250 --bold
```

### Body Text

```bash
# Standard body text (typically 11pt)
python scripts/google-docs.py formatting apply DOC_ID \
  --start-index 300 --end-index 500 --font-size 11
```

## Common Font Sizes

| Size (pt) | Typical Use |
|-----------|-------------|
| 18-24 | Main document title |
| 14-16 | Section headers (H1) |
| 12-13 | Subsection headers (H2) |
| 11 | Body text (default) |
| 10 | Small text, footnotes |
| 8-9 | Very small text, captions |

## Advanced Formatting Workflow

### Creating a Structured Document

```bash
#!/bin/bash
DOC_ID="your-document-id"

# Add content with proper structure
python scripts/google-docs.py content append $DOC_ID --text "Project Report\n\n"
python scripts/google-docs.py content append $DOC_ID --text "Executive Summary\n\n"
python scripts/google-docs.py content append $DOC_ID --text "This report covers...\n\n"
python scripts/google-docs.py content append $DOC_ID --text "Introduction\n\n"
python scripts/google-docs.py content append $DOC_ID --text "Background information...\n\n"

# Format title (assuming it starts at index 1)
python scripts/google-docs.py formatting apply $DOC_ID \
  --start-index 1 --end-index 15 --bold --font-size 18

# Format first section header
python scripts/google-docs.py formatting apply $DOC_ID \
  --start-index 17 --end-index 34 --bold --font-size 14

# Format second section header
python scripts/google-docs.py formatting apply $DOC_ID \
  --start-index 60 --end-index 73 --bold --font-size 14
```

### Highlighting Important Text

```bash
# Bold + larger for emphasis
python scripts/google-docs.py formatting apply $DOC_ID \
  --start-index 100 --end-index 120 --bold --font-size 12

# Italic for quotes
python scripts/google-docs.py formatting apply $DOC_ID \
  --start-index 200 --end-index 300 --italic
```

## Limitations and Notes

### Current Limitations

The Google Docs skill currently supports basic text formatting. The following are **not yet supported**:

- Font family/typeface changes
- Text color
- Background/highlight color
- Alignment (left, center, right, justify)
- Lists (bullet points, numbered lists)
- Links (hyperlinks)
- Images
- Tables
- Headers and footers
- Page breaks

These features can be added to the skill in future versions or accessed through the Google Docs web interface.

### Best Practices

1. **Test indices first** - Use `documents get --json` to verify index positions before formatting
2. **Format after content** - Add all content first, then apply formatting
3. **Use descriptive sizes** - Maintain clear hierarchy with font sizes
4. **Be consistent** - Use the same formatting for similar elements
5. **Avoid overlapping ranges** - Apply formatting to non-overlapping ranges when possible

### Batch Formatting

For complex documents with many formatting operations, consider:

1. Creating a script that applies all formatting at once
2. Using the `--json` output to verify each operation
3. Working with larger ranges when possible to minimize API calls

## Troubleshooting

### "Invalid index" errors

- Verify the document length with `documents get`
- Ensure start_index < end_index
- Remember that end_index is exclusive
- Check that indices are within document bounds

### Formatting not visible

- Ensure you're using the write scope (`documents`, not `documents.readonly`)
- Check that the format operation succeeded (look for success message)
- Verify you're looking at the correct document
- Try refreshing the Google Docs page in your browser

### Unexpected formatting results

- Double-check your index calculations
- Use `documents get --json` to see the exact structure
- Remember that newlines and spaces count as characters
- Verify that flags are being interpreted correctly (`--bold` vs `--bold=false`)

## API Reference

For complete details on text formatting capabilities:
- [Google Docs API - TextStyle](https://developers.google.com/docs/api/reference/rest/v1/documents#TextStyle)
- [Batch update requests](https://developers.google.com/docs/api/how-tos/batch-update)
- [Document structure](https://developers.google.com/docs/api/how-tos/documents)
