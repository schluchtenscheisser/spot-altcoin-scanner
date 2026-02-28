from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from scanner.tools import export_evaluation_dataset as exporter


FIXTURE_DIR = Path("tests/fixtures/snapshots/history")


def _copy_snapshots(tmp_path: Path) -> Path:
    target = tmp_path / "snapshots" / "history"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE_DIR, target)
    return target


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_export_meta_and_candidate_count_and_file_scope_run_id(tmp_path: Path, monkeypatch):
    snapshots_dir = _copy_snapshots(tmp_path)
    output_dir = tmp_path / "datasets" / "eval"

    monkeypatch.setattr(exporter, "_utc_now", lambda: exporter.datetime(2026, 2, 10, 11, 22, 33, 482000, tzinfo=exporter.timezone.utc))

    rc = exporter.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-03",
        "--snapshots-dir",
        str(snapshots_dir),
        "--output-dir",
        str(output_dir),
    ])

    assert rc == 0
    out = output_dir / "eval_2026-02-10_112233Z_482.jsonl"
    rows = _load_jsonl(out)
    assert rows[0]["type"] == "meta"
    assert rows[0]["run_id"] == "2026-02-10_112233Z_482"
    assert rows[0]["export_run_id"] == "2026-02-10_112233Z_482"
    assert rows[0]["export_started_at_ts_ms"] == 1770722553482
    assert rows[0]["source_snapshot_dates"] == ["2026-02-01", "2026-02-02", "2026-02-03"]
    assert rows[0]["source_snapshot_count"] == 3

    candidates = [r for r in rows[1:] if r["type"] == "candidate_setup"]
    # day1: 22 setups, day2: 1 setup, day3: 0
    assert len(candidates) == 23
    assert {candidate["run_id"] for candidate in candidates} == {"2026-02-10_112233Z_482"}


def test_default_run_id_is_unique_within_same_minute(tmp_path: Path, monkeypatch):
    snapshots_dir = _copy_snapshots(tmp_path)
    output_dir = tmp_path / "datasets" / "eval"

    times = iter([
        exporter.datetime(2026, 2, 10, 11, 22, 33, 101000, tzinfo=exporter.timezone.utc),
        exporter.datetime(2026, 2, 10, 11, 22, 33, 987000, tzinfo=exporter.timezone.utc),
    ])
    monkeypatch.setattr(exporter, "_utc_now", lambda: next(times))

    first_rc = exporter.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--snapshots-dir",
        str(snapshots_dir),
        "--output-dir",
        str(output_dir),
    ])
    second_rc = exporter.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-01",
        "--snapshots-dir",
        str(snapshots_dir),
        "--output-dir",
        str(output_dir),
    ])

    assert first_rc == 0
    assert second_rc == 0

    first = output_dir / "eval_2026-02-10_112233Z_101.jsonl"
    second = output_dir / "eval_2026-02-10_112233Z_987.jsonl"
    assert first.exists()
    assert second.exists()

    first_rows = _load_jsonl(first)
    second_rows = _load_jsonl(second)
    assert first_rows[0]["run_id"] != second_rows[0]["run_id"]
    assert first_rows[1]["record_id"].split(":")[0] != second_rows[1]["record_id"].split(":")[0]


def test_export_ordering_btc_regime_and_global_rank_top20_only(tmp_path: Path):
    snapshots_dir = _copy_snapshots(tmp_path)
    output_dir = tmp_path / "datasets" / "eval"

    rc = exporter.main([
        "--from",
        "2026-02-01",
        "--to",
        "2026-02-03",
        "--run-id",
        "RUN42",
        "--snapshots-dir",
        str(snapshots_dir),
        "--output-dir",
        str(output_dir),
    ])
    assert rc == 0

    rows = _load_jsonl(output_dir / "eval_RUN42.jsonl")
    candidates = rows[1:]

    sort_keys = [(r["t0_date"], r["setup_type"], r["setup_rank"], r["symbol"]) for r in candidates]
    assert sort_keys == sorted(sort_keys)

    s20 = next(r for r in candidates if r["symbol"] == "S20USDT")
    s21 = next(r for r in candidates if r["symbol"] == "S21USDT")
    assert s20["global_rank"] == 20
    assert s21["global_rank"] is None

    pull = next(r for r in candidates if r["symbol"] == "PULLUSDT")
    assert pull["btc_regime"] is None
    assert pull["record_id"] == "RUN42:2026-02-02:PULLUSDT:pullback:pb_test"


def test_strict_missing_exits_nonzero(tmp_path: Path):
    snapshots_dir = _copy_snapshots(tmp_path)
    output_dir = tmp_path / "datasets" / "eval"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scanner.tools.export_evaluation_dataset",
            "--from",
            "2026-02-01",
            "--to",
            "2026-02-04",
            "--strict-missing",
            "--snapshots-dir",
            str(snapshots_dir),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Missing" in result.stderr


def test_golden_jsonl_output(tmp_path: Path, monkeypatch):
    snapshots_dir = _copy_snapshots(tmp_path)
    output_dir = tmp_path / "datasets" / "eval"
    monkeypatch.setattr(exporter, "_utc_now", lambda: exporter.datetime(2026, 2, 10, 0, 0, 0, 0, tzinfo=exporter.timezone.utc))

    rc = exporter.main([
        "--from",
        "2026-02-02",
        "--to",
        "2026-02-02",
        "--run-id",
        "RID",
        "--snapshots-dir",
        str(snapshots_dir),
        "--output-dir",
        str(output_dir),
    ])
    assert rc == 0

    content = (output_dir / "eval_RID.jsonl").read_text(encoding="utf-8")
    expected = "\n".join([
        '{"type":"meta","run_id":"RID","from_date":"2026-02-02","to_date":"2026-02-02","exported_at_iso":"2026-02-10T00:00:00Z","export_started_at_ts_ms":1770681600000,"export_run_id":"RID","source_snapshot_count":1,"source_snapshot_dates":["2026-02-02"],"thresholds_pct":[10.0,20.0],"T_hold":10,"T_trigger_max":5,"dataset_schema_version":"1.2","notes":null}',
        '{"asof_iso":"2026-02-02T00:00:00Z","asof_ts_ms":1770086400000,"btc_regime":null,"entry_price":10.0,"global_rank":1,"hit_10":null,"hit_20":null,"hits":{"10":null,"20":null},"liquidity_grade":"C","mae_pct":null,"market_cap_usd":1234,"mfe_pct":null,"quote_volume_24h_usd":4567,"reason":"insufficient_forward_history","record_id":"RID:2026-02-02:PULLUSDT:pullback:pb_test","run_id":"RID","score":55.5,"setup_id":"pb_test","setup_rank":1,"setup_type":"pullback","snapshot_version":"1.1","symbol":"PULLUSDT","t0_date":"2026-02-02","t_trigger_date":"2026-02-02","t_trigger_day_offset":0,"type":"candidate_setup"}',
        "",
    ])

    assert content == expected
