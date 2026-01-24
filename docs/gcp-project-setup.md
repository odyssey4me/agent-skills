# Google Cloud Project Setup Guide

This guide walks you through setting up a Google Cloud Platform (GCP) project for use with Google OAuth skills (Gmail, Google Drive, Google Calendar). A single GCP project can be shared across all Google skills.

## Overview

To use Google OAuth skills, you need:

1. A GCP project with billing enabled (free tier is sufficient)
2. Required APIs enabled
3. OAuth consent screen configured
4. OAuth 2.0 client credentials

**Cost**: All required APIs are free within Google's generous quotas. You will not incur charges for personal use. See [Billing Options](#billing-options) for details.

## Prerequisites

- A Google account
- [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install) installed

### Installing gcloud CLI

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

**macOS:**
```bash
brew install --cask google-cloud-sdk
gcloud init
```

**Windows:**
Download and run the installer from https://cloud.google.com/sdk/docs/install

After installation, authenticate:
```bash
gcloud auth login
```

## Step 1: Create a GCP Project

Create a new project for your agent skills:

```bash
# Create the project
gcloud projects create agent-skills-oauth --name="Agent Skills OAuth"

# Set it as the active project
gcloud config set project agent-skills-oauth
```

**Note**: Project IDs must be globally unique. If `agent-skills-oauth` is taken, choose another name like `agent-skills-oauth-12345`.

Verify the project was created:
```bash
gcloud projects describe agent-skills-oauth
```

## Step 2: Enable Billing

Google requires a billing account even for free-tier usage. This is used for identity verification, not charges.

### Option A: Free Tier (No Charges)

The free tier includes generous quotas sufficient for personal use:

| API | Free Quota |
|-----|------------|
| Gmail API | 1 billion quota units/day |
| Google Drive API | 1 billion quota units/day |
| Google Calendar API | 1 million queries/day |

To use the free tier, you still need to link a billing account, but you won't be charged within these limits.

### Option B: Link an Existing Billing Account

If you already have a billing account:

```bash
# List your billing accounts
gcloud billing accounts list

# Link billing account to project (replace BILLING_ACCOUNT_ID)
gcloud billing projects link agent-skills-oauth \
  --billing-account=BILLING_ACCOUNT_ID
```

### Option C: Create a New Billing Account

If you don't have a billing account, create one in the Cloud Console:

1. Go to https://console.cloud.google.com/billing
2. Click **Create Account**
3. Follow the prompts to add payment information
4. Link the billing account to your project:
   ```bash
   gcloud billing accounts list
   gcloud billing projects link agent-skills-oauth \
     --billing-account=BILLING_ACCOUNT_ID
   ```

