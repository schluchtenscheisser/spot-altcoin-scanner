# Title
[P0] Add Shadow-Live Daily Workflow for Real-Data Operation (Ticket 22)

## Context / Source

Ticket 20 proved technical executability against real MEXC data via a manual smoke-test workflow.
Tickets 21 and 21.1 made run diagnostics evaluation-ready and prevented invisible Intraday execution attempts when attachable diagnostics context is missing.

The latest post-T21/T21.1 smoke run passed technically and produced populated Daily diagnostics. It also showed the expected current Intraday state: Intraday monitoring rows currently lack cycle context and therefore emit `reasons.intraday_skip_reason="missing_intraday_cycle_context"` with `execution_attempted=false`. This is the intended safety behavior from T21.1 and is **not** a workflow failure.

This ticket introduces the first scheduled Shadow-Live workflow: real MEXC data, real Daily run artifacts, evaluation replay artifacts, and optional/non-blocking Intraday diagnostic output — but no trading, no orders, no automatic Git commits, and no end-user production guarantees.

```yaml
depends_on: [20, 21, 21.1]
```

Authoritative references:

- Current `main` after Tickets 20, 21, and 21.1.
- `.github/workflows/independence-smoke-test.yml` as technical reference only.
- `scripts/run_independence_smoke_test.py` as technical reference only.
- Current canonical artifact contracts:
  - `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`
  - `reports/runs/YYYY/MM/DD/<run_id>/report.json`
  - `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`
  - `evaluation/exports/**`
  - `evaluation/replay/**`
- Current output-path constraints:
  - no reports-side manifest files
  - no active `reports/analysis` output
  - no committing run artifacts to the repo

If existing implementation and this ticket conflict, preserve the established v2.1/T20/T21/T21.1 contracts. Do not introduce a second artifact model.

---

## Goal

Create a scheduled and manually dispatchable Shadow-Live workflow that runs the scanner on real MEXC data and uploads all relevant run and evaluation artifacts for review.

The goal is operational learning:

- observe Daily bucket quality on real data over time,
- collect populated diagnostics for candidate review,
- verify evaluation replay from run artifacts,
- observe current Intraday limitations safely,
- produce enough artifacts to drive the next product/calibration tickets.

This is **not** final production trading operation.

---

## Behavioral definition: Shadow-Live

Shadow-Live means:

- real MEXC data,
- scheduled real-time operation,
- real reports, diagnostics, manifests, and evaluation artifacts,
- no automatic orders,
- no automatic trading decisions,
- no automatic Git commits of generated artifacts,
- no user-facing production SLA,
- outputs are research/diagnostic signals until explicitly promoted later.

All Shadow-Live outputs must be treated as diagnostic/research artifacts.

---

## Scope

### In scope

1. Add a new GitHub Actions workflow:

   ```text
   .github/workflows/independence-shadow-live.yml
   ```

2. The workflow must support:

   - `workflow_dispatch`
   - scheduled daily execution via `schedule`

3. The workflow must run with real MEXC data.

4. Daily run is required and blocking.

5. Evaluation Replay is required and blocking.

6. Intraday may run as non-blocking diagnostic-only step if technically convenient, but current `missing_intraday_cycle_context` is a known state and must not fail the workflow by itself.

7. Upload all relevant required artifacts, including evaluation artifacts:

   ```text
   shadow-live-report.json
   snapshots/runs/**
   reports/runs/**
   evaluation/exports/**
   evaluation/replay/**
   ```

   Also upload optional convenience report paths when present:

   ```text
   reports/daily/**
   reports/index/**
   ```

8. Keep outputs as GitHub Actions artifacts only. Do not commit generated run artifacts.

9. Address the current GitHub Actions Node.js 20 deprecation warning inside this workflow implementation. Prefer Node-24-compatible action versions where available. If needed, opt into Node 24 explicitly via workflow environment.

10. Create a new dedicated Shadow-Live orchestrator script:

    ```text
    scripts/run_independence_shadow_live.py
    ```

    Do not functionally modify `scripts/run_independence_smoke_test.py`. Shared utility code may be extracted only if the smoke orchestrator behavior and output contract remain unchanged.

