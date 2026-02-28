> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Canonical: MODEL_E2 Reason Codes erweitern + Precedence definieren

## Context / Source (optional)
- Roadmap: LowCost Automation / Evaluation Outcomes
- Aktueller Ist-Stand: docs/canonical/BACKTEST/MODEL_E2.md (Reason Codes nur: ok/no_trigger/insufficient_forward_history)
- Ziel: Tool wird schrittweise verbessert; Canonical muss vor Implementierung aktualisiert werden.

## Goal
Erweitere die Canonical Spec von MODEL_E2 um zusätzliche Reason Codes und eine eindeutige Precedence/Validitätsdefinition, damit Implementierung (E2-Model + Dataset Export) strikt daran ausgerichtet werden kann.

## Scope
- docs/canonical/BACKTEST/MODEL_E2.md

## Out of Scope
- Code-Implementierung des E2-Modells
- Dataset Exporter
- Snapshot-Änderungen

## Canonical References (important)
- docs/canonical/BACKTEST/MODEL_E2.md

## Proposed change (high-level)
Before:
- reason ∈ { ok, no_trigger, insufficient_forward_history }

After:
1) Reason Codes erweitern (canonical):
- ok
- no_trigger
- insufficient_forward_history
- missing_price_series
- invalid_entry_price
- missing_trade_levels
- invalid_trade_levels

2) Canonical Precedence (ein Feld `reason`, genau ein Wert):
1. missing_price_series  
2. invalid_entry_price  
3. missing_trade_levels  
4. invalid_trade_levels  
5. no_trigger  
6. insufficient_forward_history  
7. ok

3) Canonical Semantik (präzise, deterministisch):
- missing_price_series:
  - gilt für Trigger-Suche (t0..t0+T_trigger_max) wenn es *keinen einzigen* evaluierbaren Tag mit numerischem `close` gibt (oder Serie leer).
  - einzelne Lücken im Suchfenster sind erlaubt und werden übersprungen.
- invalid_entry_price:
  - entry_price ist null oder <= 0 (nach Bestimmung der Entry-Regel).
- missing_trade_levels / invalid_trade_levels (setup-typ-spezifisch):
  - breakout: benötigt `trade_levels.entry_trigger` (numeric>0) ODER `trade_levels.breakout_level_20` (numeric>0)
  - reversal: benötigt `trade_levels.entry_trigger` (numeric>0)
  - pullback: benötigt `trade_levels.entry_zone.lower` und `trade_levels.entry_zone.upper` (beide numeric>0 und lower<=upper)
  - missing_* wenn benötigtes Feld fehlt; invalid_* wenn vorhanden aber null/nicht numerisch/<=0/inkonsistent.
- insufficient_forward_history:
  - Forward/Hold-Window ist strict: es müssen für *alle* Tage t_trigger+1..t_trigger+T_hold gültige High/Low vorhanden sein.
  - Wenn irgendein Tag fehlt oder High/Low fehlt: insufficient_forward_history.
- no_trigger:
  - Trigger-Suche lief (ohne missing_* / invalid_*), aber kein Trigger innerhalb T_trigger_max gefunden.
- ok:
  - Trigger gefunden + Forward history vollständig gemäß rule above.

Backward compatibility impact:
- Erweiterung von enumerierten reason values; downstream darf zusätzliche Werte sehen.
- Bestehende drei Werte bleiben unverändert.

## Implementation Notes (optional but useful)
- Canonical Spec muss explizit die Trigger-Suche (t0..t0+T_trigger_max) vs Hold-Window (strict) abgrenzen.
- No-lookahead bleibt invariant.

## Acceptance Criteria (deterministic)
1) docs/canonical/BACKTEST/MODEL_E2.md enthält exakt die neuen Reason Codes (oben) als canonical Werte.
2) docs/canonical/BACKTEST/MODEL_E2.md enthält die Precedence-Reihenfolge (oben) als normative Regel.
3) docs/canonical/BACKTEST/MODEL_E2.md enthält die setup-typ-spezifischen Trade-Level Mindestanforderungen inkl. missing vs invalid Definition.
4) docs/canonical/BACKTEST/MODEL_E2.md beschreibt missing_price_series tolerant im Trigger-Suchfenster und insufficient_forward_history strict im Hold-Window.

## Tests (required if logic changes)
- Docs-only Ticket: keine Code-Tests.
- Reviewer-Check: alle Regeln sind eindeutig (keine Heuristik-Wörter wie “usually”, “roughly”, “best effort”).

## Constraints / Invariants (must not change)
- Closed-candle-only
- No lookahead
- Determinismus (stable ordering, klare Regeln)

## Definition of Done (Codex must satisfy)
(Reference: docs/canonical/WORKFLOW_CODEX.md)
- [ ] Canonical Doc aktualisiert gemäß Acceptance Criteria
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR nach docs/legacy/tickets/ verschoben

---
## Metadata (optional)
```yaml
created_utc: "2026-02-27T00:00:00Z"
priority: P0
type: docs
owner: codex
related_issues: []
```
