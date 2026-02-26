> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# 3) 2026-02-26__P0__proxy_liquidity_percent_rank_tests.md

## Title
[P0] Proxy Liquidity percent-rank: Regression-Tests (unsortierter Input, ties, Monotonie)

## Context / Source (optional)
- PR-Feedback: percent-rank darf nicht von Input-Reihenfolge abhängen.
- Code enthält `percent_rank_average_ties`, aber es fehlen Regression-Tests.

## Goal
Regressionen im `proxy_liquidity_score` verhindern.

## Scope
- `scanner/pipeline/cross_section.py`
- `scanner/pipeline/shortlist.py` (nur falls minimale Anpassungen nötig sind)
- Tests:
  - `tests/pipeline/test_percent_rank_average_ties.py`
  - `tests/pipeline/test_proxy_liquidity_score_is_order_independent.py`

## Out of Scope
- Keine Änderungen an Scoring/Rerank-Policy

## Canonical References (important)
- `docs/canonical/PIPELINE.md`

## Proposed change (high-level)
- Add tests:
  - Permutation-invariant mapping
  - Tie-average behavior
  - Monotonie property

## Acceptance Criteria (deterministic)
1) Unsortierter Input liefert konsistente percent-ranks (value-based).
2) Ties liefern identische percent-ranks (average-rank tie handling).
3) Für unique values gilt: größerer Wert ⇒ größerer percent-rank.
4) percent-rank ist immer in [0,100].

## Tests (required if logic changes)
- Unit: wie oben

## Constraints / Invariants (must not change)
- [ ] Deterministisch
- [ ] percent-rank in [0..100]

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented tests (und ggf. minimal bugfix)
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-02-26T21:11:08Z"
priority: P0
type: test
owner: codex
related_issues: []
```

---
