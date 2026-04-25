> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket 20 — Add Manual End-to-End Smoke Test Workflow

## Status

Ready for Codex implementation.

## Purpose

Add a manually triggered GitHub Actions workflow that runs the Independence-Release pipeline
against a fixed minimal smoke candidate list and verifies that all three pipeline stages
(Daily Runner, Intraday Runner, Evaluation Replay) execute without exception and produce
artifacts in canonical locations only.

This ticket is an infrastructure/validation ticket. It does not change scanner business logic,
schemas, configuration defaults, report semantics, evaluation metrics, or any v2.1
phase/state/decision semantics.

---

## Authoritative reference set

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`, as supplemental context only
   where it does not conflict with the v2.1 sections or the consolidated concept.
4. The current repo reality, especially `scanner/main.py`, `scanner/runners/daily.py`,
   `scanner/runners/intraday.py`, `scanner/evaluation/replay.py`,
   `scanner/data/bar_clock.py`, and existing workflows under `.github/workflows/`.
5. The master preflight checklist for Codex-ready tickets.

If the authoritative reference set, existing repo canonical documents, and existing code
collide, the authoritative reference set wins.

---

## Current problem

There is no automated way to verify that the full pipeline executes end-to-end against real
MEXC data after changes. The existing test suite is unit/integration-only and does not
exercise real network calls, real bar-clock resolution, or real artifact write paths. A
manually triggered smoke-test workflow fills this gap without requiring permanent scheduling
or CI gating.

---

## Scope

### In scope

1. Add `.github/workflows/independence-smoke-test.yml` — a manual `workflow_dispatch`
   workflow.
2. Add a smoke-test orchestrator script at `scripts/run_independence_smoke_test.py`.
   This script is required because the existing `scanner/main.py` CLI does not expose
   parameters for a fixed symbol list, a temporary DB path, or a configurable output
   working directory. The orchestrator bridges this gap without modifying production code.
3. The workflow invokes the orchestrator script, which runs the three pipeline stages in
   sequence: Daily Runner → Intraday Runner → Evaluation Replay.
4. Use a fixed hardcoded smoke candidate list of five symbols:
   `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `INJUSDT`, `ARBUSDT`.
   This is a smoke-test candidate pool only — not a canonical discovery universe, not a
   production filter, not a fachlicher Top-N cut.
5. All smoke-test outputs (manifests, diagnostics, reports, summary) are written under
   `SMOKE_WORKDIR="${RUNNER_TEMP}/ir-smoke-workdir"`. The repository checkout must remain
   free of generated run artifacts.
6. Use a clean SQLite state DB under `SMOKE_WORKDIR` for each run.
7. Perform a live public MEXC connectivity preflight before any pipeline stage executes.
8. Verify artifact locations after each stage using explicit shell assertions.
9. Produce a structured JSON summary report at
   `SMOKE_WORKDIR/artifacts/smoke-test-report.json`.
10. Upload smoke-test outputs via `actions/upload-artifact` with `if: always()`.
11. Clean up `SMOKE_WORKDIR` unconditionally after the run.

### Out of scope

- Scheduled or push-triggered execution. Manual `workflow_dispatch` only.
- Changes to `scanner/runners/daily.py`, `scanner/runners/intraday.py`,
  `scanner/evaluation/replay.py`, or `scanner/main.py`.
- Changes to report schemas, snapshot schemas, or evaluation metrics.
- Changes to business logic, decision buckets, state machine, or phase interpretation.
- Changes to bar-clock logic or canonical ID definitions.
- Changes to existing workflows (`run-analysis-script.yml`, `code-map.yml`,
  `gpt-snapshot.yml`).
- Retention or archiving beyond the uploaded GitHub Actions artifact.
- Business-logic assertions: score values, bucket distributions, phase outcomes, or signal
  quality are not verified by the smoke test.
- Golden assertions or calibration checks.

---

## Canonical contracts (do not redefine)

