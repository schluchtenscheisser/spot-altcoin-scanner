import numpy as np
import pytest

from scanner.pipeline.features import FeatureEngine


def test_calc_ema_uses_sma_initialization() -> None:
    """Thema 4 mini reference check: EMA starts from SMA(period), not first value."""
    engine = FeatureEngine(config={})

    # period=3 -> SMA init at t=2: (10 + 11 + 13) / 3 = 11.3333333333
    # alpha = 2/(3+1)=0.5
    # t=3: ema = 0.5*12 + 0.5*11.3333333333 = 11.6666666667
    # t=4: ema = 0.5*14 + 0.5*11.6666666667 = 12.8333333333
    data = np.array([10.0, 11.0, 13.0, 12.0, 14.0], dtype=float)
    ema = engine._calc_ema("TESTUSDT", data, 3)

    assert ema == pytest.approx(12.833333333333334, rel=1e-12, abs=1e-12)


def test_calc_atr_pct_uses_wilder_smoothing() -> None:
    """Thema 5 mini reference check: ATR% uses Wilder recursion after ATR init."""
    engine = FeatureEngine(config={})

    highs = np.array([11.0, 12.0, 13.0, 12.0, 14.0, 13.0], dtype=float)
    lows = np.array([9.0, 10.0, 11.0, 10.0, 12.0, 11.0], dtype=float)
    closes = np.array([10.0, 11.0, 12.0, 11.0, 13.0, 12.0], dtype=float)

    # TRs from t=1..5: [2, 2, 2, 3, 2]
    # period=3 => ATR init = mean([2,2,2]) = 2
    # next: ATR = (2*2 + 3) / 3 = 2.3333333333
    # next: ATR = (2.3333333333*2 + 2) / 3 = 2.2222222222
    # ATR% = 2.2222222222 / close[-1](12) * 100 = 18.5185185185
    atr_pct = engine._calc_atr_pct("TESTUSDT", highs, lows, closes, 3)

    assert atr_pct == pytest.approx(18.51851851851852, rel=1e-12, abs=1e-12)
    assert atr_pct >= 0
