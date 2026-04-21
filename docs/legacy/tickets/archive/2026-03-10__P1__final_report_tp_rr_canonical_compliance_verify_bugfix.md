> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Final report TP/RR canonical compliance hart absichern und gegen 2026-03-10 regressionsfest verifizieren

## Kontext / Source
Die Canonical-Doku definiert:

> "TP10 and TP20 are orientation targets for reward/risk computation. They DO NOT imply mandatory exits or automated take-profit behavior."

Die fachliche Zielsetzung dahinter ist:
- `tp10_price` und `tp20_price` sind **kanonische RR-Orientierungsziele relativ zum geplanten Entry**
- reale Exits im Live-Trading dürfen früher/später erfolgen
- scorer-/analysis-interne Struktur-Targets dürfen **nicht** stillschweigend die kanonischen TP-Felder speisen

Das vorherige Ticket zur Umstellung auf:
- `tp10_price = entry_price_usdt * 1.10`
- `tp20_price = entry_price_usdt * 1.20`

wurde zwar umgesetzt, aber der reale Daily-Report `reports/2026-03-10.json` zeigt weiterhin effektiv das alte Verhalten:
- `rr_to_tp10` liegt weiterhin systematisch bei ca. `0.5`
- `rr_to_tp20` liegt weiterhin systematisch bei ca. `1.0`
- `analysis.trade_levels.targets` erscheinen weiterhin faktisch als Quelle der kanonischen RR-Semantik im finalen Output

Das bedeutet:
- Entweder ist der Fix im finalen Output-Pfad nicht vollständig wirksam
- oder Snapshot-/Output-Pfade nutzen weiterhin eine alte Ableitung
- oder Golden-/Regression-Absicherung fehlt so, dass die fachlich falsche Ausgabe unbemerkt geblieben ist

Dieses Ticket ist daher ein **eng begrenztes Verify-/Bugfix-Härtungs-Ticket**:
- keine neue Semantik
- keine Config-Änderung
- keine Decision-/Risk-/Tradeability-Änderung
- sondern harte Sicherstellung, dass der **finale Report** die bereits definierte Canonical-Semantik wirklich ausgibt

## Goal
Nach diesem Ticket ist fachlich und testseitig gesichert:

- Der **finale kanonische JSON-Report** verwendet für `trade_candidates.tp10_price` und `trade_candidates.tp20_price` ausschließlich die kanonischen RR-Orientierungsziele aus `entry_price_usdt`
- `rr_to_tp10` und `rr_to_tp20` im finalen Report werden ausschließlich daraus und aus `stop_price_initial` berechnet
- scorer-/analysis-interne Targets bleiben erhalten, beeinflussen aber die kanonischen TP-/RR-Felder nicht
- Ein Run wie `reports/2026-03-10.json`, der weiterhin faktisch `rr_to_tp10 ≈ 0.5` / `rr_to_tp20 ≈ 1.0` für fast alle Kandidaten ausgibt, wird durch Tests oder Verification eindeutig erkannt

## Scope
Erlaubte Änderungen in diesem Ticket:

- `scanner/pipeline/output.py`
- output-nahe Helper, falls TP-/RR-Ableitung dort zentralisiert ist
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`, falls Golden-/Verification-Regeln für TP-/RR explizit ergänzt werden müssen
- output-nahe Tests unter `tests/`
- Markdown-/Excel-Output nur soweit nötig, um konsistent zum kanonischen JSON zu bleiben

Betroffene reale Repo-Pfade, auf die sich dieses Ticket stützt:
- `scanner/pipeline/output.py`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- ggf. `scanner/pipeline/excel_output.py`
- output-nahe Tests unter `tests/`
- Referenz-Report: `reports/2026-03-10.json`

## Out of Scope
Explizit **nicht** Teil dieses Tickets:

- keine Änderung von `min_rr_to_tp10`
- keine Änderung von `min_rr_to_tp20`
- keine Änderung von ATR-/Stop-Regeln
- keine Änderung von `risk_acceptable`-Schwellen
- keine Änderung von `decision.py`
- keine Änderung der Setup-Scorer
- keine Änderung an `analysis.trade_levels.targets`
- keine Änderung an Ranking, Sortierung oder Kandidatenselektion
- keine Änderung an `entry_state`-Klassifikation
- kein neues Threshold-Tuning

## Canonical References (important)
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/INDEX.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Proposed change (high-level)
Beschreibe gewünschtes Verhalten, nicht freie Neuinterpretation:

- **Before:**
  - Die Canonical-Doku definiert `tp10` / `tp20` als RR-Orientierungsziele
  - Der finale Report `reports/2026-03-10.json` zeigt aber weiterhin RR-Werte, die faktisch aus scorer-/analysis-internen Targets stammen oder ihnen entsprechen
  - Die bestehende Test-/Verification-Absicherung hat diesen Drift nicht zuverlässig verhindert
- **After:**
  - Der finale JSON-Output gibt für jeden gültigen `trade_candidate`:
    - `tp10_price = entry_price_usdt * 1.10`
    - `tp20_price = entry_price_usdt * 1.20`
  - `rr_to_tp10` und `rr_to_tp20` werden deterministisch nur aus:
    - `entry_price_usdt`
    - `stop_price_initial`
    - `tp10_price`
    - `tp20_price`
    berechnet
  - `analysis.trade_levels.targets` bleiben separat im Analysis-Bereich erhalten und sind ausdrücklich **nicht** die Quelle der kanonischen TP-/RR-Felder
  - Golden-/Integration-/Verification-Tests decken explizit den Drift-Fall ab, dass im finalen Report wieder scorer-interne Targets statt kanonischer TP-Felder auftauchen
- **Edge cases:**
  - `entry_price_usdt = null`
  - `stop_price_initial = null`
  - `entry_price_usdt <= 0`
  - `stop_price_initial <= 0`
  - `stop_price_initial >= entry_price_usdt`
  - `NaN`, `inf`, `-inf`
  - scorer-interne Targets vorhanden, aber Entry/Stop ungültig
- **Backward compatibility impact:**
  - Keine neue Semantik; dieses Ticket stellt die bereits definierte Canonical-Semantik im finalen Output sicher
  - Snapshot-/Golden-Dateien für TP-/RR-Felder müssen ggf. aktualisiert werden, falls sie bisher den falschen Zustand zementiert haben

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> Diese Sektion ist eine **Ausführungsanweisung** für Codex. Wenn hier etwas nicht eindeutig ist, muss das Ticket angepasst werden. Kein Raten.

- **Config/Defaults:** Dieses Ticket führt **keine neue Konfigurationslogik** ein. Keine neuen Config-Keys, keine Defaults, keine Merge-vs-Replace-Fragen.
- **Raw vs canonical semantics:**
  - `analysis.trade_levels.targets` bleibt ein analysis-/scorer-nahes Rohfeld
  - `trade_candidates.tp10_price` und `trade_candidates.tp20_price` sind ausschließlich die **kanonischen normalisierten RR-Orientierungsziele**
  - scorer-/analysis-interne Targets dürfen die kanonischen TP-Felder **unter keinen Umständen** überschreiben
- **Nullability:**
  - Fehlender/ungültiger `entry_price_usdt` ⇒ `tp10_price = null`, `tp20_price = null`, `rr_to_tp10 = null`, `rr_to_tp20 = null`
  - Fehlender/ungültiger `stop_price_initial` bei gültigem Entry ⇒ `tp10_price` / `tp20_price` bleiben berechenbar, `rr_to_tp10 = null`, `rr_to_tp20 = null`
  - `null` darf nicht zu `0`, `false` oder leerem String koerziert werden
- **Not-evaluated vs failed:**
  - Fehlender oder ungültiger Entry/Stop bedeutet: TP/RR **nicht auswertbar**
  - Das ist semantisch nicht dasselbe wie negatives RR
- **Numeric robustness:**
  - `NaN`, `inf`, `-inf` gelten als ungültige numerische Inputs
  - Solche Werte dürfen nicht in numerisch aussehende TP-/RR-Outputs serialisiert werden
- **RR formula semantics:**
  - Nur Long-Semantik gemäß bestehendem System
  - Risiko pro Einheit = `entry_price_usdt - stop_price_initial`
  - RR wird nur berechnet, wenn diese Differenz strikt `> 0` ist
  - `rr_to_tp10 = (tp10_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
  - `rr_to_tp20 = (tp20_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
  - Wenn Nenner `<= 0`, ist RR `null`
- **Determinismus:**
  - Sortierung, Rank, Decision und Reason-Reihenfolge bleiben unverändert
  - Dieses Ticket ändert nur die Sicherstellung der TP-/RR-Feldausgabe und deren Absicherung
- **Repo-Reality:**
  - Vorhandene Helper zur Entry-/Float-/Sanitization-Ableitung wiederverwenden
  - Keine zweite parallele TP-/RR-Wahrheitsquelle einführen
- **Verification hardening:**
  - Dieses Ticket ist **nicht** erledigt, wenn nur Code geändert wird
  - Es muss mindestens ein Test/Verification-Fall existieren, der den konkreten Drift-Typ erkennt:
    - kanonische TP-Feldnamen vorhanden
    - aber numerische Werte faktisch noch aus scorer-internen Targets / altem RR-Verhalten

## Implementation Notes (optional but useful)
- Ausgangspunkt ist der reale Drift-Fall `reports/2026-03-10.json`
- Ziel ist nicht neue Semantik, sondern Sicherstellung, dass der finale Output-Pfad und die Verification denselben Canonical-Vertrag erzwingen
- Wenn mehrere Output-Pfade existieren (JSON/Markdown/Excel), ist JSON die Quelle der Wahrheit; andere Exporte dürfen davon nicht abweichen

## Acceptance Criteria (deterministic)
1) Für jeden `trade_candidate` mit numerisch endlichem `entry_price_usdt > 0` gilt im finalen JSON:
   - `tp10_price = entry_price_usdt * 1.10`
   - `tp20_price = entry_price_usdt * 1.20`

2) Für jeden `trade_candidate` mit numerisch endlichem `entry_price_usdt > 0` und `stop_price_initial > 0` sowie `stop_price_initial < entry_price_usdt` gilt im finalen JSON:
   - `rr_to_tp10 = (tp10_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
   - `rr_to_tp20 = (tp20_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`

3) Für jeden `trade_candidate` mit fehlendem/ungültigem `entry_price_usdt` sind `tp10_price`, `tp20_price`, `rr_to_tp10`, `rr_to_tp20` = `null`.

4) Für jeden `trade_candidate` mit fehlendem/ungültigem `stop_price_initial` oder `stop_price_initial >= entry_price_usdt` sind `rr_to_tp10`, `rr_to_tp20` = `null`; `tp10_price` und `tp20_price` bleiben aus dem Entry ableitbar, sofern der Entry gültig ist.

