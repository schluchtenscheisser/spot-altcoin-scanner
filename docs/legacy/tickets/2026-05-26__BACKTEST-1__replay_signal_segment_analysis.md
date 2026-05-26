> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# 2026-05-26 — BACKTEST-1 — Replay Signal Segment Analysis

## Status

Draft for review.

## Purpose

Build the first deterministic Backtest-1 analysis layer on top of the BACKTEST-MERGE-1 export dataset.

This ticket does **not** change replay generation, signal generation, state-machine semantics, forward-return calculation, or merge/export semantics. It consumes the already-created `enriched_replay_events.parquet` dataset and produces segment-level return summaries for signal-quality evaluation.

## Current authoritative reference set

The current implementation must remain consistent with:

- the approved BACKTEST-MERGE-1 output contract,
- the current `enriched_replay_events.parquet` schema,
- the current replay scenario `hsq_replay_2025_05_to_2026_05_v1`,
- the current no-lookahead rule: forward returns are evaluation labels only,
- the current MarketCap policy: no current/historical MarketCap feature is available for this dataset; quote-volume proxies are used instead.

If this ticket, existing repo documentation, and current code disagree, the implemented BACKTEST-MERGE-1 dataset contract wins for this ticket.

## Context

BACKTEST-MERGE-1 now produces a validated dataset:

```text
evaluation/backtest/exports/<scenario_id>/<replay_id>/enriched_replay_events.parquet
```

The validated real-run dataset currently contains:

```text
raw_event_count: 1523
signal_analysis_event_count: 1328
primary_analysis_event_count: 574
primary_signal_analysis_event_count: 516
duplicate_signal_event_count: 195
duplicate_signal_event_count_by_event_type: {"first_confirmed_ready": 195}
```

BACKTEST-MERGE-1 also provides:

- `included_in_primary_analysis`
- `included_in_signal_analysis`
- `analysis_event_type`
- `dedup_group_key`
- `analysis_event_rank`
- `dedup_reason`
- forward-return labels:
  - `forward_close_return_1d`
  - `forward_close_return_3d`
  - `forward_close_return_5d`
  - `forward_close_return_10d`
  - `forward_close_return_20d`
- availability flags:
  - `has_forward_1d`
  - `has_forward_3d`
  - `has_forward_5d`
  - `has_forward_10d`
  - `has_forward_20d`
- BTC regime fields:
  - `btc_regime_week`
  - `btc_regime_label`
  - `btc_30d_return`
  - `btc_30d_realized_vol`
- OHLCV-derived liquidity/size proxies:
  - `signal_day_quote_volume`
  - `median_quote_volume_30d`
  - `median_quote_volume_90d`
  - `quote_volume_bucket`
  - `available_history_days_1d_at_event`

The manual exploratory analysis showed meaningful signal structure, but that analysis was ad hoc. This ticket turns it into a reproducible analysis script and output contract.

## Problem

Manual Codespace analysis is not sufficient as a durable evaluation layer.

We need a repeatable script that:

1. reads the BACKTEST-MERGE-1 enriched dataset,
2. applies the correct default analysis filters,
3. computes segment-level forward-return metrics,
4. writes machine-readable and human-readable reports,
5. preserves separation between raw-event analysis and deduplicated signal-quality analysis,
6. prevents accidental double-counting of confirmed events,
7. prevents accidental inclusion of the May 2025 boundary month in the default primary analysis.

## Goal

Create a deterministic BACKTEST-1 segment analysis utility that summarizes forward-return labels by relevant signal, phase, pattern, regime, and quote-volume segments.

## Non-goals

Do **not** implement:

- new replay semantics,
- new signal/event generation,
- new state-machine logic,
- new BACKTEST-MERGE-1 logic,
- new forward-return formulas,
- MFE/MAE calculations,
- next-daily-open returns,
- terminal-event special return semantics,
- execution / orderbook / MEXC liquidity evaluation,
- MarketCap fetching or current MarketCap enrichment,
- trading recommendations,
- automatic config/ranking recalibration,
- strategy P&L simulation,
- stop-loss/take-profit/exit modeling.

