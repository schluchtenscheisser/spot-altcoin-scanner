from pathlib import Path

import pytest

from scanner.evaluation.historical_replay.scenario import load_scenario, scenario_config_hash
from scanner.evaluation.historical_replay.scenario_registry import ensure_scenario_hash


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "scenario.yml"
    p.write_text(content, encoding="utf-8")
    return p


def test_scenario_hash_excludes_splits(tmp_path: Path) -> None:
    common = """
scenario_id: s1
history_dataset_ref: snapshots/history/ohlcv
history_manifest_ref: snapshots/history/manifests/history_manifest.json
universe_manifest_ref: snapshots/history/manifests/universe_manifest.json
evaluation: {start_date: 2025-01-01, end_date: 2025-01-31}
timeframes: [1d, 4h]
universe_mode: fixed
execution: {mode: disabled_historical_ohlcv_only}
scanner_config: {ref: config/config.yml, hash: abc}
regime_labels: {method_ref: x}
daily_replay_time_policy: {settlement_delay_seconds: 0}
warmup: {warm_up_1d_bars: 120, warm_up_4h_bars: 120}
"""
    a = load_scenario(_write(tmp_path, common + "splits:\n  calibration: {start_date: 2025-01-01, end_date: 2025-01-10}\n"))
    b = load_scenario(_write(tmp_path, common + "splits:\n  calibration: {start_date: 2025-01-01, end_date: 2025-01-12}\n"))
    assert scenario_config_hash(a) == scenario_config_hash(b)


def test_registry_rejects_hash_change(tmp_path: Path) -> None:
    reg = tmp_path / "scenario_registry.sqlite"
    ensure_scenario_hash(registry_path=reg, scenario_id="abc", scenario_hash="h1", scenario_path="a.yml")
    with pytest.raises(ValueError):
        ensure_scenario_hash(registry_path=reg, scenario_id="abc", scenario_hash="h2", scenario_path="b.yml")


def test_rejects_datetime_in_date_field(tmp_path: Path) -> None:
    scenario = _write(
        tmp_path,
        """
scenario_id: s1
history_dataset_ref: a
history_manifest_ref: b
universe_manifest_ref: c
evaluation: {start_date: 2025-01-01T00:00:00Z, end_date: 2025-01-31}
timeframes: [1d, 4h]
universe_mode: fixed
execution: {mode: disabled_historical_ohlcv_only}
scanner_config: {ref: config/config.yml, hash: abc}
regime_labels: {method_ref: x}
daily_replay_time_policy: {settlement_delay_seconds: 0}
warmup: {warm_up_1d_bars: 120, warm_up_4h_bars: 120}
""",
    )
    with pytest.raises(ValueError):
        load_scenario(scenario)
