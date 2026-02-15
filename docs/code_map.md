# 📘 Code Map — Automatically Generated

**Repository:** schluchtenscheisser/spot-altcoin-scanner  
**Last Updated:** 2026-02-15 11:19 UTC  
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

- **Total Modules:** 29
- **Total Classes:** 16
- **Total Functions:** 150

---

## 🧩 Module Structure

### 📄 `scanner/__init__.py`

**Functions:** —

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

**Functions:** `__init__, _rate_limit, _request, get_24h_tickers, get_exchange_info, get_klines, get_multiple_klines, get_spot_usdt_symbols`

**Module Variables:** `BASE_URL, cache_key, data, elapsed, exchange_info, logger, params, response, results, retry_after` _(+3 more)_

**Imports:** `requests, time, typing, utils.io_utils, utils.logging_utils`

---

### 📄 `scanner/config.py`

**Classes:** `ScannerConfig`

**Functions:** `cmc_api_key, config_version, exclude_leveraged, exclude_stablecoins, exclude_wrapped, load_config, log_file, log_level, log_to_file, lookback_days_1d, lookback_days_4h, market_cap_max, market_cap_min, mexc_enabled, min_history_days_1d, min_quote_volume_24h, run_mode, shortlist_size, spec_version, timezone, validate_config`

**Module Variables:** `CONFIG_PATH, cfg_path, env_var, errors, raw, valid_modes`

**Imports:** `dataclasses, os, pathlib, typing, yaml`

---

### 📄 `scanner/main.py`

**Functions:** `main, parse_args`

**Module Variables:** `args, cfg, parser`

**Imports:** `__future__, argparse, config, pipeline, sys`

---

### 📄 `scanner/pipeline/__init__.py`

**Functions:** `run_pipeline`

**Module Variables:** `asof_dt, asof_iso, asof_ts_ms, breakout_results, cmc, cmc_listings, cmc_listings_ts_utc, cmc_symbol_map, exchange_info, exchange_info_ts_utc` _(+33 more)_

**Imports:** `__future__, clients.mapping, clients.marketcap_client, clients.mexc_client, config, features, filters, logging` _(+9 more)_

---

### 📄 `scanner/pipeline/backtest_runner.py`

**Functions:** —

---

### 📄 `scanner/pipeline/excel_output.py`

**Classes:** `ExcelReportGenerator`

**Functions:** `__init__, _create_setup_sheet, _create_summary_sheet, _format_large_number, generate_excel_report`

**Module Variables:** `cell, col_letter, comp_key, comp_value, components, excel_path, flag_str, flags, flags_col, headers` _(+9 more)_

**Imports:** `datetime, logging, openpyxl, openpyxl.styles, openpyxl.utils, pathlib, typing`

---

### 📄 `scanner/pipeline/features.py`

**Classes:** `FeatureEngine`

**Functions:** `__init__, _calc_atr_pct, _calc_breakout_distance, _calc_drawdown, _calc_ema, _calc_quote_volume_features, _calc_return, _calc_sma, _calc_volume_spike, _compute_timeframe_features, _config_get, _convert_to_native_types, _detect_base, _detect_higher_high, _detect_higher_low, _get_last_closed_idx, _get_volume_period_for_timeframe, compute_all`

**Module Variables:** `alpha, ath, atr, base_features, base_low, base_score, close_time, closes, converted, current` _(+45 more)_

**Imports:** `logging, numpy, typing`

---

### 📄 `scanner/pipeline/filters.py`

**Classes:** `UniverseFilters`

**Functions:** `__init__, _filter_exclusions, _filter_liquidity, _filter_mcap, apply_all, get_filter_stats`

**Module Variables:** `base, default_patterns, exclusion_pass, exclusions_cfg, filtered, final_pass, history_cfg, is_excluded, legacy_filters, liquidity_pass` _(+9 more)_

**Imports:** `logging, typing`

---

### 📄 `scanner/pipeline/ohlcv.py`

**Classes:** `OHLCVFetcher`

**Functions:** `__init__, fetch_all, get_fetch_stats`

**Module Variables:** `candles, collect_raw_ohlcv, date_range, failed, first_symbol, general_cfg, history_cfg, klines, limit, logger` _(+12 more)_

**Imports:** `datetime, logging, scanner.utils.raw_collector, typing`

---

### 📄 `scanner/pipeline/output.py`

**Classes:** `ReportGenerator`

**Functions:** `__init__, _format_setup_entry, generate_json_report, generate_markdown_report, save_reports`

**Module Variables:** `analysis, coin_name, components, excel_config, excel_gen, excel_path, flag_list, flag_str, flags, json_content` _(+18 more)_

