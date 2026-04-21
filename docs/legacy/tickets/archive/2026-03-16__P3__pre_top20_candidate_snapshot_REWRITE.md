> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# [P3] Add deterministic pre-Top20 candidate snapshot for inclusion audit

## Context / Source

The current analysis stack can explain downstream blocker behavior on the published `trade_candidates` Top20, but it still cannot determine whether the Top20 itself is compositionally wrong because the pipeline does not persist a run-matched, globally ranked candidate universe before the Top20 cap.

Recent analysis established three things:

- The published Top20 is structurally weak for executable entries: heavy `reversal` concentration, very high `tradeability_class = MARGINAL`, and near-total `entry_state = chased`.
- The Top20 formation audit shows that the visible Top20 is unhealthy, but does not prove a Top20-selection bug by itself.
- The hardened pre-Top20 inclusion audit could not find a run-matched, global-ranking-capable upstream array in `snapshots/runtime`, `snapshots/history`, `snapshots/raw`, or other repo JSONs. Therefore the upstream inclusion question remains unmeasured, not disproven.

This ticket adds exactly the missing observability artifact: a deterministic snapshot of the full globally ranked candidate list **after symbol-level dedup and before the Top20 cap**.

## Goal

Persist a deterministic, run-scoped JSON snapshot of the full globally ranked candidate list at the exact ranking stage needed for a real pre-Top20 inclusion audit.

After this change, it must be possible to answer, for a specific run:

- whether the published Top20 is identical to the first 20 rows of the pre-cap ranked universe,
- which candidates sit at ranks 21–40,
- whether more executable candidates were displaced below the cut line,
- whether setup concentration already exists before the Top20 cap.

## Scope

Allowlist of files/modules that may need changes:

- `scanner/pipeline/ranking/` or the actual module where global ranking, symbol-level dedup, and Top20 capping happen
- `scanner/report_writer.py` or the actual artifact/output writer used by the pipeline
- snapshot/runtime directory creation and atomic JSON write helper reuse, if already present
- optional: `scripts/pre_top20_inclusion_audit.py` only if a tiny consumption-path adjustment is needed for the new artifact name/location

## Out of Scope

- Any change to scoring, ranking, setup weighting, dedup logic, tradeability logic, risk logic, confirmation logic, or decision logic
- Any change to Top20 selection criteria
- Any change to existing `trade_candidates` contents, order, or schema
- Any change to existing `setups.*` arrays in the published run JSON
- Any new gate, filter, API call, OHLCV fetch, or scoring pass
- Any config-semantics change unless an optional output-path config key already exists and is merely reused

## Canonical References (important)

- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)

- **Before:**
  - The pipeline computes a globally ranked candidate list, performs symbol-level dedup, caps to the published Top20, and persists only the final `trade_candidates` list in the run outputs.
  - The pre-cap ranked universe is not persisted as a dedicated runtime artifact, so inclusion-vs-executability questions cannot be audited on a per-run basis.

- **After:**
  - At the ranking stage **post symbol-level dedup, pre Top20 cap**, the pipeline writes a deterministic JSON artifact to:
    - `snapshots/runtime/<run_id>_pre_top20.json`
  - The artifact contains:
    - a `meta` block describing the run and the exact ranking stage,
    - a `candidates` array containing one row per globally ranked candidate in the exact order used for Top20 selection,
    - enough candidate fields to support downstream inclusion analysis without recomputing ranking logic.

- **Edge cases:**
  - If the ranked candidate universe is empty, write a valid artifact with `candidates: []`.
  - If the ranked candidate universe has fewer than 20 rows, write the artifact normally and set the Top20 cutoff metadata to `null` where appropriate.
  - If the target directory does not exist, create it.
  - If the same `run_id` is re-run, overwrite deterministically.
  - If any numeric field is non-finite (`NaN`, `inf`, `-inf`), serialize it as `null` in the snapshot output.
  - If a source field is nullable at that ranking stage, preserve `null` exactly; do not coerce to `false`, `0`, `""`, or `[]`.

