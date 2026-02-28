# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

> Dieses Ticket ist **Docs-only**, aber es referenziert **kanonische Semantik** (Defaults/Keys/Fallback) aus bereits umgesetzten Tickets. Keine neuen Entscheidungen treffen.

#### A) Defaults / Config-Semantik (Pflicht, wenn Config dokumentiert wird)
- [x] Defaults müssen **exakt** den beschlossenen/implementierten Werten entsprechen:
  - `universe_filters.volume.min_turnover_24h = 0.03`
  - `universe_filters.volume.min_mexc_quote_volume_24h_usdt = 5_000_000`
  - `universe_filters.volume.min_mexc_share_24h = 0.01`
- [x] Missing vs Invalid muss explizit getrennt werden:
  - Missing key ⇒ Default greift
  - Invalid value ⇒ Validation-Error (fail-fast)
- [x] Legacy-Alias-Regel muss dokumentiert werden:
  - `universe_filters.volume.min_quote_volume_24h` ⇒ Alias für `min_mexc_quote_volume_24h_usdt` (nur wenn neuer Key fehlt)

#### B) Nullability / Schema / Output (Pflicht)
- [x] Neue Felder sind **nullable**: `null` bedeutet „nicht auswertbar“, **nicht** 0.
- [x] Keine `bool()`-Coercion / Truthy-Semantik in der Doku beschreiben.

#### C) Edgecases (Pflicht, wenn relevant)
- [x] Fallback-Regel dokumentieren:
  - Wenn global Turnover nicht berechenbar ⇒ fallback **nur** auf `min_mexc_quote_volume_24h_usdt`
  - `mexc_share_24h` wird im Fallback **nicht** angewendet (nicht berechenbar ohne global volume)

#### D) Tests
- [x] Keine Code-Tests erforderlich (Docs-only). Aber Doku muss konsistent mit Canonical Authority sein.

---

## Title
[P1] Canonical Docs aktualisieren: Global Volume/Turnover/Share + Volume-Gates + Output-Schema (nach Umsetzung Tickets 1–4)

## Context / Source (optional)
Dieses Ticket ist ein **Dokumentations-Follow-up** nachdem die folgenden Tickets bereits umgesetzt wurden:

- Ticket 1: Plumbing der globalen Marktmetriken (`global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h`)
- Ticket 2: Universe-Filter: global Turnover + MEXC-Min + MEXC-Share, inkl. Fallback & Legacy-Alias
- Ticket 3: (optional) Scoring `volume_source` Switch (falls umgesetzt)
- Ticket 4: Outputs (JSON/Markdown/Excel) zeigen die neuen Felder

Ziel: Canonical Docs sollen die **Single Source of Truth** sein (`docs/canonical/*`), Auto-Docs bleiben unangetastet.

## Goal
- Alle relevanten **kanonischen** Dokumente unter `docs/canonical/` sind aktualisiert und konsistent mit dem implementierten Verhalten aus Tickets 1–4:
  - Neue Felder/Derivations
  - Neue Config Keys + Defaults + Valid ranges
  - Gate-Logik + Fallback + Legacy-Alias
  - Output-Schema-Erweiterungen (Reports + runtime meta export)
- **Auto-Docs nicht editieren** (`docs/code_map.md`, `docs/GPT_SNAPSHOT.md`).

## Scope
### Canonical Docs (müssen geprüft & bei Bedarf aktualisiert werden)
1) `docs/canonical/CONFIGURATION.md`
   - Keys & Defaults unter `universe_filters.volume` ergänzen:
     - `min_turnover_24h: 0.03`
     - `min_mexc_quote_volume_24h_usdt: 5000000`
     - `min_mexc_share_24h: 0.01`
   - Meaning/Units/Valid ranges dokumentieren:
     - turnover: ratio (0..∞), default 0.03
     - mexc quote volume: USDT (>=0), default 5_000_000
     - mexc share: ratio [0..1], default 0.01
   - Legacy-Alias `min_quote_volume_24h` dokumentieren (Migrationsregel).
   - Missing vs Invalid Verhalten explizit: Default vs fail-fast.

2) `docs/canonical/DATA_SOURCES.md`
   - CMC liefert `quote.USD.volume_24h` als Quelle für `global_volume_24h_usd` (USD).
   - Ableitungen dokumentieren (nullable):
     - `turnover_24h = global_volume_24h_usd / market_cap_usd`
     - `mexc_share_24h = mexc_quote_volume_24h_usdt / global_volume_24h_usd`

