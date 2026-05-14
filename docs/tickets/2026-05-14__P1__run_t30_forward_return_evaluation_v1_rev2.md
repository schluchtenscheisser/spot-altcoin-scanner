# Run T30 Forward-Return Evaluation v1 on Shadow-Live Signal Events

**Ticket ID:** T30_FORWARD_RETURN_EVALUATION_V1  
**Priority:** P1  
**Status:** Draft for implementation  
**Date:** 2026-05-14  
**Target schema:** no diagnostics schema bump expected  
**Expected PR size:** Medium, one PR only  
**Primary owner:** Codex implementation  
**Review focus:** narrow analysis scope, T18 execution correctness, T30-Pre-2 OHLCV history usage, output determinism, no workflow integration, no new evaluation engine

---

## 1. Authoritative context

T30 is the first real Forward-Return Evaluation run on accumulated Independence Shadow-Live data.

T18 already implemented the technical evaluation machinery:

- `scanner/evaluation/replay.py`
- `scanner/evaluation/forward_returns.py`
- `scanner/evaluation/dataset_export.py`

T30-Pre-1 fixed Shadow-Live report persistence integrity and replay manifest availability.

T30-Pre-2 added candidate-scoped 1d OHLCV history generation for evaluation:

- `scripts/fetch_ohlcv_history_for_evaluation.py`
- artifact-only OHLCV history under `snapshots/history/ohlcv/timeframe=1d/...`
- no OHLCV commit to repo

This ticket does **not** replace T18 and does **not** implement a new evaluation engine. It executes the existing T18 machinery on real Shadow-Live data and produces a compact analysis note.

Authoritative references for this ticket:

1. The 7 v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `docs/canonical/SNAPSHOTS.md`.
4. `docs/canonical/REPORTS.md`.
5. `docs/AI_CONTEXT_CURRENT.md`.
6. `docs/canonical/decisions/Q1_Q2_operational_tradeability_and_stablecoin_exclusion.md`.
7. Existing T18 implementation:
   - `scanner/evaluation/replay.py`
   - `scanner/evaluation/forward_returns.py`
   - `scanner/evaluation/dataset_export.py`
8. Existing T30-Pre-2 script:
   - `scripts/fetch_ohlcv_history_for_evaluation.py`
9. Existing tests around T18/T30 preconditions.

If the current authoritative reference set, repo canonical documents, and existing code collide, the v2.1 reference set plus this ticket's explicit requirements win. Existing repo documents remain valid only where they do not conflict with this ticket.

---

## 2. Architectural decision for T30 v1

T30 v1 is a **narrow analysis execution ticket**.

It must:

1. Run the existing T18 evaluation export on real Shadow-Live data.
2. Use already available or pre-fetched T30-Pre-2 OHLCV history.
3. Produce the existing T18 export files.
4. Produce a compact, human-readable analysis note.
5. Explicitly document metric coverage and data limitations.

It must **not**:

- add scheduled evaluation automation,
- integrate into the scheduled Shadow-Live workflow,
- build a new evaluation engine,
- implement a permanent cohort framework,
- make final performance claims,
- recalibrate T_EL2/T29 thresholds.

### 2.1 Script placement

Add a manually executable script:

```text
scripts/run_t30_evaluation.py
```

The script must be runnable from repo root and must orchestrate the existing T18 export path.

### 2.2 Workflow placement

Do **not** add a scheduled workflow and do **not** add a step to `.github/workflows/independence-shadow-live.yml`.

For T30 v1, the required deliverable is the script and deterministic local/CI-compatible outputs. A later ticket may add a manual `workflow_dispatch` wrapper that runs this script and uploads outputs as CI artifacts. If such a manual evaluation workflow already exists in the repo, Codex may update only its artifact path list if strictly necessary; otherwise do not create a new workflow in this ticket.

### 2.3 Data-source expectation

T30 v1 assumes the repo/workdir already contains:

```text
snapshots/runs/**/run.manifest.json
reports/runs/**/symbol_diagnostics.jsonl.gz or report-derived diagnostics where available
snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/*.parquet
```

The OHLCV history is produced by T30-Pre-2 and remains artifact-only. T30 v1 must not fetch OHLCV itself unless explicitly invoked with an optional validation/preflight mode that only checks presence.

---

## 3. Problem statement

After T30-Pre-1 and T30-Pre-2, the project should have enough artifact-local data to run T18 on real Shadow-Live events.

However, there is not yet a simple, stable command that:

1. validates the required input roots,
2. runs `scanner.evaluation.dataset_export.run_evaluation_export(...)`,
3. checks the generated outputs,
4. summarizes metric coverage,
5. writes a compact T30 note for human review.

T30 v1 fills that gap.

This ticket is not intended to prove final strategy profitability. The current dataset is still small:

- only early Shadow-Live history is available,
- `10d` forward returns will mostly be `insufficient_future_data` for recent events,
- primary `ir1.5+` data is still thin,
- older `ir1.2`-`ir1.4` data is useful only as exploratory context.

---

## 4. Scope

### 4.1 In scope

1. Add:

```text
scripts/run_t30_evaluation.py
```

2. Run existing T18 evaluation export using:

```python
scanner.evaluation.dataset_export.run_evaluation_export(project_root=..., config=...)
```

3. Validate required input roots before running.
4. Validate generated output files after running.
5. Produce a compact analysis note:

```text
evaluation/notes/T30_forward_return_evaluation_v1.md
```

6. Produce or update a machine-readable T30 run summary:

```text
evaluation/replay/t30_run_summary.json
```

7. Keep all generated evaluation Parquet/OHLCV files artifact-only.
8. Add tests for script orchestration, missing-input handling, note generation, metric coverage summaries, and output validation.
9. Add minimal docs explaining how to run T30 v1 manually.

### 4.2 Out of scope

Do not implement any of the following in this ticket:

- Do not add a scheduled GitHub Actions workflow.
- Do not add a step to the scheduled Shadow-Live workflow.
- Do not auto-run T30 after every Shadow-Live run.
- Do not implement a new evaluation engine.
- Do not replace T18 replay or forward-return code.
- Do not fetch OHLCV from MEXC inside the T30 script.
- Do not commit generated OHLCV Parquet files.
- Do not commit generated evaluation Parquet files unless explicitly already allowed by existing repo policy; default is artifact/local output only.
- Do not change T_EL2 thresholds.
- Do not change T29 reduced-size thresholds.
- Do not change Q1/Q2 operational tradeability semantics.
- Do not implement final `ir1.5+` vs historical cohort performance claims as a permanent framework.
- Do not create final investment-signal conclusions from the small v1 dataset.
- Do not write or modify trading/order-execution code.

---

## 5. Required script contract

Add:

```text
scripts/run_t30_evaluation.py
```

The script must be executable from repo root.

### 5.1 Required CLI arguments

Implement these arguments with these defaults:

```text
--project-root .
--evaluation-start-date 2026-05-03
--primary-schema-min ir1.5
--include-first-watch-metrics true
--output-note evaluation/notes/T30_forward_return_evaluation_v1.md
--summary-output evaluation/replay/t30_run_summary.json
--fail-on-missing-inputs true
```

Use standard CLI parsing via `argparse`.

Boolean CLI values must be deterministic. Prefer explicit flags such as:

```text
--include-first-watch-metrics
--no-include-first-watch-metrics
--fail-on-missing-inputs
--no-fail-on-missing-inputs
```

if this matches existing repo style.

### 5.2 Optional CLI arguments

Add if useful and low-risk:

```text
--config-file config/config.yml
--history-root snapshots/history
--snapshots-runs-root snapshots/runs
--reports-runs-root reports/runs
--exports-dir evaluation/exports
--replay-dir evaluation/replay
--notes-dir evaluation/notes
```