11. Add tests or static checks where reasonable for the new workflow/orchestrator behavior.

12. Update canonical docs with the Shadow-Live operating semantics and artifact expectations.

### Out of scope

- Business logic changes.
- Phase/state/decision/invalidation/ranking changes.
- Calibration changes.
- Execution grading changes.
- New Diagnostics schema fields.
- New Evaluation metrics.
- Intraday carry-forward / Monitoring Row persistence contract.
- Full Intraday replay completeness.
- Automatic trading or order placement.
- Automatic Git commits of run artifacts.
- Changes to canonical report/snapshot/evaluation path contracts.
- Changes to artifact writer semantics outside what is needed to upload existing artifacts.
- `workflow_dispatch` date override / backfill input. If needed later, record it as a deferred enhancement, not part of T22.

---

## Known current Intraday state

The latest post-T21/T21.1 smoke run showed Intraday diagnostics records with:

```text
execution_attempted=false
reasons.intraday_skip_reason="missing_intraday_cycle_context"
```

This is expected because the current Intraday Monitoring Row context does not yet carry enough cycle/state/decision context for attachable execution diagnostics.

For Ticket 22:

- This condition is **not** a workflow failure.
- It must be surfaced clearly in `shadow-live-report.json`.
- The workflow must not hide it.
- The workflow must not invent carry-forward context to remove it.
- A later dedicated ticket may define a proper Intraday carry-forward context.

Intraday can run in Shadow-Live as a diagnostic/non-blocking observation path. Daily remains the primary Shadow-Live signal.

---

## Workflow requirements

### Workflow file

Create:

```text
.github/workflows/independence-shadow-live.yml
```

Recommended triggers:

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "30 1 * * *"
```

The exact cron time may be adjusted if needed to allow MEXC Daily bars to settle. Use UTC and document the chosen timing in a comment.

### Permissions

Use minimal permissions. The workflow should not need repository write permissions for generated artifacts.

Recommended:

```yaml
permissions:
  contents: read
