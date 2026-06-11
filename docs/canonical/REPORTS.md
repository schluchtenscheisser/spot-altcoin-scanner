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

## Verbindliche Dateitypen
Die Independence-Release Reports-Struktur enthält verbindliche maschinenlesbare Canonical-Artefakte:
- `report.json` als kompakte Run-/Daily-Summary
- `symbol_diagnostics.jsonl.gz` als vollständige Symbol-Diagnostics
- `reports/index/*` als deterministische Latest-/Pointer-/Recent-Run-Artefakte

Optional können abgeleitete Convenience-Ausgaben (`report.md`, `report.xlsx`) existieren, sie sind aber nicht die Canonical-Truth-Ebene.

## Canonical schema and ownership
- `schema_version` is currently `ir1.5` for newly emitted report/diagnostics artifacts.
- The output layer owns report/diagnostics/index writers in `scanner/output/`.
- `scan_mode` values are exactly `daily` or `intraday`.
- `run_id` is a non-empty opaque string (format not constrained here).
- `as_of_utc` uses `YYYY-MM-DDTHH:MM:SSZ`.
- `daily_bar_id` uses `YYYY-MM-DD` and is the date basis for report directories.
- `intraday_bar_id` is always present; for daily mode it is `null`, for intraday mode it is a canonical UTC 4h bar-id string (`YYYY-MM-DDTHH:00:00Z`).

## Canonical run, daily, intraday, and snapshot-linked artifacts
Run outputs:
- `reports/runs/YYYY/MM/DD/<run_id>/report.json`
- `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`

Daily outputs:
- `reports/daily/YYYY/MM/DD/report.json`

Snapshot manifest:
- `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`

Path derivation rule:
- `YYYY/MM/DD` comes from `daily_bar_id` only (never from wall-clock time, never from `as_of_utc` date).
- Report paths are produced by the output/report writer layer under `scanner/output/`; daily and intraday runners call those writers after runner-specific data collection and diagnostics construction.
- Snapshot run-manifest placement is owned by the snapshot storage layer; reports carry `manifest_path` as a repository-root-relative reference and do not duplicate the manifest body.

### Artifact purpose and consumers

| Artifact | Producer path | Primary consumer purpose | Notes |
|---|---|---|---|
| `reports/runs/YYYY/MM/DD/<run_id>/report.json` | Output report writer called by daily/intraday runners | Compact machine-readable run summary and candidate/report segment surface | `latest.json` is a content-identical copy of the latest run report, regardless of scan mode. |
| `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz` | Diagnostics writer called by daily/intraday runners | Full row-level machine diagnostics for audit, analysis, and operational row-level labels | Prefer this artifact for per-symbol evidence such as `candidate_excluded`, `is_operational_trade_candidate`, execution fields, and Entry-Location blocks. |
| `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` | Snapshot storage/runner path | Run provenance and manifest body | `report.json.manifest_path` references this path; full manifest payload schema remains owned outside this report-summary contract. |
| `reports/daily/YYYY/MM/DD/report.json` | Daily discovery runner/report writer | Latest canonical daily candidate-producing report for that daily bar | Consumers needing daily candidates should prefer this path or `reports/index/latest_daily.json` over generic `latest.json`. |
| Intraday report under `reports/runs/.../report.json` | Intraday promotion runner/report writer | Intraday promotion or no-op run summary | No-op intraday reports may contain `no_op=true` and `no_op_reason`; diagnostics-only/no-op intraday runs must not clear candidate-oriented latest files. |

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

Validation invariants are enforced centrally in `scanner/output/schema.py` via `validate_diagnostics_record`:
- `execution_attempted=true` requires coherent non-null execution context (`state`, `decision`, `phase`, cycle-id resolvability).
- non-null `decision.decision_bucket` requires non-null `state.state_machine_state`, except `decision.decision_bucket="discarded"` which may validly occur with `state.state_machine_state=null` for non-admitted / `market_phase="none"` records.
- active/event states (`watch|early_ready|confirmed_ready|late|chased|rejected`) require at least one cycle-id source (`state.setup_cycle_id`, `state.current_setup_cycle_id`, `cycle.resolved_setup_cycle_id`).

Replay compatibility:
- canonical writer contract remains nested blocks (`state.*`, `cycle.*`, `decision.*`, `phase.*`);
- replay extraction keeps backward-compatible top-level fallbacks and also accepts `cycle.resolved_setup_cycle_id` as cycle-id fallback.

This contract does not introduce `data_resolution_class`.