The following contracts are established by T1–T19 and must be respected without change:

- `daily_bar_id`: canonical string `YYYY-MM-DD`.
- `intraday_bar_id`: canonical string `YYYY-MM-DDTHH:00:00Z`, UTC 4h-aligned, hour in
  `{00, 04, 08, 12, 16, 20}`.
- Canonical manifest path: `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`.
- Canonical diagnostics path: `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`.
- `reports/analysis/` is deprecated; no stage may write there.
- Allowed CI output roots: `evaluation/exports/`, `evaluation/calibration/`,
  `artifacts/`, `reports/aux/`.

All paths above are relative to `SMOKE_WORKDIR` during the smoke test, preserving the
canonical relative structure while isolating outputs from the repository checkout.

---

## Smoke-test orchestrator: `scripts/run_independence_smoke_test.py`

### Purpose

Bridge the gap between the existing CLI (which does not accept a symbol list, DB path, or
output working directory) and the smoke-test workflow, without modifying production code.

### Output isolation guarantee

The orchestrator must guarantee that all run artifacts land under `SMOKE_WORKDIR` and that
nothing is written to the repository checkout (`GITHUB_WORKSPACE`).

If the existing runners resolve output paths relative to the current working directory
(e.g. `Path.cwd() / "snapshots"`), the orchestrator must change the working directory to
`SMOKE_WORKDIR` before invoking any runner and restore the previous working directory in a
`finally` block:

```python
import os

prev_cwd = os.getcwd()
try:
    os.chdir(smoke_workdir)
    run_daily_scan(...)
    run_intraday_scan(...)
    run_evaluation_replay(...)
finally:
    os.chdir(prev_cwd)
```

Merely setting config attributes that the runner does not actually use for path resolution
is not sufficient. The orchestrator must verify at runtime that artifacts appeared under
`SMOKE_WORKDIR` and not under `prev_cwd`.

### SQLite DB path

The orchestrator must ensure the SQLite state DB is created under `SMOKE_WORKDIR`. If the
existing runner resolves the DB path relative to `cwd` (e.g. `data/independence_release.sqlite`),
`chdir(SMOKE_WORKDIR)` is sufficient and preferred over any production code change. Do not
modify `scanner/runners/daily.py` or `scanner/runners/intraday.py` to accept an explicit
DB path parameter.

### Configuration path

Before changing the working directory to `SMOKE_WORKDIR`, the orchestrator must resolve
`SCANNER_CONFIG_PATH` to an absolute path:

```python
import os
config_path = os.environ.get(
    "SCANNER_CONFIG_PATH",
    os.path.join(os.environ["GITHUB_WORKSPACE"], "config", "config.yml")
)
config_path = os.path.abspath(config_path)
```

This absolute path must be passed to `ScannerConfig` after `chdir`. Do not rely on a
relative config path after changing the working directory.

### What the orchestrator may do

- Hardcode the five smoke candidate symbols.
- Load `ScannerConfig` from the absolute config path resolved above.
- Attach smoke-specific provider instances to `ScannerConfig` at runtime, scoped to the
  five symbols and backed by real MEXC API calls.
- Change working directory to `SMOKE_WORKDIR` before invoking runners, and restore it in
  `finally`.
- Invoke `run_daily_scan`, `run_intraday_scan`, and the Evaluation Replay entry point
  directly as Python calls.
- Write the JSON summary report to `SMOKE_WORKDIR/artifacts/smoke-test-report.json`.
- Perform artifact location assertions and emit PASS/FAIL per check to stdout.
- Exit with code `0` on full pass, code `1` on any FAIL.

### What the orchestrator must not do

- Modify `scanner/runners/daily.py`, `scanner/runners/intraday.py`,
  `scanner/evaluation/replay.py`, or `scanner/main.py`.
- Change any business logic, schema, config default, or canonical output path definition.
- Use mocked or simulated MEXC API responses.
- Write any output outside `SMOKE_WORKDIR`.
- Commit or push files.
- Introduce a new production execution mode or config key.

