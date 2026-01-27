# Google Slides Layouts Guide

This guide covers available slide layouts and when to use them.

## Layout Overview

Google Slides provides predefined layouts that automatically position placeholder elements. When you create a slide with a layout, it sets up the structure for content.

## Available Layouts

### BLANK

Empty slide with no predefined elements.

**Use when:**
- Building custom layouts
- Creating diagrams or infographics
- Maximum control over element positioning

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout BLANK
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│         (Empty canvas)              │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### TITLE

Title slide layout with centered title and subtitle.

**Use when:**
- Creating presentation cover slide
- Section dividers
- Standalone title slides

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout TITLE

# Add title and subtitle
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Presentation Title" \
  --x 50 --y 150 --width 620 --height 100

python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Subtitle or Date" \
  --x 50 --y 280 --width 620 --height 60
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│      [TITLE PLACEHOLDER]            │
│    [SUBTITLE PLACEHOLDER]           │
│                                     │
└─────────────────────────────────────┘
```

### TITLE_AND_BODY

Standard content slide with title and body text area.

**Use when:**
- Presenting bulleted lists
- Standard content slides
- Text-heavy content

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout TITLE_AND_BODY

# Add title
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Key Points" \
  --x 50 --y 30 --width 620 --height 60

# Add body content
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "• First point\n• Second point\n• Third point" \
  --x 50 --y 120 --width 620 --height 350
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│  [TITLE PLACEHOLDER]                │
│                                     │
│  [BODY PLACEHOLDER]                 │
│  • Bullet point                     │
│  • Bullet point                     │
│  • Bullet point                     │
└─────────────────────────────────────┘
```

### TITLE_ONLY

Slide with only a title placeholder.

**Use when:**
- Adding images or charts
- Visual content with minimal text
- Custom content below title

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout TITLE_ONLY

# Add title
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Sales Chart" \
  --x 50 --y 30 --width 620 --height 60

# Add chart below
python scripts/google-slides.py images create $PRES_ID \
  --slide-id $SLIDE_ID \
  --image-url "https://example.com/chart.png" \
  --x 100 --y 120 --width 520 --height 380
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│  [TITLE PLACEHOLDER]                │
│                                     │
│                                     │
│       (Empty content area)          │
│                                     │
└─────────────────────────────────────┘
```

### SECTION_HEADER

Section divider with large centered title.

**Use when:**
- Marking new sections
- Transitioning between topics
- Chapter dividers in long presentations

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout SECTION_HEADER

python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Part 2: Analysis" \
  --x 50 --y 200 --width 620 --height 100
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│   [LARGE SECTION TITLE]             │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### SECTION_TITLE_AND_DESCRIPTION

Section divider with title and description.

**Use when:**
- Section intros with context
- Chapter summaries
- Multi-part transitions

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID \
  --layout SECTION_TITLE_AND_DESCRIPTION

python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Financial Overview" \
  --x 50 --y 150 --width 620 --height 80

python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Quarterly results and projections" \
  --x 50 --y 260 --width 620 --height 60
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│                                     │
│   [SECTION TITLE]                   │
│   [DESCRIPTION]                     │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### ONE_COLUMN_TEXT

Single column of text, optimized for reading.

**Use when:**
- Long-form text content
- Quotes or testimonials
- Detailed explanations

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout ONE_COLUMN_TEXT

python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Mission Statement" \
  --x 50 --y 30 --width 620 --height 50

python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Our mission is to empower teams..." \
  --x 100 --y 100 --width 520 --height 400
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│  [TITLE]                            │
│                                     │
│    [TEXT COLUMN]                    │
│    Lorem ipsum dolor sit amet,      │
│    consectetur adipiscing elit.     │
│    Sed do eiusmod tempor...         │
└─────────────────────────────────────┘
```

### MAIN_POINT

Large centered text for emphasis.

**Use when:**
- Highlighting key message
- Call to action slides
- Single important statement

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout MAIN_POINT

