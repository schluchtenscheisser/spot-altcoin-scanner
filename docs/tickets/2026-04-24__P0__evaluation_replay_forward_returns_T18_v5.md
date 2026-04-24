# 2026-04-24__P18__evaluation_replay_forward_returns

Status: Draft for review  
Project: Independence-Release / MEXC Spot Altcoin Scanner  
Ticket: 18  
Title: Evaluation Replay + Forward Returns + MFE/MAE  
Depends on: Tickets 13, 14, 15, 17  
Primary implementation area: `scanner/evaluation/`

---

## 1. Authoritative reference set

The authoritative reference set for this ticket is:

1. The seven v2.1 section documents:
   - Abschnitt 1: Tier-1 axes
   - Abschnitt 2: Tier-2 simplified axes
   - Abschnitt 3: Phase interpreter
   - Abschnitt 4: State machine
   - Abschnitt 5: Invalidation + setup cycle
   - Abschnitt 6: Daily vs intraday update policy
   - Abschnitt 7: Entry-pattern resolution + decision buckets
2. `independence_release_gesamtkonzept_final.md`
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`
4. `docs/canonical/open_questions.md`
5. `docs/canonical/feature_enhancements.md`
6. The ticket template and preflight checklist
7. The already implemented repo reality after Tickets 1-17

If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents continue to apply only insofar as they do not contradict this reference set.

Existing repo paths/helpers may be reused if they are consistent with the current authoritative reference set. Do not introduce a second competing implementation truth.

---

## 2. Goal

Implement the first canonical Independence-Release evaluation layer for deterministic replay, signal-event forward-return measurement, MFE/MAE measurement, and transition lead-time analysis.

The evaluation layer must answer questions such as:

- Does `early_ready` appear before the main move?
- Does `confirmed_ready` have better forward-return and MFE/MAE profiles than `watch`?
- How often does `watch -> early_ready -> confirmed_ready` occur within the same `setup_cycle_id`?
- How quickly do active opportunities decay into `late`, `chased`, or `rejected`?
- Are daily and intraday scanner outputs evaluation-compatible without changing scanner business logic?

This ticket must not add or modify scanner decision logic. It reads canonical run snapshots and OHLCV history and produces evaluation artifacts.

---

## 3. Non-goals

Do not implement or change:

- Phase interpretation logic
- Tier-1 or Tier-2 axis logic
- Invalidation, cycle, freshness, or state-machine logic
- Entry-pattern logic
- Execution subset, execution grading, or orderbook logic
- Decision-bucket, ranking, or reason-code logic
- Daily runner or intraday runner behavior
- OHLCV long-term storage architecture beyond using the canonical Ticket-14 target
- `dist_to_base_mid_pct`
- Legacy backtest/ENTER/WAIT/NO_TRADE business-golden behavior
- Terminal-event forward returns from `first_late`, `first_chased`, or `first_rejected`

The evaluation layer is read-only with respect to scanner business outputs.

---

## 4. Canonical input sources

### 4.1 Replay input: run snapshots

Replay must reconstruct event timelines from canonical point-in-time run artifacts under:

```text
snapshots/runs/YYYY/MM/DD/<run_id>/
```

These snapshots are the primary replay truth for state, bucket, cycle, and diagnostic observations.

`reports/` is not a primary evaluation input. `reports/index/` may be used only as a navigation convenience to discover run paths. No business/evaluation state may be derived from `report.json` or markdown/xlsx comfort reports.

### 4.2 OHLCV input: history Parquet

Forward returns, MFE, and MAE must read OHLCV from the canonical long-term history store introduced by Ticket 14:

```text
snapshots/history/ohlcv/timeframe=<tf>/symbol=<symbol>/year=<yyyy>/month=<mm>/
```

For this ticket, Parquet under `snapshots/history/ohlcv/` is the only canonical OHLCV long-term storage target. SQLite must not be treated as the long-term OHLCV history source for evaluation.

### 4.3 No live-state replay source

Do not use live SQLite state persistence as the primary replay source. SQLite may be used only if existing helpers are necessary to locate metadata, and only if doing so does not replace the archived point-in-time run truth from `snapshots/runs/`.

Replay must be reproducible from archived run snapshots and archived OHLCV history.

---

## 5. Documentation updates required in this ticket

### 5.1 Resolve `open_questions.md` §2

`docs/canonical/open_questions.md` currently still describes long-term OHLCV history storage as open/transitional. This ticket must update that section to resolved status if the repo contains the Ticket-14 canonical Parquet history implementation.

Required updated meaning:

- Status: resolved by Ticket 14.
- Canonical OHLCV long-term storage: `snapshots/history/ohlcv/timeframe=<tf>/symbol=<symbol>/year=<yyyy>/month=<mm>/`.
- SQLite is not the canonical long-term OHLCV history store.
- T18 evaluation reads forward-looking OHLCV data from the canonical Parquet history store.

This is a narrow canonical cleanup only. Do not perform a broader open-questions refactor.

### 5.2 Add deferred enhancement for terminal-event returns

Add the following deferred topic to `docs/canonical/feature_enhancements.md`:

```markdown
- **Terminal-event forward returns for decay / invalidation states**
  - Source context: Ticket 18 records terminal events (`first_late`, `first_chased`, `first_rejected`) for transition and lead-time analysis, but does not calculate forward returns, MFE, or MAE from those events.
  - Current handling: terminal events are timestamp/provenance records only.
  - Reason for deferral: these events are not entry signals; returns from them would answer a separate counterfactual question and could be confused with signal-event quality metrics.
  - Future enhancement scope:
    - define the analytical question for terminal-event returns
    - define reference-price semantics for each terminal event
    - decide whether terminal-event returns belong in separate exports
    - ensure they cannot be mixed with signal-event forward-return metrics
