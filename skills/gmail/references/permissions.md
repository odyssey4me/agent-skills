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
| messages list | read | List messages matching a query |
| messages get | read | Get a message by ID |
| send | write | Send an email |
| drafts list | read | List draft messages |
| drafts create | write | Create a draft message |
| drafts send | write | Send an existing draft |
| labels list | read | List Gmail labels |
| labels create | write | Create a Gmail label |
