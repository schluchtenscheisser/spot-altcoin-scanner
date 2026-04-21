> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-25 Label-Export V2 für Eval-/Kalibrierungsdaten erweitern

## Context / Source
- Die aktuelle alleinige Referenz verlangt einen erweiterten Label-Export für spätere Evaluation und Kalibrierung.
- Phase 1 nutzt Outcome-Proxies, aber noch keine kalibrierten Wahrscheinlichkeiten.
- Laut Referenz sollen mindestens folgende Labels exportiert werden:
  - `hit5_5d`
  - `hit10_5d`
  - `hit20_5d`
  - `mae_5d_pct`
  - `mfe_5d_pct`
- Ziel ist ein konsistenter Export, der spätere Shadow Calibration vorbereitet, ohne jetzt schon Kalibrierungslogik einzubauen.

## Goal
Den Evaluation-/Label-Export so erweitern, dass die kanonischen Outcome-Labels deterministisch, closed-candle-konform und ohne Lookahead-Fehler exportiert werden.

## Scope
- Export-Logik / Dataset-Export für Evaluation-Labels
- relevante Tests für:
  - Hit-Labels
  - MAE/MFE
  - Window-Definition
  - Umgang mit fehlenden Daten
- falls nötig: minimale Schema-Erweiterung des Eval-Exports

## Out of Scope
- Keine Shadow Calibration
- Keine kalibrierten Wahrscheinlichkeiten
- Keine Decision-Threshold-Änderung
- Keine Portfolio-/Exit-/Hold-Logik
- Keine Änderung an Live-Decision-Semantik
- Keine neue Output-SoT für Scan-Artefakte

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- aktuelle alleinige Referenz für Eval-/Label-Ziele

## Proposed change (high-level)
Before:
- Der bestehende Dataset-/Label-Export deckt die neuen Phase-1-Eval-Ziele nicht vollständig ab oder nicht in der kanonisch gewünschten Form.
- MAE/MFE und die erweiterten Hit-Labels sind nicht vollständig oder nicht konsistent exportiert.

After:
- Der Export enthält mindestens:
  - `hit5_5d`
  - `hit10_5d`
  - `hit20_5d`
  - `mae_5d_pct`
  - `mfe_5d_pct`
- Die Berechnung ist:
  - deterministisch
  - closed-candle-only
  - frei von Zukunfts-/Lookahead-Fehlern außerhalb des definierten Auswertungsfensters
- Fehlende oder unzureichende Forward-Daten werden explizit und sauber behandelt.

Edge cases:
- nicht genügend Folgekerzen für volles 5d-Fenster
- fehlende OHLCV-Daten im Fenster
- Entry-Preis fehlt oder ist ungültig
- `NaN`/`inf` in Eingangsserien
- hohe Intraday-Spikes für MFE
- tiefe Intraday-Lows für MAE
- Hit-Schwelle exakt erreicht vs knapp verfehlt

Backward compatibility impact:
- Eval-Export wird erweitert.
- Bestehende Datensätze/Tests müssen ggf. auf die neuen Label-Felder angepasst werden.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** nur die kanonisch geforderten Labelnamen und Semantiken verwenden.
- **Keine Kalibrierungslogik vorziehen:** dieses Ticket exportiert Labels, nicht Wahrscheinlichkeiten oder Thresholds.
- **Closed-candle-only / no-lookahead:** das 5d-Fenster muss eindeutig definiert und testbar sein.
- **Numerische Robustheit:** `NaN`, `inf`, `-inf` gelten als nicht auswertbar und dürfen nicht still in Labelwerte diffundieren.
- **Missing vs invalid trennen:** fehlender Entry oder unvollständiges Fenster ≠ negatives Label; das Verhalten muss explizit definiert und getestet werden.
- **Nullability explizit:** falls Labels bei unzureichenden Daten nullable sind, muss `null` semantisch erhalten bleiben und darf nicht implizit zu `false` oder `0` kollabieren.
- **Exakte Schwellenregeln:** „hit“ bei genauem Erreichen der Schwelle muss explizit definiert werden.
- **Determinismus:** gleicher Input + gleiche Window-Regel => identische Label-Ausgabe.