```

---

## 6. Modules and artifact paths

Implement or extend modules under `scanner/evaluation/`.

Suggested module ownership:

```text
scanner/evaluation/replay.py           # reconstruct event timelines from snapshots/runs
scanner/evaluation/forward_returns.py  # forward returns, MFE, MAE from OHLCV history
scanner/evaluation/dataset_export.py   # deterministic export writing
scanner/evaluation/diagnostics.py      # optional helper for evaluation diagnostics if useful
```

Do not introduce evaluation logic inside runners, decision, state, execution, or output modules unless only wiring existing data paths is required.

### 6.1 Evaluation artifact locations

Use:

```text
evaluation/replay/
  event_timeline.jsonl
  replay_manifest.json
  replay_diagnostics.json

evaluation/exports/
  signal_event_metrics.parquet
  terminal_event_timeline.parquet
  transition_lead_times.parquet
  evaluation_summary.json
```

CSV is allowed only as an additional convenience export if existing project conventions already support it. Parquet/JSON/JSONL are preferred canonical evaluation formats.

Do not write evaluation outputs to `reports/`.

---

## 7. Event model

### 7.1 Event identity

Evaluation records are event-based, not run-based.

A unique event identity is:

```text
symbol + setup_cycle_id + event_type
```

`run_id` is provenance, not identity.

### 7.2 Event types

Allowed event types for T18:

```text
first_watch
first_early_ready
first_confirmed_ready
first_late
first_chased
first_rejected
```

Allowed event order values:

```text
first_watch = 10
first_early_ready = 20
first_confirmed_ready = 30
first_late = 40
first_chased = 40
first_rejected = 40
```

Use `event_order` only as a stable sorting helper. It is not a causal topology statement. Terminal events share the same order group because `late`, `chased`, and `rejected` are alternative terminal/decay observations and `rejected` can occur directly from active states via structural invalidation. Do not infer that `chased` must follow `late` or that `rejected` must follow `chased`. Within identical `event_order`, break ties deterministically by `event_type`. Do not rely on alphabetical ordering alone as the primary event model.

### 7.3 Event classes

| Event class | Events | Forward returns / MFE / MAE | Timestamp record |
|---|---|---:|---:|
| Signal / baseline events | `first_watch`, `first_early_ready`, `first_confirmed_ready` | Yes | Yes |
| Terminal events | `first_late`, `first_chased`, `first_rejected` | No | Yes |

`first_watch` is a base-rate and lead-time reference, not a primary signal-quality event.

Primary signal-quality comparison in T18 is between:

```text
first_early_ready
first_confirmed_ready
```

Terminal events are used for lifecycle, decay, and invalidation timing analysis only.

### 7.4 State vs bucket separation

`late` is a state-machine state. `late_monitor` is a decision bucket. Keep state and bucket fields separate in all replay records.

Do not treat `late_monitor` as a state. Do not treat `late` as a bucket.

---

## 8. Event reconstruction rules

### 8.1 Source observations

For each run snapshot record, replay needs at least:

- `symbol`
- `setup_cycle_id`
- `state_machine_state`
- `decision_bucket`
- `run_id`
- `run_mode`
- `daily_bar_id` and/or `intraday_bar_id`
- event timestamp or bar timestamp fields available in the snapshot/manifest
- `market_phase`
- `market_phase_confidence`
- `state_confidence`
- `priority_score` if available
- `close_at_early_entry_bar` if available
- `close_at_confirmed_entry_bar` if available
- source snapshot path / manifest reference if available

Use the actual implemented snapshot schema after Tickets 13, 15, and 17. If names differ, map them explicitly in a small adapter. Do not silently invent alias fields.

### 8.2 First-event detection

For each `symbol + setup_cycle_id`, replay must detect the first observation of each event type:

- `first_watch`: first snapshot where `state_machine_state == "watch"`
- `first_early_ready`: first snapshot where `state_machine_state == "early_ready"`
- `first_confirmed_ready`: first snapshot where `state_machine_state == "confirmed_ready"`
- `first_late`: first snapshot where `state_machine_state == "late"`
- `first_chased`: first snapshot where `state_machine_state == "chased"`
- `first_rejected`: first snapshot where `state_machine_state == "rejected"`

Events are cycle-local. Do not carry an event from one `setup_cycle_id` into another.

Across multiple runs, repeated observations of the same state are expected. For each `symbol + setup_cycle_id + event_type`, replay must select the earliest observed event bar/timestamp across all eligible run snapshots.

Do not fail just because a later run observes the same symbol/cycle/state on a later bar. That is normal multi-run replay behavior and must not create a duplicate event.

Fail fast only if a single run snapshot contains conflicting state records for the same `symbol + setup_cycle_id` identity, or if the same run snapshot contains internally inconsistent bar/timestamp data for the same symbol/cycle/state observation. Do not silently overwrite intra-snapshot conflicts.

### 8.3 Bar IDs and timestamps

Respect the post-T17 canonical bar-ID contracts:

- `daily_bar_id`: `str` in `YYYY-MM-DD` format
- `intraday_bar_id` / `intraday_cache_bar_id`: `YYYY-MM-DDTHH:00:00Z`, UTC, 4h-aligned

All evaluation timestamps must be UTC.

If both daily and intraday observations exist for a cycle, preserve `run_mode` and the observed event bar ID. Do not normalize away the run-mode distinction.

### 8.4 Deterministic sorting

Sort event timeline exports by:

```text
symbol
setup_cycle_id
event_order
event_timestamp_utc
event_type
```

`first_observed_run_id` is not part of event identity and not a primary sort dimension.

---

## 9. Reference-price rules

Reference price handling is intentionally strict to avoid replay inventing a new business truth.

### 9.1 Signal/baseline reference prices

| Event | Reference price rule |
|---|---|
| `first_watch` | Close of the OHLCV bar mapped from the first watch event bar ID. This is a base-rate reference, not a state-entry reference. |
| `first_early_ready` | Use persisted `close_at_early_entry_bar` from the first run snapshot where the symbol enters `early_ready` in the given `setup_cycle_id`. |
| `first_confirmed_ready` | Use persisted `close_at_confirmed_entry_bar` from the first run snapshot where the symbol enters `confirmed_ready` in the given `setup_cycle_id`. |

For `first_early_ready` and `first_confirmed_ready`, do not reconstruct the reference price from OHLCV if the persisted state reference is missing, invalid, non-finite, or non-positive.

If the persisted reference is not usable, set:

```text
reference_price = null
reference_price_status = reference_price_not_evaluable
reference_price_reason = missing_persisted_state_reference
forward_return_* = null
mfe_* = null
mae_* = null
metric_status_* = reference_price_not_evaluable
```

### 9.2 Terminal-event reference prices

For terminal events:

```text
first_late
first_chased
first_rejected
```

No forward returns, MFE, or MAE are calculated in T18.

Terminal event exports must either omit return metric fields or set them to `null` with:

```text
return_metrics_status = terminal_event_returns_out_of_scope
```

Preferred implementation: keep terminal events in a separate `terminal_event_timeline.parquet` without signal metric fields.

---

## 10. Forward returns, MFE, and MAE

### 10.1 Horizons

Canonical T18 horizons:

```text
1d
3d
5d
10d
```

### 10.2 Per-horizon MFE/MAE design decision

The v2.1 concept defines MFE and MAE as validation metrics. This ticket operationalizes that requirement as per-horizon metrics aligned with the canonical forward-return horizons (`1d`, `3d`, `5d`, `10d`). This is an explicit v2.1 evaluation-export design decision, not a new scanner decision rule.

### 10.3 Output fields for signal/baseline events

For `first_watch`, `first_early_ready`, and `first_confirmed_ready`, produce:

```text
forward_return_1d_pct
forward_return_3d_pct
forward_return_5d_pct
forward_return_10d_pct

