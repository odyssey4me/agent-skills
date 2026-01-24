# Common GitHub Workflows with gh CLI

This document provides practical examples of common GitHub workflows using the `gh` CLI.

## Table of Contents

- [Issue Management](#issue-management)
- [Pull Request Workflow](#pull-request-workflow)
- [CI/CD and Actions](#cicd-and-actions)
- [Repository Management](#repository-management)
- [Team Collaboration](#team-collaboration)
- [Automation Examples](#automation-examples)

## Issue Management

### Daily Issue Triage

Review and label new issues:

```bash
#!/bin/bash
# List unlabeled issues
gh issue list --label "" --json number,title,author

# For each issue, view and add labels
gh issue list --label "" --limit 10 | while read issue; do
  issue_num=$(echo $issue | awk '{print $1}' | tr -d '#')
  gh issue view $issue_num
  echo "Add label (bug/enhancement/question/documentation/skip):"
  read label
  if [ "$label" != "skip" ]; then
    gh issue edit $issue_num --add-label $label
  fi
done
```

### Close Stale Issues

Close issues inactive for over 90 days:

```bash
# List issues older than 90 days
gh issue list --state open --json number,title,updatedAt | \
  jq -r --arg date "$(date -d '90 days ago' +%Y-%m-%d)" \
  '.[] | select(.updatedAt < $date) | "\(.number) \(.title)"'

# Close them with a comment
gh issue list --state open --json number,updatedAt | \
  jq -r --arg date "$(date -d '90 days ago' +%Y-%m-%d)" \
  '.[] | select(.updatedAt < $date) | .number' | \
  while read num; do
    gh issue close $num --comment "Closing due to inactivity. Please reopen if still relevant."
  done
```

### Create Issue from Template

```bash
# List available templates
ls .github/ISSUE_TEMPLATE/

# Create issue from template
gh issue create --template bug_report.md \
  --title "Login fails with OAuth" \
  --body "Steps to reproduce: ..." \
  --label bug \
  --assignee @me
```

### Bulk Issue Operations

Add milestone to multiple issues:

```bash
# Find issues with label "v2.0"
gh issue list --label "v2.0" --json number | \
  jq -r '.[].number' | \
  while read num; do
    gh issue edit $num --milestone "2.0 Release"
  done
```

## Pull Request Workflow

### Create PR from Feature Branch

```bash
# Ensure you're on feature branch
git checkout -b feature/new-login

# Make changes and commit
git add .
git commit -m "feat: implement new login flow"

# Push branch
git push -u origin feature/new-login

# Create PR with auto-filled title/body from commits
gh pr create --fill

# Or with custom details
gh pr create \
  --title "Implement new login flow" \
  --body "This PR implements OAuth 2.0 login.

## Changes
- Add OAuth provider
- Update login UI
- Add tests

Fixes #123" \
  --label enhancement \
  --reviewer teammate1,teammate2
```

### Review PRs Assigned to You

```bash
#!/bin/bash
# Daily PR review workflow

echo "=== PRs waiting for your review ==="
gh pr list --search "review-requested:@me" --json number,title,author

# Review each PR
gh pr list --search "review-requested:@me" --json number | \
  jq -r '.[].number' | \
  while read pr; do
    echo -e "\n=== Reviewing PR #$pr ==="

    # View PR details
    gh pr view $pr

    # Check CI status
    gh pr checks $pr

    # View diff
    gh pr diff $pr

    # Checkout locally to test
    echo "Checkout and test locally? (y/n)"
    read checkout
    if [ "$checkout" = "y" ]; then
      gh pr checkout $pr
      # Run tests
      make test
      # Switch back
      git checkout -
    fi

    # Submit review
    echo "Action: (approve/comment/request-changes/skip)"
    read action
    case $action in
      approve)
        gh pr review $pr --approve --body "LGTM! ✅"
        ;;
      comment)
        echo "Enter comment:"
        read comment
        gh pr review $pr --comment --body "$comment"
        ;;
      request-changes)
        echo "Enter requested changes:"
        read changes
        gh pr review $pr --request-changes --body "$changes"
        ;;
    esac
  done
```

### Auto-merge When Checks Pass

```bash
# Enable auto-merge with squash
gh pr merge 456 --auto --squash --delete-branch

# The PR will automatically merge when:
# - All required checks pass
# - Required reviews are approved
# - No merge conflicts
```

### Update PR Based on Review Comments

```bash
# View PR with comments
gh pr view 456 --comments

# Make changes
git add .
git commit -m "fix: address review comments"
git push

# Add comment to PR
gh pr comment 456 --body "Updated per review feedback"

# Request re-review
gh pr review 456 --comment --body "@reviewer1 please re-review"
```

## CI/CD and Actions

### Monitor Workflow Status

```bash
#!/bin/bash
# Watch latest CI run for current branch

# Get latest run for current branch
BRANCH=$(git branch --show-current)
RUN_ID=$(gh run list --branch $BRANCH --limit 1 --json databaseId --jq '.[0].databaseId')

# Watch it in real-time
gh run watch $RUN_ID
```

### Trigger Deployment

```bash
# Trigger production deployment
gh workflow run "Deploy to Production" \
  --ref main \
  -f environment=production \
  -f version=v2.1.0

# Monitor deployment
gh run list --workflow="Deploy to Production" --limit 1
DEPLOY_RUN=$(gh run list --workflow="Deploy to Production" --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch $DEPLOY_RUN
```

### Rerun Failed CI Jobs

```bash
# List recent failed runs
gh run list --status failure --limit 10

# Rerun failed jobs only
gh run rerun 123456 --failed

# Or rerun all jobs
gh run rerun 123456
```

### Download Build Artifacts

```bash
# List artifacts for a run
gh run view 123456 --json artifacts

# Download all artifacts
gh run download 123456

# Download specific artifact
gh run download 123456 --name "build-artifacts"

# Download to specific directory
gh run download 123456 --dir ./artifacts
```

### Cancel In-Progress Runs

```bash
# Cancel specific run
gh run cancel 123456

# Cancel all in-progress runs for a branch
gh run list --branch feature/test --status in_progress --json databaseId | \
  jq -r '.[].databaseId' | \
  while read run; do
    gh run cancel $run
  done
```

## Repository Management

### Create New Repository from Template

```bash
# Fork a template repository
gh repo fork template-org/template-repo --clone

# Or create from scratch
gh repo create my-new-project \
  --public \
  --description "My awesome project" \
  --gitignore Python \
  --license MIT

# Create from current directory
gh repo create --source=. --public --push
```

### Sync Fork with Upstream

```bash
# Add upstream if not already added
git remote add upstream https://github.com/original-owner/repo.git

# Fetch upstream changes
git fetch upstream

# Sync via gh
gh repo sync --branch main

# Or manually merge
git checkout main
git merge upstream/main
git push origin main
```

### Archive Old Repositories

```bash
# List repositories to archive
gh repo list --json name,pushedAt,isArchived | \
  jq -r --arg date "$(date -d '2 years ago' +%Y-%m-%d)" \
  '.[] | select(.isArchived == false and .pushedAt < $date) | .name'

# Archive them
gh repo list --json name,pushedAt,isArchived | \
  jq -r --arg date "$(date -d '2 years ago' +%Y-%m-%d)" \
  '.[] | select(.isArchived == false and .pushedAt < $date) | .name' | \
  while read repo; do
    gh repo archive $repo --yes
  done
```

## Team Collaboration

### Assign Code Review to Team

```bash
# Create PR and assign to team
gh pr create --fill --reviewer team-name

# Or add reviewers to existing PR
gh pr edit 456 --add-reviewer @teammate1,@teammate2
```

### Track Team's PR Status

```bash
#!/bin/bash
# Team PR dashboard

echo "=== Team PRs Status ==="

# List PRs by team members
for member in alice bob carol; do
  echo -e "\n$member's PRs:"
  gh pr list --author $member --json number,title,reviews,checks | \
    jq -r '.[] | "  #\(.number): \(.title) | Reviews: \(.reviews | length) | Checks: \(.checks[0].status)"'
done
```

### Create Release

```bash
# Create a release
gh release create v2.1.0 \
  --title "Version 2.1.0" \
  --notes "## What's New
- Feature 1
- Feature 2

## Bug Fixes
- Fix 1
- Fix 2" \
  --target main \
  ./dist/app-v2.1.0.tar.gz

# Or generate notes automatically from PRs
gh release create v2.1.0 --generate-notes --target main
```

## Automation Examples

### Daily Standup Report

```bash
#!/bin/bash
# Generate daily activity report

TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -d '1 day ago' +%Y-%m-%d)

echo "=== Activity Report for $TODAY ==="

echo -e "\nIssues closed:"
gh issue list --state closed --search "closed:>=$YESTERDAY" --json number,title | \
  jq -r '.[] | "  #\(.number): \(.title)"'

echo -e "\nPRs merged:"
gh pr list --state merged --search "merged:>=$YESTERDAY" --json number,title | \
  jq -r '.[] | "  #\(.number): \(.title)"'

echo -e "\nNew issues:"
gh issue list --search "created:>=$YESTERDAY" --json number,title,author | \
  jq -r '.[] | "  #\(.number): \(.title) (@\(.author.login))"'

echo -e "\nNew PRs:"
gh pr list --search "created:>=$YESTERDAY" --json number,title,author | \
  jq -r '.[] | "  #\(.number): \(.title) (@\(.author.login))"'
```

### Auto-label PRs Based on Files Changed

```bash
#!/bin/bash
# Auto-label PRs based on changed files

for pr in $(gh pr list --state open --json number --jq '.[].number'); do
  # Get changed files
  FILES=$(gh pr view $pr --json files --jq '.files[].path')

  # Add labels based on file patterns
  if echo "$FILES" | grep -q "^docs/"; then
    gh pr edit $pr --add-label documentation
  fi

  if echo "$FILES" | grep -q "test"; then
    gh pr edit $pr --add-label tests
  fi

  if echo "$FILES" | grep -q "\.py$"; then
    gh pr edit $pr --add-label python
  fi

  if echo "$FILES" | grep -q "\.js$\|\.ts$"; then
    gh pr edit $pr --add-label javascript
  fi
done
```

### Notify on Failed CI

```bash
#!/bin/bash
# Check for failed CI and notify

# Get failed runs from last hour
gh run list --status failure --created "$(date -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)" \
  --json number,displayTitle,workflowName,url | \
  jq -r '.[] | "❌ \(.workflowName): \(.displayTitle)\n   \(.url)"' | \
  while read -r line; do
    # Send notification (example using curl to a webhook)
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
      -H 'Content-Type: application/json' \
      -d "{\"text\": \"$line\"}"
  done
```

### Bulk PR Cleanup

Close draft PRs older than 30 days:

```bash
# List old draft PRs
gh pr list --state open --draft --json number,title,createdAt | \
  jq -r --arg date "$(date -d '30 days ago' +%Y-%m-%d)" \
  '.[] | select(.createdAt < $date) | "\(.number) \(.title)"'

# Close them
gh pr list --state open --draft --json number,createdAt | \
  jq -r --arg date "$(date -d '30 days ago' +%Y-%m-%d)" \
  '.[] | select(.createdAt < $date) | .number' | \
  while read pr; do
    gh pr close $pr --comment "Closing stale draft PR. Please reopen if still working on this."
    gh pr edit $pr --add-label "stale"
  done
```

## Advanced: Using GitHub API

For operations not covered by gh commands, use the API:

```bash
# List repository languages
gh api repos/OWNER/REPO/languages | jq '.'

# Get repository statistics
gh api repos/OWNER/REPO | jq '{
  stars: .stargazers_count,
  forks: .forks_count,
  watchers: .watchers_count,
  open_issues: .open_issues_count
}'

# List contributors
gh api repos/OWNER/REPO/contributors --paginate | \
  jq -r '.[] | "\(.contributions)\t\(.login)"' | \
  sort -rn | head -10

# Create a project card
gh api projects/columns/COLUMN_ID/cards \
  -X POST \
  -f note='Task description' \
  -f content_type='Issue' \
  -f content_id=123

# Search code across organization
gh api search/code \
  -f q='org:myorg function authenticate language:python' | \
  jq -r '.items[] | "\(.repository.full_name):\(.path)"'
```

## Tips for Efficient Workflows

### Use Aliases

Create shortcuts for common operations:

```bash
# Save frequently used commands as aliases
gh alias set prs 'pr list --author @me'
gh alias set issues 'issue list --assignee @me'
gh alias set review 'pr list --search "review-requested:@me"'

# Use them
gh prs
gh issues
gh review
```

### JSON Output for Scripting

Use `--json` flag for programmatic processing:

```bash
# Get specific fields only
gh pr list --json number,title,author,labels

# Process with jq
gh issue list --json number,title,labels | \
  jq '.[] | select(.labels | map(.name) | index("bug"))'

# Export to CSV
gh pr list --json number,title,author,createdAt | \
  jq -r '.[] | [.number, .title, .author.login, .createdAt] | @csv'
```

### Environment Variables

Control gh behavior with environment variables:

```bash
# Enable debug logging
GH_DEBUG=1 gh pr list

# Use different editor
GH_EDITOR=vim gh issue create

# Disable interactive prompts
GH_PROMPT_DISABLED=1 gh pr create --fill

# Use specific PAT
GH_TOKEN=ghp_custom_token gh repo list
```

## Additional Resources

- [gh Manual](https://cli.github.com/manual/)
- [GitHub CLI Examples](https://github.com/cli/cli/tree/trunk/docs)
- [Advanced Scripting](https://cli.github.com/manual/gh_help_formatting)
- [GitHub API Documentation](https://docs.github.com/en/rest)