5) `analysis.trade_levels.targets` oder andere scorer-interne Target-Felder bleiben, wenn vorhanden, im Analysis-Bereich erhalten, werden aber **nicht** mehr zur Befüllung von `trade_candidates.tp10_price` / `tp20_price` oder `rr_to_tp10` / `rr_to_tp20` verwendet.

6) Mindestens ein Integration- oder Golden-Test deckt explizit einen Kandidaten mit:
   - gültigem `entry_price_usdt`
   - gültigem `stop_price_initial`
   - vorhandenen `analysis.trade_levels.targets`
   ab und verifiziert, dass die finalen TP-/RR-Felder **nicht** den analysis-internen Targets folgen.

7) Mindestens ein Verification-/Regression-Test erkennt den Drift-Typ:
   - Report enthält formal `tp10_price` / `tp20_price`
   - numerisch verhalten sich `rr_to_tp10` / `rr_to_tp20` aber weiterhin wie altes scorer-internes RR
   Dieser Zustand muss testseitig/verification-seitig als Fehler erkennbar sein.

8) `decision`, `decision_reasons`, `risk_pct_to_stop`, `setup_score`, `global_score`, Rank, Sortierung und Auswahl der `trade_candidates` bleiben gegenüber derselben Eingabe unverändert, außer dort, wo Snapshot-/Golden-Tests die korrigierten TP-/RR-Felder abbilden.

9) `docs/canonical/OUTPUT_SCHEMA.md` dokumentiert explizit:
   - `tp10_price` / `tp20_price` als kanonische RR-Orientierungsziele relativ zum Entry
   - dass diese Felder **keine** verpflichtenden Exit-Level und **keine** automatischen Take-Profits sind

