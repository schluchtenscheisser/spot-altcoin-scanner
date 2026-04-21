> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Restore breakout trend scoring by wiring `close_series` / `high_series` / `low_series` from FeatureEngine into active breakout pipeline

## Context / Source
- Active pipeline wiring in `scanner/pipeline/__init__.py` uses `score_breakout_trend_1_5d(...)`, not the legacy/simple breakout scorer.
- Current runs show `breakout_scored: 0` while multiple symbols (e.g. TAO / RENDER / HYPE class) exhibit breakout-like feature profiles in snapshots/reports.
- Root-cause analysis indicates an integration gap between FeatureEngine output and the active breakout scorer:
  - `scanner/pipeline/scoring/breakout_trend_1_5d.py` requires:
    - `f1d["high_series"]`
    - `f4h["close_series"]`
    - `f4h["low_series"]`
  - `scanner/pipeline/features.py` currently builds `closes`, `highs`, `lows` arrays inside `_compute_timeframe_features(...)` but only emits scalar last-value fields such as `close`, `high`, `low`.
  - The required `*_series` fields are not emitted, so the breakout scorer falls back to empty lists and returns `[]` immediately:
    - `_calc_high_20d_excluding_current(...)` -> `None` when `high_series` missing
    - `_find_breakout_indices(...)` -> `None` when `close_series` missing
- This means the active breakout path is very likely non-functional before any of the later hard gates (trend / trigger window / ATR rank / risk-off liquidity) can even matter.

## Goal
After this change:
- FeatureEngine emits the required OHLC series fields for each timeframe in a canonical, deterministic format.
- The active `score_breakout_trend_1_5d(...)` scorer receives real `close_series`, `high_series`, and `low_series` from FeatureEngine output.
- Breakout scoring is no longer structurally dead due to missing feature wiring.
- The repo contains an integration test that would fail if FeatureEngine and breakout scorer drift apart again.

