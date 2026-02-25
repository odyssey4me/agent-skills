---
name: google-drive
description: Manage Google Drive files and folders. List, search, upload, download files, create folders, and manage sharing. Use when working with Google Drive file management.
metadata:
  author: odyssey4me
  version: "0.1.0"
  category: google-workspace
  tags: [files, folders, sharing]
  complexity: standard
license: MIT
allowed-tools: Bash(python $SKILL_DIR/scripts/google-drive.py *)
---

# Google Drive

Interact with Google Drive for file management, search, and sharing.

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
   ```

2. **Download the skill** from [Releases](https://github.com/odyssey4me/agent-skills/releases) or use directly from this repository.

## Setup Verification

After installation, verify the skill is properly configured:

```bash
python $SKILL_DIR/scripts/google-drive.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml)
- Authentication configuration
- Connectivity to Google Drive API

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Drive uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](../../docs/gcp-project-setup.md) - Create project, enable Drive API
2. [Google OAuth Setup Guide](../../docs/google-oauth-setup.md) - Configure credentials

### Quick Start

1. Create `~/.config/agent-skills/google.yaml`:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```

2. Run `python $SKILL_DIR/scripts/google-drive.py check` to trigger OAuth flow and verify setup.

### OAuth Scopes

The skill requests granular scopes for different operations:

| Scope | Permission | Used For |
|-------|-----------|----------|
| `drive.readonly` | Read files and metadata | list, search, download |
| `drive` | Full read/write access to all files | upload, create folders, share, move |
| `drive.metadata.readonly` | View file metadata only | get file info |

### Scope Errors

If you encounter "insufficient scope" errors, reset your token and re-authenticate:

1. Reset token: `python $SKILL_DIR/scripts/google-drive.py auth reset`
2. Re-run: `python $SKILL_DIR/scripts/google-drive.py check`

## Commands

### check

Verify configuration and connectivity.

```bash
python $SKILL_DIR/scripts/google-drive.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Google Drive API
- Displays your email address and storage usage

### auth setup

Store OAuth 2.0 client credentials for custom OAuth flow.

```bash
python $SKILL_DIR/scripts/google-drive.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

Credentials are saved to `~/.config/agent-skills/google-drive.yaml`.

### auth reset

Clear stored OAuth token. The next command that needs authentication will trigger re-authentication automatically.

```bash
python $SKILL_DIR/scripts/google-drive.py auth reset
```

Use this when you encounter scope or authentication errors.

### auth status

Show current OAuth token information without making API calls.

```bash
python $SKILL_DIR/scripts/google-drive.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token presence, token expiry, and client ID.

### files list

List files in your Drive.

```bash
# List recent files
python $SKILL_DIR/scripts/google-drive.py files list

# List with search query
python $SKILL_DIR/scripts/google-drive.py files list --query "name contains 'report'"

# List with max results
python $SKILL_DIR/scripts/google-drive.py files list --max-results 20

# List sorted by name
python $SKILL_DIR/scripts/google-drive.py files list --order-by "name"
```

**Arguments:**
- `--query`: Drive search query (optional)
- `--max-results`: Maximum number of results (default: 10)
- `--order-by`: Sort order (default: "modifiedTime desc")

### files search

Search for files with filters.

```bash
# Search by name
python $SKILL_DIR/scripts/google-drive.py files search --name "quarterly report"

# Search by MIME type
python $SKILL_DIR/scripts/google-drive.py files search --mime-type "application/pdf"

# Search in a specific folder
python $SKILL_DIR/scripts/google-drive.py files search --folder FOLDER_ID

# Combine filters
python $SKILL_DIR/scripts/google-drive.py files search --name "budget" --mime-type "application/vnd.google-apps.spreadsheet"
```

**Arguments:**
- `--name`: File name to search for (partial match)
- `--mime-type`: MIME type filter
- `--folder`: Parent folder ID

### files get

Get file metadata by ID.

```bash
# Get file details
python $SKILL_DIR/scripts/google-drive.py files get FILE_ID
```

**Arguments:**
- `file_id`: The file ID (required)

### files download

Download a file from Google Drive.

```bash
# Download a file
python $SKILL_DIR/scripts/google-drive.py files download FILE_ID --output /path/to/local/file

# Short form
python $SKILL_DIR/scripts/google-drive.py files download FILE_ID -o ./downloaded-file.pdf
```

**Arguments:**
- `file_id`: The file ID (required)
- `--output`, `-o`: Output file path (required)

**Note:** Google Docs, Sheets, and Slides cannot be downloaded directly. Use the Google Drive web interface to export them.

### files upload

Upload a file to Google Drive.

