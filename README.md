# Agent Skills

Portable skills for AI coding assistants providing integrations with Jira, Confluence, Google Workspace, GitHub, GitLab, Gerrit, and other development tools.

## Features

- **Self-Contained**: Each skill is independently installable with no framework dependencies
- **Multi-Agent Compatible**: Works with [multiple AI coding assistants](https://github.com/vercel-labs/skills#supported-agents) via the [Agent Skills specification](https://agentskills.io/specification)
- **Simple Installation**: Just Python and a few pip packages
- **Built-in Validation**: Each skill includes a `check` command for setup verification
- **Secure Authentication**: Supports system keyring, environment variables, and config files

## Quick Start

Install skills using the official [`skills` CLI](https://github.com/vercel-labs/skills):

```bash
# Install all skills
npx skills add odyssey4me/agent-skills

# Or install specific skills
npx skills add odyssey4me/agent-skills --skill google --skill jira
```

After installation, configure authentication and verify setup — see the [User Guide](docs/user-guide.md) for details.

## Available Skills

| Skill | Description |
|-------|-------------|
| [Confluence](skills/confluence/SKILL.md) | Content management, page CRUD with Markdown support, CQL search |
| [Gerrit](skills/gerrit/SKILL.md) | Code review, submit changes, download patches via `git-review` CLI |
| [GitHub](skills/github/SKILL.md) | Issues, pull requests, workflows, and repositories via `gh` CLI |
| [GitLab](skills/gitlab/SKILL.md) | Issues, merge requests, pipelines, and repositories via `glab` CLI |
| [Google](skills/google/SKILL.md) | Google Workspace — Gmail, Calendar, Drive, Docs, Sheets, Slides via `gog` CLI |
| [Jira](skills/jira/SKILL.md) | Issue tracking, search, create/update, transitions |

Browse install counts on [skills.sh](https://skills.sh/odyssey4me/agent-skills). Manual downloads available from [Releases](https://github.com/odyssey4me/agent-skills/releases).

## Documentation

- **[User Guide](docs/user-guide.md)** — Installation, setup, usage, and troubleshooting
- **[Developer Guide](docs/developer-guide.md)** — Architecture, creating skills, testing
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Contribution guidelines
- **[TODO.md](TODO.md)** — Planned skills and features

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
