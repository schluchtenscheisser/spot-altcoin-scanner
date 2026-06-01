# T30-v2: Segment Selection Forward-Return Analysis (ir1.5+ Basis)

## Metadata

- Ticket ID: T30-v2
- Title: Segment Selection Forward-Return Analysis — Pilot Basket Calibration
- Status: v3 — Codex-ready
- Priority: P1
- Language: Implementation and code artifacts in English
- Primary mode affected: Offline analysis of ir1.5+ Shadow-Live Daily artifacts
- Scope type: Analysis ticket; no runtime policy implementation
- Minimum data prerequisite: 20 ir1.5+ Shadow-Live Daily runs accumulated
- Predecessor: T30-v1 / T30-v1.1 (forward-return framework; see feature_enhancements.md Enhancement 3)
- Changelog:
  - v1→v2: Fixed entry_location nested extraction; added schema_version fallback; S6 buy_now invariant; OHLCV prerequisite step
  - v2→v3: ir1.5+ detection changed to semantic version comparison (>= ir1.5); S6/S8 inconsistency fixed, S9 reference segment added; Basket C clarified as independent filter definition, not segment union; tranche_ok handling made explicit; Basket A/B clarified as independent filter definitions; report.json cross-validation operationalized; Cross-breakdown 1 expanded to pre-filter population; config validation added; required tests section added; Breakdown 4 phase terminology corrected to v2.1 values

---

## Authoritative reference set

1. The seven v2.1 specification section files, especially:
   - Abschnitt 7: Entry Pattern + Decision Buckets
2. `independence_release_gesamtkonzept_final.md`
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`
4. Current repo reality, especially:
   - `scanner/output/diagnostics.py` (field schema for `symbol_diagnostics.jsonl.gz`)
   - `scanner/output/report_builder.py` and `docs/canonical/REPORTS.md`
   - `scanner/config.py` and central config defaults (position size, depth thresholds)
   - `scripts/` (existing T25/T28/T30 analysis script patterns)
   - T29 execution semantics (codex_instruction_document_t29_diagnostics_semantics.md)
5. Existing implemented contracts from T12, T16, T21, T21.1, T22, T23, T24, T25, T26, T27, T28, T29, T_EL2.
6. `open_questions.md` — especially Q5 (dual meaning of `execution_size_class = "full"`), Q6 (`is_reduced_size_eligible` naming).
7. `feature_enhancements.md` — especially Enhancement 3 (T30 forward returns), Enhancement 4 (overextension marker, explicitly out of scope here).
8. The master preflight checklist for Codex-ready tickets.

The seven v2.1 section files remain the primary authority. This ticket is implementation guidance for an offline analysis script and must not override the v2.1 specs or Gesamtkonzept.

---

## Purpose and motivation

T30-v1 and T30-v1.1 established the forward-return evaluation framework and produced preliminary findings on a pre-ir1.5 run base. The key limitation was that `is_operational_trade_candidate` was unavailable for approximately 91% of events, making segment-level return comparisons unreliable.

T30-v2 uses the accumulated ir1.5+ run base, where:

- `is_operational_trade_candidate` is consistently populated
- `execution_size_class` and `recommended_position_factor` are operational (post-T29)
- `entry_action_hint` and `entry_location_status` are operational (post-T_EL2)
- `candidate_excluded` is a reliable top-level field (post-Q1/Q2 resolution)

The central question T30-v2 must answer is:

> Which combination of `decision_bucket`, `execution_size_class`, and `entry_action_hint` produces sufficient trading frequency, acceptable realized slippage-adjusted returns, and manageable adverse excursion to justify inclusion in the live pilot basket?

T30-v2 does not make the final basket decision. It produces structured, segment-level evidence against which the three pre-defined pilot basket hypotheses (Baskets A, B, C) are evaluated.

---

## Non-goals / out of scope

The following are explicitly excluded from this ticket:

- No runtime scanner changes of any kind.
- No changes to execution grading, bucket assignment, ranking, or config defaults.
- No live API calls or MEXC data fetches.
- No intraday-promotion-event analysis (Q4 scope).
- No overextension marker implementation (feature_enhancements.md Enhancement 4).
- No terminal-event forward returns (feature_enhancements.md Enhancement 9).
- No schema cleanup for Q5 or Q6 (analysis must read fields as-is with documented dual-meaning handling).
- No new diagnostics fields added to `symbol_diagnostics.jsonl.gz`.
- No changes to T18 Evaluation Replay mechanics.
- No trading decisions, position sizing, or exit strategy logic.
- No conclusion about `max_new_positions_per_run` (this is trading policy, not scanner output).

---

## Prerequisites

Before running the analysis script, OHLCV history must be available locally for the symbols and date ranges covered by the ir1.5+ runs. This is required for forward-return computation. The analysis script does not perform OHLCV fetching itself.

### Required prerequisite step

Run the existing OHLCV fetch script against the ir1.5+ run date range before executing T30-v2:

```bash
python scripts/fetch_ohlcv_history_for_evaluation.py --project-root .
```

This script fetches daily OHLCV data for all symbols appearing in the accumulated Shadow-Live diagnostics and writes it to the canonical Parquet history path used by T18.

### Behavior when OHLCV is absent

If the fetch step was skipped or OHLCV coverage is incomplete, the analysis script must:

1. Continue without error.
2. Produce frequency metrics (segment counts, basket projections) for all records.
3. Set `forward_return_derivable = false` for records with missing OHLCV coverage.
4. Prominently warn in `run_coverage.md` and `decision_support.md`:

```text
WARNING: OHLCV history absent or incomplete for [N] symbols.
Forward-return metrics are unavailable or partial.
Run scripts/fetch_ohlcv_history_for_evaluation.py before re-running this script.
```

The script must not silently produce an apparently valid empty evaluation. Frequency outputs remain valid without OHLCV; return outputs require it.

---

## Input data contract

### Primary input: ir1.5+ `symbol_diagnostics.jsonl.gz`

T30-v2 reads from accumulated `symbol_diagnostics.jsonl.gz` files across ir1.5+ Shadow-Live Daily runs.

### ir1.5+ run identification

The script must identify and reject any runs predating the ir1.5 schema. Version identification uses semantic comparison, not string equality.

**Step 1 — schema_version field (primary):**

```text
A run is ir1.5+ if at least one diagnostics record has a `schema_version`
field that parses as an Independence Release schema version >= ir1.5.

