# T29: Implement Marginal Reduced-Size Execution Policy

## Metadata

- Ticket ID: T29
- Title: Implement Marginal Reduced-Size Execution Policy
- Status: Draft
- Priority: P0
- Scope type: Runtime policy implementation / diagnostics and report contract extension
- Depends on: T27, T28
- Language: Implementation and code artifacts in English

---

## Authoritative reference set

Primary authority remains:

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`, only insofar as it does not contradict the primary authority.
4. Existing implemented contracts from T12, T16, T21, T21.1, T22, T23, T24, T25, T26, T27, and T28.
5. `docs/canonical/TRADEABILITY_GATE.md` for the current tradeability-gate parameter relationship.
6. The T28 analysis outputs, especially:
   - `recommended_policy.md`
   - `scenario_20k_vs_10k_summary.md`
   - `fail_sanity_check.md`
   - `marginal_band_distribution.md`
   - `spread_slippage_by_band.md`
   - `grade_mapping_sensitivity.md`
   - `recurring_symbols.md`
   - `candidate_availability_by_day.md`
7. The master preflight checklist for Codex-ready tickets.

This ticket may not override the v2.1 section files or the consolidated Gesamtkonzept. If repo reality differs from the target behavior below, Codex must preserve existing contracts where explicitly required and implement the T29 changes only within this ticket's scope.

---

## Purpose and motivation

T27 added execution-depth diagnostics to `symbol_diagnostics.jsonl.gz`, including:

- `available_depth_1pct_usdt`
- `depth_threshold_1pct_usdt`
- `available_depth_ratio`
- `depth_ratio_band`
- `recommended_position_factor_preview`
- `spread_pct`
- `estimated_slippage_bps`
- `depth_side_used`

T28 analyzed five T27-capable Shadow-Live daily runs from 2026-05-03 to 2026-05-07 and produced a reduced-size policy recommendation.

T28 confirmed:

- `fail` records remain far below even the 10k `reduced_25` scenario and remain hard no-trade.
- The relevant policy opportunity is within `marginal` records in top buckets.
- `marginal + below_min` should remain visible but not tradeable.
- `marginal + reduced_25/reduced_50/reduced_75/full` should become reduced-size eligible, subject to unchanged spread/slippage gates.
- The target position size should be reduced from 20k USDT to 10k USDT while preserving the 10x 1%-depth buffer.
- `execution_grade_t16` must remain a raw T16 audit field and must not be repurposed as the final decision/ranking grade.
- A new effective execution-grade field is needed in diagnostics so later analyses do not need to reconstruct the T12/default mapping.

T29 implements the selected policy.

---

## Non-goals

T29 must not implement unrelated execution changes.

Out of scope:

- No `fail -> marginal` promotion.
- No reduced-size eligibility for `fail`.
- No order splitting changes.
- No `tranche_ok` redesign.
- No live order placement.
- No forward-return / profitability analysis.
- No new market-cap, listing-age, stablecoin, or universe filters.
- No changes to phase, state-machine, or entry-pattern logic.
- No schema migration to nested execution objects.
- No removal or repurposing of `execution_grade_t16`.
- No loosening of spread or slippage thresholds.

T29 changes execution policy, diagnostics, report output, and ranking-grade mapping only where explicitly specified below.

---

## High-level target behavior

T29 introduces a size-aware execution classification on top of the existing execution status.

Existing execution status remains canonical:

```text
execution_status_raw ∈ {direct_ok, tranche_ok, marginal, fail, unknown, null}
```

New fields distinguish operational size eligibility:

```text
execution_size_class ∈ {
  full,
  reduced_75,
  reduced_50,
  reduced_25,
  observe_only,
  blocked,
  not_evaluable,
  not_evaluated
}
```

```text
recommended_position_factor ∈ {1.00, 0.75, 0.50, 0.25, 0.00, null}
```

```text
execution_grade_effective ∈ float | null
```

`execution_grade_effective` is the final execution grade used by decision/ranking after status/default mapping and T29 size-aware mapping. It must be emitted in `symbol_diagnostics.jsonl.gz`.

---

## Core policy

### Direct and tranche statuses

| `execution_status_raw` | `execution_size_class` | `recommended_position_factor` | `execution_grade_effective` | Meaning |
|---|---:|---:|---:|---|
| `direct_ok` | `full` | `1.00` | `100.0` | Fully tradeable at target position size |
| `tranche_ok` | `full` | `1.00` | `75.0` | Existing tranche-ok behavior unchanged |

T29 must not change `tranche_ok` execution mechanics. The grade remains the existing mapped/default value unless the repo already has a different canonical value.

### Marginal statuses

For `execution_status_raw = "marginal"`, T29 derives size eligibility from the scenario-adjusted `depth_ratio_band` under the target 10k configuration.

| `execution_status_raw` | `depth_ratio_band` | `execution_size_class` | `recommended_position_factor` | `execution_grade_effective` |
|---|---|---|---:|---:|
| `marginal` | `full` | `full` | `1.00` | `75.0` |
| `marginal` | `reduced_75` | `reduced_75` | `0.75` | `75.0` |
| `marginal` | `reduced_50` | `reduced_50` | `0.50` | `60.0` |
| `marginal` | `reduced_25` | `reduced_25` | `0.25` | `40.0` |
| `marginal` | `below_min` | `observe_only` | `0.00` | `0.0` |
| `marginal` | `not_evaluable` or null | `not_evaluable` | `null` | `null` |

This is the T28 Mapping C / strict tradeable-only policy.

Important clarifications:

```text
execution_size_class = "full" for a marginal record means that depth is sufficient for a full target-size position, but `execution_status_raw` remains "marginal" because other execution quality metrics placed it below `direct_ok`. T29 must preserve both fields. `execution_size_class` governs sizing; `execution_status_raw` remains the canonical execution outcome.
```

```text
`marginal + reduced_25` intentionally retains the current marginal baseline grade of 40.0. It receives no grade uplift. The strict Mapping C change is that `marginal + below_min` / `observe_only` is demoted from the old marginal baseline to 0.0.
```

```text
`marginal + full` and `marginal + reduced_75` intentionally share `execution_grade_effective = 75.0`. Both are fully or nearly fully depth-sufficient under the target threshold, but neither is promoted to the `direct_ok` grade of 100.0 because `execution_status_raw` remains `marginal`.
```

### Fail, unknown, and not evaluated

| Condition | `execution_size_class` | `recommended_position_factor` | `execution_grade_effective` | Meaning |
|---|---|---:|---:|---|
| `execution_status_raw = fail` | `blocked` | `0.00` | `0.0` | Hard no-trade |
| `execution_status_raw = unknown` | `not_evaluable` | `null` | `null` | No safe tradeability decision |
| `execution_attempted = False` | `not_evaluated` | `null` | `null` | Execution not evaluated for this symbol |

T29 must not promote any `fail` record to reduced-size eligibility, even if a future diagnostic run ever shows a higher depth ratio. Any such future case requires a separate manual review / follow-up ticket.

---

## Target 10k execution config

T29 must set the target execution-size defaults centrally, not by hard-coding them in analysis or policy helpers.

Required target defaults:

```yaml
execution:
  notional_total_usdt: 10000
  notional_chunk_usdt: 5000
  max_tranches: 2
  depth_buffer_multiple: 10
  min_depth_1pct_usd: 100000
