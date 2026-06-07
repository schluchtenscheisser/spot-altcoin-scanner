# Legacy Pipeline Boundary Review & Decision Matrix v0

## 1. Executive summary

CODE-A2 reviews the boundary conflicts identified by CODE-A1 around `scanner/pipeline/`. The review confirms that `scanner/pipeline/` cannot safely be classified as fully active or fully dead:

- `scanner/pipeline/__init__.py` self-labels the package orchestrator as legacy and points Independence-Release flows to `scanner/runners/daily.py`.
- Current execution grading imports `scanner.pipeline.liquidity.compute_tradeability_metrics`, and the active execution adapter calls that grading path.
- Current evaluation export tooling imports `scanner.pipeline.global_ranking.compute_global_top20` and `scanner.backtest.e2_model` helpers.
- `scanner.tools.backfill_snapshots --mode full` can execute `scanner.pipeline.run_pipeline`, which reaches legacy scoring modules under `scanner/pipeline/scoring/`.
- Active scanner dispatch accepts old mode names (`standard`, `fast`, `offline`, `backtest`) and routes them to the Daily runner, while `intraday_promotion` routes to the Intraday runner.

Primary conclusion: DOC-D may proceed only partially until Martin decides the boundary labels for these paths. DOC-D can document active Daily/Intraday runtime entry points and runner behavior, but it must not present legacy pipeline scoring/ranking/output semantics as current Independence runtime behavior. Execution/tradeability, evaluation/replay, analysis/backfill, and mode alias sections need explicit boundary wording or follow-up cleanup tickets.

## 2. Authority and evidence rules used

This review used the current repository authority hierarchy:

1. Current repository reality is the primary anchor for implemented behavior.
2. Validated current-state canonical documentation is secondary.
3. Build-spec and design-intent sources are useful only where not contradicted by current repository reality.
4. AI context helpers and generated maps are navigation/context aids only.
5. Previous-scanner and legacy references are historical unless explicitly revalidated.

Evidence rules applied:

- File existence alone does not establish active status.
- A legacy-labeled namespace does not prove every contained helper is inactive.
- Active status requires entry-point, import, call, workflow, script, test, or artifact evidence.
- Conflicts between code, tests, workflows, artifacts, canonical authority, AI helpers, generated navigation, and build intent are surfaced rather than silently resolved.
- Recommendations are non-binding and require Martin approval where product or architecture intent is ambiguous.

Authority files inspected:

- `docs/canonical/AUTHORITY.md`
- `docs/canonical/INDEX.md`
- `docs/AI_CONTEXT_CURRENT.md`
- `docs/GPT_SNAPSHOT.md`
- `docs/audit/active_code_path_inventory_v0.md`

Key authority observations:

- `docs/canonical/AUTHORITY.md` makes current repository reality the top evidence layer and warns that AI helpers and generated navigation do not override current reality.
- `docs/AI_CONTEXT_CURRENT.md` explicitly says the old scanner pipeline may still exist and should be treated as legacy/reference-only unless current active code paths prove otherwise.
- CODE-A1 identifies the same four boundary risks reviewed here and flags `scanner/pipeline/` as mixed rather than uniformly dead or active.

## 3. CODE-A1 findings used as input

CODE-A1 supplied the following inputs for this review:

| CODE-A1 finding | How CODE-A2 used it |
| --- | --- |
| `scanner/execution/grading.py` imports `scanner.pipeline.liquidity.compute_tradeability_metrics`. | Reviewed as conflict area A, with additional call-path evidence through `scanner/execution/adapter.py` and Daily runner execution evaluation. |
| `scanner/tools/export_evaluation_dataset.py` imports `scanner.pipeline.global_ranking.compute_global_top20` and `scanner.backtest.e2_model`. | Reviewed as conflict area B, including tests that exercise export ordering and labels. |
| `scanner/tools/backfill_snapshots.py --mode full` reaches `scanner.pipeline.run_pipeline` and legacy scoring. | Reviewed as conflict area C, including CLI and strict/full-mode tests. |
| Old modes `standard`, `fast`, `offline`, and `backtest` remain accepted and map to Daily behavior. | Reviewed as conflict area D, including `scanner/main.py`, `scanner/config.py`, and storage scan-mode normalization. |
| Pipeline namespace is self-labeled legacy but contains actively imported helpers. | Used as the cross-conflict boundary problem and the reason for a proposed boundary model. |

CODE-A2 intentionally did not repeat a broad repository inventory. It inspected only the source, tests, and workflow evidence needed to classify the four mandatory conflict areas.

## 4. Conflict area A — execution grading uses pipeline liquidity

### Evidence summary

