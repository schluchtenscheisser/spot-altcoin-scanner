# BACKTEST-MERGE-1: Replay Event Dataset Export for Backtest-1

## Metadata

- Ticket ID: BACKTEST-MERGE-1
- Title: Replay Event Dataset Export for Backtest-1
- Status: Ready for external review
- Priority: P1
- Language: Implementation and code artifacts in English
- Target PR size: 1 PR
- Created: 2026-05-26

---

## Context and motivation

The historical replay infrastructure is now capable of producing a complete chunked
replay over the scenario:

```text
configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml
```

The relevant scenario properties are:

```yaml
scenario_id: hsq_replay_2025_05_to_2026_05_v1
history_dataset_ref: snapshots/history/ohlcv
timeframes:
  - 1d
  - 4h
universe_mode: binance_spot_usdt_all
evaluation:
  start_date: "2025-05-01"
  end_date: "2026-05-17"
execution:
  mode: disabled_historical_ohlcv_only
```

The completed full chunked replay produced a valid replay artifact with:

- 13 monthly chunks
- a complete `replay_manifest.json`
- per-chunk `replay_event_candidates.parquet`
- per-chunk `replay_symbol_diagnostics.jsonl.gz`
- state handoff across chunk boundaries
- the expected execution-disabled historical OHLCV-only context

A May-2025 cold-start diagnostic showed:

```text
cold_start May 2025 events:   949
state_preroll May 2025 events: 949
reduction:                       0.0%
```

Therefore the May-2025 event spike is not explained by a simple
`evaluation_start` cold-start effect. However, May remains a boundary /
warm-up-diagnostic month because it dominates the event population. Backtest
analysis must support an `analysis_start_date`, defaulting to `2025-06-01`, while
still preserving the full event population.

This ticket creates the merge/export layer that converts the replay artifact into
a deterministic Backtest-1 input dataset.

---

## Authoritative references

Current authoritative reference hierarchy:

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. The v2.1 addendum for future tickets and new chats.
4. Approved and implemented Backtest/Replay tickets and repo reality:
   - `docs/legacy/tickets/2026-05-18__BACKTEST_PRE_2__historical_daily_replay_harness.md`
   - `docs/legacy/tickets/2026-05-23__BACKTEST-CHUNK-1__chunk_capable_replay_runner_v3.md`
   - `docs/legacy/tickets/2026-05-24__BACKTEST-CHUNK-2__github_actions_chunked_replay_workflow_v3.md`
   - `configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml`
   - `scripts/run_replay_chunks.py`
   - `scanner/evaluation/historical_replay/replay_runner.py`
   - `scanner/evaluation/historical_replay/bar_loader.py`

Authority rule:

> If the current authoritative reference set, existing repo Authority/Canonical
> documents, and existing code collide, the current authoritative reference set
> wins. Repo documents remain valid only where they do not contradict this
> reference set.

This ticket must not create a second competing documentation authority. Existing
repo documents apply only insofar as they do not contradict this ticket and the
authoritative reference set above.

---

## Goal

Create a deterministic merge/export utility that builds a clean Backtest-1 input
dataset from a completed historical replay run.

The utility must:

1. Merge all chunk-level event Parquets.
2. Merge all chunk-level diagnostics JSONL.GZ files.
3. Join events to diagnostics context.
4. Add analysis-window flags.
5. Add BTC regime labels.
6. Add OHLCV-derived liquidity/size proxy fields.
7. Add basic forward-return label columns.
8. Write a machine-readable export manifest.
9. Validate all relevant counts and joins fail-fast.

---

## Non-goals / out of scope

This ticket must not implement:

- strategy conclusions
- ranking recalibration
- trading recommendations
- Backtest-1 aggregate performance reports
- MFE / MAE calculations
- `next_daily_open`
- terminal-event special handling
- execution / orderbook simulation
- MEXC liquidity checks
- external MarketCap fetching
- present-day MarketCap classification of historical events
- scenario parser or scenario registry changes
- replay runner semantics changes
- chunk workflow changes
- production adapter changes
- `historical_signal_bucket` mapping changes
- Pre-1 fetch logic changes

