> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-23 Shadow Mode / Parallelbetrieb für alte und neue Pipeline einführen

## Context / Source
- Die aktuelle alleinige Referenz verlangt einen kontrollierten Übergang vom alten Ranking-/Watchlist-System zur neuen Decision-first-Architektur.
- Bereits implementierte oder geplante PRs führen neue Stages und neue Outputs ein:
  - Tradeability Gate
  - Risk-Stufe
  - Decision Layer
  - `trade_candidates` als kanonische SoT
- Ohne Shadow Mode / Parallelbetrieb besteht das Risiko eines harten Umschaltens mit schlechter Vergleichbarkeit und erhöhtem Fehlerpotenzial.

## Goal
Einen expliziten Shadow-Mode einführen, der alten und neuen Pfad kontrolliert parallel laufen lassen kann, sodass:

- alter und neuer Pipeline-Pfad getrennt aktivierbar sind
- neue Stages zunächst parallel beobachtet werden können
- Outputs vergleichbar bleiben
- Umschalten nicht als Big Bang erfolgen muss

## Scope
- Pipeline-Konfiguration und Pipeline-Orchestrierung für Shadow Mode
- Aktivierungs-/Deaktivierungslogik für:
  - neue Tradeability-/Risk-/Decision-Pfade
  - alte Ranking-/Watchlist-Pfade, soweit noch erforderlich
- kontrollierter Parallelbetrieb der relevanten Outputs
- minimale, klare Status-/Manifest-Hinweise, falls für Parallelbetrieb nötig

