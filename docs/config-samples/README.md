# Sample Configuration Files

This directory contains sample configuration files for Claude Code.

> **Note**: These samples are for Claude Code. Skills work with [multiple AI agents](https://github.com/vercel-labs/add-skill#supported-agents) via the Agent Skills specification. See [../user-guide.md](../user-guide.md) for multi-agent installation.

## Available Samples

### Claude Code
- [`.claude/CLAUDE.md.sample`](.claude/CLAUDE.md.sample) - Global configuration file
- **Install to**: `~/.claude/CLAUDE.md`

## When to Use This

After installing skills with `npx add-skill odyssey4me/agent-skills`, you may want to configure Claude Code to make skills easier to discover and use. (These config samples are Claude Code-specific, but skills work with multiple AI agents.) The sample configuration:

1. Documents which skills are available
2. Shows how to invoke skills (via `/jira` commands or natural language)
3. Provides example script commands

## Installation

1. Copy the sample file to its destination:
   ```bash
   cp docs/config-samples/.claude/CLAUDE.md.sample ~/.claude/CLAUDE.md
   ```

2. Adjust paths if you installed skills to a different location (default is `~/.claude/skills`)

3. Restart Claude Code if needed

## Notes

- The sample assumes skills were installed with `npx add-skill` to `~/.claude/skills`
- If you installed to a custom location, update the paths in CLAUDE.md
- See [../user-guide.md](../user-guide.md) for complete installation instructions
