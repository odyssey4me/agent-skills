# ScriptRunner Enhanced Search Guide

ScriptRunner Enhanced Search provides advanced JQL functions for complex queries that aren't possible with standard JQL.

## Availability

ScriptRunner works differently depending on your Jira deployment:

- **Cloud**: Atlassian Marketplace app with REST API endpoints
- **Data Center/Server**: Self-hosted plugin with different API structure

The Jira skill automatically detects your deployment type and validates ScriptRunner availability.

## User Lookup for Advanced Queries

Many ScriptRunner functions require user identifiers. Users are typically known by email or username, not internal account IDs.

### Finding User Account IDs

Before using user-based ScriptRunner functions, look up the user's account ID:

```bash
# Search for user by email or display name
python jira.py search "assignee = 'user@example.com'"

# Or use Jira's user search API
# The response includes accountId field needed for ScriptRunner queries
```

**Note**: In Cloud, users are identified by `accountId`. In Data Center/Server, they may use `username` or `key`.

## Available Functions

### Link-Related Functions

Find issues based on link relationships:

```bash
# Find all issues linked to a specific issue
python jira.py search 'issue in linkedIssuesOf("DEMO-123")'

# Find all linked issues recursively (includes links of links)
python jira.py search 'issue in linkedIssuesOfAll("DEMO-123")'

# Find issues with specific link types
python jira.py search 'issue in hasLinkType("Dependency")'
python jira.py search 'issue in hasLinkType("Blocks")'
python jira.py search 'issue in hasLinkType("Relates")'

# Find issues that have any links
python jira.py search 'issue in hasLinks()'

# Find issues with remote links (external URLs)
python jira.py search 'issue in issuesWithRemoteLinks()'
python jira.py search 'issue in hasRemoteLinks()'
```

**Common link types:**
- `Blocks` / `is blocked by`
- `Dependency` / `depends on`
- `Relates` / `relates to`
- `Cloners` / `is cloned by`
- `Duplicate` / `duplicates`

### Hierarchy Functions

Navigate parent/child and epic relationships:

```bash
# Find all subtasks of an issue
python jira.py search 'issue in subtasksOf("DEMO-123")'

# Find parent issues
python jira.py search 'issue in parentsOf("DEMO-456")'

# Find issues that have subtasks
python jira.py search 'project = DEMO AND issue in hasSubtasks()'

# Find the epic for specific issues
python jira.py search 'issue in epicsOf("DEMO-123")'

# Find all issues in specific epics
python jira.py search 'issue in issuesInEpics("EPIC-123")'
python jira.py search 'issue in issuesInEpics("EPIC-123", "EPIC-456")'
```

### Comment and User Activity Functions

Find issues based on comments and user interactions:

```bash
# IMPORTANT: First look up the user's account ID
# For Cloud (uses accountId):
python jira.py search "assignee = 'user@example.com'" --fields accountId
# Note the accountId from the response, e.g., "5b10a2844c20165700ede21g"

# Then use it in ScriptRunner queries:
python jira.py search 'issue in commentedByUser("5b10a2844c20165700ede21g")'

# For Data Center/Server (uses username):
python jira.py search 'issue in commentedByUser("jsmith")'

# Find issues that have comments
python jira.py search 'issue in issuesWithComments()'

# Find issues last updated by a user
python jira.py search 'issue in lastUpdatedBy("5b10a2844c20165700ede21g")'
```

**Workflow for finding issues commented on by a user:**

1. Identify the user by a known attribute (email, display name)
2. Look up their `accountId` (Cloud) or `username` (DC/Server)
3. Use the identifier in ScriptRunner query

Example:
```bash
# Step 1: Find the user's account ID
python jira.py search "assignee = 'john.smith@example.com'" --fields accountId --max-results 1

# Step 2: Use the account ID in ScriptRunner query
python jira.py search 'issue in commentedByUser("5b10a2844c20165700ede21g") AND project = DEMO'
```

### Workflow Transition Functions

Track issue status changes:

