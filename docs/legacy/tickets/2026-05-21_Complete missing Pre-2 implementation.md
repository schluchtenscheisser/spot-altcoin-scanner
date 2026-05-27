Task: Complete the missing Pre-2 Historical Daily Replay Harness implementation.

Context:
Pre-2 was only partially implemented in the previous PR. The current repo has the Scenario-YAML scaffold and scenario immutability registry, but not the actual historical daily replay harness.

Already implemented and should be reused:
- scanner/evaluation/historical_replay/__init__.py
- scanner/evaluation/historical_replay/scenario.py
- scanner/evaluation/historical_replay/scenario_registry.py
- tests/replay/test_historical_scenario.py
- scanner/tools/run_historical_daily_replay.py currently validates/registers scenarios only

Important boundary:
- Do not modify or reuse scanner/evaluation/replay.py for this work. That module is the T18 post-hoc evaluation layer over finished run artifacts. Pre-2 is a separate historical daily replay harness.
- Do not call T4, scanner/data/ohlcv_fetch.py, mexc_client, or any live API client.
- Do not compute forward returns, next_daily_open, MFE, MAE, calibration/validation reports, execution grading, or intraday replay.
- Do not emit decision_bucket anywhere in replay outputs.

Implement the missing Pre-2 scope from the approved ticket docs/legacy/tickets/2026-05-18__BACKTEST_PRE_2__historical_daily_replay_harness.md.

Required components:

1. Bar loader / point-in-time slicer
Implement a module under scanner/evaluation/historical_replay/, e.g. bar_loader.py or bar_slicer.py.

Responsibilities:
- Load Pre-1 Binance Parquet OHLCV history from history_dataset_ref.
- Support symbols and timeframes 1d / 4h.
- For a given as_of_utc, return only fully closed bars with close_time_utc <= as_of_utc.
- Never return partial/open bars.
- Never return future bars.
- Convert rows into the same closed-bar input shape expected by the production T5 feature computation or by the replay adapter.

2. Replay-local state
Implement SQLite-backed replay state under:

evaluation/replay/runs/<scenario_id>/<replay_id>/state.sqlite

Hard rules:
- No reads from live/shadow scanner state.
- No writes to live/shadow scanner state.
- No state sharing across scenario_id or scenario_config_hash.

Persist at least:
- symbol
- state_machine_state
- state_confidence
- state_transition_reason
- setup_cycle_id
- bars_since_state_entered
- bars_since_early_entered
- bars_since_confirmed_entered
- close_at_early_entry_bar
- close_at_confirmed_entry_bar
- cycle_end_timestamp
- bars_since_cycle_end
- last_aging_daily_bar_id
- freshness_distance_state_early
- freshness_distance_state_confirmed
- distance_from_ideal_entry_after_early
- distance_from_ideal_entry_after_confirmed
- last_evaluable_replay_date
- consecutive_missing_1d_bars
- consecutive_missing_4h_bars

Also include all fields from the production StatePersistencePatch dataclass or equivalent production state-persistence model that are required for state-machine continuity, unless explicitly documented as irrelevant to historical replay.

3. Replay runner
Implement the daily replay loop, e.g. replay_runner.py or historical_daily_replay.py.

Scenario hash / immutability rule:
- scenario_config_hash is computed over replay-operative scenario fields only.
- splits.calibration and splits.validation are excluded from scenario_config_hash.
- Changes to splits alone must not trigger a new scenario_id requirement.
- The replay runner must use the existing scenario_config_hash / scenario_registry behavior and must not reintroduce hashing over splits.*.

For each as_of_daily_bar_id from evaluation.start_date through evaluation.end_date:
- Compute daily_replay_run_time_utc = daily bar close + settlement_delay_seconds.
- Slice 1d bars point-in-time.
- Slice 4h bars point-in-time.
- Iterate symbols deterministically sorted ascending.
- Check warm-up eligibility:
  - at least warm_up_1d_bars closed 1d bars
  - at least warm_up_4h_bars closed 4h bars
  - signal-evaluable according to Pre-1 universe/symbol completeness
