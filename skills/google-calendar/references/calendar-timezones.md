# Google Calendar Timezone Guide

This guide explains how to work with dates, times, and timezones in Google Calendar.

## Time Format Overview

Google Calendar uses **RFC3339** format for timestamps, which is an internet standard for representing dates and times.

### RFC3339 Format

```
YYYY-MM-DDTHH:MM:SS±HH:MM
```

Components:
- `YYYY-MM-DD` - Date (year-month-day)
- `T` - Separator between date and time
- `HH:MM:SS` - Time (hours:minutes:seconds)
- `±HH:MM` - Timezone offset from UTC, OR `Z` for UTC

## Examples

### UTC Time

Use `Z` suffix to indicate UTC (Coordinated Universal Time):

```bash
2026-01-24T10:00:00Z       # 10:00 AM UTC
2026-01-24T15:30:00Z       # 3:30 PM UTC
2026-12-31T23:59:59Z       # December 31, 11:59:59 PM UTC
```

### Time with Timezone Offset

Specify explicit timezone offset:

```bash
# Eastern Standard Time (EST = UTC-5)
2026-01-24T10:00:00-05:00

# Eastern Daylight Time (EDT = UTC-4)
2026-06-24T10:00:00-04:00

# Pacific Standard Time (PST = UTC-8)
2026-01-24T10:00:00-08:00

# Central European Time (CET = UTC+1)
2026-01-24T10:00:00+01:00

# India Standard Time (IST = UTC+5:30)
2026-01-24T10:00:00+05:30
```

### All-Day Events

Use date format (YYYY-MM-DD) without time:

```bash
2026-01-24      # All day on January 24, 2026
2026-12-25      # All day on December 25, 2026
```

For all-day events, optionally specify timezone using `--timezone`:

```bash
python scripts/google-calendar.py events create \
  --summary "Conference" \
  --start "2026-01-24" \
  --end "2026-01-25" \
  --timezone "America/New_York"
```

## Common Timezone Offsets

### North America

| Timezone | Standard (Winter) | Daylight (Summer) |
|----------|------------------|-------------------|
| Eastern (ET) | UTC-5 | UTC-4 |
| Central (CT) | UTC-6 | UTC-5 |
| Mountain (MT) | UTC-7 | UTC-6 |
| Pacific (PT) | UTC-8 | UTC-7 |
| Alaska (AKT) | UTC-9 | UTC-8 |
| Hawaii (HST) | UTC-10 | No DST |

### Europe

| Timezone | Standard (Winter) | Daylight (Summer) |
|----------|------------------|-------------------|
| GMT/WET | UTC+0 | UTC+1 |
| CET | UTC+1 | UTC+2 |
| EET | UTC+2 | UTC+3 |

### Asia Pacific

| Timezone | Offset |
|----------|--------|
| India (IST) | UTC+5:30 |
| China (CST) | UTC+8 |
| Japan (JST) | UTC+9 |
| Australia Eastern | UTC+10 / UTC+11 (DST) |
| New Zealand | UTC+12 / UTC+13 (DST) |

## IANA Timezone Names

For all-day events, you can use IANA timezone database names with the `--timezone` flag:

```
America/New_York
America/Los_Angeles
America/Chicago
America/Denver
Europe/London
Europe/Paris
Europe/Berlin
Asia/Tokyo
Asia/Shanghai
Asia/Kolkata
Australia/Sydney
Pacific/Auckland
```

**Example:**

```bash
python scripts/google-calendar.py events create \
  --summary "All Day Event" \
  --start "2026-01-24" \
  --end "2026-01-25" \
  --timezone "America/New_York"
```

## Daylight Saving Time (DST)

When working with timezones, be aware of Daylight Saving Time transitions:

- **Spring forward**: Clocks move ahead (e.g., EST UTC-5 becomes EDT UTC-4)
- **Fall back**: Clocks move back (e.g., EDT UTC-4 becomes EST UTC-5)

### DST Transitions in 2026 (US)

- **March 8, 2026**: Clocks spring forward at 2:00 AM
- **November 1, 2026**: Clocks fall back at 2:00 AM

**Tip**: Use UTC timestamps (with `Z` suffix) to avoid DST complications, or use explicit timezone offsets that match the current DST status.

## Best Practices

### 1. Use UTC for Consistency

When possible, use UTC timestamps to avoid timezone confusion:

```bash
python scripts/google-calendar.py events create \
  --summary "Meeting" \
  --start "2026-01-24T15:00:00Z" \
  --end "2026-01-24T16:00:00Z"
```

### 2. Be Explicit with Offsets

If using local time, always include the timezone offset:

```bash
# Good - explicit offset
--start "2026-01-24T10:00:00-05:00"

# Avoid - ambiguous without timezone
--start "2026-01-24T10:00:00"
```

### 3. Consider Attendees' Timezones

When scheduling meetings with attendees in different timezones, Google Calendar automatically adjusts display times for each attendee based on their calendar settings.

