> DRAFT (ticket): Not yet implemented. Canonical truth remains the authoritative source set until merged.

# Title
[P0] Implement execution adapter and grading (Ticket 16)

## Context / Source

This ticket implements **Ticket 16** from the Independence-Release consolidated concept: the **execution adapter + grading** layer.

**Gesamtkonzept reference:** Gesamtkonzept §3 (`execution/`), §19 Ticket 16.

```
depends_on: [12, 15]
```

Formal fachliche dependency is T12 (provides `ExecutionInputContract` read contract and dual-mode T12 architecture). Integration dependency is T15 (provides the execution call-site boundary in `scanner/runners/daily.py` that T16 fills). Both must be implemented before T16 is implemented.

The authoritative fachliche source set for this ticket is:

- the 7 uploaded v2.1 section files (especially Abschnitt 6 §8 and Abschnitt 7 §§12–15)
- `independence_release_gesamtkonzept_final.md`

If current code, existing repo-canonical docs, older ticket assumptions, or existing storage/config contracts conflict with that source set, the authoritative source set wins. Repo documents remain in force only insofar as they do not contradict this source set. Extend the ticket or ask rather than interpret.

The addendum (`v2_1_addendum_for_future_tickets_and_new_chats_updated.md`) is supplemental working context only. It does not constitute a competing authority and must not override the source set above.

**Primary spec references for this ticket:**
- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` §8 (Execution-Daten und Cache-Regel)
- `v2_1_abschnitt_7_entry_pattern_decision_buckets_rev3_aligned.md` §§11–15 (Execution-Einfluss, Priority Score, execution_grade)
- `independence_release_gesamtkonzept_final.md` §3 (`execution/` module), §19 Ticket 16, §21 Question 3

---

### Important framing for this ticket

T16 implements the **execution adapter**: it selects a reduced subset of symbols for orderbook/liquidity evaluation, fetches fresh execution data from the MEXC API for that subset, derives the canonical `ExecutionInputContract` fields by adapting existing liquidity helper output, and integrates the two-pass T12 decision sequence into the daily runner.

T16 is the **authoritative owner** of `ExecutionInputContract` field derivation. T12 declared a read contract for these fields; T16 must populate them and remain backward-compatible with that contract.

T16 introduces **no new fachliche logic** for market phase, state, invalidation, cycle, or entry pattern. Execution influences only bucket assignment, priority score, and presentation priority — not market phase, state, or entry pattern (Abschnitt 7 §15.1).

**Partial resolution of §21/3:** Gesamtkonzept §21 Question 3 ("Execution-Frequenz und Top-N-Regeln") is resolved for the Daily Discovery Scan by this ticket via the Abschnitt 6 §8.2 subset rule. For the Intraday Promotion Scan (T17), §21/3 remains open; T17 must explicitly adopt or adapt the same rule.

---

### Legacy code boundary

`scanner/pipeline/liquidity.py` exists in the repository as a pre-Independence-Release component with tested implementations of spread, depth, VWAP slippage, and tranche-execution logic. For T16:

- Legacy liquidity helper functions **may be called as technical input machinery** to derive the orderbook metrics needed for classification.
- The authoritative output contract is `ExecutionInputContract` with `execution_status`, `execution_grade`, `execution_pass`, `execution_reason` in v2.1 format.
- Legacy statuses (`DIRECT_OK`, `TRANCHE_OK`, `MARGINAL`, `FAIL`, `UNKNOWN`) are inputs to be mapped to v2.1 lowercase equivalents — they are not authoritative final states.
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md` is a technical reference. It is not the fachliche authority for T16. The authoritative source is Abschnitt 6 §8 and Abschnitt 7 §§12–15.

Codex must not carry forward legacy decision semantics, legacy reason-code naming conventions, or legacy output schemas that conflict with the v2.1 contract defined here.

---

### `ExecutionInputContract` model ownership

T12 may already define `ExecutionInputContract` as a typed model. T16 must inspect the existing codebase before implementing:

- If T12 already defines `ExecutionInputContract`: T16 **must import and use** that model. No second definition may be created. No move of the model in this ticket.
- If `ExecutionInputContract` does not yet exist as a typed model: T16 creates it in `scanner/execution/models.py` as the canonical definition, and T12's import is updated to reference it.
- Under no circumstances may two `ExecutionInputContract` definitions coexist after this ticket.

Codex must confirm the current state of `ExecutionInputContract` before choosing which path to implement, and document the chosen path in the PR description.

---

### Two-pass T12 decision sequence in the daily runner

T15 built an explicit execution call-site boundary (returning `None`) in `scanner/runners/daily.py`. T16 fills this boundary by introducing a two-pass decision sequence:

**Pass 1 — Pre-execution T12 (already implemented in T15):**
- T12 runs with `execution_contract=None` for all symbols.
- Symbols that structurally qualify for execution receive `execution_required = True`, `execution_pending = True`.
- This pass produces the pre-execution `DecisionBundle` per symbol.