### CLI interface

The orchestrator must accept the following arguments:

```bash
python scripts/run_independence_smoke_test.py \
  --workdir "$SMOKE_WORKDIR" \
  --daily-bar-id "$DAILY_BAR_ID" \
  --intraday-bar-id "$INTRADAY_BAR_ID"
```

`--workdir` is required. `--daily-bar-id` and `--intraday-bar-id` are required when passed
by the workflow (see Step 3 below) so the orchestrator uses the same IDs that the workflow
validated in the bar-clock step. If not provided, the orchestrator resolves them using the
existing `bar_clock.py` helpers.

---

## Required workflow behavior

### File

`.github/workflows/independence-smoke-test.yml`

### Trigger

```yaml
on:
  workflow_dispatch:
```

No schedule. No push trigger. No required inputs beyond manual dispatch.

### Permissions

```yaml
permissions:
  contents: read
```

The workflow must not commit or push any artifact back to the repository.

### Standard setup steps

The workflow must include these steps before any pipeline step:

```yaml
- uses: actions/checkout@v5

- uses: actions/setup-python@v6
  with:
    python-version: "3.12"

- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

### Environment setup

```yaml
- name: Set smoke workdir and config path
  run: |
    echo "SMOKE_WORKDIR=${{ runner.temp }}/ir-smoke-workdir" >> "$GITHUB_ENV"
    echo "SCANNER_CONFIG_PATH=${{ github.workspace }}/config/config.yml" >> "$GITHUB_ENV"
    mkdir -p "${{ runner.temp }}/ir-smoke-workdir/artifacts"
```

### Step sequence

Steps execute in order. Each step fails the workflow on unhandled exception or assertion
failure, except upload and cleanup which run with `if: always()`.

#### Step 1 — Public MEXC connectivity preflight

Perform a live HTTP check against the public MEXC endpoint used by the scanner client:

```bash
curl -sf --max-time 10 "https://api.mexc.com/api/v3/exchangeInfo" > /dev/null \
  || { echo "FAIL: MEXC public endpoint unreachable. Check network/proxy policy."; exit 1; }
echo "PASS: MEXC public endpoint reachable."
```

Do not infer credential requirements by static code inspection. If the runtime path
explicitly requires API credentials (i.e. a secret is referenced in the client code for the
endpoints used by the smoke candidate list), verify that the relevant secret is configured
and fail with a clear diagnostic if it is not.

#### Step 2 — Bar clock sanity

Resolve and validate both canonical bar IDs using the actual helpers available in
`scanner/data/bar_clock.py`. Inspect the current signatures before writing this step;
the example below reflects the known current API but Codex must verify against the actual
module:

```yaml
- name: Bar clock sanity
  id: bar_clock
  run: |
    python - > /tmp/bar_ids.out <<'PY'
    from datetime import datetime, timezone
    from scanner.data.bar_clock import daily_bar_id, get_last_closed_intraday_bar_id
    import re

    now = datetime.now(timezone.utc)
    daily = daily_bar_id(now)
    intraday = get_last_closed_intraday_bar_id(now)

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", daily):
        raise SystemExit(f"FAIL: Invalid daily_bar_id: {daily}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T(00|04|08|12|16|20):00:00Z", intraday):
        raise SystemExit(f"FAIL: Invalid intraday_bar_id: {intraday}")

    print(f"daily_bar_id={daily}")
    print(f"intraday_bar_id={intraday}")
    PY
    cat /tmp/bar_ids.out >> "$GITHUB_OUTPUT"
    echo "PASS: daily_bar_id=$(grep daily_bar_id /tmp/bar_ids.out | cut -d= -f2)"
    echo "PASS: intraday_bar_id=$(grep intraday_bar_id /tmp/bar_ids.out | cut -d= -f2)"