**Example**: An event at `2026-01-24T15:00:00Z` (3 PM UTC) will display as:
- 10 AM EST (UTC-5)
- 11 PM CST (UTC+8) in China
- 2 AM JST (UTC+9) in Japan (next day!)

### 4. All-Day Events and Timezones

For all-day events, specifying timezone ensures the event appears on the correct calendar day for that timezone:

```bash
# Without timezone - may shift to adjacent day in some timezones
python scripts/google-calendar.py events create \
  --summary "Holiday" \
  --start "2026-12-25" \
  --end "2026-12-26"

# With timezone - ensures correct day
python scripts/google-calendar.py events create \
  --summary "Holiday" \
  --start "2026-12-25" \
  --end "2026-12-26" \
  --timezone "America/New_York"
```

## Converting Between Timezones

### Manual Conversion

To convert from one timezone to another:

1. Convert local time to UTC
2. Apply target timezone offset

**Example**: Convert 2 PM EST to Tokyo time

```
2 PM EST = 14:00-05:00 (EST is UTC-5)
In UTC  = 14:00 + 05:00 = 19:00 UTC
In JST  = 19:00 + 09:00 = 04:00 JST next day (JST is UTC+9)
```

Result: `2026-01-24T14:00:00-05:00` (EST) = `2026-01-25T04:00:00+09:00` (JST)

### Using Date Command (Linux/macOS)

```bash
# Convert EST to UTC
date -u -d "2026-01-24T14:00:00-05:00"

# Convert UTC to local timezone
date -d "2026-01-24T19:00:00Z"
```

### Python Helper

```python
from datetime import datetime, timezone

# Parse RFC3339 timestamp
dt = datetime.fromisoformat("2026-01-24T14:00:00-05:00")

# Convert to UTC
utc_dt = dt.astimezone(timezone.utc)
print(utc_dt.isoformat())  # 2026-01-24T19:00:00+00:00
```

## Command Examples

### Create event in specific timezone

```bash
# 10 AM Eastern Time on January 24
python scripts/google-calendar.py events create \
  --summary "Team Meeting" \
  --start "2026-01-24T10:00:00-05:00" \
  --end "2026-01-24T11:00:00-05:00"
```

### List events in time range (UTC)

```bash
python scripts/google-calendar.py events list \
  --time-min "2026-01-24T00:00:00Z" \
  --time-max "2026-01-31T23:59:59Z"
```

### Create all-day event with timezone

```bash
python scripts/google-calendar.py events create \
  --summary "Company Offsite" \
  --start "2026-01-24" \
  --end "2026-01-26" \
  --timezone "America/Los_Angeles"
```

### Check availability across timezones

```bash
# Check 9 AM - 5 PM EST (14:00 - 22:00 UTC)
python scripts/google-calendar.py freebusy \
  --start "2026-01-24T14:00:00Z" \
  --end "2026-01-24T22:00:00Z" \
  --calendars "primary,colleague@example.com"
```

## Google Calendar API Timezone Behavior

### Event Display

- Google Calendar stores events in UTC internally
- Events are displayed in each user's local timezone
- All-day events respect the timezone they were created in
- Recurring events handle DST transitions automatically

### Timezone Information in API Responses

When you retrieve an event, Google Calendar provides:

```json
{
  "start": {
    "dateTime": "2026-01-24T10:00:00-05:00",
    "timeZone": "America/New_York"
  },
  "end": {
    "dateTime": "2026-01-24T11:00:00-05:00",
    "timeZone": "America/New_York"
  }
}
```

Or for all-day events:

```json
{
  "start": {
    "date": "2026-01-24"
  },
  "end": {
    "date": "2026-01-25"
  }
}
```

## Common Issues and Solutions

### Issue: Event appears on wrong day

**Cause**: Timezone offset caused date boundary crossing

**Solution**: Use explicit timezone or UTC timestamps

```bash
# Wrong - might appear on wrong day
--start "2026-01-24T23:00:00-08:00"  # 11 PM PST = 7 AM UTC next day

# Better - explicitly in UTC
--start "2026-01-25T07:00:00Z"
```

### Issue: Recurring events shift with DST

**Cause**: Fixed offset doesn't account for DST transitions

**Solution**: Use IANA timezone names for recurring events (requires direct API access, not available via command line for this skill)

### Issue: Meeting time confusion across timezones

**Cause**: Participants in different timezones see different local times

**Solution**: Include timezone in event description or use UTC:

```bash
python scripts/google-calendar.py events create \
  --summary "Global Team Call" \
  --start "2026-01-24T15:00:00Z" \
  --end "2026-01-24T16:00:00Z" \
  --description "3 PM UTC / 10 AM EST / 7 AM PST / 11 PM CST (China)"
```

## Additional Resources

- [RFC3339 Specification](https://datatracker.ietf.org/doc/html/rfc3339)
- [IANA Time Zone Database](https://www.iana.org/time-zones)
- [Google Calendar API - Time Format](https://developers.google.com/calendar/api/guides/create-events#date-times)
- [World Time Zones](https://www.timeanddate.com/time/map/)
