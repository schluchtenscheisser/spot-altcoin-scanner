# Active Code Path & Legacy Residue Inventory v0

## 1. Executive summary

CODE-A1 performed an audit-only inventory of active scanner entry points, current runtime/evaluation/script call paths, legacy-looking residue, test semantics, and artifact paths.

Key findings:

- The active scanner runtime dispatch is `scanner/main.py`, which loads config and routes `daily_discovery`, `standard`, `fast`, `offline`, and `backtest` modes to `scanner.runners.daily.run_daily_scan`, while `intraday_promotion` routes to `scanner.runners.intraday.run_intraday_scan`.
- The active Independence runtime path is centered on `scanner/runners/`, plus active module families under `scanner/axes/`, `scanner/data/`, `scanner/decision/`, `scanner/entry/`, `scanner/execution/`, `scanner/features/`, `scanner/output/`, `scanner/phase/`, `scanner/state/`, `scanner/storage/`, and `scanner/universe/`.
- `scanner/pipeline/` is explicitly self-labeled legacy in `scanner/pipeline/__init__.py` and is also treated as legacy/reference-only by current authority helpers. However, parts of `scanner/pipeline/` are still used by executable tools, tests, and one active execution utility (`scanner/execution/grading.py` imports `scanner.pipeline.liquidity.compute_tradeability_metrics`). This is an authority/implementation conflict that should be reviewed before DOC-D current-state documentation uses pipeline code as an architecture source.
- Current evaluation/replay paths are active under `scanner/evaluation/`, `scanner/tools/run_historical_daily_replay.py`, `scripts/generate_replay_chunk_plan.py`, `scripts/run_replay_chunks.py`, and backtest/analysis scripts under `scripts/backtest/`.
- Several old-style artifact paths still exist as checked-in historical artifacts or analysis defaults, especially root-level `reports/YYYY-MM-DD.{json,md}` and root-level `reports/*_*.manifest.json`; active runtime code and workflows expect `reports/runs/...`, `reports/daily/...`, `reports/index/...`, and `snapshots/runs/.../run.manifest.json` instead.
- No scanner code, tests, schemas, workflows, canonical current-state domain docs, or runtime behavior were changed by this ticket.

## 2. Authority and evidence rules used

Authority sources inspected:

1. `docs/canonical/AUTHORITY.md`.
2. `docs/canonical/INDEX.md`.
3. `docs/AI_CONTEXT_CURRENT.md`.
4. `docs/GPT_SNAPSHOT.md`.
5. `docs/code_map.md` as generated navigation only.
6. Current code, tests, workflows, checked-in reports/manifests, scripts, and tool modules.
7. Build-spec/canonical files only where not contradicted by current repository reality.

Evidence rules applied:

- Current repository reality is the primary anchor, but file existence alone does not make a module active.
- `docs/code_map.md` was used only as a navigation aid and not as authority.
- Active status required entry-point, workflow, import/call, script, test, or artifact-path evidence.
- Call-path tracing in the main path sections is limited to:
  - Level 0: entry point.
  - Level 1: directly invoked modules/functions.
  - Level 2: direct imports and directly invoked modules/functions from Level 1.
- Imports alone were not treated as proof that business logic executes.
- Test imports alone were not treated as proof of active runtime status.
- When evidence was conflicting or outside the call-depth limit, classification is `ambiguous` unless a more specific test-only/script-only classification was supported.

Classification taxonomies used exactly as required:

- Module/file classifications: `active_runtime`, `active_evaluation`, `active_analysis_script`, `active_utility`, `legacy_residue_unused`, `legacy_residue_test_only`, `ambiguous`.
- Evidence strength: `strong`, `medium`, `weak`, `none`.
- Audit follow-up hints: `none`, `investigate`, `clarify_authority_conflict`, `candidate_for_future_legacy_isolation_review`, `candidate_for_future_test_semantics_review`, `candidate_for_future_artifact_path_review`.
- Test classifications: `current_semantics_test`, `legacy_semantics_test`, `compatibility_test`, `schema_guard_test`, `utility_test`, `ambiguous_test`.
- Artifact path classifications: `expected_current`, `allowed_analysis_or_auxiliary`, `potentially_stale`, `confirmed_deprecated_by_authority`, `ambiguous`.

## 3. Runtime entry points

| Entry point | Trigger / caller | Level 1 direct calls | Classification | Evidence strength | Notes |
|---|---|---|---|---|---|
| `scanner/main.py` | `python -m scanner.main` or module execution | `load_config`, `run_daily_scan`, `run_intraday_scan` | `active_runtime` | strong | CLI parser accepts `daily_discovery`, `standard`, `fast`, `offline`, `backtest`, `intraday_promotion`; all non-intraday modes route to daily runner. |
| `scanner/runners/daily.py::run_daily_scan` | `scanner/main.py`, shadow-live/smoke scripts, tests | feature bundle, axes, phase, state, entry, decision, execution, report, manifest, SQLite persistence | `active_runtime` | strong | Current daily scanner path; writes run report, daily report, diagnostics, manifest, SQLite run metadata/state. |
| `scanner/runners/intraday.py::run_intraday_scan` | `scanner/main.py`, shadow-live/smoke scripts, tests | bar clock, context provider, execution selection/evaluation, report builder, manifest, SQLite run metadata | `active_runtime` | strong | Current intraday promotion path; reads daily context provider rows and writes intraday report/diagnostics/manifest. |
| `scripts/run_independence_shadow_live.py` | scheduled/manual workflow | loads config, builds real providers, calls daily and intraday runners, calls evaluation export | `active_runtime` | strong | Active Shadow-Live operational orchestrator; enforces allowed write prefixes. |
| `scripts/run_independence_smoke_test.py` | manual workflow | calls daily and intraday runners and active module smoke checks | `active_analysis_script` | strong | Runtime-validation script, not the production scanner itself. |
| `scanner/tools/run_historical_daily_replay.py` | historical replay workflow | loads scenario, verifies registry hash, calls replay runner | `active_evaluation` | strong | Active replay CLI. |
| `scanner/tools/export_evaluation_dataset.py` | direct CLI/tests; legacy-looking evaluation export | `scanner.pipeline.global_ranking.compute_global_top20`, `scanner.backtest.e2_model.evaluate_e2_candidate` | `active_evaluation` | medium | Executable tool but depends on pipeline/global-ranking and backtest model; classify as evaluation with legacy dependency conflict. |
| `scanner/tools/backfill_btc_regime.py` | direct CLI/tests | `scanner.pipeline.regime`, `scanner.pipeline.snapshot` | `active_analysis_script` | medium | Utility/backfill tool; not daily/intraday runtime. |
| `scanner/tools/backfill_snapshots.py` | direct CLI/tests | `--mode full` -> `_run_full_mode` -> `scanner.pipeline.run_pipeline` -> legacy pipeline/scoring path | `active_analysis_script` | strong | Historical backfill utility that can execute legacy pipeline scoring; not active Daily/Intraday runtime. |

Directories explicitly checked:

- `.github/workflows/**`: exists and contains runtime, replay, backtest, analysis, persistence, validation, AI-sparring, and auto-doc workflows.
- `scanner/main.py`: exists and is the scanner CLI dispatch.
- `scanner/runners/**`: exists and contains current daily/intraday runners.
- `scanner/tools/**`: exists and contains evaluation/backfill/calibration/validation tools.
- `scripts/**`: exists and contains operational orchestrators, analysis scripts, backtest scripts, history-fetch helpers, and runner guard.
- `scanner/evaluation/**`: exists and contains current replay, dataset export, historical replay, and history fetch infrastructure.
- `scanner/backtest/**`: exists and contains E2 labeling/model helper used by export tests/tools.
- `scanner/output/**`: exists and contains active report/diagnostics/schema writing.
- `scanner/storage/**`: exists and contains active SQLite and snapshot path utilities.
- `scanner/data/**`: exists and contains active bar clock, OHLCV fetch, and cache policy helpers.

## 4. GitHub Actions / workflow entry points

