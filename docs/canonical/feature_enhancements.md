# Feature Enhancements — Deferred Topics (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_FEATURE_ENHANCEMENTS
status: canonical
last_reviewed: 2026-05-15
review_context: "Post T30 v1.1 / ir1.5 data accumulation phase"
```

## Purpose


Compatibility note: Diese Liste dokumentiert bewusst verschobene Themen aus früheren Planungsständen. Historical placeholder status: none yet.
This file lists deliberately deferred, partially implemented, and completed enhancement topics for the Independence-Release architecture.

Items that are fully implemented are retained in a reference section so that older tickets, reviews, and open-question links remain traceable without treating completed work as still deferred.

---

## Active deferred enhancements

*Sorted roughly by impact and practical priority. Items marked **Low Hanging Fruit** can be inserted as quick parallel fixes without a full ticket cycle if source evidence is available.*

---

### 4) Overextension marker using short-term price performance

**Status:** Deferred

**Source context**

Several candidates were output as `confirmed / direct_ok / full` despite strong recent price appreciation visible on short-term charts. T_EL2 now covers the 4h EMA20 / entry-location perspective, but short-term raw returns would capture the broader trend-exhaustion perspective.

**Reason for deferral**

T_EL2 v1 is now implemented and should be observed first. Adding a second overextension dimension too early could over-filter candidates and confound T_EL2 recalibration.

**Future enhancement scope**

- Add fields such as:

```text
return_24h_pct
return_3d_pct
return_7d_pct
```

- Consider:

```text
distance_from_recent_breakout_pct
freshness_distance_state_confirmed
```

- Clarify relationship to `expansion_progress_structural` to avoid duplicate or contradictory overextension signals.
- Decide whether this is only diagnostic, an Entry-Location modifier, or a future bucket/ranking input.

**Prerequisite**

Observe and recalibrate T_EL2 v1 on a larger `ir1.5+` Shadow-Live base first.

---

### 7) Override-Map maintenance — pending tokenized-stock / ETF entries *(Low Hanging Fruit)*

**Status:** Active / verification pending

**Source context**

T23 established the override-map pattern. One known confirmed case exists:

```yaml
TSLAONUSDT:
  category: tokenized_stock_or_etf
  confidence: high
  reason: exact_override_tokenized_stock
