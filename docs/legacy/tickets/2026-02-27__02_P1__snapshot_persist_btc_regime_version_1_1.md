> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Snapshot: meta.btc_regime persistieren + snapshot.version auf 1.1 bumpen

## Context / Source (optional)
- Pipeline berechnet btc_regime und nutzt es in Reports, Snapshot speichert es aktuell nicht (siehe scanner/pipeline/__init__.py vs scanner/pipeline/snapshot.py).
- Dataset Exporter benötigt btc_regime als Feld (nullable für Alt-Snapshots).

## Goal
Snapshots sollen btc_regime deterministisch speichern, damit Offline-Repro und Dataset Export ohne API Calls möglich ist. Snapshot-Version wird eindeutig auf 1.1 erhöht.

## Scope
- scanner/pipeline/snapshot.py
- scanner/pipeline/__init__.py (Übergabe der Daten an SnapshotManager.create_snapshot)
- ggf. docs/SCHEMA_CHANGES.md (wenn repo policy das verlangt)

## Out of Scope
- Backfill alter Snapshots (separates Ticket)
- Dataset Exporter
- E2 Model

## Canonical References (important)
- docs/SCHEMA_CHANGES.md (Schema change logging, falls gefordert durch Projektkonvention)

## Proposed change (high-level)
Before:
- snapshot.meta.version = "1.0"
- snapshot.meta enthält date/created_at/version + asof_* injected, aber kein btc_regime.

After:
- snapshot.meta.version = "1.1"
- snapshot.meta.btc_regime = <btc_regime object> (so wie compute_btc_regime(...) es liefert)
- Keine Änderung an bestehenden meta Feldern (date/created_at/asof_ts_ms/asof_iso bleiben)

Backward compatibility impact:
- Alte Snapshots bleiben lesbar; neue Felder optional.
- Dataset Exporter behandelt fehlendes meta.btc_regime als null.

## Implementation Notes (optional but useful)
- btc_regime wird in run_pipeline(...) bereits berechnet. Übergabe an create_snapshot(...) erweitern: metadata dict enthält btc_regime (oder separater param).
- snapshot.py: meta.version von "1.0" → "1.1". (Nicht dynamisch, hart codiert.)
- Ensure: meta.asof_ts_ms und meta.asof_iso werden weiterhin gesetzt, auch wenn metadata übergeben wird.

## Acceptance Criteria (deterministic)
1) Neue Snapshots enthalten `meta.btc_regime` und `meta.version == "1.1"`.
2) Der Inhalt von `meta.btc_regime` entspricht exakt dem Objekt, das in run_pipeline(...) berechnet wurde (kein Recompute, keine Heuristik).
3) Alte Snapshot-Felder bleiben unverändert.
4) CI/pytest grün.

## Tests (required if logic changes)
- Unit:
  - Teste SnapshotManager.create_snapshot(...) mit metadata inkl. btc_regime: gespeicherte JSON enthält meta.btc_regime.
  - Teste meta.version == "1.1".
- Integration (light):
  - Pipeline-run (fast mode) erzeugt Snapshot; Snapshot enthält meta.btc_regime.

## Constraints / Invariants (must not change)
- Deterministisches Snapshot-Format (json dump stable, ensure_ascii False ok)
- Closed-candle-only bleibt unberührt
- Keine zusätzlichen API Calls für Snapshot write (nur Persistenz)

## Definition of Done (Codex must satisfy)
(Reference: docs/canonical/WORKFLOW_CODEX.md)
- [ ] Implementiert gemäß Acceptance Criteria
- [ ] Tests hinzugefügt/angepasst
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