| Workflow file | Trigger | Commands / called modules/scripts | Artifact inputs | Artifact outputs | Classification | Evidence strength | Notes |
|---|---|---|---|---|---|---|---|
| `.github/workflows/independence-shadow-live.yml` | `workflow_dispatch`, scheduled cron `30 1 * * *` | `scripts/shadow_live_state.py restore/checkpoint-stage`, bar-clock inline Python, `scripts/run_independence_shadow_live.py`, `scripts/persist_shadow_live_reports.py` | restored SQLite state artifact, credentials, config path | `reports/index/`, `reports/daily/`, `reports/runs/`, `snapshots/runs/**/run.manifest.json`, `evaluation/exports/**`, SQLite state artifact | `active_runtime` | strong | Active Shadow-Live scheduled workflow. |
| `.github/workflows/independence-smoke-test.yml` | `workflow_dispatch` | bar-clock inline Python, `scripts/run_independence_smoke_test.py` | live/public MEXC connectivity; temp workdir | `artifacts/smoke-test-report.json`, `snapshots/runs/**`, `reports/runs/**` | `active_analysis_script` | strong | Operational validation path; asserts no report-side manifests and no `reports/analysis` writes. |
| `.github/workflows/run-historical-replay.yml` | `workflow_dispatch` | `scanner/tools/run_historical_daily_replay.py --validate-only`, `scripts/generate_replay_chunk_plan.py`, `scripts/run_replay_chunks.py` | Pre-1 history release asset, scenario YAML, optional resume state | packaged replay outputs, chunk outputs, state DB | `active_evaluation` | strong | Active historical replay workflow. |
| `.github/workflows/run-backtest-3a-exit-path-metrics.yml` | `workflow_dispatch` | `scripts/backtest/generate_exit_path_metrics_4h.py` | enriched replay events parquet, frozen OHLCV history | backtest 3A artifacts | `active_evaluation` | strong | Current executable analysis/backtest workflow. |
| `.github/workflows/run-backtest-3b-exit-model-simulation.yml` | `workflow_dispatch` | regenerates 3A via `generate_exit_path_metrics_4h.py`, then runs `simulate_exit_model_variants_4h.py` | enriched replay events, frozen OHLCV history, 3A outputs | backtest 3B artifacts plus regenerated 3A artifacts | `active_evaluation` | strong | Current executable analysis/backtest workflow. |
| `.github/workflows/run-may-cold-start-diagnostic.yml` | `workflow_dispatch` | `PYTHONPATH=. python scripts/diagnostics/may_2025_cold_start_diagnostic.py` | scenario YAML and Pre-1 history asset | diagnostic report tarball | `active_analysis_script` | strong | Diagnostic workflow writes a legacy-doc default unless overridden by workflow input. |
| `.github/workflows/run-analysis-script.yml` | `workflow_dispatch` | `scripts/_runner_guard.py`, then selected script under `scripts/` | user-selected script | `evaluation/exports/**`, `reports/aux/**`, `artifacts/**` | `active_analysis_script` | strong | Generic manual analysis runner; guarded to `scripts/`. |
| `.github/workflows/run-artifact-download-script.yml` | `workflow_dispatch` | `scripts/_runner_guard.py`, then selected script under `scripts/` with args | user-selected artifacts/script args | `artifacts/**`, `reports/**`, `evaluation/**`, `data/**` per workflow upload glob | `active_analysis_script` | strong | Generic artifact-download/manual script runner. |
| `.github/workflows/pr-ci.yml` | `pull_request`, `workflow_dispatch` | `python -m pytest -q` | repository/tests | pytest result | `active_utility` | strong | Validation/test workflow. |
| `.github/workflows/generate-gpt-snapshot.yml` | `push` to main, `workflow_dispatch` | `scripts/update_codemap.py`, inline GPT snapshot generator | repo files | `docs/code_map.md`, `docs/GPT_SNAPSHOT.md` auto-commit | `active_utility` | strong | Generated navigation/context workflow; not architecture authority. |
| `.github/workflows/ai-sparring.yml` | `workflow_dispatch` | `python -m tools.ai_sparring.cli`, optional writeback | prompt/context inputs | `artifacts/ai-sparring/`, optional draft ticket PR | `active_utility` | medium | AI support workflow outside scanner runtime. |
| `.github/workflows/ai-sparring-issue.yml` | issue comment command | `python -m tools.ai_sparring.cli issue-event` | issue command payload | `artifacts/ai-sparring/` | `active_utility` | medium | AI support workflow outside scanner runtime. |

Workflow categories identified:

- Scheduled workflow: `independence-shadow-live.yml`.
- Manually triggered workflows: all listed workflows except `pr-ci` PR trigger and `generate-gpt-snapshot` push trigger also support manual dispatch where defined.
- Analysis-script workflows: `run-analysis-script.yml`, `run-artifact-download-script.yml`, `run-backtest-3a-exit-path-metrics.yml`, `run-backtest-3b-exit-model-simulation.yml`, `run-may-cold-start-diagnostic.yml`.
- Shadow-Live workflows: `independence-shadow-live.yml`; smoke validation via `independence-smoke-test.yml`.
- Persistence workflows: Shadow-Live restore/checkpoint and `persist_shadow_live_reports.py` job in `independence-shadow-live.yml`.
- Validation/test workflows: `pr-ci.yml`, `independence-smoke-test.yml`, replay validation step in `run-historical-replay.yml`.

## 5. CLI and script entry points

| Entry point | Primary role observed | Classification | Evidence strength | Artifact paths touched | Notes |
|---|---|---|---|---|---|
| `scanner/main.py` | Scanner mode dispatch | `active_runtime` | strong | indirect via runners | Primary CLI dispatch. |
| `scripts/run_independence_shadow_live.py` | Shadow-Live orchestration | `active_runtime` | strong | `reports/runs/`, `reports/daily/`, `reports/index/`, `snapshots/runs/`, `evaluation/exports/`, `artifacts/` | Calls daily/intraday runners and evaluation export. |
| `scripts/run_independence_smoke_test.py` | Smoke validation | `active_analysis_script` | strong | temp `reports/runs/`, `snapshots/runs/`, `artifacts/smoke-test-report.json` | Verifies active artifact model and no forbidden paths. |
| `scripts/persist_shadow_live_reports.py` | Persist selected Shadow-Live reports | `active_analysis_script` | strong | checked-in/persisted report paths under allowed prefixes | Active in Shadow-Live workflow second job. |
| `scripts/shadow_live_state.py` | SQLite state restore/checkpoint/stage | `active_utility` | strong | SQLite state artifact | Active in Shadow-Live workflow. |
| `scanner/tools/run_historical_daily_replay.py` | Historical replay CLI | `active_evaluation` | strong | replay output dirs/state store | Active replay workflow entry. |
| `scripts/generate_replay_chunk_plan.py` | Replay chunk plan generator | `active_evaluation` | strong | `chunk_plan.json` | Active replay workflow step. |
| `scripts/run_replay_chunks.py` | Replay chunk subprocess runner | `active_evaluation` | strong | per-chunk replay outputs | Active replay workflow step. |
| `scripts/backtest/generate_exit_path_metrics_4h.py` | Exit-path metrics backtest | `active_evaluation` | strong | `evaluation/backtest/reports/.../exit_path_metrics_4h` | Active backtest workflow. |
| `scripts/backtest/simulate_exit_model_variants_4h.py` | Exit-model simulation backtest | `active_evaluation` | strong | `evaluation/backtest/reports/.../exit_model_simulation_4h` | Active backtest workflow. |
| `scripts/diagnostics/may_2025_cold_start_diagnostic.py` | Cold-start diagnostic | `active_analysis_script` | strong | default `docs/legacy/reports/...`; workflow packages requested report | Active diagnostic workflow but default path is legacy-doc-like. |
| `scripts/fetch_ohlcv_history_for_evaluation.py`, `scripts/fetch_binance_history.py` | History fetch/export helpers | `active_analysis_script` | medium | `snapshots/history/ohlcv/`, manifests | Executable scripts used by evaluation data prep. |
| `scanner/tools/export_evaluation_dataset.py` | Evaluation dataset export | `active_evaluation` | medium | `evaluation/exports/` | Uses legacy pipeline global ranking and E2 backtest model. |
| `scanner/tools/backfill_btc_regime.py` | BTC regime snapshot backfill | `active_analysis_script` | medium | snapshots dir from config | Uses pipeline regime/snapshot helpers. |
| `scanner/tools/backfill_snapshots.py` | Snapshot backfill | `active_analysis_script` | strong | snapshots dir from config | `--mode full` can call legacy `scanner.pipeline.run_pipeline` and reach pipeline scoring. |
| `scanner/tools/prepare_shadow_calibration.py` | Shadow calibration prep | `active_analysis_script` | medium | user-selected JSON output | Tested and executable. |
| `scripts/analyze_*.py`, `scripts/counterfactual_*.py`, `scripts/diagnose_*.py`, `scripts/post_risk_unlock_audit.py`, `scripts/top20_formation_audit.py`, `scripts/pre_top20_inclusion_audit-*.py` | Manual analyses and counterfactuals | `active_analysis_script` | medium | usually `reports/aux/`, `artifacts/`, or user-selected output | Executable through generic analysis workflow when guarded path passes. |
| `scripts/update_codemap.py` | Generated navigation updater | `active_utility` | strong | `docs/code_map.md` | Active auto-doc workflow; not architecture authority. |

