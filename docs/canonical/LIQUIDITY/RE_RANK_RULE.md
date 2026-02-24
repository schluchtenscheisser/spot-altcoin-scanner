# Liquidity — Re-Rank Rule (Deterministic) (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_RE_RANK_RULE
status: canonical
proxy_liquidity_score_definition:
  output_field: quote_volume_24h_usd
  meaning: "raw 24h quote volume in USD (or USDT treated as USD)"
  nan_policy: "missing treated as -inf for proxy sort"
sort_keys:
  - key: score
    order: desc
  - key: slippage_bps
    order: asc
    missing: "+inf"
  - key: quote_volume_24h_usd
    order: desc
    missing: "-inf"
final_tie_breaker:
  - key: symbol
    order: asc
```

## 1) Ziel
Re-rank optimiert Tradeability, ohne die Score-Skala zu verändern.

## 2) Proxy liquidity value (canonical)
`quote_volume_24h_usd` is the canonical proxy used for the third sort key.

- It is the **raw 24h quote volume** in USD (or USDT treated as USD).
- No normalization is applied in re-rank (raw value is used).
- Missing values are treated as `-inf` for the proxy sort (worst).

## 3) Sorting keys (canonical)
Sortiere Kandidaten deterministisch nach:
1) `score` (setup_score oder global_score) **absteigend**
2) `slippage_bps` **aufsteigend**
   - wenn missing: behandle als `+inf` (schlechtester Fall)
3) `quote_volume_24h_usd` **absteigend**
   - wenn missing: behandle als `-inf` (schlechtester Fall)
4) Tie-break: `symbol` **aufsteigend**

## 4) Determinismus
- Tie-breaker ist immer gesetzt, sodass Reihenfolge stabil ist.
- Keine random ordering.
