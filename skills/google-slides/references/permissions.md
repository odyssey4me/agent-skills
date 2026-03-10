# Command Permissions

This reference classifies commands by access level to help agents
enforce appropriate permission controls.

- **read**: Safe to execute without user confirmation. These commands
  only retrieve or display information.
- **write**: Requires user confirmation before execution. These
  commands create, modify, or delete data.

| Command | Access | Description |
|---------|--------|-------------|
| check | read | Verify setup and connectivity |
| auth status | read | Show OAuth token information |
| auth setup | write | Store OAuth client credentials |
| auth reset | write | Clear stored OAuth token |
| presentations get | read | Get presentation metadata |
| presentations read | read | Read slide content |
| presentations create | write | Create a new presentation |
| slides create | write | Add a slide |
| slides delete | write | Delete a slide |
| text insert | write | Insert text into a shape |
| shapes create | write | Create a shape |
| images create | write | Insert an image |