```

Do not use the deprecated `::set-output` syntax. Informational PASS messages must go to
stdout only, not to `$GITHUB_OUTPUT`.

Codex must verify the actual function names and signatures in `scanner/data/bar_clock.py`
before writing this step. If the signatures differ from the example above, adapt the call
accordingly without changing the bar-clock module.

#### Step 3 — Run smoke-test orchestrator

Pass the bar-clock step outputs into the orchestrator so the IDs validated by the workflow
are the same IDs used by the smoke run:

```bash
python scripts/run_independence_smoke_test.py \
  --workdir "$SMOKE_WORKDIR" \
  --daily-bar-id "${{ steps.bar_clock.outputs.daily_bar_id }}" \
  --intraday-bar-id "${{ steps.bar_clock.outputs.intraday_bar_id }}"
```

The orchestrator runs all three pipeline stages internally and writes the JSON summary to
`$SMOKE_WORKDIR/artifacts/smoke-test-report.json`. It exits with code `1` on any FAIL.

#### Step 4 — Artifact location assertions

After the orchestrator completes, the workflow performs independent shell-level assertions:

```bash
# Canonical manifest exists under SMOKE_WORKDIR
MANIFEST=$(find "$SMOKE_WORKDIR/snapshots/runs" -name "run.manifest.json" 2>/dev/null | head -1)
[ -n "$MANIFEST" ] \
  || { echo "FAIL: no run.manifest.json found under SMOKE_WORKDIR/snapshots/runs"; exit 1; }
echo "PASS: manifest at $MANIFEST"

# No manifest under SMOKE_WORKDIR/reports/runs
if [ -d "$SMOKE_WORKDIR/reports/runs" ] && \
   find "$SMOKE_WORKDIR/reports/runs" -name "*.manifest.json" -print -quit 2>/dev/null \
   | grep -q .; then
  echo "FAIL: manifest found under SMOKE_WORKDIR/reports/runs"
  exit 1
fi
echo "PASS: no manifest under SMOKE_WORKDIR/reports/runs"

# No writes to SMOKE_WORKDIR/reports/analysis
if [ -d "$SMOKE_WORKDIR/reports/analysis" ] && \
   find "$SMOKE_WORKDIR/reports/analysis" -mindepth 1 -print -quit 2>/dev/null \
   | grep -q .; then
  echo "FAIL: artifact written to SMOKE_WORKDIR/reports/analysis"
  exit 1
fi
echo "PASS: no artifact under SMOKE_WORKDIR/reports/analysis"

# Repository checkout must be clean of any generated run artifacts
DIRTY=$(git -C "$GITHUB_WORKSPACE" status --short -- \
  reports snapshots evaluation artifacts data 2>/dev/null)
if [ -n "$DIRTY" ]; then
  echo "FAIL: repository checkout is not clean after smoke test:"
  echo "$DIRTY"
  exit 1
