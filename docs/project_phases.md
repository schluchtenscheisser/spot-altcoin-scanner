# Project Development Phases

This document defines the development phases for the Spot Altcoin Scanner MVP.

---

## Overview

**Total Phases:** 6  
**Estimated Total Time:** ~6-7 hours  
**Status:** Phase 1-3 complete (as of 2026-01-17)

---

## Phase 1: Foundation ✅

**Duration:** ~30 minutes  
**Status:** Complete  

**Components:**
- `scanner/utils/logging_utils.py` - Logging system
- `scanner/utils/time_utils.py` - Time utilities (UTC)
- `scanner/utils/io_utils.py` - File I/O + caching
- `scanner/config.py` - Configuration loader
- `requirements.txt` - Dependencies

**Deliverables:**
- Working logger
- Config loading from YAML
- Caching infrastructure

**Tests:**
- Config loading test
- Logger output test

---

## Phase 2: Data Clients ✅

**Duration:** ~60 minutes  
**Status:** Complete  

**Components:**
- `scanner/clients/mexc_client.py` - MEXC API
  - Universe loading (1837 USDT pairs)
  - 24h ticker data
  - OHLCV (klines) fetching
  - Rate-limit handling
  
- `scanner/clients/marketcap_client.py` - CoinMarketCap API
  - Bulk listings (5000 coins)
  - Market cap data
  - Symbol map builder

**Deliverables:**
- MEXC universe: 1837 tradable pairs
- CMC data: 5000 coins with market cap
- Caching for both APIs

**Tests:**
- MEXC symbol fetch
- CMC listings fetch
- Klines fetch for BTC

---

## Phase 3: Mapping Layer ✅

**Duration:** ~30 minutes  
**Status:** Complete  

**Components:**
- `scanner/clients/mapping.py` - Symbol mapping
  - MEXC ↔ CMC linking
  - Confidence scoring
  - Collision detection
  - Override system
  - Report generation

**Deliverables:**
- 88.4% mapping success (1624/1837)
- Reports: unmapped, collisions, stats
- Override suggestions

**Tests:**
- Full universe mapping
- Report generation
- Override loading

---

## Phase 4: Pipeline 🔄

**Duration:** ~90 minutes  
**Status:** In Progress  

### Phase 4.1: Filters (~30min)

**File:** `scanner/pipeline/filters.py`

**Functionality:**
- MidCap filter (100M-3B USD)
- Liquidity filter (min volume)
- Exclusions (stables, wrapped, leveraged)
- History availability check

**Deliverables:**
- Filtered universe (estimated: ~200-400 coins)

---

### Phase 4.2: Shortlist (~15min)

**File:** `scanner/pipeline/shortlist.py`

**Functionality:**
- Cheap-pass ranking (by volume)
- Top N selection (configurable, default: 100)
- Pre-OHLCV reduction

**Deliverables:**
- Shortlist of candidates for expensive operations

---

### Phase 4.3: OHLCV Fetching (~20min)

**File:** `scanner/pipeline/ohlcv.py`

**Functionality:**
- Fetch klines only for shortlist
- 1d + 4h timeframes
- Caching per symbol
- Error handling

**Deliverables:**
- OHLCV data for shortlist (100 assets)

---

### Phase 4.4: Feature Engine (~45min)

**File:** `scanner/pipeline/features.py`

**Functionality:**
- Price features: returns (1d/3d/7d), HH/HL
- Trend features: EMA20/50
- Volatility: ATR%
- Volume: spike detection, SMA
- Structure: breakout distance, drawdown, base detection

**Deliverables:**
- Feature dict per asset
- 1d + 4h features

---

## Phase 5: Scoring Modules 🔜

**Duration:** ~90 minutes  
**Status:** Not started  

### Phase 5.1: Breakout Score (~30min)

**File:** `scanner/pipeline/scoring/breakout.py`

**Criteria:**
- Price > 20d/30d high
- Volume spike
- Low volatility before break
- Overextension penalty

---

### Phase 5.2: Pullback Score (~30min)

**File:** `scanner/pipeline/scoring/pullback.py`

**Criteria:**
- Established uptrend (EMA50)
- Pullback to EMA20/50
- Rebound signal
- Volume confirmation

---

### Phase 5.3: Reversal Score (~30min)

**File:** `scanner/pipeline/scoring/reversal.py`

**Criteria:**
- Drawdown from ATH (40-90%)
- Base formation (no new lows)
- Reclaim EMA20/50
- Volume expansion

**Priority:** Highest (key use case)

---

## Phase 6: Output & Reports 🔜

**Duration:** ~30 minutes  
**Status:** Not started  

**Components:**
- `scanner/pipeline/output.py` - Report generation
  - Markdown reports (human-readable)
  - JSON output (machine-readable)
  
- `scanner/pipeline/snapshot.py` - Snapshot system
  - Daily snapshots for backtests
  - Metadata inclusion

- `scanner/main.py` - Pipeline orchestration
  - CLI entry point
  - Mode handling
  - Error handling

**Deliverables:**
- Daily markdown report
- JSON snapshot
- Runnable `python -m scanner.main`

---

## Post-MVP (Future)

### Phase 7: Backtesting
- Forward returns (7/14/30d)
- Performance metrics
- Score validation

### Phase 8: Enhancements
- News/sentiment (optional)
- DeFi TVL data (optional)
- Regime filters (BTC/ETH)
- Dashboard (optional)

---

## Milestones

- [x] **M1:** Data Layer Complete (Phase 1-3) - 2026-01-17
- [ ] **M2:** Pipeline Complete (Phase 4) - Target: 2026-01-18
- [ ] **M3:** MVP Complete (Phase 5-6) - Target: 2026-01-19
- [ ] **M4:** Backtesting (Phase 7) - TBD

---

## End of Document
