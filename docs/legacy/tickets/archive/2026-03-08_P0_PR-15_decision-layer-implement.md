> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-15 Decision Layer implementieren

## Context / Source
- Die aktuelle alleinige Referenz definiert in EPIC 7 / PR-15 die Einführung einer eigenständigen Decision Layer.
- Vorbedingung: Nur Coins, die das Tradeability Gate bereits passiert haben (`tradeability_class ∈ {DIRECT_OK, TRANCHE_OK, MARGINAL}`), erreichen diese Stufe.
- Die Decision Layer soll aus strukturierten Inputs eine eindeutige Phase-1-Entscheidung bilden:
  - `ENTER`
  - `WAIT`
  - `NO_TRADE`
- Die neuen verbindlichen Regeln gelten vollständig: Missing vs Invalid, `null` vs `false`, nicht evaluierbar vs negativ bewertet, Determinismus, keine stillen Interpretationen.

## Goal
Eine neue Datei `scanner/pipeline/decision.py` implementieren, die für voll evaluierte Kandidaten deterministisch Trade-Entscheidungen baut und strukturierte Reason Keys vergibt, ohne Exit-/Hold-/Portfolio-Logik einzuführen.

## Scope
- neue Datei `scanner/pipeline/decision.py`
- ggf. enge Integration in `scanner/pipeline/__init__.py`, soweit für die Einbindung der Decision Layer zwingend nötig
- ggf. TypedDicts/Dataclasses oder lokale Hilfsfunktionen im direkten Decision-Kontext
- keine Änderungen außerhalb des direkten Decision-Pfads, außer minimal nötige Signatur-/Import-Anpassungen

## Out of Scope
- Keine Tradeability-Berechnung
- Kein Tradeability-Gate
- Keine Risk-Berechnung
- Keine BTC-Regime-Neulogik über die Übergabe eines optionalen Regime-Inputs hinaus (vollständige Regime-Integration kommt im nächsten PR)
- Keine Output-Renderer-Umstellung
- Keine Portfolio-Management-Logik
- Keine Exit-/Hold-/Rotate-Logik
- Keine Kalibrierung

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- einschlägige Canonical-Dokumente für Tradeability-, Risk- und Setup-Felder
- die aktuelle verbindliche Ticket-Preflight-Checkliste

## Proposed change (high-level)
Before:
- Es gibt noch keine eigenständige Decision Layer, die aus strukturierten Vorstufen-Outputs eine Phase-1-Entscheidung erzeugt.
- Status- und Reason-Semantik sind noch nicht als klarer, maschinenlesbarer Entscheidungspfad umgesetzt.

After:
- Neue Funktion in `scanner/pipeline/decision.py`, sinngemäß:
  - Eingabe: voll evaluierte Kandidaten, Config, optionales BTC-Regime
  - Ausgabe: Kandidaten mit genau einem Decision-Status und passenden Reason Keys
- Statuslogik:
  - `ENTER` nur, wenn alle ENTER-Bedingungen erfüllt sind
  - `WAIT` nur für voll evaluierte Kandidaten mit ausreichender Grundqualität, aber noch nicht reif oder grenzwertig
  - `NO_TRADE` für negative bzw. unattraktive voll evaluierte Kandidaten
- UNKNOWN-Kandidaten erreichen die Decision Layer nicht; dies wird nicht stillschweigend umgangen.
- Reason-Matrix wird integriert und maschinenlesbar ausgegeben.

Edge cases:
- `tradeability_class = MARGINAL` => kein ENTER, typischerweise `WAIT`
- `risk_acceptable = null` oder fehlend => kein ENTER; Candidate ist nicht belastbar positiv entscheidbar
- `entry_ready = false`, aber Score hoch genug für Beobachtung => `WAIT`
- Score unter `min_score_for_wait` => `NO_TRADE`
- harter Risk-Flag-Blocker => `NO_TRADE`
- `FAIL` oder `UNKNOWN` gelangen theoretisch nicht bis hier; defensive Absicherung bleibt erlaubt

