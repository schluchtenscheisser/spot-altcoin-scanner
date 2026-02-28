> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## 2026-02-27__05_P1__backfill_tools_atomicity_time_sources_snapshot_path.md

### Title
[P1] Backfill Tools: btc_regime unknown bei fehlenden BTC-features, strict-missing atomar, full-mode time sources, snapshot_dir fallback

### Context / Problem
Codex meldet Tool-Robustheitsprobleme:
- Backfill btc_regime schreibt default RISK_OFF, wenn BTC-features fehlen → Bias. fileciteturn1file0
- `--strict-missing` failt erst nach teilweisen Änderungen → nicht atomar. fileciteturn1file0
- Full-mode backfill patched nur utc_now, aber cache/time utils nutzen echte wall-clock → historische Snapshots können mit heutigem Cache/State gefüllt werden. fileciteturn1file0
- Tools respektieren `snapshot_dir` fallback nicht, schreiben ggf. in falsches Verzeichnis. fileciteturn1file0

### Goal
Backfill Tools sollen deterministisch, atomar in strict mode und pfad-korrekt sein.

### Scope
- scanner/tools/backfill_btc_regime.py
- scanner/tools/backfill_snapshots.py
- ggf. scanner/pipeline/snapshot.py (path resolution helper) oder SnapshotManager API Nutzung
- tests:
  - tests/test_backfill_btc_regime.py
  - tests/test_backfill_snapshots.py

### Out of Scope
- Exporter/E2 changes (separate Tickets)

### Implementation Requirements
1) **btc_regime Backfill: unknown statt RISK_OFF**
   - Wenn `snapshot.data.features.BTCUSDT.1d` (oder die erwartete BTC-feature Reihe) fehlt:
     - Tool darf **kein** Regime konstruieren.
     - Stattdessen:
       - entweder: `meta.btc_regime = null` (und optional `meta.btc_regime_status="missing_btc_features"`)
       - oder: Field nicht setzen (aber dann bleibt Snapshot version evtl. <1.1; bevorzugt: setze null + bump version)
   - Diese Semantik muss in Tool-Hilfe + Tests abgebildet werden.

2) **strict-missing atomar**
   - In strict mode muss der Tool-Lauf vor jeder Mutation einen Preflight machen:
     - Liste aller Dates im Range
     - Prüfe Existenz aller notwendigen Files (oder Quellen)
     - Wenn ein Problem: exit non-zero **ohne Änderungen**
   - Für non-strict bleibt “best effort”.

3) **full-mode time sources**
   - Full-mode muss alle relevanten Zeitquellen patchen:
     - scanner.pipeline.utc_now
     - scanner.utils.time_utils.utc_date
     - ggf. timestamp_to_ms / utc_timestamp wenn genutzt
   - Zusätzlich: Cache-Namespace muss auf das Ziel-Datum zeigen:
     - entweder: disable cache in full-mode
     - oder: monkeypatch get_cache_path so, dass es das Ziel-Datum nutzt
   - Ergebnis: full-mode darf nicht “heutige” Daten in “gestern”-Snapshot schreiben.

4) **snapshot_dir fallback**
   - Tools dürfen History-Pfad nicht hart auf `snapshots/history` festnageln.
   - Pfadauflösung:
     - wenn config `snapshots.history_dir` existiert → nutze den
     - else wenn config `snapshots.snapshot_dir` existiert → nutze `<snapshot_dir>/history` oder die vom SnapshotManager verwendete Struktur
     - else default wie bisher
   - Implementiere eine gemeinsame helper-Funktion (preferably in SnapshotManager), die Tools nutzen.

### Acceptance Criteria
- Backfill btc_regime:
  - fehlende BTC-features → `meta.btc_regime` bleibt null/unknown (kein RISK_OFF default)
- strict-missing:
  - fehlende Datei im Range → tool exits non-zero, **keine Datei verändert**
- full-mode:
  - tests/fixtures beweisen, dass cache paths nicht das aktuelle Datum benutzen (z. B. indem ein “heute” marker nicht im Snapshot landet)
- snapshot_dir fallback:
  - tool schreibt/liest in konfigurierten snapshot location

### Definition of Done
- [ ] Code + Tests umgesetzt
- [ ] pytest -q grün
- [ ] 1 PR

---
