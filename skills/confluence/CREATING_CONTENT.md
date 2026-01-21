# Creating and Updating Confluence Content

This guide covers creating and updating Confluence pages using Markdown.

> **Note**: Most users primarily read from Confluence. For basic usage (search, viewing pages, listing spaces), see the main [SKILL.md](SKILL.md).

## Markdown Support

The Confluence skill uses Markdown as the default format for page content, making it easy to create and read pages.

### Supported Markdown Features

- **Headers**: `#` through `######`
- **Bold**: `**text**` or `__text__`
- **Italic**: `*text*` or `_text_`
- **Code**: \`inline code\`
- **Code blocks**: \`\`\`language ... \`\`\`
- **Lists**: Unordered (`-` or `*`) and ordered (`1.`)
- **Links**: `[text](url)`

### Format Conversion

The skill automatically converts between formats:
- **Cloud instances**: Markdown → ADF (Atlassian Document Format)
- **DC/Server instances**: Markdown → Storage format (XHTML)
- **Reading**: Storage/ADF → Markdown (for display)

You can override the automatic format with `--format`:
```bash
# Use storage format directly
python confluence.py page create --space DEMO --title "Page" \
  --body "<p>HTML content</p>" --format storage

# Use editor format (ADF) directly
python confluence.py page create --space DEMO --title "Page" \
  --body '{"type":"doc","content":[...]}' --format editor
```

## Creating Pages

### Basic Page Creation

```bash
# Create page with inline Markdown
python confluence.py page create --space DEMO --title "New Page" \
  --body "# Heading\n\nThis is **bold** text."

# Create from Markdown file
python confluence.py page create --space DEMO --title "Documentation" \
  --body-file README.md

# Create with parent page
python confluence.py page create --space DEMO --title "Child Page" \
  --body "Content here" --parent 123456

# Create with labels
python confluence.py page create --space DEMO --title "Tagged Page" \
  --body "Content" --labels "important,draft"
```

**Arguments:**
- `--space`: Space key (required)
- `--title`: Page title (required)
- `--body`: Page content (Markdown by default)
- `--body-file`: Read content from file (Markdown)
- `--format`: Input format - `markdown` (default), `storage`, `editor`
- `--parent`: Parent page ID for hierarchy
- `--labels`: Comma-separated labels
- `--json`: Output as JSON

### Example: Creating Rich Content

```bash
python confluence.py page create --space DEMO --title "API Documentation" --body "
# API Documentation

## Overview

This document describes our **REST API**.

## Endpoints

- \`GET /api/users\` - List users
- \`POST /api/users\` - Create user

## Example

\`\`\`python
import requests
response = requests.get('https://api.example.com/users')
\`\`\`

See [official docs](https://docs.example.com) for more.
"
```

### Creating from Markdown Files

```bash
# Use existing README as Confluence page
python confluence.py page create --space DEMO --title "Project README" \
  --body-file README.md
```

## Updating Pages

### Basic Updates

```bash
# Update page content
python confluence.py page update 123456 --body "# Updated\n\nNew content"

# Update from file
python confluence.py page update 123456 --body-file updated.md

# Update title only
python confluence.py page update 123456 --title "New Title"

# Update with specific version (prevents conflicts)
python confluence.py page update 123456 --body "Content" --version 5

# Update using storage format
python confluence.py page update 123456 --body "<p>HTML</p>" --format storage
```

**Arguments:**
- `page_id`: Page ID to update (required)
- `--title`: New title
- `--body`: New content (Markdown by default)
- `--body-file`: Read content from file (Markdown)
- `--format`: Input format - `markdown` (default), `storage`, `editor`
- `--version`: Current version number (auto-detected if not provided)
- `--json`: Output as JSON

**Note**: Version is auto-detected, but you can specify it to ensure you're updating the correct version.

### Handling Version Conflicts

If you get a version conflict when updating, the page was modified since you last viewed it. Get the latest version:

```bash
# Get current version
python confluence.py page get 123456 --no-body

# Update with correct version
python confluence.py page update 123456 --body "Content" --version 5
```

Or let the tool auto-detect the version:

```bash
python confluence.py page update 123456 --body "Content"
```

## Creating Spaces

```bash
# Create new space
python confluence.py space create --key PROJ --name "Project Space"

# Create with description
python confluence.py space create --key PROJ --name "Project Space" \
  --description "Documentation for the project"

# JSON output
python confluence.py space create --key PROJ --name "Project" --json
```

**Arguments:**
- `--key`: Space key (required)
- `--name`: Space name (required)
- `--description`: Space description
- `--type`: Space type (global, personal)
- `--json`: Output as JSON

## Advanced Examples

### Batch Page Creation

```bash
#!/bin/bash
# Create multiple pages from a directory

SPACE="DOCS"
PARENT="123456"

for file in docs/*.md; do
    title=$(basename "$file" .md)
    python confluence.py page create \
        --space "$SPACE" \
        --title "$title" \
        --body-file "$file" \
        --parent "$PARENT"
done
```

### Create Documentation from Files

```bash
# Create main page
python confluence.py page create --space DOCS --title "Main Documentation" \
  --body-file README.md

# Create sub-pages
python confluence.py page create --space DOCS --title "API Reference" \
  --body-file docs/api.md --parent 123456

python confluence.py page create --space DOCS --title "Installation Guide" \
  --body-file docs/install.md --parent 123456
```

### Update Existing Page

```bash
# Update from file
python confluence.py page update 123456 --body-file updated-docs.md

# Update title
python confluence.py page update 123456 --title "Updated Title"

# Update both
python confluence.py page update 123456 --title "New Title" --body-file content.md
```

## Configuration Defaults for Page Creation

Optionally configure space-specific defaults in `~/.config/agent-skills/confluence.yaml`:

```yaml
# Optional space-specific defaults
spaces:
  DEMO:
    default_parent: "123456"  # Parent page ID
    default_labels: ["auto-created"]
  PROD:
    default_parent: "789012"
```

When creating pages in configured spaces, these defaults are automatically applied:

```bash
# Create page uses space defaults
python confluence.py page create --space DEMO --title "New Page" --body "Content"
# Automatically uses default_parent and default_labels from DEMO space defaults
```

## Cloud vs Data Center/Server

The skill automatically detects your Confluence deployment type and adapts:

- **Cloud** (atlassian.net): Uses `/wiki/rest/api` and editor format (ADF)
- **Data Center/Server**: Uses `/rest/api` and storage format (XHTML)

Markdown conversion works seamlessly on both:
- Your Markdown input → Appropriate format for your deployment
- API responses → Converted to Markdown for display

You don't need to worry about the internal formats unless you want to use `--format storage` or `--format editor` explicitly.
