# Data and Reports Evidence Inventory v0

## Purpose

This file is a non-authoritative evidence inventory for DOC-E2. It is not canonical current-state documentation and does not change data/report contracts by itself. Its purpose is to collect current repository evidence for data fields, report artifacts, diagnostics artifacts, schema-version context, evaluation/T30 outputs, consumer guidance, documentation gaps, and unresolved conflicts.

Status vocabulary follows the ticket: `confirmed`, `partial`, and `needs_review`. `confirmed` is used only where current code/tests/schema/artifacts or multiple consistent non-AI evidence sources support the claim.

## Source coverage summary

| Source type | Checked? | Paths / refs | Notes |
|---|---|---|---|
| Code | yes | `scanner/output/schema.py`, `scanner/output/report_builder.py`, `scanner/output/diagnostics.py`, `scanner/runners/daily.py`, `scanner/runners/intraday.py`, `scanner/decision/entry_location.py`, `scanner/execution/grading.py`, `scanner/execution/policy.py`, `scanner/execution/tradeability_metrics.py`, `scanner/storage/snapshots.py`, `scanner/evaluation/replay.py`, `scanner/evaluation/forward_returns.py`, `scanner/evaluation/dataset_export.py`, `scanner/tools/export_evaluation_dataset.py`, `scanner/pipeline/global_ranking.py`, `scanner/backtest/e2_model.py` | Current output/report/runner/evaluation paths were used as primary evidence. The exporter cluster is treated as active executable legacy snapshot evaluation export tooling, but not active `scanner/evaluation/*` infrastructure. |
| Tests | yes | `tests/test_ticket13_output_artifacts.py`, `tests/test_q1_q2_operational_tradeability.py`, `tests/test_ticket16_execution_adapter.py`, `tests/test_ticket26_execution_depth_analysis.py`, `tests/test_ticket27_execution_size_policy.py`, `tests/test_ticket28_operational_tradeability.py`, `tests/test_ticket29_reduced_size_eligibility.py`, `tests/test_ticket30_forward_return_evaluation.py`, `tests/test_ticket30_operational_tradeability_eval.py`, `tests/test_entry_location_t_el2.py`, `tests/test_ticket14_snapshots.py`, `tests/test_ticket15_daily_runner.py`, `tests/test_intraday_runner.py`, `tests/test_evaluation_dataset_export.py` | Tests confirm many output, tradeability, Entry-Location, snapshot path, and evaluation fields. |
| Schemas / validators | yes | `scanner/output/schema.py`, `scanner/storage/schema.py` | Output validators are code-level schemas; no standalone JSON Schema file found for report/diagnostics. |
| Current artifacts | partial | Path templates in producer code: `reports/runs/YYYY/MM/DD/<run_id>/report.json`, `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`, `reports/daily/YYYY/MM/DD/report.json`, `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`, `evaluation/replay/*`, `evaluation/exports/*` | Historical/generated artifacts were not modified. Evidence is primarily producer path code and tests. |
| SCHEMA_CHANGES | yes | `docs/SCHEMA_CHANGES.md` | Strong change/evidence log for `ir1.1` through `ir1.5`; not treated as a full data model. |
| Current docs | yes | `docs/canonical/ARCHITECTURE.md`, `docs/canonical/RUNTIME_AND_OPERATIONS.md`, `docs/canonical/DATA_MODEL.md`, `docs/canonical/REPORTS.md`, `docs/canonical/SNAPSHOTS.md`, `docs/canonical/AUTHORITY.md` | Current docs provide boundaries and known stale/partial areas; field-level semantics remain incomplete. |
| Tickets / PRs | yes | `docs/tickets/2026-06-11__DOC-E1__data_reports_evidence_inventory.md`, `docs/audit/active_code_path_inventory_v0.md`, `docs/audit/legacy_pipeline_boundary_review_v0.md`, `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md`, current decision note under `docs/canonical/decisions/Q1_Q2_operational_tradeability_and_stablecoin_exclusion.md` | Used for requested scope and boundary classification; CODE-A1/CODE-A2 nuance is preserved for the exporter/global-ranking/e2-model cluster. |
| AI context | no | none | `docs/AI_CONTEXT_CURRENT.md` was not needed and is not the sole source for any confirmed claim. |

## Candidate exclusion and tradeability fields