Accepted examples: "ir1.5", "ir1.6", "ir2.0"
Rejected examples: "ir1.4", "ir1.3", "ir1.2"

Parsing rule: strip the leading "ir" prefix, parse the remainder as a
comparable version tuple (major.minor). A value of "ir1.5" → (1, 5).
Comparison: parsed version >= (1, 5).

If schema_version is present but parses below ir1.5, exclude the run
with reason `schema_pre_ir1.5`.

If schema_version cannot be parsed (unexpected format), log a warning
and fall through to Step 2.
```

**Step 2 — is_operational_trade_candidate fallback:**

```text
If no parseable schema_version is available for a run — either because
schema_version is absent from all records, or because all present
schema_version values are unparseable — fall back to: a run is ir1.5+
if `is_operational_trade_candidate` is present as a non-null top-level
field for at least one record.
```

**Required field check for higher schema versions:**

If a run is accepted via Step 1 with a schema version > ir1.5, the script must verify that the following T30-v2 required fields are present for at least one record before including the run:

```text
is_operational_trade_candidate
execution_size_class
execution_status_raw
entry_location (block)
```

If required fields are missing despite a qualifying schema version, exclude the run with reason `missing_required_fields` and log to `run_coverage.json`.

**Minimum run count:**

If fewer than 20 ir1.5+ runs are available at execution time, the script must exit with a clear error message:

```text
T30-v2 requires at least 20 ir1.5+ runs. Found: {n}. Accumulate more runs and retry.
```

### Secondary input: report.json (T24 execution-aware segments)

T30-v2 reads daily `report.json` candidate counts from `reports/runs/` as a cross-validation source. It must not reconstruct bucket populations from `report.json` alone; diagnostics remain the primary source.

**Cross-validation behavior:**

For each included run, compare the diagnostics-derived `confirmed_candidates` and `early_candidates` counts against the corresponding counts in `report.json` execution-aware segments where those fields exist.

If counts differ by more than a configurable tolerance (default: 0 — exact match expected):

- Do not fail the analysis.
- Write the mismatch to `run_coverage.json` under `cross_validation_mismatches`.
- Include a warning table in `run_coverage.md`.

If `report.json` is missing for a run:

- Continue with diagnostics-only mode.
- Mark `report_cross_validation_available = false` for that run in `run_coverage.json`.

### Tertiary input: OHLCV data (forward return computation)

Forward returns are computed from Parquet OHLCV history per T18 reference-price semantics. See "Forward Return Computation" section below. OHLCV data must be fetched via the prerequisite step described above.

---

## Field extraction contract

All fields must be extracted from `symbol_diagnostics.jsonl.gz` using robust nested-field access with the following documented precedence. This precedence pattern is established by T28 and must be preserved consistently.

### Operational tradeability fields (top-level)

These fields are top-level in ir1.5+ diagnostics. Do not look under nested dicts.

```text
symbol                          top-level
run_date                        top-level (derive from file path if absent)
schema_version                  top-level
is_operational_trade_candidate  top-level
is_tradeable_candidate          top-level
candidate_excluded              top-level
execution_size_class            top-level
recommended_position_factor     top-level
execution_status_raw            top-level
execution_grade_effective       top-level
spread_pct                      top-level
estimated_slippage_bps          top-level
depth_ratio_band                top-level
available_depth_ratio           top-level
```

### Decision / ranking fields (nested with fallback)

```text
decision_bucket:
  record["decision"]["decision_bucket"]  if present
  else record["decision_bucket"]

