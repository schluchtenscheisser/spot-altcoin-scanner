# Batch 1 (P0) — Messbarkeit + Zielkopplung + Trader-Briefing

Reihenfolge (empfohlen): **P0-01 → P0-02 → P0-03 → P0-04 → P0-05**

---

## P0-01 — Backtest-E2 als ausführbares Modul implementieren (analytics-only)

### Goal
Implementiere das Canonical-Backtestmodell **E2** als Python-Modul, um Setups deterministisch anhand von **+10% / +20%** Zielen zu evaluieren.

### Scope
- **Neu:** `scanner/backtest/e2_model.py`
- **Neu:** `scanner/backtest/__init__.py`
- **Optional CLI:** `scanner/backtest/run_e2.py`
- **Tests:** `tests/backtest/test_e2_model.py`

### Out of Scope
- Kein ML
- Keine Live-Ranking-Integration

### Canonical References
- `docs/canonical/BACKTEST/MODEL_E2.md`

### Implementation Notes
- Closed-candle-only, no-lookahead.
- Default-Parameter:
  - `T_trigger_max_days = 5`
  - `T_hold_days = 10`
  - `thresholds_pct = [10, 20]`
- Entry-Preis: `close[t_trigger]` (Canonical default).
- Output pro Setup-Instanz:
  - `t0`, `t_trigger`, `entry_price`
  - `hit_10`, `hit_20`
  - optional `mfe_pct`, `mae_pct`
  - `reason` ∈ `{ok, no_trigger, insufficient_forward_history}`

### Acceptance Criteria
1. Implementierung folgt Canonical exakt (Parameter/Definitionen).
2. Deterministische Ergebnisse (kein Random, feste Sortierung falls benötigt).
3. Unit-Tests decken mind. ab:
   - Trigger gefunden + hit_10 true / hit_20 false
   - kein Trigger im Fenster
   - unzureichender Forward-Horizont
4. Modul ist unabhängig vom Live-Scoring ausführbar.

### Tests
- Unit: `tests/backtest/test_e2_model.py`

---

## P0-02 — Snapshot → E2-Evaluation Pipeline (historisch)

### Goal
Lade `snapshots/history/*.json` und berechne E2-Labels/Stats pro Kandidat, um später Kalibrierung und Benchmarks zu bauen.

### Scope
- **Neu:** `scanner/analytics/io_snapshots.py`
- **Neu:** `scanner/analytics/e2_evaluate_snapshots.py`
- **Output:** `reports/analytics/` (oder `artifacts/analytics/`)
- **Tests:** `tests/analytics/test_e2_evaluate_snapshots.py`

### Out of Scope
- Keine GUI
- Keine Live-Integration in Ranking

### Canonical References
- `docs/canonical/BACKTEST/MODEL_E2.md`
- `docs/canonical/PIPELINE.md` (Snapshot-Stage)

### Implementation Notes
- Script verarbeitet mehrere Snapshots in einem Run (Datei-Glob + Date-Range Filter optional).
- Ergebnis deterministisch sortieren: `run_date`, `symbol`, `setup_id`.
- Robustness: kaputte/inkompatible Snapshots loggen und überspringen (nicht silent).

### Output (Minimum)
Zeilen pro Kandidat:
- `run_date`, `symbol`, `setup_id`
- `final_score`, `global_score` (falls vorhanden)
- `btc_regime_state` (falls vorhanden)
- `hit_10_1d`, `hit_10_3d`, `hit_10_5d`
- `hit_20_3d`, `hit_20_5d`
- optional `mfe_pct`, `mae_pct`, `reason`

### Acceptance Criteria
1. Lädt und verarbeitet mehrere Snapshot-Dateien in einem Lauf.
2. Fehlerhafte Snapshots werden sichtbar geloggt.
3. Output ist deterministisch sortiert.
4. Mindestens ein Test mit Mini-Fixture.

### Tests
- Unit: `tests/analytics/test_e2_evaluate_snapshots.py`

---

## P0-03 — Score-Kalibrierungstabellen aus E2-Ergebnissen

### Goal
Erzeuge Kalibrierungstabellen: **Score-Bins → empirische Trefferquote** für `hit_10_*` und `hit_20_*`, getrennt nach Setup-Typ (und optional Regime).

