# Contributing to Agent Skills

Thank you for your interest in contributing to Agent Skills. This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or later
- Git

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills

# Install development dependencies
pip install -e ".[dev]"
```

**Note**: Skills themselves have no dependencies on this package. They only require `requests`, `keyring`, and `pyyaml` which are installed as dev dependencies.

## Development Workflow

### Before Making Changes

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Ensure tests pass:
   ```bash
   pytest tests/ -v
   ```

### Making Changes

1. Write your code following the code style guidelines
2. Add tests for new functionality
3. Update documentation as needed

### Code Style

- **Python version**: 3.10+
- **Formatting**: ruff (line-length 100)
- **Linting**: ruff
- **Type hints**: Required for all function signatures
- **Docstrings**: Google style
- **Test coverage**: Minimum 50% initially (goal: 80%)

### Running Checks

```bash
# Activate venv first
source .venv/bin/activate

# Lint and format
ruff check .
ruff format .

# Run tests with coverage
pytest tests/ -v --cov=skills --cov=scripts --cov-fail-under=50

# Validate skill structure
python scripts/validate_skill.py skills/*

# Test each skill's check command
python skills/jira/jira.py check
```

### Commit Messages

Use conventional commits:

```
type(scope): description

Examples:
feat(jira): add issue transition support
fix(auth): handle expired OAuth tokens
docs(readme): update installation instructions
test(jira): add tests for search functionality
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

## Project Structure

```
agent-skills/
├── skills/<name>/          # Skill implementations
│   ├── SKILL.md            # Skill documentation
│   └── <name>.py           # Self-contained skill script
├── scripts/                # Repository utilities
│   ├── setup_auth.py       # Optional interactive auth setup
│   └── validate_skill.py   # Skill structure validation
├── templates/api-skill/    # Template for new skills
├── tests/                  # Test suite
└── docs/                   # Documentation
```

**Note**: Each skill is self-contained with no dependencies on shared code.

## Adding a New Skill

Skills are self-contained Python scripts that work across AI agents.

### Skill Structure

```
skills/yourskill/
├── SKILL.md          # Documentation
└── yourskill.py      # Self-contained script
```

### Skill Guidelines

1. **Self-contained**: No imports from shared code or other skills
2. **Single file**: All functionality in one script with subcommands
3. **Dependencies**: Only use `requests`, `keyring`, `pyyaml`, and stdlib
4. **Authentication**: Support keyring, env vars, and config files with fallback chain
5. **CLI**: Use `argparse` with subcommands (like git, docker)
6. **Validation**: Include a `check` subcommand for setup verification
7. **Help**: Provide good `--help` output for all commands

### Creating a Skill

1. **Copy the template**:
   ```bash
   cp -r templates/api-skill skills/<skill-name>
   ```

2. **Edit the script**:
   - Rename `skill.py.template` to `<skill-name>.py`
   - Implement your functionality with all utilities inlined
   - Add a `check` subcommand that validates:
     - Python dependencies installed
     - Authentication configured
     - Service connectivity
     - Provides setup instructions if anything is missing

3. **Update documentation** (`skills/<skill-name>/SKILL.md`):
   - Document authentication requirements
   - Document all commands
   - Add usage examples
   - Include Setup Verification section showing `check` command

4. **Test the skill**:
   ```bash
   python skills/<skill-name>/<skill-name>.py --help
   python skills/<skill-name>/<skill-name>.py check
   ```

5. **Add tests** in `tests/test_<skill-name>.py`

6. **Validate structure**:
   ```bash
   python scripts/validate_skill.py skills/<skill-name>
   ```

7. **Update the skills table** in `README.md`

### Example Skill Structure

See [skills/jira/jira.py](skills/jira/jira.py) for a complete example of a self-contained skill with:
- Dependency checking
- Authentication utilities inlined
- HTTP utilities inlined
- Output formatting inlined
- Multiple subcommands
- Built-in `check` command

## Packaging and Distribution

Skills are distributed as tarballs via GitHub Releases. Each skill is packaged separately to maintain the multi-file structure.

### Package a Skill

```bash
cd skills
tar czf jira.tar.gz jira/
```

This creates a tarball containing:
```
jira/
├── SKILL.md
└── jira.py
```

### Creating a Release

1. **Tag the version**:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

2. **GitHub Actions automatically**:
   - Packages each skill in `skills/` as a tarball
   - Creates a GitHub Release
   - Attaches all skill tarballs to the release

3. **Or manually** attach tarballs to a GitHub Release

### Release Checklist

- [ ] All skills thoroughly tested
- [ ] All SKILL.md files updated
- [ ] Version bumped in `pyproject.toml`
- [ ] All tests passing
- [ ] CI checks passing
- [ ] Each skill's `check` command works

## Pull Request Process

1. Ensure all checks pass locally
2. Push your branch and create a pull request
3. Fill out the PR template with:
   - Summary of changes
   - Test plan
   - Related issues
4. Wait for CI to pass
5. Request review from maintainers

### PR Title Format

Use the same format as commit messages:

```
feat(jira): add issue transition support
```

## Reporting Issues

When reporting issues, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Minimal steps to reproduce the issue
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: OS, Python version, etc.

## Questions

For questions, open a GitHub issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
