> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`

## Title
[P0] PR-04 Budget-Shortlist und Cheap-Pass V4.2.1 anpassen

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- Nach PR-03 ist der frühe Pool bewusst breiter; PR-04 stellt sicher, dass teure Stages trotzdem kontrolliert budgetiert bleiben.
- Die Shortlist ist der operative Flaschenhals zwischen geöffnetem Pool und teuren Orderbook-/OHLCV-Stages.

## Goal
Die Cheap-Shortlist wird so angepasst, dass:
- `budget.shortlist_size` config-driven auf 200 gesetzt und zentral gelesen wird,
- der neue harte `pre_shortlist_market_cap_floor_usd` vor dem Cheap-Pass wirksam ist,
- der Cheap-Pass als deterministischer Ranking-/Budget-Mechanismus bestehen bleibt,
- bei gleichem Input dieselben Symbole in derselben Reihenfolge shortgelistet werden.

## Scope
- `scanner/pipeline/shortlist.py`
- ggf. `scanner/pipeline/__init__.py` oder der direkte Aufrufer der Shortlist-Stufe, falls Signatur/Config-Zugriff angepasst werden muss
- ggf. kleine testnahe Hilfsfunktionen, falls erforderlich

## Out of Scope
- Keine neue Tradeability-Berechnung
- Keine Orderbook-Top-K-Implementierung jenseits der Übergabe/Beachtung des Budgetmodells
- Keine Risk-/Decision-Logik
- Keine Output-/Manifest-Änderung
- Keine Änderung an harten Safety-Excludes (liegt in PR-03)
- Keine Änderung der Cheap-Pass-Score-Formel, sofern nicht zwingend nötig für Determinismus oder Config-Anbindung

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`

## Proposed change (high-level)
Before:
- Die Shortlist arbeitet auf einem historisch engeren Filterpool.
- Budgetparameter und Naming sind nicht vollständig auf V4.2.1 ausgerichtet.
- Der Pre-Shortlist-Floor ist nicht als harter, expliziter Guardrail vor dem Cheap-Pass festgezogen.

After:
- Die Shortlist liest `budget.shortlist_size` zentral aus der Config.
- Default ist 200, kompatibel zur Canonical Definition.
- Coins unter `budget.pre_shortlist_market_cap_floor_usd` belegen keine Shortlist-Plätze.
- Der Cheap-Pass bleibt der Ranking-Mechanismus für die Budgetselektion.
- Die Shortlist liefert höchstens `shortlist_size` Kandidaten.
- Die Shortlist-Reihenfolge ist deterministisch, inklusive klarer Tie-Breaker.

Edge cases:
- Weniger Kandidaten als `shortlist_size` => alle zulässigen Kandidaten werden übernommen
- Mehr Kandidaten als `shortlist_size` => strikt auf Cap begrenzen
- Kandidaten mit identischem Cheap-Pass-Score => deterministischer Tie-Breaker
- Coin oberhalb des alten MarketCap-Max, aber oberhalb des neuen Floors => darf shortgelistet werden
- Coin unter neuem Floor => darf keinen Shortlist-Platz erhalten

Backward compatibility impact:
- Shortlist kann bei gleichem Run mehr / andere Kandidaten enthalten als in der alten Logik.
- Config-Defaults müssen kompatibel bleiben; fehlende neue Budget-Keys dürfen nicht hart brechen.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** `budget.shortlist_size = 200` und `budget.pre_shortlist_market_cap_floor_usd` gelten gemäß Canonical/Config-Defaults.
- **No raw-dict default drift:** Budgetwerte nur über zentrale Config-/Default-Logik lesen.
- **Cap strikt einhalten:** Shortlist darf nie mehr als `budget.shortlist_size` Kandidaten enthalten.
- **Pre-Shortlist-Floor respektieren:** Coins unter dem Floor dürfen vor dem Ranking keine Plätze belegen.
- **Cheap-Pass bleibt Cheap-Pass:** Keine Tradeability-/Orderbook-Logik in die Shortlist ziehen.
- **Determinismus ist Pflicht:** Gleicher Input + gleiche Config => gleiche Auswahl und gleiche Reihenfolge.
- **Tie-Breaker explizit:** Wenn bestehender Code keinen stabilen Tie-Breaker garantiert, muss einer eingeführt werden (z. B. symbol/market-spezifisch, aber explizit und stabil).
- **Keine stillen Koerzierungen:** Ungültige Budgetwerte dürfen nicht implizit in brauchbar wirkende Werte umgewandelt werden.

## Implementation Notes (optional but useful)
- Prüfe, ob `shortlist.py` bereits einen Proxy Liquidity Score oder ähnlichen Cheap-Pass berechnet.
- Ziel ist primär:
  - Config-Anbindung,
  - Cap auf 200,
  - harter Vorfilter via `pre_shortlist_market_cap_floor_usd`,
  - deterministische Auswahl/Reihenfolge.
