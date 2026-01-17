# Spot Altcoin Scanner • GPT Snapshot

**Generated:** 2026-01-17 16:51 UTC  
**Commit:** `cc99b35` (cc99b35e8cc4096b289ec95067acba875ec229d1)  
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
| `scanner/pipeline/features.py` | `FeatureEngine` | - |
| `scanner/pipeline/filters.py` | `UniverseFilters` | - |
| `scanner/pipeline/ohlcv.py` | `OHLCVFetcher` | - |
| `scanner/pipeline/output.py` | `ReportGenerator` | - |
| `scanner/pipeline/scoring/__init__.py` | - | - |
| `scanner/pipeline/scoring/breakout.py` | `BreakoutScorer` | `score_breakouts` |
| `scanner/pipeline/scoring/pullback.py` | `PullbackScorer` | `score_pullbacks` |
| `scanner/pipeline/scoring/reversal.py` | `ReversalScorer` | `score_reversals` |
| `scanner/pipeline/shortlist.py` | `ShortlistSelector` | - |
| `scanner/pipeline/snapshot.py` | `SnapshotManager` | - |
| `scanner/utils/__init__.py` | - | - |
| `scanner/utils/io_utils.py` | - | `load_json`, `save_json`, `get_cache_path`, `cache_exists`, `load_cache` ... (+1 more) |
| `scanner/utils/logging_utils.py` | - | `setup_logger`, `get_logger` |
| `scanner/utils/time_utils.py` | - | `utc_now`, `utc_timestamp`, `utc_date`, `parse_timestamp`, `timestamp_to_ms` ... (+1 more) |

**Statistics:**
- Total Modules: 23
- Total Classes: 14
- Total Functions: 22

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

**SHA256:** `e6918e0f11a2667fc060416051ec4b9c08de10c7594161302a4a72acb55c4ffa`

```text
# HTTP & API
requests>=2.31.0

# Config & Serialization
PyYAML>=6.0.1

# Data Processing
pandas>=2.1.0
numpy>=1.24.0

# Time & Date
python-dateutil>=2.8.2

# Optional: Better Logging
loguru>=0.7.0

```

### `README.md`

**SHA256:** `f6a359b8b2088fa0f08e3c24e2ef12467ce27437f63004e43a95ce225d6689f7`

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
- Snapshot for backtesting: `snapshots/runtime/YYYY-MM-DD.json`

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

The scanner runs automatically every day at **6:00 AM UTC** via GitHub Actions.

**To trigger manually:**
1. Go to **Actions** tab in GitHub
2. Select **"Daily Scanner Run"**
3. Click **"Run workflow"**

Reports are automatically committed to the repository.

---

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

**SHA256:** `0102124caf8099e55046f0c5eddf6d40cb96547beb9c122bef1fd3e4acf6fcde`

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
    enabled: true
    high_lookback_days: 30
    min_volume_spike_factor: 1.5
    max_overextension_ema20_percent: 25
    weights:
      price_break: 0.40
      volume_confirmation: 0.40
      volatility_context: 0.20

  pullback:
    enabled: true
    max_pullback_from_high_percent: 25
    min_trend_days: 10
    ema_trend_period_days: 20
    weights:
      trend_quality: 0.40
      pullback_quality: 0.40
      rebound_signal: 0.20

  reversal:
    enabled: true
    min_drawdown_from_ath_percent: 40
    max_drawdown_from_ath_percent: 90
    base_lookback_days: 45
    min_base_days_without_new_low: 10
    max_allowed_new_low_percent_vs_base_low: 3
    min_reclaim_above_ema_days: 1
    min_volume_spike_factor: 1.5
    weights:
      base_structure: 0.30
      reclaim_signal: 0.40
      volume_confirmation: 0.30

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

**SHA256:** `9a1e424a1bd3f35a727e5e11e8f4f5a09a6c3098ac6900eb22d387eef005bcf8`

