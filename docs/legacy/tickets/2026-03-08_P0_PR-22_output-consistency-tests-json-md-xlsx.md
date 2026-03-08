> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-22 Output-Consistency-Tests für JSON / Markdown / Excel

## Context / Source
- Die aktuelle alleinige Referenz verlangt `trade_candidates` als kanonische Output-Source-of-Truth.
- Nach PR-18 bis PR-21 existieren bzw. entstehen mehrere Output-Kanäle:
  - JSON (`trade_candidates`)
  - Run Manifest
  - Markdown-Rendering
  - Excel-Rendering
- Dieses Ticket stellt sicher, dass Markdown und Excel keine zweite Wahrheit aufbauen und dass formatübergreifend dieselben Inhalte aus derselben kanonischen Basis stammen.
- Die neuen verbindlichen Ticket-Regeln gelten vollumfänglich, insbesondere:
  - Canonical first
  - Determinismus
  - keine stillen Fallbacks
  - Nullability explizit
  - konkrete Testfälle statt nur Kategorien

## Goal
Ein belastbares Testnetz für die Output-Konsistenz aufbauen, das sicherstellt:

- `trade_candidates` bleibt die einzige fachliche Wahrheit
- Markdown und Excel rendern konsistent aus derselben SoT
- Pflichtfelder, Nullability und semantische Unterschiede bleiben formatübergreifend korrekt
- identischer Input erzeugt deterministisch konsistente Artefakte

## Scope
- Tests unter `tests/` für:
  - JSON ↔ Markdown Konsistenz
  - JSON ↔ Excel Konsistenz
  - Pflichtfeldabdeckung
  - Nullability-/Reason-/Status-Konsistenz
  - deterministische Reihenfolge / Sortierung
- Falls nötig:
  - kleine Testfixtures / Golden Fixtures
  - testnahe Hilfsfunktionen
- Falls erforderlich:
  - minimale Korrekturen in Test-Utilities, aber keine fachliche Produktionslogik

