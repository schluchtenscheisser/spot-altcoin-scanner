# 2026-05-27 — BACKTEST-2 — Actionable Segment Report

## Status

**Status:** Draft for Codex implementation  
**Project:** Independence — Spot Altcoin Scanner  
**Workstream:** Historical Backtest / Segment Validation  
**Target PR size:** One focused PR  
**Language:** English ticket, German chat context  

---

## 1. Context / Source

Backtest-1 produced a validated enriched historical replay dataset and an initial descriptive segment analysis.

Current validated dataset family:

```text
evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/enriched_replay_events.parquet
```

Backtest-1 showed that the scanner's edge is primarily short-horizon:

```text
1d: strongest
3d: still clearly useful in strong segments
5d: still useful in some segments but weaker
10d / 20d: unstable / weak without exit logic
```

This matches the intended use case: identify short-term spot-altcoin opportunities with an expected holding period of roughly 1–3 days.

Backtest-1 also identified preliminary candidate segments:

```text
Tier A hypotheses:
- early_candidates × base_reclaim
- confirmed_candidates × ema_reclaim
- early_candidates × early_reversal_break

Tier B / observe:
- confirmed_candidates × base_reclaim
```

Important boundary: Backtest-1 is not a trading P&L simulation. Forward returns are labels for evaluation only. Historical execution, MEXC orderbook depth, slippage, fees, and point-in-time market cap are not included.

BACKTEST-2 must automate the manually inspected actionable segment view so the project can make repeatable segment decisions without changing live scanner logic.

---

## 2. Canonical References

Use the current authoritative reference hierarchy:

1. The seven v2.1 specification section documents.
2. `independence_release_gesamtkonzept_final.md`.
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md` as supplementary ticket context.
4. Backtest-1 empirical findings:
   - `backtest_1_findings.md`
   - `2026-05-26__backtest_1_segment_findings_project_update.md`
   - `Claude_handover_segment_decision_chat.md`
5. Existing repository reality, especially:
   - `scripts/backtest/build_replay_event_dataset.py`
   - `scripts/backtest/analyze_replay_event_dataset.py`
   - existing output conventions under `evaluation/backtest/reports/`

If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents apply only insofar as they do not contradict this reference set.

Backtest-1 findings are empirical decision support, not canonical scanner-spec changes.

---

## 3. Goal

Implement a focused, repeatable actionable segment report that groups enriched replay events by:

```text
historical_signal_bucket × entry_pattern
```

and classifies segments into:

```text
Tier A
Tier B
Exclude
Diagnostic
```

The report must support decision-making for later initial tradeable segment selection, especially for 1d–3d holding horizons.

---

## 4. Non-Goals / Out of Scope

Do **not** implement or change any live scanner logic.

Do **not** implement real trading rules.

Do **not** implement exit logic.

Do **not** implement execution simulation.

Do **not** use MEXC orderbook depth, spreads, slippage, fees, or real tradeability in this ticket.

Do **not** change Backtest-Merge logic unless a trivial helper import is required.

Do **not** require a new full historical replay.

Do **not** promote `late_monitor` to a tradeable entry segment.

Do **not** group by `entry_pattern_score`. It is numeric context only, not the categorical pattern label.

Do **not** use `event_type` for BACKTEST-2 diagnostic classification. Terminal-event return analysis remains a separate deferred topic.

---

## 5. Proposed Change

Add a new script:

```text
scripts/backtest/analyze_actionable_segments.py
```

The script reads an enriched replay-events parquet file, computes segment-level forward-return statistics, classifies each segment, and writes a Markdown, JSON, CSV, and Parquet report set.

Required CLI:

```bash
python scripts/backtest/analyze_actionable_segments.py \
  --input-events-parquet evaluation/backtest/exports/<scenario_id>/<replay_id>/enriched_replay_events.parquet \
  --output-dir evaluation/backtest/reports/<scenario_id>/<replay_id>/
