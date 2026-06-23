# Command Permissions

This reference classifies commands by access level to help agents
enforce appropriate permission controls.

- **read**: Safe to execute without user confirmation. These commands
  only retrieve or display information.
- **write**: Requires user confirmation before execution. These
  commands create, modify, or delete data, or produce files on disk.

| Command | Access | Description |
|---------|--------|-------------|
| check | read | Verify setup and connectivity |
| auth status | read | Show OAuth token information |
| auth setup | write | Store OAuth client credentials |
| auth reset | write | Clear stored OAuth token |
| get | read | Download presentation as Markdown |
| palettes | read | List available color palettes |
| verify | read | Check .pptx for quality/accessibility issues |
| preview --format summary | read | Print text summary of slides |
| create | write | Build .pptx from Markdown (and optionally upload) |
| update | write | Upload .pptx to an existing presentation |
| preview --format images | write | Render slide images to disk |
