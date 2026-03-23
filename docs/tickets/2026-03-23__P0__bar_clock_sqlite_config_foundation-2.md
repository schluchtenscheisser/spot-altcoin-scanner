# Title
[P0] Implement Independence-Release bar clock, SQLite foundation, and config scaffold

## Context / Source
This ticket is a foundational implementation ticket for the Independence-Release architecture.

The new architecture requires an early, deterministic foundation for:

- canonical time handling for daily and 4h bars,
- persistent state/cycle/cache metadata storage,
- structured configuration scaffolding for the new architecture.

The planning process established that `bar_clock.py` is not a helper but core infrastructure, because `daily_bar_id`, `intraday_bar_id`, 4h-bar deltas, and canonical `bars_since_*` semantics depend on it. SQLite was chosen as the persistence foundation for symbol state, cycle state, cache metadata, and run metadata. The Independence-Release config needs explicit top-level sections so later tickets do not grow ad hoc config shape.

**Gesamtkonzept reference:** This ticket corresponds to Gesamtkonzept §19, Ticket 1 ("bar_clock + sqlite + config foundation").

`depends_on: []`

This ticket is independent of the bootstrap ticket (Gesamtkonzept §19, Ticket 2). If the required directories (`scanner/data/`, `scanner/storage/`) do not yet exist, this ticket creates them.

## Goal
After this ticket is completed, the repository must provide:

1. a deterministic `bar_clock` module with explicit UTC semantics and concrete boundary behavior,
2. a SQLite infrastructure layer (open/create/migrate) for Independence-Release storage,
3. a config scaffold for Independence-Release sections with explicit merge semantics,
4. tests for bar-clock edge cases and storage bootstrap with concrete input/output pairs,
5. canonical docs that define these foundations clearly for later tickets.

## Scope
Allowed changes for this ticket:

- `scanner/data/bar_clock.py`
- `scanner/data/__init__.py` if needed
- `scanner/data/` directory creation if it does not yet exist
- `scanner/storage/sqlite.py`
- `scanner/storage/schema.py`
- `scanner/storage/__init__.py` if needed
- `scanner/storage/` directory creation if it does not yet exist
- `scanner/config.py` or the repo's central config module(s)
- `tests/**` for new bar-clock / SQLite / config-scaffold tests
- `docs/canonical/**` where these foundations are defined
- `docs/tickets/**` only as required by `WORKFLOW_CODEX.md`

## Out of Scope
- Implementing OHLCV fetching
- Implementing cache refresh logic beyond what is required to define storage infrastructure
- Implementing tier1/tier2 axes
- Implementing phase logic
- Implementing invalidation, cycle transitions, state machine, or pattern logic
- Implementing runners
- Implementing report generation
- Implementing history Parquet storage
- Implementing execution logic
- Defining business-level SQLite tables (symbol_state, cycle_state, cache_meta) — these belong to the tickets that define the business logic requiring them
- Implementing `repositories.py` business logic

