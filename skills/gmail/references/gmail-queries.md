# Gmail Search Query Reference

Gmail's search syntax is powerful and allows you to find exactly what you need. This reference covers the search operators you can use with `gmail.py messages list --query`.

## Basic Search Operators

### Sender and Recipient

| Operator | Description | Example |
|----------|-------------|---------|
| `from:` | Messages from specific sender | `from:alice@example.com` |
| `to:` | Messages sent to recipient | `to:bob@example.com` |
| `cc:` | Messages CC'd to recipient | `cc:team@example.com` |
| `bcc:` | Messages BCC'd to recipient | `bcc:boss@example.com` |

**Examples:**
```bash
# All emails from Alice
python scripts/gmail.py messages list --query "from:alice@example.com"

# Emails I sent to Bob
python scripts/gmail.py messages list --query "to:bob@example.com"

# Emails where team was CC'd
python scripts/gmail.py messages list --query "cc:team@example.com"
```

### Subject and Body

| Operator | Description | Example |
|----------|-------------|---------|
| `subject:` | Subject contains text | `subject:meeting` |
| (no operator) | Body or subject contains | `project alpha` |
| `"exact phrase"` | Exact phrase match | `"quarterly review"` |

**Examples:**
```bash
# Emails with "meeting" in subject
python scripts/gmail.py messages list --query "subject:meeting"

# Emails containing "project alpha" anywhere
python scripts/gmail.py messages list --query "project alpha"

# Exact phrase in subject or body
python scripts/gmail.py messages list --query '"quarterly review"'
```

## Message States

### Read/Unread

| Operator | Description |
|----------|-------------|
| `is:unread` | Unread messages |
| `is:read` | Read messages |

**Examples:**
```bash
# All unread emails
python scripts/gmail.py messages list --query "is:unread"

# Read emails from last week
python scripts/gmail.py messages list --query "is:read newer_than:7d"
```

### Starred/Important

| Operator | Description |
|----------|-------------|
| `is:starred` | Starred messages |
| `is:important` | Important messages (Gmail priority) |

**Examples:**
```bash
# Starred emails
python scripts/gmail.py messages list --query "is:starred"

# Important unread emails
python scripts/gmail.py messages list --query "is:important is:unread"
```

## Labels and Categories

### Labels

| Operator | Description | Example |
|----------|-------------|---------|
| `label:` | Has specific label | `label:work` |
| `has:userlabels` | Has any user label | `has:userlabels` |
| `has:nouserlabels` | Has no user labels | `has:nouserlabels` |

**Examples:**
```bash
# Emails with "work" label
python scripts/gmail.py messages list --query "label:work"

# Emails with any custom label
python scripts/gmail.py messages list --query "has:userlabels"

# Emails without custom labels
python scripts/gmail.py messages list --query "has:nouserlabels"
```

### Categories (Gmail tabs)

| Operator | Description |
|----------|-------------|
| `category:primary` | Primary inbox |
| `category:social` | Social tab |
| `category:promotions` | Promotions tab |
| `category:updates` | Updates tab |
| `category:forums` | Forums tab |

**Examples:**
```bash
# Unread emails in primary inbox
python scripts/gmail.py messages list --query "category:primary is:unread"

# Social emails from last day
python scripts/gmail.py messages list --query "category:social newer_than:1d"
```

## Attachments

| Operator | Description | Example |
|----------|-------------|---------|
| `has:attachment` | Has any attachment | `has:attachment` |
| `filename:` | Attachment filename | `filename:pdf` |
| `filename:` (exact) | Exact filename | `filename:report.pdf` |

**Examples:**
```bash
# Emails with attachments
python scripts/gmail.py messages list --query "has:attachment"

# Emails with PDF attachments
python scripts/gmail.py messages list --query "filename:pdf"

# Specific file
python scripts/gmail.py messages list --query "filename:report.pdf"

# Attachments from specific sender
python scripts/gmail.py messages list --query "from:alice@example.com has:attachment"
```

## Date and Time

### Relative Dates

| Operator | Description | Example |
|----------|-------------|---------|
| `newer_than:` | Newer than time period | `newer_than:7d` |
| `older_than:` | Older than time period | `older_than:30d` |

Time units:
- `d` = days (e.g., `7d` = 7 days)
- `m` = months (e.g., `2m` = 2 months)
- `y` = years (e.g., `1y` = 1 year)

