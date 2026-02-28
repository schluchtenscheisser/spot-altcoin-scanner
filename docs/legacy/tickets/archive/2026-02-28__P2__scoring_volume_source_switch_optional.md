> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

#### A) Defaults / Config-Semantik
- [x] Missing key ⇒ Default bleibt unverändert (MEXC).

#### B) Nullability / Schema / Output
- [x] Quelle wird explizit dokumentiert; keine stillen Fallbacks außer explizit definiert.

#### C) Edgecases
- [x] global missing ⇒ fallback auf MEXC (Policy aus User-Entscheidung 3=B)

#### D) Tests
- [x] Tests für Source-Switch + missing global

---

## Title
[P2] Scoring: Volume-Quelle optional (MEXC vs Global) + Reasons transparenter machen

## Context / Source (optional)
- Universe-Filter wird global+MEXC. Scoring nutzt noch `volume_map` basierend auf MEXC quoteVolume.
- Dieses Ticket ist optional und ändert Scores nur, wenn aktiviert.

## Goal
- Neue Config Option steuert, welche Volume-Quelle in `volume_map` für Scoring genutzt wird:
  - Default bleibt **MEXC** (keine Änderung wenn nicht aktiviert)
  - Option: **GLOBAL_FALLBACK_MEXC** (wenn global missing ⇒ nutze MEXC; sonst global)
- In Score-Reasons wird die verwendete Quelle explizit genannt.

## Scope
- `scanner/pipeline/__init__.py` (volume_map building)
- scoring module(s), die `volume_map` nutzen
- `docs/canonical/SCORING/*` falls Regeln/Meaning berührt

## Out of Scope
- Universe Filter (Ticket 2)
- Execution/Liquidity Stage

## Canonical References (important)
- `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- `docs/canonical/CONFIGURATION.md`

## Proposed change (high-level)
### Neue Config
- `scoring.volume_source: "mexc" | "global_fallback_mexc"`

### Semantik
- `mexc`: `volume_map[symbol] = mexc_quote_volume_24h_usdt` (Status quo)
- `global_fallback_mexc`:
  - Wenn `global_volume_24h_usd` berechenbar ⇒ nutze `global_volume_24h_usd`
  - Sonst ⇒ nutze `mexc_quote_volume_24h_usdt`
- Reasons/Output sollen `volume_source_used` pro scored row enthalten (oder im reasons array).

### Missing vs Invalid
- Missing config key ⇒ Default `mexc`
- Invalid config value ⇒ Validation-Error

## Acceptance Criteria (deterministic)
1) Default behavior unverändert (`mexc`).
2) Bei `global_fallback_mexc` wird global genutzt wenn vorhanden, sonst mexc.
3) Output/Reasons nennen die Quelle deterministisch.
4) Tests decken missing global ab.

## Tests (required if logic changes)
- Unit: `volume_map` source selection
- Unit: scorer consumes map unchanged (keine weiteren Seiteneffekte)

## Constraints / Invariants (must not change)
- Score ranges bleiben 0..100
- Deterministisches tie-handling unverändert

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Canonical docs updated if scoring rules/outputs changed
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
