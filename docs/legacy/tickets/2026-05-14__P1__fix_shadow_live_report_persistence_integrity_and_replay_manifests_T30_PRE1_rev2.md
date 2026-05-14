> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# Fix Shadow-Live Report Persistence Integrity and Replay Manifest Availability

**Ticket ID:** T30_PRE1_PERSISTENCE_INTEGRITY_AND_REPLAY_MANIFESTS  
**Priority:** P1  
**Status:** Draft for implementation  
**Date:** 2026-05-14  
**Target schema:** no diagnostics schema bump expected  
**Expected PR size:** Small/medium, one PR only  
**Primary owner:** Codex implementation  
**Review focus:** persistence integrity, artifact copy paths, non-empty JSON guards, replay manifest allowlist, no large artifact commits

---

## 1. Authoritative context

This ticket is a precondition for T30 Forward-Return Evaluation.

T18 already implemented the technical evaluation/replay machinery. T30 should later execute that machinery on accumulated Shadow-Live data. Current repo reality blocks that execution:

1. persisted report/index JSON files in the repository are partially empty,
2. T18 replay requires `snapshots/runs/**/run.manifest.json`, but those manifests are currently not persisted to the repository,
3. current report persistence commits only selected `reports/**` files and does not persist replay manifests.

Authoritative references for this ticket:

1. The 7 v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `docs/canonical/SNAPSHOTS.md`.
4. `docs/canonical/REPORTS.md`.
5. `docs/AI_CONTEXT_CURRENT.md`.
6. Existing T18 implementation in:
   - `scanner/evaluation/replay.py`
   - `scanner/evaluation/forward_returns.py`
   - `scanner/evaluation/dataset_export.py`
7. Existing Shadow-Live workflow and persistence implementation:
   - `.github/workflows/independence-shadow-live.yml`
   - `scripts/persist_shadow_live_reports.py`
8. Existing tests around snapshot storage, output artifacts, Shadow-Live, and persistence.

If the current authoritative reference set, repo canonical documents, and existing code collide, the v2.1 reference set plus this ticket's explicit requirements win. Existing repo documents remain valid only where they do not conflict with this ticket.

---

## 2. Problem statement

### 2.1 Empty persisted JSON files

Repo inspection showed a corrupt/inconsistent persistence state:

- some persisted index files are valid and non-empty, for example:
  - `reports/index/latest.json`
  - `reports/index/latest_paths.json`
  - `reports/index/recent_runs.json`
  - `reports/index/latest_confirmed_candidates.json`
- but other persisted files are empty, for example:
  - `reports/index/latest_daily.json`
  - `reports/daily/2026/05/12/report.json`
  - `reports/runs/2026/05/12/daily-2026-05-12-f3ed01869b4c/report.json`

This must not be possible. Report/index files that are committed to the repo must be non-empty valid JSON, except `latest_run.txt`, which is plain text and must be non-empty.

### 2.2 Replay manifests are referenced but missing

Current index files can reference manifest paths such as:

```text
snapshots/runs/2026/05/12/daily-2026-05-12-f3ed01869b4c/run.manifest.json
snapshots/runs/2026/05/12/intraday-2026-05-12-49beeb738502/run.manifest.json
```

T18 replay uses:

```text
snapshots/runs/**/run.manifest.json
```

as the starting point for event reconstruction.

But the current repo does not persist those manifest files. The Shadow-Live workflow uploads `snapshots/runs/**` only in the large CI artifact, while the report-persistence job commits only selected `reports/**` files.

Result: T30 cannot reconstruct an event timeline from the repository even if report files exist.

### 2.3 This ticket is not OHLCV history work

This ticket does not build `snapshots/history/ohlcv/...` Parquet history. That is a separate follow-up decision and ticket.

This ticket only fixes report persistence integrity and persists the minimal replay manifest files required by T18.

---

## 3. Current repo behavior to inspect first

Before changing code, inspect and document the actual cause of empty JSON persistence.

Codex must inspect at minimum:

```text
.github/workflows/independence-shadow-live.yml
scripts/persist_shadow_live_reports.py
scanner/output/report_builder.py
scanner/storage/snapshots.py
scripts/run_independence_shadow_live.py
```

and relevant tests.