Backward compatibility impact:
- Neue Phase-1-Decision-Stufe wird eingeführt.
- Bestehende Ranking-/Watchlist-Pfade dürfen nicht implizit zur zweiten Wahrheit werden.
- `global_score` bleibt Kontext/Priorisierung, nicht primäre Decision-Wahrheit.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Statuswerte und Reason Keys exakt wie kanonisch vorgegeben verwenden.
- **Exakt ein Status pro Kandidat:** Jeder Kandidat erhält genau einen Status aus `{ENTER, WAIT, NO_TRADE}`.
- **Decision Layer nur für voll evaluierte Kandidaten:** UNKNOWN darf diese Stufe nicht erreichen; wenn defensiv doch vorhanden, nie als WAIT/ENTER behandeln.
- **`setup_score` vs `global_score` strikt trennen:** `setup_score` steuert Schwellen; `global_score` dient nur als Kontext/Priorisierung.
- **`risk_acceptable` Nullability beachten:** Wenn `risk_acceptable` nullable ist, darf `null` nicht implizit zu `false` oder `true` koerziert werden. Nicht evaluierbar bleibt nicht evaluierbar.
- **Missing vs invalid sauber:** Fehlende notwendige Inputs dürfen nicht stillschweigend in generische negative Status umkippen, ohne passenden Reason Key.
- **WAIT nur für voll evaluierte Coins:** WAIT ist kein Auffangbecken für technische Unbestimmtheit.
- **Determinismus:** Gleicher Input + gleiche Config + gleiches BTC-Regime => identischer Status und identische Reason-Ausgabe.
- **Keine Exit-/Portfolio-Logik einziehen.**
- **Reason-Matrix explizit:** Wenn mehrere Reasons relevant sind, Reihenfolge/Stabilität deterministisch halten.

## Implementation Notes (optional but useful)
- Die zentrale Funktion sollte eine klar testbare, reine Transformationsfunktion sein.
- Defensive Absicherung für Kandidaten mit `FAIL`/`UNKNOWN` ist erlaubt, auch wenn sie vor dieser Stufe eigentlich ausgeschlossen wurden.
- Wenn Reason Keys gesammelt werden, eine stabile Reihenfolge definieren oder dokumentieren.
- `btc_regime` darf zunächst optional als Input aufgenommen werden; der spezifische Regime-Boost wird im Folge-PR erweitert, die Signatur sollte aber kompatibel bleiben.

## Acceptance Criteria (deterministic)
1) Es existiert eine neue Datei `scanner/pipeline/decision.py`.

2) Die Decision-Komponente vergibt pro Kandidat genau einen Status aus:
   - `ENTER`
   - `WAIT`
   - `NO_TRADE`

3) `ENTER` wird nur vergeben, wenn mindestens alle folgenden Bedingungen erfüllt sind:
   - `tradeability_class` in `{DIRECT_OK, TRANCHE_OK}`
   - `entry_ready = true`
   - `risk_acceptable = true`
   - `setup_score` erfüllt die ENTER-Schwelle
   - kein harter Risk-Flag-Blocker

4) `WAIT` wird nur für voll evaluierte Kandidaten vergeben, z. B. wenn:
   - `entry_ready = false`, aber ausreichende Beobachtungsqualität vorhanden ist
   - `tradeability_class = MARGINAL`
   - ein BTC-Regime-Boost den ENTER-Schwellenwert erhöht und der Kandidat darunter fällt

5) `NO_TRADE` wird vergeben, wenn mindestens eines zutrifft:
   - `setup_score` unter `min_score_for_wait`
   - `risk_acceptable = false`
   - harter Risk-Flag-Blocker
   - defensive Absicherung für unzulässige Klassen wie `FAIL`

6) UNKNOWN-Kandidaten werden in der Decision Layer nicht als `WAIT` oder `ENTER` behandelt.

