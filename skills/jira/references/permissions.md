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
| search | read | Search issues with JQL |
| issue get | read | Get issue details |
| issue comments | read | List issue comments |
| issue create | write | Create a new issue |
| issue update | write | Update issue fields |
| issue comment | write | Add a comment to an issue |
| transitions list | read | List available transitions |
| transitions do | write | Transition an issue |
| config show | read | Show configuration |
| fields | read | List available fields |
| statuses | read | List available statuses |
| collaboration epics | read | List collaboration epics |
