# Open Questions — Independence-Release Bootstrap (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OPEN_QUESTIONS
status: canonical
```

## Purpose
This file tracks authoritative open questions that remain unresolved in the current Independence-Release architecture and therefore must not be silently decided by later implementation tickets.
These questions map to the unresolved clarification surface referenced in Gesamtkonzept §21.

## Bootstrap rule
Until an open question listed here is resolved in canonical documentation, later tickets and implementations must not silently invent business-logic answers for it.

---

## Open questions

*Sorted by impact on investment-signal correctness. Items at the top affect which candidates are shown as actionable; items further down are architectural quality concerns.*

---

### 1) `is_tradeable_candidate` does not account for `candidate_excluded` / universe exclusion

**Context**

Observed in Shadow-Live (May 2026): `USDPUSDT` showed:

```text
decision_bucket = confirmed_candidates
is_tradeable_candidate = true
universe.candidate_excluded = true
universe_category = stable_or_cash_proxy
```

The report summary correctly excludes such symbols from tradeable counts, but at the row level `is_tradeable_candidate` remains `true`. Any consumer reading the diagnostics directly (analysis scripts, T30 evaluation) sees a false positive.

**Still to decide**

- **Option A:** `candidate_excluded = true` forces `is_tradeable_candidate = false`. The field is final-operative.
- **Option B:** `is_tradeable_candidate` remains execution-/bucket-scoped. A separate field (e.g. `is_operational_trade_candidate`) additionally respects `candidate_excluded`.

**Why this must be resolved before a fix ticket**

The semantics of `is_tradeable_candidate` must be decided canonically first. A fix ticket without this decision risks either breaking downstream consumers of the current field or producing an inconsistent second field.

**Related:** See Q5 (Stablecoin filter) for the root cause; Q14 (operational tradeability field) for the Option B enhancement.

---

### 2) Stablecoin / cash-proxy exclusion is incomplete

**Context**

Multiple Shadow-Live runs have produced stablecoin/cash-proxy candidates that pass the eligibility and decision layers:

- `TUSDUSDT` — appeared as confirmed candidate on two consecutive days (early Shadow-Live runs)
- `USDPUSDT` — appeared as confirmed candidate with `universe_category = stable_or_cash_proxy` and `candidate_excluded = true` but `is_tradeable_candidate = true` (May 2026 run)

Stablecoins should be caught by market-cap or price-stability filters, but no explicit categorical exclusion exists in the spec.

**Still to decide**

1. Should an explicit stablecoin/cash-proxy hard exclusion be added to the Eligibility layer (pre-decision), the Universe Classification layer, or both?
2. Candidate rule: `universe_category in {stable_or_cash_proxy, fiat_proxy, wrapped_cash}` → hard exclude before decision/tradeability evaluation.
3. Which module owns enforcement?

---

### 3) `distance_to_range_high_pct_abs` has no canonical formula — T_EL2 input missing

**Context**

The field exists in T5 as a `FeatureBundle` attribute but is not implemented. T_EL1b (Schema `ir1.2`) correctly emits it as `null` in `entry_location_inputs` for all symbols, with a code comment referencing this open question. Codex was explicitly instructed not to implement it.

**Why this matters**

This is one of the six planned T_EL2 input fields. Until a canonical formula exists, T_EL2 operates with five inputs instead of six, and any threshold calibration in Step B cannot include this dimension.

**Still to decide**

1. What exactly is the "Range High" — swing high over what lookback?
2. Which historical bars or anchors define the range?
3. Is a configurable lookback parameter involved?
4. Which module owns the computation?
5. How does this field differ from `dist_to_base_mid_pct` (Q8)? The distinction must remain explicit.

---

### 4) Intraday diagnostics are repeatedly empty (0 records)

**Context**

Multiple Shadow-Live artifacts contain `intraday symbol_diagnostics.jsonl.gz = 0 records`. Daily diagnostics are complete and correct in the same artifacts.

**Still to decide**

- Is zero records expected behavior when no new 4h bar is present (`NO_NEW_4H_BAR` no-op)?
- Or does the Intraday Runner process symbols but write to the wrong / empty file (artifact packaging issue)?
- Or is this a serialization defect in the Intraday Runner itself?
- If zero records is intentional, should the report/manifest document this explicitly so analysis scripts do not treat it as a failure?

**Consequence**

Until resolved, Intraday Promotion scan quality cannot be validated from diagnostics. Recommended: small diagnostic ticket before productive Intraday expansion.

---

### 5) `execution_size_class = "full"` has two distinct meanings

**Context**

`execution_size_class = "full"` occurs in two separate scenarios:

1. `direct_ok` + full orderbook depth → full position possible, all execution metrics passed.
2. `marginal` + full orderbook depth, but at least one other execution quality metric prevented `direct_ok`.

The distinction is only preserved via `execution_status_raw`. Documented in `TRADEABILITY_GATE.md` (PR #236), but the single value conflates depth-capacity and execution-quality.

**Still to decide**

Does the current documentation suffice permanently, or should a future schema version introduce granular fields such as:

```text
execution_capacity_class  = full / reduced_75 / reduced_50 / reduced_25
execution_quality_status  = direct_ok / marginal / fail / unknown
```

No current misbehavior. Deferred until schema cleanup is warranted.

---

### 6) `is_reduced_size_eligible` is semantically misleading — rename pending

**Context**

`is_reduced_size_eligible = true` also applies to `direct_ok` records, which trade at full — not reduced — size. The field name implies "only eligible for reduced-size trading". The actual semantics (documented in `TRADEABILITY_GATE.md`, PR #236) are:

```text
tradeable at the policy-permitted position size, whether full or reduced
```

**Still to decide**

Should the field be renamed in a future schema cleanup? Candidate names:

```text
is_execution_eligible
is_policy_tradeable
is_policy_size_eligible
```

A rename requires a schema version bump (`ir1.3` or later) and explicit migration handling. Must be decided before a rename ticket can be authored.

---

### 7) Smoke test vs. full-universe intraday behavior differs

**Context**

Smoke-test runs and full-universe runs show different Intraday behavior. Most likely not a bug, but the root cause has not been verified.

**Still to decide**

Diagnose and document why the difference occurs. If intentional (e.g. universe size affects 4h-bar availability thresholds), document this explicitly. If a bug, fix.

---

### 8) `candidate_excluded_symbol_count` missing from `candidate_segments`

**Context**

T23 defines `candidate_excluded_symbol_count` as an explicit contract field (integer). In Shadow-Live reports the key is absent from `candidate_segments` — the value comes back as `None`. No operational impact, but the report contract is incomplete.

**Still to decide**

Is this a T23 implementation defect (Codex omitted the field) or a known scope gap? If a defect, it is a small targeted fix against the T23 module. If intentional, the contract must be updated to document the absence.

---

### 9) Non-ASCII symbol `币安人生USDT` passes the eligibility filter

**Context**

A symbol containing Chinese characters appeared as a Confirmed Candidate in a Shadow-Live run, classified as `classic_crypto`. The eligibility filter does not reject non-Latin or non-ASCII symbol names.

**Still to decide**

1. Should the Eligibility layer apply an explicit ASCII / Latin-character filter on symbol names?
2. Or is this handled canonically via the Override Map (explicit inclusion/exclusion)?
3. If neither, document that non-ASCII symbols are intentionally allowed through and will appear in output.

---

### 10) `tokenized_stock_or_etf` shows systematically higher `unknown_execution` rate

**Context**

Observed in T24 run (bar_id 2026-05-02): 6/22 tokenized assets showed `UNKNOWN_ORDERBOOK_STALE`, significantly higher than in `classic_crypto` segments.

**Still to decide**

Is this a structural pattern (lower market-maker activity, less frequently updated order books for tokenized assets)? If so:

- Should tokenized assets receive different execution grading behavior?
- Should the `observe_only` threshold for stale orderbooks be tighter for this category?
- Or is the current handling correct and this is informational only?

---

### 11) ARBUSDT shows `execution_attempted = true` without a valid decision bucket

**Context**

Observed after the Smoke-Test run (T20): `ARBUSDT` had `execution_attempted = True` with no corresponding `decision_bucket` or `state_machine_state` in diagnostics. Flagged as a "pre-existing anomaly in the execution adapter path" at the time, never investigated further.

**Still to decide**

Is this a defect in the Execution Adapter logic, a diagnostics serialization gap, or an edge case specific to early Smoke-Test-phase behavior that is no longer reproducible? Lowest priority — verify first whether this is still observable in current Shadow-Live runs before investing in a fix.

---

### 12) Evaluation Replay does not accumulate across runs

**Context**

`run_count: 1` on every day. Correct by T18 design — the Replay reads from the run artifact of the current session, not from a persistent event store. This means the Evaluation does not build a cross-day event history.

**Consequence**

For genuine forward-return evaluation ("What did TURTLEUSDT do after the confirmed signal?") either an accumulating event store or a separate analysis script that merges multiple Replay artifacts across days is required. This is the prerequisite for T30.

**Still to decide**

Which approach: accumulating event store (architectural change to T18) or aggregating analysis script (lighter, consistent with T25 pattern)?

---

### 13) `dist_to_base_mid_pct` remains unresolved

**Context**

The field `dist_to_base_mid_pct` was identified during the Ticket-5 / Ticket-5.1 / Ticket-6 workstream as a required input for `expansion_progress_structural`, but no authoritative formula was found in the governing specifications.

The field name and descriptive intent exist, but the architecture still lacks a canonical definition for:

- what exactly the "base mid" is,
- which historical range/base it refers to,
- how that base is selected,
- and the exact formula for converting it into `dist_to_base_mid_pct`.

**Why this matters**

Without an authoritative formula, independent implementations may invent incompatible meanings for the same field, causing divergence in Tier-1 axis computation, diagnostics, later runner/state interpretation, and backtest comparability.

**Current consequence**

`expansion_progress_structural` treats this sub-input as absent. The related subscore remains unavailable; the axis continues to rely on canonical weight-dropout / re-normalization with `expansion_progress_structural_reduced_resolution = true`.

**Still to decide**

1. The authoritative base-selection rule.
2. The exact mathematical formula.
3. Whether any lookback/config parameter is involved.
4. Which module owns the computation contract.

---

## Resolved questions (for reference)

### R2) Long-term OHLCV history storage path beyond Ticket 4 transitional SQLite persistence
**Status:** Resolved by Ticket 14. Canonical path: `snapshots/history/ohlcv/timeframe=<tf>/symbol=<symbol>/year=<yyyy>/month=<mm>/`

### R3) `daily_bar_id` type consistency across Independence-Release layers
**Status:** Resolved by Ticket 15. Canonical cross-layer type: `str` in `YYYY-MM-DD` format.

### R4) §21/3 Execution frequency + Top-N policy (Daily vs Intraday)
**Status:** Resolved by Tickets 16 and 17. No fachlicher Top-N cap; optional limits are technical safeguards only.
