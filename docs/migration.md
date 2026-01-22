# Migration Guide: v0.1.x to v0.2.0

This guide helps you upgrade from v0.1.x to v0.2.0, which adopts the [Agent Skills specification](https://agentskills.io/specification) standard.

## What Changed?

Version 0.2.0 restructures the repository to comply with the Agent Skills specification, enabling:
- ✅ Compatibility with `npx add-skill` installation tool
- ✅ Better organization with `scripts/` and `references/` subdirectories
- ✅ YAML frontmatter for skill discovery
- ✅ Progressive disclosure for better AI agent performance

## Directory Structure Changes

### Before (v0.1.x)

```
skills/jira/
├── SKILL.md
├── jira.py
└── scriptrunner.md

skills/confluence/
├── SKILL.md
├── confluence.py
└── creating-content.md
```

### After (v0.2.0)

```
skills/jira/
├── SKILL.md (with YAML frontmatter)
├── scripts/
│   └── jira.py
└── references/
    └── scriptrunner.md

skills/confluence/
├── SKILL.md (with YAML frontmatter)
├── scripts/
│   └── confluence.py
└── references/
    └── creating-content.md
```

## Migration Steps

### For Users

If you installed skills manually to `~/.claude/skills/`:

#### Option 1: Clean Reinstall (Recommended)

1. **Backup your configuration**:
   ```bash
   cp ~/.config/agent-skills/jira.yaml ~/jira-config-backup.yaml
   cp ~/.config/agent-skills/confluence.yaml ~/confluence-config-backup.yaml
   ```

2. **Remove old skills**:
   ```bash
   rm -rf ~/.claude/skills/jira
   rm -rf ~/.claude/skills/confluence
   ```

3. **Install new version**:
   ```bash
   npx add-skill odyssey4me/agent-skills --skill jira --skill confluence
   ```

   Or download from [releases](https://github.com/odyssey4me/agent-skills/releases):
   ```bash
   cd ~/.claude/skills
   curl -L https://github.com/odyssey4me/agent-skills/releases/latest/download/jira.tar.gz | tar xz
   curl -L https://github.com/odyssey4me/agent-skills/releases/latest/download/confluence.tar.gz | tar xz
   ```

4. **Restore your configuration**:
   ```bash
   cp ~/jira-config-backup.yaml ~/.config/agent-skills/jira.yaml
   cp ~/confluence-config-backup.yaml ~/.config/agent-skills/confluence.yaml
   ```

5. **Verify**:
   ```bash
   python ~/.claude/skills/jira/scripts/jira.py check
   python ~/.claude/skills/confluence/scripts/confluence.py check
   ```

#### Option 2: Manual Update

If you prefer to update in-place:

1. **Create new directory structure**:
   ```bash
   cd ~/.claude/skills/jira
   mkdir -p scripts references

   cd ~/.claude/skills/confluence
   mkdir -p scripts references
   ```

2. **Move Python scripts**:
   ```bash
   mv ~/.claude/skills/jira/jira.py ~/.claude/skills/jira/scripts/
   mv ~/.claude/skills/confluence/confluence.py ~/.claude/skills/confluence/scripts/
   ```

3. **Move reference docs**:
   ```bash
   mv ~/.claude/skills/jira/scriptrunner.md ~/.claude/skills/jira/references/
   mv ~/.claude/skills/confluence/creating-content.md ~/.claude/skills/confluence/references/
   ```

4. **Download updated SKILL.md files**:
   ```bash
   # Jira
   curl -L https://raw.githubusercontent.com/odyssey4me/agent-skills/main/skills/jira/SKILL.md \
     -o ~/.claude/skills/jira/SKILL.md

   # Confluence
   curl -L https://raw.githubusercontent.com/odyssey4me/agent-skills/main/skills/confluence/SKILL.md \
     -o ~/.claude/skills/confluence/SKILL.md
   ```

5. **Verify**:
   ```bash
   python ~/.claude/skills/jira/scripts/jira.py check
   python ~/.claude/skills/confluence/scripts/confluence.py check
   ```

### For Developers

If you have a local clone of the repository:

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "WIP: my changes"
   ```

2. **Pull latest**:
   ```bash
   git checkout main
   git pull origin main
   ```

3. **Update your branch**:
   ```bash
   git checkout your-feature-branch
   git rebase main
   ```

4. **Update import paths in tests** (if you have custom tests):
   ```python
   # Old
   from skills.jira import jira

   # New
   from skills.jira.scripts import jira
   ```

5. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

## Command Changes

### Script Path Updates

All Python scripts have moved to `scripts/` subdirectories:

| Old Path | New Path |
|----------|----------|
| `skills/jira/jira.py` | `skills/jira/scripts/jira.py` |
| `skills/confluence/confluence.py` | `skills/confluence/scripts/confluence.py` |

### Updated Commands

If you were calling scripts directly:

**Before:**
```bash
python ~/.claude/skills/jira/jira.py search "project = DEMO"
python ~/.claude/skills/confluence/confluence.py search "space = DOCS"
```

**After:**
```bash
python ~/.claude/skills/jira/scripts/jira.py search "project = DEMO"
python ~/.claude/skills/confluence/scripts/confluence.py search "space = DOCS"
```

### Scripts and Aliases

If you have shell scripts or aliases that reference the old paths, update them:

**Before:**
```bash
alias jira='python ~/.claude/skills/jira/jira.py'
```

**After:**
```bash
alias jira='python ~/.claude/skills/jira/scripts/jira.py'
```

## SKILL.md Changes

SKILL.md files now include YAML frontmatter for skill discovery:

**Before:**
```markdown
# Jira

Interact with Jira for issue tracking...
```

**After:**
```markdown
---
name: jira
description: Search and manage Jira issues using JQL queries, create/update issues, and manage workflows
metadata:
  author: odyssey4me
  version: "0.2.0"
license: MIT
---

# Jira

Interact with Jira for issue tracking...
```

This frontmatter enables:
- Skill discovery by `npx add-skill`
- Progressive disclosure by AI agents
- Version tracking

## Reference Documentation

Additional documentation has moved to `references/` subdirectories:

| File | Old Location | New Location |
|------|--------------|--------------|
| ScriptRunner Guide | `skills/jira/scriptrunner.md` | `skills/jira/references/scriptrunner.md` |
| Content Creation Guide | `skills/confluence/creating-content.md` | `skills/confluence/references/creating-content.md` |

Links in SKILL.md files have been updated accordingly.

## Configuration (No Changes)

**Good news**: Configuration files and environment variables remain unchanged!

Your existing authentication setup will continue to work:

- Environment variables (`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, etc.)
- Config files (`~/.config/agent-skills/jira.yaml`, `~/.config/agent-skills/confluence.yaml`)
- Keyring credentials

No reconfiguration needed.

## Compatibility

### Python Scripts

The Python scripts themselves are **functionally identical** to v0.1.x:
- Same commands and arguments
- Same authentication methods
- Same API integrations
- Same output formats

Only the file locations changed.

### Claude Code

Skills will automatically work with Claude Code after migration. Claude Code discovers skills via YAML frontmatter, which is now present in v0.2.0.

### npx add-skill

New in v0.2.0: You can now install skills using the official `add-skill` CLI:

```bash
npx add-skill odyssey4me/agent-skills --skill jira
npx add-skill odyssey4me/agent-skills --skill confluence
```

## Troubleshooting

### "Command not found" or "No such file"

If you get errors like:
```
python ~/.claude/skills/jira/jira.py: No such file or directory
```

You're using the old path. Update to:
```bash
python ~/.claude/skills/jira/scripts/jira.py
```

### "SKILL.md missing frontmatter"

If npx add-skill cannot discover skills:

1. Verify SKILL.md starts with `---`:
   ```bash
   head ~/.claude/skills/jira/SKILL.md
   ```

2. Should show:
   ```yaml
   ---
   name: jira
   description: ...
   ```

3. If not, redownload SKILL.md from the repository.

### Scripts don't execute

Ensure Python scripts are executable:

```bash
chmod +x ~/.claude/skills/jira/scripts/jira.py
chmod +x ~/.claude/skills/confluence/scripts/confluence.py
```

### Import errors in tests

If you're a developer and tests fail with import errors:

Update import paths:
```python
# Old
from skills.jira import jira

# New
from skills.jira.scripts import jira
```

## Getting Help

### Documentation

- **[User Guide](user-guide.md)** - Installation and usage
- **[Developer Guide](developer-guide.md)** - Development and architecture
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

### Skill Documentation

- [Jira SKILL.md](skills/jira/SKILL.md) - Jira skill documentation
- [Confluence SKILL.md](skills/confluence/SKILL.md) - Confluence skill documentation

### Support

- **Issues**: [GitHub Issues](https://github.com/odyssey4me/agent-skills/issues)
- **Discussions**: [GitHub Discussions](https://github.com/odyssey4me/agent-skills/discussions)

## Summary

### Key Changes

1. ✅ Scripts moved to `scripts/` subdirectory
2. ✅ References moved to `references/` subdirectory
3. ✅ YAML frontmatter added to SKILL.md
4. ✅ Compatible with `npx add-skill`

### What Stayed the Same

1. ✅ Configuration files and environment variables
2. ✅ Command-line arguments and usage
3. ✅ Authentication methods
4. ✅ API functionality
5. ✅ Python dependencies

### Migration Checklist

- [ ] Backup configuration files
- [ ] Remove or update old skill installations
- [ ] Install v0.2.0 (via `npx add-skill` or manual download)
- [ ] Restore configuration
- [ ] Update script paths in aliases/scripts
- [ ] Run `check` command to verify
- [ ] Update tests (developers only)

Welcome to v0.2.0! 🎉