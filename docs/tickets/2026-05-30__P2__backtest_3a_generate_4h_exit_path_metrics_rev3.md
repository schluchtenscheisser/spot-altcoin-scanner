# [P2] BACKTEST-3A — Generate 4h Exit Path Metrics for Primary Trade Scope v0

> Place this ticket in `docs/tickets/`.
> Before implementation, apply the ticket preflight loop.
> Language: English.

## Implementation Notes

### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

> Goal: Codex must not have to infer business semantics. Defaults, missing keys, nullability, and "not evaluated" vs. "evaluated but failed" are explicitly defined and tested below.

#### A) Defaults / Config-Semantik
- [x] This ticket may add CLI/script parameters. All defaults are explicitly specified in this ticket.
- [x] Missing optional CLI flags use the defaults defined here.
- [x] Invalid CLI values fail preflight before any output files are written.
- [x] No raw-dict config fallback is introduced.
- [x] If existing repo config accessors are reused, they must use the existing central config/default mechanism and must not introduce parallel defaults.

#### B) Nullability / Schema / Output
- [x] Nullable output fields are explicitly listed.
- [x] `null` means "not reliably evaluable" and must not be coerced to `false`, `0`, or an empty string.
- [x] Non-finite numerical values (`NaN`, `inf`, `-inf`) must not be emitted as valid numerical metric values.

#### C) Edgecases
- [x] `path_not_evaluated`, `path_partial`, and `path_evaluated` are separate statuses.
- [x] Reference-price availability is separate from 4h-path availability.
- [x] ATR availability is diagnostic only in this ticket and does not trigger exit simulation.
- [x] Strict preflight must complete before writes; failed preflight leaves zero partial output files.

#### D) Tests
- [x] Concrete unit, integration, fixture, and deterministic reproducibility tests are listed below.
- [x] Preflight against canonical/repo/ticket drift is part of Definition of Done.

---

## Title

[P2] BACKTEST-3A — Generate 4h Exit Path Metrics for Primary Trade Scope v0

## Context / Source

The historical replay and BACKTEST-2 actionable segment report identified a preliminary **Primary Trade Scope v0** for initial exit-analysis work:

- `early_candidates × base_reclaim`
- `confirmed_candidates × ema_reclaim`
- `early_candidates × early_reversal_break`

This scope is documented as an empirical trading-scope hypothesis, not as a v2.1 specification change and not as an automatic live-trading permission.

The exit-strategy handover established that the scanner's strongest empirical edge is short-term:

- strongest horizon: 1d–3d
- 5d: possible stretch horizon
- 10d/20d: not a primary target horizon without active exit logic

Existing forward-return reports only provide endpoint labels. They do not provide the 4h path data needed to calibrate stop-loss, partial profit-taking, trailing, or time-stop logic.

The repository already contains `docs/canonical/BACKTEST/TRADE_MODEL_4H_IMMEDIATE_RETEST.md` as an `analytics_only` model. That model must be treated as a future baseline for later simulation, not as an already validated live-exit rule.

This ticket is therefore **BACKTEST-3A**: data production and path-metric generation only.

## Goal

Generate deterministic 4h post-signal path metrics for all events in the Primary Trade Scope v0 so that a later ticket can empirically simulate exit variants.

After this ticket, we must be able to answer, per event and per segment:

- Was enough 4h OHLCV available after the signal?
- Which reference price was used?
- What was the maximum favorable excursion (MFE) over the path?
- What was the maximum adverse excursion (MAE) over the path?
- At which 4h bar did MFE and MAE occur?
- How did returns evolve by 4h bar after signal?
- Is 4h ATR available for later stop-model simulation?

This ticket must **not** choose a final exit rule.

## Scope

Allowed implementation areas:

- `evaluation/backtest/` scripts, helpers, reports, and exports
- new or existing BACKTEST-3A script entrypoint under the repo's established evaluation/backtest structure
- tests/fixtures for the new analysis
- documentation updates only where needed to describe the new analysis artifact

Expected input dataset:

```text
evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/enriched_replay_events.parquet
```

Expected historical 4h OHLCV source:

