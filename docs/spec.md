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
