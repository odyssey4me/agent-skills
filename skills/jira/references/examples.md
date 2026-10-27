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
  --security-level "Internal"

# Verify comment was added
$SKILL_DIR/scripts/jira.py issue comments DEMO-123 --max-results 1
```

## View Comments on an Issue

```bash
$SKILL_DIR/scripts/jira.py issue comments DEMO-123
```

## Find Issues by Contributor

```bash
# Find all issues where jsmith reported, is assigned to, or updated
$SKILL_DIR/scripts/jira.py search --contributor "jsmith" --project DEMO
```

## Find Collaborative Epics

```bash
# Find epics in DEMO project with 2+ contributors
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO

# Require at least 3 contributors
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO --min-contributors 3

# Quarter retrospective: closed epics included, bounded by resolution date
$SKILL_DIR/scripts/jira.py collaboration epics --project DEMO \
  --contributor "jane@example.com" --date-field resolved \
  --since 2026-07-01 --until 2026-09-30 --include-done
```

Done epics are excluded by default. `--include-done` includes them, and
`--status Closed,Done` narrows to specific statuses instead.

## Search with Specific Fields

```bash
$SKILL_DIR/scripts/jira.py search \
  "project = DEMO AND created >= -7d" \
  --fields "key,summary,status,assignee,created"
```

## Collect Comment Authors in Bulk

Request the `comment` field instead of calling `issue comments` once per
issue. A single search returns the comment authors inline and cuts a crawl
from one call per issue to one call per page.

```bash
$SKILL_DIR/scripts/jira.py search \
  "project = DEMO AND statusCategory = Done" \
  --fields key,comment --json
```

Each issue carries `fields.comment.comments` (with `author`) and
`fields.comment.total`. The field is a bounded page, so compare `total` with
`len(comments)` before treating the author list as complete; when they
differ, fetch the issue's full thread with `issue comments`.

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
# Automatically applies security_level="Internal"

# Override defaults when needed
$SKILL_DIR/scripts/jira.py search "status = Open" --max-results 100
# CLI argument overrides the configured default of 25
```
