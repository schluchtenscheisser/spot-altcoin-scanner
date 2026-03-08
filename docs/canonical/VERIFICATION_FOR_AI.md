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


## Universe filter / soft-prior verification boundaries
- Hard pre-shortlist guardrail: `budget.pre_shortlist_market_cap_floor_usd` excludes symbols with `market_cap < floor`; default floor is `25_000_000` when key is missing.
- `budget.pre_shortlist_market_cap_floor_usd` invalid values (e.g. negative) must raise a clear validation error; no silent coercion.
- Safety/risk hard excludes remain deterministic and hard (`stable/wrapped/leveraged`, denylist, major unlock blockers).
- Legacy config defaults are still loaded for context fields: `min_turnover_24h=0.03`, `min_mexc_quote_volume_24h_usdt=5_000_000`, `min_mexc_share_24h=0.01`.
- Legacy alias behavior remains: `universe_filters.volume.min_quote_volume_24h` aliases to `min_mexc_quote_volume_24h_usdt` only when the new key is absent; if both exist, new key wins.
- Above the pre-shortlist floor, legacy market-cap/turnover/mexc-volume/mexc-share thresholds are soft-prior context only and do not hard-exclude symbols.


## Tradeability verification boundaries
- `tradeability_class` domain is exactly `{DIRECT_OK, TRANCHE_OK, MARGINAL, FAIL, UNKNOWN}` and `execution_mode` domain is `{direct, tranches, none}`.
- `DIRECT_OK` requires all of: 20k-slippage <= direct threshold, spread gate pass, depth gate pass.
- `TRANCHE_OK` requires not `DIRECT_OK`, 5k-slippage <= tranche threshold, and `notional_chunk_usdt * max_tranches >= notional_total_usdt`.
- `MARGINAL` is fully evaluated, never UNKNOWN, and always uses `execution_mode=none`.
- `UNKNOWN` must remain distinct from `FAIL`; required reason identities include `orderbook_data_missing`, `orderbook_data_stale`, `orderbook_not_in_budget`.
- Missing tradeability config keys use canonical defaults; invalid threshold ordering raises a clear validation error (no silent coercion).


## Phase-1 risk computation verification boundaries
- Risk fields `stop_price_initial`, `risk_pct_to_stop`, `rr_to_tp10`, `rr_to_tp20`, `risk_acceptable` are computed only when planned entry and ATR are valid positive numbers.
- Long-spot invariant is strict: if `stop_price_initial >= entry_price`, all risk fields remain nullable (`null`).
- Missing required risk inputs and invalid required risk inputs are both non-evaluable paths and must keep risk fields nullable (`null`) without coercion.
- `risk_acceptable` is threshold-driven and evaluated only when risk distance and `rr_to_tp10` are evaluable.


## Scorer V2 readiness verification boundaries
- All affected setup scorers emit `entry_ready`, `entry_readiness_reasons`, and deterministic `setup_subtype`.
- Breakout emits `breakout_confirmed`; pullback emits `rebound_confirmed` and `retest_reclaimed`; reversal emits `reclaim_confirmed` and `retest_reclaimed`.
- Reversal without confirmed reclaim is a hard non-entry-ready path: `entry_ready=false` and `entry_readiness_reasons=[retest_not_reclaimed]`.
- `entry_ready=false` requires at least one standardized readiness reason key.
- `entry_ready=true` requires `entry_readiness_reasons=[]`.
- Missing/invalid/non-finite scorer inputs must not produce a false-valid confirmation; confirmation fields stay `null` for non-evaluable paths.
- Invalidation anchor consistency: `invalidation_derivable=false => invalidation_anchor_price=null`; `invalidation_derivable=true` requires finite positive `invalidation_anchor_price`.


## Decision layer verification boundaries
- Decision domain is exactly `{ENTER, WAIT, NO_TRADE}` with exactly one status per candidate.
- `WAIT` is only allowed for fully evaluated candidates (`risk_acceptable=true` and `entry_ready` explicitly evaluated as bool).
- Non-evaluable risk (`risk_acceptable=null`) must produce `NO_TRADE` with `risk_data_insufficient`, never `WAIT`.
- In `RISK_OFF`, candidates in `[min_score_for_enter, min_score_for_enter + risk_off_enter_boost)` degrade from potential `ENTER` to `WAIT` with `btc_regime_caution` (not a hard block).
- Tradeability `UNKNOWN`/`FAIL` must be stopped before decision layer in pipeline integration; if evaluated defensively, they remain `NO_TRADE`.
