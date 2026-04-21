> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-24 Umschaltlogik für Legacy- zu Decision-first-Pfad dokumentieren und testen

## Context / Source
- Die aktuelle alleinige Referenz verlangt einen kontrollierten Übergang vom Legacy-Ranking-/Watchlist-Pfad zum neuen Decision-first-Pfad.
- PR-23 führt Shadow Mode / Parallelbetrieb ein.
- PR-24 konkretisiert und härtet die Umschaltlogik: Wann ist welcher Pfad primär, wie wird der aktive Modus dokumentiert, und welche Invarianten gelten beim Wechsel.
- Dieses Ticket folgt den verbindlichen neuen Regeln:
  - Canonical first
  - keine stillen Fallbacks
  - klare Default-/Invalid-Semantik
  - deterministische Aktivierung
  - konkrete Tests statt nur Kategorien

## Goal
Die Umschaltlogik zwischen Legacy- und neuem Pfad ist explizit dokumentiert und testseitig abgesichert, sodass:

- der aktive Modus eindeutig bestimmt ist
- die Primär-/Sekundärrolle von Artefakten klar ist
- ungültige Umschaltzustände explizit fehlschlagen
- kein stiller Big-Bang-Switch oder heimlicher Rückfall entsteht

## Scope
- Dokumentation / Run-Transparenz für Umschaltlogik
- Tests für zulässige und unzulässige Umschaltzustände
- falls nötig: minimale Produktionslogik, um den aktiven Modus und die Primärrolle sauber zu markieren
- ggf. Anpassung von Run-Manifest-/Meta-Information, falls nötig für explizite Umschalttransparenz

