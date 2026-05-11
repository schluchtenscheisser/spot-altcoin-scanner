# T_EL2: Implement Entry-Location / Action-Hint Layer v1

## Metadata

- Ticket ID: T_EL2
- Title: Implement Entry-Location / Action-Hint Layer v1
- Status: Draft for review
- Priority: P1
- Language: Implementation and code artifacts in English
- Primary mode affected: Daily Shadow-Live diagnostics and reports
- Implementation type: Informational decision-layer extension
- Schema context: `ir1.2` diagnostics provide `entry_location_inputs`
- Depends on: T_EL1 Step A re-run, T_EL1 Step B calibration, T_EL1b diagnostics extension, T29 tradeability diagnostics

---

## Authoritative reference set

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. Canonical docs, as long as they do not contradict the v2.1 specification or this explicitly approved T_EL2 calibration decision.
4. `docs/canonical/open_questions.md`.
5. `docs/canonical/feature_enhancements.md`, especially the Entry-Location / Chase-Risk Layer entry.
6. T_EL1 Step A re-run + Step B analysis over `ir1.2` Shadow-Live artifacts from 2026-05-08, 2026-05-09, and 2026-05-10.
7. T28/T29 diagnostics semantics for execution and reduced-size eligibility.
8. Master ticket preflight checklist.

If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents continue to apply only insofar as they do not contradict this reference set.

---

## Purpose and motivation

The current scanner can output candidates as actionable even when the price is already materially extended above the 4h EMA20 or near a local range high. T_EL1 Step B has now produced provisional empirical thresholds from three `ir1.2` Shadow-Live daily runs.

T_EL2 implements the first production version of an Entry-Location / Action-Hint Layer.

This layer must answer two different questions and keep them separate:

1. `entry_location_status`: How fresh or extended is the candidate's current entry location?
2. `entry_action_hint`: Given the location status plus bucket, tradeability, universe exclusion, and execution size class, how should this candidate be displayed operationally?

T_EL2 v1 is informational only. It must not change ranking, bucket membership, tradeability gates, or order execution.

---

## Empirical calibration basis

The thresholds in this ticket are provisional starting points derived from three `ir1.2` Shadow-Live daily runs:

- 2026-05-08
- 2026-05-09
- 2026-05-10

Observed populations:

| Population | Count |
|---|---:|
| Day-0 confirmed candidates | 40 |
| Day-1+ confirmed candidates | 10 |
| Day-0 early candidates | 41 |
| Tradeable Day-0 confirmed candidates | 7 |

Important caveat:

> Thresholds are derived from 3 Shadow-Live runs (`n=40` Day-0 confirmed, `n=7` tradeable). These are provisional starting points, not statistically validated benchmarks. Recalibration is expected after 10+ runs.

Core calibration decisions approved for T_EL2 v1:

| Dimension | Decision |
|---|---|
| Global EMA20 thresholds | `2.5 / 5.5 / 8.5` |
| Pattern override | only `continuation_breakout`: `3.5 / 7.0 / 10.0` |
| `distance_to_range_high_pct_abs` | auxiliary warning only, not a status dimension |
| Extreme EMA distance | `> 50.0` => `not_evaluable` |
| Range-high proximity warning | `<= 0.5` => `range_high_proximity_warning = true` |
| Negative `close_vs_ema20_4h_pct` | may still be `fresh_entry`; do not mark not_evaluable solely because it is below EMA20 |

---

## Scope

### In scope

1. Add a new deterministic entry-location module:

```text
scanner/decision/entry_location.py
```

2. Add config support under:

```yaml
independence_release.entry_location
```

3. Compute and emit these new diagnostics fields per symbol:

```text
entry_location_status
entry_action_hint
entry_location_reason_primary
entry_location_reason_codes
entry_location_inputs_used
range_high_proximity_warning
```

4. Add report-level segments:

```text
buy_now_candidates
wait_pullback_candidates
early_watch_candidates
good_location_but_not_tradeable
tradeable_but_extended
```

5. Add unit tests for config resolution, status classification, action-hint mapping, edge cases, and report segment building.

6. Preserve all missing / not-evaluable / invalid states as explicit states. Do not collapse them to `false`.

### Out of scope

T_EL2 v1 must not:

- modify `priority_score`
- modify `decision_bucket`
- modify bucket membership
- modify the Tradeability Gate
- modify execution grading
- modify `is_tradeable_candidate` semantics
- solve Q1 (`is_tradeable_candidate` vs. `candidate_excluded`)
- solve Q2 stablecoin/cash-proxy exclusion
- implement `is_operational_trade_candidate`
- implement any order execution
- add forward-return evaluation
- add short-term return overextension metrics such as `return_24h_pct`, `return_3d_pct`, or `return_7d_pct`
- reclassify historical artifacts

---

## Pipeline position

Entry-location computation runs after these layers already exist for a record:

1. Phase
2. State
3. Entry pattern
4. Execution / tradeability diagnostics where evaluated
5. Decision bucket
6. Universe classification / candidate exclusion

It runs before final diagnostics/report serialization.

T_EL2 is a soft informational layer. It must not stop later processing and must not trigger additional expensive data fetches.

---

## Required input paths

All fachliche diagnostic fields must be read from their canonical nested paths. Do not use top-level fallback access for nested fields.

### Entry-location inputs

```text
rec["entry_location_inputs"]["close_vs_ema20_4h_pct"]
rec["entry_location_inputs"]["dist_to_ema20_4h_pct_abs"]
rec["entry_location_inputs"]["bars_above_ema20_4h"]
rec["entry_location_inputs"]["distance_to_last_structural_anchor_pct_abs"]
rec["entry_location_inputs"]["bars_since_last_structural_break_4h"]
rec["entry_location_inputs"]["distance_to_range_high_pct_abs"]
```

### Decision / pattern / universe / execution context

Use actual repo models / builders where available, but preserve these semantics:

```text
rec["decision"]["decision_bucket"]
rec["pattern"]["entry_pattern"]
rec["candidate_excluded"]  # top-level field in current ir1.2 diagnostics; not nested under rec["universe"]
rec["is_tradeable_candidate"]
rec["execution_size_class"]
rec["execution_status_raw"]
```

If the repo currently represents these values via typed intermediate objects rather than raw diagnostic dictionaries, implement equivalent typed access at the layer where diagnostics are built. Do not introduce a second competing field source.

---

## New output fields

### `entry_location_status`

Type: nullable string enum.

Allowed values:

```text
fresh_entry
acceptable_entry
extended_entry
chased_entry
not_evaluable
```

Meaning:

| Value | Meaning |
|---|---|
| `fresh_entry` | The current price is close enough to the calibrated 4h EMA20 entry zone to be considered fresh. |
| `acceptable_entry` | The current price is no longer ideal but remains within the calibrated acceptable entry zone. |
| `extended_entry` | The current price is materially extended; a pullback is preferred. |
| `chased_entry` | The current price is beyond the calibrated extended zone; chasing should be avoided. |
| `not_evaluable` | Required inputs are missing, invalid, non-finite, malformed, or outside the calibration range. |

`entry_location_status` is an entry-location classification only. It does not mean the candidate is tradeable or operationally actionable.

### `entry_action_hint`

Type: nullable string enum.

Allowed values:

```text
buy_now_candidate
acceptable_if_strategy_allows
wait_for_pullback
avoid_chasing
monitor_only
not_evaluable
```

Meaning:

| Value | Meaning |
|---|---|
| `buy_now_candidate` | Confirmed, tradeable, full-size candidate with fresh entry location. |
| `acceptable_if_strategy_allows` | Potentially usable only if strategy accepts the location / reduced-size execution tradeoff. |
| `wait_for_pullback` | Location and/or execution-size combination is no longer good enough for immediate action. |
| `avoid_chasing` | Entry location is chased; do not chase this move. |
| `monitor_only` | Keep visible as a diagnostic / watch item, but do not treat as an actionable buy candidate. |
| `not_evaluable` | Action hint cannot be evaluated because entry location itself is not evaluable. |

### `entry_location_reason_primary`

Type: nullable string.

Single stable machine-readable primary reason code for `entry_location_status`, not for the later `entry_action_hint` override result. It must be `null` only when the entire entry-location layer is disabled.

Action-hint reasons produced by the ordered override sequence or the main action matrix must be appended to `entry_location_reason_codes`; they must not replace the status-level primary reason. In other words: `entry_location_reason_primary` explains `entry_location_status`; `entry_location_reason_codes` contains both the status reason if useful for traceability and all final action-hint reasons such as `candidate_excluded_monitor_only` or `fresh_full_buy_now_candidate`.

Allowed status-level primary reason examples:

```text
fresh_by_default_ema20_distance
acceptable_by_default_ema20_distance
extended_by_default_ema20_distance
chased_by_default_ema20_distance
fresh_by_continuation_breakout_override
acceptable_by_continuation_breakout_override
extended_by_continuation_breakout_override
chased_by_continuation_breakout_override
missing_entry_location_inputs
invalid_entry_location_inputs_type
missing_dist_to_ema20_4h_pct_abs
non_finite_dist_to_ema20_4h_pct_abs
invalid_negative_abs_ema20_distance
extreme_ema20_distance_outside_calibration_range
```

Action-hint reason code examples that belong in `entry_location_reason_codes`, not in `entry_location_reason_primary`:

```text
fresh_full_buy_now_candidate
candidate_excluded_monitor_only
not_tradeable_monitor_only
early_bucket_monitor_only
fresh_reduced_size_acceptable
acceptable_reduced_size_strategy_allows
acceptable_reduced_25_wait_for_pullback
extended_wait_for_pullback
range_high_proximity_warning
unhandled_action_hint_combination
```

### `entry_location_reason_codes`

Type: list of strings.

- Must always be present when the layer is enabled.
- Empty list is allowed only if the implementation has no secondary reasons beyond `entry_location_reason_primary`.
- Include warning/context reason codes such as `range_high_proximity_warning` without changing the enum if the warning does not alter the final action hint.

### `entry_location_inputs_used`

Type: object/dict.

Must include the sanitized numeric inputs used for the final status computation and key warning flags. Suggested shape:

```json
{
  "dist_to_ema20_4h_pct_abs": 4.66,
  "close_vs_ema20_4h_pct": 4.66,
  "bars_above_ema20_4h": 3,
  "distance_to_last_structural_anchor_pct_abs": 1.01,
  "bars_since_last_structural_break_4h": 1,
  "distance_to_range_high_pct_abs": 0.42,
  "entry_pattern": "early_reversal_break",
  "threshold_source": "default",
  "range_high_proximity_warning": true
}
```

Missing or invalid inputs must remain `null` in this object. Do not coerce missing values to `0`.

### `range_high_proximity_warning`

Type: nullable bool.

Semantics:

```text
true   distance_to_range_high_pct_abs is finite and <= cfg.entry_location.auxiliary.distance_to_range_high_pct_abs.proximity_warning_max_pct
false  distance_to_range_high_pct_abs is finite and above the warning threshold
null   distance_to_range_high_pct_abs is missing, invalid, non-finite, or auxiliary range-high warning is disabled
```

This field is an auxiliary diagnostic/warning only in T_EL2 v1. It must not change `entry_location_status` and must not change `entry_action_hint` in v1.

---

## Config defaults

Add this default config block to the central Independence config defaults. Use the actual repo config style, but preserve the exact semantics and values below.

```yaml
independence_release:
  entry_location:
    enabled: true
    version: "v1"

    thresholds:
      default:
        dist_to_ema20_4h_pct_abs:
          fresh_max: 2.5
          acceptable_max: 5.5
          extended_max: 8.5

      pattern_overrides:
        continuation_breakout:
          dist_to_ema20_4h_pct_abs:
            fresh_max: 3.5
            acceptable_max: 7.0
            extended_max: 10.0

    auxiliary:
      distance_to_range_high_pct_abs:
        enabled: true
        proximity_warning_max_pct: 0.5
        usage: "diagnostic_warning_only"

    guards:
      extreme_value_not_evaluable_pct: 50.0
```

### Config resolution rules

- Missing `independence_release.entry_location` block: use defaults.
- Partial overrides in `independence_release.entry_location` are merged field-by-field with central defaults; missing subkeys are not invalid.
- Unknown keys are allowed only if existing repo config policy generally allows unknown keys. If the repo normally rejects unknown keys, reject them here too. Do not create a special one-off policy.
- Invalid numeric config values must raise a clear config validation error before a scan starts.
- All threshold values must be finite numbers.
- Threshold ordering must be validated:

```text
fresh_max < acceptable_max < extended_max
```

- `extreme_value_not_evaluable_pct` must be finite and greater than the largest configured `extended_max` across default and all pattern overrides.
- `proximity_warning_max_pct` must be finite and `>= 0`.
- `version` must be exactly `"v1"` for this ticket.

Partial overrides in `independence_release.entry_location` are merged field-by-field with central defaults; missing subkeys are not invalid.

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid config values and must not be accepted.

---

## Entry-location status algorithm

