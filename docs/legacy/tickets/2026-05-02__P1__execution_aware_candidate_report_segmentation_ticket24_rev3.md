> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# T24: Add Execution-Aware Candidate Report Segmentation

## Metadata

- Ticket ID: T24
- Title: Add Execution-Aware Candidate Report Segmentation
- Status: Ready for implementation
- Target PR size: One focused PR
- Language: Implementation and code artifacts in English
- Primary mode affected: Daily Discovery / Shadow-Live daily reporting

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
   - `scanner/execution/grading.py`
   - `scanner/execution/adapter.py`
   - `scanner/universe/classification.py`
   - `docs/canonical/REPORTS.md`
5. Existing implemented contracts from T13, T21, T21.1, T22, and T23.

This ticket must not create a second competing reporting truth. It extends the canonical daily `report.json` additively and documents the added fields in `docs/canonical/REPORTS.md`.

Repo-reality clarification for this ticket: `tranche_ok` is an actual current execution status in `scanner/execution/grading.py`. The current grader maps legacy `TRANCHE_OK` to `execution_status_raw == "tranche_ok"`, maps its reason through `TRANCHE_OK_SPREAD_DEPTH`, and currently sets `execution_pass=True` for `direct_ok` and `tranche_ok`. T24 must therefore report `tranche_ok` explicitly rather than treating it as dead or unknown infrastructure.

## Current context

Daily Shadow-Live runs are stable and produce full diagnostics and reports. T23 added universe classification and candidate segmentation while preserving raw candidate buckets. Execution is now the main operational bottleneck: many structurally interesting symbols fail or remain unknown on execution, especially due to depth and stale orderbook conditions.

The current report shows structural candidate buckets and T23 tradable/excluded candidate segmentation, but it does not make execution usability immediately visible at the candidate-view level. Operators currently need to inspect diagnostics manually to determine whether a structurally interesting candidate is actually executable.

This ticket adds execution-aware report views for the daily report only. It does not change execution thresholds, execution grading, decision bucket assignment, ranking, evaluation metrics, or intraday carry-forward behavior.

## Goal

Add execution-aware candidate report segmentation to canonical daily run reports so that the report immediately shows which structurally visible candidates are:

- executable,
- direct OK,
- tranche OK,
- marginal,
- failed,
- unknown execution,
- not attempted,
- or unexpected / internally inconsistent.

The new report blocks must be additive and must preserve all existing raw and T23 candidate-facing report outputs.

## Non-goals / out of scope

Do not implement any of the following in this ticket:

- No execution threshold changes.
- No execution grader changes.
- No execution adapter behavior changes.
- No `DecisionBucket` assignment changes.
- No `priority_score` changes.
- No ranking changes.
- No universe classification rule changes.
- No T23 candidate exclusion rule changes.
- No evaluation replay or evaluation metric changes.
- No intraday carry-forward work.
- No OHLCV replay or orderbook replay.
- No multi-run analysis script. That belongs to T25.
- No workflow integration changes.
- No reports-side manifest files.
- No output under `reports/analysis`.
- No report segmentation module refactor.
- Do not move `_build_ticket23_report_payload(...)` out of `scanner/runners/daily.py`.
- Do not introduce a new output/report segmentation module in this ticket.

## Required repo changes

### 1. Add a daily execution-aware report payload builder

Add a new helper in `scanner/runners/daily.py`, next to `_build_ticket23_report_payload(...)`:

```python
def _build_execution_aware_report_payload(
    *,
    ranked: list[RankedDecision],
    diagnostics: list[dict[str, Any]],
) -> dict[str, Any]:
    ...
```

The function must build additive report blocks from the final per-symbol diagnostics and final ranked decisions after the post-execution decision pass.

It must not mutate `ranked`, `diagnostics`, decision objects, or diagnostics records.

It must use T23 candidate-visible/tradable semantics as the structural base for candidate-facing segments:

- `structural` means: symbol is in an active candidate bucket and `diagnostics[*].universe.candidate_excluded is False`.
- Active candidate buckets are exactly:
  - `confirmed_candidates`
  - `early_candidates`
  - `watchlist`
  - `late_monitor`