```bash
# Upload a file
python $SKILL_DIR/scripts/google-drive.py files upload /path/to/file.pdf

# Upload to a specific folder
python $SKILL_DIR/scripts/google-drive.py files upload /path/to/file.pdf --parent FOLDER_ID

# Upload with custom name
python $SKILL_DIR/scripts/google-drive.py files upload /path/to/file.pdf --name "Quarterly Report 2024"

# Upload with specific MIME type
python $SKILL_DIR/scripts/google-drive.py files upload /path/to/file --mime-type "text/csv"
```

**Arguments:**
- `path`: Local file path (required)
- `--parent`: Parent folder ID
- `--mime-type`: MIME type (auto-detected if not provided)
- `--name`: Name for the file in Drive

### files move

Move a file to a different folder.

```bash
# Move a file to a folder
python $SKILL_DIR/scripts/google-drive.py files move FILE_ID --parent FOLDER_ID
```

**Arguments:**
- `file_id`: The file ID (required)
- `--parent`: Destination folder ID (required)

### folders create

Create a new folder.

```bash
# Create folder in root
python $SKILL_DIR/scripts/google-drive.py folders create "New Folder"

# Create folder inside another folder
python $SKILL_DIR/scripts/google-drive.py folders create "Subfolder" --parent FOLDER_ID
```

**Arguments:**
- `name`: Folder name (required)
- `--parent`: Parent folder ID

### folders list

List contents of a folder.

```bash
# List folder contents
python $SKILL_DIR/scripts/google-drive.py folders list FOLDER_ID

# List with max results
python $SKILL_DIR/scripts/google-drive.py folders list FOLDER_ID --max-results 50
```

**Arguments:**
- `folder_id`: The folder ID (required)
- `--max-results`: Maximum number of results (default: 100)

### share

Share a file with a user.

```bash
# Share as reader (default)
python $SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com

# Share as writer
python $SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com --role writer

# Share as commenter
python $SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com --role commenter

# Share without sending notification
python $SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com --no-notify
```

**Arguments:**
- `file_id`: File ID to share (required)
- `--email`: Email address to share with (required)
- `--role`: Permission role - reader, writer, commenter, owner (default: reader)
- `--no-notify`: Don't send notification email

### permissions list

List permissions for a file.

```bash
# List permissions
python $SKILL_DIR/scripts/google-drive.py permissions list FILE_ID
```

**Arguments:**
- `file_id`: The file ID (required)

### permissions delete

Remove a permission from a file.

```bash
# Delete a permission
python $SKILL_DIR/scripts/google-drive.py permissions delete FILE_ID PERMISSION_ID
```

**Arguments:**
- `file_id`: The file ID (required)
- `permission_id`: The permission ID to delete (required)

## Examples

### Verify Setup

```bash
python $SKILL_DIR/scripts/google-drive.py check
```

### Find recent PDF files

```bash
python $SKILL_DIR/scripts/google-drive.py files list --query "mimeType='application/pdf'" --max-results 5
```

### Search for documents by name

```bash
python $SKILL_DIR/scripts/google-drive.py files search --name "project proposal"
```

### Download a file

```bash
# First, find the file ID
python $SKILL_DIR/scripts/google-drive.py files search --name "report.pdf"

# Then download it
python $SKILL_DIR/scripts/google-drive.py files download FILE_ID -o ./report.pdf
```

### Upload and share a file

```bash
# Upload the file
python $SKILL_DIR/scripts/google-drive.py files upload ./presentation.pdf --name "Q4 Presentation"

# Share with a colleague
python $SKILL_DIR/scripts/google-drive.py share FILE_ID --email colleague@example.com --role writer
```

### Organize files into folders

```bash
# Create a folder
python $SKILL_DIR/scripts/google-drive.py folders create "Project Documents"

# Upload files to the folder
python $SKILL_DIR/scripts/google-drive.py files upload ./doc1.pdf --parent FOLDER_ID
python $SKILL_DIR/scripts/google-drive.py files upload ./doc2.pdf --parent FOLDER_ID

# List folder contents
python $SKILL_DIR/scripts/google-drive.py folders list FOLDER_ID
```

## Drive Search Query Syntax

Common search operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `name contains` | Name contains string | `name contains 'report'` |
| `name =` | Exact name match | `name = 'Budget 2024.xlsx'` |
| `mimeType =` | File type | `mimeType = 'application/pdf'` |
| `'ID' in parents` | In folder | `'folder_id' in parents` |
| `modifiedTime >` | Modified after | `modifiedTime > '2024-01-01'` |
| `trashed =` | Trashed status | `trashed = false` |
| `starred =` | Starred status | `starred = true` |
| `sharedWithMe` | Shared files | `sharedWithMe = true` |

