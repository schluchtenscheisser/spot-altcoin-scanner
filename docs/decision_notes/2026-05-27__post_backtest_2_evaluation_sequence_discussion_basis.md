# Post-BACKTEST-2 Evaluation Sequence — Discussion Basis

## Status

**Status:** Discussion basis  
**Status:** Empirical evaluation roadmap proposal  
**Status:** Not a canonical specification change  
**Status:** Not a scanner-configuration change  
**Status:** Not a live-trading approval  

## Context

This note documents a proposed evaluation sequence after completion of:

- BACKTEST-1 — primary signal segment analysis
- BACKTEST-2 — actionable segment report
- initial trade-scope v0 segment decision note

It is intended to preserve the current reasoning for future chats and analysis work. It should not be read as a hard project mandate. The sequence may be revised if new evidence, implementation constraints, or reviewer feedback justify a different order.

## Current empirical basis

BACKTEST-1 and BACKTEST-2 support the working interpretation that the scanner primarily identifies short-horizon opportunities.

Observed shape:

```text
Strongest empirical edge: 1d–3d
5d: still useful in selected cases, but weaker
10d/20d: unstable and not suitable as blind-hold horizons
```

This aligns with the initial strategy idea: identify spot altcoins with short-term upside potential over approximately 1–3 days.

At the same time, this makes exit logic central. The scanner should not be treated as a blind-hold system.

## Current primary trade-scope hypothesis

The currently documented Primary Trade Scope v0 consists of:

```text
early_candidates × base_reclaim
confirmed_candidates × ema_reclaim
early_candidates × early_reversal_break
```

Secondary / Observe:

```text
confirmed_candidates × base_reclaim
confirmed_candidates × early_reversal_break
```

Late Monitor remains diagnostic for now, despite some positive short-horizon behavior in selected subsegments.

Reference decision note:

```text
docs/decision_notes/2026-05-27__initial_trade_scope_v0_segment_decision_note.md
```

## Core concern

The current Backtest-1/2 results are based on forward-return endpoints.

They answer questions such as:

```text
What was the return after exactly 1d, 3d, 5d, 10d, or 20d?
```

They do not yet answer the path-dependent trading questions:

```text
How far did the trade move in favor before the endpoint?
How far did it move against the entry before the endpoint?
Was the peak reached early and then faded?
Would a stop, partial take-profit, or trailing exit have triggered first?
How long did winners need to become winners?
How quickly did losers fail?
```

Because of that, scanner-configuration tuning should be approached carefully. A segment that looks weaker at a fixed 5d endpoint may still be highly tradable with a better exit. Conversely, a segment that looks good at 3d may be practically difficult if it has large adverse excursions before reaching the endpoint.

## Proposed evaluation sequence

This is a suggested order, not a hard rule.

### Step 1 — BACKTEST-3: Exit Path Metrics / MFE-MAE Analysis

Purpose:

Understand how current signals behave after entry before changing scanner configuration.

Recommended metrics:

```text
MFE — Maximum Favorable Excursion
MAE — Maximum Adverse Excursion
time_to_peak
time_to_max_drawdown
return path by 4h bar after signal
drawdown after entry
peak-to-close giveback
stop/target/trailing hit order
```

Scope priority:

1. Primary Trade Scope v0 segments
2. Secondary / Observe segments
3. Late Monitor only as a separate diagnostic view

Reasoning:

The next analytical bottleneck is not yet scanner parameter tuning. It is understanding whether the current signals are tradable with a realistic exit model.

### Step 2 — Evaluate or challenge the existing analytics-only trade model

Existing model in repo:

```text
docs/canonical/BACKTEST/TRADE_MODEL_4H_IMMEDIATE_RETEST.md
```

Important framing:

- This is an analytics-only model.
- It is not a validated live-trading rule.
- Its canonical status documents the analysis model, not a final execution rule.

Known model elements to test:

```text
timeframe: 4h
stop: ATR × 1.2
partial: 40% at 1.5R
trailing activation: after partial filled
trailing exit: close_4h < ema20_4h
time stop: max_hold_hours = 168 / 7 days
intracandle priority: STOP → PARTIAL → TRAIL
```

Key question:

```text
Does this model fit a scanner whose strongest empirical edge appears in the first 1–3 days?
```

Specific concern:

The model was designed for a 4h breakout setup with a 7-day maximum runner. The scanner's observed edge peaks at 1–3 days. Whether these are compatible needs to be evaluated against MFE/MAE path data, not assumed.

The 7-day max time stop may still be useful as a maximum runner stop, but it should not be mistaken for the standard intended holding period.

### Step 3 — BACKTEST-4: Scanner Parameter Sensitivity / Segment Stability

Only after exit-path behavior is better understood, evaluate whether scanner configuration changes are needed.

Possible scenario dimensions:

```text
freshness thresholds
early/confirmed thresholds
late/chased thresholds
entry-pattern-score minimums
phase-confidence minimums
state-confidence minimums
treatment of confirmed_candidates × early_reversal_break
late_monitor promotion hypotheses
```

Important evaluation criteria:

```text
signal count
segment stability
1d/3d/5d behavior
MFE/MAE profile
exit-adjusted trade quality
BTC-regime robustness
quote-volume bucket robustness
trade frequency
overfitting risk
```

Reasoning:

Configuration tuning should not optimize endpoint forward returns alone. It should consider whether the adjusted configuration improves tradable behavior after realistic exits.

### Step 4 — Optional full replay with selected alternative configurations

If a sensitivity scenario looks promising, it may need a full replay rather than only filtering an existing enriched event dataset.

Reason:

Some configuration changes alter:

```text
state transitions
entry timing
bucket assignment
event occurrence
event timestamp
forward-return anchor
```

Therefore, post-hoc filtering may be insufficient for configuration changes that affect the generation of events.

Suggested pipeline for serious alternatives:

```text
Config variant
→ full replay
→ BACKTEST-MERGE
→ BACKTEST-1
→ BACKTEST-2
→ BACKTEST-3
```

## Practical guiding principle

A useful working principle for the next phase:

```text
First understand exit behavior on the current signal basis.
Then evaluate scanner-parameter sensitivity.
Only then consider configuration changes or live-trading rule changes.
```

This is a discussion guide, not a hard constraint. It is intended to prevent premature optimization, not to block useful analysis if new evidence suggests a better path.

## Open discussion points

The following questions remain open and should be discussed before turning this into implementation tickets:

1. Should BACKTEST-3 focus only on the three Primary Trade Scope v0 segments, or also include Secondary / Observe from the beginning?
2. Should Late Monitor be included in BACKTEST-3 as a separate diagnostic table, or deferred to a later dedicated Late-Momentum analysis?
3. Should the existing 4h immediate retest model be tested first as-is, or should BACKTEST-3 initially be model-agnostic and only compute path metrics?

   Recommended starting position: begin model-agnostic. Compute MFE, MAE, time-to-peak, and drawdown first without imposing exit-rule assumptions. Apply the existing trade model as a second evaluation pass once path behavior is understood. This prevents the model's parameters (ATR × 1.2, 1.5R partial, EMA20 trail) from anchoring the analysis before the data has been examined.
4. Which exit hypotheses should be tested first:
   - hard 3d time exit
   - 3d soft exit with runner exception
   - ATR stop + partial + EMA20 trail
   - fixed take-profit thresholds
   - segment-specific exits
5. Which result would justify scanner-configuration tuning rather than only exit-model adjustment?

## Non-goals

This note does not:

- change the v2.1 scanner specification
- change scanner thresholds
- approve live trading
- define final exit rules
- replace BACKTEST-3 ticket design
- replace the existing trade-model document

## Suggested next step

Use this note as a reference when designing:

```text
BACKTEST-3 — Exit Path Metrics / MFE-MAE Analysis
```

The immediate objective should be to define which path metrics and hypothetical exit-rule evaluations are needed to judge whether the current primary segments are practically tradable.