**Note**: Google offers a $300 free trial credit for new accounts. See [Google Cloud Free Program](https://cloud.google.com/free) for details.

## Step 3: Enable Required APIs

Enable the APIs for the Google skills you plan to use:

```bash
# Enable all Google Workspace APIs (recommended)
gcloud services enable \
  gmail.googleapis.com \
  drive.googleapis.com \
  calendar-json.googleapis.com

# Or enable individually
gcloud services enable gmail.googleapis.com      # For Gmail skill
gcloud services enable drive.googleapis.com      # For Google Drive skill
gcloud services enable calendar-json.googleapis.com  # For Google Calendar skill
```

Verify APIs are enabled:
```bash
gcloud services list --enabled --filter="name:(gmail OR drive OR calendar)"
```

## Step 4: Configure OAuth Consent Screen

The OAuth consent screen is what users see when authorizing your application.

### Choosing User Type: Internal vs External

When configuring the OAuth consent screen, you must choose a user type:

| User Type | When to Use | Requirements | Limitations |
|-----------|-------------|--------------|-------------|
| **Internal** | You have Google Workspace (formerly G Suite) and only need access for users within your organization | Google Workspace subscription | Only users in your Workspace domain can authenticate |
| **External** | Personal Gmail accounts, or you need users outside your organization to authenticate | None | Requires adding test users while in "Testing" mode; shows "unverified app" warning |

**Choose Internal if:**
- You have a Google Workspace account (e.g., `alice@acme.com`)
- You only need to authenticate with accounts from your Workspace domain
- You want to skip the test user setup and unverified app warnings

**Choose External if:**
- You use a personal Gmail account (e.g., `alice@gmail.com`)
- You need to authenticate with accounts outside your organization
- You don't have Google Workspace

**Recommendation**: Most personal users should choose **External**. The "unverified app" warning during OAuth can be safely clicked through for personal use.

### Configure via Cloud Console

1. Go to https://console.cloud.google.com/apis/credentials/consent
2. Select your **User Type**:
   - **Internal** - If you have Google Workspace and only need your organization's accounts
   - **External** - For personal Gmail or if you need accounts outside your organization
3. Click **Create**
4. Fill in required fields:
   - **App name**: `Agent Skills`
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click **Save and Continue**
6. On **Scopes** page, click **Add or Remove Scopes**
7. Add these scopes (filter by "Gmail", "Drive", "Calendar"):
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.labels`
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/drive.metadata.readonly`
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/calendar.events`
8. Click **Save and Continue**
9. On **Test users** page (External user type only):
   - **Skip this step if you chose Internal** - all users in your Workspace domain can authenticate automatically
   - For External: Click **Add Users**
   - Add your Google account email (the one you'll authenticate with)
   - Click **Save and Continue**
10. Review and click **Back to Dashboard**

**Important for External user type**: While your app is in "Testing" mode, only test users you explicitly added can authenticate. For personal use, this is fine - just add your own email. See [Publishing Your App](#publishing-your-app-optional) if you need wider access.

**Note for Internal user type**: There is no test user requirement. Any user in your Google Workspace organization can authenticate immediately.

## Step 5: Create OAuth 2.0 Client Credentials

Create OAuth client credentials for desktop applications:

```bash
# Create OAuth client ID
gcloud alpha iap oauth-clients create \
  $(gcloud alpha iap oauth-brands list --format='value(name)') \
  --display_name="Agent Skills Desktop Client"
```

**Note**: If the above command fails, create credentials via Cloud Console:

1. Go to https://console.cloud.google.com/apis/credentials
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Application type**: **Desktop app**
4. Enter name: `Agent Skills Desktop Client`
5. Click **Create**
6. **Copy the Client ID and Client Secret** - you'll need these

## Step 6: Configure Skills with Credentials

Store your OAuth credentials for use with all Google skills:

### Option A: Shared Config File (Recommended)

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

### Option B: Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export GOOGLE_CLIENT_ID="YOUR_CLIENT_ID.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="YOUR_CLIENT_SECRET"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Step 7: Verify Setup

Test authentication with each skill:

```bash
# Verify Gmail
python ~/.claude/skills/gmail/scripts/gmail.py check

# Verify Google Drive
python ~/.claude/skills/google-drive/scripts/google-drive.py check

# Verify Google Calendar
python ~/.claude/skills/google-calendar/scripts/google-calendar.py check
```

On first run, your browser will open for OAuth authorization. After granting access, tokens are stored securely in your system keyring.

## Billing Options

### Free Tier Limits

Google provides generous free quotas that are more than sufficient for personal use:

| API | Daily Free Quota | Typical Personal Usage |
|-----|------------------|------------------------|
| Gmail API | 1 billion units | ~10,000 emails/day |
| Drive API | 1 billion units | ~10,000 operations/day |
| Calendar API | 1 million queries | ~1,000 operations/day |

You will not be charged unless you exceed these limits, which is extremely unlikely for personal use.

### Monitoring Usage

Check your API usage:

```bash
# View quota usage in Cloud Console
gcloud services list --enabled
```

Or visit: https://console.cloud.google.com/apis/dashboard

### Setting Budget Alerts (Optional)

To ensure you're never charged unexpectedly:

1. Go to https://console.cloud.google.com/billing/budgets
2. Click **Create Budget**
3. Set budget to $0 or $1
4. Configure email alerts at 50%, 90%, 100%

## Multiple Projects (Optional)

While a single project is recommended, you can optionally use separate projects for each skill. Each project would need its own API enablement and OAuth credentials. This adds complexity without significant benefit for personal use.

## Publishing Your App (Optional)

By default, your OAuth app is in "Testing" mode:
- Only test users (added in Step 4) can authenticate
- You see an "unverified app" warning during OAuth flow

For personal use, this is fine. To remove the warning or allow other users:

1. Go to https://console.cloud.google.com/apis/credentials/consent
2. Click **Publish App**
3. For sensitive scopes (Gmail, Drive), Google requires verification
4. Verification requires domain ownership and privacy policy

**Recommendation**: For personal use, stay in Testing mode and add yourself as a test user. Simply click through the "unverified app" warning during OAuth.

## Troubleshooting

### "Billing account not found"

```bash
# List available billing accounts
gcloud billing accounts list

# If empty, create one at:
# https://console.cloud.google.com/billing
```

### "API not enabled"

```bash
# Check which APIs are enabled
gcloud services list --enabled

# Enable missing APIs
gcloud services enable gmail.googleapis.com drive.googleapis.com calendar-json.googleapis.com
```

### "Access blocked: This app's request is invalid"

- Ensure OAuth consent screen is configured
- Verify you added yourself as a test user
- Check that the OAuth client is type "Desktop app"

### "The OAuth client was not found"

- Verify Client ID and Secret are correct
- Check credentials at https://console.cloud.google.com/apis/credentials

### "Quota exceeded"

- Check usage at https://console.cloud.google.com/apis/dashboard
- Wait for quota reset (daily)
- Request quota increase if needed (free for most cases)

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use config files** with restricted permissions (600)
3. **Review connected apps** periodically at https://myaccount.google.com/permissions
4. **Use minimal scopes** - only enable APIs you need
5. **Monitor API usage** in Cloud Console

## Quick Reference

| Action | Command |
|--------|---------|
| Create project | `gcloud projects create agent-skills-oauth` |
| Set active project | `gcloud config set project agent-skills-oauth` |
| Enable Gmail API | `gcloud services enable gmail.googleapis.com` |
| Enable Drive API | `gcloud services enable drive.googleapis.com` |
| Enable Calendar API | `gcloud services enable calendar-json.googleapis.com` |
| List enabled APIs | `gcloud services list --enabled` |
| View billing accounts | `gcloud billing accounts list` |
| Link billing | `gcloud billing projects link PROJECT --billing-account=ID` |

## Additional Resources

- [Google Cloud Free Program](https://cloud.google.com/free)
- [OAuth 2.0 Overview](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Drive API Documentation](https://developers.google.com/drive/api)
- [Calendar API Documentation](https://developers.google.com/calendar)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Managing API Quotas](https://cloud.google.com/docs/quota)
