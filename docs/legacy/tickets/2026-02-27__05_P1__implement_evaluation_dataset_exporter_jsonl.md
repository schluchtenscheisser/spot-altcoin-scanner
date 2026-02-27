> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Implement: Evaluation Dataset Exporter (snapshots/history -> datasets/eval/eval_{run_id}.jsonl)

## Context / Source (optional)
- Roadmap verlangt Evaluation Dataset aus Snapshot-History
- Canonical Dataset Spec: docs/canonical/OUTPUTS/EVALUATION_DATASET.md (Ticket 3)
- E2 Model: scanner/backtest/e2_model.py (Ticket 4)

## Goal
Implementiere einen Exporter, der Snapshots im Datumsbereich einliest und eine JSONL-Datei erzeugt:
- 1. Zeile: meta record
- danach: candidate_setup records (1 pro Symbol×Setup×t0_date)
- E2 Outcome wird immer via E2 Model recomputed.

## Scope
- New: scanner/tools/export_evaluation_dataset.py (CLI)
- Output directory: datasets/eval/ (mkdir parents)
- Tests: tests/test_export_evaluation_dataset.py

## Out of Scope
- A3/A4 Analytics/Calibration
- Backfills (separate Tickets)

## Canonical References (important)
- docs/canonical/OUTPUTS/EVALUATION_DATASET.md
- docs/canonical/BACKTEST/MODEL_E2.md

## Proposed change (high-level)
CLI (fest):
- `python -m scanner.tools.export_evaluation_dataset --from YYYY-MM-DD --to YYYY-MM-DD [--run-id RUNID] [--strict-missing]`

Defaults:
- run_id default: aus `meta.asof_iso` des *letzten* verarbeiteten Snapshots (UTC) → "YYYY-MM-DD_HHMMZ"
- output path: `datasets/eval/eval_{run_id}.jsonl`
- missing snapshot files in range:
  - default: warn + skip
  - if --strict-missing: exit non-zero

Processing:
1) Enumeriere alle Tage im [from..to] inkl.
2) Für jedes Datum:
   - wenn file fehlt: handle per strict flag
   - lade snapshot JSON
   - wenn scoring.* leer: emit 0 candidate_setup records für dieses t0_date
   - sonst: iteriere scoring lists:
     - setup_type mapping: breakouts->breakout, pullbacks->pullback, reversals->reversal
     - setup_id: entry["setup_id"] else setup_type
     - score: mapping strikt gemäß Canonical Mapping Doc (Ticket 3)
     - setup_rank: index+1 innerhalb Liste
3) global_rank:
   - recompute compute_global_top20(...) aus snapshot scoring lists
   - match per symbol => rank 1..20 else null
4) Build price_series für E2:
   - pro date: snapshot.data.features[symbol]["1d"] -> close/high/low
   - Wenn date existiert, aber symbol fehlt: treat as missing values für diesen symbol/date
5) E2 evaluate pro candidate_setup:
   - ruft scanner/backtest/e2_model.py auf
   - thresholds_pct: konfigurierbar, aber muss 10/20 enthalten (per Canonical)
6) Write JSONL:
   - First line meta record: type="meta" enthält run_id, from_date, to_date, generated_at_iso, thresholds_pct, T_hold, T_trigger_max, dataset_schema_version, etc.
   - Danach candidate_setup lines in stabiler Reihenfolge:
     - sort key: (t0_date, setup_type, setup_rank, symbol)

## Acceptance Criteria (deterministic)
1) CLI existiert und funktioniert für beliebigen Datumsbereich.
2) Output JSONL: erste Zeile meta record, danach nur candidate_setup records.
3) run_id:
   - default aus snapshot.meta.asof_iso (letzter Snapshot)
   - optional override via --run-id
4) record_id exakt: "{run_id}:{t0_date}:{symbol}:{setup_type}:{setup_id}"
5) E2 outcomes werden immer recomputed via e2_model (keine Übernahme alter Felder).
6) setup_rank/global_rank Regeln exakt (setup_rank immer, global_rank nur Top20 else null).
7) Missing snapshot files: default warn+skip; --strict-missing => fail.
8) Determinismus: gleiche Inputs => byte-identischer Output (stable ordering; keine neue Rundung).

## Tests (required if logic changes)
- Unit/Integration:
  - Fixture snapshots (synthetic small JSON) in tests/fixtures/snapshots/history/
  - Tests:
    - meta record exists and correct fields present
    - candidate_setup count matches scoring entries
    - ordering stable
    - run_id derivation from asof_iso works
    - strict missing causes non-zero exit
    - btc_regime missing in old snapshot => null in record
    - global_rank only set for top20 entries
- Golden test:
  - Compare whole output file content for a deterministic fixture range.

## Constraints / Invariants (must not change)
- Closed-candle-only
- No lookahead
- Stable ordering (explicit sort)
- No heuristic field lookups beyond canonical mapping
- JSONL only (kein CSV)

## Definition of Done (Codex must satisfy)
(Reference: docs/canonical/WORKFLOW_CODEX.md)
- [ ] Implementiert + Tests grün (pytest -q)
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR nach docs/legacy/tickets/ verschoben

---
## Metadata (optional)
```yaml
created_utc: "2026-02-27T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
