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

## Cloud-native JQL

Jira Cloud silently ignores JQL functions it does not recognise and returns
a successful empty result, so queries must use documented Cloud functions.
The script rejects the removed functions below with an error naming the
Cloud-native replacement.

| Removed function | Cloud-native replacement |
|-------------------|---------------------------|
| `linkedIssuesOf`, `linkedIssuesOfAll`, `linkedIssuesOfRecursive` | `issue in linkedWorkItems("KEY")`; walk links iteratively for recursion |
| `hasLinks`, `hasLinkType` | No project-wide equivalent; `issue in linkedWorkItems("KEY", "Link type")` when a key is known, otherwise filter the `issuelinks` field locally |
| `issuesWithRemoteLinks`, `hasRemoteLinks` | No general equivalent; read remote links per issue |
| `subtasksOf` | `parent = KEY` |
| `parentsOf` | `issue get KEY --fields parent` |
| `hasSubtasks` | `parent is not EMPTY` finds children; invert the result for parents |
| `epicsOf` | Read `fields.parent`; `parentEpic = KEY` is the forward direction |
| `issuesInEpics` | `parentEpic = KEY` or `parentEpic in (K1, K2)` |
| `commentedByUser` | `issue in updatedBy("user")` |
| `lastUpdatedBy` | `issue in updatedBy("user")` |
| `issuesWithComments` | No equivalent; request the comment field and filter locally |
| `transitionedIssues` | `status CHANGED` |
| `transitionedBy` | `status CHANGED BY "user"` |
| `transitionedFrom` | `status CHANGED FROM "Status"` |
| `transitionedTo` | `status CHANGED TO "Status"` |
| `issuesWithFieldValue` | `"Field" = value` |
| `hasFieldValue` | `"Field" is not EMPTY` |
| `lastUpdated("7d")` | `updated >= -7d` |
| `expression`, `searchIssues` | No JQL equivalent; compute outside Jira or run a separate search |

### Finding linked issues

`issue in linkedWorkItems("PROJ-123")` returns the issues linked to
PROJ-123. Add a link type to narrow the search:
`issue in linkedWorkItems("PROJ-123", "Blocks")`. To walk links
recursively, search the linked issues and query their links in turn.

### Finding subtasks

`parent = PROJ-123` returns the subtasks of PROJ-123.

### Finding parent issues

Use `issue get PROJ-123 --fields parent` to read the parent directly.

### Finding epic children

`parentEpic = EPIC-123` returns the children of an epic. Use
`parentEpic in (EPIC-123, EPIC-456)` to cover several epics.

### Finding issues by commenter

`issue in updatedBy("user")` returns issues the user updated, including
comments, field edits, and transitions. To find issues with comments only,
request the comment field and filter locally. The `--contributor` search
flag combines reporter, assignee, and updater in one query.
