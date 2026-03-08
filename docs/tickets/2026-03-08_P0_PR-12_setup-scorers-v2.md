## Title
[P0] PR-12 Setup-Scorer V2

## Context / Source
- Die aktuell alleinige Referenz verlangt, dass die Setup-Scorer strukturierte, decision-taugliche Felder liefern.
- Dieses Ticket setzt PR-12 der gültigen Epic-/PR-Struktur um.
- Die Decision Layer darf später keine implizite Heuristik mehr aus freien Texten oder scorer-spezifischen Sonderfällen ableiten müssen.
- Die neuen verbindlichen Ticket-Regeln gelten vollständig, insbesondere:
  - Missing vs invalid sauber trennen
  - Nullable Felder explizit behandeln
  - not-evaluated vs failed getrennt halten
  - keine stillen Alias-Felder oder freien Statusbegriffe einführen

## Goal
Die Setup-Scorer liefern V2-Outputs mit standardisierten, maschinenlesbaren Feldern zur Entry-Reife und Setup-Einordnung, sodass spätere PRs (WAIT-Reason-Standardisierung, Decision Layer) nur noch Regeln auf strukturierte Felder anwenden müssen.

## Scope
- `scanner/pipeline/scoring/breakout.py`
- `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `scanner/pipeline/scoring/pullback.py`
- `scanner/pipeline/scoring/reversal.py`
- falls nötig: gemeinsame scorer-nahe Typen/Hilfsfunktionen im direkten Scoring-Kontext
- falls nötig: direkte scorer-nahe Tests, soweit unbedingt erforderlich, aber keine vollständige Test-Suite dieses PRs vorwegnehmen

## Out of Scope
- Keine Decision Layer
- Keine WAIT-/Decision-Reason-Matrix als globale Policy
- Keine Tradeability-Änderung
- Keine Risk-Berechnung
- Keine BTC-Regime-Logik
- Keine Output-/Renderer-Anpassung
- Keine Portfolio-/Exit-/Hold-Logik
- Keine Directional-Volume-Logik als aktive Bewertungslogik
- Keine stillen Schema-Änderungen außerhalb der betroffenen Scorer

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/RISK_MODEL.md`
- relevante bestehende Canonical-Scoring-/Pipeline-Dokumente unter `docs/canonical/*`

## Proposed change (high-level)
Before:
- Scorer liefern heute primär Score-/Signal-Outputs, aber die Entry-Reife und Setup-Teilzustände sind nicht in einem ausreichend standardisierten, decision-fähigen V2-Format verfügbar.
- Reversal-/Pullback-/Breakout-spezifische Bedingungen müssen teilweise implizit interpretiert werden.

After:
- Alle betroffenen Scorer liefern zusätzliche strukturierte Felder:
  - `entry_ready: bool`
  - `entry_readiness_reason: str | None` oder scorer-interne Vorstufe, falls PR-13 auf `entry_readiness_reasons: List[str]` standardisiert
  - scorer-spezifische Bestätigungsfelder wie:
    - `breakout_confirmed: bool` (nur Breakout)
    - `retest_reclaimed: bool` (Pullback/Reversal, wenn fachlich passend)
    - `reclaim_confirmed: bool` (Reversal)
    - `rebound_confirmed: bool` (Pullback)
  - `setup_subtype: str`
- Reversal-spezifische harte Fachregel:
  - Reversal ohne bestätigten Reclaim ist **nicht entry-ready**
  - `entry_ready = false`
  - Reason signalisiert `retest_not_reclaimed`
- Das Scorer-Output bleibt **additiv erweiterbar**, damit spätere Felder wie Directional Volume ohne Breaking Change ergänzt werden können.

Edge cases:
- ein Setup ist scorbar, aber nicht entry-ready
- Reversal-Hypothese ohne Reclaim
- Breakout-Level knapp verfehlt
- Pullback ohne bestätigten Rebound
- fehlende Daten für scorer-spezifische Teilflags
- `setup_subtype` darf nicht still leer oder frei-formatiert inkonsistent sein

Backward compatibility impact:
- Scorer-Outputs erweitern sich um zusätzliche strukturierte Felder.
- Bestehende reine Score-Pfade sollen möglichst kompatibel bleiben, dürfen aber nicht die neuen Felder verfälschen oder überschreiben.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Neue Felder und Begriffe nur verwenden, wenn sie zur aktuellen alleinigen Referenz und Canonical passen.
- **Keine freie Textheuristik als Hauptwahrheit:** Die Decision-relevante Reife muss über strukturierte Felder abbildbar sein.
- **Keine stillen Alias-Namen:** Nicht mehrere Varianten für denselben Zustand einführen.
- **Reversal-Regel ist hart:** Reversal ohne bestätigten Reclaim ist nicht entry-ready. Das ist keine weiche Heuristik.
- **Missing vs negative sauber trennen:** Fehlende Daten für ein Teilflag sind nicht automatisch dasselbe wie ein fachlich negatives Signal; falls fehlende Daten zu `false` führen sollen, muss dies kanonisch und im Code klar sein.
- **Keine stille Null-/Bool-Koerzierung:** Semantisch fehlende/optionale Felder dürfen nicht implizit per `bool(...)` in `false` umgedeutet werden.
- **`setup_subtype` deterministisch:** Kein freier, unstabiler Stringbau; nur klar definierte subtype-Werte.
- **Additiv erweiterbar:** Das Output-Schema der Scorer darf für spätere Zusatzfelder erweiterbar sein, ohne den V2-Contract zu brechen.
- **Keine globale WAIT-Reason-Policy in diesem PR:** Dieses Ticket liefert Inputs, standardisiert aber noch nicht die vollständige Decision-Reason-Liste von PR-13/15.

