# Roadmap

This document tracks planned features for the agent-skills repository. Only pending work belongs here — remove items as they are delivered.

## Google Drive Enhancements

- [ ] **google-drive** - Add missing Drive API operations
  - [ ] Rename files (`files.update` with name)
  - [ ] Delete files permanently (`files.delete`)
  - [ ] Trash / untrash files (`files.update` with trashed)
  - [ ] Copy files (`files.copy`)
  - [ ] Export Google Docs/Sheets/Slides (`files.export`)
  - [ ] Update existing permissions / change role (`permissions.update`)
  - [ ] Empty trash (`files.emptyTrash`)
  - [ ] File version history (`revisions.*`)
  - [ ] Comments and replies (`comments.*`, `replies.*`)
  - [ ] Watch for file changes (`files.watch`, `changes.*`)
  - [ ] Shared drive management (`drives.*`)

## Markdown Output Compliance

- [ ] **gerrit** - Add markdown wrapper script for `git-review` / Gerrit REST API
  - `git-review` has limited output formatting
  - Wrapper may need to call Gerrit REST API directly for structured data
  - Cover read/view commands: changes, reviews, projects

## Infrastructure Improvements

- [ ] Consider migrating Jira skill to use official Atlassian CLI (ACLI)
  - Official ACLI released May 2025 for Jira Cloud
  - Covers issue management, JQL search, projects, transitions
  - Would reduce maintenance burden (no custom API wrapper to maintain)
  - Current custom script works well - no urgent need to migrate
  - See: https://developer.atlassian.com/cloud/acli/guides/introduction/
