# Google Drive Search Query Syntax

This document provides a comprehensive reference for Google Drive search queries used with the `files list` command.

## Basic Syntax

Queries use a simple syntax of `field operator value`. Multiple conditions can be combined with `and` or `or`.

```bash
python scripts/google-drive.py files list --query "name contains 'report'"
```

## Operators

| Operator | Description | Applies To |
|----------|-------------|------------|
| `contains` | Contains substring | name, fullText |
| `=` | Equals exactly | name, mimeType, trashed, starred, etc. |
| `!=` | Not equals | mimeType, trashed, starred, etc. |
| `<` | Less than | modifiedTime, createdTime |
| `<=` | Less than or equal | modifiedTime, createdTime |
| `>` | Greater than | modifiedTime, createdTime |
| `>=` | Greater than or equal | modifiedTime, createdTime |
| `in` | Value in collection | parents, owners, writers, readers |
| `has` | Collection contains | owners, writers, readers |

## Searchable Fields

### Name and Content

| Field | Description | Example |
|-------|-------------|---------|
| `name` | File name | `name contains 'budget'` |
| `fullText` | Name + content + description | `fullText contains 'quarterly'` |

**Note:** `fullText` searches inside documents (Google Docs, PDFs with OCR, etc.).

### File Properties

| Field | Description | Example |
|-------|-------------|---------|
| `mimeType` | MIME type | `mimeType = 'application/pdf'` |
| `trashed` | In trash | `trashed = false` |
| `starred` | Is starred | `starred = true` |
| `sharedWithMe` | Shared with me | `sharedWithMe = true` |

### Dates

| Field | Description | Example |
|-------|-------------|---------|
| `modifiedTime` | Last modified | `modifiedTime > '2024-01-01T00:00:00'` |
| `createdTime` | Created date | `createdTime >= '2024-06-01'` |
| `viewedByMeTime` | Last viewed | `viewedByMeTime > '2024-01-01'` |

**Date format:** RFC 3339 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`)

### Relationships

| Field | Description | Example |
|-------|-------------|---------|
| `parents` | Parent folder | `'folder_id' in parents` |
| `owners` | File owners | `'user@example.com' in owners` |
| `writers` | Users with write access | `'user@example.com' in writers` |
| `readers` | Users with read access | `'user@example.com' in readers` |

## Common Query Examples

### By Name

```bash
# Contains substring
--query "name contains 'report'"

# Exact match
--query "name = 'Budget 2024.xlsx'"

# Case-insensitive contains
--query "name contains 'REPORT'"
```

### By Type

```bash
# PDF files
--query "mimeType = 'application/pdf'"

# Google Docs
--query "mimeType = 'application/vnd.google-apps.document'"

# Google Sheets
--query "mimeType = 'application/vnd.google-apps.spreadsheet'"

# Folders only
--query "mimeType = 'application/vnd.google-apps.folder'"

# Images
--query "mimeType contains 'image/'"

# Not folders
--query "mimeType != 'application/vnd.google-apps.folder'"
```

### By Date

```bash
# Modified this year
--query "modifiedTime > '2024-01-01'"

# Modified in the last 7 days
--query "modifiedTime > '2024-01-17'"

# Created between dates
--query "createdTime >= '2024-01-01' and createdTime < '2024-02-01'"

# Recently viewed
--query "viewedByMeTime > '2024-01-01'"
```

### By Location

```bash
# Files in a specific folder
--query "'FOLDER_ID' in parents"

# Files in root folder
--query "'root' in parents"

# Exclude trashed files
--query "'FOLDER_ID' in parents and trashed = false"
```

### By Sharing

```bash
# Files shared with me
--query "sharedWithMe = true"

# Files I own
--query "'me' in owners"

# Files shared with specific user
--query "'user@example.com' in writers"
```

### Combined Queries

```bash
# PDFs modified this year
--query "mimeType = 'application/pdf' and modifiedTime > '2024-01-01'"

# Spreadsheets containing 'budget'
--query "name contains 'budget' and mimeType = 'application/vnd.google-apps.spreadsheet'"

