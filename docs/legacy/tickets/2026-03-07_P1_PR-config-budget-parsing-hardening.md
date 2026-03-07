> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P1] Config parsing robust gegen nicht-mapping Budget-Blöcke und numerische YAML-Notation machen

## Context / Source
- In PR #130 meldete Codex einen Validierungsfehler: Wenn `budget` vorhanden, aber kein Mapping ist (z. B. `null` oder String), ruft `validate_config` verkettete `.get(...)`-Zugriffe auf einem Nicht-Dict auf und kann mit `AttributeError` abbrechen, statt deterministische Validierungsfehler zurückzugeben.
- In PR #132 meldete Codex einen Laufzeitfehler: Budget-Felder werden über `ScannerConfig` mit `int(...)` gelesen, wodurch häufige YAML-Notationen wie `"2e2"` oder `"2.5e7"` zwar die Validierung bestehen, später aber bei Accessor-/Runtime-Zugriffen mit `ValueError` crashen können.
- PR #131 meldete einen möglichen Volumen-/Tie-Breaker-Fehler. Dieser konkrete Hinweis ist nach aktuellem Stand **nicht** als separates Follow-up zu behandeln, weil `ShortlistSelector` bereits `float(... or 0)` bei Proxy-/Tie-Breaker-Pfaden nutzt und damit den konkret gemeldeten `None`-vs-`0.0`-Sortiercrash nicht mehr reproduziert.
- PR #133 enthält keinen sichtbaren negativen Codex-Reviewpunkt; dort ist nur eine positive Reaktion sichtbar.

## Goal
Der Config-Layer verarbeitet malformed/hand-edited Budget-Konfigurationen robust und deterministisch:
- `validate_config` darf bei nicht-mapping Budget-Blöcken nicht crashen.
- `ScannerConfig`-Accessor für Budget-Felder müssen dieselben numerischen Formen akzeptieren wie die Validierung.
- Missing, invalid und semantisch unzulässige Werte bleiben sauber getrennt.
- Laufzeit und Validierung verwenden konsistente Parsing-Semantik.

## Scope
Änderungen an:

- `scanner/config.py`
- zugehörige Tests für Config/Budget-Validierung und Accessor-Verhalten
- ggf. `docs/canonical/VERIFICATION_FOR_AI.md`, **nur falls** bestehende Verifikationsregeln für Scoring/Threshold/Curve-Verhalten betroffen wären (wahrscheinlich nicht nötig)
- Ticket-Archivierung gemäß Workflow nach PR-Erstellung

