from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scanner.tools import backfill_btc_regime as tool


def _write_snapshot(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _base_snapshot(version: str | None = "1.0", btc_regime=None, btc_1d: dict | None = None) -> dict:
    meta = {"date": "2026-02-01", "asof_ts_ms": 1, "asof_iso": "2026-02-01T00:00:00Z"}
    if version is not None:
        meta["version"] = version
    if btc_regime is not None:
        meta["btc_regime"] = btc_regime

    payload = {"meta": meta, "data": {"features": {}}, "scoring": {}}
    if btc_1d is not None:
        payload["data"]["features"]["BTCUSDT"] = {"1d": btc_1d}
    return payload


def test_backfill_adds_missing_regime_and_bumps_version(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    path = snapshots_dir / "2026-02-01.json"
    _write_snapshot(path, _base_snapshot(version="1.0", btc_1d={"close": 110, "ema_20": 105, "ema_50": 100}))

    rc = tool.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--snapshots-dir",
        str(snapshots_dir),
    ])

    assert rc == 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["meta"]["version"] == "1.1"
    assert payload["meta"]["btc_regime"]["state"] == "RISK_ON"


def test_backfill_preserves_existing_regime_noop(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    path = snapshots_dir / "2026-02-01.json"
    existing = {"state": "RISK_OFF", "multiplier_risk_on": 1.0, "multiplier_risk_off": 0.85, "checks": {}}
    _write_snapshot(path, _base_snapshot(version="1.1", btc_regime=existing))

    before = path.read_text(encoding="utf-8")
    rc = tool.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--snapshots-dir",
        str(snapshots_dir),
    ])

    assert rc == 0
    assert path.read_text(encoding="utf-8") == before


def test_backfill_dry_run_does_not_write(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    path = snapshots_dir / "2026-02-01.json"
    _write_snapshot(path, _base_snapshot(version="1.0", btc_1d={"close": 90, "ema_20": 95, "ema_50": 100}))
    before = path.read_text(encoding="utf-8")

    rc = tool.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--dry-run",
        "--snapshots-dir",
        str(snapshots_dir),
    ])

    assert rc == 0
    assert path.read_text(encoding="utf-8") == before


def test_backfill_strict_missing_exits_nonzero(tmp_path: Path):
    snapshots_dir = tmp_path / "snapshots" / "history"
    _write_snapshot(snapshots_dir / "2026-02-01.json", _base_snapshot(version="1.0", btc_1d={"close": 90}))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scanner.tools.backfill_btc_regime",
            "--from",
            "2026-02-01",
            "--to",
            "2026-02-02",
            "--strict-missing",
            "--snapshots-dir",
            str(snapshots_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Missing" in result.stderr
