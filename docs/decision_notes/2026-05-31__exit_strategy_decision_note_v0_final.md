# Exit Strategy Decision Note v0

**Status:** Discussion basis / Paper-trading candidate  
**Status:** Not a scanner-spec change  
**Status:** Not an automated live-trading rule  
**Status:** Not a canonical v2.1 specification change  
**Date:** 2026-05-31  
**Project:** Independence — Spot Altcoin Scanner  
**Source analysis:** BACKTEST-3A Exit Path Metrics, BACKTEST-3B Exit Model Simulation  
**Analysis IDs:** `BACKTEST-3A_EXIT_PATH_METRICS_4H`, `BACKTEST-3B_EXIT_MODEL_SIMULATION_4H`  
**Replay ID:** `2026-05-24T21-27-31Z`  
**Scenario:** `hsq_replay_2025_05_to_2026_05_v1`

---

## 1. Purpose

This note documents exit hypotheses for the Primary Trade Scope v0 segments after
BACKTEST-3A and BACKTEST-3B.

It does **not** implement live exit logic, modify scanner behavior, or change the
canonical v2.1 specification.

The purpose is to:

- preserve the exit analysis context in structured form,
- define a narrow paper-trading hypothesis for `early_reversal_break`,
- document why `base_reclaim` and `ema_reclaim` are not yet paper-trading ready,
- and capture open questions for a potential BACKTEST-3C.

---

## 2. Method Boundary

BACKTEST-3A and BACKTEST-3B are in-sample analyses on a single historical replay
scenario. They do not substitute for out-of-sample validation.

Not included in this analysis:

```text
MEXC orderbook depth
spread
slippage
fees
real execution sizing
live scanner exit logic
out-of-sample forward returns
```

Included:

```text
4h bar-level path data for 228 events (42 bars per event)
MFE / MAE / time-to-MFE / time-to-MAE per event
ATR(14) 4h for all events
1,230 exit model variants simulated per event
segmentwise result breakdown
```

Exit hypotheses in this note are labeled `observed_in_sample` and
`paper_trading_candidate`. They are not live recommendations.

---

## 3. Dataset Summary

```text
Primary Trade Scope v0 events: 228
Segments:
  early_candidates__base_reclaim:          101 events
  confirmed_candidates__ema_reclaim:        63 events
  early_candidates__early_reversal_break:   64 events

Exit model variants simulated:            1,230
Event-model rows total:                 280,440
Evaluated:                              280,239
Not evaluable:                              201  (1 partial-path event × 201 models)

Reference price source: path_bar_1_open for all 228 events
ATR(14) 4h available: all 228 events
```

---

## 4. Core Finding

BACKTEST-3B confirms the strategic conclusion from BACKTEST-1/2:

```text
The scanner is a short-term setup finder.
The empirical edge window is 1d–3d.
5d is a usable stretch horizon.
Blind holding beyond 5d is not supported without active exit logic.
```

BACKTEST-3B adds a critical path-level finding:

```text
MFE exists materially within the 42-bar path for all three segments.
But median close returns decay and in some cases turn negative without active exits.
This confirms that exit logic is mandatory, not optional, for real trading.
```

The three primary segments show structurally different exit profiles and must not
be treated as a homogeneous group.

---

## 5. Segment Analysis

### 5.1 `early_candidates × early_reversal_break`

**In-sample metrics (3A):**

```text
n:                      64 events
MFE median:            +17.8%
MAE median:             -2.1%
time_to_MFE median:      72h
time_to_MAE median:      56h
recovery_after_mae:     65.6%
mae_before_mfe_rate:    45.3%
```

**Key 3B finding — this is structurally a time-exit segment:**

At 48h / no-partial / ATR 1.5:

```text
median return:    +10.44%
p25 return:        +0.13%
win rate:          76.6%
stop rate:         21.9%
time_stop rate:    78.1%
```

78% of events exit via the 48h time stop, not via the initial stop. The stop
multiplier (ATR 1.0 through Fixed 12%) is nearly irrelevant for median return at
this horizon — all variants produce +10.33% to +10.44% median. This is because
the stop fires in only ~22–25% of events before the 48h bar is reached.

