# Agent Skills

Instructions for AI coding assistants working with this repository.

## What This Repository Provides

Skills are portable, self-contained integrations that work across multiple AI agents. Each skill provides:
- A `SKILL.md` file with instructions and commands
- A single Python script with all functionality (e.g., `jira.py`)
- Built-in `check` command for setup verification

## Available Skills

| Skill | Location | Description |
|-------|----------|-------------|
| Jira | `skills/jira/` | Issue tracking, search, create/update, transitions |

See [TODO.md](TODO.md) for planned skills.

## Using Skills

### Reading Skill Documentation

To use a skill, read its `SKILL.md` file:
```
skills/<skill-name>/SKILL.md
```

### Running Skill Scripts

Each skill is a self-contained Python script. Run directly:
```bash
python skills/<skill>/<skill>.py [command] [arguments]
```

Examples:
```bash
python skills/jira/jira.py search "project = DEMO"
python skills/jira/jira.py issue get DEMO-123
python skills/jira/jira.py check  # Verify setup
```

### Verifying Setup

Every skill includes a `check` command to verify requirements:
```bash
python skills/jira/jira.py check
```

This validates:
- Python dependencies installed
- Authentication configured
- Service connectivity

If anything is missing, the check command provides setup instructions.

### Authentication

Skills support three authentication methods (checked in order):

1. **Environment variables** (recommended):
   ```bash
   export JIRA_BASE_URL="https://yourcompany.atlassian.net"
   export JIRA_EMAIL="you@example.com"
   export JIRA_API_TOKEN="your-token"
   ```

2. **Config file** (`~/.config/agent-skills/jira.yaml`):
   ```yaml
   jira:
     url: https://yourcompany.atlassian.net
     email: you@example.com
     token: your-token
   ```

## Troubleshooting

### Authentication Errors

**"No credentials found for service"** or **Missing authentication**
- Run the check command first: `python skills/jira/jira.py check`
- It will tell you exactly what's missing and how to configure it
- Set environment variables (see Authentication section above)
- Or create a config file at `~/.config/agent-skills/jira.yaml`

**"401 Unauthorized" or "403 Forbidden"**
- Credentials may be expired or invalid
- Verify authentication is correctly configured
- For Jira: verify the API token is still valid at https://id.atlassian.com/manage-profile/security/api-tokens

### Dependency Errors

**"ModuleNotFoundError: No module named 'requests'"** (or keyring, yaml)
- Install dependencies: `pip install --user requests keyring pyyaml`
- Or for development: `pip install -e ".[dev]"`

### Connection Errors

**"Connection refused" or timeout errors**
- Check network connectivity to the service
- Verify the service URL in your credentials
- Run the check command: `python skills/jira/jira.py check`

### Verification

Always start with the check command:
```bash
python skills/jira/jira.py check
```

It will diagnose all common issues and provide specific fix instructions.

## Skill Format

Each skill follows this structure:

```
skills/<skill-name>/
├── SKILL.md      # Instructions, commands, examples
└── <skill>.py    # Self-contained script with all functionality
```

### Skill Script Structure

Each skill is a single Python file with:
- Inlined authentication utilities (keyring, env vars, config files)
- Inlined HTTP utilities
- Inlined output formatting
- Multiple subcommands using argparse
- Built-in `check` command for validation

Example command structure:
```bash
python skills/jira/jira.py check                    # Verify setup
python skills/jira/jira.py search "JQL query"       # Search issues
python skills/jira/jira.py issue get DEMO-123       # Get issue
python skills/jira/jira.py issue create ...         # Create issue
python skills/jira/jira.py transitions list DEMO-123 # List transitions
```

### SKILL.md Structure

```markdown
# <Skill Name>

<description>

## Installation

How to install and set up the skill

## Setup Verification

How to run the check command

## Authentication

Authentication options and configuration

## Commands

### check
Verify setup

### command-name
<usage>

## Examples
<examples>
```

## Development Guidelines

For code style, testing, and contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Key Principles

1. **Self-contained**: No imports from shared code or other skills
2. **Single file**: All functionality in one script with subcommands
3. **Dependencies**: Only use `requests`, `keyring`, `pyyaml`, and stdlib
4. **Built-in validation**: Every skill has a `check` command
5. **Help text**: Comprehensive `--help` for all commands

## Why Skills Over MCP?

See [docs/skills-vs-mcp.md](docs/skills-vs-mcp.md) for the comparison.
