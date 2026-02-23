# FEAT_ATR_WILDER — Average True Range (Wilder)

## Machine Header (YAML)
```yaml
id: FEAT_ATR_WILDER
status: canonical
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
formula:
  tr: "max(high-low, abs(high-prev_close), abs(low-prev_close))"
  seed: "mean(TR[1..n])"
  smooth: "(ATR[t-1]*(n-1)+TR[t])/n"
```

## True Range
- `TR[t] = max(high[t]-low[t], abs(high[t]-close[t-1]), abs(low[t]-close[t-1]))`

## Seed & smoothing (Wilder)
- `ATR[n] = mean(TR[1..n])`
- `ATR[t] = (ATR[t-1]*(n-1) + TR[t]) / n`

## ATR%
- `ATR_pct[t] = ATR[t] / close[t] * 100`

## Edge cases
- `t=0` hat kein `prev_close`: TR[0] ist nicht definiert; canonical seed nutzt TR[1..n].
- Wenn close[t] <= 0: ATR_pct ist NaN.
