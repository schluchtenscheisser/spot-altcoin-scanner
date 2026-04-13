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
