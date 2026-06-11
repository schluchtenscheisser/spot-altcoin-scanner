# CODE-FU-D: Canonical Run Modes and Compatibility Alias Policy

## Metadata

- Ticket ID: CODE-FU-D
- Title: Canonical Run Modes and Compatibility Alias Policy
- Status: Draft — Codex-ready after Martin approval
- Priority: P1 / P2
- Type: Runtime mode boundary cleanup / compatibility policy
- Language: Implementation and code artifacts in English
- Primary modules affected:
  - `scanner/main.py`
  - `scanner/config.py`
  - `scanner/runners/daily.py`
  - `scanner/runners/intraday.py`
  - `scanner/storage/*`
  - `scanner/output/*`
- Related audits:
  - CODE-A1 — `docs/audit/active_code_path_inventory_v0.md`
  - CODE-A2 — `docs/audit/legacy_pipeline_boundary_review_v0.md`
- Related decision note:
  - `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md`
- Decision from Martin:
  - old mode names `standard`, `fast`, `offline`, and `backtest` are `keep_as_compatibility_only`
- Blocks / unblocks:
  - Reduces DOC-D ambiguity around runtime modes
  - Does not address legacy snapshot exporter or full-mode backfill

---

## Context

CODE-A2 identified that old mode names are still accepted by the active scanner dispatch:

```text
standard
fast
offline
backtest
```

The Decision Note records Martin’s decision:

```text
D — old mode names standard, fast, offline, backtest
Decision: keep_as_compatibility_only
```

These names should remain accepted as compatibility aliases for now, but they must not be documented or treated as distinct current runtime architectures.

This ticket must make the mode model explicit and deterministic for implementation, storage, reports, diagnostics, tests, and DOC-D.

---

## Critical terminology distinction

This ticket must keep three contexts strictly separate.

### Context 1 — CLI / config input mode

This is the user/config/CLI-facing mode accepted by scanner entry points, especially:

```text
scanner/main.py
ScannerConfig.run_mode
```

Compatibility aliases live here.

Relevant values:

```text
daily_discovery
intraday_promotion
standard
fast
offline
backtest
```

### Context 2 — SQLite `run_metadata.scan_mode`

This is the storage/run-metadata context.

Canonical values are T1-canonical:

```text
daily_discovery
intraday_promotion
```

Old compatibility aliases must not be stored here as canonical run metadata values after normalization.

### Context 3 — Report / diagnostics `scan_mode`

This is the report/diagnostics payload context.

Canonical values are T13-canonical:

```text
daily
intraday
```

Old compatibility aliases must not be emitted in report/diagnostics `scan_mode`.

### Non-negotiable rule

Do not mix these contexts.

The same word `scan_mode` may appear in multiple layers, but the valid value domain depends on the layer.

---

## Goal

Implement or formalize a deterministic mode-normalization policy:

| Input mode | CLI/config meaning | Runner target | SQLite `run_metadata.scan_mode` | Report/diagnostics `scan_mode` |
|---|---|---|---|---|
| `daily_discovery` | canonical Daily input mode | Daily runner | `daily_discovery` | `daily` |
| `intraday_promotion` | canonical Intraday input mode | Intraday runner | `intraday_promotion` | `intraday` |
| `standard` | compatibility alias | Daily runner | `daily_discovery` | `daily` |
| `fast` | compatibility alias | Daily runner | `daily_discovery` | `daily` |
| `offline` | compatibility alias | Daily runner | `daily_discovery` | `daily` |
| `backtest` | compatibility alias | Daily runner | `daily_discovery` | `daily` |

The old names must live only at the input/compatibility layer unless existing repository evidence proves that a legacy migration reader must still accept old stored values.

Important guard for `backtest`: if inspection reveals that `backtest` mode has distinct routing behavior that is not identical to Daily runner behavior, stop and report the finding before implementing. Do not assume the mapping in that case.

---

## Scope

### In scope

- Inspect current handling of runtime modes in:
  - `scanner/main.py`
  - `scanner/config.py`
  - `scanner/runners/daily.py`
  - `scanner/runners/intraday.py`
  - `scanner/storage/*`
  - `scanner/output/*`
  - relevant tests and workflows
