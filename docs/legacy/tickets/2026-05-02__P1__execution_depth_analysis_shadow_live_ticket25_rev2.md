> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# T25: Add Execution Depth Analysis Script for Shadow-Live Runs

## Metadata

- Ticket ID: T25
- Title: Add Execution Depth Analysis Script for Shadow-Live Runs
- Status: Ready for implementation
- Target PR size: One focused PR
- Language: Implementation and code artifacts in English
- Primary mode affected: Offline analysis of Daily Shadow-Live run reports

## Authoritative reference hierarchy

If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Existing repo documents remain valid only to the extent that they do not contradict this reference set.

Current authoritative reference set for this ticket:

1. Independence Release v2.1 section files, especially:
   - Section 6: Daily vs Intraday Update Policy
   - Section 7: Entry Pattern Resolution + Decision Buckets
2. `independence_release_gesamtkonzept_final.md`
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`
4. Current repo reality on `main`, especially:
   - `scanner/runners/daily.py`
   - `scanner/output/report_builder.py`
   - `scanner/output/schema.py`
   - `docs/canonical/REPORTS.md`
   - `scripts/`
   - existing analysis-output path tests
5. Existing implemented contracts from T13, T19, T21, T21.1, T22, T23, and T24.

This ticket must not create a second competing execution-reporting truth. T25 reads and aggregates the additive T24 execution-aware report blocks. It must not reconstruct equivalent semantics from diagnostics or live state.

## Current context

T24 added execution-aware segmentation to daily `report.json` so that each daily Shadow-Live run can distinguish structural candidates from executable, direct OK, tranche OK, marginal, failed, unknown, not-attempted, and unexpected execution states.

The next operational question is no longer whether a single report is readable. The next question is whether multiple Shadow-Live runs show stable execution bottlenecks by bucket, universe category, reason, and symbol recurrence.

T25 adds one offline analysis script that aggregates multiple T24 reports and writes auxiliary analysis artifacts under `reports/aux/`. It does not change scanner runtime behavior.

## Goal

Add a deterministic offline analysis script for T24 daily Shadow-Live reports that quantifies execution quality and execution-depth bottlenecks across multiple runs.

The script must answer, from T24 report fields only:

- how many structural candidates were seen across runs,
- how many were executable,
- how many were direct OK or tranche OK,
- how many were marginal, failed, unknown, not attempted, or unexpected,
- which buckets and universe categories are execution-problematic,
- which execution reasons dominate,
- which symbols repeatedly fail, remain marginal, remain unknown, or repeatedly pass execution,
- how confirmed and early structural-vs-executable counts evolve over time.

The script must produce machine-readable JSON and human-readable Markdown under `reports/aux/`.

## Non-goals / out of scope

Do not implement any of the following in this ticket:

- No execution threshold changes.
- No execution grader changes.
- No execution adapter changes.
- No `DecisionBucket` assignment changes.
- No `priority_score` changes.
- No ranking changes.
- No T23 universe classification changes.
- No T24 report-segmentation changes.
- No daily report schema changes.
- No evaluation replay or evaluation metric changes.
- No intraday carry-forward work.
- No OHLCV replay.
- No orderbook replay.
- No MEXC live API calls.
- No reads from live SQLite.
- No workflow-required integration.
- No report writer changes in `scanner/output/report_builder.py`.
- No report-generation changes in `scanner/runners/daily.py`.
- No output under `reports/analysis`.
- No writes under `reports/runs/**`.
- No fallback to `symbol_diagnostics.jsonl.gz`.

## Required repo changes

### 1. Add a new analysis script

Add:

```text
scripts/analyze_execution_depth_shadow_live.py
```

The script must be executable as a normal Python CLI script.

It must support these CLI arguments:

```text
--reports-root reports/runs
--run-dir <path>              # may be passed multiple times
--output-json reports/aux/execution_depth_analysis.json
--output-md reports/aux/execution_depth_analysis.md
--max-runs <n>
--top-n 20
```

Argument behavior:

- If one or more `--run-dir` values are provided, analyze exactly those run directories.
- If no `--run-dir` is provided, recursively discover `report.json` files under `--reports-root`.
- `--reports-root` default is `reports/runs`.
- `--output-json` default is `reports/aux/execution_depth_analysis.json`.
- `--output-md` default is `reports/aux/execution_depth_analysis.md`.
- `--top-n` default is `20`.
- `--top-n` must be an integer `>= 1`; invalid values must fail with a clear error.
- `--max-runs`, if provided, must be an integer `>= 1`; invalid values must fail with a clear error.
- If `--max-runs` is provided, analyze the newest runs first based on `(daily_bar_id, as_of_utc, run_id)` descending and keep at most `max_runs`. The output itself must still use deterministic ordering rules defined below.

The script must create parent directories for `--output-json` and `--output-md` if needed.

### 2. Enforce output path policy

The default outputs must be under:

```text
reports/aux/
```

The script must reject output paths under:

```text
reports/analysis
reports/runs
snapshots/runs
```

Rejecting these paths should produce a clear error before writing anything.

The script may allow custom output paths under other allowed analysis roots only if they do not violate the forbidden path rules. Do not introduce a persistent artifact root outside the established allowed roots.

### 3. Require T24 report fields

T25 must read these T24 top-level blocks from each `report.json`:

```json
{
  "execution_aware_summary": {},
  "execution_counts_by_bucket": {},
  "execution_counts_by_universe_category": {},
  "execution_counts_by_bucket_and_category": {},
  "execution_aware_candidate_segments": {}
}
```

If any required T24 block is missing from any analyzed report, the script must fail with a clear error, for example:

```text
T25 requires T24 execution-aware report fields. Missing execution_aware_summary in <path>.
```

Do not fall back to `symbol_diagnostics.jsonl.gz`. Do not reconstruct T24 semantics from diagnostics. Do not read live SQLite. Do not call live APIs.

### 4. Add tests

Add focused tests, for example:

```text
tests/test_ticket25_execution_depth_analysis.py
tests/test_ticket25_execution_depth_analysis_paths.py
```

The exact file split may differ if the existing test style suggests a better layout, but coverage must include all required cases listed below.

## Input contract

Each input report must be a T24 daily `report.json` with:

- `run_id`
- `scan_mode`
- `as_of_utc`
- `daily_bar_id`
- `execution_aware_summary`
- `execution_counts_by_bucket`
- `execution_counts_by_universe_category`
- `execution_counts_by_bucket_and_category`
- `execution_aware_candidate_segments`

Only `scan_mode == "daily"` reports are in scope. If a discovered or provided report has `scan_mode != "daily"`, the script must ignore it with a deterministic warning in the Markdown summary or fail clearly. Prefer fail clearly for explicit `--run-dir` inputs and skip with warning for recursive discovery.

The script must not require `symbol_diagnostics.jsonl.gz` to exist.

Sparse category maps from T24 are valid:

- Missing universe category keys mean `0`, not schema failure.
- Existing category keys must be aggregated normally.
- Existing category blocks should contain the T24 count keys; if a present block is malformed, fail clearly.

## Execution status semantics inherited from T24

T25 must not redefine execution semantics. It must aggregate T24 fields using the following T24 meanings:

- `structural`: T23 candidate-visible/tradable structural base.
- `executable`: execution-pass structural candidate, currently direct OK or tranche OK in T24.
- `direct_ok`: direct executable outcome.
- `tranche_ok`: tranche executable outcome.
- `marginal`: evaluated but not executable marginal outcome.
- `failed`: evaluated negative execution outcome.
- `unknown_execution`: attempted but no reliable positive/negative execution evaluation.
- `not_attempted`: execution was not attempted.
- `unexpected_execution_state`: internally inconsistent or unsupported execution diagnostic combination surfaced by T24.

Not evaluated / not attempted and fachlich negative execution evaluation are separate states and must remain separate in T25.

`unknown_execution` and `failed` are separate states and must not be collapsed.

`marginal` and `failed` are separate states and must not be collapsed.

`unexpected_execution_state` must not be hidden under `failed`, `unknown_execution`, `marginal`, or `executable`.

## Count keys and rate rules

Use this common count-key set wherever a count block is specified:

```json
{
  "structural": 0,
  "execution_attempted": 0,
  "executable": 0,
  "direct_ok": 0,
  "tranche_ok": 0,
  "marginal": 0,
  "failed": 0,
  "unknown_execution": 0,
  "unexpected_execution_state": 0,
  "not_attempted": 0
}
```

Use this common rate-key set wherever rates are specified:

```json
{
  "executable_rate": null,
  "direct_ok_rate": null,
  "tranche_ok_rate": null,
  "marginal_rate": null,
  "failed_rate": null,
  "unknown_execution_rate": null,
  "unexpected_execution_state_rate": null,
  "not_attempted_rate": null
}
```

For all rates in this ticket:

- denominator is `structural`, unless explicitly stated otherwise;
- if `structural == 0`, rate value is `null`, not `0.0`;
- if numerator is `0` and denominator is positive, rate value is `0.0`;
- rates must be finite JSON numbers or `null`;
- never emit `NaN`, `Infinity`, or `-Infinity`.

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid / non-emittable for analysis JSON and Markdown. They must be normalized to `null` for rates or rejected for required integer counts.

All counts must be integers `>= 0`. Bool is not a valid integer count.

## JSON output contract

The JSON output must be strict JSON and must not contain non-standard numeric tokens such as `NaN`, `Infinity`, or `-Infinity`.

Top-level shape:

```json
{
  "schema_version": "t25_execution_depth_analysis_v1",
  "generated_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "input": {},
  "summary": {},
  "by_run": {},
  "by_bucket": {},
  "by_universe_category": {},
  "by_bucket_and_category": {},
  "execution_reason_counts": {},
  "execution_reason_counts_by_bucket": {},
  "execution_reason_counts_by_universe_category": {},
  "over_time": {},
  "top_repeated_symbols": {}
}
```

### `input`

Shape:

```json
{
  "reports_root": "reports/runs",
  "run_count": 0,
  "run_ids": [],
  "report_paths": [],
  "top_n": 20,
  "max_runs": null
}
```

Rules:

- `run_count` is the number of analyzed reports after filtering and `max_runs` application.
- `run_ids` is sorted by `(daily_bar_id, as_of_utc, run_id)` ascending.
- `report_paths` is sorted in the same order as `run_ids`.
- `top_n` is the effective integer top-N limit.
- `max_runs` is the effective integer limit or `null`.

### `summary`

Shape:

```json
{
  "total_structural": 0,
  "total_execution_attempted": 0,
  "total_executable": 0,
  "total_direct_ok": 0,
  "total_tranche_ok": 0,
  "total_marginal": 0,
  "total_failed": 0,
  "total_unknown_execution": 0,
  "total_unexpected_execution_state": 0,
  "total_not_attempted": 0,
  "overall_executable_rate": null,
  "overall_direct_ok_rate": null,
  "overall_tranche_ok_rate": null,
  "overall_marginal_rate": null,
  "overall_failed_rate": null,
  "overall_unknown_execution_rate": null,
  "overall_unexpected_execution_state_rate": null,
  "overall_not_attempted_rate": null
}
```

Rules:

- Summary totals aggregate all analyzed reports over the T24 structural candidate base.
- Rate denominators are `total_structural`.
- Denominator `0` yields `null`.

### `by_run`

Shape:

```json
{
  "<run_id>": {
    "daily_bar_id": "2026-05-01",
    "as_of_utc": "2026-05-02T01:23:45Z",
    "report_path": "reports/runs/2026/05/01/<run_id>/report.json",
    "structural": 0,
    "execution_attempted": 0,
    "executable": 0,
    "direct_ok": 0,
    "tranche_ok": 0,
    "marginal": 0,
    "failed": 0,
    "unknown_execution": 0,
    "unexpected_execution_state": 0,
    "not_attempted": 0,
    "executable_rate": null,
    "direct_ok_rate": null,
    "tranche_ok_rate": null,
    "marginal_rate": null,
    "failed_rate": null,
    "unknown_execution_rate": null,
    "unexpected_execution_state_rate": null,
    "not_attempted_rate": null
  }
}
```

Rules:

- One entry per analyzed run.
- Keys are run IDs.
- Values include all common count keys and all common rate keys.
- Ordering in serialized JSON must be deterministic. Prefer sorting by `(daily_bar_id, as_of_utc, run_id)` ascending.

### `by_bucket`

Shape:

```json
{
  "confirmed_candidates": {
    "structural": 0,
    "execution_attempted": 0,
    "executable": 0,
    "direct_ok": 0,
    "tranche_ok": 0,
    "marginal": 0,
    "failed": 0,
    "unknown_execution": 0,
    "unexpected_execution_state": 0,
    "not_attempted": 0,
    "executable_rate": null,
    "direct_ok_rate": null,
    "tranche_ok_rate": null,
    "marginal_rate": null,
    "failed_rate": null,
    "unknown_execution_rate": null,
    "unexpected_execution_state_rate": null,
    "not_attempted_rate": null
  },
  "early_candidates": {},
  "watchlist": {},
  "late_monitor": {}
}
```

Rules:

- All four active buckets must be present even if all counts are zero.
- Each bucket value must contain all common count keys and all common rate keys.
- Do not include `discarded` in T25 analysis.

### `by_universe_category`

Shape:

```json
{
  "classic_crypto": {
    "structural": 0,
    "execution_attempted": 0,
    "executable": 0,
    "direct_ok": 0,
    "tranche_ok": 0,
    "marginal": 0,
    "failed": 0,
    "unknown_execution": 0,
    "unexpected_execution_state": 0,
    "not_attempted": 0,
    "executable_rate": null,
    "direct_ok_rate": null,
    "tranche_ok_rate": null,
    "marginal_rate": null,
    "failed_rate": null,
    "unknown_execution_rate": null,
    "unexpected_execution_state_rate": null,
    "not_attempted_rate": null
  }
}
```

Rules:

- Category map is sparse.
- Missing category means count `0`, not schema error.
- If a category is present, its value must contain all common count keys and all common rate keys.
- Category ordering must be deterministic. Prefer alphabetical order.

### `by_bucket_and_category`

Shape:

```json
{
  "confirmed_candidates": {
    "classic_crypto": {
      "structural": 0,
      "execution_attempted": 0,
      "executable": 0,
      "direct_ok": 0,
      "tranche_ok": 0,
      "marginal": 0,
      "failed": 0,
      "unknown_execution": 0,
      "unexpected_execution_state": 0,
      "not_attempted": 0,
      "executable_rate": null,
      "direct_ok_rate": null,
      "tranche_ok_rate": null,
      "marginal_rate": null,
      "failed_rate": null,
      "unknown_execution_rate": null,
      "unexpected_execution_state_rate": null,
      "not_attempted_rate": null
    }
  },
  "early_candidates": {},
  "watchlist": {},
  "late_monitor": {}
}
```

Rules:

- All four active buckets must be present.
- Category maps within each bucket are sparse.
- Missing category means count `0`, not schema error.
- If a category is present, its value must contain all common count keys and all common rate keys.
- Do not include `discarded`.

### `execution_reason_counts`

Shape:

```json
{
  "depth_1pct_insufficient": 0,
  "UNKNOWN_ORDERBOOK_STALE": 0,
  "DIRECT_OK_SPREAD_DEPTH": 0,
  "__null__": 0
}
```

Rules:

- Count `execution_reason_raw` from T24 segment items.
- Use `__null__` as the sentinel key for `null` reason.
- Count reasons only for actual execution outcome items:
  - `direct_ok`
  - `tranche_ok`
  - `marginal`
  - `failed`
  - `unknown_execution`
  - `unexpected_execution_state`
- Do not count `not_attempted` reasons.
- Reason keys are sparse and deterministic. Prefer alphabetical order with `__null__` included in normal lexical order.

### `execution_reason_counts_by_bucket`

Shape:

```json
{
  "confirmed_candidates": {
    "depth_1pct_insufficient": 0,
    "__null__": 0
  },
  "early_candidates": {},
  "watchlist": {},
  "late_monitor": {}
}
```

Rules:

- All four active buckets must be present.
- Reason maps are sparse.
- Do not include `discarded`.
- Do not count `not_attempted` reasons.

### `execution_reason_counts_by_universe_category`

Shape:

```json
{
  "classic_crypto": {
    "depth_1pct_insufficient": 0,
    "UNKNOWN_ORDERBOOK_STALE": 0
  }
}
```

Rules:

- Category map is sparse.
- Reason maps are sparse.
- Missing category means no observed reasons for that category, not schema error.
- Do not count `not_attempted` reasons.

### `over_time`

Shape:

```json
{
  "confirmed_structural_vs_executable": [
    {
      "run_id": "daily-2026-05-01-abc",
      "daily_bar_id": "2026-05-01",
      "as_of_utc": "2026-05-02T01:23:45Z",
      "structural": 0,
      "executable": 0,
      "direct_ok": 0,
      "tranche_ok": 0,
      "marginal": 0,
      "failed": 0,
      "unknown_execution": 0,
      "unexpected_execution_state": 0,
      "not_attempted": 0,
      "executable_rate": null
    }
  ],
  "early_structural_vs_executable": []
}
```

Rules:

- Include exactly these two lists:
  - `confirmed_structural_vs_executable`
  - `early_structural_vs_executable`
- One item per analyzed run per list.
- `confirmed_structural_vs_executable` uses the `confirmed_candidates` bucket counts.
- `early_structural_vs_executable` uses the `early_candidates` bucket counts.
- Sort each list by `(daily_bar_id, as_of_utc, run_id)` ascending.
- `executable_rate` denominator is `structural`.
- If `structural == 0`, `executable_rate` is `null`.
- Each `over_time` item includes only `executable_rate` as a rate field. Do not add additional rate fields to `over_time` items.

### `top_repeated_symbols`

Shape:

```json
{
  "failed": [
    {
      "symbol": "XYZUSDT",
      "run_count": 3,
      "runs": [
        {
          "run_id": "daily-2026-05-01-abc",
          "daily_bar_id": "2026-05-01",
          "bucket": "confirmed_candidates",
          "universe_category": "classic_crypto",
          "execution_reason_raw": "depth_1pct_insufficient"
        }
      ]
    }
  ],
  "marginal": [],
  "unknown_execution": [],
  "direct_ok": [],
  "tranche_ok": [],
  "unexpected_execution_state": []
}
```

Rules:

- Include exactly these top-level outcome lists:
  - `failed`
  - `marginal`
  - `unknown_execution`
  - `direct_ok`
  - `tranche_ok`
  - `unexpected_execution_state`
- Do not include `not_attempted` in top repeated symbols.
- Each list is capped at `--top-n` items.
- Sort each outcome list by:
  1. `run_count` descending
  2. `symbol` ascending
- `run_count` counts distinct runs, not raw occurrences.
- If the same symbol appears more than once within the same run for the same outcome, count that run only once for that symbol/outcome.
- Sort each item's `runs` array by:
  1. `daily_bar_id` ascending
  2. `run_id` ascending
  3. `bucket` ascending
- `execution_reason_raw` must be the raw reason string or `null`. Do not use `__null__` inside run items; `__null__` is only for reason-count map keys.

## Source of symbol-level repeated outcomes

Use `execution_aware_candidate_segments` from T24 for symbol-level repeated outcome analysis.

Expected segment families:

- confirmed and early full segment lists:
  - `confirmed_direct_ok`
  - `confirmed_tranche_ok`
  - `confirmed_marginal`
  - `confirmed_failed`
  - `confirmed_unknown_execution`
  - `confirmed_unexpected_execution_state`
  - `early_direct_ok`
  - `early_tranche_ok`
  - `early_marginal`
  - `early_failed`
  - `early_unknown_execution`
  - `early_unexpected_execution_state`
- watchlist and late-monitor pass-only lists:
  - `watchlist_direct_ok`
  - `watchlist_tranche_ok`
  - `late_monitor_direct_ok`
  - `late_monitor_tranche_ok`

Do not invent missing T24 segment lists for watchlist or late_monitor marginal/failed/unknown/not-attempted outcomes. T24 intentionally does not emit full watchlist/late-monitor segment lists for those outcomes. Counts by bucket still cover those outcomes; repeated-symbol analysis only includes symbol-level outcomes available in T24 segments.

If a required T24 segment list for confirmed/early outcomes is missing, fail clearly. If optional pass-only watchlist/late_monitor lists are missing in a pre-final T24 fixture, fail clearly for current T25 because T25 requires T24 report fields as deployed.

## Markdown output contract

The Markdown output is a human-readable auxiliary summary. JSON is the canonical machine-readable analysis output.

The Markdown must include at least:

```markdown
# Execution Depth Analysis

## Summary

## By Bucket

## By Universe Category

## Execution Reason Counts

## Confirmed Candidates Over Time

## Early Candidates Over Time

## Top Repeated Failed Symbols

## Top Repeated Marginal Symbols

## Top Repeated Unknown Execution Symbols

## Top Repeated Direct OK Symbols

## Top Repeated Tranche OK Symbols

## Top Repeated Unexpected Execution State Symbols
```

Markdown tables should be deterministic and compact. Avoid dumping full raw JSON into Markdown.

## Determinism and ordering

For identical input files and identical CLI arguments, JSON and Markdown outputs must be byte-stable except for `generated_at_utc`.

Ordering rules:

- Runs: `(daily_bar_id, as_of_utc, run_id)` ascending in final outputs.
- Buckets: `confirmed_candidates`, `early_candidates`, `watchlist`, `late_monitor`.
- Categories: alphabetical order.
- Reason keys: alphabetical order.
- Top repeated symbol lists: `run_count` descending, then `symbol` ascending.
- Per-symbol run arrays: `daily_bar_id` ascending, `run_id` ascending, `bucket` ascending.

Do not rely on dict/set iteration order for semantic ordering unless the dict was explicitly built in the required order.

## Nullability and numeric robustness

- Rate fields are nullable. `null` means no valid denominator (`structural == 0`) and must not be coerced to `0.0`.
- Count fields are non-null integers `>= 0`.
- Bool is not a valid count.
- `0` and `0.0` are valid numeric values and must not be treated as missing.
- Non-finite numeric values (`NaN`, `inf`, `-inf`) must not appear in outputs.
- JSON must be written in strict JSON-compatible form. Use `json.dumps(..., allow_nan=False)` or an equivalent guard.

## Error handling

Fail clearly for:

- no reports found,
- malformed JSON input,
- missing required T24 blocks,
- missing required report identity fields,
- unsupported explicit `--run-dir` scan mode,
- invalid `--top-n`,
- invalid `--max-runs`,
- output path under forbidden roots,
- present count blocks with non-integer / negative / bool counts,
- present rate fields that are non-finite if consumed from input.

Do not silently skip malformed explicit `--run-dir` inputs.

For recursive discovery under `--reports-root`, the script may skip non-daily reports with a warning summary, but it must not silently skip malformed daily T24 reports.

## Invariants

1. T25 reads T24 `report.json` fields only.
2. T25 does not read `symbol_diagnostics.jsonl.gz`.
3. T25 does not read live SQLite.
4. T25 does not call MEXC or any live external API.
5. T25 does not write under `reports/analysis`.
6. T25 does not write under `reports/runs/**`.
7. T25 default outputs are under `reports/aux/`.
8. All four active buckets are present in `by_bucket`, `by_bucket_and_category`, and reason-by-bucket maps.
9. `discarded` is not included in T25 bucket analysis.
10. Sparse category maps are valid; missing category means `0`, not schema error.
11. Existing category blocks contain all required common count/rate keys where the block shape requires them.
12. `unknown_execution` is not collapsed into `failed`.
13. `marginal` is not collapsed into `failed`.
14. `unexpected_execution_state` is not collapsed into any normal outcome.
15. `not_attempted` is not counted as a reason outcome.
16. All rates use `structural` as denominator unless explicitly stated otherwise.
17. Denominator `0` produces `null` rate.
18. `0` numerator with positive denominator produces `0.0` rate.
19. Repeated-symbol `run_count` counts distinct runs only.
20. Output JSON contains no `NaN`, `Infinity`, or `-Infinity`.
21. At identical input and config, ordering is deterministic.

## Tests required

Add tests covering at least the following.

### 1. Happy path with two T24 reports

Given two minimal T24-compatible daily reports:

- aggregate summary counts correctly,
- aggregate `by_run` correctly,
- aggregate `by_bucket` correctly,
- aggregate `by_universe_category` correctly,
- aggregate `by_bucket_and_category` correctly,
- write JSON and Markdown to `reports/aux/`.

### 2. Missing T24 block

If a report is missing one of the required T24 blocks, the script fails with a clear message and does not fall back to diagnostics.

### 3. No diagnostics fallback

Provide a fixture with `symbol_diagnostics.jsonl.gz` present but missing T24 fields in `report.json`. The script must still fail because T25 requires T24 fields.

### 4. Sparse categories

A report with only `classic_crypto` in category maps must aggregate without requiring every T23 category key.

Missing categories must be treated as zero in aggregate logic, not as schema errors.

### 5. `by_bucket` full shape

The output `by_bucket` must contain exactly the four active buckets and all common count/rate keys for each bucket, even when counts are zero.

### 6. `by_universe_category` full present-category shape

For every category present in output, assert all common count/rate keys exist.

### 7. `by_bucket_and_category` full bucket shape

The output must contain all four active buckets. For each present category under a bucket, assert all common count/rate keys exist.

### 8. `over_time` shape and sorting

Assert:

- `confirmed_structural_vs_executable` exists,
- `early_structural_vs_executable` exists,
- each list contains one item per analyzed run,
- items are sorted by `(daily_bar_id, as_of_utc, run_id)` ascending,
- `executable_rate` is `null` when structural count is zero.

### 9. Reason counts

Use reports containing reasons such as:

- `depth_1pct_insufficient`,
- `UNKNOWN_ORDERBOOK_STALE`,
- `DIRECT_OK_SPREAD_DEPTH`,
- `null` reason.

Assert:

- global reason counts are correct,
- by-bucket reason counts are correct,
- by-category reason counts are correct,
- null reason is represented by `__null__` in reason-count map keys,
- not-attempted symbols do not contribute to reason counts.

### 10. Top repeated symbols

Use repeated symbols across multiple runs.

Assert:

- output item shape is correct,
- `run_count` counts distinct runs,
- duplicate occurrences inside one run do not inflate `run_count`,
- each list is capped by `--top-n`,
- top-list sorting is `run_count desc`, then `symbol asc`,
- per-symbol `runs` arrays are sorted by `daily_bar_id`, `run_id`, `bucket`.

### 11. `--top-n` validation

Assert invalid values fail clearly:

- `0`,
- negative integer,
- non-integer string.

### 12. `--max-runs` behavior

Given more reports than `max_runs`, assert:

- newest runs are selected by `(daily_bar_id, as_of_utc, run_id)` descending,
- final output ordering remains ascending according to output ordering rules.

### 13. Zero denominator rates

If `structural == 0`, all rates for that block are `null`.

If `structural > 0` and numerator is `0`, the rate is `0.0`.

### 14. Output path policy

Assert default output goes to `reports/aux/`.

Assert these paths are rejected:

- `reports/analysis/...`,
- `reports/runs/...`,
- `snapshots/runs/...`.

### 15. Strict JSON / non-finite guard

Assert output serialization rejects or prevents:

- `NaN`,
- `Infinity`,
- `-Infinity`.

Use strict JSON dumping (`allow_nan=False`) or equivalent validation.

### 16. Unexpected execution state aggregation

Given T24 reports containing `unexpected_execution_state` counts and segments, assert they are aggregated under `unexpected_execution_state` and not under fail, unknown, marginal, or executable.

## Acceptance criteria

T25 is complete when:

- `scripts/analyze_execution_depth_shadow_live.py` exists and is locally executable.
- The script reads T24 daily `report.json` fields only.
- The script does not read diagnostics, SQLite, OHLCV history, orderbooks, or live APIs.
- Missing T24 blocks produce a clear error.
- JSON output is written to `reports/aux/execution_depth_analysis.json` by default.
- Markdown output is written to `reports/aux/execution_depth_analysis.md` by default.
- The script rejects forbidden output roots.
- JSON output matches the defined top-level contract.
- `by_run`, `by_bucket`, `by_universe_category`, `by_bucket_and_category`, `over_time`, and `top_repeated_symbols` have fully specified shapes.
- Reason counts are produced globally, by bucket, and by universe category.
- Sparse categories are tolerated.
- All rate rules are implemented.
- `--top-n` and `--max-runs` are implemented and validated.
- Repeated-symbol logic is deterministic and deduplicates by distinct run.
- Outputs are strict JSON-safe and contain no non-finite numeric values.
- Required tests pass.
- Existing T13/T19/T23/T24 output/report tests remain green.

## Codex implementation guidance

Keep this implementation small and local.

Recommended structure inside the script:

- `parse_args(...)`
- `discover_report_paths(...)`
- `load_report(...)`
- `validate_t24_report(...)`
- `empty_count_block(...)`
- `add_count_block(...)`
- `rate_block(...)`
- `aggregate_reports(...)`
- `build_reason_counts(...)`
- `build_top_repeated_symbols(...)`
- `write_json_strict(...)`
- `write_markdown(...)`
- `main(...)`

This guidance is not a requirement for exact function names, but the implementation should stay readable and testable. Prefer pure helpers that can be unit-tested without invoking subprocesses.

## Codex failure modes to avoid

- Do not add a diagnostics fallback.
- Do not read `symbol_diagnostics.jsonl.gz`.
- Do not reimplement T24 classification from raw execution fields.
- Do not alter T24 report generation.
- Do not change execution thresholds.
- Do not change execution grading.
- Do not add workflow-required integration.
- Do not write to `reports/analysis`.
- Do not write to `reports/runs/**`.
- Do not treat missing sparse categories as errors.
- Do not treat valid `0` counts as missing.
- Do not convert denominator-zero rates to `0.0`.
- Do not hide `unexpected_execution_state` under normal outcomes.
- Do not emit non-strict JSON numbers.

## Self-review checklist before handoff

Before marking this ticket complete, verify:

- The PR changes are limited to the new script, tests, and any minimal docs update if needed.
- No runtime scanner behavior changed.
- No report writer behavior changed.
- No decision/execution/ranking behavior changed.
- No forbidden output roots are used.
- Missing T24 fields fail clearly.
- Top repeated symbol results are deterministic.
- Reason counts use `__null__` only as a map key, not inside run item payloads.
- All new JSON blocks have fully specified shapes.
- Tests cover malformed inputs and path policy, not only the happy path.