priority_score:
  record["decision"]["priority_score"]   if present
  else record["priority_score"]

entry_pattern:
  record["decision"]["entry_pattern"]    if present
  else record["pattern"]["entry_pattern"] if present
  else record["entry_pattern"]

entry_pattern_score:
  record["decision"]["entry_pattern_score"]    if present
  else record["pattern"]["entry_pattern_score"] if present
  else record["entry_pattern_score"]
```

### Phase / state fields (nested with fallback)

```text
market_phase:
  record["phase"]["market_phase"]            if present
  else record["market_phase"]

market_phase_confidence:
  record["phase"]["market_phase_confidence"] if present
  else record["market_phase_confidence"]

state_machine_state:
  record["state"]["state_machine_state"]     if present
  else record["state_machine_state"]

state_confidence:
  record["state"]["state_confidence"]        if present
  else record["state_confidence"]
```

### Entry location fields (nested under `entry_location` block)

Entry location fields are nested under the `entry_location` block in ir1.5+ diagnostics. They are **not** top-level fields. Do not attempt to read them directly from the record root.

```text
entry_location_status:
  record["entry_location"]["entry_location_status"]  if record["entry_location"] present
  else "not_evaluable"

entry_action_hint:
  record["entry_location"]["entry_action_hint"]  if record["entry_location"] present
  else "not_evaluable"
