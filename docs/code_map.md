# 📘 Code Map — Automatically Generated

**Repository:** schluchtenscheisser/spot-altcoin-scanner  
**Last Updated:** 2026-03-14 20:24 UTC  
**Generator:** scripts/update_codemap.py

---

## 📋 Overview

This Code Map provides a comprehensive structural overview of the Spot Altcoin Scanner codebase, including:
- Module structure (classes, functions, variables)
- Import dependencies
- **Call Graph Analysis** (function dependencies)
- Coupling statistics (internal vs. external calls)

---

## 📊 Repository Statistics

- **Total Modules:** 46
- **Total Classes:** 19
- **Total Functions:** 417

---

## 🧩 Module Structure

### 📄 `scanner/__init__.py`

**Functions:** —

---

### 📄 `scanner/backtest/__init__.py`

**Functions:** —

**Imports:** `e2_model`

---

### 📄 `scanner/backtest/e2_model.py`

**Functions:** `_is_triggered, _parse_date, _resolve_param_int, _resolve_thresholds, _threshold_key, _to_float, _trade_level_status, evaluate_e2_candidate`

**Module Variables:** `DEFAULT_THRESHOLDS_PCT, DEFAULT_T_HOLD, DEFAULT_T_TRIGGER_MAX, alias_list, breakout, breakout_invalid, candle, close, day, entry_price` _(+35 more)_

**Imports:** `__future__, collections.abc, datetime, math, typing`

---

### 📄 `scanner/clients/__init__.py`

**Functions:** —

---

### 📄 `scanner/clients/mapping.py`

**Classes:** `MappingResult, SymbolMapper`

**Functions:** `__init__, _get_market_cap, _load_overrides, base_asset, generate_reports, map_symbol, map_universe, mapped, suggest_overrides, to_dict`

**Module Variables:** `base_asset, base_asset_upper, collisions, collisions_file, logger, output_path, override, override_symbol, overrides, result` _(+5 more)_

**Imports:** `json, pathlib, typing, utils.io_utils, utils.logging_utils`

---

### 📄 `scanner/clients/marketcap_client.py`

**Classes:** `MarketCapClient`

**Functions:** `__init__, _request, build_symbol_map, get_all_listings, get_listings, get_market_cap_for_symbol`

**Module Variables:** `BASE_URL, cache_key, cached, collect_raw_marketcap, collisions, data, existing_rank, listings, logger, new_rank` _(+5 more)_

**Imports:** `os, requests, scanner.utils.raw_collector, typing, utils.io_utils, utils.logging_utils`

---

### 📄 `scanner/clients/mexc_client.py`

**Classes:** `MEXCClient`

**Functions:** `__init__, _rate_limit, _request, get_24h_tickers, get_exchange_info, get_klines, get_multiple_klines, get_orderbook, get_spot_usdt_symbols`

**Module Variables:** `BASE_URL, cache_key, data, elapsed, exchange_info, logger, params, response, results, retry_after` _(+3 more)_

**Imports:** `requests, time, typing, utils.io_utils, utils.logging_utils`

---

### 📄 `scanner/config.py`

**Classes:** `ScannerConfig`

**Functions:** `_budget_mapping, _expect_integer_number, _expect_number, _parse_integer_budget_value, btc_regime_enabled, btc_regime_mode, btc_regime_risk_off_enter_boost, budget_orderbook_top_k, budget_shortlist_size, cmc_api_key, config_version, decision_enabled, decision_min_effective_rr_to_target_2_for_enter, decision_min_score_for_enter, decision_min_score_for_wait, decision_require_risk_acceptable_for_enter, decision_require_tradeability_for_enter, exclude_leveraged, exclude_stablecoins, exclude_wrapped, load_config, log_file, log_level, log_to_file, lookback_days_1d, lookback_days_4h, market_cap_max, market_cap_min, mexc_enabled, min_history_days_1d, min_mexc_quote_volume_24h_usdt, min_mexc_share_24h, min_quote_volume_24h, min_turnover_24h, pre_shortlist_market_cap_floor_usd, resolve_risk_min_rr_to_target_1, risk_atr_multiple, risk_atr_period, risk_atr_timeframe, risk_enabled, risk_max_stop_distance_pct, risk_min_rr_to_target_1, risk_min_rr_to_tp10, risk_min_stop_distance_pct, risk_stop_method, run_mode, scoring_volume_source, shadow_mode, shortlist_size, spec_version, timezone, tradeability_band_pct, tradeability_class_thresholds, tradeability_enabled, tradeability_max_spread_pct, tradeability_max_tranches, tradeability_min_depth_1pct_usd, tradeability_notional_chunk_usdt, tradeability_notional_total_usdt, validate_config`

**Module Variables:** `CONFIG_PATH, allowed_shadow_modes, btc_cfg, budget_cfg, cfg, cfg_path, class_thresholds, configured_primary, d, decision_cfg` _(+24 more)_

**Imports:** `dataclasses, math, os, pathlib, typing, yaml`

---

### 📄 `scanner/main.py`

**Functions:** `main, parse_args`

**Module Variables:** `args, cfg, parser`

**Imports:** `__future__, argparse, config, pipeline, sys`

---

### 📄 `scanner/pipeline/__init__.py`

**Functions:** `_apply_tradeability_gate, _build_scoring_volume_maps, _compute_mexc_share_24h, _compute_turnover_24h, _enrich_scored_entries_with_market_activity, _extract_cmc_global_volume_24h, _to_optional_float, run_pipeline`

**Module Variables:** `allowed, allowed_classes, asof_dt, asof_iso, asof_ts_ms, breakout_results, btc_regime, cmc, cmc_data, cmc_listings` _(+73 more)_

**Imports:** `__future__, clients.mapping, clients.marketcap_client, clients.mexc_client, config, decision, discovery, features` _(+16 more)_

---

### 📄 `scanner/pipeline/backtest_runner.py`

**Functions:** `_calendar_window_indices, _evaluate_candidate, _extract_backtest_config, _float_or_none, _infer_breakout_no_trade_reason, _is_executed_trade, _iso_to_date, _setup_triggered, _simulate_breakout_4h_trade, _summarize, run_backtest_from_history, run_backtest_from_snapshots`

**Module Variables:** `BREAKOUT_TREND_SETUP_IDS, FOUR_H_TIME_STOP_CANDLES, all_dates, analysis, atr_abs, atr_pct, breakout_level, bt, candle, candles` _(+59 more)_

**Imports:** `__future__, collections, datetime, json, pathlib, typing`

---

### 📄 `scanner/pipeline/cross_section.py`

**Functions:** `percent_rank_average_ties`

**Module Variables:** `avg_rank_by_value, n, sorted_values, value_list`

**Imports:** `__future__, typing`

---

### 📄 `scanner/pipeline/decision.py`

**Functions:** `_evaluate_late_entry_guard, _expect_bool, _expect_number, _load_decision_config, _normalize_reason_list, _normalize_tradeability_reasons, _resolve_btc_regime_state, _resolve_current_price, _resolve_target_price, _stable_reason_order, _to_optional_bool, _to_optional_float, _to_optional_str, apply_decision_layer`

**Module Variables:** `ALLOWED_TRADEABILITY, ENTER_TRADEABILITY, REASON_ORDER, VALID_BTC_REGIME_STATES, analysis, btc_cfg, btc_regime_state, can_enter, can_wait, cfg` _(+34 more)_

**Imports:** `__future__, math, typing`

---

### 📄 `scanner/pipeline/discovery.py`

**Functions:** `_iso_to_ts_ms, compute_discovery_fields`

**Module Variables:** `age_days, normalized, parsed, source, source_ts`

**Imports:** `__future__, datetime, typing`

---

### 📄 `scanner/pipeline/excel_output.py`

**Classes:** `ExcelReportGenerator`

**Functions:** `__init__, _create_summary_sheet, _create_trade_candidates_sheet, _sanitize_float_if_needed, _sanitize_float_or_none, _to_excel_cell_value, _validate_trade_candidates, generate_excel_report`

**Module Variables:** `ALLOWED_DECISIONS, CANDIDATE_COLUMNS, REQUIRED_FIELDS, btc_regime, cell, checks, col, counts, decision, enter_candidates` _(+16 more)_

**Imports:** `datetime, logging, math, openpyxl, openpyxl.styles, openpyxl.utils, pathlib, typing`

---

### 📄 `scanner/pipeline/features.py`

**Classes:** `FeatureEngine`

