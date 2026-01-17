"""
Universe filters.

Responsibilities:
- Apply hard filters to the raw tradable universe:
  - market cap range (MidCaps)
  - minimum 24h quote volume
  - minimum history length (1d candles)
  - category exclusions (stablecoins, wrapped, leveraged, synthetic)
- Prepare the filtered asset list for the cheap shortlist pass.
"""

