---
name: google-docs
description: Create and modify Google Docs documents. Read document content and structure, manage formatting, paragraphs, and styles. Use when working with Google Docs document management.
metadata:
  author: odyssey4me
  version: "0.1.0"
  category: google-workspace
  tags: [documents, editing]
  complexity: standard
license: MIT
allowed-tools: Bash(python $SKILL_DIR/scripts/google-docs.py *)
---

# Google Docs

Interact with Google Docs for document creation, editing, and content management.

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
   ```

2. **Download the skill** from [Releases](https://github.com/odyssey4me/agent-skills/releases) or use directly from this repository.

## Setup Verification

After installation, verify the skill is properly configured:

```bash
python $SKILL_DIR/scripts/google-docs.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml)
- Authentication configuration
- Connectivity to Google Docs API

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Docs uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](../../docs/gcp-project-setup.md) - Create project, enable Docs API
2. [Google OAuth Setup Guide](../../docs/google-oauth-setup.md) - Configure credentials

### Quick Start

1. Create `~/.config/agent-skills/google.yaml`:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```

2. Run `python $SKILL_DIR/scripts/google-docs.py check` to trigger OAuth flow and verify setup.

### OAuth Scopes

The skill requests granular scopes for different operations:

| Scope | Permission | Used For |
|-------|-----------|----------|
| `documents.readonly` | Read documents | Reading document content and metadata |
| `documents` | Full access | Creating and modifying documents |
| `drive.readonly` | Read Drive files | Exporting documents as markdown or PDF |

### Scope Errors

If you encounter "insufficient scope" errors, reset your token and re-authenticate:

1. Reset token: `python $SKILL_DIR/scripts/google-docs.py auth reset`
2. Re-run: `python $SKILL_DIR/scripts/google-docs.py check`

## Commands

### check

Verify configuration and connectivity.

```bash
python $SKILL_DIR/scripts/google-docs.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Google Docs API
- Creates a test document to verify write access

### auth setup

Store OAuth 2.0 client credentials for custom OAuth flow.

```bash
python $SKILL_DIR/scripts/google-docs.py auth setup \
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
python $SKILL_DIR/scripts/google-docs.py auth reset
```

Use this when you encounter scope or authentication errors.

### auth status

Show current OAuth token information without making API calls.

```bash
python $SKILL_DIR/scripts/google-docs.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token presence, token expiry, and client ID.

### documents create

Create a new blank Google Doc.

```bash
python $SKILL_DIR/scripts/google-docs.py documents create --title "My Document"
```

**Options:**
- `--title` - Document title (required)

**Example:**
```bash
# Create a new document
python $SKILL_DIR/scripts/google-docs.py documents create --title "Project Notes"

# Output:
# ✓ Document created successfully
#   Title: Project Notes
#   Document ID: 1abc...xyz
#   URL: https://docs.google.com/document/d/1abc...xyz/edit
```

### documents get

Get document metadata and structure.

```bash
python $SKILL_DIR/scripts/google-docs.py documents get DOCUMENT_ID
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Example:**
```bash
# Get document metadata
python $SKILL_DIR/scripts/google-docs.py documents get 1abc...xyz

# Output:
# Title: Project Notes
# Document ID: 1abc...xyz
# Characters: 1234
# Revision ID: abc123
```

### documents read

Read document content as plain text, markdown, or PDF.

```bash
python $SKILL_DIR/scripts/google-docs.py documents read DOCUMENT_ID
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--format` - Output format: `markdown` (default, preserves tables and headings) or `pdf`
- `--output`, `-o` - Output file path (used with pdf format)

**Example:**
```bash
# Read as markdown (default, preserves tables and headings)
python $SKILL_DIR/scripts/google-docs.py documents read 1abc...xyz

# Export as PDF
python $SKILL_DIR/scripts/google-docs.py documents read 1abc...xyz --format pdf --output document.pdf

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
python $SKILL_DIR/scripts/google-docs.py content append DOCUMENT_ID --text "Additional content"
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--text` - Text to append (required)

**Example:**
```bash
# Append text
python $SKILL_DIR/scripts/google-docs.py content append 1abc...xyz --text "Meeting notes from today..."

# Output:
# ✓ Text appended successfully
```

### content insert

Insert text at a specific position in the document.

```bash
python $SKILL_DIR/scripts/google-docs.py content insert DOCUMENT_ID --text "Insert this" --index 10
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--text` - Text to insert (required)
- `--index` - Position to insert at, 0-based (required)

**Example:**
```bash
# Insert text at the beginning (index 1, after title)
python $SKILL_DIR/scripts/google-docs.py content insert 1abc...xyz --text "Introduction\n\n" --index 1

# Output:
# ✓ Text inserted successfully
```

**Note:** Index 0 is before the document content. Index 1 is at the beginning of content.

### content delete

Delete a range of content from the document.

```bash
python $SKILL_DIR/scripts/google-docs.py content delete DOCUMENT_ID --start-index 10 --end-index 50
```

**Arguments:**
- `document_id` - The Google Docs document ID

**Options:**
- `--start-index` - Start position, inclusive (required)
- `--end-index` - End position, exclusive (required)

**Example:**
```bash
# Delete characters 10-50
python $SKILL_DIR/scripts/google-docs.py content delete 1abc...xyz --start-index 10 --end-index 50

# Output:
# ✓ Content deleted successfully
```

**Warning:** Be careful with indices. Deleting the wrong range can corrupt document structure.

### content insert-after-anchor

Insert markdown-formatted content after a structural anchor (horizontal rule, heading, or bookmark) in a document. Handles text insertion, heading styles, bullet lists, bold formatting, and links in a single operation.

