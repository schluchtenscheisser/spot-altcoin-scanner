> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket 19 — Harden Analysis Workflow and Script Output Conventions

## Status

Ready for Codex implementation.

## Purpose

Harden the repository's analysis script runner so that ad-hoc analysis scripts can be executed safely through GitHub Actions without creating permanent repository artifacts, without writing to deprecated output locations, and without accepting unsafe script paths.

This ticket is an infrastructure/conventions ticket. It does not change scanner business logic, Daily/Intraday runner logic, report schemas, snapshot schemas, evaluation metrics, or any v2.1 phase/state/decision semantics.

---

## Authoritative reference set

The current authoritative reference set for this ticket is:

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`, as supplemental context only where it does not conflict with the v2.1 sections or the consolidated concept.
4. The current repo reality, especially the existing `.github/workflows/run-analysis-script.yml`.
5. The master preflight checklist for Codex-ready tickets.

If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents continue to apply only insofar as they do not conflict with this reference set.

Existing repo paths/helpers may be reused if they do not conflict with the current authoritative reference set. Do not introduce a second competing output convention or workflow authority.

---

## Current problem

The existing analysis workflow currently violates the v2.1 output and CI artifact conventions:

- It uses a hardcoded `env.ANALYSIS_SCRIPT` value.
- It uploads artifacts from `reports/analysis/**`, which is not an allowed script output target in the Independence-Release target architecture.
- It commits and pushes generated analysis artifacts back into the repository via `git add`, `git commit`, and `git push`.
- It requires `contents: write` even though analysis-runner outputs must not be committed back into the repo.
- It only checks whether the configured script file exists; it does not validate path traversal, absolute paths, non-`scripts/` paths, empty script path values, or non-Python files.

This ticket must migrate the existing workflow, not merely add guardrails for future workflows.

---

## Scope

### In scope

Implement all of the following in one PR:

1. Migrate `.github/workflows/run-analysis-script.yml`.
2. Remove hardcoded `env.ANALYSIS_SCRIPT` from the workflow.
3. Add a required `workflow_dispatch.inputs.script_path` input.
4. Add a reusable and testable Python guard module at `scripts/_runner_guard.py`.
5. Use the guard in the workflow before executing the requested script.
6. Use the guard's normalized output path for execution, not the raw workflow input.
7. Restrict the runner to Python scripts under `scripts/` only.
8. Reject empty script paths, absolute paths, path traversal, non-`scripts/` paths, missing files, directories, and non-`.py` files.
9. Remove all `git add`, `git commit`, and `git push` behavior from the analysis runner.
10. Reduce the workflow permissions from `contents: write` to `contents: read`, unless another strictly necessary read-only-compatible permission pattern already exists in the repo.
11. Remove all references to `reports/analysis/**` from the analysis runner workflow.
12. Upload analysis outputs only via `actions/upload-artifact`.
13. Configure the upload step to collect files from all allowed analysis-script output targets:
    - `evaluation/exports/**`
    - `evaluation/calibration/**`
    - `artifacts/**`
    - `reports/aux/**`
14. Set `if-no-files-found: warn` for the analysis artifact upload, because valid analysis scripts may only print to stdout and may not produce files.
15. Add focused tests for the guard module.
16. Add or update lightweight documentation for running analysis scripts via the workflow.

### Out of scope

Do not implement or modify any of the following in this ticket:

- Code Map workflow behavior.
- GPT Snapshot workflow behavior.
- Daily Discovery runner logic.
- Intraday Promotion runner logic.
- Evaluation event model, Forward Returns, MFE, MAE, or aggregation semantics.
- Report schema.
- Snapshot schema.
- `recent_runs.json` structure.
- Retention or archive automation.
- OHLCV history compaction.
- Business logic, ranking logic, decision buckets, execution grading, phase interpretation, state machine, invalidation, or setup-cycle logic.
- Any new permanent output target beyond the allowed script-output targets listed below.

Code Map and GPT Snapshot workflows are explicitly out of scope for this ticket. They may only be changed if the tests or repository reality show that they directly violate the same artifact/commit boundary addressed here; otherwise leave them untouched.

---

## Deliberate clarification: allowed script output targets

For analysis scripts run via the analysis runner, the allowed output targets are exactly:

```text
evaluation/exports/
evaluation/calibration/
artifacts/
reports/aux/
```

`evaluation/calibration/` is intentionally added as an allowed script-output target for calibration-related analysis scripts. This is a deliberate clarification of script-output conventions, not an implicit change to report, snapshot, or evaluation schema semantics.

The following paths are explicitly not allowed as analysis-runner output targets:

```text
reports/analysis/
reports/runs/
reports/daily/
reports/index/
snapshots/runs/
snapshots/history/
```

This ticket does not require implementing runtime enforcement of script output writes. It does require documenting these allowed targets and ensuring that the workflow's artifact upload only collects from the allowed targets.

---

## Required workflow behavior

Update `.github/workflows/run-analysis-script.yml` to follow this behavior.

### Trigger

Use a required manual-dispatch input:

```yaml
on:
  workflow_dispatch:
    inputs:
      script_path:
        description: "Relative path to a Python script under scripts/"
        required: true
        type: string
```

There must be no hardcoded `env.ANALYSIS_SCRIPT` default.

### Permissions

Use read-only contents permissions:

```yaml
permissions:
  contents: read
```

The analysis runner must not need repository write permissions.

### Guarded script execution

The workflow must validate `inputs.script_path` before execution by invoking `scripts/_runner_guard.py`.

The recommended pattern is:

```yaml
- name: Validate analysis script path
  id: guard
  run: |
    python scripts/_runner_guard.py "${{ inputs.script_path }}" >> "$GITHUB_OUTPUT"

- name: Run analysis script
  run: |
    python "${{ steps.guard.outputs.script_path }}"
```

The exact implementation may differ, but these invariants are mandatory:

- The raw workflow input must not be executed directly.
- The script must only run after successful guard validation.
- The execution step must use the normalized path emitted by the guard.
- Guard failure must fail the workflow with exit code `1` and a clear error message.
- There must be no silent skip for invalid script paths.

### Artifact upload

Replace the previous upload path with all allowed script-output locations:

```yaml
- name: Upload analysis artifacts
  uses: actions/upload-artifact@v4
  with:
    name: analysis-output
    path: |
      evaluation/exports/**
      evaluation/calibration/**
      artifacts/**
      reports/aux/**
    if-no-files-found: warn
```

Do not upload from `reports/analysis/**`.

### Remove repository writeback

Delete the entire commit/push behavior from the analysis runner. The final workflow must contain no effective equivalent of:

```bash
git add ...
git commit ...
git push
```

Analysis outputs must remain GitHub Actions artifacts, not automatic permanent repository artifacts.

---

## Required guard module

Add:

```text
scripts/_runner_guard.py
```

### Purpose

Validate and normalize the analysis script path before the GitHub Actions workflow executes it.

### CLI contract

The module must be executable as a CLI:

```bash
python scripts/_runner_guard.py <script_path>
```

On success:

- exit with code `0`
- emit exactly one GitHub Actions output assignment line to stdout:

```text
script_path=<normalized-relative-path>
```

No other content may be written to stdout on success. No preamble, success banner, debug line, blank line, or second output line is allowed. Informational or diagnostic messages must go to stderr, not stdout, because the workflow appends guard stdout directly to `$GITHUB_OUTPUT`.

On failure:

- exit with code `1`
- print a clear, actionable error message to stderr
- do not emit a valid `script_path=` output

### Validation requirements

The guard must reject all of the following:

- missing argument
- empty string
- whitespace-only string
- absolute paths, for example `/tmp/foo.py`
- path traversal, including but not limited to:
  - `../scripts/foo.py`
  - `scripts/../foo.py`
  - `scripts/subdir/../../foo.py`
- paths outside `scripts/`, for example:
  - `docs/foo.py`
  - `reports/analysis/foo.py`
  - `evaluation/exports/foo.py`
- non-`.py` files, for example:
  - `scripts/foo.sh`
  - `scripts/foo.md`
  - `scripts/foo`
- missing files
- directories

The guard must accept valid existing Python files under `scripts/`, including nested script files such as:

```text
scripts/foo.py
scripts/analysis/foo.py
```

if those files exist.

### Normalization rule

Normalize the candidate path before checking whether it is under `scripts/`.

Implementation guidance:

- Use `pathlib.Path` or equivalent robust path handling.
- Do not rely on a raw string `startswith("scripts/")` check before normalization.
- Resolve the repository root relative to the current working directory used by the workflow.
- Keep the emitted path repository-relative, using POSIX-style separators.

A valid path such as `scripts/analysis/foo.py` should emit:

```text
script_path=scripts/analysis/foo.py
```

### Determinism

For identical current working directory, identical repository contents, and identical input path, the guard must produce identical accept/reject behavior and identical normalized output.

---

## Required tests

Add focused unit tests for `scripts/_runner_guard.py`.

Preferred location:

```text
tests/scripts/test_runner_guard.py
```

If the repository already has a different convention for script/helper tests, use that convention, but do not bury these tests in unrelated runner or business-logic test files.

### Mandatory test cases

Tests must cover at least:

1. Accepts an existing `scripts/foo.py` file.
2. Accepts an existing nested `scripts/analysis/foo.py` file.
3. Rejects missing argument / no argument.
4. Rejects empty string.
5. Rejects whitespace-only string.
6. Rejects absolute path such as `/tmp/foo.py`.
7. Rejects `../scripts/foo.py`.
8. Rejects `scripts/../foo.py`.
9. Rejects `scripts/subdir/../../foo.py`.
10. Rejects `docs/foo.py`.
11. Rejects `reports/analysis/foo.py`.
12. Rejects `evaluation/exports/foo.py`.
13. Rejects missing file under `scripts/`.
14. Rejects directory under `scripts/`.
15. Rejects non-`.py` file under `scripts/`, for example `scripts/foo.sh`.
16. Emits exactly one stdout line on success: `script_path=<path>`.
17. Emits no other stdout content on success, including no success banners, debug lines, or blank lines.
18. Emits an error to stderr and exits non-zero on failure.

Use temporary directories or test fixtures so the tests do not depend on a specific ad-hoc analysis file already existing in the repo.

---

## Documentation requirement

Add or update a lightweight documentation section for the analysis runner. Use the existing repo documentation location if one exists; otherwise update the most appropriate README or developer/operations doc.

The documentation must state:

- Analysis scripts are launched manually through `workflow_dispatch`.
- The required input is `script_path`.
- `script_path` must be a relative path to an existing `.py` file under `scripts/`.
- Empty values, absolute paths, path traversal, non-`scripts/` paths, missing files, directories, and non-Python files are rejected.
- Analysis outputs are not committed back to the repository by the workflow.
- File outputs should go only to:
  - `evaluation/exports/`
  - `evaluation/calibration/`
  - `artifacts/`
  - `reports/aux/`
- Some scripts may only print stdout and produce no files; in that case the artifact upload step may warn about no files found but the run can still be valid.
- `reports/analysis/` is deprecated/not allowed for this workflow.

---

## Acceptance criteria

The ticket is complete only if all of the following are true:

### Workflow migration

- `.github/workflows/run-analysis-script.yml` no longer contains a hardcoded `ANALYSIS_SCRIPT` default.
- The workflow has a required `workflow_dispatch.inputs.script_path` input.
- The workflow invokes `scripts/_runner_guard.py` before executing the script.
- The workflow executes only the normalized script path emitted by the guard.
- Invalid script paths fail the workflow before script execution.
- The workflow uses `permissions.contents: read` unless a documented, strictly necessary exception exists.
- The workflow contains no `git add`, `git commit`, or `git push` command.
- The workflow contains no `reports/analysis` reference.
- The artifact upload step covers exactly the allowed analysis output locations:
  - `evaluation/exports/**`
  - `evaluation/calibration/**`
  - `artifacts/**`
  - `reports/aux/**`
- The artifact upload step uses `if-no-files-found: warn`.

### Guard behavior

- `scripts/_runner_guard.py` exists.
- It accepts only existing `.py` files under `scripts/`.
- It rejects empty input.
- It rejects absolute paths.
- It rejects path traversal after normalization.
- It rejects paths outside `scripts/`.
- It rejects non-`.py` files.
- It rejects missing files.
- It rejects directories.
- It emits exactly one stdout line on success: `script_path=<normalized-relative-path>`.
- It emits no success banners, debug lines, blank lines, or other stdout content.
- It writes informational or diagnostic messages to stderr only.
- It exits with code `1` and a clear stderr message on failure.

### Tests

- Guard tests cover all mandatory cases above.
- Existing test suite still passes.
- No scanner business-logic tests require changes due to this ticket unless they directly inspect the workflow file or script-runner documentation.

### Documentation

- Analysis-runner usage is documented.
- Allowed output targets are documented.
- Deprecated/disallowed `reports/analysis/` usage is documented.
- Documentation does not imply that analysis-runner outputs are permanent canonical repo artifacts.

---

## Non-goals and anti-requirements

Codex must not:

- Add a default script to run when `script_path` is missing.
- Execute the raw workflow input directly.
- Keep or reintroduce `reports/analysis/**`.
- Keep or reintroduce `git add`, `git commit`, or `git push` for generated analysis artifacts.
- Grant `contents: write` to the analysis runner without a documented necessity.
- Add output uploads from `reports/runs/`, `reports/daily/`, `reports/index/`, `snapshots/runs/`, or `snapshots/history/`.
- Modify Code Map or GPT Snapshot workflows unless directly necessary to resolve the same output/commit-boundary issue.
- Change report, snapshot, evaluation, Daily runner, Intraday runner, or business-logic semantics.
- Introduce another script-runner convention in parallel to this one.

---

## Suggested implementation sequence

1. Add `scripts/_runner_guard.py` with a small pure-Python implementation.
2. Add guard tests using temporary files/directories.
3. Update `.github/workflows/run-analysis-script.yml`:
   - replace hardcoded `ANALYSIS_SCRIPT` with required `workflow_dispatch.inputs.script_path`
   - reduce permissions to read-only
   - add guard step
   - run normalized guard output
   - replace artifact upload paths
   - remove commit/push step
4. Update lightweight documentation.
5. Run tests locally.
6. Inspect the workflow file to verify no stale `reports/analysis`, `git add`, `git commit`, or `git push` remains.

---

## Review checklist for Codex before final response

Before reporting completion, verify:

- [ ] No `reports/analysis` reference remains in `.github/workflows/run-analysis-script.yml`.
- [ ] No `git add`, `git commit`, or `git push` remains in `.github/workflows/run-analysis-script.yml`.
- [ ] `contents: read` is used in `.github/workflows/run-analysis-script.yml`.
- [ ] The workflow input is named `script_path` and is required.
- [ ] The script path is validated by `scripts/_runner_guard.py` before execution.
- [ ] Guard stdout is exactly one `script_path=<normalized-relative-path>` line on success, because stdout is appended to `$GITHUB_OUTPUT`.
- [ ] The raw input is not executed directly.
- [ ] Artifact upload uses the four allowed paths and `if-no-files-found: warn`.
- [ ] Guard tests cover valid, invalid, traversal, absolute, missing, directory, outside-root, and non-Python cases.
- [ ] Documentation states that generated analysis outputs are uploaded as workflow artifacts only and are not committed back into the repo.