## Out of Scope
- Keine neue Fachlogik für Tradeability, Risk, Decision oder BTC-Regime
- Kein Portfolio-Management
- Keine Kalibrierung
- Kein Entfernen des alten Pfads
- Keine endgültige Umschalt-/Abschaltlogik für Legacy-Artefakte über diesen PR hinaus
- Keine neue zweite SoT

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`

## Proposed change (high-level)
Before:
- Neue und alte Pfade sind nicht explizit als kontrollierter Parallelbetrieb modelliert.
- Übergangsverhalten ist anfällig für Big-Bang-Umschaltungen oder stillen Drift.

After:
- Die Pipeline unterstützt expliziten Shadow Mode / Parallelbetrieb.
- Alte und neue Stages sind über zentrale Config-/Feature-Flags kontrollierbar.
- Der neue Pfad kann beobachtet werden, ohne den alten sofort zu ersetzen.
- Es ist klar erkennbar, welcher Pfad bzw. welche Kombination aktiv war.
- `trade_candidates` bleibt die neue fachliche SoT, auch wenn alte Artefakte temporär weiterlaufen.

Edge cases:
- nur alter Pfad aktiv
- nur neuer Pfad aktiv
- beide Pfade parallel aktiv
- neuer Pfad aktiv, aber mit leerem Candidate-Set
- alter Pfad aktiv, neuer Pfad deaktiviert
- partiell aktivierte neue Stages sind nicht erlaubt, wenn sie die Canonical-Pipeline semantisch brechen würden

Backward compatibility impact:
- Übergangsverhalten wird erweitert, nicht entfernt.
- Bestehende Workflows können parallel weiterlaufen, solange der Shadow Mode korrekt konfiguriert ist.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Shadow Mode dient nur dem Übergang, nicht der Einführung einer zweiten fachlichen Wahrheit.
- **`trade_candidates` bleibt fachliche Ziel-SoT:** Parallelbetrieb ändert das nicht.
- **Feature Flags zentral:** Keine verstreuten ad-hoc Booleans im Code.
- **Keine semantisch gebrochenen Halbzustände:** Wenn bestimmte Stages logisch zusammengehören, muss ihre Aktivierung konsistent erfolgen.
- **Determinismus:** Gleiche Config + gleicher Input => gleicher aktiver Pfad und gleiche Artefakte.
- **Missing vs invalid:** fehlende Shadow-Mode-Keys nutzen zentrale Defaults; ungültige Kombinationen erzeugen klaren Fehler.
- **Keine stillen Fallbacks:** Der Code darf nicht heimlich vom neuen auf den alten Pfad zurückfallen oder umgekehrt.
- **Explizite Pfadtransparenz:** Es muss nachvollziehbar sein, welcher Pfad aktiv war.
- **Keine Legacy-Verfestigung:** Shadow Mode ist Übergangsmechanik, kein neues dauerhaftes Parallel-System.

## Implementation Notes (optional but useful)
- Wahrscheinlich betroffene Stellen:
  - zentrale Config
  - Pipeline-Orchestrierung
  - ggf. Run Manifest / Runtime-Meta
- Wenn bereits einzelne `enabled`-Flags existieren, sollen diese konsolidiert und nicht verdoppelt werden.
- Ungültige Konfigurationskombinationen sollten früh und explizit fehlschlagen.

## Acceptance Criteria (deterministic)
1) Es existiert eine zentrale, kanonisch benannte Konfigurationssteuerung für den Shadow Mode / Parallelbetrieb.

2) Die Pipeline kann deterministisch in mindestens folgenden Modi laufen:
   - alter Pfad aktiv, neuer Pfad inaktiv
   - neuer Pfad aktiv, alter Pfad inaktiv
   - beide Pfade parallel aktiv, sofern Canonical dies erlaubt

3) Ungültige Aktivierungskombinationen erzeugen einen klaren Fehler und keinen stillen Fallback.

4) Es ist programmatisch oder in den Laufartefakten eindeutig erkennbar, welcher Pfad aktiv war.

5) Der Shadow Mode erzeugt keine zweite fachliche SoT neben `trade_candidates`.

6) Gleicher Input + gleiche Config => deterministisch identisches Shadow-Mode-Verhalten.

7) Tests decken die zulässigen und unzulässigen Aktivierungskombinationen explizit ab.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (fehlende Shadow-Mode-Keys nutzen zentrale Defaults)
- **Config Invalid Value Handling:** ✅ (ungültige Moduskombinationen => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (keine implizite truthiness-basierte Pfadwahl)
- **Not-evaluated vs failed getrennt:** ✅ (N/A im engeren Sinn, aber ungültige Aktivierung ≠ semantischer Fachstatus)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (kein halb-aktivierter Modus bei Fehler)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (Artefakte im Parallelbetrieb dürfen sich nicht still überschreiben)
- **Deterministische Sortierung / Tie-breaker:** ✅ (Pfad- und Artefaktwahl deterministisch)

## Tests (required if logic changes)
- Unit:
  - Default-Verhalten bei fehlenden Shadow-Mode-Keys
  - klarer Fehler bei ungültigen Moduskombinationen
  - deterministische Pfadwahl
  - keine stillen Fallbacks

- Integration:
  - alter Pfad aktiv / neuer aus
  - neuer Pfad aktiv / alter aus
  - beide aktiv (falls erlaubt)
  - Artefakte / Manifest zeigen korrekt den aktiven Modus
  - keine stillen Überschreibungen

- Golden fixture / verification:
  - nur dort anpassen, wo bestehende Laufartefakte jetzt explizit Shadow-Mode-Information enthalten
  - keine unnötigen kosmetischen Änderungen

## Constraints / Invariants (must not change)
- [ ] `trade_candidates` bleibt Ziel-SoT
- [ ] Shadow Mode ist Übergangsmechanik, keine zweite Wahrheit
- [ ] keine stillen Fallbacks zwischen alt und neu
- [ ] ungültige Moduskombinationen brechen klar
- [ ] deterministische Pfadwahl
- [ ] keine Scope-Erweiterung in Kalibrierung / Portfolio / Exit-Logik

## Definition of Done (Codex must satisfy)
- [ ] Shadow-Mode-/Parallelbetriebslogik implementiert
- [ ] zentrale Config-Anbindung vorhanden
- [ ] gültige und ungültige Moduskombinationen getestet
- [ ] aktive Pfade transparent nachvollziehbar
- [ ] keine zweite fachliche SoT eingeführt
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
