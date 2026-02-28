# Data Sources — Providers, Felder, As-Of & Closed-Candle Policy (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_DATA_SOURCES
status: canonical
policy:
  free_first: true
providers:
  - name: MEXC
    purpose:
      - universe_symbols
      - tickers_24h_quote_volume
      - ohlcv_1d
      - ohlcv_4h
      - orderbook_depth_topk
  - name: CoinMarketCap
    purpose:
      - market_cap_universe
      - metadata_date_added
      - asset_validation
run_modes:
  standard:
    cmc_required: true
    behavior_if_missing_cmc_key: "fail_run_with_error"
  fast:
    cmc_required: true
    behavior_if_missing_cmc_key: "fail_run_with_error"
  offline:
    cmc_required: false
    behavior: "use_cached_or_skip_market_cap_dependent_steps"
  backtest:
    cmc_required: false
    behavior: "use_snapshot_inputs"
asof_policy:
  closed_candle_only: true
  timestamp_unit: ms
  rule: "use only candles with closeTime_ms <= asof_ts_ms"
```

## As-Of & Closed-Candle Policy (milliseconds)
Canonical timestamps are epoch **milliseconds** UTC.

Provider raw field:
- `closeTime` MUST be interpreted as epoch milliseconds (UTC).
- If a provider returns seconds, it MUST be converted to ms before comparisons.

Rule:
- Only candles with `closeTime_ms <= asof_ts_ms` are valid for computation.

If `asof_ts_ms` is None:
- use the last available closed candle.

## Notes
- `quote_volume_24h_usd` treats USDT as USD for proxy/liquidity.

## Canonical 24h volume derivatives (nullable)
For each mapped symbol, CoinMarketCap `quote.USD.volume_24h` is the canonical source for:
- `global_volume_24h_usd` (number|null)

Derived fields (informational, deterministic):
- `turnover_24h = global_volume_24h_usd / market_cap_usd`
- `mexc_share_24h = mexc_quote_volume_24h_usdt / global_volume_24h_usd`

Nullability rules:
- If `global_volume_24h_usd` is missing/non-castable/`<= 0`, both `turnover_24h` and `mexc_share_24h` MUST be `null`.
- If `market_cap_usd` is missing/non-castable/`<= 0`, `turnover_24h` MUST be `null`.
- These values are report/runtime-meta fields and MUST NOT introduce implicit boolean coercion.
