# PR0 — Breakout Trend 1–5D: v2 Docs + Ticket Queue (Docs-only)

## Scope (docs only)
Update canonical v2 docs and create the ticket queue for Codex. No code changes.

## Tasks
1) Update `docs/v2/20_FEATURE_SPEC.md`
   - Check, if changes mentioned in this file are already respected. If not:
   - Add a new section: **Breakout Trend 1–5D (Immediate + Retest)**
   - Include (verbatim):
     - Features to be available in `FeatureEngine` outputs:
       - `features.volume_sma_periods.1d = 20`, `features.volume_sma_periods.4h = 20`
       - `1d.atr_pct_rank_120` (percent rank over 120 1D bars)
       - `4h.bb_width_pct` (BB period=20, std=2.0)
       - `4h.bb_width_rank_120` (percent rank over 120 4H bars)
     - Universe:
       - Market cap: 100M–10B
       - Liquidity gate: quote_volume_24h_usd >= 10M
       - Risk-off liquidity gate: quote_volume_24h_usd >= 15M
     - Breakout level:
       - `high_20d_1d = max(1D_high over bars [t1d-20 ... t1d-1])` (exclude current 1D candle)
     - Trigger:
       - `triggered = any(close_4h[i] > high_20d_1d for i in last 6 closed 4H candles)`
     - Retest:
       - window: 12×4H after first trigger candle
       - zone: ±1.0% around `high_20d_1d`
       - valid: low touches zone AND close >= level
       - invalidation: any close < level inside retest window
     - Gates:
       - Trend: ema20_1d > ema50_1d AND close_1d > ema20_1d
       - ATR gate: atr_pct_rank_120_1d <= 0.80
       - Momentum gate: r7_1d > 0.0
       - Overextension hard gate: dist_ema20_pct_1d < 28.0
     - Multipliers (applied at end):
       - Anti-chase (r7): start 30, full 60, min multiplier 0.75
       - Overextension: penalty start 12, strong 20, hard gate 28 (piecewise exact)
       - BTC regime:
         - Risk-On: (btc_close_1d > btc_ema50_1d) AND (btc_ema20_1d > btc_ema50_1d) -> multiplier 1.0
         - Risk-Off: allow only RS override + risk-off liquidity; multiplier 0.85
         - RS override: (alt_r7 - btc_r7) >= 7.5 OR (alt_r3 - btc_r3) >= 3.5
     - Scoring components (0..100) + weights:
       - Breakout distance (4H close vs 1D high_20d): weight 0.35
       - Volume score (combined spike 0.7/0.3): weight 0.35
       - Trend score (base 70 + 15 + 15): weight 0.15
       - BB score: weight 0.15
       - final_score = clamp(base_score * multipliers..., 0..100)
     - Setup IDs and required output fields.

2) Update `docs/v2/40_TEST_FIXTURES_VALIDATION.md`
   - Check, if changes mentioned in this file are already respected. If not:
   - Add a section with fixtures/validation for the new setup:
     - MORPHO snapshot 2026-02-21 (fill in exact values you already validated)
     - Negative: BTC Risk-Off + no RS override => excluded
     - Negative: overextension >= 28 => excluded
     - Deterministic unit-series tables for multipliers and BB/ATR thresholds


## Acceptance criteria
- Canonical docs updated: `20_FEATURE_SPEC.md`, `40_TEST_FIXTURES_VALIDATION.md`, `30_IMPLEMENTATION_TICKETS.md`.
- Ticket files exist in `docs/v2/tickets/`.
- No code changes in `scanner/`.
- CI passes.

## Close-out / Archive step (mandatory)
After merge of this ticket:
1) Move **this** ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md` so the next Codex session can continue without context loss.
