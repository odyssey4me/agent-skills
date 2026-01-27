# Google Slides Shapes Guide

This guide covers available shape types and how to use them effectively.

## Shape Overview

Google Slides provides a wide variety of predefined shapes that can be inserted into slides. Shapes can be used for:
- Visual emphasis
- Diagrams and flowcharts
- Decorative elements
- Call-outs and annotations

## Basic Shapes

### Rectangles and Squares

```bash
# Rectangle
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RECTANGLE \
  --x 100 --y 100 --width 300 --height 150

# Square (equal width and height)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RECTANGLE \
  --x 100 --y 100 --width 200 --height 200

# Rounded rectangle
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ROUND_RECTANGLE \
  --x 100 --y 100 --width 300 --height 150
```

**Use cases:**
- Background boxes for text
- Container elements
- Buttons
- Highlighting areas

### Circles and Ellipses

```bash
# Circle (equal width and height)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ELLIPSE \
  --x 100 --y 100 --width 200 --height 200

# Ellipse
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ELLIPSE \
  --x 100 --y 100 --width 300 --height 150
```

**Use cases:**
- Circular badges
- Venn diagrams
- Focal points
- Profile picture frames

### Triangles

```bash
# Triangle
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type TRIANGLE \
  --x 100 --y 100 --width 200 --height 200

# Right triangle
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RIGHT_TRIANGLE \
  --x 100 --y 100 --width 200 --height 200
```

**Use cases:**
- Directional indicators
- Geometric patterns
- Chart elements

## Polygon Shapes

### Regular Polygons

```bash
# Pentagon (5 sides)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type PENTAGON \
  --x 100 --y 100 --width 200 --height 200

# Hexagon (6 sides)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type HEXAGON \
  --x 100 --y 100 --width 200 --height 200

# Octagon (8 sides)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type OCTAGON \
  --x 100 --y 100 --width 200 --height 200
```

**Use cases:**
- Process diagrams
- Geometric infographics
- Decorative elements

## Star Shapes

Google Slides offers multiple star variations:

```bash
# 5-point star
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type STAR_5 \
  --x 100 --y 100 --width 200 --height 200

# 8-point star
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type STAR_8 \
  --x 100 --y 100 --width 200 --height 200

# 24-point star (sunburst)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type STAR_24 \
  --x 100 --y 100 --width 200 --height 200

# 32-point star
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type STAR_32 \
  --x 100 --y 100 --width 200 --height 200
```

**Available star types:**
- `STAR_4`
- `STAR_5`
- `STAR_6`
- `STAR_7`
- `STAR_8`
- `STAR_10`
- `STAR_12`
- `STAR_16`
- `STAR_24`
- `STAR_32`

**Use cases:**
- Awards and achievements
- Highlights and callouts
- Rating systems
- Decorative accents

## Arrow Shapes

### Directional Arrows

```bash
# Arrow pointing north
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ARROW_NORTH \
  --x 100 --y 100 --width 100 --height 150

# Arrow pointing east
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ARROW_EAST \
  --x 100 --y 100 --width 150 --height 100

# Arrow pointing south
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ARROW_SOUTH \
  --x 100 --y 100 --width 100 --height 150

# Arrow pointing west
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ARROW_WEST \
  --x 100 --y 100 --width 150 --height 100
```

### Specialized Arrows

```bash
# Left-right arrow
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type LEFT_RIGHT_ARROW \
  --x 100 --y 100 --width 200 --height 80

# Up-down arrow
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type UP_DOWN_ARROW \
  --x 100 --y 100 --width 80 --height 200

# Notched right arrow
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type NOTCHED_RIGHT_ARROW \
  --x 100 --y 100 --width 200 --height 100

# Bent arrow
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type BENT_ARROW \
  --x 100 --y 100 --width 200 --height 200

# U-turn arrow
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type UTURN_ARROW \
  --x 100 --y 100 --width 150 --height 200
```

