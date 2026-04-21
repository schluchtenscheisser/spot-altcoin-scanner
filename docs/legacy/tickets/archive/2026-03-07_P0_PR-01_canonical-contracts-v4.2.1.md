> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] Canonical Contracts V4.2.1 festziehen

## Context / Source
- V4.2.1 ist die alleinige Referenz für die Neuausrichtung.
- EPIC 1 / PR-01 verlangt, dass alle späteren PRs gegen eindeutige, stabile Verträge arbeiten.
- Aktuell sind Pipeline-, Tradeability-, Risk-, Decision- und Output-Semantik nicht vollständig als kanonische, widerspruchsfreie Source of Truth zusammengezogen.

## Goal
Die kanonischen Dokumente unter `docs/canonical/` definieren die neue Zielarchitektur vollständig und widerspruchsfrei, sodass nachfolgende Tickets keine Kernsemantik mehr interpretieren müssen.

## Scope
Erstellen/ändern der folgenden kanonischen Dokumente:

- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`
- `docs/canonical/CHANGELOG.md` oder bestehende kanonische Stelle für `canonical_schema_version`-Pflege
- falls erforderlich: bestehende kanonische Querverweise aktualisieren, damit keine widersprüchlichen Altdefinitionen verbleiben

## Out of Scope
- Keine Codeänderungen in `scanner/`
- Keine Config-Implementierung
- Keine Pipeline- oder Output-Implementierung
- Keine Tests/Fixtures, außer falls ein kanonisches Verifikationsdokument explizit wegen Dokumentlogik angepasst werden muss
- Keine Legacy-Dokumente als Autorität umschreiben
- Keine neue Portfolio-Logik, Exit-/Hold-/Rotate-Logik oder Kalibrierungslogik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`

## Proposed change (high-level)
Before:
- Kernsemantik ist über mehrere Dokumente und historische Zwischenstände verteilt.
- Nicht alle neuen Begriffe und Regeln der V4.2.1 sind als kanonische Verträge festgezogen.
- Es besteht Drift-Risiko für Folge-PRs, insbesondere bei UNKNOWN-Pfad, MARGINAL-Semantik, Score-Rollen, Risk-Blockern und Output-SoT.

After:
- Die neuen kanonischen Dokumente definieren die Phase-1-Zielarchitektur vollständig.
- Pipeline-Reihenfolge, Tradeability-Taxonomie, Risk-/Downside-Semantik, Decision-Logik, Output-SoT und Budget-/Pool-Modell sind eindeutig spezifiziert.
- `setup_score` und `global_score` sind explizit getrennt.
- UNKNOWN ist widerspruchsfrei definiert: kein WAIT, kein ENTER, kein Durchreichen in die Decision Layer.
- `MARGINAL` ist explizit als nicht ENTER-fähig definiert.
- Risk-Flag-Blocker verweisen auf autoritative Quellen im Repo.
- `canonical_schema_version` ist als Semver-Regel dokumentiert.

Edge cases:
- UNKNOWN vs FAIL vs NOT-EVALUATED sauber trennen
- `orderbook_data_missing`, `orderbook_data_stale`, `orderbook_not_in_budget` semantisch sauber abgrenzen
- `pre_shortlist_market_cap_floor_usd` als harter Pool-Guardrail, nicht als Soft-Prior
- `TP10` / `TP20` sind Orientierungsziele, keine verpflichtende Exit-Logik
- Reversal ohne Reclaim ist nicht entry-ready
- Directional Volume ist architektonisch vorbereitbar, aber nicht Teil von Phase 1

Backward compatibility impact:
- Rein dokumentarische Änderung, aber mit bewusstem kanonischem Vorrang.
- Bestehende nicht-kanonische/legacy Beschreibungen können dadurch fachlich überholt sein.
- Nachfolgende PRs müssen sich an diese Spezifikation halten; bei Widerspruch zählt Canonical.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
> Dieses Ticket ist ein Docs-/Canonical-Ticket. Es definiert Verträge für Folge-PRs. Wenn ein Punkt nicht eindeutig formulierbar ist, muss das Ticket ergänzt werden statt eine fuzzy Formulierung zu wählen.

