# Global Ranking — Top-N, Dedup, Setup Weights (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_GLOBAL_RANKING_TOP20
status: canonical
global_top_n_default: 20
dedup:
  per_symbol_max_rows: 1
  tie_break_prefer_setup_id:
    - breakout_retest_1_5d
    - breakout_immediate_1_5d
sorting:
  - key: global_score
    order: desc
  - key: setup_preference
    order: desc
  - key: symbol
    order: asc
global_score_definition:
  method: "max_over_setups"
  setup_weights:
    breakout_trend: 1.0
    pullback: 0.9
    reversal: 0.8
```

## 0) Purpose
This document defines how individual setup scores become a single global ranked list (Top-N), without duplication and with deterministic tie-break rules.

## 1) Inputs
A set of scored setup rows, each containing at minimum:
- `symbol`
- `setup_id`
- `final_score` (0..100)
- any required diagnostics fields
- optional liquidity fields (used later for re-rank)

## 2) Setup weights (canonical defaults)
Setup weights apply to the per-setup `final_score` to produce a comparable global score.

Default weights (configurable, but canonical defaults):
- Breakout: 1.0
- Pullback: 0.9
- Reversal: 0.8

> Note: If only Breakout Trend 1–5d is currently active, then only weight 1.0 applies. Other weights remain reserved for future/legacy setups.

## 3) Global score definition
For a given symbol, compute:

- `weighted_setup_score = final_score * setup_weight(setup_id)`
- `global_score(symbol) = max(weighted_setup_score over all valid setups for symbol)`

Also store:
- `best_setup_id = argmax(weighted_setup_score)`
- `confluence = count(valid setups for symbol)` (optional diagnostic)

## 4) Dedup rule (one row per symbol)
A symbol must appear at most once in the global list.

Canonical dedup:
1) For each symbol, select the row with the highest `weighted_setup_score`.
2) If multiple rows tie on `weighted_setup_score` (rare but possible), apply setup preference tie-break:
   - Prefer `breakout_retest_1_5d` over `breakout_immediate_1_5d`
   - If still tied, prefer lexicographically smallest `setup_id` (stable)
3) If still tied, final tie-break is `symbol` ascending.

## 5) Sorting the global list
After dedup:
- Sort by `global_score` descending
- Then by setup preference (retest > immediate, etc.)
- Then by `symbol` ascending

## 6) Top-N truncation
- Keep only the first `global_top_n` rows (default 20).
- If fewer rows exist, output all.

## 7) Interaction with liquidity re-rank
Liquidity re-rank may reorder the top candidates (see `docs/canonical/LIQUIDITY/RE_RANK_RULE.md`) but must be consistent with deterministic keys.

Canonical ordering pipeline:
1) Compute global list (this doc)
2) Apply liquidity re-rank (slippage asc, proxy desc, etc.)
3) Render outputs (JSON/MD/Excel)

## 8) Determinism requirements
- No randomness
- Stable tie-breakers always defined
- Identical inputs + config => identical ranked list
