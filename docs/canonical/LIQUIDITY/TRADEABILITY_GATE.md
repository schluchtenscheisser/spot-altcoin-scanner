# Tradeability Gate — Classes, Reasons, Decision Eligibility (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_TRADEABILITY_GATE
status: canonical
tradeability_classes:
  - DIRECT_OK
  - TRANCHE_OK
  - MARGINAL
  - FAIL
  - UNKNOWN
unknown_reason_family:
  - tradeability_unknown
  - orderbook_data_missing
  - orderbook_data_stale
  - orderbook_not_in_budget
```

## Class semantics
- `DIRECT_OK`: Entry-size feasible under direct execution constraints.
- `TRANCHE_OK`: Entry feasible only via tranche execution constraints.
- `MARGINAL`: Fully evaluated but below Phase-1 entry execution quality threshold.
- `FAIL`: Fully evaluated and hard-failed tradeability checks.
- `UNKNOWN`: Not evaluable / not evaluated; no deterministic execution quality assessment available.

## Required invariants
- `MARGINAL` is **not ENTER-fähig**.
- `UNKNOWN` is **not WAIT-fähig**.
- `UNKNOWN` is **not FAIL**.
- `UNKNOWN` candidates stop before `DECISION_LAYER`.

## UNKNOWN reason-paths (distinct, non-collapsed)
- `tradeability_unknown`: generic fallback when unknown state is explicit but no narrower reason applies.
- `orderbook_data_missing`: required orderbook snapshot unavailable.
- `orderbook_data_stale`: snapshot exists but violates freshness threshold.
- `orderbook_not_in_budget`: skipped because symbol is outside configured orderbook budget (`orderbook_top_k`).

These reasons MUST remain distinguishable in outputs and diagnostics.

## Decision eligibility mapping
- Eligible for `ENTER`: `DIRECT_OK` or `TRANCHE_OK` only, plus other decision prerequisites.
- Eligible for `WAIT`: fully evaluated non-enter state only (`MARGINAL` or context-dependent holdback); never `UNKNOWN`.
- Forced `NO_TRADE`: `FAIL`.

## Determinism
- Tradeability class assignment order and tie-breaking must be deterministic.
- Null/missing fields must not be bool-coerced into a pass/fail class.