python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Revenue Up 45%" \
  --x 100 --y 200 --width 520 --height 150
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│      [LARGE CENTERED TEXT]          │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### BIG_NUMBER

Layout optimized for displaying a large number or metric.

**Use when:**
- Showing statistics
- Key performance indicators
- Metric highlights

**Example:**
```bash
python scripts/google-slides.py slides create $PRES_ID --layout BIG_NUMBER

# Big number
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "1,234" \
  --x 200 --y 150 --width 320 --height 150

# Label below
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "New Customers" \
  --x 200 --y 330 --width 320 --height 60
```

**Typical structure:**
```
┌─────────────────────────────────────┐
│                                     │
│          [BIG NUMBER]               │
│             1,234                   │
│          [Label Text]               │
│                                     │
└─────────────────────────────────────┘
```

## Layout Positioning Guide

When working with layouts, typical placeholder positions are:

**Title placeholders:**
- Position: (50, 30)
- Size: (620, 60-80)

**Body placeholders:**
- Position: (50, 100-120)
- Size: (620, 350-400)

**Centered content:**
- Position: (100-200, 150-250)
- Size: (320-520, 100-200)

## Layout Selection Strategy

### For presentations focused on:

**Text and bullets → TITLE_AND_BODY**
- Standard corporate presentations
- Meeting notes
- Educational content

**Visuals and images → TITLE_ONLY or BLANK**
- Photo presentations
- Design portfolios
- Chart-heavy decks

**Impact and emphasis → MAIN_POINT or BIG_NUMBER**
- Sales pitches
- Metric dashboards
- Key message slides

**Organization → SECTION_HEADER**
- Long presentations
- Training materials
- Multi-topic decks

## Custom Layouts

If predefined layouts don't fit your needs, use `BLANK` and manually position elements:

```bash
# Create blank slide
python scripts/google-slides.py slides create $PRES_ID --layout BLANK

# Custom header
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Custom Header" \
  --x 30 --y 20 --width 660 --height 40

# Left column
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Left content..." \
  --x 30 --y 80 --width 300 --height 430

# Right column
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID \
  --text "Right content..." \
  --x 360 --y 80 --width 330 --height 430
```

## Layout Modification

You can insert elements on any layout - the layout just provides initial placeholders:

```bash
# Start with TITLE_AND_BODY
python scripts/google-slides.py slides create $PRES_ID --layout TITLE_AND_BODY

# Add title
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID --text "Overview" \
  --x 50 --y 30 --width 620 --height 60

# Add custom shape (not part of layout)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID --shape-type STAR_5 \
  --x 600 --y 30 --width 60 --height 60

# Add body text
python scripts/google-slides.py text insert $PRES_ID \
  --slide-id $SLIDE_ID --text "Content..." \
  --x 50 --y 120 --width 620 --height 350
```

## Best Practices

1. **Use consistent layouts** - Stick to 2-3 layout types per presentation for visual consistency

2. **Match layout to content** - Don't force text-heavy content into MAIN_POINT layout

3. **BLANK for complex slides** - When mixing many element types, BLANK gives most control

4. **Section headers for structure** - Use SECTION_HEADER every 5-10 slides to mark transitions

5. **Test visibility** - Ensure text is readable and elements don't overlap

## Troubleshooting Layouts

### Text doesn't fit in placeholder

Increase the height or use a different layout:

```bash
# Instead of default height (60)
--height 100
```

### Elements overlap

Check positions and sizes:
- Standard slide is 720 x 540 points
- Leave margins (at least 30-50 points from edges)
- Space elements 20+ points apart

### Layout looks different than expected

Layouts provide structure but don't auto-populate content. You must explicitly insert text/images into the placeholder areas.

## API Reference

For complete layout details:
- [Google Slides API - Layouts](https://developers.google.com/slides/api/reference/rest/v1/presentations.pages#Layout)
- [Predefined layouts](https://developers.google.com/slides/api/reference/rest/v1/presentations.pages#PredefinedLayout)
