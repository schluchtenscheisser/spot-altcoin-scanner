> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-03 Hard-Gates zu Soft-Priors umbauen

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- EPIC 3 / PR-03 öffnet den Kandidatenpool früh, damit spätere Tradeability- und Decision-Stages auf einem realistischen Pool validiert werden können.
- Gleichzeitig muss die Pipeline interpretierbar und budgetiert bleiben; Safety-Excludes und harte Risk-Blocker dürfen nicht aufgeweicht werden.

## Goal
Die bisherigen harten Kill-Switches für MarketCap/Volume/Turnover/MEXC-Share werden so zurückgebaut, dass:
- Safety-Excludes unverändert hart bleiben,
- ein neuer harter Pre-Shortlist-Guardrail (`pre_shortlist_market_cap_floor_usd`) vor der Shortlist greift,
- frühere Hard-Gates oberhalb dieses Floors zu Kontext-/Prior-Feldern werden,
- der resultierende Pool deutlich breiter ist, ohne in spätere teure Stages ungefiltert durchzulaufen.

## Scope
- `scanner/pipeline/filters.py`
- falls nötig: kleine begleitende Anpassungen in Modulen, die `filters.py`-Outputs konsumieren, aber nur soweit nötig für die neue Semantik
- falls nötig: ergänzende Inline-Dokumentation/Kommentare im betroffenen Code