```bash
# Find issues that have been transitioned
python jira.py search 'issue in transitionedIssues()'

# Find issues transitioned by a specific user
python jira.py search 'issue in transitionedBy("5b10a2844c20165700ede21g")'

# Find issues transitioned from a specific status
python jira.py search 'issue in transitionedFrom("In Progress")'

# Find issues transitioned to a specific status
python jira.py search 'issue in transitionedTo("Done")'

# Combine for complex queries
python jira.py search 'issue in transitionedFrom("In Progress") AND issue in transitionedTo("Done") AND updated >= -7d'
```

### Field-Based Functions

Query based on custom field values:

```bash
# Find issues with specific field values
python jira.py search 'issue in issuesWithFieldValue("customfield_10001", "value")'

# Find issues that have a value in a specific field
python jira.py search 'issue in hasFieldValue("Story Points")'

# Find recently updated issues
python jira.py search 'issue in lastUpdated("7d")'
```

### General Purpose Functions

Advanced expression-based queries:

```bash
# Use custom expressions (advanced)
python jira.py search 'issue in expression("issue.assignee == currentUser()")'

# Search issues with custom logic
python jira.py search 'issue in searchIssues("project = DEMO AND priority = High")'
```

## Practical Examples

### Find all dependencies for a feature

```bash
# Find all issues that DEMO-123 depends on
python jira.py search 'issue in linkedIssuesOf("DEMO-123") AND issuelinktype = "Dependency"'

# Find what depends on DEMO-123
python jira.py search 'issue in linkedIssuesOf("DEMO-123") AND issuelinktype = "is depended on by"'
```

### Track epic progress

```bash
# Find all incomplete issues in an epic
python jira.py search 'issue in issuesInEpics("EPIC-123") AND status != Done'

# Count subtasks by status
python jira.py search 'issue in subtasksOf("STORY-456") AND status = "In Progress"'
```

### Audit user activity

```bash
# Find all issues a user commented on this week
# (First look up accountId as shown in Comment Functions section)
python jira.py search 'issue in commentedByUser("ACCOUNT_ID") AND updated >= -7d'

# Find issues transitioned by a user today
python jira.py search 'issue in transitionedBy("ACCOUNT_ID") AND updated >= startOfDay()'
```

### Find blocked work

```bash
# Find all issues blocked by open issues
python jira.py search 'issuelinktype = "is blocked by" AND issue in linkedIssuesOf(status = Open)'
```

## Troubleshooting

### Function Not Found Error

**Error**: `Function 'linkedIssuesOf' not found`

**Solution**: ScriptRunner is not installed on your Jira instance. Check with:
```bash
python jira.py check
```

If ScriptRunner is not detected, install it from:
- **Cloud**: [Atlassian Marketplace](https://marketplace.atlassian.com/apps/6820/scriptrunner-for-jira)
- **Data Center/Server**: Install via Universal Plugin Manager (UPM)

### Invalid User Identifier

**Error**: Query returns no results or "User not found"

**Solution**: Verify you're using the correct identifier type:
- **Cloud**: Use `accountId` (e.g., `"5b10a2844c20165700ede21g"`)
- **Data Center/Server**: Use `username` (e.g., `"jsmith"`)

Look up the user first:
```bash
python jira.py search "assignee = 'user@example.com'" --fields accountId,name
```

### Performance Issues

**Tip**: ScriptRunner functions can be slow on large instances. Combine with filters:

```bash
# Good: Scoped to recent issues
python jira.py search 'issue in linkedIssuesOf("DEMO-123") AND updated >= -30d'

# Less optimal: Scans all history
python jira.py search 'issue in linkedIssuesOf("DEMO-123")'
```

## Reference

For complete ScriptRunner documentation, see:
- [ScriptRunner JQL Functions Reference](https://docs.adaptavist.com/sr4js/latest/features/jql-functions)
- [Cloud vs Server Differences](https://docs.adaptavist.com/sr4js/latest/cloud-vs-dc-server)