## Current `ir1.5+` report and diagnostics field groups

Daily report consumers should read `reports/daily/YYYY/MM/DD/report.json` or `reports/index/latest_daily.json` for daily discovery candidates. Generic `reports/index/latest.json` points to the latest run report and may therefore point to intraday no-op or diagnostics-oriented runs. Diagnostics consumers should follow `diagnostics_path` from a report or latest index to `symbol_diagnostics.jsonl.gz` for row-level evidence.

For `ir1.5+`, actionable report candidate lists (`confirmed_candidates`, `early_candidates`, and `watchlist`) are already filtered so rows with `candidate_excluded=true` are not included as actionable candidates. Row-level operational consumers should prefer `is_operational_trade_candidate` wherever diagnostics or report segment rows expose it. `is_tradeable_candidate` remains useful as bucket-/execution-scoped audit evidence, but it is not the final operational label.

Execution-aware report blocks expose current implemented execution names such as `execution_status_raw`, `execution_size_class`, `execution_grade_effective`, and `is_reduced_size_eligible`. `execution_status` is not the active serialized artifact field. Report-level execution summaries may normalize raw `fail` into `failed` segment/count labels, so consumers must not expect report summary labels to be byte-identical to raw diagnostics values.

Entry-Location report support is segment-oriented. Current `ir1.5` daily reports emit exactly these `entry_location_candidate_segments` keys: `buy_now_candidates`, `wait_pullback_candidates`, `early_watch_candidates`, `good_location_but_not_tradeable`, and `tradeable_but_extended`. These segments are sourced from nested diagnostics fields under `entry_location`. The implemented diagnostics values are `entry_location.entry_location_status` and `entry_location.entry_action_hint`; field names such as `entry_location_bucket`, `entry_location_reason`, `entry_location_flags`, `entry_location_score`, `buy_now`, and `avoid_chase` are not current flat artifact fields unless a future schema introduces them explicitly. `avoid_chasing` is a valid `entry_location.entry_action_hint` value, but it is not currently an emitted `entry_location_candidate_segments` key; consumers must not expect an `avoid_chasing` key under `entry_location_candidate_segments` in current `ir1.5` daily reports. Consumers that need avoid-chasing rows should derive them by filtering emitted row fields, especially `entry_location.entry_action_hint == "avoid_chasing"`, or by inspecting `tradeable_but_extended` rows with `entry_location_status == "chased_entry"` when the row is tradeable and not excluded.

## Evaluation and legacy snapshot exporter boundary

Evaluation/T30 output schemas are outside this document's current-state data/report contract and remain subject to dedicated evaluation documentation and CODE-FU-B boundary resolution. Do not read this reports contract as canonizing Evaluation/T30 dataset fields such as forward-return, MFE/MAE, basket, or evaluation-dataset columns.

The linked path `scanner/tools/export_evaluation_dataset.py` together with `scanner.pipeline.global_ranking.compute_global_top20` and `scanner.backtest.e2_model` is classified here only as active executable legacy snapshot evaluation export tooling, but not active `scanner/evaluation/*` infrastructure and not active Daily/Intraday scanner runtime. This boundary prevents conflating legacy snapshot evaluation exports with current report/diagnostics artifacts while avoiding a premature inactive-legacy classification.

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
- `reports/index/latest_intraday.json`
- `reports/index/latest_confirmed_candidates.json`
- `reports/index/latest_watchlist.json`
- `reports/index/recent_runs.json`

Semantics:
- `latest.json` is content-identical to the latest run `report.json` for any scan mode, including no-op intraday runs.
- `latest_daily.json` is content-identical to the latest daily discovery run `report.json`.
- `latest_intraday.json` is content-identical to the latest intraday promotion run `report.json` when an intraday report is produced.
- `latest_confirmed_candidates.json` and `latest_watchlist.json` are JSON arrays of plain symbol strings from the latest candidate-producing report for that list. Daily runs are authoritative candidate-producing reports even when a candidate list is present and empty. Intraday reports update a candidate-specific latest file only when that candidate-list key was actually produced by the report.
- Diagnostics-only intraday runs, even with diagnostics records, must not clear candidate-oriented latest files. A present-but-empty candidate list means “candidate-producing run with zero candidates”; an absent candidate-list key means “this report did not produce that candidate list.”
- Consumers that need daily candidates should read `latest_daily.json` or the candidate-specific latest files, not assume `latest.json` always points to a candidate-producing run.
- Intraday no-op reports set `no_op=true`; `no_op_reason` reuses the existing intraday `skip_reason` string values such as `no_new_4h_bar` and `empty_monitoring_universe`. Non-no-op reports set `no_op=false` and `no_op_reason=null`.
- `recent_runs.json` is newest-first and bounded (`recent_runs_limit`, default `30`).
- All path fields are repository-root-relative.


