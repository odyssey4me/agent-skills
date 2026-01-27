# Google Sheets Range Notation Guide

This guide covers A1 notation for specifying cell ranges in Google Sheets.

## A1 Notation Basics

A1 notation is the standard way to refer to cells and ranges in Google Sheets.

### Single Cell

```
A1          - Cell in column A, row 1
B5          - Cell in column B, row 5
Z100        - Cell in column Z, row 100
AA1         - Cell in column AA (27th column), row 1
```

### Column References

Columns are lettered from A to ZZZ (18,278 columns maximum).

```
A, B, C, ... Z           - First 26 columns
AA, AB, AC, ... AZ       - Columns 27-52
BA, BB, BC, ... BZ       - Columns 53-78
ZA, ZB, ... ZZ           - Columns 677-702
AAA, AAB, ... ZZZ        - Columns 703-18278
```

### Row References

Rows are numbered from 1 to 10,000,000.

### Range Notation

```
A1:B2       - 2x2 range from A1 to B2
A1:A10      - Column A, rows 1-10
A1:Z1       - Row 1, columns A-Z
A:A         - Entire column A
1:1         - Entire row 1
A:C         - Columns A through C (all rows)
1:10        - Rows 1 through 10 (all columns)
```

## Sheet-Qualified Ranges

To specify a range on a particular sheet, use the format: `SheetName!Range`

```
Sheet1!A1:D5            - Range A1:D5 on Sheet1
'My Sheet'!A1:B10       - Range on sheet with spaces (needs quotes)
'Q1 Data'!A:A           - Column A on 'Q1 Data' sheet
Summary!1:1             - Row 1 on Summary sheet
```

### Sheet Names with Special Characters

If a sheet name contains spaces, special characters, or starts with a number, enclose it in single quotes:

```
'2024 Sales'!A1:D5
'Revenue (Q1)'!A1:B10
'Sheet #1'!A:Z
```

## Common Patterns

### Headers and Data

```bash
# Read headers
--range "Sheet1!A1:Z1"

# Read first 100 rows of data (excluding header)
--range "Sheet1!A2:Z101"

# Read specific columns
--range "Sheet1!A:A,C:C,E:E"  # Note: Multiple ranges not supported in single command
```

### Named Ranges

Google Sheets supports named ranges, but this skill uses A1 notation. To work with named ranges:

1. Get the range reference from the spreadsheet metadata
2. Use the A1 notation equivalent

### Unbounded Ranges

```
Sheet1!A1:Z          - From A1 to column Z, all rows
Sheet1!A2:B          - From A2 to column B, all rows
Sheet1!A:A           - Entire column A
Sheet1!1:1           - Entire row 1
```

## Usage Examples

### Reading Data

```bash
# Read a fixed range
python scripts/google-sheets.py values read $SS_ID --range "Sheet1!A1:D10"

# Read entire sheet (up to used range)
python scripts/google-sheets.py values read $SS_ID --range "Sheet1"

# Read multiple columns
python scripts/google-sheets.py values read $SS_ID --range "Sheet1!A:A"
python scripts/google-sheets.py values read $SS_ID --range "Sheet1!C:E"

# Read specific row
python scripts/google-sheets.py values read $SS_ID --range "Sheet1!5:5"
```

### Writing Data

```bash
# Write to specific cell
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A1" \
  --values '[["Header"]]'

# Write a row
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A2" \
  --values '[["Value1","Value2","Value3"]]'

# Write a column
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A1" \
  --values '[["R1"],["R2"],["R3"]]'

# Write a block
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!B2" \
  --values '[["A","B"],["C","D"]]'
```

### Appending Data

```bash
# Append to sheet (finds next empty row)
python scripts/google-sheets.py values append $SS_ID \
  --range "Sheet1" \
  --values '[["New","Row"]]'

# Append to specific range (still finds next empty)
python scripts/google-sheets.py values append $SS_ID \
  --range "Sheet1!A:C" \
  --values '[["Data","In","Columns ABC"]]'
```

### Clearing Data

```bash
# Clear specific range
python scripts/google-sheets.py values clear $SS_ID --range "Sheet1!A1:Z100"

# Clear entire sheet
python scripts/google-sheets.py values clear $SS_ID --range "Sheet1"

# Clear specific rows
python scripts/google-sheets.py values clear $SS_ID --range "Sheet1!5:10"

# Clear specific columns
python scripts/google-sheets.py values clear $SS_ID --range "Sheet1!A:C"
```

