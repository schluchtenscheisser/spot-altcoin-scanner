# FEAT_ATR_PCT_RANK_120_1D — ATR% Rolling Rank (Lookback 120, 1D) (Canonical)

## Machine Header (YAML)
```yaml
id: FEAT_ATR_PCT_RANK_120_1D
status: canonical
type: rolling_time_series_rank
inputs:
  - key: atr_pct_1d
parameters:
  - key: features.atr_pct_rank_lookback_1d
    default: 120
    unit: bars
outputs:
  - key: atr_pct_rank_120_1d
    unit: rank_0_1
determinism:
  closed_candle_only: true
  tie_handling: average_rank
  equality: ieee754_exact
nan_policy:
  population_excludes_nan: true
```

## Computation
Let `t1d` be the last closed 1D candle index.

- Window (120 values, includes last-closed):
  - `W = atr_pct_1d[t1d-119 .. t1d]`
- Current:
  - `x = atr_pct_1d[t1d]`

- `atr_pct_rank_120_1d = rolling_percent_rank(W, x)`

## Rolling percent-rank (time-series window) — canonical helper

This document uses **rolling_percent_rank** for *time-series* windows.

### Definition
Given a window of numeric values `W = [w1..wk]` (time-ordered) and a current value `x`:

1) Population:
- `P = [wi for wi in W if wi is not NaN]`
- `N = len(P)`
- If `N == 0`: result is NaN.

2) Tie handling (average-rank, canonical):
- `count_less  = |{p in P : p < x}|`
- `count_equal = |{p in P : p == x}|`
- `rank = (count_less + 0.5*count_equal) / N`  in `[0..1]`

3) Equality rule (canonical):
- Equality is **exact IEEE-754 float equality** on computed values (no rounding/quantization).

4) NaN policy (canonical):
- NaNs are excluded from the population P.
- If `x` itself is NaN: result is NaN.


## Important clarification
This is **NOT** the cross-sectional `percent_rank` defined in `FEATURES/FEAT_PERCENT_RANK.md`.
It is a *rolling/time-series* rank over a 120-bar window for a single symbol.

## Edge cases
- If insufficient history for full window: output is NaN.
- If `x` is NaN: output is NaN.