## Canonical References (important)
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/tickets/_TEMPLATE.md`
- Gesamtkonzept §11 (Zeitlogik und Bar-Clock)
- Abschnitt 6, §12.2 (kanonische Bar-Einheit, delta)

**Note:** Since this ticket has `depends_on: []`, the following canonical docs may not yet exist when this ticket runs. If they do not exist, this ticket must create them with at least the content required by this ticket. If they already exist (e.g., from the bootstrap ticket), this ticket updates them.
- `docs/canonical/ARCHITECTURE.md` — add bar_clock and storage module roles
- `docs/canonical/RUNTIME_AND_OPERATIONS.md` — add UTC bar semantics
- `docs/canonical/DATA_MODEL.md` — add SQLite infrastructure role, `run_metadata` schema

This ticket must also update canonical docs where required so that later tickets can rely on:
- UTC bar semantics and boundary behavior
- fixed `daily_bar_id` and `intraday_bar_id` definitions
- `delta_closed_bars` computation
- SQLite infrastructure role and scope
- Independence-Release config sections and merge semantics

## Proposed change (high-level)

### Before
- The repo may contain legacy time handling and legacy config shape.
- There is no canonical Independence-Release `bar_clock` foundation.
- There is no new SQLite storage infrastructure for Independence-Release.
- Later tickets would otherwise be forced to guess bar semantics and storage layout.

### After
- A dedicated Independence-Release `bar_clock` exists with deterministic UTC logic and explicit boundary behavior.
- SQLite infrastructure code exists for the new architecture (open/create/WAL mode/migration).
- A `run_metadata` table exists for tracking scanner runs.
- Independence-Release config sections exist in scaffold form with documented merge semantics.
- Canonical docs describe these foundations explicitly.

### Edge cases
- Daily/4h boundary handling at exact close times must be deterministic (see Fixed Bar Semantics below).
- Invalid, `None`, `NaN`, and `inf` timestamps must raise explicit exceptions (see Guardrails below).
- Storage initialization must be idempotent.
- Config scaffold must not silently drift from later intended top-level Independence-Release sections.

### Backward compatibility impact
This ticket introduces new Independence-Release foundations. It must not break reusable legacy infrastructure unnecessarily, but legacy runtime behavior is not the target of this repo.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Workflow priority:** Follow `docs/canonical/WORKFLOW_CODEX.md` strictly for ticket lifecycle and docs-first behavior.
- **Canonical docs first:** Because this ticket defines time semantics and storage semantics, update canonical docs before or alongside code in the same PR.
- **UTC is mandatory:** Do not introduce local-time or implicit timezone behavior.
- **Closed-bar semantics only:** No lookahead, no partial current-bar semantics.
- **Determinism:** All boundary functions must be deterministic for identical timestamps. At identical input and identical config, selection, ordering, state, and reasons are identical.
- **SQLite role only:** This ticket provides the SQLite infrastructure and a `run_metadata` table, not business-level repositories or business-level tables.
- **No raw-dict default drift:** If a config abstraction already exists, extend it consistently instead of inventing parallel config access semantics.
- **Do not implement future logic prematurely:** No fake state machine tables, no guessed business thresholds, no placeholder business rules pretending to be canonical.
- **No auto-doc manual editing:** `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` remain read-only.

### Config semantics (Pflicht)
> Partial overrides in `independence_release` config blocks are merged field-by-field with central defaults; missing sub-keys are not treated as invalid.

> Missing keys fall back to the defined defaults. Invalid values (wrong type, out of range) produce a clear error with the key name and the invalid value in the error message.

### Numeric robustness (Pflicht)
> Non-finite numeric values (`NaN`, `inf`, `-inf`) and `None` are not valid timestamps and must not be silently accepted. Bar clock functions must raise `TypeError` for `None` and `ValueError` for non-finite float values.

### Determinism (Pflicht)
> At identical input and identical config, all bar clock outputs are identical.

> If the current authoritative reference, Canonical, and existing code conflict, the authoritative reference wins. If additional clarification is needed, extend the ticket or ask the user rather than interpret.

> Existing repo paths/helpers may be reused as long as they do not conflict with Canonical; do not introduce a second source of truth.

## Implementation Notes

### Fixed Bar Semantics (verbindlich, nicht Vorschlag)

These semantics are canonical and must be implemented exactly as specified.

#### Daily bar schedule
- **Exchange:** MEXC
- **Daily close:** 00:00:00.000 UTC
- **Bar for date D** opens at D 00:00 UTC and closes at (D+1) 00:00 UTC.
- **Boundary rule:** At exact close time, the bar that closes at that time **is treated as closed**.

#### `daily_bar_id` definition
`daily_bar_id(t)` returns the `YYYY-MM-DD` string of the **most recently closed** daily bar.

The bar that represents trading on date D opens at D 00:00 UTC and closes at (D+1) 00:00 UTC. The `daily_bar_id` is the date D of the closed bar, not the close timestamp. At time t, we find the most recent 00:00 UTC boundary ≤ t. The bar that closed at that boundary has date = (boundary_date − 1 day).

Concrete examples:

| Input timestamp (UTC) | Most recent daily close ≤ t | Closed bar date (= close − 1 day) | `daily_bar_id` |
|---|---|---|---|
| `2026-03-24T00:00:00.000Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `"2026-03-23"` |
| `2026-03-24T00:00:00.001Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `"2026-03-23"` |
| `2026-03-24T12:00:00.000Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `"2026-03-23"` |
| `2026-03-23T23:59:59.999Z` | `2026-03-23T00:00:00Z` | `2026-03-22` | `"2026-03-22"` |
| `2026-03-24T23:59:59.999Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `"2026-03-23"` |

#### 4h bar schedule
- **Close times:** 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC (6 bars per day)
- **Boundary rule:** At exact close time, the bar that closes at that time **is treated as closed**.

#### `intraday_bar_id` definition
`intraday_bar_id(t)` returns the `close_time_utc_ms` (integer, milliseconds since epoch) of the **most recently closed** 4h bar.

| Input timestamp (UTC) | Most recent 4h close ≤ t | `intraday_bar_id` (ms) |
|---|---|---|
| `2026-03-24T04:00:00.000Z` | `2026-03-24T04:00:00Z` | `1774324800000` |
| `2026-03-24T04:00:00.001Z` | `2026-03-24T04:00:00Z` | `1774324800000` |
| `2026-03-24T03:59:59.999Z` | `2026-03-24T00:00:00Z` | `1774310400000` |
| `2026-03-24T08:30:00.000Z` | `2026-03-24T08:00:00Z` | `1774339200000` |

#### `delta_closed_bars` computation (Pflicht)
The bar clock must provide a function to compute the number of newly closed 4h bars between two timestamps.

`delta_closed_4h_bars(t_previous, t_current)` returns the count of 4h close boundaries in the half-open interval `(t_previous, t_current]`.

| `t_previous` (UTC) | `t_current` (UTC) | Result | Explanation |
|---|---|---|---|
| `2026-03-24T00:00:00Z` | `2026-03-24T04:00:00Z` | `1` | One 4h boundary (04:00) in (00:00, 04:00] |
| `2026-03-24T00:00:00Z` | `2026-03-24T08:00:00Z` | `2` | Two boundaries (04:00, 08:00) |
| `2026-03-24T00:00:01Z` | `2026-03-24T04:00:00Z` | `1` | 00:00 is excluded (half-open) |
| `2026-03-24T04:00:00Z` | `2026-03-24T04:00:00Z` | `0` | Same time, empty interval |
| `2026-03-24T00:00:00Z` | `2026-03-25T00:00:00Z` | `6` | Full day = 6 bars |

Additionally, a constant `DAILY_SCAN_DELTA_BARS = 6` must be exposed as the canonical daily-to-4h mapping (Abschnitt 6, §12.2).

#### Invalid input handling
- `None` → raise `TypeError` with descriptive message
- `float('nan')`, `float('inf')`, `float('-inf')` → raise `ValueError` with descriptive message
- Non-numeric / non-datetime types → raise `TypeError` with descriptive message

### Required SQLite infrastructure

This ticket provides **infrastructure only**, not business-level tables.

#### Infrastructure scope
- `scanner/storage/sqlite.py`: open/create database, enable WAL mode, provide connection management
- `scanner/storage/schema.py`: schema version tracking and idempotent migration framework

#### `run_metadata` table
**Technical foundation decision:** The Gesamtkonzept (§14) authorizes SQLite for run metadata storage, and Abschnitt 6 defines daily/intraday scan modes and bar semantics. The specific `run_metadata` table schema below is a technical concretization derived from these requirements, not a verbatim extraction from the fachliche Spezifikation.

This ticket creates exactly one table:

```sql
CREATE TABLE IF NOT EXISTS run_metadata (
    run_id          TEXT PRIMARY KEY,
    scan_mode       TEXT NOT NULL,       -- 'daily_discovery' | 'intraday_promotion'
    started_at_utc  TEXT NOT NULL,       -- ISO 8601
    finished_at_utc TEXT,                -- ISO 8601, NULL while running
    daily_bar_id    TEXT NOT NULL,       -- YYYY-MM-DD
    intraday_bar_id INTEGER,            -- close_time_utc_ms, NULL for daily-only
    schema_version  INTEGER NOT NULL,
    status          TEXT NOT NULL        -- 'running' | 'completed' | 'failed'
);
```

- `finished_at_utc` is nullable: `NULL` means the run is still in progress.
- `intraday_bar_id` is nullable: `NULL` for daily discovery scans that do not track intraday bar context.
- `status` is an enum with exactly three values: `running`, `completed`, `failed`.
- `scan_mode` is an enum with exactly two values: `daily_discovery`, `intraday_promotion`.

#### Explicitly out of scope for SQLite
Business tables for `symbol_state`, `cycle_state`, `cache_meta` are **not** created in this ticket. They require business field definitions from later tickets (Abschnitt 6 §15 fields will be defined when the state machine ticket implements them).

#### Idempotency
- `CREATE TABLE IF NOT EXISTS` for all tables
- Schema version tracking so later tickets can add migrations
- Running the bootstrap twice produces no errors and no duplicate structures

### Required config scaffold (verbindlich, nicht Vorschlag)

The following top-level structure is the **mandatory** Independence-Release config namespace. It must exist after this ticket.

```yaml
independence_release:
  runtime: {}
  bar_clock: {}
  universe: {}
  market_data_budget: {}
  phase: {}
  state: {}
  invalidation: {}
  entry: {}
  execution: {}
  reports: {}
  snapshots: {}
  retention: {}