Field: candidate_excluded
Claim: `candidate_excluded` is emitted as a top-level diagnostics boolean, mirrored from the nested `universe.candidate_excluded` block with backward-compatible normalization from the nested value when the top-level key is absent. It is used to remove excluded symbols from actionable report candidate lists (`confirmed_candidates`, `early_candidates`, `watchlist`) while retaining excluded rows in diagnostics.
Evidence sources:
  - ticket_text: DOC-E1 section 8.1 requires this field; Q1/Q2 decision note documents stable/cash exclusion intent.
  - current_code: `scanner/runners/daily.py` builds nested and top-level `candidate_excluded`; `scanner/output/schema.py::validate_diagnostics_record` normalizes top-level from nested; `scanner/output/report_builder.py::write_run_report` removes excluded symbols from actionable lists; `scanner/runners/daily.py::ranked_inputs` filters actionable excluded categories.
  - test: `tests/test_q1_q2_operational_tradeability.py::test_candidate_excluded_symbols_are_removed_from_candidate_lists_and_latest_files`; `tests/test_q1_q2_operational_tradeability.py::test_stable_cash_categories_are_classified_as_candidate_excluded`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` requires boolean output after normalization.
  - artifact: `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`; report lists in `reports/runs/.../report.json` and candidate latest indexes.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 entry says diagnostics emit top-level `candidate_excluded` context and final actionable lists exclude `candidate_excluded=true`.
Status: confirmed
Notes: DOC-E2 should document both locations and the current preferred top-level field, plus the nested `universe` compatibility/mirroring relation.

Field: is_tradeable_candidate
Claim: `is_tradeable_candidate` is a top-level diagnostics nullable boolean produced from decision bucket plus reduced-size execution eligibility; it remains a bucket-/execution-scoped audit field and is not the final `ir1.5+` operational tradeability label.
Evidence sources:
  - ticket_text: DOC-E1 section 8.1 requires this field; Q1/Q2 decision note says it remains unchanged audit signal.
  - current_code: `scanner/execution/policy.py::is_tradeable_candidate`; `scanner/runners/daily.py` assigns it from decision bucket and `is_reduced_size_eligible`; `scanner/output/schema.py::validate_diagnostics_record` accepts nullable bool and defaults missing to `False`; `scanner/evaluation/replay.py` preserves it in event rows.
  - test: `tests/test_q1_q2_operational_tradeability.py`; `tests/test_ticket28_operational_tradeability.py`; `tests/test_ticket30_operational_tradeability_eval.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` field normalization.
  - artifact: `symbol_diagnostics.jsonl.gz`; daily execution-aware report segments include it; evaluation event timeline and signal metrics include it.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 says existing `is_tradeable_candidate` remains bucket-/execution-scoped audit field.
Status: confirmed
Notes: DOC-E2 should warn consumers not to use this alone as final row-level tradeability for `ir1.5+`.

Field: is_operational_trade_candidate
Claim: `is_operational_trade_candidate` is the top-level `ir1.5+` final row-level operational tradeability label, computed as `is_tradeable_candidate is True AND candidate_excluded is not True`, and should be preferred by T30/operative consumers.
Evidence sources:
  - ticket_text: DOC-E1 section 8.1 requires this field.
  - current_code: `scanner/output/schema.py::is_operational_trade_candidate`; `scanner/output/schema.py::validate_diagnostics_record`; `scanner/runners/daily.py` assigns it; `scanner/evaluation/replay.py::_operational_tradeability` prefers native field and compat-backfills only when absent.
  - test: `tests/test_q1_q2_operational_tradeability.py::test_operational_trade_candidate_formula`; `tests/test_ticket30_operational_tradeability_eval.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` always writes normalized `is_operational_trade_candidate`.
  - artifact: `symbol_diagnostics.jsonl.gz`; daily execution-aware report segments; evaluation timeline and metrics.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 documents field and consumer impact.
Status: confirmed
Notes: DOC-E2 should make this the preferred consumer field for `ir1.5+` and document compat behavior for pre-`ir1.5` records.

## Execution fields

Field: execution_status
Claim: The exact expected field name `execution_status` is not an active diagnostics/report field; current diagnostics use `execution_status_raw`, while `ExecutionInputContract` has an internal `execution_status` attribute before serialization.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 requires `execution_status` as an expected subject.
  - current_code: `scanner/execution/grading.py::ExecutionGradeResult` and `ExecutionInputContract` use internal status; `scanner/runners/daily.py` and `scanner/runners/intraday.py` serialize `execution_status_raw`; `scanner/output/schema.py` validates `execution_status_raw`.
  - test: `tests/test_ticket16_execution_adapter.py` asserts `execution_status_raw`; no active test found for top-level diagnostics field named exactly `execution_status`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` has `execution_status_raw`, not `execution_status`.
  - artifact: `symbol_diagnostics.jsonl.gz` and execution-aware report segments use `execution_status_raw`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` Ticket 24 notes recognized raw statuses.
Status: partial
Notes: Field-name mismatch. DOC-E2 should document `execution_status_raw` as implemented and mention `execution_status` only as internal/expected-name mismatch if needed.

Field: execution_status_raw
Claim: `execution_status_raw` is the active serialized diagnostics/report execution status field. Known values from current grading/policy paths include `direct_ok`, `tranche_ok`, `marginal`, `fail`, `unknown`, and `null` for not-attempted symbols.
Evidence sources:
  - ticket_text: DOC-E1 section 10 search terms include execution status concepts.
  - current_code: `scanner/execution/grading.py::grade_execution_orderbook`; `scanner/runners/daily.py`; `scanner/runners/intraday.py`; `scanner/runners/daily.py::_build_execution_aware_report_payload`.
  - test: `tests/test_ticket16_execution_adapter.py`; `tests/test_ticket26_execution_depth_analysis.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` nullable string.
  - artifact: `symbol_diagnostics.jsonl.gz`; `execution_aware_candidate_segments` in daily report.
  - schema_changes: `docs/SCHEMA_CHANGES.md` Ticket 24 summary lists recognized raw statuses including `null` for not-attempted.
Status: confirmed
Notes: DOC-E2 should prefer `execution_status_raw` for current artifacts.

Field: execution_size_class
Claim: `execution_size_class` is a top-level diagnostics field, included in execution-aware report segments and evaluation metrics. It is derived by policy from execution-attempt state, raw execution status, and depth ratio band, and values include `not_evaluated`, `full`, `blocked`, `not_evaluable`, `reduced_75`, `reduced_50`, `reduced_25`, and `observe_only`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 requires this field.
  - current_code: `scanner/execution/policy.py::classify_execution_size`; `scanner/runners/daily.py`; `scanner/runners/intraday.py`; `scanner/runners/daily.py::_build_execution_aware_report_payload`; `scanner/evaluation/replay.py`.
  - test: `tests/test_ticket27_execution_size_policy.py`; `tests/test_ticket29_reduced_size_eligibility.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` nullable string.
  - artifact: `symbol_diagnostics.jsonl.gz`; `execution_aware_candidate_segments`; evaluation signal metrics.
  - schema_changes: `docs/SCHEMA_CHANGES.md` T28/T29 entries mention execution-size and reduced-size concepts.
Status: confirmed
Notes: DOC-E2 should define it as diagnostics top-level and report-segment field, not a report root field.

Field: is_reduced_size_eligible
Claim: `is_reduced_size_eligible` is a top-level diagnostics boolean derived from raw execution status, execution size class, tradeability reason keys, and explicit non-depth gate flags; it feeds `is_tradeable_candidate`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 requires this field.
  - current_code: `scanner/execution/policy.py::is_reduced_size_eligible`; `scanner/runners/daily.py`; `scanner/runners/intraday.py`; `scanner/output/schema.py::validate_diagnostics_record`.
  - test: `tests/test_ticket29_reduced_size_eligibility.py`; `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` requires boolean with default `False`.
  - artifact: `symbol_diagnostics.jsonl.gz`; execution-aware report segments; evaluation signal metrics.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.1/T29 notes `tradeability_reason_keys` for reduced-size gating.
Status: confirmed
Notes: DOC-E2 should document non-depth reason/gate dependency and its upstream role for `is_tradeable_candidate`.

Field: execution_grade_t16
Claim: `execution_grade_t16` is retained as a top-level diagnostics compatibility field but current validation requires it to be `null`; current effective grading is represented by `execution_grade_effective`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 requires this field.
  - current_code: `scanner/runners/daily.py` and `scanner/runners/intraday.py` seed `execution_grade_t16=None`; `scanner/output/schema.py::validate_diagnostics_record` raises if non-null.
  - test: `tests/test_ticket16_execution_adapter.py`; schema validation coverage in output tests.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` enforces null.
  - artifact: `symbol_diagnostics.jsonl.gz` contains the field as `null` in current records.
  - schema_changes: `docs/SCHEMA_CHANGES.md` references newer effective execution fields; no current non-null T16 grade support found.
Status: confirmed
Notes: DOC-E2 should mark this as compatibility/deprecated-by-null, not current scoring signal.

Field: execution_grade
Claim: `execution_grade` appears as an internal `ExecutionInputContract` attribute but is set to `None` in current orderbook grading and is not the active serialized diagnostics field.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 asks to add related discovered execution fields.
  - current_code: `scanner/execution/grading.py::grade_execution_orderbook` creates `ExecutionInputContract(execution_grade=None)`; serialized diagnostics use `execution_grade_effective` and `execution_grade_t16`.
  - test: none found for serialized top-level `execution_grade`.
  - schema: none found for diagnostics field named exactly `execution_grade`.
  - artifact: none found in active report/diagnostics path.
  - schema_changes: none found for active serialized `execution_grade`.
Status: needs_review
Notes: Avoid documenting `execution_grade` as an active output field unless DOC-E2 explicitly covers internal contracts.

Field: execution_grade_effective
Claim: `execution_grade_effective` is the active numeric execution-grade output used in diagnostics, execution-aware report segments, and evaluation rows; it is derived by execution-size policy rather than by the legacy `execution_grade_t16` field.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 asks to add related fields.
  - current_code: `scanner/execution/policy.py::classify_execution_size`; `scanner/runners/daily.py`; `scanner/runners/intraday.py`; `scanner/runners/daily.py::_build_execution_aware_report_payload`; `scanner/evaluation/replay.py`.
  - test: `tests/test_ticket27_execution_size_policy.py`; `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` finite number or null.
  - artifact: `symbol_diagnostics.jsonl.gz`; daily execution-aware report segments; evaluation signal metrics.
  - schema_changes: `docs/SCHEMA_CHANGES.md` T28/T29 execution-size/effective-grade entries.
Status: confirmed
Notes: DOC-E2 should document nullable numeric semantics and relation to `execution_size_class`.

Field: execution_notional_usdt
Claim: No active serialized field named exactly `execution_notional_usdt` was found. Execution configuration contains notional inputs and tradeability metrics use notional thresholds, but this exact artifact field is not confirmed.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 example related field.
  - current_code: `scanner/execution/grading.py::_LegacyExecutionCfg` reads `notional_total_usdt` and `notional_chunk_usdt`; no active diagnostics key named `execution_notional_usdt` found.
  - test: none found for exact field.
  - schema: none found.
  - artifact: none found.
  - schema_changes: none found for exact field.
Status: needs_review
Notes: DOC-E2 should not invent this field. If notional inputs need documentation, use actual config/metric names.

