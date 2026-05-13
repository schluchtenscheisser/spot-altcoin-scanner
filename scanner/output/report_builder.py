from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, Mapping, Iterable

from scanner.config import resolve_independence_release_reports_config
from .diagnostics import write_symbol_diagnostics_jsonl_gz
from .schema import (
    RunReport,
    normalize_symbol_lists,
    normalize_counts_by_bucket,
    validate_daily_bar_id,
    validate_diagnostics_record,
)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(path, json.dumps(payload, sort_keys=True, indent=2) + "\n")


def _date_parts_from_daily_bar_id(daily_bar_id: str) -> tuple[str, str, str]:
    validated = validate_daily_bar_id(daily_bar_id)
    year, month, day = validated.split("-")
    return year, month, day


def _sort_newest_first(entries: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return sorted(entries, key=lambda x: (x["as_of_utc"], x["run_id"]), reverse=True)


class ReportBuilder:
    def __init__(self, project_root: Path, config: Mapping[str, Any] | None = None):
        self.project_root = project_root
        self.reports_root = project_root / "reports"
        self.index_root = self.reports_root / "index"
        self.config = resolve_independence_release_reports_config(config or {})

    def write_run_report(
        self,
        *,
        run_id: str,
        scan_mode: str,
        as_of_utc: str,
        daily_bar_id: str,
        intraday_bar_id: str | None,
        symbol_lists: Mapping[str, list[str]] | None,
        manifest_path: str,
        diagnostics_records: Iterable[Mapping[str, Any]],
        counts_by_bucket: Mapping[str, int] | None = None,
        extra_report_fields: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        produced_symbol_list_keys = set((symbol_lists or {}).keys())
        symbol_lists_normalized = normalize_symbol_lists(symbol_lists)
        counts = normalize_counts_by_bucket(counts_by_bucket)
        if counts_by_bucket is None:
            counts = {
                **counts,
                "confirmed_candidates": len(symbol_lists_normalized["confirmed_candidates"]),
                "early_candidates": len(symbol_lists_normalized["early_candidates"]),
                "watchlist": len(symbol_lists_normalized["watchlist"]),
                "late_monitor": len(symbol_lists_normalized["late_monitor"]),
            }

        year, month, day = _date_parts_from_daily_bar_id(daily_bar_id)
        run_dir = self.reports_root / "runs" / year / month / day / run_id
        diagnostics_path_rel = run_dir.relative_to(self.project_root) / "symbol_diagnostics.jsonl.gz"
        report_path_rel = run_dir.relative_to(self.project_root) / "report.json"

        # Materialize once so the writer and index semantics use the same
        # diagnostics record count without adding another persisted report field.
        diagnostics_records_list = [validate_diagnostics_record(record) for record in diagnostics_records]
        diagnostics_record_count = len(diagnostics_records_list)
        excluded_symbols = {
            str(record["symbol"])
            for record in diagnostics_records_list
            if record.get("candidate_excluded") is True
        }
        for key in ("confirmed_candidates", "early_candidates", "watchlist"):
            symbol_lists_normalized[key] = [
                symbol for symbol in symbol_lists_normalized[key] if symbol not in excluded_symbols
            ]
        for key in ("confirmed_candidates", "early_candidates", "watchlist"):
            counts[key] = len(symbol_lists_normalized[key])
        write_symbol_diagnostics_jsonl_gz(self.project_root / diagnostics_path_rel, diagnostics_records_list)

        report = RunReport(
            run_id=run_id,
            scan_mode=scan_mode,
            as_of_utc=as_of_utc,
            daily_bar_id=daily_bar_id,
            intraday_bar_id=intraday_bar_id,
            counts_by_bucket=counts,
            symbol_lists=symbol_lists_normalized,
            manifest_path=manifest_path,
            diagnostics_path=diagnostics_path_rel.as_posix(),
        ).to_dict()
        is_intraday_noop = scan_mode == "intraday" and diagnostics_record_count == 0
        report["no_op"] = is_intraday_noop
        report["no_op_reason"] = None
        if extra_report_fields is not None:
            for key, value in extra_report_fields.items():
                report[str(key)] = value
        _atomic_write_json(self.project_root / report_path_rel, report)

        self._update_index_after_run(
            report=report,
            report_path=report_path_rel.as_posix(),
            produced_symbol_list_keys=produced_symbol_list_keys,
        )
        return report

    def write_daily_report(self, report: Mapping[str, Any]) -> Dict[str, Any]:
        daily_bar_id = str(report["daily_bar_id"])
        year, month, day = _date_parts_from_daily_bar_id(daily_bar_id)
        daily_report_path = self.reports_root / "daily" / year / month / day / "report.json"
        _atomic_write_json(daily_report_path, report)
        self.index_root.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(self.index_root / "latest_daily.json", report)
        return dict(report)

    def _update_index_after_run(
        self,
        *,
        report: Mapping[str, Any],
        report_path: str,
        produced_symbol_list_keys: set[str],
    ) -> None:
        self.index_root.mkdir(parents=True, exist_ok=True)

        run_id = report["run_id"]
        latest_paths = {
            "run_id": run_id,
            "scan_mode": report["scan_mode"],
            "as_of_utc": report["as_of_utc"],
            "daily_bar_id": report["daily_bar_id"],
            "intraday_bar_id": report["intraday_bar_id"],
            "report_path": report_path,
            "diagnostics_path": report["diagnostics_path"],
            "manifest_path": report["manifest_path"],
        }

        _atomic_write_text(self.index_root / "latest_run.txt", f"{run_id}\n")
        _atomic_write_json(self.index_root / "latest_paths.json", latest_paths)
        _atomic_write_json(self.index_root / "latest.json", report)
        if report["scan_mode"] == "intraday":
            _atomic_write_json(self.index_root / "latest_intraday.json", report)

        # Candidate-oriented latest files track reports that intentionally
        # produced each candidate list. Daily runs are authoritative even when
        # a list is empty. Intraday reports must provide the relevant input key;
        # diagnostics records alone never imply candidate-list availability.
        should_update_confirmed_candidates = (
            report["scan_mode"] == "daily"
            or "confirmed_candidates" in produced_symbol_list_keys
        )
        should_update_watchlist = (
            report["scan_mode"] == "daily" or "watchlist" in produced_symbol_list_keys
        )
        if should_update_confirmed_candidates:
            _atomic_write_json(
                self.index_root / "latest_confirmed_candidates.json",
                list(report["symbol_lists"]["confirmed_candidates"]),
            )
        if should_update_watchlist:
            _atomic_write_json(
                self.index_root / "latest_watchlist.json",
                list(report["symbol_lists"]["watchlist"]),
            )

        recent_runs_path = self.index_root / "recent_runs.json"
        existing: list[Dict[str, Any]] = []
        if recent_runs_path.exists():
            existing_payload = json.loads(recent_runs_path.read_text(encoding="utf-8"))
            if isinstance(existing_payload, list):
                existing = [x for x in existing_payload if isinstance(x, dict)]

        new_entry = {
            "run_id": report["run_id"],
            "scan_mode": report["scan_mode"],
            "as_of_utc": report["as_of_utc"],
            "daily_bar_id": report["daily_bar_id"],
            "intraday_bar_id": report["intraday_bar_id"],
            "manifest_path": report["manifest_path"],
            "report_path": report_path,
            "diagnostics_path": report["diagnostics_path"],
        }
        merged = [new_entry] + [x for x in existing if x.get("run_id") != new_entry["run_id"]]
        newest = _sort_newest_first(merged)
        _atomic_write_json(recent_runs_path, newest[: self.config["recent_runs_limit"]])


def make_report_builder(project_root: Path, config: Mapping[str, Any] | None = None) -> ReportBuilder:
    return ReportBuilder(project_root=project_root, config=config)
