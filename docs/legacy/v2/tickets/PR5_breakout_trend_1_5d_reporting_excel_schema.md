# PR5 — Breakout Trend 1–5D: Reporting + Excel + Schema bump

## Scope
Add reporting for:
- Top 20 Immediate (1–5D)
- Top 20 Retest (1–5D)
- Global Top20 (dedup by symbol)
And ensure BTC regime block is shown at the top of markdown + excel summary.

Also bump schema version and update schema changes doc.

## Files to change
- `scanner/pipeline/output.py`
- `scanner/pipeline/excel_output.py`
- `scanner/pipeline/global_ranking.py`
- `scanner/schema.py`
- `docs/SCHEMA_CHANGES.md`
- `tests/`

## Hard requirements
### BTC block placement
- Markdown: BTC Regime section at the very top (before rankings)
- Excel Summary: BTC block at A1..B6 (explicit cells), before rankings

### Global Top20 dedup
- Per symbol: keep highest final_score row; tie -> retest
- Then top 20

## Tests (tests-first)
- Markdown serialization: BTC block appears before Global Top20 header
- Excel generator: Summary `A1 == "BTC Regime"`

## Acceptance criteria
- Reports contain the 3 ranking sections and BTC block in correct order.
- Schema version bumped and `docs/SCHEMA_CHANGES.md` updated.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge of this ticket:
1) Move **this** ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md` so the next Codex session can continue without context loss.
