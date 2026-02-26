---
name: google-drive
description: Upload, download, search, and share files on Google Drive. Create folders and manage permissions. Use when asked to share a file, upload to gdrive, search cloud storage, manage a Drive folder, or organize Google Drive files.
metadata:
  author: odyssey4me
  version: "0.2.0"
  category: google-workspace
  tags: "files, folders, sharing"
  complexity: standard
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/google-drive.py:*)
---

# Google Drive

Interact with Google Drive for file management, search, and sharing.

## Installation

**Dependencies**: `pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml`

## Setup Verification

After installation, verify the skill is properly configured:

```bash
$SKILL_DIR/scripts/google-drive.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml)
- Authentication configuration
- Connectivity to Google Drive API

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Drive uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/gcp-project-setup.md) - Create project, enable Drive API
2. [Google OAuth Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md) - Configure credentials

### Quick Start

1. Create `~/.config/agent-skills/google.yaml`:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```

2. Run `$SKILL_DIR/scripts/google-drive.py check` to trigger OAuth flow and verify setup.

On scope or authentication errors, see the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

## Script Usage

```bash
# Setup and auth
$SKILL_DIR/scripts/google-drive.py check
$SKILL_DIR/scripts/google-drive.py auth setup --client-id ID --client-secret SECRET
$SKILL_DIR/scripts/google-drive.py auth reset
$SKILL_DIR/scripts/google-drive.py auth status

# Files
$SKILL_DIR/scripts/google-drive.py files list [--query QUERY] [--max-results N] [--order-by FIELD]
$SKILL_DIR/scripts/google-drive.py files search [--name NAME] [--mime-type TYPE] [--folder ID]
$SKILL_DIR/scripts/google-drive.py files get FILE_ID
$SKILL_DIR/scripts/google-drive.py files download FILE_ID --output PATH
$SKILL_DIR/scripts/google-drive.py files upload PATH [--parent ID] [--name NAME] [--mime-type TYPE]
$SKILL_DIR/scripts/google-drive.py files move FILE_ID --parent FOLDER_ID

# Folders
$SKILL_DIR/scripts/google-drive.py folders create NAME [--parent ID]
$SKILL_DIR/scripts/google-drive.py folders list FOLDER_ID [--max-results N]

# Sharing and permissions
$SKILL_DIR/scripts/google-drive.py share FILE_ID --email EMAIL [--role ROLE] [--no-notify]
$SKILL_DIR/scripts/google-drive.py permissions list FILE_ID
$SKILL_DIR/scripts/google-drive.py permissions delete FILE_ID PERMISSION_ID
```

See [command-reference.md](references/command-reference.md) for full argument details and examples.

## Examples

### Verify Setup

```bash
$SKILL_DIR/scripts/google-drive.py check
```

### Find recent PDF files

```bash
$SKILL_DIR/scripts/google-drive.py files list --query "mimeType='application/pdf'" --max-results 5
```

### Search for documents by name

```bash
$SKILL_DIR/scripts/google-drive.py files search --name "project proposal"
```

### Download a file

```bash
# First, find the file ID
$SKILL_DIR/scripts/google-drive.py files search --name "report.pdf"

# Then download it
$SKILL_DIR/scripts/google-drive.py files download FILE_ID -o ./report.pdf
```

### Upload and share a file

```bash
# Upload the file
$SKILL_DIR/scripts/google-drive.py files upload ./presentation.pdf --name "Q4 Presentation"

# Share with a colleague
$SKILL_DIR/scripts/google-drive.py share FILE_ID --email colleague@example.com --role writer
```

### Organize files into folders

```bash
# Create a folder
$SKILL_DIR/scripts/google-drive.py folders create "Project Documents"

# Upload files to the folder
$SKILL_DIR/scripts/google-drive.py files upload ./doc1.pdf --parent FOLDER_ID
$SKILL_DIR/scripts/google-drive.py files upload ./doc2.pdf --parent FOLDER_ID

# List folder contents
$SKILL_DIR/scripts/google-drive.py folders list FOLDER_ID
```

## Drive Search Query Syntax

See [drive-queries.md](references/drive-queries.md) for operators, searchable fields, and query examples.

## Common MIME Types

See [api-reference.md](references/api-reference.md) for MIME types used with `--mime-type` and search queries.

## Unsupported Operations

See [api-reference.md](references/api-reference.md#unsupported-operations) for operations not yet implemented and their alternatives.

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails with an authentication error, insufficient scope error, or permission denied error (exit code 1), **stop and inform the user**. Do not retry or attempt to fix the issue autonomously — these errors require user interaction (browser-based OAuth consent). Point the user to the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors (HTTP 5xx) may succeed on retry after a brief wait. All other errors should be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Cannot download Google Docs

Google Docs, Sheets, and Slides are not binary files - they cannot be downloaded directly. Use the Google Drive web interface to export them to a downloadable format (PDF, DOCX, etc.).

