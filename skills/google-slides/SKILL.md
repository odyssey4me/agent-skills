---
name: google-slides
description: Create and edit Google Slides presentations. Add or delete slides, insert text, shapes, and images. Use when asked to build a deck, create a slideshow, update a Google presentation, or edit slides.
metadata:
  author: odyssey4me
  version: "0.1.2"
  category: google-workspace
  tags: "presentations, slides"
  complexity: standard
license: MIT
allowed-tools: Bash($SKILL_DIR/scripts/google-slides.py:*)
---

# Google Slides

Interact with Google Slides for presentation creation, slide management, and content insertion.

## Installation

**Dependencies**: `pip install --user google-auth google-auth-oauthlib google-api-python-client keyring pyyaml`

## Setup Verification

After installation, verify the skill is properly configured:

```bash
$SKILL_DIR/scripts/google-slides.py check
```

This will check:
- Python dependencies (google-auth, google-auth-oauthlib, google-api-python-client, keyring, pyyaml)
- Authentication configuration
- Connectivity to Google Slides API

If anything is missing, the check command will provide setup instructions.

## Authentication

Google Slides uses OAuth 2.0 for authentication. For complete setup instructions, see:

1. [GCP Project Setup Guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/gcp-project-setup.md) - Create project, enable Slides API
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

```bash
# Setup and auth
$SKILL_DIR/scripts/google-slides.py check
$SKILL_DIR/scripts/google-slides.py auth setup --client-id ID --client-secret SECRET
$SKILL_DIR/scripts/google-slides.py auth reset
$SKILL_DIR/scripts/google-slides.py auth status

# Presentations
$SKILL_DIR/scripts/google-slides.py presentations create --title "Title"
$SKILL_DIR/scripts/google-slides.py presentations get PRESENTATION_ID
$SKILL_DIR/scripts/google-slides.py presentations read PRESENTATION_ID [--format text|pdf] [--output PATH]

# Slides — use presentations get to find slide IDs
$SKILL_DIR/scripts/google-slides.py slides create PRESENTATION_ID --layout LAYOUT [--index N]
$SKILL_DIR/scripts/google-slides.py slides delete PRESENTATION_ID --slide-id SLIDE_ID

# Content — coordinates are in points; origin (0,0) is top-left
$SKILL_DIR/scripts/google-slides.py text insert PRESENTATION_ID --slide-id ID --text "..." [--x N --y N --width N --height N]
$SKILL_DIR/scripts/google-slides.py shapes create PRESENTATION_ID --slide-id ID --shape-type TYPE [--x N --y N --width N --height N]
$SKILL_DIR/scripts/google-slides.py images create PRESENTATION_ID --slide-id ID --image-url URL [--x N --y N --width N --height N]
```

See [command-reference.md](references/command-reference.md) for full argument details and examples.

## Examples

### Create a simple presentation

```bash
# Create presentation
$SKILL_DIR/scripts/google-slides.py presentations create --title "Team Update"

# Verify creation and get the default slide ID
$SKILL_DIR/scripts/google-slides.py presentations get $PRES_ID

# Add title text
$SKILL_DIR/scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Q4 Team Update" \
  --x 50 --y 50 --width 600 --height 100

# Add subtitle
$SKILL_DIR/scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "December 2024" \
  --x 50 --y 180 --width 600 --height 50

# Verify content was inserted correctly
$SKILL_DIR/scripts/google-slides.py presentations read $PRES_ID
```

### Build a multi-slide presentation

```bash
#!/bin/bash
PRES_ID="your-presentation-id"

# Add content slide
$SKILL_DIR/scripts/google-slides.py slides create $PRES_ID --layout TITLE_AND_BODY

# Verify slide was added and get its ID
$SKILL_DIR/scripts/google-slides.py presentations get $PRES_ID

# Add title
$SKILL_DIR/scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Key Metrics" \
  --x 50 --y 30 --width 600 --height 60

# Add chart image
$SKILL_DIR/scripts/google-slides.py images create $PRES_ID \
  --slide-id $SLIDE_ID \
  --image-url "https://example.com/metrics.png" \
  --x 100 --y 120 --width 500 --height 350

# Add another slide with shapes
$SKILL_DIR/scripts/google-slides.py slides create $PRES_ID --layout BLANK

# Verify and get the new slide ID
$SKILL_DIR/scripts/google-slides.py presentations get $PRES_ID

# Add decorative shape
$SKILL_DIR/scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE2_ID \
  --shape-type STAR_5 \
  --x 550 --y 30 --width 80 --height 80

# Verify final presentation content
$SKILL_DIR/scripts/google-slides.py presentations read $PRES_ID
```

### Create presentation from data

```bash
#!/bin/bash

# Create presentation
$SKILL_DIR/scripts/google-slides.py presentations create --title "Sales Report"

# Verify creation
$SKILL_DIR/scripts/google-slides.py presentations get $PRES_ID

# Add a slide for each region
$SKILL_DIR/scripts/google-slides.py slides create $PRES_ID --layout TITLE_AND_BODY

# Verify slide was added and get its ID
$SKILL_DIR/scripts/google-slides.py presentations get $PRES_ID

# Insert text on each slide using the slide ID from the output above
$SKILL_DIR/scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "North Region Sales" \
  --x 50 --y 30 --width 600 --height 80

# Verify content
$SKILL_DIR/scripts/google-slides.py presentations read $PRES_ID
```

## Coordinate System

Google Slides uses **points** for positioning and sizing:
- 1 point = 1/72 inch
- 1 inch = 72 points
- Origin (0, 0) is at the top-left corner
- Standard slide size: 720 x 540 points (10 x 7.5 inches)

**Common reference positions:**

```
(0, 0)                                    (720, 0)
  ┌───────────────────────────────────────┐
  │  Title area                           │
  │  (50, 50, 620, 80)                    │
  │                                       │
  │  Content area                         │
  │  (50, 150, 620, 350)                  │
  │                                       │
  │                                       │
  └───────────────────────────────────────┘
(0, 540)                                (720, 540)
```

## Error Handling

**Authentication and scope errors are not retryable.** If a command fails with an authentication error, insufficient scope error, or permission denied error (exit code 1), **stop and inform the user**. Do not retry or attempt to fix the issue autonomously — these errors require user interaction (browser-based OAuth consent). Point the user to the [OAuth troubleshooting guide](https://github.com/odyssey4me/agent-skills/blob/main/docs/google-oauth-setup.md#troubleshooting).

**Retryable errors**: Rate limiting (HTTP 429) and temporary server errors (HTTP 5xx) may succeed on retry after a brief wait. All other errors should be reported to the user.

## Model Guidance

This skill makes API calls requiring structured input/output. A standard-capability model is recommended.

## Troubleshooting

### Cannot find presentation

Make sure you're using the correct presentation ID from the URL:
- URL: `https://docs.google.com/presentation/d/1abc...xyz/edit`
- Presentation ID: `1abc...xyz`

### Image not appearing

The image URL must be:
- Publicly accessible (no authentication required), OR
- Accessible to the Google account you're using

Test the URL in a browser. If it requires authentication, you'll need to:
1. Upload the image to Google Drive
2. Make it publicly accessible or share it with your Google account
3. Use the Google Drive URL

## API Reference

For advanced usage, see:
- [Google Slides API Documentation](https://developers.google.com/slides/api)
- [Working with presentations](https://developers.google.com/slides/api/guides/presentations)
- [Layouts guide](references/layouts-guide.md)
- [Shapes guide](references/shapes-guide.md)
