> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## 2026-02-27__04_P1__liquidity_fetch_payload_semantics_alignment.md

### Title
[P1] Liquidity: Fetch-Payload Semantik an Runtime anpassen (oder Runtime härten) + Tests

### Context / Problem
Docs behaupten, die Orderbook-Map enthält nur erfolgreiche dict payloads und Missing Keys sind “missing orderbook”. Runtime speichert jedoch jeden non-exception return value und downstream behandelt malformed dicts als “grade D” (nicht missing). Das erzeugt Debug/Metric Divergenz. fileciteturn1file0

### Goal
Runtime und Dokumentation müssen übereinstimmen. Zusätzlich soll Runtime robust werden gegen non-dict / malformed orderbooks.

### Scope
- scanner/pipeline/liquidity.py (fetch_orderbooks_for_top_k, apply_liquidity_metrics_to_shortlist)
- passende Canonical/Docs Stelle (z. B. docs/canonical/LIQUIDITY/* oder OUTPUT_SCHEMA)
- tests/test_liquidity.py (neu oder erweitern)

### Out of Scope
- Ranking/Scoring Änderungen (außer durch klar definierte “missing orderbook” Semantik)
- Pipeline orchestration

### Implementation Requirements (präzise)
Option (empfohlen): **Runtime härten + Docs aktualisieren**
1) fetch_orderbooks_for_top_k:
   - Speichere payload nur, wenn:
     - payload ist dict
     - enthält `bids` und `asks` als nicht-leere listen
   - sonst:
     - speichere NICHT in payload-map
     - logge debug-level „malformed orderbook“ (symbol)
2) apply_liquidity_metrics_to_shortlist:
   - wenn payload missing → treat as missing orderbook:
     - setze liquidity metrics Felder auf None
     - setze liquidity_grade auf "D" (oder “MISSING”) **nur**, wenn Canonical das so will; andernfalls "D" bleibt, aber payload-map size muss dann “valid payloads” zählen.
   - Wichtig: Implementierung + Docs müssen exakt die gewählte Semantik spiegeln.

### Acceptance Criteria
- Docs beschreiben exakt die Map-Definition (“contains only validated orderbooks” ODER “contains any payload”) passend zur Implementierung.
- Tests:
  - non-dict payload wird ignoriert (nicht im map)
  - dict ohne bids/asks wird ignoriert
  - downstream setzt erwartete Felder konsistent
  - fetched-map size entspricht “valid payload count”

### Definition of Done
- [ ] Code + Docs + Tests umgesetzt
- [ ] pytest -q grün
- [ ] 1 PR
