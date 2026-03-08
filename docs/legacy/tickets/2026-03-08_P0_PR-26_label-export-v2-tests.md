> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-26 Label-Export V2 Tests schärfen und Golden-/Fixture-Abdeckung ergänzen

## Context / Source
- Die aktuelle alleinige Referenz verlangt einen erweiterten Eval-/Label-Export für spätere Kalibrierung.
- PR-25 führt oder erweitert den Label-Export mit:
  - `hit5_5d`
  - `hit10_5d`
  - `hit20_5d`
  - `mae_5d_pct`
  - `mfe_5d_pct`
- Dieses Ticket stellt sicher, dass diese Label-Semantik regressionssicher, deterministisch und numerisch robust abgesichert ist.
- Die neuen verbindlichen Ticket-Regeln gelten vollständig, insbesondere:
  - Missing vs Invalid
  - `NaN` / `inf`
  - `null`-Semantik
  - kein stilles Umdeuten unvollständiger Fenster in negative Labels
  - konkrete Tests statt allgemeiner Kategorien

## Goal
Ein vollständiges Testnetz für den Label-Export aufbauen oder schärfen, das sicherstellt:

- die Hit-Labels sind korrekt und deterministisch
- `mae_5d_pct` / `mfe_5d_pct` sind korrekt und robust
- unvollständige Datenfenster werden explizit behandelt
- numerische Sonderwerte diffundieren nicht still in scheinbar gültige Labels
- Golden-/Fixture-Abdeckung reflektiert die kanonische Label-Semantik

## Scope
- Tests für Eval-/Label-Export
- vorhandene Testdateien anpassen oder neue Tests anlegen
- falls nötig:
  - kleine Golden-/Fixture-Updates
  - testnahe Helper
- keine fachliche Produktionslogik außer minimal nötigen Test-Hooks

## Out of Scope
- Keine neue Kalibrierungslogik
- Keine Änderung der Label-Semantik selbst
- Keine Änderung der Decision- oder Live-Pipeline
- Keine Portfolio-/Exit-/Hold-Logik
- Keine neue Output-SoT für Scanner-Artefakte
- Keine Änderung an Canonical Docs

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- relevante Canonical Docs zu Output / Eval / Pipeline
- aktuelle alleinige Referenz für Eval-Labels

## Proposed change (high-level)
Before:
- Der Label-Export kann formal existieren, ohne dass seine Randfälle und numerischen Spezialfälle vollständig regressionssicher getestet sind.
- Gerade bei Hitschwellen, MAE/MFE, unvollständigen Forward-Fenstern und `NaN`-/`inf`-Inputs besteht hohes Risiko für semantische Drift.

After:
- Es existieren explizite Tests für:
  - `hit5_5d`
  - `hit10_5d`
  - `hit20_5d`
  - `mae_5d_pct`
  - `mfe_5d_pct`
- unvollständige oder ungültige Daten werden explizit und testbar behandelt
- deterministische Golden-/Fixture-Ergebnisse sichern die Semantik zusätzlich ab

Edge cases:
- Schwelle exakt erreicht
- Schwelle knapp verfehlt
- High/Low-Spikes im Forward-Fenster
- unvollständiges 5d-Fenster
- fehlender oder ungültiger Entry
- `NaN`, `inf`, `-inf` in Preis-/Forward-Daten
- Forward-Fenster mit Lücken