**Pass 2 — Execution fetch (T16, new):**
- The execution adapter selects the execution subset from Pass 1 results per the §8.2 rule (see Execution subset section).
- For each symbol in the subset: fetch orderbook data from MEXC API; derive `ExecutionInputContract`.
- Symbols where execution evaluation produces `unknown` do not receive an `ExecutionInputContract`; they remain in pre-execution mode for T12.

**Pass 3 — Post-execution T12 (T16 triggers, T12 logic):**
- T12 is called again with `ExecutionInputContract` for each symbol that has one.
- Symbols without `ExecutionInputContract` (including `unknown` outcomes) retain their Pass 1 result with `execution_pending = True`.
- The final ranked output combines both.

**Runner modification:** T16 must update `scanner/runners/daily.py` to implement this two-pass sequence. The change is scoped to wiring the execution adapter into the existing T15 call-site boundary and adding the second T12 call for symbols with contracts. No state re-evaluation, no state re-persistence, no OHLCV re-fetch, no re-running of features/axes/phase.

**`unknown` and `execution_pending` semantics in final output:** When a symbol is selected for execution but produces `unknown`, it retains its Pass 1 T12 result including `execution_pending = True`. This may make the symbol appear as if execution is still pending, when in fact it was attempted but not reliably evaluable. This is the correct behavior given T12's contract (`execution_status` has no `"unknown"` value). The distinction is represented solely in diagnostics: `execution_attempted = True`, `execution_status_raw = "unknown"`, `execution_reason_raw = UNKNOWN_*`. T16 must not mutate T12 output fields outside T12, and must not fabricate a fail contract for `unknown`.

**State invariant:** T16 must not trigger any re-evaluation or re-persistence of state fields (`state_machine_state`, `setup_cycle_id`, `bars_since_*`, etc.).

---

### Execution subset selection (Abschnitt 6 §8.2)

The execution subset for the daily scan is determined as follows. A symbol is selected for execution if it satisfies **at least one** of:

1. `state_machine_state in {"early_ready", "confirmed_ready", "late"}`
2. `market_phase_confidence >= cfg.execution.min_phase_confidence` (default: `60`)
3. `decision_bucket` (from Pass 1) is in the active-bucket set: `{"early_candidates", "confirmed_candidates", "late_monitor"}`

**Hard exclusions (applied before the three conditions above):**
- `state_machine_state in {"rejected", "chased"}` → excluded regardless of phase confidence or bucket.
- `decision_bucket = "discarded"` → excluded regardless of phase confidence or state.

Rationale: `rejected`, `chased`, and `discarded` symbols are operationally non-actionable. Spending API budget on execution evaluation for them is not consistent with the intent of §8.2.

**`watchlist` note:** `watchlist` is not in the active-bucket set, but a `watchlist` symbol may still enter the execution subset if it satisfies condition 1 (state) or condition 2 (confidence). This is intentional per §8.2 and must be explicitly noted in the runner code with a comment.

**No fachlicher Top-N cap:** There is no maximum number of symbols for execution evaluation. If an operational safety limit is needed, it is implemented as an explicit, config-controlled hard-fail guard (see Config section). Absent explicit config, no limit applies.

**Deterministic fetch order:** Symbols in the execution subset are processed in deterministic order: by `priority_score` descending from Pass 1, with symbol alphabetically as tie-break. This order must be stable and reproducible.

---

### Orderbook evaluation and status derivation (Variant A — legacy helpers)

T16 calls existing technical helpers from `scanner/pipeline/liquidity.py` to compute orderbook metrics. The legacy code is used as technical input machinery only. T16 then maps the legacy output to v2.1 `execution_status` per the canonical mapping table below.

**Step 1 — Input validation:**
- Verify orderbook is non-empty, non-stale (within `cfg.execution.orderbook_freshness_max_seconds`), and has finite non-negative values for bid/ask prices and quantities.
- Any NaN, inf, negative, or zero bid/ask → treat as `unknown`; no contract produced.

**Step 2 — Inventory and call legacy helpers:**

Before implementing, Codex must inspect `scanner/pipeline/liquidity.py` and identify the existing helper functions for:
- spread calculation → target output: `spread_pct`
- 1% ask-side depth → target output: `depth_1pct_usd`
- VWAP slippage for a given notional → target output: `slippage_bps_20k` (for `cfg.execution.notional_total_usdt`), `slippage_bps_5k` (for `cfg.execution.notional_chunk_usdt`)
- tranche-execution feasibility → target output: `tradeable_via_tranches`

The PR description must list the exact helper functions chosen for each metric.

**If no suitable helper exists for a required metric:** Codex must stop and explicitly extend this ticket before implementing any new formula logic. No new spread, depth, slippage, or tranche formulas may be introduced in T16 without an explicit ticket extension.

