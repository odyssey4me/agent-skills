# Google OAuth Setup Guide

This guide explains how to configure OAuth 2.0 authentication for Google skills (Gmail, Google Drive, Google Calendar).

## Prerequisites

Before configuring any Google skill, you need a Google Cloud Project with OAuth credentials. Follow the [GCP Project Setup Guide](gcp-project-setup.md) to:

1. Create a GCP project
2. Enable required APIs
3. Configure OAuth consent screen
4. Create OAuth client credentials

A single GCP project and OAuth client can be shared across all Google skills.

## Configuring Credentials

Once you have OAuth client credentials from your GCP project, configure them for all Google skills using one of these methods:

### Option 1: Shared Config File (Recommended)

Create `~/.config/agent-skills/google.yaml`:

```yaml
oauth_client:
  client_id: YOUR_CLIENT_ID.apps.googleusercontent.com
  client_secret: YOUR_CLIENT_SECRET
```

Set secure permissions:
```bash
chmod 600 ~/.config/agent-skills/google.yaml
```

This single config file works for all Google skills.

### Option 2: Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export GOOGLE_CLIENT_ID="YOUR_CLIENT_ID.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Option 3: Skill-Specific Config

You can override shared credentials for individual skills by creating skill-specific config files:

- Gmail: `~/.config/agent-skills/gmail.yaml`
- Google Drive: `~/.config/agent-skills/google-drive.yaml`
- Google Calendar: `~/.config/agent-skills/google-calendar.yaml`

Format:
```yaml
oauth_client:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET
```

### Credential Priority Order

OAuth credentials are resolved in this order:

1. **Service-specific config file** (e.g., `gmail.yaml`)
2. **Service-specific environment variables** (e.g., `GMAIL_CLIENT_ID`)
3. **Shared config file** (`google.yaml`)
4. **Shared environment variables** (`GOOGLE_CLIENT_ID`)

## First Authentication

Run the `check` command for any Google skill to trigger the OAuth flow:

```bash
# Gmail
python scripts/gmail.py check

# Google Drive
python scripts/google-drive.py check

# Google Calendar
python scripts/google-calendar.py check
```

This will:
1. Open your browser automatically
2. Ask you to select a Google account
3. Show the OAuth consent screen with requested permissions
4. Ask you to allow access
5. Redirect to localhost (showing success)
6. Store the OAuth token in your system keyring

**On subsequent runs**, the skill uses the stored token automatically and refreshes it when needed.

## OAuth Scopes by Skill

Each skill requests specific scopes. When you authenticate with a skill for the first time, you grant access only to the scopes that skill needs.

### Gmail Scopes

| Scope | Permission | Used For |
|-------|-----------|----------|
| `gmail.readonly` | Read email messages and settings | Listing and reading messages |
| `gmail.send` | Send email | Sending messages and drafts |
| `gmail.modify` | Modify labels and metadata | Managing labels on messages |
| `gmail.labels` | Manage labels | Creating and listing labels |

### Google Drive Scopes

| Scope | Permission | Used For |
|-------|-----------|----------|
| `drive.readonly` | Read files and metadata | list, search, download |
| `drive` | Full read/write access to all files | upload, create folders, share, move |
| `drive.metadata.readonly` | View file metadata only | get file info |

### Google Calendar Scopes

| Scope | Permission | Used For |
|-------|-----------|----------|
| `calendar.readonly` | Read calendar events | Listing and viewing events, calendars, and availability |
| `calendar.events` | Manage events | Creating, updating, and deleting events |

### Google Docs Scopes

| Scope | Permission | Used For |
|-------|-----------|----------|
| `documents.readonly` | Read documents | Reading document content and metadata |
| `documents` | Manage documents | Creating, editing, and deleting documents |

### Google Sheets Scopes

| Scope | Permission | Used For |
|-------|-----------|----------|
| `spreadsheets.readonly` | Read spreadsheets | Reading cell values and metadata |
| `spreadsheets` | Manage spreadsheets | Creating, editing spreadsheets, and managing sheets |

