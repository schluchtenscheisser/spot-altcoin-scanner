# Title
[P0] Define Independence-Release output schema, reports architecture, and diagnostics format

## Context / Source
This ticket defines the canonical output artifact layer for the Independence-Release architecture.

The authoritative basis for this ticket is exclusively:

- the 7 v2.1 section documents,
- `independence_release_gesamtkonzept_final.md`.

The addendum is supplementary working context, not a competing primary authority. Existing repo docs and code remain relevant only insofar as they do not conflict with the current authoritative reference set.

This ticket corresponds to the Gesamtkonzept workstream block for output artifacts / reports / diagnostics. It is the architecture ticket that fixes:

- canonical report artifacts,
- canonical diagnostics artifact format,
- report/index path conventions,
- schema versioning,
- manifest referencing rules,
- deterministic writer responsibilities.

`depends_on:`
- Ticket 1: bar_clock / sqlite / config foundation
- Ticket 2: repo bootstrap / canonical structure foundation

## Goal
After this ticket is completed, the repository must provide:

1. a canonical typed schema for Independence-Release report and diagnostics artifacts,
2. deterministic writers for run reports, daily reports, diagnostics, and index files,
3. fixed path conventions under `reports/`,
4. explicit manifest-reference semantics without manifest duplication,
5. fixture-based tests that validate schema, serialization, nullability, ordering, and index update invariants,
6. canonical docs that describe the artifact model clearly for later runner tickets.

## Scope
Allowed changes for this ticket:

- `scanner/output/schema.py`
- `scanner/output/diagnostics.py`
- `scanner/output/report_builder.py`
- `scanner/output/__init__.py` if needed
- `tests/**` for schema / diagnostics / report-builder / index tests
- `docs/canonical/**` where output artifacts, report semantics, and diagnostics semantics are described
- config defaults/extensions inside the central config abstraction, if needed for `independence_release.reports`
- `docs/tickets/**` only as required by workflow docs

## Out of Scope
- Implementing daily or intraday runners
- Implementing execution logic
- Implementing phase/state/pattern/bucket business logic itself
- Implementing Parquet snapshot storage
- Implementing retention or archive jobs
- Implementing evaluation/replay exports
- Implementing full content-rich `report.md` / `report.xlsx`
- Introducing persisted candidate continuity / transition-history logic beyond point-in-time output
- Duplicating `run.manifest.json` under `reports/`
- Introducing a second output authority outside the canonical report/diagnostics/manifest separation