| Required evidence item | Evidence |
| --- | --- |
| Source files inspected | `scanner/execution/grading.py`; `scanner/pipeline/liquidity.py`; `scanner/execution/adapter.py`; `scanner/runners/daily.py`; `docs/audit/active_code_path_inventory_v0.md`; authority/context files. |
| Functions/classes inspected | `ExecutionGradeResult`; `_LegacyExecutionCfg`; `grade_execution_orderbook`; `compute_tradeability_metrics`; `evaluate_execution_subset`; Daily runner call sites for execution evaluation. |
| Tests inspected, if relevant | `tests/test_t23_slippage_metrics.py` for liquidity/global ranking utility tests; execution-related tests were located through imports but not exhaustively inventoried. |
| Workflows inspected, if relevant | `independence-shadow-live.yml` as active Daily operational context. |
| Call path evidence | `scanner/execution/adapter.py` imports `grade_execution_orderbook`, then calls it after orderbook freshness handling. `scanner/execution/grading.py` imports and calls `compute_tradeability_metrics`. |
| Artifact path evidence, if relevant | Daily diagnostics/report payloads include execution/tradeability-derived fields built by `scanner/runners/daily.py`. |
| Authority conflict, if any | `scanner/pipeline/__init__.py` labels the pipeline orchestrator as legacy, while `scanner/pipeline/liquidity.py` is imported by active execution code. |

### Analysis

This is the strongest active dependency among the four conflict areas. The dependency is not merely test-only: active execution evaluation routes through `scanner/execution/adapter.py` into `scanner/execution/grading.py`, and grading calls `scanner.pipeline.liquidity.compute_tradeability_metrics`.

`scanner.pipeline.liquidity` is therefore best understood as useful active utility code that is misplaced under a legacy-labeled package, unless Martin chooses to canonicalize it in place. The package-level legacy label applies clearly to the old orchestrator in `scanner/pipeline/__init__.py`; it should not automatically classify `compute_tradeability_metrics` as dead.

DOC-D can document execution grading and tradeability only if it explicitly describes the current import as a boundary exception. It should not imply that the whole legacy pipeline is current runtime architecture.

### Decision matrix — conflict area A

| Option | What it would mean | Evidence supporting it | Evidence against it / risk | Impact on DOC-D | Follow-up ticket required? | Recommended? yes/no/conditional |
| --- | --- | --- | --- | --- | --- | --- |
| `canonicalize_current_dependency` | Keep `scanner.pipeline.liquidity` as an active current dependency and document it as such. | Active execution adapter calls grading; grading imports and calls `compute_tradeability_metrics`. | Canonicalizing a helper inside `scanner/pipeline/` risks teaching agents that more of the legacy package is active than intended. | DOC-D could document it directly, but must define the namespace exception. | Yes: documentation/boundary ticket to mark `pipeline.liquidity` active. | Conditional. |
| `isolate_legacy_dependency` | Keep the reachable dependency for now but label/isolate it so legacy namespace is not treated as current architecture. | Package orchestrator is legacy-labeled; helper remains reachable. | Isolation without extraction may leave future confusion in imports. | DOC-D can proceed with explicit “legacy namespace exception” wording. | Yes: isolation/boundary-marker ticket. | Conditional. |
| `extract_active_utility` | Move tradeability utility code to active module family such as `scanner/execution/` or `scanner/utils/`. | Function is used by active execution grading; active semantics belong closer to execution. | Refactor could affect tests and any legacy pipeline callers; must preserve behavior separately. | DOC-D can proceed after or before extraction if it labels current behavior and pending refactor. | Yes: code refactor ticket with compatibility tests. | Yes, pending Martin approval. |
| `deprecate_or_remove_later` | Plan removal of the pipeline liquidity helper. | Would reduce legacy residue. | Unsafe now because active execution grading depends on it. | Would block accurate execution docs until replacement is implemented. | Yes, but only after extraction/replacement. | No. |
| `keep_as_compatibility_only` | Treat liquidity helper as compatibility-only. | It lives in legacy namespace. | Contradicted by active execution import/call evidence. | Would misdocument active execution dependency. | Yes if Martin intentionally rewrites active execution first. | No. |
| `needs_martin_decision` | Martin decides whether to canonicalize in place, isolate, or extract. | Product/architecture intent is not encoded in current code. | Delays cleanup and DOC-D wording for execution boundary. | DOC-D execution section remains partial until decision or explicit interim boundary language. | Yes. | Yes as governance wrapper around `extract_active_utility`. |

Recommended option:
`extract_active_utility`

Reason:
`compute_tradeability_metrics` is actively used by execution grading, but its package path conflicts with legacy-pipeline labeling. Extraction into `scanner/execution/` or a neutral utility module would preserve current behavior while reducing namespace contamination.

Required follow-up ticket:
CODE-A2-FU-A — Extract or canonicalize active tradeability liquidity utility used by execution grading.

