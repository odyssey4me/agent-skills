# Sample Configuration Files

This directory contains sample configuration files for Claude Code.

> **Note**: Currently focused on Claude Code only. Support for other AI agents (Cursor, Continue.dev, etc.) is planned for future releases. See [../../TODO.md](../../TODO.md) for roadmap.

## Available Samples

### Claude Code
- [`.claude/CLAUDE.md.sample`](.claude/CLAUDE.md.sample) - Global configuration file
- **Install to**: `~/.claude/CLAUDE.md`

## Manual Installation

To install manually:

1. Copy the sample file to its destination:
   ```bash
   cp docs/config-samples/.claude/CLAUDE.md.sample ~/.claude/CLAUDE.md
   ```

2. Adjust paths if you installed skills to a different location (default is `~/.claude/skills`)

3. Restart Claude Code if needed

## Notes

- The sample uses `~/.claude/skills` as the default skills directory
- You can install skills to any location - just update the paths in CLAUDE.md
- See [../installation.md](../installation.md) for complete installation instructions
