# Contributing to Agent Skills

Thank you for your interest in contributing!

**New to the project?** Read the [Developer Guide](docs/developer-guide.md) first - it covers architecture, design principles, and detailed implementation guidelines.

This document covers the essential workflow for contributing.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type pre-push

# Verify setup
pytest
ruff check .
```

**Prerequisites**: Python 3.10+, Git

## Standards

This repository implements the [Agent Skills specification](https://agentskills.io/specification). See the [Developer Guide - Architecture](docs/developer-guide.md#architecture) for how we apply the spec.

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow code style guidelines (below)
- Add tests for new functionality
- Update documentation

### 3. Run Checks

Pre-commit hooks automatically run before each commit and push:

**Before each commit:**
- `ruff check --fix` - Lints and auto-fixes code
- `ruff format` - Formats code
- `pytest tests/` - Runs all tests

**Before each push:**
- `pytest tests/ --cov` - Runs tests with coverage (must be ≥50%)

**Manual checks** (optional, hooks handle this):
```bash
# Lint and format
ruff check .
ruff format .

# Run tests with coverage
pytest tests/ -v --cov=skills --cov=scripts --cov-fail-under=50

# Validate skill structure
python scripts/validate_skill.py skills/*
```

### 4. Commit

Use [conventional commits](https://www.conventionalcommits.org/):

```
feat(jira): add issue transition support
fix(auth): handle expired OAuth tokens
docs(readme): update installation instructions
```

### 5. Submit PR

- Ensure CI passes
- Fill out PR template
- Request review

## Code Style

- **Python**: 3.10+
- **Formatting**: ruff (line-length 100)
- **Type hints**: Required for all function signatures
- **Docstrings**: Google style
- **Coverage**: Minimum 50% (goal: 80%)

## Creating a New Skill

See the [Developer Guide - Creating New Skills](docs/developer-guide.md#creating-new-skills) for complete instructions, structure requirements, and design guidelines.

**Quick commands**:
```bash
cp -r templates/api-skill skills/myskill
python skills/myskill/scripts/myskill.py check
python scripts/validate_skill.py skills/myskill
```

## Project Structure

See [Developer Guide - Repository Structure](docs/developer-guide.md#repository-structure) for the complete project structure and architecture details.

## Reporting Issues

Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version)

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Additional Resources

- **[Developer Guide](docs/developer-guide.md)** - Comprehensive development documentation
- **[User Guide](docs/user-guide.md)** - Installation and usage
- **[Agent Skills Specification](https://agentskills.io/specification)** - Standard we implement
- **[AGENTS.md](AGENTS.md)** - Instructions for AI coding assistants
