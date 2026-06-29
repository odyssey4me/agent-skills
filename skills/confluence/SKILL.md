---
name: confluence
description: Search and manage Confluence pages and spaces using CQL, read/create/update pages with Markdown support. Use when working with Confluence documentation.
metadata:
  author: odyssey4me
  version: "2.4.1"
  category: documentation
  tags: "wiki, pages, spaces"
  complexity: standard
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/confluence.py:*)
---

# Confluence

Interact with Confluence for content search, viewing pages, and space management.

> **Creating/Updating Content?** See [references/creating-content.md](references/creating-content.md) for page creation and updates with Markdown.

## Installation

**Dependencies**: `pip install --user requests keyring pyyaml`

## Setup Verification

After installation, verify the skill configuration by running:

```bash
$SKILL_DIR/scripts/confluence.py check
```

This will check:
- Python dependencies (requests, keyring, pyyaml)
- Authentication configuration
- Connectivity to Confluence

If anything is missing, the check command will provide setup instructions.

## Authentication

Configure Confluence authentication using one of these methods:

### Option 1: Environment Variables (Recommended)

```bash
export CONFLUENCE_URL="https://yourcompany.atlassian.net/wiki"
export CONFLUENCE_EMAIL="you@example.com"
export CONFLUENCE_API_TOKEN="your-token"
```

Add these to your `~/.bashrc` or `~/.zshrc` for persistence.

### Option 2: Config File

Create `~/.config/agent-skills/confluence.yaml`:

```yaml
url: https://yourcompany.atlassian.net/wiki
email: you@example.com
token: your-token
```

### Required Credentials

- **URL**: Your Confluence Cloud URL (e.g. `https://yourcompany.atlassian.net/wiki`)
- **Email**: Your Atlassian account email
- **API Token**: Create at https://id.atlassian.com/manage-profile/security/api-tokens

## Configuration Defaults

Optionally configure defaults in `~/.config/agent-skills/confluence.yaml` to reduce repetitive typing:

```yaml
# Authentication (optional if using environment variables)
url: https://yourcompany.atlassian.net/wiki
email: you@example.com
token: your-token

# Optional defaults
defaults:
  cql_scope: "space = DEMO"
  max_results: 25
  default_space: "DEMO"
```

### How Defaults Work

- **CLI arguments always override** config defaults
- **CQL scope** is prepended to all searches: `(scope) AND (your_query)`
- **Default space** is used when space parameter is omitted

### View Configuration

```bash
# Show all configuration
$SKILL_DIR/scripts/confluence.py config show

# Show space-specific defaults
$SKILL_DIR/scripts/confluence.py config show --space DEMO
```

## Commands

See [permissions.md](references/permissions.md) for read/write classification of each command.

### check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/confluence.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Confluence
- API connectivity is working

### search

Search for content using CQL (Confluence Query Language).

```bash
# Basic search
$SKILL_DIR/scripts/confluence.py search "type=page AND space = DEMO"
$SKILL_DIR/scripts/confluence.py search "title~login" --space DEMO

# Filter by type
$SKILL_DIR/scripts/confluence.py search "space = DEMO" --type page

# Limit results
$SKILL_DIR/scripts/confluence.py search "type=page" --max-results 10
```

**Arguments:**
- `cql`: CQL query string (required)
- `--max-results`: Maximum number of results (default: 50)
- `--type`: Content type filter (page, blogpost, comment)
- `--space`: Limit to specific space

