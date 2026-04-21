> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Canonical TP10/TP20: RR-Orientierungsziele auf Entry×1.10 / Entry×1.20 umstellen

## Kontext / Source
Die Canonical-Doku definiert `tp10` und `tp20` wie folgt:

> "TP10 and TP20 are orientation targets for reward/risk computation. They DO NOT imply mandatory exits or automated take-profit behavior."

Zusätzliche fachliche Zielsetzung des Autors:
- Die 10–20 % sind eine **Richtgröße** für die RR-Bewertung
- Reale Exits dürfen im Live-Trading natürlich früher erfolgen, wenn der Markt weniger hergibt oder kippt
- `tp10` / `tp20` sind also **keine** scorer-internen Struktur-Targets, sondern kanonische RR-Orientierungsziele relativ zum geplanten Entry

Aktueller Ist-Zustand:
- `trade_candidates.entry_price_usdt` ist inzwischen korrekt als geplanter Entry modelliert
- `trade_candidates.tp10_price` / `tp20_price` werden aber weiterhin aus scorer-/analysis-internen Targets gespeist
- Dadurch liegen `rr_to_tp10` im aktuellen Report systematisch um ~0.5 und `rr_to_tp20` um ~1.0, auch bei Kandidaten mit sehr kleinem Stop
- Das kollidiert mit der Canonical-Bedeutung von `tp10` / `tp20`

Dieses Ticket ist daher ein **Canonical-Compliance-/Bugfix-Ticket**.  
Es korrigiert die Semantik der kanonischen `tp10_price` / `tp20_price`-Felder und der daraus abgeleiteten RR-Felder.

## Goal
Nach diesem Ticket gilt im kanonischen Output:

- `tp10_price` ist immer der **10%-Orientierungswert relativ zum geplanten Entry**
- `tp20_price` ist immer der **20%-Orientierungswert relativ zum geplanten Entry**
- `rr_to_tp10` und `rr_to_tp20` werden gegen diese kanonischen Orientierungsziele gerechnet
- scorer-interne / analysis-interne Targets bleiben getrennt und dürfen die kanonischen `tp10` / `tp20`-Felder nicht mehr speisen

## Scope
Erlaubte Änderungen in diesem Ticket:

- `scanner/pipeline/output.py`
- output-nahe Helper, falls RR-/TP-Ableitung dort zentralisiert wird
- `docs/canonical/OUTPUT_SCHEMA.md`
- ggf. weitere Canonical-Doku, falls `tp10` / `tp20` dort erläutert werden
- Markdown-/Excel-Output, soweit diese Candidate-Felder explizit rendern
- output-nahe Tests unter `tests/`

Betroffene reale Repo-Pfade, auf die sich dieses Ticket stützt:
- `scanner/pipeline/output.py`
- `docs/canonical/OUTPUT_SCHEMA.md`
- ggf. `scanner/pipeline/excel_output.py`
- output-nahe Tests unter `tests/`

## Out of Scope
Explizit **nicht** Teil dieses Tickets:

- keine Änderung von `min_rr_to_tp10`
- keine Änderung von `min_rr_to_tp20`
- keine Änderung von ATR-/Stop-Regeln
- keine Änderung von `risk_acceptable`-Schwellen
- keine Änderung von `decision.py`
- keine Änderung der Setup-Scorer
- keine Änderung scorer-interner Targets unter `analysis.trade_levels.targets`
- keine Änderung realer Exit-/Trade-Management-Logik
- keine Änderung an Ranking, Sortierung oder Kandidatenselektion

