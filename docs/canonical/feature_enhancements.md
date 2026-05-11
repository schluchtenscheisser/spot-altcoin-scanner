# Feature Enhancements — Deferred Topics (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_FEATURE_ENHANCEMENTS
status: canonical
```

## Purpose
This file lists **deliberately deferred topics** for the Independence-Release architecture. New entries are added only when a future ticket explicitly defers an enhancement instead of implementing it, or when a finding from Shadow-Live analysis is logged here for later action.

---

## Deferred enhancements

*Sorted by impact on investment-signal correctness. Items marked **Low Hanging Fruit** can be inserted as quick parallel fixes without a full ticket cycle.*

---

### 1) Entry-Location / Chase-Risk Layer (T_EL2)

**Source context:** T_EL1b exposed `entry_location_inputs` fields in `symbol_diagnostics.jsonl.gz` (Schema `ir1.2`). Shadow-Live analysis shows that multiple high-scoring, fully-tradeable candidates are already significantly extended above 4h EMA20 at the time of scan:

```text
ASTERUSDT: close_vs_ema20_4h_pct ~ +5.5%
ENAUSDT:   close_vs_ema20_4h_pct ~ +7.8%
TERRAUSDT: close_vs_ema20_4h_pct ~ +11.1%
KISHUUSDT: close_vs_ema20_4h_pct ~ +17.2%
```

The scanner currently outputs these as actionable with no overextension signal.

**Reason for deferral:** T_EL2 requires empirical threshold calibration (T_EL1 Step B) to run first. Thresholds must not be hard-coded.

**Future enhancement scope:**

- Implement `scanner/decision/entry_location.py` with fields `entry_location_status` and `entry_action_hint`.
- Add report segments: `buy_now_candidates`, `wait_pullback_candidates`, `early_watch_candidates`.
- Thresholds from Step B, provisional, config-parametrised — no hard-coding.
- Phase 1: no impact on `priority_score`, bucket membership, or Tradeability Gate.
- `entry_location_inputs` is the canonical namespace for all Entry-Location input fields (since T_EL1b, `ir1.2`).

**Prerequisite:** T_EL1 Step B must complete first.

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
- Explicitly document the `distance_to_range_high_pct_abs` dimension as not calibrated (field is `null` in all current artifacts; see Q3).
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

### 6) Operational tradeability field (`is_operational_trade_candidate`)

**Source context:** See open question Q1 (`is_tradeable_candidate` vs. `candidate_excluded`). If Q1 is resolved with Option B (separate fields rather than overwriting), this enhancement becomes the implementation vehicle.

**Reason for deferral:** Blocked by Q1 — the semantic decision must be made first.

**Timing note:** If Q1 is resolved with Option B, implement this field before T30 is executed. Otherwise T30 evaluation scripts will require ad-hoc filters (`is_tradeable_candidate == true AND candidate_excluded != true`) — exactly the kind of implicit logic the architecture is designed to avoid.

**Future enhancement scope:**

- Add field `is_operational_trade_candidate = is_tradeable_candidate AND NOT candidate_excluded`.
- This field is the final-operative signal for analysis scripts, T30, and any execution-adjacent tooling.
- Schema version bump required.

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

### 8) AI context hygiene: `AI_CONTEXT_CURRENT.md` + SUPERSEDED headers

**Source context:** Context-hygiene audit (April 2026) identified that `docs/GPT_SNAPSHOT.md` is entirely stale (generated 2026-03-13, pre-Independence-Release architecture) and `docs/code_map.md` has an active/legacy blindspot (`scanner/pipeline/` legacy modules appear alongside new Independence-Release families without distinction). `v2_1_addendum_for_future_tickets_and_new_chats_updated.md` is frozen at T1–T3 status.

**Reason for deferral:** No impact on scanner output. Deferred until after T_EL2 to avoid context churn during active implementation.

**Future enhancement scope (two-track):**

**Immediate (no ticket required):** Add `SUPERSEDED` header block to `GPT_SNAPSHOT.md` and `v2_1_addendum_for_future_tickets_and_new_chats_updated.md` to prevent AI agents from reading them as current context.

**Full ticket (T0.1A + T0.1B already drafted):**

- New `docs/AI_CONTEXT_CURRENT.md`: architecture overview, active-vs-legacy module distinction, run-mode context (`daily` / `intraday`), spec-file hierarchy, current implementation status.
- **Mandatory embedded maintenance rule**: document must include an explicit instruction specifying when and how it must be updated, to prevent future staleness.
- `docs/code_map.md`: extend the generator script (`scripts/update_codemap.py`) to include a curator-protected header block with active/legacy distinction — do not manually patch the generated file.

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
