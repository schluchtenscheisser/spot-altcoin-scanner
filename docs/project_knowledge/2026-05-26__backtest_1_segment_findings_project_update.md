# Project Knowledge Update — Backtest-1 Segment Findings

## Status

**Status:** Empirical observation from Backtest-1  
**Status:** Preliminary decision support  
**Status:** Not a canonical specification change  
**Status:** Requires confirmation with future replay/backtest runs  

**Scenario:** `hsq_replay_2025_05_to_2026_05_v1`  
**Replay ID:** `2026-05-24T21-27-31Z`  
**Primary analysis scope:** `included_in_primary_analysis = true AND included_in_signal_analysis = true`  
**Primary signal event count:** 516  

---

## Core Finding

The first validated Backtest-1 primary-signal analysis suggests that the scanner has a clear short-horizon edge in selected bucket × entry-pattern combinations.

The edge is strongest over **1d–3d**, remains useful in some cases over **5d**, and becomes much less stable over **10d–20d** without exit logic.

This supports the working assumption that exit logic is central and that blind long holding is not the correct evaluation frame for the current scanner output.

---

## Preliminary Tier A Segment Hypotheses

Prioritize these for follow-up validation:

```text
early_candidates × base_reclaim
confirmed_candidates × ema_reclaim
early_candidates × early_reversal_break
```

Rationale:
- Positive 1d/3d/5d means and medians
- High 1d and 3d win rates
- Concrete entry pattern present
- Not only driven by the May 2025 boundary month
- Not solely microcap-driven based on quote-volume proxies

---

## Tier B / Observe

```text
confirmed_candidates × base_reclaim
```

Rationale:
- Positive but weaker than Tier A
- Smaller sample
- May still be useful as secondary or lower-priority setup

---

## Do Not Prioritize Initially

Avoid treating the following as initial tradeable segments based on this run:

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

Notes:
- `late_monitor` showed some positive short-horizon behavior in subsegments, especially in Bull conditions, but should remain diagnostic for now.
- Positive `late_monitor` behavior may indicate that late/chased thresholds need future review, not that late entries should be immediately enabled.

---

## Important Method Constraints

This Backtest-1 result is not an execution-quality validation.

Not included:
```text
MEXC orderbook depth
spread
slippage
fees
real execution sizing
current or historical MarketCap
```

Included as proxy:
```text
signal_day_quote_volume
median_quote_volume_30d
median_quote_volume_90d
quote_volume_bucket
```

Quote-volume is an OHLCV-derived proxy, not a substitute for real execution analysis.

---

## Data Handling Decisions

Primary signal analysis uses:
```text
included_in_primary_analysis = true
included_in_signal_analysis = true
```

This means:
- May 2025 boundary/warm-up month is excluded from the primary analysis.
- Duplicate raw transition events are removed from signal-quality counts.
- `first_confirmed_ready` remains as raw diagnostic event but is not double-counted when `first_confirmed_with_entry_pattern` exists.

---

## Follow-Up Actions

1. Create BACKTEST-2 / Actionable Segment Report.
2. Keep findings as empirical guidance, not as scanner-spec changes.
3. Use Tier A segments as the first candidate set for deeper validation.
4. Revisit late/chased treatment later, but do not promote it to initial tradeable scope based only on this run.
5. Rerun full replay later after the analysis pipeline and reporting are stable.
