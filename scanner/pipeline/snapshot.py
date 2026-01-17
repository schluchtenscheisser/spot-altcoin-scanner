"""
Snapshot creation.

Responsibilities:
- Build a full snapshot object for the current run:
  - spec_version, config_version
  - universe
  - mapping
  - market caps
  - features
  - scores (breakout, pullback, reversal)
  - meta info (runtime, counts, etc.)
- Serialize snapshot as JSON in snapshots/runtime/YYYY-MM-DD.json.
- Guarantee determinism for backtests and regression analysis.

See docs/data_model.md and docs/backtest.md.
"""