Backward compatibility impact:
- Keine neue Fachlogik; Ticket erhöht Testschärfe.
- Bestehende Fixtures / Golden Files dürfen angepasst werden, wenn sie die neue kanonische Label-Semantik noch nicht korrekt abbilden.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Tests müssen die kanonischen Labelnamen und deren definierte Semantik prüfen.
- **Keine Kalibrierung vorziehen:** Nur Label-Semantik testen, keine Wahrscheinlichkeiten oder Threshold-Tuning.
- **Closed-candle-only / no-lookahead:** Tests müssen sicherstellen, dass nur das definierte Forward-Fenster verwendet wird.
- **`NaN` / `inf` explizit:** Nicht-finite Inputs dürfen nicht zu scheinbar gültigen Labelwerten führen.
- **Missing vs invalid trennen:** fehlende Forward-Daten / unvollständige Fenster ≠ negatives Label, sofern Canonical das nicht explizit sagt.
- **`null` bleibt `null`:** Wenn unvollständige oder ungültige Daten `null`/nicht auswertbar bedeuten, darf das nicht zu `false`/`0` kollabieren.
- **Determinismus ist Pflicht:** gleicher Input + gleiche Regeln => gleicher Export.
- **Keine stillen Golden-Änderungen:** Fixture-/Golden-Updates nur, wenn semantisch notwendig.

## Implementation Notes (optional but useful)
- Wahrscheinlich betroffene Pfade:
  - Tests zum Eval-/Dataset-Export
  - ggf. Golden-Fixtures für Exporte
- Für MAE/MFE sollten Tests mit kleinen, gut nachrechenbaren Preisfolgen arbeiten.
- Für Hit-Labels sollten Tests exakte Grenzfälle enthalten.

## Acceptance Criteria (deterministic)
1) Es gibt explizite Tests für `hit5_5d`, `hit10_5d` und `hit20_5d`.

2) Es gibt explizite Tests für `mae_5d_pct` und `mfe_5d_pct`.

3) Es gibt einen Test, der definiert und absichert, ob „Schwelle exakt erreicht“ als Hit gilt.

4) Es gibt Tests für unvollständige oder fehlende Forward-Daten, die sicherstellen, dass diese nicht still als negatives Label interpretiert werden.

5) Es gibt Tests für `NaN`, `inf` und `-inf` in relevanten numerischen Inputs.

6) Gleicher Input + gleiche Regeln => deterministisch identischer Label-Export.

7) Bestehende Golden-/Fixture-Dateien sind, wo nötig, an die kanonische Semantik angepasst und nicht nur kosmetisch verändert.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (falls Label-Parameter konfigurierbar sind)
- **Config Invalid Value Handling:** ✅ (ungültige Label-/Window-Konfiguration => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (nicht-auswertbare Labels kollabieren nicht still)
- **Not-evaluated vs failed getrennt:** ✅ (unzureichendes Fenster ≠ negatives Label)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (kein halb-valides Fixture-/Golden-Update)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (Golden-/Export-Dateien konfliktfrei)
- **Deterministische Sortierung / Tie-breaker:** ✅ (wenn Exportsortierung Teil des Fixtures ist, explizit halten)

## Tests (required if logic changes)
- Unit:
  - exakte Hit-Schwellenfälle
  - knappe Nicht-Hits
  - MAE korrekt
  - MFE korrekt
  - unvollständiges Fenster
  - ungültiger Entry
  - `NaN`/`inf`-Inputs

- Integration:
  - kleiner Fixture-Datensatz ergibt vollständigen, deterministischen Label-Export
  - keine Lookahead-Verletzung außerhalb des Fensters

- Golden fixture / verification:
  - semantisch notwendige Updates an bestehenden Golden Files
  - keine unnötigen kosmetischen Updates

## Constraints / Invariants (must not change)
- [ ] keine Kalibrierungslogik
- [ ] closed-candle-only / no-lookahead bleibt gewahrt
- [ ] Labelnamen bleiben kanonisch
- [ ] unzureichende Daten werden nicht still zu negativen Labels
- [ ] Determinismus bleibt erhalten
- [ ] keine Scope-Ausweitung in Decision / Live-Pipeline

## Definition of Done (Codex must satisfy)
- [ ] Tests gemäß Acceptance Criteria ergänzt oder angepasst
- [ ] Hit-/MAE-/MFE-/Missing-/Numerik-Randfälle abgesichert
- [ ] Golden-/Fixture-Änderungen semantisch begründet
- [ ] keine Kalibrierungslogik eingeführt
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
