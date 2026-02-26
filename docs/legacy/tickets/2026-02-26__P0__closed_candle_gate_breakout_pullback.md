> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# 2) 2026-02-26__P0__closed_candle_gate_breakout_pullback.md

## Title
[P0] Closed-candle history gate: Breakout/Pullback behandeln None als insufficient history

## Context / Source (optional)
- PR-Feedback: „Treat missing closed-candle count as insufficient history“
- Breakout/Pullback skippen aktuell nicht, wenn `candles_*` None ist.

## Goal
Breakout und Pullback sollen Symbole mit fehlender `last_closed_idx` Information **immer** als unzureichende Historie behandeln und **nicht** emitten.

## Scope
- `scanner/pipeline/scoring/breakout.py`
- `scanner/pipeline/scoring/pullback.py`
- Tests:
  - `tests/test_breakout_closed_candle_gate.py`
  - `tests/test_pullback_closed_candle_gate.py`

## Out of Scope
- Keine Änderung an Scoring-Formeln/Weights
- Keine Änderung an OHLCV lookbacks

## Canonical References (important)
- `docs/canonical/DATA_SOURCES.md`
- `docs/canonical/PIPELINE.md`

## Proposed change (high-level)
- Before: Gate überspringt None-Werte.
- After:
  - Wenn `candles_1d is None` oder `candles_4h is None` → skip.
  - Wenn `< min_history` → skip.
- Edge cases:
  - Boundary: `idx+1 == min_history` ist ausreichend.

## Acceptance Criteria (deterministic)
1) Breakout: fehlender `last_closed_idx` (1d oder 4h) → Symbol wird nicht returned.
2) Breakout: boundary-min-history → Symbol wird nicht geskippt.
3) Pullback: analog.
4) Keine Score-Änderung für valide Historie.

## Tests (required if logic changes)
- Unit: Tests analog zu `tests/test_reversal_closed_candle_gate.py`:
  - `test_breakout_history_gate_treats_none_as_insufficient_history`
  - `test_breakout_history_gate_allows_boundary_min_history`
  - `test_pullback_history_gate_treats_none_as_insufficient_history`
  - `test_pullback_history_gate_allows_boundary_min_history`

## Constraints / Invariants (must not change)
- [ ] Closed-candle-only
- [ ] No lookahead
- [ ] Keine Scoring-Kurve geändert

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented code changes per Acceptance Criteria
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-02-26T21:11:08Z"
priority: P0
type: bugfix
owner: codex
related_issues: []
```

---
