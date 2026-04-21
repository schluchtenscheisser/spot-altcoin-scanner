> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-06 Tradeability-Berechnung inkl. Klassifikation V4.2.1 implementieren

## Context / Source
- V4.2.1 ist die alleinige Referenz.
- EPIC 4 / PR-06 definiert Tradeability als primäre Eintrittsbedingung.
- Nach PR-03/04 ist der Pool breiter und die Shortlist budgetiert; jetzt muss `scanner/pipeline/liquidity.py` aus Orderbook-Daten eine deterministische Tradeability-Bewertung für 20k total und 5k-Tranchen ableiten.
- Die bestehende Liquidity-Logik im Repo enthält bereits Spread-/Depth-/Slippage-Bausteine und Liquidity-Grades; dieses Ticket hebt sie auf die neue kanonische Tradeability-Taxonomie.

## Goal
`scanner/pipeline/liquidity.py` berechnet für jeden shortgelisteten Coin eine vollständige, deterministische Tradeability-Bewertung mit:
- 5k- und 20k-Slippage,
- direkter und trancheweiser Handelbarkeit,
- `tradeability_class ∈ {DIRECT_OK, TRANCHE_OK, MARGINAL, FAIL, UNKNOWN}`,
- `execution_mode ∈ {direct, tranches, none}`,
- strukturierten `tradeability_reason_keys`.

## Scope
- `scanner/pipeline/liquidity.py`
- ggf. kleine Hilfsfunktionen in demselben Modul
- ggf. enge, direkte Anpassungen an Import-/Dataclass-/TypedDict-Definitionen, die `liquidity.py` zwingend für die neuen Rückgabefelder benötigt
- keine Änderungen außerhalb des Liquidity-Bereichs, außer minimal nötiger Typ-/Import-Anpassungen

