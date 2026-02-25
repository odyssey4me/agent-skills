---
name: google-calendar
description: Manage Google Calendar events and calendars. List, create, update, and delete events, check availability, and organize schedules. Use when working with Google Calendar management.
metadata:
  author: odyssey4me
  version: "0.1.0"
  category: google-workspace
  tags: [events, scheduling, availability]
  complexity: standard
license: MIT
allowed-tools: Bash(python $SKILL_DIR/scripts/google-calendar.py *)
---

# Google Calendar

Interact with Google Calendar for event management, scheduling, and availability checking.

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
   ```

2. **Download the skill** from [Releases](https://github.com/odyssey4me/agent-skills/releases) or use directly from this repository.

## Setup Verification

After installation, verify the skill is properly configured:

```bash
python $SKILL_DIR/scripts/google-calendar.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml)
- Authentication configuration
- Connectivity to Google Calendar API

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Calendar uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](../../docs/gcp-project-setup.md) - Create project, enable Calendar API
2. [Google OAuth Setup Guide](../../docs/google-oauth-setup.md) - Configure credentials

### Quick Start

1. Create `~/.config/agent-skills/google.yaml`:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```

2. Run `python $SKILL_DIR/scripts/google-calendar.py check` to trigger OAuth flow and verify setup.

### OAuth Scopes

The skill requests granular scopes for different operations:

| Scope | Permission | Used For |
|-------|-----------|----------|
| `calendar.readonly` | Read calendars and events | list, get events |
| `calendar.events` | Create/edit/delete events | create, update, delete |

### Scope Errors

If you encounter "insufficient scope" errors, reset your token and re-authenticate:

1. Reset token: `python $SKILL_DIR/scripts/google-calendar.py auth reset`
2. Re-run: `python $SKILL_DIR/scripts/google-calendar.py check`

## Commands

### check

Verify configuration and connectivity.

```bash
python $SKILL_DIR/scripts/google-calendar.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Google Calendar API
- Displays your primary calendar information

### auth setup

Store OAuth 2.0 client credentials for custom OAuth flow.

```bash
python $SKILL_DIR/scripts/google-calendar.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

Credentials are saved to `~/.config/agent-skills/google-calendar.yaml`.

### auth reset

Clear stored OAuth token. The next command that needs authentication will trigger re-authentication automatically.

```bash
python $SKILL_DIR/scripts/google-calendar.py auth reset
```

Use this when you encounter scope or authentication errors.

### auth status

Show current OAuth token information without making API calls.

```bash
python $SKILL_DIR/scripts/google-calendar.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token presence, token expiry, and client ID.

### calendars list

List all calendars for the authenticated user.

```bash
python $SKILL_DIR/scripts/google-calendar.py calendars list
```

### calendars get

Get details for a specific calendar.

```bash
# Get primary calendar
python $SKILL_DIR/scripts/google-calendar.py calendars get primary

# Get specific calendar by ID
python $SKILL_DIR/scripts/google-calendar.py calendars get CALENDAR_ID
```

**Arguments:**
- `calendar_id`: Calendar ID or "primary" (required)

### events list

List calendar events.

```bash
# List upcoming events
python $SKILL_DIR/scripts/google-calendar.py events list

# List events in specific time range
python $SKILL_DIR/scripts/google-calendar.py events list \
  --time-min "2026-01-24T00:00:00Z" \
  --time-max "2026-01-31T23:59:59Z"

# List events from specific calendar
python $SKILL_DIR/scripts/google-calendar.py events list --calendar CALENDAR_ID

# Search events
python $SKILL_DIR/scripts/google-calendar.py events list --query "meeting"

# List with custom max results
python $SKILL_DIR/scripts/google-calendar.py events list --max-results 20
```

**Arguments:**
- `--calendar`: Calendar ID (default: "primary")
- `--time-min`: Start time (RFC3339 timestamp, e.g., "2026-01-24T00:00:00Z")
- `--time-max`: End time (RFC3339 timestamp)
- `--max-results`: Maximum number of results (default: 10)
- `--query`: Free text search query
- `--include-declined`: Include events you have declined (excluded by default)

**Time Format Examples:**
- UTC: `2026-01-24T10:00:00Z`
- With timezone: `2026-01-24T10:00:00-05:00` (EST)
- Date only (all-day): `2026-01-24`

### events get

Get details for a specific event.

