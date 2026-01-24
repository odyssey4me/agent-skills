# Google Calendar OAuth 2.0 Setup Guide

This guide covers two authentication methods for the Google Calendar skill:

1. **Method 1: gcloud CLI** (Recommended) - Zero-config for gcloud users
2. **Method 2: Custom OAuth 2.0** - Self-contained authentication

## Method 1: gcloud CLI (Recommended)

If you have the Google Cloud SDK installed, this is the simplest method.

### Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- A Google account with Google Calendar access

### Steps

1. **Install gcloud SDK** (if not already installed):

   **Linux:**
   ```bash
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

   **macOS:**
   ```bash
   brew install --cask google-cloud-sdk
   ```

   **Windows:**
   Download from https://cloud.google.com/sdk/docs/install

2. **Authenticate with Application Default Credentials**:

   ```bash
   gcloud auth application-default login \
     --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/calendar.events
   ```

   **Note**: The `cloud-platform` scope is required by gcloud in addition to the Calendar-specific scopes.

   This will:
   - Open your browser
   - Prompt you to sign in with your Google account
   - Ask you to grant permissions for Calendar access
   - Store credentials in `~/.config/gcloud/application_default_credentials.json`

3. **Verify authentication**:

   ```bash
   python scripts/google-calendar.py check
   ```

   You should see:
   ```
   ✓ Successfully authenticated to Google Calendar
     Primary Calendar: Your Name
     Calendar ID: your-email@gmail.com
     Timezone: America/New_York
   ```

### Benefits

- **Zero configuration** - No client IDs or secrets needed
- **Automatic token refresh** - gcloud handles token lifecycle
- **Production-grade** - Uses Google's official OAuth flow
- **Secure** - Credentials managed by gcloud

### Revoking Access

To revoke and re-authenticate:

```bash
# Revoke current credentials
gcloud auth application-default revoke

# Re-authenticate with new account
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/calendar.events
```

## Method 2: Custom OAuth 2.0 Credentials

Use this method if you don't have gcloud or prefer custom OAuth credentials.

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** > **New Project**
3. Enter a project name (e.g., "Calendar Skill")
4. Click **Create**
5. Wait for project creation, then select it

### Step 2: Enable Google Calendar API

1. In your project, go to **APIs & Services** > **Library**
2. Search for "Google Calendar API"
3. Click on **Google Calendar API**
4. Click **Enable**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **User Type**:
   - **External** - For personal Google accounts (recommended for testing)
   - **Internal** - Only if you have a Google Workspace organization
3. Click **Create**
4. Fill in required fields:
   - **App name**: "Calendar Skill" (or any name)
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click **Save and Continue**
6. On **Scopes** page, click **Add or Remove Scopes**:
   - Search for "Google Calendar API"
   - Select these scopes:
     - `.../auth/calendar.readonly` - Read calendar events
     - `.../auth/calendar.events` - Create, update, delete events
   - Click **Update**
7. Click **Save and Continue**
8. On **Test users** page (for External apps):
   - Click **Add Users**
   - Enter your Google account email address
   - Click **Add**
   - Click **Save and Continue**
9. Review summary and click **Back to Dashboard**

### Step 4: Create OAuth 2.0 Client ID

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Application type**: **Desktop app**
4. Enter a name: "Calendar Skill Client"
5. Click **Create**
6. A dialog appears with your **Client ID** and **Client Secret**
   - **Save these somewhere safe!**
   - You can also download the JSON file (optional)
7. Click **OK**

### Step 5: Store Credentials in Skill

Store your OAuth client credentials:

```bash
python scripts/google-calendar.py auth setup \
  --client-id YOUR_CLIENT_ID_HERE \
  --client-secret YOUR_CLIENT_SECRET_HERE
```

This saves credentials to `~/.config/agent-skills/google-calendar.yaml`:

```yaml
oauth_client:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET
```

**Security note**: This file has permissions 600 (owner read/write only).

### Step 6: First Authentication

Run any Calendar command to trigger the OAuth flow:

```bash
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

### Step 7: Verify

```bash
python scripts/google-calendar.py check
```

You should see:
```
✓ Successfully authenticated to Google Calendar
  Primary Calendar: Your Name
  Calendar ID: your-email@gmail.com
  Timezone: America/New_York
```

## Alternative: Environment Variables

Instead of `google-calendar.py auth setup`, you can use environment variables:

```bash
export GOOGLE_CALENDAR_CLIENT_ID="your-client-id"
export GOOGLE_CALENDAR_CLIENT_SECRET="your-client-secret"
```

