# Developer Guide

Complete guide for developing agent skills and contributing to this repository.

## Table of Contents

- [Architecture](#architecture)
- [Why Python?](#why-python)
- [Repository Structure](#repository-structure)
- [Development Setup](#development-setup)
- [Creating New Skills](#creating-new-skills)
- [Design Guidelines](#design-guidelines)
- [Testing and Validation](#testing-and-validation)
- [References](#references)

## Architecture

This repository implements the [Agent Skills specification](https://agentskills.io/specification), a standard for creating portable, discoverable tools for AI coding assistants.

### Implementation Decisions

Our implementation follows the specification while making specific choices optimized for production use:

1. **Python scripts** - Not Bash (explained in [Why Python?](#why-python))
2. **Self-contained** - Each skill is independently distributable
3. **Progressive disclosure** - Minimizes context usage per specification
4. **Inlined utilities** - No shared dependencies between skills

Each decision is justified with references to the specification and practical requirements.

### How Skills Work

Skills follow the **progressive disclosure** principle defined in the spec:

1. **Discovery**: AI agents discover skills by reading YAML frontmatter
   - Only `name` and `description` are initially loaded
   - See: [Spec - Frontmatter](https://agentskills.io/specification#frontmatter)

2. **Activation**: When activated, full SKILL.md content loads
   - Complete command documentation
   - Usage examples
   - See: [Spec - SKILL.md](https://agentskills.io/specification#skill-md)

3. **On-Demand Loading**: Additional documentation in `references/` loads only when needed
   - Supplementary guides
   - Advanced topics
   - See: [Spec - References](https://agentskills.io/specification#references)

This minimizes context usage and improves AI agent performance.

## Why Python?

The Agent Skills specification **explicitly supports multiple languages**:

> "Common options include Python, Bash, and JavaScript"
> — [Agent Skills Specification](https://agentskills.io/specification#scripts)

While many examples use Bash (see [Vercel's agent-skills](https://github.com/vercel-labs/agent-skills)), Python is a valid and recommended choice for complex integrations.

### Rationale for Python

**Complex API Interactions**
- OAuth flows and token management
- JSON parsing and manipulation
- Pagination handling
- Request/response transformation

**Better Error Handling**
- Structured exception handling
- Type safety with type hints
- Comprehensive logging
- Graceful degradation

**Rich Ecosystem**
- `requests` - HTTP client with session management
- `keyring` - Secure credential storage
- `pyyaml` - Configuration parsing
- Standard library batteries included

**Maintainability**
- Easier to test and debug
- Better IDE support
- Self-documenting with type hints
- Familiar to most developers

**Proven in Production**
- Anthropic's own examples use Python (e.g., [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) with `scripts/rotate_pdf.py`)
- Production-grade API clients
- Enterprise authentication patterns

### When to Use Bash vs Python

**Use Bash for:**
- Simple file operations
- Git commands
- Shell tool integration
- Quick utilities

**Use Python for:**
- API integrations (REST, GraphQL)
- Complex data transformations
- OAuth/authentication flows
- Multi-step workflows

Our skills (Jira, Confluence, Gmail) are API-heavy, making Python the right choice.

## Repository Structure

```
agent-skills/
├── skills/                    # Individual skills
│   ├── jira/
│   │   ├── SKILL.md          # Documentation with YAML frontmatter (spec-required)
│   │   ├── scripts/          # Executable scripts (spec-required location)
│   │   │   └── jira.py       # Self-contained Python script
│   │   └── references/       # Additional documentation (spec-optional)
│   │       └── scriptrunner.md
│   ├── confluence/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── confluence.py
│   │   └── references/
│   │       └── creating-content.md
│   └── gmail/
│       ├── SKILL.md
│       ├── scripts/
│       │   └── gmail.py
│       └── references/
│           ├── oauth-setup.md
│           └── gmail-queries.md
├── templates/                 # Templates for new skills
│   └── api-skill/
│       ├── SKILL.md.template
│       └── scripts/
│           └── skill.py.template
├── scripts/                   # Development utilities
│   ├── validate_skill.py     # Validates skill structure and frontmatter
│   └── setup_helper.py       # Setup and configuration helpers
├── tests/                     # Test suite
│   ├── test_jira.py
│   ├── test_confluence.py
│   └── test_gmail.py
├── docs/                      # Documentation
│   ├── user-guide.md          # User installation and setup guide
│   └── developer-guide.md (this file)
├── AGENTS.md                  # Instructions for AI coding assistants
├── CONTRIBUTING.md            # Contribution guidelines
└── README.md                  # Project overview
```

### Mapping to Specification

| Our Structure | Spec Requirement | Reference |
|---------------|------------------|-----------|
| `SKILL.md` with frontmatter | Required | [Spec - SKILL.md](https://agentskills.io/specification#skill-md) |
| `scripts/` directory | Required | [Spec - Scripts](https://agentskills.io/specification#scripts) |
| `references/` directory | Optional | [Spec - References](https://agentskills.io/specification#references) |
| YAML frontmatter (`name`, `description`) | Required | [Spec - Frontmatter](https://agentskills.io/specification#frontmatter) |

## Development Setup

### Prerequisites

- Python 3.10 or later
- Git
- `pip` package manager

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Development Dependencies

The `[dev]` extra installs:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `ruff` - Linting and formatting
- `requests`, `keyring`, `pyyaml` - Skill dependencies

### Verify Setup

```bash
# Run tests
pytest tests/ -v

# Lint code
ruff check .

# Format code
ruff format .

# Validate skill structure
python scripts/validate_skill.py skills/jira
```

## Creating New Skills

### Step 1: Copy Template

```bash
cp -r templates/api-skill skills/myskill
cd skills/myskill
```

### Step 2: Rename and Configure

1. Create `scripts/` directory:
   ```bash
   mkdir -p scripts
   ```

2. Rename template:
   ```bash
   mv scripts/skill.py.template scripts/myskill.py
   ```

3. Update SKILL.md frontmatter:
   ```yaml
   ---
   name: myskill
   description: Brief description for AI agents to understand when to use this skill
   metadata:
     author: your-github-username
     version: "0.1.0"
   license: Apache-2.0
   ---
   ```

### Step 3: Implement Functionality

Edit `scripts/myskill.py` following these patterns:

**Required Components:**

1. **Authentication handling** (keyring, env vars, config file)
2. **`check` subcommand** for setup verification
3. **Subcommands** for each major operation
4. **Error handling** with helpful messages
5. **`--help` documentation** for all commands

**Script Structure:**

```python
#!/usr/bin/env python3
"""
MySkill - Brief description

Self-contained skill for AI coding assistants.
"""

import argparse
import sys
from typing import Optional

# Inlined utilities (don't import from shared code)
class AuthManager:
    """Handle authentication from keyring, env vars, or config file."""
    pass

class SkillClient:
    """Main client for interacting with the service."""
    pass

def cmd_check(args):
    """Verify setup and configuration."""
    # Check dependencies
    # Verify authentication
    # Test connectivity
    pass

def cmd_operation(args):
    """Perform main operation."""
    pass

def main():
    parser = argparse.ArgumentParser(description="MySkill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check subcommand
    parser_check = subparsers.add_parser("check", help="Verify setup")
    parser_check.set_defaults(func=cmd_check)

    # operation subcommand
    parser_op = subparsers.add_parser("operation", help="Do something")
    parser_op.add_argument("arg", help="Required argument")
    parser_op.set_defaults(func=cmd_operation)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
```

### Step 4: Write Documentation

Update `SKILL.md` following this structure:

```markdown
---
name: myskill
description: One-line description for discovery
metadata:
  author: username
  version: "0.1.0"
license: Apache-2.0
---

# MySkill

Brief description of what this skill does.

## Installation

Installation instructions...

## Setup Verification

```bash
python scripts/myskill.py check
```

## Authentication

How to configure credentials...

## Commands

### check
Verification command...

### operation
Main operations...

## Examples

Practical examples...

## Troubleshooting

Common issues and solutions...
```

### Step 5: Add Tests

Create `tests/test_myskill.py`:

```python
import pytest
from skills.myskill.scripts import myskill

def test_auth_manager():
    """Test authentication handling."""
    pass

def test_check_command():
    """Test check command."""
    pass
```

### Step 6: Validate

```bash
# Validate skill structure and frontmatter
python scripts/validate_skill.py skills/myskill

# Run tests
pytest tests/test_myskill.py -v

# Test manually
python skills/myskill/scripts/myskill.py --help
python skills/myskill/scripts/myskill.py check
```

## Design Guidelines

### Self-Contained Scripts

**Principle**: Each skill must work independently without shared dependencies.

**Why**:
- Skills can be distributed individually
- No version conflicts between skills
- Simple installation (just download and run)

**Implementation**:
- Inline all utilities within the script
- Don't import from `../shared` or other skills
- Only depend on `requests`, `keyring`, `pyyaml`, stdlib

**Example**:
```python
# ❌ Bad - external dependency
from shared.auth import AuthManager

# ✅ Good - inlined
class AuthManager:
    """Authentication handling inlined in this skill."""
    pass
```

### Progressive Disclosure

**Principle**: Minimize context usage by loading information on-demand.

**Why**: Per [spec](https://agentskills.io/specification#progressive-disclosure), AI agents work better with less context.

**Implementation**:
1. **Frontmatter**: Only `name` and `description` (always loaded)
2. **SKILL.md**: Full documentation (loaded when skill activated)
3. **references/**: Detailed guides (loaded when explicitly referenced)

**Example**:
```yaml
---
name: jira
description: Search and manage Jira issues using JQL queries, create/update issues, and manage workflows
---
```

Keep `description` concise (one sentence) but informative enough for the AI to know when to use the skill.

### CLI Design Patterns

**Use subcommands** like `git`, `docker`, `kubectl`:

```bash
# Good
python scripts/jira.py search "JQL query"
python scripts/jira.py issue create --project DEMO --summary "Title"
python scripts/jira.py transitions list DEMO-123

# Avoid
python scripts/jira-search.py "JQL query"
python scripts/jira-issue-create.py --project DEMO --summary "Title"
```

**Always include a `check` subcommand**:

```bash
python scripts/myskill.py check
```

It should verify:
- Dependencies installed
- Authentication configured
- Service connectivity
- Provide actionable error messages

### Error Handling

**Provide context and solutions**:

```python
# ❌ Bad
raise Exception("Auth failed")

# ✅ Good
print("ERROR: Authentication failed", file=sys.stderr)
print("", file=sys.stderr)
print("Please configure authentication:", file=sys.stderr)
print("  export JIRA_BASE_URL='https://your-company.atlassian.net'", file=sys.stderr)
print("  export JIRA_EMAIL='you@example.com'", file=sys.stderr)
print("  export JIRA_API_TOKEN='your-token'", file=sys.stderr)
print("", file=sys.stderr)
print("Or create ~/.config/agent-skills/jira.yaml", file=sys.stderr)
sys.exit(1)
```

### Configuration Hierarchy

Support multiple configuration methods (checked in order):

1. **CLI arguments** (highest priority)
2. **Environment variables**
3. **Config file** (`~/.config/agent-skills/<skill>.yaml`)
4. **Default values** (lowest priority)

```python
def get_base_url(args):
    return (
        args.url or                                    # CLI argument
        os.environ.get("JIRA_BASE_URL") or            # Environment variable
        config.get("url") or                           # Config file
        "https://jira.example.com"                     # Default
    )
```

## Testing and Validation

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific skill
pytest tests/test_jira.py -v

# With coverage
pytest tests/ --cov=skills --cov-report=html

# Coverage threshold
pytest tests/ --cov=skills --cov-fail-under=50
```

### Skill Structure Validation

```bash
# Validate single skill
python scripts/validate_skill.py skills/jira

# Validate all skills
python scripts/validate_skill.py skills/*
```

The validator checks:
- YAML frontmatter exists and is valid
- Required fields present (`name`, `description`)
- `scripts/` directory exists
- Script files are executable
- SKILL.md has proper structure

### Manual Testing

Test each command manually:

```bash
# Help output
python skills/myskill/scripts/myskill.py --help
python skills/myskill/scripts/myskill.py check --help

# Check command
python skills/myskill/scripts/myskill.py check

# Main operations
python skills/myskill/scripts/myskill.py operation arg
```

### Testing with npx add-skill

Verify compatibility with the installation tool:

```bash
# List skills (should show your skill)
npx add-skill odyssey4me/agent-skills --list

# Install skill
npx add-skill odyssey4me/agent-skills --skill myskill

# Verify installation
ls ~/.claude/skills/myskill
```

## References

### Official Specifications

- **[Agent Skills Specification](https://agentskills.io/specification)** - The standard we implement
  - [Frontmatter format](https://agentskills.io/specification#frontmatter)
  - [Directory structure](https://agentskills.io/specification#structure)
  - [Progressive disclosure](https://agentskills.io/specification#progressive-disclosure)

### Reference Implementations

- **[Vercel agent-skills](https://github.com/vercel-labs/agent-skills)** - Reference implementation (Bash-based)
  - See their AGENTS.md for implementation patterns
  - Skills follow similar structure with Bash scripts

- **[Anthropic skills](https://github.com/anthropics/skills)** - Claude-focused examples
  - [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) - Python example
  - Shows `scripts/rotate_pdf.py` implementation

### Tools

- **[add-skill CLI](https://github.com/vercel-labs/add-skill)** - Installation tool
  - How skill discovery works
  - Installation process
  - Symlink mode

### Tutorials and Articles

- [Agent Skills in 100 lines of Python](https://www.jairtrejo.com/blog/2026/01/agent-skills) - Minimal implementation
- [How to Write and Implement Agent Skills - DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-implement-agent-skills)
- [How to Use Vercel Agent-Skills - Apidog](https://apidog.com/blog/vercel-agent-skills/)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Testing requirements
- Commit message format

## Next Steps

- Read the [Agent Skills specification](https://agentskills.io/specification)
- Review existing skills ([Jira](../skills/jira/SKILL.md), [Confluence](../skills/confluence/SKILL.md), [Gmail](../skills/gmail/SKILL.md))
- Copy the template and start building
- Test with `npx add-skill` for compatibility
- Submit a pull request

For questions, [open an issue on GitHub](https://github.com/odyssey4me/agent-skills/issues).