- Define canonical constants or helper functions if useful.
- Ensure old names are accepted only as compatibility aliases on the input side.
- Ensure alias normalization is explicit and tested.
- Ensure SQLite run metadata uses T1-canonical values:
  - `daily_discovery`
  - `intraday_promotion`
- Ensure report/diagnostics payloads use T13-canonical values:
  - `daily`
  - `intraday`
- Update tests to enforce this two-context distinction.
- Preserve current runtime behavior.
- Keep old aliases accepted unless explicitly impossible due to current validation structure.

### Out of scope

Do not:

- remove old aliases,
- change Daily runner behavior,
- change Intraday runner behavior,
- change scheduling,
- change artifact paths,
- change report/diagnostics schemas except to preserve/correct canonical mode values,
- change scoring, ranking, entry, state, phase, or execution behavior,
- change legacy snapshot exporter behavior,
- change `backfill_snapshots.py`,
- update DOC-D or canonical current-state docs,
- perform broad mode-system redesign beyond this compatibility policy.

---

## Required implementation details

### 1. Centralize or make explicit mode normalization

Normalization must happen once, at the earliest possible point in the call path, before the mode value is passed to runners, storage, or output. Prefer `scanner/main.py` or `scanner/config.py` if that matches current architecture.

Codex should inspect whether mode normalization already exists.

If it exists, update it to match this ticket.

If it does not exist, add a small explicit helper in the most appropriate existing module, for example:

```text
scanner/main.py
scanner/config.py
scanner/storage/schema.py
```

or a small dedicated utility if that better fits current architecture.

The helper must not blur the two canonical output contexts.

Suggested conceptual helpers:

```python
resolve_cli_mode_to_runner(mode: str) -> str
resolve_cli_mode_to_run_metadata_scan_mode(mode: str) -> str
resolve_runner_mode_to_report_scan_mode(mode: str) -> str
```

Exact names are up to Codex, but behavior must be deterministic and tested.

### 2. CLI/config input aliases

The following values must remain accepted at the input layer:

```text
standard
fast
offline
backtest
```

They must map to Daily runner behavior.

They must not create separate current runtime architectures.

### 3. SQLite `run_metadata.scan_mode`

SQLite run metadata must use:

```text
daily_discovery
intraday_promotion
```

Compatibility aliases must normalize to:

```text
daily_discovery
```

for old Daily aliases.

If current repository code still stores or accepts old values for historical migration/compatibility, Codex must:

- identify the exact reader/writer path,
- preserve read compatibility if needed,
- ensure new writes use canonical values,
- add or update tests to make this distinction explicit.

### 4. Report/diagnostics `scan_mode`

Reports and diagnostics must use:

```text
daily
intraday
```

Compatibility aliases must not appear in newly emitted report/diagnostics `scan_mode`.

If tests currently expect old names in report payloads, update those tests to the T13-canonical values unless they are explicitly historical fixture tests.

### 5. Explicit mapping table in tests

Add or update tests that assert the required mapping table:

```text
daily_discovery -> Daily runner -> run_metadata daily_discovery -> report/diagnostics daily
intraday_promotion -> Intraday runner -> run_metadata intraday_promotion -> report/diagnostics intraday
standard -> Daily runner -> run_metadata daily_discovery -> report/diagnostics daily
fast -> Daily runner -> run_metadata daily_discovery -> report/diagnostics daily
offline -> Daily runner -> run_metadata daily_discovery -> report/diagnostics daily
backtest -> Daily runner -> run_metadata daily_discovery -> report/diagnostics daily
```

Tests should fail if an old alias leaks into new SQLite run metadata or new report/diagnostics payloads.

### 6. Workflows

Inspect workflows for old alias usage, especially `standard`.

If workflows pass old aliases intentionally, they may remain unchanged for compatibility, but tests/code must prove those aliases normalize to the canonical contexts above.

Do not change workflow schedule or operational behavior in this ticket unless strictly required for tests.

---

## Documentation impact

No canonical documentation update required.

Reason: this ticket implements the already-recorded Decision Note policy for compatibility aliases and canonical mode contexts. It clarifies runtime behavior in code/tests without updating DOC-D or canonical current-state documentation.

Do not update:

```text
docs/canonical/*
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
docs/code_map.md
docs/audit/*
docs/decision_notes/*
```

Allowed documentation updates:

- inline comments or docstrings explaining normalization helpers,
- test comments clarifying the two `scan_mode` contexts.