- Use the repository's existing historical OHLCV storage/access pattern.
- If the repo already has a canonical helper for loading 4h OHLCV history, reuse it.
- Do not invent a second OHLCV path convention.

Expected output directory:

```text
evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/
```

Required output files:

```text
exit_path_metrics_4h.parquet
exit_path_metrics_4h.csv
exit_path_metrics_4h_summary.json
exit_path_metrics_4h_report.md
exit_path_returns_by_bar.parquet
exit_path_returns_by_bar.csv
```

The exact script name is implementation-local, but it must be discoverable from the report and documented in the report header.

## Out of Scope

Do not implement in this ticket:

- live trading rules
- production scanner exit logic
- order placement logic
- MEXC execution simulation
- slippage or fee simulation
- stop/partial/trailing sweeps
- final time-stop selection
- segment-specific live parameters
- changes to decision buckets, state machine, phase interpreter, or entry-pattern logic
- promotion of `late_monitor` into tradable scope
- changes to `TRADE_MODEL_4H_IMMEDIATE_RETEST.md` semantics

`late_monitor` may be mentioned in the report as explicitly out of scope. It must not be mixed into the Primary Trade Scope metrics.

## Canonical References (important)

Current authoritative/reference context for this ticket:

- `docs/decision_notes/2026-05-27__initial_trade_scope_v0_segment_decision_note.md`
- `docs/canonical/BACKTEST/TRADE_MODEL_4H_IMMEDIATE_RETEST.md`
- `evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/actionable_segment_report.md`
- `evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/actionable_segment_report.json`
- v2.1 specification section files and `independence_release_gesamtkonzept_final.md` remain the primary architecture authority where applicable.

Authority rule:

> If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents continue to apply only to the extent that they do not contradict that reference set.

This ticket must not create a second competing document authority. The output report is an evaluation artifact, not a canonical spec update.

## Proposed change (high-level)

### Before

BACKTEST-1 and BACKTEST-2 provide endpoint forward-return labels and segment summaries. They do not provide 4h path-level information after each signal event.

### After

A BACKTEST-3A evaluation artifact exists that provides 4h post-signal path metrics for the three Primary Trade Scope v0 segments.

### Edge cases

- Missing 4h OHLCV does not silently drop events.
- Insufficient 4h coverage is flagged explicitly.
- Missing reference price is flagged separately from missing 4h data.
- ATR availability is diagnostic only and does not imply that an ATR stop has been simulated.
- Non-finite numerical inputs are treated as invalid/not evaluable, never as valid metric values.

### Backward compatibility impact

- No existing report schema is changed.
- No production scanner behavior is changed.
- No canonical exit rule is introduced.
- The new files are additive evaluation outputs.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> This section is an execution instruction for Codex. If anything here is ambiguous, update the ticket before implementation. Do not guess.

### Config / CLI defaults

If a new script or CLI is added, it must expose or internally use these defaults:

```text
input_events_path = evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/enriched_replay_events.parquet
scenario_id = hsq_replay_2025_05_to_2026_05_v1
replay_id = 2026-05-24T21-27-31Z
bar_timeframe = 4h
path_bars = 42
primary_only = true
output_dir = evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h
strict_preflight = true
```

Missing optional CLI flags use these defaults.

Invalid values fail preflight before any writes:

- `path_bars` must be an integer in `[1, 240]`; default is `42`.
- `bar_timeframe` must be exactly `4h` for this ticket.
- `input_events_path` must exist and be readable.
- `output_dir` must either not exist or be safely replaceable according to existing repo conventions. If existing repo conventions do not define overwrite behavior, fail unless an explicit `--overwrite` flag is provided.

No `include_late_monitor` CLI/config flag is introduced by BACKTEST-3A. If an implementation nevertheless exposes such a flag, `include_late_monitor = true` is not supported in this ticket and must fail preflight with a clear error before any writes.

No nested config block is introduced by this ticket. If Codex chooses to add one, partial overrides must merge field-by-field with the defaults above; invalid supplied values must fail clearly.

### Input semantics / units / rejection rules

Allowed input types and units:

- event timestamps: timezone-aware UTC timestamps or parseable ISO-8601 strings with explicit timezone; unit is absolute UTC time.
- OHLCV timestamps: existing repo canonical timestamp representation; if raw integer timestamps are accepted by existing helpers, their unit must be the existing repo unit only and must not be guessed.
- price fields: positive finite floats in quote currency terms.
- return fields: percentage points, e.g. `5.0` means `+5.0%`, not `0.05`.
- bar index fields: integer offset from the first eligible post-signal 4h bar; first bar offset is `1`.

Hard rejection / not-evaluable rules:

- Naive datetimes are forbidden unless an existing repo helper already canonicalizes them to UTC with explicit documented semantics. If not documented, fail preflight or mark the event not evaluable.
- Ambiguous raw numeric timestamps with unknown unit are forbidden.
- Zero or negative reference prices are invalid.
- `NaN`, `inf`, and `-inf` are invalid numerical inputs and must not propagate to numerical outputs.
- Empty OHLCV frames are `path_not_evaluated`, not `path_evaluated`.

Required ticket-level statement:

> Allowed input types, units, coercion rules, and hard rejection rules are fully specified. Ambiguous inputs must not be silently reinterpreted.

### Primary Trade Scope filter

A row is in scope if and only if it matches one of these pairs:

```text
(decision_bucket == "early_candidates"     and entry_pattern == "base_reclaim")
(decision_bucket == "confirmed_candidates" and entry_pattern == "ema_reclaim")
(decision_bucket == "early_candidates"     and entry_pattern == "early_reversal_break")
```

If the existing dataset uses equivalent but differently named columns, Codex must map them explicitly in the script and document the mapping in the report header. Do not use fuzzy matching.

Rows outside those three pairs are out of scope for primary metrics.

`segment_key` is constructed as `{decision_bucket}__{entry_pattern}` (double underscore separator). It must be computed deterministically from these two fields for every output row. Example: `early_candidates__base_reclaim`.

### Reference price policy

Reference price selection must be deterministic and auditable.

For each event, select exactly one `reference_price` and one `reference_price_source` using this order:

1. Reuse the existing repo/T30 signal reference-price helper if it exists and is applicable to replay events.
2. Else, use `signal_reference_price` if the column exists and is a positive finite number.
3. Else, use `entry_reference_price` if the column exists and is a positive finite number.
4. Else, if `state_machine_state == "early_ready"` or `decision_bucket == "early_candidates"`, use `close_at_early_entry_bar` if the column exists and is a positive finite number.
5. Else, if `state_machine_state == "confirmed_ready"` or `decision_bucket == "confirmed_candidates"`, use `close_at_confirmed_entry_bar` if the column exists and is a positive finite number.
6. Else, use the event close price only if a clearly named event close column exists and is a positive finite number. The accepted names are `close`, `close_price`, or `signal_close`. If more than one exists and values differ, fail the row as `reference_price_status = "ambiguous"` instead of choosing silently.
7. Else, set `reference_price = null`, `reference_price_status = "missing"`, and keep the row in the output.

Allowed `reference_price_status` values:

```text
available
missing
invalid
ambiguous
```

Allowed `reference_price_source` values:

```text
t30_helper
signal_reference_price
entry_reference_price
close_at_early_entry_bar
close_at_confirmed_entry_bar
event_close
null
```

`reference_price` is nullable. `null` means "not reliably evaluable" and must not be coerced to `0` or `false`.

If `reference_price_status = "ambiguous"`, set `reference_price_source = "null"` and keep the row in the output with nullable percentage metrics.

If `reference_price_status != "available"`, percentage path metrics for that row must be `null`, but path coverage diagnostics may still be computed.

### 4h path anchoring policy

The 4h path must use only completed 4h bars after the signal event.

For each event:

- identify the signal timestamp using the existing event timestamp semantics;
- select the first completed 4h bar that starts at the first canonical 4h boundary at or after the signal timestamp;
- if the signal timestamp falls inside an already-open 4h bar, do not use that in-progress bar; use the next 4h bar instead;
- if the signal timestamp is exactly on a canonical 4h boundary, the bar opening at that boundary is the first eligible path bar;
- if a canonical repo bar-clock helper exists, use it and document the helper name in the report.