```

If the existing config schema does not yet contain all keys, Codex must extend the config resolver with explicit defaults and validation.

Preferred relationship:

```text
min_depth_1pct_usd = notional_total_usdt * depth_buffer_multiple
```

If the repo keeps `min_depth_1pct_usd` as an explicit config value, T29 must validate or at least clearly enforce consistency with the derived target value. Do not allow silent divergence between:

```text
notional_total_usdt * depth_buffer_multiple
```

and:

```text
min_depth_1pct_usd
```

unless an explicit documented override mode already exists in the repo.

### Config override semantics

Partial overrides in the execution config block are field-wise merged with central defaults; missing subkeys are not invalid.

Invalid config values must fail fast with a clear error.

Validation rules:

- `notional_total_usdt`: finite positive number.
- `notional_chunk_usdt`: finite positive number.
- `max_tranches`: positive integer.
- `depth_buffer_multiple`: finite positive number.
- `min_depth_1pct_usd`: finite positive number.
- If both explicit threshold and derived threshold are present and they diverge materially, fail fast unless an existing config contract explicitly allows divergence.
- Non-finite values (`NaN`, `inf`, `-inf`) are invalid.

### Tranche relationship

Target default relationship:

```text
notional_total_usdt = notional_chunk_usdt * max_tranches
```

For the target default:

```text
10000 = 5000 * 2
```

T29 must not change tranche execution behavior. This relationship is config consistency only.

---

## Depth ratio recalculation under target config

T27 diagnostics were produced under the then-current threshold. T29 runtime must compute `depth_ratio_band` using the current effective config threshold.

Required formula:

```text
available_depth_ratio = available_depth_1pct_usdt / depth_threshold_1pct_usdt
```

Where:

```text
depth_threshold_1pct_usdt = effective_min_depth_1pct_usd
```

Under target defaults:

```text
depth_threshold_1pct_usdt = 100000
```

Band mapping:

```text
if available_depth_ratio is null:
    depth_ratio_band = "not_evaluable"
