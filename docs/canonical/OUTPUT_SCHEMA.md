# Output Schema — JSON / Markdown / Excel (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OUTPUT_SCHEMA
status: canonical
schema_version: v1.9
meta_version: 1.9
outputs:
  - json
  - markdown
  - excel
limits:
  global_top_n_default: 20
manifest:
  config_hash_required: true
  config_version_optional: true
  asof_ts_ms_required: true
  asof_iso_utc_optional: true
trade_levels:
  status: canonical_output_only
  levels_timeframe_default_by_setup_id:
    breakout_immediate_1_5d: 4h
    breakout_retest_1_5d: 4h
  levels_timeframe_default_fallback: 4h
  atr_timeframe_rule: "atr_pct uses the same timeframe as levels_timeframe"
  rounding:
    mode: none
discovery:
  discovery_source_values:
    cmc_date_added: string
    first_seen_ts: string
    none: null
```

## 1) JSON output

### 1.1 Schema contract version (required)
- `schema_version` MUST be `v1.9`.
- `meta.version` MUST be `1.9`.

### 1.1 Run manifest (required)
Required:
- `commit_hash`
- `schema_version`
- `providers_used`
- `config_hash`
- `asof_ts_ms` (int, epoch ms UTC)

Optional:
- `config_version`
- `asof_iso_utc` (string, RFC3339 UTC)

### 1.2 Candidate row (required, minimal set)
- `symbol`, `setup_id`
- `base_score`, `final_score`, `global_score`
- Liquidity: `proxy_liquidity_score`, `quote_volume_24h_usd`, `spread_bps`, `slippage_bps`, `liquidity_grade`, `volume_source_used` (`mexc` | `global`)
- Execution gate (breakout trend rows): `execution_gate_pass`, `execution_gate_fail_reasons`, `spread_pct`, `depth_bid_0_5pct_usd`, `depth_ask_0_5pct_usd`, `depth_bid_1pct_usd`, `depth_ask_1pct_usd`, `orderbook_ok`
- `proxy_liquidity_score` is a percent-rank on scale `[0.0, 100.0]` (not rank01).
- Optional discovery: `discovery`, `age_days`, `discovery_source` ("cmc_date_added" | "first_seen_ts" | null)

### 1.2.1 Report-layer market activity fields (additive, nullable)
For JSON/Markdown/Excel reports, candidate rows MAY include the following additive fields:
- `global_volume_24h_usd` (number | null)
- `turnover_24h` (number | null)
- `mexc_share_24h` (number | null)

Rules:
- Missing value => MUST remain `null` in JSON and empty cell in Excel.
- Invalid report-layer numeric (`NaN`, negative, non-castable) => treat as `null` in report serialization.
- These fields are informational only and MUST NOT alter ranking/selection/scoring.

### 1.3 Ordering and limits
- Top-n inclusion: `SCORING/GLOBAL_RANKING_TOP20.md`
- Final ordering: `LIQUIDITY/RE_RANK_RULE.md`

## 2) Trade levels (informational output, deterministic)
If present:
- `levels_timeframe` default: per setup_id map; fallback `levels_timeframe_default_fallback`
- ATR% uses the same timeframe as levels_timeframe.
- No rounding (raw floats).
