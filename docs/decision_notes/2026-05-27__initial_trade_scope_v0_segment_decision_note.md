# Initial Trade Scope v0 — Segment Decision Note

**Status:** Decision note / empirical guidance  
**Status:** Not a scanner-spec change  
**Status:** Not an automated live-trading rule  
**Date:** 2026-05-27  
**Project:** Independence — Spot Altcoin Scanner  
**Source analysis:** BACKTEST-2 Actionable Segment Report  
**Analysis ID:** `BACKTEST-2_ACTIONABLE_SEGMENT_REPORT`  
**Replay ID:** `2026-05-24T21-27-31Z`  
**Scenario:** `hsq_replay_2025_05_to_2026_05_v1`

---

## 1. Purpose

This note documents the current segment-level trading hypothesis after BACKTEST-2.

It does **not** modify scanner logic, v2.1 bucket semantics, entry-pattern rules, execution logic, ranking logic, or live-trading automation.

The purpose is to preserve the decision context for the next phase:

- defining a narrow initial trade-scope hypothesis,
- separating primary entry segments from secondary/observe segments,
- keeping `late_monitor` as a separate diagnostic research path,
- and explicitly linking the segment decision to the need for a valid exit framework.

---

## 2. Method Boundary

BACKTEST-2 is an empirical segment analysis, not a full trading simulation.

Not included:

```text
MEXC orderbook depth
spread
slippage
fees
real execution sizing
point-in-time MarketCap
live order feasibility
exit logic
```

Included:

```text
historical signal bucket
entry_pattern
forward returns at 1d / 3d / 5d / 10d / 20d
BTC regime annotation
quote-volume bucket annotation
sample warnings
```

Forward returns are labels, not signal inputs.

Quote-volume is an OHLCV-derived liquidity proxy, not a substitute for real execution validation.

---

## 3. Core Finding

BACKTEST-2 confirms the original strategic intent of the scanner:

```text
The scanner is primarily a short-term setup finder.
The strongest observed edge is in the 1d–3d window.
5d is a useful stretch / decay horizon.
10d–20d are not suitable as blind-hold target windows without active exit logic.
```

This supports the working assumption that the scanner can identify coins with short-term upside potential, but it also confirms that a separate and robust exit logic is mandatory before real trading is enabled.

---

## 4. BACKTEST-2 Summary

BACKTEST-2 processed:

```text
input_rows: 1523
primary_actionable_rows: 163
diagnostic_rows: 353
overall_segment_rows: 34
split_rows: 333
```

Classification counts:

```text
Tier A:        4
Tier B:        1
Exclude:       11
Diagnostic:    18
Unclassified:  0
```

---

## 5. Formal Tier-A Output

BACKTEST-2 classified the following segments as Tier A:

| Segment | Count | 1d Median | 3d Median | 5d Median | Report Classification |
|---|---:|---:|---:|---:|---|
| `confirmed_candidates × ema_reclaim` | 17 | +6.55% | +8.17% | +6.22% | Tier A |
| `early_candidates × early_reversal_break` | 17 | +5.79% | +5.27% | +2.74% | Tier A |
| `early_candidates × base_reclaim` | 62 | +5.27% | +3.24% | +2.02% | Tier A |
| `confirmed_candidates × early_reversal_break` | 18 | +4.62% | +1.84% | +0.50% | Tier A |

Important interpretation:

`confirmed_candidates × early_reversal_break` is formally Tier A under the deterministic BACKTEST-2 thresholds, but it is not treated as equal-quality Tier A for initial trade-scope purposes because its 3d and 5d continuation metrics are weaker and closer to threshold.

---

## 6. Formal Tier-B Output

BACKTEST-2 classified the following segment as Tier B:

| Segment | Count | 1d Median | 3d Median | 5d Median | Report Classification |
|---|---:|---:|---:|---:|---|
| `confirmed_candidates × base_reclaim` | 12 | +1.57% | +1.13% | +0.87% | Tier B |

This segment remains useful as a secondary / observe candidate, but the sample is small and the return profile is weaker than the core Tier-A candidates.

---

## 7. Initial Trade Scope v0

The current recommended initial trade-scope hypothesis is:

```text
Primary Trade Scope v0:
1. early_candidates × base_reclaim
2. confirmed_candidates × ema_reclaim
3. early_candidates × early_reversal_break
```

Rationale:

### `early_candidates × base_reclaim`

- Best sample size among the primary candidates.
- Positive 1d / 3d / 5d median returns.
- No sample warning.
- Strongest candidate for the initial real-trade segment set.

### `confirmed_candidates × ema_reclaim`

- Strongest 1d / 3d / 5d return profile.
- Sample size is only 17, so this requires sample-warning awareness.
- Suitable for initial scope only with conservative sizing and strict exit discipline.