- **Backward compatibility impact:**
  - None to existing published outputs. This is a pure observability addition via a new runtime artifact.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Pipeline stage contract:** The snapshot must be taken at exactly:
  - `post_symbol_dedup_pre_top20_cap`
  - not earlier,
  - not after a second ranking pass,
  - not after any alternate filtering step,
  - not from reconstructed data in a later writer.
- **Single source of truth:** Reuse the in-memory ranked list that already drives Top20 selection. Do not rebuild ranking from separate data structures.
- **Config/Defaults:** This ticket should not introduce required config. If an optional path override is introduced, missing key must fall back to `snapshots/runtime/`.
- **Nullability:** Nullable source fields must remain nullable in the snapshot. No implicit `bool(...)` coercion on tri-state fields.
- **Non-finite numeric handling:** `NaN`, `inf`, and `-inf` must not appear as numeric-looking JSON values. Serialize them as `null`.
- **Strict/Preflight:** The snapshot write must be atomic: temp file + rename. On failure, no partial target file may remain.
- **Not-evaluated vs failed:** This ticket must not collapse non-evaluated states into failed states. It is an observability ticket, not an evaluation-policy ticket.
- **Determinism:** At identical input and identical config, the snapshot bytes must be identical.
- **Sorting/Tie-breaker:** The snapshot row order must be exactly the same order the pipeline uses to determine Top20 inclusion, with the same existing tie-breaker and no alternate sort implementation.

## Implementation Notes (optional but useful)

- **Pipeline position:** Write the artifact from the same ranked candidate list that is already used to derive `trade_candidates`.
- **No extra compute:** No additional API calls, no OHLCV refetch, no re-scoring, no recomputation of decision/risk/tradeability from scratch.
- **Artifact semantics:** The artifact is a runtime observability artifact, not a replacement for the canonical published run JSON.
- **Determinism note:** If the ranking stage already has a stable sort and explicit tie-breaker, the snapshot must reuse that exact order, not restate it approximately.
- **Directory semantics:** `snapshots/runtime/` is the preferred location for this artifact because the inclusion audit script prioritizes that directory first.

## Acceptance Criteria (deterministic)

1) After each pipeline run, a file exists at:
   - `snapshots/runtime/<run_id>_pre_top20.json`

2) The file contains valid JSON with this top-level structure:
   ```json
   {
     "meta": {
       "run_id": "<run_id>",
       "timestamp_utc": "<ISO-8601 UTC timestamp>",
       "canonical_schema_version": "<version>",
       "ranking_stage": "post_symbol_dedup_pre_top20_cap",
       "sort_key_description": "<human-readable description of the exact existing ranking order>",
       "total_candidates": <int>,
       "top20_cutoff_index": 20,
       "top20_cutoff_global_score": <float or null>
     },
     "candidates": [ ... ]
   }
   ```

3) `meta.ranking_stage` is exactly:
   - `post_symbol_dedup_pre_top20_cap`

4) `meta.sort_key_description` is present and describes the real sort already used for Top20 selection, including the existing tie-breaker if applicable.

5) `candidates` contains one row per globally ranked candidate **after symbol-level dedup and before Top20 cap**, in the exact order used by Top20 selection.

6) Each candidate row contains at minimum:
   - `rank` (int, 1-based)
   - `symbol` (str)
   - `best_setup_type` (str)
   - `setup_subtype` (str or null)
   - `setup_score` (float or null)
   - `global_score` (float or null)
   - `tradeability_class` (str or null)
   - `risk_acceptable` (bool or null)
   - `entry_ready` (bool or null)
   - `entry_state` (str or null)
   - `decision` (str or null)
   - `decision_reasons` (list[str] or null)
   - `risk_pct_to_stop` (float or null)
   - `distance_to_entry_pct` (float or null)

7) The first 20 rows in `candidates` correspond exactly to the symbols in published `trade_candidates`, in the same order, for the same run.

8) `meta.total_candidates == len(candidates)`.

9) If `len(candidates) >= 20`, `meta.top20_cutoff_global_score == candidates[19].global_score`.
   If `len(candidates) < 20`, `meta.top20_cutoff_global_score == null`.

