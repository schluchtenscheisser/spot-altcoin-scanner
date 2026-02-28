> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

#### A) Defaults / Config-Semantik (Pflicht, wenn Config gelesen/validiert wird)
- [x] Kein Config-Change in diesem Ticket.

#### B) Nullability / Schema / Output (Pflicht, wenn Outputs betroffen sind)
- [x] Nullable Felder bleiben nullable: bei `null` werden die Bulletpoints trotzdem ausgegeben, mit `n/a` (keine Coercion zu `0` oder `False`).
- [x] Kein bool()-Coercion.

#### C) Edgecases (Pflicht, wenn relevant)
- [x] Sehr große Werte (global volume) korrekt in **M USD** formatiert.
- [x] Formatierung muss robust gegen `None` sein.

#### D) Tests (Pflicht bei Logikänderungen)
- [x] Mindestens 1 Test: Zahlenformatierung (M USD + %)
- [x] Mindestens 1 Test: `None` ⇒ Bulletpoints existieren + `n/a`

---

## Title
[P2] Markdown-Report: Market-Activity als Bulletpoints + Formatierung (M USD, %)

## Context / Source (optional)
Im Markdown-Report werden aktuell die Market-Activity-Felder in einer Zeile ausgegeben:

`**Market Activity:** global_volume_24h_usd=..., turnover_24h=..., mexc_share_24h=...`

Das ist schwer lesbar. Gewünscht ist eine Darstellung in separaten Bulletpoints, inkl. konsistenter Formatierung.

## Goal
Im Markdown-Report werden `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h` wie folgt dargestellt:

- als **Bulletpoints in separaten Zeilen**
- `global_volume_24h_usd` als gerundete Zahl in **M USD** mit **1 Nachkommastelle**
  - Beispiel: `103,7 M USD`
- `turnover_24h` und `mexc_share_24h` als **%** mit **2 Nachkommastellen**
  - Beispiel: `3,78 %`

## Scope
- `scanner/pipeline/output.py`
  - Methode: `ReportGenerator._format_setup_entry` (Abschnitt „Market Activity“)
  - Ergänze/verwende Helper-Funktionen für Formatierung:
    - `_format_m_usd(value)` → `"103,7 M USD"` (value in USD)
    - `_format_pct(value)` → `"3,78 %"` (value ist Ratio, z.B. 0.0378)
  - Ersetze die aktuelle 1-Zeilen-Ausgabe durch 3 Bulletpoints.

- Unit tests unter `tests/...` (Repo-üblich)

## Out of Scope
- Keine Änderungen am JSON-Report
- Keine Änderungen am Excel-Report
- Keine Änderungen an Scoring/Filtering/Fields (nur Markdown-Rendering)

## Canonical References (important)
- `docs/canonical/OUTPUT_SCHEMA.md` oder `docs/canonical/OUTPUTS/*` (falls Markdown Layout dort kanonisch beschrieben ist)

## Proposed change (high-level)
### Before
Markdown enthält:
- `**Market Activity:** global_volume_24h_usd=..., turnover_24h=..., mexc_share_24h=...`

### After
Markdown enthält:
- `**Market Activity:**`
- `- global_volume_24h_usd: 103,7 M USD`
- `- turnover_24h: 3,78 %`
- `- mexc_share_24h: 1,23 %`

### Formatierungsregeln
- `global_volume_24h_usd`:
  - Input: USD (float)
  - Output: `(value / 1_000_000)` gerundet auf 1 Nachkommastelle + `" M USD"`
- `turnover_24h`, `mexc_share_24h`:
  - Input: Ratio (0..1, float)
  - Output: `(value * 100)` mit 2 Nachkommastellen + `" %"`

### Nullability
- Wenn value `None` ⇒ Ausgabe `n/a` und Bulletpoint rendern:
  - `- turnover_24h: n/a`

## Implementation Notes (optional but useful)
- **Decimal separator:** Output soll **Komma** als Dezimaltrenner haben (wie in den Beispielen), aber ohne Locale-Abhängigkeit.
  - Implementiere deterministisch: formatiere mit Punkt (`f"{x:.1f}"`) und ersetze anschließend `.` → `,`.
- `n/a` als feste Darstellung (klein, deterministisch).

## Acceptance Criteria (deterministic)
1) Market-Activity wird im Markdown-Report als eigener Block mit 3 Bulletpoints ausgegeben.
2) `global_volume_24h_usd` wird als `X,Y M USD` (eine Nachkommastelle, **Komma**) formatiert.
3) `turnover_24h` und `mexc_share_24h` werden als `X,YZ %` (zwei Nachkommastellen, **Komma**) formatiert.
4) Bei `None` wird der Bulletpoint dennoch ausgegeben und zeigt `n/a`, ohne Crash.
5) Keine Änderungen an JSON/Excel Outputs.

## Tests (required if logic changes)
- Unit:
  - `test_format_market_activity_markdown_numbers`:
    - `global_volume_24h_usd=103_700_000` ⇒ `103,7 M USD`
    - `turnover_24h=0.0378` ⇒ `3,78 %`
    - `mexc_share_24h=0.0123` ⇒ `1,23 %`
  - `test_format_market_activity_markdown_none`:
    - Alle drei None ⇒ Bulletpoints vorhanden, jeweils `n/a`

## Constraints / Invariants (must not change)
- Deterministische Report-Ausgabe (kein Locale-Dependency)
- Keine Änderungen an Scoring/Selektion/Ranking

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
priority: P2
type: feature
owner: codex
related_issues: []
```
