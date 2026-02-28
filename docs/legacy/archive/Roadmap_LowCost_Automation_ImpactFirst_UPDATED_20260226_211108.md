# Roadmap_LowCost_Automation_ImpactFirst (updated)

This document is a low/no-cost, automation-first roadmap. It assumes only **MEXC + CMC** and optional free additions (RSS/CoinGecko) behind feature flags.

## Phase 0 — Stop-the-bleeding (run stability + correctness)
Highest impact; do these first.

- Orderbook Top-K robustness: per-symbol error isolation; do not insert `None` orderbooks; budget-safe Top-K calls.
- Closed-candle gate consistency: treat missing `last_closed_idx` as insufficient history for **all** setup scorers.
- Schema discipline: bump output schema version when payload shape changes; maintain `docs/SCHEMA_CHANGES.md`.
- GPT snapshot integrity: ensure scoring rules remain present in GPT snapshot generation workflow.
- Test reliability: fixture paths independent of current working directory.

## Phase 1 — Measurement + objective alignment (no new data sources)
- Implement executable E2 evaluation module (canonical MODEL_E2) and snapshot → evaluation pipeline.
- Add ranking quality metrics:
  - Precision@K, score→return correlation, rank monotonicity diagnostics.
- Build score-bin calibration tables and expose calibrated probabilities in daily reports.

## Phase 2 — Trader-briefing outputs (no new data sources)
- Standardized trade plan fields (trigger/entry/invalidation/SL/TP, R:R) per setup.
- Explicit setup validity reasons + near-miss watchlist.

## Phase 3 — Beta/Alpha layer (MEXC-only, filter + multiplier in ranking)
- Compute rolling beta to BTC (optionally ETH) + alpha proxies (r3/r7 vs benchmark).
- Apply configurable:
  - Risk-off filters (require alpha positive, cap beta).
  - Multipliers producing `adjusted_global_score` with clamped range and deterministic tie-breaks.

## Phase 4 — Signal quality upgrades from existing data (no new sources)
- Robust statistics features (median/trimmed mean, percentile ranks, robust z-scores).
- Candle-structure and wick-robust logic (body/wicks/range/efficiency, false-breakout flags).
- Wick-robust breakout definitions (avoid one-wick spikes).
- Unify base logic across setups (single canonical base definition).
- Config-driven parameters audit (thresholds/weights from config.yml with legacy fallback + warning).
- Drift/health monitoring (missing candles, abnormal volumes, feature distribution checks; run manifest warnings).

## Phase 5 — Portfolio view & diversification (no new sources)
- Correlation/cluster awareness using returns (BTC/ETH beta + pairwise correlation).
- Diversified “portfolio_candidates” output separate from raw global_top list.
