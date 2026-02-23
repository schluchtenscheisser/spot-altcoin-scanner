# Liquidity — Orderbook Top-K Policy & Budget (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_ORDERBOOK_TOPK_POLICY
status: canonical
top_k_default: 200
fetch_policy:
  pre_rank_by: "proxy_liquidity"
  fetch_only_topk: true
proxy:
  primary_field: quote_volume_24h
determinism:
  stable_symbol_order: true
  missing_orderbook: "treated_as_worst_for_rerank"
```

## 1) Ziel
Orderbook-Fetch ist teuer. Canonical Policy:
1) Proxy-Liquidity berechnen (cheap)
2) Nur für Top-Kandidaten Orderbook bis Top-K Levels fetchen
3) Slippage/Grade berechnen
4) Kandidaten re-ranken (ohne Score-Skala zu verändern)

## 2) Top-K Definition
- Es werden nur die **Top-K** Levels je Seite (bids/asks) berücksichtigt.
- Default: `K = 200`.

## 3) Pre-Rank (Proxy)
- Proxy basiert auf `quote_volume_24h` (MEXC Ticker), monotone Ranking-Funktion.
- Zweck: deterministische Auswahl der Kandidaten, für die Orderbooks geladen werden.

## 4) Fetch Policy
- Es werden ausschließlich Orderbooks für die per Proxy vorselektierten Kandidaten geladen.
- Der Fetch muss deterministisch sein:
  - gleiche Inputs => gleiche Reihenfolge der Fetches
  - keine “random sampling”
  - bei Ties: stabile Tie-breaker (z.B. Symbol-Name asc)

## 5) Fehler-/Outage-Verhalten
Canonical (konzeptuell):
- Wenn Orderbook nicht verfügbar ist:
  - markiere Slippage als missing
  - behandle beim Re-rank so, dass missing Slippage “schlechter” ist (siehe `RE_RANK_RULE.md`)
- Keine stillen Teilresultate, wenn die Run-Policy ausdrücklich “fail hard” vorsieht (dies ist abhängig von Workflow; canonical Re-Rank Regel muss trotzdem definiert bleiben)

## 6) Outputs (für Schema)
- `spread_bps` / `slippage_bps`
- `liquidity_grade` (A/B/C/D)
- `liquidity_insufficient_depth` (bool)