**Imports:** `datetime, excel_output, json, logging, pathlib, typing`

---

### 📄 `scanner/pipeline/runtime_market_meta.py`

**Classes:** `RuntimeMarketMetaExporter`

**Functions:** `__init__, _build_exchange_symbol_map, _build_identity, _build_quality, _build_symbol_info, _build_ticker, _extract_filter_value, _to_float, _to_int, export`

**Module Variables:** `ask, bid, cmc_data, exchange_symbol, exchange_symbol_map, fdv, fdv_to_mcap, identity, logger, mapping` _(+21 more)_

**Imports:** `__future__, clients.mapping, config, logging, pathlib, typing, utils.io_utils, utils.time_utils`

---

### 📄 `scanner/pipeline/scoring/__init__.py`

**Functions:** —

---

### 📄 `scanner/pipeline/scoring/breakout.py`

**Classes:** `BreakoutScorer`

**Functions:** `__init__, _generate_reasons, _score_breakout, _score_momentum, _score_trend, _score_volume, score, score_breakouts`

**Module Variables:** `breakout_curve, breakout_dist, breakout_score, default_weights, denom, dist, dist_ema20, dist_ema50, f1d, f4h` _(+25 more)_

**Imports:** `logging, scanner.pipeline.scoring.weights, typing`

---

### 📄 `scanner/pipeline/scoring/pullback.py`

**Classes:** `PullbackScorer`

**Functions:** `__init__, _generate_reasons, _score_pullback, _score_rebound, _score_trend, _score_volume, score, score_pullbacks`

**Module Variables:** `default_weights, dist_ema20, dist_ema50, f1d, f4h, final_score, flags, logger, max_spike, momentum_cfg` _(+23 more)_

**Imports:** `logging, scanner.pipeline.scoring.weights, typing`

---

### 📄 `scanner/pipeline/scoring/reversal.py`

**Classes:** `ReversalScorer`

**Functions:** `__init__, _generate_reasons, _score_base, _score_drawdown, _score_reclaim, _score_volume, score, score_reversals`

**Module Variables:** `base_score, dd, dd_pct, default_weights, dist_ema20, dist_ema50, drawdown_score, excess, f1d, f4h` _(+26 more)_

**Imports:** `logging, math, scanner.pipeline.scoring.weights, typing`

---

### 📄 `scanner/pipeline/scoring/weights.py`

**Functions:** `load_component_weights`

**Module Variables:** `alias_key, alias_present, canonical_present, cfg_weights, logger, missing, mode, total`

**Imports:** `logging, typing`

---

### 📄 `scanner/pipeline/shortlist.py`

**Classes:** `ShortlistSelector`

**Functions:** `__init__, get_shortlist_stats, select`

**Module Variables:** `coverage, general_cfg, logger, max_vol, min_vol, shortlist, shortlist_volume, sorted_symbols, total_volume`

**Imports:** `logging, typing`

---

### 📄 `scanner/pipeline/snapshot.py`

**Classes:** `SnapshotManager`

**Functions:** `__init__, create_snapshot, get_snapshot_stats, list_snapshots, load_snapshot`

**Module Variables:** `date, logger, size_mb, snapshot, snapshot_config, snapshot_path, snapshots`

**Imports:** `datetime, json, logging, pathlib, typing`

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

**Functions:** `collect_raw_features, collect_raw_marketcap, collect_raw_ohlcv`

**Module Variables:** `df, flat_records`

**Imports:** `json, pandas, scanner.utils.save_raw, typing`

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
| `get_spot_usdt_symbols` | `get_exchange_info` | `append`, `get`, `info` |

### 📄 scanner/config.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `cmc_api_key` | — | `get`, `getenv` |
| `config_version` | — | `get` |
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
| `min_quote_volume_24h` | — | `get` |
| `run_mode` | — | `get` |
| `shortlist_size` | — | `get` |
| `spec_version` | — | `get` |
| `timezone` | — | `get` |
| `validate_config` | — | `append` |

### 📄 scanner/main.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `main` | `parse_args` | `load_config`, `run_pipeline`, `setdefault` |
| `parse_args` | `parse_args` | `ArgumentParser`, `add_argument` |

### 📄 scanner/pipeline/__init__.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `run_pipeline` | — | `FeatureEngine`, `MEXCClient`, `MarketCapClient`, `OHLCVFetcher`, `ReportGenerator`, `RuntimeMarketMetaExporter`, `ShortlistSelector`, `SnapshotManager`, `SymbolMapper`, `UniverseFilters`, `_get_market_cap`, `append`, `apply_all`, `build_symbol_map`, `compute_all`, `create_snapshot`, `export`, `fetch_all`, `get`, `get_24h_tickers`, `get_exchange_info`, `get_listings`, `info`, `keys`, `map_symbol`, `map_universe`, `replace`, `save_reports`, `score_breakouts`, `score_pullbacks`, `score_reversals`, `select`, `strftime`, `timestamp_to_ms`, `utc_now` |

