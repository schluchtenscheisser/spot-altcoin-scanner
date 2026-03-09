> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Entry-state diagnostics: Summary-Counts und explizite Timing-Reasons ergänzen

## Kontext / Source
Mit den letzten zwei Tickets wurde die Timing-Semantik im Output deutlich verbessert:

- `trade_candidates.entry_price_usdt` repräsentiert jetzt den **geplanten Entry**
- `trade_candidates.current_price_usdt` repräsentiert den **aktuellen Spot**
- `trade_candidates.distance_to_entry_pct` und `trade_candidates.entry_state` machen die Lage von Spot vs. geplantem Entry sichtbar

Der nächste Engpass ist jetzt **nicht** die Datengrundlage, sondern die **Attribution**:

- Im Report ist noch nicht aggregiert sichtbar, wie viele Kandidaten `early`, `at_trigger`, `late`, `chased` oder `null` sind
- Timing-Probleme werden in der Kandidatenbegründung noch nicht explizit als eigene maschinenlesbare Gründe ausgewiesen
- Dadurch bleibt unklar, ob `NO_TRADE` heute primär an
  - Timing,
  - Liquidität,
  - Risk,
  - Score-Hürde
  oder einer Kombination scheitert

Dieses Ticket ist bewusst ein **Diagnose-/Erklärbarkeits-Ticket**.  
Es soll **keine** Scoring-, Risk-, Tradeability- oder Decision-Logik verändern.

## Goal
Der Report soll nach diesem Ticket zwei neue Diagnose-Ebenen bieten:

1. **Aggregierte Entry-State-Sicht**
   - Der Report zeigt explizit, wie viele Kandidaten in welchem `entry_state` liegen

2. **Explizite Timing-Reasons**
   - Kandidaten bekommen zusätzlich maschinenlesbare Timing-Gründe wie:
     - `entry_too_early`
     - `entry_late`
     - `entry_chased`

Ziel ist, nach mehreren Runs belastbar beantworten zu können:

- Sind gute Setups vorhanden, aber zum Run-Zeitpunkt einfach nicht frisch?
- Oder scheitern Kandidaten überwiegend an anderen Regeln?

## Scope
Erlaubte Änderungen in diesem Ticket:

- `scanner/pipeline/output.py`
- canonical Output-Dokumentation in `docs/canonical/OUTPUT_SCHEMA.md`
- ggf. angrenzende Doku, falls Summary-/Reason-Verträge dort beschrieben sind
- Markdown-/Excel-Output, soweit diese Candidate-/Summary-Felder explizit rendern
- output-nahe Tests unter `tests/`

Betroffene reale Repo-Pfade, auf die sich dieses Ticket stützt:

- `scanner/pipeline/output.py`
- `docs/canonical/OUTPUT_SCHEMA.md`
- ggf. `scanner/pipeline/excel_output.py`
- output-nahe Tests unter `tests/`

## Out of Scope
Explizit **nicht** Teil dieses Tickets:

- keine Änderung an `decision.py`
- keine Änderung von `risk_acceptable`
- keine Änderung von ATR-/Stop-/RR-Regeln
- keine Änderung an Tradeability-Gates
- keine Änderung der Setup-Scorer
- keine Änderung an BTC-Regime-Logik
- keine Änderung der Ranking-/Sortierlogik
- keine neuen harten Entry-State-Filter
- keine automatische Ableitung von `decision` aus `entry_state`

