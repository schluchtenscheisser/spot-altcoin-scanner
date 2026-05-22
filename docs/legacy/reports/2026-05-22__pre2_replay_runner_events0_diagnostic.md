# 2026-05-22 Pre-2 replay runner `events=0` diagnostic

## Root cause summary

`scanner/evaluation/historical_replay/replay_runner.py` currently runs as a scaffold and does **not** invoke the production T5–T12 pipeline (feature bundle → axes → phase interpretation → invalidation/cycle → state machine → entry pattern → bucket decision). Instead, it writes placeholder values (`market_phase="none"`, `entry_pattern="none"`, and mostly `state_machine_state="watch"`) and never appends event rows, which deterministically yields `signal_events_total=0`.

## Diagnostic checklist findings

1. **Production modules/functions currently called from `replay_runner.py`:**
   - `HistoricalBarLoader.closed_bars_as_of`
   - `ReplayStateStore.get` / `ReplayStateStore.upsert`
   - local helpers in this module (`_map_bucket`, `get_current_daily_bar`, `has_current_day_4h_coverage`)
   - No imports from production T5–T12 modules.

2. **T4 bypass + T5–T12 invocation status:**
   - T4/live fetch is bypassed (bars are loaded from historical parquet via `HistoricalBarLoader`).
   - T5–T12 production logic is **not invoked**.

3. **`market_phase` source:**
   - Hard-coded to `"none"` in diagnostics row assembly.

4. **`state_machine_state` source:**
   - For admitted rows, hard-coded to `"watch"`.
   - For missing-data rows, copied from persisted state if available.
   - No call to production state machine.

5. **`entry_pattern` source:**
   - Hard-coded to `"none"`.

6. **`replay_event_candidates` emission source:**
   - `events` list is initialized empty and never appended.
   - File is written from this always-empty list.

7. **`replay_manifest.production_modules_used` accuracy:**
   - Manifest claims `"scanner.state.machine"` is used, but this module is not imported/called in `replay_runner.py`.
   - Field is therefore misleading in current implementation.

## Why no direct integration patch in this change

The minimal correct Pre-2 behavior requires wiring more than 2–3 production modules that are currently not imported in `replay_runner.py`:

1. `scanner.features.bundle.build_feature_bundle`
2. `scanner.axes.tier1.compute_tier1_axes`
3. `scanner.axes.tier2.compute_tier2_axes`
4. `scanner.phase.interpreter.compute_phase_interpretation`
5. `scanner.state.invalidation.compute_invalidation_and_cycle`
6. `scanner.state.machine.compute_state_machine`
7. `scanner.entry.patterns.resolve_entry_pattern`
8. `scanner.decision.buckets.assign_bucket`
9. state persistence helpers currently used by daily runner for machine context continuity

Because this exceeds the requested 2–3-module threshold, this diagnostic intentionally stops before a full integration implementation.

## Proposed minimal next patch plan (bounded)

1. Add `scanner/evaluation/historical_replay/production_adapter.py` that:
   - accepts symbol, day context, historical 1d/4h closed bars, persisted replay state/context, and scanner config;
   - calls the production chain above (no T4, no live APIs);
   - returns structured outputs: `phase`, `state_bundle`, `entry`, `decision`, and `transition metadata` needed for events.

2. Update `replay_runner.py` to:
   - use adapter outputs instead of hard-coded phase/state/entry values for admitted symbols;
   - derive `historical_signal_bucket` from production outputs;
   - emit `first_confirmed_with_entry_pattern` event when state transitions to `confirmed_ready` and `entry_pattern != "none"`.

3. Correct manifest accuracy:
   - populate `production_modules_used` from actual adapter dependency list.

4. Add focused tests (`tests/replay/test_historical_replay_runner_production_adapter.py`):
   - stub adapter to return `confirmed_ready` + non-none entry; assert one emitted event with type `first_confirmed_with_entry_pattern`;
   - stub adapter phase output (e.g., `pressure_build`) and assert diagnostics `market_phase` equals adapter output (proves no hard-coded `none`).

5. Keep hard constraints:
   - no changes to bar loader/scenario/scenario registry;
   - no live API calls;
   - no execution grading or Backtest-1 metrics.