The 120h no-partial model shows nearly identical median return (+10.35%), but p25
declines and the distribution widens, indicating higher variance without additional
gain in the central tendency.

**Structural interpretation:**

The segment often experiences an initial adverse move (MAE before MFE in 45% of
events) before recovering and continuing. The 65.6% recovery-after-MAE rate
explains why no-partial with a time exit works: the setup frequently dips, then
runs — and the 48h window captures the run before decay sets in.

**Exit Hypothesis v0:**

```text
primary_time_stop:     48h (bar 12)
initial_stop_mode:     ATR × 1.5
partial_mode:          none (baseline)
trail_mode:            none

rationale:
  - time_stop dominates exit behavior at 48h
  - stop multiplier choice has minimal impact at this horizon
  - ATR 1.5 provides moderate stop width without changing outcomes
  - partial adds complexity without clear in-sample benefit at 48h
  - 120h is a stretch comparison, not the primary hypothesis
```

**Paper trading status:** `candidate — proceed with primary hypothesis`

---

### 5.2 `early_candidates × base_reclaim`

**In-sample metrics (3A):**

```text
n:                     101 events
MFE median:             +8.8%
MAE median:             -8.9%
time_to_MFE median:      76h
time_to_MAE median:      84h
recovery_after_mae:     53.0%
mae_before_mfe_rate:    43.0%
```

**Key 3B finding — partial + trail is structurally required:**

The 48h no-partial model is structurally negative for this segment:

```text
48h / no-partial / ATR 1.5:
  median return:  -2.73%
  win rate:       37.6%
  stop rate:      51.5%
```

The segment's deeper MAE (median −8.9% vs −2.1% for erb) means that ATR-based
stops fire frequently before MFE is reached. Partial + trail models are required
to capture gains:

Best observed in-sample model (fixed 12% stop / +7.5% partial / 50% / trail
low_2bars / 168h):

```text
median return:    +3.25%
p25 return:      -12.00%
win rate:         59.0%
stop rate:        31.0%
partial fill rate: 55.0%
```

**Structural limitation:**

p25 = −12.00% is a wall, not a tail. When the stop fires before partial fills
(31% of events), the full 12% loss is taken with no partial protection. This
bimodal loss profile is a structural feature of the setup, not a calibration
problem. A wider stop reduces stop frequency but increases loss magnitude when
the stop does fire.

The best in-sample models all require a wide fixed stop (12%), early partial
(+7.5%), and low_2bars trailing. This combination has too many moving parts to
paper-trade without better understanding of the loss-side behavior.

**Exit Hypothesis v0:**

```text
directional hypothesis:
  - wide initial stop required (fixed ~12% or ATR ≥ 1.5)
  - partial take-profit at +5% to +7.5% is necessary for positive median
  - post-partial trailing (low_2bars) improves outcome vs no trail
  - time stop of 120h–168h compatible with partial/trail structure

open questions (see Section 7):
  - does a tighter stop with earlier partial improve p25?
  - is the 12% loss wall reducible through structural stop placement?
```

**Paper trading status:** `not yet — requires further analysis (3C candidate)`

---

### 5.3 `confirmed_candidates × ema_reclaim`

**In-sample metrics (3A):**

```text
n:                      63 events
MFE median:             +9.5%
MAE median:            -11.5%
time_to_MFE median:      56h
time_to_MAE median:     108h
recovery_after_mae:     50.8%
mae_before_mfe_rate:    46.0%
```

**Key 3B finding — fragile positive median, painful loss distribution:**

Best observed in-sample model (fixed 12% stop / +7.5% partial / 50% / trail
low_2bars / 120h):

```text
median return:    +2.56%
mean return:      +0.12%
p25 return:      -10.86%
p75 return:       +6.86%
win rate:         57.1%
stopped before partial: 25.4%
```

The mean of +0.12% against a median of +2.56% reveals a left-skewed distribution.
The 25.4% of events that are stopped before partial always lose exactly −12.00%
(zero variance). This is structurally identical to base_reclaim but with a deeper
MAE median (−11.5% vs −8.9%), making the stop-firing pattern more punishing.

