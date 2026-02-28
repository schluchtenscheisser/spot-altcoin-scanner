> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Liquidity: Nicht gefetchte Symbole dürfen nicht automatisch `liquidity_grade="D"` bekommen (Top-K darf Universe nicht hart beschneiden)

## Context / Problem
Codex-Kommentar: Wenn `liquidity_grade="D"` für jedes Symbol ohne Orderbook-Payload gesetzt wird, wird `orderbook_top_k < len(shortlist)` zu einem impliziten Hard Cutoff: alle Symbole außerhalb Top-K werden zu "D" und werden dann vom bestehenden Hard Gate (`liquidity_grade == 'D'` Filter) entfernt. Vorher blieben diese `None` und konnten weiter in Scoring/Re-rank laufen. Das kann das Candidate-Universe massiv verändern oder bei Outages auf 0 schrumpfen. fileciteturn2file0

## Goal
Semantik korrigieren:
- **"non-fetched"** (nicht im Top-K Fetch Budget) ≠ **"bad liquidity"**
- Nur wirklich **evaluierte** Symbole dürfen eine Grade bekommen.
- Nicht gefetchte Symbole sollen ihren bisherigen Zustand (typisch `None`) behalten und dürfen nicht durch das Hard Gate gelöscht werden.

## Scope
- scanner/pipeline/liquidity.py
- scanner/pipeline/__init__.py (nur falls Hard Gate angepasst werden muss; bevorzugt nicht)
- docs/canonical/LIQUIDITY/* oder relevante Doc-Stelle
- tests/test_liquidity.py

## Out of Scope
- Scoring-Algorithmen
- Global Ranking Regeln

## Proposed Change (No-Guesswork)
### 1) Unterscheide Fälle
In `apply_liquidity_metrics_to_shortlist(...)` pro Symbol:

A) **Fetched + valid orderbook payload**
- compute metrics
- set `liquidity_grade` gemäß thresholds

B) **Fetched but malformed/invalid payload**
- set `liquidity_insufficient = True` (oder existing field)
- set `liquidity_grade = "D"` (falls canonical: malformed zählt als fail)
- (Wichtig: dieser Fall ist nur für Symbole, die wirklich gefetchd wurden)

C) **Not fetched (symbol nicht in top-k selection)**
- **do not set** `liquidity_grade`
- **do not set** "D"
- leave liquidity metric fields as `None` (or untouched)

### 2) fetch_orderbooks_for_top_k(...) muss "selected symbols" liefern
Damit apply_liquidity "not fetched" erkennen kann:
- fetch_orderbooks_for_top_k returns `(orderbooks_map, selected_symbols_set)` ODER
- apply_liquidity bekommt `selected_symbols_set` als parameter.

### 3) Documentation alignment
Docs müssen explizit sagen:
- `liquidity_grade` wird nur gesetzt, wenn ein Symbol evaluiert wurde (fetched).
- Nicht gefetchte Symbole behalten `None`.

## Acceptance Criteria
1) Bei `orderbook_top_k < len(shortlist)` bleiben Symbole außerhalb Top-K **nicht** automatisch grade "D" und werden nicht vom Hard Gate entfernt.
2) Bei Orderbook-Outage (alle fetch fails) wird Universe nicht automatisch zu 0 (non-fetched bleibt None).
3) Tests:
   - shortlist mit 5 Symbolen, top_k=2: nur 2 Symbole bekommen grade; rest bleibt None.
   - fetched malformed payload führt zu grade D (und nur dann).
4) Docs spiegeln die Semantik wider.

## Definition of Done
- [ ] Code + Docs + Tests umgesetzt
- [ ] pytest -q grün
- [ ] 1 PR
