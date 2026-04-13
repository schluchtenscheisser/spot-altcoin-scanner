# Title
[P0] Implement eligibility, staged market-data budget, post_1d_activity_gate, and pre_4h_candidate_filter

## Context / Source

This ticket implements Ticket 3 from the Independence-Release consolidated concept: `eligibility + market data budget + pre_4h_candidate_filter`.

**Gesamtkonzept reference:** This ticket corresponds to Gesamtkonzept §19, Ticket 3.

`depends_on: [1, 2]` — requires `bar_clock + sqlite + config foundation` (Ticket 1) and `canonical docs bootstrap` (Ticket 2).

The uploaded v2.1 section files plus `independence_release_gesamtkonzept_final.md` are the authoritative source set for this ticket and take precedence over older repo-canonical material where they differ.

This ticket follows the approved decisions from the ticket clarification loop:
- pre-1d eligibility uses cheap MEXC/CMC/persisted metadata only
- `post_1d_activity_gate` is a hard post-1d gate and is semantically distinct from `pre_4h_candidate_filter`
- monitored symbols receive 4h via monitoring bypass before the budget filter
- `pre_4h_candidate_filter` is a cheap operational 4h budget gate with exactly 3 OR-rules
- budget overflow for non-bypass symbols is resolved deterministically

## Goal

After this change, the daily pipeline must be able to:
- decide pre-1d eligibility for discovered MEXC spot symbols using deterministic hard rules
- derive and persist first-seen MEXC listing metadata without requiring a pre-1d OHLCV fetch
- apply a hard `post_1d_activity_gate` after the 1d fetch
- always grant 4h fetch to currently monitored symbols via monitoring bypass
- apply a cheap 1d-based `pre_4h_candidate_filter` only to non-bypass candidates
- cap non-bypass 4h fetches with deterministic ranking and tie-breaks
- expose auditable per-symbol and per-run decision diagnostics

## Scope

Allowed change surface:
- `scanner/universe/eligibility.py`
- `scanner/universe/market_data_budget.py`
- `scanner/universe/__init__.py` if needed
- `scanner/clients/mexc_client.py` for any required read-only method additions (no refactor of existing methods)
- `scanner/clients/marketcap_client.py` for any required read-only method additions
- `scanner/storage/schema.py` for new table definitions
- `scanner/storage/repositories.py` for new read/write access to universe decision data
- `scanner/config.py` or the central config accessor for new config keys and defaults
- `tests/**` for new tests covering eligibility, activity gate, bypass, filter rules, ranking, cap, and persistence bootstrap behavior
- `docs/canonical/**` for updates required by this ticket (see "Canonical docs to update" below)

## Out of Scope

This ticket must not:
- implement phase interpretation
- implement state-machine transitions
- implement invalidation logic
- implement entry-pattern logic
- implement execution logic or orderbook-quality checks
- implement Tier-1 or Tier-2 score computation
- use 4h-derived fields to decide whether 4h should be fetched
- use pullback/reset signal families inside `pre_4h_candidate_filter`
- rename the post-1d gate as a second eligibility phase
- refactor existing client methods unrelated to the needs of this ticket
- implement OHLCV fetch logic (that is Ticket 4)
- implement cache policy logic (that is Ticket 4)
- implement feature/raw-field derivation logic (that is Ticket 5) — this ticket consumes 1d raw fields via interfaces defined here and provides test doubles/fixtures for them

## Canonical References (important)

Primary authority for this ticket:
- `independence_release_gesamtkonzept_final.md` (§2.1, §2.2, §10.1, §12, §19, §21)
- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` (§2.1, §3.2, §5.1)
- `v2_1_abschnitt_2_tier_2_simplified_achsen_rev2.md` (§2.2 — authoritative for Rule C unit semantics)
- `v2_1_abschnitt_4_state_machine_rev3_aligned.md` (state enum source)
- `v2_1_abschnitt_7_entry_pattern_decision_buckets_rev3_aligned.md` (decision_bucket enum source)

Repo template/checklist references for ticket shape and Codex-readiness:
- `docs/tickets/_TEMPLATE.md`
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`

