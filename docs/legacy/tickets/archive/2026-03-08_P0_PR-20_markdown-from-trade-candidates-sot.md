> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-20 Markdown aus `trade_candidates`-SoT rendern

## Context / Source
- Die aktuelle alleinige Referenz ist die gültige Epic-/PR-Struktur für die Neuausrichtung.
- EPIC 9 / PR-20 verlangt, dass Markdown-Reports nicht länger eine eigene Wahrheit besitzen, sondern ausschließlich aus dem kanonischen JSON-SoT `trade_candidates` erzeugt werden.
- Die neuen verbindlichen Ticket-Regeln gelten vollständig, insbesondere:
  - keine zweite Wahrheit im Renderer,
  - Missing vs Invalid explizit,
  - nullable Felder nicht implizit koerzieren,
  - deterministische Reihenfolge,
  - konkrete Tests statt bloßer Kategorien.

## Goal
Der Markdown-Renderer erzeugt den Report ausschließlich aus `trade_candidates` plus Run-Manifest/Kontext und bildet dieselben Kandidaten, Decisions, Reasons und Pflichtfelder deterministisch ab.

## Scope
- `scanner/pipeline/output.py`
- ggf. enge Anpassungen an Hilfsfunktionen, die direkt vom Markdown-Renderer verwendet werden
- ggf. kleine Snapshot-/Fixture-Anpassungen für Markdown-spezifische Tests

