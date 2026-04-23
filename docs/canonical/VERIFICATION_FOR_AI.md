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
- Breakout calibration defaults are deterministic: `volume_score_min_spike=1.0`, `volume_score_full_spike=1.4`, weights `(distance,volume,trend,bb)=(0.40,0.30,0.20,0.10)`.
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



- Setup-specific max-stop resolution is deterministic: scalar `risk.max_stop_distance_pct` applies globally; object form requires `default`, supports optional `{reversal,pullback,breakout}` overrides, and missing setup override falls back to `default`.

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


## Ticket 3 verification boundaries
- pre-1d eligibility uses only MEXC metadata/ticker, persisted listing metadata, and CMC cap (no pre-1d OHLCV requirement).
- `listing_age_status` and `market_cap_status` domains are `{known_pass, known_fail, unknown_pass}`; unknown states are explicit and non-coerced.
- post-1d activity gate window is fixed calendar window ending at `daily_bar_id`; missing bars count inactive; >2 invalid-volume bars => `not_evaluable`.
- filter reason priority is deterministic: `COMPRESSION > TREND > VOLUME`; cap tie-break is `quote_volume_24h desc` then `symbol asc`.

## Ticket 4 verification boundaries (OHLCV cache/fetch)

- `cache_status` decision table: `fresh|stale|missing|broken` must be deterministic and closed.
- `fetch_decision` table: `fresh->skip`, `missing/broken->fetch_full`, `stale -> incremental/full` via `incremental_max_bars` threshold.
- Defaults and bounds:
  - `lookback_bars_1d=250` (`120..1000`), `lookback_bars_4h=250` (`120..1000`)
  - `min_lookback_bars_1d=120`, `min_lookback_bars_4h=120`
  - `incremental_max_bars=50` (`1..500`)
- Accepted-window verification:
  - full fetch persists only last `lookback_bars_<tf>` closed bars ending at cutoff
  - incremental persists only `cached_close < close <= cutoff`
- Conflict-strict upsert verification:
  - same PK + identical values => no-op
  - same PK + differing values => hard conflict/rollback

## Ticket 14 verification boundaries (history storage + snapshot lifecycle)

- Canonical OHLCV base-history root is `snapshots/history/ohlcv/`; path outputs are repository-root-relative.
- Supported canonical history timeframes are exactly `{1d, 4h}`; unsupported values fail clearly.
- History partition shape is deterministic: `timeframe=<tf>/symbol=<symbol>/year=<YYYY>/month=<MM>/`.
- Symbol path segments reject separators/traversal inputs (`/`, `\\`, `..`).
- Open/closed month classification uses explicit `reference_date` input only (no implicit wall-clock reads).
- Open month => mutable in normal operation; closed month => immutable in normal operation.
- Targeted monthly repair/backfill permission remains explicit and does not imply generic compaction/rewrite orchestration.
- Run snapshot path is deterministic from `daily_bar_id`: `snapshots/runs/YYYY/MM/DD/<run_id>/`.
- Canonical manifest path is exactly `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`.
- Manifest-path derivation is existence-agnostic (must succeed even before a runner physically writes the file).
- Config defaults and validation:
  - missing `independence_release.snapshots.*` and `independence_release.retention.*` keys fall back to defaults;
  - partial overrides merge field-by-field;
  - invalid values fail with key-specific validation errors.

## Ticket 5 verification boundaries (raw features)

- Mandatory public functions: `compute_raw_1d`, `compute_raw_4h`, `compute_raw_shared`, `build_feature_bundle`.
- Bundle order must be deterministic: `1d -> 4h -> shared`.
- Companion status fields are mandatory per derived metric.
- Missing/Gap/Fallback rules:
  - insufficient lookback => `insufficient_history`
  - required upstream null => `upstream_dependency_null`
  - invalid denominator / non-finite upstream => `invalid_upstream_value`
  - no shortened-window fallback unless spec defines an alternate path
- `volume_spike_persistence_4h` uses fixed `N=4` and requires full canonical history for all four checks (including each 10-bar baseline); otherwise `null + insufficient_history`.
- 1d required windows must detect missing-day gaps by canonical daily cadence and return `gap_in_required_window` at field level (no whole-pass crash).
- EMA warm-up rule: SMA bootstrap + `2 x period` bars minimum.
- Rank formula: `((count_strictly_less + 0.5 * count_equal) / n) * 100` on the full canonical window.
- Config split:
  - fixed/non-configurable: field-name-encoded windows (e.g., EMA20/50, median10, rank120)
  - configurable class-2: segmentation windows, `persistence_spike_threshold`, `features.structural_break.min_bars_below_before_break`
  - missing keys use defaults; invalid values fail validation.