No lookahead is allowed before the signal timestamp.

Required per-event diagnostics:

```text
path_bar_1_timestamp
path_bar_1_open
path_bar_1_close
path_bar_1_high
path_bar_1_low
available_path_bars
required_path_bars
path_coverage_ratio
path_coverage_status
```

`path_bar_1_*` fields always refer to the first 1-based bar of the evaluated 4h path, not to a signal-open condition.

Allowed `path_coverage_status` values:

```text
path_evaluated              available_path_bars >= required_path_bars
path_partial                1 <= available_path_bars < required_path_bars
path_not_evaluated          no post-signal 4h bars available or OHLCV not loadable
path_failed_invalid_input   required event inputs are invalid/ambiguous
```

Do not collapse `path_partial` into failure. Do not silently drop `path_not_evaluated` rows.

### MFE / MAE definitions

For each event with `reference_price_status = "available"` and at least one valid post-signal 4h bar:

```text
mfe_pct = max(high_4h[1..N] / reference_price - 1) * 100
mae_pct = min(low_4h[1..N] / reference_price - 1) * 100
```

Where:

- `N = min(available_path_bars, required_path_bars)`
- bars are completed 4h bars after the signal anchor
- `high_4h` and `low_4h` must be positive finite numbers

Output bar indices:

```text
mfe_bar_index_4h = first 1-based bar index where mfe_pct occurs
mae_bar_index_4h = first 1-based bar index where mae_pct occurs
time_to_mfe_hours = mfe_bar_index_4h * 4
time_to_mae_hours = mae_bar_index_4h * 4
```

If the metric cannot be evaluated, output `null` for the metric and a reason code.

### Return path by bar

Create a long-form bar-level output with one row per event per available 4h bar up to `path_bars`.

Required columns:

```text
event_id
symbol
segment_key
decision_bucket
entry_pattern
signal_timestamp
bar_index_4h
bar_timestamp
open_4h
high_4h
low_4h
close_4h
return_open_pct
return_high_pct
return_low_pct
return_close_pct
reference_price
reference_price_source
reference_price_status
```

Percentage returns are nullable and must be `null` if `reference_price_status != "available"`.

### ATR diagnostic only

This ticket may compute or expose 4h ATR diagnostics for later BACKTEST-3B work, but must not simulate ATR stops.

Required event-level ATR fields:

```text
atr_4h_available
atr_4h_value
atr_4h_period
atr_4h_source
```

Defaults:

```text
atr_4h_period = 14
```

Allowed `atr_4h_source` values:

```text
existing_feature
computed_from_4h_ohlcv
not_available
```

If insufficient prior 4h bars exist to compute ATR(14), set:

```text
atr_4h_available = false
atr_4h_value = null
atr_4h_source = "not_available"
```

`atr_4h_source` is a non-null enum field. It must use the string literal `not_available` when ATR cannot be computed, not Python `None` / JSON `null`.

Do not approximate ATR from daily bars in this ticket.

### No exit simulation in BACKTEST-3A

This ticket must not implement:

- stop-hit simulation
- partial-hit simulation
- trailing-stop simulation
- time-stop outcome selection
- P&L computation
- win/loss trade classification

The report may include a short section named `Prepared for BACKTEST-3B` listing which future simulations the produced fields support. That section must be descriptive only.

### Determinism

Output order must be deterministic:

Event-level outputs sort by:

```text
signal_timestamp ASC, symbol ASC, decision_bucket ASC, entry_pattern ASC, event_id ASC
```

Bar-level outputs sort by:

```text
signal_timestamp ASC, symbol ASC, event_id ASC, bar_index_4h ASC
```

If `event_id` does not exist in the input, create a stable deterministic event id using a hash over these fields, if present:

```text
scenario_id, replay_id, symbol, signal_timestamp, decision_bucket, entry_pattern, setup_cycle_id
```

If any hash input is missing, use the literal string `NULL` for that component. Do not use random or time-based suffixes.

### Strict preflight / atomic writes

When `strict_preflight = true`:

- validate input path exists;
- validate required in-scope filter columns or explicit mappings exist;
- validate timestamp parsing policy;
- validate output directory overwrite policy;
- validate that OHLCV loader can be initialized;
- validate all enum/default values.

If preflight fails, write zero output files.

For successful runs, write outputs atomically according to existing repo conventions. If no convention exists, write to a temp directory and move into final location only after all files are complete.

## Implementation Notes (optional but useful)

### Dataflow

1. Load enriched replay events.
2. Filter to Primary Trade Scope v0.
3. Determine deterministic `event_id` where needed.
4. Resolve reference price per event.
5. Load 4h OHLCV path per symbol/event.
6. Compute path coverage diagnostics.
7. Compute MFE/MAE and return path metrics where evaluable.
8. Compute or expose ATR(14) 4h diagnostics if possible.
9. Write event-level and bar-level outputs.
10. Write JSON summary and Markdown report.

### Recommended report sections

`exit_path_metrics_4h_report.md` should include:

- run metadata
- input/output paths
- Primary Trade Scope filter definition
- row counts by segment
- path coverage summary by segment
- reference-price source summary by segment
- MFE/MAE median, p25, p75 by segment
- time-to-MFE/time-to-MAE median by segment
- ATR availability summary by segment
- explicit statement: `No exit simulation was performed in BACKTEST-3A.`
- explicit statement: `late_monitor was not included in Primary Trade Scope metrics.`

### Summary JSON minimum schema

`exit_path_metrics_4h_summary.json` must include at least:

```json
{
  "scenario_id": "hsq_replay_2025_05_to_2026_05_v1",
  "replay_id": "2026-05-24T21-27-31Z",
  "analysis_id": "BACKTEST-3A_EXIT_PATH_METRICS_4H",
  "bar_timeframe": "4h",
  "required_path_bars": 42,
  "primary_scope_segments": [
    "early_candidates__base_reclaim",
    "confirmed_candidates__ema_reclaim",
    "early_candidates__early_reversal_break"
  ],
  "late_monitor_included": false,
  "exit_simulation_performed": false,
  "counts": {},
  "coverage_by_segment": {},
  "reference_price_by_segment": {},
  "atr_4h_by_segment": {}
}
```

Additional fields are allowed if deterministic and documented.

## Acceptance Criteria (deterministic)

1. A BACKTEST-3A script or equivalent evaluation entrypoint exists and can generate the required outputs for the specified replay dataset.
2. The implementation filters exactly the three Primary Trade Scope v0 segment pairs and excludes `late_monitor` from primary metrics.
3. The event-level output contains one row per in-scope event, including rows with missing reference price or insufficient 4h coverage.
4. The bar-level output contains one row per available post-signal 4h bar per in-scope event, capped at `path_bars = 42` by default.
5. Reference-price resolution follows the ordered policy in this ticket and emits `reference_price`, `reference_price_source`, and `reference_price_status` for every event.
6. 4h path anchoring uses completed post-signal 4h bars only and emits first-bar diagnostics for every event where at least one post-signal bar exists.
7. MFE and MAE are computed exactly from post-signal 4h highs/lows versus `reference_price`, using percentage-point units.
8. MFE/MAE timing fields use 1-based 4h bar indices and hour offsets equal to `bar_index * 4`.
9. Non-evaluable metrics are emitted as `null` with explicit status/reason fields; they are not coerced to `0`, `false`, or empty strings.
10. ATR(14) 4h diagnostics are emitted if possible; missing ATR is flagged and does not fail the event.
11. No stop/partial/trailing/time-stop simulation or P&L classification is implemented in this ticket.
12. Output ordering is deterministic and stable across repeated runs with identical inputs.
13. Strict preflight failures produce zero partial output files.
14. The Markdown report explicitly states that BACKTEST-3A is data production only and not a live-trading or exit-rule decision.
15. The JSON summary includes counts, path coverage, reference-price status, and ATR availability summaries by segment.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ (AC: 1, 4; Tests: `test_cli_defaults_path_bars_42`, `test_default_primary_only_true`)
- **Config Invalid Value Handling:** ✅ (AC: 13; Tests: `test_invalid_path_bars_fails_preflight`, `test_invalid_timeframe_fails_preflight`, `test_include_late_monitor_true_fails_preflight_if_exposed`)
- **Nullability / kein bool()-Coercion:** ✅ (AC: 9, 10; Tests: `test_missing_reference_price_outputs_null_metrics`, `test_missing_atr_outputs_not_available_source`)
- **Not-evaluated vs failed getrennt:** ✅ (AC: 3, 6, 9; Tests: `test_no_ohlcv_path_not_evaluated`, `test_invalid_timestamp_path_failed_invalid_input`)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (AC: 13; Test: `test_preflight_failure_writes_no_files`)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (AC: 12; Test: `test_missing_event_id_generates_stable_hash`)
- **Deterministische Sortierung/Tie-breaker:** ✅ (AC: 12; Test: `test_repeated_runs_identical_output_order`)
- **Input semantics / units / coercion / rejection:** ✅ (AC: 5, 6, 7, 8, 13; Tests: `test_naive_datetime_rejected_or_marked_invalid`, `test_ambiguous_event_close_columns_mark_reference_ambiguous`)
- **No lookahead / closed-candle-only:** ✅ (AC: 6; Tests: `test_signal_inside_4h_bar_uses_next_bar`, `test_signal_on_4h_boundary_uses_boundary_bar`)
- **No exit simulation in 3A:** ✅ (AC: 11, 14; Test: `test_no_exit_outcome_columns_present`)

