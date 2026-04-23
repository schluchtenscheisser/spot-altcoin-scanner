> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Define Independence-Release history storage and snapshot lifecycle policy

## Context / Source
This ticket defines the canonical storage contract for Independence-Release historical OHLCV data and run snapshot placement/lifecycle.

The authoritative basis for this ticket is exclusively:

- the 7 v2.1 section documents,
- `independence_release_gesamtkonzept_final.md`.

The addendum is supplementary working context, not a competing primary authority. Existing repo docs and code remain relevant only insofar as they do not conflict with the current authoritative reference set.

This ticket corresponds to the Gesamtkonzept workstream block for history storage and snapshot lifecycle. It is the architecture ticket that fixes:

- canonical storage location for OHLCV base history,
- canonical Parquet partitioning rules for 1d and 4h OHLCV history,
- canonical placement of run snapshots under `snapshots/runs/`,
- lifecycle separation between base history, run artifacts, evaluation artifacts, and provenance artifacts,
- clean-start policy for OHLCV history persistence,
- the remaining operational role of SQLite cache metadata after OHLCV history moves to Parquet.

`depends_on:`
- Ticket 1: bar_clock / sqlite / config foundation
- Ticket 2: repo bootstrap / canonical structure foundation

Note: this ticket references Ticket 13 / `docs/canonical/OUTPUT_SCHEMA.md` only for the manifest-content ownership boundary. That reference is documentary and does not create a sequencing dependency.

## Goal
After this ticket is completed, the repository must provide:

1. a canonical Parquet-based storage contract for OHLCV base history (`1d` and `4h`) under `snapshots/history/ohlcv/`,
2. deterministic path-building and writer helpers for history partitions,
3. a canonical run-snapshot placement contract under `snapshots/runs/YYYY/MM/DD/<run_id>/`,
4. explicit clean-start policy stating that Parquet becomes the sole canonical OHLCV base-history store and that no SQLite-to-Parquet migration is performed,
5. explicit lifecycle/retention policy contracts for snapshot classes without implementing archive/delete jobs,
6. canonical docs that describe this storage model clearly for later runner and evaluation tickets.

## Scope
Allowed changes for this ticket:

- `scanner/storage/**` where snapshot/history path helpers, manifest-placement helpers, or lifecycle policy helpers belong
- `scanner/data/**` only if a small storage-path helper is more consistent there
- central config abstraction for `independence_release.snapshots` and/or `independence_release.retention`
- `tests/**` for history pathing, partitioning, lifecycle-policy, clean-start, and cache-meta-role tests
- `docs/canonical/**` where history storage, snapshot classes, and retention/lifecycle policy are described
- `docs/tickets/**` only as required by workflow docs

## Out of Scope
- Implementing daily or intraday runners
- Implementing OHLCV fetch logic itself
- Implementing active archive jobs or delete jobs
- Implementing evaluation/replay exports
- Implementing Parquet compaction policy beyond what is explicitly stated in this ticket
- Implementing backfill workflows beyond the explicit permission to rebuild individual monthly partitions
- Redefining manifest content or manifest required fields
- Redefining report artifacts under `reports/`
- Migrating historical OHLCV rows from SQLite into Parquet
- Keeping SQLite `ohlcv_bars` as a second canonical OHLCV history store

