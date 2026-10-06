---
name: confluence
description: Search and manage Confluence pages and spaces using CQL, read/create/update pages with Markdown support. Use when working with Confluence documentation.
metadata:
  author: odyssey4me
  version: "2.6.2"
  category: documentation
  tags: "wiki, pages, spaces"
  complexity: standard
license: MIT
---

# Confluence

Interact with Confluence for content search, viewing pages, and space management.

> **Creating/Updating Content?** See [references/creating-content.md](references/creating-content.md) for page creation and updates with Markdown.

## Network access

Confluence API commands require outbound HTTPS to the configured Confluence host. Remote operations require outbound network access. If the agent environment restricts it, obtain access through that environment's approval or network controls before the first remote command, reusing authorization already granted. Local help and file processing do not need network access. Skill instructions do not grant network permission. Report DNS, connection, and timeout failures as network errors; do not reset credentials to resolve them. If approved access also fails, stop and report it. Authentication and permission errors require user action.

## Resolving script paths

`SKILL_DIR` in the examples is the directory containing this loaded `SKILL.md`.
Set it to that absolute path before running commands; do not assume the agent
sets this shell variable. Quote the script path if it contains spaces.

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

Optionally configure defaults in `~/.config/agent-skills/confluence.yaml`:

```yaml
url: https://yourcompany.atlassian.net/wiki
email: you@example.com
token: your-token
defaults:
  cql_scope: "space = DEMO"
  max_results: 25
  default_space: "DEMO"
```

View configuration: `$SKILL_DIR/scripts/confluence.py config show`

## Commands

See [permissions.md](references/permissions.md) for read/write classification of each command.

### check

See [Setup Verification](#setup-verification) for dependency, authentication, and connectivity checks.

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

**Output**: Page metadata and content as Markdown. Images are downloaded to a sibling directory when using `--output`/`-o`.

**Arguments:**
- `page_identifier`: Page ID or title (required)
- `--markdown`: Output body as Markdown (default)
- `--raw`: Output in original format
- `--no-body`: Don't include body content
- `--frontmatter`: Output as markdown with YAML frontmatter (title, space, labels, parent) for round-tripping with `page create`/`page update`
- `--output`/`-o`: Write output to file; images are downloaded to a sibling directory named after the file stem

### page history

Show version history for a page.

```bash
# By title
$SKILL_DIR/scripts/confluence.py page history "My Page Title"

# By ID, limit results
$SKILL_DIR/scripts/confluence.py page history 123456 --max-results 10
```

**Arguments:**
- `page_identifier`: Page ID or title (required)
- `--max-results`: Maximum versions to return (default: 25)

### page create / update

Read [references/creating-content.md](references/creating-content.md) when creating or
updating pages for Markdown, images, frontmatter, table of contents, and internal links.

```bash
$SKILL_DIR/scripts/confluence.py page create --space DEMO --title "Documentation" \
  --body-file README.md
$SKILL_DIR/scripts/confluence.py page update 123456 --body-file updated.md
```

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

See the [Confluence CQL documentation](https://support.atlassian.com/confluence-cloud/articles/advanced-searching-using-cql/) for full CQL syntax.

Common patterns: `type=page`, `space=KEY`, `title~text`, `text~keyword`, `created >= now("-7d")`, `label=name`.

Combine with `AND`, `OR`, and `ORDER BY`:
```bash
$SKILL_DIR/scripts/confluence.py search "type=page AND space=DEMO ORDER BY created DESC"
```

## Examples

Use the examples under [search](#search), [page get](#page-get), and
[space](#space) for common read operations. For page creation, updates, and
batch workflows, see [Creating Content](references/creating-content.md#advanced-examples).

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

