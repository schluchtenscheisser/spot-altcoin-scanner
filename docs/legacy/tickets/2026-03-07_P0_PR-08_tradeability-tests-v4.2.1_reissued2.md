> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-08 Tradeability-Tests V4.2.1

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- PR-06 und PR-07 führen die neue Tradeability-Berechnung und das Tradeability-Gate ein.
- Dieses Ticket liefert das verpflichtende Testnetz für die neue Taxonomie und ihre Pipeline-Semantik.
- Es folgt `docs/tickets/_TEMPLATE.md` sowie `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`.

## Goal
Die neue Tradeability-Logik ist durch deterministische Unit-/Integrations-Tests so abgesichert, dass:
- `DIRECT_OK`, `TRANCHE_OK`, `MARGINAL`, `FAIL`, `UNKNOWN` eindeutig getrennt sind,
- Missing vs Invalid vs Not-Evaluated sauber behandelt wird,
- das Gate-Verhalten in der Pipeline reproduzierbar ist,
- Budget-/Missing-/Stale-Pfade explizit geprüft sind.

## Scope
- neue/angepasste Tests unter `tests/`
- ggf. neue Fixtures unter `tests/fixtures/`
- ggf. Golden-/Verification-Anpassungen nur soweit unbedingt nötig
- keine fachliche Erweiterung der Runtime-Logik über minimale Testability-Hooks hinaus

## Out of Scope
- Keine neue Tradeability-Fachlogik
- Keine neue Risk-/Decision-Logik
- Keine Output-Schema-Änderung
- Keine Shadow-/Migration-Änderung

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`
- `docs/canonical/OUTPUT_SCHEMA.md`

## Proposed change (high-level)
Before:
- Bestehende Tests decken die Phase-1-Tradeability-Taxonomie nicht vollständig ab.
- Budget-/Missing-/Stale-Pfade sind nicht sauber als eigene Statusfamilien verifiziert.

After:
- Es gibt ein deterministisches Testnetz für:
  - Taxonomie-Zuordnung
  - Missing vs Invalid
  - UNKNOWN vs FAIL
  - Gate-Verhalten in der Pipeline
  - deterministische Reason-Pfade
  - stabile Behandlung von stale/missing/not-in-budget

Edge cases:
- Orderbook fehlt vollständig
- Orderbook vorhanden, aber stale
- Symbol liegt außerhalb des Orderbook-Budgets
- 20k direct nicht handelbar, 4x5k tranchefähig
- knapp handelbar => `MARGINAL`
- negative/ungültige Slippage-/Depth-Werte => klarer Fehler, kein stilles Mapping

Backward compatibility impact:
- Keine Produktivlogik-Änderung beabsichtigt.
- Bestehende Tests können angepasst werden müssen, falls sie alte Bool-Semantik implizit voraussetzen.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Nur die kanonische Taxonomie ist maßgeblich.
- **UNKNOWN ≠ FAIL:** UNKNOWN steht für nicht evaluierbar / nicht belastbar bewertbar; FAIL steht für voll evaluiert und negativ.
- **MARGINAL ist voll evaluiert:** Nicht ENTER-fähig, aber kein UNKNOWN.
- **Missing ≠ Invalid:** Fehlender Key darf nur über definierte Defaults laufen; ungültige Werte müssen klar fehlschlagen.
- **Keine bool()-Koerzierung semantischer Zustände.**
- **Determinismus ist Pflicht:** identischer Input + identische Config => identische Klasse, identische Reasons.
- **Tests dürfen keine zweite Wahrheit erfinden:** Feldnamen/Enums nur gemäß Canonical verwenden.

## Implementation Notes (optional but useful)
Sinnvolle Testabdeckung:
1. reine Klassifikation auf Funktionsebene
2. Pipeline-/Gate-Ebene
3. Konfigurations- und Budgetpfade
4. Fehlerpfade für invaliden Input

Mögliche Testdateien:
- `tests/test_pr08_tradeability_taxonomy.py`
- `tests/test_pr08_tradeability_gate_pipeline.py`

## Acceptance Criteria (deterministic)
1) Es existieren Tests, die jede `tradeability_class` explizit abdecken:
   - `DIRECT_OK`
   - `TRANCHE_OK`
   - `MARGINAL`
   - `FAIL`
   - `UNKNOWN`

2) Es existiert mindestens ein Test, in dem ein Symbol `TRANCHE_OK` ist, obwohl `DIRECT_OK` für 20k nicht erfüllt ist.

3) Es existiert mindestens ein Test, in dem ein Symbol als `MARGINAL` klassifiziert wird und dadurch nicht ENTER-fähig ist.

4) Es existiert mindestens ein Test für `orderbook_data_missing` → `UNKNOWN`.

5) Es existiert mindestens ein Test für `orderbook_data_stale` → `UNKNOWN`.

6) Es existiert mindestens ein Test für `orderbook_not_in_budget` → `UNKNOWN`.

7) Es existiert mindestens ein Test, der verifiziert, dass `UNKNOWN` im Pipeline-Gate nicht als `WAIT` weitergereicht wird.

8) Es existiert mindestens ein Test, der verifiziert, dass `FAIL` nicht mit `UNKNOWN` zusammenfällt.

9) Fehlende Config-Keys nutzen definierte Defaults; ungültige Config-Werte erzeugen klare Fehler.

10) Bei identischem Input und identischer Config sind Klasse und Reason-Pfade deterministisch.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅
- **Config Invalid Value Handling:** ✅
- **Nullability / kein bool()-Coercion:** ✅
- **Not-evaluated vs failed getrennt:** ✅
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – Testticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A)
- **Deterministische Sortierung / Tie-breaker:** ✅ (soweit für Gate-/Reason-Determinismus relevant)

## Tests (required if logic changes)
- Unit:
  - DIRECT_OK
  - TRANCHE_OK
  - MARGINAL
  - FAIL
  - UNKNOWN missing/stale/not_in_budget
  - invalid config/value error paths
- Integration:
  - Gate stoppt UNKNOWN vor Decision
  - FAIL bleibt negativ bewertet
  - identischer Input => identischer Output
- Golden fixture / verification:
  - nur anpassen, wenn bestehende Golden-Files alte Bool-Semantik erzwingen

## Constraints / Invariants (must not change)
- [ ] Canonical Taxonomie bleibt maßgeblich
- [ ] UNKNOWN bleibt vom FAIL-Pfad getrennt
- [ ] MARGINAL bleibt voll evaluiert
- [ ] Keine neue Fachlogik außerhalb minimaler Testability-Hooks
- [ ] Keine Decision-/Risk-/Output-Scope-Erweiterung

## Definition of Done (Codex must satisfy)
- [ ] Tests gemäß Acceptance Criteria ergänzt
- [ ] Alle neuen Tests laufen grün
- [ ] Keine versteckte Semantik-Änderung außerhalb des Testscopes
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-07T00:00:00Z"
priority: P0
type: test
owner: codex
related_issues: []
```