## Canonical References (important)
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/tickets/_TEMPLATE.md`
- Gesamtkonzept sections for:
  - directory roles and storage classes
  - snapshot classes A-D
  - Parquet partitioning for OHLCV history
  - canonical manifest placement under `snapshots/runs/...`
  - retention policy classes
- `docs/canonical/OUTPUT_SCHEMA.md` for manifest content ownership
- Addendum guidance that 4h fetch remains staged and persistence is a core architectural concern

## Mandatory Authority Rule
> If the current authoritative reference set, existing repo authority/canonical documents, and existing code conflict, the current authoritative reference set wins. Repo documents and existing code remain valid only insofar as they do not contradict that reference set.

## Proposed change (high-level)

### Before
- The repo may still treat SQLite as a historical OHLCV persistence candidate.
- There may be no fixed canonical Parquet partitioning contract for `1d` and `4h` OHLCV history.
- The `snapshots/runs/...` placement contract may not yet be fixed independently of runner implementation.
- Lifecycle/retention intent may exist conceptually but not as explicit typed policy/contracts.

### After
- Parquet under `snapshots/history/ohlcv/` is the sole canonical base-history store for OHLCV `1d` and `4h`.
- OHLCV history uses one explicit partitioning rule: `timeframe + symbol + year/month`.
- Open month partitions are mutable/appendable; closed month partitions are immutable.
- `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` is the canonical run-manifest placement.
- Manifest content remains owned by Ticket 13 / `OUTPUT_SCHEMA.md`; this ticket only fixes placement and lifecycle.
- SQLite `ohlcv_bars` loses its canonical history role.
- SQLite `ohlcv_cache_meta` explicitly retains an operational rest role for fetch/refresh decisions.
- Retention and storage-class policy become explicit contracts without implementing archive/delete automation.

### Edge cases
- No SQLite-to-Parquet migration script is introduced.
- Existing SQLite `ohlcv_bars` content is not treated as canonical after this ticket.
- The canonical run-snapshot path exists conceptually from T14 onward, but T14 does not need to create empty production directories preemptively.
- Path references created by this ticket must use repository-root-relative paths, not absolute filesystem paths.
- Closed months may be rebuilt only by explicit repair/backfill operations; they are not silently reopened.

### Backward compatibility impact
This ticket deliberately moves canonical OHLCV base-history storage to Parquet under `snapshots/history/ohlcv/`. Any pre-existing SQLite OHLCV rows become non-canonical legacy/transitional data. This is a clean-start decision, not a migration ticket.

## Codex Implementation Guardrails (No-Guesswork, mandatory)

- **Workflow priority:** Follow `docs/canonical/WORKFLOW_CODEX.md` strictly.
- **Canonical docs first or alongside code:** This ticket defines storage contracts. Update canonical docs in the same PR.
- **No second truth:** Do not keep SQLite `ohlcv_bars` as an alternative canonical OHLCV base-history store.
- **Manifest ownership boundary:** Do not redefine manifest content or required fields here. Manifest content is already canonically defined by Ticket 13 / `docs/canonical/OUTPUT_SCHEMA.md`.
- **Clean start means no migration:** Do not add a migration script from SQLite OHLCV rows to Parquet.
- **No silent compaction policy:** Do not invent compaction/rewrite rules beyond what is explicitly specified in this ticket.
- **No runner leakage:** Do not make runner orchestration decisions in this ticket.
- **No raw-dict schema drift:** Typed config and lifecycle policy definitions must live centrally and not as ad hoc dictionaries scattered across modules.
- **No committed history data:** Parquet files under `snapshots/history/ohlcv/` are not regularly committable per the canonical storage policy. Ensure `.gitignore` covers this path. Do not commit OHLCV Parquet partitions.
- **No committed run snapshots:** Point-in-time files under `snapshots/runs/` are not regularly committable. Ensure `.gitignore` covers this path. Do not commit run snapshot artifacts from operational runs.
- **No manual edits to generated docs:** `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` remain read-only.

## Required storage class and lifecycle model (binding)

This ticket treats the snapshot/storage model using the canonical classes from the Gesamtkonzept:

- **Class A — base history:** canonical OHLCV base history under `snapshots/history/`
- **Class B — point-in-time run artifacts:** canonical run snapshots under `snapshots/runs/...`
- **Class C — evaluation/calibration artifacts:** explicitly out of scope for this ticket
- **Class D — manifest/provenance artifacts:** canonical manifest placement under `snapshots/runs/...`

This ticket must not blur these classes or introduce hybrid placement rules.

## Clean-start policy (binding)

T14 makes the following clean-start decision explicit:

- Parquet under `snapshots/history/ohlcv/` becomes the sole canonical persistence for OHLCV base history.
- Existing SQLite `ohlcv_bars` rows are not migrated.
- T14 contains no migration script.
- Existing SQLite OHLCV rows, if present, are treated as non-canonical transitional/legacy data and must not be used as the canonical long-term history store after this ticket.

> This ticket adopts a clean-start policy for OHLCV base-history persistence. No SQLite-to-Parquet migration is performed. Parquet is the only canonical base-history store after T14.

## SQLite residual role after clean start (binding)

### `ohlcv_bars`
- loses its canonical OHLCV-history role completely with this ticket
- must not remain an alternative canonical base-history source

### `ohlcv_cache_meta`
- explicitly retains an operational rest role
- purpose: fetch/refresh decision support for the current operational fetch cycle
- includes metadata such as:
  - `cache_status`
  - `cached_close_time_utc_ms`

This means:
- Parquet = canonical long-term/history storage
- SQLite `ohlcv_cache_meta` = operational fetch/cache metadata
- SQLite `ohlcv_bars` = non-canonical / no longer the canonical history store

## Required module responsibilities (binding, not suggestion)

This ticket does not force a single exact filename layout, but responsibilities must be clearly separated and centralized.

### History storage / partition helpers
Responsible for:
- canonical history path building under `snapshots/history/ohlcv/`
- Parquet partition path derivation for `timeframe`, `symbol`, `year`, `month`
- rules for open vs closed month mutability

### Run snapshot placement helpers
Responsible for:
- canonical run snapshot path derivation under `snapshots/runs/YYYY/MM/DD/<run_id>/`
- canonical `run.manifest.json` placement helper
- no manifest content redefinition

### Lifecycle / retention policy definitions
Responsible for:
- typed policy/config for storage classes
- online/archived/durable policy semantics
- no active archive or deletion jobs in this ticket

Codex must not distribute these responsibilities arbitrarily across unrelated modules.

## Canonical history storage contract (binding)

### Supported canonical OHLCV history scopes in T14
This ticket covers only:
- `1d` OHLCV base history
- `4h` OHLCV base history

It does not generalize further to other history classes in this ticket.

### Canonical base-history root
The canonical root for OHLCV base history is:

- `snapshots/history/ohlcv/`

### Partitioning rule
OHLCV Parquet history must be partitioned by:
- `timeframe`
- `symbol`
- `year`
- `month`

Canonical partition-directory shape:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=TAOUSDT/year=2026/month=03/
snapshots/history/ohlcv/timeframe=4h/symbol=TAOUSDT/year=2026/month=03/
```

