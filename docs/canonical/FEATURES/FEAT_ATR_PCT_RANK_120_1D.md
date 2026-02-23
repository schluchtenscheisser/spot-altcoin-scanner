# FEAT_ATR_PCT_RANK_120_1D — ATR% Rolling Rank (Lookback 120, 1D)

## Machine Header (YAML)
```yaml
id: FEAT_ATR_PCT_RANK_120_1D
status: canonical
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
```

## Computation
Let `t1d` be the last closed 1D candle index.
- Window = `atr_pct_1d[t1d-119 .. t1d]` (120 values, includes last-closed)
- `atr_pct_rank_120_1d = percent_rank(window, current=atr_pct_1d[t1d])`

## Edge cases
- If insufficient history for full window: output is NaN.