Field: execution_depth_impact
Claim: No active serialized field named exactly `execution_depth_impact` was found. Closest active fields are `available_depth_1pct_usdt`, `depth_threshold_1pct_usdt`, `available_depth_ratio`, `depth_ratio_band`, `bid_depth_1pct_usdt`, `ask_depth_1pct_usdt`, `estimated_slippage_bps`, and `spread_pct`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.2 example related field.
  - current_code: `scanner/output/schema.py::validate_diagnostics_record`; `scanner/runners/daily.py::_build_execution_aware_report_payload`; `scanner/execution/tradeability_metrics.py`.
  - test: `tests/test_ticket26_execution_depth_analysis.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` validates closest numeric fields.
  - artifact: `symbol_diagnostics.jsonl.gz`; execution-aware report segments.
  - schema_changes: `docs/SCHEMA_CHANGES.md` execution-depth/tradeability entries.
Status: partial
Notes: Exact field mismatch; DOC-E2 should document actual fields, not this expected label.

## Entry-Location / T_EL2 fields

Field: entry_location
Claim: `entry_location` is an optional nested diagnostics block added in `ir1.3`; active daily diagnostics attach it after execution/tradeability fields, while older accepted diagnostics may omit it and should be treated as not evaluated by version-gated consumers.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 requires this field.
  - current_code: `scanner/decision/entry_location.py::attach_entry_location`; `scanner/runners/daily.py`; `scanner/output/schema.py::normalize_entry_location_block`.
  - test: `tests/test_entry_location_t_el2.py`; `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py::normalize_entry_location_block`; accepted schema versions include pre-`ir1.3` versions.
  - artifact: `symbol_diagnostics.jsonl.gz` nested block.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 entry.
Status: confirmed
Notes: DOC-E2 should document nested structure and absence semantics separately from `null` field values.

Field: entry_location_bucket
Claim: No active field named exactly `entry_location_bucket` was found. Current T_EL2 status/bucket-like output is `entry_location.entry_location_status` with values `fresh_entry`, `acceptable_entry`, `extended_entry`, `chased_entry`, and `not_evaluable`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 requires this expected subject.
  - current_code: `scanner/decision/entry_location.py::ENTRY_LOCATION_STATUS_VALUES`; `scanner/output/schema.py::ENTRY_LOCATION_STATUS_VALUES`; no exact `entry_location_bucket` field found.
  - test: `tests/test_entry_location_t_el2.py` uses status/action hint names.
  - schema: `scanner/output/schema.py::normalize_entry_location_block` validates `entry_location_status`.
  - artifact: `symbol_diagnostics.jsonl.gz` nested `entry_location_status`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 lists `entry_location_status`, not `entry_location_bucket`.
Status: partial
Notes: Expected-name mismatch; add to DOC-E2 as `entry_location_status` if documenting actual implementation.

Field: entry_location_reason
Claim: No active single field named exactly `entry_location_reason` was found. Current implementation uses `entry_location.entry_location_reason_primary` and `entry_location.entry_location_reason_codes`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 requires this expected subject.
  - current_code: `scanner/decision/entry_location.py::EntryLocationResult`; `scanner/output/schema.py::normalize_entry_location_block`.
  - test: `tests/test_entry_location_t_el2.py`; `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py::normalize_entry_location_block`.
  - artifact: `symbol_diagnostics.jsonl.gz` nested reason fields.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 lists reason primary/codes.
Status: partial
Notes: DOC-E2 should document implemented primary/codes fields and avoid asserting a flat `entry_location_reason` field.

Field: entry_location_flags
Claim: No active grouped field named exactly `entry_location_flags` was found. The closest active flag is nested `range_high_proximity_warning`, duplicated inside `entry_location_inputs_used` for audit input context.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 requires this expected subject.
  - current_code: `scanner/decision/entry_location.py::_range_high_warning`; `scanner/output/schema.py::normalize_entry_location_block`.
  - test: `tests/test_entry_location_t_el2.py`.
  - schema: `scanner/output/schema.py::normalize_entry_location_block`.
  - artifact: `symbol_diagnostics.jsonl.gz` nested `range_high_proximity_warning`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 lists `range_high_proximity_warning`.
Status: partial
Notes: Expected-name mismatch; document actual flag field.

Field: entry_location_score
Claim: No active field named `entry_location_score` was found. Entry-Location is categorical/status-and-hint based, with numeric input distances retained under `entry_location_inputs_used` rather than a score.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 requires this expected subject.
  - current_code: `scanner/decision/entry_location.py`; `scanner/output/schema.py`.
  - test: none found for exact field.
  - schema: none found for exact field.
  - artifact: none found.
  - schema_changes: none found for exact field.
Status: needs_review
Notes: DOC-E2 should not document a score unless new evidence is added.

Field: buy_now
Claim: No active field named exactly `buy_now` was found. The current buy-now concept is the `entry_action_hint` value `buy_now_candidate`, and daily reports segment those records under `entry_location_candidate_segments.buy_now_candidates`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 requires concept.
  - current_code: `scanner/decision/entry_location.py::_resolve_action_hint`; `scanner/decision/entry_location.py::build_entry_location_report_segments`; `scanner/runners/daily.py` adds `entry_location_candidate_segments`.
  - test: `tests/test_entry_location_t_el2.py`; `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py::ENTRY_ACTION_HINT_VALUES` includes `buy_now_candidate`.
  - artifact: nested diagnostics `entry_action_hint`; report segment `buy_now_candidates`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 example uses `buy_now_candidate`.
Status: partial
Notes: Document implemented value/segment, not a boolean/field named `buy_now`.

Field: watchlist
Claim: `watchlist` is an active report symbol-list bucket and an Entry-Location-adjacent report consumer concept, but no T_EL2 field named `watchlist` exists. Entry-Location report segments use `early_watch_candidates` for early fresh/acceptable monitor-only rows.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 includes watchlist concept.
  - current_code: `scanner/output/schema.py::SYMBOL_LIST_BUCKET_KEYS`; `scanner/runners/daily.py` builds `symbol_lists.watchlist`; `scanner/decision/entry_location.py::build_entry_location_report_segments` builds `early_watch_candidates`.
  - test: `tests/test_ticket13_output_artifacts.py`; `tests/test_entry_location_t_el2.py`.
  - schema: `scanner/output/schema.py::normalize_symbol_lists`.
  - artifact: `report.json` `symbol_lists.watchlist`; latest index `latest_watchlist.json`; report entry-location segment.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 says final actionable `watchlist` excludes `candidate_excluded=true`.
Status: confirmed
Notes: DOC-E2 should separate report bucket/list semantics from Entry-Location action hints.

Field: avoid_chase
Claim: No active field/value named exactly `avoid_chase` was found. The implemented action hint value is `avoid_chasing`, emitted when status is `chased_entry`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 requires concept.
  - current_code: `scanner/decision/entry_location.py::_resolve_action_hint`; `scanner/output/schema.py::ENTRY_ACTION_HINT_VALUES`.
  - test: `tests/test_entry_location_t_el2.py`.
  - schema: `scanner/output/schema.py::normalize_entry_location_block` validates `avoid_chasing`.
  - artifact: `symbol_diagnostics.jsonl.gz` nested `entry_action_hint`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 lists action hint field, not exact `avoid_chase`.
Status: partial
Notes: Expected-name mismatch; document actual `avoid_chasing` value.

Field: reduced_25
Claim: `reduced_25` is an execution depth-ratio band / execution-size class value and affects Entry-Location action hints: fresh reduced-size confirmed candidates become acceptable-if-strategy-allows, while acceptable `reduced_25` candidates are told to wait for pullback.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 includes concept.
  - current_code: `scanner/execution/policy.py::depth_ratio_band`; `scanner/execution/policy.py::classify_execution_size`; `scanner/decision/entry_location.py::_resolve_action_hint`.
  - test: `tests/test_ticket27_execution_size_policy.py`; `tests/test_entry_location_t_el2.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record` validates `execution_size_class`/`depth_ratio_band` as nullable strings.
  - artifact: `symbol_diagnostics.jsonl.gz`; execution-aware and entry-location report segments.
  - schema_changes: `docs/SCHEMA_CHANGES.md` T28/T29 execution-size context.
Status: confirmed
Notes: Document as execution-size value, not as a standalone field.