elif available_depth_ratio >= 1.00:
    depth_ratio_band = "full"
elif available_depth_ratio >= 0.75:
    depth_ratio_band = "reduced_75"
elif available_depth_ratio >= 0.50:
    depth_ratio_band = "reduced_50"
elif available_depth_ratio >= 0.25:
    depth_ratio_band = "reduced_25"
else:
    depth_ratio_band = "below_min"
```

T29 must ensure the effective threshold used in diagnostics, size class, and grade mapping is the same threshold used by the tradeability gate.

---

## Effective execution grade

### Preserve `execution_grade_t16`

`execution_grade_t16` remains a raw audit field.

Meaning:

```text
Did T16 itself provide a fine-grained execution grade?
```

Current v2.1 behavior:

```text
T16 does not provide a fine-grained grade, so `execution_grade_t16` may remain null.
```

T29 must not fill `execution_grade_t16` with mapped values such as `100`, `75`, `40`, or `0`.

### Add `execution_grade_effective`

T29 must add `execution_grade_effective` to `symbol_diagnostics.jsonl.gz`.

Meaning:

```text
Final execution grade used by decision/ranking after default/status mapping and T29 size-aware mapping.
```

This field is mandatory for records where an effective grade is deterministically available.

Rules:

- `direct_ok` → `100.0`
- `tranche_ok` → `75.0`
- `marginal + full` → `75.0`
- `marginal + reduced_75` → `75.0`
- `marginal + reduced_50` → `60.0`
- `marginal + reduced_25` → `40.0`
- `marginal + below_min` → `0.0`
- `fail` → `0.0`
- `unknown` → `null`
- `not_attempted` → `null`

If the existing ranking code uses an internal field named `execution_grade`, Codex must either:

1. route that internal value into `execution_grade_effective` for diagnostics, or
2. introduce a clear adapter so the diagnostics field and ranking input are guaranteed to match.

Required invariant:

```text
The value used in priority_score ranking must equal `execution_grade_effective` for the same record whenever `execution_grade_effective` is not null.
```

---

## Ranking integration path

T29 must integrate `execution_grade_effective` through the existing T12 ranking contract without creating a second ranking truth.

Chosen implementation path: **Option A**.

T29 derives `execution_grade_effective` after execution-size classification and injects the same numeric value into `ExecutionInputContract.execution_grade` before passing the record to the T12 decision/ranking path. The existing T12 contract rule then applies unchanged:

```text
If `ExecutionInputContract.execution_grade` is a valid finite float, T12 uses it directly for the priority-score execution component. Otherwise T12 falls back to its default status-based mapping.
```

Required consequences:

- Do not modify `ranking.py` merely to add a parallel `execution_grade_effective` lookup if the existing `ExecutionInputContract.execution_grade` override path is available.
- Do not modify `map_execution_grade` to encode T29 size-class logic unless Option A is impossible in the current repo reality.
- If Option A is impossible due to actual repo structure, Codex must implement the smallest adapter that preserves one source of truth and must document why the direct contract injection path could not be used.
- `execution_grade_effective` emitted in `symbol_diagnostics.jsonl.gz` must equal the value injected into `ExecutionInputContract.execution_grade` whenever it is non-null.
- `execution_grade_t16` remains a raw T16 audit field and must not be used as the T29 effective grade.

The T12-style formula must conceptually use the injected effective grade:

```text
priority_score = 0.30 * market_phase_confidence
               + 0.35 * state_confidence
               + 0.20 * entry_pattern_score
               + 0.15 * execution_grade_effective
