# Google Drive OAuth Setup Guide

This guide explains how to set up OAuth 2.0 authentication for the Google Drive skill.

## Method 1: gcloud CLI (Recommended)

If you have the Google Cloud SDK installed, this is the simplest approach.

### Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- A Google account

### Steps

1. **Install gcloud CLI** (if not already installed):
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Ubuntu/Debian
   sudo apt-get install google-cloud-sdk

   # Or download from https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate with Drive scopes**:

   **Read-only access:**
   ```bash
   gcloud auth application-default login \
     --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly
   ```

   **Full access (recommended):**
   ```bash
   gcloud auth application-default login \
     --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/drive.metadata.readonly
   ```

3. **Verify authentication**:
   ```bash
   python scripts/google-drive.py check
   ```

### Revoking Access

To revoke gcloud credentials:

```bash
gcloud auth application-default revoke
```

Then re-authenticate with the desired scopes.

## Method 2: Custom OAuth 2.0 Credentials

If you cannot use gcloud CLI or need custom credentials.

### Prerequisites

- A Google Cloud Platform account
- Access to Google Cloud Console

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top
3. Click "New Project"
4. Enter a project name (e.g., "Agent Skills")
5. Click "Create"

### Step 2: Enable the Drive API

1. In your project, go to **APIs & Services** > **Library**
2. Search for "Google Drive API"
3. Click on it and click **Enable**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** user type (unless you have Google Workspace)
3. Click **Create**
4. Fill in the required fields:
   - App name: "Agent Skills" (or your preferred name)
   - User support email: Your email
   - Developer contact: Your email
5. Click **Save and Continue**

6. On the **Scopes** page:
   - Click **Add or Remove Scopes**
   - Add these scopes:
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/drive.file`
     - `https://www.googleapis.com/auth/drive.metadata.readonly`
   - Click **Update**
   - Click **Save and Continue**

7. On the **Test users** page:
   - Click **Add Users**
   - Add your email address
   - Click **Save and Continue**

8. Review and click **Back to Dashboard**

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Application type: **Desktop app**
4. Name: "Agent Skills Drive" (or your preferred name)
5. Click **Create**
6. **Copy the Client ID and Client Secret** (you'll need these)

### Step 5: Configure the Skill

Store the credentials using the skill command:

```bash
python scripts/google-drive.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

Alternatively, set environment variables:

```bash
export GOOGLE_DRIVE_CLIENT_ID="your-client-id"
export GOOGLE_DRIVE_CLIENT_SECRET="your-client-secret"
```

Or create a config file at `~/.config/agent-skills/google-drive.yaml`:

```yaml
oauth_client:
  client_id: "your-client-id"
  client_secret: "your-client-secret"
```

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

1. **Service-specific config file** (e.g., `google-drive.yaml`)
2. **Service-specific environment variables** (e.g., `GOOGLE_DRIVE_CLIENT_ID`)
3. **Shared config file** (`google.yaml`)
4. **Shared environment variables** (`GOOGLE_CLIENT_ID`)

This allows you to use shared credentials for most skills while overriding for specific skills if needed.

**Note**: OAuth tokens are still stored separately per skill, as each skill may request different scopes.

### Step 6: First Run

On your first command, a browser window will open asking you to authorize the application:

```bash
python scripts/google-drive.py files list
```

1. Select your Google account
2. Click "Continue" (you may see a warning since the app is in testing mode)
3. Review the permissions and click "Allow"
4. The browser will show "The authentication flow has completed"
5. Return to your terminal

The OAuth token is now stored securely in your system keyring for future use.

## Troubleshooting

### "Access blocked: This app's request is invalid"

Your OAuth consent screen may not be configured correctly:
1. Ensure you've added yourself as a test user
2. Verify the redirect URI is set correctly

### "Insufficient scope" errors

Re-authenticate with the required scopes:
```bash
gcloud auth application-default revoke
gcloud auth application-default login --scopes=...
```

Or for custom OAuth, delete the stored token and re-run a command to trigger a new OAuth flow.

### Token refresh failed

If token refresh fails, clear the stored credentials:

```bash
# For gcloud
gcloud auth application-default revoke

# For custom OAuth, use keyring CLI or delete manually
python -c "import keyring; keyring.delete_password('agent-skills', 'google-drive-token-json')"
```

Then re-authenticate.

### Rate limits or quota errors

1. Check your project's quota in Google Cloud Console
2. Request quota increases if needed for high-volume usage

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** or config files with restricted permissions
3. **Regularly review** OAuth tokens and revoke unused ones
4. **Use minimal scopes** - start with read-only and expand as needed
5. **Monitor API usage** in Google Cloud Console

## Scope Reference

| Scope | Permission | Required For |
|-------|------------|--------------|
| `drive.readonly` | Read files and metadata | list, search, download |
| `drive.file` | Create/edit files created by app | upload, create folders, share |
| `drive.metadata.readonly` | View file metadata only | get file info |

For most use cases, `drive.readonly` + `drive.file` provides a good balance of functionality and security.