This ticket is only a merge/enrichment/export step.

---

## New script

Create:

```text
scripts/backtest/build_replay_event_dataset.py
```

The script must be executable as a CLI tool and importable for tests.

---

## CLI

Required command shape:

```bash
python scripts/backtest/build_replay_event_dataset.py \
  --replay-run-dir evaluation/replay/runs/<scenario_id>/<replay_id> \
  --history-root snapshots/history/ohlcv \
  --regime-labels snapshots/history/regime_labels/regime_labels_btc_weekly_30d_return_vol_v1.json \
  --output-root evaluation/backtest/exports \
  --analysis-start-date 2025-06-01
```

### Required arguments

| Argument | Type | Unit / format | Required | Semantics |
|---|---|---:|---:|---|
| `--replay-run-dir` | path string | existing directory | yes | Directory containing `replay_manifest.json` and `chunks/` |
| `--history-root` | path string | existing directory | yes | Pre-1 OHLCV Parquet root, usually `snapshots/history/ohlcv` |
| `--regime-labels` | path string | existing file | yes | Frozen BTC weekly regime label JSON |
| `--output-root` | path string | directory path | yes | Root under which export directory is created |

### Optional arguments

| Argument | Type | Unit / format | Default | Semantics |
|---|---|---:|---|---|
| `--analysis-start-date` | string | `YYYY-MM-DD` | `2025-06-01` | Start of primary analysis window; rows before this remain exported but are flagged out |
| `--analysis-end-date` | string | `YYYY-MM-DD` | replay manifest `evaluation_end_date` | End of primary analysis window |
| `--forward-horizons` | string | comma-separated positive integer days | `1,3,5,10,20` | Forward-close return horizons |

### Input contract and rejection rules

Allowed input types, units, coercion rules, and hard rejection rules are fully
specified. Ambiguous inputs must not be silently reinterpreted.

Date arguments:

- Must be strings in exact `YYYY-MM-DD` format.
- Must represent valid calendar dates.
- Timezone-aware or naive `datetime` strings are not accepted.
- Numeric epoch timestamps are not accepted.
- `analysis_start_date <= analysis_end_date` is required.
- `analysis_start_date` and `analysis_end_date` must fall within the replay
  evaluation window in `replay_manifest.json`.
- Invalid dates must raise a clear `ValueError` or `SystemExit` with an actionable
  message.

Path arguments:

- `--replay-run-dir`, `--history-root`, and `--regime-labels` must exist.
- Missing required files under those paths fail fast before any output write.
- Output directory may be created if missing.
- Existing output directory for the same `<scenario_id>/<replay_id>` must fail
  fast unless the implementation provides an explicit `--overwrite` flag. This
  ticket does **not** require an `--overwrite` flag.

Forward horizons:

- Parsed from comma-separated positive integers.
- Values must be unique after parsing.
- Values must be sorted ascending in the manifest and output schema.
- `0`, negative numbers, non-integers, empty entries, and duplicated values are
  invalid and must fail fast.
- Units are calendar daily bars, not hours, not milliseconds.

---

## Input structure

A valid replay run directory has this structure:

```text
<replay-run-dir>/
  replay_manifest.json
  state_latest.sqlite
  chunks/
    <chunk_id>/
      chunk_manifest.json
      replay_event_candidates.parquet
      replay_symbol_diagnostics.jsonl.gz
      state_working.sqlite
      state_final.sqlite
```

Only the following files are required for this ticket:

```text
replay_manifest.json
chunks/<chunk_id>/chunk_manifest.json
chunks/<chunk_id>/replay_event_candidates.parquet
chunks/<chunk_id>/replay_symbol_diagnostics.jsonl.gz
```

State SQLite files may exist but must not be read or modified by this script.

---

## Output structure

Write outputs under:

```text
evaluation/backtest/exports/<scenario_id>/<replay_id>/
```

Required files:

```text
all_replay_event_candidates.parquet
all_replay_symbol_diagnostics.parquet
enriched_replay_events.parquet
backtest_merge_manifest.json
```

