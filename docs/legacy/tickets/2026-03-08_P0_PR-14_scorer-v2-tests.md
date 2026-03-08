> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-14 Scorer-V2-Tests

## Context / Source
- Die aktuelle alleinige Referenz definiert in EPIC 6 / PR-14 ein explizites Testnetz für die erweiterten Setup-Scorer.
- PR-12 und PR-13 haben die Setup-Scorer auf strukturierte, WAIT-fähige Outputs umgestellt.
- Die Decision Layer im nächsten Epic darf ausschließlich auf diesen strukturierten Outputs operieren und keine Heuristik oder Text-Parsing mehr benötigen.
- Die neuen verbindlichen Ticket-Regeln gelten: deterministische Tests, klare Nullability, not-evaluated vs negative evaluation getrennt, keine impliziten Bool-Koerzierungen, kein stilles Interpretieren.

## Goal
Ein deterministisches Testnetz für die Setup-Scorer V2 bereitstellen, das absichert:
- `entry_ready` ist nur bei wirklich reifen Setups `true`
- Breakout-/Retest-/Reversal-/Rebound-Felder werden korrekt gesetzt
- Reason-Listen sind bei nicht entry-ready Kandidaten aussagekräftig und nicht leer
- Reversal ohne Reclaim wird explizit als nicht entry-ready behandelt
- gleiche Eingaben erzeugen gleiche Scorer-Outputs

## Scope
- Testdateien unter `tests/`, insbesondere scorer-/pipeline-nahe Tests
- bestehende Setup-Scorer-Tests anpassen oder ergänzen
- ggf. neue dedizierte Testdatei für V2-Scorer-Outputs anlegen
- kleine Testhilfen/Fixtures, falls für deterministische Eingabefälle nötig

