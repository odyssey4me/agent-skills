# Roadmap

This document tracks planned skills and features for the agent-skills repository.

## Planned Skills

### Code Hosting

- [ ] **gitlab** - GitLab operations
  - Issues
  - Merge requests
  - Repository operations
  - Pipelines
  - Check for official GitLab CLI first

- [ ] **gerrit** - Gerrit code review
  - Changes (create, review, submit)
  - Topics
  - Review comments
  - Check for official Gerrit CLI first

## Documentation Improvements

- [ ] Document GCP project setup for Google OAuth skills
  - Add section to user guide showing how to setup GCP project using gcloud CLI
  - Cover: creating project, enabling APIs, creating OAuth credentials, setting redirect URIs
  - Link from Gmail, Google Drive, and Google Calendar SKILL.md files
  - Consolidate setup instructions in one place to follow DRY principle

- [ ] Simplify Google skills authentication to OAuth-only
  - Remove gcloud CLI auth fallback from Gmail, Google Drive, Google Calendar skills
  - OAuth is the recommended approach with better security (granular scopes)
  - gcloud auth is confusing for users and has broader permissions than needed
  - Update SKILL.md files to focus solely on OAuth flow
  - Remove gcloud-related code paths from skill scripts

## Infrastructure Improvements

- [ ] Consider migrating Jira skill to use official Atlassian CLI (ACLI)
  - Official ACLI released May 2025 for Jira Cloud
  - Covers issue management, JQL search, projects, transitions
  - Would reduce maintenance burden (no custom API wrapper to maintain)
  - Current custom script works well - no urgent need to migrate
  - See: https://developer.atlassian.com/cloud/acli/guides/introduction/
