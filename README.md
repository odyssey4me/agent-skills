# Agent Skills

Portable skills for AI coding assistants providing integrations with Jira, Confluence, Gmail, Google Workspace (Docs, Sheets, Slides), GitHub, GitLab, Gerrit, and other development tools.

## Features

- **Self-Contained**: Each skill is a single Python script - no framework dependencies
- **Multi-Agent Compatible**: Works with [multiple AI coding assistants](https://github.com/vercel-labs/add-skill#supported-agents) including [Claude Code](https://claude.com/claude-code), Cursor, Continue.dev, and more
- **Simple Installation**: Just Python + 3 packages (`requests`, `keyring`, `pyyaml`)
- **Built-in Validation**: Each skill includes a `check` command for setup verification
- **Secure Authentication**: Supports system keyring, environment variables, and config files

## Quick Start

### Installation (Recommended)

Install skills using the official `add-skill` CLI:

```bash
# Install all skills
npx add-skill odyssey4me/agent-skills

# Or install a specific skill
npx add-skill odyssey4me/agent-skills --skill confluence

# Or install multiple specific skills
npx add-skill odyssey4me/agent-skills --skill gmail --skill google-calendar
```

This automatically:
- Downloads skills to `~/.claude/skills/`
- Makes them available to Claude Code
- Handles all setup

### Next Steps

After installation:

1. **Configure authentication** - See skill documentation for setup (links in [Available Skills](#available-skills) table below)

2. **Verify setup** - Each skill includes a `check` command to validate configuration

3. **Start using** - Describe your needs naturally to Claude Code, or see skill docs for specific commands

For comprehensive setup instructions, see the [User Guide](docs/user-guide.md).

### For Developers

Want to contribute or modify skills? See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## Available Skills

| Skill | Description |
|-------|-------------|
| [Code Review](skills/code-review/SKILL.md) | Review PRs, MRs, and Gerrit changes with focus on security, maintainability, and architectural fit |
| [Confluence](skills/confluence/SKILL.md) | Content management, page CRUD with Markdown support, CQL search |
| [Gerrit](skills/gerrit/SKILL.md) | Code review, submit changes, download patches via `git-review` CLI |
| [GitHub](skills/github/SKILL.md) | Issues, pull requests, workflows, and repositories via `gh` CLI |
| [GitLab](skills/gitlab/SKILL.md) | Issues, merge requests, pipelines, and repositories via `glab` CLI |
| [Gmail](skills/gmail/SKILL.md) | Email management, send/receive messages, drafts, labels |
| [Google Calendar](skills/google-calendar/SKILL.md) | Calendar management, event CRUD, availability checking, scheduling |
| [Google Docs](skills/google-docs/SKILL.md) | Document creation and editing, content management, formatting |
| [Google Drive](skills/google-drive/SKILL.md) | File management, list/search/upload/download files, folder management, sharing |
| [Google Sheets](skills/google-sheets/SKILL.md) | Spreadsheet management, cell values, formulas, sheets |
| [Google Slides](skills/google-slides/SKILL.md) | Presentation creation, slides, shapes, images, layouts |
| [Jira](skills/jira/SKILL.md) | Issue tracking, search, create/update, transitions |

Browse install counts and popularity on [skills.sh](https://skills.sh/odyssey4me/agent-skills). Skills are also available on the [Tessl Registry](https://tessl.io/registry/odyssey4me). See [TODO.md](TODO.md) for planned skills.

**Installation**: Use `npx add-skill odyssey4me/agent-skills` to install all skills, or see individual SKILL.md files for details. Manual downloads available from [Releases](https://github.com/odyssey4me/agent-skills/releases).

## Why Skills?

Skills provide a simple, transparent approach to extending Claude Code:

- **Simple**: No server process or protocol configuration required
- **Transparent**: Self-contained Python scripts you can read and modify
- **Self-Validating**: Built-in `check` command diagnoses setup issues
- **Portable**: Follows the [Agent Skills specification](https://agentskills.io/specification) for cross-agent compatibility

This repository follows the Agent Skills spec, ensuring compatibility with `npx add-skill` and other standard tooling.

## Supported AI Agents

These skills work with [multiple AI coding assistants](https://github.com/vercel-labs/add-skill#supported-agents) through the [Agent Skills specification](https://agentskills.io/specification), including:

- **Claude Code** - Anthropic's official CLI
- **Cursor** - AI-first code editor
- **Continue.dev** - Open-source AI coding assistant
- **GitHub Copilot** - GitHub's AI pair programmer
- **OpenCode**, **Gemini CLI**, **Command Code**, and more

See the [full list of supported agents](https://github.com/vercel-labs/add-skill#supported-agents). Installation via `npx add-skill` automatically configures skills for your AI agent.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Documentation

### For Users
- **[User Guide](docs/user-guide.md)** - Installation, setup, usage, and troubleshooting
- Individual skill documentation - see links in [Available Skills](#available-skills) table

### For Developers
- **[Developer Guide](docs/developer-guide.md)** - Architecture, creating skills, testing, and contributing
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines and code standards
- [AGENTS.md](AGENTS.md) - Instructions for AI coding assistants working with this repo

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