## Scope
Allowed files/modules to modify:
- `scanner/pipeline/features.py`
- `scanner/pipeline/scoring/breakout_trend_1_5d.py` (only if tiny defensive compatibility comments/typing adjustments are needed; do not change gating semantics in this ticket)
- `docs/canonical/OUTPUT_SCHEMA.md` only if feature payload documentation explicitly enumerates emitted feature fields
- `docs/canonical/PIPELINE.md` only if it explicitly documents feature payload shape
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md` if examples/fixtures need updates
- relevant tests under `tests/`

## Out of Scope
- No tuning of breakout thresholds or gates
- No gate-level diagnostic logging ticket in this PR
- No changes to breakout ranking formula
- No changes to decision thresholds
- No changes to risk/stop/target logic
- No schema cleanup beyond the exact feature series fields needed for active scorer compatibility

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Before:
- `_compute_timeframe_features(...)` computes numpy arrays:
  - `closes`
  - `highs`
  - `lows`
- but only writes scalar snapshots like `close`, `high`, `low` into the timeframe feature dict.
- `score_breakout_trend_1_5d(...)` expects time-series fields and silently short-circuits to `[]` when they are absent.

After:
- `_compute_timeframe_features(...)` emits:
  - `close_series`
  - `high_series`
  - `low_series`
- Values are emitted as native Python lists aligned to the same truncated, closed-candle-only dataset already used for all other computed features.
- Active breakout scorer receives these lists through the normal pipeline without any ad-hoc reconstruction.
- Add integration coverage to prove:
  - FeatureEngine emits the fields
  - Active breakout scorer can consume them from real FeatureEngine output
  - A fixture that should generate a breakout candidate does so through the real integration path

Edge cases:
- Series must reflect only candles up to `last_closed_idx`; do not leak future/open candles.
- If timeframe data is insufficient and `_compute_timeframe_features(...)` already returns `{}`, no synthetic empty series should be inserted elsewhere.
- Series lists must preserve original chronological order.
- Non-finite values already present in source arrays must not be silently reordered or truncated beyond existing closed-candle slicing behavior.

Backward compatibility impact:
- Adds new feature fields to per-timeframe feature payloads.
- This is additive and should not break existing consumers that ignore unknown fields.
- Do not rename existing scalar `close` / `high` / `low` fields in this ticket.

## Codex Implementation Guardrails (No-Guesswork, Pflicht)
- **Config/Defaults:** This ticket introduces no new config keys and must not change config resolution/defaults.
- **Closed-candle-only:** Series must be built from the already-sliced `klines = klines[: last_closed_idx + 1]`. No future/open candle leakage.
- **Canonical source of truth:** Reuse the exact `closes`, `highs`, `lows` arrays already derived inside `_compute_timeframe_features(...)`. Do not reconstruct series in the scorer.
- **Native types:** Emit Python lists (`tolist()` or equivalent native conversion), not numpy arrays, to keep JSON-/snapshot-safe payloads.
- **Nullability / bool coercion:** Do not use truthiness of numpy arrays for presence detection. Use explicit conversion and explicit assertions in tests.
- **Missing vs invalid:** If `_compute_timeframe_features(...)` returns `{}` due to insufficient history, downstream behavior remains unchanged. Do not fabricate placeholder series.
- **No semantic tuning:** Do not change any breakout hard gate thresholds or ordering in this PR.
- **Determinism:** Feature serialization order/content must be deterministic for identical input OHLCV.
- **Repo reuse:** The integration test must use the real FeatureEngine output path, not manually hand-built feature rows only.

## Implementation Notes
- In `scanner/pipeline/features.py`, inside `_compute_timeframe_features(...)`, after numpy arrays `closes`, `highs`, `lows` are created from the truncated closed-candle slice, add:
  - `f["close_series"]`
  - `f["high_series"]`
  - `f["low_series"]`
- Ensure these fields pass through `_convert_to_native_types(...)` unchanged as native lists.
- Prefer to keep them present whenever the timeframe feature dict is returned successfully, not only for 1D or only for 4H.
- Do not add `volume_series` or other extra series in this ticket unless strictly required by active code (currently not required).
- Add one integration-style test that starts from OHLCV fixture data, runs FeatureEngine, then runs `score_breakout_trend_1_5d(...)`.
- Add at least one regression test proving the scorer would have failed before the wiring fix and now produces candidate rows when provided a breakout-shaped fixture through the real pipeline.
- If docs describe timeframe feature payload contents, add the three new fields there.

## Acceptance Criteria (deterministic)
1. `scanner/pipeline/features.py::_compute_timeframe_features(...)` emits `close_series`, `high_series`, and `low_series` for successful timeframe feature computations.
2. The emitted series are native Python lists and are aligned exactly with the closed-candle slice used for all other timeframe features.
3. `score_breakout_trend_1_5d(...)` can consume real FeatureEngine output without relying on manually injected series fields.
4. A regression/integration test using real FeatureEngine output and a breakout-shaped OHLCV fixture produces at least one breakout row where previously the scorer would have short-circuited due to missing series fields.
5. Existing scalar fields `close`, `high`, and `low` remain unchanged and available.
6. No breakout thresholds, gate ordering, or scoring weights are changed in this ticket.
7. No future/open candles are included in the emitted series.
8. Canonical docs/verification examples are updated if they explicitly enumerate the timeframe feature payload.

## Default-/Edgecase-Abdeckung (Pflicht)
- **Config Defaults (Missing key -> Default):** ✅ (N/A – no new config introduced)
- **Config Invalid Value Handling:** ✅ (N/A – no new config introduced)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #2/#3; Test: series presence checked explicitly, not via numpy truthiness)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #2/#4; Test: insufficient-history `{}` case remains distinct from successful feature rows with series)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no strict write mode feature introduced)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (N/A – not relevant)
- **Deterministische Sortierung/Tie-Breaker:** ✅ (AC: #2/#7; Test: deterministic series content from identical input)

## Tests (required)
- Unit:
  - Test `_compute_timeframe_features(...)` returns `close_series`, `high_series`, `low_series` for a valid 1D input fixture.
  - Test `_compute_timeframe_features(...)` returns `close_series`, `high_series`, `low_series` for a valid 4H input fixture.
  - Test the emitted lists match the exact closed-candle slice length and last values align with scalar `close`, `high`, `low`.
  - Test insufficient-history path still returns `{}` (or existing behavior) and does not fabricate partial series.
- Integration:
  - End-to-end test: OHLCV fixture -> `FeatureEngine.compute_all(...)` -> `score_breakout_trend_1_5d(...)` yields breakout rows for a known breakout-shaped fixture.
  - Regression test that the breakout scorer is consuming real FeatureEngine output rather than hand-crafted feature rows only.
- Golden fixture / verification:
  - Update `docs/canonical/VERIFICATION_FOR_AI.md` if feature payload examples or fixture expectations need the three new fields.

## Constraints / Invariants (must not change)
- Closed-candle-only
- No lookahead
- No breakout threshold tuning
- No decision-layer changes
- No risk-model changes
- No output/report field renames in this ticket
- Existing scalar feature fields remain intact

- [ ] Preserve existing feature computation semantics for scalar fields
- [ ] Preserve existing insufficient-history behavior
- [ ] Preserve existing breakout gate semantics exactly

## Definition of Done
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Added required unit + integration regression tests
- [ ] Updated canonical docs under `docs/canonical/` if payload docs/examples are impacted
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if examples changed
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata
```yaml
created_utc: "2026-03-13T00:00:00Z"
priority: P0
type: bugfix
owner: codex
related_issues: []
```
