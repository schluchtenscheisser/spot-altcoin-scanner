> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

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