10) If the ranked candidate universe is empty, the file is still written with:
    - `"candidates": []`
    - `meta.total_candidates = 0`
    - `meta.top20_cutoff_global_score = null`

11) Nullable candidate fields preserve source nullability exactly. No implicit coercion to `false`, `0`, `""`, or empty collections.

12) Non-finite numeric source values (`NaN`, `inf`, `-inf`) are serialized as `null` in the snapshot.

13) The snapshot file is written atomically. If the write fails, no partial target file remains.

14) Existing published outputs remain byte-identical:
    - `trade_candidates`
    - `setups.*`
    - run manifest
    - MD report
    - any existing JSON/XLSX/MD outputs

15) No additional API calls, OHLCV fetches, scoring passes, or decision recomputations are introduced by this change.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ (AC: #1, guardrails; if optional path override exists/gets introduced, missing key → `snapshots/runtime/`)
- **Config Invalid Value Handling:** ✅ (N/A — no new required config validation in scope)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #11 ; Test: nullable fields remain `null`)
- **Not-evaluated vs failed getrennt:** ✅ (N/A — no new evaluation logic; existing semantics must remain untouched)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (AC: #13 ; Test: simulated write failure leaves no partial target file)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (AC: #1 ; deterministic overwrite on identical `run_id`)
- **Deterministische Sortierung/Tie-breaker:** ✅ (AC: #4, #5, #7 ; Tests verify exact order and tie-break preservation)

## Tests (required if logic changes)

- **Unit:**
  - Snapshot with `>20` candidates: first 20 `symbol`s match `trade_candidates` in order (AC #7)
  - Snapshot with `<20` candidates: all candidates present; `top20_cutoff_global_score = null` (AC #9)
  - Snapshot with `0` candidates: valid file with empty `candidates` and correct `meta` (AC #10)
  - Nullable preservation: `risk_acceptable = null` in source remains `null` in snapshot (AC #11)
  - Nullable preservation: `decision = null` and `decision_reasons = null` remain `null`, not `[]` or fallback strings (AC #11)
  - Non-finite numeric handling: `global_score = NaN`, `inf`, `-inf` in source serializes as `null` (AC #12)
  - Deterministic overwrite: same `run_id` written twice produces byte-identical snapshot output
  - Atomic write failure: simulated failure leaves no partial target file (AC #13)
  - Meta block correctness: `ranking_stage` and `sort_key_description` are present and correct (AC #3, #4)

- **Integration:**
  - Full pipeline run writes `snapshots/runtime/<run_id>_pre_top20.json`
  - Snapshot row count matches the actual pre-cap ranked candidate universe
  - First 20 snapshot rows match published `trade_candidates`
  - Existing published outputs remain byte-identical before vs after the change (AC #14)

- **Golden fixture / verification:**
  - Not required for scoring curves/thresholds because no scoring logic changes
  - Add one stable runtime fixture or snapshot comparison proving deterministic bytes for identical input

## Constraints / Invariants (must not change)

- [x] Closed-candle-only behavior must not change
- [x] No-lookahead behavior must not change
- [x] Existing Top20 ranking logic must not change
- [x] Existing tie-break behavior must not change
- [x] Existing `trade_candidates` order and content must not change
- [x] Existing published JSON/MD/XLSX outputs must remain byte-identical
- [x] No additional API calls or OHLCV fetches introduced
- [x] No second source of truth for ranking introduced
- [x] This remains exactly **1 ticket → 1 PR**

---

## Definition of Done (Codex must satisfy)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Snapshot artifact written at `snapshots/runtime/<run_id>_pre_top20.json`
- [ ] Tests added for nullable preservation, non-finite handling, deterministic ordering, and atomic write
- [ ] Existing published outputs verified byte-identical
- [ ] Canonical docs updated if this new runtime artifact is documented under `docs/canonical/`
- [ ] `docs/canonical/VERIFICATION_FOR_AI.md` unchanged unless artifact verification documentation requires an explicit addition
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR creation

---

## Metadata (optional)
```yaml
created_utc: "2026-03-16T23:15:00Z"
priority: P3
type: feature
owner: codex
related_issues: []
```