3) `docs/canonical/PIPELINE.md`
   - Universe-Filtering Abschnitt aktualisieren:
     - Deterministische Gate-Reihenfolge
     - Primary path: turnover + mexc-min + mexc-share
     - Fallback: global turnover nicht berechenbar ⇒ mexc-min only (share nicht prüfen)
     - Verhalten bei invalid per-symbol Daten (drop) dokumentieren (keine silent corrections)

4) Output-Doku (je nach Repo-Layout)
   - `docs/canonical/OUTPUT_SCHEMA.md` **oder** relevante Output-Dokumente unter `docs/canonical/OUTPUTS/`
   - Reports (JSON/Markdown/Excel) additiv erweitern:
     - `global_volume_24h_usd` (nullable)
     - `turnover_24h` (nullable)
     - `mexc_share_24h` (nullable)
   - `docs/canonical/OUTPUTS/RUNTIME_MARKET_META_EXPORT.md` (falls vorhanden):
     - Schema additiv erweitern (nullable fields)

5) Schema-Change Log (laut `docs/AGENTS.md`)
   - `docs/SCHEMA_CHANGES.md` aktualisieren:
     - Additive Felder (Reports/runtime meta) dokumentieren
     - Additive Config Keys dokumentieren
   - Falls ein `schema_version` Prozess existiert/benutzt wird:
     - Version bump + Eintrag in `docs/SCHEMA_CHANGES.md`
     - **Nur** falls tatsächlich Bestandteil des Projekts.

6) Optional: Scoring Doku (nur wenn Ticket 3 implementiert wurde)
   - `docs/canonical/SCORING/*` (z.B. breakout_trend_1_5d):
     - `scoring.volume_source` (mexc vs global_fallback_mexc) dokumentieren
     - Default bleibt mexc (backward compatible)

## Out of Scope
- Keine Code-Änderungen
- Keine Änderungen an Auto-Docs (`docs/code_map.md`, `docs/GPT_SNAPSHOT.md`)
- Keine neuen Parameter/Defaults/Regeln definieren (nur dokumentieren, was implementiert ist)

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/INDEX.md`
- `docs/AGENTS.md`

## Proposed change (high-level)
- Aktualisiere Canonical Dokumente so, dass ein Leser ohne Code-Lesen versteht:
  - Woher global volume kommt, wie turnover/share berechnet werden, wann `null` entsteht
  - Welche Universe-Filter-Gates existieren, welche Defaults gelten, wie Fallback/Legacy funktioniert
  - Wo die neuen Felder in Outputs auftauchen (inkl. Nullability)

## Acceptance Criteria (deterministic)
1) Canonical Docs nennen exakt die implementierten Defaults: `0.03`, `5_000_000`, `0.01`.
2) Missing vs Invalid ist klar getrennt (Defaults vs fail-fast).
3) Fallback-Regel ist explizit dokumentiert:
   - turnover nicht berechenbar ⇒ mexc-min only
   - mexc-share wird im Fallback nicht angewendet
4) Output-Doku listet `global_volume_24h_usd`, `turnover_24h`, `mexc_share_24h` als additive nullable Felder für JSON/Markdown/Excel + runtime meta export.
5) `docs/SCHEMA_CHANGES.md` enthält einen additiven Eintrag für Output+Config Erweiterungen (und ggf. schema_version bump, falls im Projekt vorgesehen).
6) Auto-Docs bleiben unverändert.

## Tests (required if logic changes)
- Keine (Docs-only).
- Falls `docs/canonical/VERIFICATION_FOR_AI.md` explizite Checks für betroffene Bereiche enthält, diese aktualisieren (nur wenn relevant).

## Constraints / Invariants (must not change)
- Canonical precedence wahren: Änderungen in `docs/canonical/*` sind maßgeblich.
- Keine neuen Regeln/Defaults einführen – nur implementiertes Verhalten dokumentieren.
- Auto-Docs nicht anfassen.

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Canonical Docs aktualisiert (CONFIGURATION, DATA_SOURCES, PIPELINE, OUTPUT docs)
- [ ] `docs/SCHEMA_CHANGES.md` aktualisiert (Output/Config additiv)
- [ ] Auto-Docs unverändert (`docs/code_map.md`, `docs/GPT_SNAPSHOT.md`)
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-02-28T00:00:00Z"
priority: P1
type: docs
owner: codex
related_issues: []
```