- Load previous replay-local state.
- Run production T5–T12 signal logic directly where possible, via narrow adapters if needed.
- Do not copy fachliche signal logic into replay-only modules.
- Apply disposition logic.
- Derive historical_signal_bucket via the explicit mapping below.
- Persist updated replay state.
- Emit diagnostics rows where required.
- Emit replay event candidates where applicable.

Disposition semantics:
- state_machine_state must remain null before admission / not evaluable / untracked.
- Do not introduce pseudo-state strings.
- Allowed disposition_status values:
  - admitted
  - untracked
  - not_evaluable_warmup
  - not_evaluable_missing_data

Required disposition_reason codes at minimum:
- PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE
- WARMUP_INSUFFICIENT
- MISSING_1D_BAR
- MISSING_4H_CONTEXT

Warm-up behavior:
- Do not emit one diagnostics row per symbol/day for warm-up days.
- Record warm-up only in replay_manifest.json via warmup_summary_by_symbol with first_evaluable_date and warmup_days_skipped.
- Warm-up days must not generate signal events.

Diagnostics emission:
Emit diagnostics rows for:
- admitted days,
- untracked days,
- missing-data days.

Do not emit per-symbol/per-day diagnostics rows for warm-up days.

Missing 1d behavior:
- Freeze prior state.
- Do not increment bars_since_*.
- Do not age state.
- Do not synthesize or forward-fill prices.
- Set disposition_status = not_evaluable_missing_data.
- Set disposition_reason = MISSING_1D_BAR.
- Set historical_signal_bucket = not_evaluable_missing_data.
- Increment consecutive_missing_1d_bars.

Missing 4h behavior:
- If 1d exists but 4h context is missing/incomplete:
  - data_4h_available = false or production-equivalent field
  - consecutive_missing_4h_bars increments
  - early_ready must not be produced without 4h
  - confirmed_ready without 4h only if production/v2.1 daily-only constraints allow it
  - if required inputs are absent, disposition_status = not_evaluable_missing_data and disposition_reason = MISSING_4H_CONTEXT

Aging idempotency:
Before applying any state-aging increment, compare current as_of_daily_bar_id to persisted last_aging_daily_bar_id.
- If equal: skip aging increments.
- If different and symbol is evaluable: apply exactly one aging step and set last_aging_daily_bar_id to current as_of_daily_bar_id.
Rerunning the same replay day must not increment bars_since_* twice.

4. Historical signal bucket mapping
Use this exact pre-execution mapping. Execution-conditioned live demotion rules do not apply.

- disposition_status = not_evaluable_warmup -> not_evaluable_warmup
- disposition_status = not_evaluable_missing_data -> not_evaluable_missing_data
- disposition_status = untracked -> watchlist
- state_machine_state = confirmed_ready and entry_pattern != none -> confirmed_candidates
- state_machine_state = confirmed_ready and entry_pattern = none -> late_monitor
- state_machine_state = early_ready and entry_pattern != none -> early_candidates
- state_machine_state = early_ready and entry_pattern = none -> watchlist
- state_machine_state = watch -> watchlist
- state_machine_state in {late, chased} -> late_monitor
- state_machine_state = rejected -> discarded

Do not write decision_bucket to replay diagnostics or replay_event_candidates.parquet.

5. Execution-disabled semantics
Set:
- execution_mode = disabled_historical_ohlcv_only
- execution_evaluation_status = not_evaluated_historical_ohlcv_only
- execution_status_raw = not_evaluated
- execution_size_class = not_evaluated
- execution_grade_effective = null
- is_tradeable_candidate = null

Do not use execution fields in ranking or bucket decisions.

6. Replay diagnostics
Write:

evaluation/replay/runs/<scenario_id>/<replay_id>/replay_symbol_diagnostics.jsonl.gz

Required fields include at least:
- scenario_id
- replay_id
- as_of_daily_bar_id
- symbol
- disposition_status
- disposition_reason
- state_machine_state
- state_confidence
- state_transition_reason
- setup_cycle_id
- market_phase
- market_phase_confidence
- entry_pattern
- entry_pattern_score
- historical_signal_bucket
- execution_mode
- execution_evaluation_status
- execution_status_raw
- execution_size_class
- execution_grade_effective
- is_tradeable_candidate
- signal_daily_close
- consecutive_missing_1d_bars
- consecutive_missing_4h_bars
- last_evaluable_replay_date
- data_4h_available
- data_resolution_class

