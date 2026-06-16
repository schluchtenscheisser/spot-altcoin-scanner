# Open Questions — Independence-Release Bootstrap (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OPEN_QUESTIONS
status: canonical
last_reviewed: 2026-05-15
review_context: "Post T30 v1.1 / ir1.5 data accumulation phase"
```

## Purpose

This file tracks authoritative open questions that remain unresolved in the current Independence-Release architecture and therefore must not be silently decided by later implementation tickets.

Compatibility note: this document tracks Open questions and includes historical references, including items resolved by Ticket 14, for traceability across older tests/tickets. Legacy reference anchors such as Gesamtkonzept §21 and Canonical OHLCV long-term storage are retained as compatibility snippets and do not change the active open-question semantics.

Resolved questions are kept in a reference section at the bottom so that older ticket references (`Q1`, `Q2`, etc.) remain traceable without leaving resolved items in the active decision surface.

## Bootstrap rule

Until an open question listed here is resolved in canonical documentation, a newer decision note, or an implemented ticket, later tickets and implementations must not silently invent business-logic answers for it.

Where an item is marked `partially resolved`, the implemented part is no longer open, but the remaining unresolved part must still be treated as an active decision surface.

---

## Active open questions

*Sorted by impact on investment-signal correctness. Original question numbers are preserved to avoid breaking references from prior tickets, decision notes, and reviews.*

---

### Q3) `distance_to_range_high_pct_abs` formula remains not fully canonical

**Status:** Partially resolved / remains open for v2

**Current implementation status**

`distance_to_range_high_pct_abs` is now numerically present in current diagnostics for most symbols since the `ir1.3` / T_EL2 workstream. It is used in T_EL2 v1 only as an auxiliary proximity-warning input, specifically via:

```text
entry_location.range_high_proximity_warning
```

It is not yet a fully calibrated primary Entry-Location input, and its canonical formula has not been finalized in the v2.1 specification.

**Current boundary**

T_EL2 v1 may use this field only as an auxiliary warning / context signal. It must not be treated as a fully calibrated primary input until a future calibration/spec pass defines:

1. the exact range-high anchor,
2. the lookback or structural range selection rule,
3. the precise formula,
4. ownership of the computation contract,
5. how this field differs from `dist_to_base_mid_pct` (Q13).

**Still to decide**

1. What exactly is the "Range High" — swing high over what lookback or structural range?
2. Which historical bars or anchors define the range?
3. Is a configurable lookback parameter involved?
4. Which module owns the computation contract?
5. How does this field differ from `dist_to_base_mid_pct` (Q13)? The distinction must remain explicit.

**Do not silently change**

Future tickets must not promote `distance_to_range_high_pct_abs` from auxiliary warning to primary calibrated Entry-Location input without resolving this question.

---

### Q4) Intraday diagnostics / no-op behavior and future promotion diagnostics

**Status:** Partially resolved

**Resolved part**

The no-op semantics for intraday runs have been implemented and are now expected behavior when no new actionable intraday cycle exists. Current diagnostics/reporting may explicitly surface:

```text
no_op
no_op_reason
```

An intraday run with `0` records is therefore no longer automatically a serialization defect when it represents an intentional no-op condition.

**Still open**

The remaining open part concerns productive Intraday Promotion expansion:

1. When genuine intraday promotions occur, should the intraday runner always emit full symbol diagnostics for the promoted / monitored population?
2. Which subset is diagnostic-mandatory: all monitoring-universe symbols, only promoted symbols, only bucket-changing symbols, or all symbols with refreshed 4h context?
3. How should intraday promotion diagnostics be evaluated against daily diagnostics and T30/T31 evaluation exports?
4. Which `no_op_reason` values are canonical for skip/no-op states versus true empty outputs?

**Current boundary**

`0` intraday records can be valid no-op behavior, but this must not be generalized to mean that productive intraday promotions may remain diagnostically invisible.

---

### Q5) `execution_size_class = "full"` has two distinct meanings

**Status:** Still open / deferred schema cleanup

**Context**

`execution_size_class = "full"` occurs in two separate scenarios:

1. `direct_ok` + full orderbook depth → full position possible, all execution metrics passed.
2. `marginal` + full orderbook depth, but at least one other execution-quality metric prevented `direct_ok`.

The distinction is preserved via `execution_status_raw`. The current documentation clarifies that both fields must be read together, so there is no known current misbehavior.

**Still to decide**

Does the current documentation suffice permanently, or should a future schema version introduce granular fields such as:

```text
execution_capacity_class = full / reduced_75 / reduced_50 / reduced_25
execution_quality_status = direct_ok / marginal / fail / unknown
```

**Current boundary**

No immediate fix is required. This is a schema-cleanup candidate only.

---

### Q6) `is_reduced_size_eligible` is semantically misleading — rename pending

**Status:** Still open / deferred schema cleanup

**Context**

`is_reduced_size_eligible = true` also applies to `direct_ok` records, which trade at full — not reduced — size. The field name implies "only eligible for reduced-size trading". The documented semantics are instead:

```text
tradeable at the policy-permitted position size, whether full or reduced
```

**Still to decide**

Should the field be renamed in a future schema cleanup?

Candidate names:

```text
is_execution_eligible
is_policy_tradeable
is_policy_size_eligible
```

**Current boundary**

A rename requires a schema version bump and explicit migration handling. Until then, consumers must use the documented semantics and must not interpret the field as "reduced-size only".

---

### Q7) Smoke-test vs. full-universe intraday behavior differs

**Status:** Still open / verify if still reproducible

**Context**

Smoke-test runs and full-universe runs previously showed different intraday behavior. This may be expected, but the root cause has not been verified in the current `ir1.5` phase.

**Still to decide**

Diagnose and document why the difference occurs. If intentional, document the exact cause. If a bug, fix.

**Current boundary**

Before opening a fix ticket, first verify whether this difference is still observable in current Shadow-Live runs.

---

### Q8) `candidate_excluded_symbol_count` in `candidate_segments`

**Status:** Verification pending

**Context**

T23 defined `candidate_excluded_symbol_count` as an explicit contract field in `candidate_segments`. Earlier Shadow-Live reports appeared to omit the key, returning `None` when analysis scripts read it.

**Current check required**

Verify against a current `ir1.5+` `report.json` whether:

```text
candidate_segments.candidate_excluded_symbol_count
```

is present and emitted as an integer.

**Resolution rule**

- If present and correct in current reports: mark Q8 as resolved.
- If absent: create a small targeted bugfix against the report/T23 module.
- If intentionally absent: update the report contract to remove or explicitly document the omission.

**Current boundary**

No business-logic decision is required. This is either resolved in implementation or a small report-contract bugfix candidate. Do not mark as resolved without checking a current report artifact.

---

### Q9) Non-ASCII symbol `币安人生USDT` passes the eligibility filter

**Status:** Still open

**Context**

A symbol containing Chinese characters appeared as a Confirmed Candidate in a Shadow-Live run, classified as `classic_crypto`. The eligibility filter does not reject non-Latin or non-ASCII symbol names.

**Still to decide**

1. Should the Eligibility or Universe Classification layer flag non-Latin/non-ASCII symbol names with lower confidence rather than hard-excluding them?
2. Alternatively: is the canonical path an explicit Override Map entry — include or exclude — for any non-ASCII symbol that surfaces in Shadow-Live runs?
3. If flagging: which confidence level and which reason code?
4. Should non-ASCII handling affect only diagnostics/classification or also operational eligibility?

**Current boundary**

Do not introduce a hard ASCII filter without evidence. A flag-first or explicit-override approach is more consistent with the diagnostic-before-config principle, but this still needs an explicit decision.

---

### Q10) `tokenized_stock_or_etf` shows systematically higher `unknown_execution` rate

**Status:** Still open / informational until reproduced

**Context**

Observed in T24 run: tokenized-stock-/ETF-like assets showed a higher `UNKNOWN_ORDERBOOK_STALE` rate than `classic_crypto` segments.

**Still to decide**

Is this a structural pattern, such as lower market-maker activity or less frequently updated orderbooks for tokenized assets? If so:

- Should tokenized assets receive different execution grading behavior?
- Should the `observe_only` threshold for stale orderbooks be tighter for this category?
- Or is the current handling correct and this is informational only?

**Current boundary**

No immediate config or execution-rule change without reproduced evidence across newer runs.

---

### Q11) ARBUSDT shows `execution_attempted = true` without a valid decision bucket

**Status:** Still open / verify if still reproducible

**Context**

Observed after the T20 Smoke-Test run: `ARBUSDT` had `execution_attempted = true` with no corresponding `decision_bucket` or `state_machine_state` in diagnostics. It was flagged as a pre-existing anomaly in the execution-adapter path.

**Still to decide**

Is this a defect in Execution Adapter logic, a diagnostics serialization gap, or an edge case specific to early Smoke-Test-phase behavior that is no longer reproducible?

**Current boundary**

Lowest priority. Verify first whether this is still observable in current Shadow-Live runs before investing in a fix.

---

### Q13) `dist_to_base_mid_pct` remains unresolved

**Status:** Still open

**Context**

`dist_to_base_mid_pct` was identified during the Ticket-5 / Ticket-5.1 / Ticket-6 workstream as a required input for `expansion_progress_structural`, but no authoritative formula was found in the governing specifications.

The field name and descriptive intent exist, but the architecture still lacks a canonical definition for:

- what exactly the "base mid" is,
- which historical range/base it refers to,
- how that base is selected,
- and the exact formula for converting it into `dist_to_base_mid_pct`.

**Why this matters**

Without an authoritative formula, independent implementations may invent incompatible meanings for the same field, causing divergence in Tier-1 axis computation, diagnostics, runner/state interpretation, and backtest comparability.

**Current consequence**

`expansion_progress_structural` treats this sub-input as absent. The related subscore remains unavailable; the axis continues to rely on canonical weight-dropout / re-normalization.

**Still to decide**

1. The authoritative base-selection rule.
2. The exact mathematical formula.
3. Whether any lookback/config parameter is involved.
4. Which module owns the computation contract.
5. How it differs from `distance_to_range_high_pct_abs` (Q3).

---

### Q14) DOC-E2 data/report evidence items that remain not yet fully validated

**Status:** Still open / DOC-E2 follow-up

The following DOC-E1 items are relevant to data/report interpretation but must not be documented as current-state facts until additional evidence or a follow-up decision validates them:

- DOC-E2 follow-up: `execution_grade` remains not yet fully validated as an active serialized output field. DOC-E1 status: `needs_review`. Resolution needed before documenting it as a current-state data/report contract.
- DOC-E2 follow-up: `execution_notional_usdt` remains not yet fully validated as an active serialized output field. DOC-E1 status: `needs_review`. Resolution needed before documenting it as a current-state data/report contract.
- DOC-E2 follow-up: `entry_location_score` remains not yet fully validated as an active Entry-Location output field. DOC-E1 status: `needs_review`. Resolution needed before documenting it as a current-state data/report contract.
- DOC-E2 follow-up: `not_applicable` remains not yet fully validated as an active diagnostics/report field value. DOC-E1 status: `needs_review`. Resolution needed before documenting it as a current-state data/report contract.
- DOC-G follow-up: `basket` is not confirmed as an active `scanner/evaluation/*` or Daily/Intraday report/diagnostics output field. Current evidence places basket hypotheses in offline T30-v2 segment-selection tooling and artifacts such as `basket_summary.json`; this remains non-canonical evidence tooling unless a future ticket promotes a specific basket output contract.

**Current boundary**

DOC-E2 documents implemented alternatives or boundaries where evidence is confirmed or partial with qualification. It does not promote any item above into a current artifact contract.

---

## Resolved questions (for reference)

### Q1) `is_tradeable_candidate` vs. `candidate_excluded` / universe exclusion

**Status:** Resolved

**Resolution**

Resolved by the Q1/Q2 operational-tradeability decision and implementation.

The chosen path keeps:

```text
is_tradeable_candidate
```

as the execution-/bucket-scoped field and introduces:

```text
is_operational_trade_candidate
```

as the final operational field that combines:

```text
is_tradeable_candidate == true
AND candidate_excluded != true
```

**Current contract**

- `candidate_excluded` is a top-level diagnostics field.
- Do not read `universe.candidate_excluded` for current diagnostics.
- `universe_category` remains nested under `universe.universe_category`.
- Current schema after this resolution: `ir1.5`.

---

### Q2) Stablecoin / cash-proxy exclusion is incomplete

**Status:** Resolved

**Resolution**

Resolved by the Q1/Q2 implementation.

Stablecoin-/cash-proxy cases are excluded in the Universe-/Decision path and no longer rely only on downstream report-summary filtering.

**Current contract**

- Stablecoin-/cash-proxy candidates must be excluded before final operational tradeability is reported.
- Operational consumers should rely on `is_operational_trade_candidate`, not on ad-hoc filters.
- `candidate_excluded` remains the top-level exclusion marker.

---

### Q12) Evaluation Replay does not accumulate across runs

**Status:** Resolved

**Resolution**

Resolved by the T18/T30 Replay-/Event-Evaluation architecture.

T30 v1/v1.1 now provides the exploratory forward-return evaluation path using persisted/replayed report artifacts and event exports. The first T30 v1.1 run has technically validated:

- replay execution,
- OHLCV fetch,
- early-/confirmed-reference-price fallback,
- segment fields in the export.

**Current boundary**

The architectural accumulation question is resolved, but T30 analytical conclusions remain deferred until a larger `ir1.5+` run base exists. This is no longer an open architecture question; it is a data-accumulation/calibration constraint.

---

### R2) Long-term OHLCV history storage path beyond Ticket 4 transitional SQLite persistence

**Status:** Resolved by Ticket 14.

Canonical path:

```text
snapshots/history/ohlcv/timeframe=<tf>/symbol=<symbol>/year=<yyyy>/month=<mm>/
```

---

### R3) `daily_bar_id` type consistency across Independence-Release layers

**Status:** Resolved by Ticket 15.

Canonical cross-layer type:

```text
str in YYYY-MM-DD format
```

---

### R4) §21/3 Execution frequency + Top-N policy (Daily vs Intraday)

**Status:** Resolved by Tickets 16 and 17.

No fachlicher Top-N cap; optional limits are technical safeguards only.