**`cfg.execution` is the sole threshold source:** All parameters passed to legacy helpers must be sourced from the validated `cfg.execution` object — specifically `max_spread_pct`, `min_depth_1pct_usd`, `notional_total_usdt`, `notional_chunk_usdt`, `max_tranches`, `direct_ok_max_slippage_bps`, `tranche_ok_max_slippage_bps`, `marginal_max_slippage_bps`. Legacy helper internal defaults must not be used if they differ from `cfg.execution`. If a helper requires a legacy-style config object, T16 must build that object deterministically from `cfg.execution` fields — it must not pass a raw legacy config dict or rely on legacy default values.

If any helper raises, returns `None` for a required field, or returns non-finite values → treat as `unknown`; no contract produced.

**Step 3 — Legacy-to-v2.1 status mapping:**

The legacy `tradeability_class` values map to v2.1 `execution_status` as follows:

| Legacy `tradeability_class` | v2.1 `execution_status` | `ExecutionInputContract` produced? |
|---|---|---|
| `DIRECT_OK` | `direct_ok` | Yes |
| `TRANCHE_OK` | `tranche_ok` | Yes |
| `MARGINAL` | `marginal` | Yes |
| `FAIL` | `fail` | Yes |
| `UNKNOWN` | — | No (no contract) |

**Step 4 — `execution_reason` derivation:**

`ExecutionInputContract.execution_reason` must be one of the canonical v2.1 reason codes listed below, or `None`. Legacy reason strings from `tradeability_reason_keys` must never be written into `ExecutionInputContract.execution_reason`. They appear only in `execution_reason_raw` in diagnostics.

Derive `execution_reason` from the derived `execution_status` and determining gate condition using the following priority order:

| Condition | `execution_reason` (in contract) |
|---|---|
| `execution_status = direct_ok` | `DIRECT_OK_SPREAD_DEPTH` |
| `execution_status = tranche_ok` | `TRANCHE_OK_SPREAD_DEPTH` |
| `execution_status = marginal`, spread or depth borderline | `MARGINAL_SPREAD_OR_DEPTH` |
| `execution_status = fail`, spread gate failed | `FAIL_SPREAD` |
| `execution_status = fail`, depth gate failed | `FAIL_DEPTH` |
| `execution_status = fail`, slippage threshold exceeded | `FAIL_SLIPPAGE` |
| `execution_status = fail`, determining condition not identifiable | `None` |
| `execution_status = marginal`, determining condition not identifiable | `None` |

**Fallback rule:** If the legacy helper output does not yield a clearly identifiable determining gate condition for a non-`unknown` status, `execution_reason = None`. This is the correct behavior; no legacy string may substitute.

**Diagnostics-only `execution_reason_raw`:**

| Legacy reason key | `execution_reason_raw` |
|---|---|
| `orderbook_data_missing` | `UNKNOWN_ORDERBOOK_MISSING` |
| `orderbook_data_stale` | `UNKNOWN_ORDERBOOK_STALE` |
| fetch failure | `UNKNOWN_FETCH_FAILED` |
| `orderbook_not_in_budget` | `UNKNOWN_ORDERBOOK_MISSING` |
| any legacy string for a produced contract | preserved as-is in diagnostics only |

`UNKNOWN_*` reason codes appear only in `symbol_diagnostics.jsonl.gz`. They are not placed in `ExecutionInputContract.execution_reason`.

---

### `ExecutionInputContract` field derivation

| Field | Type | T16 production rule |
|---|---|---|
| `execution_status` | `Literal["direct_ok", "tranche_ok", "marginal", "fail"]` | Derived per mapping table above |
| `execution_grade` | `float \| None` | Always `None` in v2.1; T12 applies default mapping |
| `execution_pass` | `bool \| None` | `True` for `direct_ok`/`tranche_ok`; `False` for `marginal`/`fail` |
| `execution_reason` | `str \| None` | Canonical v2.1 reason code; `None` if not determinable |

**Canonical mapping table (authoritative):**

| `execution_status` | `execution_pass` | `execution_grade` (T16 output) | T12 effective grade |
|---|---|---|---|
| `direct_ok` | `True` | `None` | `100.0` |
| `tranche_ok` | `True` | `None` | `75.0` |
| `marginal` | `False` | `None` | `40.0` |
| `fail` | `False` | `None` | `0.0` |
| `unknown` | — | — | No contract; no grade |

**`unknown` → no contract:** When execution cannot be reliably evaluated, T16 does not produce an `ExecutionInputContract`. `"unknown"` is not a valid `execution_status` value in T12's contract.

**Critical T12 invariant (non-negotiable):** T12 uses `execution_status` for hard bucket-blocking logic. `execution_pass = False` is shared by both `marginal` and `fail`. Only `execution_status = "fail"` triggers the hard candidate-bucket block. `marginal` with `execution_pass = False` does not block candidate buckets — it lowers `priority_score` only. No code path in T16 or the runner may use `execution_pass == False` as a proxy for `execution_status == "fail"`.

---

### Cache rule (Abschnitt 6 §8.3 — hard invariant)