- Falls der Floor bereits in PR-03 auf Filterebene hart greift, darf PR-04 ihn nicht verwässern; die Shortlist muss aber weiterhin korrekt damit umgehen, falls sie Kandidaten mit Floor-Feld verarbeitet.
- Falls `orderbook_top_k` in derselben Stufe indirekt gesteuert wird, nur config-driven Durchleitung anpassen, keine neue Semantik erfinden.

## Acceptance Criteria (deterministic)
1) Die Shortlist liest `budget.shortlist_size` zentral aus der Config; Default ist 200.

2) Die Shortlist gibt nie mehr als `budget.shortlist_size` Kandidaten zurück.

3) Wenn weniger zulässige Kandidaten als `budget.shortlist_size` vorhanden sind, werden alle zulässigen Kandidaten zurückgegeben.

4) Coins unter `budget.pre_shortlist_market_cap_floor_usd` erhalten keinen Shortlist-Platz.

5) Coins oberhalb des neuen Floors dürfen unabhängig vom früheren `market_cap.max_usd` shortgelistet werden, sofern ihr Cheap-Pass-Ranking hoch genug ist.

6) Der Cheap-Pass bleibt die Auswahlbasis; es werden in diesem PR keine Orderbook-/Tradeability-Metriken in die Shortlist aufgenommen.

7) Bei identischem Input und identischer Config ist sowohl die Auswahl als auch die Reihenfolge der Shortlist deterministisch.

8) Bei identischem Cheap-Pass-Score mehrerer Kandidaten ist ein stabiler, expliziter Tie-Breaker wirksam.

9) Fehlende neue Budget-Keys greifen über zentrale Defaults; ungültige Budgetwerte erzeugen einen klaren Fehler.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (AC: #1, #9 ; Test: fehlender `budget.shortlist_size` => zentraler Default 200)
- **Config Invalid Value Handling:** ✅ (AC: #9 ; Test: `shortlist_size <= 0` oder nicht-numerisch => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (N/A — keine neuen nullable Output-Felder; keine implizite bool-Koerzierung für Score-/Budgetzustände)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #4, #6 ; Test: nicht-shortgelistet wegen Budget/Floor ≠ failed evaluiert in späteren Stages)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A — kein Datei-/ID-Generator)
- **Deterministische Sortierung / Tie-breaker:** ✅ (AC: #7, #8 ; Test: stabile Reihenfolge bei Score-Gleichstand)

## Tests (required if logic changes)
- Unit:
  - Missing `budget.shortlist_size` => zentraler Default 200
  - Invalid `budget.shortlist_size` => klarer Fehler
  - Shortlist cap wird strikt eingehalten
  - Weniger Kandidaten als Cap => alle zulässigen Kandidaten werden übernommen
  - Coins unter Floor werden nicht shortgelistet
  - Coins über altem MarketCap-Max können shortgelistet werden
  - Score-Gleichstand => stabiler Tie-Breaker greift
  - Kein Orderbook-/Tradeability-Feld beeinflusst die Shortlist in diesem PR

- Integration:
  - Gemischte Universe-Fixture mit >200 zulässigen Coins ergibt exakt 200 Shortlist-Kandidaten
  - Identische Fixture + identische Config => identische Shortlist-Reihenfolge
  - Fixture mit <200 zulässigen Coins gibt alle zulässigen Kandidaten zurück

- Golden fixture / verification:
  - Falls bestehende Fixtures die exakte Shortlist-Reihenfolge festhalten, bewusst auf neue deterministische Reihenfolge aktualisieren
  - `docs/canonical/VERIFICATION_FOR_AI.md` nur anpassen, falls dort Shortlist-/Budgetverhalten explizit verifiziert wird

## Constraints / Invariants (must not change)
- [ ] Cheap-Pass bleibt günstiger Vorselektion-Mechanismus
- [ ] Keine Orderbook-/Tradeability-Logik in dieser Stufe
- [ ] Cap auf `budget.shortlist_size` bleibt strikt
- [ ] Coins unter `pre_shortlist_market_cap_floor_usd` belegen keine Plätze
- [ ] Deterministische Auswahl und Reihenfolge
- [ ] Keine Decision-/Risk-/Output-Semantik in diesem Ticket

## Definition of Done (Codex must satisfy)
- [ ] Codeänderungen gemäß Acceptance Criteria implementiert
- [ ] Unit-/Integration-Tests gemäß Ticket ergänzt oder angepasst
- [ ] Deterministische Tie-Breaker explizit abgesichert
- [ ] Keine Scope-Überschreitung in Tradeability-/Risk-/Decision-/Output-Logik
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-07T00:00:00Z"
priority: P0
type: feature
owner: codex
related_issues: []
```
