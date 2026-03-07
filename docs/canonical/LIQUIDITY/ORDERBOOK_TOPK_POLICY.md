# Liquidity — Orderbook Top-K Policy & Budget (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_ORDERBOOK_TOPK_POLICY
status: canonical
top_k_default: 200
fetch_policy:
  pre_rank_by: "proxy_liquidity_score"
  fetch_only_topk: true
determinism:
  stable_symbol_order: true
  tie_breaker_for_fetch: "symbol_asc"
symbol_definition: "full exchange trading pair string (e.g., ETHUSDT)"
missing_orderbook: "outside_topk_budget_is_unknown_stop_path"
```

## 1) Ziel
Orderbook-Fetch ist teuer. Canonical Policy:
1) Proxy-Liquidity vorberechnen (deterministisch)
2) Nur für Top-Kandidaten Orderbooks laden
3) Slippage/Grade berechnen
4) Kandidaten re-ranken (`RE_RANK_RULE.md`)

## 2) Top-K Definition
- Es werden nur die **Top-K** Levels je Seite (bids/asks) berücksichtigt.
- Default: `K = 200`.

## 3) Pre-Rank (Proxy)
- Pre-rank uses `proxy_liquidity_score` (0..100) computed from cross-sectional percent-rank of `quote_volume_24h_usd`.
- This stage must not change the percent-rank population definition.

## 4) Fetch Policy (deterministic)
- Fetch orderbooks for candidates in descending proxy rank order.
- Ties are broken by `symbol` ascending, where `symbol` is the full exchange pair string (e.g., `ETHUSDT`).

## 5) Fetch payload semantics & failure isolation
- Per-symbol orderbook fetch failures MUST NOT fail the whole run (failure isolation).
- The returned orderbook map contains only symbols with a successfully fetched and **validated** payload.
- Validation for map inclusion is strict: payload is `dict`, includes `bids` and `asks`, and both are non-empty lists.
- Non-`dict` payloads or dict payloads with missing/empty `bids`/`asks` MUST be ignored at fetch stage and logged as malformed payload.
- Downstream semantics are split deterministically:
  - Fetched + validated payload: liquidity metrics and `liquidity_grade` are computed.
  - Fetched but invalid/malformed payload, stale snapshot, or fetch exception: evaluated failure-path with explicit UNKNOWN reasons from `TRADEABILITY_GATE.md` (`orderbook_data_missing` / `orderbook_data_stale` as applicable).
  - Not fetched (outside Top-K budget): explicit not-evaluated path with reason `orderbook_not_in_budget`; class remains `UNKNOWN` and candidate stops before Decision Layer.
- Only fetched symbols may receive a liquidity grade.
- `orderbook_not_in_budget` is not a rerank shortcut and not a FAIL-class mapping.
- Re-rank semantics in `RE_RANK_RULE.md` apply only to symbols that were fetched/evaluated for execution quality; budget-skipped symbols stay on the UNKNOWN stop-path.


## 6) Execution metrics from orderbook snapshot
- Derived metrics per symbol (deterministic):
  - `spread_pct = (best_ask - best_bid)/mid * 100`, `mid=(best_bid+best_ask)/2`
  - `depth_bid_0_5pct_usd`, `depth_ask_0_5pct_usd`
  - `depth_bid_1pct_usd`, `depth_ask_1pct_usd`
  - `orderbook_ok` (bool)
- Depth bands are computed around mid:
  - bid cutoff `mid * (1 - band/100)`
  - ask cutoff `mid * (1 + band/100)`
- Missing/empty/invalid books produce null metrics and `orderbook_ok=false`.
