> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-05 Tests für Pool/Budget-Verhalten V4.2.1

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- EPIC 3 / PR-05 verlangt ein explizites Testnetz für den frühen geöffneten Pool und die budgetierte Shortlist.
- PR-03 und PR-04 ändern die frühe Filter- und Shortlist-Semantik. Dieses Ticket zieht die deterministischen Tests dafür nach.
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md` ist verbindlich: Das Ticket muss Missing-vs-Invalid, not-evaluated-vs-failed, Determinismus, Canonical-Konsistenz und Repo-Realität explizit abdecken.

## Goal
Ein belastbares Testnetz für EPIC 3 aufbauen bzw. anpassen, das nach PR-03 und PR-04 deterministisch absichert:

- harte Safety-/Risk-Excludes greifen weiter,
- `pre_shortlist_market_cap_floor_usd` greift hart,
- der Pool ist oberhalb des Floors geöffnet,
- die Shortlist bleibt budgetiert,
- die Auswahl bleibt reproduzierbar.

## Scope
- Testdateien unter `tests/`
- bestehende Tests anpassen, falls sie alte Hard-Gate-Semantik oder alte Shortlist-Caps fest verdrahten
- neue gezielte Unit-/Integration-Tests für:
  - Filter-Pool-Verhalten
  - Shortlist-Cap
  - Determinismus
  - Budget-/Floor-Interaktion

### Wahrscheinliche betroffene Testdateien
- `tests/test_volume_gates_config_and_filters.py`
- `tests/test_t82_topk_budget.py`
- ggf. neue dedizierte Testdatei für V4.2.1 Pool-/Budget-Verhalten, wenn bestehende Dateien semantisch unpassend zugeschnitten sind

## Out of Scope
- Keine Produktionscode-Änderung in `scanner/`, außer minimale Test-Hooks/Imports, falls technisch zwingend
- Keine neue Filter-/Shortlist-Logik
- Keine Tradeability-, Risk-, Decision- oder Output-Tests
- Keine Canonical-Dokumente ändern
- Keine Golden-/Backtest-Updates außerhalb der direkt betroffenen Pool-/Budget-Tests
- Kein stilles Uminterpretieren früherer Tickets; falls zusätzliche Korrekturen nötig wären, eigenes Follow-up-Ticket statt Scope-Drift

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/tickets/_TEMPLATE.md`
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`

## Proposed change (high-level)
Before:
- Bestehende Tests spiegeln teilweise die alte Hard-Gate-/Budget-Welt wider oder decken die neue V4.2.1-Semantik nicht vollständig ab.
- Es fehlt ein explizites Testbündel, das frühe Pool-Öffnung + harten Floor + deterministische Budget-Shortlist gemeinsam absichert.

After:
- Tests sichern explizit ab:
  - `shortlist_size`-Cap wird strikt eingehalten
  - Coins unter `pre_shortlist_market_cap_floor_usd` werden nicht shortgelistet
  - Coins über altem `market_cap.max_usd` können jetzt shortgelistet werden
  - Safety-Excludes und harte Risk-Blocker greifen weiterhin
  - identischer Input + identische Config => identische Filter-/Shortlist-Ergebnisse
- Alte Tests, die bewusst die frühere Hard-Gate-Semantik erwarteten, sind entweder angepasst oder klar ersetzt.
- EPIC 3 ist testseitig reproduzierbar abgesichert.

Edge cases:
- weniger zulässige Kandidaten als `shortlist_size`
- mehr zulässige Kandidaten als `shortlist_size`
- identische Cheap-Pass-Scores / Tie-Breaker
- Coin oberhalb des Floors, aber mit sehr schwachen Aktivitätsmetriken => darf im Pool bleiben
- Coin unter Floor mit sonst starken Kennzahlen => darf nicht in die Shortlist
- Denylist-/Risk-Flag-/Stable-/Wrapped-/Leveraged-Cases bleiben hart ausgeschlossen

Backward compatibility impact:
- Tests dürfen bewusst brechen, wenn sie die alte Hard-Gate-Welt fest eincodiert hatten.
- Nach dem PR muss die Testsuite die V4.2.1-Semantik reflektieren, nicht den Altzustand.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Testerwartungen müssen V4.2.1 + Canonical widerspiegeln, nicht historische Defaults.
- **Ein PR, ein Fokus:** Dieses Ticket testet nur EPIC 3 (Pool/Budget-Verhalten). Keine Vorwegnahme von Tradeability-/Decision-Tests.
- **Repo-Realität beachten:** Bestehende Testdateien nur dann erweitern, wenn ihr Zuschnitt fachlich passt; sonst neue dedizierte Datei anlegen.
- **Missing vs invalid trennen:** Tests müssen explizit unterscheiden zwischen fehlendem Config-Key (Default) und ungültigem Wert (Fehler).
- **Not-evaluated vs failed trennen:** Nicht-shortgelistet wegen Floor/Budget ist kein „failed tradeability“-Fall; diese Semantik darf in den Tests nicht verwischt werden.
- **Determinismus explizit prüfen:** Keine fuzzy Erwartung wie „ähnliche Auswahl“; Auswahl und Reihenfolge müssen bei identischem Input identisch sein.
- **Keine stillen Alias-Namen einführen:** Verwende `pre_shortlist_market_cap_floor_usd`, nicht alte oder freie Varianten.
- **Keine implizite bool()-Koerzierung semantischer Zustände.**
- **Keine Anpassung bestehender Tickets durch stilles Uminterpretieren:** Wenn ein früheres Ticket fachlich korrigiert werden müsste, Follow-up statt stiller Änderung.

## Implementation Notes (optional but useful)
- Prüfe zuerst, welche Tests heute bereits Volumen-/Gate-/Budget-Logik abdecken:
  - `tests/test_volume_gates_config_and_filters.py`
  - `tests/test_t82_topk_budget.py`
- Wenn diese Tests stark auf Altsemantik zugeschnitten sind, ist eine neue dedizierte Datei wie z. B. `tests/test_v421_pool_budget_behavior.py` wahrscheinlich sauberer.
- Integrationstests dürfen kleine synthetische Universen nutzen; keine unnötig großen Fixtures erzeugen.
- Tie-Breaker-Erwartungen nur dort fest codieren, wo PR-04 sie explizit definiert.
- Dieses Ticket darf vorhandene Test-Helfer nutzen, aber keine neue Produktionslogik in Test-Utilities verstecken.

## Acceptance Criteria (deterministic)
1) Es existieren explizite Tests für das EPIC-3-Verhalten nach V4.2.1, entweder durch Anpassung bestehender Tests oder durch neue dedizierte Testdatei(en).

2) Ein Test belegt deterministisch: Die Shortlist enthält nie mehr als `budget.shortlist_size` Kandidaten.

3) Ein Test belegt deterministisch: Coins unter `pre_shortlist_market_cap_floor_usd` erhalten keinen Shortlist-Platz.

4) Ein Test belegt deterministisch: Coins oberhalb des neuen Floors können trotz Überschreiten des früheren `market_cap.max_usd` shortgelistet werden.

5) Ein Test belegt deterministisch: zu niedrige Turnover-/MEXC-Quote-Volume-/MEXC-Share-Werte oberhalb des Floors verursachen keinen harten frühen Ausschluss mehr.

6) Ein Test belegt deterministisch: Stablecoins, Wrapped, Leveraged, Denylist- und harte Risk-Flag-Cases bleiben ausgeschlossen.

7) Ein Test belegt deterministisch: Bei identischem Input und identischer Config sind Auswahl und Reihenfolge der Shortlist identisch.

8) Ein Test belegt deterministisch: Fehlender Budget-Key nutzt den zentralen Default; ein ungültiger Budgetwert erzeugt einen klaren Fehler.

9) Kein Test in diesem PR behauptet oder impliziert Tradeability-, Risk-, Decision- oder Output-Semantik, die erst in späteren Tickets eingeführt wird.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (AC: #8; Test: fehlender `budget.shortlist_size` oder Floor-Key nutzt zentralen Default)
- **Config Invalid Value Handling:** ✅ (AC: #8; Test: ungültiger `shortlist_size` / ungültiger Floor-Wert => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (N/A — keine neuen nullable Output-Felder; semantische Zustände nicht implizit in bool mappen)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #3, #5, #9; Test: nicht-shortgelistet wegen Floor/Budget ≠ failed Tradeability)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — Testticket ohne Writer-/CLI-Output)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A — keine neuen Runtime-Dateinamen)
- **Deterministische Sortierung / Tie-breaker:** ✅ (AC: #7; Test: gleiche Fixture + gleiche Config => gleiche Reihenfolge)

## Tests (required if logic changes)
- Unit:
  - `shortlist_size`-Cap wird strikt eingehalten
  - fehlender Budget-Key nutzt zentralen Default
  - ungültiger Budgetwert erzeugt klaren Fehler
  - Coin unter `pre_shortlist_market_cap_floor_usd` wird nicht shortgelistet
  - Coin oberhalb des Floors und oberhalb altem `market_cap.max_usd` kann shortgelistet werden
  - niedrige Turnover-/Quote-Volume-/Share-Werte oberhalb des Floors führen nicht mehr zu hartem frühem Ausschluss
  - Stable/Wrapped/Leveraged bleiben ausgeschlossen
  - Denylist / harte Risk-Flags bleiben ausgeschlossen

- Integration:
  - kleine gemischte Universe-Fixture mit >Cap Kandidaten ergibt exakt `shortlist_size` Einträge
  - kleine gemischte Universe-Fixture mit <Cap Kandidaten gibt alle zulässigen Kandidaten zurück
  - identische Fixture + identische Config => identische Shortlist-Auswahl und -Reihenfolge

- Golden fixture / verification:
  - Nur falls bestehende Golden-/Schema-Tests explizit alte Pool-/Budget-Semantik fest verdrahten, diese bewusst auf V4.2.1 aktualisieren
  - Kein unnötiges Umschreiben nicht betroffener Golden-Files

## Constraints / Invariants (must not change)
- [ ] Dieses Ticket ändert keine Produktionslogik
- [ ] Safety-Excludes bleiben in den Testerwartungen hart
- [ ] `pre_shortlist_market_cap_floor_usd` bleibt harter Guardrail in den Testerwartungen
- [ ] Keine Vorwegnahme späterer Tradeability-/Decision-/Risk-Tickets
- [ ] Determinismus ist Pflichtbestandteil des Testnetzes
- [ ] Keine stille Drift gegenüber Ticket 3 und Ticket 4

## Definition of Done (Codex must satisfy)
- [ ] Relevante Testdateien erstellt/angepasst
- [ ] Acceptance Criteria testseitig abgedeckt
- [ ] Bestehende Altsemantik-Tests bewusst angepasst oder ersetzt, wo nötig
- [ ] Keine Produktionslogik in diesem PR verändert (außer minimal technisch zwingende Test-Hooks)
- [ ] Keine Scope-Überschreitung in spätere Epics
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-07T00:00:00Z"
priority: P0
type: tests
owner: codex
related_issues: []
```
