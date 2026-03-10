# Command Permissions

This reference classifies commands by access level to help agents
enforce appropriate permission controls.

- **read**: Safe to execute without user confirmation. These commands
  only retrieve or display information.
- **write**: Requires user confirmation before execution. These
  commands create, modify, or delete data.

Note: This skill's script only provides read operations. Write
operations (creating issues, PRs, merging) use the `gh` CLI
directly and are not covered here.

| Command | Access | Description |
|---------|--------|-------------|
| check | read | Verify setup and connectivity |
| issues list | read | List repository issues |
| issues view | read | View issue details |
| prs list | read | List pull requests |
| prs view | read | View pull request details |
| prs checks | read | View PR check status |
| prs status | read | View PR review status |
| runs list | read | List workflow runs |
| runs view | read | View workflow run details |
| repos list | read | List repositories |
| repos view | read | View repository details |
| search repos | read | Search repositories |
| search issues | read | Search issues |
| search prs | read | Search pull requests |