## Canonical References (important)
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/INDEX.md`

## Proposed change (high-level)
Beschreibe gewünschtes Verhalten, nicht freie Neuinterpretation:

- **Before:**
  - `trade_candidates` enthalten bereits `distance_to_entry_pct` und `entry_state`
  - Die Summary aggregiert diese Information nicht
  - Timing-Probleme erscheinen nicht explizit als eigene maschinenlesbare Diagnose-Gründe
- **After:**
  - Der Report enthält aggregierte `entry_state`-Counts
  - Die Counts werden mindestens für **alle `trade_candidates`** ausgewiesen
  - Falls praktikabel im bestehenden Summary-Vertrag, zusätzlich getrennt nach:
    - `ENTER`
    - `WAIT`
    - `NO_TRADE`
  - `trade_candidates.decision_reasons` werden um **diagnostische Timing-Reasons** ergänzt, wenn `entry_state` dies fachlich eindeutig nahelegt:
    - `entry_too_early`
    - `entry_late`
    - `entry_chased`
- **Wichtige Semantik:**
  - Diese Timing-Reasons sind zunächst **erklärend / diagnostisch**
  - Sie sind **keine** neue harte Entscheidungslogik
  - Bestehende Gründe wie `risk_reward_unattractive` oder `entry_not_confirmed` bleiben erhalten, wenn sie weiterhin gelten
- **Edge cases:**
  - `entry_state = null`
  - `distance_to_entry_pct = null`
  - `decision_reasons = null` / fehlend / leere Liste
  - Kandidat mit mehreren gleichzeitigen Gründen
  - Kandidat mit `entry_state = at_trigger` bekommt **keinen** neuen Timing-Reason
- **Backward compatibility impact:**
  - JSON-Summary wird erweitert
  - `decision_reasons` können zusätzliche maschinenlesbare Timing-Reasons enthalten
  - Ranking, Entscheidung und Risiko-Felder bleiben unverändert

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> Diese Sektion ist eine **Ausführungsanweisung** für Codex. Wenn hier etwas nicht eindeutig ist, muss das Ticket angepasst werden. Kein Raten.

- **Config/Defaults:** Dieses Ticket führt **keine neue Konfigurationslogik** ein. Keine neuen Config-Keys, keine ad-hoc Defaults.
- **Nullability:** Summary-Zählungen dürfen nie durch implizite `bool(...)`-Coercion aus nullable Feldern entstehen. Ein fehlender `entry_state` bleibt semantisch fehlend und wird als eigener Count (`null`) oder explizit dokumentierter fehlender Zustand gezählt.
- **Strict/Preflight:** Falls Output-Validierung existiert, muss sie den erweiterten Summary-/Reason-Vertrag vor dem Schreiben prüfen. Keine stillen Umbauten außerhalb der beschriebenen Regeln.
- **Not-evaluated vs failed:**
  - `entry_state = null` bedeutet: Timing derzeit **nicht auswertbar**
  - `entry_state = early|at_trigger|late|chased` bedeutet: Timing wurde **fachlich ausgewertet**
  - `entry_state = null` darf **nicht** automatisch zu `entry_too_early`, `entry_late` oder `entry_chased` führen
- **Determinismus:** Die Einfügung diagnostischer Timing-Reasons muss deterministisch sein. Bei identischem Input und identischer Config bleiben Reihenfolge und Inhalt der Reasons stabil.
- **Reason-Semantik:**
  - `entry_too_early` nur für `entry_state = early`
  - `entry_late` nur für `entry_state = late`
  - `entry_chased` nur für `entry_state = chased`
  - Für `entry_state = at_trigger` wird **kein** zusätzlicher Timing-Reason erzeugt
  - Für `entry_state = null` wird **kein** zusätzlicher Timing-Reason erzeugt
- **Reason-Liste / Deduplizierung:**
  - Vorhandene `decision_reasons` bleiben erhalten
  - Timing-Reasons werden **additiv** ergänzt
  - Doppelte Einträge sind nicht erlaubt
  - Die finale Reihenfolge der Reasons muss stabil und testbar sein; vorhandene Gründe dürfen nicht zufällig umsortiert werden
- **Repo-Reality:** Vorhandene `entry_state`-Ableitung wiederverwenden; keine zweite parallele Timing-Klassifikation einführen.

## Implementation Notes (optional but useful)
- Summary:
  - Aggregiere `entry_state` explizit statt implizit
  - Empfehlung: `entry_state_counts_all`
  - optional zusätzlich:
    - `entry_state_counts_enter`
    - `entry_state_counts_wait`
    - `entry_state_counts_no_trade`
- Reasoning:
  - Timing-Reasons werden im Output-Layer aus vorhandenem `entry_state` abgeleitet
  - Keine Logikverschiebung in Decision-/Scoring-Module
- Wichtig:
  - Das Ticket ist erfolgreich, wenn der Report besser erklärt, **warum** Kandidaten heute unattraktiv sind
  - Das Ticket ist **nicht** erfolgreich, wenn es dadurch neue `ENTER`/`WAIT`/`NO_TRADE`-Entscheidungen erzeugt

## Acceptance Criteria (deterministic)
1) Der finale JSON-Report enthält auf Summary-Ebene aggregierte `entry_state`-Counts für alle `trade_candidates`, mindestens für die Zustände:
   - `early`
   - `at_trigger`
   - `late`
   - `chased`
   - `null`

2) Wenn im bestehenden Summary-Vertrag Untergruppen nach `decision` praktikabel sind, enthält der Report zusätzlich getrennte `entry_state`-Counts für:
   - `ENTER`
   - `WAIT`
   - `NO_TRADE`
   Falls diese Untergruppen bewusst nicht aufgenommen werden, ist dies in der Canonical-Doku explizit dokumentiert.

3) Für einen `trade_candidate` mit `entry_state = early` wird `decision_reasons` um `entry_too_early` ergänzt, sofern dieser Grund nicht bereits vorhanden ist.

4) Für einen `trade_candidate` mit `entry_state = late` wird `decision_reasons` um `entry_late` ergänzt, sofern dieser Grund nicht bereits vorhanden ist.

5) Für einen `trade_candidate` mit `entry_state = chased` wird `decision_reasons` um `entry_chased` ergänzt, sofern dieser Grund nicht bereits vorhanden ist.

6) Für `trade_candidate` mit `entry_state = at_trigger` oder `entry_state = null` wird **kein** neuer Timing-Reason ergänzt.

7) Vorhandene `decision_reasons` bleiben erhalten; Timing-Reasons werden additiv und dedupliziert ergänzt, ohne zufällige Umordnung.

8) `decision`, `risk_acceptable`, `rr_to_tp10`, `rr_to_tp20`, `setup_score`, `global_score`, Sortierung, Rank und die Auswahl der `trade_candidates` bleiben gegenüber derselben Eingabe unverändert.

9) `docs/canonical/OUTPUT_SCHEMA.md` dokumentiert:
   - die neuen Summary-Felder bzw. Summary-Struktur
   - die erlaubten Timing-Reasons
   - die Semantik, dass diese Timing-Reasons zunächst diagnostisch und nicht entscheidungssteuernd sind

10) Markdown-/Excel-Renderer dürfen die neuen Timing-Reasons und/oder Entry-State-Counts anzeigen, müssen aber mindestens konsistent mit dem kanonischen JSON bleiben; sie dürfen keine abweichende Timing-Interpretation erzeugen.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

> Markiere explizit, was dieses Ticket abdeckt. Jeder ✅ braucht einen Verweis auf Acceptance Criteria und Test(s).
> Nicht relevante Punkte werden explizit als N/A markiert.

- **Config Defaults (Missing key → Default):** ✅ N/A – Ticket liest keine neue Config
- **Config Invalid Value Handling:** ✅ N/A – Ticket führt keine neue Config ein
- **Nullability / kein bool()-Coercion:** ✅ (AC: #1, #6; Tests: `entry_state = null`, fehlende Reason-Liste)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #1, #6; Tests: `entry_state = null` erzeugt keinen Timing-Reason)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A – Ticket führt kein neues Write-/Preflight-Verhalten ein
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A – Ticket ändert keine Benennung/Dateinamen
- **Deterministische Sortierung/Tie-Breaker:** ✅ (AC: #7, #8; Tests: deterministische Reason-Reihenfolge und unveränderte Candidate-Sortierung)

## Tests (required if logic changes)
- **Unit:**
  - Test: Summary zählt `entry_state` korrekt für eine gemischte Candidate-Liste mit `early`, `at_trigger`, `late`, `chased`, `null`
  - Test: `entry_state = early` ergänzt genau `entry_too_early`
  - Test: `entry_state = late` ergänzt genau `entry_late`
  - Test: `entry_state = chased` ergänzt genau `entry_chased`
  - Test: `entry_state = at_trigger` ergänzt keinen neuen Timing-Reason
  - Test: `entry_state = null` ergänzt keinen neuen Timing-Reason
  - Test: vorhandene Timing-Reasons werden dedupliziert und nicht doppelt angehängt
  - Test: vorhandene nicht-Timing-Reasons bleiben erhalten und werden nicht verloren
  - Test: Reason-Reihenfolge bleibt deterministisch
- **Integration:**
  - JSON-Report-Test mit mehreren `trade_candidates`, die unterschiedliche `entry_state`-Werte haben
  - Test der Summary-Struktur inkl. Counts
  - Markdown-/Excel-nahe Tests, falls dort Summary- oder Reason-Felder explizit gerendert werden
- **Golden fixture / verification:**
  - Snapshot-/Golden-Test für einen repräsentativen Report mit:
    - unveränderten `decision`-Werten
    - erweiterten `decision_reasons`
    - neuen `entry_state`-Counts in der Summary

## Constraints / Invariants (must not change)
- Keine Änderung an Closed-candle-only-Annahmen
- Kein Lookahead
- Deterministic ordering with stable tie-breakers bleibt erhalten
- Score-Ranges / Scoring-Verhalten bleiben unverändert
- Timestamp-Units bleiben unverändert
- Keine Änderung an Risk-/Decision-/Tradeability-Logik
- Keine Änderung an BTC-Regime-Verhalten
- Keine Änderung an Setup-Scorern
- Keine Änderung an bestehenden Stage-Gates oder Budget-Pfaden

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` (Summary-/Reason-Vertrag präzisiert)
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if required by output-contract verification rules
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-03-09T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
