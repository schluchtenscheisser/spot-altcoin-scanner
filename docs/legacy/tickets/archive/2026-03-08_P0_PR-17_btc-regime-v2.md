> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-17 BTC-Regime V2 implementieren

## Context / Source
- Die aktuelle alleinige Referenz definiert in EPIC 8 / PR-17 den BTC-Regime-Mechanismus für Phase 1.
- Die Decision Layer aus PR-15 konsumiert optional ein BTC-Regime und verwendet daraus eine effektive ENTER-Schwelle.
- Phase 1 verlangt ausdrücklich:
  - kein pauschaler Blocker für Setup-Typen,
  - keine globale Score-Degradierung als versteckte Wahrheit,
  - sondern eine transparente Schwellenanhebung bei `RISK_OFF`.
- Das Ticket unterliegt den neuen verbindlichen Regeln, insbesondere für:
  - Missing vs Invalid Config
  - Determinismus
  - keine implizite Bool-Koerzierung
  - kein Scope-Drift in Portfolio-/Exit-/Kalibrierungslogik

## Goal
Das BTC-Regime wird als transparenter, deterministischer Decision-Modifier implementiert, sodass:
- `RISK_OFF`, `NEUTRAL`, `RISK_ON` explizit modelliert sind,
- bei `RISK_OFF` die effektive ENTER-Schwelle um den konfigurierten Boost erhöht wird,
- starke Setups weiter `ENTER` werden können,
- Kandidaten, die unter NEUTRAL `ENTER` wären, unter RISK_OFF aber nicht mehr, zu `WAIT` mit `btc_regime_caution` werden,
- das aktive Regime im Output/Decision-Kontext sichtbar bleibt.

## Scope
- `scanner/pipeline/regime.py`
- `scanner/pipeline/decision.py` (nur soweit nötig für die saubere Regime-Integration)
- ggf. kleine Typ-/Konstanten-Helfer im direkten Regime-Kontext
- begleitende Tests unter `tests/`

## Out of Scope
- Keine neue Portfolio-Logik
- Keine Änderung von Tradeability- oder Risk-Berechnung
- Keine Output-Renderer-Umstellung über minimal nötige Regime-Sichtbarkeit hinaus
- Keine pauschale Setup-Typ-Sperre
- Keine Exit-/Hold-/Rotate-Logik
- Keine Wahrscheinlichkeitskalibrierung
- Keine Änderung der Grunddefinition von `ENTER / WAIT / NO_TRADE`

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- ggf. vorhandene Canonical-Regime-Dokumentation im Repo, falls separat vorhanden

## Proposed change (high-level)
Before:
- BTC-Regime kann im Bestand als globaler Multiplikator oder versteckte Degradierung wirken.
- Die Phase-1-Zielarchitektur verlangt stattdessen einen transparenten, reason-fähigen Decision-Modifier.

After:
- `scanner/pipeline/regime.py` liefert ein explizites Regime, z. B.:
  - `RISK_OFF`
  - `NEUTRAL`
  - `RISK_ON`
- `scanner/pipeline/decision.py` verwendet daraus:
  - `effective_min_score = min_score_for_enter + btc_risk_off_enter_boost` bei `RISK_OFF`
  - `effective_min_score = min_score_for_enter` bei `NEUTRAL` oder `RISK_ON`
- Ein Coin, der:
  - bei `NEUTRAL` ein `ENTER` wäre,
  - bei `RISK_OFF` aber nicht mehr die ENTER-Schwelle erreicht,
  wird zu `WAIT` mit Reason `btc_regime_caution`
- Kein Setup-Typ wird pauschal blockiert.
- Das aktive BTC-Regime ist im Candidate-/Decision-Kontext sichtbar.

Edge cases:
- Regime fehlt komplett
- ungültiger Regime-Wert
- `RISK_ON` soll nicht unter die Basisschwelle senken, sofern nicht kanonisch definiert
- Coin mit sehr hohem Score bleibt auch bei `RISK_OFF` `ENTER`
- Coin knapp unter erhöhter Schwelle wird `WAIT`, nicht `NO_TRADE`, sofern sonst voll evaluierbar
- BTC-Regime darf keinen Kandidaten mit fachlich negativem Risk zu `WAIT` retten

Backward compatibility impact:
- Bestehende implizite Regime-Wirkung wird auf einen expliziten Schwellenmechanismus umgestellt oder darauf abgebildet.
- Das Verhalten wird transparenter und reason-fähig, kann aber einzelne Candidate-Status gegenüber früherem Hidden-Multiplier-Verhalten ändern.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Regime-Werte und Semantik exakt wie autoritativ definiert verwenden.
- **Regime ist Modifier, kein Hard Blocker:** Keine pauschale Setup-Blockade, keine globale heimliche Score-Degradierung.
- **Missing vs Invalid trennen:** Fehlendes Regime und ungültiges Regime dürfen nicht stillschweigend gleich behandelt werden.
- **NEUTRAL ist Baseline:** Wenn nicht anders kanonisch festgelegt, verändert nur `RISK_OFF` die ENTER-Schwelle.
- **RISK_ON senkt nichts implizit ab:** Keine zusätzliche „Boost nach unten“-Logik erfinden.
- **Reason-Key Pflicht:** Wenn ein Coin nur wegen `RISK_OFF` von ENTER zu WAIT fällt, muss `btc_regime_caution` gesetzt werden.
- **Keine bool()-Koerzierung für Regime-Zustände:** Regime explizit als Enum/String behandeln.
- **Keine Scope-Ausweitung in Portfolio oder Exit-Logik.**
- **Determinismus:** Gleicher Input + gleiche Config + gleiches Regime => identisches Ergebnis.

