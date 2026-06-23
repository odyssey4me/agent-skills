# Google Slides Command Reference

Full argument details and examples for all google-slides commands.

## create

Build a .pptx presentation from a Markdown file. Optionally upload to
Google Drive in the same step.

```bash
$SKILL_DIR/scripts/google-slides.py create --file deck.md
```

**Options:**
- `--file` - Path to the Markdown source file (required)
- `--output`, `-o` - Output .pptx path (default: same basename as input, e.g. `deck.pptx`)
- `--palette` - Color palette name (overrides frontmatter `palette` field)
- `--title` - If provided, also upload to Google Drive with this title; returns the presentation URL

**Examples:**

```bash
# Build with default palette
$SKILL_DIR/scripts/google-slides.py create --file deck.md

# Build with a specific palette and output path
$SKILL_DIR/scripts/google-slides.py create --file deck.md \
  --output /tmp/team-update.pptx --palette redhat-brand

# Build and upload in one step
$SKILL_DIR/scripts/google-slides.py create --file deck.md --title "Q2 Team Update"

# Output:
# Created: deck.pptx (12 slides)
# Palette: redhat-brand
# Uploaded: https://docs.google.com/presentation/d/1abc...xyz/edit
```

## get

Download a Google Slides presentation and output as Markdown. Uses layout
detection to score each slide against all 14 built-in templates, emitting
the best-matching `<!-- layout: name -->` directive for each slide. Prints
to stdout by default, or writes to a file with `-o`.

```bash
$SKILL_DIR/scripts/google-slides.py get PRESENTATION_ID
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--output`, `-o` - Write Markdown to this file instead of stdout

**Examples:**

```bash
# Print Markdown to stdout
$SKILL_DIR/scripts/google-slides.py get 1abc...xyz

# Save to a file
$SKILL_DIR/scripts/google-slides.py get 1abc...xyz -o deck.md

# Output (stdout):
# ---
# title: Q2 Team Update
# subtitle: June 2026
# ---
#
# # Q2 Team Update
#
# ## June 2026
#
# ---
#
# <!-- layout: content -->
#
# ## Key Metrics
#
# - Revenue: $1.2M
# - Active users: 50,000
```

## update

Upload a .pptx file to replace, append to, or insert into an existing
Google Slides presentation.

```bash
$SKILL_DIR/scripts/google-slides.py update PRESENTATION_ID --file deck.pptx
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--file` - Path to the .pptx file to upload (required)
- `--mode` - Upload mode (default: `replace`)
  - `replace` - Replace all slides in the presentation
  - `append` - Add slides after existing slides
  - `insert` - Insert slides at a specific position
- `--position` - Slide position for `insert` mode (0-based index)

**Examples:**

```bash
# Replace all slides
$SKILL_DIR/scripts/google-slides.py update 1abc...xyz --file deck.pptx

# Append new slides to the end
$SKILL_DIR/scripts/google-slides.py update 1abc...xyz --file deck.pptx --mode append

# Insert slides at position 3
$SKILL_DIR/scripts/google-slides.py update 1abc...xyz --file deck.pptx --mode insert --position 3

# Output:
# Updated: https://docs.google.com/presentation/d/1abc...xyz/edit
# Mode: replace
# Slides: 12
```

## preview

Preview a .pptx file locally. Requires LibreOffice for image output.

```bash
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx
```

**Options:**
- `--file` - Path to the .pptx file (required)
- `--format` - Output format (default: `images`)
  - `images` - Render each slide as a PNG image (requires LibreOffice)
  - `summary` - Print a text summary of each slide's content

**Examples:**

```bash
# Render slide images (writes to deck_slides/ directory)
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx --format images

# Output:
# Rendered 12 slides to deck_slides/
#   deck_slides/slide_01.png
#   deck_slides/slide_02.png
#   ...

# Text summary (no LibreOffice required)
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx --format summary

# Output:
# Slide 1 [title]: Q2 Team Update / June 2026
# Slide 2 [section]: Progress Review
# Slide 3 [content]: Key Metrics - 3 bullets
# Slide 4 [two-column]: Comparison - 3+3 bullets
# ...
```

## verify

Check a .pptx file for quality and accessibility issues. Optionally
compare against a cloud presentation.

```bash
$SKILL_DIR/scripts/google-slides.py verify --file deck.pptx
```

**Options:**
- `--file` - Path to the .pptx file (required)
- `--presentation-id` - Google Slides presentation ID for cloud comparison (optional)

**Examples:**

```bash
# Local verification only
$SKILL_DIR/scripts/google-slides.py verify --file deck.pptx

# Output:
# Verifying deck.pptx (12 slides)
# [PASS] All slides have titles
# [PASS] No empty slides
# [PASS] Images have alt text
# [PASS] Color contrast meets WCAG AA (4.5:1 body, 3:1 large text)
# [PASS] Image DPI >= 150
# [WARN] Slide 7: bullet count exceeds 6 (readability)
# [WARN] Slide 9: text may overflow placeholder (estimated 112% fill)
# Result: 5 passed, 2 warnings, 0 errors

# Compare local file against cloud version
$SKILL_DIR/scripts/google-slides.py verify --file deck.pptx --presentation-id 1abc...xyz

# Output:
# Verifying deck.pptx (12 slides)
# ...
# Cloud comparison (1abc...xyz):
#   Local: 12 slides, Cloud: 10 slides
#   Slides 1-10: content matches
#   Slides 11-12: new (not in cloud)
```

## palettes

List all available color palettes with their color slots.

```bash
$SKILL_DIR/scripts/google-slides.py palettes
```

**Example output:**

```
Available palettes:

  redhat-brand       Red Hat primary brand colors
  redhat-dark        Red Hat dark theme
  redhat-light       Red Hat light theme
  redhat-accessible  Red Hat accessible (high-contrast)
  corporate          Neutral corporate palette
  modern             Contemporary muted tones
  vibrant            Bold, high-saturation colors
```

## auth setup

Store OAuth 2.0 client credentials for authentication.

```bash
$SKILL_DIR/scripts/google-slides.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

**Options:**
- `--client-id` - OAuth 2.0 client ID (required)
- `--client-secret` - OAuth 2.0 client secret (required)

Credentials are saved to `~/.config/agent-skills/google-slides.yaml`.

## auth reset

Clear stored OAuth token. The next command that needs authentication will
trigger re-authentication automatically.

```bash
$SKILL_DIR/scripts/google-slides.py auth reset
```

Use this when you encounter scope or authentication errors.

## auth status

Show current OAuth token information without making API calls.

```bash
$SKILL_DIR/scripts/google-slides.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token
presence, token expiry, and client ID.

## check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/google-slides.py check
```

This validates:
- Python dependencies are installed (google-auth, python-pptx, cairosvg, etc.)
- Authentication is configured
- Can connect to Google APIs
- LibreOffice availability (optional, for preview)