- Ticket 5.1 contract deltas:
  - `RawFeatures4H` canonical anchor naming is `fixed_structural_break_anchor_4h` only (no public alias field).
  - `close_vs_high20_4h_pct` is mandatory in `RawFeatures4H` and computed as `((close_4h / fixed_structural_break_anchor_4h) - 1) * 100`.
  - `close_vs_high20_4h_pct` status contract: missing/non-`ok` anchor -> `upstream_dependency_null`; zero/non-finite anchor or non-finite close -> `invalid_upstream_value`; otherwise `ok`.
  - `bars_since_last_volume_shift_4h` uses configurable lookback and threshold `>= persistence_spike_threshold`; full window with no event returns lookback cap with status `ok`.
  - `distance_to_range_high_pct_abs` uses configurable 4h rolling high window and computes `abs((rolling_high-close)/rolling_high)*100`; zero or non-finite required window values yield `invalid_upstream_value`.

## Ticket 6 verification boundaries (Tier-1 axes)

- Tier-1 domain is exactly six axes: `trend_strength`, `reclaim_progress`, `compression_strength`, `expansion_progress_structural`, `volume_regime_shift`, `freshness_distance_structural`.
- Input availability rule: a feature is usable iff `value != null` and companion status is exactly `ok`.
- Normalization utility set is fixed: `norm_linear_clamped`, `norm_linear_clamped_inv`, `norm_piecewise_linear`, `weighted_mean`.
- Per-axis calibration values (anchors/points/weights) are sourced from `cfg.axes.<axis>`; defaults are canonical Ticket-6 values and partial overrides merge field-by-field.
- `weighted_mean` drops `null` scores and renormalizes retained weights; caller computes and persists `effective_weight_ratio`.
- Generic floor rule: `effective_weight_ratio < cfg.axes.min_effective_weight_ratio => axis not evaluable`.
- `reclaim_progress` must use two-level aggregation: per-anchor score first, then cross-anchor weighted aggregation.
- `compression_strength` pre-gate: at least one valid 4h compression input is required.
- `expansion_progress_structural` pre-gate: `data_4h_available=false => not_evaluable`; unresolved `dist_to_base_mid_pct` implies reduced-resolution path.
- `volume_regime_shift` pre-gate: `data_4h_available=false => not_evaluable`.
- `freshness_distance_structural` minimum-input rule: `<2` valid inputs => not evaluable; `2-3` => reduced resolution; `4` => full resolution.

## Ticket 7 verification boundaries (Tier-2-Simplified axes)

- Tier-2-Simplified domain is exactly three axes: `base_integrity_simplified`, `pullback_quality_simplified`, `reacceleration_strength_simplified`.
- Public entrypoint is exactly `compute_tier2_axes(feature_bundle, cfg)`.
- Input availability rule is strict: feature input is usable iff `value != null` and companion status is exactly `ok`.
- Two-path selection is deterministic and exclusive:
  - `data_4h_available=true` => 4h path only;
  - `data_4h_available=false` => 1d fallback path only;
  - no automatic fallthrough from 4h to 1d when 4h has dropout.
- Generic floor rule: `effective_weight_ratio < cfg.axes.min_effective_weight_ratio => axis not evaluable`.
- Reduced-resolution rule:
  - successful 1d fallback always yields `<axis>_reduced_resolution=true`;
  - successful 4h path with dropout yields `<axis>_reduced_resolution=true`;
  - full 4h path with all sub-inputs yields `<axis>_reduced_resolution=false`.
- `pullback_quality_simplified` requires segmentation validity pre-gate on selected path:
  - valid iff `impulse_high_price_tf > impulse_start_price_tf`;
  - invalid/missing/non-`ok` gate inputs => immediate not-evaluable (no dropout scoring).
- Pullback depth curve is intentionally non-monotone:
  - points `[(0,70),(20,100),(40,75),(60,40),(100,0)]`;
  - verification sample includes `x=10 -> 85`.
- Nullability contract:
  - `not_evaluable=true => axis is null`;
  - `effective_weight_ratio=null` when axis not evaluable;
  - axis null must never be coerced to 0/false/sentinel.

## Ticket 8 verification boundaries (phase interpreter)

- Domain and output:
  - positive phases are exactly `{pressure_build, trend_resume, transition_reclaim}` plus `none`.
  - `market_phase_runner_up` is always one positive phase and is deterministic.
