"""
Trend pullback scoring module.

Responsibilities:
- Detect established uptrends (EMA / HH/HL structure).
- Measure pullback depth from recent highs.
- Detect rebound signals (EMA reclaim, short-term momentum, volume).
- Produce a 0–100 pullback score per asset with components and flags.

See docs/scoring.md for detailed logic.
"""

