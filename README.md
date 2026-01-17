# Spot Altcoin Scanner (v1)

Scanner for short-term trading setups in MidCap Altcoins  
on MEXC Spot USDT markets.

## What it does

- Builds a daily tradable universe from MEXC Spot USDT pairs
- Filters for MidCap projects (100M–3B USD market cap)
- Computes three independent setup scores:
  - Breakout
  - Trend Pullback
  - Reversal
- Outputs daily:
  - Markdown report in `reports/YYYY-MM-DD.md`
  - JSON snapshot in `snapshots/runtime/YYYY-MM-DD.json`

For full technical specification, see `/docs/spec.md` and related documents.

## Getting Started

### 1. Create a virtualenv and install deps

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts ctivate
pip install -r requirements.txt
```

### 2. Configure environment

Copy .env.example to .env and fill:

```text
CMC_API_KEY
```

Make sure your shell or tooling loads .env so the key is available.

### 3. Configure scanner

Edit config/config.yml if needed (filters, thresholds, etc.).

### 4. Run scanner (local)

```bash
Code kopieren
python -m scanner.main --mode standard
```

### Scheduling

See .github/workflows/daily.yml for a GitHub Actions example.

### Tests

```bash
Code kopieren
pytest
```

### Documentation

All specs and dev guides live in /docs.