## Canonical References (important)
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/tickets/_TEMPLATE.md`
- Gesamtkonzept sections for:
  - `output/` module roles
  - `reports/` structure
  - `reports/index/` required files
  - manifest non-duplication
  - `symbol_diagnostics.jsonl.gz` as canonical full diagnostics format
- Addendum guidance that persisted candidate context is a later precision block and must not be silently pulled into earlier tickets

## Mandatory Authority Rule
> If the current authoritative reference set, existing repo authority/canonical documents, and existing code conflict, the current authoritative reference set wins. Repo documents and existing code remain valid only insofar as they do not contradict that reference set.

## Proposed change (high-level)

### Before
- The repo may have no canonical Independence-Release output layer yet.
- There is no fixed schema for `report.json`, diagnostics records, or index files.
- Later runner tickets would otherwise have to guess path conventions, artifact ownership, and summary-vs-diagnostics separation.
- There is a high risk of duplicate truth between report output and manifest output.

### After
- `scanner/output/schema.py` contains the canonical typed artifact models and schema version constant.
- `scanner/output/diagnostics.py` serializes canonical `symbol_diagnostics.jsonl.gz`.
- `scanner/output/report_builder.py` builds run reports, daily reports, and index files with deterministic path and atomic write behavior.
- The `reports/` tree follows one explicit target layout.
- `report.json` is canonical compact summary output.
- `symbol_diagnostics.jsonl.gz` is canonical full diagnostics output.
- `run.manifest.json` remains canonical only under `snapshots/runs/...`.
- Index files are derived artifacts written only after run artifacts are complete.

### Edge cases
- `intraday_bar_id` must be present in summary and diagnostics records even for daily scans; in that case it is `null`, not absent.
- `latest_manifest.json`, if written at all, must be a pure pointer/reference file, never a copied manifest body.
- `latest_confirmed_candidates.json` must exclude `late_monitor` cases, including `CONFIRMED_PATTERN_UNRESOLVED`.
- Missing bucket populations must not produce missing keys or ad hoc schema drift.
- Fixture-based tests must work before later full pipeline layers exist.

### Backward compatibility impact
This ticket defines the canonical Independence-Release output layer. It may coexist with legacy repo artifacts temporarily, but it must not derive its semantics from legacy output contracts where those conflict with the current authoritative Independence-Release target architecture.

## Codex Implementation Guardrails (No-Guesswork, mandatory)

- **Workflow priority:** Follow `docs/canonical/WORKFLOW_CODEX.md` strictly.
- **Canonical docs first or alongside code:** This ticket defines artifact contracts. Update canonical docs in the same PR.
- **No second truth:** Do not introduce competing output schemas, duplicate manifest copies, or independent path conventions in multiple modules.
- **Determinism:** At identical input and identical config, selection, ordering, status, and file content are identical.
- **Point-in-time only:** Do not infer continuity, promotion history, or drop-off history beyond the fields explicitly defined in this ticket.
- **No premature execution semantics:** Do not add `execution_pending` or equivalent execution-stage placeholders unless explicitly required by this ticket. This ticket does not require them.
- **No guessed business logic:** This ticket serializes and structures outputs. It does not invent phase/state/pattern/bucket rules.
- **No raw-dict schema drift:** Typed schema definitions must live centrally in `scanner/output/schema.py`.
- **No manual edits to generated docs:** `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` remain read-only.

## Required module responsibilities (binding, not suggestion)

### `scanner/output/schema.py`
Responsible for:
- typed schema definitions,
- artifact dataclasses / TypedDicts / equivalent typed models,
- central enums,
- central `SCHEMA_VERSION = "ir1.0"`,
- canonical report/index record shapes.

### `scanner/output/diagnostics.py`
Responsible for:
- validating symbol diagnostics records,
- serializing `symbol_diagnostics.jsonl.gz`,
- JSONL line generation,
- gzip write logic.

### `scanner/output/report_builder.py`
Responsible for:
- report path conventions,
- building/writing run report artifacts,
- building/writing daily report artifacts,
- building/writing index artifacts,
- manifest-path references,
- atomic file finalization,
- exposing the writer that later runner tickets call (for example `write_run_report(...)` and `write_daily_report(...)`).

Codex must not distribute these responsibilities arbitrarily across other modules.

## Required artifact tree (binding, not suggestion)

### Canonical run artifacts
- `reports/runs/YYYY/MM/DD/<run_id>/report.json`
- `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`

### Canonical daily artifact
- `reports/daily/YYYY/MM/DD/report.json`

The `YYYY/MM/DD` directory components under both `reports/runs/` and `reports/daily/` are derived from `daily_bar_id` as the date basis, not from the calendar date portion of `as_of_utc`.

### Date basis for `YYYY/MM/DD` path segments
For both `reports/runs/YYYY/MM/DD/` and `reports/daily/YYYY/MM/DD/`, the path date basis is the artifact's `daily_bar_id` value.

That means:
- `YYYY/MM/DD` is derived from `daily_bar_id`,
- not from wall-clock write time,
- not from the date component of `as_of_utc` when that could differ from `daily_bar_id`.

### Derived / convenience outputs
- `reports/runs/YYYY/MM/DD/<run_id>/report.md`
- `reports/runs/YYYY/MM/DD/<run_id>/report.xlsx`

These are derived convenience outputs only. T13 may create stubs/interfaces for them, but does not need to implement final rich content.

### Index artifacts
Required:
- `reports/index/latest_run.txt`
- `reports/index/latest_paths.json`
- `reports/index/latest.json`
- `reports/index/latest_daily.json`
- `reports/index/latest_confirmed_candidates.json`
- `reports/index/latest_watchlist.json`
- `reports/index/recent_runs.json`

Optional:
- `reports/index/latest_manifest.json` as a pure pointer/reference file only

### Additional defined directories
The target structure must also recognize:
- `reports/aux/`
- `reports/archive/` (optional target path, no archive job required in this ticket)

## Schema versioning (binding)
Central schema version:
- `schema_version = "ir1.0"`

At minimum, the following artifacts must carry `schema_version`:
- `report.json`
- `run.manifest.json` reference target remains canonical elsewhere, but its schema version is part of the canonical manifest contract
- diagnostics records may also carry `schema_version`; this ticket requires that they do

## `scan_mode` enum (binding)
Allowed values:
- `daily`
- `intraday`

No additional values in this ticket.

`scan_mode` must be explicitly typed and validated. It must not be inferred from path shape or bool flags.

## Core scalar field contracts and bar-ID/nullability rules (binding)

### `run_id`
- type: `str`
- semantics: non-empty opaque string
- T13 does **not** validate any internal `run_id` format
- the concrete `run_id` format contract belongs to the later runner ticket

### `as_of_utc`
- type: `str`
- format: ISO 8601 UTC string in the form `YYYY-MM-DDTHH:MM:SSZ`
- never absent in report, diagnostics, or index entry records defined by this ticket

### `daily_bar_id`
- type: `str`
- format: `YYYY-MM-DD`
- source of truth: canonical bar-clock output
- never absent in report or diagnostics records

### `intraday_bar_id`
- type: `int | null`
- semantics when non-null: UTC close timestamp of the most recently closed 4h bar in milliseconds since epoch
- must be **present** in report and diagnostics records
- for `scan_mode = intraday`: integer value
- for `scan_mode = daily`: `null`

> `intraday_bar_id` is nullable. `null` means “no intraday bar context for this artifact because the scan mode is daily” and must not be represented by field absence, `0`, empty string, or any other sentinel.

## Canonical data-resolution field decision
This ticket does **not** introduce `data_resolution_class`.

For output and diagnostics records in T13, the canonical data-resolution distinction is represented only by:
- `data_4h_available: bool`

No alternative alias such as `data_resolution_class` may be introduced in this ticket.

## Required `report.json` contract (binding)

`report.json` is the canonical compact summary artifact. It is **not** the full diagnostics artifact.

It must contain at minimum:

- `schema_version`
- `run_id`
- `scan_mode`
- `as_of_utc`
- `daily_bar_id`
- `intraday_bar_id`
- `counts_by_bucket`
- `symbol_lists`
- `manifest_path`
- `diagnostics_path`

### `counts_by_bucket`
`counts_by_bucket` must contain all canonical decision buckets, even if zero:

- `watchlist`
- `early_candidates`
- `confirmed_candidates`
- `late_monitor`
- `discarded`

Missing bucket keys are not allowed.

### `symbol_lists`
`symbol_lists` is the compact-symbol-list section of `report.json`.

To prevent Codex from guessing which buckets appear here, the compact lists in `report.json` are explicitly limited to exactly these buckets:

- `confirmed_candidates`
- `early_candidates`
- `watchlist`
- `late_monitor`

`discarded` is counted in `counts_by_bucket` but does **not** appear in `symbol_lists`.

Each of the four `symbol_lists` keys must always be present and contain a list, possibly empty.

### `manifest_path`
- string path/reference to canonical manifest under `snapshots/runs/...`
- not the manifest body
- serialized as a reference only; this ticket does not require the referenced manifest path to already exist physically at write time

> T13 writes `manifest_path` as a string reference and does not validate physical path existence at artifact write time. Manifest creation and existence checks are outside the output-layer scope of this ticket.
- T13 writes `manifest_path` as a string reference only
- T13 does **not** require that the referenced manifest path already exists physically at write time
- existence/availability checks for the target manifest path do not belong to the output layer in this ticket

### `diagnostics_path`
- string path/reference to `symbol_diagnostics.jsonl.gz`

## Required diagnostics record contract (binding)

Each line in `symbol_diagnostics.jsonl.gz` represents exactly one symbol record.

Each diagnostics record must contain at minimum:

- `schema_version`
- `run_id`
- `scan_mode`
- `symbol`
- `as_of_utc`
- `daily_bar_id`
- `intraday_bar_id`
- `data_4h_available`
- `axes`
- `phase`
- `invalidation`
- `cycle`
- `state`
- `pattern`
- `decision`
- `reasons`

### Block semantics
The following keys are required as block containers even in stub fixtures:
- `axes`
- `phase`
- `invalidation`
- `cycle`
- `state`
- `pattern`
- `decision`
- `reasons`

These keys must be present as mappings/dicts, not omitted.

### Minimal stub fixture record (binding for tests)
Use this exact minimal stub shape for fixture/golden tests, with value changes only where a test explicitly needs them:

```json
{
  "schema_version": "ir1.0",
  "run_id": "stub-run-id",
  "scan_mode": "daily",
  "symbol": "STUBUSDT",
  "as_of_utc": "2026-01-01T00:00:00Z",
  "daily_bar_id": "2025-12-31",
  "intraday_bar_id": null,
  "data_4h_available": false,
  "axes": {},
  "phase": {},
  "invalidation": {},
  "cycle": {},
  "state": {},
  "pattern": {},
  "decision": {},
  "reasons": {}
}
```

This stub exists to remove schema ambiguity before later full pipeline tickets exist. Codex must not invent an alternative base fixture shape.

## Required index file semantics (binding)

### `latest_run.txt`
Contains exactly the latest `run_id` as plain text.

### `latest_paths.json`
Contains path references for the latest run artifact set, at minimum:
- `run_id`
- `scan_mode`
- `as_of_utc`
- `daily_bar_id`
- `intraday_bar_id`
- `report_path`
- `diagnostics_path`
- `manifest_path`

Path fields in `latest_paths.json` are stored as **repository-root-relative paths**, not absolute filesystem paths.

### `latest.json`
Contains the latest run summary with content identical to the canonical `report.json` of the latest run.

It is a copied/derived latest-pointer artifact, not an independently-defined schema and not a subset.

### `latest_daily.json`
Contains content identical to the canonical `reports/daily/YYYY/MM/DD/report.json` of the latest daily report.

It is a copied/derived latest-pointer artifact, not an independently-defined schema and not a subset.

### `latest_confirmed_candidates.json`
Contains only symbols that are actually in `confirmed_candidates`.

Payload format:
- JSON array of pure symbol strings
- canonical shape: `["SYMBOLUSDT", ...]`
- derived directly from `report.json.symbol_lists.confirmed_candidates`

Hard invariant:
- no `late_monitor` symbol may appear here,
- specifically, no symbol whose operative outcome is `late_monitor` due to `CONFIRMED_PATTERN_UNRESOLVED` may appear here.

### `latest_watchlist.json`
Contains the latest watchlist symbols.

Payload format:
- JSON array of pure symbol strings
- canonical shape: `["SYMBOLUSDT", ...]`
- derived directly from `report.json.symbol_lists.watchlist`

### `recent_runs.json`
Contains a list of recent run entries with exactly this minimum per-entry structure:
- `run_id`
- `scan_mode`
- `as_of_utc`
- `daily_bar_id`
- `intraday_bar_id`
- `manifest_path`
- `report_path`
- `diagnostics_path`

Rules:
- newest-first ordering,
- `intraday_bar_id` always present, `null` for daily runs,
- bounded length with default `recent_runs_limit = 30`,
- no embedded manifest body,
- path/reference fields only,
- all path fields are repository-root-relative.

### `latest_manifest.json`
Optional. If implemented in this ticket, it must be a pure pointer/reference file to the canonical manifest path. It must not contain the manifest content body.

## Daily writer ownership (binding)
This ticket implements the daily report writer function in `scanner/output/report_builder.py`.

A later runner ticket may call that function, but must not implement a second independent daily-report path convention.

> `write_daily_report(...)` is owned by the output layer. Runners call it; they do not redefine its path logic.

## Atomic write rule (binding)
All final report and index artifacts must be written via:

1. write temp file in the target directory,
2. flush/close successfully,
3. atomically rename to the final path.

Direct in-place overwrite is not allowed.

`reports/index/*` must only be updated after the corresponding run artifacts have already been fully written successfully.

## Path date-basis convention (binding)
The `YYYY/MM/DD` directory depth under both `reports/runs/` and `reports/daily/` is derived from `daily_bar_id`.

Rule:
- split the canonical `daily_bar_id` value (`YYYY-MM-DD`) into `YYYY/MM/DD`
- do not derive the directory date from `as_of_utc`
- this rule applies equally to daily and intraday scan outputs

## Config semantics (mandatory)
This ticket may extend the central `independence_release.reports` config block, but must not create a parallel config loading mechanism.

If config is needed, use:

```yaml
independence_release:
  reports:
    recent_runs_limit: 30
    emit_report_md: false
    emit_report_xlsx: false
```

### Required config semantics
> Partial overrides in `independence_release.reports` are merged field-by-field with central defaults; missing sub-keys are not treated as invalid.

> Missing keys fall back to defaults. Invalid values produce a clear `ValueError` containing the key name and invalid value.

### Config validation
- `recent_runs_limit` must be a positive integer
- `emit_report_md` must be bool
- `emit_report_xlsx` must be bool

## Missing vs invalid vs null semantics (mandatory)

### Missing key
- report config key missing → default applies

### Invalid value
- wrong type / invalid range in report config → clear `ValueError`

### Null
- `intraday_bar_id = null` means “no intraday bar context because this artifact belongs to a daily scan”
- `null` is not the same as field absence
- no bool-coercion of nullable fields is allowed

### Not evaluated vs failed
This ticket does not introduce fetch/evaluation status enums. It must not collapse later business semantics into output-layer pseudo-statuses.

## Canonical docs to update
At minimum, update or create the relevant sections in canonical docs so later tickets can rely on:

- output module roles,
- canonical separation of summary vs full diagnostics vs manifest,
- report path conventions under `reports/`,
- index file semantics,
- schema version `ir1.0`,
- `scan_mode` enum values,
- `daily_bar_id` / `intraday_bar_id` type and nullability rules,
- diagnostics record minimum contract,
- manifest non-duplication rule,
- atomic index update rule.

## Acceptance Criteria (deterministic)

1. `scanner/output/schema.py` exists and defines typed schemas/models for:
   - run summary artifact,
   - diagnostics record artifact,
   - index file entries,
   - `scan_mode` enum,
   - `schema_version = "ir1.0"`.

2. `scanner/output/diagnostics.py` exists and can serialize a list/stream of diagnostics records into canonical `symbol_diagnostics.jsonl.gz`.

3. `scanner/output/report_builder.py` exists and can build/write:
   - run `report.json`,
   - daily `report.json`,
   - required index files,
   - using deterministic path conventions.

4. `report.json` contains at minimum:
   - `schema_version`,
   - `run_id`,
   - `scan_mode`,
   - `as_of_utc`,
   - `daily_bar_id`,
   - `intraday_bar_id`,
   - `counts_by_bucket`,
   - `symbol_lists`,
   - `manifest_path`,
   - `diagnostics_path`.

5. `counts_by_bucket` contains exactly these keys:
   - `watchlist`,
   - `early_candidates`,
   - `confirmed_candidates`,
   - `late_monitor`,
   - `discarded`.

6. `symbol_lists` contains exactly these keys:
   - `confirmed_candidates`,
   - `early_candidates`,
   - `watchlist`,
   - `late_monitor`.

7. `symbol_lists` does not include `discarded`.

8. Each entry in a `symbol_lists` list is a plain symbol string (for example `AAAUSDT`), never an object.

9. `daily_bar_id` is serialized as `str` in `YYYY-MM-DD` format and never as integer or timestamp.

10. `intraday_bar_id` is always present in summary and diagnostics records:
    - integer for intraday runs,
    - `null` for daily runs.

11. `run_id` is treated as a non-empty opaque string and T13 does not impose or validate any internal `run_id` format beyond non-empty string validation.

12. `as_of_utc` is serialized as an ISO 8601 UTC string in the format `YYYY-MM-DDTHH:MM:SSZ`.

13. Diagnostics records contain at minimum the required identity fields and the required block keys:
    - `axes`,
    - `phase`,
    - `invalidation`,
    - `cycle`,
    - `state`,
    - `pattern`,
    - `decision`,
    - `reasons`.

14. This ticket does not introduce `data_resolution_class`.
    The only canonical data-resolution field in this ticket is `data_4h_available: bool`.

15. `latest.json` is content-identical to the canonical `report.json` of the latest run.

16. `latest_daily.json` is content-identical to the canonical `report.json` of the latest daily report.

17. `latest_confirmed_candidates.json` is serialized as a JSON array of plain symbol strings and excludes all `late_monitor` symbols, including symbols whose effective outcome is `late_monitor` because of `CONFIRMED_PATTERN_UNRESOLVED`.

18. `latest_watchlist.json` is serialized as a JSON array of plain symbol strings derived from `report.json.symbol_lists.watchlist`.

19. `latest_paths.json` contains at minimum:
    - `run_id`,
    - `scan_mode`,
    - `as_of_utc`,
    - `daily_bar_id`,
    - `intraday_bar_id`,
    - `report_path`,
    - `diagnostics_path`,
    - `manifest_path`,
    and all path fields are repository-root-relative.

20. `recent_runs.json` stores newest-first entries with the required minimum fields and a bounded length controlled by `recent_runs_limit` defaulting to `30`.

21. If `latest_manifest.json` is implemented, it contains only a reference/pointer to the canonical manifest path, not the manifest body.

22. Manifest duplication does not occur anywhere under `reports/runs/...`.

23. `manifest_path` is written as a string reference and T13 does not require the referenced manifest path to already exist physically at artifact write time.

24. Writers use temp-file-then-atomic-rename semantics for final artifact creation.

25. `reports/index/*` is written only after run artifacts are fully written successfully.

26. The `YYYY/MM/DD` path depth under both `reports/runs/` and `reports/daily/` is derived from `daily_bar_id`, not from `as_of_utc`.

27. The daily report writer is implemented in the output layer and can later be called by the runner layer without duplicating path logic.

28. Config handling for `independence_release.reports` uses merge-with-defaults semantics and raises clear errors for invalid values.

29. Canonical docs are updated to describe the final artifact model and constraints defined in this ticket.

30. This ticket does not implement:
    - runners,
    - execution logic,
    - continuity/history semantics,
    - archive jobs,
    - evaluation exports,
    - rich final `report.md`/`report.xlsx` content.

31. The ticket is archived in the same PR according to workflow docs.

## Default-/Edgecase coverage (mandatory)

- **Config Defaults (Missing key → Default):** ✅  
  Missing `independence_release.reports` keys fall back to defaults.

- **Config Invalid Value Handling:** ✅  
  Wrong type / invalid range in `independence_release.reports` produces clear `ValueError`.

- **Nullability / no bool coercion:** ✅  
  `intraday_bar_id` is nullable and must remain `null`, not absent / `0` / empty string.

- **Not-evaluated vs failed separated:** ✅  
  This ticket does not invent evaluation/failure status aliases.

- **Strict/Preflight atomicity:** ✅  
  Index files are only finalized after successful artifact creation.

- **Deterministic ordering / tie-breakers:** ✅  
  `recent_runs.json` is newest-first; compact lists and counts are deterministic for identical input.

- **Authority consistency:** ✅  
  No second manifest truth, no `data_resolution_class` alias, no competing report schema.

## Tests (required if logic changes)

### Unit tests

#### Schema version
- `SCHEMA_VERSION == "ir1.0"`

#### Scalar contract tests
- `run_id` accepts non-empty opaque strings without enforcing an internal format
- `as_of_utc` serializes as ISO 8601 UTC string in the format `YYYY-MM-DDTHH:MM:SSZ`
- `intraday_bar_id` is present and `null` for daily fixtures

#### Report summary serialization
Given a valid fixture input, `report.json` must:
- include all required top-level keys,
- serialize `daily_bar_id` as string,
- serialize `intraday_bar_id` as `null` for daily,
- include all `counts_by_bucket` keys even when zero,
- include all `symbol_lists` keys even when empty,
- serialize each `symbol_lists` element as a plain symbol string,
- write `manifest_path` and `diagnostics_path` as repository-root-relative paths.

#### Diagnostics serialization
Given the minimal stub fixture record, diagnostics serialization must:
- preserve all required top-level keys,
- preserve `as_of_utc` in ISO 8601 UTC string form,
- preserve `intraday_bar_id = null` for daily,
- preserve `data_4h_available`,
- preserve all required empty block dicts.

#### `latest.json` and `latest_daily.json`
- `latest.json` content is identical to the latest run `report.json`
- `latest_daily.json` content is identical to the latest daily `report.json`

#### `latest_confirmed_candidates.json` invariant
Fixture case:
- one symbol in `confirmed_candidates`,
- one symbol in `late_monitor` because of `CONFIRMED_PATTERN_UNRESOLVED`.

Expected:
- confirmed symbol appears,
- late-monitor symbol does not appear,
- payload is a JSON array of plain symbol strings.

#### `latest_watchlist.json`
- payload is a JSON array of plain symbol strings,
- values are derived directly from `report.json.symbol_lists.watchlist`.

#### `latest_paths.json`
- contains `run_id`, `scan_mode`, `as_of_utc`, `daily_bar_id`, `intraday_bar_id`, `report_path`, `diagnostics_path`, `manifest_path`
- all path fields are repository-root-relative

#### `recent_runs.json`
Given multiple run summaries:
- entries are newest-first,
- length is truncated to `recent_runs_limit`,
- each entry has required fields,
- `intraday_bar_id` is always present,
- all path fields are repository-root-relative.

#### Pointer semantics
- `manifest_path` points to canonical manifest location
- no manifest body is copied into `report.json`
- writing `manifest_path` does not require that the target file already exists physically
- if present, `latest_manifest.json` contains only a pointer/reference payload

#### Path date-basis tests
- for a fixture with `daily_bar_id = "2025-12-31"`, run and daily artifact directories use `2025/12/31`
- path date derivation uses `daily_bar_id`, not `as_of_utc`

#### Atomic writes
Mock/fake filesystem or temp-dir based test:
- write temp file,
- rename to final path,
- index files are not finalized before main run artifacts exist.

#### Config validation
- missing `independence_release.reports` → defaults apply
- `recent_runs_limit = 30` → valid
- `recent_runs_limit = 0` → `ValueError`
- `recent_runs_limit = "30"` → `ValueError`
- `emit_report_md = "false"` → `ValueError`
- partial override such as `{recent_runs_limit: 10}` merges with remaining defaults

### Integration tests
If the repo already has a suitable pattern, add a lightweight integration test that writes:
- one run report,
- one diagnostics gzip,
- index files,
- and verifies final paths/content shape end-to-end.

## Constraints / Invariants (must not change)

- [ ] `schema_version` is exactly `ir1.0`
- [ ] `scan_mode` values are exactly `daily` and `intraday`
- [ ] `run_id` is a non-empty opaque string; T13 does not format-validate it
- [ ] `as_of_utc` is ISO 8601 UTC string `YYYY-MM-DDTHH:MM:SSZ`
- [ ] `daily_bar_id` is `YYYY-MM-DD` string
- [ ] `intraday_bar_id` is nullable integer close-time UTC milliseconds
- [ ] `intraday_bar_id` is always present; daily uses `null`
- [ ] `run_id` is a non-empty opaque string; no internal format validation is introduced in T13
- [ ] `as_of_utc` is an ISO 8601 UTC string in the format `YYYY-MM-DDTHH:MM:SSZ`
- [ ] `data_4h_available` is the only canonical data-resolution field in this ticket
- [ ] `data_resolution_class` is not introduced
- [ ] `report.json` is compact summary, not full diagnostics
- [ ] `symbol_diagnostics.jsonl.gz` is canonical full diagnostics artifact
- [ ] `run.manifest.json` remains canonical only under `snapshots/runs/...`
- [ ] no manifest duplication under `reports/`
- [ ] `manifest_path` is written as reference only and is not existence-checked by the output layer
- [ ] `latest_manifest.json`, if implemented, is pointer-only
- [ ] `latest.json` is content-identical to the latest run `report.json`
- [ ] `latest_daily.json` is content-identical to the latest daily `report.json`
- [ ] `symbol_lists` in `report.json` are exactly: `confirmed_candidates`, `early_candidates`, `watchlist`, `late_monitor`
- [ ] `discarded` is counted but not listed in compact symbol lists
- [ ] `latest_confirmed_candidates.json` excludes `late_monitor`
- [ ] `latest_confirmed_candidates.json` payload is a JSON array of plain symbol strings
- [ ] `latest_watchlist.json` payload is a JSON array of plain symbol strings
- [ ] `recent_runs.json` is newest-first and bounded
- [ ] all path reference fields are repository-root-relative
- [ ] `manifest_path` is written without requiring physical target existence at write time
- [ ] `YYYY/MM/DD` path depth is derived from `daily_bar_id`
- [ ] temp-file + atomic rename is used for final writes
- [ ] `latest.json` and `latest_daily.json` are identical-content latest-pointer copies of their canonical source reports
- [ ] `reports/runs/YYYY/MM/DD/` and `reports/daily/YYYY/MM/DD/` derive `YYYY/MM/DD` from `daily_bar_id`
- [ ] index finalization happens only after run artifacts are complete
- [ ] no execution placeholder semantics are introduced
- [ ] no continuity/history semantics are introduced
- [ ] no manual edits to `docs/code_map.md`
- [ ] no manual edits to `docs/GPT_SNAPSHOT.md`

---

## Definition of Done (Codex must satisfy)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/`
- [ ] Added/updated tests per concrete test specifications
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata (optional)
```yaml
created_utc: "2026-04-22T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on:
  - "Ticket 1"
  - "Ticket 2"
gesamtkonzept_ref: "§19 Ticket 13"
related_issues: []
```