## Zusätzliche Pflichtsektion für numerische / Config-lastige Tickets
- [ ] Partielle Nested-Overrides: merge oder replace explizit festlegen
- [ ] Nicht-finite Werte (`NaN`, `inf`, `-inf`) explizit behandeln
- [ ] Nullable Ergebnisse explizit als nullable markieren
- [ ] Nicht auswertbar ≠ negativ bewertet
- [ ] Fehlender Key ≠ ungültiger Key
- [ ] Konkrete Tests für genau diese Fälle ausschreiben

Hinweis zu diesem Ticket:
- Es führt primär strukturierte scorer-Felder ein und ist nicht primär config-lastig.
- Falls scorer-interne numerische Flags auf bestehenden Indikatoren/Preislevels beruhen, gelten trotzdem:
  - nicht-finite Inputs dürfen nicht still in scheinbar gültige scorer-Felder übergehen
  - fehlende Vorbedingungen müssen explizit und deterministisch behandelt werden

## Implementation Notes (optional but useful)
- Prüfe, ob bestehende Scorer bereits interne Teilzustände berechnen, die direkt auf die neuen Felder gemappt werden können.
- Neue Felder möglichst an einer klaren Stelle im jeweiligen scorer-output zusammenführen.
- Für `setup_subtype` pro Scorer nur eine kleine, stabile Wertemenge verwenden, z. B.:
  - Breakout: `fresh_breakout`, `confirmed_breakout`
  - Pullback: `pullback_to_ema`, `pullback_to_support`
  - Reversal: `reversal_base_reclaim`
- Wenn ein Teilflag fachlich nicht anwendbar ist, nicht durch erfundene Default-Semantik verwässern; sauber dokumentieren oder auf PR-13-Standardisierung vorbereiten.

## Acceptance Criteria (deterministic)
1) Die betroffenen Scorer liefern zusätzliche strukturierte V2-Felder für Entry-Reife und Setup-Zustand.

2) Jeder betroffene Scorer liefert mindestens:
   - `entry_ready`
   - `setup_subtype`

3) Breakout-Scorer liefern zusätzlich ein explizites Feld zur Breakout-Bestätigung, z. B. `breakout_confirmed`.

4) Pullback-/Reversal-Scorer liefern explizite Felder zur Reclaim-/Rebound-Bestätigung, soweit fachlich anwendbar.

5) Reversal ohne bestätigten Reclaim wird deterministisch mit `entry_ready = false` markiert.

6) Für Reversal ohne bestätigten Reclaim ist der Readiness-Grund fachlich als `retest_not_reclaimed` abbildbar und nicht nur implizit über Score/Kommentar versteckt.

7) `setup_subtype` wird deterministisch aus einer klaren, scorer-spezifischen, stabilen Wertemenge gesetzt.

8) Nicht-finite oder fachlich unbrauchbare interne numerische Inputs führen nicht zu stillschweigend „gültig“ wirkenden V2-Feldern.

9) Dieses PR führt keine globale Decision-Statuslogik (`ENTER`, `WAIT`, `NO_TRADE`) ein.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ N/A, sofern keine neue Config eingeführt wird; falls scorer neue Config nutzt, explizit Missing-vs-Default festlegen
- **Config Invalid Value Handling:** ✅ N/A, sofern keine neue Config eingeführt wird; andernfalls klarer Fehler statt stiller Koerzierung
- **Nullability / kein bool()-Coercion:** ✅ relevante optionale/fehlende Teilzustände nicht still zu `false` kollabieren
- **Not-evaluated vs failed getrennt:** ✅ fehlende Teilinformationen ≠ fachlich negatives Gesamtsignal, außer explizit definierte Fachregel
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A
- **Deterministische Sortierung / Tie-breaker:** ✅ `setup_subtype` und Teilflags deterministisch

## Tests (required if logic changes)
- Unit:
  - `entry_ready` ist true nur bei tatsächlich reifen Setups
  - `breakout_confirmed` ist false, wenn Close unter Breakout-Level
  - `retest_reclaimed` / `reclaim_confirmed` ist false, wenn Reclaim fachlich nicht bestätigt ist
  - Reversal ohne Reclaim: `entry_ready = false`
  - Reversal ohne Reclaim: Reason ist fachlich `retest_not_reclaimed`
  - `setup_subtype` kommt aus stabiler definierter Wertemenge
  - nicht-finite scorer-relevante numerische Inputs erzeugen keine scheinbar gültigen Bestätigungsfelder

- Integration:
  - bestehende scorer outputs bleiben für nachgelagerte Nutzung kompatibel erweitert
  - identischer Input führt zu identischen V2-Feldern

- Golden fixture / verification:
  - Nur anpassen, wenn bestehende Golden-Tests die alten scorer outputs vollständig fest verdrahten
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] Reversal ohne Reclaim bleibt nicht entry-ready
- [ ] Keine globale Decision- oder WAIT-Policy in diesem PR
- [ ] Neue scorer-Felder bleiben additiv und maschinenlesbar
- [ ] Keine stillen Alias-Felder für denselben Zustand
- [ ] Nicht-finite Inputs werden nicht als gültige scorer-signals durchgereicht
- [ ] `setup_subtype` bleibt stabil und deterministisch

## Definition of Done (Codex must satisfy)
- [ ] Betroffene Scorer implementieren die V2-Felder
- [ ] Akzeptanzkriterien erfüllt
- [ ] Tests gemäß Ticket ergänzt/aktualisiert
- [ ] Keine Scope-Überschreitung in Decision/Risk/Output
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-08T00:00:00Z"
priority: P0
type: feature
owner: codex
related_issues: []
```