**Examples:**
```bash
# Emails from last 7 days
python scripts/gmail.py messages list --query "newer_than:7d"

# Emails older than 30 days
python scripts/gmail.py messages list --query "older_than:30d"

# Last 2 months from specific sender
python scripts/gmail.py messages list --query "from:boss@example.com newer_than:2m"
```

### Absolute Dates

| Operator | Description | Example |
|----------|-------------|---------|
| `after:` | After specific date | `after:2024/01/01` |
| `before:` | Before specific date | `before:2024/12/31` |

Date formats:
- `YYYY/MM/DD` (e.g., `2024/01/15`)
- `YYYY-MM-DD` (e.g., `2024-01-15`)

**Examples:**
```bash
# Emails after January 1, 2024
python scripts/gmail.py messages list --query "after:2024/01/01"

# Emails before end of year
python scripts/gmail.py messages list --query "before:2024/12/31"

# Emails in specific date range
python scripts/gmail.py messages list --query "after:2024/01/01 before:2024/01/31"
```

### Relative Date Shortcuts

| Operator | Description |
|----------|-------------|
| `newer_than:1d` | Last 24 hours |
| `newer_than:7d` | Last week |
| `newer_than:1m` | Last month |
| `older_than:1y` | Older than 1 year |

## Size

| Operator | Description | Example |
|----------|-------------|---------|
| `size:` | Exact size in bytes | `size:1000000` |
| `larger:` | Larger than size | `larger:10M` |
| `smaller:` | Smaller than size | `smaller:1M` |

Size units:
- No unit = bytes
- `K` = kilobytes
- `M` = megabytes

**Examples:**
```bash
# Emails larger than 10 MB
python scripts/gmail.py messages list --query "larger:10M"

# Small emails (less than 100 KB)
python scripts/gmail.py messages list --query "smaller:100K"

# Large attachments from last week
python scripts/gmail.py messages list --query "has:attachment larger:5M newer_than:7d"
```

## Conversation Threads

| Operator | Description |
|----------|-------------|
| `is:chat` | Chat messages |
| `is:snoozed` | Snoozed messages |
| `list:` | Messages from mailing list |

**Examples:**
```bash
# Chat messages
python scripts/gmail.py messages list --query "is:chat"

# Snoozed messages
python scripts/gmail.py messages list --query "is:snoozed"

# Messages from specific mailing list
python scripts/gmail.py messages list --query "list:dev-team@example.com"
```

## Special Searches

### Trash and Spam

| Operator | Description |
|----------|-------------|
| `in:trash` | In trash |
| `in:spam` | In spam |
| `in:inbox` | In inbox |
| `in:sent` | In sent mail |
| `in:drafts` | In drafts |
| `in:anywhere` | Anywhere (including trash/spam) |

**Examples:**
```bash
# Trash items
python scripts/gmail.py messages list --query "in:trash"

# Sent emails to specific person
python scripts/gmail.py messages list --query "in:sent to:alice@example.com"

# Search everywhere including trash
python scripts/gmail.py messages list --query "in:anywhere subject:important"
```

## Boolean Operators

### Combining Searches

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` (implicit) | Both conditions | `from:alice subject:meeting` |
| `OR` | Either condition | `from:alice OR from:bob` |
| `NOT` or `-` | Exclude condition | `-from:spam@example.com` |
| `( )` | Grouping | `(from:alice OR from:bob) subject:meeting` |

**Examples:**
```bash
# From Alice AND about meetings (implicit AND)
python scripts/gmail.py messages list --query "from:alice@example.com subject:meeting"

# From Alice OR Bob
python scripts/gmail.py messages list --query "from:alice@example.com OR from:bob@example.com"

# NOT from spam sender
python scripts/gmail.py messages list --query "-from:spam@example.com"

# Complex: (Alice OR Bob) AND meeting AND unread
python scripts/gmail.py messages list --query "(from:alice@example.com OR from:bob@example.com) subject:meeting is:unread"
```

### Negation Examples

```bash
# Unread emails NOT from Alice
python scripts/gmail.py messages list --query "is:unread -from:alice@example.com"

# Emails without attachments
python scripts/gmail.py messages list --query "-has:attachment"

# Not labeled
python scripts/gmail.py messages list --query "-has:userlabels"

# Not in trash or spam
python scripts/gmail.py messages list --query "-in:trash -in:spam"
```

## Practical Examples

### Daily Email Triage

```bash
# Today's unread emails
python scripts/gmail.py messages list --query "is:unread newer_than:1d"

# Important unread from last 3 days
python scripts/gmail.py messages list --query "is:important is:unread newer_than:3d" --max-results 20

