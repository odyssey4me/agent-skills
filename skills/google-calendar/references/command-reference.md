# Google Calendar Command Reference

## check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/google-calendar.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Google Calendar API
- Displays your primary calendar information

## auth setup

Store OAuth 2.0 client credentials for custom OAuth flow.

```bash
$SKILL_DIR/scripts/google-calendar.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

Credentials are saved to `~/.config/agent-skills/google-calendar.yaml`.

## auth reset

Clear stored OAuth token. The next command that needs authentication will trigger re-authentication automatically.

```bash
$SKILL_DIR/scripts/google-calendar.py auth reset
```

Use this when you encounter scope or authentication errors.

## auth status

Show current OAuth token information without making API calls.

```bash
$SKILL_DIR/scripts/google-calendar.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token presence, token expiry, and client ID.

## calendars list

List all calendars for the authenticated user.

```bash
$SKILL_DIR/scripts/google-calendar.py calendars list
```

## calendars get

Get details for a specific calendar.

```bash
$SKILL_DIR/scripts/google-calendar.py calendars get CALENDAR_ID
```

**Arguments:**
- `calendar_id`: Calendar ID or "primary" (required)

## events list

List calendar events.

```bash
$SKILL_DIR/scripts/google-calendar.py events list \
  --time-min "2026-01-24T00:00:00Z" \
  --time-max "2026-01-31T23:59:59Z" \
  --query "meeting" \
  --max-results 20 \
  --calendar CALENDAR_ID
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

## events get

Get details for a specific event.

```bash
$SKILL_DIR/scripts/google-calendar.py events get EVENT_ID --calendar CALENDAR_ID
```

**Arguments:**
- `event_id`: Event ID (required)
- `--calendar`: Calendar ID (default: "primary")

## events create

Create a new calendar event.

```bash
# Timed event
$SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Team Meeting" \
  --start "2026-01-24T10:00:00-05:00" \
  --end "2026-01-24T11:00:00-05:00" \
  --description "Quarterly project review meeting" \
  --location "Conference Room A" \
  --attendees "alice@example.com,bob@example.com"

# All-day event
$SKILL_DIR/scripts/google-calendar.py events create \
  --summary "Conference" \
  --start "2026-01-24" \
  --end "2026-01-25" \
  --timezone "America/New_York"
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

## events update

Update an existing event.

```bash
$SKILL_DIR/scripts/google-calendar.py events update EVENT_ID \
  --summary "Updated Meeting Title" \
  --start "2026-01-24T15:00:00Z" \
  --end "2026-01-24T16:00:00Z" \
  --description "Updated agenda" \
  --location "Room B"
```

**Arguments:**
- `event_id`: Event ID (required)
- `--calendar`: Calendar ID (default: "primary")
- `--summary`: New event title
- `--start`: New start time (RFC3339 or YYYY-MM-DD)
- `--end`: New end time (RFC3339 or YYYY-MM-DD)
- `--description`: New description
- `--location`: New location

## events delete

Delete a calendar event.

```bash
$SKILL_DIR/scripts/google-calendar.py events delete EVENT_ID --calendar CALENDAR_ID
```

**Arguments:**
- `event_id`: Event ID (required)
- `--calendar`: Calendar ID (default: "primary")

## freebusy

Check free/busy information for calendars.

```bash
$SKILL_DIR/scripts/google-calendar.py freebusy \
  --start "2026-01-24T08:00:00Z" \
  --end "2026-01-24T17:00:00Z" \
  --calendars "primary,colleague@example.com"
```

**Arguments:**
- `--start`: Start time (RFC3339 timestamp, required)
- `--end`: End time (RFC3339 timestamp, required)
- `--calendars`: Comma-separated calendar IDs (default: "primary")

## Date and Time Format

Google Calendar uses RFC3339 format for timestamps. See [calendar-timezones.md](calendar-timezones.md) for detailed timezone handling.

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
