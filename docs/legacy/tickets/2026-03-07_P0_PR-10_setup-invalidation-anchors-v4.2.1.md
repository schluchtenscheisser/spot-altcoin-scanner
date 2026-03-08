> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-10 Setup-seitige Invalidation-Anchors V4.2.1

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- EPIC 5 / PR-10 ergänzt die Setup-Scorer um optionale, setup-spezifische Invalidation-Anchors.
- Phase 1 nutzt für die tatsächliche Stop-Berechnung weiterhin den ATR-basierten Stop aus PR-09.
- Die Setup-Anchors sind in Phase 1 Kontextfelder für spätere Erweiterungen und für bessere Transparenz, aber **nicht** die primäre Stop-Methode.

## Goal
Die relevanten Setup-Scorer liefern optionale, maschinenlesbare Invalidation-Anchors mit, ohne die aktuelle ATR-basierte Stop-Logik zu verändern. Pro Setup sollen folgende Felder verfügbar sein:

- `invalidation_anchor_price`
- `invalidation_anchor_type`
- `invalidation_derivable`

## Scope
- `scanner/pipeline/scoring/breakout.py`
- `scanner/pipeline/scoring/pullback.py`
- `scanner/pipeline/scoring/reversal.py`
- ggf. enge, direkte Anpassungen an gemeinsame Score-/TypedDict-/Dataclass-Strukturen im Scoring-Kontext, falls nötig, um die neuen Felder sauber zu tragen