```

For `unknown` / `not_evaluable` with null effective grade, preserve the existing nullability / non-finality behavior. Do not coerce unknown to `0.0` unless the existing canonical decision path already does so for a specific bucket-safe demotion path.

---

## Bucket semantics and tradeability visibility

T29 must not silently erase structurally valid candidates.

### Required behavior

- `marginal + reduced_25/reduced_50/reduced_75/full` may remain in `early_candidates` or `confirmed_candidates` and is reduced-size eligible.
- `marginal + below_min` must be marked `observe_only` and not tradeable.
- `fail` remains hard-blocked.
- `unknown` is not tradeable.

### Top-bucket handling

If the existing T12/T16 contract currently allows `marginal` into top buckets, T29 should preserve candidate visibility but add explicit tradeability fields.

Preferred output model:

```text
confirmed_candidates_all
confirmed_tradeable_candidates
confirmed_observe_only_candidates

early_candidates_all
early_tradeable_candidates
early_observe_only_candidates
```

If the repo's report schema does not support separate lists yet, T29 must at minimum add per-symbol fields so downstream consumers can filter:

- `execution_size_class`
- `recommended_position_factor`
- `execution_grade_effective`
- `is_reduced_size_eligible`
- `is_tradeable_candidate`

### Tradeable flag definitions

```text
is_reduced_size_eligible = true
iff execution_size_class ∈ {full, reduced_75, reduced_50, reduced_25}
and execution_status_raw ∈ {direct_ok, tranche_ok, marginal}
and spread/slippage gates pass if evaluated.
```

```text
is_tradeable_candidate = true
iff decision_bucket ∈ {confirmed_candidates, early_candidates}
and is_reduced_size_eligible = true.
```

`observe_only` records may remain visible in reports but must not be counted as tradeable candidates.

---

## Spread and slippage gates

T29 must preserve existing spread and slippage thresholds.

Required rule:

```text
Reduced-size eligibility does not loosen spread or slippage gates.
```

If a marginal record has sufficient depth band but violates an existing spread/slippage gate, it must not become tradeable.

If `estimated_slippage_bps` is unavailable:

- Do not invent a slippage value.
- Preserve existing behavior.
- Do not loosen eligibility because slippage is missing.
- Continue to emit null where not derivable.

Spread calculation remains valid only when:

```text
best_bid > 0
best_ask > 0
mid_price > 0
all values finite
```

---

## Diagnostics output requirements

T29 must add or populate the following fields in `symbol_diagnostics.jsonl.gz` as top-level fields, consistent with the current diagnostics schema:

```text
execution_size_class
recommended_position_factor
execution_grade_effective
is_reduced_size_eligible
is_tradeable_candidate
```

T29 must preserve these existing T27 fields:

```text
available_depth_1pct_usdt
depth_threshold_1pct_usdt
available_depth_ratio
depth_ratio_band
recommended_position_factor_preview
execution_limiting_metric
spread_pct
estimated_slippage_bps
orderbook_snapshot_age_ms
bid_depth_1pct_usdt
ask_depth_1pct_usdt
depth_side_used
execution_grade_t16
```

Do not move fields into a nested `execution` object.

Do not remove `recommended_position_factor_preview` in T29. It may remain for transition/audit purposes. The new operative field is:

```text
recommended_position_factor
```

Required relationship:

- In steady-state T29, `recommended_position_factor` should match the policy output.
- `recommended_position_factor_preview` remains diagnostic/legacy-preview and may match the operative factor, but consumers should use `recommended_position_factor`.

---

## Report output requirements

T29 must make reduced-size eligibility visible in report outputs.

At minimum, include the following per listed candidate in report outputs where candidates are shown:

```text
execution_status_raw
execution_size_class
recommended_position_factor
execution_grade_effective
available_depth_ratio
depth_ratio_band
spread_pct
estimated_slippage_bps
is_reduced_size_eligible
is_tradeable_candidate
```

Report summaries should include counts for:

```text
confirmed_candidates_total
confirmed_tradeable_candidates
confirmed_observe_only_candidates

early_candidates_total
early_tradeable_candidates
early_observe_only_candidates