## Out of Scope
- Keine neue Output-Produktionslogik
- Keine Änderung der Decision-Layer-Semantik
- Keine Änderung von Risk-, Tradeability- oder BTC-Regime-Logik
- Keine Änderung der JSON-SoT-Struktur selbst
- Keine Änderung an Canonical Docs
- Kein Umbau des Run Manifests außerhalb klarer Testanpassungen

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`

## Proposed change (high-level)
Before:
- JSON, Markdown und Excel können nach Implementierung in benachbarten PRs formal vorhanden sein, ohne dass ihre inhaltliche Gleichheit und SoT-Treue testseitig hart abgesichert ist.
- Dadurch besteht Drift-Risiko bei:
  - fehlenden Pflichtfeldern
  - unterschiedlicher Sortierung
  - wegfallenden Reason Keys
  - falscher Behandlung von `null`
  - impliziten Format-spezifischen Defaults

After:
- Tests sichern explizit ab:
  - Markdown und Excel leiten ihre fachlichen Inhalte ausschließlich aus `trade_candidates` ab
  - dieselben Kandidaten, Decisions, Reasons und Kernfelder erscheinen formatübergreifend konsistent
  - `null` bleibt semantisch korrekt und kollabiert nicht still zu leerem String / `false` / `0`
  - Sortierung und Priorisierung sind deterministisch
  - Pflichtfelder bleiben vollständig

Edge cases:
- `risk_acceptable = null`
- `rr_to_tp10 = null`
- `tradeability_class = UNKNOWN` darf in Output-Kontexten nur so auftauchen, wie es der kanonische Output erlaubt
- leere Candidate-Liste
- mehrere `ENTER`-Kandidaten mit gleichem `global_score`
- Unicode / Sonderzeichen in Reason Keys oder Textfeldern
- optionale Felder fehlen nicht, sondern sind explizit `null`, wenn semantisch vorgesehen

Backward compatibility impact:
- Keine neue Fachlogik; Ticket erhöht die Testschärfe.
- Bestehende Golden-/Snapshot-Tests dürfen angepasst werden, wenn sie die neue SoT-Struktur oder Sortierregeln noch nicht korrekt spiegeln.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** `trade_candidates` ist die einzige fachliche Source of Truth.
- **Keine zweite Wahrheit:** Markdown und Excel dürfen nichts fachlich Eigenständiges berechnen oder umdeuten.
- **Nullability explizit:** `null`-Felder dürfen nicht still zu `false`, `0`, `""` oder „nicht vorhanden“ kollabieren, wenn Canonical `null` semantisch verlangt.
- **Determinismus ist Pflicht:** gleicher JSON-Input => inhaltlich gleiche gerenderte Outputs.
- **Tie-Breaker nicht erfinden:** wenn Sortierung aus Upstream kommt, Tests müssen genau diese Ordnung prüfen und keine neue implizite Ordnung verlangen.
- **Missing vs invalid getrennt:** fehlendes Pflichtfeld in `trade_candidates` ist ein Fehler; optionales `null` ist kein Fehler.
- **Nicht-evaluiert vs negativ nicht verwischen:** z. B. `risk_acceptable = null` darf nicht als `false` interpretiert werden.
- **Formatunterschiede nur Darstellung, nie Fachlogik:** unterschiedliche Spaltennamen/Überschriften sind okay, semantische Abweichung nicht.

## Implementation Notes (optional but useful)
- Wahrscheinlich betroffene Testbereiche:
  - Output-/Renderer-Tests
  - JSON-/Snapshot-/Golden-Tests
- Falls Markdown und Excel unterschiedlich rendern dürfen, muss der Test auf semantische Gleichheit prüfen, nicht auf byte-identische Darstellung.
- Für Excel kann ein Parser oder strukturierter Reader im Test sinnvoll sein, statt Binärvergleich.
- Für Markdown sollten relevante semantische Zeilen/Tabellenwerte geprüft werden, nicht fragiles Whitespace-Matching.

## Acceptance Criteria (deterministic)
1) Es existieren Tests, die sicherstellen, dass Markdown ausschließlich auf Basis von `trade_candidates` gerendert wird.

2) Es existieren Tests, die sicherstellen, dass Excel ausschließlich auf Basis von `trade_candidates` gerendert wird.

3) Ein Test prüft, dass dieselben Kandidaten mit denselben Kernfeldern in JSON, Markdown und Excel konsistent erscheinen.

4) Ein Test prüft, dass Pflichtfelder aus `trade_candidates` in allen relevanten Outputs vorhanden bzw. korrekt dargestellt sind.

5) Ein Test prüft, dass `null`-Werte semantisch korrekt behandelt werden und nicht still zu `false`, `0`, `""` oder fehlenden Einträgen kollabieren, sofern Canonical `null` vorsieht.

6) Ein Test prüft, dass Decision-/Reason-Felder formatübergreifend konsistent bleiben.

7) Ein Test prüft deterministische Reihenfolge / Priorisierung bei identischem Input.

8) Leere Candidate-Listen werden in allen relevanten Outputs deterministisch und ohne Fehler behandelt.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (N/A für Kernlogik; Test darf aber keine stillen Renderer-Defaults als Fachlogik akzeptieren)
- **Config Invalid Value Handling:** ✅ (N/A, außer Renderer-Konfiguration existiert explizit; dann klarer Fehler statt stiller Umdeutung)
- **Nullability / kein bool()-Coercion:** ✅ (`null`-Felder explizit prüfen)
- **Not-evaluated vs failed getrennt:** ✅ (z. B. `risk_acceptable = null` vs `false`)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (Testen, dass Renderer bei invalidem Pflichtinput nicht halb-konsistente Artefakte behaupten)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (falls Output-Dateinamen Teil des Renderings sind, deterministisch prüfen)
- **Deterministische Sortierung / Tie-breaker:** ✅ (expliziter Test)

## Tests (required if logic changes)
- Unit:
  - Pflichtfelder in JSON-SoT vorhanden
  - semantische Abbildung von Decision / Reasons nach Markdown
  - semantische Abbildung von Decision / Reasons nach Excel
  - `null`-Felder bleiben semantisch korrekt
  - leere Candidate-Liste wird korrekt behandelt

- Integration:
  - ein vollständiger `trade_candidates`-Fixture wird nach JSON / Markdown / Excel gerendert
  - Kandidaten, Reasons, Decisions und Kern-Risk-/Tradeability-Felder bleiben konsistent
  - deterministische Reihenfolge bleibt erhalten

- Golden fixture / verification:
  - nur dort aktualisieren, wo bestehende Golden-Files nicht die kanonische SoT widerspiegeln
  - keine unnötigen kosmetischen Golden-Änderungen

## Constraints / Invariants (must not change)
- [ ] `trade_candidates` bleibt die einzige fachliche SoT
- [ ] keine zweite Wahrheit in Markdown oder Excel
- [ ] `null` bleibt semantisch unterscheidbar
- [ ] Determinismus bleibt erhalten
- [ ] keine Scope-Erweiterung in Decision / Risk / Tradeability / BTC

## Definition of Done (Codex must satisfy)
- [ ] Tests gemäß Acceptance Criteria implementiert oder angepasst
- [ ] Output-Konsistenz über JSON / Markdown / Excel abgesichert
- [ ] `null`-Semantik explizit getestet
- [ ] Deterministische Reihenfolge getestet
- [ ] keine Scope-Überschreitung in Produktionslogik
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
