# Open Questions — Independence-Release Bootstrap (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OPEN_QUESTIONS
status: canonical
```

## Purpose
This file tracks authoritative open questions that remain unresolved in the current Independence-Release architecture and therefore must not be silently decided by later implementation tickets.
These questions map to the unresolved clarification surface referenced in Gesamtkonzept §21.

## Bootstrap rule
Until an open question listed here is resolved in canonical documentation, later tickets and implementations must not silently invent business-logic answers for it.

## Open questions

### 1) `dist_to_base_mid_pct` remains unresolved

**Context**

The field `dist_to_base_mid_pct` was identified during the Ticket-5 / Ticket-5.1 / Ticket-6 workstream as a required input for `expansion_progress_structural`, but no authoritative formula was found in the governing specifications.

The field name and descriptive intent exist, but the architecture still lacks a canonical definition for:

- what exactly the “base mid” is,
- which historical range/base it refers to,
- how that base is selected,
- and the exact formula for converting it into `dist_to_base_mid_pct`.

**Why this matters**

Without an authoritative formula, independent implementations may invent incompatible meanings for the same field, causing divergence in:

- Tier-1 axis computation,
- diagnostics and explainability,
- later runner/state interpretation,
- backtest comparability.

**Current consequence**

`expansion_progress_structural` must continue to treat this sub-input as absent.

The related subscore remains unavailable, and the axis continues to rely on canonical weight-dropout / re-normalization with:

- `expansion_progress_structural_reduced_resolution = true`

for as long as `dist_to_base_mid_pct` has no authoritative formula.

**Still to decide**

A future canonical resolution must define:

1. the authoritative base-selection rule,
2. the exact mathematical formula,
3. whether any lookback/config parameter is involved,
4. and which module owns the computation contract.

---

### 2) Long-term OHLCV history storage path beyond Ticket 4 transitional SQLite persistence

**Status:** resolved by Ticket 14.

Canonical OHLCV long-term storage is:

`snapshots/history/ohlcv/timeframe=<tf>/symbol=<symbol>/year=<yyyy>/month=<mm>/`

SQLite is not the canonical long-term OHLCV history store.

Ticket 18 evaluation reads forward-looking OHLCV data from the canonical Parquet history store above.

No additional open question remains for this topic.

---

### 3) `daily_bar_id` type consistency across Independence-Release layers

**Status:** Resolved by Ticket 15 (daily runner integration).

Canonical cross-layer type is now `str` in `YYYY-MM-DD` format for: bar-clock context, runner-facing typed bundles, and output/report schemas.

Resolved scope includes at least:
- `Tier1AxisBundle.daily_bar_id`
- `Tier2AxisBundle.daily_bar_id`
- `PhaseInterpretationBundle.daily_bar_id`

No dual `int`/`str` representation is canonical after this resolution.

---

### 4) §21/3 Execution frequency + Top-N policy (Daily vs Intraday)

**Status:** Resolved by Ticket 17 for the **Intraday Promotion Scan** (and previously Ticket 16 for Daily).

Resolved Daily rule: execution subset selection follows Abschnitt 6 §8.2 (state/confidence/active-bucket OR-logic with hard exclusions for rejected/chased/discarded). No fachlicher Top-N cap is applied in Daily unless an explicit safety-limit hard-fail guard is configured.

Resolved Intraday rule:
- Intraday execution subset selection follows Abschnitt 6 §8.2 inside the reduced intraday monitoring universe.
- No fachlicher Top-N cap is applied.
- Optional intraday execution-subset limits are technical safeguards only (hard-fail / run-incomplete guard), never silent ranking-based truncation.

---

### 5) Stablecoins are not filtered

TUSDUSDT — Tag 2 confirmed, Tag 3 confirmed. Zwei aufeinanderfolgende Tage — aber TUSD ist ein Stablecoin. Das ist ein klarer False-Positive-Kandidat für die Eligibility. Stablecoins sollten eigentlich durch den Market-Cap- oder Listing-Age-Filter rausfallen, oder die Spec muss einen expliziten Stablecoin-Ausschluss vorsehen.

---

### 6) Intraday smoke test vs. Full-Universe

Smoke-Test vs. Full-Universe zeigen unterschiedliches Intraday-Verhalten — wahrscheinlich kein Bug, aber Ursache noch nicht verifiziert.

---

### 7) Strukturelle Beobachtung Tag 2: Evaluation Replay akkumuliert nicht
`run_count: 1` an beiden Tagen. Das ist korrekt nach T18-Design — der Replay liest aus dem Run-Artefakt der jeweiligen Sitzung, nicht aus einem persistenten Event-Store. Das bedeutet: Die Evaluation baut aktuell keine tagesübergreifende Event-Historie auf. Für echte Forward-Return-Auswertung (z.B. "Was hat TURTLEUSDT nach dem confirmed-Signal gemacht?") braucht es später entweder einen akkumulierenden Event-Store oder ein separates Analysis-Script, das mehrere Replay-Artefakte zusammenführt.