## Out of Scope
- Kein globales Pipeline-Gate in `scanner/pipeline/__init__.py` (kommt in PR-07)
- Keine OHLCV-/Feature-/Scoring-/Decision-Logik
- Keine Risk-/Downside-Logik
- Keine Output-/Renderer-Änderung
- Keine BTC-Regime-Logik
- Keine Shadow-Mode-/Migration-Logik
- Keine neue Config-Struktur außerhalb dessen, was bereits in PR-02 definiert wurde

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md` (nur für Statusgrenzen, nicht implementieren)

## Proposed change (high-level)
Before:
- Liquidity-/Orderbook-Logik liefert bestehende Spread-/Depth-/Slippage-Metriken und Liquidity-Grades, aber noch nicht die vollständige V4.2.1-Tradeability-Taxonomie.
- Die Entscheidung „20k direkt / 4×5k trancheweise / marginal / fail / unknown“ ist noch nicht als kanonische Klasse im Modul festgezogen.

After:
- `liquidity.py` berechnet pro Coin:
  - `slippage_bps_5k`
  - `slippage_bps_20k`
  - `tradeable_5k`
  - `tradeable_20k`
  - `tradeable_via_tranches`
  - `tradeability_class`
  - `execution_mode`
  - `tradeability_reason_keys`
- Die Klassifikation folgt den V4.2.1-Regeln:
  - `DIRECT_OK`: 20k Slippage ≤ direct_ok-Grenze UND Spread-Gate UND Depth-Gate
  - `TRANCHE_OK`: kein DIRECT_OK, aber 5k trancheweise ≤ tranche_ok-Grenze und bis `max_tranches` machbar
  - `MARGINAL`: kein DIRECT_OK/TRANCHE_OK, aber noch innerhalb marginaler Slippage-Grenze bzw. grenzwertiger Spread/Depth-Konstellation
  - `FAIL`: vollständig evaluiert, aber nicht akzeptabel handelbar
  - `UNKNOWN`: Orderbook fehlt / stale / nicht brauchbar für Bewertung
- `execution_mode` ist nur:
  - `direct`
  - `tranches`
  - `none`

Edge cases:
- Orderbook fehlt komplett => `tradeability_class = UNKNOWN`, `execution_mode = none`
- Orderbook stale => `tradeability_class = UNKNOWN`, `execution_mode = none`
- Orderbook vorhanden, aber 20k nicht handelbar, 4×5k handelbar => `TRANCHE_OK`
- 5k nur knapp innerhalb marginaler Grenze => `MARGINAL`
- Spread-Gate verletzt => kein DIRECT_OK/TRANCHE_OK, aber je nach restlicher Ausprägung `MARGINAL` oder `FAIL`
- `MARGINAL` ist voll evaluiert, nicht UNKNOWN
- `UNKNOWN` ist nicht `FAIL`

Backward compatibility impact:
- Bestehende Liquidity-Felder bleiben möglichst erhalten, werden aber um die kanonischen V4.2.1-Felder ergänzt oder fachlich darauf abgebildet.
- Bestehende Grade-Logik kann intern weitergenutzt werden, darf aber die neue Taxonomie nicht widersprechen.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Begriffe und Enum-Werte exakt wie in Canonical/V4.2.1 verwenden. Keine Aliase wie `PASS`, `OK`, `TRADEABLE`.
- **Kein Bool als Hauptwahrheit:** `tradeability_pass` darf nicht die primäre neue Wahrheit sein. Die primäre Wahrheit ist `tradeability_class`.
- **UNKNOWN vs FAIL strikt trennen:**
  - `UNKNOWN` = nicht belastbar evaluierbar
  - `FAIL` = belastbar evaluiert und negativ
- **Missing vs Invalid explizit:** Fehlendes/stales Orderbook darf nicht stillschweigend als `FAIL` oder `False` enden.
- **Nullability explizit:** Wo Slippage mangels Daten nicht berechnet werden kann, ist `null`/`None` semantisch erlaubt; keine implizite `bool(...)`-Koerzierung.
- **Tranche-Logik deterministisch:** `tradeable_via_tranches` nutzt exakt:
  - `notional_chunk_usdt`
  - `max_tranches`
  - konfigurierte Schwellen
  keine heuristischen Extra-Schritte.
- **Konfigurationswerte nur zentral lesen:** Keine ad-hoc Magic Numbers im Modul.
- **Keine Decision-Semantik hineinziehen:** Dieses Ticket klassifiziert Tradeability, entscheidet aber noch nicht `ENTER/WAIT/NO_TRADE`.
- **Determinismus:** Gleicher Orderbook-Input + gleiche Config => identische Klassifikation und identische Reason-Keys.
- **Execution mode konsistent:** `direct` nur bei `DIRECT_OK`; `tranches` nur bei `TRANCHE_OK`; `none` bei `MARGINAL/FAIL/UNKNOWN`.

## Implementation Notes (optional but useful)
- Nutze bestehende Orderbook-/Slippage-Helfer, falls vorhanden, statt doppelte Logik neu zu erfinden.
- Wenn das Modul aktuell nur eine einzelne Slippage-Metrik ausgibt, erweitere es auf getrennte Notional-Sichten.
- Reason-Keys sollen maschinenlesbar und stabil sein, z. B.:
  - `spread_too_wide`
  - `depth_1pct_insufficient`
  - `slippage_20k_too_high`
  - `slippage_5k_too_high`
  - `tranche_execution_not_feasible`
  - `orderbook_data_missing`
  - `orderbook_data_stale`
- Reason-Keys müssen nicht die Decision-Reasons abbilden; sie sind Tradeability-interne Gründe.
- Wenn bestehende Liquidity-Grades (A/B/C/D) intern nützlich sind, dürfen sie intern weiterverwendet werden, solange die kanonische Ausgabe die neue Taxonomie ist.

## Acceptance Criteria (deterministic)
1) `scanner/pipeline/liquidity.py` berechnet getrennt:
   - `slippage_bps_5k`
   - `slippage_bps_20k`

2) Das Modul liefert pro evaluiertem Coin:
   - `tradeable_5k`
   - `tradeable_20k`
   - `tradeable_via_tranches`
   - `tradeability_class`
   - `execution_mode`
   - `tradeability_reason_keys`

3) `tradeability_class` ist exakt einer der Werte:
   - `DIRECT_OK`
   - `TRANCHE_OK`
   - `MARGINAL`
   - `FAIL`
   - `UNKNOWN`

4) `execution_mode` ist exakt einer der Werte:
   - `direct`
   - `tranches`
   - `none`

5) Ein Coin mit akzeptabler 20k-Slippage, akzeptablem Spread und ausreichender 1%-Depth wird als `DIRECT_OK` klassifiziert.

6) Ein Coin ohne `DIRECT_OK`, aber mit akzeptabler trancheweiser 5k-Handelbarkeit bis `max_tranches`, wird als `TRANCHE_OK` klassifiziert.

7) Ein Coin, der weder `DIRECT_OK` noch `TRANCHE_OK` erreicht, aber nur knapp/grenzwertig handelbar ist, wird als `MARGINAL` klassifiziert.

8) Ein Coin mit auswertbaren Orderbook-Daten, der die Anforderungen klar verfehlt, wird als `FAIL` klassifiziert.

9) Fehlende oder stale Orderbook-Daten führen zu `tradeability_class = UNKNOWN` und **nicht** zu `FAIL`.

10) `tradeability_reason_keys` trennen Missing/Stale explizit von negativer Bewertung.

11) Bei identischem Orderbook-Input und identischer Config ist die Klassifikation deterministisch.

12) Es werden keine Decision- oder Risk-Felder in diesem PR eingeführt.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (Test: fehlende Tradeability-Threshold-Keys nutzen zentrale Defaults aus PR-02)
- **Config Invalid Value Handling:** ✅ (Test: ungültige Slippage-/Spread-/Depth-Thresholds erzeugen klaren Fehler, keine stille Koerzierung)
- **Nullability / kein bool()-Coercion:** ✅ (Test: fehlendes Orderbook => Slippage-Felder `None`, Klasse `UNKNOWN`, kein implizites `False` als FAIL)
- **Not-evaluated vs failed getrennt:** ✅ (AC #8, #9, #10)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A)
- **Deterministische Sortierung / Tie-breaker:** ✅ (N/A für Ranking; Determinismus der Klassifikation via AC #11)

## Tests (required if logic changes)
- Unit:
  - DIRECT_OK bei tiefem Orderbook + engem Spread + akzeptabler 20k-Slippage
  - TRANCHE_OK bei nicht akzeptabler 20k-Slippage, aber akzeptabler 5k-Tranche × max_tranches
  - MARGINAL bei grenzwertiger, aber nicht ENTER-fähiger Handelbarkeit
  - FAIL bei dünnem Orderbook / hoher Slippage / zu weitem Spread
  - UNKNOWN bei fehlendem Orderbook
  - UNKNOWN bei stale Orderbook
  - `execution_mode = direct` nur bei DIRECT_OK
  - `execution_mode = tranches` nur bei TRANCHE_OK
  - `execution_mode = none` bei MARGINAL / FAIL / UNKNOWN
  - Missing zentrale Config-Keys => Defaults greifen
  - Invalid Threshold-Werte => klarer Fehler

- Integration:
  - Kleine Fixture mit mehreren Orderbook-Profilen erzeugt exakt die erwarteten Klassen
  - Identische Fixture + identische Config => identische Ergebnisse
  - Bestehende Liquidity-Metriken bleiben kompatibel, soweit im Modul bereits verwendet

- Golden fixture / verification:
  - Falls bestehende Tests/Golden-Files auf alte Liquidity-Outputform fest verdrahtet sind, bewusst nur dort anpassen, wo die neue kanonische Tradeability-Ausgabe betroffen ist
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] `tradeability_class` bleibt die primäre neue Truth, nicht ein Bool
- [ ] UNKNOWN und FAIL bleiben semantisch strikt getrennt
- [ ] `MARGINAL` bleibt voll evaluiert und nicht UNKNOWN
- [ ] Keine Decision-/Risk-/Output-SoT-Logik in diesem Ticket
- [ ] Konfigurationswerte nur zentral lesen
- [ ] Deterministische Klassifikation
- [ ] Keine Scope-Ausweitung auf Pipeline-Gating

## Definition of Done (Codex must satisfy)
- [ ] Codeänderungen gemäß Acceptance Criteria implementiert
- [ ] Unit-/Integration-Tests gemäß Ticket ergänzt oder angepasst
- [ ] Missing vs Invalid und UNKNOWN vs FAIL explizit sauber abgebildet
- [ ] Keine Scope-Überschreitung in Pipeline-Gate, Risk oder Decision
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
