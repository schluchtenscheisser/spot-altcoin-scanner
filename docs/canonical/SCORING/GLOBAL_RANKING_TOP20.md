# Global Ranking — Top-N, Dedup, Setup Weights (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_GLOBAL_RANKING_TOP20
status: canonical
global_top_n_default: 20
setup_weights_by_category:
  breakout_trend: 1.0
  pullback: 0.9
  reversal: 0.8
setup_id_to_weight_category:
  breakout_immediate_1_5d: breakout_trend
  breakout_retest_1_5d: breakout_trend
dedup:
  per_symbol_max_rows: 1
  prefer_setup_id_order:
    - breakout_retest_1_5d
    - breakout_immediate_1_5d
setup_preference:
  mapping:
    breakout_retest_1_5d: 1
    breakout_immediate_1_5d: 0
  default_for_unknown_setup_id: -1
composition:
  final_ordering_defined_by: docs/canonical/LIQUIDITY/RE_RANK_RULE.md
```

## 0) Purpose
Define how per-setup scores become a single **deduplicated** global list (Top-N input list).

Important:
- This document defines **selection + dedup**.
- Final ordering of the published list is defined by `LIQUIDITY/RE_RANK_RULE.md`.

## 1) Inputs
Scored setup rows, each with:
- `symbol`
- `setup_id`
- `final_score` (0..100)

## 2) Setup weight categories
Weights apply to per-setup `final_score`:

- `weighted_setup_score = final_score * weight(category(setup_id))`

Categories and default weights:
- breakout_trend: 1.0
- pullback: 0.9
- reversal: 0.8

Category mapping is explicit in Machine Header: `setup_id_to_weight_category`.

## 3) Global score definition
For a given symbol:
- `global_score(symbol) = max(weighted_setup_score over all valid setups for symbol)`
- `best_setup_id = argmax(weighted_setup_score)`

## 4) Dedup rule (one row per symbol)
1) For each symbol, select the row with the highest `weighted_setup_score`.
2) If multiple rows tie on `weighted_setup_score`, select the one whose `setup_id` appears earliest in `prefer_setup_id_order`.
3) If still tied, tie-break by `setup_id` lexicographically ascending.
4) If still tied, tie-break by `symbol` ascending.

## 5) Top-N truncation
After dedup (and before liquidity re-rank):
- Keep the first `global_top_n` rows by `global_score` descending.
- If fewer rows exist, output all.

Note:
- The final published ordering is applied afterwards by `LIQUIDITY/RE_RANK_RULE.md`.

## 6) Determinism requirements
- No randomness
- Stable tie-breakers always defined