### Google Slides Scopes

| Scope | Permission | Used For |
|-------|-----------|----------|
| `presentations.readonly` | Read presentations | Reading presentation content and metadata |
| `presentations` | Manage presentations | Creating, editing, and managing slides |

**Note**: OAuth tokens are stored separately per skill, as each skill requests different scopes.

## Security Best Practices

### Credential Storage

- **Client ID/Secret**: Stored in config files with permissions 600 (owner read/write only)
- **OAuth Tokens**: Stored securely in system keyring:
  - **Linux**: Secret Service (GNOME Keyring, KWallet)
  - **macOS**: Keychain
  - **Windows**: Credential Manager

### Revoking Access

To revoke OAuth tokens:

1. **Via Google Account**:
   - Go to https://myaccount.google.com/permissions
   - Find your OAuth app
   - Click **Remove Access**

2. **Via keyring** (Linux example):
   ```bash
   pip install --user keyring

   # Gmail
   keyring del agent-skills gmail-token-json

   # Google Drive
   keyring del agent-skills google-drive-token-json

   # Google Calendar
   keyring del agent-skills google-calendar-token-json
   ```

3. **Re-authenticate** by running the skill's `check` command.

## Troubleshooting

### Auth reset workflow

Most authentication problems (expired tokens, insufficient scopes, permission
denied) can be resolved with the same two-step process:

1. **Reset the token**: `<skill-script> auth reset`
2. **Re-authenticate**: `<skill-script> check`

The `check` command opens a browser for OAuth consent — this requires user
interaction and cannot be completed autonomously by an agent. If you are an
AI agent, **stop and inform the user** when you encounter auth errors rather
than retrying or attempting to fix the issue yourself.

### GCP project verification checklist

If auth reset doesn't resolve the issue, verify the GCP project setup:

- [ ] Required API is enabled (e.g., Gmail API, Drive API) — see [GCP Project Setup Guide](gcp-project-setup.md)
- [ ] OAuth consent screen is configured
- [ ] Your Google account is added as a test user (for External user type)
- [ ] OAuth client type is "Desktop app"
- [ ] Client ID and secret in `~/.config/agent-skills/google.yaml` match the GCP console

### "Access blocked: This app's request is invalid"

- OAuth consent screen is not properly configured
- Verify you added yourself as a test user (for External user type)
- See [GCP Project Setup Guide](gcp-project-setup.md#step-4-configure-oauth-consent-screen)

### "Error 400: redirect_uri_mismatch"

- OAuth client is not configured as "Desktop app"
- Delete the client and create a new one with type "Desktop app"

### "The OAuth client was not found"

- Client ID or secret is incorrect
- Verify credentials in Google Cloud Console under **Credentials**

### "Token has been expired or revoked"

Run the [auth reset workflow](#auth-reset-workflow) to clear the stored token and re-authenticate.

### "insufficient_scope"

Run the [auth reset workflow](#auth-reset-workflow). If that doesn't work:

- Revoke access at https://myaccount.google.com/permissions
- Then run `auth reset` and `check` again

### "Permission denied"

Run the [auth reset workflow](#auth-reset-workflow). If the error persists, verify your GCP project has the required API enabled using the [checklist above](#gcp-project-verification-checklist).

### Browser doesn't open

The skill uses Python's `webbrowser` module. If it fails, copy and paste the printed URL into your browser manually.

### Rate limits or quota errors

1. Check your project's quota in Google Cloud Console
2. Request quota increases if needed for high-volume usage
3. See [GCP Project Setup Guide](gcp-project-setup.md#billing-options) for quota details

## Additional Resources

- [GCP Project Setup Guide](gcp-project-setup.md)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [Google Calendar API Documentation](https://developers.google.com/calendar)
- [OAuth 2.0 Overview](https://developers.google.com/identity/protocols/oauth2)
- [Google Account Permissions](https://myaccount.google.com/permissions)
