> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-16 Decision-Tests

## Context / Source
- Die aktuelle alleinige Referenz definiert in EPIC 7 / PR-16 die Testabsicherung der neuen Decision Layer.
- PR-15 führt `scanner/pipeline/decision.py` mit Statuslogik `ENTER / WAIT / NO_TRADE` ein.
- Die Master-Checkliste für codex-feste Tickets ist verbindlich, insbesondere für:
  - not-evaluated vs failed
  - nullable vs bool
  - deterministische Reason-Ausgabe
  - keine stillen Status-Kollisionen
- Die Decision Layer arbeitet nur auf Kandidaten, die das Tradeability Gate bereits passiert haben (`DIRECT_OK`, `TRANCHE_OK`, `MARGINAL`).

## Goal
Ein vollständiges, deterministisches Testnetz für die Decision Layer aufbauen, das sicherstellt:
- jeder Kandidat erhält exakt **einen** Status,
- Reason-Keys sind korrekt, vollständig und stabil,
- `UNKNOWN` erreicht die Decision Layer nicht,
- `risk_acceptable = null` / nicht evaluierbar wird nicht still zu `false` oder `WAIT` umgedeutet,
- BTC-Regime-Effekte werden korrekt auf die Schwellenlogik angewendet.

## Scope
- Tests unter `tests/` für `scanner/pipeline/decision.py`
- ggf. neue Testdatei wie:
  - `tests/test_decision_layer.py`
  - oder `tests/pipeline/test_decision_layer.py`
- ggf. Pipeline-nahe Integrationstests für:
  - Ausschluss von `UNKNOWN` vor Decision
  - Zusammenspiel aus Tradeability, Risk, Scorer-Flags und Decision