# Files in folder, not trashed
--query "'FOLDER_ID' in parents and trashed = false"

# Starred PDFs
--query "starred = true and mimeType = 'application/pdf'"

# Recent documents shared with me
--query "sharedWithMe = true and modifiedTime > '2024-01-01'"
```

### Using OR

```bash
# PDFs or Word documents
--query "mimeType = 'application/pdf' or mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'"

# Files containing 'report' or 'summary'
--query "name contains 'report' or name contains 'summary'"
```

### Full Text Search

```bash
# Search inside documents
--query "fullText contains 'quarterly earnings'"

# Combine with type filter
--query "fullText contains 'project plan' and mimeType = 'application/vnd.google-apps.document'"
```

## MIME Type Reference

### Google Workspace Types

| Type | MIME Type |
|------|-----------|
| Folder | `application/vnd.google-apps.folder` |
| Document | `application/vnd.google-apps.document` |
| Spreadsheet | `application/vnd.google-apps.spreadsheet` |
| Presentation | `application/vnd.google-apps.presentation` |
| Form | `application/vnd.google-apps.form` |
| Drawing | `application/vnd.google-apps.drawing` |
| Site | `application/vnd.google-apps.site` |
| Shortcut | `application/vnd.google-apps.shortcut` |

### Common File Types

| Type | MIME Type |
|------|-----------|
| PDF | `application/pdf` |
| Word (.docx) | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Word (.doc) | `application/msword` |
| Excel (.xlsx) | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| Excel (.xls) | `application/vnd.ms-excel` |
| PowerPoint (.pptx) | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| PowerPoint (.ppt) | `application/vnd.ms-powerpoint` |
| Plain text | `text/plain` |
| CSV | `text/csv` |
| HTML | `text/html` |
| JSON | `application/json` |
| ZIP | `application/zip` |

### Image Types

| Type | MIME Type |
|------|-----------|
| JPEG | `image/jpeg` |
| PNG | `image/png` |
| GIF | `image/gif` |
| WebP | `image/webp` |
| SVG | `image/svg+xml` |
| BMP | `image/bmp` |

### Video Types

| Type | MIME Type |
|------|-----------|
| MP4 | `video/mp4` |
| AVI | `video/x-msvideo` |
| MOV | `video/quicktime` |
| WebM | `video/webm` |

### Audio Types

| Type | MIME Type |
|------|-----------|
| MP3 | `audio/mpeg` |
| WAV | `audio/wav` |
| OGG | `audio/ogg` |
| M4A | `audio/mp4` |

## Order By Options

When listing files, you can specify the sort order:

| Order | Description |
|-------|-------------|
| `modifiedTime desc` | Most recently modified first (default) |
| `modifiedTime` | Oldest modified first |
| `createdTime desc` | Most recently created first |
| `name` | Alphabetical by name |
| `name desc` | Reverse alphabetical |
| `folder,modifiedTime desc` | Folders first, then by modified time |
| `quotaBytesUsed desc` | Largest files first |

```bash
python scripts/google-drive.py files list --order-by "name"
python scripts/google-drive.py files list --order-by "createdTime desc"
```

## Tips

1. **Always exclude trash**: Add `and trashed = false` to avoid finding deleted files

2. **Use specific MIME types**: More efficient than searching by extension

3. **Date queries are fast**: Use `modifiedTime` or `createdTime` for efficient filtering

4. **Full text is slow**: `fullText contains` searches inside documents, which is slower

5. **Escape special characters**: Use backslash to escape quotes in names
   ```bash
   --query "name contains 'John\\'s Report'"
   ```

6. **Combine for precision**: More specific queries return faster results
   ```bash
   --query "mimeType = 'application/pdf' and modifiedTime > '2024-01-01' and trashed = false"
   ```

## References

- [Google Drive API Query Reference](https://developers.google.com/drive/api/v3/search-files)
- [Drive API MIME Types](https://developers.google.com/drive/api/v3/mime-types)