```bash
# Get event from primary calendar
python $SKILL_DIR/scripts/google-calendar.py events get EVENT_ID

# Get event from specific calendar
python $SKILL_DIR/scripts/google-calendar.py events get EVENT_ID --calendar CALENDAR_ID
```

**Arguments:**
- `event_id`: Event ID (required)
- `--calendar`: Calendar ID (default: "primary")

### events create

Create a new calendar event.

```bash
# Create simple event with time
python $SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Team Meeting" \
  --start "2026-01-24T10:00:00-05:00" \
  --end "2026-01-24T11:00:00-05:00"

# Create all-day event
python $SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Conference" \
  --start "2026-01-24" \
  --end "2026-01-25" \
  --timezone "America/New_York"

# Create event with details
python $SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Project Review" \
  --start "2026-01-24T14:00:00Z" \
  --end "2026-01-24T15:00:00Z" \
  --description "Quarterly project review meeting" \
  --location "Conference Room A" \
  --attendees "alice@example.com,bob@example.com"

# Create on specific calendar
python $SKILL_DIR/scripts/google-calendar.py events create \
  --calendar CALENDAR_ID \
  --summary "Event" \
  --start "2026-01-24T10:00:00Z" \
  --end "2026-01-24T11:00:00Z"
```

**Arguments:**
- `--summary`: Event title (required)
- `--start`: Start time - RFC3339 timestamp or YYYY-MM-DD for all-day (required)
- `--end`: End time - RFC3339 timestamp or YYYY-MM-DD for all-day (required)
- `--calendar`: Calendar ID (default: "primary")
- `--description`: Event description
- `--location`: Event location
- `--attendees`: Comma-separated list of attendee email addresses
- `--timezone`: Timezone for all-day events (e.g., "America/New_York")

### events update

Update an existing event.

```bash
# Update event summary
python $SKILL_DIR/scripts/google-calendar.py events update EVENT_ID \
  --summary "Updated Meeting Title"

# Update event time
python $SKILL_DIR/scripts/google-calendar.py events update EVENT_ID \
  --start "2026-01-24T15:00:00Z" \
  --end "2026-01-24T16:00:00Z"

# Update multiple fields
python $SKILL_DIR/scripts/google-calendar.py events update EVENT_ID \
  --summary "Project Sync" \
  --location "Room B" \
  --description "Updated agenda"

# Update event on specific calendar
python $SKILL_DIR/scripts/google-calendar.py events update EVENT_ID \
  --calendar CALENDAR_ID \
  --summary "New Title"
```

**Arguments:**
- `event_id`: Event ID (required)
- `--calendar`: Calendar ID (default: "primary")
- `--summary`: New event title
- `--start`: New start time (RFC3339 or YYYY-MM-DD)
- `--end`: New end time (RFC3339 or YYYY-MM-DD)
- `--description`: New description
- `--location`: New location

### events delete

Delete a calendar event.

```bash
# Delete event from primary calendar
python $SKILL_DIR/scripts/google-calendar.py events delete EVENT_ID

# Delete event from specific calendar
python $SKILL_DIR/scripts/google-calendar.py events delete EVENT_ID --calendar CALENDAR_ID
```

**Arguments:**
- `event_id`: Event ID (required)
- `--calendar`: Calendar ID (default: "primary")

### freebusy

Check free/busy information for calendars.

```bash
# Check availability for primary calendar
python $SKILL_DIR/scripts/google-calendar.py freebusy \
  --start "2026-01-24T00:00:00Z" \
  --end "2026-01-25T00:00:00Z"

# Check multiple calendars
python $SKILL_DIR/scripts/google-calendar.py freebusy \
  --start "2026-01-24T08:00:00Z" \
  --end "2026-01-24T17:00:00Z" \
  --calendars "primary,calendar1@example.com,calendar2@example.com"
```

**Arguments:**
- `--start`: Start time (RFC3339 timestamp, required)
- `--end`: End time (RFC3339 timestamp, required)
- `--calendars`: Comma-separated calendar IDs (default: "primary")

## Examples

### Verify Setup

```bash
python $SKILL_DIR/scripts/google-calendar.py check
```

### View upcoming events

```bash
# Next 10 events
python $SKILL_DIR/scripts/google-calendar.py events list

# This week's events
python $SKILL_DIR/scripts/google-calendar.py events list \
  --time-min "2026-01-24T00:00:00Z" \
  --time-max "2026-01-31T23:59:59Z"
```

### Create a meeting

```bash
python $SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Team Standup" \
  --start "2026-01-25T09:00:00-05:00" \
  --end "2026-01-25T09:30:00-05:00" \
  --location "Zoom" \
  --attendees "team@example.com"
```