DOC-D status:
Partial. DOC-D may document execution grading if it notes that one active helper currently lives under a legacy-labeled namespace and that cleanup is pending.

Martin decision required:
Yes. Exact decision question: Should `scanner.pipeline.liquidity.compute_tradeability_metrics` be extracted to active execution/utility code, canonicalized in place, or isolated as a temporary legacy-namespace exception?

## 5. Conflict area B — evaluation export uses pipeline global ranking and backtest helper

### Evidence summary

| Required evidence item | Evidence |
| --- | --- |
| Source files inspected | `scanner/tools/export_evaluation_dataset.py`; `scanner/pipeline/global_ranking.py`; `scanner/backtest/e2_model.py`; `docs/audit/active_code_path_inventory_v0.md`; authority/context files. |
| Functions/classes inspected | `export_dataset`; `compute_global_ranked_candidates`; `compute_global_top20`; `evaluate_e2_candidate`; label-window helpers and CLI parser. |
| Tests inspected, if relevant | `tests/test_export_evaluation_dataset.py`; `tests/test_t23_slippage_metrics.py`; `tests/test_pr3_breakout_trend_scoring.py`. |
| Workflows inspected, if relevant | Backtest workflows under `.github/workflows/run-backtest-3a-exit-path-metrics.yml` and `.github/workflows/run-backtest-3b-exit-model-simulation.yml` were inspected as adjacent evaluation/backtest context. No direct workflow call to `export_evaluation_dataset.py` was identified in this focused review. |
| Call path evidence | `export_evaluation_dataset.py` imports `compute_global_top20` and `evaluate_e2_candidate`; `export_dataset` uses `compute_global_top20` to assign `global_rank` only to top-20 entries and uses E2 helpers for labels. |
| Artifact path evidence, if relevant | Export tool writes evaluation dataset outputs under a caller-supplied `--output-dir`; tests use `datasets/eval` temp paths. Backtest workflows use `evaluation/backtest/...` artifacts for current analysis outputs. |
| Authority conflict, if any | `scanner.pipeline.global_ranking` is under a legacy-labeled package, while the evaluation export tool and tests actively import it. `scanner.backtest.e2_model` package naming suggests backtest/legacy ambiguity but it is imported by active evaluation tooling. |

### Analysis

This path is active as executable evaluation tooling, but it is not evidence of active Daily/Intraday runtime ranking. `compute_global_top20` remains a valid helper for current export tests and dataset generation, but the namespace makes it ambiguous whether it is current evaluation support or retained compatibility for legacy snapshots.

`scanner.backtest.e2_model` appears to be current evaluation/backtest infrastructure by usage: the export tool imports its constants and label evaluator, and tests exercise the tool as an executable module. However, the `backtest` package name can confuse DOC-D readers and agents if not explicitly scoped as evaluation/replay support rather than live trading/runtime exit automation.

DOC-D can document evaluation/replay only partially while this dependency remains unresolved. It should say the export tool currently reuses legacy-named ranking/backtest helpers and must not treat that as Daily runner ranking architecture.

### Decision matrix — conflict area B

| Option | What it would mean | Evidence supporting it | Evidence against it / risk | Impact on DOC-D | Follow-up ticket required? | Recommended? yes/no/conditional |
| --- | --- | --- | --- | --- | --- | --- |
| `canonicalize_current_dependency` | Treat `global_ranking` and `e2_model` as current evaluation infrastructure. | Export tool imports both; tests execute export module and verify global-rank top-20 behavior and label fields. | Could blur active runtime ranking with evaluation-only ranking; `pipeline` and `backtest` package names remain misleading. | DOC-D evaluation section can proceed if clearly scoped to evaluation/replay. | Yes: documentation/boundary ticket for evaluation helpers. | Conditional. |
| `isolate_legacy_dependency` | Keep dependencies reachable but label them as legacy-named support for evaluation exports. | Namespaces are legacy/ambiguous; no focused evidence shows Daily runner imports `global_ranking`. | Too much isolation may understate their current executable evaluation role. | DOC-D may proceed with explicit compatibility/evaluation wording. | Yes: isolation/labeling ticket. | Yes for `global_ranking` pending Martin decision. |
| `extract_active_utility` | Move global-ranking evaluation helper and/or E2 label model into active `scanner/evaluation/`. | Export tool belongs to evaluation dataset generation; extraction would align namespace with role. | May require migration of tests and compatibility imports; must avoid changing output semantics. | DOC-D could document clean evaluation architecture after refactor. | Yes: code refactor ticket. | Conditional. |
| `deprecate_or_remove_later` | Plan removal of helper path. | If Martin decides legacy snapshot exports are obsolete, cleanup is possible. | Current tests and executable export tooling depend on it. | Would block evaluation docs until replacement/retirement decision. | Yes. | No now. |
| `keep_as_compatibility_only` | Retain as compatibility/replay support only, not current Daily architecture. | Export tool operates on snapshots; helpers are legacy-named; no active Daily runner dependency found. | If Martin intends the export pipeline as active evaluation architecture, compatibility-only may under-document it. | DOC-D can mention as compatibility/evaluation tooling, not runtime. | Yes: documentation/boundary-marker ticket. | Conditional/yes for `compute_global_top20` if Martin wants no extraction yet. |
| `needs_martin_decision` | Martin decides whether evaluation export helper paths are current evaluation infrastructure or compatibility-only. | Current code proves executable usage but not product intent. | Until decided, DOC-D evaluation wording remains cautious. | DOC-D evaluation/replay remains partial. | Yes. | Yes. |

