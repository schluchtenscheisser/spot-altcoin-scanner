> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# 2026-05-18__BACKTEST_PRE_1__binance_ohlcv_history_fetch

## Title

Backtest-Pre-1: Binance OHLCV History Fetch for Historical Signal-Quality Replay

## Context / Source

We are adding the first preparation ticket for the **Historical Signal-Quality Replay** workstream.

This workstream is not a trading backtest. It is a historical signal-quality validation layer for the Independence-Release scanner. The goal is to later run the existing signal-generation layers over historical OHLCV data and evaluate signal quality across multiple market regimes.

This ticket implements only the reusable historical OHLCV dataset required by later replay and evaluation tickets.

The agreed architecture decisions for this workstream are:

- Use the term **Historical Signal-Quality Replay**, not “trading backtest”.
- Use Binance Spot USDT OHLCV as the first external historical data source.
- Support two explicit universe modes: `fixed_current_mexc_binance_intersection` for operative validation and `binance_spot_usdt_all` for broad engine validation.
- Quantify survivorship bias via a structured universe manifest.
- Store historical OHLCV as Parquet under `snapshots/history/ohlcv/`.
- Keep fetch, replay, and evaluation strictly separated.
- Pre-1 does not run scanner logic.
- Pre-1 does not compute signals, states, buckets, execution grades, forward returns, MFE, MAE, or market-regime labels.

## Authoritative references

Use the current authoritative Independence-Release reference set:

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. The current canonical project documents, only insofar as they do not contradict the above reference set.
4. The agreed Historical Signal-Quality Replay decisions from Martin / ChatGPT / Claude review.

If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents continue to apply only insofar as they do not contradict this reference set.

Existing repo paths/helpers may be reused if they do not contradict the current authoritative reference set. Do not introduce a second competing truth for storage, manifests, time semantics, or universe definitions.

## Goal

Implement an idempotent, incrementally extendable Binance OHLCV history fetch layer that:

1. Builds reusable Binance Spot USDT OHLCV history datasets for the configured universe mode.
2. Stores closed 1d and 4h Binance Spot USDT candles as partitioned Parquet.
3. Emits mandatory provenance and universe manifests.
4. Quantifies survivorship-bias-related exclusions.
5. Supports later replay scenarios without requiring another full data fetch.

## Scope

Implement exactly this Pre-1 scope:

1. Binance Spot USDT symbol discovery / lookup.
2. Configurable universe mode resolution:
   - `fixed_current_mexc_binance_intersection`
   - `binance_spot_usdt_all`
3. MEXC/Binance symbol normalization and intersection when `universe_mode = fixed_current_mexc_binance_intersection`.
4. Binance OHLCV fetch for timeframes:
   - `1d`
   - `4h`
5. Closed-bar-only fetch semantics.
6. Parquet storage under:

```text
snapshots/history/ohlcv/timeframe=<timeframe>/symbol=<symbol>/year=<YYYY>/month=<MM>/part-000.parquet
```

7. Idempotent incremental updates.
8. History completeness checks.
9. Mandatory `history_manifest.json`.
10. Mandatory `universe_manifest.json`.
11. Mandatory `symbol_completeness.json`.
12. Tests covering date handling, closed-bar-only behavior, manifest output, universe modes/exclusions, idempotency, and repair/backfill behavior.

## Out of scope

Do not implement any of the following in this ticket:

- Historical replay runner.
- Scenario-YAML.
- Scenario immutability enforcement.
- T4 refactor or data-source abstraction.
- Changes to `scanner/data/ohlcv_fetch.py` unless required only for harmless shared utilities.
- Changes to `scanner/clients/mexc_client.py`.
- Changes to the live daily runner.
- T5–T12 execution.
- State Machine execution.
- Entry-pattern resolution.
- Decision bucket assignment.
- Historical pre-execution signal buckets.
- Execution simulation.
- Dummy execution fields.
- Forward returns.
- MFE / MAE.
- Market-regime labeling.
- Calibration / validation evaluation logic.
- Config tuning.
- Dynamic historical universe reconstruction.
- Delisting-aware historical universe reconstruction.

Pre-1 may record `evaluation_start_date` and `evaluation_end_date` in manifests for downstream planning only. Pre-1 must not use evaluation dates operationally except to validate and document warm-up coverage.

## Terminology

Use these terms consistently:

| Term | Meaning |
|---|---|
| `fetch_start_date` | First date to fetch OHLCV history from, including warm-up history. |
| `fetch_end_date` | Last date to fetch OHLCV history through. Default is the last fully closed daily bar at runtime. |
| `evaluation_start_date` | Planned downstream replay/evaluation start date. Manifest-only in Pre-1. |
| `evaluation_end_date` | Planned downstream replay/evaluation end date. Manifest-only in Pre-1. |
| `warm_up_1d_bars` | Required count of closed 1d warm-up bars before signal evaluation can start. |
| `warm_up_4h_bars` | Required count of closed 4h warm-up bars before signal evaluation can start. |
| `min_history_days` | Minimum daily-bar count for a symbol to be eligible for later signal evaluation. |
| `history_manifest.json` | Fetch/provenance/completeness manifest. |
| `universe_manifest.json` | Universe selection/exclusion/survivorship-bias manifest. |
| `symbol_completeness.json` | Per-symbol/per-timeframe completeness details for fetched OHLCV history. |

## Required defaults

Implement these defaults. They may be overridden only through the Pre-1 fetch interface, not by Scenario-YAML.

```yaml
fetch_start_date: 2025-01-01
fetch_end_date: auto_last_closed_daily_bar
evaluation_start_date: 2025-05-01
evaluation_end_date: fetch_end_date
warm_up_1d_bars: 120
warm_up_4h_bars: 120
min_history_days: 150
timeframes:
  - 1d
  - 4h
source: binance_spot
universe_mode: fixed_current_mexc_binance_intersection
# valid values:
#   - fixed_current_mexc_binance_intersection
#   - binance_spot_usdt_all
```

### Important date semantics

- `fetch_start_date` and `fetch_end_date` are operational Pre-1 fetch parameters.
- `evaluation_start_date` and `evaluation_end_date` are recorded for downstream scenario planning only.
- Pre-1 must not filter, replay, score, or evaluate symbols based on `evaluation_start_date` / `evaluation_end_date`.
- Pre-1 may use `evaluation_start_date` only to report whether `fetch_start_date` provides sufficient warm-up coverage.
- The default `fetch_start_date = 2025-01-01` exists to provide sufficient warm-up before the default `evaluation_start_date = 2025-05-01`.
- A later decision to fetch further back, for example from `2024-01-01`, is out of scope for this ticket and should be made only after the first full Pre-2 replay and inspection of `universe_manifest.json`.

## Input rules

Allowed date input type:

- ISO date string: `YYYY-MM-DD`.

Date timezone semantics:

- Dates are interpreted in UTC.
- Naive date strings are allowed only as calendar dates with UTC exchange-bar semantics.
- Naive datetimes are not allowed.
- Timezone-bearing datetime strings are not accepted in Pre-1 date parameters.

Hard rejection rules:

- Reject invalid date strings.
- Reject datetimes where a date is required.
- Reject `fetch_start_date > fetch_end_date`.
- Reject `evaluation_start_date > evaluation_end_date`.
- Reject missing required current-universe input if no existing repo resolver can provide it.
- Reject non-finite numeric values (`NaN`, `inf`, `-inf`) in runtime parameters, manifest-derived numeric fields, and computed completeness outputs.
- Reject unsupported timeframes.
- Reject ambiguous symbol mappings unless explicitly classified as `normalization_mismatch` in `universe_manifest.json`.

Allowed input types, units, coercion rules, and hard rejection rules must be fully specified in code and tests. Ambiguous inputs must not be silently reinterpreted.

## Proposed implementation shape

Codex should inspect the repo first and reuse existing helpers where appropriate. The exact file names may be adjusted to fit the repo reality, but keep the boundaries below.

Recommended implementation shape:

```text
scanner/evaluation/history/
  __init__.py
  binance_client.py              # small, OHLCV-only Binance public API helper if no existing helper exists
  history_fetch_config.py        # typed/defaulted Pre-1 fetch config
  symbol_intersection.py         # MEXC/Binance universe normalization and exclusion reasons
  ohlcv_history_fetch.py         # fetch orchestration, closed-bar-only logic, incremental writes
  parquet_store.py               # partition read/write helpers
  manifests.py                   # history_manifest.json, universe_manifest.json, and symbol_completeness.json builders

scripts/
  fetch_binance_history.py        # thin CLI entry point for Pre-1 only

tests/evaluation/history/
  ...
```