## 6. Daily runtime call path

Level 0:

- `scanner/main.py::main` parses `--mode`, calls `load_config`, resolves effective mode, and calls `run_daily_scan(cfg)` for `daily_discovery`, `standard`, `fast`, `offline`, and `backtest`.
- `scripts/run_independence_shadow_live.py` and `scripts/run_independence_smoke_test.py` also call `run_daily_scan` directly after configuring providers/workdir.

Level 1 (`scanner/runners/daily.py::run_daily_scan` direct calls/imports):

- Config and time: `ScannerConfig`, `scanner.data.daily_bar_id`.
- Universe/data providers: `cfg.daily_universe_provider` or default empty provider; `cfg.daily_ohlcv_provider` or default empty provider.
- Feature/axis/phase path: `build_feature_bundle`, `compute_tier1_axes`, `compute_tier2_axes`, `compute_phase_interpretation`.
- State path: `init_db`, `load_persisted_state_machine_context`, `_to_cycle_context`, `compute_invalidation_and_cycle`, `_derive_runtime_context`, `compute_state_machine`, `apply_state_persistence_patch`.
- Entry/decision path: `resolve_entry_pattern`, `assign_bucket`, `rank_coins`.
- Execution path: `select_execution_subset`, `evaluate_execution_subset`, `classify_execution_size`, `is_reduced_size_eligible`, `is_tradeable_candidate`.
- Output path: `_persist_run_manifest`, `make_report_builder`, `ReportBuilder.write_run_report`, `ReportBuilder.write_daily_report`, diagnostics serialization helpers, `validate_diagnostics_record`, `attach_entry_location`, `build_entry_location_report_segments`.
- Universe category path: `classify_symbol` and actionable-exclusion category constants.

Level 2 direct module families from Level 1:

- `scanner/axes/`: active Tier-1/Tier-2 axis computations and normalization.
- `scanner/features/`: active raw/shared/bundle feature structures.
- `scanner/phase/`: active market phase interpretation.
- `scanner/state/`: active invalidation, freshness, setup cycle, state-machine context and persistence patches.
- `scanner/decision/`: active bucket assignment, ranking, entry-location report segments, reasons/models.
- `scanner/entry/`: active entry pattern resolution.
- `scanner/execution/`: active execution subset selection/evaluation/policy. Note: `scanner/execution/grading.py` imports `scanner.pipeline.liquidity.compute_tradeability_metrics`, creating a pipeline dependency inside active execution infrastructure.
- `scanner/output/`: active diagnostics serialization/schema/report writing.
- `scanner/storage/`: active SQLite schema/repositories/snapshot path utilities.
- `scanner/universe/`: active symbol classification and eligibility/budget helpers where imported by runtime/tests.

Artifact writes from daily path:

- Empty universe special case writes minimal `reports/runs/YYYY/MM/DD/<run_id>/report.json` directly.
- Normal run writes `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` via `_persist_run_manifest`.
- Normal run writes `reports/runs/YYYY/MM/DD/<run_id>/report.json` and `symbol_diagnostics.jsonl.gz` through `ReportBuilder.write_run_report`.
- Normal run writes `reports/daily/YYYY/MM/DD/report.json` and updates `reports/index/latest*.json`, `latest_run.txt`, and `recent_runs.json` through `write_daily_report`/index update.
- SQLite metadata/state writes go to `data/independence_release.sqlite`.

Legacy-looking modules in Level 0-2:

- `scanner.pipeline.liquidity` is used by `scanner/execution/grading.py`; this is a direct active utility dependency into a legacy-labeled package and is therefore an authority conflict to review.

## 7. Intraday runtime call path

Level 0:

- `scanner/main.py::main` calls `run_intraday_scan(cfg)` only when effective mode is `intraday_promotion`.
- `scripts/run_independence_shadow_live.py` and `scripts/run_independence_smoke_test.py` also call `run_intraday_scan` directly.

Level 1 (`scanner/runners/intraday.py::run_intraday_scan` direct calls/imports):

- Bar-clock path: `daily_bar_id`, `get_last_closed_intraday_bar_id`, `has_new_intraday_bar`.
- Persistence path: `init_db`, `_create_run_metadata`, `_finish_run_metadata`, `_latest_completed_intraday_bar_id`, `build_run_manifest_path`.
- Data/context path: `cfg.intraday_context_provider` or default empty provider; `cfg.intraday_refresh_provider`; optional predecision/postdecision providers.
- Selection/evaluation path: `_select_monitoring_universe`, `_intraday_row_has_attachable_execution_context`, `select_execution_subset`, `evaluate_execution_subset`.
- Diagnostics path: `_diag`, `_intraday_diag_from_row`, `validate_diagnostics_record`.
- Output path: `_write_intraday_noop_report`, `_write_intraday_manifest`, `make_report_builder`, `ReportBuilder.write_run_report`.

Level 2 direct module families from Level 1:

- `scanner/data/bar_clock.py`: active daily and intraday bar IDs, closed-bar checks.
- `scanner/execution/`: active execution selection/evaluation and diagnostics. As in daily path, execution grading includes a direct dependency on `scanner.pipeline.liquidity`.
- `scanner/output/`: active report/diagnostics/schema writer.
- `scanner/storage/`: active SQLite/run manifest path utility.

Artifact writes from intraday path:

- `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` via `_write_intraday_manifest` and `build_run_manifest_path`.
- `reports/runs/YYYY/MM/DD/<run_id>/report.json` and `symbol_diagnostics.jsonl.gz` through `ReportBuilder.write_run_report`.
- `reports/index/latest.json`, `latest_intraday.json`, `latest_paths.json`, `latest_run.txt`, and `recent_runs.json` through report-builder index update.
- SQLite run metadata uses `data/independence_release.sqlite`.

Legacy-looking modules in Level 0-2:

- No direct `scanner/pipeline/*` import in `scanner/runners/intraday.py` itself.
- Indirect active dependency through `scanner/execution/grading.py` to `scanner.pipeline.liquidity` remains in the Level-2 execution family and should be reviewed.

## 8. Evaluation / replay call paths

### 8.1 Historical daily replay workflow path

Level 0:

- `.github/workflows/run-historical-replay.yml`.
- `scanner/tools/run_historical_daily_replay.py`.
- `scripts/generate_replay_chunk_plan.py`.
- `scripts/run_replay_chunks.py`.

Level 1:

- `scanner/tools/run_historical_daily_replay.py` calls `load_scenario`, `scenario_config_hash`, `ensure_scenario_hash`, and `run_replay`.
- `scripts/generate_replay_chunk_plan.py` loads scenario metadata and writes a chunk plan.
- `scripts/run_replay_chunks.py` runs chunk subprocesses and handles resume state file selection.

Level 2:

- `scanner/evaluation/historical_replay/replay_runner.py` imports `HistoricalBarLoader`, `HistoricalProductionAdapter`, `ReplayScenario`, `scenario_config_hash`, and `ReplayStateStore`.
- `scanner/evaluation/historical_replay/production_adapter.py` imports active Independence modules: axes, config, entry patterns, feature bundle, phase interpreter, state invalidation/machine/models.
- `scanner/evaluation/historical_replay/bar_loader.py` and `state_store.py` provide replay data/state infrastructure.

Classification:

- `scanner/evaluation/historical_replay/*`: `active_evaluation`, evidence `strong`.
- `scanner/tools/run_historical_daily_replay.py`: `active_evaluation`, evidence `strong`.
- `scripts/generate_replay_chunk_plan.py` and `scripts/run_replay_chunks.py`: `active_evaluation`, evidence `strong`.

### 8.2 Event timeline and dataset export path

Level 0:

- `scanner/evaluation/dataset_export.py::run_evaluation_export`.
- `scanner/tools/export_evaluation_dataset.py`.
- Shadow-Live orchestrator calls `run_evaluation_export`.

Level 1:

- `dataset_export.py` calls `reconstruct_event_timeline` from `scanner/evaluation/replay.py` and `build_signal_metrics` from `scanner/evaluation/forward_returns.py`.
- `export_evaluation_dataset.py` loads snapshots and calls `compute_global_top20` plus E2 label helpers.

Level 2:

- `scanner/evaluation/replay.py` reads `snapshots/runs` manifests and resolves diagnostics paths from report/manifests.
- `scanner/evaluation/forward_returns.py` reads daily OHLCV history and computes signal metrics.
- `scanner/tools/export_evaluation_dataset.py` directly depends on `scanner.pipeline.global_ranking` and `scanner.backtest.e2_model`.

Classification:

- `scanner/evaluation/dataset_export.py`, `forward_returns.py`, `replay.py`: `active_evaluation`, evidence `strong` for dataset export/replay outputs.
- `scanner/tools/export_evaluation_dataset.py`: `active_evaluation`, evidence `medium`, with `clarify_authority_conflict` due to pipeline/global-ranking dependency.
- `scanner/backtest/e2_model.py`: `active_evaluation`, evidence `medium`; used by export tool/tests but not daily/intraday runtime.

### 8.3 History fetch path

Level 0:

- `scripts/fetch_ohlcv_history_for_evaluation.py` and `scripts/fetch_binance_history.py`.
- `scanner/evaluation/history/__init__.py` exports `HistoryFetchConfig` and `run_history_fetch`.

Level 1:

- `scanner/evaluation/history/ohlcv_history_fetch.py::run_history_fetch` uses Binance client, history config, manifests, parquet store, and symbol intersection helpers.

Level 2:

- `parquet_store.py` writes/reads partitioned OHLCV parquet.
- `manifests.py` writes history, universe, completeness manifests.
- `symbol_intersection.py` resolves MEXC/Binance universe overlap.

Classification:

- `scanner/evaluation/history/*`: `active_evaluation`, evidence `medium` to `strong` depending on script usage; not daily/intraday runtime.

### 8.4 Backtest and analysis workflows

Level 0:

- `.github/workflows/run-backtest-3a-exit-path-metrics.yml`.
- `.github/workflows/run-backtest-3b-exit-model-simulation.yml`.
- `.github/workflows/run-may-cold-start-diagnostic.yml`.

Level 1:

- `scripts/backtest/generate_exit_path_metrics_4h.py` reads enriched replay events and OHLCV history, writes 3A metrics/report.
- `scripts/backtest/simulate_exit_model_variants_4h.py` reads 3A outputs and writes 3B simulation outputs.
- `scripts/diagnostics/may_2025_cold_start_diagnostic.py` uses historical replay loader/adapter/runner helpers and writes a report.

Level 2:

- These scripts depend primarily on pandas, replay events, historical OHLCV partitions, and `scanner/evaluation/historical_replay/*` in the diagnostic script.

Classification:

- Backtest/diagnostic scripts listed above: `active_evaluation` or `active_analysis_script` with strong workflow evidence.

## 9. Output and artifact write paths

Current runtime writers:

- `scanner/output/report_builder.py`:
  - Writes `reports/runs/YYYY/MM/DD/<run_id>/report.json`.
  - Writes `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz` via diagnostics writer.
  - Writes `reports/daily/YYYY/MM/DD/report.json`.
  - Writes `reports/index/latest_run.txt`, `latest_paths.json`, `latest.json`, `latest_intraday.json`, `latest_confirmed_candidates.json`, `latest_watchlist.json`, `recent_runs.json`, and `latest_daily.json`.
- `scanner/runners/daily.py`:
  - Writes `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`.
  - Empty-universe special case writes a minimal report under `reports/runs/...`.
  - Writes SQLite run metadata and state to `data/independence_release.sqlite`.
- `scanner/runners/intraday.py`:
  - Writes `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`.
  - Writes intraday run report/diagnostics via `ReportBuilder`.
  - Writes SQLite run metadata to `data/independence_release.sqlite`.
- `scanner/storage/snapshots.py`:
  - Builds `snapshots/history/ohlcv/timeframe=<tf>/symbol=<sym>/year=YYYY/month=MM` paths.
  - Builds `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` paths.
- `scanner/evaluation/history/*`:
  - Writes partitioned OHLCV and history manifests under history roots, commonly `snapshots/history/`.
- `scanner/evaluation/dataset_export.py` and Shadow-Live orchestrator:
  - Write `evaluation/exports/` evaluation outputs.
- Backtest scripts:
  - Write `evaluation/backtest/reports/...` output trees.
- Analysis scripts/workflows:
  - Allowed auxiliary outputs include `artifacts/`, `reports/aux/`, and `evaluation/exports/`.

Potentially stale/deprecated-looking checked-in artifacts:

- Root-level `reports/YYYY-MM-DD.json` and `reports/YYYY-MM-DD.md` files exist as historical artifacts.
- Root-level `reports/YYYY-MM-DD_YYYY-MM-DD_<id>.manifest.json` files exist and resemble report-side manifests that current smoke workflow rejects under `reports/runs` and current canonical snapshots docs place under `snapshots/runs`.
- `reports/analysis/` is explicitly checked as forbidden/nonempty in smoke runtime assertions.

## 10. Module classification table