**Functions:** `__init__, _calc_atr_pct, _calc_atr_pct_series, _calc_bollinger_width_series, _calc_breakout_distance, _calc_drawdown, _calc_ema, _calc_percent_rank, _calc_quote_volume_features, _calc_return, _calc_sma, _calc_volume_spike, _compute_timeframe_features, _config_get, _convert_to_native_types, _detect_base, _detect_higher_high, _detect_higher_low, _get_atr_rank_lookback, _get_bollinger_params, _get_last_closed_idx, _get_volume_period_for_timeframe, _lookback_days_to_bars, _timeframe_to_seconds, compute_all`

**Module Variables:** `alpha, ath, atr, atr_pct, atr_pct_series, atr_rank_lookback, atr_rank_window, avg_rank, bars, base_features` _(+81 more)_

**Imports:** `logging, math, numpy, typing`

---

### 📄 `scanner/pipeline/filters.py`

**Classes:** `UniverseFilters`

**Functions:** `__init__, _apply_risk_flags, _apply_soft_liquidity_priors, _build_exclusion_patterns_from_new_config, _extract_quote_asset, _filter_exclusions, _filter_pre_shortlist_market_cap_floor, _filter_quote_assets, _load_denylist, _load_unlock_overrides, _parse_days_to_unlock, _safe_load_yaml, apply_all, get_filter_stats`

**Module Variables:** `base, bases, budget_cfg, data, days_to_unlock, default_patterns, default_quote_allowlist, entries, exclusion_pass, exclusions_cfg` _(+28 more)_

**Imports:** `logging, pathlib, typing, yaml`

---

### 📄 `scanner/pipeline/global_ranking.py`

**Functions:** `_config_get, _resolve_setup_weight, _validate_weight, compute_global_top20`

**Module Variables:** `agg, cat_map, category, cur, cur_setup_id, prefer_retest, prev, prev_setup_id, prev_setups, prev_weighted` _(+11 more)_

**Imports:** `__future__, math, typing`

---

### 📄 `scanner/pipeline/liquidity.py`

**Functions:** `_band_label, _compute_buy_vwap, _compute_slippage_bps, _empty_orderbook_metrics, _is_orderbook_stale, _read_tradeability_thresholds, _root_config, _to_levels, _tradeability_params, _unknown_tradeability, apply_liquidity_metrics_to_shortlist, compute_orderbook_liquidity_metrics, compute_orderbook_metrics, compute_tradeability_metrics, fetch_orderbooks_for_top_k, get_grade_thresholds_bps, get_orderbook_top_k, get_slippage_notional_usdt, select_top_k_for_orderbook`

**Module Variables:** `a_max, ask_cutoff, ask_depth, asks, b_max, band_f, band_label, band_metrics, bands_cfg, bands_pct` _(+57 more)_

**Imports:** `__future__, logging, typing`

---

### 📄 `scanner/pipeline/manifest.py`

**Functions:** `_nested_bool, _nested_mapping_value, build_config_hash, derive_feature_flags, derive_pipeline_paths, read_canonical_schema_version, resolve_pipeline_paths, resolve_shadow_mode, write_manifest_atomic`

**Module Variables:** `canonical_json, cursor, has_config_primary, mode, primary_path, raw_primary, resolved_primary, shadow_cfg, source, tmp_path` _(+1 more)_

**Imports:** `__future__, hashlib, json, pathlib, typing`

---

### 📄 `scanner/pipeline/ohlcv.py`

**Classes:** `OHLCVFetcher`

**Functions:** `__init__, _build_lookback, fetch_all, get_fetch_stats`

**Module Variables:** `candles, collect_raw_ohlcv, date_range, failed, first_symbol, general_cfg, history_cfg, klines, limit, logger` _(+14 more)_

**Imports:** `datetime, logging, scanner.utils.raw_collector, typing`

---

### 📄 `scanner/pipeline/output.py`

**Classes:** `ReportGenerator`

**Functions:** `__init__, _append_timing_reason, _build_entry_state_counts, _build_entry_state_counts_by_decision, _build_run_manifest, _build_trade_candidates, _classify_entry_state, _compute_distance_to_entry_pct, _compute_rr_to_target, _decision_sort_key, _entry_state_key, _finite_number_or_none, _format_m_usd, _format_markdown_summary, _format_nullable_bool, _format_nullable_float, _format_pct, _format_reason_list, _format_setup_entry, _format_trade_candidate_markdown, _resolve_planned_entry_price, _resolve_target_price, _sanitize_bool_or_none, _sanitize_directional_volume_preparation, _sanitize_float_or_none, _sanitize_optional_metric, _sanitize_positive_float_or_none, _sanitize_reason_list, _validate_trade_candidates_for_markdown, _with_rank, generate_json_report, generate_markdown_report, save_reports`

**Module Variables:** `allowed_keys, analysis, asof_iso, asof_ts_ms, candidate, canonical_schema_version, coin_name, components, counts, current_numeric` _(+82 more)_

**Imports:** `datetime, excel_output, json, logging, manifest, pathlib, scanner.schema, typing`

---

### 📄 `scanner/pipeline/regime.py`

**Functions:** `_to_float, compute_btc_regime, compute_btc_regime_from_1d_features`

**Module Variables:** `btc_features, btc_klines_1d, close, close_gt_ema50, ema20, ema20_gt_ema50, ema50, features_1d, logger, state`

**Imports:** `__future__, logging, typing`

---

### 📄 `scanner/pipeline/runtime_market_meta.py`

**Classes:** `RuntimeMarketMetaExporter`

**Functions:** `__init__, _build_exchange_symbol_map, _build_identity, _build_quality, _build_symbol_info, _build_ticker, _extract_filter_value, _to_float, _to_int, export`

**Module Variables:** `ask, bid, cmc_data, exchange_symbol, exchange_symbol_map, fdv, fdv_to_mcap, global_volume_24h_usd, identity, identity_payload` _(+27 more)_

**Imports:** `__future__, clients.mapping, config, logging, pathlib, typing, utils.io_utils, utils.time_utils`

---

### 📄 `scanner/pipeline/scoring/__init__.py`

**Functions:** —

---

### 📄 `scanner/pipeline/scoring/breakout.py`

**Classes:** `BreakoutScorer`

**Functions:** `__init__, _closed_candle_count, _generate_reasons, _resolve_breakout_v2_fields, _resolve_invalidation_anchor, _score_breakout, _score_momentum, _score_trend, _score_volume, score, score_breakouts`

**Module Variables:** `anchor, breakout_confirmed, breakout_curve, breakout_dist, breakout_dist_numeric, breakout_score, breakout_v2, candles_1d, candles_4h, close_1d` _(+48 more)_

**Imports:** `logging, math, scanner.pipeline.scoring.decision_inputs, scanner.pipeline.scoring.trade_levels, scanner.pipeline.scoring.weights, typing`

---

### 📄 `scanner/pipeline/scoring/breakout_trend_1_5d.py`

**Classes:** `BreakoutTrend1to5DScorer`

**Functions:** `__init__, _anti_chase_multiplier, _band_label, _band_reason, _bb_score, _breakout_distance_score, _btc_multiplier, _calc_high_20d_excluding_current, _evaluate_execution_gate, _find_breakout_indices, _optional_finite_float, _overextension_multiplier, _require_finite_float, _require_int, _trend_score, _volume_score, score_breakout_trend_1_5d, score_symbol`

**Module Variables:** `alt_r3, alt_r7, anti, ask, base, base_score, bb_rank, bb_score, bf, bid` _(+63 more)_

**Imports:** `__future__, math, scanner.pipeline.scoring.decision_inputs, scanner.pipeline.scoring.trade_levels, typing`

---

### 📄 `scanner/pipeline/scoring/decision_inputs.py`

**Functions:** `standardize_entry_readiness, standardize_invalidation_anchor`

**Module Variables:** `is_ready, numeric_anchor, reasons, seen`

**Imports:** `__future__, math, typing`

---

### 📄 `scanner/pipeline/scoring/pullback.py`

**Classes:** `PullbackScorer`

**Functions:** `__init__, _closed_candle_count, _generate_reasons, _resolve_invalidation_anchor, _resolve_pullback_v2_fields, _score_pullback, _score_rebound, _score_trend, _score_volume, score, score_pullbacks`

**Module Variables:** `anchor_price, anchor_type, candles_1d, candles_4h, default_weights, dist_ema20, dist_ema50, ema20_4h, ema50_4h, f1d` _(+48 more)_

