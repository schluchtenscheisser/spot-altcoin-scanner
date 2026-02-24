# Liquidity — Re-Rank Rule (Deterministic) (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_RE_RANK_RULE
status: canonical
composition:
  replaces_global_sort: true
  note: "Global ranking performs dedup + selects one row per symbol; liquidity re-rank then defines the final ordering."
proxy_liquidity_score_definition:
  output_field: proxy_liquidity_score
  range: [0.0, 1.0]
  meaning: "cross-sectional percent-rank of quote_volume_24h_usd across the eligible universe after hard gates"
  source_field: quote_volume_24h_usd
  formula: "(count_less + 0.5*count_equal) / N"
  tie_handling: average_rank
  equality: ieee754_exact
  nan_policy:
    if_source_missing: 0.0
sort_keys:
  - key: score
    order: desc
  - key: slippage_bps
    order: asc
    missing: "+inf"
  - key: proxy_liquidity_score
    order: desc
    missing: 0.0
final_tie_breaker:
  - key: symbol
    order: asc
```

## 1) Ziel
Liquidity re-rank optimiert Tradeability, ohne die Score-Skala zu verändern.

## 2) Composition with global ranking (canonical)
1) `GLOBAL_RANKING_TOP20.md` selects at most one row per symbol (dedup) and produces a global list.
2) This document defines the **final ordering** of that list.
   - I.e., this re-rank replaces the global list’s previous sort order.

Because dedup already resolves setup ties, `setup_preference` does not need to appear in the re-rank chain.

## 3) Proxy liquidity score (canonical)
Canonical proxy field used for re-rank is `proxy_liquidity_score` (range 0..1), defined as:

- Cross-sectional percent-rank of `quote_volume_24h_usd` over the eligible universe after hard gates.
- Tie handling: average-rank.
- Equality: exact IEEE-754 float equality (no rounding).
- If `quote_volume_24h_usd` is missing/NaN: `proxy_liquidity_score = 0.0`.

## 4) Sorting keys (canonical)
Sort candidates deterministically by:
1) `score` (setup_score or global_score) descending
2) `slippage_bps` ascending (missing treated as +inf)
3) `proxy_liquidity_score` descending (missing treated as 0.0)
4) `symbol` ascending (final tie-break)

## 5) Determinismus
- Tie-breaker is always set.
- No random ordering.
