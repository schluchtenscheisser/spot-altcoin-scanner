# Spot Altcoin Scanner • GPT Snapshot

**Generated:** 2026-02-19 07:53 UTC  
**Commit:** `9a538a2` (9a538a23ee12d53c914564c79cc4d9b1d844bf84)  
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
| `scanner/clients/__init__.py` | - | - |
| `scanner/clients/mapping.py` | `MappingResult`, `SymbolMapper` | - |
| `scanner/clients/marketcap_client.py` | `MarketCapClient` | - |
| `scanner/clients/mexc_client.py` | `MEXCClient` | - |
| `scanner/config.py` | `ScannerConfig` | `load_config`, `validate_config` |
| `scanner/main.py` | - | `parse_args`, `main` |
| `scanner/pipeline/__init__.py` | - | `run_pipeline` |
| `scanner/pipeline/backtest_runner.py` | - | - |
| `scanner/pipeline/excel_output.py` | `ExcelReportGenerator` | - |
| `scanner/pipeline/features.py` | `FeatureEngine` | - |
| `scanner/pipeline/filters.py` | `UniverseFilters` | - |
| `scanner/pipeline/ohlcv.py` | `OHLCVFetcher` | - |
| `scanner/pipeline/output.py` | `ReportGenerator` | - |
| `scanner/pipeline/runtime_market_meta.py` | `RuntimeMarketMetaExporter` | - |
| `scanner/pipeline/scoring/__init__.py` | - | - |
| `scanner/pipeline/scoring/breakout.py` | `BreakoutScorer` | `score_breakouts` |
| `scanner/pipeline/scoring/pullback.py` | `PullbackScorer` | `score_pullbacks` |
| `scanner/pipeline/scoring/reversal.py` | `ReversalScorer` | `score_reversals` |
| `scanner/pipeline/scoring/weights.py` | - | `load_component_weights` |
| `scanner/pipeline/shortlist.py` | `ShortlistSelector` | - |
| `scanner/pipeline/snapshot.py` | `SnapshotManager` | - |
| `scanner/tools/validate_features.py` | - | `_is_number`, `_error`, `_emit`, `validate_features` |
| `scanner/utils/__init__.py` | - | - |
| `scanner/utils/io_utils.py` | - | `load_json`, `save_json`, `get_cache_path`, `cache_exists`, `load_cache` ... (+1 more) |
| `scanner/utils/logging_utils.py` | - | `setup_logger`, `get_logger` |
| `scanner/utils/raw_collector.py` | - | `collect_raw_ohlcv`, `collect_raw_marketcap`, `collect_raw_features` |
| `scanner/utils/save_raw.py` | - | `save_raw_snapshot` |
| `scanner/utils/time_utils.py` | - | `utc_now`, `utc_timestamp`, `utc_date`, `parse_timestamp`, `timestamp_to_ms` ... (+1 more) |

**Statistics:**
- Total Modules: 29
- Total Classes: 16
- Total Functions: 31

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

**SHA256:** `4e3e218240cde97de5f9a89570dd3ad48135f91b81655ddc87e7761325e18bd4`

```markdown
# Spot Altcoin Scanner (v1)

**Status:** ✅ MVP Complete  
**Last Updated:** 2026-01-17

Scanner for short-term trading setups in MidCap Altcoins on MEXC Spot USDT markets.

---

## What It Does

Scans **1837 MEXC USDT pairs** daily and identifies three types of trading setups:

1. **🔄 Reversal** (Priority) - Downtrend → Base → Reclaim
2. **📈 Breakout** - Range break + volume confirmation  
3. **🔽 Pullback** - Trend continuation after retracement

**Filters for:**
- Market Cap: 100M–3B USD (MidCaps)
- Liquidity: Minimum 24h volume
- Exclusions: Stablecoins, wrapped tokens, leveraged tokens

**Outputs:**
- Daily Markdown report: `reports/YYYY-MM-DD.md`
- JSON data: `reports/YYYY-MM-DD.json`
- Snapshot for backtesting: `snapshots/history/YYYY-MM-DD.json`

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/schluchtenscheisser/spot-altcoin-scanner.git
cd spot-altcoin-scanner
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

For local testing/development (same baseline as CI):
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Set API Key

Get a free API key from [CoinMarketCap](https://coinmarketcap.com/api/) and set it:
```bash
export CMC_API_KEY='your-api-key-here'
```

### 4. Run Scanner
```bash
# Fast mode (uses cache if available)
python -m scanner.main --mode fast

# Standard mode (fresh API calls)
python -m scanner.main --mode standard
```

### 5. View Results
```bash
# Human-readable report
cat reports/$(date +%Y-%m-%d).md

# Machine-readable JSON
cat reports/$(date +%Y-%m-%d).json
```

---

## Automated Daily Runs

The scanner runs automatically every day at **4:10 AM UTC** via GitHub Actions.

**To trigger manually:**
1. Go to **Actions** tab in GitHub
2. Select **"Daily Scanner Run"**
3. Click **"Run workflow"**

Reports are automatically committed to the repository.

---

## Pull Request CI


### Outage / Quota Fallback Policy

If live data providers fail (API outage/quota):
- Use last-known cache **only when available**.
- Mark run metadata as degraded with freshness timestamps.
- If no cache is available, fail explicitly (no silent partial output).


A dedicated GitHub Actions workflow (`.github/workflows/pr-ci.yml`) runs on every pull request targeting `main`.

Current PR gate:
- `pytest -q`

Recommended repository setting (GitHub → Settings → Branches → `main`):
- Enable **Require status checks to pass before merging**
- Mark the **PR CI / pytest** check as required
- (Optional) Enable **Require branches to be up to date before merging**

---


### CI Dependency Policy

PR CI installs dependencies **explicitly** from:
- `requirements.txt`
- `requirements-dev.txt` (includes `pytest`)

This avoids implicit runner assumptions and keeps CI reproducible.

## Example Output
```markdown
# Spot Altcoin Scanner Report
**Date:** 2026-01-17

## Summary
- Reversal Setups: 45 scored
- Breakout Setups: 38 scored
- Pullback Setups: 42 scored

## 🔄 Top Reversal Setups

### 1. EXAMPLEUSDT - Score: 87.5
**Components:**
- Drawdown: 95.0
- Base: 85.0
- Reclaim: 90.0
- Volume: 80.0

