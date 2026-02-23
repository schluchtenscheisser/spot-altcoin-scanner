# Discovery Tag — “New coin” identification (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_DISCOVERY_TAG
status: canonical
default_max_age_days: 180
primary_source: "CMC.date_added"
fallback_source: "first_seen_ts_from_ohlcv_1d"
determinism:
  closed_candle_only: true
```

## 0) Purpose
Discovery is an informational tag/bonus that indicates whether an asset is “new” within a defined age window. It must be deterministic.

## 1) Inputs
Primary (preferred):
- `date_added` from CoinMarketCap (CMC), if available and verified.

Fallback:
- `first_seen_ts`: earliest available 1D OHLCV candle timestamp in deterministic cache/fetch result.

## 2) Age computation
Let:
- `asof_ts` = as-of timestamp (run as-of, UTC)
- `date_added_ts` = CMC date_added timestamp (UTC)

If `date_added_ts` exists:
- `age_days = floor((asof_ts - date_added_ts) / 86400)`

Else:
- `age_days = floor((asof_ts - first_seen_ts) / 86400)`

## 3) Discovery decision
Let `max_age_days = 180` (default).

- `discovery = (age_days <= max_age_days)`

## 4) Output fields
Per symbol:
- `discovery` (bool)
- `age_days` (int, non-negative if as-of >= source timestamp)
- `discovery_source` in {"cmc_date_added", "ohlcv_first_seen"}

## 5) Determinism constraints
- `asof_ts` is canonical and fixed for the run.
- Fallback `first_seen_ts` must not depend on non-deterministic API ordering; it must be derived from the candle data itself.
- If both sources are missing, discovery must be `false` and source set to `"none"` (explicit).

## 6) Notes
Discovery must not silently influence scoring unless explicitly defined in a setup scorer document.
