## Title
[P0] PR-07 Tradeability Gate in die Pipeline einbauen

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- PR-06 liefert die Tradeability-Klassifikation pro Coin; PR-07 verankert diese Klassifikation an der richtigen Stelle in der Pipeline.
- Laut Canonical/V4.2.1 gilt die Reihenfolge:
  Universe → Mapping → Safety Excludes → Pre-Shortlist Floor → Cheap Shortlist → Orderbook Fetch → Tradeability Gate → OHLCV Fetch → Features → Scoring → Risk/Downside → Decision Layer → Output.
- UNKNOWN-Coins werden in Phase 1 nicht weiter evaluiert und dürfen keine OHLCV-/Feature-/Scoring-Kosten verursachen.

## Goal
`scanner/pipeline/__init__.py` integriert ein globales Tradeability Gate nach dem Orderbook-Fetch und vor OHLCV/Features, sodass:
- jeder shortgelistete Coin mit Orderbook eine `tradeability_class` bekommt,
- nur Coins mit `tradeability_class ∈ {DIRECT_OK, TRANCHE_OK, MARGINAL}` weiterlaufen,
- Coins mit `FAIL` oder `UNKNOWN` explizit gestoppt werden,
- OHLCV-Calls für `FAIL`/`UNKNOWN` entfallen.

## Scope
- `scanner/pipeline/__init__.py`
- ggf. enge, direkte Anpassungen an Aufrufsignaturen zwischen `__init__.py`, `liquidity.py` und `ohlcv.py`, soweit für die Gate-Position zwingend nötig
- ggf. kleine Pipeline-nahe Hilfslogik für explizite Stop-/Reason-Behandlung

