# FEAT_ATR_WILDER — Average True Range (Wilder) (Canonical)

## Machine Header (YAML)
```yaml
id: FEAT_ATR_WILDER
status: canonical
indexing: "0-based"
inputs:
  - source: OHLCV
    field: high
    unit: price
  - source: OHLCV
    field: low
    unit: price
  - source: OHLCV
    field: close
    unit: price
parameters:
  - key: features.atr_period
    default: 14
    unit: bars
outputs:
  - key: atr_<tf>
    unit: price
  - key: atr_pct_<tf>
    unit: percent
determinism:
  closed_candle_only: true
nan_policy:
  propagate: true
```

## True Range (TR)
Using 0-based indexing:
- `TR[0]` is undefined (no `prev_close`).
- For `t >= 1`:
  - `TR[t] = max(high[t]-low[t], abs(high[t]-close[t-1]), abs(low[t]-close[t-1]))`

## ATR seed & Wilder smoothing (period = n)
Let `n = 14` (default).

- For `t < n`: `ATR[t] = NaN`
- Seed:
  - `ATR[n] = mean(TR[1..n])`  (indices 1..14 inclusive, 14 values)
- Smoothing:
  - for `t > n`:
    - `ATR[t] = (ATR[t-1]*(n-1) + TR[t]) / n`

## ATR%
- `ATR_pct[t] = ATR[t] / close[t] * 100` (if close[t] > 0 else NaN)

## NaN policy (canonical)
- If any required input is NaN, ATR/ATR_pct becomes NaN at that index and propagates (no skipping).
