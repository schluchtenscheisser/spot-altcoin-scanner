# Documentation Cleanup Closure Review v0

## Purpose

This document is a non-authoritative audit and triage review for the DOC-A through DOC-E2 documentation cleanup workstream. It records closure findings, unresolved-boundary status, and recommended follow-up sequencing only. It is not canonical documentation, does not replace `docs/canonical/*`, and does not close or rewrite any item in `docs/canonical/open_questions.md`.

DOC-F0 intentionally does not update canonical documentation. Its purpose is to reduce the next-step decision surface after DOC-E2 by separating already-clean areas from items that still need code-boundary work, small documentation navigation cleanup, future Evaluation/T30 documentation, or human decisions.

## Source coverage summary

| Source group | Files inspected | Coverage result | Notes |
|---|---|---|---|
| Canonical authority/navigation | `docs/canonical/AUTHORITY.md`, `docs/canonical/INDEX.md` | Covered | Authority hierarchy is repo-reality-first; `INDEX.md` is the role/navigation index. |
| Current-state runtime docs | `docs/canonical/ARCHITECTURE.md`, `docs/canonical/RUNTIME_AND_OPERATIONS.md` | Covered | Daily/Intraday runtime architecture is documented with explicit compatibility boundaries. |
| Data/report/snapshot docs | `docs/canonical/DATA_MODEL.md`, `docs/canonical/REPORTS.md`, `docs/canonical/SNAPSHOTS.md`, `docs/SCHEMA_CHANGES.md` | Covered | DATA_MODEL/REPORTS were updated by DOC-E2; SNAPSHOTS remains narrower and only indirectly aligned; SCHEMA_CHANGES remains an evidence/change log. |
| Open-question tracking | `docs/canonical/open_questions.md` | Covered | Active questions Q3-Q11, Q13, and Q14 were triaged below; resolved reference items were checked only for context. |
| Audit inputs | `docs/audit/documentation_inventory_v0.md`, `docs/audit/active_code_path_inventory_v0.md`, `docs/audit/legacy_pipeline_boundary_review_v0.md`, `docs/audit/data_reports_evidence_inventory_v0.md` | Covered | Used as non-authoritative evidence/inventory inputs for DOC-A, CODE-boundary, and DOC-E1/E2 status. |
| Decision input | `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md` | Covered | Confirms the legacy snapshot exporter cluster and CODE-FU-B follow-up map. |
| Optional sources | Current code/tests were not re-audited beyond the evidence already captured in required inputs. | Not needed for DOC-F0 | DOC-F0 is a closure review, not a fresh code audit; no new implementation facts were introduced. |

## DOC-A to DOC-E2 completion summary

| Workstream step | Primary output / files | Current status | Residual concerns |
|---|---|---|---|
| DOC-A | `docs/audit/documentation_inventory_v0.md` | complete | Inventory role was correctly non-authoritative and identified authority/schema/navigation conflicts for later cleanup. |
| DOC-B | `docs/canonical/AUTHORITY.md`, `INDEX.md`, workflow docs | complete | Authority model is materially cleaner; a small navigation clarification around `docs/SCHEMA_CHANGES.md` may still be useful, but the model itself does not need reopening. |
| DOC-C | ticket template / preflight / workflow guard | complete | Documentation-impact process guard appears in place; no DOC-F0 follow-up required unless future tickets reveal process drift. |
| DOC-D | `ARCHITECTURE.md`, `RUNTIME_AND_OPERATIONS.md` | complete | Runtime/current-state docs preserve Daily/Intraday boundaries and legacy compatibility caveats; CODE-FU-B remains outside DOC-D. |
| DOC-E1 | `docs/audit/data_reports_evidence_inventory_v0.md` | complete | Evidence inventory remains the key basis for unresolved field validation items, especially Q14. |
| DOC-E2 | `DATA_MODEL.md`, `REPORTS.md`, `open_questions.md` | partial | DATA_MODEL/REPORTS are mostly clean for current report/diagnostics artifacts, but DOC-E2 intentionally left Evaluation/T30 schemas, legacy exporter fate, and several evidence items unresolved. |

## Canonical documentation state after DOC-E2

