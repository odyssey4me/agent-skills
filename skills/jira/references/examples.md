# Jira Skill Examples

Detailed usage examples for common Jira workflows.

## Find My Open Issues

```bash
$SKILL_DIR/scripts/jira.py search "assignee = currentUser() AND status != Done ORDER BY priority DESC"
```

## Create a Bug Report

```bash
# Create the bug
$SKILL_DIR/scripts/jira.py issue create \
  --project DEMO \
  --type Bug \
  --summary "Login button not working" \
  --description "The login button on the homepage does not respond to clicks."

# Verify it was created correctly
$SKILL_DIR/scripts/jira.py issue get DEMO-456
```

## Move Issue Through Workflow

```bash
# Check available transitions first
$SKILL_DIR/scripts/jira.py transitions list DEMO-123

# Start work on an issue
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "In Progress"

# Verify the transition
$SKILL_DIR/scripts/jira.py issue get DEMO-123 --fields "summary,status"

# Complete the issue
$SKILL_DIR/scripts/jira.py transitions do DEMO-123 "Done" --comment "Implemented and tested"

# Verify completion
$SKILL_DIR/scripts/jira.py issue get DEMO-123 --fields "summary,status"
```

## Add Private Comment

```bash
# Add comment visible only to specific security level
$SKILL_DIR/scripts/jira.py issue comment DEMO-123 \
  "This is sensitive internal information" \
  --security-level "Red Hat Internal"

# Verify comment was added
$SKILL_DIR/scripts/jira.py issue comments DEMO-123 --max-results 1
```

## View Comments on an Issue

```bash
$SKILL_DIR/scripts/jira.py issue comments DEMO-123
```

## Find Issues by Contributor

```bash
# Find all issues where jsmith is reporter, assignee, or commenter
$SKILL_DIR/scripts/jira.py search --contributor "jsmith" --project DEMO
```

## Find Collaborative Epics

```bash
# Find epics in DEMO project with 2+ assignees on child issues
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO

# Require at least 3 contributors
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO --min-contributors 3
```

## Search with Specific Fields

```bash
$SKILL_DIR/scripts/jira.py search \
  "project = DEMO AND created >= -7d" \
  --fields "key,summary,status,assignee,created"
```

## Using Configuration Defaults

With defaults configured (see SKILL.md [Configuration Defaults](#configuration-defaults)):

```bash
# Search uses JQL scope automatically
$SKILL_DIR/scripts/jira.py search "status = Open"
# Becomes: (project = DEMO AND assignee = currentUser()) AND (status = Open)

# Create issue uses project defaults
$SKILL_DIR/scripts/jira.py issue create --project DEMO --summary "Fix login bug"
# Automatically uses issue_type="Task" and priority="Medium" from DEMO defaults

# Comments use default security level
$SKILL_DIR/scripts/jira.py issue comment DEMO-123 "Internal note"
# Automatically applies security_level="Red Hat Internal"

# Override defaults when needed
$SKILL_DIR/scripts/jira.py search "status = Open" --max-results 100
# CLI argument overrides the configured default of 25
```
