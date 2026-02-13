# Spot Altcoin Scanner

# Critical Findings -- Immediate Fixes Required

------------------------------------------------------------------------

## 1. Base Detection Mismatch (Reversal)

FeatureEngine provides base_score. ReversalScorer expects base_detected.

Impact: Base weight may evaluate to zero.

------------------------------------------------------------------------

## 2. Duplicate Base Definitions

Continuous base_score vs ATR bucket logic.

------------------------------------------------------------------------

## 3. Hardcoded Parameters

All thresholds embedded in scorer logic.

------------------------------------------------------------------------

## 4. Step-Based Momentum (Breakout & Pullback)

Non-continuous score jumps.

------------------------------------------------------------------------

## 5. Full-History Drawdown

Uses entire available history.