```

### Secrets / API credentials

Before implementing the workflow, inspect `.github/workflows/independence-smoke-test.yml` and current config/client code for the authoritative credential wiring.

Current smoke workflow uses public MEXC connectivity and may not require API secrets. Do **not** invent mandatory secret names if the current real-data path does not use them.

If the Shadow-Live full-universe data path requires authenticated credentials or a market-data provider key, expose the repository secrets using the exact names already used by the repo/config. Expected candidate names to verify are:

```text
MEXC_API_KEY
MEXC_API_SECRET
CMC_API_KEY
```

If the exact names differ, use the existing smoke/config/client wiring as the authoritative reference and document the names in the PR description. A missing or empty required credential must be reported as a clear preflight failure, not silently converted into an empty universe.


### Environment / Node 24 compatibility

The latest smoke workflow emitted a GitHub Actions warning that Node.js 20 actions are deprecated.

Ticket 22 must address this directly.

Allowed approaches:

1. Prefer updated action versions that support Node 24 where available.
2. If the used action version is still the correct current version, explicitly test/opt into Node 24 in this workflow:

   ```yaml
   env:
     FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"
   ```

Do **not** use:

```yaml
ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION: "true"
```

That is an opt-out and is not acceptable for this ticket.

### Workdir

Use an isolated temporary workdir similar to the smoke test.

Recommended:

```text
${{ runner.temp }}/ir-shadow-live-workdir
```

Do not write run artifacts into unexpected repository paths outside the established output contracts.

### Disk / storage visibility

Shadow-Live may process a much larger universe than the 5-symbol smoke test. The workflow or orchestrator must report basic disk usage after the run, at minimum:

```bash
df -h
du -sh "$SHADOW_LIVE_WORKDIR" || true
```

Disk usage reporting is informational unless the run fails. Do not introduce retention/purge behavior outside the isolated Shadow-Live workdir.

### Artifact upload

Upload one artifact containing all Shadow-Live outputs.

Artifact name should be deterministic enough for identification, for example:

```text
independence-shadow-live-${{ github.run_id }}
```

Required upload paths — must exist after a successful Daily + Evaluation run; absence is a blocking failure detected by the orchestrator before upload:

```text
shadow-live-report.json
snapshots/runs/**
reports/runs/**
evaluation/exports/**
evaluation/replay/**
```

Optional upload paths — convenience/index copies written by the report layer when available; absence is non-blocking and must not fail the workflow:

```text
reports/daily/**
reports/index/**
```

`reports/daily/**` and `reports/index/**` are useful for review automation, but they are not the primary run artifacts. The orchestrator must not treat missing optional paths as failures.

---

## Orchestrator requirements

Create a dedicated Shadow-Live orchestrator:

```text
scripts/run_independence_shadow_live.py
```

This is mandatory. Do not reuse, repurpose, or functionally refactor `scripts/run_independence_smoke_test.py` for Shadow-Live.

Rationale: the smoke orchestrator has an accepted T20 contract (`smoke-test-report.json`, smoke candidate list, smoke-specific upload candidates, and smoke-specific workdir semantics). Shadow-Live has different report semantics (`shadow-live-report.json`, workflow mode, known-state markers, blocking/non-blocking classification). Mixing both concerns risks regressions in the already accepted smoke workflow.

Shared utility logic such as artifact-existence checks or forbidden-path validation may be extracted to a shared internal helper module, but the smoke orchestrator behavior and output contract must remain unchanged. Existing smoke workflow tests must remain green.

### Required responsibilities

The orchestrator must:

1. Run the Daily scanner on real MEXC data.
2. Run Evaluation Replay from run artifacts.
3. Optionally run Intraday as non-blocking diagnostic-only step.
4. Produce a top-level summary:

   ```text
   shadow-live-report.json
   ```

5. Verify expected artifact existence:

   - Daily report exists.
   - Daily diagnostics exists.
   - Run manifest exists.
   - Evaluation Replay produced its expected summary/timeline artifacts, unless there are legitimately no events and the evaluation component represents that explicitly.

6. Check forbidden writes using the same constraints established by the smoke test:

   - no report-side manifest files
   - no active `reports/analysis` output
   - no unexpected output roots

   The Shadow-Live orchestrator must use an explicit allow-list for expected output roots inside the isolated Shadow-Live workdir. At minimum, the following roots are allowed:

   ```text
   artifacts/
   data/
   evaluation/exports/
   evaluation/replay/
   logs/
   reports/runs/
   reports/daily/
   reports/index/
   snapshots/runs/
   snapshots/history/ohlcv/
   ```

   Notes:
   - `reports/daily/` and `reports/index/` are optional convenience/index copies, not primary run artifacts.
   - `evaluation/exports/` and `evaluation/replay/` are required upload roots after successful Evaluation Replay.
   - `snapshots/history/ohlcv/` is allowed for the canonical OHLCV long-term store.
   - `reports/analysis/` is explicitly forbidden as an active output root.
   - If implementation discovers additional existing legitimate runtime roots by inspecting the smoke orchestrator/current code, they may be added only with a short comment explaining the source. Do not silently broaden the allow-list to all repository directories.

7. Exit non-zero on blocking failures.

### Suggested summary fields

`shadow-live-report.json` should contain at minimum:

```json
{
  "workflow_mode": "shadow_live",
  "status": "pass|fail",
  "run_started_at_utc": "...",
  "run_finished_at_utc": "...",
  "daily": {
    "status": "pass|fail",
    "run_id": "...",
    "report_path": "...",
    "diagnostics_path": "...",
    "manifest_path": "...",
    "counts_by_bucket": {},
    "symbol_lists": {}
  },
  "intraday": {
    "status": "pass|fail|skipped|non_blocking_warning",
    "known_state": "missing_intraday_cycle_context|none|...",
    "diagnostics_path": "..."
  },
  "evaluation_replay": {
    "status": "pass|fail",
    "event_count": 0,
    "summary_path": "...",
    "timeline_path": "..."
  },
  "artifact_paths": [],
  "forbidden_path_writes": [],
  "errors": [],
  "warnings": []
}
```

Exact shape may vary, but it must be machine-readable and stable enough for later review automation.

### Blocking vs non-blocking semantics

Blocking failures:

- Daily runner exception.
- Missing Daily `report.json` after Daily success.
- Missing Daily `symbol_diagnostics.jsonl.gz` after Daily success.
- Missing run manifest after Daily success.
- Evaluation Replay exception.
- Forbidden path writes.
- Unexpected report-side manifest.
- Active `reports/analysis` output.

Non-blocking / expected states:

- No `confirmed_candidates`.
- No `early_candidates`.
- No replay events, if Evaluation Replay reports this explicitly and does not error.
- Intraday `missing_intraday_cycle_context`, as long as `execution_attempted=false` and no invisible execution attempts occur.
- Empty Intraday monitoring universe.
- No new Intraday 4h bar.

---

## Daily requirements

Daily is the primary Shadow-Live signal.

The workflow must verify:

- Daily run completed.
- Daily report exists under canonical `reports/runs/**`.
- Daily diagnostics exists under canonical `reports/runs/**/symbol_diagnostics.jsonl.gz`.
- Manifest exists under canonical `snapshots/runs/**/run.manifest.json`.
- Daily diagnostics are not trivially empty if symbols were processed.

The workflow does not need to assert that any specific bucket is non-empty. For example, `confirmed_candidates=0` is valid.

---

## Evaluation Replay requirements

Evaluation Replay must run after Daily artifacts are written.

The workflow must upload Evaluation artifacts explicitly:

```text
evaluation/exports/**
evaluation/replay/**
```

If Replay produces no events, this is not automatically a workflow failure if Replay reports the no-event state explicitly. However, Replay execution itself must not silently fail.

The summary must include at least:

- replay status,
- event count if available,
- paths to replay summary/timeline artifacts if available.

Replay must continue to read from run artifacts, not live SQLite.

---

## Intraday requirements

Intraday may be included in the Shadow-Live workflow as a non-blocking diagnostic step.

If included:

- It must use the current Intraday runner without changing provider contracts.
- It must upload Intraday reports/diagnostics if produced.
- It must treat `missing_intraday_cycle_context` as known non-blocking state.
- It must fail only if there is a true runner exception or invariant violation.
- It must not perform invisible execution attempts.

If Intraday is not included in the first version of T22, the workflow summary must explicitly say:

```text
intraday.status="skipped"
intraday.reason="not_enabled_in_initial_shadow_live"
```

Recommendation: include Intraday as non-blocking if the existing smoke orchestrator already runs it cleanly, but do not let known missing-cycle context block Daily Shadow-Live.

---

## Documentation updates

Update canonical docs, likely under:

```text
docs/canonical/REPORTS.md
docs/canonical/WORKFLOW_CODEX.md
```

or another appropriate canonical operations doc.

The docs must describe:

- Shadow-Live purpose.
- Difference between smoke test and Shadow-Live.
- Daily is blocking and primary.
- Intraday missing cycle context is a known non-blocking state in current architecture.
- Evaluation artifacts are uploaded.
- Generated run artifacts are not committed.
- No orders/trading are performed.
- Node-24-compatible workflow stance.

Do not manually edit generated docs such as code maps or snapshots if the repo treats them as generated artifacts.

---

## Tests / verification

Add tests where practical. At minimum, include one or more of:

1. Static workflow existence/path test:
   - `.github/workflows/independence-shadow-live.yml` exists.

2. Static workflow content test:
   - contains `workflow_dispatch`,
   - contains `schedule`,
   - uploads `evaluation/exports/**`,
   - uploads `evaluation/replay/**`,
   - does not set `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION`.

3. Orchestrator unit test:
   - summary JSON includes Daily, Intraday, Evaluation, forbidden writes, errors/warnings.

4. Artifact path test:
   - required upload paths are represented.

5. Existing smoke tests must remain green.

Required commands before PR completion:

```bash
pytest -q
```

If workflow tests are not feasible due to current test infrastructure, document manual verification in the PR description and ensure the workflow YAML is straightforward and reviewable.

---

## Acceptance criteria

- New Shadow-Live workflow exists at `.github/workflows/independence-shadow-live.yml`.
- Dedicated Shadow-Live orchestrator exists at `scripts/run_independence_shadow_live.py`.
- `scripts/run_independence_smoke_test.py` behavior/output contract remains unchanged.
- Workflow supports both `workflow_dispatch` and scheduled execution.
- Workflow uses real MEXC data.
- Workflow does not commit generated artifacts.
- Daily run is blocking.
- Evaluation Replay is blocking.
- Intraday is either:
  - included as non-blocking diagnostic step, or
  - explicitly marked as skipped in summary.
- Current `missing_intraday_cycle_context` state is documented as known non-blocking state.
- `shadow-live-report.json` is produced.
- Artifact upload includes required paths:
  - `shadow-live-report.json`
  - `snapshots/runs/**`
  - `reports/runs/**`
  - `evaluation/exports/**`
  - `evaluation/replay/**`
- Artifact upload includes optional convenience paths when present, without treating absence as failure:
  - `reports/daily/**`
  - `reports/index/**`
- Workflow or orchestrator checks for forbidden path writes using an explicit allow-list of expected output roots.
- The allow-list includes canonical Shadow-Live roots and does not silently allow arbitrary repository directories.
- Node.js 20 GitHub Actions deprecation warning is addressed in this workflow implementation via updated action versions and/or Node 24 opt-in.
- No `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true` is introduced.
- No output path contracts are changed.
- No diagnostics schema changes are introduced.
- No business logic changes are introduced.
- Full test suite passes.

---

## Anti-requirements

Codex must not:

- add automatic trading,
- add order placement,
- add exchange account write operations,
- commit generated artifacts,
- modify or functionally refactor `scripts/run_independence_smoke_test.py`,
- change Daily/Intraday business logic,
- change diagnostics schema,
- change evaluation metric semantics,
- invent Intraday carry-forward context,
- treat `missing_intraday_cycle_context` as a workflow failure,
- remove or weaken T21/T21.1 invariants,
- add report-side manifests,
- write active outputs to `reports/analysis`,
- change canonical artifact paths,
- use `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true`.

---

## Suggested implementation sequence

1. Inspect current smoke workflow and smoke orchestrator as technical references only.
2. Create dedicated `scripts/run_independence_shadow_live.py`; do not functionally modify `scripts/run_independence_smoke_test.py`.
3. Define the Shadow-Live forbidden-path allow-list explicitly, using the ticket list above and the smoke orchestrator/current code as references.
4. Verify credential/secret wiring against existing workflow/config/client code and document it in the PR.
5. Implement the Shadow-Live orchestrator/summary generation.
6. Add `.github/workflows/independence-shadow-live.yml`.
7. Ensure artifact upload includes required reports, snapshots, and evaluation paths plus optional convenience report paths.
8. Add disk usage reporting after the run.
9. Address Node-24 compatibility in the workflow.
10. Add static/unit tests where practical.
11. Update canonical docs.
12. Run targeted tests if added.
13. Run full `pytest -q`.
14. In PR description, include:
    - selected workflow schedule,
    - credential/secret wiring decision,
    - artifact upload paths,
    - blocking vs non-blocking semantics,
    - Node-24 compatibility decision,
    - disk usage visibility,
    - confirmation that no generated artifacts are committed.

---

## Definition of Done

- Ticket implemented within stated scope.
- Workflow can be manually dispatched.
- Workflow is scheduled.
- Shadow-Live summary is generated.
- Required artifacts are uploaded, including evaluation artifacts.
- Node.js 20 deprecation warning is addressed for this workflow.
- Full tests pass.
- PR description documents all operational semantics.
- Ticket archived according to repo workflow.
