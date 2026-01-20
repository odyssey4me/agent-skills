# Installation

This guide explains how to install and use agent-skills with Claude Code.

> **Note**: Currently focused on Claude Code only. Support for other AI agents is planned for future releases. See [../TODO.md](../TODO.md) for roadmap.

## For Users

Skills are self-contained Python scripts. No virtual environment or package installation required.

### Quick Start

1. **Install Python dependencies** (user-space only):
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

   Add these to your `~/.bashrc` or `~/.zshrc` for persistence.

4. **Verify setup**:
   ```bash
   python ~/.claude/skills/jira/jira.py check
   ```

5. **Use it**:
   ```bash
   python ~/.claude/skills/jira/jira.py search "project = DEMO"
   ```

### Installation Locations

You can install skills anywhere. Common locations:

- `~/.claude/skills/` - For Claude Code
- `~/.local/share/agent-skills/skills/` - Following XDG Base Directory Specification
- `~/code/agent-skills/skills/` - Custom location

The location doesn't matter - just point your AI agent to the skill files.

## For Developers

Clone the repository to develop or contribute:

```bash
# Clone repository
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills

# Install development dependencies
pip install -e ".[dev]"

# Test a skill
python skills/jira/jira.py check
python skills/jira/jira.py search "project = DEMO"

# Run tests
pytest

# Lint
ruff check .
```

## Claude Code Configuration

[Claude Code](https://claude.com/claude-code) automatically loads `CLAUDE.md` files. Create `~/.claude/CLAUDE.md` for global configuration:

```markdown
# Global Agent Skills

Skills are available at ~/.claude/skills

## Available Skills

- **Jira**: Issue tracking - read ~/.claude/skills/jira/SKILL.md

## Running Scripts

Always run skill scripts directly:

```bash
python ~/.claude/skills/jira/jira.py search "project = DEMO"
```

## Skill Invocation

Use `/jira` or describe naturally:
- "Search Jira for my open issues"
- "Create a bug in PROJECT about login failures"
```

See the [Claude Code settings documentation](https://code.claude.com/docs/en/settings) and [CLAUDE.md guide](https://www.builder.io/blog/claude-md-guide) for details.

> **Other AI Agents**: Support for other agents (Cursor, Continue.dev, etc.) is planned. See [../TODO.md](../TODO.md).

## Authentication

Skills support three authentication methods (checked in order):

1. **Environment variables** (recommended):
   ```bash
   export JIRA_BASE_URL="https://yourcompany.atlassian.net"
   export JIRA_EMAIL="you@example.com"
   export JIRA_API_TOKEN="your-token"
   ```

2. **System keyring** (interactive setup):
   ```bash
   cd agent-skills
   python scripts/setup_auth.py jira
   ```

3. **Config file** (`~/.config/agent-skills/config.yaml`):
   ```yaml
   jira:
     url: https://yourcompany.atlassian.net
     email: you@example.com
     token: your-token
   ```

Environment variables are the easiest for most users. Add them to your `~/.bashrc` or `~/.zshrc`.

## Updating Skills

To update skills to the latest version:

```bash
cd ~/.claude/skills
curl -L https://github.com/odyssey4me/agent-skills/releases/latest/download/jira.tar.gz | tar xz
```

For developers working from the repository:

```bash
cd agent-skills
git pull
pip install -e ".[dev]"  # In case dependencies changed
```

## Verifying Setup

Each skill includes a `check` command to verify requirements:

```bash
# Check Jira skill
python ~/.claude/skills/jira/jira.py check
```

This validates:
- Python dependencies installed
- Authentication configured
- Service connectivity

If anything is missing, the check command provides setup instructions.

## Troubleshooting

### Issue: Import errors

**Solution**: Install dependencies in user-space:

```bash
pip install --user requests keyring pyyaml
```

### Issue: Authentication failing

**Solution**: Verify credentials are configured:

```bash
# Check environment variables
env | grep -i jira

# Or run the check command
python ~/.claude/skills/jira/jira.py check
```

The check command will tell you exactly what's missing and how to configure it.

### Issue: Agent can't find skills

**Solution**: Verify the skill files exist at the path you configured:

```bash
ls -la ~/.claude/skills/jira/
```

You should see:
```
jira/
├── SKILL.md
└── jira.py
```

Update your agent configuration to point to the correct path.

### Issue: Permission denied

**Solution**: Ensure the script is readable:

```bash
chmod +r ~/.claude/skills/jira/jira.py
```

## Why User-Space Installation?

This project uses user-space installation (`pip install --user`) to:

1. **No sudo required**: Installs to `~/.local/lib/python*/site-packages/`
2. **Per-user isolation**: Each user has their own packages
3. **No virtual environment needed**: Skills are self-contained scripts
4. **System packages untouched**: System Python remains clean

For system-wide packages (if ever needed), use your platform's package manager:
- Fedora/RHEL: `sudo dnf install python3-requests`
- Ubuntu/Debian: `sudo apt install python3-requests`
- macOS: `brew install python3`

## Installation Paths

Common installation locations following XDG Base Directory Specification:

- `~/.claude/skills/` - Claude Code skills directory
- `~/.local/share/agent-skills/` - XDG data directory
- `~/.config/agent-skills/` - Configuration files
- `~/.cache/agent-skills/` - Cache data (if needed)

For more information:
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/)
- [ArchWiki: XDG Base Directory](https://wiki.archlinux.org/title/XDG_Base_Directory)
