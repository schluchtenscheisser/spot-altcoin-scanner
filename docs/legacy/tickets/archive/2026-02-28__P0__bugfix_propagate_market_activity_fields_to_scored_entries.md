> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

> Ziel: Codex soll nicht interpretieren müssen. Deshalb müssen Defaults, Missing-Keys, Nullability und „nicht evaluiert“ vs „evaluiert aber fehlgeschlagen“ explizit im Ticket stehen und getestet werden.

#### A) Defaults / Config-Semantik (Pflicht, wenn Config gelesen/validiert wird)
- [x] **Kein** neues Config in diesem Ticket (Bugfix in Datenweitergabe). Keine Defaults.

#### B) Nullability / Schema / Output (Pflicht, wenn Outputs betroffen sind)
- [x] **Nullable Felder explizit:** `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h` sind **immer vorhanden** in scored entries und dürfen `null` sein, wenn nicht auswertbar.
- [x] **Kein bool()-Coercion:** `None/null` bleibt `null`, wird nicht in `False`/`0` umgewandelt.

#### C) Edgecases, die oft übersehen werden (Pflicht, wenn relevant)
- [x] Entry ohne `symbol` ⇒ setze alle drei Felder auf `null` (Keys sind trotzdem vorhanden).
- [x] `symbol` nicht in `features` ⇒ setze alle drei Felder auf `null`.
- [x] `features[symbol]` enthält Feld nicht (missing) ⇒ setze Feld auf `null` (keine Exceptions, keine Defaults wie `0`).

#### D) Tests (Pflicht bei Logikänderungen)
- [x] Mindestens 1 Test: Symbol vorhanden ⇒ Werte werden übernommen
- [x] Mindestens 1 Test: Symbol fehlt/unknown ⇒ Keys existieren und sind `null`
- [x] Mindestens 1 Test: Field missing in features ⇒ `null` (ohne Crash)

---

## Title
[P0] Bugfix: Market-Activity-Felder (global_volume/turnover/mexc_share) in scored entries propagieren (Option A: always present nullable)

## Context / Source (optional)
Nach Umsetzung der Tickets 1–4 werden `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h` in der Pipeline berechnet (siehe `scanner/pipeline/__init__.py`, Step 9), und sind z.B. im runtime meta export vorhanden.

Problem: In den Report-Outputs (JSON/Markdown/Excel) erscheinen diese Felder bei Setups durchgehend als `null`. Ursache ist, dass die Scoring-Result-Entries diese Felder nicht enthalten; der `ReportGenerator` kann nur `entry.get(...)` ausgeben.

User-Entscheidung: **Option A** — Felder sollen pro scored entry **immer vorhanden** sein und bei fehlender Datenlage `null` sein (nicht fehlen, nicht 0).

## Goal
- Alle scored entries, die in Reports geschrieben werden, enthalten **immer** die Keys:
  - `global_volume_24h_usd`
  - `turnover_24h`
  - `mexc_share_24h`
- Die Werte stammen aus `features[symbol]` (Single Source of Truth) und sind `null`, wenn nicht verfügbar.
- Keine Änderung an Ranking/Scoring/Selektion — nur Feld-Propagation.

## Scope
- `scanner/pipeline/__init__.py`
  - Nach den Scoring-Aufrufen (reversal/breakout/pullback + global_top20) und **vor** `ReportGenerator.save_reports(...)` einen Enrichment-Step einfügen.
  - Helper-Funktion z.B. `_enrich_scored_entries_with_market_activity(entries, features)` (Name beliebig, aber zentral und wiederverwendbar).

- Tests unter `tests/...` (Repo-üblich)
  - Unit-Tests für den Enrichment-Helper.

## Out of Scope
- Keine Änderungen an Scoring-Algorithmen/Thresholds
- Keine Änderungen an Universe-Filtern
- Keine Änderungen an runtime meta export (bereits korrekt)
- Keine Änderungen an Output-Formatierung im `ReportGenerator` (der ist bereits vorbereitet)