- **Canonical first:** Nur `docs/canonical/*` ist autoritativ. Keine legacy oder Autodocs als Wahrheitsquelle verwenden.
- **Keine stillen Interpretationen:** Wenn V4.2.1 einen Begriff oder Default nennt, muss er explizit im Canonical landen.
- **UNKNOWN klar trennen:** `UNKNOWN` bedeutet nicht evaluiert / nicht weiter evaluierbar; es ist weder `WAIT` noch `FAIL`.
- **MARGINAL klar trennen:** `MARGINAL` ist voll evaluiert, aber nicht ENTER-fähig.
- **Score-Rollen trennen:** `setup_score` = Decision-Schwelle; `global_score` = Priorisierung/Kontext.
- **Risk-Blocker referenzieren:** Autoritative Quellen müssen explizit genannt werden, nicht nur „Risk Flag“ als Sammelbegriff.
- **Semver-Regel dokumentieren:** `canonical_schema_version` muss dokumentiert sein mit Inkrementierungslogik.
- **Keine Portfolio-Logik hineinschreiben:** Phase 1 bleibt Signal-/Decision-System, kein Portfolio-Manager.
- **Keine Exit-Logik hineininterpretieren:** TP10/TP20 sind Orientierungsziele, keine verpflichtenden Exits.
- **Determinismus dokumentieren:** Wo Reihenfolgen, Tie-Breaker oder Statuspfade relevant sind, explizit festschreiben.

## Implementation Notes (optional but useful)
Die neuen/aktualisierten Canonical Docs müssen mindestens folgende Inhalte festziehen:

1. **PIPELINE.md**
   - Zielreihenfolge der Pipeline in Phase 1
   - frühe Pool-Öffnung mit Budget-Shortlist
   - UNKNOWN-Stopp vor Decision Layer
   - Shadow-Mode/Migration nur referenzieren, nicht voll implementieren

2. **LIQUIDITY/TRADEABILITY_GATE.md**
   - `tradeability_class ∈ {DIRECT_OK, TRANCHE_OK, MARGINAL, FAIL, UNKNOWN}`
   - `UNKNOWN`-Reason-Familie:
     - `tradeability_unknown`
     - `orderbook_data_missing`
     - `orderbook_data_stale`
     - `orderbook_not_in_budget`
   - `MARGINAL` = kein ENTER möglich
   - `DIRECT_OK` / `TRANCHE_OK` / `FAIL` / `UNKNOWN` semantisch sauber trennen

3. **RISK_MODEL.md**
   - ATR-basierter Stop als Phase-1-Default
   - `stop_price_initial`
   - `risk_pct_to_stop`
   - `rr_to_tp10`
   - `rr_to_tp20`
   - `risk_acceptable`
   - Setup-basierte Stops nur als spätere Erweiterung / Kontext

4. **DECISION_LAYER.md**
   - `decision ∈ {ENTER, WAIT, NO_TRADE}`
   - `WAIT` nur für voll evaluierte Coins
   - UNKNOWN erreicht die Decision Layer nicht
   - `ENTER` braucht mindestens:
     - evaluierbare Tradeability
     - entry-ready
     - akzeptables Risk
     - ausreichenden `setup_score`
   - `global_score` nur als Priorisierung innerhalb der Kandidaten, nicht als primäre Decision-Wahrheit

5. **OUTPUT_SCHEMA.md**
   - `trade_candidates` als SoT
   - Pflichtfelder und Nullable-Regeln
   - `decision_reasons`
   - Trennung von `trade_candidates` vs separatem Run Manifest
   - keine Format-spezifische abweichende Wahrheit

6. **BUDGET_AND_POOL_MODEL.md**
   - `shortlist_size`
   - `orderbook_top_k`
   - `pre_shortlist_market_cap_floor_usd`
   - Soft-Priors vs harte Pool-Guardrails
   - operative Begründung für frühe Filter-Lockerung

7. **CHANGELOG / canonical_schema_version**
   - Semver-Regel
   - wann Major/Minor/Patch erhöht wird
   - manuell gepflegt

## Acceptance Criteria (deterministic)
1) Die folgenden kanonischen Dokumente existieren oder sind aktualisiert und widerspruchsfrei:
   - `PIPELINE.md`
   - `OUTPUT_SCHEMA.md`
   - `DECISION_LAYER.md`
   - `RISK_MODEL.md`
   - `LIQUIDITY/TRADEABILITY_GATE.md`
   - `BUDGET_AND_POOL_MODEL.md`

2) `PIPELINE.md` dokumentiert die Phase-1-Pipeline so, dass UNKNOWN-Kandidaten vor der Decision Layer gestoppt werden.

