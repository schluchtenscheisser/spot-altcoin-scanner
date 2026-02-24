# FEAT_EMA_STANDARD — Exponential Moving Average (Standard) (Canonical)

## Machine Header (YAML)
```yaml
id: FEAT_EMA_STANDARD
status: canonical
inputs:
  - source: OHLCV
    field: close
    unit: price
parameters:
  - key: features.ema_periods
    unit: bars
outputs:
  - key: ema_<n>_<tf>
    unit: price
determinism:
  closed_candle_only: true
  warmup:
    before_n_minus_1: NaN
    at_n_minus_1: SMA_seed
formula:
  alpha: "2/(n+1)"
nan_policy:
  propagate: true
```

## Definition
EMA ist standardisiert:
- `alpha = 2/(n+1)`
- Für `t < n-1`: `EMA[t] = NaN`
- Für `t = n-1`: `EMA[t] = SMA(close[0..n-1])`
- Für `t > n-1`: rekursiv

## Formula
- `EMA[t] = alpha*close[t] + (1-alpha)*EMA[t-1]`

## NaN policy (canonical)
- If any required input in the EMA recursion is NaN, EMA becomes NaN at that index and continues NaN propagation (no skipping, no forward-fill).
