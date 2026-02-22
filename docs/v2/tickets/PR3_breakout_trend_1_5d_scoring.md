# PR3 — Breakout Trend 1–5D: Scoring (Immediate + Retest) + Global Top20 Dedup

## Scope
Implement the new scoring module `breakout_trend_1_5d` with two setup IDs:
- `breakout_immediate_1_5d`
- `breakout_retest_1_5d`

Also implement Global Top20 dedup by symbol (tie -> retest).

## Files to change
- `config/config.yml`
- `scanner/pipeline/scoring/breakout_trend_1_5d.py` (new)
- `scanner/pipeline/__init__.py`
- `scanner/pipeline/global_ranking.py`
- `tests/`

## Config (exact)
Add `scoring.breakout_trend_1_5d` config block exactly as documented in `docs/v2/20_FEATURE_SPEC.md`.
Update market cap universe:
- min 100M
- max 10B

## Exact scoring & gating rules (must match docs)
Implement exactly as documented in `docs/v2/20_FEATURE_SPEC.md` for Breakout Trend 1–5D, including:
- breakout level high_20d_1d (exclude current 1D candle)
- 4H trigger freshness window: 6 bars
- retest window: 12 bars, zone ±1.0%, invalidation on 4H close < level
- gates: liquidity, trend, ATR rank, overextension hard gate, momentum gate
- BTC risk-off override rules:
  - risk-off liquidity >= 15M
  - RS override: (alt_r7 - btc_r7) >= 7.5 OR (alt_r3 - btc_r3) >= 3.5
  - btc_multiplier = 0.85 if override true, else excluded
- multipliers applied at the end: overextension, anti-chase, btc_multiplier
- components and weights:
  - breakout distance weight 0.35
  - volume score (spike_combined=0.7*spike_1d+0.3*spike_4h) weight 0.35
  - trend score weight 0.15
  - BB score weight 0.15
- output fields per row: setup_id, base_score, final_score, multipliers, components, key inputs

## Global Top20 dedup rule (exact)
- Dedup by symbol: keep the row with higher `final_score`.
- If tie: prefer retest setup.
- Then take top 20.

## Tests (tests-first)
- high_20d exclusion correctness
- trigger detection within last 6 closed 4H candles
- anti-chase multiplier at r7=30/45/60
- overextension multiplier at dist=12/20/27.9
- global top20 dedup tie-break prefers retest

## Acceptance criteria
- Both setup lists are produced deterministically.
- Global Top20 dedup works as specified.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge of this ticket:
1) Move **this** ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md` so the next Codex session can continue without context loss.