**Imports:** `logging, math, scanner.pipeline.scoring.decision_inputs, scanner.pipeline.scoring.trade_levels, scanner.pipeline.scoring.weights, typing`

---

### 📄 `scanner/pipeline/scoring/reversal.py`

**Classes:** `ReversalScorer`

**Functions:** `__init__, _closed_candle_count, _generate_reasons, _resolve_invalidation_anchor, _resolve_reversal_v2_fields, _resolve_volume_spike, _score_base, _score_drawdown, _score_reclaim, _score_volume, score, score_reversals`

**Module Variables:** `anchor_type, base_low, base_score, candles_1d, candles_4h, dd, dd_pct, default_weights, dist_ema20, dist_ema50` _(+46 more)_

**Imports:** `logging, math, scanner.pipeline.scoring.decision_inputs, scanner.pipeline.scoring.trade_levels, scanner.pipeline.scoring.weights, typing`

---

### 📄 `scanner/pipeline/scoring/trade_levels.py`

**Functions:** `_atr_absolute, _planned_entry_price, _risk_cfg, _targets, _to_float, breakout_trade_levels, compute_phase1_risk_fields, pullback_trade_levels, reversal_trade_levels`

**Module Variables:** `atr_1d, atr_4h, atr_pct, atr_stop, atr_value, base_low, breakout_dist_20, breakout_level_20, cfg, close` _(+22 more)_

**Imports:** `__future__, math, scanner.config, typing`

---

### 📄 `scanner/pipeline/scoring/weights.py`

**Functions:** `load_component_weights`

**Module Variables:** `alias_key, alias_present, canonical_present, cfg_weights, logger, missing, mode, total`

**Imports:** `logging, typing`

---

### 📄 `scanner/pipeline/shortlist.py`

**Classes:** `ShortlistSelector`

**Functions:** `__init__, _attach_proxy_liquidity_score, get_shortlist_stats, select`

**Module Variables:** `cfg, coverage, eligible_symbols, logger, max_vol, min_vol, percent_scores, r, shortlist, shortlist_volume` _(+4 more)_

**Imports:** `cross_section, logging, math, scanner.config, typing`

---

### 📄 `scanner/pipeline/snapshot.py`

**Classes:** `SnapshotManager`

**Functions:** `__init__, create_snapshot, get_snapshot_stats, list_snapshots, load_snapshot, resolve_history_dir`

**Module Variables:** `base, history_dir, logger, payload, size_mb, snapshot, snapshot_config, snapshot_dir, snapshot_path, snapshots`

**Imports:** `datetime, json, logging, pathlib, re, typing`

---

### 📄 `scanner/schema.py`

**Functions:** —

**Module Variables:** `REPORT_META_VERSION, REPORT_SCHEMA_VERSION`

---

### 📄 `scanner/tools/backfill_btc_regime.py`

**Classes:** `BackfillStats`

**Functions:** `_compute_regime, _daterange, _ensure_minimum_version, _extract_btc_features_1d, _load_snapshot, _parse_date, _preflight_missing_paths, _resolve_snapshots_dir, backfill, build_parser, main`

**Module Variables:** `args, btc, btc_features_1d, changed, current, end, features, maybe_1d, meta, missing_paths` _(+10 more)_

**Imports:** `__future__, argparse, dataclasses, datetime, json, pathlib, scanner.config, scanner.pipeline.regime` _(+3 more)_

---

### 📄 `scanner/tools/backfill_snapshots.py`

**Classes:** `BackfillStats`

**Functions:** `_build_minimal_features, _daterange, _extract_ohlcv_row, _fake_get_cache_path, _fake_timestamp_to_ms, _fake_utc_date, _fake_utc_now, _fake_utc_timestamp, _mark_full_backfill, _parse_date, _patched_full_mode_time_sources, _preflight_requirements, _resolve_cache_date, _resolve_snapshots_dir, _run_full_mode, _snapshot_base, _validate_full_mode_prerequisites, backfill, build_parser, main`

**Module Variables:** `SYMBOL_CACHE_RE, args, asof_iso, asof_ts_ms, candles, close, config, current, date_dir, end` _(+29 more)_

**Imports:** `__future__, argparse, contextlib, dataclasses, datetime, json, pathlib, re` _(+7 more)_

---

### 📄 `scanner/tools/export_evaluation_dataset.py`

**Functions:** `_build_price_series_by_symbol, _daterange, _evaluate_label_window_5d, _load_snapshot, _parse_date, _run_id_from_export_start, _score_from_entry, _utc_iso, _utc_now, build_parser, export_dataset, main`

**Module Variables:** `DATASET_SCHEMA_VERSION, args, backtest_cfg, candle, config, config_root, current, e2, e2_labels_5d, end` _(+36 more)_

**Imports:** `__future__, argparse, datetime, json, pathlib, scanner.backtest.e2_model, scanner.config, scanner.pipeline.global_ranking` _(+2 more)_

---

### 📄 `scanner/tools/prepare_shadow_calibration.py`

**Functions:** `_bool_or_none, _derive_recommendation, _finite_float, _is_finite_or_none, _load_jsonl, _status_from_quality, _utc_iso, _utc_now, _write_json_atomic, build_parser, build_shadow_calibration_prep_report, main, run`

**Module Variables:** `REQUIRED_LABEL_FIELDS, args, candidates, evaluable, generated_at, hit10_rate, hit20_rate, idx, line, mae` _(+27 more)_

**Imports:** `__future__, argparse, datetime, json, math, pathlib, sys, typing`

---

### 📄 `scanner/tools/validate_features.py`

**Functions:** `_emit, _error, _is_number, validate_features`

**Module Variables:** `comps, data, pm, report_path, results, section_key, setup_path, val`

**Imports:** `json, os, sys, typing`

---

### 📄 `scanner/utils/__init__.py`

**Functions:** —

---

### 📄 `scanner/utils/io_utils.py`

**Functions:** `cache_exists, get_cache_path, load_cache, load_json, save_cache, save_json`

**Module Variables:** `cache_dir, cache_path, date, filepath`

**Imports:** `datetime, json, pathlib, time_utils, typing`

---

### 📄 `scanner/utils/logging_utils.py`

**Functions:** `get_logger, setup_logger`

**Module Variables:** `console_handler, file_handler, formatter, log_dir, log_file, logger`

**Imports:** `datetime, logging, logging.handlers, pathlib, sys`

---

### 📄 `scanner/utils/raw_collector.py`

**Functions:** `_is_missing_value, _prepare_marketcap_payload_for_normalize, _sanitize_marketcap_df_for_parquet, _stringify_scalar_for_raw_snapshot, collect_raw_features, collect_raw_marketcap, collect_raw_ohlcv`

**Module Variables:** `df, flat_records, has_non_finite_float, has_oversized_int, prepared_data, sanitized, series`

**Imports:** `json, math, pandas, scanner.utils.save_raw, typing`

---

### 📄 `scanner/utils/save_raw.py`

**Functions:** `save_raw_snapshot`

**Module Variables:** `base_dir, base_root, csv_filename, csv_gzip, csv_path, parquet_path, run_id, saved_paths`

**Imports:** `datetime, os, pandas`

---

### 📄 `scanner/utils/time_utils.py`

**Functions:** `ms_to_timestamp, parse_timestamp, timestamp_to_ms, utc_date, utc_now, utc_timestamp`

**Module Variables:** `ts`

**Imports:** `datetime, typing`

---


## 🔗 Function Dependencies (Call Graph)

_This section shows which functions call which other functions, helping identify coupling and refactoring opportunities._

### 📄 scanner/backtest/e2_model.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_is_triggered` | `_to_float` | `get` |
| `_parse_date` | — | `fromisoformat` |
| `_resolve_param_int` | — | `ValueError`, `append`, `join` |
| `_resolve_thresholds` | `_to_float` | `ValueError`, `add` |
| `_threshold_key` | — | `is_integer` |
| `_to_float` | — | `isfinite` |
| `_trade_level_status` | `_to_float` | `get` |
| `evaluate_e2_candidate` | `_is_triggered`, `_parse_date`, `_resolve_param_int`, `_resolve_thresholds`, `_threshold_key`, `_to_float`, `_trade_level_status` | `append`, `get`, `isclose`, `isoformat`, `timedelta` |

