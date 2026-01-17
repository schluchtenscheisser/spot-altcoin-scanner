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