- Symbols classified as `stable_or_cash_proxy` or `leveraged_or_margin_token` remain visible in raw report structures but must not appear in execution-aware candidate-facing structural/executable segments when `candidate_excluded is True`.

### 2. Merge T23 and T24 additive payloads into `extra_report_fields`

In `run_daily_scan(...)`, build both additive payloads and pass a merged dict into `builder.write_run_report(...)`:

```python
ticket23_payload = _build_ticket23_report_payload(ranked=ranked, diagnostics=diagnostics)
execution_aware_payload = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)
extra_report_fields = {**ticket23_payload, **execution_aware_payload}
```

The exact variable names may differ, but the behavior must be equivalent.

Do not replace or rename existing T23 fields.

### 3. Add documentation to `docs/canonical/REPORTS.md`

Extend `docs/canonical/REPORTS.md` with a short additive section for T24.

The documentation must state:

- T24 adds additive blocks only.
- Existing `counts_by_bucket`, `symbol_lists`, `universe_classification`, and `candidate_segments` remain backward-compatible.
- Execution-aware structural candidate views are based on T23 candidate-visible/tradable semantics, not raw buckets.
- `execution_status_raw` values recognized by reporting are:
  - `direct_ok`
  - `tranche_ok`
  - `marginal`
  - `fail`
  - `unknown`
  - `null` for not-attempted symbols
- For valid current grader output, `execution_pass=true` means executable and currently corresponds to `direct_ok` or `tranche_ok`. Any contradictory combination must be surfaced as `unexpected_execution_state`, not silently accepted.
- `marginal`, `fail`, `unknown`, not-attempted, and unexpected execution states are visible but not executable.

## New report fields

Add the following top-level fields to canonical daily `reports/runs/**/report.json` and therefore to `reports/index/latest_daily.json` and `reports/daily/**/report.json` when `write_daily_report(report)` is called:

```json
{
  "execution_aware_summary": {},
  "execution_counts_by_bucket": {},
  "execution_counts_by_universe_category": {},
  "execution_counts_by_bucket_and_category": {},
  "execution_aware_candidate_segments": {}
}
```

These fields must be absent only for non-daily legacy/backward reports that were produced before this ticket. Current daily runs after T24 must include them.

## Execution status semantics

Use only the following reporting statuses:

### `direct_ok`

`direct_ok` means `execution_status_raw == "direct_ok"`. It is executable. It must be counted under both `direct_ok` and `executable`.

### `tranche_ok`

`tranche_ok` means `execution_status_raw == "tranche_ok"`. It is executable. It must be counted under both `tranche_ok` and `executable`.

### `marginal`

`marginal` means `execution_status_raw == "marginal"` with `execution_pass is false`. It is not executable. If a symbol has `execution_status_raw == "marginal"` with `execution_pass is null` or `execution_pass is true`, that is an invalid combination and must be counted as `unexpected_execution_state`, not as marginal and not as executable.

### `fail`

`fail` means `execution_status_raw == "fail"`. It is a negative execution evaluation. It must be counted as failed and must not be counted as unknown or executable.

### `unknown`

`unknown` means `execution_status_raw == "unknown"`. It indicates execution was attempted but no reliable positive/negative execution evaluation is available, for example stale, missing, malformed, or failed orderbook fetch conditions. It must be counted as `unknown_execution`, not as failed and not as executable.

### `null` / not attempted

`execution_status_raw == null` with `execution_attempted == false` means execution was not attempted for that symbol in this run. It must be counted as `not_attempted`, not as failed and not as unknown execution.

### Invalid combinations

Do not silently reinterpret invalid combinations. At report-segmentation level, classify defensively and preserve visibility:

- For valid current grader output, only `execution_status_raw in {"direct_ok", "tranche_ok"}` with `execution_pass is true` counts as `executable`.
- If `execution_pass is true` but `execution_status_raw` is not `direct_ok` or `tranche_ok`, this is an internally inconsistent execution state. Count it as `unexpected_execution_state`, do not count it as `executable`, and preserve the raw status and `execution_pass` value in the emitted item.
- If `execution_status_raw in {"direct_ok", "tranche_ok"}` but `execution_pass is not true`, this is also an internally inconsistent execution state. Count it as `unexpected_execution_state`, do not count it as `executable`, and preserve the raw status and `execution_pass` value in the emitted item.
- If `execution_status_raw == "marginal"` but `execution_pass is not false`, this is also an internally inconsistent execution state. Count it as `unexpected_execution_state`, not as `marginal`, and preserve the raw status and `execution_pass` value in the emitted item.
- If `execution_attempted is true` and `execution_status_raw is null`, count it as `unknown_execution`.
- If `execution_attempted is false`, count it as `not_attempted` regardless of raw status; tests should cover the normal null-status case.

Unexpected execution states must be visible in counts and in confirmed/early segment lists. They are not normal business outcomes and must not be collapsed into `marginal`, `fail`, `unknown_execution`, or `executable`.

`execution_pass` is nullable. `null` means not reliably evaluable / not attempted and must not be implicitly coerced to `false`.

Not evaluable / not evaluated and fachlich negative execution evaluation are separate states and must remain separate in the report.

## Field shapes

### `execution_aware_summary`

Shape:

```json
{
  "total_structural_candidates": 0,
  "total_execution_attempted": 0,
  "total_executable": 0,
  "total_unexpected_execution_state": 0,
  "total_direct_ok": 0,
  "total_tranche_ok": 0,
  "total_marginal": 0,
  "total_failed": 0,
  "total_unknown_execution": 0,
  "total_not_attempted": 0
}
```

All counts must be integers `>= 0`.

The summary counts use the T23 candidate-visible/tradable structural base across active candidate buckets only. They must not include T23-excluded stable/cash proxies or leveraged/margin tokens.

### `execution_counts_by_bucket`

Shape:

```json
{
  "confirmed_candidates": {
    "structural": 0,
    "execution_attempted": 0,
    "executable": 0,
    "unexpected_execution_state": 0,
    "direct_ok": 0,
    "tranche_ok": 0,
    "marginal": 0,
    "failed": 0,
    "unknown_execution": 0,
    "not_attempted": 0
  },
  "early_candidates": { },
  "watchlist": { },
  "late_monitor": { }
}
```

All four active buckets must be present even when counts are zero. Each bucket must contain the same count keys.

### `execution_counts_by_universe_category`

Shape:

```json
{
  "classic_crypto": {
    "structural": 0,
    "execution_attempted": 0,
    "executable": 0,
    "unexpected_execution_state": 0,
    "direct_ok": 0,
    "tranche_ok": 0,
    "marginal": 0,
    "failed": 0,
    "unknown_execution": 0,
    "not_attempted": 0
  }
}
```

Use observed universe categories from diagnostics. Do not invent a second category taxonomy.

This count block uses the same T23 candidate-visible/tradable structural base. T23-excluded symbols must not contribute to these structural/execution-aware counts.

### `execution_counts_by_bucket_and_category`

Shape:

```json
{
  "confirmed_candidates": {
    "classic_crypto": {
      "structural": 0,
      "execution_attempted": 0,
      "executable": 0,
      "unexpected_execution_state": 0,
      "direct_ok": 0,
      "tranche_ok": 0,
      "marginal": 0,
      "failed": 0,
      "unknown_execution": 0,
      "not_attempted": 0
    }
  },
  "early_candidates": {},
  "watchlist": {},
  "late_monitor": {}
}
```

All active buckets must be present. Category entries may be sparse and only include observed non-excluded categories.

### `execution_aware_candidate_segments`

Shape:

```json
{
  "confirmed_structural": [],
  "confirmed_executable": [],
  "confirmed_unexpected_execution_state": [],
  "confirmed_direct_ok": [],
  "confirmed_tranche_ok": [],
  "confirmed_marginal": [],
  "confirmed_failed": [],
  "confirmed_unknown_execution": [],
  "confirmed_not_attempted": [],

  "early_structural": [],
  "early_executable": [],
  "early_unexpected_execution_state": [],
  "early_direct_ok": [],
  "early_tranche_ok": [],
  "early_marginal": [],
  "early_failed": [],
  "early_unknown_execution": [],
  "early_not_attempted": [],

  "watchlist_direct_ok": [],
  "watchlist_tranche_ok": [],
  "late_monitor_direct_ok": [],
  "late_monitor_tranche_ok": []
}
```

