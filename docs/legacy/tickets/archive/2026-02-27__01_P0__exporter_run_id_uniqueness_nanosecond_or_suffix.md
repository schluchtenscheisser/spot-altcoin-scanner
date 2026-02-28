> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Evaluation Dataset Exporter: run_id standardmäßig eindeutig (keine Overwrites/Namespace-Kollisionen)

## Context / Problem
Codex-Kommentar: Deriving `run_id` from `exported_at_iso` at minute precision kann bei zwei Exports im selben Minutenfenster zu identischen `run_id`s führen → identischer Output-Dateiname `eval_{run_id}.jsonl` und identischer `record_id`-Namespace. Das überschreibt frühere Exporte und korruptiert Experiment-Outputs. fileciteturn2file0

## Goal
Sicherstellen, dass `run_id` **standardmäßig** pro Export-Job eindeutig ist (auch bei Start innerhalb derselben Minute), ohne dass Nutzer zwingend `--run-id` angeben müssen.

## Scope
- scanner/tools/export_evaluation_dataset.py
- docs/canonical/OUTPUTS/EVALUATION_DATASET.md (run_id Spezifikation)
- tests/test_export_evaluation_dataset.py

## Out of Scope
- E2 Model
- Snapshot/Backfill Tools

## Proposed Change (No-Guesswork)
### 1) run_id Format
Behalte das lesbare Format bei, erweitere aber um einen deterministischen, hochauflösenden Suffix:

- **Neues Default-Format:** `YYYY-MM-DD_HHMMSSZ` (Sekundenauflösung) **+** `_{ms}` (Millisekunden)  
  Beispiel: `2026-02-27_151233Z_482`

Regel:
- Wenn CLI `--run-id` gesetzt ist → **immer** verwenden.
- Sonst:
  - `export_started_at = utc_now()` (oder time_utils) exakt einmal beim Start
  - `run_id = export_started_at.strftime("%Y-%m-%d_%H%M%SZ") + "_" + f"{milliseconds:03d}"`

### 2) Record-ID Konsistenz
`record_id` bleibt unverändert: `"{run_id}:{t0_date}:{symbol}:{setup_type}:{setup_id}"`  
Nur `run_id` wird eindeutiger.

### 3) Meta-Record
Meta-Record enthält:
- `export_run_id` (= run_id)
- `export_started_at_iso` (RFC3339 UTC)
- optional `export_started_at_ts_ms` (int)

## Acceptance Criteria
1) Zwei Exporte, die innerhalb derselben Minute gestartet werden (ohne `--run-id`) erzeugen **unterschiedliche** Output-Dateien (unterschiedlicher run_id).
2) `record_id`-Namespace kollidiert nicht zwischen zwei Exports im selben Minutenfenster.
3) Canonical Doc beschreibt das neue run_id Default-Format eindeutig.
4) Tests:
   - Monkeypatch time source so, dass zwei Runs gleiche Minute aber verschiedene ms haben → unterschiedliche run_id.

## Implementation Notes
- Falls `utc_now()` keine ms liefert, nutze `datetime.now(timezone.utc)` und derive ms via `microsecond // 1000`.
- Vermeide Randomness; Ziel ist Determinismus pro Run-Startzeit.

## Definition of Done
- [ ] Docs + Code + Tests umgesetzt
- [ ] pytest -q grün
- [ ] 1 PR
