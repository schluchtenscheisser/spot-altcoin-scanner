import json
import os
from pathlib import Path
from typing import Any

import pytest

from scanner.pipeline.backtest_runner import run_backtest_from_snapshots


def _assert_close(actual: Any, expected: Any, path: str = "") -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual)}"
        assert set(actual.keys()) == set(expected.keys()), f"{path}: key mismatch"
        for key in expected:
            _assert_close(actual[key], expected[key], f"{path}.{key}" if path else key)
        return

    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual)}"
        assert len(actual) == len(expected), f"{path}: length mismatch"
        for idx, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            _assert_close(actual_item, expected_item, f"{path}[{idx}]")
        return

    if isinstance(expected, float) or isinstance(actual, float):
        if expected is None:
            assert actual is None, f"{path}: expected None, got {actual}"
        else:
            assert actual == pytest.approx(expected, rel=1e-9, abs=1e-9), f"{path}: float mismatch"
        return

    assert actual == expected, f"{path}: value mismatch ({actual} != {expected})"


def test_t84_backtest_golden_fixture() -> None:
    tests_dir = Path(__file__).resolve().parent
    fixture_path = tests_dir / "golden" / "fixtures" / "backtest_t84_snapshots.json"
    golden_path = tests_dir / "golden" / "backtest_t84_expected.json"

    fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    snapshots = fixture_payload["snapshots"]
    config = fixture_payload["config"]

    actual = run_backtest_from_snapshots(snapshots, config=config)

    if os.getenv("UPDATE_GOLDEN") in {"1", "true", "yes"}:
        golden_path.write_text(
            json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return

    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    _assert_close(actual, expected)

    breakout_event = actual["events"]["breakout"][0]
    pullback_event = actual["events"]["pullback"][0]
    reversal_event = actual["events"]["reversal"][0]

    assert breakout_event["triggered"] is True
    assert breakout_event["hit_10"] is True
    assert breakout_event["hit_20"] is True

    assert pullback_event["triggered"] is False

    assert reversal_event["triggered"] is True
    assert reversal_event["hit_10"] is True
    assert reversal_event["hit_20"] is False
