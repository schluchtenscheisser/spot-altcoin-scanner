# Feature Enhancements — Deferred Topics (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_FEATURE_ENHANCEMENTS
status: canonical
```

## Purpose
This file lists **deliberately deferred topics** (bewusst verschobene Themen) for the Independence-Release architecture. New entries are added only when a future ticket explicitly defers an enhancement instead of implementing it, or when a finding from Shadow-Live analysis is logged here for later action.

---

## Deferred enhancements

Bootstrap marker: `none yet` is retained for compatibility with the original Independence-Release bootstrap check, even though deferred topics are now tracked below.

*Sorted by impact on investment-signal correctness. Items marked **Low Hanging Fruit** can be inserted as quick parallel fixes without a full ticket cycle.*

---

### 1) Entry-Location / Action-Hint Layer (T_EL2 v1 implemented)

**Source context:** T_EL1b exposed `entry_location_inputs` fields in `symbol_diagnostics.jsonl.gz` (Schema `ir1.2`). T_EL2 v1 adds an informational layer that classifies current entry location separately from the operational display hint.

**Implemented v1 scope:**

- `scanner/decision/entry_location.py` resolves `entry_location_status` with enum values `fresh_entry`, `acceptable_entry`, `extended_entry`, `chased_entry`, and `not_evaluable`.
- The same layer resolves `entry_action_hint` with enum values `buy_now_candidate`, `acceptable_if_strategy_allows`, `wait_for_pullback`, `avoid_chasing`, `monitor_only`, and `not_evaluable`.
- Status is based on `entry_location_inputs.dist_to_ema20_4h_pct_abs`, the optional `continuation_breakout` EMA20-distance override, and the extreme-distance guard only.
- Default EMA20 thresholds are `2.5 / 5.5 / 8.5`; the `continuation_breakout` override uses `3.5 / 7.0 / 10.0`; `dist_to_ema20_4h_pct_abs > 50.0` is `not_evaluable`.
- Ordered action-hint overrides are: not-evaluable status, chased status, `candidate_excluded is True`, `is_tradeable_candidate is not True`, `early_candidates`, then the confirmed/tradeable execution-size matrix.
- Report segments are emitted under `entry_location_candidate_segments`: `buy_now_candidates`, `wait_pullback_candidates`, `early_watch_candidates`, `good_location_but_not_tradeable`, and `tradeable_but_extended`.
- `distance_to_range_high_pct_abs` is used only for nullable `range_high_proximity_warning` with default warning threshold `<= 0.5`; it does not change v1 status or action hint.
- T_EL2 v1 is informational only: it does not change `priority_score`, bucket membership, the Tradeability Gate, execution grading, or order execution.

**Remaining enhancement scope:**

- Recalibrate thresholds after at least 10 Shadow-Live runs.
- Decide whether and how range-high proximity should become a primary status/action dimension in a future T_EL2 version.
- Consider later complementary overextension metrics only after v1 has been evaluated.

**Prerequisite status:** T_EL1 Step B completed for the provisional v1 calibration basis.

---

### 2) T_EL1 Step B — Empirical calibration of entry-location thresholds

**Source context:** T_EL1 Step A established the baseline distribution of `close_vs_ema20_4h_pct` and related fields across confirmed/tradeable candidates. One run (2026-05-09) produced n=25, Median ~4.66%, P75 ~5.85% — insufficient for stable threshold derivation.

**Reason for deferral:** Requires 3–5 `ir1.2` Shadow-Live runs before calibration is meaningful. Target date: ~2026-05-12–14.

**Future enhancement scope:**

- Run Step B analysis script against accumulated `ir1.2` artifacts.
- Analyse `close_vs_ema20_4h_pct`, `dist_to_ema20_4h_pct_abs`, `bars_above_ema20_4h` across all relevant segments — not only `confirmed/tradeable`, but at minimum:
  - `confirmed direct_ok full`
  - `early direct_ok full`
  - `marginal reduced-size eligible`
  - `observe_only`
  - `unknown / not_evaluable`
  - high-score but non-tradeable
- The gap between "good entry-location but non-tradeable" and "tradeable but overextended" is particularly valuable for T_EL2 threshold design.
- Derive provisional thresholds separating `fresh_entry / acceptable_entry / extended_entry / chased_entry`.
- Validate pattern-specific differentiation (especially `early_reversal_break` vs. `shallow_pullback`).
- Explicitly document the `distance_to_range_high_pct_abs` dimension as not calibrated (field is numerically present in current `ir1.2` artifacts but remains only auxiliary-warning calibrated; see Q3).
- Output: provisional threshold candidates for T_EL2 config.

---

### 3) Forward-return evaluation for T29 tradeable candidates (T30)

**Source context:** T29 introduced a clean segmentation of tradeable candidates into `direct_ok`, `marginal reduced-size eligible`, `marginal observe_only`, `fail blocked`, and `unknown not_evaluable`. No analysis yet validates whether these groups actually produce different forward returns.

**Reason for deferral:** Requires Automated Report Persistence (enhancement 5) so that report.json files are available for aggregation without manual ZIP downloads.

**Future enhancement scope:**

- Compare forward returns by `execution_size_class` (full / reduced_25 / reduced_50 / reduced_75).
- Compare `direct_ok` vs. `marginal reduced-size eligible` vs. `observe_only`.
- Cross-reference with spread/slippage band and entry-location distance.
- Validate the T28 calibration empirically: do `reduced_25` candidates underperform `direct_ok` as expected?

**Prerequisite:** Automated Report Persistence (enhancement 5) + Q12 resolution (Evaluation Replay accumulation).

---

### 4) Overextension marker using short-term price performance

**Source context:** Several candidates were output as `confirmed / direct_ok / full` despite strong recent price appreciation visible on the 7-day chart (e.g. TONUSDT +100% in 7 days, ASTERUSDT breakout after an already extended prior move). The 4h EMA20 distance (T_EL2) captures the intraday overextension perspective; short-term raw returns capture the broader trend-exhaustion perspective.

**Reason for deferral:** T_EL2 (enhancement 1) should be implemented and validated before adding a second overextension dimension to avoid over-filtering. This marker addresses the broader trend-exhaustion perspective (raw short-term returns); it is a complement to T_EL2's 4h EMA20 analysis, not a replacement for it.

**Future enhancement scope:**

- Add fields `return_24h_pct`, `return_3d_pct`, `return_7d_pct` to diagnostics or report output.
- Consider `distance_from_recent_breakout_pct` and `freshness_distance_state_confirmed`.
- Clarify relationship to `expansion_progress_structural` (T1/T5 axis) — potential redundancy or complementarity.

---

### 5) Automated report persistence (report.json commits after each daily run)

**Source context:** T25 aggregation and T30 forward-return evaluation currently require manual ZIP artifact downloads. All data is available in the run artifacts, but there is no automated path to accumulate it in the repo.

**Reason for deferral:** Not blocking current Shadow-Live data collection; manual downloads have been sufficient for T25–T27 analysis.

**Priority note:** Although this is not a signal-quality feature itself, it is a direct enabler for T30. If manual artifact handling becomes a bottleneck during T30 preparation, this should be implemented first — not deferred until after T30 is designed.

**Future enhancement scope:**

- After each Daily Run, commit small plaintext files to the repository: `report.json` family, index files, manifest files.
- Explicitly excluded from commits: `symbol_diagnostics.jsonl.gz`, Parquet files, raw data.
- Workflow permission: `contents: write` scoped to this job only.
- Enables T25 aggregation and T30 forward-return evaluation to run directly against the repo without manual intervention.

---

### 6) Operational tradeability field (`is_operational_trade_candidate`) — IMPLEMENTED

**Implementation status (2026-05-13, T_Q1_Q2_OPERATIONAL_TRADEABILITY):** Implemented in schema `ir1.5`. Diagnostics emit top-level `is_operational_trade_candidate = (is_tradeable_candidate is True AND candidate_excluded is not True)`. T30 and operative consumers must use this field as the final row-level tradeability label.

**Source context:** See open question Q1 (`is_tradeable_candidate` vs. `candidate_excluded`). If Q1 is resolved with Option B (separate fields rather than overwriting), this enhancement becomes the implementation vehicle.

**Resolution note:** Q1 was resolved with Option B by `docs/canonical/decisions/Q1_Q2_operational_tradeability_and_stablecoin_exclusion.md`; this enhancement is no longer deferred.

**Historical timing note:** If Q1 is resolved with Option B, implement this field before T30 is executed. Otherwise T30 evaluation scripts will require ad-hoc filters (`is_tradeable_candidate == true AND candidate_excluded != true`) — exactly the kind of implicit logic the architecture is designed to avoid.

**Implemented scope:**

- Added field `is_operational_trade_candidate = (is_tradeable_candidate is True AND candidate_excluded is not True)`.
- This field is the final-operative signal for analysis scripts, T30, and any execution-adjacent tooling.
- Schema version bumped to `ir1.5`.

---

### 7) Override-Map maintenance — pending entries  *(Low Hanging Fruit)*

**Source context:** T23 established the exact override map. Several symbols have been identified in Shadow-Live runs as clearly classifiable but not yet added.

**Confirmed next entry:**

```yaml
TSLAONUSDT:
  category: tokenized_stock_or_etf
  confidence: high
  reason: exact_override_tokenized_stock
