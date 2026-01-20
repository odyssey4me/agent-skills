# API Skill Template

This template provides a starting point for creating a new API-based skill.

## Usage

1. **Copy the template**:
   ```bash
   cp -r templates/api-skill skills/myskill
   cd skills/myskill
   ```

2. **Rename and customize files**:
   ```bash
   # Rename the template files
   mv skill.py.template myskill.py
   mv SKILL.md.template SKILL.md

   # Replace placeholders in both files
   # {{SKILL_NAME}} - Display name (e.g., "MyService", "GitHub")
   # {{SERVICE_NAME}} - Lowercase identifier (e.g., "myservice", "github")
   # {{SERVICE_NAME_UPPER}} - Uppercase for env vars (e.g., "MYSERVICE", "GITHUB")
   # {{DESCRIPTION}} - Brief description of the skill
   ```

3. **Implement your skill**:
   - Edit `myskill.py`:
     - Replace placeholders (`{{SKILL_NAME}}`, etc.)
     - Implement API functions (`list_resources`, `get_resource`, `create_resource`)
     - Update the `check` command connectivity test
     - Add more commands as needed
   - Edit `SKILL.md`:
     - Replace placeholders
     - Document authentication requirements
     - Document all commands
     - Add usage examples

4. **Test your skill**:
   ```bash
   python myskill.py --help
   python myskill.py check
   ```

5. **Add tests**:
   - Create `tests/test_myskill.py`
   - Test all commands
   - Test authentication fallback chain

## Template Structure

```
templates/api-skill/
├── README.md              # This file
├── skill.py.template      # Self-contained skill script template
└── SKILL.md.template      # Documentation template
```

## What's Included

The template provides:

- **Self-contained script**: All utilities inlined (auth, HTTP, output formatting)
- **Authentication**: Supports keyring, env vars, and config files with fallback chain
- **Built-in validation**: `check` command verifies requirements and connectivity
- **Subcommand CLI**: Uses argparse with subcommands (like git, docker)
- **Output formatting**: JSON and table formatting
- **Error handling**: Proper error messages and exit codes
- **Example commands**: list, get, create (customize for your API)

## Placeholder Reference

| Placeholder | Example | Usage |
|-------------|---------|-------|
| `{{SKILL_NAME}}` | `GitHub` | Display name in documentation |
| `{{SERVICE_NAME}}` | `github` | Lowercase identifier for function names, file names |
| `{{SERVICE_NAME_UPPER}}` | `GITHUB` | Uppercase for environment variables |
| `{{DESCRIPTION}}` | `GitHub API integration for repository management` | Brief description |

## Implementation Checklist

- [ ] Copy template to `skills/yourskill/`
- [ ] Rename `skill.py.template` to `yourskill.py`
- [ ] Rename `SKILL.md.template` to `SKILL.md`
- [ ] Replace all placeholders in both files
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
mv skill.py.template github.py
mv SKILL.md.template SKILL.md

# Replace placeholders (manual or with sed)
sed -i 's/{{SKILL_NAME}}/GitHub/g' github.py SKILL.md
sed -i 's/{{SERVICE_NAME}}/github/g' github.py SKILL.md
sed -i 's/{{SERVICE_NAME_UPPER}}/GITHUB/g' github.py SKILL.md
sed -i 's/{{DESCRIPTION}}/GitHub API integration for repository management/g' SKILL.md

# Implement API functions in github.py
# - Update list_resources() to call GitHub's repos API
# - Update get_resource() to get repo details
# - Update create_resource() to create a repo
# - Update connectivity test in cmd_check()

# Test
python github.py --help
python github.py check
```

## Tips

1. **Start simple**: Implement the most common operations first (list, get, create)
2. **Use the Jira skill as reference**: See `skills/jira/jira.py` for a complete example
3. **Keep it self-contained**: Don't import from other skills or shared code
4. **Test the `check` command**: Ensure it validates all requirements
5. **Document thoroughly**: Good `SKILL.md` helps AI agents use your skill effectively
