# Command Permissions

This reference classifies commands by access level to help agents
enforce appropriate permission controls.

- **read**: Safe to execute without user confirmation. These commands
  only retrieve or display information.
- **write**: Requires user confirmation before execution. These
  commands create, modify, or delete data.

Note: `files download` is classified as read because it retrieves
data without modifying remote state.

| Command | Access | Description |
|---------|--------|-------------|
| check | read | Verify setup and connectivity |
| auth status | read | Show OAuth token information |
| auth setup | write | Store OAuth client credentials |
| auth reset | write | Clear stored OAuth token |
| files list | read | List files |
| files search | read | Search files |
| files get | read | Get file metadata |
| files download | read | Download a file |
| files upload | write | Upload a file |
| files move | write | Move a file |
| files delete | write | Permanently delete a file |
| files rename | write | Rename a file |
| files copy | write | Copy a file |
| folders list | read | List folder contents |
| folders create | write | Create a folder |
| permissions list | read | List file permissions |
| share | write | Share a file with users |
| permissions delete | write | Remove sharing permissions |
