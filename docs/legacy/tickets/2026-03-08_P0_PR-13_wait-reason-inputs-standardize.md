> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-13 WAIT-Reason-Inputs standardisieren

## Context / Source
- Die aktuell alleinige Referenz verlangt, dass alle betroffenen Scorer ein standardisiertes, decision-taugliches Interface liefern.
- PR-12 führt die neuen scorer-spezifischen V2-Felder ein; PR-13 zieht diese in ein gemeinsames, standardisiertes Output-Format über.
- Ziel ist, dass die Decision Layer keine scorer-spezifische Interpretation oder Parsing-Logik mehr braucht.

## Goal
Alle relevanten Setup-Scorer liefern ein standardisiertes Dict mit Decision-relevanten Inputs, sodass nachgelagerte PRs rein regelbasiert arbeiten können.

## Scope
- alle betroffenen Scorer unter `scanner/pipeline/scoring/`
- ggf. gemeinsamer Typ / Hilfsfunktion / Normalisierungslogik im direkten Scoring-Kontext
- ggf. bestehende scorer-nahe Tests, soweit für das standardisierte Interface nötig

## Out of Scope
- Keine Decision Layer
- Keine globale Decision-Reason-Matrix außerhalb der scorer-inputs
- Keine Tradeability-/Risk-Änderung
- Keine BTC-Regime-Logik
- Keine Output-Renderer
- Keine Portfolio-/Exit-/Hold-Logik
- Keine freien zusätzlichen Felder außerhalb des standardisierten Contracts, sofern nicht additiv und klar als optional markiert

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- relevante Canonical-Scoring-/Pipeline-Dokumente unter `docs/canonical/*`

## Proposed change (high-level)
Before:
- Scorer liefern teilweise unterschiedliche oder implizite Felder.
- Decision-relevante Informationen sind noch nicht als standardisiertes, gemeinsames Interface abgesichert.

After:
- Jeder relevante Scorer liefert ein standardisiertes Interface mindestens in der Form:
```python
{
    "entry_ready": bool,
    "entry_readiness_reasons": list[str],
    "invalidation_anchor_price": float | None,
    "invalidation_derivable": bool,
    "setup_subtype": str,
}
```
- Dieses Interface ist die gemeinsame Vertragsbasis für spätere Decision-/WAIT-Logik.
- Das Scorer-Output bleibt additive erweiterbar, damit spätere Felder ergänzt werden können, ohne den Contract zu brechen.

Edge cases:
- `entry_ready = false` und leere `entry_readiness_reasons` darf nicht vorkommen
- `invalidation_derivable = false` bei gleichzeitig numerisch gesetztem Anchor ist inkonsistent
- `invalidation_anchor_price = None` bei `invalidation_derivable = true` ist inkonsistent
- scorer-spezifische Gründe müssen auf standardisierte Reason-Keys gemappt werden
- nicht-finite numerische Anchor-Werte (`NaN`, `inf`) dürfen nicht in den standardisierten Output gelangen

Backward compatibility impact:
- Scorer-Outputs werden auf ein gemeinsames Interface normalisiert.
- Bestehende nachgelagerte Nutzung kann Anpassungen benötigen, darf aber keine zweite Wahrheit behalten.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Das standardisierte Interface ist die gemeinsame Wahrheit; keine scorer-spezifischen Sonderpfade in die spätere Decision Layer verschieben.
- **Reason-Keys standardisieren:** `entry_readiness_reasons` muss aus stabilen, standardisierten Keys bestehen, nicht aus freien Texten.
- **`entry_ready = false` braucht Gründe:** Keine leere Reason-Liste in diesem Fall.
- **`entry_ready = true` darf keine negativen Readiness-Reasons mitschleppen**, außer explizit als separate neutrale Kontextgründe definiert; in diesem PR vermeiden.
- **Invalidation-Konsistenz ist Pflicht:** `invalidation_derivable`, `invalidation_anchor_price` und ihre Semantik dürfen sich nicht widersprechen.
- **Nicht-finite numerische Werte sind invalid/not evaluable:** `NaN`, `inf`, `-inf` dürfen nicht als Anchor-Preis durchgereicht werden.
- **Keine bool()-Koerzierung semantisch fehlender Werte:** `None`/fehlende Anker nicht implizit zu „0“ oder `false`-Semantik verwischen.
- **Keine stillen Alias-Felder:** Nur das standardisierte Interface ist die gemeinsame Hauptwahrheit.
- **Additiv erweiterbar, aber nicht brechend:** Zusätzliche optionale Felder sind erlaubt, der Standard-Contract darf nicht uneindeutig werden.

## Zusätzliche Pflichtsektion für numerische / Config-lastige Tickets
- [ ] Partielle Nested-Overrides: merge oder replace explizit festlegen
- [ ] Nicht-finite Werte (`NaN`, `inf`, `-inf`) explizit behandeln
- [ ] Nullable Ergebnisse explizit als nullable markieren
- [ ] Nicht auswertbar ≠ negativ bewertet
- [ ] Fehlender Key ≠ ungültiger Key
- [ ] Konkrete Tests für genau diese Fälle ausschreiben