**Analysis:**
- Strong drawdown setup (68% from ATH)
- Clean base formation detected
- Reclaimed EMAs (5.2% above EMA50)
- Strong volume (2.8x average)
```

---

## Configuration

Edit `config/config.yml` to customize:

- **Filters:** Market cap range, liquidity thresholds
- **Shortlist:** Number of symbols to analyze
- **Scoring:** Component weights, penalties
- **Output:** Report format, top N count

See `docs/config.md` for details.

---

## Architecture
```
scanner/
├── clients/          # API clients (MEXC, CMC)
│   ├── mexc_client.py
│   ├── marketcap_client.py
│   └── mapping.py
├── pipeline/         # Core pipeline
│   ├── filters.py
│   ├── shortlist.py
│   ├── ohlcv.py
│   ├── features.py
│   ├── scoring/      # Setup scorers
│   │   ├── reversal.py
│   │   ├── breakout.py
│   │   └── pullback.py
│   ├── output.py
│   └── snapshot.py
├── utils/            # Utilities
│   ├── logging_utils.py
│   ├── time_utils.py
│   └── io_utils.py
├── config.py         # Configuration
└── main.py           # Entry point
```

**Pipeline Flow:**
1. Fetch MEXC universe (1837 pairs)
2. Map to CoinMarketCap data
3. Apply filters (MidCaps, liquidity)
4. Create shortlist (top 100 by volume)
5. Fetch OHLCV data (1d + 4h)
6. Compute features (EMAs, ATR, returns, etc.)
7. Score setups (3 independent scores)
8. Generate reports
9. Save snapshot

---

## Documentation

### For Users:
- **README.md** (this file) - Getting started
- **reports/YYYY-MM-DD.md** - Daily scanner results

### For Developers:
- **docs/dev_guide.md** - Development workflow
- **docs/spec.md** - Technical specification
- **docs/project_phases.md** - Development roadmap
- **docs/scoring.md** - Scoring algorithms
- **snapshots/gpt/** - Session snapshots

**New to this project?** Start with `docs/dev_guide.md`.

---

## Development Status

### ✅ Completed (v1.0 MVP):
- **Phase 1:** Foundation (Utils + Config)
- **Phase 2:** Data Clients (MEXC + CMC)
- **Phase 3:** Mapping Layer
- **Phase 4:** Pipeline (Filters, OHLCV, Features)
- **Phase 5:** Scoring (Reversal, Breakout, Pullback)
- **Phase 6:** Output (Reports, Snapshots, Automation)

### 📋 Roadmap:
- **Phase 7:** Backtesting & validation
- **Phase 8+:** Extensions (regime filters, on-chain data, dashboard)

See `docs/future_extensions.md` for details.

---

## Performance

**Typical Run (with cache):**
- Execution time: ~4-5 minutes
- Symbols processed: 1837 → ~400 → 100 → ~95
- Reports generated: Markdown + JSON
- Snapshot size: ~245 KB

**API Usage:**
- MEXC: Cached daily (free)
- CMC: 1 call/day (free tier: 333 calls/month)

---

## Requirements

- Python 3.11+
- CMC API Key (free tier)
- Internet connection (for API calls)

**Dependencies:**
- requests
- PyYAML
- pandas
- numpy
- loguru

---

## Contributing

This is a personal trading research tool. Contributions are not currently accepted, but you're welcome to fork and adapt for your own use.

---

## Disclaimer

**This is a research tool, not financial advice.**

- No buy/sell recommendations
- No automated trading/execution
- No guaranteed returns
- Always do your own research
- Trade at your own risk

The scanner identifies potential setups based on technical analysis. Market conditions change, and past performance does not indicate future results.

---

## License

Private use only. See repository license for details.

---

## Support

For issues or questions:
1. Check `docs/` folder
2. Review `logs/scanner_YYYY-MM-DD.log`
3. See GitHub Issues

---

**Built with:** Python | MEXC API | CoinMarketCap API | GitHub Actions

**Last Scanner Run:** Check `reports/` folder for latest date

```

### `config/config.yml`

**SHA256:** `2c713e6cdd7d7a3465c6646ddebd4b68c6741d45f32b425631f118343479fbf0`

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
    min_usd: 100000000      # 100M
    max_usd: 3000000000     # 3B
  volume:
    min_quote_volume_24h: 1000000
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
  volume_sma_period: 7
  volume_spike_threshold: 1.5
  drawdown_lookback_days: 365

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
  forward_return_days: [7, 14, 30]
  max_holding_days: 30
  entry_price: "close"
  exit_price: "close_forward"
  slippage_bps: 10

logging:
  level: "INFO"
  file: "logs/scanner.log"
  log_to_file: true

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

**SHA256:** `f9f1aaeeb68b48ecb4f7635fff7ccfae15230353f497afc027d4ca5f05260260`

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
          # Use force-with-lease to handle potential conflicts
          push_options: '--force-with-lease'
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

**SHA256:** `2c41d23986f93d60983b02ceea884043cdd4db00db53641145907dd031e24971`

```yaml
name: gpt-snapshot

on:
  push:
    branches: [ main ]
  workflow_dispatch:
  release:
    types: [ published ]

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
          push_options: '--force-with-lease'
      
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

**SHA256:** `8929dbed8f8bd92be416aa823ff0deefa630b1ab4953baa95fde41b485facddd`

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
        return self.raw.get("general", {}).get("shortlist_size", 100)
    
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
    
    # Universe Filters
    @property
    def market_cap_min(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("min_usd", 100_000_000)
    
    @property
    def market_cap_max(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("max_usd", 3_000_000_000)
    
    @property
    def min_quote_volume_24h(self) -> int:
        return self.raw.get("universe_filters", {}).get("volume", {}).get("min_quote_volume_24h", 1_000_000)
    
    @property
    def min_history_days_1d(self) -> int:
        return self.raw.get("universe_filters", {}).get("history", {}).get("min_history_days_1d", 60)
    
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
    
    return errors

```

### `scanner/clients/mexc_client.py`

**SHA256:** `8ed9807845616371013fd9ae0137e05a8bf2db2fdf306a41196e7f35aa57fd20`

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

### `scanner/pipeline/shortlist.py`

**SHA256:** `c1d072e6fad5550b342acbad20e3abbf02d01a41ba4d2059754cb51f2da0c4f0`