```bash
python $SKILL_DIR/scripts/google-docs.py content insert-after-anchor DOCUMENT_ID \
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
python $SKILL_DIR/scripts/google-docs.py content insert-after-anchor 1abc...xyz \
  --anchor-type horizontal_rule \
  --markdown '## Status Update\n\n**Summary:**\n- Task completed\n  - Sub-task done\n- [Details](https://example.com)'

# Insert after a specific heading
python $SKILL_DIR/scripts/google-docs.py content insert-after-anchor 1abc...xyz \
  --anchor-type heading \
  --anchor-value "Notes" \
  --markdown '- New note item\n- Another item'

# Insert after the second horizontal rule
python $SKILL_DIR/scripts/google-docs.py content insert-after-anchor 1abc...xyz \
  --anchor-type horizontal_rule \
  --anchor-value 2 \
  --markdown '## New Section\n\nParagraph text here.'
```

### formatting apply

Apply text formatting to a range of text.

```bash
python $SKILL_DIR/scripts/google-docs.py formatting apply DOCUMENT_ID \
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
python $SKILL_DIR/scripts/google-docs.py formatting apply 1abc...xyz \
  --start-index 1 --end-index 20 --bold --font-size 18

# Apply italic to a section
python $SKILL_DIR/scripts/google-docs.py formatting apply 1abc...xyz \
  --start-index 50 --end-index 100 --italic

# Output:
# ✓ Formatting applied successfully
```

## Examples

### Create and populate a document

```bash
# Create a new document
python $SKILL_DIR/scripts/google-docs.py documents create --title "Weekly Report"

# Add content
python $SKILL_DIR/scripts/google-docs.py content append $DOC_ID --text "Weekly Report\n\n"
python $SKILL_DIR/scripts/google-docs.py content append $DOC_ID --text "Summary: This week's accomplishments...\n"

# Format the title
python $SKILL_DIR/scripts/google-docs.py formatting apply $DOC_ID --start-index 1 --end-index 14 --bold --font-size 18

# Read it back
python $SKILL_DIR/scripts/google-docs.py documents read $DOC_ID
```

### Read and extract content

```bash
# Get document info
python $SKILL_DIR/scripts/google-docs.py documents get 1abc...xyz

# Extract plain text
python $SKILL_DIR/scripts/google-docs.py documents read 1abc...xyz > document.txt

# Get document structure
python $SKILL_DIR/scripts/google-docs.py documents get 1abc...xyz
```

### Insert formatted content after an anchor

```bash
# Insert a formatted status update after a horizontal rule
python $SKILL_DIR/scripts/google-docs.py content insert-after-anchor $DOC_ID \
  --anchor-type horizontal_rule \
  --markdown '## Weekly Update\n\n**Completed:**\n- Feature implementation\n  - Backend API\n  - Frontend UI\n- [Project board](https://example.com/board)'
```

### Edit existing content

```bash
# Insert a new section
python $SKILL_DIR/scripts/google-docs.py content insert 1abc...xyz \
  --text "\n\nNew Section\n" --index 100

# Format the new section header
python $SKILL_DIR/scripts/google-docs.py formatting apply 1abc...xyz \
  --start-index 102 --end-index 113 --bold

# Append more content
python $SKILL_DIR/scripts/google-docs.py content append 1abc...xyz \
  --text "Additional details about the new section..."
```

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails with an authentication error, insufficient scope error, or permission denied error (exit code 1), do NOT retry the same command. Instead:

1. Inform the user about the error
2. Run `python $SKILL_DIR/scripts/google-docs.py auth status` to check the current token state
3. Suggest the user run `python $SKILL_DIR/scripts/google-docs.py auth reset` followed by `python $SKILL_DIR/scripts/google-docs.py check` to re-authenticate
4. The `auth reset` and `check` commands require user interaction (browser-based OAuth consent) and cannot be completed autonomously

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors (HTTP 5xx) may succeed on retry after a brief wait. All other errors should be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Authentication failed

1. Verify your OAuth client ID and client secret are correct in `~/.config/agent-skills/google-docs.yaml`
2. Token expired or corrupted — reset and re-authenticate:
   ```bash
   python $SKILL_DIR/scripts/google-docs.py auth reset
   python $SKILL_DIR/scripts/google-docs.py check
   ```

### Permission denied

Your OAuth token may not have the necessary scopes. Reset your token and re-authenticate:

```bash
python $SKILL_DIR/scripts/google-docs.py auth reset
python $SKILL_DIR/scripts/google-docs.py check
```

### Cannot find document

Make sure you're using the correct document ID from the URL:
- URL: `https://docs.google.com/document/d/1abc...xyz/edit`
- Document ID: `1abc...xyz`

### Index errors when inserting/deleting

Use `documents get` to see the document structure and valid index ranges. Remember:
- Index 0 is before any content
- Index 1 is at the start of document body
- The last index is the document length

### Dependencies not found

Install required dependencies:

```bash
pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
```

### OAuth flow fails

Ensure your GCP project has:
1. Google Docs API enabled (`docs.googleapis.com`)
2. OAuth 2.0 credentials created
3. OAuth consent screen configured
4. Your email added as a test user (if app is in testing mode)

See [docs/gcp-project-setup.md](../../docs/gcp-project-setup.md) for detailed instructions.

## Related Skills

- [Google Drive](../google-drive/SKILL.md) - File management (Drive manages file metadata, Docs manages content)
- [Google Sheets](../google-sheets/SKILL.md) - Spreadsheet management
- [Google Slides](../google-slides/SKILL.md) - Presentation management

## API Reference

For advanced usage, see:
- [Google Docs API Documentation](https://developers.google.com/docs/api)
- [Document structure](https://developers.google.com/docs/api/how-tos/documents)
- [Formatting reference](references/formatting-guide.md)
