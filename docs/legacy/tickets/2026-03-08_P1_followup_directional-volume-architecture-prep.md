> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P1] Follow-up — Directional Volume architektonisch vorbereiten, ohne Phase-1-Scoring zu erweitern

## Context / Source
- Das Ergänzungsdokument fordert, Directional Volume **nicht** als Phase-1-Scorer-Komponente zu aktivieren, aber die Architektur so vorzubereiten, dass spätere Einführung **ohne Schema-/Contract-Bruch** möglich ist.
- Die aktuelle Ticketserie deckt Reversal-ohne-Reclaim und Run Manifest bereits ab, aber die gewünschte vorbereitende Contract-/Schema-Absicherung für Directional Volume ist noch nicht explizit genug verankert.
- Dieses Ticket ist ein bewusst kleines Follow-up und darf **keine** fachliche Phase-1-Erweiterung in Richtung aktiver Directional-Volume-Bewertung einführen.
- Verbindliche Ticket-Regeln gelten vollständig:
  - Canonical first
  - keine zweite Wahrheit
  - keine stillen Annahmen
  - Missing vs Invalid explizit
  - Nullability explizit
  - konkrete Tests statt bloßer Kategorien

## Goal
Die bestehenden Contracts / Schemas / scorer-nahen Strukturen so vorbereiten, dass Directional Volume später sauber ergänzt werden kann, ohne:
- bestehende Phase-1-Semantik zu ändern,
- Feldnamen nachträglich zu brechen,
- Output-/SoT-Schemata rückwirkend umzubauen,
- implizite Alias- oder Platzhalterlogik einzuführen.

## Scope
- Kanonische und/oder interne Contract-/Schema-Erweiterung für **vorbereitende** Directional-Volume-Anschlussfähigkeit
- falls nötig:
  - reservierte optionale Felder oder Namespaces
  - scorer-nahe Strukturfelder
  - Output-/SoT-Anschlussfähigkeit, sofern wirklich für spätere Erweiterung nötig
- Tests / Verifikation dafür, dass:
  - die neuen vorbereitenden Felder optional bleiben
  - sie Phase-1-Entscheidungen nicht beeinflussen
  - bestehende Schemata/Artefakte kompatibel bleiben

## Out of Scope
- Keine aktive Directional-Volume-Berechnung
- Keine neue Live-Scoring-Logik
- Keine Decision-Layer-Erweiterung durch Directional Volume
- Keine Änderung produktiver ENTER/WAIT/NO_TRADE-Schwellen
- Keine neue Pflichtdatenquelle für Phase 1
- Kein künstliches Platzhalter-Scoring mit Dummy-Werten
- Keine Portfolio-/Exit-/Hold-Logik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- relevante Canonical Docs zu Pipeline / Scorern / Contracts
- aktuelle alleinige Referenz
- Ergänzungsdokument zu V4

## Proposed change (high-level)
Before:
- Directional Volume ist fachlich als spätere Erweiterung vorgesehen, aber die vorbereitende Contract-/Schema-Verankerung ist nicht explizit genug.
- Dadurch besteht das Risiko, dass spätere Einführung von Directional Volume:
  - neue ad-hoc Feldnamen erzeugt,
  - bestehende Scorer-/Output-Schemata bricht,
  - oder implizite Parallel-Contracts erzeugt.

After:
- Es gibt eine explizite architektonische Vorbereitung für Directional Volume, z. B. über klar benannte optionale Anschlussfelder / Namespaces / Contract-Hinweise.
- Diese Vorbereitung verändert **nicht** die fachliche Phase-1-Bewertung.
- Bestehende Outputs und Decisions bleiben unverändert.
- Spätere Einführung kann ohne rückwirkenden Schema-Bruch erfolgen.

Edge cases:
- vorbereitende Felder fehlen komplett
- vorbereitende Felder sind `null`
- bestehende Artefakte ohne Directional-Volume-Daten bleiben voll gültig
- spätere Erweiterung darf keinen Alias-Konflikt mit bestehenden Scorer-Feldern erzeugen

Backward compatibility impact:
- Bestehende Phase-1-Artefakte und Decisions bleiben fachlich unverändert.
- Falls optionale vorbereitende Felder ergänzt werden, müssen sie rückwärtskompatibel und nullable sein.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Directional Volume bleibt in Phase 1 eine spätere Erweiterung und darf durch dieses Ticket nicht aktiv in Decision oder produktives Scoring einfließen.
- **Nur Vorbereitung, keine Aktivierung:** Dieses Ticket schafft Anschlussfähigkeit, keine fachliche Bewertungslogik.
- **Keine zweite Wahrheit:** Keine parallelen ad-hoc Felder, wenn vorbereitende Felder ergänzt werden; Namen und Struktur müssen konsistent und zukunftsfähig sein.
- **Field-name discipline:** Wenn vorbereitende Directional-Volume-Felder eingeführt werden, müssen sie explizit als optional und vorbereitend markiert sein; keine freien Alias-Namen.
- **Nullability explizit:** Vorbereitende Felder dürfen `null` sein; `null` bedeutet hier „nicht erhoben / nicht verwendet“ und darf nicht zu `false`, `0` oder „negativ“ kollabieren.
- **Missing vs Invalid trennen:** Fehlende vorbereitende Felder in Phase 1 sind gültig; formal ungültige Werte in solchen Feldern sind getrennt zu behandeln.
- **Keine Scope-Ausweitung:** Keine neuen Decision-Reasons, keine Score-Änderung, keine Pflicht in Output-Renderern außer falls Contract-seitig explizit nötig.
- **Determinismus:** Gleicher Input + gleiche Config => gleiche Phase-1-Outputs; vorbereitende DV-Contracts dürfen bestehende Ergebnisse nicht verändern.
- **Partielle Nested-Overrides explizit:** Falls es einen neuen verschachtelten Config-Block für Directional Volume preparation gibt, muss explizit festgelegt werden, ob Overrides mergen oder vollständig ersetzen.

