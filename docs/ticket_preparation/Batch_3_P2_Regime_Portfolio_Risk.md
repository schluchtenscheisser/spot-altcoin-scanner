# Batch 3 (P2) — Regime, Ranking-Robustheit, Portfolio-Logik

Reihenfolge (empfohlen): **P2-01 → P2-02 → P2-03 → P2-04**

---

## P2-01 — Altcoin-Breadth-Regime ergänzen (zusätzlich zu BTC-Regime)

### Goal
Berechne eine Altcoin-Marktbreite (Breadth) über das eligible universe und gib sie im Report aus.

### Scope
- **Neu:** `scanner/pipeline/alt_breadth_regime.py`
- **Update:** `scanner/pipeline/__init__.py`
- **Update:** `scanner/pipeline/output.py`
- **Tests:** `tests/pipeline/test_alt_breadth_regime.py`

### Out of Scope
- Noch keine direkten Score-Änderungen (nur reporting + meta)

### Implementation Notes
V1 Metriken:
- `% close > EMA20 (1D)`
- `% EMA20 > EMA50 (1D)`
- median `r_7` (1D)
- state ∈ `{BROAD_RISK_ON, MIXED, BROAD_RISK_OFF}`

### Acceptance Criteria
1. Regime basiert auf eligible universe (nach hard gates).
2. JSON + Markdown zeigen Zustand + Metriken.
3. Deterministisch.

---

## P2-02 — Regime-gesteuerte Score-/Filter-Profile (konfigurierbar)

### Goal
Konfigurierbare Profile pro Regime, um Schwellenwerte (z. B. risk-off) zu verschärfen/lockern.

### Scope
- **Update:** `config/config.yml`
- **Neu:** `scanner/pipeline/regime_profiles.py`
- **Update:** `scanner/pipeline/scoring/breakout_trend_1_5d.py` (zuerst)
- Optional: `reversal.py`, `pullback.py`
- **Tests:** `tests/pipeline/test_regime_profiles.py`

### Out of Scope
- Keine ML-optimierten Profile

### Acceptance Criteria
1. Profile pro Regime (`RISK_ON`, `RISK_OFF`, optional `MIXED`) existieren.
2. Scorer nutzt Profile deterministisch.
3. Report markiert verwendetes Profil.

---

## P2-03 — Portfolio-Auswahlschicht nach Global Top (Diversifikation)

### Goal
Erzeuge zusätzlich zur Global Top20 eine deterministische Portfolio-Auswahl, die Klumpen reduziert.

### Scope
- **Neu:** `scanner/pipeline/portfolio_select.py`
- **Update:** `scanner/pipeline/__init__.py`
- **Update:** `scanner/pipeline/output.py`
- **Tests:** `tests/pipeline/test_portfolio_select.py`

### Out of Scope
- Keine Positionsgrößenoptimierung in diesem Ticket

### V1 Rules (deterministisch)
- max `N` Picks pro `best_setup_type`
- prefer low slippage when scores close
- optional einfache Korrelation-Proxy Regeln

### Acceptance Criteria
1. `global_top20` bleibt unverändert.
2. Zusätzlich `portfolio_candidates_v1` im Output.
3. Config-Flag zum Aktivieren/Deaktivieren.
4. Tests prüfen Determinismus + Limits.

---

## P2-04 — Advisory Risk Budget / Position Notional Vorschläge im Output

### Goal
Pro Kandidat advisory-only Vorschläge zur Positionsgröße basierend auf Volatilität/Liquidität.

### Scope
- **Neu:** `scanner/pipeline/risk_budget.py`
- **Update:** `scanner/pipeline/output.py`
- **Tests:** `tests/pipeline/test_risk_budget.py`

### Out of Scope
- Keine Auto-Execution

### V1 Fields
- `risk_bucket` ∈ `{small, medium, large}`
- `suggested_position_notional_usdt`
- `max_slippage_budget_bps`
- `position_size_rationale`

### Acceptance Criteria
1. Berechnung nutzt mindestens `ATR%`, `slippage_bps`, `liquidity_grade`.
2. Advisory-only Kennzeichnung im Report.
3. Fallback bei fehlenden Daten.