marginal_reduced_75_count
marginal_reduced_50_count
marginal_reduced_25_count
marginal_observe_only_count
fail_blocked_count
unknown_not_evaluable_count
```

If Excel/Markdown reports are derived from `report.json`, ensure they do not contradict the canonical JSON/diagnostics output.

---

## Missing vs invalid vs failed semantics

T29 must preserve these distinctions:

```text
not_evaluated:
  execution was not attempted for this symbol.

not_evaluable:
  execution/orderbook evaluation was attempted or expected, but required metrics are missing/stale/invalid.

observe_only:
  execution was evaluated and the symbol may remain structurally interesting, but it is not tradeable under the minimum reduced-size policy.

blocked:
  execution was evaluated and hard-failed.

tradeable:
  execution was evaluated and the symbol is eligible for full or reduced-size trade according to size class and gates.
```

Required invariant:

```text
Not evaluable / not evaluated and evaluated-but-negative are separate states and must remain separate in code and diagnostics.
```

Do not collapse `null`, `unknown`, `below_min`, and `fail` into a single `False` state.

---

## Numeric robustness

T29 touches numeric tradeability and ranking fields. Therefore:

```text
Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid / not evaluable inputs and must not be emitted as numeric-looking outputs.
```

Rules:

- If `available_depth_1pct_usdt` is missing/non-finite: `available_depth_ratio = null`, `depth_ratio_band = not_evaluable`.
- If threshold is missing, zero, negative, or non-finite: fail fast if config-derived; otherwise emit not-evaluable for diagnostics only where appropriate.
- If `recommended_position_factor` is not derivable: null.
- If `execution_grade_effective` is not derivable: null.
- Do not coerce missing ratios to `0.0`.
- Do not coerce `unknown` to `fail`.

---

## Determinism

At identical input diagnostics/orderbook data and identical config, T29 must produce identical:

- `execution_size_class`
- `recommended_position_factor`
- `execution_grade_effective`
- `is_reduced_size_eligible`
- `is_tradeable_candidate`
- priority ordering
- report counts

Sorting/tie-breaks must remain deterministic. If the existing ranking tie-breaker is symbol/name based, preserve it. Do not introduce dict/set iteration order as an implicit tie-breaker.

---

## Pipeline placement

T29 policy should be applied after execution/orderbook evaluation and before final decision/ranking/report emission.

Required flow:

```text
Execution evaluation
  -> depth/spread/slippage diagnostics available
  -> derive execution_size_class
  -> derive recommended_position_factor
  -> derive execution_grade_effective
  -> decision/ranking uses execution_grade_effective
  -> report/diagnostics emit all fields