**Use cases:**
- Process flows
- Directional indicators
- Cause and effect diagrams
- Navigation elements

## Callout and Banner Shapes

### Callouts

```bash
# Rectangular callout
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RECTANGULAR_CALLOUT \
  --x 100 --y 100 --width 200 --height 100

# Rounded rectangular callout
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type ROUNDED_RECTANGULAR_CALLOUT \
  --x 100 --y 100 --width 200 --height 100

# Oval callout
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type OVAL_CALLOUT \
  --x 100 --y 100 --width 200 --height 100

# Cloud callout
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type CLOUD_CALLOUT \
  --x 100 --y 100 --width 200 --height 100
```

**Use cases:**
- Annotations
- Comments and notes
- Speech bubbles
- Emphasis on specific points

### Ribbons and Banners

```bash
# Wave (ribbon-like)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type WAVE \
  --x 100 --y 100 --width 300 --height 80

# Double wave
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type DOUBLE_WAVE \
  --x 100 --y 100 --width 300 --height 80

# Ribbon
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RIBBON \
  --x 100 --y 100 --width 200 --height 100

# Ribbon 2
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RIBBON_2 \
  --x 100 --y 100 --width 200 --height 100
```

**Use cases:**
- Headers and titles
- Award badges
- Decorative accents
- Section markers

## Flowchart Shapes

### Process Shapes

```bash
# Flowchart: Process
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_PROCESS \
  --x 100 --y 100 --width 200 --height 100

# Flowchart: Decision (diamond)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_DECISION \
  --x 100 --y 100 --width 200 --height 200

# Flowchart: Terminator (start/end)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_TERMINATOR \
  --x 100 --y 100 --width 200 --height 100

# Flowchart: Document
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_DOCUMENT \
  --x 100 --y 100 --width 200 --height 150

# Flowchart: Data
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_DATA \
  --x 100 --y 100 --width 200 --height 150
```

### Specialized Flowchart Shapes

```bash
# Flowchart: Input/Output
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_INPUT_OUTPUT \
  --x 100 --y 100 --width 200 --height 100

# Flowchart: Manual operation
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_MANUAL_OPERATION \
  --x 100 --y 100 --width 200 --height 100

# Flowchart: Preparation
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_PREPARATION \
  --x 100 --y 100 --width 200 --height 100

# Flowchart: Connector
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type FLOWCHART_CONNECTOR \
  --x 100 --y 100 --width 100 --height 100
```

**Use cases:**
- Process diagrams
- Workflow documentation
- Decision trees
- System architecture

## Decorative Shapes

### Nature and Symbols

```bash
# Cloud
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type CLOUD \
  --x 100 --y 100 --width 250 --height 150

# Heart
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type HEART \
  --x 100 --y 100 --width 200 --height 200

# Lightning bolt
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type LIGHTNING_BOLT \
  --x 100 --y 100 --width 120 --height 200

# Moon
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type MOON \
  --x 100 --y 100 --width 200 --height 200

# Sun
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type SUN \
  --x 100 --y 100 --width 200 --height 200
```

**Use cases:**
- Thematic presentations
- Weather diagrams
- Conceptual illustrations
- Icons and symbols

### Special Symbols

```bash
# Smiley face
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type SMILEY_FACE \
  --x 100 --y 100 --width 200 --height 200

# No symbol (prohibition)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type NO_SMOKING_SIGN \
  --x 100 --y 100 --width 200 --height 200

# Plus sign
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type PLUS \
  --x 100 --y 100 --width 150 --height 150
```

**Use cases:**
- Emotional indicators
- Warning signs
- Mathematical operators
- User feedback

## Mathematical and Equation Shapes

```bash
# Plus
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type PLUS \
  --x 100 --y 100 --width 100 --height 100

# Minus (horizontal line)
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type MINUS \
  --x 100 --y 100 --width 100 --height 50

# Multiply
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type MULTIPLY \
  --x 100 --y 100 --width 100 --height 100

# Divide
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type DIVIDE \
  --x 100 --y 100 --width 100 --height 100
```