Field: entry_action_hint
Claim: `entry_action_hint` is the active nested T_EL2 decision/action hint field with closed values including `buy_now_candidate`, `acceptable_if_strategy_allows`, `wait_for_pullback`, `avoid_chasing`, `monitor_only`, and `not_evaluable`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.3 asks to cover discovered T_EL2 decision fields.
  - current_code: `scanner/decision/entry_location.py::ENTRY_ACTION_HINT_VALUES`; `scanner/decision/entry_location.py::_resolve_action_hint`; `scanner/output/schema.py::ENTRY_ACTION_HINT_VALUES`.
  - test: `tests/test_entry_location_t_el2.py`; `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py::normalize_entry_location_block`.
  - artifact: `symbol_diagnostics.jsonl.gz`; `entry_location_candidate_segments` in daily report.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3.
Status: confirmed
Notes: This is a key actual field for DOC-E2.

## Null / skipped / failed evaluation semantics

Field: null
Claim: `null` is used for nullable diagnostics/report fields where a value is absent, not attempted, not computable, or intentionally not applicable depending on field context; consumers must use the field-specific status/reason when present rather than treating all `null` values identically.
Evidence sources:
  - ticket_text: DOC-E1 section 8.4 requires this semantic value.
  - current_code: `scanner/output/schema.py` nullable validators; `scanner/runners/daily.py` seeds not-attempted execution fields as `None`; `scanner/evaluation/forward_returns.py` sets metrics to `None` with status fields.
  - test: `tests/test_ticket16_execution_adapter.py`; `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: `scanner/output/schema.py::_require_nullable_str`, `_require_nullable_bool`, numeric nullable validation.
  - artifact: diagnostics fields such as `execution_pass`, `execution_grade_t16`, `execution_grade_effective`, and evaluation metric fields.
  - schema_changes: `docs/SCHEMA_CHANGES.md` T24 notes `null` raw status for not-attempted symbols; ir1.2 says missing Entry-Location input fields can be read as `null`.
Status: confirmed
Notes: DOC-E2 should provide field-specific null semantics rather than a universal definition.

Field: not_evaluated
Claim: `not_evaluated` is an explicit string used by execution size policy when execution was not attempted, and SCHEMA_CHANGES also uses it as reader semantics for missing pre-`ir1.3` `entry_location` blocks.
Evidence sources:
  - ticket_text: DOC-E1 section 8.4 requires this semantic value.
  - current_code: `scanner/execution/policy.py::classify_execution_size`; `scanner/runners/intraday.py` seeds `execution_size_class="not_evaluated"`.
  - test: `tests/test_ticket27_execution_size_policy.py`; `tests/test_intraday_runner.py`.
  - schema: `scanner/output/schema.py` accepts nullable string; no closed enum for execution size class.
  - artifact: `symbol_diagnostics.jsonl.gz` execution fields; reader interpretation for missing older `entry_location` block.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 says missing older `entry_location` blocks should be treated as `not_evaluated`.
Status: confirmed
Notes: DOC-E2 should distinguish explicit serialized value from compatibility interpretation of absent blocks.

Field: not_evaluable
Claim: `not_evaluable` is used when an evaluation was attempted conceptually but inputs/state make a value not computable, including Entry-Location classification, execution-size classification for unknown/unhandled statuses, depth ratio band for missing ratio, and universe activity/pre-4h gates.
Evidence sources:
  - ticket_text: DOC-E1 section 8.4 requires this semantic value.
  - current_code: `scanner/decision/entry_location.py::_classify_status`; `scanner/execution/policy.py::depth_ratio_band`; `scanner/execution/policy.py::classify_execution_size`; `scanner/universe/market_data_budget.py`.
  - test: `tests/test_entry_location_t_el2.py`; `tests/test_ticket27_execution_size_policy.py`.
  - schema: `scanner/output/schema.py` Entry-Location status/action hint closed values include `not_evaluable`.
  - artifact: `symbol_diagnostics.jsonl.gz` fields such as `entry_location_status`, `entry_action_hint`, `execution_size_class`, `depth_ratio_band`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.3 documents `not_evaluable` in Entry-Location values/examples; other entries discuss not-evaluable gates.
Status: confirmed
Notes: DOC-E2 should distinguish from `not_evaluated`.

Field: unknown
Claim: `unknown` is used for execution status when orderbook/depth evaluation cannot classify due to missing/stale/fetch-failed data, and as compatibility/placeholder state in some eligibility/evaluation contexts.
Evidence sources:
  - ticket_text: DOC-E1 section 8.4 requires this semantic value.
  - current_code: `scanner/execution/grading.py::grade_execution_orderbook`; `scanner/execution/policy.py::classify_execution_size`; `scanner/evaluation/replay.py` handles unknown/missing event bar ids.
  - test: `tests/test_ticket16_execution_adapter.py`; `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: `scanner/output/schema.py` nullable string fields accept it where produced.
  - artifact: diagnostics `execution_status_raw="unknown"`; evaluation diagnostics count missing/unknown event bar ids.
  - schema_changes: `docs/SCHEMA_CHANGES.md` Ticket 24 summary recognizes `unknown` raw execution status and `unknown_execution` report bucket.
Status: confirmed
Notes: DOC-E2 should document `unknown` per field, especially execution vs event bar id contexts.

Field: failed
Claim: `failed` appears mainly as report/summary label and gate status language; raw execution status uses `fail`, not `failed`, while report counts/segments use `failed` as a normalized category.
Evidence sources:
  - ticket_text: DOC-E1 section 8.4 requires this semantic value.
  - current_code: `scanner/execution/grading.py` returns `fail`; `scanner/runners/daily.py::_build_execution_aware_report_payload` has metric key/segment `failed`; `scanner/universe/market_data_budget.py` uses gate status `failed`.
  - test: `tests/test_ticket26_execution_depth_analysis.py`; universe gate tests.
  - schema: no closed schema for `failed`; current fields are nullable/string or report keys.
  - artifact: daily report `execution_counts*` and `execution_aware_candidate_segments.confirmed_failed`; gate diagnostics may contain `failed` statuses.
  - schema_changes: `docs/SCHEMA_CHANGES.md` Ticket 24 says `failed` is visible in counts/segments but raw status is `fail`.
Status: partial
Notes: DOC-E2 should explicitly separate raw `fail` from report label `failed`.

Field: not_applicable
Claim: No active current diagnostics/report field value named exactly `not_applicable` was found in the mandatory scanned active paths. The code more commonly uses `null`, `not_evaluated`, `not_evaluable`, or reason/status-specific strings.
Evidence sources:
  - ticket_text: DOC-E1 section 8.4 requires this semantic value.
  - current_code: none found in active `scanner/output`, `scanner/runners`, `scanner/decision`, `scanner/execution`, `scanner/evaluation` paths by explicit search.
  - test: none found.
  - schema: none found.
  - artifact: none found.
  - schema_changes: none found for active report/diagnostics semantics.
Status: needs_review
Notes: DOC-E2 should not document `not_applicable` as current artifact value unless additional evidence appears.

## Report and diagnostics artifact paths

Field: report.json
Claim: Current run reports are written to `reports/runs/YYYY/MM/DD/<run_id>/report.json` and include `schema_version`, run identity, scan mode, bar ids, counts, symbol lists, manifest path, diagnostics path, no-op fields, and optional daily extras. Daily runs also copy the run report to `reports/daily/YYYY/MM/DD/report.json`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.5 requires artifact subject.
  - current_code: `scanner/output/report_builder.py::write_run_report`; `scanner/output/schema.py::RunReport`; `scanner/runners/daily.py`; `scanner/runners/intraday.py`.
  - test: `tests/test_ticket13_output_artifacts.py`; `tests/test_intraday_runner.py`.
  - schema: `scanner/output/schema.py::RunReport`.
  - artifact: `reports/runs/YYYY/MM/DD/<run_id>/report.json`; `reports/daily/YYYY/MM/DD/report.json`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.4 and ir1.5 changed report fields/semantics.
Status: confirmed
Notes: DOC-E2 should document run vs daily report copies and no-op behavior.

