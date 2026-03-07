# Budget and Pool Model — Early Broad Pool, Controlled Cost (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_BUDGET_POOL
status: canonical
phase: 1
controls:
  - pre_shortlist_market_cap_floor_usd
  - shortlist_size
  - orderbook_top_k
```

## Purpose
Keep early candidate discovery broad while controlling expensive downstream calls deterministically.

## Hard guardrail vs soft prior
- `pre_shortlist_market_cap_floor_usd` is a **hard pool guardrail**.
- It is **not** a soft prior and must not be treated as ranking preference.

## Budget controls
- `shortlist_size`: cap for symbols that proceed from cheap screening to expensive evaluation stages.
- `orderbook_top_k`: cap for symbols receiving orderbook fetch/execution-quality evaluation.

`orderbook_not_in_budget` is an explicit UNKNOWN-path reason in tradeability, not a FAIL.

## Operational rationale
Phase 1 intentionally relaxes some early filters to avoid missing opportunities, then applies deterministic budgeted narrowing:
1. broad pool after hard guardrails,
2. shortlist for expensive OHLCV/feature workload,
3. orderbook top-k for deepest liquidity checks.

This preserves opportunity coverage while bounding runtime and API cost.