- Input contract:
  - accepts exactly `Tier1AxisBundle`, `Tier2AxisBundle`, and `cfg`.
  - rejects type mismatches (`TypeError`) and bundle metadata mismatches (`ValueError`).
  - axis values must be finite `0..100` or `null` with consistent `*_not_evaluable`/`*_effective_weight_ratio` companions.
- Per-phase admissibility:
  - minimum-basis gate is checked before hard floors.
  - hard-floor missing inputs are not imputable and force phase score `0` with `hard_floor_failed`.
- Score/dropout:
  - optional weighted-score components may drop out phase-locally with renormalization.
  - if surviving weighted mass `< cfg.phase.min_effective_weight_ratio`, phase is `hard_floor_failed`.
- Ranking and semantics:
  - rank by `phase_score`, then `phase_floor_margin`, then fixed order (`pressure_build > trend_resume > transition_reclaim`).
  - `market_phase_gap = top_score - runner_up_score`.
  - `market_phase_blended=true` only when positive phase selected and gap below `phase_gap_floor`.
- Confidence:
  - global confidence floor uses uncapped `top_score`.
  - reduced-resolution cap applies only if winner used a weighted-score input with `_reduced_resolution=true`.
- Freshness:
  - `freshness_distance_structural*` values are passthrough diagnostics only.
  - freshness is excluded from minimum-basis, hard-floor, and weighted-score calculations.
- Canonical defaults:
  - `global_confidence_floor=55`, `reduced_resolution_confidence_cap=75`, `phase_gap_floor=8`, `min_effective_weight_ratio=0.60`.
  - floors: pressure_build `(60,50,50)`, trend_resume `(55,45,65)`, transition_reclaim `(45,45,55)`.

## Ticket 9 verification boundaries (invalidation + setup-cycle pre-state)

- Public entrypoint is exactly `compute_invalidation_and_cycle(phase_bundle, tier1_bundle, tier2_bundle, persisted_context, cfg)`.
- Current-run bundle identity mismatch on `symbol`, `daily_bar_id`, `intraday_bar_id`, or `data_4h_available` is a hard error.
- Persisted context symbol mismatch is a hard error.
- Structural invalidation suppresses timing invalidation (`timing_invalidation=false`, `timing_invalidation_reason=null`).
- `new_cycle_detected=true` and `structural_invalidation=true` cannot coexist.
- `phase_floor_recovered_since_cycle_end` is evaluated from current hard-floor admissibility diagnostics, not from `market_phase` label alone.
- First-seen bootstrap returns `FIRST_CYCLE_INITIALIZED` and `resolved_setup_cycle_id=1`.
- `cycle_reason_code` is always populated and `resolved_setup_cycle_id` is never null.
- Missing config keys under `invalidation`/`cycle` use defaults; invalid values fail validation.

## Ticket 10 verification boundaries (freshness + final state + persistence)

- Public entrypoints are exactly `compute_state_freshness(...)` and `compute_state_machine(...)` with typed input contracts.
- Current-run bundle mismatch (`symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available`) is a hard error.
- Persisted context symbol mismatch is a hard error.
- Not-admitted path (`PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE`) yields `state_machine_state=null` and `persistence_patch=null`.
- State confidence starts from `market_phase_confidence` and applies only blended + not-full-resolution penalties.
- Ticket 10 excludes the unresolved "knappe Margins" penalty.
- State/cycle persistence uses one authoritative writer and must be atomic per symbol.


## Ticket 11 verification boundaries (entry patterns)

- Public entrypoint is exactly `resolve_entry_pattern(phase_bundle, tier1_bundle, tier2_bundle, cfg)`.
- Resolver must not accept or read `state_bundle` / state-machine outputs.
- Phase gate: only `{pressure_build, trend_resume, transition_reclaim}` evaluate patterns; `none`/unknown phase returns `entry_pattern=none`, `entry_pattern_score=0.0`, `{}`.
- Admission requires finite numeric values for all axes referenced by admission conditions **and** score formulas.
- Missing/invalid/non-finite required axes (`None`, `NaN`, `inf`, `-inf`) make the pattern non-admitted.
- `base_reclaim` explicitly requires finite `volume_regime_shift` because it is a score-formula input.
- `candidate_pattern_scores_within_phase` includes admitted patterns only; non-admitted patterns must be absent.
- Deterministic tie-break order:
  - pressure_build: `range_reclaim > break_and_hold > breakout`
  - trend_resume: `resume_reclaim > shallow_pullback > continuation_breakout`
  - transition_reclaim: `base_reclaim > ema_reclaim > early_reversal_break`
- `compute_breakout_expansion_fit(expansion, target)` is a named helper and clamps to `[0,100]`.
