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
- `schema_version` is currently `ir1.3` for newly emitted report/diagnostics artifacts.
- The output layer owns report/diagnostics/index writers in `scanner/output/`.
- `scan_mode` values are exactly `daily` or `intraday`.
- `run_id` is a non-empty opaque string (format not constrained here).
- `as_of_utc` uses `YYYY-MM-DDTHH:MM:SSZ`.
- `daily_bar_id` uses `YYYY-MM-DD` and is the date basis for report directories.
- `intraday_bar_id` is always present; for daily mode it is `null`, for intraday mode it is a canonical UTC 4h bar-id string (`YYYY-MM-DDTHH:00:00Z`).

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

Validation invariants are enforced centrally in `scanner/output/schema.py` via `validate_diagnostics_record`:
- `execution_attempted=true` requires coherent non-null execution context (`state`, `decision`, `phase`, cycle-id resolvability).
- non-null `decision.decision_bucket` requires non-null `state.state_machine_state`, except `decision.decision_bucket="discarded"` which may validly occur with `state.state_machine_state=null` for non-admitted / `market_phase="none"` records.
- active/event states (`watch|early_ready|confirmed_ready|late|chased|rejected`) require at least one cycle-id source (`state.setup_cycle_id`, `state.current_setup_cycle_id`, `cycle.resolved_setup_cycle_id`).

Replay compatibility:
- canonical writer contract remains nested blocks (`state.*`, `cycle.*`, `decision.*`, `phase.*`);
- replay extraction keeps backward-compatible top-level fallbacks and also accepts `cycle.resolved_setup_cycle_id` as cycle-id fallback.

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
