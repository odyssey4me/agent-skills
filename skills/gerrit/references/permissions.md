# Command Permissions

This reference classifies commands by access level to help agents
enforce appropriate permission controls.

- **read**: Safe to execute without user confirmation. These commands
  only retrieve or display information.
- **write**: Requires user confirmation before execution. These
  commands create, modify, or delete data.

Note: This skill's script only provides read operations. Write
operations use `git-review` directly and are not covered here.

| Command | Access | Description |
|---------|--------|-------------|
| check | read | Verify setup and connectivity |
| changes list | read | List changes |
| changes view | read | View change details |
| changes search | read | Search changes |
| projects list | read | List projects |