### 📄 scanner/pipeline/excel_output.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Path`, `get`, `info`, `mkdir` |
| `_create_setup_sheet` | `_format_large_number` | `Alignment`, `Font`, `PatternFill`, `cell`, `create_sheet`, `get`, `get_column_letter`, `items`, `join`, `lower` |
| `_create_summary_sheet` | — | `Alignment`, `Font`, `PatternFill`, `create_sheet`, `get`, `strftime`, `utcnow` |
| `generate_excel_report` | `_create_setup_sheet`, `_create_summary_sheet` | `Workbook`, `info`, `remove`, `save` |

### 📄 scanner/pipeline/features.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `info` |
| `_calc_atr_pct` | — | `nanmean`, `warning` |
| `_calc_breakout_distance` | — | `error`, `nanmax`, `warning` |
| `_calc_drawdown` | — | `nanmax` |
| `_calc_ema` | — | `nanmean`, `warning` |
| `_calc_quote_volume_features` | `_calc_sma`, `_calc_volume_spike` | `isnan` |
| `_calc_return` | — | `error`, `warning` |
| `_calc_sma` | — | `nanmean` |
| `_calc_volume_spike` | — | `isnan`, `warning` |
| `_compute_timeframe_features` | `_calc_atr_pct`, `_calc_breakout_distance`, `_calc_drawdown`, `_calc_ema`, `_calc_quote_volume_features`, `_calc_return`, `_calc_sma`, `_calc_volume_spike`, `_config_get`, `_convert_to_native_types`, `_detect_base`, `_detect_higher_high`, `_detect_higher_low`, `_get_volume_period_for_timeframe` | `array`, `get`, `update`, `warning` |
| `_config_get` | — | `get` |
| `_convert_to_native_types` | — | `isnan`, `items` |
| `_detect_base` | `_config_get` | `isnan`, `nanmax`, `nanmin`, `warning` |
| `_detect_higher_high` | — | `nanmax` |
| `_detect_higher_low` | — | `nanmin` |
| `_get_volume_period_for_timeframe` | `_config_get` | `get`, `warning` |
| `compute_all` | `_compute_timeframe_features`, `_get_last_closed_idx` | `debug`, `error`, `get`, `info`, `items` |

### 📄 scanner/pipeline/filters.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `extend`, `get`, `info`, `upper` |
| `_filter_exclusions` | — | `append`, `get`, `upper` |
| `_filter_liquidity` | — | `append`, `get` |
| `_filter_mcap` | — | `append`, `get` |
| `apply_all` | `_filter_exclusions`, `_filter_liquidity`, `_filter_mcap` | `info` |
| `get_filter_stats` | `_filter_exclusions`, `_filter_liquidity`, `_filter_mcap`, `apply_all` | — |

### 📄 scanner/pipeline/ohlcv.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `info` |
| `fetch_all` | — | `collect_raw_ohlcv`, `error`, `get`, `get_klines`, `info`, `warning` |
| `get_fetch_stats` | — | `fromtimestamp`, `keys`, `strftime`, `values` |

### 📄 scanner/pipeline/output.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Path`, `get`, `info`, `mkdir` |
| `_format_setup_entry` | — | `append`, `capitalize`, `get`, `items`, `join`, `replace` |
| `generate_json_report` | — | `isoformat`, `update`, `utcnow` |
| `generate_markdown_report` | `_format_setup_entry` | `append`, `extend`, `join`, `strftime`, `utcnow` |
| `save_reports` | `generate_json_report`, `generate_markdown_report` | `ExcelReportGenerator`, `dump`, `error`, `generate_excel_report`, `info`, `warning`, `write` |

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
| `export` | `_build_exchange_symbol_map`, `_build_identity`, `_build_quality`, `_build_symbol_info`, `_build_ticker` | `get`, `info`, `keys`, `save_json`, `strftime`, `utc_now` |

### 📄 scanner/pipeline/scoring/breakout.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `load_component_weights` |
| `_generate_reasons` | — | `append`, `get` |
| `_score_breakout` | — | `get` |
| `_score_momentum` | — | `get` |
| `_score_trend` | — | `get` |
| `_score_volume` | — | `get` |
| `score` | `_generate_reasons`, `_score_breakout`, `_score_momentum`, `_score_trend`, `_score_volume` | `append`, `get` |
| `score_breakouts` | `score` | `BreakoutScorer`, `append`, `error`, `get`, `items`, `sort` |