All output writes must be atomic where practical:

- Write to a temporary path in the same directory.
- Replace the final path only after a complete successful write.
- Never leave partially written JSON manifests.

---

## Output 1: `all_replay_event_candidates.parquet`

This is the deterministic concatenation of all chunk event candidate Parquets.

Required behavior:

- Read every chunk listed in `replay_manifest.json.chunks_completed`.
- Concatenate all `replay_event_candidates.parquet` files.
- Do not silently include unlisted chunk directories.
- Sort deterministically by:

```text
scenario_id
replay_id
as_of_daily_bar_id
symbol
event_type
```

Expected minimum fields are inherited from the replay event schema. If the current
event Parquets already contain the enriched context fields added after the first
full replay, preserve them.

---

## Output 2: `all_replay_symbol_diagnostics.parquet`

This is the deterministic concatenation of all chunk diagnostics files.

Required behavior:

- Read every chunk listed in `replay_manifest.json.chunks_completed`.
- Concatenate all `replay_symbol_diagnostics.jsonl.gz` files.
- Convert to Parquet.
- Do not silently include unlisted chunk directories.
- Sort deterministically by:

```text
scenario_id
replay_id
as_of_daily_bar_id
symbol
```

---

## Output 3: `enriched_replay_events.parquet`

This is the main Backtest-1 input dataset.

It must be produced by left-joining events to diagnostics on:

```text
scenario_id
replay_id
symbol
as_of_daily_bar_id
```

Join integrity is strict:

- Every event row must match exactly one diagnostics row.
- Diagnostics duplicate keys for the join key are invalid.
- Event duplicate keys for the event key are invalid.
- Missing joins are invalid.
- Join failures must fail the script.

### Required enriched event fields

The enriched dataset must include at least the following fields.

#### Replay identity

```text
scenario_id
replay_id
symbol
as_of_daily_bar_id
event_timestamp_utc
event_type
```

#### Signal context

```text
state_machine_state
historical_signal_bucket
market_phase
market_phase_confidence
state_confidence
state_transition_reason
entry_pattern
entry_pattern_score
setup_cycle_id
signal_daily_close
```

#### Data / missing context

```text
consecutive_missing_1d_bars_at_event
consecutive_missing_4h_bars_at_event
data_4h_available
data_resolution_class
```

#### Disposition / execution-disabled context

```text
disposition_status
disposition_reason
execution_evaluation_status
is_tradeable_candidate
```

#### Analysis controls

```text
included_in_primary_analysis
analysis_start_date
analysis_end_date
```

#### BTC regime

```text
btc_regime_week
btc_regime_label
btc_30d_return
btc_30d_realized_vol
```

#### OHLCV-derived liquidity / size proxies

```text
signal_day_quote_volume
median_quote_volume_30d
median_quote_volume_90d
available_history_days_1d_at_event
quote_volume_bucket
```

#### Forward-return labels

For every requested forward horizon `N`:

```text
forward_close_return_<N>d
has_forward_<N>d
```

Example for default horizons:

```text
forward_close_return_1d
has_forward_1d
forward_close_return_3d
has_forward_3d
forward_close_return_5d
has_forward_5d
forward_close_return_10d
has_forward_10d
forward_close_return_20d
has_forward_20d
```

---

## Field semantics

### `included_in_primary_analysis`

Boolean, not nullable.

```text
true  iff analysis_start_date <= as_of_daily_bar_id <= analysis_end_date
false otherwise
```

Rows before `analysis_start_date` and after `analysis_end_date` must remain in
the export. They are not dropped.

### `analysis_start_date` / `analysis_end_date`

String fields in `YYYY-MM-DD` format copied into every enriched row.

### `event_timestamp_utc`

If already present in the event Parquet, preserve it.

If missing, derive it from `as_of_daily_bar_id`:

```text
<as_of_daily_bar_id>T23:59:59Z
```

This timestamp is a closed daily bar event timestamp and not a live execution
timestamp.

### `is_tradeable_candidate`

Nullable tri-state field.

