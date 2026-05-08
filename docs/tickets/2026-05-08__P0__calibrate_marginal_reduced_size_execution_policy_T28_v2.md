# T28: Calibrate Marginal Reduced-Size Execution Policy from Five T27 Shadow-Live Runs

## Metadata

- Ticket ID: T28
- Title: Calibrate Marginal Reduced-Size Execution Policy from Five T27 Shadow-Live Runs
- Status: Draft — ready for preflight review
- Priority: P0
- Language: Implementation and code artifacts in English
- Primary mode affected: Offline analysis / calibration of post-T27 Shadow-Live Daily diagnostics
- Scope type: Analysis + policy-specification ticket; no runtime policy implementation

---

## Authoritative reference set

1. The seven v2.1 specification section files, especially:
   - Abschnitt 6: Daily vs Intraday Update Policy
   - Abschnitt 7: Entry Pattern + Decision Buckets
2. `independence_release_gesamtkonzept_final.md`
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`
4. Current repo reality, especially:
   - `scanner/execution/grading.py`
   - `scanner/pipeline/liquidity.py`
   - `scanner/decision/buckets.py`
   - `scanner/decision/ranking.py`
   - `scanner/output/diagnostics.py`
   - `scanner/config.py` and config defaults
5. Existing implemented contracts from T12, T16, T21, T21.1, T22, T23, T24, T25, T26, and T27.
6. The five T27-capable Shadow-Live Daily ZIP artifacts covering 2026-05-03 through 2026-05-07.
7. The master preflight checklist for Codex-ready tickets.

The seven v2.1 section files remain the primary authority. `independence_release_gesamtkonzept_final.md` is secondary and must be interpreted consistently with the seven section files. This ticket is implementation guidance for an offline calibration analysis and may not override the v2.1 specs or Gesamtkonzept.

---

## Purpose and motivation

T26 showed that execution depth is a material bottleneck but could not calibrate position-size thresholds because raw depth fields were missing from diagnostics. T27 added execution-depth diagnostics, including:

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
```

Five post-T27 Shadow-Live Daily runs now provide enough data for an offline calibration pass.

T28 must answer:

1. Whether `fail` should remain hard-blocked under both the current 20k sizing and the planned 10k sizing scenario.
2. Which `marginal` candidates are reduced-size eligible based on `depth_ratio_band`.
3. How many actionable tradeable candidates exist per day under 20k vs. 10k sizing.
4. Whether spread/slippage introduce additional constraints.
5. Which exact config defaults and operational policy should be recommended for T29 implementation.

T28 must not implement runtime policy changes. It produces a reproducible analysis and a final policy recommendation for T29.

---

## Background: current empirical findings to reproduce

The following findings are based on manual analysis of five T27-capable Shadow-Live Daily runs. They are preliminary and must be reproduced by the T28 analysis script. If the script output differs, the script output is authoritative and the report must explain the discrepancy.

### Aggregate execution status counts across five runs

```text
symbols total:         9,067
execution_attempted:   2,068
marginal:              1,235
fail:                    735
direct_ok:                 50
unknown:                   48
```

### Fail findings

Preliminary findings:

```text
fail total:             735
fail below_min:         735
max fail ratio 20k:     0.02466
max fail ratio 10k:     0.04931
```

Interpretation to verify:

- No fail case reaches `reduced_25` under the current 20k / 200k threshold.
- No fail case reaches `reduced_25` under the planned 10k / 100k threshold.
- Therefore, fail remains hard no-trade for the T28 policy recommendation.

T28 must not simply assume this. It must formally compute and document it.

### Marginal top-bucket findings

Preliminary findings for `marginal` records in `confirmed_candidates` or `early_candidates`:

```text
marginal top-bucket cases: 460

20k basis:
reduced_25+ eligible:  76 / 460 = 16.5%

10k basis:
reduced_25+ eligible: 124 / 460 = 27.0%
```

Interpretation to verify:

- The reduced-size opportunity is concentrated in the `marginal` class.
- `marginal + below_min` should remain observable but not tradeable.
- `marginal + reduced_25/reduced_50/reduced_75/full` should be treated as reduced-size eligible for the policy recommendation.

---

## Scope

### In scope

T28 is an offline analysis and policy-specification ticket.

In scope:

1. Process the five T27-capable Shadow-Live Daily ZIP artifacts.
2. Reproduce or correct the aggregate findings above.
3. Analyze `fail` as a hard-block sanity check only.
4. Analyze `marginal` top-bucket candidates by `depth_ratio_band`.
5. Compare current and target sizing scenarios:
   - current: 20,000 USDT total notional / 200,000 USDT 1% depth threshold
   - target: 10,000 USDT total notional / 100,000 USDT 1% depth threshold
6. Define exact T29 config values for the target 10k policy.
7. Simulate reduced-size candidate classes and position factors.
8. Simulate execution-grade mappings by depth band.
9. Analyze spread and slippage availability/constraints.
10. Produce a final `recommended_policy.md` for T29 implementation.

### Out of scope

T28 must not change runtime behavior.

Out of scope:

- No runtime execution policy change.
- No actual order sizing change.
- No production config default change.
- No `fail -> marginal` promotion.
- No reduced-size trading implementation.
- No order splitting implementation.
- No `tranche_ok` behavior change.
- No production bucket semantic change.
- No live API calls.
- No forward return, MFE, MAE, or profitability conclusion.
- No claim that reduced-size eligible candidates are profitable trades.

---

## Input data

### Required input artifacts

The analysis script must process exactly five T27-capable Shadow-Live Daily ZIP artifacts:

```text
2026-05-03
2026-05-04
2026-05-05
2026-05-06
2026-05-07
```

Each ZIP must contain a Daily `symbol_diagnostics.jsonl.gz` file.

### Daily diagnostics selection

The script must select only Daily diagnostics:

```text
reports/runs/YYYY/MM/DD/daily-*/symbol_diagnostics.jsonl.gz
```

It must not select Intraday diagnostics:

```text
reports/runs/YYYY/MM/DD/intraday-*/symbol_diagnostics.jsonl.gz
```

### Archive validation

For each expected date, the script must:

1. Locate exactly one Daily diagnostics file.
2. Fail clearly if the date is missing.
3. Fail clearly if multiple Daily diagnostics files are found for the same date unless a deterministic run-id selection rule is explicitly implemented and reported.
4. Count records after loading.
5. Fail if `record_count == 0`.
6. Include selected ZIP filename and internal diagnostics path in the output report.

---

## Required field extraction

T28 must read T27 top-level diagnostic fields. T28 must not expect a nested `execution` object.

Required top-level fields:

```text
symbol
execution_attempted
execution_status_raw
execution_reason_raw
execution_pass
execution_grade_t16
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
```

Decision/state/pattern fields may exist top-level or nested depending on current diagnostics schema. The script must use robust extraction with documented precedence:

```text
decision_bucket:
  record["decision"]["decision_bucket"] first if present
  else record["decision_bucket"]

priority_score:
  record["decision"]["priority_score"] first if present
  else record["priority_score"]

entry_pattern:
  record["decision"]["entry_pattern"] first if present
  else record["pattern"]["entry_pattern"]
  else record["entry_pattern"]

entry_pattern_score:
  record["decision"]["entry_pattern_score"] first if present
  else record["pattern"]["entry_pattern_score"]
  else record["entry_pattern_score"]

state_machine_state:
  record["state"]["state_machine_state"] first if present
  else record["state_machine_state"]

state_confidence:
  record["state"]["state_confidence"] first if present
  else record["state_confidence"]

market_phase:
  record["phase"]["market_phase"] first if present
  else record["market_phase"]

market_phase_confidence:
  record["phase"]["market_phase_confidence"] first if present
  else record["market_phase_confidence"]
```

If a required analysis field is missing for a record, the record must remain in the full export with derivability flags rather than silently disappearing.

---

## Sizing scenarios

