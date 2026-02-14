# Phase Appendix: Features & Scoring (Conflict-Reduced Reference)

This file contains phase-specific additions that change more frequently and previously caused repeated merge conflicts when appended at the end of high-traffic docs.

## Features appendix

### Quote Volume (Thema 7)
- `volume_quote`
- `volume_quote_sma`
- `volume_quote_spike`
- legacy compatibility key: `volume_quote_sma_14`

If quote-volume is unavailable, these keys remain present with `null` values for schema stability.

### Volume Baseline per Timeframe
- Primary config: `features.volume_sma_periods` with explicit values per timeframe (e.g. `1d=14`, `4h=7`).
- Legacy fallback: `features.volume_sma_period` applies to all timeframes if `volume_sma_periods` is missing.
- Baseline uses `include_current=False` (current candle excluded).
- Output keys per timeframe: `volume_sma`, `volume_sma_period`, `volume_spike`, `volume_quote_sma`, `volume_quote_spike`.
- Legacy keys (`volume_sma_14`, `volume_quote_sma_14`) remain for backward compatibility.

### Reversal Base Features (Phase 2)
For timeframe `1d`, base detection is config-driven via:
- `scoring.reversal.base_lookback_days`
- `scoring.reversal.min_base_days_without_new_low`
- `scoring.reversal.max_allowed_new_low_percent_vs_base_low`

Additional output fields:
- `base_low`
- `base_recent_low`
- `base_range_pct`
- `base_no_new_lows_pass`

`base_score` is `None` if insufficient candles for the configured lookback.

---

## Scoring appendix

### Reversal Score Transparency
Reversal scorer outputs include:
- `raw_score`
- `penalty_multiplier`
- `final_score` (same numeric value as `score`, before display rounding differences)

Volume component prefers `volume_quote_spike` if available; otherwise it falls back to `volume_spike`.

### Phase 3 Deterministic Scoring Curves
- Breakout component `breakout_dist_20` uses explicit piecewise mapping with
  `breakout_curve.floor_pct`, `min_breakout_pct`, `ideal_breakout_pct`, and `max_breakout_pct`.
- Breakout adds info flag `overextended_breakout_zone` if `breakout_dist_20 > breakout_curve.overextended_cap_pct`.
- Breakout overextension penalty is tied to `dist_ema20_pct > penalties.max_overextension_ema20_percent`.
- Breakout and Pullback volume components prefer `volume_quote_spike` over `volume_spike` whenever available.