The segment shows MFE when it works (+9.5% median), but the path to MFE frequently
requires surviving a −11.5% adverse excursion. ATR-based stops are structurally
too tight for this segment — they fire in over 50% of events in no-partial models.

**Exit Hypothesis v0:**

```text
directional hypothesis:
  - ema_reclaim requires wide stop tolerance to avoid excessive stop-outs
  - partial + trail structure is necessary (same conclusion as base_reclaim)
  - the loss profile (mean ≈ 0) does not yet justify paper trading

open questions (see Section 7):
  - can structural stop placement (below EMA level or base) outperform
    fixed-percent stop?
  - does reducing position size reduce the penalty of the loss wall?
```

**Paper trading status:** `not yet — requires further analysis (3C candidate)`

---

## 6. Paper-Trading Scope v0

Based on the segment analysis above, paper trading scope v0 is limited to
`early_candidates × early_reversal_break`.

**Paper-Trading Hypothesis v0:**

```text
segment:           early_candidates × early_reversal_break
entry condition:   scanner signal valid (current bucket/pattern still active)
execution gates:   as defined in Initial Trade Scope v0 decision note

exit rule:
  initial_stop:    ATR(14, 4h) × 1.5 below entry/reference price, where
                   the reference price is the first executable post-signal
                   price used in BACKTEST-3A (path_bar_1_open)
  partial:         none
  trail:           none
  time_stop:       48h from entry; for paper tracking, use the close of
                   bar_index_4h = 12 (the 12th completed 4h bar after entry)

position sizing:   reduced initial sizing as previously agreed
```

Paper trading is manual / off-system tracking. It does not imply automated
execution, alerting, or scanner-side exit enforcement.

This is a single, concrete hypothesis — not multiple parallel tests. The goal
is to observe whether the in-sample pattern holds under live conditions before
adding complexity.

Stretch observation (not primary hypothesis): for paper-trading logs, record
what would have happened at bar_index_4h = 30 (120h), but do not manage the
primary paper trade according to the 120h outcome.

Not in paper-trading scope:

```text
confirmed_candidates × ema_reclaim
early_candidates × base_reclaim
late_monitor segments
any variant with partial or trailing in this first phase
```

---

## 7. Open Questions for BACKTEST-3C

The following questions are not answered by BACKTEST-3A/3B and are candidates
for a focused BACKTEST-3C analysis:

**For `early_reversal_break`:**

```text
Does an early partial (+5% at bar 6–12) + low_2bars trail outperform the
48h no-partial baseline? In-sample, no-partial wins on median, but the
partial variant has not been analyzed at bar-level resolution for this
specific window.
```

**For `base_reclaim` and `ema_reclaim`:**

```text
Is the 12% fixed-stop loss wall reducible through structural stop placement
(e.g. below the reclaim level or last structural low), which is not modeled
in 3B?

Does a tighter partial trigger (+5% instead of +7.5%) reduce stop-before-
partial frequency without materially reducing the upside capture?

How sensitive are the best in-sample models to the exact partial size
(40% vs 50%)?
```

BACKTEST-3C should be defined as a focused, question-driven analysis — not
a broad parameter sweep. The questions above should be answered sequentially,
starting with the `early_reversal_break` partial question after paper-trading
data is collected.

---

## 8. Exit Logic Implication for Live System

When exit logic is eventually implemented in the live scanner, it must address
at minimum:

```text
time stop (segment-specific)
initial stop placement and mode
partial take-profit trigger and size
post-partial trailing mechanism
failure / invalidation exit (not yet modeled in 3B)
```

Implementation is out of scope for this note. This document does not
authorize live system changes.

---

## 9. Decision Status

This document should be treated as:

```text
empirical guidance from BACKTEST-3A/3B
preliminary exit hypothesis — discussion basis only
paper-trading candidate for early_reversal_break only
not canonical v2.1 specification
not scanner behavior change
not automated trading permission
```

Next recommended workstreams:

```text
1. Paper trading for early_candidates × early_reversal_break
   using Exit Hypothesis v0 defined in Section 6.

2. BACKTEST-3C (focused) for base_reclaim and ema_reclaim
   after paper-trading phase produces initial observations.

3. Live exit implementation only after out-of-sample validation.
```