- `true` means evaluated and tradeable in the source context.
- `false` means evaluated and not tradeable in the source context.
- `null` means not evaluated / not applicable.

For this scenario, execution is disabled historical OHLCV-only, so null is the
expected value. `null` must not be coerced to `false`.

### `execution_evaluation_status`

Expected value for this scenario:

```text
not_evaluated_historical_ohlcv_only
```

This is not a failure. It means execution/orderbook evaluation was intentionally
not performed.

### `signal_daily_close`

Numeric signal reference close from the event output.

- Must be finite for rows where forward returns are calculated.
- If missing or non-finite, forward returns for that row must be null and
  `has_forward_<N>d = false`.
- Missing/non-finite values must be counted in the manifest.

### Nullable fields

The following fields are nullable:

```text
state_machine_state
state_confidence
state_transition_reason
entry_pattern_score
setup_cycle_id
disposition_reason
is_tradeable_candidate
btc_regime_label
btc_30d_return
btc_30d_realized_vol
signal_day_quote_volume
median_quote_volume_30d
median_quote_volume_90d
quote_volume_bucket
forward_close_return_<N>d
```

For each nullable field:

> `null` means "not reliably evaluable / not available in this context" and must
> not be implicitly coerced to `false`, `0`, empty string, or a negative
> evaluation.

Not evaluable / not assessed and negative evaluation are separate states and
must remain separate in code.

---

## BTC regime join

Join the frozen weekly BTC regime label file by ISO week derived from
`as_of_daily_bar_id`.

Required behavior:

- Derive ISO year/week from each event date.
- Join to the regime label JSON.
- Store the joined week identifier as `btc_regime_week`.
- If an individual week label is missing:
  - set `btc_regime_label = null`
  - set `btc_30d_return = null`
  - set `btc_30d_realized_vol = null`
  - increment `missing_regime_label_count`
  - do not fail
- If the regime label file itself is missing or unreadable, fail fast.
- If all events have missing regime labels, fail fast because this almost
  certainly indicates an incompatible regime-label schema.

The implementation must inspect the existing regime-label JSON schema in the repo
or release artifact and adapt to the actual field names without inventing a
second schema. If the schema cannot be interpreted unambiguously, fail fast with
a clear error.

---

## OHLCV-derived liquidity / size proxies

Because the current replay intentionally disables execution and uses
`binance_spot_usdt_all`, this export must add OHLCV-based proxy fields so that
later analysis can detect whether results are dominated by tiny volatile symbols.

### Required fields

For each event, derive from Pre-1 1d OHLCV history:

```text
signal_day_quote_volume
median_quote_volume_30d
median_quote_volume_90d
available_history_days_1d_at_event
quote_volume_bucket
```

### 1d OHLCV source

Read from:

```text
<history-root>/timeframe=1d/symbol=<symbol>/year=<YYYY>/month=<MM>/part-000.parquet
```

The implementation may reuse existing historical bar loading helpers if they do
not contradict this ticket. No second truth should be introduced.

### Quote-volume source field

Use the `quote_volume` column from Pre-1 OHLCV Parquet.

If `quote_volume` is missing from a symbol's OHLCV file:

- set the relevant quote-volume proxy fields to null
- set `quote_volume_bucket = "qv_unknown"`
- count the row in manifest diagnostics
- do not fail the entire export unless all symbols lack `quote_volume`

### Lookback windows

For an event at date `t = as_of_daily_bar_id`:

- `signal_day_quote_volume` is `quote_volume[t]` from the 1d bar matching the event date.
- `median_quote_volume_30d` is the median of up to 30 closed daily bars ending at `t`,
  inclusive.
- `median_quote_volume_90d` is the median of up to 90 closed daily bars ending at `t`,
  inclusive.
- `available_history_days_1d_at_event` is the count of available 1d bars with
  `date <= t`.

If fewer than 30 or 90 bars exist, compute the median over the available bars and
record the available count. If no valid finite `quote_volume` exists in the
window, the median is null.

### `quote_volume_bucket`

