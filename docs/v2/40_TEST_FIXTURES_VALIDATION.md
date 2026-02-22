# Test‑Fixtures & Validierungsstrategie (v2) – Canonical

**Status:** Canonical v2 (für GPT‑Codex)  
**Datum:** 2026-02-18  

## Ziel
Codex‑sichere Entwicklung: deterministische Golden‑Fixtures + Unit‑Invarianten verhindern Fehlinterpretationen.

## Ordner (Repo‑konform)
- Tests: `tests/`
- Golden: `tests/golden/`
- Golden Fixtures: `tests/golden/fixtures/`

## Must‑have Unit Tests
### 1) EMA & ATR Definitionen
- EMA: SMA‑Seed bei Index `n-1`, Standard‑EMA Rekursion
- ATR: TR‑Definition + Wilder Seed + Wilder Smoothing

### 2) percent_rank Population
- Universe nach Hard Gates (N groß) vs Shortlist (N klein) → percent_rank muss Universe nutzen

### 3) Global Ranking Einmaligkeit & Weights
- Coin mit mehreren Setups → best_setup korrekt, Coin erscheint global nur einmal

### 4) Orderbook Budget (Top‑K)
- Sicherstellen, dass Orderbook‑Fetch <= K pro Run

### 5) Slippage Berechnung
- deterministisches Orderbook‑Fixture → erwartete `slippage_bps` innerhalb Toleranz

### 6) Backtest (E2‑K)
- Trigger innerhalb T_trigger_max
- hit_10/hit_20 korrekt
- no‑lookahead

### 7) Historie‑Gate
- Lege für jedes Setup mindestens zwei Fixtures an:
  1. **Insufficient history:** Die OHLCV‑Serie ist kürzer als die in der Konfiguration definierten `min_history_*`‑Schwellen. `is_valid_setup` muss `False` sein, und das Ergebnis soll den Grund „insufficient history“ enthalten.
  2. **Sufficient history:** Die OHLCV‑Serie erfüllt die Schwellenwerte. Das Setup darf an dieser Stelle nicht aufgrund der Historie invalide werden (andere Gate‑Regeln können natürlich greifen).

## Golden Fixtures (Minimum)
- Setup‑Validity: je Setup valide + invalide + fast‑valide (Watchlist)
- Liquidity Grade: A/B/C/D + “insufficient depth”
- Ranking: confluence + ties
- Backtest: trigger/hit / trigger/no hit / no trigger

## Property / Invarianten
- Closed‑candle only (keine Nutzung der aktuellen Candle in Baselines)
- No‑lookahead (t+1 darf nicht in Features/Score)
- Score Range bleibt 0–100

## Doc↔Code Drift Guard
- Konsistenztests für EMA/ATR und Re‑Rank Regel (Sort Keys) – wenn abweichend: Test fail.

## Breakout Trend 1–5D (Immediate + Retest) — Fixtures & Validation (NEU)

### Fixture Set A: MORPHOUSDT Snapshot 2026-02-21 (05:10 UTC)

**Snapshot Zeit:** 2026-02-21 05:10:00 UTC  
**Last closed candles (Closed-Candle Reality):**
- 1D last closed: close_time = 2026-02-21 00:00 UTC
- 4H last closed: close_time = 2026-02-21 04:00 UTC

#### A1) Golden Inputs (MORPHOUSDT)

**Market/CMC snapshot**
- `quote_volume_24h_usd` = 55,339,590
- `market_cap_usd` = 591,203,400
- `price_usd` = 1.556758

**1D OHLCV (last closed candle @ 2026-02-21 00:00)**
- `close_1d` = 1.5769
- `ema20_1d` = 1.306868269
- `ema50_1d` = 1.281034261
- `dist_ema20_pct_1d` = 20.662505719
- `dist_ema50_pct_1d` = 23.095849054
- `atr_pct_1d` = 7.903712459
- `atr_pct_rank_120_1d` = 0.627358491
- `r_7_1d` = 33.015605230
- `r_3_1d` = 4.568965517

**Breakout Level (1D structure)**
- `high_20d_1d` = 1.5334
  - Definition: max high over bars [t1d-20 .. t1d-1] excluding current 1D bar

**4H OHLCV (last closed candle @ 2026-02-21 04:00)**
- `close_4h_last_closed` = 1.5586
- `ema20_4h_last_closed` = 1.472211725
- `ema50_4h_last_closed` = 1.390535901
- `bb_width_pct_4h_last_closed` = 17.072137112
- `bb_width_rank_120_4h` = 0.595833333