Generated docs may be updated later by normal workflows, not manually in this ticket.

---

## Test requirements

At minimum, run or update targeted tests around:

```text
scanner/main.py dispatch
scanner/config.py run_mode validation/defaults
SQLite run metadata writes/reads
report/diagnostics scan_mode payloads
Shadow-Live workflow assumptions if covered by tests
```

Suggested commands:

```bash
pytest -q tests/test_main_dispatch_ticket17_fixes.py
pytest -q tests/test_sqlite_foundation.py
pytest -q tests/test_ticket13_output_artifacts.py
pytest -q tests/test_output_schema_version.py
pytest -q tests/test_independence_shadow_live.py
pytest -q tests/test_independence_smoke_test.py
```

If any file does not exist or is no longer relevant, run the closest matching tests and report the substitution.

Also run grep checks:

```bash
grep -R "scan_mode" -n scanner tests scripts .github docs | head -200
grep -R "standard\|fast\|offline\|backtest\|daily_discovery\|intraday_promotion" -n scanner tests scripts .github docs | head -300
```

Do not rely only on grep; inspect the relevant code paths manually.

---

## Acceptance criteria

CODE-FU-D is complete when:

1. The repo has an explicit deterministic policy for CLI/config input modes.
2. `daily_discovery` routes to the Daily runner.
3. `intraday_promotion` routes to the Intraday runner.
4. `standard`, `fast`, `offline`, and `backtest` remain accepted as compatibility aliases.
5. All four old aliases route to the Daily runner.
6. If `backtest` is found to have distinct non-Daily routing behavior, Codex stops and reports before implementing instead of forcing the mapping.
7. New SQLite `run_metadata.scan_mode` writes use only:
   - `daily_discovery`
   - `intraday_promotion`
8. New report/diagnostics `scan_mode` writes use only:
   - `daily`
   - `intraday`
9. Tests explicitly assert the full mapping table for all six input modes, unless the `backtest` stop/report guard is triggered.
10. Old aliases do not leak into newly emitted SQLite run metadata or report/diagnostics payloads.
11. Historical read compatibility is preserved where current code/tests require it.
12. No scanner runtime behavior changes except explicit canonicalization/normalization of mode labels.
13. No canonical docs are updated.
14. No unrelated legacy pipeline code is changed.

---

## Validation

Run:

```bash
git diff --stat
git diff --name-only
```

Run targeted tests:

```bash
pytest -q tests/test_main_dispatch_ticket17_fixes.py
pytest -q tests/test_sqlite_foundation.py
pytest -q tests/test_ticket13_output_artifacts.py
pytest -q tests/test_output_schema_version.py
pytest -q tests/test_independence_shadow_live.py
pytest -q tests/test_independence_smoke_test.py
```

Run grep checks:

```bash
grep -R "scan_mode" -n scanner tests scripts .github docs | head -200
grep -R "standard\|fast\|offline\|backtest\|daily_discovery\|intraday_promotion" -n scanner tests scripts .github docs | head -300
```

If feasible, also run:

```bash
pytest -q
```

If the full suite is too slow or unrelated failures occur, report exactly which targeted tests passed and which broader tests were not run or failed for unrelated reasons.

---

## Codex guardrails

- Do not remove compatibility aliases.
- Do not rename public CLI flags unless necessary and approved.
- Normalize once at the earliest possible call-path point before passing mode values to runners, storage, or output.
- If `backtest` has distinct non-Daily routing behavior, stop and report before implementing.
- Do not change Daily/Intraday runner behavior.
- Do not conflate SQLite `run_metadata.scan_mode` with report/diagnostics `scan_mode`.
- Do not store old aliases as new canonical SQLite run metadata values.
- Do not emit old aliases in new report/diagnostics payloads.
- Do not document old aliases as current distinct architectures.
- Do not update canonical docs.
- Do not change legacy snapshot exporter or backfill behavior.
- Keep the diff focused on mode normalization and tests.

---

## Definition of Done

- Mode normalization is explicit and tested.
- The two `scan_mode` contexts are separated and guarded by tests.
- Old aliases remain accepted only at the compatibility input layer.
- New storage/report outputs use canonical values for their respective contexts.
- DOC-D can rely on a deterministic runtime mode policy.
