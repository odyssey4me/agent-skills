# Google Drive API Reference

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
