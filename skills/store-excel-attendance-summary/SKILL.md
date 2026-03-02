---
name: store-excel-attendance-summary
description: Summarize Excel records by store and business dates, compute difference against a target day count (default 27), and list missing specific dates. Use when the user asks for monthly store date reconciliation, store-level attendance day totals, missing date details, or output of a new summary workbook.
---

# Store Excel Attendance Summary

Generate a summary workbook with four columns:
- `Store`
- `ActualBusinessDays`
- `DifferenceDays`
- `MissingDates`

## Workflow

1. Confirm input workbook path and output folder.
2. Run the bundled script:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\zhang\.codex\skills\store-excel-attendance-summary\scripts\build_store_attendance_summary.ps1" -InputPath "<input.xlsx>" -OutputPath "<output.xlsx>" -ExpectedDays 27
```

3. Return output path and key counts.

## Script

- Script path: `scripts/build_store_attendance_summary.ps1`
- Default expected days: `27`
- Default output file name: `store-attendance-summary.xlsx` in same folder as input if no output path is provided
- Default input headers are Chinese labels for date and store. Override with `-DateHeader` and `-StoreHeader` if needed.

## Notes

- If script reports missing headers, pass custom header names.
- Date parsing supports Excel serial dates and text dates.
