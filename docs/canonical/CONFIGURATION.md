# Configuration — Keys, Defaults, Limits (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_CONFIG
status: canonical
intent: "single machine-readable source for defaults/limits and their meanings"
runtime_config_file: config/config.yml
```

## 0) Canonical principle
This document defines canonical defaults, limits, and parameter meanings.
If the implementation deviates, either:
- update code to match canonical, or
- update canonical explicitly (AUTHORITY process).

## 1) Machine Defaults (VALID YAML)
```yaml
limits:
  universe:
    market_cap_usd_default: {min: 100_000_000, max: 10_000_000_000}
    volume_gates_default:
      min_turnover_24h: 0.03
      min_mexc_quote_volume_24h_usdt: 5_000_000
      min_mexc_share_24h: 0.01
      fallback_when_turnover_unavailable: "require only min_mexc_quote_volume_24h_usdt"
  outputs:
    global_top_n_default: 20

liquidity:
  orderbook_top_k_default: 200
  slippage_notional_usdt_default: 20_000
  grade_thresholds_bps_default:
    A_max: 20
    B_max: 50
    C_max: 100
    D_rule: "> C_max OR insufficient_depth"

execution_gates:
  mexc_orderbook:
    enabled_default: true
    max_spread_pct_default: 0.15
    bands_pct_default: [0.5, 1.0]
    min_depth_usd_default:
      "0.5": 80_000
      "1.0": 200_000

discovery:
  max_age_days_default: 180
  primary_source: cmc_date_added
  fallback_source: first_seen_ts

backtest:
  model_e2:
    T_hold_days_default: 10
    T_trigger_max_days_default: 5
    thresholds_pct_default: [10, 20]
    entry_price_default: close

history_minimums_default:
  breakout: { "1d": 30, "4h": 50 }
  pullback: { "1d": 60, "4h": 80 }
  reversal: { "1d": 120, "4h": 80 }
  # alias (doc-level): breakout_trend_1_5d setups use breakout thresholds
  breakout_trend_1_5d_uses: breakout

features:
  ema_periods_default: [20, 50]
  atr_period_default: 14
  volume_sma_periods_default: { "1d": 20, "4h": 20 }
  bb:
    period_default: 20
    stddev_default: 2.0
    rank_lookback_4h_default: 120
  atr_pct_rank_lookback_1d_default: 120

percent_rank_cross_section:
  population_definition: "eligible universe after hard gates with non-NaN feature value"
  output_scale: percent_0_100
  tie_handling: average_rank
  equality: ieee754_exact
  rounding_before_compare: none
  formula_rank01: "(count_less + 0.5*count_equal) / N"
  formula_percent_rank: "100 * rank01"

rolling_percent_rank_time_series:
  tie_handling: average_rank
  equality: ieee754_exact
  nan_policy:
    population_excludes_nan: true
  formula: "(count_less + 0.5*count_equal) / N"

scoring:
  volume_source_default: mexc
  volume_source_values: [mexc, global_fallback_mexc]

budget:
  shortlist_size_default: 200
  orderbook_top_k_default: 200
  pre_shortlist_market_cap_floor_usd_default: 25_000_000

tradeability:
  enabled_default: true
  notional_total_usdt_default: 20_000
  notional_chunk_usdt_default: 5_000
  max_tranches_default: 4
  band_pct_default: 1.0
  max_spread_pct_default: 0.15
  min_depth_1pct_usd_default: 200_000
  class_thresholds_bps_default:
    direct_ok_max_slippage_bps: 50
    tranche_ok_max_slippage_bps: 100
    marginal_max_slippage_bps: 150

risk:
  enabled_default: true
  stop_method_default: atr_multiple
  atr_period_default: 14
  atr_timeframe_default: 1d
  atr_multiple_default: 2.0
  min_stop_distance_pct_default: 4.0
  max_stop_distance_pct_default: 12.0
  min_rr_to_target_1_default: 1.3  # applied to rr_to_target_2 acceptance checkpoint

decision:
  enabled_default: true
  min_score_for_enter_default: 65
  min_score_for_wait_default: 40
  require_tradeability_for_enter_default: true
  require_risk_acceptable_for_enter_default: true
  min_effective_rr_to_target_2_for_enter_default: 1.0

btc_regime:
  enabled_default: true
  mode_default: threshold_modifier
  mode_values: [threshold_modifier]
  risk_off_enter_boost_default: 15

