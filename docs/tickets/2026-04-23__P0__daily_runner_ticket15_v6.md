> DRAFT (ticket): Not yet implemented. Canonical truth remains the authoritative source set until merged.

# Title
[P0] Implement daily runner and resolve OQ3 (`daily_bar_id` type harmonization) (Ticket 15)

## Context / Source

This ticket implements **Ticket 15** from the Independence-Release consolidated concept: the **daily runner** (`daily_discovery_scan`).

**Gesamtkonzept reference:** Gesamtkonzept §10 (Daily Discovery Scan steps 1–14), §19 Ticket 15, §20 Festlegungen 1–6.

```
depends_on: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
```

The authoritative fachliche source set for this ticket is:

- the 7 uploaded v2.1 section files (especially Abschnitt 6)
- `independence_release_gesamtkonzept_final.md`

If current code, existing repo-canonical docs, older ticket assumptions, or existing storage/config contracts conflict with that source set, the authoritative source set wins. Repo documents remain in force only insofar as they do not contradict this source set. Extend the ticket or ask rather than interpret.

The addendum (`v2_1_addendum_for_future_tickets_and_new_chats_updated.md`) is supplemental working context only. It does not constitute a competing authority and must not override the source set above.

**Primary spec references for this ticket:**
- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` §§1–2, §§9–15
- Gesamtkonzept §§7, 10, 19

---

### Important framing for this ticket

This ticket implements the **daily runner** — the first full-pipeline integration of all upstream fachliche modules (T3–T12) and infrastructure modules (T13–T14) into a single, deterministic, closed-bar-only daily discovery scan. It introduces no new fachliche logic. Every computation is performed by previously implemented modules; this ticket is solely responsible for their correct invocation sequence, data flow, state lifecycle, and output production.

T15 additionally resolves **Open Question OQ3** (`daily_bar_id` type harmonization) as an explicitly authorized architectural repair carried in this ticket. This resolution is not a side effect — it is a named deliverable of T15.

---

### OQ3 resolution: `daily_bar_id` type harmonization

**This ticket explicitly resolves OQ3.**

`daily_bar_id` is canonicalized to `str` in `YYYY-MM-DD` format across all affected typed layer contracts and output-facing contracts within the daily-runner call graph and its directly dependent contracts.

**Primary affected models:**

- `Tier1AxisBundle` — `daily_bar_id: int` → `daily_bar_id: str`
- `Tier2AxisBundle` — `daily_bar_id: int` → `daily_bar_id: str`
- `PhaseInterpretationBundle` — `daily_bar_id: int` → `daily_bar_id: str`

**Full scope of required changes (all in the same PR):**

Beyond the three typed models above, Codex must also update any directly dependent serializers, validators, fixtures, and diagnostics helpers that currently enforce or expect `daily_bar_id` as `int`. The invariant is: no code path within the daily-runner call graph and its directly dependent contracts may produce or consume `daily_bar_id` as `int` after this ticket. Codex must audit the full call graph from `run_daily_scan` and correct all occurrences found there. This is not a repo-wide cleanup directive; it is scoped to the daily runner and the contracts it directly depends on.

**Canonical doc updates required in the same PR:**

- `docs/canonical/DATA_MODEL.md` must be updated to declare `daily_bar_id: str (YYYY-MM-DD)` as the canonical cross-layer type.
- `docs/canonical/open_questions.md` OQ3 must be marked as resolved by this ticket.

**No dual representation may remain after this ticket.** No ad-hoc conversion bridges between `int` and `str` representations are permitted anywhere in the daily-runner call graph and its directly dependent contracts.

Rationale: `daily_bar_id` is a provenance/traceability field in all affected bundles. It does not drive any fachliche computation. Type harmonization carries zero regression risk on computed outputs and eliminates a known cross-layer inconsistency before it propagates into T16/T17/T18.

---

### Module architecture

**New file:** `scanner/runners/daily.py` — the canonical daily runner for the Independence-Release architecture.

**Modified file:** `scanner/main.py` — updated to invoke `scanner.runners.daily.run_daily_scan()` instead of the legacy orchestrator.

**Legacy isolation (explicit, decided in this ticket):** `scanner/pipeline/__init__.py` (existing `run_pipeline` function) is the legacy orchestrator from the pre-Independence-Release pipeline. As part of this ticket, it must be explicitly marked as non-authoritative by adding a module-level docstring:

```python
"""
LEGACY — non-authoritative for Independence-Release logic.
This module is the pre-Independence-Release pipeline orchestrator.
Do not use for Independence-Release flows. See scanner/runners/daily.py.
"""
```

The legacy file is **not deleted** in this ticket. Deleting it and verifying all README/Onboarding/Authority docs are consistent is deferred to a dedicated cleanup ticket. What this ticket guarantees:
- `scanner/main.py` no longer calls `run_pipeline()` from this module.
- No Independence-Release code path in `scanner/runners/` imports from `scanner/pipeline/__init__.py`.
- The legacy docstring is in place.

---

### Pre-execution mode

T16 (execution adapter) is not yet implemented. T15 therefore operates exclusively in **pre-execution mode** as defined by T12:

- No `ExecutionInputContract` is passed to `assign_bucket(...)`.
- T12 assigns buckets using structural conditions only.
- `execution_required = True` and `execution_pending = True` are set on qualifying coins by T12 (this is T12 behavior, not T15 behavior).

**Execution call-site boundary:** T15 must define an explicit, named call-site in the runner where the T16 execution adapter would be invoked. This boundary:
- is a no-op in the T15 implementation (returns `None`),
- is clearly marked: `# Execution adapter call-site — Ticket 16. Returns None in pre-execution mode.`,
- does not prescribe the T16 function signature, which is not yet authoritatively defined.

