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