- Execution data is **not cached** across scan runs for decision purposes.
- Every run in which execution data is needed must fetch it fresh from the MEXC API.
- Stale execution data from prior runs must not be reused as a decision basis.
- Short-lived in-memory deduplication **within the same run** is permitted (each symbol fetched at most once per run).
- Execution data must not be written to any persistent cache (SQLite, Parquet, file) for decision reuse in future runs.
- Execution diagnostic fields in `symbol_diagnostics.jsonl.gz` are for audit only; they must not be read back as a decision cache in any future run.

---

### Orderbook fetch error handling

**`unknown` outcomes (no contract produced):**
- Empty orderbook returned → `unknown`; `UNKNOWN_ORDERBOOK_MISSING` in diagnostics.
- Stale orderbook (beyond `cfg.execution.orderbook_freshness_max_seconds`) → `unknown`; `UNKNOWN_ORDERBOOK_STALE` in diagnostics.
- Fetch failure after retries → `unknown`; `UNKNOWN_FETCH_FAILED` in diagnostics.
- NaN/inf/negative/zero bid-ask prices or quantities → `unknown`.
- Legacy helper raises or returns None for a required metric → `unknown`.
- One symbol's `unknown` outcome does not abort execution fetching for remaining symbols.

**Category 3 — hard run abort:**
- MEXC API returns a total infrastructure failure for all orderbook requests (not individual symbol timeouts) → Category 3 per T15 policy. `run_metadata.status = 'failed'`.
- Config validation failure at load time → Category 3 before any fetch.

**Distinction:** Individual symbol failures are `unknown` outcomes (no contract). Shared infrastructure failures are Category 3. An empty or stale orderbook for one symbol is `unknown`, not Category 3.

---

### Config semantics (`cfg.execution`)

T16 introduces the `cfg.execution` config block. **Config semantics:** missing keys use defaults (not invalid); partial overrides are merged field-by-field with defaults (Merge, not Replace); invalid types or out-of-range values raise `ValueError` at config load time naming the offending key; no ad-hoc raw-dict fallbacks inside execution logic.

| Field | Default | Type | Constraint |
|---|---|---|---|
| `min_phase_confidence` | `60` | `float` | `[0, 100]` |
| `orderbook_depth_levels` | `20` | `int` | `> 0` |
| `orderbook_freshness_max_seconds` | `300` | `int` | `> 0` |
| `fetch_timeout_seconds` | `10` | `int` | `> 0` |
| `fetch_max_retries` | `2` | `int` | `>= 0` |
| `max_spread_pct` | `0.15` | `float` | `> 0` |
| `min_depth_1pct_usd` | `200_000` | `float` | `> 0` |
| `notional_total_usdt` | `20_000` | `float` | `> 0` |
| `notional_chunk_usdt` | `5_000` | `float` | `> 0` |
| `max_tranches` | `4` | `int` | `> 0` |
| `direct_ok_max_slippage_bps` | `50` | `float` | `> 0` |
| `tranche_ok_max_slippage_bps` | `100` | `float` | `> 0` |
| `marginal_max_slippage_bps` | `150` | `float` | `> 0` |
| `execution_safety_limit` | `null` | `int \| null` | `> 0` if set; `null` = no limit |

**`execution_safety_limit` semantics:** If set and the execution subset exceeds this value, the run aborts as Category 3 (hard fail). This is a hard-fail guard — there is no soft-warning mode. If not set (`null`), no limit applies.

---

### Diagnostics

T16 extends `symbol_diagnostics.jsonl.gz` with execution diagnostic fields. Before adding these fields, Codex must inspect the existing T13 diagnostics schema in `scanner/output/schema.py` (or equivalent T13 schema file) and confirm the extension path. If T13's schema already defines an extension mechanism for per-symbol diagnostic blocks, use it. If not, the schema extension must be added explicitly to T13's schema as part of this ticket's scope.

Required diagnostic fields per symbol where execution was attempted:

| Field | Type | Value |
|---|---|---|
| `execution_attempted` | `bool` | `True` for all symbols where T16 attempted a fetch |
| `execution_status_raw` | `str` | `"direct_ok"` / `"tranche_ok"` / `"marginal"` / `"fail"` / `"unknown"` |
| `execution_reason_raw` | `str \| None` | Full reason code including `UNKNOWN_*`; `None` if not available |
| `execution_pass` | `bool \| None` | Per canonical mapping; `None` for `unknown` |
| `execution_grade_t16` | `null` | Always `null` in v2.1 (documents that T16 does not supply a finer score) |
| `execution_fetch_duration_ms` | `int` | Fetch duration in milliseconds |

Symbols outside the execution subset have `execution_attempted = False`; all other execution diagnostic fields are `null` for these symbols.

---

## Goal

After this ticket is completed:

- `scanner/execution/adapter.py` implements `evaluate_execution_subset(symbols, pre_execution_decisions, cfg) -> dict[str, ExecutionInputContract]`
- `scanner/execution/grading.py` implements the legacy-to-v2.1 mapping and `unknown` determination
- `ExecutionInputContract` has exactly one definition after this ticket; T16 imports the existing T12 model if present, otherwise defines it in `scanner/execution/models.py` and updates T12 to import that same class
- `scanner/runners/daily.py` implements the two-pass T12 sequence via the T15 call-site boundary
- No state re-evaluation or re-persistence occurs in T16
- `execution_grade = None` for all T16-produced contracts; T12 applies the default mapping
- `execution_pass` follows the canonical mapping; `unknown` produces no contract
- T12's hard bucket-blocking uses `execution_status`, not `execution_pass` alone
- Execution subset selected per §8.2 with hard exclusions for `rejected`, `chased`, `discarded`
- `watchlist` may enter subset via state/confidence rule, not via active-bucket membership
- Fetch order is deterministic: `priority_score` descending, symbol alphabetically as tie-break
- No persistent execution cache; in-run in-memory deduplication is permitted
- `cfg.execution` block is validated at load time with Merge semantics
- `symbol_diagnostics.jsonl.gz` extended with execution diagnostic fields per T13 schema
- T13 schema updated to include execution diagnostic fields if not already present
- No `ExecutionInputContract` duplicate definition exists after this ticket
- §21/3 is partially resolved for Daily; open for Intraday/T17

---

## Scope

Allowed change surface:

- `scanner/execution/adapter.py` (new) — subset selection and `ExecutionInputContract` production
- `scanner/execution/grading.py` (new) — legacy helper invocation, mapping, and `unknown` determination
- `scanner/execution/models.py` (new only if `ExecutionInputContract` does not already exist; otherwise import from T12 location)
- `scanner/execution/__init__.py` (new, if needed)
- `scanner/runners/daily.py` — wire two-pass T12 sequence into T15 call-site boundary; no other runner architecture changes
- `scanner/config.py` or central config accessor — add `cfg.execution` block with all fields, Merge semantics, validation
- `scanner/output/schema.py` or equivalent T13 schema file — extend diagnostics schema for execution fields (only if T13 schema requires explicit extension)
- `tests/**` — add tests per Tests section
- `docs/canonical/DATA_MODEL.md` — document `ExecutionInputContract` fields, canonical mapping table, `unknown`→no-contract rule, `execution_pending` semantics for `unknown` symbols
- `docs/canonical/open_questions.md` — mark §21/3 as partially resolved (Daily); open for Intraday/T17
- `docs/canonical/ARCHITECTURE.md` — update only if this file exists
- `docs/canonical/GLOSSARY.md` — update only if this file exists

Do not create new canonical doc files unless already established in the repo. Do not manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

## Out of Scope

This ticket must not:

- implement the intraday runner → Ticket 17
- resolve §21/3 for Intraday → Ticket 17
- implement a finer `execution_grade` numeric score → `feature_enhancements.md`
- re-evaluate or re-persist state fields
- re-fetch OHLCV or re-run features/axes/phase
- implement persistent execution cache for cross-run decision reuse
- pass `"unknown"` as `execution_status` in any `ExecutionInputContract`
- create a second `ExecutionInputContract` definition if one already exists
- move `ExecutionInputContract` model between modules without explicit full import-migration in-scope
- implement evaluation, replay, or forward-return logic → Ticket 18
- implement GitHub Actions scheduling → Ticket 19
- introduce a soft-warning mode for `execution_safety_limit` (hard fail only)
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority:

- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` — §8 (Execution-Daten und Cache-Regel)
- `v2_1_abschnitt_7_entry_pattern_decision_buckets_rev3_aligned.md` — §§11–15
- `independence_release_gesamtkonzept_final.md` — §3, §19 Ticket 16, §21 Question 3

Upstream contracts (read-only):

- Ticket 12 — `ExecutionInputContract` read contract, dual-mode architecture, `execution_status` hard-block invariant
- Ticket 15 — `scanner/runners/daily.py` execution call-site boundary, Category 2/3 error policy

Legacy technical reference (not fachliche authority):

- `scanner/pipeline/liquidity.py` — technical helper functions for orderbook metrics
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md` — technical reference for legacy status taxonomy

Supplemental context: `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`

Repo process references (conditional on existence): `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST_updated.md`, `docs/canonical/WORKFLOW_CODEX.md`

---

## Proposed Change (high-level)

### Before

- `scanner/runners/daily.py` has an execution call-site boundary returning `None`; T12 runs only in pre-execution mode.
- No `scanner/execution/` module exists.
- §21/3 is open.

### After

- `scanner/execution/adapter.py` selects the subset per §8.2 (with hard exclusions) and produces `ExecutionInputContract` per symbol by adapting legacy helper output.
- `scanner/execution/grading.py` maps legacy tradeability output to v2.1 status/pass/reason.
- `scanner/runners/daily.py` implements the two-pass T12 sequence.
- Symbols with a produced `ExecutionInputContract` receive post-execution T12 results.
- `unknown` symbols retain Pass 1 results; their outcome is represented in diagnostics only.
- T12's hard block is driven by `execution_status = "fail"`, not by `execution_pass = False`.
- §21/3 partially resolved for Daily.

---

## Acceptance Criteria

