# Google Sheets Formulas Guide

This guide covers using formulas with the Google Sheets skill.

## Formula Basics

Formulas in Google Sheets start with `=` and can reference cells, use functions, and perform calculations.

### Writing Formulas

When writing formulas via the API, include them as strings in your values array:

```bash
# Single formula
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!C2" \
  --values '[["=A2+B2"]]'

# Multiple formulas in a row
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!D2" \
  --values '[["=A2*B2","=A2/B2","=SUM(A2:C2)"]]'

# Formula column
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!E2" \
  --values '[["=A2*2"],["=A3*2"],["=A4*2"]]'
```

### Reading Formulas

Use `--format FORMULA` to read the formulas themselves:

```bash
# Read formulas
python scripts/google-sheets.py values read $SS_ID \
  --range "Sheet1!C2:C10" \
  --format FORMULA

# Read calculated values (default)
python scripts/google-sheets.py values read $SS_ID \
  --range "Sheet1!C2:C10" \
  --format FORMATTED_VALUE
```

## Common Formula Patterns

### Arithmetic Operations

```bash
# Basic math
--values '[["=A1+B1"]]'          # Addition
--values '[["=A1-B1"]]'          # Subtraction
--values '[["=A1*B1"]]'          # Multiplication
--values '[["=A1/B1"]]'          # Division
--values '[["=A1^2"]]'           # Exponentiation

# Combined
--values '[["=(A1+B1)*C1"]]'    # Parentheses for order
```

### Cell References

```bash
# Relative references (adjust when copied)
--values '[["=A1"]]'

# Absolute column ($ before column)
--values '[["=\$A1"]]'

# Absolute row ($ before row)
--values '[["=A\$1"]]'

# Absolute cell ($ before both)
--values '[["=\$A\$1"]]'
```

**Note:** Escape `$` in bash strings as `\$`.

### Common Functions

#### SUM, AVERAGE, COUNT

```bash
# Sum a range
--values '[["=SUM(A1:A10)"]]'

# Average
--values '[["=AVERAGE(B2:B20)"]]'

# Count numbers
--values '[["=COUNT(C1:C100)"]]'

# Count non-empty cells
--values '[["=COUNTA(D1:D50)"]]'
```

#### MIN, MAX

```bash
# Minimum value
--values '[["=MIN(A:A)"]]'

# Maximum value
--values '[["=MAX(B2:B100)"]]'
```

#### IF Statements

```bash
# Simple IF
--values '[["=IF(A1>10,\"High\",\"Low\")"]]'

# Nested IF
--values '[["=IF(A1>100,\"High\",IF(A1>50,\"Medium\",\"Low\"))"]]'

# IF with calculations
--values '[["=IF(B2>0,A2/B2,0)"]]'
```

#### TEXT Functions

```bash
# Concatenate
--values '[["=CONCATENATE(A1,\" \",B1)"]]'
# Or use &
--values '[["=A1&\" \"&B1"]]'

# Upper/Lower case
--values '[["=UPPER(A1)"]]'
--values '[["=LOWER(A1)"]]'

# Text length
--values '[["=LEN(A1)"]]'

# Substring
--values '[["=MID(A1,2,5)"]]'    # 5 chars starting at position 2
```

#### DATE Functions

```bash
# Today's date
--values '[["=TODAY()"]]'

# Current date and time
--values '[["=NOW()"]]'

# Date from components
--values '[["=DATE(2024,12,25)"]]'

# Date difference
--values '[["=DAYS(B1,A1)"]]'

# Format date
--values '[["=TEXT(A1,\"YYYY-MM-DD\")"]]'
```

#### LOOKUP Functions

```bash
# VLOOKUP (vertical lookup)
--values '[["=VLOOKUP(A2,Data!A:D,3,FALSE)"]]'
# Looks up A2 in Data sheet column A, returns value from column 3

# HLOOKUP (horizontal lookup)
--values '[["=HLOOKUP(\"Revenue\",A1:Z5,3,FALSE)"]]'

# INDEX/MATCH (more flexible)
--values '[["=INDEX(C:C,MATCH(A2,A:A,0))"]]'
```

## Complete Examples

### Expense Tracker

```bash
SS_ID="your-spreadsheet-id"

# Create headers
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A1" \
  --values '[["Date","Category","Amount","Running Total"]]'

# Add data with formula for running total
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A2" \
  --values '[
    ["2024-01-01","Food",50,"=C2"],
    ["2024-01-02","Transport",20,"=D2+C3"],
    ["2024-01-03","Food",30,"=D3+C4"]
  ]'

# Add summary row
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A10" \
  --values '[["Total","","=SUM(C2:C9)",""]]'
```

### Sales Report

```bash
# Headers and data
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A1" \
  --values '[
    ["Product","Units","Price","Revenue","Commission"],
    ["Widget",100,10,"=B2*C2","=D2*0.05"],
    ["Gadget",50,25,"=B3*C3","=D3*0.05"],
    ["Doohickey",75,15,"=B4*C4","=D4*0.05"]
  ]'

# Totals
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A5" \
  --values '[
    ["Total","=SUM(B2:B4)","","=SUM(D2:D4)","=SUM(E2:E4)"]
  ]'
```

### Grade Calculator

