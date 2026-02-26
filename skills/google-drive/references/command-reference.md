# Google Drive Command Reference

Full argument details and examples for all google-drive commands.

## check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/google-drive.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Google Drive API
- Displays your email address and storage usage

## auth setup

Store OAuth 2.0 client credentials for custom OAuth flow.

```bash
$SKILL_DIR/scripts/google-drive.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

Credentials are saved to `~/.config/agent-skills/google-drive.yaml`.

## auth reset

Clear stored OAuth token. The next command that needs authentication will trigger re-authentication automatically.

```bash
$SKILL_DIR/scripts/google-drive.py auth reset
```

Use this when you encounter scope or authentication errors.

## auth status

Show current OAuth token information without making API calls.

```bash
$SKILL_DIR/scripts/google-drive.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token presence, token expiry, and client ID.

## files list

List files in your Drive.

```bash
# List recent files
$SKILL_DIR/scripts/google-drive.py files list

# List with search query
$SKILL_DIR/scripts/google-drive.py files list --query "name contains 'report'"

# List with max results
$SKILL_DIR/scripts/google-drive.py files list --max-results 20

# List sorted by name
$SKILL_DIR/scripts/google-drive.py files list --order-by "name"
```

**Arguments:**
- `--query`: Drive search query (optional)
- `--max-results`: Maximum number of results (default: 10)
- `--order-by`: Sort order (default: "modifiedTime desc")

## files search

Search for files with filters.

```bash
# Search by name
$SKILL_DIR/scripts/google-drive.py files search --name "quarterly report"

# Search by MIME type
$SKILL_DIR/scripts/google-drive.py files search --mime-type "application/pdf"

# Search in a specific folder
$SKILL_DIR/scripts/google-drive.py files search --folder FOLDER_ID

# Combine filters
$SKILL_DIR/scripts/google-drive.py files search --name "budget" --mime-type "application/vnd.google-apps.spreadsheet"
```

**Arguments:**
- `--name`: File name to search for (partial match)
- `--mime-type`: MIME type filter
- `--folder`: Parent folder ID

## files get

Get file metadata by ID.

```bash
# Get file details
$SKILL_DIR/scripts/google-drive.py files get FILE_ID
```

**Arguments:**
- `file_id`: The file ID (required)

## files download

Download a file from Google Drive.

```bash
# Download a file
$SKILL_DIR/scripts/google-drive.py files download FILE_ID --output /path/to/local/file

# Short form
$SKILL_DIR/scripts/google-drive.py files download FILE_ID -o ./downloaded-file.pdf
```

**Arguments:**
- `file_id`: The file ID (required)
- `--output`, `-o`: Output file path (required)

**Note:** Google Docs, Sheets, and Slides cannot be downloaded directly. Use the Google Drive web interface to export them.

## files upload

Upload a file to Google Drive.

```bash
# Upload a file
$SKILL_DIR/scripts/google-drive.py files upload /path/to/file.pdf

# Upload to a specific folder
$SKILL_DIR/scripts/google-drive.py files upload /path/to/file.pdf --parent FOLDER_ID

# Upload with custom name
$SKILL_DIR/scripts/google-drive.py files upload /path/to/file.pdf --name "Quarterly Report 2024"

# Upload with specific MIME type
$SKILL_DIR/scripts/google-drive.py files upload /path/to/file --mime-type "text/csv"
```

**Arguments:**
- `path`: Local file path (required)
- `--parent`: Parent folder ID
- `--mime-type`: MIME type (auto-detected if not provided)
- `--name`: Name for the file in Drive

## files move

Move a file to a different folder.

```bash
# Move a file to a folder
$SKILL_DIR/scripts/google-drive.py files move FILE_ID --parent FOLDER_ID
```

**Arguments:**
- `file_id`: The file ID (required)
- `--parent`: Destination folder ID (required)

## folders create

Create a new folder.

```bash
# Create folder in root
$SKILL_DIR/scripts/google-drive.py folders create "New Folder"

# Create folder inside another folder
$SKILL_DIR/scripts/google-drive.py folders create "Subfolder" --parent FOLDER_ID
```

**Arguments:**
- `name`: Folder name (required)
- `--parent`: Parent folder ID

## folders list

List contents of a folder.

```bash
# List folder contents
$SKILL_DIR/scripts/google-drive.py folders list FOLDER_ID

# List with max results
$SKILL_DIR/scripts/google-drive.py folders list FOLDER_ID --max-results 50
```

**Arguments:**
- `folder_id`: The folder ID (required)
- `--max-results`: Maximum number of results (default: 100)

## share

Share a file with a user.

```bash
# Share as reader (default)
$SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com

# Share as writer
$SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com --role writer

# Share as commenter
$SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com --role commenter

# Share without sending notification
$SKILL_DIR/scripts/google-drive.py share FILE_ID --email user@example.com --no-notify
```

**Arguments:**
- `file_id`: File ID to share (required)
- `--email`: Email address to share with (required)
- `--role`: Permission role - reader, writer, commenter, owner (default: reader)
- `--no-notify`: Don't send notification email

## permissions list

List permissions for a file.

```bash
# List permissions
$SKILL_DIR/scripts/google-drive.py permissions list FILE_ID
```

**Arguments:**
- `file_id`: The file ID (required)

## permissions delete

Remove a permission from a file.

```bash
# Delete a permission
$SKILL_DIR/scripts/google-drive.py permissions delete FILE_ID PERMISSION_ID
```

**Arguments:**
- `file_id`: The file ID (required)
- `permission_id`: The permission ID to delete (required)