Recommended option:
`needs_martin_decision`

Reason:
The evidence proves active executable evaluation usage, but not whether Martin wants these helpers canonicalized as current evaluation infrastructure, extracted into `scanner/evaluation/`, or retained only for compatibility/replay.

Required follow-up ticket:
CODE-A2-FU-B — Decide and label/extract evaluation export ranking and E2 label helpers.

DOC-D status:
Partial. DOC-D may document the export tool and replay/evaluation outputs as current executable tooling, but must mark `pipeline.global_ranking` and `backtest.e2_model` as ambiguous helper boundaries until Martin decides.

Martin decision required:
Yes. Exact decision question: Should `scanner.pipeline.global_ranking.compute_global_top20` and `scanner.backtest.e2_model` be treated as active evaluation infrastructure, extracted into `scanner/evaluation/`, or retained as compatibility-only replay helpers?

## 6. Conflict area C — full snapshot backfill reaches legacy pipeline scoring

### Evidence summary

| Required evidence item | Evidence |
| --- | --- |
| Source files inspected | `scanner/tools/backfill_snapshots.py`; `scanner/pipeline/__init__.py`; `scanner/pipeline/scoring/reversal.py`; `scanner/pipeline/scoring/breakout_trend_1_5d.py`; `scanner/pipeline/scoring/pullback.py`; `scanner/pipeline/snapshot.py`; `docs/audit/active_code_path_inventory_v0.md`; authority/context files. |
| Functions/classes inspected | `_run_full_mode`; `_validate_full_mode_prerequisites`; `_patched_full_mode_time_sources`; `build_parser`; `backfill`; `run_pipeline`; `score_reversals`; `score_breakout_trend_1_5d`; `score_pullbacks`. |
| Tests inspected, if relevant | `tests/test_backfill_snapshots.py`; pipeline scoring/golden tests identified by CODE-A1 and targeted searches. |
| Workflows inspected, if relevant | No direct workflow call to `scanner.tools.backfill_snapshots --mode full` was identified in this focused review. |
| Call path evidence | `backfill_snapshots.py` exposes `--mode` choices `minimal` and `full`; `_run_full_mode` imports `scanner.pipeline.run_pipeline`; `run_pipeline` imports and calls the scoring modules. |
| Artifact path evidence, if relevant | Full backfill writes snapshot files via pipeline snapshot history and marks metadata with `backfill_mode = full` and `backfill_source = pipeline`. |
| Authority conflict, if any | `scanner/pipeline/__init__.py` explicitly says the orchestrator is legacy and not for Independence-Release flows, but the full backfill CLI remains executable and tested. |

### Analysis

This path is executable and covered by tests, but evidence does not show it is operationally relevant to active Daily/Intraday runtime. The strongest classification is `active_analysis_or_backfill_compatibility`: it can be run for snapshot reconstruction or historical reproduction, but it should not be used as evidence for current Independence runtime scoring, ranking, or output semantics.

The path should not be ignored in repository documentation because it remains a reachable command path. However, DOC-D can ignore it when documenting active Daily/Intraday runtime semantics, as long as DOC-D includes a separate legacy/reference/compatibility note for analysis/backfill tools.

### Decision matrix — conflict area C