## Shadow-Live repository persistence
- After a successful Shadow-Live report generation, the workflow may persist only small plaintext report/index artifacts and minimal replay manifests to the repository.
- Persisted allowlist: `reports/index/latest_run.txt`, `reports/index/latest.json`, `reports/index/latest_daily.json`, `reports/index/latest_intraday.json`, `reports/index/latest_confirmed_candidates.json`, `reports/index/latest_watchlist.json`, `reports/index/latest_paths.json`, `reports/index/recent_runs.json`, `reports/daily/YYYY/MM/DD/report.json`, `reports/runs/YYYY/MM/DD/<run_id>/report.json`, and `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`.
- Persisted JSON files must be non-empty valid JSON with the expected top-level type; `latest_run.txt` must be non-empty plaintext.
- Full diagnostics and large/generated data remain Actions-artifact-only and are intentionally excluded from repository commits, including `symbol_diagnostics.jsonl.gz`, Excel reports, Parquet files, ZIP archives, run snapshots except `run.manifest.json`, and raw market data.
- Workflow retry idempotency is evaluated over the complete persisted allowlist from the source artifact: every allowed target file must already exist, validate successfully, and match the source content. A valid daily run report alone is not a valid idempotency skip; missing, empty, invalid, or stale siblings are repaired from a valid source artifact.
- Candidate-specific latest files remain candidate-effective outputs: no-op or diagnostics-only intraday runs must not clear `latest_confirmed_candidates.json` or `latest_watchlist.json`.

## Writer determinism and atomicity
- Final artifacts use temp-file then atomic rename.
- Index files are updated only after run artifacts are finalized successfully.
- For identical input and config, report content and ordering are deterministic.

## Shadow-Live reporting overlay (Ticket 22)
- Shadow-live workflow emits one top-level workflow summary file:
  - `shadow-live-report.json`
- `shadow-live-report.json` is a workflow-orchestration summary (diagnostic/research) and does not replace canonical per-run `report.json` contracts.
- Shadow-live artifact uploads must include:
  - `shadow-live-report.json`
  - `snapshots/runs/**`
  - `reports/runs/**`
  - `evaluation/exports/**`
  - `evaluation/replay/**`
- Optional convenience uploads (non-blocking if absent):
  - `reports/daily/**`
  - `reports/index/**`

- **Universe classification + candidate segmentation (Ticket 23)**
  - Adds additive report blocks `universe_classification` and `candidate_segments` while keeping existing raw `counts_by_bucket` and `symbol_lists` backward-compatible.
  - Introduces deterministic categories: `classic_crypto`, `stable_or_cash_proxy`, `leveraged_or_margin_token`, `tokenized_stock_or_etf`, `commodity_or_index_proxy`, `wrapped_or_synthetic_btc`, `unknown`.
  - Candidate-facing exclusion applies only to `stable_or_cash_proxy` and `leveraged_or_margin_token`; raw bucket outputs remain unchanged.
  - Daily diagnostics include a mandatory `universe` block with `universe_category`, `universe_category_confidence`, `universe_category_reason`, `candidate_excluded`, `candidate_exclusion_reason`.

- **Execution-aware candidate segmentation (Ticket 24)**
  - Adds additive daily report blocks only: `execution_aware_summary`, `execution_counts_by_bucket`, `execution_counts_by_universe_category`, `execution_counts_by_bucket_and_category`, `execution_aware_candidate_segments`.
  - Existing `counts_by_bucket`, `symbol_lists`, `universe_classification`, and `candidate_segments` remain backward-compatible and unchanged in semantics.
  - Execution-aware structural candidate views use Ticket 23 candidate-visible/tradable semantics (active candidate buckets with `candidate_excluded == false`), not raw bucket populations.
  - Report-level recognized raw statuses are: `direct_ok`, `tranche_ok`, `marginal`, `fail`, `unknown`, and `null` for not-attempted symbols.
  - Under valid current grader output, executable means `execution_pass == true` with `execution_status_raw` in `{direct_ok, tranche_ok}`. Contradictory combinations are surfaced as `unexpected_execution_state` and are not counted as executable.
  - `marginal`, `failed`, `unknown_execution`, `not_attempted`, and `unexpected_execution_state` are always visible in counts/segments but non-executable.
