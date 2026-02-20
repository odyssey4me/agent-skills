# Workflow Skill Template

This template provides a starting point for creating a new workflow skill following the [Agent Skills specification](https://agentskills.io/specification).

Workflow skills are **documentation-only** -- they contain no scripts. Instead, they guide the agent through multi-step processes that orchestrate other skills.

## Usage

1. **Copy the template**:
   ```bash
   cp -r templates/workflow-skill skills/myworkflow
   cd skills/myworkflow
   ```

2. **Set up directory structure** (already created):
   ```
   skills/myworkflow/
   ├── SKILL.md.template      # Rename to SKILL.md
   └── references/            # Add supplementary docs here
   ```

3. **Rename and customize files**:
   ```bash
   mv SKILL.md.template SKILL.md
   ```

   Replace placeholders in SKILL.md:

   | Placeholder | Example | Usage |
   |-------------|---------|-------|
   | `{{SKILL_NAME}}` | `Code Review` | Display name in documentation |
   | `{{SERVICE_NAME}}` | `code-review` | Lowercase identifier for frontmatter |
   | `{{DESCRIPTION}}` | `Review PRs across platforms` | Brief one-line description |
   | `{{AUTHOR}}` | `yourusername` | Author name for metadata |
   | `{{LICENSE}}` | `MIT` | License identifier |
   | `{{CATEGORY}}` | `development` | Skill category |
   | `{{TAGS}}` | `review, security` | Comma-separated tags |
   | `{{REQUIRED_SKILLS}}` | `github, gitlab` | Skills this workflow depends on |

4. **Define the workflow steps**:
   - Document each step with clear instructions
   - Include the exact commands from dependent skills
   - Specify decision points and branching logic
   - Add references/ docs for checklists or guidelines

5. **Validate your skill**:
   ```bash
   python scripts/validate_skill.py skills/myworkflow
   ```

## Key Differences from API Skills

| Aspect | API Skill | Workflow Skill |
|--------|-----------|----------------|
| Scripts | Has `scripts/` directory | No scripts |
| Dependencies | Python packages | Other skills |
| Complexity | `standard` | `orchestration` |
| Type | `api` | `workflow` |
| Auth | Direct (keyring/env/config) | Delegated to sub-skills |

## Example: Creating a Release Workflow

```bash
cp -r templates/workflow-skill skills/release
cd skills/release
mv SKILL.md.template SKILL.md

# Edit SKILL.md:
# - Orchestrates github skill for PR merges and releases
# - Orchestrates jira skill for updating issue statuses
# - Defines steps: check CI, merge PRs, create release, update Jira
```

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Code Review Skill](../../skills/code-review/) - Working workflow skill example
- [Developer Guide](../../docs/developer-guide.md)