| Module / file | Primary role observed | Classification | Evidence strength | Evidence | Runtime path? | Evaluation path? | Script/tool path? | Test-only? | Artifact paths touched | Authority conflict? | Audit follow-up hint | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `scanner/main.py` | Scanner CLI dispatch | `active_runtime` | strong | Direct entry dispatch to daily/intraday runners | yes | no | yes | no | indirect | no | none | Includes old mode labels but routes to current daily runner. |
| `scanner/runners/daily.py` | Daily Discovery runner | `active_runtime` | strong | Called by main, Shadow-Live, smoke; writes active artifacts | yes | no | no | no | `reports/runs`, `reports/daily`, `reports/index`, `snapshots/runs`, SQLite | no | none | Current daily path. |
| `scanner/runners/intraday.py` | Intraday Promotion runner | `active_runtime` | strong | Called by main, Shadow-Live, smoke | yes | no | no | no | `reports/runs`, `reports/index`, `snapshots/runs`, SQLite | no | none | Current intraday path. |
| `scanner/axes/` | Tier axis computations | `active_runtime` | strong | Daily runner and historical production adapter import/call axes | yes | yes | no | no | none | no | none | Active domain computation. |
| `scanner/features/` | Feature bundle/raw/shared feature helpers | `active_runtime` | strong | Daily runner and replay production adapter import/call feature bundle | yes | yes | no | no | none | no | none | Active domain computation. |
| `scanner/phase/` | Phase interpreter | `active_runtime` | strong | Daily runner and replay production adapter call phase interpretation | yes | yes | no | no | none | no | none | Active domain computation. |
| `scanner/state/` | Invalidation, setup cycle, state machine | `active_runtime` | strong | Daily runner and replay adapter call invalidation/state machine | yes | yes | no | no | SQLite via persistence patch | no | none | Active state domain. |
| `scanner/decision/` | Bucket/ranking/entry-location decision layer | `active_runtime` | strong | Daily runner imports bucket, ranking, entry-location helpers | yes | no | no | no | report payload fields | no | none | Active current decision path. |
| `scanner/entry/` | Entry pattern resolution | `active_runtime` | strong | Daily runner and replay adapter call entry pattern resolver | yes | yes | no | no | none | no | none | Active. |
| `scanner/execution/` | Execution subset/evaluation/policy/grading | `active_runtime` | strong | Daily/intraday runners call execution selection/evaluation | yes | no | no | no | diagnostics fields | yes | clarify_authority_conflict | `scanner/execution/grading.py` imports legacy-labeled `scanner.pipeline.liquidity`. |
| `scanner/output/` | Report/diagnostics/schema writers | `active_runtime` | strong | Daily/intraday runners call `make_report_builder` and validation | yes | yes (replay reads diagnostics schema outputs) | no | no | `reports/runs`, `reports/daily`, `reports/index` | no | none | Active artifact writer. |
| `scanner/storage/` | SQLite schema/repositories/snapshot path utilities | `active_runtime` | strong | Daily/intraday runners call `init_db`, state persistence, manifest path builder | yes | yes | no | no | SQLite, `snapshots/runs`, `snapshots/history` | no | none | Active utility/data persistence. |
| `scanner/data/` | Bar clock, OHLCV fetch, cache policy | `active_runtime` | strong | Runners/scripts use daily/intraday bar IDs and closed-bar fetch | yes | yes | yes | no | history fetch/cache paths | no | none | Active utility/data. |
| `scanner/universe/` | Symbol classification/eligibility/budget | `active_runtime` | medium | Daily runner calls `classify_symbol`; other helpers tested/imported | yes | no | no | no | none | no | none | Some modules are active by tests/config; runtime direct evidence strongest for classification. |
| `scanner/clients/` | MEXC/marketcap/mapping clients | `active_utility` | medium | Shadow-Live/smoke scripts use MEXC client; legacy pipeline uses marketcap/mapping clients | yes (script provider) | yes (history via Binance under evaluation/history) | yes | no | network/data inputs | no | none | Client activity varies by caller. |
| `scanner/config.py` | Config load/default/validation/accessors | `active_utility` | strong | Main/runners/scripts/evaluation import config helpers | yes | yes | yes | no | config path/env | no | none | Central utility. |
| `scanner/evaluation/dataset_export.py` | Evaluation export | `active_evaluation` | strong | Shadow-Live orchestrator imports/calls `run_evaluation_export` | no | yes | yes | no | `evaluation/exports` | no | none | Active evaluation output. |
| `scanner/evaluation/replay.py` | Reconstruct event timeline from manifests/diagnostics | `active_evaluation` | strong | Dataset export imports/calls reconstruct function | no | yes | yes | no | reads `snapshots/runs`, diagnostics paths | no | none | Active evaluation reader. |
| `scanner/evaluation/forward_returns.py` | Forward-return metrics | `active_evaluation` | strong | Dataset export imports/calls build metrics | no | yes | yes | no | reads OHLCV history | no | none | Active evaluation. |
| `scanner/evaluation/historical_replay/*` | Historical replay infrastructure | `active_evaluation` | strong | Replay CLI/workflow calls `run_replay`; diagnostic workflow imports helpers | no | yes | yes | no | replay output/state dirs | no | none | Active replay. |
| `scanner/evaluation/history/*` | OHLCV history fetch/store/manifests | `active_evaluation` | medium | Exported by package and used by history fetch scripts/tests | no | yes | yes | no | `snapshots/history/ohlcv`, manifests | no | none | Active data-prep/evaluation infrastructure. |
| `scanner/backtest/e2_model.py` | E2 label/model helper | `active_evaluation` | medium | `scanner/tools/export_evaluation_dataset.py` imports/calls; tests cover | no | yes | yes | no | none | possible | investigate | Not daily/intraday runtime; name may imply old backtest but used by export tooling. |
| `scanner/tools/run_historical_daily_replay.py` | Replay CLI | `active_evaluation` | strong | Active workflow step | no | yes | yes | no | replay outputs | no | none | Current replay CLI. |
| `scanner/tools/export_evaluation_dataset.py` | Snapshot-based export CLI | `active_evaluation` | medium | Tests and executable tool; uses pipeline global ranking | no | yes | yes | no | `evaluation/exports` | yes | clarify_authority_conflict | Legacy dependency should be reviewed. |
| `scanner/tools/backfill_btc_regime.py` | BTC regime snapshot backfill | `active_analysis_script` | medium | Executable tool/tests; imports pipeline regime/snapshot | no | no | yes | no | snapshots | yes | candidate_for_future_legacy_isolation_review | Tool-only, pipeline-dependent. |
| `scanner/tools/backfill_snapshots.py` | Snapshot backfill | `active_analysis_script` | strong | Executable tool/tests; `--mode full` calls `_run_full_mode`, imports `scanner.pipeline.run_pipeline`, and can execute legacy pipeline scoring | no | no | yes | no | snapshots | yes | candidate_for_future_legacy_isolation_review | Tool-only, pipeline-dependent; not active Daily/Intraday runtime architecture. |
| `scanner/tools/prepare_shadow_calibration.py` | Calibration prep report | `active_analysis_script` | medium | Tests and executable script | no | yes-ish calibration | yes | no | user-selected JSON | no | none | Analysis/calibration utility. |
| `scanner/tools/validate_features.py` | Feature JSON validator | `active_utility` | weak | Utility function; no workflow call found | no | no | possible | no | none | no | investigate | Executable utility status unclear. |
| `scanner/pipeline/__init__.py` | Pre-Independence pipeline orchestrator | `active_analysis_script` | strong | Self-labeled legacy; `scanner/tools/backfill_snapshots.py --mode full` calls `_run_full_mode`, imports `scanner.pipeline.run_pipeline`, and executes the legacy pipeline | no | no | yes | no | legacy reports/snapshots | yes | clarify_authority_conflict | Reachable through executable backfill tooling; not active Independence Daily/Intraday runtime architecture. |
| `scanner/pipeline/decision.py` | Legacy decision layer | `legacy_residue_test_only` | weak | Found in pipeline package/tests; no active runner/workflow call | no | no | no | yes | none | yes | candidate_for_future_test_semantics_review | Search anchor; `ENTER`/`WAIT` context belongs legacy pipeline decision semantics. |
| `scanner/pipeline/global_ranking.py` | Legacy/global ranking Top-20 | `active_evaluation` | medium | Used by export evaluation tool and many tests; legacy pipeline also imports | no | yes | yes | no | pre-top20/export payloads | yes | clarify_authority_conflict | Active as evaluation/tool dependency, not current daily ranking path. |
| `scanner/pipeline/scoring/*` | Legacy scoring implementations reachable from full snapshot backfill | `active_analysis_script` | strong | Concrete path: `scanner/tools/backfill_snapshots.py --mode full` -> `_run_full_mode` -> `scanner.pipeline.run_pipeline` -> `score_reversals`, `score_breakout_trend_1_5d`, `score_pullbacks` from `scanner.pipeline.scoring/*` | no | no | yes | no | legacy pipeline reports/snapshots | yes | clarify_authority_conflict | Legacy pipeline dependency requiring follow-up before isolation/removal; not active Independence Daily/Intraday runtime architecture. |
| `scanner/pipeline/output.py` | Legacy report generator | `legacy_residue_test_only` | weak | Tests import `ReportGenerator`; no active runtime path | no | no | no | yes | root `reports`, legacy manifest conventions | yes | candidate_for_future_artifact_path_review | Legacy output semantics can contaminate docs. |
| `scanner/pipeline/features.py` | Legacy feature engine | `legacy_residue_test_only` | weak | Tests import; no active daily runner import | no | no | no | yes | none | yes | candidate_for_future_test_semantics_review | Legacy feature semantics. |
| `scanner/pipeline/backtest_runner.py` | Snapshot backtest runner | `legacy_residue_test_only` | weak | Tests import; no active workflow/script found | no | no | no | yes | test/golden outputs | possible | candidate_for_future_test_semantics_review | Backtest test-only evidence in this audit. |
| `scanner/pipeline/liquidity.py` | Liquidity/tradeability helpers | `active_utility` | strong | Active `scanner/execution/grading.py` imports `compute_tradeability_metrics`; tests also cover pipeline liquidity | yes (via execution) | no | yes | no | diagnostics metrics | yes | clarify_authority_conflict | Key active legacy dependency. |
| `scanner/pipeline/manifest.py` | Legacy pipeline manifest/path helpers | `legacy_residue_test_only` | weak | Tests import; no active runner/workflow path found | no | no | no | yes | legacy manifest/path config | yes | candidate_for_future_artifact_path_review | `shadow_mode` here is legacy path context, not Shadow-Live runtime by itself. |
| `scanner/pipeline/pre_top20_snapshot.py` | Pre-top20 snapshot helper | `legacy_residue_test_only` | weak | Tests import; legacy pipeline imports; no active runner path | no | no | no | yes | `snapshots/runtime` | possible | candidate_for_future_artifact_path_review | May be historical/transition support. |
| `scanner/pipeline/runtime_market_meta.py` | Runtime market metadata exporter | `legacy_residue_test_only` | weak | Tests import; legacy pipeline imports | no | no | no | yes | market metadata artifacts | possible | candidate_for_future_test_semantics_review | Not in current daily runner. |
| `scanner/pipeline/snapshot.py` | Snapshot manager | `active_analysis_script` | medium | Backfill tools import/use | no | no | yes | no | snapshots | yes | candidate_for_future_legacy_isolation_review | Pipeline utility used by tools. |
| `scanner/pipeline/regime.py` | BTC regime helper | `active_analysis_script` | medium | Backfill BTC regime tool imports/use | no | no | yes | no | snapshots metadata | yes | candidate_for_future_legacy_isolation_review | BTC-regime context is tool/legacy, not active daily scorer. |
| `scanner/pipeline/cross_section.py` | Percent-rank helper | `ambiguous` | medium | Pipeline shortlist/tests use; active docs mention percent-rank semantics; no direct daily runner import | no | unclear | no | yes | none | possible | investigate | Could be retained utility, but active call path not found within Level 2. |
| `scanner/pipeline/filters.py`, `shortlist.py`, `ohlcv.py`, `excel_output.py`, `discovery.py` | Legacy pipeline support | `legacy_residue_test_only` | weak | Tests/legacy pipeline imports only in audit | no | no | no | yes | legacy output/snapshot paths | yes | candidate_for_future_test_semantics_review | No active runner/workflow direct usage found. |
| `scripts/backtest/*` | Backtest/evaluation analysis scripts | `active_evaluation` | strong | Active backtest workflows call 3A/3B scripts | no | yes | yes | no | `evaluation/backtest/reports` | no | none | Current analysis/evaluation paths. |
| `scripts/diagnostics/may_2025_cold_start_diagnostic.py` | Diagnostic analysis | `active_analysis_script` | strong | Active workflow calls script | no | yes | yes | no | default `docs/legacy/reports/...` | yes | candidate_for_future_artifact_path_review | Active workflow but default output path is legacy-doc-like. |
| `scripts/_runner_guard.py` | Guards user-selected scripts | `active_utility` | strong | Generic analysis workflows call it | no | no | yes | no | none | no | none | Active workflow utility. |
| `tools/ai_sparring/*` | AI sparring support | `active_utility` | medium | AI workflows call CLI | no | no | yes | no | `artifacts/ai-sparring` | no | none | Outside scanner runtime. |
| Root `reports/YYYY-MM-DD.*` checked-in files | Historical/stale artifacts | `ambiguous` | weak | Existing artifacts only; active code writes nested paths | no | no | no | no | root reports | yes | candidate_for_future_artifact_path_review | Do not use as current report model without review. |

