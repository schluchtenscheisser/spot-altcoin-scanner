import json
from pathlib import Path

from scanner.config import ScannerConfig
from scanner.pipeline.runtime_market_meta import RuntimeMarketMetaExporter
from scanner.pipeline.snapshot import SnapshotManager


def test_snapshot_and_runtime_meta_use_separate_default_namespaces(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = ScannerConfig(raw={})

    snapshot_mgr = SnapshotManager(cfg)
    runtime_exporter = RuntimeMarketMetaExporter(cfg)

    assert snapshot_mgr.snapshots_dir == Path("snapshots/history")
    assert runtime_exporter.runtime_dir == Path("snapshots/runtime")


def test_list_snapshots_ignores_non_snapshot_json_schemas(tmp_path: Path) -> None:
    cfg = ScannerConfig(raw={"snapshots": {"history_dir": str(tmp_path)}})
    snapshot_mgr = SnapshotManager(cfg)

    valid_snapshot = {
        "meta": {"date": "2026-02-12"},
        "pipeline": {},
        "data": {},
        "scoring": {},
    }
    (tmp_path / "2026-02-12.json").write_text(json.dumps(valid_snapshot), encoding="utf-8")

    runtime_meta_like = {"meta": {"run_id": "1"}, "universe": {}, "coins": {}}
    (tmp_path / "runtime_market_meta_2026-02-12.json").write_text(
        json.dumps(runtime_meta_like), encoding="utf-8"
    )

    (tmp_path / "not-a-date.json").write_text("{}", encoding="utf-8")
    (tmp_path / "2026-02-13.json").write_text("{invalid-json", encoding="utf-8")

    assert snapshot_mgr.list_snapshots() == ["2026-02-12"]



def test_create_snapshot_persists_btc_regime_and_version_1_1(tmp_path: Path) -> None:
    cfg = ScannerConfig(raw={"snapshots": {"history_dir": str(tmp_path)}})
    snapshot_mgr = SnapshotManager(cfg)

    btc_regime = {
        "state": "RISK_ON",
        "multiplier_risk_on": 1.0,
        "multiplier_risk_off": 0.85,
        "checks": {"close_gt_ema50": True, "ema20_gt_ema50": True},
    }

    snapshot_path = snapshot_mgr.create_snapshot(
        run_date="2026-02-27",
        universe=[{"symbol": "BTCUSDT"}],
        filtered=[{"symbol": "BTCUSDT"}],
        shortlist=[{"symbol": "BTCUSDT"}],
        features={"BTCUSDT": {"close": 100000}},
        reversal_scores=[],
        breakout_scores=[],
        pullback_scores=[],
        metadata={
            "mode": "fast",
            "asof_ts_ms": 1700000000000,
            "asof_iso": "2026-02-27T00:00:00Z",
            "btc_regime": btc_regime,
        },
    )

    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert payload["meta"]["version"] == "1.1"
    assert payload["meta"]["btc_regime"] == btc_regime
    assert payload["meta"]["date"] == "2026-02-27"
    assert payload["meta"]["asof_ts_ms"] == 1700000000000
    assert payload["meta"]["asof_iso"] == "2026-02-27T00:00:00Z"
