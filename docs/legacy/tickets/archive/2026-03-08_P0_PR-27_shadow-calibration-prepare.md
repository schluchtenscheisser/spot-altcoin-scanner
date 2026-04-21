> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-27 Shadow Calibration vorbereiten (ohne aktive Kalibrierung)

## Context / Source
- Die aktuelle alleinige Referenz sieht Shadow Calibration erst **nach** stabiler Datensammlung vor.
- Vor aktiver Kalibrierung braucht es vorbereitende Infrastruktur, aber noch keine Änderung produktiver Schwellen oder Decision-Logik.
- Dieses Ticket ist bewusst ein Vorbereitungs-PR und darf keine semantische Vorwegnahme der eigentlichen Kalibrierung enthalten.

## Goal
Die technische Grundlage für spätere Shadow Calibration schaffen, ohne bereits aktive Kalibrierung oder automatische Threshold-Anpassung einzubauen.

## Scope
- vorbereitende Infrastruktur für spätere Kalibrierung
- saubere Ablage / Einlesbarkeit der benötigten Eval-Daten
- ggf. vorbereitende Analyse-/Export-Strukturen
- klare Trennung zwischen:
  - Datensammlung
  - späterer Kalibrierung
  - produktiver Decision-Logik

## Out of Scope
- Keine Änderung produktiver Decision-Schwellen
- Keine `p_hit10_5d` / `p_hit20_5d`-Produktion im Live-Scanner
- Keine automatische Threshold-Anpassung
- Keine aktive Modellkalibrierung
- Keine Portfolio-/Exit-/Hold-Logik
- Keine neue Live-Fachlogik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- relevante Canonical Docs zu Pipeline / Output / Eval
- aktuelle alleinige Referenz für spätere Kalibrierung

## Proposed change (high-level)
Before:
- Eval-/Label-Export existiert, aber die Infrastruktur für spätere Shadow Calibration ist nicht sauber vorbereitet oder nicht klar von Live-Logik getrennt.

After:
- Es gibt vorbereitende technische Strukturen, um später Kalibrierungsdaten konsistent auszuwerten.
- Produktive Thresholds und Decision-Logik bleiben unverändert.
- Es ist klar und testbar sichergestellt, dass Shadow Calibration nur vorbereitet, aber noch nicht aktiv angewendet wird.

Edge cases:
- unzureichende historische Daten
- fehlende Label-Felder
- teilweise unvollständige Datensätze
- numerische Ausreißer in Eval-Daten
- versehentliches Aktivieren kalibrierter Pfade trotz unzureichender Daten

Backward compatibility impact:
- Keine Änderung produktiver Entscheidungslogik.
- Infrastruktur wird ergänzt, ohne die aktive Scanner-Semantik zu ändern.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Shadow Calibration bleibt Phase-2-Thema und darf produktive Phase-1-Logik nicht verändern.
- **Keine aktive Kalibrierung:** Dieses Ticket bereitet nur vor; keine Schwellen anpassen, keine Live-Outputs umdeuten.
- **Missing vs invalid trennen:** fehlende oder unzureichende Datensätze klar von formal ungültigen Datensätzen trennen.
- **`NaN` / `inf` explizit:** numerische Problemwerte in Eval-Daten nicht still übernehmen.
- **Nullability explizit:** falls vorbereitende Metriken nullable sind, darf `null` nicht still zu `0`/`false` kollabieren.
- **Determinismus:** gleicher Input + gleiche Datenbasis => gleiche vorbereitende Auswertung.
- **Keine zweite Fachwahrheit:** Vorbereitete Kalibrierungsdaten sind Meta-/Analyse-Ebene, nicht produktive Scan-Wahrheit.
- **Keine stillen Feature-Flags:** Wenn Vorbereitung aktivierbar ist, dann zentral, explizit und ohne Einfluss auf produktive Entscheidungen.

## Implementation Notes (optional but useful)
- Wahrscheinlich betroffen:
  - Eval-/Dataset-Export
  - Analyse-/Tools-Bereich
  - evtl. vorbereitende Ablagestrukturen
- Falls Reports oder Analyse-Summaries entstehen, müssen sie als Vorbereitung / Shadow klar getrennt von produktiven Outputs bleiben.

## Acceptance Criteria (deterministic)
1) Es existiert vorbereitende Infrastruktur für spätere Shadow Calibration, ohne produktive Decision-Schwellen zu verändern.

2) Produktive Outputs und produktive Decision-Logik bleiben unverändert.

3) Fehlende oder unzureichende Kalibrierungsdaten werden explizit und testbar behandelt.

4) Nicht-finite numerische Werte in vorbereitenden Kalibrierungsdaten werden explizit behandelt und nicht still übernommen.

5) Gleicher Input + gleiche Datenbasis => deterministisch identische vorbereitende Auswertung.

6) Tests belegen, dass durch dieses Ticket keine aktive Kalibrierung oder automatische Threshold-Anpassung eingeschaltet wird.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (falls vorbereitende Features konfigurierbar sind)
- **Config Invalid Value Handling:** ✅ (ungültige Vorbereitungs-Konfiguration => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (nullable vorbereitende Felder bleiben semantisch korrekt)
- **Not-evaluated vs failed getrennt:** ✅ (unzureichende Datengrundlage ≠ negative Kalibrierung)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (kein halb-aktivierter Shadow-Calibration-Zustand)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (vorbereitende Artefakte konfliktfrei)
- **Deterministische Sortierung / Tie-breaker:** ✅ (wenn vorbereitende Artefakt-Reihenfolge relevant ist)

## Tests (required if logic changes)
- Unit:
  - vorbereitende Auswertung bei gültigen Daten
  - unzureichende Daten werden explizit behandelt
  - `NaN`/`inf` in Kalibrierungsdaten werden explizit behandelt
  - keine aktive Schwellenänderung

- Integration:
  - vorbereitender Shadow-Calibration-Pfad beeinflusst produktiven Scanner-Output nicht
  - gleicher Input + gleiche Datenbasis => deterministische vorbereitende Ergebnisse

- Golden fixture / verification:
  - nur dort Golden-/Fixture-Updates, wo vorbereitende Kalibrierungsartefakte bewusst neu eingeführt werden
  - keine kosmetischen Änderungen an produktiven Artefakten

## Constraints / Invariants (must not change)
- [ ] keine aktive Kalibrierung
- [ ] keine Änderung produktiver Decision-Schwellen
- [ ] keine neue Live-Fachlogik
- [ ] Shadow Calibration bleibt Vorbereitung
- [ ] Determinismus bleibt erhalten
- [ ] keine Scope-Ausweitung in Portfolio / Exit / Hold

## Definition of Done (Codex must satisfy)
- [ ] vorbereitende Shadow-Calibration-Infrastruktur implementiert
- [ ] Tests sichern ab, dass produktive Logik unverändert bleibt
- [ ] Missing-/Numerik-/Nullability-Randfälle abgedeckt
- [ ] keine aktive Kalibrierung eingeführt
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
