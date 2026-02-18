# Future Extensions & Roadmap
Version: v1.0
Language: English
Audience: Developer + GPT

---

## 1. Purpose

This document outlines potential future extensions for the scanner.  
It is intentionally broad and conceptual — not a commitment, not a spec.

Roadmap items are grouped by **expected dependency level** and **expected payoff**.

A good extension is one that:
- increases signal quality or interpretability
- does not collapse architecture
- remains backtestable
- remains deterministic

---

## 2. Extension Categories

### Category A — Market Insight Modules
Enhance understanding of market structure.

Candidates:
- BTC/ETH regime filters
- sector/category tagging
- liquidity cluster analysis
- OI/funding tracking (if derivatives enabled)
- index-relative performance (beta/alpha split)

Rationale: clarifies **when certain setups work**.

---

### Category B — Data Dimension Expansion
Adds new kinds of data beyond OHLCV.

Candidates:
- On-chain metrics (TVL, users, gas, bridges, flows)
- CEX/DEX volume split
- launchpad/IDO activity
- exchange listings
- token unlock schedules
- treasury/governance actions

Rationale: increases context surface area.

---

### Category C — Execution & Research Tools
Not trading automation, but analysis assistants.

Candidates:
- forward scenario simulator (no execution)
- scoring calibration dashboards
- regime explorer
- hit-rate inspector
- timeline visualizer
- snapshot replay tool
- event overlay annotations

Rationale: speeds up iterative research.

---

### Category D — Backtest Enhancements
Improves evaluation fidelity.

Candidates:
- rolling CAGR
- volatility clustering
- tail risk distribution
- score → return correlation
- rank monotonicity metrics
- parameter sweeps
- cross-setup interactions analysis
- feature attribution

Rationale: validates the scanner, not markets.

---

### Category E — Candidate Selection Refinement
Improves signal/noise ratio.

Candidates:
- liquidity-aware re-ranking
- volatility regime constraints
- adaptive shortlist sizing
- time-of-day windows
- dynamic penalties

Rationale: prevents obvious suboptimal picks.

---

### Category F — Output & UX Enhancements
Improves consumption & human usability.

Candidates:
- dashboard
- daily HTML reports
- comparison diffs (day → day)
- annotation of price structure
- code-assist for charts (optional)
- sqlite/notebook export

---

### Category G — Trading/Execution (Late)
Advanced, optional, out-of-scope for v1–v2.

Candidates:
- simulation of execution
- portfolio sizing
- Kelly/half-Kelly
- risk overlays
- auto-execution (not research)

Prereq:
- stable scoring
- stable backtests
- stable setup metrics

---

## 3. Timeline Estimation (Non-binding)

Minimal sensible timeline:

| Phase | Deliverable |
|---|---|
| v1 | scanner + snapshot + basic backtest |
| v2 | backtest refinement + calibration tools |
| v3 | metadata/context extensions |
| v4 | execution (optional) |

---

## 4. Dependencies / Blocking Factors

Some extensions require prerequisite infrastructure:

| Extension | Depends on |
|---|---|
| regime filters | BTC/ETH feed |
| on-chain | provider + caching |
| unlock schedules | calendar + db |
| dashboards | stable data model |
| execution | latency + API + risk |
| ML scoring | data consistency + labels |
| parameter sweep | stable config |

No extension should short-circuit versioning.

---

## 5. Design Criteria for Future Extensions

Extensions must satisfy:

- deterministic inputs
- definable outputs
- backtestable behavior
- specifiable config
- snapshot-compatible

Failure to satisfy → postpone.

---

## 6. Out-of-scope (permanent anti-roadmap)

These features are unlikely to ever belong:

- crypto price prediction
- newsletter alpha calls
- “buy/sell” signals
- financial advice
- opinion layers
- macro narrative explanation
- hype sentiment

Scanner remains a **research assistant**, not a forecaster.

---

## 7. Final Notes

Future extensions should emerge from **backtest evidence**, not speculation.  
Roadmaps without validation create waste.

---

## End of `future_extensions.md`