1. `scanner/execution/adapter.py` exists and implements `evaluate_execution_subset(symbols, pre_execution_decisions, cfg) -> dict[str, ExecutionInputContract]`.
2. `scanner/execution/grading.py` exists and maps legacy tradeability output to v2.1 `execution_status`, `execution_pass`, `execution_reason`.
3. Only one `ExecutionInputContract` definition exists after this ticket. Codex documents in the PR description whether T12's existing model was imported or a new model was created. If newly created, the model must exactly match the T12 read contract; T12 must import this class; tests must assert both modules reference the same type.
4. The PR description lists the exact helper functions from `scanner/pipeline/liquidity.py` used for spread, depth, slippage (20k and 5k), and tranche feasibility. No new spread/depth/slippage/tranche formula logic is introduced without explicit ticket extension. New validation and adapter-control logic (input validation, null/NaN/inf checks, stale-detection, error classification) is in scope.
5. All parameters passed to legacy helpers are sourced exclusively from validated `cfg.execution`. No legacy helper default values are used for spread, depth, slippage, or notional thresholds.
6. `scanner/runners/daily.py` implements the two-pass T12 sequence via the T15 call-site boundary. No other runner architecture changes.
7. No state re-evaluation or state re-persistence occurs in T16 code paths.
8. Hard exclusions are enforced: `state_machine_state in {"rejected", "chased"}` and `decision_bucket = "discarded"` are excluded from the execution subset regardless of phase confidence.
9. Execution subset selection follows §8.2: `state in {"early_ready", "confirmed_ready", "late"}` OR `market_phase_confidence >= cfg.execution.min_phase_confidence` OR `decision_bucket in {"early_candidates", "confirmed_candidates", "late_monitor"}` — minus the hard exclusions above.
10. `watchlist` may enter the subset via the state or confidence condition; it is not in the active-bucket set.
11. Fetch order is deterministic: `priority_score` descending (Pass 1 values), symbol alphabetically as tie-break.
12. Legacy-to-v2.1 status mapping follows the canonical table: `DIRECT_OK→direct_ok`, `TRANCHE_OK→tranche_ok`, `MARGINAL→marginal`, `FAIL→fail`, `UNKNOWN→no contract`.
13. `execution_grade = None` for all produced contracts. T12 applies the default mapping.
14. `execution_pass = True` for `direct_ok`/`tranche_ok`; `False` for `marginal`/`fail`.
15. `unknown` outcomes do not produce an `ExecutionInputContract`. Symbol retains Pass 1 result with `execution_pending = True`. Diagnostics for that symbol include `execution_attempted = True` and `execution_status_raw = "unknown"` to disambiguate from symbols where execution was not attempted.
16. `"unknown"` is not passed as `execution_status` in any `ExecutionInputContract`.
17. T12's post-execution call uses `execution_status` for hard bucket-blocking. No code path uses `execution_pass == False` as proxy for `execution_status == "fail"`. `marginal` does not block candidate buckets.
18. `ExecutionInputContract.execution_reason` contains only canonical v2.1 reason codes or `None`. No legacy reason strings appear in the contract field.
19. Empty, stale, and invalid orderbooks → `unknown`; no contract; appropriate `UNKNOWN_*` code in diagnostics.
20. Fetch failure after retries → `unknown`; no contract; `UNKNOWN_FETCH_FAILED` in diagnostics.
21. NaN/inf/negative/zero values in orderbook → `unknown`; no contract.
22. One symbol's failure does not abort execution fetching for remaining symbols.
23. Total MEXC API infrastructure failure → Category 3 abort per T15 policy.
24. No execution data written to any persistent cache for cross-run reuse.
25. In-run in-memory deduplication (at most one fetch per symbol per run) is permitted.
26. `cfg.execution` block validated at config load time: missing keys use defaults; invalid types/values raise `ValueError` naming the key; merge semantics. `min_phase_confidence` outside `[0, 100]` raises `ValueError`. `execution_safety_limit = 0` or negative raises `ValueError`.
27. If `execution_safety_limit` is set and the subset exceeds it, the run aborts as Category 3. No soft-warning mode.
28. Codex inspects existing T13 diagnostics schema before adding execution fields. If T13 schema requires explicit extension, it is added in-scope. `symbol_diagnostics.jsonl.gz` contains execution diagnostic fields per the Diagnostics section. `execution_fetch_duration_ms` is `int >= 0` for all attempted symbols (including failed attempts where a fetch was initiated); `null` for non-attempted symbols.
29. `docs/canonical/DATA_MODEL.md` documents `ExecutionInputContract` fields, canonical mapping table, `unknown`→no-contract rule, and `execution_pending = True` semantics for `unknown` symbols.
30. `docs/canonical/open_questions.md` marks §21/3 as partially resolved (Daily); notes open for Intraday/T17.

---

## Default-/Edgecase-Abdeckung

