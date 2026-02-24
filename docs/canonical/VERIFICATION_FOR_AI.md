# Verification for AI — Golden Fixtures, Invariants, Checklist (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_VERIFICATION_FOR_AI
status: canonical
rounding_policy:
  component_scores: "no rounding"
  reported_decimals_optional: 9
```

## 1) Invariants (must always hold)
- Closed-candle only
- No lookahead
- Deterministic outputs
- Score range clamped to 0..100

Cross-sectional percent_rank:
- average-rank
- IEEE-754 exact equality
- NaNs excluded from population

---

## 2) Golden Fixture Set A — MORPHOUSDT Snapshot (2026-02-21)

### 2.1 Snapshot time & last closed candles
- Snapshot time: 2026-02-21 05:10:00 UTC
- 1D last closed: 2026-02-21 00:00 UTC
- 4H last closed: 2026-02-21 04:00 UTC

### 2.2 Market/CMC snapshot inputs (MORPHOUSDT)
- quote_volume_24h_usd = 55,339,590
- market_cap_usd = 591,203,400
- price_usd = 1.556758

### 2.3 1D OHLCV-derived values (last closed)
- close_1d = 1.5769
- ema20_1d = 1.306868269
- ema50_1d = 1.281034261
- dist_ema20_pct_1d = 20.662505719
- atr_pct_rank_120_1d = 0.627358491
- r_7_1d = 33.015605230
- r_3_1d = 4.568965517

### 2.4 Breakout level (1D structure)
- high_20d_1d = 1.5334 (exclude current 1D bar)

### 2.5 4H OHLCV-derived values (last closed)
- close_4h_last_closed = 1.5586
- ema20_4h_last_closed = 1.472211725
- ema50_4h_last_closed = 1.390535901
- bb_width_rank_120_4h = 0.595833333

### 2.6 Volume spikes (SMA20, exclude current)
- volume_quote_spike_1d = 2.645454792
- volume_quote_spike_4h = 1.910802512
- spike_combined = 2.425059108

### 2.7 Distance for scoring
- dist_pct = 1.643406808

---

## 3) Expected values (authoritative)

### 3.1 Multipliers
- overextension_multiplier = 0.837578018
- anti_chase_multiplier = 0.974869956
- btc_multiplier = 1.0  (assume BTC risk-on for this fixture)

### 3.2 Component scores (0..100)
- breakout_distance_score = 62.868136160
  - authoritative value derived from canonical curve in `SCORING/SCORE_BREAKOUT_TREND_1_5D.md` §7.1
- volume_score = 92.505910842
- bb_score = 40.625000000
- trend_score = 100.000000000

### 3.3 Base score (weighted sum)
- base_score = 75.474666451

### 3.4 Final score
- final_score = base_score * anti_chase_multiplier * overextension_multiplier * btc_multiplier
- final_score = 61.627302645

---

## 4) Negative Fixture Set B — BTC Risk-Off without RS override => Excluded
Arrange (synthetic):
- btc_risk_on = false
- quote_volume_24h_usd (alt) = 20,000,000
- alt_r7_1d - btc_r7_1d = 7.49
- alt_r3_1d - btc_r3_1d = 3.49
Assert: setup invalid/excluded.

## 5) Negative Fixture Set C — Overextension boundary => Excluded
Arrange: dist_ema20_pct_1d = 28.0
Assert: excluded because hard gate is strict: dist_ema20_pct_1d < 28.0