Concrete Parquet file naming inside that partition directory is not canonicalized by this ticket and may be determined by the writer implementation.

### Allowed `timeframe` values in this ticket
- `1d`
- `4h`

No other timeframe values are introduced in T14.

### `symbol`
- type: `str`
- semantics: exchange symbol string such as `TAOUSDT`
- must be non-empty
- path-building must reject path separators or traversal attempts in `symbol`

### `year`
- type: four-digit numeric year component in the partition path

### `month`
- type: two-digit month component `01`..`12` in the partition path

## Open-vs-closed month mutability rules (binding)

### Open month
A month partition `(year, month)` is classified as **open** if the explicit `reference_date` passed to the classifier falls within that same calendar month.

An open month partition may be:
- appended to,
- replaced/rebuilt in full,
- repaired in full if necessary.

### Closed month
A month partition `(year, month)` is classified as **closed** if the explicit `reference_date` passed to the classifier falls in any later calendar month.

A closed month partition is immutable in normal operation.

Closed month partitions may only be changed by an explicit repair/backfill workflow that deliberately rebuilds the affected month partition.

> T14 does not introduce any broader compaction or automatic rewrite policy beyond this open/closed month rule.

### Open/closed classifier contract
The open/closed month classifier must take the reference date/time explicitly as an input parameter. It must not read wall-clock time internally.

For the purposes of this ticket, the reference date is derived from the current run's `daily_bar_id` and passed explicitly to the classifier as a `date` or `datetime`-derived date value.

Illustrative examples:
- `is_month_open(year=2026, month=3, reference_date=date(2026, 3, 15))` → open
- `is_month_open(year=2026, month=3, reference_date=date(2026, 4, 1))` → closed

## Repair / backfill semantics (binding)

T14 does not implement a full backfill system.

It defines only the following contract:
- targeted repair/backfill is allowed at the granularity of an individual monthly partition
- such repair/backfill may rebuild a month partition completely
- this permission does not imply any generic automatic backfill orchestration in this ticket

## Canonical run snapshot placement contract (binding)

### Canonical run snapshot root
Run snapshots use:
- `snapshots/runs/YYYY/MM/DD/<run_id>/`

### Date basis for `YYYY/MM/DD`
For run snapshot placement, `YYYY/MM/DD` is derived from the run artifact's `daily_bar_id` value.

