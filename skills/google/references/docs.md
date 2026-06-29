# Docs Command Reference

Full command reference for `gog docs`. All commands support `--json` and `--plain` output.

## Read

| Command | Description |
|---------|-------------|
| `info <docId>` | Get document metadata |
| `cat <docId>` | Print document as plain text |
| `export <docId>` | Export document (pdf, docx, txt, md, html) |
| `structure <docId>` | Show document structure with numbered paragraphs |
| `headings list <docId>` | List document headings |
| `paragraphs list <docId>` | List document paragraphs |
| `tables list <docId>` | List native tables (use `--json` to get row/column counts) |
| `images list <docId>` | List document images |
| `raw <docId>` | Dump raw API response as JSON |

### Export flags

- `--format pdf|docx|txt|md|html` — output format (default: pdf)
- `--out <path>` — output file path

## Create and Copy

| Command | Description |
|---------|-------------|
| `create <title>` | Create a new document |
| `copy <docId> <title>` | Copy a document |

### Create flags

- `--folder <folderId>` — create in specific folder
- `--body "Initial content"` — set initial content
- `--file <path.md>` — import from markdown file (supports inline HTTPS images)
- `--pageless` — set document to pageless mode
- `--parent <folderId>` — destination folder ID

## Write Content

| Command | Description |
|---------|-------------|
| `write <docId>` | Write/append content |
| `insert <docId> <content>` | Insert text at a position |
| `delete <docId>` | Delete a text range |
| `clear <docId>` | Clear all content |
| `update <docId>` | Insert or replace text at index/range |
| `edit <docId> <find> <replace>` | Find and replace text |
| `find-replace <docId> <find> [<replace>]` | Find and replace (supports markdown) |
| `sed <docId> <expression>` | Regex find/replace (sed-style) |

### Write flags

- `--body "Content"` — text to write
- `--body-file path.md` — read content from file
- `--file <path.md>` — text file path (`-` for stdin)
- `--markdown` — convert markdown to Google Docs formatting (requires `--replace` or `--append`)
- `--replace` — replace all content
- `--append` — append instead of replacing
- `--at <index>` — insertion index
- `--at-end` — append at end
- `--pageless` — set document to pageless mode
- `--line-spacing <N>` — paragraph line spacing percentage (e.g. 115)
- `--space-above <Npt>` — space above paragraphs in points
- `--space-below <Npt>` — space below paragraphs in points
- `--check-orphans` — block markdown replacement when open comment quotes would disappear

## Formatting

| Command | Description |
|---------|-------------|
| `format <docId>` | Apply text or paragraph formatting |
| `find-range <docId> <text>` | Find text and print UTF-16 index ranges |
| `page-layout <docId>` | Set page layout (pageless or pages) |
| `section-columns <docId>` | Set column count for a section |

### Format flags

- `--bold` / `--italic` / `--underline` — text styling
- `--font-size <pt>` — font size in points
- `--font-family "Arial"` — font family
- `--start <index>` / `--end <index>` — range to format
- `--alignment LEFT|CENTER|RIGHT|JUSTIFIED` — paragraph alignment

## Tables

| Command | Description |
|---------|-------------|
| `insert-table <docId>` | Insert a table (--rows, --cols) |
| `cell-update <docId>` | Replace or append cell content |
| `cell-style <docId>` | Apply cell/border/text styling |
| `table-row` | Insert, delete, style, or pin rows |
| `table-column` | Insert or delete columns |
| `table-merge <docId>` | Merge a cell range |
| `table-unmerge <docId>` | Unmerge cells |
| `table-column-width <docId>` | Set column widths |

## Images and Rich Content

| Command | Description |
|---------|-------------|
| `insert-image <docId>` | Insert image (URL or local file) |
| `replace-image <docId>` | Replace an existing image |
| `insert-person <docId>` | Insert a person smart chip |
| `insert-file-chip <docId>` | Insert a Drive file smart chip |
| `insert-date-chip <docId>` | Insert a date smart chip |
| `insert-page-break <docId>` | Insert a page break |
| `insert-footnote <docId>` | Insert and populate a footnote |
| `insert-section-break <docId>` | Insert a section break |
| `insert-horizontal-rule <docId>` | Insert a horizontal rule |

## Tabs

| Command | Description |
|---------|-------------|
| `list-tabs <docId>` | List all tabs |
| `add-tab <docId>` | Add a tab |
| `rename-tab <docId>` | Rename a tab |
| `delete-tab <docId>` | Delete a tab |

## Workflows

See [docs-workflows.md](docs-workflows.md) for round-trip import/export recipes, frontmatter handling, and table formatting.

## Other

| Command | Description |
|---------|-------------|
| `comments` | Manage document comments |
| `named-range` | Manage named ranges |
| `header` | List, create, or delete headers |
| `footer` | List, create, or delete footers |