## Implementation Notes (optional but useful)
- Bevorzugt minimale, klar benannte Vorbereitung statt großer Vorab-Implementierung.
- Wenn möglich, Contract-/Schema-Vorbereitung dort ansetzen, wo Scorer-V2 / Output-SoT ohnehin schon strukturierte Felder tragen.
- Falls vorbereitende Felder ergänzt werden, besser als eigener optionaler Namespace statt losem Einzel-Feldmix.
- Keine Dummy-Berechnung und kein Platzhalter-Score; lieber explizit `null` / nicht vorhanden als scheinbar sinnvolle Fake-Werte.

## Acceptance Criteria (deterministic)
1) Directional Volume ist durch dieses Ticket architektonisch vorbereitbar, ohne aktive Phase-1-Scoring- oder Decision-Logik einzuführen.

2) Falls vorbereitende Felder oder Namespaces ergänzt werden, sind sie:
   - optional
   - klar benannt
   - rückwärtskompatibel
   - nullable, wenn nicht erhoben / nicht verwendet

3) Bestehende Phase-1-Outputs und Decisions bleiben bei identischem Input unverändert.

4) Fehlende vorbereitende Directional-Volume-Felder sind in Phase 1 ein gültiger Zustand und werden nicht als Fehler oder negatives Signal interpretiert.

5) Falls vorbereitende Felder formal ungültige Werte enthalten, ist das klar von „fehlend/nicht verwendet“ getrennt.

6) Es wird keine neue produktive Decision- oder Score-Abhängigkeit von Directional Volume eingeführt.

7) Tests oder Verifikation belegen, dass:
   - bestehende Artefakte ohne Directional-Volume-Daten gültig bleiben
   - optionale vorbereitende Felder keine fachliche Phase-1-Änderung bewirken
   - keine Schema-/Contract-Kollision mit bestehenden Feldern entsteht

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (falls vorbereitender DV-Config-Block eingeführt wird: Missing key nutzt zentralen Default oder bleibt inaktiv)
- **Config Invalid Value Handling:** ✅ (formal ungültige vorbereitende Werte => klarer Fehler oder klarer Invalid-Pfad; fehlend ≠ invalid)
- **Nullability / kein bool()-Coercion:** ✅ (`null` in vorbereitenden DV-Feldern bleibt semantisch „nicht erhoben / nicht verwendet“)
- **Not-evaluated vs failed getrennt:** ✅ (fehlende DV-Daten in Phase 1 ≠ negatives Signal)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (keine halb-validen Schema-/Contract-Zustände)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (keine Konflikte bei neuen optionalen Namespaces/Feldern)
- **Deterministische Sortierung / Tie-breaker:** ✅ (bestehende Reihenfolgen/Outputs bleiben unverändert)

## Tests (required if logic changes)
- Unit:
  - bestehende Artefakte ohne vorbereitende DV-Felder bleiben gültig
  - optionale vorbereitende DV-Felder dürfen `null` sein
  - fehlende DV-Felder erzeugen kein negatives Signal
  - formal ungültige DV-Feldwerte werden getrennt von fehlenden Feldern behandelt

- Integration:
  - identischer Input ohne DV-Daten => identische Phase-1-Outputs wie vorher
  - identischer Input mit optionalen, aber ungenutzten DV-Feldern => ebenfalls identische Phase-1-Outputs
  - keine neue Decision-/Score-Abhängigkeit entsteht

- Golden fixture / verification:
  - nur dort Golden-/Fixture-Anpassungen, wo vorbereitende optionale Felder / Schemas bewusst ergänzt werden
  - keine kosmetischen Änderungen ohne semantischen Grund

## Constraints / Invariants (must not change)
- [ ] Directional Volume bleibt in Phase 1 eine spätere Erweiterung
- [ ] keine aktive Directional-Volume-Berechnung
- [ ] keine Änderung produktiver Decision-/Scoring-Logik
- [ ] fehlende DV-Daten bleiben gültig
- [ ] vorbereitende Felder bleiben optional und nullable
- [ ] bestehende Outputs bleiben bei gleichem Input fachlich unverändert

## Definition of Done (Codex must satisfy)
- [ ] vorbereitende Directional-Volume-Contract-/Schema-Absicherung implementiert
- [ ] keine aktive Phase-1-DV-Logik eingeführt
- [ ] Missing vs Invalid und Nullability explizit abgedeckt
- [ ] Tests / Verifikation gemäß Acceptance Criteria vorhanden
- [ ] keine Schema-/Contract-Kollision mit bestehenden Feldern
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-08T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