The implementation must determine whether empty JSON files are caused by one of these layers:

1. report generation writes empty files,
2. upload-artifact path or timing captures empty files,
3. download-artifact layout changes source paths,
4. `persist_shadow_live_reports.py` copies from the wrong source path,
5. idempotency/skip behavior leaves previously corrupted empty files untouched,
6. a different repo-real cause.

Do not assume the cause. Fix the actual layer.

---

## 4. Scope

### 4.1 In scope

1. Diagnose and fix empty JSON persistence for report/index and report/run files.
2. Add validation so the persistence helper refuses to commit empty or invalid JSON files.
3. Add validation so `latest_run.txt` is non-empty before commit.
4. Persist minimal replay manifests:

```text
snapshots/runs/**/run.manifest.json
```

5. Ensure only `run.manifest.json` files are persisted from `snapshots/runs`.
6. Keep existing report persistence idempotency semantics.
7. Keep push gating on `created_commit == true`.
8. Add tests covering empty JSON, invalid JSON, manifest allowlist, and forbidden files.
9. Update minimal documentation if existing canonical docs describe report persistence or replay inputs incorrectly.

### 4.2 Out of scope

Do not implement any of the following in this ticket:

- Do not implement T30 Forward-Return Evaluation.
- Do not build or persist OHLCV Parquet history.
- Do not modify `scanner/evaluation/forward_returns.py` logic except tests if necessary to keep current behavior passing.
- Do not change T18 event semantics.
- Do not change T_EL2 logic.
- Do not change Q1/Q2 operational tradeability logic.
- Do not change candidate bucket semantics.
- Do not commit `symbol_diagnostics.jsonl.gz`.
- Do not commit Parquet files.
- Do not commit SQLite state.
- Do not commit ZIP artifacts.
- Do not commit raw market data.
- Do not commit `run.snapshot.json`, symbol snapshots, debug dumps, or other large snapshot payloads.
- Do not broaden persistence to arbitrary `reports/**` or arbitrary `snapshots/**`.

---

## 5. Required final persistence allowlist

The persistence helper must use an explicit allowlist.

### 5.1 Allowed report/index files

Persist only these index files when present and valid:

```text
reports/index/latest_run.txt
reports/index/latest.json
reports/index/latest_daily.json
reports/index/latest_intraday.json
reports/index/latest_confirmed_candidates.json
reports/index/latest_watchlist.json
reports/index/latest_paths.json
reports/index/recent_runs.json
```

Notes:

- `latest_run.txt` is plain text and must be non-empty after stripping whitespace.
- All `.json` files must be non-empty valid JSON.
- `latest_intraday.json` must be included if produced by the current report builder.
- Missing optional index files should not fail the persistence job unless the current report contract marks them required.

### 5.2 Allowed report files

Persist only:

```text
reports/daily/**/report.json
reports/runs/**/report.json
```

Each persisted `report.json` must be:

```text
non-empty valid JSON object
```

A zero-byte `report.json`, whitespace-only `report.json`, or invalid JSON file must not be committed.

### 5.3 Allowed replay manifest files

Persist only:

```text
snapshots/runs/**/run.manifest.json
```

Each persisted `run.manifest.json` must be:

```text
non-empty valid JSON object
```

Required minimum fields:

```text
run_id
```

If the existing manifest contract requires additional fields, preserve that existing contract and test it.

### 5.4 Explicitly forbidden files

Never persist:

```text
reports/runs/**/symbol_diagnostics.jsonl.gz
snapshots/runs/**/run.snapshot.json
snapshots/runs/**/*.jsonl
snapshots/runs/**/*.jsonl.gz
snapshots/runs/**/*.parquet
snapshots/history/**
evaluation/exports/**
evaluation/replay/**
*.sqlite
*.zip
*.xlsx
```

Do not use broad commands such as:

```bash
git add reports/
git add snapshots/
```

Always stage only explicitly allowed paths.

---

## 6. Required behavior

### 6.1 Diagnose-first behavior

Before changing the persistence implementation, Codex must identify which layer causes the empty persisted JSON files.

The PR description must include a short diagnostic note:

```text
Root cause found: <report generation | artifact upload | artifact download layout | copy/staging logic | idempotency interaction | other>
Fix applied at: <file/function/workflow step>
```