This ticket is segment-level descriptive analysis only.

## New script

Create:

```text
scripts/backtest/analyze_replay_event_dataset.py
```

## CLI

Required:

```bash
python scripts/backtest/analyze_replay_event_dataset.py \
  --dataset evaluation/backtest/exports/<scenario_id>/<replay_id>/enriched_replay_events.parquet \
  --output-root evaluation/backtest/reports
```

Optional:

```text
--min-count
  default: 10
  positive integer

--horizons
  default: 1,3,5,10,20
  comma-separated positive integers
  each horizon requires columns:
    forward_close_return_<N>d
    has_forward_<N>d

--analysis-scope
  enum: primary_signal | primary_raw | full_signal | full_raw
  default: primary_signal

--sort-horizon
  default: 3
  must be one of --horizons

--include-appendix
  default: true
  if true, write additional appendix tables for non-default scopes

--output-dir
  optional explicit output directory
  if omitted, derive from dataset scenario_id/replay_id as:
    <output-root>/<scenario_id>/<replay_id>/
```

## Analysis scopes

The script must support four explicit scopes.

### `primary_signal` — default

Filter:

```text
included_in_primary_analysis == true
included_in_signal_analysis == true
```

Purpose:

- default signal-quality analysis,
- excludes May 2025 boundary month,
- avoids confirmed-event double-counting.

### `primary_raw`

Filter:

```text
included_in_primary_analysis == true
```

Purpose:

- raw transition-event analysis after analysis start date,
- still includes duplicate raw events.

### `full_signal`

Filter:

```text
included_in_signal_analysis == true
```

Purpose:

- deduplicated signal analysis including May 2025 boundary month.

### `full_raw`

Filter:

```text
no filter
```

Purpose:

- raw transition-event inventory over the whole dataset,
- not default for signal-quality conclusions.

## Required input validation

Fail fast with a clear error if:

1. `--dataset` does not exist.
2. The dataset is empty.
3. Required identity columns are missing:
   - `scenario_id`
   - `replay_id`
   - `symbol`
   - `as_of_daily_bar_id`
4. Required analysis flags are missing:
   - `included_in_primary_analysis`
   - `included_in_signal_analysis`
5. Required grouping fields are missing:
   - `historical_signal_bucket`
   - `analysis_event_type`
   - `event_type`
   - `entry_pattern`
   - `market_phase`
   - `quote_volume_bucket`
   - `btc_regime_label`
6. For any requested horizon `N`, either required column is missing:
   - `forward_close_return_<N>d`
   - `has_forward_<N>d`
7. `--min-count <= 0`.
8. `--sort-horizon` is not included in `--horizons`.
9. `--analysis-scope` is not one of the supported enum values.

## Required outputs

Write under:

```text
evaluation/backtest/reports/<scenario_id>/<replay_id>/
```

unless `--output-dir` is explicitly provided.

Required files:

```text
backtest_summary.md
backtest_summary.json
segment_returns.parquet
segment_returns.csv
```

Optional but recommended appendix outputs:

```text
appendix_primary_raw_segment_returns.csv
appendix_full_signal_segment_returns.csv
appendix_full_raw_segment_returns.csv
```

Appendix files should only be created when `--include-appendix` is enabled.

## Segment groups

Compute segment summaries for at least the following group definitions:

### Single-dimension groups

```text
historical_signal_bucket
analysis_event_type
event_type
entry_pattern
market_phase
quote_volume_bucket
btc_regime_label
```

### Two-dimension groups

```text
historical_signal_bucket × entry_pattern
historical_signal_bucket × analysis_event_type
market_phase × entry_pattern
btc_regime_label × historical_signal_bucket
quote_volume_bucket × historical_signal_bucket
quote_volume_bucket × entry_pattern
```

### Special control group

```text
ALL
```