This ticket must also create or update the following canonical docs (see "Canonical docs to update" in Implementation Notes):
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/open_questions.md`

> If the current authoritative reference, Canonical, and existing code conflict, the authoritative reference wins. If additional clarification is needed, extend the ticket or ask the user rather than interpret.

> Existing repo paths/helpers may be reused as long as they do not conflict with Canonical; do not introduce a second source of truth.

## Proposed change (high-level)

### Before
- The repo does not yet have the Independence-Release staged universe-admission and 4h-budget chain.
- There is no deterministic contract for pre-1d eligibility, hard post-1d activity gating, monitoring bypass, 3-rule `pre_4h_candidate_filter`, and capped non-bypass 4h selection.

### After
- Daily universe selection executes this exact chain:
  1. universe discovery
  2. pre-1d eligibility
  3. 1d OHLCV fetch for pre-1d eligible symbols
  4. 1d raw-field derivation
  5. `post_1d_activity_gate`
  6. monitoring bypass
  7. `pre_4h_candidate_filter`
  8. non-bypass 4h budget cap
  9. 4h OHLCV fetch for selected symbols

### Edge cases
- Unknown MEXC listing age before first persistence: passes as explicitly flagged `unknown_pass`.
- Unknown/unmapped CMC market cap: passes as explicitly flagged `unknown_pass`.
- Symbol with fewer than 14 daily bars of any history available: `activity_gate_status = not_evaluable`, `pre_4h_filter_primary_reason = "ACTIVITY_GATE_NOT_EVALUABLE"`.
- Within the fixed 14-day window ending at `daily_bar_id`, bars missing entirely from the window count as inactive days (no tolerance).
- Bars present in the window with invalid `quote_volume` (`null`/`NaN`/`inf`/`-inf`) count as inactive up to 2 occurrences; if invalid-volume bars exceed 2, `activity_gate_status = not_evaluable` with reason `ACTIVITY_GATE_INVALID_INPUTS`, and `pre_4h_filter_primary_reason = "ACTIVITY_GATE_NOT_EVALUABLE"`.
- Activity-gate failure vs. not-evaluable is distinguished in both `activity_gate_status` (fine-grained) and `pre_4h_filter_primary_reason` (`ACTIVITY_GATE_FAILED` vs `ACTIVITY_GATE_NOT_EVALUABLE`).
- `not_evaluable` is distinct from `failed`.
- Monitored symbols receive 4h even if the nominal cap is already exhausted.
- If monitoring bypass alone exceeds the nominal cap, total actual 4h fetch count may exceed that nominal cap.
- If more non-bypass symbols pass than slots remain, ranking is deterministic.
- `max_4h_fetch_count = 0` is a valid config value and means no non-bypass symbols receive 4h; bypass symbols still receive 4h.

### Backward compatibility impact
- Config surface grows under `independence_release.universe` and `independence_release.market_data_budget` namespaces.
- SQLite schema grows by two new tables (`symbol_metadata`, `symbol_run_decisions`) and extensions to `run_metadata`.
- New reason-code and status contracts must be reused by later tickets, not redefined.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Workflow priority:** Follow `docs/canonical/WORKFLOW_CODEX.md` strictly.
- **Authority precedence:** If older repo-canonical material conflicts with the uploaded v2.1 section files or the Gesamtkonzept, implement the uploaded authority set.
- **Config/Defaults:** Use `ScannerConfig` defaults or the central config-accessor path. Do not create raw-dict default drift. Every new config key introduced by this ticket has an explicit deterministic default specified below.
- **Nullability:** Do not coerce nullable fields with implicit `bool(...)`. `None`/`null` remains semantically distinct.
- **Strict status separation:**
  - `unknown_pass` is not `pass`
  - `unknown_pass` is not `fail`
  - `not_evaluable` is not `failed`
  - `not_evaluable` is not `passed`
  - `skipped_bypass` and `skipped_activity_gate` are not `failed` and not `passed`
- **Determinism:** All ranking, reason selection, and list ordering must be stable. Tie-break for capped non-bypass symbols is `quote_volume_24h` descending, then `symbol` ascending lexicographic. `matched_filter_rules` ordering uses the same deterministic priority as primary-reason selection.
- **No semantic leakage in `pre_4h_candidate_filter`:** Do not use 4h-derived fields, phase-interpreter outputs, Tier-1/Tier-2 scores, pullback/reset fields, state-transition logic, or any persisted metadata other than what is explicitly allowed below.
- **Pipeline stop enforcement:** Symbols with `activity_gate_status = failed` or `activity_gate_status = not_evaluable` stop before monitoring bypass and `pre_4h_candidate_filter`. They must not incur further processing cost in those stages.
- **Auditability:** Persisted output must make the decision path auditable per symbol and per run. No hidden in-memory-only state for first-seen listing-date bootstrap or 4h-selection reasons.
- **No auto-doc manual editing:** `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` remain read-only.

### Config merge semantics (Pflicht)
> Partial overrides in `independence_release.universe` and `independence_release.market_data_budget` are merged field-by-field with central defaults; missing sub-keys are not treated as invalid. Invalid values (wrong type, out of range) produce a clear `ValueError` that includes the key name and the invalid value.

### Numeric robustness (Pflicht)
> Non-finite numeric values (`NaN`, `inf`, `-inf`) and `None` in rule inputs or activity-gate inputs are treated as not evaluable for the affected rule/check. They must not be silently coerced to 0, false, or any numeric default. They must not appear in numeric-looking outputs.

### Determinism (Pflicht)
> At identical input and identical config, all eligibility decisions, activity-gate decisions, bypass decisions, filter decisions, ranking order, cap outcomes, reason codes, and counter values are identical.

### Pipeline stop (Pflicht)
> `activity_gate_status in {failed, not_evaluable}` stops the symbol before monitoring bypass and `pre_4h_candidate_filter` and must not incur any processing cost in those stages for the current daily run.

### Nullability (Pflicht)
> `listing_age_days`, `market_cap_usd`, `active_days_last_14`, `quote_volume_24h`, and per-rule input fields are nullable. `null` means "not reliably evaluable" and must not be implicitly coerced to `0` or `false`.

## Implementation Notes

### Dataflow / pipeline stage impacts

Implement the decision chain in this order:
1. universe discovery
2. pre-1d eligibility
3. 1d OHLCV fetch for eligible symbols (handled by later ticket; this ticket defines the interface)
4. 1d raw-field derivation (handled by later ticket; this ticket defines the interface)
5. `post_1d_activity_gate`
6. monitoring bypass
7. `pre_4h_candidate_filter`
8. non-bypass budget cap
9. 4h OHLCV fetch for selected symbols (handled by later ticket)

### Config contract

All new config keys live under `independence_release.universe` and `independence_release.market_data_budget`.

#### `independence_release.universe` — defaults

| Key | Default | Type | Validation |
|---|---|---|---|
| `quote_asset_allowed` | `["USDT"]` | list[str] | non-empty list of strings |
| `listing_age_days_min` | `45` | int | `>= 0` |
| `quote_volume_24h_min` | `500000` | number | `>= 0` |
| `market_cap_usd_min` | `10000000` | number | `>= 0` |
| `mexc_tradeable_status_values` | `["1"]` | list[str] | non-empty list of strings |

#### `independence_release.market_data_budget` — defaults

| Key | Default | Type | Validation |
|---|---|---|---|
| `activity_gate.daily_quote_volume_active_floor` | `25000` | number | `>= 0` |
| `activity_gate.min_active_days` | `12` | int | `>= 0` |
| `activity_gate.window_days` | `14` | int | `>= 1`, `>= min_active_days` |
| `monitoring_bypass.min_phase_confidence` | `55` | number | `0..100` |
| `pre_4h_candidate_filter.rule_a.close_vs_ema50_1d_pct_min_exclusive` | `0.0` | number | finite |
| `pre_4h_candidate_filter.rule_a.ema20_vs_ema50_1d_pct_min_inclusive` | `0.0` | number | finite |
| `pre_4h_candidate_filter.rule_a.ema20_slope_1d_pct_per_bar_min_exclusive` | `0.0` | number | finite |
| `pre_4h_candidate_filter.rule_b.volume_1d_current_vs_median10_min_inclusive` | `2.0` | number | `> 0` |
| `pre_4h_candidate_filter.rule_c.range_width_10bars_1d_pct_max_inclusive` | `10.0` | number | `> 0` |
| `pre_4h_candidate_filter.rule_c.close_position_in_range_10bars_1d_min_inclusive` | `0.70` | number | `0..1` |
| `max_4h_fetch_count` | `100` | int | `>= 0` |

Missing keys fall back to these defaults. Invalid values produce a `ValueError` naming the key and the invalid value.

### Pre-1d eligibility contract

For every discovered symbol, evaluate pre-1d eligibility using only:
- MEXC spot symbol metadata (from MEXC `GET /api/v3/exchangeInfo` — authoritative for `quoteAsset` and `status`)
- MEXC 24h market snapshot (from MEXC `GET /api/v3/ticker/24hr` — authoritative for `quoteVolume`)
- persisted SQLite metadata from earlier runs (`symbol_metadata.mexc_first_tradable_date`)
- CMC global market-cap data (from CMC `GET /v1/cryptocurrency/quotes/latest` — authoritative for `market_cap`)

Do not require fresh 1d or 4h OHLCV to evaluate pre-1d eligibility.

A symbol is pre-1d eligible iff all of the following hold:

**1. Quote asset rule**
- MEXC `exchangeInfo.quoteAsset` must be in `cfg.universe.quote_asset_allowed` (default: `["USDT"]`)

**2. Tradability rule**
- MEXC `exchangeInfo.status` must be contained in `cfg.universe.mexc_tradeable_status_values` (default: `["1"]`)
- The default is aligned to the currently documented MEXC Spot `exchangeInfo.status` value for tradeable symbols. If MEXC changes the status taxonomy in the future, this config list can be extended without a code change.
- Any status value not contained in the allowed list fails this rule (suspended / offline / delisted / non-tradeable states).

**3. MEXC listing-age rule**
- target semantics: days since first tradeable availability of the concrete MEXC spot symbol
- pre-1d source: persisted `symbol_metadata.mexc_first_tradable_date` only, if known
- threshold: `listing_age_days >= cfg.universe.listing_age_days_min` (default: 45)
- bootstrap behavior:
  - if no persisted `mexc_first_tradable_date` exists for the symbol: `listing_age_status = "unknown_pass"`, `listing_age_days = null`
  - `unknown_pass` does not block pre-1d eligibility but is explicitly flagged
  - this is not a silent default
- after the first 1d-backed derivation in a later pipeline stage, persist `mexc_first_tradable_date` (the `open_time` of the earliest available MEXC 1d bar for this symbol)
- subsequent runs must use the persisted value

**4. MEXC 24h quote-volume rule**
- source: MEXC `ticker/24hr.quoteVolume` for the concrete symbol
- threshold: `quote_volume_24h >= cfg.universe.quote_volume_24h_min` (default: 500000)
- if the ticker response is missing the symbol or `quoteVolume` is `null`/`NaN`/`inf`/`-inf`: the symbol fails this rule with reason `QUOTE_VOLUME_24H_NOT_EVALUABLE`

**5. CMC market-cap rule**
- source: CMC global market cap for the matched CMC ID of the symbol
- threshold: `market_cap_usd >= cfg.universe.market_cap_usd_min` (default: 10000000)
- behavior:
  - matched + cap >= threshold → `market_cap_status = "known_pass"`
  - matched + cap < threshold → `market_cap_status = "known_fail"`, rule fails
  - no CMC match → `market_cap_status = "unknown_pass"`, rule passes flagged
  - matched but `market_cap` is `null`/`NaN`/`inf`/`-inf` → `market_cap_status = "unknown_pass"` (treated as unmapped)

**Status enums — complete allowed value sets**

- `listing_age_status ∈ {"known_pass", "known_fail", "unknown_pass"}` — no other values allowed
- `market_cap_status ∈ {"known_pass", "known_fail", "unknown_pass"}` — no other values allowed
- `quote_asset_status ∈ {"pass", "fail"}` — no other values allowed
- `tradability_status ∈ {"pass", "fail"}` — no other values allowed

**Required per-symbol pre-1d eligibility outputs**

- `symbol: str`
- `eligible_pre_1d: bool`
- `eligibility_fail_reasons: list[str]` — always present, may be empty; see Reason Codes section
- `quote_asset_status`
- `tradability_status`
- `listing_age_status`
- `listing_age_days: int | null`
- `market_cap_status`
- `market_cap_usd: float | null`
- `quote_volume_24h: float | null`
- `mexc_first_tradable_date: str | null` — ISO 8601 date if known
- `decision_timestamp_utc: str` — ISO 8601

### post_1d_activity_gate contract

Runs after 1d OHLCV fetch and 1d raw-field derivation (steps 3–4).

**Input:** MEXC 1d OHLCV of the concrete symbol, retrieved in step 3.

**Window semantics (verbindlich):**
- The window is the **last `window_days` bars ending at `daily_bar_id` (exclusive of any open current bar)**, not "last `window_days` available bars".
- Concretely: if current `daily_bar_id = "2026-04-12"` and `window_days = 14`, the window is bars with `date ∈ ["2026-03-30", ..., "2026-04-12"]` (14 calendar dates, all closed).
- Missing bars in this window (date exists in window but no OHLCV record for this symbol) count as non-active days and reduce the active-day count. A missing bar is **not** an exchange-outage fallback; it counts against the symbol's activity.
- **Fetcher assumption (verbindlich):** This rule assumes the OHLCV fetcher (Ticket 4) only produces missing bars when the symbol genuinely had no trading activity on that date — not as a result of fetcher-side errors (network timeout, API rate-limit, retry failure, etc.). Fetcher robustness is the responsibility of Ticket 4. If Ticket 4 cannot guarantee this property, the activity gate's interpretation of "missing bar = inactive" must be revisited in a follow-up ticket.
- Bars present in the window with invalid `quote_volume` (`null`/`NaN`/`inf`/`-inf`) also count as non-active days **up to 2 occurrences**.
- If invalid-volume bars in the window exceed 2, `activity_gate_status = not_evaluable` with reason `ACTIVITY_GATE_INVALID_INPUTS`.
- If the symbol has fewer than `window_days` daily bars of any history (i.e., listing newer than the window): `activity_gate_status = not_evaluable`.

**Activity definition:**
- A daily bar is active iff `daily_quote_volume >= cfg.market_data_budget.activity_gate.daily_quote_volume_active_floor` (default: 25000).
- Exactly `25000` counts as active (inclusive).

**Pass condition:**
- The symbol passes iff the count of active bars in the window is `>= cfg.market_data_budget.activity_gate.min_active_days` (default: 12).

**Semantics:**
- This is a hard gate for the current daily run.
- Symbols with `activity_gate_status ∈ {failed, not_evaluable}` do not proceed to monitoring bypass or `pre_4h_candidate_filter`.
- This gate is not a soft budget decision.

**Required outputs:**

- `activity_gate_status ∈ {"passed", "failed", "not_evaluable"}` — no other values allowed
- `active_days_last_14: int | null` — null iff `activity_gate_status = not_evaluable`
- `activity_gate_reason: str` — one of the codes in the Reason Codes section

### Monitoring bypass contract

Runs after `post_1d_activity_gate` and before `pre_4h_candidate_filter`, only for symbols with `activity_gate_status = passed`.

A symbol receives 4h without applying `pre_4h_candidate_filter` if at least one of the following holds (source fields read from persistence):

- `state_machine_state ∈ {watch, early_ready, confirmed_ready, late}`
- `decision_bucket ∈ {watchlist, early_candidates, confirmed_candidates, late_monitor}`
- `market_phase_confidence >= cfg.market_data_budget.monitoring_bypass.min_phase_confidence` (default: 55)

**Semantics:**
- Bypass symbols always receive 4h in the current daily run.
- Bypass symbols count toward the total actual 4h fetch count.
- Bypass may exceed the nominal cap (see Cap contract).
- Missing values (`state_machine_state = null`, `decision_bucket = null`, `market_phase_confidence = null`) do not implicitly pass any bypass predicate.
- `market_phase_confidence` that is `NaN`/`inf`/`-inf` does not pass the confidence predicate.

**Required outputs:**

- `monitoring_bypass_applied: bool`
- `monitoring_bypass_reason: str | null` — one of `BYPASS_STATE`, `BYPASS_BUCKET`, `BYPASS_CONFIDENCE`, or null if not bypassed

### pre_4h_candidate_filter contract

Runs only for symbols that:
- passed pre-1d eligibility
- received 1d OHLCV
- have `activity_gate_status = passed`
- have `monitoring_bypass_applied = false`

**Allowed inputs:**
- Eligibility metadata from this ticket
- MEXC 1d OHLCV of the concrete symbol
- 1d-only raw fields named explicitly in this ticket (Rule A/B/C inputs)

**Forbidden inputs:**
- Any 4h-derived field
- Phase-interpreter output
- State-transition logic
- Tier-1 or Tier-2 scores
- Pullback/reset signal families
- Persisted metadata other than that required for pre-1d eligibility checks

**Filter form:**
- Exactly 3 OR-rules
- One rule per allowed signal family (Trend / Volume / Compression)
- Overall pass iff at least one rule has `status = passed`

**Rule A — Trend 1d**

Pass iff all three hold:
- `close_vs_ema50_1d_pct > cfg...rule_a.close_vs_ema50_1d_pct_min_exclusive` (default: 0.0, strict greater-than)
- `ema20_vs_ema50_1d_pct >= cfg...rule_a.ema20_vs_ema50_1d_pct_min_inclusive` (default: 0.0, inclusive)
- `ema20_slope_1d_pct_per_bar > cfg...rule_a.ema20_slope_1d_pct_per_bar_min_exclusive` (default: 0.0, strict greater-than)

Pass reason code: `FILTER_PASSED_TREND_1D`

**Rule B — Volume impulse 1d**

Pass iff:
- `volume_1d_current_vs_median10 >= cfg...rule_b.volume_1d_current_vs_median10_min_inclusive` (default: 2.0, inclusive)

Pass reason code: `FILTER_PASSED_VOLUME_IMPULSE_1D`

**Rule C — Compression 1d**

Pass iff both hold:
- `range_width_10bars_1d_pct <= cfg...rule_c.range_width_10bars_1d_pct_max_inclusive` (default: 10.0, inclusive)
- `close_position_in_range_10bars_1d >= cfg...rule_c.close_position_in_range_10bars_1d_min_inclusive` (default: 0.70, inclusive)

Pass reason code: `FILTER_PASSED_COMPRESSION_1D`

**Rule C unit requirements (verbindlich):**
- `range_width_10bars_1d_pct` uses **percent of close**, per Abschnitt 2 §2.2: `((highest_high − lowest_low) / close) * 100`
- `close_position_in_range_10bars_1d` uses **normalized `0..1`**, per Abschnitt 2 §2.2: `(close - range_low) / max(range_high - range_low, epsilon)`
- Implementation code comments, docstrings, and tests must reference `Abschnitt 2 §2.2` to prevent alternative normalization drift.

**Per-rule evaluation state — complete allowed value set:**

- `rule_status ∈ {"passed", "failed", "not_evaluable"}` — no other values allowed

**Definitions:**
- `passed`: all required inputs are present and numeric-valid, threshold(s) satisfied
- `failed`: all required inputs are present and numeric-valid, threshold(s) not satisfied
- `not_evaluable`: at least one required input is missing, `null`, `NaN`, `inf`, or `-inf`

**Overall filter status — complete allowed value set:**

- `pre_4h_filter_status ∈ {"passed", "failed", "skipped_bypass", "skipped_activity_gate"}` — no other values allowed

**Overall pass/fail:**
- `pre_4h_filter_status = passed` iff at least one rule has `status = passed`
- `pre_4h_filter_status = failed` iff all three rules have `status ∈ {failed, not_evaluable}`
- `pre_4h_filter_status = skipped_bypass` iff the symbol was bypassed (filter not evaluated)
- `pre_4h_filter_status = skipped_activity_gate` iff the symbol failed or was not-evaluable at the activity gate (filter not evaluated)

**Primary reason priority (verbindlich):**
1. `FILTER_PASSED_COMPRESSION_1D`
2. `FILTER_PASSED_TREND_1D`
3. `FILTER_PASSED_VOLUME_IMPULSE_1D`

**`matched_filter_rules` schema:**
- Type: `list[str]`
- Contents: reason codes of passed rules only (not failed, not not_evaluable)
- Ordering: same priority order as primary-reason selection (Compression first, then Trend, then Volume)
- Always present; may be an empty list
- Example when only Compression passes: `["FILTER_PASSED_COMPRESSION_1D"]`
- Example when Compression and Trend both pass: `["FILTER_PASSED_COMPRESSION_1D", "FILTER_PASSED_TREND_1D"]`

**Reason-code field rules:**
- `pre_4h_filter_status` is always present
- `pre_4h_filter_primary_reason` is always present
- If no rule passes, `pre_4h_filter_primary_reason = "FILTER_FAILED_ALL_RULES"`
- If bypassed, `pre_4h_filter_primary_reason = "MONITORING_BYPASS"`
- If activity-gate-skipped with `activity_gate_status = "failed"`: `pre_4h_filter_primary_reason = "ACTIVITY_GATE_FAILED"`
- If activity-gate-skipped with `activity_gate_status = "not_evaluable"`: `pre_4h_filter_primary_reason = "ACTIVITY_GATE_NOT_EVALUABLE"`
- This split makes downstream diagnostics self-contained: the primary reason field alone distinguishes "symbol was inactive" from "symbol could not be evaluated", without requiring a join against `activity_gate_status`.

### 4h budget cap contract

Config key: `independence_release.market_data_budget.max_4h_fetch_count` (default: 100).

**Cap semantics (Option A — bypass wins):**
- Monitoring-bypass symbols always get 4h.
- Bypass symbols count toward the actual total 4h fetch count.
- Non-bypass remaining slots: `remaining_non_bypass_slots = max(max_4h_fetch_count - monitoring_bypass_count, 0)`.
- If bypass count >= nominal cap, `remaining_non_bypass_slots = 0`; all bypass symbols still get 4h; no non-bypass symbols get 4h; `total_4h_fetch_count = monitoring_bypass_count` (may exceed nominal cap).
- Only non-bypass symbols with `pre_4h_filter_status = passed` compete for `remaining_non_bypass_slots`.

**Overflow ranking for non-bypass passed symbols:**
1. `quote_volume_24h` descending (numeric)
2. `symbol` ascending lexicographic (ties)

Non-bypass symbols that passed the filter but lose the cap receive:
- `was_capped_after_filter = true`
- `pre_4h_filter_primary_reason = "FILTER_PASSED_BUT_CAPPED"` (overrides the rule-specific primary reason in this final field)
- `matched_filter_rules` retains the originally matched rules (is not cleared)

### Reason Codes — complete set

The following top-level reason codes are authoritative for this ticket. No other codes may be introduced without a follow-up ticket.

**Eligibility fail reasons (values of `eligibility_fail_reasons`):**
- `QUOTE_ASSET_NOT_ALLOWED`
- `NOT_TRADEABLE`
- `LISTING_AGE_BELOW_THRESHOLD`
- `QUOTE_VOLUME_24H_BELOW_THRESHOLD`
- `QUOTE_VOLUME_24H_NOT_EVALUABLE`
- `MARKET_CAP_BELOW_THRESHOLD`

**Activity gate reasons (values of `activity_gate_reason`):**
- `ACTIVITY_GATE_PASSED`
- `ACTIVITY_GATE_INSUFFICIENT_ACTIVE_DAYS`
- `ACTIVITY_GATE_INSUFFICIENT_HISTORY`
- `ACTIVITY_GATE_INVALID_INPUTS`

**Monitoring bypass reasons (values of `monitoring_bypass_reason`):**
- `BYPASS_STATE`
- `BYPASS_BUCKET`
- `BYPASS_CONFIDENCE`

**Filter primary reasons (values of `pre_4h_filter_primary_reason`):**
- `FILTER_PASSED_COMPRESSION_1D`
- `FILTER_PASSED_TREND_1D`
- `FILTER_PASSED_VOLUME_IMPULSE_1D`
- `FILTER_FAILED_ALL_RULES`
- `FILTER_PASSED_BUT_CAPPED`
- `MONITORING_BYPASS`
- `ACTIVITY_GATE_FAILED`
- `ACTIVITY_GATE_NOT_EVALUABLE`

### SQLite schema additions

#### New table: `symbol_metadata`

Purpose: persist per-symbol metadata that is derived once and reused.

```sql
CREATE TABLE IF NOT EXISTS symbol_metadata (
    symbol                     TEXT PRIMARY KEY,
    mexc_first_tradable_date   TEXT,            -- ISO 8601 date, nullable until first derived
    cmc_id                     INTEGER,         -- nullable if unmapped
    first_seen_utc             TEXT NOT NULL,   -- ISO 8601, when symbol was first observed
    last_updated_utc           TEXT NOT NULL    -- ISO 8601, updated on each write
);
```

#### New table: `symbol_run_decisions`

Purpose: persist the per-symbol decision chain for each daily run.

```sql
CREATE TABLE IF NOT EXISTS symbol_run_decisions (
    run_id                          TEXT NOT NULL,
    symbol                          TEXT NOT NULL,
    eligible_pre_1d                 INTEGER NOT NULL,  -- 0 or 1
    eligibility_fail_reasons_json   TEXT NOT NULL,     -- JSON array of reason-code strings
    quote_asset_status              TEXT NOT NULL,
    tradability_status              TEXT NOT NULL,
    listing_age_status              TEXT NOT NULL,
    listing_age_days                INTEGER,           -- nullable
    market_cap_status               TEXT NOT NULL,
    market_cap_usd                  REAL,              -- nullable
    quote_volume_24h                REAL,              -- nullable
    activity_gate_status            TEXT,              -- nullable until gate runs
    active_days_last_14             INTEGER,           -- nullable
    activity_gate_reason            TEXT,              -- nullable
    monitoring_bypass_applied       INTEGER,           -- 0 or 1, nullable until bypass runs
    monitoring_bypass_reason        TEXT,              -- nullable
    pre_4h_filter_status            TEXT,              -- nullable until filter runs
    pre_4h_filter_primary_reason    TEXT,              -- nullable until filter runs
    matched_filter_rules_json       TEXT,              -- nullable; JSON array of reason-code strings
    rule_a_status                   TEXT,              -- nullable
    rule_b_status                   TEXT,              -- nullable
    rule_c_status                   TEXT,              -- nullable
    was_capped_after_filter         INTEGER,           -- 0 or 1, nullable
    selected_for_4h_fetch           INTEGER NOT NULL,  -- 0 or 1
    decision_timestamp_utc          TEXT NOT NULL,
    PRIMARY KEY (run_id, symbol),
    FOREIGN KEY (run_id) REFERENCES run_metadata(run_id)
);
```

#### Extension to existing `run_metadata` table

Add columns for the per-run counters specified in this ticket:

```sql
ALTER TABLE run_metadata ADD COLUMN pre_1d_eligible_count         INTEGER;
ALTER TABLE run_metadata ADD COLUMN pre_1d_ineligible_count       INTEGER;
ALTER TABLE run_metadata ADD COLUMN activity_gate_failed_count    INTEGER;
ALTER TABLE run_metadata ADD COLUMN monitoring_bypass_count       INTEGER;
ALTER TABLE run_metadata ADD COLUMN pre_4h_filter_passed_count    INTEGER;
ALTER TABLE run_metadata ADD COLUMN pre_4h_filter_failed_count    INTEGER;
ALTER TABLE run_metadata ADD COLUMN pre_4h_filter_capped_count    INTEGER;
ALTER TABLE run_metadata ADD COLUMN total_4h_fetch_count          INTEGER;
```

All counters are nullable while the run is in progress and must be written atomically at run completion or incrementally with last-write-wins semantics.

Schema migration must be handled via the schema-version mechanism from Ticket 1 (idempotent `CREATE TABLE IF NOT EXISTS`, idempotent `ALTER TABLE` guarded by schema version check).

### Canonical docs to update

**`docs/canonical/GLOSSARY.md`** — add definitions for:
- `post_1d_activity_gate` (with reference to this ticket)
- `monitoring_bypass`
- `pre_4h_candidate_filter` (with reference to Abschnitt 6 §2.1)
- `unknown_pass`
- `skipped_bypass`
- `skipped_activity_gate`
- `not_evaluable`
- `mexc_first_tradable_date`
- `ACTIVITY_GATE_FAILED` vs `ACTIVITY_GATE_NOT_EVALUABLE` (distinction at the filter-primary-reason level)

**`docs/canonical/ARCHITECTURE.md`** — add the 9-step universe-admission pipeline under the Daily Discovery Scan section.

**`docs/canonical/DATA_MODEL.md`** — add:
- `symbol_metadata` table schema
- `symbol_run_decisions` table schema
- `run_metadata` counter column additions
- complete reason-code taxonomy from this ticket

**`docs/canonical/RUNTIME_AND_OPERATIONS.md`** — update Daily Discovery Scan section to reflect the 9-step chain.

**`docs/canonical/open_questions.md`** — mark questions 1 and 2 from Gesamtkonzept §21 as resolved by this ticket; reference the ticket ID.

## Acceptance Criteria (deterministic)

1. Given discovered MEXC spot symbols, pre-1d eligibility marks a symbol eligible iff it passes all 5 rules (quote asset, tradability, listing age, 24h volume, market cap) using the exact thresholds and the unknown-pass semantics specified in "Pre-1d eligibility contract". The tradability rule uses `cfg.universe.mexc_tradeable_status_values` (default: `["1"]`) to determine which MEXC `exchangeInfo.status` values pass; all other status values fail.

2. Given a symbol without persisted `mexc_first_tradable_date`, pre-1d eligibility sets `listing_age_status = "unknown_pass"` and `listing_age_days = null`. After the first 1d-backed derivation in a later pipeline stage, the date is persisted in `symbol_metadata`, and subsequent runs use the persisted value.

3. Given MEXC 1d OHLCV for the concrete symbol, `post_1d_activity_gate` counts a day as active iff `daily_quote_volume >= cfg.market_data_budget.activity_gate.daily_quote_volume_active_floor` (default: `25000`, inclusive), and the symbol passes iff at least `cfg.market_data_budget.activity_gate.min_active_days` (default: `12`) of the `cfg.market_data_budget.activity_gate.window_days` (default: `14`) closed daily bars in the window ending at `daily_bar_id` are active.

4. Given a symbol with fewer than `cfg.market_data_budget.activity_gate.window_days` daily bars of history (default: `14`), or with more than 2 bars containing `null`/`NaN`/`inf`/`-inf` volume values in the window, `activity_gate_status = "not_evaluable"` and `active_days_last_14 = null`.

5. Given `activity_gate_status ∈ {"failed", "not_evaluable"}`, the symbol does not proceed to monitoring bypass or `pre_4h_candidate_filter` in that daily run, and no further processing costs are incurred for those stages. If `activity_gate_status = "failed"`, `pre_4h_filter_primary_reason = "ACTIVITY_GATE_FAILED"`. If `activity_gate_status = "not_evaluable"`, `pre_4h_filter_primary_reason = "ACTIVITY_GATE_NOT_EVALUABLE"`.

6. Given a symbol with `activity_gate_status = "passed"` and satisfying at least one monitoring bypass predicate, the symbol is selected for 4h fetch with `monitoring_bypass_applied = true` and a specific `monitoring_bypass_reason`, and `pre_4h_candidate_filter` is not evaluated for this symbol.

7. Given a non-bypass symbol eligible for filter evaluation, `pre_4h_candidate_filter` contains exactly 3 OR-rules, and `pre_4h_filter_status = "passed"` iff at least one rule has `status = "passed"`.

8. Given Rule A inputs, Rule A passes iff `close_vs_ema50_1d_pct > cfg...rule_a.close_vs_ema50_1d_pct_min_exclusive` (default: `0.0`, strict), `ema20_vs_ema50_1d_pct >= cfg...rule_a.ema20_vs_ema50_1d_pct_min_inclusive` (default: `0.0`, inclusive), and `ema20_slope_1d_pct_per_bar > cfg...rule_a.ema20_slope_1d_pct_per_bar_min_exclusive` (default: `0.0`, strict).

9. Given Rule B inputs, Rule B passes iff `volume_1d_current_vs_median10 >= cfg...rule_b.volume_1d_current_vs_median10_min_inclusive` (default: `2.0`, inclusive).

10. Given Rule C inputs, Rule C passes iff `range_width_10bars_1d_pct <= cfg...rule_c.range_width_10bars_1d_pct_max_inclusive` (default: `10.0`, inclusive) and `close_position_in_range_10bars_1d >= cfg...rule_c.close_position_in_range_10bars_1d_min_inclusive` (default: `0.70`, inclusive), with `range_width_10bars_1d_pct` interpreted as percent of close and `close_position_in_range_10bars_1d` as normalized `0..1` per Abschnitt 2 §2.2.

11. Given any rule input that is missing/`null`/`NaN`/`inf`/`-inf`, the affected rule has `status = "not_evaluable"`. `not_evaluable` is distinct from `failed` and does not count as pass.

12. Given multiple passed filter rules, the primary filter reason is `COMPRESSION > TREND > VOLUME`, and `matched_filter_rules` contains only passed rules, sorted in the same priority order.

13. Given no passed filter rules, `pre_4h_filter_primary_reason = "FILTER_FAILED_ALL_RULES"` and `matched_filter_rules = []`.

14. Given more non-bypass filter-passing symbols than `remaining_non_bypass_slots`, non-bypass symbols are kept by `quote_volume_24h` descending with `symbol` ascending as tie-break. Overflowed symbols have `was_capped_after_filter = true` and `pre_4h_filter_primary_reason = "FILTER_PASSED_BUT_CAPPED"`, while `matched_filter_rules` retains the originally matched rules.

15. Given monitoring-bypass symbols exceed the nominal `max_4h_fetch_count`, all bypass symbols still receive 4h, `remaining_non_bypass_slots = 0`, no non-bypass symbols receive 4h, and `total_4h_fetch_count` may exceed the nominal cap.

16. Given `max_4h_fetch_count = 0`, no non-bypass symbols receive 4h; bypass symbols still receive 4h.

17. Given any daily run, the required per-run counters are persisted in `run_metadata` and the required per-symbol decision fields are persisted in `symbol_run_decisions`.

18. Given the status enums `listing_age_status`, `market_cap_status`, `quote_asset_status`, `tradability_status`, `activity_gate_status`, `rule_status`, `pre_4h_filter_status`, no output value falls outside the complete allowed sets specified in the contract.

19. Given partial config overrides under `independence_release.universe` or `independence_release.market_data_budget`, missing sub-keys fall back to the specified defaults without raising errors. Invalid values raise `ValueError` naming the key and the invalid value.

20. Given identical input data and identical config, two runs of the decision chain produce identical outputs (statuses, reason codes, ranking order, counter values).

21. Canonical docs (`GLOSSARY.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `RUNTIME_AND_OPERATIONS.md`, `open_questions.md`) are updated per the "Canonical docs to update" section in the same PR.