## Out of Scope
- Keine neue Fachlogik für Tradeability, Risk, Decision oder BTC-Regime
- Keine Output-Renderer-Neuentwicklung
- Kein Entfernen des Legacy-Pfads
- Keine Kalibrierung
- Keine Portfolio-/Exit-/Hold-Logik
- Keine zweite fachliche SoT

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`

## Proposed change (high-level)
Before:
- Shadow Mode kann parallel laufen, aber die Umschaltlogik von „beobachten“ zu „neuer Pfad primär“ ist nicht explizit genug dokumentiert und abgesichert.
- Es besteht Risiko für implizite oder schwer nachvollziehbare Umschaltzustände.

After:
- Es ist explizit dokumentiert und maschinenlesbar nachvollziehbar:
  - welcher Pfad aktiv war
  - welcher Pfad primär war
  - welche Artefakte nur Kontext / Legacy sind
- Tests sichern ab:
  - zulässige Umschaltzustände funktionieren deterministisch
  - unzulässige Zustände brechen klar
  - `trade_candidates` bleibt Ziel-SoT des neuen Pfads
  - Legacy-Artefakte werden nicht still als primäre Wahrheit behandelt, wenn der neue Pfad primär ist

Edge cases:
- nur Legacy aktiv
- nur neuer Pfad aktiv
- Parallelbetrieb, aber neuer Pfad als primär markiert
- Parallelbetrieb, aber Legacy fälschlich als primär markiert
- fehlende Umschalt-Config
- widersprüchliche Umschalt-Config
- leere `trade_candidates` bei aktivem neuen Primärpfad

Backward compatibility impact:
- Übergangsverhalten wird klarer und transparenter.
- Bestehende Workflows bleiben möglich, aber ungültige/mehrdeutige Umschaltzustände werden nicht mehr still akzeptiert.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** `trade_candidates` bleibt fachliche Ziel-SoT des neuen Pfads.
- **Kein stiller Primärwechsel:** Ob Legacy oder neuer Pfad primär ist, muss explizit aus Config/Manifest hervorgehen.
- **Keine stillen Fallbacks:** Wenn der primäre neue Pfad aktiv sein soll, darf der Code nicht heimlich auf Legacy zurückfallen.
- **Missing vs invalid trennen:** fehlende Umschalt-Keys nutzen zentrale Defaults; widersprüchliche Zustände sind invalid und brechen klar.
- **Determinismus:** gleicher Input + gleiche Config => identischer aktiver und primärer Modus.
- **Keine zweite Wahrheit:** Parallelbetrieb darf Legacy-Artefakte nicht wieder zur fachlichen Primärquelle machen.
- **Nullability klar:** falls ein Primärpfad nicht gesetzt sein darf, muss das explizit beschrieben und getestet werden; keine truthiness-Abkürzungen.
- **Keine Scope-Ausweitung:** dieses Ticket dokumentiert/testet Umschaltlogik, erfindet aber keine neue Fachbewertung.

## Implementation Notes (optional but useful)
- Wahrscheinlich betroffene Stellen:
  - Shadow-Mode-Config / Pipeline-Orchestrierung
  - Run Manifest / Runtime-Meta
  - Tests für Moduskombinationen
- Falls bereits `enabled`-Flags existieren, ihre Kombinationen explizit validieren statt implizit zu deuten.
- Falls „primär“ bereits im Run-Manifest notiert wird, Tests daran aufhängen statt zusätzliche Wahrheitsschicht einzuführen.

## Acceptance Criteria (deterministic)
1) Es ist explizit dokumentiert oder maschinenlesbar markiert, welcher Pfad aktiv und welcher Pfad primär war.

2) Ein zulässiger Modus „nur Legacy aktiv“ ist deterministisch und transparent erkennbar.

3) Ein zulässiger Modus „nur neuer Pfad aktiv“ ist deterministisch und transparent erkennbar.

4) Ein zulässiger Modus „Parallelbetrieb“ ist nur dann erlaubt, wenn die Primärrolle explizit festgelegt und transparent ist.

5) Widersprüchliche Umschaltkonfigurationen erzeugen einen klaren Fehler und keinen stillen Fallback.

6) Wenn der neue Pfad primär ist, bleibt `trade_candidates` die fachliche Primärquelle.

7) Tests decken mindestens die zulässigen und unzulässigen Umschaltzustände explizit ab.

8) Gleicher Input + gleiche Config => identischer aktiver/primärer Modus und identische entsprechende Artefakt-Transparenz.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (fehlende Umschalt-Keys nutzen zentrale Defaults)
- **Config Invalid Value Handling:** ✅ (widersprüchliche Primär-/Aktivierungszustände => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (keine truthiness-basierte Primärpfadwahl)
- **Not-evaluated vs failed getrennt:** ✅ (N/A im engeren Fachsinn; Umschaltfehler ≠ Fachbewertung)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (bei invalidem Umschaltzustand kein halb-konsistenter Run-Status)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (Parallel-/Umschaltartefakte dürfen sich nicht still überschreiben)
- **Deterministische Sortierung / Tie-breaker:** ✅ (Pfad-/Moduswahl deterministisch)

## Tests (required if logic changes)
- Unit:
  - Default-Verhalten bei fehlenden Umschalt-Keys
  - klarer Fehler bei widersprüchlicher Umschalt-Config
  - explizite Primärrolle wird korrekt gesetzt/erkannt
  - kein stiller Fallback von neu auf Legacy

- Integration:
  - nur Legacy aktiv
  - nur neuer Pfad aktiv
  - Parallelbetrieb mit expliziter Primärrolle
  - unzulässiger Parallelbetrieb / widersprüchliche Primärrolle => klarer Fehler
  - Run-Transparenz / Manifest zeigt aktiven und primären Pfad korrekt

- Golden fixture / verification:
  - nur anpassen, wenn Artefakte/Manifest jetzt explizite Umschaltinformationen tragen
  - keine unnötigen kosmetischen Änderungen

## Constraints / Invariants (must not change)
- [ ] `trade_candidates` bleibt Ziel-SoT des neuen Pfads
- [ ] keine stillen Fallbacks zwischen Primärpfaden
- [ ] ungültige Umschaltzustände brechen klar
- [ ] Determinismus bleibt erhalten
- [ ] keine Scope-Ausweitung in Fachlogik / Kalibrierung / Portfolio

## Definition of Done (Codex must satisfy)
- [ ] Umschaltlogik transparent dokumentiert oder maschinenlesbar markiert
- [ ] zulässige und unzulässige Umschaltzustände getestet
- [ ] keine stille Primärpfadwahl
- [ ] `trade_candidates` bleibt fachliche Ziel-SoT
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