```

**Pending verification**

The following symbols surfaced in Shadow-Live context and may be tokenized-stock-/ETF-like entries, but must not be added without high-confidence source evidence:

```text
VONUSDT
OXYONUSDT
PBRONUSDT
MAONUSDT
NVDAXUSDT
```

**Canonical rule**

Only add symbols with high-confidence source backing, for example:

- MEXC listing page,
- CoinMarketCap,
- clearly identifiable ticker/product mapping.

Unverified symbols remain unresolved and must not be guessed into the override map.

**Implementation path**

No large ticket is required if evidence is unambiguous. Use a direct config edit following T23 conventions. If any symbol is ambiguous, leave it open.

---

### 9) Terminal-event forward returns for decay / invalidation states

**Status:** Deferred

**Source context**

Ticket 18 records terminal events such as:

```text
first_late
first_chased
first_rejected
```

for transition and lead-time analysis, but does not calculate forward returns, Maximum Favorable Excursion (MFE), or Maximum Adverse Excursion (MAE) from those events.

**Reason for deferral**

These events are not entry signals. Returns from them answer a separate counterfactual question and could be confused with signal-event quality metrics.

**Future enhancement scope**

- Define the analytical question for terminal-event returns.
- Define reference-price semantics for each terminal event.
- Decide whether terminal-event returns belong in separate exports.
- Ensure they cannot be mixed with signal-event forward-return metrics.

---

### 10) State confidence penalty for "narrow margins" — operationalization and calibration

**Status:** Deferred

**Source context**

Abschnitt 4 defines a `-5` penalty when the current state rests on "narrow margins", but the concept is not yet operationalized.

**Current interim handling**

Treated as `0` / not applied until the concept is specified.

**Future enhancement scope**

- Define what exactly qualifies as "narrow".
- Decide whether the margin is measured against phase floors, state admission thresholds, or both.
- Decide whether the rule is phase-specific, state-specific, or global.
- Specify how multiple near-threshold conditions combine.
- Calibrate the penalty empirically on real run populations before activation.

---

### 11) Spec consistency pass for rule tables vs. enum / reason-code lists

**Status:** Deferred

**Source context**

Earlier ticket preparation exposed mismatches between explicit bucket-assignment rules and corresponding standard reason-code lists.

**Future enhancement scope**

- Run a systematic consistency audit across Gesamtkonzept and section files.
- Verify that explicit rules, enum families, reason-code lists, and examples stay aligned.
- Resolve inconsistencies centrally before they propagate into future tickets.

---

### 12) Standardized nullable-numeric handling for decision / ranking paths

**Status:** Deferred

**Source context**

Decision and ranking paths can mis-handle nullable numeric inputs, especially across gated, non-gated, demotion, and catch-all paths.

**Future enhancement scope**

- Define a clearer architecture-level policy for nullable numeric inputs by path category.
- Document which paths must reject, which may floor, and which must preserve nullability.
- Keep the policy narrow and explicit rather than relying on helper-local conventions.

---

### 13) Standardized demotion / fallback scoring pattern in the decision layer

**Status:** Deferred

**Source context**

Execution-fail demotions and other fallback paths are easy to route incorrectly through candidate-style scoring logic.

**Future enhancement scope**

- Define a standard demotion/fallback scoring pattern.
- Separate candidate-ranking paths from demotion / blocked / observe-only paths.
- Ensure fallback paths do not accidentally inherit actionable-candidate ranking semantics.
- Add explicit tests for demotion paths and null-preserving paths.

---

### 14) Broader architecture/code-quality enhancements

**Status:** Deferred

**Source context**

The current implementation is operationally stable enough for Shadow-Live data accumulation, but future maintainability work remains useful after T30/T_EL2 data collection.

**Future enhancement scope**

Potential areas include:

- stricter typed models for diagnostics/report contracts,
- central helpers for nested diagnostics field access,
- schema-validation hardening,
- stronger module-boundary tests,
- reduction of duplicated report/export transformation logic,
- improved CI checks for canonical field paths.

**Current boundary**

Do not block the current 2–3 week data-accumulation phase on these improvements unless a concrete bug appears.

---

## Implemented / completed enhancements (reference)

### 1) Entry-Location / Chase-Risk Layer (T_EL2)

**Status:** Implemented

**Resolution**

Implemented as T_EL2 v1 and live since schema `ir1.3`.

Current important fields:

```text
entry_location.entry_location_status
entry_location.entry_action_hint
entry_location.entry_location_reason_primary
entry_location.entry_location_reason_codes
entry_location.range_high_proximity_warning
```

**Current boundary**

T_EL2 v1 is intentionally informative/action-hint oriented. It does not rewrite the full v2.1 state machine and does not by itself make final performance claims.

`distance_to_range_high_pct_abs` is numerically available but not yet a fully calibrated primary input; it remains covered by Q3 in `open_questions.md`.

**Next step**

Recalibration waits for more `ir1.5+` Shadow-Live runs, roughly after a larger data base is accumulated.

---

### 2) T_EL1 Step B — Empirical calibration of entry-location thresholds

**Status:** Completed / implemented as calibration basis

**Resolution**

Step-B threshold work was completed and used as the calibration basis for T_EL2 v1.

**Current boundary**

The resulting thresholds are provisional and should be revisited after more `ir1.5+` Shadow-Live data. This is now a recalibration/data-accumulation topic, not an unimplemented enhancement.

---

### 3) Forward-return evaluation for T29 tradeable candidates (T30)

**Status:** Implemented v1/v1.1

**Resolution**

T30 v1 and T30-Fix-1 were implemented. A first T30 v1.1 run completed technically.

Validated technical capabilities:

- Replay runs successfully.
- OHLCV fetch works.
- Early-/confirmed-reference-price fallback works.
- Segment fields are present in the export.

**Current analytical boundary**

T30 is not yet analytically final:

- data base is still small,
- `10d` horizon is not yet meaningful,
- further `ir1.5+` runs are required,
- T30-Fix-2 for broader OHLCV scope is optional/nachgelagert.

---

### 5) Automated report persistence

**Status:** Implemented

**Resolution**

Automated Report Persistence is active. It supports ongoing T25/T30-style aggregation without requiring manual ZIP handling for the small report/index/manifest family.

**Current boundary**

Large diagnostics, OHLCV Parquet, SQLite files, and heavy evaluation exports must still not be committed as regular repo data.

---

### 6) Operational tradeability field (`is_operational_trade_candidate`)

**Status:** Implemented

**Resolution**

Implemented through the Q1/Q2 decision path with schema `ir1.5`.

Current semantics:

```text
is_operational_trade_candidate =
  is_tradeable_candidate == true
  AND candidate_excluded != true
```

**Current contract**

- `is_tradeable_candidate` remains execution-/bucket-scoped.
- `is_operational_trade_candidate` is the final operational field for analysis/evaluation consumers.
- `candidate_excluded` is top-level.
- `universe_category` remains nested under `universe.universe_category`.

---

### 8) AI context hygiene: `AI_CONTEXT_CURRENT.md` + SUPERSEDED headers

**Status:** Implemented / verify headers separately

**Resolution**

`AI_CONTEXT_CURRENT.md` has been created/updated as the current AI context document.

The stale-context problem for `GPT_SNAPSHOT.md` and `v2_1_addendum_for_future_tickets_and_new_chats_updated.md` is expected to be handled via `SUPERSEDED` header blocks.

**Current boundary**

Verify separately whether the following files currently contain the intended `SUPERSEDED` header:

```text
GPT_SNAPSHOT.md
v2_1_addendum_for_future_tickets_and_new_chats_updated.md
```

If missing, this is a small Codex one-liner / documentation-only fix, not a large enhancement ticket.
