# Backtest-1 Findings — Primary Signal Segment Analysis

## Status

**Status:** Empirical Backtest-1 result report  
**Scenario:** `hsq_replay_2025_05_to_2026_05_v1`  
**Replay ID:** `2026-05-24T21-27-31Z`  
**Dataset:** `enriched_replay_events.parquet` from BACKTEST-MERGE-1  
**Analysis scope:** `primary_signal`  
**Scope filter:** `included_in_primary_analysis = true AND included_in_signal_analysis = true`  
**Generated from discussion date:** 2026-05-26  

This report summarizes the first validated Backtest-1 segment analysis for the historical replay dataset.

This is **not** a trading-strategy P&L simulation. Forward returns are evaluation labels, not signal inputs. Execution, MEXC orderbook depth, slippage, fees, and point-in-time MarketCap are not included.

---

## 1. Data Basis

The validated BACKTEST-MERGE-1 dataset contains:

| Metric | Count |
|---|---:|
| Raw replay events | 1,523 |
| Signal-analysis events after deduplication | 1,328 |
| Primary raw events after excluding May 2025 boundary month | 574 |
| Primary signal events after both filters | 516 |
| Duplicate signal events removed from signal-analysis scope | 195 |

All duplicate signal events were `first_confirmed_ready` rows that duplicated an equivalent `first_confirmed_with_entry_pattern` event for the same symbol/date/bucket group.

Primary analysis excludes May 2025 because the May event cluster was identified as a boundary / warm-up diagnostic month. The May cold-start diagnostic showed no difference between cold-start and state-preroll for May 2025, but May still dominates raw event count and should not drive first-pass segment selection.

---

## 2. Global Primary-Signal Forward Return Shape

Across the deduplicated primary signal set, the short-horizon profile was materially stronger than longer horizons.

| Horizon | Interpretation |
|---|---|
| 1d | Strongest and most consistent positive short-term response |
| 3d | Still clearly positive across strong segments |
| 5d | Often still positive, but weaker and more dispersed |
| 10d / 20d | Uneven; many medians flatten or turn negative |

Preliminary interpretation: the scanner appears to identify short-term momentum / reaction windows better than long blind-hold windows. Exit logic is therefore likely important.

---

## 3. Actionable-Only Segment Analysis

Actionable-only filter used for this diagnostic view:

```text
included_in_primary_analysis = true
included_in_signal_analysis = true
historical_signal_bucket in {confirmed_candidates, early_candidates}
```

This leaves **163 actionable rows**.

### 3.1 Strongest Actionable Segments

| Segment | Count | 1d Mean | 1d Median | 1d Win | 3d Mean | 3d Median | 3d Win | 5d Mean | 5d Median | 5d Win | Median 30d Quote Volume |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `confirmed_candidates × ema_reclaim` | 17 | +9.79% | +6.55% | 88.2% | +11.66% | +8.17% | 70.6% | +9.65% | +6.22% | 58.8% | 3.66M |
| `early_candidates × base_reclaim` | 62 | +7.28% | +5.27% | 91.9% | +6.47% | +3.24% | 71.0% | +5.47% | +2.02% | 56.5% | 1.77M |
| `early_candidates × early_reversal_break` | 17 | +6.95% | +5.79% | 94.1% | +5.92% | +5.27% | 76.5% | +4.01% | +2.74% | 70.6% | 0.88M |
| `confirmed_candidates × base_reclaim` | 12 | +3.03% | +1.57% | 91.7% | +3.39% | +1.13% | 66.7% | +3.52% | +0.87% | 50.0% | 2.25M |

### 3.2 Actionable Segments That Should Not Be Prioritized Yet

| Segment | Count | Reason |
|---|---:|---|
| `early_candidates × resume_reclaim` | 6 | Small sample; 3d median negative |
| `confirmed_candidates × early_reversal_break` | 18 | Positive 1d but weak 3d/5d continuation |
| `early_candidates × ema_reclaim` | 6 | Weak 3d/5d; small sample |
| `early_candidates × range_reclaim` | 6 | Weak 3d/5d; small sample |

---

## 4. Broader Segment Observations

### 4.1 Entry Pattern Matters

`entry_pattern = none` was consistently weaker in prior segment views. The first actionable-only pass supports focusing on concrete entry-pattern combinations rather than bucket/state alone.

### 4.2 Transition Reclaim Is a Strong Phase

The broader Backtest-1 segment output showed `transition_reclaim` as a large and consistently positive market-phase block. Its strongest combinations were with:

```text
transition_reclaim × ema_reclaim
transition_reclaim × base_reclaim
transition_reclaim × early_reversal_break
```

### 4.3 Bull Regime Supports Longer Continuation

BTC Bull-regime rows showed stronger 3d/5d continuation than Sideways in the segment output. Sideways still had short-term edge, but longer horizons weakened faster.

### 4.4 Late Monitor Requires Separate Treatment

Some `late_monitor` combinations, especially under Bull conditions or with concrete reclaim patterns, showed surprisingly positive short-horizon returns. This should **not** be treated as an immediate trading permission. It is a diagnostic signal that the `late/chased` thresholds may need later review or that continuation can persist in strong momentum regimes.

---

## 5. Preliminary Segment Prioritization

### Tier A — Candidate Initial Focus

These are the strongest current hypotheses for future validation:

```text
early_candidates × base_reclaim
confirmed_candidates × ema_reclaim
early_candidates × early_reversal_break
```

### Tier B — Observe / Secondary Candidate

```text
confirmed_candidates × base_reclaim
```

### Not Initial Priority

```text
entry_pattern = none
discarded
watchlist
late_monitor as direct entry segment
trend_resume × none
trend_resume × shallow_pullback
pressure_build × none
early_candidates × ema_reclaim
early_candidates × range_reclaim
early_candidates × resume_reclaim
confirmed_candidates × early_reversal_break
```

---

## 6. Methodological Limitations

1. **No execution layer**  
   The replay uses historical OHLCV only. It does not evaluate MEXC orderbook depth, spread, slippage, execution sizing, or real tradeability.

2. **No point-in-time MarketCap**  
   MarketCap is not included because current MarketCap would create lookahead bias. Quote-volume proxies are used instead.

3. **Small samples in several strong-looking segments**  
   `confirmed_candidates × ema_reclaim` and `early_candidates × early_reversal_break` each have only 17 actionable primary-signal rows. They are promising, not proven.

4. **Forward returns are blind-hold labels**  
   They do not include exit logic. The decay after 3d/5d suggests exit design will materially affect real strategy performance.

5. **May 2025 excluded from primary analysis**  
   May remains preserved in the dataset, but is excluded from the primary analysis because it is a boundary / warm-up diagnostic month.

---

## 7. Recommended Next Steps

1. Create BACKTEST-2 / Actionable Segment Report:
   - stable tier tables
   - count thresholds
   - 1d/3d/5d focus
   - BTC-regime split
   - quote-volume bucket split
   - warning segments

2. Do not immediately change live scanner rules from this single run.
   Treat findings as empirical decision support.

3. Later rerun full historical replay with current code after the analysis pipeline stabilizes.

4. After BACKTEST-2, use the findings to inform:
   - initial tradeable segment selection
   - exit-strategy work
   - potential refinement of late/chased rules
   - future T_EL2 / entry-location recalibration