```

If the `entry_location` block is absent entirely (pre-T_EL2 records that slip through the ir1.5 filter), both fields must be set to `"not_evaluable"`. Such records are excluded from all entry-location breakdowns (Breakdown 2) but retained in frequency and return statistics where other fields qualify them.

### tranche_ok handling

Per T29 policy, `execution_status_raw = "tranche_ok"` maps to `execution_size_class = "full"` and `recommended_position_factor = 1.00`. This means `tranche_ok` records satisfy the `execution_size_class = "full"` condition used in basket filters and in reference segments S8/S9. They do not satisfy segments that additionally filter on a specific `execution_status_raw` value (S1/S2 require `direct_ok`; S7 requires `marginal`).

`tranche_ok` records must not be silently merged into `direct_ok` in any output. In all breakdown tables and segment outputs, `execution_status_raw` must always be reported alongside `execution_size_class` so that `direct_ok + full` and `tranche_ok + full` remain distinguishable in the data. Segment membership is determined by `execution_size_class`; `execution_status_raw` is a diagnostic visibility field in outputs.

If `tranche_ok` records are present in the population, they must appear as a distinct `execution_status_raw` value in Cross-breakdown 1 and in `run_coverage.json`.

### Q5 dual-meaning handling

`execution_size_class = "full"` occurs in three distinct scenarios:

1. `execution_status_raw = "direct_ok"` — all execution metrics passed, full depth.
2. `execution_status_raw = "tranche_ok"` — existing tranche execution behavior, full depth.
3. `execution_status_raw = "marginal"` — full depth, but at least one execution quality metric prevented `direct_ok`.

The analysis must always read both `execution_size_class` and `execution_status_raw` together. All segment definitions must specify which combination is intended. The analysis must never use `execution_size_class` alone as a proxy for execution quality.

---

## Segment definitions

### Design principle: segments vs. baskets

Primary segments (S1–S9) are analytical units used to produce per-group return and frequency statistics. They are not required to be exhaustive or mutually exclusive with respect to basket definitions.

Baskets (A, B, C) are pilot hypothesis filters defined independently of segment boundaries. A basket may include records that fall in multiple segments, in no named segment, or at the intersection of segments. The relationship between a basket and its constituent segments is documented explicitly below for transparency, but baskets are not defined as segment unions.

### Primary analysis segments

All segments require as baseline:

```text
is_operational_trade_candidate = true
candidate_excluded = false (or absent / null treated as false)
execution_size_class NOT IN {observe_only, blocked, not_evaluable, not_evaluated}
```

| Segment ID | Label | `decision_bucket` | `execution_status_raw` | `execution_size_class` | `entry_action_hint` |
|---|---|---|---|---|---|
| S1 | confirmed · direct_ok · buy_now | confirmed_candidates | direct_ok | full | buy_now_candidate |
| S2 | confirmed · direct_ok · acceptable | confirmed_candidates | direct_ok | full | acceptable_if_strategy_allows |
| S3 | confirmed · marginal · reduced_75 · acceptable | confirmed_candidates | marginal | reduced_75 | acceptable_if_strategy_allows |
| S4 | confirmed · marginal · reduced_50 · acceptable | confirmed_candidates | marginal | reduced_50 | acceptable_if_strategy_allows |
| S5 | confirmed · marginal · reduced_25 · acceptable | confirmed_candidates | marginal | reduced_25 | acceptable_if_strategy_allows |
| S6 | early · direct_ok_or_marginal · full_or_reduced_75 · acceptable | early_candidates | direct_ok OR marginal | full OR reduced_75 | acceptable_if_strategy_allows |
| S7 | confirmed · marginal · full · acceptable | confirmed_candidates | marginal | full | acceptable_if_strategy_allows |
| S8 | reference: all confirmed top-bucket (no hint filter) | confirmed_candidates | any | any tradeable | any |
| S9 | reference: all early top-bucket (no hint filter) | early_candidates | any | any tradeable | any |

Notes on segment design:

- S1 and S2 separate `buy_now_candidate` from `acceptable_if_strategy_allows` within `direct_ok` confirmed records to measure the entry-hint signal value.
- S7 captures the `marginal + full depth` case (Q5 scenario 3) separately from S3–S5 to make the dual-meaning visible in returns data.
- S8 and S9 are reference segments for baseline comparison; they are not live basket candidates.
- S6 collapses `direct_ok` and `marginal` for `early_candidates` because early-bucket depth distribution may differ structurally from confirmed; a preliminary check suffices. S6 is scoped to the two best-liquidity execution classes only (full and reduced_75).
- **S6 invariant:** S6 explicitly filters on `entry_action_hint = acceptable_if_strategy_allows` only. Records with `entry_action_hint = buy_now_candidate` in `early_candidates` are excluded from S6 by design. If such records exist, they appear in S9 (reference) and in Cross-breakdown 1 and 2, but are not counted in S6. The exclusion count must be reported in `run_coverage.md`.
- If `buy_now_candidate` has `n = 0` across all runs, S1 is reported as empty. This is expected and must not cause a script error.
- `tranche_ok` records with `execution_size_class = "full"` satisfy the basket filters for Basket A, Basket B, and Basket C, and the reference segments S8/S9 (which accept any `execution_status_raw`). They do **not** satisfy S1/S2 (which require `execution_status_raw = direct_ok`) or S7 (which requires `execution_status_raw = marginal`). S1/S2 remain `direct_ok`-only by design; S7 remains `marginal`-only by design. In all outputs where `tranche_ok` records are included (Baskets A/B/C, S8/S9, Cross-breakdown 1, `run_coverage.json`), their `execution_status_raw = "tranche_ok"` must be preserved via `execution_status_raw_distribution`; they must never be relabeled as `direct_ok`.

### Basket hypothesis segments

Baskets are independent filter definitions, not unions of primary segments. Records that satisfy a basket filter but do not match any named segment S1–S9 are valid basket members; they are counted in basket frequency projections and basket return aggregates. Their segment membership (or absence) is noted in `run_coverage.md`.

```text
Basket A — Conservative Live Pilot:
  is_operational_trade_candidate = true
  candidate_excluded = false
  decision_bucket = confirmed_candidates
  execution_size_class = full
  entry_action_hint IN {buy_now_candidate, acceptable_if_strategy_allows}
  entry_location_status IN {fresh_entry, acceptable_entry}
  priority_score >= PRIORITY_THRESHOLD_A             (see "Priority Score" section)

  Note: Basket A overlaps primarily with S1 + S2 (plus any tranche_ok + full records).

Basket B — Practical Pilot:
  is_operational_trade_candidate = true
  candidate_excluded = false
  decision_bucket = confirmed_candidates
  execution_size_class IN {full, reduced_75, reduced_50}
  entry_action_hint IN {buy_now_candidate, acceptable_if_strategy_allows}
  entry_location_status IN {fresh_entry, acceptable_entry}
  priority_score >= PRIORITY_THRESHOLD_B             (see "Priority Score" section)

  Note: Basket B overlaps with S1–S4, S7 (full-depth marginal), and any
  confirmed + marginal + reduced_75/reduced_50 + buy_now_candidate records
  (which have no dedicated primary segment but are valid basket members).

Basket C — Observation Expansion (shadow/watch only):
  is_operational_trade_candidate = true
  candidate_excluded = false
  decision_bucket IN {confirmed_candidates, early_candidates}
  execution_size_class IN {full, reduced_75, reduced_50, reduced_25}
  entry_action_hint IN {buy_now_candidate, acceptable_if_strategy_allows}
  entry_location_status IN {fresh_entry, acceptable_entry, extended_entry}
  priority_score >= PRIORITY_THRESHOLD_C             (see "Priority Score" section)

  Note: Basket C is broader than S1–S9. It includes early_candidates with
  reduced_50/reduced_25 execution and early buy_now_candidate records that
  have no dedicated primary segment. These out-of-segment basket members are
  valid observation candidates; they are counted in basket projections and
  noted in run_coverage.md.
