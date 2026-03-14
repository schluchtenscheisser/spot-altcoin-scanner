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
- Exact threshold touch is inclusive for E2 hits (`max_high >= target` => hit=true).
- Non-finite OHLC values (`NaN`, `+inf`, `-inf`) are treated as non-evaluable inputs.
- Evaluation dataset Label-Export V2 fields (`hit5_5d`, `hit10_5d`, `hit20_5d`, `mfe_5d_pct`, `mae_5d_pct`) are recomputed with fixed `T_hold=5` and preserve nullability on non-`ok` reasons.


## Breakout Trend 1-5D verification boundaries
- Trigger lookup window uses `trigger_4h_lookback_bars` (default 30), not a fixed 6-bar window.
- `_find_breakout_indices` returns `(first_breakout_idx, last_breakout_idx)` over the configured trigger window.
- BTC regime state domain is exactly `{RISK_OFF, NEUTRAL, RISK_ON}` with deterministic parsing (`missing => NEUTRAL`, invalid => validation error).
- `bb_width_rank_120_4h` is interpreted on percent scale `[0..100]`; defensive rank01 input (`<=1.0`) is multiplied by 100 before scoring.
- Breakout calibration defaults are deterministic: `volume_score_min_spike=1.2`, `volume_score_full_spike=2.2`, weights `(distance,volume,trend,bb)=(0.40,0.30,0.20,0.10)`.
- Breakout multiplier floors are deterministic: anti-chase minimum `0.80`, overextension pre-hard-gate minimum `0.80`, BTC risk-off multipliers `{0.90, 0.80}`.
- Missing/non-finite breakout scoring inputs (`volume_quote_spike_*`, `dist_ema20_pct_1d`, `bb_width_rank_120_4h`, trigger close) are non-evaluable and must not emit breakout rows.
- Deterministic breakout row order is `(final_score desc, retest-first, symbol asc, setup_id asc)`.
- Fixed 2026-03-14 comparison set checks:
  - HYPEUSDT and C98USDT breakout immediate `final_score` increase vs stored fixture rows.
  - C98USDT remains `execution_gate_pass=false` in this fixture family.
  - JSTUSDT remains execution-gated (`execution_gate_pass=false`) despite score calibration.
  - KERNELUSDT, TAOUSDT, GRTUSDT, ALGOUSDT have no breakout-immediate rows in this fixture family; this absence is explicitly documented (no silent substitution).


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


## Entry timing verification boundaries
- `distance_to_entry_pct` uses `((current_price_usdt / entry_price_usdt) - 1.0) * 100` with no UI-rounding dependence.
- Missing/invalid/non-positive `entry_price_usdt` or `current_price_usdt` yields `distance_to_entry_pct=null` and `entry_state=null`.
- Entry-state thresholds are deterministic: `early (<-0.25)`, `at_trigger ([-0.25,+0.25])`, `late ((+0.25,+3.00])`, `chased (>+3.00)`.
- Entry-timing fields are output-only semantics and MUST NOT alter decision, risk, scoring, or ranking behavior.

## Phase-1 risk computation verification boundaries
- Risk fields include `stop_source` with allowed values `invalidation`, `atr_fallback`, `null`.
- Stop selection is deterministic and invalidation-first:
  1) valid setup invalidation below entry
  2) else valid ATR fallback below entry
  3) else non-evaluable (`null`) stop/risk path
- Long-spot invariant is strict: if `stop_price_initial >= entry_price`, all risk fields remain nullable (`null`).
- Missing required stop inputs and invalid stop inputs are non-evaluable paths and must keep stop/risk fields nullable (`null`) without coercion.
- If stop/risk distance is evaluable, canonical `1R/2R/3R` targets and RR fields are always derivable from `R`.
- `risk_acceptable` is threshold-driven and evaluated only when risk distance is evaluable; RR gate uses `rr_to_target_2`.
- RR threshold config key precedence is deterministic: `risk.min_rr_to_target_1` (canonical) wins when present; legacy alias `risk.min_rr_to_tp10` is only used when canonical key is absent; missing both uses default `1.3`.
- If canonical key is present but invalid, validation fails even if legacy alias is valid; non-finite RR threshold values are invalid for both keys.