If multiple causes exist, list all.

### 6.2 Source validation before copy/stage

Before copying or staging an allowed file, validate it according to file type.

For `.json` files:

- file exists,
- file is a regular file,
- file size > 0,
- stripped content is non-empty,
- JSON parses successfully,
- top-level JSON type is correct:
  - `dict` for `report.json`, `latest.json`, `latest_daily.json`, `latest_intraday.json`, `latest_paths.json`, `run.manifest.json`
  - `list` or existing contract type for `recent_runs.json`, `latest_confirmed_candidates.json`, `latest_watchlist.json`

For `latest_run.txt`:

- file exists,
- file is a regular file,
- stripped content is non-empty.

Invalid allowed files must fail the persistence step with a clear error message. Do not silently skip a required/currently produced allowed file if it is present but empty or invalid.

### 6.3 Destination validation after copy

After copying allowed files into the repo checkout, validate the destination copy as well.

This catches truncation/copy errors.

### 6.4 Idempotency anchor remains daily report

Keep the existing idempotency anchor:

```text
reports/runs/YYYY/MM/DD/<daily_run_id>/report.json
```

The daily run id is read from `reports/index/latest_daily.json` in the source artifact.

If the daily anchor already exists in the repo and is valid non-empty JSON, persistence may skip without creating a commit.

If the daily anchor exists but is empty or invalid JSON, the helper must not treat that as a valid idempotency skip. It must repair/replace it from the current valid source artifact or fail clearly if the source is not valid.

### 6.5 Existing corrupted empty files

If the repo already contains empty persisted files at paths that this ticket now validates, the next successful persistence run must be able to replace them with valid non-empty files.

Do not make idempotency skip over an existing empty anchor.

### 6.6 Replay manifest availability

After a successful persistence run, for every persisted run report:

```text
reports/runs/YYYY/MM/DD/<run_id>/report.json
```

there should be a corresponding persisted manifest if it exists in the source artifact:

```text
snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
```

If a persisted report references a manifest path in its metadata or index fields, that manifest must be persisted when present in the source artifact.

If a report is persisted but the matching manifest is absent from the source artifact, the persistence helper must fail clearly rather than silently creating a replay-incomplete repo state.

### 6.7 Artifact transfer between jobs

The `shadow-live` job and `persist-reports` job run in separate runner environments.

If `snapshots/runs/**/run.manifest.json` is needed by the persistence job, the workflow must upload it from the `shadow-live` job and download it in the `persist-reports` job.

Preferred change:

- include the manifest allowlist in the existing `shadow-live-reports` upload artifact, or
- add a separate small artifact for replay manifests.

Do not rely on filesystem access across jobs.

### 6.8 Push behavior

Keep the existing push guard:

```yaml
if: steps.persist_reports.outputs.created_commit == 'true'
```

No push should run if the helper did not create a commit.

### 6.9 Determinism

For identical source artifact contents and identical repo state:

- copied paths are identical,
- staged paths are identical,
- validation result is identical,
- `created_commit` output is identical.

Do not rely on unordered directory iteration. Sort matched paths before copy/stage.

---

## 7. Implementation guidance

### 7.1 Likely files to modify

Likely implementation files:

```text
scripts/persist_shadow_live_reports.py
.github/workflows/independence-shadow-live.yml
```

Likely tests:

```text
tests/test_shadow_live_report_persistence.py
```

or an existing persistence-related test file if one already exists.

Documentation updates only if needed:

```text
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/AI_CONTEXT_CURRENT.md
```

Do not create a second persistence helper unless the existing helper cannot be extended safely.

### 7.2 Suggested helper functions

Codex may add helper functions like:

```python
def _validate_json_file(path: Path, *, expected_type: type, label: str) -> None: ...
def _validate_text_file(path: Path, *, label: str) -> None: ...
def _allowed_manifest_paths(source_root: Path) -> list[Path]: ...
```

Names are suggestions only. Reuse existing style.

### 7.3 Source root handling

The current helper supports source roots where the downloaded artifact may either contain:

```text
reports/...
```

or directly:

```text
index/...
daily/...
runs/...
```

Preserve this compatibility for reports.

For manifests, support the actual downloaded artifact layout introduced by the workflow change. Do not guess blindly; write tests for the supported layout.

