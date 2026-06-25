# Calendar Command Reference

Full command reference for `gog calendar`. All commands support `--json` and `--plain` output.

## Calendars

| Command | Description |
|---------|-------------|
| `calendars` | List calendars |
| `subscribe <calendarId>` | Add a calendar to your list |
| `unsubscribe <calendarId>` | Remove a calendar from your list |
| `create-calendar <summary>` | Create a new secondary calendar |
| `delete-calendar <calendarId>` | Delete an owned secondary calendar |
| `acl <calendarId>` | List calendar ACL/permissions |
| `alias` | Manage calendar aliases |
| `colors` | Show calendar colors |

## Events

| Command | Description |
|---------|-------------|
| `events [<calendarId>...]` | List events from calendars |
| `event <calendarId> <eventId>` | Get a single event |
| `create <calendarId>` | Create an event |
| `update <calendarId> <eventId>` | Update an event |
| `delete <calendarId> <eventId>` | Delete an event |
| `move <calendarId> <eventId> <destCalendarId>` | Move event to another calendar |
| `search <query>` | Search events by text |
| `raw <calendarId> <eventId>` | Dump raw API response as JSON |

### Events list flags

- `--today` — show today's events
- `--tomorrow` — show tomorrow's events
- `--from "2026-06-25"` — start date
- `--to "2026-06-30"` — end date
- `--max N` — limit results
- `--include-declined` — include declined events

### Create flags

- `--summary "Title"` — event title (required)
- `--from "2026-06-25T10:00:00"` — start time (required)
- `--to "2026-06-25T11:00:00"` — end time (required)
- `--description "Details"` — event description
- `--location "Room 42"` — event location
- `--attendees "a@x.com,b@x.com"` — comma-separated attendees
- `--all-day` — create an all-day event

## Availability

| Command | Description |
|---------|-------------|
| `freebusy [<calendarIds>]` | Get free/busy information |
| `conflicts` | Find busy-time overlaps across calendars |
| `respond <calendarId> <eventId>` | RSVP to an event invitation |
| `propose-time <calendarId> <eventId>` | Generate URL to propose a new time |

### Freebusy flags

- `--from "2026-06-25T09:00:00Z"` — start time
- `--to "2026-06-25T17:00:00Z"` — end time

## Workspace

| Command | Description |
|---------|-------------|
| `focus-time` | Create a Focus Time block |
| `out-of-office` | Create an Out of Office event |
| `working-location` | Set working location (home/office/custom) |
| `users` | List workspace users |
| `team <group-email>` | Show events for group members |
| `time` | Show server time |