That means:
- `YYYY/MM/DD` is derived from `daily_bar_id`
- not from wall-clock write time
- not from the date component of `as_of_utc` when that could differ from `daily_bar_id`

### Canonical manifest placement
The canonical manifest location is:
- `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`

### Manifest content ownership boundary
This ticket does **not** define manifest content or required manifest fields.
Those remain owned by Ticket 13 and canonically defined in `docs/canonical/OUTPUT_SCHEMA.md`.

T14 only defines:
- path placement,
- lifecycle/persistence expectations,
- non-duplication under `reports/`.

### Run-snapshot minimum in T14
T14 defines no additional mandatory run snapshot files beyond canonical manifest placement.

That means:
- `run.manifest.json` is the only mandatory run-snapshot file defined by this ticket
- no additional run snapshot sidecar files may be guessed or invented in T14

### Path status from T14 onward
The path `snapshots/runs/YYYY/MM/DD/<run_id>/` is canonical from T14 onward.

This means:
- T14 may implement path builders and manifest placement helpers against this path
- T14 may create the path in tests/fixtures when needed
- T14 does **not** need to pre-create empty production directories before later runners actually write run artifacts

## Path reference format (binding)

All path reference fields and path-returning helpers defined by this ticket must use repository-root-relative paths.

Examples:
- `snapshots/history/ohlcv/timeframe=1d/symbol=TAOUSDT/year=2026/month=03/`
- `snapshots/runs/2026/04/23/example-run-id/run.manifest.json`

Absolute filesystem paths are not allowed in artifact contracts defined by this ticket.

## Lifecycle / retention policy contract (binding)

This ticket defines lifecycle/retention policy as contracts and typed config only. It does not implement active archive/delete jobs.

### Base history (`snapshots/history/`)
- durable / retained
- not subject to routine deletion in this ticket

### Run snapshots (`snapshots/runs/`)
- online retention class applies
- later archive/move jobs may act on them according to later implementation tickets
- this ticket defines policy semantics only

### Manifest/provenance
- stays with the run snapshot
- no duplicate canonical manifest copy under `reports/runs/...`

### Evaluation artifacts
- explicitly outside this ticket

## Config semantics (mandatory)
If config is needed, extend the central config abstraction; do not introduce a parallel config loader.

Suggested config namespace in this ticket:

```yaml
independence_release:
  snapshots:
    history_root: snapshots/history
    runs_root: snapshots/runs
  retention:
    run_snapshots_online_days: 90
```

### Required config semantics
> Partial overrides in `independence_release.snapshots` and `independence_release.retention` are merged field-by-field with central defaults; missing sub-keys are not treated as invalid.

> Missing keys fall back to defaults. Invalid values produce a clear `ValueError` containing the key name and invalid value.

### Config validation
- snapshot roots must be non-empty strings
- retention day values must be positive integers

## Manifest path existence semantics (binding)
Because this ticket defines placement contracts before later runner tickets physically create all run snapshots, T14 must not require that the manifest target path already exists at contract-definition time.

If a helper returns a canonical manifest path, it returns a repository-root-relative string/path object representing the canonical target location. It does not, by itself, validate that a later runner has already created the file.

> T14 defines canonical manifest placement. It does not require that the referenced manifest file already exists physically at every call site where the canonical path is derived or referenced.

## Canonical docs to update
At minimum, update or create the relevant sections in canonical docs so later tickets can rely on:

- storage classes A/B/D and their separation,
- canonical `snapshots/history/ohlcv/` contract,
- Parquet partitioning by `timeframe + symbol + year/month`,
- open-vs-closed month mutability rules,
- clean-start policy (Parquet canonical, no SQLite migration),
- SQLite residual role (`ohlcv_cache_meta` operational, `ohlcv_bars` non-canonical),
- canonical run manifest placement under `snapshots/runs/YYYY/MM/DD/<run_id>/`,
- lifecycle/retention policy semantics without job automation,
- repository-root-relative path conventions,
- non-committable path classification for `snapshots/history/ohlcv/` and `snapshots/runs/` (including `.gitignore` coverage rule).

## Acceptance Criteria (deterministic)

1. The repo provides a canonical helper/contract layer for OHLCV base-history path derivation under `snapshots/history/ohlcv/`.

2. T14 supports exactly these canonical OHLCV history timeframes:
   - `1d`
   - `4h`

