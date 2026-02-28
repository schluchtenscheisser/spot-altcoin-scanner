> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

#### A) Defaults / Config-Semantik (Pflicht, wenn Config gelesen/validiert wird)
- [x] **Kein raw-dict Default drift:** Defaults müssen in `ScannerConfig` und Canonical Config Doc konsistent sein.
- [x] **Missing vs Invalid getrennt:**
  - Missing config key ⇒ Default greift
  - Invalid config value ⇒ klarer Validation-Error (fail-fast)
- [x] **Keine silent fallbacks** außer explizit dokumentiert (hier: global-metric missing ⇒ fallback nur auf mexc-min)

#### B) Nullability / Schema / Output (Pflicht, wenn Outputs betroffen sind)
- [x] Nullable Felder explizit: `None`/`null` bedeutet „nicht auswertbar“, nicht „0“.
- [x] Kein bool()-Coercion.

#### C) Edgecases (Pflicht, wenn relevant)
- [x] Turnover nicht berechenbar ⇒ Fallback (nur MEXC-Min).
- [x] `mexc_share_24h` wird im Fallback **nicht** angewendet (nicht berechenbar ohne global volume).

#### D) Tests (Pflicht bei Logikänderungen)
- [x] Missing key ⇒ Default greift
- [x] Invalid value ⇒ klarer Validation-Error
- [x] Edgecases turnover/share

---

## Title
[P0] Universe-Volume-Gates: global Turnover (CMC) + MEXC-Min + MEXC-Share, mit definiertem Fallback

## Context / Source (optional)
- Volume-Gate war exchange-spezifisch (MEXC). Ziel: globale Marktqualität via Turnover + Execution via MEXC.
- Entscheidungen (User):
  - Global gate: Turnover
  - MEXC gate: Minimum + mexc_share
  - Missing global: Fallback auf MEXC-Min only

## Goal
Universe-Liquidity Filter nutzt:
- **Global gate (primär):** `turnover_24h >= 0.03`
- **MEXC gate:** `mexc_quote_volume_24h_usdt >= 5_000_000`
- **MEXC share gate:** `mexc_share_24h >= 0.01`
- **Fallback policy (wenn global turnover nicht berechenbar):**
  - Nutze **nur** `mexc_quote_volume_24h_usdt >= 5_000_000`
  - `mexc_share_24h` wird in Fallback nicht angewendet

## Scope
- `config/config.yml`
- `scanner/config.py` (Properties + validate_config)
- `scanner/pipeline/filters.py`
- `docs/canonical/CONFIGURATION.md`
- ggf. `docs/canonical/PIPELINE.md` (Gate-Definition)

## Out of Scope
- Scoring (separates Ticket)
- Orderbook/Slippage Stage

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/DATA_SOURCES.md`

## Proposed change (high-level)

### Neue Config Keys (Runtime: `config/config.yml`)
Unter `universe_filters.volume`:

- `min_turnover_24h: 0.03`
- `min_mexc_quote_volume_24h_usdt: 5000000`
- `min_mexc_share_24h: 0.01`

### Backward compatibility / Migration
- Legacy Key `universe_filters.volume.min_quote_volume_24h` (falls vorhanden) wird als Alias für `min_mexc_quote_volume_24h_usdt` behandelt:
  - Wenn legacy vorhanden und neuer Key fehlt ⇒ legacy value verwenden
  - Wenn beide vorhanden ⇒ neuer Key gewinnt
  - Verhalten dokumentieren + testen (Missing vs Present)

### Filterlogik (deterministisch)
Für jedes Symbol:
1) Prüfe, ob `turnover_24h` berechenbar ist (nicht None, numerisch, `>= 0`).
   - Wenn ja: require
     - `turnover_24h >= min_turnover_24h`
     - `mexc_quote_volume_24h_usdt >= min_mexc_quote_volume_24h_usdt`
     - `mexc_share_24h >= min_mexc_share_24h`
       - Wenn `mexc_share_24h` nicht berechenbar (None/0-div) ⇒ fail (kein fallback innerhalb des primären Pfads).
2) Wenn `turnover_24h` nicht berechenbar: fallback
   - require nur `mexc_quote_volume_24h_usdt >= min_mexc_quote_volume_24h_usdt`
   - `mexc_share_24h` nicht prüfen

**Invalid per-symbol values** (negativ, NaN, nicht castbar) ⇒ Drop (nicht stillschweigend korrigieren).

## Acceptance Criteria (deterministic)
1) Defaults greifen bei missing keys:
   - `min_turnover_24h=0.03`
   - `min_mexc_quote_volume_24h_usdt=5_000_000`
   - `min_mexc_share_24h=0.01`
2) Invalid config values führen zu Validation-Error:
   - `min_turnover_24h < 0`
   - `min_mexc_quote_volume_24h_usdt < 0`
   - `min_mexc_share_24h < 0` oder `> 1`
3) Filter folgt exakt der Priorität + Fallback-Regel.
4) Legacy alias wird korrekt gehandhabt und getestet.
5) Canonical docs spiegeln Keys, Defaults, Bedeutung und Fallback wider.

## Tests (required if logic changes)
- Unit (Filters):
  - Turnover berechenbar: pass/fail Fälle für turnover + mexc-min + share
  - Turnover missing: fallback nur mexc-min (share nicht erforderlich)
  - Turnover berechenbar aber share missing ⇒ fail
  - Invalid per-symbol values (negativ/NaN) ⇒ drop deterministisch
- Unit (Config validation):
  - missing keys ⇒ defaults
  - invalid values ⇒ error
  - legacy alias behavior (legacy only / both keys)

- Golden fixture / verification:
  - Wenn Canonical Pipeline/Config Regeln geändert werden: Update `docs/canonical/VERIFICATION_FOR_AI.md` **nur falls** dort Schwellen/Regeln validiert werden.

## Constraints / Invariants (must not change)
- Deterministische Filter-Reihenfolge.
- Kein silent fallback außer explizit beschriebenem fallback.

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Canonical docs updated under `docs/canonical/` (CONFIGURATION + ggf. PIPELINE)
- [ ] Tests hinzugefügt/aktualisiert
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-02-28T00:00:00Z"
priority: P0
type: feature
owner: codex
related_issues: []
```
