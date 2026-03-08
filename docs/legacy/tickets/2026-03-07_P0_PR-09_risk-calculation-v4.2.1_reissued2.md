> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-09 Risk-Berechnung V4.2.1

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- Nach Tradeability muss die Phase-1-Risk-/Downside-Logik eingeführt werden, bevor die Decision Layer fachlich vollständig sein kann.
- `docs/canonical/RISK_MODEL.md` definiert ATR-basierten Stop als Phase-1-Default.

## Goal
Implementiere die Phase-1-Risk-Berechnung so, dass für voll evaluierbare Kandidaten deterministisch berechnet werden:
- `stop_price_initial`
- `risk_pct_to_stop`
- `rr_to_tp10`
- `rr_to_tp20`
- `risk_acceptable`

## Scope
- Risk-/Trade-Level-nahe Berechnung in der bestehenden Scoring-/Pipeline-Struktur
- relevante Tests
- minimale Verkabelung, damit die berechneten Felder an nachfolgende Stufen übergeben werden können

## Out of Scope
- Keine finale Decision Layer
- Keine BTC-Regime-Logik
- Keine Portfolio-Logik
- Keine Exit-/Hold-/Rotate-Logik
- Keine setup-spezifischen alternativen Stopmodelle jenseits des ATR-Defaults
- Keine Output-Renderer-Änderung, außer zwingend für Testbarkeit/Transport

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`

## Proposed change (high-level)
Before:
- Trade-Levels/Targets existieren teilweise, aber die Phase-1-Risk-Felder sind nicht als vollständiger, kanonischer Berechnungspfad implementiert.

After:
- Für evaluierbare Kandidaten wird ein ATR-basierter Initial-Stop berechnet.
- Darauf aufbauend werden `risk_pct_to_stop`, `rr_to_tp10`, `rr_to_tp20` und `risk_acceptable` deterministisch erzeugt.
- Missing vs Invalid vs Not-Evaluated ist sauber getrennt.

Edge cases:
- ATR fehlt / ist null / ungültig
- Entry-Preis fehlt oder ist ungültig
- Stop liegt nicht unter Entry bei Long-Spot
- TP10/TP20 nicht sinnvoll ableitbar
- Reversal ohne gültigen Reclaim / ohne belastbaren Anchor darf nicht als risk-ready gelten

Backward compatibility impact:
- Neue Risk-Felder entstehen im Datenfluss.
- Spätere Decision-/Output-PRs konsumieren diese Felder; dieses Ticket selbst führt noch keine finale Decision ein.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** ATR-basierter Stop ist Phase-1-Default.
- **Long spot only:** Risk-Berechnung ausschließlich für Long-Spot-Semantik.
- **Missing ≠ Invalid:** Fehlende Inputs führen nicht stillschweigend zu Zahlen; ungültige Inputs müssen klar abgegrenzt werden.
- **Not-evaluated ≠ failed:** Wenn Risk nicht berechnet werden kann, ist das kein negativer Risk-Score, sondern ein fehlender evaluierbarer Pfad.
- **Stop muss logisch sein:** `stop_price_initial < entry_price` für Long-Spot.
- **Keine bool()-Koerzierung bei semantisch nullable Feldern.**
- **Keine alternative Stop-Engine hineinziehen:** kein Support-Level-/Structure-Stop als paralleler Phase-1-Standard.
- **Determinismus ist Pflicht:** gleicher Input + gleiche Config => gleiche Risk-Felder.

## Implementation Notes (optional but useful)
Wahrscheinliche Berührungspunkte:
- `scanner/pipeline/scoring/trade_levels.py`
- ggf. Setup-Scorer unter `scanner/pipeline/scoring/`
- ggf. Pipeline-Transportstruktur

Empfohlene Berechnungsreihenfolge:
1. Entry-Preis validieren
2. ATR validieren
3. ATR-basierten `stop_price_initial` ableiten
4. `risk_pct_to_stop` berechnen
5. `rr_to_tp10`, `rr_to_tp20` gegen bestehende TP10/TP20 berechnen
6. `risk_acceptable` aus Config-Schwellen ableiten

## Acceptance Criteria (deterministic)
1) Für einen gültigen Long-Spot-Kandidaten mit gültigem Entry und ATR wird `stop_price_initial` deterministisch berechnet.

2) `risk_pct_to_stop` wird aus Entry und `stop_price_initial` deterministisch berechnet.

3) `rr_to_tp10` und `rr_to_tp20` werden deterministisch berechnet, sofern TP10/TP20 und Risk valide vorliegen.

4) `risk_acceptable` wird config-driven aus den kanonischen Risk-Schwellen abgeleitet.

5) Für einen Kandidaten mit fehlendem oder ungültigem ATR werden keine stillschweigend brauchbar wirkenden Risk-Zahlen erzeugt.

6) Für Long-Spot gilt: Ein Stop auf oder über Entry ist kein valider Initial-Stop und wird nicht als akzeptabler Risk-Pfad behandelt.

7) Missing Inputs und invalid Inputs sind im Codepfad explizit getrennt.

8) Bei identischem Input und identischer Config sind alle Risk-Felder deterministisch.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅
- **Config Invalid Value Handling:** ✅
- **Nullability / kein bool()-Coercion:** ✅
- **Not-evaluated vs failed getrennt:** ✅
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A)
- **Deterministische Sortierung / Tie-breaker:** ✅ (soweit für numerische Ableitung/Transport relevant)

## Tests (required if logic changes)
- Unit:
  - gültiger ATR-Stop
  - ungültiger/fehlender ATR
  - ungültiger Entry
  - Stop logisch unter Entry
  - RR-Berechnung für TP10/TP20
  - config-driven `risk_acceptable`
- Integration:
  - Risk-Felder werden an nachgelagerte Stufen durchgereicht
  - identischer Input => identische Risk-Felder
- Golden fixture / verification:
  - nur anpassen, wenn bestehende Golden-Files jetzt bewusst die neuen Risk-Felder tragen

## Constraints / Invariants (must not change)
- [ ] ATR-basierter Stop bleibt Phase-1-Default
- [ ] Long-Spot-only bleibt erhalten
- [ ] Keine Decision Layer in diesem Ticket
- [ ] Keine Portfolio-/Exit-Logik in diesem Ticket
- [ ] Missing vs Invalid vs Not-Evaluated bleibt getrennt
- [ ] Deterministische Berechnung

## Definition of Done (Codex must satisfy)
- [ ] Codeänderungen gemäß Acceptance Criteria implementiert
- [ ] Tests gemäß Ticket ergänzt
- [ ] Keine Scope-Überschreitung in Decision-/BTC-/Portfolio-/Output-Logik
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-07T00:00:00Z"
priority: P0
type: feature
owner: codex
related_issues: []
```