```

Both arguments are required.

No input path, replay ID, scenario ID, or output path may be hardcoded in the script.

The script may create `--output-dir` if it does not exist.

---

## 6. Required Inputs and Schema Validation

### 6.1 Required categorical / filter columns

The input parquet must contain these columns:

```text
included_in_primary_analysis
included_in_signal_analysis
historical_signal_bucket
entry_pattern
```

`entry_pattern` is the required categorical entry-pattern label. `entry_pattern_score` must not be used as a substitute grouping key.

If `entry_pattern` is absent, fail fast with a clear schema error listing available columns.

Rows where `entry_pattern` is `null`, `NaN`, empty string, or only whitespace must be normalized for analysis purposes to:

```text
entry_pattern = "none"
```

This normalization applies to all scope filters, segment keys, classification rules, output files, and tests. It must happen before applying `entry_pattern != "none"` filters so nullable pattern labels cannot accidentally pass primary actionable scope through pandas comparison behavior.

### 6.2 Required forward-return columns

The script must support horizons:

```text
1d
3d
5d
10d
20d
```

Do not guess forward-return column names from this ticket if the existing repository already defines them.

Implementation rule:

1. Inspect and reuse the existing forward-return column mapping or helper logic used by `scripts/backtest/analyze_replay_event_dataset.py` and/or produced by `scripts/backtest/build_replay_event_dataset.py`.
2. If such helper constants already exist, import/reuse them instead of duplicating string literals.
3. If no reusable mapping exists, define a local mapping in `analyze_actionable_segments.py` using the actual column names present in `enriched_replay_events.parquet` as produced by the current repo code.
4. Validate that all required horizon columns exist before computing metrics.
5. If any required horizon column is missing, fail fast with a clear schema error listing:
   - missing required columns
   - available columns
   - the expected horizon mapping used by the script

Output column names must be standardized as specified in this ticket, even if internal input column names differ.

### 6.3 Required split / context columns

Required for split output:

```text
btc_regime_label
quote_volume_bucket
```

Required for liquidity-proxy output if available in the enriched dataset:

```text
median_quote_volume_30d
median_quote_volume_90d
```

If `median_quote_volume_30d` or `median_quote_volume_90d` is missing, the script must still run, but the corresponding output metric must be `null` and the JSON/Markdown report must include a warning.

If `btc_regime_label` or `quote_volume_bucket` is missing, fail fast. These are required for BACKTEST-2 split output.

### 6.4 Required input type rules

Allowed input type:

```text
--input-events-parquet: path to a readable parquet file
--output-dir: path to a directory, created if missing
```

Ambiguous inputs must not be silently reinterpreted.

Hard rejection rules:

```text
- missing --input-events-parquet -> CLI error
- missing --output-dir -> CLI error
- input path does not exist -> CLI error
- input path is not a file -> CLI error
- input file cannot be read as parquet -> clear error
- required columns missing -> clear schema error
```

Allowed input types, units, coercion rules, and hard rejection rules are fully specified. Ambiguous inputs must not be silently reinterpreted.

---

## 7. Analysis Scopes

### 7.1 Primary actionable scope

Rows belong to the primary actionable scope iff, after normalizing nullable/blank `entry_pattern` values to `"none"`:

```text
included_in_primary_analysis = true
AND included_in_signal_analysis = true
AND historical_signal_bucket in {confirmed_candidates, early_candidates}
AND entry_pattern != "none"
```

This scope is the main segment-selection view.

### 7.2 Actionable candidate scope including excludes

For explicit `Exclude` classification, also evaluate actionable buckets with `entry_pattern = "none"`, including rows normalized to `"none"` because the original `entry_pattern` was null/NaN/blank:

```text
included_in_primary_analysis = true
AND included_in_signal_analysis = true
AND historical_signal_bucket in {confirmed_candidates, early_candidates}
```

This lets the report explicitly classify `entry_pattern = none` as `Exclude` instead of silently dropping it.

### 7.3 Diagnostic scope

Rows belong to diagnostic scope iff:

```text
included_in_primary_analysis = true
AND included_in_signal_analysis = true
AND historical_signal_bucket in {late_monitor, watchlist, discarded}
```

Diagnostic classification is based only on `historical_signal_bucket` in BACKTEST-2.

Do not use `event_type` for diagnostic classification in this ticket.

Diagnostic segments must never be classified as Tier A or Tier B, even if their short-horizon returns look strong.

---

## 8. Segment Key

The canonical segment key is:

```text
historical_signal_bucket
entry_pattern
```

For human-readable Markdown output, also render:

```text
<bucket> × <entry_pattern>
```

Example:

```text
early_candidates × base_reclaim
```

Sorting must be deterministic.

Default segment sort order:

1. `classification_sort_order`:
   - `Tier A` = 1
   - `Tier B` = 2
   - `Exclude` = 3
   - `Diagnostic` = 4
2. `forward_return_3d_median_pct` descending, nulls last
3. `forward_return_1d_median_pct` descending, nulls last
4. `count` descending
5. `historical_signal_bucket` ascending
6. `entry_pattern` ascending

At identical input and identical code, output ordering must be identical.

---

## 9. Metrics

Compute these metrics per segment and per split row.

For each horizon in:

```text
1d, 3d, 5d, 10d, 20d
```

compute:

```text
forward_return_<horizon>_mean_pct
forward_return_<horizon>_median_pct
forward_return_<horizon>_win_rate_pct
forward_return_<horizon>_non_null_count
```

Win rate definition:

```text
100 * count(forward_return_<horizon>_pct > 0) / count(non-null finite forward_return_<horizon>_pct)
```

If the non-null finite denominator is 0:

```text
forward_return_<horizon>_win_rate_pct = null
```

Also compute:

```text
count
median_quote_volume_30d
median_quote_volume_90d
```

`count` is the number of rows in the segment/split before excluding null return values.

Median quote-volume metrics are medians over finite non-null values. If unavailable or no finite values exist, output `null`.

---

## 10. Numeric Robustness

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid / non-evaluable inputs for metric aggregation and must not be passed through as numeric-looking outputs.

For metric aggregation:

```text
None / NaN / inf / -inf -> excluded from mean, median, and win-rate denominator
```

If all values for a metric are missing/non-finite:

```text
mean = null
median = null
win_rate = null
non_null_count = 0
```

Do not coerce missing forward returns to 0.

Do not coerce null win rates to 0.

Do not let `bool(x)` determine nullable semantic fields.

Not evaluable / not available and negative performance are separate states and must remain separate.

---

## 11. Classification Rules

Classification is segment-level, computed from the overall segment row, not from split rows.

### 11.1 Tier A

```text
classification = "Tier A"
iff:
  historical_signal_bucket in {early_candidates, confirmed_candidates}
  AND entry_pattern != "none"
  AND count >= 15
  AND forward_return_1d_median_pct > 0
  AND forward_return_3d_median_pct > 0
  AND forward_return_1d_win_rate_pct >= 60
  AND forward_return_3d_win_rate_pct >= 55
  AND forward_return_5d_median_pct > -2.0