```

T29 must not trigger additional orderbook fetches for symbols outside the existing execution evaluation subset.

---

## Tests

Add or update tests for the following.

### Config tests

- Default config resolves to:
  - `notional_total_usdt = 10000`
  - `notional_chunk_usdt = 5000`
  - `max_tranches = 2`
  - `depth_buffer_multiple = 10`
  - `min_depth_1pct_usd = 100000`
- Partial overrides merge with defaults.
- Invalid config values fail fast:
  - `NaN`
  - `inf`
  - negative values
  - zero values
  - non-integer `max_tranches`
- Divergence between derived threshold and explicit threshold fails fast unless an existing explicit override mode exists.

### Size-class mapping tests

For `execution_status_raw = marginal`:

- ratio `>= 1.00` -> `execution_size_class = full`, factor `1.00`, grade `75.0`
- ratio `0.75..1.00` -> `reduced_75`, factor `0.75`, grade `75.0`
- ratio `0.50..0.75` -> `reduced_50`, factor `0.50`, grade `60.0`
- ratio `0.25..0.50` -> `reduced_25`, factor `0.25`, grade `40.0`
- ratio `< 0.25` -> `observe_only`, factor `0.00`, grade `0.0`
- ratio null -> `not_evaluable`, factor null, grade null

For other statuses:

- `direct_ok` -> full, factor `1.00`, grade `100.0`
- `tranche_ok` -> full, factor `1.00`, grade `75.0`
- `fail` -> blocked, factor `0.00`, grade `0.0`
- `unknown` -> not_evaluable, factor null, grade null
- `execution_attempted = False` -> `execution_size_class = "not_evaluated"`, factor null, grade null
- Assert explicitly that `execution_attempted = False` does not produce `execution_size_class = "not_evaluable"`; `not_evaluated` is the pipeline-state class, while `not_evaluable` is reserved for attempted-but-not-safely-evaluable execution records.

### Ranking tests

- Ranking uses `execution_grade_effective`, not `execution_grade_t16`.
- `execution_grade_t16 = null` does not prevent ranking when `execution_grade_effective` is available.
- `marginal + below_min` gets grade `0.0` and ranks behind equivalent reduced-size-eligible records.
- `marginal + reduced_50` ranks above an otherwise identical `marginal + reduced_25` record.
- Priority score equals the expected formula using `execution_grade_effective`.

### Diagnostics tests

`symbol_diagnostics.jsonl.gz` includes top-level:

- `execution_size_class`
- `recommended_position_factor`
- `execution_grade_effective`
- `is_reduced_size_eligible`
- `is_tradeable_candidate`

Also verify:

- `execution_grade_t16` remains null when T16 did not provide a raw grade.
- T29 does not fill `execution_grade_t16` with mapped/default grades.
- Existing T27 depth/spread/slippage fields remain present.
- No JSON `NaN`/`inf` values are emitted.

### Report tests

- Report includes reduced-size fields for candidates.
- Confirmed/early tradeable counts exclude `observe_only`, `blocked`, `unknown`, and `not_evaluable`.
- `marginal + below_min` may remain visible but is not counted as tradeable.
- `fail` is not shown as tradeable.
- Direct candidates remain tradeable when all gates pass.

### No-policy-regression tests

- No `fail -> marginal` promotion occurs.
- No order-splitting behavior changes.
- No additional execution fetches are triggered outside the existing execution subset.
- Existing spread/slippage gates are not loosened.
- Phase/state/pattern logic is unchanged.

---

## Acceptance criteria

- [ ] Target execution defaults are centrally configured as 10k total notional, 5k chunk, 2 max tranches, 10x depth buffer, 100k 1%-depth threshold.
- [ ] No hard-coded 10k/100k values are embedded outside config/default resolution and tests.
- [ ] `execution_size_class` is derived and emitted in diagnostics.
- [ ] `recommended_position_factor` is derived and emitted in diagnostics.
- [ ] `execution_grade_effective` is derived, emitted in diagnostics, and injected into `ExecutionInputContract.execution_grade` for ranking via the existing T12 override path.
- [ ] `execution_grade_t16` remains a raw T16 audit field and is not repurposed.
- [ ] `direct_ok` remains full tradeable.
- [ ] `tranche_ok` behavior remains unchanged.
- [ ] `marginal + reduced_25/reduced_50/reduced_75/full` becomes reduced-size eligible subject to unchanged spread/slippage gates.
- [ ] `marginal + below_min` becomes `observe_only`, not tradeable.
- [ ] `fail` remains blocked / hard no-trade.
- [ ] `unknown` remains not safely tradeable.
- [ ] Report outputs distinguish all candidates from tradeable candidates and observe-only candidates.
- [ ] Existing T27 diagnostic fields remain present and top-level.
- [ ] No non-finite numeric values are emitted.
- [ ] Tests cover config, size-class mapping, effective grade, ranking integration, diagnostics, reports, and no-regression constraints.
- [ ] Full test suite passes with `python -m pytest -q`.

---

## Invariants

- T29 is the first implementation of reduced-size eligibility, but only for `marginal` records with sufficient depth band.
- `fail` is not eligible for reduced-size trading.
- `marginal + below_min` is observable but not tradeable.
- `execution_grade_t16` remains raw/audit-only.
- `execution_grade_effective` is the final ranking/decision grade and must be visible in diagnostics.
- Spread/slippage gates are not loosened.
- No order-splitting semantics are changed.
- No additional external calls are introduced.
- Existing phase/state/pattern semantics remain unchanged.

---

## Follow-on after T29

Potential follow-ons, not part of T29:

- T30: Evaluate reduced-size candidate forward returns / MFE / MAE.
- Stablecoin exclusion / eligibility follow-up if TUSD-style false positives remain visible.
- Overextension / late-risk report marker for coins with extreme 7d or 30d moves.
- Future T16 fine-grained execution scoring that may eventually populate `execution_grade_t16`.
- Separate tranche/order-splitting policy revision.
