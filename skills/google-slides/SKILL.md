---
name: google-slides
description: Markdown-driven presentation builder with Google Slides upload. Write Markdown, build .pptx locally, review in LibreOffice, upload to Google Slides.
metadata:
  author: odyssey4me
  version: "1.0.0"
  category: google-workspace
  tags: "presentations, slides"
  complexity: standard
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/google-slides.py:*)
---

# Google Slides

Build presentations from Markdown files with YAML frontmatter. The skill
generates .pptx files locally using python-pptx, with optional upload to
Google Slides via the Drive API. A round-trip workflow lets you download an
existing presentation as Markdown, edit it, rebuild, and re-upload.

## Installation

**Required Python packages:**

```bash
pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml
```

**For local .pptx building:**

```bash
pip install --user python-pptx cairosvg
```

**Optional system dependency:** LibreOffice (for `preview` command). The
skill auto-detects `libreoffice`, `soffice`, Flatpak, or the path set in
the `LIBREOFFICE_PATH` environment variable.

## Setup Verification

After installation, verify the skill is properly configured:

```bash
$SKILL_DIR/scripts/google-slides.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml, python-pptx, cairosvg)
- Authentication configuration
- Connectivity to Google APIs
- LibreOffice availability (optional)

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Slides uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/gcp-project-setup.md) - Create project, enable Drive API
2. [Google OAuth Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md) - Configure credentials

### Quick Start

1. Create `~/.config/agent-skills/google.yaml`:
   ```yaml
   oauth_client:
     client_id: your-client-id.apps.googleusercontent.com
     client_secret: your-client-secret
   ```

2. Run `$SKILL_DIR/scripts/google-slides.py check` to trigger OAuth flow and verify setup.

On scope or authentication errors, see the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

## Script Usage

See [permissions.md](references/permissions.md) for read/write classification of each command.

```bash
# Setup and auth
$SKILL_DIR/scripts/google-slides.py check
$SKILL_DIR/scripts/google-slides.py auth setup --client-id ID --client-secret SECRET
$SKILL_DIR/scripts/google-slides.py auth reset
$SKILL_DIR/scripts/google-slides.py auth status

# Build a presentation from Markdown
$SKILL_DIR/scripts/google-slides.py create --file deck.md
$SKILL_DIR/scripts/google-slides.py create --file deck.md --output deck.pptx --palette redhat-brand
$SKILL_DIR/scripts/google-slides.py create --file deck.md --title "My Deck"  # build and upload

# Download a presentation as Markdown
$SKILL_DIR/scripts/google-slides.py get PRESENTATION_ID
$SKILL_DIR/scripts/google-slides.py get PRESENTATION_ID -o deck.md

# Upload or replace slides in an existing presentation
$SKILL_DIR/scripts/google-slides.py update PRESENTATION_ID --file deck.pptx
$SKILL_DIR/scripts/google-slides.py update PRESENTATION_ID --file deck.pptx --mode append

# Preview and verify
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx --format summary
$SKILL_DIR/scripts/google-slides.py verify --file deck.pptx

# List available color palettes
$SKILL_DIR/scripts/google-slides.py palettes
```

See [command-reference.md](references/command-reference.md) for full argument details and examples.

## Markdown Format

Presentations are written as Markdown files with YAML frontmatter. Slides
are separated by `---` on its own line. Slide types are set with HTML
comment directives.

```markdown
---
title: Team Update
subtitle: Q2 2026
author: Jane Smith
date: 2026-06-23
palette: redhat-brand
---

# Team Update

## Q2 2026

> Speaker notes go in blockquotes.

---

<!-- type: section -->

# Progress Review

---

## Key Metrics

- Revenue: $1.2M (up 15%)
- Active users: 50,000
- NPS: 72

::icon:trending-up::

> Mention the NPS improvement from last quarter.

---

<!-- type: two-column -->

## Comparison

<!-- left -->

### Before

- Manual process
- 3-day turnaround
- Error-prone

<!-- right -->

### After

- Fully automated
- 15-minute turnaround
- 99.9% accuracy

---

<!-- type: image -->

# Architecture

![System architecture diagram](images/architecture.png)

---

<!-- type: closing -->

# Thank You

## Questions?
```

### Slide Types

| Type | Directive | Description |
|------|-----------|-------------|
| Title | *(first slide, auto-detected)* | Presentation title and subtitle |
| Section | `<!-- type: section -->` | Section divider with large heading |
| Content | *(default)* | Standard slide with heading and bullets |
| Two-column | `<!-- type: two-column -->` | Side-by-side content with `<!-- left -->` / `<!-- right -->` markers |
| Image | `<!-- type: image -->` | Full-slide image with optional heading |
| Closing | `<!-- type: closing -->` | Closing slide (e.g., "Thank You") |

### Formatting

- `# H1` -- slide title
- `## H2` -- slide subtitle
- `- bullets` -- bullet points (nested supported)
- `> blockquote` -- speaker notes (not rendered on slide)
- `![alt](path)` -- image
- `::icon:name::` -- icon from the Red Hat icons repository

See [presentations-guide.md](references/presentations-guide.md) for the full
Markdown format specification, icon categories, and color palettes.

## Color Palettes

Seven built-in palettes are available -- four Red Hat brand palettes and
three general-purpose palettes. Use `palettes` to list them.

Set the palette in frontmatter (`palette: name`) or on the command line
(`--palette name`). The command-line flag overrides frontmatter.

## Examples

### Build and preview a deck

```bash
# Create .pptx from Markdown
$SKILL_DIR/scripts/google-slides.py create --file deck.md --output deck.pptx

# Preview as images (requires LibreOffice)
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx --format images

# Get a text summary instead
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx --format summary
```

### Build and upload in one step

```bash
$SKILL_DIR/scripts/google-slides.py create --file deck.md --title "Q2 Team Update"
# Builds .pptx, uploads to Google Drive, returns the presentation URL
```

### Round-trip workflow

```bash
# Download existing presentation as Markdown
$SKILL_DIR/scripts/google-slides.py get 1abc...xyz -o deck.md

# Edit deck.md in your editor...

# Rebuild
$SKILL_DIR/scripts/google-slides.py create --file deck.md --output deck.pptx

# Verify quality and accessibility
$SKILL_DIR/scripts/google-slides.py verify --file deck.pptx

# Replace slides in the original presentation
$SKILL_DIR/scripts/google-slides.py update 1abc...xyz --file deck.pptx --mode replace
```

### Verify against a cloud version

```bash
$SKILL_DIR/scripts/google-slides.py verify --file deck.pptx --presentation-id 1abc...xyz
```

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails
with an authentication error, insufficient scope error, or permission denied
error (exit code 1), **stop and inform the user**. Do not retry or attempt
to fix the issue autonomously -- these errors require user interaction
(browser-based OAuth consent). Point the user to the
[OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors
(HTTP 5xx) may succeed on retry after a brief wait. All other errors should
be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A
standard-capability model is recommended.

## Troubleshooting

### Cannot find presentation

Make sure you are using the correct presentation ID from the URL:
- URL: `https://docs.google.com/presentation/d/1abc...xyz/edit`
- Presentation ID: `1abc...xyz`

### LibreOffice not found

The `preview` command requires LibreOffice. Install it via your package
manager, or set `LIBREOFFICE_PATH` to the binary location. The skill checks
for `libreoffice`, `soffice`, and Flatpak installations automatically.

## Reference

- [Command reference](references/command-reference.md) -- full argument details
- [Permissions](references/permissions.md) -- read/write classification
- [Presentations guide](references/presentations-guide.md) -- Markdown format, palettes, icons
