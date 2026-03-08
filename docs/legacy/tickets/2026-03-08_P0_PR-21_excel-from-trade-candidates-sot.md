> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-21 Excel aus `trade_candidates`-SoT rendern

## Context / Source
- Die aktuelle alleinige Referenz ist die gültige Epic-/PR-Struktur für die Neuausrichtung.
- EPIC 9 / PR-21 verlangt, dass Excel/XLSX nicht länger eine eigene fachliche Wahrheit besitzt, sondern ausschließlich aus dem kanonischen JSON-SoT `trade_candidates` erzeugt wird.
- Nach PR-20 muss jetzt auch Excel dieselben Kandidaten, Decisions, Reasons und Pflichtfelder aus derselben Quelle spiegeln.

## Goal
Der Excel-Renderer erzeugt seine Sheets ausschließlich aus `trade_candidates` plus dem dafür vorgesehenen Manifest-/Kontextinput und bildet dieselben Kandidaten, Decisions, Reasons und Pflichtfelder deterministisch ab.

## Scope
- `scanner/pipeline/excel_output.py`
- ggf. enge Anpassungen an direkte Excel-Hilfsfunktionen
- ggf. kleine testnahe Fixture-/Snapshot-Anpassungen für XLSX-Rendering

## Out of Scope
- Keine Änderung am JSON-SoT
- Keine Markdown-Änderungen
- Keine formatübergreifenden Konsistenztests (separater PR)
- Keine neue Decision-/Risk-/Tradeability-Logik
- Keine Änderung an Pipeline-/Feature-Flag-Logik
- Keine Änderung an kanonischen Feldnamen oder Enum-Werten

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`

## Proposed change (high-level)
Before:
- Excel/XLSX kann historisch eigene Selektions- oder Ableitungslogik enthalten und dadurch von JSON/Markdown abweichen.
- Felddarstellung und Reihenfolgen sind potenziell nicht vollständig an die SoT gebunden.

After:
- Excel rendert ausschließlich aus `trade_candidates`.
- Es existieren mindestens die Sheets:
  - `Trade Candidates`
  - `Enter Candidates`
  - `Wait Candidates`
- `Trade Candidates` enthält alle Kandidaten aus dem SoT.
- `Enter Candidates` ist ein reiner Filter auf `decision == ENTER`.
- `Wait Candidates` ist ein reiner Filter auf `decision == WAIT`.
- Reihenfolge, Feldwerte und Reasons stammen aus demselben SoT wie Markdown/JSON.

Edge cases:
- keine ENTER-Kandidaten
- keine WAIT-Kandidaten
- nur NO_TRADE-Kandidaten
- multiple `decision_reasons`
- nullable numerische Felder
- optionale Kontextfelder fehlen
- Kandidaten mit nicht auswertbaren Feldern dürfen nicht stillschweigend in irreführende Zahlen umgewandelt werden

Backward compatibility impact:
- Excel-Inhalte/Spalten können sich bewusst ändern, wenn historischer Renderer eine abweichende Wahrheit hatte.
- Ziel ist fachliche Angleichung an SoT, nicht visuelle Rückwärtskompatibilität um jeden Preis.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Excel ist ein Renderformat, keine zweite Business-Logik.
- **JSON-SoT ist alleinige Kandidatenquelle:** Keine parallele Kandidatenermittlung aus alten Rankings/Snapshots.
- **Sheets sind reine Views:** `Enter Candidates` und `Wait Candidates` sind Filter auf `Trade Candidates` / SoT, keine eigene Ableitungslogik.
- **Keine bool()-Koerzierung nullable Felder:** `null`/`None` darf nicht als `0`, `False`, `No` oder leerer numerischer Wert maskiert werden, wenn das fachlich etwas anderes bedeutet.
- **Missing vs invalid trennen:** Fehlende optionale Felder dürfen Rendering nicht hart brechen; invalides Pflichtschema muss klar fehlschlagen.
- **Multiple reasons erhalten:** `decision_reasons` nicht heuristisch kürzen oder zusammenfassen, wenn das Information verliert.
- **Determinismus:** Bei identischem SoT und identischem Kontext entstehen dieselben Sheet-Inhalte in derselben Zeilenreihenfolge.
- **Keine neue Business-Logik:** Kein Neuberechnen von Score, Risk, Tradeability oder Decisions im Excel-Renderer.

## Zusätzliche Pflichtsektion für numerische / Config-lastige Tickets
- [ ] Partielle Nested-Overrides: **N/A** — dieses Ticket definiert keine neue Config-Semantik
- [ ] Nicht-finite Werte (`NaN`, `inf`, `-inf`) explizit behandeln, falls sie im SoT auftauchen
- [ ] Nullable Ergebnisse explizit als nullable behandeln
- [ ] Nicht auswertbar ≠ negativ bewertet
- [ ] Fehlender Key ≠ ungültiger Key
- [ ] Konkrete Tests für genau diese Fälle ausschreiben

## Implementation Notes (optional but useful)
- Prüfe `scanner/pipeline/excel_output.py` auf:
  - alte Ranking-/Top-N-Abhängigkeiten
  - eigene Candidate-Selektion
  - implizite Defaults / Formatierungstricks, die `None` zu 0 oder leerem „ok“ machen
- Wenn es gemeinsame Feldlisten/Spaltenmappings gibt, nur kanonische Feldnamen verwenden.
- Falls `decision_reasons` serialisiert werden, muss die Darstellung stabil und reversibel nachvollziehbar bleiben (z. B. definierter Delimiter, keine zufällige Reihenfolge).

## Acceptance Criteria (deterministic)
1) `scanner/pipeline/excel_output.py` erzeugt seine Kandidaten-Sheets ausschließlich aus `trade_candidates`.

2) Die folgenden Sheets existieren mindestens:
   - `Trade Candidates`
   - `Enter Candidates`
   - `Wait Candidates`

3) `Trade Candidates` enthält alle Kandidaten aus dem SoT.

4) `Enter Candidates` enthält genau die Kandidaten mit `decision = ENTER`.

5) `Wait Candidates` enthält genau die Kandidaten mit `decision = WAIT`.

6) `decision` und `decision_reasons` werden inhaltlich unverändert aus dem SoT übernommen; keine heuristische Verkürzung oder Umdeutung.

7) Nullable Felder bleiben semantisch korrekt und werden nicht still zu `0`/`false`/leeren numerischen Werten koerziert.

8) Fehlende optionale Felder führen nicht zu Render-Abstürzen; invalides Pflichtschema führt zu einem klaren Fehler.

9) Die Zeilenreihenfolge ist bei identischem Input deterministisch reproduzierbar.

10) Der Excel-Renderer führt keine neue Risk-/Decision-/Tradeability-Business-Logik ein.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ N/A — kein neuer Config-Block; fehlende optionale Kontextfelder dürfen nicht hart brechen
- **Config Invalid Value Handling:** ✅ N/A — kein neuer Config-Block; invalides Pflichtschema muss klar fehlschlagen
- **Nullability / kein bool()-Coercion:** ✅ explizit relevant für nullable numerische und bool-artige Felder
- **Not-evaluated vs failed getrennt:** ✅ Excel darf diese Zustände nicht kollabieren
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ kein halbgeschriebenes Workbook bei fatalem Schemafehler
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ bestehende Output-Pfade unverändert oder klar dokumentiert
- **Deterministische Sortierung / Tie-breaker:** ✅ deterministische Zeilenreihenfolge

## Tests (required if logic changes)
- Unit:
  - `Trade Candidates` enthält alle SoT-Kandidaten
  - `Enter Candidates` filtert exakt auf `decision = ENTER`
  - `Wait Candidates` filtert exakt auf `decision = WAIT`
  - `decision_reasons` bleiben vollständig erhalten
  - fehlende optionale Felder brechen Rendering nicht
  - invalides Pflichtschema führt zu klarem Fehler
  - nullable Felder werden nicht irreführend koerziert

- Integration:
  - ein Beispiel-SoT erzeugt ein Workbook mit allen drei Sheets
  - identischer Input erzeugt dieselben Zeileninhalte in derselben Reihenfolge
  - keine alte parallele Candidate-Quelle beeinflusst den Excel-Inhalt

- Golden fixture / verification:
  - bestehende XLSX-/Sheet-Snapshots nur dort aktualisieren, wo die Umstellung auf SoT bewusst inhaltliche Drift beseitigt
  - keine nicht betroffenen Snapshots anfassen

## Constraints / Invariants (must not change)
- [ ] `trade_candidates` bleibt die alleinige Kandidatenquelle für Excel
- [ ] `Trade Candidates` / `Enter Candidates` / `Wait Candidates` bleiben reine Views auf dasselbe SoT
- [ ] keine neue Business-Logik im Renderer
- [ ] nullable Felder bleiben semantisch korrekt
- [ ] deterministische Zeilenreihenfolge
- [ ] keine Änderung kanonischer Feldnamen

## Definition of Done (Codex must satisfy)
- [ ] Excel-Renderer ausschließlich auf SoT umgestellt
- [ ] Acceptance Criteria erfüllt
- [ ] Unit-/Integration-/ggf. Snapshot-Tests ergänzt oder angepasst
- [ ] keine Scope-Überschreitung in JSON-/Markdown-/Consistency-/Pipeline-Logik
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