- **`unknown` → no contract:** ✅ (AC: #15, #16; symbol retains Pass 1; diagnostics disambiguate)
- **`rejected`/`chased` hard-excluded:** ✅ (AC: #8; regardless of confidence)
- **`discarded` hard-excluded:** ✅ (AC: #8; regardless of confidence)
- **`watchlist` via state/confidence only:** ✅ (AC: #10; not via active-bucket set)
- **`marginal` ≠ `fail` in bucket logic:** ✅ (AC: #17; `execution_status` drives hard block)
- **`execution_pass = False` shared by `marginal`/`fail`:** ✅ (AC: #14, #17; differentiated by `execution_status`)
- **`execution_grade = None` from T16:** ✅ (AC: #13; T12 applies default mapping)
- **Empty/stale/invalid orderbook → `unknown`:** ✅ (AC: #19)
- **Fetch failure → `unknown`:** ✅ (AC: #20)
- **NaN/inf/negative values → `unknown`:** ✅ (AC: #21)
- **One symbol fails, others continue:** ✅ (AC: #22)
- **Total API failure → Category 3:** ✅ (AC: #23)
- **No persistent cache:** ✅ (AC: #24)
- **In-run deduplication permitted:** ✅ (AC: #25)
- **Deterministic fetch order:** ✅ (AC: #11)
- **No fachlicher Top-N-Cap:** ✅ (safety limit = hard fail only; AC: #27)
- **No state re-evaluation:** ✅ (AC: #7)
- **Single `ExecutionInputContract` definition:** ✅ (AC: #3)
- **execution_reason only canonical codes or None:** ✅ (AC: #18)
- **Config missing key → default:** ✅ (AC: #26)
- **Config invalid type → `ValueError`:** ✅ (AC: #26)
- **min_phase_confidence > 100 → `ValueError`:** ✅ (AC: #26)
- **Safety limit hard-fail only:** ✅ (AC: #27)
- **T13 schema confirmed before extension:** ✅ (AC: #28)
- **§21/3 partial resolution:** ✅ (AC: #30; Daily only)

---

## Tests

### Unit tests

- `test_hard_exclude_rejected` — symbol with `state = "rejected"` and high confidence is not selected for execution subset
- `test_hard_exclude_chased` — symbol with `state = "chased"` is not selected regardless of confidence
- `test_hard_exclude_discarded` — symbol with `decision_bucket = "discarded"` is not selected regardless of confidence
- `test_subset_state_rule` — `state in {"early_ready", "confirmed_ready", "late"}` → selected
- `test_subset_confidence_rule` — `market_phase_confidence >= 60` → selected even if bucket is `watchlist`
- `test_subset_active_bucket_rule` — `decision_bucket in {"early_candidates", "confirmed_candidates", "late_monitor"}` → selected
- `test_watchlist_not_active_bucket` — `watchlist` without state/confidence trigger → not selected
- `test_fetch_order_deterministic` — identical inputs → identical fetch order across multiple calls
- `test_mapping_direct_ok` — legacy `DIRECT_OK` → `execution_status = "direct_ok"`, `execution_pass = True`, `execution_grade = None`
- `test_mapping_tranche_ok` — legacy `TRANCHE_OK` → `tranche_ok`, `True`, `None`
- `test_mapping_marginal` — legacy `MARGINAL` → `marginal`, `False`, `None`
- `test_mapping_fail` — legacy `FAIL` → `fail`, `False`, `None`
- `test_mapping_unknown_no_contract` — legacy `UNKNOWN` → no `ExecutionInputContract` produced
- `test_empty_orderbook_unknown` — empty orderbook → `unknown`; no contract; `UNKNOWN_ORDERBOOK_MISSING` in diagnostics
- `test_stale_orderbook_unknown` — stale orderbook → `unknown`; `UNKNOWN_ORDERBOOK_STALE`
- `test_fetch_failure_unknown` — fetch fails after retries → `unknown`; `UNKNOWN_FETCH_FAILED`
- `test_nan_in_orderbook_unknown` — NaN bid price → `unknown`
- `test_marginal_does_not_block_candidate_bucket` — post-execution T12 with `marginal` does not move `early_candidates` to `late_monitor`
- `test_fail_blocks_candidate_bucket` — post-execution T12 with `fail` moves `early_candidates` out
- `test_one_symbol_failure_does_not_abort` — one symbol raises network error; remaining symbols processed
- `test_no_persistent_cache_write` — after execution fetch, no data written to SQLite or Parquet
- `test_execution_grade_none_from_t16` — all produced contracts have `execution_grade = None`
- `test_config_missing_key_uses_default` — missing `cfg.execution.min_phase_confidence` → default 60
- `test_config_invalid_type_raises` — `cfg.execution.max_spread_pct = "bad"` → `ValueError`
- `test_config_safety_limit_zero_raises` — `cfg.execution.execution_safety_limit = 0` → `ValueError`
- `test_config_safety_limit_negative_raises` — `cfg.execution.execution_safety_limit = -1` → `ValueError`
- `test_config_min_phase_confidence_above_100_raises` — `cfg.execution.min_phase_confidence = 101` → `ValueError`
- `test_shared_execution_contract_type` — assert that the `ExecutionInputContract` class used in `scanner/execution/adapter.py` and the class imported/used in T12's decision logic are the same type object (identity check); no duplicate class definitions
- `test_execution_reason_never_uses_legacy_string` — produce a contract with `execution_status = "fail"`; assert `execution_reason` is one of the canonical v2.1 codes or `None`; assert no legacy reason string appears in `execution_reason`
- `test_execution_reason_unknown_gate_returns_none` — simulate a case where the determining gate is not identifiable from helper output; assert `execution_reason = None`
- `test_execution_reason_fail_spread_maps_correctly` — simulate spread gate failure; assert `execution_reason = "FAIL_SPREAD"`
- `test_unknown_reason_codes_diagnostics_only` — simulate `unknown` outcome; assert `UNKNOWN_*` code appears in `execution_reason_raw` in diagnostics; assert `ExecutionInputContract` is not produced (no contract in output)

### Integration tests

- **Two-pass T12 sequence:** Mocked orderbook data for subset; assert Pass 3 results differ from Pass 1 for symbols with contracts; assert symbols without contracts retain Pass 1 result with `execution_pending = True`; assert `unknown` symbols retain Pass 1 result
- **Post-execution default mapping:** Symbols with `direct_ok` contract have effective `priority_score` using 4-factor formula with `execution_grade = 100.0`; `marginal` uses `40.0`; `fail` does not appear in candidate buckets
- **Diagnostics conformance:** `symbol_diagnostics.jsonl.gz` contains `execution_attempted`, `execution_status_raw`, `execution_reason_raw`, `execution_pass`, `execution_grade_t16`, `execution_fetch_duration_ms` for subset symbols; non-subset symbols have `execution_attempted = False`
- **Determinism:** Two identical runs with identical mocked orderbooks produce identical `ExecutionInputContract` mapping, identical subset, identical final ranking

---

## Constraints / Invariants (must not change)

- [ ] `ExecutionInputContract.execution_status` is `Literal["direct_ok", "tranche_ok", "marginal", "fail"]` — never `"unknown"`
- [ ] `unknown` outcomes produce no `ExecutionInputContract`
- [ ] `execution_pass = True` only for `direct_ok`/`tranche_ok`; `False` for `marginal`/`fail`
- [ ] `execution_grade = None` for all T16-produced contracts in v2.1
- [ ] T12 hard bucket-blocking uses `execution_status`, not `execution_pass` alone
- [ ] `marginal` does not block candidate buckets
- [ ] `rejected`, `chased`, `discarded` hard-excluded from execution subset regardless of confidence
- [ ] No state re-evaluation or re-persistence in T16 code paths
- [ ] No persistent execution cache for cross-run reuse
- [ ] Fetch order is deterministic
- [ ] Active bucket set: `{"early_candidates", "confirmed_candidates", "late_monitor"}`
- [ ] `cfg.execution`: missing key → default; invalid type/value → `ValueError`; Merge semantics
- [ ] `execution_safety_limit`: hard-fail only; no soft-warning mode
- [ ] Single `ExecutionInputContract` definition after this ticket
- [ ] `ExecutionInputContract.execution_reason` contains only canonical v2.1 reason codes or `None`; no legacy reason strings
- [ ] Legacy helper defaults not used; all thresholds sourced from `cfg.execution`
- [ ] Helper functions inventoried and documented in PR; no new formulas without ticket extension
- [ ] §21/3 partially resolved (Daily only); open for Intraday/T17
- [ ] No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`
- [ ] 1 ticket = 1 PR

---

## Definition of Done (Codex must satisfy)

(Reference: `docs/canonical/WORKFLOW_CODEX.md` if this file exists in the repo)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] `scanner/execution/adapter.py`, `scanner/execution/grading.py` implemented
- [ ] `ExecutionInputContract` model: either imported from T12 or newly created in `scanner/execution/models.py`; PR describes which path was taken
- [ ] `scanner/runners/daily.py` updated for two-pass T12 sequence
- [ ] `cfg.execution` block added and validated
- [ ] T13 diagnostics schema inspected; execution diagnostic fields added in-scope if needed
- [ ] All tests per Tests section added
- [ ] `docs/canonical/DATA_MODEL.md` updated: `ExecutionInputContract` fields, mapping table, `unknown`→no-contract, `execution_pending` semantics
- [ ] `docs/canonical/open_questions.md` §21/3 marked partially resolved (Daily); open for Intraday/T17
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata

```yaml
created_utc: "2026-04-24T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [12, 15]
gesamtkonzept_ref: "§19 Ticket 16"
partially_resolves_open_questions:
  - "§21/3: Execution-Frequenz und Top-N-Regeln — resolved for Daily Discovery Scan only; open for Intraday/T17"
related_issues: []
follow_ups:
  - "Ticket 17: intraday runner — must explicitly adopt §8.2 subset rule; §21/3 remains open for intraday until T17"
  - "feature_enhancements.md: finer execution_grade numeric score based on slippage bps"
```
