---
name: code-review
description: Review PRs, MRs, and Gerrit changes with focus on security, maintainability, and architectural fit. Leverages github, gitlab, or gerrit skills based on repository context.
metadata:
  author: odyssey4me
  version: "0.2.0"
  category: development
  tags: "review, security, maintainability, pr, mr"
  type: workflow
  complexity: orchestration
  requires: "github, gitlab, gerrit"
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

### remember

Save additional context for the current repository's reviews. This persists information that should be considered in future reviews of the same repo.

**Usage:**
```
Remember that this repo follows the Google Python Style Guide
Remember: authentication changes must be reviewed by the security team
Remember https://internal-docs.example.com/api-conventions as a reference for API design
Remember that the data layer uses the Repository pattern, not Active Record
```

**Keyword**: The word **remember** at the start of a message triggers saving. The context is stored in `~/.config/agent-skills/code-review.yaml` under the current repository's remote URL.

**What to save**: Coding standards, architectural decisions, external documentation links, team conventions, review policies, or any context that should inform future reviews.

### forget

Remove previously saved context for the current repository.

**Usage:**
```
Forget the note about the Google Python Style Guide
Forget all saved context for this repo
```

### show context

Display all saved context for the current repository.

**Usage:**
```
Show review context for this repo
```

### check

Verify that the required platform skill is available and authenticated.

```bash
# For GitHub repos
python skills/github/scripts/github.py check

# For GitLab repos
python skills/gitlab/scripts/gitlab.py check

# For Gerrit repos
python skills/gerrit/scripts/gerrit.py check
```

## Repository Context

The code-review skill persists per-repository context in `~/.config/agent-skills/code-review.yaml`. This allows the agent to accumulate knowledge about a repository's conventions, architecture, and review policies across sessions.

### Config File Structure

```yaml
# ~/.config/agent-skills/code-review.yaml
repositories:
  "git@github.com:myorg/myrepo.git":
    references:
      - "https://internal-docs.example.com/api-conventions"
      - "https://google.github.io/styleguide/pyguide.html"
    standards:
      - "All API endpoints must validate input with Pydantic models"
      - "Authentication changes require security team review"
    notes:
      - "Data layer uses Repository pattern, not Active Record"
      - "Legacy modules in src/compat/ are exempt from new style rules"
  "https://gitlab.com/myorg/other-repo.git":
    references:
      - "https://docs.example.com/other-repo/architecture"
    standards: []
    notes:
      - "Migrating from REST to GraphQL -- new endpoints should use GraphQL"
```

The repository key is the first remote URL from `git remote -v` (normalized to the fetch URL). Each repository entry has three lists:

- **references**: URLs to external documentation, style guides, or architecture docs
- **standards**: Coding standards, policies, or rules specific to this repo
- **notes**: Architectural decisions, team conventions, or other contextual information

### Loading Context

At the start of every review, the agent checks for saved context:

```bash
# Get the repo remote URL for config lookup
git remote get-url origin
```

If context exists for the repo, the agent loads it and applies it during the review. For example, if a standard says "API endpoints must validate input with Pydantic models," the agent checks whether new endpoints follow that rule.

### Prompting to Save

When the user provides out-of-repo context during a review (e.g., links to external docs, mentions of team conventions, or references to other repositories), the agent should proactively suggest:

> "This seems like useful context for future reviews of this repo. Say **remember** followed by what you'd like me to save, and I'll persist it for next time."

This ensures users discover the feature naturally without needing to read documentation.

## Workflow

### Step 0: Load Repository Context

Before starting the review, check for saved context:

```bash
git remote get-url origin
```

Read `~/.config/agent-skills/code-review.yaml` and look up the remote URL. If context exists, load it and keep it in mind throughout the review:

- **references**: Consult these when evaluating architectural decisions
- **standards**: Actively check compliance with each standard
- **notes**: Factor these into review feedback

If no context file exists or the repo has no entries, proceed without additional context.

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
python skills/github/scripts/github.py prs view <number> --repo OWNER/REPO
python skills/github/scripts/github.py prs checks <number> --repo OWNER/REPO
```

**GitLab:**
```bash
python skills/gitlab/scripts/gitlab.py mrs view <number> --repo GROUP/REPO
python skills/gitlab/scripts/gitlab.py pipelines list --repo GROUP/REPO
```

**Gerrit:**
```bash
python skills/gerrit/scripts/gerrit.py changes view <change-number>
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

The agent will run `git remote -v`, detect GitHub, fetch the PR with `python skills/github/scripts/github.py prs view 42`, check CI with `python skills/github/scripts/github.py prs checks 42`, fetch the diff with `gh pr diff 42`, and provide structured review feedback.

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

### Save Context for Future Reviews

```
Remember that this repo uses the Twelve-Factor App methodology
Remember https://wiki.example.com/team/coding-standards as a reference
Remember: all database migrations must be backwards-compatible
```

### Show Saved Context

```
Show review context for this repo
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
python skills/github/scripts/github.py prs view <number>

# GitLab
python skills/gitlab/scripts/gitlab.py mrs view <number>
```