## Range Size Calculations

### Column Index to Letter

```
1 → A
26 → Z
27 → AA
52 → AZ
53 → BA
702 → ZZ
703 → AAA
```

### Range Dimensions

When writing data, the range automatically expands:

```bash
# Writing 2x3 array to A1
--range "Sheet1!A1" --values '[["A","B","C"],["D","E","F"]]'
# Actually writes to A1:C2

# Writing single column to B1
--range "Sheet1!B1" --values '[["R1"],["R2"],["R3"]]'
# Actually writes to B1:B3
```

## Advanced Patterns

### Dynamic Ranges

To work with dynamic data:

```bash
# Read to find data extent
DATA=$(python scripts/google-sheets.py values read $SS_ID \
  --range "Sheet1" --json)

# Process to determine actual range
# Then write to specific calculated range
```

### Multi-Sheet Operations

```bash
# Read from multiple sheets
python scripts/google-sheets.py values read $SS_ID --range "Summary!A1:D10"
python scripts/google-sheets.py values read $SS_ID --range "Details!A1:Z100"

# Copy pattern (read from one, write to another)
DATA=$(python scripts/google-sheets.py values read $SS_ID \
  --range "Source!A1:C10" --json | jq '.values')

python scripts/google-sheets.py values write $SS_ID \
  --range "Destination!A1" \
  --values "$DATA"
```

### Absolute vs Relative References

A1 notation in the API is absolute - it always refers to specific cells:

```
A1      - Always cell A1
$A$1    - Also cell A1 ($ notation is for formulas, not API)
```

For formulas within cells, use $ notation:

```bash
# Formula with absolute reference
--values '[["=\$A\$1*2"]]'

# Formula with relative reference
--values '[["=A1*2"]]'
```

## Limitations

### Maximum Ranges

- Maximum columns: 18,278 (A to ZZZ)
- Maximum rows: 10,000,000
- Maximum cells per sheet: 10,000,000

### Multiple Ranges

This skill doesn't support multiple discontinuous ranges in a single command. For multiple ranges, make multiple API calls:

```bash
# Not supported
--range "Sheet1!A:A,C:C,E:E"

# Instead, use multiple commands
python scripts/google-sheets.py values read $SS_ID --range "Sheet1!A:A"
python scripts/google-sheets.py values read $SS_ID --range "Sheet1!C:C"
python scripts/google-sheets.py values read $SS_ID --range "Sheet1!E:E"
```

## Error Messages

### "Unable to parse range"

- Check sheet name is properly quoted if it has spaces
- Ensure range uses correct A1 notation
- Verify sheet exists in spreadsheet

```bash
# Wrong
--range "My Sheet!A1:D5"      # Missing quotes

# Correct
--range "'My Sheet'!A1:D5"
```

### "Range not found"

- Sheet name doesn't exist
- Check spelling and capitalization
- Use `spreadsheets get` to see available sheets

### "Requested range is outside grid limits"

- Range exceeds sheet dimensions
- Check column letters and row numbers
- Extend sheet size if needed (via web UI or API)

## Quick Reference

| Pattern | Description | Example |
|---------|-------------|---------|
| `A1` | Single cell | `Sheet1!B5` |
| `A1:B2` | Rectangle | `Sheet1!A1:D10` |
| `A:A` | Entire column | `Sheet1!C:C` |
| `1:1` | Entire row | `Summary!1:1` |
| `A1:Z` | Unbounded right | `Sheet1!A1:Z` |
| `A2:A` | Unbounded down | `Sheet1!A2:A` |
| `Sheet!Range` | Qualified | `'Q1'!A1:C3` |

## Best Practices

1. **Always qualify with sheet name** - Use `Sheet1!A1` not just `A1`
2. **Quote special sheet names** - Use `'My Sheet'!A1` for names with spaces
3. **Use specific ranges** - Prefer `A1:D10` over unbounded `A:D` for performance
4. **Check existence first** - Use `spreadsheets get` to verify sheets exist
5. **Start from A1** - Avoid leaving empty rows/columns at the start

## API Reference

For complete details:
- [Google Sheets API - A1 Notation](https://developers.google.com/sheets/api/guides/concepts#cell)
- [ValueRange reference](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values#ValueRange)
