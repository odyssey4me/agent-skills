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
| documents get | read | Get document metadata |
| documents read | read | Read document content |
| documents create | write | Create a new document |
| content append | write | Append content to a document |
| content insert | write | Insert content at a position |
| content delete | write | Delete content from a document |
| content insert-after-anchor | write | Insert content after an anchor |
| formatting apply | write | Apply formatting to content |