| Canonical doc | Current role after cleanup | Apparent status | Remaining action needed? | Notes |
|---|---|---|---|---|
| `docs/canonical/AUTHORITY.md` | Central documentation authority and precedence model | clean | No immediate action | Explicitly states current repository reality wins and `SCHEMA_CHANGES.md` is evidence, not a full model. |
| `docs/canonical/INDEX.md` | Role/navigation index | mostly_clean | small_doc_patch | Active vs legacy-reference split is clear, but navigation could better point readers from `SCHEMA_CHANGES.md` to DATA_MODEL/REPORTS/SNAPSHOTS and clarify its non-replacement role. |
| `docs/canonical/ARCHITECTURE.md` | Current-state module/runtime architecture map | clean | No immediate action | Correctly avoids making field-level or Evaluation/T30 schema claims. |
| `docs/canonical/RUNTIME_AND_OPERATIONS.md` | Runtime and operations contract | clean | No immediate action | Daily/Intraday operation and workflow boundaries are documented; output semantics are delegated to data/report/snapshot docs. |
| `docs/canonical/DATA_MODEL.md` | Current report/diagnostics data model plus persistence foundation | mostly_clean | future_evaluation_doc after CODE-FU-B | Covers current serialized report/diagnostics contracts and explicitly excludes Evaluation/T30 output schemas. |
| `docs/canonical/REPORTS.md` | Current report contract and report-consumer guidance | mostly_clean | future_evaluation_doc after CODE-FU-B | Correctly preserves the Evaluation/T30 and legacy exporter boundary; remaining uncertainty is outside its current scope. |
| `docs/canonical/SNAPSHOTS.md` | Snapshot placement/history lifecycle and limited T30 OHLCV artifact note | partial | dedicated_doc_ticket | Useful and not obviously contradictory, but narrower than post-DOC-E2 report/data docs and not independently updated for current replay/evaluation/export boundaries. |
| `docs/canonical/open_questions.md` | Active unresolved-decision tracker | mostly_clean | small_doc_patch later, not in DOC-F0 | Valid active questions remain; Q14 was newly added by DOC-E2 and should stay until evidence validation occurs. |
| `docs/SCHEMA_CHANGES.md` | Schema/output change evidence log | mostly_clean | small_doc_patch in navigation only | Should remain evidence/change history. Do not rewrite it into a full data model or report contract. |

## Open questions triage

| Open question / subject | Source / section | Current relevance after DOC-A..E2 | Classification | Recommended action | Notes |
|---|---|---|---|---|---|
| `distance_to_range_high_pct_abs` formula and boundary | Q3 | Still relevant as an Entry-Location calibration/spec question; DATA_MODEL documents current auxiliary usage but does not define a full formula. | `follow_up_ticket_needed` | Future calibration/spec ticket, not broad docs cleanup | Keep auxiliary-warning boundary until formula, anchor, lookback, owner, and distinction from Q13 are decided. |
| Intraday diagnostics / no-op and future promotion diagnostics | Q4 | Partly resolved for no-op semantics; productive promotion diagnostics and canonical no-op reason values remain open. | `follow_up_ticket_needed` | Dedicated Intraday Promotion diagnostics contract ticket when promotion expansion resumes | Does not block DOC cleanup, but should not be silently generalized from valid no-op emptiness. |
| `execution_size_class = "full"` two meanings | Q5 | Still valid but current docs explain the consumer rule to read it with `execution_status_raw`. | `defer` | Defer to future schema cleanup if a version bump is warranted | No evidence of current misbehavior; not a DOC-F0 blocker. |
| `is_reduced_size_eligible` misleading name | Q6 | Still valid as a naming/schema-cleanup concern; current semantics are documented. | `defer` | Defer to future schema cleanup with migration plan | Rename requires schema bump and backward compatibility handling. |
| Smoke-test vs full-universe intraday behavior | Q7 | Still an evidence/repro question, not resolved by documentation cleanup. | `follow_up_ticket_needed` | Verification ticket if current Shadow-Live evidence still shows divergence | Close only after checking current artifacts. |
| `candidate_excluded_symbol_count` in `candidate_segments` | Q8 | Still a concrete report-contract validation item. | `follow_up_ticket_needed` | Small report-artifact validation/bugfix ticket | If current `ir1.5+` reports include an integer, then future cleanup can mark it resolved; DOC-F0 did not mutate open questions. |
| Non-ASCII symbol eligibility/classification | Q9 | Still a business/design policy decision. | `needs_human_decision` | Human decision on flag-first vs override-map vs operational eligibility impact | Do not introduce a hard ASCII filter through docs cleanup. |
| `tokenized_stock_or_etf` higher `unknown_execution` rate | Q10 | Still observational and evidence-dependent. | `defer` | Defer until reproduced across newer runs | No immediate rule/config change recommended. |
| `ARBUSDT` execution attempted without valid decision bucket | Q11 | Still an anomaly verification question. | `follow_up_ticket_needed` | Low-priority diagnostics/execution-adapter verification ticket | There is duplicated wording in the source question, but this audit does not edit `open_questions.md`. |
| `dist_to_base_mid_pct` formula | Q13 | Still relevant because formula/owner are unresolved and related to Q3. | `needs_human_decision` | Human/spec decision before implementation or documentation | Should be resolved together with or explicitly distinguished from Q3. |
| DOC-E2 evidence items: `execution_grade`, `execution_notional_usdt`, `entry_location_score`, `not_applicable`, `basket` | Q14 | Newly added DOC-E2 follow-up remains valid; DATA_MODEL/REPORTS document alternatives/boundaries but do not validate these as active contracts. | `follow_up_ticket_needed` | Focused evidence-validation doc/code-audit ticket; route `basket` through future Evaluation/T30 docs after CODE-FU-B | This is the main DOC-E2 residual data/report cleanup item. |
| Q1, Q2, Q12, R2, R3, R4 resolved-reference items | Resolved questions section | Remain traceability references, not active decision blockers. | `resolved_by_DOC_A_to_E2` | No action in DOC-F0 | Future `open_questions.md` hygiene could keep references but should not reopen them. |

