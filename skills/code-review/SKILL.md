---
name: code-review
description: Review PRs, MRs, and Gerrit changes with focus on security, maintainability, and architectural fit. Leverages github, gitlab, or gerrit skills based on repository context.
metadata:
  author: odyssey4me
  version: "0.1.0"
  category: development
  tags: [review, security, maintainability, pr, mr]
  type: workflow
  complexity: orchestration
  requires: [github, gitlab, gerrit]
license: MIT
---

# Code Review

Orchestrates code review across GitHub PRs, GitLab MRs, and Gerrit changes. Auto-detects the platform from git remote configuration and provides focused review feedback on security, maintainability, and architectural fit.

This is a **workflow skill** -- it contains no scripts and instead guides the agent through a multi-step review process using the appropriate platform skill.

## Authentication

This skill delegates authentication to the underlying platform skill:

- **GitHub**: Requires `gh auth login` (see the github skill)
- **GitLab**: Requires `glab auth login` (see the gitlab skill)
- **Gerrit**: Requires `git-review` configuration (see the gerrit skill)

Ensure the relevant platform skill is authenticated before using code-review.

## Commands

### review

Review a change by number or URL.

**Usage:**
```
Review PR #123
Review this MR: https://gitlab.com/org/repo/-/merge_requests/42
Review Gerrit change 456789
```

The agent will:
1. Detect the platform from git remotes or the provided URL
2. Fetch change metadata and CI/test status
3. Fetch the diff and changed files
4. Provide focused review feedback
5. Optionally post review comments

### check

Verify that the required platform skill is available and authenticated.

```bash
# For GitHub repos
gh auth status

# For GitLab repos
glab auth status

# For Gerrit repos
git review --version
```

## Workflow

### Step 1: Detect Platform

Determine the code hosting platform from the repository context:

```bash
# Check git remotes
git remote -v
```

- If remote contains `github.com` -> use the **github** skill
- If remote contains `gitlab` -> use the **gitlab** skill
- If `.gitreview` file exists -> use the **gerrit** skill
- If a URL is provided, detect from the URL hostname

### Step 2: Fetch Change Metadata and CI Status

**GitHub:**
```bash
gh pr view <number> --json title,body,author,baseRefName,headRefName,state,additions,deletions,changedFiles,reviews,labels
gh pr checks <number>
```

**GitLab:**
```bash
glab mr view <number>
glab ci status
```

**Gerrit:**
```bash
git review -d <change-number>
# Review the fetched change locally
```

### Step 3: Assess CI/Test Status

Before reviewing, check whether CI/tests have passed:

- If CI is **passing**: proceed with full review
- If CI is **failing**: note the failures, skip reviewing concerns that would be caught by tests, and focus on issues tests cannot catch (security, architecture, design)
- If CI is **pending**: note it and proceed with review

### Step 4: Fetch the Diff

**GitHub:**
```bash
gh pr diff <number>
```

**GitLab:**
```bash
glab mr diff <number>
```

**Gerrit:**
```bash
git diff HEAD~1
```

### Step 5: Review the Changes

Focus review feedback on these areas, in priority order. See [references/review-checklist.md](references/review-checklist.md) for the full checklist.

1. **Security concerns**: injection vulnerabilities, authentication/authorization gaps, data exposure, unsafe deserialization, hardcoded secrets
2. **Maintainability**: excessive complexity, poor naming, missing separation of concerns, code duplication that harms readability
3. **Good coding practices**: error handling gaps, resource leaks, race conditions, missing input validation at system boundaries
4. **Architectural fit**: consistency with existing codebase patterns, appropriate abstraction level, dependency direction

**Do not flag:**
- Style/formatting issues (leave to linters)
- Minor naming preferences without clear readability impact
- Test coverage gaps (leave to CI coverage tools)
- Issues already caught by failing CI

### Step 6: Present Findings

Format findings as a structured review:

```markdown
## Code Review: PR #<number> - <title>

### Summary
<1-2 sentence summary of the change and overall assessment>

### CI Status
<passing/failing/pending -- note any failures>

### Findings

#### Security
- [ ] <finding with file:line reference>

#### Maintainability
- [ ] <finding with file:line reference>

#### Coding Practices
- [ ] <finding with file:line reference>

#### Architecture
- [ ] <finding with file:line reference>

### Verdict
<APPROVE / REQUEST_CHANGES / COMMENT -- with brief rationale>
```

If the user requests it, post the review as comments on the PR/MR using the platform skill:

**GitHub:**
```bash
gh pr review <number> --comment --body "<review>"
# Or approve/request changes:
gh pr review <number> --approve --body "<review>"
gh pr review <number> --request-changes --body "<review>"
```

**GitLab:**
```bash
glab mr note <number> --message "<review>"
# Or approve:
glab mr approve <number>
```

## Examples

### Review a GitHub PR

```
Review PR #42
```

The agent will run `git remote -v`, detect GitHub, fetch the PR with `gh pr view 42`, check CI with `gh pr checks 42`, fetch the diff with `gh pr diff 42`, and provide structured review feedback.

### Review a GitLab MR by URL

```
Review https://gitlab.com/myorg/myrepo/-/merge_requests/15
```

### Review with Posting Comments

```
Review PR #42 and post your findings as a review comment
```

### Review Focusing on Security Only

```
Review PR #42, focus only on security concerns
```

## Model Guidance

This skill coordinates multiple sub-skills and requires reasoning about multi-step workflows. A higher-capability model is recommended for best results.

## Troubleshooting

### Platform not detected

Ensure you are running from within a git repository with a remote configured:
```bash
git remote -v
```

### Authentication errors

Verify the underlying platform skill is authenticated:
```bash
# GitHub
gh auth status

# GitLab
glab auth status
```

### No diff available

Ensure the PR/MR number is correct and the change exists:
```bash
# GitHub
gh pr view <number>

# GitLab
glab mr view <number>
```