```python
"""
Shortlist Selection (Cheap Pass)
=================================

Reduces filtered universe to a shortlist for expensive operations (OHLCV fetch).
Uses cheap metrics (24h volume) to rank and select top N candidates.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ShortlistSelector:
    """Selects top candidates based on volume for OHLCV processing."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize shortlist selector.
        
        Args:
            config: Config dict with 'shortlist' section
        """
        self.config = config.get('shortlist', {})
        general_cfg = config.get('general', {})

        # Default: Top 100 by volume
        self.max_size = int(general_cfg.get('shortlist_size', self.config.get('max_size', 100)))
        
        # Minimum size (even if fewer pass filters)
        self.min_size = self.config.get('min_size', 10)
        
        logger.info(f"Shortlist initialized: max_size={self.max_size}, min_size={self.min_size}")
    
    def select(self, filtered_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Select top N symbols by 24h volume.
        
        Args:
            filtered_symbols: List of symbols that passed filters
                Each dict must have:
                - symbol: str
                - base: str
                - quote_volume_24h: float
                - market_cap: float
        
        Returns:
            Shortlist (top N by volume)
        """
        if not filtered_symbols:
            logger.warning("No symbols to shortlist (empty input)")
            return []
        
        # Sort by volume (descending)
        sorted_symbols = sorted(
            filtered_symbols,
            key=lambda x: x.get('quote_volume_24h', 0),
            reverse=True
        )
        
        # Take top N
        shortlist = sorted_symbols[:self.max_size]
        
        logger.info(f"Shortlist selected: {len(shortlist)} symbols from {len(filtered_symbols)} "
                   f"(top {len(shortlist)/len(filtered_symbols)*100:.1f}% by volume)")
        
        # Log volume range
        if shortlist:
            max_vol = shortlist[0].get('quote_volume_24h', 0)
            min_vol = shortlist[-1].get('quote_volume_24h', 0)
            logger.info(f"Volume range: ${max_vol/1e6:.2f}M - ${min_vol/1e6:.2f}M")
        
        return shortlist
    
    def get_shortlist_stats(
        self,
        filtered_symbols: List[Dict[str, Any]],
        shortlist: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about shortlist selection.
        
        Args:
            filtered_symbols: Input (post-filter)
            shortlist: Output (post-shortlist)
        
        Returns:
            Stats dict
        """
        if not filtered_symbols:
            return {
                'input_count': 0,
                'shortlist_count': 0,
                'reduction_rate': '0%',
                'volume_coverage': '0%'
            }
        
        # Volume stats
        total_volume = sum(s.get('quote_volume_24h', 0) for s in filtered_symbols)
        shortlist_volume = sum(s.get('quote_volume_24h', 0) for s in shortlist)
        
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

### `scanner/pipeline/filters.py`

**SHA256:** `a5637c2004ebdedc79757a5c610a5e96b642cbfcbe1ae37b1c3901d529e2db86`

```python
"""
Universe Filtering
==================

Filters the MEXC universe to create a tradable shortlist:
1. Market Cap Filter (100M - 3B USD)
2. Liquidity Filter (minimum volume)
3. Exclusions (stablecoins, wrapped tokens, leveraged tokens)
"""

