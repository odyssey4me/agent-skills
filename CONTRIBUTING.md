# Contributing to Agent Skills

Thank you for your interest in contributing to Agent Skills. This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or later
- Git

### Setting Up the Development Environment

**Always use a virtual environment.** This ensures isolation from the host system.

```bash
# Clone the repository
git clone https://github.com/odyssey4me/agent-skills.git
cd agent-skills

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install development dependencies
pip install -e ".[dev]"
```

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
pytest tests/ -v --cov=shared --cov=skills --cov=scripts --cov-fail-under=80

# Validate skill structure
python scripts/validate_skill.py skills/*
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
│   ├── SKILL.md            # Skill instructions and commands
│   └── scripts/            # Python helper scripts
├── shared/                 # Shared utilities
│   ├── auth/               # Authentication (keyring, OAuth)
│   ├── http.py             # HTTP request utilities
│   └── output.py           # Output formatting
├── scripts/                # Repository utilities
│   ├── setup_auth.py       # Interactive auth setup
│   └── validate_skill.py   # Skill structure validation
├── templates/api-skill/    # Template for new skills
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## Adding a New Skill

1. Copy the template:
   ```bash
   cp -r templates/api-skill skills/<skill-name>
   ```

2. Update `skills/<skill-name>/SKILL.md` with:
   - Skill description
   - Authentication requirements
   - Available commands
   - Usage examples

3. Implement scripts in `skills/<skill-name>/scripts/`

4. Add tests in `tests/test_<skill-name>.py`

5. Validate structure:
   ```bash
   python scripts/validate_skill.py skills/<skill-name>
   ```

6. Update the skills table in `AGENTS.md` and `README.md`

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