## Implementation Notes (optional but useful)
- Wahrscheinlich betroffen:
  - bestehender Dataset-/Eval-Export, evtl. `scanner/tools/export_evaluation_dataset.py`
- MAE/MFE sollten auf Basis derselben kanonischen Entry-Definition und desselben Forward-Fensters berechnet werden wie die Hit-Labels.
- Wenn bestehende Exporte CSV/JSON/Parquet unterstützen, muss dieses Ticket nicht alle Formate neu bauen; nur die Label-Semantik korrekt erweitern.

## Acceptance Criteria (deterministic)
1) Der Eval-/Label-Export enthält mindestens:
   - `hit5_5d`
   - `hit10_5d`
   - `hit20_5d`
   - `mae_5d_pct`
   - `mfe_5d_pct`

2) Die Label-Berechnung verwendet ein explizit definiertes 5d-Fenster und ist closed-candle-only.

3) Es ist explizit definiert und getestet, ob „Schwelle exakt erreicht“ als Hit zählt.

4) `mae_5d_pct` und `mfe_5d_pct` werden deterministisch aus dem definierten Forward-Fenster berechnet.

5) Fehlende oder unzureichende Forward-Daten werden explizit behandelt; kein stilles Umdeuten in negative Labels.

6) Nicht-finite Inputs (`NaN`, `inf`, `-inf`) werden explizit behandelt und diffundieren nicht still in scheinbar gültige Labels.

7) Gleicher Input + gleiche Regeln => identische Label-Ausgabe.

8) Tests decken Hit-, MAE-, MFE-, Missing- und numerische Edge Cases explizit ab.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (falls Window-/Label-Parameter konfigurierbar sind: zentrale Defaults; sonst N/A klar benennen)
- **Config Invalid Value Handling:** ✅ (ungültige Window-/Threshold-Werte => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (fehlende/insufficient Daten dürfen nicht implizit zu `false`/`0` kollabieren, wenn `null` semantisch korrekt ist)
- **Not-evaluated vs failed getrennt:** ✅ (unzureichende Forward-Daten ≠ negativer Hit)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (bei invalidem Eval-Input kein halb-konsistenter Export)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (falls Dataset-Dateien geschrieben werden: deterministische und konfliktfreie Benennung)
- **Deterministische Sortierung / Tie-breaker:** ✅ (sofern Datensatzsortierung relevant: explizit halten)

## Tests (required if logic changes)
- Unit:
  - `hit5_5d`, `hit10_5d`, `hit20_5d` bei klaren Schwellenfällen
  - Schwelle exakt erreicht zählt korrekt gemäß definierter Regel
  - `mae_5d_pct` korrekt
  - `mfe_5d_pct` korrekt
  - unvollständiges 5d-Fenster explizit behandelt
  - `NaN`-/`inf`-Inputs explizit behandelt
  - ungültiger Entry explizit behandelt

- Integration:
  - kleiner Eval-Export-Fixture erzeugt alle geforderten Felder
  - identischer Input => identischer Export
  - keine Lookahead-Verletzung außerhalb des definierten Fensters

- Golden fixture / verification:
  - bestehende Eval-/Dataset-Fixtures nur dort anpassen, wo neue Label-Felder oder deren Semantik betroffen sind
  - keine unnötigen kosmetischen Änderungen

## Constraints / Invariants (must not change)
- [ ] keine Kalibrierungslogik in diesem Ticket
- [ ] closed-candle-only / no-lookahead bleibt gewahrt
- [ ] Labelnamen bleiben kanonisch
- [ ] Missing/insufficient Daten werden nicht still zu negativen Labels
- [ ] Determinismus bleibt erhalten
- [ ] keine Scope-Ausweitung in Decision-/Output-SoT

## Definition of Done (Codex must satisfy)
- [ ] Label-Export gemäß Acceptance Criteria erweitert
- [ ] Tests für Hit-/MAE-/MFE-/Missing-/numerische Edge Cases vorhanden
- [ ] keine Kalibrierungslogik eingeführt
- [ ] closed-candle-only / no-lookahead explizit gewahrt
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