## Out of Scope
- Keine Runtime-Änderung der Decision-Logik selbst, außer minimal zwingende Test-Hooks
- Keine Änderung der Tradeability-, Risk- oder BTC-Regime-Implementierung
- Keine Output-/Renderer-Änderungen
- Keine zusätzliche Portfolio-Logik
- Keine Exit-/Hold-/Rotate-Logik
- Keine Kalibrierung oder Wahrscheinlichkeitslogik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/PIPELINE.md`

## Proposed change (high-level)
Before:
- Die Decision Layer kann fachlich implementiert sein, aber ohne vollständige Testabsicherung drohen Regressionsfehler bei:
  - Status-Priorität
  - Reason-Vergabe
  - BTC-Regime-Schwellen
  - nullable Risk-Feldern
  - Abgrenzung von WAIT vs NO_TRADE

After:
- Es existieren deterministische Tests für alle kanonischen Decision-Pfade:
  - `ENTER`
  - `WAIT`
  - `NO_TRADE`
- Es ist explizit abgesichert:
  - `DIRECT_OK` + `entry_ready` + `risk_acceptable = true` + ausreichender Score => `ENTER`
  - `TRANCHE_OK` kann ebenfalls `ENTER` werden
  - `MARGINAL` führt nicht zu `ENTER`
  - `entry_ready = false` bei ausreichendem Grundscore => `WAIT`
  - unattraktives Risk oder insuffiziente Risk-Daten => `NO_TRADE`
  - BTC-RISK_OFF kann `ENTER` zu `WAIT` degradieren
  - `UNKNOWN` erreicht die Decision Layer nicht

Edge cases:
- `risk_acceptable = null` bzw. Risk nicht evaluierbar => nicht `WAIT`, sondern `NO_TRADE`
- Kandidat mit mehreren potenziellen WAIT-Reasons => deterministische, stabile Reason-Menge
- Kandidat mit `MARGINAL` + sonst starkem Setup => `WAIT`, nicht `ENTER`
- Kandidat mit Score unter `min_score_for_wait` => `NO_TRADE`, auch wenn `entry_ready = false`
- harter Risk-Flag-Blocker => `NO_TRADE`
- BTC-RISK_OFF hebt nur Threshold an, blockiert aber nicht pauschal

Backward compatibility impact:
- Keine fachliche Runtime-Änderung beabsichtigt; Ticket erhöht/aktualisiert nur die Testschärfe.
- Bestehende Tests dürfen angepasst werden, wenn sie die alte oder unvollständige Statuslogik implizit widerspiegeln.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Tests müssen exakt die kanonischen Status und Reason-Keys abprüfen.
- **Exakt ein Status pro Kandidat:** Nie mehrere Status gleichzeitig, nie statuslos.
- **Nullable sauber behandeln:** Wenn `risk_acceptable` nicht belastbar evaluierbar ist, darf das nicht still als `false` oder als bloßer WAIT-Grund kollabieren.
- **UNKNOWN bleibt ausgeschlossen:** Die Decision-Tests dürfen nicht stillschweigend `UNKNOWN` innerhalb der Decision behandeln, außer explizit als Pipeline-Abwehrtest.
- **WAIT nur für voll evaluierte Kandidaten:** Nicht-evaluierbare Kandidaten sind nicht WAIT.
- **Reason-Determinismus ist Pflicht:** Bei identischem Input müssen Status und Reason-Menge identisch sein.
- **Keine implizite Bool-Koerzierung:** Keine Assertions, die nur truthiness prüfen, wenn tri-state oder nullability fachlich relevant ist.
- **BTC-Regime nur als Schwellenmodifikator testen:** Kein pauschaler Blocker, keine erfundene Setup-Typ-Sonderlogik.
- **Kein Scope-Drift:** Dieses Ticket schreibt keine neue Runtime-Semantik, sondern testet die definierte.

## Implementation Notes (optional but useful)
- Prüfe bestehende Tests im Umfeld von:
  - Decision / pipeline / scoring / regime
- Wenn keine saubere vorhandene Testdatei passt, ist eine neue dedizierte Datei für Decision-Tests vorzuziehen.
- Für Integrationstests:
  - Inputs klein und vollständig synthetisch halten
  - keine echten API-/Netzwerkzugriffe
  - BTC-Regime ggf. per Fixture oder Monkeypatch einspeisen
- Wenn Reason-Reihenfolge kanonisch nicht fest vorgegeben ist, auf deterministische Mengenvergleichslogik achten; wenn Reihenfolge kanonisch festgelegt ist, exakt prüfen.

## Acceptance Criteria (deterministic)
1) Es existieren explizite Tests für `ENTER` bei:
   - `tradeability_class = DIRECT_OK`
   - `entry_ready = true`
   - `risk_acceptable = true`
   - `setup_score >= effective_min_score`

2) Es existieren explizite Tests für `ENTER` bei:
   - `tradeability_class = TRANCHE_OK`
   - `entry_ready = true`
   - `risk_acceptable = true`
   - `setup_score >= effective_min_score`

3) Es existieren explizite Tests für `WAIT`, wenn:
   - `entry_ready = false`
   - `setup_score >= min_score_for_wait`
   - Kandidat voll evaluierbar ist

4) Es existieren explizite Tests für `WAIT` bei:
   - `tradeability_class = MARGINAL`

5) Es existieren explizite Tests für `WAIT`, wenn:
   - Kandidat unter RISK_OFF wegen angehobener Schwelle nicht mehr `ENTER` wäre,
   - aber unter NEUTRAL `ENTER` wäre,
   - Reason enthält `btc_regime_caution`

6) Es existieren explizite Tests für `NO_TRADE`, wenn:
   - `risk_acceptable = false`

7) Es existieren explizite Tests für `NO_TRADE`, wenn:
   - Risk-Daten nicht belastbar evaluierbar sind
   - und der kanonische Reason dafür gesetzt wird (z. B. `risk_data_insufficient`)

8) Es existieren explizite Tests für `NO_TRADE`, wenn:
   - `setup_score < min_score_for_wait`

9) Es existieren explizite Tests für `NO_TRADE`, wenn:
   - harter Risk-Flag-Blocker aktiv ist

10) Es existiert ein Integrationstest, der absichert:
   - `UNKNOWN`-Kandidaten erreichen die Decision Layer nicht

11) Jeder geprüfte Kandidat hat genau einen Status und mindestens einen Reason-Key.

12) Bei identischem Input und identischer Config sind Status und Reason-Ausgabe deterministisch.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (Test: fehlende Decision-/BTC-Regime-Schwellen greifen über zentrale Defaults)
- **Config Invalid Value Handling:** ✅ (Test: ungültige Decision-Schwellen oder BTC-Regime-Boost-Werte führen zu klarem Fehler, nicht zu stiller Koerzierung)
- **Nullability / kein bool()-Coercion:** ✅ (Test: `risk_acceptable = null` bleibt semantisch „nicht evaluierbar“ und wird nicht still zu `false` oder `WAIT`)
- **Not-evaluated vs failed getrennt:** ✅ (Test: insuffiziente Risk-Daten vs fachlich negatives Risk getrennt)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A)
- **Deterministische Sortierung / Tie-breaker:** ✅ (Test: identischer Input => identische Status-/Reason-Ausgabe)

## Tests (required if logic changes)
- Unit:
  - ENTER via DIRECT_OK
  - ENTER via TRANCHE_OK
  - WAIT bei `entry_ready = false`
  - WAIT bei `tradeability_class = MARGINAL`
  - WAIT bei BTC-RISK_OFF-Threshold-Boost
  - NO_TRADE bei `risk_acceptable = false`
  - NO_TRADE bei insuffizienten Risk-Daten
  - NO_TRADE bei Score unter `min_score_for_wait`
  - NO_TRADE bei hartem Risk-Flag-Blocker
  - jeder Kandidat hat exakt einen Status
  - mindestens ein Reason-Key vorhanden
  - Missing Key => zentraler Default
  - Invalid Value => klarer Fehler

- Integration:
  - `UNKNOWN` erreicht die Decision Layer nicht
  - identische Fixture + identische Config => identische Status/Reasons
  - keine Netzwerkzugriffe / kein externes IO

- Golden fixture / verification:
  - Nur anpassen, wenn bestehende Golden-/Snapshot-Tests eine ältere Decision-Semantik indirekt festhalten
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] Decision kennt nur `ENTER`, `WAIT`, `NO_TRADE`
- [ ] genau ein Status pro Kandidat
- [ ] WAIT nur für voll evaluierte Kandidaten
- [ ] UNKNOWN bleibt vor Decision ausgeschlossen
- [ ] BTC-Regime wirkt nur als Schwellenmodifikator
- [ ] keine Portfolio-/Exit-/Hold-Logik
- [ ] deterministische Reason-Ausgabe

## Definition of Done (Codex must satisfy)
- [ ] Tests gemäß Acceptance Criteria ergänzt/aktualisiert
- [ ] Nullability und not-evaluated-vs-failed explizit abgesichert
- [ ] Integrationstest für Ausschluss von UNKNOWN vorhanden
- [ ] Keine Runtime-Scope-Überschreitung in Risk/Output/BTC-Implementierung
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-08T00:00:00Z"
priority: P0
type: test
owner: codex
related_issues: []
```
