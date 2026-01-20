# Agent Skills

Portable skills for AI coding assistants providing integrations with Jira and other development tools.

## Features

- **Self-Contained**: Each skill is a single Python script - no framework dependencies
- **Multi-Agent Support**: Works with Claude Code, OpenAI Codex, Gemini CLI, Cursor, Continue.dev, GitHub Copilot
- **Simple Installation**: Just Python + 3 packages (`requests`, `keyring`, `pyyaml`)
- **Built-in Validation**: Each skill includes a `check` command for setup verification
- **Secure Authentication**: Supports system keyring, environment variables, and config files

## Quick Start

### For Users

1. **Install Python dependencies**:
   ```bash
   pip install --user requests keyring pyyaml
   ```

2. **Download a skill** from [Releases](https://github.com/odyssey4me/agent-skills/releases):
   ```bash
   mkdir -p ~/.claude/skills
   cd ~/.claude/skills
   curl -L https://github.com/odyssey4me/agent-skills/releases/latest/download/jira.tar.gz | tar xz
   ```

3. **Configure authentication**:
   ```bash
   export JIRA_BASE_URL="https://yourcompany.atlassian.net"
   export JIRA_EMAIL="you@example.com"
   export JIRA_API_TOKEN="your-token"
   ```

4. **Verify setup**:
   ```bash
   python ~/.claude/skills/jira/jira.py check
   ```

5. **Use it**:
   ```bash
   python ~/.claude/skills/jira/jira.py search "project = DEMO"
   ```

### For Developers

```bash
# Clone repository
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills

# Install development dependencies
pip install -e ".[dev]"

# Test a skill
python skills/jira/jira.py check

# Run tests
pytest

# Lint
ruff check .
```

## Available Skills

| Skill | Description | Download |
|-------|-------------|----------|
| [Jira](skills/jira/SKILL.md) | Issue tracking, search, create/update, transitions | [jira.tar.gz](https://github.com/odyssey4me/agent-skills/releases/latest/download/jira.tar.gz) |

See [TODO.md](TODO.md) for planned skills.

## Project Structure

```
agent-skills/
├── skills/              # Individual skills (self-contained)
│   └── jira/
│       ├── SKILL.md     # Documentation
│       └── jira.py      # Self-contained script
├── templates/           # Templates for new skills
├── scripts/             # Optional setup utilities
├── tests/               # Tests
└── docs/                # Documentation
```

Each skill is self-contained - no dependencies on shared code.

## Why Skills Over MCP Servers?

Skills offer advantages over MCP servers:

1. **Portability**: Work across multiple agents without modification
2. **Simplicity**: No server process or protocol configuration
3. **Transparency**: Single Python file - you can read and modify it
4. **Self-Validating**: Built-in `check` command diagnoses setup issues

See [docs/skills-vs-mcp.md](docs/skills-vs-mcp.md) for details.

## Creating a New Skill

1. **Copy template**:
   ```bash
   cp -r templates/api-skill skills/myskill
   ```

2. **Edit the script**:
   - Rename `skill.py.template` to `myskill.py`
   - Implement your functionality
   - Include a `check` subcommand for validation

3. **Update documentation**:
   - Edit `SKILL.md` with usage instructions
   - Document authentication requirements
   - Add examples

4. **Test**:
   ```bash
   python skills/myskill/myskill.py --help
   python skills/myskill/myskill.py check
   ```

5. **Package for release**:
   ```bash
   cd skills
   tar czf myskill.tar.gz myskill/
   ```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Development

### Setup

```bash
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills

# Install dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Lint code
ruff check .

# Format code
ruff format .
```

### Skill Development Guidelines

1. **Self-contained**: No imports from shared code or other skills
2. **Single file**: All functionality in one script with subcommands
3. **Dependencies**: Only use `requests`, `keyring`, `pyyaml`, stdlib
4. **Authentication**: Support keyring, env vars, and config files
5. **CLI**: Use `argparse` with subcommands (like `git`, `docker`)
6. **Validation**: Include a `check` subcommand for setup verification
7. **Help**: Provide good `--help` output for all commands

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Documentation

- [docs/installation.md](docs/installation.md) - Installation and agent configuration
- [AGENTS.md](AGENTS.md) - Instructions for AI coding assistants
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development and contribution guidelines
- [docs/skills-vs-mcp.md](docs/skills-vs-mcp.md) - Skills vs MCP comparison

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