If the repo already has a more appropriate evaluation or data-history namespace, use it. Do not modify live scanner runtime modules unless the change is a harmless shared utility and does not alter live behavior.

## Fetch interface

Pre-1 may expose CLI/config parameters because Scenario-YAML is not yet part of Pre-1.

The CLI entry point should support at least:

```text
--fetch-start-date YYYY-MM-DD
--fetch-end-date YYYY-MM-DD | auto_last_closed_daily_bar
--evaluation-start-date YYYY-MM-DD
--evaluation-end-date YYYY-MM-DD | fetch_end_date
--mexc-universe-path <path>          # if no existing repo resolver is available
--output-root snapshots/history/ohlcv
--manifest-root snapshots/history/manifests
--universe-mode fixed_current_mexc_binance_intersection | binance_spot_usdt_all
--force-repair                       # explicit closed-partition repair/backfill mode
--dry-run                            # optional; if implemented, see dry-run semantics below
```

If the repo has a preferred config mechanism, it may be used instead of or in addition to CLI flags, but Pre-1 must remain reproducible and must record the effective parameters in `history_manifest.json`.

Pre-2 and Backtest-1 must not use ad-hoc CLI overrides for scenario-defining parameters. Scenario-YAML will be the only canonical run definition there. Do not implement Scenario-YAML in this ticket.

### Dry-run semantics

If `--dry-run` is implemented, it must mean:

- validate effective parameters, dates, universe mode, and output paths;
- resolve the planned universe where possible;
- log or print planned fetch/write/skip operations;
- perform no Parquet writes;
- perform no manifest writes;
- perform no closed-partition repair;
- return a non-zero exit code for invalid parameters.

If these semantics are not implemented completely, omit `--dry-run` from Pre-1 rather than providing a partial dry-run mode.

## Closed-bar-only requirements

Pre-1 must fetch and persist only fully closed bars.

Rules:

1. Never write a partial currently open 1d candle.
2. Never write a partial currently open 4h candle.
3. For `fetch_end_date = auto_last_closed_daily_bar`, compute the last fully closed daily bar using UTC exchange-bar semantics.
4. 4h bars must be included only if their close time is within the requested fetch window and the 4h bar is fully closed at runtime.
5. Any Binance API response containing a still-open candle must be filtered before persistence.
6. The manifest must record:
   - `closed_bar_only: true`
   - `runtime_utc`
   - `effective_fetch_end_date`
   - latest persisted close timestamp per symbol/timeframe where available.

Partial bars for the current open candle must never be written to the history dataset.

## Storage rules

Store data under:

```text
snapshots/history/ohlcv/timeframe=<timeframe>/symbol=<symbol>/year=<YYYY>/month=<MM>/part-000.parquet
```

Partition rules:

- Partition by `timeframe`, `symbol`, `year`, `month`.
- Month is the smallest regular time partition.
- Completed monthly partitions are immutable by default.
- The current/open month partition may be extended as new closed bars become available.
- Repair/backfill of a closed monthly partition requires an explicit flag such as `--force-repair` and must be logged in `history_manifest.json`.
- Repair/backfill must not trigger automatically.
- A repeated normal fetch run must not rewrite completed closed monthly partitions.

Required OHLCV columns:

```text
source              string, fixed value "binance_spot"
symbol              string, normalized Binance symbol, e.g. "BTCUSDT"
timeframe           string enum: "1d" / "4h"
open_time_utc       timestamp or ISO UTC string
close_time_utc      timestamp or ISO UTC string
open                float
high                float
low                 float
close               float
volume              float
quote_volume        float or null if unavailable
trade_count         integer or null if unavailable
is_closed           bool, must always be true for persisted rows
fetch_run_id        string
fetched_at_utc      timestamp or ISO UTC string
```

Additional Binance-native columns may be preserved if useful, but they must not replace the required normalized columns.

Numeric robustness:

- Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid or not evaluable and must not be passed through into numeric-looking manifest outputs.
- If Binance returns invalid OHLCV values for a row, do not silently coerce them. Either reject the row and record a data-quality issue or fail the run if safe continuation is impossible.

## Universe rules

Pre-1 must support exactly two universe modes. The default is `fixed_current_mexc_binance_intersection`.

### `universe_mode = fixed_current_mexc_binance_intersection`

Purpose: operative validation against the current scanner-relevant trading universe.

Rules:

1. Use the existing current MEXC scanner universe source/resolver if available.
2. If no resolver exists, accept an explicit current-universe input file and document this in the implementation notes.
3. Discover or load Binance Spot USDT symbols.
4. Normalize symbols deterministically.
5. Include only unambiguous MEXC/Binance symbol matches.
6. Do not invent mappings for ambiguous or unusual symbols.
7. Do not silently drop symbols.
8. Every excluded MEXC source symbol must appear in `universe_manifest.json` with a reason.
9. The exclusion reason `mexc_only` applies in this mode.

### `universe_mode = binance_spot_usdt_all`

Purpose: broad engine validation with a larger Binance-native sample and no MEXC-universe filter.

Rules:

1. Source universe is all Binance Spot USDT symbols with available history.
2. No MEXC intersection is required.
3. No current MEXC scanner universe input is required.
4. The exclusion reason `mexc_only` does not apply in this mode.
5. `universe_manifest.json` records `source_mexc_symbol_count` as `null`, meaning not applicable. Do not write `0` for this field in this mode.
6. Symbols can still be excluded for `no_binance_history`, `insufficient_history`, `unsupported_symbol`, `fetch_error`, or `normalization_mismatch` if applicable.

General rules for both modes:

1. Discover or load Binance Spot USDT symbols.
2. Normalize symbols deterministically.
3. Include only unambiguous symbols.
4. Do not silently drop symbols.
5. Every excluded source symbol must appear in `universe_manifest.json` with a reason.

Required exclusion reason enum:

```text
mexc_only              # present in current MEXC universe but not available as Binance Spot USDT
no_binance_history     # symbol exists/matches but no Binance OHLCV could be fetched
insufficient_history   # fetched but has fewer than min_history_days daily bars for later signal evaluation
normalization_mismatch # symbol could not be normalized/mapped unambiguously
unsupported_symbol     # symbol intentionally unsupported by the Pre-1 fetch implementation
fetch_error            # fetch failed for technical reasons; include error summary
```

`insufficient_history` is not a fetch blocker. A symbol may be fetched and stored even if it is later marked not signal-evaluable due to insufficient history.

Unknown/missing data must be flagged, not silently converted into a negative business decision.

## Manifest requirements

Emit both manifests on every non-dry-run execution under the fixed manifest directory:

```text
snapshots/history/manifests/history_manifest.json
snapshots/history/manifests/universe_manifest.json
```

`fetch_run_id` must be a field inside the manifests. It must not be part of the manifest file path.

### `history_manifest.json`

Purpose: describes the fetch operation, dataset provenance, partitions, aggregate bar counts, closed-bar policy, and completeness. Per-symbol/per-timeframe completeness details must be written to a separate `symbol_completeness.json`, not embedded as top-level detail maps in `history_manifest.json`.

Required top-level fields:

```json
{
  "manifest_type": "history_manifest",
  "schema_version": "backtest_pre1_v1",
  "fetch_run_id": "...",
  "created_at_utc": "...",
  "source": "binance_spot",
  "timeframes": ["1d", "4h"],
  "fetch_start_date": "2025-01-01",
  "fetch_end_date_requested": "auto_last_closed_daily_bar",
  "effective_fetch_end_date": "YYYY-MM-DD",
  "evaluation_start_date": "2025-05-01",
  "evaluation_end_date": "YYYY-MM-DD",
  "evaluation_dates_operational_in_pre1": false,
  "warm_up_1d_bars": 120,
  "warm_up_4h_bars": 120,
  "min_history_days": 150,
  "closed_bar_only": true,
  "output_root": "snapshots/history/ohlcv",
  "partitioning": "timeframe/symbol/year/month",
  "force_repair": false,
  "symbols_total": 0,
  "symbols_with_any_history": 0,
  "bar_counts_by_timeframe": {},
  "symbol_completeness_path": "snapshots/history/manifests/symbol_completeness.json",
  "partitions_written": [],
  "partitions_skipped_existing": [],
  "partitions_repaired": [],
  "data_quality_issues": [],
  "incremental_update_summary": {
    "existing_partitions_detected": 0,
    "new_partitions_written": 0,
    "existing_closed_partitions_rewritten": 0
  }
}
```

`evaluation_start_date` and `evaluation_end_date` are manifest fields for downstream scenario planning only. Pre-1 must not use them operationally.

### `symbol_completeness.json`

Purpose: contains per-symbol/per-timeframe details that would be too large or too granular for the top-level history manifest.

Required content:

```json
{
  "manifest_type": "symbol_completeness",
  "schema_version": "backtest_pre1_v1",
  "fetch_run_id": "...",
  "created_at_utc": "...",
  "bar_counts_by_symbol_timeframe": {},
  "latest_close_time_by_symbol_timeframe": {},
  "first_close_time_by_symbol_timeframe": {},
  "missing_ranges_by_symbol_timeframe": {}
}
```

`symbol_completeness.json` is mandatory for every non-dry-run execution. It supplements `history_manifest.json`; it does not replace it.

### `universe_manifest.json`

Purpose: describes the selected universe mode, source symbols, included symbols, exclusions, and survivorship-bias-related counts.

Required top-level fields:

```json
{
  "manifest_type": "universe_manifest",
  "schema_version": "backtest_pre1_v1",
  "fetch_run_id": "...",
  "created_at_utc": "...",
  "universe_mode": "fixed_current_mexc_binance_intersection",
  "source_mexc_symbol_count": 0,
  "binance_usdt_symbol_count": 0,
  "included_replay_symbol_count": 0,
  "signal_evaluable_symbol_count": 0,
  "excluded_counts": {
    "mexc_only": 0,
    "no_binance_history": 0,
    "insufficient_history": 0,
    "normalization_mismatch": 0,
    "unsupported_symbol": 0,
    "fetch_error": 0
  },
  "included_symbols": [],
  "signal_evaluable_symbols": [],
  "excluded_symbols": [
    {
      "source_symbol": "...",
      "normalized_symbol": "...",
      "reason": "mexc_only",
      "detail": "..."
    }
  ]
}
```

`source_mexc_symbol_count` must be an integer for `fixed_current_mexc_binance_intersection`. It must be `null` for `binance_spot_usdt_all`, because the MEXC universe is not used in that mode.

`history_manifest.json`, `universe_manifest.json`, and `symbol_completeness.json` are mandatory non-dry-run outputs. Do not merge them into a single file. Do not omit any of them.

## Incremental fetch requirements

Pre-1 must be idempotent and incrementally extendable.

Required behavior:

1. If no history exists, fetch and write the full requested closed-bar range.
2. If history already exists, detect existing partitions and existing latest close times.
3. On a repeated run with the same effective date range, do not duplicate rows.
4. On a later run with a later `fetch_end_date`, append only missing/new closed bars where possible.
5. Do not rebuild all history on every run.
6. Do not rewrite closed monthly partitions unless `--force-repair` is explicitly set.
7. Record all written, skipped, and repaired partitions in `history_manifest.json`.
8. Row uniqueness must be enforced at least by `(source, symbol, timeframe, open_time_utc)`.

Example expected behavior:

```text
Run 1:
  fetch_start_date = 2025-01-01
  effective_fetch_end_date = 2026-05-17
  writes all required partitions

Run 2 on the next day:
  fetch_start_date = 2025-01-01
  effective_fetch_end_date = 2026-05-18
  detects existing partitions
  fetches only missing/new closed bars
  does not rewrite completed historical monthly partitions
```

## Determinism requirements

For identical input parameters, identical source responses, and identical existing storage state:

- included symbols are identical,
- exclusion reasons are identical,
- partition paths are identical,
- row ordering within written Parquet files is deterministic,
- manifests are identical except for allowed runtime/provenance fields such as `created_at_utc` and `fetch_run_id`.

Ordering rules:

- Sort symbols ascending lexicographically by normalized symbol.
- Sort timeframes in explicit order: `1d`, then `4h`.
- Sort rows by `symbol`, `timeframe`, `open_time_utc`.
- Sort `excluded_symbols` by `reason`, then `source_symbol`, then `normalized_symbol`.

For identical input and identical config, selection, ordering, statuses, and reasons are identical.

## Pipeline boundaries / stop paths

This ticket stops before scanner replay.

`Backtest-Pre-1` stops before T5 raw feature computation and must not trigger any downstream scanner costs in T5–T12, execution, decision, report generation, or forward-return evaluation.

Pre-1 output is a reusable historical OHLCV dataset plus manifests only.

## Acceptance criteria

### AC1 — Scope boundary

- The implementation fetches Binance Spot USDT OHLCV history and writes Parquet + manifests only.
- No scanner signal-generation layers are executed.
- No state machine, entry-pattern, decision, execution, or forward-return code is added or called.
- No Scenario-YAML is implemented.

### AC2 — Date parameter separation