### 7.4 Avoiding large snapshot persistence

When scanning source artifacts for manifests, match exactly:

```text
snapshots/runs/*/*/*/*/run.manifest.json
```

or the equivalent layout under the downloaded artifact root.

Do not use:

```text
snapshots/runs/**
```

as a staging path.

---

## 8. Tests required

Add or update tests so each behavior below is covered.

### 8.1 Valid report persistence still works

Given a source artifact with:

```text
reports/index/latest_daily.json
reports/index/latest.json
reports/index/latest_paths.json
reports/index/latest_run.txt
reports/runs/2026/05/12/daily-2026-05-12-abc/report.json
reports/daily/2026/05/12/report.json
snapshots/runs/2026/05/12/daily-2026-05-12-abc/run.manifest.json
```

Expected:

- all allowed valid files are copied,
- allowed files are staged,
- commit is created when repo has no prior daily anchor,
- `created_commit=true` is emitted.

### 8.2 Empty JSON source is rejected

Given source artifact contains an allowed JSON file that is zero bytes or whitespace-only, for example:

```text
reports/index/latest_daily.json
```

Expected:

- persistence fails with a clear error,
- no commit is created,
- `created_commit=false` is emitted if the helper reaches controlled failure handling, or no output is acceptable if the process exits before output emission according to existing test conventions.

### 8.3 Invalid JSON source is rejected

Given source artifact contains invalid JSON in an allowed `.json` path:

Expected:

- persistence fails with a clear error naming the path,
- no commit is created.

### 8.4 Existing empty repo anchor does not trigger idempotency skip

Given repo contains:

```text
reports/runs/2026/05/12/daily-2026-05-12-abc/report.json
```

but it is empty or invalid, and the source artifact contains a valid report for the same path:

Expected:

- helper does not print the idempotency skip message,
- helper replaces the empty/invalid file with valid content,
- commit is created if resulting repo diff is non-empty.

### 8.5 Valid existing repo anchor still skips

Given repo contains a valid non-empty daily anchor report for the same daily run id:

Expected:

- helper skips persistence,
- no commit is created,
- `created_commit=false` is emitted,
- no push step is eligible.

### 8.6 Manifests are persisted

Given matching source manifest:

```text
snapshots/runs/2026/05/12/daily-2026-05-12-abc/run.manifest.json
```

Expected:

- copied to repo at the same relative path,
- staged if changed,
- valid JSON object,
- contains at least `run_id`.

### 8.7 Large snapshot payloads are not persisted

Given source artifact also contains:

```text
snapshots/runs/2026/05/12/daily-2026-05-12-abc/run.snapshot.json
snapshots/runs/2026/05/12/daily-2026-05-12-abc/symbols.jsonl.gz
snapshots/runs/2026/05/12/daily-2026-05-12-abc/anything.parquet
reports/runs/2026/05/12/daily-2026-05-12-abc/symbol_diagnostics.jsonl.gz
```

Expected:

- none of these files are copied or staged,
- only `run.manifest.json` from `snapshots/runs` is eligible.

### 8.8 Workflow artifact transfer includes manifests

Verify the concrete workflow artifact path and helper source-root layout.

Expected workflow behavior:

- the `shadow-live` upload-artifact step includes the small replay manifests explicitly, for example:

```text
${{ runner.temp }}/ir-shadow-live-workdir/snapshots/runs/**/run.manifest.json
```

- the `persist-reports` download-artifact step downloads to a root from which `scripts/persist_shadow_live_reports.py` can find manifests at the expected relative path, for example:

```text
<source-root>/snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
```

- add a unit test with a fixture source root containing:

```text
snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
```

Expected test result:

- the helper copies the manifest to the repo checkout at the same relative path,
- the helper validates it as non-empty JSON object,
- the helper stages it if changed,
- no broad `snapshots/runs/**` payload is copied or staged.

Do not satisfy this requirement with a comment-only or purely superficial workflow string test. The test must prove that a manifest in the downloaded artifact layout is actually discoverable and copyable by the helper.

### 8.9 Push remains gated by commit creation

Existing behavior must remain:

```yaml
if: steps.persist_reports.outputs.created_commit == 'true'
```

