# Canonical Consistency Checklist (for AI review)

## Machine Header (YAML)
```yaml
id: CANON_CONSISTENCY_CHECKLIST
status: canonical_helper
goal: "detect contradictions, missing defaults, and ambiguous rules in canonical docs"
```

## How to use
Run this checklist after any documentation or logic change. The output should be a list of issues with exact file paths and headings.

---

## A) Canonical root integrity
- [ ] `docs/canonical/INDEX.md` links resolve (no missing files).
- [ ] `docs/AGENTS.md` precedence points to `docs/canonical/` (not `docs/v2/`).
- [ ] Auto-docs are untouched: `docs/code_map.md`, `docs/GPT_SNAPSHOT.md`.

## B) Single-source defaults (no contradictions)
Verify each default appears **exactly once** as canonical, and all other docs reference it consistently:

- [ ] Market cap default range (USD): value is consistent across:
  - `SCOPE.md`
  - `CONFIGURATION.md`
  - `SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- [ ] Liquidity thresholds:
  - normal quote volume 24h min
  - BTC risk-off quote volume 24h min
- [ ] Orderbook parameters:
  - top_k_default
  - slippage_notional_usd_default
- [ ] percent_rank:
  - population definition
  - tie-handling formula
  - output range [0..100] for cross-sectional `percent_rank` (and explicit rank01 naming for rolling time-series ranks)
- [ ] Score range: all scores in [0..100] with clamping rules.
- [ ] Discovery:
  - max_age_days
  - primary vs fallback source behavior

## C) Closed-candle / no-lookahead
- [ ] All feature docs explicitly state closed-candle-only.
- [ ] Setup scorer docs exclude current 1D bar from structure levels where required (e.g., `high_20d_1d` excludes current 1D).
- [ ] Backtest docs respect no-lookahead: triggers use only info available at trigger.

## D) Piecewise curves & boundaries
Confirm strictness and boundary values match fixtures:

- [ ] Overextension hard gate uses strict inequality (e.g., `< 28.0`).
- [ ] ATR chaos gate uses `<= 0.80` boundary.
- [ ] BB score boundaries (0.20, 0.60) match `VERIFICATION_FOR_AI.md`.
- [ ] Anti-chase multiplier table matches `VERIFICATION_FOR_AI.md`.

## E) Output schema completeness
- [ ] Required row fields for Breakout Trend 1–5d listed in `SCORE_BREAKOUT_TREND_1_5D.md` are reflected (or referenced) in `OUTPUT_SCHEMA.md`.
- [ ] Trade levels section:
  - If emitted, formulas and determinism rules are explicit (no guessing).
  - If not emitted, schema documents absence clearly.

## F) Mapping determinism
- [ ] `MAPPING.md` forbids fuzzy matching (unless explicitly added).
- [ ] Collision behavior is explicit and “not silently resolved”.
- [ ] Overrides are version-controlled and recorded.

## G) Liquidity re-rank determinism
- [ ] `RE_RANK_RULE.md` defines missing slippage behavior (treated as worst).
- [ ] Tie-breaker includes symbol sorting for stable ordering.

## H) Review outputs
- [ ] `VERIFICATION_FOR_AI.md` contains:
  - golden fixture inputs
  - expected outputs/tables for key functions
  - negative fixtures for boundary cases

## Result format (recommended)
For each issue found, output:
- file path
- heading / section
- problem description
- proposed exact fix (doc-only, no code changes)
