from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scanner.tools import backfill_snapshots as tool


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_ohlcv_day(cache_root: Path, day: str, symbol: str, high: float, low: float, close: float) -> None:
    open_time_ms = 1767139200000  # 2026-01-01T00:00:00Z, overwritten below if needed by day parsing fallback
    # Build deterministic timestamp from day string without external deps
    yyyy, mm, dd = map(int, day.split("-"))
    from datetime import datetime, timezone

    open_time_ms = int(datetime(yyyy, mm, dd, tzinfo=timezone.utc).timestamp() * 1000)
    payload = [[open_time_ms, "1", str(high), str(low), str(close), "10", open_time_ms + 86_399_999, "100"]]
    _write_json(cache_root / day / f"mexc_klines_{symbol}_1d.json", payload)


def test_creates_missing_snapshot_with_minimal_ohlcv_fields(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    ohlcv_root = tmp_path / "data" / "raw"
    _write_ohlcv_day(ohlcv_root, "2026-02-01", "AAAUSDT", high=12.5, low=10.0, close=11.5)
    _write_ohlcv_day(ohlcv_root, "2026-02-01", "BTCUSDT", high=110000, low=100000, close=105000)

    rc = tool.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--snapshots-dir",
        str(snapshots_dir),
        "--ohlcv-cache-dir",
        str(ohlcv_root),
    ])

    assert rc == 0
    snapshot_path = snapshots_dir / "2026-02-01.json"
    assert snapshot_path.exists()
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert payload["meta"]["backfill"] is True
    assert payload["meta"]["backfill_mode"] == "minimal"
    assert payload["meta"]["backfill_source"] == "ohlcv_only"
    assert payload["scoring"] == {"reversals": [], "breakouts": [], "pullbacks": []}

    assert list(payload["data"]["features"].keys()) == ["AAAUSDT", "BTCUSDT"]
    assert payload["data"]["features"]["AAAUSDT"]["1d"] == {"close": 11.5, "high": 12.5, "low": 10.0}


def test_existing_snapshot_is_skipped_by_default(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    existing = snapshots_dir / "2026-02-01.json"
    _write_json(existing, {"meta": {"date": "2026-02-01"}, "pipeline": {}, "data": {"features": {}}, "scoring": {}})

    rc = tool.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--snapshots-dir",
        str(snapshots_dir),
        "--ohlcv-cache-dir",
        str(tmp_path / "does-not-matter"),
    ])

    assert rc == 0
    payload = json.loads(existing.read_text(encoding="utf-8"))
    assert payload["meta"]["date"] == "2026-02-01"


def test_strict_existing_fails_if_snapshot_exists(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    _write_json(snapshots_dir / "2026-02-01.json", {"meta": {"date": "2026-02-01"}})

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scanner.tools.backfill_snapshots",
            "--from",
            "2026-02-01",
            "--to",
            "2026-02-01",
            "--strict-existing",
            "--snapshots-dir",
            str(snapshots_dir),
            "--ohlcv-cache-dir",
            str(tmp_path / "data" / "raw"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "already exists" in result.stderr


def test_dry_run_creates_no_files(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    ohlcv_root = tmp_path / "data" / "raw"
    _write_ohlcv_day(ohlcv_root, "2026-02-01", "AAAUSDT", high=2.0, low=1.0, close=1.5)

    rc = tool.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--dry-run",
        "--snapshots-dir",
        str(snapshots_dir),
        "--ohlcv-cache-dir",
        str(ohlcv_root),
    ])

    assert rc == 0
    assert not (snapshots_dir / "2026-02-01.json").exists()


def test_missing_local_ohlcv_source_fails_clearly(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scanner.tools.backfill_snapshots",
            "--from",
            "2026-02-01",
            "--to",
            "2026-02-01",
            "--snapshots-dir",
            str(snapshots_dir),
            "--ohlcv-cache-dir",
            str(tmp_path / "missing-cache"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "No local OHLCV cache files found" in result.stderr


def test_strict_missing_is_atomic_for_minimal_mode(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    ohlcv_root = tmp_path / "data" / "raw"
    _write_ohlcv_day(ohlcv_root, "2026-02-01", "AAAUSDT", high=12.5, low=10.0, close=11.5)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scanner.tools.backfill_snapshots",
            "--from",
            "2026-02-01",
            "--to",
            "2026-02-02",
            "--strict-missing",
            "--snapshots-dir",
            str(snapshots_dir),
            "--ohlcv-cache-dir",
            str(ohlcv_root),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Strict preflight failed" in result.stderr
    assert not (snapshots_dir / "2026-02-01.json").exists()


def test_uses_snapshot_dir_fallback(tmp_path: Path):
    snapshot_dir = tmp_path / "custom_snapshots"
    history_dir = snapshot_dir / "history"
    ohlcv_root = tmp_path / "data" / "raw"
    _write_ohlcv_day(ohlcv_root, "2026-02-01", "AAAUSDT", high=12.5, low=10.0, close=11.5)

    config_path = tmp_path / "config.yml"
    config_path.write_text(f"snapshots:\n  snapshot_dir: \"{snapshot_dir.as_posix()}\"\n", encoding="utf-8")

    rc = tool.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--config",
        str(config_path),
        "--ohlcv-cache-dir",
        str(ohlcv_root),
    ])

    assert rc == 0
    assert (history_dir / "2026-02-01.json").exists()


def test_full_mode_time_patch_uses_target_cache_date(tmp_path: Path):
    from datetime import date
    from scanner.utils import io_utils
    from scanner.tools.backfill_snapshots import _patched_full_mode_time_sources

    with _patched_full_mode_time_sources(date(2026, 2, 1)):
        cache_path = io_utils.get_cache_path("probe")

    assert cache_path.parts[-2] == "2026-02-01"
