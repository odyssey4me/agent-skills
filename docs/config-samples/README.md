# Optional agent configuration samples

Skills use the Agent Skills specification and can be consumed by any compatible
agent. Install using `npx skills add odyssey4me/agent-skills` and use your agent's
skill interface or natural language. No particular agent configuration is required
by these skills.

The following optional examples show how to add instructions for specific agents:

- [Codex](.codex/AGENTS.md.sample): merge into `${CODEX_HOME:-~/.codex}/AGENTS.md`.
- [Claude Code](.claude/CLAUDE.md.sample): merge into `~/.claude/CLAUDE.md`.

Adjust paths for your installation and preserve existing instructions. Other
agents can use the same guidance in their own instruction files.

The repository's `scripts/setup_helper.py` is a Codex development convenience,
not a requirement for consuming skills. Use `--dry-run` to preview changes or
`--agents-md /path/to/AGENTS.md` to choose a development instruction file.

See the [user guide](../user-guide.md) for agent-neutral installation and usage.
