# 2026-05-12 — P1 — Automated Shadow-Live Report Persistence

Status: Draft for review  
Priority: P1  
Target PR size: 1 PR  
Language: English  
Implementation owner: Codex  
Review mode: adversarial review before merge

---

## 1. Purpose

Persist small Shadow-Live report artifacts into the repository after successful runs so that downstream analyses no longer depend on manual ZIP artifact downloads.

This ticket enables later work such as:

- T_EL2 post-run validation / calibration over accumulated runs
- Q1/Q2 analysis with a broader historical report base
- T25-style aggregation without manual artifact handling
- later T30 forward-return evaluation preparation

This ticket does **not** implement evaluation, aggregation, forward returns, or any new trading/decision logic.

---

## 2. Authoritative references and hierarchy

If the current authoritative v2.1 specification, canonical repo docs, and existing code conflict, the current v2.1 authoritative reference set wins. Existing repo docs remain valid only insofar as they do not contradict that reference set.

Authoritative / guiding references:

1. The 7 v2.1 specification section files
2. `independence_release_gesamtkonzept_final.md`
3. Current canonical docs, only where not conflicting with v2.1
4. `docs/canonical/open_questions.md`
5. `docs/canonical/feature_enhancements.md`
6. Current Shadow-Live workflow implementation, especially T22/T25-era report artifact behavior
7. Master ticket preflight checklist

Relevant established principles:

- Report and diagnostic output are durable architecture, not temporary ZIP-only artifacts.
- `reports/index/` and `reports/runs/...` are part of the intended report architecture.
- Evaluation is a core future component, but this ticket only creates the persistence precondition.
- Large diagnostics and market data must not be committed as regular repo data.
- One change per step.

---

## 3. Problem statement

Current Shadow-Live runs produce useful report files as GitHub Actions artifacts, but these files are not accumulated in the repository.

As a result:

- multi-run analyses require manual ZIP downloads;
- T_EL2 status/action-hint distributions do not accumulate automatically;
- Q1/Q2 tradeability/exclusion analysis requires ad-hoc artifact handling;
- T30 preparation remains blocked by manual report collection.

The intended architecture already distinguishes small report/index files from large diagnostics and raw data. This ticket implements persistence only for the small report/index layer.

---

## 4. Scope

### In scope

Add an automated persistence step after successful Shadow-Live report generation that commits only small plaintext report/index artifacts.

Persist these paths if they exist and are non-large:

```text
reports/index/latest.json
reports/index/latest_daily.json
reports/index/latest_confirmed_candidates.json
reports/index/latest_watchlist.json
reports/index/latest_paths.json
reports/index/recent_runs.json

reports/daily/YYYY/MM/DD/report.json
reports/runs/YYYY/MM/DD/<run_id>/report.json
```

Optionally persist Markdown reports only if they exist and are meaningfully populated:

```text
reports/daily/YYYY/MM/DD/report.md
reports/runs/YYYY/MM/DD/<run_id>/report.md
```

`report.md` files must not be committed if they are missing, trivial empty stubs, or placeholder-only files.

### Explicitly out of scope

Do **not** commit or implement persistence for:

```text
symbol_diagnostics.jsonl.gz
report.xlsx
*.xlsx
*.parquet
OHLCV snapshots
raw market data
large debug artifacts
profiling artifacts
zip artifacts
full diagnostics archives
```

Also out of scope:

- no T_EL2 logic changes;
- no decision bucket changes;
- no tradeability/execution changes;
- no Q1/Q2 semantic decision;
- no T30 forward-return evaluation;
- no aggregation job;
- no new report schema beyond what is needed for persistence metadata if already available;
- no large artifact retention policy changes.

---

## 5. Required behavior

### 5.1 Persistence trigger

Add the persistence step after the Shadow-Live run has completed and report files have been written.

The persistence step must run only after a successful scan/report-generation step.

It must not mask or alter the scan step's exit code.

### 5.2 Idempotency rule

Before creating a commit, check whether the canonical daily run report already exists in the repository:

```text
reports/runs/YYYY/MM/DD/<daily_run_id>/report.json
```

For this ticket, the idempotency anchor is the **daily run report**. Shadow-Live workflows may also produce an intraday report in the same overall workflow run. Persist intraday run reports if they are present in the allowlisted downloaded report tree, but do **not** use the intraday run id as the idempotency anchor for this ticket.