## Canonical References (important)
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/INDEX.md`

## Proposed change (high-level)
Beschreibe gewünschtes Verhalten, nicht freie Neuinterpretation:

- **Before:**
  - `tp10_price` / `tp20_price` im kanonischen `trade_candidates`-Output können aus analysis-/scorer-internen Targets stammen
  - `rr_to_tp10` / `rr_to_tp20` werden dadurch faktisch gegen diese internen Targets gerechnet
  - Die Feldnamen `tp10` / `tp20` suggerieren aber kanonische 10%/20%-Orientierungsziele
- **After:**
  - `tp10_price = entry_price_usdt * 1.10`
  - `tp20_price = entry_price_usdt * 1.20`
  - `rr_to_tp10` wird aus `entry_price_usdt`, `stop_price_initial` und `tp10_price` berechnet
  - `rr_to_tp20` wird aus `entry_price_usdt`, `stop_price_initial` und `tp20_price` berechnet
  - scorer-/analysis-interne Targets bleiben, wenn vorhanden, separat unter ihrer bisherigen analysis-Struktur erhalten
  - scorer-/analysis-interne Targets dürfen **nicht** mehr stillschweigend die kanonischen `tp10_price` / `tp20_price`-Felder überschreiben
- **Edge cases:**
  - `entry_price_usdt = null`
  - `stop_price_initial = null`
  - `entry_price_usdt <= 0`
  - `stop_price_initial <= 0`
  - `stop_price_initial >= entry_price_usdt`
  - nicht-finite numerische Werte (`NaN`, `inf`, `-inf`)
- **Backward compatibility impact:**
  - Kanonische `tp10_price` / `tp20_price`-Werte im JSON ändern sich
  - `rr_to_tp10` / `rr_to_tp20` ändern sich entsprechend
  - scorer-interne Targets in `analysis` bleiben separat und sind kein Breaking Change, solange sie nicht mehr als kanonische `tp10` / `tp20` verkauft werden

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> Diese Sektion ist eine **Ausführungsanweisung** für Codex. Wenn hier etwas nicht eindeutig ist, muss das Ticket angepasst werden. Kein Raten.

- **Config/Defaults:** Dieses Ticket führt **keine neue Konfigurationslogik** ein. Keine neuen Config-Keys, keine neuen Defaults.
- **Raw vs canonical semantics:**
  - `analysis.trade_levels.targets` bleibt ein analysis-/scorer-nahes Rohfeld
  - `trade_candidates.tp10_price` und `trade_candidates.tp20_price` sind nach diesem Ticket **kanonische normalisierte RR-Orientierungsziele**
  - Roh-Targets und kanonische TP-Felder dürfen semantisch nicht vermischt werden
- **Nullability:**
  - Wenn `entry_price_usdt` fachlich nicht auswertbar ist, dann sind `tp10_price`, `tp20_price`, `rr_to_tp10`, `rr_to_tp20` = `null`
  - Wenn `stop_price_initial` fachlich nicht auswertbar ist, dann sind `rr_to_tp10`, `rr_to_tp20` = `null`
  - `null` darf nicht implizit zu `0`, `false` oder leeren Strings koerziert werden
- **Not-evaluated vs failed:**
  - Fehlender oder ungültiger Entry/Stop bedeutet: RR/TP **nicht auswertbar**
  - Das ist semantisch nicht dasselbe wie „negatives RR“
- **Numeric robustness:**
  - Nicht-finite Werte (`NaN`, `inf`, `-inf`) für Entry/Stop dürfen nicht in numerische Outputs durchgereicht werden
  - Solche Inputs führen für die betroffenen kanonischen TP-/RR-Felder zu `null`
- **RR formula semantics:**
  - Für Long-Setups ist Risiko pro Einheit `entry_price_usdt - stop_price_initial`
  - Nur wenn diese Differenz strikt `> 0` ist, darf RR berechnet werden
  - `rr_to_tp10 = (tp10_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
  - `rr_to_tp20 = (tp20_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
  - Wenn Nenner `<= 0`, ist RR `null`
- **Determinismus:** Sortierung, Rank, Decision und Reason-Reihenfolge bleiben unverändert. Dieses Ticket ändert nur TP-/RR-Semantik.
- **Repo-Reality:** Vorhandene Sanitization-/Float-Helper wiederverwenden; keine zweite parallele Wahrheitsquelle für Entry-Ableitung einführen.

## Implementation Notes (optional but useful)
- `entry_price_usdt` ist bereits der korrekte geplante Entry
- `tp10_price` / `tp20_price` sollen konsequent daraus abgeleitet werden
- scorer-interne Targets können für Analyse nützlich bleiben, aber nicht mehr die kanonischen TP-Felder speisen
- Das Ticket ist erfolgreich, wenn die kanonische RR-Bewertung mit der Doku konsistent ist, nicht wenn dadurch automatisch mehr `ENTER` entstehen

## Acceptance Criteria (deterministic)
1) Für jeden `trade_candidate` mit numerisch endlichem `entry_price_usdt > 0` gilt:
   - `tp10_price = entry_price_usdt * 1.10`
   - `tp20_price = entry_price_usdt * 1.20`

2) Für jeden `trade_candidate` mit numerisch endlichem `entry_price_usdt > 0` und `stop_price_initial > 0` sowie `stop_price_initial < entry_price_usdt` gilt:
   - `rr_to_tp10 = (tp10_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
   - `rr_to_tp20 = (tp20_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`

3) Für jeden `trade_candidate` mit fehlendem/ungültigem `entry_price_usdt` sind `tp10_price`, `tp20_price`, `rr_to_tp10`, `rr_to_tp20` = `null`.

4) Für jeden `trade_candidate` mit fehlendem/ungültigem `stop_price_initial` oder `stop_price_initial >= entry_price_usdt` sind `rr_to_tp10`, `rr_to_tp20` = `null`; `tp10_price` und `tp20_price` bleiben aus dem Entry ableitbar, sofern der Entry gültig ist.