The `ALL` group summarizes the full selected scope.

## Output schema: `segment_returns.parquet` and `.csv`

Each row represents one segment.

Required columns:

### Segment identity

```text
scope
segment_group
segment_key
segment_key_1
segment_key_2
```

Rules:

- For single-dimension groups:
  - `segment_key = value`
  - `segment_key_1 = value`
  - `segment_key_2 = null`
- For two-dimension groups:
  - `segment_key = <value_1> | <value_2>`
  - `segment_key_1 = value_1`
  - `segment_key_2 = value_2`
- For `ALL`:
  - `segment_key = ALL`
  - `segment_key_1 = ALL`
  - `segment_key_2 = null`

### Counts

```text
count
distinct_symbols
distinct_days
```

### Horizon metrics

For each requested horizon `N`:

```text
available_count_<N>d
missing_count_<N>d
mean_return_<N>d
median_return_<N>d
win_rate_<N>d
positive_count_<N>d
negative_count_<N>d
flat_count_<N>d
min_return_<N>d
max_return_<N>d
p25_return_<N>d
p75_return_<N>d
```

Metric definitions:

- Use only rows where `has_forward_<N>d == true` and `forward_close_return_<N>d` is finite.
- `available_count_<N>d` = count of rows used for that horizon.
- `missing_count_<N>d` = `count - available_count_<N>d`.
- `win_rate_<N>d` = `positive_count_<N>d / available_count_<N>d`.
- `positive_count_<N>d` = count where return > 0.
- `negative_count_<N>d` = count where return < 0.
- `flat_count_<N>d` = count where return == 0.
- If `available_count_<N>d == 0`, metric values must be null, not zero.

### Ranking / display helpers

```text
passes_min_count
sort_metric
sort_horizon
```

Rules:

- `passes_min_count = count >= min_count`
- `sort_metric = mean_return_<sort_horizon>d`
- `sort_horizon = <configured sort horizon>`

## Nullability and numeric robustness

- Non-finite returns (`NaN`, `inf`, `-inf`) must be treated as missing.
- Non-finite numeric outputs must not be written as numeric values.
- Missing metrics must be written as null.
- Missing segment values should be represented as `null` in Parquet and as empty or `<NA>` in CSV consistently.
- Do not coerce missing numeric values to `0`.
- Do not coerce nullable booleans to false unless explicitly required by scope filter.

## Default report interpretation rules

`backtest_summary.md` must clearly state:

1. Default scope is `primary_signal`.
2. `primary_signal` means:

```text
included_in_primary_analysis == true
included_in_signal_analysis == true
```

3. May 2025 boundary-month rows are excluded from the default primary analysis but retained in full-scope appendix outputs.
4. Confirmed raw duplicate events are excluded from default signal-quality analysis via `included_in_signal_analysis`.
5. Forward returns are labels, not signal inputs.
6. MarketCap is unavailable point-in-time and not used.
7. Quote-volume buckets are OHLCV-derived proxies, not execution/liquidity guarantees.
8. No orderbook, MEXC depth, slippage, or execution filters are applied in this backtest.

## Required `backtest_summary.json`

Write machine-readable metadata and summary:

```json
{
  "scenario_id": "...",
  "replay_id": "...",
  "dataset_path": "...",
  "created_at_utc": "...",
  "analysis_scope": "primary_signal",
  "min_count": 10,
  "horizons": [1, 3, 5, 10, 20],
  "sort_horizon": 3,
  "input_row_count": 1523,
  "selected_row_count": 516,
  "raw_event_count": 1523,
  "signal_analysis_event_count": 1328,
  "primary_analysis_event_count": 574,
  "primary_signal_analysis_event_count": 516,
  "segment_row_count": 0,
  "segment_row_count_passing_min_count": 0,
  "top_segments_by_mean_return": {
    "1d": [],
    "3d": [],
    "5d": [],
    "10d": [],
    "20d": []
  },
  "scope_definitions": {...},
  "warnings": [],
  "validation_status": "passed",
  "validation_errors": []
}
```

