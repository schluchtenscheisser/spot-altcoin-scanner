# FEAT_VOLUME_SPIKE — Quote Volume SMA & Spike Ratio (1D/4H)

## Machine Header (YAML)
```yaml
id: FEAT_VOLUME_SPIKE
status: canonical
inputs:
  - source: OHLCV
    field: quote_volume
    unit: quote_value
parameters:
  - key: features.volume_sma_periods.1d
    default: 20
    unit: bars
  - key: features.volume_sma_periods.4h
    default: 20
    unit: bars
rule:
  sma_excludes_current_closed_candle: true
outputs:
  - key: quote_volume_sma_<tf>
  - key: volume_quote_spike_<tf>
determinism:
  closed_candle_only: true
```

## SMA definition (exclude current)
For timeframe TF in {1d, 4h} and last-closed index t:
- `SMA_TF[t] = mean(quote_volume_TF[t-period .. t-1])`

## Spike ratio
- `spike_TF[t] = quote_volume_TF[t] / SMA_TF[t]`

## Edge cases
- If `t < period`: SMA is NaN -> spike is NaN.
- If SMA is 0: spike is NaN (avoid inf).
