# Presentations Guide

This guide covers the Markdown format for writing presentations, available
layout templates, color palettes, icon syntax, and the round-trip workflow.

## Markdown Format

A presentation is a Markdown file with YAML frontmatter at the top and
slides separated by `---` on its own line.

### Frontmatter

The YAML frontmatter block sets presentation-level metadata:

```yaml
---
title: Presentation Title
subtitle: Optional Subtitle
author: Author Name
date: 2026-06-23
palette: redhat-brand
---
```

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Presentation title (used on the title slide) |
| `subtitle` | No | Subtitle shown below the title |
| `author` | No | Author name |
| `date` | No | Presentation date |
| `palette` | No | Color palette name (default: `corporate`) |
| `custom_layouts` | No | Custom layout definitions (see Custom Layouts below) |

The `palette` field can be overridden on the command line with `--palette`.

### Slide Separators

Slides are separated by `---` on its own line (with blank lines around it
for readability):

```markdown
## Slide One

- Content here

---

## Slide Two

- More content
```

### Layout Directives

Set the slide layout with an HTML comment at the start of a slide:

```markdown
---

<!-- layout: section -->

# Section Title
```

If no directive is present, the slide defaults to `content` layout (except
the first slide, which is auto-detected as `title`).

The older `<!-- type: name -->` syntax is still accepted for backward
compatibility but `<!-- layout: name -->` is preferred.

### Content Elements

**Headings:**
- `# H1` -- slide title (large)
- `## H2` -- slide subtitle or secondary heading
- `### H3` -- sub-heading within content

**Bullet points:**

```markdown
- First point
- Second point
  - Nested point
  - Another nested point
- Third point
```

**Speaker notes:** Use blockquotes. These are extracted as speaker notes
and are not rendered on the slide itself.

```markdown
> This appears only in speaker notes, not on the slide.
> Multiple lines are joined together.
```

**Images:**

```markdown
![Alt text for accessibility](path/to/image.png)
```

Paths can be relative to the Markdown file or absolute.

**Icons:**

```markdown
::icon:icon-name::
```

Icons are fetched from the Red Hat icons repository and rendered as SVG
on the slide. See the Icons section below for available categories.

## Layout Templates

There are 14 named layout templates. Each template defines placeholder
positions, colors, and decorative elements (accent bars, background fills,
slide numbers).

### title

The first slide in the deck is automatically treated as a title slide.
It uses `# H1` for the title and `## H2` for the subtitle.

```markdown
---
title: Q2 Team Update
subtitle: June 2026
palette: redhat-brand
---

# Q2 Team Update

## June 2026

> Welcome everyone. Today we'll review Q2 progress.
```

### title-dark

A variant of the title slide with a dark background and light text.
Useful for high-impact openings or stage presentations.

```markdown
<!-- layout: title-dark -->

# Q2 Team Update

## June 2026
```

### section

A divider slide that introduces a new section. Uses large centered text.

```markdown
<!-- layout: section -->

# Financial Review
```

### content (default)

Standard slide with a heading and bullet points. This is the default
layout when no directive is specified.

```markdown
## Key Achievements

- Launched v2.0 to 15,000 users
- Reduced deploy time by 40%
- Achieved 99.95% uptime SLA
- Hired 3 senior engineers

> Emphasize the deploy time improvement -- it was a team effort.
```

### content-with-icon

Same as `content` but with a prominent icon rendered alongside the
title. Use the `::icon:name::` syntax in the slide body.

```markdown
<!-- layout: content-with-icon -->

## Deployment Pipeline

::icon:rocket::

- Automated builds on every merge
- Rolling deploys with health checks
- Instant rollback capability
```

### content-with-graphic

Content slide with a supporting image placed beside the text area.
The image is sized to complement the content rather than dominate.

```markdown
<!-- layout: content-with-graphic -->

## Platform Architecture

![Service mesh overview](images/mesh.png)

- Microservices on Kubernetes
- Service mesh for traffic management
- Centralized observability
```

### two-column

Side-by-side content. Use `<!-- left -->` and `<!-- right -->` markers
to separate the columns.

```markdown
<!-- layout: two-column -->

## Before and After

<!-- left -->

### Before

- Manual deployments
- 3-day release cycle
- No automated tests

<!-- right -->

### After

- CI/CD pipeline
- Deploy on merge
- 95% test coverage
```

