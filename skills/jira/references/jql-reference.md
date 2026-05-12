# JQL Reference

Common JQL queries for use with the Jira skill.

## Basic Queries

| Query | Description |
|-------|-------------|
| `project = DEMO` | Issues in DEMO project |
| `assignee = currentUser()` | Issues assigned to you |
| `status = "In Progress"` | Issues in progress |
| `created >= -7d` | Created in last 7 days |
| `updated >= startOfDay()` | Updated today |
| `priority = High` | High priority issues |
| `labels = "bug"` | Issues with "bug" label |

Combine with `AND`, `OR`, and use `ORDER BY` for sorting.

## Status Categories

Jira organizes all statuses into three categories. Use `statusCategory` for
queries that work across projects:

| Category | Meaning | Example Statuses |
|----------|---------|------------------|
| To Do | Not started | Open, Backlog, New |
| In Progress | Being worked on | In Development, In Review |
| Done | Completed | Closed, Resolved, Done |

**Example:** Instead of `status = "Open" OR status = "Backlog"`, use
`statusCategory = "To Do"`.

Use `$SKILL_DIR/scripts/jira.py statuses --categories` to see all status
categories in your Jira instance.

## Date Functions

| Function | Description |
|----------|-------------|
| `startOfDay()` | Start of today |
| `endOfDay()` | End of today |
| `startOfWeek()` | Start of current week |
| `startOfMonth()` | Start of current month |
| `-7d` | Relative: 7 days ago |
| `-4w` | Relative: 4 weeks ago |

## Useful Patterns

```jql
# My open issues, highest priority first
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC

# Recently updated in a project
project = DEMO AND updated >= -7d ORDER BY updated DESC

# Unassigned bugs
project = DEMO AND issuetype = Bug AND assignee is EMPTY

# Issues created this sprint
project = DEMO AND sprint in openSprints()

# High priority items not yet started
priority in (High, Highest) AND statusCategory = "To Do"
```

## Cloud Alternatives

These standard JQL patterns replace ScriptRunner functions that are
only available on Data Center/Server.

### Finding linked issues

ScriptRunner: `issue in linkedIssuesOf("PROJ-123")`

Cloud alternative: Use `issue get PROJ-123` to read the issue's links,
then search by the linked issue keys directly.

### Finding subtasks

ScriptRunner: `issue in subtasksOf("PROJ-123")`

Cloud alternative: `parent = PROJ-123`

### Finding parent issues

ScriptRunner: `issue in parentsOf("PROJ-123")`

Cloud alternative: Use `issue get PROJ-123` to read the parent field.

### Finding epic children

ScriptRunner: `issue in issuesInEpics("EPIC-123")`

Cloud alternative: `"Epic Link" = EPIC-123` or `parentEpic = EPIC-123`

### Finding issues by commenter

ScriptRunner: `issue in commentedByUser("accountId")`

Cloud alternative: No direct JQL equivalent. Use the `--contributor`
flag which searches reporter and assignee fields.