## Implementation Notes (optional but useful)
- Prüfe bestehende Regime-Logik in `scanner/pipeline/regime.py`.
- Wenn dort bereits Multiplikatoren oder Risk-Off-Suppression existieren, diese nicht parallel weiterlaufen lassen; auf die kanonische Schwellenlogik zurückführen.
- In `decision.py` nur den minimal nötigen Integrationspunkt anfassen:
  - Berechnung `effective_min_score`
  - Reason `btc_regime_caution`
  - Sichtbarkeit des Regimes im Decision-Kontext
- Tests sollten Beispiele aus der Referenz explizit nachbilden:
  - Score 85 => ENTER auch bei RISK_OFF (bei Schwelle 80)
  - Score 72 => WAIT bei RISK_OFF, ENTER bei NEUTRAL

## Acceptance Criteria (deterministic)
1) `scanner/pipeline/regime.py` liefert oder verarbeitet explizite Regime-Zustände:
   - `RISK_OFF`
   - `NEUTRAL`
   - `RISK_ON`

2) In `decision.py` wird bei `RISK_OFF` die effektive ENTER-Schwelle deterministisch erhöht:
   - `effective_min_score = min_score_for_enter + btc_risk_off_enter_boost`

3) In `decision.py` bleibt bei `NEUTRAL` und `RISK_ON` die ENTER-Schwelle auf der Baseline, sofern Canonical nichts anderes vorgibt.

4) Ein Coin, der unter `NEUTRAL` `ENTER` wäre, unter `RISK_OFF` aber nicht mehr, wird zu `WAIT` mit Reason `btc_regime_caution`, sofern er sonst voll evaluierbar ist.

5) Ein Coin mit deutlich ausreichend hohem Score bleibt auch unter `RISK_OFF` `ENTER`.

6) Das BTC-Regime ist im Candidate-/Decision-Kontext explizit sichtbar.

7) Kein Setup-Typ wird pauschal wegen BTC-Regime blockiert.

8) Fehlendes Regime und ungültiges Regime werden explizit und getrennt behandelt; keine stille Koerzierung.

9) Bei identischem Input und identischer Config/Regime ist die Wirkung deterministisch.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (Test: fehlender `btc_risk_off_enter_boost` greift über zentralen Default; fehlender Regime-Modus folgt kanonischer Baseline-Regel)
- **Config Invalid Value Handling:** ✅ (Test: ungültiger Boost oder ungültiger Regime-Wert => klarer Fehler, nicht stille Koerzierung)
- **Nullability / kein bool()-Coercion:** ✅ (Regime ist expliziter Zustand, kein truthy/falsy Toggle; fehlendes Regime wird semantisch klar behandelt)
- **Not-evaluated vs failed getrennt:** ✅ (Coin wegen RISK_OFF von ENTER zu WAIT ≠ fachlich negatives Risk/Tradeability)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A)
- **Deterministische Sortierung / Tie-breaker:** ✅ (Wirkung des Regimes deterministisch; keine implizite Reihenfolgedrift)

## Tests (required if logic changes)
- Unit:
  - `RISK_OFF` erhöht `effective_min_score`
  - `NEUTRAL` nutzt Basisschwelle
  - `RISK_ON` nutzt Basisschwelle, sofern nichts anderes kanonisch definiert ist
  - Score 85 bleibt ENTER bei `RISK_OFF` (bei Beispiel-Schwelle 80)
  - Score 72 wird WAIT bei `RISK_OFF`, ENTER bei `NEUTRAL`
  - `btc_regime_caution` wird gesetzt, wenn nur das Regime den ENTER-Pfad verhindert
  - fehlender Boost => zentraler Default
  - ungültiger Regime-Wert => klarer Fehler

- Integration:
  - Decision + Regime zusammen liefern deterministisch dieselben Status
  - keine pauschale Setup-Blockade
  - fachlich negatives Risk oder `tradeability = MARGINAL/FAIL` wird durch Regime nicht „gerettet“

- Golden fixture / verification:
  - Nur anpassen, wenn bestehende Tests eine ältere Hidden-Multiplier-Logik indirekt festhalten
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] BTC-Regime bleibt Schwellenmodifikator, kein Hard Blocker
- [ ] `btc_regime_caution` bleibt expliziter Reason-Key
- [ ] `NEUTRAL` bleibt Baseline
- [ ] keine Portfolio-/Exit-/Kalibrierungslogik
- [ ] keine stillen Multiplikatoren zusätzlich zur neuen Schwellenlogik
- [ ] deterministisches Verhalten

## Definition of Done (Codex must satisfy)
- [ ] Codeänderungen gemäß Acceptance Criteria implementiert
- [ ] Tests gemäß Ticket ergänzt/aktualisiert
- [ ] Missing vs Invalid für Regime-/Boost-Inputs explizit abgesichert
- [ ] Keine Scope-Überschreitung in Portfolio/Exit/Calibration/Output-Rendering
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
