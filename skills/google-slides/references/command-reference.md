# Google Slides Command Reference

Full argument details and examples for all google-slides commands.

## check

Verify configuration and connectivity.

```bash
$SKILL_DIR/scripts/google-slides.py check
```

This validates:
- Python dependencies are installed
- Authentication is configured
- Can connect to Google Slides API
- Creates a test presentation to verify write access

## auth setup

Store OAuth 2.0 client credentials for custom OAuth flow.

```bash
$SKILL_DIR/scripts/google-slides.py auth setup \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

Credentials are saved to `~/.config/agent-skills/google-slides.yaml`.

**Options:**
- `--client-id` - OAuth 2.0 client ID (required)
- `--client-secret` - OAuth 2.0 client secret (required)

## auth reset

Clear stored OAuth token. The next command that needs authentication will trigger re-authentication automatically.

```bash
$SKILL_DIR/scripts/google-slides.py auth reset
```

Use this when you encounter scope or authentication errors.

## auth status

Show current OAuth token information without making API calls.

```bash
$SKILL_DIR/scripts/google-slides.py auth status
```

Displays: whether a token is stored, granted scopes, refresh token presence, token expiry, and client ID.

## presentations create

Create a new Google Slides presentation.

```bash
$SKILL_DIR/scripts/google-slides.py presentations create --title "My Presentation"
```

**Options:**
- `--title` - Presentation title (required)

**Example:**
```bash
$SKILL_DIR/scripts/google-slides.py presentations create --title "Q4 Review"

# Output:
# ✓ Presentation created successfully
# Title: Q4 Review
# Presentation ID: 1abc...xyz
# Slides: 1
# URL: https://docs.google.com/presentation/d/1abc...xyz/edit
```

## presentations get

Get presentation metadata and structure.

```bash
$SKILL_DIR/scripts/google-slides.py presentations get PRESENTATION_ID
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Example:**
```bash
$SKILL_DIR/scripts/google-slides.py presentations get 1abc...xyz

# Output:
# Title: Q4 Review
# Presentation ID: 1abc...xyz
# Slides: 5
# URL: https://docs.google.com/presentation/d/1abc...xyz/edit
#
# Slides:
# Slide 1:
#   ID: slide_id_1
#   Layout: TITLE
#   Elements: 2 (2 text, 0 shapes, 0 images, 0 other)
# Slide 2:
#   ID: slide_id_2
#   Layout: TITLE_AND_BODY
#   Elements: 3 (2 text, 1 shapes, 0 images, 0 other)
```

## presentations read

Read presentation text content from all slides, or export as PDF.

```bash
$SKILL_DIR/scripts/google-slides.py presentations read PRESENTATION_ID
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--format` - Output format: `text` (default) or `pdf`
- `--output`, `-o` - Output file path (used with pdf format)

**Example:**
```bash
# Read as text (default)
$SKILL_DIR/scripts/google-slides.py presentations read 1abc...xyz

# Export as PDF
$SKILL_DIR/scripts/google-slides.py presentations read 1abc...xyz --format pdf --output presentation.pdf

# Output (text format):
# --- Slide 1 ---
# Welcome to Our Product
# An introduction to key features
#
# --- Slide 2 ---
# Key Metrics
# Revenue: $1.2M
# Users: 50,000
#
# --- Slide 3 ---
# | Quarter | Revenue | Growth |
# | --- | --- | --- |
# | Q1 | $250K | 10% |
# | Q2 | $300K | 20% |
```

**Note:** Text format extracts text from all shapes, text boxes, and tables on each slide (tables formatted as markdown). PDF export uses Google's native Drive API export, which requires the `drive.readonly` scope.

## slides create

Add a new slide to a presentation.

```bash
$SKILL_DIR/scripts/google-slides.py slides create PRESENTATION_ID --layout BLANK
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--layout` - Slide layout (default: BLANK)
  - `BLANK` - Empty slide
  - `TITLE` - Title slide
  - `TITLE_AND_BODY` - Title and body text
  - `TITLE_ONLY` - Title only
  - `SECTION_HEADER` - Section header
  - `SECTION_TITLE_AND_DESCRIPTION` - Section with description
  - `ONE_COLUMN_TEXT` - Single column of text
  - `MAIN_POINT` - Large centered text
  - `BIG_NUMBER` - Large number display
- `--index` - Insert at specific position (0-based, optional)

**Example:**
```bash
# Add blank slide at the end
$SKILL_DIR/scripts/google-slides.py slides create 1abc...xyz --layout BLANK

# Add title slide at position 0
$SKILL_DIR/scripts/google-slides.py slides create 1abc...xyz --layout TITLE --index 0

# Output:
# ✓ Slide created successfully
#   Slide ID: slide_abc123
#   Layout: TITLE
```