## Tests (required if logic changes)

### Unit

Add tests for the following concrete cases:

1. `test_primary_scope_filter_exact_pairs`
   - Input contains the three primary pairs plus `late_monitor`, `watchlist`, and Secondary/Observe pairs.
   - Expected: only the three primary pairs remain in primary outputs.

2. `test_reference_price_priority_signal_reference_price`
   - Event has `signal_reference_price`, `entry_reference_price`, and event close.
   - Expected: `signal_reference_price` wins, source is `signal_reference_price`.

3. `test_reference_price_confirmed_fallback`
   - Confirmed event lacks explicit signal reference price but has `close_at_confirmed_entry_bar`.
   - Expected: reference price uses `close_at_confirmed_entry_bar`.

4. `test_ambiguous_event_close_columns_mark_reference_ambiguous`
   - Event has `close` and `signal_close` with different positive finite values and no higher-priority reference field.
   - Expected: `reference_price_status = "ambiguous"`, `reference_price_source = "null"`, percentage metrics are `null`.

5. `test_non_finite_reference_price_invalid`
   - Reference price is `NaN`, `inf`, or `-inf`.
   - Expected: `reference_price_status = "invalid"`, metrics are `null`.

6. `test_mfe_mae_math_from_4h_high_low`
   - Reference price = `100`, highs `[103, 108]`, lows `[98, 95]`.
   - Expected: `mfe_pct = 8.0`, `mae_pct = -5.0`, first occurrence indices are correct.

7. `test_first_mfe_mae_occurrence_wins_tie`
   - Same max high or min low occurs in multiple bars.
   - Expected: first 1-based bar index is emitted.

8. `test_atr_insufficient_history_outputs_not_available`
   - Fewer than required prior 4h bars are available.
   - Expected: `atr_4h_available = false`, `atr_4h_value = null`, `atr_4h_source = "not_available"`.

9. `test_missing_event_id_generates_stable_hash`
   - Input lacks event id.
   - Expected: stable deterministic id is identical across runs.

10. `test_signal_inside_4h_bar_uses_next_bar`
    - Signal timestamp falls inside an already-open 4h bar.
    - Expected: that in-progress bar is not used; the next 4h bar is the first path bar.

11. `test_signal_on_4h_boundary_uses_boundary_bar`
    - Signal timestamp is exactly on a canonical 4h boundary.
    - Expected: the bar opening at that boundary is the first path bar.

12. `test_naive_datetime_rejected_or_marked_invalid`
    - Event timestamp is naive and no repo helper documents UTC conversion.
    - Expected: preflight failure or row `path_failed_invalid_input`, with no silent timezone assumption.

