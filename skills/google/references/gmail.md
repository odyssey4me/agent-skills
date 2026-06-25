# Gmail Command Reference

Full command reference for `gog gmail`. All commands support `--json` and `--plain` output.

## Read

| Command | Description |
|---------|-------------|
| `search <query>` | Search threads using Gmail query syntax |
| `get <messageId>` | Get a message (full, metadata, or raw) |
| `raw <messageId>` | Dump raw Gmail API response as JSON |
| `attachment <messageId> <attachmentId>` | Download a single attachment |
| `url <threadId>` | Print Gmail web URLs for threads |
| `history` | Gmail history |

### Search flags

- `--max N` — limit results (default varies)
- `--after "2026-01-01"` — messages after date
- `--before "2026-12-31"` — messages before date
- `--has attachment` — filter by attachment
- `--label <name>` — filter by label

### Gmail query syntax

Standard Gmail search operators work: `from:`, `to:`, `subject:`, `is:unread`, `is:starred`, `has:attachment`, `newer_than:7d`, `older_than:30d`, `label:`, `in:inbox`, `in:sent`, `in:trash`, `filename:pdf`.

## Organize

| Command | Description |
|---------|-------------|
| `thread get <threadId>` | Get a full thread |
| `thread modify <threadId>` | Modify thread labels |
| `labels list` | List all labels |
| `labels create <name>` | Create a label |
| `labels delete <labelId>` | Delete a label |
| `batch delete <messageId>...` | Permanently delete messages |
| `archive <messageId>...` | Remove from inbox |
| `mark-read <messageId>...` | Mark messages as read |
| `unread <messageId>...` | Mark messages as unread |
| `trash <messageId>...` | Move to trash |

## Write

| Command | Description |
|---------|-------------|
| `send` | Send an email |
| `reply <messageId>` | Reply to a message |
| `reply-all <messageId>` | Reply to all participants |
| `forward <messageId>` | Forward to new recipients |
| `autoreply <query>` | Reply once to matching messages |

### Send flags

- `--to "user@example.com"` — recipient (required)
- `--cc "cc@example.com"` — CC recipients
- `--bcc "bcc@example.com"` — BCC recipients
- `--subject "Subject"` — email subject
- `--body "Body text"` — email body
- `--body-file path.md` — read body from file
- `--html` — send as HTML
- `--attach file.pdf` — attach a file

## Drafts

| Command | Description |
|---------|-------------|
| `drafts list` | List drafts |
| `drafts create` | Create a draft (same flags as send) |
| `drafts send <draftId>` | Send an existing draft |
| `drafts delete <draftId>` | Delete a draft |

## Admin

| Command | Description |
|---------|-------------|
| `settings filters export` | Export Gmail filters |
| `track` | Email open tracking commands |
