# API Skill Template

This template provides a starting point for creating a new API-based skill following the [Agent Skills specification](https://agentskills.io/specification).

## Usage

1. **Copy the template**:
   ```bash
   cp -r templates/api-skill skills/myskill
   cd skills/myskill
   ```

2. **Set up directory structure** (already created):
   ```
   skills/myskill/
   ├── SKILL.md.template      # Rename to SKILL.md
   ├── scripts/
   │   └── skill.py.template  # Rename to myskill.py
   └── references/            # Optional: add additional docs here
   ```

3. **Rename and customize files**:
   ```bash
   # Rename the template files
   mv SKILL.md.template SKILL.md
   mv scripts/skill.py.template scripts/myskill.py

   # Replace placeholders in both files
   # {{SKILL_NAME}} - Display name (e.g., "MyService", "GitHub")
   # {{SERVICE_NAME}} - Lowercase identifier (e.g., "myservice", "github")
   # {{SERVICE_NAME_UPPER}} - Uppercase for env vars (e.g., "MYSERVICE", "GITHUB")
   # {{DESCRIPTION}} - Brief one-line description for the frontmatter
   # {{AUTHOR}} - Your GitHub username or name
   # {{LICENSE}} - License (e.g., "MIT", "Apache-2.0")
   ```

4. **Implement your skill**:
   - Edit `scripts/myskill.py`:
     - Replace placeholders (`{{SKILL_NAME}}`, etc.)
     - Implement API functions (`list_resources`, `get_resource`, `create_resource`)
     - Update the `check` command connectivity test
     - Add more commands as needed
   - Edit `SKILL.md`:
     - Replace placeholders in YAML frontmatter
     - Replace placeholders in documentation
     - Document authentication requirements
     - Document all commands
     - Add usage examples

5. **Test your skill**:
   ```bash
   python scripts/myskill.py --help
   python scripts/myskill.py check
   python scripts/validate_skill.py skills/myskill
   ```

6. **Add tests**:
   - Create `tests/test_myskill.py`
   - Test all commands
   - Test authentication fallback chain

## Template Structure

```
templates/api-skill/
├── README.md              # This file
├── SKILL.md.template      # Documentation template with YAML frontmatter
├── scripts/
│   └── skill.py.template  # Self-contained skill script template
└── references/            # Optional: add additional documentation
```

## What's Included

The template provides:

- **YAML frontmatter**: Required `name` and `description` fields for skill discovery
- **Self-contained script**: All utilities inlined (auth, HTTP, output formatting)
- **Authentication**: Supports keyring, env vars, and config files with fallback chain
- **Built-in validation**: `check` command verifies requirements and connectivity
- **Subcommand CLI**: Uses argparse with subcommands (like git, docker)
- **Output formatting**: JSON and table formatting
- **Error handling**: Proper error messages and exit codes
- **Example commands**: list, get, create (customize for your API)
- **Progressive disclosure**: Frontmatter → SKILL.md → references/ structure

## Placeholder Reference

| Placeholder | Example | Usage |
|-------------|---------|-------|
| `{{SKILL_NAME}}` | `GitHub` | Display name in documentation |
| `{{SERVICE_NAME}}` | `github` | Lowercase identifier for function names, file names, frontmatter |
| `{{SERVICE_NAME_UPPER}}` | `GITHUB` | Uppercase for environment variables |
| `{{DESCRIPTION}}` | `Manage GitHub repositories and issues` | Brief one-line description for frontmatter |
| `{{AUTHOR}}` | `yourusername` | Author name for metadata |
| `{{LICENSE}}` | `MIT` | License identifier |

## Implementation Checklist

- [ ] Copy template to `skills/yourskill/`
- [ ] Rename `SKILL.md.template` to `SKILL.md`
- [ ] Rename `scripts/skill.py.template` to `scripts/yourskill.py`
- [ ] Replace all placeholders in both files
- [ ] Verify YAML frontmatter is valid
- [ ] Implement API functions with actual endpoints
- [ ] Update `check` command connectivity test
- [ ] Add/remove commands as needed for your API
- [ ] Update documentation with real examples
- [ ] Test `--help` for all commands
- [ ] Test `check` command
- [ ] Test all functionality with real API
- [ ] Add tests in `tests/test_yourskill.py`
- [ ] Run `python scripts/validate_skill.py skills/yourskill`
- [ ] Update `README.md` skills table

## Example: Creating a GitHub Skill

```bash
# Copy template
cp -r templates/api-skill skills/github
cd skills/github

# Rename files
mv SKILL.md.template SKILL.md
mv scripts/skill.py.template scripts/github.py

# Replace placeholders (manual or with sed)
sed -i 's/{{SKILL_NAME}}/GitHub/g' SKILL.md scripts/github.py
sed -i 's/{{SERVICE_NAME}}/github/g' SKILL.md scripts/github.py
sed -i 's/{{SERVICE_NAME_UPPER}}/GITHUB/g' SKILL.md scripts/github.py
sed -i 's/{{DESCRIPTION}}/Manage GitHub repositories and issues/g' SKILL.md
sed -i 's/{{AUTHOR}}/yourusername/g' SKILL.md
sed -i 's/{{LICENSE}}/MIT/g' SKILL.md

# Implement API functions in scripts/github.py
# - Update list_resources() to call GitHub's repos API
# - Update get_resource() to get repo details
# - Update create_resource() to create a repo
# - Update connectivity test in cmd_check()

# Test
python scripts/github.py --help
python scripts/github.py check

# Validate
python scripts/validate_skill.py skills/github
```

## Tips

1. **Start simple**: Implement the most common operations first (list, get, create)
2. **Use the Jira skill as reference**: See `skills/jira/scripts/jira.py` for a complete example
3. **Keep it self-contained**: Don't import from other skills or shared code
4. **Test the `check` command**: Ensure it validates all requirements
5. **Document thoroughly**: Good `SKILL.md` helps AI agents use your skill effectively
6. **Follow the spec**: See [Agent Skills specification](https://agentskills.io/specification) for requirements
7. **Keep description brief**: The frontmatter `description` should be one line for discovery

## References

- [Agent Skills Specification](https://agentskills.io/specification) - Standard we follow
- [Developer Guide](../../docs/developer-guide.md) - Comprehensive development documentation
- [Jira Skill](../../skills/jira/) - Complete working example
- [Confluence Skill](../../skills/confluence/) - Another complete example