| Option | What it would mean | Evidence supporting it | Evidence against it / risk | Impact on DOC-D | Follow-up ticket required? | Recommended? yes/no/conditional |
| --- | --- | --- | --- | --- | --- | --- |
| `canonicalize_current_dependency` | Treat full-mode backfill and legacy pipeline scoring as current architecture. | CLI remains executable; tests verify full-mode success path through a fake `_run_full_mode`; run_pipeline can execute scoring. | Package orchestrator explicitly says not to use for Independence-Release flows; no active Daily/Intraday import evidence. | Would risk contaminating DOC-D with old scoring semantics. | Yes if Martin intentionally revives it. | No. |
| `isolate_legacy_dependency` | Keep full mode reachable but isolate/mark it as legacy pipeline backfill. | Legacy label and active executable path coexist. | Isolation alone may not prevent accidental operational use. | DOC-D can proceed if active runtime excludes it and tools section labels it. | Yes: boundary-marker ticket. | Yes. |
| `extract_active_utility` | Extract any still-needed snapshot/backfill utilities from legacy pipeline. | Backfill tool may need snapshot reconstruction capabilities independent of old scoring. | The full-mode value may depend on historical reproduction of old pipeline semantics; extraction could defeat that. | Useful only after Martin defines future backfill intent. | Yes: code refactor ticket after decision. | Conditional/no now. |
| `deprecate_or_remove_later` | Plan to remove or disable full mode and/or legacy scoring later. | Not active Daily/Intraday; package labels it legacy. | Current tests and possible historical backfill/replay use depend on it. | DOC-D can proceed with note that cleanup is pending. | Yes: cleanup ticket requiring approval. | Conditional. |
| `keep_as_compatibility_only` | Retain full mode for compatibility/backfill/historical reproduction only. | Executable CLI and tests exist; legacy orchestrator label excludes active Independence runtime. | Compatibility-only scope must be clearly documented to prevent runtime contamination. | DOC-D can document active runtime separately and mention full mode in tools/legacy compatibility. | Yes: docs/boundary-marker ticket. | Yes. |
| `needs_martin_decision` | Martin decides whether full mode remains compatibility-only, is isolated, or is removed later. | Operational intent is not proven by code alone. | Delays cleanup. | DOC-D analysis/backfill section remains partial until decision. | Yes. | Yes as approval gate. |

Recommended option:
`keep_as_compatibility_only`

Reason:
The path is executable and tested, but the orchestrator is explicitly legacy-labeled and no focused evidence shows it is part of active Independence Daily/Intraday runtime.

Required follow-up ticket:
CODE-A2-FU-C — Mark or isolate `backfill_snapshots.py --mode full` as legacy-pipeline compatibility/backfill and decide future removal criteria.

DOC-D status:
Partial. DOC-D may document active Daily/Intraday runtime without this path, but analysis/backfill and legacy/reference-only sections need explicit compatibility wording.

Martin decision required:
Yes. Exact decision question: Should `backfill_snapshots.py --mode full` remain executable only for historical compatibility/backfill, be isolated more strongly, or be deprecated/removed later?

## 7. Conflict area D — old mode names accepted by active scanner dispatch

### Evidence summary

| Required evidence item | Evidence |
| --- | --- |
| Source files inspected | `scanner/main.py`; `scanner/config.py`; `scanner/runners/daily.py`; `scanner/runners/intraday.py`; `scanner/storage/schema.py`; `docs/AI_CONTEXT_CURRENT.md`; `docs/audit/active_code_path_inventory_v0.md`; authority/context files. |
| Functions/classes inspected | `parse_args`; `_resolve_effective_run_mode`; `main`; `ScannerConfig.run_mode`; `validate_config`; storage scan-mode mapping; `run_daily_scan`; `run_intraday_scan`. |
| Tests inspected, if relevant | `tests/test_main_dispatch_ticket17_fixes.py`; `tests/test_sqlite_foundation.py`; `tests/test_ticket_p0_docs_authority_readme.py`. |
| Workflows inspected, if relevant | `.github/workflows/independence-shadow-live.yml` preflights `CMC_API_KEY` for `run_mode=standard`. |
| Call path evidence | `scanner/main.py` accepts `daily_discovery`, `standard`, `fast`, `offline`, `backtest`, and `intraday_promotion`; only `intraday_promotion` routes to Intraday, all daily modes route to `run_daily_scan`. |
| Artifact path evidence, if relevant | `scanner/storage/schema.py` normalizes old daily modes to `daily` for reporting/storage output families. |
| Authority conflict, if any | AI context warns `fast`, `standard`, `offline`, and `backtest` are deprecated/legacy active-mode assumptions, while code still accepts them and config validation allows only the older four values. |

### Analysis

The old mode names are active accepted values, but current dispatch does not preserve separate old-pipeline behavior for them. In `scanner/main.py`, `standard`, `fast`, `offline`, `backtest`, and `daily_discovery` are all daily modes that route to `run_daily_scan`; only `intraday_promotion` routes to `run_intraday_scan`.

`scanner/config.py` still defaults `run_mode` to `standard` and `validate_config` allows only `standard`, `fast`, `offline`, and `backtest`; it does not include `daily_discovery` or `intraday_promotion` in that validator. This is a separate validation/dispatch boundary inconsistency that DOC-D should not resolve silently.

Current-state docs should mention these old names only as accepted compatibility aliases or deprecated accepted values, not as distinct current runtime modes. A future code ticket should normalize, rename, or explicitly deprecate them.

### Decision matrix — conflict area D