```

Null handling for Tier A:

```text
If forward_return_5d_median_pct is null, the segment is not eligible for Tier A.
Missing / not evaluable 5d median is not negative performance, but it fails the conservative Tier A evidence requirement.
```

### 11.2 Tier B

```text
classification = "Tier B"
iff:
  historical_signal_bucket in {early_candidates, confirmed_candidates}
  AND entry_pattern != "none"
  AND count >= 10
  AND forward_return_1d_median_pct > 0
  AND (
        forward_return_3d_median_pct >= 0
        OR forward_return_3d_win_rate_pct >= 55
      )
  AND NOT Tier A
```

Tier B intentionally has no hard 5d floor. Weak 5d behavior is surfaced through warning fields.

### 11.3 Exclude

```text
classification = "Exclude"
iff:
  historical_signal_bucket in {early_candidates, confirmed_candidates}
  AND (
       entry_pattern = "none"
       OR count < 10
       OR forward_return_1d_median_pct <= 0
       OR (
            forward_return_3d_median_pct <= 0
            AND forward_return_3d_win_rate_pct < 55
          )
      )
```

### 11.4 Diagnostic

```text
classification = "Diagnostic"
iff:
  historical_signal_bucket in {late_monitor, watchlist, discarded}
```

Diagnostic segments must never be promoted to Tier A or Tier B in BACKTEST-2.

### 11.5 Classification precedence

Apply classification in this order:

1. Diagnostic
2. Tier A
3. Tier B
4. Exclude
5. Fallback `Unclassified`

`Unclassified` should be rare. If produced, include it in outputs and add a report warning with the affected segment keys.

---

## 12. Warning Fields

Compute these boolean warning fields for each overall segment and each split row:

```text
low_sample = true iff count < 15
sample_warning = true iff count < 20
warning_5d_weak = true iff forward_return_5d_median_pct <= -2.0
warning_5d_severe = true iff forward_return_5d_median_pct <= -5.0
```

Null handling:

```text
If forward_return_5d_median_pct is null:
  warning_5d_weak = null
  warning_5d_severe = null
