from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from scripts import run_independence_shadow_live as shadow


def _write_gz_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def test_shadow_live_main_writes_summary_with_non_blocking_intraday_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run_daily_scan(_cfg, as_of_date: str | None = None) -> None:
        assert as_of_date == "2026-04-24"
        run_id = "daily-2026-04-24-fake"
        run_dir = tmp_path / "shadow-workdir" / "reports" / "runs" / "2026" / "04" / "24" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        diag = run_dir / "symbol_diagnostics.jsonl.gz"
        _write_gz_jsonl(diag, [{"symbol": "SOLUSDT", "daily_bar_id": "2026-04-24"}])
        manifest = tmp_path / "shadow-workdir" / "snapshots" / "runs" / "2026" / "04" / "24" / run_id / "run.manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("{}\n", encoding="utf-8")
        (run_dir / "report.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "scan_mode": "daily",
                    "daily_bar_id": "2026-04-24",
                    "diagnostics_path": "reports/runs/2026/04/24/daily-2026-04-24-fake/symbol_diagnostics.jsonl.gz",
                    "manifest_path": "snapshots/runs/2026/04/24/daily-2026-04-24-fake/run.manifest.json",
                    "counts_by_bucket": {"watchlist": 1, "early_candidates": 0, "confirmed_candidates": 0, "late_monitor": 0, "discarded": 0},
                    "symbol_lists": {"watchlist": ["SOLUSDT"], "early_candidates": [], "confirmed_candidates": [], "late_monitor": []},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def fake_run_intraday_scan(_cfg, now_utc=None) -> None:
        _ = now_utc
        run_id = "intraday-2026-04-24-fake"
        run_dir = tmp_path / "shadow-workdir" / "reports" / "runs" / "2026" / "04" / "24" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_gz_jsonl(
            run_dir / "symbol_diagnostics.jsonl.gz",
            [{"execution_attempted": False, "reasons": {"intraday_skip_reason": "missing_intraday_cycle_context"}}],
        )
        (run_dir / "report.json").write_text(
            json.dumps({"diagnostics_path": f"reports/runs/2026/04/24/{run_id}/symbol_diagnostics.jsonl.gz"}) + "\n",
            encoding="utf-8",
        )

    def fake_run_eval(*, project_root: Path, config: dict[str, object] | None = None) -> dict[str, object]:
        _ = config
        replay = project_root / "evaluation" / "replay"
        exports = project_root / "evaluation" / "exports"
        replay.mkdir(parents=True, exist_ok=True)
        exports.mkdir(parents=True, exist_ok=True)
        (replay / "event_timeline.jsonl").write_text("{}\n", encoding="utf-8")
        (exports / "evaluation_summary.json").write_text(json.dumps({"cycle_count": 0}) + "\n", encoding="utf-8")
        return {"cycle_count": 0}

    monkeypatch.setattr(shadow, "run_daily_scan", fake_run_daily_scan)
    monkeypatch.setattr(shadow, "run_intraday_scan", fake_run_intraday_scan)
    monkeypatch.setattr(shadow, "run_evaluation_export", fake_run_eval)
    monkeypatch.setattr(shadow, "MEXCClient", lambda *args, **kwargs: type("C", (), {"get_exchange_info": lambda self, **kw: {}})())

    workdir = tmp_path / "shadow-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_shadow_live.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-24T20:00:00Z",
        ],
    )

    rc = shadow.main()
    payload = json.loads((workdir / "shadow-live-report.json").read_text(encoding="utf-8"))

    assert rc == 0
    assert payload["status"] == "pass"
    assert payload["daily"]["status"] == "pass"
    assert payload["evaluation_replay"]["status"] == "pass"
    assert payload["intraday"]["status"] == "non_blocking_warning"
    assert payload["intraday"]["known_state"] == "missing_intraday_cycle_context"


def test_shadow_live_workdir_disallows_reports_analysis(tmp_path: Path) -> None:
    workdir = tmp_path / "shadow"
    target = workdir / "reports" / "analysis" / "x.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")

    forbidden = shadow._collect_forbidden_writes(workdir)
    assert "reports/analysis/x.json" in forbidden