```

`chased_entry` is excluded from all three baskets, including Basket C.

Basket filters on `entry_location_status` use `record["entry_location"]["entry_location_status"]` per the nested extraction rule above. Records with `entry_location_status = "not_evaluable"` (absent `entry_location` block) do not satisfy the basket filter and are excluded from basket counts.

### Priority score thresholds

Priority score floor thresholds are not hardcoded. The script must:

1. Compute the priority score distribution (P10, P25, median, P75, P90) for the `confirmed_candidates` ir1.5+ population.
2. Compute the distribution for `early_candidates` separately.
3. Report these distributions as the empirical basis for threshold selection.
4. Apply three configurable threshold values from the central config block (see "Config validation" section):

```python
PRIORITY_THRESHOLD_A = 65   # conservative placeholder — override after data review
PRIORITY_THRESHOLD_B = 60   # practical pilot placeholder
PRIORITY_THRESHOLD_C = 55   # observation expansion placeholder
```

The output report must document the applied thresholds and flag them as preliminary pending manual review of the priority score distributions.

---

## Forward return computation

### Reference price semantics

T30-v2 uses the same reference-price semantics as T30-v1, per the T18 Evaluation Replay contract. The script must reuse the existing T18/T30 forward-return helpers or event export for reference-event lookup. It must not implement ad-hoc event reconstruction from daily diagnostics.

```text
For confirmed_candidates:
  reference_price = close price of the bar at which first_confirmed_ready event occurred

For early_candidates:
  reference_price = close price of the bar at which first_early_ready event occurred

If neither event is available for a record:
  mark forward_return_derivable = false
  exclude from forward-return statistics
  retain in segment count and frequency statistics
```

If both the T18 event export and diagnostics-derived state fields are available for the same record, the T18/T30 helper result is authoritative.

### Return horizons

Compute for each record with `forward_return_derivable = true`:

```text
return_1d_pct   = (close[T+1] / reference_price - 1) * 100
return_3d_pct   = (close[T+3] / reference_price - 1) * 100
return_7d_pct   = (close[T+7] / reference_price - 1) * 100
```

Where T is the bar index of the reference event. Returns are computed from daily OHLCV Parquet data.

If fewer than the required forward bars are available (symbol delisted, data gap, run too recent), set the specific return horizon to `null` and do not impute.

### Slippage-adjusted returns

For each return horizon, compute slippage-adjusted variants:

```text
return_1d_adj_pct = return_1d_pct - (estimated_slippage_bps / 10000 * 100)
return_3d_adj_pct = return_3d_pct - (estimated_slippage_bps / 10000 * 100)
return_7d_adj_pct = return_7d_pct - (estimated_slippage_bps / 10000 * 100)
```

Slippage adjustment applies entry slippage only; exit slippage is not modeled in this ticket. If `estimated_slippage_bps` is null for a record, report raw returns only and flag `slippage_adjustment_available = false` for that record.

---

## MFE / MAE computation

MFE (Maximum Favorable Excursion) and MAE (Maximum Adverse Excursion) are conditional outputs.

### Prerequisite check

Before attempting MFE/MAE computation, the script must verify that the Parquet history contains intrabar high/low data for the required symbols and date ranges covered by the ir1.5+ runs.

If the prerequisite is not met, the script must:

1. Log a warning: `MFE/MAE computation skipped: insufficient OHLCV coverage for ir1.5+ run population.`
2. Emit `mfe_mae_available = false` in the output summary.
3. Continue with all other outputs unaffected.

### MFE / MAE definition (when available)

```text
MAE_Nd = minimum of (low[T+1..T+N] / reference_price - 1) * 100   [most negative = worst drawdown]
MFE_Nd = maximum of (high[T+1..T+N] / reference_price - 1) * 100  [most positive = peak gain]
```

Compute at N = 1, 3, 7 days.

---

## Required output metrics per segment

For each primary segment (S1–S9) and each basket (A, B, C), compute:

### Frequency metrics

```text
n_total_records              total records meeting segment filter (all runs)
n_forward_return_derivable   records with computable returns
n_per_run_median             median daily count across runs (frequency proxy)
n_per_run_p25                P25 daily count
n_per_run_p75                P75 daily count
n_zero_days                  runs where segment produced 0 records
```

### Return metrics (for each horizon: 1d, 3d, 7d)

```text
mean_return_pct
median_return_pct
win_pct                      share of records with return > 0
mean_return_adj_pct          slippage-adjusted mean
median_return_adj_pct        slippage-adjusted median
win_pct_adj                  share of records with slippage-adjusted return > 0
p10_return_pct               10th percentile (tail loss indicator)
p90_return_pct               90th percentile (tail gain indicator)
```

### Execution metrics

```text
median_spread_pct
median_estimated_slippage_bps
median_available_depth_ratio
depth_ratio_band_distribution   count by band value
execution_status_raw_distribution  count by execution_status_raw value (for tranche_ok visibility)
```

### Priority score distribution

```text
priority_score_p25
priority_score_median
priority_score_p75
```

### MFE / MAE (if available)

```text
median_mae_1d_pct
median_mae_3d_pct
median_mae_7d_pct
median_mfe_1d_pct
median_mfe_3d_pct
median_mfe_7d_pct
```

---

## Required cross-breakdowns

### Breakdown 1: `execution_size_class` × `decision_bucket` (broad population)

**Population:** All `confirmed_candidates` and `early_candidates` records with `candidate_excluded = false`, regardless of `execution_size_class` value. This includes `observe_only`, `blocked`, `not_evaluable`, and `not_evaluated` records.

For each cell: n, `execution_status_raw_distribution` (count by raw value for tranche_ok visibility), median_return_1d_adj_pct (where derivable), win_pct_adj (1d, where derivable), median_spread_pct.

Purpose: makes the full execution drop-off surface visible before the tradeable-baseline filters are applied. Separation of `direct_ok + full`, `tranche_ok + full`, and `marginal + full` must be visible via `execution_status_raw` within the `full` execution_size_class row.

### Breakdown 2: `entry_location_status` × `entry_action_hint` (tradeable baseline)

**Population:** Records meeting the tradeable baseline (same as primary segments).

For each cell: n, median_return_1d_adj_pct, win_pct_adj (1d).

Records with `entry_location_status = "not_evaluable"` are excluded from cells but reported in a `not_evaluable` summary row with their count.

Purpose: validates whether `entry_location_status` adds explanatory power beyond `entry_action_hint`.

### Breakdown 3: `entry_pattern` × `decision_bucket` (tradeable baseline)

**Population:** Records meeting the tradeable baseline.

For each pattern value: n, median_return_1d_adj_pct, win_pct_adj (1d), median_estimated_slippage_bps.

Flag `continuation_breakout` cells with a `caution_note` field in output: `"high EMA distance risk — validate entry_location_status before inclusion"`. This is a diagnostic annotation, not an exclusion rule.

### Breakdown 4: `market_phase` × `execution_size_class` (tradeable baseline)

**Population:** Records meeting the tradeable baseline.

For each cell: n, median_return_1d_adj_pct.

Valid `market_phase` values per v2.1 Phase Interpreter: `pressure_build`, `trend_resume`, `transition_reclaim`, `none`. Do not use informal labels such as "bull", "accumulation", or "distribution".

Purpose: checks whether execution quality and forward returns vary systematically across v2.1 market phases.

---

## Basket frequency projection

For each basket (A, B, C), compute:

```text
basket_frequency_by_run:
  for each run date: count of records meeting basket filter