## Out of Scope
- Keine Anpassung der Cheap-Shortlist-Mechanik selbst
- Keine Änderung an `shortlist_size` oder `orderbook_top_k`
- Keine Tradeability-Berechnung
- Keine Risk-/Decision-Logik
- Keine Output-/Schema-Änderung
- Keine Migration-/Shadow-Mode-Logik
- Keine Änderung an Canonical Docs außer falls ein klarer Widerspruch zur Implementierung entdeckt wird; in dem Fall Ticket stoppen statt interpretieren

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/RISK_MODEL.md` (nur soweit Risk-Flags/Blocker referenziert werden)
- `docs/canonical/OUTPUT_SCHEMA.md` (nur falls Filterfelder downstream explizit genannt sind)

## Proposed change (high-level)
Before:
- Mehrere Universe-/Marktmetriken wirken als harte Excludes und schrumpfen den Pool bereits vor der Cheap-Shortlist stark zusammen.
- Dadurch werden nachgelagerte neue Stages (Tradeability / Decision) auf einem unrealistisch kleinen Kandidatenpool getestet.

After:
- Harte Safety-Excludes bleiben unverändert hart.
- Harte Risk-Flag-Blocker bleiben unverändert hart.
- Coins unter `budget.pre_shortlist_market_cap_floor_usd` werden weiterhin vor der Shortlist hart ausgeschlossen.
- Frühere harte Grenzen für:
  - `market_cap.min_usd`
  - `market_cap.max_usd`
  - `min_turnover_24h`
  - `min_mexc_quote_volume_24h`
  - `min_mexc_share_24h`
  werden oberhalb des Pre-Shortlist-Floors nicht mehr als Kill-Switch angewendet.
- Diese Felder bleiben als Kontext-/Prior-Information im Datensatz erhalten, damit Cheap-Pass, Output oder spätere Scores sie weiter nutzen können.
- Der resultierende Pool nach Filtern ist spürbar breiter, aber weiterhin kontrolliert.

Edge cases:
- Coin unter `pre_shortlist_market_cap_floor_usd` => harter Exclude, auch wenn sonst hohe Aktivität vorliegt
- Coin über altem `market_cap.max_usd` => darf jetzt im Pool verbleiben
- Coin mit sehr niedriger MEXC-Share / Turnover / Quote-Volume oberhalb des Floors => kein harter Exclude mehr
- Denylist / harte Risk-Flags => weiterhin harter Exclude
- Stable / Wrapped / Leveraged => weiterhin harter Exclude

Backward compatibility impact:
- Verhalten der frühen Filterstufe ändert sich bewusst.
- Bestehende Runs können mehr Symbole nach der Filterstufe enthalten als zuvor.
- Safety-Excludes und harte Risk-Blocker bleiben kompatibel.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Wenn Canonical und bestehender Code widersprechen, Canonical gewinnt.
- **Pre-Shortlist-Floor ist hart:** `budget.pre_shortlist_market_cap_floor_usd` ist ein operativer Pool-Guardrail, kein Soft-Prior, kein optionaler Penalty.
- **Legacy-Grenzen oberhalb des Floors nicht mehr als Kill-Switch verwenden:** `market_cap.*`, `min_turnover_24h`, `min_mexc_quote_volume_24h`, `min_mexc_share_24h` dürfen nach diesem PR oberhalb des Floors keinen frühen Ausschluss mehr verursachen.
- **Safety-Excludes nicht aufweichen:** Stablecoins, Wrapped, Leveraged sowie harte Risk-Flag-Blocker bleiben harte Ausschlüsse.
- **Kein stilles Fallback auf Raw-Dicts:** Config-Werte nur über die zentrale Config-/Default-Logik lesen; Missing key ≠ invalid.
- **Not-evaluated vs failed sauber trennen:** Dieses Ticket führt keine neue „failed“-Semantik ein; es regelt nur frühe Excludes vs im Pool verbleiben.
- **Determinismus bewahren:** Bei gleicher Eingabe und gleicher Config müssen dieselben Symbole dieselbe Filterentscheidung erhalten.
- **Keine neue Portfolio-/Decision-Semantik hineinziehen.**
- **Keine Umbenennung auf alte V4-Begriffe:** Nur `pre_shortlist_market_cap_floor_usd`, nicht `soft_market_cap_floor_usd`.

## Implementation Notes (optional but useful)
- Bestehende Filterpfade wahrscheinlich entlang:
  - Universe metadata
  - market cap
  - volume/turnover/share
  - denylist / risk flags
- Ziel ist nicht, alle Metriken zu ignorieren, sondern ihre harte Exclude-Semantik oberhalb des neuen Floors zu entfernen.
- Wenn Kontextfelder derzeit gar nicht downstream erhalten bleiben, muss mindestens sichergestellt werden, dass ihre Werte im Datenobjekt erhalten bleiben und nicht durch die Filterstufe gelöscht werden.
- Harte Risk-Blocker müssen weiterhin auf den autoritativen Quellen basieren:
  - `config/denylist.yaml`
  - `config/unlock_overrides.yaml`
  - `filters.py._apply_risk_flags()`

## Acceptance Criteria (deterministic)
1) `scanner/pipeline/filters.py` verwendet `budget.pre_shortlist_market_cap_floor_usd` als harten Exclude vor der Shortlist.

2) Ein Coin mit MarketCap unter `pre_shortlist_market_cap_floor_usd` wird in der Filterstufe ausgeschlossen, auch wenn andere Aktivitätsmetriken positiv sind.

3) Ein Coin mit MarketCap oberhalb des Floors wird nicht mehr allein deshalb ausgeschlossen, weil:
   - er über dem früheren `market_cap.max_usd` liegt,
   - `min_turnover_24h` nicht erreicht,
   - `min_mexc_quote_volume_24h` nicht erreicht,
   - `min_mexc_share_24h` nicht erreicht.

4) Stablecoins, Wrapped, Leveraged bleiben harte Excludes.

5) Harte Risk-Flag-Blocker und Denylist-Einträge bleiben harte Excludes.

6) Die frühere Hard-Gate-Semantik für MarketCap/Volume/Turnover/MEXC-Share oberhalb des Floors ist im Code entfernt oder so umgestellt, dass diese Felder nur noch Kontext-/Prior-Rolle haben.

7) Bestehende Configs bleiben lauffähig; fehlende neue Keys greifen über zentrale Defaults, nicht über ad-hoc Raw-Dict-Fallbacks.

8) Die Filterentscheidung ist bei identischem Input und identischer Config deterministisch.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (AC: #7 ; Test: Config ohne neuen Budget-Key nutzt zentralen Default)
- **Config Invalid Value Handling:** ✅ (AC: #1 ; Test: ungültiger `pre_shortlist_market_cap_floor_usd` führt zu klarem Validierungsfehler, nicht zu stiller Koerzierung)
- **Nullability / kein bool()-Coercion:** ✅ (N/A — Ticket produziert keine neuen nullable Output-Felder; keine implizite `bool(...)`-Koerzierung für semantische Zustände)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #3, #5 ; Test: fehlende Aktivitätsmetriken oberhalb des Floors führen nicht zu „hart excluded“, Risk-Blocker schon)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A — kein Datei-/ID-Generator)
- **Deterministische Sortierung / Tie-breaker:** ✅ (AC: #8 ; Test: identischer Input → identische Filterentscheidung)

## Tests (required if logic changes)
- Unit:
  - Coin unter `pre_shortlist_market_cap_floor_usd` wird ausgeschlossen
  - Coin oberhalb des Floors und oberhalb altem `market_cap.max_usd` bleibt im Pool
  - Coin oberhalb des Floors mit zu niedrigem Turnover bleibt im Pool
  - Coin oberhalb des Floors mit zu niedriger MEXC-Quote-Volume bleibt im Pool
  - Coin oberhalb des Floors mit zu niedriger MEXC-Share bleibt im Pool
  - Stable/Wrapped/Leveraged bleiben ausgeschlossen
  - Denylist / harte Risk-Flags bleiben ausgeschlossen
  - Missing neuer Budget-Key => zentraler Default greift
  - Invalid `pre_shortlist_market_cap_floor_usd` => klarer Fehler

- Integration:
  - Kleine Fixture mit gemischtem Universum zeigt: Pool ist breiter als vorher, aber Coins unter Floor bleiben draußen
  - Identische Fixture + identische Config => identisches Filterresultat

- Golden fixture / verification:
  - Falls bestehende Golden-Files die Filtermenge exakt fest verdrahten, nur dann aktualisieren, wenn sie bewusst die alte Hard-Gate-Semantik abbilden
  - Wenn Scoring-/Threshold-/Curve-Verhalten betroffen ist: `docs/canonical/VERIFICATION_FOR_AI.md` nur aktualisieren, falls dort diese Filterlogik explizit verifiziert wird

## Constraints / Invariants (must not change)
- [ ] Closed-candle-only / no-lookahead bleibt unberührt
- [ ] Safety-Excludes bleiben hart
- [ ] Harte Risk-Flags bleiben hart
- [ ] `pre_shortlist_market_cap_floor_usd` bleibt harter Pool-Guardrail
- [ ] Keine Tradeability-, Risk- oder Decision-Logik in diesem Ticket
- [ ] Keine Output-Schema-Änderung
- [ ] Deterministische Filterentscheidungen

## Definition of Done (Codex must satisfy)
- [ ] Codeänderungen gemäß Acceptance Criteria implementiert
- [ ] Unit-/Integration-Tests gemäß Ticket ergänzt oder angepasst
- [ ] Keine stillen Fallbacks / Raw-Dict-Defaults eingeführt
- [ ] Keine Scope-Überschreitung in Shortlist-, Tradeability-, Risk- oder Decision-Logik
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