Do not require these if existing T18 functions already assume canonical roots. Keep defaults aligned with T18.

### 5.3 Exit behavior

The script must exit non-zero when:

- required input root is missing and `--fail-on-missing-inputs` is active,
- no `snapshots/runs/**/run.manifest.json` files are found,
- no OHLCV history files are found under the required T18-compatible path,
- `run_evaluation_export(...)` raises,
- required output files are missing after export,
- required output files exist but are empty or unreadable,
- generated summary JSON cannot be written.

The script may exit zero with explicit warning when `--no-fail-on-missing-inputs` is set and the missing data condition is intentionally tolerated for diagnostics.

---

## 6. Input validation

Before running evaluation, validate the following.

### 6.1 Replay manifests

Required:

```text
snapshots/runs/**/run.manifest.json
```

There must be at least one manifest.

Each manifest considered by the script must be:

- non-empty,
- valid JSON object,
- include or imply a `run_id` through payload or parent directory.

Missing manifests are fatal in default mode.

### 6.2 Reports / diagnostics availability

T18 resolves diagnostics using `run.manifest.json` plus the canonical split layout:

```text
snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz
```

Important: `symbol_diagnostics.jsonl.gz` is intentionally **not** repo-persisted. It is present only in the large Shadow-Live CI artifact unless the user has manually unpacked that artifact into the working tree. The T30 script must not invent diagnostics and must rely on T18's existing resolution logic.

If replay diagnostics after export report:

```text
missing_diagnostics_run_count > 0
```

then the note and summary must surface this explicitly.

If:

```text
missing_diagnostics_run_count == manifest_count
```

then the note must prominently warn that no signal events could be reconstructed because diagnostics are missing locally. It must not silently produce an apparently valid empty evaluation.

Do not silently treat missing diagnostics as zero events.

### 6.3 OHLCV history availability