## Out of Scope
- Keine Produktionscode-Änderung an den Setup-Scorern selbst, außer minimal zwingende Test-Hooks
- Keine Decision Layer
- Keine Risk-Berechnung
- Keine Tradeability-Logik
- Keine BTC-Regime-Logik
- Keine Output-Renderer oder Output-Schema-Änderung
- Keine Canonical-Dokumente ändern

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`
- einschlägige Canonical-Dokumente für Setup-/Scorer-Felder
- `docs/tickets/_TEMPLATE.md`
- die aktuelle verbindliche Ticket-Preflight-Checkliste

## Proposed change (high-level)
Before:
- Die Setup-Scorer liefern zwar bereits strukturierte Felder, aber die neue WAIT-/Entry-Readiness-Semantik ist noch nicht vollständig regressionssicher getestet.
- Besonders grenzwertige Fälle wie „Reversal ohne Reclaim“ oder „Breakout nicht bestätigt“ müssen explizit und deterministisch abgesichert werden.

After:
- Es existieren deterministische Tests für die zentralen Scorer-V2-Ausgaben:
  - `entry_ready`
  - `breakout_confirmed`
  - `retest_reclaimed`
  - `rebound_confirmed` bzw. analoges kanonisches Feld
  - `setup_reason_keys` / Scorer-Reason-Listen
- Reversal ohne Reclaim ist explizit abgesichert:
  - `entry_ready = false`
  - Reason enthält `retest_not_reclaimed`
- Reason-Listen sind bei `entry_ready = false` nicht leer.
- Die Outputs sind bei identischem Input deterministisch.

Edge cases:
- Breakout-Level knapp verfehlt
- Close unter Breakout-Level trotz sonst guter Struktur
- Retest vorhanden, aber Reclaim nicht erfolgt
- Reversal-Bedingungen teilweise erfüllt, aber Reclaim fehlt
- Reason-Felder leer oder `None`, obwohl `entry_ready = false`
- grenzwertige numerische Inputs, soweit für die Scorer relevant

Backward compatibility impact:
- Keine fachliche Verhaltensänderung beabsichtigt; Ticket erhöht/aktualisiert die Testabdeckung für die V2-Scorer-Semantik.
- Bestehende Tests dürfen angepasst werden, wenn sie ältere Heuristik- oder Naming-Annahmen fest verdrahten.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Es werden ausschließlich kanonische Feldnamen und Reason Keys getestet.
- **Kein Text-Parsing in der Decision vorbereiten:** Tests müssen strukturierte Felder absichern, nicht freie Report-Texte.
- **`entry_ready` ist bool, aber nur für voll evaluierte Setup-Reife:** nicht durch fehlende Daten oder implizite truthiness ableiten.
- **Reason-Listen explizit prüfen:** Bei `entry_ready = false` muss mindestens ein passender Reason Key gesetzt sein.
- **Reversal ohne Reclaim ist Pflichtfall:** Dieser Fall muss explizit und nicht nur indirekt getestet werden.
- **Determinismus ist Pflicht:** Identische Inputs müssen identische Felder und identische Reason-Listen liefern.
- **Keine Scope-Ausweitung:** Dieses Ticket testet Scorer-V2-Verträge, nicht Decision-/Risk-/Tradeability-Logik.

## Implementation Notes (optional but useful)
- Vorhandene scorer-nahe Tests im Repo bevorzugt erweitern, wenn deren Zuschnitt passt.
- Falls bestehende Tests stark an alte Score-Heuristiken gebunden sind, eine neue dedizierte Datei für V2-Scorer-Outputs anlegen.
- Deterministische kleine Fixtures bevorzugen; keine externen Datenquellen oder fuzzy Marktinputs.
- Wenn numerische Hilfswerte benutzt werden, explizit stabile Inputs wählen.

## Acceptance Criteria (deterministic)
1) Es existieren Tests, die absichern: `entry_ready` ist nur dann `true`, wenn das Setup tatsächlich reif ist.

2) Es existieren Tests, die absichern: `breakout_confirmed = false`, wenn der Close unter dem Breakout-Level liegt.

3) Es existieren Tests, die absichern: `retest_reclaimed = false`, wenn Preis/Close unter dem Reclaim-/EMA-/Support-Kriterium bleibt.

4) Es existiert ein expliziter Testfall für Reversal ohne Reclaim:
   - `entry_ready = false`
   - Reason enthält `retest_not_reclaimed`

5) Es existieren Tests, die absichern: Reason-Listen sind bei `entry_ready = false` nicht leer.

6) Bei identischem Input und identischer Config sind alle relevanten Scorer-V2-Outputs deterministisch identisch.

7) Kein Test in diesem PR behauptet oder impliziert Decision-, Risk-, BTC-Regime- oder Output-Renderer-Semantik, die erst in späteren Tickets eingeführt wird.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ Falls die Scorer V2 konfigurierbare Schwellen verwenden, muss mindestens ein Test den zentralen Default-Pfad prüfen.
- **Config Invalid Value Handling:** ✅ Falls konfigurierbare Schwellen relevant sind, muss mindestens ein Test ungültige Werte als klaren Fehler prüfen.
- **Nullability / kein bool()-Coercion:** ✅ Keine implizite truthiness-Prüfung für Reason-Listen oder numerische Hilfswerte; strukturierte Felder explizit prüfen.
- **Not-evaluated vs failed getrennt:** ✅ Nicht entry-ready ist nicht dasselbe wie fehlende Evaluierbarkeit; Tests dürfen diese Zustände nicht verwischen.
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A — Testticket ohne Writer-/CLI-Output.
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A.
- **Deterministische Sortierung / Tie-breaker:** ✅ Soweit Reason-Listen oder Felder geordnet sind, muss bei identischem Input dieselbe Ordnung entstehen.

## Tests (required if logic changes)
- Unit:
  - `entry_ready = true` nur bei tatsächlich reifem Setup
  - `breakout_confirmed = false` bei Close unter Breakout-Level
  - `retest_reclaimed = false` bei fehlendem Reclaim
  - expliziter Reversal-ohne-Reclaim-Fall mit `retest_not_reclaimed`
  - Reason-Liste nicht leer bei `entry_ready = false`
  - ggf. Default-Pfad für konfigurierbare Schwellen
  - ggf. ungültige Schwellen => klarer Fehler

- Integration:
  - kleiner deterministischer Fixture-Durchlauf über mehrere Setup-Typen
  - identischer Input + identische Config => identische V2-Outputs
  - keine externen IO-/Netzwerkzugriffe

- Golden fixture / verification:
  - Nur anpassen, wenn bestehende Golden-/Snapshot-Tests alte Setup-Heuristik oder Feldnamen fest verdrahten
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] Scorer liefern strukturierte V2-Felder, keine Heuristik-Texte als Wahrheit
- [ ] Reversal ohne Reclaim bleibt nicht entry-ready
- [ ] Reason-Listen bleiben bei negativem Setup nicht leer
- [ ] Keine Decision-/Risk-/BTC-/Output-Semantik in diesem Ticket
- [ ] Tests bleiben deterministisch und offline

## Definition of Done (Codex must satisfy)
- [ ] Testdateien erstellt oder aktualisiert
- [ ] Acceptance Criteria testseitig abgedeckt
- [ ] Reversal-ohne-Reclaim-Fall explizit abgesichert
- [ ] Determinismus der V2-Scorer-Outputs abgesichert
- [ ] Keine Scope-Überschreitung in spätere Epics
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-08T00:00:00Z"
priority: P0
type: test
owner: codex
related_issues: []
```
