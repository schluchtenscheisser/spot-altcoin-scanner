# PR7 — Reports: bump schema version for `btc_regime` + honor `output.top_n_per_setup` for Breakout 1–5D lists

## Short explanation
Two report-contract regressions:
1) Adding top-level `btc_regime` changes the JSON report schema, but `schema_version` was not bumped and `docs/SCHEMA_CHANGES.md` was not updated — this is a silent breaking change.
2) Breakout 1–5D lists in markdown/json are hard-sliced with `[:20]`, ignoring `output.top_n_per_setup`, which breaks the config contract and creates inconsistent report sizing.

Fix both together in one PR because they touch the same output/report contract.

## Scope
- Update schema version + schema changes docs.
- Fix output list limiting to use configured `top_n_per_setup` consistently.
- Add/adjust tests to lock contract.

## Files to change
- `scanner/pipeline/output.py`
- `scanner/schema.py` (or wherever schema version is defined)
- `docs/SCHEMA_CHANGES.md`
- `tests/`

---

## Required code changes (exact)

### 1) Schema bump for JSON report
- Increment `schema_version` (currently v1.6) to the next version (e.g. v1.7).
- Ensure the JSON report includes the bumped `schema_version` whenever `btc_regime` exists in payload.
- Update `docs/SCHEMA_CHANGES.md` with an entry describing:
  - added top-level `btc_regime` object
  - fields inside it (`state`, multipliers, checks)
  - new setup IDs (if not already documented)

### 2) Honor `output.top_n_per_setup` for Breakout Trend 1–5D lists
In `scanner/pipeline/output.py` (and JSON/markdown generation):
- Replace any hardcoded `[:20]` slicing for:
  - Breakout Immediate (1–5D)
  - Breakout Retest (1–5D)
with the same per-setup limit used elsewhere, i.e. the configured `output.top_n_per_setup` (or existing `self.top_n` variable).
- Ensure consistent behavior across all setup lists.

---

## Tests (tests-first)

### A) Schema version bump when btc_regime present
- Create a unit test that generates a minimal JSON report payload with `btc_regime` included.
Assert:
- `schema_version` equals the new version (e.g. `"1.7"`).
- `btc_regime` is present in output.

### B) Breakout 1–5D lists honor `top_n_per_setup`
- Configure `output.top_n_per_setup = 1` in test config.
- Provide a payload with multiple breakout immediate/retest rows.
Assert:
- Output includes at most 1 row for each of those lists (markdown and/or JSON, whichever you test).
- No hardcoded 20 behavior remains.

---

## Acceptance criteria
- Schema version is bumped and documented.
- Breakout 1–5D lists respect configured per-setup limits.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