| Option | What it would mean | Evidence supporting it | Evidence against it / risk | Impact on DOC-D | Follow-up ticket required? | Recommended? yes/no/conditional |
| --- | --- | --- | --- | --- | --- | --- |
| `canonicalize_current_dependency` | Treat old names as official current modes. | CLI and storage accept/map them; workflow references `run_mode=standard`; config defaults to `standard`. | Dispatch routes all old names to the same Daily runner; AI context calls them deprecated/legacy assumptions. | DOC-D could list them, but might imply behavior differences that do not exist. | Yes: docs update and validator consistency ticket. | No. |
| `isolate_legacy_dependency` | Keep names accepted but mark as legacy/deprecated aliases. | AI context warns against deprecated assumptions; storage maps them to daily. | If users rely on them, overly strong isolation may confuse operations. | DOC-D can proceed by naming canonical modes and listing aliases separately. | Yes: mode-boundary docs/code ticket. | Yes. |
| `extract_active_utility` | Not applicable except to extract mode normalization into a central helper. | Dispatch and storage both normalize modes. | Does not directly solve naming/product decision. | Could help DOC-D after implementation, but not the primary decision. | Yes if Martin approves central normalization refactor. | No as primary option. |
| `deprecate_or_remove_later` | Plan eventual removal or rejection of old names. | They no longer represent distinct current behavior. | Workflow/config/tests may still rely on `standard`; removal could break operations. | DOC-D can mention pending deprecation only after approval. | Yes: migration/deprecation ticket. | Conditional. |
| `keep_as_compatibility_only` | Retain old names as compatibility aliases that route to Daily. | Directly matches current dispatch behavior and storage normalization. | Requires clear user-facing wording; config validator inconsistency remains. | DOC-D can proceed with aliases clearly separated from canonical runner modes. | Yes: docs and normalization ticket. | Yes. |
| `needs_martin_decision` | Martin decides whether aliases remain accepted, are renamed, or are removed later. | Product compatibility choice is not inferable from code alone. | Delays cleanup. | DOC-D runtime entry point section is partial until alias policy is approved. | Yes. | Yes as approval gate. |

Recommended option:
`keep_as_compatibility_only`

Reason:
Current code accepts old names and routes them to Daily behavior, so they are not dead. They are also not distinct current runtime architectures. Compatibility-alias wording best matches implementation without over-canonicalizing legacy terminology.

Required follow-up ticket:
CODE-A2-FU-D — Define canonical mode names and compatibility alias normalization/deprecation policy.

DOC-D status:
Partial. DOC-D may document canonical Daily/Intraday runners and list old names as accepted compatibility aliases only after Martin approves that wording or as a clearly pending boundary note.

Martin decision required:
Yes. Exact decision question: Should `standard`, `fast`, `offline`, and `backtest` remain accepted compatibility aliases for Daily, be renamed/normalized centrally, or be removed later?

## 8. Cross-conflict boundary model

This model is proposed only. It is not approved current-state canonical documentation until Martin accepts it in a follow-up decision.

| Category | What it means | May DOC-D use it as current-state documentation evidence? | May future Codex tickets edit it for runtime changes? | Requires Martin decision before cleanup? |
| --- | --- | --- | --- | --- |
| `active_independence_runtime` | Code, tests, workflows, and artifacts that implement current Daily/Intraday runtime behavior. Examples: `scanner/runners/daily.py`, `scanner/runners/intraday.py`, active decision/execution modules. | Yes, as primary current-state evidence when validated against code/tests/artifacts. | Yes, if the ticket is a runtime-change ticket and tests cover behavior. | Usually no for normal changes; yes for architecture-breaking cleanup. |
| `active_independence_evaluation` | Executable evaluation/replay/export tooling that supports current analysis of Independence outputs but is not live Daily/Intraday runtime. | Yes, but only for evaluation/replay sections, not runtime ranking/scoring sections. | Yes, if scoped to evaluation tooling and artifacts. | Yes before removing or reclassifying ambiguous legacy-named helpers. |
| `active_analysis_or_backfill_compatibility` | Executable analysis/backfill/reproduction paths retained for snapshots, replay, migration, or historical reproduction. | Partially. DOC-D may describe them in analysis/backfill or compatibility sections, not as active runtime semantics. | Yes, but only for tooling/compatibility tickets, not current runtime behavior changes unless explicitly approved. | Yes before cleanup/removal. |
| `active_utility_misplaced_under_legacy_namespace` | Functions used by active code but located under a legacy-labeled namespace. | Yes with explicit boundary exception wording; no for generalizing the whole namespace. | Yes for extraction/canonicalization tickets; runtime changes require normal test coverage. | Yes before deciding canonicalize vs extract vs isolate. |
| `legacy_test_only` | Code retained only because tests cover historical or compatibility semantics; no executable active tool/runtime path found. | No for current-state behavior, except as legacy/test-history context. | Only for test cleanup or historical fixture maintenance tickets. | Yes before deletion if tests still encode desired compatibility. |
| `legacy_reference_only` | Historical code/docs/artifacts not active by current evidence. | No, except in explicit legacy/reference sections. | No for active runtime changes; only cleanup/migration tickets should touch it. | Yes before deletion if repository history or migration value is uncertain. |
| `ambiguous_requires_decision` | Evidence proves reachability but not product/architecture intent. | Partial at most; DOC-D must present the ambiguity rather than resolving it. | Only after the ticket states the selected decision or asks for investigation. | Yes. |

