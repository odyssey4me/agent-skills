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
| calendars list | read | List calendars |
| calendars get | read | Get calendar details |
| events list | read | List events |
| events get | read | Get event details |
| events create | write | Create an event |
| events update | write | Update an event |
| events delete | write | Delete an event |
| freebusy | read | Check availability |