T28 must compare two sizing scenarios.

### Scenario A — current 20k basis

```text
scenario_id = "current_20k"
notional_total_usdt = 20_000
notional_chunk_usdt = 5_000
max_tranches = 4
depth_buffer_multiple = 10
depth_threshold_1pct_usdt = 200_000
```

### Scenario B — target 10k basis

```text
scenario_id = "target_10k"
notional_total_usdt = 10_000
notional_chunk_usdt = 5_000
max_tranches = 2
depth_buffer_multiple = 10
depth_threshold_1pct_usdt = 100_000
```

The 10k values are the intended target defaults for T29 implementation if T28 confirms no blocking evidence.

### No hard-coding rule

The script must not hard-code these values throughout the logic. It must define them in one central scenario configuration block, e.g.:

```python
SCENARIOS = {
    "current_20k": {
        "notional_total_usdt": 20_000.0,
        "notional_chunk_usdt": 5_000.0,
        "max_tranches": 4,
        "depth_buffer_multiple": 10.0,
    },
    "target_10k": {
        "notional_total_usdt": 10_000.0,
        "notional_chunk_usdt": 5_000.0,
        "max_tranches": 2,
        "depth_buffer_multiple": 10.0,
    },
}
```

For each scenario:

```text
scenario_depth_threshold_1pct_usdt = notional_total_usdt * depth_buffer_multiple
scenario_available_depth_ratio = available_depth_1pct_usdt / scenario_depth_threshold_1pct_usdt
```

If `available_depth_1pct_usdt` is missing/non-finite or `scenario_depth_threshold_1pct_usdt <= 0`, scenario ratio is `null`.

---

## Depth band mapping per scenario

T28 must compute scenario-specific depth bands rather than relying only on the recorded T27 `depth_ratio_band`, because T27 was emitted under the then-active threshold.

### Scenario depth band enum

Allowed values:

```text
full
reduced_75
reduced_50
reduced_25
below_min
not_evaluable
```

### Mapping

```text
if scenario_available_depth_ratio is null:
    scenario_depth_ratio_band = "not_evaluable"

elif scenario_available_depth_ratio >= 1.00:
    scenario_depth_ratio_band = "full"

elif scenario_available_depth_ratio >= 0.75:
    scenario_depth_ratio_band = "reduced_75"

elif scenario_available_depth_ratio >= 0.50:
    scenario_depth_ratio_band = "reduced_50"

elif scenario_available_depth_ratio >= 0.25:
    scenario_depth_ratio_band = "reduced_25"

else:
    scenario_depth_ratio_band = "below_min"
```

### Scenario recommended position factor

Allowed values:

```text
1.00
0.75
0.50
0.25
0.00
null
```

Mapping:

```text
full          -> 1.00
reduced_75    -> 0.75
reduced_50    -> 0.50
reduced_25    -> 0.25
below_min     -> 0.00
not_evaluable -> null
```

This is analysis-only in T28. It must not be used for runtime sizing.

---

## Fail-class sanity check

T28 does not calibrate reduced-size trading for `fail`.

However, it must formally prove the exclusion for the five-run dataset.

### Required fail analysis

For all records with:

```text
execution_status_raw = "fail"
```

compute for each scenario:

```text
scenario_available_depth_ratio
scenario_depth_ratio_band
scenario_recommended_position_factor
```

Required summary:

```text
fail_count
fail_count_by_day
fail_ratio_min
fail_ratio_median
fail_ratio_p75
fail_ratio_max
fail_count_reaching_reduced_25_current_20k
fail_count_reaching_reduced_25_target_10k
max_fail_ratio_target_10k
```

### Explicit decision rule

A fail case would reach reduced-size eligibility under the target 10k scenario only if:

```text
available_depth_1pct_usdt / 100_000 >= 0.25
```

Equivalent:

```text
available_depth_1pct_usdt >= 25_000
```

T28 must compute and report whether any fail case meets this threshold.

Expected result from preliminary analysis:

