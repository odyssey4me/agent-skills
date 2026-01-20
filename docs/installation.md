# Installation

This guide explains how to install agent-skills for use across all your projects.

## Quick Setup

Use the install helper script to automate setup:

```bash
# Clone to standard location
git clone https://github.com/odyssey4me/agent-skills.git ~/.local/share/agent-skills
cd ~/.local/share/agent-skills

# Run setup with all agent configs (dry-run first to preview)
python3 -m venv .venv && source .venv/bin/activate && pip install -e .
python scripts/install.py setup --all-agents --dry-run

# Apply changes
python scripts/install.py setup --all-agents

# Configure authentication
python scripts/install.py setup --auth jira
```

Or configure specific agents only:

```bash
python scripts/install.py setup --agents claude,gemini
```

Check your installation status:

```bash
python scripts/install.py check
```

## Manual Setup

If you prefer to set things up manually, follow the sections below.

## Clone the Repository

### Option 1: Standard Location (Recommended)

Clone to `~/.local/share/agent-skills`, following the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/) which defines `~/.local/share` as the standard location for user-specific data files on Linux systems. This keeps your home directory organized and follows established conventions.

```bash
git clone https://github.com/odyssey4me/agent-skills.git ~/.local/share/agent-skills
cd ~/.local/share/agent-skills

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Configure authentication
python scripts/setup_auth.py jira
```

### Option 2: Custom Location with Path File

If you prefer a different location, create a path pointer file:

```bash
# Clone wherever you prefer
git clone https://github.com/odyssey4me/agent-skills.git ~/code/agent-skills

# Create pointer file
mkdir -p ~/.config/agent-skills
echo "$HOME/code/agent-skills" > ~/.config/agent-skills/path

# Set up as usual
cd ~/code/agent-skills
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Scripts can then locate the installation:

```bash
SKILLS_PATH="${AGENT_SKILLS_PATH:-$(cat ~/.config/agent-skills/path 2>/dev/null || echo ~/.local/share/agent-skills)}"
```

## Agent Configuration

**Important**: `~/.local/share/agent-skills` is NOT automatically discovered by AI coding tools. You must configure each agent to use the skills as described below.

Each agent has different mechanisms for loading instructions from your home directory:

### Claude Code

[Claude Code](https://claude.com/claude-code) automatically loads `CLAUDE.md` files from multiple locations in a hierarchy. The global configuration at `~/.claude/CLAUDE.md` applies to all your projects. See the [Claude Code settings documentation](https://code.claude.com/docs/en/settings) and [CLAUDE.md guide](https://www.builder.io/blog/claude-md-guide) for complete details.

**Create `~/.claude/CLAUDE.md` for global configuration:**

```markdown title="~/.claude/CLAUDE.md"
--8<-- "docs/config-samples/.claude/CLAUDE.md.sample"
```

**Note**: The filename must be exactly `CLAUDE.md` (case-sensitive). Claude Code looks for this file in:
1. `~/.claude/CLAUDE.md` - Global configuration (recommended for skills)
2. Project root where you run `claude` - Project-specific settings
3. Parent and child directories (loaded hierarchically)

[Download sample file](config-samples/.claude/CLAUDE.md.sample)

### OpenAI Codex

[OpenAI Codex](https://developers.openai.com/codex/) is a VS Code extension that provides an AI coding agent. See the [Codex quickstart](https://developers.openai.com/codex/quickstart/) for installation and the [IDE documentation](https://developers.openai.com/codex/ide/) for details.

**Configure via VS Code settings** (`Ctrl+,` or `Cmd+,`):

Add to your user or workspace `settings.json`:

```json title=".vscode/settings.json or User Settings"
--8<-- "docs/config-samples/.vscode/codex-settings.json.sample"
```

**Requirements:**
- ChatGPT Plus, Pro, Business, Edu, or Enterprise plan
- Install the [Codex VS Code extension](https://marketplace.visualstudio.com/items?itemName=openai.chatgpt)
- Sign in with your ChatGPT account or API key

[Download sample file](config-samples/.vscode/codex-settings.json.sample)

### Gemini CLI

[Gemini CLI](https://ai.google.dev/gemini-api/docs/cli) uses `@` syntax to include files. See the [Gemini API documentation](https://ai.google.dev/gemini-api/docs) for more details. Reference skills directly in your prompts:

```
@~/.local/share/agent-skills/skills/jira/SKILL.md