basket_n_median
basket_n_p25
basket_n_p75
basket_zero_run_count          runs where basket = 0 records
basket_one_plus_run_count      runs where basket >= 1 record
basket_three_plus_run_count    runs where basket >= 3 records
```

This projection answers the practical question: how often would each basket produce at least one actionable candidate?

---

## Config validation

The following config block must appear at the top of the script. All threshold values must pass validation before the script proceeds.

```python
# T30-v2 config — all thresholds are preliminary placeholders.
# Override after reviewing priority_score_distributions in output.
PRIORITY_THRESHOLD_A = 65
PRIORITY_THRESHOLD_B = 60
PRIORITY_THRESHOLD_C = 55
```

Validation rules:

- Each threshold must be a finite numeric value in the range [0, 100].
- `NaN`, `inf`, `-inf`, strings, and `None` are invalid and must raise `ValueError` at startup.
- Missing values use the script defaults above.
- If CLI or environment overrides are supported, invalid overrides must fail fast with `ValueError` before any data is read.
- The actual thresholds applied in the run must be written to `basket_summary.json` and to `decision_support.md` under a "Applied Configuration" heading.

---

## Decision support summary

The script must emit a `decision_support.md` file summarizing the evidence against each of the six basket selection questions:

```
Q1. Minimum execution_size_class:
    [Show: segment frequency and slippage-adjusted returns by size class]
    [Show: frequency of reduced_75 and reduced_50 in ir1.5+ population]
    [Show: tranche_ok frequency if present]

Q2. Allowed entry_action_hints:
    [Show: frequency of buy_now_candidate vs. acceptable_if_strategy_allows]
    [Show: return comparison between S1 vs S2]

Q3. confirmed_candidates only vs. including early_candidates:
    [Show: S6 vs S1+S2 slippage-adjusted return differential]
    [Show: frequency contribution of early_candidates to Basket C]

Q4. Priority score floor:
    [Show: priority score distributions for confirmed and early populations]
    [Show: return differential above/below each threshold candidate]

Q5. Pattern restrictions:
    [Show: Breakdown 3 (entry_pattern × decision_bucket)]
    [Show: continuation_breakout frequency and return profile]

