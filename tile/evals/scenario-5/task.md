# Jira Workflow Transition Manager

A utility that lists the available workflow transitions for a Jira issue and executes a specified transition to move the issue to a new status.

## Capabilities

### List and Execute Workflow Transitions
- Requesting the available transitions for an issue key returns a list of valid next-state names that the issue can move to from its current status [@test](./tests/test_list_transitions.py)
- Executing a transition by name moves the issue to the corresponding new status, confirmed by retrieving the updated status after the transition [@test](./tests/test_execute_transition.py)
- Attempting to execute a transition that is not currently valid for the issue produces an error message that includes the list of valid transition names [@test](./tests/test_invalid_transition.py)

## Dependencies { .dependencies }

### agent-skills 0.2.0 { .dependency }

Portable skills for AI coding assistants providing integrations with Jira, Confluence, and other development tools.
[@satisfied-by](agent-skills)
