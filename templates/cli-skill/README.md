# CLI Skill Template

This template provides a starting point for creating a new CLI wrapper skill following the [Agent Skills specification](https://agentskills.io/specification).

CLI skills are **documentation-only** -- they contain no scripts. Instead, they document how to use an official CLI tool effectively.

## Usage

1. **Copy the template**:
   ```bash
   cp -r templates/cli-skill skills/mytool
   cd skills/mytool
   ```

2. **Set up directory structure** (already created):
   ```
   skills/mytool/
   ├── SKILL.md.template      # Rename to SKILL.md
   └── references/            # Add workflow examples, cheat sheets, etc.
   ```

3. **Rename and customize files**:
   ```bash
   mv SKILL.md.template SKILL.md
   ```

   Replace placeholders in SKILL.md:

   | Placeholder | Example | Usage |
   |-------------|---------|-------|
   | `{{SKILL_NAME}}` | `GitHub` | Display name in documentation |
   | `{{SERVICE_NAME}}` | `github` | Lowercase identifier for frontmatter |
   | `{{CLI_TOOL}}` | `gh` | CLI binary name |
   | `{{DESCRIPTION}}` | `Work with GitHub using the gh CLI` | Brief one-line description |
   | `{{AUTHOR}}` | `yourusername` | Author name for metadata |
   | `{{LICENSE}}` | `MIT` | License identifier |
   | `{{CATEGORY}}` | `code-hosting` | Skill category |
   | `{{TAGS}}` | `issues, pull-requests` | Comma-separated tags |
   | `{{CLI_INSTALL_URL}}` | `https://cli.github.com/manual/installation` | Install docs URL |
   | `{{CLI_DOCS_URL}}` | `https://cli.github.com/manual/` | CLI reference docs URL |

4. **Document the CLI commands**:
   - Group commands logically (e.g., Issues, PRs, Repos)
   - Include common flags and options
   - Add real-world workflow examples in references/
   - Document authentication steps

5. **Validate your skill**:
   ```bash
   python scripts/validate_skill.py skills/mytool
   ```

## Key Differences from API Skills

| Aspect | API Skill | CLI Skill |
|--------|-----------|-----------|
| Scripts | Has `scripts/` directory | No scripts |
| Dependencies | Python packages | External CLI tool |
| Complexity | `standard` | `lightweight` |
| Auth | Keyring/env/config fallback | CLI's built-in auth |
| Output | JSON/table formatting | CLI's native output |

## When to Use This Template

Use this template when:
- An official, well-maintained CLI already exists for the service
- The CLI provides comprehensive coverage of the service's features
- Writing a custom script would duplicate CLI functionality

Use the **api-skill** template instead when:
- No official CLI exists
- The CLI is incomplete or poorly maintained
- You need custom logic (e.g., JQL query building, OAuth flows)

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [GitHub Skill](../../skills/github/) - Working CLI skill example
- [GitLab Skill](../../skills/gitlab/) - Another CLI skill example
- [Developer Guide](../../docs/developer-guide.md)
