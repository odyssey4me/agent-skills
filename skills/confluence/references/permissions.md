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
| search | read | Search pages with CQL |
| page get | read | Get page content |
| page create | write | Create a new page |
| page update | write | Update page content |
| space list | read | List spaces |
| space get | read | Get space details |
| config show | read | Show configuration |