Suggested classification from this review:

| Path or concept | Proposed boundary category | Rationale |
| --- | --- | --- |
| `scanner/execution/grading.py` | `active_independence_runtime` | Active execution grading module called by execution adapter. |
| `scanner.pipeline.liquidity.compute_tradeability_metrics` | `active_utility_misplaced_under_legacy_namespace` | Active execution import/call despite pipeline namespace. |
| `scanner.tools.export_evaluation_dataset` | `active_independence_evaluation` | Executable export tool with tests. |
| `scanner.pipeline.global_ranking.compute_global_top20` | `ambiguous_requires_decision` or `active_independence_evaluation` after approval | Active evaluation import, but legacy namespace and non-runtime ranking ambiguity. |
| `scanner.backtest.e2_model` | `ambiguous_requires_decision` or `active_independence_evaluation` after approval | Active evaluation import, but package name implies backtest/legacy ambiguity. |
| `scanner.tools.backfill_snapshots --mode full` | `active_analysis_or_backfill_compatibility` | Executable and tested; reaches legacy pipeline. |
| `scanner.pipeline.run_pipeline` and `scanner/pipeline/scoring/*` | `active_analysis_or_backfill_compatibility` for full-mode backfill; otherwise `legacy_reference_only` for Independence runtime | Package label excludes Independence flows; scoring reachable through full backfill only. |
| `standard`, `fast`, `offline`, `backtest` mode names | `active_analysis_or_backfill_compatibility` / compatibility aliases | Accepted by dispatch/storage but route to Daily, not distinct runtime architectures. |

## 9. Decision matrices

This section consolidates the four per-conflict matrices above. The exact option taxonomy used throughout is:

- `canonicalize_current_dependency`
- `isolate_legacy_dependency`
- `extract_active_utility`
- `deprecate_or_remove_later`
- `keep_as_compatibility_only`
- `needs_martin_decision`

### Matrix index

| Conflict area | Matrix location | Primary recommended option | Governance option |
| --- | --- | --- | --- |
| A — execution grading uses pipeline liquidity | Section 4 | `extract_active_utility` | `needs_martin_decision` |
| B — evaluation export uses pipeline global ranking and backtest helper | Section 5 | `needs_martin_decision` | `needs_martin_decision` |
| C — full snapshot backfill reaches legacy pipeline scoring | Section 6 | `keep_as_compatibility_only` | `needs_martin_decision` |
| D — old mode names accepted by active scanner dispatch | Section 7 | `keep_as_compatibility_only` | `needs_martin_decision` |

## 10. Recommended follow-up ticket map

| conflict_area | current_evidence | risk_level: high \| medium \| low | available_options | recommended_option | why | required_follow_up_ticket | blocks_DOC_D: yes \| no \| partial | martin_decision_required: yes \| no |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A — execution grading uses pipeline liquidity | Active execution adapter calls grading; grading imports `scanner.pipeline.liquidity.compute_tradeability_metrics`. | high | `canonicalize_current_dependency`; `isolate_legacy_dependency`; `extract_active_utility`; `deprecate_or_remove_later`; `keep_as_compatibility_only`; `needs_martin_decision` | `extract_active_utility` | Active runtime helper is misplaced under legacy namespace; extraction would reduce contamination. | CODE-A2-FU-A — Extract/canonicalize execution tradeability liquidity helper. | partial | yes |
| B — evaluation export uses pipeline global ranking and backtest helper | Export tool imports `compute_global_top20` and `evaluate_e2_candidate`; tests execute export and verify rank/label behavior. | medium | `canonicalize_current_dependency`; `isolate_legacy_dependency`; `extract_active_utility`; `deprecate_or_remove_later`; `keep_as_compatibility_only`; `needs_martin_decision` | `needs_martin_decision` | Executable evaluation use is proven, but current evaluation infrastructure vs compatibility-only intent is not. | CODE-A2-FU-B — Decide/label/extract evaluation ranking and E2 helpers. | partial | yes |
| C — full snapshot backfill reaches legacy pipeline scoring | Backfill CLI accepts `--mode full`; `_run_full_mode` imports `scanner.pipeline.run_pipeline`; pipeline run calls scoring modules. | medium | `canonicalize_current_dependency`; `isolate_legacy_dependency`; `extract_active_utility`; `deprecate_or_remove_later`; `keep_as_compatibility_only`; `needs_martin_decision` | `keep_as_compatibility_only` | Executable and tested, but legacy orchestrator label excludes active Independence runtime. | CODE-A2-FU-C — Isolate/label full-mode backfill and decide future removal. | partial | yes |
| D — old mode names accepted by active scanner dispatch | CLI accepts old names; only `intraday_promotion` routes Intraday; old names route Daily; storage normalizes them to daily. | medium | `canonicalize_current_dependency`; `isolate_legacy_dependency`; `extract_active_utility`; `deprecate_or_remove_later`; `keep_as_compatibility_only`; `needs_martin_decision` | `keep_as_compatibility_only` | Names remain accepted but do not represent distinct runtime architectures. | CODE-A2-FU-D — Define canonical mode names and compatibility alias policy. | partial | yes |