Add or preserve a test/inspection assertion where practical.

### 8.10 No broad git add

Test or code-inspect that the helper stages explicit paths only.

Forbidden:

```bash
git add reports/
git add snapshots/
```

---

## 9. Acceptance criteria

This ticket is complete only if all criteria below are met.

1. The root cause of empty persisted JSON files is identified in the PR description.
2. Empty allowed JSON files are never committed by the persistence helper.
3. Invalid allowed JSON files are never committed by the persistence helper.
4. `latest_run.txt` is validated as non-empty plain text.
5. Existing valid idempotency behavior is preserved.
6. Existing empty/invalid repo anchor files do not cause false idempotency skips.
7. `snapshots/runs/**/run.manifest.json` is persisted for runs whose reports are persisted.
8. No large snapshot files are persisted.
9. No diagnostics `.jsonl.gz` files are persisted.
10. No Parquet files are persisted.
11. No SQLite or ZIP files are persisted.
12. The persistence job receives manifest files via artifact upload/download, not cross-job filesystem assumptions.
13. `created_commit=false` is emitted on no-op/skip/no-change paths.
14. The push step still runs only when `created_commit == true`.
15. Tests cover valid persistence, empty JSON rejection, invalid JSON rejection, corrupted anchor repair, manifest allowlist, forbidden files, and idempotency skip.
16. Existing Shadow-Live workflow behavior is otherwise unchanged.
17. T18 replay can discover at least the persisted `run.manifest.json` files from the repository after a successful future Shadow-Live persistence run.
18. Known existing empty persisted JSON files are either replaced with valid source content or removed if valid source content is unavailable.

---

## 10. Definition of done

- Code changes are limited to persistence/workflow/test/doc areas needed for this ticket.
- Relevant tests pass.
- Full test command is run unless too expensive; if not run, Codex must state why and run the narrow relevant tests.
- PR description includes:
  - root cause of empty JSON persistence,
  - exact files changed,
  - whether workflow artifact layout changed,
  - proof that only `run.manifest.json` is persisted from `snapshots/runs`,
  - test commands and results.

Suggested test commands:

```bash
python -m pytest -q tests/test_shadow_live_report_persistence.py
python -m pytest -q tests/test_ticket18_evaluation_replay.py tests/test_ticket14_snapshot_storage_contract.py tests/test_ticket13_output_artifacts.py
python -m pytest -q
```

Use actual test filenames if the repo has different names.

---

## 11. Post-merge validation

Before or during post-merge validation, manually address the known corrupted empty files identified during diagnosis:

```text
reports/index/latest_daily.json
reports/runs/2026/05/12/daily-2026-05-12-f3ed01869b4c/report.json
reports/daily/2026/05/12/report.json
```

These files may not be auto-repaired by future persistence runs if their run IDs do not match a future daily idempotency anchor. If valid source artifacts for those exact runs are still available, replace the empty files with valid non-empty JSON from the source artifact. If valid source artifacts are not available, delete the empty files from the repository so T18/T30 tooling does not treat them as present-but-unreadable inputs.

After merge and the next Shadow-Live run:

1. Check repository files:

```text
reports/index/latest_daily.json
reports/runs/YYYY/MM/DD/<daily_run_id>/report.json
reports/daily/YYYY/MM/DD/report.json
snapshots/runs/YYYY/MM/DD/<daily_run_id>/run.manifest.json
```

2. Confirm they are non-empty.
3. Confirm all JSON files parse.
4. Confirm `latest_paths.json` manifest paths resolve to existing repo files for persisted runs.
5. Confirm no forbidden files were committed.
6. Confirm `scanner.evaluation.replay.reconstruct_event_timeline(project_root=repo_root)` sees persisted manifests and does not report all runs as missing diagnostics.

This post-merge validation is not T30 itself. It only proves the repository now contains the minimal replay metadata required for T30-Pre-2 and T30.

---

## 12. Notes for later tickets

This ticket intentionally does not solve the OHLCV history problem.

The next ticket should decide and implement the OHLCV strategy for T30, likely:

```text
candidate-/event-scoped 1d OHLCV history for all symbols that ever appeared in confirmed_candidates or early_candidates within the selected evaluation window.
```

Do not sneak that logic into this PR.
