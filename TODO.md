# Roadmap

This document tracks planned skills and features for the agent-skills repository.

## Planned Skills

### Phase 1: Atlassian (Confluence)

- [ ] **confluence** - Confluence page management
  - Page search
  - Read page content
  - Create/update pages
  - Space management

### Phase 2: Google Workspace

- [ ] **gmail** - Email management
  - Read emails
  - Search emails
  - Send emails
  - Label management
  - Draft management

- [ ] **google-drive** - File management
  - List files
  - Search files
  - Read file content
  - Upload files
  - Share files

- [ ] **google-calendar** - Calendar management
  - List events
  - Create events
  - Update events
  - Check availability
  - Scheduling

### Phase 3: Code Hosting

- [ ] **github** - GitHub operations
  - Issues (create, update, search, close)
  - Pull requests (create, review, merge)
  - Repository operations
  - Actions/workflows
  - Releases

- [ ] **gitlab** - GitLab operations
  - Issues
  - Merge requests
  - Repository operations
  - Pipelines

- [ ] **gerrit** - Gerrit code review
  - Changes (create, review, submit)
  - Topics
  - Review comments

## Multi-Agent Support

Currently focusing on Claude Code only. Other AI agents will be supported later:

- [ ] **OpenAI Codex** - VS Code integration
- [ ] **Gemini CLI** - Google's AI assistant
- [ ] **Cursor** - AI-first code editor
- [ ] **Continue.dev** - Open-source AI coding assistant
- [ ] **GitHub Copilot** - GitHub's AI pair programmer

## Infrastructure Improvements

- [ ] Increase test coverage to 80%
- [ ] Add GCP project setup helper script for Google OAuth
- [ ] Add skill discovery/listing command
- [ ] Add skill installation/update mechanism
- [ ] Create comprehensive skill tests (test real API calls with mocking)

## Completed

- [x] **jira** - Jira issue tracking (Phase 0)
  - JQL search
  - Get/create/update issues
  - Workflow transitions
  - Comments
