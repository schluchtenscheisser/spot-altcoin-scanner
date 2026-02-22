# PR10 — Excel Output: Keep legacy “Breakout Setups” worksheet for compatibility

## Short explanation
`scanner/pipeline/excel_output.py` renamed the existing breakout worksheet to “Breakout Immediate 1-5D” and stopped writing the legacy sheet name “Breakout Setups”. This is a breaking change for downstream consumers that access worksheets by name (e.g. `wb["Breakout Setups"]`). Since other changes are treated as additive, Excel output should preserve the legacy sheet (either unchanged or as an alias).

Fix: always create the legacy “Breakout Setups” sheet, keeping its historical structure, while also adding the new 1–5D sheets.

## Scope
- Restore legacy sheet name “Breakout Setups” in generated Excel reports.
- Keep new sheets for Immediate/Retest/Global.
- Add tests to lock sheet existence.

## Files to change
- `scanner/pipeline/excel_output.py`
- `tests/`

---

## Required code changes (exact)

### 1) Always create legacy sheet
When generating the workbook:
- Ensure a worksheet named exactly: `Breakout Setups` exists.
- Populate it with the same content as the legacy breakout list (the pre-rename content).
  - If legacy breakout list is no longer computed, populate with the current legacy breakout setup outputs (whatever previously fed that sheet).
  - Do not repurpose it to show only 1–5D immediate/retest unless that is exactly what the legacy sheet used to show.

### 2) Keep new sheets
Keep:
- `Breakout Immediate 1-5D`
- `Breakout Retest 1-5D`
- `Global Top20` (or whatever your naming is)
but do not remove the legacy sheet.

### 3) No breaking renames
Do not rename existing sheet identifiers other than adding the legacy back.

---

## Tests (tests-first)

### A) Workbook contains legacy sheet
Generate an Excel report in a unit/integration test.
Assert:
- `Breakout Setups` is present in `wb.sheetnames`.

### B) New sheets still present
Assert:
- `Breakout Immediate 1-5D` present
- `Breakout Retest 1-5D` present

---

## Acceptance criteria
- Excel output contains the legacy sheet “Breakout Setups” plus the new 1–5D sheets.
- Tests pass.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
