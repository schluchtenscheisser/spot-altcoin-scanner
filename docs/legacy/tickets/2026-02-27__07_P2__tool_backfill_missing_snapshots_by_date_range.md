> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P2] Tool: Backfill missing snapshots (by date range) — default minimal, optional --full

## Context / Source (optional)
- Es existieren historische Lücken in snapshots/history (fehlender Tag).
- E2/Exporter nutzen Snapshot-Features; Hold-Window ist strict => Lücken führen zu insufficient_forward_history.
- Wir wollen offline/deterministisch bleiben (kein API-Nachladen im Exporter).

## Goal
Ein CLI Tool erstellt fehlende Snapshot-Dateien in einem Datumsbereich:
- Default: minimaler Backfill-Snapshot (Backtest-minimal)
- Optional: --full versucht vollständigen Pipeline-Run (best effort)

## Scope
- New: scanner/tools/backfill_snapshots.py
- Tests: tests/test_backfill_snapshots.py

## Out of Scope
- Änderung der Pipeline-Run-Logik für echtes “historical as-of”; --full ist optional/best effort, muss aber klar dokumentiert sein.

## Canonical References (important)
- Snapshot format: scanner/pipeline/snapshot.py
- Dataset needs: docs/canonical/OUTPUTS/EVALUATION_DATASET.md
- E2 needs: docs/canonical/BACKTEST/MODEL_E2.md

## Proposed change (high-level)
CLI:
- `python -m scanner.tools.backfill_snapshots --from YYYY-MM-DD --to YYYY-MM-DD [--mode minimal|full] [--dry-run] [--strict-existing]`

Default mode:
- minimal

Behavior (minimal):
- For each date in range:
  - if snapshots/history/{date}.json exists:
    - default: skip
    - if --strict-existing: fail
  - else create minimal snapshot with structure:
    - meta:
      - date=<date>
      - created_at=<now utc iso + Z>
      - version="1.1"
      - asof_ts_ms + asof_iso (UTC, derived from created_at)
      - backfill=true
      - backfill_mode="minimal"
      - backfill_source="ohlcv_only"
    - pipeline: counts (0 or derived)
    - data:
      - features: for each symbol available in the source OHLCV dataset for that date,
        include {"1d": {"close":..., "high":..., "low":...}}
    - scoring: {"reversals": [], "breakouts": [], "pullbacks": []}
- Source OHLCV dataset for minimal mode:
  - MUST be explicitly defined in implementation (e.g. read from a local cache/raw store if existing in repo; do not “guess”).
  - If no local OHLCV source exists for that date, tool must fail with clear error (no silent partial snapshot).

Behavior (full):
- If mode=full:
  - attempt to run pipeline for that date and write snapshot
  - backfill_mode="full", backfill_source="pipeline"

Acceptance behavior for Dataset Exporter:
- days with empty scoring lists will yield 0 records.

## Acceptance Criteria (deterministic)
1) Tool creates missing snapshot JSON files for dates without files (minimal mode).
2) Minimal snapshots contain meta backfill flags exactly:
   - meta.backfill=true
   - meta.backfill_mode="minimal"
   - meta.backfill_source="ohlcv_only"
3) Minimal snapshots contain scoring lists empty arrays.
4) Minimal snapshots contain only required 1d OHLCV fields under data.features[*].1d: close/high/low.
5) dry-run produces no files.
6) strict-existing fails if any target date already has a snapshot file.
7) Tests cover: missing file created, existing file skipped, strict-existing, dry-run, meta flags.

## Tests (required if logic changes)
- Use a temporary directory for snapshots/history in tests (monkeypatch path).
- Provide a deterministic local OHLCV fixture source for minimal mode.

## Constraints / Invariants (must not change)
- Determinismus: generated snapshot must have stable structure; any ordering of symbols must be sorted.
- No lookahead: only that date’s 1d candle used in minimal mode.
- Minimal snapshots are explicitly marked via meta flags.

## Definition of Done (Codex must satisfy)
(Reference: docs/canonical/WORKFLOW_CODEX.md)
- [ ] Implementiert + Tests grün
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR nach docs/legacy/tickets/ verschoben

---
## Metadata (optional)
```yaml
created_utc: "2026-02-27T00:00:00Z"
priority: P2
type: feature
owner: codex
related_issues: []
```