### Required primary input

The primary classification input is:

```text
dist_to_ema20_4h_pct_abs
```

Use this field rather than re-computing absolute distance from `close_vs_ema20_4h_pct`.

### Validation sequence for status

The status classifier must run this ordered sequence. First match wins.

1. If entry-location layer disabled:

```text
entry_location_status = null
entry_action_hint = null
reason_primary = null
reason_codes = []
```

2. If `entry_location_inputs` is missing or not a mapping:

```text
entry_location_status = not_evaluable
reason_primary = missing_entry_location_inputs or invalid_entry_location_inputs_type
```

3. If `dist_to_ema20_4h_pct_abs` is missing:

```text
entry_location_status = not_evaluable
reason_primary = missing_dist_to_ema20_4h_pct_abs
```

4. If `dist_to_ema20_4h_pct_abs` is not a finite numeric value:

```text
entry_location_status = not_evaluable
reason_primary = non_finite_dist_to_ema20_4h_pct_abs
```

5. If `dist_to_ema20_4h_pct_abs < 0`:

```text
entry_location_status = not_evaluable
reason_primary = invalid_negative_abs_ema20_distance
```

6. If `dist_to_ema20_4h_pct_abs > cfg.entry_location.guards.extreme_value_not_evaluable_pct`:

```text
entry_location_status = not_evaluable
reason_primary = extreme_ema20_distance_outside_calibration_range
```

7. Resolve thresholds:

- If `entry_pattern` has a configured pattern override, use that override.
- Otherwise use `thresholds.default.dist_to_ema20_4h_pct_abs`.
- For T_EL2 v1, the only default configured pattern override is `continuation_breakout`.

8. Classify:

```text
if dist <= fresh_max:        fresh_entry
elif dist <= acceptable_max: acceptable_entry
elif dist <= extended_max:   extended_entry
else:                        chased_entry
```

Boundary rule: Thresholds are inclusive at the upper bound. Example: exactly `2.5` is `fresh_entry`; exactly `5.5` is `acceptable_entry`; exactly `8.5` is `extended_entry`.

### Negative `close_vs_ema20_4h_pct`

Do not mark a record as `not_evaluable` solely because `close_vs_ema20_4h_pct` is negative.

If `dist_to_ema20_4h_pct_abs` is finite, non-negative, and not extreme, a candidate below EMA20 may still classify as `fresh_entry`, especially for `range_reclaim` / `base_reclaim`-like contexts.

### Secondary metrics

These fields are recorded in `entry_location_inputs_used` for diagnostics and later recalibration only:

```text
bars_above_ema20_4h
distance_to_last_structural_anchor_pct_abs
bars_since_last_structural_break_4h
```

In T_EL2 v1 they must not override the primary EMA20-distance status and must not have config thresholds. The v1 classifier's status decision is based only on `dist_to_ema20_4h_pct_abs`, the optional `continuation_breakout` EMA20 override, and the extreme-value guard.

---

## Range-high auxiliary warning

Compute `range_high_proximity_warning` independently after input sanitization.

Rules:

1. If auxiliary config is disabled:

```text
range_high_proximity_warning = null
```

2. If `distance_to_range_high_pct_abs` is missing, invalid, or non-finite:

```text
range_high_proximity_warning = null
```

3. If finite:

```text
range_high_proximity_warning = distance_to_range_high_pct_abs <= proximity_warning_max_pct
```

Default:

```text
proximity_warning_max_pct = 0.5
```

In T_EL2 v1 this warning is diagnostic-only. It must be emitted and included in reason codes when true, but it must not change `entry_location_status` or `entry_action_hint`.

Rationale: `distance_to_range_high_pct_abs` is now numerically present in `ir1.2` artifacts, but its calibration evidence remains thin. It is therefore visible and auditable, not yet a primary action modifier.

---

## Entry-action-hint algorithm

`entry_action_hint` must be resolved as an ordered sequence. This is not a set of unordered conditions. First match wins.

### Required ordered override sequence

1. If `entry_location_inputs` are missing / invalid, or `dist_to_ema20_4h_pct_abs` is missing / invalid / non-finite / extreme:

```text
entry_action_hint = not_evaluable
```

Implementation note: This is normally reached because `entry_location_status == not_evaluable`. It must remain first so invalid/extreme input is not overwritten by later operational context.

2. If `entry_location_status == chased_entry`:

```text
entry_action_hint = avoid_chasing
```