**Use cases:**
- Mathematical presentations
- Equation slides
- Statistical diagrams

## Bracket and Brace Shapes

```bash
# Left bracket
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type LEFT_BRACKET \
  --x 100 --y 100 --width 50 --height 200

# Right bracket
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RIGHT_BRACKET \
  --x 100 --y 100 --width 50 --height 200

# Left brace
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type LEFT_BRACE \
  --x 100 --y 100 --width 80 --height 200

# Right brace
python scripts/google-slides.py shapes create $PRES_ID \
  --slide-id $SLIDE_ID \
  --shape-type RIGHT_BRACE \
  --x 100 --y 100 --width 80 --height 200
```

**Use cases:**
- Grouping related items
- Mathematical notation
- Code presentations
- Organizational charts

## Shape Sizing Guidelines

### Aspect Ratios

Different shapes work best with specific aspect ratios:

**Square shapes (1:1):**
- ELLIPSE (circle)
- HEXAGON
- OCTAGON
- STAR_5
- HEART

**Wide shapes (2:1 or 3:1):**
- RECTANGLE (banner)
- ARROW_EAST/WEST
- RIBBON
- WAVE

**Tall shapes (1:2 or 1:3):**
- ARROW_NORTH/SOUTH
- LIGHTNING_BOLT

**Custom ratios:**
- Adjust width and height to fit content
- Maintain consistent proportions for similar shapes

### Standard Sizes

```bash
# Icon size (small decorative)
--width 60 --height 60

# Small shape (accent)
--width 100 --height 100

# Medium shape (standard)
--width 200 --height 200

# Large shape (focal point)
--width 400 --height 400

# Banner (horizontal)
--width 600 --height 80

# Sidebar (vertical)
--width 100 --height 500
```

## Positioning Patterns

### Grid Layout

```bash
# Create 3x3 grid of shapes
for row in 0 1 2; do
  for col in 0 1 2; do
    x=$((100 + col * 200))
    y=$((100 + row * 150))

    python scripts/google-slides.py shapes create $PRES_ID \
      --slide-id $SLIDE_ID \
      --shape-type ELLIPSE \
      --x $x --y $y --width 150 --height 100
  done
done
```

### Diagonal Pattern

```bash
# Create diagonal line of shapes
for i in 0 1 2 3 4; do
  pos=$((50 + i * 120))

  python scripts/google-slides.py shapes create $PRES_ID \
    --slide-id $SLIDE_ID \
    --shape-type STAR_5 \
    --x $pos --y $pos --width 80 --height 80
done
```

### Circular Arrangement

Mathematical approach for circular layouts (pseudo-code):

```bash
# Place shapes in circle
radius=200
center_x=360
center_y=270
num_shapes=6

for i in $(seq 0 $((num_shapes - 1))); do
  angle=$(echo "scale=4; $i * 2 * 3.14159 / $num_shapes" | bc)
  x=$(echo "scale=0; $center_x + $radius * c($angle)" | bc -l)
  y=$(echo "scale=0; $center_y + $radius * s($angle)" | bc -l)

  python scripts/google-slides.py shapes create $PRES_ID \
    --slide-id $SLIDE_ID \
    --shape-type PENTAGON \
    --x $x --y $y --width 100 --height 100
done
```

## Complete Shape List

**Basic:**
- RECTANGLE
- ROUND_RECTANGLE
- ELLIPSE
- TRIANGLE
- RIGHT_TRIANGLE

**Polygons:**
- PENTAGON
- HEXAGON
- HEPTAGON
- OCTAGON
- DECAGON
- DODECAGON

**Stars:**
- STAR_4, STAR_5, STAR_6, STAR_7, STAR_8
- STAR_10, STAR_12, STAR_16, STAR_24, STAR_32