Do not add full watchlist/late marginal/fail/unknown/not-attempted/unexpected segment lists in this ticket. Watchlist and late-monitor execution-aware segment lists are intentionally limited to executable operational highlights.

This asymmetry is intentional: `execution_counts_by_bucket` contains the full count taxonomy for all four active buckets, but `execution_aware_candidate_segments` exposes full status segment lists only for `confirmed_candidates` and `early_candidates`. Codex must not add the "missing" watchlist/late marginal, failed, unknown, not-attempted, or unexpected segment lists in this ticket.

Each item in these lists must be a compact object with at least:

```json
{
  "symbol": "BTCUSDT",
  "decision_bucket": "confirmed_candidates",
  "priority_score": 0.0,
  "execution_status_raw": "direct_ok",
  "execution_reason_raw": "DIRECT_OK_SPREAD_DEPTH",
  "execution_pass": true,
  "universe_category": "classic_crypto",
  "universe_category_confidence": "low",
  "universe_category_reason": "...",
  "candidate_excluded": false,
  "candidate_exclusion_reason": null
}
```

Optional additional compact fields are allowed only if they are already available in diagnostics and do not create a new semantic contract. Do not add nested full diagnostics blocks to segment items.

## Deterministic ordering

For all new segment lists, ordering must be deterministic:

1. `priority_score` descending.
2. `symbol` ascending as tie-breaker.

`priority_score == 0` and `priority_score == 0.0` are valid values and must not be treated as missing.

If `priority_score` is missing or not a finite numeric value, sort that item after finite numeric priorities and then by symbol. Do not emit `NaN`, `inf`, or `-inf` into report JSON.

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid / not reliably evaluable inputs and must not be passed through as numeric-looking outputs.

For identical input and identical config, selection, ordering, statuses, counts, and emitted report fields must be identical.

## Invariants

T24 must preserve all of the following:

1. Existing raw `counts_by_bucket` remains unchanged.
2. Existing raw `symbol_lists` remains unchanged.
3. Existing T23 `universe_classification` remains unchanged except for normal deterministic ordering if already present.
4. Existing T23 `candidate_segments.tradable_buckets` remains unchanged.
5. Existing T23 `candidate_segments.excluded_candidate_buckets` remains unchanged.
6. Existing T23 `candidate_segments.segmented_tradable_buckets` remains unchanged.
7. New execution-aware fields are additive.
8. `reports/runs/**/report.json` for daily runs contains the new fields.
9. `reports/index/latest_daily.json` contains the new fields after a successful daily report write.
10. `reports/daily/**/report.json` contains the new fields when daily convenience report writing is used.
11. `confirmed_executable` is a subset of `confirmed_structural`.
12. `confirmed_direct_ok` is a subset of `confirmed_executable`.
13. `confirmed_tranche_ok` is a subset of `confirmed_executable`.
14. `early_executable` is a subset of `early_structural`.
15. `early_direct_ok` is a subset of `early_executable`.
16. `early_tranche_ok` is a subset of `early_executable`.
17. `confirmed_unexpected_execution_state` is a subset of `confirmed_structural`, and `early_unexpected_execution_state` is a subset of `early_structural`.
18. `marginal`, `fail`, `unknown_execution`, `not_attempted`, and `unexpected_execution_state` are visible but not executable under the current expected execution contract.
19. Invalid combinations are counted as `unexpected_execution_state` and are not silently counted as `executable`.
20. `unknown_execution` is not counted as `failed`.
21. `failed` is not counted as `unknown_execution`.
22. `marginal` is not counted as `failed`.
23. `null` execution fields are not coerced into `false` execution outcomes.
24. T23-excluded symbols are not present in execution-aware candidate-facing structural/executable segments.
25. No report output is written to `reports/analysis`.
26. No manifest copy is written under `reports/runs/**`.

## Backward compatibility

The existing report contract from T13/T22/T23 must continue to work:

- Required top-level report fields remain present.
- Existing code reading `counts_by_bucket` and `symbol_lists` must not break.
- Existing T23 tests for universe classification and candidate segmentation must continue to pass.
- Existing diagnostics validation must continue to pass.
- `scan_mode` remains exactly `daily` or `intraday`; do not introduce `daily_discovery` or `intraday_promotion` into report/diagnostics `scan_mode`.
- `daily_bar_id` remains canonical `YYYY-MM-DD`.
- `intraday_bar_id` remains `null` for daily reports.
- Manifest remains canonical only under `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` and is referenced by `manifest_path`.

## Implementation guidance

Suggested implementation approach:

1. Build `diag_by_symbol = {diag["symbol"]: diag}` from validated diagnostics.
2. Build `bucket_by_symbol` from final `ranked` decisions.
3. Iterate over final ranked symbols to preserve a deterministic base order, but explicitly sort emitted lists by priority descending and symbol ascending.
4. For each symbol:
   - Determine final bucket from `ranked` / final decision.
   - Skip symbols outside active buckets.
   - Read `universe` from diagnostics.
   - Exclude from execution-aware structural/candidate-facing segments if `universe.candidate_excluded is True`.
   - Read execution fields from diagnostics:
     - `execution_attempted`
     - `execution_status_raw`
     - `execution_reason_raw`
     - `execution_pass`
   - Build a compact item.
   - Add to count blocks and segment lists according to the definitions above.
5. Return only the new T24 top-level fields from `_build_execution_aware_report_payload(...)`.
6. Merge that return value with the existing T23 payload in `extra_report_fields`.
7. Update `docs/canonical/REPORTS.md` with the T24 additive contract.

Do not call daily-only feature functions from any intraday path. This ticket should not touch intraday runner logic.

## Tests required

Add a new test module, for example:

- `tests/test_ticket24_execution_aware_report_segmentation.py`

Extend existing tests only if necessary. Prefer focused tests for the new helper.

### Test 1: confirmed execution status segmentation

Create ranked/diagnostics fixtures with confirmed candidates covering:

- `direct_ok`, `execution_pass=true`
- `tranche_ok`, `execution_pass=true`
- `marginal`, `execution_pass=false`
- `fail`, `execution_pass=false`
- `unknown`, `execution_pass=null`
- not attempted, `execution_attempted=false`, `execution_status_raw=null`, `execution_pass=null`
- unexpected execution state, for example `execution_status_raw="marginal"`, `execution_pass=true`

Assert:

- `confirmed_structural` contains all non-excluded confirmed fixtures.
- `confirmed_executable` contains exactly direct_ok + tranche_ok.
- `confirmed_direct_ok` contains only the direct_ok symbol.
- `confirmed_tranche_ok` contains only the tranche_ok symbol.
- `confirmed_marginal`, `confirmed_failed`, `confirmed_unknown_execution`, `confirmed_not_attempted`, and `confirmed_unexpected_execution_state` each contain the expected symbol.
- Counts match segment lengths.

### Test 2: early execution status segmentation

Repeat the same coverage for `early_candidates` at least for:

- direct_ok
- tranche_ok
- marginal
- fail
- unknown
- not attempted
- unexpected execution state

Assert the same subset invariants for early candidates, including `early_unexpected_execution_state`.

### Test 3: T23 candidate exclusions are preserved

Create stable/cash proxy and leveraged/margin token fixtures with active buckets and execution statuses.

Assert:

- They remain unaffected in existing T23 raw/excluded structures if that test path includes T23 payload.
- They do not appear in T24 execution-aware structural/executable candidate-facing segments.
- They do not contribute to `execution_aware_summary.total_structural_candidates`.

### Test 4: universe category count matrix

Create fixtures across at least:

- `classic_crypto`
- `tokenized_stock_or_etf`
- `commodity_or_index_proxy`
- `wrapped_or_synthetic_btc`
- `unknown`

Assert:

- `execution_counts_by_universe_category` counts statuses correctly.
- `execution_counts_by_bucket_and_category` counts statuses correctly per bucket.
- All active buckets are present in `execution_counts_by_bucket_and_category`.

### Test 5: deterministic ordering and zero priority

