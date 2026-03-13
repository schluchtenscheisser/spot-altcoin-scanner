# Global Ranking — Top-N, Dedup, Setup Weights (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_GLOBAL_RANKING_TOP20
status: canonical
global_top_n_default: 20
phase_policy:
  phase1_single_setup_type: true
  setup_weights_active: true
setup_weights_by_category:
  breakout: 1.0
  pullback: 0.9
  reversal: 0.8
setup_id_to_weight_category_active:
  breakout_immediate_1_5d: breakout
  breakout_retest_1_5d: breakout
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
top_n_selection_order_before_truncation:
  - key: global_score
    order: desc
  - key: setup_preference
    order: desc
  - key: symbol
    order: asc
composition:
  final_ordering_defined_by: docs/canonical/LIQUIDITY/RE_RANK_RULE.md
```

## 0) Purpose
Define how per-setup scores become a single **deduplicated** global list (Top-N input list).

Important:
- This document defines **selection + dedup + top-n inclusion**.
- Final ordering of the published list is defined by `LIQUIDITY/RE_RANK_RULE.md`.

## 1) Inputs
Scored setup rows, each with:
- `symbol`
- `setup_id`
- `final_score` (0..100)

## 2) Setup weights (Phase policy)
Phase 1 (current canonical):
- `setup_weights_active = true`
- Effective setup-type weights are active in global score computation.
- `setup_weights_by_category.breakout = 1.0`
- `setup_weights_by_category.pullback = 0.9`
- `setup_weights_by_category.reversal = 0.8`
- Missing weight key for resolved category/type defaults to `1.0`.
- Invalid configured weights (non-numeric, non-finite, `<= 0`) are invalid and must fail clearly.

## 3) Global score definition
For a given symbol:
- `weighted_score(row) = final_score(row) × setup_weight(row)`
- `global_score(symbol) = max(weighted_score over all valid setups for symbol)`
- `best_setup_id = argmax(weighted_score)`

## 4) Setup preference (deterministic)
- `setup_preference(setup_id)` is defined by the mapping in the Machine Header and is used only as a deterministic tie-breaker.

## 5) Dedup rule (one row per symbol)
1) For each symbol, select the row with the highest `weighted_score`.
2) If multiple rows tie on `weighted_score`, select the one whose `setup_id` appears earliest in `prefer_setup_id_order`.
3) If still tied, tie-break by `setup_id` lexicographically ascending.
4) If still tied, tie-break by `symbol` ascending.

## 6) Top-N selection (deterministic inclusion)
Before truncation, order rows using **exactly**:
1) `global_score` descending
2) `setup_preference` descending
3) `symbol` ascending

Then take the first `global_top_n` rows (default 20).

## 7) Final ordering
After top-n inclusion is determined, apply `LIQUIDITY/RE_RANK_RULE.md` to produce the final published ordering.
