@./AGENTS.md

Refer to @./CONTRIBUTING.md for development guidelines.

## Gemini-Specific Notes

### File References
Use `@` syntax to include files in context:
- `@./skills/jira/SKILL.md` - Include Jira skill docs
- `@./skills/jira/jira.py` - Include Jira skill implementation

### Context Management
Reference specific files rather than directories to manage context size.

### Running Skills
Skills are self-contained Python scripts:
```bash
python skills/jira/jira.py check
python skills/jira/jira.py search "project = DEMO"
```