### `early_candidates × early_reversal_break`

- Strong 1d / 3d return profile.
- Higher-risk early reversal setup type.
- Lower median quote-volume proxy than some other Tier-A segments.
- Requires particular attention to execution quality and position sizing.

---

## 8. Secondary / Observe Segments

The following segments should not be part of the primary initial trade scope yet, but should remain under observation:

```text
confirmed_candidates × base_reclaim
confirmed_candidates × early_reversal_break
```

### `confirmed_candidates × base_reclaim`

- Formal Tier B.
- Positive but weaker 1d / 3d / 5d profile.
- Low sample count.
- Possible future secondary candidate.

### `confirmed_candidates × early_reversal_break`

- Formal Tier A by thresholds.
- Qualitatively downgraded to Tier B+ / Watch.
- 3d and 5d continuation are materially weaker than the three preferred Tier-A candidates.
- Should not be treated as equal to the primary Tier-A group without more evidence.

---

## 9. Late Monitor Interpretation

`late_monitor` remains diagnostic and is not promoted to initial entry scope.

However, BACKTEST-2 showed that some `late_monitor` combinations remain empirically interesting:

| Segment | Count | 1d Median | 3d Median | 5d Median | Classification |
|---|---:|---:|---:|---:|---|
| `late_monitor × base_reclaim` | 52 | +5.72% | +4.79% | +1.67% | Diagnostic |
| `late_monitor × early_reversal_break` | 36 | +5.37% | +2.33% | +0.92% | Diagnostic |
| `late_monitor × range_reclaim` | 13 | +4.32% | +4.08% | +1.09% | Diagnostic |

Interpretation:

```text
late_monitor is not automatically bad.
late_monitor may represent momentum that continues after the ideal fresh-entry window.
But late_monitor is likely more exit-sensitive and more vulnerable to sudden reversals.
```

Therefore:

```text
Do not promote late_monitor into the initial trade scope.
Create or plan a separate Late Momentum / Late Threshold analysis later.
```

This separate analysis should answer:

- Which late setups continue despite being late?
- Which late setups are genuinely chased?
- Which late setups only work in Bull conditions?
- Which need tighter exits?
- Whether late/chased thresholds should be recalibrated.

---

## 10. Segments Not Prioritized for Initial Trading

The following should not be treated as initial tradeable segments based on BACKTEST-2:

```text
entry_pattern = none
watchlist
discarded
low-count Exclude segments
early_candidates × ema_reclaim
early_candidates × range_reclaim
early_candidates × resume_reclaim
early_candidates × shallow_pullback
```

Low-count segments with strong-looking returns are not promoted because their empirical support is insufficient.

---

## 11. Execution and Entry-Location Gates Still Required

Even if a segment is part of Primary Trade Scope v0, a concrete coin should not be treated as tradeable unless additional live-run gates pass.

Required later decision stack:

```text
segment allowed
AND current bucket / pattern still valid
AND execution quality acceptable
AND position-size class acceptable
AND entry-location / chase-risk acceptable
AND tokenized-stock / ETF exclusions respected
AND exit framework defined
```

Minimum operational constraints expected before real trading:

```text
execution_status_raw != fail
execution_size_class not worse than the agreed minimum
no severe low-depth / extreme-low-depth condition
not tokenized_stock_or_etf
entry location not avoid_chasing
position size reduced for initial deployment
```

Exact thresholds for live trading remain outside this note.

---

## 12. Exit Logic Implication

The strongest empirical edge is concentrated in the 1d–3d window.

Therefore, the scanner should be treated as a short-term entry/setup finder, not a blind long-hold signal.

A valid exit framework is required before any real trade deployment. It should address at least:

```text
time stop
profit-taking logic
momentum continuation handling
failure / invalidation exit
late-monitor-specific tighter exit behavior
maximum hold assumptions
```

5d should be treated as a stretch / decay horizon, not the main target holding period.

10d and 20d should not be used as primary hold targets without active exit logic.

---

## 13. Current Decision

Current decision:

```text
Proceed with Primary Trade Scope v0 as a documented hypothesis:
- early_candidates × base_reclaim
- confirmed_candidates × ema_reclaim
- early_candidates × early_reversal_break
```

Do not yet implement this as a live trading rule.

Next recommended workstreams:

```text
1. Exit logic design.
2. Execution / entry-location gate definition for the initial real-trade scope.
3. Later separate Late Momentum / late_monitor threshold analysis.
```

---

## 14. Decision Status

This decision note should be treated as:

```text
empirical guidance from BACKTEST-2
preliminary trading-scope hypothesis
not canonical v2.1 specification
not scanner behavior change
not automated trading permission
```