## Out of Scope
- Keine Änderung der tatsächlichen Stop-Berechnung in `scanner/pipeline/risk.py`
- Keine Änderung der Decision Layer
- Keine Änderung der Tradeability-Logik
- Keine Änderung an `breakout_trend_1_5d.py`, außer wenn technisch zwingend eine gemeinsame Interface-Struktur angepasst werden muss
- Keine Output-Renderer-Änderung
- Keine BTC-Regime-Logik
- Keine Portfolio-/Exit-/Hold-Logik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/PIPELINE.md`

## Proposed change (high-level)
Before:
- Die Setup-Scorer liefern Setup-/Score-/Signal-Felder, aber keine standardisierten setup-spezifischen Invalidation-Anchors.
- Spätere Erweiterungen in Richtung setup-basierter Stop-Alternativen oder Kontext-Transparenz sind dadurch unstrukturiert.

After:
- Breakout-, Pullback- und Reversal-Scorer liefern optional:
  - `invalidation_anchor_price`
  - `invalidation_anchor_type`
  - `invalidation_derivable`
- Die Felder sind rein additive Kontextfelder.
- Die ATR-basierte Stop-Berechnung aus PR-09 bleibt in Phase 1 unverändert die operative Wahrheit.
- Fehlende sinnvolle Anker führen **nicht** zu stillen Platzhalterwerten, sondern zu:
  - `invalidation_anchor_price = null/None`
  - `invalidation_anchor_type = null/None`
  - `invalidation_derivable = false`

Edge cases:
- Breakout ohne klar ableitbares Breakout-Level
- Pullback ohne sinnvollen EMA-/Support-Rebound-Anker
- Reversal ohne belastbaren Base-/Reclaim-Anker
- Setup liefert gültigen Score, aber keinen Anker
- Anchor-Preis wäre offensichtlich ungültig (<= 0 oder nicht numerisch) => nicht derivable, kein stilles Durchreichen

Backward compatibility impact:
- Scorer-Outputs werden additiv erweitert.
- Bestehende Konsumenten, die unbekannte Felder ignorieren, bleiben kompatibel.
- Es darf keine bestehende Stop- oder Decision-Semantik heimlich auf diese Felder umgestellt werden.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Die neuen Felder sind Kontext für Phase 1, keine Stop-Primärlogik.
- **Keine stille Stop-Umstellung:** `risk.py` darf durch dieses Ticket nicht auf setup-basierte Anchors umschwenken.
- **Nullability explizit:** Wenn kein Anchor ableitbar ist, `None`/`null` statt Fantasiewerte; `invalidation_derivable = false`.
- **Missing vs invalid trennen:** Nicht ableitbar ≠ fachlich negativer Score; Scorer dürfen nicht implizit „schlechter“ nur wegen fehlendem Anchor werden, sofern Canonical das nicht verlangt.
- **Kein bool()-Shortcut für Preise:** `invalidation_anchor_price` darf nicht über truthiness bewertet werden; `0` oder ungültig ist invalid, nicht „false im Sinne von nicht vorhanden“.
- **Determinismus:** Gleicher Input + gleiche Config => gleicher Anchor oder gleiches `not derivable`.
- **Keine Interface-Breaks:** Wenn bestehende Score-Dicts erweitert werden, additive Keys statt breaking changes.
- **Keine Decision-Reasons hineinziehen:** Dieses Ticket erzeugt keine neuen Decision-Statuswerte.

## Implementation Notes (optional but useful)
- Mögliche Anchor-Typen gemäß V4.2.1:
  - Breakout: `breakout_level`
  - Pullback: z. B. `ema_reclaim` oder `support_level`
  - Reversal: z. B. `base_low`, `ema_reclaim`, `reclaim_level`
- Wenn mehrere Anker denkbar sind, nur den kanonisch naheliegendsten Primär-Anker setzen; keine Liste/Multi-Anchor-Struktur in Phase 1 einführen.
- Falls gemeinsame Helper im Scoring-Bereich sinnvoll sind, nur im direkten Scope ergänzen und nicht gleich eine große Interface-Refaktorierung beginnen.

## Acceptance Criteria (deterministic)
1) `scanner/pipeline/scoring/breakout.py` liefert additive Felder:
   - `invalidation_anchor_price`
   - `invalidation_anchor_type`
   - `invalidation_derivable`

2) `scanner/pipeline/scoring/pullback.py` liefert additive Felder:
   - `invalidation_anchor_price`
   - `invalidation_anchor_type`
   - `invalidation_derivable`

3) `scanner/pipeline/scoring/reversal.py` liefert additive Felder:
   - `invalidation_anchor_price`
   - `invalidation_anchor_type`
   - `invalidation_derivable`

4) Wenn ein sinnvoller Anchor ableitbar ist, gilt:
   - `invalidation_derivable = true`
   - `invalidation_anchor_price` ist gesetzt
   - `invalidation_anchor_type` ist gesetzt

5) Wenn kein sinnvoller Anchor ableitbar ist, gilt:
   - `invalidation_derivable = false`
   - `invalidation_anchor_price` ist `None`/`null`
   - `invalidation_anchor_type` ist `None`/`null`

6) Dieses Ticket ändert **nicht** die operative Stop-Berechnung: ATR-basierter Stop bleibt Phase-1-Default.

7) Die neuen Felder sind deterministisch und bei identischem Input stabil.

8) Bestehende Score-Felder und Scorer-Verhalten bleiben kompatibel, soweit nicht direkt für die neuen Anchor-Felder erweitert.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (N/A, sofern keine neuen Config-Keys nötig sind; wenn doch, zentrale Defaults verwenden)
- **Config Invalid Value Handling:** ✅ (N/A, sofern keine neuen Config-Keys nötig sind; falls neue Keys nötig werden, klarer Fehler statt stiller Koerzierung)
- **Nullability / kein bool()-Coercion:** ✅ (AC #5; Tests für `None`/`null` statt impliziter Falsy-Logik)
- **Not-evaluated vs failed getrennt:** ✅ (fehlender Anchor ≠ negatives Setup)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A)
- **Deterministische Sortierung / Tie-breaker:** ✅ (N/A für Sortierung; Anchor-Ableitung selbst deterministisch)

## Tests (required if logic changes)
- Unit:
  - Breakout mit klar ableitbarem Breakout-Level liefert gültigen Anchor
  - Pullback mit klar ableitbarem EMA-/Support-Anker liefert gültigen Anchor
  - Reversal mit klar ableitbarem Base-/Reclaim-Anker liefert gültigen Anchor
  - Breakout/Pullback/Reversal ohne sinnvollen Anchor liefern `invalidation_derivable = false`
  - Ungültige Anchor-Werte werden nicht still durchgereicht
  - gleiche Eingabe => gleicher Anchor

- Integration:
  - Scorer-Outputs bleiben kompatibel mit bestehenden Konsumenten
  - ATR-Stop-Pfad aus PR-09 bleibt unberührt

- Golden fixture / verification:
  - Bestehende Golden-/Snapshot-Tests nur anpassen, wenn Scorer-Output-Form bewusst erweitert wird
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] ATR-basierter Stop bleibt operative Phase-1-Stop-Methode
- [ ] neue Felder sind additive Kontextfelder
- [ ] kein stilles Umschalten auf setup-basierte Stops
- [ ] fehlender Anchor ist kein negatives Setup-Urteil
- [ ] keine Decision-/BTC-/Output-Renderer-Logik in diesem Ticket
- [ ] deterministische Anchor-Ableitung

## Definition of Done (Codex must satisfy)
- [ ] Scorer gemäß Acceptance Criteria erweitert
- [ ] Tests gemäß Ticket ergänzt/angepasst
- [ ] Keine Scope-Überschreitung in Risk-Primärlogik oder Decision
- [ ] Additive, kompatible Output-Erweiterung umgesetzt
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
