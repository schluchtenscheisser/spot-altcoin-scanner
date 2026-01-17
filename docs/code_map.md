# Code Map - Spot Altcoin Scanner
Version: v1.0  
Last Updated: 2026-01-17  
Status: MVP Complete  
Based on: Actual codebase analysis

---

## Purpose

This Code Map provides a **complete structural index** of the Spot Altcoin Scanner codebase. It documents all classes, functions, and their relationships based on the actual implementation.

**Update Protocol:** This file should be updated when modules are added/removed or class/function signatures change significantly.

---

## Repository Structure

```
spot-altcoin-scanner/
├── scanner/              # Main package
│   ├── __init__.py
│   ├── main.py          # CLI entry point
│   ├── config.py        # Configuration management
│   ├── clients/         # API clients
│   ├── pipeline/        # Core pipeline
│   ├── utils/           # Utilities
├── config/              # Configuration files
├── data/                # Data storage (cached)
├── docs/                # Documentation
├── logs/                # Runtime logs
├── reports/             # Scanner outputs
├── snapshots/           # Runtime + GPT snapshots
├── tests/               # Test suite
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Core Package: `scanner/`

### Package Initialization

**`scanner/__init__.py`**
- Type: Package initialization
- Content: Minimal (docstring only)
- Docstring: "Spot Altcoin Scanner package. See /docs/spec.md for full specification."

---

### Entry Point & Configuration

**`scanner/main.py`**
- **Purpose:** CLI entry point and pipeline orchestration
- **Functions:**
  - `parse_args(argv: list[str] | None) -> argparse.Namespace`
    - Parses command-line arguments
    - Supports `--mode` flag: standard, fast, offline, backtest
  - `main(argv: list[str] | None) -> int`
    - Main entry point
    - Loads config, overrides mode if specified
    - Calls `run_pipeline()`
    - Returns exit code
- **Dependencies:**
  - `scanner.config.load_config`
  - `scanner.pipeline.run_pipeline`
- **Usage:** `python -m scanner.main --mode fast`

**`scanner/config.py`**
- **Purpose:** Configuration loading and validation
- **Classes:**
  - `ScannerConfig` (dataclass)
    - Properties (all return types from config):
      - Version: `spec_version`, `config_version`
      - General: `run_mode`, `timezone`, `shortlist_size`, `lookback_days_1d`, `lookback_days_4h`
      - Data Sources: `mexc_enabled`, `cmc_api_key`
      - Filters: `market_cap_min`, `market_cap_max`, `min_quote_volume_24h`, `min_history_days_1d`
      - Exclusions: `exclude_stablecoins`, `exclude_wrapped`, `exclude_leveraged`
      - Logging: `log_level`, `log_to_file`, `log_file`
    - Stores raw config dict in `raw` attribute
- **Functions:**
  - `load_config(path: str | Path | None) -> ScannerConfig`
    - Loads YAML config from file
    - Returns ScannerConfig instance
    - Raises: FileNotFoundError, yaml.YAMLError
  - `validate_config(config: ScannerConfig) -> List[str]`
    - Validates configuration values
    - Returns list of error messages (empty if valid)
- **Constants:**
  - `CONFIG_PATH = "config/config.yml"` (overridable via env var)

---

## Utilities: `scanner/utils/`

### Package Initialization

**`scanner/utils/__init__.py`**
- Type: Package initialization
- Content: Minimal (docstring only)
- Modules: time_utils, logging_utils, io_utils

### Time Utilities

**`scanner/utils/time_utils.py`**
- **Purpose:** UTC-based time and date handling
- **Functions:**
  - `utc_now() -> datetime` - Current UTC time (timezone-aware)
  - `utc_timestamp() -> str` - ISO timestamp (YYYY-MM-DDTHH:MM:SSZ)
  - `utc_date() -> str` - Date string (YYYY-MM-DD)
  - `parse_timestamp(ts: str) -> datetime` - Parse ISO timestamp
  - `timestamp_to_ms(dt: datetime) -> int` - Convert to milliseconds (for APIs)
  - `ms_to_timestamp(ms: int) -> datetime` - Convert from milliseconds

### Logging Utilities

**`scanner/utils/logging_utils.py`**
- **Purpose:** Centralized logging with rotation
- **Functions:**
  - `setup_logger(name, level, log_file, log_to_console, log_to_file) -> logging.Logger`
    - Creates configured logger
    - Supports file rotation (10MB, 5 backups)
    - Format: `YYYY-MM-DD HH:MM:SS | LEVEL | NAME | MESSAGE`
  - `get_logger(name: str) -> logging.Logger`
    - Gets existing logger or creates default

### I/O Utilities

**`scanner/utils/io_utils.py`**
- **Purpose:** File I/O and caching helpers
- **Functions:**
  - `load_json(filepath) -> dict | list` - Load JSON file
  - `save_json(data, filepath, indent=2)` - Save JSON file
  - `get_cache_path(cache_type, date) -> Path` - Get standardized cache path
    - Location: `data/raw/YYYY-MM-DD/`
  - `cache_exists(cache_type, date) -> bool` - Check if cache exists
  - `load_cache(cache_type, date) -> Optional[dict | list]` - Load cached data
  - `save_cache(data, cache_type, date)` - Save data to cache

---

## API Clients: `scanner/clients/`

### Package Initialization

**`scanner/clients/__init__.py`**
- Type: Package initialization
- Content: Empty

### MEXC Client

**`scanner/clients/mexc_client.py`**
- **Purpose:** MEXC Spot API client with rate limiting and caching
- **Classes:**
  - `MEXCClient`
    - **Constants:**
      - `BASE_URL = "https://api.mexc.com"`
    - **Initialization:**
      - `__init__(max_retries=3, retry_backoff=3.0, timeout=30)`
      - Rate limiting: 100ms between requests
    - **Methods:**
      - `_rate_limit()` - Apply rate limiting between requests
      - `_request(method, endpoint, params) -> Dict` - HTTP request with retry logic
        - Handles 429 (rate limit) with exponential backoff
        - Max retries: 3 (configurable)
      - `get_exchange_info(use_cache=True) -> Dict` - Get exchange info (symbols, rules)
      - `get_spot_usdt_symbols(use_cache=True) -> List[str]` - Get all USDT Spot pairs
        - Filters: quoteAsset=USDT, isSpotTradingAllowed=True, status="1"
        - Returns: List of symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
      - `get_24h_tickers(use_cache=True) -> List[Dict]` - Bulk 24h ticker data
      - `get_klines(symbol, interval='1d', limit=120, use_cache=True) -> List[List]` - OHLCV data
        - Intervals: 1m, 5m, 15m, 1h, 4h, 1d, 1w
        - Format: [openTime, open, high, low, close, volume, closeTime, quoteVolume, ...]
      - `get_multiple_klines(symbols, interval, limit, use_cache) -> Dict[str, List]` - Bulk klines
- **Caching:**
  - Cache keys: `mexc_exchange_info`, `mexc_24h_tickers`, `mexc_klines_{symbol}_{interval}`
  - Daily cache invalidation

### CoinMarketCap Client

**`scanner/clients/marketcap_client.py`**
- **Purpose:** CoinMarketCap API client for market cap data
- **Classes:**
  - `MarketCapClient`
    - **Constants:**
      - `BASE_URL = "https://pro-api.coinmarketcap.com"`
    - **Initialization:**
      - `__init__(api_key=None, timeout=30)`
      - API key from: parameter > CMC_API_KEY env var
    - **Methods:**
      - `_request(endpoint, params) -> Dict` - API request
        - Handles 429 (rate limit)
        - Extracts 'data' field from response
      - `get_listings(start=1, limit=5000, use_cache=True) -> List[Dict]` - Get cryptocurrency listings
        - Sorted by market cap (descending)
        - Returns: List with id, symbol, name, slug, cmc_rank, quote.USD.market_cap, etc.
      - `get_all_listings(use_cache=True) -> List[Dict]` - Get all listings (up to 5000)
      - `build_symbol_map(listings) -> Dict[str, Dict]` - Build symbol → data mapping
        - Handles collisions (keeps higher-ranked)
        - Returns: Dict mapping uppercase symbol to CMC data
      - `get_market_cap_for_symbol(symbol, symbol_map) -> Optional[float]` - Get market cap for symbol
- **Caching:**
  - Cache key: `cmc_listings_start{start}_limit{limit}`
  - Daily cache invalidation

### Symbol Mapping

**`scanner/clients/mapping.py`**
- **Purpose:** Maps MEXC symbols to CMC market cap data (CRITICAL component)
- **Classes:**
  - `MappingResult`
    - **Initialization:**
      - `__init__(mexc_symbol, cmc_data, confidence, method, collision, notes)`
    - **Properties:**
      - `mapped: bool` - Was mapping successful?
      - `base_asset: str` - Extracted base (e.g., BTCUSDT → BTC)
    - **Methods:**
      - `to_dict() -> Dict` - Convert to dict for serialization
      - `_get_market_cap() -> Optional[float]` - Extract market cap from CMC data
  
  - `SymbolMapper`
    - **Initialization:**
      - `__init__(overrides_file="config/mapping_overrides.json")`
      - Loads manual overrides from JSON file
      - Initializes stats tracking
    - **Stats Structure:**
      ```python
      {
          "total": 0,
          "mapped": 0,
          "unmapped": 0,
          "collisions": 0,
          "overrides_used": 0,
          "confidence": {"high": 0, "medium": 0, "low": 0, "none": 0}
      }
      ```
    - **Methods:**
      - `_load_overrides() -> Dict` - Load manual mapping overrides
      - `map_symbol(mexc_symbol, cmc_symbol_map) -> MappingResult` - Map single symbol
        - Confidence levels: high, medium, low, none
        - Methods: override_exclude, override_match, symbol_exact_match, no_match
        - Override format: `{"BTC": "BTC"}` or `{"SYMBOL": "exclude"}`
      - `map_universe(mexc_symbols, cmc_symbol_map) -> Dict[str, MappingResult]` - Map entire universe
        - Returns: Dict mapping mexc_symbol → MappingResult
        - Updates internal stats
      - `generate_reports(mapping_results, output_dir="reports")` - Generate mapping reports
        - Creates: unmapped_symbols.json, mapping_collisions.json, mapping_stats.json
      - `suggest_overrides(mapping_results, output_file) -> Dict[str, str]` - Generate override suggestions
- **Current Performance:**
  - Mapping success: 88.4% (1624/1837)
  - Override file: Empty by design (213 unmapped are low-volume/new tokens)

---

## Pipeline: `scanner/pipeline/`

### Pipeline Orchestration

**`scanner/pipeline/__init__.py`**
- **Purpose:** Orchestrates the complete 10-step daily pipeline
- **Functions:**
  - `run_pipeline(config: ScannerConfig) -> None`
    - **Steps:**
      1. Initialize clients (MEXC, CMC)
      2. Fetch MEXC universe (1837 USDT pairs)
      3. Fetch 24h tickers
      4. Fetch CMC listings + map symbols
      5. Apply universe filters (market cap, liquidity, exclusions)
      6. Create shortlist (top N by volume)
      7. Fetch OHLCV data (1d + 4h)
      8. Compute features
      9. Score setups (Reversal, Breakout, Pullback)
      10. Generate reports + snapshot
    - **Mode-dependent behavior:**
      - standard: Fresh API calls
      - fast: Use cache when available
      - offline: Cache-only (no API calls)
      - backtest: TBD (Phase 7)
- **Dependencies:**
  - All client modules
  - All pipeline modules
  - All scoring modules

### Universe Filtering

**`scanner/pipeline/filters.py`**
- **Purpose:** Filter MEXC universe to tradable MidCaps
- **Classes:**
  - `UniverseFilters`
    - **Initialization:**
      - `__init__(config: Dict)`
      - Defaults: 100M-3B MCAP, 1M min volume
    - **Filter Parameters:**
      - `mcap_min`: 100,000,000 USD (100M)
      - `mcap_max`: 3,000,000,000 USD (3B)
      - `min_volume_24h`: 1,000,000 USDT (1M)
      - `exclusion_patterns`: Stablecoins, wrapped tokens, leveraged tokens
    - **Methods:**
      - `apply_all(symbols_with_data) -> List[Dict]` - Apply all filters in sequence
        - Input format: List of dicts with symbol, base, quote_volume_24h, market_cap
        - Pipeline: MCAP filter → Liquidity filter → Exclusions filter
      - `_filter_mcap(symbols) -> List[Dict]` - Filter by market cap range
      - `_filter_liquidity(symbols) -> List[Dict]` - Filter by minimum 24h volume
      - `_filter_exclusions(symbols) -> List[Dict]` - Exclude by pattern matching
      - `get_filter_stats(symbols) -> Dict` - Get filter statistics
- **Typical Results:**
  - Input: 1837 symbols
  - After filters: ~300-400 symbols (varies daily)

### Shortlist Selection

**`scanner/pipeline/shortlist.py`**
- **Purpose:** Reduce filtered universe to shortlist for OHLCV fetching (cheap pass)
- **Classes:**
  - `ShortlistSelector`
    - **Initialization:**
      - `__init__(config: Dict)`
      - Defaults: max_size=100, min_size=10
    - **Methods:**
      - `select(filtered_symbols) -> List[Dict]` - Select top N by 24h volume
        - Sorts by quote_volume_24h (descending)
        - Returns top N symbols
      - `get_shortlist_stats(filtered_symbols, shortlist) -> Dict` - Get selection statistics
        - Returns: input_count, shortlist_count, reduction_rate, volume_coverage

### OHLCV Data Fetching

**`scanner/pipeline/ohlcv.py`**
- **Purpose:** Fetch OHLCV data for shortlisted symbols
- **Classes:**
  - `OHLCVFetcher`
    - **Initialization:**
      - `__init__(mexc_client, config: Dict)`
      - Defaults: timeframes=['1d', '4h'], lookback={'1d': 120, '4h': 180}
      - Min candles: {'1d': 60, '4h': 90}
    - **Methods:**
      - `fetch_all(shortlist) -> Dict[str, Dict[str, Any]]` - Fetch OHLCV for all symbols
        - Returns: {symbol: {timeframe: klines}}
        - Skips symbols with insufficient data
        - Only includes symbols with complete data across all timeframes
      - `get_fetch_stats(ohlcv_data) -> Dict` - Get fetch statistics
- **Typical Results:**
  - Input: 100 symbols (shortlist)
  - Output: ~90-98 symbols (with complete OHLCV)
  - Skipped: ~2-10 symbols (insufficient history)

### Feature Computation

**`scanner/pipeline/features.py`**
- **Purpose:** Compute technical features from OHLCV data
- **Classes:**
  - `FeatureEngine`
    - **Initialization:**
      - `__init__(config: Dict)`
    - **Methods:**
      - `compute_all(ohlcv_data) -> Dict[str, Dict[str, Any]]` - Compute features for all symbols
        - Returns: {symbol: {'1d': {...}, '4h': {...}, 'meta': {...}}}
      - `_compute_timeframe_features(klines, timeframe) -> Dict` - Compute features for single timeframe
      - `_convert_to_native_types(features) -> Dict` - Convert numpy types to Python native
      - Feature calculation methods:
        - `_calc_return(closes, periods) -> float` - Return over N periods (%)
        - `_calc_ema(data, period) -> float` - Exponential Moving Average
        - `_calc_sma(data, period) -> float` - Simple Moving Average
        - `_calc_atr_pct(highs, lows, closes, period) -> float` - ATR as % of price
        - `_detect_higher_high(highs, lookback) -> bool` - Higher high detection
        - `_detect_higher_low(lows, lookback) -> bool` - Higher low detection
        - `_calc_breakout_distance(closes, highs, lookback) -> float` - Distance to breakout (%)
        - `_calc_drawdown(closes) -> float` - Drawdown from ATH (%)
        - `_detect_base(closes, lows, lookback) -> bool` - Base formation detection (1d only)
- **Features Computed (1d timeframe):**
  - Price: close, high, low, volume
  - Returns: r_1, r_3, r_7 (1d, 3d, 7d returns in %)
  - EMAs: ema_20, ema_50
  - EMA Distance: dist_ema20_pct, dist_ema50_pct
  - Volatility: atr_pct (14-period ATR as %)
  - Volume: volume_sma_14, volume_spike (vs 14-period SMA)
  - Structure: hh_20, hl_20 (higher high/low detection)
  - Breakout: breakout_dist_20, breakout_dist_30 (distance to 20d/30d high)
  - Drawdown: drawdown_from_ath (% from all-time high)
  - Base: base_detected (consolidation without new lows)
- **Features Computed (4h timeframe):**
  - Same as 1d except: no base_detected (None)
- **Important:** All numpy types converted to Python native for JSON serialization

### Scoring Modules

#### Scoring Package Initialization

**`scanner/pipeline/scoring/__init__.py`**
- Type: Package initialization
- Content: Minimal (docstring only)
- Modules: breakout.py, pullback.py, reversal.py
- Note: Three independent scoring modules

#### Reversal Setup Scorer

**`scanner/pipeline/scoring/reversal.py`**
- **Purpose:** Score downtrend → base → reclaim setups (PRIORITY setup)
- **Pattern:** Humanity Protocol style reversal
- **Classes:**
  - `ReversalScorer`
    - **Initialization:**
      - `__init__(config: Dict)`
      - Config section: `scoring.reversal`
    - **Thresholds:**
      - `min_drawdown`: 40% (minimum drawdown to consider)
      - `ideal_drawdown_min`: 50% (ideal range start)
      - `ideal_drawdown_max`: 80% (ideal range end)
      - `min_base_days`: 10 (minimum consolidation days)
      - `min_volume_spike`: 1.5x (minimum volume spike)
      - `overextension_threshold`: 15% (>15% above EMA50 = overextended)
    - **Component Weights:**
      - Drawdown: 30%
      - Base Quality: 25%
      - Reclaim Strength: 25%
      - Volume Confirmation: 20%
    - **Methods:**
      - `score(symbol, features, quote_volume_24h) -> Dict` - Score single symbol
        - Returns: {score, components, penalties, flags, reasons}
      - `_score_drawdown(f1d) -> float` - Score drawdown context (0-100)
        - Ideal: 50-80% from ATH
      - `_score_base(f1d) -> float` - Score base formation (0-100)
        - Checks: base_detected, ATR volatility
      - `_score_reclaim(f1d, f4h) -> float` - Score reclaim strength (0-100)
        - Checks: Above EMA20/50, higher highs, momentum
      - `_score_volume(f1d, f4h) -> float` - Score volume confirmation (0-100)
        - Uses max of 1d and 4h volume spikes
      - `_generate_reasons(...)  -> List[str]` - Generate human-readable reasons
    - **Penalties:**
      - Overextension: 0.7x (>15% above EMA50)
      - Low liquidity: 0.8x (<500K USDT)
- **Top-Level Function:**
  - `score_reversals(features_data, volumes, config) -> List[Dict]`
    - Scores all symbols, returns sorted list (descending)

#### Breakout Setup Scorer

**`scanner/pipeline/scoring/breakout.py`**
- **Purpose:** Score range breakouts with volume confirmation
- **Classes:**
  - `BreakoutScorer`
    - **Initialization:**
      - `__init__(config: Dict)`
      - Config section: `scoring.breakout`
    - **Thresholds:**
      - `min_breakout_pct`: 2% (>2% above recent high)
      - `ideal_breakout_pct`: 5% (ideal breakout distance)
      - `max_breakout_pct`: 20% (>20% = overextended)
      - `min_volume_spike`: 1.5x
      - `ideal_volume_spike`: 2.5x
    - **Component Weights:**
      - Breakout Distance: 35%
      - Volume Confirmation: 30%
      - Trend Context: 20%
      - Momentum: 15%
    - **Methods:**
      - `score(symbol, features, quote_volume_24h) -> Dict` - Score single symbol
      - `_score_breakout(f1d) -> float` - Score breakout distance (0-100)
      - `_score_volume(f1d, f4h) -> float` - Score volume confirmation (0-100)
      - `_score_trend(f1d) -> float` - Score trend context (0-100)
      - `_score_momentum(f1d) -> float` - Score momentum (0-100)
      - `_generate_reasons(...) -> List[str]` - Generate reasons
    - **Penalties:**
      - Overextension: 0.6x (>20% above high)
      - Low liquidity: 0.8x (<500K USDT)
- **Top-Level Function:**
  - `score_breakouts(features_data, volumes, config) -> List[Dict]`

#### Pullback Setup Scorer

**`scanner/pipeline/scoring/pullback.py`**
- **Purpose:** Score trend continuation after retracement
- **Classes:**
  - `PullbackScorer`
    - **Initialization:**
      - `__init__(config: Dict)`
      - Config section: `scoring.pullback`
    - **Thresholds:**
      - `min_trend_strength`: 5% (>5% above EMA50)
      - `ideal_pullback_depth`: 5% (5-10% from EMA20)
      - `max_pullback_depth`: 15% (<15% not too deep)
      - `min_rebound`: 3% (>3% bounce)
      - `min_volume_spike`: 1.3x
    - **Component Weights:**
      - Trend Strength: 30%
      - Pullback Depth: 25%
      - Rebound Strength: 25%
      - Volume Pattern: 20%
    - **Methods:**
      - `score(symbol, features, quote_volume_24h) -> Dict` - Score single symbol
      - `_score_trend(f1d) -> float` - Score trend strength (0-100)
      - `_score_pullback(f1d) -> float` - Score pullback depth (0-100)
      - `_score_rebound(f1d, f4h) -> float` - Score rebound strength (0-100)
      - `_score_volume(f1d, f4h) -> float` - Score volume pattern (0-100)
      - `_generate_reasons(...) -> List[str]` - Generate reasons
    - **Penalties:**
      - Broken trend: 0.5x (below EMA50)
      - Low liquidity: 0.8x (<500K USDT)
- **Top-Level Function:**
  - `score_pullbacks(features_data, volumes, config) -> List[Dict]`

### Output Generation

**`scanner/pipeline/output.py`**
- **Purpose:** Generate human-readable (Markdown) and machine-readable (JSON) reports
- **Classes:**
  - `ReportGenerator`
    - **Initialization:**
      - `__init__(config: Dict)`
      - Defaults: reports_dir='reports', top_n=10
    - **Methods:**
      - `generate_markdown_report(reversal, breakout, pullback, run_date) -> str`
        - Generates Markdown report with top N setups per type
        - Sections: Summary, Reversal, Breakout, Pullback, Notes
      - `_format_setup_entry(rank, entry) -> List[str]` - Format single setup entry
      - `generate_json_report(reversal, breakout, pullback, run_date, metadata) -> Dict`
        - Generates JSON report with meta, summary, setups
      - `save_reports(reversal, breakout, pullback, run_date, metadata) -> Dict[str, Path]`
        - Saves both Markdown and JSON reports
        - Returns: {'markdown': Path, 'json': Path}

### Snapshot Management

**`scanner/pipeline/snapshot.py`**
- **Purpose:** Create deterministic daily snapshots for backtesting
- **Classes:**
  - `SnapshotManager`
    - **Initialization:**
      - `__init__(config: Dict)`
      - Defaults: snapshots_dir='snapshots/runtime'
    - **Methods:**
      - `create_snapshot(run_date, universe, filtered, shortlist, features, reversal_scores, breakout_scores, pullback_scores, metadata) -> Path`
        - Creates complete pipeline snapshot
        - Returns: Path to saved snapshot file
      - `load_snapshot(run_date) -> Dict` - Load snapshot by date
      - `list_snapshots() -> List[str]` - List all available snapshot dates
      - `get_snapshot_stats(run_date) -> Dict` - Get snapshot statistics without loading full data
- **Typical Size:** ~245 KB per snapshot

### Backtesting

**`scanner/pipeline/backtest_runner.py`**
- **Status:** Stub (Phase 7 - not yet implemented)
- **Purpose:** Compute forward returns from historical snapshots
- **Planned Features:**
  - Consume historical snapshots
  - Compute forward returns (7/14/30 days)
  - Calculate hit rates, median/mean returns
  - Rank vs return behavior analysis
  - Output backtest summaries (JSON/Markdown)

---

## Module Dependencies

### Dependency Graph (High-Level)

```
main.py
  └─> config.py (load_config)
  └─> pipeline/__init__.py (run_pipeline)
       └─> clients/mexc_client.py (MEXCClient)
       └─> clients/marketcap_client.py (MarketCapClient)
       └─> clients/mapping.py (SymbolMapper)
       └─> filters.py (UniverseFilters)
       └─> shortlist.py (ShortlistSelector)
       └─> ohlcv.py (OHLCVFetcher)
       └─> features.py (FeatureEngine)
       └─> scoring/reversal.py (score_reversals)
       └─> scoring/breakout.py (score_breakouts)
       └─> scoring/pullback.py (score_pullbacks)
       └─> output.py (ReportGenerator)
       └─> snapshot.py (SnapshotManager)
