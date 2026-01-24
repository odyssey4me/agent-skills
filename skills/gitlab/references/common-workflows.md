# Common GitLab Workflows with glab CLI

This document provides practical examples of common GitLab workflows using the `glab` CLI.

## Table of Contents

- [Issue Management](#issue-management)
- [Merge Request Workflow](#merge-request-workflow)
- [CI/CD and Pipelines](#cicd-and-pipelines)
- [Repository Management](#repository-management)
- [Team Collaboration](#team-collaboration)
- [Automation Examples](#automation-examples)

## Issue Management

### Daily Issue Triage

Review and label new issues:

```bash
#!/bin/bash
# List unlabeled issues
glab issue list --label "" --output json | jq -r '.[] | "\(.iid) \(.title)"'

# For each issue, view and add labels
glab issue list --label "" --per-page 10 | while read issue; do
  issue_num=$(echo $issue | awk '{print $1}' | tr -d '#')
  glab issue view $issue_num
  echo "Add label (bug/enhancement/question/documentation/skip):"
  read label
  if [ "$label" != "skip" ]; then
    glab issue update $issue_num --label $label
  fi
done
```

### Close Stale Issues

Close issues inactive for over 90 days:

```bash
# List issues older than 90 days
glab issue list --state opened --output json | \
  jq -r --arg date "$(date -d '90 days ago' --iso-8601)" \
  '.[] | select(.updated_at < $date) | "\(.iid) \(.title)"'

# Close them with a comment
glab issue list --state opened --output json | \
  jq -r --arg date "$(date -d '90 days ago' --iso-8601)" \
  '.[] | select(.updated_at < $date) | .iid' | \
  while read num; do
    glab issue note $num --message "Closing due to inactivity. Please reopen if still relevant."
    glab issue close $num
  done
```

### Create Issue from Template

```bash
# Create issue with details
glab issue create \
  --title "Login fails with OAuth" \
  --description "Steps to reproduce: ..." \
  --label bug \
  --assignee @me
```

### Bulk Issue Operations

Add milestone to multiple issues:

```bash
# Find issues with label "v2.0"
glab issue list --label "v2.0" --output json | \
  jq -r '.[].iid' | \
  while read num; do
    glab issue update $num --milestone "2.0 Release"
  done
```

## Merge Request Workflow

### Create MR from Feature Branch

```bash
# Ensure you're on feature branch
git checkout -b feature/new-login

# Make changes and commit
git add .
git commit -m "feat: implement new login flow"

# Push branch
git push -u origin feature/new-login

# Create MR with auto-filled title/body from commits
glab mr create --fill

# Or with custom details
glab mr create \
  --title "Implement new login flow" \
  --description "This MR implements OAuth 2.0 login.

## Changes
- Add OAuth provider
- Update login UI
- Add tests

Closes #123" \
  --label enhancement \
  --assignee @reviewer1
```

### Review MRs Assigned to You

```bash
#!/bin/bash
# Daily MR review workflow

echo "=== MRs waiting for your review ==="
glab mr list --assignee=@me --output json | jq -r '.[] | "\(.iid) \(.title) (@\(.author.username))"'

# Review each MR
glab mr list --assignee=@me --output json | \
  jq -r '.[].iid' | \
  while read mr; do
    echo -e "\n=== Reviewing MR !$mr ==="

    # View MR details
    glab mr view $mr

    # View diff
    glab mr diff $mr

    # Checkout locally to test
    echo "Checkout and test locally? (y/n)"
    read checkout
    if [ "$checkout" = "y" ]; then
      glab mr checkout $mr
      # Run tests
      make test
      # Switch back
      git checkout -
    fi

    # Submit review
    echo "Action: (approve/comment/skip)"
    read action
    case $action in
      approve)
        glab mr approve $mr
        glab mr note $mr --message "LGTM! ✅"
        ;;
      comment)
        echo "Enter comment:"
        read comment
        glab mr note $mr --message "$comment"
        ;;
    esac
  done
```

### Auto-merge When Checks Pass

```bash
# Merge MR when pipeline succeeds
glab mr merge 456 --when-pipeline-succeeds --remove-source-branch
```

### Update MR Based on Review Comments

```bash
# View MR with comments
glab mr view 456

# Make changes
git add .
git commit -m "fix: address review comments"
git push

# Add comment to MR
glab mr note 456 --message "Updated per review feedback"
```

## CI/CD and Pipelines

### Monitor Pipeline Status

```bash
#!/bin/bash
# Watch latest CI run for current branch

# Get latest pipeline for current branch
BRANCH=$(git branch --show-current)
PIPELINE_ID=$(glab ci list --branch $BRANCH --per-page 1 --output json | jq -r '.[0].id')

# Watch it in real-time
glab ci trace $PIPELINE_ID
```

### Trigger Deployment

```bash
# Trigger pipeline with variables
glab ci run --branch main

# Monitor pipeline
glab ci status
glab ci trace
```

### Retry Failed CI Jobs

```bash
# List recent failed pipelines
glab ci list --status failed --per-page 10

# Retry failed jobs
glab ci retry 123456
```

### Download Build Artifacts

```bash
# Download artifacts from latest pipeline
glab ci artifact download
```

### Cancel In-Progress Pipelines

```bash
# Cancel specific pipeline
glab ci cancel 123456

# Cancel all in-progress pipelines for a branch
glab ci list --branch feature/test --status running --output json | \
  jq -r '.[].id' | \
  while read pipeline; do
    glab ci cancel $pipeline
  done
```

## Repository Management

### Create New Repository

```bash
# Create new repository
glab repo create my-new-project \
  --description "My awesome project" \
  --public

# Clone it
glab repo clone my-username/my-new-project
```

### Sync Fork with Upstream

```bash
# Fork a repository
glab repo fork original-owner/repo

# Add upstream if not already added
git remote add upstream https://gitlab.com/original-owner/repo.git

# Fetch upstream changes
git fetch upstream

# Merge upstream changes
git checkout main
git merge upstream/main
git push origin main
```

### Archive Old Repositories

```bash
# Archive a repository
glab repo archive my-username/old-project
```

## Team Collaboration

### Assign Code Review to Team

```bash
# Create MR and assign reviewer
glab mr create --fill --assignee @teammate1

# Or add reviewers to existing MR
glab mr update 456 --assignee @teammate2
```

### Track Team's MR Status

```bash
#!/bin/bash
# Team MR dashboard

echo "=== Team MRs Status ==="

# List MRs by team members
for member in alice bob carol; do
  echo -e "\n$member's MRs:"
  glab mr list --author $member --output json | \
    jq -r '.[] | "  !\(.iid): \(.title) | Pipeline: \(.pipeline.status)"'
done
```

### Create Release

```bash
# Create a release
glab release create v2.1.0 \
  --name "Version 2.1.0" \
  --notes "## What's New
- Feature 1
- Feature 2

## Bug Fixes
- Fix 1
- Fix 2" \
  --ref main

# Or create release from tag
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0
glab release create v2.1.0 --ref v2.1.0
```

## Automation Examples

### Daily Standup Report

```bash
#!/bin/bash
# Generate daily activity report

TODAY=$(date --iso-8601)
YESTERDAY=$(date -d '1 day ago' --iso-8601)

echo "=== Activity Report for $TODAY ==="

echo -e "\nIssues closed:"
glab issue list --state closed --updated-after $YESTERDAY --output json | \
  jq -r '.[] | "  #\(.iid): \(.title)"'

echo -e "\nMRs merged:"
glab mr list --state merged --updated-after $YESTERDAY --output json | \
  jq -r '.[] | "  !\(.iid): \(.title)"'

echo -e "\nNew issues:"
glab issue list --created-after $YESTERDAY --output json | \
  jq -r '.[] | "  #\(.iid): \(.title) (@\(.author.username))"'

echo -e "\nNew MRs:"
glab mr list --created-after $YESTERDAY --output json | \
  jq -r '.[] | "  !\(.iid): \(.title) (@\(.author.username))"'
```

### Auto-label MRs Based on Files Changed

```bash
#!/bin/bash
# Auto-label MRs based on changed files

for mr in $(glab mr list --state opened --output json | jq -r '.[].iid'); do
  # Get changed files
  FILES=$(glab mr view $mr --output json | jq -r '.changes[].new_path')

  # Add labels based on file patterns
  if echo "$FILES" | grep -q "^docs/"; then
    glab mr update $mr --label documentation
  fi

  if echo "$FILES" | grep -q "test"; then
    glab mr update $mr --label tests
  fi

  if echo "$FILES" | grep -q "\.py$"; then
    glab mr update $mr --label python
  fi

  if echo "$FILES" | grep -q "\.js$\|\.ts$"; then
    glab mr update $mr --label javascript
  fi
done
```

### Notify on Failed CI

```bash
#!/bin/bash
# Check for failed CI and notify

# Get failed pipelines from last hour
glab ci list --status failed --output json | \
  jq -r --arg time "$(date -d '1 hour ago' --iso-8601=seconds)" \
  '.[] | select(.created_at > $time) | "❌ \(.ref): \(.web_url)"' | \
  while read -r line; do
    # Send notification (example using curl to a webhook)
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
      -H 'Content-Type: application/json' \
      -d "{\"text\": \"$line\"}"
  done
```

### Bulk MR Cleanup

Close draft MRs older than 30 days:

```bash
# List old draft MRs
glab mr list --state opened --draft --output json | \
  jq -r --arg date "$(date -d '30 days ago' --iso-8601)" \
  '.[] | select(.created_at < $date) | "\(.iid) \(.title)"'

# Close them
glab mr list --state opened --draft --output json | \
  jq -r --arg date "$(date -d '30 days ago' --iso-8601)" \
  '.[] | select(.created_at < $date) | .iid' | \
  while read mr; do
    glab mr note $mr --message "Closing stale draft MR. Please reopen if still working on this."
    glab mr close $mr
  done
```

## Advanced: Using GitLab API

For operations not covered by glab commands, use the API:

```bash
# Get project statistics
glab api projects/:id | jq '{
  stars: .star_count,
  forks: .forks_count,
  issues: .open_issues_count
}'

# List project members
glab api projects/:id/members --paginate | \
  jq -r '.[] | "\(.username)\t\(.access_level)"'

# Search code across group
glab api /projects/:id/search \
  -f scope=blobs \
  -f search='function authenticate' | \
  jq -r '.[] | "\(.filename):\(.startline)"'
```

## Tips for Efficient Workflows

### Use Aliases

Create shortcuts for common operations:

```bash
# Save frequently used commands as aliases
glab alias set mrs 'mr list --assignee=@me'
glab alias set issues 'issue list --assignee=@me'
glab alias set pipelines 'ci list'

# Use them
glab mrs
glab issues
glab pipelines
```

### JSON Output for Scripting

Use `--output json` flag for programmatic processing:

```bash
# Get specific fields only
glab mr list --output json | jq '.[] | {iid, title, author}'

# Process with jq
glab issue list --output json | \
  jq '.[] | select(.labels[] | contains("bug"))'

# Export to CSV
glab mr list --output json | \
  jq -r '.[] | [.iid, .title, .author.username, .created_at] | @csv'
```

### Environment Variables

Control glab behavior with environment variables:

```bash
# Enable debug logging
DEBUG=1 glab mr list

# Use specific token
GITLAB_TOKEN=glpat_custom_token glab repo list

# Use different host
GITLAB_HOST=gitlab.company.com glab mr list
```

## Additional Resources

- [glab Manual](https://docs.gitlab.com/cli/)
- [glab Repository](https://gitlab.com/gitlab-org/cli)
- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)
