---
name: google-docs
description: Create and modify Google Docs documents. Read content, insert tables, apply heading styles, and manage formatting. Use when asked to edit a gdoc, write a Google document, update a doc, or format document content.
metadata:
  author: odyssey4me
  version: "0.2.0"
  category: google-workspace
  tags: "documents, editing"
  complexity: standard
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/google-docs.py:*)
---

# Google Docs

Interact with Google Docs for document creation, editing, and content management.

## Installation

**Dependencies**: `pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml`

## Setup Verification

After installation, verify the skill is properly configured:

```bash
$SKILL_DIR/scripts/google-docs.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml)
- Authentication configuration
- Connectivity to Google Docs API

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Docs uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/gcp-project-setup.md) - Create project, enable Docs API
2. [Google OAuth Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md) - Configure credentials

### Quick Start

1. Create `~/.config/agent-skills/google.yaml`:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```

2. Run `$SKILL_DIR/scripts/google-docs.py check` to trigger OAuth flow and verify setup.

On scope or authentication errors, see the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

## Commands

### check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/google-docs.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Google Docs API
- Creates a test document to verify write access

### auth setup

Store OAuth 2.0 client credentials for custom OAuth flow.

```bash
$SKILL_DIR/scripts/google-docs.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

Credentials are saved to `~/.config/agent-skills/google-docs.yaml`.

**Options:**
- `--client-id` - OAuth 2.0 client ID (required)
- `--client-secret` - OAuth 2.0 client secret (required)

### auth reset

Clear stored OAuth token. The next command that needs authentication will trigger re-authentication automatically.

```bash
$SKILL_DIR/scripts/google-docs.py auth reset
```

Use this when you encounter scope or authentication errors.

### auth status

Show current OAuth token information without making API calls.

```bash
$SKILL_DIR/scripts/google-docs.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token presence, token expiry, and client ID.

### documents create

Create a new blank Google Doc.

```bash
$SKILL_DIR/scripts/google-docs.py documents create --title "My Document"
```

**Options:**
- `--title` - Document title (required)

**Example:**
```bash
# Create a new document
$SKILL_DIR/scripts/google-docs.py documents create --title "Project Notes"

# Output:
# ✓ Document created successfully
#   Title: Project Notes
#   Document ID: 1abc...xyz
#   URL: https://docs.google.com/document/d/1abc...xyz/edit
```

### documents get

Get document metadata and structure.

```bash
$SKILL_DIR/scripts/google-docs.py documents get DOCUMENT_ID
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Example:**
```bash
# Get document metadata
$SKILL_DIR/scripts/google-docs.py documents get 1abc...xyz

# Output:
# Title: Project Notes
# Document ID: 1abc...xyz
# Characters: 1234
# Revision ID: abc123
```

### documents read

Read document content as plain text, markdown, or PDF.

```bash
$SKILL_DIR/scripts/google-docs.py documents read DOCUMENT_ID
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--format` - Output format: `markdown` (default, preserves tables and headings) or `pdf`
- `--output`, `-o` - Output file path (used with pdf format)

**Example:**
```bash
# Read as markdown (default, preserves tables and headings)
$SKILL_DIR/scripts/google-docs.py documents read 1abc...xyz

# Export as PDF
$SKILL_DIR/scripts/google-docs.py documents read 1abc...xyz --format pdf --output document.pdf

# Output as markdown:
# # Heading
#
# This is a paragraph.
#
# | Column 1 | Column 2 |
# |----------|----------|
# | Value 1  | Value 2  |
```

**Note:** Markdown and PDF export use Google's native Drive API export. Markdown preserves tables, headings, formatting, and structure with high fidelity. Both require the `drive.readonly` scope.

### content append

Append text to the end of a document.

```bash
$SKILL_DIR/scripts/google-docs.py content append DOCUMENT_ID --text "Additional content"
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--text` - Text to append (required)

**Example:**
```bash
# Append text
$SKILL_DIR/scripts/google-docs.py content append 1abc...xyz --text "Meeting notes from today..."

# Output:
# ✓ Text appended successfully
```

### content insert

Insert text at a specific position in the document.

```bash
$SKILL_DIR/scripts/google-docs.py content insert DOCUMENT_ID --text "Insert this" --index 10
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--text` - Text to insert (required)
- `--index` - Position to insert at, 0-based (required)

**Example:**
```bash
# Insert text at the beginning (index 1, after title)
$SKILL_DIR/scripts/google-docs.py content insert 1abc...xyz --text "Introduction\n\n" --index 1

# Output:
# ✓ Text inserted successfully
```

**Note:** Index 0 is before the document content. Index 1 is at the beginning of content.

### content delete

Delete a range of content from the document.

```bash
$SKILL_DIR/scripts/google-docs.py content delete DOCUMENT_ID --start-index 10 --end-index 50
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--start-index` - Start position, inclusive (required)
- `--end-index` - End position, exclusive (required)

**Example:**
```bash
# Delete characters 10-50
$SKILL_DIR/scripts/google-docs.py content delete 1abc...xyz --start-index 10 --end-index 50