## Trade-candidates TP/RR orientation verification boundaries
- Canonical `trade_candidates.target_1_price` / `trade_candidates.target_2_price` must be derived from setup-target levels only (no fixed +10%/+20% projection fallback).
- Canonical `trade_candidates.rr_to_target_1` / `trade_candidates.rr_to_target_2` must be derived against those canonical TP orientation targets.
- Missing/invalid/non-positive/non-finite `entry_price_usdt` yields `target_1_price=null`, `target_2_price=null`, `rr_to_target_1=null`, `rr_to_target_2=null`.
- Missing/invalid/non-positive `stop_price_initial` or `stop_price_initial >= entry_price_usdt` yields `rr_to_target_1=null`, `rr_to_target_2=null` and target prices remain nullable based on setup target availability/validity.
- Analysis/scorer raw target fields (e.g. `analysis.trade_levels.targets`) may exist for analysis, but must not override canonical TP/RR output fields.
- Drift guard: reports that keep `target_1_price`/`target_2_price` fields but show RR values numerically matching legacy scorer-target behavior (typical `rr_to_target_1≈0.5`, `rr_to_target_2≈1.0` despite different entry/stop-implied canonical RR) must fail verification.



## Global ranking setup-weight verification boundaries
- `phase_policy.setup_weights_active=true` applies canonical setup weights to global ranking as `global_score = final_score × setup_weight` (rounded to 6 decimals in runtime output).
- `phase_policy.setup_weights_active=false` bypasses configured setup weights and uses `setup_weight=1.0` for all rows.
- Weight resolution order is deterministic: direct lookup by `setup_type`, then optional `setup_id_to_weight_category_active` mapping, otherwise default `1.0`.
- Missing resolved weight key defaults to `1.0`; invalid configured weights (non-numeric, non-finite, `<=0`) fail clearly.
- Weighting must not alter `confluence`, `valid_setups`, dedup cardinality, or tie-breaker order definitions.


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
- Late-entry hard guard: if `current_price_usdt >= target_1_price`, decision cannot be `ENTER`; it must be `NO_TRADE` with `price_past_target_1`.
- Late-entry effective RR guard: for otherwise ENTER-eligible rows with `current_price_usdt < target_1_price`, compute `(target_2_price-current_price_usdt)/(current_price_usdt-stop_price_initial)`; values below `decision.min_effective_rr_to_target_2_for_enter` must downgrade to `WAIT` with `effective_rr_insufficient`.
- Missing/invalid/non-finite late-entry guard inputs are non-evaluable and must not be coerced to `price_past_target_1` or `effective_rr_insufficient`.
- `entry_state=chased` alone must not force a downgrade if late-entry guards do not fire.

## Shadow mode verification boundaries
- `shadow.mode` allowed values are exactly `{legacy_only, new_only, parallel}`; missing key defaults to `parallel`.
- Invalid `shadow.mode` values raise a clear config validation error (no silent fallback).
- `new_only`/`parallel` require `{tradeability.enabled, risk.enabled, decision.enabled} = true`; invalid partial activation fails validation.
- `shadow.primary_path` allowed values are exactly `{legacy, new}`; missing key follows deterministic semantics (`derived` for single-path modes, canonical default `legacy` for `parallel`).
- `mode`/`primary_path` contradictions fail validation clearly (e.g. `legacy_only`+`new`, `new_only`+`legacy`).
- Run manifest exposes deterministic path state via `pipeline_paths.shadow_mode`, `pipeline_paths.legacy_path_enabled`, `pipeline_paths.new_path_enabled`, `pipeline_paths.primary_path`, and `pipeline_paths.primary_path_source`.
- `trade_candidates` remains canonical SoT regardless of shadow mode and regardless of legacy artifacts produced in parallel.

## Shadow calibration recommendation verification boundaries
- Shadow recommendation status domain is exactly `{ready, insufficient_data, invalid_data}`.
- `insufficient_data` (not enough valid/evaluable samples) is distinct from `invalid_data` (invalid/non-finite rows present).
- Without sufficient sample basis, `shadow_recommendation.recommended_thresholds.*` and `shadow_recommendation.shadow_probabilities.overall.*` remain `null` (no coercion to live defaults).
- Non-finite calibration inputs (`NaN`, `+inf`, `-inf`) are reported as invalid and must not propagate into recommendation outputs.
- Recommendation outputs are analysis-only and MUST NOT change productive decision thresholds.


## Directional Volume preparation verification boundaries
- `trade_candidates.directional_volume_preparation` is optional; missing namespace is valid in Phase 1.
- `directional_volume_preparation=null` is valid and means not evaluated/not used (must not be coerced).
- If present as object, allowed keys are exactly `{buy_volume_share, sell_volume_share, imbalance_ratio, lookback_bars}`.
- `buy_volume_share`, `sell_volume_share`, and `imbalance_ratio` accept finite numbers or `null`; non-finite/invalid types are invalid input.
- `lookback_bars` accepts positive integer or `null`; zero/negative/non-integer/bool values are invalid input.
- Presence/absence of preparatory Directional Volume fields must not change Phase-1 score/decision outputs for identical otherwise-valid inputs.
