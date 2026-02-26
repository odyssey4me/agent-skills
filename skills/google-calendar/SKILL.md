---
name: google-calendar
description: Create, update, and organize Google Calendar events and schedules. Check availability, book time, and manage calendars. Use when asked to schedule a meeting, set up an appointment, book a call, check gcal, or manage calendar events.
metadata:
  author: odyssey4me
  version: "0.1.0"
  category: google-workspace
  tags: "events, scheduling, availability"
  complexity: standard
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/google-calendar.py:*)
---

# Google Calendar

Interact with Google Calendar for event management, scheduling, and availability checking.

## Installation

**Dependencies**: `pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml`

## Setup Verification

After installation, verify the skill is properly configured:

```bash
$SKILL_DIR/scripts/google-calendar.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml)
- Authentication configuration
- Connectivity to Google Calendar API

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Calendar uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/gcp-project-setup.md) - Create project, enable Calendar API
2. [Google OAuth Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md) - Configure credentials

### Quick Start

1. Create `~/.config/agent-skills/google.yaml`:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```

2. Run `$SKILL_DIR/scripts/google-calendar.py check` to trigger OAuth flow and verify setup.

On scope or authentication errors, see the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

## Script Usage

```bash
# Setup and auth
$SKILL_DIR/scripts/google-calendar.py check
$SKILL_DIR/scripts/google-calendar.py auth setup --client-id ID --client-secret SECRET
$SKILL_DIR/scripts/google-calendar.py auth reset
$SKILL_DIR/scripts/google-calendar.py auth status

# Calendars
$SKILL_DIR/scripts/google-calendar.py calendars list
$SKILL_DIR/scripts/google-calendar.py calendars get CALENDAR_ID

# Events
$SKILL_DIR/scripts/google-calendar.py events list
$SKILL_DIR/scripts/google-calendar.py events get EVENT_ID
$SKILL_DIR/scripts/google-calendar.py events create --summary TITLE --start TIME --end TIME
$SKILL_DIR/scripts/google-calendar.py events update EVENT_ID --summary TITLE
$SKILL_DIR/scripts/google-calendar.py events delete EVENT_ID

# Availability
$SKILL_DIR/scripts/google-calendar.py freebusy --start TIME --end TIME
```

All commands support `--calendar CALENDAR_ID` (default: "primary"). Times use RFC3339 format (e.g., `2026-01-24T10:00:00Z`) or `YYYY-MM-DD` for all-day events.

See [command-reference.md](references/command-reference.md) for full argument details and examples.

## Examples

### Schedule a meeting with attendees

```bash
$SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Team Standup" \
  --start "2026-01-25T09:00:00-05:00" \
  --end "2026-01-25T09:30:00-05:00" \
  --location "Zoom" \
  --attendees "team@example.com"
```

### Find available time across calendars

```bash
$SKILL_DIR/scripts/google-calendar.py freebusy \
  --start "2026-01-24T08:00:00-05:00" \
  --end "2026-01-24T17:00:00-05:00" \
  --calendars "primary,colleague@example.com"
```

### List this week's events

```bash
$SKILL_DIR/scripts/google-calendar.py events list \
  --time-min "2026-01-24T00:00:00Z" \
  --time-max "2026-01-31T23:59:59Z"
```

## Agent Guidance — Declined Events

When listing events, declined meetings are excluded by default. The script output will indicate if declined invitations were filtered out (e.g. "3 declined invitation(s) not shown"). When this notice appears, inform the user that there are declined invitations and offer to show them if desired. To include declined events, re-run with `--include-declined`.

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails with an authentication error, insufficient scope error, or permission denied error (exit code 1), **stop and inform the user**. Do not retry or attempt to fix the issue autonomously — these errors require user interaction (browser-based OAuth consent). Point the user to the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors (HTTP 5xx) may succeed on retry after a brief wait. All other errors should be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Event not found

Verify the event ID and calendar ID are correct. Event IDs are unique per calendar.

### Timezone issues

Always use RFC3339 format with explicit timezone offsets, or UTC (Z suffix). For all-day events, use YYYY-MM-DD format and optionally specify `--timezone`.
