from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from scanner.config import resolve_independence_release_reports_config
from scanner.output.diagnostics import write_symbol_diagnostics_jsonl_gz
from scanner.output.report_builder import ReportBuilder
from scanner.output.schema import SCHEMA_VERSION, validate_intraday_bar_id, validate_run_id


def _stub_diag(symbol: str = "STUBUSDT") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": "stub-run-id",
        "scan_mode": "daily",
        "symbol": symbol,
        "as_of_utc": "2026-01-01T00:00:00Z",
        "daily_bar_id": "2025-12-31",
        "intraday_bar_id": None,
        "data_4h_available": False,
        "axes": {},
        "phase": {},
        "invalidation": {},
        "cycle": {},
        "state": {},
        "pattern": {},
        "decision": {},
        "reasons": {},
    }


def test_reports_config_defaults_and_validation() -> None:
    defaults = resolve_independence_release_reports_config({})
    assert defaults == {
        "recent_runs_limit": 30,
        "emit_report_md": False,
        "emit_report_xlsx": False,
    }

    partial = resolve_independence_release_reports_config(
        {"independence_release": {"reports": {"recent_runs_limit": 10}}}
    )
    assert partial == {
        "recent_runs_limit": 10,
        "emit_report_md": False,
        "emit_report_xlsx": False,
    }

    with pytest.raises(ValueError):
        resolve_independence_release_reports_config(
            {"independence_release": {"reports": {"recent_runs_limit": 0}}}
        )

    for invalid in ("oops", 123, []):
        with pytest.raises(ValueError):
            resolve_independence_release_reports_config(
                {"independence_release": {"reports": invalid}}
            )


def test_write_run_report_and_indexes(tmp_path: Path) -> None:
    builder = ReportBuilder(project_root=tmp_path)

    report = builder.write_run_report(
        run_id="opaque-run-id",
        scan_mode="daily",
        as_of_utc="2026-01-01T00:00:00Z",
        daily_bar_id="2025-12-31",
        intraday_bar_id=None,
        symbol_lists={
            "confirmed_candidates": ["AAAUSDT"],
            "early_candidates": ["CCCUSDT"],
            "watchlist": ["BBBUSDT"],
            "late_monitor": ["LATEUSDT"],
        },
        manifest_path="snapshots/runs/2025/12/31/opaque-run-id/run.manifest.json",
        diagnostics_records=[_stub_diag("AAAUSDT"), _stub_diag("BBBUSDT")],
    )

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["intraday_bar_id"] is None
    assert list(report["counts_by_bucket"].keys()) == [
        "watchlist",
        "early_candidates",
        "confirmed_candidates",
        "late_monitor",
        "discarded",
    ]
    assert list(report["symbol_lists"].keys()) == [
        "confirmed_candidates",
        "early_candidates",
        "watchlist",
        "late_monitor",
    ]

    run_base = tmp_path / "reports" / "runs" / "2025" / "12" / "31" / "opaque-run-id"
    report_path = run_base / "report.json"
    diag_path = run_base / "symbol_diagnostics.jsonl.gz"
    assert report_path.exists()
    assert diag_path.exists()

    latest = json.loads((tmp_path / "reports" / "index" / "latest.json").read_text(encoding="utf-8"))
    persisted_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert latest == persisted_report

    latest_confirmed = json.loads(
        (tmp_path / "reports" / "index" / "latest_confirmed_candidates.json").read_text(encoding="utf-8")
    )
    assert latest_confirmed == ["AAAUSDT"]
    assert "LATEUSDT" not in latest_confirmed

    lines = gzip.decompress(diag_path.read_bytes()).decode("utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["intraday_bar_id"] is None
    assert first["data_4h_available"] is False


def test_recent_runs_limit_newest_first(tmp_path: Path) -> None:
    cfg = {"independence_release": {"reports": {"recent_runs_limit": 2}}}
    builder = ReportBuilder(project_root=tmp_path, config=cfg)

    for run_id, as_of in [
        ("run-1", "2026-01-01T00:00:00Z"),
        ("run-2", "2026-01-02T00:00:00Z"),
        ("run-3", "2026-01-03T00:00:00Z"),
    ]:
        builder.write_run_report(
            run_id=run_id,
            scan_mode="daily",
            as_of_utc=as_of,
            daily_bar_id="2026-01-03",
            intraday_bar_id=None,
            symbol_lists={},
            manifest_path=f"snapshots/runs/2026/01/03/{run_id}/run.manifest.json",
            diagnostics_records=[_stub_diag("AAAUSDT")],
        )

    recent = json.loads((tmp_path / "reports" / "index" / "recent_runs.json").read_text(encoding="utf-8"))
    assert [x["run_id"] for x in recent] == ["run-3", "run-2"]


def test_write_daily_report_and_latest_daily(tmp_path: Path) -> None:
    builder = ReportBuilder(project_root=tmp_path)
    report = builder.write_run_report(
        run_id="run-daily",
        scan_mode="daily",
        as_of_utc="2026-01-05T00:00:00Z",
        daily_bar_id="2026-01-04",
        intraday_bar_id=None,
        symbol_lists={},
        manifest_path="snapshots/runs/2026/01/04/run-daily/run.manifest.json",
        diagnostics_records=[_stub_diag("AAAUSDT")],
    )

    builder.write_daily_report(report)

    daily_path = tmp_path / "reports" / "daily" / "2026" / "01" / "04" / "report.json"
    assert daily_path.exists()
    latest_daily = json.loads((tmp_path / "reports" / "index" / "latest_daily.json").read_text(encoding="utf-8"))
    assert latest_daily == json.loads(daily_path.read_text(encoding="utf-8"))


def test_diagnostics_gzip_bytes_are_deterministic(tmp_path: Path) -> None:
    one = tmp_path / "one.jsonl.gz"
    two = tmp_path / "two.jsonl.gz"
    records = [_stub_diag("AAAUSDT"), _stub_diag("BBBUSDT")]

    write_symbol_diagnostics_jsonl_gz(one, records)
    write_symbol_diagnostics_jsonl_gz(two, records)

    assert one.read_bytes() == two.read_bytes()


def test_run_id_rejects_path_traversal_and_separators() -> None:
    invalid_ids = [
        "../x",
        "../../foo",
        "a/b",
        r"a\\b",
        "/abs",
        "C:\\temp",
        "..hidden",
        "has space",
    ]
    for candidate in invalid_ids:
        with pytest.raises(ValueError):
            validate_run_id(candidate)

    assert validate_run_id("safe-run_01.v1") == "safe-run_01.v1"


def test_reports_doc_and_ticket_preflight_path_compatibility() -> None:
    reports_doc = Path("docs/canonical/REPORTS.md").read_text(encoding="utf-8")
    assert "Verbindliche Dateitypen" in reports_doc
    assert Path("docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md").exists()


def test_intraday_bar_id_validation_accepts_canonical_strings_and_rejects_ints() -> None:
    assert validate_intraday_bar_id("intraday", "2026-04-24T08:00:00Z") == "2026-04-24T08:00:00Z"
    with pytest.raises(ValueError, match="YYYY-MM-DDTHH:00:00Z"):
        validate_intraday_bar_id("intraday", 1774324800000)