This boundary is not optional. It ensures T16/T17 can integrate at the correct location without restructuring the runner.

**BTC regime:** T15 passes `btc_regime=None` to T12 in all cases. No BTC regime computation is performed in this ticket. No legacy `scanner/pipeline/regime.py` fallback is used. T12 tolerates `None` per its contract.

---

### Daily runner: pipeline execution sequence

The daily runner implements the `daily_discovery_scan` as specified in Gesamtkonzept §10 and Abschnitt 6 §10.1. The canonical layer invocation order is:

**Phase 1 — Universe and eligibility (T3, T4)**
1. Resolve the eligible universe: pre-1d eligibility gate, market data fetch, activity gate.
2. Run monitoring bypass check per symbol.
3. Fetch 1d OHLCV for all eligible symbols (T4).
4. Run `pre_4h_candidate_filter` for non-bypass symbols (T3). Result: set of symbols selected for 4h fetch. This filter is an operational budget gate only — not a fachlicher Verwerfer. Symbols not selected receive no 4h data this run but are not fachlich excluded.
5. Fetch 4h OHLCV for selected symbols (T4).

**Phase 2 — Feature computation (T5/T5.1)**
6. Compute `FeatureBundle` per symbol (T5/T5.1). Symbols without 4h data: `data_4h_available = False`; 1d-fallback path applies in T7/T8.

**Phase 3 — Axes (T6, T7)**
7. Compute `Tier1AxisBundle` per symbol (T6). All 6 Tier-1 axes computed.
8. Compute `Tier2AxisBundle` per symbol (T7). Two-path model applies.

**Phase 4 — Phase interpretation (T8)**
9. Compute `PhaseInterpretationBundle` per symbol (T8).

**Phase 5 — State lifecycle (T9, T10)**
10. Load persisted state from SQLite per symbol using the T10 persistence read contract. State is loaded after phase computation (steps 6–9) because T9/T10 require `PhaseInterpretationBundle` as input. Missing state → no-backfill rule applies (Abschnitt 6 §9.4).
11. Evaluate invalidation and cycle detection per symbol (T9).
12. Evaluate state machine transitions per symbol (T10). Persist state via the canonical T10 state persistence write interface. `delta_closed_bars_relevant = 6` (T1 constant `DAILY_SCAN_DELTA_BARS`). State write must complete before any output write for that symbol.

**Phase 6 — Entry patterns (T11)**
13. Compute `EntryPatternBundle` per symbol (T11). Invoked unconditionally for all symbols with a valid `PhaseInterpretationBundle`. No config flag conditions this invocation.

**Phase 7 — Execution call-site boundary (stub)**
14. Invoke execution call-site boundary (returns `None`). No `ExecutionInputContract` produced.

**Phase 8 — Decision (T12)**
15. Invoke `assign_bucket(phase_bundle, state_bundle, entry_bundle, cfg, execution_contract=None)` per symbol (T12, pre-execution mode).
16. Invoke `rank_coins(decisions, cfg)` on the full result set (T12).

**Phase 9 — Output production (T13, T14)**
17. Serialize `RankedDecision` list to run-internal in-memory representation.
18–23. See Publish sequence section.

---

### State persistence: read/write contract

