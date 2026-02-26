# Stop-the-bleeding Tickets (1 Ticket = 1 PR)

Place each ticket file under `docs/tickets/` using the suggested filenames below.
Template source: `_TEMPLATE.md`. fileciteturn2file0

---

## Suggested file list

1. `2026-02-26__P0__orderbook_topk_budget_and_errors.md`
2. `2026-02-26__P0__closed_candle_gate_breakout_pullback.md`
3. `2026-02-26__P0__proxy_liquidity_percent_rank_tests.md`
4. `2026-02-26__P1__schema_versioning_and_scoring_snapshot_docs.md`
5. `2026-02-26__P1__tests_fixture_paths_independent_of_cwd.md`

---

# 1) 2026-02-26__P0__orderbook_topk_budget_and_errors.md

## Title
[P0] Orderbook Top-K: keine None-Einträge, pro-Symbol Fehler isolieren (degrade statt abort)

## Context / Source (optional)
- PR-Feedback: „Avoid inserting None orderbooks for non-selected symbols“ + „Guard orderbook fetch loop against single-symbol API failures“
- Aktueller Code: `fetch_orderbooks_for_top_k` initialisiert `payload[symbol]=None` für alle Kandidaten und setzt nur für ausgewählte Symbole einen Snapshot. Downstream ruft `compute_orderbook_liquidity_metrics(orderbook.get(...))` auf und crasht bei `None`.

## Goal
- Ein einzelner Orderbook-API-Fehler darf **nicht** den Run abbrechen.
- Wenn `orderbook_top_k < shortlist_size`, dürfen **nicht ausgewählte** Symbole **keine** `None`-Orderbooks in der Map erhalten.
- Liquidity-Enrichment muss deterministisch bleiben und bei fehlendem Orderbook sauber degradieren.

## Scope
- `scanner/pipeline/liquidity.py`
- Optional: `scanner/clients/mexc_client.py` (nur wenn Exception-Typen/Retry-Verhalten angepasst werden müssen)
- Tests:
  - `tests/pipeline/test_liquidity_orderbook_topk_budget.py`
  - `tests/pipeline/test_liquidity_orderbook_error_isolation.py`

## Out of Scope
- Keine Änderung am Slippage/Spread Rechenmodell
- Keine Änderung an Ranking/Sort-Keys außerhalb der Orderbook-Stufe

## Canonical References (important)
- `docs/canonical/LIQUIDITY/SLIPPAGE_CALCULATION.md`
- `docs/canonical/LIQUIDITY/RE_RANK_RULE.md`
- `docs/canonical/PIPELINE.md`

## Proposed change (high-level)
- Before:
  - `fetch_orderbooks_for_top_k(...)` legt `orderbooks[symbol]=None` für alle Kandidaten an.
  - `apply_liquidity_metrics_to_shortlist(...)` prüft nur `if symbol in orderbooks:` und ruft dann `compute_orderbook_liquidity_metrics(orderbooks[symbol], ...)` auf → crash wenn Wert `None`.
- After:
  - `fetch_orderbooks_for_top_k(...)` gibt **nur** eine Map für die tatsächlich selektierten Top-K Symbole zurück (`symbol -> orderbook_payload`).
  - Jeder `get_orderbook(symbol)` Call ist in `try/except` gekapselt; Fehler werden geloggt, aber der Run läuft weiter.
  - `apply_liquidity_metrics_to_shortlist(...)` behandelt fehlendes Orderbook wie „nicht verfügbar“ und setzt:
    - `spread_bps=None`, `slippage_bps=None`, `liquidity_grade=None`, `liquidity_insufficient=None`
- Edge cases:
  - `top_k <= 0` → keine Orderbooks; alle Kandidaten erhalten None-Felder.
  - `get_orderbook` liefert payload ohne bids/asks oder leere bids/asks → `compute_orderbook_liquidity_metrics` liefert weiterhin `grade="D"` + `liquidity_insufficient=True`.
- Backward compatibility impact:
  - Report-Felder bleiben gleich (keine neuen keys).
  - Bedeutungsänderung: „Orderbook nicht gefetched“ wird `liquidity_grade=None`; „gefetched aber insufficient depth“ bleibt `grade="D"`.

## Implementation Notes (optional but useful)
- Budget: garantiert maximal `orderbook_top_k` API calls.
- Determinismus: `select_top_k_for_orderbook` bleibt sortiert nach `(proxy_liquidity_score, quote_volume_24h)` desc.