## Out of Scope
- Keine neue Tradeability-Berechnung (kommt aus PR-06)
- Keine Risk-/Downside-Logik
- Keine Decision-Layer-Implementierung
- Keine Output-Renderer-Umstellung
- Keine BTC-Regime-Logik
- Keine Shadow-Mode-/Migration-Logik
- Keine Änderung der Cheap-Shortlist oder Filter-Semantik
- Keine neue Score-Logik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`

## Proposed change (high-level)
Before:
- Orderbook-/Liquidity-Daten werden budgetiert erhoben, aber die neue V4.2.1-Tradeability-Klassifikation ist noch nicht als globales Pipeline-Gate verankert.
- Coins können trotz fehlender belastbarer Tradeability unnötig in spätere teure Stages laufen.

After:
- Nach dem Orderbook-Fetch wird für jeden Kandidaten die Tradeability berechnet.
- Globales Gate:
  - `DIRECT_OK` → weiter
  - `TRANCHE_OK` → weiter
  - `MARGINAL` → weiter
  - `FAIL` → stoppt vor OHLCV/Features/Scoring
  - `UNKNOWN` → stoppt vor OHLCV/Features/Scoring
- Für `FAIL` und `UNKNOWN` werden strukturierte Gründe an der Pipeline-Grenze festgehalten.
- OHLCV-Fetch wird nur für weiterzulassende Coins ausgeführt.
- UNKNOWN bleibt ein Stop-Pfad vor der Decision Layer; UNKNOWN wird nicht als WAIT behandelt.

Edge cases:
- Coin außerhalb des Orderbook-Budgets => `UNKNOWN` und kein OHLCV
- Fetch-Exception / leeres Orderbook => `UNKNOWN` und kein OHLCV
- Coin mit `MARGINAL` => läuft weiter und kann später WAIT/NO_TRADE werden
- Coin mit `FAIL` => expliziter Stop, kein stilles Degraden
- Wenn weniger Coins weiterlaufen als shortgelistet wurden, muss der restliche Pipeline-Flow trotzdem stabil bleiben

Backward compatibility impact:
- Die Pipeline verarbeitet nach dem Orderbook-Fetch potenziell weniger Coins als bisher in OHLCV/Features.
- Das ist beabsichtigt und reduziert API-/Laufzeitkosten.
- Vorhandene nachgelagerte Stages müssen mit kleinerem Input sauber umgehen.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Gate-Position exakt wie in `PIPELINE.md`.
- **Globales Gate, nicht setup-spezifisch:** PR-07 filtert auf Coin-/Orderbook-Ebene, nicht pro Setup-Typ.
- **UNKNOWN nicht durchreichen:** UNKNOWN darf weder OHLCV-Fetch noch Feature-/Scoring-/Decision erreichen.
- **FAIL nicht still degradieren:** FAIL muss explizit gestoppt und begründet werden.
- **MARGINAL durchlassen:** MARGINAL ist voll evaluiert und bleibt für spätere Decision/Risk offen.
- **Keine WAIT-Semantik hier:** Dieses Ticket baut das technische Gate, nicht die fachliche Decision.
- **Missing vs Invalid sauber:** Coin außerhalb Orderbook-Budget, Fetch-Fehler und stale Daten dürfen nicht still als FAIL markiert werden.
- **Determinismus:** Gleicher Input + gleiche Config => identische Menge an weitergelassenen Coins.
- **Keine zusätzlichen OHLCV-Calls:** FAIL/UNKNOWN dürfen keine OHLCV-Kosten verursachen.
- **Keine neue zweite Wahrheit im Output:** Wenn Pipeline-interne Stopgründe persistiert werden, müssen sie kanonisch benannt sein.

## Implementation Notes (optional but useful)
- Prüfe in `scanner/pipeline/__init__.py`, wo aktuell:
  - shortlist result
  - orderbook fetch
  - liquidity metrics
  - OHLCV fetch
  - features/scoring
  aufeinander folgen.
- Das Gate sollte als klar benannte Stufe implementiert werden, nicht als verstreute `if`-Logik an mehreren Stellen.
- Wenn bestehende Snapshot-/Runtime-Meta-Strukturen Kandidatenlisten spiegeln, nur minimal anpassen; keine Output-SoT-Umstellung in diesem PR.
- Für gestoppte Coins kann ein internes Sammelobjekt oder reason-trace sinnvoll sein, aber keine neue Output-Semantik erfinden.

## Acceptance Criteria (deterministic)
1) In `scanner/pipeline/__init__.py` wird die Tradeability-Berechnung nach dem Orderbook-Fetch und vor dem OHLCV-Fetch ausgeführt.

2) Jeder Coin mit Orderbook-Bewertung erhält eine `tradeability_class` aus PR-06.

3) Nur Coins mit `tradeability_class ∈ {DIRECT_OK, TRANCHE_OK, MARGINAL}` werden an OHLCV/Features/Scoring weitergereicht.

4) Coins mit `tradeability_class = FAIL` werden vor OHLCV/Features/Scoring gestoppt.

5) Coins mit `tradeability_class = UNKNOWN` werden vor OHLCV/Features/Scoring gestoppt.

6) Für gestoppte Coins werden explizite, maschinenlesbare Gründe erhalten oder durchgereicht; UNKNOWN-Gründe bleiben differenzierbar (`orderbook_data_missing`, `orderbook_data_stale`, `orderbook_not_in_budget`).

7) Für FAIL/UNKNOWN-Coins werden keine OHLCV-Calls ausgelöst.

8) Die Pipeline bleibt stabil, auch wenn nach dem Gate deutlich weniger Coins weiterlaufen als shortgelistet wurden.

9) Die Gate-Entscheidung ist bei identischem Input und identischer Config deterministisch.

10) PR-07 führt keine Decision-Statuswerte (`ENTER`, `WAIT`, `NO_TRADE`) ein.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (Test: deaktivierte/fehlende Gate-nahe Keys nutzen zentrale Defaults; keine ad-hoc Fallbacks)
- **Config Invalid Value Handling:** ✅ (Test: ungültige Gate-relevante Config führt zu klarem Fehler; kein stilles Weiterlaufen)
- **Nullability / kein bool()-Coercion:** ✅ (Test: `tradeability_class = UNKNOWN` bleibt UNKNOWN und wird nicht via `bool(...)` implizit zu FAIL)
- **Not-evaluated vs failed getrennt:** ✅ (AC #4, #5, #6, #7)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A)
- **Deterministische Sortierung / Tie-breaker:** ✅ (AC #9 ; Test: identische Pipeline-Eingabe => identische weitergelassene Coin-Menge)

## Tests (required if logic changes)
- Unit:
  - Coin mit DIRECT_OK läuft weiter
  - Coin mit TRANCHE_OK läuft weiter
  - Coin mit MARGINAL läuft weiter
  - Coin mit FAIL stoppt vor OHLCV
  - Coin mit UNKNOWN stoppt vor OHLCV
  - UNKNOWN-Gründe bleiben differenziert
  - Keine Decision-Statuswerte werden in diesem PR erzeugt

- Integration:
  - Pipeline-Fixture mit gemischten Tradeability-Klassen führt nur für DIRECT_OK/TRANCHE_OK/MARGINAL OHLCV-Fetch aus
  - FAIL/UNKNOWN erzeugen keine OHLCV-Calls
  - Reduzierte Coin-Menge nach Gate bricht Features/Scoring nicht
  - Identischer Input + identische Config => identisches Gate-Ergebnis

- Golden fixture / verification:
  - Falls bestehende Pipeline-Golden-Files die bisherige Kandidatenanzahl nach OHLCV fest verdrahten, nur dort bewusst aktualisieren, wo das neue Gate diese Menge reduziert
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] Gate sitzt nach Orderbook-Fetch und vor OHLCV
- [ ] UNKNOWN bleibt Stop-Pfad vor Decision
- [ ] MARGINAL bleibt durchlässig
- [ ] FAIL und UNKNOWN verursachen keine OHLCV-Kosten
- [ ] Keine Decision-/Risk-/Output-SoT-Logik in diesem Ticket
- [ ] Deterministisches Gate-Verhalten

## Definition of Done (Codex must satisfy)
- [ ] Codeänderungen gemäß Acceptance Criteria implementiert
- [ ] Unit-/Integration-Tests gemäß Ticket ergänzt oder angepasst
- [ ] FAIL vs UNKNOWN vs weiterlaufende Klassen sauber getrennt
- [ ] Keine Scope-Überschreitung in Decision/Risk/Output
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