### Scope
- **Neu:** `scanner/analytics/calibration.py`
- **Neu:** `scanner/analytics/build_calibration_tables.py`
- **Output:** `artifacts/calibration/*.json`
- **Tests:** `tests/analytics/test_calibration.py`

### Out of Scope
- Kein ML
- Keine Live-Score-Änderungen

### Canonical References
- `docs/canonical/BACKTEST/MODEL_E2.md`

### Implementation Notes
- Binning z. B. 10er-Bins: `[0,10), [10,20), ... [90,100]`
- Kennzahlen pro Bin:
  - `count`
  - `hit_rate_10_5d`, `hit_rate_20_5d` (plus weitere Horizonte optional)
  - optional: `avg_mfe_pct`, `avg_mae_pct`
- Slices:
  - `setup_id`
  - optional `btc_regime_state`

### Acceptance Criteria
1. Script erzeugt JSON-Kalibrierungsartefakte aus E2-Evaluationsdaten.
2. Leere Bins sind stabil/definiert (z. B. `count=0`, hit_rate=None).
3. Schema-Versionierung für Kalibrierungsartefakte.
4. Tests prüfen Bin-Grenzen und Trefferquoten.

### Tests
- Unit: `tests/analytics/test_calibration.py`

---

## P0-04 — Daily Report um kalibrierte Wahrscheinlichkeiten erweitern

### Goal
Daily Output (JSON + Markdown + Excel) enthält **kalibrierte Wahrscheinlichkeiten** (Lookup via Score-Bins) je Top-Kandidat.

### Scope
- **Neu:** `scanner/analytics/calibration_runtime.py`
- **Update:** `scanner/pipeline/__init__.py` (Kalibrierung laden)
- **Update:** `scanner/pipeline/output.py` (Felder anzeigen)
- **Docs:** `docs/canonical/OUTPUT_SCHEMA.md` (falls vorhanden/benötigt)
- **Tests:** `tests/analytics/test_calibration_runtime.py`

### Out of Scope
- Kein ML
- Keine Garantieaussagen

### Canonical References
- `docs/canonical/OUTPUT_SCHEMA.md` (falls vorhanden)
- `docs/canonical/PIPELINE.md`

### New Fields (Minimum)
- `p_hit_10_5d_calibrated`
- `p_hit_20_5d_calibrated`
- `calibration_source`
- `calibration_sample_n`

### Acceptance Criteria
1. Wenn Kalibrierungsdateien fehlen: Run läuft weiter, `meta.degraded=true` + Reason.
2. JSON enthält neue Felder mindestens für `global_top20`.
3. Markdown zeigt Wahrscheinlichkeiten lesbar.
4. Tests decken Lookup und Fallback ab.

### Tests
- Unit: `tests/analytics/test_calibration_runtime.py`

---

## P0-05 — Standardisierte Trade-Plan-Felder im Output (Trader-Briefing)

### Goal
Erzeuge pro Top-Kandidat standardisierte Trade-Plan-Felder (Trigger, Entry-Zone, Invalidierung, SL, TP1/TP2, R:R).

### Scope
- **Neu:** `scanner/pipeline/trade_plan.py`
- **Update:** `scanner/pipeline/output.py`
- **Optional Update:** `scanner/pipeline/scoring/*.py` (Rohdaten ergänzen)
- **Tests:** `tests/pipeline/test_trade_plan.py`

### Out of Scope
- Keine Auto-Execution
- Keine Orderplatzierung

### Canonical References
- `docs/canonical/SCORING/*` (Setup-Definitionen)
- `docs/canonical/PIPELINE.md`

### Trade Plan Fields (Minimum)
- `trigger_price`
- `entry_zone_low`, `entry_zone_high`
- `invalidation_price`
- `stop_loss_price`
- `tp1_price`, `tp2_price`
- `risk_reward_tp1`, `risk_reward_tp2`
- `trade_plan_notes`

### Acceptance Criteria
1. Trade-Plan-Felder werden im JSON für `global_top20` erzeugt.
2. Markdown zeigt die Felder strukturiert.
3. Regeln unterscheiden mind. `breakout_immediate_1_5d` vs `breakout_retest_1_5d`.
4. Tests prüfen Preislogik + Missing-Data-Fallback.

### Tests
- Unit: `tests/pipeline/test_trade_plan.py`