## Acceptance Criteria (deterministic)
1) Wenn `orderbook_top_k < len(shortlist)`, darf `apply_liquidity_metrics_to_shortlist` nicht crashen.
2) Wenn `mexc_client.get_orderbook(symbol)` für ein ausgewähltes Symbol eine Exception wirft, läuft der Run weiter und dieses Symbol erhält `spread_bps/slippage_bps/liquidity_grade/liquidity_insufficient = None`.
3) Für ein Symbol mit gefetchtem Orderbook aber leeren bids/asks liefert `compute_orderbook_liquidity_metrics` weiterhin `liquidity_grade="D"` und `liquidity_insufficient=True`.
4) `fetch_orderbooks_for_top_k` erzeugt höchstens `orderbook_top_k` API Calls.

## Tests (required if logic changes)
- Unit:
  - `test_topk_budget_does_not_insert_none_orderbooks_and_does_not_crash`
  - `test_orderbook_exception_isolated_per_symbol`

## Constraints / Invariants (must not change)
- [ ] Closed-candle-only
- [ ] No lookahead
- [ ] Deterministische Sortierung (Top-K Selektion)
- [ ] Slippage/Spread rounding wie Canonical (6 decimals)

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

# 4) 2026-02-26__P1__schema_versioning_and_scoring_snapshot_docs.md

## Title
[P1] Schema-Version bump + docs/SCHEMA_CHANGES + GPT Snapshot Scoring-Text sichern

## Context / Source (optional)
- PR-Feedback: Schema-Versionierung für neue Output-Felder (discovery) fehlt.
- PR-Feedback: GPT Snapshot Workflow darf Scoring-Regeln nicht verlieren, wenn `docs/scoring.md` nur Redirect ist.

## Goal
1) Output-Schema Version ist eindeutig gebumpt und changelogged.  
2) Scoring-Regeln sind weiterhin im GPT Snapshot enthalten.

## Scope
- `scanner/pipeline/output.py` (Version field in meta bump)
- `docs/SCHEMA_CHANGES.md` (anlegen falls fehlt)
- `docs/scoring.md` und/oder `.github/workflows/generate-gpt-snapshot.yml`
- Tests:
  - `tests/test_output_schema_version.py` (checks exact expected version string)

## Out of Scope
- Keine Scoring-Änderungen
- Keine Discovery-Änderungen

## Canonical References (important)
- `docs/canonical/PIPELINE.md`
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/canonical/OUTPUTS/` (falls vorhanden)

## Proposed change (high-level)
- Bump schema version string in report meta (e.g. `1.5`→`1.6`).
- Add `docs/SCHEMA_CHANGES.md` entry documenting added discovery fields.
- Ensure scoring rules text is included in GPT snapshot generation:
  - Preferred: restore full text into `docs/scoring.md`
  - Alternative: modify workflow to include canonical scoring docs directly.

## Acceptance Criteria (deterministic)
1) Output meta contains the new exact schema version string.
2) `docs/SCHEMA_CHANGES.md` contains a matching entry with discovery field list.
3) GPT snapshot generation still includes scoring rules text (verified by checking generated snapshot file in CI output or by running workflow locally).
4) No scoring behavior changes.

## Tests (required if logic changes)
- Unit: `test_output_schema_version_is_expected`
- Verification: PR description includes steps to verify snapshot content

## Constraints / Invariants (must not change)
- [ ] Closed-candle-only
- [ ] No lookahead
- [ ] Keine Scoring-Kurve geändert

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented code/doc changes per Acceptance Criteria
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-02-26T21:11:08Z"
priority: P1
type: docs
owner: codex
related_issues: []
```

---

# 5) 2026-02-26__P1__tests_fixture_paths_independent_of_cwd.md

## Title
[P1] Tests: Fixture-Pfade relativ zu __file__ (CWD-unabhängig)

## Context / Source (optional)
- PR-Feedback: Fixture-Pfade sind aktuell CWD-abhängig und brechen in IDE/CI-Kontexten.

## Goal
Alle Tests mit Fixtures müssen CWD-unabhängig sein.

## Scope
- Betroffene Tests (alle, die `Path("tests/...")` oder ähnliche Root-relative Pfade verwenden)
- Optional: `tests/_helpers.py` für eine zentrale Fixture-Resolver Funktion

## Out of Scope
- Keine Änderungen am Produktionscode

## Canonical References (important)
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
- Replace any `Path("tests/...")` with paths derived from `Path(__file__).resolve()` or helper.

## Acceptance Criteria (deterministic)
1) `pytest` läuft aus Repo-Root.
2) `pytest` läuft aus `tests/`.
3) Kein Test verwendet `Path("tests/")` für Fixtures.

## Tests
- Existing tests updated accordingly.

## Constraints / Invariants (must not change)
- [ ] Deterministische Tests
- [ ] Keine Produktionscode-Änderung

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented test changes per Acceptance Criteria
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-02-26T21:11:08Z"
priority: P1
type: test
owner: codex
related_issues: []
```
