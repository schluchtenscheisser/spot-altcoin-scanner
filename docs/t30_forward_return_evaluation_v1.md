# T30 Forward-Return Evaluation v1 Manual Run

T30 v1 is a manual, exploratory validation run over locally available Shadow-Live artifacts. It orchestrates the existing T18 evaluation export and writes a compact note plus a machine-readable summary; it does not fetch OHLCV, run trades, change thresholds, or integrate with scheduled workflows.

## Required local inputs

Before running T30, unpack the relevant Shadow-Live artifacts into the worktree so these paths are present:

```text
snapshots/runs/**/run.manifest.json
reports/runs/**/symbol_diagnostics.jsonl.gz
snapshots/history/ohlcv/timeframe=1d/symbol=*/year=*/month=*/*.parquet
```

If OHLCV history is missing, generate it with the T30-Pre-2 helper first:

```bash
python scripts/fetch_ohlcv_history_for_evaluation.py --project-root .
```

## Run command

From the repository root:

```bash
python scripts/run_t30_evaluation.py --project-root .
```

Useful flags:

```bash
python scripts/run_t30_evaluation.py \
  --project-root . \
  --evaluation-start-date 2026-05-03 \
  --history-root snapshots/history \
  --include-first-watch-metrics \
  --fail-on-missing-inputs
```

`--history-root` may be relative to `--project-root` or absolute. The runner validates and passes the same effective history root into `scanner.evaluation.dataset_export.run_evaluation_export(...)`; it must contain `ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/*.parquet` below that root.

The script validates replay manifests and candidate-scoped 1d OHLCV before running the T18 export.

## Outputs

Expected local outputs are:

```text
evaluation/exports/signal_event_metrics.parquet
evaluation/exports/terminal_event_timeline.parquet
evaluation/exports/transition_lead_times.parquet
evaluation/exports/evaluation_summary.json
evaluation/replay/event_timeline.jsonl
evaluation/replay/replay_manifest.json
evaluation/replay/replay_diagnostics.json
evaluation/replay/t30_run_summary.json
evaluation/notes/T30_forward_return_evaluation_v1.md
```

The generated note is exploratory and must not be read as a final performance conclusion. It preserves distinct metric statuses such as `ok`, `insufficient_future_data`, `missing_ohlcv_history`, and `reference_price_not_evaluable` instead of collapsing them into a generic failure bucket.
