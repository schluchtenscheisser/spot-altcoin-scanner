# Liquidity — Re-Rank Rule (Deterministic) (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_RE_RANK_RULE
status: canonical
sort_keys:
  - key: score
    order: desc
  - key: slippage_bps
    order: asc
    missing: "+inf"
  - key: proxy_liquidity_score
    order: desc
final_tie_breaker:
  - key: symbol
    order: asc
```

## 1) Ziel
Re-rank optimiert Tradeability, ohne die Score-Skala zu verändern.

## 2) Sorting keys (canonical)
Sortiere Kandidaten deterministisch nach:
1) `score` (setup_score oder global_score) **absteigend**
2) `slippage_bps` **aufsteigend**
   - wenn missing: behandle als `+inf` (schlechtester Fall)
3) `proxy_liquidity_score` **absteigend**
4) Tie-break: `symbol` **aufsteigend**

## 3) Determinismus
- Tie-breaker muss immer gesetzt sein, sodass Reihenfolge stabil ist.
- Keine random ordering.