### 📄 scanner/pipeline/scoring/pullback.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `load_component_weights` |
| `_generate_reasons` | — | `append`, `get` |
| `_score_pullback` | — | `get` |
| `_score_rebound` | — | `get` |
| `_score_trend` | — | `get` |
| `_score_volume` | — | `get` |
| `score` | `_generate_reasons`, `_score_pullback`, `_score_rebound`, `_score_trend`, `_score_volume` | `append`, `get` |
| `score_pullbacks` | `score` | `PullbackScorer`, `append`, `error`, `get`, `items`, `sort` |

### 📄 scanner/pipeline/scoring/reversal.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `load_component_weights` |
| `_generate_reasons` | — | `append`, `get` |
| `_score_base` | — | `get`, `isfinite` |
| `_score_drawdown` | — | `get` |
| `_score_reclaim` | — | `get` |
| `_score_volume` | — | `get` |
| `score` | `_generate_reasons`, `_score_base`, `_score_drawdown`, `_score_reclaim`, `_score_volume` | `append`, `get` |
| `score_reversals` | `score` | `ReversalScorer`, `append`, `error`, `get`, `items`, `sort` |

### 📄 scanner/pipeline/scoring/weights.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `load_component_weights` | — | `copy`, `get`, `items`, `join`, `lower`, `strip`, `values`, `warning` |

### 📄 scanner/pipeline/shortlist.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `get`, `info` |
| `get_shortlist_stats` | — | `get` |
| `select` | — | `get`, `info`, `warning` |

### 📄 scanner/pipeline/snapshot.py

| Calling Function | Internal Calls | External Calls |
|------------------|----------------|----------------|
| `__init__` | — | `Path`, `get`, `info`, `mkdir` |
| `create_snapshot` | — | `dump`, `info`, `isoformat`, `stat`, `strftime`, `timestamp`, `update`, `utcnow` |
| `get_snapshot_stats` | `load_snapshot` | — |
| `list_snapshots` | — | `append`, `glob`, `info`, `sort` |
| `load_snapshot` | — | `FileNotFoundError`, `exists`, `info`, `load` |

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
| `collect_raw_features` | — | `save_raw_snapshot` |
| `collect_raw_marketcap` | — | `dumps`, `json_normalize`, `save_raw_snapshot` |
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
| `scanner/pipeline/features.py` | 20 | 35 | 55 | 🔴 High |
| `scanner/pipeline/__init__.py` | 0 | 35 | 35 | 🔴 High |
| `scanner/clients/mexc_client.py` | 6 | 28 | 34 | 🔴 High |
| `scanner/clients/marketcap_client.py` | 4 | 27 | 31 | 🔴 High |
| `scanner/pipeline/runtime_market_meta.py` | 12 | 17 | 29 | ⚠️ Medium |
| `scanner/pipeline/excel_output.py` | 3 | 25 | 28 | 🔴 High |
| `scanner/pipeline/output.py` | 3 | 25 | 28 | 🔴 High |
| `scanner/config.py` | 0 | 26 | 26 | 🔴 High |
| `scanner/clients/mapping.py` | 4 | 21 | 25 | 🔴 High |
| `scanner/pipeline/scoring/reversal.py` | 6 | 17 | 23 | 🔴 High |
| `scanner/pipeline/scoring/breakout.py` | 6 | 16 | 22 | 🔴 High |
| `scanner/pipeline/scoring/pullback.py` | 6 | 16 | 22 | 🔴 High |
| `scanner/pipeline/snapshot.py` | 1 | 20 | 21 | 🔴 High |
| `scanner/pipeline/filters.py` | 7 | 12 | 19 | 🔴 High |
| `scanner/utils/io_utils.py` | 5 | 10 | 15 | 🔴 High |
| `scanner/utils/logging_utils.py` | 1 | 14 | 15 | 🔴 High |
| `scanner/pipeline/ohlcv.py` | 0 | 12 | 12 | 🔴 High |
| `scanner/tools/validate_features.py` | 3 | 6 | 9 | 🔴 High |
| `scanner/utils/time_utils.py` | 2 | 7 | 9 | 🔴 High |
| `scanner/pipeline/scoring/weights.py` | 0 | 8 | 8 | 🔴 High |
| `scanner/utils/raw_collector.py` | 0 | 8 | 8 | 🔴 High |
| `scanner/utils/save_raw.py` | 0 | 8 | 8 | 🔴 High |
| `scanner/main.py` | 2 | 5 | 7 | 🔴 High |
| `scanner/pipeline/shortlist.py` | 0 | 6 | 6 | 🔴 High |

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

_Generated by GitHub Actions • 2026-02-15 11:19 UTC_