3. OHLCV history partition paths use exactly this partitioning basis:
   - `timeframe`
   - `symbol`
   - `year`
   - `month`

4. Canonical history paths are repository-root-relative, not absolute.

5. Canonical history partition-directory paths follow the shape:
   - `snapshots/history/ohlcv/timeframe=<tf>/symbol=<symbol>/year=<YYYY>/month=<MM>/`

6. `symbol` path input rejects path traversal and path separator cases.

7. A month partition `(year, month)` is classified as open if the explicit `reference_date` passed to the classifier falls within that same calendar month.

8. A month partition `(year, month)` is classified as closed if the explicit `reference_date` passed to the classifier falls in any later calendar month.

9. Open month partitions are explicitly allowed to be appended/rebuilt.

10. Closed month partitions are immutable in normal operation.

11. Closed month partitions may only be changed by explicit targeted repair/backfill at month-partition granularity.

12. T14 does not introduce broader compaction/rewrite policy beyond the explicit open/closed month rule.

13. T14 explicitly adopts clean-start policy:
   - Parquet becomes the sole canonical OHLCV base-history store
   - SQLite OHLCV rows are not migrated
   - no migration script is implemented

14. `ohlcv_bars` no longer remains a canonical OHLCV base-history store after T14.

15. `ohlcv_cache_meta` explicitly retains operational fetch/refresh metadata role, including metadata such as `cache_status` and `cached_close_time_utc_ms`.

16. The canonical run snapshot root is `snapshots/runs/YYYY/MM/DD/<run_id>/`.

17. For run snapshot placement, `YYYY/MM/DD` is derived from `daily_bar_id`.

18. The canonical manifest path is exactly:
   - `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`

19. T14 does not redefine manifest content or required manifest fields.

20. T14 defines `run.manifest.json` placement/lifecycle only; manifest content remains owned by Ticket 13 / `docs/canonical/OUTPUT_SCHEMA.md`.

21. T14 defines no additional mandatory run snapshot files beyond `run.manifest.json` placement.

22. The path `snapshots/runs/YYYY/MM/DD/<run_id>/` is canonical from T14 onward, but T14 does not need to create empty production directories preemptively.

23. Path references returned by helpers defined in this ticket are repository-root-relative.

24. T14 does not require that a canonical manifest target file already physically exists whenever its canonical path is derived or referenced.

25. Config for `independence_release.snapshots` / `independence_release.retention` uses merge-with-defaults semantics and rejects invalid values clearly.

26. Lifecycle/retention policy is defined as contract/config/helper semantics only; no active archive/delete jobs are implemented in this ticket.

27. Canonical docs are updated to describe the final storage/snapshot model and constraints defined in this ticket.

28. This ticket does not implement:
   - runners,
   - OHLCV fetch logic,
   - archive/delete jobs,
   - generic backfill orchestration,
   - evaluation/replay exports,
   - manifest content redefinition.

29. The ticket is archived in the same PR according to workflow docs.
## Default-/Edgecase coverage (mandatory)

- **Config Defaults (Missing key → Default):** ✅  
  Missing `independence_release.snapshots` / `independence_release.retention` keys fall back to defaults.

- **Config Invalid Value Handling:** ✅  
  Wrong type / invalid range in `independence_release.snapshots` / `independence_release.retention` produces clear `ValueError`.

- **Nullability / no bool coercion:** ✅  
  This ticket does not introduce new nullable business tri-state fields beyond path/reference semantics; no implicit coercion is allowed where config values are expected to be typed.

- **Not-evaluated vs failed separated:** ✅  
  This ticket does not invent evaluation/failure status aliases.

- **Strict/Preflight atomicity:** ✅  
  If this ticket writes files in tests/helpers, path contracts remain deterministic and do not rely on implicit runtime state.

- **Deterministic ordering / tie-breakers:** ✅  
  Partition-path derivation and run-snapshot path derivation are deterministic for identical input.

- **Authority consistency:** ✅  
  Manifest content remains T13-owned; T14 defines only placement/lifecycle and must not introduce a second manifest contract.

## Tests (required if logic changes)

### Unit tests

#### History partition path derivation
- `1d` + `TAOUSDT` + `2026-03` yields repo-root-relative partition-directory path `snapshots/history/ohlcv/timeframe=1d/symbol=TAOUSDT/year=2026/month=03/`
- `4h` + `TAOUSDT` + `2026-03` yields repo-root-relative partition-directory path `snapshots/history/ohlcv/timeframe=4h/symbol=TAOUSDT/year=2026/month=03/`

