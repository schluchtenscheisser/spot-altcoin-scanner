# Decision Layer — ENTER / WAIT / NO_TRADE (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_DECISION_LAYER
status: canonical
decision_domain:
  - ENTER
  - WAIT
  - NO_TRADE
requires_fully_evaluated_for_wait: true
unknown_reaches_decision_layer: false
```

## Decision domain
`decision ∈ {ENTER, WAIT, NO_TRADE}` only.

## Score-role separation (authoritative)
- `setup_score`: decision-threshold score for ENTER/WAIT eligibility.
- `global_score`: prioritization/context score among already decision-eligible candidates.

`global_score` MUST NOT be used as primary truth to bypass hard blockers from tradeability/risk/setup readiness.

## Entry prerequisites (minimum)
A candidate can be `ENTER` only if all are true:
1. Tradeability is evaluable and entry-eligible (`DIRECT_OK` or `TRANCHE_OK`).
2. Setup is entry-ready (including reversal/reclaim requirements where applicable).
3. Risk is evaluable and acceptable (`risk_acceptable = true`).
4. `setup_score` meets configured ENTER threshold.

## WAIT semantics
- `WAIT` applies only to fully evaluated candidates.
- Typical WAIT causes: valid setup but below ENTER threshold, timing/confirmation pending, or `MARGINAL` execution quality.
- `UNKNOWN` can never become `WAIT`.

## NO_TRADE semantics
Use `NO_TRADE` for hard blockers/non-eligibility (e.g., `FAIL`, denied risk, invalid setup).

## Explicit exclusions
- Reversal without reclaim is not entry-ready.
- Phase 1 does not define hold/rotate/portfolio orchestration decisions.
