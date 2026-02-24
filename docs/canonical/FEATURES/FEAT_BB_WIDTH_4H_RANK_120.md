# FEAT_BB_WIDTH_4H_RANK_120 — Bollinger Width% + Rolling Rank (4H) (Canonical)

## Machine Header (YAML)
```yaml
id: FEAT_BB_WIDTH_4H_RANK_120
status: canonical
type: rolling_time_series_rank
inputs:
  - source: OHLCV
    field: close
    unit: price
parameters:
  - key: features.bb.period
    default: 20
    unit: bars
  - key: features.bb.stddev
    default: 2.0
  - key: features.bb.rank_lookback_4h
    default: 120
    unit: bars
outputs:
  - key: bb_width_pct_4h
    unit: percent
  - key: bb_width_rank_120_4h
    unit: rank_0_1
determinism:
  closed_candle_only: true
  std_ddof: 0
  tie_handling: average_rank
  equality: ieee754_exact
nan_policy:
  population_excludes_nan: true
```

## Computation (per 4H candle t)
Let `period = 20`, `k = 2.0`.

For `t < period-1`: outputs are NaN.

For `t >= period-1`:
- `middle[t] = SMA(close[t-19 .. t])`
- `std[t] = STD(close[t-19 .. t], ddof=0)`
- `upper[t] = middle[t] + k*std[t]`
- `lower[t] = middle[t] - k*std[t]`
- `bb_width_pct_4h[t] = ((upper[t] - lower[t]) / middle[t]) * 100` if `middle[t] > 0` else NaN.

## Rolling rank (lookback 120)
Let `t4h` be the last closed 4H index.

- Window (120 values, includes last-closed):
  - `W = bb_width_pct_4h[t4h-119 .. t4h]`
- Current:
  - `x = bb_width_pct_4h[t4h]`

- `bb_width_rank_120_4h = rolling_percent_rank(W, x)`

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
This rolling rank is **NOT** the cross-sectional `percent_rank` defined in `FEATURES/FEAT_PERCENT_RANK.md`.

## Edge cases
- If window incomplete: output is NaN.
- If `x` is NaN: output is NaN.