5) `analysis.trade_levels.targets` oder andere scorer-interne Target-Felder bleiben, wenn vorhanden, im analysis-Bereich erhalten, werden aber **nicht** mehr zur Befüllung von `trade_candidates.tp10_price` / `tp20_price` verwendet.

6) `decision`, `decision_reasons`, `risk_pct_to_stop`, `setup_score`, `global_score`, Rank, Sortierung und Auswahl der `trade_candidates` bleiben gegenüber derselben Eingabe unverändert, außer dort, wo Snapshot-/Golden-Tests die korrigierten TP-/RR-Felder abbilden.

7) `docs/canonical/OUTPUT_SCHEMA.md` dokumentiert explizit:
   - `tp10_price` / `tp20_price` als kanonische RR-Orientierungsziele relativ zum Entry
   - dass diese Felder **keine** verpflichtenden Exit-Level und **keine** automatischen Take-Profits sind

8) Markdown-/Excel-Renderer dürfen die neuen kanonischen TP-/RR-Werte anzeigen, müssen aber konsistent mit dem JSON bleiben und dürfen scorer-interne Targets nicht als kanonische `tp10` / `tp20` ausgeben.

9) Nicht-finite numerische Inputs (`NaN`, `inf`, `-inf`) werden nicht als numerische TP-/RR-Werte serialisiert, sondern führen für die betroffenen Felder zu `null`.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

> Markiere explizit, was dieses Ticket abdeckt. Jeder ✅ braucht einen Verweis auf Acceptance Criteria und Test(s).
> Nicht relevante Punkte werden explizit als N/A markiert.

- **Config Defaults (Missing key → Default):** ✅ N/A – Ticket liest keine neue Config
- **Config Invalid Value Handling:** ✅ N/A – Ticket führt keine neue Config ein
- **Nullability / kein bool()-Coercion:** ✅ (AC: #3, #4, #9; Tests: fehlender Entry, ungültiger Stop, `null` bleibt `null`)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #3, #4; Tests: ungültiger Entry/Stop erzeugt `null`, nicht negatives RR)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A – Ticket führt kein neues Write-/Preflight-Verhalten ein
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A – Ticket ändert keine Benennung/Dateinamen
- **Deterministische Sortierung/Tie-Breaker:** ✅ (AC: #6; Tests: unveränderte Candidate-Sortierung)

## Tests (required if logic changes)
- **Unit:**
  - Test: gültiger Entry `100` ergibt `tp10_price = 110`, `tp20_price = 120`
  - Test: gültiger Entry `100`, Stop `95` ergibt `rr_to_tp10 = 2.0`, `rr_to_tp20 = 4.0`
  - Test: gültiger Entry `100`, Stop `90` ergibt `rr_to_tp10 = 1.0`, `rr_to_tp20 = 2.0`
  - Test: fehlender Entry → `tp10_price`, `tp20_price`, `rr_to_tp10`, `rr_to_tp20` = `null`
  - Test: fehlender Stop → `tp10_price` / `tp20_price` bleiben gesetzt, RR-Felder = `null`
  - Test: Stop `>=` Entry → RR-Felder = `null`
  - Test: `NaN` / `inf` / `-inf` in Entry oder Stop → betroffene TP-/RR-Felder = `null`
  - Test: scorer-interne `analysis.trade_levels.targets` bleiben erhalten, überschreiben aber die kanonischen TP-Felder nicht
- **Integration:**
  - JSON-Report-Test mit mindestens einem Kandidaten mit gültigem Entry/Stop
  - JSON-Report-Test mit ungültigem Stop-Fall
  - Markdown-/Excel-nahe Tests, falls TP-/RR-Felder dort explizit gerendert werden
- **Golden fixture / verification:**
  - Snapshot-/Golden-Test für einen repräsentativen Report mit:
    - kanonischen `tp10_price` / `tp20_price`
    - daraus abgeleiteten `rr_to_tp10` / `rr_to_tp20`
    - unveränderten Decisions/Ranking-Feldern

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
- [ ] Updated canonical docs under `docs/canonical/` (TP-/RR-Vertrag präzisiert)
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if required by output-contract verification rules
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-03-09T00:00:00Z"
priority: P1
type: bugfix
owner: codex
related_issues: []
```
