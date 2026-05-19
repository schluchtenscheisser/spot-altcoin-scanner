from pathlib import Path
import subprocess
import sys

import pytest

from scanner.evaluation.historical_replay.scenario import load_scenario, scenario_config_hash
from scanner.evaluation.historical_replay.scenario_registry import ensure_scenario_hash


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "scenario.yml"
    p.write_text(content, encoding="utf-8")
    return p


def _base_scenario(timeframes: str = "[1d, 4h]", policy: str = "{settlement_delay_seconds: 0}", warmup: str = "{warm_up_1d_bars: 120, warm_up_4h_bars: 120}") -> str:
    return f"""
scenario_id: s1
history_dataset_ref: snapshots/history/ohlcv
history_manifest_ref: snapshots/history/manifests/history_manifest.json
universe_manifest_ref: snapshots/history/manifests/universe_manifest.json
evaluation: {{start_date: 2025-01-01, end_date: 2025-01-31}}
timeframes: {timeframes}
universe_mode: fixed
execution: {{mode: disabled_historical_ohlcv_only}}
scanner_config: {{ref: config/config.yml, hash: abc}}
regime_labels: {{method_ref: x}}
daily_replay_time_policy: {policy}
warmup: {warmup}
"""


def test_scenario_hash_excludes_splits(tmp_path: Path) -> None:
    common = _base_scenario()
    a = load_scenario(_write(tmp_path, common + "splits:\n  calibration: {start_date: 2025-01-01, end_date: 2025-01-10}\n"))
    b = load_scenario(_write(tmp_path, common + "splits:\n  calibration: {start_date: 2025-01-01, end_date: 2025-01-12}\n"))
    assert scenario_config_hash(a) == scenario_config_hash(b)


def test_timeframes_are_canonicalized_for_hash(tmp_path: Path) -> None:
    a = load_scenario(_write(tmp_path, _base_scenario(timeframes="[1d, 4h]")))
    b = load_scenario(_write(tmp_path, _base_scenario(timeframes="[4h, 1d]")))
    assert a.timeframes == ("1d", "4h")
    assert b.timeframes == ("1d", "4h")
    assert scenario_config_hash(a) == scenario_config_hash(b)


@pytest.mark.parametrize("timeframes", ["[1d, 1d, 4h]", "[1d, 2h]"])
def test_invalid_timeframes_fail(tmp_path: Path, timeframes: str) -> None:
    with pytest.raises(ValueError):
        load_scenario(_write(tmp_path, _base_scenario(timeframes=timeframes)))


@pytest.mark.parametrize(
    "policy,warmup",
    [
        ("{}", "{warm_up_1d_bars: 120, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: 0}", "{warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: 0}", "{warm_up_1d_bars: 120}"),
    ],
)
def test_missing_required_numeric_fields_fail_cleanly(tmp_path: Path, policy: str, warmup: str) -> None:
    with pytest.raises(ValueError):
        load_scenario(_write(tmp_path, _base_scenario(policy=policy, warmup=warmup)))


@pytest.mark.parametrize(
    "policy,warmup",
    [
        ("{settlement_delay_seconds: null}", "{warm_up_1d_bars: 120, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: '0'}", "{warm_up_1d_bars: 120, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: 0.5}", "{warm_up_1d_bars: 120, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: true}", "{warm_up_1d_bars: 120, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: -1}", "{warm_up_1d_bars: 120, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: 0}", "{warm_up_1d_bars: '120', warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: 0}", "{warm_up_1d_bars: 120.5, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: 0}", "{warm_up_1d_bars: true, warm_up_4h_bars: 120}"),
        ("{settlement_delay_seconds: 0}", "{warm_up_1d_bars: -1, warm_up_4h_bars: 120}"),
    ],
)
def test_invalid_required_numeric_fields_fail_cleanly(tmp_path: Path, policy: str, warmup: str) -> None:
    with pytest.raises(ValueError):
        load_scenario(_write(tmp_path, _base_scenario(policy=policy, warmup=warmup)))


def test_registry_rejects_hash_change(tmp_path: Path) -> None:
    reg = tmp_path / "scenario_registry.sqlite"
    ensure_scenario_hash(registry_path=reg, scenario_id="abc", scenario_hash="h1", scenario_path="a.yml")
    with pytest.raises(ValueError):
        ensure_scenario_hash(registry_path=reg, scenario_id="abc", scenario_hash="h2", scenario_path="b.yml")


def test_rejects_datetime_in_date_field(tmp_path: Path) -> None:
    scenario = _write(tmp_path, _base_scenario().replace("2025-01-01", "2025-01-01T00:00:00Z", 1))
    with pytest.raises(ValueError):
        load_scenario(scenario)


def test_cli_dry_run_validation_failure_is_clean(tmp_path: Path) -> None:
    scenario_path = _write(tmp_path, _base_scenario(policy="{}"))
    cmd = [sys.executable, "-m", "scanner.tools.run_historical_daily_replay", "--scenario", str(scenario_path), "--dry-run-validate-scenario"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert "Scenario validation failed:" in result.stderr
    assert "Traceback" not in result.stderr