# Output:
# ✓ Content deleted successfully
```

**Warning:** Be careful with indices. Deleting the wrong range can corrupt document structure.

### content insert-after-anchor

Insert markdown-formatted content after a structural anchor (horizontal rule, heading, or bookmark) in a document. Handles text insertion, heading styles, bullet lists, bold formatting, and links in a single operation.

```bash
$SKILL_DIR/scripts/google-docs.py content insert-after-anchor DOCUMENT_ID \
  --anchor-type ANCHOR_TYPE --markdown "MARKDOWN_CONTENT"
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--anchor-type` - Type of anchor to find: `horizontal_rule`, `heading`, or `bookmark` (required)
- `--anchor-value` - Anchor-specific value: heading text (for `heading`), bookmark ID (for `bookmark`), or occurrence number (for `horizontal_rule`, default 1)
- `--markdown` - Markdown-formatted content to insert (required). Use `\n` for newlines.

**Supported markdown:**

| Syntax | Result |
|--------|--------|
| `## Heading` | Heading (levels 1-6) |
| `**text**` | Bold text |
| `[text](url)` | Hyperlink |
| `- item` | Bullet list |
| `  - item` | Nested bullet (indent 2 spaces per level) |

**Examples:**
```bash
# Insert after the first horizontal rule
$SKILL_DIR/scripts/google-docs.py content insert-after-anchor 1abc...xyz \
  --anchor-type horizontal_rule \
  --markdown '## Status Update\n\n**Summary:**\n- Task completed\n  - Sub-task done\n- [Details](https://example.com)'

# Insert after a specific heading
$SKILL_DIR/scripts/google-docs.py content insert-after-anchor 1abc...xyz \
  --anchor-type heading \
  --anchor-value "Notes" \
  --markdown '- New note item\n- Another item'

# Insert after the second horizontal rule
$SKILL_DIR/scripts/google-docs.py content insert-after-anchor 1abc...xyz \
  --anchor-type horizontal_rule \
  --anchor-value 2 \
  --markdown '## New Section\n\nParagraph text here.'
```

### formatting apply

Apply text formatting to a range of text.

```bash
$SKILL_DIR/scripts/google-docs.py formatting apply DOCUMENT_ID \
  --start-index 1 --end-index 20 --bold --italic
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--start-index` - Start position, inclusive (required)
- `--end-index` - End position, exclusive (required)
- `--bold` - Apply bold formatting
- `--italic` - Apply italic formatting
- `--underline` - Apply underline formatting
- `--font-size SIZE` - Set font size in points

**Example:**
```bash
# Make title bold and larger
$SKILL_DIR/scripts/google-docs.py formatting apply 1abc...xyz \
  --start-index 1 --end-index 20 --bold --font-size 18

# Apply italic to a section
$SKILL_DIR/scripts/google-docs.py formatting apply 1abc...xyz \
  --start-index 50 --end-index 100 --italic

# Output:
# ✓ Formatting applied successfully
```

## Examples

### Create and populate a document

```bash
# Create a new document
$SKILL_DIR/scripts/google-docs.py documents create --title "Weekly Report"

# Add content
$SKILL_DIR/scripts/google-docs.py content append $DOC_ID --text "Weekly Report\n\n"
$SKILL_DIR/scripts/google-docs.py content append $DOC_ID --text "Summary: This week's accomplishments...\n"

# Format the title
$SKILL_DIR/scripts/google-docs.py formatting apply $DOC_ID --start-index 1 --end-index 14 --bold --font-size 18

# Read it back
$SKILL_DIR/scripts/google-docs.py documents read $DOC_ID
```

### Read and extract content

```bash
# Get document info
$SKILL_DIR/scripts/google-docs.py documents get 1abc...xyz

# Extract plain text
$SKILL_DIR/scripts/google-docs.py documents read 1abc...xyz > document.txt

# Get document structure
$SKILL_DIR/scripts/google-docs.py documents get 1abc...xyz
```

### Insert formatted content after an anchor

```bash
# Insert a formatted status update after a horizontal rule
$SKILL_DIR/scripts/google-docs.py content insert-after-anchor $DOC_ID \
  --anchor-type horizontal_rule \
  --markdown '## Weekly Update\n\n**Completed:**\n- Feature implementation\n  - Backend API\n  - Frontend UI\n- [Project board](https://example.com/board)'
```

### Edit existing content

```bash
# Insert a new section
$SKILL_DIR/scripts/google-docs.py content insert 1abc...xyz \
  --text "\n\nNew Section\n" --index 100

# Format the new section header
$SKILL_DIR/scripts/google-docs.py formatting apply 1abc...xyz \
  --start-index 102 --end-index 113 --bold

# Append more content
$SKILL_DIR/scripts/google-docs.py content append 1abc...xyz \
  --text "Additional details about the new section..."
```

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails with an authentication error, insufficient scope error, or permission denied error (exit code 1), **stop and inform the user**. Do not retry or attempt to fix the issue autonomously — these errors require user interaction (browser-based OAuth consent). Point the user to the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors (HTTP 5xx) may succeed on retry after a brief wait. All other errors should be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Cannot find document

Make sure you're using the correct document ID from the URL:
- URL: `https://docs.google.com/document/d/1abc...xyz/edit`
- Document ID: `1abc...xyz`

### Index errors when inserting/deleting

Use `documents get` to see the document structure and valid index ranges. Remember:
- Index 0 is before any content
- Index 1 is at the start of document body
- The last index is the document length


## API Reference

For advanced usage, see:
- [Google Docs API Documentation](https://developers.google.com/docs/api)
- [Document structure](https://developers.google.com/docs/api/how-tos/documents)
- [Formatting reference](references/formatting-guide.md)
