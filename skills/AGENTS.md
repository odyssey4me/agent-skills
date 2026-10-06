# Skills Directory

Each subdirectory is a self-contained, independently deployable agent skill
following the [Agent Skills specification](https://agentskills.io/specification).

## Skill Structure

```
skills/<name>/
├── SKILL.md           # Documentation + YAML frontmatter (required)
├── scripts/
│   └── <name>.py      # Python implementation
└── references/        # Optional supplementary docs
```

## Running Checks for a Single Skill

- Validate structure: `python scripts/validate_skill.py skills/<name>/SKILL.md`
- Run tests: `pytest tests/test_<name>.py`

## Creating a New Skill

Copy a template from `templates/` (api-skill, cli-skill, or workflow-skill)
and follow its README checklist.
