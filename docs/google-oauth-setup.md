# Google OAuth Setup Guide

This guide explains how to configure OAuth 2.0 authentication for the Google Workspace skill using `gog` ([gogcli](https://github.com/openclaw/gogcli)).

## Prerequisites

Before configuring the Google skill, you need:

1. A Google Cloud Project with OAuth credentials — follow the [GCP Project Setup Guide](gcp-project-setup.md)
2. The `gog` CLI installed — see [installation instructions](../skills/google/references/configuration.md)

A single GCP project and OAuth client can be shared across all Google services (Gmail, Calendar, Drive, Docs, Sheets, Slides).

## Configuring Credentials

### Option 1: Interactive Setup (Recommended)

```bash
# Guided setup — creates OAuth client and authorizes your account
gog auth setup
```

This walks you through:
1. Setting up OAuth client credentials
2. Authorizing your Google account
3. Storing tokens securely in the system keyring

### Option 2: Import Existing Credentials

If you already have a `credentials.json` from Google Cloud Console:

```bash
# Import OAuth client credentials
gog auth credentials set credentials.json

# Authorize with only the services you need (opens browser)
gog auth add your@email.com --services gmail,calendar,drive,docs,sheets,slides
```

### Option 3: Non-Interactive Import

For CI or headless environments:

```bash
# Import refresh token from environment variable
gog auth import --email your@email.com --refresh-token-env MY_REFRESH_TOKEN
```

## Verify Setup

```bash
# Run diagnostics
gog auth doctor

# Or use the skill check command
skills/google/scripts/google.py check
```

## Migrating from Legacy Python OAuth

If you previously used the per-service Python-based Google skills (gmail, google-calendar, etc.), clean up the old tokens and config:

```bash
skills/google/scripts/google.py cleanup
```

This removes legacy keyring tokens and config files (`~/.config/agent-skills/google.yaml`, per-service YAML files). Then set up fresh authentication with gog using the steps above.

## OAuth Scopes

gog manages scopes automatically based on the services you use. When you authorize with `gog auth add`, it requests scopes for all supported services. You can restrict to read-only scopes:

```bash
gog auth add your@email.com --readonly
```

## Security Best Practices

### Credential Storage

- **OAuth client credentials**: Stored in gog's keyring (`~/.local/share/gogcli/keyring/`)
- **Refresh tokens**: Stored in the system keyring (OS keychain) or encrypted file backend
- **Access tokens**: Short-lived (1 hour), never persisted to disk

### Encrypted File Backend

For headless environments without a system keyring:

```bash
export GOG_KEYRING_BACKEND=file
export GOG_KEYRING_PASSWORD="your-encryption-password"
gog auth add your@email.com
```

### Revoking Access

```bash
# Remove stored tokens for an account
gog auth remove your@email.com

# Also revoke via Google Account
# Visit: https://myaccount.google.com/permissions
```

### Agent Safety

When running gog from AI agents, use safety flags:

```bash
# Read-only mode — blocks all mutations
gog --readonly gmail search "test"

# Block Gmail send specifically
gog --gmail-no-send gmail search "test"

# Disable interactive prompts (fail instead of hanging)
gog --no-input calendar events --today
```

## Troubleshooting

### Auth reset workflow

Most authentication problems can be resolved by re-authorizing:

```bash
gog auth remove your@email.com
gog auth add your@email.com
```

If you are an AI agent, **stop and inform the user** when you encounter auth errors (exit code 4) rather than retrying.

### "Auth required" (exit code 4)

```bash
gog auth doctor    # diagnose the issue
gog auth setup     # re-run setup if needed
```

### GCP project verification checklist

If re-authorization doesn't help:

- [ ] Required API is enabled (e.g., Gmail API, Drive API) — see [GCP Project Setup Guide](gcp-project-setup.md)
- [ ] OAuth consent screen is configured
- [ ] Your Google account is added as a test user (for External user type)
- [ ] OAuth client type is "Desktop app"

### Rate limits or quota errors (exit code 7)

1. Wait briefly and retry — gog exit code 7 means rate limited
2. Check your project's quota at https://console.cloud.google.com/apis/dashboard
3. See [GCP Project Setup Guide](gcp-project-setup.md#billing-options) for quota details

## Additional Resources

- [GCP Project Setup Guide](gcp-project-setup.md)
- [gogcli documentation](https://gogcli.sh/)
- [Google Workspace skill reference](../skills/google/SKILL.md)
- [Configuration reference](../skills/google/references/configuration.md)
- [OAuth 2.0 Overview](https://developers.google.com/identity/protocols/oauth2)
- [Google Account Permissions](https://myaccount.google.com/permissions)