Use `median_quote_volume_30d` if finite and available, else `signal_day_quote_volume`.

Allowed enum values:

```text
qv_lt_100k
qv_100k_1m
qv_1m_10m
qv_10m_100m
qv_ge_100m
qv_unknown
```

Bucket thresholds:

| Bucket | Condition |
|---|---|
| `qv_lt_100k` | `0 <= value < 100_000` |
| `qv_100k_1m` | `100_000 <= value < 1_000_000` |
| `qv_1m_10m` | `1_000_000 <= value < 10_000_000` |
| `qv_10m_100m` | `10_000_000 <= value < 100_000_000` |
| `qv_ge_100m` | `value >= 100_000_000` |
| `qv_unknown` | missing, null, non-finite, or negative value |

Negative quote-volume values are invalid data and must not be placed into a
numeric-looking bucket.

---

## MarketCap handling

Do not add current MarketCap as a historical feature.

Do not fetch external MarketCap data.

Do not use present-day MarketCap to classify historical 2025/2026 events because
that would introduce lookahead bias.

The manifest must explicitly state:

```json
{
  "market_cap_available": false,
  "market_cap_reason": "not_available_point_in_time",
  "liquidity_proxy_fields": [
    "signal_day_quote_volume",
    "median_quote_volume_30d",
    "median_quote_volume_90d",
    "quote_volume_bucket"
  ]
}
```

---

## Forward-return labels

For every requested horizon `N`, compute:

```text
forward_close_return_<N>d = close[t + N] / signal_daily_close - 1
```

Where:

- `t` is `as_of_daily_bar_id`.
- `close[t + N]` is the close of the 1d bar `N` available calendar daily bars after
  `t` for the same symbol.
- `signal_daily_close` is the event reference close.

Add:

```text
has_forward_<N>d = true
```

iff `close[t + N]` exists and both numerator and denominator are finite, and
`signal_daily_close > 0`.

Otherwise:

```text
forward_close_return_<N>d = null
has_forward_<N>d = false
```

Forward-return columns are evaluation labels only. They are not signal inputs,
bucket inputs, ranking inputs, or tradeability inputs.

The manifest must explicitly state:

```json
{
  "forward_returns_are_labels_only": true,
  "no_lookahead_signal_inputs": true
}
```

No-lookahead rule:

> Forward-return columns may use future OHLCV only as evaluation labels. They
> must not be used to compute or alter any signal, bucket, ranking, filter, or
> tradeability field.

---

## Numeric robustness

Non-finite numerical values (`NaN`, `inf`, `-inf`) are invalid or not-evaluable
inputs and must not be passed through into numeric-looking outputs.

Required behavior:

- Output Parquet nullable numeric columns may contain nulls.
- They must not contain `NaN`, `inf`, or `-inf`.
- Division by zero or quasi-zero denominators must produce null return and
  `has_forward_<N>d = false`.
- Negative `quote_volume` must not be bucketed as valid volume.
- Non-finite `quote_volume` must be treated as unknown.
- Non-finite `close` values in OHLCV history must prevent the affected forward
  label from being marked available.

---

## Required validations

### V1 — Replay completeness

Read `replay_manifest.json`.

Fail if:

- file is missing
- `is_complete is not true`
- `replay_days_completed != replay_days_total`
- `chunks_completed` is missing or empty

### V2 — Chunk completeness

Every chunk listed in `chunks_completed` must have:

```text
chunk_manifest.json
replay_event_candidates.parquet
replay_symbol_diagnostics.jsonl.gz
```

Fail if any are missing.

### V3 — Event count consistency

Sum event rows across all listed chunk Parquets.

Compare against:

```text
replay_manifest.signal_events_so_far
```

Fail on mismatch.

Important:

```text
replay_manifest.signal_events_total
```

must not be used as the total event count in chunk mode because it may represent
only the final chunk.

### V4 — Diagnostics count consistency

Sum diagnostics rows across all listed chunk JSONL.GZ files.

Compare against:

```text
replay_manifest.diagnostics_so_far
```

Fail on mismatch.

### V5 — Join integrity