### 📄 scanner/clients/mapping.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | `_load_overrides` | `Path` |
| `_load_overrides` | — | `error`, `exists`, `info`, `load_json` |
| `base_asset` | — | `endswith` |
| `generate_reports` | `to_dict` | `Path`, `info`, `mkdir`, `save_json`, `values` |
| `map_symbol` | — | `MappingResult`, `endswith`, `upper` |
| `map_universe` | `map_symbol` | `info` |
| `suggest_overrides` | — | `Path`, `info`, `mkdir`, `save_json`, `values` |
| `to_dict` | `_get_market_cap` | `get` |

### 📄 scanner/clients/marketcap_client.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Session`, `getenv`, `update`, `warning` |
| `_request` | — | `RequestException`, `ValueError`, `error`, `get`, `json`, `keys`, `raise_for_status` |
| `build_symbol_map` | `get_all_listings` | `append`, `debug`, `get`, `info`, `upper`, `warning` |
| `get_all_listings` | `get_listings` | — |
| `get_listings` | `_request` | `cache_exists`, `collect_raw_marketcap`, `error`, `get`, `info`, `load_cache`, `save_cache`, `warning` |
| `get_market_cap_for_symbol` | `build_symbol_map` | `get`, `upper` |

### 📄 scanner/clients/mexc_client.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Session` |
| `_rate_limit` | — | `sleep`, `time` |
| `_request` | `_rate_limit` | `RequestException`, `error`, `get`, `json`, `raise_for_status`, `request`, `sleep`, `warning` |
| `get_24h_tickers` | `_request` | `cache_exists`, `info`, `load_cache`, `save_cache` |
| `get_exchange_info` | `_request` | `cache_exists`, `info`, `load_cache`, `save_cache` |
| `get_klines` | `_request` | `cache_exists`, `debug`, `load_cache`, `save_cache` |
| `get_multiple_klines` | `get_klines` | `error`, `info` |
| `get_orderbook` | `_request` | — |
| `get_spot_usdt_symbols` | `get_exchange_info` | `append`, `get`, `info` |

### 📄 scanner/config.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_budget_mapping` | — | `get` |
| `_expect_integer_number` | `_expect_number` | `append`, `is_integer` |
| `_expect_number` | — | `append`, `isfinite` |
| `_parse_integer_budget_value` | — | `ValueError`, `is_integer` |
| `btc_regime_enabled` | — | `get` |
| `btc_regime_mode` | — | `get` |
| `btc_regime_risk_off_enter_boost` | — | `get` |
| `budget_orderbook_top_k` | `_budget_mapping`, `_parse_integer_budget_value` | `get` |
| `budget_shortlist_size` | `_budget_mapping`, `_parse_integer_budget_value` | `get` |
| `cmc_api_key` | — | `get`, `getenv` |
| `config_version` | — | `get` |
| `decision_enabled` | — | `get` |
| `decision_min_effective_rr_to_target_2_for_enter` | — | `get` |
| `decision_min_score_for_enter` | — | `get` |
| `decision_min_score_for_wait` | — | `get` |
| `decision_require_risk_acceptable_for_enter` | — | `get` |
| `decision_require_tradeability_for_enter` | — | `get` |
| `exclude_leveraged` | — | `get` |
| `exclude_stablecoins` | — | `get` |
| `exclude_wrapped` | — | `get` |
| `load_config` | — | `FileNotFoundError`, `Path`, `ScannerConfig`, `exists`, `safe_load` |
| `log_file` | — | `get` |
| `log_level` | — | `get` |
| `log_to_file` | — | `get` |
| `lookback_days_1d` | — | `get` |
| `lookback_days_4h` | — | `get` |
| `market_cap_max` | — | `get` |
| `market_cap_min` | — | `get` |
| `mexc_enabled` | — | `get` |
| `min_history_days_1d` | — | `get` |
| `min_mexc_quote_volume_24h_usdt` | — | `get` |
| `min_mexc_share_24h` | — | `get` |
| `min_turnover_24h` | — | `get` |
| `pre_shortlist_market_cap_floor_usd` | `_budget_mapping`, `_parse_integer_budget_value` | `get` |
| `resolve_risk_min_rr_to_target_1` | — | `ValueError`, `get`, `isfinite` |
| `risk_atr_multiple` | — | `get` |
| `risk_atr_period` | — | `get` |
| `risk_atr_timeframe` | — | `get` |
| `risk_enabled` | — | `get` |
| `risk_max_stop_distance_pct` | — | `get` |
| `risk_min_rr_to_target_1` | `resolve_risk_min_rr_to_target_1` | `get` |
| `risk_min_stop_distance_pct` | — | `get` |
| `risk_stop_method` | — | `get` |
| `run_mode` | — | `get` |
| `scoring_volume_source` | — | `get` |
| `shadow_mode` | — | `get` |
| `shortlist_size` | — | `get` |
| `spec_version` | — | `get` |
| `timezone` | — | `get` |
| `tradeability_band_pct` | — | `get` |
| `tradeability_class_thresholds` | — | `get` |
| `tradeability_enabled` | — | `get` |
| `tradeability_max_spread_pct` | — | `get` |
| `tradeability_max_tranches` | — | `get` |
| `tradeability_min_depth_1pct_usd` | — | `get` |
| `tradeability_notional_chunk_usdt` | — | `get` |
| `tradeability_notional_total_usdt` | — | `get` |
| `validate_config` | `_expect_integer_number`, `_expect_number` | `append`, `get` |

### 📄 scanner/main.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `main` | `parse_args` | `load_config`, `run_pipeline`, `setdefault` |
| `parse_args` | `parse_args` | `ArgumentParser`, `add_argument` |

### 📄 scanner/pipeline/__init__.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_apply_tradeability_gate` | — | `append`, `get` |
| `_build_scoring_volume_maps` | `_to_optional_float` | `get` |
| `_enrich_scored_entries_with_market_activity` | — | `get` |
| `_extract_cmc_global_volume_24h` | `_to_optional_float` | `get` |
| `run_pipeline` | `_apply_tradeability_gate`, `_build_scoring_volume_maps`, `_compute_mexc_share_24h`, `_compute_turnover_24h`, `_enrich_scored_entries_with_market_activity`, `_extract_cmc_global_volume_24h`, `_to_optional_float` | `FeatureEngine`, `MEXCClient`, `MarketCapClient`, `OHLCVFetcher`, `ReportGenerator`, `RuntimeMarketMetaExporter`, `ShortlistSelector`, `SnapshotManager`, `SymbolMapper`, `UniverseFilters`, `_get_market_cap`, `append`, `apply_all`, `apply_decision_layer`, `apply_liquidity_metrics_to_shortlist`, `build_symbol_map`, `compute_all`, `compute_btc_regime`, `compute_discovery_fields`, `compute_global_top20`, `create_snapshot`, `derive_pipeline_paths`, `export`, `fetch_all`, `fetch_orderbooks_for_top_k`, `get`, `get_24h_tickers`, `get_exchange_info`, `get_listings`, `info`, `keys`, `map_symbol`, `map_universe`, `perf_counter`, `replace`, `save_reports`, `score_breakout_trend_1_5d`, `score_pullbacks`, `score_reversals`, `select`, `strftime`, `timestamp_to_ms`, `update`, `utc_now` |

### 📄 scanner/pipeline/backtest_runner.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_calendar_window_indices` | — | `get`, `isoformat`, `timedelta` |
| `_evaluate_candidate` | `_calendar_window_indices`, `_iso_to_date`, `_setup_triggered` | `append`, `get`, `isoformat`, `timedelta`, `update` |
| `_extract_backtest_config` | — | `get` |
| `_infer_breakout_no_trade_reason` | `_float_or_none` | `get` |
| `_is_executed_trade` | `_float_or_none` | `get` |
| `_iso_to_date` | — | `fromisoformat` |
| `_setup_triggered` | `_float_or_none` | `get` |
| `_simulate_breakout_4h_trade` | `_float_or_none` | `get` |
| `_summarize` | `_is_executed_trade` | `get` |
| `run_backtest_from_history` | `run_backtest_from_snapshots` | `Path`, `append`, `get`, `glob`, `load` |
| `run_backtest_from_snapshots` | `_evaluate_candidate`, `_extract_backtest_config`, `_float_or_none`, `_infer_breakout_no_trade_reason`, `_simulate_breakout_4h_trade`, `_summarize` | `append`, `defaultdict`, `get`, `items`, `setdefault` |

### 📄 scanner/pipeline/cross_section.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `percent_rank_average_ties` | — | `append`, `items`, `setdefault` |