mfe_1d_pct
mfe_3d_pct
mfe_5d_pct
mfe_10d_pct

mae_1d_pct
mae_3d_pct
mae_5d_pct
mae_10d_pct

metric_status_1d
metric_status_3d
metric_status_5d
metric_status_10d
```

### 10.4 Calculation definitions

For each event and horizon:

- `reference_price` is defined by section 9.
- `forward_return_<horizon>_pct` is the percent return from `reference_price` to the close of the horizon end bar.
- `mfe_<horizon>_pct` is the maximum favorable high-based excursion from `reference_price` over the closed bars in the horizon window.
- `mae_<horizon>_pct` is the maximum adverse low-based excursion from `reference_price` over the closed bars in the horizon window.

Use real percentages:

```text
+3.5 means +3.5%
-2.0 means -2.0%
```

Do not use 0..1 return fractions in exported fields ending in `_pct`.

### 10.5 Closed-bar and no-lookahead rule

All calculations must use closed OHLCV bars only.

The event bar itself is allowed only as the reference context. Forward-looking metrics must not use unknown future values at event creation time. In replay, future values are used only as retrospective evaluation targets.

The exact inclusion rule is mandatory and must be tested:

- The reference event occurs at a closed bar.
- For daily events, horizon `Nd` measures from the event reference price to the close of the daily bar that is `N` subsequent daily bars after the event daily bar.
- For intraday events, map the `intraday_bar_id` to the daily bar whose `daily_bar_id` equals the UTC date component of the intraday bar ID. Example: `2026-04-01T08:00:00Z` maps to daily bar `2026-04-01`.
- For intraday events, horizon `Nd` measures from the event reference price to the close of the daily bar that is `N` subsequent daily bars after the mapped reference daily bar.
- For intraday `first_early_ready` and `first_confirmed_ready`, the reference price remains the persisted state reference (`close_at_early_entry_bar` / `close_at_confirmed_entry_bar`), which may be a 4h-state reference. Only the horizon window is mapped to daily bars.
- MFE/MAE for horizon `Nd` use highs/lows of the `N` closed daily bars after the reference daily bar, up to and including the horizon end bar.
- Do not use the same-day daily close as the `1d` horizon close for an intraday event. `1d` means the first subsequent daily bar after the mapped reference daily bar.

Do not use local time. All date extraction and horizon mapping are UTC-based.

### 10.6 Missing future data

If insufficient future OHLCV exists for a horizon:

```text
forward_return_<horizon>_pct = null
mfe_<horizon>_pct = null
mae_<horizon>_pct = null
metric_status_<horizon> = insufficient_future_data
```

Do not silently drop the event. Do not coerce missing metrics to `0.0`.

---

## 11. Lead-time and transition metrics

Produce transition lead-time outputs from the reconstructed event timeline.

Required transition families:

```text
first_watch -> first_early_ready
first_watch -> first_confirmed_ready
first_watch -> first_rejected
first_early_ready -> first_confirmed_ready
first_confirmed_ready -> first_late
first_confirmed_ready -> first_chased
first_confirmed_ready -> first_rejected
first_early_ready -> first_late
first_early_ready -> first_chased
first_early_ready -> first_rejected
```

If a target event never occurs within the available replay window, preserve that as:

```text
transition_status = target_event_not_observed
```

Do not treat unobserved transitions as zero-duration transitions.

Output at least:

- `symbol`
- `setup_cycle_id`
- `source_event_type`
- `target_event_type`
- `source_event_timestamp_utc`
- `target_event_timestamp_utc`
- `source_event_bar_id`
- `target_event_bar_id`
- `bars_between` if deterministically computable
- `elapsed_hours` if deterministically computable
- `transition_status`

---

## 12. Nullability, invalid inputs, and status semantics

### 12.1 Non-finite numerics

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid or not evaluable inputs and must not be passed through as numeric-looking outputs.

### 12.2 Nullable metrics

Metric fields are nullable. `null` means the value is not reliably evaluable for the corresponding event/horizon. `null` must not be implicitly coerced to `false`, `0`, or a negative result.

### 12.3 Status values

Required metric status values:

```text
ok
insufficient_future_data
reference_price_not_evaluable
missing_ohlcv_history
terminal_event_returns_out_of_scope
not_applicable
```

Required `reference_price_reason` values when `reference_price_status != ok`:

```text
missing_persisted_state_reference
missing_ohlcv_event_bar
non_finite_reference_price
non_positive_reference_price
not_applicable
```

Meaning:

- `ok`: metric was calculated from finite reference price and sufficient closed OHLCV history.
- `insufficient_future_data`: the event exists and the reference price is usable, but the requested horizon is not fully available.
- `reference_price_not_evaluable`: the event exists, but the reference price is missing, non-finite, non-positive, or otherwise unusable.
- `missing_ohlcv_history`: no usable OHLCV history can be loaded for the symbol/timeframe required by the metric.
- `terminal_event_returns_out_of_scope`: the event is terminal and T18 intentionally does not calculate returns/MFE/MAE for it.
- `not_applicable`: the field does not apply to the export row by design.

Non-evaluable and negative evaluation are separate states. A missing metric must not be treated as a bad return.

---

## 13. Config contract

If this ticket introduces an evaluation config block, put it under the `independence_release` namespace, for example:

```yaml
independence_release:
  evaluation:
    horizons_days: [1, 3, 5, 10]
    include_first_watch_metrics: true
    include_terminal_event_return_metrics: false