```yaml
name: Daily Scanner Run

on:
  schedule:
    # Runs daily at 6:00 AM UTC
    - cron: '0 6 * * *'
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

**SHA256:** `f20408e6cccb4c7c6f82fff59f51b29fa9dc549851506ba22ddf27838738db56`

```yaml
name: Update Code Map

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'scanner/**/*.py'
      - 'tests/**/*.py'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-code-map:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Generate Code Map Update
        run: |
          python3 << 'PYTHON_SCRIPT'
          import os
          import ast
          from pathlib import Path
          from datetime import datetime
          
          def analyze_module(filepath):
              """Analyze a Python module and extract structure."""
              with open(filepath, 'r', encoding='utf-8') as f:
                  try:
                      tree = ast.parse(f.read())
                  except:
                      return None
              
              classes = []
              functions = []
              
              for node in ast.walk(tree):
                  if isinstance(node, ast.ClassDef):
                      methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                      classes.append({'name': node.name, 'methods': methods})
                  elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                      functions.append(node.name)
              
              return {'classes': classes, 'functions': functions}
          
          def scan_package(package_path):
              """Scan a package and return structure."""
              modules = {}
              base_path = Path(package_path).resolve()
              
              for py_file in base_path.rglob('*.py'):
                  rel_path = str(py_file.relative_to(Path.cwd()))
                  result = analyze_module(py_file)
                  if result:
                      modules[rel_path] = result
              
              return modules
          
          def generate_code_map_update():
              """Generate code map update section."""
              scanner_modules = scan_package('scanner')
              
              lines = []
              lines.append("# Code Map - Auto-Generated Section")
              lines.append("")
              lines.append(f"**Last Auto-Update:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
              lines.append("")
              lines.append("## Module Summary")
              lines.append("")
              
              total_classes = sum(len(m['classes']) for m in scanner_modules.values())
              total_functions = sum(len(m['functions']) for m in scanner_modules.values())
              
              lines.append(f"- **Total Modules:** {len(scanner_modules)}")
              lines.append(f"- **Total Classes:** {total_classes}")
              lines.append(f"- **Total Functions:** {total_functions}")
              lines.append("")
              lines.append("## Quick Reference")
              lines.append("")
              
              lines.append("### Classes")
              for module_path, data in sorted(scanner_modules.items()):
                  if data['classes']:
                      for cls in data['classes']:
                          lines.append(f"- **{cls['name']}** (`{module_path}`)")
                          if cls['methods']:
                              method_count = len(cls['methods'])
                              lines.append(f"  - {method_count} methods")
              
              lines.append("")
              return '\n'.join(lines)
          
          update_section = generate_code_map_update()
          
          code_map_path = Path('docs/code_map.md')
          if code_map_path.exists():
              with open(code_map_path, 'r', encoding='utf-8') as f:
                  content = f.read()
              
              start_marker = '# Code Map - Auto-Generated Section'
              if start_marker in content:
                  parts = content.split(start_marker)
                  if len(parts) == 2:
                      end_idx = parts[1].find('\n## ', 100)
                      if end_idx != -1:
                          new_content = parts[0] + update_section + parts[1][end_idx:]
                      else:
                          new_content = parts[0] + update_section
                  else:
                      new_content = content + '\n\n---\n\n' + update_section
              else:
                  new_content = content + '\n\n---\n\n' + update_section
              
              with open(code_map_path, 'w', encoding='utf-8') as f:
                  f.write(new_content)
              
              print("✓ Code Map updated")
          else:
              print("✗ Code Map not found")
              exit(1)
          PYTHON_SCRIPT
      
      - name: Check for changes
        id: check_changes
        run: |
          if git diff --quiet docs/code_map.md; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi
      
      - name: Commit changes
        if: steps.check_changes.outputs.changed == 'true'
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add docs/code_map.md
          git commit -m "docs: auto-update code map [skip ci]"
          git push

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

### `scanner/__init__.py`

**SHA256:** `c6d8ea689789828672d38ce8d93859015f5cc8d69934f34f23366d6a1ddc8b84`

```python
# scanner/__init__.py

"""
Spot Altcoin Scanner package.

See /docs/spec.md for the full technical specification.
"""


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

### `scanner/pipeline/snapshot.py`

**SHA256:** `f40940b649285ada7cc99a802467a2801cf5eb3357e049d7e572bdeabeaa4597`

```python
"""
Snapshot System
===============

Creates deterministic daily snapshots for backtesting and reproducibility.
Snapshots include all pipeline data at a specific point in time.
"""

import logging
from typing import Dict, Any, List
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
        
        self.snapshots_dir = Path(snapshot_config.get('runtime_dir', 'snapshots/runtime'))
        
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
            date = path.stem  # Filename without extension
            snapshots.append(date)
        
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

### `scanner/pipeline/features.py`

**SHA256:** `6ca81bd282734a31268ada96b007fc89d06e1a7611aa02393270960a8696664c`

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
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngine:
    """Computes technical features from OHLCV data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize feature engine.
        
        Args:
            config: Config dict (not used currently, for future extensions)
        """
        self.config = config
        logger.info("Feature Engine initialized")
    
    def compute_all(
        self,
        ohlcv_data: Dict[str, Dict[str, List[List]]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute features for all symbols.
        
        Args:
            ohlcv_data: Dict mapping symbol -> timeframe -> klines
                {
                    'BTCUSDT': {
                        '1d': [[ts, o, h, l, c, v, ...], ...],
                        '4h': [[ts, o, h, l, c, v, ...], ...]
                    },
                    ...
                }
        
        Returns:
            Dict mapping symbol -> features
            {
                'BTCUSDT': {
                    '1d': {...},
                    '4h': {...},
                    'meta': {...}
                },
                ...
            }
        """
        results = {}
        total = len(ohlcv_data)
        
        logger.info(f"Computing features for {total} symbols")
        
        for i, (symbol, tf_data) in enumerate(ohlcv_data.items(), 1):
            logger.debug(f"[{i}/{total}] Computing features for {symbol}")
            
            try:
                symbol_features = {}
                
                # Compute features for each timeframe
                if '1d' in tf_data:
                    symbol_features['1d'] = self._compute_timeframe_features(
                        tf_data['1d'], 
                        timeframe='1d'
                    )
                
                if '4h' in tf_data:
                    symbol_features['4h'] = self._compute_timeframe_features(
                        tf_data['4h'],
                        timeframe='4h'
                    )
                
                # Meta info
                symbol_features['meta'] = {
                    'symbol': symbol,
                    'last_update': int(tf_data['1d'][-1][0]) if '1d' in tf_data else None
                }
                
                results[symbol] = symbol_features
                
            except Exception as e:
                logger.error(f"Failed to compute features for {symbol}: {e}")
                continue
        
        logger.info(f"Features computed for {len(results)}/{total} symbols")
        return results
    
    def _compute_timeframe_features(
        self,
        klines: List[List],
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Compute features for a single timeframe.
        
        Args:
            klines: List of klines [[ts, o, h, l, c, v, ...], ...]
            timeframe: '1d' or '4h'
        
        Returns:
            Feature dict (all numpy types converted to Python native types)
        """
        # Extract OHLCV arrays
        closes = np.array([k[4] for k in klines], dtype=float)
        highs = np.array([k[2] for k in klines], dtype=float)
        lows = np.array([k[3] for k in klines], dtype=float)
        volumes = np.array([k[5] for k in klines], dtype=float)
        
        features = {}
        
        # Current price
        features['close'] = float(closes[-1])
        features['high'] = float(highs[-1])
        features['low'] = float(lows[-1])
        features['volume'] = float(volumes[-1])
        
        # Returns
        features['r_1'] = self._calc_return(closes, 1)
        features['r_3'] = self._calc_return(closes, 3)
        features['r_7'] = self._calc_return(closes, 7)
        
        # EMAs
        features['ema_20'] = self._calc_ema(closes, 20)
        features['ema_50'] = self._calc_ema(closes, 50)
        
        # Price relative to EMAs (%)
        features['dist_ema20_pct'] = ((closes[-1] / features['ema_20']) - 1) * 100 if features['ema_20'] else None
        features['dist_ema50_pct'] = ((closes[-1] / features['ema_50']) - 1) * 100 if features['ema_50'] else None
        
        # ATR (as % of price)
        features['atr_pct'] = self._calc_atr_pct(highs, lows, closes, period=14)
        
        # Volume
        features['volume_sma_14'] = self._calc_sma(volumes, 14)
        features['volume_spike'] = float((volumes[-1] / features['volume_sma_14'])) if features['volume_sma_14'] and features['volume_sma_14'] > 0 else 1.0
        
        # Higher High / Higher Low (trend structure) - convert to native bool
        features['hh_20'] = bool(self._detect_higher_high(highs, lookback=20))
        features['hl_20'] = bool(self._detect_higher_low(lows, lookback=20))
        
        # Breakout distance (distance to recent high)
        features['breakout_dist_20'] = self._calc_breakout_distance(closes, highs, lookback=20)
        features['breakout_dist_30'] = self._calc_breakout_distance(closes, highs, lookback=30)
        
        # Drawdown from ATH
        features['drawdown_from_ath'] = self._calc_drawdown(closes)
        
        # Base detection (sideways consolidation)
        if timeframe == '1d':
            base_result = self._detect_base(closes, lows, lookback=30)
            features['base_detected'] = bool(base_result) if base_result is not None else None
        else:
            features['base_detected'] = None
        
        # Ensure all numeric values are native Python types for JSON serialization
        return self._convert_to_native_types(features)
    
    def _convert_to_native_types(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Convert numpy types to Python native types for JSON serialization."""
        converted = {}
        for key, value in features.items():
            if value is None:
                converted[key] = None
            elif isinstance(value, (np.floating, np.float64, np.float32)):
                converted[key] = float(value)
            elif isinstance(value, (np.integer, np.int64, np.int32)):
                converted[key] = int(value)
            elif isinstance(value, (np.bool_, bool)):
                converted[key] = bool(value)
            else:
                converted[key] = value
        return converted
    
    def _calc_return(self, closes: np.ndarray, periods: int) -> Optional[float]:
        """Calculate return over N periods (%)."""
        if len(closes) <= periods:
            return None
        return float(((closes[-1] / closes[-periods-1]) - 1) * 100)
    
    def _calc_ema(self, data: np.ndarray, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average."""
        if len(data) < period:
            return None
        
        alpha = 2 / (period + 1)
        ema = data[0]
        
        for val in data[1:]:
            ema = alpha * val + (1 - alpha) * ema
        
        return float(ema)
    
    def _calc_sma(self, data: np.ndarray, period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(data) < period:
            return None
        return float(np.mean(data[-period:]))
    
    def _calc_atr_pct(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int = 14
    ) -> Optional[float]:
        """Calculate Average True Range as % of price."""
        if len(highs) < period + 1:
            return None
        
        # True Range
        tr = []
        for i in range(1, len(highs)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr.append(max(hl, hc, lc))
        
        tr = np.array(tr)
        
        # ATR
        atr = np.mean(tr[-period:])
        
        # As % of current price
        return float((atr / closes[-1]) * 100) if closes[-1] > 0 else None
    
    def _detect_higher_high(self, highs: np.ndarray, lookback: int = 20) -> bool:
        """Detect if recent high is highest in lookback period."""
        if len(highs) < lookback:
            return False
        
        recent_high = np.max(highs[-5:])  # Last 5 bars
        lookback_high = np.max(highs[-lookback:-5])  # Previous bars
        
        return bool(recent_high > lookback_high)
    
    def _detect_higher_low(self, lows: np.ndarray, lookback: int = 20) -> bool:
        """Detect if recent low is higher than lookback period."""
        if len(lows) < lookback:
            return False
        
        recent_low = np.min(lows[-5:])  # Last 5 bars
        lookback_low = np.min(lows[-lookback:-5])  # Previous bars
        
        return bool(recent_low > lookback_low)
    
    def _calc_breakout_distance(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lookback: int = 20
    ) -> Optional[float]:
        """
        Calculate distance to breakout level (%).
        Positive = above recent high, Negative = below.
        """
        if len(highs) < lookback:
            return None
        
        recent_high = np.max(highs[-lookback:])
        current = closes[-1]
        
        return float(((current / recent_high) - 1) * 100)
    
    def _calc_drawdown(self, closes: np.ndarray) -> Optional[float]:
        """Calculate drawdown from ATH (%)."""
        if len(closes) == 0:
            return None
        
        ath = np.max(closes)
        current = closes[-1]
        
        return float(((current / ath) - 1) * 100)
    
    def _detect_base(
        self,
        closes: np.ndarray,
        lows: np.ndarray,
        lookback: int = 30
    ) -> Optional[bool]:
        """
        Detect base formation (sideways consolidation).
        
        Criteria:
        - No new lows in last 10 bars
        - Low volatility (ATR)
        """
        if len(closes) < lookback:
            return None
        
        recent_period = lookback // 3  # Last third of lookback
        
        # Check for new lows
        recent_low = np.min(lows[-recent_period:])
        prior_low = np.min(lows[-lookback:-recent_period])
        
        no_new_lows = recent_low >= prior_low
        
        # Check volatility (simple range check)
        recent_range = (np.max(closes[-recent_period:]) - np.min(closes[-recent_period:])) / np.mean(closes[-recent_period:])
        
        low_volatility = recent_range < 0.15  # Less than 15% range
        
        return bool(no_new_lows and low_volatility)

```

### `scanner/pipeline/output.py`

**SHA256:** `3c2547095ab669b1670dcdd6e3338b5672a6d4f5c9da619fc9662e90a361bfdc`

```python
"""
Output & Report Generation
===========================

Generates human-readable (Markdown) and machine-readable (JSON) reports
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
        lines.append("*Downtrend → Base → Reclaim (like Humanity Protocol)*")
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
        lines.append("## 🔽 Top Pullback Setups")
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
    
    def _format_setup_entry(self, rank: int, entry: Dict[str, Any]) -> List[str]:
        """Format a single setup entry for markdown."""
        lines = []
        
        symbol = entry['symbol']
        score = entry['score']
        components = entry['components']
        flags = entry.get('flags', [])
        reasons = entry.get('reasons', [])
        
        # Header
        flag_str = f" ⚠️ {', '.join(flags)}" if flags else ""
        lines.append(f"### {rank}. {symbol} - Score: {score:.1f}{flag_str}")
        lines.append("")
        
        # Components
        lines.append("**Components:**")
        for comp_name, comp_score in components.items():
            lines.append(f"- {comp_name.capitalize()}: {comp_score:.1f}")
        lines.append("")
        
        # Reasons
        if reasons:
            lines.append("**Analysis:**")
            for reason in reasons:
                lines.append(f"- {reason}")
            lines.append("")
        
        return lines
    
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
                'reversals': reversal_results[:self.top_n],
                'breakouts': breakout_results[:self.top_n],
                'pullbacks': pullback_results[:self.top_n]
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
        Generate and save both Markdown and JSON reports.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata
        
        Returns:
            Dict with paths: {'markdown': Path, 'json': Path}
        """
        logger.info(f"Generating reports for {run_date}")
        
        # Generate reports
        md_content = self.generate_markdown_report(
            reversal_results, breakout_results, pullback_results, run_date
        )
        
        json_content = self.generate_json_report(
            reversal_results, breakout_results, pullback_results, run_date, metadata
        )
        
        # Save files
        md_path = self.reports_dir / f"{run_date}.md"
        json_path = self.reports_dir / f"{run_date}.json"
        
        # Write Markdown
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Markdown report saved: {md_path}")
        
        # Write JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON report saved: {json_path}")
        
        return {
            'markdown': md_path,
            'json': json_path
        }

```

### `scanner/pipeline/filters.py`

**SHA256:** `63103cc1fa6aca7eb81ca58efc96e61ee4ab3c32ba1271d98f21d847d58c73e4`

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
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class UniverseFilters:
    """Filters for reducing MEXC universe to tradable MidCaps."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize filters with config.
        
        Args:
            config: Config dict with 'filters' section
        """
        self.config = config.get('filters', {})
        
        # Market Cap bounds (in USD)
        self.mcap_min = self.config.get('mcap_min', 100_000_000)  # 100M
        self.mcap_max = self.config.get('mcap_max', 3_000_000_000)  # 3B
        
        # Liquidity (24h volume in USDT)
        self.min_volume_24h = self.config.get('min_volume_24h', 1_000_000)  # 1M
        
        # Exclusion patterns
        self.exclusion_patterns = self.config.get('exclusion_patterns', [
            'USD', 'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD',  # Stablecoins
            'WBTC', 'WETH', 'WBNB',  # Wrapped tokens
            'UP', 'DOWN', 'BULL', 'BEAR',  # Leveraged tokens
        ])
        
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
        
        # Step 2: Liquidity filter
        filtered = self._filter_liquidity(filtered)
        logger.info(f"After Liquidity filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")
        
        # Step 3: Exclusions
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
        liquidity_pass = len(self._filter_liquidity(symbols))
        exclusion_pass = len(self._filter_exclusions(symbols))
        
        # Full pipeline
        final_pass = len(self.apply_all(symbols))
        
        return {
            'total_input': total,
            'mcap_pass': mcap_pass,
            'mcap_fail': total - mcap_pass,
            'liquidity_pass': liquidity_pass,
            'liquidity_fail': total - liquidity_pass,
            'exclusion_pass': exclusion_pass,
            'exclusion_fail': total - exclusion_pass,
            'final_pass': final_pass,
            'final_fail': total - final_pass,
            'filter_rate': f"{final_pass/total*100:.1f}%" if total > 0 else "0%"
        }

```

### `scanner/pipeline/shortlist.py`

**SHA256:** `bb87c2b8206482deb918d7c8cb374d43babe7dc2d60c7a48b4f32d14c98afa82`

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
        
        # Default: Top 100 by volume
        self.max_size = self.config.get('max_size', 100)
        
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

### `scanner/pipeline/ohlcv.py`

**SHA256:** `54be3754a9ffb8a4f51784f386f8dba43125df1b6598abaf0c3506663ce6b87f`

```python
"""
OHLCV Data Fetching
===================

Fetches OHLCV (klines) data for shortlisted symbols.
Supports multiple timeframes with caching.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OHLCVFetcher:
    """Fetches and caches OHLCV data for symbols."""
    
    def __init__(self, mexc_client, config: Dict[str, Any]):
        """
        Initialize OHLCV fetcher.
        
        Args:
            mexc_client: Instance of MEXCClient
            config: Config dict with 'ohlcv' section OR ScannerConfig object
        """
        self.mexc = mexc_client
        
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            # It's a ScannerConfig object
            self.timeframes = config.raw.get('ohlcv', {}).get('timeframes', ['1d', '4h'])
            self.lookback = config.raw.get('ohlcv', {}).get('lookback', {'1d': 120, '4h': 180})
            self.min_candles = config.raw.get('ohlcv', {}).get('min_candles', {'1d': 60, '4h': 90})
        else:
            # It's a dict
            ohlcv_config = config.get('ohlcv', {})
            self.timeframes = ohlcv_config.get('timeframes', ['1d', '4h'])
            self.lookback = ohlcv_config.get('lookback', {'1d': 120, '4h': 180})
            self.min_candles = ohlcv_config.get('min_candles', {'1d': 60, '4h': 90})
        
        logger.info(f"OHLCV Fetcher initialized: timeframes={self.timeframes}")
    
    def fetch_all(
        self,
        shortlist: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch OHLCV for all symbols in shortlist.
        
        Args:
            shortlist: List of symbol dicts with 'symbol' key
        
        Returns:
            Dict mapping symbol -> timeframe -> OHLCV data
            {
                'BTCUSDT': {
                    '1d': [...],
                    '4h': [...]
                },
                ...
            }
        """
        results = {}
        total = len(shortlist)
        
        logger.info(f"Fetching OHLCV for {total} symbols across {len(self.timeframes)} timeframes")
        
        for i, sym_data in enumerate(shortlist, 1):
            symbol = sym_data['symbol']
            
            logger.info(f"[{i}/{total}] Fetching {symbol}...")
            
            symbol_ohlcv = {}
            failed = False
            
            # Fetch each timeframe
            for tf in self.timeframes:
                limit = self.lookback.get(tf, 120)
                
                try:
                    klines = self.mexc.get_klines(symbol, tf, limit=limit)
                    
                    if not klines:
                        logger.warning(f"  {symbol} {tf}: No data returned")
                        failed = True
                        break
                    
                    # Check minimum candles
                    min_required = self.min_candles.get(tf, 60)
                    if len(klines) < min_required:
                        logger.warning(f"  {symbol} {tf}: Insufficient data "
                                     f"({len(klines)} < {min_required} candles)")
                        failed = True
                        break
                    
                    symbol_ohlcv[tf] = klines
                    logger.info(f"  ✓ {symbol} {tf}: {len(klines)} candles")
                    
                except Exception as e:
                    logger.error(f"  ✗ {symbol} {tf}: {e}")
                    failed = True
                    break
            
            # Only include if all timeframes succeeded
            if not failed:
                results[symbol] = symbol_ohlcv
            else:
                logger.warning(f"  Skipping {symbol} (incomplete data)")
        
        logger.info(f"OHLCV fetch complete: {len(results)}/{total} symbols with complete data")
        
        return results
    
    def get_fetch_stats(
        self,
        ohlcv_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about fetched OHLCV data.
        
        Args:
            ohlcv_data: Output from fetch_all()
        
        Returns:
            Stats dict
        """
        if not ohlcv_data:
            return {
                'symbols_count': 0,
                'timeframes': [],
                'total_candles': 0
            }
        
        # Count candles
        total_candles = 0
        for symbol_data in ohlcv_data.values():
            for tf_data in symbol_data.values():
                total_candles += len(tf_data)
        
        # Get date range (from 1d data)
        date_range = None
        if ohlcv_data:
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
            'date_range': date_range
        }

```

### `scanner/pipeline/__init__.py`

**SHA256:** `21e6f825bd4ab9b3c2f8e0b2d050499c25768633a451bb9cc5bee27958dd5a3a`

```python
"""
Pipeline Orchestration
======================

Orchestrates the full daily scanning pipeline.
"""

from __future__ import annotations
import logging
from datetime import datetime

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
    8. Compute scores (breakout / pullback / reversal)
    9. Write reports (Markdown + JSON)
    10. Write snapshot for backtests
    """
    run_mode = config.run_mode
    run_date = datetime.utcnow().strftime('%Y-%m-%d')
    
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
    logger.info("\n[1/10] Fetching MEXC universe...")
    universe = mexc.get_spot_usdt_symbols(use_cache=use_cache)
    logger.info(f"✓ Universe: {len(universe)} USDT pairs")
    
    # Get 24h tickers
    logger.info("  Fetching 24h tickers...")
    tickers = mexc.get_24h_tickers(use_cache=use_cache)
    ticker_map = {t['symbol']: t for t in tickers}
    logger.info(f"  ✓ Tickers: {len(ticker_map)} symbols")
    
    # Step 2 & 3: Fetch market cap + Run mapping layer
    logger.info("\n[2-3/10] Fetching market cap & mapping...")
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
    logger.info("\n[4/10] Applying universe filters...")
    filters = UniverseFilters(config.raw)
    filtered = filters.apply_all(symbols_with_data)
    logger.info(f"✓ Filtered: {len(filtered)} symbols")
    
    # Step 5: Run cheap pass (shortlist)
    logger.info("\n[5/10] Creating shortlist...")
    selector = ShortlistSelector(config.raw)
    shortlist = selector.select(filtered)
    logger.info(f"✓ Shortlist: {len(shortlist)} symbols")
    
    # Step 6: Fetch OHLCV for shortlist
    logger.info("\n[6/10] Fetching OHLCV data...")
    ohlcv_fetcher = OHLCVFetcher(mexc, config.raw)
    ohlcv_data = ohlcv_fetcher.fetch_all(shortlist)
    logger.info(f"✓ OHLCV: {len(ohlcv_data)} symbols with complete data")
    
    # Step 7: Compute features (1d + 4h)
    logger.info("\n[7/10] Computing features...")
    feature_engine = FeatureEngine(config.raw)
    features = feature_engine.compute_all(ohlcv_data)
    logger.info(f"✓ Features: {len(features)} symbols")
    
    # Prepare volume map for scoring
    volume_map = {s['symbol']: s['quote_volume_24h'] for s in shortlist}
    
    # Step 8: Compute scores (breakout / pullback / reversal)
    logger.info("\n[8/10] Scoring setups...")
    
    logger.info("  Scoring Reversals...")
    reversal_results = score_reversals(features, volume_map, config.raw)
    logger.info(f"  ✓ Reversals: {len(reversal_results)} scored")
    
    logger.info("  Scoring Breakouts...")
    breakout_results = score_breakouts(features, volume_map, config.raw)
    logger.info(f"  ✓ Breakouts: {len(breakout_results)} scored")
    
    logger.info("  Scoring Pullbacks...")
    pullback_results = score_pullbacks(features, volume_map, config.raw)
    logger.info(f"  ✓ Pullbacks: {len(pullback_results)} scored")
    
    # Step 9: Write reports (Markdown + JSON)
    logger.info("\n[9/10] Generating reports...")
    report_gen = ReportGenerator(config.raw)
    report_paths = report_gen.save_reports(
        reversal_results,
        breakout_results,
        pullback_results,
        run_date
    )
    logger.info(f"✓ Markdown: {report_paths['markdown']}")
    logger.info(f"✓ JSON: {report_paths['json']}")
    
    # Step 10: Write snapshot for backtests
    logger.info("\n[10/10] Creating snapshot...")
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
        metadata={'mode': run_mode}
    )
    logger.info(f"✓ Snapshot: {snapshot_path}")
    
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
    logger.info(f"  Snapshot: {snapshot_path}")
    logger.info("=" * 80)

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

### `scanner/clients/marketcap_client.py`

**SHA256:** `2531da553442b95077a0dbbbc6b583c3e4086057bc475b21b6d632edf5334aab`

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
            return cached.get("data", [])
        
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

### `scanner/pipeline/scoring/pullback.py`

**SHA256:** `eb0f7f3854b9db26abf88ab0f5050d98fc5cf2fdb67d002ada1f6992740fd96a`

```python
"""
Pullback Setup Scoring
======================

Identifies trend continuation after retracement (pullback to support).

Scoring Components:
1. Trend Strength (30%) - Established uptrend (above EMA50)
2. Pullback Depth (25%) - Healthy retracement to EMA20/50
3. Rebound Strength (25%) - Recovery from pullback
4. Volume Pattern (20%) - Volume decrease on pullback, increase on rebound

Penalties:
- Broken trend (below EMA50)
- Low liquidity
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PullbackScorer:
    """Scores pullback setups (trend continuation)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize pullback scorer.
        
        Args:
            config: Config dict with 'scoring' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            scoring_config = config.raw.get('scoring', {}).get('pullback', {})
        else:
            scoring_config = config.get('scoring', {}).get('pullback', {})
        
        # Thresholds
        self.min_trend_strength = scoring_config.get('min_trend_strength', 5)  # >5% above EMA50
        self.ideal_pullback_depth = scoring_config.get('ideal_pullback_depth', 5)  # 5-10% from EMA20
        self.max_pullback_depth = scoring_config.get('max_pullback_depth', 15)  # <15% (not too deep)
        
        self.min_rebound = scoring_config.get('min_rebound', 3)  # >3% bounce
        self.min_volume_spike = scoring_config.get('min_volume_spike', 1.3)  # 1.3x on rebound
        
        # Component weights
        self.weights = {
            'trend': 0.30,
            'pullback': 0.25,
            'rebound': 0.25,
            'volume': 0.20
        }
        
        logger.info("Pullback Scorer initialized")
    
    def score(
        self,
        symbol: str,
        features: Dict[str, Any],
        quote_volume_24h: float
    ) -> Dict[str, Any]:
        """
        Score a single symbol for pullback setup.
        
        Args:
            symbol: Trading pair
            features: Feature dict with '1d' and '4h'
            quote_volume_24h: 24h volume in USDT
        
        Returns:
            Score dict
        """
        f1d = features.get('1d', {})
        f4h = features.get('4h', {})
        
        # Components
        trend_score = self._score_trend(f1d)
        pullback_score = self._score_pullback(f1d)
        rebound_score = self._score_rebound(f1d, f4h)
        volume_score = self._score_volume(f1d, f4h)
        
        # Weighted total
        raw_score = (
            trend_score * self.weights['trend'] +
            pullback_score * self.weights['pullback'] +
            rebound_score * self.weights['rebound'] +
            volume_score * self.weights['volume']
        )
        
        # Penalties & Flags
        penalties = []
        flags = []
        
        # Broken trend penalty
        dist_ema50 = f1d.get('dist_ema50_pct')
        if dist_ema50 and dist_ema50 < 0:
            penalties.append(('broken_trend', 0.5))
            flags.append('broken_trend')
        
        # Low liquidity
        if quote_volume_24h < 500_000:
            penalties.append(('low_liquidity', 0.8))
            flags.append('low_liquidity')
        
        # Apply penalties
        final_score = raw_score
        for name, factor in penalties:
            final_score *= factor
        
        # Reasons
        reasons = self._generate_reasons(
            trend_score, pullback_score, rebound_score, volume_score,
            f1d, f4h, flags
        )
        
        return {
            'score': round(final_score, 2),
            'components': {
                'trend': round(trend_score, 2),
                'pullback': round(pullback_score, 2),
                'rebound': round(rebound_score, 2),
                'volume': round(volume_score, 2)
            },
            'penalties': {name: factor for name, factor in penalties},
            'flags': flags,
            'reasons': reasons
        }
    
    def _score_trend(self, f1d: Dict[str, Any]) -> float:
        """
        Score trend strength (0-100).
        
        Strong trend = well above EMA50, higher highs.
        """
        score = 0.0
        
        dist_ema50 = f1d.get('dist_ema50_pct')
        
        # Must be above EMA50
        if not dist_ema50 or dist_ema50 < 0:
            return 0.0
        
        # Distance score
        if dist_ema50 >= 15:  # >15% above
            score += 60
        elif dist_ema50 >= 10:
            score += 50
        elif dist_ema50 >= self.min_trend_strength:
            score += 40
        else:
            score += 20
        
        # Higher highs
        if f1d.get('hh_20'):
            score += 40
        
        return min(score, 100.0)
    
    def _score_pullback(self, f1d: Dict[str, Any]) -> float:
        """
        Score pullback depth (0-100).
        
        Ideal: Pullback to EMA20/50 support.
        """
        dist_ema20 = f1d.get('dist_ema20_pct', 100)
        dist_ema50 = f1d.get('dist_ema50_pct', 100)
        
        # Currently near EMA20 (ideal pullback level)
        if -2 <= dist_ema20 <= 2:  # Within 2% of EMA20
            return 100.0
        
        # Near EMA50 (deeper pullback)
        if -2 <= dist_ema50 <= 2:
            return 80.0
        
        # Between EMAs (healthy pullback)
        if dist_ema20 < 0 and dist_ema50 > 0:
            return 60.0
        
        # Above both (no pullback yet)
        if dist_ema20 > 5:
            return 20.0
        
        # Below both (too deep)
        if dist_ema50 < -5:
            return 10.0
        
        return 40.0
    
    def _score_rebound(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """
        Score rebound strength (0-100).
        
        Recent bounce from pullback low.
        """
        score = 0.0
        
        # 1d momentum
        r3 = f1d.get('r_3', 0)
        
        if r3 >= 10:  # >10% in 3 days
            score += 50
        elif r3 >= self.min_rebound:
            score += 30
        elif r3 > 0:
            score += 10
        
        # 4h momentum (recent)
        r3_4h = f4h.get('r_3', 0)
        
        if r3_4h >= 5:
            score += 50
        elif r3_4h >= 2:
            score += 30
        elif r3_4h > 0:
            score += 10
        
        return min(score, 100.0)
    
    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """
        Score volume pattern (0-100).
        
        Ideal: Volume spike on rebound.
        """
        vol_spike_1d = f1d.get('volume_spike', 1.0)
        vol_spike_4h = f4h.get('volume_spike', 1.0)
        
        max_spike = max(vol_spike_1d, vol_spike_4h)
        
        if max_spike < self.min_volume_spike:
            return 0.0
        
        # Strong volume
        if max_spike >= 2.5:
            return 100.0
        
        # Moderate volume
        if max_spike >= 2.0:
            return 80.0
        
        # Linear scale
        ratio = (max_spike - self.min_volume_spike) / (2.0 - self.min_volume_spike)
        return ratio * 70.0
    
    def _generate_reasons(
        self,
        trend_score: float,
        pullback_score: float,
        rebound_score: float,
        volume_score: float,
        f1d: Dict[str, Any],
        f4h: Dict[str, Any],
        flags: List[str]
    ) -> List[str]:
        """Generate human-readable reasons."""
        reasons = []
        
        # Trend
        dist_ema50 = f1d.get('dist_ema50_pct', 0)
        if trend_score > 70:
            reasons.append(f"Strong uptrend ({dist_ema50:.1f}% above EMA50)")
        elif trend_score > 30:
            reasons.append(f"Moderate uptrend ({dist_ema50:.1f}% above EMA50)")
        else:
            reasons.append("Weak/no uptrend")
        
        # Pullback
        dist_ema20 = f1d.get('dist_ema20_pct', 0)
        if pullback_score > 70:
            reasons.append(f"At support level ({dist_ema20:.1f}% from EMA20)")
        elif pullback_score > 40:
            reasons.append("Healthy pullback depth")
        else:
            reasons.append("No clear pullback")
        
        # Rebound
        r3 = f1d.get('r_3', 0)
        if rebound_score > 60:
            reasons.append(f"Strong rebound ({r3:.1f}% in 3d)")
        elif rebound_score > 30:
            reasons.append("Moderate rebound")
        else:
            reasons.append("No rebound yet")
        
        # Volume
        vol_spike = max(f1d.get('volume_spike', 1.0), f4h.get('volume_spike', 1.0))
        if volume_score > 60:
            reasons.append(f"Strong volume ({vol_spike:.1f}x)")
        elif volume_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")
        
        # Flags
        if 'broken_trend' in flags:
            reasons.append("⚠️ Below EMA50 (trend broken)")
        
        if 'low_liquidity' in flags:
            reasons.append("⚠️ Low liquidity")
        
        return reasons


def score_pullbacks(
    features_data: Dict[str, Dict[str, Any]],
    volumes: Dict[str, float],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Score all symbols for pullback setups and return ranked list.
    
    Args:
        features_data: Dict mapping symbol -> features
        volumes: Dict mapping symbol -> 24h volume
        config: Config dict
    
    Returns:
        List of scored symbols, sorted by score (descending)
    """
    scorer = PullbackScorer(config)
    results = []
    
    logger.info(f"Scoring {len(features_data)} symbols for pullback setups")
    
    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        
        try:
            score_result = scorer.score(symbol, features, volume)
            
            results.append({
                'symbol': symbol,
                'score': score_result['score'],
                'components': score_result['components'],
                'penalties': score_result['penalties'],
                'flags': score_result['flags'],
                'reasons': score_result['reasons']
            })
            
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"Pullback scoring complete: {len(results)} symbols scored")
    
    return results

```

### `scanner/pipeline/scoring/breakout.py`

**SHA256:** `77ea425ca0a0b50c9daa1613ca4b8b3c279c4d1425811a9a4bced9ddd3437e12`

```python
"""
Breakout Setup Scoring
======================

Identifies range breakouts with volume confirmation.

Scoring Components:
1. Breakout Distance (35%) - How far above recent high
2. Volume Confirmation (30%) - Volume spike on breakout
3. Trend Context (20%) - Uptrend vs range
4. Momentum (15%) - Recent price action strength

Penalties:
- Overextension (too far, too fast)
- Low liquidity
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class BreakoutScorer:
    """Scores breakout setups (range break + volume)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize breakout scorer.
        
        Args:
            config: Config dict with 'scoring' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            scoring_config = config.raw.get('scoring', {}).get('breakout', {})
        else:
            scoring_config = config.get('scoring', {}).get('breakout', {})
        
        # Thresholds
        self.min_breakout_pct = scoring_config.get('min_breakout_pct', 2)  # >2% above high
        self.ideal_breakout_pct = scoring_config.get('ideal_breakout_pct', 5)  # 5-10% ideal
        self.max_breakout_pct = scoring_config.get('max_breakout_pct', 20)  # >20% = overextended
        
        self.min_volume_spike = scoring_config.get('min_volume_spike', 1.5)  # 1.5x normal
        self.ideal_volume_spike = scoring_config.get('ideal_volume_spike', 2.5)  # 2.5x+
        
        # Component weights
        self.weights = {
            'breakout': 0.35,
            'volume': 0.30,
            'trend': 0.20,
            'momentum': 0.15
        }
        
        logger.info("Breakout Scorer initialized")
    
    def score(
        self,
        symbol: str,
        features: Dict[str, Any],
        quote_volume_24h: float
    ) -> Dict[str, Any]:
        """
        Score a single symbol for breakout setup.
        
        Args:
            symbol: Trading pair
            features: Feature dict with '1d' and '4h'
            quote_volume_24h: 24h volume in USDT
        
        Returns:
            Score dict
        """
        f1d = features.get('1d', {})
        f4h = features.get('4h', {})
        
        # Components
        breakout_score = self._score_breakout(f1d)
        volume_score = self._score_volume(f1d, f4h)
        trend_score = self._score_trend(f1d)
        momentum_score = self._score_momentum(f1d)
        
        # Weighted total
        raw_score = (
            breakout_score * self.weights['breakout'] +
            volume_score * self.weights['volume'] +
            trend_score * self.weights['trend'] +
            momentum_score * self.weights['momentum']
        )
        
        # Penalties & Flags
        penalties = []
        flags = []
        
        # Overextension penalty
        breakout_dist = f1d.get('breakout_dist_20', 0)
        if breakout_dist > self.max_breakout_pct:
            penalties.append(('overextension', 0.6))
            flags.append('overextended')
        
        # Low liquidity
        if quote_volume_24h < 500_000:
            penalties.append(('low_liquidity', 0.8))
            flags.append('low_liquidity')
        
        # Apply penalties
        final_score = raw_score
        for name, factor in penalties:
            final_score *= factor
        
        # Reasons
        reasons = self._generate_reasons(
            breakout_score, volume_score, trend_score, momentum_score,
            f1d, f4h, flags
        )
        
        return {
            'score': round(final_score, 2),
            'components': {
                'breakout': round(breakout_score, 2),
                'volume': round(volume_score, 2),
                'trend': round(trend_score, 2),
                'momentum': round(momentum_score, 2)
            },
            'penalties': {name: factor for name, factor in penalties},
            'flags': flags,
            'reasons': reasons
        }
    
    def _score_breakout(self, f1d: Dict[str, Any]) -> float:
        """
        Score breakout distance (0-100).
        
        Ideal: 5-10% above recent high
        """
        dist = f1d.get('breakout_dist_20', -100)
        
        # Below high (no breakout)
        if dist < self.min_breakout_pct:
            return 0.0
        
        # Ideal range
        if self.ideal_breakout_pct <= dist <= self.ideal_breakout_pct * 2:
            return 100.0
        
        # Below ideal (linear scale)
        if dist < self.ideal_breakout_pct:
            ratio = (dist - self.min_breakout_pct) / (self.ideal_breakout_pct - self.min_breakout_pct)
            return 50.0 + ratio * 50.0
        
        # Above ideal but not overextended
        if dist < self.max_breakout_pct:
            excess = dist - (self.ideal_breakout_pct * 2)
            penalty = (excess / (self.max_breakout_pct - self.ideal_breakout_pct * 2)) * 30
            return max(70.0 - penalty, 40.0)
        
        # Overextended
        return 20.0
    
    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """Score volume confirmation (0-100)."""
        vol_1d = f1d.get('volume_spike', 1.0)
        vol_4h = f4h.get('volume_spike', 1.0)
        
        max_spike = max(vol_1d, vol_4h)
        
        # Below minimum
        if max_spike < self.min_volume_spike:
            return 0.0
        
        # Ideal or above
        if max_spike >= self.ideal_volume_spike:
            return 100.0
        
        # Linear scale
        ratio = (max_spike - self.min_volume_spike) / (self.ideal_volume_spike - self.min_volume_spike)
        return ratio * 100.0
    
    def _score_trend(self, f1d: Dict[str, Any]) -> float:
        """
        Score trend context (0-100).
        
        Better if already in uptrend (above EMAs).
        """
        score = 0.0
        
        dist_ema20 = f1d.get('dist_ema20_pct')
        dist_ema50 = f1d.get('dist_ema50_pct')
        
        # Above EMA20
        if dist_ema20 and dist_ema20 > 0:
            score += 40
            if dist_ema20 > 5:
                score += 10
        
        # Above EMA50
        if dist_ema50 and dist_ema50 > 0:
            score += 40
            if dist_ema50 > 5:
                score += 10
        
        return min(score, 100.0)
    
    def _score_momentum(self, f1d: Dict[str, Any]) -> float:
        """
        Score recent momentum (0-100).
        
        Based on recent returns.
        """
        r7 = f1d.get('r_7', 0)
        
        if r7 <= 0:
            return 0.0
        
        if r7 >= 20:  # >20% in 7 days
            return 100.0
        
        # Linear scale 0-20%
        return (r7 / 20) * 100.0
    
    def _generate_reasons(
        self,
        breakout_score: float,
        volume_score: float,
        trend_score: float,
        momentum_score: float,
        f1d: Dict[str, Any],
        f4h: Dict[str, Any],
        flags: List[str]
    ) -> List[str]:
        """Generate human-readable reasons."""
        reasons = []
        
        # Breakout
        dist = f1d.get('breakout_dist_20', 0)
        if breakout_score > 70:
            reasons.append(f"Strong breakout ({dist:.1f}% above 20d high)")
        elif breakout_score > 30:
            reasons.append(f"Moderate breakout ({dist:.1f}% above high)")
        elif dist > 0:
            reasons.append(f"Early breakout ({dist:.1f}% above high)")
        else:
            reasons.append("No breakout (below recent high)")
        
        # Volume
        vol_spike = max(f1d.get('volume_spike', 1.0), f4h.get('volume_spike', 1.0))
        if volume_score > 70:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif volume_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")
        else:
            reasons.append("Low volume (no confirmation)")
        
        # Trend
        if trend_score > 70:
            reasons.append("In uptrend (above EMAs)")
        elif trend_score > 30:
            reasons.append("Neutral trend")
        else:
            reasons.append("In downtrend (below EMAs)")
        
        # Flags
        if 'overextended' in flags:
            reasons.append(f"⚠️ Overextended ({dist:.1f}% above high)")
        
        if 'low_liquidity' in flags:
            reasons.append("⚠️ Low liquidity")
        
        return reasons


def score_breakouts(
    features_data: Dict[str, Dict[str, Any]],
    volumes: Dict[str, float],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Score all symbols for breakout setups and return ranked list.
    
    Args:
        features_data: Dict mapping symbol -> features
        volumes: Dict mapping symbol -> 24h volume
        config: Config dict
    
    Returns:
        List of scored symbols, sorted by score (descending)
    """
    scorer = BreakoutScorer(config)
    results = []
    
    logger.info(f"Scoring {len(features_data)} symbols for breakout setups")
    
    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        
        try:
            score_result = scorer.score(symbol, features, volume)
            
            results.append({
                'symbol': symbol,
                'score': score_result['score'],
                'components': score_result['components'],
                'penalties': score_result['penalties'],
                'flags': score_result['flags'],
                'reasons': score_result['reasons']
            })
            
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"Breakout scoring complete: {len(results)} symbols scored")
    
    return results

```

### `scanner/pipeline/scoring/reversal.py`

**SHA256:** `b5dca2b5ce0478ed77e32594669a93b4ac12fa9e6c682350c72fc94739b16994`

```python
"""
Reversal Setup Scoring
======================

Identifies downtrend → base → reclaim setups (like Humanity Protocol example).

Scoring Components:
1. Drawdown Context (30%) - Deep enough pullback from ATH
2. Base Quality (25%) - Consolidation without new lows
3. Reclaim Strength (25%) - Breaking back above EMAs with momentum
4. Volume Confirmation (20%) - Volume expansion on reclaim

Penalties:
- Overextension (too far above EMAs)
- Low liquidity
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ReversalScorer:
    """Scores reversal setups (downtrend → base → reclaim)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize reversal scorer.
        
        Args:
            config: Config dict with 'scoring' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            scoring_config = config.raw.get('scoring', {}).get('reversal', {})
        else:
            scoring_config = config.get('scoring', {}).get('reversal', {})
        
        # Thresholds
        self.min_drawdown = scoring_config.get('min_drawdown_pct', 40)  # Min 40% drawdown
        self.ideal_drawdown_min = scoring_config.get('ideal_drawdown_min', 50)  # 50-80% ideal
        self.ideal_drawdown_max = scoring_config.get('ideal_drawdown_max', 80)
        
        self.min_base_days = scoring_config.get('min_base_days', 10)  # Min consolidation
        self.min_volume_spike = scoring_config.get('min_volume_spike', 1.5)  # 1.5x normal
        
        self.overextension_threshold = scoring_config.get('overextension_threshold', 15)  # >15% above EMA50
        
        # Component weights
        self.weights = {
            'drawdown': 0.30,
            'base': 0.25,
            'reclaim': 0.25,
            'volume': 0.20
        }
        
        logger.info("Reversal Scorer initialized")
    
    def score(
        self,
        symbol: str,
        features: Dict[str, Any],
        quote_volume_24h: float
    ) -> Dict[str, Any]:
        """
        Score a single symbol for reversal setup.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            features: Feature dict with '1d' and '4h' sub-dicts
            quote_volume_24h: 24h volume in USDT
        
        Returns:
            Score dict with:
            - score: float (0-100)
            - components: dict of component scores
            - flags: list of condition flags
            - reasons: list of human-readable reasons
        """
        f1d = features.get('1d', {})
        f4h = features.get('4h', {})
        
        # Components
        drawdown_score = self._score_drawdown(f1d)
        base_score = self._score_base(f1d)
        reclaim_score = self._score_reclaim(f1d, f4h)
        volume_score = self._score_volume(f1d, f4h)
        
        # Weighted total
        raw_score = (
            drawdown_score * self.weights['drawdown'] +
            base_score * self.weights['base'] +
            reclaim_score * self.weights['reclaim'] +
            volume_score * self.weights['volume']
        )
        
        # Penalties & Flags
        penalties = []
        flags = []
        
        # Overextension penalty
        dist_ema50 = f1d.get('dist_ema50_pct')
        if dist_ema50 and dist_ema50 > self.overextension_threshold:
            penalties.append(('overextension', 0.7))
            flags.append('overextended')
        
        # Low liquidity penalty
        if quote_volume_24h < 500_000:  # <500K USDT
            penalties.append(('low_liquidity', 0.8))
            flags.append('low_liquidity')
        
        # Apply penalties (multiplicative)
        final_score = raw_score
        for name, factor in penalties:
            final_score *= factor
        
        # Reasons
        reasons = self._generate_reasons(
            drawdown_score, base_score, reclaim_score, volume_score,
            f1d, f4h, flags
        )
        
        return {
            'score': round(final_score, 2),
            'components': {
                'drawdown': round(drawdown_score, 2),
                'base': round(base_score, 2),
                'reclaim': round(reclaim_score, 2),
                'volume': round(volume_score, 2)
            },
            'penalties': {name: factor for name, factor in penalties},
            'flags': flags,
            'reasons': reasons
        }
    
    def _score_drawdown(self, f1d: Dict[str, Any]) -> float:
        """
        Score drawdown context (0-100).
        
        Ideal: 50-80% drawdown from ATH
        """
        dd = f1d.get('drawdown_from_ath')
        if dd is None or dd >= 0:
            return 0.0
        
        dd_pct = abs(dd)
        
        # Below minimum
        if dd_pct < self.min_drawdown:
            return 0.0
        
        # Ideal range
        if self.ideal_drawdown_min <= dd_pct <= self.ideal_drawdown_max:
            return 100.0
        
        # Below ideal (linear scale)
        if dd_pct < self.ideal_drawdown_min:
            ratio = (dd_pct - self.min_drawdown) / (self.ideal_drawdown_min - self.min_drawdown)
            return 50.0 + ratio * 50.0
        
        # Above ideal (diminishing returns)
        if dd_pct > self.ideal_drawdown_max:
            excess = dd_pct - self.ideal_drawdown_max
            penalty = min(excess / 20, 0.5)  # Max 50% penalty
            return 100.0 * (1 - penalty)
        
        return 50.0
    
    def _score_base(self, f1d: Dict[str, Any]) -> float:
        """
        Score base formation quality (0-100).
        
        Good base = consolidation without new lows.
        """
        base_detected = f1d.get('base_detected')
        
        if base_detected is None:
            return 0.0
        
        if base_detected:
            # Check volatility (ATR)
            atr = f1d.get('atr_pct')
            if atr and atr < 5:  # Very tight base
                return 100.0
            elif atr and atr < 10:  # Good base
                return 80.0
            else:
                return 60.0
        else:
            # No base detected
            return 0.0
    
    def _score_reclaim(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """
        Score reclaim strength (0-100).
        
        Strong reclaim:
        - Price above EMA20 and EMA50
        - Recent higher high
        - Positive momentum
        """
        score = 0.0
        
        # 1d reclaim
        dist_ema20 = f1d.get('dist_ema20_pct')
        dist_ema50 = f1d.get('dist_ema50_pct')
        
        # Above both EMAs
        if dist_ema20 and dist_ema20 > 0:
            score += 30
        if dist_ema50 and dist_ema50 > 0:
            score += 30
        
        # Higher high detected
        if f1d.get('hh_20'):
            score += 20
        
        # Momentum (recent returns)
        r7 = f1d.get('r_7')
        if r7 and r7 > 10:  # >10% in 7 days
            score += 20
        elif r7 and r7 > 5:
            score += 10
        
        return min(score, 100.0)
    
    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """
        Score volume confirmation (0-100).
        
        Strong volume = spike on reclaim.
        """
        vol_spike_1d = f1d.get('volume_spike', 1.0)
        vol_spike_4h = f4h.get('volume_spike', 1.0)
        
        # Use higher of the two
        max_spike = max(vol_spike_1d, vol_spike_4h)
        
        if max_spike < self.min_volume_spike:
            return 0.0
        
        # Linear scale from min to 3x
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
        flags: List[str]
    ) -> List[str]:
        """Generate human-readable reasons for the score."""
        reasons = []
        
        # Drawdown
        dd = f1d.get('drawdown_from_ath')
        if dd and dd < 0:
            dd_pct = abs(dd)
            if dd_score > 70:
                reasons.append(f"Strong drawdown setup ({dd_pct:.1f}% from ATH)")
            elif dd_score > 30:
                reasons.append(f"Moderate drawdown ({dd_pct:.1f}% from ATH)")
        
        # Base
        if base_score > 60:
            reasons.append("Clean base formation detected")
        elif base_score == 0:
            reasons.append("No base detected (still declining)")
        
        # Reclaim
        dist_ema50 = f1d.get('dist_ema50_pct')
        if reclaim_score > 60:
            reasons.append(f"Reclaimed EMAs (${dist_ema50:.1f}% above EMA50)")
        elif reclaim_score > 30:
            reasons.append("Partial reclaim in progress")
        else:
            reasons.append("Below EMAs (no reclaim yet)")
        
        # Volume
        vol_spike = max(f1d.get('volume_spike', 1.0), f4h.get('volume_spike', 1.0))
        if vol_score > 60:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif vol_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")
        
        # Flags
        if 'overextended' in flags:
            reasons.append(f"⚠️ Overextended ({dist_ema50:.1f}% above EMA50)")
        
        if 'low_liquidity' in flags:
            reasons.append("⚠️ Low liquidity")
        
        return reasons


def score_reversals(
    features_data: Dict[str, Dict[str, Any]],
    volumes: Dict[str, float],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Score all symbols for reversal setups and return ranked list.
    
    Args:
        features_data: Dict mapping symbol -> features
        volumes: Dict mapping symbol -> 24h volume
        config: Config dict
    
    Returns:
        List of scored symbols, sorted by score (descending)
    """
    scorer = ReversalScorer(config)
    results = []
    
    logger.info(f"Scoring {len(features_data)} symbols for reversal setups")
    
    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        
        try:
            score_result = scorer.score(symbol, features, volume)
            
            results.append({
                'symbol': symbol,
                'score': score_result['score'],
                'components': score_result['components'],
                'penalties': score_result['penalties'],
                'flags': score_result['flags'],
                'reasons': score_result['reasons']
            })
            
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"Reversal scoring complete: {len(results)} symbols scored")
    
    return results

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

### `docs/spec.md`

**SHA256:** `403d4986860eb1b6701c1f4af943048b035631ea6e30464d2b7e86a6c8f0d6b5`

```markdown
# Spot Altcoin Scanner – Technical Master Specification  
Version: v1.0  
Language: English (technical)  
Audience: Developer + GPT (no external stakeholders)  

---

## 1. Purpose & Scope

This document defines the **technical specification** for a Spot Altcoin Scanner intended to systematically identify **short-term trading opportunities** in the **Altcoin MidCap segment**, with a holding horizon of **days to a few weeks**.

This scanner is not a trading bot.  
It produces **daily ranked candidate lists** for three distinct setup types:

1. Breakouts (momentum-based range breaks)
2. Trend Pullbacks (trend continuation after retracement)
3. Reversals (downtrend → base → reclaim + volume)

The scanner will operate autonomously on a daily schedule and output:
- human-readable reports (Markdown)
- machine-readable data (JSON, snapshots)
- optional analytics (for backtests & performance evaluation)

---

## 2. Strategic Intent (High Level)

The scanner aims to:
- surface potential asymmetric opportunities
- filter for liquidity + tradeability
- isolate setups with clear structure
- avoid noise/pumps/illiquid microcaps
- produce consistent signals for review and evaluation

The scanner must be:
- deterministic (same input → same output)
- explainable (scores decomposable into components)
- stable under iteration (extensible without rewrites)
- versionable (spec + code + data evolution)

---

## 3. Overall Design Principles

1. **Setup Separation**
   → each signal type must be scored independently  
   → no single monolithic “global score”

2. **Cheap → Expensive Pipeline**
   → bulk filtering using lightweight metrics  
   → heavy computation (OHLCV) only on a shortlist

3. **Free-API Friendly**
   → no subscription dependencies  
   → rate-limit aware  
   → bulk queries preferred over per-asset requests  
   → caching + retries + idempotent runs

4. **Tradeability First**
   → only assets that can actually be traded (Spot, USDT pairs)

5. **MidCap Focus**
   → reduce microcap noise and mega-cap sluggishness

6. **Snapshot + Backtest Support**
   → daily historical data for performance evaluation

7. **Model > Data > Execution**
   → the scanner serves as a research model, not an executor

---

## 4. Universe Specification

The tradeable universe is defined as:

- Exchange: **MEXC**
- Venue: **Spot**
- Quote Asset: **USDT**
- Asset Class: **Altcoins**
- Market Cap Filter: **100M – 3B USD**
- Category Exclusions:
  - Stablecoins
  - Wrapped assets
  - Leveraged tokens
  - Synthetic derivatives
  - Index/ETF-like instruments

The scanner never considers:
- Futures-only assets
- Non-spot assets
- Assets without a USDT pair on MEXC

---

## 5. Data Sources (Roles)

| Source | Role | Priority |
|---|---|---|
| MEXC | trading data, universe, OHLCV | primary |
| Market Cap Provider | valuation filter | secondary |
| CSV/JSON Snapshots | historical consistency | internal |
| Backtest Engine | evaluation | internal |

Market Cap provider must support **bulk listing**.  
CoinMarketCap (CMC) Free Tier is suitable.

---

## 6. Mapping Layer (Critical Component)

MEXC tickers (e.g. `HUSDT`) must map to a Market Cap asset.  
Mapping must support:

- symbol-based matching
- collision detection
- override file
- confidence levels
- reporting for manual inspection

Incorrect mapping = corrupted scoring.  
Mapping is evaluated before OHLCV requests.

---

## 7. Pipeline Architecture (High Level)

Daily Run Pipeline:

1. Fetch Universe (MEXC Spot USDT)
2. Fetch MarketCap (bulk)
3. Mapping (MEXC ↔ MCAP)
4. Filters (Hard Gates)
5. Cheap Pass (Ticker-based shortlist selection)
6. Expensive Pass (OHLCV fetch + feature computation)
7. Scoring (Breakout / Pullback / Reversal)
8. Output (MD + JSON)
9. Snapshot (for backtests)
10. Optional Backtest (forward returns on historical snapshots)

This pipeline must be deterministic & order-stable.

---

## 8. Filters (Hard Gates)

Filters run before scoring:

1. Tradeability:
   - must have MEXC Spot USDT pair

2. Market Cap:
   - `100M ≤ MCAP ≤ 3B`

3. Liquidity:
   - `quote_volume_24h ≥ threshold` (configurable)

4. History Availability:
   - ≥ X days of 1d data (configurable, recommended: ≥ 60 days)

5. Category Exclusion:
   - stable / wrapped / leveraged / synthetic

Assets that fail gates do not proceed to scoring.

---

## 9. Timeframes & Lookbacks

Required timeframes:

- **Daily (1d)** → primary for structure + trend
- **4h** → refinement for pullback + breakout timing

Optional (future):
- **1h** (for timing & volatility)
- **Weekly (1w)** (for context)

Recommended lookbacks:

| Feature | Lookback |
|---|---|
| trend/EMA | 60–120d |
| drawdown/ATH | 120–365d |
| pullback structure | 20–60d |
| reversal base | 30–60d |
| breakout highs | 20–30d |
| volume smoothing | 7–14d |

---

## 10. Setup Taxonomy (Core Requirement)

The scanner distinguishes **three independent setup types**:

1. **Breakout**
   - Range break + volume expansion
2. **Trend Pullback**
   - established trend + retracement + rebound
3. **Reversal**
   - downtrend → base → reclaim + volume

Each setup yields its own:
- score
- ranking
- candidate list
- reasons/flags

---

## 11. Scoring Framework

Each Score:

- normalizes to 0–100
- decomposes into weighted components
- supports penalties & flags
- produces human-readable reasoning
- is independent from other scores

There is **no global combined score**  
(to prevent setup-type bias).

---

## 12. Output Specification

For each daily run:

1. Human Output (Markdown)
   - Top Breakouts
   - Top Pullbacks
   - Top Reversals
   - Key Metrics + Reasons + Flags

2. Machine Output (JSON)
   - metrics
   - features
   - scores
   - flags
   - meta (run info)
   - mapping info

3. Snapshot Storage
   - required for backtests
   - deterministic file naming

---

## 13. Backtesting Support

Backtests compute forward returns over:
- 7 days
- 14 days
- 30 days

per score type.

Additional metrics:
- hit rate
- median return
- tail losses
- distribution analysis

Backtesting is performed on stored snapshots, not live queries.

---

## 14. Versioning Model

The scanner must maintain:

- spec versions
- config versions
- code versions
- snapshot versions

Version bumps occur on:
- scoring changes
- mapping rules changes
- pipeline changes
- feature schema changes

---

## 15. Extensibility

Future-proof extensions include:

- news & sentiment feed
- DeFi TVL data
- category analytics
- market regime detection (BTC/ETH trends)
- execution layer
- parameter search
- reinforcement / optimization loops

None of these are required for v1.

---

## 16. Non-Goals / Exclusions

The scanner is not:

- an automatic trading bot
- a market prediction model
- a risk engine
- a portfolio allocator
- a DeFi on-chain analytics platform
- a sentiment engine

---

## 17. Success Criteria

The scanner is considered successful if:

- daily reports surface relevant candidates
- reversal setups like the Humanity Protocol example are captured
- Breakout and Pullback opportunities are captured
- false positives are manageable
- performance improves through iterative refinement

---

## 18. Dependencies & Constraints

Dependencies:
- Python ecosystem
- GitHub Actions / Cron
- Free APIs

Constraints:
- Rate limits
- Historical data availability
- Mapping ambiguity

---

## 19. Master Requirements Summary

- run daily
- Spot, USDT, MEXC
- MidCaps only
- 3 setup scores
- deterministic output
- free API / rate limit friendly
- scoring explainability
- snapshot + backtest support
- pipeline stability
- modular + extendable

---

## End of `spec.md`

```

### `docs/dev_guide.md`

**SHA256:** `af904b75ca1f74c0240d437ec4664ed62779810bf2aa2d74729b875911a47046`

```markdown
# Developer Guide
Version: v1.0  
Language: English  
Audience: Developer + GPT

---
## Working with AI Assistants

This project is developed with AI assistance. This guide documents the workflow.

---

## Developer Profile

**Background:**
- Not a professional developer
- Limited coding knowledge
- Works in GitHub Web Interface + Codespaces
- Needs complete, copy-paste-ready solutions

**Development Environment:**
- GitHub Web for file editing
- Codespaces for testing
- Terminal commands via Codespace terminal

---

## Standard Workflow

### 1. Code Implementation

**AI provides:**
- ✅ Complete file content (not snippets)
- ✅ Exact file path (e.g., `scanner/clients/mexc_client.py`)
- ✅ Clear instructions: "Open file X, REPLACE entire content with:"
- ✅ No partial edits unless explicitly requested

**For changes/updates:**
- ✅ "FIND this block: `[exact code]`"
- ✅ "REPLACE with: `[new code]`"
- ✅ Line numbers as reference (ca. line X)

---

### 2. Testing

**AI provides:**
- ✅ Complete test file (e.g., `test_mexc.py`)
- ✅ Where to save it (repo root)
- ✅ Single-line terminal command with `&&` chains

**Example:**
```bash
git pull origin main && python test_mexc.py
```

**NOT multiple separate commands** (error-prone)

---

### 3. Cleanup

**After successful test:**

Single command to:
- Remove test file
- Stage changes
- Commit
- Push

**Example:**
```bash
rm test_mexc.py && git add -A && git commit -m "Phase X complete" && git push origin main
```

---

### 4. Terminal Commands

**Always provide:**
- ✅ Complete commands (copy-paste ready)
- ✅ Chained with `&&` for efficiency
- ✅ No multi-step manual sequences

**Avoid:**
- ❌ "Run command A, then command B, then C"
- ❌ Multi-line Python in terminal (use test files)

---

## File Organization Rules

### New Files
- Implementation: Direct path (e.g., `scanner/clients/new_file.py`)
- Tests: Repo root (e.g., `test_feature.py`)
- Docs: `docs/` folder

### Editing Files
- Always: "Open X, REPLACE entire content" (clearest)
- For small changes: "FIND line X, REPLACE with Y"

---

## Communication Style

### AI should:
- ✅ Give complete, working code
- ✅ Provide exact file paths
- ✅ Use `&&` command chains
- ✅ Create test files for validation
- ✅ Explain WHAT is being done (briefly)
- ✅ Avoid unnecessary prose

### AI should NOT:
- ❌ Provide partial code snippets
- ❌ Say "add this somewhere in the file"
- ❌ Give multi-step manual instructions
- ❌ Assume developer knowledge

---

## Information Gathering

### Before implementing:
- ✅ **Ask for existing code/structure** if needed
- ✅ Request relevant files (e.g., "Can you upload sample_file.py?")
- ✅ Ask about repo structure/dependencies
- ✅ Verify assumptions with developer

### AI should NOT:
- ❌ Guess implementation details from other modules
- ❌ Assume function signatures without seeing code
- ❌ Trial-and-error when info is available
- ❌ Invent structure - ask the developer

**Principle:** Developer has the information. Ask first, implement second.

**Example:**
```
"Before I implement the filter, I need to see:
1. sample_file.py (upload please)
2. How your data structure looks in pipeline.py
3. How your repo structure looks like (use Output from tree -L 3)

This ensures the code works on first try."
```

---

## Error Handling

**If something fails:**

1. Show complete error output
2. AI analyzes and provides fix
3. Fix is again: complete code + exact location
4. Test again

**No guessing, no trial-and-error**

---

## Git Workflow

**Currently:**
- Direct commits to `main`
- Clean, descriptive commit messages
- Format: `"Phase X: Feature description"`

**Future:**
- Feature branches (after Phase 4)
- Will be documented when activated

---

## Session Handoff

**Between sessions / AI instances:**

1. **GPT Snapshot** in `snapshots/gpt/`
   - Contains: Status, next steps, context
   - Updated at session end

2. **Key files to reference:**
   - `snapshots/gpt/gpt_snapshot_YYYY-MM-DD.md` (latest)
   - `docs/spec.md` (master spec)
   - `docs/pipeline.md` (architecture)
   - `README.md` (project overview)

3. **First message in new session:**
```
   I'm working on spot-altcoin-scanner (GitHub: schluchtenscheisser/spot-altcoin-scanner).
   
   Please read:
   - snapshots/gpt/gpt_snapshot_YYYY-MM-DD.md (upload if needed)
   - docs/spec.md (upload if needed)
   - docs/dev_guide.md (this file)
   
   Then continue with Phase X.
   
   Remember: I'm not a developer. Provide complete code + && command chains.
```

---

## Examples

### Good: Complete Implementation
```
Create scanner/pipeline/filters.py

Content:
[complete 200 lines of code]

Then test:
python test_filters.py

Cleanup:
rm test_filters.py && git add -A && git commit -m "Phase 4.1: Filters" && git push origin main
```

### Bad: Partial Instructions
```
Add this function to filters.py somewhere:
def filter_midcaps():
    # your code here
```
(Missing: where exactly? complete context? how to test?)

---

## Tools & Technologies

- **Language:** Python 3.11+
- **Development:** GitHub Web + Codespaces
- **Testing:** Command-line execution
- **Dependencies:** See `requirements.txt`
- **APIs:** MEXC (free), CoinMarketCap (free tier)

---

## End of `dev_guide.md`

```

### `docs/features.md`

**SHA256:** `24bde7c73ef0dc963ff96a7d26a0f5b064eb389d3308a6ec10337d98718ada49`

```markdown
# Feature Engine Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

The Feature Engine converts raw OHLCV + ticker inputs into **structured technical features** used by scoring modules.

Features must be:

- deterministic
- time-consistent
- numerically stable
- snapshot-compatible
- interpretable
- minimally dependent on parameter tuning

The Feature Engine does **not** make trading decisions; it prepares the signal inputs.

---

## 2. Timeframes

v1 uses two core timeframes:

- **1d** (daily): primary structure/timeframe of the scanner
- **4h** (intra-day refinement)

Optional future timeframes:

- **1h** (timing/signal amplification)
- **1w** (macro context)

Timeframes must not be mixed in the same feature without explicit definition.

---

## 3. Lookback Requirements

Minimum recommended lookbacks:

| Feature | Lookback |
|---|---|
| Trend / EMA | 60–120 days |
| Drawdown / ATH | 120–365 days |
| Reversal Base | 30–60 days |
| Breakout Highs | 20–30 days |
| Volume SMA | 7–14 days |
| ATR Volatility | 14–30 days |

Lookbacks must be configurable via `config.yml`.

---

## 4. Input Data Requirements

Feature computation requires:

- OHLC: `open`, `high`, `low`, `close`
- Volume: `volume`
- Derived: `quote_volume` (from ticker data)
- Timestamps: aligned to UTC
- No missing candles

Missing candles must be either:
- forward-filled (preferred for 4h gaps)
- linear-filled (not preferred)
- or asset excluded if too incomplete

---

## 5. Price-Based Features

### 5.1 Returns

Returns are computed windowed and normalized:

```
r_n = close[t] / close[t-n] - 1
```

v1 windows:
- `r_1d`
- `r_3d`
- `r_7d`

Optional future:
- `r_14d`, `r_30d`

Returns computed both on 1d and 4h basis (4h for near-term changes).

---

### 5.2 Highs & Lows

Compute for `n ∈ {20, 30}`:

```
high_n = max(high[t-n .. t])
low_n = min(low[t-n .. t])
```

Used for breakout logic + pullbacks + context.

---

### 5.3 ATH + Drawdown (Context)

ATH computed over long window, e.g.:

```
ath_price = max(close[0 .. t])
drawdown = close[t] / ath_price - 1
```

Used for reversal gating and base formation, not exclusion.

---

### 5.4 HH/HL Structure (Directional Structure)

Directional structure on 1d:

```
higher_low = low[t] > low[t-k]
higher_high = high[t] > high[t-k]
```

Used for trend + reversal confirmation.

Optional context:
- consecutive HH/HL counts
- structure strength factor

---

## 6. Trend Features

### 6.1 EMA

Compute:
- `ema20`
- `ema50`

On both 1d and 4h.

Trend inference:

```
trend_up = close > ema50 and ema50 increasing
trend_down = close < ema50 and ema50 decreasing
```

Trend is used for pullback/trend gating.

---

### 6.2 Slope

Slope may be computed via log regression:

```
slope = slope_of(log(close))
```

Used indirectly; not mandatory for v1 scoring.

---

## 7. Volatility Features

Volatility measured via ATR:

```
atr = ATR(14)
atr_pct = atr / close
```

Used for:
- breakout context
- reversal stability
- penalty for extreme volatility

Optional: realized volatility windows (future).

---

## 8. Volume Features

Volume features include:

- raw volume
- volume SMA (7, 14 days)
- volume spike factor:

```
vol_spike = volume_today / volume_sma7
```

Volume assists:

| Setup | Role |
|---|---|
| Breakout | confirmation |
| Pullback | rebound strength |
| Reversal | base → reclaim confirmation |

Volume spikes must normalize across assets via SMA.

---

## 9. Pullback Features

Pullback requires:

1. established trend (↑)
2. retracement from recent highs
3. rebound attempt

Retracement measured:

```
pullback_pct = (recent_high - close) / recent_high
```

Rebound detected via HH/HL + volume + EMA recapture.

---

## 10. Reversal Features

Reversal decomposed into:

1. **Drawdown Context**  
   coin must be down significantly from ATH

2. **Base Detection**  
   base low + no new lows for `k` days

3. **Reclaim**  
   EMA20/EMA50 recapture + r_3d > threshold

4. **Volume Confirmation**  
   vol spike vs SMA

Reversal is stricter than “oscillator oversold” signals.

---

## 11. Breakout Features

Breakout decomposed into:

1. **High Break**

```
close > high_20 or close > high_30
```

2. **Volume Confirmation**

```
vol_spike ≥ threshold
```

3. **Overextension Check**

```
close / ema20 within limit
```

Breakout does not require drawdown context.

---

## 12. Liquidity Features

Ticker-based 24h quote volume is used for:

- shortlist selection
- low liquidity penalty
- backtest weighting (future)

Must be in USDT terms.

---

## 13. Flags (Derived from Features)

Feature engine must generate flags such as:

| Flag | Meaning |
|---|---|
| low_liquidity | poor tradeability |
| extreme_volatility | ATR too high |
| falling_knife | new lows + high volume |
| late_stage_move | overextended breakout |
| mapping_low_confidence | unreliable binding |

Flags affect scoring and reporting.

---

## 14. Output Format (Feature Layer)

Features must be stored per-asset per-day in JSON:

Recommended:

```
features[timeframe][feature_name]
```

Example:

```
features["1d"]["ema20"]
features["4h"]["r_4h"]
```

---

## 15. Determinism Requirements

- no stochastic components
- no random thresholds
- no forward-looking leak
- snapshot reproducibility mandatory

---

## 16. Exclusions (What Features Are Not)

Feature layer must **not** include:

- RSI, MACD, stochastic oscillators (v1)
- multi-timeframe fusion signals (v1)
- sentiment
- onchain data
- news data
- model-based predictions

These belong to future extensions and bias the scanner away from pure structural signals.

---

## 17. Integration

Feature Engine feeds:
- scoring modules
- backtests
- reports
- snapshots

It does not pull data from scoring.

---

## End of `features.md`

```

### `docs/scoring.md`

**SHA256:** `fd48fb58113908af0783f48566a7411d5cf608bbcb13aaeb9bfae3814f575a2b`

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
close > ema50 (1d)
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

## End of `scoring.md`

```

---

## 📚 Additional Resources

- **Code Map:** `docs/code_map.md` (detailed structural overview)
- **Specifications:** `docs/spec.md` (technical master spec)
- **Dev Guide:** `docs/dev_guide.md` (development workflow)
- **Latest Reports:** `reports/YYYY-MM-DD.md` (daily scanner outputs)

---

_Generated by GitHub Actions • 2026-01-17 16:51 UTC_
