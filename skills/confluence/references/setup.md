# Confluence Setup

This skill supports **Confluence Cloud only**. It authenticates with an
Atlassian account email and API token.

## Installation

**Dependencies**: `pip install --user requests keyring pyyaml`

## Setup Verification

After installation, verify the configuration by running:

```bash
$SKILL_DIR/scripts/confluence.py check
```

This checks:

- Python dependencies (requests, keyring, pyyaml)
- Authentication configuration
- Connectivity to Confluence Cloud

If anything is missing, the check command prints the setup steps.

## Authentication

Configure Confluence Cloud authentication using one of these methods.

### Option 1: Environment Variables (Recommended)

```bash
export CONFLUENCE_URL="https://yourcompany.atlassian.net"
export CONFLUENCE_EMAIL="you@example.com"
export CONFLUENCE_API_TOKEN="your-token"
```

Add these to your `~/.bashrc` or `~/.zshrc` for persistence.

### Option 2: Config File

Create `~/.config/agent-skills/confluence.yaml`:

```yaml
url: https://yourcompany.atlassian.net
email: you@example.com
token: your-token
```

### Required Credentials

- **URL**: Your Confluence Cloud site URL (for example
  `https://yourcompany.atlassian.net`). Do not include the `/wiki` path;
  the skill adds `/wiki/rest/api` to every request.
- **Email**: Your Atlassian account email
- **API Token**: Create at https://id.atlassian.com/manage-profile/security/api-tokens

Credentials can also be stored in the system keyring under `agent-skills`
as `confluence-url`, `confluence-email` and `confluence-token`.

## Configuration Defaults

Optionally configure defaults in `~/.config/agent-skills/confluence.yaml`:

```yaml
url: https://yourcompany.atlassian.net
email: you@example.com
token: your-token
defaults:
  cql_scope: "space = DEMO"
  max_results: 25
  default_space: "DEMO"
spaces:
  DEMO:
    default_parent: "123456"
    default_labels:
      - documentation
```

CLI arguments always override these defaults. View the resolved
configuration with:

```bash
$SKILL_DIR/scripts/confluence.py config show
```
