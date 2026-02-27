> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## 2026-02-27__02_P0__evaluation_dataset_run_id_and_hits_consistency.md

### Title
[P0] Evaluation Dataset: run_id file-scope, record_id konsistent, keine Hit-Coercion, Schema-Nullability

### Context / Problem
Codex meldet Dataset/Exporter Korrektheitsprobleme:
- `run_id` darf nicht pro Snapshot-Row aus `snapshot.meta.asof_iso` abgeleitet werden, wenn eine JSONL mehrere Snapshots aggregiert. fileciteturn1file0
- `hit_*` Felder dürfen bei unevaluable E2 nicht als `false` erzwungen werden (Exporter coerced None → False). fileciteturn1file0
- Spec/Schema widerspricht nullable Hits. fileciteturn1file0

### Goal
Exporter + Canonical Dataset Spec so korrigieren, dass:
- Ein JSONL-Export **genau ein** `run_id` (file-scope) hat.
- Alle Rows nutzen denselben `run_id`, damit `record_id` stabil ist.
- `hit_*`/`hits` werden **nie** von None auf False coerced.
- Canonical Dataset Spec markiert Hit-Felder als nullable.

### Scope
- docs/canonical/OUTPUTS/EVALUATION_DATASET.md
- scanner/tools/export_evaluation_dataset.py
- tests/test_export_evaluation_dataset.py (golden output)

### Out of Scope
- E2 Model intern (Ticket 01)
- Backfill Tools (Ticket 05)

### Required Spec Decisions (fix, no ambiguity)
- `run_id` Bestimmung (Default):
  1) wenn CLI `--run-id` gesetzt → verwenden
  2) sonst: aus **Exportzeit** (UTC now) erzeugen: `YYYY-MM-DD_HHMMZ`
     - (Nicht aus Snapshot-asof ableiten)
- JSONL Meta-Record enthält zusätzlich:
  - `export_run_id` (= run_id)
  - `source_snapshot_count`
  - `source_snapshot_dates` optional (oder min/max + count)

### Implementation Requirements
- In Exporter:
  - `run_id` einmalig beim Start ermitteln (oder aus CLI).
  - Meta-record uses same run_id.
  - Candidate rows use the same run_id; `record_id` basiert darauf.
  - Entferne jede `bool(hit_value)`-Logik; schreibe `None` als `null`.

### Acceptance Criteria
- Canonical Dataset Doc:
  - run_id ist file-scope, nicht snapshot-scope.
  - hit_10/hit_20/hits sind nullable.
- Golden test:
  - Ein Export über mehrere Tage produziert ein File mit **konstantem** run_id über alle Zeilen.
  - Fälle mit insufficient_forward_history enthalten `"hit_10": null` (nicht false).

### Definition of Done
- [ ] Docs + Code + Tests umgesetzt
- [ ] pytest -q grün
- [ ] 1 PR für dieses Ticket
