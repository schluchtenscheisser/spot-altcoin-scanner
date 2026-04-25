# Runtime and Operations — Independence-Release Operating Model (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_RUNTIME_AND_OPERATIONS
status: canonical
persistence_foundation: sqlite
scan_types:
  - daily_discovery_scan
  - intraday_promotion_scan
bar_clock_policy: utc_closed_bar_only
```

## Persistence foundation
SQLite is the persistence foundation for the Independence-Release operating model. The runtime layer uses SQLite for infrastructure metadata first; business tables are introduced only when later tickets define their fields canonically.

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

## Daily Discovery Scan (Gesamtkonzept §10, steps 1–14)
1. Start the daily discovery run for the closed daily context.
2. Resolve the eligible universe for the run.
3. Load required market and history inputs for that universe.
4. Prepare target-architecture feature inputs from the closed daily context.
5. Evaluate the relevant structural/axis/phase prerequisites that are available at bootstrap level only as module boundaries.
6. Build or update candidate state for the daily discovery pass.
7. Apply the target-architecture entry qualification boundary for daily discovery candidates.
8. Produce decision-oriented candidate classifications for the daily pass.
9. Persist the daily run state to the SQLite-backed target architecture.
10. Write report artifacts into the canonical reports structure.
11. Write snapshot/history artifacts into the canonical snapshot structure.
12. Export evaluation-facing artifacts where required by the target directory model.
13. Record run metadata and operational diagnostics.
14. Close the daily discovery run as a deterministic, closed-bar-only cycle.

## Intraday Promotion Scan (Gesamtkonzept §10, steps 1–7)
1. Start the intraday promotion run for the closed intraday context.
2. Load the previously discovered candidate universe relevant for intraday review.
3. Refresh required intraday inputs using the target data boundary.
4. Re-evaluate promotion-relevant structure, phase, and state boundaries.
5. Update decision bucketing for candidates eligible for promotion or reclassification.
6. Persist and export the intraday promotion results into the target storage/output paths.
7. Close the intraday promotion run as a deterministic, closed-bar-only cycle.

## Operating constraints
- This bootstrap does not introduce live trading or automated order execution.
- Runtime logic for phase/state/entry remains deferred even though the operating model reserves those stages.
- All future implementations must preserve the documented separation between daily discovery and intraday promotion scans.


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