# Starred emails I haven't read
python scripts/gmail.py messages list --query "is:starred is:unread"
```

### Project Management

```bash
# All project-related emails
python scripts/gmail.py messages list --query "subject:project-alpha"

# Project emails with attachments
python scripts/gmail.py messages list --query "subject:project-alpha has:attachment"

# Team emails from last sprint (2 weeks)
python scripts/gmail.py messages list --query "from:team@example.com newer_than:14d"

# Unread project emails
python scripts/gmail.py messages list --query "label:project-alpha is:unread"
```

### Finding Specific Content

```bash
# Invoice emails
python scripts/gmail.py messages list --query "subject:invoice has:attachment"

# Password reset emails
python scripts/gmail.py messages list --query "subject:password subject:reset"

# Meeting invites from this month
python scripts/gmail.py messages list --query "subject:meeting subject:invite newer_than:1m"

# Receipts with PDFs
python scripts/gmail.py messages list --query "subject:receipt filename:pdf"
```

### Cleanup Tasks

```bash
# Large old emails
python scripts/gmail.py messages list --query "larger:10M older_than:1y"

# Old read emails
python scripts/gmail.py messages list --query "is:read older_than:6m"

# Promotional emails
python scripts/gmail.py messages list --query "category:promotions older_than:30d"

# Social emails older than 3 months
python scripts/gmail.py messages list --query "category:social older_than:3m"
```

### Sender Analysis

```bash
# All emails from domain
python scripts/gmail.py messages list --query "from:@example.com"

# Emails TO a specific domain
python scripts/gmail.py messages list --query "to:@clients.com"

# Emails from boss with attachments
python scripts/gmail.py messages list --query "from:boss@example.com has:attachment"

# Team emails I sent
python scripts/gmail.py messages list --query "to:team@example.com in:sent"
```

## Advanced Patterns

### Date Range Searches

```bash
# Q1 2024 emails
python scripts/gmail.py messages list --query "after:2024/01/01 before:2024/04/01"

# Last year's December
python scripts/gmail.py messages list --query "after:2023/12/01 before:2024/01/01"

# Specific week
python scripts/gmail.py messages list --query "after:2024/01/15 before:2024/01/22"
```

### Multi-Condition Searches

```bash
# Unread, important, with attachments from this week
python scripts/gmail.py messages list \
  --query "is:unread is:important has:attachment newer_than:7d"

# Large PDFs from specific sender in last month
python scripts/gmail.py messages list \
  --query "from:reports@example.com filename:pdf larger:5M newer_than:1m"

# Meeting invites not yet read
python scripts/gmail.py messages list \
  --query "subject:meeting subject:invite is:unread"
```

### Exclusion Patterns

```bash
# Inbox emails excluding newsletters
python scripts/gmail.py messages list \
  --query "in:inbox -category:promotions -category:social -category:updates"

# Emails from domain EXCEPT automated@
python scripts/gmail.py messages list \
  --query "from:@example.com -from:automated@example.com"

# Important emails without certain labels
python scripts/gmail.py messages list \
  --query "is:important -label:archived -label:reviewed"
```

## Tips and Best Practices

### Performance

1. **Use specific operators** - `from:` is faster than searching body text
2. **Add date constraints** - Narrows search space significantly
3. **Limit results** - Use `--max-results` to avoid fetching too many

### Quotes and Escaping

1. **Use quotes for exact phrases**: `"quarterly review"`
2. **Shell quoting**: Wrap entire query in quotes when using shell
   ```bash
   python scripts/gmail.py messages list --query "from:alice subject:meeting"
   ```
3. **Special characters**: Gmail handles most special chars, but quotes need escaping in shell

### Common Mistakes

1. **Date format**: Use `YYYY/MM/DD` not `MM/DD/YYYY`
2. **Time units**: `7d` not `7days`, `2m` not `2months`
3. **Spaces in AND**: `from:alice subject:meeting` (implicit AND) not `from:alice AND subject:meeting`
4. **Case sensitivity**: Most operators are case-insensitive

## Testing Queries

Before using in automation:

1. **Test in Gmail web interface** first
2. **Start broad, then narrow** - Add constraints incrementally
3. **Verify result counts** - Use `--max-results 5` to spot-check

## Additional Resources

- [Official Gmail Search Operators](https://support.google.com/mail/answer/7190)
- [Advanced Gmail Search](https://support.google.com/mail/answer/7190?hl=en)
