# Roadmap

This document tracks planned skills and features for the agent-skills repository.

## Planned Skills

### Phase 2: Google Workspace

- [x] **gmail** - Email management
  - Read emails
  - Search emails
  - Send emails
  - Label management
  - Draft management

- [x] **google-drive** - File management
  - List and search files
  - Get file metadata
  - Download files
  - Upload files
  - Folder management (create, list contents)
  - Sharing (share file, list/delete permissions)
  - Hybrid authentication (gcloud ADC, custom OAuth 2.0)
  - Self-contained Python script with keyring storage
  - Built-in check command for setup verification

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

## Multi-Agent Testing & Verification

Skills currently work with [multiple AI agents](https://github.com/vercel-labs/add-skill#supported-agents) via `npx add-skill` and the Agent Skills specification. Future work focuses on agent-specific testing:

- [ ] **Cursor** - Verify skill discovery and invocation patterns
- [ ] **Continue.dev** - Test natural language integration
- [ ] **GitHub Copilot** - Validate skill execution
- [ ] **Gemini CLI** - Test compatibility and workflows
- [ ] **OpenCode** - Verify functionality

Note: Basic multi-agent support is complete via the Agent Skills specification. This section tracks verification and agent-specific optimization.

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

- [x] **confluence** - Confluence page management (Phase 1)
  - CQL search for pages and content
  - Get page content (with Markdown output)
  - Create pages (with Markdown input support)
  - Update pages (with Markdown input support)
  - Space management (list, get, create)
  - Automatic Cloud vs DC/Server detection
  - Markdown ↔ Storage/ADF format conversion
  - File-based content input (--body-file)

- [x] **gmail** - Gmail email management (Phase 2)
  - List and search messages (Gmail query syntax)
  - Get message details (full, minimal, raw, metadata formats)
  - Send emails (to, cc, bcc)
  - Draft management (create, list, send)
  - Label operations (list, create, modify on messages)
  - Hybrid authentication (gcloud ADC, custom OAuth 2.0)
  - Self-contained Python script with keyring storage
  - Built-in check command for setup verification