## Known unresolved boundary checklist

| Open area | Last decision / current state | DOC-F0 review question | Finding | Recommended next action |
|---|---|---|---|---|
| Evaluation/T30 output schema | In DOC-E2 deliberately not canonized | Is the boundary reference enough, or does this need CODE-FU-B first? | DATA_MODEL and REPORTS correctly exclude Evaluation/T30 output schemas from current report/diagnostics contracts. The boundary reference is enough for now, but a durable Evaluation/T30 schema document should wait until CODE-FU-B classifies the legacy snapshot exporter cluster. | CODE-FU-B_first |
| `export_evaluation_dataset.py` / `compute_global_top20` / `e2_model` | Classified as active executable legacy snapshot evaluation export tooling, not active `scanner/evaluation/*` infrastructure | Should this remain in `open_questions.md`, become CODE-FU-B, or become a dedicated evaluation-doc ticket? | This cluster is active executable legacy snapshot evaluation export tooling, but not active scanner/evaluation/* infrastructure. It should be handled as CODE-FU-B first so documentation does not canonize a soon-to-change boundary. | CODE-FU-B_first |
| `SNAPSHOTS.md` | Only touched indirectly / marginally during DOC-E2 | Is the current snapshot documentation sufficient, or is a standalone update ticket needed? | SNAPSHOTS documents OHLCV history, run snapshot placement, lifecycle, and a limited T30 OHLCV artifact note, but it does not yet receive the same post-DOC-E2 boundary treatment as DATA_MODEL/REPORTS. | dedicated_doc_ticket |
| `SCHEMA_CHANGES.md` navigation | Remains an evidence/change log; INDEX/AUTHORITY role alignment may still be incomplete | Is a small INDEX/AUTHORITY navigation clarification enough, or is a separate ticket needed? | AUTHORITY already defines `SCHEMA_CHANGES.md` as evidence, not a full data model. A small navigation patch in INDEX/AUTHORITY-adjacent wording is enough if humans want clearer reader routing; do not rewrite `SCHEMA_CHANGES.md` as a model. | small_doc_patch |

## Residual documentation gaps

| Gap | Why it remains | Suggested handling |
|---|---|---|
| Evaluation/T30 output schema contract | Explicitly excluded from DATA_MODEL/REPORTS and entangled with the legacy exporter boundary. | CODE-FU-B first, then future Evaluation/T30 documentation. |
| Legacy snapshot evaluation exporter cluster | Decision note classifies components but does not implement deprecation/removal/ownership. | CODE-FU-B code-boundary ticket. |
| Snapshot/replay documentation alignment | SNAPSHOTS is valid but narrower than updated DATA_MODEL/REPORTS and only lightly mentions T30 OHLCV generation. | Standalone SNAPSHOTS doc update after or alongside CODE-FU-B, depending on scope. |
| Q14 evidence-validation fields | DOC-E2 intentionally refused to promote unvalidated fields as contracts. | Focused evidence-validation ticket; move `basket` to Evaluation/T30 follow-up if it belongs there. |
| Open-question tracker hygiene | Some active questions are correctly still open; resolved references remain for traceability; Q11 contains duplicated wording. | Optional later small_doc_patch after evidence decisions, not in DOC-F0. |
| SCHEMA_CHANGES reader routing | Its role is clear in AUTHORITY, but INDEX-level navigation could be more explicit. | Small final navigation patch; no rewrite of SCHEMA_CHANGES. |

## Recommended follow-up sequence

DOC-F0 recommends path 4 as the immediate next step: CODE-FU-B first, then Evaluation/T30 documentation. This path avoids canonizing Evaluation/T30 fields or legacy-exporter behavior before the code boundary is decided. A small documentation/navigation patch can be done before CODE-FU-B only if the team wants low-risk reader-routing cleanup, but it should not block CODE-FU-B.

| Priority | Proposed ticket | Type | Rationale | Depends on |
|---|---|---|---|---|
| P1 | CODE-FU-B: classify/deprecate/own legacy snapshot evaluation export path | code_boundary | Resolves the highest-risk ambiguity around `export_evaluation_dataset.py`, `compute_global_top20`, and `e2_model` before Evaluation/T30 docs make schema claims. | Human approval of CODE-FU-B scope |
| P2 | Evaluation/T30 output schema documentation | evaluation_doc | Documents forward-return/evaluation/export fields only after the active-vs-legacy exporter boundary is stable. | CODE-FU-B |
| P3 | SNAPSHOTS current-state update | doc_update | Aligns snapshot/replay/T30 artifact wording with post-DOC-E2 data/report boundaries. | Preferably CODE-FU-B; can proceed earlier if limited to placement/lifecycle wording |
| P4 | Small INDEX/AUTHORITY navigation clarification for `SCHEMA_CHANGES.md` | doc_patch | Clarifies reader routing without changing the evidence-log role or rewriting schema history. | None |
| P5 | Q14 evidence-validation cleanup | doc_inventory | Validates unconfirmed DOC-E1/DOC-E2 field subjects and prepares a later `open_questions.md` hygiene patch. | Access to current artifacts/code evidence |
| P6 | Open-questions hygiene patch | doc_patch | Updates statuses only after evidence/code-boundary tickets have resolved the relevant items. | CODE-FU-B and/or Q14 validation outcomes |

## Deferred items

| Item | Deferral reason | Revisit trigger |
|---|---|---|
| Q5 schema split for execution capacity vs quality | Current documentation mitigates consumer ambiguity; schema rename/split requires versioning. | Future schema-version bump or consumer confusion. |
| Q6 rename of `is_reduced_size_eligible` | Current semantics are documented; rename requires migration. | Future schema cleanup window. |
| Q10 tokenized asset execution behavior | Informational until reproduced. | Multiple newer Shadow-Live runs show the same pattern. |
| Broad rewrite of `docs/SCHEMA_CHANGES.md` | It is an evidence/change log, not a complete current-state data model. | Never as a rewrite; only append future schema changes or improve navigation elsewhere. |
| Canonicalizing Evaluation/T30 schemas inside DATA_MODEL/REPORTS | Explicitly outside current contract. | Dedicated Evaluation/T30 doc ticket after CODE-FU-B. |

## Conflicts and uncertainties

| Area | Conflict / uncertainty | DOC-F0 stance |
|---|---|---|
| Evaluation/T30 vs report/data contracts | Evaluation outputs are present in the repository ecosystem but intentionally excluded from DATA_MODEL/REPORTS current-state contracts. | Preserve boundary; do not document Evaluation/T30 schemas as current DATA_MODEL/REPORTS facts in this ticket. |
| Legacy exporter executability | The exporter cluster is executable and tested but legacy-classified relative to active `scanner/evaluation/*` infrastructure. | Treat as active executable legacy snapshot evaluation export tooling, but not active scanner/evaluation/* infrastructure, until CODE-FU-B decides fate. |
| SNAPSHOTS coverage | SNAPSHOTS is useful and not obviously stale, but it is less comprehensive than DOC-E2-updated DATA_MODEL/REPORTS. | Classify as partial and recommend a dedicated update ticket. |
| Q14 field subjects | Several fields/concepts are plausible but not fully validated as active serialized contracts. | Keep them open; use a focused evidence-validation ticket rather than broad docs cleanup. |
| Human policy questions | Non-ASCII symbol treatment and structural formula definitions cannot be solved by evidence review alone. | Mark as `needs_human_decision`; no silent implementation or documentation invention. |