State persistence is a fachlicher correctness requirement (Abschnitt 6 §9.3, §15).

**Per-symbol state read (step 10, before T9/T10 invocation):**
- Executed after T8 outputs are available, before T9 evaluation.
- If no prior state exists: all persistence-dependent fields are `null`. No backfill, no inference (Abschnitt 6 §9.4).
- If state reflects a prior cycle: use as-is; T9/T10 handles stale-state cases.

**Per-symbol state write (step 12, after T10 evaluation):**
- The canonical T10 state persistence write interface is the only permitted writer of `state_machine_state`, `setup_cycle_id`, `cycle_end_bar_index`, `cycle_end_timestamp`, and all `bars_since_*` counters.
- T15 invokes the T10 write interface. T15 must not write state fields directly.
- **The T10 state write interface must be atomic per symbol: either fully committed or fully rolled back. No partial state mutation may remain persisted after a write failure.**
- State write must complete before any output write for that symbol.
- If the T10 write interface raises for a symbol: that symbol is treated as a Category 2 controlled failure (see Error handling). Partial state writes are not acceptable.

---

### Publish sequence, index atomicity, and publishable runs

The canonical rule from Gesamtkonzept §7.3 (Festlegung 3): **`reports/index/` is updated atomically only after the run is fully written.**

#### Publishable vs. non-publishable runs

Not every completed run updates the index. A run is **publishable** only if it produced a non-empty symbol result set. An empty-universe run (see Error handling, Category: Empty universe) is **not publishable**: it completes with `status = 'completed'` but follows a minimal artifact path, not the full publish sequence. This is an explicit exception and must be documented in the runner code with a comment.

**Non-publishable run minimal artifact contract:**

| Artifact | Non-publishable run |
|---|---|
| `run_metadata` (`status = 'completed'`, `finished_at_utc`) | **must write** |
| `reports/runs/YYYY/MM/DD/<run_id>/report.json` (minimal, `candidate_count = 0`) | **must write** |
| `reports/daily/YYYY/MM/DD/report.json` | **must not write** |
| `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json` | **must not write** |
| `symbol_diagnostics.jsonl.gz` | **must not write** |
| Parquet history partitions | **must not write** |
| `reports/index/` files (any) | **must not write** |
| `recent_runs.json` | **must not write** |

Rationale: the run-scoped `report.json` is written for operational auditability (evidence that the run executed and found zero symbols). All other artifacts are either meaningless without candidates or would corrupt the index with a zero-candidate run.

#### Publish sequence (publishable runs only)

1. **Write run-scoped report artifacts** (T13 writers): `reports/runs/YYYY/MM/DD/<run_id>/report.json`, `symbol_diagnostics.jsonl.gz`. Written first, independently of the index.
2. **Write daily report artifact** (T13 writers): `reports/daily/YYYY/MM/DD/report.json`.
3. **Write snapshot manifest** (T14 writers): `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`. This is the canonical manifest location (Gesamtkonzept §7.4 Festlegung 4). No second copy under `reports/runs/`.
4. **Write Parquet history partitions** (T14 writers): `snapshots/history/ohlcv/<timeframe>/<symbol>/YYYY/MM/` per T14 contract. Note: T14 defines this as the canonical Parquet path. OQ2 (long-term OHLCV history storage architecture) remains open and is not resolved by this ticket; T14 Parquet writes are used as-is per T14's established contract.
5. **Publish index files atomically**: Only after steps 1–4 complete with no write-level errors. All `reports/index/` files are written using stage-then-rename (`os.replace()`). Required per Gesamtkonzept §7.3: `latest_run.txt`, `latest_paths.json`, `latest.json`, `latest_daily.json`, `latest_confirmed_candidates.json`, `latest_watchlist.json`, `recent_runs.json`. Optional: `latest_manifest.json`.
6. **Write `run_metadata` terminal status**: `status = 'completed'`, `finished_at_utc`.

**Invariant:** Index files must never point to a partially written or failed run. If any step in 1–4 fails with a write-level error, step 5 must not execute.

---

### `run_metadata` write contract

T1 defines the `run_metadata` SQLite table. T1's Acceptance Criteria (AC 11) establish the canonical enum values: `scan_mode` accepts exactly `daily_discovery` and `intraday_promotion`. Abschnitt 6 uses `daily_discovery_scan` as a conceptual mode label; that label is not the SQLite enum value.

