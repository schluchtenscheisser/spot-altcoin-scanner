from __future__ import annotations

from ..config import ScannerConfig


def run_pipeline(config: ScannerConfig) -> None:
    """
    Orchestrates the full daily pipeline:

    1. Fetch universe (MEXC Spot USDT)
    2. Fetch market cap listings
    3. Run mapping layer
    4. Apply hard filters (market cap, liquidity, exclusions)
    5. Run cheap pass (shortlist)
    6. Fetch OHLCV for shortlist
    7. Compute features (1d + 4h)
    8. Compute scores (breakout / pullback / reversal)
    9. Write reports (Markdown + JSON)
    10. Write snapshot for backtests
    """

    run_mode = config.run_mode
    print(f"[scanner] run_pipeline started in mode={run_mode}")
    # TODO: Step-by-step implement the stages listed above.

