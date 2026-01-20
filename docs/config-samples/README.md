# Sample Configuration Files

This directory contains sample configuration files for various AI coding assistants.

**Important**: These files are used by `scripts/install.py` to generate agent configurations. When you run `python scripts/install.py setup --agents <agent>`, it reads the appropriate sample file and automatically replaces `~/.local/share/agent-skills` with your actual installation path.

## Available Samples

### Claude Code
- [`.claude/CLAUDE.md.sample`](.claude/CLAUDE.md.sample) - Global configuration file
- **Install to**: `~/.claude/CLAUDE.md`

### OpenAI Codex
- [`.vscode/codex-settings.json.sample`](.vscode/codex-settings.json.sample) - VS Code settings
- **Install to**: User or workspace `settings.json`

### Gemini CLI
- [`.gemini/GEMINI.md.sample`](.gemini/GEMINI.md.sample) - Global configuration file
- **Install to**: `~/.gemini/GEMINI.md`

### Cursor
- [`.cursor/rules/agent-skills.mdc.sample`](.cursor/rules/agent-skills.mdc.sample) - Project-specific rules
- [`cursor-global-rules.json.sample`](cursor-global-rules.json.sample) - Global settings snippet
- **Install to**:
  - Project: `.cursor/rules/agent-skills.mdc`
  - Global: Copy content to Cursor Settings > General > Rules for AI

### Continue.dev
- [`.continue/config.json.sample`](.continue/config.json.sample) - Global configuration
- **Install to**:
  - MacOS/Linux: `~/.continue/config.json`
  - Windows: `C:\Users\[username]\.continue\config.json`

### GitHub Copilot
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) - Per-repository instructions
- **Install to**: `.github/copilot-instructions.md` in each project

## Automated Installation (Recommended)

Use the install helper script to automatically configure agents:

```bash
cd ~/.local/share/agent-skills  # or wherever you installed
source .venv/bin/activate

# Preview what would be done
python scripts/install.py setup --agents claude,codex --dry-run

# Actually create configs (auto-detects install location)
python scripts/install.py setup --agents claude,codex

# Or set up all agents at once
python scripts/install.py setup --all-agents
```

The script will:
- Detect your actual installation path
- Load the sample files from this directory
- Replace `~/.local/share/agent-skills` with your actual path
- Back up any existing configs (if they don't already reference agent-skills)
- Respect existing agent-skills configurations

## Manual Installation

If you prefer manual installation:

1. Copy the sample file to its destination
2. Rename it (remove `.sample` extension where applicable)
3. Replace `~/.local/share/agent-skills` with your actual installation path
4. Restart your IDE/editor if needed

## Notes

- **Path placeholder**: All samples use `~/.local/share/agent-skills` as a placeholder
- **Auto-detection**: The install script automatically replaces this with your actual path
- **Existing configs**: The install script respects existing configurations that already reference agent-skills
- **JSON configs**: For Continue.dev and Codex, the script provides merge instructions if you have existing settings
- **Documentation syntax**: The `--8<--` syntax in installation.md is for MkDocs rendering - don't use it in actual config files
