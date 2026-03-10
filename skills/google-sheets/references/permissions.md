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
| spreadsheets get | read | Get spreadsheet metadata |
| spreadsheets create | write | Create a new spreadsheet |
| values read | read | Read cell values |
| values write | write | Write cell values |
| values append | write | Append rows to a sheet |
| values clear | write | Clear cell values |
| sheets create | write | Add a sheet to a spreadsheet |
| sheets delete | write | Remove a sheet from a spreadsheet |