Q6. Frequency / parallelism:
    [Show: basket frequency projections for A, B, C]
    [Show: zero-candidate run frequency]
```

The decision support summary must not recommend a specific basket. It must present evidence in structured form for human review. It must include:

- An "Applied Configuration" section listing the actual threshold values used.
- A "Limitations" section (see below).
- A prominent warning if OHLCV coverage was insufficient for return metrics.

---

## Output artifacts

All outputs are written to `reports/aux/t30_v2/`. The directory must be created if absent.

### Machine-readable outputs

```text
reports/aux/t30_v2/
  segment_summary.json          per-segment aggregate metrics (S1–S9)
  basket_summary.json           per-basket aggregate metrics (A, B, C) + applied config
  basket_frequency.json         per-run candidate counts by basket
  cross_breakdown_exec_bucket.json
  cross_breakdown_entry_location.json
  cross_breakdown_pattern_bucket.json
  cross_breakdown_phase_exec.json
  priority_score_distributions.json
  run_coverage.json             included/excluded runs, schema result, cross-validation mismatches, forward-return coverage
  mfe_mae_summary.json          if available; else {"mfe_mae_available": false}
```

### Human-readable outputs

```text
reports/aux/t30_v2/
  segment_report.md             tables for S1–S9 with all required metrics
  basket_report.md              tables for baskets A, B, C with frequency projections
  decision_support.md           structured evidence against Q1–Q6 + applied config + limitations
  run_coverage.md               runs included, excluded, cross-validation mismatches, S6 exclusion counts