## 11. Legacy-residue candidates

Explicit path/symbol search results and classifications:

| Candidate | Findings | Classification | Evidence strength | Audit follow-up hint | Notes |
|---|---|---|---|---|---|
| `scanner/pipeline/` | Package has a top docstring: legacy/non-authoritative for Independence flows; not imported by daily/intraday runners; imported by tools/tests, full-mode snapshot backfill, and indirectly active via execution liquidity dependency | `ambiguous` | medium | clarify_authority_conflict | Overall package is mixed: legacy-looking/test/tool/backfill, with one active runtime utility dependency; do not treat the package as active Daily/Intraday architecture. |
| `scanner/pipeline/decision.py` | Implements old `ENTER`/`WAIT`/`NO_TRADE`-style decision semantics; no active runner call found | `legacy_residue_test_only` | weak | candidate_for_future_test_semantics_review | Search strings are legacy only in this context, not globally. |
| `scanner/pipeline/global_ranking.py` | Contains `compute_global_top20`; used by export evaluation tool and tests; not active daily ranking path | `active_evaluation` | medium | clarify_authority_conflict | Evaluation/tool active, runtime inactive. |
| `scanner/pipeline/scoring/` | Contains `base_score`, multiplier-style scoring, BTC-regime scoring contexts; tests import extensively and full-mode snapshot backfill can execute it through the legacy pipeline | `active_analysis_script` | strong | clarify_authority_conflict | Reachable path: `scanner/tools/backfill_snapshots.py --mode full` -> `_run_full_mode` -> `scanner.pipeline.run_pipeline` -> `scanner.pipeline.scoring/*`; not active Daily/Intraday runtime architecture. |
| `scanner/pipeline/output.py` | Legacy `ReportGenerator`, root reports and manifest conventions; tests import | `legacy_residue_test_only` | weak | candidate_for_future_artifact_path_review | Potential docs contamination risk. |
| `scanner/pipeline/features.py` | Legacy `FeatureEngine`; tests import | `legacy_residue_test_only` | weak | candidate_for_future_test_semantics_review | Active daily uses `scanner/features/bundle.py`, not this file. |
| `scanner/backtest/` | `e2_model.py` used by evaluation export tool/tests; no daily/intraday runtime | `active_evaluation` | medium | investigate | Backtest naming may confuse agents, but it is not unused. |
| `scanner/tools/export_evaluation_dataset.py` | Current executable export tool but depends on pipeline global ranking and backtest model | `active_evaluation` | medium | clarify_authority_conflict | Legacy dependency inside active evaluation tooling. |
| `scanner/tools/backfill_btc_regime.py` | Tool uses pipeline regime/snapshot | `active_analysis_script` | medium | candidate_for_future_legacy_isolation_review | `btc_regime` is tool/backfill context here. |
| `scanner/tools/backfill_snapshots.py` | Tool can call legacy `scanner.pipeline.run_pipeline` via `--mode full` / `_run_full_mode` | `active_analysis_script` | strong | candidate_for_future_legacy_isolation_review | Not active runtime; script-only/backfill path that can reach pipeline scoring. |
| `global_score` | Found primarily in generated code map, legacy docs/tests/output contexts | `ambiguous` | weak | candidate_for_future_test_semantics_review | Not found as active daily runner primitive. |
| `GLOBAL_RANKING_TOP20` | Found in tests/legacy output/schema contexts | `legacy_residue_test_only` | weak | candidate_for_future_test_semantics_review | Old output/schema naming. |
| `base_score`, `multiplier` | Found in pipeline scoring/tests and reachable through full-mode snapshot backfill legacy pipeline execution | `active_analysis_script` | medium | clarify_authority_conflict | Legacy scoring semantics reachable through an executable analysis/backfill tool, not active Daily/Intraday runtime scoring. |
| `btc_regime` | Found in config, pipeline regime/scoring, backfill tools, replay/backtest analyses | `ambiguous` | medium | investigate | Context-dependent; active as evaluation/backfill label/input, not proof of current daily BTC multiplier scoring. |
| `fast`, `standard`, `offline`, `backtest` | Accepted by `scanner/main.py` and normalized in storage schema to daily scan mode | `active_runtime` | strong | investigate | Mode labels remain active CLI/config compatibility, but all route to daily runner. |
| `reports/analysis` | Smoke workflow/script explicitly rejects artifacts there | `confirmed_deprecated_by_authority` as artifact path | strong | candidate_for_future_artifact_path_review | Forbidden for active smoke/runtime assumption. |
| `reports/YYYY-MM-DD.md` | Root-level reports exist; active runtime writes nested reports | `potentially_stale` | weak | candidate_for_future_artifact_path_review | Historical artifacts; avoid as current model source. |
| `run.manifest.json under reports/` | Smoke checks reject manifests under `reports/runs`; canonical snapshots docs place manifests under `snapshots/runs` | `confirmed_deprecated_by_authority` for report-side manifest | strong | candidate_for_future_artifact_path_review | Existing root manifests are stale/historical. |
| `scanner.pipeline`, `pipeline.decision`, `pipeline.global_ranking`, `pipeline.scoring` | Tests and some tools import; active runners mostly do not | mixed | medium | clarify_authority_conflict | Must classify by caller, not path string. |
| `legacy` | Appears in authority/context docs and pipeline docstring | `ambiguous` | weak | investigate | A text marker, not runtime evidence. |
| `shadow_mode` | Active Shadow-Live context and legacy pipeline manifest config both use shadow wording | `ambiguous` | medium | investigate | Context-dependent; not a legacy signal alone. |
| `entry_ready`, `ENTER`, `WAIT`, `NO_TRADE` | Found in pipeline decision/scoring, scripts, diagnostics/counterfactual analyses | mixed | weak | candidate_for_future_test_semantics_review | Not legacy indicators by themselves; legacy only where tied to old pipeline decision/scoring. |

No file was classified `legacy_residue_unused` with high confidence in this pass because the audit did not exhaustively prove absence across all possible dynamic calls for every file. Where no active call was found but tests exist, files were classified `legacy_residue_test_only`; where evidence was incomplete/conflicting, files were classified `ambiguous`.

## 12. Test semantics inventory

Mandatory anchor search summary:

- `scanner.pipeline`, `pipeline.decision`, `pipeline.global_ranking`, `pipeline.scoring`, `compute_global_top20`, `base_score`, `multiplier`, `btc_regime`, and `GLOBAL_RANKING_TOP20` appear heavily in tests for pre-Independence/legacy pipeline behavior; additionally, `pipeline.scoring`, `base_score`, and multiplier-style scoring are reachable through `scanner/tools/backfill_snapshots.py --mode full` via legacy `scanner.pipeline.run_pipeline`.
- `fast`, `standard`, `offline`, and `backtest` appear in config/main/storage tests and are current compatibility/runtime dispatch semantics because `scanner/main.py` accepts them and storage schema normalizes old daily run-mode values.
- `reports/analysis`, report-side manifest checks, `reports/YYYY-MM-DD.*`, and `run.manifest.json` appear in output/schema/smoke tests; current tests generally guard the new nested artifact model and reject old report-side manifest locations.
- `shadow_mode` appears in active Shadow-Live tests and in legacy pipeline manifest tests; classify by module under test.
- `entry_ready`, `ENTER`, `WAIT`, and `NO_TRADE` appear in both old decision tests/counterfactual analyses and current diagnostics/report contexts. These strings are not legacy indicators by themselves.

