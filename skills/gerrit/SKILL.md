---
name: gerrit
description: Submit, amend, and review Gerrit changes using git-review CLI. Use when asked to submit a patchset, download a change, rebase a change request, check CR status, or manage code reviews in Gerrit.
metadata:
  author: odyssey4me
  version: "0.2.0"
  category: code-hosting
  tags: "code-review, patches"
  complexity: lightweight
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/gerrit.py:*)
---

# Gerrit Skill

This skill provides Gerrit code review integration using `git-review` with a Python wrapper for markdown-formatted query output on read/view operations. Action commands (submit, review, abandon) should use `git-review` or SSH commands directly.

## Prerequisites

**Install git-review**: `pip install git-review` — [docs](https://docs.opendev.org/opendev/git-review/latest/installation.html)

## Authentication

git-review uses SSH for authentication with Gerrit servers.

```bash
# Configure Gerrit username (if different from local user)
git config --global gitreview.username yourgerrituser

# Test SSH connection
ssh -p 29418 youruser@review.example.com gerrit version

# Add SSH key to Gerrit
# 1. Generate SSH key if needed: ssh-keygen -t ed25519
# 2. Copy public key: cat ~/.ssh/id_ed25519.pub
# 3. Add to Gerrit: Settings > SSH Keys
```

Gerrit supports multiple authentication methods:
- **SSH** (recommended): Used by git-review for all operations
- **HTTP/HTTPS**: For web UI and REST API access (set password in Settings > HTTP Password)

See [Gerrit Authentication](https://gerrit-review.googlesource.com/Documentation/user-upload.html#ssh) for details.

## Initial Setup

### Configure Repository

```bash
# One-time setup for a repository
git review -s

# Or manually create .gitreview file in repository root
cat > .gitreview <<EOF
[gerrit]
host=review.example.com
port=29418
project=myproject
defaultbranch=main
EOF
```

See [Installation Guide](https://docs.opendev.org/opendev/git-review/latest/installation.html) for details.

## Script Usage

The wrapper script (`scripts/gerrit.py`) uses Gerrit SSH query commands and formats output as markdown. Connection details are read from `.gitreview` or provided via `--host`/`--port`/`--username` flags.

```bash
# Check Gerrit SSH access
$SKILL_DIR/scripts/gerrit.py check

# Changes
$SKILL_DIR/scripts/gerrit.py changes list
$SKILL_DIR/scripts/gerrit.py changes view 12345
$SKILL_DIR/scripts/gerrit.py changes search "status:open project:myproject"

# Projects
$SKILL_DIR/scripts/gerrit.py projects list
```

All commands support `--limit N` for list commands (default 30).

Global connection options: `--host`, `--port` (default 29418), `--username`.

## Commands (Direct git-review Usage)

For action commands, use `git-review` or SSH commands directly:

### Submitting Changes

```bash
git review                          # Submit current branch for review
git review -t topic-name            # Submit with topic
git review -f                       # Submit and close local branch
git review --reviewers user1,user2  # Add reviewers
git review -n                       # Dry-run (show what would be done)
```

Full reference: [git-review usage](https://docs.opendev.org/opendev/git-review/latest/usage.html)

### Downloading Changes

```bash
git review -d 12345                 # Download change 12345
git review -d 12345,3               # Download patchset 3 of change 12345
git review -x 12345                 # Cherry-pick change (no branch)
git review -m 12345                 # Compare local changes to remote
```

Downloads create a local branch named `review/username/topic`.

### Updating Changes

```bash
# Make changes to downloaded review
git commit --amend
git review                          # Upload new patchset

# Update to latest patchset
git review -d 12345                 # Re-download updates the branch
```

### Advanced Options

```bash
git review -R                       # Don't rebase (submit as-is)
git review -D                       # Draft mode (WIP changes)
git review --no-cache               # Skip local cache
git review -v                       # Verbose output
git review --track                  # Track remote branch
```

## Configuration

### Per-Repository Settings

File: `.gitreview` (repository root)
```ini
[gerrit]
host=review.example.com
port=29418
project=myproject/subproject
defaultbranch=main
defaultremote=origin
```

### Global Settings

```bash
# Set Gerrit username
git config --global gitreview.username myuser

# Set default remote
git config --global gitreview.remote gerrit

# Configure scheme (ssh/http/https)
git config --global gitreview.scheme ssh
```

Configuration stored in `~/.gitconfig`

## Examples

### Daily Workflow

```bash
# Start work on new feature
git checkout -b feature-branch
# ... make changes ...
git commit -m "Add new feature"

# Submit for review
git review -t feature-topic
# Verify submission
$SKILL_DIR/scripts/gerrit.py changes list  # confirm change appears

# Address review comments
# ... make changes ...
git commit --amend
git review
# Verify new patchset uploaded
$SKILL_DIR/scripts/gerrit.py changes view <change-number>
```

### Reviewing Others' Changes

```bash
# Download change for review
git review -d 12345
# Verify download
$SKILL_DIR/scripts/gerrit.py changes view 12345

# Test the change
# ... run tests, verify code ...

# Return to main branch
git checkout main
git branch -D review/user/topic
```

### Working with Topics

```bash
# Submit with topic
git review -t authentication-refactor
# Verify submission
$SKILL_DIR/scripts/gerrit.py changes list

# All related changes will be grouped under this topic
git commit -m "Part 2: Update tests"
git review -t authentication-refactor
```

See [common-workflows.md](references/common-workflows.md) for more examples.

## Advanced Usage

See [advanced-usage.md](references/advanced-usage.md) for SSH commands, JSON output, and multi-server configuration.

## Model Guidance

This skill wraps an official CLI. A fast, lightweight model is sufficient.

## Troubleshooting

See [troubleshooting.md](references/troubleshooting.md) for common issues and fixes.

## Official Documentation

- **git-review Manual**: <https://docs.opendev.org/opendev/git-review/latest/>
- **git-review Repository**: <https://opendev.org/opendev/git-review>
- **Gerrit Documentation**: <https://gerrit-review.googlesource.com/Documentation/>
- **Gerrit SSH Commands**: <https://gerrit-review.googlesource.com/Documentation/cmd-index.html>
