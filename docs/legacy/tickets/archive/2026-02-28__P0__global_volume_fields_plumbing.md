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
- [x] Kein Config-Change in diesem Ticket (nur Plumbing). Keine neuen Defaults notwendig.

#### B) Nullability / Schema / Output (Pflicht, wenn Outputs betroffen sind)
- [x] Nullable Felder explizit: `None`/`null` bedeutet „nicht auswertbar“, nicht „0“.
- [x] Kein bool()-Coercion: keine impliziten `bool(x)` für numerische Felder.

#### C) Edgecases, die oft übersehen werden (Pflicht, wenn relevant)
- [x] Missing CMC volume ⇒ `None`
- [x] Division-by-zero (market_cap=0 oder global_volume=0) ⇒ derived `None`

#### D) Tests (Pflicht bei Logikänderungen)
- [x] Mindestens 1 Test: Missing key ⇒ Default/None greift
- [x] Mindestens 1 Test: Invalid value ⇒ klarer Reason/None
- [x] Mindestens 1 Test: Edgecase Division-by-zero

---

## Title
[P1] Globales 24h-Volumen (CMC) + Turnover + MEXC-Share plumbed (ohne Filter/Scoring-Änderung)

## Context / Source (optional)
- Aktuell wird im Universe/Filters nur `quote_volume_24h` aus MEXC genutzt; CMC wird bereits gemappt, aber globales 24h-Volumen wird nicht in `symbols_with_data`, `features` oder Runtime-Meta durchgereicht.
- Ziel: Daten verfügbar machen, ohne Filter/Scoring-Verhalten zu ändern.

## Goal
- Pipeline berechnet und führt für gemappte Symbole folgende Felder durch:
  - `global_volume_24h_usd` (float | None)
  - `turnover_24h` = `global_volume_24h_usd / market_cap` (float | None)
  - `mexc_share_24h` = `mexc_quote_volume_24h_usdt / global_volume_24h_usd` (float | None)
- Runtime-Meta-Export enthält die Felder pro Coin.

## Scope
- `scanner/pipeline/__init__.py` (Erweiterung `symbols_with_data`, Enrichment von `features`)
- `scanner/pipeline/runtime_market_meta.py` (Export der neuen Felder)
- Unit-Tests unter `tests/…` (Repo-üblich)

## Out of Scope
- Keine Änderungen an Universe-Filtern / Scoring / Thresholds
- Keine neuen Config-Keys

## Canonical References (important)
- `docs/canonical/DATA_SOURCES.md`
- `docs/canonical/OUTPUTS/RUNTIME_MARKET_META_EXPORT.md` (falls Schema dort kanonisch definiert ist)
- `docs/canonical/VERIFICATION_FOR_AI.md` (nur falls canonical output schema betroffen)

## Proposed change (high-level)
- **Before:** `symbols_with_data` enthält `quote_volume_24h` (MEXC) + `market_cap` (CMC).
- **After:** + `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h` (alle nullable).
- **Edge cases:**
  - CMC `quote.USD.volume_24h` missing/None ⇒ `global_volume_24h_usd=None`, abgeleitete Felder None
  - `market_cap` missing/0 ⇒ `turnover_24h=None`
  - `global_volume_24h_usd` missing/0 ⇒ `mexc_share_24h=None`
- **Backward compatibility impact:** keine bestehenden Keys entfernen oder umbenennen.

## Implementation Notes (optional but useful)
- **Nullability:** strikt `None` statt `0` für „nicht auswertbar“.
- Runtime-Meta: neue Felder stabil benennen (snake_case) und explizit serialisieren.

## Acceptance Criteria (deterministic)
1) Bei einem Symbol mit CMC `volume_24h` und `market_cap` sind alle Felder korrekt berechnet.
2) Bei missing CMC `volume_24h` sind `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h` **None**.
3) Bei `market_cap==0` ist `turnover_24h` **None**.
4) Bei `global_volume_24h_usd==0` ist `mexc_share_24h` **None**.
5) Runtime-Meta-Export enthält die neuen Felder pro Coin.

## Tests (required if logic changes)
- Unit:
  - Happy path: extrahiert CMC volume, berechnet turnover + share
  - Missing key: volume fehlt ⇒ alle derived None
  - Division-by-zero: market_cap=0 ⇒ turnover None; global_volume=0 ⇒ share None
- Golden fixture / verification:
  - Wenn `docs/canonical/OUTPUTS/RUNTIME_MARKET_META_EXPORT.md` geändert wird: Update `docs/canonical/VERIFICATION_FOR_AI.md`.

## Constraints / Invariants (must not change)
- Keine Änderung an Filter-/Scoring-Entscheidungen
- Keine Änderung an deterministischer Reihenfolge

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Canonical docs updated under `docs/canonical/` **nur wenn** Output-Schema verändert wurde
- [ ] Tests hinzugefügt/aktualisiert
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-02-28T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