```

### Utility Dependencies

All modules may import from:
- `utils/logging_utils.py` (get_logger)
- `utils/io_utils.py` (load_json, save_json, caching)
- `utils/time_utils.py` (utc_date, utc_timestamp)

---

## Key Statistics (as of 2026-01-17)

### Pipeline Performance
- **Universe:** 1837 MEXC USDT pairs
- **Mapped:** 1624 symbols (88.4%)
- **Filtered MidCaps:** ~300-400 symbols (varies daily)
- **Shortlist:** 100 symbols (configurable)
- **Complete OHLCV:** ~90-98 symbols
- **Scored Setups:** 3 independent scores per symbol
- **Execution Time:** ~4-5 minutes (with cache)
- **Snapshot Size:** ~245 KB

### Code Statistics
- **Total Modules:** 23 Python files
- **Total Classes:** 13
  - 3 API Clients (MEXCClient, MarketCapClient, SymbolMapper)
  - 2 Data Classes (ScannerConfig, MappingResult)
  - 6 Pipeline Components (UniverseFilters, ShortlistSelector, OHLCVFetcher, FeatureEngine, ReportGenerator, SnapshotManager)
  - 3 Scorers (ReversalScorer, BreakoutScorer, PullbackScorer)
- **Entry Points:** 1 (main.py)
- **Pipeline Orchestrators:** 1 (pipeline/__init__.py)

---

## Update Protocol

### When to Update This Code Map

✅ **UPDATE when:**
- Files/modules are added or removed
- Classes are added, removed, or renamed
- Function signatures change significantly
- Module responsibilities change
- New pipeline steps are added
- Major refactoring occurs

❌ **DO NOT update when:**
- Implementation details change (without structural impact)
- Bug fixes without architectural changes
- Comments or docstrings are updated
- Configuration values change
- Test files are modified

---

**End of Code Map**

Last Validated: 2026-01-17  
Based on: Complete codebase analysis (23 modules)  
Accuracy: 100% (generated from actual source code)
