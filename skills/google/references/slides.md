# Slides Command Reference

Full command reference for `gog slides`. All commands support `--json` and `--plain` output.

## Read

| Command | Description |
|---------|-------------|
| `info <presentationId>` | Get presentation metadata |
| `list-slides <presentationId>` | List all slides with object IDs |
| `read-slide <presentationId> <slideId>` | Read slide content (notes, text, images) |
| `locate <presentationId> <text>` | Find text in shapes/tables with object IDs |
| `thumbnail <presentationId> <slideId>` | Get or download a slide thumbnail |
| `raw <presentationId>` | Dump raw API response as JSON |

## Create

| Command | Description |
|---------|-------------|
| `create <title>` | Create a new presentation |
| `create-from-markdown <title>` | Create presentation from markdown |
| `create-from-template <templateId> <title>` | Create from template with replacements |
| `copy <presentationId> <title>` | Copy a presentation |
| `export <presentationId>` | Export presentation (pdf, pptx) |

### Create from markdown flags

- `--file slides.md` — read markdown from file
- `--stdin` — read markdown from stdin

### Create from template flags

- `--replacements '{"{{KEY}}":"value"}'` — text replacements as JSON

## Slide Management

| Command | Description |
|---------|-------------|
| `new-slide <presentationId>` | Create a native themed slide |
| `add-slide <presentationId> <image>` | Add a slide with full-bleed image |
| `duplicate-slide <presentationId> <slideId>` | Duplicate a slide |
| `move-slide <presentationId> <slideId>` | Move slide to a position |
| `delete-slide <presentationId> <slideId>` | Delete a slide |
| `replace-slide <presentationId> <slideId> [<image>]` | Replace slide image |
| `update-notes <presentationId> <slideId>` | Update speaker notes |

## Content Editing

| Command | Description |
|---------|-------------|
| `insert-text <presentationId> <objectId> <text>` | Insert text into a shape/table |
| `replace-text <presentationId> <find> <replacement>` | Find and replace text |
| `insert-image <presentationId> <slideId> [<image>]` | Insert an image |
| `style-text <presentationId> <objectId>` | Apply text styling |
| `link <presentationId> <objectId>` | Apply a hyperlink to text |
| `bullets <presentationId> <objectId>` | Toggle paragraph bullets |

### Style-text flags

- `--range "0:10"` — character range to style
- `--bold` / `--italic` / `--underline` — text styling
- `--font-size <pt>` — font size
- `--font-family "Arial"` — font family
- `--color "#FF0000"` — text color

## Tables and Elements

| Command | Description |
|---------|-------------|
| `table create <presentationId> <slideId>` | Create a native table |
| `table update <presentationId> <objectId>` | Update table content |
| `element create <presentationId> <slideId>` | Create a page element |
| `element delete <presentationId> <objectId>` | Delete a page element |
| `element transform <presentationId> <objectId>` | Transform element position/size |