| Test file / group | Important assertions / strings | Modules under test | Classification | Evidence strength | Audit follow-up hint | Notes |
|---|---|---|---|---|---|---|
| `tests/test_ticket15_daily_runner.py`, `tests/test_ticket17_intraday_runner.py`, `tests/test_main_dispatch_ticket17_fixes.py` | daily/intraday runner dispatch, reports, mode handling | `scanner/main.py`, `scanner/runners/*` | `current_semantics_test` | strong | none | Guards active runtime path. |
| `tests/test_ticket13_output_artifacts.py`, `tests/test_output_schema_version.py`, `tests/test_run_manifest_output.py`, `tests/test_pr20_markdown_trade_candidates_sot.py`, `tests/test_pr22_output_consistency_json_md_xlsx.py` | reports, diagnostics, manifests, schema versions | `scanner/output/*`, pipeline output in older tests | mixed: `schema_guard_test` and `legacy_semantics_test` | medium | candidate_for_future_artifact_path_review | Split needed: active `scanner/output` tests are current; `scanner.pipeline.output` tests are legacy/test-only. |
| `tests/test_ticket18_evaluation_replay.py`, `tests/replay/*`, `tests/test_run_historical_replay_workflow.py`, `tests/test_run_replay_chunks.py`, `tests/test_generate_replay_chunk_plan.py` | replay scenarios, chunking, state, production adapter | `scanner/evaluation/historical_replay/*`, replay scripts | `current_semantics_test` | strong | none | Guards active evaluation/replay. |
| `tests/test_t30_forward_return_evaluation_v1.py`, `tests/test_t30_v2.py`, `tests/test_export_evaluation_dataset.py`, `tests/test_shadow_calibration_prepare.py` | forward returns, evaluation exports, calibration prep | `scanner/evaluation/*`, `scanner/tools/export_evaluation_dataset.py`, calibration tool | `current_semantics_test` | medium | clarify_authority_conflict | Export tool uses legacy global ranking/backtest helpers. |
| `tests/test_independence_shadow_live.py`, `tests/test_independence_smoke_test.py`, `tests/test_shadow_live_workflow.py`, `tests/test_manifest_shadow_switching.py`, `tests/test_shadow_live_report_persistence.py` | Shadow-Live orchestration, allowed paths, state persistence | scripts and active runners | `current_semantics_test` | strong | none | `shadow_mode` here is active operational context or compatibility config, not legacy by itself. |
| `tests/test_config_independence_release.py`, `tests/test_config_v421.py`, `tests/test_phase0_config_wiring.py`, `tests/test_risk_config_key_alias.py`, `tests/test_unlock_overrides_parsing.py` | config defaults/validation/aliases | `scanner/config.py` and config consumers | `schema_guard_test` / `compatibility_test` | strong | none | Current config semantics and backward-compatible aliases. |
| `tests/test_ticket6_axes.py`, `tests/test_ticket7_tier2_axes.py`, `tests/test_ticket8_phase_interpreter.py`, `tests/test_ticket9_invalidation_cycle.py`, `tests/test_ticket10_state_machine.py`, `tests/test_ticket11_entry_patterns.py`, `tests/test_ticket12_decision_buckets.py` | current axis/phase/state/entry/decision behavior | active Independence modules | `current_semantics_test` | strong | none | Current domain semantics. |
| `tests/test_ticket16_execution_adapter.py`, `tests/test_ticket26_execution_depth_analysis.py`, `tests/test_ticket28_reduced_size_policy_calibration.py`, `tests/test_ticket29_reduced_size_execution_policy.py`, `tests/test_t23_slippage_metrics.py` | execution selection/grading/slippage/policy | `scanner/execution/*`, some `scanner.pipeline.liquidity` | `current_semantics_test` / `utility_test` | medium | clarify_authority_conflict | Active execution grading uses pipeline liquidity helper. |
| `tests/test_pr1_breakout_feature_engine.py`, `tests/test_phase1_volume_periods.py`, `tests/test_phase2_reversal_logic.py`, `tests/test_pr3_breakout_trend_scoring.py`, `tests/test_pr14_scorer_v2_contracts.py`, `tests/test_t11_global_ranking.py`, `tests/test_pre_top20_snapshot.py`, `tests/test_ticket1_weight_loading.py`, `tests/test_t51_trade_levels_output.py`, `tests/test_t41_soft_penalty_scoring.py`, `tests/test_v421_risk_calculation.py`, `tests/test_breakout_closed_candle_gate.py`, `tests/test_pullback_closed_candle_gate.py`, `tests/test_reversal_closed_candle_gate.py`, `tests/test_t32_min_history_gate.py` | old scoring/ranking/top20, `base_score`, multipliers, trade levels, closed-candle gates | `scanner/pipeline/features.py`, `scanner/pipeline/scoring/*`, `scanner/pipeline/global_ranking.py` | `legacy_semantics_test` | medium | clarify_authority_conflict | These guard legacy pipeline semantics; scoring is also reachable through full-mode backfill, but that does not make it active Daily/Intraday runtime architecture. |
| `tests/test_pr2_btc_regime.py`, `tests/test_ticket02_snapshot_btc_regime_pipeline.py`, `tests/test_backfill_btc_regime.py` | BTC regime snapshot/pipeline/backfill behavior | `scanner/pipeline/regime.py`, pipeline runner, backfill tool | `legacy_semantics_test` / `compatibility_test` | medium | candidate_for_future_legacy_isolation_review | `btc_regime` is context-dependent; tool/backfill active, old scoring pipeline not current runtime. |
| `tests/test_backfill_snapshots.py`, `tests/test_backfill_btc_regime.py` | CLI/backfill preflight and snapshot mutation | scanner tools + pipeline snapshot/run_pipeline | `compatibility_test` | medium | candidate_for_future_legacy_isolation_review | Guards executable tools that depend on legacy pipeline. |
| `tests/test_t71_backtest_runner.py`, `tests/test_t84_backtest_golden.py`, `tests/test_pr13_backtest_count_trades_from_executions_only.py`, `tests/test_pr4_breakout_backtest_4h.py`, `tests/test_backtest_calendar_days.py` | snapshot backtest runner/golden outputs | `scanner/pipeline/backtest_runner.py` | `legacy_semantics_test` | weak | candidate_for_future_test_semantics_review | No active workflow call to this runner found. |
| `tests/test_sqlite_foundation.py`, `tests/test_storage_ticket3.py`, `tests/test_ticket14_snapshot_storage_contract.py`, `tests/test_raw_marketcap_parquet_sanitization.py`, `tests/test_t30_pre2_ohlcv_history_fetch.py`, `tests/test_pre1_history_fetch.py` | SQLite/snapshot/history storage | `scanner/storage/*`, `scanner/evaluation/history/*` | `schema_guard_test` / `utility_test` | strong | none | Current persistence/data-prep contracts. |
| `tests/test_bar_clock_foundation.py`, `tests/test_indicator_reference_examples.py`, `tests/test_percent_rank_average_ties.py`, `tests/pipeline/test_percent_rank_average_ties.py` | time/indicator/math helpers | active data and pipeline utility helpers | `utility_test` | medium | investigate | Some helpers are shared/neutral; pipeline location can confuse. |
| `tests/scripts/*` | script guards and diagnostics | scripts under `scripts/` | `utility_test` / `current_semantics_test` | medium | none | Covers executable script behavior. |
| `tests/test_gpt_snapshot_canonical_include_list.py`, `tests/test_ticket_p0_docs_authority_readme.py`, `tests/test_no_merge_conflict_markers.py`, `tests/test_baseline_convention.py` | docs/context/repo hygiene | docs/workflow conventions | `utility_test` | medium | none | Not scanner runtime semantics. |
| `tests/pipeline/*` | pipeline tradeability/liquidity/budget behavior | `scanner/pipeline/*` | mixed: `legacy_semantics_test` and `utility_test` | weak/medium | candidate_for_future_test_semantics_review | Pipeline namespace should be reviewed before DOC-D uses it as current architecture. |

## 13. Artifact path classification