```

**Pending verification** (likely `tokenized_stock_or_etf / high`, but source verification outstanding):

```text
VONUSDT, OXYONUSDT, PBRONUSDT, MAONUSDT, NVDAXUSDT
```

**Canonical rule:** Only add symbols with high confidence backed by a verifiable source (MEXC listing page, CMC, or known ticker). Unverified symbols remain `unknown / low`. No ticket required — direct config edit following T23 conventions.

---

### 8) AI context hygiene: `AI_CONTEXT_CURRENT.md`, GPT snapshot refresh, and superseded roadmap addendum

**Status:** Mostly completed / keep under maintenance.

**Source context:** Context-hygiene audit (April 2026) identified that earlier AI context files could mislead AI agents into using stale pre-Independence or early-Independence assumptions. In particular:

- an older `docs/GPT_SNAPSHOT.md` had become stale relative to the active Independence Release implementation,
- `docs/code_map.md` had an active/legacy blindspot (`scanner/pipeline/` legacy modules appeared alongside new Independence-Release families without distinction),
- `v2_1_addendum_for_future_tickets_and_new_chats_updated.md` was frozen at the early T1–T3 implementation state.

**Resolution implemented:**

- `docs/AI_CONTEXT_CURRENT.md` now exists as the current AI-context routing document.
- It documents the active implementation status, active-vs-legacy module distinction, run-mode context, authority hierarchy, and known non-blocking states.
- `docs/roadmap/v2_1_addendum_for_future_tickets_and_new_chats_updated.md` now has a `SUPERSEDED — HISTORICAL WORKING CONTEXT ONLY` header and must not be used as current implementation status or current ticket-planning baseline.
- `docs/GPT_SNAPSHOT.md` was not marked superseded. Instead, it was refreshed into a current AI onboarding snapshot and is explicitly treated as an AI support artifact, not as independent domain authority.
- `docs/code_map.md` remains a generated structural map only and must not be treated as a semantic authority.

**Current intended document roles:**

- `docs/AI_CONTEXT_CURRENT.md` = primary AI-context routing and staleness-prevention document.
- `docs/GPT_SNAPSHOT.md` = compact current GPT onboarding snapshot, subordinate to repo reality and AI_CONTEXT_CURRENT.
- `docs/code_map.md` = generated navigation aid only.
- `docs/roadmap/v2_1_addendum_for_future_tickets_and_new_chats_updated.md` = historical working context only.
- v2.1 section documents and `independence_release_gesamtkonzept_final.md` = historical build-spec authority where no newer current-state documentation or implementation contract supersedes them.

**Maintenance rule:**

Whenever implementation status, schema version, active ticket range, Shadow-Live behavior, active module families, or authority hierarchy materially changes, update `docs/AI_CONTEXT_CURRENT.md` first. Then update `docs/GPT_SNAPSHOT.md` only if the compact onboarding snapshot would otherwise become misleading.

**Remaining follow-up:**

- Keep `docs/code_map.md` AI-safe via the generator script (`scripts/update_codemap.py`), not by manually patching generated content.
- Ensure generated/curated headers continue to distinguish active Independence Release module families from legacy/reference-only paths.
- Periodically verify that `docs/GPT_SNAPSHOT.md` and `docs/AI_CONTEXT_CURRENT.md` do not drift apart.

**No current signal-quality impact:** This topic affects AI/Codex/Claude context hygiene and implementation safety, not scanner output quality directly.

---

### 9) Terminal-event forward returns for decay / invalidation states

**Source context:** Ticket 18 records terminal events (`first_late`, `first_chased`, `first_rejected`) for transition and lead-time analysis, but does not calculate forward returns, MFE, or MAE from those events.

**Reason for deferral:** These events are not entry signals; returns from them would answer a separate counterfactual question and could be confused with signal-event quality metrics.

**Future enhancement scope:**

- Define the analytical question for terminal-event returns.
- Define reference-price semantics for each terminal event.
- Decide whether terminal-event returns belong in separate exports.
- Ensure they cannot be mixed with signal-event forward-return metrics.

---

### 10) State confidence penalty for "narrow margins" — operationalization and calibration

**Source context:** Abschnitt 4 defines a `-5` penalty when the current state rests on "narrow margins", but the concept is not yet operationalized.

**Current interim handling:** Treated as `0` / not applied until the concept is specified.

**Future enhancement scope:**

- Define what exactly qualifies as "narrow".
- Decide whether the margin is measured against phase floors, state admission thresholds, or both.
- Decide whether the rule is phase-specific, state-specific, or global.
- Specify how multiple near-threshold conditions combine.
- Calibrate the penalty empirically on real run populations before activation.

---

### 11) Spec consistency pass for rule tables vs. enum / reason-code lists

**Source context:** The Ticket-12 preparation exposed at least one mismatch between an explicit bucket-assignment rule and the corresponding standard reason-code list.

**Future enhancement scope:**

- Run a systematic consistency audit across Gesamtkonzept and section files.
- Verify that explicit rules, enum families, reason-code lists, and examples stay aligned.
- Resolve inconsistencies centrally before they propagate into future tickets.

---

### 12) Standardized nullable-numeric handling for decision / ranking paths

**Source context:** Ticket-12 work exposed that nullable numeric inputs in decision and ranking paths are easy to mis-handle, especially across gated, non-gated, demotion, and catch-all paths.

**Future enhancement scope:**

- Define a clearer architecture-level policy for nullable numeric inputs by path category.
- Document which paths must reject, which may floor, and which must preserve nullability.
- Keep the policy narrow and explicit rather than relying on helper-local conventions.

---

### 13) Standardized demotion / fallback scoring pattern in the decision layer

**Source context:** Execution-fail demotions and other fallback paths proved easy to route incorrectly through candidate-style scoring logic.

**Future enhancement scope:**

- Define a canonical scoring pattern for demotion, unresolved, and catch-all paths.
- Make explicit which score-building helpers are allowed in those paths.
- Reduce the chance that future decision tickets or implementations accidentally reuse the wrong scoring path.

---

### 14) More explicit ranking-input contract pattern for decision outputs

**Source context:** Ticket-12 required several iterations to make the ranking input contract fully explicit, especially around `symbol`, tie-break fields, and the distinction between decision output and ranking-ready records.

**Future enhancement scope:**

- Define a reusable canonical pattern for ranking-ready records.
- Standardize which fields must be present for deterministic ranking.
- Reduce repeated clarification effort in later tickets touching ranking or downstream reporting.
