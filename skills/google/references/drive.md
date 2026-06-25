# Drive Command Reference

Full command reference for `gog drive`. All commands support `--json` and `--plain` output.

## Browse

| Command | Description |
|---------|-------------|
| `ls` | List files in a folder (default: root) |
| `search <query>` | Full-text search across Drive |
| `tree` | Print a read-only folder tree |
| `du` | Summarize Drive folder sizes |
| `inventory` | Export a read-only Drive inventory |
| `get <fileId>` | Get file metadata |
| `url <fileId>...` | Print web URLs for files |
| `raw <fileId>` | Dump raw API response as JSON |

### List/search flags

- `--folder <folderId>` — list files in specific folder
- `--max N` — limit results
- `--mime-type "application/pdf"` — filter by MIME type
- `--raw-query "..."` — exact Drive API query filter

## File Operations

| Command | Description |
|---------|-------------|
| `download <fileId>` | Download a file (exports Google formats) |
| `upload <localPath>` | Upload a file |
| `copy <fileId> <name>` | Copy a file |
| `move <fileId>` | Move a file to a different folder |
| `rename <fileId> <newName>` | Rename a file or folder |
| `mkdir <name>` | Create a folder |
| `delete <fileId>` | Move to trash (--permanent for forever) |

### Upload flags

- `--parent <folderId>` — destination folder
- `--name "Custom Name"` — override filename
- `--convert` — convert to Google format (e.g., CSV to Sheets)

### Download flags

- `--format <fmt>` — export format for Google files (pdf, docx, xlsx, pptx, md, txt, html, csv)
- `--out <path>` — output file path

## Sharing

| Command | Description |
|---------|-------------|
| `share <fileId>` | Share a file or folder |
| `unshare <fileId> <permissionId>` | Remove a permission |
| `permissions <fileId>` | List permissions on a file |
| `audit` | Audit Drive sharing (read-only) |
| `bulk` | Bulk permission operations |

### Share flags

- `--email "user@example.com"` — share with user
- `--role reader|writer|commenter` — permission role
- `--type user|group|domain|anyone` — permission type

## Comments

| Command | Description |
|---------|-------------|
| `comments list <fileId>` | List comments on a file |
| `comments create <fileId>` | Add a comment |
| `comments reply <fileId> <commentId>` | Reply to a comment |
| `comments resolve <fileId> <commentId>` | Resolve a comment |
| `comments delete <fileId> <commentId>` | Delete a comment |

## Advanced

| Command | Description |
|---------|-------------|
| `labels` | Read and modify Drive labels |
| `shortcut` | Manage shortcuts to Drive files |
| `drives` | List shared drives (Team Drives) |
| `revisions` | List and inspect file revisions |
| `changes` | Track Drive changes for sync/automation |
| `activity` | Query Drive Activity audit events |
