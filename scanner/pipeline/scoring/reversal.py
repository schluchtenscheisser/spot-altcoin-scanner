"""
Reversal scoring module.

Responsibilities:
- Detect drawdown context vs ATH.
- Identify base formation (no new lows for K days).
- Detect reclaim of key levels/EMAs.
- Confirm with volume spike.
- Penalize falling knife conditions and extreme volatility.
- Produce a 0–100 reversal score per asset with components and flags.

See docs/scoring.md for detailed logic.
"""

