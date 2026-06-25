# Sheets Command Reference

Full command reference for `gog sheets`. All commands support `--json` and `--plain` output.

## Read

| Command | Description |
|---------|-------------|
| `metadata <spreadsheetId>` | Get spreadsheet metadata |
| `get <spreadsheetId> <range>` | Get values from a range |
| `read-format <spreadsheetId> <range>` | Read cell formatting |
| `notes <spreadsheetId> <range>` | Get cell notes |
| `raw <spreadsheetId>` | Dump raw API response as JSON |

### Get flags

- `--format FORMATTED_VALUE|UNFORMATTED_VALUE|FORMULA` — value render option

### Range syntax (A1 notation)

- `Sheet1!A1:D10` — specific range
- `Sheet1!A:A` — entire column
- `Sheet1!1:1` — entire row
- `'Sheet Name With Spaces'!A1:B5` — quote sheet names with spaces

## Write

| Command | Description |
|---------|-------------|
| `update <spreadsheetId> <range> [values...]` | Update values in a range |
| `batch-update <spreadsheetId>` | Update multiple ranges at once |
| `append <spreadsheetId> <range> [values...]` | Append values to a range |
| `clear <spreadsheetId> <range>` | Clear values in a range |
| `insert <spreadsheetId> <sheet> <dimension> <start>` | Insert empty rows/columns |
| `delete-dimension <spreadsheetId> <rangeOrSheet>` | Delete rows or columns |
| `update-note <spreadsheetId> <range>` | Set or clear a cell note |
| `find-replace <spreadsheetId> <find> <replace>` | Find and replace text |

### Update flags

- `--input RAW|USER_ENTERED` — how to interpret input (default: USER_ENTERED)

## Create and Export

| Command | Description |
|---------|-------------|
| `create <title>` | Create a new spreadsheet |
| `copy <spreadsheetId> <title>` | Copy a spreadsheet |
| `export <spreadsheetId>` | Export (pdf, xlsx, csv) |

## Formatting

| Command | Description |
|---------|-------------|
| `format <spreadsheetId> <range>` | Apply cell formatting |
| `number-format <spreadsheetId> <range>` | Apply number format |
| `conditional-format` | Manage conditional formatting rules |
| `merge <spreadsheetId> <range>` | Merge cells |
| `unmerge <spreadsheetId> <range>` | Unmerge cells |
| `freeze <spreadsheetId>` | Freeze rows and columns |
| `resize-columns <spreadsheetId> <columns>` | Resize columns |
| `resize-rows <spreadsheetId> <rows>` | Resize rows |
| `copy-paste <spreadsheetId> <source> <dest>` | Copy range values/format |
| `banding` | Manage alternating color banding |

## Structure

| Command | Description |
|---------|-------------|
| `add-tab <spreadsheetId> <tabName>` | Add a new tab/sheet |
| `rename-tab <spreadsheetId> <oldName> <newName>` | Rename a tab |
| `delete-tab <spreadsheetId> <tabName>` | Delete a tab |
| `reorder-tab <spreadsheetId>` | Move a tab to a position |

## Advanced

| Command | Description |
|---------|-------------|
| `links` | Get or set cell hyperlinks |
| `named-ranges` | Manage named ranges |
| `table` | Manage Google Sheets tables |
| `chart` | Manage spreadsheet charts |
| `validation` | Manage data validation rules |