shadow:
  mode_default: parallel
  mode_values: [legacy_only, new_only, parallel]
  primary_path_default_parallel: legacy
  primary_path_values: [legacy, new]

```

## 2) Units & conventions
- Cross-sectional `percent_rank` values are in `[0..100]` (percent scale).
- Rolling time-series ranks (e.g., `*_rank_120_*`) remain in `[0..1]` and use explicit rank01-style field names/units.
- Scores are in `[0..100]`.
- `*_pct` is percent (e.g., 7.5 means 7.5%)
- `*_bps` is basis points (1% = 100 bps)
- All timestamps in canonical docs are milliseconds unless explicitly stated.

## 3) Canonical → runtime config key mapping (config/config.yml)
Canonical rule:
- If a runtime key exists, it must match this mapping.
- If a runtime key does **not** exist, the canonical default applies (still deterministic) and the manifest must report that the runtime key was absent.

| Canonical key | Runtime key in `config/config.yml` |
|---|---|
| limits.universe.market_cap_usd_default.min | universe_filters.market_cap.min_usd |
| limits.universe.market_cap_usd_default.max | universe_filters.market_cap.max_usd |
| limits.universe.volume_gates_default.min_turnover_24h | universe_filters.volume.min_turnover_24h |
| limits.universe.volume_gates_default.min_mexc_quote_volume_24h_usdt | universe_filters.volume.min_mexc_quote_volume_24h_usdt |
| limits.universe.volume_gates_default.min_mexc_share_24h | universe_filters.volume.min_mexc_share_24h |
| limits.outputs.global_top_n_default | outputs.global_top_n |
| liquidity.orderbook_top_k_default | liquidity.orderbook_top_k |
| liquidity.slippage_notional_usdt_default | liquidity.slippage_notional_usdt |
| liquidity.grade_thresholds_bps_default.A_max | liquidity.grade_thresholds_bps.a_max |
| liquidity.grade_thresholds_bps_default.B_max | liquidity.grade_thresholds_bps.b_max |
| liquidity.grade_thresholds_bps_default.C_max | liquidity.grade_thresholds_bps.c_max |
| execution_gates.mexc_orderbook.enabled_default | execution_gates.mexc_orderbook.enabled |
| execution_gates.mexc_orderbook.max_spread_pct_default | execution_gates.mexc_orderbook.max_spread_pct |
| execution_gates.mexc_orderbook.bands_pct_default | execution_gates.mexc_orderbook.bands_pct |
| execution_gates.mexc_orderbook.min_depth_usd_default.0.5 | execution_gates.mexc_orderbook.min_depth_usd."0.5" |
| execution_gates.mexc_orderbook.min_depth_usd_default.1.0 | execution_gates.mexc_orderbook.min_depth_usd."1.0" |
| discovery.max_age_days_default | discovery.max_age_days |
| backtest.model_e2.T_hold_days_default | backtest.t_hold_days |
| backtest.model_e2.T_trigger_max_days_default | backtest.t_trigger_max_days |
| backtest.model_e2.thresholds_pct_default | backtest.thresholds_pct |
| backtest.model_e2.entry_price_default | backtest.entry_price_field |
| history_minimums_default.breakout.1d | setup_validation.min_history_breakout_1d |
| history_minimums_default.breakout.4h | setup_validation.min_history_breakout_4h |
| history_minimums_default.pullback.1d | setup_validation.min_history_pullback_1d |
| history_minimums_default.pullback.4h | setup_validation.min_history_pullback_4h |
| history_minimums_default.reversal.1d | setup_validation.min_history_reversal_1d |
| history_minimums_default.reversal.4h | setup_validation.min_history_reversal_4h |
| features.ema_periods_default | features.ema_periods |
| features.atr_period_default | features.atr_period |
| features.volume_sma_periods_default.1d | features.volume_sma_periods.1d |
| features.volume_sma_periods_default.4h | features.volume_sma_periods.4h |
| features.bb.period_default | features.bollinger.period |
| features.bb.stddev_default | features.bollinger.stddev |
| features.bb.rank_lookback_4h_default | features.bollinger.rank_lookback_bars.4h |
| features.atr_pct_rank_lookback_1d_default | features.atr_rank_lookback_bars.1d |
| scoring.volume_source_default | scoring.volume_source |
| budget.shortlist_size_default | budget.shortlist_size |
| budget.orderbook_top_k_default | budget.orderbook_top_k |
| budget.pre_shortlist_market_cap_floor_usd_default | budget.pre_shortlist_market_cap_floor_usd |
| tradeability.enabled_default | tradeability.enabled |
| tradeability.notional_total_usdt_default | tradeability.notional_total_usdt |
| tradeability.notional_chunk_usdt_default | tradeability.notional_chunk_usdt |
| shadow.mode_default | shadow.mode |
| shadow.primary_path_default_parallel | shadow.primary_path |
| tradeability.max_tranches_default | tradeability.max_tranches |
| tradeability.band_pct_default | tradeability.band_pct |
| tradeability.max_spread_pct_default | tradeability.max_spread_pct |
| tradeability.min_depth_1pct_usd_default | tradeability.min_depth_1pct_usd |
| tradeability.class_thresholds_bps_default.direct_ok_max_slippage_bps | tradeability.class_thresholds.direct_ok_max_slippage_bps |
| tradeability.class_thresholds_bps_default.tranche_ok_max_slippage_bps | tradeability.class_thresholds.tranche_ok_max_slippage_bps |
| tradeability.class_thresholds_bps_default.marginal_max_slippage_bps | tradeability.class_thresholds.marginal_max_slippage_bps |
| risk.enabled_default | risk.enabled |
| risk.stop_method_default | risk.stop_method |
| risk.atr_period_default | risk.atr_period |
| risk.atr_timeframe_default | risk.atr_timeframe |
| risk.atr_multiple_default | risk.atr_multiple |
| risk.min_stop_distance_pct_default | risk.min_stop_distance_pct |
| risk.max_stop_distance_pct_default | risk.max_stop_distance_pct |
| risk.min_rr_to_target_1_default | risk.min_rr_to_target_1 |
| decision.enabled_default | decision.enabled |
| decision.min_score_for_enter_default | decision.min_score_for_enter |
| decision.min_score_for_wait_default | decision.min_score_for_wait |
| decision.require_tradeability_for_enter_default | decision.require_tradeability_for_enter |
| decision.require_risk_acceptable_for_enter_default | decision.require_risk_acceptable_for_enter |
| decision.min_effective_rr_to_target_2_for_enter_default | decision.min_effective_rr_to_target_2_for_enter |
| btc_regime.enabled_default | btc_regime.enabled |
| btc_regime.mode_default | btc_regime.mode |
| btc_regime.risk_off_enter_boost_default | btc_regime.risk_off_enter_boost |

Notes:
- `general.shortlist_size` is a *prefetch/workload budget* and is not the same as output top-n.
- Legacy alias for backward compatibility:
  - `universe_filters.volume.min_quote_volume_24h` aliases to `universe_filters.volume.min_mexc_quote_volume_24h_usdt`.
  - If both keys are present, `min_mexc_quote_volume_24h_usdt` wins.
  - `risk.min_rr_to_tp10` aliases to canonical `risk.min_rr_to_target_1` for one migration phase.
  - In this phase, the configured threshold is applied to `rr_to_target_2` (2R checkpoint) while key naming remains backward-compatible.
  - If both risk keys are present, `risk.min_rr_to_target_1` wins; if canonical key is present but invalid, validation fails.
- Legacy soft-prior keys for backward compatibility:
  - `universe_filters.market_cap.*` and `universe_filters.volume.*` remain readable and should be marked `legacy_soft_prior: true` in runtime config.

### Volume-gate semantics (deterministic)
- `min_turnover_24h` unit: ratio in `[0, +inf)`; default `0.03`.
- `min_mexc_quote_volume_24h_usdt` unit: USDT in `[0, +inf)`; default `5_000_000`.
- `min_mexc_share_24h` unit: ratio in `[0, 1]`; default `0.01`.
- Missing key => canonical default applies.
- Invalid value (NaN, non-castable, negative, out-of-range for share) => config validation error (fail-fast).


## 4) Setup-specific runtime keys (scoring.breakout_trend_1_5d)
- `risk_off_min_quote_volume_24h` default: `15_000_000`
- `trigger_4h_lookback_bars` default: `30`


## 5) Scoring volume source
- `scoring.volume_source` steuert die 24h-Volumenquelle für Setup-Scoring (`volume_map`).
- Defaults/Values:
  - `mexc` (default): nutze `quote_volume_24h` (MEXC)
  - `global_fallback_mexc`: nutze `global_volume_24h_usd`, fallback auf `quote_volume_24h` falls global fehlt
- Missing key => default `mexc`.
- Invalid value => Config-Validation-Error.
