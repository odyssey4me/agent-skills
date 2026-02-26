# agent-skills

Portable, self-contained Python scripts that give AI coding assistants (Claude Code, Cursor, Continue.dev, GitHub Copilot, etc.) the ability to interact with Jira and Confluence. Each skill is a single Python file with no framework dependencies. Skills are invoked as CLI commands by the AI agent.

## Package Information

- **Package Name**: agent-skills
- **Package Type**: pypi
- **Language**: Python 3.10+
- **Installation**: `pip install agent-skills` or `npx add-skill odyssey4me/agent-skills`
- **Runtime dependencies** (not included, must install separately): `pip install --user requests keyring pyyaml`

## Core Imports

Skills are self-contained CLI scripts, not Python library modules. They are invoked as subprocesses:

```bash
# Jira skill
python ~/.claude/skills/jira.py <command> [args]

# Confluence skill
python ~/.claude/skills/confluence.py <command> [args]
```

After `pip install agent-skills`, skill scripts are located at:
- `skills/jira/scripts/jira.py`
- `skills/confluence/scripts/confluence.py`

After `npx add-skill odyssey4me/agent-skills`, scripts are installed to `~/.claude/skills/`.

## Basic Usage

```bash
# Verify setup
python jira.py check
python confluence.py check

# Search Jira issues
python jira.py search "project = DEMO AND status = Open"

# Get a Jira issue
python jira.py issue get DEMO-123

# Search Confluence
python confluence.py search "type=page AND space=DEMO"

# Get a Confluence page
python confluence.py page get "My Page Title"
```

## Authentication

Both skills use the same credential priority order:

1. **System keyring** (highest priority)
2. **Environment variables**
3. **YAML config file** (`~/.config/agent-skills/{service}.yaml`)

### Jira Environment Variables

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="your-api-token"
# For Data Center/Server with basic auth:
# export JIRA_USERNAME="username"
# export JIRA_PASSWORD="password"
```

### Confluence Environment Variables

```bash
export CONFLUENCE_URL="https://yourcompany.atlassian.net/wiki"
export CONFLUENCE_EMAIL="you@example.com"
export CONFLUENCE_API_TOKEN="your-api-token"
# For Data Center/Server:
# export CONFLUENCE_USERNAME="username"
# export CONFLUENCE_PASSWORD="password"
```

## Deployment Auto-Detection

Both skills automatically detect Cloud vs. Data Center/Server and adapt API calls accordingly:

- **Jira Cloud**: API v3, email+token basic auth, ADF text format
- **Jira DC/Server**: API v2, Bearer token auth, plain text format
- **Confluence Cloud**: `/wiki/rest/api` base path, ADF editor format
- **Confluence DC/Server**: `/rest/api` base path, XHTML storage format

## Capabilities

### Jira Skill

Full Jira issue tracking integration with search, create, update, comment, and workflow transition support. Includes ScriptRunner Enhanced Search JQL functions when the plugin is installed.

```python { .api }
# CLI commands
python jira.py check
python jira.py search <jql> [--max-results N] [--fields f1,f2] [--json]
python jira.py issue get <issue_key> [--json]
python jira.py issue create --project P --summary S [--type T] [--description D] [--priority P] [--labels L] [--assignee A] [--json]
python jira.py issue update <issue_key> [--summary S] [--description D] [--priority P] [--labels L] [--assignee A]
python jira.py issue comment <issue_key> <body> [--security-level SL]
python jira.py transitions list <issue_key> [--json]
python jira.py transitions do <issue_key> <transition> [--comment C] [--security-level SL]
python jira.py config show [--project P]
```

[Jira Skill](./jira.md)

### Confluence Skill

Full Confluence content management with CQL search, page CRUD operations with Markdown support, and space management.

```python { .api }
# CLI commands
python confluence.py check
python confluence.py search <cql> [--max-results N] [--type T] [--space S] [--json]
python confluence.py page get <page_identifier> [--json] [--markdown] [--raw] [--no-body] [--expand fields]
python confluence.py page create --space S --title T [--body B] [--body-file F] [--format F] [--parent P] [--labels L] [--json]
python confluence.py page update <page_id> [--title T] [--body B] [--body-file F] [--format F] [--version V] [--json]
python confluence.py space list [--type T] [--max-results N] [--json]
python confluence.py space get <space_key> [--expand fields] [--json]
python confluence.py space create --key K --name N [--description D] [--type T] [--json]
python confluence.py config show [--space S]
```

[Confluence Skill](./confluence.md)

### Setup Helper

A utility script (`scripts/setup_helper.py`) that discovers installed skills and configures the AI agent's CLAUDE.md to reference them. Searches standard installation locations and generates/updates `~/.claude/CLAUDE.md`.

```python { .api }
python scripts/setup_helper.py [--skill-path PATH] [--claude-md PATH] [--show] [--dry-run] [--auto]
```

[Setup Helper](./setup-helper.md)

### Validate Skill

A utility script (`scripts/validate_skill.py`) that validates agent skill directory structure and requirements. Checks SKILL.md frontmatter, required sections, script structure, and coding standards.

```python { .api }
python scripts/validate_skill.py <skills...> [--strict]
```

[Validate Skill](./validate-skill.md)
