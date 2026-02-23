# FEAT_BB_WIDTH_4H_RANK_120 — Bollinger Width% + Rank (4H)

## Machine Header (YAML)
```yaml
id: FEAT_BB_WIDTH_4H_RANK_120
status: canonical
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

## Rank (lookback 120)
Let `t4h` be last closed 4H index.
- Window = `bb_width_pct_4h[t4h-119 .. t4h]` (120 values)
- `bb_width_rank_120_4h = percent_rank(window, current=bb_width_pct_4h[t4h])`

## Edge cases
- If window incomplete or bb_width_pct contains NaN => rank is NaN (exclude from population for percent_rank).