3) `TRADEABILITY_GATE.md` definiert `tradeability_class` explizit als:
   - `DIRECT_OK`
   - `TRANCHE_OK`
   - `MARGINAL`
   - `FAIL`
   - `UNKNOWN`

4) `TRADEABILITY_GATE.md` dokumentiert explizit:
   - `MARGINAL` ist nicht ENTER-fähig
   - `UNKNOWN` ist nicht WAIT-fähig
   - `UNKNOWN` ist nicht FAIL
   - `orderbook_data_missing`, `orderbook_data_stale`, `orderbook_not_in_budget` sind getrennte Reason-Pfade

5) `RISK_MODEL.md` dokumentiert den Phase-1-Stop als ATR-basierten Default und definiert mindestens:
   - `stop_price_initial`
   - `risk_pct_to_stop`
   - `rr_to_tp10`
   - `rr_to_tp20`
   - `risk_acceptable`

6) `DECISION_LAYER.md` definiert explizit:
   - `setup_score` steuert ENTER/WAIT-Schwellen
   - `global_score` dient nur der Priorisierung/Kontext
   - `WAIT` gilt nur für voll evaluierte Coins
   - UNKNOWN-Coins erreichen die Decision Layer nicht

7) `OUTPUT_SCHEMA.md` definiert `trade_candidates` als kanonische SoT und dokumentiert Nullable-Regeln für alle neu eingeführten Felder, bei denen `null` semantisch relevant sein kann.

8) `BUDGET_AND_POOL_MODEL.md` dokumentiert explizit:
   - `pre_shortlist_market_cap_floor_usd` ist ein harter Pool-Guardrail
   - es ist kein Soft-Prior
   - frühe Filter-Lockerung wird über Budget-Shortlist kontrolliert

9) Die autoritativen Risk-Flag-Blocker sind explizit referenziert:
   - `config/denylist.yaml`
   - `config/unlock_overrides.yaml`
   - `filters.py._apply_risk_flags()`

10) `canonical_schema_version` ist als Semver dokumentiert, inklusive Inkrementierungsregeln und kanonischer Ablage.

11) Kein kanonisches Dokument enthält Aussagen, die Portfolio-Management, Exit-/Hold-Logik oder automatische Kalibrierung als Phase-1-Bestandteil definieren.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
> Dieses Ticket ist primär ein Docs-/Canonical-Ticket. Relevanz daher pro Punkt explizit markiert.

- **Config Defaults (Missing key → Default):** ✅ (N/A — Ticket liest keine Runtime-Config; dokumentiert nur kanonische Defaults)
- **Config Invalid Value Handling:** ✅ (N/A — Ticket implementiert keine Validierung; Canonical darf aber keine widersprüchlichen Werte definieren)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #7)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #3, #4, #6)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A — kein Datei-Namensgenerator)
- **Deterministische Sortierung / Tie-breaker:** ✅ (AC: #2, #6; soweit in Canonical relevant)

## Tests (required if logic changes)
- Unit:
  - N/A für Runtime-Code
- Integration:
  - N/A für Runtime-Code
- Golden fixture / verification:
  - Prüfe manuell bzw. im PR-Review, dass kein Widerspruch zwischen den genannten Canonical Docs verbleibt
  - Falls ein bestehendes kanonisches Verifikationsdokument diese Semantik widerspiegelt, entsprechend aktualisieren
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] `docs/canonical/AUTHORITY.md` bleibt maßgeblich
- [ ] Keine Legacy-Doku wird als Autorität verwendet
- [ ] Keine Runtime-Logik wird in diesem Ticket implementiert
- [ ] Keine stillen Phase-1-Erweiterungen für Portfolio-/Exit-/Hold-Logik
- [ ] UNKNOWN bleibt ein Stopp-Pfad vor Decision
- [ ] `setup_score` und `global_score` bleiben fachlich getrennt
- [ ] `trade_candidates` bleibt das vorgesehene Output-SoT der Neuausrichtung

## Definition of Done (Codex must satisfy)
- [ ] Kanonische Dokumente gemäß Acceptance Criteria erstellt/aktualisiert
- [ ] Keine Widersprüche zwischen Pipeline-, Tradeability-, Risk-, Decision- und Output-Dokumenten
- [ ] `canonical_schema_version` dokumentiert
- [ ] Keine Runtime-Codeänderung in diesem PR
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket wird nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-07T00:00:00Z"
priority: P0
type: docs
owner: codex
related_issues: []
```