The exact counts above are examples from the current real dataset; the script must compute them from input.

## Markdown report structure

`backtest_summary.md` must include at least:

1. Title and run metadata
2. Scope explanation
3. Dataset counts
4. Overall selected-scope return summary
5. Top segments by configured sort horizon
6. Segment summaries by:
   - historical signal bucket
   - analysis event type
   - entry pattern
   - market phase
   - quote-volume bucket
   - BTC regime
7. Notes / caveats
8. Paths to generated artifacts

The Markdown report should not overstate conclusions. It should use language such as:

```text
This is descriptive segment analysis, not a trading-strategy P&L simulation.
```

## Determinism

At identical input and identical CLI arguments, all outputs must be deterministic.

Sorting rules for `segment_returns`:

```text
scope ASC
segment_group ASC
passes_min_count DESC
sort_metric DESC nulls last
count DESC
segment_key ASC
```

If exact implementation requires a different stable sort, document it in `backtest_summary.json`.

## No-lookahead rule

Forward returns are evaluation labels only. They must not affect:

- segment membership,
- scope filters,
- bucket assignment,
- event selection,
- ranking fields derived from signal state.

Only report sorting may use forward returns.

## Fail-fast behavior

Fail fast for invalid input schema or CLI arguments.

Do not silently drop rows except by explicit analysis-scope filtering.

Segments below `--min-count` must still be written, but marked with:

```text
passes_min_count = false
```

## Tests

Add focused tests under:

```text
tests/backtest/test_analyze_replay_event_dataset.py
```

Minimum tests:

1. CLI/input validation fails when dataset path is missing.
2. Required analysis flag missing fails.
3. Required forward-return column missing for requested horizon fails.
4. `primary_signal` scope selects only rows with both flags true.
5. `primary_raw` scope selects primary rows regardless of signal dedup flag.
6. `full_signal` scope selects all signal-analysis rows.
7. `full_raw` scope selects all rows.
8. Segment metrics compute mean/median/win-rate/counts correctly.
9. Missing forward returns are excluded from horizon metrics and counted as missing.
10. Non-finite forward returns are treated as missing.
11. `passes_min_count` is set but rows below min count are still written.
12. Two-dimensional segment keys are deterministic.
13. `ALL` segment is present.
14. Output files are written to the expected directory.
15. `backtest_summary.json` contains computed counts and top segment lists.
16. Markdown report includes required caveats about labels, MarketCap, and execution-disabled context.

Run:

```bash
pytest -q tests/backtest/test_analyze_replay_event_dataset.py
```

## Acceptance criteria

1. Script exists at `scripts/backtest/analyze_replay_event_dataset.py`.
2. Script can read a valid BACKTEST-MERGE-1 enriched dataset.
3. Default analysis scope is `primary_signal`.
4. Default analysis excludes May boundary rows and excludes duplicate confirmed raw events through existing dataset flags.
5. Segment summaries are written to Parquet and CSV.
6. Markdown and JSON summaries are written.
7. All required metrics are computed for all requested horizons.
8. Segments below `--min-count` are retained and flagged.
9. Missing/non-finite forward returns do not corrupt metrics.
10. No MarketCap or execution logic is introduced.
11. Tests pass.

## Definition of done

- Implementation merged.
- Focused pytest passes.
- A real Codespace run against the current BACKTEST-MERGE-1 export succeeds.
- `backtest_summary.md`, `backtest_summary.json`, `segment_returns.parquet`, and `segment_returns.csv` are generated.
- The report clearly states that this is descriptive analysis, not strategy P&L.

## Example real-run command

```bash
python scripts/backtest/analyze_replay_event_dataset.py \
  --dataset evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/enriched_replay_events.parquet \
  --output-root evaluation/backtest/reports \
  --min-count 10 \
  --analysis-scope primary_signal \
  --sort-horizon 3
```

Expected output directory:

```text
evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/
```
