> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Implement OHLCV fetch, cache policy, and transitional SQLite OHLCV persistence for 1d and 4h

## Context / Source

This ticket implements **Ticket 4** from the Independence-Release consolidated concept: `ohlcv fetch + cache policy`.

**Gesamtkonzept reference:** Gesamtkonzept §19, Ticket 4.

`depends_on: [1, 3]` — requires:
- Ticket 1 (`bar_clock + sqlite + config foundation`)
- Ticket 3 (`eligibility + market data budget + pre_4h_candidate_filter`)

This `depends_on` is a **ticket-sequencing dependency**, not a runtime requirement that Ticket 4 directly read or reinterpret Ticket-3 persistence fields. Ticket 4 exposes symbol+timeframe OHLCV primitives; later runner tickets decide when to call them.

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, or older ticket assumptions conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Important framing for this ticket

This ticket is an **implementation ticket for OHLCV fetch + cache + interim persistence**, not a runner ticket and not a long-term history-storage ticket.

Therefore:

- this ticket defines how closed 1d and 4h bars are fetched, validated, cached, and stored **now**
- this ticket does **not** define the final long-term history-storage end-state beyond its own scope
- this ticket does **not** define run orchestration over Ticket 3 outputs; it defines symbol+timeframe primitives that later runner tickets will call
- this ticket uses SQLite as the canonical OHLCV persistence layer **for this ticket’s implementation scope only**

### Transitional storage note (authoritative wording for this ticket)

This ticket uses SQLite for `ohlcv_bars` as a **transitional implementation only**, acknowledging a known deviation from Gesamtkonzept §14.3 and Festlegung 1, which define Parquet under the historical OHLCV storage path as the authoritative long-term storage layer for bulk OHLCV timeseries.

Ticket 14 **will** complete the migration to that canonical long-term target. Downstream tickets that read Ticket-4 SQLite OHLCV persistence must not assume SQLite OHLCV storage is permanent.

### Supplemental working context

The following document is **supplemental working context**, not primary fachliche authority:

- `v21_addendum_for_future_tickets_and_new_chats.md`

It may be used as architecture guidance where it does not conflict with the authoritative source set.

## Goal

After this ticket is completed, the repo must be able to:

- decide deterministically, for a given `(symbol, timeframe, now)`, whether the existing OHLCV cache is reusable or a fetch is required
- fetch closed MEXC spot OHLCV for `1d` and `4h` only
- reject invalid, partial, future, or grid-misaligned bars deterministically
- persist valid closed bars and cache metadata atomically in SQLite
- expose deterministic read access to recent closed bars for downstream tickets (features, axes, phase, state)
- preserve missing-bar semantics exactly as absence, without interpolation, reconstruction, or synthetic fill
- fail loudly on invalid caller inputs and on storage conflicts, while treating exchange-returned invalid bars as deterministic data-quality rejects
- document the transitional SQLite OHLCV persistence decision and its later migration successor ticket

## Scope

Allowed change surface:

- `scanner/data/ohlcv_fetch.py` (new)
- `scanner/data/cache_policy.py` (new)
- `scanner/data/__init__.py` if needed
- `scanner/data/bar_clock.py` — only minimal helper additions if strictly required for reuse of canonical close-boundary logic; no semantic changes
- `scanner/storage/schema.py` — add `ohlcv_bars` and `ohlcv_cache_meta`
- `scanner/storage/repositories.py` — add OHLCV bar and cache-meta repositories / methods
- `scanner/clients/mexc_client.py` — add or extend read-only klines method(s) if strictly required; no refactor of unrelated methods
- `scanner/config.py` or central config accessor — add config keys and merge/validation rules
- `tests/**` — add tests specified below
- `docs/canonical/**` — update docs listed below

## Out of Scope

This ticket must not:

- implement runner orchestration over a whole daily or intraday campaign
- implement feature derivation / raw-field computation
- implement Tier-1 or Tier-2 axes
- implement phase interpretation
- implement invalidation, cycle logic, or state machine logic
- implement entry patterns
- implement decision buckets / ranking
- implement execution logic or orderbook fetch
- implement long-term Parquet history storage or snapshot lifecycle
- introduce dual-write to SQLite and Parquet
- introduce a generic storage abstraction layer for OHLCV
- interpolate, reconstruct, or impute missing bars
- alter Ticket 1 `run_metadata`
- alter Ticket 3 `symbol_run_decisions`
- introduce new state / phase / bucket enums
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