#### Timeframe validation
- `1d` accepted
- `4h` accepted
- unsupported timeframe rejected with clear error

#### Symbol path safety
- valid symbol such as `TAOUSDT` accepted
- invalid examples such as `../x`, `A/B`, `A\\B`, absolute-like path fragments rejected

#### Open/closed month mutability helpers / policy
- `is_month_open(year=2026, month=3, reference_date=date(2026, 3, 15))` -> open
- `is_month_open(year=2026, month=3, reference_date=date(2026, 4, 1))` -> closed
- open month classified mutable
- closed month classified immutable in normal operation
- targeted month rebuild permission can be represented without implying general compaction/orchestration
- classifier takes explicit `reference_date` input and does not read wall-clock time internally

#### Run snapshot path derivation
Given:
- `daily_bar_id = "2026-04-23"`
- `run_id = "example-run-id"`

expected canonical manifest path:
- `snapshots/runs/2026/04/23/example-run-id/run.manifest.json`

#### Manifest ownership boundary
- tests verify T14 helpers do not define or validate manifest content fields beyond placement/lifecycle responsibilities

#### Manifest existence semantics
- deriving the canonical manifest path must succeed even if no file yet exists at that path

#### Config validation
- missing snapshot/retention config → defaults apply
- invalid retention days (`0`, negative, string) → `ValueError`
- invalid root path types → `ValueError`
- partial overrides merge with defaults

#### Clean-start policy
- tests/documented helper behavior confirm no migration script or migration path is introduced by T14
- tests confirm no code path treats SQLite `ohlcv_bars` as the canonical history store after T14
- tests confirm `ohlcv_cache_meta` helpers/policy remain allowed for fetch metadata role

### Integration tests
If the repo already has a suitable pattern, add a lightweight integration-style test that:
- builds canonical history paths,
- builds canonical run manifest placement path,
- validates repo-root-relative outputs,
- confirms no absolute paths are emitted.

## Constraints / Invariants (must not change)

- [ ] Parquet under `snapshots/history/ohlcv/` is the sole canonical OHLCV base-history store after T14
- [ ] Supported canonical timeframes in this ticket are exactly `1d` and `4h`
- [ ] OHLCV history is partitioned by `timeframe + symbol + year/month`
- [ ] Open/closed month classification uses an explicit `reference_date` parameter; no implicit wall-clock reads
- [ ] A month is open iff `reference_date` falls within that same calendar month; it is closed if `reference_date` falls in any later calendar month
- [ ] Open month partitions are mutable; closed month partitions are immutable in normal operation
- [ ] T14 does not define any broader compaction policy
- [ ] No SQLite-to-Parquet migration script is introduced
- [ ] `ohlcv_bars` loses canonical base-history role
- [ ] `ohlcv_cache_meta` retains operational fetch/refresh metadata role
- [ ] Run snapshot root is `snapshots/runs/YYYY/MM/DD/<run_id>/`
- [ ] `YYYY/MM/DD` for run snapshots is derived from `daily_bar_id`
- [ ] Canonical manifest path is `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`
- [ ] Manifest content is not redefined in this ticket
- [ ] `run.manifest.json` is the only mandatory run-snapshot file defined here
- [ ] Path references are repository-root-relative, never absolute
- [ ] T14 does not require empty production run directories to be pre-created
- [ ] T14 does not require manifest file existence whenever canonical path is derived
- [ ] `snapshots/history/ohlcv/` Parquet history files are not regularly committable; `.gitignore` must cover them
- [ ] `snapshots/runs/` run snapshot artifacts are not regularly committable; `.gitignore` must cover them
- [ ] No manual edits to `docs/code_map.md`
- [ ] No manual edits to `docs/GPT_SNAPSHOT.md`

---

## Definition of Done (Codex must satisfy)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Implemented code/doc/config changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/`
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` in the same PR
- [ ] Added/updated tests per concrete test specifications
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata (optional)
```yaml
created_utc: "2026-04-23T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on:
  - "Ticket 1"
  - "Ticket 2"
gesamtkonzept_ref: "§19 Ticket 14"
related_issues: []
```