## Canonical References (important)
- `docs/canonical/PIPELINE.md` (Pipeline stage: scoring → reports)
- `docs/canonical/OUTPUT_SCHEMA.md` oder `docs/canonical/OUTPUTS/*` (falls Output-Felder dort kanonisch beschrieben sind)
- `docs/SCHEMA_CHANGES.md` (nur falls tatsächlich neue Felder eingeführt würden — in diesem Ticket **nicht** der Fall)

## Proposed change (high-level)
### Before
- `features[symbol]` enthält `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h`.
- Scoring-Funktionen geben result entries zurück, die diese Felder nicht enthalten.
- Reports zeigen daher für alle Setups `null`.

### After
- Direkt vor dem Report-Write werden alle Ergebnislisten enriched:
  - `reversal_results`
  - `breakout_results`
  - `pullback_results`
  - `global_top20`
- Für jedes `entry`:
  - `symbol = entry.get("symbol")`
  - `f = features.get(symbol, {})`
  - Setze **immer**:
    - `entry["global_volume_24h_usd"] = f.get("global_volume_24h_usd")`
    - `entry["turnover_24h"] = f.get("turnover_24h")`
    - `entry["mexc_share_24h"] = f.get("mexc_share_24h")`
  - Wenn `symbol` fehlt/unknown ⇒ alle drei `null`.

### Edge cases
- Fehlende `symbol`-Keys: Keine Exception; Felder werden auf `null` gesetzt.
- Missing Felder in `features`: `null` (keine Coercion auf `0`).

### Backward compatibility impact
- Additiv / stabil: Keys existieren bereits im ReportGenerator; dieses Ticket sorgt nur dafür, dass sie in den Entries befüllt werden.
- Report-Schema ändert sich nicht (Keys existierten bereits), nur Werte (von `null` → ggf. Zahl).

## Implementation Notes (optional but useful)
- Keine zusätzlichen API Calls / Budgets.
- Determinismus: Enrichment darf nicht sortieren oder Scores verändern.
- Am besten eine kleine helper function + re-use für alle Ergebnislisten.

## Acceptance Criteria (deterministic)
1) Für jedes Entry in `reversal_results`, `breakout_results`, `pullback_results`, `global_top20` sind die Keys
   `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h` **immer vorhanden**.
2) Wenn `features[symbol]` Werte enthält, werden diese Werte in den Entry übernommen (numerisch/nullable unverändert).
3) Wenn `symbol` fehlt oder `features` keinen Eintrag hat, sind die Werte `null` (Keys bleiben vorhanden).
4) Reports (JSON/Markdown/Excel) zeigen danach nicht mehr “überall null”, sofern `features` Werte liefern.
5) Keine Änderung an Scores, Reihenfolge, Top-N Auswahl oder Confluence-Regeln.

## Tests (required if logic changes)
- Unit:
  - `test_enrich_market_activity_happy_path`: Entry mit `symbol`, features hat Werte ⇒ entry erhält Werte.
  - `test_enrich_market_activity_missing_symbol`: Entry ohne symbol ⇒ keys existieren, values `None`.
  - `test_enrich_market_activity_unknown_symbol_or_missing_field`: symbol vorhanden, aber features missing/field missing ⇒ `None`.

- Integration (optional):
  - Minimaler pipeline smoke test: mocked features + mocked score results → report entries enthalten keys.

- Golden fixture / verification:
  - Nicht erforderlich, solange keine scoring/threshold/curve geändert wird.

## Constraints / Invariants (must not change)
- Closed-candle-only / no-lookahead unverändert
- Deterministische Reihenfolge & Tie-breaks unverändert
- Score ranges 0..100 unverändert
- Keine zusätzlichen Netzwerkanfragen

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Tests hinzugefügt/aktualisiert
- [ ] CI must pass (`python -m pytest -q`)
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-02-28T00:00:00Z"
priority: P0
type: bugfix
owner: codex
related_issues: []
```