## Canonical References (important)

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §11, §12, §14, §18, §19 Ticket 4, and Festlegung 1 for long-term OHLCV history storage direction
- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` — especially cache / freshness / persistence / failure-handling sections and 4h-bar canonical unit semantics
- Ticket 1 — canonical time semantics (`daily_bar_id`, `intraday_bar_id`, UTC, closed-bar boundaries)
- the accepted timestamp input contract from the Ticket-2-repair workstream (numeric timestamps in ms, aware datetimes only)

Supplemental working context:

- `v21_addendum_for_future_tickets_and_new_chats.md` — use only as architecture guidance where it does not conflict with primary authority

Repo process references:

- `docs/tickets/_TEMPLATE.md`
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- `docs/canonical/WORKFLOW_CODEX.md`

### Canonical docs to update

- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/open_questions.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Proposed change (high-level)

### Before

- Upstream selection logic exists, but there is no canonical OHLCV fetch/cache contract for 1d and 4h.
- There is no canonical SQLite OHLCV persistence schema for downstream tickets to read from.
- There is no deterministic definition of fresh vs stale vs missing vs broken cache state.
- There is no canonical contract for rejecting partial or invalid exchange-returned bars.

### After

- `cache_policy.py` answers deterministic freshness and fetch-decision questions for one `(symbol, timeframe, now)`.
- `ohlcv_fetch.py` fetches, validates, filters, and persists closed bars for one `(symbol, timeframe, now)`.
- Valid bars are stored in SQLite in a canonical `ohlcv_bars` table.
- Cache metadata is stored in SQLite in a canonical `ohlcv_cache_meta` table.
- Missing bars remain absent; downstream consumers see gaps as gaps.
- Caller-input errors fail loudly; exchange-returned bad bars are rejected deterministically and surfaced in diagnostics.
- Downstream tickets can read recent closed bars from a stable repository contract.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Docs in same PR:** Update all listed canonical docs in the same PR as the code.
- **Transitional SQLite only for this ticket’s scope:** Use SQLite as the canonical OHLCV persistence layer in this ticket. Do not introduce Parquet writes or a second storage authority here.
- **Closed-bar-only:** Never persist a bar whose close time is after the canonical most-recently-closed bar for the requested timeframe and `now`.
- **Reuse bar-clock semantics:** Time boundary math must reuse Ticket-1 bar-clock semantics. Do not re-derive alternate daily/4h closing rules in local ad-hoc arithmetic if a reusable bar_clock helper exists or can be minimally added.
- **No silent caller fallbacks:** Invalid public-function inputs raise immediately. No best-effort reinterpretation.
- **Data-quality rejects are bar-level, not caller-level:** Exchange-returned invalid/future/misaligned bars are rejected deterministically at bar level and counted; they do not become silently persisted.
- **Atomic persist:** Bar persistence plus cache-meta update must be atomic per `(symbol, timeframe)`.
- **No duplicate-truth bootstrap states:** Missing cache is represented by absence of a row in `ohlcv_cache_meta`. Do not add a competing `never_attempted` state.
- **Idempotent and conflict-strict persistence:** Existing identical bars are no-op; existing same-PK bars with differing values are a hard conflict and must raise.
- **Nullability preserved:** Nullable SQL fields must round-trip to Python `None`, not `0` or `""`.
- **Closed enums:** `timeframe`, `cache_status`, `fetch_decision`, and `last_fetch_status` are closed sets defined here.
- **No backfill / no interpolation:** Missing bars remain absent. No reconstruction from future data.
- **No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.**
- **One ticket = one PR.**

## Input contract

Public functions in `ohlcv_fetch.py` and `cache_policy.py` must obey this exact contract:

### `symbol`
- required type: `str`
- required form: non-empty uppercase MEXC spot symbol, e.g. `"FOOUSDT"`
- empty string, whitespace-only string, non-string, or `None` → `TypeError` or `ValueError`
- function may normalize lowercase input to uppercase **only if** the normalized string is otherwise valid; whitespace-wrapped strings must raise, not silently trim

### `timeframe`
- closed enum: `"1d"` or `"4h"`
- any other value → `ValueError`

### `now`
- accepted:
  - Unix epoch milliseconds as finite numeric value
  - timezone-aware `datetime`
- rejected:
  - naive `datetime`
  - `None`
  - `NaN`
  - `inf`
  - `-inf`

Numeric inputs are milliseconds. No seconds heuristic is allowed.

### `lookback_bars` override
For public functions that accept `lookback_bars`:

- `None` means: use the configured default for the requested timeframe
- non-`None` requires:
  - integer type
  - `> 0`
  - `>= min_lookback_bars_<tf>`
  - `<= 1000`
- invalid values raise `ValueError` naming the argument and value

Override validation follows the same bounds logic as config validation. There is no second weaker override-only rule set.

## Closed-bar and bar-grid semantics

This ticket must use one canonical concept:

- `most_recent_closed_bar_close_time_utc_ms(timeframe, now)`

This may be an existing Ticket-1 bar-clock function or a minimal new helper added to `scanner/data/bar_clock.py`, but the semantics must be canonical and shared.

Rules:

- For `timeframe = "4h"`, the canonical close grid is `00:00`, `04:00`, `08:00`, `12:00`, `16:00`, `20:00` UTC.
- For `timeframe = "1d"`, the canonical close grid is `00:00` UTC for the closed daily bar.
- Only bars with `close_time_utc_ms <= most_recent_closed_bar_close_time_utc_ms(timeframe, now)` may be persisted.
- Any exchange-returned bar with `close_time_utc_ms` after that cutoff is a **future / partial bar** and must be rejected from persistence and counted in diagnostics.

Grid alignment rules:

- `4h` bars must close exactly on the canonical 4h UTC grid.
- `1d` bars must close exactly on the canonical daily UTC grid.

Bars failing these rules are rejected and counted as misaligned.

## Fetch decision semantics (canonical)

For each `(symbol, timeframe, now)`:

### `cache_status`

Closed enum:

- `"fresh"`
- `"stale"`
- `"missing"`
- `"broken"`

Definitions:

- `missing` — no row exists in `ohlcv_cache_meta` for `(symbol, timeframe)`
- `fresh` — row exists, `last_fetch_status = "ok"`, `cached_close_time_utc_ms` equals `most_recent_closed_bar_close_time_utc_ms(timeframe, now)`, and the corresponding bar exists in `ohlcv_bars`
- `stale` — row exists, `last_fetch_status = "ok"`, `cached_close_time_utc_ms` is earlier than the canonical current closed cutoff, and the corresponding cached bar exists in `ohlcv_bars`
- `broken` — row exists, but one of the following holds:
  - `last_fetch_status != "ok"` and no newer successful cache state exists
  - `cached_close_time_utc_ms` is `NULL`
  - `cached_close_time_utc_ms` is inconsistent with `ohlcv_bars` (for example meta claims a cached close time but that bar row is absent)

### `bars_missing_since_cached`

Returns:

- integer count of missing closed bars between `cached_close_time_utc_ms` and `most_recent_closed_bar_close_time_utc_ms(timeframe, now)` for stale caches
- `0` if `cache_status = "fresh"`
- `None` if `cache_status in {"missing", "broken"}`

Definition for stale caches:
- count the number of canonical closed bars with close times `> cached_close_time_utc_ms` and `<= current_closed_cutoff`

### `fetch_decision`

Closed enum:

- `"skip"`
- `"fetch_full"`
- `"fetch_incremental"`

Definitions:

- `skip` iff `cache_status = "fresh"`
- `fetch_full` iff `cache_status in {"missing", "broken"}`
- `fetch_incremental` iff `cache_status = "stale"` and `bars_missing_since_cached < cfg.independence_release.ohlcv_fetch.incremental_max_bars`
- `fetch_full` iff `cache_status = "stale"` and `bars_missing_since_cached >= cfg.independence_release.ohlcv_fetch.incremental_max_bars`

## Exact fetch-window semantics

This ticket defines the **logical accepted fetch window**. The client call may overfetch if needed, but post-fetch filtering must enforce these exact windows.

### Full fetch

For `fetch_decision = "fetch_full"`:

- accepted window is the last `lookback_bars_<tf>` canonical closed bars ending at `most_recent_closed_bar_close_time_utc_ms(timeframe, now)`
- only bars in that logical window may reach persistence

### Incremental fetch

For `fetch_decision = "fetch_incremental"`:

- accepted window is all canonical closed bars with:
  - `close_time_utc_ms > cached_close_time_utc_ms`
  - `close_time_utc_ms <= most_recent_closed_bar_close_time_utc_ms(timeframe, now)`
- no older bars outside that window may be newly persisted in incremental mode
- the API request may start at most **one canonical bar earlier** than the logical incremental window start for dedup safety
- zero overlap bars returned is valid
- an overlapped already-cached bar may appear in the exchange response, but it must not count as newly persisted

## Exchange-response mapping contract

`ohlcv_fetch.py` is responsible for mapping the exchange response into the canonical internal `Bar` dataclass.

Canonical `Bar` fields:

- `open_time_utc_ms: int`
- `close_time_utc_ms: int`
- `open: float`
- `high: float`
- `low: float`
- `close: float`
- `base_volume: float`
- `quote_volume: float`

If the client response provides both open and close times, use them.

If the client response provides only open time and interval semantics, derive:

- `close_time_utc_ms = open_time_utc_ms + timeframe_duration_ms`

where:
- `timeframe_duration_ms = 86_400_000` for `1d`
- `timeframe_duration_ms = 14_400_000` for `4h`

Derived close times must still pass closed-bar-only and grid-alignment checks.

### Open/close interval consistency check and MEXC close-time normalization

MEXC spot klines are Binance-compatible in shape and identify klines by open time; Binance-style kline payloads use a close time convention of `open_time + interval_ms - 1`. This means the raw exchange close time may differ by exactly `1 ms` from the canonical bar-close boundary used by Ticket 1 bar-clock semantics.

Normalization rule (applied during exchange-response mapping, before grid-alignment and closed-bar-only checks):

- compute `expected_canonical_close_time_utc_ms = open_time_utc_ms + timeframe_duration_ms`
- if the exchange provides `close_time_utc_ms` and  
  `abs(exchange_close_time_utc_ms - expected_canonical_close_time_utc_ms) <= 1`,  
  then normalize to  
  `canonical_close_time_utc_ms = expected_canonical_close_time_utc_ms`
- if the exchange provides `close_time_utc_ms` and the difference exceeds `1 ms`, the bar is rejected and counted in `invalid_bars_rejected`
- if the exchange does not provide `close_time_utc_ms`, derive  
  `canonical_close_time_utc_ms = expected_canonical_close_time_utc_ms`

The normalized `canonical_close_time_utc_ms` is what is stored, indexed, and used for grid alignment and closed-bar-only checks. The raw exchange close-time value is not persisted.

All numeric OHLCV fields must be finite. Non-finite fields make the bar invalid.

## No-Backfill / gap semantics

If a historical bar is missing:

- no reconstruction from future data
- no interpolation
- no synthetic fill row
- no gap imputation

Absence means absence.

If fetch returns no valid bar for a requested missing range, the gap remains a gap.

## Public module responsibilities

### `scanner/data/cache_policy.py`

Public functions:

- `get_cache_status(symbol: str, timeframe: str, now: int | datetime) -> str`
- `get_fetch_decision(symbol: str, timeframe: str, now: int | datetime) -> str`
- `bars_missing_since_cached(symbol: str, timeframe: str, now: int | datetime) -> int | None`

No run/campaign orchestration helper is introduced in this ticket.

### `scanner/data/ohlcv_fetch.py`

Public functions:

- `fetch_closed_bars(symbol: str, timeframe: str, now: int | datetime, lookback_bars: int | None = None) -> FetchResult`
- `persist_fetch(symbol: str, timeframe: str, fetch_result: FetchResult, now: int | datetime) -> PersistResult`
- `fetch_and_persist(symbol: str, timeframe: str, now: int | datetime, lookback_bars: int | None = None) -> PersistResult`

### Required `fetch_and_persist` call flow

`fetch_and_persist` must execute this exact sequence:

1. Call `get_fetch_decision(symbol, timeframe, now)`.
2. If the decision is `skip`:
   - do not issue any MEXC API call
   - do not write any new bar rows
   - return a `PersistResult` with:
     - `rows_inserted = 0`
     - `rows_noop_identical = 0`
     - `last_fetch_status = "ok"`
     - `last_error_code = None`
     - `cached_close_time_utc_ms` equal to the existing cached meta value if present, otherwise `None`
3. If the decision is `fetch_full` or `fetch_incremental`:
   - call `fetch_closed_bars(...)`
   - then call `persist_fetch(...)`
   - return the resulting `PersistResult`

### `FetchResult`

Minimum required fields:

- `symbol`
- `timeframe`
- `requested_at_utc_ms`
- `canonical_close_cutoff_utc_ms`
- `bars: list[Bar]` — valid bars only, ascending by `close_time_utc_ms`
- `partial_bars_dropped: int`
- `invalid_bars_rejected: int`
- `duplicate_bars_deduplicated: int`
- `misaligned_bars_rejected: int`
- `last_fetch_status: str`
- `last_error_code: str | None`

### `PersistResult`

Minimum required fields:

- `symbol`
- `timeframe`
- `rows_inserted: int`
- `rows_noop_identical: int`
- `cached_close_time_utc_ms: int | None`
- `last_fetch_status: str`
- `last_error_code: str | None`

## SQLite schema additions (authoritative in this ticket)

```sql
CREATE TABLE IF NOT EXISTS ohlcv_bars (
    symbol              TEXT    NOT NULL,
    timeframe           TEXT    NOT NULL,
    open_time_utc_ms    INTEGER NOT NULL,
    close_time_utc_ms   INTEGER NOT NULL,
    open                REAL    NOT NULL,
    high                REAL    NOT NULL,
    low                 REAL    NOT NULL,
    close               REAL    NOT NULL,
    base_volume         REAL    NOT NULL,
    quote_volume        REAL    NOT NULL,
    PRIMARY KEY (symbol, timeframe, close_time_utc_ms),
    CHECK (timeframe IN ('1d', '4h'))
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_bars_symbol_tf_close_desc
    ON ohlcv_bars (symbol, timeframe, close_time_utc_ms DESC);

CREATE TABLE IF NOT EXISTS ohlcv_cache_meta (
    symbol                    TEXT    NOT NULL,
    timeframe                 TEXT    NOT NULL,
    cached_close_time_utc_ms  INTEGER,
    last_fetch_at_utc         TEXT,
    last_fetch_status         TEXT    NOT NULL,
    last_error_code           TEXT,
    PRIMARY KEY (symbol, timeframe),
    CHECK (timeframe IN ('1d', '4h')),
    CHECK (last_fetch_status IN ('ok', 'empty', 'error_transport', 'error_invalid'))
);
```

### Enum closed sets

- `timeframe ∈ {"1d", "4h"}`
- `last_fetch_status ∈ {"ok", "empty", "error_transport", "error_invalid"}`
- `cache_status ∈ {"fresh", "stale", "missing", "broken"}`
- `fetch_decision ∈ {"skip", "fetch_full", "fetch_incremental"}`

### Nullability rules

- `cached_close_time_utc_ms` nullable
- `last_fetch_at_utc` nullable
- `last_error_code` nullable

No `never_attempted` value exists. Absence of a row is the bootstrap missing-cache state.

### Timestamp serialization rule

`last_fetch_at_utc` is stored as ISO 8601 UTC string in the format:

- `YYYY-MM-DDTHH:MM:SS.sssZ`

This must be consistent across all writes by this ticket.

### Reconciliation with Abschnitt-6 cache-bar terminology

The `cached_close_time_utc_ms` field in `ohlcv_cache_meta` is the OHLCV-cache-specific representation of the bar-clock concepts that later tickets may persist elsewhere as `daily_cache_bar_id` and `intraday_cache_bar_id`.

Mapping:

- for `timeframe = "1d"`, `cached_close_time_utc_ms` equals the UTC epoch-ms representation of the closed daily bar identified by `daily_bar_id`
- for `timeframe = "4h"`, `cached_close_time_utc_ms` equals the epoch-ms value of the closed 4h bar identified by `intraday_bar_id`

This ticket does **not** replace or remove the later requirement to persist `daily_cache_bar_id` / `intraday_cache_bar_id` in state-oriented persistence where the authoritative spec requires them. It only defines the OHLCV-cache-specific storage representation for Ticket 4.

## Persistence semantics (authoritative)

### Writing bars

Repository contract:

- `write_bars(symbol, timeframe, bars)` must process bars one by one under one transaction

For each bar PK `(symbol, timeframe, close_time_utc_ms)`:

- if no row exists: insert
- if row exists and all persisted OHLCV/time fields are identical: no-op
- if row exists and any persisted value differs: raise a hard conflict error and roll back the whole transaction

Silent overwrite / replace is forbidden.

Historical OHLCV rows are immutable within normal fetch flow. Any differing same-PK bar is treated as a data-consistency violation, not an update case.

### Updating cache meta

`persist_fetch` must write `fetch_result.last_fetch_status` and `fetch_result.last_error_code` into `ohlcv_cache_meta`.

`PersistResult.last_fetch_status` and `PersistResult.last_error_code` must reflect the values actually persisted into `ohlcv_cache_meta`.

`cached_close_time_utc_ms` may advance only when:

- `fetch_result.last_fetch_status = "ok"`
- and at least one valid bar from the accepted fetch window was newly inserted in this persist operation

On:
- `empty`
- `error_transport`
- `error_invalid`

the existing `cached_close_time_utc_ms` remains unchanged.

### Atomicity

`persist_fetch` must update `ohlcv_bars` and `ohlcv_cache_meta` in the same transaction per `(symbol, timeframe)`.

If any conflict or write failure occurs:

- neither partial bar writes
- nor advanced cache meta
- may remain committed

## Bar-level rejection semantics

### Future / partial bars
A bar whose `close_time_utc_ms` is after the canonical current closed cutoff is rejected and counted in `partial_bars_dropped`.

### Non-finite / invalid bars
A bar with `None`, `NaN`, `inf`, or `-inf` in any required OHLCV field is rejected and counted in `invalid_bars_rejected`.

Bars failing the allowed close-time normalization rule are also rejected and counted in `invalid_bars_rejected`. After normalization, all surviving bars satisfy the canonical interval relation by construction; no separate post-normalization interval check is required.

### Misaligned bars
A bar whose close time does not sit on the canonical 1d or 4h UTC grid is rejected and counted in `misaligned_bars_rejected`.

### Duplicate bars in one response
If multiple bars in the same response share the same `close_time_utc_ms`:

- dedup deterministically
- the **last occurrence in response order** wins
- count each dropped earlier duplicate in `duplicate_bars_deduplicated`

### Whole-fetch result status
- `ok` — at least one valid bar remains after filtering
- `empty` — zero valid bars remain and there was no transport error and no invalid-numeric/invalid-interval rejection
- `error_invalid` — zero valid bars remain and at least one returned bar was rejected for invalid numeric data or invalid interval consistency
- `error_transport` — client call failed due to transport/auth/timeout/network/API failure before producing a usable response

Additional explicit rules:
- if all returned bars are rejected only as future/partial and no valid bars remain, `last_fetch_status = "empty"`
- if all returned bars are rejected only as misaligned and no valid bars remain, `last_fetch_status = "empty"`
- if zero valid bars remain and at least one bar was rejected for invalid numeric data or invalid close-time consistency beyond the allowed `1 ms` normalization tolerance, `last_fetch_status = "error_invalid"`
- if zero valid bars remain and mixed rejects occurred, including at least one invalid-numeric or invalid-close-time-consistency reject, `last_fetch_status = "error_invalid"`

## Config contract

All new keys live under:

- `independence_release.ohlcv_fetch`
- `independence_release.cache_policy`

### `independence_release.ohlcv_fetch`

| Key | Default | Type | Validation |
|---|---:|---|---|
| `lookback_bars_1d` | `250` | int | `120 <= x <= 1000` |
| `lookback_bars_4h` | `250` | int | `120 <= x <= 1000` |
| `incremental_max_bars` | `50` | int | `1 <= x <= 500` |
| `per_call_timeout_s` | `30` | int | `5 <= x <= 300` |
| `max_retries` | `0` | int | `0 <= x <= 3` |
| `min_lookback_bars_1d` | `120` | int | `1 <= x <= lookback_bars_1d` |
| `min_lookback_bars_4h` | `120` | int | `1 <= x <= lookback_bars_4h` |

### `independence_release.cache_policy`

No required user-facing keys in this ticket. The block may exist as an empty reserved namespace for future extension, but this ticket must not rely on any keys inside it.

### Merge semantics

Partial overrides are merged field-by-field with central defaults.

Missing sub-keys are valid and fall back to defaults.

Invalid values (wrong type, out of range, or `lookback_bars_<tf> < min_lookback_bars_<tf>`) must raise `ValueError` naming the key and the invalid value.

## Canonical docs to update

### `docs/canonical/ARCHITECTURE.md`
Add:
- `scanner/data/cache_policy.py`
- `scanner/data/ohlcv_fetch.py`
- transitional SQLite OHLCV persistence role
- Ticket 14 as later migration successor for long-term history storage

### `docs/canonical/DATA_MODEL.md`
Add:
- `ohlcv_bars` schema
- `ohlcv_cache_meta` schema
- PK/index/nullability rules
- closed enum sets
- conflict-strict upsert rule
- the mapping note between `cached_close_time_utc_ms` and later `daily_cache_bar_id` / `intraday_cache_bar_id` terminology

### `docs/canonical/RUNTIME_AND_OPERATIONS.md`
Add:
- `cache_status` decision table
- `fetch_decision` decision table
- closed-bar-only fetch contract
- exact full vs incremental fetch-window semantics
- no-backfill / no-interpolation rule
- bar-level reject semantics
- `fetch_and_persist` call flow

### `docs/canonical/GLOSSARY.md`
Add definitions for:
- `cache_status`
- `fetch_decision`
- `cached_close_time_utc_ms`
- `closed-bar-only`
- `full fetch`
- `incremental fetch`
- `broken cache`

### `docs/canonical/open_questions.md`
Add a follow-up reference that Ticket 14 will define the later migration path for long-term OHLCV history storage beyond this ticket’s transitional SQLite persistence.

### `docs/canonical/VERIFICATION_FOR_AI.md`
Add:
- `cache_status` decision table
- `fetch_decision` decision table
- default config values and min-bounds
- conflict-strict upsert semantics
- full vs incremental accepted-window semantics

## Acceptance Criteria (deterministic)

1. `scanner/data/cache_policy.py` and `scanner/data/ohlcv_fetch.py` exist with exactly the public-function surface defined in this ticket.
2. `ohlcv_bars` and `ohlcv_cache_meta` exist in SQLite with exactly the schema, PK, index, enum, and nullability rules defined in this ticket.
3. Ticket 1 `run_metadata` and Ticket 3 `symbol_run_decisions` are not altered by this ticket.
4. `get_cache_status(symbol, timeframe, now)` returns exactly one of `{"fresh", "stale", "missing", "broken"}` and obeys the definitions in this ticket.
5. `get_fetch_decision(symbol, timeframe, now)` returns exactly one of `{"skip", "fetch_full", "fetch_incremental"}` and obeys the definitions in this ticket.
6. `bars_missing_since_cached(symbol, timeframe, now)` returns `0` for `fresh`, an integer count for `stale`, and `None` for `missing` or `broken`.
7. `fetch_closed_bars` never returns any bar whose `close_time_utc_ms` exceeds `most_recent_closed_bar_close_time_utc_ms(timeframe, now)`.
8. `fetch_closed_bars` rejects and counts future/partial, invalid, duplicate, and misaligned bars exactly as defined in this ticket.
9. `persist_fetch` writes bars and updates cache metadata atomically per `(symbol, timeframe)`.
10. Existing same-PK identical bars are no-op; existing same-PK differing bars raise a hard conflict and roll back the transaction.
11. `cached_close_time_utc_ms` advances only when `fetch_result.last_fetch_status = "ok"` and at least one valid accepted-window bar was newly inserted.
12. No row in `ohlcv_cache_meta` means `cache_status = "missing"`. There is no competing `never_attempted` state.
13. On `cache_status = "fresh"` and `fetch_decision = "skip"`, no MEXC API call is issued for that `(symbol, timeframe)` in that call path.
14. `fetch_and_persist` follows exactly the call flow defined in this ticket.
15. `persist_fetch` persists `fetch_result.last_fetch_status` and `fetch_result.last_error_code` into `ohlcv_cache_meta`, and `PersistResult` reflects the persisted values.
16. `last_fetch_at_utc` is written in the required ISO 8601 UTC format `YYYY-MM-DDTHH:MM:SS.sssZ`.
17. Public functions reject invalid caller inputs exactly per the input contract in this ticket.
18. Config defaults, merge semantics, override validation, and invalid-value failures behave exactly as defined here.
19. Nullable SQL fields round-trip to Python `None`.
20. Deterministic reproduction: identical seeded DB state, identical config, identical `now`, and identical mocked exchange response produce identical `FetchResult`, `PersistResult`, and SQLite table state.
21. Canonical docs listed in this ticket are updated in the same PR.
22. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually edited.
23. The ticket is archived in the same PR per workflow.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅
- **Config Invalid Value Handling:** ✅
- **Nullability / kein bool()-Coercion:** ✅
- **Not-evaluated vs failed / missing vs broken explicit:** ✅
- **Strict Atomizität (0 Partial Writes):** ✅
- **Deterministische Sortierung / Dedup / Conflict Handling:** ✅
- **Numerische Robustheit (`NaN` / `inf` / `-inf` / `None`):** ✅
- **Input Contract explicit:** ✅
- **No backfill / no interpolation:** ✅

## Tests (required)

### Unit — input contract

- `symbol=""` → `ValueError`
- `symbol="   "` → `ValueError`
- `symbol=None` → `TypeError`
- `symbol=123` → `TypeError`
- `symbol="foousdt"` → accepted only as uppercase-normalized `"FOOUSDT"` if normalization rule is implemented consistently
- `timeframe="1h"` → `ValueError`
- `now=None` → `TypeError`
- `now=float("nan")` → `ValueError`
- `now=float("inf")` → `ValueError`
- naive `datetime` → `TypeError` or `ValueError` consistent with the established timestamp contract
- aware `datetime` UTC → accepted
- numeric ms timestamp → accepted
- `lookback_bars=0` override → `ValueError`
- `lookback_bars=100` for `4h` when `min_lookback_bars_4h=120` → `ValueError`

### Unit — canonical close cutoff integration

- `fetch_closed_bars("FOOUSDT", "4h", now=2026-04-14T09:30:00Z)` with a returned bar closing at `12:00Z` → bar rejected as future / partial
- same call with a returned bar closing at `08:00Z` → bar accepted
- exact-boundary test: `now=2026-04-14T08:00:00Z`, bar closing `08:00Z` → accepted
- daily exact-boundary test: bar closing at canonical daily close for current closed daily bar → accepted
- daily bar closing after canonical current closed daily close → rejected

### Unit — grid alignment

- `4h` bar closing at `05:00Z` → rejected as misaligned
- `1d` bar closing at non-daily UTC boundary → rejected as misaligned
- exchange-returned close time exactly 1 ms before the canonical grid boundary with open time on the canonical grid → normalized to the canonical grid boundary and passes grid alignment (standard MEXC/Binance-compatible convention)
- bar with `open_time = 2026-04-14T00:00:01.000Z` for `timeframe="4h"` and exchange close time within the allowed ±1 ms normalization tolerance relative to `open_time + timeframe_duration_ms` → normalized canonical close time remains off-grid and is rejected as misaligned

### Unit — exchange-response mapping

- response includes both open and close times → exchange close time is normalized per the `±1 ms` rule before further checks
- response includes only open time + interval semantics → close time derived correctly
- exchange-returned `close_time_utc_ms = open_time_utc_ms + timeframe_duration_ms - 1` with open time on the canonical grid → normalized to `open_time_utc_ms + timeframe_duration_ms`, then passes normal grid and closed-bar checks
- exchange-returned `open_time_utc_ms` and `close_time_utc_ms` whose difference deviates from `timeframe_duration_ms` by more than `1 ms` → rejected as invalid
- derived close time then passes normal grid and closed-bar checks
- derived close time misaligned → rejected

### Unit — non-finite OHLCV

- bar with `high = NaN` → rejected, counted in `invalid_bars_rejected`
- bar with `close = inf` → rejected
- bar with `quote_volume = -inf` → rejected
- all returned bars invalid → `last_fetch_status = "error_invalid"`

### Unit — future-only and mixed reject status mapping

- all returned bars rejected only as future/partial → `last_fetch_status = "empty"`
- all returned bars rejected only as misaligned → `last_fetch_status = "empty"`
- zero valid bars remain and at least one bar rejected for invalid numeric data → `last_fetch_status = "error_invalid"`
- zero valid bars remain and at least one bar rejected for invalid close-time consistency beyond the allowed `1 ms` tolerance → `last_fetch_status = "error_invalid"`
- zero valid bars remain with mixed future + invalid rejects → `last_fetch_status = "error_invalid"`

### Unit — duplicates

- two bars with same `close_time_utc_ms`, different `close` values in one response → last occurrence wins, earlier one counted as deduplicated

### Unit — cache status

- no meta row → `missing`
- meta row with `last_fetch_status = "ok"`, matching `cached_close_time_utc_ms`, matching bar exists, cutoff equal → `fresh`
- meta row with `last_fetch_status = "ok"`, cached close older than current cutoff, cached bar exists → `stale`
- meta row with `last_fetch_status = "error_transport"` → `broken`
- meta row with `cached_close_time_utc_ms = NULL` → `broken`
- meta row says cached close exists but corresponding bar row missing → `broken`

### Unit — fetch decision

- `fresh` → `skip`
- `missing` → `fetch_full`
- `broken` → `fetch_full`
- `stale` with `bars_missing_since_cached = 3`, threshold 50 → `fetch_incremental`
- `stale` with `bars_missing_since_cached = 50`, threshold 50 → `fetch_full`
- `stale` with `bars_missing_since_cached = 200`, threshold 50 → `fetch_full`

### Unit — exact fetch-window semantics

- full fetch accepts only last `lookback_bars_<tf>` closed bars ending at cutoff
- incremental fetch accepts only bars with `close_time > cached_close_time` and `<= cutoff`
- one overlapped already-cached bar may be requested for dedup safety, but does not count as newly persisted

### Unit — skip path issues no API call

- seed fresh cache state, call `fetch_and_persist`, mocked client call count remains `0`

### Unit — persistence conflict semantics

- insert new bar on absent PK → inserted
- same PK with byte-identical values → no-op
- same PK with differing OHLCV or time field → hard conflict error, rollback

### Unit — atomicity

- simulate failure after bar insert attempt but before cache-meta update → no committed partial writes
- simulate failure during cache-meta update in same transaction → no advanced cache state and no committed partial writes

### Unit — status propagation

- `FetchResult.last_fetch_status = "error_transport"` → `persist_fetch` writes `"error_transport"` into cache meta, does not insert bars, does not advance cache, and `PersistResult.last_fetch_status = "error_transport"`
- `FetchResult.last_fetch_status = "ok"` with inserted bars → cache meta advances and `PersistResult.last_fetch_status = "ok"`

### Unit — no-backfill semantics

- stale cache, fetch fails with transport error → old valid bars remain, cache meta records error, no synthetic rows inserted
- missing cache, fetch returns no valid bars → no synthetic rows inserted

### Unit — config

- missing `ohlcv_fetch` block → defaults apply
- `lookback_bars_1d = 0` → `ValueError` with key and value
- `lookback_bars_4h = 100`, `min_lookback_bars_4h = 120` → `ValueError`
- partial override of `lookback_bars_1d` only → merge, remaining defaults preserved
- `ohlcv_fetch = "not_a_dict"` → `ValueError`

### Unit — nullability

- `cached_close_time_utc_ms`, `last_fetch_at_utc`, `last_error_code` stored as SQL `NULL` read back as Python `None`

### Unit — determinism

- two identical seeded runs with identical mocked response, config, and now → identical fetch results, persist results, and DB contents

### Integration

- end-to-end symbol+timeframe call with missing cache: fetch, validate, persist, create meta row
- end-to-end symbol+timeframe call with stale cache: incremental or full chosen correctly, cache advances correctly
- end-to-end symbol+timeframe call with fresh cache: no client call, DB unchanged
- downstream repository read returns most recent `N` closed bars ascending by `close_time_utc_ms`

### Golden fixture / verification

- `docs/canonical/VERIFICATION_FOR_AI.md` is updated in the same PR with:
  - `cache_status` table
  - `fetch_decision` table
  - lookback and threshold defaults
  - full vs incremental accepted-window semantics
  - persistence conflict semantics

## Constraints / Invariants (must not change)

- [ ] Ticket-1 bar-clock semantics are reused, not reinterpreted.
- [ ] Closed-bar-only persistence.
- [ ] UTC only.
- [ ] No lookahead.
- [ ] No backfill / no interpolation / no synthetic fill.
- [ ] `timeframe ∈ {"1d", "4h"}` is closed.
- [ ] `cache_status`, `fetch_decision`, and `last_fetch_status` are closed sets.
- [ ] No competing `never_attempted` state.
- [ ] `cached_close_time_utc_ms` advances only on `"ok"` with at least one newly inserted valid bar.
- [ ] Same-PK differing historical bars are conflict errors, not silent replacements.
- [ ] No Ticket-1 / Ticket-3 schema changes.
- [ ] No Parquet / dual-write / abstract store introduced in this ticket.
- [ ] No unrelated MEXC client refactor.
- [ ] One ticket = one PR.
- [ ] No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` per this ticket
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` in the same PR
- [ ] Added/updated tests per this ticket
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata

```yaml
created_utc: "2026-04-14T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [1, 3]
gesamtkonzept_ref: "§19 Ticket 4"
related_issues: []
follow_ups:
  - "Ticket 14: define long-term OHLCV history storage migration beyond transitional SQLite persistence"
```