- `fetch_start_date`, `fetch_end_date`, `evaluation_start_date`, and `evaluation_end_date` are separate parameters/manifest fields.
- `fetch_start_date` default is `2025-01-01`.
- `fetch_end_date` default is `auto_last_closed_daily_bar`.
- `evaluation_start_date` default is `2025-05-01`.
- `evaluation_end_date` default resolves to the effective `fetch_end_date`.
- `evaluation_start_date` and `evaluation_end_date` are recorded in the manifest for downstream scenario planning only.
- Pre-1 does not use evaluation dates operationally except to report warm-up coverage.

### AC3 — Closed-bar-only guarantee

- Only fully closed 1d and 4h bars are written.
- Partial current candles are filtered out and never persisted.
- Persisted rows have `is_closed = true`.
- The manifest records `closed_bar_only = true`.

### AC4 — Warm-up and history constants

- `warm_up_1d_bars = 120`.
- `warm_up_4h_bars = 120`.
- `min_history_days = 150`.
- These constants are recorded in `history_manifest.json`.
- Symbols with fewer than `min_history_days` daily bars are marked as not signal-evaluable in `universe_manifest.json`, not silently dropped.

### AC5 — Parquet storage

- 1d and 4h OHLCV are stored under `snapshots/history/ohlcv/`.
- Partitioning follows `timeframe/symbol/year/month`.
- Required normalized OHLCV columns are present.
- Rows are sorted deterministically.
- Duplicate `(source, symbol, timeframe, open_time_utc)` rows are prevented.

### AC6 — Idempotent incremental fetch

- Re-running with the same parameters does not duplicate rows.
- Re-running after new closed bars exist fetches only missing/new bars where possible.
- Completed monthly partitions are not rewritten by default.
- Current/open monthly partitions may be extended with newly closed bars.
- Closed-partition repair/backfill requires an explicit `--force-repair` flag or equivalent explicit option.
- Any repair/backfill is recorded in `history_manifest.json`.

### AC7 — Universe modes, universe manifest, and survivorship quantification

- `universe_manifest.json` is always emitted.
- Both universe modes are supported:
  - `fixed_current_mexc_binance_intersection`
  - `binance_spot_usdt_all`
- `fixed_current_mexc_binance_intersection` uses current MEXC scanner symbols intersected with Binance Spot USDT symbols.
- `binance_spot_usdt_all` uses all Binance Spot USDT symbols with available history and does not require a MEXC universe input.
- `source_mexc_symbol_count` is an integer for `fixed_current_mexc_binance_intersection` and `null` for `binance_spot_usdt_all`.
- The `mexc_only` exclusion reason applies only to `fixed_current_mexc_binance_intersection`.
- It includes source symbol counts where applicable, Binance USDT symbol count, included replay symbol count, signal-evaluable symbol count, exclusion counts, included symbols, signal-evaluable symbols, and excluded symbols.
- Exclusion reasons include at least:
  - `mexc_only`
  - `no_binance_history`
  - `insufficient_history`
  - `normalization_mismatch`
  - `unsupported_symbol`
  - `fetch_error`
- No symbol is silently dropped.

### AC8 — History manifest

- `history_manifest.json` is always emitted.
- It describes the fetch operation, effective date parameters, source, timeframes, closed-bar-only status, partitioning, written/skipped/repaired partitions, aggregate bar counts, completeness summary, data-quality issues, and incremental update summary.
- Per-symbol/per-timeframe completeness details are written to mandatory `symbol_completeness.json`.
- It is separate from `universe_manifest.json`.

### AC9 — Input validation

- Invalid date strings are rejected.
- Datetimes are rejected where dates are required.
- `fetch_start_date > fetch_end_date` is rejected.
- `evaluation_start_date > evaluation_end_date` is rejected.
- Unsupported timeframes are rejected.
- Ambiguous symbol mappings are not guessed and are represented via `normalization_mismatch`.
- Non-finite numeric values are not passed through into numeric-looking outputs.

### AC10 — Tests and CI

- Add focused unit tests and/or integration tests for all required behavior below.
- Existing tests continue to pass.
- Run `python -m pytest -q` and report the result.

## Required tests / explicit cases

Implement concrete tests or testable fixtures covering at least:

1. **Default date resolution**
   - Given no explicit dates, defaults resolve to `fetch_start_date=2025-01-01`, `evaluation_start_date=2025-05-01`, and `fetch_end_date=auto_last_closed_daily_bar`.