Hinweis zu diesem Ticket:
- Der Fokus liegt auf Interface-Standardisierung, nicht auf neuer Config.
- Numerische Sonderfälle sind trotzdem relevant für `invalidation_anchor_price`.

## Implementation Notes (optional but useful)
- Falls PR-12 scorer-spezifische Vorstufenfelder eingeführt hat, ist PR-13 die Stelle für die Normalisierung in ein gemeinsames Interface.
- Standardisierte Reasons sollen aus einer klaren, begrenzten Wertemenge stammen, z. B.:
  - `breakout_not_confirmed`
  - `retest_not_reclaimed`
  - `rebound_not_confirmed`
  - ggf. weitere nur, wenn bereits referenziell abgesichert
- Wenn ein Scorer keinen Invalidation-Anchor fachlich ableiten kann:
  - `invalidation_derivable = false`
  - `invalidation_anchor_price = None`
- Ein Scorer darf keinen nicht-finiten Anchor-Preis ausgeben.

## Acceptance Criteria (deterministic)
1) Alle relevanten Scorer liefern das standardisierte Interface mit mindestens:
   - `entry_ready`
   - `entry_readiness_reasons`
   - `invalidation_anchor_price`
   - `invalidation_derivable`
   - `setup_subtype`

2) `entry_readiness_reasons` ist eine Liste standardisierter, stabiler Reason-Keys und keine freie Textsammlung.

3) Wenn `entry_ready = false`, ist `entry_readiness_reasons` nicht leer.

4) Wenn `entry_ready = true`, enthält `entry_readiness_reasons` keine negativen Readiness-Gründe.

5) Wenn `invalidation_derivable = false`, ist `invalidation_anchor_price = None`.

6) Wenn `invalidation_derivable = true`, ist `invalidation_anchor_price` gesetzt und numerisch endlich.

7) Nicht-finite Werte (`NaN`, `inf`, `-inf`) dürfen nicht als `invalidation_anchor_price` im standardisierten Output erscheinen.

8) Das standardisierte Interface ist zwischen den betroffenen Scorern konsistent genug, dass die spätere Decision Layer keine scorer-spezifische Sonderlogik für Readiness/Invalidation braucht.

9) Dieses PR führt keine Decision-Statuswerte (`ENTER`, `WAIT`, `NO_TRADE`) ein.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ N/A, sofern keine neue Config genutzt wird
- **Config Invalid Value Handling:** ✅ N/A, sofern keine neue Config genutzt wird
- **Nullability / kein bool()-Coercion:** ✅ `invalidation_anchor_price` bleibt nullable; `None` wird nicht still in numerische Scheinwerte verwandelt
- **Not-evaluated vs failed getrennt:** ✅ fehlende Invalidation-Ableitung ≠ fachlich negatives Trade-Urteil
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A
- **Deterministische Sortierung / Tie-breaker:** ✅ Reason-Reihenfolge und Interface-Ausgabe müssen bei identischem Input stabil sein, falls Reihenfolge relevant ist

## Tests (required if logic changes)
- Unit:
  - jeder betroffene Scorer liefert die Standardfelder
  - `entry_ready = false` => `entry_readiness_reasons` nicht leer
  - `entry_ready = true` => keine negativen Readiness-Reasons
  - `invalidation_derivable = false` => Anchor ist `None`
  - `invalidation_derivable = true` => Anchor ist gesetzt und endlich
  - `NaN`/`inf` werden nicht als Anchor durchgereicht
  - bekannte scorer-spezifische Gründe werden korrekt auf standardisierte Reason-Keys gemappt

- Integration:
  - mehrere Scorer liefern konsistentes Standard-Interface
  - identischer Input führt zu identischem Interface-Output
  - spätere Consumers könnten auf die Standardfelder zugreifen, ohne scorer-spezifische Sonderbehandlung

- Golden fixture / verification:
  - Nur anpassen, wenn bestehende Tests alte scorer-spezifische Outputformen vollständig fixiert haben
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] `entry_readiness_reasons` bleibt standardisierte Key-Liste, kein Freitext
- [ ] `entry_ready = false` ohne Reason-Liste ist verboten
- [ ] `invalidation_anchor_price` bleibt nullable
- [ ] nicht-finite Anchor-Werte sind verboten
- [ ] Keine Decision-/Tradeability-/Risk-Statuslogik in diesem PR
- [ ] Standardisiertes Interface bleibt additiv erweiterbar und nicht brechend

## Definition of Done (Codex must satisfy)
- [ ] Standard-Interface in allen relevanten Scorern implementiert
- [ ] Acceptance Criteria erfüllt
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
