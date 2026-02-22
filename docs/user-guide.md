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

Agent skills work with [multiple AI coding assistants](https://github.com/vercel-labs/add-skill#supported-agents) through the [Agent Skills specification](https://agentskills.io/specification). When you install skills using `npx add-skill`, they're automatically configured for your AI agent:

**Supported AI Agents:**
- Claude Code, Cursor, Continue.dev, GitHub Copilot, OpenCode, Gemini CLI, Command Code, and [more](https://github.com/vercel-labs/add-skill#supported-agents)

**Agent-Specific Installation:**
```bash
# Install for specific agent (optional, auto-detects by default)
npx add-skill odyssey4me/agent-skills --skill gitlab -a cursor

# Install for multiple agents
npx add-skill odyssey4me/agent-skills --skill gitlab -a claude-code -a cursor
```

The examples in this guide use Claude Code, but the same natural language patterns and commands work across all supported AI agents.

## Installation

### Option 1: Using npx add-skill (Recommended)

The fastest way to install skills is using the official `add-skill` CLI tool:

```bash
# Install a specific skill
npx add-skill odyssey4me/agent-skills --skill jira

# Install multiple skills
npx add-skill odyssey4me/agent-skills --skill google-docs --skill google-sheets
```

This will:
- Download the skills from GitHub
- Install them to `~/.claude/skills/`
- Make them available to your AI coding assistant automatically

Learn more: [add-skill CLI documentation](https://github.com/vercel-labs/add-skill)

### Option 2: Manual Installation

If you prefer manual installation or need to customize the setup:

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

3. **Verify the installation**:
   ```bash
   ls ~/.claude/skills/jira
   # Should show: SKILL.md  scripts/  references/
   ```

### Option 3: Development Installation

For contributors or developers who want to modify skills:

```bash
# Clone the repository
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills

# Install development dependencies
pip install -e ".[dev]"

# Skills are now available in skills/ directory
# You can use them directly or symlink to ~/.claude/skills/
```

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
- **URL**: Your Confluence instance URL
  - Cloud: `https://yourcompany.atlassian.net/wiki`
  - Data Center/Server: `https://confluence.yourcompany.com`
- **Email**: Your account email (Cloud) or username (DC/Server)
- **API Token**: Same as Jira for Cloud; from Confluence profile for DC/Server

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
3. Verify with `python ~/.claude/skills/gmail/scripts/gmail.py check`

On first run, your browser opens for OAuth authorization. After granting access, tokens are stored securely in your system keyring.

### Verify Authentication

Each skill includes a `check` command to verify setup:

```bash
# Check Jira configuration
python ~/.claude/skills/jira/scripts/jira.py check

# Check Confluence configuration
python ~/.claude/skills/confluence/scripts/confluence.py check

# Check Gmail configuration
python ~/.claude/skills/gmail/scripts/gmail.py check

# Check Google Drive configuration
python ~/.claude/skills/google-drive/scripts/google-drive.py check
```

The check command will:
- Verify Python dependencies are installed
- Check authentication is configured
- Test connectivity to the service
- Provide specific instructions if anything is missing

## Using Skills

Once installed and configured, skills are automatically available to your AI coding assistant.

Skills work with [multiple AI coding assistants](https://github.com/vercel-labs/add-skill#supported-agents). The examples below use Claude Code, but the same patterns apply to other agents like Cursor, Continue.dev, and GitHub Copilot.

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

Add these guidelines to your project's `AGENTS.md` (or equivalent agent instructions file) to ensure agents use skills correctly:

1. **Always invoke skills via the Skill tool** — don't bypass them with direct CLI calls to underlying scripts. The Skill tool loads the skill's SKILL.md which documents defaults, conventions, and correct usage.

2. **Trust skill defaults** — don't add post-processing, format flags, or output transformations unless there's a specific reason. Skills default to markdown output; use it as-is.

3. **Subagents follow the same rules** — when spawning agents via the Task tool, instruct them to use skills by name (e.g. "Use the gmail skill to search for..."). The agent will invoke the Skill tool, which loads the correct documentation and conventions. Agents should not construct raw API calls or CLI commands that replicate what a skill already provides.

4. **Describe what, not how** — tell agents what information to gather, not which commands to run. The skills evolve independently; hardcoding their implementation details creates coupling that breaks when skills change.

### Skill-Specific Commands

You can also invoke skills directly with specific commands. See individual skill documentation:

- [Jira Skill Documentation](../skills/jira/SKILL.md)
- [Confluence Skill Documentation](../skills/confluence/SKILL.md)
- [Gmail Skill Documentation](../skills/gmail/SKILL.md)
- [Google Drive Skill Documentation](../skills/google-drive/SKILL.md)

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
4. For Data Center/Server, verify your username and password/token

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

1. Verify skills are in the correct location (or your agent's skill directory if using a different AI assistant):
   ```bash
   ls ~/.claude/skills/
   ```

2. Check that SKILL.md has YAML frontmatter:
   ```bash
   head ~/.claude/skills/jira/SKILL.md
   ```
   Should start with `---` and include `name` and `description` fields

3. Restart Claude Code after installing new skills

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

Each skill provides comprehensive help:

```bash
# Jira help
python ~/.claude/skills/jira/scripts/jira.py --help
python ~/.claude/skills/jira/scripts/jira.py search --help

# Confluence help
python ~/.claude/skills/confluence/scripts/confluence.py --help
python ~/.claude/skills/confluence/scripts/confluence.py search --help

# Google Drive help
python ~/.claude/skills/google-drive/scripts/google-drive.py --help
python ~/.claude/skills/google-drive/scripts/google-drive.py files --help
```

### Documentation

**Skill Documentation:**
- **Jira**: See [skills/jira/SKILL.md](../skills/jira/SKILL.md)
- **Confluence**: See [skills/confluence/SKILL.md](../skills/confluence/SKILL.md)
- **Gmail**: See [skills/gmail/SKILL.md](../skills/gmail/SKILL.md)
- **Google Drive**: See [skills/google-drive/SKILL.md](../skills/google-drive/SKILL.md)
- **Google Calendar**: See [skills/google-calendar/SKILL.md](../skills/google-calendar/SKILL.md)

**Setup Guides:**
- **GCP Project Setup**: See [gcp-project-setup.md](gcp-project-setup.md) - Create GCP project for Google skills
- **Google OAuth Setup**: See [google-oauth-setup.md](google-oauth-setup.md) - Configure OAuth for all Google skills

**Reference Guides:**
- **ScriptRunner (Jira)**: See [skills/jira/references/scriptrunner.md](../skills/jira/references/scriptrunner.md)
- **Content Creation (Confluence)**: See [skills/confluence/references/creating-content.md](../skills/confluence/references/creating-content.md)
- **Gmail Search Queries**: See [skills/gmail/references/gmail-queries.md](../skills/gmail/references/gmail-queries.md)
- **Google Drive Search Queries**: See [skills/google-drive/references/drive-queries.md](../skills/google-drive/references/drive-queries.md)

### Reporting Issues

Found a bug or have a feature request? [Open an issue on GitHub](https://github.com/odyssey4me/agent-skills/issues).

## References

- [Agent Skills Specification](https://agentskills.io/specification) - Official standard
- [add-skill CLI](https://github.com/vercel-labs/add-skill) - Installation tool
- [Vercel agent-skills](https://github.com/vercel-labs/agent-skills) - Reference implementation
- [Anthropic skills](https://github.com/anthropics/skills) - Additional examples

## Next Steps

- **Configure authentication** for the skills you want to use
- **Run the check command** to verify everything works
- **Try natural language** to invoke skills with Claude Code
- **Read skill documentation** for advanced features and examples

For developers interested in creating skills, see the [Developer Guide](developer-guide.md).