### two-column-uneven

Similar to `two-column` but with an uneven split -- the left column is
wider than the right. Useful when one side has more detailed content.

```markdown
<!-- layout: two-column-uneven -->

## Feature Details

<!-- left -->

### Implementation

- Redesigned the authentication flow
- Added multi-factor support
- Integrated with corporate SSO
- Backward-compatible session handling

<!-- right -->

### Timeline

- Phase 1: Q1
- Phase 2: Q2
```

### image

A full-slide image with an optional heading.

```markdown
<!-- layout: image -->

# System Architecture

![Architecture diagram showing service mesh](images/architecture.png)
```

The image is scaled to fill the available slide area. Always include
descriptive alt text for accessibility.

### image-with-text

An image paired with a text area. The image occupies roughly half the
slide, with the remaining space used for a heading and bullet points.

```markdown
<!-- layout: image-with-text -->

## Team Offsite

![Team photo from the Q2 offsite](images/offsite.jpg)

- 45 attendees across 3 time zones
- Workshops on platform strategy
- Hackathon produced 3 prototypes
```

### comparison

A two-column layout with contrasting header colors, designed for
side-by-side comparisons. Uses the same `<!-- left -->` and
`<!-- right -->` markers as `two-column`.

```markdown
<!-- layout: comparison -->

## Option A vs Option B

<!-- left -->

### Option A

- Lower upfront cost
- Longer integration timeline
- Limited scalability

<!-- right -->

### Option B

- Higher upfront cost
- Faster time to value
- Scales horizontally
```

### data

A layout optimized for presenting a single key metric. Uses `# H1` for
the title, a plain text line for the prominent metric value, and bullet
points for supporting context.

```markdown
<!-- layout: data -->

# Monthly Active Users

2.4 Million

- Up 18% from last quarter
- 60% mobile, 40% desktop
- Strongest growth in APAC region
```

### quote

A layout for displaying a quotation. Uses Markdown blockquote syntax
(`>`) for the quote text and `### H3` for the attribution line.

```markdown
<!-- layout: quote -->

> The best way to predict the future is to invent it.

### Alan Kay
```

### closing

A closing slide, typically used for "Thank You" or "Questions?" endings.

```markdown
<!-- layout: closing -->

# Thank You

## Questions?
```

## Custom Layouts

You can define custom layouts in the frontmatter `custom_layouts` field.
Each custom layout specifies background color, accent bar, slide number
visibility, and a set of named placeholders with position, size, role,
and styling.

```yaml
---
title: My Deck
palette: corporate
custom_layouts:
  my-layout:
    background: background
    accent_bar: null
    slide_number: true
    placeholders:
      title:
        x: 5.0
        y: 5.0
        w: 90.0
        h: 10.0
        role: text
        font: heading_size
        color: heading
        bold: true
      body:
        x: 5.0
        y: 18.0
        w: 90.0
        h: 72.0
        role: text
        font: body_size
        color: body
        bold: false
---
```

**Placeholder fields:**

| Field | Description |
|-------|-------------|
| `x`, `y` | Position as percentage of slide width/height |
| `w`, `h` | Size as percentage of slide width/height |
| `role` | Placeholder role: `text`, `image`, or `icon` |
| `font` | Font size key from the palette (e.g., `heading_size`, `body_size`) |
| `color` | Color key from the palette (e.g., `heading`, `body`, `accent`) |
| `bold` | Whether to use bold text |

Use a custom layout the same way as a built-in one:

```markdown
<!-- layout: my-layout -->

# Custom Slide

- Content rendered using the custom placeholder positions
```

## Icons

Icons use the `::icon:name::` syntax and are sourced from the Red Hat
icons repository. They are fetched at build time and embedded as SVG.

### Syntax

```markdown
::icon:trending-up::
::icon:check-circle::
::icon:warning::
```

Place icons inline within a slide's content. They are rendered at a
standard size appropriate to their context.

### Available Icon Categories

Icons are organized into categories in the Red Hat icons repository:

- **Navigation** -- arrows, chevrons, menus, search
- **Action** -- check, close, delete, edit, save, share
- **Status** -- error, info, success, warning, pending
- **Social** -- email, chat, group, person, notifications
- **Content** -- document, folder, image, link, code
- **Data** -- chart, trending, analytics, database
- **Hardware** -- server, cloud, network, storage, container

