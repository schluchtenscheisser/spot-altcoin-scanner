ARCHIVED: Superseded by `docs/canonical/OUTPUT_SCHEMA.md`.

Start here: `docs/canonical/INDEX.md`

# Data Model Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

This document defines the **data models** used throughout the scanner system.  
The data model enables:

- deterministic snapshots
- backtests
- reproducible scoring
- debugging
- versioned config evolution

Data models must be stable, explicit, and backward-aware.

---

## 2. Design Principles

Data models must:

- separate human vs machine data
- avoid implicit inference
- include provenance metadata
- be JSON-serializable
- support versioning
- be deterministic and order-stable
- survive multiple iterations

Snapshot models must support future replay/backtest.

---

## 3. Primary Data Objects

Primary data objects:

1. Universe Object
2. Asset Object
3. Market Cap Object
4. Feature Object
5. Score Object (3 types)
6. Snapshot Object
7. Backtest Input/Output

Each object described below.

---

## 4. Universe Object

Represents the set of assets tradeable at run time.

```json
{
  "timestamp": "2025-01-12T00:00:00Z",
  "exchange": "MEXC",
  "quote_asset": "USDT",
  "assets": ["H", "ABC", "XYZ", "..."],
  "count": 213,
  "meta": {
    "filters": ["usdt_pairs_only"]
  }
}
```

Universe object is deterministic for the day.

---

## 5. Asset Object

Represents a single tradeable asset.

```json
{
  "symbol": "HUSDT",
  "base": "H",
  "quote": "USDT",
  "tradeability": {
    "spot": true,
    "futures": false
  },
  "24h": {
    "price": 1.32,
    "quote_volume": 1234567.89,
    "base_volume": 932111.10,
    "change_24h_pct": 12.3
  }
}
```

This object feeds:
- filtering
- shortlist
- mapping

---

## 6. Market Cap Object

Represents valuation metadata.

```json
{
  "cmc_id": 12345,
  "symbol": "H",
  "slug": "humanity-protocol",
  "name": "Humanity Protocol",
  "market_cap_usd": 850000000,
  "rank": 142,
  "circulating_supply": 1234000000,
  "last_updated": "2025-01-12T00:00:00Z"
}
```

Market cap object connects via Mapping Layer.

---

## 7. Mapping Object

Defines binding between MEXC asset and CMC asset.

```json
{
  "base": "H",
  "cmc_id": 12345,
  "confidence": "high",
  "method": "symbol_exact",
  "collision": false,
  "override": false
}
```

Mapping object must appear in snapshot for reproducibility.

---

## 8. Feature Object

Features computed per asset per timeframe:

```json
{
  "asset": "H",
  "timeframe": "1d",
  "features": {
    "r_1d": 0.12,
    "r_3d": 0.28,
    "ema20": 1.20,
    "ema50": 1.05,
    "atr_pct": 0.15,
    "high_30d": 1.35,
    "drawdown": -0.65,
    "vol_sma7": 820000,
    "vol_spike": 2.1
  }
}
```

Timeframe must be explicit.

---

## 9. Score Object

Scoring must produce three independent score objects:

### 9.1 Breakout Score

```json
{
  "asset": "H",
  "setup": "breakout",
  "score": 82.3,
  "normalized": 0.823,
  "components": {
    "price_break": 0.88,
    "volume_confirmation": 0.91,
    "volatility_context": 0.70
  },
  "penalties": {
    "low_liquidity": false,
    "late_stage": false
  },
  "flags": ["volume_confirmed"],
  "rank": 3
}
```

### 9.2 Pullback Score

```json
{
  "asset": "H",
  "setup": "pullback",
  "score": 71.5,
  "normalized": 0.715,
  "components": {
    "trend_quality": 0.80,
    "pullback_quality": 0.67,
    "rebound_signal": 0.65
  },
  "flags": ["trend_confirmed"],
  "rank": 10
}
```

### 9.3 Reversal Score

```json
{
  "asset": "H",
  "setup": "reversal",
  "score": 91.2,
  "normalized": 0.912,
  "components": {
    "base_structure": 0.85,
    "reclaim_signal": 0.95,
    "volume_confirmation": 0.93
  },
  "flags": ["drawdown", "base", "reclaim"],
  "rank": 1
}
```

---

## 10. Snapshot Object (Critical)

Snapshot must store:

```json
{
  "timestamp": "2025-01-12T00:00:00Z",
  "spec_version": "1.0",
  "config_version": "1.0",
  "universe": { "...": "..." },
  "mapping": { "...": "..." },
  "market_caps": { "...": "..." },
  "features": { "...": "..." },
  "scores": {
    "breakout": ["..."],
    "pullback": ["..."],
    "reversal": ["..."]
  },
  "meta": {
    "runtime_ms": 8123,
    "asset_count": 142,
    "shortlist_count": 100
  }
}
```

Snapshots drive backtesting and regression.

---

## 11. Backtest I/O Model

Backtest consumes snapshots and emits evaluation metrics:

### 11.1 Backtest Input

```json
{
  "asset": "H",
  "setup": "reversal",
  "date": "2025-01-12",
  "entry_price": 1.20,
  "forward_prices": {
    "7d": 1.60,
    "14d": 1.90,
    "30d": 2.45
  }
}
```

### 11.2 Backtest Output

```json
{
  "setup": "reversal",
  "metrics": {
    "hit_rate": 0.42,
    "median_return_7d": 0.33,
    "median_return_14d": 0.52,
    "median_return_30d": 0.85,
    "tail_loss_7d": -0.18
  },
  "sample_size": 187
}
```

---

## 12. Human Output Model (Markdown)

Markdown output must be human-review oriented, not snapshot-format.

Example:

```
Top Reversals (v1)
------------------
1. H — score 91 — reclaim + volume spike
2. XYZ — score 87 — deep base + reclaim
```

Markdown and JSON serve different consumers.

---

## 13. Determinism Requirements

Data models must guarantee:

- stable ordering
- same score & features for same input
- deterministic serialization
- no randomization

---

## 14. Versioning

Data model changes → version bump:

- snapshot version
- spec version

Backward compatibility optional but desirable.

---

## 15. Anti-Goals

Data model must not:

- mix scoring & execution
- infer semantics implicitly
- hide penalties or flags
- lose provenance metadata
- mutate between backtest runs

---

## 16. Extensibility

Future extensions may include:

- category metadata
- sentiment metadata
- TVL metadata
- derivatives metadata
- factor models
- market regime indicators

None require refactoring of v1 structure.

---

## End of `data_model.md`