### 📄 scanner/pipeline/decision.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_evaluate_late_entry_guard` | `_resolve_current_price`, `_resolve_target_price`, `_to_optional_float` | `get` |
| `_expect_bool` | — | `ValueError` |
| `_expect_number` | — | `ValueError`, `isfinite` |
| `_load_decision_config` | `_expect_bool`, `_expect_number` | `ValueError`, `get` |
| `_normalize_reason_list` | — | `add`, `append`, `strip` |
| `_normalize_tradeability_reasons` | `_normalize_reason_list` | `get` |
| `_resolve_btc_regime_state` | — | `ValueError`, `get`, `strip`, `upper` |
| `_resolve_current_price` | `_to_optional_float` | `get` |
| `_resolve_target_price` | `_to_optional_float` | `get` |
| `_stable_reason_order` | — | `add`, `append` |
| `_to_optional_float` | — | `isfinite` |
| `_to_optional_str` | — | `strip` |
| `apply_decision_layer` | `_evaluate_late_entry_guard`, `_load_decision_config`, `_normalize_reason_list`, `_normalize_tradeability_reasons`, `_resolve_btc_regime_state`, `_stable_reason_order`, `_to_optional_bool`, `_to_optional_float`, `_to_optional_str` | `append`, `extend`, `get` |

### 📄 scanner/pipeline/discovery.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_iso_to_ts_ms` | — | `endswith`, `fromisoformat`, `replace`, `strip`, `timestamp` |
| `compute_discovery_fields` | `_iso_to_ts_ms` | — |

### 📄 scanner/pipeline/excel_output.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Path`, `get`, `info`, `mkdir` |
| `_create_summary_sheet` | `_sanitize_float_or_none` | `Alignment`, `Font`, `PatternFill`, `cell`, `create_sheet`, `extend`, `get`, `strftime`, `utcnow` |
| `_create_trade_candidates_sheet` | `_to_excel_cell_value` | `Alignment`, `Font`, `PatternFill`, `cell`, `create_sheet`, `get`, `get_column_letter` |
| `_sanitize_float_if_needed` | — | `isinf`, `isnan` |
| `_sanitize_float_or_none` | — | `isinf`, `isnan` |
| `_to_excel_cell_value` | `_sanitize_float_if_needed` | `join` |
| `_validate_trade_candidates` | — | `ValueError`, `append`, `get`, `join` |
| `generate_excel_report` | `_create_summary_sheet`, `_create_trade_candidates_sheet`, `_validate_trade_candidates` | `Workbook`, `get`, `info`, `remove`, `save` |

### 📄 scanner/pipeline/features.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `info` |
| `_calc_atr_pct` | — | `nanmean`, `warning` |
| `_calc_atr_pct_series` | — | `full`, `isnan`, `nanmean` |
| `_calc_bollinger_width_series` | — | `full`, `nanmean`, `nanstd` |
| `_calc_breakout_distance` | — | `error`, `nanmax`, `warning` |
| `_calc_drawdown` | — | `nanmax` |
| `_calc_ema` | — | `nanmean`, `warning` |
| `_calc_percent_rank` | — | `array`, `isnan` |
| `_calc_quote_volume_features` | `_calc_sma`, `_calc_volume_spike` | `isnan` |
| `_calc_return` | — | `error`, `warning` |
| `_calc_sma` | — | `nanmean` |
| `_calc_volume_spike` | — | `isnan`, `warning` |
| `_compute_timeframe_features` | `_calc_atr_pct`, `_calc_atr_pct_series`, `_calc_bollinger_width_series`, `_calc_breakout_distance`, `_calc_drawdown`, `_calc_ema`, `_calc_percent_rank`, `_calc_quote_volume_features`, `_calc_return`, `_calc_sma`, `_calc_volume_spike`, `_config_get`, `_convert_to_native_types`, `_detect_base`, `_detect_higher_high`, `_detect_higher_low`, `_get_atr_rank_lookback`, `_get_bollinger_params`, `_get_volume_period_for_timeframe`, `_lookback_days_to_bars` | `array`, `get`, `tolist`, `update`, `warning` |
| `_config_get` | — | `get` |
| `_convert_to_native_types` | — | `isnan`, `items` |
| `_detect_base` | `_config_get` | `isnan`, `nanmax`, `nanmin`, `warning` |
| `_detect_higher_high` | — | `nanmax` |
| `_detect_higher_low` | — | `nanmin` |
| `_get_atr_rank_lookback` | `_config_get` | — |
| `_get_bollinger_params` | `_config_get` | — |
| `_get_volume_period_for_timeframe` | `_config_get` | `get`, `warning` |
| `_lookback_days_to_bars` | `_timeframe_to_seconds` | `ceil`, `warning` |
| `_timeframe_to_seconds` | — | `lower`, `strip` |
| `compute_all` | `_compute_timeframe_features`, `_get_last_closed_idx` | `debug`, `error`, `get`, `info`, `items` |

### 📄 scanner/pipeline/filters.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | `_build_exclusion_patterns_from_new_config`, `_load_denylist`, `_load_unlock_overrides` | `Path`, `get`, `info`, `upper`, `warning` |
| `_apply_risk_flags` | — | `append`, `get`, `upper` |
| `_build_exclusion_patterns_from_new_config` | — | `extend`, `get`, `upper` |
| `_extract_quote_asset` | — | `endswith`, `get`, `upper` |
| `_filter_exclusions` | — | `append`, `get`, `upper` |
| `_filter_pre_shortlist_market_cap_floor` | — | `append`, `get` |
| `_filter_quote_assets` | `_extract_quote_asset` | `append` |
| `_load_denylist` | `_safe_load_yaml` | `get`, `update`, `upper` |
| `_load_unlock_overrides` | `_parse_days_to_unlock`, `_safe_load_yaml` | `add`, `get`, `lower`, `upper` |
| `_parse_days_to_unlock` | — | `warning` |
| `_safe_load_yaml` | — | `exists`, `safe_load` |
| `apply_all` | `_apply_risk_flags`, `_apply_soft_liquidity_priors`, `_filter_exclusions`, `_filter_pre_shortlist_market_cap_floor`, `_filter_quote_assets` | `info` |
| `get_filter_stats` | `_apply_soft_liquidity_priors`, `_filter_exclusions`, `_filter_pre_shortlist_market_cap_floor`, `_filter_quote_assets`, `apply_all` | — |

### 📄 scanner/pipeline/global_ranking.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_config_get` | — | `get` |
| `_resolve_setup_weight` | `_config_get`, `_validate_weight` | `ValueError`, `get` |
| `_validate_weight` | — | `ValueError`, `isfinite` |
| `compute_global_top20` | `_config_get`, `_resolve_setup_weight` | `add`, `endswith`, `get`, `items`, `update`, `values` |

### 📄 scanner/pipeline/liquidity.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_band_label` | — | `is_integer`, `replace` |
| `_compute_slippage_bps` | `_compute_buy_vwap`, `_to_levels` | `get` |
| `_empty_orderbook_metrics` | `_band_label` | — |
| `_is_orderbook_stale` | — | `get` |
| `_read_tradeability_thresholds` | `_root_config` | `ValueError`, `get` |
| `_to_levels` | — | `append` |
| `_tradeability_params` | `_read_tradeability_thresholds`, `_root_config` | `get` |
| `apply_liquidity_metrics_to_shortlist` | `_empty_orderbook_metrics`, `_root_config`, `_unknown_tradeability`, `compute_orderbook_liquidity_metrics`, `compute_orderbook_metrics`, `compute_tradeability_metrics`, `get_grade_thresholds_bps`, `get_slippage_notional_usdt` | `append`, `get`, `update` |
| `compute_orderbook_liquidity_metrics` | `_compute_buy_vwap`, `_to_levels` | `get` |
| `compute_orderbook_metrics` | `_band_label`, `_empty_orderbook_metrics`, `_to_levels` | `get` |
| `compute_tradeability_metrics` | `_band_label`, `_compute_slippage_bps`, `_is_orderbook_stale`, `_tradeability_params`, `_unknown_tradeability`, `compute_orderbook_metrics` | `add`, `get` |
| `fetch_orderbooks_for_top_k` | `get_orderbook_top_k`, `select_top_k_for_orderbook` | `add`, `debug`, `get`, `get_orderbook`, `warning` |
| `get_grade_thresholds_bps` | `_root_config` | `get` |
| `get_orderbook_top_k` | `_root_config` | `get` |
| `get_slippage_notional_usdt` | `_root_config` | `get` |
| `select_top_k_for_orderbook` | — | `get` |

