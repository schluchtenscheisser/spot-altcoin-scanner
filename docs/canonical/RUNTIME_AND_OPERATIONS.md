# Runtime and Operations — Current-State Operating Model (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_RUNTIME_AND_OPERATIONS
status: canonical
persistence_foundation: sqlite
scan_types:
  - daily_discovery_scan
  - intraday_promotion_scan
bar_clock_policy: utc_closed_bar_only
mode_model: canonical_daily_intraday_with_input_aliases
```

## Purpose and scope

This document describes current scanner runtime operations: active entry points, Daily vs Intraday operation, canonical run-mode naming, scan-mode storage/report boundaries, compatibility aliases, backfill compatibility, and operational guardrails.

It does not define field-level data model, report, diagnostics, Entry-Location, T30, schema-version, or nullable/not-evaluated semantics. Those details belong to dedicated data/report/snapshot/schema documentation.

## Runtime entry points

The active scanner runtime entry points are:

| Entry point | Operational role |
|---|---|
| `scanner/main.py` | CLI/config input boundary. It accepts canonical modes plus compatibility aliases and resolves them to a Daily or Intraday runner target. |
| `scanner/runners/daily.py` | Active Daily Discovery operation for the latest closed daily context or explicit historical daily date used by the runner. |
| `scanner/runners/intraday.py` | Active Intraday Promotion operation for the latest closed 4h context and prior daily context. |

Operationally, callers should think in two current runner targets: Daily Discovery and Intraday Promotion. Old mode names may remain accepted at input boundaries, but they are not separate runtime modes.

## Daily vs intraday operation

### Daily Discovery Scan

Daily Discovery is the full closed-daily scanner pass. It resolves the run universe, loads closed-bar inputs, builds features, evaluates axes/phase/state/entry/decision/execution context, writes reports and diagnostics, writes run metadata, persists state patches, and emits the run manifest.

Daily Discovery is the active route for canonical `daily_discovery` input and for compatibility aliases that map to the Daily runner.

### Intraday Promotion Scan

Intraday Promotion is the 4h closed-bar promotion/recheck pass. It loads prior Daily context, selects the monitoring universe, refreshes required intraday inputs, evaluates attachable execution context, writes intraday reports and diagnostics, writes intraday run metadata, and emits the run manifest.

Intraday Promotion is the active route for canonical `intraday_promotion` input only.

## Canonical run mode naming

The repository deliberately separates three mode contexts:

```text
SQLite run_metadata.scan_mode:   daily_discovery / intraday_promotion   (T1-canonical)
Report/Diagnostics scan_mode:    daily / intraday                        (T13-canonical)
Compatibility aliases:           standard / fast / offline / backtest    (CLI/input-layer only)
```

Required operational interpretation:

- CLI/config input accepts canonical names `daily_discovery` and `intraday_promotion`.
- CLI/config input also accepts the old names `standard`, `fast`, `offline`, and `backtest` only as compatibility aliases.
- SQLite `run_metadata.scan_mode` uses `daily_discovery` / `intraday_promotion`.
- Report and diagnostics `scan_mode` uses `daily` / `intraday`.
- Compatibility aliases do not define additional runner targets, storage modes, report modes, or diagnostics modes.

## Storage vs Report/Diagnostics `scan_mode` boundary

`scan_mode` has different valid values depending on where it appears:

| Context | Canonical values | Notes |
|---|---|---|
| CLI/config input | `daily_discovery`, `intraday_promotion`, plus compatibility aliases | Input-layer only; resolves to runner targets. |
| SQLite `run_metadata.scan_mode` | `daily_discovery`, `intraday_promotion` | Runner-level / T1-canonical persisted metadata values. |
| Report/Diagnostics `scan_mode` | `daily`, `intraday` | Output-level / T13-canonical values. |

Do not use `daily` or `intraday` as new canonical SQLite `run_metadata.scan_mode` values. Do not use `daily_discovery` or `intraday_promotion` as report/diagnostics `scan_mode` values. Always identify which `scan_mode` context is being changed before editing code, tests, schemas, or documentation.

## Compatibility aliases

The old mode names standard, fast, offline, and backtest are compatibility aliases at the CLI/config/input layer. They are not independent runtime modes and must not be emitted as new canonical Storage, Report, or Diagnostics scan_mode values.

Current alias behavior:

| Input mode | Runner target | SQLite `run_metadata.scan_mode` | Report/diagnostics `scan_mode` |
|---|---|---|---|
| `daily_discovery` | Daily | `daily_discovery` | `daily` |
| `intraday_promotion` | Intraday | `intraday_promotion` | `intraday` |
| `standard` | Daily compatibility alias | `daily_discovery` | `daily` |
| `fast` | Daily compatibility alias | `daily_discovery` | `daily` |
| `offline` | Daily compatibility alias | `daily_discovery` | `daily` |
| `backtest` | Daily compatibility alias | `daily_discovery` | `daily` |

Compatibility aliases may appear at CLI/config/input-layer boundaries. They must not leak into new Storage, Report, or Diagnostics contexts.

## Backfill and historical reconstruction compatibility

`backfill_snapshots.py --mode full` is retained as compatibility-only / historical reconstruction support. It is not the current v2.1 Daily/Intraday runtime.

Operational consequences:

- Do not use full-mode backfill as evidence for the current Daily/Intraday scanner architecture.
- Do not present `scanner.pipeline.run_pipeline` or `scanner.pipeline.scoring/*` as active Daily/Intraday runtime because full-mode backfill can reach them.
- If historical reconstruction needs the full mode, document that invocation as compatibility/historical reconstruction work, not as a current scanner run mode.

## Persistence foundation

SQLite is the persistence foundation for the current scanner operating model. The active runners write technical run metadata and state/context data through `scanner/storage`, with current run metadata scan-mode values constrained to `daily_discovery` and `intraday_promotion`.

## Canonical UTC bar semantics

All bar-clock behavior is UTC-only. Local timezone conversion is forbidden. Exact close boundaries are inclusive: if `t` equals a daily or 4h close timestamp exactly, the bar that closes at `t` is treated as closed.

### Bar-clock public input contract
- Accepted input forms for `daily_bar_id`, `intraday_bar_id`, and `delta_closed_4h_bars`:
  - timezone-aware `datetime` (any offset; normalized by instant to UTC),
  - ISO-8601 strings,
  - raw numeric Unix timestamps interpreted as **epoch milliseconds**.
- Raw numeric seconds are not a canonical input form.
- Naive `datetime` values are rejected (no silent timezone relabeling).

### Daily bar schedule
- Exchange: MEXC
- Daily close: `00:00:00.000 UTC`
- A bar for date `D` opens at `D 00:00 UTC` and closes at `(D + 1 day) 00:00 UTC`
- `daily_bar_id(t)` returns the date `D` of the most recently closed daily bar

| Input timestamp (UTC) | Most recent daily close `<= t` | Closed bar date | `daily_bar_id` |
|---|---|---|---|
| `2026-03-24T00:00:00.000Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |
| `2026-03-24T00:00:00.001Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |
| `2026-03-24T12:00:00.000Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |
| `2026-03-23T23:59:59.999Z` | `2026-03-23T00:00:00Z` | `2026-03-22` | `2026-03-22` |
| `2026-03-24T23:59:59.999Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |

### 4h bar schedule
- Close times: `00:00`, `04:00`, `08:00`, `12:00`, `16:00`, `20:00 UTC`
- `intraday_bar_id(t)` returns the UTC epoch-millisecond close time of the most recently closed 4h bar

| Input timestamp (UTC) | Most recent 4h close `<= t` | `intraday_bar_id` |
|---|---|---|
| `2026-03-24T04:00:00.000Z` | `2026-03-24T04:00:00Z` | `1774324800000` |
| `2026-03-24T04:00:00.001Z` | `2026-03-24T04:00:00Z` | `1774324800000` |
| `2026-03-24T03:59:59.999Z` | `2026-03-24T00:00:00Z` | `1774310400000` |
| `2026-03-24T08:30:00.000Z` | `2026-03-24T08:00:00Z` | `1774339200000` |

### Closed-bar delta semantics
`delta_closed_4h_bars(t_previous, t_current)` counts 4h close boundaries in the half-open interval `(t_previous, t_current]`.

| `t_previous` | `t_current` | Result |
|---|---|---|
| `2026-03-24T00:00:00Z` | `2026-03-24T04:00:00Z` | `1` |
| `2026-03-24T00:00:00Z` | `2026-03-24T08:00:00Z` | `2` |
| `2026-03-24T00:00:01Z` | `2026-03-24T04:00:00Z` | `1` |
| `2026-03-24T04:00:00Z` | `2026-03-24T04:00:00Z` | `0` |
| `2026-03-24T00:00:00Z` | `2026-03-25T00:00:00Z` | `6` |

### Fixed daily-to-4h mapping
`DAILY_SCAN_DELTA_BARS = 6` is canonical. Future daily/intraday coordination must use this constant instead of recomputing or introducing alternative mappings.

### Invalid timestamp handling
- `None` is invalid and raises `TypeError`
- `NaN`, `inf`, and `-inf` are invalid numeric timestamps and raise `ValueError`
- Naive `datetime` values are invalid and raise `TypeError`
- Unsupported types raise `TypeError`

## Operational guardrails

- The current scanner does not implement live trading or automated order execution.
- Daily and Intraday runner targets must remain distinct operational flows.
- Compatibility aliases are accepted only at CLI/config/input boundaries and must not be emitted as new canonical Storage, Report, or Diagnostics `scan_mode` values.
- `scanner/pipeline/*` is not the current Daily/Intraday runtime architecture; retained pipeline paths are legacy/compatibility/historical reconstruction boundaries only where explicitly classified.
- Active tradeability metrics belong to `scanner/execution/tradeability_metrics.py`.
- Deep output/report/data semantics are intentionally deferred to the dedicated data model, report, snapshot, and schema documentation layer.

## Pointers to output/report/data model details

Use this runtime document for operational flow and run-mode boundaries. Use the dedicated canonical documents when validated for current state for:

- data model/schema details (`docs/canonical/DATA_MODEL.md`, `docs/SCHEMA_CHANGES.md`),
- report and diagnostics field details (`docs/canonical/REPORTS.md`),
- snapshot and replay artifact details (`docs/canonical/SNAPSHOTS.md`),
- architecture/module boundaries (`docs/canonical/ARCHITECTURE.md`).

## Shadow-Live Daily Workflow Operations Contract (Ticket 22)

- Workflow: `.github/workflows/independence-shadow-live.yml`
- Triggers:
  - manual `workflow_dispatch`
  - scheduled UTC run (`cron`)
- The scan job remains read-only (`contents: read`) and does not receive repository write permission.
- A downstream `persist-reports` job may use narrowly scoped `contents: write` permission after a successful scan to commit only allowlisted small plaintext report/index artifacts.
- This workflow is a diagnostic/research runtime (shadow-live), not trading automation.
- Daily run is blocking and primary.
- Evaluation replay/export is blocking and required after daily run artifacts are written.
- Intraday is diagnostic and non-blocking in the known current architecture state.
- Known non-blocking intraday state:
  - `reasons.intraday_skip_reason=\"missing_intraday_cycle_context\"`
  - `execution_attempted=false`
- Forbidden runtime outputs remain forbidden:
  - manifest bodies under `reports/runs/**.manifest.json`
  - active writes under `reports/analysis/**`

- The scan job uploads a dedicated `shadow-live-reports` artifact containing `reports/index/`, `reports/daily/`, and `reports/runs/` so the persistence job does not rely on cross-job filesystem state.
- The persistence job downloads that artifact and uses the daily run report as its idempotency anchor: when `reports/runs/YYYY/MM/DD/<daily_run_id>/report.json` already exists in the checkout, it skips commit creation successfully.
- Persisted report paths are allowlisted to index JSON plus `report.json` files under `reports/daily/YYYY/MM/DD/` and `reports/runs/YYYY/MM/DD/<run_id>/`; full diagnostics remain artifact-only.
- Forbidden repository-persisted outputs include `symbol_diagnostics.jsonl.gz`, Excel reports, Parquet files, ZIP files, snapshots, raw market data, and large debug/profiling artifacts.
- Allowed shadow-live output roots are explicitly bounded to:
  - `artifacts/`
  - `data/`
  - `evaluation/exports/`
  - `evaluation/replay/`
  - `logs/`
  - `reports/runs/`
  - `reports/daily/` (optional convenience copies)
  - `reports/index/` (optional convenience/index copies)
  - `snapshots/runs/`
  - `snapshots/history/ohlcv/`
- Node.js runtime stance for GitHub JavaScript actions in this workflow:
  - prefer Node-24-compatible action versions;
  - enforce Node 24 execution via `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=\"true\"`;
  - do not use `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true`.


## Analysis Script Runner Operations Contract (Ticket 19)

- Workflow: `.github/workflows/run-analysis-script.yml`
- Trigger: manual `workflow_dispatch` with required input `script_path`.
- `script_path` must be a relative path to an existing `.py` file under `scripts/`.
- The workflow must validate `script_path` via `scripts/_runner_guard.py` and execute only the normalized guarded output.
- Invalid `script_path` (empty, absolute, traversal, outside `scripts/`, non-`.py`, missing, directory) fails before script execution.
- Permissions are read-only (`contents: read`); analysis runs must not commit/push generated files.
- Analysis file outputs are uploaded as action artifacts only (not repository writeback).
- Allowed artifact collection roots for this workflow are exactly:
  - `evaluation/exports/**`
  - `evaluation/calibration/**`
  - `artifacts/**`
  - `reports/aux/**`
- `reports/analysis/**` is deprecated/not allowed for this workflow contract.
- Artifact upload uses `if-no-files-found: warn` because valid analysis runs may produce stdout-only output.

## AI Sparring Runtime Operations Contract

`tools/ai_sparring/` provides a manual/operator-triggered runtime (local CLI and `workflow_dispatch`) for design/code review sparring.

### Preflight (atomic)
Before the first provider call, preflight must validate:
- prompt, mode, rounds,
- provider names and required model ids,
- required API keys for selected real providers,
- required default context files,
- optional repo-relative context-path validity (inside repo, regular file, UTF-8, <= 153600 bytes).

If preflight fails, zero output files are written.

### Deterministic context loading
Default context sources are always loaded first in this order:
1. `docs/AGENTS.md`
2. `docs/code_map.md`
3. `docs/canonical/ROADMAP.md`

Optional `--context-path` entries are normalized to repo-relative POSIX paths, sorted lexicographically, deduplicated, and appended after defaults.

### Mode and prompt resolution contract
`mode` changes only role-specific resolved default system prompts. It does not change context loading, artifact filenames, session schema version, or round structure.

For each supported mode, the runtime resolves and persists deterministic prompt identifiers:
- `resolved_prompts.drafter`
- `resolved_prompts.reviewer`

Required `(role, mode)` prompt identity matrix:
- `drafter.ticket_review`
- `reviewer.ticket_review`
- `drafter.implementation_planning`
- `reviewer.implementation_planning`
- `drafter.roadmap_review`
- `reviewer.roadmap_review`

### Round input visibility contract
For round `r`:
- `draft_1` sees prompt, mode, and loaded context sources.
- `review_r` sees prompt, mode, loaded context sources, and `draft_r`.
- `revision_r` sees prompt, mode, loaded context sources, `draft_r`, and `review_r`.
- `draft_(r+1)` sees prompt, mode, loaded context sources, and exactly prior round `review_r` plus `revision_r`.

Full session-history replay to each provider call is not part of this contract.

### Runtime persistence semantics
Session artifacts are:
- `session.json`
- `session.md`
- `final_summary.md`

`session.json` uses `session_version: 2` and statuses:
- `completed`
- `failed_runtime` (no protocol step succeeded)
- `failed_partial` (at least one protocol step succeeded)

When provider/runtime failure happens after successful preflight, completed protocol steps are preserved and artifacts are still written.

### Retry policy
A single explicit retry wrapper is used for real providers:
- 3 attempts total,
- delay before attempt 2: 5s,
- delay before attempt 3: 15s,
- retries only on connection/timeouts/HTTP 429/HTTP 5xx,
- no retries for validation/auth/configuration/provider-selection failures.

## AI Sparring Issue Operations Contract

Issue UI is additive and does not replace `workflow_dispatch`.

- Workflow: `.github/workflows/ai-sparring-issue.yml`
- Event: `issue_comment` with `types: [created]`
- Permissions are limited to:
  - `contents: read`
  - `issues: write`
  - `actions: read`
- Concurrency is serialized per issue number with `cancel-in-progress: false`.
- Non-command comments are no-op (no state mutation, no artifact upload).
- Terminal states are: `completed`, `stopped`, `failed_runtime`, `failed_partial`.
- Only `awaiting_continue` is active/resumable.
- `/continue` resume resolution uses pointer `latest_run_id` and pointer `latest_artifact_name` against the Actions artifacts REST endpoints.
- `/focus <text>` updates `current_focus` only and preserves `latest_run_id` + `latest_artifact_name`.
- `/stop` sets pointer status to `stopped`, preserves prior artifact pointer references, and does not upload a new artifact.

### Daily Discovery Scan — universe-admission chain (Ticket 3)
1. discover symbols
2. pre-1d eligibility
3. 1d fetch
4. 1d raw derivation
5. post_1d_activity_gate
6. monitoring bypass
7. pre_4h_candidate_filter (non-bypass only)
8. non-bypass cap selection
9. 4h fetch for selected symbols

## Ticket 4 runtime contract: cache policy + fetch windows

- `cache_status`: `fresh | stale | missing | broken`.
- `fetch_decision`: `skip | fetch_full | fetch_incremental`.
- Closed-bar-only: only bars with `close_time_utc_ms <= most_recent_closed_bar_close_time_utc_ms(timeframe, now)` are eligible for persistence.
- Full fetch accepted window: last `lookback_bars_<tf>` closed bars ending at current cutoff.
- Incremental fetch accepted window: `cached_close_time_utc_ms < close_time_utc_ms <= cutoff`.
- No-backfill/no-interpolation: missing bars remain absent.
- Rejections are bar-level and counted (`partial`, `invalid`, `misaligned`, `duplicates`).
- `fetch_and_persist` flow: decision → skip(no API/no writes) OR fetch_closed_bars → persist_fetch (atomic bars+meta write).

## Ticket 5 runtime contract (feature derivation)

Public ticket-5 functions accept pre-loaded closed OHLCV sequences and bar-clock context. They must not access repositories, SQLite, Parquet, or cache metadata directly.

Input preconditions at function entry:
- wrong type => `TypeError`
- invalid content/preconditions => `ValueError`
- `ohlcv_1d=[]` invalid
- `ohlcv_4h=[]` invalid (use `None` for unavailable 4h)

Determinism/semantics:
- closed-bar-only inputs
- no shortened-window fallback
- field-local failure nulls only affected field + companion status
- EMA warm-up uses SMA bootstrap and requires at least `2 x period` bars for `ok` status.

## Ticket 6 runtime boundary (Tier-1 axes)

`compute_tier1_axes(...)` is deterministic and closed-input:
- reads only `FeatureBundle` and `cfg.axes`
- no direct OHLCV access
- no repository/cache/SQLite/Parquet IO
- no raw `now`/timestamp side effects.

## Ticket 8 runtime verification boundaries (phase interpreter)

- Public entrypoint is exactly `compute_phase_interpretation(tier1_bundle, tier2_bundle, cfg)`.
- Bundle identity fields must match exactly (`symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available`) or fail hard.
- Minimum-basis failure, hard-floor failure, and global-confidence-floor `none` remain diagnostically distinct.
- Tie-break is deterministic: higher `phase_score`, then higher `phase_floor_margin`, then fixed phase order.
- `market_phase_runner_up` is deterministic and non-nullable, including exact ties and all-zero scores.
- Reduced-resolution confidence cap is derived only from weighted-score inputs used by the winning phase.
- `freshness_distance_structural` is passthrough-only and must not influence phase floors or weighted scores.

## Ticket 9 runtime boundary (state invalidation/cycle pre-state)

`compute_invalidation_and_cycle(...)` is a pure computation boundary:
- no repository handles,
- no storage writes,
- no OHLCV/raw timestamps.

Execution order is deterministic:
1. structural invalidation,
2. timing invalidation (only if structural is false),
3. cycle resolution and `resolved_setup_cycle_id` determination.

Ticket 10 consumes this bundle and performs the single authoritative persistence write.

## Ticket 10 runtime policy (state admission, freshness, and counters)

- `compute_state_machine(...)` must call `compute_state_freshness(...)` exactly once and forward that bundle unchanged.
- `delta_closed_bars_relevant` is the canonical increment unit for all `bars_since_*` counters.
- New-cycle detection resets cycle-scoped state references and clears stale `cycle_end_*` markers.
- Terminal transitions into `rejected`/`chased` write `cycle_end_bar_index`, `cycle_end_timestamp`, and `bars_since_cycle_end=0` exactly on transition.
- `market_phase=none` without prior active-cycle evidence is a disposition (`admitted=false`), not a synthetic `rejected` state.