**Arrows:**
- ARROW_NORTH, ARROW_SOUTH, ARROW_EAST, ARROW_WEST
- LEFT_RIGHT_ARROW, UP_DOWN_ARROW
- NOTCHED_RIGHT_ARROW
- BENT_ARROW, UTURN_ARROW
- BENT_UP_ARROW, CURVED_DOWN_ARROW, CURVED_UP_ARROW
- STRIPED_RIGHT_ARROW, QUAD_ARROW

**Callouts:**
- RECTANGULAR_CALLOUT
- ROUNDED_RECTANGULAR_CALLOUT
- OVAL_CALLOUT
- CLOUD_CALLOUT
- WEDGE_RECTANGULAR_CALLOUT
- WEDGE_ROUNDED_RECTANGULAR_CALLOUT
- WEDGE_OVAL_CALLOUT

**Ribbons:**
- WAVE, DOUBLE_WAVE
- RIBBON, RIBBON_2
- VERTICAL_SCROLL, HORIZONTAL_SCROLL

**Flowchart:**
- FLOWCHART_PROCESS
- FLOWCHART_DECISION
- FLOWCHART_TERMINATOR
- FLOWCHART_DOCUMENT
- FLOWCHART_DATA
- FLOWCHART_INPUT_OUTPUT
- FLOWCHART_MANUAL_OPERATION
- FLOWCHART_PREPARATION
- FLOWCHART_CONNECTOR
- FLOWCHART_PUNCHED_CARD
- FLOWCHART_PUNCHED_TAPE
- FLOWCHART_SUMMING_JUNCTION
- FLOWCHART_OR
- FLOWCHART_COLLATE
- FLOWCHART_SORT
- FLOWCHART_EXTRACT
- FLOWCHART_MERGE
- FLOWCHART_STORED_DATA
- FLOWCHART_DELAY
- FLOWCHART_ALTERNATE_PROCESS
- FLOWCHART_OFF_PAGE_CONNECTOR

**Decorative:**
- CLOUD
- HEART
- LIGHTNING_BOLT
- MOON, SUN
- SMILEY_FACE
- NO_SMOKING_SIGN (prohibition circle)

**Math:**
- PLUS, MINUS, MULTIPLY, DIVIDE

**Brackets:**
- LEFT_BRACKET, RIGHT_BRACKET
- LEFT_BRACE, RIGHT_BRACE

**Misc:**
- ARC
- CHORD
- CROSS
- DIAGONAL_STRIPE
- FRAME, HALF_FRAME, CORNER
- TRAPEZOID, PARALLELOGRAM
- PLAQUE
- BLOCK_ARC

## Best Practices

1. **Match shape to purpose** - Use flowchart shapes for processes, stars for highlights

2. **Consistent sizing** - Use similar sizes for related shapes

3. **Spacing** - Leave 20-30 points between shapes for clarity

4. **Color and fill** - Shapes can be colored (requires additional API calls for formatting)

5. **Layering** - Shapes are added in order; later shapes appear on top

6. **Visibility** - Ensure shapes fit within slide boundaries (0-720 x 0-540)

## Troubleshooting

### Shape appears cut off

Check that shape fits within slide:
- Max X: `x + width <= 720`
- Max Y: `y + height <= 540`

### Shape looks distorted

Some shapes have optimal aspect ratios:
- Stars: use square dimensions (width = height)
- Arrows: use 2:1 or 3:1 ratio in arrow direction
- Circles: use square dimensions for ELLIPSE

### Cannot see shape

Verify:
- Coordinates are positive
- Shape size is reasonable (at least 10x10 points)
- Shape isn't hidden behind other elements

## API Reference

For complete shape details:
- [Google Slides API - Shapes](https://developers.google.com/slides/api/reference/rest/v1/presentations.pages#Shape)
- [Shape types](https://developers.google.com/slides/api/reference/rest/v1/presentations.pages#ShapeType)
