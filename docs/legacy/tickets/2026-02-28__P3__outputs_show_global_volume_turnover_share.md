> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

#### A) Defaults / Config-Semantik
- [x] Keine neuen Config-Keys in diesem Ticket (Outcome-neutral Output-Erweiterung).

#### B) Nullability / Schema / Output (Pflicht)
- [x] Neue Output-Felder sind explizit nullable (`null` wenn nicht auswertbar).
- [x] Keine bool()-Coercion für numerische Felder.
- [x] Backward compatible: bestehende Felder bleiben unverändert; neue Felder sind additive.

#### C) Edgecases
- [x] Wenn global volume fehlt ⇒ Felder bleiben `null`, Reports bleiben dennoch generierbar.

#### D) Tests
- [x] Mindestens 1 Test: Report enthält neue Felder (wenn vorhanden)
- [x] Mindestens 1 Test: Report setzt `null` wenn Daten fehlen

---

## Title
[P2] Outputs: global_volume/turnover/mexc_share in Reports (JSON/Markdown/Excel) sichtbar machen (ohne Ranking-Änderung)

## Context / Source (optional)
- Ticket 1 plumbed globale Marktmetriken durch Pipeline und Runtime-Meta.
- Nutzer sollen diese Metriken in den täglichen Reports sehen können, ohne dass Filtering/Scoring verändert wird.

## Goal
- Daily Reports zeigen pro Coin (wo sinnvoll) zusätzliche Felder:
  - `global_volume_24h_usd`
  - `turnover_24h`
  - `mexc_share_24h`
- Gilt für:
  - JSON Report (additive fields)
  - Markdown Report (zusätzliche Spalten oder Abschnitt)
  - Excel Report (zusätzliche Spalten im Setup-/Global-Sheet; keine Layout-Zerstörung)
- **Keine** Änderung an Scoring/Ranking/Top20-Auswahl.

## Scope
- `scanner/pipeline/output.py` (JSON/Markdown Report generator)
- `scanner/pipeline/excel_output.py` (Excel columns)
- `docs/canonical/OUTPUT_SCHEMA.md` (wenn dort Felder/Reportformat kanonisch beschrieben)
- ggf. `docs/canonical/OUTPUTS/EVALUATION_DATASET.md` (falls betroffen)

## Out of Scope
- Filter/Scoring/Thresholds (Tickets 2/3)
- Runtime-Meta-Export (Ticket 1)

## Canonical References (important)
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/OUTPUTS/EVALUATION_DATASET.md`
- `docs/canonical/AUTHORITY.md`

## Proposed change (high-level)
### JSON Report
- **Before:** Output enthält pro Coin die bisherigen Felder (z.B. market_cap, quote_volume_24h, liquidity metrics, scores).
- **After:** Additiv:
  - `global_volume_24h_usd` (nullable)
  - `turnover_24h` (nullable)
  - `mexc_share_24h` (nullable)

### Markdown Report
- Additiver Abschnitt oder zusätzliche Spalten (stabil, deterministisch):
  - Empfehlung: eigener Abschnitt „Market activity“ je Coin oder zusätzliche Spalten in Tabellen, sofern Spaltenbreite ok.
  - Keine Re-Order der bestehenden Spalten ohne Grund.

### Excel
- Additive Spalten in bestehenden Sheets:
  - Wo bereits `market_cap` und `quote_volume_24h` existieren, daneben die neuen Felder einfügen.
  - Formatierung: große Zahlen konsistent mit vorhandener `_format_large_number` (falls vorhanden).
  - Nullable: leere Zelle statt 0.

### Missing vs Invalid
- Missing per-coin metric ⇒ `null`/empty cell (kein Fail)
- Invalid numeric (NaN/negative) ⇒ treat as `null` in report layer (Report darf nicht crashen; Validierung/Filter liegt woanders)

## Acceptance Criteria (deterministic)
1) JSON Report enthält neue Felder additiv, existing keys unverändert.
2) Markdown Report zeigt die Felder deterministisch (gleiches Layout bei gleichen Inputs).
3) Excel Report enthält neue Spalten; leere Zellen bei missing.
4) Keine Änderung am Ranking/Score/Top20 (Outcome-neutral).
5) Canonical Output-Schema ist aktualisiert, falls es Report-Felder explizit spezifiziert.

## Tests (required if logic changes)
- Unit:
  - Report Generator: given minimal fixture coin entry mit den Feldern ⇒ JSON enthält keys
  - Missing fields ⇒ JSON enthält keys mit `null` (keys sind präsent und `null`)
- Golden/verification:
  - Wenn `docs/canonical/OUTPUT_SCHEMA.md` geändert wird: Update `docs/canonical/VERIFICATION_FOR_AI.md` falls dort relevante Checks existieren.

## Constraints / Invariants (must not change)
- Deterministisches Ordering in Markdown/Excel (stable sort/tie-breaks unverändert)
- Keine Änderung an Scores/Selektion

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Canonical docs updated under `docs/canonical/` (falls Output-Schema spezifiziert)
- [ ] Tests hinzugefügt/aktualisiert
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-02-28T00:00:00Z"
priority: P2
type: feature
owner: codex
related_issues: []
```