### Integration

1. `test_backtest_3a_fixture_outputs_all_required_files`
   - Run the script on a small fixture with at least three symbols and at least one event per primary segment.
   - Expected: all required output files are produced.

2. `test_backtest_3a_fixture_keeps_insufficient_coverage_rows`
   - Fixture includes one event with only 3 available post-signal 4h bars.
   - Expected: row remains in event output with `path_coverage_status = "path_partial"`.

3. `test_backtest_3a_fixture_no_ohlcv_not_silent_drop`
   - Fixture includes one symbol with no OHLCV path.
   - Expected: row remains in event output with `path_coverage_status = "path_not_evaluated"`.

4. `test_preflight_failure_writes_no_files`
   - Run with invalid `path_bars = 0` or invalid timeframe.
   - Expected: command fails and output directory remains absent or unchanged.

5. `test_include_late_monitor_true_fails_preflight_if_exposed`
   - If the implementation exposes an `include_late_monitor` flag/config, run it with `true`.
   - Expected: command fails preflight with a clear unsupported-scope error and writes no files.

6. `test_repeated_runs_identical_output_order`
   - Run twice on identical fixture.
   - Expected: event-level and bar-level outputs have identical row order and identical content.

### Golden fixture / verification

Create or update a small deterministic fixture under the existing test fixture conventions. The fixture must include:

- one event for each Primary Trade Scope segment;
- one event outside Primary Scope;
- one `late_monitor` event;
- one event with missing reference price;
- one event with partial 4h coverage;
- one event with insufficient ATR history;
- deterministic 4h OHLCV where MFE/MAE can be manually verified.

No scoring/threshold/curve behavior is changed by this ticket. Therefore `docs/canonical/VERIFICATION_FOR_AI.md` does not need to be updated unless the existing repo policy requires it for all new evaluation artifacts.

## Constraints / Invariants (must not change)

- [ ] Closed-candle-only: use completed 4h bars after the signal anchor only.
- [ ] No lookahead before the signal timestamp.
- [ ] Do not modify production scanner decision logic.
- [ ] Do not modify bucket definitions or Primary Trade Scope decision note semantics.
- [ ] Do not treat `late_monitor` as tradable Primary Scope.
- [ ] Do not simulate exit rules in BACKTEST-3A.
- [ ] Do not use daily ATR as a substitute for missing 4h ATR.
- [ ] Do not silently drop non-evaluable rows.
- [ ] Do not coerce `null` metrics to `0`, `false`, or empty string.
- [ ] Do not emit non-finite numerical values as metric outputs.
- [ ] Keep output additive; do not alter existing BACKTEST-1/BACKTEST-2 outputs.
- [ ] Maintain deterministic ordering and deterministic event id generation.

---

## Definition of Done (Codex must satisfy)

(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria.
- [ ] Added or updated tests listed in this ticket, or equivalent tests with the same explicit cases.
- [ ] Generated BACKTEST-3A outputs for the target replay dataset.
- [ ] Verified that the report explicitly says no exit simulation was performed.
- [ ] Verified that `late_monitor` is excluded from Primary Trade Scope metrics.
- [ ] Verified that rows with missing reference price or missing/partial 4h coverage remain in output with explicit statuses.
- [ ] Verified deterministic repeated output on the fixture.
- [ ] Updated canonical docs under `docs/canonical/` only if required by existing repo policy for new evaluation artifacts.
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` only if required by repo policy; no scoring/threshold/curve behavior is changed in this ticket.
- [ ] PR created: exactly **1 ticket → 1 PR**.
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created.

---

## Metadata

```yaml
created_utc: "2026-05-30T00:00:00Z"
priority: P2
type: feature
owner: codex
analysis_id: BACKTEST-3A_EXIT_PATH_METRICS_4H
scenario_id: hsq_replay_2025_05_to_2026_05_v1
replay_id: 2026-05-24T21-27-31Z
related_decision_note: docs/decision_notes/2026-05-27__initial_trade_scope_v0_segment_decision_note.md
related_future_ticket: BACKTEST-3B__simulate_exit_model_variants
related_issues: []
```