Add to `~/.bashrc` or `~/.zshrc` for persistence.

## Shared Credentials for Multiple Google Skills

If you use multiple Google skills (Gmail, Google Drive, Google Calendar), you can share OAuth client credentials instead of configuring each skill separately.

### Shared Config File

Create `~/.config/agent-skills/google.yaml`:

```yaml
oauth_client:
  client_id: your-client-id.apps.googleusercontent.com
  client_secret: your-client-secret
```

### Shared Environment Variables

```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

### Priority Order

OAuth credentials are resolved in this order:

1. **Service-specific config file** (e.g., `google-calendar.yaml`)
2. **Service-specific environment variables** (e.g., `GOOGLE_CALENDAR_CLIENT_ID`)
3. **Shared config file** (`google.yaml`)
4. **Shared environment variables** (`GOOGLE_CLIENT_ID`)

This allows you to use shared credentials for most skills while overriding for specific skills if needed.

**Note**: OAuth tokens are still stored separately per skill, as each skill may request different scopes.

## Security Best Practices

### Credential Storage

- **Client ID/Secret**: Stored in `~/.config/agent-skills/google-calendar.yaml` (permissions 600)
- **OAuth Tokens**: Stored securely in system keyring:
  - **Linux**: Secret Service (GNOME Keyring, KWallet)
  - **macOS**: Keychain
  - **Windows**: Credential Manager

### OAuth Token Lifecycle

1. **Initial authentication**: Browser-based OAuth flow
2. **Token storage**: Access token + refresh token saved to keyring
3. **Automatic refresh**: When access token expires, refresh token is used
4. **Re-authentication**: Only needed if refresh token expires (rare)

### Revoking Access

To revoke OAuth tokens:

1. **Via Google Account**:
   - Go to https://myaccount.google.com/permissions
   - Find your OAuth app
   - Click **Remove Access**

2. **Via keyring** (Linux example):
   ```bash
   # Install keyring CLI
   pip install --user keyring

   # Delete stored token
   keyring del agent-skills google-calendar-token-json
   ```

3. **Re-authenticate**:
   ```bash
   python scripts/google-calendar.py check
   # Will trigger new OAuth flow
   ```

## Troubleshooting

### "Access blocked: This app's request is invalid"

- Your OAuth consent screen is not properly configured
- Go back to **OAuth consent screen** and ensure all required fields are filled
- Verify you added yourself as a test user (for External apps)

### "Error 400: redirect_uri_mismatch"

- OAuth client is not configured as "Desktop app"
- Delete the client and create a new one with type "Desktop app"

### "The OAuth client was not found"

- Client ID or secret is incorrect
- Verify credentials in Google Cloud Console under **Credentials**
- Re-run `python scripts/google-calendar.py auth setup` with correct values

### "Token has been expired or revoked"

- Token was revoked in Google Account settings
- Delete stored token and re-authenticate:
  ```bash
  keyring del agent-skills google-calendar-token-json
  python scripts/google-calendar.py check
  ```

### "insufficient_scope: Request had insufficient authentication scopes"

- OAuth flow didn't request all necessary scopes
- Revoke access: https://myaccount.google.com/permissions
- Delete stored token: `keyring del agent-skills google-calendar-token-json`
- Re-authenticate: `python scripts/google-calendar.py check`

### Browser doesn't open

- The skill uses Python's `webbrowser` module to open the OAuth URL
- If it fails, you'll see the URL printed to console
- Copy and paste the URL into your browser manually

### "Connection refused" on localhost redirect

- Another application is using the OAuth callback port
- The skill uses port 0 (random available port)
- If issues persist, check firewall settings

## Publishing Your App (Optional)

If you want to use the skill without "unverified app" warnings:

1. Go to **OAuth consent screen**
2. Click **Publish App**
3. Submit for Google verification (requires domain ownership proof)
4. Wait for approval (can take weeks)

**Note**: For personal use, verification is not required. You can safely skip the "unverified app" warning during OAuth flow.

## OAuth Scopes Reference

The Google Calendar skill requests these OAuth scopes:

| Scope | Permission | Used For |
|-------|-----------|----------|
| `https://www.googleapis.com/auth/calendar.readonly` | Read calendar events | Listing and viewing events, calendars, and availability |
| `https://www.googleapis.com/auth/calendar.events` | Manage events | Creating, updating, and deleting events |

## Additional Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar)
- [OAuth 2.0 Overview](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Account Permissions](https://myaccount.google.com/permissions)
