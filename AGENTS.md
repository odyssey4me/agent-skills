# Agent Skills

Instructions for AI coding assistants working with this repository.

## What This Repository Provides

Skills are portable integrations that work across multiple AI agents. Each skill provides:
- A `SKILL.md` file with instructions and commands
- Python scripts in `scripts/` for API interactions

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

Scripts are standalone Python files. Run from the repository root:
```bash
python skills/<skill>/scripts/<script>.py [arguments]
```

Example:
```bash
python skills/jira/scripts/search.py "project = DEMO"
python skills/jira/scripts/issue.py get DEMO-123
```

### Authentication

Skills use the system keyring for credentials. If a script fails with authentication errors, the user needs to run:
```bash
python scripts/setup_auth.py <service>
```

## Troubleshooting

### Authentication Errors

**"No credentials found for service"**
- Run: `python scripts/setup_auth.py <service>`
- Ensure the keyring service is available on your system

**"401 Unauthorized" or "403 Forbidden"**
- Credentials may be expired or invalid
- Re-run: `python scripts/setup_auth.py <service>`
- For Jira: verify the API token is still valid in Atlassian settings

### Script Errors

**"ModuleNotFoundError: No module named 'shared'"**
- Run from repository root, not from within skill directory
- Ensure venv is activated: `source .venv/bin/activate`

**"Connection refused" or timeout errors**
- Check network connectivity to the service
- Verify the service URL in your credentials

### Verification

Test that a skill is configured correctly:
```bash
# Jira: search for a known project
python skills/jira/scripts/search.py "project = <YOUR_PROJECT> ORDER BY created DESC" --limit 1
```

## Skill Format

Each skill follows this structure:

```
skills/<skill-name>/
├── SKILL.md      # Instructions, commands, examples
└── scripts/
    ├── __init__.py
    └── *.py      # Executable scripts
```

### SKILL.md Structure

```markdown
# <Skill Name>

<description>

## Authentication
<how to authenticate>

## Commands
### <command-name>
<usage>

## Examples
<examples>
```

## Development Guidelines

For code style, testing, and contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Why Skills Over MCP?

See [docs/skills-vs-mcp.md](docs/skills-vs-mcp.md) for the comparison.