## 11. DOC-D unblock assessment

Overall DOC-D status: partial proceed.

DOC-D may proceed on stable active Daily/Intraday runner sections if it follows the boundary rules below. DOC-D must not document legacy pipeline scoring/ranking/output semantics as current Independence runtime behavior. It must mark evaluation/backfill/mode alias ambiguity where relevant or wait for Martin decisions.

| DOC-D area | Can proceed? yes/no/partial | Conditions | Relevant conflict areas | Notes |
| --- | --- | --- | --- | --- |
| Architecture overview | partial | May describe active Daily/Intraday architecture and explicitly exclude legacy pipeline orchestrator from current runtime. Must include a boundary note for mixed `scanner/pipeline/` evidence. | A, B, C, D | Avoid saying all pipeline code is dead. |
| Runtime entry points | partial | May document `scanner/main.py` dispatch, but old mode names must be listed as compatibility aliases or unresolved aliases, not separate architectures. | D | Needs Martin approval for final alias wording. |
| Daily runner | yes | May document `scanner/runners/daily.py` as active Daily runtime. Must not import legacy scoring semantics from `scanner.pipeline.run_pipeline`. | A, C, D | Execution subsection has a boundary exception for liquidity helper. |
| Intraday runner | yes | May document Intraday runner as the `intraday_promotion` dispatch target if validated by current code. | D | Old daily aliases do not route Intraday. |
| Execution/tradeability | partial | May document current grading behavior, but must note active dependency on `scanner.pipeline.liquidity` and pending extraction/canonicalization decision. | A | Do not imply entire pipeline namespace is active. |
| Evaluation/replay | partial | May document export/replay tooling as executable, but must label `pipeline.global_ranking` and `backtest.e2_model` boundary ambiguity. | B | Avoid describing export ranking as live Daily ranking unless validated separately. |
| Analysis/backfill tools | partial | May document minimal/full backfill commands only with compatibility/historical reproduction labels for full mode. | C | Full mode should not be framed as active scanner runtime. |
| Output/report paths | partial | May document active runner output/report paths from current builders/artifacts. Must not use legacy pipeline report output semantics as current runtime without separate validation. | C | Legacy pipeline writes reports/snapshots in its own path. |
| Legacy/reference-only section | yes | May include `scanner/pipeline.run_pipeline` and scoring as legacy/reference/compatibility, while carving out active utility exceptions. | A, B, C | This section should explicitly list exceptions rather than flattening the namespace. |

## 12. Martin decision checklist

- [ ] Decide whether `scanner.pipeline.liquidity` should be canonicalized as active utility or extracted from `scanner/pipeline/`.
- [ ] Decide whether `scanner.pipeline.global_ranking` remains active evaluation support or compatibility-only.
- [ ] Decide whether `scanner.backtest.e2_model` should be treated as active evaluation infrastructure despite its package name.
- [ ] Decide whether `backfill_snapshots.py --mode full` should remain executable as compatibility/backfill-only.
- [ ] Decide whether legacy pipeline scoring should be isolated, deprecated, or retained for historical reproduction.
- [ ] Decide whether `standard`, `fast`, `offline`, and `backtest` remain accepted compatibility aliases or should be removed/renamed later.
- [ ] Decide which DOC-D sections may proceed before cleanup.

## 13. No action taken confirmation

- [x] No scanner code changed.
- [x] No tests changed.
- [x] No schemas changed.
- [x] No workflows changed.
- [x] No runtime behavior changed.
- [x] No files moved.
- [x] No files deleted.
- [x] No deprecation markers added.
- [x] No current-state canonical domain documentation updated.
- [x] Only the CODE-A2 audit/decision-preparation artifact was added.
