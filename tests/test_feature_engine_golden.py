import json
import os
from pathlib import Path
from typing import Any

import pytest

from scanner.pipeline.features import FeatureEngine


def _gen_klines(
    n: int,
    start_ts_ms: int,
    step_ms: int,
    start_close: float,
    close_step: float,
    vol_start: float,
    vol_step: float,
) -> list[list[float]]:
    """
    Deterministic kline generator.

    We only need indices [0]=timestamp, [2]=high, [3]=low, [4]=close, [5]=volume
    because FeatureEngine reads exactly those fields.
    """
    klines: list[list[float]] = []

    for i in range(n):
        ts = start_ts_ms + i * step_ms
        c = start_close + i * close_step
        v = vol_start + i * vol_step

        o = c * (1 - 0.002)
        h = c * (1 + 0.01)
        l = c * (1 - 0.01)

        klines.append([int(ts), float(o), float(h), float(l), float(c), float(v)])

    return klines


def _fixture_ohlcv() -> dict[str, dict[str, list[list[float]]]]:
    """
    Minimal-but-valid OHLCV sample for both 1d and 4h.

    Note: FeatureEngine currently returns {} if a timeframe has < 50 candles,
    so we generate 60 candles here (small, but above the threshold).
    """
    start_ts_ms = 1_700_000_000_000  # fixed timestamp -> stable 'last_update'
    return {
        "TESTUSDT": {
            "1d": _gen_klines(
                n=60,
                start_ts_ms=start_ts_ms,
                step_ms=86_400_000,
                start_close=100.0,
                close_step=0.5,
                vol_start=1000.0,
                vol_step=10.0,
            ),
            "4h": _gen_klines(
                n=60,
                start_ts_ms=start_ts_ms,
                step_ms=14_400_000,
                start_close=10.0,
                close_step=0.05,
                vol_start=200.0,
                vol_step=2.0,
            ),
        }
    }


def _assert_close(actual: Any, expected: Any, path: str = "") -> None:
    """
    Deep-compare nested dicts/lists.

    - floats: compared via pytest.approx
    - everything else: strict equality
    """
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual)}"
        assert set(actual.keys()) == set(expected.keys()), f"{path}: key mismatch"
        for k in expected:
            _assert_close(actual[k], expected[k], f"{path}.{k}" if path else k)
        return

    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual)}"
        assert len(actual) == len(expected), f"{path}: length mismatch"
        for i, (a, e) in enumerate(zip(actual, expected)):
            _assert_close(a, e, f"{path}[{i}]")
        return

    if isinstance(expected, float) or isinstance(actual, float):
        if expected is None:
            assert actual is None, f"{path}: expected None, got {actual}"
        else:
            assert actual == pytest.approx(expected, rel=1e-9, abs=1e-9), f"{path}: float mismatch"
        return

    assert actual == expected, f"{path}: value mismatch ({actual} != {expected})"


def test_feature_engine_golden() -> None:
    tests_dir = Path(__file__).resolve().parent
    golden_path = tests_dir / "golden" / "feature_engine_v1_1.json"

    engine = FeatureEngine(config={})
    actual = engine.compute_all(_fixture_ohlcv())

    # Optional: regenerate golden file intentionally
    if os.getenv("UPDATE_GOLDEN") in {"1", "true", "yes"}:
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(
            json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return

    expected = json.loads(golden_path.read_text(encoding="utf-8"))

    # Sanity checks (helpful error messages before deep-compare)
    assert "TESTUSDT" in actual
    for tf in ("1d", "4h", "meta"):
        assert tf in actual["TESTUSDT"]

    _assert_close(actual, expected)


def test_baselines_exclude_current_candle() -> None:
    """Thema 6 invariant: baseline windows must exclude current candle (idx T)."""
    import numpy as np

    engine = FeatureEngine(config={})

    # volume baseline (period=3): use [20, 30, 40], exclude current=100
    volumes = np.array([10.0, 20.0, 30.0, 40.0, 100.0], dtype=float)
    baseline = engine._calc_sma(volumes, 3, include_current=False)
    assert baseline == pytest.approx((20.0 + 30.0 + 40.0) / 3.0, rel=1e-12, abs=1e-12)

    # breakout resistance (lookback=3): prior highs [11, 12, 13], current high=20 must be excluded
    closes = np.array([9.5, 10.5, 11.5, 12.5, 14.0], dtype=float)
    highs = np.array([10.0, 11.0, 12.0, 13.0, 20.0], dtype=float)
    breakout_dist = engine._calc_breakout_distance('TESTUSDT', closes, highs, 3)
    expected = ((14.0 / 13.0) - 1.0) * 100.0
    assert breakout_dist == pytest.approx(expected, rel=1e-12, abs=1e-12)