### 📄 scanner/pipeline/manifest.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_nested_bool` | `_nested_mapping_value` | — |
| `build_config_hash` | — | `dumps`, `encode`, `hexdigest`, `sha256` |
| `derive_feature_flags` | `_nested_bool`, `derive_pipeline_paths` | — |
| `derive_pipeline_paths` | `resolve_pipeline_paths` | — |
| `read_canonical_schema_version` | — | `ValueError`, `read_text`, `split`, `splitlines`, `startswith`, `strip` |
| `resolve_pipeline_paths` | `resolve_shadow_mode` | `ValueError`, `get` |
| `resolve_shadow_mode` | — | `ValueError`, `get` |
| `write_manifest_atomic` | — | `dumps`, `mkdir`, `replace`, `with_suffix`, `write_text` |

### 📄 scanner/pipeline/ohlcv.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | `_build_lookback` | `get`, `info` |
| `_build_lookback` | — | `get`, `items`, `warning` |
| `fetch_all` | — | `collect_raw_ohlcv`, `error`, `get`, `get_klines`, `info`, `warning` |
| `get_fetch_stats` | — | `fromtimestamp`, `keys`, `strftime`, `values` |

### 📄 scanner/pipeline/output.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Path`, `get`, `info`, `mkdir` |
| `_append_timing_reason` | — | `get` |
| `_build_entry_state_counts` | `_entry_state_key` | `get` |
| `_build_entry_state_counts_by_decision` | `_entry_state_key` | `get` |
| `_build_run_manifest` | — | `Path`, `build_config_hash`, `derive_feature_flags`, `derive_pipeline_paths`, `get`, `read_canonical_schema_version`, `setdefault`, `strftime`, `utcnow` |
| `_build_trade_candidates` | `_append_timing_reason`, `_classify_entry_state`, `_compute_distance_to_entry_pct`, `_compute_rr_to_target`, `_resolve_planned_entry_price`, `_resolve_target_price`, `_sanitize_bool_or_none`, `_sanitize_directional_volume_preparation`, `_sanitize_float_or_none`, `_sanitize_positive_float_or_none`, `_sanitize_reason_list` | `append`, `get`, `sort` |
| `_classify_entry_state` | `_sanitize_float_or_none` | — |
| `_compute_distance_to_entry_pct` | `_sanitize_positive_float_or_none` | — |
| `_compute_rr_to_target` | `_sanitize_positive_float_or_none` | — |
| `_decision_sort_key` | `_sanitize_float_or_none` | `get`, `upper` |
| `_finite_number_or_none` | — | `ValueError` |
| `_format_m_usd` | — | `replace` |
| `_format_markdown_summary` | `_build_entry_state_counts` | `append`, `get` |
| `_format_nullable_float` | `_sanitize_float_or_none` | — |
| `_format_pct` | — | `replace` |
| `_format_reason_list` | — | `ValueError`, `join` |
| `_format_setup_entry` | `_format_m_usd`, `_format_pct`, `_sanitize_optional_metric` | `append`, `capitalize`, `dumps`, `get`, `items`, `join`, `replace` |
| `_format_trade_candidate_markdown` | `_format_nullable_bool`, `_format_nullable_float`, `_format_reason_list` | `append`, `get` |
| `_resolve_planned_entry_price` | `_sanitize_positive_float_or_none` | `get`, `lower` |
| `_resolve_target_price` | `_sanitize_positive_float_or_none` | `get` |
| `_sanitize_directional_volume_preparation` | `_finite_number_or_none` | `ValueError`, `get`, `join`, `keys` |
| `_sanitize_positive_float_or_none` | `_sanitize_float_or_none` | — |
| `_sanitize_reason_list` | — | `append`, `strip` |
| `_validate_trade_candidates_for_markdown` | — | `ValueError`, `get`, `join` |
| `_with_rank` | `_sanitize_optional_metric` | `append`, `get` |
| `generate_json_report` | `_build_entry_state_counts`, `_build_entry_state_counts_by_decision`, `_build_run_manifest`, `_build_trade_candidates`, `_with_rank` | `endswith`, `get`, `isoformat`, `update`, `utcnow` |
| `generate_markdown_report` | `_format_markdown_summary`, `_format_trade_candidate_markdown`, `_validate_trade_candidates_for_markdown`, `generate_json_report` | `append`, `extend`, `get`, `join`, `strftime`, `utcnow` |
| `save_reports` | `generate_json_report`, `generate_markdown_report` | `ExcelReportGenerator`, `dump`, `error`, `generate_excel_report`, `get`, `info`, `warning`, `write`, `write_manifest_atomic` |

### 📄 scanner/pipeline/regime.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `compute_btc_regime` | `compute_btc_regime_from_1d_features` | `compute_all`, `get`, `get_klines`, `warning` |
| `compute_btc_regime_from_1d_features` | `_to_float` | `get` |

### 📄 scanner/pipeline/runtime_market_meta.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Path`, `ScannerConfig`, `get`, `mkdir` |
| `_build_exchange_symbol_map` | — | `get` |
| `_build_identity` | `_to_float`, `_to_int` | `get` |
| `_build_quality` | — | `append`, `get` |
| `_build_symbol_info` | `_extract_filter_value`, `_to_float`, `_to_int` | `get` |
| `_build_ticker` | `_to_float`, `_to_int` | `get` |
| `_extract_filter_value` | — | `get` |
| `export` | `_build_exchange_symbol_map`, `_build_identity`, `_build_quality`, `_build_symbol_info`, `_build_ticker` | `get`, `info`, `keys`, `pop`, `save_json`, `strftime`, `utc_now` |

### 📄 scanner/pipeline/scoring/breakout.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `load_component_weights` |
| `_closed_candle_count` | — | `get` |
| `_generate_reasons` | — | `append`, `get` |
| `_resolve_breakout_v2_fields` | — | `get`, `isfinite`, `standardize_entry_readiness` |
| `_resolve_invalidation_anchor` | — | `get`, `isfinite`, `standardize_invalidation_anchor` |
| `_score_breakout` | — | `get` |
| `_score_momentum` | — | `get` |
| `_score_trend` | — | `get` |
| `_score_volume` | — | `get` |
| `score` | `_generate_reasons`, `_resolve_breakout_v2_fields`, `_resolve_invalidation_anchor`, `_score_breakout`, `_score_momentum`, `_score_trend`, `_score_volume` | `append`, `get`, `items` |
| `score_breakouts` | `_closed_candle_count`, `score` | `BreakoutScorer`, `append`, `breakout_trade_levels`, `compute_phase1_risk_fields`, `debug`, `error`, `get`, `items`, `sort` |

### 📄 scanner/pipeline/scoring/breakout_trend_1_5d.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | `_require_finite_float`, `_require_int` | `ValueError`, `get`, `isclose`, `items` |
| `_band_label` | — | `is_integer`, `replace` |
| `_band_reason` | — | `replace` |
| `_btc_multiplier` | — | `get` |
| `_calc_high_20d_excluding_current` | — | `get` |
| `_evaluate_execution_gate` | `_band_label`, `_band_reason` | `append`, `get` |
| `_find_breakout_indices` | — | `get` |
| `_optional_finite_float` | — | `isfinite` |
| `_require_finite_float` | — | `ValueError`, `get`, `isfinite` |
| `_require_int` | — | `ValueError`, `get` |
| `_trend_score` | — | `get` |
| `score_breakout_trend_1_5d` | `score_symbol` | `BreakoutTrend1to5DScorer`, `breakout_trade_levels`, `compute_phase1_risk_fields`, `extend`, `get`, `items`, `sort`, `update` |
| `score_symbol` | `_anti_chase_multiplier`, `_bb_score`, `_breakout_distance_score`, `_btc_multiplier`, `_calc_high_20d_excluding_current`, `_evaluate_execution_gate`, `_find_breakout_indices`, `_optional_finite_float`, `_overextension_multiplier`, `_trend_score`, `_volume_score` | `append`, `get`, `standardize_entry_readiness` |

### 📄 scanner/pipeline/scoring/decision_inputs.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `standardize_entry_readiness` | — | `ValueError`, `add`, `append`, `strip` |
| `standardize_invalidation_anchor` | — | `isfinite` |