3. If `candidate_excluded == True`:

```text
entry_action_hint = monitor_only
```

This rule must run before `is_tradeable_candidate` because Q1 remains unresolved and records can currently have both `candidate_excluded == True` and `is_tradeable_candidate == True`.

4. If `is_tradeable_candidate != True`:

```text
entry_action_hint = monitor_only
```

Use `!= True`, not `== False`, so `None`, missing, or tri-state unknown values do not slip into the action matrix.

5. If `decision_bucket == early_candidates`:

```text
entry_action_hint = monitor_only
```

Early candidates are not confirmed action signals in T_EL2 v1, even if execution and entry location are good.

6. Remaining active space:

```text
confirmed_candidates
AND is_tradeable_candidate == True
AND candidate_excluded != True
AND entry_location_status in {fresh_entry, acceptable_entry, extended_entry}
```

Apply the main matrix below.

### Main matrix for confirmed + tradeable candidates

| `entry_location_status` | `execution_size_class` | `entry_action_hint` | Action-hint reason code |
|---|---|---|---|
| `fresh_entry` | `full` | `buy_now_candidate` | `fresh_full_buy_now_candidate` |
| `fresh_entry` | `reduced_75` | `acceptable_if_strategy_allows` | `fresh_reduced_size_acceptable` |
| `fresh_entry` | `reduced_50` | `acceptable_if_strategy_allows` | `fresh_reduced_size_acceptable` |
| `fresh_entry` | `reduced_25` | `acceptable_if_strategy_allows` | `fresh_reduced_size_acceptable` |
| `acceptable_entry` | `full` | `acceptable_if_strategy_allows` | `acceptable_full_strategy_allows` |
| `acceptable_entry` | `reduced_75` | `acceptable_if_strategy_allows` | `acceptable_reduced_size_strategy_allows` |
| `acceptable_entry` | `reduced_50` | `acceptable_if_strategy_allows` | `acceptable_reduced_size_strategy_allows` |
| `acceptable_entry` | `reduced_25` | `wait_for_pullback` | `acceptable_reduced_25_wait_for_pullback` |
| `extended_entry` | any value | `wait_for_pullback` | `extended_wait_for_pullback` |

Fallback rule:

If no override rule and no main-matrix row matches, then:

```text
entry_action_hint = monitor_only
append `unhandled_action_hint_combination` to `entry_location_reason_codes`
```

This fallback is required to avoid implicit Codex interpretation for new or unexpected execution size classes.

### Enum handling for execution size class

Known `execution_size_class` values in scope for the main matrix:

```text
full
reduced_75
reduced_50
reduced_25
observe_only
blocked
not_evaluable
not_evaluated
```

Only `full`, `reduced_75`, `reduced_50`, and `reduced_25` can reach the main matrix when `is_tradeable_candidate == True` and earlier guards pass. If another value reaches the matrix, use the fallback `monitor_only` with reason `unhandled_action_hint_combination`.

---

## Candidate exclusion and open Q1/Q2 handling

T_EL2 does not resolve the canonical semantics of `is_tradeable_candidate` vs. `candidate_excluded`.

However, T_EL2 must defensively prevent excluded candidates from becoming operational action hints:

```text
candidate_excluded == True => entry_action_hint = monitor_only
```

This is a local action-hint safeguard only. It must not mutate `is_tradeable_candidate`, `decision_bucket`, or universe classification fields.

---

## Report segments

Add report segments using the new fields. Use existing report builder conventions and naming style where available.

### `buy_now_candidates`

Include symbols where:

```text
entry_action_hint == buy_now_candidate
```

### `wait_pullback_candidates`

Include symbols where:

```text
entry_action_hint == wait_for_pullback
```

### `early_watch_candidates`

Include symbols where:

```text
decision_bucket == early_candidates
AND entry_location_status in {fresh_entry, acceptable_entry}
AND entry_action_hint == monitor_only
```

The third condition is intentionally explicit even though it is guaranteed by ordered override rule 5. It documents the expected serialized output and prevents future changes from silently making early candidates actionable.

### `good_location_but_not_tradeable`

Include symbols where:

```text
entry_location_status in {fresh_entry, acceptable_entry}
AND is_tradeable_candidate != True
AND candidate_excluded != True
```

This segment is intended to surface cases such as good location but observe-only / blocked / unknown execution.

### `tradeable_but_extended`

Include symbols where:

```text
is_tradeable_candidate == True
AND candidate_excluded != True
AND entry_location_status in {extended_entry, chased_entry}
```

### Segment ordering

If a segment is displayed as a list, sort deterministically by:

1. `decision.priority_score` descending, with `null` last
2. `symbol` ascending

At identical input and identical config, segment membership and ordering must be identical.

---

## Diagnostics / report serialization

Add the new fields to `symbol_diagnostics.jsonl.gz` for every symbol when the layer is enabled.

Required placement:

- Keep `entry_location_inputs` unchanged as the canonical raw input namespace.
- Add all T_EL2-derived fields under the nested `entry_location` block.
- Do not emit top-level aliases for T_EL2-derived fields.
- Do not duplicate conflicting nested and top-level versions.

Required shape:

```json
{
  "entry_location": {
    "entry_location_status": "fresh_entry",
    "entry_action_hint": "buy_now_candidate",
    "entry_location_reason_primary": "fresh_by_default_ema20_distance",
    "entry_location_reason_codes": ["fresh_full_buy_now_candidate"],
    "range_high_proximity_warning": false,
    "entry_location_inputs_used": {
      "dist_to_ema20_4h_pct_abs": 1.27,
      "close_vs_ema20_4h_pct": 1.27,
      "bars_above_ema20_4h": 4,
      "distance_to_last_structural_anchor_pct_abs": 0.42,
      "bars_since_last_structural_break_4h": 1,
      "distance_to_range_high_pct_abs": 2.1,
      "entry_pattern": "early_reversal_break",
      "threshold_source": "default"
    }
  }
}
```

If a schema version bump is required by existing schema policy, bump from `ir1.2` to the next appropriate version and document it in the affected schema/report docs. Do not bump schema ad hoc if existing policy allows additive diagnostics fields without a version bump.

## Documentation updates

Update relevant canonical docs only if they exist and are part of the current repo reality.

Minimum documentation update:

1. Document the new Entry-Location / Action-Hint Layer, including:
   - field names
   - enum values
   - status vs action-hint distinction
   - ordered action-hint override rules
   - config defaults
   - no impact on score/bucket/gate

2. Update the Q3 text around `distance_to_range_high_pct_abs` if `open_questions.md` is in scope for this PR:
   - It is no longer correct to say the field is universally null in current `ir1.2` artifacts.
   - The field is numerically present and used as a T_EL2 v1 auxiliary diagnostic warning only.
   - Its primary-status calibration remains deferred.

Do not mark Q3 as fully resolved unless the canonical formula and ownership questions are explicitly documented. The correct status after T_EL2 v1 is closer to:

```text
partially superseded by ir1.2 observation; auxiliary diagnostic usage allowed; primary calibration still deferred
```

---

## Nullability and tri-state rules

- `entry_location_status` is nullable only when the entire layer is disabled. When enabled, it must be one of the allowed enum values.
- `entry_action_hint` is nullable only when the entire layer is disabled. When enabled, it must be one of the allowed enum values.
- `range_high_proximity_warning` is nullable. `null` means not reliably evaluable or auxiliary warning disabled. It must not be implicitly coerced to `false`.
- `candidate_excluded` must be checked with `is True` semantics, not truthiness of arbitrary values.
- `is_tradeable_candidate` must be checked as `!= True` for the defensive monitor-only override.
- Do not use `bool(value)` on nullable semantic fields.

`range_high_proximity_warning` is nullable. `null` means not reliably evaluable or disabled and must not be implicitly coerced to `false`.

Non-evaluable / not assessed and fachlich negative states are separate and must remain separate in code.

---

## Numeric robustness

All percentage inputs are real percentage values. Example: `4.5` means `4.5%`, not `0.045`.

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid or not-evaluable inputs and must not be passed through into numeric-looking outputs.

Input handling:

| Input condition | Expected behavior |
|---|---|
| Missing `entry_location_inputs` | `not_evaluable` |
| `entry_location_inputs` not a mapping | `not_evaluable` |
| Missing `dist_to_ema20_4h_pct_abs` | `not_evaluable` |
| `dist_to_ema20_4h_pct_abs = None` | `not_evaluable` |
| `dist_to_ema20_4h_pct_abs = NaN/inf/-inf` | `not_evaluable` |
| `dist_to_ema20_4h_pct_abs < 0` | `not_evaluable` |
| `dist_to_ema20_4h_pct_abs > 50.0` | `not_evaluable` |
| `close_vs_ema20_4h_pct < 0` but abs distance valid | classify normally by abs distance |
| Missing `distance_to_range_high_pct_abs` | `range_high_proximity_warning = null`; status unaffected |
| Non-finite `distance_to_range_high_pct_abs` | `range_high_proximity_warning = null`; status unaffected |