## Out of Scope
- Keine Änderungen an `scanner/pipeline/filters.py`
- Keine Änderungen an `scanner/pipeline/shortlist.py`, außer falls unbedingt nötig, um neue zentrale Accessor-Semantik zu nutzen
- Keine Änderung der Canonical-Werte für `budget.shortlist_size`, `budget.orderbook_top_k` oder `budget.pre_shortlist_market_cap_floor_usd`
- Keine neue Config-Semantik für andere Blöcke als den Budget-Block
- Keine Änderung an Decision-, Risk-, Tradeability- oder Pool-Logik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/BUDGET_AND_POOL_MODEL.md`
- `docs/canonical/CHANGELOG.md`
- `docs/tickets/_TEMPLATE.md`

## Proposed change (high-level)
Before:
- `validate_config` behandelt `budget` implizit als Mapping und kann bei `budget: null` oder `budget: "bad"` mit `AttributeError` abbrechen.
- `ScannerConfig`-Budget-Accessor nutzen direkt `int(...)` auf Rohwerten.
- Dadurch entsteht Inkonsistenz:
  - Validierung akzeptiert numerische YAML-Notation via `float(...)`
  - Runtime-Accessor können denselben Wert später mit `ValueError` ablehnen
- Das verletzt die gewünschte deterministische Regel „invalid value -> klarer Validierungsfehler / kein unerwarteter Runtime-Crash“.

After:
- Budget-Block wird vor Zugriffen zentral als Mapping geprüft.
- Nicht-Mapping-Budget (`null`, String, Liste, Bool) erzeugt deterministische Validierungsfehler statt Exceptions.
- Budget-Accessor verwenden zentrale Parsing-Logik, die dieselben zulässigen numerischen Formen akzeptiert wie die Validierung.
- Für Integer-Felder wird klar geregelt:
  - numerisch darstellbare Werte sind erlaubt
  - nicht-ganzzahlige Werte sind entweder explizit verboten oder explizit und deterministisch normalisiert
- Missing vs invalid bleibt explizit getrennt.
- Laufzeit-Accessor und Validierung driften nicht mehr auseinander.

Edge cases:
- `budget` fehlt komplett
- `budget: null`
- `budget: "bad"`
- `budget: []`
- `budget: true`
- `budget.shortlist_size: "2e2"`
- `budget.orderbook_top_k: "2e2"`
- `budget.pre_shortlist_market_cap_floor_usd: "2.5e7"`
- negative Werte
- `0` bei Feldern mit Minimum `>= 1`
- nicht-ganzzahlige Werte bei Integer-Feldern, z. B. `"2.5"` oder `2.5`

Backward compatibility impact:
- Keine fachliche Änderung an den Budget-Defaults.
- Strengere Robustheit bei malformed Configs.
- Potenziell breitere Akzeptanz gängiger numerischer YAML-Schreibweisen, sofern sie semantisch zulässig sind.
- Ziel ist, Validierung und Runtime konsistent zu machen, nicht Konfigurationsverträge zu lockern oder zu verschärfen ohne explizite Regel.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Zentrale Parsing-Logik verwenden:** Kein mehrfaches ad-hoc `int(raw.get(...))` oder verkettetes `.get(...).get(...)` auf ungesicherten Objekten.
- **Budget-Mapping vor Zugriff prüfen:** Wenn `budget` vorhanden, aber kein Mapping ist, darf kein `AttributeError` oder vergleichbarer ungefangener Laufzeitfehler entstehen.
- **Missing ≠ Invalid:** Fehlender `budget`-Block nutzt Defaults; vorhandener aber ungültiger `budget`-Block produziert klare Validierungsfehler.
- **Accessor/Validation-Konsistenz:** Werte, die die Validierung ausdrücklich akzeptiert, dürfen später beim Accessor nicht an derselben Stelle crashen.
- **Keine stille Bool-Koerzierung:** `True`/`False` dürfen nicht als numerische Budgetwerte akzeptiert werden.
- **Integer-Semantik explizit:** Für `budget.shortlist_size` und `budget.orderbook_top_k` muss im Code klar festgelegt sein, ob nur echte Ganzzahlen oder auch numerisch darstellbare String-/Float-Formen akzeptiert werden. Keine implizite Interpretation ohne Tests.
- **Deterministische Fehlermeldungen:** Invalid cases müssen reproduzierbar klare Fehlertexte liefern.
- **Keine Scope-Ausweitung:** Nur Budget-Block fixen; keine allgemeine Großrefaktorierung der gesamten Config-Datei.
- **Tests zuerst mitdenken:** Jeder neue Guardrail braucht mindestens einen positiven und einen negativen Testfall.

## Implementation Notes (optional but useful)
Empfohlene Richtung:

1. Eine kleine zentrale Hilfslogik für „Block ist Mapping oder Default/Fehler“ einführen.
2. Budget-Accessor nicht direkt auf `self.raw.get("budget", {})` ketten, sondern einen gesicherten Mapping-Zugriff verwenden.
3. Budget-Felder über zentrale numerische Parser lesen:
   - `shortlist_size`
   - `orderbook_top_k`
   - `pre_shortlist_market_cap_floor_usd`
4. `validate_config` und `ScannerConfig` müssen dieselbe Zulässigkeitslogik teilen oder strikt parallel abbilden.
5. Wenn Integer-Felder numerische Strings wie `"2e2"` akzeptieren, dann muss das explizit und getestet sein.
6. Wenn nicht-ganzzahlige numerische Werte bei Integer-Feldern abgelehnt werden sollen, muss das explizit validiert und getestet sein.

## Acceptance Criteria (deterministic)
1) `validate_config` crasht nicht, wenn `budget` vorhanden, aber kein Mapping ist.

2) Für jeden der Fälle
- `budget: null`
- `budget: "bad"`
- `budget: []`
- `budget: true`
liefert `validate_config` deterministische Validierungsfehler statt ungefangener Exceptions.

3) Fehlender `budget`-Block verwendet weiterhin die kanonischen Defaults ohne Validierungsfehler.

4) `ScannerConfig.budget_shortlist_size` und `ScannerConfig.budget_orderbook_top_k` können Werte verarbeiten, die laut Validierung als zulässig gelten; es entsteht kein Accessor-/Runtime-Crash nach erfolgreicher Validierung.

5) `ScannerConfig.pre_shortlist_market_cap_floor_usd` kann Werte verarbeiten, die laut Validierung als zulässig gelten; es entsteht kein Accessor-/Runtime-Crash nach erfolgreicher Validierung.

6) Für numerische YAML-Notation wie
- `"2e2"` bei `budget.shortlist_size`
- `"2e2"` bei `budget.orderbook_top_k`
- `"2.5e7"` bei `budget.pre_shortlist_market_cap_floor_usd`
ist das Verhalten explizit geregelt und durch Tests abgesichert.

7) Bool-Werte (`true`/`false`) werden für Budget-Zahlen nicht als numerisch akzeptiert.

8) Negative oder semantisch unzulässige Budgetwerte erzeugen klare Validierungsfehler.

9) Es gibt keinen Drift mehr zwischen Validierungslogik und Runtime-Accessor-Semantik für die drei Budget-Felder:
- `budget.shortlist_size`
- `budget.orderbook_top_k`
- `budget.pre_shortlist_market_cap_floor_usd`

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (AC: #3; Test: fehlender `budget`-Block)
- **Config Invalid Value Handling:** ✅ (AC: #1, #2, #8; Test: non-mapping + negative/invalid values)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #2, #7; Test: `budget: null`, bool-Werte)
- **Not-evaluated vs failed getrennt:** ✅ (N/A — Config-Ticket, keine Runtime-State-Taxonomie)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A — kein Writer-/CLI-Ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A — kein Generator-Ticket)
- **Deterministische Sortierung / Tie-breaker:** ✅ (N/A — dieses Ticket ändert keine Ranking-/Sortierlogik)

## Tests (required if logic changes)
- Unit:
  - neue/erweiterte Tests für `validate_config` bei non-mapping `budget`
  - neue/erweiterte Tests für Budget-Accessor mit zulässigen numerischen String-/YAML-Formen
  - Tests für invalid/non-integer/negative/bool cases
- Integration:
  - mindestens ein Test, der zeigt: Config validiert erfolgreich und `ShortlistSelector`/Budget-Zugriff crasht nicht bei zulässiger numerischer YAML-Notation
- Golden fixture / verification:
  - nicht erforderlich, sofern keine Scoring-/Threshold-/Curve-Semantik geändert wird

## Constraints / Invariants (must not change)
- [ ] `docs/canonical/AUTHORITY.md` bleibt maßgeblich
- [ ] Kanonische Defaults für Budget-Felder bleiben unverändert
- [ ] Fehlender `budget`-Block bleibt default-fähig
- [ ] Invalid `budget`-Strukturen dürfen nicht mehr zu ungefangenen Exceptions führen
- [ ] Bool-Werte werden nicht als numerische Budgetwerte akzeptiert
- [ ] Keine Änderung an Filter-/Tradeability-/Decision-Semantik
- [ ] Keine Scope-Ausweitung auf andere Config-Blöcke ohne Notwendigkeit

## Definition of Done (Codex must satisfy)
- [ ] Budget-Parsing/Validation robust gegen non-mapping `budget`
- [ ] Runtime-Accessor und Validierung für Budget-Felder konsistent
- [ ] Tests für Missing, non-mapping, bool, negative und numerische YAML-Notation vorhanden
- [ ] Keine ungefangenen Exceptions mehr in den beschriebenen Budget-Fällen
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket wird nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-07T00:00:00Z"
priority: P1
type: bugfix
owner: codex
related_issues: []
```