```

#### Config merge semantics
> Partial overrides in `independence_release` sub-blocks are merged field-by-field with central defaults. Missing sub-keys are not treated as invalid. Invalid values (wrong type, out of range) produce a clear `ValueError` that includes the key name and the invalid value.

This merge-with-defaults semantics applies to all sub-blocks uniformly.

#### Interaction with existing config
If the repo already has a config abstraction (e.g., `ScannerConfig`), extend it with the `independence_release` namespace. Do not create a parallel config loading mechanism.

### Canonical docs to update
At minimum, update or create the relevant sections in:
- `docs/canonical/ARCHITECTURE.md` — add bar_clock module role
- `docs/canonical/RUNTIME_AND_OPERATIONS.md` — add UTC bar semantics
- `docs/canonical/DATA_MODEL.md` — add SQLite infrastructure role, `run_metadata` schema, schema version tracking

Document:
- UTC bar semantics with the concrete boundary examples from this ticket
- fixed `daily_bar_id` and `intraday_bar_id` with the tables from this ticket
- `delta_closed_4h_bars` semantics
- `DAILY_SCAN_DELTA_BARS = 6`
- SQLite as the persistence infrastructure (not business implementation)
- `run_metadata` table schema
- config scaffold structure and merge semantics

## Acceptance Criteria (deterministic)

1) `scanner/data/bar_clock.py` exists and exposes deterministic UTC-based helpers for:
   - `daily_bar_id(t)` → `str` (YYYY-MM-DD)
   - `intraday_bar_id(t)` → `int` (close_time_utc_ms)
   - `delta_closed_4h_bars(t_previous, t_current)` → `int`
   - constant `DAILY_SCAN_DELTA_BARS = 6`

2) `daily_bar_id` produces the exact outputs from the table in "Fixed Bar Semantics" for all 5 example timestamps.

3) `intraday_bar_id` produces the exact outputs from the table in "Fixed Bar Semantics" for all 4 example timestamps.

4) `delta_closed_4h_bars` produces the exact outputs from the table in "Fixed Bar Semantics" for all 5 example input pairs.

5) The bar clock does not use open/incomplete current bars and does not depend on local timezone behavior.

6) Bar clock functions raise `TypeError` for `None` input and `ValueError` for `NaN`/`inf`/`-inf` input.

7) Tests cover at minimum (with concrete input/output assertions):
   - all `daily_bar_id` examples from AC#2
   - all `intraday_bar_id` examples from AC#3
   - all `delta_closed_4h_bars` examples from AC#4
   - deterministic repeated evaluation: `daily_bar_id(t) == daily_bar_id(t)` for same t
   - `TypeError` for `daily_bar_id(None)`
   - `ValueError` for `daily_bar_id(float('nan'))`
   - `ValueError` for `intraday_bar_id(float('inf'))`
   - `TypeError` for `delta_closed_4h_bars(None, some_valid_ts)`

8) `scanner/storage/sqlite.py` exists and provides idempotent SQLite initialization with WAL mode for Independence-Release.

9) `scanner/storage/schema.py` exists and defines a schema version tracking mechanism and the `run_metadata` table exactly as specified in this ticket.

10) SQLite bootstrap can be run repeatedly without schema corruption, duplicate-creation failure, or errors. Specifically: calling the initialization function twice in sequence produces no exceptions and leaves the database in a valid state.

11) The `run_metadata` table matches the schema in this ticket:
    - `finished_at_utc` is nullable
    - `intraday_bar_id` is nullable
    - `status` accepts exactly `running`, `completed`, `failed`
    - `scan_mode` accepts exactly `daily_discovery`, `intraday_promotion`

12) The config scaffold contains the mandatory `independence_release` namespace with all 12 sub-blocks listed in this ticket. The sub-blocks exist as empty dicts/sections that later tickets can extend.

13) Missing config keys in the `independence_release` namespace fall back to defaults (empty dict for sub-blocks). Invalid values produce a clear `ValueError` including key name and invalid value.

14) Canonical docs are created or updated (see Canonical References note) to describe:
    - UTC bar semantics with concrete boundary examples
    - `daily_bar_id` definition and examples
    - `intraday_bar_id` definition and examples
    - `delta_closed_4h_bars` definition and examples
    - `DAILY_SCAN_DELTA_BARS = 6`
    - SQLite infrastructure role (not business implementation)
    - `run_metadata` table schema
    - config scaffold structure and merge semantics

15) The ticket does **not** implement:
    - OHLCV fetch logic
    - cache policy logic
    - axes
    - phase
    - invalidation/state machine
    - runners
    - output/report logic
    - business-level SQLite tables (`symbol_state`, `cycle_state`, `cache_meta`)

16) The ticket is archived in the same PR according to `docs/canonical/WORKFLOW_CODEX.md`.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ (AC: #12, #13 ; Test: config scaffold with missing `independence_release` key → empty defaults apply; config scaffold with missing sub-key → no error)
- **Config Invalid Value Handling:** ✅ (AC: #13 ; Test: config with `independence_release.bar_clock` set to a non-dict value → `ValueError` raised with key name)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #11 ; `finished_at_utc` and `intraday_bar_id` in `run_metadata` are nullable; `NULL` is not coerced to empty string or 0)
- **Not-evaluated vs failed getrennt:** ✅ (N/A – this ticket does not implement fetch/evaluation state)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (AC: #10 ; SQLite bootstrap is idempotent and does not leave partial schema on failure)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A – no filename-derived runtime IDs beyond deterministic bar IDs; `run_id` format is deferred to the runner ticket)
- **Deterministische Sortierung/Tie-breaker:** ✅ (AC: #2, #3, #4, #7 ; deterministic boundary behavior verified by concrete examples)

## Tests (required if logic changes)

### Unit
Add tests with concrete assertions for:

#### bar_clock.daily_bar_id
```
daily_bar_id("2026-03-24T00:00:00.000Z") == "2026-03-23"
daily_bar_id("2026-03-24T00:00:00.001Z") == "2026-03-23"
daily_bar_id("2026-03-24T12:00:00.000Z") == "2026-03-23"
daily_bar_id("2026-03-23T23:59:59.999Z") == "2026-03-22"
daily_bar_id("2026-03-24T23:59:59.999Z") == "2026-03-23"
```

#### bar_clock.intraday_bar_id
```
intraday_bar_id("2026-03-24T04:00:00.000Z") == 1774324800000
intraday_bar_id("2026-03-24T04:00:00.001Z") == 1774324800000
intraday_bar_id("2026-03-24T03:59:59.999Z") == 1774310400000
intraday_bar_id("2026-03-24T08:30:00.000Z") == 1774339200000
```

#### bar_clock.delta_closed_4h_bars
```
delta_closed_4h_bars("2026-03-24T00:00:00Z", "2026-03-24T04:00:00Z") == 1
delta_closed_4h_bars("2026-03-24T00:00:00Z", "2026-03-24T08:00:00Z") == 2
delta_closed_4h_bars("2026-03-24T00:00:01Z", "2026-03-24T04:00:00Z") == 1
delta_closed_4h_bars("2026-03-24T04:00:00Z", "2026-03-24T04:00:00Z") == 0
delta_closed_4h_bars("2026-03-24T00:00:00Z", "2026-03-25T00:00:00Z") == 6
```

#### bar_clock.DAILY_SCAN_DELTA_BARS
```
DAILY_SCAN_DELTA_BARS == 6
```

#### bar_clock invalid input handling
```
daily_bar_id(None) → TypeError
daily_bar_id(float('nan')) → ValueError
intraday_bar_id(float('inf')) → ValueError
intraday_bar_id(float('-inf')) → ValueError
delta_closed_4h_bars(None, valid_ts) → TypeError
delta_closed_4h_bars(valid_ts, float('nan')) → ValueError
```

#### bar_clock determinism
```
daily_bar_id(t) == daily_bar_id(t)  # same t, called twice
intraday_bar_id(t) == intraday_bar_id(t)  # same t, called twice
```

#### SQLite bootstrap idempotency
```
init_db(path) → success
init_db(path) → success (no error, same schema)
```

#### SQLite run_metadata nullable fields
```
INSERT run with finished_at_utc=NULL → success, SELECT returns NULL (not empty string)
INSERT run with intraday_bar_id=NULL → success, SELECT returns NULL (not 0)
```

#### Config scaffold
```
load config with no independence_release key → defaults apply, no error
load config with independence_release.bar_clock = "invalid" → ValueError mentioning key name
load config with independence_release.bar_clock = {} → merges with defaults, no error
```

### Integration
- If the repo already has a suitable pattern, add a lightweight integration test that SQLite schema initializes successfully end-to-end.

### Golden fixture / verification
- `docs/canonical/VERIFICATION_FOR_AI.md` update is **not required** unless the repo already expects it for infrastructure behavior.

## Constraints / Invariants (must not change)

- [ ] UTC-only semantics, no local timezone
- [ ] Closed-candle / closed-bar only
- [ ] No lookahead
- [ ] `daily_bar_id` format is exactly `YYYY-MM-DD`
- [ ] `intraday_bar_id` is `close_time_utc_ms` (integer)
- [ ] Daily close at 00:00:00.000 UTC
- [ ] 4h closes at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
- [ ] At exact close time, the bar is treated as closed (boundary inclusive)
- [ ] `DAILY_SCAN_DELTA_BARS = 6`
- [ ] SQLite is infrastructure only, not fake-full business implementation
- [ ] `run_metadata` is the only table created in this ticket
- [ ] Independence-Release config scaffold uses merge semantics for partial overrides
- [ ] `None`, `NaN`, `inf`, `-inf` raise exceptions in bar clock functions
- [ ] No manual edits to `docs/code_map.md`
- [ ] No manual edits to `docs/GPT_SNAPSHOT.md`
- [ ] Ticket is archived in the same PR per workflow

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/`
- [ ] Added/updated relevant tests per concrete test specifications
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata (optional)
```yaml
created_utc: "2026-03-23T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: []
gesamtkonzept_ref: "§19 Ticket 1"
related_issues: []
```