Field: symbol_diagnostics.jsonl.gz
Claim: Current diagnostics are written as gzip-compressed JSON Lines to `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`; each line is validated by `validate_diagnostics_record` before serialization.
Evidence sources:
  - ticket_text: DOC-E1 section 8.5 requires artifact subject.
  - current_code: `scanner/output/report_builder.py::write_run_report`; `scanner/output/diagnostics.py::write_symbol_diagnostics_jsonl_gz`; `scanner/output/schema.py::validate_diagnostics_record`.
  - test: `tests/test_ticket13_output_artifacts.py`; `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record`.
  - artifact: `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.1-ir1.5 entries.
Status: confirmed
Notes: DOC-E2 should state diagnostics are machine-oriented and retain rows that may be absent from actionable report lists.

Field: run manifest
Claim: Current run manifests are written under `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`. Report JSON stores the repository-relative manifest path. Intraday no-op writes a small manifest with run/bar identity and empty symbols.
Evidence sources:
  - ticket_text: DOC-E1 section 8.5 requires artifact subject.
  - current_code: `scanner/storage/snapshots.py::build_run_manifest_path`; `scanner/runners/daily.py::_persist_run_manifest`; `scanner/runners/intraday.py::_write_intraday_manifest`; `scanner/output/report_builder.py::RunReport.manifest_path`.
  - test: `tests/test_ticket14_snapshots.py`; `tests/test_independence_smoke_test.py`; `tests/test_intraday_runner.py`.
  - schema: `scanner/storage/snapshots.py` path validator; no full manifest payload schema found in active output schema.
  - artifact: `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`.
  - schema_changes: none found specific to current manifest payload.
Status: partial
Notes: Path is confirmed; payload schema appears partial/producer-specific and should be reviewed for DOC-E2/SNAPSHOTS.

Field: daily report
Claim: Daily runs traverse full daily runtime, write a run report and diagnostics, add universe/execution/Entry-Location extra blocks, then write the daily copy to `reports/daily/YYYY/MM/DD/report.json` and update daily/latest indexes.
Evidence sources:
  - ticket_text: DOC-E1 section 8.5 requires artifact subject.
  - current_code: `scanner/runners/daily.py::run_daily_scan`; `scanner/output/report_builder.py::write_daily_report`; `scanner/output/report_builder.py::_update_index_after_run`.
  - test: `tests/test_ticket15_daily_runner.py`; `tests/test_ticket13_output_artifacts.py`.
  - schema: `scanner/output/schema.py::RunReport` plus extra daily report blocks from daily runner.
  - artifact: `reports/daily/YYYY/MM/DD/report.json`; `reports/index/latest_daily.json`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 changed final actionable lists and operational counts.
Status: confirmed
Notes: DOC-E2 should document daily extras separately from base RunReport fields.

Field: intraday report
Claim: Intraday reports use the same `write_run_report` path with `scan_mode="intraday"`; no-op reports may contain zero diagnostics and set `no_op=true`/`no_op_reason`, while diagnostics-only intraday runs do not overwrite candidate-oriented latest files unless relevant candidate lists were intentionally produced.
Evidence sources:
  - ticket_text: DOC-E1 section 8.5 requires artifact subject.
  - current_code: `scanner/runners/intraday.py::_write_intraday_noop_report`; `scanner/output/report_builder.py::write_run_report`; `scanner/output/report_builder.py::_update_index_after_run`.
  - test: `tests/test_intraday_runner.py`; `tests/test_ticket13_output_artifacts.py`.
  - schema: `scanner/output/schema.py::RunReport`; no-op fields are extra report fields.
  - artifact: `reports/runs/YYYY/MM/DD/<run_id>/report.json`; `reports/index/latest_intraday.json`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.4 no-op report metadata and candidate-effective latest indexes.
Status: confirmed
Notes: DOC-E2 should distinguish `latest.json`, `latest_intraday.json`, `latest_daily.json`, and candidate-specific latest files.

Field: snapshot run path
Claim: Canonical run snapshot/manifest placement is `snapshots/runs/YYYY/MM/DD/<run_id>/`, derived from `daily_bar_id`; reports live under `reports/runs/...` and refer back to snapshot manifests.
Evidence sources:
  - ticket_text: DOC-E1 section 8.5 requires artifact subject.
  - current_code: `scanner/storage/snapshots.py::build_run_snapshot_dir` and `build_run_manifest_path`; `scanner/evaluation/replay.py::_resolve_diag_path` maps snapshot manifests to report diagnostics.
  - test: `tests/test_ticket14_snapshots.py`; `tests/test_independence_smoke_test.py`.
  - schema: `scanner/storage/snapshots.py` path validators.
  - artifact: `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`; paired `reports/runs/.../symbol_diagnostics.jsonl.gz`.
  - schema_changes: none found specific to path; `docs/canonical/SNAPSHOTS.md` documents placement.
Status: confirmed
Notes: DOC-E2/REPORTS should explain reports/snapshots split; SNAPSHOTS already documents placement but not report-field semantics.

## Schema version / ir1.5+ context

Field: schema_version
Claim: Current output `schema_version` is `ir1.5`, defined in `scanner/output/schema.py::SCHEMA_VERSION`, emitted by `RunReport.to_dict`, defaulted into diagnostics when absent, and accepted for diagnostics alongside older `ir1.0`-`ir1.4` versions.
Evidence sources:
  - ticket_text: DOC-E1 section 8.6 requires subject.
  - current_code: `scanner/output/schema.py::SCHEMA_VERSION`; `scanner/output/schema.py::ACCEPTED_DIAGNOSTICS_SCHEMA_VERSIONS`; `scanner/output/schema.py::RunReport.to_dict`; `scanner/output/schema.py::validate_diagnostics_record`.
  - test: `tests/test_ticket13_output_artifacts.py`; schema-version tests in output/diagnostics suites.
  - schema: `scanner/output/schema.py`.
  - artifact: `report.json`; `symbol_diagnostics.jsonl.gz`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 entry and prior version entries.
Status: confirmed
Notes: DOC-E2 should distinguish output schema version string from SQLite integer `schema_version` in `run_metadata`.

Field: ir1.5
Claim: `ir1.5` specifically adds operational tradeability and stable/cash candidate exclusion semantics to reports/diagnostics/latest indexes, while preserving `is_tradeable_candidate` as audit signal.
Evidence sources:
  - ticket_text: DOC-E1 section 8.6 requires subject.
  - current_code: `scanner/output/schema.py::SCHEMA_VERSION`; `scanner/output/schema.py::is_operational_trade_candidate`; `scanner/output/report_builder.py::write_run_report`; `scanner/runners/daily.py`.
  - test: `tests/test_q1_q2_operational_tradeability.py`; `tests/test_ticket28_operational_tradeability.py`; `tests/test_ticket30_operational_tradeability_eval.py`.
  - schema: `scanner/output/schema.py`.
  - artifact: `symbol_diagnostics.jsonl.gz`, `report.json`, candidate latest indexes.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 entry.
Status: confirmed
Notes: DOC-E2 should make `is_operational_trade_candidate` the `ir1.5` consumer-facing label.

Field: ir1.5+
Claim: For `ir1.5+`, T30 and operative consumers should prefer `is_operational_trade_candidate`; compatibility readers may derive it from `is_tradeable_candidate AND NOT candidate_excluded` when native field is absent, and should record source/compat status where evaluation code does so.
Evidence sources:
  - ticket_text: DOC-E1 section 8.6 requires subject.
  - current_code: `scanner/evaluation/replay.py::_operational_tradeability`; `scanner/evaluation/replay.py::reconstruct_event_timeline`; `scanner/evaluation/forward_returns.py` metric context fields.
  - test: `tests/test_ticket30_operational_tradeability_eval.py`.
  - schema: `scanner/output/schema.py` defines current version and formula.
  - artifact: evaluation `event_timeline.jsonl`; `signal_event_metrics.parquet`; diagnostics.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 consumer impact.
Status: confirmed
Notes: DOC-E2 should document native vs compat-backfilled source fields (`operational_tradeability_compat`, `operational_tradeability_source`) in evaluation outputs.

## Evaluation / T30 output fields

Field: forward_return
Claim: No generic field named exactly `forward_return` is emitted by active evaluation. Active forward-return metrics are horizon-specific fields named `forward_return_<h>d_pct` for `h in {1,3,5,10}`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::HORIZONS`; `scanner/evaluation/forward_returns.py::build_signal_metrics`.
  - test: `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: none found as standalone schema; generated DataFrame columns are code-defined.
  - artifact: `evaluation/exports/signal_event_metrics.parquet`.
  - schema_changes: none found for exact `forward_return` field.
Status: partial
Notes: Exact-name mismatch; document actual horizon-specific names in future evaluation docs.

Field: forward_return_horizon
Claim: No field named exactly `forward_return_horizon` was found. Active evaluation encodes horizon in column names (`forward_return_1d_pct`, etc.) rather than a separate horizon column.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::HORIZONS`; per-horizon loop builds column names.
  - test: `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: none found.
  - artifact: `evaluation/exports/signal_event_metrics.parquet`.
  - schema_changes: none found.
Status: partial
Notes: Add field-name mismatch to DOC-E2/future evaluation docs.

Field: forward_return_7d
Claim: No active field `forward_return_7d` or `forward_return_7d_pct` was found. Active horizons are 1, 3, 5, and 10 days.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::HORIZONS = (1, 3, 5, 10)`.
  - test: `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: none found.
  - artifact: none found for 7d field.
  - schema_changes: none found.
Status: needs_review
Notes: Expected T30-v2 naming differs from implementation.

Field: forward_return_14d
Claim: No active field `forward_return_14d` or `forward_return_14d_pct` was found. Active horizons are 1, 3, 5, and 10 days.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::HORIZONS = (1, 3, 5, 10)`.
  - test: `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: none found.
  - artifact: none found for 14d field.
  - schema_changes: none found.
Status: needs_review
Notes: Expected T30-v2 naming differs from implementation.

Field: forward_return_30d
Claim: No active field `forward_return_30d` or `forward_return_30d_pct` was found. Active horizons are 1, 3, 5, and 10 days.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::HORIZONS = (1, 3, 5, 10)`.
  - test: `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: none found.
  - artifact: none found for 30d field.
  - schema_changes: none found.
Status: needs_review
Notes: Expected T30-v2 naming differs from implementation.

Field: mfe
Claim: No generic field named exactly `mfe` is emitted by active `scanner/evaluation/*`. Active `scanner/evaluation/*` fields are `mfe_<h>d_pct` for horizons 1, 3, 5, and 10; linked exporter dependency `scanner.backtest.e2_model` uses `mfe_pct` inside the active executable legacy snapshot evaluation export tooling cluster.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::build_signal_metrics`; `scanner/backtest/e2_model.py` uses `mfe_pct` as a linked dependency in the active executable legacy snapshot evaluation export tooling cluster, not in active `scanner/evaluation/*` infrastructure.
  - test: `tests/test_ticket30_forward_return_evaluation.py`; legacy backtest tests where applicable.
  - schema: none found.
  - artifact: active `evaluation/exports/signal_event_metrics.parquet`; exporter-cluster artifacts are unresolved active executable legacy snapshot evaluation export tooling outputs, separate from active `scanner/evaluation/*` infrastructure.
  - schema_changes: none found for exact generic field.
Status: partial
Notes: Document active horizon-specific names; if `mfe_pct` is mentioned, tie it to the unresolved exporter/global-ranking/e2-model cluster rather than marking it inactive legacy-only.

Field: mae
Claim: No generic field named exactly `mae` is emitted by active `scanner/evaluation/*`. Active `scanner/evaluation/*` fields are `mae_<h>d_pct` for horizons 1, 3, 5, and 10; linked exporter dependency `scanner.backtest.e2_model` uses `mae_pct` inside the active executable legacy snapshot evaluation export tooling cluster.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::build_signal_metrics`; `scanner/backtest/e2_model.py` uses `mae_pct` as a linked dependency in the active executable legacy snapshot evaluation export tooling cluster, not in active `scanner/evaluation/*` infrastructure.
  - test: `tests/test_ticket30_forward_return_evaluation.py`; legacy backtest tests where applicable.
  - schema: none found.
  - artifact: active `evaluation/exports/signal_event_metrics.parquet`; exporter-cluster artifacts are unresolved active executable legacy snapshot evaluation export tooling outputs, separate from active `scanner/evaluation/*` infrastructure.
  - schema_changes: none found for exact generic field.
Status: partial
Notes: Document active horizon-specific names; if `mae_pct` is mentioned, tie it to the unresolved exporter/global-ranking/e2-model cluster rather than marking it inactive legacy-only.

Field: segment
Claim: Active daily reports use multiple segment blocks (`candidate_segments`, `execution_aware_candidate_segments`, `entry_location_candidate_segments`). Active evaluation outputs do not appear to emit a generic `segment` field in signal metrics.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/runners/daily.py::_build_ticket23_report_payload`, `_build_execution_aware_report_payload`; `scanner/decision/entry_location.py::build_entry_location_report_segments`; `scanner/evaluation/forward_returns.py` metric context fields.
  - test: `tests/test_ticket13_output_artifacts.py`; `tests/test_entry_location_t_el2.py`; `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: report extras are not in `RunReport` dataclass; diagnostics schema has no generic `segment` field.
  - artifact: daily `report.json` segment blocks; not active evaluation row field.
  - schema_changes: `docs/SCHEMA_CHANGES.md` Ticket 23/24 entries mention segment blocks.
Status: partial
Notes: DOC-E2 should define segment blocks by artifact, not as a single universal field.

Field: basket
Claim: No active field named exactly `basket` was found in current report/diagnostics/evaluation outputs.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: none found in active output/evaluation paths by explicit search.
  - test: none found.
  - schema: none found.
  - artifact: none found.
  - schema_changes: none found.
Status: needs_review
Notes: Do not document as implemented without additional evidence.

Field: entry_reference
Claim: No active field named exactly `entry_reference` was found. Active evaluation uses `reference_price`, `reference_price_status`, `reference_price_source`, and `reference_price_reason` derived from event/persisted close data.
Evidence sources:
  - ticket_text: DOC-E1 section 8.7 expected subject.
  - current_code: `scanner/evaluation/forward_returns.py::_reference_price_from_event`; `scanner/evaluation/forward_returns.py::build_signal_metrics`.
  - test: `tests/test_ticket30_forward_return_evaluation.py`.
  - schema: none found as standalone schema.
  - artifact: `evaluation/exports/signal_event_metrics.parquet`.
  - schema_changes: none found for exact field.
Status: partial
Notes: Expected-name mismatch; document active reference-price fields in future evaluation docs.

Field: evaluation_dataset
Claim: The active `scanner/evaluation/*` export path writes replay and metric artifacts under `evaluation/replay/` and `evaluation/exports/`. Separately, `scanner/tools/export_evaluation_dataset.py` with linked dependencies `scanner.pipeline.global_ranking.compute_global_top20` and `scanner.backtest.e2_model` is active executable legacy snapshot evaluation export tooling, but not active `scanner/evaluation/*` infrastructure; final documentation treatment remains unresolved.
Evidence sources:
  - ticket_text: DOC-E1 sections 6 and 10 instruct active `scanner/evaluation/*` vs exporter boundary.
  - current_code: `scanner/evaluation/dataset_export.py::run_evaluation_export`; `scanner/evaluation/replay.py`; `scanner/evaluation/forward_returns.py`; exporter cluster `scanner/tools/export_evaluation_dataset.py`, `scanner.pipeline.global_ranking.compute_global_top20`, and `scanner.backtest.e2_model`.
  - test: `tests/test_ticket30_forward_return_evaluation.py`; `tests/test_evaluation_dataset_export.py` for executable exporter-tool behavior.
  - schema: no standalone evaluation dataset schema found.
  - artifact: active `evaluation/replay/event_timeline.jsonl`, `evaluation/replay/replay_manifest.json`, `evaluation/replay/replay_diagnostics.json`, `evaluation/exports/signal_event_metrics.parquet`, `terminal_event_timeline.parquet`, `transition_lead_times.parquet`, `evaluation_summary.json`; exporter-cluster output remains a separate legacy snapshot evaluation export contract candidate.
  - schema_changes: none found as full evaluation schema.
Status: partial
Notes: DOC-E2 should document or defer the exporter/global-ranking/e2-model cluster separately from active `scanner/evaluation/*`; do not describe it as inactive legacy-only or as active Daily/Intraday runtime/evaluation infrastructure.


Field: legacy snapshot evaluation export path
Claim: `scanner/tools/export_evaluation_dataset.py`, `scanner.pipeline.global_ranking.compute_global_top20`, and `scanner.backtest.e2_model` form active executable legacy snapshot evaluation export tooling, but not active `scanner/evaluation/*` infrastructure and not active Daily/Intraday scanner runtime. CODE-FU-B or a dedicated evaluation-doc decision should classify whether to document this as a separate contract, extract helpers, or retire it.
Evidence sources:
  - ticket_text: DOC-E1 sections 6 and 10 mention the exporter/backtest paths and instruct boundary qualification.
  - current_code: `scanner/tools/export_evaluation_dataset.py` imports/calls `scanner.pipeline.global_ranking.compute_global_top20` and `scanner.backtest.e2_model` helpers.
  - test: `tests/test_evaluation_dataset_export.py`; CODE-A1/CODE-A2 inventories also identify executable tests/tooling.
  - schema: no standalone schema found for this exporter cluster.
  - artifact: caller-supplied exporter output path; distinct from active `evaluation/replay/*` and `evaluation/exports/*` artifacts produced by `scanner/evaluation/dataset_export.py`.
  - schema_changes: none found as full exporter schema.
Status: partial
Notes: This block preserves the review nuance: the cluster is executable tooling with unresolved classification, not current `scanner/evaluation/*` infrastructure and not inactive legacy-only.

## Consumer contract findings

Field: daily report consumer
Claim: Daily report consumers should read `reports/daily/YYYY/MM/DD/report.json` or `reports/index/latest_daily.json` for the latest daily candidate-producing report; for `ir1.5+`, actionable candidate lists already exclude `candidate_excluded=true` in confirmed/early/watchlist buckets, and operational row-level consumers should prefer `is_operational_trade_candidate` where diagnostics/report segments expose it.
Evidence sources:
  - ticket_text: DOC-E1 section 8.8 requires consumer concept.
  - current_code: `scanner/output/report_builder.py::write_daily_report`; `scanner/output/report_builder.py::_update_index_after_run`; `scanner/output/report_builder.py::write_run_report` candidate exclusion filtering.
  - test: `tests/test_ticket13_output_artifacts.py`; `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py::RunReport`.
  - artifact: `reports/daily/.../report.json`, `reports/index/latest_daily.json`, `reports/index/latest_confirmed_candidates.json`, `reports/index/latest_watchlist.json`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.4/ir1.5 consumer notes.
Status: confirmed
Notes: DOC-E2 should describe daily vs latest index selection.

Field: diagnostics consumer
Claim: Diagnostics consumers should read `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz` via the path in `report.json`/latest indexes, treat diagnostics as row-level machine evidence, and prefer top-level `candidate_excluded` and `is_operational_trade_candidate` for `ir1.5+`.
Evidence sources:
  - ticket_text: DOC-E1 section 8.8 requires consumer concept.
  - current_code: `scanner/output/report_builder.py`; `scanner/output/diagnostics.py`; `scanner/output/schema.py`; `scanner/evaluation/replay.py::_resolve_diag_path`.
  - test: `tests/test_ticket13_output_artifacts.py`; `tests/test_ticket30_operational_tradeability_eval.py`.
  - schema: `scanner/output/schema.py::validate_diagnostics_record`.
  - artifact: `symbol_diagnostics.jsonl.gz`; `report.json.diagnostics_path`; `reports/index/latest_paths.json`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.1-ir1.5.
Status: confirmed
Notes: DOC-E2 should explain older accepted diagnostics versions and absent optional blocks.

Field: T30 consumer
Claim: Active T30/evaluation consumers should use `scanner/evaluation/*` outputs; for tradeability they should prefer `is_operational_trade_candidate`/source fields, and for returns use horizon-specific `forward_return_<h>d_pct`, `mfe_<h>d_pct`, and `mae_<h>d_pct` where `h` is currently 1/3/5/10.
Evidence sources:
  - ticket_text: DOC-E1 section 8.8 requires consumer concept.
  - current_code: `scanner/evaluation/replay.py`; `scanner/evaluation/forward_returns.py`; `scanner/evaluation/dataset_export.py`.
  - test: `tests/test_ticket30_forward_return_evaluation.py`; `tests/test_ticket30_operational_tradeability_eval.py`.
  - schema: no standalone schema found; DataFrame columns defined in code.
  - artifact: `evaluation/replay/event_timeline.jsonl`; `evaluation/exports/signal_event_metrics.parquet`; `evaluation/exports/evaluation_summary.json`.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 T30 consumer note.
Status: confirmed
Notes: Recommend future evaluation docs for exact column schema.

Field: Shadow-Live analysis consumer
Claim: Shadow-Live analysis appears to consume current reports/diagnostics/evaluation outputs conceptually, but no single explicit `Shadow-Live analysis consumer` contract file or schema was found in the scanned active paths.
Evidence sources:
  - ticket_text: DOC-E1 section 8.8 requires consumer concept.
  - current_code: `scanner/evaluation/*` active analysis outputs; no dedicated Shadow-Live consumer module found by exact search.
  - test: none found for exact consumer name.
  - schema: none found.
  - artifact: likely `reports/*` and `evaluation/*`, but no explicit artifact contract found.
  - schema_changes: none found for exact consumer.
Status: partial
Notes: DOC-E2 should avoid over-specific Shadow-Live consumer guidance unless product owner confirms artifact contract.

Field: operational candidate selection
Claim: Operational candidate selection for `ir1.5+` excludes `candidate_excluded=true` from actionable confirmed/early/watchlist report lists and should use `is_operational_trade_candidate` as row-level tradeability label where a diagnostics/evaluation row is consumed.
Evidence sources:
  - ticket_text: DOC-E1 section 8.8 requires consumer concept.
  - current_code: `scanner/output/report_builder.py::write_run_report`; `scanner/runners/daily.py` filters ranked inputs for actionable excluded categories; `scanner/output/schema.py::is_operational_trade_candidate`.
  - test: `tests/test_q1_q2_operational_tradeability.py`.
  - schema: `scanner/output/schema.py`.
  - artifact: `report.json` candidate lists; `latest_confirmed_candidates.json`; `latest_watchlist.json`; diagnostics/evaluation row fields.
  - schema_changes: `docs/SCHEMA_CHANGES.md` ir1.5 consumer impact.
Status: confirmed
Notes: DOC-E2 should separate list-level exclusion from row-level labels.

## Documentation gaps for DOC-E2

| Target doc | Gap type | Subject | Evidence status | Recommended DOC-E2 action |
|---|---|---|---|---|
| `docs/canonical/DATA_MODEL.md` | missing | Output `schema_version` string vs SQLite integer `schema_version` | confirmed | Add explicit distinction or cross-reference to REPORTS/evaluation docs; avoid conflating SQLite schema integer with report/diagnostics `ir*` strings. |
| `docs/canonical/DATA_MODEL.md` | missing | `candidate_excluded`, `is_tradeable_candidate`, `is_operational_trade_candidate` | confirmed | Add concise current-state field semantics and nested/top-level relationship, or point to REPORTS if DATA_MODEL remains persistence-focused. |
| `docs/canonical/DATA_MODEL.md` | missing | Execution fields (`execution_status_raw`, `execution_size_class`, `is_reduced_size_eligible`, `execution_grade_effective`, `execution_grade_t16`) | confirmed/partial | Document actual serialized names and compatibility-null `execution_grade_t16`; avoid expected names not in code. |
| `docs/canonical/DATA_MODEL.md` | missing | Entry-Location nested block | confirmed/partial | Document actual `entry_location_status`, `entry_action_hint`, reason primary/codes, inputs used, warning flag; do not invent bucket/score fields. |
| `docs/canonical/REPORTS.md` | stale/partial | Run report vs daily report vs intraday no-op behavior | confirmed | Update path/consumer guidance, including `reports/runs`, `reports/daily`, latest indexes, and candidate-effective latest semantics. |
| `docs/canonical/REPORTS.md` | missing | Diagnostics artifact path and purpose | confirmed | Add `symbol_diagnostics.jsonl.gz` path, JSONL gzip format, row-level machine-consumer role, and relation to report `diagnostics_path`. |
| `docs/canonical/REPORTS.md` | missing | Daily extra report blocks | confirmed | Document `universe_classification`, `candidate_segments`, `execution_aware_*`, and `entry_location_candidate_segments` at summary level. |
| `docs/canonical/REPORTS.md` | missing | `ir1.5+` consumer guidance | confirmed | State that operational/T30 consumers prefer `is_operational_trade_candidate`; `is_tradeable_candidate` remains audit signal. |
| `docs/canonical/SNAPSHOTS.md` | partial | Snapshot/report split and diagnostics lookup | confirmed | Existing placement is mostly covered; add cross-reference that reports/diagnostics live under `reports/runs` while manifests live under `snapshots/runs`. |
| `docs/SCHEMA_CHANGES.md` | partial | Full field catalog | confirmed | Keep as change log; do not rewrite as data model. Add future entries only for schema changes. |
| future evaluation documentation | missing | Active T30/evaluation output schema | partial/needs_review | Create dedicated evaluation output schema for `event_timeline.jsonl`, `signal_event_metrics.parquet`, terminal/transition parquet, summary/manifest/diagnostics JSON. Separately document or defer the exporter/global-ranking/e2-model cluster. |
| future evaluation documentation | contradicted | Expected 7/14/30d fields vs implemented 1/3/5/10d fields | needs_review | Product owner should decide whether docs follow implementation or implementation should add T30-v2 horizons. |
| future evaluation documentation | missing | Shadow-Live analysis consumer | partial | Define explicit consumer contract or state it consumes standard reports/diagnostics/evaluation outputs only. |
| future evaluation documentation | partial | `scanner/tools/export_evaluation_dataset.py`, `scanner.pipeline.global_ranking.compute_global_top20`, `scanner.backtest.e2_model` | partial | Do not omit the exporter entirely and do not describe its linked dependencies as broadly active runtime/evaluation infrastructure. Document it separately as active executable legacy snapshot evaluation export tooling, but not active `scanner/evaluation/*`, or defer final treatment to CODE-FU-B / a future evaluation documentation ticket. Clarify that `compute_global_top20` and `e2_model` are linked to this exporter path, not active Daily/Intraday runtime. |

## Conflicts and uncertainties

| Subject | Conflict / uncertainty | Evidence refs | Suggested resolution path |
|---|---|---|---|
| `execution_status` vs `execution_status_raw` | Ticket expected subject uses `execution_status`, but active artifacts use `execution_status_raw`; internal contract has `execution_status`. | `scanner/execution/grading.py`, `scanner/output/schema.py`, `scanner/runners/daily.py`, `tests/test_ticket16_execution_adapter.py` | DOC-E2 should document `execution_status_raw` as serialized field and mention internal `execution_status` only if needed. |
| `entry_location_bucket` | Expected field not found; actual field is `entry_location.entry_location_status`. | `scanner/decision/entry_location.py`, `scanner/output/schema.py`, `docs/SCHEMA_CHANGES.md` ir1.3 | Use actual field name; add alias note only as historical/expected terminology. |
| `entry_location_reason` | Expected single field not found; implementation uses primary plus reason-code list. | `scanner/decision/entry_location.py`, `scanner/output/schema.py` | Document `entry_location_reason_primary` and `entry_location_reason_codes`. |
| `entry_location_flags` | Expected grouped field not found; closest flag is `range_high_proximity_warning`. | `scanner/decision/entry_location.py`, `scanner/output/schema.py` | Document actual flag; do not create grouped flag concept unless future schema adds it. |
| `entry_location_score` | No implementation evidence found. | explicit searches in active paths | Mark not implemented or remove from DOC-E2 unless product owner confirms future need. |
| `buy_now` / `avoid_chase` | Expected concepts differ from actual values `buy_now_candidate` and `avoid_chasing`. | `scanner/decision/entry_location.py`, `scanner/output/schema.py` | Document exact values; optionally include plain-English aliases. |
| `failed` vs `fail` | Raw execution status is `fail`; report labels use `failed`. | `scanner/execution/grading.py`, `scanner/runners/daily.py`, `docs/SCHEMA_CHANGES.md` Ticket 24 | DOC-E2 should define raw-vs-summary value mapping. |
| `not_applicable` | Required semantic value has no active evidence. | explicit searches in active paths | Human review; avoid claiming support. |
| `forward_return_7d/14d/30d` | Expected T30-v2 subjects are not active; active horizons are 1/3/5/10 days and include `_pct` suffix. | `scanner/evaluation/forward_returns.py::HORIZONS`, `tests/test_ticket30_forward_return_evaluation.py` | Product decision: update docs to current horizons or create implementation ticket for 7/14/30. |
| Generic `forward_return`, `mfe`, `mae` | Active `scanner/evaluation/*` implementation uses horizon-specific fields; `scanner.backtest.e2_model` uses `mfe_pct`/`mae_pct` inside the active executable legacy snapshot evaluation export tooling cluster. | `scanner/evaluation/forward_returns.py`, `scanner/backtest/e2_model.py`, `docs/audit/active_code_path_inventory_v0.md`, `docs/audit/legacy_pipeline_boundary_review_v0.md`, legacy boundary decision note | Document active fields; tie backtest names to the exporter/global-ranking/e2-model cluster and defer final classification to CODE-FU-B rather than labeling them inactive legacy-only. |
| `basket` | No active field found. | explicit searches in active paths | Do not document as implemented; product owner should define if needed. |
| `entry_reference` | Expected field differs from active `reference_price*` fields. | `scanner/evaluation/forward_returns.py` | Document actual reference-price fields in future evaluation documentation. |
| Run manifest payload schema | Path is confirmed, but full manifest payload schema is producer-specific/partial in scanned docs. | `scanner/storage/snapshots.py`, `scanner/runners/daily.py`, `scanner/runners/intraday.py`, `docs/canonical/SNAPSHOTS.md` | DOC-E2 or SNAPSHOTS follow-up should define manifest payload fields or explicitly defer. |
| Shadow-Live analysis consumer | Consumer concept is requested but no explicit active consumer contract found. | `scanner/evaluation/*`, report/diagnostics paths | Product owner should specify whether Shadow-Live consumes daily reports, diagnostics, evaluation outputs, or a separate contract. |
| `scanner/tools/export_evaluation_dataset.py`, `scanner.pipeline.global_ranking.compute_global_top20`, `scanner.backtest.e2_model` | CODE-A1/CODE-A2 identify the exporter as active executable evaluation tooling with legacy-named dependencies, while DOC-D / the boundary decision distinguish this path from active `scanner/evaluation/*` infrastructure. The exporter should not be documented as current `scanner/evaluation/*`, but the exporter plus linked dependencies should also not be de-canonized as inactive legacy-only without a follow-up decision. | `docs/audit/active_code_path_inventory_v0.md`; `docs/audit/legacy_pipeline_boundary_review_v0.md`; `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md`; current exporter code; `scanner.pipeline.global_ranking.compute_global_top20`; `scanner.backtest.e2_model` | DOC-E2 should treat this as a separate legacy snapshot evaluation export contract or defer final classification to CODE-FU-B / a dedicated evaluation-doc ticket. |
