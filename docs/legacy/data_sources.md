# Data Sources & Data Roles
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Overview

This document defines all external and internal data sources used by the scanner, and assigns **roles**, **constraints**, and **access patterns**.

Data sources are organized into the following functional groups:

1. **Primary Trading Data**
2. **Market Cap & Valuation Data**
3. **Historical OHLCV Data**
4. **Snapshots**
5. **Backtest Data**
6. **Derived Metadata (internal)**

---

## 2. Design Principles for Data Access

- **Role separation** (data source must have a single purpose)
- **Free API friendly**
- **Bulk access preferred**
- **Deterministic + reproducible**
- **Stateless acquisition**
- **Separation of cheap vs expensive queries**
- **Fail fast on mapping failures**
- **Cache-friendly**
- **Idempotent**

---

## 3. Primary Trading Data: MEXC

### 3.1 Role

MEXC defines **tradeability** and supplies:

- Spot market listings
- Quote currency pairs (e.g., `HUSDT`)
- 24h ticker data (volumes, price change)
- OHLCV data for selected intervals (1d and 4h)

### 3.2 Why MEXC?

- matches personal trading environment
- robust spot listing coverage
- accessible free API endpoints
- clear universe definition
- avoids non-tradeable signals

### 3.3 Required Endpoints

Minimum endpoints:

| Endpoint | Purpose |
|---|---|
| `/exchangeInfo` | list spot markets + base/quote assets |
| `/ticker/24hr` | liquidity + volume + 24h metrics |
| `/klines` | OHLCV for 1d + 4h |

### 3.4 Query Strategy

MEXC usage follows the principle:

```
listings (cheap) → filter → shortlist → klines (expensive)
```

24h ticker data is cheap and bulk; OHLCV is per-symbol and expensive.

---

## 4. Market Cap & Valuation Data

### 4.1 Role

Market cap is used for:

- **midcap filtering** (100M–3B)
- **valuation context**
- **liquidity sanity checks**
- optional future metrics (e.g., MC/Volume)

### 4.2 Provider Requirements

Provider must support:

- bulk listing of all assets
- market_cap, rank, supply data
- stable asset identifiers
- minimum daily update cadence

### 4.3 Preferred Provider

**CoinMarketCap (CMC Free Tier)** satisfies:

- bulk listing
- free tier access
- common identifiers (id, slug, symbol)
- consistent updates

### 4.4 Constraints

Not suitable for OHLCV or fast pricing.  
Used only once per daily run.

---

## 5. OHLCV Data

### 5.1 Required Timeframes

- **1d** for structural trend analysis
- **4h** for intra-day refinement

These are fetched only for the shortlist.

### 5.2 Precision vs Frequency

| Timeframe | Usage |
|---|---|
| 1d | trend, HH/HL, drawdown, reversal, breakout |
| 4h | pullback confirmation, breakout timing |

### 5.3 Lookback Requirements

| Use Case | Lookback |
|---|---|
| Trend | 60–120d |
| Reversal base | 30–60d |
| Breakout | 20–30d |
| Volatility | 14–30d |

Lookbacks must remain configurable.

---

## 6. Historical Snapshots (Internal)

Snapshots store:

- features
- scores
- mapping info
- universe info
- config + spec version
- runtime metadata

Purpose:

- reproducible backtests
- regression testing
- score evolution tracking
- debugging

Snapshot format: JSON

---

## 7. Backtest Data (Internal)

Backtest operates on snapshots.  
Forward returns (7/14/30d) are computed from stored prices.

No live queries for backtesting.  
Backtests must be deterministic.

---

## 8. Additional Optional Sources (Future)

These do not belong in v1:

- News / sentiment (CryptoPanic, Telegram, Twitter)
- DeFi TVL (DeFiLlama)
- Onchain metrics
- BTC/ETH regime filters
- Category/sector metadata
- Exchange listings
- Funding rate data (for derivatives)

The architecture allows extension without breaking v1.

---

## 9. Data Source Summary Table

| Data Source | Role | Frequency | Access | Required |
|---|---|---|---|---|
| MEXC | Universe + OHLCV + liquidity | Daily | API | Yes |
| CMC (or equiv) | Market Cap Filter | Daily | API | Yes |
| Snapshots | Backtest & Regression | Daily | FS | Yes |
| Backtest Engine | Evaluation | On-demand | Internal | Yes |
| Sentiment | Optional | Optional | API | No |
| Onchain | Optional | Optional | API | No |

---

## 10. Key Constraints Summary

- No mixed-role providers
- No multi-source OHLCV
- No per-asset market cap lookups
- Bulk-first, fetch-later pattern
- Snapshot-first backtesting

---

## End of `data_sources.md`