```text
fail_count_reaching_reduced_25_target_10k = 0
```

If this result is not zero, T28 must not silently recommend fail exclusion. It must report the exception symbols and mark the fail policy recommendation as requiring manual review.

### Fail policy recommendation wording

T28 must not use absolute wording such as “fail is permanently excluded”.

Required wording:

```text
Based on the five T27-capable runs, fail remains out of scope for reduced-size execution and should stay hard-blocked in the T29 policy proposal. This is because no fail record reaches reduced_25 under the target 10k scenario.
```

---

## Marginal-class analysis

T28’s primary focus is the `marginal` class.

### Target population

Primary target records:

```text
execution_status_raw = "marginal"
decision_bucket in {"confirmed_candidates", "early_candidates"}
```

These are called:

```text
marginal_top_bucket_candidates
```

Records with `execution_status_raw = "unknown"` are excluded from all marginal and fail analyses. They must still be counted per day in `run_input_manifest.md` and `candidate_availability_by_day.md`, including the bucket distribution if available. Unknown must not be treated as marginal, fail, or reduced-size eligible.

### Required classification per scenario

For every marginal top-bucket candidate and every scenario compute:

```text
scenario_available_depth_ratio
scenario_depth_ratio_band
scenario_recommended_position_factor
scenario_tradeability_class
```

Allowed values for `scenario_tradeability_class`:

```text
full
reduced_75
reduced_50
reduced_25
observe_only
not_evaluable
```

Mapping:

```text
full          -> "full"
reduced_75    -> "reduced_75"
reduced_50    -> "reduced_50"
reduced_25    -> "reduced_25"
below_min     -> "observe_only"
not_evaluable -> "not_evaluable"
```

Reduced-size eligible means:

```text
scenario_tradeability_class in {"full", "reduced_75", "reduced_50", "reduced_25"}
```

Not tradeable but still visible:

```text
scenario_tradeability_class = "observe_only"
```

Not safely evaluable:

```text
scenario_tradeability_class = "not_evaluable"
```

### Required marginal summaries

For each scenario:

```text
marginal_top_bucket_count
count_by_day
count_by_bucket
count_by_scenario_tradeability_class
eligible_count
eligible_share
observe_only_count
not_evaluable_count
recurring_symbols_eligible_3plus_days
recurring_symbols_eligible_2plus_days
```

Also summarize by:

```text
market_phase
entry_pattern
state_machine_state
depth_side_used
```

`depth_side_used` is a diagnostic consistency check. T28 does not make a policy decision from bid/ask/combined side selection, but it must summarize the distribution for marginal top-bucket candidates so that unexpected side usage is visible before T29.

---

## Spread and slippage analysis

Spread remains an execution constraint. Slippage is only partially available and must be treated cautiously.

### Spread fields

Use:

```text
spread_pct
```

For each scenario and tradeability class, report:

```text
spread_count_derivable
spread_missing_count
spread_min
spread_median
spread_p75
spread_p90
spread_max
```

### Spread threshold sensitivity

T28 must not change the production spread threshold. It must run sensitivity summaries for these candidate thresholds:

```text
0.05%
0.10%
0.15%
0.20%
0.30%
```

For each threshold, report how many reduced-size eligible marginal top-bucket candidates would remain.

This is analysis-only.

### Slippage fields

Use:

```text
estimated_slippage_bps
```

This field is expected to be in basis points. If a diagnostics record or future schema exposes slippage in another unit, T28 must convert it to basis points before aggregation. If the unit cannot be determined, mark the value as non-derivable for T28 and document the gap rather than mixing units.

Required summary:

```text
slippage_derivable_count
slippage_missing_count
slippage_derivable_share
slippage_median_if_derivable
slippage_p75_if_derivable
```

If slippage is missing for a record, do not infer it as good or bad.

### Slippage policy recommendation

T28 must recommend that T29 uses the existing full-trade slippage threshold for reduced-size candidates unless a stronger evidence-based reason is found.

Required limitation:

```text
Slippage data is only partially available. T28 does not justify loosening slippage thresholds for reduced-size candidates.
```

---

## Execution-grade mapping sensitivity

Current `marginal` uses `execution_grade_t16 = 40.0`. T26 showed that this creates a substantial rank penalty. T28 must simulate alternative grade mappings by scenario tradeability class.

### Candidate mappings

T28 must simulate at least these three mappings.

#### Mapping A — conservative

```text
full:          75
reduced_75:    70
reduced_50:    60
reduced_25:    45
observe_only:  20
not_evaluable: 0
```

#### Mapping B — balanced

```text
full:          85
reduced_75:    75
reduced_50:    60
reduced_25:    40
observe_only:  20
not_evaluable: 0
```

#### Mapping C — strict tradeable-only

```text
full:          85
reduced_75:    75
reduced_50:    60
reduced_25:    40
observe_only:  0
not_evaluable: 0
```

These mappings are analysis-only. T28 must recommend one mapping for T29 or state that the data is insufficient.

### Score formula

Use the existing T12 priority-score formula unless current repo reality has a canonical helper that must be reused.

If using formula directly:

```text
priority_score = 0.30 * market_phase_confidence
               + 0.35 * state_confidence
               + 0.20 * entry_pattern_score
               + 0.15 * execution_grade_simulated
```

`execution_grade_simulated` is the value from the mapping table being tested for the candidate's scenario tradeability class. It is not the raw diagnostics field `execution_grade_t16`. `execution_grade_t16` is read in T28 only to verify the current observed state and baseline behavior; it must not be used as the input for the simulated mapping formula unless the baseline/current mapping is explicitly being reproduced.

If any score component is missing or non-finite, mark `score_replay_derivable = False` and exclude the record from rank-displacement analysis while keeping it in full exports.

Non-finite values must not be coerced to zero.

### Ranking population

Rank simulations must use the full same-day same-bucket population, not only marginal candidates.

For each target marginal candidate:

1. Keep all other symbols in the same date + bucket ranking population.
2. Replace only the target symbol’s execution grade according to the mapping being tested.
3. Recompute only the target symbol’s priority score.
4. Re-sort the full bucket population.
5. Compute rank displacement.

Sort rule:

```text
priority_score descending
symbol ascending as deterministic tie-breaker
```

If T12 defines a different canonical tie-breaker in current repo code, reuse it and document it.

### Required ranking outputs

For each mapping and scenario:

```text
mean_rank_displacement
median_rank_displacement
count_improved_5plus_ranks
count_improved_10plus_ranks
count_no_change
count_worse
```

Negative rank displacement means better rank.

---

## Candidate availability / weak-day analysis

T28 must document operational candidate availability.

For each day and each scenario:

```text
direct_ok_top_bucket_count
marginal_reduced_eligible_top_bucket_count
combined_tradeable_top_bucket_count
combined_tradeable_top_bucket_count_after_spread_thresholds
```

T28 must explicitly flag days where:

```text
combined_tradeable_top_bucket_count < 5
```

T28 does not need to define a fallback strategy for weak days. It only documents the frequency and severity of weak candidate days.

---

## Recurring symbol analysis

For each scenario, compute symbols that are reduced-size eligible marginal top-bucket candidates on multiple days.

Required outputs:

```text
symbols_eligible_2plus_days
symbols_eligible_3plus_days
symbols_eligible_4plus_days
symbols_eligible_5_days
```

For each recurring symbol include:

```text
symbol
days_present
buckets_seen
median_scenario_available_depth_ratio
best_scenario_depth_ratio_band
median_spread_pct
market_phases_seen
entry_patterns_seen
```

Preliminary expected recurring symbols include:

```text
ETCUSDT
TONUSDT
PENDLEUSDT
ONDOUSDT
LINKUSDT
```

The script output is authoritative.

---

## Config recommendation for T29

T28 must produce exact recommended config values for T29.

Expected target recommendation unless contradicted by the script output:

```yaml
execution:
  notional_total_usdt: 10000
  notional_chunk_usdt: 5000
  max_tranches: 2
  depth_buffer_multiple: 10
  min_depth_1pct_usd: 100000
```

### Config centrality requirement for T29 recommendation

T28 must recommend that T29 centralizes sizing configuration. T29 should not scatter these values across execution, diagnostics, reports, and analysis scripts.

Preferred long-term invariant:

```text
min_depth_1pct_usd = notional_total_usdt * depth_buffer_multiple
```

If current repo reality cannot derive `min_depth_1pct_usd` from `notional_total_usdt * depth_buffer_multiple`, T28 must recommend one of:

1. Add derived threshold support in T29, or
2. Keep explicit `min_depth_1pct_usd` but add validation/warning that it equals `notional_total_usdt * depth_buffer_multiple` unless explicitly overridden.

Partial config overrides must be field-wise merged with central defaults; missing subkeys must not invalidate the entire config block unless current config architecture explicitly requires full-block replacement.

---

## Recommended T29 policy contract

T28 must produce a final recommended contract for T29. It should use this shape unless the analysis shows a reason to alter it.

### Runtime status semantics

Do not change existing `execution_status_raw` enum semantics in T29 unless explicitly justified.

Recommended interpretation:

```text
direct_ok:
  full-size tradeable

tranche_ok:
  existing behavior unchanged; no order-splitting extension in T29

marginal:
  split by execution_size_class / recommended_position_factor

fail:
  hard no-trade

unknown:
  no trade / not safely evaluable
```

### New operational fields for T29

Recommended fields:

```text
execution_size_class
recommended_position_factor
```

Allowed `execution_size_class` values:

```text
full
reduced_75
reduced_50
reduced_25
observe_only
blocked
not_evaluable
```

Recommended mapping:

```text
direct_ok -> full
tranche_ok -> full or existing tranche class, unchanged unless current contract already distinguishes it
marginal + scenario_depth_ratio_band full -> full
marginal + scenario_depth_ratio_band reduced_75 -> reduced_75
marginal + scenario_depth_ratio_band reduced_50 -> reduced_50
marginal + scenario_depth_ratio_band reduced_25 -> reduced_25
marginal + scenario_depth_ratio_band below_min -> observe_only
marginal + scenario_depth_ratio_band not_evaluable -> not_evaluable
fail -> blocked
unknown -> not_evaluable
not_attempted -> not_evaluable or null, to be decided by T29 based on existing diagnostics conventions
```

Clarification: `execution_size_class = "full"` for a `marginal` record means the measured depth is sufficient for a full position under the scenario threshold, but `execution_status_raw` remains `marginal` because other execution-quality metrics placed it below `direct_ok`. T29 must preserve both fields: `execution_size_class` governs sizing/tradeability classification, while `execution_status_raw` remains the canonical execution outcome.

Recommended `recommended_position_factor` mapping:

```text
full -> 1.00
reduced_75 -> 0.75
reduced_50 -> 0.50
reduced_25 -> 0.25
observe_only -> 0.00
blocked -> 0.00
not_evaluable -> null
```

### Bucket/report recommendation

T28 must recommend how T29 should handle `marginal + below_min` in reports.

Default recommendation:

```text
Do not remove marginal + below_min from structural buckets in T29.
Keep them visible in reports, but clearly mark them as execution_size_class = observe_only and not tradeable.
```

This preserves signal visibility while preventing false tradeability.

---

## Output artifacts

The T28 script must write outputs under:

```text
reports/aux/reduced_size_policy_calibration/2026-05-03_to_2026-05-07/
```

Required output files:

