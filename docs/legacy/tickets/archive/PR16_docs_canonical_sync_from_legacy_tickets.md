> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# PR16 — Docs-only: Canonical docs sync & consistency fixes (based on docs/legacy/tickets)

## Kurze Erläuterung
Ich habe `docs/legacy/tickets/*` erneut gegen den aktuellen Stand von `docs/canonical/*` abgeglichen (inkl. der zuletzt bearbeiteten Tickets). Ergebnis:

- **Die meisten** inhaltlich relevanten Ticket-Themen sind bereits in Canonical Docs dokumentiert (u.a. Orderbook TopK Policy, global volume / market-activity output fields, volume-source switch, evaluation dataset exporter).  
- Es gibt aber weiterhin **konkrete Inkonsistenzen innerhalb** der Canonical-Doku zum Breakout Trend 1–5D Scoring: Im YAML-“Machine Header” stehen Werte, die dem späteren Text/der Strategie-Intention widersprechen (und in der Praxis “0 Breakouts” begünstigen können, wenn jemand sich an den Header statt an den Body hält).

Diese PR behebt ausschließlich diese Canonical-Doc-Drifts (keine Code-Änderungen).

## Scope
- Docs-only (nur `docs/canonical/*`).
- Keine Änderungen an `scanner/` oder `config/`.
- Ziel: Canonical-Doku ist **intern konsistent** (Machine Header == Body) und entspricht der implementierten Breakout Trend 1–5D Logik.

## Files to change
- `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- Optional: `docs/canonical/INDEX.md` (nur falls Links/Anker angepasst werden müssen)

---

## Required doc changes (exact)

### 1) Fix trigger window default in YAML header (6 → 30 bars)
In `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md` YAML Machine Header:
- Change:
  - `trigger_4h.window_bars: 6`
- To:
  - `trigger_4h.window_bars: 30`

Then scan the document to ensure **no remaining** claim that the canonical default is 6 bars.
(Body text already states canonical default `N=30` — keep it.)

### 2) Fix ATR chaos gate scale mismatch (0.80 → 80.0 on 0..100 percent-rank scale)
`atr_pct_rank_120_1d` is a **percent-rank on scale [0..100]** (not rank01).  
Therefore the canonical hard gate must be:
- PASS if `atr_pct_rank_120_1d <= 80.0`
- FAIL if `atr_pct_rank_120_1d > 80.0`

Apply this change in **both** places:
- YAML header:
  - Replace `gates_1d.atr_chaos_gate: "atr_pct_rank_120_1d <= 0.80"`
  - With: `gates_1d.atr_chaos_gate: "atr_pct_rank_120_1d <= 80.0"`
- Body section “3.2 ATR Chaos Gate (1D)”:
  - Replace `<= 0.80` with `<= 80.0`
  - Keep the existing definition of `atr_pct_1d = atr_1d / close_1d * 100` and rolling percent-rank.

### 3) Fix section numbering / ordering (Execution Gate section is out-of-order)
In `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md` the “Execution Gate” section appears **after** “11) Test/Fixture Anchor” but is labeled “9) …”, which is confusing and breaks stable referencing.

Do:
- Reorder sections so numbering is strictly increasing, **or** renumber headings so the order matches.
- Requirement: there must be **exactly one** “Execution Gate” section, and it must appear **before** the “Test/Fixture Anchor” section.

Also ensure this explicit sentence is present (keep/add if missing):
- “Discovery candidates remain listed even if execution gate fails.”

### 4) Clarify liquidity gate source wording (no threshold change)
In the “2.2 Liquidity Gates” section, keep numeric thresholds unchanged, but ensure it is explicit that:
- the gate uses the configured volume source (default: MEXC quote volume; optional global fallback if configured).
This is a docs clarity fix only.

### 5) Optional: Update INDEX.md links if headings/anchors changed
Only if your edits change anchors referenced from `docs/canonical/INDEX.md`, update that file accordingly.

---

## Validation checklist
- Open `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md` and confirm:
  - YAML header defaults match body text: trigger window = 30 bars.
  - ATR chaos gate uses 80.0 consistently (percent scale 0..100).
  - Section numbering is consistent; Execution Gate is not out-of-order.
- Ensure `docs/canonical/INDEX.md` links still resolve (only if touched).

## Acceptance criteria
- Canonical docs are internally consistent and aligned with Breakout Trend 1–5D behavior.
- No code/config changes.
- No broken canonical links.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/tickets/` (same filename).