### 📄 scanner/pipeline/scoring/pullback.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `load_component_weights` |
| `_closed_candle_count` | — | `get` |
| `_generate_reasons` | — | `append`, `get` |
| `_resolve_invalidation_anchor` | — | `get`, `standardize_invalidation_anchor` |
| `_resolve_pullback_v2_fields` | — | `append`, `get`, `isfinite`, `standardize_entry_readiness` |
| `_score_pullback` | — | `get` |
| `_score_rebound` | — | `get` |
| `_score_trend` | — | `get` |
| `_score_volume` | — | `get` |
| `score` | `_generate_reasons`, `_resolve_invalidation_anchor`, `_resolve_pullback_v2_fields`, `_score_pullback`, `_score_rebound`, `_score_trend`, `_score_volume` | `append`, `get`, `items` |
| `score_pullbacks` | `_closed_candle_count`, `score` | `PullbackScorer`, `append`, `compute_phase1_risk_fields`, `debug`, `error`, `get`, `items`, `pullback_trade_levels`, `sort` |

### 📄 scanner/pipeline/scoring/reversal.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `load_component_weights` |
| `_closed_candle_count` | — | `get` |
| `_generate_reasons` | `_resolve_volume_spike` | `append`, `get` |
| `_resolve_invalidation_anchor` | — | `get`, `standardize_invalidation_anchor` |
| `_resolve_reversal_v2_fields` | — | `get`, `isfinite`, `standardize_entry_readiness` |
| `_resolve_volume_spike` | — | `get` |
| `_score_base` | — | `get`, `isfinite` |
| `_score_drawdown` | — | `get` |
| `_score_reclaim` | — | `get` |
| `_score_volume` | `_resolve_volume_spike` | — |
| `score` | `_generate_reasons`, `_resolve_invalidation_anchor`, `_resolve_reversal_v2_fields`, `_score_base`, `_score_drawdown`, `_score_reclaim`, `_score_volume` | `append`, `get`, `items` |
| `score_reversals` | `_closed_candle_count`, `score` | `ReversalScorer`, `append`, `compute_phase1_risk_fields`, `debug`, `error`, `get`, `items`, `reversal_trade_levels`, `sort` |

### 📄 scanner/pipeline/scoring/trade_levels.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_atr_absolute` | `_to_float` | `get` |
| `_planned_entry_price` | `_to_float` | `get` |
| `_risk_cfg` | — | `get`, `resolve_risk_min_rr_to_target_1` |
| `_to_float` | — | `isfinite` |
| `breakout_trade_levels` | `_atr_absolute`, `_targets`, `_to_float` | `get` |
| `compute_phase1_risk_fields` | `_planned_entry_price`, `_risk_cfg`, `_to_float` | `get`, `update` |
| `pullback_trade_levels` | `_atr_absolute`, `_targets`, `_to_float` | `get` |
| `reversal_trade_levels` | `_atr_absolute`, `_targets`, `_to_float` | `get` |

### 📄 scanner/pipeline/scoring/weights.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `load_component_weights` | — | `copy`, `get`, `items`, `join`, `lower`, `strip`, `values`, `warning` |

### 📄 scanner/pipeline/shortlist.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `ScannerConfig`, `ValueError`, `info` |
| `_attach_proxy_liquidity_score` | — | `append`, `get`, `log1p`, `percent_rank_average_ties` |
| `get_shortlist_stats` | — | `get` |
| `select` | `_attach_proxy_liquidity_score` | `get`, `info`, `warning` |

### 📄 scanner/pipeline/snapshot.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | `resolve_history_dir` | `info`, `mkdir` |
| `create_snapshot` | — | `dump`, `info`, `isoformat`, `stat`, `strftime`, `timestamp`, `update`, `utcnow` |
| `get_snapshot_stats` | `load_snapshot` | — |
| `list_snapshots` | — | `append`, `fullmatch`, `glob`, `info`, `load`, `sort` |
| `load_snapshot` | — | `FileNotFoundError`, `exists`, `info`, `load` |
| `resolve_history_dir` | — | `Path`, `get` |

### 📄 scanner/tools/backfill_btc_regime.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_compute_regime` | `_extract_btc_features_1d` | `compute_btc_regime_from_1d_features` |
| `_daterange` | — | `timedelta` |
| `_ensure_minimum_version` | — | `get` |
| `_extract_btc_features_1d` | — | `get` |
| `_load_snapshot` | — | `ValueError`, `load` |
| `_parse_date` | — | `fromisoformat` |
| `_preflight_missing_paths` | `_daterange` | `exists`, `isoformat` |
| `_resolve_snapshots_dir` | — | `Path`, `load_config`, `resolve_history_dir` |
| `backfill` | `_compute_regime`, `_daterange`, `_ensure_minimum_version`, `_load_snapshot`, `_parse_date`, `_preflight_missing_paths`, `_resolve_snapshots_dir` | `BackfillStats`, `FileNotFoundError`, `ValueError`, `append`, `dump`, `exists`, `get`, `isoformat`, `join`, `pop`, `setdefault`, `write` |
| `build_parser` | — | `ArgumentParser`, `add_argument` |
| `main` | `backfill`, `build_parser` | `parse_args` |

### 📄 scanner/tools/backfill_snapshots.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_build_minimal_features` | `_extract_ohlcv_row` | `FileNotFoundError`, `exists`, `is_file`, `items`, `iterdir`, `match` |
| `_daterange` | — | `timedelta` |
| `_extract_ohlcv_row` | — | `ValueError`, `date`, `fromtimestamp`, `group`, `isoformat`, `load`, `match` |
| `_fake_get_cache_path` | `_resolve_cache_date` | `original_io_get_cache_path` |
| `_fake_timestamp_to_ms` | — | `timestamp` |
| `_fake_utc_date` | `_resolve_cache_date` | — |
| `_fake_utc_timestamp` | — | `strftime` |
| `_mark_full_backfill` | — | `ValueError`, `dump`, `load`, `setdefault`, `write` |
| `_parse_date` | — | `fromisoformat` |
| `_patched_full_mode_time_sources` | — | `datetime` |
| `_preflight_requirements` | `_build_minimal_features`, `_daterange`, `_validate_full_mode_prerequisites` | `FileNotFoundError`, `append`, `exists`, `isoformat`, `join` |
| `_resolve_cache_date` | — | `isoformat` |
| `_resolve_snapshots_dir` | — | `Path`, `load_config`, `resolve_history_dir` |
| `_run_full_mode` | `_patched_full_mode_time_sources` | `ScannerConfig`, `get`, `load_config`, `run_pipeline` |
| `_snapshot_base` | — | `isoformat`, `replace`, `strftime`, `timestamp` |
| `_validate_full_mode_prerequisites` | `_build_minimal_features` | `ValueError`, `get`, `isoformat`, `load_config`, `lower` |
| `backfill` | `_build_minimal_features`, `_daterange`, `_mark_full_backfill`, `_parse_date`, `_preflight_requirements`, `_resolve_snapshots_dir`, `_run_full_mode`, `_snapshot_base` | `BackfillStats`, `FileExistsError`, `FileNotFoundError`, `Path`, `ValueError`, `dump`, `exists`, `isoformat`, `mkdir`, `now`, `write` |
| `build_parser` | — | `ArgumentParser`, `add_argument` |
| `main` | `backfill`, `build_parser` | `parse_args` |

### 📄 scanner/tools/export_evaluation_dataset.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_build_price_series_by_symbol` | — | `get`, `items`, `setdefault` |
| `_daterange` | — | `timedelta` |
| `_evaluate_label_window_5d` | — | `evaluate_e2_candidate` |
| `_load_snapshot` | — | `ValueError`, `load` |
| `_parse_date` | — | `fromisoformat` |
| `_run_id_from_export_start` | — | `strftime` |
| `_score_from_entry` | — | `ValueError`, `get` |
| `_utc_iso` | — | `strftime` |
| `_utc_now` | — | `now` |
| `build_parser` | — | `ArgumentParser`, `add_argument` |
| `export_dataset` | `_build_price_series_by_symbol`, `_daterange`, `_evaluate_label_window_5d`, `_load_snapshot`, `_parse_date`, `_run_id_from_export_start`, `_score_from_entry`, `_utc_iso`, `_utc_now` | `FileNotFoundError`, `Path`, `ValueError`, `append`, `compute_global_top20`, `dumps`, `evaluate_e2_candidate`, `exists`, `get`, `isoformat`, `join`, `load_config`, `mkdir`, `sort`, `timestamp`, `write` |
| `main` | `build_parser`, `export_dataset` | `parse_args` |

