# Presentations Guide

This guide covers the Markdown format for writing presentations, available
slide types, color palettes, icon syntax, and the round-trip workflow.

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

### Slide Type Directives

Set the slide type with an HTML comment at the start of a slide:

```markdown
---

<!-- type: section -->

# Section Title
```

If no directive is present, the slide defaults to `content` type (except
the first slide, which is auto-detected as `title`).

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

## Slide Types

### Title Slide

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

### Section Slide

A divider slide that introduces a new section. Uses large centered text.

```markdown
<!-- type: section -->

# Financial Review
```

### Content Slide (default)

Standard slide with a heading and bullet points. This is the default
type when no directive is specified.

```markdown
## Key Achievements

- Launched v2.0 to 15,000 users
- Reduced deploy time by 40%
- Achieved 99.95% uptime SLA
- Hired 3 senior engineers

> Emphasize the deploy time improvement -- it was a team effort.
```

### Two-Column Slide

Side-by-side content. Use `<!-- left -->` and `<!-- right -->` markers
to separate the columns.

```markdown
<!-- type: two-column -->

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

### Image Slide

A full-slide image with an optional heading.

```markdown
<!-- type: image -->

# System Architecture

![Architecture diagram showing service mesh](images/architecture.png)
```

The image is scaled to fill the available slide area. Always include
descriptive alt text for accessibility.

### Closing Slide

A closing slide, typically used for "Thank You" or "Questions?" endings.

```markdown
<!-- type: closing -->

# Thank You

## Questions?
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
slide type directives.

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
- The `get` command preserves slide type directives, so round-tripping
  maintains slide types accurately.
- Use `--mode append` when adding slides to a shared deck without
  disrupting existing content.
