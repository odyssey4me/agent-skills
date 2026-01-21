# Confluence

Interact with Confluence for content search, viewing pages, and space management.

> **Creating/Updating Content?** See [CREATING_CONTENT.md](CREATING_CONTENT.md) for page creation and updates with Markdown.

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install --user requests keyring pyyaml
   ```

2. **Download the skill** from [Releases](https://github.com/odyssey4me/agent-skills/releases) or use directly from this repository.

## Setup Verification

After installation, verify the skill is properly configured:

```bash
python confluence.py check
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
python confluence.py config show

# Show space-specific defaults
python confluence.py config show --space DEMO
```

## Commands

### check

Verify configuration and connectivity.

```bash
python confluence.py check
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
python confluence.py search "type=page AND space = DEMO"
python confluence.py search "title~login" --space DEMO

# Filter by type
python confluence.py search "space = DEMO" --type page

# Limit results
python confluence.py search "type=page" --max-results 10

# JSON output
python confluence.py search "type=page" --json
```

**Arguments:**
- `cql`: CQL query string (required)
- `--max-results`: Maximum number of results (default: 50)
- `--type`: Content type filter (page, blogpost, comment)
- `--space`: Limit to specific space
- `--json`: Output as JSON

**See also**: [CQL Reference](#cql-reference) for query syntax

### page get

Get page content by ID or title.

```bash
# Get by title (returns Markdown by default)
python confluence.py page get "My Page Title"

# Get by ID
python confluence.py page get 123456

# Get without body content
python confluence.py page get "My Page" --no-body

# Get in original format (not Markdown)
python confluence.py page get "My Page" --raw

# JSON output
python confluence.py page get 123456 --json
```

**Output**: By default, displays page metadata and body content converted to Markdown for readability.

**Arguments:**
- `page_identifier`: Page ID or title (required)
- `--json`: Output as JSON
- `--markdown`: Output body as Markdown (default)
- `--raw`: Output in original format
- `--no-body`: Don't include body content

#### Example Output

```bash
$ python confluence.py page get "API Documentation"

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

For creating and updating pages with Markdown support, see [CREATING_CONTENT.md](CREATING_CONTENT.md).

Quick examples:
```bash
# Create page from Markdown file
python confluence.py page create --space DEMO --title "Documentation" \
  --body-file README.md

# Update page from file
python confluence.py page update 123456 --body-file updated.md
```

### space

Manage spaces.

```bash
# List all spaces
python confluence.py space list

# List with limit
python confluence.py space list --max-results 10

# Filter by type
python confluence.py space list --type global

# Get space details
python confluence.py space get DEMO

# JSON output
python confluence.py space list --json
```

**Arguments:**
- `list`: List spaces
  - `--type`: Filter by type (global, personal)
  - `--max-results`: Maximum results
  - `--json`: Output as JSON
- `get <space-key>`: Get space details
  - `--json`: Output as JSON

For creating spaces, see [CREATING_CONTENT.md](CREATING_CONTENT.md).

### config

Show configuration and defaults.

```bash
# Show all configuration
python confluence.py config show

# Show space-specific defaults
python confluence.py config show --space DEMO
```

This displays:
- Authentication settings (with masked token)
- Default CQL scope, max results, and default space
- Space-specific defaults for parent pages and labels

## Common Usage Examples

### Search for Pages

```bash
# Find pages in a space
python confluence.py search "type=page AND space = DEMO"

# Search by title
python confluence.py search "title~login"

# Find recent pages
python confluence.py search "type=page AND created >= now('-7d')"
```

### View Page Content

```bash
# View page as Markdown
python confluence.py page get "My Page Title"

# View page metadata only
python confluence.py page get 123456 --no-body

# Export to file
python confluence.py page get "My Page" > exported-page.md
```

### List and Explore Spaces

```bash
# List all spaces
python confluence.py space list

# Get details about a space
python confluence.py space get DEMO
```

### Using Configuration Defaults

With defaults configured as shown in the [Configuration Defaults](#configuration-defaults) section:

```bash
# Search uses CQL scope automatically
python confluence.py search "type=page"
# Becomes: (space = DEMO) AND (type=page)

# Search with automatic max_results from config
python confluence.py search "status=current"
# Uses configured max_results (25) automatically

# Override defaults when needed
python confluence.py search "type=page" --max-results 100
# CLI argument overrides the configured default of 25
```

### Search and Process Results

```bash
# Search and extract IDs
python confluence.py search "space=DEMO" --json | jq -r '.[] | .id'

# Count pages in a space
python confluence.py search "type=page AND space=DEMO" --max-results 1000 --json | jq '. | length'
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
python confluence.py search "type=page AND space=DEMO AND created >= now('-30d') ORDER BY created DESC"
```

## Troubleshooting

### Check command fails

Run `python confluence.py check` to diagnose issues. It will provide specific error messages and setup instructions.

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
- Exact title: `python confluence.py page get "Exact Page Title"`
- Page ID: `python confluence.py page get 123456`

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