```

---

## Invariants

- T30-v2 is offline-only.
- T30-v2 does not change runtime scanner behavior.
- T30-v2 does not make basket selection decisions. It produces evidence.
- T30-v2 does not implement Q5 schema cleanup.
- T30-v2 does not implement the overextension marker (feature_enhancements.md Enhancement 4).
- Slippage-adjusted returns are always reported alongside unadjusted returns; they are not silently substituted.
- MFE/MAE are conditional on OHLCV coverage; missing coverage must not block other outputs.
- The priority score thresholds in the config block are explicitly marked as preliminary placeholders.
- `chased_entry` is excluded from all basket definitions by design.
- `max_new_positions_per_run` is not a script output; it is trading policy and belongs outside this ticket.
- Non-finite numeric values must not be emitted in any JSON output.
- `entry_location_status` and `entry_action_hint` are always read from `record["entry_location"][...]`, never from the record root.
- Records with absent `entry_location` block are excluded from entry-location breakdowns but retained in all other statistics.
- `execution_status_raw` is always reported alongside `execution_size_class` in outputs; `tranche_ok` must never be silently merged into `direct_ok`.
- ir1.5+ schema detection uses semantic version comparison (`>= ir1.5`), not string equality.
- The T18/T30 forward-return helper is authoritative for reference-price lookup; no ad-hoc event reconstruction is permitted.
- Baskets are independent filter definitions; a record may satisfy a basket without matching any named primary segment.

---

## Required tests

Add tests under `tests/test_t30_v2.py` (or the existing test layout if a different naming convention applies). All tests must use minimal synthetic fixtures; no live data or CI artifacts required.

1. **ir1.5+ schema detection:**
   - `schema_version = "ir1.5"` → accepted
   - `schema_version = "ir1.4"` → rejected, reason `schema_pre_ir1.5`
   - `schema_version = "ir1.6"` with required fields present → accepted
   - `schema_version = "ir1.6"` with required fields absent → rejected, reason `missing_required_fields`
   - `schema_version` absent + `is_operational_trade_candidate` present → accepted via fallback
   - `schema_version` absent + `is_operational_trade_candidate` absent → rejected

2. **entry_location nested extraction:**
   - Nested values read correctly from `record["entry_location"]["entry_location_status"]`
   - A root-level `entry_location_status` key on the record is ignored (not used instead of nested)
   - Absent `entry_location` block → both fields `"not_evaluable"`

3. **Q5 full dual-meaning (tranche_ok visibility):**
   - `direct_ok + full` and `tranche_ok + full` are distinct in all outputs where `tranche_ok` records are included: Baskets A/B/C, S8/S9, Cross-breakdown 1, and `run_coverage.json`
   - `tranche_ok` records do not appear in S1, S2, or S7 (which filter on `execution_status_raw = direct_ok` or `marginal` respectively)
   - `execution_status_raw_distribution` in Basket and S8/S9 outputs shows distinct counts for `direct_ok`, `tranche_ok`, and `marginal`

4. **S6 invariant:**
   - `early_candidates + buy_now_candidate` records are not counted in S6
   - Exclusion count appears in `run_coverage.md`
   - Such records appear in S9

5. **Basket C consistency:**
   - A fixture record with `early_candidates + reduced_50 + acceptable_if_strategy_allows` satisfies Basket C
   - The same record does not match any of S1–S7 (out-of-segment basket member)
   - It is counted in Basket C frequency and noted in `run_coverage.md`

6. **Slippage-adjusted returns:**
   - 31 bps slippage subtracts exactly 0.31 percentage points from raw return
   - Null `estimated_slippage_bps` → raw return reported, `slippage_adjustment_available = false`

7. **Missing OHLCV:**
   - Frequency metrics are emitted for all records
   - Forward return fields are null / `forward_return_derivable = false`
   - Warning appears in `decision_support.md` and `run_coverage.md`

8. **JSON finiteness:**
   - `NaN`, `inf`, `-inf` inputs in return fields do not appear as numeric values in any JSON output; they must be written as `null`

9. **Config validation:**
   - Threshold value of `NaN` raises `ValueError` at startup before data is read
   - Threshold of 101 raises `ValueError`
   - Valid threshold of 65 is written to `basket_summary.json`

10. **Minimum run count gate:**
    - Script exits with the specified error message when fewer than 20 ir1.5+ runs are found

---

## Acceptance criteria

- [ ] Script runs to completion against a minimum of 20 ir1.5+ runs without manual intervention.
- [ ] Script exits with a clear error message if fewer than 20 ir1.5+ runs are found.
- [ ] ir1.5+ identification uses semantic version comparison (`>= ir1.5`), with `is_operational_trade_candidate` presence as fallback when `schema_version` is absent.
- [ ] Higher schema versions trigger a required-field check before inclusion.
- [ ] All nine primary segments (S1–S9) are computed; S1 and S9 with `n = 0` are valid and must not cause errors.
- [ ] S6 excludes `buy_now_candidate` records; exclusion count reported in `run_coverage.md`; such records appear in S9.
- [ ] `tranche_ok` records are never silently merged into `direct_ok`; `execution_status_raw_distribution` is present in all segment and breakdown outputs.
- [ ] Basket A, B, C are evaluated as independent filter definitions; out-of-segment basket members are noted in `run_coverage.md`.
- [ ] Basket filters apply `entry_location_status` via nested extraction; records with absent `entry_location` block are excluded from basket counts.
- [ ] Slippage-adjusted returns are present for all segments and horizons where `estimated_slippage_bps` is available.
- [ ] MFE/MAE section either produces results or emits `{"mfe_mae_available": false}` without blocking other outputs.
- [ ] Cross-breakdown 1 is computed on the broad population (including observe_only/blocked/not_evaluable/not_evaluated, excluding only `candidate_excluded = true`).
- [ ] Cross-breakdown 2 excludes `not_evaluable` records from cells but reports a `not_evaluable` summary count.
- [ ] Cross-breakdown 4 uses v2.1 phase values (`pressure_build`, `trend_resume`, `transition_reclaim`, `none`); no informal phase labels.
- [ ] `decision_support.md` covers all six basket selection questions (Q1–Q6) with data references, applied config, and limitations.
- [ ] `decision_support.md` includes a prominent warning if OHLCV coverage is insufficient for return metrics.
- [ ] `report.json` cross-validation mismatches written to `run_coverage.json` and `run_coverage.md`; missing `report.json` handled gracefully.
- [ ] Priority score distributions are reported for confirmed and early populations separately.
- [ ] `continuation_breakout` entries in Breakdown 3 carry a `caution_note` field.
- [ ] `run_coverage.json` identifies which runs were included and excluded and why.
- [ ] Config thresholds written to `basket_summary.json` and `decision_support.md`.
- [ ] No non-finite numeric values in any JSON output.
- [ ] No hardcoded priority thresholds outside the central config block.
- [ ] All field extractions use the documented nested-field precedence with fallback.
- [ ] Full test suite passes with `python -m pytest -q`.

---

## Known limitations to document in output

The script must include a `limitations` section in `decision_support.md`:

1. **Bullenmarkt-Verzerrung.** The ir1.5+ run accumulation period (May–June 2026) coincides with a pronounced bull market. Forward returns are likely upward-biased. Segment return differentials are more reliable than absolute return levels.
2. **Small n per segment.** Most primary segments will have n < 30. Win percentages and mean returns at this scale have wide confidence intervals. The analysis supports direction, not precise calibration.
3. **No exit modeling.** Forward returns are unrealized open returns at fixed horizons. Realized returns depend on exit strategy, which is out of scope.
4. **Entry slippage only.** Slippage adjustment covers estimated entry slippage. Exit slippage, market-impact costs, and funding are not modeled.
5. **MFE/MAE may be unavailable.** If OHLCV coverage is insufficient for ir1.5+ runs, MFE/MAE conclusions cannot be drawn.
6. **`buy_now_candidate` frequency.** If S1 has `n = 0`, no empirical comparison between `buy_now_candidate` and `acceptable_if_strategy_allows` is possible from this analysis alone.
