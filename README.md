# Agent Skills

A collection of portable skills for AI coding assistants providing integrations with Atlassian, Google Workspace, and code hosting platforms.

## Features

- **Multi-Agent Support**: Works with Claude Code, OpenAI Codex, Gemini CLI, Cursor, Continue.dev, GitHub Copilot
- **Secure Authentication**: Uses system keyring for credential storage
- **Portable**: Skills are markdown + Python scripts, no server required
- **Extensible**: Template-based skill creation

## Quick Start

### 1. Install the Repository

```bash
# Clone to standard location (~/.local/share follows XDG Base Directory spec)
git clone https://github.com/odyssey4me/agent-skills.git ~/.local/share/agent-skills
cd ~/.local/share/agent-skills

# Create and activate virtual environment (required)
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Your AI Tool

**Important**: Skills are NOT automatically discovered. You must configure your AI coding tool to use them.

See the [Installation Guide](docs/installation.md#agent-configuration) for complete setup instructions for:
- [Claude Code](docs/installation.md#claude-code) - Create `~/.claude/CLAUDE.md`
- [OpenAI Codex](docs/installation.md#openai-codex) - Use VS Code extension settings
- [Cursor](docs/installation.md#cursor) - Configure in Settings > Rules for AI
- [Continue.dev](docs/installation.md#continuedev) - Edit `~/.continue/config.json`
- [Gemini CLI](docs/installation.md#gemini-cli) - Use `@` syntax to reference skills
- [GitHub Copilot](docs/installation.md#github-copilot) - Copy `.github/copilot-instructions.md` per-project

### 3. Set Up Authentication (Optional)

For services that require authentication (like Jira):

```bash
cd ~/.local/share/agent-skills
source .venv/bin/activate
python scripts/setup_auth.py jira
```

Or use environment variables (see [Installation Guide](docs/installation.md#authentication) for details).

---

**Complete setup instructions**: See [docs/installation.md](docs/installation.md)

## Available Skills

| Skill | Description |
|-------|-------------|
| [Jira](skills/jira/SKILL.md) | Issue tracking, search, create/update, transitions |

See [TODO.md](TODO.md) for planned skills (Confluence, Google Workspace, GitHub, GitLab, Gerrit).

## Why Skills Over MCP Servers?

Skills offer advantages over MCP servers:

1. **Portability**: Work across multiple agents without modification
2. **Simplicity**: No server process or protocol configuration
3. **Transparency**: Readable markdown shows exactly what the agent does
4. **Context-Aware**: Load progressively based on relevance

See [docs/skills-vs-mcp.md](docs/skills-vs-mcp.md) for details.

## Development

All development uses a virtual environment for isolation from the host system.

```bash
# Create and activate venv (if not done)
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov

# Lint and format
ruff check .
ruff format .

# Validate skill structure
python scripts/validate_skill.py skills/*
```

## Creating a New Skill

```bash
# Copy template
cp -r templates/api-skill skills/my-skill

# Edit SKILL.md and implement scripts
# Add tests in tests/test_my_skill.py

# Validate
python scripts/validate_skill.py skills/my-skill
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Documentation

- [docs/installation.md](docs/installation.md) - Installation and agent configuration
- [AGENTS.md](AGENTS.md) - Instructions for AI coding assistants
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development and contribution guidelines
- [docs/skills-vs-mcp.md](docs/skills-vs-mcp.md) - Skills vs MCP comparison

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
