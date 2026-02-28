> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P2] Tool: Backfill btc_regime in historischen Snapshots (date range)

## Context / Source (optional)
- Neue Snapshots speichern meta.btc_regime (Ticket 2).
- Alte Snapshots sollen optional ergänzt werden, ohne Exporter zu blockieren.

## Goal
Ein CLI Tool ergänzt `meta.btc_regime` in bestehenden snapshot JSONs für einen Datumsbereich.

## Scope
- New: scanner/tools/backfill_btc_regime.py
- Tests: tests/test_backfill_btc_regime.py

## Out of Scope
- Missing snapshot creation (separates Ticket)
- Dataset export

## Canonical References (important)
- Snapshot schema versioning (Ticket 2)
- btc_regime computation: scanner/pipeline/regime.py

## Proposed change (high-level)
CLI:
- `python -m scanner.tools.backfill_btc_regime --from YYYY-MM-DD --to YYYY-MM-DD [--dry-run] [--strict-missing]`

Behavior:
- For each snapshot file in range:
  - if missing: warn+skip unless strict
  - if meta.btc_regime already present: no-op
  - else compute btc_regime deterministically (preferred: compute_btc_regime_from_1d_features if possible)
  - write back snapshot with meta.btc_regime added
  - set meta.version to at least "1.1" (if version missing or "1.0")

## Acceptance Criteria (deterministic)
1) Tool adds meta.btc_regime only when missing.
2) Tool does not change other snapshot content (except meta.version bump to "1.1" if needed).
3) dry-run does not modify files.
4) strict-missing makes tool fail if any date in range has missing snapshot file.
5) Tests cover: already present, missing snapshot, dry run, version bump.

## Tests (required if logic changes)
- Use fixture snapshots with and without btc_regime.

## Constraints / Invariants (must not change)
- No lookahead
- Deterministic computation
- Minimal diffs to snapshots

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