Required path pattern:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=*/year=*/month=*/*.parquet
```

There must be at least one Parquet file.

The script must not fetch OHLCV. If files are absent, fail with a message instructing the user to run:

```text
python scripts/fetch_ohlcv_history_for_evaluation.py --project-root .
```

or the exact current script invocation if the implemented CLI differs.

### 6.4 Generated outputs

After running T18 export, validate the presence and readability of:

```text
evaluation/exports/signal_event_metrics.parquet
evaluation/exports/terminal_event_timeline.parquet
evaluation/exports/transition_lead_times.parquet
evaluation/exports/evaluation_summary.json
evaluation/replay/event_timeline.jsonl
evaluation/replay/replay_manifest.json
evaluation/replay/replay_diagnostics.json
```

For Parquet files:

- file must exist,
- file size must be > 0,
- `pandas.read_parquet(...)` must succeed.

For JSON files:

- file must exist,
- file size must be > 0,
- JSON must parse successfully,
- object-vs-array type must be preserved as generated by T18.

For JSONL:

- file must exist,
- each non-empty line must parse as JSON.

---

## 7. Evaluation execution

The script must call the existing T18 export function rather than reimplement replay/metrics:

```python
from scanner.evaluation.dataset_export import run_evaluation_export

payload = run_evaluation_export(
    project_root=project_root,
    config={
        "independence_release": {
            "evaluation": {
                "include_first_watch_metrics": <bool>
            }
        }
    },
)
```

If the repo already has a canonical config loader that should be used for evaluation, reuse it. Do not introduce a second conflicting config path.

The script must preserve T18 default horizons:

```text
1d / 3d / 5d / 10d
```

Do not narrow the actual export to 1d/3d. Instead, the note should explain which horizons are materially populated and which are dominated by `insufficient_future_data`.

---

## 8. T30 analysis note

Create:

```text
evaluation/notes/T30_forward_return_evaluation_v1.md
```

The note must be generated by the script from actual output files, not handwritten static content.

### 8.1 Required note structure

Use this structure:

```markdown
# T30 Forward-Return Evaluation v1

## Status

## Input data

## Evaluation outputs

## Event coverage

## Forward-return metric coverage

## Primary cohort: ir1.5+

## Exploratory historical cohort: pre-ir1.5

## Segment observations

## Known limitations

## Next recommended steps
```

### 8.2 Status section

Must state explicitly:

```text
Status: first Shadow-Live forward-return evaluation run
Type: exploratory / validation note
Not a final performance conclusion
No threshold changes recommended by this note alone
```

### 8.3 Input data section

Must include:

- project root,
- evaluation start date,
- number of replay manifests found,
- number of events reconstructed,
- number of symbols with OHLCV history,
- OHLCV date coverage min/max if available,
- timestamp of T30 execution.

### 8.4 Evaluation outputs section

Must list the generated output files and whether they are present/readable.

Required files:

```text
evaluation/exports/signal_event_metrics.parquet
evaluation/exports/terminal_event_timeline.parquet
evaluation/exports/transition_lead_times.parquet
evaluation/exports/evaluation_summary.json
evaluation/replay/event_timeline.jsonl
evaluation/replay/replay_manifest.json
evaluation/replay/replay_diagnostics.json
evaluation/replay/t30_run_summary.json
```

### 8.5 Event coverage section

Must summarize event counts by `event_type`, using the event timeline and/or `evaluation_summary.json`.

At minimum:

```text
first_watch
first_early_ready
first_confirmed_ready
first_late
first_chased
first_rejected
```

Only include event types that exist in the data, but the note should state when a key event type has zero observed rows.

### 8.6 Forward-return metric coverage section

From `signal_event_metrics.parquet`, summarize metric statuses for each horizon:

```text
metric_status_1d
metric_status_3d
metric_status_5d
metric_status_10d
```

Status counts must preserve distinct meanings:

- `ok`
- `insufficient_future_data`
- `missing_ohlcv_history`
- `reference_price_not_evaluable`
- `missing_persisted_state_reference`
- any other status emitted by T18

Do not collapse missing/future/reference failures into a generic failure bucket.

### 8.7 Primary cohort: `ir1.5+`

T30 v1 must treat `ir1.5+` as the primary cohort for operational tradeability interpretation.

If schema version is available in event source diagnostics or report context, use it to count `ir1.5+` rows.

If schema version is not available in T18 event rows, the script may derive primary cohort by run IDs / source report manifests only if this can be done deterministically. If this cannot be done cleanly without expanding T18, the note must say:

```text
Primary cohort separation could not be derived from current T18 event rows without additional source metadata. No silent schema inference was applied.
```

Do not invent schema versions.

### 8.8 Exploratory historical cohort: pre-`ir1.5`

Older `ir1.2`-`ir1.4` runs are valuable for exploratory examples such as INJ/LAB/UB/TRUTH.

T30 v1 may include them in overall technical event coverage, but the note must clearly mark them as exploratory if post-`ir1.5` operational fields are missing.

Do not silently backfill `is_operational_trade_candidate` as if it were a native field.

If a compatibility calculation is needed for the note, it must be explicitly named:

```text
operational_tradeability_compat = is_tradeable_candidate == true AND candidate_excluded != true
```

and must not be written back into diagnostics or used as a native schema field.

### 8.9 Segment observations

Before implementing segment extraction in the note generator, inspect `scanner/evaluation/dataset_export.py`, `scanner/evaluation/replay.py`, and the generated `signal_event_metrics.parquet` columns. T18's current event model may not export all diagnostic fields needed for segmentation, such as `is_operational_trade_candidate`, `execution_size_class`, `is_reduced_size_eligible`, or `candidate_excluded`.

The note must include first-pass observations for these segments **only where the required columns are actually available**:

1. `confirmed/early + operational`.
2. `confirmed/early + reduced-size eligible`.
3. `confirmed/early + below_min / observe_only`.
4. `late/chased after signal`.
5. structurally missed / no early signal examples are out-of-scope for automated extraction unless already present in event rows.

If a segment cannot be computed from current T18 exports because required fields are not included in the event rows, the note must state this explicitly instead of approximating, backfilling, or inventing aliases.

Do not introduce non-canonical field aliases.

### 8.10 Known limitations

Must include, if applicable:

- small sample size,
- 5d/10d mostly insufficient for recent events,
- historical schema heterogeneity,
- missing diagnostics for any runs,
- missing persisted reference prices,
- OHLCV history limited to candidate-scoped symbol set,
- no automatic workflow integration,
- no final performance conclusion.

### 8.11 Next recommended steps

Must include decision points, not automatic implementation:

- whether to run T30 v2 after more accumulated `ir1.5+` runs,
- whether to add workflow automation later,
- whether T18 event rows should carry additional segmentation fields for T30 v2,
- whether to add a formal cohort framework after v1 findings.

---

## 9. Machine-readable T30 summary

Create:

```text
evaluation/replay/t30_run_summary.json
```

It must be valid JSON object with at least:

```json
{
  "schema": "t30_run_summary_v1",
  "generated_at_utc": "...",
  "project_root": "...",
  "evaluation_start_date": "2026-05-03",
  "outputs": {
    "signal_event_metrics_parquet": "evaluation/exports/signal_event_metrics.parquet",
    "terminal_event_timeline_parquet": "evaluation/exports/terminal_event_timeline.parquet",
    "transition_lead_times_parquet": "evaluation/exports/transition_lead_times.parquet",
    "evaluation_summary_json": "evaluation/exports/evaluation_summary.json",
    "event_timeline_jsonl": "evaluation/replay/event_timeline.jsonl",
    "t30_note_md": "evaluation/notes/T30_forward_return_evaluation_v1.md"
  },
  "input_counts": {
    "manifest_count": 0,
    "ohlcv_symbol_count": 0
  },
  "event_counts_by_type": {},
  "metric_status_counts_by_horizon": {},
  "validation": {
    "missing_input_roots": [],
    "missing_outputs": [],
    "unreadable_outputs": []
  }
}
```

The exact shape may include additional fields, but the keys above must exist.

Use `null` only where a value is truly not evaluable. Do not coerce unknown counts to `0` unless actually counted.

---

## 10. Generated-file policy

T30 v1 outputs are analysis artifacts.

Default policy:

- The script writes files locally under `evaluation/`.
- It does not commit generated Parquet or OHLCV files.
- It does not modify report persistence allowlists.
- It does not upload artifacts itself; artifact upload belongs to a future manual workflow wrapper if needed.

If the repo policy already allows committing compact analysis notes under `evaluation/notes/`, Codex may leave the generated note as an untracked output or add documentation explaining where to place it. Do not automatically commit generated files from the script.

Update `.gitignore` if needed to prevent accidental commits of:

```text
evaluation/exports/*.parquet
snapshots/history/ohlcv/**
```

Do not ignore the script or static docs.

---

## 11. Tests

Add or update tests in the existing test suite. Prefer a new focused file:

```text
tests/test_t30_forward_return_evaluation_v1.py
```

Use temporary directories and synthetic fixture data. Do not require network access.

### 11.1 Script runs T18 export with valid fixture data

Fixture:

- `snapshots/runs/2026/05/03/daily-test/run.manifest.json`
- matching `reports/runs/2026/05/03/daily-test/symbol_diagnostics.jsonl.gz`
- matching OHLCV Parquet under `snapshots/history/ohlcv/timeframe=1d/symbol=AAAUSDT/year=2026/month=05/part-000.parquet`

Expected:

- script exits zero,
- required T18 outputs exist,
- note exists,
- `t30_run_summary.json` exists,
- 1d metric status is `ok` where enough future data exists.

### 11.2 Missing manifests fail clearly

Fixture:

- no `snapshots/runs/**/run.manifest.json`

Expected:

- default mode exits non-zero,
- error message mentions missing replay manifests,
- no misleading empty note is written.

### 11.3 Missing OHLCV history fails clearly

Fixture:

- replay manifest + diagnostics exist,
- no `snapshots/history/ohlcv/.../*.parquet`

Expected:

- default mode exits non-zero,
- error message instructs to run `scripts/fetch_ohlcv_history_for_evaluation.py`,
- no forward-return metrics are presented as valid.

### 11.4 Output validation catches empty files

Fixture:

- monkeypatch or construct post-export condition where one required output file is empty.

Expected:

- validation reports the file under `unreadable_outputs` or equivalent,
- script exits non-zero in default mode.

### 11.5 Metric status counts are per-horizon and not collapsed

Fixture creates rows that produce at least:

- `ok`,
- `insufficient_future_data`,
- `reference_price_not_evaluable` or `missing_persisted_state_reference`.

Expected:

- `t30_run_summary.json` reports statuses separately by horizon,
- note preserves distinct statuses.

### 11.6 Note includes required sections

Expected note contains all required headings:

```text
Status
Input data
Evaluation outputs
Event coverage
Forward-return metric coverage
Primary cohort: ir1.5+
Exploratory historical cohort: pre-ir1.5
Segment observations
Known limitations
Next recommended steps
```

### 11.7 No workflow integration

Add a test or static assertion if repo style supports it:

- scheduled Shadow-Live workflow is not modified to run T30,
- no new scheduled trigger for T30 is added.

If this is not practical as an automated test, document in the PR summary that no workflow integration was added.

### 11.8 Generated-file ignore guard

Test or inspect that generated Parquet/OHLCV artifacts are ignored and not part of report persistence allowlists:

```text
evaluation/exports/*.parquet
snapshots/history/ohlcv/**
```

Do not assert ignoring of `evaluation/notes/*.md` unless repo policy requires it.

### 11.9 Deterministic summary ordering

Given the same fixture input, repeated script runs should produce the same event/status counts and deterministic key ordering in JSON output.

Use `json.dumps(..., sort_keys=True)` or equivalent where appropriate.

### 11.10 No network access

Tests must not call MEXC or any external API.

---

## 12. Acceptance criteria

1. `scripts/run_t30_evaluation.py` exists and is runnable from repo root.
2. The script uses existing T18 evaluation code, especially `run_evaluation_export(...)`.
3. The script validates replay manifests before execution.
4. The script validates OHLCV history before execution.
5. The script does not fetch OHLCV itself.
6. The script fails clearly when T30-Pre-2 OHLCV history is absent.
7. The script generates/validates all existing T18 outputs.
8. The script writes `evaluation/notes/T30_forward_return_evaluation_v1.md`.
9. The script writes `evaluation/replay/t30_run_summary.json`.
10. The note states that T30 v1 is exploratory and not a final performance conclusion.
11. The note reports event counts and metric status counts.
12. The note preserves separate metric statuses instead of collapsing them.
13. The note separates primary `ir1.5+` interpretation from exploratory historical context or explicitly states when that separation cannot be derived.
14. The script does not add a scheduled workflow.
15. The script does not modify `independence-shadow-live.yml` to run T30.
16. Generated OHLCV/evaluation Parquet files remain artifact/local output only.
17. `.gitignore` or equivalent guardrails prevent accidental commit of OHLCV/evaluation Parquet files if not already covered.
18. Tests cover valid execution, missing inputs, output validation, note generation, metric-status counting, and no-network behavior.
19. Running the relevant test command succeeds.
20. PR summary reports exact commands run and results.

---

## 13. Definition of done

The PR is complete when:

1. Code and tests are implemented.
2. `scripts/run_t30_evaluation.py --help` works.
3. A fixture-based T30 test proves the end-to-end path from manifests + diagnostics + OHLCV to outputs + note.
4. No generated OHLCV or evaluation Parquet files are committed.
5. No scheduled workflow integration is added.
6. The PR summary includes:
   - implementation summary,
   - generated paths,
   - test command(s),
   - explicit statement that this is T30 v1 exploratory execution only.

---

## 14. Codex implementation notes

### 14.1 Reuse existing helpers

Before implementing new logic, inspect:

```text
scanner/evaluation/dataset_export.py
scanner/evaluation/replay.py
scanner/evaluation/forward_returns.py
scripts/fetch_ohlcv_history_for_evaluation.py
```

Reuse existing helpers where possible. Do not duplicate replay or metric formulas.

### 14.2 Missing vs invalid vs insufficient future data

Keep these distinct:

```text
missing_ohlcv_history
reference_price_not_evaluable
missing_persisted_state_reference
insufficient_future_data
ok
```

Do not collapse them into `failed`.

### 14.3 Nullable and numeric values

When summarizing metrics:

- `None`/`NaN` return values are expected for non-`ok` statuses.
- Non-finite values must not be presented as numeric performance.
- Do not compute averages over missing/non-finite values.
- If no `ok` rows exist for a segment/horizon, write `null` or `not_evaluable`, not `0.0`.

### 14.4 Determinism

Given the same input files and config, generated summaries and note tables must be deterministic.

Sort by stable keys when listing:

```text
symbol
setup_cycle_id
event_type
event_timestamp_utc
horizon
status
```

### 14.5 Do not overstate findings

The note may describe first observations, but must not make final performance claims such as:

```text
strategy works
strategy fails
thresholds should be changed
```

Use wording like:

```text
first observation
small-sample indication
not yet statistically meaningful
requires follow-up after more ir1.5+ runs
```

---

## 15. Suggested manual run sequence after merge

After this PR is merged and a workdir contains T30-Pre-1/Pre-2 inputs, first ensure diagnostics are available locally. `symbol_diagnostics.jsonl.gz` is intentionally not repo-persisted. If running from a CI artifact download, unzip the large Shadow-Live artifact into the repository/workdir before running T30:

```bash
# Example only; use the actual artifact file name from the run.
unzip independence-shadow-live-<run_id>.zip -d .
```

Then run:

```bash
python scripts/fetch_ohlcv_history_for_evaluation.py --project-root .
python scripts/run_t30_evaluation.py --project-root .
```

If diagnostics are not present, `run_t30_evaluation.py` must warn prominently via the note/summary when `missing_diagnostics_run_count == manifest_count`, because no events can be reconstructed.

Expected local outputs:

```text
evaluation/exports/signal_event_metrics.parquet
evaluation/exports/terminal_event_timeline.parquet
evaluation/exports/transition_lead_times.parquet
evaluation/exports/evaluation_summary.json
evaluation/replay/event_timeline.jsonl
evaluation/replay/replay_manifest.json
evaluation/replay/replay_diagnostics.json
evaluation/replay/t30_run_summary.json
evaluation/notes/T30_forward_return_evaluation_v1.md
```

If this is later wrapped in a manual GitHub Actions workflow, that wrapper should upload:

```text
evaluation/exports/**
evaluation/replay/**
evaluation/notes/**
snapshots/history/ohlcv/**
```

as artifacts, but that wrapper is out of scope for this ticket.

---

## 16. Self-review checklist before opening PR

Codex must verify:

- [ ] Scope is one PR only.
- [ ] T18 replay/forward-return formulas were not reimplemented.
- [ ] No scheduled workflow integration was added.
- [ ] No Shadow-Live workflow step was added.
- [ ] No OHLCV fetch was added to T30 script.
- [ ] Missing inputs fail clearly.
- [ ] Output validation catches empty/unreadable files.
- [ ] Metric statuses remain separate.
- [ ] Generated note is based on actual outputs.
- [ ] Generated JSON is deterministic.
- [ ] Tests do not use network.
- [ ] Generated Parquet/OHLCV files are not committed.
- [ ] Relevant tests pass.

