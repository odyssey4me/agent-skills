# Agent Skills

Portable skills for Claude Code providing integrations with Jira, Confluence, and other development tools.

## Features

- **Self-Contained**: Each skill is a single Python script - no framework dependencies
- **Claude Code Native**: Designed specifically for [Claude Code](https://claude.com/claude-code)
- **Simple Installation**: Just Python + 3 packages (`requests`, `keyring`, `pyyaml`)
- **Built-in Validation**: Each skill includes a `check` command for setup verification
- **Secure Authentication**: Supports system keyring, environment variables, and config files

> **Note**: Currently focused on Claude Code. Support for other AI agents (Cursor, Continue.dev, etc.) is planned for future releases. See [TODO.md](TODO.md) for roadmap.

## Quick Start

### Installation (Recommended)

Install skills using the official `add-skill` CLI:

```bash
# Install all skills
npx add-skill odyssey4me/agent-skills

# Or install individual skills
npx add-skill odyssey4me/agent-skills --skill jira
npx add-skill odyssey4me/agent-skills --skill confluence

# Or install multiple specific skills
npx add-skill odyssey4me/agent-skills --skill jira --skill confluence
```

This automatically:
- Downloads skills to `~/.claude/skills/`
- Makes them available to Claude Code
- Handles all setup

### Next Steps

After installation:

1. **Configure authentication** - See skill documentation for setup:
   - [Jira SKILL.md](skills/jira/SKILL.md) - Jira authentication and usage
   - [Confluence SKILL.md](skills/confluence/SKILL.md) - Confluence authentication and usage

2. **Verify setup** - Each skill includes a `check` command to validate configuration

3. **Start using** - Describe your needs naturally to Claude Code, or see skill docs for specific commands

For comprehensive setup instructions, see the [User Guide](docs/user-guide.md).

### For Developers

Want to contribute or modify skills? See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## Available Skills

| Skill | Description |
|-------|-------------|
| [Jira](skills/jira/SKILL.md) | Issue tracking, search, create/update, transitions |
| [Confluence](skills/confluence/SKILL.md) | Content management, page CRUD with Markdown support, CQL search |

See [TODO.md](TODO.md) for planned skills.

**Installation**: Use `npx add-skill odyssey4me/agent-skills` to install all skills, or see individual SKILL.md files for details. Manual downloads available from [Releases](https://github.com/odyssey4me/agent-skills/releases).

## Why Skills?

Skills provide a simple, transparent approach to extending Claude Code:

- **Simple**: No server process or protocol configuration required
- **Transparent**: Self-contained Python scripts you can read and modify
- **Self-Validating**: Built-in `check` command diagnoses setup issues
- **Portable**: Compatible with the [Agent Skills specification](https://agentskills.io/specification)

This repository follows the Agent Skills spec, ensuring compatibility with `npx add-skill` and other standard tooling.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Documentation

### For Users
- **[User Guide](docs/user-guide.md)** - Installation, setup, usage, and troubleshooting
- Individual skill documentation:
  - [Jira SKILL.md](skills/jira/SKILL.md)
  - [Confluence SKILL.md](skills/confluence/SKILL.md)

### For Developers
- **[Developer Guide](docs/developer-guide.md)** - Architecture, creating skills, testing, and contributing
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines and code standards
- [AGENTS.md](AGENTS.md) - Instructions for AI coding assistants working with this repo

### Migration
- **[Migration Guide](docs/migration.md)** - Upgrade guide from v0.1.x to v0.2.0

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