## Out of Scope
- Keine Änderung am kanonischen JSON-SoT selbst
- Keine Excel-Änderungen
- Keine neue Decision- oder Risk-Logik
- Keine Änderung der Pipeline-Steuerung / Feature-Flags
- Keine Format-übergreifenden Konsistenztests (kommen in separatem PR)
- Keine Änderung an `trade_candidates`-Feldnamen, Enum-Werten oder Canonical-Contracts

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`

## Proposed change (high-level)
Before:
- Der Markdown-Output besitzt historisch eigene Ableitungslogik und ist potenziell anfällig für Format-Drift gegenüber JSON/Excel.
- Einzelne Felder oder Sections können aus nicht-kanonischen Zwischenzuständen gerendert werden.

After:
- Der Markdown-Renderer nutzt `trade_candidates` als alleinige Kandidatenquelle.
- Der Report enthält mindestens:
  - `ENTER Candidates`
  - `WAIT Candidates`
  - `Summary`
- `ENTER Candidates` zeigen relevante Risk-/Tradeability-/TP-Felder.
- `WAIT Candidates` zeigen Reasons explizit und vollständig.
- Die Summary zeigt operative Mindestinfos:
  - Anzahl ENTER / WAIT / NO_TRADE
  - BTC-Regime-Kontext, sofern vorhanden
  - Kurzfassung des Run-Manifests, soweit dafür kanonisch vorgesehen
- Die Reihenfolge der Kandidaten ist deterministisch und folgt dem kanonischen Priorisierungspfad.

Edge cases:
- leere `ENTER`-Menge
- leere `WAIT`-Menge
- nur `NO_TRADE`-Kandidaten
- nullable Felder wie `risk_acceptable`, `rr_to_tp10`, `slippage_bps_20k`, `decision_reasons`
- Kandidaten mit `decision = WAIT`, aber mehreren Reasons
- Kandidaten mit fehlenden optionalen Kontextfeldern dürfen nicht zu Render-Fehlern führen

Backward compatibility impact:
- Markdown-Inhalt kann sich bewusst ändern, wenn historischer Renderer von der JSON-SoT abgewichen ist.
- Ziel ist fachliche Angleichung, nicht pixelgenaue Beibehaltung alter Reports.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Der Renderer ist rein konsumierend; keine neue semantische Wahrheit im Markdown erzeugen.
- **JSON-SoT ist alleinige Kandidatenquelle:** Keine sekundäre Ableitung derselben Kandidaten aus alten Ranking-/Snapshot-Strukturen.
- **Keine bool()-Koerzierung nullable Felder:** `null`/`None` darf nicht stillschweigend zu `false`, `0`, leerem String oder „No“ umgedeutet werden, wenn das fachlich etwas anderes bedeutet.
- **Missing vs invalid trennen:** Fehlende optionale Felder dürfen den Report nicht hart brechen; wirklich invalides SoT-Schema ist dagegen ein klarer Fehler.
- **Decision/Reason unverändert rendern:** Keine Umbenennung, Reduktion oder heuristische Verkürzung von `decision` oder `decision_reasons`.
- **Determinismus:** Bei identischem SoT und identischem Manifest ist der Markdown-Output byte-stabil oder zumindest in Inhalt und Reihenfolge stabil.
- **Keine neue Business-Logik:** Keine zusätzliche Filterung, kein Neuberechnen von Score/Risk/Tradeability im Renderer.
- **Summary nur aus vorhandenen Daten:** Keine impliziten Rückschlüsse, wenn Manifest-/Kontextfelder fehlen.
- **Keine Format-spezifische zweite Wahrheit:** Was Markdown zeigt, muss aus demselben SoT stammen wie spätere Excel-/Consistency-Tests.

## Zusätzliche Pflichtsektion für numerische / Config-lastige Tickets
- [ ] Partielle Nested-Overrides: **N/A** — dieses Ticket definiert keine neue Config-Semantik
- [ ] Nicht-finite Werte (`NaN`, `inf`, `-inf`) explizit behandeln, falls sie im SoT auftauchen; nicht als legitime Anzeigezahlen durchreichen
- [ ] Nullable Ergebnisse explizit als nullable behandeln
- [ ] Nicht auswertbar ≠ negativ bewertet
- [ ] Fehlender Key ≠ ungültiger Key
- [ ] Konkrete Tests für genau diese Fälle ausschreiben

## Implementation Notes (optional but useful)
- Prüfe den bestehenden Markdown-Renderer in `scanner/pipeline/output.py` auf:
  - alte Ranking-/Top20-Abhängigkeiten
  - eigene Feldableitungen
  - implizite Defaults / `.get(..., 0)` / `or ""` auf semantisch kritischen Feldern
- Wenn `trade_candidates` bereits sortiert anliegt, nur diese Reihenfolge verwenden.
- Wenn Sortierung im Renderer nötig ist, muss sie explizit und deterministisch sein.
- Für numerische Felder:
  - `None` / nicht auswertbar nicht als 0 formatieren
  - `NaN`/`inf` nicht unkommentiert rendern; als fehlend/nicht auswertbar behandeln oder klaren Fehler auslösen, je nach bereits garantiertem SoT-Contract

## Acceptance Criteria (deterministic)
1) `scanner/pipeline/output.py` rendert Kandidatenlisten ausschließlich aus `trade_candidates` und nicht aus parallelen alten Kandidatenquellen.

2) Der Markdown-Report enthält mindestens die Abschnitte:
   - `ENTER Candidates`
   - `WAIT Candidates`
   - `Summary`

3) Jeder in `trade_candidates` enthaltene `ENTER`-Kandidat erscheint im Markdown-Abschnitt `ENTER Candidates`.

4) Jeder in `trade_candidates` enthaltene `WAIT`-Kandidat erscheint im Markdown-Abschnitt `WAIT Candidates`.

5) `decision` und `decision_reasons` werden im Markdown inhaltlich unverändert aus dem SoT übernommen; keine heuristische Verkürzung oder Umbenennung.

6) Nullable Felder bleiben semantisch korrekt:
   - nicht auswertbar bleibt nicht auswertbar
   - `null` wird nicht still zu `false` oder `0`

7) Fehlende optionale Felder führen nicht zu Render-Abstürzen; invalides SoT-Schema führt zu einem klaren Fehler statt stiller Korrektur.

8) Die Kandidatenreihenfolge im Markdown ist deterministisch und bei identischem Input reproduzierbar.

9) Der Renderer führt keine neue Risk-/Decision-/Tradeability-Business-Logik ein.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ N/A — kein neuer Config-Block, aber fehlende optionale Manifest-/Kontextfelder dürfen nicht hart brechen
- **Config Invalid Value Handling:** ✅ N/A — kein neuer Config-Block; invalides SoT-Schema muss jedoch klar fehlschlagen
- **Nullability / kein bool()-Coercion:** ✅ explizit relevant für `risk_acceptable`, `rr_to_tp10`, `slippage_bps_20k`, optionale Reasons
- **Not-evaluated vs failed getrennt:** ✅ Renderer darf diese Zustände nicht kollabieren
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ wenn Output-Datei geschrieben wird, kein Teilreport bei fatalem Schemafehler
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ bestehende Output-Pfade unverändert oder klar dokumentiert
- **Deterministische Sortierung / Tie-breaker:** ✅ deterministische Report-Reihenfolge

## Tests (required if logic changes)
- Unit:
  - `ENTER`-Kandidat wird aus `trade_candidates` korrekt in `ENTER Candidates` gerendert
  - `WAIT`-Kandidat wird mit vollständigen `decision_reasons` korrekt in `WAIT Candidates` gerendert
  - fehlende optionale Felder brechen das Rendering nicht
  - nullable Felder bleiben semantisch korrekt und werden nicht zu `0`/`false` koerziert
  - invalides Pflichtschema führt zu klarem Fehler

- Integration:
  - ein Beispiel-SoT mit ENTER/WAIT/NO_TRADE erzeugt einen vollständigen Markdown-Report mit Summary
  - identischer Input erzeugt identischen Markdown-Output
  - keine parallele alte Kandidatenquelle beeinflusst den Markdown-Inhalt

- Golden fixture / verification:
  - bestehende Markdown-Golden-Files nur dort aktualisieren, wo der Wechsel auf SoT-basierte Wahrheit bewusst Inhalt ändert
  - keine nicht betroffenen Snapshots anfassen

## Constraints / Invariants (must not change)
- [ ] `trade_candidates` bleibt die alleinige Kandidatenquelle für den Markdown-Renderer
- [ ] keine zweite Wahrheit im Markdown
- [ ] keine Risk-/Decision-/Tradeability-Business-Logik im Renderer
- [ ] nullable Felder bleiben semantisch korrekt
- [ ] deterministische Reihenfolge
- [ ] bestehende kanonische Feldnamen bleiben unverändert

## Definition of Done (Codex must satisfy)
- [ ] Markdown-Renderer ausschließlich auf SoT umgestellt
- [ ] Acceptance Criteria erfüllt
- [ ] Unit-/Integration-/ggf. Golden-Tests ergänzt oder angepasst
- [ ] keine Scope-Überschreitung in Excel-/Consistency-/Pipeline-Logik
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
