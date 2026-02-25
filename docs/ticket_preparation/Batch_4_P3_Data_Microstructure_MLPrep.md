# Batch 4 (P3) — Data/Microstructure Tiefe + ML-Vorbereitung

Reihenfolge (empfohlen): **P3-01 → P3-02 → P3-03 → P3-04**

---

## P3-01 — Multi-Snapshot Orderbook (stabilere Liquidity Metriken)

### Goal
Mehrere Orderbuch-Snapshots je Symbol ziehen und robuste Kennzahlen (median/p90) berechnen.

### Scope
- **Update:** `scanner/pipeline/liquidity.py`
- **Update:** `scanner/clients/mexc_client.py`
- **Update:** `config/config.yml`
- **Tests:** `tests/pipeline/test_liquidity_multisnapshot.py`

### Out of Scope
- Kein WebSocket-Streaming

### New Metrics (V1)
- `spread_bps_median`, `slippage_bps_median`
- `spread_bps_p90`, `slippage_bps_p90`
- `orderbook_snapshot_count`

### Acceptance Criteria
1. Snapshot count + delay sind konfigurierbar.
2. Backward compatible: fallback auf single snapshot.
3. Optional Re-Rank kann median statt single verwenden.
4. Tests prüfen Aggregation und deterministische Regeln.

---

## P3-02 — Event/Catalyst Framework (override-basiert, V1)

### Goal
Bestehende Unlock Overrides zu einem generischen Events-Framework ausbauen (hard exclude / penalty / tag-only).

### Scope
- **Neu:** `scanner/pipeline/events.py`
- **Update:** `scanner/pipeline/filters.py`
- **Neu/Migration:** `config/events_overrides.yaml` (Adapter für `unlock_overrides.yaml`)
- **Docs:** `docs/canonical/CONFIGURATION.md` (falls vorhanden), `DATA_SOURCES.md`
- **Tests:** `tests/pipeline/test_events.py`

### Out of Scope
- Keine externe Event-API Integration

### Event Types (V1)
- `major_unlock`, `minor_unlock`
- `listing`
- `delisting_risk`
- `suspension`

### Acceptance Criteria
1. Eventmodell unterstützt severity + time window + effect.
2. Events erscheinen im Output strukturiert.
3. Unlock-Logik bleibt kompatibel (Migration oder Adapter).

---

## P3-03 — Trainingsdatensatz-Export (tabellarisch) aus Snapshots + E2

### Goal
Exportiere leakagesicheren Datensatz (Features + Labels) für spätere ML-Modelle.

### Scope
- **Neu:** `scanner/ml/feature_registry.py`
- **Neu:** `scanner/ml/export_training_dataset.py`
- **Tests:** `tests/ml/test_export_training_dataset.py`

### Out of Scope
- Kein Training in diesem Ticket

### Output
- CSV/Parquet mit:
  - Features (1D/4H, Liquidity, Regime, Setup meta)
  - Labels (`hit_10_5d`, `hit_20_5d`, `mfe_pct`, `mae_pct`)
  - `run_date`, `asof_ts_ms` (für time-splits)

### Acceptance Criteria
1. Keine Zukunftslabels in Feature-Spalten.
2. Schema-Versionierung.
3. Export filterbar nach Date Range.

---

## P3-04 — Baseline ML Modell (offline) für `hit_10_5d`

### Goal
Trainiere ein Baseline-Modell (z. B. Gradient Boosting) offline und evaluiere gegen Rules-only.

### Scope
- **Neu:** `scanner/ml/train_baseline_gbm.py`
- **Neu:** `scanner/ml/evaluate_baseline.py`
- Optional Dependency: `scikit-learn` (oder `xgboost`/`lightgbm`) in `requirements-dev.txt`

### Out of Scope
- Keine Live-Integration
- Keine Auto-Execution

### Acceptance Criteria
1. Time-based split / walk-forward (kein random split).
2. Report enthält mindestens:
   - Precision@K
   - PR-AUC oder ROC-AUC (optional)
   - Brier Score / Calibration Data (optional)
3. Vergleich gegen Score-Baseline.

### Tests
- Smoke-Test (optional): Script runs end-to-end on small fixture.