**At run start (before any symbol processing):**
```
status          = 'running'
scan_mode       = 'daily_discovery'    ← T1 AC-11 enum value
daily_bar_id    = '<YYYY-MM-DD>'       ← str
intraday_bar_id = null
started_at_utc  = <UTC ISO 8601>
finished_at_utc = null
```

**At run completion:**
```
status          = 'completed'
finished_at_utc = <UTC ISO 8601>
```

**At hard failure (`finally` block):**
```
status          = 'failed'
finished_at_utc = <UTC ISO 8601>
```

The `finally` block must execute on both normal exit and exception. A run must never exit with `status = 'running'`.

T15 must not add columns to `run_metadata` beyond the T1 schema.

**Skipped-symbol count:** This count belongs in the T13 `report.json` run-level stage-counts or diagnostics section (consistent with the existing `stage_counts` pattern used in the current pipeline). Before implementing this field placement, Codex must inspect the T13 output schema and identify the exact existing field path. If a suitable section already exists in T13's `report.json` schema, place the count there and name it explicitly in the implementation. If no suitable T13 field path exists, Codex must stop, add an explicit T13-schema extension to the in-scope change surface of this ticket, and document the new field path in `docs/canonical/DATA_MODEL.md` before proceeding. Silent schema invention is not permitted.

---

### As-of bar determination

The runner derives `daily_bar_id` using the T1 bar-clock utility: the last fully closed daily UTC bar at invocation time. Result is always `str` in `YYYY-MM-DD` format (canonical type per OQ3 resolution). No lookahead: the runner must not process data from a bar not yet closed at invocation time.

**CLI override:** `--as-of YYYY-MM-DD` is permitted for manual/backfill runs. Non-`YYYY-MM-DD` format raises `ValueError`. A future or current date raises `ValueError`. This override selects a specific past bar; closed-bar semantics still apply.

---

### Per-symbol error handling

**Category 1 — Fachlich expected non-evaluability**
Examples: insufficient OHLCV history, `data_4h_available = False` without viable 1d fallback, no prior persisted state on a first-seen coin, feature computation returning all-null for a symbol.
Handling: symbol flows through the pipeline with appropriate `null` fields and `reduced_resolution` / `not_evaluable` statuses as defined by upstream modules (T5–T12). Not an error at runner level. Symbol is included in output artifacts with its computed (possibly partial) status.

**Category 2 — Controlled symbol-local operational failure**
Examples: OHLCV fetch returns a network error for one symbol after retries; T10 write interface raises for one symbol due to a transient DB lock; one symbol returns a malformed or unparseable API response.
Distinction from Category 3: the failure can be attributed to a single symbol's data path and does not indicate a shared infrastructure problem.
Handling: skip the symbol for this run. Log a structured warning with `symbol`, `stage_of_failure`, `exception_type`. The symbol does not appear in decision or output artifacts for this run. All other symbols continue. Skipped-symbol count is recorded per the T13 `report.json` schema section above.

**Category 3 — Hard infrastructure or shared contract failure**
Examples: SQLite database unreachable at run start; a typed bundle contract violation that cannot be attributed to a single symbol (i.e., affects the shared data path or runner state); universe fetch returns a technical failure (non-200, parse failure, or unusable payload at the shared universe level — not a single-symbol API response).
Distinction from Category 2: the failure is in shared infrastructure or in a contract path that cannot be isolated to one symbol without corrupting runner state.
Handling: abort the run immediately. Set `run_metadata.status = 'failed'`. Do not write index files. Log a structured error with `stage_of_failure`, `exception_type`, `exception_message`. Re-raise so the process exits non-zero.

**Empty universe (zero symbols, technically successful fetch):**
A universe fetch that returns an empty symbol list without a technical failure is neither Category 2 nor Category 3. It is treated as a non-publishing completed run per the minimal artifact contract: `run_metadata.status = 'completed'`; the run-scoped `report.json` is written with `candidate_count = 0`; all other artifacts (daily report, manifest, diagnostics, history partitions, index files) are not written; a structured warning is logged. This case is explicitly marked as a non-publishable run in the runner code.

**Status fields:** The runner must not invent per-symbol `status = 'error'` fields on output records beyond what T13's output schema defines. Codex must not add per-symbol status fields not defined by T13.

---

## Goal

After this ticket is completed:

- `scanner/runners/daily.py` implements `run_daily_scan(cfg, as_of_date: str | None = None) -> None`
- `scanner/main.py` invokes `run_daily_scan`; no active call to the legacy orchestrator remains
- `scanner/pipeline/__init__.py` carries an explicit legacy-isolation docstring; not deleted; no Independence-Release import from it
- `daily_bar_id` is `str` (`YYYY-MM-DD`) in `Tier1AxisBundle`, `Tier2AxisBundle`, `PhaseInterpretationBundle`, and all directly dependent serializers, validators, fixtures, and diagnostics helpers — no `int` representation anywhere in the Independence-Release runner call graph
- `docs/canonical/DATA_MODEL.md` declares `daily_bar_id: str (YYYY-MM-DD)` as canonical cross-layer type
- `docs/canonical/open_questions.md` OQ3 is marked as resolved; OQ2 remains open
- For publishable runs (non-empty result set): the full canonical output artifact set is produced; `reports/index/` is updated atomically via stage-then-rename after all artifacts in publish steps 1–4 are written
- For non-publishable runs (empty universe): `run_metadata.status = 'completed'`; run-scoped `report.json` written with `candidate_count = 0`; all other artifacts not written per the minimal artifact contract; structured warning logged
- `run_metadata` is written at run start and updated to `'completed'` or `'failed'` in a `finally` block; `'running'` is never the terminal status; no extra columns beyond T1 schema
- Skipped-symbol count is in the T13 `report.json` stage-counts/diagnostics section; T15 does not silently extend T13 schema without explicit in-scope confirmation
- T11 invoked unconditionally for all symbols with a valid `PhaseInterpretationBundle`; T12 in pre-execution mode; `btc_regime=None`; execution call-site boundary present returning `None`
- State read after T8 outputs available, before T9/T10 evaluation; state write before output publication for each symbol; `delta_closed_bars_relevant = 6`
- Determinism: identical inputs, config, and `as_of_date` → identical outputs

---

## Scope

Allowed change surface:

- `scanner/runners/daily.py` (new)
- `scanner/runners/__init__.py` (new, if needed)
- `scanner/main.py` — re-wire entry point
- `scanner/pipeline/__init__.py` — add legacy-isolation docstring only
- Typed bundle model files for `Tier1AxisBundle`, `Tier2AxisBundle`, `PhaseInterpretationBundle` — `daily_bar_id` type `int` → `str`
- All directly dependent serializers, validators, fixtures, and diagnostics helpers that enforce `daily_bar_id` as `int` — update to `str`
- `scanner/config.py` or central config accessor — `cfg.runner` operational defaults only (e.g., `max_symbol_retries`); no business-logic flags. **Config semantics for `cfg.runner`:** partial overrides are merged field-wise with central defaults (missing subkeys use their defaults and are not treated as invalid); invalid types or out-of-range values raise a clear config validation `ValueError` naming the offending key; no ad-hoc raw-dict fallback is permitted.
- `tests/**` — update fixtures/tests for `daily_bar_id` str type; add runner tests
- `docs/canonical/DATA_MODEL.md` — `daily_bar_id: str (YYYY-MM-DD)` declaration
- `docs/canonical/open_questions.md` — OQ3 resolved
- `docs/canonical/ARCHITECTURE.md` — update only if this file exists in the repo
- `docs/canonical/GLOSSARY.md` — update `daily_bar_id` entry only if this file exists
- `docs/canonical/VERIFICATION_FOR_AI.md` — update only if this file exists

Do not create new canonical doc files unless those paths are already established in the repo. Do not manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

## Out of Scope

This ticket must not:

- implement new fachliche logic not already in T3–T12
- implement the intraday runner → Ticket 17
- implement the execution adapter → Ticket 16
- prescribe the T16 function signature
- implement BTC regime computation
- implement evaluation, replay, or forward-return logic → Ticket 18
- implement GitHub Actions scheduling → Ticket 19
- delete `scanner/pipeline/__init__.py`
- add per-symbol output status fields not defined by T13's output schema
- add columns to `run_metadata` beyond the T1 schema
- silently extend T13's `report.json` schema for the skipped-symbol count without explicit in-scope confirmation
- implement active archive or delete jobs
- mark OQ2 as resolved
- implement a runtime toggle conditioning whether T11 is called
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority:

- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` — §§1–2, §§9–12, §14, §15
- `independence_release_gesamtkonzept_final.md` — §7, §10, §19, §20 Festlegungen 1–6

Upstream contracts (read-only):

- Ticket 1 — `run_metadata` schema, bar-clock utility, `DAILY_SCAN_DELTA_BARS = 6`, `scan_mode` enum values
- Ticket 3 — eligibility, activity gate, monitoring bypass, `pre_4h_candidate_filter`
- Ticket 4 — OHLCV fetch and cache policy
- Ticket 5/5.1 — `FeatureBundle`
- Ticket 6 — `Tier1AxisBundle` (OQ3)
- Ticket 7 — `Tier2AxisBundle` (OQ3)
- Ticket 8 — `PhaseInterpretationBundle` (OQ3)
- Ticket 9 — invalidation and cycle detection output contract
- Ticket 10 — `StateMachineBundle`, state persistence single-write contract
- Ticket 11 — `EntryPatternBundle`
- Ticket 12 — `DecisionBundle`, `RankedDecision`, pre-execution mode contract
- Ticket 13 — output schema, report writers, `report.json` stage-counts section, `symbol_diagnostics.jsonl.gz` format
- Ticket 14 — snapshot placement, Parquet history writers, manifest contract

Supplemental context: `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`

Repo process references (conditional on existence in repo): `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST_updated.md`, `docs/canonical/WORKFLOW_CODEX.md`

---

## Proposed Change (high-level)

### Before

- `scanner/main.py` calls the legacy `run_pipeline()` orchestrator.
- T3–T12 modules exist as standalone layers with no unified runner.
- `daily_bar_id` is `int` in `Tier1AxisBundle`, `Tier2AxisBundle`, `PhaseInterpretationBundle` — inconsistent with the output/schema layer.
- OQ3 is open.

### After

- `scanner/runners/daily.py` is the canonical Independence-Release daily runner.
- `scanner/main.py` calls `run_daily_scan`.
- `scanner/pipeline/__init__.py` carries a legacy docstring; not deleted.
- All T3–T12 layers invoked in correct sequence with correct data flow and state lifecycle.
- `daily_bar_id` is `str` (`YYYY-MM-DD`) everywhere — OQ3 resolved.
- Publishable runs produce the full canonical artifact set with atomic index update.
- Non-publishable (empty-universe) runs produce a minimal audit record without index update.
- Per-symbol errors handled per the three-category policy.

---

## Acceptance Criteria

1. `scanner/runners/daily.py` exists and implements `run_daily_scan(cfg, as_of_date: str | None = None) -> None`.
2. `scanner/main.py` calls `run_daily_scan`; no active call to `run_pipeline()` remains.
3. `scanner/pipeline/__init__.py` carries the explicit legacy-isolation docstring. No Independence-Release code imports from it.
4. `Tier1AxisBundle.daily_bar_id` is typed `str`. All tests/fixtures asserting `int` updated.
5. `Tier2AxisBundle.daily_bar_id` is typed `str`. Same requirement.
6. `PhaseInterpretationBundle.daily_bar_id` is typed `str`. Same requirement.
7. All serializers, validators, fixtures, and diagnostics helpers within the daily-runner call graph and its directly dependent contracts that previously enforced `daily_bar_id` as `int` are updated to `str`. No `int` representation of `daily_bar_id` remains in that call graph.
8. `docs/canonical/DATA_MODEL.md` declares `daily_bar_id: str (YYYY-MM-DD)` as the canonical cross-layer type.
9. `docs/canonical/open_questions.md` OQ3 is marked as resolved by this ticket.
10. `run_metadata` is written with `status = 'running'`, `scan_mode = 'daily_discovery'`, `daily_bar_id` (str), `intraday_bar_id = null`, `started_at_utc` before any symbol is processed.
11. `run_metadata` is updated to `status = 'completed'` or `status = 'failed'` in a `finally` block. `'running'` is never the terminal status.
12. No columns are added to `run_metadata` beyond the T1 schema.
13. The fachliche layers run in canonical order per Abschnitt 6 §10.1: eligibility (T3) → 1d OHLCV (T4) → pre-4h filter (T3) → 4h OHLCV (T4) → features (T5/T5.1) → Tier-1 (T6) → Tier-2 (T7) → phase (T8) → state read → invalidation (T9) → state machine + write (T10) → entry patterns (T11) → execution boundary → decision (T12). State read must be available before T9/T10 evaluation (i.e., after T8 outputs are available). State write (via T10 canonical write interface) must complete before output publication for that symbol.
14. T10 canonical write interface receives `delta_closed_bars_relevant = 6`.
15. T12 is called with `execution_contract=None`.
16. An explicit execution call-site boundary is present, returning `None`, with a Ticket 16 reference comment. No T16 signature prescribed.
17. `btc_regime=None` passed to T12. No BTC regime computation.
18. T11 invoked for all symbols with a valid `PhaseInterpretationBundle`. No config flag gates this.
19. For publishable runs: `reports/index/` files written via `os.replace()` only after publish steps 1–4 complete without write-level errors.
20. `run.manifest.json` only under `snapshots/runs/YYYY/MM/DD/<run_id>/`. No copy under `reports/runs/`.
21. Skipped-symbol count placed in the T13 `report.json` stage-counts/diagnostics section. Codex must identify the exact existing field path before implementing. If no suitable T13 path exists, Codex must extend the in-scope change surface and document the new field path in `docs/canonical/DATA_MODEL.md` before implementing — no silent schema invention.
22. Category 2 failures: symbol skipped with structured warning; run continues; skipped count recorded.
23. Category 3 failures: run aborts; `status = 'failed'`; index not written; process exits non-zero.
24. Empty universe (zero symbols, no technical failure): follows the non-publishable run minimal artifact contract — `run_metadata.status = 'completed'`; run-scoped `report.json` written with `candidate_count = 0`; daily report, manifest, diagnostics, history partitions, and all index files not written; `recent_runs.json` not updated; structured warning logged. Runner code explicitly marks this branch as non-publishable.
25. Determinism: identical inputs, config, `as_of_date` → identical outputs, rankings, reason codes, artifact contents.
26. `--as-of YYYY-MM-DD` accepted. Non-`YYYY-MM-DD` format raises `ValueError`. Future/current date raises `ValueError`.

---

## Default-/Edgecase-Abdeckung

- **`daily_bar_id` type (`str` vs `int`):** ✅ (AC: #4–#9; call-graph audit scoped to daily-runner call graph and directly dependent contracts; no dual representation)
- **First-seen coin (no prior state):** ✅ (AC: #13; no-backfill; Category 1)
- **Symbol with no 4h data:** ✅ (AC: #13; `data_4h_available = False`; 1d-fallback)
- **Category 1 non-evaluability:** ✅ (symbol flows through with `null`/`not_evaluable`; not a skip)
- **Category 2 symbol-local failure:** ✅ (AC: #22; structured log; count in T13 `report.json`)
- **Category 3 hard failure:** ✅ (AC: #23; abort; `status = 'failed'`; no index write)
- **Empty universe (non-publishable run):** ✅ (AC: #24; minimal artifact contract; `completed`; only run_metadata + run-scoped report.json written; no index, manifest, diagnostics, history)
- **`run_metadata` open after crash:** ✅ (AC: #11; `finally` block)
- **Index on partial output failure:** ✅ (AC: #19; gated on all publish steps 1–4)
- **Manifest duplication:** ✅ (AC: #20; single canonical location)
- **`as_of_date` validation:** ✅ (AC: #26; format and future-date both raise `ValueError`)
- **`scan_mode` enum drift:** ✅ (AC: #10; `'daily_discovery'` per T1 AC-11)
- **Skipped-symbol count placement:** ✅ (AC: #21; T13 `report.json`; no `run_metadata` extension; Codex confirms field path or extends in-scope explicitly)
- **T13 schema extension without authority:** ✅ (AC: #21; Codex stops and documents before inventing schema)
- **Not-evaluated vs failed:** ✅ (Category 1 ≠ skip; Category 2 = controlled skip; Category 3 = abort)
- **State read/write ordering:** ✅ (AC: #13; read after T8, before T9; write before output; atomic per symbol)
- **Determinism:** ✅ (AC: #25)
- **OQ2 not resolved:** ✅ (Parquet write per T14 contract; OQ2 explicitly remains open)

---

## Tests

### Unit tests

- `test_daily_bar_id_is_str_in_tier1_axis_bundle` — `int` input raises `TypeError`/`ValidationError`; `str` input accepted
- `test_daily_bar_id_is_str_in_tier2_axis_bundle` — same
- `test_daily_bar_id_is_str_in_phase_bundle` — same
- `test_run_metadata_written_at_start` — assert `status = 'running'`, `scan_mode = 'daily_discovery'`, `daily_bar_id` is str, `intraday_bar_id` is null
- `test_run_metadata_completed_on_success` — assert `status = 'completed'`
- `test_run_metadata_failed_on_hard_error` — inject Category 3; assert `status = 'failed'`; assert no index write; assert non-zero exit
- `test_run_metadata_no_extra_columns` — assert write does not include fields beyond T1 schema
- `test_category2_symbol_skip_does_not_abort_run` — inject Category 2 on one symbol; run completes; structured warning logged; skipped count in `report.json`
- `test_category3_failure_aborts_run` — abort; `status = 'failed'`; index not written
- `test_empty_universe_non_publishable` — empty symbol list from successful fetch; `status = 'completed'`; run-scoped `report.json` written with `candidate_count = 0`; structured warning logged; index not updated; `recent_runs.json` unchanged; daily report, manifest, diagnostics, and history partitions not written
- `test_index_not_written_on_partial_output_failure` — simulate write failure at publish step 3; assert index not written
- `test_index_written_atomically` — verify `os.replace()` used; no partial file visible during write
- `test_execution_stub_returns_none` — call execution boundary; assert `None`
- `test_as_of_date_invalid_format` — `ValueError`
- `test_as_of_date_future_date` — `ValueError`
- `test_delta_closed_bars_relevant_is_6` — assert T1 `DAILY_SCAN_DELTA_BARS` constant is value passed to T10 write interface

### Integration tests

- Full run with mocked MEXC API, OHLCV, CMC: all canonical artifact paths exist; `status = 'completed'`; `latest_run.txt` updated; manifest only under `snapshots/runs/`; `report.json` with non-zero candidate count
- One symbol Category 2 failure: run completes; failed symbol absent from `symbol_diagnostics.jsonl.gz`; other symbols present; `report.json` skipped count = 1
- Determinism: two identical runs → `report.json` and `symbol_diagnostics.jsonl.gz` field-identical

---

## Constraints / Invariants (must not change)

- [ ] `daily_bar_id` is `str` (`YYYY-MM-DD`) in all affected typed bundles and directly dependent contracts within the daily-runner call graph after this ticket
- [ ] No `int` representation of `daily_bar_id` remains in the daily-runner call graph and its directly dependent contracts
- [ ] `scan_mode` SQLite value is `'daily_discovery'` (T1 AC-11)
- [ ] T10 canonical write interface is the only writer of state fields; write is atomic per symbol (fully committed or fully rolled back)
- [ ] State read after T8 outputs available, before T9/T10 evaluation
- [ ] State write before output publication for each symbol
- [ ] `delta_closed_bars_relevant = 6` for daily scan
- [ ] `reports/index/` updated only after publish steps 1–4 complete (publishable runs only)
- [ ] `run.manifest.json` only under `snapshots/runs/YYYY/MM/DD/<run_id>/`
- [ ] Empty universe → non-publishable completed run; follows minimal artifact contract; only run_metadata and run-scoped report.json written; all other artifacts and index not written
- [ ] `btc_regime=None`
- [ ] T12 in pre-execution mode
- [ ] T11 unconditionally called for all symbols with valid `PhaseInterpretationBundle`
- [ ] No-backfill: missing state → `null`, not inferred
- [ ] UTC only; closed-bar only; no lookahead
- [ ] OQ2 remains open
- [ ] No extra `run_metadata` columns beyond T1 schema
- [ ] `scanner/pipeline/__init__.py` not deleted in this ticket
- [ ] Skipped-symbol count in T13 `report.json`; not in `run_metadata`
- [ ] No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`
- [ ] 1 ticket = 1 PR