Validate that every event row matches exactly one diagnostics row on:

```text
scenario_id
replay_id
symbol
as_of_daily_bar_id
```

Fail if:

- any event has no matching diagnostic row
- any event has more than one matching diagnostic row
- diagnostics contains duplicate join keys

### V6 — Duplicate event keys

Fail if duplicate event rows exist for:

```text
scenario_id
replay_id
symbol
as_of_daily_bar_id
event_type
```

### V7 — Required fields

Fail if required event identity fields are missing:

```text
scenario_id
replay_id
symbol
as_of_daily_bar_id
event_type
```

Fail if neither event nor diagnostics source can provide required enriched fields
listed in this ticket. Nullable fields may be null, but the columns must exist.

### V8 — History root

Fail if `--history-root` does not exist.

Fail if no usable 1d OHLCV can be loaded for any event symbol.

### V9 — Regime labels

Fail if `--regime-labels` file is missing or unreadable.

Do not fail for individual missing weeks. Count them.

Fail if all regime joins are missing.

### V10 — Output destination

Fail if output destination for the same `<scenario_id>/<replay_id>` already exists,
unless a future explicit `--overwrite` flag is implemented. This ticket does not
require `--overwrite`.

---

## Determinism

At identical input and identical CLI arguments, all output row sets, row order,
status fields, counts, and manifest values must be identical except for
`created_at_utc`.

All output Parquets must be sorted deterministically by:

```text
scenario_id
replay_id
as_of_daily_bar_id
symbol
event_type
```

For `all_replay_symbol_diagnostics.parquet`, omit `event_type` from the sort key.

Dict, set, glob, and filesystem iteration order must not determine output order.
Chunk processing order must be derived from `replay_manifest.chunks_completed`
and then validated/sorted deterministically by chunk date if needed.

---

## Manifest: `backtest_merge_manifest.json`

Write:

```text
evaluation/backtest/exports/<scenario_id>/<replay_id>/backtest_merge_manifest.json
```

Required fields:

```json
{
  "scenario_id": "...",
  "replay_id": "...",
  "replay_run_dir": "...",
  "history_root": "...",
  "regime_labels_path": "...",
  "created_at_utc": "...",
  "analysis_start_date": "2025-06-01",
  "analysis_end_date": "2026-05-17",
  "forward_horizons": [1, 3, 5, 10, 20],
  "full_event_count": 0,
  "primary_analysis_event_count": 0,
  "diagnostics_count": 0,
  "chunk_count": 0,
  "chunks_completed": [],
  "event_count_by_month": {},
  "primary_event_count_by_month": {},
  "event_count_by_type": {},
  "primary_event_count_by_type": {},
  "event_count_by_historical_signal_bucket": {},
  "primary_event_count_by_historical_signal_bucket": {},
  "quote_volume_bucket_counts": {},
  "primary_quote_volume_bucket_counts": {},
  "btc_regime_label_counts": {},
  "primary_btc_regime_label_counts": {},
  "missing_regime_label_count": 0,
  "missing_forward_return_counts_by_horizon": {},
  "missing_signal_daily_close_count": 0,
  "missing_quote_volume_count": 0,
  "negative_quote_volume_count": 0,
  "nonfinite_numeric_values_replaced_with_null_count": 0,
  "market_cap_available": false,
  "market_cap_reason": "not_available_point_in_time",
  "liquidity_proxy_fields": [
    "signal_day_quote_volume",
    "median_quote_volume_30d",
    "median_quote_volume_90d",
    "quote_volume_bucket"
  ],
  "forward_returns_are_labels_only": true,
  "no_lookahead_signal_inputs": true,
  "validation_status": "passed",
  "validation_errors": []
}
```

If validation fails before manifest write, a partial manifest is not required.
If a manifest is written, `validation_status` must be either `"passed"` or
`"failed"` and `validation_errors` must be a list of stable error strings.

---

## Implementation notes

Preferred implementation shape:

- Keep script logic in importable functions for tests.
- Use pandas/pyarrow for Parquet reads/writes if already available in the repo.
- Use gzip/json lines handling for diagnostics.
- Cache loaded 1d OHLCV per symbol while enriching events to avoid repeated file IO.
- Reuse existing loader helpers if they support the required point-in-time slices
  without network access.
- Do not add network calls.
- Do not write to `snapshots/`.
- Do not mutate replay artifacts.

---

## Codex guardrails

- Do not change replay output generation.
- Do not patch around invalid replay artifacts by guessing missing data.
- Do not drop May 2025 events; flag them via `included_in_primary_analysis = false`
  when `analysis_start_date = 2025-06-01`.
- Do not use `signal_events_total` as total event count in chunk mode.
- Do not fetch or infer MarketCap.
- Do not treat `null` as `false`.
- Do not treat execution-disabled as execution failure.
- Do not make future returns part of signal or bucket computation.
- Do not silently accept ambiguous date or horizon inputs.
- Do not use current date/time except for `created_at_utc`.

---

## Tests

Add focused tests under:

```text
tests/backtest/
```

or, if existing repo conventions require it:

```text
tests/scripts/
```

Synthetic fixtures are sufficient. Tests must not require real Pre-1 data or
network access.

Required tests:

1. **Merge two synthetic chunks**
   - Create two chunk directories with small event Parquets and diagnostics JSONL.GZ.
   - Verify `all_replay_event_candidates.parquet` row count and deterministic order.

2. **Diagnostics join succeeds**
   - One event matches exactly one diagnostics row.
   - Verify enriched fields from diagnostics appear in `enriched_replay_events.parquet`.

3. **Missing diagnostics join fails**
   - Event has no matching diagnostics row.
   - Script fails with clear error.

4. **Duplicate diagnostics join key fails**
   - Two diagnostics rows share the same join key.
   - Script fails.

5. **Duplicate event key fails**
   - Two event rows share `(scenario_id, replay_id, symbol, as_of_daily_bar_id, event_type)`.
   - Script fails.

6. **`analysis_start_date` preserves full rows**
   - Include one May row and one June row.
   - Verify both rows remain exported.
   - Verify May row has `included_in_primary_analysis = false`.
   - Verify June row has `included_in_primary_analysis = true`.

7. **Chunk-mode total uses `signal_events_so_far`**
   - Manifest has `signal_events_so_far = 2` and `signal_events_total = 1`.
   - Two event rows exist.
   - Script passes.
   - If implementation used `signal_events_total`, this test would fail.

8. **Quote-volume bucket assignment**
   - Test all bucket boundaries:
     - `99_999.99 -> qv_lt_100k`
     - `100_000 -> qv_100k_1m`
     - `1_000_000 -> qv_1m_10m`
     - `10_000_000 -> qv_10m_100m`
     - `100_000_000 -> qv_ge_100m`
     - null / `NaN` / negative -> `qv_unknown`

9. **Forward return calculation**
   - For synthetic 1d OHLCV, verify:
     - `forward_close_return_1d`
     - `forward_close_return_3d`
   - Verify `has_forward_<N>d = false` when future close is missing.
   - Verify zero or non-finite `signal_daily_close` yields null return and `has_forward_<N>d = false`.

10. **MarketCap not required**
    - No MarketCap input exists.
    - Manifest records `market_cap_available = false`.
    - Manifest records `market_cap_reason = "not_available_point_in_time"`.

11. **Individual missing regime labels do not fail**
    - One event week joins, one event week does not.
    - Script passes and increments `missing_regime_label_count`.

12. **Missing regime label file fails**
    - `--regime-labels` path missing.
    - Script fails before output write.

13. **Input validation: invalid dates**
    - `--analysis-start-date 2025-06-01T00:00:00Z` fails.
    - `--analysis-start-date 20250601` fails.
    - `--analysis-end-date` before `--analysis-start-date` fails.

14. **Input validation: invalid horizons**
    - `--forward-horizons 1,0,3` fails.
    - `--forward-horizons 1,-3` fails.
    - `--forward-horizons 1,3.5` fails.
    - `--forward-horizons 1,,3` fails.
    - duplicate horizons fail.

