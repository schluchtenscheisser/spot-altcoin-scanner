# Pipeline & System Architecture
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Overview

The scanner operates as a **deterministic daily batch pipeline**.  
Every run produces a ranked set of candidates for three distinct setup types:

- Breakout
- Trend Pullback
- Reversal

The pipeline is designed around three core constraints:

1. **Free API & Rate Limits**
2. **Cheap → Expensive Execution Order**
3. **Snapshot + Backtest Compatibility**

---

## 2. Architectural Style

The system is architected as:

- **modular**
- **functional**
- **stateless across runs**
- **stateful via snapshots**

There is no daemon/process-server.  
Execution is initiated via:

- Cron scheduler (e.g. GitHub Actions)
- manual invocation (local development)

---

## 3. Core Pipeline (Daily Run)

Full run (conceptual):

```
(1) Fetch Universe
(2) Market Cap Fetch
(3) Mapping + Confidence
(4) Filter Gate
(5) Cheap Pass (Ticker-based shortlist)
(6) OHLCV Fetch (for shortlist)
(7) Feature Computation
(8) Scoring (3 independent modules)
(9) Output (MD + JSON)
(10) Snapshot
(11) Optional Backtest
```

All steps must be **reproducible**, **idempotent** and **order-stable**.

---

## 4. Step-by-Step Description

### (1) Fetch Universe

Source: **MEXC Spot USDT**

Actions:
- query exchange info / symbols endpoint
- extract all tradable `*/USDT` pairs
- normalize tickers (base_asset, quote_asset)
- validate Spot availability

Universe at this point = `tradeable_usdt_universe`

---

### (2) Market Cap Fetch (Bulk)

Source: **Market Cap Provider (CMC or similar)**

Requirements:
- single bulk call for listings
- map symbol + slug + id
- obtain:
  - market_cap_usd
  - circulating_supply
  - FDV (optional)
  - rank
  - last_updated

No per-asset fetch; bulk is mandatory.

---

### (3) Mapping & Confidence Layer

Goal: link MEXC base asset → MarketCap asset

Mechanisms:
- direct symbol match
- symbol normalization
- collision detection
- override file (manual fix)
- confidence scoring (high/medium/low)

Outputs:
- mapped asset or filtered out
- mapping report
- collision report (for manual review)
- confidence flags

---

### (4) Filter Gate (Hard Filters)

All filters must pass:

- must be tradable on MEXC Spot USDT
- market_cap in configured range (100M–3B)
- minimum liquidity (`volume_24h`)
- minimum historical data requirement
- exclusion categories:
  - stablecoins
  - wrapped tokens
  - leveraged tokens
  - synthetic derivatives

Failure → asset removed from pipeline.

---

### (5) Cheap Pass (Ticker Shortlist)

Goal: reduce N → K before OHLCV fetch

Cheap features include:
- 24h quote volume
- 24h return
- 24h price change %
- simple vol spike (vs 7d if cached)

Ranking:
- ordered by liquidity first
- then optional momentum/vol filters

Result: shortlist of size K (e.g. 80–120 assets)

---

### (6) Expensive Pass (OHLCV Fetch)

For shortlist only.

Fetch:
- **1d OHLCV** (60–120 days)
- **4h OHLCV** (14–60 days)

These datasets feed the Feature Engine.

---

### (7) Feature Computation

Features computed on `1d` and `4h`:

- returns (1d, 3d, 7d)
- HH/HL structures
- EMA20/EMA50
- ATR%
- breakout highs (20–30d)
- base/reversal metrics
- volume spike (vs SMA7)
- drawdown (ATH / context)

All features must be deterministic & snapshot-compatible.

---

### (8) Scoring (3 Independent Modules)

Inputs: features + flags

Modules:
1. Breakout Score
2. Trend Pullback Score
3. Reversal Score

Outputs:
- score 0–100
- normalized score 0–1
- rank
- components (weighted)
- penalties
- flags
- setup-specific metadata

No global fusion scoring.

---

### (9) Output Layer

Two primary outputs:

(1) Human (Markdown):
- Top Breakouts
- Top Pullbacks
- Top Reversals
- contextual metrics
- reasoning + flags

(2) Machine (JSON):
- full metrics
- features
- scores
- flags
- mapping info
- meta info

Outputs are snapshot-stored.

---

### (10) Snapshot Storage

Snapshots contain:
- daily universe
- input data hashes
- features
- scores
- config version
- spec version

Snapshots enable:
- reproducible backtests
- regression analysis
- scoring evolution
- cross-version consistency checks

---

### (11) Optional Backtest

Backtest runs on snapshots only; never live.

Forward Returns:
- +7d
- +14d
- +30d

Evaluated per setup type.

---

## 5. Execution Modes

Scanner must support:

| Mode | Purpose |
|---|---|
| standard | full pipeline |
| fast | skips expensive fetch (cached only) |
| offline | uses snapshot data only |
| backtest | compute forward returns only |

Modes are set via ENV or config.

---

## 6. Rate Limit Strategy

Principles:
- bulk fetch > per asset fetch
- caching where deterministic
- retries with exponential backoff
- 429/5xx resilience
- idempotent progression

Cheap→expensive ensures rate compliance.

---

## 7. Determinism Requirements

Pipeline must guarantee determinism for:
- ranking
- scoring
- output order
- penalty logic

Determinism is required for backtests.

---

## 8. Failure & Error Handling

Hard failures:
- mapping failure (uncorrectable)
- no market cap
- missing OHLCV
- insufficient data

Soft failures:
- low confidence mapping
- extreme volatility
- falling knife risk
- low liquidity

Soft failures influence scores & flags.

---

## 9. Deployment & Scheduling

Preferred runs:
- GitHub Actions (cron)
- UTC midnight or post EOD
- snapshot retained in repo or storage

---

## 10. Extensibility Requirements

Pipeline structure must allow future extensions:

- sentiment
- news
- defi categories
- market regime filters
- execution engine
- portfolio allocations

Core architecture must not require rewrite to add extensions.

---

## 11. Summary Diagram (ASCII)

```
      [MEXC Symbols]
             |
             v
  [Tradeable USDT Universe]
             |
             v
   [Market Cap Bulk Fetch]
             |
             v
       [Mapping Layer]
             |
             v
     [Filter Gate (hard)]
             |
             v
   [Cheap Pass (shortlist)]
             |
             v
[OHLCV Fetch (1d + 4h only)]
             |
             v
   [Feature Computation]
             |
             v
  +-----------+------------+
  |           |            |
  v           v            v
[Breakout] [Pullback] [Reversal]
     |         |         |
     +-----------+--------+
                 |
                 v
          [Report + JSON]
                 |
                 v
              [Snapshot]
                 |
                 v
              [Backtest]
```

---

## End of `pipeline.md`
