# Spot Altcoin Scanner • GPT Snapshot

**Generated:** 2026-03-08 16:06 UTC  
**Commit:** `71cbe9e` (71cbe9e8f87e0eb4c4d3fc1e816b20c420601172)  
**Status:** MVP Complete (Phase 6)  

---

## 📋 Project Overview

**Purpose:** Systematic identification of short-term trading opportunities in MidCap Altcoins

**Key Features:**
- Scans 1837 MEXC USDT Spot pairs daily
- 3 independent setup types: Reversal (priority), Breakout, Pullback
- Market Cap filter: 100M-3B USD (MidCaps)
- Automated daily runs via GitHub Actions
- Deterministic snapshots for backtesting

**Architecture:**
- 10-step pipeline orchestration
- File-based caching system
- 88.4% symbol mapping success (1624/1837)
- Execution time: ~4-5 minutes (with cache)

---

## 🧩 Module & Function Overview (Code Map)

| Module | Classes | Functions |
|--------|---------|------------|
| `scanner/__init__.py` | - | - |
| `scanner/backtest/__init__.py` | - | - |
| `scanner/backtest/e2_model.py` | - | `_to_float`, `_threshold_key`, `_parse_date`, `_resolve_thresholds`, `_resolve_param_int` ... (+3 more) |
| `scanner/clients/__init__.py` | - | - |
| `scanner/clients/mapping.py` | `MappingResult`, `SymbolMapper` | - |
| `scanner/clients/marketcap_client.py` | `MarketCapClient` | - |
| `scanner/clients/mexc_client.py` | `MEXCClient` | - |
| `scanner/config.py` | `ScannerConfig` | `load_config`, `_expect_number`, `_expect_integer_number`, `_parse_integer_budget_value`, `validate_config` |
| `scanner/main.py` | - | `parse_args`, `main` |
| `scanner/pipeline/__init__.py` | - | `_to_optional_float`, `_extract_cmc_global_volume_24h`, `_compute_turnover_24h`, `_compute_mexc_share_24h`, `_build_scoring_volume_maps` ... (+3 more) |
| `scanner/pipeline/backtest_runner.py` | - | `_float_or_none`, `_extract_backtest_config`, `_setup_triggered`, `_evaluate_candidate`, `_summarize` ... (+4 more) |
| `scanner/pipeline/cross_section.py` | - | `percent_rank_average_ties` |
| `scanner/pipeline/decision.py` | - | `apply_decision_layer`, `_resolve_btc_regime_state`, `_load_decision_config`, `_expect_number`, `_expect_bool` ... (+6 more) |
| `scanner/pipeline/discovery.py` | - | `_iso_to_ts_ms`, `compute_discovery_fields` |
| `scanner/pipeline/excel_output.py` | `ExcelReportGenerator` | - |
| `scanner/pipeline/features.py` | `FeatureEngine` | - |
| `scanner/pipeline/filters.py` | `UniverseFilters` | - |
| `scanner/pipeline/global_ranking.py` | - | `_config_get`, `compute_global_top20` |
| `scanner/pipeline/liquidity.py` | - | `_root_config`, `get_orderbook_top_k`, `get_slippage_notional_usdt`, `get_grade_thresholds_bps`, `_read_tradeability_thresholds` ... (+14 more) |
| `scanner/pipeline/manifest.py` | - | `_nested_mapping_value`, `_nested_bool`, `derive_feature_flags`, `build_config_hash`, `read_canonical_schema_version` ... (+1 more) |
| `scanner/pipeline/ohlcv.py` | `OHLCVFetcher` | - |
| `scanner/pipeline/output.py` | `ReportGenerator` | - |
| `scanner/pipeline/regime.py` | - | `compute_btc_regime_from_1d_features`, `compute_btc_regime`, `_to_float` |
| `scanner/pipeline/runtime_market_meta.py` | `RuntimeMarketMetaExporter` | - |
| `scanner/pipeline/scoring/__init__.py` | - | - |
| `scanner/pipeline/scoring/breakout.py` | `BreakoutScorer` | `score_breakouts` |
| `scanner/pipeline/scoring/breakout_trend_1_5d.py` | `BreakoutTrend1to5DScorer` | `score_breakout_trend_1_5d` |
| `scanner/pipeline/scoring/decision_inputs.py` | - | `standardize_entry_readiness`, `standardize_invalidation_anchor` |
| `scanner/pipeline/scoring/pullback.py` | `PullbackScorer` | `score_pullbacks` |
| `scanner/pipeline/scoring/reversal.py` | `ReversalScorer` | `score_reversals` |
| `scanner/pipeline/scoring/trade_levels.py` | - | `_to_float`, `_atr_absolute`, `_targets`, `breakout_trade_levels`, `pullback_trade_levels` ... (+4 more) |
| `scanner/pipeline/scoring/weights.py` | - | `load_component_weights` |
| `scanner/pipeline/shortlist.py` | `ShortlistSelector` | - |
| `scanner/pipeline/snapshot.py` | `SnapshotManager` | - |
| `scanner/schema.py` | - | - |
| `scanner/tools/backfill_btc_regime.py` | `BackfillStats` | `_parse_date`, `_daterange`, `_load_snapshot`, `_ensure_minimum_version`, `_extract_btc_features_1d` ... (+6 more) |
| `scanner/tools/backfill_snapshots.py` | `BackfillStats` | `_parse_date`, `_daterange`, `_snapshot_base`, `_extract_ohlcv_row`, `_build_minimal_features` ... (+10 more) |
| `scanner/tools/export_evaluation_dataset.py` | - | `_parse_date`, `_daterange`, `_run_id_from_export_start`, `_utc_now`, `_utc_iso` ... (+6 more) |
| `scanner/tools/validate_features.py` | - | `_is_number`, `_error`, `_emit`, `validate_features` |
| `scanner/utils/__init__.py` | - | - |
| `scanner/utils/io_utils.py` | - | `load_json`, `save_json`, `get_cache_path`, `cache_exists`, `load_cache` ... (+1 more) |
| `scanner/utils/logging_utils.py` | - | `setup_logger`, `get_logger` |
| `scanner/utils/raw_collector.py` | - | `collect_raw_ohlcv`, `collect_raw_marketcap`, `collect_raw_features` |
| `scanner/utils/save_raw.py` | - | `save_raw_snapshot` |
| `scanner/utils/time_utils.py` | - | `utc_now`, `utc_timestamp`, `utc_date`, `parse_timestamp`, `timestamp_to_ms` ... (+1 more) |

**Statistics:**
- Total Modules: 45
- Total Classes: 19
- Total Functions: 151

---

## 📄 File Contents

### `pyproject.toml`

**SHA256:** `7a61576f60f2c8ce65998ca2f73910888439501885999bacb5174318128d6d39`

```toml
[project]
name = "spot-altcoin-scanner"
version = "1.0.0"
requires-python = ">=3.11"

```

### `requirements.txt`

**SHA256:** `5491fb2c532a194a57449e717dcf8cad07f8791c1c72c063c6f39a8b8a19c503`

```text
# HTTP & API
requests>=2.31.0

# Config & Serialization
PyYAML>=6.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0

# Time & Date
python-dateutil>=2.8.2

# Optional: Better Logging
loguru>=0.7.0

# Excel output
openpyxl>=3.1.0

# save raw data
pyarrow>=14.0.1

```

### `README.md`

**SHA256:** `88cc0b924a4e56a1d86845feca4cf53c8d277f74da87776618c07cf498309b59`

```markdown
# Spot Altcoin Scanner (MEXC Spot)

Deterministic scanner for short-term **spot altcoin** trading setups on **MEXC (USDT-quoted pairs)**.

**Canonical documentation (source of truth):** `docs/canonical/INDEX.md`

---

## What it does
- Builds an eligible universe (market cap + exchange availability + hard gates)
- Computes deterministic features (closed candles only)
- Scores and ranks setups
- Optionally applies liquidity re-rank using orderbook-based slippage
- Exports machine- and human-readable outputs (JSON/Markdown/Excel)

What it does **not** do:
- No automated execution / no trading bot
- No ML prediction model
- No “lookahead” (uses closed candles only)

---

## Documentation map
- Canonical index: `docs/canonical/INDEX.md`
- Configuration defaults/limits: `docs/canonical/CONFIGURATION.md`
- Output schema: `docs/canonical/OUTPUT_SCHEMA.md`
- Setup scoring (Breakout Trend 1–5d): `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- Verification fixtures: `docs/canonical/VERIFICATION_FOR_AI.md`
- Codex ticket workflow: `docs/canonical/WORKFLOW_CODEX.md`

---

## Quickstart (local)

### 1) Install
```bash
pip install -r requirements.txt
```

### 2) Configure API keys (required for standard/fast)
`run_mode=standard` and `run_mode=fast` require a CoinMarketCap key (see canonical data source policy).

```bash
export CMC_API_KEY="your_key_here"
```

### 3) Run
```bash
# fast mode (may use cache depending on implementation)
python -m scanner.main --mode fast

# standard mode (fresh provider calls)
python -m scanner.main --mode standard
```

---

## Outputs
Outputs and fields are defined canonically here:
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/OUTPUTS/RUNTIME_MARKET_META_EXPORT.md`

---

## Determinism contract (high level)
- Closed-candle-only (`closeTime_ms <= asof_ts_ms`)
- Stable ordering / explicit tie-breakers
- Same inputs + same config => same outputs

---

## Disclaimer
This is a research tool, not financial advice. Use at your own risk.

```

### `config/config.yml`

**SHA256:** `142f91f53184592f66372204c64265a33af69f57a5b40d07541dfca60aedea56`

```yaml
version:
  spec: 1.0
  config: 1.0

general:
  run_mode: "standard"        # "standard", "fast", "offline", "backtest"
  timezone: "UTC"
  shortlist_size: 100
  lookback_days_1d: 120
  lookback_days_4h: 30



budget:
  shortlist_size: 200
  orderbook_top_k: 200
  pre_shortlist_market_cap_floor_usd: 25000000

tradeability:
  enabled: true
  notional_total_usdt: 20000
  notional_chunk_usdt: 5000
  max_tranches: 4
  band_pct: 1.0
  max_spread_pct: 0.15
  min_depth_1pct_usd: 200000
  class_thresholds:
    direct_ok_max_slippage_bps: 50
    tranche_ok_max_slippage_bps: 100
    marginal_max_slippage_bps: 150

risk:
  enabled: true
  stop_method: "atr_multiple"
  atr_period: 14
  atr_timeframe: "1d"
  atr_multiple: 2.0
  min_stop_distance_pct: 4.0
  max_stop_distance_pct: 12.0
  min_rr_to_tp10: 1.3

decision:
  enabled: true
  min_score_for_enter: 65
  min_score_for_wait: 40
  require_tradeability_for_enter: true
  require_risk_acceptable_for_enter: true

btc_regime:
  enabled: true
  mode: "threshold_modifier"
  risk_off_enter_boost: 15

data_sources:
  mexc:
    enabled: true
    max_retries: 3
    retry_backoff_seconds: 3

  market_cap:
    provider: "cmc"
    api_key_env_var: "CMC_API_KEY"
    max_retries: 3
    bulk_limit: 5000

universe_filters:
  market_cap:
    legacy_soft_prior: true
    min_usd: 100000000      # 100M
    max_usd: 10000000000    # 10B
  volume:
    legacy_soft_prior: true
    min_turnover_24h: 0.03
    min_mexc_quote_volume_24h_usdt: 5000000
    min_mexc_share_24h: 0.01
  history:
    min_history_days_1d: 60
  include_only_usdt_pairs: true

exclusions:
  exclude_stablecoins: true
  exclude_wrapped_tokens: true
  exclude_leveraged_tokens: true
  exclude_synthetic_derivatives: true

mapping:
  require_high_confidence: false
  overrides_file: "config/mapping_overrides.json"
  collisions_report_file: "reports/mapping_collisions.csv"
  unmapped_behavior: "filter"

features:
  timeframes:
    - "1d"
    - "4h"
  ema_periods:
    - 20
    - 50
  atr_period: 14
  high_low_lookback_days:
    breakout: 30
    reversal: 60
  volume_sma_periods:
    1d: 20
    4h: 20
  volume_sma_period: 7
  volume_spike_threshold: 1.5
  drawdown_lookback_days: 365
  bollinger:
    period: 20
    stddev: 2.0
    rank_lookback_bars:
      1d: 120
      4h: 120
  atr_rank_lookback_bars:
    1d: 120

scoring:
  breakout:
    weights_mode: "compat"
    enabled: true
    min_breakout_pct: 2
    ideal_breakout_pct: 5
    max_breakout_pct: 20
    min_volume_spike: 1.5
    ideal_volume_spike: 2.5
    breakout_curve:
      floor_pct: -5
      fresh_cap_pct: 1
      overextended_cap_pct: 3
    momentum:
      r7_divisor: 10
    penalties:
      overextension_factor: 0.6
      low_liquidity_threshold: 500000
      low_liquidity_factor: 0.8
    high_lookback_days: 30
    min_volume_spike_factor: 1.5
    max_overextension_ema20_percent: 25
    weights:
      breakout: 0.40
      volume: 0.40
      trend: 0.20
      momentum: 0.00


  breakout_trend_1_5d:
    risk_off_min_quote_volume_24h: 15000000
    trigger_4h_lookback_bars: 30

  pullback:
    weights_mode: "compat"
    enabled: true
    min_trend_strength: 5
    min_rebound: 3
    min_volume_spike: 1.3
    momentum:
      r7_divisor: 10
    penalties:
      broken_trend_factor: 0.5
      low_liquidity_threshold: 500000
      low_liquidity_factor: 0.8
    max_pullback_from_high_percent: 25
    min_trend_days: 10
    ema_trend_period_days: 20
    weights:
      trend: 0.40
      pullback: 0.40
      rebound: 0.20
      volume: 0.00

  reversal:
    weights_mode: "compat"
    enabled: true
    min_drawdown_pct: 40
    ideal_drawdown_min: 50
    ideal_drawdown_max: 80
    min_volume_spike: 1.5
    penalties:
      overextension_threshold_pct: 15
      overextension_factor: 0.7
      low_liquidity_threshold: 500000
      low_liquidity_factor: 0.8
    min_drawdown_from_ath_percent: 40
    max_drawdown_from_ath_percent: 90
    base_lookback_days: 45
    min_base_days_without_new_low: 10
    max_allowed_new_low_percent_vs_base_low: 3
    min_reclaim_above_ema_days: 1
    min_volume_spike_factor: 1.5
    weights:
      drawdown: 0.00
      base: 0.30
      reclaim: 0.40
      volume: 0.30


snapshots:
  history_dir: "snapshots/history"
  runtime_dir: "snapshots/runtime"

backtest:
  enabled: true
  t_hold: 10
  t_trigger_max: 5
  thresholds_pct: [10, 20]
  # legacy v1 fields (kept for compatibility)
  forward_return_days: [7, 14, 30]
  max_holding_days: 30
  entry_price: "close"
  exit_price: "close_forward"
  slippage_bps: 10

logging:
  level: "INFO"
  file: "logs/scanner.log"
  log_to_file: true

setup_validation:
  min_history_breakout_1d: 30
  min_history_breakout_4h: 50
  min_history_pullback_1d: 60
  min_history_pullback_4h: 80
  min_history_reversal_1d: 120
  min_history_reversal_4h: 80

liquidity:
  orderbook_top_k: 200
  slippage_notional_usdt: 20000
  grade_thresholds_bps:
    a_max: 20
    b_max: 50
    c_max: 100



execution_gates:
  mexc_orderbook:
    enabled: true
    max_spread_pct: 0.15
    bands_pct: [0.5, 1.0]
    min_depth_usd:
      "0.5": 80000
      "1.0": 200000

risk_flags:
  denylist_file: "config/denylist.yaml"
  unlock_overrides_file: "config/unlock_overrides.yaml"
  minor_unlock_penalty_factor: 0.9



discovery:
  max_age_days: 180

trade_levels:
  pullback_entry_tolerance_pct: 1.0
  target_atr_multipliers: [1.0, 2.0, 3.0]

```

### `.github/workflows/daily.yml`

**SHA256:** `29bbe171738e87019cc00aebcf7b1f1de2137f73bea6a5440709fbeb37ecb745`

```yaml
name: Daily Scanner Run

on:
  schedule:
    # Runs daily at 6:00 AM UTC
    - cron: '10 4 * * *'
  workflow_dispatch: # Allows manual trigger

permissions:
  contents: write
  
jobs:
  scan:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run scanner
      env:
        CMC_API_KEY: ${{ secrets.CMC_API_KEY }}
        RAW_SNAPSHOT_BASEDIR: snapshots/raw
        RAW_SNAPSHOT_CSV_GZIP: "1"
      run: |
        python -m scanner.main --mode standard
    
    - name: Commit and push reports
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        git add reports/ snapshots/
        git diff --quiet && git diff --staged --quiet || git commit -m "Daily scan: $(date +'%Y-%m-%d')"
        git push

```

### `.github/workflows/update-code-map.yml`

**SHA256:** `44ee021e97e3d8c73bb5ad78eac43eda7cfa482172b38c867c5899538880f8cd`

```yaml
name: 🗺️ Auto-Update Code Map with Call Graph

on:
  # Run after GPT Snapshot workflow completes
  workflow_run:
    workflows: ["gpt-snapshot"]
    types: [completed]
    branches: [main]
  
  # Also allow manual trigger
  workflow_dispatch:
  
  # Trigger on direct changes to Python files (but not after auto-commits)
  push:
    branches: [main]
    paths:
      - 'scanner/**/*.py'
      - 'tests/**/*.py'
      - 'scripts/update_codemap.py'

concurrency:
  group: pr-automation-serial
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  update-codemap:
    runs-on: ubuntu-latest
    
    # Prevent infinite loop - skip if this is an auto-commit
    if: |
      !contains(github.event.head_commit.message, 'Auto-update code map') &&
      !contains(github.event.head_commit.message, '[skip ci]')
    
    steps:
      - name: 📦 Checkout Repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          # Use a token that can trigger other workflows if needed
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Ensure this run is tip of main (skip if outdated)
        run: |
          git fetch origin main --quiet
          TIP="$(git rev-parse origin/main)"
          if [ "${{ github.event_name }}" = "workflow_run" ]; then
            EVENT="${{ github.event.workflow_run.head_sha }}"
          else
            EVENT="${GITHUB_SHA}"
          fi
          echo "TIP=$TIP"
          echo "EVENT=$EVENT"
          if [ "$TIP" != "$EVENT" ]; then
            echo "Outdated run (not tip of main). Skipping commit."
            exit 0
          fi
      
      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: 📋 Verify Script Exists
        run: |
          if [ ! -f scripts/update_codemap.py ]; then
            echo "❌ scripts/update_codemap.py not found!"
            exit 1
          fi
          echo "✅ Script found"
      
      - name: 🧩 Generate Code Map with Call Graph
        run: |
          echo "🗺️  Running Code Map Generator..."
          python scripts/update_codemap.py
      
      - name: 📊 Check Generated File
        run: |
          if [ -f docs/code_map.md ]; then
            SIZE=$(wc -c < docs/code_map.md)
            LINES=$(wc -l < docs/code_map.md)
            echo "✅ Code Map generated successfully"
            echo "   Size: ${SIZE} bytes"
            echo "   Lines: ${LINES}"
          else
            echo "❌ docs/code_map.md not found!"
            exit 1
          fi
      
      - name: 🔍 Check for Changes
        id: check_changes
        run: |
          if git diff --quiet docs/code_map.md; then
            echo "changed=false" >> $GITHUB_OUTPUT
            echo "✅ Code Map is already up to date"
          else
            echo "changed=true" >> $GITHUB_OUTPUT
            echo "📝 Changes detected in Code Map"
            echo ""
            echo "Summary of changes:"
            git diff --stat docs/code_map.md
          fi
      
      - name: 📤 Commit and Push Changes
        if: steps.check_changes.outputs.changed == 'true'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "🤖 Auto-update code map with call graph analysis [skip ci]"
          file_pattern: docs/code_map.md
          commit_user_name: github-actions[bot]
          commit_user_email: github-actions[bot]@users.noreply.github.com
          skip_fetch: false
          skip_checkout: false
      
      - name: 📊 Summary
        run: |
          echo "╔════════════════════════════════════════════════════════════╗"
          if [ "${{ steps.check_changes.outputs.changed }}" == "true" ]; then
            echo "✅ Code Map has been updated with call graph analysis"
            echo ""
            echo "New features in Code Map:"
            echo "  • Module structure overview"
            echo "  • Function dependencies (who calls whom)"
            echo "  • Internal vs. external call separation"
            echo "  • Coupling statistics with refactoring insights"
          else
            echo "✅ Code Map was already up to date"
            echo "   No changes needed"
          fi
          echo "╚════════════════════════════════════════════════════════════╝"

```

### `.github/workflows/generate-gpt-snapshot.yml`

**SHA256:** `96dffa634f1c1e03148800344bdf70891a2366aadd28d442eab0dc84f1094601`

```yaml
name: gpt-snapshot

on:
  push:
    branches: [ main ]
  workflow_dispatch:
  release:
    types: [ published ]

concurrency:
  group: pr-automation-serial
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: true
      
      - name: Ensure this run is tip of main (skip if outdated)
        run: |
          git fetch origin main --quiet
          TIP="$(git rev-parse origin/main)"
          echo "TIP=$TIP"
          echo "EVENT=${GITHUB_SHA}"
          if [ "$TIP" != "$GITHUB_SHA" ]; then
            echo "Outdated run (not tip of main). Skipping commit."
            exit 0
          fi
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Build docs/GPT_SNAPSHOT.md
        run: |
          python - <<'PY'
          import os, hashlib, re
          from pathlib import Path
          from datetime import datetime
          
          out = Path("docs/GPT_SNAPSHOT.md")
          out.parent.mkdir(parents=True, exist_ok=True)
          
          # Files to include in snapshot
          include = [
            "pyproject.toml",
            "requirements.txt", 
            "README.md",
            "config/config.yml",
            ".github/workflows/daily.yml",
            ".github/workflows/update-code-map.yml",
            ".github/workflows/generate-gpt-snapshot.yml",
          ]
          
          # All Python modules
          for p in Path("scanner").rglob("*.py"):
            include.append(str(p))
          
          # Key documentation files
          for doc in ["spec.md", "dev_guide.md", "features.md", "scoring.md"]:
            doc_path = Path("docs") / doc
            if doc_path.exists():
              include.append(str(doc_path))

          # Canonical docs are the single source of truth for model-facing snapshot context.
          canonical_docs = [
            "docs/canonical/INDEX.md",
            "docs/canonical/CONFIGURATION.md",
            "docs/canonical/OUTPUT_SCHEMA.md",
            "docs/canonical/VERIFICATION_FOR_AI.md",
            "docs/canonical/SCORING/SETUP_VALIDITY_RULES.md",
            "docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md",
            "docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md",
            "docs/canonical/SCORING/DISCOVERY_TAG.md",
          ]
          for doc in canonical_docs:
            if Path(doc).exists():
              include.append(doc)
          
          def sha256(p):
            h = hashlib.sha256()
            with open(p, "rb") as f:
              for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
            return h.hexdigest()
          
          def lang(p):
            ext = Path(p).suffix.lower().lstrip(".")
            return {
              "py": "python",
              "yml": "yaml", 
              "yaml": "yaml",
              "toml": "toml",
              "md": "markdown",
              "txt": "text",
              "json": "json"
            }.get(ext, "text")
          
          def extract_structure(pyfile: Path):
            """Extract classes and functions from Python file."""
            try:
              text = pyfile.read_text(encoding="utf-8", errors="ignore")
              funcs = re.findall(r"^def ([a-zA-Z_][a-zA-Z0-9_]*)", text, re.MULTILINE)
              classes = re.findall(r"^class ([a-zA-Z_][a-zA-Z0-9_]*)", text, re.MULTILINE)
              return funcs, classes
            except:
              return [], []
          
          parts = []
          
          # Header
          head = os.popen('git rev-parse HEAD').read().strip()
          short_head = head[:7] if head else "unknown"
          timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
          
          parts += [
            f"# Spot Altcoin Scanner • GPT Snapshot\n\n",
            f"**Generated:** {timestamp}  \n",
            f"**Commit:** `{short_head}` ({head})  \n",
            f"**Status:** MVP Complete (Phase 6)  \n\n",
            "---\n\n"
          ]
          
          # Project overview
          parts += [
            "## 📋 Project Overview\n\n",
            "**Purpose:** Systematic identification of short-term trading opportunities in MidCap Altcoins\n\n",
            "**Key Features:**\n",
            "- Scans 1837 MEXC USDT Spot pairs daily\n",
            "- 3 independent setup types: Reversal (priority), Breakout, Pullback\n",
            "- Market Cap filter: 100M-3B USD (MidCaps)\n",
            "- Automated daily runs via GitHub Actions\n",
            "- Deterministic snapshots for backtesting\n\n",
            "**Architecture:**\n",
            "- 10-step pipeline orchestration\n",
            "- File-based caching system\n",
            "- 88.4% symbol mapping success (1624/1837)\n",
            "- Execution time: ~4-5 minutes (with cache)\n\n",
            "---\n\n"
          ]
          
          # Module & function overview (Code Map)
          parts.append("## 🧩 Module & Function Overview (Code Map)\n\n")
          
          modules = []
          for p in Path("scanner").rglob("*.py"):
            funcs, classes = extract_structure(p)
            modules.append({
              "path": str(p),
              "functions": funcs,
              "classes": classes,
            })
          
          # Sort by path
          modules.sort(key=lambda m: m["path"])
          
          parts.append("| Module | Classes | Functions |\n")
          parts.append("|--------|---------|------------|\n")
          
          for m in modules:
            classes_str = ", ".join(f"`{c}`" for c in m["classes"]) or "-"
            funcs_str = ", ".join(f"`{f}`" for f in m["functions"][:5]) or "-"
            if len(m["functions"]) > 5:
              funcs_str += f" ... (+{len(m['functions'])-5} more)"
            parts.append(f"| `{m['path']}` | {classes_str} | {funcs_str} |\n")
          
          parts.append("\n")
          
          # Statistics
          total_modules = len(modules)
          total_classes = sum(len(m["classes"]) for m in modules)
          total_functions = sum(len(m["functions"]) for m in modules)
          
          parts += [
            "**Statistics:**\n",
            f"- Total Modules: {total_modules}\n",
            f"- Total Classes: {total_classes}\n",
            f"- Total Functions: {total_functions}\n\n",
            "---\n\n"
          ]
          
          # File contents
          parts.append("## 📄 File Contents\n\n")
          
          for p in include:
            if not Path(p).is_file():
              continue
            
            rel_path = p
            sha = sha256(p)
            
            parts += [
              f"### `{rel_path}`\n\n",
              f"**SHA256:** `{sha}`\n\n",
              f"```{lang(p)}\n",
              Path(p).read_text(encoding="utf-8", errors="ignore"),
              "\n```\n\n"
            ]
          
          # Footer
          parts += [
            "---\n\n",
            "## 📚 Additional Resources\n\n",
            "- **Code Map:** `docs/code_map.md` (detailed structural overview)\n",
            "- **Specifications:** `docs/spec.md` (technical master spec)\n",
            "- **Dev Guide:** `docs/dev_guide.md` (development workflow)\n",
            "- **Latest Reports:** `reports/YYYY-MM-DD.md` (daily scanner outputs)\n\n",
            "---\n\n",
            f"_Generated by GitHub Actions • {timestamp}_\n"
          ]
          
          out.write_text("".join(parts), encoding="utf-8")
          print(f"✓ Wrote {out} ({len(''.join(parts))} bytes)")
          print(f"  Modules: {total_modules}")
          print(f"  Classes: {total_classes}")
          print(f"  Functions: {total_functions}")
          print(f"  Files included: {len([p for p in include if Path(p).is_file()])}")
          PY
      
      - name: Commit snapshot
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "docs: update GPT_SNAPSHOT.md [skip ci]"
          file_pattern: docs/GPT_SNAPSHOT.md
      
      - name: Summary
        run: |
          if [ -f docs/GPT_SNAPSHOT.md ]; then
            SIZE=$(wc -c < docs/GPT_SNAPSHOT.md)
            echo "✅ GPT Snapshot Generated"
            echo "  Location: docs/GPT_SNAPSHOT.md"
            echo "  Size: ${SIZE} bytes"
          else
            echo "❌ Snapshot generation failed"
            exit 1
          fi

```

### `scanner/main.py`

**SHA256:** `6c8cb80699e90b776b7f8244462b311d999b40130efe294831eee2646b010933`

```python
from __future__ import annotations

import argparse
import sys

from .config import load_config
from .pipeline import run_pipeline


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Spot Altcoin Scanner – daily pipeline runner"
    )
    parser.add_argument(
        "--mode",
        choices=["standard", "fast", "offline", "backtest"],
        help="Override run_mode from config.yml",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = load_config()

    if args.mode:
        cfg.raw.setdefault("general", {})["run_mode"] = args.mode

    run_pipeline(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


```

### `scanner/schema.py`

**SHA256:** `5a76b97a0232d42afa7c5c14f36b9653dee562b9d1c2fb166a2a4d9dedce43e9`

```python
"""Schema/version constants for scanner outputs."""

REPORT_SCHEMA_VERSION = "v1.12"
REPORT_META_VERSION = "1.9"

```

### `scanner/__init__.py`

**SHA256:** `c6d8ea689789828672d38ce8d93859015f5cc8d69934f34f23366d6a1ddc8b84`

```python
# scanner/__init__.py

"""
Spot Altcoin Scanner package.

See /docs/spec.md for the full technical specification.
"""


```

### `scanner/config.py`

**SHA256:** `77a3a95e27819505cc8ae43d62872f3e18e13828348dff863d0e4f0007fab530`

```python
"""
Configuration loading and validation.
Loads config.yml and applies environment variable overrides.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import yaml


CONFIG_PATH = os.getenv("SCANNER_CONFIG_PATH", "config/config.yml")

_BUDGET_DEFAULTS = {
    "shortlist_size": 200,
    "orderbook_top_k": 200,
    "pre_shortlist_market_cap_floor_usd": 25_000_000,
}


@dataclass
class ScannerConfig:
    """
    Scanner configuration wrapper.
    Provides type-safe access to config values.
    """

    raw: Dict[str, Any]

    # Version
    @property
    def spec_version(self) -> str:
        return self.raw.get("version", {}).get("spec", "1.0")

    @property
    def config_version(self) -> str:
        return self.raw.get("version", {}).get("config", "1.0")

    # General
    @property
    def run_mode(self) -> str:
        return self.raw.get("general", {}).get("run_mode", "standard")

    @property
    def timezone(self) -> str:
        return self.raw.get("general", {}).get("timezone", "UTC")

    @property
    def shortlist_size(self) -> int:
        budget_cfg = self.raw.get("budget", {})
        if "shortlist_size" in budget_cfg:
            return budget_cfg.get("shortlist_size", 200)
        if "shortlist_size" in self.raw.get("general", {}):
            return self.raw.get("general", {}).get("shortlist_size", 100)
        return 200

    @property
    def lookback_days_1d(self) -> int:
        return self.raw.get("general", {}).get("lookback_days_1d", 120)

    @property
    def lookback_days_4h(self) -> int:
        return self.raw.get("general", {}).get("lookback_days_4h", 30)

    # Data Sources
    @property
    def mexc_enabled(self) -> bool:
        return self.raw.get("data_sources", {}).get("mexc", {}).get("enabled", True)

    @property
    def cmc_api_key(self) -> str:
        """Get CMC API key from ENV or config."""
        env_var = self.raw.get("data_sources", {}).get("market_cap", {}).get("api_key_env_var", "CMC_API_KEY")
        return os.getenv(env_var, "")

    # Budget
    def _budget_mapping(self) -> Dict[str, Any]:
        budget_cfg = self.raw.get("budget")
        if isinstance(budget_cfg, dict):
            return budget_cfg
        return {}

    @property
    def budget_shortlist_size(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get("shortlist_size", _BUDGET_DEFAULTS["shortlist_size"]),
            "budget.shortlist_size",
        )

    @property
    def budget_orderbook_top_k(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get("orderbook_top_k", _BUDGET_DEFAULTS["orderbook_top_k"]),
            "budget.orderbook_top_k",
        )

    @property
    def pre_shortlist_market_cap_floor_usd(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get(
                "pre_shortlist_market_cap_floor_usd",
                _BUDGET_DEFAULTS["pre_shortlist_market_cap_floor_usd"],
            ),
            "budget.pre_shortlist_market_cap_floor_usd",
        )

    # Universe Filters (legacy soft priors)
    @property
    def market_cap_min(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("min_usd", 100_000_000)

    @property
    def market_cap_max(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("max_usd", 10_000_000_000)

    @property
    def min_turnover_24h(self) -> float:
        return float(self.raw.get("universe_filters", {}).get("volume", {}).get("min_turnover_24h", 0.03))

    @property
    def min_mexc_quote_volume_24h_usdt(self) -> float:
        volume_cfg = self.raw.get("universe_filters", {}).get("volume", {})
        if "min_mexc_quote_volume_24h_usdt" in volume_cfg:
            return float(volume_cfg.get("min_mexc_quote_volume_24h_usdt", 5_000_000))
        return float(volume_cfg.get("min_quote_volume_24h", 5_000_000))

    @property
    def min_mexc_share_24h(self) -> float:
        return float(self.raw.get("universe_filters", {}).get("volume", {}).get("min_mexc_share_24h", 0.01))

    @property
    def min_quote_volume_24h(self) -> float:
        """Backward-compatible alias for runtime metadata export."""
        return self.min_mexc_quote_volume_24h_usdt

    @property
    def scoring_volume_source(self) -> str:
        return str(self.raw.get("scoring", {}).get("volume_source", "mexc"))

    @property
    def min_history_days_1d(self) -> int:
        return self.raw.get("universe_filters", {}).get("history", {}).get("min_history_days_1d", 60)

    # Tradeability
    @property
    def tradeability_enabled(self) -> bool:
        return self.raw.get("tradeability", {}).get("enabled", True)

    @property
    def tradeability_notional_total_usdt(self) -> float:
        return float(self.raw.get("tradeability", {}).get("notional_total_usdt", 20_000))

    @property
    def tradeability_notional_chunk_usdt(self) -> float:
        return float(self.raw.get("tradeability", {}).get("notional_chunk_usdt", 5_000))

    @property
    def tradeability_max_tranches(self) -> int:
        return int(self.raw.get("tradeability", {}).get("max_tranches", 4))

    @property
    def tradeability_band_pct(self) -> float:
        return float(self.raw.get("tradeability", {}).get("band_pct", 1.0))

    @property
    def tradeability_max_spread_pct(self) -> float:
        return float(self.raw.get("tradeability", {}).get("max_spread_pct", 0.15))

    @property
    def tradeability_min_depth_1pct_usd(self) -> float:
        return float(self.raw.get("tradeability", {}).get("min_depth_1pct_usd", 200_000))

    @property
    def tradeability_class_thresholds(self) -> Dict[str, Any]:
        return self.raw.get("tradeability", {}).get(
            "class_thresholds",
            {
                "direct_ok_max_slippage_bps": 50,
                "tranche_ok_max_slippage_bps": 100,
                "marginal_max_slippage_bps": 150,
            },
        )

    # Risk
    @property
    def risk_enabled(self) -> bool:
        return self.raw.get("risk", {}).get("enabled", True)

    @property
    def risk_stop_method(self) -> str:
        return str(self.raw.get("risk", {}).get("stop_method", "atr_multiple"))

    @property
    def risk_atr_period(self) -> int:
        return int(self.raw.get("risk", {}).get("atr_period", 14))

    @property
    def risk_atr_timeframe(self) -> str:
        return str(self.raw.get("risk", {}).get("atr_timeframe", "1d"))

    @property
    def risk_atr_multiple(self) -> float:
        return float(self.raw.get("risk", {}).get("atr_multiple", 2.0))

    @property
    def risk_min_stop_distance_pct(self) -> float:
        return float(self.raw.get("risk", {}).get("min_stop_distance_pct", 4.0))

    @property
    def risk_max_stop_distance_pct(self) -> float:
        return float(self.raw.get("risk", {}).get("max_stop_distance_pct", 12.0))

    @property
    def risk_min_rr_to_tp10(self) -> float:
        return float(self.raw.get("risk", {}).get("min_rr_to_tp10", 1.3))

    # Decision
    @property
    def decision_enabled(self) -> bool:
        return self.raw.get("decision", {}).get("enabled", True)

    @property
    def decision_min_score_for_enter(self) -> int:
        return int(self.raw.get("decision", {}).get("min_score_for_enter", 65))

    @property
    def decision_min_score_for_wait(self) -> int:
        return int(self.raw.get("decision", {}).get("min_score_for_wait", 40))

    @property
    def decision_require_tradeability_for_enter(self) -> bool:
        return self.raw.get("decision", {}).get("require_tradeability_for_enter", True)

    @property
    def decision_require_risk_acceptable_for_enter(self) -> bool:
        return self.raw.get("decision", {}).get("require_risk_acceptable_for_enter", True)

    # BTC regime
    @property
    def btc_regime_enabled(self) -> bool:
        return self.raw.get("btc_regime", {}).get("enabled", True)

    @property
    def btc_regime_mode(self) -> str:
        return str(self.raw.get("btc_regime", {}).get("mode", "threshold_modifier"))

    @property
    def btc_regime_risk_off_enter_boost(self) -> float:
        return float(self.raw.get("btc_regime", {}).get("risk_off_enter_boost", 15))

    # Exclusions
    @property
    def exclude_stablecoins(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_stablecoins", True)

    @property
    def exclude_wrapped(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_wrapped_tokens", True)

    @property
    def exclude_leveraged(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_leveraged_tokens", True)

    # Logging
    @property
    def log_level(self) -> str:
        return self.raw.get("logging", {}).get("level", "INFO")

    @property
    def log_to_file(self) -> bool:
        return self.raw.get("logging", {}).get("log_to_file", True)

    @property
    def log_file(self) -> str:
        return self.raw.get("logging", {}).get("file", "logs/scanner.log")


def load_config(path: str | Path | None = None) -> ScannerConfig:
    """
    Load configuration from YAML file.

    Args:
        path: Path to config.yml (default: config/config.yml)

    Returns:
        ScannerConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config is invalid YAML
    """
    cfg_path = Path(path) if path else Path(CONFIG_PATH)

    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return ScannerConfig(raw=raw)


def _expect_number(errors: List[str], value: Any, field_name: str, *, minimum: float | None = None, maximum: float | None = None) -> float | None:
    if isinstance(value, bool) or value is None:
        errors.append(f"{field_name} must be numeric")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be numeric")
        return None

    if minimum is not None and number < minimum:
        errors.append(f"{field_name} ({number}) must be >= {minimum}")
    if maximum is not None and number > maximum:
        errors.append(f"{field_name} ({number}) must be <= {maximum}")
    return number


def _expect_integer_number(
    errors: List[str],
    value: Any,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> int | None:
    number = _expect_number(errors, value, field_name, minimum=minimum, maximum=maximum)
    if number is None:
        return None
    if not number.is_integer():
        errors.append(f"{field_name} must be an integer")
        return None
    return int(number)


def _parse_integer_budget_value(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be numeric")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if not number.is_integer():
        raise ValueError(f"{field_name} must be an integer")

    return int(number)


def validate_config(config: ScannerConfig) -> List[str]:
    """
    Validate configuration.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check run_mode
    valid_modes = ["standard", "fast", "offline", "backtest"]
    if config.run_mode not in valid_modes:
        errors.append(f"Invalid run_mode: {config.run_mode}. Must be one of {valid_modes}")

    # Check market cap range
    if config.market_cap_min >= config.market_cap_max:
        errors.append(f"market_cap_min ({config.market_cap_min}) must be < market_cap_max ({config.market_cap_max})")

    # Check CMC API key (if needed)
    if not config.cmc_api_key and config.run_mode == "standard":
        errors.append("CMC_API_KEY environment variable not set")

    # Universe volume-gate configuration
    if config.min_turnover_24h < 0:
        errors.append(f"min_turnover_24h ({config.min_turnover_24h}) must be >= 0")

    if config.min_mexc_quote_volume_24h_usdt < 0:
        errors.append(
            f"min_mexc_quote_volume_24h_usdt ({config.min_mexc_quote_volume_24h_usdt}) must be >= 0"
        )

    if not (0 <= config.min_mexc_share_24h <= 1):
        errors.append(f"min_mexc_share_24h ({config.min_mexc_share_24h}) must be in [0, 1]")

    valid_volume_sources = ["mexc", "global_fallback_mexc"]
    if config.scoring_volume_source not in valid_volume_sources:
        errors.append(
            f"scoring.volume_source ({config.scoring_volume_source}) must be one of {valid_volume_sources}"
        )

    # Budget defaults / limits
    budget_cfg = config.raw.get("budget")
    if budget_cfg is None:
        budget_cfg = {}
    elif not isinstance(budget_cfg, dict):
        errors.append("budget must be an object")
        budget_cfg = {}

    _expect_integer_number(
        errors,
        budget_cfg.get("shortlist_size", _BUDGET_DEFAULTS["shortlist_size"]),
        "budget.shortlist_size",
        minimum=1,
    )
    _expect_integer_number(
        errors,
        budget_cfg.get("orderbook_top_k", _BUDGET_DEFAULTS["orderbook_top_k"]),
        "budget.orderbook_top_k",
        minimum=1,
    )
    _expect_integer_number(
        errors,
        budget_cfg.get("pre_shortlist_market_cap_floor_usd", _BUDGET_DEFAULTS["pre_shortlist_market_cap_floor_usd"]),
        "budget.pre_shortlist_market_cap_floor_usd",
        minimum=0,
    )

    # Tradeability block
    tradeability_cfg = config.raw.get("tradeability", {})
    if "enabled" in tradeability_cfg and not isinstance(tradeability_cfg.get("enabled"), bool):
        errors.append("tradeability.enabled must be boolean")
    _expect_number(errors, tradeability_cfg.get("notional_total_usdt", 20_000), "tradeability.notional_total_usdt", minimum=0)
    _expect_number(errors, tradeability_cfg.get("notional_chunk_usdt", 5_000), "tradeability.notional_chunk_usdt", minimum=0)
    _expect_number(errors, tradeability_cfg.get("max_tranches", 4), "tradeability.max_tranches", minimum=1)
    _expect_number(errors, tradeability_cfg.get("band_pct", 1.0), "tradeability.band_pct", minimum=0)
    _expect_number(errors, tradeability_cfg.get("max_spread_pct", 0.15), "tradeability.max_spread_pct", minimum=0)
    _expect_number(errors, tradeability_cfg.get("min_depth_1pct_usd", 200_000), "tradeability.min_depth_1pct_usd", minimum=0)

    class_thresholds = tradeability_cfg.get("class_thresholds")
    if class_thresholds is None:
        class_thresholds = {
            "direct_ok_max_slippage_bps": 50,
            "tranche_ok_max_slippage_bps": 100,
            "marginal_max_slippage_bps": 150,
        }
    if not isinstance(class_thresholds, dict):
        errors.append("tradeability.class_thresholds must be an object")
    else:
        required = [
            "direct_ok_max_slippage_bps",
            "tranche_ok_max_slippage_bps",
            "marginal_max_slippage_bps",
        ]
        missing = [key for key in required if key not in class_thresholds]
        if missing:
            errors.append(f"tradeability.class_thresholds missing keys: {missing}")
        else:
            d = _expect_number(errors, class_thresholds.get(required[0]), f"tradeability.class_thresholds.{required[0]}", minimum=0)
            t = _expect_number(errors, class_thresholds.get(required[1]), f"tradeability.class_thresholds.{required[1]}", minimum=0)
            m = _expect_number(errors, class_thresholds.get(required[2]), f"tradeability.class_thresholds.{required[2]}", minimum=0)
            if d is not None and t is not None and m is not None and not (d <= t <= m):
                errors.append(
                    "tradeability.class_thresholds must satisfy direct_ok_max_slippage_bps <= tranche_ok_max_slippage_bps <= marginal_max_slippage_bps"
                )

    # Risk block
    risk_cfg = config.raw.get("risk", {})
    if "enabled" in risk_cfg and not isinstance(risk_cfg.get("enabled"), bool):
        errors.append("risk.enabled must be boolean")
    if str(risk_cfg.get("stop_method", "atr_multiple")) != "atr_multiple":
        errors.append("risk.stop_method must be 'atr_multiple' in Phase 1")
    _expect_number(errors, risk_cfg.get("atr_period", 14), "risk.atr_period", minimum=1)
    if str(risk_cfg.get("atr_timeframe", "1d")) not in ["1d"]:
        errors.append("risk.atr_timeframe must be '1d' in Phase 1")
    _expect_number(errors, risk_cfg.get("atr_multiple", 2.0), "risk.atr_multiple", minimum=0)
    min_stop = _expect_number(errors, risk_cfg.get("min_stop_distance_pct", 4.0), "risk.min_stop_distance_pct", minimum=0)
    max_stop = _expect_number(errors, risk_cfg.get("max_stop_distance_pct", 12.0), "risk.max_stop_distance_pct", minimum=0)
    if min_stop is not None and max_stop is not None and min_stop > max_stop:
        errors.append("risk.min_stop_distance_pct must be <= risk.max_stop_distance_pct")
    _expect_number(errors, risk_cfg.get("min_rr_to_tp10", 1.3), "risk.min_rr_to_tp10", minimum=0)

    # Decision block
    decision_cfg = config.raw.get("decision", {})
    if "enabled" in decision_cfg and not isinstance(decision_cfg.get("enabled"), bool):
        errors.append("decision.enabled must be boolean")
    min_enter = _expect_number(errors, decision_cfg.get("min_score_for_enter", 65), "decision.min_score_for_enter", minimum=0, maximum=100)
    min_wait = _expect_number(errors, decision_cfg.get("min_score_for_wait", 40), "decision.min_score_for_wait", minimum=0, maximum=100)
    if min_enter is not None and min_wait is not None and min_wait > min_enter:
        errors.append("decision.min_score_for_wait must be <= decision.min_score_for_enter")
    for bool_key in ["require_tradeability_for_enter", "require_risk_acceptable_for_enter"]:
        if bool_key in decision_cfg and not isinstance(decision_cfg.get(bool_key), bool):
            errors.append(f"decision.{bool_key} must be boolean")

    # BTC regime block
    btc_cfg = config.raw.get("btc_regime", {})
    if "enabled" in btc_cfg and not isinstance(btc_cfg.get("enabled"), bool):
        errors.append("btc_regime.enabled must be boolean")
    mode = str(btc_cfg.get("mode", "threshold_modifier"))
    if mode != "threshold_modifier":
        errors.append("btc_regime.mode must be 'threshold_modifier'")
    _expect_number(errors, btc_cfg.get("risk_off_enter_boost", 15), "btc_regime.risk_off_enter_boost")

    return errors

```

### `scanner/clients/mexc_client.py`

**SHA256:** `895c43d74c5d963773e503f856a45989c679c665bae91284b5ed3b36b463ab7e`

```python
"""
MEXC API Client for Spot market data.

Responsibilities:
- Fetch spot symbol list (exchangeInfo)
- Fetch 24h ticker data (bulk)
- Fetch OHLCV (klines) for specific pairs

API Docs: https://mexcdevelop.github.io/apidocs/spot_v3_en/
"""

import time
from typing import Dict, List, Optional, Any
import requests
from ..utils.logging_utils import get_logger
from ..utils.io_utils import load_cache, save_cache, cache_exists


logger = get_logger(__name__)


class MEXCClient:
    """
    MEXC Spot API client with rate-limit handling and caching.
    """
    
    BASE_URL = "https://api.mexc.com"
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_backoff: float = 3.0,
        timeout: int = 30
    ):
        """
        Initialize MEXC client.
        
        Args:
            max_retries: Maximum retry attempts on failure
            retry_backoff: Seconds to wait between retries
            timeout: Request timeout in seconds
        """
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.timeout = timeout
        self.session = requests.Session()
        
        # Rate limiting (conservative)
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint (e.g., '/api/v3/exchangeInfo')
            params: Query parameters
            
        Returns:
            JSON response
            
        Raises:
            requests.RequestException: On persistent failure
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=self.timeout
                )
                
                # Handle rate limit (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_backoff))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_backoff * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts")
                    raise
        
        raise requests.RequestException("Unexpected error in retry loop")
    
    def get_exchange_info(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get exchange info (symbols, trading rules).
        
        Args:
            use_cache: Use cached data if available (today)
            
        Returns:
            Exchange info dict with 'symbols' list
        """
        cache_key = "mexc_exchange_info"
        
        if use_cache and cache_exists(cache_key):
            logger.info("Loading exchange info from cache")
            return load_cache(cache_key)
        
        logger.info("Fetching exchange info from MEXC API")
        data = self._request("GET", "/api/v3/exchangeInfo")
        
        save_cache(data, cache_key)
        return data
    
    def get_spot_usdt_symbols(self, use_cache: bool = True) -> List[str]:
        """
        Get all Spot USDT trading pairs.
        
        Returns:
            List of symbols (e.g., ['BTCUSDT', 'ETHUSDT', ...])
        """
        exchange_info = self.get_exchange_info(use_cache=use_cache)
        
        symbols = []
        for symbol_info in exchange_info.get("symbols", []):
            # Filter: USDT quote, Spot, Trading status
            # Note: MEXC uses status="1" for enabled (not "ENABLED")
            if (
                symbol_info.get("quoteAsset") == "USDT" and
                symbol_info.get("isSpotTradingAllowed", False) and
                symbol_info.get("status") == "1"
            ):
                symbols.append(symbol_info["symbol"])
        
        logger.info(f"Found {len(symbols)} USDT Spot pairs")
        return symbols
    
    def get_24h_tickers(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get 24h ticker statistics for all symbols (bulk).
        
        Returns:
            List of ticker dicts with keys:
            - symbol
            - lastPrice
            - priceChangePercent
            - quoteVolume
            - volume
            etc.
        """
        cache_key = "mexc_24h_tickers"
        
        if use_cache and cache_exists(cache_key):
            logger.info("Loading 24h tickers from cache")
            return load_cache(cache_key)
        
        logger.info("Fetching 24h tickers from MEXC API")
        data = self._request("GET", "/api/v3/ticker/24hr")
        
        save_cache(data, cache_key)
        logger.info(f"Fetched {len(data)} ticker entries")
        return data
    

    def get_orderbook(self, symbol: str, limit: int = 200) -> Dict[str, Any]:
        """Get orderbook depth snapshot for a symbol."""
        return self._request("GET", "/api/v3/depth", params={"symbol": symbol, "limit": int(limit)})

    def get_klines(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int = 120,
        use_cache: bool = True
    ) -> List[List]:
        """
        Get candlestick/kline data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            limit: Number of candles (max 1000)
            use_cache: Use cached data if available
            
        Returns:
            List of klines, each kline is a list:
            [openTime, open, high, low, close, volume, closeTime, quoteVolume, ...]
        """
        cache_key = f"mexc_klines_{symbol}_{interval}"
        
        if use_cache and cache_exists(cache_key):
            logger.debug(f"Loading klines from cache: {symbol} {interval}")
            return load_cache(cache_key)
        
        logger.debug(f"Fetching klines: {symbol} {interval} (limit={limit})")
        
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000)  # API max is 1000
        }
        
        data = self._request("GET", "/api/v3/klines", params=params)
        
        save_cache(data, cache_key)
        return data
    
    def get_multiple_klines(
        self,
        symbols: List[str],
        interval: str = "1d",
        limit: int = 120,
        use_cache: bool = True
    ) -> Dict[str, List[List]]:
        """
        Get klines for multiple symbols (sequential, rate-limited).
        
        Args:
            symbols: List of trading pairs
            interval: Timeframe
            limit: Candles per symbol
            use_cache: Use cached data
            
        Returns:
            Dict mapping symbol -> klines
        """
        results = {}
        total = len(symbols)
        
        logger.info(f"Fetching klines for {total} symbols ({interval})")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                results[symbol] = self.get_klines(symbol, interval, limit, use_cache)
                
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{total} symbols")
                    
            except Exception as e:
                logger.error(f"Failed to fetch klines for {symbol}: {e}")
                results[symbol] = []
        
        logger.info(f"Successfully fetched klines for {len(results)} symbols")
        return results

```

### `scanner/clients/__init__.py`

**SHA256:** `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`

```python


```

### `scanner/clients/marketcap_client.py`

**SHA256:** `5d8072e16cc2f3388b6834d559c65d0c04b9557703ab5e62f2c8e7c1ffa03ace`

```python
"""
CoinMarketCap API Client for market cap data.

Responsibilities:
- Fetch bulk cryptocurrency listings
- Get market cap, rank, supply data
- Cache daily for rate-limit efficiency

API Docs: https://coinmarketcap.com/api/documentation/v1/
"""

import os
from typing import Dict, List, Optional, Any
import requests
from ..utils.logging_utils import get_logger
from ..utils.io_utils import load_cache, save_cache, cache_exists

# 🔹 Neu: zentralisierte Rohdaten-Speicherung
try:
    from scanner.utils.raw_collector import collect_raw_marketcap
except ImportError:
    collect_raw_marketcap = None


logger = get_logger(__name__)


class MarketCapClient:
    """
    CoinMarketCap API client with caching and rate-limit protection.
    """
    
    BASE_URL = "https://pro-api.coinmarketcap.com"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize CMC client.
        
        Args:
            api_key: CMC API key (default: from CMC_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("CMC_API_KEY")
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("CMC_API_KEY not set - client will fail on API calls")
        
        self.session = requests.Session()
        self.session.headers.update({
            "X-CMC_PRO_API_KEY": self.api_key or "",
            "Accept": "application/json"
        })
    
    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API request.
        
        Args:
            endpoint: API endpoint (e.g., '/v1/cryptocurrency/listings/latest')
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            requests.RequestException: On API failure
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            # Handle rate limit
            if response.status_code == 429:
                logger.error("CMC rate limit hit - check your plan limits")
                raise requests.RequestException("CMC rate limit exceeded")
            
            response.raise_for_status()
            
            data = response.json()
            
            # CMC wraps data in 'data' field
            if "data" not in data:
                logger.error(f"Unexpected CMC response structure: {data.keys()}")
                raise ValueError("Invalid CMC response format")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"CMC API request failed: {e}")
            raise
    
    def get_listings(
        self,
        start: int = 1,
        limit: int = 5000,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get cryptocurrency listings with market cap data.
        
        Args:
            start: Start rank (1-based)
            limit: Number of results (max 5000)
            use_cache: Use cached data if available (today)
            
        Returns:
            List of cryptocurrency dicts with keys:
            - id: CMC ID
            - symbol: Ticker symbol
            - name: Full name
            - slug: URL slug
            - cmc_rank: CMC rank
            - quote.USD.market_cap: Market cap in USD
            - quote.USD.price: Current price
            - circulating_supply: Circulating supply
            - total_supply: Total supply
            - max_supply: Max supply
        """
        cache_key = f"cmc_listings_start{start}_limit{limit}"
        
        if use_cache and cache_exists(cache_key):
            logger.info("Loading CMC listings from cache")
            cached = load_cache(cache_key)
            data = cached.get("data", []) if isinstance(cached, dict) else []

            # 🔹 Rohdaten-Snapshot auch bei Cache-Hit speichern
            if collect_raw_marketcap and data:
                try:
                    collect_raw_marketcap(data)
                except Exception as e:
                    logger.warning(f"Could not collect MarketCap snapshot: {e}")

            return data
        
        logger.info(f"Fetching CMC listings (start={start}, limit={limit})")
        
        params = {
            "start": start,
            "limit": min(limit, 5000),  # API max
            "convert": "USD",
            "sort": "market_cap",
            "sort_dir": "desc"
        }
        
        try:
            response = self._request("/v1/cryptocurrency/listings/latest", params)
            data = response.get("data", [])
            
            logger.info(f"Fetched {len(data)} listings from CMC")
            
            # Cache the full response
            save_cache(response, cache_key)

            # 🔹 Rohdaten-Snapshot über zentralen Collector speichern
            if collect_raw_marketcap and data:
                try:
                    collect_raw_marketcap(data)
                except Exception as e:
                    logger.warning(f"Could not collect MarketCap snapshot: {e}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch CMC listings: {e}")
            return []
    
    def get_all_listings(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get all available listings (up to 5000).
        
        Returns:
            List of all cryptocurrency dicts
        """
        return self.get_listings(start=1, limit=5000, use_cache=use_cache)
    
    def build_symbol_map(
        self,
        listings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a symbol → data mapping for fast lookups.
        
        Args:
            listings: CMC listings (default: fetch all)
            
        Returns:
            Dict mapping symbol (uppercase) to full CMC data
            
        Note:
            If multiple coins share a symbol, only the highest-ranked is kept.
        """
        if listings is None:
            listings = self.get_all_listings()
        
        symbol_map = {}
        collisions = []
        
        for item in listings:
            symbol = item.get("symbol", "").upper()
            
            if not symbol:
                continue
            
            # Collision detection
            if symbol in symbol_map:
                # Keep higher-ranked (lower cmc_rank number)
                existing_rank = symbol_map[symbol].get("cmc_rank", float('inf'))
                new_rank = item.get("cmc_rank", float('inf'))
                
                if new_rank < existing_rank:
                    collisions.append({
                        "symbol": symbol,
                        "replaced": symbol_map[symbol].get("name"),
                        "with": item.get("name")
                    })
                    symbol_map[symbol] = item
                else:
                    collisions.append({
                        "symbol": symbol,
                        "kept": symbol_map[symbol].get("name"),
                        "ignored": item.get("name")
                    })
            else:
                symbol_map[symbol] = item
        
        if collisions:
            logger.warning(f"Found {len(collisions)} symbol collisions (kept higher-ranked)")
            logger.debug(f"Collisions: {collisions[:10]}")  # Show first 10
        
        logger.info(f"Built symbol map with {len(symbol_map)} unique symbols")
        return symbol_map
    
    def get_market_cap_for_symbol(
        self,
        symbol: str,
        symbol_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[float]:
        """
        Get market cap for a specific symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'BTC')
            symbol_map: Pre-built symbol map (default: build from listings)
            
        Returns:
            Market cap in USD or None if not found
        """
        if symbol_map is None:
            symbol_map = self.build_symbol_map()
        
        symbol = symbol.upper()
        data = symbol_map.get(symbol)
        
        if not data:
            return None
        
        try:
            return data["quote"]["USD"]["market_cap"]
        except (KeyError, TypeError):
            return None

```

### `scanner/clients/mapping.py`

**SHA256:** `02c9c16ef03964e8bcc92f905fbd0078203bec98cf6099509ae8fb5ffe1617e5`

```python
"""
Mapping layer between MEXC symbols and CMC market cap data.

Handles:
- Symbol-based matching (primary)
- Collision detection (multiple CMC assets per symbol)
- Confidence scoring
- Manual overrides
- Mapping reports

This is a CRITICAL component - incorrect mapping = corrupted scores.
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from ..utils.logging_utils import get_logger
from ..utils.io_utils import load_json, save_json


logger = get_logger(__name__)


class MappingResult:
    """Result of a mapping operation."""
    
    def __init__(
        self,
        mexc_symbol: str,
        cmc_data: Optional[Dict[str, Any]] = None,
        confidence: str = "none",
        method: str = "none",
        collision: bool = False,
        notes: Optional[str] = None
    ):
        self.mexc_symbol = mexc_symbol
        self.cmc_data = cmc_data
        self.confidence = confidence  # "high", "medium", "low", "none"
        self.method = method
        self.collision = collision
        self.notes = notes
    
    @property
    def mapped(self) -> bool:
        """Check if mapping was successful."""
        return self.cmc_data is not None
    
    @property
    def base_asset(self) -> str:
        """Extract base asset from MEXC symbol (e.g., BTCUSDT -> BTC)."""
        # Remove USDT suffix
        if self.mexc_symbol.endswith("USDT"):
            return self.mexc_symbol[:-4]
        return self.mexc_symbol
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "mexc_symbol": self.mexc_symbol,
            "base_asset": self.base_asset,
            "mapped": self.mapped,
            "confidence": self.confidence,
            "method": self.method,
            "collision": self.collision,
            "notes": self.notes,
            "cmc_data": {
                "id": self.cmc_data.get("id") if self.cmc_data else None,
                "symbol": self.cmc_data.get("symbol") if self.cmc_data else None,
                "name": self.cmc_data.get("name") if self.cmc_data else None,
                "slug": self.cmc_data.get("slug") if self.cmc_data else None,
                "market_cap": self._get_market_cap() if self.cmc_data else None,
            }
        }
    
    def _get_market_cap(self) -> Optional[float]:
        """Extract market cap from CMC data."""
        try:
            return self.cmc_data["quote"]["USD"]["market_cap"]
        except (KeyError, TypeError):
            return None


class SymbolMapper:
    """
    Maps MEXC symbols to CMC market cap data.
    """
    
    def __init__(
        self,
        overrides_file: str = "config/mapping_overrides.json"
    ):
        """
        Initialize mapper.
        
        Args:
            overrides_file: Path to manual overrides JSON
        """
        self.overrides_file = Path(overrides_file)
        self.overrides = self._load_overrides()
        
        # Statistics
        self.stats = {
            "total": 0,
            "mapped": 0,
            "unmapped": 0,
            "collisions": 0,
            "overrides_used": 0,
            "confidence": {
                "high": 0,
                "medium": 0,
                "low": 0,
                "none": 0
            }
        }
    
    def _load_overrides(self) -> Dict[str, Any]:
        """Load manual mapping overrides."""
        if not self.overrides_file.exists():
            logger.info(f"No overrides file found at {self.overrides_file}")
            return {}
        
        try:
            overrides = load_json(self.overrides_file)
            logger.info(f"Loaded {len(overrides)} mapping overrides")
            return overrides
        except Exception as e:
            logger.error(f"Failed to load overrides: {e}")
            return {}
    
    def map_symbol(
        self,
        mexc_symbol: str,
        cmc_symbol_map: Dict[str, Dict[str, Any]]
    ) -> MappingResult:
        """
        Map a single MEXC symbol to CMC data.
        
        Args:
            mexc_symbol: MEXC trading pair (e.g., 'BTCUSDT')
            cmc_symbol_map: Symbol -> CMC data mapping
            
        Returns:
            MappingResult with confidence + collision info
        """
        # Extract base asset
        base_asset = mexc_symbol[:-4] if mexc_symbol.endswith("USDT") else mexc_symbol
        base_asset_upper = base_asset.upper()
        
        # Check overrides first
        if base_asset_upper in self.overrides:
            override = self.overrides[base_asset_upper]
            
            # Override can specify CMC symbol or "exclude"
            if override == "exclude":
                return MappingResult(
                    mexc_symbol=mexc_symbol,
                    cmc_data=None,
                    confidence="none",
                    method="override_exclude",
                    notes="Manually excluded via overrides"
                )
            
            # Try to find CMC data for override symbol
            override_symbol = override.upper()
            if override_symbol in cmc_symbol_map:
                self.stats["overrides_used"] += 1
                return MappingResult(
                    mexc_symbol=mexc_symbol,
                    cmc_data=cmc_symbol_map[override_symbol],
                    confidence="high",
                    method="override_match",
                    notes=f"Overridden to {override_symbol}"
                )
        
        # Direct symbol match
        if base_asset_upper in cmc_symbol_map:
            return MappingResult(
                mexc_symbol=mexc_symbol,
                cmc_data=cmc_symbol_map[base_asset_upper],
                confidence="high",
                method="symbol_exact_match"
            )
        
        # No match found
        return MappingResult(
            mexc_symbol=mexc_symbol,
            cmc_data=None,
            confidence="none",
            method="no_match",
            notes=f"Symbol {base_asset_upper} not found in CMC data"
        )
    
    def map_universe(
        self,
        mexc_symbols: List[str],
        cmc_symbol_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, MappingResult]:
        """
        Map entire MEXC universe to CMC data.
        
        Args:
            mexc_symbols: List of MEXC trading pairs
            cmc_symbol_map: CMC symbol -> data mapping
            
        Returns:
            Dict mapping mexc_symbol -> MappingResult
        """
        logger.info(f"Mapping {len(mexc_symbols)} MEXC symbols to CMC data")
        
        results = {}
        self.stats["total"] = len(mexc_symbols)
        
        for symbol in mexc_symbols:
            result = self.map_symbol(symbol, cmc_symbol_map)
            results[symbol] = result
            
            # Update stats
            if result.mapped:
                self.stats["mapped"] += 1
            else:
                self.stats["unmapped"] += 1
            
            if result.collision:
                self.stats["collisions"] += 1
            
            self.stats["confidence"][result.confidence] += 1
        
        # Log summary
        logger.info(f"Mapping complete:")
        logger.info(f"  Mapped: {self.stats['mapped']}/{self.stats['total']}")
        logger.info(f"  Unmapped: {self.stats['unmapped']}")
        logger.info(f"  Collisions: {self.stats['collisions']}")
        logger.info(f"  Confidence: {self.stats['confidence']}")
        logger.info(f"  Overrides used: {self.stats['overrides_used']}")
        
        return results
    
    def generate_reports(
        self,
        mapping_results: Dict[str, MappingResult],
        output_dir: str = "reports"
    ) -> None:
        """
        Generate mapping reports.
        
        Creates:
        - unmapped_symbols.json: Symbols without CMC match
        - mapping_collisions.json: Symbols with multiple CMC candidates
        - mapping_stats.json: Overall statistics
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Unmapped symbols
        unmapped = [
            {
                "mexc_symbol": result.mexc_symbol,
                "base_asset": result.base_asset,
                "notes": result.notes
            }
            for result in mapping_results.values()
            if not result.mapped
        ]
        
        unmapped_file = output_path / "unmapped_symbols.json"
        save_json(unmapped, unmapped_file)
        logger.info(f"Saved {len(unmapped)} unmapped symbols to {unmapped_file}")
        
        # Collisions
        collisions = [
            result.to_dict()
            for result in mapping_results.values()
            if result.collision
        ]
        
        collisions_file = output_path / "mapping_collisions.json"
        save_json(collisions, collisions_file)
        logger.info(f"Saved {len(collisions)} collisions to {collisions_file}")
        
        # Stats
        stats_file = output_path / "mapping_stats.json"
        save_json(self.stats, stats_file)
        logger.info(f"Saved mapping stats to {stats_file}")
    
    def suggest_overrides(
        self,
        mapping_results: Dict[str, MappingResult],
        output_file: str = "reports/suggested_overrides.json"
    ) -> Dict[str, str]:
        """
        Generate suggested overrides for unmapped symbols.
        
        Returns:
            Dict of base_asset -> "exclude" (user must review)
        """
        suggestions = {}
        
        for result in mapping_results.values():
            if not result.mapped and result.base_asset not in self.overrides:
                # Suggest exclusion (user can change to proper symbol)
                suggestions[result.base_asset] = "exclude"
        
        if suggestions:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_json(suggestions, output_path, indent=2)
            logger.info(f"Generated {len(suggestions)} override suggestions: {output_file}")
        
        return suggestions

```

### `scanner/utils/logging_utils.py`

**SHA256:** `16b928c91c236b53ca1e7a9d74f6ba890d50b3afb2ae508d3962c1fe44bb2e50`

```python
"""
Logging utilities for the scanner.
Provides centralized logging with file rotation and console output.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(
    name: str = "scanner",
    level: str = "INFO",
    log_file: str | None = None,
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> logging.Logger:
    """
    Set up a logger with file and/or console handlers.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (default: logs/scanner_YYYY-MM-DD.log)
        log_to_console: Enable console output
        log_to_file: Enable file output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        if log_file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"scanner_{datetime.utcnow().strftime('%Y-%m-%d')}.log"
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "scanner") -> logging.Logger:
    """Get existing logger or create default one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger

```

### `scanner/utils/time_utils.py`

**SHA256:** `ed28e91229a8ee46f5154d1baa9ece921c37531327ee42ffd2ef635df7a456a0`

```python
"""
Time and date utilities.
All times are UTC-based for consistency.
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def utc_timestamp() -> str:
    """Get current UTC timestamp as ISO string (YYYY-MM-DDTHH:MM:SSZ)."""
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_date() -> str:
    """Get current UTC date as string (YYYY-MM-DD)."""
    return utc_now().strftime("%Y-%m-%d")


def parse_timestamp(ts: str) -> datetime:
    """
    Parse ISO timestamp to datetime.
    
    Args:
        ts: ISO timestamp string (e.g., "2025-01-17T12:00:00Z")
        
    Returns:
        Timezone-aware datetime object
    """
    # Handle both with and without 'Z'
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)


def timestamp_to_ms(dt: datetime) -> int:
    """Convert datetime to milliseconds since epoch (for APIs)."""
    return int(dt.timestamp() * 1000)


def ms_to_timestamp(ms: int) -> datetime:
    """Convert milliseconds since epoch to datetime."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

```

### `scanner/utils/__init__.py`

**SHA256:** `f230bbd04291338e0d737b6ea6813a830bdbd2cfff379a1b6ce8ade07fc98021`

```python
"""
Utility helpers for the scanner.

Modules:
- time_utils: time and date handling
- logging_utils: logging configuration helpers
- io_utils: file I/O helpers (JSON, Markdown, paths)
"""


```

### `scanner/utils/save_raw.py`

**SHA256:** `028ba8f22a65fca5ba1119dcbd3129689f2ef2e2623adb7add2a461c7984e3a8`

```python
import os
import pandas as pd
from datetime import datetime


def save_raw_snapshot(
    df: pd.DataFrame,
    source_name: str = "unknown",
    require_parquet: bool = False
):
    """
    Speichert die Rohdaten eines Runs im Ordner <BASEDIR>/<RUN_ID>/.

    - BASEDIR: per ENV `RAW_SNAPSHOT_BASEDIR` konfigurierbar (default: data/raw)
    - RUN_ID: wird einmal pro Run/Prozess erzeugt (ENV `RAW_SNAPSHOT_RUN_ID`)
             -> sorgt dafür, dass alle Snapshots eines Runs im selben Ordner landen.

    Exportiert immer zwei Formate:
      1. Parquet (für Analyse, effizient)
      2. CSV (für manuelle Kontrolle, optional gzip per `RAW_SNAPSHOT_CSV_GZIP=1`)
    """

    # 1) Ein Ordner pro Run: RUN_ID einmalig erzeugen und für den Prozess merken
    run_id = os.getenv("RAW_SNAPSHOT_RUN_ID")
    if not run_id:
        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        os.environ["RAW_SNAPSHOT_RUN_ID"] = run_id

    # 2) Basisordner konfigurierbar machen (z. B. snapshots/raw in GitHub Actions)
    base_root = os.getenv("RAW_SNAPSHOT_BASEDIR", os.path.join("data", "raw"))
    base_dir = os.path.join(base_root, run_id)
    os.makedirs(base_dir, exist_ok=True)

    parquet_path = os.path.join(base_dir, f"{source_name}.parquet")

    csv_gzip = os.getenv("RAW_SNAPSHOT_CSV_GZIP", "0").lower() in ("1", "true", "yes")
    csv_filename = f"{source_name}.csv.gz" if csv_gzip else f"{source_name}.csv"
    csv_path = os.path.join(base_dir, csv_filename)

    saved_paths = {"parquet": None, "csv": None}

    # --- 1️⃣ Parquet speichern ---
    try:
        df.to_parquet(parquet_path, index=False)
        print(f"[INFO] Raw data snapshot saved as Parquet: {parquet_path}")
        saved_paths["parquet"] = parquet_path
    except Exception as e:
        print(f"[WARN] Parquet export failed ({e}). You may need to install 'pyarrow' or 'fastparquet'.")

    # Wenn Parquet zwingend ist, zumindest klar & eindeutig loggen
    if require_parquet and not saved_paths["parquet"]:
        print("[ERROR] Parquet export is REQUIRED for this snapshot but failed.")

    # --- 2️⃣ CSV speichern ---
    try:
        if csv_gzip:
            df.to_csv(csv_path, index=False, compression="gzip")
        else:
            df.to_csv(csv_path, index=False)
        print(f"[INFO] Raw data snapshot saved as CSV: {csv_path}")
        saved_paths["csv"] = csv_path
    except Exception as e:
        print(f"[ERROR] CSV export failed: {e}")

    # --- Ergebnis ---
    if saved_paths["parquet"] or saved_paths["csv"]:
        print(f"[INFO] Raw data snapshot complete → {base_dir}")
    else:
        print("[ERROR] Could not save any raw data snapshot.")

    return saved_paths

```

### `scanner/utils/io_utils.py`

**SHA256:** `677ddb859b6128ad55a7f44837a3a807e7c0cc5fc23f3be564d32e558d3fee7a`

```python
"""
I/O utilities for file operations and caching.
"""

import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


def load_json(filepath: str | Path) -> dict | list:
    """
    Load JSON from file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    filepath = Path(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, filepath: str | Path, indent: int = 2) -> None:
    """
    Save data as JSON to file.
    
    Args:
        data: Data to serialize
        filepath: Output file path
        indent: JSON indentation (default: 2)
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def get_cache_path(cache_type: str, date: Optional[str] = None) -> Path:
    """
    Get standardized cache file path.
    
    Args:
        cache_type: Type of cache (e.g., 'universe', 'marketcap', 'klines')
        date: Date string (YYYY-MM-DD), defaults to today
        
    Returns:
        Path to cache file
    """
    if date is None:
        from .time_utils import utc_date
        date = utc_date()
    
    cache_dir = Path("data/raw") / date
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir / f"{cache_type}.json"


def cache_exists(cache_type: str, date: Optional[str] = None) -> bool:
    """Check if cache file exists for given type and date."""
    return get_cache_path(cache_type, date).exists()


def load_cache(cache_type: str, date: Optional[str] = None) -> Optional[dict | list]:
    """
    Load cached data if exists.
    
    Returns:
        Cached data or None if not found
    """
    cache_path = get_cache_path(cache_type, date)
    if cache_path.exists():
        return load_json(cache_path)
    return None


def save_cache(data: Any, cache_type: str, date: Optional[str] = None) -> None:
    """Save data to cache."""
    cache_path = get_cache_path(cache_type, date)
    save_json(data, cache_path)

```

### `scanner/utils/raw_collector.py`

**SHA256:** `91cf6703951a3b0a678f39b3a7956cbc4b51c747e55a601c05e0ce95ce019482`

```python
"""
Raw Data Collector Utilities
============================

Diese Datei bündelt alle Funktionen, die Rohdaten aus der Pipeline
(OHLCV, MarketCap, Feature-Inputs etc.) zentral speichern.

Ziel:
- Einheitliche Logik für Speicherung & Logging
- Immer beide Formate (Parquet + CSV)
- Kein Code-Duplikat in den Clients oder Pipelines
"""

import json
import pandas as pd
from typing import List, Dict, Any
from scanner.utils.save_raw import save_raw_snapshot


# ===============================================================
# OHLCV Snapshots
# ===============================================================

def collect_raw_ohlcv(results: Dict[str, Dict[str, Any]]):
    """
    Speichert alle OHLCV-Daten als Rohdaten-Snapshot.
    Erwartet das Dictionary, das aus OHLCVFetcher.fetch_all() zurückkommt.
    """
    if not results:
        print("[WARN] No OHLCV data to snapshot.")
        return None

    try:
        flat_records = []
        for symbol, tf_data in results.items():
            for tf, candles in tf_data.items():
                for candle in candles:
                    if not isinstance(candle, (list, tuple)) or len(candle) < 6:
                        print(f"[WARN] Skipping malformed candle for {symbol} {tf}: {candle}")
                        continue

                    flat_records.append({
                        "symbol": symbol,
                        "timeframe": tf,
                        "open_time": candle[0],
                        "close_time": candle[6] if len(candle) > 6 else None,
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
                        "quote_volume": candle[7] if len(candle) > 7 else None,
                    })
        df = pd.DataFrame(flat_records)
        return save_raw_snapshot(df, source_name="ohlcv_snapshot")
    except Exception as e:
        print(f"[WARN] Could not collect OHLCV snapshot: {e}")
        return None


# ===============================================================
# MarketCap Snapshots
# ===============================================================

def collect_raw_marketcap(data: List[Dict[str, Any]]):
    """
    Speichert alle MarketCap-Daten (Listings) als Rohdaten-Snapshot.
    Erwartet die Ausgabe aus MarketCapClient.get_listings() oder get_all_listings().

    Wichtig: CMC liefert verschachtelte Strukturen (z.B. quote -> USD -> ...).
    Für Parquet müssen wir das in eine flache Tabelle umwandeln.
    """
    if not data:
        print("[WARN] No MarketCap data to snapshot.")
        return None

    try:
        # Flach machen: quote.USD.* etc. -> quote__USD__*
        df = pd.json_normalize(data, sep="__")

        # Restliche dict/list Werte Parquet-sicher machen (als JSON-String)
        for col in df.columns:
            if df[col].dtype == "object":
                if df[col].map(lambda v: isinstance(v, (dict, list))).any():
                    df[col] = df[col].map(
                        lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                    )

        # Parquet ist hier zwingend (und sollte nach Normalisierung sauber durchlaufen)
        return save_raw_snapshot(df, source_name="marketcap_snapshot", require_parquet=True)
    except Exception as e:
        print(f"[WARN] Could not collect MarketCap snapshot: {e}")
        return None


# ===============================================================
# Feature Snapshots (optional für spätere Erweiterung)
# ===============================================================

def collect_raw_features(df: pd.DataFrame, stage_name: str = "features"):
    """
    Speichert Feature-Inputs oder Zwischenstufen.
    Ideal für Debugging oder Backtests.
    """
    if df is None or df.empty:
        print("[WARN] No feature data to snapshot.")
        return None

    try:
        return save_raw_snapshot(df, source_name=f"{stage_name}_snapshot")
    except Exception as e:
        print(f"[WARN] Could not collect feature snapshot: {e}")
        return None

```

### `scanner/backtest/e2_model.py`

**SHA256:** `26770eb0054087e9a7598e43a8b3bb8d5122164df49ed9b4f0219b24091347fa`

```python
from __future__ import annotations

from datetime import date, timedelta
from collections.abc import Iterable
from typing import Any, Dict, Mapping, Optional


DEFAULT_T_TRIGGER_MAX = 5
DEFAULT_T_HOLD = 10
DEFAULT_THRESHOLDS_PCT = (10.0, 20.0)


def _to_float(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def _threshold_key(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _parse_date(value: str) -> Optional[date]:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _resolve_thresholds(thresholds_pct: Any) -> list[float]:
    if thresholds_pct is None:
        raw = DEFAULT_THRESHOLDS_PCT
    else:
        raw = thresholds_pct

    if isinstance(raw, (str, bytes)) or not isinstance(raw, Iterable):
        raise ValueError("thresholds_pct must be list-like or null")

    resolved: set[float] = set()
    for value in raw:
        numeric = _to_float(value)
        if numeric is None:
            continue
        resolved.add(numeric)
    resolved.add(10.0)
    resolved.add(20.0)
    return sorted(resolved)


def _resolve_param_int(params: Mapping[str, Any], aliases: tuple[str, ...], default: int) -> int:
    values: list[int] = []
    for alias in aliases:
        if alias not in params:
            continue
        values.append(int(params[alias]))

    if not values:
        return default

    if any(value != values[0] for value in values[1:]):
        alias_list = ", ".join(aliases)
        raise ValueError(f"Conflicting values for parameter aliases: {alias_list}")

    return values[0]


def _trade_level_status(setup_type: str, trade_levels: Mapping[str, Any]) -> tuple[bool, bool]:
    if setup_type == "breakout":
        has_entry_trigger = "entry_trigger" in trade_levels
        has_breakout_level = "breakout_level_20" in trade_levels
        if not has_entry_trigger and not has_breakout_level:
            return True, False

        trigger = _to_float(trade_levels.get("entry_trigger"))
        breakout = _to_float(trade_levels.get("breakout_level_20"))
        trigger_invalid = has_entry_trigger and (trigger is None or trigger <= 0)
        breakout_invalid = has_breakout_level and (breakout is None or breakout <= 0)

        if has_entry_trigger and has_breakout_level:
            if trigger_invalid and breakout_invalid:
                return False, True
            return False, False

        if has_entry_trigger and trigger_invalid:
            return False, True
        if has_breakout_level and breakout_invalid:
            return False, True
        return False, False

    if setup_type == "reversal":
        if "entry_trigger" not in trade_levels:
            return True, False
        trigger = _to_float(trade_levels.get("entry_trigger"))
        if trigger is None or trigger <= 0:
            return False, True
        return False, False

    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone")
        if not isinstance(zone, Mapping):
            return True, False

        missing = "lower" not in zone or "upper" not in zone
        if missing:
            return True, False

        lower = _to_float(zone.get("lower"))
        upper = _to_float(zone.get("upper"))
        if lower is None or upper is None or lower <= 0 or upper <= 0 or lower > upper:
            return False, True
        return False, False

    return True, False


def _is_triggered(setup_type: str, close: float, trade_levels: Mapping[str, Any]) -> bool:
    if setup_type == "breakout":
        trigger = _to_float(trade_levels.get("entry_trigger"))
        fallback = _to_float(trade_levels.get("breakout_level_20"))
        level = trigger if trigger is not None and trigger > 0 else fallback
        return level is not None and level > 0 and close >= level

    if setup_type == "reversal":
        trigger = _to_float(trade_levels.get("entry_trigger"))
        return trigger is not None and trigger > 0 and close >= trigger

    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone")
        if not isinstance(zone, Mapping):
            return False
        lower = _to_float(zone.get("lower"))
        upper = _to_float(zone.get("upper"))
        if lower is None or upper is None or lower > upper:
            return False
        return lower <= close <= upper

    return False


def evaluate_e2_candidate(
    *,
    t0_date: str,
    setup_type: str,
    trade_levels: Mapping[str, Any],
    price_series: Mapping[str, Mapping[str, Any]],
    params: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    runtime_params = params or {}
    t_trigger_max = _resolve_param_int(
        runtime_params,
        ("T_trigger_max", "t_trigger_max", "T_trigger_max_days", "t_trigger_max_days"),
        DEFAULT_T_TRIGGER_MAX,
    )
    t_hold = _resolve_param_int(
        runtime_params,
        ("T_hold", "t_hold", "T_hold_days", "t_hold_days"),
        DEFAULT_T_HOLD,
    )
    thresholds = _resolve_thresholds(runtime_params.get("thresholds_pct"))

    hits: Dict[str, Optional[bool]] = {_threshold_key(threshold): None for threshold in thresholds}

    t0 = _parse_date(t0_date)
    missing_trade_levels, invalid_trade_levels = _trade_level_status(setup_type, trade_levels)
    if t0 is None:
        return {
            "reason": "missing_price_series",
            "t_trigger_date": None,
            "t_trigger_day_offset": None,
            "entry_price": None,
            "hit_10": None,
            "hit_20": None,
            "hits": hits,
            "mfe_pct": None,
            "mae_pct": None,
        }

    has_evaluable_close = False
    trigger_date: Optional[date] = None
    trigger_day_offset: Optional[int] = None
    entry_price: Optional[float] = None

    for offset in range(t_trigger_max + 1):
        day = t0 + timedelta(days=offset)
        candle = price_series.get(day.isoformat())
        close = _to_float(candle.get("close") if isinstance(candle, Mapping) else None)
        if close is None:
            continue
        has_evaluable_close = True
        if _is_triggered(setup_type, close, trade_levels):
            trigger_date = day
            trigger_day_offset = offset
            entry_price = close
            break

    missing_price_series = not has_evaluable_close
    invalid_entry_price = trigger_date is not None and (entry_price is None or entry_price <= 0)
    no_trigger = trigger_date is None

    insufficient_forward_history = False
    max_high: Optional[float] = None
    min_low: Optional[float] = None
    if trigger_date is not None:
        highs: list[float] = []
        lows: list[float] = []
        for hold_offset in range(1, t_hold + 1):
            hold_day = trigger_date + timedelta(days=hold_offset)
            candle = price_series.get(hold_day.isoformat())
            high = _to_float(candle.get("high") if isinstance(candle, Mapping) else None)
            low = _to_float(candle.get("low") if isinstance(candle, Mapping) else None)
            if high is None or low is None:
                insufficient_forward_history = True
                break
            highs.append(high)
            lows.append(low)

        if not insufficient_forward_history and highs and entry_price is not None and entry_price > 0:
            max_high = max(highs)
            min_low = min(lows)
            for threshold in thresholds:
                target = entry_price * (1 + threshold / 100.0)
                hits[_threshold_key(threshold)] = max_high >= target

    if missing_price_series:
        reason = "missing_price_series"
    elif invalid_entry_price:
        reason = "invalid_entry_price"
    elif missing_trade_levels:
        reason = "missing_trade_levels"
    elif invalid_trade_levels:
        reason = "invalid_trade_levels"
    elif no_trigger:
        reason = "no_trigger"
    elif insufficient_forward_history:
        reason = "insufficient_forward_history"
    else:
        reason = "ok"

    hit_10 = hits.get("10")
    hit_20 = hits.get("20")

    mfe_pct = None
    mae_pct = None
    if reason == "ok" and entry_price is not None and entry_price > 0 and max_high is not None and min_low is not None:
        mfe_pct = (max_high / entry_price - 1.0) * 100.0
        mae_pct = (min_low / entry_price - 1.0) * 100.0

    return {
        "reason": reason,
        "t_trigger_date": trigger_date.isoformat() if trigger_date is not None else None,
        "t_trigger_day_offset": trigger_day_offset,
        "entry_price": entry_price,
        "hit_10": hit_10,
        "hit_20": hit_20,
        "hits": hits,
        "mfe_pct": mfe_pct,
        "mae_pct": mae_pct,
    }

```

### `scanner/backtest/__init__.py`

**SHA256:** `d02e454c04830601cf9d21a3de0fc4a8daf55a35b59ad71b881c67c9cf62d499`

```python
from .e2_model import evaluate_e2_candidate

__all__ = ["evaluate_e2_candidate"]

```

### `scanner/pipeline/shortlist.py`

**SHA256:** `c7e29d2b5d96122834993daf1161fa21e0c5247b5df04396682980c3ffb593ad`

```python
"""
Shortlist Selection (Cheap Pass)
=================================

Reduces filtered universe to a shortlist for expensive operations (OHLCV fetch).
Uses cheap metrics (24h volume) to rank and select top N candidates.
"""

import logging
import math
from typing import List, Dict, Any

from scanner.config import ScannerConfig

from .cross_section import percent_rank_average_ties

logger = logging.getLogger(__name__)


class ShortlistSelector:
    """Select top candidates based on cheap-pass proxy liquidity."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize shortlist selector from central config defaults."""
        cfg = ScannerConfig(raw=config)
        self.max_size = int(cfg.budget_shortlist_size)
        self.pre_shortlist_market_cap_floor_usd = float(cfg.pre_shortlist_market_cap_floor_usd)

        if self.max_size < 1:
            raise ValueError(f"budget.shortlist_size ({self.max_size}) must be >= 1")
        if self.pre_shortlist_market_cap_floor_usd < 0:
            raise ValueError(
                "budget.pre_shortlist_market_cap_floor_usd "
                f"({self.pre_shortlist_market_cap_floor_usd}) must be >= 0"
            )

        logger.info(
            "Shortlist initialized: max_size=%s, pre_shortlist_market_cap_floor_usd=%.2f",
            self.max_size,
            self.pre_shortlist_market_cap_floor_usd,
        )

    def _attach_proxy_liquidity_score(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach proxy_liquidity_score based on quote_volume_24h percent-rank (log-scaled input)."""
        if not rows:
            return []

        log_volumes: List[float] = []
        for row in rows:
            vol = float(row.get('quote_volume_24h', 0) or 0)
            log_volumes.append(math.log1p(max(0.0, vol)))

        percent_scores = percent_rank_average_ties(log_volumes)

        enriched: List[Dict[str, Any]] = []
        for row, score in zip(rows, percent_scores):
            r = dict(row)
            r['proxy_liquidity_score'] = round(float(score), 6)
            r['proxy_liquidity_population_n'] = len(rows)
            enriched.append(r)

        return enriched

    def select(self, filtered_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select top-N symbols via cheap-pass ranking under budget + floor constraints."""
        if not filtered_symbols:
            logger.warning("No symbols to shortlist (empty input)")
            return []

        eligible_symbols = [
            row for row in filtered_symbols
            if float(row.get('market_cap', 0) or 0) >= self.pre_shortlist_market_cap_floor_usd
        ]

        with_proxy_score = self._attach_proxy_liquidity_score(eligible_symbols)

        # Deterministic ordering: score desc, volume desc, symbol asc.
        sorted_symbols = sorted(
            with_proxy_score,
            key=lambda x: (
                -float(x.get('proxy_liquidity_score', 0) or 0),
                -float(x.get('quote_volume_24h', 0) or 0),
                str(x.get('symbol', '')),
            ),
        )

        shortlist = sorted_symbols[:self.max_size]

        logger.info(
            "Shortlist selected: %s symbols from %s eligible (%s input before floor; top %.1f%% of eligible by volume)",
            len(shortlist),
            len(eligible_symbols),
            len(filtered_symbols),
            (len(shortlist) / len(eligible_symbols) * 100.0) if eligible_symbols else 0.0,
        )

        if shortlist:
            max_vol = float(shortlist[0].get('quote_volume_24h', 0) or 0)
            min_vol = float(shortlist[-1].get('quote_volume_24h', 0) or 0)
            logger.info(f"Volume range: ${max_vol/1e6:.2f}M - ${min_vol/1e6:.2f}M")

        return shortlist

    def get_shortlist_stats(
        self,
        filtered_symbols: List[Dict[str, Any]],
        shortlist: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get statistics about shortlist selection."""
        if not filtered_symbols:
            return {
                'input_count': 0,
                'shortlist_count': 0,
                'reduction_rate': '0%',
                'volume_coverage': '0%'
            }

        total_volume = sum(float(s.get('quote_volume_24h', 0) or 0) for s in filtered_symbols)
        shortlist_volume = sum(float(s.get('quote_volume_24h', 0) or 0) for s in shortlist)

        coverage = (shortlist_volume / total_volume * 100) if total_volume > 0 else 0

        return {
            'input_count': len(filtered_symbols),
            'shortlist_count': len(shortlist),
            'reduction_rate': f"{(1 - len(shortlist)/len(filtered_symbols))*100:.1f}%",
            'total_volume': f"${total_volume/1e6:.2f}M",
            'shortlist_volume': f"${shortlist_volume/1e6:.2f}M",
            'volume_coverage': f"{coverage:.1f}%"
        }

```

### `scanner/pipeline/regime.py`

**SHA256:** `d91b92a42f99c5e4063cb1b2412da752fff19b90a91b0c83a8a73c8857312151`

```python
"""BTC regime helpers for report-level risk context."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def compute_btc_regime_from_1d_features(features_1d: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute canonical BTC regime payload from 1D BTC features."""
    features_1d = features_1d or {}
    close = _to_float(features_1d.get("close"))
    ema20 = _to_float(features_1d.get("ema_20"))
    ema50 = _to_float(features_1d.get("ema_50"))

    close_gt_ema50 = (close > ema50) if close is not None and ema50 is not None else None
    ema20_gt_ema50 = (ema20 > ema50) if ema20 is not None and ema50 is not None else None

    if close_gt_ema50 is None or ema20_gt_ema50 is None:
        state = "NEUTRAL"
    elif close_gt_ema50 and ema20_gt_ema50:
        state = "RISK_ON"
    else:
        state = "RISK_OFF"

    return {
        "state": state,
        "multiplier_risk_on": 1.0,
        "multiplier_risk_off": 0.85,
        "checks": {
            "close_gt_ema50": close_gt_ema50,
            "ema20_gt_ema50": ema20_gt_ema50,
        },
    }


def compute_btc_regime(mexc_client: Any, feature_engine: Any, lookback_1d: int, asof_ts_ms: int) -> Dict[str, Any]:
    """Fetch BTCUSDT 1D candles and compute report-level regime payload."""
    try:
        btc_klines_1d = mexc_client.get_klines("BTCUSDT", "1d", limit=int(lookback_1d))
        btc_features = feature_engine.compute_all({"BTCUSDT": {"1d": btc_klines_1d}}, asof_ts_ms=asof_ts_ms)
        return compute_btc_regime_from_1d_features(btc_features.get("BTCUSDT", {}).get("1d", {}))
    except Exception as exc:  # pragma: no cover - defensive runtime fallback
        logger.warning("BTC regime fallback to NEUTRAL due to recoverable error: %s", exc)
        return compute_btc_regime_from_1d_features({})


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


```

### `scanner/pipeline/filters.py`

**SHA256:** `edb0370c285a8bda17c9a86317ea80723e819787b3b2eb1847bb9616ec6c7301`

```python
"""Universe filtering for pre-shortlist pool construction.

Hard excludes in this stage are intentionally limited to:
- pre-shortlist market-cap floor guardrail
- quote asset allowlist
- safety exclusions (stable/wrapped/leveraged/etc.)
- hard risk blockers (denylist + major unlock)

Legacy market-cap/volume/share limits are loaded as soft-prior context only.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml

logger = logging.getLogger(__name__)


class UniverseFilters:
    """Filters for reducing MEXC universe to tradable MidCaps."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize filters with config.
        
        Args:
            config: Config dict with 'filters' section
        """
        legacy_filters = config.get('filters', {})
        universe_cfg = config.get('universe_filters', {})
        exclusions_cfg = config.get('exclusions', {})
        risk_cfg = config.get('risk_flags', {})

        mcap_cfg = universe_cfg.get('market_cap', {})
        volume_cfg = universe_cfg.get('volume', {})
        history_cfg = universe_cfg.get('history', {})

        budget_cfg = config.get('budget', {})

        # Market Cap context bounds (in USD, no hard exclude semantics).
        self.mcap_min = mcap_cfg.get('min_usd', legacy_filters.get('mcap_min', 100_000_000))  # 100M
        self.mcap_max = mcap_cfg.get('max_usd', legacy_filters.get('mcap_max', 3_000_000_000))  # 3B

        # Hard pre-shortlist floor guardrail.
        self.pre_shortlist_market_cap_floor_usd = float(budget_cfg.get('pre_shortlist_market_cap_floor_usd', 25_000_000))

        # Liquidity context (legacy hard gates are now soft priors only)
        self.min_turnover_24h = float(volume_cfg.get('min_turnover_24h', 0.03))
        if 'min_mexc_quote_volume_24h_usdt' in volume_cfg:
            self.min_mexc_quote_volume_24h_usdt = float(volume_cfg.get('min_mexc_quote_volume_24h_usdt', 5_000_000))
        else:
            self.min_mexc_quote_volume_24h_usdt = float(
                volume_cfg.get('min_quote_volume_24h', legacy_filters.get('min_volume_24h', 5_000_000))
            )
        self.min_mexc_share_24h = float(volume_cfg.get('min_mexc_share_24h', 0.01))

        # Minimum 1d history used by OHLCV filtering step.
        self.min_history_days_1d = int(history_cfg.get('min_history_days_1d', 60))

        self.include_only_usdt_pairs = bool(universe_cfg.get('include_only_usdt_pairs', True))

        default_quote_allowlist = ['USDT', 'USDC', 'DAI', 'TUSD', 'FDUSD', 'USDP', 'BUSD']
        self.quote_allowlist = [str(q).upper() for q in universe_cfg.get('quote_allowlist', default_quote_allowlist)]

        default_patterns = {
            'stablecoin_patterns': ['USD', 'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD'],
            'wrapped_patterns': ['WBTC', 'WETH', 'WBNB'],
            'leveraged_patterns': ['UP', 'DOWN', 'BULL', 'BEAR'],
            'synthetic_patterns': [],
        }

        def _build_exclusion_patterns_from_new_config() -> List[str]:
            patterns: List[str] = []
            if exclusions_cfg.get('exclude_stablecoins', True):
                patterns.extend(exclusions_cfg.get('stablecoin_patterns', default_patterns['stablecoin_patterns']))
            if exclusions_cfg.get('exclude_wrapped_tokens', True):
                patterns.extend(exclusions_cfg.get('wrapped_patterns', default_patterns['wrapped_patterns']))
            if exclusions_cfg.get('exclude_leveraged_tokens', True):
                patterns.extend(exclusions_cfg.get('leveraged_patterns', default_patterns['leveraged_patterns']))
            if exclusions_cfg.get('exclude_synthetic_derivatives', False):
                patterns.extend(exclusions_cfg.get('synthetic_patterns', default_patterns['synthetic_patterns']))
            return [str(p).upper() for p in patterns]

        if 'exclusion_patterns' in legacy_filters:
            # Legacy override is key-presence based: [] explicitly disables exclusions.
            # A null value is treated as unset to avoid accidental broad allow-through.
            legacy_patterns = legacy_filters.get('exclusion_patterns')
            if legacy_patterns is None:
                logger.warning(
                    "filters.exclusion_patterns is null; treating as unset and falling back to exclusions.*"
                )
                self.exclusion_patterns = _build_exclusion_patterns_from_new_config()
            else:
                self.exclusion_patterns = [str(p).upper() for p in legacy_patterns]
        else:
            self.exclusion_patterns = _build_exclusion_patterns_from_new_config()

        self.minor_unlock_penalty_factor = float(risk_cfg.get('minor_unlock_penalty_factor', 0.9))
        self.denylist_path = Path(risk_cfg.get('denylist_file', 'config/denylist.yaml'))
        self.unlock_overrides_path = Path(risk_cfg.get('unlock_overrides_file', 'config/unlock_overrides.yaml'))

        self.denylist_symbols, self.denylist_bases = self._load_denylist(self.denylist_path)
        (
            self.major_unlock_symbols,
            self.major_unlock_bases,
            self.minor_unlock_symbols,
            self.minor_unlock_bases,
        ) = self._load_unlock_overrides(self.unlock_overrides_path)
        
        logger.info(
            f"Filters initialized: pre-shortlist MCAP floor>={self.pre_shortlist_market_cap_floor_usd/1e6:.1f}M, "
            f"legacy MCAP context {self.mcap_min/1e6:.0f}M-{self.mcap_max/1e9:.1f}B, "
            f"legacy liquidity priors turnover>={self.min_turnover_24h:.4f}, "
            f"mexc_volume>={self.min_mexc_quote_volume_24h_usdt/1e6:.1f}M, "
            f"mexc_share>={self.min_mexc_share_24h:.4f}"
        )

    @staticmethod
    def _safe_load_yaml(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    def _load_denylist(self, path: Path) -> tuple[set[str], set[str]]:
        data = self._safe_load_yaml(path)
        symbols = set()
        bases = set()

        hard_exclude = data.get('hard_exclude', {}) if isinstance(data.get('hard_exclude', {}), dict) else {}
        for key in ('symbols', 'symbol'):
            raw = hard_exclude.get(key, [])
            if isinstance(raw, str):
                raw = [raw]
            symbols.update(str(v).upper() for v in raw)

        for key in ('bases', 'base'):
            raw = hard_exclude.get(key, [])
            if isinstance(raw, str):
                raw = [raw]
            bases.update(str(v).upper() for v in raw)

        return symbols, bases

    def _load_unlock_overrides(self, path: Path) -> tuple[set[str], set[str], set[str], set[str]]:
        data = self._safe_load_yaml(path)
        major_symbols: set[str] = set()
        major_bases: set[str] = set()
        minor_symbols: set[str] = set()
        minor_bases: set[str] = set()

        entries = data.get('overrides', [])
        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list):
            return major_symbols, major_bases, minor_symbols, minor_bases

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            severity = str(entry.get('severity', '')).lower()
            days_to_unlock = entry.get('days_to_unlock')
            symbol = entry.get('symbol')
            base = entry.get('base')

            parsed_days = self._parse_days_to_unlock(days_to_unlock, symbol=symbol, base=base)
            if parsed_days is None:
                continue
            if parsed_days > 14:
                continue

            if severity == 'major':
                if symbol:
                    major_symbols.add(str(symbol).upper())
                if base:
                    major_bases.add(str(base).upper())
            elif severity == 'minor':
                if symbol:
                    minor_symbols.add(str(symbol).upper())
                if base:
                    minor_bases.add(str(base).upper())

        return major_symbols, major_bases, minor_symbols, minor_bases

    def _parse_days_to_unlock(
        self,
        value: Any,
        *,
        symbol: Optional[str] = None,
        base: Optional[str] = None,
    ) -> Optional[int]:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            identifier = symbol or base or '<unknown>'
            logger.warning("Invalid days_to_unlock for %s: %r", identifier, value)
            return None

        if parsed < 0:
            identifier = symbol or base or '<unknown>'
            logger.warning("Invalid days_to_unlock for %s: %r", identifier, value)
            return None

        return parsed
    
    def apply_all(
        self,
        symbols_with_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply all filters in sequence.
        
        Args:
            symbols_with_data: List of dicts with keys:
                - symbol: str (e.g. "BTCUSDT")
                - base: str (e.g. "BTC")
                - quote_volume_24h: float
                - market_cap: float (from CMC mapping)
        
        Returns:
            Filtered list
        """
        original_count = len(symbols_with_data)
        logger.info(f"Starting filters with {original_count} symbols")
        
        # Step 1: Hard pre-shortlist market-cap floor
        filtered = self._filter_pre_shortlist_market_cap_floor(symbols_with_data)
        logger.info(f"After pre-shortlist MCAP floor: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 2: Quote asset filter (USDT-only or stablecoin allowlist)
        filtered = self._filter_quote_assets(filtered)
        logger.info(f"After Quote filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 3: Liquidity stage is soft-prior only; no hard excludes.
        filtered = self._apply_soft_liquidity_priors(filtered)
        logger.info(f"After soft liquidity priors: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 4: Exclusions
        filtered = self._filter_exclusions(filtered)
        logger.info(f"After Exclusions filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 5: Risk hard-excludes and soft penalties
        filtered = self._apply_risk_flags(filtered)
        logger.info(f"After Risk filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")
        
        logger.info(f"Final universe: {len(filtered)} symbols "
                   f"(filtered out {original_count - len(filtered)})")
        
        return filtered
    
    def _filter_pre_shortlist_market_cap_floor(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply hard pre-shortlist market-cap floor guardrail."""
        filtered = []
        
        for sym_data in symbols:
            mcap = sym_data.get('market_cap')
            
            # Skip if no market cap data
            if mcap is None:
                continue
            
            # Hard guardrail: below floor is excluded before shortlist.
            if mcap >= self.pre_shortlist_market_cap_floor_usd:
                filtered.append(sym_data)
        
        return filtered
    

    def _extract_quote_asset(self, sym_data: Dict[str, Any]) -> Optional[str]:
        quote = sym_data.get('quote')
        if quote:
            return str(quote).upper()

        symbol = str(sym_data.get('symbol', '')).upper()
        for q in sorted(self.quote_allowlist, key=len, reverse=True):
            if symbol.endswith(q):
                return q

        return None

    def _filter_quote_assets(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter by quote asset according to include_only_usdt_pairs semantics."""
        filtered: List[Dict[str, Any]] = []

        for sym_data in symbols:
            quote = self._extract_quote_asset(sym_data)
            if self.include_only_usdt_pairs:
                if quote == 'USDT':
                    filtered.append(sym_data)
            else:
                if quote in self.quote_allowlist:
                    filtered.append(sym_data)

        return filtered

    def _apply_soft_liquidity_priors(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep rows unchanged; liquidity metrics remain context/prior fields only."""
        return symbols
    
    def _filter_exclusions(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Exclude stablecoins, wrapped tokens, leveraged tokens."""
        filtered = []
        
        for sym_data in symbols:
            base = sym_data.get('base', '')
            
            # Check if base matches any exclusion pattern
            is_excluded = False
            for pattern in self.exclusion_patterns:
                if pattern in base.upper():
                    is_excluded = True
                    break
            
            if not is_excluded:
                filtered.append(sym_data)
        
        return filtered

    def _apply_risk_flags(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered = []
        for sym_data in symbols:
            symbol = str(sym_data.get('symbol', '')).upper()
            base = str(sym_data.get('base', '')).upper()

            hard_reasons = []
            if symbol in self.denylist_symbols or base in self.denylist_bases:
                hard_reasons.append('denylist')
            if symbol in self.major_unlock_symbols or base in self.major_unlock_bases:
                hard_reasons.append('major_unlock_within_14d')

            if hard_reasons:
                continue

            row = dict(sym_data)
            row['risk_flags'] = []
            row['soft_penalties'] = {}

            if symbol in self.minor_unlock_symbols or base in self.minor_unlock_bases:
                row['risk_flags'].append('minor_unlock_within_14d')
                row['soft_penalties']['minor_unlock_within_14d'] = self.minor_unlock_penalty_factor

            filtered.append(row)

        return filtered
    
    def get_filter_stats(self, symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about what would be filtered.
        
        Args:
            symbols: Input symbols
        
        Returns:
            Dict with filter stats
        """
        total = len(symbols)
        
        # Count what passes each filter
        mcap_pass = len(self._filter_pre_shortlist_market_cap_floor(symbols))
        quote_pass = len(self._filter_quote_assets(symbols))
        liquidity_pass = len(self._apply_soft_liquidity_priors(symbols))
        exclusion_pass = len(self._filter_exclusions(symbols))
        
        # Full pipeline
        final_pass = len(self.apply_all(symbols))
        
        return {
            'total_input': total,
            'mcap_pass': mcap_pass,
            'mcap_fail': total - mcap_pass,
            'quote_pass': quote_pass,
            'quote_fail': total - quote_pass,
            'liquidity_pass': liquidity_pass,
            'liquidity_fail': total - liquidity_pass,
            'exclusion_pass': exclusion_pass,
            'exclusion_fail': total - exclusion_pass,
            'final_pass': final_pass,
            'final_fail': total - final_pass,
            'filter_rate': f"{final_pass/total*100:.1f}%" if total > 0 else "0%"
        }

```

### `scanner/pipeline/global_ranking.py`

**SHA256:** `d6f7546c8cf7c6899a4decb229c45a1a36beeb9d5766aeeba44ed47163552b6c`

```python
"""Global ranking aggregation across setup-specific rankings."""

from __future__ import annotations

from typing import Any, Dict, List


def _config_get(root: Dict[str, Any], path: List[str], default: Any) -> Any:
    cur: Any = root
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def compute_global_top20(
    reversal_results: List[Dict[str, Any]],
    breakout_results: List[Dict[str, Any]],
    pullback_results: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build unique global top-20 list from setup results using weighted setup score."""
    root = config.raw if hasattr(config, "raw") else config

    setup_map = {
        "breakout": breakout_results,
        "pullback": pullback_results,
        "reversal": reversal_results,
    }

    by_symbol: Dict[str, Dict[str, Any]] = {}

    for setup_type, entries in setup_map.items():
        for entry in entries:
            symbol = entry.get("symbol")
            if not symbol:
                continue
            setup_score = float(entry.get("final_score", entry.get("score", 0.0)))
            weighted = setup_score

            if symbol not in by_symbol:
                agg = dict(entry)
                agg["setup_score"] = setup_score
                agg["best_setup_type"] = setup_type
                agg["best_setup_score"] = setup_score
                agg["setup_weight"] = 1.0
                agg["global_score"] = round(weighted, 6)
                agg["confluence"] = 1
                agg["valid_setups"] = [setup_type]
                by_symbol[symbol] = agg
                continue

            prev = by_symbol[symbol]
            prev_setups = set(prev.get("valid_setups", []))
            prev_setups.add(setup_type)
            prev["valid_setups"] = sorted(prev_setups)
            prev["confluence"] = len(prev_setups)

            prev_weighted = float(prev.get("global_score", 0.0))
            prev_setup_id = str(prev.get("setup_id", ""))
            cur_setup_id = str(entry.get("setup_id", ""))
            prefer_retest = weighted == prev_weighted and cur_setup_id.endswith("retest_1_5d") and not prev_setup_id.endswith("retest_1_5d")

            if weighted > prev_weighted or prefer_retest:
                prev.update(entry)
                prev["setup_score"] = setup_score
                prev["best_setup_type"] = setup_type
                prev["best_setup_score"] = setup_score
                prev["setup_weight"] = 1.0
                prev["global_score"] = round(weighted, 6)
                prev["confluence"] = len(prev_setups)
                prev["valid_setups"] = sorted(prev_setups)

    ranked = sorted(
        by_symbol.values(),
        key=lambda x: (
            -float(x.get("global_score", 0.0)),
            float("inf") if x.get("slippage_bps") is None else float(x.get("slippage_bps")),
            -float(x.get("proxy_liquidity_score", 0.0) or 0.0),
            str(x.get("symbol", "")),
        ),
    )

    top20 = ranked[:20]
    for i, e in enumerate(top20, start=1):
        e["rank"] = i
    return top20

```

### `scanner/pipeline/liquidity.py`

**SHA256:** `d9ac0a9851119ca0fe9c12f4a835515f5f6e7d636b6dd6cadb4c4711a44feca6`

```python
"""Liquidity stage utilities (Top-K orderbook budget + slippage metrics)."""

from __future__ import annotations

import logging

from typing import Any, Dict, List, Set, Tuple


logger = logging.getLogger(__name__)


def _root_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return config.raw if hasattr(config, "raw") else config


def get_orderbook_top_k(config: Dict[str, Any]) -> int:
    root = _root_config(config)
    return int(root.get("liquidity", {}).get("orderbook_top_k", 200))


def get_slippage_notional_usdt(config: Dict[str, Any]) -> float:
    root = _root_config(config)
    return float(root.get("liquidity", {}).get("slippage_notional_usdt", 20_000.0))


def get_grade_thresholds_bps(config: Dict[str, Any]) -> Tuple[float, float, float]:
    root = _root_config(config)
    cfg = root.get("liquidity", {}).get("grade_thresholds_bps", {})
    a_max = float(cfg.get("a_max", 20.0))
    b_max = float(cfg.get("b_max", 50.0))
    c_max = float(cfg.get("c_max", 100.0))
    return a_max, b_max, c_max


def _read_tradeability_thresholds(config: Dict[str, Any]) -> Tuple[float, float, float]:
    if hasattr(config, "tradeability_class_thresholds"):
        cfg = config.tradeability_class_thresholds
    else:
        root = _root_config(config)
        cfg = root.get("tradeability", {}).get(
            "class_thresholds",
            {
                "direct_ok_max_slippage_bps": 50,
                "tranche_ok_max_slippage_bps": 100,
                "marginal_max_slippage_bps": 150,
            },
        )

    if not isinstance(cfg, dict):
        raise ValueError("tradeability.class_thresholds must be an object")

    required = [
        "direct_ok_max_slippage_bps",
        "tranche_ok_max_slippage_bps",
        "marginal_max_slippage_bps",
    ]
    missing = [key for key in required if key not in cfg]
    if missing:
        raise ValueError(f"tradeability.class_thresholds missing keys: {missing}")

    direct_max = float(cfg[required[0]])
    tranche_max = float(cfg[required[1]])
    marginal_max = float(cfg[required[2]])
    if direct_max < 0 or tranche_max < 0 or marginal_max < 0:
        raise ValueError("tradeability.class_thresholds values must be >= 0")
    if not (direct_max <= tranche_max <= marginal_max):
        raise ValueError(
            "tradeability.class_thresholds must satisfy direct_ok_max_slippage_bps <= tranche_ok_max_slippage_bps <= marginal_max_slippage_bps"
        )
    return direct_max, tranche_max, marginal_max


def _tradeability_params(config: Dict[str, Any]) -> Dict[str, float]:
    direct_max, tranche_max, marginal_max = _read_tradeability_thresholds(config)
    root = _root_config(config)
    tradeability_cfg = root.get("tradeability", {})
    return {
        "notional_total_usdt": float(
            config.tradeability_notional_total_usdt if hasattr(config, "tradeability_notional_total_usdt") else tradeability_cfg.get("notional_total_usdt", 20_000)
        ),
        "notional_chunk_usdt": float(
            config.tradeability_notional_chunk_usdt if hasattr(config, "tradeability_notional_chunk_usdt") else tradeability_cfg.get("notional_chunk_usdt", 5_000)
        ),
        "max_tranches": int(config.tradeability_max_tranches if hasattr(config, "tradeability_max_tranches") else tradeability_cfg.get("max_tranches", 4)),
        "band_pct": float(config.tradeability_band_pct if hasattr(config, "tradeability_band_pct") else tradeability_cfg.get("band_pct", 1.0)),
        "max_spread_pct": float(config.tradeability_max_spread_pct if hasattr(config, "tradeability_max_spread_pct") else tradeability_cfg.get("max_spread_pct", 0.15)),
        "min_depth_1pct_usd": float(
            config.tradeability_min_depth_1pct_usd if hasattr(config, "tradeability_min_depth_1pct_usd") else tradeability_cfg.get("min_depth_1pct_usd", 200_000)
        ),
        "direct_ok_max_slippage_bps": direct_max,
        "tranche_ok_max_slippage_bps": tranche_max,
        "marginal_max_slippage_bps": marginal_max,
    }


def select_top_k_for_orderbook(candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """Select top-k candidates by proxy_liquidity_score then quote_volume_24h."""
    ranked = sorted(
        candidates,
        key=lambda x: (float(x.get("proxy_liquidity_score", 0.0)), float(x.get("quote_volume_24h", 0.0))),
        reverse=True,
    )
    return ranked[: max(0, top_k)]


def fetch_orderbooks_for_top_k(
    mexc_client: Any,
    candidates: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[Dict[str, Any], Set[str]]:
    """Fetch Top-K orderbooks and return (validated_payloads, selected_symbols)."""
    top_k = get_orderbook_top_k(config)
    selected = select_top_k_for_orderbook(candidates, top_k)

    payload: Dict[str, Any] = {}
    selected_symbols: Set[str] = set()

    for row in selected:
        symbol = row.get("symbol")
        if not symbol:
            continue
        selected_symbols.add(symbol)
        try:
            fetched = mexc_client.get_orderbook(symbol)
            if not isinstance(fetched, dict):
                logger.debug("Malformed orderbook payload ignored for %s: non-dict", symbol)
                continue
            bids = fetched.get("bids")
            asks = fetched.get("asks")
            if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
                logger.debug("Malformed orderbook payload ignored for %s: missing/empty bids or asks", symbol)
                continue
            payload[symbol] = fetched
        except Exception as exc:
            logger.warning("Orderbook fetch failed for %s: %s", symbol, exc, exc_info=True)
    return payload, selected_symbols


def _to_levels(levels: Any) -> List[Tuple[float, float]]:
    out: List[Tuple[float, float]] = []
    if not isinstance(levels, list):
        return out
    for row in levels:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        try:
            p = float(row[0])
            q = float(row[1])
        except (TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            out.append((p, q))
    return out


def _compute_buy_vwap(asks: List[Tuple[float, float]], notional_usdt: float) -> Tuple[float, bool]:
    remaining = float(notional_usdt)
    if remaining <= 0:
        return 0.0, False

    spent = 0.0
    qty = 0.0
    for price, size in asks:
        level_quote = price * size
        take_quote = min(level_quote, remaining)
        take_qty = take_quote / price
        spent += take_quote
        qty += take_qty
        remaining -= take_quote
        if remaining <= 1e-9:
            break

    if qty <= 0:
        return 0.0, True
    return spent / qty, remaining > 1e-9


def _compute_slippage_bps(orderbook: Dict[str, Any], notional_usdt: float) -> float | None:
    bids = _to_levels(orderbook.get("bids"))
    asks = _to_levels(orderbook.get("asks"))
    if not bids or not asks:
        return None
    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid = (best_bid + best_ask) / 2.0
    if mid <= 0:
        return None
    vwap_ask, insufficient = _compute_buy_vwap(asks, notional_usdt)
    if insufficient or vwap_ask <= 0:
        return None
    return round(((vwap_ask - mid) / mid) * 10_000.0, 6)


def _is_orderbook_stale(orderbook: Dict[str, Any]) -> bool:
    return bool(orderbook.get("stale") or orderbook.get("is_stale"))


def _unknown_tradeability(reason: str) -> Dict[str, Any]:
    return {
        "slippage_bps_5k": None,
        "slippage_bps_20k": None,
        "tradeable_5k": None,
        "tradeable_20k": None,
        "tradeable_via_tranches": None,
        "tradeability_class": "UNKNOWN",
        "execution_mode": "none",
        "tradeability_reason_keys": [reason],
    }


def compute_tradeability_metrics(orderbook: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    params = _tradeability_params(config)
    if _is_orderbook_stale(orderbook):
        return _unknown_tradeability("orderbook_data_stale")

    band_metrics = compute_orderbook_metrics(orderbook, [float(params["band_pct"])])
    band_label = _band_label(float(params["band_pct"]))
    depth_bid = band_metrics.get(f"depth_bid_{band_label}pct_usd")
    depth_ask = band_metrics.get(f"depth_ask_{band_label}pct_usd")
    spread_pct = band_metrics.get("spread_pct")

    slippage_5k = _compute_slippage_bps(orderbook, float(params["notional_chunk_usdt"]))
    slippage_20k = _compute_slippage_bps(orderbook, float(params["notional_total_usdt"]))

    spread_ok = spread_pct is not None and float(spread_pct) <= float(params["max_spread_pct"])
    depth_ok = (
        depth_bid is not None
        and depth_ask is not None
        and float(depth_bid) >= float(params["min_depth_1pct_usd"])
        and float(depth_ask) >= float(params["min_depth_1pct_usd"])
    )

    tradeable_20k = (
        slippage_20k is not None and float(slippage_20k) <= float(params["direct_ok_max_slippage_bps"]) and spread_ok and depth_ok
    )
    tradeable_5k = (
        slippage_5k is not None and float(slippage_5k) <= float(params["tranche_ok_max_slippage_bps"]) and spread_ok and depth_ok
    )
    tradeable_via_tranches = tradeable_5k and (float(params["notional_chunk_usdt"]) * int(params["max_tranches"]) >= float(params["notional_total_usdt"]))

    reasons: Set[str] = set()
    if not spread_ok:
        reasons.add("spread_too_wide")
    if not depth_ok:
        reasons.add("depth_1pct_insufficient")
    if slippage_20k is None or float(slippage_20k) > float(params["direct_ok_max_slippage_bps"]):
        reasons.add("slippage_20k_too_high")
    if slippage_5k is None or float(slippage_5k) > float(params["tranche_ok_max_slippage_bps"]):
        reasons.add("slippage_5k_too_high")
    if not tradeable_via_tranches:
        reasons.add("tranche_execution_not_feasible")

    if tradeable_20k:
        tradeability_class = "DIRECT_OK"
        execution_mode = "direct"
        reasons = set()
    elif tradeable_via_tranches:
        tradeability_class = "TRANCHE_OK"
        execution_mode = "tranches"
        reasons = set()
    else:
        within_marginal = (slippage_20k is not None and float(slippage_20k) <= float(params["marginal_max_slippage_bps"])) or (
            slippage_5k is not None and float(slippage_5k) <= float(params["marginal_max_slippage_bps"])
        )
        spread_borderline = spread_pct is not None and float(spread_pct) <= (float(params["max_spread_pct"]) * 1.25)
        depth_borderline = (
            depth_bid is not None
            and depth_ask is not None
            and float(depth_bid) >= float(params["min_depth_1pct_usd"]) * 0.8
            and float(depth_ask) >= float(params["min_depth_1pct_usd"]) * 0.8
        )
        tradeability_class = "MARGINAL" if (within_marginal or spread_borderline or depth_borderline) else "FAIL"
        execution_mode = "none"

    return {
        "slippage_bps_5k": slippage_5k,
        "slippage_bps_20k": slippage_20k,
        "tradeable_5k": tradeable_5k,
        "tradeable_20k": tradeable_20k,
        "tradeable_via_tranches": tradeable_via_tranches,
        "tradeability_class": tradeability_class,
        "execution_mode": execution_mode,
        "tradeability_reason_keys": sorted(reasons),
    }


def compute_orderbook_liquidity_metrics(orderbook: Dict[str, Any], notional_usdt: float, thresholds_bps: Tuple[float, float, float]) -> Dict[str, Any]:
    """Compute spread/slippage/grade from an orderbook snapshot."""
    bids = _to_levels(orderbook.get("bids"))
    asks = _to_levels(orderbook.get("asks"))

    if not bids or not asks:
        return {
            "spread_bps": None,
            "slippage_bps": None,
            "liquidity_grade": "D",
            "liquidity_insufficient": True,
        }

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid = (best_bid + best_ask) / 2.0
    if mid <= 0:
        return {
            "spread_bps": None,
            "slippage_bps": None,
            "liquidity_grade": "D",
            "liquidity_insufficient": True,
        }

    spread_bps = ((best_ask - best_bid) / mid) * 10_000.0
    vwap_ask, insufficient = _compute_buy_vwap(asks, float(notional_usdt))

    if insufficient or vwap_ask <= 0:
        return {
            "spread_bps": round(spread_bps, 6),
            "slippage_bps": None,
            "liquidity_grade": "D",
            "liquidity_insufficient": True,
        }

    slippage_bps = ((vwap_ask - mid) / mid) * 10_000.0

    a_max, b_max, c_max = thresholds_bps
    if slippage_bps <= a_max:
        grade = "A"
    elif slippage_bps <= b_max:
        grade = "B"
    elif slippage_bps <= c_max:
        grade = "C"
    else:
        grade = "D"

    return {
        "spread_bps": round(spread_bps, 6),
        "slippage_bps": round(slippage_bps, 6),
        "liquidity_grade": grade,
        "liquidity_insufficient": False,
    }


def _band_label(band: float) -> str:
    bf = float(band)
    if bf.is_integer():
        return str(int(bf))
    return str(bf).replace(".", "_")


def _empty_orderbook_metrics(bands_pct: List[float]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"spread_pct": None, "orderbook_ok": False}
    for band in bands_pct:
        label = _band_label(band)
        out[f"depth_bid_{label}pct_usd"] = None
        out[f"depth_ask_{label}pct_usd"] = None
    return out


def compute_orderbook_metrics(orderbook: Dict[str, Any], bands_pct: List[float]) -> Dict[str, Any]:
    """Compute deterministic spread/depth metrics for execution gating."""
    metrics = _empty_orderbook_metrics(bands_pct)
    bids = _to_levels(orderbook.get("bids"))
    asks = _to_levels(orderbook.get("asks"))
    if not bids or not asks:
        return metrics

    best_bid = max(p for p, _ in bids)
    best_ask = min(p for p, _ in asks)
    if best_bid <= 0 or best_ask <= 0:
        return metrics

    mid = (best_bid + best_ask) / 2.0
    if mid <= 0:
        return metrics

    metrics["spread_pct"] = ((best_ask - best_bid) / mid) * 100.0
    for band in bands_pct:
        band_f = float(band)
        label = _band_label(band_f)
        bid_cutoff = mid * (1.0 - band_f / 100.0)
        ask_cutoff = mid * (1.0 + band_f / 100.0)

        bid_depth = sum(price * qty for price, qty in bids if price >= bid_cutoff)
        ask_depth = sum(price * qty for price, qty in asks if price <= ask_cutoff)
        metrics[f"depth_bid_{label}pct_usd"] = bid_depth
        metrics[f"depth_ask_{label}pct_usd"] = ask_depth

    metrics["orderbook_ok"] = True
    return metrics


def apply_liquidity_metrics_to_shortlist(
    shortlist: List[Dict[str, Any]],
    orderbooks: Dict[str, Any],
    config: Dict[str, Any],
    selected_symbols: Set[str] | None = None,
) -> List[Dict[str, Any]]:
    """Attach liquidity fields for fetched symbols and leave non-fetched symbols untouched."""
    notional = get_slippage_notional_usdt(config)
    thresholds = get_grade_thresholds_bps(config)

    root = _root_config(config)
    gate_cfg = root.get("execution_gates", {}).get("mexc_orderbook", {})
    bands_cfg = gate_cfg.get("bands_pct", [0.5, 1.0])
    bands_pct = [float(v) for v in bands_cfg]

    out: List[Dict[str, Any]] = []
    for row in shortlist:
        symbol = row.get("symbol")
        r = dict(row)
        orderbook = orderbooks.get(symbol)
        if isinstance(orderbook, dict):
            metrics = compute_orderbook_liquidity_metrics(orderbook, notional, thresholds)
            r.update(metrics)
            r.update(compute_orderbook_metrics(orderbook, bands_pct))
            r.update(compute_tradeability_metrics(orderbook, config))
        elif selected_symbols is not None and symbol in selected_symbols:
            r.update(
                {
                    "spread_bps": None,
                    "slippage_bps": None,
                    "liquidity_grade": "D",
                    "liquidity_insufficient": True,
                }
            )
            r.update(_empty_orderbook_metrics(bands_pct))
            r.update(_unknown_tradeability("orderbook_data_missing"))
        else:
            r.update(
                {
                    "spread_bps": None,
                    "slippage_bps": None,
                    "liquidity_grade": None,
                    "liquidity_insufficient": None,
                }
            )
            metrics = _empty_orderbook_metrics(bands_pct)
            metrics["orderbook_ok"] = None
            r.update(metrics)
            r.update(_unknown_tradeability("orderbook_not_in_budget"))
        out.append(r)
    return out

```

### `scanner/pipeline/excel_output.py`

**SHA256:** `846e3eb752351b98beca26144324dbe4590a6f30aa262461350107eae9669118`

```python
"""
Excel Output Generation
=======================

Generates Excel workbooks from canonical trade_candidates SoT.
"""

import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelReportGenerator:
    """Generates Excel reports as pure SoT views."""

    REQUIRED_FIELDS = {"rank", "symbol", "decision", "decision_reasons"}
    ALLOWED_DECISIONS = {"ENTER", "WAIT", "NO_TRADE"}
    CANDIDATE_COLUMNS = [
        ("rank", "Rank"),
        ("symbol", "Symbol"),
        ("coin_name", "Name"),
        ("decision", "Decision"),
        ("decision_reasons", "Decision Reasons"),
        ("best_setup_type", "Best Setup"),
        ("setup_subtype", "Setup Subtype"),
        ("global_score", "Global Score"),
        ("setup_score", "Setup Score"),
        ("entry_ready", "Entry Ready"),
        ("entry_readiness_reasons", "Entry Readiness Reasons"),
        ("execution_mode", "Execution Mode"),
        ("tradeability_class", "Tradeability Class"),
        ("risk_acceptable", "Risk Acceptable"),
        ("entry_price_usdt", "Entry Price (USDT)"),
        ("stop_price_initial", "Stop Price Initial"),
        ("risk_pct_to_stop", "Risk % to Stop"),
        ("tp10_price", "TP10 Price"),
        ("tp20_price", "TP20 Price"),
        ("rr_to_tp10", "RR to TP10"),
        ("rr_to_tp20", "RR to TP20"),
        ("spread_pct", "Spread %"),
        ("depth_bid_1pct_usd", "Depth Bid 1.0% USD"),
        ("depth_ask_1pct_usd", "Depth Ask 1.0% USD"),
        ("slippage_bps_5k", "Slippage BPS 5k"),
        ("slippage_bps_20k", "Slippage BPS 20k"),
        ("market_cap_usd", "Market Cap USD"),
        ("btc_regime", "BTC Regime"),
        ("flags", "Flags"),
    ]

    def __init__(self, config: Dict[str, Any]):
        if hasattr(config, "raw"):
            output_config = config.raw.get("output", {})
        else:
            output_config = config.get("output", {})

        self.reports_dir = Path(output_config.get("reports_dir", "reports"))
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Excel Report Generator initialized: reports_dir=%s", self.reports_dir)

    def generate_excel_report(
        self,
        trade_candidates: List[Dict[str, Any]],
        run_date: str,
        run_manifest: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
        btc_regime: Dict[str, Any] | None = None,
    ) -> Path:
        """Generate workbook from canonical trade_candidates SoT."""
        logger.info("Generating Excel report for %s", run_date)

        validated = self._validate_trade_candidates(trade_candidates)
        enter_candidates = [row for row in validated if row.get("decision") == "ENTER"]
        wait_candidates = [row for row in validated if row.get("decision") == "WAIT"]

        wb = Workbook()
        wb.remove(wb.active)

        self._create_summary_sheet(
            wb,
            run_date=run_date,
            trade_candidates=validated,
            run_manifest=run_manifest or {},
            metadata=metadata,
            btc_regime=btc_regime,
        )
        self._create_trade_candidates_sheet(wb, "Trade Candidates", validated)
        self._create_trade_candidates_sheet(wb, "Enter Candidates", enter_candidates)
        self._create_trade_candidates_sheet(wb, "Wait Candidates", wait_candidates)

        excel_path = self.reports_dir / f"{run_date}.xlsx"
        wb.save(excel_path)
        logger.info("Excel report saved: %s", excel_path)
        return excel_path

    def _validate_trade_candidates(self, trade_candidates: Any) -> List[Dict[str, Any]]:
        if not isinstance(trade_candidates, list):
            raise ValueError("trade_candidates must be a list")

        validated: List[Dict[str, Any]] = []
        for idx, row in enumerate(trade_candidates):
            if not isinstance(row, dict):
                raise ValueError(f"trade_candidates[{idx}] must be an object")

            missing = [field for field in self.REQUIRED_FIELDS if field not in row]
            if missing:
                raise ValueError(f"trade_candidates[{idx}] missing required fields: {', '.join(missing)}")

            decision = row.get("decision")
            if decision not in self.ALLOWED_DECISIONS:
                raise ValueError(f"trade_candidates[{idx}].decision invalid: {decision}")

            reasons = row.get("decision_reasons")
            if reasons is not None and not isinstance(reasons, list):
                raise ValueError(f"trade_candidates[{idx}].decision_reasons must be list or null")

            validated.append(row)
        return validated

    def _create_summary_sheet(
        self,
        wb: Workbook,
        run_date: str,
        trade_candidates: List[Dict[str, Any]],
        run_manifest: Dict[str, Any],
        metadata: Dict[str, Any] | None,
        btc_regime: Dict[str, Any] | None,
    ) -> None:
        ws = wb.create_sheet("Summary", 0)

        btc_regime = btc_regime or {}
        checks = btc_regime.get("checks") or {}
        counts = {"ENTER": 0, "WAIT": 0, "NO_TRADE": 0}
        for row in trade_candidates:
            decision = row.get("decision")
            if decision in counts:
                counts[decision] += 1

        ws["A1"] = "BTC Regime"
        ws["A2"] = "State"
        ws["B2"] = btc_regime.get("state", "RISK_OFF")
        ws["A3"] = "Multiplier (Risk-On)"
        ws["B3"] = self._sanitize_float_or_none(btc_regime.get("multiplier_risk_on"), default=1.0)
        ws["A4"] = "Multiplier (Risk-Off)"
        ws["B4"] = self._sanitize_float_or_none(btc_regime.get("multiplier_risk_off"), default=0.85)
        ws["A5"] = "close>ema50"
        ws["B5"] = checks.get("close_gt_ema50")
        ws["A6"] = "ema20>ema50"
        ws["B6"] = checks.get("ema20_gt_ema50")

        ws["A8"] = "Metric"
        ws["B8"] = "Value"
        for cell in ["A8", "B8"]:
            ws[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            ws[cell].font = Font(bold=True, size=12, color="FFFFFF")
            ws[cell].alignment = Alignment(horizontal="center")

        row_idx = 9
        summary_rows = [
            ("Run Date", run_date),
            ("Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
            ("Trade Candidates", len(trade_candidates)),
            ("ENTER Candidates", counts["ENTER"]),
            ("WAIT Candidates", counts["WAIT"]),
            ("NO_TRADE Candidates", counts["NO_TRADE"]),
            ("run_id", run_manifest.get("run_id")),
            ("canonical_schema_version", run_manifest.get("canonical_schema_version")),
        ]

        if metadata:
            summary_rows.extend(
                [
                    ("Total Symbols Scanned", metadata.get("universe_size")),
                    ("Symbols Filtered (MidCaps)", metadata.get("filtered_size")),
                    ("Symbols in Shortlist", metadata.get("shortlist_size")),
                ]
            )

        for key, value in summary_rows:
            ws.cell(row=row_idx, column=1, value=key)
            ws.cell(row=row_idx, column=2, value=value)
            row_idx += 1

        ws.column_dimensions["A"].width = 32
        ws.column_dimensions["B"].width = 28

    def _create_trade_candidates_sheet(self, wb: Workbook, sheet_name: str, rows: List[Dict[str, Any]]) -> None:
        ws = wb.create_sheet(sheet_name)

        for col_idx, (_, header) in enumerate(self.CANDIDATE_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(bold=True, size=11, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center")

        for row_idx, row in enumerate(rows, start=2):
            for col_idx, (key, _) in enumerate(self.CANDIDATE_COLUMNS, start=1):
                ws.cell(row=row_idx, column=col_idx, value=self._to_excel_cell_value(row.get(key)))

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        for col_idx, (_, header) in enumerate(self.CANDIDATE_COLUMNS, start=1):
            col = get_column_letter(col_idx)
            ws.column_dimensions[col].width = max(12, min(len(header) + 4, 36))

    @classmethod
    def _to_excel_cell_value(cls, value: Any) -> Any:
        if isinstance(value, list):
            return " | ".join(str(item) for item in value)
        if isinstance(value, dict):
            return str(value)
        return cls._sanitize_float_if_needed(value)

    @staticmethod
    def _sanitize_float_if_needed(value: Any) -> Any:
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value

    @staticmethod
    def _sanitize_float_or_none(value: Any, default: float | None = None) -> float | None:
        if value is None:
            return default
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return default
        if math.isnan(numeric) or math.isinf(numeric):
            return default
        return numeric

```

### `scanner/pipeline/__init__.py`

**SHA256:** `dfa7c54697d78eb1ec0a16bc1a56f777ebf0044215ed7dd6d55f9bea6a2ad28f`

```python
"""
Pipeline Orchestration
======================

Orchestrates the full daily scanning pipeline.
"""

from __future__ import annotations
import logging
import time
from ..utils.time_utils import utc_now, timestamp_to_ms

from ..config import ScannerConfig
from ..clients.mexc_client import MEXCClient
from ..clients.marketcap_client import MarketCapClient
from ..clients.mapping import SymbolMapper
from .filters import UniverseFilters
from .shortlist import ShortlistSelector
from .ohlcv import OHLCVFetcher
from .features import FeatureEngine
from .scoring.reversal import score_reversals
from .scoring.breakout_trend_1_5d import score_breakout_trend_1_5d
from .scoring.pullback import score_pullbacks
from .output import ReportGenerator
from .global_ranking import compute_global_top20
from .liquidity import fetch_orderbooks_for_top_k, apply_liquidity_metrics_to_shortlist
from .snapshot import SnapshotManager
from .runtime_market_meta import RuntimeMarketMetaExporter
from .discovery import compute_discovery_fields
from .regime import compute_btc_regime
from .decision import apply_decision_layer

logger = logging.getLogger(__name__)


def _to_optional_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_cmc_global_volume_24h(mapping_result):
    if not mapping_result or not mapping_result.mapped:
        return None
    cmc_data = mapping_result.cmc_data or {}
    quote_usd = cmc_data.get('quote', {}).get('USD', {})
    return _to_optional_float(quote_usd.get('volume_24h'))


def _compute_turnover_24h(global_volume_24h_usd, market_cap):
    if global_volume_24h_usd is None or market_cap in (None, 0):
        return None
    return global_volume_24h_usd / market_cap


def _compute_mexc_share_24h(mexc_quote_volume_24h_usdt, global_volume_24h_usd):
    if mexc_quote_volume_24h_usdt is None or global_volume_24h_usd in (None, 0):
        return None
    return mexc_quote_volume_24h_usdt / global_volume_24h_usd


def _build_scoring_volume_maps(shortlist, root_config):
    scoring_cfg = root_config.get('scoring', {}) if isinstance(root_config, dict) else {}
    volume_source = str(scoring_cfg.get('volume_source', 'mexc'))

    volume_map = {}
    volume_source_map = {}
    for row in shortlist:
        symbol = row.get('symbol')
        if not symbol:
            continue

        mexc_volume = _to_optional_float(row.get('quote_volume_24h'))
        global_volume = _to_optional_float(row.get('global_volume_24h_usd'))

        selected_volume = mexc_volume
        selected_source = 'mexc'
        if volume_source == 'global_fallback_mexc' and global_volume is not None:
            selected_volume = global_volume
            selected_source = 'global'

        volume_map[symbol] = float(selected_volume or 0.0)
        volume_source_map[symbol] = selected_source

    return volume_map, volume_source_map




def _enrich_scored_entries_with_market_activity(entries, features):
    for entry in entries:
        symbol = entry.get('symbol')
        feature_row = features.get(symbol, {}) if symbol else {}
        entry['global_volume_24h_usd'] = feature_row.get('global_volume_24h_usd')
        entry['turnover_24h'] = feature_row.get('turnover_24h')
        entry['mexc_share_24h'] = feature_row.get('mexc_share_24h')
        if entry.get('spread_pct') is None:
            entry['spread_pct'] = feature_row.get('spread_pct')
        if entry.get('depth_bid_1pct_usd') is None:
            entry['depth_bid_1pct_usd'] = feature_row.get('depth_bid_1pct_usd')
        if entry.get('depth_ask_1pct_usd') is None:
            entry['depth_ask_1pct_usd'] = feature_row.get('depth_ask_1pct_usd')
        if entry.get('slippage_bps_5k') is None:
            entry['slippage_bps_5k'] = feature_row.get('slippage_bps_5k')
        if entry.get('slippage_bps_20k') is None:
            entry['slippage_bps_20k'] = feature_row.get('slippage_bps_20k')
        if entry.get('tradeability_class') is None:
            entry['tradeability_class'] = feature_row.get('tradeability_class')
        if entry.get('execution_mode') is None:
            entry['execution_mode'] = feature_row.get('execution_mode')
    return entries


def _apply_tradeability_gate(shortlist):
    allowed_classes = {"DIRECT_OK", "TRANCHE_OK", "MARGINAL"}
    allowed = []
    stopped = []

    for row in shortlist:
        entry = dict(row)
        tradeability_class = entry.get("tradeability_class")
        if tradeability_class in allowed_classes:
            allowed.append(entry)
            continue

        reason_keys = entry.get("tradeability_reason_keys")
        if isinstance(reason_keys, list) and reason_keys:
            normalized_reasons = [str(reason) for reason in reason_keys]
        elif tradeability_class == "UNKNOWN":
            normalized_reasons = ["tradeability_unknown"]
        elif tradeability_class == "FAIL":
            normalized_reasons = ["tradeability_failed"]
        else:
            normalized_reasons = ["tradeability_unknown"]

        entry["tradeability_reason_keys"] = normalized_reasons
        entry["tradeability_gate_stop"] = True
        entry["tradeability_gate_stop_reason_keys"] = normalized_reasons
        stopped.append(entry)

    return allowed, stopped

def run_pipeline(config: ScannerConfig) -> None:
    """
    Orchestrates the full daily pipeline:
    1. Fetch universe (MEXC Spot USDT)
    2. Fetch market cap listings
    3. Run mapping layer
    4. Apply hard filters (market cap, liquidity, exclusions)
    5. Run cheap pass (shortlist)
    6. Liquidity stage: orderbook fetch for Top-K only
    7. Fetch OHLCV for shortlist
    8. Compute features (1d + 4h)
    9. Enrich features with price, name, market cap, and volume
    10. Compute scores (breakout / pullback / reversal)
    11. Write reports (Markdown + JSON + Excel)
    12. Write snapshot for backtests
    """
    run_mode = config.run_mode
    pipeline_start_time = time.perf_counter()

    # As-Of Timestamp (einmal pro Run)
    asof_dt = utc_now()
    asof_ts_ms = timestamp_to_ms(asof_dt)
    asof_iso = asof_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Run-Date konsistent aus asof_dt
    run_date = asof_dt.strftime('%Y-%m-%d')
    
    use_cache = run_mode in ['fast', 'standard']
    
    logger.info("=" * 80)
    logger.info(f"PIPELINE STARTING - {run_date}")
    logger.info(f"Mode: {run_mode}")
    logger.info("=" * 80)
    
    # Initialize clients
    logger.info("\n[INIT] Initializing clients...")
    mexc = MEXCClient()
    cmc = MarketCapClient(api_key=config.cmc_api_key)
    logger.info("✓ Clients initialized")
    
    # Step 1: Fetch universe (MEXC Spot USDT)
    logger.info("\n[1/12] Fetching MEXC universe...")
    exchange_info_ts_utc = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    exchange_info = mexc.get_exchange_info(use_cache=use_cache)

    universe = []
    for symbol_info in exchange_info.get("symbols", []):
        if (
            symbol_info.get("quoteAsset") == "USDT"
            and symbol_info.get("isSpotTradingAllowed", False)
            and symbol_info.get("status") == "1"
        ):
            universe.append(symbol_info["symbol"])

    logger.info(f"✓ Universe: {len(universe)} USDT pairs")
    
    # Get 24h tickers
    logger.info("  Fetching 24h tickers...")
    tickers_24h_ts_utc = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    tickers = mexc.get_24h_tickers(use_cache=use_cache)
    ticker_map = {t['symbol']: t for t in tickers}
    logger.info(f"  ✓ Tickers: {len(ticker_map)} symbols")
    
    # Step 2 & 3: Fetch market cap + Run mapping layer
    logger.info("\n[2-3/12] Fetching market cap & mapping...")
    cmc_listings_ts_utc = utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    cmc_listings = cmc.get_listings(use_cache=use_cache)
    cmc_symbol_map = cmc.build_symbol_map(cmc_listings)
    logger.info(f"  ✓ CMC: {len(cmc_symbol_map)} symbols")
    
    mapper = SymbolMapper()
    mapping_results = mapper.map_universe(universe, cmc_symbol_map)
    logger.info(f"✓ Mapped: {mapper.stats['mapped']}/{mapper.stats['total']} "
               f"({mapper.stats['mapped']/mapper.stats['total']*100:.1f}%)")
    
    # Prepare data for filters
    symbols_with_data = []
    for symbol in universe:
        result = mapping_results.get(symbol)
        if not result or not result.mapped:
            continue
        
        ticker = ticker_map.get(symbol, {})
        quote_volume_24h = _to_optional_float(ticker.get('quoteVolume'))
        market_cap = _to_optional_float(result._get_market_cap())
        global_volume_24h_usd = _extract_cmc_global_volume_24h(result)

        symbols_with_data.append({
            'symbol': symbol,
            'base': symbol.replace('USDT', ''),
            'quote_volume_24h': quote_volume_24h,
            'market_cap': market_cap,
            'global_volume_24h_usd': global_volume_24h_usd,
            'turnover_24h': _compute_turnover_24h(global_volume_24h_usd, market_cap),
            'mexc_share_24h': _compute_mexc_share_24h(quote_volume_24h, global_volume_24h_usd),
        })
    
    # Step 4: Apply hard filters
    logger.info("\n[4/12] Applying universe filters...")
    filters = UniverseFilters(config.raw)
    filtered = filters.apply_all(symbols_with_data)
    logger.info(f"✓ Filtered: {len(filtered)} symbols")
    
    # Step 5: Run cheap pass (shortlist)
    logger.info("\n[5/12] Creating shortlist...")
    selector = ShortlistSelector(config.raw)
    shortlist = selector.select(filtered)
    logger.info(f"✓ Shortlist: {len(shortlist)} symbols")
    
    # Step 6: Liquidity Stage (Top-K orderbook budget)
    logger.info("\n[6/12] Liquidity stage: fetching orderbook for Top-K only...")
    orderbooks, selected_symbols = fetch_orderbooks_for_top_k(mexc, shortlist, config.raw)
    logger.info(f"✓ Orderbooks fetched: {len(orderbooks)} (Top-K budget)")
    shortlist = apply_liquidity_metrics_to_shortlist(shortlist, orderbooks, config.raw, selected_symbols=selected_symbols)

    logger.info("  Applying tradeability gate before OHLCV...")
    shortlist, tradeability_stopped = _apply_tradeability_gate(shortlist)
    logger.info(
        "  ✓ Tradeability gate passed=%s stopped=%s",
        len(shortlist),
        len(tradeability_stopped),
    )
    if tradeability_stopped:
        stop_reasons = {}
        for stopped_entry in tradeability_stopped:
            for reason in stopped_entry.get("tradeability_gate_stop_reason_keys", []):
                stop_reasons[reason] = stop_reasons.get(reason, 0) + 1
        logger.info("  Tradeability stop reasons: %s", stop_reasons)

    # Step 7: Fetch OHLCV for shortlist
    logger.info("\n[7/12] Fetching OHLCV data...")
    ohlcv_fetcher = OHLCVFetcher(mexc, config.raw)
    ohlcv_data = ohlcv_fetcher.fetch_all(shortlist)
    logger.info(f"✓ OHLCV: {len(ohlcv_data)} symbols with complete data")
    
    # Step 8: Compute features (1d + 4h)
    logger.info("\n[8/12] Computing features...")
    feature_engine = FeatureEngine(config.raw)
    features = feature_engine.compute_all(ohlcv_data, asof_ts_ms=asof_ts_ms)
    logger.info(f"✓ Features: {len(features)} symbols")

    logger.info("  Computing BTC regime...")
    btc_regime = compute_btc_regime(
        mexc_client=mexc,
        feature_engine=feature_engine,
        lookback_1d=ohlcv_fetcher.lookback.get("1d", 120),
        asof_ts_ms=asof_ts_ms,
    )
    logger.info("  ✓ BTC regime: %s", btc_regime.get("state"))

    # Step 9: Enrich features with price, coin name, market cap, and volume
    logger.info("\n[9/12] Enriching features with price, name, market cap, and volume...")
    for symbol in features.keys():
        # Add current price from tickers
        ticker = ticker_map.get(symbol)
        if ticker:
            features[symbol]['price_usdt'] = float(ticker.get('lastPrice', 0))
        else:
            features[symbol]['price_usdt'] = None
    
        # Add coin name from CMC
        mapping = mapper.map_symbol(symbol, cmc_symbol_map)
        if mapping.mapped and mapping.cmc_data:
            features[symbol]['coin_name'] = mapping.cmc_data.get('name', 'Unknown')
            features[symbol]['cmc_date_added'] = mapping.cmc_data.get('date_added')
        else:
            features[symbol]['coin_name'] = 'Unknown'
            features[symbol]['cmc_date_added'] = None
        
        # Add market cap and volume from shortlist data
        shortlist_entry = next((s for s in shortlist if s['symbol'] == symbol), None)
        if shortlist_entry:
            features[symbol]['market_cap'] = shortlist_entry.get('market_cap')
            features[symbol]['quote_volume_24h'] = shortlist_entry.get('quote_volume_24h')
            features[symbol]['global_volume_24h_usd'] = shortlist_entry.get('global_volume_24h_usd')
            features[symbol]['turnover_24h'] = shortlist_entry.get('turnover_24h')
            features[symbol]['mexc_share_24h'] = shortlist_entry.get('mexc_share_24h')
            features[symbol]['proxy_liquidity_score'] = shortlist_entry.get('proxy_liquidity_score')
            features[symbol]['spread_bps'] = shortlist_entry.get('spread_bps')
            features[symbol]['slippage_bps'] = shortlist_entry.get('slippage_bps')
            features[symbol]['liquidity_grade'] = shortlist_entry.get('liquidity_grade')
            features[symbol]['liquidity_insufficient'] = shortlist_entry.get('liquidity_insufficient')
            features[symbol]['spread_pct'] = shortlist_entry.get('spread_pct')
            features[symbol]['depth_bid_0_5pct_usd'] = shortlist_entry.get('depth_bid_0_5pct_usd')
            features[symbol]['depth_ask_0_5pct_usd'] = shortlist_entry.get('depth_ask_0_5pct_usd')
            features[symbol]['depth_bid_1pct_usd'] = shortlist_entry.get('depth_bid_1pct_usd')
            features[symbol]['depth_ask_1pct_usd'] = shortlist_entry.get('depth_ask_1pct_usd')
            features[symbol]['orderbook_ok'] = shortlist_entry.get('orderbook_ok')
            features[symbol]['slippage_bps_5k'] = shortlist_entry.get('slippage_bps_5k')
            features[symbol]['slippage_bps_20k'] = shortlist_entry.get('slippage_bps_20k')
            features[symbol]['tradeability_class'] = shortlist_entry.get('tradeability_class')
            features[symbol]['execution_mode'] = shortlist_entry.get('execution_mode')
            features[symbol]['risk_flags'] = shortlist_entry.get('risk_flags', [])
            features[symbol]['soft_penalties'] = shortlist_entry.get('soft_penalties', {})
        else:
            features[symbol]['market_cap'] = None
            features[symbol]['quote_volume_24h'] = None
            features[symbol]['global_volume_24h_usd'] = None
            features[symbol]['turnover_24h'] = None
            features[symbol]['mexc_share_24h'] = None
            features[symbol]['proxy_liquidity_score'] = None
            features[symbol]['spread_bps'] = None
            features[symbol]['slippage_bps'] = None
            features[symbol]['liquidity_grade'] = None
            features[symbol]['liquidity_insufficient'] = None
            features[symbol]['spread_pct'] = None
            features[symbol]['depth_bid_0_5pct_usd'] = None
            features[symbol]['depth_ask_0_5pct_usd'] = None
            features[symbol]['depth_bid_1pct_usd'] = None
            features[symbol]['depth_ask_1pct_usd'] = None
            features[symbol]['orderbook_ok'] = None
            features[symbol]['slippage_bps_5k'] = None
            features[symbol]['slippage_bps_20k'] = None
            features[symbol]['tradeability_class'] = None
            features[symbol]['execution_mode'] = None
            features[symbol]['risk_flags'] = []
            features[symbol]['soft_penalties'] = {}

        symbol_ohlcv = ohlcv_data.get(symbol, {})
        first_seen_ts = None
        if isinstance(symbol_ohlcv, dict) and symbol_ohlcv.get('1d'):
            first = symbol_ohlcv['1d'][0]
            if isinstance(first, (list, tuple)) and first:
                try:
                    first_seen_ts = int(float(first[0]))
                except (TypeError, ValueError):
                    first_seen_ts = None

        discovery_cfg = config.raw.get('discovery', {}) if isinstance(config.raw, dict) else {}
        discovery_fields = compute_discovery_fields(
            asof_ts_ms=asof_ts_ms,
            date_added=features[symbol].get('cmc_date_added'),
            first_seen_ts=first_seen_ts,
            max_age_days=int(discovery_cfg.get('max_age_days', 180)),
        )
        features[symbol]['first_seen_ts'] = first_seen_ts
        features[symbol].update(discovery_fields)

    logger.info(f"✓ Enriched {len(features)} symbols with price, name, market cap, and volume")
    
    # Prepare volume map for scoring
    volume_map, volume_source_map = _build_scoring_volume_maps(shortlist, config.raw)
    
    # Step 10: Compute scores (breakout / pullback / reversal)
    logger.info("\n[10/12] Scoring setups...")
    
    logger.info("  Scoring Reversals...")
    reversal_results = score_reversals(features, volume_map, config.raw, volume_source_map=volume_source_map)
    logger.info(f"  ✓ Reversals: {len(reversal_results)} scored")
    
    logger.info("  Scoring Breakout Trend 1-5D...")
    breakout_results = score_breakout_trend_1_5d(features, volume_map, config.raw, btc_regime=btc_regime, volume_source_map=volume_source_map)
    logger.info(f"  ✓ Breakout Trend 1-5D rows: {len(breakout_results)} scored")
    
    logger.info("  Scoring Pullbacks...")
    pullback_results = score_pullbacks(features, volume_map, config.raw, volume_source_map=volume_source_map)
    logger.info(f"  ✓ Pullbacks: {len(pullback_results)} scored")

    global_top20 = compute_global_top20(
        reversal_results=reversal_results,
        breakout_results=breakout_results,
        pullback_results=pullback_results,
        config=config.raw,
    )

    reversal_results = _enrich_scored_entries_with_market_activity(reversal_results, features)
    breakout_results = _enrich_scored_entries_with_market_activity(breakout_results, features)
    pullback_results = _enrich_scored_entries_with_market_activity(pullback_results, features)
    global_top20 = _enrich_scored_entries_with_market_activity(global_top20, features)
    global_top20 = apply_decision_layer(global_top20, config.raw, btc_regime=btc_regime)

    logger.info(f"  ✓ Global Top20: {len(global_top20)} entries")

    # Step 11: Write reports (Markdown + JSON + Excel)
    logger.info("\n[11/12] Generating reports...")
    report_gen = ReportGenerator(config.raw)
    stage_counts = {
        'universe': len(universe),
        'filtered': len(filtered),
        'shortlist': len(shortlist),
        'orderbook_requested': len(selected_symbols),
        'orderbook_selected': len(selected_symbols),
        'tradeability_passed': len(shortlist),
        'tradeability_stopped': len(tradeability_stopped),
        'ohlcv_symbols': len(ohlcv_data),
        'features': len(features),
        'reversal_scored': len(reversal_results),
        'breakout_scored': len(breakout_results),
        'pullback_scored': len(pullback_results),
        'global_top20': len(global_top20),
    }
    warnings = []
    if tradeability_stopped:
        warnings.append('tradeability_gate_stopped_symbols')
    if len(orderbooks) < len(selected_symbols):
        warnings.append('orderbook_partial_fetch')

    report_paths = report_gen.save_reports(
        reversal_results,
        breakout_results,
        pullback_results,
        global_top20,
        run_date,
        metadata={
            'mode': run_mode,
            'run_id': f"{run_date}_{asof_ts_ms}",
            'timestamp_utc': asof_iso,
            'asof_ts_ms': asof_ts_ms,
            'asof_iso': asof_iso,
            'stage_counts': stage_counts,
            'warnings': warnings,
            'duration_seconds': time.perf_counter() - pipeline_start_time,
            'shortlist_size_used': config.budget_shortlist_size,
            'orderbook_top_k_used': config.budget_orderbook_top_k,
            'data_freshness': {
                'exchange_info_ts_utc': exchange_info_ts_utc,
                'tickers_24h_ts_utc': tickers_24h_ts_utc,
                'market_cap_listings_ts_utc': cmc_listings_ts_utc,
                'asof_iso_utc': asof_iso,
                'asof_ts_ms': asof_ts_ms,
            },
        },
        btc_regime=btc_regime,
    )
    logger.info(f"✓ Markdown: {report_paths['markdown']}")
    logger.info(f"✓ JSON: {report_paths['json']}")
    if 'excel' in report_paths:
        logger.info(f"✓ Excel: {report_paths['excel']}")
    
    # Step 12: Write snapshot for backtests
    logger.info("\n[12/12] Creating snapshot...")
    snapshot_mgr = SnapshotManager(config.raw)
    snapshot_path = snapshot_mgr.create_snapshot(
        run_date=run_date,
        universe=[{'symbol': s} for s in universe],
        filtered=filtered,
        shortlist=shortlist,
        features=features,
        reversal_scores=reversal_results,
        breakout_scores=breakout_results,
        pullback_scores=pullback_results,
        metadata={
            'mode': run_mode,
            'asof_ts_ms': asof_ts_ms,
            'asof_iso': asof_iso,
            'btc_regime': btc_regime,
        }
    )
    logger.info(f"✓ Snapshot: {snapshot_path}")

    runtime_meta_exporter = RuntimeMarketMetaExporter(config)
    runtime_meta_path = runtime_meta_exporter.export(
        run_date=run_date,
        asof_iso=asof_iso,
        run_id=str(asof_ts_ms),
        filtered_symbols=[entry['symbol'] for entry in filtered],
        mapping_results=mapping_results,
        exchange_info=exchange_info,
        ticker_map=ticker_map,
        features=features,
        ohlcv_data=ohlcv_data,
        exchange_info_ts_utc=exchange_info_ts_utc,
        tickers_24h_ts_utc=tickers_24h_ts_utc,
        listings_ts_utc=cmc_listings_ts_utc,
    )
    logger.info(f"✓ Runtime Market Meta: {runtime_meta_path}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Date: {run_date}")
    logger.info(f"Universe: {len(universe)} symbols")
    logger.info(f"Filtered: {len(filtered)} symbols")
    logger.info(f"Shortlist: {len(shortlist)} symbols")
    logger.info(f"Features: {len(features)} symbols")
    logger.info(f"\nScored:")
    logger.info(f"  Reversals: {len(reversal_results)}")
    logger.info(f"  Breakouts: {len(breakout_results)}")
    logger.info(f"  Pullbacks: {len(pullback_results)}")
    logger.info(f"\nOutputs:")
    logger.info(f"  Report: {report_paths['markdown']}")
    if 'excel' in report_paths:
        logger.info(f"  Excel: {report_paths['excel']}")
    logger.info(f"  Snapshot: {snapshot_path}")
    logger.info(f"  Runtime Market Meta: {runtime_meta_path}")
    logger.info("=" * 80)

```

### `scanner/pipeline/cross_section.py`

**SHA256:** `af16010718d0097f9f7adc448602dbc23c6008513524c5e31fa9d359c5ffc773`

```python
"""Cross-section helpers for deterministic percent-rank calculations."""

from __future__ import annotations

from typing import Dict, Iterable, List


def percent_rank_average_ties(values: Iterable[float]) -> List[float]:
    """Return percent-ranks in [0,100] with average-rank tie handling.

    Ranking is computed against the full provided population and is independent
    of input order.
    """
    value_list = [float(v) for v in values]
    n = len(value_list)
    if n == 0:
        return []
    if n == 1:
        return [100.0]

    sorted_values = sorted(value_list)
    positions_by_value: Dict[float, List[int]] = {}
    for idx, value in enumerate(sorted_values, start=1):
        positions_by_value.setdefault(value, []).append(idx)

    avg_rank_by_value = {
        value: (sum(positions) / len(positions))
        for value, positions in positions_by_value.items()
    }

    return [((avg_rank_by_value[value] - 1.0) / (n - 1.0)) * 100.0 for value in value_list]


```

### `scanner/pipeline/features.py`

**SHA256:** `e66c5c37f9923c3eac70e1ab6e5147af8cbfc9047fdfde408b6b47082e68b187`

```python
"""
Feature Engine
==============

Computes technical features from OHLCV data for both 1d and 4h timeframes.

Features computed:
- Price: Returns (1d/3d/7d), HH/HL detection
- Trend: EMA20/50, Price relative to EMAs
- Volatility: ATR%
- Volume: Spike detection, Volume SMA
- Structure: Breakout distance, Drawdown, Base detection
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngine:
    """Computes technical features from OHLCV data (v1.3 – critical findings remediation)."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("Feature Engine v1.3 initialized")

    def _config_get(self, path: List[str], default: Any) -> Any:
        """Read config path from either dict or ScannerConfig.raw."""
        root = self.config.raw if hasattr(self.config, "raw") else self.config
        current: Any = root
        for key in path:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default
        return current

    def _get_volume_period_for_timeframe(self, timeframe: str) -> int:
        periods_cfg = self._config_get(["features", "volume_sma_periods"], None)
        if isinstance(periods_cfg, dict):
            tf_period = periods_cfg.get(timeframe)
            if tf_period is not None:
                return int(tf_period)

        legacy_period = self._config_get(["features", "volume_sma_period"], None)
        if legacy_period is not None:
            return int(legacy_period)

        logger.warning("Using legacy default volume_sma_period=14; please define config.features.volume_sma_periods")
        return 14


    def _get_bollinger_params(self, timeframe: str) -> Tuple[int, float, int]:
        period = int(self._config_get(["features", "bollinger", "period"], 20))
        stddev = float(self._config_get(["features", "bollinger", "stddev"], 2.0))
        rank_lookback = int(
            self._config_get(["features", "bollinger", "rank_lookback_bars", timeframe], 120)
        )
        return period, stddev, rank_lookback

    def _get_atr_rank_lookback(self, timeframe: str) -> int:
        return int(self._config_get(["features", "atr_rank_lookback_bars", timeframe], 120))

    def _calc_percent_rank(self, values: np.ndarray, min_history: int = 2) -> Optional[float]:
        clean = np.array([float(v) for v in values if not np.isnan(v)], dtype=float)
        if len(clean) < min_history:
            return np.nan

        current = float(clean[-1])
        less = float(np.sum(clean < current))
        equal = float(np.sum(clean == current))
        avg_rank = less + ((equal + 1.0) / 2.0)
        denom = float(len(clean) - 1)
        if denom <= 0:
            return np.nan
        return float(((avg_rank - 1.0) / denom) * 100.0)

    def _calc_bollinger_width_series(self, closes: np.ndarray, period: int, stddev: float) -> np.ndarray:
        result = np.full(len(closes), np.nan, dtype=float)
        if period <= 1 or len(closes) < period:
            return result

        for i in range(period - 1, len(closes)):
            window = closes[i - period + 1 : i + 1]
            middle = float(np.nanmean(window))
            sigma = float(np.nanstd(window))
            if middle <= 0:
                continue
            upper = middle + (stddev * sigma)
            lower = middle - (stddev * sigma)
            result[i] = ((upper - lower) / middle) * 100.0

        return result

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------
    def compute_all(
        self,
        ohlcv_data: Dict[str, Dict[str, List[List]]],
        asof_ts_ms: Optional[int] = None
    ) -> Dict[str, Dict[str, Any]]:
        results = {}
        total = len(ohlcv_data)
        logger.info(f"Computing features for {total} symbols")

        for i, (symbol, tf_data) in enumerate(ohlcv_data.items(), 1):
            try:
                logger.debug(f"[{i}/{total}] Computing features for {symbol}")
                symbol_features = {}

                last_closed_idx_map: Dict[str, Optional[int]] = {}

                if "1d" in tf_data:
                    idx_1d = self._get_last_closed_idx(tf_data["1d"], asof_ts_ms)
                    last_closed_idx_map["1d"] = idx_1d
                    symbol_features["1d"] = self._compute_timeframe_features(
                        tf_data["1d"], "1d", symbol, last_closed_idx=idx_1d
                    )

                if "4h" in tf_data:
                    idx_4h = self._get_last_closed_idx(tf_data["4h"], asof_ts_ms)
                    last_closed_idx_map["4h"] = idx_4h
                    symbol_features["4h"] = self._compute_timeframe_features(
                        tf_data["4h"], "4h", symbol, last_closed_idx=idx_4h
                    )

                last_update = None
                if "1d" in tf_data:
                    idx = last_closed_idx_map.get("1d")
                    if isinstance(idx, int) and idx >= 0:
                        last_update = int(tf_data["1d"][idx][0])

                symbol_features["meta"] = {
                    "symbol": symbol,
                    "asof_ts_ms": asof_ts_ms,
                    "last_closed_idx": last_closed_idx_map,
                    "last_update": last_update,
                }
                results[symbol] = symbol_features
            except Exception as e:
                logger.error(f"Failed to compute features for {symbol}: {e}")
        logger.info(f"Features computed for {len(results)}/{total} symbols")
        return results

    # -------------------------------------------------------------------------
    # Helper Funktion
    # -------------------------------------------------------------------------
    def _get_last_closed_idx(self, klines: List[List], asof_ts_ms: Optional[int]) -> int:
        """
        Returns index of the last candle with closeTime <= asof_ts_ms.
        Expected kline format includes closeTime at index 6.
        """
        if not klines:
            return -1
        if asof_ts_ms is None:
            return len(klines) - 1

        for i in range(len(klines) - 1, -1, -1):
            k = klines[i]
            if len(k) < 7:
                continue
            try:
                close_time = int(float(k[6]))
            except (TypeError, ValueError):
                continue
            if close_time <= asof_ts_ms:
                return i

        return -1

    # -------------------------------------------------------------------------
    # Timeframe feature computation
    # -------------------------------------------------------------------------
    def _compute_timeframe_features(
        self,
        klines: List[List],
        timeframe: str,
        symbol: str,
        last_closed_idx: Optional[int] = None
    ) -> Dict[str, Any]:
        if not klines:
            return {}

        if last_closed_idx is None:
            last_closed_idx = len(klines) - 1

        if last_closed_idx < 0:
            logger.warning(f"[{symbol}] no closed candles found for timeframe={timeframe}")
            return {}

        klines = klines[: last_closed_idx + 1]
        closes = np.array([k[4] for k in klines], dtype=float)
        highs = np.array([k[2] for k in klines], dtype=float)
        lows = np.array([k[3] for k in klines], dtype=float)
        volumes = np.array([k[5] for k in klines], dtype=float)
        quote_volumes = np.array([k[7] if len(k) > 7 else np.nan for k in klines], dtype=float)

        if len(closes) < 50:
            logger.warning(f"[{symbol}] insufficient candles ({len(closes)}) for timeframe {timeframe}")
            return {}

        f = {}
        f["close"], f["high"], f["low"], f["volume"] = map(float, (closes[-1], highs[-1], lows[-1], volumes[-1]))

        # Returns & EMAs
        f["r_1"] = self._calc_return(symbol, closes, 1)
        f["r_3"] = self._calc_return(symbol, closes, 3)
        f["r_7"] = self._calc_return(symbol, closes, 7)
        f["ema_20"] = self._calc_ema(symbol, closes, 20)
        f["ema_50"] = self._calc_ema(symbol, closes, 50)

        f["dist_ema20_pct"] = ((closes[-1] / f["ema_20"]) - 1) * 100 if f.get("ema_20") else np.nan
        f["dist_ema50_pct"] = ((closes[-1] / f["ema_50"]) - 1) * 100 if f.get("ema_50") else np.nan

        f["atr_pct"] = self._calc_atr_pct(symbol, highs, lows, closes, 14)

        if timeframe == "1d":
            atr_rank_lookback = self._get_atr_rank_lookback("1d")
            atr_pct_series = self._calc_atr_pct_series(highs, lows, closes, 14)
            atr_rank_window = atr_pct_series[-atr_rank_lookback:]
            f[f"atr_pct_rank_{atr_rank_lookback}"] = self._calc_percent_rank(atr_rank_window)

        if timeframe == "4h":
            bb_period, bb_stddev, bb_rank_lookback = self._get_bollinger_params("4h")
            bb_width_series = self._calc_bollinger_width_series(closes, bb_period, bb_stddev)
            f["bb_width_pct"] = float(bb_width_series[-1]) if len(bb_width_series) else np.nan
            bb_rank_window = bb_width_series[-bb_rank_lookback:]
            f[f"bb_width_rank_{bb_rank_lookback}"] = self._calc_percent_rank(bb_rank_window)

        # Phase 1: timeframe-specific volume baseline period (include_current=False baseline)
        volume_period = self._get_volume_period_for_timeframe(timeframe)
        f["volume_sma"] = self._calc_sma(volumes, volume_period, include_current=False)
        f["volume_sma_period"] = int(volume_period)
        f["volume_spike"] = self._calc_volume_spike(symbol, volumes, f["volume_sma"])

        # Backward compatibility keys
        f["volume_sma_14"] = self._calc_sma(volumes, 14, include_current=False)

        # Quote volume features (with same period by timeframe + legacy key)
        f.update(self._calc_quote_volume_features(symbol, quote_volumes, volume_period))

        # Trend structure
        f["hh_20"] = bool(self._detect_higher_high(highs, 20))
        f["hl_20"] = bool(self._detect_higher_low(lows, 20))

        # Structural metrics
        f["breakout_dist_20"] = self._calc_breakout_distance(symbol, closes, highs, 20)
        f["breakout_dist_30"] = self._calc_breakout_distance(symbol, closes, highs, 30)
        drawdown_lookback_days = int(self._config_get(["features", "drawdown_lookback_days"], 365))
        drawdown_lookback_bars = self._lookback_days_to_bars(drawdown_lookback_days, timeframe)
        f["drawdown_from_ath"] = self._calc_drawdown(closes, drawdown_lookback_bars)

        # Phase 2: Base detection (1d only, config-driven)
        if timeframe == "1d":
            base_features = self._detect_base(symbol, closes, lows)
            f.update(base_features)
        else:
            f["base_score"] = np.nan

        return self._convert_to_native_types(f)

    # -------------------------------------------------------------------------
    # Calculation methods
    # -------------------------------------------------------------------------
    def _calc_return(self, symbol: str, closes: np.ndarray, periods: int) -> Optional[float]:
        if len(closes) <= periods:
            logger.warning(f"[{symbol}] insufficient candles for return({periods})")
            return np.nan
        try:
            return float(((closes[-1] / closes[-periods-1]) - 1) * 100)
        except Exception as e:
            logger.error(f"[{symbol}] return({periods}) error: {e}")
            return np.nan

    def _calc_ema(self, symbol: str, data: np.ndarray, period: int) -> Optional[float]:
        if len(data) < period:
            logger.warning(f"[{symbol}] insufficient data for EMA{period}")
            return np.nan

        alpha = 2 / (period + 1)
        ema = float(np.nanmean(data[:period]))
        for val in data[period:]:
            ema = alpha * val + (1 - alpha) * ema
        return float(ema)

    def _calc_sma(self, data: np.ndarray, period: int, include_current: bool = True) -> Optional[float]:
        if include_current:
            return float(np.nanmean(data[-period:])) if len(data) >= period else np.nan
        return float(np.nanmean(data[-period-1:-1])) if len(data) >= (period + 1) else np.nan

    def _calc_volume_spike(self, symbol: str, volumes: np.ndarray, sma: Optional[float]) -> float:
        if sma is None or np.isnan(sma) or sma == 0:
            logger.warning(f"[{symbol}] volume_spike fallback=1.0 (SMA invalid)")
            return 1.0
        return float(volumes[-1] / sma)

    def _calc_quote_volume_features(
        self,
        symbol: str,
        quote_volumes: np.ndarray,
        period: int,
    ) -> Dict[str, Optional[float]]:
        if len(quote_volumes) == 0 or np.all(np.isnan(quote_volumes)):
            return {
                "volume_quote": None,
                "volume_quote_sma": None,
                "volume_quote_spike": None,
                "volume_quote_sma_14": None,
            }

        volume_quote = float(quote_volumes[-1]) if not np.isnan(quote_volumes[-1]) else np.nan
        volume_quote_sma = self._calc_sma(quote_volumes, period, include_current=False)
        volume_quote_spike = self._calc_volume_spike(symbol, quote_volumes, volume_quote_sma)
        volume_quote_sma_14 = self._calc_sma(quote_volumes, 14, include_current=False)

        return {
            "volume_quote": volume_quote,
            "volume_quote_sma": volume_quote_sma,
            "volume_quote_spike": volume_quote_spike,
            "volume_quote_sma_14": volume_quote_sma_14,
        }

    def _calc_atr_pct(self, symbol: str, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> Optional[float]:
        if len(highs) < period + 1:
            logger.warning(f"[{symbol}] insufficient candles for ATR{period}")
            return np.nan

        tr = [
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            for i in range(1, len(highs))
        ]

        atr = float(np.nanmean(tr[:period]))
        for tr_val in tr[period:]:
            atr = ((atr * (period - 1)) + tr_val) / period

        if atr < 0:
            logger.warning(f"[{symbol}] ATR computed negative ({atr}); returning NaN")
            return np.nan

        return float((atr / closes[-1]) * 100) if closes[-1] > 0 else np.nan

    def _calc_atr_pct_series(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> np.ndarray:
        n = len(closes)
        atr_pct = np.full(n, np.nan, dtype=float)

        if len(highs) < period + 1:
            return atr_pct

        tr = np.full(n, np.nan, dtype=float)
        for i in range(1, n):
            hi = highs[i]
            lo = lows[i]
            prev_close = closes[i - 1]

            if np.isnan(hi) or np.isnan(lo) or np.isnan(prev_close):
                continue
            if hi < lo:
                continue

            c1 = hi - lo
            c2 = abs(hi - prev_close)
            c3 = abs(lo - prev_close)

            if np.isnan(c1) or np.isnan(c2) or np.isnan(c3):
                continue

            tr[i] = max(c1, c2, c3)

        atr = np.full(n, np.nan, dtype=float)
        seed_window = tr[1 : period + 1]
        if np.isnan(seed_window).all():
            atr[period] = np.nan
        else:
            atr[period] = float(np.nanmean(seed_window))
        if np.isnan(atr[period]) or atr[period] < 0:
            atr[period] = np.nan

        for i in range(period + 1, n):
            if np.isnan(atr[i - 1]):
                reseed_window = tr[max(1, i - period + 1) : i + 1]
                if reseed_window.size == 0 or np.isnan(reseed_window).all():
                    atr[i] = np.nan
                else:
                    atr[i] = float(np.nanmean(reseed_window))
            elif np.isnan(tr[i]):
                atr[i] = atr[i - 1]
            else:
                atr[i] = ((atr[i - 1] * (period - 1)) + tr[i]) / period

            if not np.isnan(atr[i]) and atr[i] < 0:
                atr[i] = np.nan

        for i in range(period, n):
            if np.isnan(atr[i]):
                atr_pct[i] = np.nan
                continue
            if closes[i] <= 0:
                atr_pct[i] = np.nan
                continue

            atr_pct[i] = (atr[i] / closes[i]) * 100.0
            if atr_pct[i] < 0:
                atr_pct[i] = np.nan

        return atr_pct

    def _calc_breakout_distance(self, symbol: str, closes: np.ndarray, highs: np.ndarray, lookback: int) -> Optional[float]:
        if len(highs) < lookback + 1:
            logger.warning(f"[{symbol}] insufficient candles for breakout_dist_{lookback}")
            return np.nan
        try:
            prior_high = np.nanmax(highs[-lookback-1:-1])
            return float(((closes[-1] / prior_high) - 1) * 100)
        except Exception as e:
            logger.error(f"[{symbol}] breakout_dist_{lookback} error: {e}")
            return np.nan


    def _timeframe_to_seconds(self, timeframe: str) -> Optional[int]:
        if not timeframe:
            return None

        tf = str(timeframe).strip().lower()
        units = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
        unit = tf[-1:]
        if unit not in units:
            return None

        try:
            magnitude = int(tf[:-1])
        except ValueError:
            return None

        if magnitude <= 0:
            return None

        return magnitude * units[unit]

    def _lookback_days_to_bars(self, lookback_days: int, timeframe: str) -> int:
        days = max(1, int(lookback_days))
        seconds_per_bar = self._timeframe_to_seconds(timeframe)
        if not seconds_per_bar:
            logger.warning(f"Unknown timeframe '{timeframe}' for drawdown lookback conversion; using days as bars fallback")
            return days

        bars = math.ceil((days * 86400) / seconds_per_bar)
        return max(1, int(bars))

    def _calc_drawdown(self, closes: np.ndarray, lookback_bars: int = 365) -> Optional[float]:
        if len(closes) == 0:
            return np.nan
        lookback = max(1, int(lookback_bars))
        window = closes[-lookback:]
        ath = np.nanmax(window)
        return float(((closes[-1] / ath) - 1) * 100)

    # -------------------------------------------------------------------------
    # Structure detection
    # -------------------------------------------------------------------------
    def _detect_higher_high(self, highs: np.ndarray, lookback: int = 20) -> bool:
        if len(highs) < lookback:
            return False
        return bool(np.nanmax(highs[-5:]) > np.nanmax(highs[-lookback:-5]))

    def _detect_higher_low(self, lows: np.ndarray, lookback: int = 20) -> bool:
        if len(lows) < lookback:
            return False
        return bool(np.nanmin(lows[-5:]) > np.nanmin(lows[-lookback:-5]))

    def _detect_base(self, symbol: str, closes: np.ndarray, lows: np.ndarray) -> Dict[str, Optional[float]]:
        lookback = int(self._config_get(["scoring", "reversal", "base_lookback_days"], 45))
        recent_days = int(self._config_get(["scoring", "reversal", "min_base_days_without_new_low"], 10))
        max_new_low_pct = float(
            self._config_get(["scoring", "reversal", "max_allowed_new_low_percent_vs_base_low"], 3.0)
        )

        if lookback <= 0 or recent_days <= 0 or recent_days >= lookback:
            logger.warning(
                f"[{symbol}] invalid base config (lookback={lookback}, recent_days={recent_days}); using defaults"
            )
            lookback = 45
            recent_days = 10
            max_new_low_pct = 3.0

        if len(closes) < lookback or len(lows) < lookback:
            logger.warning(f"[{symbol}] insufficient candles for base detection")
            return {
                "base_score": np.nan,
                "base_low": np.nan,
                "base_recent_low": np.nan,
                "base_range_pct": np.nan,
                "base_no_new_lows_pass": np.nan,
            }

        window_closes = closes[-lookback:]
        window_lows = lows[-lookback:]

        older_lows = window_lows[:-recent_days]
        recent_lows = window_lows[-recent_days:]
        recent_closes = window_closes[-recent_days:]

        base_low = float(np.nanmin(older_lows))
        recent_low = float(np.nanmin(recent_lows))

        tol = max_new_low_pct / 100.0
        no_new_lows_pass = bool(recent_low >= (base_low * (1 - tol)))

        recent_close_min = float(np.nanmin(recent_closes))
        recent_close_max = float(np.nanmax(recent_closes))
        if recent_close_min <= 0:
            range_pct = np.nan
        else:
            range_pct = float(((recent_close_max - recent_close_min) / recent_close_min) * 100.0)

        stability_score = 0.0 if np.isnan(range_pct) else max(0.0, 100.0 - range_pct)
        base_score = stability_score if no_new_lows_pass else 0.0

        return {
            "base_score": float(base_score),
            "base_low": base_low,
            "base_recent_low": recent_low,
            "base_range_pct": range_pct,
            "base_no_new_lows_pass": no_new_lows_pass,
        }

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    def _convert_to_native_types(self, features: Dict[str, Any]) -> Dict[str, Any]:
        converted = {}
        for k, v in features.items():
            if v is None or (isinstance(v, float) and np.isnan(v)):
                converted[k] = None
            elif isinstance(v, (np.floating, np.float64, np.float32)):
                converted[k] = float(v)
            elif isinstance(v, (np.integer, np.int64, np.int32)):
                converted[k] = int(v)
            elif isinstance(v, (np.bool_, bool)):
                converted[k] = bool(v)
            else:
                converted[k] = v
        return converted

```

### `scanner/pipeline/snapshot.py`

**SHA256:** `efe82d54e854edee4b267a8414f5399c3353895948a206ac051e72e65d879888`

```python
"""
Snapshot System
===============

Creates deterministic daily snapshots for backtesting and reproducibility.
Snapshots include all pipeline data at a specific point in time.
"""

import logging
from typing import Dict, Any, List
import re
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Manages daily pipeline snapshots."""
    
    @staticmethod
    def resolve_history_dir(config: Dict[str, Any]) -> Path:
        """Resolve the snapshot history directory from config with fallback semantics."""
        if hasattr(config, 'raw'):
            snapshot_config = config.raw.get('snapshots', {})
        else:
            snapshot_config = config.get('snapshots', {})

        history_dir = snapshot_config.get('history_dir')
        if history_dir:
            return Path(history_dir)

        snapshot_dir = snapshot_config.get('snapshot_dir')
        if snapshot_dir:
            base = Path(snapshot_dir)
            return base if base.name == 'history' else (base / 'history')

        return Path('snapshots/history')

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize snapshot manager.
        
        Args:
            config: Config dict with 'snapshots' section
        """
        self.snapshots_dir = self.resolve_history_dir(config)

        # Ensure directory exists
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Snapshot Manager initialized: {self.snapshots_dir}")
    
    def create_snapshot(
        self,
        run_date: str,
        universe: List[Dict[str, Any]],
        filtered: List[Dict[str, Any]],
        shortlist: List[Dict[str, Any]],
        features: Dict[str, Dict[str, Any]],
        reversal_scores: List[Dict[str, Any]],
        breakout_scores: List[Dict[str, Any]],
        pullback_scores: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> Path:
        """
        Create a complete snapshot of the pipeline run.
        
        Args:
            run_date: Date string (YYYY-MM-DD)
            universe: Full MEXC universe
            filtered: Post-filter universe
            shortlist: Shortlisted symbols
            features: Computed features
            reversal_scores: Reversal scoring results
            breakout_scores: Breakout scoring results
            pullback_scores: Pullback scoring results
            metadata: Optional metadata
        
        Returns:
            Path to saved snapshot file
        """
        logger.info(f"Creating snapshot for {run_date}")
        
        snapshot = {
            'meta': {
                'date': run_date,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'version': '1.1'
            },
            'pipeline': {
                'universe_count': len(universe),
                'filtered_count': len(filtered),
                'shortlist_count': len(shortlist),
                'features_count': len(features)
            },
            'data': {
                'universe': universe,
                'filtered': filtered,
                'shortlist': shortlist,
                'features': features
            },
            'scoring': {
                'reversals': reversal_scores,
                'breakouts': breakout_scores,
                'pullbacks': pullback_scores
            }
        }
        
        if metadata:
            snapshot['meta'].update(metadata)
            
        # Safety: ensure as-of exists (for reproducibility)
        if 'asof_ts_ms' not in snapshot['meta']:
            snapshot['meta']['asof_ts_ms'] = int(datetime.utcnow().timestamp() * 1000)

        if 'asof_iso' not in snapshot['meta']:
            snapshot['meta']['asof_iso'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
        # Save snapshot
        snapshot_path = self.snapshots_dir / f"{run_date}.json"
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        # Get file size
        size_mb = snapshot_path.stat().st_size / (1024 * 1024)
        
        logger.info(f"Snapshot saved: {snapshot_path} ({size_mb:.2f} MB)")
        
        return snapshot_path
    
    def load_snapshot(self, run_date: str) -> Dict[str, Any]:
        """
        Load a snapshot by date.
        
        Args:
            run_date: Date string (YYYY-MM-DD)
        
        Returns:
            Snapshot dict
        
        Raises:
            FileNotFoundError: If snapshot doesn't exist
        """
        snapshot_path = self.snapshots_dir / f"{run_date}.json"
        
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
        
        logger.info(f"Loading snapshot: {snapshot_path}")
        
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        return snapshot
    
    def list_snapshots(self) -> List[str]:
        """
        List all available snapshot dates.
        
        Returns:
            List of date strings (YYYY-MM-DD)
        """
        snapshots = []

        for path in self.snapshots_dir.glob("*.json"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
                continue

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(payload, dict):
                continue
            if not all(key in payload for key in ('meta', 'pipeline', 'data', 'scoring')):
                continue

            snapshots.append(path.stem)

        snapshots.sort()

        logger.info(f"Found {len(snapshots)} snapshots")

        return snapshots
    
    def get_snapshot_stats(self, run_date: str) -> Dict[str, Any]:
        """
        Get statistics about a snapshot without loading full data.
        
        Args:
            run_date: Date string
        
        Returns:
            Stats dict
        """
        snapshot = self.load_snapshot(run_date)
        
        return {
            'date': snapshot['meta']['date'],
            'created_at': snapshot['meta']['created_at'],
            'universe_count': snapshot['pipeline']['universe_count'],
            'filtered_count': snapshot['pipeline']['filtered_count'],
            'shortlist_count': snapshot['pipeline']['shortlist_count'],
            'features_count': snapshot['pipeline']['features_count'],
            'reversal_count': len(snapshot['scoring']['reversals']),
            'breakout_count': len(snapshot['scoring']['breakouts']),
            'pullback_count': len(snapshot['scoring']['pullbacks'])
        }

```

### `scanner/pipeline/discovery.py`

**SHA256:** `af2733523f90f9904ce93e2bcdf1796a878cca11e030cc8a1105ed59c02da41e`

```python
"""Discovery tag helpers (v2 T6.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _iso_to_ts_ms(value: str) -> Optional[int]:
    if not value:
        return None

    normalized = str(value).strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def compute_discovery_fields(
    *,
    asof_ts_ms: int,
    date_added: Optional[str],
    first_seen_ts: Optional[int],
    max_age_days: int = 180,
) -> Dict[str, Any]:
    """Compute deterministic discovery metadata for a symbol."""
    source_ts = _iso_to_ts_ms(date_added) if date_added else None
    source = "cmc_date_added" if source_ts is not None else None

    if source_ts is None and first_seen_ts is not None:
        try:
            source_ts = int(first_seen_ts)
            source = "first_seen_ts"
        except (TypeError, ValueError):
            source_ts = None
            source = None

    if source_ts is None:
        return {
            "discovery": False,
            "discovery_age_days": None,
            "discovery_source": None,
        }

    age_days = max(0, int((asof_ts_ms - source_ts) / 86_400_000))
    return {
        "discovery": age_days <= int(max_age_days),
        "discovery_age_days": age_days,
        "discovery_source": source,
    }


```

### `scanner/pipeline/manifest.py`

**SHA256:** `2f448573be5f56692958f7a742c04256787c47ccb8a8ad8dcbd3af89e5be09d0`

```python
"""Run manifest generation and persistence helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def _nested_mapping_value(config: Dict[str, Any], path: List[str], default: Any) -> Any:
    cursor: Any = config
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            return default
        cursor = cursor[key]
    return cursor


def _nested_bool(config: Dict[str, Any], path: List[str], default: bool) -> bool:
    return bool(_nested_mapping_value(config, path, default))


def derive_feature_flags(config: Dict[str, Any]) -> Dict[str, bool]:
    """Return a deterministic map of relevant feature flags and their states."""
    return {
        "decision_enabled": _nested_bool(config, ["decision", "enabled"], True),
        "risk_enabled": _nested_bool(config, ["risk", "enabled"], True),
        "tradeability_enabled": _nested_bool(config, ["tradeability", "enabled"], True),
        "btc_regime_enabled": _nested_bool(config, ["btc_regime", "enabled"], False),
        "breakout_scoring_enabled": _nested_bool(config, ["scoring", "breakout", "enabled"], True),
        "pullback_scoring_enabled": _nested_bool(config, ["scoring", "pullback", "enabled"], True),
        "reversal_scoring_enabled": _nested_bool(config, ["scoring", "reversal", "enabled"], True),
        "mexc_enabled": _nested_bool(config, ["data_sources", "mexc", "enabled"], True),
    }


def build_config_hash(config: Dict[str, Any]) -> str:
    """Build a stable SHA-256 hash from the raw runtime config."""
    canonical_json = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def read_canonical_schema_version(changelog_path: Path) -> str:
    """Read canonical_schema_version from docs/canonical/CHANGELOG.md."""
    for line in changelog_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("canonical_schema_version:"):
            _, value = line.split(":", 1)
            version = value.strip()
            if version:
                return version
            raise ValueError("canonical_schema_version is empty")
    raise ValueError("canonical_schema_version not found in canonical changelog")


def write_manifest_atomic(path: Path, payload: Dict[str, Any]) -> None:
    """Atomically write manifest JSON to avoid partial writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)

```

### `scanner/pipeline/decision.py`

**SHA256:** `279c451d27aadbb8a5a48b1ed3cb1e199609633d5489098967d2d9638daf9bbb`

```python
"""Decision layer for canonical Phase-1 outcomes."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

ALLOWED_TRADEABILITY = {"DIRECT_OK", "TRANCHE_OK", "MARGINAL"}
ENTER_TRADEABILITY = {"DIRECT_OK", "TRANCHE_OK"}
VALID_BTC_REGIME_STATES = {"RISK_OFF", "NEUTRAL", "RISK_ON"}

REASON_ORDER = [
    "tradeability_fail",
    "tradeability_marginal",
    "risk_flag_blocked",
    "stop_distance_too_wide",
    "risk_reward_unattractive",
    "risk_data_insufficient",
    "insufficient_edge",
    "btc_regime_caution",
    "entry_not_confirmed",
    "breakout_not_confirmed",
    "retest_not_reclaimed",
    "rebound_not_confirmed",
]


def apply_decision_layer(
    candidates: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    btc_regime: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Attach deterministic decision state and reasons to fully evaluated candidates."""

    cfg = _load_decision_config(config)
    btc_regime_state = _resolve_btc_regime_state(btc_regime)
    is_risk_off = btc_regime_state == "RISK_OFF"
    enter_threshold = cfg["min_score_for_enter"] + (cfg["risk_off_enter_boost"] if is_risk_off else 0)

    out: List[Dict[str, Any]] = []
    for row in candidates:
        entry = dict(row)
        entry["btc_regime_state"] = btc_regime_state

        tradeability_class = _to_optional_str(entry.get("tradeability_class"))
        setup_score = _to_optional_float(entry.get("setup_score"))
        entry_ready = _to_optional_bool(entry.get("entry_ready"))
        risk_acceptable = _to_optional_bool(entry.get("risk_acceptable"))
        hard_risk_flags = _normalize_reason_list(entry.get("risk_flags"))
        readiness_reasons = _normalize_reason_list(entry.get("entry_readiness_reasons"))

        reasons: List[str] = []

        if tradeability_class not in ALLOWED_TRADEABILITY:
            reasons.extend(_normalize_tradeability_reasons(entry, tradeability_class))
            entry["decision"] = "NO_TRADE"
            entry["decision_reasons"] = _stable_reason_order(reasons)
            out.append(entry)
            continue

        if tradeability_class == "MARGINAL":
            reasons.append("tradeability_marginal")

        if hard_risk_flags:
            reasons.extend(hard_risk_flags)
            reasons.append("risk_flag_blocked")

        if setup_score is None:
            reasons.append("risk_data_insufficient")

        if risk_acceptable is False:
            reasons.append("risk_reward_unattractive")
        elif risk_acceptable is None:
            reasons.append("risk_data_insufficient")

        if entry_ready is False:
            reasons.append("entry_not_confirmed")
            reasons.extend(readiness_reasons)
        elif entry_ready is None:
            reasons.append("risk_data_insufficient")

        can_enter = (
            tradeability_class in ENTER_TRADEABILITY
            and entry_ready is True
            and (risk_acceptable is True or not cfg["require_risk_acceptable_for_enter"])
            and setup_score is not None
            and setup_score >= enter_threshold
            and not hard_risk_flags
        )

        if can_enter:
            entry["decision"] = "ENTER"
            entry["decision_reasons"] = []
            out.append(entry)
            continue

        if is_risk_off and setup_score is not None and setup_score < enter_threshold and setup_score >= cfg["min_score_for_enter"]:
            reasons.append("btc_regime_caution")

        can_wait = (
            tradeability_class in ALLOWED_TRADEABILITY
            and (setup_score is not None and setup_score >= cfg["min_score_for_wait"])
            and risk_acceptable is True
            and entry_ready is not None
            and not hard_risk_flags
        )

        if can_wait:
            entry["decision"] = "WAIT"
            entry["decision_reasons"] = _stable_reason_order(reasons)
        else:
            if setup_score is None or setup_score < cfg["min_score_for_wait"]:
                reasons.append("insufficient_edge")
            entry["decision"] = "NO_TRADE"
            entry["decision_reasons"] = _stable_reason_order(reasons)

        out.append(entry)

    return out


def _resolve_btc_regime_state(btc_regime: Optional[Mapping[str, Any]]) -> str:
    if btc_regime is None:
        return "NEUTRAL"

    raw_state = btc_regime.get("state")
    if raw_state is None:
        return "NEUTRAL"

    if not isinstance(raw_state, str):
        raise ValueError("btc_regime.state must be string when provided")

    state = raw_state.strip().upper()
    if state not in VALID_BTC_REGIME_STATES:
        raise ValueError(
            "btc_regime.state must be one of {'RISK_OFF','NEUTRAL','RISK_ON'}"
        )

    return state


def _load_decision_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    decision_cfg = config.get("decision", {}) if isinstance(config, Mapping) else {}
    btc_cfg = config.get("btc_regime", {}) if isinstance(config, Mapping) else {}

    min_score_for_enter = _expect_number(decision_cfg.get("min_score_for_enter", 65), "decision.min_score_for_enter")
    min_score_for_wait = _expect_number(decision_cfg.get("min_score_for_wait", 40), "decision.min_score_for_wait")
    if min_score_for_wait > min_score_for_enter:
        raise ValueError("decision.min_score_for_wait must be <= decision.min_score_for_enter")

    require_risk_acceptable_for_enter = _expect_bool(
        decision_cfg.get("require_risk_acceptable_for_enter", True),
        "decision.require_risk_acceptable_for_enter",
    )

    risk_off_enter_boost = _expect_number(btc_cfg.get("risk_off_enter_boost", 15), "btc_regime.risk_off_enter_boost")

    return {
        "min_score_for_enter": min_score_for_enter,
        "min_score_for_wait": min_score_for_wait,
        "require_risk_acceptable_for_enter": require_risk_acceptable_for_enter,
        "risk_off_enter_boost": risk_off_enter_boost,
    }


def _expect_number(value: Any, field_name: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{field_name} must be finite")
    return numeric


def _expect_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be boolean")
    return value


def _to_optional_float(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _to_optional_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return None


def _to_optional_str(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_reason_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            continue
        reason = item.strip()
        if not reason or reason in seen:
            continue
        seen.add(reason)
        out.append(reason)
    return out


def _normalize_tradeability_reasons(entry: MutableMapping[str, Any], tradeability_class: Optional[str]) -> List[str]:
    provided = _normalize_reason_list(entry.get("tradeability_reason_keys"))
    if provided:
        return provided
    if tradeability_class == "MARGINAL":
        return ["tradeability_marginal"]
    return ["tradeability_fail"]


def _stable_reason_order(reasons: Iterable[str]) -> List[str]:
    provided: List[str] = []
    seen = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        provided.append(reason)

    ordered: List[str] = []
    for reason in REASON_ORDER:
        if reason in seen:
            ordered.append(reason)

    for reason in provided:
        if reason not in ordered:
            ordered.append(reason)

    return ordered

```

### `scanner/pipeline/output.py`

**SHA256:** `99e09fb69ed49843b4870b8fa27a8429d7ec3cc0e573c928729c586bb6bf7e98`

```python
"""
Output & Report Generation
===========================

Generates human-readable (Markdown), machine-readable (JSON), and Excel reports
from scored results.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from scanner.schema import REPORT_META_VERSION, REPORT_SCHEMA_VERSION
from .manifest import (
    build_config_hash,
    derive_feature_flags,
    read_canonical_schema_version,
    write_manifest_atomic,
)

logger = logging.getLogger(__name__)

_DECISION_PRIORITY = {"ENTER": 0, "WAIT": 1, "NO_TRADE": 2}


class ReportGenerator:
    """Generates daily reports from scoring results."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            config: Config dict with 'output' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            self.root_config = config.raw
            output_config = config.raw.get('output', {})
        else:
            self.root_config = config
            output_config = config.get('output', {})
        
        self.reports_dir = Path(output_config.get('reports_dir', 'reports'))
        self.top_n = output_config.get('top_n_per_setup', 10)
        
        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Report Generator initialized: reports_dir={self.reports_dir}")

    def _build_run_manifest(
        self,
        run_date: str,
        metadata: Optional[Dict[str, Any]],
        trade_candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        asof_ts_ms = metadata.get("asof_ts_ms")
        asof_iso = metadata.get("asof_iso")
        run_id = str(metadata.get("run_id") or asof_ts_ms or run_date)

        default_stage_counts = {
            "trade_candidates": len(trade_candidates),
        }
        stage_counts = metadata.get("stage_counts")
        if not isinstance(stage_counts, dict):
            stage_counts = default_stage_counts
        else:
            stage_counts = {**stage_counts}
            stage_counts.setdefault("trade_candidates", len(trade_candidates))

        warnings_list = metadata.get("warnings", [])
        if isinstance(warnings_list, list):
            warnings_payload = [str(item) for item in warnings_list]
        else:
            warnings_payload = [str(warnings_list)]

        data_freshness = metadata.get("data_freshness")
        if not isinstance(data_freshness, dict):
            data_freshness = {
                "asof_iso_utc": asof_iso,
                "asof_ts_ms": asof_ts_ms,
            }

        manifest = {
            "run_id": run_id,
            "timestamp_utc": metadata.get("timestamp_utc") or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "config_hash": build_config_hash(self.root_config),
            "canonical_schema_version": read_canonical_schema_version(Path("docs/canonical/CHANGELOG.md")),
            "feature_flags": derive_feature_flags(self.root_config),
            "counts_per_stage": stage_counts,
            "shortlist_size_used": metadata.get("shortlist_size_used", self.root_config.get("budget", {}).get("shortlist_size", 200)),
            "orderbook_top_k_used": metadata.get("orderbook_top_k_used", self.root_config.get("budget", {}).get("orderbook_top_k", 200)),
            "data_freshness": data_freshness,
            "warnings": warnings_payload,
            "duration_seconds": float(metadata.get("duration_seconds", 0.0)),
        }
        return manifest
    
    def generate_markdown_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        btc_regime: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Generate Markdown report.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
        
        Returns:
            Markdown content as string
        """
        report = self.generate_json_report(
            reversal_results=reversal_results,
            breakout_results=breakout_results,
            pullback_results=pullback_results,
            global_top20=global_top20,
            run_date=run_date,
            metadata=metadata,
            btc_regime=btc_regime,
        )
        trade_candidates = report.get("trade_candidates", [])
        run_manifest = report.get("run_manifest", {})
        resolved_regime = report.get("btc_regime", {})

        self._validate_trade_candidates_for_markdown(trade_candidates)

        enter_candidates = [row for row in trade_candidates if row.get("decision") == "ENTER"]
        wait_candidates = [row for row in trade_candidates if row.get("decision") == "WAIT"]

        lines = [
            "# Spot Altcoin Scanner Report",
            f"**Date:** {run_date}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## ENTER Candidates",
            "",
        ]

        if enter_candidates:
            for row in enter_candidates:
                lines.extend(self._format_trade_candidate_markdown(row, include_reasons=False))
        else:
            lines.append("*No ENTER candidates.*")
            lines.append("")

        lines.extend(["## WAIT Candidates", ""])
        if wait_candidates:
            for row in wait_candidates:
                lines.extend(self._format_trade_candidate_markdown(row, include_reasons=True))
        else:
            lines.append("*No WAIT candidates.*")
            lines.append("")

        lines.extend(self._format_markdown_summary(trade_candidates, run_manifest, resolved_regime))
        return "\n".join(lines)
    

    @staticmethod
    def _format_nullable_bool(value: Any) -> str:
        if value is None:
            return "n/a"
        return "true" if value is True else "false"

    @staticmethod
    def _format_nullable_float(value: Any, digits: int = 4) -> str:
        numeric = ReportGenerator._sanitize_float_or_none(value)
        if numeric is None:
            return "n/a"
        return f"{numeric:.{digits}f}"

    @staticmethod
    def _format_reason_list(value: Any) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, list):
            normalized = [item for item in value if isinstance(item, str)]
            if not normalized:
                return "[]"
            return ", ".join(normalized)
        raise ValueError("trade_candidates.decision_reasons must be a list or null")

    def _validate_trade_candidates_for_markdown(self, trade_candidates: Any) -> None:
        if not isinstance(trade_candidates, list):
            raise ValueError("trade_candidates must be a list")
        required_fields = {"rank", "symbol", "decision", "decision_reasons"}
        for idx, row in enumerate(trade_candidates):
            if not isinstance(row, dict):
                raise ValueError(f"trade_candidates[{idx}] must be an object")
            missing = [field for field in required_fields if field not in row]
            if missing:
                raise ValueError(f"trade_candidates[{idx}] missing required fields: {', '.join(missing)}")
            decision = row.get("decision")
            if decision not in {"ENTER", "WAIT", "NO_TRADE"}:
                raise ValueError(f"trade_candidates[{idx}].decision invalid: {decision}")
            reasons = row.get("decision_reasons")
            if reasons is not None and not isinstance(reasons, list):
                raise ValueError(f"trade_candidates[{idx}].decision_reasons must be list or null")

    def _format_trade_candidate_markdown(self, row: Dict[str, Any], include_reasons: bool) -> List[str]:
        rank = row.get("rank", "?")
        symbol = row.get("symbol") or "UNKNOWN"
        coin_name = row.get("coin_name") or "Unknown"
        lines = [f"### {rank}. {symbol} ({coin_name})", ""]
        lines.append(f"- decision: {row.get('decision')}")
        if include_reasons:
            lines.append(f"- decision_reasons: {self._format_reason_list(row.get('decision_reasons'))}")
        lines.append(f"- risk_acceptable: {self._format_nullable_bool(row.get('risk_acceptable'))}")
        lines.append(f"- rr_to_tp10: {self._format_nullable_float(row.get('rr_to_tp10'))}")
        lines.append(f"- slippage_bps_20k: {self._format_nullable_float(row.get('slippage_bps_20k'))}")
        lines.append(f"- spread_pct: {self._format_nullable_float(row.get('spread_pct'), digits=6)}")
        lines.append(f"- depth_bid_1pct_usd: {self._format_nullable_float(row.get('depth_bid_1pct_usd'), digits=2)}")
        lines.append(f"- depth_ask_1pct_usd: {self._format_nullable_float(row.get('depth_ask_1pct_usd'), digits=2)}")
        lines.append("")
        return lines

    def _format_markdown_summary(
        self,
        trade_candidates: List[Dict[str, Any]],
        run_manifest: Dict[str, Any],
        btc_regime: Dict[str, Any],
    ) -> List[str]:
        counts = {"ENTER": 0, "WAIT": 0, "NO_TRADE": 0}
        for row in trade_candidates:
            decision = row.get("decision")
            if decision in counts:
                counts[decision] += 1

        lines = ["## Summary", ""]
        lines.append(f"- ENTER: {counts['ENTER']}")
        lines.append(f"- WAIT: {counts['WAIT']}")
        lines.append(f"- NO_TRADE: {counts['NO_TRADE']}")

        regime_state = (btc_regime or {}).get("state")
        if regime_state is not None:
            lines.append(f"- BTC Regime: {regime_state}")

        run_id = (run_manifest or {}).get("run_id")
        if run_id is not None:
            lines.append(f"- run_id: {run_id}")
        canonical_schema_version = (run_manifest or {}).get("canonical_schema_version")
        if canonical_schema_version is not None:
            lines.append(f"- canonical_schema_version: {canonical_schema_version}")

        lines.append("")
        return lines

    def _format_setup_entry(self, rank: int, data: dict) -> List[str]:
        """
        Format a single setup entry for markdown output.
        
        Args:
            rank: Position in ranking (1-based)
            data: Setup data dict containing symbol, score, components, etc.
        
        Returns:
            List of markdown lines
        """
        lines = []
        
        # Extract data
        symbol = data.get('symbol', 'UNKNOWN')
        coin_name = data.get('coin_name', 'Unknown')
        score = data.get('score', 0)
        raw_score = data.get('raw_score')
        penalty_multiplier = data.get('penalty_multiplier')
        price = data.get('price_usdt')
        
        # Header with rank, symbol, name, and score
        lines.append(f"### {rank}. {symbol} ({coin_name}) - Score: {score:.1f}")
        lines.append("")

        # Score transparency
        if raw_score is not None or penalty_multiplier is not None:
            raw_display = f"{float(raw_score):.2f}" if raw_score is not None else "n/a"
            pm_display = f"{float(penalty_multiplier):.4f}" if penalty_multiplier is not None else "n/a"
            lines.append(f"**Score Details:** score={float(score):.2f}, raw_score={raw_display}, penalty_multiplier={pm_display}")
            lines.append("")
        
        # Price
        if price is not None:
            lines.append(f"**Price:** ${price:.6f} USDT")
            lines.append("")

        if "execution_gate_pass" in data:
            lines.append(f"**Execution Gate:** {bool(data.get('execution_gate_pass'))}")
            lines.append(f"**Spread %:** {data.get('spread_pct')}")
            lines.append(f"**Depth Bid 1.0% (USD):** {data.get('depth_bid_1pct_usd')}")
            lines.append(f"**Depth Ask 1.0% (USD):** {data.get('depth_ask_1pct_usd')}")
            fail_reasons = data.get('execution_gate_fail_reasons') or []
            if fail_reasons:
                lines.append(f"**Execution Gate Fail Reasons:** {', '.join(fail_reasons)}")
            lines.append("")

        global_volume_24h_usd = self._sanitize_optional_metric(data.get('global_volume_24h_usd'))
        turnover_24h = self._sanitize_optional_metric(data.get('turnover_24h'))
        mexc_share_24h = self._sanitize_optional_metric(data.get('mexc_share_24h'))
        lines.append("**Market Activity:**")
        lines.append(f"- global_volume_24h_usd: {self._format_m_usd(global_volume_24h_usd)}")
        lines.append(f"- turnover_24h: {self._format_pct(turnover_24h)}")
        lines.append(f"- mexc_share_24h: {self._format_pct(mexc_share_24h)}")
        lines.append("")
        
        # Components
        components = data.get('components', {})
        if components:
            lines.append("**Components:**")
            for comp_name, comp_value in components.items():
                lines.append(f"- {comp_name.replace('_', ' ').capitalize()}: {comp_value:.1f}")
            lines.append("")
        
        # Analysis
        analysis = data.get('analysis', '')
        if analysis:
            lines.append("**Analysis:**")
            if isinstance(analysis, str):
                lines.append(analysis)
            else:
                lines.append(json.dumps(analysis, ensure_ascii=False))
            lines.append("")
        
        # Flags - handle both dict and list formats
        flags = data.get('flags', {})
        flag_list = []
        
        if isinstance(flags, dict):
            flag_list = [k for k, v in flags.items() if v]
        elif isinstance(flags, list):
            flag_list = flags
        
        if flag_list:
            flag_str = ', '.join(flag_list)
            lines.append(f"**⚠️ Flags:** {flag_str}")
            lines.append("")
        
        return lines
        
    @staticmethod
    def _with_rank(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return entries with explicit 1-based rank preserving order."""
        ranked = []
        for idx, entry in enumerate(entries, start=1):
            ranked_entry = dict(entry)
            ranked_entry["rank"] = idx
            ranked_entry["global_volume_24h_usd"] = ReportGenerator._sanitize_optional_metric(entry.get("global_volume_24h_usd"))
            ranked_entry["turnover_24h"] = ReportGenerator._sanitize_optional_metric(entry.get("turnover_24h"))
            ranked_entry["mexc_share_24h"] = ReportGenerator._sanitize_optional_metric(entry.get("mexc_share_24h"))
            ranked.append(ranked_entry)
        return ranked


    @staticmethod
    def _format_m_usd(value: Any) -> str:
        if value is None:
            return "n/a"
        return f"{value / 1_000_000:.1f}".replace('.', ',') + " M USD"

    @staticmethod
    def _format_pct(value: Any) -> str:
        if value is None:
            return "n/a"
        return f"{value * 100:.2f}".replace('.', ',') + " %"

    @staticmethod
    def _sanitize_optional_metric(value: Any) -> Any:
        """Return nullable numeric metric; invalid values become None."""
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric < 0:
            return None
        if numeric != numeric:  # NaN
            return None
        return numeric

    @staticmethod
    def _sanitize_reason_list(value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        out: List[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        return out

    @staticmethod
    def _sanitize_bool_or_none(value: Any) -> Any:
        if value is None or isinstance(value, bool):
            return value
        return None

    @staticmethod
    def _sanitize_float_or_none(value: Any) -> Any:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric != numeric:
            return None
        return numeric

    @staticmethod
    def _decision_sort_key(row: Dict[str, Any]) -> Any:
        decision = str(row.get("decision") or "NO_TRADE").upper()
        priority = _DECISION_PRIORITY.get(decision, 99)
        global_score = ReportGenerator._sanitize_float_or_none(row.get("global_score"))
        score_key = -(global_score if global_score is not None else float("-inf"))
        return (
            priority,
            score_key,
            str(row.get("symbol") or ""),
            str(row.get("best_setup_type") or ""),
        )

    def _build_trade_candidates(self, global_top20: List[Dict[str, Any]], btc_regime: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        regime_state = ((btc_regime or {}).get("state") or "NEUTRAL")
        candidates: List[Dict[str, Any]] = []
        for row in global_top20:
            trade_levels = (row.get("analysis") or {}).get("trade_levels") if isinstance(row.get("analysis"), dict) else {}
            targets = trade_levels.get("targets") if isinstance(trade_levels, dict) and isinstance(trade_levels.get("targets"), list) else []
            entry_price = row.get("entry_price_usdt", row.get("price_usdt"))
            candidate = {
                "rank": None,
                "symbol": row.get("symbol"),
                "coin_name": row.get("coin_name"),
                "decision": row.get("decision", "NO_TRADE"),
                "decision_reasons": self._sanitize_reason_list(row.get("decision_reasons")),
                "entry_price_usdt": self._sanitize_float_or_none(entry_price),
                "stop_price_initial": self._sanitize_float_or_none(row.get("stop_price_initial")),
                "risk_pct_to_stop": self._sanitize_float_or_none(row.get("risk_pct_to_stop")),
                "tp10_price": self._sanitize_float_or_none(row.get("tp10_price", targets[0] if len(targets) >= 1 else None)),
                "tp20_price": self._sanitize_float_or_none(row.get("tp20_price", targets[1] if len(targets) >= 2 else None)),
                "rr_to_tp10": self._sanitize_float_or_none(row.get("rr_to_tp10")),
                "rr_to_tp20": self._sanitize_float_or_none(row.get("rr_to_tp20")),
                "best_setup_type": row.get("best_setup_type"),
                "setup_subtype": row.get("setup_subtype"),
                "setup_score": self._sanitize_float_or_none(row.get("setup_score", row.get("score"))),
                "global_score": self._sanitize_float_or_none(row.get("global_score", row.get("score"))),
                "entry_ready": self._sanitize_bool_or_none(row.get("entry_ready")),
                "entry_readiness_reasons": self._sanitize_reason_list(row.get("entry_readiness_reasons")),
                "tradeability_class": row.get("tradeability_class"),
                "execution_mode": row.get("execution_mode", "none"),
                "spread_pct": self._sanitize_float_or_none(row.get("spread_pct")),
                "depth_bid_1pct_usd": self._sanitize_float_or_none(row.get("depth_bid_1pct_usd")),
                "depth_ask_1pct_usd": self._sanitize_float_or_none(row.get("depth_ask_1pct_usd")),
                "slippage_bps_5k": self._sanitize_float_or_none(row.get("slippage_bps_5k")),
                "slippage_bps_20k": self._sanitize_float_or_none(row.get("slippage_bps_20k", row.get("slippage_bps"))),
                "risk_acceptable": self._sanitize_bool_or_none(row.get("risk_acceptable")),
                "market_cap_usd": self._sanitize_float_or_none(row.get("market_cap_usd", row.get("market_cap"))),
                "btc_regime": row.get("btc_regime", row.get("btc_regime_state", regime_state)),
                "flags": row.get("flags", []),
            }
            candidates.append(candidate)

        candidates.sort(key=self._decision_sort_key)
        for idx, row in enumerate(candidates, start=1):
            row["rank"] = idx
        return candidates

    def generate_json_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None,
        btc_regime: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate JSON report.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata dict
        
        Returns:
            Report dict (JSON-serializable)
        """
        trade_candidates = self._build_trade_candidates(global_top20[:20], btc_regime=btc_regime)
        run_manifest = self._build_run_manifest(run_date=run_date, metadata=metadata, trade_candidates=trade_candidates)

        report = {
            'schema_version': REPORT_SCHEMA_VERSION,
            'meta': {
                'date': run_date,
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'version': REPORT_META_VERSION
            },
            'summary': {
                'reversal_count': len(reversal_results),
                'breakout_count': len(breakout_results),
                'pullback_count': len(pullback_results),
                'total_scored': len(reversal_results) + len(breakout_results) + len(pullback_results),
                'global_top20_count': len(global_top20)
            },
            'setups': {
                'reversals': self._with_rank(reversal_results[:self.top_n]),
                'breakouts': self._with_rank(breakout_results[:self.top_n]),
                'breakout_immediate_1_5d': self._with_rank([
                    row for row in breakout_results if not str(row.get('setup_id', '')).endswith('retest_1_5d')
                ][:self.top_n]),
                'breakout_retest_1_5d': self._with_rank(
                    [row for row in breakout_results if str(row.get('setup_id', '')).endswith('retest_1_5d')][:self.top_n]
                ),
                'pullbacks': self._with_rank(pullback_results[:self.top_n]),
                'global_top20': self._with_rank(global_top20[:20])
            },
            'trade_candidates': trade_candidates,
            'run_manifest': run_manifest,
            'btc_regime': btc_regime or {
                'state': 'RISK_OFF',
                'multiplier_risk_on': 1.0,
                'multiplier_risk_off': 0.85,
                'checks': {
                    'close_gt_ema50': False,
                    'ema20_gt_ema50': False,
                },
            },
        }
        
        if metadata:
            report['meta'].update(metadata)
        
        return report
    
    def save_reports(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None,
        btc_regime: Dict[str, Any] = None,
    ) -> Dict[str, Path]:
        """
        Generate and save Markdown, JSON, and Excel reports.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata
        
        Returns:
            Dict with paths: {'markdown': Path, 'json': Path, 'excel': Path}
        """
        logger.info(f"Generating reports for {run_date}")
        
        # Generate Markdown
        md_content = self.generate_markdown_report(
            reversal_results, breakout_results, pullback_results, global_top20, run_date, btc_regime=btc_regime, metadata=metadata
        )
        
        # Generate JSON
        json_content = self.generate_json_report(
            reversal_results, breakout_results, pullback_results, global_top20, run_date, metadata, btc_regime=btc_regime
        )
        
        # Save Markdown
        md_path = self.reports_dir / f"{run_date}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Markdown report saved: {md_path}")
        
        # Save JSON
        json_path = self.reports_dir / f"{run_date}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON report saved: {json_path}")

        manifest = json_content.get("run_manifest", {})
        run_id = manifest.get("run_id", run_date)
        manifest_path = self.reports_dir / f"{run_date}_{run_id}.manifest.json"
        write_manifest_atomic(manifest_path, manifest)
        logger.info(f"Run manifest saved: {manifest_path}")
        
        # Generate Excel
        try:
            from .excel_output import ExcelReportGenerator
            # Reconstruct config dict for Excel generator
            excel_config = {
                'output': {
                    'reports_dir': str(self.reports_dir),
                    'top_n_per_setup': self.top_n
                }
            }
            excel_gen = ExcelReportGenerator(excel_config)
            excel_path = excel_gen.generate_excel_report(
                trade_candidates=json_content.get('trade_candidates', []),
                run_date=run_date,
                run_manifest=json_content.get('run_manifest', {}),
                metadata=metadata,
                btc_regime=btc_regime,
            )
            logger.info(f"Excel report saved: {excel_path}")
        except ImportError:
            logger.warning("openpyxl not installed - Excel export skipped")
            excel_path = None
        except Exception as e:
            logger.error(f"Excel generation failed: {e}")
            excel_path = None
        
        result = {
            'markdown': md_path,
            'json': json_path,
            'manifest': manifest_path,
        }
        
        if excel_path:
            result['excel'] = excel_path
        
        return result

```

### `scanner/pipeline/ohlcv.py`

**SHA256:** `5b15b497293e634782803d809b78160a966ac098878a54626d0e0975c3e4aa59`

```python
"""
OHLCV Data Fetching
===================

Fetches OHLCV (klines) data for shortlisted symbols.
Supports multiple timeframes with caching.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

try:
    from scanner.utils.raw_collector import collect_raw_ohlcv
except ImportError:
    collect_raw_ohlcv = None

logger = logging.getLogger(__name__)


class OHLCVFetcher:
    """Fetches and caches OHLCV data for symbols."""

    def __init__(self, mexc_client, config: Dict[str, Any]):
        self.mexc = mexc_client
        root = config.raw if hasattr(config, 'raw') else config

        ohlcv_config = root.get('ohlcv', {})
        general_cfg = root.get('general', {})
        history_cfg = root.get('universe_filters', {}).get('history', {})

        self.timeframes = ohlcv_config.get('timeframes', ['1d', '4h'])

        self.lookback = self._build_lookback(general_cfg, ohlcv_config.get('lookback', {}))

        self.min_candles = ohlcv_config.get('min_candles', {'1d': 50, '4h': 50})
        self.min_history_days_1d = int(history_cfg.get('min_history_days_1d', 60))

        logger.info(f"OHLCV Fetcher initialized: timeframes={self.timeframes}, lookback={self.lookback}")


    def _build_lookback(self, general_cfg: Dict[str, Any], ohlcv_lookback_cfg: Dict[str, Any]) -> Dict[str, int]:
        """Build timeframe lookback (API limit bars) with explicit precedence.

        Precedence:
        1) `ohlcv.lookback[timeframe]` explicit override (bars)
        2) `general.lookback_days_*` defaults (`1d`: days->bars 1:1, `4h`: days*6)
        3) hard defaults (`1d`=120, `4h`=180 bars)

        1D lookback is always incremented by +1 bar to include one potentially open
        candle while still guaranteeing `min_history_*_1d` checks run against closed
        candles only (closed-candle reality).
        """
        lookback_1d_default = int(general_cfg.get('lookback_days_1d', 120))
        lookback_4h_default = int(general_cfg.get('lookback_days_4h', 30)) * 6

        lookback = {
            '1d': lookback_1d_default + 1,
            '4h': lookback_4h_default,
        }

        if isinstance(ohlcv_lookback_cfg, dict):
            for tf, bars in ohlcv_lookback_cfg.items():
                try:
                    parsed = int(bars)
                    if str(tf) == '1d':
                        parsed += 1
                    lookback[str(tf)] = parsed
                except (TypeError, ValueError):
                    logger.warning(f"Invalid ohlcv.lookback value for timeframe '{tf}': {bars}; ignoring override")

        return lookback

    def fetch_all(self, shortlist: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        results = {}
        total = len(shortlist)

        logger.info(f"Fetching OHLCV for {total} symbols across {len(self.timeframes)} timeframes")

        for i, sym_data in enumerate(shortlist, 1):
            symbol = sym_data['symbol']
            logger.info(f"[{i}/{total}] Fetching {symbol}...")

            symbol_ohlcv = {}
            failed = False

            for tf in self.timeframes:
                limit = int(self.lookback.get(tf, 120))

                try:
                    klines = self.mexc.get_klines(symbol, tf, limit=limit)

                    if not klines:
                        logger.warning(f"  {symbol} {tf}: No data returned")
                        failed = True
                        break

                    min_required = int(self.min_candles.get(tf, 50))
                    if len(klines) < min_required:
                        logger.warning(f"  {symbol} {tf}: Insufficient data ({len(klines)} < {min_required} candles)")
                        failed = True
                        break

                    if tf == '1d' and len(klines) < self.min_history_days_1d:
                        logger.warning(
                            f"  {symbol} {tf}: Below history threshold ({len(klines)} < {self.min_history_days_1d} days)"
                        )
                        failed = True
                        break

                    symbol_ohlcv[tf] = klines
                    logger.info(f"  ✓ {symbol} {tf}: {len(klines)} candles")

                except Exception as e:
                    logger.error(f"  ✗ {symbol} {tf}: {e}")
                    failed = True
                    break

            if not failed:
                results[symbol] = symbol_ohlcv
            else:
                logger.warning(f"  Skipping {symbol} (incomplete data)")

        logger.info(f"OHLCV fetch complete: {len(results)}/{total} symbols with complete data")

        if collect_raw_ohlcv and results:
            try:
                collect_raw_ohlcv(results)
            except Exception as e:
                logger.warning(f"Could not collect raw OHLCV snapshot: {e}")

        return results

    def get_fetch_stats(self, ohlcv_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not ohlcv_data:
            return {'symbols_count': 0, 'timeframes': [], 'total_candles': 0}

        total_candles = 0
        for symbol_data in ohlcv_data.values():
            for tf_data in symbol_data.values():
                total_candles += len(tf_data)

        date_range = None
        first_symbol = list(ohlcv_data.keys())[0]
        if '1d' in ohlcv_data[first_symbol]:
            candles = ohlcv_data[first_symbol]['1d']
            if candles:
                oldest = datetime.fromtimestamp(candles[0][0] / 1000).strftime('%Y-%m-%d')
                newest = datetime.fromtimestamp(candles[-1][0] / 1000).strftime('%Y-%m-%d')
                date_range = f"{oldest} to {newest}"

        return {
            'symbols_count': len(ohlcv_data),
            'timeframes': self.timeframes,
            'total_candles': total_candles,
            'avg_candles_per_symbol': total_candles / len(ohlcv_data) if ohlcv_data else 0,
            'date_range': date_range,
        }

```

### `scanner/pipeline/backtest_runner.py`

**SHA256:** `d3e0d07cd7845da343c32f58ab88d7c5519dfcd239901e116ac0b26691b1480f`

```python
from __future__ import annotations

"""Deterministic backtest runner (Analytics-only, E2-K).

Canonical v2 rules (Feature-Spec section 10):
- Trigger search on 1D close within ``[t0 .. t0 + T_trigger_max]``
- ``entry_price = close[trigger_day]``
- ``hit_10`` / ``hit_20`` use ``max(high[trigger_day+1 .. trigger_day+T_hold])``
- No exit logic.
"""

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import json


DEFAULT_BACKTEST_CFG: Dict[str, Any] = {
    "t_hold": 10,
    "t_trigger_max": 5,
    "thresholds_pct": [10.0, 20.0],
}

BREAKOUT_TREND_SETUP_IDS = {"breakout_immediate_1_5d", "breakout_retest_1_5d"}
FOUR_H_TIME_STOP_CANDLES = 42  # 168h / 4h


def _float_or_none(value: Any) -> Optional[float]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN guard
        return None
    return f


def _extract_backtest_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not config:
        return dict(DEFAULT_BACKTEST_CFG)

    bt = config.get("backtest", config)
    out = dict(DEFAULT_BACKTEST_CFG)

    # Canonical aliases in case legacy keys still exist.
    out["t_hold"] = int(bt.get("t_hold", bt.get("max_holding_days", out["t_hold"])))
    out["t_trigger_max"] = int(bt.get("t_trigger_max", out["t_trigger_max"]))

    if "thresholds_pct" in bt:
        out["thresholds_pct"] = [float(x) for x in bt.get("thresholds_pct", [])]
    elif "thresholds" in bt:
        out["thresholds_pct"] = [float(x) for x in bt.get("thresholds", [])]

    return out


def _setup_triggered(setup_type: str, close: float, trade_levels: Mapping[str, Any]) -> bool:
    if setup_type == "breakout":
        trigger = _float_or_none(trade_levels.get("entry_trigger") or trade_levels.get("breakout_level_20"))
        return trigger is not None and close >= trigger
    if setup_type == "reversal":
        trigger = _float_or_none(trade_levels.get("entry_trigger"))
        return trigger is not None and close >= trigger
    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone") or {}
        low = _float_or_none(zone.get("lower"))
        high = _float_or_none(zone.get("upper"))
        return low is not None and high is not None and low <= close <= high
    return False


def _evaluate_candidate(
    *,
    symbol: str,
    setup_type: str,
    t0_date: str,
    index_by_date: Mapping[str, int],
    series_close: Sequence[Optional[float]],
    series_high: Sequence[Optional[float]],
    trade_levels: Mapping[str, Any],
    t_trigger_max: int,
    t_hold: int,
    thresholds_pct: Sequence[float],
) -> Dict[str, Any]:
    def _iso_to_date(value: str) -> Optional[date]:
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    def _calendar_window_indices(
        *,
        start_date: date,
        days_inclusive: int,
    ) -> Iterable[Tuple[int, int]]:
        for day_offset in range(days_inclusive + 1):
            day = (start_date + timedelta(days=day_offset)).isoformat()
            idx = index_by_date.get(day)
            if idx is None:
                continue
            yield day_offset, idx

    t0_parsed = _iso_to_date(t0_date)
    if t0_parsed is None:
        return {
            "symbol": symbol,
            "setup_type": setup_type,
            "t0_date": t0_date,
            "triggered": False,
            "trigger_day_offset": None,
            "entry_price": None,
            "max_high_after_entry": None,
            **{f"hit_{int(thr)}": False for thr in thresholds_pct},
        }

    trigger_idx: Optional[int] = None
    trigger_day_offset: Optional[int] = None
    for day_offset, idx in _calendar_window_indices(start_date=t0_parsed, days_inclusive=t_trigger_max):
        close = series_close[idx]
        if close is None:
            continue
        if _setup_triggered(setup_type, close, trade_levels):
            trigger_idx = idx
            trigger_day_offset = day_offset
            break

    outcome: Dict[str, Any] = {
        "symbol": symbol,
        "setup_type": setup_type,
        "t0_date": t0_date,
        "triggered": trigger_idx is not None,
        "trigger_day_offset": None,
        "entry_price": None,
        "max_high_after_entry": None,
    }

    for thr in thresholds_pct:
        outcome[f"hit_{int(thr)}"] = False

    if trigger_idx is None:
        return outcome

    entry_price = series_close[trigger_idx]
    if entry_price is None or entry_price <= 0:
        return outcome

    trigger_date = t0_parsed + timedelta(days=trigger_day_offset or 0)
    window_highs: List[float] = []
    for hold_offset in range(1, t_hold + 1):
        hold_day = (trigger_date + timedelta(days=hold_offset)).isoformat()
        hold_idx = index_by_date.get(hold_day)
        if hold_idx is None:
            continue
        high = series_high[hold_idx]
        if high is None:
            continue
        window_highs.append(high)

    max_high = max(window_highs) if window_highs else None

    outcome.update(
        {
            "trigger_day_offset": trigger_day_offset,
            "entry_price": entry_price,
            "max_high_after_entry": max_high,
        }
    )

    if max_high is None:
        return outcome

    for thr in thresholds_pct:
        target = entry_price * (1.0 + thr / 100.0)
        outcome[f"hit_{int(thr)}"] = max_high >= target

    return outcome


def _summarize(events: Sequence[Dict[str, Any]], thresholds_pct: Sequence[float]) -> Dict[str, Any]:
    def _is_executed_trade(event: Mapping[str, Any]) -> bool:
        if event.get("trade_status") == "TRADE":
            return True

        entry_price = _float_or_none(event.get("entry_price"))
        if entry_price is None:
            return False

        entry_time = event.get("entry_time")
        if entry_time is not None:
            return True

        trigger_day_offset = event.get("trigger_day_offset")
        if isinstance(trigger_day_offset, int) and trigger_day_offset >= 0:
            return True

        entry_idx = event.get("entry_idx")
        if isinstance(entry_idx, int) and entry_idx >= 0:
            return True

        position_size = _float_or_none(event.get("position_size"))
        return position_size is not None and position_size > 0

    total = len(events)
    triggered = [e for e in events if e.get("triggered")]
    trades = [e for e in events if _is_executed_trade(e)]
    summary: Dict[str, Any] = {
        "count": total,
        "signals_count": total,
        "triggered_count": len(triggered),
        "trigger_rate": (len(triggered) / total) if total else 0.0,
        "trades_count": len(trades),
        "trade_rate_on_signals": (len(trades) / total) if total else 0.0,
    }

    for thr in thresholds_pct:
        key = f"hit_{int(thr)}"
        hit_count = sum(1 for e in triggered if e.get(key))
        summary[f"{key}_count"] = hit_count
        summary[f"{key}_rate_on_triggered"] = (hit_count / len(triggered)) if triggered else 0.0

    return summary


def _simulate_breakout_4h_trade(entry: Mapping[str, Any], setup_id: str) -> Optional[Dict[str, Any]]:
    analysis = entry.get("analysis") if isinstance(entry.get("analysis"), Mapping) else {}
    trade_levels = analysis.get("trade_levels") if isinstance(analysis.get("trade_levels"), Mapping) else {}
    bt = analysis.get("backtest_4h") if isinstance(analysis.get("backtest_4h"), Mapping) else {}
    candles = bt.get("candles") if isinstance(bt.get("candles"), list) else []
    if not candles:
        return None

    breakout_level = _float_or_none(trade_levels.get("entry_trigger") or trade_levels.get("breakout_level_20"))
    if breakout_level is None:
        return None

    trigger_idx = None
    for idx, candle in enumerate(candles):
        close = _float_or_none(candle.get("close") if isinstance(candle, Mapping) else None)
        if close is not None and close > breakout_level:
            trigger_idx = idx
            break
    if trigger_idx is None:
        return {
            "symbol": entry.get("symbol"),
            "setup_id": setup_id,
            "triggered": False,
            "entry_idx": None,
            "exit_reason": None,
        }

    if setup_id == "breakout_immediate_1_5d":
        entry_idx = trigger_idx + 1
        if entry_idx >= len(candles):
            return None
        entry_price = _float_or_none(candles[entry_idx].get("open") if isinstance(candles[entry_idx], Mapping) else None)
    else:
        entry_price = breakout_level
        entry_idx = None
        for idx in range(trigger_idx + 1, len(candles)):
            candle = candles[idx]
            if not isinstance(candle, Mapping):
                continue
            close = _float_or_none(candle.get("close"))
            if close is not None and close < breakout_level:
                return {
                    "symbol": entry.get("symbol"),
                    "setup_id": setup_id,
                    "triggered": True,
                    "entry_idx": None,
                    "entry_price": None,
                    "retest_invalidated": True,
                    "exit_reason": None,
                }
            low = _float_or_none(candle.get("low"))
            high = _float_or_none(candle.get("high"))
            if low is not None and high is not None and low <= entry_price <= high:
                entry_idx = idx
                break
        if entry_idx is None:
            return None

    if entry_price is None:
        return None

    atr_abs = _float_or_none(bt.get("atr_abs_4h"))
    if atr_abs is None:
        atr_pct = _float_or_none(bt.get("atr_pct_4h_last_closed"))
        close_4h = _float_or_none(bt.get("close_4h_last_closed"))
        if atr_pct is not None and close_4h is not None:
            atr_abs = (atr_pct / 100.0) * close_4h
    if atr_abs is None:
        return None

    stop = entry_price - 1.2 * atr_abs
    r_val = entry_price - stop
    partial_target = entry_price + 1.5 * r_val

    partial_hit = False
    partial_idx = None
    exit_idx = None
    exit_reason = None
    exit_price = None

    for idx in range(entry_idx, len(candles)):
        candle = candles[idx]
        if not isinstance(candle, Mapping):
            continue
        low = _float_or_none(candle.get("low"))
        high = _float_or_none(candle.get("high"))

        # Intra-candle priority: STOP > PARTIAL > TRAIL
        if low is not None and low <= stop:
            exit_idx = idx
            exit_reason = "stop"
            exit_price = stop
            break

        if (not partial_hit) and high is not None and high >= partial_target:
            partial_hit = True
            partial_idx = idx

        if partial_hit:
            close = _float_or_none(candle.get("close"))
            ema20 = _float_or_none(candle.get("ema20"))
            if close is not None and ema20 is not None and close < ema20 and (idx + 1) < len(candles):
                nxt = candles[idx + 1]
                if isinstance(nxt, Mapping):
                    exit_idx = idx + 1
                    exit_reason = "trail"
                    exit_price = _float_or_none(nxt.get("open"))
                    break

        hold_candles = idx - entry_idx + 1
        if hold_candles >= FOUR_H_TIME_STOP_CANDLES and (idx + 1) < len(candles):
            nxt = candles[idx + 1]
            if isinstance(nxt, Mapping):
                exit_idx = idx + 1
                exit_reason = "time_stop"
                exit_price = _float_or_none(nxt.get("open"))
                break

    return {
        "symbol": entry.get("symbol"),
        "setup_id": setup_id,
        "trade_status": "TRADE",
        "triggered": True,
        "entry_idx": entry_idx,
        "entry_price": entry_price,
        "stop": stop,
        "partial_target": partial_target,
        "partial_hit": partial_hit,
        "partial_idx": partial_idx,
        "exit_idx": exit_idx,
        "exit_reason": exit_reason,
        "exit_price": exit_price,
    }


def _infer_breakout_no_trade_reason(entry: Mapping[str, Any], setup_id: str) -> str:
    analysis = entry.get("analysis") if isinstance(entry.get("analysis"), Mapping) else {}
    trade_levels = analysis.get("trade_levels") if isinstance(analysis.get("trade_levels"), Mapping) else {}
    bt = analysis.get("backtest_4h") if isinstance(analysis.get("backtest_4h"), Mapping) else {}
    candles = bt.get("candles") if isinstance(bt.get("candles"), list) else []
    if not candles:
        return "INSUFFICIENT_4H_HISTORY"

    breakout_level = _float_or_none(trade_levels.get("entry_trigger") or trade_levels.get("breakout_level_20"))
    if breakout_level is None:
        return "MISSING_REQUIRED_FEATURES"

    trigger_idx = None
    for idx, candle in enumerate(candles):
        close = _float_or_none(candle.get("close") if isinstance(candle, Mapping) else None)
        if close is not None and close > breakout_level:
            trigger_idx = idx
            break
    if trigger_idx is None:
        return "MISSING_NEXT_4H_OPEN"

    if setup_id == "breakout_immediate_1_5d":
        entry_idx = trigger_idx + 1
        if entry_idx >= len(candles):
            return "MISSING_NEXT_4H_OPEN"
        entry_open = _float_or_none(candles[entry_idx].get("open") if isinstance(candles[entry_idx], Mapping) else None)
        if entry_open is None:
            return "MISSING_NEXT_4H_OPEN"
    else:
        retest_filled = False
        for idx in range(trigger_idx + 1, len(candles)):
            candle = candles[idx]
            if not isinstance(candle, Mapping):
                continue
            low = _float_or_none(candle.get("low"))
            high = _float_or_none(candle.get("high"))
            if low is not None and high is not None and low <= breakout_level <= high:
                retest_filled = True
                break
        if not retest_filled:
            return "RETEST_NOT_FILLED"

    atr_abs = _float_or_none(bt.get("atr_abs_4h"))
    if atr_abs is None:
        atr_pct = _float_or_none(bt.get("atr_pct_4h_last_closed"))
        close_4h = _float_or_none(bt.get("close_4h_last_closed"))
        if atr_pct is None or close_4h is None:
            return "MISSING_REQUIRED_FEATURES"

    return "MISSING_REQUIRED_FEATURES"


def run_backtest_from_snapshots(
    snapshots: Sequence[Mapping[str, Any]],
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Run deterministic E2-K backtest on in-memory snapshot payloads."""
    cfg = _extract_backtest_config(config)
    t_hold = cfg["t_hold"]
    t_trigger_max = cfg["t_trigger_max"]
    thresholds_pct = cfg["thresholds_pct"]

    sorted_snapshots = sorted(snapshots, key=lambda s: str(s.get("meta", {}).get("date", "")))
    all_dates = [str(s.get("meta", {}).get("date")) for s in sorted_snapshots]
    index_by_date = {d: i for i, d in enumerate(all_dates)}

    closes: Dict[str, List[Optional[float]]] = defaultdict(lambda: [None] * len(all_dates))
    highs: Dict[str, List[Optional[float]]] = defaultdict(lambda: [None] * len(all_dates))

    for i, snap in enumerate(sorted_snapshots):
        features = snap.get("data", {}).get("features", {})
        for symbol, feat in features.items():
            one_d = feat.get("1d", {}) if isinstance(feat, Mapping) else {}
            closes[symbol][i] = _float_or_none(one_d.get("close"))
            highs[symbol][i] = _float_or_none(one_d.get("high"))

    setup_map = {
        "breakout": "breakouts",
        "pullback": "pullbacks",
        "reversal": "reversals",
    }

    events_by_setup: Dict[str, List[Dict[str, Any]]] = {k: [] for k in setup_map}

    for snap in sorted_snapshots:
        t0_date = str(snap.get("meta", {}).get("date"))
        scoring = snap.get("scoring", {})

        for setup_type, score_key in setup_map.items():
            for entry in scoring.get(score_key, []):
                symbol = entry.get("symbol")
                if symbol not in closes or t0_date not in index_by_date:
                    continue

                setup_id = str(entry.get("setup_id") or "")
                if setup_type == "breakout" and setup_id in BREAKOUT_TREND_SETUP_IDS:
                    event_4h = _simulate_breakout_4h_trade(entry, setup_id)
                    if event_4h is not None:
                        event_4h["t0_date"] = t0_date
                        events_by_setup.setdefault(setup_id, []).append(event_4h)
                    else:
                        events_by_setup.setdefault(setup_id, []).append(
                            {
                                "symbol": symbol,
                                "setup_id": setup_id,
                                "t0_date": t0_date,
                                "trade_status": "NO_TRADE",
                                "no_trade_reason": _infer_breakout_no_trade_reason(entry, setup_id),
                                "triggered": True,
                                "entry_idx": None,
                                "entry_price": None,
                                "exit_reason": None,
                            }
                        )
                    continue

                trade_levels = (
                    entry.get("analysis", {}).get("trade_levels")
                    if isinstance(entry.get("analysis"), Mapping)
                    else None
                ) or {}

                event = _evaluate_candidate(
                    symbol=symbol,
                    setup_type=setup_type,
                    t0_date=t0_date,
                    index_by_date=index_by_date,
                    series_close=closes[symbol],
                    series_high=highs[symbol],
                    trade_levels=trade_levels,
                    t_trigger_max=t_trigger_max,
                    t_hold=t_hold,
                    thresholds_pct=thresholds_pct,
                )
                events_by_setup[setup_type].append(event)

    summary_by_setup = {
        setup_type: _summarize(events, thresholds_pct)
        for setup_type, events in events_by_setup.items()
    }

    return {
        "params": {
            "t_hold": t_hold,
            "t_trigger_max": t_trigger_max,
            "thresholds_pct": thresholds_pct,
        },
        "by_setup": summary_by_setup,
        "events": events_by_setup,
    }


def run_backtest_from_history(
    history_dir: str | Path,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Load all snapshot json files from ``history_dir`` and run backtest."""
    history_path = Path(history_dir)
    snapshots: List[Dict[str, Any]] = []

    for snapshot_file in sorted(history_path.glob("*.json")):
        with open(snapshot_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and payload.get("meta", {}).get("date"):
            snapshots.append(payload)

    return run_backtest_from_snapshots(snapshots, config=config)

```

### `scanner/pipeline/runtime_market_meta.py`

**SHA256:** `2f7acaa18f785a04b7a0baabb6702ce7475814237acebea03f9d822059661f65`

```python
"""Runtime market metadata export for each pipeline run."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..clients.mapping import MappingResult
from ..config import ScannerConfig
from ..utils.io_utils import save_json
from ..utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class RuntimeMarketMetaExporter:
    """Builds and writes runtime market metadata export JSON."""

    def __init__(self, config: ScannerConfig | Dict[str, Any]):
        if hasattr(config, "raw"):
            self.config = config
            snapshots_config = config.raw.get("snapshots", {})
        else:
            self.config = ScannerConfig(raw=config)
            snapshots_config = config.get("snapshots", {})

        self.runtime_dir = Path(snapshots_config.get("runtime_dir", "snapshots/runtime"))
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _build_exchange_symbol_map(exchange_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        return {
            symbol_info.get("symbol"): symbol_info
            for symbol_info in exchange_info.get("symbols", [])
            if symbol_info.get("symbol")
        }

    @staticmethod
    def _extract_filter_value(symbol_info: Dict[str, Any], filter_type: str, field: str) -> Any:
        for item in symbol_info.get("filters", []):
            if item.get("filterType") == filter_type:
                return item.get(field)
        return None

    def _build_identity(self, mapping: MappingResult) -> Dict[str, Any]:
        cmc_data = mapping.cmc_data or {}
        quote_usd = cmc_data.get("quote", {}).get("USD", {})

        market_cap = self._to_float(quote_usd.get("market_cap"))
        fdv = self._to_float(quote_usd.get("fully_diluted_market_cap"))

        platform = cmc_data.get("platform")
        platform_obj = None
        if isinstance(platform, dict):
            token_address = platform.get("token_address")
            platform_obj = {
                "name": platform.get("name"),
                "symbol": platform.get("symbol"),
                "token_address": token_address,
            }
        else:
            token_address = None

        fdv_to_mcap = None
        if fdv is not None and market_cap not in (None, 0):
            fdv_to_mcap = fdv / market_cap

        return {
            "_cmc_quote_usd": quote_usd,
            "cmc_id": cmc_data.get("id"),
            "name": cmc_data.get("name"),
            "symbol": cmc_data.get("symbol"),
            "slug": cmc_data.get("slug"),
            "category": cmc_data.get("category"),
            "tags": cmc_data.get("tags"),
            "platform": platform_obj,
            "is_token": bool(token_address),
            "market_cap_usd": market_cap,
            "circulating_supply": self._to_float(cmc_data.get("circulating_supply")),
            "total_supply": self._to_float(cmc_data.get("total_supply")),
            "max_supply": self._to_float(cmc_data.get("max_supply")),
            "fdv_usd": fdv,
            "fdv_to_mcap": fdv_to_mcap,
            "rank": self._to_int(cmc_data.get("cmc_rank")),
        }

    def _build_symbol_info(self, symbol: str, exchange_symbol: Dict[str, Any]) -> Dict[str, Any]:
        tick_size = self._extract_filter_value(exchange_symbol, "PRICE_FILTER", "tickSize")
        step_size = self._extract_filter_value(exchange_symbol, "LOT_SIZE", "stepSize")
        min_qty = self._extract_filter_value(exchange_symbol, "LOT_SIZE", "minQty")
        max_qty = self._extract_filter_value(exchange_symbol, "LOT_SIZE", "maxQty")

        min_notional = self._extract_filter_value(exchange_symbol, "MIN_NOTIONAL", "minNotional")
        max_notional = self._extract_filter_value(exchange_symbol, "NOTIONAL", "maxNotional")


        return {
            "mexc_symbol": symbol,
            "base_asset": exchange_symbol.get("baseAsset"),
            "quote_asset": exchange_symbol.get("quoteAsset"),
            "status": exchange_symbol.get("status"),
            "price_precision": self._to_int(exchange_symbol.get("quotePrecision") or exchange_symbol.get("priceScale")),
            "quantity_precision": self._to_int(exchange_symbol.get("baseAssetPrecision") or exchange_symbol.get("quantityScale")),
            "tick_size": tick_size,
            "step_size": step_size,
            "min_qty": self._to_float(min_qty),
            "max_qty": self._to_float(max_qty),
            "min_notional": self._to_float(min_notional),
            "max_notional": self._to_float(max_notional),
        }

    def _build_ticker(self, ticker: Dict[str, Any], identity: Dict[str, Any]) -> Dict[str, Any]:
        bid = self._to_float(ticker.get("bidPrice"))
        ask = self._to_float(ticker.get("askPrice"))
        mid = None
        spread_pct = None

        if bid is not None and ask is not None:
            mid = (bid + ask) / 2
            if mid != 0:
                spread_pct = ((ask - bid) / mid) * 100

        quote_volume_24h = self._to_float(ticker.get("quoteVolume"))
        global_volume_24h_usd = self._to_float(
            ((identity.get("_cmc_quote_usd") or {}).get("volume_24h"))
        )

        turnover_24h = None
        market_cap_usd = identity.get("market_cap_usd")
        if global_volume_24h_usd is not None and market_cap_usd not in (None, 0):
            turnover_24h = global_volume_24h_usd / market_cap_usd

        mexc_share_24h = None
        if quote_volume_24h is not None and global_volume_24h_usd not in (None, 0):
            mexc_share_24h = quote_volume_24h / global_volume_24h_usd

        return {
            "last_price": self._to_float(ticker.get("lastPrice")),
            "high_24h": self._to_float(ticker.get("highPrice")),
            "low_24h": self._to_float(ticker.get("lowPrice")),
            "quote_volume_24h": quote_volume_24h,
            "global_volume_24h_usd": global_volume_24h_usd,
            "turnover_24h": turnover_24h,
            "mexc_share_24h": mexc_share_24h,
            "price_change_pct_24h": self._to_float(ticker.get("priceChangePercent")),
            "bid_price": bid,
            "ask_price": ask,
            "spread_pct": spread_pct,
            "mid_price": mid,
            "trades_24h": self._to_int(ticker.get("count")),
            "base_volume_24h": self._to_float(ticker.get("volume")),
        }

    def _build_quality(
        self,
        symbol: str,
        identity: Dict[str, Any],
        symbol_info: Dict[str, Any],
        has_scanner_features: bool,
        has_ohlcv: bool,
    ) -> Dict[str, Any]:
        missing_fields: List[str] = []

        if symbol_info.get("tick_size") in (None, ""):
            missing_fields.append("tick_size")
        if symbol_info.get("min_notional") is None:
            missing_fields.append("min_notional")
        if identity.get("platform") and not identity["platform"].get("token_address"):
            missing_fields.append("token_address")

        return {
            "has_scanner_features": has_scanner_features,
            "has_ohlcv": has_ohlcv,
            "missing_fields": missing_fields,
            "notes": None,
        }

    def export(
        self,
        run_date: str,
        asof_iso: str,
        run_id: str,
        filtered_symbols: List[str],
        mapping_results: Dict[str, MappingResult],
        exchange_info: Dict[str, Any],
        ticker_map: Dict[str, Dict[str, Any]],
        features: Dict[str, Dict[str, Any]],
        ohlcv_data: Dict[str, Dict[str, Any]],
        exchange_info_ts_utc: str,
        tickers_24h_ts_utc: str,
        listings_ts_utc: str,
    ) -> Path:
        """Create and save runtime market metadata export."""
        exchange_symbol_map = self._build_exchange_symbol_map(exchange_info)

        coins: Dict[str, Dict[str, Any]] = {}
        symbols = sorted(filtered_symbols)

        for symbol in symbols:
            mapping = mapping_results.get(symbol)
            if not mapping or not mapping.mapped:
                continue

            exchange_symbol = exchange_symbol_map.get(symbol, {})
            ticker = ticker_map.get(symbol, {})

            identity = self._build_identity(mapping)
            symbol_info = self._build_symbol_info(symbol, exchange_symbol)
            ticker_24h = self._build_ticker(ticker, identity)

            quality = self._build_quality(
                symbol=symbol,
                identity=identity,
                symbol_info=symbol_info,
                has_scanner_features=symbol in features,
                has_ohlcv=symbol in ohlcv_data,
            )

            identity_payload = dict(identity)
            identity_payload.pop("_cmc_quote_usd", None)

            coins[symbol] = {
                "identity": identity_payload,
                "mexc": {
                    "symbol_info": symbol_info,
                    "ticker_24h": ticker_24h,
                },
                "quality": quality,
            }

        payload = {
            "meta": {
                "run_id": run_id,
                "asof_utc": asof_iso,
                "generated_at_utc": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "mexc": {
                    "api_base": "https://api.mexc.com",
                    "exchange_info_ts_utc": exchange_info_ts_utc,
                    "tickers_24h_ts_utc": tickers_24h_ts_utc,
                },
                "cmc": {
                    "listings_ts_utc": listings_ts_utc,
                    "source": "CoinMarketCap",
                },
                "config": {
                    "mcap_min_usd": self.config.market_cap_min,
                    "mcap_max_usd": self.config.market_cap_max,
                    "min_quote_volume_24h_usdt": self.config.min_quote_volume_24h,
                },
            },
            "universe": {
                "count": len(coins),
                "symbols": list(coins.keys()),
            },
            "coins": coins,
        }

        output_path = self.runtime_dir / f"runtime_market_meta_{run_date}.json"
        save_json(payload, output_path)

        logger.info("Runtime market meta export saved: %s", output_path)
        logger.info("Runtime market meta universe count: %s", payload["universe"]["count"])

        return output_path

```

### `scanner/tools/export_evaluation_dataset.py`

**SHA256:** `bb4f0d7788d5d2b0e5e73b51aab9038604b9528b9e0c338a4c6e2c87c2f92b4c`

```python
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from scanner.backtest.e2_model import (
    DEFAULT_T_HOLD,
    DEFAULT_T_TRIGGER_MAX,
    DEFAULT_THRESHOLDS_PCT,
    evaluate_e2_candidate,
)
from scanner.config import load_config
from scanner.pipeline.global_ranking import compute_global_top20

DATASET_SCHEMA_VERSION = "1.2"


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _run_id_from_export_start(export_started_at: datetime) -> str:
    millis = export_started_at.microsecond // 1000
    return f"{export_started_at.strftime('%Y-%m-%d_%H%M%SZ')}_{millis:03d}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _score_from_entry(entry: dict[str, Any]) -> float:
    score = entry.get("score")
    if score is None:
        raise ValueError("Missing non-nullable scoring_entry.score")
    return float(score)


def _load_snapshot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid snapshot structure: {path}")
    return payload


def _build_price_series_by_symbol(snapshots: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for snapshot in snapshots:
        meta = snapshot.get("meta", {})
        t_date = meta.get("date")
        if not t_date:
            continue
        features = snapshot.get("data", {}).get("features", {})
        if not isinstance(features, dict):
            continue
        for symbol, feature in features.items():
            one_day = feature.get("1d") if isinstance(feature, dict) else None
            candle = {
                "close": one_day.get("close") if isinstance(one_day, dict) else None,
                "high": one_day.get("high") if isinstance(one_day, dict) else None,
                "low": one_day.get("low") if isinstance(one_day, dict) else None,
            }
            result.setdefault(symbol, {})[t_date] = candle
    return result


def export_dataset(args: argparse.Namespace) -> Path:
    start = _parse_date(args.from_date)
    end = _parse_date(args.to_date)
    if end < start:
        raise ValueError("--to must be >= --from")

    config = load_config(args.config)
    config_root = config.raw
    backtest_cfg = config_root.get("backtest", {})

    t_hold = int(args.t_hold if args.t_hold is not None else backtest_cfg.get("t_hold", DEFAULT_T_HOLD))
    t_trigger_max = int(
        args.t_trigger_max
        if args.t_trigger_max is not None
        else backtest_cfg.get("t_trigger_max", DEFAULT_T_TRIGGER_MAX)
    )
    thresholds_pct = [float(x) for x in (args.thresholds_pct or backtest_cfg.get("thresholds_pct", list(DEFAULT_THRESHOLDS_PCT)))]
    thresholds_pct = sorted(set(thresholds_pct + [10.0, 20.0]))

    snapshots_dir = Path(args.snapshots_dir or config_root.get("snapshots", {}).get("history_dir", "snapshots/history"))
    output_dir = Path(args.output_dir)

    snapshots: list[dict[str, Any]] = []
    missing_paths: list[Path] = []
    for day in _daterange(start, end):
        path = snapshots_dir / f"{day.isoformat()}.json"
        if not path.exists():
            missing_paths.append(path)
            continue
        snapshots.append(_load_snapshot(path))

    if missing_paths:
        msg = f"Missing {len(missing_paths)} snapshot file(s): " + ", ".join(str(p) for p in missing_paths)
        if args.strict_missing:
            raise FileNotFoundError(msg)
        print(f"WARN: {msg}", file=sys.stderr)

    if not snapshots:
        raise ValueError("No snapshots loaded for requested range")

    export_started_at = _utc_now()
    exported_at_iso = _utc_iso(export_started_at)
    run_id = args.run_id or _run_id_from_export_start(export_started_at)

    price_series_by_symbol = _build_price_series_by_symbol(snapshots)

    rows: list[dict[str, Any]] = []
    setup_map = (("reversal", "reversals"), ("breakout", "breakouts"), ("pullback", "pullbacks"))

    for snapshot in snapshots:
        meta = snapshot.get("meta", {})
        scoring = snapshot.get("scoring", {})
        features = snapshot.get("data", {}).get("features", {})

        t0_date = meta.get("date")
        if not t0_date:
            raise ValueError("Missing non-nullable snapshot.meta.date")

        global_top20 = compute_global_top20(
            list(scoring.get("reversals", []) or []),
            list(scoring.get("breakouts", []) or []),
            list(scoring.get("pullbacks", []) or []),
            config,
        )
        global_rank_by_symbol = {entry.get("symbol"): idx for idx, entry in enumerate(global_top20, start=1)}

        for setup_type, key in setup_map:
            entries = list(scoring.get(key, []) or [])
            for idx, entry in enumerate(entries, start=1):
                symbol = entry.get("symbol")
                if not symbol:
                    raise ValueError("Missing non-nullable scoring_entry.symbol")

                setup_id = entry.get("setup_id") or setup_type
                feat = features.get(symbol, {}) if isinstance(features, dict) else {}

                e2 = evaluate_e2_candidate(
                    t0_date=t0_date,
                    setup_type=setup_type,
                    trade_levels=entry.get("trade_levels", {}) if isinstance(entry, dict) else {},
                    price_series=price_series_by_symbol.get(symbol, {}),
                    params={
                        "T_hold": t_hold,
                        "T_trigger_max": t_trigger_max,
                        "thresholds_pct": thresholds_pct,
                    },
                )

                row = {
                    "type": "candidate_setup",
                    "record_id": f"{run_id}:{t0_date}:{symbol}:{setup_type}:{setup_id}",
                    "run_id": run_id,
                    "t0_date": t0_date,
                    "symbol": symbol,
                    "setup_type": setup_type,
                    "setup_id": setup_id,
                    "snapshot_version": meta.get("version"),
                    "asof_ts_ms": meta.get("asof_ts_ms"),
                    "asof_iso": meta.get("asof_iso"),
                    "market_cap_usd": feat.get("market_cap") if isinstance(feat, dict) else None,
                    "quote_volume_24h_usd": feat.get("quote_volume_24h") if isinstance(feat, dict) else None,
                    "liquidity_grade": feat.get("liquidity_grade") if isinstance(feat, dict) else None,
                    "btc_regime": meta.get("btc_regime"),
                    "score": _score_from_entry(entry),
                    "setup_rank": idx,
                    "global_rank": global_rank_by_symbol.get(symbol),
                    "reason": e2.get("reason"),
                    "t_trigger_date": e2.get("t_trigger_date"),
                    "t_trigger_day_offset": e2.get("t_trigger_day_offset"),
                    "entry_price": e2.get("entry_price"),
                    "hit_10": e2.get("hit_10"),
                    "hit_20": e2.get("hit_20"),
                    "hits": e2.get("hits"),
                    "mfe_pct": e2.get("mfe_pct"),
                    "mae_pct": e2.get("mae_pct"),
                }

                required_non_nullable = [
                    "snapshot_version",
                    "asof_ts_ms",
                    "asof_iso",
                    "score",
                    "reason",
                ]
                for required in required_non_nullable:
                    if row.get(required) is None:
                        raise ValueError(f"Missing non-nullable field: {required}")

                rows.append(row)

    rows.sort(key=lambda row: (row["t0_date"], row["setup_type"], row["setup_rank"], row["symbol"]))

    meta_record = {
        "type": "meta",
        "run_id": run_id,
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
        "exported_at_iso": exported_at_iso,
        "export_started_at_ts_ms": int(export_started_at.timestamp() * 1000),
        "export_run_id": run_id,
        "source_snapshot_count": len(snapshots),
        "source_snapshot_dates": [snapshot.get("meta", {}).get("date") for snapshot in snapshots],
        "thresholds_pct": thresholds_pct,
        "T_hold": t_hold,
        "T_trigger_max": t_trigger_max,
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "notes": None,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"eval_{run_id}.jsonl"

    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(meta_record, ensure_ascii=False, separators=(",", ":")) + "\n")
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")

    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export E2 evaluation dataset JSONL from snapshot history")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--run-id", dest="run_id", default=None, help="Optional run_id override")
    parser.add_argument("--strict-missing", action="store_true", help="Fail on missing snapshot files")
    parser.add_argument("--config", default="config/config.yml", help="Path to scanner config")
    parser.add_argument("--snapshots-dir", default=None, help="Override snapshots history directory")
    parser.add_argument("--output-dir", default="datasets/eval", help="Output directory")
    parser.add_argument("--thresholds-pct", nargs="*", type=float, default=None, help="Optional threshold list")
    parser.add_argument("--t-hold", type=int, default=None)
    parser.add_argument("--t-trigger-max", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        out_path = export_dataset(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### `scanner/tools/backfill_btc_regime.py`

**SHA256:** `07a2248809e76593748dbf9641d7e58a1ea61d2ba1b6c0b9bdb9efeb50495112`

```python
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from scanner.config import load_config
from scanner.pipeline.regime import compute_btc_regime_from_1d_features
from scanner.pipeline.snapshot import SnapshotManager


@dataclass(frozen=True)
class BackfillStats:
    scanned: int = 0
    updated: int = 0
    skipped_existing: int = 0
    missing: int = 0


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _load_snapshot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid snapshot structure: {path}")
    return payload


def _ensure_minimum_version(meta: dict[str, Any]) -> bool:
    version = meta.get("version")
    if version in (None, "", "1.0"):
        meta["version"] = "1.1"
        return True
    return False


def _extract_btc_features_1d(snapshot: dict[str, Any]) -> dict[str, Any]:
    features = snapshot.get("data", {}).get("features", {})
    btc_features_1d = {}
    if isinstance(features, dict):
        btc = features.get("BTCUSDT", {})
        if isinstance(btc, dict):
            maybe_1d = btc.get("1d", {})
            if isinstance(maybe_1d, dict):
                btc_features_1d = maybe_1d
    return btc_features_1d


def _compute_regime(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    btc_features_1d = _extract_btc_features_1d(snapshot)
    if not btc_features_1d:
        return None
    return compute_btc_regime_from_1d_features(btc_features_1d)


def _resolve_snapshots_dir(args: argparse.Namespace) -> Path:
    if args.snapshots_dir:
        return Path(args.snapshots_dir)
    return SnapshotManager.resolve_history_dir(load_config(args.config))


def _preflight_missing_paths(start: date, end: date, snapshots_dir: Path) -> list[Path]:
    return [snapshots_dir / f"{day.isoformat()}.json" for day in _daterange(start, end) if not (snapshots_dir / f"{day.isoformat()}.json").exists()]


def backfill(args: argparse.Namespace) -> BackfillStats:
    start = _parse_date(args.from_date)
    end = _parse_date(args.to_date)
    if end < start:
        raise ValueError("--to must be >= --from")

    snapshots_dir = _resolve_snapshots_dir(args)

    stats = BackfillStats()
    missing_paths: list[Path] = []

    if args.strict_missing:
        missing_paths = _preflight_missing_paths(start, end, snapshots_dir)
        if missing_paths:
            msg = f"Missing {len(missing_paths)} snapshot file(s): " + ", ".join(str(p) for p in missing_paths)
            raise FileNotFoundError(msg)

    for day in _daterange(start, end):
        stats = BackfillStats(
            scanned=stats.scanned + 1,
            updated=stats.updated,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )
        path = snapshots_dir / f"{day.isoformat()}.json"
        if not path.exists():
            missing_paths.append(path)
            stats = BackfillStats(
                scanned=stats.scanned,
                updated=stats.updated,
                skipped_existing=stats.skipped_existing,
                missing=stats.missing + 1,
            )
            continue

        snapshot = _load_snapshot(path)
        meta = snapshot.setdefault("meta", {})
        if not isinstance(meta, dict):
            raise ValueError(f"Invalid snapshot.meta structure: {path}")

        if meta.get("btc_regime") is not None:
            changed = _ensure_minimum_version(meta)
            if changed and not args.dry_run:
                with path.open("w", encoding="utf-8") as fh:
                    json.dump(snapshot, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
            stats = BackfillStats(
                scanned=stats.scanned,
                updated=stats.updated + (1 if changed else 0),
                skipped_existing=stats.skipped_existing + (0 if changed else 1),
                missing=stats.missing,
            )
            continue

        regime = _compute_regime(snapshot)
        if regime is None:
            meta["btc_regime"] = None
            meta["btc_regime_status"] = "missing_btc_features"
        else:
            meta["btc_regime"] = regime
            if meta.get("btc_regime_status") == "missing_btc_features":
                meta.pop("btc_regime_status", None)
        _ensure_minimum_version(meta)

        if not args.dry_run:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(snapshot, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

        stats = BackfillStats(
            scanned=stats.scanned,
            updated=stats.updated + 1,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )

    if missing_paths:
        msg = f"Missing {len(missing_paths)} snapshot file(s): " + ", ".join(str(p) for p in missing_paths)
        if args.strict_missing:
            raise FileNotFoundError(msg)
        print(f"WARN: {msg}", file=sys.stderr)

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill meta.btc_regime in snapshot history (missing BTC features => btc_regime=null)")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify files")
    parser.add_argument("--strict-missing", action="store_true", help="Fail if any snapshot is missing")
    parser.add_argument("--config", default="config/config.yml", help="Path to scanner config")
    parser.add_argument("--snapshots-dir", default=None, help="Override snapshots history directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        stats = backfill(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        f"scanned={stats.scanned} updated={stats.updated} "
        f"skipped_existing={stats.skipped_existing} missing={stats.missing}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### `scanner/tools/backfill_snapshots.py`

**SHA256:** `c076e1cea93bfd91dab9c6f6a3f7a18b072e0756357d199fb9656fee7a1a2c6f`

```python
from __future__ import annotations

import argparse
import json
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from scanner.config import ScannerConfig, load_config
from scanner.pipeline.snapshot import SnapshotManager

SYMBOL_CACHE_RE = re.compile(r"^mexc_klines_(?P<symbol>[A-Z0-9]+)_1d\.json$")


@dataclass(frozen=True)
class BackfillStats:
    scanned: int = 0
    created: int = 0
    skipped_existing: int = 0
    missing: int = 0


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _snapshot_base(now: datetime, run_date: str, features: dict[str, dict[str, dict[str, float]]], mode: str, source: str) -> dict[str, Any]:
    asof_ts_ms = int(now.timestamp() * 1000)
    asof_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "meta": {
            "date": run_date,
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "version": "1.1",
            "asof_ts_ms": asof_ts_ms,
            "asof_iso": asof_iso,
            "backfill": True,
            "backfill_mode": mode,
            "backfill_source": source,
        },
        "pipeline": {
            "universe_count": 0,
            "filtered_count": 0,
            "shortlist_count": 0,
            "features_count": len(features),
        },
        "data": {
            "universe": [],
            "filtered": [],
            "shortlist": [],
            "features": features,
        },
        "scoring": {
            "reversals": [],
            "breakouts": [],
            "pullbacks": [],
        },
    }


def _extract_ohlcv_row(path: Path, target_date: str) -> tuple[str, dict[str, float]] | None:
    match = SYMBOL_CACHE_RE.match(path.name)
    if not match:
        return None

    with path.open("r", encoding="utf-8") as fh:
        candles = json.load(fh)

    if not isinstance(candles, list):
        raise ValueError(f"Invalid OHLCV cache format: {path}")

    for row in candles:
        if not isinstance(row, list) or len(row) < 5:
            continue
        try:
            open_time_ms = int(float(row[0]))
            row_date = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc).date().isoformat()
            if row_date != target_date:
                continue
            high = float(row[2])
            low = float(row[3])
            close = float(row[4])
        except (TypeError, ValueError):
            continue
        symbol = match.group("symbol")
        return symbol, {"1d": {"close": close, "high": high, "low": low}}

    return None


def _build_minimal_features(ohlcv_cache_dir: Path, target_date: str) -> dict[str, dict[str, dict[str, float]]]:
    date_dir = ohlcv_cache_dir / target_date
    if not date_dir.exists():
        raise FileNotFoundError(
            f"No local OHLCV cache files found for {target_date} in {date_dir}. "
            "Expected source: data/raw/<YYYY-MM-DD>/mexc_klines_<SYMBOL>_1d.json"
        )

    files = sorted(path for path in date_dir.iterdir() if path.is_file() and SYMBOL_CACHE_RE.match(path.name))
    if not files:
        raise FileNotFoundError(
            f"No local OHLCV cache files found for {target_date} in {date_dir}. "
            "Expected source: data/raw/<YYYY-MM-DD>/mexc_klines_<SYMBOL>_1d.json"
        )

    features: dict[str, dict[str, dict[str, float]]] = {}
    for file_path in files:
        extracted = _extract_ohlcv_row(file_path, target_date)
        if extracted is None:
            continue
        symbol, payload = extracted
        features[symbol] = payload

    if not features:
        raise FileNotFoundError(
            f"No OHLCV candles for {target_date} found in local cache files under {date_dir}. "
            "Tool requires local 1d candles for that date; no API fallback is allowed."
        )

    return dict(sorted(features.items(), key=lambda item: item[0]))


def _run_full_mode(target_day: date, config_path: str, snapshots_dir: Path, dry_run: bool) -> None:
    if dry_run:
        return

    from scanner.pipeline import run_pipeline

    config = load_config(config_path)
    raw_copy = dict(config.raw)
    snapshots_cfg = dict(raw_copy.get("snapshots", {}))
    snapshots_cfg["history_dir"] = str(snapshots_dir)
    raw_copy["snapshots"] = snapshots_cfg
    patched_config = ScannerConfig(raw=raw_copy)

    with _patched_full_mode_time_sources(target_day):
        run_pipeline(patched_config)


def _mark_full_backfill(snapshot_path: Path) -> None:
    with snapshot_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if not isinstance(payload, dict):
        raise ValueError(f"Invalid snapshot structure in full mode output: {snapshot_path}")

    meta = payload.setdefault("meta", {})
    if not isinstance(meta, dict):
        raise ValueError(f"Invalid snapshot.meta structure in full mode output: {snapshot_path}")

    meta["backfill"] = True
    meta["backfill_mode"] = "full"
    meta["backfill_source"] = "pipeline"

    with snapshot_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _resolve_snapshots_dir(args: argparse.Namespace) -> Path:
    if args.snapshots_dir:
        return Path(args.snapshots_dir)
    return SnapshotManager.resolve_history_dir(load_config(args.config))


def _preflight_requirements(args: argparse.Namespace, start: date, end: date, snapshots_dir: Path, ohlcv_cache_dir: Path) -> None:
    errors: list[str] = []
    for day in _daterange(start, end):
        run_date = day.isoformat()
        snapshot_path = snapshots_dir / f"{run_date}.json"
        if snapshot_path.exists():
            if args.strict_existing:
                errors.append(f"Snapshot already exists for {run_date}: {snapshot_path}")
            continue

        if args.mode == "minimal":
            try:
                _build_minimal_features(ohlcv_cache_dir=ohlcv_cache_dir, target_date=run_date)
            except Exception as exc:  # preflight aggregation
                errors.append(f"{run_date}: {exc}")
        else:
            try:
                _validate_full_mode_prerequisites(target_day=day, config_path=args.config, ohlcv_cache_dir=ohlcv_cache_dir)
            except Exception as exc:  # preflight aggregation
                errors.append(f"{run_date}: {exc}")

    if errors:
        raise FileNotFoundError("Strict preflight failed: " + " | ".join(errors))


def _resolve_cache_date(target_day: date) -> str:
    return target_day.isoformat()


def _validate_full_mode_prerequisites(target_day: date, config_path: str, ohlcv_cache_dir: Path) -> None:
    """Validate deterministic full-mode prerequisites for one target date.

    Full-mode backfill is expected to replay a historical day from local inputs.
    In strict mode we fail early unless all required local artifacts are present.
    """

    config = load_config(config_path)
    run_mode = str(config.raw.get("general", {}).get("run_mode", "")).lower()
    if run_mode != "standard":
        raise ValueError(
            "Full-mode strict backfill requires config.general.run_mode='standard' "
            f"(current: {run_mode or 'unset'})."
        )

    # Full mode depends on complete local OHLCV for the target day.
    _build_minimal_features(ohlcv_cache_dir=ohlcv_cache_dir, target_date=target_day.isoformat())


@contextmanager
def _patched_full_mode_time_sources(target_day: date):
    from scanner import pipeline as pipeline_module
    from scanner.utils import io_utils, time_utils

    fake_now = datetime(target_day.year, target_day.month, target_day.day, 0, 0, 0, tzinfo=timezone.utc)

    original_pipeline_utc_now = pipeline_module.utc_now
    original_pipeline_timestamp_to_ms = pipeline_module.timestamp_to_ms
    original_time_utils_utc_now = time_utils.utc_now
    original_time_utils_utc_date = time_utils.utc_date
    original_time_utils_utc_timestamp = time_utils.utc_timestamp
    original_io_get_cache_path = io_utils.get_cache_path

    def _fake_utc_now() -> datetime:
        return fake_now

    def _fake_utc_date() -> str:
        return _resolve_cache_date(target_day)

    def _fake_utc_timestamp() -> str:
        return fake_now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _fake_timestamp_to_ms(dt: datetime) -> int:
        return int(dt.timestamp() * 1000)

    def _fake_get_cache_path(cache_type: str, date: str | None = None) -> Path:
        return original_io_get_cache_path(cache_type, date or _resolve_cache_date(target_day))

    pipeline_module.utc_now = _fake_utc_now
    pipeline_module.timestamp_to_ms = _fake_timestamp_to_ms
    time_utils.utc_now = _fake_utc_now
    time_utils.utc_date = _fake_utc_date
    time_utils.utc_timestamp = _fake_utc_timestamp
    io_utils.get_cache_path = _fake_get_cache_path
    try:
        yield
    finally:
        pipeline_module.utc_now = original_pipeline_utc_now
        pipeline_module.timestamp_to_ms = original_pipeline_timestamp_to_ms
        time_utils.utc_now = original_time_utils_utc_now
        time_utils.utc_date = original_time_utils_utc_date
        time_utils.utc_timestamp = original_time_utils_utc_timestamp
        io_utils.get_cache_path = original_io_get_cache_path


def backfill(args: argparse.Namespace) -> BackfillStats:
    start = _parse_date(args.from_date)
    end = _parse_date(args.to_date)
    if end < start:
        raise ValueError("--to must be >= --from")

    snapshots_dir = _resolve_snapshots_dir(args)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    ohlcv_cache_dir = Path(args.ohlcv_cache_dir)

    stats = BackfillStats()

    if args.strict_missing:
        _preflight_requirements(args=args, start=start, end=end, snapshots_dir=snapshots_dir, ohlcv_cache_dir=ohlcv_cache_dir)

    for day in _daterange(start, end):
        run_date = day.isoformat()
        snapshot_path = snapshots_dir / f"{run_date}.json"

        stats = BackfillStats(
            scanned=stats.scanned + 1,
            created=stats.created,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )

        if snapshot_path.exists():
            if args.strict_existing:
                raise FileExistsError(f"Snapshot already exists for {run_date}: {snapshot_path}")
            stats = BackfillStats(
                scanned=stats.scanned,
                created=stats.created,
                skipped_existing=stats.skipped_existing + 1,
                missing=stats.missing,
            )
            continue


        if args.mode == "minimal":
            features = _build_minimal_features(ohlcv_cache_dir=ohlcv_cache_dir, target_date=run_date)
            payload = _snapshot_base(
                now=datetime.now(timezone.utc),
                run_date=run_date,
                features=features,
                mode="minimal",
                source="ohlcv_only",
            )
            if not args.dry_run:
                with snapshot_path.open("w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
        else:
            _run_full_mode(target_day=day, config_path=args.config, snapshots_dir=snapshots_dir, dry_run=args.dry_run)
            if not args.dry_run:
                if not snapshot_path.exists():
                    raise FileNotFoundError(
                        f"Full mode did not produce expected snapshot for {run_date} at {snapshot_path}. "
                        "Historical as-of backfill is best effort and may require local caches/config."
                    )
                _mark_full_backfill(snapshot_path)

        stats = BackfillStats(
            scanned=stats.scanned,
            created=stats.created + 1,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill missing snapshot files by date range")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--mode", choices=["minimal", "full"], default="minimal")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser.add_argument("--strict-existing", action="store_true", help="Fail if any target date already has a snapshot")
    parser.add_argument("--strict-missing", action="store_true", help="Preflight dates and fail atomically before writes if any target snapshot is missing")
    parser.add_argument("--config", default="config/config.yml", help="Path to scanner config (used for snapshots dir and full mode)")
    parser.add_argument("--snapshots-dir", default=None, help="Override snapshots history directory")
    parser.add_argument(
        "--ohlcv-cache-dir",
        default="data/raw",
        help="Root directory for local OHLCV cache (expected: <root>/<YYYY-MM-DD>/mexc_klines_<SYMBOL>_1d.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        stats = backfill(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"mode={args.mode} scanned={stats.scanned} created={stats.created} skipped_existing={stats.skipped_existing} missing={stats.missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### `scanner/tools/validate_features.py`

**SHA256:** `be0e041fff94015cfdd32acd4fbcded4dd38daa693bce1f4d3e55fceb701f359`

```python
"""Validate scanner report feature/scoring plausibility."""

import json
import os
from typing import Any, Dict, List


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _error(
    path: str,
    code: str,
    msg: str,
    got: Any = None,
    expected: str | None = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {"path": path, "code": code, "msg": msg}
    if got is not None:
        entry["got"] = got
    if expected is not None:
        entry["expected"] = expected
    return entry


def _emit(ok: bool, errors: List[Dict[str, Any]]) -> int:
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


def validate_features(report_path: str) -> int:
    """
    Validate report scoring structure and numeric ranges.

    Checks:
    - score and raw_score in [0, 100]
    - each component in [0, 100]
    - penalty_multiplier in (0, 1]

    Returns process-style status code:
    - 0 if valid
    - 1 if report missing/invalid/anomalies found
    """

    if not os.path.exists(report_path):
        return _emit(
            False,
            [_error("report", "FILE_NOT_FOUND", "Report file not found.", got=report_path)],
        )

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        return _emit(
            False,
            [_error("report", "INVALID_JSON", "Report is not valid JSON.", got=str(exc))],
        )

    if "setups" in data:
        section_key = "setups"
    elif "data" in data:
        section_key = "data"
    elif "results" in data:
        section_key = "results"
    else:
        return _emit(
            False,
            [
                _error(
                    "report",
                    "MISSING_SECTION",
                    "Report must contain 'setups', 'data' or 'results' section.",
                )
            ],
        )

    results = data[section_key]
    if not results:
        return _emit(True, [])

    anomalies: List[Dict[str, Any]] = []

    for setup_type, setups in results.items():
        for idx, s in enumerate(setups):
            setup_path = f"{section_key}.{setup_type}[{idx}]"

            for required_key in ("score", "raw_score", "penalty_multiplier", "components"):
                if required_key not in s:
                    anomalies.append(
                        _error(
                            f"{setup_path}.{required_key}",
                            "MISSING_FIELD",
                            f"Required field '{required_key}' is missing.",
                            expected="present",
                        )
                    )

            for scalar_key in ("score", "raw_score"):
                if scalar_key in s:
                    val = s.get(scalar_key)
                    if not _is_number(val) or not (0 <= float(val) <= 100):
                        anomalies.append(
                            _error(
                                f"{setup_path}.{scalar_key}",
                                "RANGE",
                                f"{scalar_key} must be a number in [0,100].",
                                got=val,
                                expected="[0,100]",
                            )
                        )

            if "penalty_multiplier" in s:
                pm = s.get("penalty_multiplier")
                if not _is_number(pm) or not (0 < float(pm) <= 1):
                    anomalies.append(
                        _error(
                            f"{setup_path}.penalty_multiplier",
                            "RANGE",
                            "penalty_multiplier must be a number in (0,1].",
                            got=pm,
                            expected="(0,1]",
                        )
                    )

            comps = s.get("components", {})
            if not isinstance(comps, dict):
                anomalies.append(
                    _error(
                        f"{setup_path}.components",
                        "TYPE",
                        "components must be an object/dict.",
                        got=comps,
                        expected="dict",
                    )
                )
                continue

            for key, value in comps.items():
                if not _is_number(value) or not (0 <= float(value) <= 100):
                    anomalies.append(
                        _error(
                            f"{setup_path}.components.{key}",
                            "RANGE",
                            f"Component '{key}' must be a number in [0,100].",
                            got=value,
                            expected="[0,100]",
                        )
                    )

    if anomalies:
        return _emit(False, anomalies)

    return _emit(True, [])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "ok": False,
                    "errors": [
                        {
                            "path": "cli",
                            "code": "MISSING_ARGUMENT",
                            "msg": "Please provide report path, e.g. python -m scanner.tools.validate_features reports/2026-01-22.json",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    report_path = sys.argv[1]
    sys.exit(validate_features(report_path))

```

### `scanner/pipeline/scoring/breakout.py`

**SHA256:** `d89089e19f3ecd4368bf93e58d51f15ba41a67f5344269515c3726b93feeb007`

```python
"""Breakout scoring."""

import logging
import math
from typing import Dict, Any, List, Optional

from scanner.pipeline.scoring.weights import load_component_weights
from scanner.pipeline.scoring.trade_levels import breakout_trade_levels, compute_phase1_risk_fields
from scanner.pipeline.scoring.decision_inputs import standardize_entry_readiness, standardize_invalidation_anchor

logger = logging.getLogger(__name__)


class BreakoutScorer:
    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        scoring_cfg = root.get("scoring", {}).get("breakout", {})

        self.min_breakout_pct = float(scoring_cfg.get("min_breakout_pct", 2.0))
        self.ideal_breakout_pct = float(scoring_cfg.get("ideal_breakout_pct", 5.0))
        self.max_breakout_pct = float(scoring_cfg.get("max_breakout_pct", 20.0))
        breakout_curve = scoring_cfg.get("breakout_curve", {})
        self.breakout_floor_pct = float(breakout_curve.get("floor_pct", -5.0))
        self.breakout_fresh_cap_pct = float(breakout_curve.get("fresh_cap_pct", 1.0))
        self.breakout_overextended_cap_pct = float(breakout_curve.get("overextended_cap_pct", 3.0))

        self.min_volume_spike = float(scoring_cfg.get("min_volume_spike", 1.5))
        self.ideal_volume_spike = float(scoring_cfg.get("ideal_volume_spike", 2.5))

        momentum_cfg = scoring_cfg.get("momentum", {})
        self.momentum_divisor = float(momentum_cfg.get("r7_divisor", 10.0))

        penalties_cfg = scoring_cfg.get("penalties", {})
        self.overextension_factor = float(penalties_cfg.get("overextension_factor", 0.6))
        self.max_overextension_ema20_percent = float(
            penalties_cfg.get("max_overextension_ema20_percent", scoring_cfg.get("max_overextension_ema20_percent", 25.0))
        )
        self.low_liquidity_threshold = float(penalties_cfg.get("low_liquidity_threshold", 500_000))
        self.low_liquidity_factor = float(penalties_cfg.get("low_liquidity_factor", 0.8))

        default_weights = {"breakout": 0.35, "volume": 0.30, "trend": 0.20, "momentum": 0.15}
        self.weights = load_component_weights(
            scoring_cfg=scoring_cfg,
            section_name="breakout",
            default_weights=default_weights,
            aliases={
                "breakout": "price_break",
                "volume": "volume_confirmation",
                "trend": "volatility_context",
            },
)
    @staticmethod
    def _closed_candle_count(features: Dict[str, Any], timeframe: str) -> Optional[int]:
        meta = features.get("meta", {})
        idx_map = meta.get("last_closed_idx", {}) if isinstance(meta, dict) else {}
        idx = idx_map.get(timeframe)
        if isinstance(idx, int) and idx >= 0:
            return idx + 1
        return None

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float, volume_source_used: str = "mexc") -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})
        invalidation_anchor = self._resolve_invalidation_anchor(f1d)

        breakout_score = self._score_breakout(f1d)
        volume_score = self._score_volume(f1d, f4h)
        trend_score = self._score_trend(f1d)
        momentum_score = self._score_momentum(f1d)

        raw_score = (
            breakout_score * self.weights["breakout"]
            + volume_score * self.weights["volume"]
            + trend_score * self.weights["trend"]
            + momentum_score * self.weights["momentum"]
        )

        penalties = []
        flags = []

        breakout_dist = f1d.get("breakout_dist_20", 0)
        if breakout_dist is not None and breakout_dist > self.breakout_overextended_cap_pct:
            flags.append("overextended_breakout_zone")

        dist_ema20 = f1d.get("dist_ema20_pct")
        if dist_ema20 is not None and dist_ema20 > self.max_overextension_ema20_percent:
            penalties.append(("overextension", self.overextension_factor))
            flags.append("overextended")

        if quote_volume_24h < self.low_liquidity_threshold:
            penalties.append(("low_liquidity", self.low_liquidity_factor))
            flags.append("low_liquidity")

        soft_penalties = features.get("soft_penalties", {}) if isinstance(features, dict) else {}
        if isinstance(soft_penalties, dict):
            for penalty_name, factor in soft_penalties.items():
                try:
                    penalties.append((str(penalty_name), float(factor)))
                except (TypeError, ValueError):
                    continue

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor
        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(breakout_score, volume_score, trend_score, momentum_score, f1d, f4h, flags, volume_source_used)
        breakout_v2 = self._resolve_breakout_v2_fields(f1d)

        return {
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 6),
            "penalty_multiplier": round(penalty_multiplier, 6),
            "final_score": round(final_score, 6),
            "components": {
                "breakout": round(breakout_score, 2),
                "volume": round(volume_score, 2),
                "trend": round(trend_score, 2),
                "momentum": round(momentum_score, 2),
            },
            "penalties": {name: factor for name, factor in penalties},
            "flags": flags,
            "reasons": reasons,
            "volume_source_used": volume_source_used,
            **breakout_v2,
            **invalidation_anchor,
        }


    def _resolve_breakout_v2_fields(self, f1d: Dict[str, Any]) -> Dict[str, Any]:
        breakout_dist = f1d.get("breakout_dist_20")
        try:
            numeric_dist = float(breakout_dist)
        except (TypeError, ValueError):
            return {
                "breakout_confirmed": None,
                **standardize_entry_readiness(
                    entry_ready=False,
                    reason_keys=["breakout_not_evaluable"],
                    setup_subtype="fresh_breakout",
                ),
            }

        if not math.isfinite(numeric_dist):
            return {
                "breakout_confirmed": None,
                **standardize_entry_readiness(
                    entry_ready=False,
                    reason_keys=["breakout_not_evaluable"],
                    setup_subtype="fresh_breakout",
                ),
            }

        breakout_confirmed = numeric_dist >= 0
        setup_subtype = "confirmed_breakout" if breakout_confirmed else "fresh_breakout"
        return {
            "breakout_confirmed": breakout_confirmed,
            **standardize_entry_readiness(
                entry_ready=breakout_confirmed,
                reason_keys=["breakout_not_confirmed"],
                setup_subtype=setup_subtype,
            ),
        }

    def _resolve_invalidation_anchor(self, f1d: Dict[str, Any]) -> Dict[str, Any]:
        close_1d = f1d.get("close")
        breakout_dist = f1d.get("breakout_dist_20")
        try:
            close_numeric = float(close_1d)
            breakout_dist_numeric = float(breakout_dist)
        except (TypeError, ValueError):
            return standardize_invalidation_anchor(anchor_price=None, anchor_type=None, derivable=False)

        if not math.isfinite(close_numeric) or not math.isfinite(breakout_dist_numeric) or close_numeric <= 0:
            return standardize_invalidation_anchor(anchor_price=None, anchor_type=None, derivable=False)

        denominator = 1.0 + breakout_dist_numeric / 100.0
        if denominator <= 0:
            return standardize_invalidation_anchor(anchor_price=None, anchor_type=None, derivable=False)

        anchor = close_numeric / denominator
        return standardize_invalidation_anchor(anchor_price=anchor, anchor_type="breakout_level", derivable=True)

    def _score_breakout(self, f1d: Dict[str, Any]) -> float:
        dist = f1d.get("breakout_dist_20")
        if dist is None:
            return 0.0
        if dist <= self.breakout_floor_pct:
            return 0.0
        if self.breakout_floor_pct < dist < 0:
            return 30.0 * (dist - self.breakout_floor_pct) / (0 - self.breakout_floor_pct)
        if 0 <= dist < self.min_breakout_pct:
            if self.min_breakout_pct <= 0:
                return 70.0
            return 30.0 + 40.0 * (dist / self.min_breakout_pct)
        if self.min_breakout_pct <= dist <= self.ideal_breakout_pct:
            denom = self.ideal_breakout_pct - self.min_breakout_pct
            if denom <= 0:
                return 100.0
            return 70.0 + 30.0 * ((dist - self.min_breakout_pct) / denom)
        if self.ideal_breakout_pct < dist <= self.max_breakout_pct:
            denom = self.max_breakout_pct - self.ideal_breakout_pct
            if denom <= 0:
                return 0.0
            return 100.0 * (1.0 - ((dist - self.ideal_breakout_pct) / denom))
        return 0.0

    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        max_spike = max(spike_1d, spike_4h)
        if max_spike < self.min_volume_spike:
            return 0.0
        if max_spike >= self.ideal_volume_spike:
            return 100.0
        ratio = (max_spike - self.min_volume_spike) / (self.ideal_volume_spike - self.min_volume_spike)
        return ratio * 100.0

    def _score_trend(self, f1d: Dict[str, Any]) -> float:
        score = 0.0
        dist_ema20 = f1d.get("dist_ema20_pct")
        dist_ema50 = f1d.get("dist_ema50_pct")

        if dist_ema20 is not None and dist_ema20 > 0:
            score += 40
            if dist_ema20 > 5:
                score += 10
        if dist_ema50 is not None and dist_ema50 > 0:
            score += 40
            if dist_ema50 > 5:
                score += 10
        return min(score, 100.0)

    def _score_momentum(self, f1d: Dict[str, Any]) -> float:
        r7 = f1d.get("r_7")
        if r7 is None or self.momentum_divisor <= 0:
            return 0.0
        return max(0.0, min(100.0, (float(r7) / self.momentum_divisor) * 100.0))

    def _generate_reasons(self, breakout_score: float, volume_score: float, trend_score: float, momentum_score: float,
                          f1d: Dict[str, Any], f4h: Dict[str, Any], flags: List[str], volume_source_used: str) -> List[str]:
        reasons = [f"Volume source used: {volume_source_used}"]
        dist = f1d.get("breakout_dist_20", 0)
        if breakout_score > 70:
            reasons.append(f"Strong breakout ({dist:.1f}% above 20d high)")
        elif breakout_score > 30:
            reasons.append(f"Moderate breakout ({dist:.1f}% above high)")
        elif dist > 0:
            reasons.append(f"Early breakout ({dist:.1f}% above high)")
        else:
            reasons.append("No breakout (below recent high)")

        spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        vol_spike = max(spike_1d, spike_4h)
        if volume_score > 70:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif volume_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")
        else:
            reasons.append("Low volume (no confirmation)")

        if trend_score > 70:
            reasons.append("In uptrend (above EMAs)")
        elif trend_score > 30:
            reasons.append("Neutral trend")
        else:
            reasons.append("In downtrend (below EMAs)")

        if "overextended_breakout_zone" in flags:
            reasons.append(f"⚠️ Breakout in overextended zone ({dist:.1f}% above high)")
        if "overextended" in flags:
            reasons.append("⚠️ Overextended vs EMA20")
        if "low_liquidity" in flags:
            reasons.append("⚠️ Low liquidity")
        return reasons


def score_breakouts(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any], volume_source_map: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    scorer = BreakoutScorer(config)
    results = []
    root = config.raw if hasattr(config, "raw") else config
    min_1d = int(root.get("setup_validation", {}).get("min_history_breakout_1d", 30))
    min_4h = int(root.get("setup_validation", {}).get("min_history_breakout_4h", 50))
    trade_levels_cfg = root.get("trade_levels", {}) if isinstance(root, dict) else {}
    target_multipliers = [float(x) for x in trade_levels_cfg.get("target_atr_multipliers", [1.0, 2.0, 3.0])]
    for symbol, features in features_data.items():
        candles_1d = scorer._closed_candle_count(features, "1d")
        candles_4h = scorer._closed_candle_count(features, "4h")
        if candles_1d is None or candles_4h is None or candles_1d < min_1d or candles_4h < min_4h:
            logger.debug(
                "Skipping breakout for %s due to insufficient history (1d=%s/%s, 4h=%s/%s)",
                symbol,
                candles_1d,
                min_1d,
                candles_4h,
                min_4h,
            )
            continue
        volume = volumes.get(symbol, 0)
        try:
            volume_source_used = (volume_source_map or {}).get(symbol, "mexc")
            score_result = scorer.score(symbol, features, volume, volume_source_used=volume_source_used)
            trade_levels = breakout_trade_levels(features, target_multipliers)
            risk_fields = compute_phase1_risk_fields("breakout", trade_levels, root)
            results.append(
                {
                    "symbol": symbol,
                    "price_usdt": features.get("price_usdt"),
                    "coin_name": features.get("coin_name"),
                    "market_cap": features.get("market_cap"),
                    "quote_volume_24h": features.get("quote_volume_24h"),
                    "proxy_liquidity_score": features.get("proxy_liquidity_score"),
                    "spread_bps": features.get("spread_bps"),
                    "slippage_bps": features.get("slippage_bps"),
                    "liquidity_grade": features.get("liquidity_grade"),
                    "liquidity_insufficient": features.get("liquidity_insufficient"),
                    "score": score_result["score"],
                    "raw_score": score_result["raw_score"],
                    "penalty_multiplier": score_result["penalty_multiplier"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "risk_flags": features.get("risk_flags", []),
                    "reasons": score_result["reasons"],
                    "volume_source_used": score_result["volume_source_used"],
                    "entry_ready": score_result["entry_ready"],
                    "entry_readiness_reasons": score_result["entry_readiness_reasons"],
                    "setup_subtype": score_result["setup_subtype"],
                    "breakout_confirmed": score_result["breakout_confirmed"],
                    "invalidation_anchor_price": score_result["invalidation_anchor_price"],
                    "invalidation_anchor_type": score_result["invalidation_anchor_type"],
                    "invalidation_derivable": score_result["invalidation_derivable"],
                    "analysis": {"trade_levels": trade_levels},
                    **risk_fields,
                    "discovery": features.get("discovery", False),
                    "discovery_age_days": features.get("discovery_age_days"),
                    "discovery_source": features.get("discovery_source"),
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

```

### `scanner/pipeline/scoring/trade_levels.py`

**SHA256:** `92531a41bd0033cc50ff18772ff119b31081db06292807c4202d39c851eb3403`

```python
"""Deterministic trade-level helpers (output-only, no scoring impact)."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        parsed = float(value)
        if not math.isfinite(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def _atr_absolute(tf_features: Dict[str, Any]) -> Optional[float]:
    atr_pct = _to_float(tf_features.get("atr_pct"))
    close = _to_float(tf_features.get("close"))
    if atr_pct is None or close is None:
        return None
    return (atr_pct / 100.0) * close


def _targets(base: Optional[float], atr: Optional[float], multipliers: List[float]) -> List[Optional[float]]:
    if base is None or atr is None:
        return [None for _ in multipliers]
    return [base + (k * atr) for k in multipliers]


def breakout_trade_levels(features: Dict[str, Any], multipliers: List[float]) -> Dict[str, Any]:
    f1d = features.get("1d", {})
    close_1d = _to_float(f1d.get("close"))
    breakout_dist_20 = _to_float(f1d.get("breakout_dist_20"))

    breakout_level_20: Optional[float] = None
    if close_1d is not None and breakout_dist_20 is not None and (100.0 + breakout_dist_20) != 0.0:
        breakout_level_20 = close_1d / (1.0 + breakout_dist_20 / 100.0)

    ema20_1d = _to_float(f1d.get("ema_20"))
    invalidation = min(v for v in [breakout_level_20, ema20_1d] if v is not None) if any(
        v is not None for v in [breakout_level_20, ema20_1d]
    ) else None

    atr_1d = _atr_absolute(f1d)
    return {
        "entry_trigger": breakout_level_20,
        "breakout_level_20": breakout_level_20,
        "invalidation": invalidation,
        "targets": _targets(breakout_level_20, atr_1d, multipliers),
        "atr_value": atr_1d,
    }


def pullback_trade_levels(features: Dict[str, Any], multipliers: List[float], pb_tol_pct: float) -> Dict[str, Any]:
    f4h = features.get("4h", {})
    ema20_4h = _to_float(f4h.get("ema_20"))
    ema50_4h = _to_float(f4h.get("ema_50"))

    zone = {
        "center": ema20_4h,
        "lower": None if ema20_4h is None else ema20_4h * (1.0 - pb_tol_pct / 100.0),
        "upper": None if ema20_4h is None else ema20_4h * (1.0 + pb_tol_pct / 100.0),
        "tolerance_pct": pb_tol_pct,
    }
    atr_4h = _atr_absolute(f4h)
    return {
        "entry_zone": zone,
        "invalidation": ema50_4h,
        "targets": _targets(ema20_4h, atr_4h, multipliers),
        "atr_value": atr_4h,
    }


def reversal_trade_levels(features: Dict[str, Any], multipliers: List[float]) -> Dict[str, Any]:
    f1d = features.get("1d", {})
    ema20_1d = _to_float(f1d.get("ema_20"))
    base_low = _to_float(f1d.get("base_low"))
    atr_1d = _atr_absolute(f1d)
    return {
        "entry_trigger": ema20_1d,
        "invalidation": base_low,
        "targets": _targets(ema20_1d, atr_1d, multipliers),
        "atr_value": atr_1d,
    }


def _risk_cfg(root_config: Dict[str, Any]) -> Dict[str, float]:
    risk_cfg = root_config.get("risk", {}) if isinstance(root_config, dict) else {}
    return {
        "atr_multiple": float(risk_cfg.get("atr_multiple", 2.0)),
        "min_stop_distance_pct": float(risk_cfg.get("min_stop_distance_pct", 4.0)),
        "max_stop_distance_pct": float(risk_cfg.get("max_stop_distance_pct", 12.0)),
        "min_rr_to_tp10": float(risk_cfg.get("min_rr_to_tp10", 1.3)),
    }


def _planned_entry_price(setup_type: str, trade_levels: Dict[str, Any]) -> Optional[float]:
    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone") if isinstance(trade_levels.get("entry_zone"), dict) else {}
        return _to_float(zone.get("center"))
    return _to_float(trade_levels.get("entry_trigger"))


def compute_phase1_risk_fields(setup_type: str, trade_levels: Dict[str, Any], root_config: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _risk_cfg(root_config)
    entry_price = _planned_entry_price(setup_type, trade_levels)
    atr_value = _to_float(trade_levels.get("atr_value"))

    result: Dict[str, Any] = {
        "stop_price_initial": None,
        "risk_pct_to_stop": None,
        "rr_to_tp10": None,
        "rr_to_tp20": None,
        "risk_acceptable": None,
    }

    if entry_price is None or atr_value is None:
        return result
    if entry_price <= 0 or atr_value <= 0:
        return result

    stop_price_initial = entry_price - (cfg["atr_multiple"] * atr_value)
    if stop_price_initial >= entry_price:
        return result

    risk_abs = entry_price - stop_price_initial
    if risk_abs <= 0:
        return result

    risk_pct_to_stop = (risk_abs / entry_price) * 100.0

    targets = trade_levels.get("targets") if isinstance(trade_levels.get("targets"), list) else []
    tp10 = _to_float(targets[0]) if len(targets) >= 1 else None
    tp20 = _to_float(targets[1]) if len(targets) >= 2 else None
    if tp10 is None or tp20 is None:
        return result
    if tp10 <= entry_price or tp20 <= entry_price:
        return result

    rr_to_tp10 = (tp10 - entry_price) / risk_abs
    rr_to_tp20 = (tp20 - entry_price) / risk_abs

    risk_acceptable = (
        cfg["min_stop_distance_pct"] <= risk_pct_to_stop <= cfg["max_stop_distance_pct"]
        and rr_to_tp10 is not None
        and rr_to_tp10 >= cfg["min_rr_to_tp10"]
    )

    result.update(
        {
            "stop_price_initial": stop_price_initial,
            "risk_pct_to_stop": risk_pct_to_stop,
            "rr_to_tp10": rr_to_tp10,
            "rr_to_tp20": rr_to_tp20,
            "risk_acceptable": risk_acceptable,
        }
    )
    return result

```

### `scanner/pipeline/scoring/weights.py`

**SHA256:** `06fe401a509b1dbfbdadaaa5243ba31d81b8d60168d473a5b352d2d2042eed4d`

```python
"""Shared scorer weight loading helpers."""

import logging
from typing import Any, Dict


logger = logging.getLogger(__name__)

_WEIGHT_SUM_TOLERANCE = 1e-6


def load_component_weights(
    *,
    scoring_cfg: Dict[str, Any],
    section_name: str,
    default_weights: Dict[str, float],
    aliases: Dict[str, str],
) -> Dict[str, float]:
    """Load scorer component weights with deterministic compatibility behavior.

    Modes:
    - compat (default): canonical keys may be mixed with legacy aliases; missing keys are
      filled from defaults; no normalization is applied.
    - strict: all canonical keys must be present in config.scoring.<section>.weights.
    """

    mode = str(scoring_cfg.get("weights_mode", "compat")).strip().lower()
    if mode not in {"compat", "strict"}:
        logger.warning(
            "Unknown weights_mode '%s' for config.scoring.%s, using compat",
            mode,
            section_name,
        )
        mode = "compat"

    cfg_weights = scoring_cfg.get("weights")
    if not isinstance(cfg_weights, dict):
        logger.warning("Using default weights for config.scoring.%s.weights", section_name)
        return default_weights.copy()

    resolved: Dict[str, float] = {}
    for canonical_key, fallback_value in default_weights.items():
        alias_key = aliases.get(canonical_key)
        canonical_present = canonical_key in cfg_weights and cfg_weights.get(canonical_key) is not None
        alias_present = bool(alias_key) and alias_key in cfg_weights and cfg_weights.get(alias_key) is not None

        if canonical_present and alias_present and cfg_weights[canonical_key] != cfg_weights[alias_key]:
            logger.warning(
                "Conflicting canonical/legacy weights for config.scoring.%s.weights.%s/%s; using canonical value",
                section_name,
                canonical_key,
                alias_key,
            )

        if canonical_present:
            resolved[canonical_key] = float(cfg_weights[canonical_key])
        elif alias_present and mode == "compat":
            resolved[canonical_key] = float(cfg_weights[alias_key])
        elif mode == "compat":
            resolved[canonical_key] = float(fallback_value)

    if mode == "strict":
        missing = [k for k in default_weights if k not in resolved]
        if missing:
            logger.warning(
                "Missing required canonical weight keys for config.scoring.%s.weights: %s. Using defaults.",
                section_name,
                ", ".join(missing),
            )
            return default_weights.copy()

    if any(v < 0 for v in resolved.values()):
        logger.warning("Negative weights detected for config.scoring.%s.weights. Using defaults.", section_name)
        return default_weights.copy()

    total = sum(resolved.values())
    if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
        logger.warning(
            "Weight sum for config.scoring.%s.weights must be ~1.0 (got %.10f). Using defaults.",
            section_name,
            total,
        )
        return default_weights.copy()

    return resolved

```

### `scanner/pipeline/scoring/__init__.py`

**SHA256:** `a6825c25a4e86a74fc0161093fbb40635de680c8d49b0da16935e6ff41c74efc`

```python
"""
Scoring package.

Contains three independent scoring modules:
- breakout.py
- breakout_trend_1_5d.py
- pullback.py
- reversal.py

Each module:
- consumes features
- applies setup-specific logic
- outputs normalized scores, components, penalties and flags.
"""


```

### `scanner/pipeline/scoring/pullback.py`

**SHA256:** `794a4b1e81b85ead5f20bab7c353380aa32b9c5aab6d7162c4dff27b02377a05`

```python
"""Pullback scoring."""

import logging
import math
from typing import Dict, Any, List, Optional

from scanner.pipeline.scoring.weights import load_component_weights
from scanner.pipeline.scoring.trade_levels import pullback_trade_levels, compute_phase1_risk_fields
from scanner.pipeline.scoring.decision_inputs import standardize_entry_readiness, standardize_invalidation_anchor

logger = logging.getLogger(__name__)


class PullbackScorer:
    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        scoring_cfg = root.get("scoring", {}).get("pullback", {})

        self.min_trend_strength = float(scoring_cfg.get("min_trend_strength", 5.0))
        self.min_rebound = float(scoring_cfg.get("min_rebound", 3.0))
        self.min_volume_spike = float(scoring_cfg.get("min_volume_spike", 1.3))

        momentum_cfg = scoring_cfg.get("momentum", {})
        self.momentum_divisor = float(momentum_cfg.get("r7_divisor", 10.0))

        penalties_cfg = scoring_cfg.get("penalties", {})
        self.broken_trend_factor = float(penalties_cfg.get("broken_trend_factor", 0.5))
        self.low_liquidity_threshold = float(penalties_cfg.get("low_liquidity_threshold", 500_000))
        self.low_liquidity_factor = float(penalties_cfg.get("low_liquidity_factor", 0.8))

        default_weights = {"trend": 0.30, "pullback": 0.25, "rebound": 0.25, "volume": 0.20}
        self.weights = load_component_weights(
            scoring_cfg=scoring_cfg,
            section_name="pullback",
            default_weights=default_weights,
            aliases={
                "trend": "trend_quality",
                "pullback": "pullback_quality",
                "rebound": "rebound_signal",
            },
)
    @staticmethod
    def _closed_candle_count(features: Dict[str, Any], timeframe: str) -> Optional[int]:
        meta = features.get("meta", {})
        idx_map = meta.get("last_closed_idx", {}) if isinstance(meta, dict) else {}
        idx = idx_map.get(timeframe)
        if isinstance(idx, int) and idx >= 0:
            return idx + 1
        return None

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float, volume_source_used: str = "mexc") -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})
        invalidation_anchor = self._resolve_invalidation_anchor(f1d, f4h)

        trend_score = self._score_trend(f1d)
        pullback_score = self._score_pullback(f1d)
        rebound_score = self._score_rebound(f1d, f4h)
        volume_score = self._score_volume(f1d, f4h)

        raw_score = (
            trend_score * self.weights["trend"]
            + pullback_score * self.weights["pullback"]
            + rebound_score * self.weights["rebound"]
            + volume_score * self.weights["volume"]
        )

        penalties = []
        flags = []

        dist_ema50 = f1d.get("dist_ema50_pct")
        if dist_ema50 is not None and dist_ema50 < 0:
            penalties.append(("broken_trend", self.broken_trend_factor))
            flags.append("broken_trend")

        if quote_volume_24h < self.low_liquidity_threshold:
            penalties.append(("low_liquidity", self.low_liquidity_factor))
            flags.append("low_liquidity")

        soft_penalties = features.get("soft_penalties", {}) if isinstance(features, dict) else {}
        if isinstance(soft_penalties, dict):
            for penalty_name, factor in soft_penalties.items():
                try:
                    penalties.append((str(penalty_name), float(factor)))
                except (TypeError, ValueError):
                    continue

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor
        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(trend_score, pullback_score, rebound_score, volume_score, f1d, f4h, flags, volume_source_used)
        pullback_v2 = self._resolve_pullback_v2_fields(f1d, f4h)

        return {
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 6),
            "penalty_multiplier": round(penalty_multiplier, 6),
            "final_score": round(final_score, 6),
            "components": {
                "trend": round(trend_score, 2),
                "pullback": round(pullback_score, 2),
                "rebound": round(rebound_score, 2),
                "volume": round(volume_score, 2),
            },
            "penalties": {name: factor for name, factor in penalties},
            "flags": flags,
            "reasons": reasons,
            "volume_source_used": volume_source_used,
            **pullback_v2,
            **invalidation_anchor,
        }


    def _resolve_pullback_v2_fields(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> Dict[str, Any]:
        r3_1d = f1d.get("r_3")
        r3_4h = f4h.get("r_3")

        numeric_values = []
        for value in (r3_1d, r3_4h):
            if value is None:
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(numeric):
                return {
                    "rebound_confirmed": None,
                    "retest_reclaimed": None,
                    **standardize_entry_readiness(
                        entry_ready=False,
                        reason_keys=["rebound_not_evaluable"],
                        setup_subtype="pullback_to_ema",
                    ),
                }
            numeric_values.append(numeric)

        if not numeric_values:
            return {
                "rebound_confirmed": None,
                "retest_reclaimed": None,
                **standardize_entry_readiness(
                    entry_ready=False,
                    reason_keys=["rebound_not_evaluable"],
                    setup_subtype="pullback_to_ema",
                ),
            }

        rebound_confirmed = max(numeric_values) >= self.min_rebound
        retest_reclaimed = rebound_confirmed
        return {
            "rebound_confirmed": rebound_confirmed,
            "retest_reclaimed": retest_reclaimed,
            **standardize_entry_readiness(
                entry_ready=rebound_confirmed,
                reason_keys=["rebound_not_confirmed"],
                setup_subtype="pullback_to_ema",
            ),
        }

    def _resolve_invalidation_anchor(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> Dict[str, Any]:
        ema50_4h = f4h.get("ema_50")
        ema20_4h = f4h.get("ema_20")

        anchor_type = None
        anchor_price = None
        if ema50_4h is not None:
            anchor_type = "support_level"
            anchor_price = ema50_4h
        elif ema20_4h is not None:
            anchor_type = "ema_reclaim"
            anchor_price = ema20_4h

        if anchor_type is None:
            return standardize_invalidation_anchor(anchor_price=None, anchor_type=None, derivable=False)
        return standardize_invalidation_anchor(anchor_price=anchor_price, anchor_type=anchor_type, derivable=True)

    def _score_trend(self, f1d: Dict[str, Any]) -> float:
        score = 0.0
        dist_ema50 = f1d.get("dist_ema50_pct")
        if dist_ema50 is None or dist_ema50 < 0:
            return 0.0

        if dist_ema50 >= 15:
            score += 60
        elif dist_ema50 >= 10:
            score += 50
        elif dist_ema50 >= self.min_trend_strength:
            score += 40
        else:
            score += 20

        if f1d.get("hh_20"):
            score += 40
        return min(score, 100.0)

    def _score_pullback(self, f1d: Dict[str, Any]) -> float:
        dist_ema20 = f1d.get("dist_ema20_pct", 100)
        dist_ema50 = f1d.get("dist_ema50_pct", 100)

        if -2 <= dist_ema20 <= 2:
            return 100.0
        if -2 <= dist_ema50 <= 2:
            return 80.0
        if dist_ema20 < 0 and dist_ema50 >= 0:
            return 60.0
        if dist_ema20 > 5:
            return 20.0
        if dist_ema50 < -5:
            return 10.0
        return 40.0

    def _score_rebound(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        score = 0.0
        r3 = f1d.get("r_3", 0)
        if r3 >= 10:
            score += 50
        elif r3 >= self.min_rebound:
            score += 30
        elif r3 > 0:
            score += 10

        r3_4h = f4h.get("r_3", 0)
        if r3_4h >= 5:
            score += 50
        elif r3_4h >= 2:
            score += 30
        elif r3_4h > 0:
            score += 10

        r7 = f1d.get("r_7")
        if r7 is not None and self.momentum_divisor > 0:
            score = 0.8 * score + 0.2 * max(0.0, min(100.0, (float(r7) / self.momentum_divisor) * 100.0))

        return min(score, 100.0)

    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        max_spike = max(spike_1d, spike_4h)
        if max_spike < self.min_volume_spike:
            return 0.0
        if max_spike >= 2.5:
            return 100.0
        if max_spike >= 2.0:
            return 80.0
        ratio = (max_spike - self.min_volume_spike) / (2.0 - self.min_volume_spike)
        return ratio * 70.0

    def _generate_reasons(self, trend_score: float, pullback_score: float, rebound_score: float, volume_score: float,
                          f1d: Dict[str, Any], f4h: Dict[str, Any], flags: List[str], volume_source_used: str) -> List[str]:
        reasons = [f"Volume source used: {volume_source_used}"]

        dist_ema50 = f1d.get("dist_ema50_pct", 0)
        if trend_score > 70:
            reasons.append(f"Strong uptrend ({dist_ema50:.1f}% above EMA50)")
        elif trend_score > 30:
            reasons.append(f"Moderate uptrend ({dist_ema50:.1f}% above EMA50)")
        else:
            reasons.append("Weak/no uptrend")

        dist_ema20 = f1d.get("dist_ema20_pct", 0)
        if pullback_score > 70:
            reasons.append(f"At support level ({dist_ema20:.1f}% from EMA20)")
        elif pullback_score > 40:
            reasons.append("Healthy pullback depth")
        else:
            reasons.append("No clear pullback")

        r3 = f1d.get("r_3", 0)
        if rebound_score > 60:
            reasons.append(f"Strong rebound ({r3:.1f}% in 3d)")
        elif rebound_score > 30:
            reasons.append("Moderate rebound")
        else:
            reasons.append("No rebound yet")

        spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        vol_spike = max(spike_1d, spike_4h)
        if volume_score > 60:
            reasons.append(f"Strong volume ({vol_spike:.1f}x)")
        elif volume_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")

        if "broken_trend" in flags:
            reasons.append("⚠️ Below EMA50 (trend broken)")
        if "low_liquidity" in flags:
            reasons.append("⚠️ Low liquidity")

        return reasons


def score_pullbacks(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any], volume_source_map: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    scorer = PullbackScorer(config)
    results = []
    root = config.raw if hasattr(config, "raw") else config
    min_1d = int(root.get("setup_validation", {}).get("min_history_pullback_1d", 60))
    min_4h = int(root.get("setup_validation", {}).get("min_history_pullback_4h", 80))
    trade_levels_cfg = root.get("trade_levels", {}) if isinstance(root, dict) else {}
    pb_tol_pct = float(trade_levels_cfg.get("pullback_entry_tolerance_pct", 1.0))
    target_multipliers = [float(x) for x in trade_levels_cfg.get("target_atr_multipliers", [1.0, 2.0, 3.0])]
    for symbol, features in features_data.items():
        candles_1d = scorer._closed_candle_count(features, "1d")
        candles_4h = scorer._closed_candle_count(features, "4h")
        if candles_1d is None or candles_4h is None or candles_1d < min_1d or candles_4h < min_4h:
            logger.debug(
                "Skipping pullback for %s due to insufficient history (1d=%s/%s, 4h=%s/%s)",
                symbol,
                candles_1d,
                min_1d,
                candles_4h,
                min_4h,
            )
            continue
        volume = volumes.get(symbol, 0)
        try:
            volume_source_used = (volume_source_map or {}).get(symbol, "mexc")
            score_result = scorer.score(symbol, features, volume, volume_source_used=volume_source_used)
            trade_levels = pullback_trade_levels(features, target_multipliers, pb_tol_pct=pb_tol_pct)
            risk_fields = compute_phase1_risk_fields("pullback", trade_levels, root)
            results.append(
                {
                    "symbol": symbol,
                    "price_usdt": features.get("price_usdt"),
                    "coin_name": features.get("coin_name"),
                    "market_cap": features.get("market_cap"),
                    "quote_volume_24h": features.get("quote_volume_24h"),
                    "proxy_liquidity_score": features.get("proxy_liquidity_score"),
                    "spread_bps": features.get("spread_bps"),
                    "slippage_bps": features.get("slippage_bps"),
                    "liquidity_grade": features.get("liquidity_grade"),
                    "liquidity_insufficient": features.get("liquidity_insufficient"),
                    "score": score_result["score"],
                    "raw_score": score_result["raw_score"],
                    "penalty_multiplier": score_result["penalty_multiplier"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "risk_flags": features.get("risk_flags", []),
                    "reasons": score_result["reasons"],
                    "volume_source_used": score_result["volume_source_used"],
                    "entry_ready": score_result["entry_ready"],
                    "entry_readiness_reasons": score_result["entry_readiness_reasons"],
                    "setup_subtype": score_result["setup_subtype"],
                    "rebound_confirmed": score_result["rebound_confirmed"],
                    "retest_reclaimed": score_result["retest_reclaimed"],
                    "invalidation_anchor_price": score_result["invalidation_anchor_price"],
                    "invalidation_anchor_type": score_result["invalidation_anchor_type"],
                    "invalidation_derivable": score_result["invalidation_derivable"],
                    "analysis": {"trade_levels": trade_levels},
                    **risk_fields,
                    "discovery": features.get("discovery", False),
                    "discovery_age_days": features.get("discovery_age_days"),
                    "discovery_source": features.get("discovery_source"),
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

```

### `scanner/pipeline/scoring/reversal.py`

**SHA256:** `11e5e735879e1f0a6e5e2659f7497c60370e1416b7d11487289e9bc23eb7ebdb`

```python
"""
Reversal Setup Scoring
======================

Identifies downtrend → base → reclaim setups.
"""

import logging
import math
from typing import Dict, Any, List, Optional

from scanner.pipeline.scoring.weights import load_component_weights
from scanner.pipeline.scoring.trade_levels import reversal_trade_levels, compute_phase1_risk_fields
from scanner.pipeline.scoring.decision_inputs import standardize_entry_readiness, standardize_invalidation_anchor

logger = logging.getLogger(__name__)


class ReversalScorer:
    """Scores reversal setups (downtrend → base → reclaim)."""

    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        scoring_cfg = root.get("scoring", {}).get("reversal", {})

        self.min_drawdown = float(scoring_cfg.get("min_drawdown_pct", 40.0))
        self.ideal_drawdown_min = float(scoring_cfg.get("ideal_drawdown_min", 50.0))
        self.ideal_drawdown_max = float(scoring_cfg.get("ideal_drawdown_max", 80.0))
        self.min_volume_spike = float(scoring_cfg.get("min_volume_spike", 1.5))

        penalties_cfg = scoring_cfg.get("penalties", {})
        self.overextension_threshold = float(penalties_cfg.get("overextension_threshold_pct", 15.0))
        self.overextension_factor = float(penalties_cfg.get("overextension_factor", 0.7))
        self.low_liquidity_threshold = float(penalties_cfg.get("low_liquidity_threshold", 500_000))
        self.low_liquidity_factor = float(penalties_cfg.get("low_liquidity_factor", 0.8))

        default_weights = {
            "drawdown": 0.30,
            "base": 0.25,
            "reclaim": 0.25,
            "volume": 0.20,
        }
        self.weights = load_component_weights(
            scoring_cfg=scoring_cfg,
            section_name="reversal",
            default_weights=default_weights,
            aliases={
                "base": "base_structure",
                "reclaim": "reclaim_signal",
                "volume": "volume_confirmation",
            },
)
    @staticmethod
    def _closed_candle_count(features: Dict[str, Any], timeframe: str) -> Optional[int]:
        meta = features.get("meta", {})
        idx_map = meta.get("last_closed_idx", {}) if isinstance(meta, dict) else {}
        idx = idx_map.get(timeframe)
        if isinstance(idx, int) and idx >= 0:
            return idx + 1
        return None

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float, volume_source_used: str = "mexc") -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})
        invalidation_anchor = self._resolve_invalidation_anchor(f1d)

        drawdown_score = self._score_drawdown(f1d)
        base_score = self._score_base(f1d)
        reclaim_score = self._score_reclaim(f1d)
        volume_score = self._score_volume(f1d, f4h)

        raw_score = (
            drawdown_score * self.weights["drawdown"]
            + base_score * self.weights["base"]
            + reclaim_score * self.weights["reclaim"]
            + volume_score * self.weights["volume"]
        )

        penalties = []
        flags = []

        dist_ema50 = f1d.get("dist_ema50_pct")
        if dist_ema50 is not None and dist_ema50 > self.overextension_threshold:
            penalties.append(("overextension", self.overextension_factor))
            flags.append("overextended")

        if quote_volume_24h < self.low_liquidity_threshold:
            penalties.append(("low_liquidity", self.low_liquidity_factor))
            flags.append("low_liquidity")

        soft_penalties = features.get("soft_penalties", {}) if isinstance(features, dict) else {}
        if isinstance(soft_penalties, dict):
            for penalty_name, factor in soft_penalties.items():
                try:
                    penalties.append((str(penalty_name), float(factor)))
                except (TypeError, ValueError):
                    continue

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor

        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(drawdown_score, base_score, reclaim_score, volume_score, f1d, f4h, flags, volume_source_used)
        reversal_v2 = self._resolve_reversal_v2_fields(f1d)

        return {
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 6),
            "penalty_multiplier": round(penalty_multiplier, 6),
            "final_score": round(final_score, 6),
            "components": {
                "drawdown": round(drawdown_score, 2),
                "base": round(base_score, 2),
                "reclaim": round(reclaim_score, 2),
                "volume": round(volume_score, 2),
            },
            "penalties": {name: factor for name, factor in penalties},
            "flags": flags,
            "reasons": reasons,
            "volume_source_used": volume_source_used,
            **reversal_v2,
            **invalidation_anchor,
        }


    def _resolve_reversal_v2_fields(self, f1d: Dict[str, Any]) -> Dict[str, Any]:
        dist_ema20 = f1d.get("dist_ema20_pct")
        dist_ema50 = f1d.get("dist_ema50_pct")

        if dist_ema20 is None or dist_ema50 is None:
            return {
                "reclaim_confirmed": None,
                "retest_reclaimed": None,
                **standardize_entry_readiness(
                    entry_ready=False,
                    reason_keys=["reclaim_not_evaluable"],
                    setup_subtype="reversal_base_reclaim",
                ),
            }

        try:
            ema20 = float(dist_ema20)
            ema50 = float(dist_ema50)
        except (TypeError, ValueError):
            return {
                "reclaim_confirmed": None,
                "retest_reclaimed": None,
                **standardize_entry_readiness(
                    entry_ready=False,
                    reason_keys=["reclaim_not_evaluable"],
                    setup_subtype="reversal_base_reclaim",
                ),
            }

        if not math.isfinite(ema20) or not math.isfinite(ema50):
            return {
                "reclaim_confirmed": None,
                "retest_reclaimed": None,
                **standardize_entry_readiness(
                    entry_ready=False,
                    reason_keys=["reclaim_not_evaluable"],
                    setup_subtype="reversal_base_reclaim",
                ),
            }

        reclaim_confirmed = ema20 > 0 and ema50 > 0
        return {
            "reclaim_confirmed": reclaim_confirmed,
            "retest_reclaimed": reclaim_confirmed,
            **standardize_entry_readiness(
                entry_ready=reclaim_confirmed,
                reason_keys=["retest_not_reclaimed"],
                setup_subtype="reversal_base_reclaim",
            ),
        }

    def _resolve_invalidation_anchor(self, f1d: Dict[str, Any]) -> Dict[str, Any]:
        base_low = f1d.get("base_low")
        anchor_type = "base_low"
        if base_low is None:
            base_low = f1d.get("ema_20")
            anchor_type = "ema_reclaim"

        return standardize_invalidation_anchor(anchor_price=base_low, anchor_type=anchor_type, derivable=base_low is not None)

    def _score_drawdown(self, f1d: Dict[str, Any]) -> float:
        dd = f1d.get("drawdown_from_ath")
        if dd is None or dd >= 0:
            return 0.0

        dd_pct = abs(dd)
        if dd_pct < self.min_drawdown:
            return 0.0
        if self.ideal_drawdown_min <= dd_pct <= self.ideal_drawdown_max:
            return 100.0
        if dd_pct < self.ideal_drawdown_min:
            ratio = (dd_pct - self.min_drawdown) / (self.ideal_drawdown_min - self.min_drawdown)
            return 50.0 + ratio * 50.0

        excess = dd_pct - self.ideal_drawdown_max
        penalty = min(excess / 20, 0.5)
        return 100.0 * (1 - penalty)

    def _score_base(self, f1d: Dict[str, Any]) -> float:
        base_score = f1d.get("base_score")
        if base_score is None:
            return 0.0

        try:
            numeric = float(base_score)
        except (TypeError, ValueError):
            return 0.0

        if not math.isfinite(numeric):
            return 0.0

        return max(0.0, min(100.0, numeric))

    def _score_reclaim(self, f1d: Dict[str, Any]) -> float:
        score = 0.0
        dist_ema20 = f1d.get("dist_ema20_pct")
        dist_ema50 = f1d.get("dist_ema50_pct")

        if dist_ema20 is not None and dist_ema20 > 0:
            score += 30
        if dist_ema50 is not None and dist_ema50 > 0:
            score += 30
        if f1d.get("hh_20"):
            score += 20

        r7 = f1d.get("r_7")
        if r7 is not None:
            momentum_score = max(0.0, min(100.0, (float(r7) / 10.0) * 100.0))
            score += 0.2 * momentum_score

        return min(score, 100.0)

    def _resolve_volume_spike(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        vol_spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        vol_spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        return max(vol_spike_1d, vol_spike_4h)

    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        max_spike = self._resolve_volume_spike(f1d, f4h)

        if max_spike < self.min_volume_spike:
            return 0.0
        if max_spike >= 3.0:
            return 100.0
        ratio = (max_spike - self.min_volume_spike) / (3.0 - self.min_volume_spike)
        return ratio * 100.0

    def _generate_reasons(
        self,
        dd_score: float,
        base_score: float,
        reclaim_score: float,
        vol_score: float,
        f1d: Dict[str, Any],
        f4h: Dict[str, Any],
        flags: List[str],
        volume_source_used: str,
    ) -> List[str]:
        reasons = [f"Volume source used: {volume_source_used}"]

        dd = f1d.get("drawdown_from_ath")
        if dd and dd < 0:
            dd_pct = abs(dd)
            if dd_score > 70:
                reasons.append(f"Strong drawdown setup ({dd_pct:.1f}% from ATH)")
            elif dd_score > 30:
                reasons.append(f"Moderate drawdown ({dd_pct:.1f}% from ATH)")

        if base_score > 60:
            reasons.append("Clean base formation detected")
        elif base_score == 0:
            reasons.append("No base detected (still declining)")

        dist_ema50 = f1d.get("dist_ema50_pct")
        if reclaim_score > 60:
            reasons.append(f"Reclaimed EMAs ({dist_ema50:.1f}% above EMA50)")
        elif reclaim_score > 30:
            reasons.append("Partial reclaim in progress")
        else:
            reasons.append("Below EMAs (no reclaim yet)")

        vol_spike = self._resolve_volume_spike(f1d, f4h)
        if vol_score > 60:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif vol_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")

        if "overextended" in flags:
            reasons.append(f"⚠️ Overextended ({dist_ema50:.1f}% above EMA50)")
        if "low_liquidity" in flags:
            reasons.append("⚠️ Low liquidity")

        return reasons


def score_reversals(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any], volume_source_map: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    scorer = ReversalScorer(config)
    results = []
    root = config.raw if hasattr(config, "raw") else config
    min_1d = int(root.get("setup_validation", {}).get("min_history_reversal_1d", 120))
    min_4h = int(root.get("setup_validation", {}).get("min_history_reversal_4h", 80))

    trade_levels_cfg = root.get("trade_levels", {}) if isinstance(root, dict) else {}
    target_multipliers = [float(x) for x in trade_levels_cfg.get("target_atr_multipliers", [1.0, 2.0, 3.0])]
    for symbol, features in features_data.items():
        candles_1d = scorer._closed_candle_count(features, "1d")
        candles_4h = scorer._closed_candle_count(features, "4h")
        if candles_1d is None or candles_4h is None or candles_1d < min_1d or candles_4h < min_4h:
            logger.debug(
                "Skipping reversal for %s due to insufficient history (1d=%s/%s, 4h=%s/%s)",
                symbol,
                candles_1d,
                min_1d,
                candles_4h,
                min_4h,
            )
            continue
        volume = volumes.get(symbol, 0)
        try:
            volume_source_used = (volume_source_map or {}).get(symbol, "mexc")
            score_result = scorer.score(symbol, features, volume, volume_source_used=volume_source_used)
            trade_levels = reversal_trade_levels(features, target_multipliers)
            risk_fields = compute_phase1_risk_fields("reversal", trade_levels, root)
            results.append(
                {
                    "symbol": symbol,
                    "price_usdt": features.get("price_usdt"),
                    "coin_name": features.get("coin_name"),
                    "market_cap": features.get("market_cap"),
                    "quote_volume_24h": features.get("quote_volume_24h"),
                    "proxy_liquidity_score": features.get("proxy_liquidity_score"),
                    "spread_bps": features.get("spread_bps"),
                    "slippage_bps": features.get("slippage_bps"),
                    "liquidity_grade": features.get("liquidity_grade"),
                    "liquidity_insufficient": features.get("liquidity_insufficient"),
                    "score": score_result["score"],
                    "raw_score": score_result["raw_score"],
                    "penalty_multiplier": score_result["penalty_multiplier"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "risk_flags": features.get("risk_flags", []),
                    "reasons": score_result["reasons"],
                    "volume_source_used": score_result["volume_source_used"],
                    "entry_ready": score_result["entry_ready"],
                    "entry_readiness_reasons": score_result["entry_readiness_reasons"],
                    "setup_subtype": score_result["setup_subtype"],
                    "reclaim_confirmed": score_result["reclaim_confirmed"],
                    "retest_reclaimed": score_result["retest_reclaimed"],
                    "invalidation_anchor_price": score_result["invalidation_anchor_price"],
                    "invalidation_anchor_type": score_result["invalidation_anchor_type"],
                    "invalidation_derivable": score_result["invalidation_derivable"],
                    "analysis": {"trade_levels": trade_levels},
                    **risk_fields,
                    "discovery": features.get("discovery", False),
                    "discovery_age_days": features.get("discovery_age_days"),
                    "discovery_source": features.get("discovery_source"),
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

```

### `scanner/pipeline/scoring/breakout_trend_1_5d.py`

**SHA256:** `f36dbd8720aca4a7243b0e4f32d38c96126837fc030af0d1d4999332c21ec94a`

```python
"""Breakout Trend 1-5D scoring (immediate + retest)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from scanner.pipeline.scoring.trade_levels import breakout_trade_levels, compute_phase1_risk_fields
from scanner.pipeline.scoring.decision_inputs import standardize_entry_readiness


class BreakoutTrend1to5DScorer:
    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        cfg = root.get("scoring", {}).get("breakout_trend_1_5d", {})

        self.min_24h_risk_off = float(cfg.get("risk_off_min_quote_volume_24h", 15_000_000))
        self.trigger_4h_lookback_bars = int(cfg.get("trigger_4h_lookback_bars", 30))

        gate_cfg = root.get("execution_gates", {}).get("mexc_orderbook", {})
        self.execution_gate_enabled = bool(gate_cfg.get("enabled", True))
        self.max_spread_pct = float(gate_cfg.get("max_spread_pct", 0.15))
        self.execution_bands = [float(v) for v in gate_cfg.get("bands_pct", [0.5, 1.0])]
        self.execution_min_depth = {
            str(k): float(v)
            for k, v in (gate_cfg.get("min_depth_usd", {"0.5": 80_000, "1.0": 200_000}) or {}).items()
        }

    @staticmethod
    def _calc_high_20d_excluding_current(f1d: Dict[str, Any]) -> Optional[float]:
        highs = f1d.get("high_series") or []
        if len(highs) < 21:
            return None
        window = highs[-21:-1]
        return float(max(window)) if window else None

    def _find_breakout_indices(self, f4h: Dict[str, Any], high_20d_1d: float) -> Optional[Tuple[int, int]]:
        closes = f4h.get("close_series") or []
        if not closes:
            return None
        start = max(0, len(closes) - self.trigger_4h_lookback_bars)
        breakout_idxs = [idx for idx in range(start, len(closes)) if float(closes[idx]) > high_20d_1d]
        if not breakout_idxs:
            return None
        return breakout_idxs[0], breakout_idxs[-1]

    @staticmethod
    def _anti_chase_multiplier(r7: float) -> float:
        if r7 < 30:
            return 1.0
        if r7 <= 60:
            return 1.0 - ((r7 - 30.0) / 30.0) * 0.25
        return 0.75

    @staticmethod
    def _overextension_multiplier(dist_ema20_pct_1d: float) -> float:
        d = dist_ema20_pct_1d
        if d < 12:
            return 1.0
        if d <= 20:
            return 1.0 - ((d - 12.0) / 8.0) * 0.15
        if d < 28:
            return 0.85 - ((d - 20.0) / 8.0) * 0.15
        return 0.0

    @staticmethod
    def _breakout_distance_score(dist: float) -> float:
        floor, min_breakout, ideal, max_breakout = -5.0, 2.0, 5.0, 20.0
        if dist <= floor:
            return 0.0
        if floor < dist < 0:
            return 30.0 * (dist - floor) / (0.0 - floor)
        if 0 <= dist < min_breakout:
            return 30.0 + 40.0 * (dist / min_breakout)
        if min_breakout <= dist <= ideal:
            return 70.0 + 30.0 * (dist - min_breakout) / (ideal - min_breakout)
        if ideal < dist <= max_breakout:
            return 100.0 * (1.0 - (dist - ideal) / (max_breakout - ideal))
        return 0.0

    @staticmethod
    def _volume_score(spike_combined: float) -> float:
        if spike_combined < 1.5:
            return 0.0
        if spike_combined >= 2.5:
            return 100.0
        return (spike_combined - 1.5) * 100.0

    @staticmethod
    def _trend_score(f4h: Dict[str, Any]) -> float:
        score = 70.0
        close = float(f4h.get("close") or 0.0)
        ema20 = float(f4h.get("ema_20") or 0.0)
        ema50 = float(f4h.get("ema_50") or 0.0)
        if close > ema20:
            score += 15.0
        if ema20 > ema50:
            score += 15.0
        return min(score, 100.0)

    @staticmethod
    def _bb_score(rank: float) -> float:
        rank_pct = rank * 100.0 if rank <= 1.0 else rank
        if rank_pct <= 20.0:
            return 100.0
        if rank_pct <= 60.0:
            return 100.0 - (rank_pct - 20.0) * (60.0 / 40.0)
        return 0.0

    def _btc_multiplier(
        self,
        feature_row: Dict[str, Any],
        btc_regime: Optional[Dict[str, Any]],
    ) -> Tuple[float, str, bool, bool]:
        state = (btc_regime or {}).get("state") or "UNKNOWN"
        if not btc_regime or state == "RISK_ON":
            return 1.0, state, False, False

        f1d = feature_row.get("1d", {})
        alt_r7 = float(f1d.get("r_7") or 0.0)
        alt_r3 = float(f1d.get("r_3") or 0.0)
        btc_r7 = float((btc_regime.get("btc_returns") or {}).get("r_7") or 0.0)
        btc_r3 = float((btc_regime.get("btc_returns") or {}).get("r_3") or 0.0)

        rs_override = (alt_r7 - btc_r7) >= 7.5 or (alt_r3 - btc_r3) >= 3.5
        liq_ok = float(feature_row.get("quote_volume_24h") or 0.0) >= self.min_24h_risk_off
        multiplier = 0.85 if rs_override and liq_ok else 0.75
        return multiplier, state, rs_override, liq_ok


    @staticmethod
    def _band_label(band: float) -> str:
        bf = float(band)
        if bf.is_integer():
            return str(int(bf))
        return str(bf).replace(".", "_")

    @staticmethod
    def _band_reason(band: float) -> str:
        return f"DEPTH_TOO_LOW_{str(float(band)).replace('.', '_')}"

    def _evaluate_execution_gate(self, feature_row: Dict[str, Any]) -> Tuple[bool, List[str]]:
        if not self.execution_gate_enabled:
            return True, []

        fail_reasons: List[str] = []
        if feature_row.get("orderbook_ok") is not True:
            fail_reasons.append("ORDERBOOK_MISSING")
            return False, fail_reasons

        spread_pct = feature_row.get("spread_pct")
        if spread_pct is None or float(spread_pct) > self.max_spread_pct:
            fail_reasons.append("SPREAD_TOO_WIDE")

        for band in self.execution_bands:
            label = self._band_label(band)
            reason = self._band_reason(band)
            bid = feature_row.get(f"depth_bid_{label}pct_usd")
            ask = feature_row.get(f"depth_ask_{label}pct_usd")
            threshold = self.execution_min_depth.get(str(band), self.execution_min_depth.get(f"{band:.1f}", 0.0))
            if bid is None or ask is None or min(float(bid), float(ask)) < float(threshold):
                fail_reasons.append(reason)

        return len(fail_reasons) == 0, fail_reasons

    def score_symbol(
        self,
        symbol: str,
        feature_row: Dict[str, Any],
        quote_volume_24h: float,
        btc_regime: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        f1d = feature_row.get("1d", {})
        f4h = feature_row.get("4h", {})

        high_20 = self._calc_high_20d_excluding_current(f1d)
        if high_20 is None:
            return []

        breakout_indices = self._find_breakout_indices(f4h, high_20)
        if breakout_indices is None:
            return []
        first_breakout_idx, last_breakout_idx = breakout_indices

        if not (
            float(f1d.get("close") or 0.0) > float(f1d.get("ema_20") or 0.0)
            and float(f1d.get("ema_20") or 0.0) > float(f1d.get("ema_50") or 0.0)
        ):
            return []
        if float(f1d.get("atr_pct_rank_120") or 0.0) > 80.0:
            return []
        if float(f1d.get("r_7") or 0.0) <= 0.0:
            return []

        dist_ema20 = float(f1d.get("dist_ema20_pct") or 0.0)
        if dist_ema20 >= 28.0:
            return []

        closes = f4h.get("close_series") or []
        close_4h_trigger = float(closes[last_breakout_idx]) if last_breakout_idx < len(closes) else float(f4h.get("close") or 0.0)
        dist_pct = ((close_4h_trigger / high_20) - 1.0) * 100.0

        spike_1d = float(f1d.get("volume_quote_spike") or 0.0)
        spike_4h = float(f4h.get("volume_quote_spike") or 0.0)
        spike_combined = 0.7 * spike_1d + 0.3 * spike_4h

        breakout_distance_score = self._breakout_distance_score(dist_pct)
        volume_score = self._volume_score(spike_combined)
        trend_score = self._trend_score(f4h)
        bb_rank = float(f4h.get("bb_width_rank_120") or 0.0)
        bb_score = self._bb_score(bb_rank)

        base_score = (
            0.35 * breakout_distance_score
            + 0.35 * volume_score
            + 0.15 * trend_score
            + 0.15 * bb_score
        )

        anti = self._anti_chase_multiplier(float(f1d.get("r_7") or 0.0))
        over = self._overextension_multiplier(dist_ema20)
        btc_mult, btc_state, btc_rs_override, btc_liq_ok_risk_off = self._btc_multiplier(
            {**feature_row, "quote_volume_24h": quote_volume_24h}, btc_regime
        )

        final_score = max(0.0, min(100.0, base_score * anti * over * btc_mult))

        base = {
            **standardize_entry_readiness(
                entry_ready=True,
                reason_keys=["breakout_not_confirmed"],
                setup_subtype="confirmed_breakout",
            ),
            "breakout_confirmed": True,
            "symbol": symbol,
            "score": round(final_score, 6),
            "base_score": round(base_score, 6),
            "final_score": round(final_score, 6),
            "high_20d_1d": round(high_20, 8),
            "dist_pct": round(dist_pct, 6),
            "volume_quote_spike_1d": spike_1d,
            "volume_quote_spike_4h": spike_4h,
            "spike_combined": round(spike_combined, 6),
            "atr_pct_rank_120_1d": f1d.get("atr_pct_rank_120"),
            "bb_width_pct_4h": f4h.get("bb_width_pct"),
            "bb_width_rank_120_4h": bb_rank,
            "overextension_multiplier": round(over, 6),
            "anti_chase_multiplier": round(anti, 6),
            "btc_multiplier": round(btc_mult, 6),
            "btc_state": btc_state,
            "btc_rs_override": btc_rs_override,
            "btc_liq_ok_risk_off": btc_liq_ok_risk_off,
            "breakout_distance_score": round(breakout_distance_score, 6),
            "volume_score": round(volume_score, 6),
            "trend_score": round(trend_score, 6),
            "bb_score": round(bb_score, 6),
            "triggered": True,
            "quote_volume_24h": quote_volume_24h,
            "coin_name": feature_row.get("coin_name"),
            "market_cap": feature_row.get("market_cap"),
            "price_usdt": feature_row.get("price_usdt"),
            "proxy_liquidity_score": feature_row.get("proxy_liquidity_score"),
            "spread_bps": feature_row.get("spread_bps"),
            "slippage_bps": feature_row.get("slippage_bps"),
            "liquidity_grade": feature_row.get("liquidity_grade"),
            "liquidity_insufficient": feature_row.get("liquidity_insufficient"),
            "spread_pct": feature_row.get("spread_pct"),
            "depth_bid_0_5pct_usd": feature_row.get("depth_bid_0_5pct_usd"),
            "depth_ask_0_5pct_usd": feature_row.get("depth_ask_0_5pct_usd"),
            "depth_bid_1pct_usd": feature_row.get("depth_bid_1pct_usd"),
            "depth_ask_1pct_usd": feature_row.get("depth_ask_1pct_usd"),
            "orderbook_ok": feature_row.get("orderbook_ok"),
            "risk_flags": feature_row.get("risk_flags", []),
        }

        execution_gate_pass, execution_gate_fail_reasons = self._evaluate_execution_gate(feature_row)
        base["execution_gate_pass"] = execution_gate_pass
        base["execution_gate_fail_reasons"] = execution_gate_fail_reasons

        results: List[Dict[str, Any]] = [{**base, "setup_id": "breakout_immediate_1_5d", "retest_valid": False, "retest_invalidated": False, "setup_subtype": "fresh_breakout"}]

        lows = f4h.get("low_series") or []
        zone_low = high_20 * 0.99
        zone_high = high_20 * 1.01
        retest_valid = False
        retest_invalidated = False
        end_idx = min(len(closes) - 1, first_breakout_idx + 12)
        for j in range(first_breakout_idx + 1, end_idx + 1):
            c = float(closes[j])
            if c < high_20:
                retest_invalidated = True
                break
            low = float(lows[j]) if j < len(lows) else c
            touch = zone_low <= low <= zone_high
            reclaim = c >= high_20
            if touch and reclaim:
                retest_valid = True
                break

        if retest_valid and not retest_invalidated:
            results.append({**base, "setup_id": "breakout_retest_1_5d", "retest_valid": True, "retest_invalidated": False, "setup_subtype": "confirmed_breakout"})

        return results


def score_breakout_trend_1_5d(
    features_data: Dict[str, Dict[str, Any]],
    volumes: Dict[str, float],
    config: Dict[str, Any],
    btc_regime: Optional[Dict[str, Any]] = None,
    volume_source_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    scorer = BreakoutTrend1to5DScorer(config)
    root = config.raw if hasattr(config, "raw") else config
    min_1d = int(root.get("setup_validation", {}).get("min_history_breakout_1d", 30))
    min_4h = int(root.get("setup_validation", {}).get("min_history_breakout_4h", 50))
    trade_levels_cfg = root.get("trade_levels", {}) if isinstance(root, dict) else {}
    target_multipliers = [float(x) for x in trade_levels_cfg.get("target_atr_multipliers", [1.0, 2.0, 3.0])]

    results: List[Dict[str, Any]] = []
    for symbol, feature_row in features_data.items():
        idxs = ((feature_row.get("meta") or {}).get("last_closed_idx") or {})
        candles_1d = int(idxs.get("1d", -1)) + 1 if idxs.get("1d") is not None else None
        candles_4h = int(idxs.get("4h", -1)) + 1 if idxs.get("4h") is not None else None
        if (candles_1d is not None and candles_1d < min_1d) or (candles_4h is not None and candles_4h < min_4h):
            continue
        rows = scorer.score_symbol(symbol, feature_row, float(volumes.get(symbol, 0.0)), btc_regime)
        volume_source_used = (volume_source_map or {}).get(symbol, "mexc")
        for row in rows:
            row["volume_source_used"] = volume_source_used
            trade_levels = breakout_trade_levels(feature_row, target_multipliers)
            row["analysis"] = {"trade_levels": trade_levels}
            row.update(compute_phase1_risk_fields("breakout", trade_levels, root))
        results.extend(rows)

    results.sort(key=lambda x: (float(x.get("final_score", 0.0)), x.get("setup_id") == "breakout_retest_1_5d"), reverse=True)
    return results

```

### `scanner/pipeline/scoring/decision_inputs.py`

**SHA256:** `bfe4020decddcf205e4dc9dd30c3b5392f84a9ef6f14fe556eb6bb641a9cc98f`

```python
"""Helpers for standardized setup-scorer decision inputs."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List


def standardize_entry_readiness(entry_ready: bool, reason_keys: Iterable[str], setup_subtype: str) -> Dict[str, Any]:
    """Build standardized readiness fields for setup scorers.

    Contract:
    - non-entry-ready rows must include at least one standardized reason key
    - entry-ready rows must not include negative readiness reasons
    """

    reasons: List[str] = []
    seen = set()
    for reason in reason_keys:
        if not isinstance(reason, str) or not reason.strip():
            continue
        if reason in seen:
            continue
        seen.add(reason)
        reasons.append(reason)

    is_ready = bool(entry_ready)
    if is_ready:
        reasons = []
    elif not reasons:
        raise ValueError("entry_ready=false requires at least one entry_readiness_reasons key")

    return {
        "entry_ready": is_ready,
        "entry_readiness_reasons": reasons,
        "setup_subtype": setup_subtype,
    }


def standardize_invalidation_anchor(anchor_price: Any, anchor_type: Any, derivable: bool) -> Dict[str, Any]:
    """Build normalized invalidation anchor fields.

    Non-finite or semantically missing anchors are always returned as not-derivable.
    """

    if not derivable:
        return {
            "invalidation_anchor_price": None,
            "invalidation_anchor_type": None,
            "invalidation_derivable": False,
        }

    try:
        numeric_anchor = float(anchor_price)
    except (TypeError, ValueError):
        return {
            "invalidation_anchor_price": None,
            "invalidation_anchor_type": None,
            "invalidation_derivable": False,
        }

    if not math.isfinite(numeric_anchor) or numeric_anchor <= 0 or not isinstance(anchor_type, str) or not anchor_type:
        return {
            "invalidation_anchor_price": None,
            "invalidation_anchor_type": None,
            "invalidation_derivable": False,
        }

    return {
        "invalidation_anchor_price": numeric_anchor,
        "invalidation_anchor_type": anchor_type,
        "invalidation_derivable": True,
    }


```

### `docs/spec.md`

**SHA256:** `b0c5ad329e4d3d78eb8fbfd282cc9df48f1975288fb1eb32ea42854ed81209ca`

```markdown
# LEGACY (moved)

⚠️ This file is kept as a **stub** to preserve automation and historical links.

The canonical legacy content was moved to:
- `docs/legacy/spec.md`

Do **not** use this file as a source of truth.

```

### `docs/scoring.md`

**SHA256:** `ce88e826e0031642412c2ac03a9bee96f708908e216019e313b93a2b9a8fe4a1`

```markdown
# LEGACY (moved)

⚠️ This file is kept as a **stub** to preserve automation and historical links.

The canonical legacy content was moved to:
- `docs/legacy/scoring.md`

Do **not** use this file as a source of truth.

```

### `docs/canonical/INDEX.md`

**SHA256:** `2de26526aade3eaaade383966474dd51d8d8f887da7237b8f2f56d2c82a4f4f8`

```markdown
# Canonical Documentation — Index

## Machine Header (YAML)
```yaml
id: CANON_INDEX
status: canonical
canonical_root: docs/canonical
last_updated_utc: "2026-02-25T14:41:04Z"
```

## Start here
- [AUTHORITY](AUTHORITY.md)
- [INDEX](INDEX.md)
- [SCOPE](SCOPE.md)
- [PIPELINE](PIPELINE.md)
- [DATA_SOURCES](DATA_SOURCES.md)
- [CONFIGURATION](CONFIGURATION.md)
- [OUTPUT_SCHEMA](OUTPUT_SCHEMA.md)
- [VERIFICATION_FOR_AI](VERIFICATION_FOR_AI.md)
- [MAPPING](MAPPING.md)
- [GLOSSARY](GLOSSARY.md)
- [CHANGELOG](CHANGELOG.md)


## Architecture contracts
- [PIPELINE](PIPELINE.md)
- [DECISION_LAYER](DECISION_LAYER.md)
- [RISK_MODEL](RISK_MODEL.md)
- [BUDGET_AND_POOL_MODEL](BUDGET_AND_POOL_MODEL.md)

## Scoring
- [SETUP_VALIDITY_RULES](SCORING/SETUP_VALIDITY_RULES.md)
- [SCORE_BREAKOUT_TREND_1_5D](SCORING/SCORE_BREAKOUT_TREND_1_5D.md)
- [GLOBAL_RANKING_TOP20](SCORING/GLOBAL_RANKING_TOP20.md)
- [DISCOVERY_TAG](SCORING/DISCOVERY_TAG.md)

## Liquidity
- [ORDERBOOK_TOPK_POLICY](LIQUIDITY/ORDERBOOK_TOPK_POLICY.md)
- [SLIPPAGE_CALCULATION](LIQUIDITY/SLIPPAGE_CALCULATION.md)
- [RE_RANK_RULE](LIQUIDITY/RE_RANK_RULE.md)
- [TRADEABILITY_GATE](LIQUIDITY/TRADEABILITY_GATE.md)

## Features
- [FEAT_EMA_STANDARD](FEATURES/FEAT_EMA_STANDARD.md)
- [FEAT_ATR_WILDER](FEATURES/FEAT_ATR_WILDER.md)
- [FEAT_PERCENT_RANK](FEATURES/FEAT_PERCENT_RANK.md)
- [FEAT_VOLUME_SPIKE](FEATURES/FEAT_VOLUME_SPIKE.md)
- [FEAT_ATR_PCT_RANK_120_1D](FEATURES/FEAT_ATR_PCT_RANK_120_1D.md)
- [FEAT_BB_WIDTH_4H_RANK_120](FEATURES/FEAT_BB_WIDTH_4H_RANK_120.md)

## Outputs
- [EVALUATION_DATASET](OUTPUTS/EVALUATION_DATASET.md)
- [RUNTIME_MARKET_META_EXPORT](OUTPUTS/RUNTIME_MARKET_META_EXPORT.md)

## Backtest / Analytics-only
- [MODEL_E2](BACKTEST/MODEL_E2.md)
- [TRADE_MODEL_4H_IMMEDIATE_RETEST](BACKTEST/TRADE_MODEL_4H_IMMEDIATE_RETEST.md)

```

### `docs/canonical/CONFIGURATION.md`

**SHA256:** `32450a04d504b6d27a17b927df293caa0df86c09df9edb7f1dfbc72fd03ce136`

```markdown
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
  min_rr_to_tp10_default: 1.3

decision:
  enabled_default: true
  min_score_for_enter_default: 65
  min_score_for_wait_default: 40
  require_tradeability_for_enter_default: true
  require_risk_acceptable_for_enter_default: true

btc_regime:
  enabled_default: true
  mode_default: threshold_modifier
  mode_values: [threshold_modifier]
  risk_off_enter_boost_default: 15
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
| risk.min_rr_to_tp10_default | risk.min_rr_to_tp10 |
| decision.enabled_default | decision.enabled |
| decision.min_score_for_enter_default | decision.min_score_for_enter |
| decision.min_score_for_wait_default | decision.min_score_for_wait |
| decision.require_tradeability_for_enter_default | decision.require_tradeability_for_enter |
| decision.require_risk_acceptable_for_enter_default | decision.require_risk_acceptable_for_enter |
| btc_regime.enabled_default | btc_regime.enabled |
| btc_regime.mode_default | btc_regime.mode |
| btc_regime.risk_off_enter_boost_default | btc_regime.risk_off_enter_boost |

Notes:
- `general.shortlist_size` is a *prefetch/workload budget* and is not the same as output top-n.
- Legacy alias for backward compatibility:
  - `universe_filters.volume.min_quote_volume_24h` aliases to `universe_filters.volume.min_mexc_quote_volume_24h_usdt`.
  - If both keys are present, `min_mexc_quote_volume_24h_usdt` wins.
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

```

### `docs/canonical/OUTPUT_SCHEMA.md`

**SHA256:** `863b3b078e9587e1e0616db33790cb2ac5d519e7845d8f540ff05dd616d2e97a`

```markdown
# Output Schema — Trade Candidates Source of Truth (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OUTPUT_SCHEMA
status: canonical
schema_version: v1.12
canonical_schema_version_ref: docs/canonical/CHANGELOG.md
outputs:
  - json
  - markdown
  - excel
source_of_truth_entity: trade_candidates
```

## Core contract
- `trade_candidates` is the canonical output Source of Truth (SoT) for candidate-level decision data.
- Markdown and Excel are renderings of the same truth; they must not redefine semantics.
- Run manifest metadata is separate from candidate rows.
- Setup-specific scoring documents may define additional per-row fields, but they MUST NOT redefine this global minimum contract.

## Run manifest (required)
Required fields:
- `run_id`
- `timestamp_utc`
- `config_hash`
- `canonical_schema_version`
- `feature_flags`
- `counts_per_stage`
- `shortlist_size_used`
- `orderbook_top_k_used`
- `data_freshness`
- `warnings`
- `duration_seconds`

Notes:
- `warnings` MUST be a machine-readable list and MAY be empty (`[]`), but MUST NOT be `null`.
- `canonical_schema_version` MUST be sourced from `docs/canonical/CHANGELOG.md`.
- Manifest metadata is operational and remains separated from `trade_candidates`.

## trade_candidates row contract
Minimum required fields:
- `rank`
- `symbol`
- `coin_name`
- `decision`
- `decision_reasons`
- `entry_price_usdt`
- `stop_price_initial`
- `risk_pct_to_stop`
- `tp10_price`
- `tp20_price`
- `rr_to_tp10`
- `rr_to_tp20`
- `best_setup_type`
- `setup_subtype`
- `setup_score`
- `global_score`
- `entry_ready`
- `entry_readiness_reasons`
- `tradeability_class`
- `execution_mode`
- `spread_pct`
- `depth_bid_1pct_usd`
- `depth_ask_1pct_usd`
- `slippage_bps_5k`
- `slippage_bps_20k`
- `risk_acceptable`
- `market_cap_usd`
- `btc_regime`
- `flags`

Deterministic ordering:
- Primary: `decision` priority `ENTER` > `WAIT` > `NO_TRADE`
- Secondary for `ENTER` and `WAIT`: `global_score` descending
- Stable tie-breakers: `symbol` ascending, then `best_setup_type` ascending

## Nullable rules (authoritative)
Whenever a field is semantically not evaluable, value MUST remain `null`.

Typical nullable fields include (non-exhaustive):
- `invalidation_anchor_price`
- `invalidation_anchor_type`
- `invalidation_derivable`
- `stop_price_initial`
- `risk_pct_to_stop`
- `rr_to_tp10`
- `rr_to_tp20`
- `spread_bps`
- `slippage_bps`
- `global_volume_24h_usd`
- `turnover_24h`
- `mexc_share_24h`

No implicit bool/number coercion is allowed for nullable fields.

## decision_reasons contract
- `decision_reasons` must preserve deterministic reason identity and ordering.
- UNKNOWN-path reasons (e.g. `orderbook_data_missing`, `orderbook_data_stale`, `orderbook_not_in_budget`) MUST remain distinct.

## entry_readiness_reasons contract
- `entry_readiness_reasons` must be a deterministic list of standardized reason keys (no free text).
- If `entry_ready=false`, the list must be non-empty.
- If `entry_ready=true`, the list must be empty.

## Trade-candidates vs run-manifest separation
- Candidate-truth lives in `trade_candidates`.
- Operational metadata (runtime, versions, provider set) lives in manifest.
- No format-specific output may contradict the JSON `trade_candidates` truth.

## Markdown rendering minimum contract
- Markdown MUST render candidate rows from `trade_candidates` only.
- Markdown MUST include sections `ENTER Candidates`, `WAIT Candidates`, and `Summary`.
- `WAIT Candidates` MUST include full `decision_reasons` from SoT (no renaming, shortening, or heuristic replacement).
- Missing optional fields in `trade_candidates` MUST be rendered as not-available values rather than causing render crashes.
- Invalid `trade_candidates` schema (e.g. wrong type for required fields) MUST fail clearly instead of silent correction.

## Excel rendering minimum contract
- Excel MUST render candidate rows from `trade_candidates` only.
- Excel MUST contain sheets `Trade Candidates`, `Enter Candidates`, and `Wait Candidates`.
- `Trade Candidates` MUST contain all rows from SoT in deterministic order.
- `Enter Candidates` and `Wait Candidates` MUST be pure filters on `decision` (`ENTER` / `WAIT`) over the same SoT rows.
- `decision` and `decision_reasons` MUST be preserved from SoT without heuristic shortening or semantic remapping.
- Missing optional fields in `trade_candidates` MUST render as empty/not-available cells, not as coerced `0`/`false`.
- Invalid `trade_candidates` schema (e.g. wrong type for required fields) MUST fail clearly instead of silent correction.

## Setup scorer V2 structured fields
Scorer rows may include setup-specific confirmation flags as additive machine-readable fields.
Allowed examples:
- breakout: `breakout_confirmed`
- pullback: `rebound_confirmed`, `retest_reclaimed`
- reversal: `reclaim_confirmed`, `retest_reclaimed`

When a confirmation is semantically not evaluable due to missing/invalid/non-finite inputs, the confirmation field MUST remain `null`.

```

### `docs/canonical/VERIFICATION_FOR_AI.md`

**SHA256:** `adeffba2c8a216695ba6ba5e17c360c4b8d83b9fc59f5ff796c526eca7c658bf`

```markdown
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
- BTC regime state domain is exactly `{RISK_OFF, NEUTRAL, RISK_ON}` with deterministic parsing (`missing => NEUTRAL`, invalid => validation error).
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

```

### `docs/canonical/SCORING/SETUP_VALIDITY_RULES.md`

**SHA256:** `727956639c2b5fba44f7c80dd471632b81ed78179595a05beae6876710dc48bb`

```markdown
# Setup Validity Rules — `is_valid_setup`, Minimum History, Watchlist (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_SETUP_VALIDITY
status: canonical
invalid_behavior:
  top_lists: exclude
  watchlist: optional_include_with_reason
reasons_canonical:
  - insufficient_history
  - failed_gate
  - risk_flag
  - btc_risk_off_ineligible
minimum_history_defaults:
  breakout: { "1d": 30, "4h": 50 }
  pullback: { "1d": 60, "4h": 80 }
  reversal: { "1d": 120, "4h": 80 }
setup_id_to_history_key:
  breakout_immediate_1_5d: breakout
  breakout_retest_1_5d: breakout
```

## 1) `is_valid_setup` contract
- If `is_valid_setup == false`:
  - must not appear in Top lists/rankings
  - may appear in watchlist only if a stable reason is provided

## 2) Canonical reasons
Reasons must be deterministic strings (stable keys), e.g.:
- `insufficient_history:<tf>`
- `failed_gate:<gate_name>`
- `risk_flag:<flag_name>`
- `btc_risk_off_ineligible`

## 3) Minimum history thresholds (defaults)
These defaults must match `CONFIGURATION.md`.

### Breakout (used by Breakout Trend 1–5d)
- 1D: >= 30 closed candles
- 4H: >= 50 closed candles

### Pullback
- 1D: >= 60 closed candles
- 4H: >= 80 closed candles

### Reversal
- 1D: >= 120 closed candles
- 4H: >= 80 closed candles

## 4) Closed-candle buffer rule (implementation guard)
Effective lookback includes a buffer so the last in-progress candle never affects the required minimum of closed candles.

## 5) Interaction with percent_rank
Population definitions remain as specified in feature docs.

```

### `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`

**SHA256:** `36dbb78d4c028f6784320c69b3db8c9227242d6b4c7047a03f0af8f6656dc69c`

```markdown
# SCORE_BREAKOUT_TREND_1_5D — Immediate + Retest (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_BREAKOUT_TREND_1_5D
status: canonical
setup_ids:
  - breakout_immediate_1_5d
  - breakout_retest_1_5d
timeframes:
  - 1d
  - 4h
determinism:
  closed_candle_only: true
  no_lookahead: true
universe_defaults:
  market_cap_usd: {min: 100_000_000, max: 10_000_000_000}
liquidity_gates:
  normal_quote_volume_24h_usd_min: 10_000_000
  btc_risk_off_quote_volume_24h_usd_min: 15_000_000
gates_1d:
  trend_gate: "(ema20_1d > ema50_1d) AND (close_1d > ema20_1d)"
  atr_chaos_gate: "atr_pct_rank_120_1d <= 80.0"
  momentum_gate: "r_7_1d > 0"
  overextension_hard_gate: "dist_ema20_pct_1d < 28.0"
trigger_4h:
  window_bars: 30
  breakout_level: "high_20d_1d"
retest_4h:
  tolerance_pct: 1.0
  window_bars: 12
weights_fixed:
  breakout_distance: 0.35
  volume: 0.35
  trend: 0.15
  bb_score: 0.15
multipliers:
  anti_chase: {start: 30, full: 60, min_mult: 0.75}
  overextension: {start: 12, strong: 20, hard_gate: 28}
  btc_regime:
    risk_on_definition: "(btc_close_1d > btc_ema50_1d) AND (btc_ema20_1d > btc_ema50_1d)"
    risk_off_multiplier: 0.85
```

## 0) Ziel
Kurzfristige Trendfolge-Setups (Hold 1–5 Tage), Breakout aus 1D-Struktur mit 4H-Bestätigung, inkl.:
- Immediate: Breakout bestätigt in der aktuellen “fresh” 4H-Window
- Retest: Breakout + Retest/Touch + Reclaim in definierter Zone

Alle Regeln sind deterministisch und verwenden ausschließlich **abgeschlossene** 1D/4H Candles.

---

## 1) Zeitindizes & Closed-Candle Realität
### 1.1 Indizes
- `t1d`: Index der **letzten abgeschlossenen** 1D Candle
- `t4h`: Index der **letzten abgeschlossenen** 4H Candle

Regel: Alle Referenzen auf “current” meinen **last closed**.

### 1.2 No Lookahead
Kein Feature, Gate oder Score darf Candles mit Index > `t1d` (1D) bzw. > `t4h` (4H) verwenden.

---

## 2) Universe & Setup-übergreifende Hard Gates

### 2.1 Market Cap Universe (CMC)
Canonical Default für diesen Setup-Typ:
- `100M <= market_cap_usd <= 10B`

### 2.2 Liquidity Gates (CMC quoteVol24h USD)
Die Gates nutzen die konfigurierte Volume-Quelle (Default: MEXC `quote_volume_24h`; optional global fallback wenn konfiguriert).
- Normal: `quote_volume_24h_usd >= 10_000_000`
- BTC Risk-Off Override: `quote_volume_24h_usd >= 15_000_000` (nur wenn BTC Risk-Off)

> Der genaue Feldname im Code kann abweichen; canonical meint Quote-Volumen in USD.

### 2.3 Configurable volume source for scoring
- `scoring.volume_source = mexc` (default): verwende MEXC `quote_volume_24h` für score-nahe Liquiditäts-/Penalty-Checks.
- `scoring.volume_source = global_fallback_mexc`: verwende `global_volume_24h_usd` wenn vorhanden, sonst MEXC `quote_volume_24h`.
- Output rows enthalten `volume_source_used` (`global` | `mexc`) zur deterministischen Nachvollziehbarkeit.

---

## 3) Setup-spezifische 1D Gates (Hard)

### 3.1 Trend Gate (1D)
Setup ist nur zulässig wenn:
- `ema20_1d > ema50_1d`
- `close_1d > ema20_1d`

### 3.2 ATR Chaos Gate (1D)
Setup ist nur zulässig wenn:
- `atr_pct_rank_120_1d <= 80.0`

**Definition `atr_pct_rank_120_1d`:**
- `atr_pct_1d[t] = atr_1d[t] / close_1d[t] * 100`
- Ranking wird als rolling percent_rank über die letzten 120 **abgeschlossenen** 1D Candles berechnet.
- Tie-Handling: average-rank (siehe `FEATURES/FEAT_PERCENT_RANK`)

### 3.3 Momentum Gate (1D)
Setup ist nur zulässig wenn:
- `r_7_1d > 0`

### 3.4 Overextension Hard Gate (1D)
Setup ist nur zulässig wenn:
- `dist_ema20_pct_1d < 28.0`

---

## 4) Breakout Level (1D Struktur)

### 4.1 Definition `high_20d_1d`
Sei `t1d` der Index der letzten abgeschlossenen 1D Candle.

Dann:
- `high_20d_1d = max(high_1d[t1d-20 .. t1d-1])`

Wichtig:
- Die aktuelle (letzte abgeschlossene) 1D Candle **t1d** ist **nicht** Teil des 20D-High-Fensters.
- Das verhindert Lookahead und “self-referential” Levels.

---

## 5) Trigger-Definition (4H lookback window)

### 5.1 Trigger Window (4H)
Sei `t4h` der Index der letzten abgeschlossenen 4H Candle.

Das Trigger-Fenster umfasst die letzten `N` abgeschlossenen 4H Candles mit
- `N = trigger_4h_lookback_bars`
- canonical default: `N = 30` (≈ 5 Tage)

Window:
- `[t4h-(N-1) .. t4h]`

### 5.2 Trigger Condition
- `triggered = any(close_4h[i] > high_20d_1d for i in [t4h-(N-1) .. t4h])`

Wenn `triggered == false`:
- Setup ist **invalid** (nicht in Top-Listen).

---

## 6) Retest Setup (Break-and-Retest)

### 6.1 Retest Zone
`retest_tolerance_pct = 1.0%` (default)

- `zone_low  = high_20d_1d * (1 - 0.01)`
- `zone_high = high_20d_1d * (1 + 0.01)`

### 6.2 Breakout-Indizes im Trigger Window
Im Trigger Window `[t4h-(N-1) .. t4h]`:
- `first_breakout_idx = first index i where close_4h[i] > high_20d_1d`
- `last_breakout_idx = last index i where close_4h[i] > high_20d_1d`

Usage:
- Immediate-Setup verwendet `last_breakout_idx` (jüngster Breakout im 5D-Fenster).
- Retest-Setup verwendet `first_breakout_idx` als Startpunkt des 12x4H-Fensters.

### 6.3 Retest Search Window
Suche in den nächsten 12 abgeschlossenen 4H Candles nach dem ersten Breakout:
- `j in [first_breakout_idx+1 .. first_breakout_idx+12]`

### 6.4 Retest Valid
Retest ist **valid**, wenn es ein `j` im Window gibt mit:
- Touch: `low_4h[j] >= zone_low AND low_4h[j] <= zone_high`
- Reclaim: `close_4h[j] >= high_20d_1d`

### 6.5 Retest Hard Invalidation
Retest ist **invalid**, wenn im Retest Window irgendeine Candle `k` gilt:
- `close_4h[k] < high_20d_1d`

---

## 7) Component Scores (0..100) & Formeln

> Alle Scores werden deterministisch berechnet und am Ende geclamped.

### 7.1 Breakout Distance Score (4H close vs 1D level)
Input:
- `dist_pct = ((close_4h_last_closed / high_20d_1d) - 1) * 100`

Piecewise-Kurve (canonical defaults):
- `floor = -5.0`
- `min_breakout = 2.0`
- `ideal_breakout = 5.0`
- `max_breakout = 20.0`

Mapping:
- Wenn `dist_pct <= floor` → `0`
- Wenn `floor < dist_pct < 0` → `30 * (dist_pct - floor) / (0 - floor)`
- Wenn `0 <= dist_pct < min_breakout` → `30 + 40 * (dist_pct / min_breakout)`
- Wenn `min_breakout <= dist_pct <= ideal_breakout` → `70 + 30 * (dist_pct - min_breakout) / (ideal_breakout - min_breakout)`
  - falls Nenner `<=0` → `100`
- Wenn `ideal_breakout < dist_pct <= max_breakout` → `100 * (1 - (dist_pct - ideal_breakout) / (max_breakout - ideal_breakout))`
  - falls Nenner `<=0` → `0`
- Sonst → `0`

### 7.2 Volume Score (combined spike)
Spikes:
- `spike_1d = volume_quote_spike_1d` (SMA exclude current closed candle)
- `spike_4h = volume_quote_spike_4h` (SMA exclude current closed candle)
- `spike_combined = 0.7*spike_1d + 0.3*spike_4h`

Mapping:
- Wenn `spike_combined < 1.5` → `0`
- Wenn `spike_combined >= 2.5` → `100`
- Sonst linear:
  - `((spike_combined - 1.5) / (2.5 - 1.5)) * 100`

### 7.3 Trend Score (Option A)
Voraussetzung: Trend Gate ist erfüllt (sonst Setup invalid).
- `trend_score = 70`
- `+15` wenn `close_4h_last_closed > ema20_4h_last_closed`
- `+15` wenn `ema20_4h_last_closed > ema50_4h_last_closed`
- cap: `trend_score = min(trend_score, 100)`

### 7.4 BB Score (Compression Bonus)
Input:
- `r = bb_width_rank_120_4h` im Percent-Scale `[0..100]`
- Defensive compatibility: wenn `r <= 1.0`, dann `rank_pct = r*100`

Mapping auf `rank_pct`:
- Wenn `rank_pct <= 20` → `100`
- Wenn `20 < rank_pct <= 60` → linear `100 -> 40`:
  - `100 - (rank_pct - 20) * (100-40) / (60-20)`
- Wenn `rank_pct > 60` → `0`

### 7.5 Base Score (fixed weights)
Fixed weights:
- breakout_distance: `0.35`
- volume: `0.35`
- trend: `0.15`
- bb_score: `0.15`

- `base_score = 0.35*breakout_distance_score + 0.35*volume_score + 0.15*trend_score + 0.15*bb_score`

---

## 8) Multipliers (applied at end)

### 8.1 Anti-Chase Multiplier (based on r_7_1d)
Parameters:
- start = 30
- full = 60
- min_mult = 0.75

Piecewise:
- Wenn `r_7_1d < 30` → `1.0`
- Wenn `30 <= r_7_1d <= 60` → linear `1.0 -> 0.75`
- Wenn `r_7_1d > 60` → `0.75`

### 8.2 Overextension Multiplier (based on dist_ema20_pct_1d)
Parameters:
- penalty_start = 12
- strong = 20
- hard_gate = 28 (bereits in Gates)

Piecewise:
- Wenn `d < 12` → `1.0`
- Wenn `12 <= d <= 20` → linear `1.0 -> 0.85`
- Wenn `20 < d < 28` → linear `0.85 -> 0.70`
- Wenn `d >= 28` → invalid (Hard Gate)

### 8.3 BTC Regime Multiplier (forced)
BTC Risk-On Definition:
- `btc_risk_on = (btc_close_1d > btc_ema50_1d) AND (btc_ema20_1d > btc_ema50_1d)`

Wenn `btc_risk_on == true`:
- `btc_multiplier = 1.0`

Wenn `btc_risk_on == false` (Risk-Off):
- `rs_override = ((alt_r7_1d - btc_r7_1d) >= 7.5) OR ((alt_r3_1d - btc_r3_1d) >= 3.5)`
- `liq_ok = quote_volume_24h_usd >= 15_000_000`
- `btc_multiplier = 0.85` wenn `rs_override AND liq_ok`, sonst `0.75`
- Kandidat bleibt immer gelistet (kein Hard-Exclude durch BTC-Regime)

---

## 9) Final Score
- `final_score = clamp(base_score * anti_chase_multiplier * overextension_multiplier * btc_multiplier, 0..100)`

---

## 10) Execution Gate (MEXC orderbook)
- Discovery candidates remain listed even if execution gate fails.
- Gate is controlled by `execution_gates.mexc_orderbook.*` config.
- `execution_gate_pass = true` iff all are true:
  1) `orderbook_ok == true`
  2) `spread_pct <= max_spread_pct`
  3) for each configured band `b`: `min(depth_bid_b_pct_usd, depth_ask_b_pct_usd) >= min_depth_usd[b]`
- Fail reason enum is closed and deterministic:
  - `ORDERBOOK_MISSING`
  - `SPREAD_TOO_WIDE`
  - `DEPTH_TOO_LOW_0_5`
  - `DEPTH_TOO_LOW_1_0`

---

## 11) Setup IDs & Output-Pflichtfelder

### 11.1 Setup IDs
- `breakout_immediate_1_5d`
- `breakout_retest_1_5d`

### 11.2 Setup-spezifische Zusatzfelder (nicht globales Row-Minimum)
Für dieses Setup werden typischerweise zusätzliche Diagnose-/Scoring-Felder pro Candidate-Row geführt, z. B.:
- `base_score`, `final_score`
- Level & Distanz: `high_20d_1d`, `dist_pct`
- Volume: `volume_quote_spike_1d`, `volume_quote_spike_4h`, `spike_combined`
- ATR: `atr_pct_rank_120_1d`
- BB: `bb_width_pct_4h`, `bb_width_rank_120_4h`
- Multipliers: `anti_chase_multiplier`, `overextension_multiplier`, `btc_multiplier`
- BTC Regime Flags: `btc_state`, `btc_rs_override`, `btc_liq_ok_risk_off`
- Gates/Flags: `triggered`, `retest_valid`, `retest_invalidated` (wo relevant)

Wichtig:
- Das globale Pflichtfeld-Minimum für `trade_candidates` wird ausschließlich in `docs/canonical/OUTPUT_SCHEMA.md` definiert.
- Dieses Setup-Dokument erweitert die globale Row-Semantik nur um setup-spezifische Felder; es überschreibt das globale Minimum nicht.

### 11.3 Dedup (global)
Wenn ein Symbol beide Setups erfüllt:
- Retest wird bevorzugt (Tie-break).
Global Top-N dedup & Setup-Gewichte sind in `GLOBAL_RANKING_TOP20.md` zu definieren.

---

## 12) Test/Fixture Anker
Golden fixtures & deterministische Tabellen liegen in:
- `docs/canonical/VERIFICATION_FOR_AI.md`

```

### `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`

**SHA256:** `aea45f306198fca4f3805440fba85849c59fc843c213465c7e4595cd46abfcb8`

```markdown
# Global Ranking — Top-N, Dedup, Setup Weights (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_GLOBAL_RANKING_TOP20
status: canonical
global_top_n_default: 20
phase_policy:
  phase1_single_setup_type: true
  setup_weights_active: false
setup_weights_by_category_reserved_for_future:
  breakout_trend: 1.0
  pullback: 0.9
  reversal: 0.8
setup_id_to_weight_category_active:
  breakout_immediate_1_5d: breakout_trend
  breakout_retest_1_5d: breakout_trend
dedup:
  per_symbol_max_rows: 1
  prefer_setup_id_order:
    - breakout_retest_1_5d
    - breakout_immediate_1_5d
setup_preference:
  mapping:
    breakout_retest_1_5d: 1
    breakout_immediate_1_5d: 0
  default_for_unknown_setup_id: -1
top_n_selection_order_before_truncation:
  - key: global_score
    order: desc
  - key: setup_preference
    order: desc
  - key: symbol
    order: asc
composition:
  final_ordering_defined_by: docs/canonical/LIQUIDITY/RE_RANK_RULE.md
```

## 0) Purpose
Define how per-setup scores become a single **deduplicated** global list (Top-N input list).

Important:
- This document defines **selection + dedup + top-n inclusion**.
- Final ordering of the published list is defined by `LIQUIDITY/RE_RANK_RULE.md`.

## 1) Inputs
Scored setup rows, each with:
- `symbol`
- `setup_id`
- `final_score` (0..100)

## 2) Setup weights (Phase policy)
Phase 1 (current canonical):
- `setup_weights_active = false`
- Effective weight is `1.0` for all active setup_ids.

Reserved for future multi-setup phases:
- breakout_trend: 1.0
- pullback: 0.9
- reversal: 0.8

If/when pullback/reversal setups are added, their `setup_id` strings must be added to the Machine Header mapping and the weights activation must be explicitly switched on.

## 3) Global score definition
For a given symbol:
- `global_score(symbol) = max(final_score over all valid setups for symbol)`
- `best_setup_id = argmax(final_score)`

## 4) Setup preference (deterministic)
- `setup_preference(setup_id)` is defined by the mapping in the Machine Header and is used only as a deterministic tie-breaker.

## 5) Dedup rule (one row per symbol)
1) For each symbol, select the row with the highest `final_score`.
2) If multiple rows tie on `final_score`, select the one whose `setup_id` appears earliest in `prefer_setup_id_order`.
3) If still tied, tie-break by `setup_id` lexicographically ascending.
4) If still tied, tie-break by `symbol` ascending.

## 6) Top-N selection (deterministic inclusion)
Before truncation, order rows using **exactly**:
1) `global_score` descending
2) `setup_preference` descending
3) `symbol` ascending

Then take the first `global_top_n` rows (default 20).

## 7) Final ordering
After top-n inclusion is determined, apply `LIQUIDITY/RE_RANK_RULE.md` to produce the final published ordering.

```

### `docs/canonical/SCORING/DISCOVERY_TAG.md`

**SHA256:** `27e313afbaefa4f837a7404436389ce850f52cf0f0fb5995942b586db6960809`

```markdown
# Discovery Tag — “New coin” identification (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_DISCOVERY_TAG
status: canonical
default_max_age_days: 180
timestamps_unit: ms
discovery_source_allowed:
  - cmc_date_added
  - first_seen_ts
  - null
```

## Age computation (ms)
- `age_days = floor((asof_ts_ms - source_ts_ms) / 86_400_000)`

## Output
- `discovery_source` is `null` if neither source exists.

```

---

## 📚 Additional Resources

- **Code Map:** `docs/code_map.md` (detailed structural overview)
- **Specifications:** `docs/spec.md` (technical master spec)
- **Dev Guide:** `docs/dev_guide.md` (development workflow)
- **Latest Reports:** `reports/YYYY-MM-DD.md` (daily scanner outputs)

---

_Generated by GitHub Actions • 2026-03-08 16:06 UTC_