10) `docs/canonical/VERIFICATION_FOR_AI.md` beschreibt – falls dieses Dokument bereits Output-/Scoring-Verifikation normiert – einen expliziten Prüfpunkt dafür, dass kanonische TP-/RR-Felder im finalen Report nicht aus scorer-internen Targets gespeist werden.

11) Markdown-/Excel-Renderer dürfen die neuen TP-/RR-Werte anzeigen, müssen aber konsistent mit dem finalen JSON bleiben und dürfen scorer-interne Targets nicht als kanonische `tp10` / `tp20` ausgeben.

12) Nicht-finite numerische Inputs (`NaN`, `inf`, `-inf`) werden nicht als numerische TP-/RR-Werte serialisiert, sondern führen für die betroffenen Felder zu `null`.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

> Markiere explizit, was dieses Ticket abdeckt. Jeder ✅ braucht einen Verweis auf Acceptance Criteria und Test(s).
> Nicht relevante Punkte werden explizit als N/A markiert.

- **Config Defaults (Missing key → Default):** ✅ N/A – Ticket liest keine neue Config
- **Config Invalid Value Handling:** ✅ N/A – Ticket führt keine neue Config ein
- **Nullability / kein bool()-Coercion:** ✅ (AC: #3, #4, #12; Tests: fehlender Entry, ungültiger Stop, `null` bleibt `null`)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #3, #4; Tests: ungültiger Entry/Stop erzeugt `null`, nicht negatives RR)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A – Ticket führt kein neues Write-/Preflight-Verhalten ein
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A – Ticket ändert keine Benennung/Dateinamen
- **Deterministische Sortierung/Tie-Breaker:** ✅ (AC: #8; Tests: unveränderte Candidate-Sortierung)
- **Numerische Robustheit (`NaN`/`inf`/`-inf`):** ✅ (AC: #12; Tests: nicht-finite Inputs führen zu `null`)
- **Raw-vs-canonical Drift-Schutz:** ✅ (AC: #5, #6, #7; Tests: analysis-targets vorhanden, finale TP-/RR-Felder bleiben kanonisch)

## Tests (required if logic changes)
- **Unit:**
  - Test: gültiger Entry `100` ergibt `tp10_price = 110`, `tp20_price = 120`
  - Test: gültiger Entry `100`, Stop `95` ergibt `rr_to_tp10 = 2.0`, `rr_to_tp20 = 4.0`
  - Test: gültiger Entry `100`, Stop `90` ergibt `rr_to_tp10 = 1.0`, `rr_to_tp20 = 2.0`
  - Test: fehlender Entry → `tp10_price`, `tp20_price`, `rr_to_tp10`, `rr_to_tp20` = `null`
  - Test: fehlender Stop → `tp10_price` / `tp20_price` bleiben gesetzt, RR-Felder = `null`
  - Test: Stop `>=` Entry → RR-Felder = `null`
  - Test: `NaN` / `inf` / `-inf` in Entry oder Stop → betroffene TP-/RR-Felder = `null`
  - Test: vorhandene `analysis.trade_levels.targets` überschreiben die kanonischen TP-Felder nicht
- **Integration:**
  - JSON-Report-Test mit mindestens einem Kandidaten mit gültigem Entry/Stop und vorhandenen `analysis.trade_levels.targets`
  - JSON-Report-Test mit ungültigem Stop-Fall
  - Integration-Test, der explizit sicherstellt, dass finaler Report nicht auf altes RR-Muster `~0.5 / ~1.0` zurückfällt, wenn die Inputs andere kanonische RR-Werte implizieren
  - Markdown-/Excel-nahe Tests, falls TP-/RR-Felder dort explizit gerendert werden
- **Golden fixture / verification:**
  - Snapshot-/Golden-Test für einen repräsentativen Report mit:
    - kanonischen `tp10_price` / `tp20_price`
    - daraus abgeleiteten `rr_to_tp10` / `rr_to_tp20`
    - unveränderten Decisions/Ranking-Feldern
  - Verification-Fall gegen den Drift-Typ aus `reports/2026-03-10.json`

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
- [ ] Updated canonical docs under `docs/canonical/` (TP-/RR-Vertrag und Verification präzisiert)
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if output-contract verification rules are touched
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-03-10T00:00:00Z"
priority: P1
type: bugfix
owner: codex
related_issues: []
```