import logging
from typing import List, Dict, Any, Optional

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

        mcap_cfg = universe_cfg.get('market_cap', {})
        volume_cfg = universe_cfg.get('volume', {})
        history_cfg = universe_cfg.get('history', {})

        # Market Cap bounds (in USD)
        self.mcap_min = mcap_cfg.get('min_usd', legacy_filters.get('mcap_min', 100_000_000))  # 100M
        self.mcap_max = mcap_cfg.get('max_usd', legacy_filters.get('mcap_max', 3_000_000_000))  # 3B

        # Liquidity (24h volume in USDT)
        self.min_volume_24h = volume_cfg.get('min_quote_volume_24h', legacy_filters.get('min_volume_24h', 1_000_000))

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

        if 'exclusion_patterns' in legacy_filters:
            # Legacy override is key-presence based: [] explicitly disables exclusions.
            legacy_patterns = legacy_filters.get('exclusion_patterns') or []
            self.exclusion_patterns = [str(p).upper() for p in legacy_patterns]
        else:
            self.exclusion_patterns = []
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
        
        logger.info(f"Filters initialized: MCAP {self.mcap_min/1e6:.0f}M-{self.mcap_max/1e9:.1f}B, "
                   f"Min Volume {self.min_volume_24h/1e6:.1f}M")
    
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
        
        # Step 1: Market Cap filter
        filtered = self._filter_mcap(symbols_with_data)
        logger.info(f"After MCAP filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 2: Quote asset filter (USDT-only or stablecoin allowlist)
        filtered = self._filter_quote_assets(filtered)
        logger.info(f"After Quote filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 3: Liquidity filter
        filtered = self._filter_liquidity(filtered)
        logger.info(f"After Liquidity filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 4: Exclusions
        filtered = self._filter_exclusions(filtered)
        logger.info(f"After Exclusions filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")
        
        logger.info(f"Final universe: {len(filtered)} symbols "
                   f"(filtered out {original_count - len(filtered)})")
        
        return filtered
    
    def _filter_mcap(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter by market cap range."""
        filtered = []
        
        for sym_data in symbols:
            mcap = sym_data.get('market_cap')
            
            # Skip if no market cap data
            if mcap is None:
                continue
            
            # Check bounds
            if self.mcap_min <= mcap <= self.mcap_max:
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

    def _filter_liquidity(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter by minimum 24h volume."""
        filtered = []
        
        for sym_data in symbols:
            volume = sym_data.get('quote_volume_24h', 0)
            
            if volume >= self.min_volume_24h:
                filtered.append(sym_data)
        
        return filtered
    
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
        mcap_pass = len(self._filter_mcap(symbols))
        quote_pass = len(self._filter_quote_assets(symbols))
        liquidity_pass = len(self._filter_liquidity(symbols))
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

### `scanner/pipeline/excel_output.py`

**SHA256:** `ce8f419531a271208c4b16ff269df7361a7ab2c38a7d5196aac5d3c7bfb9227d`

```python
"""
Excel Output Generation
=======================

Generates Excel workbooks with multiple sheets for daily scanner results.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelReportGenerator:
    """Generates Excel reports with multiple sheets."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Excel report generator.
        
        Args:
            config: Config dict with 'output' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            output_config = config.raw.get('output', {})
        else:
            output_config = config.get('output', {})
        
        self.reports_dir = Path(output_config.get('reports_dir', 'reports'))
        self.top_n = output_config.get('top_n_per_setup', 10)
        
        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Excel Report Generator initialized: reports_dir={self.reports_dir}")
    
    def generate_excel_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None
    ) -> Path:
        """
        Generate Excel workbook with 4 sheets.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata (universe size, etc.)
        
        Returns:
            Path to saved Excel file
        """
        logger.info(f"Generating Excel report for {run_date}")
        
        # Create workbook
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # Sheet 1: Summary
        self._create_summary_sheet(
            wb, run_date, 
            len(reversal_results), 
            len(breakout_results), 
            len(pullback_results),
            metadata
        )
        
        # Sheet 2: Reversal Setups
        self._create_setup_sheet(
            wb, "Reversal Setups", 
            reversal_results[:self.top_n],
            ['Drawdown', 'Base', 'Reclaim', 'Volume']
        )
        
        # Sheet 3: Breakout Setups
        self._create_setup_sheet(
            wb, "Breakout Setups",
            breakout_results[:self.top_n],
            ['Breakout', 'Volume', 'Trend', 'Momentum']
        )
        
        # Sheet 4: Pullback Setups
        self._create_setup_sheet(
            wb, "Pullback Setups",
            pullback_results[:self.top_n],
            ['Trend', 'Pullback', 'Rebound', 'Volume']
        )
        
        # Save
        excel_path = self.reports_dir / f"{run_date}.xlsx"
        wb.save(excel_path)
        logger.info(f"Excel report saved: {excel_path}")
        
        return excel_path
    
    def _create_summary_sheet(
        self,
        wb: Workbook,
        run_date: str,
        reversal_count: int,
        breakout_count: int,
        pullback_count: int,
        metadata: Dict[str, Any] = None
    ):
        """Create Summary sheet with run statistics."""
        ws = wb.create_sheet("Summary", 0)
        
        # Header
        ws['A1'] = 'Metric'
        ws['B1'] = 'Value'
        
        # Style header
        for cell in ['A1', 'B1']:
            ws[cell].font = Font(bold=True, size=12)
            ws[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            ws[cell].font = Font(bold=True, size=12, color="FFFFFF")
            ws[cell].alignment = Alignment(horizontal='center')
        
        # Data rows
        row = 2
        ws[f'A{row}'] = 'Run Date'
        ws[f'B{row}'] = run_date
        row += 1
        
        ws[f'A{row}'] = 'Generated At'
        ws[f'B{row}'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        row += 1
        
        # Add metadata if available
        if metadata:
            ws[f'A{row}'] = 'Total Symbols Scanned'
            ws[f'B{row}'] = metadata.get('universe_size', 'N/A')
            row += 1
            
            ws[f'A{row}'] = 'Symbols Filtered (MidCaps)'
            ws[f'B{row}'] = metadata.get('filtered_size', 'N/A')
            row += 1
            
            ws[f'A{row}'] = 'Symbols in Shortlist'
            ws[f'B{row}'] = metadata.get('shortlist_size', 'N/A')
            row += 1
        
        ws[f'A{row}'] = 'Reversal Setups Found'
        ws[f'B{row}'] = reversal_count
        row += 1
        
        ws[f'A{row}'] = 'Breakout Setups Found'
        ws[f'B{row}'] = breakout_count
        row += 1
        
        ws[f'A{row}'] = 'Pullback Setups Found'
        ws[f'B{row}'] = pullback_count
        row += 1
        
        # Column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
    
    def _create_setup_sheet(
        self,
        wb: Workbook,
        sheet_name: str,
        results: List[Dict[str, Any]],
        component_names: List[str]
    ):
        """
        Create a setup sheet (Reversal/Breakout/Pullback).
        
        Args:
            wb: Workbook object
            sheet_name: Name of the sheet
            results: List of scored setups
            component_names: List of component score names
        """
        ws = wb.create_sheet(sheet_name)
        
        # Headers
        headers = [
            'Rank', 'Symbol', 'Name', 'Price (USDT)', 
            'Market Cap', '24h Volume', 'Score'
        ] + component_names + ['Flags']
        
        # Write headers
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True, size=11)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(bold=True, size=11, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center')
        
        # Data rows
        for rank, result in enumerate(results, 1):
            row_idx = rank + 1
            
            # Basic info
            ws.cell(row=row_idx, column=1, value=rank)
            ws.cell(row=row_idx, column=2, value=result.get('symbol', 'N/A'))
            ws.cell(row=row_idx, column=3, value=result.get('coin_name', 'Unknown'))
            
            # Price
            price = result.get('price_usdt')
            if price is not None:
                ws.cell(row=row_idx, column=4, value=f"${price:.2f}")
            else:
                ws.cell(row=row_idx, column=4, value='N/A')
            
            # Market Cap (abbreviated)
            market_cap = result.get('market_cap')
            if market_cap:
                ws.cell(row=row_idx, column=5, value=self._format_large_number(market_cap))
            else:
                ws.cell(row=row_idx, column=5, value='N/A')
            
            # 24h Volume (abbreviated)
            volume = result.get('quote_volume_24h')
            if volume:
                ws.cell(row=row_idx, column=6, value=self._format_large_number(volume))
            else:
                ws.cell(row=row_idx, column=6, value='N/A')
            
            # Score
            ws.cell(row=row_idx, column=7, value=result.get('score', 0))
            
            # Component scores
            components = result.get('components', {})
            for col_offset, comp_name in enumerate(component_names):
                comp_key = comp_name.lower()
                comp_value = components.get(comp_key, 0)
                ws.cell(row=row_idx, column=8 + col_offset, value=comp_value)
            
            # Flags
            flags = result.get('flags', [])
            if isinstance(flags, list):
                flag_str = ', '.join(flags) if flags else ''
            elif isinstance(flags, dict):
                flag_str = ', '.join([k for k, v in flags.items() if v])
            else:
                flag_str = ''
            ws.cell(row=row_idx, column=8 + len(component_names), value=flag_str)
        
        # Freeze top row
        ws.freeze_panes = 'A2'
        
        # Autofilter
        ws.auto_filter.ref = ws.dimensions
        
        # Column widths
        ws.column_dimensions['A'].width = 6   # Rank
        ws.column_dimensions['B'].width = 14  # Symbol
        ws.column_dimensions['C'].width = 20  # Name
        ws.column_dimensions['D'].width = 13  # Price
        ws.column_dimensions['E'].width = 13  # Market Cap
        ws.column_dimensions['F'].width = 13  # Volume
        ws.column_dimensions['G'].width = 8   # Score
        
        # Component columns
        for i in range(len(component_names)):
            col_letter = get_column_letter(8 + i)
            ws.column_dimensions[col_letter].width = 12
        
        # Flags column
        flags_col = get_column_letter(8 + len(component_names))
        ws.column_dimensions[flags_col].width = 25
    
    def _format_large_number(self, num: float) -> str:
        """
        Format large numbers with M/B suffix.
        
        Args:
            num: Number to format
        
        Returns:
            Formatted string (e.g., "$1.23M", "$4.56B")
        """
        if num >= 1_000_000_000:
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num / 1_000:.2f}K"
        else:
            return f"${num:.2f}"

```

### `scanner/pipeline/__init__.py`

**SHA256:** `e07633302865b89b2f25f0dd6904fb8a55e0776808c129c2169f022d2f71d812`

```python
"""
Pipeline Orchestration
======================

Orchestrates the full daily scanning pipeline.
"""

from __future__ import annotations
import logging
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
from .scoring.breakout import score_breakouts
from .scoring.pullback import score_pullbacks
from .output import ReportGenerator
from .snapshot import SnapshotManager
from .runtime_market_meta import RuntimeMarketMetaExporter

logger = logging.getLogger(__name__)


def run_pipeline(config: ScannerConfig) -> None:
    """
    Orchestrates the full daily pipeline:
    1. Fetch universe (MEXC Spot USDT)
    2. Fetch market cap listings
    3. Run mapping layer
    4. Apply hard filters (market cap, liquidity, exclusions)
    5. Run cheap pass (shortlist)
    6. Fetch OHLCV for shortlist
    7. Compute features (1d + 4h)
    8. Enrich features with price, name, market cap, and volume
    9. Compute scores (breakout / pullback / reversal)
    10. Write reports (Markdown + JSON + Excel)
    11. Write snapshot for backtests
    """
    run_mode = config.run_mode

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
    logger.info("\n[1/11] Fetching MEXC universe...")
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
    logger.info("\n[2-3/11] Fetching market cap & mapping...")
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
        
        symbols_with_data.append({
            'symbol': symbol,
            'base': symbol.replace('USDT', ''),
            'quote_volume_24h': float(ticker.get('quoteVolume', 0)),
            'market_cap': result._get_market_cap()
        })
    
    # Step 4: Apply hard filters
    logger.info("\n[4/11] Applying universe filters...")
    filters = UniverseFilters(config.raw)
    filtered = filters.apply_all(symbols_with_data)
    logger.info(f"✓ Filtered: {len(filtered)} symbols")
    
    # Step 5: Run cheap pass (shortlist)
    logger.info("\n[5/11] Creating shortlist...")
    selector = ShortlistSelector(config.raw)
    shortlist = selector.select(filtered)
    logger.info(f"✓ Shortlist: {len(shortlist)} symbols")
    
    # Step 6: Fetch OHLCV for shortlist
    logger.info("\n[6/11] Fetching OHLCV data...")
    ohlcv_fetcher = OHLCVFetcher(mexc, config.raw)
    ohlcv_data = ohlcv_fetcher.fetch_all(shortlist)
    logger.info(f"✓ OHLCV: {len(ohlcv_data)} symbols with complete data")
    
    # Step 7: Compute features (1d + 4h)
    logger.info("\n[7/11] Computing features...")
    feature_engine = FeatureEngine(config.raw)
    features = feature_engine.compute_all(ohlcv_data, asof_ts_ms=asof_ts_ms)
    logger.info(f"✓ Features: {len(features)} symbols")

    # Step 8: Enrich features with price, coin name, market cap, and volume
    logger.info("\n[8/11] Enriching features with price, name, market cap, and volume...")
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
        else:
            features[symbol]['coin_name'] = 'Unknown'
        
        # Add market cap and volume from shortlist data
        shortlist_entry = next((s for s in shortlist if s['symbol'] == symbol), None)
        if shortlist_entry:
            features[symbol]['market_cap'] = shortlist_entry.get('market_cap')
            features[symbol]['quote_volume_24h'] = shortlist_entry.get('quote_volume_24h')
        else:
            features[symbol]['market_cap'] = None
            features[symbol]['quote_volume_24h'] = None

    logger.info(f"✓ Enriched {len(features)} symbols with price, name, market cap, and volume")
    
    # Prepare volume map for scoring (backwards compatibility)
    volume_map = {s['symbol']: s['quote_volume_24h'] for s in shortlist}
    
    # Step 9: Compute scores (breakout / pullback / reversal)
    logger.info("\n[9/11] Scoring setups...")
    
    logger.info("  Scoring Reversals...")
    reversal_results = score_reversals(features, volume_map, config.raw)
    logger.info(f"  ✓ Reversals: {len(reversal_results)} scored")
    
    logger.info("  Scoring Breakouts...")
    breakout_results = score_breakouts(features, volume_map, config.raw)
    logger.info(f"  ✓ Breakouts: {len(breakout_results)} scored")
    
    logger.info("  Scoring Pullbacks...")
    pullback_results = score_pullbacks(features, volume_map, config.raw)
    logger.info(f"  ✓ Pullbacks: {len(pullback_results)} scored")
    
    # Step 10: Write reports (Markdown + JSON + Excel)
    logger.info("\n[10/11] Generating reports...")
    report_gen = ReportGenerator(config.raw)
    report_paths = report_gen.save_reports(
        reversal_results,
        breakout_results,
        pullback_results,
        run_date,
        metadata={
            'mode': run_mode,
            'asof_ts_ms': asof_ts_ms,
            'asof_iso': asof_iso,
        }
    )
    logger.info(f"✓ Markdown: {report_paths['markdown']}")
    logger.info(f"✓ JSON: {report_paths['json']}")
    if 'excel' in report_paths:
        logger.info(f"✓ Excel: {report_paths['excel']}")
    
    # Step 11: Write snapshot for backtests
    logger.info("\n[11/11] Creating snapshot...")
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

### `scanner/pipeline/features.py`

**SHA256:** `aadd127cf726b4579f124fee55e0a582541b9c8ad0473ed1adb49f24c84658c4`

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
from typing import Dict, List, Any, Optional
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

**SHA256:** `7804d11b91f79cff4eb61b20149e8cab07fb72e9d90e5b67d2d534d1045a66d6`

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
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize snapshot manager.
        
        Args:
            config: Config dict with 'snapshots' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            snapshot_config = config.raw.get('snapshots', {})
        else:
            snapshot_config = config.get('snapshots', {})
        
        self.snapshots_dir = Path(
            snapshot_config.get('history_dir')
            or snapshot_config.get('snapshot_dir')
            or 'snapshots/history'
        )

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
                'version': '1.0'
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

### `scanner/pipeline/output.py`

**SHA256:** `837165bf8dc49fc7de97af4e42d02f7d5357af41e6876761d049dfc01da60766`

```python
"""
Output & Report Generation
===========================

Generates human-readable (Markdown), machine-readable (JSON), and Excel reports
from scored results.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


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
            output_config = config.raw.get('output', {})
        else:
            output_config = config.get('output', {})
        
        self.reports_dir = Path(output_config.get('reports_dir', 'reports'))
        self.top_n = output_config.get('top_n_per_setup', 10)
        
        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Report Generator initialized: reports_dir={self.reports_dir}")
    
    def generate_markdown_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        run_date: str
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
        lines = []
        
        # Header
        lines.append(f"# Spot Altcoin Scanner Report")
        lines.append(f"**Date:** {run_date}")
        lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Reversal Setups:** {len(reversal_results)} scored")
        lines.append(f"- **Breakout Setups:** {len(breakout_results)} scored")
        lines.append(f"- **Pullback Setups:** {len(pullback_results)} scored")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Reversal Setups (Priority)
        lines.append("## 🔄 Top Reversal Setups")
        lines.append("")
        lines.append("*Downtrend → Base → Reclaim*")
        lines.append("")
        
        if reversal_results:
            top_reversals = reversal_results[:self.top_n]
            for i, entry in enumerate(top_reversals, 1):
                lines.extend(self._format_setup_entry(i, entry))
        else:
            lines.append("*No reversal setups found.*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Breakout Setups
        lines.append("## 📈 Top Breakout Setups")
        lines.append("")
        lines.append("*Range break + volume confirmation*")
        lines.append("")
        
        if breakout_results:
            top_breakouts = breakout_results[:self.top_n]
            for i, entry in enumerate(top_breakouts, 1):
                lines.extend(self._format_setup_entry(i, entry))
        else:
            lines.append("*No breakout setups found.*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Pullback Setups
        lines.append("## 📽 Top Pullback Setups")
        lines.append("")
        lines.append("*Trend continuation after retracement*")
        lines.append("")
        
        if pullback_results:
            top_pullbacks = pullback_results[:self.top_n]
            for i, entry in enumerate(top_pullbacks, 1):
                lines.extend(self._format_setup_entry(i, entry))
        else:
            lines.append("*No pullback setups found.*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Footer
        lines.append("## Notes")
        lines.append("")
        lines.append("- Scores range from 0-100")
        lines.append("- Higher scores indicate stronger setups")
        lines.append("- ⚠️ flags indicate warnings (overextension, low liquidity, etc.)")
        lines.append("- This is a research tool, not financial advice")
        lines.append("")
        
        return "\n".join(lines)
    
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
            lines.append(analysis)
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
            ranked.append(ranked_entry)
        return ranked

    def generate_json_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None
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
        report = {
            'meta': {
                'date': run_date,
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0'
            },
            'summary': {
                'reversal_count': len(reversal_results),
                'breakout_count': len(breakout_results),
                'pullback_count': len(pullback_results),
                'total_scored': len(reversal_results) + len(breakout_results) + len(pullback_results)
            },
            'setups': {
                'reversals': self._with_rank(reversal_results[:self.top_n]),
                'breakouts': self._with_rank(breakout_results[:self.top_n]),
                'pullbacks': self._with_rank(pullback_results[:self.top_n])
            }
        }
        
        if metadata:
            report['meta'].update(metadata)
        
        return report
    
    def save_reports(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None
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
            reversal_results, breakout_results, pullback_results, run_date
        )
        
        # Generate JSON
        json_content = self.generate_json_report(
            reversal_results, breakout_results, pullback_results, run_date, metadata
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
                reversal_results, breakout_results, pullback_results, run_date, metadata
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
            'json': json_path
        }
        
        if excel_path:
            result['excel'] = excel_path
        
        return result

```

### `scanner/pipeline/ohlcv.py`

**SHA256:** `692e69deed5f59bbdefa0c5a9cbcd1fb2c5ea76c570bfeec1762e3d98a47f985`

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
        """
        lookback_1d_default = int(general_cfg.get('lookback_days_1d', 120))
        lookback_4h_default = int(general_cfg.get('lookback_days_4h', 30)) * 6

        lookback = {
            '1d': lookback_1d_default,
            '4h': lookback_4h_default,
        }

        if isinstance(ohlcv_lookback_cfg, dict):
            for tf, bars in ohlcv_lookback_cfg.items():
                try:
                    lookback[str(tf)] = int(bars)
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

**SHA256:** `c7c6d86798768efd84a890760c6e05a356fb4ef089cdc1ef06b0428f9f7c4ac8`

```python
"""
Backtest runner.

Responsibilities:
- Consume historical snapshots.
- Compute forward returns for each setup:
  - Breakout
  - Pullback
  - Reversal
- Aggregate evaluation metrics:
  - hit rate
  - median/mean returns
  - tail risk
  - rank vs return behavior
- Output backtest summaries (e.g. JSON / Markdown).

Backtests must be deterministic and snapshot-driven.
"""


```

### `scanner/pipeline/runtime_market_meta.py`

**SHA256:** `141820c4f9c0998fbcb5580cb89b09a76922183ded4d24a59841428e81dee150`

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

    def _build_ticker(self, ticker: Dict[str, Any]) -> Dict[str, Any]:
        bid = self._to_float(ticker.get("bidPrice"))
        ask = self._to_float(ticker.get("askPrice"))
        mid = None
        spread_pct = None

        if bid is not None and ask is not None:
            mid = (bid + ask) / 2
            if mid != 0:
                spread_pct = ((ask - bid) / mid) * 100

        return {
            "last_price": self._to_float(ticker.get("lastPrice")),
            "high_24h": self._to_float(ticker.get("highPrice")),
            "low_24h": self._to_float(ticker.get("lowPrice")),
            "quote_volume_24h": self._to_float(ticker.get("quoteVolume")),
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
            ticker_24h = self._build_ticker(ticker)

            quality = self._build_quality(
                symbol=symbol,
                identity=identity,
                symbol_info=symbol_info,
                has_scanner_features=symbol in features,
                has_ohlcv=symbol in ohlcv_data,
            )

            coins[symbol] = {
                "identity": identity,
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

**SHA256:** `c00d2021eab5f0ca1542ac63cc3d6a3e179c00bf0121872e6290157b893e2377`

```python
"""Breakout scoring."""

import logging
from typing import Dict, Any, List

from scanner.pipeline.scoring.weights import load_component_weights

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

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float) -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})

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

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor
        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(breakout_score, volume_score, trend_score, momentum_score, f1d, f4h, flags)

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
        }

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
                          f1d: Dict[str, Any], f4h: Dict[str, Any], flags: List[str]) -> List[str]:
        reasons = []
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


def score_breakouts(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scorer = BreakoutScorer(config)
    results = []
    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        try:
            score_result = scorer.score(symbol, features, volume)
            results.append(
                {
                    "symbol": symbol,
                    "price_usdt": features.get("price_usdt"),
                    "coin_name": features.get("coin_name"),
                    "market_cap": features.get("market_cap"),
                    "quote_volume_24h": features.get("quote_volume_24h"),
                    "score": score_result["score"],
                    "raw_score": score_result["raw_score"],
                    "penalty_multiplier": score_result["penalty_multiplier"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "reasons": score_result["reasons"],
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

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

**SHA256:** `85d37b09e745ca99fd4ceeca2844c758866fa7f247ded2d4a2b9a8284d6c51b4`

```python
"""
Scoring package.

Contains three independent scoring modules:
- breakout.py
- pullback.py
- reversal.py

Each module:
- consumes features
- applies setup-specific logic
- outputs normalized scores, components, penalties and flags.
"""


```

### `scanner/pipeline/scoring/pullback.py`

**SHA256:** `1588b9b0ae1b1bac5ed8124393496f7547a6caa6b7a1e1f756bb0e432373bba8`

```python
"""Pullback scoring."""

import logging
from typing import Dict, Any, List

from scanner.pipeline.scoring.weights import load_component_weights

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

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float) -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})

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

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor
        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(trend_score, pullback_score, rebound_score, volume_score, f1d, f4h, flags)

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
        }

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
                          f1d: Dict[str, Any], f4h: Dict[str, Any], flags: List[str]) -> List[str]:
        reasons = []

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


def score_pullbacks(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scorer = PullbackScorer(config)
    results = []
    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        try:
            score_result = scorer.score(symbol, features, volume)
            results.append(
                {
                    "symbol": symbol,
                    "price_usdt": features.get("price_usdt"),
                    "coin_name": features.get("coin_name"),
                    "market_cap": features.get("market_cap"),
                    "quote_volume_24h": features.get("quote_volume_24h"),
                    "score": score_result["score"],
                    "raw_score": score_result["raw_score"],
                    "penalty_multiplier": score_result["penalty_multiplier"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "reasons": score_result["reasons"],
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

```

### `scanner/pipeline/scoring/reversal.py`

**SHA256:** `d32086820a7e58be0e400bf588863387ea82ee09bf87ea7c5f2b7c05ac168db6`

```python
"""
Reversal Setup Scoring
======================

Identifies downtrend → base → reclaim setups.
"""

import logging
import math
from typing import Dict, Any, List

from scanner.pipeline.scoring.weights import load_component_weights

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

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float) -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})

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

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor

        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(drawdown_score, base_score, reclaim_score, volume_score, f1d, f4h, flags)

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
        }

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
    ) -> List[str]:
        reasons = []

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


