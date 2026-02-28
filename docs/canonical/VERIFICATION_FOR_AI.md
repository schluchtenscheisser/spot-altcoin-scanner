# Verification for AI — Golden Fixtures, Invariants, Checklist (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_VERIFICATION_FOR_AI
status: canonical
comparison:
  method: numeric_abs_tolerance
  abs_tolerance: 1e-9
```

## Comparison rule
Compare expected numeric values as floats with absolute tolerance 1e-9. No rounding.

## Fixture A trace (key point)
dist_pct=1.643406808 lies in [0,2):
breakout_distance_score = 30 + 40*(dist_pct/2) = 62.868136160

## E2 verification boundaries
- `invalid_entry_price` is evaluated only when `t_trigger` exists.
- For non-`ok` reasons (`no_trigger`, `insufficient_forward_history`, `missing_price_series`, `missing_trade_levels`, `invalid_trade_levels`, `invalid_entry_price`), E2 outcome fields remain nullable: `hit_10`, `hit_20`, `hits`, `mfe_pct`, `mae_pct`.
- Parameter alias checks:
  - `T_hold` / `t_hold` / `T_hold_days` / `t_hold_days` are equivalent.
  - `T_trigger_max` / `t_trigger_max` / `T_trigger_max_days` / `t_trigger_max_days` are equivalent.
  - conflicting alias values must raise `ValueError`.
- `thresholds_pct` parsing:
  - `null` or missing uses defaults `[10,20]`.
  - scalar input (e.g. `10` or `"10"`) raises `ValueError("thresholds_pct must be list-like or null")`.


## Breakout Trend 1-5D verification boundaries
- Trigger lookup window uses `trigger_4h_lookback_bars` (default 30), not a fixed 6-bar window.
- `_find_breakout_indices` returns `(first_breakout_idx, last_breakout_idx)` over the configured trigger window.
- In `RISK_OFF`, BTC multiplier never excludes candidates: `0.85` when `rs_override AND liq_ok`, otherwise `0.75`.
- `bb_width_rank_120_4h` is interpreted on percent scale `[0..100]`; defensive rank01 input (`<=1.0`) is multiplied by 100 before scoring.


## Execution gate verification boundaries
- Synthetic book test case: bids `[[99,10],[98,10]]`, asks `[[101,10],[102,10]]` gives `mid=100`, `spread_pct=2.0`, `depth_bid_1pct_usd=990`, `depth_ask_1pct_usd=1010`.
- Gate pass example: `max_spread_pct=2.5`, `min_depth_usd[1.0]=900`.
- Gate fail by spread: `max_spread_pct=1.0` => includes `SPREAD_TOO_WIDE`.
- Gate fail by depth: high min depth for 1.0 band => includes `DEPTH_TOO_LOW_1_0`.


## Runtime market meta verification boundaries
- `global_volume_24h_usd` is nullable and sourced from CMC `quote.USD.volume_24h`; missing value stays `null`.
- `turnover_24h` is `null` when `market_cap_usd` is missing or zero.
- `mexc_share_24h` is `null` when `global_volume_24h_usd` is missing or zero.


## Universe volume-gate verification boundaries
- Config defaults when keys are missing: `min_turnover_24h=0.03`, `min_mexc_quote_volume_24h_usdt=5_000_000`, `min_mexc_share_24h=0.01`.
- Legacy alias behavior: `universe_filters.volume.min_quote_volume_24h` aliases to `min_mexc_quote_volume_24h_usdt` only when the new key is absent; if both exist, new key wins.
- Primary path (turnover available): all three gates are required (turnover + mexc min volume + mexc share).
- Fallback path (turnover unavailable): require only mexc min volume; `mexc_share_24h` is not evaluated.
- Invalid per-symbol values (`NaN`, negative, non-castable) are rejected deterministically at liquidity gate stage.