### 📄 scanner/tools/prepare_shadow_calibration.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_derive_recommendation` | `_status_from_quality` | `append`, `get` |
| `_finite_float` | — | `isfinite` |
| `_is_finite_or_none` | — | `isfinite` |
| `_load_jsonl` | — | `ValueError`, `append`, `loads`, `read_text`, `splitlines`, `strip` |
| `_utc_iso` | — | `strftime` |
| `_utc_now` | — | `now` |
| `_write_json_atomic` | — | `dumps`, `mkdir`, `replace`, `with_suffix`, `write_text` |
| `build_parser` | — | `ArgumentParser`, `add_argument` |
| `build_shadow_calibration_prep_report` | `_bool_or_none`, `_derive_recommendation`, `_finite_float`, `_is_finite_or_none`, `_utc_iso`, `_utc_now` | `ValueError`, `append`, `get`, `join` |
| `main` | `build_parser`, `run` | `parse_args` |
| `run` | `_load_jsonl`, `_utc_now`, `_write_json_atomic`, `build_shadow_calibration_prep_report` | `Path`, `ValueError`, `strftime` |

### 📄 scanner/tools/validate_features.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_emit` | — | `dumps` |
| `validate_features` | `_emit`, `_error`, `_is_number` | `append`, `exists`, `get`, `items`, `load` |

### 📄 scanner/utils/io_utils.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `cache_exists` | `get_cache_path` | `exists` |
| `get_cache_path` | — | `Path`, `mkdir`, `utc_date` |
| `load_cache` | `get_cache_path`, `load_json` | `exists` |
| `load_json` | — | `Path`, `load` |
| `save_cache` | `get_cache_path`, `save_json` | — |
| `save_json` | — | `Path`, `dump`, `mkdir` |

### 📄 scanner/utils/logging_utils.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `get_logger` | `setup_logger` | `getLogger` |
| `setup_logger` | — | `Formatter`, `Path`, `RotatingFileHandler`, `StreamHandler`, `addHandler`, `clear`, `getLogger`, `mkdir`, `setFormatter`, `setLevel`, `strftime`, `upper`, `utcnow` |

### 📄 scanner/utils/raw_collector.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `_is_missing_value` | — | `isna` |
| `_prepare_marketcap_payload_for_normalize` | `_prepare_marketcap_payload_for_normalize` | `items` |
| `_sanitize_marketcap_df_for_parquet` | — | `copy`, `dumps`, `isinf`, `isnan` |
| `_stringify_scalar_for_raw_snapshot` | `_is_missing_value` | `isinf`, `isnan` |
| `collect_raw_features` | — | `save_raw_snapshot` |
| `collect_raw_marketcap` | `_prepare_marketcap_payload_for_normalize`, `_sanitize_marketcap_df_for_parquet` | `json_normalize`, `save_raw_snapshot` |
| `collect_raw_ohlcv` | — | `DataFrame`, `append`, `items`, `save_raw_snapshot` |

### 📄 scanner/utils/save_raw.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `save_raw_snapshot` | — | `getenv`, `join`, `lower`, `makedirs`, `strftime`, `to_csv`, `to_parquet`, `utcnow` |

### 📄 scanner/utils/time_utils.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `ms_to_timestamp` | — | `fromtimestamp` |
| `parse_timestamp` | — | `endswith`, `fromisoformat` |
| `timestamp_to_ms` | — | `timestamp` |
| `utc_date` | `utc_now` | `strftime` |
| `utc_now` | — | `now` |
| `utc_timestamp` | `utc_now` | `strftime` |


---

## 📊 Coupling Statistics

_Modules with high external call counts may benefit from refactoring._

| Module | Internal Calls | External Calls | Total | Coupling |
|--------|----------------|----------------|-------|----------|
| `scanner/pipeline/output.py` | 41 | 71 | 112 | 🔴 High |
| `scanner/config.py` | 10 | 69 | 79 | 🔴 High |
| `scanner/tools/backfill_snapshots.py` | 18 | 60 | 78 | 🔴 High |
| `scanner/pipeline/features.py` | 29 | 48 | 77 | 🔴 High |
| `scanner/pipeline/__init__.py` | 9 | 49 | 58 | 🔴 High |
| `scanner/pipeline/liquidity.py` | 30 | 24 | 54 | ⚠️ Medium |
| `scanner/pipeline/filters.py` | 17 | 31 | 48 | 🔴 High |
| `scanner/pipeline/scoring/breakout_trend_1_5d.py` | 16 | 30 | 46 | 🔴 High |
| `scanner/tools/export_evaluation_dataset.py` | 11 | 32 | 43 | 🔴 High |
| `scanner/pipeline/backtest_runner.py` | 15 | 25 | 40 | 🔴 High |
| `scanner/pipeline/decision.py` | 17 | 23 | 40 | ⚠️ Medium |
| `scanner/pipeline/excel_output.py` | 6 | 34 | 40 | 🔴 High |
| `scanner/tools/prepare_shadow_calibration.py` | 13 | 27 | 40 | 🔴 High |
| `scanner/pipeline/scoring/reversal.py` | 11 | 27 | 38 | 🔴 High |
| `scanner/tools/backfill_btc_regime.py` | 11 | 27 | 38 | 🔴 High |
| `scanner/pipeline/scoring/breakout.py` | 9 | 27 | 36 | 🔴 High |
| `scanner/pipeline/scoring/pullback.py` | 9 | 27 | 36 | 🔴 High |
| `scanner/clients/mexc_client.py` | 7 | 28 | 35 | 🔴 High |
| `scanner/clients/marketcap_client.py` | 4 | 27 | 31 | 🔴 High |
| `scanner/pipeline/runtime_market_meta.py` | 12 | 18 | 30 | 🔴 High |
| `scanner/backtest/e2_model.py` | 10 | 15 | 25 | 🔴 High |
| `scanner/clients/mapping.py` | 4 | 21 | 25 | 🔴 High |
| `scanner/pipeline/manifest.py` | 5 | 19 | 24 | 🔴 High |
| `scanner/pipeline/scoring/trade_levels.py` | 14 | 10 | 24 | ⚠️ Medium |
| `scanner/pipeline/snapshot.py` | 2 | 22 | 24 | 🔴 High |
| `scanner/utils/raw_collector.py` | 4 | 15 | 19 | 🔴 High |
| `scanner/pipeline/ohlcv.py` | 1 | 15 | 16 | 🔴 High |
| `scanner/pipeline/global_ranking.py` | 4 | 11 | 15 | 🔴 High |
| `scanner/utils/io_utils.py` | 5 | 10 | 15 | 🔴 High |
| `scanner/utils/logging_utils.py` | 1 | 14 | 15 | 🔴 High |
| `scanner/pipeline/shortlist.py` | 1 | 11 | 12 | 🔴 High |
| `scanner/tools/validate_features.py` | 3 | 6 | 9 | 🔴 High |
| `scanner/utils/time_utils.py` | 2 | 7 | 9 | 🔴 High |
| `scanner/pipeline/scoring/weights.py` | 0 | 8 | 8 | 🔴 High |
| `scanner/utils/save_raw.py` | 0 | 8 | 8 | 🔴 High |
| `scanner/main.py` | 2 | 5 | 7 | 🔴 High |
| `scanner/pipeline/regime.py` | 2 | 5 | 7 | 🔴 High |
| `scanner/pipeline/discovery.py` | 1 | 5 | 6 | 🔴 High |
| `scanner/pipeline/scoring/decision_inputs.py` | 0 | 5 | 5 | 🔴 High |
| `scanner/pipeline/cross_section.py` | 0 | 3 | 3 | 🔴 High |

**Interpretation:**
- ✅ **Low coupling:** Module is self-contained, easy to maintain
- ⚠️ **Medium coupling:** Some external dependencies, acceptable
- 🔴 **High coupling:** Many external calls, consider refactoring


---

## 📚 Additional Documentation

- **Specifications:** `docs/spec.md` (technical master spec)
- **Development Guide:** `docs/dev_guide.md` (workflow)
- **GPT Snapshot:** `docs/GPT_SNAPSHOT.md` (complete codebase)
- **Latest Reports:** `reports/YYYY-MM-DD.md` (daily outputs)

---

_Generated by GitHub Actions • 2026-03-14 20:24 UTC_