```

Defaults:

- `horizons_days`: `[1, 3, 5, 10]`
- `include_first_watch_metrics`: `true`
- `include_terminal_event_return_metrics`: `false`

`include_terminal_event_return_metrics` controls only return/MFE/MAE metric calculation for terminal events. Terminal event timeline records are always produced in T18. This key must remain false in T18. If the config key is present and true, fail fast with a clear error explaining that terminal-event return metrics are deferred and out of scope for T18.

Partial overrides in `independence_release.evaluation` are merged field-wise with central defaults; missing subkeys are not invalid.

Invalid config values fail fast:

- `horizons_days` must be a non-empty list of positive integers.
- For T18 it must resolve exactly to `[1, 3, 5, 10]` unless an existing project-wide evaluation config pattern already supports fixed canonical horizons differently.
- `include_first_watch_metrics` must be boolean.
- `include_terminal_event_return_metrics` must be boolean and must resolve to `false`.
- Non-finite numeric values are invalid.

Do not use ad-hoc raw-dict fallback logic.

---

## 14. Determinism requirements

For identical inputs and identical config, replay outputs, metric outputs, statuses, diagnostics, and manifests must be identical.

Do not rely on dict/set iteration order.

Required deterministic sort keys:

Event timeline:

```text
symbol
setup_cycle_id
event_order
event_timestamp_utc
event_type
```

Signal metrics:

```text
symbol
setup_cycle_id
event_order
event_timestamp_utc
event_type
```

Lead-time table:

```text
symbol
setup_cycle_id
source_event_type
target_event_type
```

---

## 15. Output schema requirements

### 15.1 `evaluation/replay/event_timeline.jsonl`

One row per unique `symbol + setup_cycle_id + event_type`.

Required fields:

```text
symbol
setup_cycle_id
event_type
event_order
event_timestamp_utc
event_bar_id
event_bar_id_type
state_machine_state
decision_bucket
market_phase
market_phase_confidence
state_confidence
priority_score
first_observed_run_id
first_observed_run_mode
source_snapshot_path
source_manifest_path
```

`event_bar_id_type` allowed values:

```text
daily_bar_id
intraday_bar_id
unknown
```

`unknown` is allowed only if the source snapshot genuinely lacks a usable bar ID. It must be counted in diagnostics.

### 15.2 `evaluation/exports/signal_event_metrics.parquet`

Rows only for:

```text
first_watch
first_early_ready
first_confirmed_ready
```

Required base fields:

```text
symbol
setup_cycle_id
event_type
event_order
event_timestamp_utc
event_bar_id
event_bar_id_type
reference_price
reference_price_status
reference_price_source
first_observed_run_id
first_observed_run_mode
source_snapshot_path
market_phase
market_phase_confidence
state_machine_state
state_confidence
decision_bucket
priority_score
```

Required metric fields:

```text
forward_return_1d_pct
forward_return_3d_pct
forward_return_5d_pct
forward_return_10d_pct
mfe_1d_pct
mfe_3d_pct
mfe_5d_pct
mfe_10d_pct
mae_1d_pct
mae_3d_pct
mae_5d_pct
mae_10d_pct
metric_status_1d
metric_status_3d
metric_status_5d
metric_status_10d
```

Allowed `reference_price_source` values:

```text
ohlcv_event_bar_close
close_at_early_entry_bar
close_at_confirmed_entry_bar
none
```

### 15.3 `evaluation/exports/terminal_event_timeline.parquet`

Rows only for:

```text
first_late
first_chased
first_rejected
```

Required fields:

```text
symbol
setup_cycle_id
event_type
event_order
event_timestamp_utc
event_bar_id
event_bar_id_type
state_machine_state
decision_bucket
market_phase
market_phase_confidence
state_confidence
first_observed_run_id
first_observed_run_mode
source_snapshot_path
return_metrics_status
```

`return_metrics_status` must be:

```text
terminal_event_returns_out_of_scope
```

### 15.4 `evaluation/exports/transition_lead_times.parquet`

Required fields are defined in section 11.

### 15.5 `evaluation/exports/evaluation_summary.json`

Must include at least:

- replay input date range
- run count
- symbol count
- cycle count
- event counts by `event_type`
- metric row counts by `event_type`
- count of `metric_status_*` values by horizon
- count of missing/unknown event bar IDs
- count of missing persisted reference prices
- output paths
- config hash or config payload if project conventions already support it

---

## 16. Diagnostics and failure modes

Hard-fail conditions:

- Missing or unreadable canonical OHLCV history root when signal metrics are requested.
- Invalid evaluation config.
- Conflicting state records within a single run snapshot for the same `symbol + setup_cycle_id` identity that make event observation non-deterministic. Cross-run observations of the same event identity with later timestamps are normal replay input and must be resolved by taking the earliest observed event bar, not by failing.
- Non-deterministic or ambiguous event ordering that cannot be resolved from snapshot data.
- Attempt to enable terminal-event return metrics in T18.

Non-hard diagnostic conditions:

- A symbol lacks enough future history for one or more horizons.
- A `first_early_ready` or `first_confirmed_ready` event lacks the persisted reference price.
- A source snapshot lacks a usable event bar ID.
- A transition target event is not observed in the replay window.

Diagnostics must distinguish:

- not observed
- not evaluable
- invalid
- insufficient future data
- out of scope

Do not collapse these into one generic failure status.

---

## 17. Testing requirements

Add focused tests. Do not require live MEXC or CoinMarketCap access.

### 17.1 Replay source test

Fixture:

- Two or more synthetic run snapshots under `snapshots/runs/...`.
- Conflicting or incomplete `reports/` data if needed.

Expected:

- Replay derives event timeline from `snapshots/runs/` only.
- `reports/index/` may only help locate run paths.
- No business/evaluation facts are derived from report comfort files.

### 17.2 Event model per cycle

Fixture:

- Same symbol with two `setup_cycle_id`s.
- Cycle 1: `watch -> early_ready -> confirmed_ready -> chased`.
- Cycle 2: `watch -> early_ready`.

Expected:

- Events are emitted separately per cycle.
- No event from cycle 1 is carried into cycle 2.

### 17.3 State/bucket separation

Fixture:

- State `late`, bucket `late_monitor`.
- State `confirmed_ready`, bucket `late_monitor` if allowed by an existing run snapshot fixture.

Expected:

- State and bucket fields remain separate.
- `late_monitor` is never treated as a state.
- `late` is never treated as a bucket.

### 17.4 Reference price test

Fixture:

- `first_early_ready` with finite `close_at_early_entry_bar`.
- `first_confirmed_ready` with finite `close_at_confirmed_entry_bar`.
- Same events with missing/non-finite reference values.

Expected:

- Persisted state references are used for early/confirmed.
- Missing/non-finite persisted references are not reconstructed from OHLCV.
- Metrics become `null` with `reference_price_not_evaluable`.

### 17.5 First-watch base-rate reference test

Fixture:

- `first_watch` event with a mappable event bar ID and OHLCV close.

Expected:

- `reference_price_source = ohlcv_event_bar_close`.
- Metrics are calculated as base-rate context.

### 17.6 Forward returns test

Fixture:

- Known daily OHLCV close series.
- Event at a known closed daily bar.
- `first_early_ready` event with persisted `close_at_early_entry_bar` that intentionally differs from the mapped daily OHLCV close of the event bar.
- Horizons `1d`, `3d`, `5d`, `10d`.

Expected:

- Forward returns for `first_early_ready` are calculated from the persisted `close_at_early_entry_bar`, not from the mapped daily OHLCV close.
- Forward returns match exact expected percentages.
- Exported units are real percentages.
- No horizon with insufficient future data is dropped.

### 17.7 MFE/MAE test

Fixture:

- Known high/low series after event.

Expected:

- MFE uses maximum high excursion in the horizon window.
- MAE uses maximum low adverse excursion in the horizon window.
- Both are exported as real percentages.

### 17.8 Insufficient future data test

Fixture:

- Event near end of OHLCV history.

Expected:

- Available horizons calculate normally.
- Unavailable horizons are `null` with `insufficient_future_data`.
- Event row remains present.

### 17.9 Daily vs intraday bar-ID test

Fixture:

- Daily event with `daily_bar_id = YYYY-MM-DD`.
- Intraday event with `intraday_bar_id = YYYY-MM-DDTHH:00:00Z`.

Expected:

- Both are parsed UTC-stably.
- Event bar ID and type are preserved.
- No local timezone conversion is introduced.

### 17.10 Intraday-to-daily horizon mapping test

Fixture:

- Intraday `first_early_ready` event with `intraday_bar_id = 2026-04-01T08:00:00Z`.
- Persisted `close_at_early_entry_bar` intentionally differs from the daily OHLCV close for `2026-04-01`.
- Daily OHLCV contains bars for `2026-04-01`, `2026-04-02`, and subsequent horizon dates.

Expected:

- The intraday event maps to reference daily bar `2026-04-01` using the UTC date component.
- The `1d` horizon uses the close of the first subsequent daily bar, `2026-04-02`, not the same-day close of `2026-04-01`.
- Forward return, MFE, and MAE use the persisted `close_at_early_entry_bar` as reference price, not the daily close of the mapped reference daily bar.
- MFE/MAE horizon windows use the closed daily bars after `2026-04-01` according to section 10.5.
- No local-time conversion is introduced.

### 17.11 Terminal event no-return test

Fixture:

- `first_late`, `first_chased`, `first_rejected` events.

Expected:

- Terminal events appear in terminal timeline.
- No forward-return/MFE/MAE metrics are calculated.
- `return_metrics_status = terminal_event_returns_out_of_scope`.

### 17.12 Deterministic output test

Fixture:

- Same input snapshots and OHLCV run twice.

Expected:

- Event timeline, metric outputs, transition outputs, and summary are identical.
- Sorting follows the required sort keys.

### 17.13 Documentation cleanup test/check

Expected:

- `open_questions.md` no longer presents long-term OHLCV history storage as unresolved if Ticket 14 canonical Parquet storage exists.
- `feature_enhancements.md` contains the terminal-event forward-return deferred topic.

---

## 18. Acceptance criteria

This ticket is complete when all of the following are true:

1. Evaluation replay reconstructs event timelines from `snapshots/runs/`, not from `reports/`.
2. Forward returns, MFE, and MAE read OHLCV from `snapshots/history/ohlcv/`.
3. Event identity is `symbol + setup_cycle_id + event_type`.
4. Event ordering uses explicit `event_order`.
5. `first_watch`, `first_early_ready`, and `first_confirmed_ready` are exported to `signal_event_metrics.parquet`.
6. `first_late`, `first_chased`, and `first_rejected` are exported to `terminal_event_timeline.parquet` without return metrics.
7. `close_at_early_entry_bar` and `close_at_confirmed_entry_bar` are used as authoritative persisted reference prices for early/confirmed metrics.
8. Missing persisted early/confirmed reference prices are not reconstructed from OHLCV.
9. `first_watch` metrics use OHLCV event-bar close only as base-rate reference.
10. Horizons are `1d`, `3d`, `5d`, `10d`.
11. MFE/MAE are calculated per horizon as an explicit T18 evaluation-export design decision.
12. Missing future data yields nullable metrics plus explicit status, not dropped rows and not zeroes.
13. `late` state and `late_monitor` bucket remain separate.
14. Outputs are deterministic under identical inputs and config.
15. `open_questions.md` §2 is resolved/updated consistently with Ticket 14 if canonical Parquet history exists in the repo.
16. `feature_enhancements.md` includes terminal-event forward returns as deferred.
17. Tests cover replay source, per-cycle event identity, reference prices, forward returns, MFE/MAE, insufficient future data, terminal no-return behavior, daily/intraday bar-ID handling, intraday-to-daily horizon mapping, and deterministic output.
18. Terminal event timeline records are always produced; `include_terminal_event_return_metrics` controls only deferred terminal return metrics and must remain false in T18.

---

## 19. Implementation notes for Codex

- Inspect the actual post-T17 snapshot schema before coding adapters.
- Prefer small pure functions for event detection, reference-price resolution, and metric calculation.
- Keep snapshot parsing separate from metric calculation.
- Avoid hidden fallback paths.
- Do not import or revive legacy business evaluation logic.
- Do not make network calls.
- Do not calculate any metric from stale execution data.
- Preserve all available provenance fields; do not make `run_id` part of event identity.
- Use closed-candle-only OHLCV.
- If an expected snapshot field is absent, either map the actual repo field explicitly or mark the value as not evaluable with diagnostics. Do not invent a silent alias.

---

## 20. Preflight checklist summary

- Scope is one PR: evaluation replay + metrics + narrow canonical doc cleanup.
- Current authoritative reference set is explicit.
- Repo-collision risk is addressed: `open_questions.md` drift is resolved in scope.
- `reports/` vs `snapshots/runs/` roles are explicitly separated.
- History source is canonical Parquet under `snapshots/history/ohlcv/`.
- Missing vs invalid vs not observed vs out of scope are distinct.
- Nullable metric fields are not coerced.
- Non-finite numerics are rejected/not evaluable.
- Event identity and sort order are deterministic.
- Terminal-event returns are explicitly deferred, not optional.
- No scanner business logic is changed.
