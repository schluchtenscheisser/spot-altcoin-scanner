> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
> Vor Ausarbeitung dieses Tickets ist die Ticket-Prüfschleife anzuwenden.
>
> Naming convention: `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3
>
> This ticket is written in English.

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

> Ziel: Codex soll nicht interpretieren müssen. Deshalb müssen Defaults, Missing-Keys, Nullability und “nicht evaluiert” vs “evaluiert aber fehlgeschlagen” explizit im Ticket stehen und getestet werden.

#### A) Defaults / Config-Semantik
- [x] This ticket introduces an analysis CLI with local analysis defaults, not ScannerConfig business defaults.
- [x] Missing optional CLI arguments use explicitly defined defaults.
- [x] Invalid CLI values fail preflight before writes.
- [x] No silent fallback for invalid paths, invalid enum values, non-positive time stops, non-positive stop/partial parameters, or invalid matrix values.

#### B) Nullability / Schema / Output
- [x] Nullable output fields are explicitly defined.
- [x] `null` means not evaluable / not applicable and must not be coerced to `false` or numeric zero.
- [x] Boolean fields remain binary only where evaluation status is known; otherwise use `simulation_status` and nullable fields.

#### C) Edgecases
- [x] Not-evaluable simulation rows are separated from evaluated simulation rows.
- [x] Same-bar STOP/PARTIAL/TRAIL/TIME collisions are explicitly specified.
- [x] Output writes are atomic under strict preflight.
- [x] Deterministic `exit_model_id` construction is specified.

#### D) Tests
- [x] Missing/default CLI behavior required.
- [x] Invalid config/matrix values required.
- [x] Intrabar collision tests required.
- [x] Nullability and not-evaluable tests required.
- [x] Determinism test required.

---

## Title
[P2] BACKTEST-3B — Simulate focused 4h exit model variants on validated BACKTEST-3A path outputs

## Context / Source

BACKTEST-1 and BACKTEST-2 showed that the scanner edge is strongest over short horizons, primarily 1d–3d, with 5d as a possible stretch horizon and 10d/20d not suitable as blind-hold targets. The current exit-strategy work therefore needs path-aware evidence before proposing any live exit rule.

BACKTEST-3A has now produced a validated 4h path dataset for the Primary Trade Scope v0. The latest successful BACKTEST-3A run has these relevant properties:

```text
analysis_id: BACKTEST-3A_EXIT_PATH_METRICS_4H
scenario_id: hsq_replay_2025_05_to_2026_05_v1
replay_id: 2026-05-24T21-27-31Z
raw_input_rows: 1523
primary_scope_rows_before_deduplication: 291
output_rows_after_deduplication: 228
discarded_duplicate_row_count: 63
conflicting_duplicate_event_id_count: 0
bar_rows: 9564
required_path_bars: 42
late_monitor_included: false
exit_simulation_performed: false
```

Primary Trade Scope v0 segments in BACKTEST-3A:

```text
early_candidates__base_reclaim: 101 events
confirmed_candidates__ema_reclaim: 63 events
early_candidates__early_reversal_break: 64 events
```

BACKTEST-3A also confirms:

```text
reference_price_status = available for all 228 event rows
reference_price_source = path_bar_1_open for all 228 event rows
ATR(14) 4h available for all 228 event rows
227 / 228 events have full 42-bar coverage; 1 / 228 is partial
```

Observed 3A path evidence motivates 3B:

```text
MFE exists materially within the 42-bar path, but median close returns decay for several segments.
This implies that profit-taking, stop placement, time stops, and post-partial trailing must be evaluated path-wise.
```

Important interpretation boundary:

```text
BACKTEST-3B is analytics-only. It must simulate exit variants in-sample on the validated 3A path dataset.
It must not create a live exit recommendation, change scanner ranking, or change entry/bucket logic.
```

## Goal

Create a deterministic analysis utility that simulates a focused family of exit model variants on the validated BACKTEST-3A 4h path outputs.

After this change, the project can answer questions such as:

- Which exit variants perform better per Primary-Scope segment?
- How often does an initial stop occur before partial take-profit?
- How often does maximum adverse excursion occur before maximum favorable excursion?
- How sensitive is each segment to ATR-based versus fixed-percent stops?
- Does a shorter 24h/48h/72h/96h/120h time stop outperform the prior 168h analytical max-hold baseline?
- Does simple post-partial trailing improve or hurt outcomes compared with no trailing?

The output must support later human review and BACKTEST-3B discussion, not automated live-trading decisions.

## Scope

Allowed changes:

```text
scripts/backtest/simulate_exit_model_variants_4h.py
tests/backtest/test_simulate_exit_model_variants_4h.py
```

Optional if needed for small shared helpers, but avoid unless there is already a reusable analysis helper location:

```text
scripts/backtest/* helper module used only by backtest analysis scripts
```

The script must be executable as a CLI and importable for tests.

Default input paths:

```text
--input-events-path evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_metrics_4h.parquet
--input-bars-path evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_returns_by_bar.parquet
--input-summary-path evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_metrics_4h_summary.json
--output-dir evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_model_simulation_4h
```

CSV input fallback is allowed only via explicit CLI arguments. Do not silently switch from Parquet to CSV.

## Out of Scope

This ticket must not implement:

- live exit rules
- production scanner exit logic
- scanner ranking changes
- entry selection changes
- decision bucket changes
- state machine changes
- MEXC execution simulation
- orderbook fill modeling
- slippage
- fees
- tax/accounting logic
- portfolio sizing
- late_monitor entry or exit modeling
- EMA20(4h) trailing
- recomputation of EMA20 or any new 4h indicator not already in 3A output
- new BACKTEST-3A path generation
- canonical v2.1 spec changes
- GitHub Actions workflow changes

EMA20(4h) trail is explicitly out of scope for BACKTEST-3B v0 because EMA20(4h) is not present in the 3A bar output and must not be recomputed in this ticket.

## Canonical References

Current authoritative reference hierarchy:

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md` as working-context / guardrail document, not as primary business authority.
4. Implemented BACKTEST-3A repo reality:
   - `scripts/backtest/generate_exit_path_metrics_4h.py`
   - `docs/legacy/tickets/2026-05-30__P2__backtest_3a_generate_4h_exit_path_metrics_rev3.md`
   - latest BACKTEST-3A output artifacts
5. Existing analytics-only reference model:
   - `docs/canonical/BACKTEST/TRADE_MODEL_4H_IMMEDIATE_RETEST.md`

Authority rule:

> If the current authoritative reference set, existing repo Authority/Canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents remain valid only where they do not contradict this reference set.

This ticket must not create a competing canonical exit model. It creates an analytics-only simulation dataset.

## Proposed change (high-level)

### Before

The repo has BACKTEST-3A path metrics:

- reference prices
- 42-bar 4h path returns
- MFE / MAE
- time-to-MFE / time-to-MAE
- ATR(14) 4h diagnostics

But the repo does not yet simulate concrete exit model variants on those paths.

### After

A new BACKTEST-3B script reads the validated 3A event-level and bar-level outputs, constructs a deterministic exit-model matrix, simulates each event-model pair, and writes:

```text
exit_model_simulation_4h.parquet
exit_model_simulation_4h.csv
exit_model_segment_summary.parquet
exit_model_segment_summary.csv
exit_model_simulation_summary.json
exit_model_simulation_report.md
```

### Edge cases

- Missing reference price → simulation row is `not_evaluable`, returns are `null`.
- Missing ATR for ATR stop → simulation row is `not_evaluable`, returns are `null`.
- Partial path coverage → evaluate only if the simulated exit occurs before missing bars; otherwise `not_evaluable` with `exit_reason = path_incomplete`.
- Same-bar stop and partial collision → stop wins; partial is not filled.
- Same-bar stop and trail collision → stop wins.
- Partial and trail in same bar → trail is not active until the bar after the partial-fill bar.
- Time stop and partial in same bar → partial fills first, then the remaining position exits at the same bar close via time stop, unless stop also hit in the same bar.
- Non-finite numerical values (`NaN`, `inf`, `-inf`) are invalid / not evaluable and must not be propagated into numeric-looking outputs.

### Backward compatibility impact

No production behavior changes. This is an additive analytics script and report output only.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> This section is an execution instruction for Codex. If anything below is ambiguous, the ticket must be adjusted before implementation.

### Config / CLI defaults

This script does not read `ScannerConfig`. It uses explicit analysis-local CLI defaults.

Required CLI shape:

```bash
python scripts/backtest/simulate_exit_model_variants_4h.py \
  --input-events-path evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_metrics_4h.parquet \
  --input-bars-path evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_returns_by_bar.parquet \
  --input-summary-path evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_metrics_4h_summary.json \
  --output-dir evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_model_simulation_4h \
  --overwrite
```

Optional CLI arguments and defaults:

| Argument | Type | Default | Missing behavior | Invalid behavior |
|---|---|---:|---|---|
| `--time-stops-hours` | comma-separated positive ints | `24,48,72,96,120,168` | use default | fail preflight |
| `--atr-stop-multipliers` | comma-separated positive floats | `1.0,1.2,1.5,2.0` | use default | fail preflight |
| `--fixed-stop-pcts` | comma-separated positive floats | `5,8,12` | use default | fail preflight |
| `--fixed-partial-trigger-pcts` | comma-separated positive floats | `5,7.5,10` | use default | fail preflight |
| `--r-partial-triggers` | comma-separated positive floats | `1.0,1.5,2.0` | use default | fail preflight |
| `--partial-sizes` | comma-separated floats in `(0,1]` | `0.4,0.5` | use default | fail preflight |
| `--trail-modes` | comma-separated enum | `none,low_2bars,low_3bars` | use default | fail preflight |
| `--strict-preflight` | bool flag | true | true | N/A |
| `--no-strict-preflight` | bool flag | false | false | N/A |
| `--overwrite` | bool flag | false | false | N/A |

Partial overrides are not nested dictionaries. Each comma-separated list replaces only that one list and does not change the other defaults.

Missing key / missing argument is not invalid. Invalid values are invalid.

### Required input columns

Event-level input must contain at least:

```text
event_id
symbol
segment_key
decision_bucket
entry_pattern
signal_timestamp
reference_price
reference_price_source
reference_price_status
path_coverage_status
available_path_bars
required_path_bars
mfe_pct
mae_pct
mfe_bar_index_4h
mae_bar_index_4h
time_to_mfe_hours
time_to_mae_hours
atr_4h_available
atr_4h_value
atr_4h_period
atr_4h_source
```

Bar-level input must contain at least:

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

Missing required columns fail preflight before writes.

### Exit model matrix

Default stop configurations:

```text
initial_stop_mode = atr
initial_stop_value in {1.0, 1.2, 1.5, 2.0}

initial_stop_mode = fixed_pct
initial_stop_value in {5.0, 8.0, 12.0}
```

Stop price:

```text
ATR stop:
  stop_price = reference_price - (atr_4h_value * atr_multiplier)

Fixed-percent stop:
  stop_price = reference_price * (1 - fixed_stop_pct / 100)
```

If `stop_price <= 0`, non-finite, or `stop_price >= reference_price`, the event-model row is `not_evaluable`.

Default partial configurations:

```text
partial_mode = none
partial_trigger_value = null
partial_size = 0.0

partial_mode = fixed_pct
partial_trigger_value in {5.0, 7.5, 10.0}
partial_size in {0.4, 0.5}

partial_mode = r_multiple
partial_trigger_value in {1.0, 1.5, 2.0}
partial_size in {0.4, 0.5}
```

R-multiple partial triggers are valid only when `initial_stop_mode = atr` in BACKTEST-3B v0.

Partial trigger price:

```text
fixed_pct:
  partial_trigger_price = reference_price * (1 + fixed_partial_trigger_pct / 100)

r_multiple:
  risk_abs = reference_price - stop_price
  partial_trigger_price = reference_price + r_multiple * risk_abs
```

If `partial_mode = none`, then `trail_mode` must be `none`.

Default trail modes:

```text
trail_mode = none
trail_mode = low_2bars
trail_mode = low_3bars
```

Trail modes are valid only when `partial_mode != none`.

### Trail definitions

`trail_low_2bars` / output value `low_2bars`:

```text
After partial is filled, exit at the close of any bar where:
close_4h < min(low_4h of the 2 bars preceding the current bar)
```

`trail_low_3bars` / output value `low_3bars`:

```text
After partial is filled, exit at the close of any bar where:
close_4h < min(low_4h of the 3 bars preceding the current bar)
```

Trail activation rule:

```text
Trail can only become active from the bar after the partial-fill bar.
```

If insufficient preceding bars exist for the selected trail window, trail is not evaluable for that current bar but the simulation continues.

### Time stop definitions

Default values:

```text
time_stop_hours in {24, 48, 72, 96, 120, 168}
```

Because bars are 4h and `bar_index_4h` starts at 1:

```text
time_stop_bar_index = time_stop_hours / 4
```

All default time stops divide exactly by 4. If a user-provided time stop does not divide exactly by 4, fail preflight.

Time-stop exit price:

```text
close_4h of the time_stop_bar_index bar
```

### Intrabar event priority

For each event-model pair, process bars in ascending `bar_index_4h` order.

Within the same 4h bar, priority is:

```text
STOP -> PARTIAL -> TRAIL -> TIME_EXIT
```

Hard collision rule:

```text
If low_4h <= stop_price and high_4h >= partial_trigger_price in the same bar,
the stop is assumed to have fired first.
The partial is not filled.
```

Additional collision rules:

```text
If stop and trail would occur in the same bar, stop wins.
If stop and time stop would occur in the same bar, stop wins.
If partial and time stop occur in the same bar, partial fills first and the remaining position exits at that bar close, unless stop also occurred in the same bar.
Trail never fires in the same bar as partial because trail activation starts from the next bar.
```

### Return calculation

All returns are gross returns before fees, slippage, and execution costs.

Full-position exit return:

```text
exit_return_pct = ((exit_price / reference_price) - 1) * 100
```

`exit_price` semantics are mandatory and deterministic:

```text
exit_reason = stop:
  exit_price = stop_price
  exact stop-level fill is assumed; do not use low_4h or next-bar open.

exit_reason = time_stop:
  exit_price = close_4h of the time-stop bar.

exit_reason = partial_then_stop:
  exit_price = stop_price of the final stop leg.
  gross_return_pct is the blended partial + remaining-leg return.

exit_reason = partial_then_trail:
  exit_price = close_4h of the trail-trigger bar for the remaining leg.
  gross_return_pct is the blended partial + remaining-leg return.

exit_reason = partial_then_time_stop:
  exit_price = close_4h of the time-stop bar for the remaining leg.
  gross_return_pct is the blended partial + remaining-leg return.

exit_reason in {path_incomplete, partial_then_path_incomplete} or simulation_status = not_evaluable:
  exit_price = null.
```

For partial exits, the singular `exit_price` field always represents the remaining-leg terminal exit price. The partial leg execution price is represented separately by `partial_trigger_price`.

Partial blended return:

```text
partial_return_pct = ((partial_trigger_price / reference_price) - 1) * 100
remaining_return_pct = ((remaining_exit_price / reference_price) - 1) * 100

gross_return_pct = partial_size * partial_return_pct + (1 - partial_size) * remaining_return_pct
```

If `partial_mode = none`:

```text
gross_return_pct = full-position exit return
```

### Simulation status

Allowed `simulation_status` values:

```text
evaluated
not_evaluable
```

`evaluated` means the event-model pair produced a deterministic terminal exit using available 3A path data.

`not_evaluable` means the event-model pair could not be simulated with trustworthy inputs. It is not a failed trade and must not be scored as a loss.

Allowed `exit_reason` values:

```text
stop
partial_then_stop
partial_then_trail
partial_then_time_stop
partial_then_path_incomplete
time_stop
path_incomplete
not_evaluable_missing_reference_price
not_evaluable_missing_atr
not_evaluable_invalid_stop
not_evaluable_invalid_partial_trigger
not_evaluable_missing_bar_path
```

For `simulation_status = not_evaluable`, return fields must be `null`.

### Sequence diagnostics

For every event-model row, output sequence diagnostics:

```text
partial_filled
partial_bar_index_4h
partial_timestamp
stopped_before_partial
stopped_before_mfe
partial_before_stop
mfe_before_mae
mae_before_mfe
```

Definitions:

```text
stopped_before_partial = true iff exit_reason = stop and partial_filled = false.
partial_before_stop = true iff partial_filled = true and the final exit reason is partial_then_stop.
stopped_before_mfe applies to both exit_reason = stop and exit_reason = partial_then_stop.
stopped_before_mfe = true iff the stop-exit bar has bar_index_4h < the original 3A mfe_bar_index_4h.
For exit_reason = partial_then_stop, use the final stop-leg bar as the stop-exit bar.
mfe_before_mae = true iff mfe_bar_index_4h < mae_bar_index_4h.
mae_before_mfe = true iff mae_bar_index_4h < mfe_bar_index_4h.
```

If any required index is missing, the corresponding field is `null`, not `false`.

### Segment-specific diagnostic metric

Define `recovery_after_initial_mae` at event level as:

```text
An event has recovered after initial MAE if, after the bar where MAE occurs,
there is any later bar within the available 42-bar path with return_close_pct >= 0.
```

In segment summaries:

```text
recovery_after_initial_mae_rate = mean(recovery_after_initial_mae over evaluable events where mae_bar_index_4h is known)
```

This field is especially relevant for `early_candidates__early_reversal_break`.

### Deterministic `exit_model_id`

`exit_model_id` must be deterministic and stable.

Format:

```text
stop_<stop_token>__partial_<partial_token>__trail_<trail_token>__time<time_stop_hours>h
```

Token rules:

```text
ATR stop 1.2          -> stop_atr1p2
Fixed stop 8%         -> stop_fixed8pct
Partial none          -> partial_none_0pct
Fixed partial 7.5 40% -> partial_fixed7p5pct_40pct
R partial 1.5 50%     -> partial_r1p5_50pct
Trail none            -> trail_none
Trail low 2 bars      -> trail_low2bars
Trail low 3 bars      -> trail_low3bars
Time 96h              -> time96h
```

Examples:

```text
stop_atr1p2__partial_fixed5pct_40pct__trail_none__time96h
stop_fixed8pct__partial_fixed7p5pct_50pct__trail_low2bars__time72h
stop_atr1p5__partial_r1p5_40pct__trail_low3bars__time168h
stop_atr1p0__partial_none_0pct__trail_none__time24h
```

Do not invent another `exit_model_id` format.

### Expected default matrix size

Default model count must be deterministic:

```text
ATR stops: 4
Fixed-percent stops: 3
Time stops: 6
```

For ATR stops:

```text
partial_none + trail_none: 1
fixed_pct partials: 3 triggers * 2 sizes * 3 trail modes = 18
r_multiple partials: 3 triggers * 2 sizes * 3 trail modes = 18
ATR model variants = 4 * (1 + 18 + 18) * 6 = 888
```

For fixed-percent stops:

```text
partial_none + trail_none: 1
fixed_pct partials: 3 triggers * 2 sizes * 3 trail modes = 18
r_multiple partials: not allowed
fixed model variants = 3 * (1 + 18) * 6 = 342
```

Default total:

```text
exit_model_variant_count = 1230
```

With the current default 228-event BACKTEST-3A input:

```text
expected event-model rows = 1230 * 228 = 280440
```

This size is acceptable for a simple deterministic pandas / Python loop implementation. Do not introduce multiprocessing, databases, persistent caches, or optimization layers unless profiling proves necessary.

## Implementation Notes

### Dataflow

1. Parse CLI arguments.
2. Validate CLI argument values.
3. Preflight input files and required columns.
4. Read 3A event-level and bar-level outputs.
5. Validate event IDs:
   - event-level `event_id` unique;
   - bar-level rows reference known event IDs;
   - bar-level rows sorted deterministically by `event_id`, `bar_index_4h`, `bar_timestamp`.
6. Build deterministic exit-model matrix.
7. Simulate every event-model pair.
8. Build event-model output table.
9. Build segment summary table.
10. Build JSON summary.
11. Build Markdown report.
12. Write outputs atomically.

### Numeric handling

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid / not evaluable and must not be passed through into numeric-looking outputs.

For event-model rows where required numeric inputs are missing or invalid:

```text
simulation_status = not_evaluable
exit_reason = specific not_evaluable_* reason
gross_return_pct = null
exit_price = null
exit_bar_index_4h = null
```

### Output ordering

Event-model output ordering:

```text
segment_key ASC
event_id ASC
exit_model_id ASC
```

Segment summary ordering:

```text
segment_key ASC
median_return_pct DESC with nulls last
exit_model_id ASC
```

If sorting by metric is not appropriate for a specific output, use a stable deterministic documented order and test it.

### Atomic writes

If `--strict-preflight` is true:

- all path, schema, and CLI validation must happen before writes;
- failures leave 0 partial output files;
- write to a temporary directory and atomically replace / move into the final output directory.

If output files already exist and `--overwrite` is not set:

- fail before writes.

### Report wording

The Markdown report may rank observed in-sample variants by segment, but must not say or imply:

```text
recommended live exit model
approved live exit rule
production exit configuration
```

Allowed wording:

```text
best_by_segment_observed_in_sample
highest_median_return_in_sample
lowest_stop_before_partial_rate_in_sample
```

## Required Output Schema

### Event-model output: `exit_model_simulation_4h.*`

Required columns:

```text
event_id
symbol
segment_key
decision_bucket
entry_pattern
signal_timestamp
exit_model_id
simulation_status
initial_stop_mode
initial_stop_value
stop_price
partial_mode
partial_trigger_value
partial_trigger_price
partial_size
trail_mode
time_stop_hours
exit_reason
exit_bar_index_4h
exit_timestamp
exit_price
gross_return_pct
reference_price
reference_price_source
mfe_pct
mae_pct
mfe_bar_index_4h
mae_bar_index_4h
time_to_mfe_hours
time_to_mae_hours
partial_filled
partial_bar_index_4h
partial_timestamp
stopped_before_partial
stopped_before_mfe
partial_before_stop
mfe_before_mae
mae_before_mfe
recovery_after_initial_mae
path_coverage_status
available_path_bars
required_path_bars
```

Nullability:

- `stop_price`, `partial_trigger_price`, `exit_price`, `gross_return_pct`, `exit_bar_index_4h`, `exit_timestamp` are nullable when `simulation_status = not_evaluable`.
- `partial_trigger_price` is also nullable when `partial_mode = none`.
- `partial_bar_index_4h` and `partial_timestamp` are nullable when partial is not filled.
- sequence booleans may be nullable when required sequence indices are unknown.

### Segment summary output: `exit_model_segment_summary.*`

Required columns:

```text
segment_key
exit_model_id
simulation_status_evaluated_count
simulation_status_not_evaluable_count
trade_count
median_return_pct
mean_return_pct
p25_return_pct
p75_return_pct
win_rate
loss_rate
median_exit_hours
partial_fill_rate
stop_rate
time_exit_rate
trail_exit_rate
path_incomplete_rate
stopped_before_partial_rate
stopped_before_mfe_rate
partial_before_stop_rate
mfe_before_mae_rate
mae_before_mfe_rate
recovery_after_initial_mae_rate
```

Definitions:

```text
trade_count = number of evaluated event-model rows in that segment/model.
win_rate = fraction of evaluated rows with gross_return_pct > 0.
loss_rate = fraction of evaluated rows with gross_return_pct < 0.
partial_fill_rate = fraction of evaluated rows where partial_filled = true.
stop_rate = fraction of evaluated rows where exit_reason in {stop, partial_then_stop}.
time_exit_rate = fraction of evaluated rows where exit_reason in {time_stop, partial_then_time_stop}.
trail_exit_rate = fraction of evaluated rows where exit_reason = partial_then_trail.
path_incomplete_rate = fraction of all rows, evaluated and not_evaluable, with exit_reason in {path_incomplete, partial_then_path_incomplete}.
```

### JSON summary: `exit_model_simulation_summary.json`

Must include at least:

```text
analysis_id
scenario_id
replay_id
input_events_path
input_bars_path
input_summary_path
output_dir
event_count
bar_row_count
exit_model_variant_count
event_model_row_count
simulation_status_counts
segments
model_grid
best_by_segment_observed_in_sample
created_utc
exit_simulation_performed
late_monitor_included
fees_included
slippage_included
execution_simulation_included
```

Required values:

```text
analysis_id = BACKTEST-3B_EXIT_MODEL_SIMULATION_4H
exit_simulation_performed = true
late_monitor_included = false
fees_included = false
slippage_included = false
execution_simulation_included = false
```

## Acceptance Criteria (deterministic)

1. A new CLI script exists at `scripts/backtest/simulate_exit_model_variants_4h.py`.
2. The script reads BACKTEST-3A event-level and bar-level outputs from explicit CLI paths or defaults.
3. The script fails preflight before writes if required input files or required columns are missing.
4. The script fails preflight before writes for invalid CLI matrix values, including non-positive numbers, non-finite values, unknown trail modes, time stops not divisible by 4, or partial sizes outside `(0, 1]`.
5. With the default matrix, the script creates exactly `1230` deterministic `exit_model_id` values.
6. With the latest default 228-event BACKTEST-3A input, the script creates exactly `280440` event-model rows.
7. `exit_model_id` values follow the specified tokenized format exactly.
8. Same-bar `low_4h <= stop_price` and `high_4h >= partial_trigger_price` results in `exit_reason = stop`; partial is not filled.
9. Stop exits use `exit_price = stop_price`; time exits use the time-stop bar close; trail exits use the trail-trigger bar close; partial exits use `exit_price` for the remaining-leg terminal exit while `gross_return_pct` is blended.
10. `stopped_before_mfe` applies to both `stop` and `partial_then_stop` and uses the actual stop-exit bar compared to the original 3A `mfe_bar_index_4h`.
11. Trail modes activate only from the bar after the partial-fill bar.
12. `trail_low_2bars` and `trail_low_3bars` use the low of the 2 or 3 bars preceding the current bar, respectively, and exit at current bar close when the close breaches that trailing threshold.
13. `partial_mode = none` only combines with `trail_mode = none`.
14. `partial_mode = r_multiple` is generated only for ATR stop models.
15. Missing reference price produces `simulation_status = not_evaluable`, a specific `not_evaluable_*` exit reason, and null return fields.
16. Missing ATR produces `simulation_status = not_evaluable` for ATR stop models, not for fixed stop models.
17. Partial path coverage produces evaluated rows only when the simulated exit occurs before unavailable bars; otherwise rows are `not_evaluable` with `exit_reason = path_incomplete` or `partial_then_path_incomplete`.
18. Outputs are written as Parquet, CSV, JSON, and Markdown at the specified output directory.
19. Output ordering is deterministic across repeated runs with identical inputs and CLI arguments.
20. Strict preflight failures leave zero partial output files.
21. The Markdown report contains segmentwise results and does not contain live recommendation wording.
22. The script does not include fees, slippage, orderbook execution, late_monitor, EMA20 trail, or production scanner changes.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ (AC: #2, #5 ; Tests: CLI defaults produce 1230 models)
- **Config Invalid Value Handling:** ✅ (AC: #4 ; Tests: invalid time stop, invalid trail mode, invalid partial size, non-finite numeric)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #15, #16, #17 ; Tests: missing reference, missing ATR, path incomplete preserve null return fields)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #15, #16, #17 ; Tests: not_evaluable rows are not scored as losses)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (AC: #3, #4, #20 ; Tests: invalid input path leaves no outputs)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (AC: #5, #7 ; Tests: all exit_model_id values unique and deterministic)
- **Deterministische Sortierung/Tie-breaker:** ✅ (AC: #19 ; Tests: repeated run yields identical CSV/JSON content or stable dataframe equality)

Every preflight-required category is covered by at least one explicit test case or explicit verification.

## Tests (required if logic changes)

Add tests in:

```text
tests/backtest/test_simulate_exit_model_variants_4h.py
```

### Unit tests

1. `test_default_model_grid_count_and_ids`
   - Build default matrix.
   - Assert 1230 models.
   - Assert expected IDs exist:
     - `stop_atr1p2__partial_fixed5pct_40pct__trail_none__time96h`
     - `stop_fixed8pct__partial_fixed7p5pct_50pct__trail_low2bars__time72h`
     - `stop_atr1p5__partial_r1p5_40pct__trail_low3bars__time168h`
     - `stop_atr1p0__partial_none_0pct__trail_none__time24h`

2. `test_same_bar_stop_partial_collision_stop_wins`
   - One event, one bar where low breaches stop and high hits partial.
   - Assert `exit_reason = stop`, `partial_filled = false`, no partial return is included, and `exit_price = stop_price`.

3. `test_exit_price_semantics_by_exit_reason`
   - Construct stop, time-stop, partial-then-stop, partial-then-trail, and partial-then-time-stop cases.
   - Assert stop exits use `stop_price`, time exits use time-stop bar close, trail exits use trail-trigger bar close, and partial exits store the remaining-leg terminal price in `exit_price` while using blended `gross_return_pct`.

4. `test_stopped_before_mfe_for_partial_then_stop`
   - Construct a partial fill followed by a stop before the original 3A `mfe_bar_index_4h`.
   - Assert `exit_reason = partial_then_stop`, `partial_filled = true`, and `stopped_before_mfe = true`.

5. `test_stopped_before_mfe_false_when_stop_after_mfe`
   - Construct a stop or partial-then-stop after the original 3A `mfe_bar_index_4h`.
   - Assert `stopped_before_mfe = false`.

6. `test_partial_then_time_stop_same_bar`
   - Same bar hits partial and reaches time stop, but does not hit stop.
   - Assert partial fills and remaining exits at close.

7. `test_trail_activates_only_after_partial_bar`
   - Partial fills in bar N.
   - Trail condition also appears in bar N.
   - Assert trail does not exit until bar N+1 or later.

8. `test_trail_low_2bars_uses_preceding_lows`
   - Construct bars where current close breaches min of two preceding lows.
   - Assert trail exit at current close.

9. `test_partial_none_allows_only_trail_none`
   - Matrix generation must not produce `partial_none` with `low_2bars` or `low_3bars`.

10. `test_r_multiple_partials_only_for_atr_stops`
   - Matrix generation must not produce fixed-stop + r-multiple partial variants.

11. `test_missing_reference_price_not_evaluable`
   - Event reference missing.
   - Assert return fields null and status not_evaluable.

12. `test_missing_atr_only_invalidates_atr_stop_models`
   - ATR missing.
   - Assert ATR stop model not_evaluable; fixed stop model still evaluable.

13. `test_path_incomplete_when_time_stop_bar_missing`
    - Available bars fewer than requested time-stop bar.
    - No earlier stop/partial/trail terminal exit.
    - Assert not_evaluable path incomplete.

14. `test_non_finite_numeric_values_rejected_or_not_evaluable`
    - Include `NaN`, `inf`, `-inf` in required numeric inputs.
    - Assert invalid CLI values fail; row-level invalids produce not_evaluable where appropriate.

15. `test_deterministic_output_order`
    - Same inputs and config produce identical sorted outputs.

### Integration tests

1. `test_cli_writes_expected_files_atomically`
   - Run script on a small fixture.
   - Assert all required output files exist.
   - Assert JSON summary has required flags and counts.

2. `test_cli_invalid_input_schema_fails_before_writes`
   - Missing required column.
   - Assert non-zero exit and no partial output files.

3. `test_segment_summary_metrics_are_segmentwise`
   - Fixture with at least two segments and two models.
   - Assert summary rows are grouped by segment and model.

4. `test_markdown_report_no_live_recommendation_language`
   - Assert report does not include forbidden phrases:
     - `recommended live exit model`
     - `approved live exit rule`
     - `production exit configuration`

### Golden fixture / verification

No production scoring, threshold, or curve behavior changes are introduced. Do not update `docs/canonical/VERIFICATION_FOR_AI.md` unless the repo has an existing convention requiring analysis-script verification entries.

Run:

```bash
python -m pytest tests/backtest/test_simulate_exit_model_variants_4h.py -q
python -m pytest -q
```

## Constraints / Invariants (must not change)

- [ ] No lookahead beyond the provided 3A bar path.
- [ ] Closed-candle-only semantics are preserved.
- [ ] No live scanner code changes.
- [ ] No entry, phase, state, bucket, ranking, or execution logic changes.
- [ ] No `late_monitor` mixing into Primary-Scope exit calibration.
- [ ] No fees, slippage, or orderbook execution assumptions.
- [ ] No EMA20 recomputation in 3B v0.
- [ ] Not-evaluable rows must not be counted as losing trades.
- [ ] Same input + same CLI args must produce identical outputs.
- [ ] Existing BACKTEST-3A artifacts remain read-only inputs.

---

## Definition of Done (Codex must satisfy)

Reference: `docs/canonical/WORKFLOW_CODEX.md` if present in repo.

- [ ] Implemented code changes per Acceptance Criteria.
- [ ] Added/updated tests per the Tests section.
- [ ] `python -m pytest tests/backtest/test_simulate_exit_model_variants_4h.py -q` passes.
- [ ] `python -m pytest -q` passes.
- [ ] Ran the script against the latest valid BACKTEST-3A outputs if those artifacts are available in the environment; otherwise reported the expected preflight limitation clearly.
- [ ] Produced the required output files in the target output directory when inputs are available.
- [ ] Did not modify production scanner logic.
- [ ] Did not modify canonical v2.1 business specifications.
- [ ] PR created: exactly 1 ticket → 1 PR.
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created.

---

## Metadata

```yaml
created_utc: "2026-05-31T09:40:00Z"
priority: P2
type: feature
owner: codex
related_analysis:
  - BACKTEST-3A_EXIT_PATH_METRICS_4H
  - hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z
related_inputs:
  - evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_metrics_4h.parquet
  - evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_returns_by_bar.parquet
  - evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h/exit_path_metrics_4h_summary.json
related_issues: []
```