Use descriptive icon names (e.g., `trending-up`, `check-circle`,
`arrow-right`). The build will report an error if an icon name is not
found.

## Color Palettes

Seven palettes are available. Each palette defines colors for semantic
slots used by the slide templates (background, title text, body text,
accent, divider, etc.).

### Red Hat Brand Palettes

**redhat-brand** -- Primary Red Hat brand colors. Red accents on white
backgrounds with dark text. Use for official Red Hat presentations.

**redhat-dark** -- Dark theme using Red Hat brand colors. Light text on
dark backgrounds. Suitable for stage presentations and demos.

**redhat-light** -- Light theme with subtle Red Hat brand accents.
Softer contrast than the primary brand palette.

**redhat-accessible** -- High-contrast palette meeting WCAG AA contrast
requirements. Use when accessibility is a priority.

### General-Purpose Palettes

**corporate** -- Neutral blues and grays. A safe default for business
presentations.

**modern** -- Contemporary muted tones with a warm accent. Good for
design-oriented decks.

**vibrant** -- Bold, high-saturation colors. Suitable for
attention-grabbing pitches and keynotes.

### Listing Palettes

Run the `palettes` command to see all available palettes with their
color details:

```bash
$SKILL_DIR/scripts/google-slides.py palettes
```

### Setting a Palette

Set the palette in frontmatter:

```yaml
---
title: My Deck
palette: redhat-brand
---
```

Or override on the command line:

```bash
$SKILL_DIR/scripts/google-slides.py create --file deck.md --palette modern
```

The command-line flag takes precedence over the frontmatter value.

## Round-Trip Workflow

The round-trip workflow lets you download an existing Google Slides
presentation, edit it as Markdown, rebuild, and re-upload.

### Step 1: Download

```bash
$SKILL_DIR/scripts/google-slides.py get 1abc...xyz -o deck.md
```

This exports the presentation as a Markdown file with frontmatter and
`<!-- layout: name -->` directives. The download uses layout detection
that scores each slide against all 14 built-in templates to select the
best-matching layout.

When a slide's elements don't closely match any built-in layout (score
below the threshold), the download automatically emits a `custom_layouts`
block in the frontmatter with the actual detected positions. This
preserves the exact spatial arrangement through the round-trip:

```yaml
custom_layouts:
  custom-slide-3:
    background: background
    accent_bar: null
    slide_number: true
    placeholders:
      title:
        x: 15.0
        y: 8.0
        w: 70.0
        h: 12.0
        role: text
        font: heading_size
        color: heading
        bold: true
      text_2:
        x: 15.0
        y: 25.0
        w: 70.0
        h: 15.0
        role: text
        font: body_size
        color: text
```

### Step 2: Edit

Open `deck.md` in any text editor. Add, remove, or modify slides using
the Markdown format documented above.

### Step 3: Rebuild

```bash
$SKILL_DIR/scripts/google-slides.py create --file deck.md --output deck.pptx
```

### Step 4: Verify

```bash
# Check quality and accessibility
$SKILL_DIR/scripts/google-slides.py verify --file deck.pptx

# The verify command checks:
# - Slide structure (titles, empty slides)
# - Alt text on images
# - Bullet count (readability)
# - WCAG AA color contrast (4.5:1 for body text, 3:1 for large text)
# - Text overflow (estimated overflow warnings)
# - Image DPI (minimum 150 DPI)

# Preview as images (requires LibreOffice)
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx --format images

# Or get a quick text summary
$SKILL_DIR/scripts/google-slides.py preview --file deck.pptx --format summary
```

### Step 5: Upload

```bash
# Replace all slides in the original presentation
$SKILL_DIR/scripts/google-slides.py update 1abc...xyz --file deck.pptx --mode replace

# Or append new slides
$SKILL_DIR/scripts/google-slides.py update 1abc...xyz --file deck.pptx --mode append
```

### Tips

- Keep the Markdown source in version control alongside your project.
- Use `verify` before uploading to catch accessibility issues early.
- The `get` command uses layout detection to emit accurate
  `<!-- layout: name -->` directives. Slides that don't match built-in
  layouts get auto-generated `custom_layouts` in frontmatter, so
  round-tripping preserves positioning even for unusual slide designs.
- Use `--mode append` when adding slides to a shared deck without
  disrupting existing content.
