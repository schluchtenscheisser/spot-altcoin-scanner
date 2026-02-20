import json
from pathlib import Path

import numpy as np
import pytest

from scanner.pipeline.features import FeatureEngine

FIXTURE_PATH = Path("tests/golden/fixtures/t81_indicator_cases.json")


def _to_array(values: list[float | None]) -> np.ndarray:
    return np.array([np.nan if v is None else v for v in values], dtype=float)


def _load_cases() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _load_cases()["ema"], ids=lambda c: c["name"])
def test_t81_calc_ema_cases(case: dict) -> None:
    engine = FeatureEngine(config={})

    data = _to_array(case["data"])
    result = engine._calc_ema("TESTUSDT", data, case["period"])

    expected = case["expected"]
    if expected is None:
        assert np.isnan(result)
    else:
        assert result == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("case", _load_cases()["atr_pct"], ids=lambda c: c["name"])
def test_t81_calc_atr_pct_cases(case: dict) -> None:
    engine = FeatureEngine(config={})

    highs = _to_array(case["highs"])
    lows = _to_array(case["lows"])
    closes = _to_array(case["closes"])
    result = engine._calc_atr_pct("TESTUSDT", highs, lows, closes, case["period"])

    expected = case["expected"]
    if expected is None:
        assert np.isnan(result)
    else:
        assert result == pytest.approx(expected, rel=1e-12, abs=1e-12)
        assert result >= 0