**Volume spikes (SMA20 EXCLUDE current)**
- `volume_quote_spike_1d` = 2.645454792
- `volume_quote_spike_4h` = 1.910802512
- `spike_combined` = 2.425059108
  - Definition: 0.7*spike_1d + 0.3*spike_4h

**Distance for scoring (4H close vs level)**
- `dist_pct = ((close_4h_last_closed / high_20d_1d) - 1) * 100` = 1.643406808

#### A2) Golden Multipliers & Component Scores (MORPHOUSDT)

**Overextension multiplier (d=20.6625)**
- Expected: `overextension_multiplier` = 0.837578018  
  (piecewise: 20<d<28 linear 0.85→0.70)

**Anti-Chase multiplier (r7=33.0156)**
- Expected: `anti_chase_multiplier` = 0.974869956  
  (30..60 linear 1.0→0.75)

**BB score (rank=0.595833333)**
- Expected: `bb_score` = 40.625000000  
  (0.20..0.60 linear 100→40)

**Volume score (spike_combined=2.425059108)**
- Expected: `volume_score` = 92.505910842  
  (1.5..2.5 linear 0→100)

**Breakout distance score (dist_pct=1.6434)**
- Must use the exact legacy curve from `scanner/pipeline/scoring/breakout.py` with:
  - floor=-5, min=2, ideal=5, max=20
- This fixture asserts that the *input* `dist_pct` is correct; the exact score should match the implemented curve.

**Trend gate check (must pass)**
- `ema20_1d > ema50_1d` => True
- `close_1d > ema20_1d` => True

**ATR gate check (must pass)**
- `atr_pct_rank_120_1d <= 0.80` => True

**Overextension hard gate check (must pass)**
- `dist_ema20_pct_1d < 28.0` => True

**Momentum gate check (must pass)**
- `r_7_1d > 0` => True

---

### Fixture Set B: Negative — BTC Risk-Off without RS Override => Excluded

**Goal:** When BTC is Risk-Off and the coin does not meet RS override, the setup must be invalid/excluded.

**Arrange (synthetic inputs):**
- `btc_risk_on = False`
- `quote_volume_24h_usd` of alt: 20,000,000 (passes risk-off liquidity)
- RS differences:
  - `alt_r7 - btc_r7 = 7.49` (just below 7.5)
  - `alt_r3 - btc_r3 = 3.49` (just below 3.5)

**Assert:**
- RS override == False
- Setup invalid (coin excluded from both Immediate/Retest lists)
- `btc_multiplier` must not be applied because candidate is excluded.

---

### Fixture Set C: Negative — Overextension Hard Gate => Excluded

**Arrange (synthetic inputs):**
- `dist_ema20_pct_1d = 28.0` (boundary)

**Assert:**
- Setup invalid (excluded), because hard gate requires `< 28.0`.

---

### Deterministic Unit Tables (no market data required)

#### D1) Anti-Chase Multiplier
Parameters:
- start=30, full=60, min=0.75

| r_7_1d | expected multiplier |
|-------:|---------------------:|
| 29.9   | 1.000000000          |
| 30.0   | 1.000000000          |
| 45.0   | 0.875000000          |
| 60.0   | 0.750000000          |
| 60.1   | 0.750000000          |

#### D2) Overextension Multiplier
Parameters:
- start=12 -> 1.0
- strong=20 -> 0.85
- hard gate at 28 (excluded)

| dist_ema20_pct_1d | expected |
|------------------:|---------:|
| 11.9              | 1.000000 |
| 12.0              | 1.000000 |
| 16.0              | 0.925000 |
| 20.0              | 0.850000 |
| 27.9              | 0.701875 |
| 28.0              | EXCLUDED |

#### D3) BB Score (rank)
Parameters:
- <=0.20 => 100
- 0.20..0.60 => linear 100→40
- >0.60 => 0

| bb_width_rank_120_4h | expected bb_score |
|---------------------:|------------------:|
| 0.20                 | 100.0             |
| 0.40                 | 70.0              |
| 0.60                 | 40.0              |
| 0.61                 | 0.0               |

#### D4) ATR Gate (rank)
Parameter:
- max_rank = 0.80

| atr_pct_rank_120_1d | expected |
|--------------------:|---------:|
| 0.80                | PASS     |
| 0.81                | EXCLUDED |

---