**See also**: [CQL Reference](#cql-reference) for query syntax

### page get

Get page content by ID or title.

```bash
# Get by title (returns Markdown by default)
$SKILL_DIR/scripts/confluence.py page get "My Page Title"

# Get by ID
$SKILL_DIR/scripts/confluence.py page get 123456

# Get without body content
$SKILL_DIR/scripts/confluence.py page get "My Page" --no-body

# Get in original format (not Markdown)
$SKILL_DIR/scripts/confluence.py page get "My Page" --raw

# Save to file with images downloaded to sibling directory
$SKILL_DIR/scripts/confluence.py page get "My Page" -o my-page.md

# Export with YAML frontmatter (for round-tripping)
$SKILL_DIR/scripts/confluence.py page get 123456 --frontmatter -o page.md
```

**Output**: By default, displays page metadata and body content converted to Markdown for readability. When `--output`/`-o` is used, image attachments are automatically downloaded to a sibling directory named after the output file (e.g. `-o my-page.md` saves images to `my-page/`) and referenced as relative paths in the markdown output. Without `--output`, no images are downloaded.

**Arguments:**
- `page_identifier`: Page ID or title (required)
- `--markdown`: Output body as Markdown (default)
- `--raw`: Output in original format
- `--no-body`: Don't include body content
- `--frontmatter`: Output as markdown with YAML frontmatter (title, space, labels, parent) for round-tripping with `page create`/`page update`
- `--output`/`-o`: Write output to file; images are downloaded to a sibling directory named after the file stem

### page create / update

For creating and updating pages with Markdown support, see [references/creating-content.md](references/creating-content.md).

Quick examples:
```bash
# Create page from Markdown file
$SKILL_DIR/scripts/confluence.py page create --space DEMO --title "Documentation" \
  --body-file README.md

# Create page with table of contents
$SKILL_DIR/scripts/confluence.py page create --space DEMO --title "Guide" \
  --body-file guide.md --toc

# Update page from file
$SKILL_DIR/scripts/confluence.py page update 123456 --body-file updated.md
```

**Images:** When using `--body-file`, local image references in markdown (`![alt](path/to/image.png)`) are automatically uploaded as page attachments and embedded inline. Paths are resolved relative to the markdown file's directory.

**Frontmatter support:** Markdown files can include YAML frontmatter with page metadata. CLI flags take precedence over frontmatter values. Supported fields: `title`, `space`, `labels`, `parent`, `toc`.

```yaml
---
title: API Documentation
space: DEMO
labels: docs, api
parent: 123456
toc: true
---

# Introduction
...
```

**Table of contents:** Use `--toc` (or `toc: true` in frontmatter) to prepend a TOC macro.

**Internal link conversion:** Links pointing to pages on the same Confluence instance are automatically converted to native Confluence links during markdown conversion. The linked page is validated before conversion — invalid links are left as-is.

### page move

Move a page under a new parent, or to the space root.

```bash
# Move under a new parent
$SKILL_DIR/scripts/confluence.py page move 123456 --parent 789012

# Move to space root (no parent)
$SKILL_DIR/scripts/confluence.py page move 123456
```

### page delete

Delete a page by ID (moves to trash on Cloud).

```bash
$SKILL_DIR/scripts/confluence.py page delete 123456
```

### space

Manage spaces.

```bash
# List all spaces
$SKILL_DIR/scripts/confluence.py space list

# List with limit
$SKILL_DIR/scripts/confluence.py space list --max-results 10

# Filter by type
$SKILL_DIR/scripts/confluence.py space list --type global

# Get space details
$SKILL_DIR/scripts/confluence.py space get DEMO
```

**Arguments:**
- `list`: List spaces
  - `--type`: Filter by type (global, personal)
  - `--max-results`: Maximum results
- `get <space-key>`: Get space details

For creating spaces, see [references/creating-content.md](references/creating-content.md).

### space permissions

View, add, and remove space permissions.

```bash
# List all permissions for a space
$SKILL_DIR/scripts/confluence.py space permissions list DEMO

# Filter by subject type
$SKILL_DIR/scripts/confluence.py space permissions list DEMO --subject-type group

# Add a permission
$SKILL_DIR/scripts/confluence.py space permissions add DEMO \
  --subject-type user --subject "5a1234abc" --operation read --target space

# Remove a permission by ID
$SKILL_DIR/scripts/confluence.py space permissions remove DEMO --id 2154
```

**Arguments:**
- `list <space-key>`: List permissions
  - `--subject-type`: Filter by user or group
- `add <space-key>`: Add a permission
  - `--subject-type`: user or group (required)
  - `--subject`: User account ID or group name/ID (required)
  - `--operation`: read, create, delete, export, administer, archive, restrict_content (required)
  - `--target`: space, page, blogpost, comment, attachment (required)
- `remove <space-key>`: Remove a permission
  - `--id`: Permission ID (required)

### config

Show configuration and defaults.

```bash
# Show all configuration
$SKILL_DIR/scripts/confluence.py config show

# Show space-specific defaults
$SKILL_DIR/scripts/confluence.py config show --space DEMO
```

This displays:
- Authentication settings (with masked token)
- Default CQL scope, max results, and default space
- Space-specific defaults for parent pages and labels

## CQL Reference

Common CQL (Confluence Query Language) queries:

| Query | Description |
|-------|-------------|
| `type = page` | All pages |
| `type = blogpost` | All blog posts |
| `space = DEMO` | Content in DEMO space |
| `title ~ "login"` | Title contains "login" |
| `text ~ "API"` | Body text contains "API" |
| `created >= now("-7d")` | Created in last 7 days |
| `lastmodified >= startOfDay()` | Modified today |
| `creator = currentUser()` | Created by you |
| `contributor = "username"` | User contributed |
| `label = "important"` | Has "important" label |

Combine with `AND`, `OR`, and use `ORDER BY` for sorting:

```bash
$SKILL_DIR/scripts/confluence.py search "type=page AND space=DEMO AND created >= now('-30d') ORDER BY created DESC"
```

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

