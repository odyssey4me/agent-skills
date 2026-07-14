# Configuration Reference

## Providing gog

### PATH binary (default)

Install the `gog` binary so it's available in your PATH:

```bash
# Homebrew
brew install openclaw/tap/gogcli

# Manual download (Linux amd64)
curl -sL https://github.com/openclaw/gogcli/releases/latest/download/gogcli_VERSION_linux_amd64.tar.gz | tar xz
mv gog ~/.local/bin/

# Verify
gog --version
```

### Container

Run gog via podman or docker:

```bash
podman run --rm ghcr.io/openclaw/gogcli gog --version
```

For authenticated operations, mount the config directory:

```bash
podman run --rm \
  -v ~/.config/gogcli:/root/.config/gogcli:ro \
  -v ~/.local/share/gogcli:/root/.local/share/gogcli \
  ghcr.io/openclaw/gogcli gog auth status
```

### MCP server

Run gog as an MCP server for Claude Code:

```bash
# Read-only (default)
gog mcp

# With write access
gog mcp --allow-write

# Filtered to specific services
gog mcp --allow-tool "gmail.*,calendar.*"
```

To configure as a Claude Code MCP server, add to your settings:

```json
{
  "mcpServers": {
    "google": {
      "command": "gog",
      "args": ["mcp"]
    }
  }
}
```

Default MCP tools (read-only):

| Tool | Service | Description |
|------|---------|-------------|
| `gmail_search` | Gmail | Search messages |
| `gmail_get_message` | Gmail | Get a message |
| `gmail_get_thread` | Gmail | Get a thread |
| `drive_search` | Drive | Search files |
| `drive_get` | Drive | Get file metadata |
| `docs_get` | Docs | Read a document |
| `sheets_read_range` | Sheets | Read spreadsheet range |
| `calendar_events` | Calendar | List events |

With `--allow-write`, adds:

| Tool | Service | Description |
|------|---------|-------------|
| `docs_write` | Docs | Write to a document |
| `sheets_update_range` | Sheets | Update spreadsheet values |

## Optional configuration

### Default account

Set a default account in `~/.config/agent-skills/google.yaml`:

```yaml
gog:
  account: user@example.com
```

Or set it via gog directly:

```bash
gog auth alias set default user@example.com
```

### Multi-account

Use `--account` to specify which account to use:

```bash
gog --account work@company.com gmail search "is:unread"
gog --account personal@gmail.com drive ls
```

### gog configuration

gog has its own config at `~/.config/gogcli/config.json`:

```bash
gog config list       # show all config
gog config keys       # list available keys
gog config set timezone "America/New_York"
```

## Dependency management

The gogcli version is pinned in `skills/google/SKILL.md` frontmatter (`gogcli-version`). Updates are managed by Renovate and validated by CI (checksum verification and govulncheck) before merge. See [SECURITY.md](https://github.com/odyssey4me/agent-skills/blob/main/SECURITY.md) for the full security validation process.

## Schema introspection

Get the machine-readable command schema:

```bash
# Full schema
gog schema --json

# Schema for a specific command
gog schema gmail search --json
```