fi
echo "PASS: repository checkout clean (no run artifacts written to GITHUB_WORKSPACE)"
```

All assertions must handle missing directories safely. The `git status` check is the
authoritative guard against any artifact accidentally landing in the repository checkout,
including `data/independence_release.sqlite` or similar DB paths.

#### Step 5 — Upload artifacts

```yaml
- name: Upload smoke test artifacts
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: smoke-test-output
    path: |
      ${{ runner.temp }}/ir-smoke-workdir/artifacts/smoke-test-report.json
      ${{ runner.temp }}/ir-smoke-workdir/snapshots/runs/**
      ${{ runner.temp }}/ir-smoke-workdir/reports/runs/**
    if-no-files-found: warn
    retention-days: 7
```

Do not upload from `reports/analysis/` or any `$GITHUB_WORKSPACE` run output path.

#### Step 6 — Cleanup

```yaml
- name: Cleanup smoke workdir
  if: always()
  run: rm -rf "${{ runner.temp }}/ir-smoke-workdir"
```

---

## Orchestrator: required pipeline stage behavior

### Daily Runner stage

- Run for the five hardcoded smoke candidates.
- Use a clean SQLite state DB under `SMOKE_WORKDIR` (via `chdir`).
- All outputs must land under `SMOKE_WORKDIR`.
- Assert after completion:
  - `daily_bar_id` in run metadata matches the ID passed via `--daily-bar-id`.
  - `run.manifest.json` exists under `SMOKE_WORKDIR/snapshots/runs/YYYY/MM/DD/<run_id>/`.
  - `symbol_diagnostics.jsonl.gz` exists under
    `SMOKE_WORKDIR/reports/runs/YYYY/MM/DD/<run_id>/`.
  - No manifest file exists under `SMOKE_WORKDIR/reports/runs/`.
  - No file was written under `SMOKE_WORKDIR/reports/analysis/`.
  - At least one symbol appears in the diagnostics file. Any decision bucket is acceptable.

### Intraday Runner stage

- Run using the same temporary state DB against the `--intraday-bar-id` value.
- Assert after completion:
  - Run completed without unhandled exception, or produced a clean no-op if no new 4h bar
    is available.
  - In the no-op case: no spurious manifest or diagnostics artifact is created under
    `SMOKE_WORKDIR/reports/runs/` or any non-canonical location.
  - If a run was produced: `intraday_bar_id` in run metadata is a canonical
    `YYYY-MM-DDTHH:00:00Z` string.
  - No integer or digit-string `intraday_bar_id` appears in any written artifact.
  - Any intraday manifest reference points to `SMOKE_WORKDIR/snapshots/runs/...`,
    not `SMOKE_WORKDIR/reports/runs/...`.
  - No file was written under `SMOKE_WORKDIR/reports/analysis/`.

### Evaluation Replay stage

- Run from the artifacts produced by the Daily and Intraday stages.
- Skip only if both prior stages produced no artifacts.
- Assert after completion:
  - Replay completed without unhandled exception.
  - Replay read from run manifest and diagnostics artifacts, not from live SQLite state.
  - Split layout was respected: manifest from `SMOKE_WORKDIR/snapshots/runs/...`,
    diagnostics from `SMOKE_WORKDIR/reports/runs/...`.
  - If events exist in the smoke artifacts: terminal events were not enriched with forward
    returns, MFE, or MAE; valid `0` / `0.0` confidence and priority values were not treated
    as missing or invalid. These semantic assertions must be enforced only when corresponding
    events or fields exist in the produced smoke artifacts. Absence of such events is not a
    smoke failure.
  - If no eligible events exist: `NO_EVENTS` or an equivalent empty export is an acceptable
    result, provided artifact loading, split-layout resolution, and replay initialization
    all succeeded without live SQLite access.

### Summary report

The orchestrator writes `SMOKE_WORKDIR/artifacts/smoke-test-report.json` with at minimum:

```json
{
  "daily_bar_id": "...",
  "intraday_bar_id": "...",
  "run_id": "...",
  "steps": {
    "daily_runner": "PASS|FAIL|SKIP",
    "intraday_runner": "PASS|FAIL|SKIP|NOOP",
    "evaluation_replay": "PASS|FAIL|SKIP|NO_EVENTS"
  },
  "artifacts_written": [],
  "unexpected_path_writes": [],
  "warnings": [],
  "errors": [],
  "follow_up_required": true
}
```

---

## Acceptance criteria

The ticket is complete only if all of the following are true.

### Workflow

- `.github/workflows/independence-smoke-test.yml` exists.
- Trigger is `workflow_dispatch` only — no schedule, no push trigger.
- `permissions.contents: read` is set.
- No `git add`, `git commit`, or `git push` step exists.
- Standard setup steps are present: `actions/checkout@v5`, `actions/setup-python@v6`,
  `pip install -r requirements.txt`.
- `SMOKE_WORKDIR` is set to `${{ runner.temp }}/ir-smoke-workdir`.
- `SCANNER_CONFIG_PATH` is set to an absolute path under `${{ github.workspace }}`.
- All run outputs land under `SMOKE_WORKDIR`, not under `$GITHUB_WORKSPACE`.
- Connectivity preflight runs before any pipeline stage.
- Bar clock step uses `$GITHUB_OUTPUT`, not the deprecated `::set-output` syntax.
- Bar clock step calls the actual functions present in `scanner/data/bar_clock.py` with
  correct signatures verified against the current module.
- Bar clock step outputs are passed to the orchestrator via `--daily-bar-id` and
  `--intraday-bar-id`.
- Cleanup step runs with `if: always()`.
- Upload step runs with `if: always()`, uses `${{ runner.temp }}/ir-smoke-workdir/...`
  paths, `if-no-files-found: warn`, and `retention-days: 7`.

### Orchestrator

- `scripts/run_independence_smoke_test.py` exists.
- Accepts `--workdir` (required), `--daily-bar-id`, and `--intraday-bar-id`.
- Smoke candidate list is hardcoded as `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `INJUSDT`,
  `ARBUSDT`.
- Resolves `SCANNER_CONFIG_PATH` to an absolute path before changing working directory.
- Changes working directory to `SMOKE_WORKDIR` before invoking runners and restores it in
  a `finally` block.
- Does not modify any file under `scanner/`.
- Does not use mocked or simulated API responses.
- Writes all outputs under the provided `--workdir`.
- Exits with code `1` on any FAIL assertion.
- Writes `artifacts/smoke-test-report.json` under `--workdir`.

### Artifact location assertions

- Canonical manifest path assertion is explicit with `exit 1` on failure.
- No `reports/runs/*.manifest.json` assertion handles missing directory safely.
- No `reports/analysis/` write assertion handles missing directory safely.
- `git status --short` check confirms repository checkout is clean of any run artifacts,
  including SQLite DB files under `data/`.

### Artifact upload

- Upload covers `smoke-test-report.json`, `snapshots/runs/**`, `reports/runs/**` under
  `${{ runner.temp }}/ir-smoke-workdir/`.
- Upload uses `if: always()`, `if-no-files-found: warn`, and `retention-days: 7`.
- No upload from `reports/analysis/` or `$GITHUB_WORKSPACE` run output paths.

### No production code changes

- No changes to `scanner/runners/daily.py`.
- No changes to `scanner/runners/intraday.py`.
- No changes to `scanner/evaluation/replay.py`.
- No changes to `scanner/main.py`.
- No changes to `scanner/data/bar_clock.py`.
- No changes to any schema, config default, or canonical path definition.

### Documentation

- Update `README.md` or an existing developer/operations document. Do not create a new
  parallel authority document.
- Documentation states: fixed smoke candidate list, manual trigger only, outputs not
  committed back to repository, executability check only.

---

## Non-goals and anti-requirements

Codex must not:

- Modify Daily Runner, Intraday Runner, Evaluation Replay, `scanner/main.py`, or
  `scanner/data/bar_clock.py`.
- Modify report schemas, snapshot schemas, or evaluation metrics.
- Modify bar-clock logic or canonical ID definitions.
- Modify existing workflows (`run-analysis-script.yml`, `code-map.yml`, `gpt-snapshot.yml`).
- Use mocked or simulated MEXC API responses.
- Commit or push run artifacts back to the repository.
- Write any run output under `$GITHUB_WORKSPACE`.
- Use `reports/analysis/` as an output or upload path.
- Add a scheduled or push trigger.
- Make business-logic assertions (score values, bucket distributions, phase outcomes).
- Introduce a new canonical output root beyond the four allowed roots.
- Treat the five smoke candidates as a canonical production universe or introduce them into
  any config default or production filter.
- Use the deprecated `::set-output` GitHub Actions syntax.
- Omit the `finally` block when restoring the working directory after `chdir`.
- Rely on a relative config path after changing the working directory to `SMOKE_WORKDIR`.
- Invent bar-clock function names — use only functions that actually exist in
  `scanner/data/bar_clock.py` with their actual signatures.
- Create a new documentation authority file; update existing docs only.

---

## Suggested implementation sequence

1. Inspect `scanner/data/bar_clock.py` and record the exact function names and signatures
   available for resolving `daily_bar_id` and `intraday_bar_id`.
2. Inspect `scanner/runners/daily.py` and `scanner/runners/intraday.py` to determine how
   output paths and DB paths are resolved (relative to `cwd` or via explicit parameters).
3. Inspect `scanner/evaluation/replay.py` entry point and artifact path resolution.
4. Determine whether MEXC public endpoints require API credentials for the smoke candidate
   path; document the finding inline in the orchestrator.
5. Implement `scripts/run_independence_smoke_test.py`:
   - `--workdir`, `--daily-bar-id`, `--intraday-bar-id` argument parsing
   - absolute config path resolution
   - `chdir` to `SMOKE_WORKDIR` with `finally` restore
   - Daily Runner invocation with smoke providers and assertions
   - Intraday Runner invocation with assertions and no-op handling
   - Evaluation Replay invocation with assertions and `NO_EVENTS` handling
   - JSON summary report
6. Implement `.github/workflows/independence-smoke-test.yml`:
   - standard setup steps
   - env setup (`SMOKE_WORKDIR`, `SCANNER_CONFIG_PATH`)
   - connectivity preflight
   - bar-clock sanity step using actual `bar_clock.py` signatures and `$GITHUB_OUTPUT`
   - orchestrator invocation with bar-clock step outputs
   - shell-level artifact assertions including `git status` check
   - upload step
   - cleanup step
7. Update `README.md` or existing developer/operations doc.
8. Run the workflow manually on a branch to verify end-to-end.

---

## Review checklist for Codex before final response

Before reporting completion, verify:

- [ ] `scanner/data/bar_clock.py` was inspected; bar-clock calls use actual function names
      and signatures from the current module.
- [ ] `.github/workflows/independence-smoke-test.yml` exists with `workflow_dispatch` only.
- [ ] `permissions.contents: read` is set.
- [ ] No `git add`, `git commit`, or `git push` step exists.
- [ ] Standard setup steps present: checkout, setup-python, pip install.
- [ ] `SMOKE_WORKDIR` is `${{ runner.temp }}/ir-smoke-workdir`.
- [ ] `SCANNER_CONFIG_PATH` is set to an absolute path under `${{ github.workspace }}`.
- [ ] Bar clock step uses `$GITHUB_OUTPUT`, not `::set-output`.
- [ ] Bar clock outputs `daily_bar_id` and `intraday_bar_id` are passed to the orchestrator.
- [ ] Smoke candidate list is hardcoded as `SOLUSDT AVAXUSDT LINKUSDT INJUSDT ARBUSDT`.
- [ ] Orchestrator resolves config path to absolute before `chdir`.
- [ ] Orchestrator calls `chdir(SMOKE_WORKDIR)` and restores in `finally`.
- [ ] No scanner production file was modified.
- [ ] No mocked or simulated API responses are used.
- [ ] Canonical manifest path assertion uses `exit 1` on failure.
- [ ] All shell assertions handle missing directories safely (`2>/dev/null`).
- [ ] `git status --short` check confirms checkout clean of run artifacts including `data/`.
- [ ] Evaluation Replay accepts `NO_EVENTS` as a valid smoke result.
- [ ] Semantic replay assertions are conditional on events/fields being present.
- [ ] Upload uses `${{ runner.temp }}/ir-smoke-workdir/...` paths, `if: always()`,
      `if-no-files-found: warn`, and `retention-days: 7`.
- [ ] `smoke-test-report.json` is produced and included in the upload.
- [ ] Cleanup step runs with `if: always()`.
- [ ] Documentation updated in `README.md` or existing dev/ops doc — no new authority file.
