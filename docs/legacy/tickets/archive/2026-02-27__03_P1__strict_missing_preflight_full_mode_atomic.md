> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Backfill Snapshots: strict-missing Preflight auch in Full-Mode (atomar, keine Partial Writes)

## Context / Problem
Codex-Kommentar: `_preflight_requirements` validiert Requirements nur für `mode == "minimal"`. Bei `--strict-missing --mode full` kann der Backfill bereits frühere Tage schreiben und erst später fehlschlagen → Partial Backfill, verletzt die zugesagte Atomizität. fileciteturn2file0

## Goal
`--strict-missing` garantiert atomisches Verhalten **für beide Modi**:
- minimal
- full

Wenn Preflight fehlschlägt, darf **keine** Datei verändert/geschrieben werden.

## Scope
- scanner/tools/backfill_snapshots.py
- tests/test_backfill_snapshots.py

## Out of Scope
- Exporter
- btc_regime backfill (separates Tool)

## Proposed Change (No-Guesswork)
1) Preflight läuft immer wenn `--strict-missing` gesetzt ist:
   - determine target date list in [from..to]
   - for each date:
     - check prerequisites depending on mode:
       - minimal: local OHLCV source availability for that date
       - full: full-mode prerequisites müssen vorab geprüft werden (enumerate in code, no best-effort)
   - If any date fails prerequisites: exit non-zero **before** entering write loop.

2) Write loop is gated by successful preflight.

3) Tests:
   - simulate full-mode preflight failure on a later date; assert:
     - no snapshot files created for earlier dates
     - exit code non-zero
   - simulate full-mode preflight success: files written.

## Acceptance Criteria
1) `--strict-missing --mode full` performs preflight over full date range.
2) If preflight fails, **0 files** are written/modified.
3) Tests cover the scenario "earlier succeed, later fail" and prove atomicity.

## Definition of Done
- [ ] Code + Tests umgesetzt
- [ ] pytest -q grün
- [ ] 1 PR
