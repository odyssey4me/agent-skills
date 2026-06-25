# User Guide

Complete guide for installing and using agent skills with Claude Code and other AI assistants.

## What Are Agent Skills?

Agent skills are portable integrations that extend AI coding assistants with specialized capabilities. They follow the [Agent Skills specification](https://agentskills.io/specification), a standard for creating reusable, discoverable tools that work across different AI agents.

### How Skills Work

Skills implement the **progressive disclosure** principle:
1. AI agents initially see only the skill's `name` and `description` from YAML frontmatter
2. Full documentation loads only when the skill is activated
3. Additional references load on-demand
4. This minimizes context usage and improves performance

Learn more: [Progressive Disclosure in the Agent Skills Spec](https://agentskills.io/specification#progressive-disclosure)

### Multi-Agent Compatibility

Skills work with [multiple AI coding assistants](https://github.com/vercel-labs/skills#supported-agents) through the [Agent Skills specification](https://agentskills.io/specification). The `npx skills add` command auto-detects your installed agents, or you can target specific ones with the `-a` flag.

## Installation

### Option 1: Using the skills CLI (Recommended)

The [`skills` CLI](https://github.com/vercel-labs/skills) handles installation for all supported agents:

```bash
# Install a specific skill (auto-detects your agent)
npx skills add odyssey4me/agent-skills --skill jira

# Install multiple skills
npx skills add odyssey4me/agent-skills --skill google --skill confluence

# Target a specific agent
npx skills add odyssey4me/agent-skills --skill jira -a cursor

# Install globally (available across all projects)
npx skills add odyssey4me/agent-skills --skill jira -g
```

To update previously installed skills:

```bash
npx skills update
```

### Option 2: Manual Installation

Download a skill from [Releases](https://github.com/odyssey4me/agent-skills/releases) and extract it to your agent's skills directory:

| Agent | Global path |
|-------|------------|
| Claude Code | `~/.claude/skills/` |
| Cursor | `~/.cursor/skills/` |
| OpenCode | `~/.config/opencode/skills/` |
| Continue.dev | `~/.continue/skills/` |

```bash
mkdir -p ~/.claude/skills  # or your agent's path
cd ~/.claude/skills
curl -L https://github.com/odyssey4me/agent-skills/releases/latest/download/jira.tar.gz | tar xz
```

Python-based skills (jira, confluence) also need: `pip install --user requests keyring pyyaml`

### Option 3: Development Installation

For contributors or developers who want to modify skills, see the [Contributing Guide](../CONTRIBUTING.md#quick-start) for setup instructions.

## Authentication Setup

After installation, configure authentication for each skill you want to use.

### Jira Authentication

Jira requires:
- **Base URL**: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
- **Email**: Your Atlassian account email
- **API Token**: Create at [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

**Option 1: Environment Variables (Recommended)**

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="your-token"
```

Add these to your `~/.bashrc` or `~/.zshrc` for persistence.

**Option 2: Config File**

Create `~/.config/agent-skills/jira.yaml`:

```yaml
url: https://yourcompany.atlassian.net
email: you@example.com
token: your-token
```

### Confluence Authentication

Confluence requires:
- **URL**: Your Confluence Cloud URL (e.g., `https://yourcompany.atlassian.net`)
- **Email**: Your Atlassian account email
- **API Token**: Same as Jira — create at [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

**Option 1: Environment Variables (Recommended)**

```bash
export CONFLUENCE_URL="https://yourcompany.atlassian.net/wiki"
export CONFLUENCE_EMAIL="you@example.com"
export CONFLUENCE_API_TOKEN="your-token"
```

**Option 2: Config File**

Create `~/.config/agent-skills/confluence.yaml`:

```yaml
url: https://yourcompany.atlassian.net/wiki
email: you@example.com
token: your-token
```

### Google Skills Authentication (Gmail, Google Drive, Google Calendar, Google Docs, Google Sheets, Google Slides)

Google skills use OAuth 2.0 for authentication. A single Google Cloud Platform (GCP) project can be shared across all Google skills.

For complete setup instructions, see:
1. [GCP Project Setup Guide](gcp-project-setup.md) - Create project, enable APIs, configure OAuth consent screen
2. [Google OAuth Setup Guide](google-oauth-setup.md) - Configure credentials, authenticate, troubleshoot

**Quick Start:**

1. Set up a GCP project following the [GCP Project Setup Guide](gcp-project-setup.md)
2. Create `~/.config/agent-skills/google.yaml` with your OAuth credentials:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```
3. Verify with `python ~/.claude/skills/google/scripts/google.py check`

On first run, your browser opens for OAuth authorization. After granting access, tokens are stored securely in your system keyring.

### Verify Authentication

Each skill includes a `check` command to verify setup. Run it from your agent's skills directory:

```bash
python ~/.claude/skills/jira/scripts/jira.py check
python ~/.claude/skills/confluence/scripts/confluence.py check
python ~/.claude/skills/google/scripts/google.py check
```

The check command verifies dependencies, authentication, and service connectivity.

## Using Skills

Once installed and configured, skills are automatically available to your AI coding assistant.

Skills work with [multiple AI coding assistants](https://github.com/vercel-labs/skills#supported-agents). The examples below use Claude Code, but the same patterns apply to other agents like Cursor, Continue.dev, and GitHub Copilot.

### Natural Language Invocation

Simply describe what you want in natural language:

```
"Search Jira for my open issues"
"Create a bug in PROJECT about login failures"
"Find Confluence pages about authentication"
"Show me the Confluence page titled 'API Documentation'"
"List my unread emails from the last week"
"Send an email to user@example.com about the meeting"
"List my recent Google Drive files"
"Upload this file to Google Drive"
"Share the document with colleague@example.com"
```

Claude Code will automatically use the appropriate skill to fulfill your request.

### Best Practices for Agent Behaviour

Add these guidelines to your project's `CLAUDE.md` (or equivalent agent instructions file) to ensure agents use skills correctly:

1. **Always invoke skills via the Skill tool** — don't bypass them with direct CLI calls to underlying scripts. The Skill tool loads the skill's SKILL.md which documents defaults, conventions, and correct usage.

2. **Trust skill defaults** — don't add post-processing, format flags, or output transformations unless there's a specific reason. Skills default to markdown output; use it as-is.

3. **Subagents follow the same rules** — when spawning agents via the Task tool, instruct them to use skills by name (e.g. "Use the google skill to search for..."). The agent will invoke the Skill tool, which loads the correct documentation and conventions. Agents should not construct raw API calls or CLI commands that replicate what a skill already provides.

4. **Describe what, not how** — tell agents what information to gather, not which commands to run. The skills evolve independently; hardcoding their implementation details creates coupling that breaks when skills change.

### Permission Control

Each skill includes a `references/permissions.md` file that classifies its
commands as `read` or `write`. Agents should load this reference when invoking
a skill and use it to decide whether a command can run freely (`read`) or
needs user confirmation (`write`). This keeps permission logic agent-agnostic
— any agent can read the table and map it to its own permission system.

The permission reference can also be used to pre-configure agent permissions
so that read-only commands auto-execute without prompting. For example, an
agent orchestrator can parse each skill's `permissions.md`, collect all `read`
commands, and add them to its allow-list upfront — giving the agent
frictionless access to queries and lookups while still gating write operations
behind user confirmation.

### Skill-Specific Commands

You can also invoke skills directly with specific commands. See individual skill documentation in the [Available Skills](../README.md#available-skills) table.

## Troubleshooting

### Authentication Errors

**"No credentials found"** or **"Missing authentication"**

1. Run the check command first:
   ```bash
   python ~/.claude/skills/jira/scripts/jira.py check
   ```

2. The check command will tell you exactly what's missing

3. Configure authentication using environment variables or config file (see [Authentication Setup](#authentication-setup))

**"401 Unauthorized" or "403 Forbidden"**

1. Verify your API token is still valid
2. For Jira Cloud: Check tokens at [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
3. Ensure you're using your email (not username) for Cloud instances
4. Ensure you're using your email (not username) for Cloud instances

### Dependency Errors

**"ModuleNotFoundError: No module named 'requests'"**

Install required Python packages:
```bash
pip install --user requests keyring pyyaml
```

### Connection Errors

**"Connection refused" or timeout errors**

1. Check your network connectivity
2. Verify the service URL in your credentials
3. For corporate networks, check if you need a proxy
4. Run the check command to diagnose:
   ```bash
   python ~/.claude/skills/jira/scripts/jira.py check
   ```

### Permission Errors

**"You do not have permission"** or **"Resource not found"**

1. Verify you have access to the requested project/space/page
2. Contact your Jira/Confluence administrator if needed
3. Check that the project key or space key is correct

### Skills Not Appearing

1. Verify skills are in the correct location for your agent (see [Installation](#installation) for paths):
   ```bash
   ls ~/.claude/skills/  # Claude Code
   ls ~/.cursor/skills/  # Cursor
   ```

2. Check that SKILL.md has YAML frontmatter (starts with `---` and includes `name` and `description`)

3. Restart your AI agent after installing new skills

## Configuration Defaults

Both Jira and Confluence support configuration defaults to reduce repetitive typing.

### Jira Defaults

Add to `~/.config/agent-skills/jira.yaml`:

```yaml
# Optional defaults
defaults:
  jql_scope: "project = DEMO AND assignee = currentUser()"
  security_level: "Red Hat Internal"
  max_results: 25
  fields: ["summary", "status", "assignee", "priority", "created"]

# Optional project-specific defaults
projects:
  DEMO:
    issue_type: "Task"
    priority: "Medium"
```

### Confluence Defaults

Add to `~/.config/agent-skills/confluence.yaml`:

```yaml
# Optional defaults
defaults:
  cql_scope: "space = DEMO"
  max_results: 25
  default_space: "DEMO"
```

CLI arguments always override config defaults.

## Getting Help

### Skill-Specific Help

Python-based skills provide built-in help:

```bash
python ~/.claude/skills/jira/scripts/jira.py --help
python ~/.claude/skills/jira/scripts/jira.py search --help
```

### Documentation

- **Skill documentation**: See [Available Skills](../README.md#available-skills) for links to each skill's SKILL.md
- **GCP Project Setup**: See [gcp-project-setup.md](gcp-project-setup.md)
- **Google OAuth Setup**: See [google-oauth-setup.md](google-oauth-setup.md)

### Reporting Issues

Found a bug or have a feature request? [Open an issue on GitHub](https://github.com/odyssey4me/agent-skills/issues).

## References

- [Agent Skills Specification](https://agentskills.io/specification) - Official standard
- [skills CLI](https://github.com/vercel-labs/skills) - Installation tool
- [Vercel agent-skills](https://github.com/vercel-labs/agent-skills) - Reference implementation
- [Anthropic skills](https://github.com/anthropics/skills) - Additional examples

## Next Steps

- **Configure authentication** for the skills you want to use
- **Run the check command** to verify everything works
- **Try natural language** to invoke skills with Claude Code
- **Read skill documentation** for advanced features and examples

For developers interested in creating skills, see the [Developer Guide](developer-guide.md).
