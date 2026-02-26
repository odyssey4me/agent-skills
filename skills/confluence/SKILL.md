---
name: confluence
description: Search and manage Confluence pages and spaces using CQL, read/create/update pages with Markdown support. Use when working with Confluence documentation.
metadata:
  author: odyssey4me
  version: "0.2.1"
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

After installation, verify the skill is properly configured:

```bash
$SKILL_DIR/scripts/confluence.py check
```

This will check:
- Python dependencies (requests, keyring, pyyaml)
- Authentication configuration
- Connectivity to Confluence
- Deployment type detection (Cloud vs Data Center/Server)

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

- **URL**: Your Confluence instance URL
  - Cloud: `https://yourcompany.atlassian.net/wiki`
  - DC/Server: `https://confluence.yourcompany.com`
- **Email**: Your account email (required for Cloud)
- **API Token**: Create at https://id.atlassian.com/manage-profile/security/api-tokens (Cloud) or from your Confluence profile (DC/Server)

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

### check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/confluence.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Confluence
- Deployment type (Cloud vs DC/Server) is detected correctly

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
```

**Output**: By default, displays page metadata and body content converted to Markdown for readability.

**Arguments:**
- `page_identifier`: Page ID or title (required)
- `--markdown`: Output body as Markdown (default)
- `--raw`: Output in original format
- `--no-body`: Don't include body content

#### Example Output

```bash
$ $SKILL_DIR/scripts/confluence.py page get "API Documentation"

Page ID: 123456
Title: API Documentation
Type: page
Space: DEMO
Status: current
Version: 1

---

# API Documentation

## Overview

This document describes our **REST API**.

## Endpoints

- `GET /api/users` - List users
- `POST /api/users` - Create user
```

### page create / update

For creating and updating pages with Markdown support, see [references/creating-content.md](references/creating-content.md).

Quick examples:
```bash
# Create page from Markdown file
$SKILL_DIR/scripts/confluence.py page create --space DEMO --title "Documentation" \
  --body-file README.md

# Update page from file
$SKILL_DIR/scripts/confluence.py page update 123456 --body-file updated.md
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

## Examples

### Search for Pages

```bash
# Find pages in a space
$SKILL_DIR/scripts/confluence.py search "type=page AND space = DEMO"

# Search by title
$SKILL_DIR/scripts/confluence.py search "title~login"

# Find recent pages
$SKILL_DIR/scripts/confluence.py search "type=page AND created >= now('-7d')"
```

### View Page Content

```bash
# View page as Markdown
$SKILL_DIR/scripts/confluence.py page get "My Page Title"

# View page metadata only
$SKILL_DIR/scripts/confluence.py page get 123456 --no-body

# Export to file
$SKILL_DIR/scripts/confluence.py page get "My Page" > exported-page.md
```

### List and Explore Spaces

```bash
# List all spaces
$SKILL_DIR/scripts/confluence.py space list

# Get details about a space
$SKILL_DIR/scripts/confluence.py space get DEMO
```

### Using Configuration Defaults

With defaults configured as shown in the [Configuration Defaults](#configuration-defaults) section:

```bash
# Search uses CQL scope automatically
$SKILL_DIR/scripts/confluence.py search "type=page"
# Becomes: (space = DEMO) AND (type=page)

# Search with automatic max_results from config
$SKILL_DIR/scripts/confluence.py search "status=current"
# Uses configured max_results (25) automatically

# Override defaults when needed
$SKILL_DIR/scripts/confluence.py search "type=page" --max-results 100
# CLI argument overrides the configured default of 25
```

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

## Troubleshooting

### Check command fails

Run `$SKILL_DIR/scripts/confluence.py check` to diagnose issues. It will provide specific error messages and setup instructions.

### Authentication failed

1. Verify your API token is correct
2. Ensure you're using your email (not username) for Cloud instances
3. For Cloud, use your Atlassian account email
4. For Data Center/Server, you may need username/password or Bearer token

### Permission denied

You may not have access to the requested space or page. Contact your Confluence administrator.

### CQL syntax error

Test your CQL query in the Confluence web interface search before using it in the CLI.

### Page not found

When searching by title, ensure the title is exact (case-sensitive). You can use:
- Exact title: `$SKILL_DIR/scripts/confluence.py page get "Exact Page Title"`
- Page ID: `$SKILL_DIR/scripts/confluence.py page get 123456`

### Import errors

Ensure dependencies are installed:
```bash
pip install --user requests keyring pyyaml
```

## Cloud vs Data Center/Server

The skill automatically detects your Confluence deployment type and adapts:

- **Cloud** (atlassian.net): Uses `/wiki/rest/api` and editor format (ADF)
- **Data Center/Server**: Uses `/rest/api` and storage format (XHTML)

When reading pages, content is automatically converted to Markdown for display regardless of deployment type.