Combine operators with `and` or `or`:

```bash
# PDF files modified this year
"mimeType = 'application/pdf' and modifiedTime > '2024-01-01'"

# Spreadsheets containing 'budget'
"name contains 'budget' and mimeType = 'application/vnd.google-apps.spreadsheet'"

# Files in a specific folder that are not trashed
"'folder_id' in parents and trashed = false"
```

For the complete reference, see [drive-queries.md](references/drive-queries.md).

## Common MIME Types

| Type | MIME Type |
|------|-----------|
| Folder | `application/vnd.google-apps.folder` |
| Google Doc | `application/vnd.google-apps.document` |
| Google Sheet | `application/vnd.google-apps.spreadsheet` |
| Google Slides | `application/vnd.google-apps.presentation` |
| PDF | `application/pdf` |
| Word | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Excel | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PowerPoint | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| Text | `text/plain` |
| CSV | `text/csv` |
| Image (JPEG) | `image/jpeg` |
| Image (PNG) | `image/png` |

## Unsupported Operations

The following Google Drive API operations are **not yet implemented** in this skill:

| Operation | API Method | Alternative |
|-----------|-----------|-------------|
| Rename files | `files.update` (name) | Use Google Drive web interface |
| Delete files permanently | `files.delete` | Use Google Drive web interface |
| Trash / untrash files | `files.update` (trashed) | Use Google Drive web interface |
| Copy files | `files.copy` | Download and re-upload as a workaround |
| Export Google Docs/Sheets/Slides | `files.export` | Use the **google-docs**, **google-sheets**, or **google-slides** skills to work with Workspace document content |
| Update existing permissions (change role) | `permissions.update` | Delete and re-create the permission with the new role |
| Empty trash | `files.emptyTrash` | Use Google Drive web interface |
| File version history | `revisions.*` | Use Google Drive web interface |
| Comments and replies | `comments.*`, `replies.*` | Use Google Drive web interface |
| Watch for file changes | `files.watch`, `changes.*` | Not available via any skill |
| Shared drive management | `drives.*` | Not available via any skill |

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails with an authentication error, insufficient scope error, or permission denied error (exit code 1), do NOT retry the same command. Instead:

1. Inform the user about the error
2. Run `python $SKILL_DIR/scripts/google-drive.py auth status` to check the current token state
3. Suggest the user run `python $SKILL_DIR/scripts/google-drive.py auth reset` followed by `python $SKILL_DIR/scripts/google-drive.py check` to re-authenticate
4. The `auth reset` and `check` commands require user interaction (browser-based OAuth consent) and cannot be completed autonomously

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors (HTTP 5xx) may succeed on retry after a brief wait. All other errors should be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Check command fails

Run `python $SKILL_DIR/scripts/google-drive.py check` to diagnose issues. It will provide specific error messages and setup instructions.

### Authentication failed

1. Verify your OAuth client ID and client secret are correct in `~/.config/agent-skills/google-drive.yaml`
2. Token expired or corrupted — reset and re-authenticate:
   ```bash
   python $SKILL_DIR/scripts/google-drive.py auth reset
   python $SKILL_DIR/scripts/google-drive.py check
   ```

### Permission denied

Your OAuth token may not have the necessary scopes. Reset your token and re-authenticate:

```bash
python $SKILL_DIR/scripts/google-drive.py auth reset
python $SKILL_DIR/scripts/google-drive.py check
```

### Cannot download Google Docs

Google Docs, Sheets, and Slides are not binary files - they cannot be downloaded directly. Use the Google Drive web interface to export them to a downloadable format (PDF, DOCX, etc.).

### Import errors

Ensure dependencies are installed:
```bash
pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
```

### Rate limiting

Drive API has quota limits. If you hit rate limits, wait a few minutes before retrying. For high-volume usage, consider requesting quota increases in the Google Cloud Console.

## API Scopes

This skill requests the following OAuth scopes:

- `https://www.googleapis.com/auth/drive.readonly` - Read files and metadata
- `https://www.googleapis.com/auth/drive` - Full read/write access to all files
- `https://www.googleapis.com/auth/drive.metadata.readonly` - View file metadata only

These scopes provide full file management capabilities across all Drive files.

## Security Notes

- **OAuth tokens** are stored securely in your system keyring
- **Client secrets** are stored in `~/.config/agent-skills/google-drive.yaml` with file permissions 600
- **No passwords** are stored - only OAuth tokens
- **Tokens refresh automatically** when using the skill
- **Browser-based consent** ensures you approve all requested permissions

Always review OAuth consent screens before granting access to your Google Drive.