Must not include:
- decision_bucket
- next_daily_open
- entry_reference_price
- forward_return_*
- MFE
- MAE

7. Event candidate export
Write:

evaluation/replay/runs/<scenario_id>/<replay_id>/replay_event_candidates.parquet

Minimum event types:
- first_early_ready
- first_confirmed_ready
- first_confirmed_with_entry_pattern
- first_late
- first_chased
- first_rejected

Required event fields:
- scenario_id
- replay_id
- symbol
- event_type
- as_of_daily_bar_id
- event_timestamp_utc
- state_machine_state
- historical_signal_bucket
- market_phase
- market_phase_confidence
- entry_pattern
- entry_pattern_score
- setup_cycle_id
- signal_daily_close
- consecutive_missing_1d_bars_at_event
- consecutive_missing_4h_bars_at_event

Do not include next_daily_open or forward returns. Backtest-1 derives next_daily_open from the Pre-1 OHLCV history dataset.

8. Replay manifest
Write:

evaluation/replay/runs/<scenario_id>/<replay_id>/replay_manifest.json

Required fields:
- manifest_type = replay_manifest
- schema_version
- scenario_id
- replay_id
- scenario_config_hash
- scenario_config_hash_excludes_splits = true
- scanner_config_hash
- scanner_config_ref
- history_dataset_ref
- history_manifest_ref
- universe_manifest_ref
- evaluation_start_date
- evaluation_end_date
- timeframes
- universe_mode
- daily_replay_time_policy
- warm_up_1d_bars
- warm_up_4h_bars
- execution_mode
- execution_evaluation_status
- t4_bypass = true
- production_modules_used
- state_store_path
- scenario_registry_path
- warmup_summary_by_symbol
- replay_symbol_diagnostics_path
- replay_event_candidates_path
- splits_recorded
- replay_days_total
- replay_days_completed
- symbols_total
- symbols_evaluable
- symbols_excluded_warmup
- signal_events_total
- created_at_utc

If splits.* exist, record them in the manifest only. Do not evaluate them.

9. CLI
Extend the existing scanner/tools/run_historical_daily_replay.py to run the full replay after validating and registering the scenario.

Keep:
- --scenario
- --output-root if needed as technical root
- --dry-run-validate-scenario

Do not add ad-hoc overrides for scenario-defining parameters.

If repo convention requires a scripts/ entrypoint, add a thin wrapper only. Do not create competing CLIs with divergent behavior.

Also ensure Scenario-YAML validation failures are consistently reported as clean validation errors by the CLI. Do not allow raw tracebacks for ValueError paths from scenario parsing.

10. Tests
Add focused tests for:
- point-in-time 1d slicing
- point-in-time 4h slicing
- warm-up manifest summary without per-row warm-up diagnostics
- admitted / untracked / missing-data diagnostics emission
- missing 1d freezes state and does not age bars_since_*
- last_aging_daily_bar_id prevents duplicate aging on replay rerun
- missing 4h blocks early_ready
- execution-disabled fields
- no decision_bucket in diagnostics or event candidates
- historical_signal_bucket mapping, including untracked -> watchlist
- replay_event_candidates schema and no next_daily_open / no forward returns
- replay_manifest required fields
- replay-state isolation from live/shadow state
- deterministic ordering
- T4/MEXC client not called
- import side-effect guard for production modules where practical
- CLI clean validation failures, no traceback

Scope constraints:
- Do not modify scanner/evaluation/replay.py.
- Do not modify Pre-1 fetch logic.
- Do not fetch Binance data.
- Do not call MEXC.
- Do not compute next_daily_open, forward returns, MFE, MAE.
- Do not implement intraday replay.
- Do not implement calibration/validation analysis.

Report:
- files added/changed,
- which production modules/adapters are used for T5–T12,
- test coverage added,
- focused pytest result,
- full pytest result if run.