# Reports — Independence-Release Reports Architecture (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_REPORTS
status: canonical
role: active_independence_release
report_root: reports
```

## Document role
- Classification: `active_independence_release`
- This document defines the active Independence-Release reports architecture.


## Directory structure
```text
reports/
├── index/
├── daily/
├── runs/
├── aux/
└── archive/ (optional target path)
```

## Directory roles
- `reports/index/`: stable index-style artifacts that point to available reports or latest states.
- `reports/daily/`: daily discovery scan outputs.
- `reports/runs/`: run-specific report bundles and per-run material.
- `reports/aux/`: auxiliary report artifacts that support the primary report set without redefining canonical truth.
- `reports/archive/`: optional retention/archive destination (no archive job implied by this document).

## Canonical schema and ownership
- `schema_version` is fixed to `ir1.0`.
- The output layer owns report/diagnostics/index writers in `scanner/output/`.
- `scan_mode` values are exactly `daily` or `intraday`.
- `run_id` is a non-empty opaque string (format not constrained here).
- `as_of_utc` uses `YYYY-MM-DDTHH:MM:SSZ`.
- `daily_bar_id` uses `YYYY-MM-DD` and is the date basis for report directories.
- `intraday_bar_id` is always present; for daily mode it is `null`, for intraday mode it is an integer UTC-close timestamp (ms).

## Canonical run and daily artifacts
Run outputs:
- `reports/runs/YYYY/MM/DD/<run_id>/report.json`
- `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`

Daily outputs:
- `reports/daily/YYYY/MM/DD/report.json`

Path derivation rule:
- `YYYY/MM/DD` comes from `daily_bar_id` only (never from wall-clock time, never from `as_of_utc` date).

## `report.json` contract (compact summary)
Required top-level keys:
- `schema_version`
- `run_id`
- `scan_mode`
- `as_of_utc`
- `daily_bar_id`
- `intraday_bar_id`
- `counts_by_bucket`
- `symbol_lists`
- `manifest_path`
- `diagnostics_path`

### `counts_by_bucket` keys (all mandatory)
- `watchlist`
- `early_candidates`
- `confirmed_candidates`
- `late_monitor`
- `discarded`

### `symbol_lists` keys (exactly)
- `confirmed_candidates`
- `early_candidates`
- `watchlist`
- `late_monitor`

`discarded` is counted but not included in `symbol_lists`.

## Diagnostics artifact contract
`symbol_diagnostics.jsonl.gz` is the canonical full diagnostics output.

Each record contains at minimum:
- identity fields: `schema_version`, `run_id`, `scan_mode`, `symbol`, `as_of_utc`, `daily_bar_id`, `intraday_bar_id`
- data-resolution field: `data_4h_available` (the only canonical field for this distinction here)
- required block containers: `axes`, `phase`, `invalidation`, `cycle`, `state`, `pattern`, `decision`, `reasons`

This contract does not introduce `data_resolution_class`.

## Manifest reference semantics (no duplicate truth)
- Canonical manifest body remains under `snapshots/runs/.../run.manifest.json`.
- Report artifacts store only `manifest_path` as a repository-root-relative reference.
- The output layer does not require physical manifest existence at report write time.
- `latest_manifest.json` is optional and, if present, pointer-only (no manifest-body copy).

## Required index artifacts
- `reports/index/latest_run.txt`
- `reports/index/latest_paths.json`
- `reports/index/latest.json`
- `reports/index/latest_daily.json`
- `reports/index/latest_confirmed_candidates.json`
- `reports/index/latest_watchlist.json`
- `reports/index/recent_runs.json`

Semantics:
- `latest.json` is content-identical to latest run `report.json`.
- `latest_daily.json` is content-identical to latest daily `report.json`.
- `latest_confirmed_candidates.json` and `latest_watchlist.json` are JSON arrays of plain symbol strings.
- `recent_runs.json` is newest-first and bounded (`recent_runs_limit`, default `30`).
- All path fields are repository-root-relative.

## Writer determinism and atomicity
- Final artifacts use temp-file then atomic rename.
- Index files are updated only after run artifacts are finalized successfully.
- For identical input and config, report content and ordering are deterministic.