If the daily run report already exists in the checked-out repository state, treat the persistence operation as already completed for that workflow retry:

```text
No commit should be created.
Exit successfully.
Log: report persistence skipped because daily run report already exists.
```

This is the required idempotency rule for workflow retries. Do not implement complex diff-based idempotency unless already trivial in the existing code path.

### 5.3 Commit scope

The commit must include only the allowed report/index files listed in this ticket.

Use explicit path allowlisting. Do not use broad commands such as:

```bash
git add reports/
git add .
```

unless combined with a strict allowlist and explicit exclusions that guarantee no forbidden files are staged.

Recommended behavior:

```bash
git add reports/index/latest.json \
        reports/index/latest_daily.json \
        reports/index/latest_confirmed_candidates.json \
        reports/index/latest_watchlist.json \
        reports/index/latest_paths.json \
        reports/index/recent_runs.json \
        reports/daily/YYYY/MM/DD/report.json \
        reports/runs/YYYY/MM/DD/<run_id>/report.json
```

Add `report.md` only after confirming it exists and is non-trivial.

### 5.4 Commit message

Use a deterministic commit message:

```text
Persist shadow-live reports for <run_id>
```

If the workflow has both daily and intraday runs, use the run id of the report being persisted. If only daily persistence is implemented in this ticket, use the daily run id.

### 5.5 Commit author

Use a deterministic bot identity, for example:

```bash
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
```

Reuse existing repo convention if one already exists.

### 5.6 No-op when there is nothing to commit

If the allowed files do not produce any staged diff, the step must exit successfully without creating a commit.

Log clearly:

```text
No report persistence changes to commit.
```

### 5.7 Failure behavior

The scan/report-generation step and the persistence/commit step must be separate workflow steps.

The persistence step must use:

```yaml
continue-on-error: false
```

or the equivalent default behavior.

Meaning:

- if the scan fails, the workflow fails because of the scan;
- if the scan succeeds but persistence fails, the workflow fails visibly at the persistence step;
- the persistence failure must not be hidden inside the scan step;
- the scan step must not receive a non-zero exit code caused by commit/push failure.

Do not combine scan execution and git commit/push into a single shell step.

---

## 6. GitHub Actions permission requirement

The existing Shadow-Live workflow baseline may use:

```yaml
permissions:
  contents: read
```

The new persistence operation requires write permission, but write access must be scoped as narrowly as GitHub Actions allows in this workflow.

Required implementation principle:

- Do not make the entire scan job broadly write-capable if the existing structure allows a separate persistence job or a locally scoped write permission.
- Prefer a separate downstream persistence job with `permissions: contents: write` that depends on the successful scan/report job.
- If the current workflow cannot support true step-level permissions because GitHub Actions permissions are job-scoped, then implement a separate `persist-reports` job rather than upgrading the whole scan job.

Required structure if feasible:

```yaml
jobs:
  shadow-live:
    permissions:
      contents: read
    steps:
      - run scan and write reports/artifacts
      - upload small report tree as an artifact for the persistence job

  persist-reports:
    needs: shadow-live
    if: success()
    permissions:
      contents: write
    steps:
      - checkout
      - download the report artifact from the scan job
      - idempotency check using the daily run report
      - allowlisted git add
      - commit and push
```

Because jobs run in separate runner environments, the scan job and persistence job must exchange files explicitly via GitHub Actions artifacts. Do not rely on filesystem state from the `shadow-live` job being available in `persist-reports`, and do not collapse the jobs merely to avoid artifact transfer.

If the existing workflow layout makes a separate job impractical, Codex must explain why and still keep write permission as narrow as possible. Do not silently elevate the full scan job to `contents: write` without justification.

---

## 7. Daily vs intraday handling

This ticket must preserve the index semantics fixed immediately before this ticket.

Required invariants:

- `latest.json` may point to the latest run of any scan mode.
- `latest_daily.json` points to the latest daily discovery run.
- `latest_confirmed_candidates.json` and `latest_watchlist.json` must not be cleared by intraday no-op or diagnostics-only runs.
- Candidate-oriented latest files are updated only by candidate-producing reports.

Report persistence must not reintroduce the previous bug by blindly committing candidate index files after they were incorrectly rewritten. It should persist the current output after the report builder has applied the correct index semantics.