2. **Evaluation dates are manifest-only**
   - Changing `evaluation_start_date` does not change fetched bar range, except for manifest warm-up coverage reporting.

3. **Invalid date rejection**
   - Reject `2025-13-01`.
   - Reject a datetime string such as `2025-01-01T12:00:00Z` where a date is required.
   - Reject `fetch_start_date > fetch_end_date`.

4. **Closed-bar-only filtering**
   - Given a mocked Binance response containing one closed candle and one still-open current candle, only the closed candle is written.

5. **No duplicate rows**
   - Running the same fetch twice produces no duplicate `(source, symbol, timeframe, open_time_utc)` rows.

6. **Incremental append**
   - Given existing history through day N, a later run through day N+1 writes only the new closed bars.

7. **Closed partition immutability**
   - A normal run does not rewrite an already completed historical monthly partition.

8. **Explicit repair/backfill**
   - With `--force-repair`, a closed monthly partition may be rebuilt and the repair is recorded in `history_manifest.json`.
   - Without `--force-repair`, the same repair must not occur.

9. **Universe modes**
   - `fixed_current_mexc_binance_intersection` includes only unambiguous MEXC/Binance intersections and records `source_mexc_symbol_count` as an integer.
   - `binance_spot_usdt_all` includes Binance Spot USDT symbols without requiring a MEXC universe input and records `source_mexc_symbol_count` as `null`.

10. **Universe exclusion reasons**
   - A MEXC-only symbol is recorded as `mexc_only` in `fixed_current_mexc_binance_intersection`.
   - `mexc_only` is not emitted in `binance_spot_usdt_all`.
   - A symbol with no fetched Binance history is recorded as `no_binance_history`.
   - A symbol with fewer than `min_history_days` daily bars is recorded as `insufficient_history`.
   - An ambiguous symbol mapping is recorded as `normalization_mismatch`.

11. **Manifest separation**
    - `history_manifest.json` and `universe_manifest.json` are both emitted and contain distinct required fields.
    - `symbol_completeness.json` is emitted separately for per-symbol/per-timeframe details.

12. **Dry-run writes no artifacts**
    - If `--dry-run` is implemented, no Parquet files are written.
    - If `--dry-run` is implemented, `history_manifest.json`, `universe_manifest.json`, and `symbol_completeness.json` are not written.
    - If `--dry-run` is omitted from Pre-1, this test case is not required.

13. **Deterministic ordering**
    - Given unordered source symbols and unordered mocked bars, output manifests and Parquet rows are sorted according to the deterministic rules above.

14. **Numeric robustness**
    - Non-finite OHLCV numeric values are rejected or recorded as data-quality issues according to the implemented policy; they are not silently written as valid numeric outputs.

Every required preflight category is covered by at least one explicit test case or an equally explicit, verifiable check.

## Definition of done

This ticket is done when:

1. Pre-1 fetch can build Binance Spot USDT 1d/4h OHLCV Parquet history datasets for both supported universe modes: `fixed_current_mexc_binance_intersection` and `binance_spot_usdt_all`.
2. The fetch is closed-bar-only.
3. The fetch is idempotent and incrementally extendable.
4. Completed monthly partitions are immutable by default.
5. Explicit repair/backfill requires `--force-repair` or equivalent.
6. `history_manifest.json` is emitted.
7. `universe_manifest.json` is emitted.
8. `symbol_completeness.json` is emitted.
9. Survivorship-bias exclusions are quantitatively visible in `universe_manifest.json`.
10. Evaluation dates are manifest-only in Pre-1.
11. Tests cover the required concrete cases, including at least one test for each supported universe mode.
12. `python -m pytest -q` passes, or any failure is clearly unrelated and reported with evidence.
13. No live scanner behavior changes.

## Implementation notes for later tickets

These notes are intentionally not Pre-1 scope:

- Pre-2 will use Scenario-YAML as the only canonical run definition.
- Scenario IDs will be immutable after the first replay run.
- Pre-2 will bypass T4 and feed Binance Parquet bars into the same downstream bar/feature path used by T5–T12.
- Backtest-1 will later evaluate full-sample first; calibration/validation splits will be carried in manifests but activated only after the infrastructure is stable.
- The primary future forward-return reference price will be `next_daily_open`; `signal_bar_close` returns may be retained only as secondary methodological context.
- Market-regime labels will be frozen before the first replay run, likely using objective BTC/USDT weekly rules.