---

## Determinism and invariants

- At identical input and identical config, `entry_location_status`, `entry_action_hint`, reason codes, segment membership, and segment ordering must be identical.
- Action-hint override rules must be implemented as an ordered sequence. They must not be implemented as an unordered condition set.
- The first matching action-hint rule wins.
- No entry-location field may change `priority_score` in T_EL2 v1.
- No entry-location field may change bucket membership in T_EL2 v1.
- No entry-location field may change `is_tradeable_candidate` in T_EL2 v1.
- No entry-location field may trigger order execution.
- `distance_to_range_high_pct_abs` must not change `entry_location_status` in T_EL2 v1.
- `range_high_proximity_warning` must not change `entry_action_hint` in T_EL2 v1.

---

## Testing requirements

Add unit tests in the repo's existing test structure. Reuse existing fixtures/builders where possible.

### Config tests

1. Missing `entry_location` config uses defaults.
2. Partial override merges with defaults.
3. Invalid threshold order fails validation.
4. `NaN`, `inf`, `-inf` config values fail validation.
5. `extreme_value_not_evaluable_pct <= max(extended_max)` fails validation.
6. `proximity_warning_max_pct < 0` fails validation.

### Status classification tests

1. `dist_to_ema20_4h_pct_abs = 0.0` => `fresh_entry`.
2. `dist_to_ema20_4h_pct_abs = 2.5` => `fresh_entry`.
3. `dist_to_ema20_4h_pct_abs = 2.51` => `acceptable_entry`.
4. `dist_to_ema20_4h_pct_abs = 5.5` => `acceptable_entry`.
5. `dist_to_ema20_4h_pct_abs = 5.51` => `extended_entry`.
6. `dist_to_ema20_4h_pct_abs = 8.5` => `extended_entry`.
7. `dist_to_ema20_4h_pct_abs = 8.51` => `chased_entry`.
8. `continuation_breakout` uses `3.5 / 7.0 / 10.0` thresholds.
9. Missing `entry_location_inputs` => `not_evaluable`.
10. Non-mapping `entry_location_inputs` => `not_evaluable`.
11. Missing / `None` / `NaN` / `inf` `dist_to_ema20_4h_pct_abs` => `not_evaluable`.
12. `dist_to_ema20_4h_pct_abs = 50.01` => `not_evaluable`.
13. Negative `close_vs_ema20_4h_pct` with valid abs distance <= 2.5 => `fresh_entry`.
14. Changing `bars_above_ema20_4h` while `dist_to_ema20_4h_pct_abs` and pattern stay fixed does not change `entry_location_status`.
15. Changing `distance_to_last_structural_anchor_pct_abs` while `dist_to_ema20_4h_pct_abs` and pattern stay fixed does not change `entry_location_status`.
16. Changing `bars_since_last_structural_break_4h` while `dist_to_ema20_4h_pct_abs` and pattern stay fixed does not change `entry_location_status`.

### Range-high warning tests

1. `distance_to_range_high_pct_abs = 0.5` => `range_high_proximity_warning = true`.
2. `distance_to_range_high_pct_abs = 0.51` => `range_high_proximity_warning = false`.
3. Missing / `None` / `NaN` / `inf` `distance_to_range_high_pct_abs` => `range_high_proximity_warning = null`.
4. Warning true does not change `entry_location_status`.
5. Warning true does not change `entry_action_hint`.

### Action-hint ordered override tests

1. `not_evaluable` status => `not_evaluable`, even if candidate is otherwise tradeable.
2. `chased_entry` => `avoid_chasing`.
3. `candidate_excluded == True` and `is_tradeable_candidate == True` => `monitor_only`.
4. `is_tradeable_candidate = False` => `monitor_only`.
5. `is_tradeable_candidate = None` => `monitor_only`.
6. `early_candidates + fresh_entry + full + tradeable` => `monitor_only`.
7. `confirmed + fresh_entry + full + tradeable` => `buy_now_candidate`.
8. `confirmed + fresh_entry + reduced_25 + tradeable` => `acceptable_if_strategy_allows`.
9. `confirmed + acceptable_entry + full + tradeable` => `acceptable_if_strategy_allows`.
10. `confirmed + acceptable_entry + reduced_50 + tradeable` => `acceptable_if_strategy_allows`.
11. `confirmed + acceptable_entry + reduced_25 + tradeable` => `wait_for_pullback`.
12. `confirmed + extended_entry + full + tradeable` => `wait_for_pullback`.
13. Unknown execution size reaching matrix => `monitor_only` with `unhandled_action_hint_combination`.