```

Rationale:

- `sample_warning` should flag promising but smaller samples such as count 17.
- `low_sample` identifies segments below Tier A count eligibility.
- 5d warnings protect against segments that may work on 1d/3d but decay sharply by 5d.

---

## 13. Split Output

Write a split output file containing one row per:

```text
historical_signal_bucket
entry_pattern
split_type
btc_regime_label
quote_volume_bucket
```

Allowed `split_type` values:

```text
overall
btc_regime
quote_volume_bucket
btc_regime_x_quote_volume_bucket
```

Field semantics:

| split_type | btc_regime_label | quote_volume_bucket |
|---|---|---|
| overall | ALL | ALL |
| btc_regime | concrete regime value | ALL |
| quote_volume_bucket | ALL | concrete quote-volume bucket |
| btc_regime_x_quote_volume_bucket | concrete regime value | concrete quote-volume bucket |

The split output is annotation / robustness context only.

BTC regime and volume splits are not Tier A prerequisites in BACKTEST-2.

Tier classification must be derived only from the overall segment metrics, not from split rows.

For split rows, include the segment's overall classification in a field:

```text
overall_classification
```

Do not compute independent Tier A/B classifications per split row in this ticket.

---

## 14. Output Files

Write all files to `--output-dir`:

```text
actionable_segment_report.md
actionable_segment_report.json
actionable_segments.csv
actionable_segments.parquet
actionable_segment_splits.csv
actionable_segment_splits.parquet
```

### 14.1 `actionable_segments.csv/.parquet`

One row per overall segment.

Required columns:

```text
historical_signal_bucket
entry_pattern
segment_label
classification
classification_sort_order
count
forward_return_1d_mean_pct
forward_return_1d_median_pct
forward_return_1d_win_rate_pct
forward_return_1d_non_null_count
forward_return_3d_mean_pct
forward_return_3d_median_pct
forward_return_3d_win_rate_pct
forward_return_3d_non_null_count
forward_return_5d_mean_pct
forward_return_5d_median_pct
forward_return_5d_win_rate_pct
forward_return_5d_non_null_count
forward_return_10d_mean_pct
forward_return_10d_median_pct
forward_return_10d_win_rate_pct
forward_return_10d_non_null_count
forward_return_20d_mean_pct
forward_return_20d_median_pct
forward_return_20d_win_rate_pct
forward_return_20d_non_null_count
median_quote_volume_30d
median_quote_volume_90d
low_sample
sample_warning
warning_5d_weak
warning_5d_severe
```

### 14.2 `actionable_segment_splits.csv/.parquet`

One row per split segment.

Required columns:

```text
historical_signal_bucket
entry_pattern
segment_label
split_type
btc_regime_label
quote_volume_bucket
overall_classification
count
forward_return_1d_mean_pct
forward_return_1d_median_pct
forward_return_1d_win_rate_pct
forward_return_1d_non_null_count
forward_return_3d_mean_pct
forward_return_3d_median_pct
forward_return_3d_win_rate_pct
forward_return_3d_non_null_count
forward_return_5d_mean_pct
forward_return_5d_median_pct
forward_return_5d_win_rate_pct
forward_return_5d_non_null_count
forward_return_10d_mean_pct
forward_return_10d_median_pct
forward_return_10d_win_rate_pct
forward_return_10d_non_null_count
forward_return_20d_mean_pct
forward_return_20d_median_pct
forward_return_20d_win_rate_pct
forward_return_20d_non_null_count
median_quote_volume_30d
median_quote_volume_90d
low_sample
sample_warning
warning_5d_weak
warning_5d_severe
```

### 14.3 `actionable_segment_report.json`

JSON must include:

```json
{
  "analysis_id": "BACKTEST-2_ACTIONABLE_SEGMENT_REPORT",
  "input_events_parquet": "...",
  "output_dir": "...",
  "generated_at_utc": "...",
  "row_counts": {
    "input_rows": 0,
    "primary_actionable_rows": 0,
    "actionable_candidate_rows": 0,
    "diagnostic_rows": 0,
    "overall_segment_rows": 0,
    "split_rows": 0
  },
  "thresholds": {
    "tier_a_min_count": 15,
    "tier_b_min_count": 10,
    "sample_warning_count_lt": 20,
    "low_sample_count_lt": 15,
    "tier_a_5d_median_floor_pct": -2.0,
    "warning_5d_weak_median_lte_pct": -2.0,
    "warning_5d_severe_median_lte_pct": -5.0
  },
  "classification_counts": {
    "Tier A": 0,
    "Tier B": 0,
    "Exclude": 0,
    "Diagnostic": 0,
    "Unclassified": 0
  },
  "warnings": [],
  "segments": []
}
```

`segments` should contain the same records as `actionable_segments.csv`, serialized with JSON-safe nulls.

### 14.4 `actionable_segment_report.md`

Markdown must include:

1. Title and generation metadata.
2. Method boundary:
   - not trading P&L
   - no execution simulation
   - forward returns are labels, not signal inputs
   - quote-volume is only a liquidity proxy
3. Scope definitions.
4. Threshold definitions.
5. Tier A table.
6. Tier B table.
7. Exclude table.
8. Diagnostic table.
9. Split summaries:
   - BTC regime annotation
   - quote-volume bucket annotation
   - combined BTC regime × quote-volume annotation
10. Warnings section.

If no rows exist for a section, render explicit text:

```text
No Tier A segments found under the current thresholds.
No Tier B segments found under the current thresholds.
No Exclude segments found under the current thresholds.
No Diagnostic segments found under the current scope.
```

Do not silently omit empty sections.

---

## 15. Determinism / Sorting / Formatting

At identical input and identical code, output must be deterministic.

Rules:

```text
- stable sort order as defined in section 8
- no dependence on dict/set iteration order
- consistent float rounding in Markdown only
- CSV/Parquet should preserve full numeric precision except normal pandas/pyarrow serialization behavior
```

Markdown formatting:

```text
- percentages rendered with two decimals
- null values rendered as "n/a"
- booleans rendered as true/false/n/a
```

CSV formatting may use normal pandas defaults, but nulls must remain null/empty, not stringified as `"nan"`.

---

## 16. Tests

Add or extend tests under the existing test structure. If there is already a backtest script test area, use it. Otherwise add a focused test module such as:

```text
tests/backtest/test_analyze_actionable_segments.py
```

### 16.1 Required tests

1. **CLI required arguments**
   - missing `--input-events-parquet` fails
   - missing `--output-dir` fails

2. **Schema validation and entry-pattern normalization**
   - missing `entry_pattern` fails fast
   - error message says `entry_pattern` is required and lists available columns
   - `entry_pattern_score` is not accepted as substitute grouping key
   - `entry_pattern = null` / `NaN` / blank is normalized to `"none"` before scope filtering and classification

3. **Primary actionable classification**
   - synthetic segment meeting Tier A thresholds becomes `Tier A`
   - synthetic segment meeting Tier B thresholds but not Tier A becomes `Tier B`
   - `entry_pattern = none` in actionable bucket becomes `Exclude`
   - original `entry_pattern = null` in actionable bucket becomes `Exclude` after normalization
   - weak 3d profile rule works exactly:
     ```text
     forward_return_3d_median_pct <= 0 AND forward_return_3d_win_rate_pct < 55
     ```

4. **Diagnostic classification**
   - `late_monitor` becomes `Diagnostic`
   - `watchlist` becomes `Diagnostic`
   - `discarded` becomes `Diagnostic`
   - Diagnostic segment is not Tier A/B even if returns are strong

5. **Warning fields**
   - count 14 -> `low_sample = true`, `sample_warning = true`
   - count 17 -> `low_sample = false`, `sample_warning = true`
   - count 20 -> both false
   - 5d median `-2.0` -> `warning_5d_weak = true`
   - 5d median `-5.0` -> both `warning_5d_weak = true` and `warning_5d_severe = true`
   - 5d median null -> both warning fields null
   - 5d median null -> not eligible for Tier A

6. **Split output**
   - writes rows for all required split types:
     ```text
     overall
     btc_regime
     quote_volume_bucket
     btc_regime_x_quote_volume_bucket
     ```
   - `overall` row uses `ALL` / `ALL`
   - split rows carry `overall_classification`
   - split rows do not independently promote/demote Tier classification

7. **Numeric robustness**
   - `None`, `NaN`, `inf`, `-inf` are excluded from metric denominators
   - missing return values are not coerced to 0
   - win rate denominator uses only finite non-null values
   - all-missing horizon returns null metrics and non-null count 0

8. **Empty sections**
   - Markdown explicitly includes:
     ```text
     No Tier A segments found under the current thresholds.
     ```
     when no Tier A segment exists

9. **Deterministic sorting**
   - repeated execution on shuffled equivalent input produces identical output order

10. **Output file creation**
   - all six required output files are written
   - CSV and Parquet row counts match for each output table

### 16.2 Test data guidance

Use small synthetic DataFrames written to temporary parquet files.

Do not require the full historical dataset in unit tests.

If existing project tests include fixture helpers for parquet IO, reuse them.

---

## 17. Acceptance Criteria

- `scripts/backtest/analyze_actionable_segments.py` exists.
- The script requires `--input-events-parquet` and `--output-dir`.
- No dataset path or replay ID is hardcoded.
- The script validates required columns before analysis.
- Missing `entry_pattern` fails fast with a clear schema error.
- Nullable/blank `entry_pattern` values are normalized to `"none"` before scope filtering, segment grouping, and classification.
- `entry_pattern_score` is not used as grouping key.
- Diagnostic classification uses only `historical_signal_bucket`, not `event_type`.
- Segment-level metrics are computed for 1d, 3d, 5d, 10d, and 20d horizons.
- Tier A, Tier B, Exclude, and Diagnostic classifications follow the exact rules in this ticket.
- Null `forward_return_5d_median_pct` disqualifies Tier A but leaves 5d warning fields null.
- Warning fields are present in both overall and split outputs:
  ```text
  warning_5d_weak
  warning_5d_severe
  sample_warning
  low_sample
  ```
- Outputs are written:
  ```text
  actionable_segment_report.md
  actionable_segment_report.json
  actionable_segments.csv
  actionable_segments.parquet
  actionable_segment_splits.csv
  actionable_segment_splits.parquet
  ```
- Markdown report explicitly renders empty tier messages instead of silently omitting empty sections.
- BTC-regime and quote-volume splits are annotation only and do not determine Tier A/B classification.
- Tests cover classification, warnings, split output, missing schema fields, numeric robustness, empty sections, and deterministic sorting.
- Existing BACKTEST-1 script behavior remains unchanged.

---

## 18. Constraints / Invariants

- This ticket is analysis/reporting only.
- No live scanner decision logic may change.
- No v2.1 bucket semantics may change.
- `late_monitor` remains diagnostic only in BACKTEST-2.
- `entry_pattern = none` must not be treated as equivalent to a concrete entry pattern.
- Null/NaN/blank `entry_pattern` values must be treated as `entry_pattern = none`, not as concrete patterns.
- Forward returns are output/evaluation labels, not signal inputs.
- Quote-volume is an OHLCV-derived proxy, not a substitute for real execution analysis.
- Not evaluable / missing and negative performance must remain separate.
- Non-finite numeric values must not leak into output as numeric-looking values.
- At identical input and code, outputs must be deterministic.

---

## 19. Suggested Implementation Notes

A clean implementation likely uses small pure helper functions:

```text
validate_input_schema(df) -> None
finite_series(series) -> series
compute_return_metrics(df, horizon_mapping) -> dict
build_overall_segments(df) -> DataFrame
classify_segment(row) -> str
add_warning_fields(df) -> DataFrame
build_split_segments(df, overall_classification_map) -> DataFrame
write_outputs(...)
render_markdown_report(...)
```

Prefer pure functions for classification and metrics so tests can directly exercise them.

Do not bury classification thresholds in Markdown rendering code. Keep them centralized as named constants or a small immutable dataclass.

No config file is required for this ticket.

---

## 20. Definition of Done

- Code implemented.
- Tests added and passing.
- Script can be run manually against a valid `enriched_replay_events.parquet`.
- All required outputs are generated in the provided output directory.
- JSON includes thresholds, row counts, classification counts, warnings, and segment records.
- Markdown report is human-readable and explicitly states methodological limits.
- No scanner runtime behavior is modified.
- No unrelated cleanup or refactor is included.

---

## 21. Preflight Self-Review Against Codex Ticket Checklist

Checked before publication:

- Scope is limited to one analysis/reporting PR.
- Authoritative reference hierarchy is stated.
- No scanner rule change is introduced.
- Required fields are explicitly named.
- Unconfirmed `entry_pattern` field risk is handled by fail-fast validation.
- `entry_pattern_score` is explicitly forbidden as grouping-key substitute.
- `event_type` is explicitly out of scope for Diagnostic classification.
- Thresholds are numeric and deterministic.
- Missing vs invalid vs negative values are separated.
- Nullable `entry_pattern` and nullable 5d median behavior are explicitly specified.
- Non-finite numeric handling is specified.
- Output files and schemas are explicitly defined.
- Empty tier edge cases are specified.
- Split-file semantics are specified.
- Tests cover classification, warnings, schema failures, splits, numeric robustness, and determinism.