| File | Content |
|---|---|
| `run_input_manifest.md` | Dates, ZIP names, selected diagnostics paths, per-day record counts |
| `fail_sanity_check.md` | Fail-class proof and 10k reduced_25 exclusion |
| `marginal_band_distribution.md` | Marginal top-bucket distribution by scenario, band, and `depth_side_used` |
| `scenario_20k_vs_10k_summary.md` | Current vs target sizing comparison |
| `spread_slippage_by_band.md` | Spread/slippage availability and threshold sensitivity |
| `grade_mapping_sensitivity.md` | Execution-grade and rank-displacement simulations |
| `candidate_availability_by_day.md` | Direct + reduced marginal candidate counts per day |
| `recurring_symbols.md` | Recurring eligible symbols across runs |
| `recommended_policy.md` | Final T29 policy recommendation with exact config values |
| `marginal_candidates_full.jsonl` | One record per marginal top-bucket candidate per scenario |
| `fail_sanity_full.jsonl` | One record per fail case per scenario |

---

## Output path safety

The script must validate the output root before writing.

Allowed canonical output root:

```text
reports/aux/reduced_size_policy_calibration/2026-05-03_to_2026-05-07/
```

The script must reject output paths under:

```text
reports/runs/**
reports/daily/**
reports/index/**
snapshots/runs/**
reports/analysis/**
```

Resolve/normalize paths before validation to prevent bypasses via `..` or relative path tricks. If output root is unsafe, fail before writing any files.

---

## Numeric robustness

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid / not evaluable inputs and must not be emitted as numeric-looking outputs.

Rules:

- `None`, missing keys, `NaN`, `inf`, `-inf` must result in `null` for derived numeric diagnostic fields.
- Division by zero or negative thresholds must result in scenario ratio `null`.
- Missing spread/slippage must not be interpreted as zero.
- Missing depth must not be interpreted as zero.
- `null` means not safely evaluable and must not be coerced to `false` or `0.0`.

---

## Determinism

The analysis must be deterministic.

Required invariant:

```text
With identical input artifacts and identical scenario config, output records, sorting, ranks, summaries, and recommendation tables are identical.
```

Sorting rules:

- Dates ascending.
- Symbols ascending for stable tie-breaks.
- Candidate ranking simulations use canonical T12 tie-breaker if available; otherwise `priority_score desc`, then `symbol asc`.
- Dict/set iteration order must not affect outputs.

---

## Tests

Add or update tests for the T28 analysis script.

### Archive selection tests

- Select Daily diagnostics, not Intraday diagnostics.
- Fail when an expected date is missing.
- Fail when selected Daily diagnostics has zero records.
- Include selected ZIP/internal path in input manifest.

### Scenario mapping tests

- Ratio `>= 1.0` maps to `full` and factor `1.0`.
- Ratio `0.75..1.0` maps to `reduced_75` and factor `0.75`.
- Ratio `0.50..0.75` maps to `reduced_50` and factor `0.50`.
- Ratio `0.25..0.50` maps to `reduced_25` and factor `0.25`.
- Ratio `< 0.25` maps to `below_min` / `observe_only` and factor `0.0` for marginal.
- Missing depth maps to `not_evaluable` and factor `null`.

### Fail sanity tests

- Fail case with `available_depth_1pct_usdt = 24_999` under target 10k remains below `reduced_25`.
- Fail case with `available_depth_1pct_usdt = 25_000` under target 10k reaches `reduced_25` and triggers manual-review flag.
- Fail recommendation is not silently hard-coded when a fail reaches `reduced_25`.

### Marginal classification tests

- `unknown` records are excluded from marginal/fail analysis populations but counted in per-day summaries.
- `marginal + reduced_25` in `confirmed_candidates` is reduced-size eligible.
- `marginal + below_min` in `confirmed_candidates` is observe-only, not eligible.
- `marginal + not_evaluable` is not eligible.
- Non-top-bucket marginal records are excluded from the primary marginal top-bucket population but may be counted in supplemental summaries.
- `depth_side_used` values are summarized without affecting tradeability classification.

### Spread/slippage tests

- Missing spread is counted as missing, not zero.
- Threshold sensitivity counts only records with derivable spread unless explicitly documented otherwise.
- Missing slippage does not pass or fail slippage checks.

### Ranking simulation tests