7) Die integrierte Reason-Matrix enthält mindestens die kanonischen Keys für:
   - `entry_not_confirmed`
   - `breakout_not_confirmed`
   - `retest_not_reclaimed`
   - `rebound_not_confirmed`
   - `tradeability_fail`
   - `tradeability_marginal`
   - `risk_reward_unattractive`
   - `stop_distance_too_wide`
   - `risk_data_insufficient`
   - `btc_regime_caution`
   - `insufficient_edge`
   - `risk_flag_blocked`

8) Bei identischem Input und identischer Config ist Status- und Reason-Ausgabe deterministisch identisch.

9) Dieses PR führt keine Exit-/Hold-/Portfolio-Logik ein.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ Fehlende Decision-Schwellen müssen zentral definierte Defaults verwenden oder klar als required markiert sein.
- **Config Invalid Value Handling:** ✅ Ungültige Decision-Schwellen oder inkompatible Statuswerte führen zu klarem Fehler, nicht zu stiller Koerzierung.
- **Nullability / kein bool()-Coercion:** ✅ `risk_acceptable = null` darf nicht implizit via `bool(...)` zu `False` oder `True` kollabieren; gleiches gilt für andere nullable Inputs.
- **Not-evaluated vs failed getrennt:** ✅ UNKNOWN / nicht evaluierbar bleibt getrennt von fachlich negativ bewertet.
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A — kein Writer-/CLI-Ticket.
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A.
- **Deterministische Sortierung / Tie-breaker:** ✅ Wenn Reason-Listen mehrere Keys enthalten, muss ihre Reihenfolge bei identischem Input stabil sein.

## Tests (required if logic changes)
- Unit:
  - ENTER bei `DIRECT_OK + entry_ready + risk_acceptable + Score ≥ Threshold`
  - ENTER bei `TRANCHE_OK + entry_ready + risk_acceptable + Score ≥ Threshold`
  - WAIT bei `entry_ready = false` und ausreichendem Beobachtungsscore
  - WAIT bei `tradeability_class = MARGINAL`
  - WAIT bei erhöhtem BTC-Regime-Schwellenwert und sonst starkem Kandidaten
  - NO_TRADE bei `risk_acceptable = false`
  - NO_TRADE bei Score unter `min_score_for_wait`
  - NO_TRADE bei `risk_flag_blocked`
  - defensiver Fall: UNKNOWN/FAIL führt nicht zu ENTER/WAIT
  - `risk_acceptable = null` bleibt semantisch korrekt und kollabiert nicht stillschweigend

- Integration:
  - Decision Layer verarbeitet nur voll evaluierte Kandidatenpfade
  - identischer Input + identische Config => identische Status-/Reason-Ausgabe
  - keine externen IO-/Netzwerkzugriffe

- Golden fixture / verification:
  - Nur anpassen, wenn bestehende Golden-/Snapshot-Tests alte Decision- oder Ranking-Semantik implizit fest verdrahten
  - Keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] Genau ein Status pro Kandidat
- [ ] WAIT bleibt voll evaluierter Beobachtungsstatus, kein technischem UNKNOWN-Ersatz
- [ ] `setup_score` und `global_score` bleiben fachlich getrennt
- [ ] keine Exit-/Hold-/Portfolio-Logik
- [ ] Status- und Reason-Ausgabe bleibt deterministisch
- [ ] UNKNOWN wird nicht zu WAIT/ENTER umgebogen

## Definition of Done (Codex must satisfy)
- [ ] `scanner/pipeline/decision.py` implementiert
- [ ] Acceptance Criteria erfüllt
- [ ] Tests gemäß Ticket ergänzt oder angepasst
- [ ] Missing-vs-invalid und `null`-vs-`false` sauber behandelt
- [ ] Keine Scope-Überschreitung in BTC-/Output-/Portfolio-/Exit-Logik
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-08T00:00:00Z"
priority: P0
type: feature
owner: codex
related_issues: []
```
