---
name: google
description: >-
  Google Workspace CLI for Gmail, Calendar, Drive, Docs, Sheets, and Slides
  using gogcli. Use when asked to search email, schedule meetings, manage
  files, edit documents, update spreadsheets, or create presentations.
metadata:
  author: odyssey4me
  version: "1.1.0"
  category: productivity
  tags: "gmail, calendar, drive, docs, sheets, slides"
  complexity: lightweight
license: MIT
allowed-tools: Bash(gog:*)
---

# Google Workspace Skill

This skill provides Google Workspace integration using the `gog` CLI ([gogcli](https://github.com/openclaw/gogcli)). The agent calls `gog` directly for all operations.

## Prerequisites

Install the `gog` binary:

```bash
# Homebrew
brew install openclaw/tap/gogcli

# Manual (Linux amd64)
curl -sL https://github.com/openclaw/gogcli/releases/latest/download/gogcli_VERSION_linux_amd64.tar.gz | tar xz
mv gog ~/.local/bin/
```

See [configuration.md](references/configuration.md) for container and MCP server alternatives.

## Authentication

```bash
# Import credentials.json from Google Cloud Console
gog auth credentials set /path/to/credentials.json

# Authorize with only the services you need (opens browser)
gog auth add your@email.com --services gmail,calendar,drive,docs,sheets,slides

# Verify
gog auth doctor
```

### Migrating from legacy Python OAuth

If you previously used the Python-based Google skills, clean up the old tokens and config:

```bash
$SKILL_DIR/scripts/google.py cleanup
```

Then set up fresh authentication with gog as described above.

## Quick Reference

```bash
gog gmail search "is:unread"                    # Search email
gog calendar events --today                     # Today's events
gog drive search "quarterly report"             # Search files
gog docs cat <docId>                            # Read a document
gog sheets get <spreadsheetId> "Sheet1!A1:D10"  # Read spreadsheet range
gog slides info <presentationId>                # Presentation metadata
```

All commands support `--json` for structured output and `--plain` for TSV.

## Commands

### Check Setup

```bash
$SKILL_DIR/scripts/google.py check
```

### Gmail

```bash
# Search
gog gmail search "from:boss@example.com newer_than:7d"
gog gmail search "is:unread label:inbox" --max 20

# Read
gog gmail get <messageId>
gog gmail thread get <threadId>
gog gmail labels list

# Organize
gog gmail mark-read <messageId>
gog gmail unread <messageId>
gog gmail archive <messageId>
gog gmail trash <messageId>

# Send
gog gmail send --to "user@example.com" --subject "Hello" --body "Message body"
gog gmail reply <messageId> --body "Reply text"
gog gmail forward <messageId> --to "other@example.com"

# Drafts
gog gmail drafts list
gog gmail drafts create --to "user@example.com" --subject "Draft" --body "Content"
gog gmail drafts send <draftId>
```

See [gmail.md](references/gmail.md) for the full command reference.

### Google Calendar

```bash
# View
gog calendar calendars
gog calendar events --today
gog calendar events --from "2026-06-25" --to "2026-06-30"
gog calendar event <calendarId> <eventId>
gog calendar freebusy --from "2026-06-25T09:00:00Z" --to "2026-06-25T17:00:00Z"
gog calendar search "standup"

# Create
gog calendar create primary --summary "Meeting" --from "2026-06-25T10:00:00" --to "2026-06-25T11:00:00"

# Manage
gog calendar update <calendarId> <eventId> --summary "Updated title"
gog calendar delete <calendarId> <eventId>
gog calendar respond <calendarId> <eventId> --status accepted
```

See [calendar.md](references/calendar.md) for the full command reference.

### Google Drive

```bash
# Browse
gog drive ls
gog drive ls --folder <folderId>
gog drive search "quarterly report"
gog drive tree
gog drive get <fileId>

# File operations
gog drive upload report.pdf --parent <folderId>
gog drive download <fileId>
gog drive copy <fileId> "Copy of Report"
gog drive move <fileId> --parent <newFolderId>
gog drive rename <fileId> "New Name"
gog drive delete <fileId>

# Sharing
gog drive share <fileId> --email "user@example.com" --role writer
gog drive permissions <fileId>
gog drive unshare <fileId> <permissionId>
```

See [drive.md](references/drive.md) for the full command reference.

### Google Docs

```bash
# Read
gog docs info <docId>
gog docs cat <docId>
gog docs export <docId> --format md
gog docs structure <docId>

# Write
gog docs create "New Document"
gog docs write <docId> --body "Content to append"
gog docs insert <docId> "Text to insert" --at 1
gog docs find-replace <docId> "old text" "new text"
gog docs format <docId> --bold --start 1 --end 10

# Tables
gog docs insert-table <docId> --rows 3 --cols 4
gog docs cell-update <docId> --row 1 --col 1 --body "Header"
```

See [docs.md](references/docs.md) for the full command reference.

#### Docs Workflows

For importing markdown with formatting, table styling, and round-trip editing, see [docs-workflows.md](references/docs-workflows.md).

```bash
# Import markdown as a new document with standard formatting
gog docs create "Document Title" --file document.md --pageless

# Update an existing document from markdown with formatting
gog docs write <docId> --file document.md --markdown --replace \
  --pageless --line-spacing 115 --space-below 8pt
```

### Google Sheets

```bash
# Read
gog sheets metadata <spreadsheetId>
gog sheets get <spreadsheetId> "Sheet1!A1:D10"
gog sheets get <spreadsheetId> "Sheet1!A:A" --format FORMULA

# Write
gog sheets create "New Spreadsheet"
gog sheets update <spreadsheetId> "Sheet1!A1" "value1" "value2" "value3"
gog sheets append <spreadsheetId> "Sheet1!A:D" "val1" "val2" "val3" "val4"
gog sheets clear <spreadsheetId> "Sheet1!A1:D10"

# Structure
gog sheets add-tab <spreadsheetId> "New Tab"
gog sheets delete-tab <spreadsheetId> "Old Tab"
gog sheets rename-tab <spreadsheetId> "Old Name" "New Name"
```

See [sheets.md](references/sheets.md) for the full command reference.

### Google Slides

```bash
# Read
gog slides info <presentationId>
gog slides list-slides <presentationId>
gog slides read-slide <presentationId> <slideId>
gog slides export <presentationId> --format pptx

# Create
gog slides create "New Presentation"
gog slides create-from-markdown "Deck Title" --file slides.md
gog slides create-from-template <templateId> "From Template" --replacements '{"{{NAME}}":"Value"}'

# Edit
gog slides new-slide <presentationId>
gog slides insert-text <presentationId> <objectId> "Text content"
gog slides replace-text <presentationId> "find" "replace"
gog slides insert-image <presentationId> <slideId> image.png --width 300
```

See [slides.md](references/slides.md) for the full command reference.

## Examples

### Search and summarize recent emails
```bash
gog gmail search "is:unread newer_than:7d" --json --results-only | jq '.[] | "\(.from): \(.subject)"'
```

### Create a calendar event for tomorrow
```bash
TOMORROW=$(date -d '+1 day' '+%Y-%m-%dT09:00:00')
gog calendar create primary --summary "Team Standup" --from "$TOMORROW" --to "${TOMORROW%T*}T09:30:00"
```

### Download recent documents
```bash
gog drive search "type:document newer_than:7d" --json --results-only | jq -r '.[] | .id' | \
  while read docId; do gog docs export "$docId" --format md > "doc_$docId.md"; done
```

### Check availability for a meeting
```bash
gog calendar freebusy --from "2026-06-25T09:00:00Z" --to "2026-06-25T17:00:00Z"
```

## Output Formatting

```bash
# JSON output (structured, for scripting)
gog gmail search "is:unread" --json --results-only

# Plain/TSV output (stable, parseable)
gog drive ls --plain

# Select specific fields
gog gmail search "is:unread" --json --select "id,subject,from"
```

## Agent Safety

```bash
# Read-only mode (blocks all mutations)
gog --readonly gmail search "test"

# Block Gmail send specifically
gog --gmail-no-send gmail search "test"

# Preview actions without executing
gog --dry-run drive delete <fileId>

# Disable interactive prompts (fail instead)
gog --no-input calendar create primary --summary "Test"
```

## Error Handling

| Exit Code | Meaning | Retryable |
|-----------|---------|-----------|
| 0 | Success | - |
| 3 | Empty results | No (normal) |
| 4 | Auth required | No (run `gog auth setup`) |
| 5 | Not found | No |
| 6 | Permission denied | No |
| 7 | Rate limited | Yes (wait and retry) |
| 8 | Retryable server error | Yes (wait and retry) |

Authentication and permission errors require user intervention. Rate limiting and server errors can be retried after a brief wait.
