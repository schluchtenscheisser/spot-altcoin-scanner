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
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