Do not change the intraday/latest index logic in this ticket unless a small adjustment is necessary to preserve the already-fixed behavior.

---

## 8. Implementation guidance

### 8.1 Locate current workflow and report paths

Before editing, inspect:

```text
.github/workflows/*shadow*live*.yml
.github/workflows/*.yml
scanner/output/report_builder.py
scanner/runners/daily.py
scanner/runners/intraday.py
```

Use actual existing filenames and workflow names. Do not invent new paths if the repo already has the relevant workflow.

### 8.2 Preferred implementation approach

Preferred architecture:

1. Existing scan/report job writes reports as today.
2. Existing artifact upload remains unchanged.
3. The scan/report job additionally uploads the small report tree needed by persistence using `actions/upload-artifact@v4`.
4. The `persist-reports` job downloads that artifact using `actions/download-artifact@v4`.
5. The `persist-reports` job checks idempotency by looking for `reports/runs/YYYY/MM/DD/<daily_run_id>/report.json`.
6. The `persist-reports` job stages only allowed files.
7. The `persist-reports` job commits and pushes.

Required artifact transfer pattern:

```yaml
# In the shadow-live job, after report generation:
- name: Upload report persistence artifact
  uses: actions/upload-artifact@v4
  with:
    name: shadow-live-reports
    path: |
      reports/index/
      reports/daily/
      reports/runs/
    if-no-files-found: warn

# In the persist-reports job, before idempotency check:
- name: Download report persistence artifact
  uses: actions/download-artifact@v4
  with:
    name: shadow-live-reports
    path: .
```

Codex may adjust the artifact name if the existing workflow already has a naming convention, but the scan job must upload the report files and the persistence job must download them. Do not assume cross-job filesystem sharing.

### 8.3 Run id and date extraction

Use existing report metadata or existing path conventions to derive:

```text
YYYY
MM
DD
run_id
```

Do not parse fragile strings if structured metadata already exists in `report.json`, `latest_paths.json`, or existing workflow outputs.

If no structured metadata exists, implement the smallest robust path-based extraction and cover it with tests or shell assertions.

### 8.4 Markdown report inclusion rule

`report.md` may be committed only when:

- the file exists;
- file size is greater than a small non-trivial threshold; and
- it is not an obvious placeholder/stub.

A simple minimum byte-size check is acceptable. If uncertain, skip committing Markdown reports in v1 and commit only JSON/index files.

Default recommendation: JSON/index files are mandatory; Markdown reports are optional.

---

## 9. `.gitignore` hardening

The allowlisted `git add` logic is the primary protection against committing large files. Add a defense-in-depth `.gitignore` check as part of this ticket.

Before finalizing the implementation, verify that forbidden report/snapshot artifact types are ignored under the relevant paths. If missing, update `.gitignore` to cover at least:

```gitignore
# Large Shadow-Live / scanner artifacts must remain artifact-only
reports/**/*.jsonl.gz
reports/**/*.xlsx
reports/**/*.parquet
reports/**/*.zip
reports/**/symbol_diagnostics.jsonl.gz
snapshots/**/*.parquet
snapshots/**/*.jsonl.gz
```

Adapt patterns to existing repo conventions if equivalent rules already exist. Do not add ignore rules that would block the allowed plaintext `report.json`, `report.md`, or `reports/index/*.json` files.
---

## 10. Documentation updates

Update the relevant canonical/report/operations documentation to state:

- Shadow-Live report persistence commits only small plaintext report/index artifacts.
- Full diagnostics remain artifact-only and are not committed.
- `symbol_diagnostics.jsonl.gz`, Excel reports, Parquet, snapshots, and raw data are intentionally excluded.
- `reports/index/latest.json` is the latest run of any scan mode.
- `reports/index/latest_daily.json` is the latest daily discovery run.
- Candidate-specific latest files are candidate-effective latest outputs and must not be cleared by no-op/diagnostics-only intraday runs.
- Workflow retries are idempotent: if `reports/runs/YYYY/MM/DD/<run_id>/report.json` already exists, report persistence is skipped.

If the repo already has report persistence documentation, update it rather than creating a second competing truth.

---

## 11. Tests

Add or update tests where practical. If some behavior is only testable through workflow-level shell assertions, add a lightweight script/test helper if consistent with repo conventions.

Required test coverage:

### 11.1 Allowlist behavior

A test or script assertion must verify that forbidden file types are not staged/committed:

```text
symbol_diagnostics.jsonl.gz
*.xlsx
*.parquet
*.zip
```

### 11.2 Idempotency

Given a repo state where the daily run anchor already exists:

```text
reports/runs/YYYY/MM/DD/<daily_run_id>/report.json
```

already exists, the persistence logic must:

- skip staging/committing;
- exit successfully;
- log a clear skip message.

### 11.3 New run commit path

Given a new run where the canonical run report does not exist yet, the persistence logic must stage only allowed files and create a commit.

### 11.4 Empty/no-diff case

If allowed files exist but produce no staged diff, the step exits successfully without a commit.

### 11.5 Candidate index preservation

Ensure the new persistence workflow does not alter the already-fixed no-op intraday index semantics:

- intraday no-op / diagnostics-only runs must not clear `latest_confirmed_candidates.json`;
- intraday no-op / diagnostics-only runs must not clear `latest_watchlist.json`;
- daily candidate files remain valid after such runs.

### 11.6 Workflow permission and artifact-transfer shape

If practical, add a workflow lint/assertion or reviewable structure showing:

- scan job remains `contents: read`;
- scan job uploads the report persistence artifact via `actions/upload-artifact@v4`;
- persistence job or narrowly scoped equivalent uses `contents: write`;
- persistence job downloads the report persistence artifact via `actions/download-artifact@v4`.

At minimum, the workflow YAML must make this separation and artifact transfer obvious.

### 11.7 `.gitignore` hardening

Verify that `.gitignore` prevents accidental future staging of forbidden large artifacts under `reports/` and `snapshots/`, without blocking allowed plaintext report/index files.

---

## 12. Acceptance criteria

1. A successful Shadow-Live run can persist allowed report/index artifacts into the repository.
2. The implementation commits `report.json` and index JSON files only from the allowlist.
3. No `symbol_diagnostics.jsonl.gz` file is committed.
4. No Excel, Parquet, ZIP, raw OHLCV, or large debug artifact is committed.
5. The persistence step is idempotent via the canonical daily-run `reports/runs/YYYY/MM/DD/<daily_run_id>/report.json` existence check.
6. A workflow retry for an already-persisted run does not create a duplicate commit.
7. A no-diff allowed-file state does not create an empty commit.
8. Commit message is deterministic and includes `<run_id>`.
9. Scan/report generation and commit/push are separate workflow steps or separate jobs.
10. Commit/push failures are visible and fail the persistence step.
11. Commit/push failures are not hidden inside the scan step.
12. Existing artifact upload behavior remains intact.
13. The scan job explicitly uploads the report tree for the persistence job via `actions/upload-artifact@v4` or the repo's existing equivalent.
14. The persistence job explicitly downloads that report artifact via `actions/download-artifact@v4` or the repo's existing equivalent.
15. Existing intraday/latest index semantics remain intact.
16. `latest_confirmed_candidates.json` and `latest_watchlist.json` are not cleared by no-op or diagnostics-only intraday runs.
17. Documentation explains what is persisted and what remains artifact-only.
18. Tests or equivalent assertions cover allowlist, idempotency, and no-op candidate index preservation.
19. Relevant existing tests pass.
---

## 13. Definition of Done

- Code/workflow changes implemented.
- Documentation updated.
- Tests added or updated.
- Relevant test suite passes.
- Workflow YAML uses narrow write permission, preferably in a separate persistence job.
- Workflow YAML explicitly transfers reports from scan job to persistence job via upload/download artifact steps.
- `.gitignore` is verified/hardened so forbidden large artifacts remain artifact-only.
- Manual inspection confirms no forbidden file patterns are staged by the persistence logic.
- Codex reports:
  - changed files;
  - exact test commands and results;
  - whether a separate persistence job was used;
  - whether Markdown reports are included or skipped;
  - how idempotency is implemented;
  - how candidate index preservation was verified.

---

## 13. Codex handoff notes

Implement the smallest safe version. Do not overbuild a general artifact archival system.

The core of this ticket is:

```text
After a successful Shadow-Live run, persist only small report/index files, safely and idempotently, without granting write access to the scan job and without committing diagnostics or large data.
```

Do not start T30, do not add aggregation, and do not alter signal semantics.
