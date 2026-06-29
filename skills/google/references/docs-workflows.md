# Docs Workflows

Round-trip workflows for importing, formatting, and exporting Google Docs using the `gog` CLI.

## Markdown Import

### New document from markdown

```bash
# Step 1: Create the document from markdown
gog docs create "Document Title" --file document.md --pageless

# Step 2: Apply paragraph formatting (formatting flags are not supported with --markdown)
gog docs format <docId> --line-spacing 115 --space-below 8
```

### Update existing document from markdown

```bash
# Step 1: Import markdown content
gog docs write <docId> --file document.md --markdown --replace --pageless

# Step 2: Apply paragraph formatting
gog docs format <docId> --line-spacing 115 --space-below 8
```

Use `--check-orphans` on the write command to block replacement when open comment quotes would disappear.

### Append markdown to existing document

```bash
gog docs write <docId> --file section.md --markdown --append
```

## Frontmatter Handling

The `gog` CLI does not strip YAML frontmatter. Before importing, read the markdown file, extract the `---`-delimited frontmatter block, and pass the stripped body to `gog`.

### Supported frontmatter fields

| Field | Default | Maps to |
|-------|---------|---------|
| `title` | filename stem | `gog docs create "Title"` |
| `folder_id` | root | `gog docs create --parent <id>` |
| `line_spacing` | 115 | `gog docs format --line-spacing N` |
| `space_below` | 8 | `gog docs format --space-below N` |
| `pageless` | true | `--pageless` flag |

### Removing frontmatter after import

During markdown import, YAML frontmatter (`---` delimited) converts to a horizontal rule, followed by plain text `key: value` lines. The closing `---` may convert to a second horizontal rule or may be absent — check `gog docs structure` to confirm. After importing, remove these converted elements:

```bash
# Import the full file (frontmatter included)
gog docs write <docId> --file document.md --markdown --replace --pageless

# Use the document structure to find the end of the converted frontmatter
gog docs structure <docId> --json

# Delete from the start of the document to the end of the converted frontmatter
gog docs delete <docId> --start 1 --end <index_after_frontmatter>
```

The agent should read the frontmatter before import to extract metadata (title, folder_id, formatting preferences), then use those values for the create/format commands. The agent knows the frontmatter field count from reading the file, so it can identify the converted content in the structure output and determine the correct end index.

## Import Pre-flight Checks

Before importing, check the markdown for patterns that do not convert cleanly. Warn the user if any are found:

| Pattern | Issue |
|---------|-------|
| `- [x]` / `- [ ]` | Task list checkboxes render as plain text |
| `[text][ref]` | Reference-style links may not resolve |
| `[^1]` | Footnotes are not supported |

## Post-Import Table Formatting

After importing markdown that contains tables, apply consistent formatting.

### Step 1: Discover tables

```bash
gog docs tables list <docId> --json
```

Note the table count and column count for each table.

### Step 2: Apply cell padding

```bash
gog docs cell-style <docId> --table-index 1 \
  --row 1 --col 1 --row-span <ROWS> --col-span <COLS> \
  --padding-all 5
```

Repeat for each table, adjusting `--table-index`. The `--padding-all` flag takes a float (points), not a string.

### Step 3: Style header row

Cell style flags (`--background-color`, `--padding-*`) work with `--row-span`/`--col-span` for bulk application. Text style flags (`--bold`, `--text-color`) target one cell at a time.

```bash
# Background color across all header columns
gog docs cell-style <docId> --table-index 1 \
  --row 1 --col 1 --col-span <COLS> \
  --background-color "#E5E5E5"

# Bold each header cell individually
gog docs cell-style <docId> --table-index 1 --row 1 --col 1 --bold
gog docs cell-style <docId> --table-index 1 --row 1 --col 2 --bold
# ... repeat for each column
```

### Step 4: Compact row heights

```bash
gog docs table-row style <docId> --table 1 --min-height 0
```

Use `--table "*"` to apply to all tables at once if supported by the installed version.

## Local Image Handling

`gog docs create --file` supports images via HTTPS URLs in `![alt](url)` syntax but not local file paths. For local images:

1. Import the markdown first (images will be missing)
2. Insert each local image individually:

```bash
gog docs insert-image <docId> --file path/to/image.png --at "alt text"
```

The `--at` flag replaces the placeholder alt text with the image. Default width is 468pt (full content area); override with `--width`.

Where possible, prefer HTTPS URLs in markdown to avoid this extra step.

## Export

```bash
# Export to markdown
gog docs export <docId> --format md --out document.md

# Export to other formats
gog docs export <docId> --format pdf --out document.pdf
gog docs export <docId> --format docx --out document.docx
```

Exported markdown does not include frontmatter. If round-tripping, the agent should re-add frontmatter metadata (title, folder_id, formatting preferences) before the next import.

## Round-Trip Workflow Summary

1. **Export**: `gog docs export <docId> --format md --out doc.md`
2. **Edit**: modify the markdown locally
3. **Pre-flight**: check for unsupported patterns (see above)
4. **Import**: `gog docs write <docId> --file doc.md --markdown --replace --pageless --check-orphans`
5. **Format paragraphs**: `gog docs format <docId> --line-spacing 115 --space-below 8`
6. **Format tables**: apply padding, header styling, and compact heights (see above)
7. **Insert images**: add any local images via `insert-image` (see above)