See [layouts-guide.md](layouts-guide.md) for layout details.

## slides delete

Delete a slide from a presentation.

```bash
$SKILL_DIR/scripts/google-slides.py slides delete PRESENTATION_ID --slide-id SLIDE_ID
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--slide-id` - Slide object ID to delete (required)

**Example:**
```bash
# Get slide IDs first
$SKILL_DIR/scripts/google-slides.py presentations get 1abc...xyz

# Delete a slide
$SKILL_DIR/scripts/google-slides.py slides delete 1abc...xyz --slide-id slide_abc123

# Output:
# ✓ Slide deleted successfully
```

**Warning:** Cannot delete the last remaining slide in a presentation.

## text insert

Insert text into a slide.

```bash
$SKILL_DIR/scripts/google-slides.py text insert PRESENTATION_ID \
  --slide-id SLIDE_ID \
  --text "Hello World"
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--slide-id` - Slide object ID (required)
- `--text` - Text to insert (required)
- `--x` - X position in points (default: 100)
- `--y` - Y position in points (default: 100)
- `--width` - Text box width in points (default: 400)
- `--height` - Text box height in points (default: 100)

**Example:**
```bash
# Insert text at default position
$SKILL_DIR/scripts/google-slides.py text insert 1abc...xyz \
  --slide-id slide_abc123 \
  --text "Hello World"

# Insert text at custom position
$SKILL_DIR/scripts/google-slides.py text insert 1abc...xyz \
  --slide-id slide_abc123 \
  --text "Q4 Results" \
  --x 50 --y 50 --width 500 --height 80

# Output:
# ✓ Text inserted successfully
#   Text: Q4 Results
#   Position: (50.0, 50.0) points
#   Size: 500.0 x 80.0 points
```

## shapes create

Create a shape on a slide.

```bash
$SKILL_DIR/scripts/google-slides.py shapes create PRESENTATION_ID \
  --slide-id SLIDE_ID \
  --shape-type RECTANGLE
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--slide-id` - Slide object ID (required)
- `--shape-type` - Shape type (required)
  - `RECTANGLE`, `ELLIPSE`, `TRIANGLE`, `PENTAGON`, `HEXAGON`
  - `STAR_5`, `STAR_8`, `STAR_24`, `STAR_32`
  - `CLOUD`, `HEART`, `LIGHTNING_BOLT`, `MOON`, `SUN`
  - `ARROW_NORTH`, `ARROW_EAST`, `ARROW_SOUTH`, `ARROW_WEST`
  - And many more (see [shapes-guide.md](shapes-guide.md))
- `--x` - X position in points (default: 100)
- `--y` - Y position in points (default: 100)
- `--width` - Shape width in points (default: 200)
- `--height` - Shape height in points (default: 200)

**Example:**
```bash
# Create rectangle
$SKILL_DIR/scripts/google-slides.py shapes create 1abc...xyz \
  --slide-id slide_abc123 \
  --shape-type RECTANGLE

# Create star with custom size
$SKILL_DIR/scripts/google-slides.py shapes create 1abc...xyz \
  --slide-id slide_abc123 \
  --shape-type STAR_5 \
  --x 300 --y 200 --width 150 --height 150

# Output:
# ✓ Shape created successfully
#   Type: STAR_5
#   Position: (300.0, 200.0) points
#   Size: 150.0 x 150.0 points
```

See [shapes-guide.md](shapes-guide.md) for all shape types.

## images create

Insert an image into a slide.

```bash
$SKILL_DIR/scripts/google-slides.py images create PRESENTATION_ID \
  --slide-id SLIDE_ID \
  --image-url "https://example.com/image.png"
```

**Arguments:**
- `presentation_id` - The Google Slides presentation ID

**Options:**
- `--slide-id` - Slide object ID (required)
- `--image-url` - Image URL (required, must be publicly accessible)
- `--x` - X position in points (default: 100)
- `--y` - Y position in points (default: 100)
- `--width` - Image width in points (default: 300)
- `--height` - Image height in points (default: 200)

**Example:**
```bash
$SKILL_DIR/scripts/google-slides.py images create 1abc...xyz \
  --slide-id slide_abc123 \
  --image-url "https://example.com/chart.png" \
  --x 50 --y 150 --width 400 --height 300

# Output:
# ✓ Image created successfully
#   URL: https://example.com/chart.png
#   Position: (50.0, 150.0) points
#   Size: 400.0 x 300.0 points
```

**Note:** The image URL must be publicly accessible or authenticated with Google.