Search for my open issues in PROJECT
```

**For persistent configuration**, create `~/.gemini/GEMINI.md`:

```markdown title="~/.gemini/GEMINI.md"
--8<-- "docs/config-samples/.gemini/GEMINI.md.sample"
```

[Download sample file](config-samples/.gemini/GEMINI.md.sample)

### Cursor

[Cursor](https://www.cursor.com/) supports global rules that you must manually configure. See the [Cursor Rules documentation](https://docs.cursor.com/context/rules-for-ai) for complete details.

**Option 1: Global Rules (Recommended for 2026)**

In Cursor, go to **Settings** > **General** > **Rules for AI** and add global rules that apply to all projects:

```json title="Cursor Settings > Rules for AI"
--8<-- "docs/config-samples/cursor-global-rules.json.sample"
```

**Option 2: Project Rules (Modern .mdc Format)**

For project-specific configuration, create `.cursor/rules/agent-skills.mdc` in your project root:

```markdown title=".cursor/rules/agent-skills.mdc"
--8<-- "docs/config-samples/.cursor/rules/agent-skills.mdc.sample"
```

**Note**: Cursor does NOT automatically discover configuration files. You must manually add rules through the settings UI or create `.mdc` files in your project's `.cursor/rules/` directory.

**Download sample files:**
- [Project rules (.mdc)](config-samples/.cursor/rules/agent-skills.mdc.sample)
- [Global settings (JSON)](config-samples/cursor-global-rules.json.sample)

### Continue.dev

[Continue.dev](https://www.continue.dev/) uses `~/.continue/config.json` for global configuration. This file is automatically created when you first run Continue. See the [Continue configuration guide](https://docs.continue.dev/customize/deep-dives/configuration) and [config.json reference](https://docs.continue.dev/reference/config) for complete details.

**Edit `~/.continue/config.json` to add custom slash commands:**

```json title="~/.continue/config.json"
--8<-- "docs/config-samples/.continue/config.json.sample"
```

**Location on different platforms:**
- **MacOS/Linux**: `~/.continue/config.json`
- **Windows**: `C:\Users\[username]\.continue\config.json`

[Download sample file](config-samples/.continue/config.json.sample)

### GitHub Copilot

[GitHub Copilot](https://github.com/features/copilot) reads `.github/copilot-instructions.md` per-repository only. See the [GitHub Copilot documentation](https://docs.github.com/en/copilot) for more details. For cross-project usage, you have two options:

**Option 1: Shell Alias**

Create an alias to copy instructions to new projects:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias copilot-skills='mkdir -p .github && cp ~/.local/share/agent-skills/.github/copilot-instructions.md .github/'
```

**Option 2: Git Template**

Set up a git template that includes the instructions:

```bash
mkdir -p ~/.git-templates/template/.github
cat > ~/.git-templates/template/.github/copilot-instructions.md << 'EOF'
# GitHub Copilot Instructions

Agent skills available at ~/.local/share/agent-skills

Refer to ~/.local/share/agent-skills/AGENTS.md for skill usage.
EOF

git config --global init.templateDir ~/.git-templates/template
```

New repositories created with `git init` will include the instructions file.

**Sample configuration files:**
- [Repository template](../.github/copilot-instructions.md) - Used in this repo
- [Download sample](config-samples/.github/copilot-instructions.md) - Standalone example

## Authentication

Authentication uses the system keyring, which is already system-wide. Configure once:

```bash
cd ~/.local/share/agent-skills
source .venv/bin/activate
python scripts/setup_auth.py jira
```

Credentials are available to all projects.

## Running Scripts

When running skill scripts from other directories, use the full path:

```bash
# Option 1: Full path with venv activation
(cd ~/.local/share/agent-skills && source .venv/bin/activate && python skills/jira/scripts/search.py "project = DEMO")

# Option 2: Create shell function (add to ~/.bashrc or ~/.zshrc)
agent-skills() {
    (cd ~/.local/share/agent-skills && source .venv/bin/activate && python "$@")
}

# Then use:
agent-skills skills/jira/scripts/search.py "project = DEMO"
```

## Updating

Pull updates from the repository:

```bash
cd ~/.local/share/agent-skills
git pull
source .venv/bin/activate
pip install -e .  # In case dependencies changed
```

## Verifying Setup

Use the install script to check your setup:

```bash
cd ~/.local/share/agent-skills
source .venv/bin/activate
python scripts/install.py check
```

This will show:
- Installation location status
- Virtual environment and dependencies
- Which agent configs are set up
- Authentication status for each service

For manual verification:

```bash
# Validate skills
python scripts/validate_skill.py skills/*

# Test Jira (if configured)
python skills/jira/scripts/search.py "project = YOUR_PROJECT ORDER BY created DESC" --limit 1
```

## Troubleshooting

### Issue: Agent can't find skills

**Solution**: Verify the installation location and agent configuration:

```bash
# Check if skills are in the expected location
ls -la ~/.local/share/agent-skills/skills/

# For custom locations, verify the path pointer file exists
cat ~/.config/agent-skills/path
```

If you're having trouble, refer to your specific agent's documentation:
- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
- [OpenAI Codex documentation](https://developers.openai.com/codex/)
- [Gemini API documentation](https://ai.google.dev/gemini-api/docs)
- [Cursor documentation](https://docs.cursor.com/)
- [Continue.dev documentation](https://docs.continue.dev/)
- [GitHub Copilot documentation](https://docs.github.com/en/copilot)

### Issue: Python dependencies not found

**Solution**: Ensure you've activated the virtual environment and installed dependencies:

```bash
cd ~/.local/share/agent-skills
source .venv/bin/activate  # Must be run before using skills
pip install -e .
```

### Issue: Authentication failing

**Solution**: Re-run the authentication setup:

```bash
cd ~/.local/share/agent-skills
source .venv/bin/activate
python scripts/setup_auth.py jira  # or your service name
```

Environment variables take precedence over keyring storage. Check if you have credentials in your environment:

```bash
env | grep -i jira
```

### Why ~/.local/share?

This project follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/), which defines standard locations for user files on Linux systems:

- `~/.local/share` - User-specific data files (like this project)
- `~/.config` - User-specific configuration files
- `~/.cache` - User-specific non-essential cache data

This keeps your home directory organized and follows the conventions used by modern Linux applications. For more information, see:
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/)
- [ArchWiki: XDG Base Directory](https://wiki.archlinux.org/title/XDG_Base_Directory)
```