15. **Non-finite numeric cleanup**
    - Synthetic OHLCV or event input contains `NaN`, `inf`, or `-inf`.
    - Output numeric fields contain nulls, not non-finite values.
    - Manifest count increments.

16. **Deterministic reproduction**
    - Run the builder twice with identical synthetic inputs in separate temp directories.
    - Compare output row order and manifest values excluding `created_at_utc`.
    - They must match exactly.

Every preflight Pflichtkategorie is covered by at least one explicit test case or
a checkable validation rule.

---

## Acceptance criteria

- AC1: `scripts/backtest/build_replay_event_dataset.py` exists and provides the
  specified CLI.
- AC2: Required CLI arguments are validated with clear fail-fast errors.
- AC3: Date and horizon inputs follow the specified contract and reject ambiguous
  values.
- AC4: The script reads only the specified replay artifact, history root, and
  regime label file. It performs no network calls.
- AC5: All chunk events are merged into `all_replay_event_candidates.parquet`.
- AC6: All chunk diagnostics are merged into `all_replay_symbol_diagnostics.parquet`.
- AC7: `enriched_replay_events.parquet` is produced with all required fields.
- AC8: Every event joins exactly one diagnostics row or the script fails.
- AC9: Replay completeness, chunk completeness, event counts, diagnostics counts,
  duplicate event keys, and duplicate diagnostics keys are all validated.
- AC10: Chunk-mode event total uses `signal_events_so_far`, not `signal_events_total`.
- AC11: `included_in_primary_analysis` flags rows without dropping any full-period rows.
- AC12: BTC regime fields are joined and missing individual weeks are counted.
- AC13: OHLCV-derived quote-volume proxy fields and buckets are added.
- AC14: MarketCap is not fetched or inferred and manifest records that it is not
  available point-in-time.
- AC15: Forward-close return labels are added for all requested horizons with
  nullable return columns and boolean `has_forward_<N>d` flags.
- AC16: Non-finite numeric values are not written as numeric-looking outputs.
- AC17: Outputs are deterministically sorted.
- AC18: `backtest_merge_manifest.json` is written with all required fields.
- AC19: Focused tests cover all required cases.
- AC20: Existing replay, chunk workflow, production adapter, scenario parser,
  and Pre-1 fetch tests continue to pass.

---

## Definition of Done

- The new script is implemented and importable.
- The CLI command from this ticket runs on synthetic fixtures in tests.
- The required output files are produced under:
  `evaluation/backtest/exports/<scenario_id>/<replay_id>/`.
- All validations are implemented fail-fast.
- All required enriched fields exist in `enriched_replay_events.parquet`.
- `backtest_merge_manifest.json` contains the required summary, validation, no-lookahead,
  MarketCap, and liquidity-proxy metadata.
- Tests listed in this ticket are implemented.
- Focused tests pass.
- Relevant existing replay/backtest tests pass.
- No replay-generation, chunking, production adapter, execution, or scenario semantics
  are changed.

---

## Preflight checklist result

This ticket was checked against the ticket template and Master-Checkliste for
codex-feste Tickets.

Template coverage:

- Title: covered
- Context / Source: covered
- Goal: covered
- Scope: covered
- Out of Scope: covered
- Canonical References: covered
- Proposed change: covered
- Codex Guardrails: covered
- Acceptance Criteria: covered
- Default-/Edgecase-Abdeckung: covered
- Tests: covered
- Constraints / Invariants: covered
- Definition of Done: covered

Codex-readiness checks:

- Missing vs invalid: explicit
- Null vs false: explicit
- Not evaluated vs failed: explicit
- `NaN` / `inf` / `-inf`: explicit
- Date input types and units: explicit
- Horizon input types and units: explicit
- Deterministic sorting: explicit
- No-lookahead boundary: explicit
- MarketCap lookahead avoidance: explicit
- Chunk-mode event count ambiguity: explicitly resolved via `signal_events_so_far`
- Scope limited to one PR: yes
- No silent overwrite of previous tickets: yes
- No second documentation authority: yes