- Rank simulations use full same-day same-bucket population.
- Only target candidate score changes in counterfactual rank simulation.
- Deterministic tie-breaker applies.
- Missing/non-finite score components produce `score_replay_derivable = False`.

### Output safety tests

- Canonical output path accepted.
- `reports/runs/**` rejected.
- `reports/daily/**` rejected.
- `reports/index/**` rejected.
- `snapshots/runs/**` rejected.
- `reports/analysis/**` rejected.
- Path traversal into forbidden paths rejected.
- No partial files written after validation failure.

---

## Acceptance criteria

- [ ] The script processes exactly the five expected T27-capable Daily runs.
- [ ] Daily diagnostics are selected; Intraday diagnostics are not selected.
- [ ] Input manifest lists selected ZIP and diagnostics path for each date.
- [ ] Fail sanity check computes 20k and 10k scenario ratios for all fail records.
- [ ] The report explicitly states whether any fail reaches `reduced_25` under target 10k.
- [ ] If any fail reaches `reduced_25`, `recommended_policy.md` marks fail policy as manual-review-required.
- [ ] Marginal top-bucket candidates are classified by scenario tradeability class.
- [ ] 20k vs 10k scenario summary is produced.
- [ ] Spread/slippage summaries and spread-threshold sensitivity are produced.
- [ ] Execution-grade mapping sensitivity is produced with full bucket population rank simulation.
- [ ] Candidate availability by day is produced and days with fewer than 5 tradeable candidates are flagged.
- [ ] `unknown` records are excluded from fail/marginal analyses but counted per day in manifest and candidate availability outputs.
- [ ] `depth_side_used` distribution is summarized for marginal top-bucket candidates.
- [ ] Recurring eligible symbols are reported.
- [ ] `recommended_policy.md` includes exact target config values for T29.
- [ ] `recommended_policy.md` states that T28 does not prove profitability.
- [ ] Output files are written only under the canonical `reports/aux/...` path or another validated safe path.
- [ ] No runtime scanner behavior is changed.
- [ ] No production config defaults are changed.
- [ ] No execution status semantics are changed.
- [ ] No bucket rules are changed in production.
- [ ] No live external API calls are made.

---

## Invariants

- T28 is offline-only.
- T28 is analysis + policy recommendation only.
- T28 must not change runtime scanner behavior.
- T28 must not change execution status semantics.
- T28 must not change bucket rules.
- T28 must not change order sizing.
- T28 must not implement reduced-size trading.
- T28 must not promote fail to marginal.
- T28 must keep missing, not evaluated, failed, marginal, and unknown states distinct.
- T28 must preserve current T12/T16 semantics.
- T28 output must be reproducible from the five input ZIP artifacts.

---

## Required limitations section in `recommended_policy.md`

`recommended_policy.md` must include these limitations:

1. **No profitability conclusion.** T28 does not evaluate forward returns, MFE, MAE, or realized trade performance.
2. **Five-run sample.** The analysis uses five T27-capable Shadow-Live Daily runs. It is sufficient for first policy calibration but should be revisited after more runs.
3. **Slippage partial availability.** Slippage is not available for all records. Missing slippage must not be interpreted as good execution.
4. **No fail policy generalization beyond current evidence.** Fail remains hard-blocked for T29 based on current evidence; future materially different liquidity regimes may warrant re-analysis.
5. **No order-splitting change.** T28 does not evaluate or modify `tranche_ok` or order-splitting behavior.

---

## Follow-on ticket

T28 should prepare T29:

```text
T29: Implement Marginal Reduced-Size Execution Policy
```

Expected T29 scope, subject to T28 output:

- Apply exact target config defaults.
- Centralize sizing config and threshold derivation/validation.
- Introduce operational `execution_size_class`.
- Introduce operational `recommended_position_factor`.
- Keep `marginal + below_min` visible but non-tradeable.
- Keep `fail` hard no-trade.
- Apply selected execution-grade mapping by class.
- Extend report/diagnostics to show tradeability class and position factor.
- Keep `tranche_ok` behavior unchanged.