Create fixtures with equal priority and with `priority_score=0.0`.

Assert:

- `0.0` remains emitted as valid priority.
- Equal priority ties are sorted by symbol ascending.
- Missing or non-finite priority does not emit non-finite JSON values and sorts after finite priorities.

### Test 6: latest daily propagation

Use `ReportBuilder` in a temporary project root to write a daily report with T24 fields.

Assert:

- `reports/runs/YYYY/MM/DD/<run_id>/report.json` contains T24 fields.
- `reports/index/latest_daily.json` contains T24 fields after `write_daily_report(report)`.
- `reports/daily/YYYY/MM/DD/report.json` contains T24 fields.
- Existing `symbol_lists` and `counts_by_bucket` remain unchanged.

### Test 7: backward compatibility with existing T23 report segmentation

Ensure existing T23 tests still pass. If adding combined T23+T24 fixture tests, assert that:

- `candidate_segments.tradable_buckets` is byte-for-byte or value-equivalent to pre-T24 expected output.
- T24 does not alter T23 candidate exclusion logic.

## Acceptance criteria

Implementation is accepted only if all of the following are true:

1. Daily canonical `reports/runs/**/report.json` includes:
   - `execution_aware_summary`
   - `execution_counts_by_bucket`
   - `execution_counts_by_universe_category`
   - `execution_counts_by_bucket_and_category`
   - `execution_aware_candidate_segments`
2. `reports/index/latest_daily.json` includes the same T24 fields after a daily run.
3. `reports/daily/**/report.json` includes the same T24 fields when daily convenience report writing is used.
4. Existing raw buckets remain unchanged.
5. Existing T23 tradable/excluded/segmented candidate buckets remain unchanged.
6. `direct_ok` and `tranche_ok` are both visible and both counted as executable when `execution_pass=true`.
7. `marginal`, `fail`, `unknown`, not-attempted, and unexpected execution states are visible but not counted as executable under the current expected contract.
8. Invalid execution combinations are counted as `unexpected_execution_state`, not silently accepted as executable.
9. `unknown` and `fail` are never collapsed into one another.
10. `null` execution values are not coerced to `false`.
11. Valid `0` / `0.0` priorities are preserved.
12. New segment ordering is deterministic.
13. `docs/canonical/REPORTS.md` documents the T24 fields and semantics.
14. No execution thresholds, grader behavior, decision buckets, ranking, evaluation metrics, or intraday behavior are changed.
15. Tests cover count invariants, subset invariants, T23 compatibility, invalid combinations, and latest daily propagation.
16. Existing relevant tests continue to pass.

## Suggested commands for Codex validation

Run at least:

```bash
pytest tests/test_ticket24_execution_aware_report_segmentation.py
pytest tests/test_ticket23_report_segmentation.py
pytest tests/test_ticket23_universe_classification.py
pytest tests/test_ticket13_output_artifacts.py
pytest tests/test_ticket21_diagnostics_serialization.py
```

If runtime permits, also run:

```bash
pytest
```

## Explicit anti-regression checks

Before opening the PR, verify manually or with tests:

- `scanner/execution/grading.py` was not modified unless only comments were touched; preferably do not touch it.
- `scanner/execution/adapter.py` was not modified; preferably do not touch it.
- `scanner/decision/*` was not modified.
- No config default or threshold was changed.
- No new output path contains `reports/analysis`.
- No new manifest file is written under `reports/runs/**`.
- `_build_ticket23_report_payload(...)` remains in `scanner/runners/daily.py`.
- No new report segmentation module was introduced.

## Notes for future T25

T25 is intentionally not part of this ticket.

T25 must use the T24 report fields as required input for multi-run execution depth analysis. It must not reconstruct T24 semantics from `symbol_diagnostics.jsonl.gz` as a fallback. If a run report lacks the T24 fields, T25 should fail clearly and instruct the user to provide post-T24 reports.

T25 must tolerate sparse category maps from T24. `execution_counts_by_universe_category` and nested category maps in `execution_counts_by_bucket_and_category` may omit categories that were not observed in a run; T25 aggregation must treat missing category keys as zero rather than as schema failure.