### Report segment tests

1. `buy_now_candidates` contains only `entry_action_hint == buy_now_candidate`.
2. `wait_pullback_candidates` contains only `entry_action_hint == wait_for_pullback`.
3. `early_watch_candidates` includes early fresh/acceptable monitor-only candidates.
4. `good_location_but_not_tradeable` includes fresh/acceptable non-tradeable non-excluded candidates.
5. `tradeable_but_extended` includes tradeable extended/chased non-excluded candidates.
6. Segment sorting is deterministic by priority score descending, then symbol ascending.

### Regression tests from observed cases

Use minimal synthetic records if full artifact fixtures are too large.

1. AIXDROPUSDT-like case:
   - `entry_pattern = ema_reclaim`
   - `dist_to_ema20_4h_pct_abs > 50.0`
   - expected: `entry_location_status = not_evaluable`, `entry_action_hint = not_evaluable`

2. USDPUSDT-like case:
   - `candidate_excluded = True`
   - `is_tradeable_candidate = True`
   - otherwise fresh / tradeable
   - expected: `entry_action_hint = monitor_only`

3. 1INCHUSDT-like case:
   - `entry_location_status = fresh_entry`
   - `is_tradeable_candidate != True`
   - expected: `entry_action_hint = monitor_only`, included in `good_location_but_not_tradeable`

4. ASTERUSDT-like case:
   - `dist_to_ema20_4h_pct_abs = 5.49`
   - default thresholds
   - expected: `acceptable_entry`

---

## Acceptance criteria

1. `scanner/decision/entry_location.py` or equivalent module exists and contains deterministic, unit-tested status and hint resolution.
2. Config defaults for `independence_release.entry_location` are added and validated.
3. Partial config overrides merge with defaults.
4. Invalid config fails fast with clear errors.
5. New diagnostics fields are emitted for every symbol when the layer is enabled.
6. `entry_location_inputs` remains the canonical input namespace and is not renamed.
7. `entry_location_status` has exactly the allowed enum values when enabled.
8. `entry_action_hint` has exactly the allowed enum values when enabled.
9. Action-hint override rules are implemented in the exact ordered sequence from this ticket.
10. `candidate_excluded == True` is evaluated before `is_tradeable_candidate != True`.
11. `is_tradeable_candidate != True` is used, not `== False`.
12. `early_candidates` never become `buy_now_candidate` in T_EL2 v1.
13. Reduced-size candidates do not become `buy_now_candidate` in T_EL2 v1.
14. `distance_to_range_high_pct_abs` produces `range_high_proximity_warning`, but does not change status or hint in v1.
15. Secondary diagnostic fields (`bars_above_ema20_4h`, `distance_to_last_structural_anchor_pct_abs`, `bars_since_last_structural_break_4h`) do not change `entry_location_status` in v1 and do not have v1 config thresholds.
16. `dist_to_ema20_4h_pct_abs > 50.0` produces `not_evaluable`.
17. Negative `close_vs_ema20_4h_pct` alone does not produce `not_evaluable`.
18. No `priority_score`, bucket membership, tradeability, or execution gate behavior changes.
19. Report segments are added and deterministically sorted.
20. Required unit tests pass.
21. Existing test suite passes.
22. Documentation is updated for new fields and Q3 partial-supercession if in scope.

---

## Definition of Done

- Code compiles and tests pass.
- Entry-location module is deterministic and covered by unit tests.
- Config resolution and validation are tested.
- Diagnostics include the new fields.
- Reports include the new segments.
- No ranking, bucket, tradeability, or execution behavior is changed.
- Canonical docs do not falsely claim `distance_to_range_high_pct_abs` is universally null after this ticket.
- The PR description explicitly states that T_EL2 v1 is informational only.

---

## Non-goals to reiterate in PR description

This ticket is not a live-trading activation. It does not place orders. It does not alter the scanner's candidate selection, score, or tradeability gates. It only adds entry-location semantics and action hints for better interpretation of already produced candidates.