```bash
# Structure
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A1" \
  --values '[
    ["Student","Exam1","Exam2","Exam3","Average","Grade"],
    ["Alice",85,90,88,"=AVERAGE(B2:D2)","=IF(E2>=90,\"A\",IF(E2>=80,\"B\",IF(E2>=70,\"C\",\"F\")))"],
    ["Bob",78,82,75,"=AVERAGE(B3:D3)","=IF(E3>=90,\"A\",IF(E3>=80,\"B\",IF(E3>=70,\"C\",\"F\")))"]
  ]'
```

### Budget vs Actual

```bash
python scripts/google-sheets.py values write $SS_ID \
  --range "Sheet1!A1" \
  --values '[
    ["Category","Budget","Actual","Difference","% Used"],
    ["Rent",2000,2000,"=B2-C2","=C2/B2"],
    ["Food",500,450,"=B3-C3","=C3/B3"],
    ["Transport",300,275,"=B4-C4","=C4/B4"],
    ["Total","=SUM(B2:B4)","=SUM(C2:C4)","=B5-C5","=C5/B5"]
  ]'
```

## Advanced Patterns

### Array Formulas

```bash
# Apply formula to entire range at once
--values '[["=ARRAYFORMULA(A2:A10*2)"]]'

# Multiple columns
--values '[["=ARRAYFORMULA(IF(A2:A>10,\"High\",\"Low\"))"]]'
```

### Named Ranges (Indirect Reference)

```bash
# Reference a named range via INDIRECT
--values '[["=SUM(INDIRECT(\"DataRange\"))"]]'
```

### Cross-Sheet References

```bash
# Reference another sheet
--values '[["=Summary!B5"]]'

# Sum from another sheet
--values '[["=SUM(Data!A:A)"]]'

# VLOOKUP in another sheet
--values '[["=VLOOKUP(A2,OtherSheet!A:D,2,FALSE)"]]'
```

### Dynamic References

```bash
# Use INDIRECT for dynamic cell references
--values '[["=INDIRECT(\"A\"&ROW())"]]'

# Combine with other functions
--values '[["=SUM(INDIRECT(\"A1:A\"&B1))"]]'
```

## Formula Escaping

### In Bash

```bash
# Escape $ for absolute references
--values '[["=\$A\$1+B1"]]'

# Escape quotes inside formulas
--values '[["=IF(A1>10,\"Yes\",\"No\")"]]'

# Complex formula with multiple escapes
--values '[["=IF(\$A1>10,\"Value: \"&B1,\"N/A\")"]]'
```

### In JSON

```json
{
  "values": [
    ["=IF($A$1>10,\"High\",\"Low\")"]
  ]
}
```

## Troubleshooting Formulas

### #ERROR! Messages

Common errors and solutions:

```
#DIV/0!  - Division by zero
Solution: =IF(B1=0,0,A1/B1)

#VALUE!  - Wrong data type
Solution: Check cell references contain numbers

#REF!    - Invalid cell reference
Solution: Check sheet names and ranges exist

#NAME?   - Unknown function or range name
Solution: Check function spelling, ensure named ranges exist

#N/A     - VLOOKUP not found
Solution: Verify lookup value exists, check range
```

### Formula Not Calculating

```bash
# Read as formula to verify it was written correctly
python scripts/google-sheets.py values read $SS_ID \
  --range "Sheet1!C2" \
  --format FORMULA

# Check if it starts with =
# If not, rewrite with = prefix
```

### Circular Reference

```bash
# Formula references itself
# Example: A1 contains "=A1+1"
# Solution: Break the circular reference by using different cells
```

## Performance Tips

1. **Use ranges instead of individual cells** in formulas:
   ```bash
   # Better
   --values '[["=SUM(A1:A100)"]]'

   # Avoid
   --values '[["=A1+A2+A3+...+A100"]]'
   ```

2. **Minimize VLOOKUP usage** - Consider INDEX/MATCH for large datasets

3. **Avoid volatile functions** when possible:
   - `NOW()`, `TODAY()`, `RAND()`, `RANDBETWEEN()`
   - These recalculate on every change

4. **Use ARRAYFORMULA** for applying formulas to ranges:
   ```bash
   # One formula for entire column
   --values '[["=ARRAYFORMULA(A2:A100*2)"]]'
   ```

## API Behavior

### USER_ENTERED Mode

When writing values, the skill uses `USER_ENTERED` mode, which:
- Interprets strings starting with `=` as formulas
- Parses numbers from strings
- Interprets date strings as dates

```bash
# These are treated as formulas
--values '[["=SUM(A1:A10)"]]'
--values '[["=2+2"]]'

# This is treated as text (no =)
--values '[["SUM(A1:A10)"]]'
```

### Reading Format Options

```bash
# FORMATTED_VALUE - How it appears in UI (default)
--format FORMATTED_VALUE

# UNFORMATTED_VALUE - Underlying value
--format UNFORMATTED_VALUE

# FORMULA - The formula itself
--format FORMULA
```

## Additional Resources

- [Google Sheets Function List](https://support.google.com/docs/table/25273)
- [Formula reference documentation](https://developers.google.com/sheets/api/guides/values)
- [Array formulas guide](https://support.google.com/docs/answer/6208276)