def score_reversals(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scorer = ReversalScorer(config)
    results = []

    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        try:
            score_result = scorer.score(symbol, features, volume)
            results.append(
                {
                    "symbol": symbol,
                    "price_usdt": features.get("price_usdt"),
                    "coin_name": features.get("coin_name"),
                    "market_cap": features.get("market_cap"),
                    "quote_volume_24h": features.get("quote_volume_24h"),
                    "score": score_result["score"],
                    "raw_score": score_result["raw_score"],
                    "penalty_multiplier": score_result["penalty_multiplier"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "reasons": score_result["reasons"],
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

```

### `docs/scoring.md`

**SHA256:** `63afdf61d6613c1f30a78f0ef10f1acce82f4731d2f8692911071b001ed11c6a`

```markdown
# Scoring Modules Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

This document specifies the three scoring modules used by the scanner:

1. Breakout Score
2. Trend Pullback Score
3. Reversal Score

Each scoring module must:
- operate independently
- normalize scores to [0, 100]
- decompose into weighted components
- apply contextual penalties
- output ranked candidates
- surface flags + reasons
- remain deterministic

There is **no global fused score**.

---

## 1.1 Canonical v1.3 Notes

The canonical implementation is in:
- `scanner/pipeline/scoring/breakout.py`
- `scanner/pipeline/scoring/pullback.py`
- `scanner/pipeline/scoring/reversal.py`

Critical canonical rules:
- Pullback uptrend guard uses `dist_ema50_pct >= 0` (EMA50 touch is valid uptrend; only `< 0` is broken trend).
- Volume reason text must use the exact same spike datapath/fallback as scoring (no divergence between displayed and scored spike).
- Reversal base component consumes `base_score` from FeatureEngine directly (no scorer-side base detection).
- Missing/NaN/non-finite `base_score` is treated as `0` (never coerced to 100 by clamping side effects).
- Momentum scaling is continuous and linear: `clamp((r_7 / 10) * 100, 0, 100)`.
- Penalties/thresholds are config-driven via `scoring.*.penalties` and `scoring.*.momentum`.

---

## 2. Shared Scoring Principles

### 2.1 Independence

Each setup represents a distinct trading archetype.  
Mixing setup signals degrades performance.

### 2.2 Determinism

Same data + same config → same score.

### 2.3 Explainability

Scores must return:
- components
- weights
- penalties
- flags
- structured reasons

### 2.4 Normalization

Raw score ∈ [0, 1]  
Normalized score ∈ [0, 100]

### 2.5 Penalty System

Penalties reduce normalized score based on flags:

| Flag | Penalty |
|---|---|
| low_liquidity | strong |
| extreme_volatility | moderate |
| falling_knife | strong |
| late_stage_move | moderate |
| mapping_low_confidence | optional |
| regime_mismatch (optional future) | mild |

Penalties must be multiplicative, not subtractive.

Example:

```
S_final = S_raw * P_low_liquidity * P_late_stage * ...
```

### 2.6 Output Structure

Each score returns:

```json
{
  "score": float (0–100),
  "normalized": float (0–1),
  "rank": int,
  "components": { ... },
  "penalties": { ... },
  "flags": { ... },
  "metadata": { ... }
}
```

---

## 3. Breakout Score

### 3.1 Setup Definition

Breakout = range break + volume confirmation

Breakouts occur when price exceeds prior resistance, typically measured using:

- 20d high
- 30d high

Volume confirms conviction.

### 3.2 Required Inputs

From features:

- `close`
- `high_20d`, `high_30d`
- `ema20`, `ema50`
- `volume_spike_7d`
- `atr_pct`

### 3.3 Gates

Breakout gates:

```
close > high_20d or close > high_30d
```

Volume gate:

```
volume_spike_7d ≥ threshold (config, e.g. 1.5)
```

### 3.4 Overextension Check

To avoid late-stage moves:

```
oe_ema20 = close / ema20 - 1
overextended = oe_ema20 > limit (config, e.g. 25%)
```

Late-stage moves produce penalty, not exclusion.

### 3.5 Components

Example weights:

| Component | Weight |
|---|---|
| price_break | 0.40 |
| volume_confirmation | 0.40 |
| volatility_context | 0.20 |

Normalized subcomponents:

```
s_price = clip((close - high_20d) / (0.05*high_20d), 0, 1)
s_volume = clip((vol_spike - 1.0) / (min_spike - 1.0), 0, 1)
s_vol_ctx = clip(atr_limit / atr_pct, 0, 1)
```

### 3.6 Penalties

```
if extreme_volatility → penalty
if low_liquidity → penalty
if late_stage_move → penalty
```

### 3.7 Interpretation

Breakouts are high-momentum, fragile setups.

---

## 4. Trend Pullback Score

### 4.1 Setup Definition

Trend Pullback = trend continuation after retracement

Trend must be established before retracement.

### 4.2 Required Inputs

- `close`
- `ema20`, `ema50`
- HH/HL structure
- pullback %
- volume
- 4h refinement (optional)

### 4.3 Trend Gate

Trend is up if:

```
close >= ema50 (1d, EMA50 touch allowed)
ema50 rising or flat
```

### 4.4 Pullback Detection

Compute:

```
recent_high = max(high over 20–30d)
pullback_pct = (recent_high - close) / recent_high
```

Configurable limits:

```
min_pullback_pct
max_pullback_pct (e.g. 25%)
```

### 4.5 Rebound Detection

Rebound conditions:

- HH over prior HL
- or reclaim above ema20
- or positive 3-day momentum

Optional 4h confirmation:
- ema20/ema50 cross
- volume uptick
- HH/HL on 4h

### 4.6 Components

Example weights:

| Component | Weight |
|---|---|
| trend_quality | 0.40 |
| pullback_quality | 0.40 |
| rebound_signal | 0.20 |

Component logic:

```
s_trend = f(close>ema50, ema50_slope, HH/HL_count)
s_pullback = f(pullback_pct range)
s_rebound = f(ema_reclaim + r_3d + vol_spike)
```

### 4.7 Penalties

- low liquidity
- late stage (if pullback shallow + extended trend)
- extreme volatility

### 4.8 Interpretation

Pullbacks are lower-volatility, medium-risk setups.

---

## 5. Reversal Score

### 5.1 Setup Definition

Reversal = downtrend → base → reclaim + volume

This setup captures structural transitions from bear to bull state.

### 5.2 Required Inputs

- drawdown from ATH
- base low & no-new-lows window
- volume SMA & spike
- reclaim vs EMA20/EMA50
- 3-day return
- volatility context

### 5.3 Gates (Strict)

Reversal gates:

**Gate 1: Drawdown**

```
min_dd ≤ drawdown ≤ max_dd
e.g. -40% ≤ dd ≤ -90%
```

**Gate 2: Base**

```
base_low = min(low over base_lookback)
no new lows for ≥ K days
```

**Gate 3: Reclaim**

```
close > ema20 (min 1 day)
optional: close > ema50
```

Volume Gate:

```
vol_spike ≥ threshold (e.g. 1.5)
```

### 5.4 Components

Example weights:

| Component | Weight |
|---|---|
| base_structure | 0.30 |
| reclaim_signal | 0.40 |
| volume_confirmation | 0.30 |

Normalized subcomponents:

```
s_base = g(days_without_new_low)
s_reclaim = g(close/ema20, close/ema50, r_3d)
s_vol = g(vol_spike)
```

### 5.5 Penalties

- falling_knife (strong penalty)
- extreme_volatility
- low_liquidity

### 5.6 Interpretation

Reversals are high-risk, high-reward setups and must be surfaced early.

---

## 6. Ranking

Each score produces:

- sorted list
- deterministic ordering
- stable tiebreaks via:
  1. score
  2. normalized
  3. market cap (optional descending)
  4. ticker (alphabetical)

Ranking must not change across runs for identical input.

---

## 7. Backtest Compatibility

Scores are snapshot-stored for backtesting.  
Forward returns must reference the score valid on day `t`.

---

## 8. Scoring Anti-Goals

Scoring must not:

- mix setup types
- use sentiment/news (v1)
- use ML/AI predictions
- incorporate execution logic
- overfit thresholds
- guess mapping

---

## 9. Tuning Philosophy

Tuning is done via:
- backtests
- hit/miss review
- qualitative inspection
- cluster performance analysis

No hyperparameter grid search in v1.

---

## 10. Future Extensions

Future scores may include:

- breakout fakeout detection
- sideways acceptance signals
- capitulation reversal scoring
- regime-based weighting
- risk-adjusted scoring
- volume signature profiles

v1 provides the structural foundation.

---

---

## 11. Phase Appendix Reference

Phase-specific scoring additions are maintained in:
- `docs/feature_improvements/PHASE_APPENDIX_FEATURES_SCORING.md`

This keeps high-traffic core docs conflict-stable while preserving exact phase semantics.

```

---

## 📚 Additional Resources

- **Code Map:** `docs/code_map.md` (detailed structural overview)
- **Specifications:** `docs/spec.md` (technical master spec)
- **Dev Guide:** `docs/dev_guide.md` (development workflow)
- **Latest Reports:** `reports/YYYY-MM-DD.md` (daily scanner outputs)

---

_Generated by GitHub Actions • 2026-02-19 07:53 UTC_
