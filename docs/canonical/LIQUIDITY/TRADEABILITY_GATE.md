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

## Classification criteria (Phase 1 V4.2.1)
- Inputs (runtime-configurable with canonical defaults):
  - `notional_total_usdt` (default `20_000`)
  - `notional_chunk_usdt` (default `5_000`)
  - `max_tranches` (default `4`)
  - `max_spread_pct` (default `0.15`)
  - `min_depth_1pct_usd` (default `200_000`)
  - class thresholds: `direct_ok_max_slippage_bps=50`, `tranche_ok_max_slippage_bps=100`, `marginal_max_slippage_bps=150`
- `DIRECT_OK` iff all hold: spread gate pass, depth gate pass, and `slippage_bps_20k <= direct_ok_max_slippage_bps`.
- `TRANCHE_OK` iff not `DIRECT_OK` and all hold: spread/depth gates pass, `slippage_bps_5k <= tranche_ok_max_slippage_bps`, and `notional_chunk_usdt * max_tranches >= notional_total_usdt`.
- `MARGINAL` iff fully evaluated and neither `DIRECT_OK` nor `TRANCHE_OK`, but still within marginal execution quality envelope.
- `FAIL` iff fully evaluated and hard-fails tradeability quality envelope.
- `UNKNOWN` iff required orderbook evidence is absent/not usable (`missing`, `stale`, or `not_in_budget`).

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

## T29 Diagnostics Field Semantics
T29 introduced five new top-level fields in `symbol_diagnostics.jsonl.gz`.
This section documents their intended meaning to prevent misinterpretation.

### Field overview
| Field | Type | Meaning |
| --- | --- | --- |
| `execution_size_class` | string enum | Depth-derived position size classification |
| `recommended_position_factor` | float or null | Operative position size factor (0.00–1.00) |
| `execution_grade_effective` | float or null | Final execution grade used by decision/ranking |
| `is_reduced_size_eligible` | bool | Tradeable at any policy-allowed position size |
| `is_tradeable_candidate` | bool | In a top bucket and tradeable |

### `execution_size_class` is a depth classification, not a final tradeability verdict
`execution_size_class` reflects only the orderbook depth dimension:

```text
full           depth >= 100% of threshold; full position supportable by depth alone
reduced_75     depth >= 75% of threshold
reduced_50     depth >= 50% of threshold
reduced_25     depth >= 25% of threshold
observe_only   depth < 25% of threshold; not tradeable at minimum size
blocked        execution_status_raw = fail; hard no-trade
not_evaluable  execution attempted but orderbook evidence insufficient
not_evaluated  execution not attempted for this symbol
```

`execution_size_class` does not replace `execution_status_raw`. Both fields must be read together:

- `execution_status_raw` is the canonical execution outcome (`direct_ok`, `tranche_ok`, `marginal`, `fail`, `unknown`).
- `execution_size_class` is the depth-derived position size classification.

Critical: `execution_size_class = "full"` does not imply `execution_status_raw = "direct_ok"`.
A marginal record with sufficient depth can also receive `execution_size_class = "full"`.

| `execution_status_raw` | `execution_size_class` | Meaning |
| --- | --- | --- |
| `direct_ok` | `full` | All execution metrics passed; full position |
| `marginal` | `full` | Depth sufficient; another metric kept execution below `direct_ok` |
| `marginal` | `reduced_25` | Depth at 25–50% of threshold; reduced position |

Always read both fields when making tradeability decisions.

### `is_reduced_size_eligible` covers full and reduced positions
Despite its name, `is_reduced_size_eligible` is true for `direct_ok` records as well as for reduced-size marginal records.

Its intended meaning is:

```text
is_reduced_size_eligible = true
iff execution_size_class in {full, reduced_75, reduced_50, reduced_25}
and execution_status_raw in {direct_ok, tranche_ok, marginal}
and spread/slippage gates pass if evaluated
```

The field answers:

```text
Is this symbol tradeable at the policy-permitted position size, whether full or reduced?
```

It does not mean:

```text
Only suitable for a reduced position.
```

A future rename to `is_execution_eligible` or `is_policy_tradeable` would be more precise, but no rename is implemented in T29.

### `execution_grade_effective` is the ranking input
`execution_grade_effective` is the grade injected into the T12 priority-score formula. It reflects the T29 size-class mapping:

```text
direct_ok                    -> 100.0
tranche_ok                   -> 75.0
marginal + full              -> 75.0
marginal + reduced_75        -> 75.0
marginal + reduced_50        -> 60.0
marginal + reduced_25        -> 40.0
marginal + below_min         -> 0.0
fail                         -> 0.0
unknown / not_evaluable      -> null
```

Do not use `execution_grade_t16` for ranking. That field is a raw T16 audit field and is currently null because T16 does not emit a fine-grained grade.

`execution_grade_effective` is the authoritative execution-grade input for T12 ranking/decision.

### `not_evaluable` vs. `not_evaluated`
These two `execution_size_class` values are semantically distinct and must not be collapsed:

```text
not_evaluated   execution was not attempted (`execution_attempted = false`)
not_evaluable   execution was attempted but required metrics are missing, stale, or invalid
```
