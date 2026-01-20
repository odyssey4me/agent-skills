# GitHub Copilot Instructions

Agent skills available at ~/.local/share/agent-skills

Refer to ~/.local/share/agent-skills/AGENTS.md for skill usage.

## Available Skills

- **Jira**: Read ~/.local/share/agent-skills/skills/jira/SKILL.md

## Running Scripts

Always activate the virtual environment before running scripts:

```bash
cd ~/.local/share/agent-skills
source .venv/bin/activate
python skills/jira/scripts/search.py "project = DEMO"
```

## Environment Variables

If JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN are set, authentication is automatic.
Otherwise, credentials are stored in the system keyring.
