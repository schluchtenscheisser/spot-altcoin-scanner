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
