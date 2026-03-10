# Command Permissions

This reference classifies commands by access level to help agents
enforce appropriate permission controls.

- **read**: Safe to execute without user confirmation. These commands
  only retrieve or display information.
- **write**: Requires user confirmation before execution. These
  commands create, modify, or delete data.

Note: This skill's script only provides read operations. Write
operations use the `glab` CLI directly and are not covered here.

| Command | Access | Description |
|---------|--------|-------------|
| check | read | Verify setup and connectivity |
| issues list | read | List project issues |
| issues view | read | View issue details |
| mrs list | read | List merge requests |
| mrs view | read | View merge request details |
| pipelines list | read | List pipelines |
| pipelines view | read | View pipeline details |
| repos list | read | List projects |
| repos view | read | View project details |
