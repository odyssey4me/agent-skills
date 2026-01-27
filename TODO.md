# Roadmap

This document tracks planned skills and features for the agent-skills repository.

## Planned Skills

### Code Hosting

- [x] **gitlab** - GitLab operations
  - Issues
  - Merge requests
  - Repository operations
  - Pipelines
  - ✅ Uses official GitLab CLI (glab)

- [x] **gerrit** - Gerrit code review
  - Changes (create, review, submit)
  - Topics
  - Review comments
  - ✅ Uses git-review CLI (official OpenStack/OpenDev tool)

## Documentation Improvements

- [x] Document GCP project setup for Google OAuth skills
  - ✅ Created [docs/gcp-project-setup.md](docs/gcp-project-setup.md) with complete CLI-based setup
  - ✅ Covers: creating project, enabling APIs, billing options, OAuth consent screen, credentials
  - ✅ Updated Gmail, Google Drive, and Google Calendar oauth-setup.md to reference the guide
  - ✅ Updated user-guide.md with consolidated Google skills authentication section

- [x] Simplify Google skills authentication to OAuth-only
  - ✅ Removed gcloud CLI auth fallback from Gmail, Google Drive, Google Calendar scripts
  - ✅ Updated all three SKILL.md files to focus solely on OAuth flow
  - ✅ Simplified authentication sections with Quick Start guide and OAuth scope tables
  - ✅ Updated troubleshooting sections to reference OAuth-only workflow

### Google Workspace

- [x] **google-docs** - Google Docs document management
  - ✅ Create and modify Google Docs documents
  - ✅ Read document content and structure
  - ✅ Manage document formatting, paragraphs, and styles
  - ✅ Uses Google Docs API (separate from Drive API)
  - ✅ Share OAuth credentials with other Google skills
  - Note: google-drive skill only handles file metadata, not document content

- [x] **google-sheets** - Google Sheets spreadsheet management
  - ✅ Create and modify spreadsheets
  - ✅ Read/write cell values and ranges
  - ✅ Manage sheets, formatting, and formulas
  - ✅ Uses Google Sheets API (separate from Drive API)
  - ✅ Share OAuth credentials with other Google skills
  - Note: google-drive skill only handles file metadata, not spreadsheet content

- [x] **google-slides** - Google Slides presentation management
  - ✅ Create and modify presentations
  - ✅ Manage slides, layouts, and content
  - ✅ Add text, shapes, and images
  - ✅ Uses Google Slides API (separate from Drive API)
  - ✅ Share OAuth credentials with other Google skills
  - Note: google-drive skill only handles file metadata, not presentation content

## Infrastructure Improvements

- [ ] Consider migrating Jira skill to use official Atlassian CLI (ACLI)
  - Official ACLI released May 2025 for Jira Cloud
  - Covers issue management, JQL search, projects, transitions
  - Would reduce maintenance burden (no custom API wrapper to maintain)
  - Current custom script works well - no urgent need to migrate
  - See: https://developer.atlassian.com/cloud/acli/guides/introduction/
