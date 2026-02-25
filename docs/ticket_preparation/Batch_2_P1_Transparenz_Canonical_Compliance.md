# Batch 2 (P1) — Transparenz, Diagnostik, Canonical-Compliance

Reihenfolge (empfohlen): **P1-01 → P1-02 → P1-03 → P1-04**

---

## P1-01 — Explizite Setup-Validity Engine + Reason Codes (Breakout zuerst)

### Goal
Ersetze implizite `return []`-Ausschlüsse im Breakout-Scorer durch eine standardisierte Validity-Schicht mit Reason Codes.

### Scope
- **Neu:** `scanner/pipeline/setup_validity.py`
- **Update:** `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- **Tests:** `tests/pipeline/test_setup_validity_breakout.py`

### Out of Scope
- Noch keine vollständige Umstellung von `reversal`/`pullback` (kann später folgen)

### Canonical References
- `docs/canonical/PIPELINE.md` (Stage: setup_validity)

### Reason Codes (Minimum Set)
- `insufficient_history_1d`
- `insufficient_history_4h`
- `no_breakout_detected`
- `daily_trend_filter_failed`
- `atr_rank_too_high`
- `r7_non_positive`
- `overextended_dist_ema20`
- `btc_regime_filter_failed`

### Acceptance Criteria
1. Breakout-Scorer nutzt Validity-Funktionen und gibt bei Invalidität `invalid_reason_code` aus (mind. im Debug/Watchlist-Modus).
2. Normaler Top-Output enthält weiterhin nur valide Setups (kein Behavior Change außer zusätzliche Metadaten).
3. Tests prüfen mindestens 6 Reason Codes inkl. deterministischem Verhalten.

### Tests
- Unit: `tests/pipeline/test_setup_validity_breakout.py`

---

## P1-02 — Near-Miss Watchlist (knapp invalide, aber relevant)

### Goal
Erzeuge eine zusätzliche Watchlist für „near miss“-Setups (knapp am Trigger/Threshold vorbei), inkl. Grund und Distanz.

### Scope
- **Update:** `scanner/pipeline/output.py`
- **Update:** `scanner/pipeline/setup_validity.py`
- **Update:** `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- **Tests:** `tests/pipeline/test_near_miss_watchlist.py`

### Out of Scope
- Keine Intraday-Benachrichtigungen

### Canonical References
- `docs/canonical/PIPELINE.md` (invalid setups optional in watchlist)

### Definition (V1)
Near-Miss = invalid, aber mindestens eine Metrik ist innerhalb eines Toleranzbereichs:
- `volume_spike_shortfall`
- `breakout_distance_shortfall`
- `bb_rank_outside_by`

### Acceptance Criteria
1. JSON-Report enthält `watchlist_near_miss` (Top N).
2. Jeder Eintrag enthält `invalid_reason_code` + `near_miss_metric` + `near_miss_distance`.
3. Kein Einfluss auf `global_top20`.

### Tests
- Unit: `tests/pipeline/test_near_miss_watchlist.py`

---

## P1-03 — Implementation Deviations (Canonical vs Code) dokumentieren

### Goal
Bewusste Abweichungen zwischen Canonical Docs und Implementierung dokumentieren, damit spätere Änderungen/Validierung eindeutig sind.

### Scope
- **Neu:** `docs/canonical/IMPLEMENTATION_DEVIATIONS.md`
- **Update:** `docs/canonical/INDEX.md` (Link hinzufügen)

### Out of Scope
- Keine Code-Verhaltensänderung

### Canonical References
- `docs/canonical/PIPELINE.md`
- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`

### Must-Document (Minimum)
- Liquidity-Stage Reihenfolge (Code vs Canonical)
- Global Ranking Policy (Canonical phase1 vs Code multi-setup aggregation)

### Acceptance Criteria
1. Jede Abweichung enthält: canonical reference, code behavior, rationale, impact, planned resolution (yes/no).
2. Dokument ist in Canonical Index verlinkt.

---

## P1-04 — Canonical-Compliance Tests (kritische Regeln)

### Goal
Tests hinzufügen, die zentrale Canonical-Regeln absichern (Tie-breaks, Rounding, Determinismus).

### Scope
- **Neu:** `tests/canonical/test_slippage_rounding.py`
- **Neu:** `tests/canonical/test_liquidity_rerank_rule.py`
- **Neu:** `tests/canonical/test_global_ranking_dedup.py`
- Optional: `tests/canonical/test_closed_candle_policy.py`

### Out of Scope
- Keine Vollabdeckung aller Canonical-Dokumente

### Canonical References
- `docs/canonical/LIQUIDITY/SLIPPAGE_CALCULATION.md`
- `docs/canonical/LIQUIDITY/RE_RANK_RULE.md`
- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`
- `docs/canonical/DATA_SOURCES.md` (closed candle)

### Acceptance Criteria
1. Tests prüfen deterministische Sortierung und Tie-break.
2. Slippage/Spread rounding entspricht Canonical (half-even, 6 decimals).
3. Dedup + retest-preference entspricht Canonical.
4. Tests laufen in PR-CI.

### Tests
- Unit: `tests/canonical/*`