---

## Definition of Done (Codex must satisfy)

(Reference: `docs/canonical/WORKFLOW_CODEX.md` if this file exists in the repo)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Implemented code changes per Acceptance Criteria
- [ ] `daily_bar_id` type harmonization complete: all affected models, serializers, validators, fixtures, tests
- [ ] `docs/canonical/DATA_MODEL.md` updated: canonical `daily_bar_id` type declared
- [ ] `docs/canonical/open_questions.md` OQ3 marked resolved
- [ ] Legacy docstring added to `scanner/pipeline/__init__.py`
- [ ] Added / updated tests per this ticket
- [ ] Updated canonical docs under `docs/canonical/` (ARCHITECTURE.md, GLOSSARY.md, VERIFICATION_FOR_AI.md — only if these files exist at those paths in the repo)
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata

```yaml
created_utc: "2026-04-23T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
gesamtkonzept_ref: "§19 Ticket 15"
resolves_open_questions:
  - "OQ3: daily_bar_id type harmonization"
related_issues: []
follow_ups:
  - "Ticket 16: execution adapter — wire into execution call-site boundary"
  - "Ticket 17: intraday runner — builds on runner architecture introduced here"
  - "Ticket 19: GitHub Actions scheduling — wire daily runner into CI/CD"
  - "Dedicated cleanup ticket: delete scanner/pipeline/__init__.py after confirming no remaining consumers"
  - "open_questions.md OQ2: long-term OHLCV history storage — remains open"
```
