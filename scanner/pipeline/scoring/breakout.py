"""
Breakout scoring module.

Responsibilities:
- Identify range breaks vs recent highs (e.g. 20–30d high).
- Confirm with volume spike vs volume SMA.
- Penalize late-stage, overextended breakouts and extreme volatility.
- Produce a 0–100 breakout score per asset with components and flags.

See docs/scoring.md for detailed logic.
"""

