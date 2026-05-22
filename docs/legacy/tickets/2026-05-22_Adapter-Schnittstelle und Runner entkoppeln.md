> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

Please implement the next bounded Pre-2 patch: introduce a production-adapter boundary and remove hard-coded placeholder phase/state/entry outputs from the replay runner.

Use the diagnostic report as context:
docs/legacy/reports/2026-05-22__pre2_replay_runner_events0_diagnostic.md

Problem:
The current replay_runner.py is a scaffold. It hard-codes market_phase="none", entry_pattern="none", admitted state_machine_state="watch", initializes events=[] and never appends event rows. Therefore signal_events_total=0 is deterministic and not a market result.

Goal of this patch:
Do not yet attempt a full T5–T12 integration if that requires broad production-module refactoring. First create a clean adapter boundary and make replay_runner.py consume adapter outputs instead of hard-coded placeholders.

Implement:

1. Add a replay adapter interface/module

Create:
scanner/evaluation/historical_replay/production_adapter.py

It should define:
- a dataclass or typed return object, e.g. ReplayProductionOutput
- a default adapter callable/class, e.g. HistoricalProductionAdapter

ReplayProductionOutput must contain at least:
- disposition_status
- disposition_reason
- market_phase
- market_phase_confidence
- state_machine_state
- state_confidence
- state_transition_reason
- setup_cycle_id
- entry_pattern
- entry_pattern_score
- signal_daily_close
- transition_event_types or enough transition metadata for replay_runner to emit first_* events
- updated_state_patch or updated replay-state fields
- production_modules_used

The adapter callable/class must accept the following inputs:
- symbol: str
- as_of_daily_bar_id: str
- closed_1d_bars: pd.DataFrame  (point-in-time sliced, from HistoricalBarLoader)
- closed_4h_bars: pd.DataFrame  (point-in-time sliced, from HistoricalBarLoader)
- persisted_state: dict          (current replay state loaded from ReplayStateStore,
                                  containing bars_since_*, setup_cycle_id,
                                  close_at_early_entry_bar, etc.)
- scanner_config: dict           (loaded from scanner_config.ref)

The persisted_state input is required so the state machine can continue
from the previous day's context, not restart fresh each day. Without it,
bars_since_* fields, setup_cycle_id and all state-continuity fields would
be incorrect.

For now, if full production T5–T12 calls are not implemented in this patch, the default adapter may explicitly raise NotImplementedError with a clear message such as:
"HistoricalProductionAdapter is not wired to production T5–T12 yet"
But tests must use a stub adapter to prove the runner no longer relies on hard-coded phase/state/entry values.

2. Update replay_runner.py to accept/inject adapter

Modify run_replay so it can receive an optional adapter parameter, e.g.:

run_replay(..., production_adapter: ReplayProductionAdapterProtocol | None = None)

If no adapter is provided, instantiate the default HistoricalProductionAdapter.

The runner must:
- call the adapter for admitted/evaluable symbols,
- use adapter output for market_phase, state_machine_state, entry_pattern, confidence fields, transition metadata, and state patches,
- derive historical_signal_bucket from adapter output,
- emit event candidates from adapter transition metadata,
- no longer hard-code:
  market_phase="none"
  entry_pattern="none"
  state_machine_state="watch" for admitted symbols

3. Event emission

Implement event emission at least for adapter-provided event types.

Required behavior:
If the adapter returns a transition/event type such as:
- first_early_ready
- first_confirmed_ready
- first_confirmed_with_entry_pattern
- first_late
- first_chased
- first_rejected

then replay_runner.py appends a row to replay_event_candidates.parquet with the required Pre-2 event fields.

At minimum, add test coverage for:
- adapter returns state_machine_state="confirmed_ready" and entry_pattern="range_reclaim" plus event type "first_confirmed_with_entry_pattern"
- runner emits one event candidate with historical_signal_bucket="confirmed_candidates"
- diagnostics contain adapter-provided market_phase and entry_pattern

4. Manifest accuracy

Update replay_manifest.production_modules_used:
- It must reflect actual adapter-reported modules.
- If the default adapter is not fully wired and raises NotImplementedError, do not claim production modules were used.
- Remove misleading hard-coded ["scanner.state.machine"] unless actually imported/called.

5. Tests

Add focused tests, e.g.:
tests/replay/test_historical_replay_runner_adapter_boundary.py

Tests must prove:
- Runner uses adapter output for market_phase instead of hard-coded "none".
- Runner uses adapter output for state_machine_state instead of hard-coded "watch".
- Runner uses adapter output for entry_pattern instead of hard-coded "none".
- Runner emits replay_event_candidates when adapter provides a first_* event.
- replay_manifest.production_modules_used comes from adapter output.
- decision_bucket remains absent.
- no next_daily_open / forward_return fields are emitted.

Use tiny synthetic fixture data. Do not require real Pre-1 history or network access.

6. Scope constraints

Do not:
- modify Pre-1 fetch logic,
- modify bar_loader.py unless unavoidable,
- modify scenario.py or scenario_registry.py,
- call T4/live fetch,
- call MEXC APIs,
- compute forward returns,
- compute next_daily_open,
- implement execution grading,
- tune scanner thresholds,
- change bucket mapping semantics.

Do not copy fachliche signal logic into replay_runner.py.

7. Report

After implementation, report:
- files changed,
- whether hard-coded phase/state/entry placeholders were removed from admitted-path diagnostics,
- how adapter injection works,
- what remains for the next patch to wire the real T5–T12 production modules,
- focused pytest result.