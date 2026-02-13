# Codex -- Critical Findings Remediation Instructions

Generated: 2026-02-13T12:23:34.275505

## Objective

Resolve all items in `All_Setups_Critical_Findings.md`. Ensure
repository reflects mathematically correct implementation.

## Scope

Only address Critical Findings. Do NOT implement Improvement Proposals.

## Mandatory additional Inputs

-   All_Setups_Computation_Transparency.md
-   All_Setups_Critical_Findings.md
-   All_Setups_Improvement_Proposals.md

## Required Fixes

### 1. Unify Base Logic (Reversal)

-   Use `base_score` from FeatureEngine directly.
-   Remove ATR bucket classification from ReversalScorer.
-   Ensure weight 0.25 is applied to continuous base_score.

### 2. Remove Duplicate Base Definitions

-   Only FeatureEngine defines base logic.
-   No base logic in scoring modules.

### 3. Move Thresholds to Config

All scorer thresholds must be config-driven. No hardcoded constants
allowed.

### 4. Continuous Momentum Scaling

Replace step logic with linear scaling:

momentum_score = clamp((r_7 / 10) \* 100, 0, 100)

### 5. Bounded Drawdown

Drawdown lookback = 365 days (configurable). ATH = max(C\_\[t-365:t\])

## Branch

feat/fix-critical-findings

## Tests

Add tests for: - BaseScore mapping - Config thresholds - Drawdown
lookback - Continuous momentum

Tests must fail before implementation and pass after.

## Documentation Update

Update: - All_Setups_Computation_Transparency.md

Remove outdated logic. If schema changes: - bump schema_version - update
SCHEMA_CHANGES.md

## Quality Constraints

-   Score range \[0,100\]
-   No NaN/Inf
-   Deterministic
-   Closed-candle only
-   No lookahead bias

## Definition of Done

-   All critical findings resolved
-   Tests green
-   Documentation consistent
-   PR created with summary