| Path pattern | Where found | Read or write | Classification | Evidence strength | Authority/code reference | Notes |
|---|---|---|---|---|---|---|
| `reports/runs/YYYY/MM/DD/<run_id>/report.json` | `scanner/output/report_builder.py`, daily/intraday runners, workflows/tests | write/read/upload | `expected_current` | strong | Active report builder and workflow assertions | Current per-run report path. |
| `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz` | `scanner/output/report_builder.py`, scripts/tests | write/read/upload | `expected_current` | strong | Active diagnostics writer and orchestrators | Current diagnostics path. |
| `reports/daily/YYYY/MM/DD/report.json` | `ReportBuilder.write_daily_report`, Shadow-Live workflow | write/upload/persist | `expected_current` | strong | Active daily report writer/workflow | Current daily pointer report. |
| `reports/index/latest*.json`, `reports/index/recent_runs.json`, `reports/index/latest_run.txt` | `ReportBuilder._update_index_after_run`, workflows/tests | write/read/upload | `expected_current` | strong | Active report builder | Current index model. |
| `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` | daily/intraday runners, storage snapshots, smoke/shadow workflows, canonical snapshots docs | write/read/upload | `expected_current` | strong | Active runner/storage path and workflow assertions | Canonical run manifest placement. |
| `snapshots/history/ohlcv/timeframe=<tf>/symbol=<sym>/year=YYYY/month=MM/` | `scanner/storage/snapshots.py`, evaluation history fetch, replay workflow normalization | read/write | `expected_current` | strong | Active storage/evaluation code and workflow | Current history dataset path. |
| `snapshots/history/manifests/*.json`, `snapshots/history/regime_labels/*.json` | replay workflow and evaluation history code | read/write | `expected_current` | medium | Replay workflow verifies manifests/labels | Evaluation data-prep current. |
| `evaluation/exports/` | Shadow-Live workflow, analysis workflow, dataset export | write/upload | `allowed_analysis_or_auxiliary` | strong | Active workflow/script allowed prefix | Active evaluation export output. |
| `evaluation/replay/` | Shadow-Live allowed prefix and replay outputs | write/read | `allowed_analysis_or_auxiliary` | medium | Script allowed prefixes | Auxiliary/evaluation output. |
| `evaluation/backtest/reports/...` | backtest 3A/3B scripts/workflows | write/upload | `allowed_analysis_or_auxiliary` | strong | Active backtest workflows/scripts | Current analysis/backtest outputs. |
| `artifacts/` | Smoke/Shadow-Live/AI sparring/analysis workflows | write/upload | `allowed_analysis_or_auxiliary` | strong | Active workflows and orchestrators | Auxiliary artifacts. |
| `reports/aux/` | generic analysis workflow and analysis script defaults | write/upload | `allowed_analysis_or_auxiliary` | medium | `run-analysis-script.yml`, scripts defaults | Analysis-only, not runtime current report model. |
| `reports/analysis/` | Smoke workflow/script checks forbid nonempty path | write forbidden/check | `confirmed_deprecated_by_authority` | strong | Smoke workflow and smoke script assertions | Do not use for active runtime artifacts. |
| `reports/runs/**/run.manifest.json` or `*.manifest.json` under `reports/runs` | Smoke workflow/script rejects | write forbidden/check | `confirmed_deprecated_by_authority` | strong | Smoke workflow and smoke script assertions | Manifests belong under `snapshots/runs`. |
| Root `reports/YYYY-MM-DD.md` | checked-in historical files and legacy output conventions | existing/write by legacy only | `potentially_stale` | weak | Existing artifacts; active code writes nested reports | Do not use as current report model without review. |
| Root `reports/YYYY-MM-DD.json` | checked-in historical files and legacy output conventions | existing/write by legacy only | `potentially_stale` | weak | Existing artifacts; active code writes nested reports | Potential current-doc contamination. |
| Root `reports/YYYY-MM-DD_YYYY-MM-DD_<id>.manifest.json` | checked-in historical files | existing | `potentially_stale` | weak | Existing artifacts; current active code does not write this pattern | Resembles old report-side manifest model. |
| `docs/legacy/reports/...` | default in May cold-start diagnostic script | write if not overridden | `ambiguous` | medium | Active diagnostic script default | Active workflow may override; default path is legacy-doc-like and should be reviewed. |
| `snapshots/runtime/` | `scanner/pipeline/pre_top20_snapshot.py` default | write by legacy helper/tests | `potentially_stale` | weak | Pipeline helper only | Not current runner manifest path. |
| `data/independence_release.sqlite` | daily/intraday runners, Shadow-Live state scripts | read/write/upload checkpoint | `expected_current` | strong | Active runners/workflow | Current local state DB. |

## 14. Ambiguous / unresolved cases

| Case | Why ambiguous/unresolved | Evidence strength | Follow-up hint |
|---|---|---|---|
| Overall status of `scanner/pipeline/` | Package is self-labeled legacy and not active daily/intraday, but submodules are used by active tools/tests and `pipeline.liquidity` is imported by active execution grading | medium | clarify_authority_conflict |
| `scanner/execution/grading.py` dependency on `scanner.pipeline.liquidity` | Active execution utility reaches into legacy-labeled namespace | strong | clarify_authority_conflict |
| `scanner/pipeline/global_ranking.py` | Not active daily ranker, but active evaluation export tool imports `compute_global_top20` | medium | clarify_authority_conflict |
| `scanner/tools/export_evaluation_dataset.py` | Active evaluation tool with legacy pipeline/global ranking and backtest dependencies | medium | clarify_authority_conflict |
| `btc_regime` semantics | Appears in config, legacy scoring, backfill, replay/backtest labels; not one single meaning | medium | investigate |
| `fast`, `standard`, `offline`, `backtest` modes | Accepted by main/storage but route to daily runner; whether names should remain documented as modes is a future decision | strong | investigate |
| Root-level checked-in `reports/*` historical artifacts | Existing files can mislead agents; not current writer paths | weak | candidate_for_future_artifact_path_review |
| `docs/legacy/reports/...` default from May cold-start diagnostic | Active diagnostic script default writes under legacy docs unless workflow/user overrides | medium | candidate_for_future_artifact_path_review |
| Tests and full-mode backfill coverage for pipeline scoring/ranking | Tests may be intentionally retained compatibility/golden coverage, and `scanner/pipeline/scoring/*` is reachable through `backfill_snapshots.py --mode full`; audit cannot decide rewrite/removal/isolation | medium | clarify_authority_conflict |
| `scanner/tools/validate_features.py` | Utility exists but no active workflow/runtime caller found in this pass | weak | investigate |

## 15. Risk summary

### 1. Active legacy path risk

- `risk_level: high`
- Evidence: `scanner/execution/grading.py` imports `scanner.pipeline.liquidity.compute_tradeability_metrics`, so active daily/intraday execution evaluation may depend on a helper in a legacy-labeled package.
- Why it matters: Future agents could either avoid needed code because it is under `scanner/pipeline/`, or incorrectly treat the entire pipeline package as active current architecture.
- Recommended audit follow-up hint: `clarify_authority_conflict`.

### 2. Test-only legacy risk

- `risk_level: medium`
- Evidence: Many tests import `scanner.pipeline.features`, `scanner.pipeline.global_ranking`, `scanner.pipeline.output`, and `scanner.pipeline.backtest_runner`; `scanner.pipeline.scoring.*` is not merely test-only because `scanner/tools/backfill_snapshots.py --mode full` can execute it through `_run_full_mode` and `scanner.pipeline.run_pipeline`. Active daily/intraday runners still do not import these old scoring/output modules.
- Why it matters: Tests and executable backfill tooling can keep old business semantics reachable and confuse future changes unless test/tool intent is explicitly labeled current, compatibility, analysis-only, or legacy.
- Recommended audit follow-up hint: `clarify_authority_conflict`.

### 3. AI/Codex confusion risk

- `risk_level: high`
- Evidence: `docs/code_map.md` lists all modules including `scanner/pipeline/`; root reports and legacy-looking manifests exist; `scanner/pipeline/__init__.py` is legacy-labeled while some submodules have active tool/utility dependencies.
- Why it matters: AI agents may edit inactive pipeline scoring/output code when asked to change active scanner behavior, or ignore active helper dependencies because of a legacy path prefix.
- Recommended audit follow-up hint: `clarify_authority_conflict`.

### 4. Documentation contamination risk

- `risk_level: high`
- Evidence: Legacy pipeline modules contain scoring/ranking/output/report semantics (`global_score`, `GLOBAL_RANKING_TOP20`, `base_score`, multiplier, report-side manifest behavior) that differ from current runner/report-builder paths; `scanner/pipeline/scoring/*` is reachable through the executable full-mode snapshot backfill path.
- Why it matters: DOC-D current-state docs could accidentally document old scanner scoring/output semantics as current Daily/Intraday behavior, even though that scoring is an analysis/backfill legacy-pipeline dependency rather than active Independence runtime architecture.
- Recommended audit follow-up hint: `candidate_for_future_legacy_isolation_review`.

### 5. Artifact-path drift risk

- `risk_level: medium`
- Evidence: Active runtime writes nested `reports/runs`, `reports/daily`, `reports/index`, and `snapshots/runs` paths, while checked-in root-level `reports/YYYY-MM-DD.*` and root `*.manifest.json` files remain; smoke workflow rejects `reports/analysis` and report-side manifests.
- Why it matters: Consumers and agents may use stale artifacts as examples and write new outputs to deprecated or ambiguous locations.
- Recommended audit follow-up hint: `candidate_for_future_artifact_path_review`.

## 16. No action taken confirmation

- [x] No scanner code changed.
- [x] No tests changed.
- [x] No schemas changed.
- [x] No workflows changed.
- [x] No runtime behavior changed.
- [x] No files moved.
- [x] No files deleted.
- [x] No deprecation markers added.
- [x] No current-state canonical domain documentation updated.
- [x] Only the audit artifact was added.
