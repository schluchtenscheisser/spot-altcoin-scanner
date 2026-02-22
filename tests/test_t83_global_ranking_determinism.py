import json
import os
from pathlib import Path
from typing import Any

import pytest

from scanner.pipeline.global_ranking import compute_global_top20


FIELDS = [
    "rank",
    "symbol",
    "best_setup_type",
    "setup_score",
    "setup_weight",
    "best_setup_score",
    "global_score",
    "confluence",
    "valid_setups",
    "slippage_bps",
    "proxy_liquidity_score",
    "source",
]


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


def test_t83_global_ranking_tie_matrix_and_confluence_golden() -> None:
    tests_dir = Path(__file__).resolve().parent
    fixture_path = tests_dir / "golden" / "fixtures" / "global_ranking_t83_snapshots.json"
    golden_path = tests_dir / "golden" / "t83_global_ranking_expected.json"

    fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    actual = compute_global_top20(
        reversal_results=fixture_payload["reversal_results"],
        breakout_results=fixture_payload["breakout_results"],
        pullback_results=fixture_payload["pullback_results"],
        config=fixture_payload["config"],
    )
    actual_projected = [{field: row.get(field) for field in FIELDS} for row in actual]

    if os.getenv("UPDATE_GOLDEN") in {"1", "true", "yes"}:
        golden_path.write_text(
            json.dumps(actual_projected, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return

    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    _assert_close(actual_projected, expected)

    assert len(actual) == len({row["symbol"] for row in actual})

    dup = next(row for row in actual if row["symbol"] == "DUPUSDT")
    assert dup["best_setup_type"] == "reversal"
    assert dup["confluence"] == 3
    assert dup["valid_setups"] == ["breakout", "pullback", "reversal"]

    bbb = next(row for row in actual if row["symbol"] == "BBBUSDT")
    assert bbb["global_score"] == pytest.approx(100.0)
    assert bbb["best_setup_type"] == "reversal"
