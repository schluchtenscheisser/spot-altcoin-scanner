> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket: Align percent-rank scale + document orderbook Top-K payload semantics

## Title
[P1] Canonical percent_rank/proxy_liquidity_score Skala konsistent machen + Orderbook Top-K Payload-Semantik dokumentieren

## Context / Source
Nach PR #94 sind Tests für `percent_rank_average_ties` auf einer Skala **0..100** (Prozent) formuliert. In Canonical-Doku war `percent_rank` bisher (teilweise) als **0..1** beschrieben. Das ist ein Canonical↔Code Drift-Risiko.

Nach PR #93 hat sich die Semantik von Orderbook-Fetch/Return verändert: es werden nur noch tatsächlich gefetchte Orderbooks als `dict` zurückgegeben; fehlende/invalid payloads werden downstream als “missing orderbook” behandelt. Diese Semantik ist in Canonical Doku noch nicht explizit beschrieben.

## Goal
1) Canonical Doku ist konsistent zur im Code getesteten Skala für percent-ranks (0..100) und damit auch zur Verwendung von `proxy_liquidity_score`.
2) Canonical Liquidity Doku beschreibt die Orderbook Top-K Payload-/Missing-Semantik und Failure-Isolation explizit.

## Scope
Erlaubte Änderungen:
- `docs/canonical/FEATURES/FEAT_PERCENT_RANK.md`
- `docs/canonical/LIQUIDITY/RE_RANK_RULE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/LIQUIDITY/ORDERBOOK_TOPK_POLICY.md` (oder alternativ SLIPPAGE_CALCULATION.md – aber bevorzugt hier)
- optional: `docs/canonical/CONFIGURATION.md` (nur wenn ranges/units dort genannt sind und angepasst werden müssen)

Nicht erlaubt:
- Änderungen am Code (dieses Ticket ist Doc-Alignment & Spec-Update)
- Schema-Version bump (nur Doku synchronisieren)
- Änderungen an Legacy außer ggf. reinem Archiv-Header (nicht nötig)

## Out of Scope
- Kein Umbau/Neudefinition der percent-rank Formel
- Keine Änderung an Scoring-Logik oder Ranking-Logik
- Keine Änderung der Liquidity Grade Schwellen

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/FEATURES/FEAT_PERCENT_RANK.md`
- `docs/canonical/LIQUIDITY/RE_RANK_RULE.md`
- `docs/canonical/LIQUIDITY/ORDERBOOK_TOPK_POLICY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/CONFIGURATION.md`

## Proposed change (high-level)

### A) percent_rank Skala (cross-sectional) – Canonical finalisieren
Entscheidung (canonical):
- percent-ranks werden als **0..100** (“percent”) ausgegeben, nicht 0..1.

Konkrete Änderungen:
1) `FEAT_PERCENT_RANK.md`
   - Output-Range auf **[0.0, 100.0]**
   - Formel bleibt identisch, aber Output = `rank * 100`
     - `rank01 = (count_less + 0.5*count_equal) / N`
     - `percent_rank = 100 * rank01`
   - Tie-handling + IEEE-754 equality bleibt unverändert.
2) Rolling ranks (falls irgendwo noch 0..1 erwähnt):
   - Entweder ebenfalls auf 0..100 umstellen oder ausdrücklich `*_rank01` nennen.
   - **Wichtig:** Nicht vermischen. In den betroffenen Canonical Docs muss eindeutig stehen, welche Skala verwendet wird.
3) `RE_RANK_RULE.md`
   - `proxy_liquidity_score` Range und meaning auf **0..100** anpassen, falls es auf percent_rank basiert.
4) `OUTPUT_SCHEMA.md`
   - Feldbeschreibung + Range `proxy_liquidity_score` konsistent anpassen (0..100).
5) `CONFIGURATION.md`
   - Wenn dort Ranges für ranks stehen, ebenfalls konsistent (0..100).

### B) Orderbook Top-K Payload-/Missing-Semantik explizit dokumentieren
In `ORDERBOOK_TOPK_POLICY.md` ergänzen:
- Fetch kann pro-symbol fehlschlagen, ohne den gesamten Run zu brechen (Failure-Isolation).
- Return-Map enthält nur “fetched payloads” (dict). Fehlende Keys / non-dict gelten als “missing orderbook”.
- Missing orderbook -> slippage missing -> re-rank behandelt es als worst-case (verweist auf `RE_RANK_RULE.md`).

## Implementation Notes
- Determinismus: Skala muss überall gleich sein (oder klar getrennte Feldnamen).
- Backward compatibility: Wenn Code bereits `proxy_liquidity_score` im Output liefert, darf Doku keinen anderen Wertebereich behaupten.
- Kein Code-change: Wir dokumentieren den IST-Zustand, der durch Tests/PRs etabliert wurde.

## Acceptance Criteria (deterministic)
1) In `docs/canonical/FEATURES/FEAT_PERCENT_RANK.md` ist die Skala eindeutig: **0..100**, inkl. Formel `*100`.
2) In `docs/canonical/LIQUIDITY/RE_RANK_RULE.md` ist `proxy_liquidity_score` eindeutig dokumentiert (Range 0..100).
3) In `docs/canonical/OUTPUT_SCHEMA.md` ist die Range für `proxy_liquidity_score` konsistent (0..100) und nicht widersprüchlich.
4) In `docs/canonical/LIQUIDITY/ORDERBOOK_TOPK_POLICY.md` ist die neue Payload-/Missing-Semantik explizit beschrieben.
5) Keine Canonical-Datei enthält danach widersprüchliche Rank-Ranges (kein 0..1 vs 0..100 Mix ohne klare Feldnamen).

## Tests
- Doc-only Ticket: keine Code-Tests.
- Required sanity check:
  - Suche in `docs/canonical/` nach `0..1` / `[0.0, 1.0]` / `rank_0_1` und stelle sicher, dass das entweder:
    - korrekt umgestellt ist oder
    - explizit als “rank01”/separater Feldname dokumentiert ist.

## Constraints / Invariants (must not change)
- Tie-handling: average-rank
- Equality: IEEE-754 exact
- NaN policy: NaNs excluded from population; x NaN -> output NaN
- Deterministic ordering and tie-breakers remain unchanged

## Definition of Done (Codex must satisfy)
- [ ] Canonical docs updated per Acceptance Criteria
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

## Metadata (optional)
```yaml
priority: P1
type: docs
owner: codex
related_prs:
  - https://github.com/schluchtenscheisser/spot-altcoin-scanner/pull/94
  - https://github.com/schluchtenscheisser/spot-altcoin-scanner/pull/93