22. The ticket is archived in the same PR according to `docs/canonical/WORKFLOW_CODEX.md`.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ (AC: #19 ; Test: missing-key test per config sub-block, verify defaults apply)
- **Config Invalid Value Handling:** ✅ (AC: #19 ; Test: invalid-value tests for each new config key — wrong type, negative value, out of range)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #2, #4, #11 ; Tests: unknown listing age → null; unknown market cap → null; rule inputs null/NaN → not_evaluable; no bool() coercion of these fields)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #4, #11, #13 ; Tests: per-rule `not_evaluable` vs `failed` distinction; activity_gate `not_evaluable` vs `failed`)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (AC: #17, #20 ; Test: if a run crashes mid-chain, `symbol_run_decisions` rows for that run_id are either complete for stages reached or absent; no partially written symbol decision rows)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A – this ticket does not generate filename-derived IDs)
- **Deterministische Sortierung/Tie-breaker:** ✅ (AC: #12, #14, #20 ; Tests: primary-reason priority test, sorted `matched_filter_rules` test, cap ranking tie-break test)

## Tests (required if logic changes)

### Unit — eligibility
- `USDT` symbol with all other checks passing → eligible
- `BTC` quote asset (not in allowlist) → fail with `QUOTE_ASSET_NOT_ALLOWED`
- Symbol with MEXC `status = "1"` (in default allowed list) → tradability passes
- Symbol with MEXC `status = "ENABLED"` (not in default allowed list) → fail with `NOT_TRADEABLE`
- Symbol with MEXC `status = "SUSPEND"` (not in default allowed list) → fail with `NOT_TRADEABLE`
- Symbol with MEXC `status = "BREAK"` (not in default allowed list) → fail with `NOT_TRADEABLE`
- Config override `mexc_tradeable_status_values = ["TRADING"]` + symbol with `status = "1"` → fail with `NOT_TRADEABLE` (since "1" not in overridden list)
- Config override `mexc_tradeable_status_values = ["1", "ENABLED"]` + symbol with `status = "ENABLED"` → tradability passes
- Config override `mexc_tradeable_status_values = []` → `ValueError` (empty list invalid)
- Listing age 44 days → fail with `LISTING_AGE_BELOW_THRESHOLD`
- Listing age 45 days → pass
- Listing age 46 days → pass
- Missing persisted `mexc_first_tradable_date` → `listing_age_status = "unknown_pass"`, `listing_age_days = null`, rule passes flagged
- Market cap 9,999,999 USD → fail with `MARKET_CAP_BELOW_THRESHOLD`
- Market cap 10,000,000 USD → pass, `market_cap_status = "known_pass"`
- Market cap 10,000,001 USD → pass
- No CMC match → `market_cap_status = "unknown_pass"`, rule passes flagged
- CMC match but `market_cap = null` → `market_cap_status = "unknown_pass"`
- CMC match but `market_cap = NaN` → `market_cap_status = "unknown_pass"`
- Quote volume 499,999 → fail with `QUOTE_VOLUME_24H_BELOW_THRESHOLD`
- Quote volume 500,000 → pass
- Quote volume `null` → fail with `QUOTE_VOLUME_24H_NOT_EVALUABLE`
- Quote volume `NaN` → fail with `QUOTE_VOLUME_24H_NOT_EVALUABLE`

### Unit — config
- Missing `independence_release.universe` entirely → all defaults apply, no error
- Missing `independence_release.universe.listing_age_days_min` → default 45 applies
- `listing_age_days_min = -1` → `ValueError` mentioning key name and value
- `listing_age_days_min = "forty-five"` → `ValueError`
- `quote_asset_allowed = []` → `ValueError`
- `max_4h_fetch_count = 0` → valid, accepted
- `max_4h_fetch_count = -1` → `ValueError`
- `rule_c.close_position_in_range_10bars_1d_min_inclusive = 1.5` → `ValueError` (out of 0..1)
- Partial override of `universe.listing_age_days_min = 60` merges with other universe defaults

### Unit — activity gate
- 14 bars available, 12 active → `passed`
- 14 bars available, 11 active → `failed` with `ACTIVITY_GATE_INSUFFICIENT_ACTIVE_DAYS`
- 14 bars available, 13 active → `passed`
- 14 bars available, 14 active → `passed`
- Exactly `daily_quote_volume = 25000` in a bar → that bar counts as active
- `daily_quote_volume = 24999` → that bar counts as inactive
- 10 bars available (listing newer than window) → `not_evaluable` with `ACTIVITY_GATE_INSUFFICIENT_HISTORY`
- 14 bars available, 3 bars with `quote_volume = NaN` → `not_evaluable` with `ACTIVITY_GATE_INVALID_INPUTS`
- 14 bars available, 2 bars with `quote_volume = NaN` and 12 active among remaining → `passed` (tolerance of up to 2 invalid bars)
- 14 bars available, 2 bars with `quote_volume = null` and 10 active among remaining → `failed` (insufficient active days)
- **Missing bars in window:** Symbol has 100 days of total history, but within the 14-day window ending at `daily_bar_id`, 3 calendar dates have no OHLCV record (e.g., symbol was delisted and relisted within that period). Remaining 11 bars all show active volume → `failed` with `ACTIVITY_GATE_INSUFFICIENT_ACTIVE_DAYS` (max 11 active, below threshold of 12). This is distinct from `ACTIVITY_GATE_INVALID_INPUTS` because the missing-bar rule has no tolerance limit.
- **Missing bars + insufficient active:** Symbol has 100 days of total history, 5 calendar dates missing in the 14-day window, remaining 9 bars all active → `failed` with `ACTIVITY_GATE_INSUFFICIENT_ACTIVE_DAYS` (max 9 active).
- Window is computed from current `daily_bar_id` backwards `window_days` calendar days, not from available bars.

### Unit — activity gate to filter reason mapping
- Symbol with `activity_gate_status = "failed"` → `pre_4h_filter_status = "skipped_activity_gate"`, `pre_4h_filter_primary_reason = "ACTIVITY_GATE_FAILED"`
- Symbol with `activity_gate_status = "not_evaluable"` (any reason: insufficient history or invalid inputs) → `pre_4h_filter_status = "skipped_activity_gate"`, `pre_4h_filter_primary_reason = "ACTIVITY_GATE_NOT_EVALUABLE"`
- The split ensures downstream consumers can distinguish "symbol was inactive" from "symbol could not be evaluated" from the primary reason field alone.

### Unit — monitoring bypass
- `state_machine_state = "watch"` → bypass with `BYPASS_STATE`
- `state_machine_state = "early_ready"` → bypass with `BYPASS_STATE`
- `state_machine_state = "confirmed_ready"` → bypass with `BYPASS_STATE`
- `state_machine_state = "late"` → bypass with `BYPASS_STATE`
- `state_machine_state = "rejected"` → no bypass via state
- `state_machine_state = "chased"` → no bypass via state
- `decision_bucket = "watchlist"` → bypass with `BYPASS_BUCKET`
- `decision_bucket = "early_candidates"` → bypass with `BYPASS_BUCKET`
- `decision_bucket = "confirmed_candidates"` → bypass with `BYPASS_BUCKET`
- `decision_bucket = "late_monitor"` → bypass with `BYPASS_BUCKET`
- `market_phase_confidence = 55` → bypass with `BYPASS_CONFIDENCE` (inclusive)
- `market_phase_confidence = 54` → no bypass
- `market_phase_confidence = null` → no bypass via confidence
- `market_phase_confidence = NaN` → no bypass via confidence
- All bypass inputs null/missing → no bypass
- Bypassed symbols: `pre_4h_filter_status = "skipped_bypass"`, rules are not evaluated

### Unit — filter rules
- Rule A: `close_vs_ema50_1d_pct = 0.1`, `ema20_vs_ema50_1d_pct = 0.0`, `ema20_slope_1d_pct_per_bar = 0.01` → passed
- Rule A: `close_vs_ema50_1d_pct = 0.0` (not strict greater) → failed
- Rule A: `ema20_slope_1d_pct_per_bar = 0.0` (not strict greater) → failed
- Rule A: any input = NaN → not_evaluable
- Rule A: any input = null → not_evaluable
- Rule A: any input = inf → not_evaluable
- Rule B: `volume_1d_current_vs_median10 = 2.0` → passed (inclusive)
- Rule B: `volume_1d_current_vs_median10 = 1.99` → failed
- Rule B: input = NaN → not_evaluable
- Rule C: `range_width_10bars_1d_pct = 10.0`, `close_position_in_range_10bars_1d = 0.70` → passed (both inclusive)
- Rule C: `range_width_10bars_1d_pct = 10.01` → failed
- Rule C: `close_position_in_range_10bars_1d = 0.69` → failed
- Rule C: any input = NaN → not_evaluable
- Overall filter: only Rule A passed → `pre_4h_filter_status = "passed"`, primary `FILTER_PASSED_TREND_1D`, `matched_filter_rules = ["FILTER_PASSED_TREND_1D"]`
- Overall filter: Rule A and Rule C passed → primary `FILTER_PASSED_COMPRESSION_1D`, `matched_filter_rules = ["FILTER_PASSED_COMPRESSION_1D", "FILTER_PASSED_TREND_1D"]`
- Overall filter: all three passed → primary `FILTER_PASSED_COMPRESSION_1D`, `matched_filter_rules = ["FILTER_PASSED_COMPRESSION_1D", "FILTER_PASSED_TREND_1D", "FILTER_PASSED_VOLUME_IMPULSE_1D"]`
- Overall filter: all rules failed → `pre_4h_filter_status = "failed"`, primary `FILTER_FAILED_ALL_RULES`, `matched_filter_rules = []`
- Overall filter: all rules not_evaluable → `pre_4h_filter_status = "failed"`, primary `FILTER_FAILED_ALL_RULES`, `matched_filter_rules = []`
- Overall filter: Rule A passed, Rule B failed, Rule C not_evaluable → `pre_4h_filter_status = "passed"`, primary `FILTER_PASSED_TREND_1D`

### Unit — cap
- `max_4h_fetch_count = 100`, 20 bypass, 60 non-bypass passed → all 80 selected, 0 capped
- `max_4h_fetch_count = 100`, 20 bypass, 100 non-bypass passed → 100 total (20 bypass + 80 non-bypass), 20 capped
- `max_4h_fetch_count = 100`, 100 bypass, 20 non-bypass passed → 100 selected (all bypass), 0 non-bypass selected, 20 capped
- `max_4h_fetch_count = 100`, 130 bypass, 20 non-bypass passed → 130 selected (all bypass), 0 non-bypass selected, 20 capped, total exceeds nominal cap
- `max_4h_fetch_count = 0`, 10 bypass, 50 non-bypass passed → 10 bypass selected, 0 non-bypass, 50 capped
- Cap tie-break: two non-bypass symbols with identical `quote_volume_24h` → symbol ascending lexicographic wins
- Capped symbol retains `matched_filter_rules` originally matched; only `pre_4h_filter_primary_reason` changes to `FILTER_PASSED_BUT_CAPPED`
- Run with identical input data and config produces identical cap outcomes twice

### Integration
- First-seen symbol with unknown listing age and unknown market cap passes pre-1d eligibility if other hard checks pass, proceeds through the chain, and its `mexc_first_tradable_date` is persisted after the 1d-backed derivation stage.
- Symbol fails activity gate with `activity_gate_status = "failed"` → `pre_4h_filter_status = "skipped_activity_gate"`, `pre_4h_filter_primary_reason = "ACTIVITY_GATE_FAILED"`, not present in bypass or filter stages, not selected for 4h fetch.
- Symbol fails activity gate with `activity_gate_status = "not_evaluable"` (e.g., insufficient history) → `pre_4h_filter_status = "skipped_activity_gate"`, `pre_4h_filter_primary_reason = "ACTIVITY_GATE_NOT_EVALUABLE"`, not selected for 4h fetch.
- Symbol passes activity gate, qualifies for monitoring bypass → `pre_4h_filter_status = "skipped_bypass"`, selected for 4h fetch.
- Symbol passes activity gate, does not bypass, passes filter by compression only → selected for 4h fetch, primary reason `FILTER_PASSED_COMPRESSION_1D`.
- Strong-market-day scenario: 200 non-bypass symbols pass filter, `max_4h_fetch_count = 100`, 10 bypass → 100 total selected (10 bypass + 90 non-bypass), 110 capped.
- Audit output in `symbol_run_decisions` and `run_metadata` contains complete per-symbol and per-run diagnostics for all tested scenarios.
- Partial crash scenario: chain interrupted between activity gate and bypass → no partially written `symbol_run_decisions` rows for stages not reached.

### Golden fixture / verification
- If the repo process requires threshold/behavior verification documentation: update `docs/canonical/VERIFICATION_FOR_AI.md` with the exact thresholds and rule semantics from this ticket so later runs can be verified against authoritative values.

## Constraints / Invariants (must not change)

- [ ] Pre-1d eligibility remains pre-OHLCV and does not require fresh 1d/4h OHLCV.
- [ ] `post_1d_activity_gate` remains semantically separate from `pre_4h_candidate_filter`.
- [ ] `pre_4h_candidate_filter` remains an operational budget gate, not a phase/state/score decision layer.
- [ ] No 4h-derived field may be used to decide whether 4h should be fetched.
- [ ] No pullback/reset fields may be used in `pre_4h_candidate_filter`.
- [ ] `failed`, `not_evaluable`, `unknown_pass`, `skipped_bypass`, and `skipped_activity_gate` are not collapsed into each other.
- [ ] Monitoring-bypass symbols always receive 4h in the current daily run.
- [ ] Non-bypass cap ranking is deterministic.
- [ ] All timestamps use UTC consistently (ISO 8601).
- [ ] Closed-bar-only semantics for the activity-gate window.
- [ ] No lookahead.
- [ ] Status enums are closed sets; no new values introduced without a follow-up ticket.
- [ ] Reason-code taxonomy is closed; no new codes introduced without a follow-up ticket.
- [ ] 1 ticket = 1 PR.
- [ ] No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` per "Canonical docs to update"
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if repo workflow requires it for threshold changes
- [ ] Added/updated tests per concrete test specifications
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata

```yaml
created_utc: "2026-04-13T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [1, 2]
gesamtkonzept_ref: "§19 Ticket 3"
related_issues: []
```