### Schedule an all-day event

```bash
python $SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Company Holiday" \
  --start "2026-12-25" \
  --end "2026-12-26" \
  --timezone "America/New_York"
```

### Reschedule an event

```bash
python $SKILL_DIR/scripts/google-calendar.py events update EVENT_ID \
  --start "2026-01-24T14:00:00Z" \
  --end "2026-01-24T15:00:00Z"
```

### Find available time slots

```bash
python $SKILL_DIR/scripts/google-calendar.py freebusy \
  --start "2026-01-24T08:00:00-05:00" \
  --end "2026-01-24T17:00:00-05:00" \
  --calendars "primary,colleague@example.com"
```

### Search for events

```bash
python $SKILL_DIR/scripts/google-calendar.py events list --query "project review"
```

### Cancel an event

```bash
python $SKILL_DIR/scripts/google-calendar.py events delete EVENT_ID
```

## Date and Time Format

Google Calendar uses RFC3339 format for timestamps. See [calendar-timezones.md](references/calendar-timezones.md) for detailed timezone handling.

### Timed Events

Use RFC3339 format with timezone:

```
2026-01-24T10:00:00-05:00  # 10 AM EST
2026-01-24T10:00:00Z       # 10 AM UTC
2026-01-24T10:00:00+01:00  # 10 AM CET
```

### All-Day Events

Use date format (YYYY-MM-DD):

```
2026-01-24  # All day on January 24, 2026
```

For all-day events, you can specify a timezone using the `--timezone` argument.

## Agent Guidance — Declined Events

When listing events, declined meetings are excluded by default. The script output will indicate if declined invitations were filtered out (e.g. "3 declined invitation(s) not shown"). When this notice appears, inform the user that there are declined invitations and offer to show them if desired. To include declined events, re-run with `--include-declined`.

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails with an authentication error, insufficient scope error, or permission denied error (exit code 1), do NOT retry the same command. Instead:

1. Inform the user about the error
2. Run `python $SKILL_DIR/scripts/google-calendar.py auth status` to check the current token state
3. Suggest the user run `python $SKILL_DIR/scripts/google-calendar.py auth reset` followed by `python $SKILL_DIR/scripts/google-calendar.py check` to re-authenticate
4. The `auth reset` and `check` commands require user interaction (browser-based OAuth consent) and cannot be completed autonomously

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors (HTTP 5xx) may succeed on retry after a brief wait. All other errors should be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Check command fails

Run `python $SKILL_DIR/scripts/google-calendar.py check` to diagnose issues. It will provide specific error messages and setup instructions.

### Authentication failed

1. Verify your OAuth client ID and client secret are correct in `~/.config/agent-skills/google-calendar.yaml`
2. Token expired or corrupted — reset and re-authenticate:
   ```bash
   python $SKILL_DIR/scripts/google-calendar.py auth reset
   python $SKILL_DIR/scripts/google-calendar.py check
   ```

### Permission denied

Your OAuth token may not have the necessary scopes. Reset your token and re-authenticate:

```bash
python $SKILL_DIR/scripts/google-calendar.py auth reset
python $SKILL_DIR/scripts/google-calendar.py check
```

### Import errors

Ensure dependencies are installed:
```bash
pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
```

### Event not found

Verify the event ID and calendar ID are correct. Event IDs are unique per calendar.

### Timezone issues

Always use RFC3339 format with explicit timezone offsets, or UTC (Z suffix). For all-day events, use YYYY-MM-DD format and optionally specify `--timezone`.

### Rate limiting

Google Calendar API has quota limits. If you hit rate limits, wait a few minutes before retrying. For high-volume usage, consider requesting quota increases in the Google Cloud Console.

## API Scopes

This skill requests the following OAuth scopes:

- `https://www.googleapis.com/auth/calendar.readonly` - Read calendar events and settings
- `https://www.googleapis.com/auth/calendar.events` - Create, update, and delete events

These scopes provide full calendar management capabilities while following the principle of least privilege.

## Security Notes

- **OAuth tokens** are stored securely in your system keyring
- **Client secrets** are stored in `~/.config/agent-skills/google-calendar.yaml` with file permissions 600
- **No passwords** are stored - only OAuth tokens
- **Tokens refresh automatically** when using the skill
- **Browser-based consent** ensures you approve all requested permissions

Always review OAuth consent screens before granting access to your Google Calendar.
