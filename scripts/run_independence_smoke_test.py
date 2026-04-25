from __future__ import annotations

import argparse
from contextlib import suppress
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import gzip
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scanner.clients.mexc_client import MEXCClient
import scanner.config as scanner_config_module
from scanner.config import load_config
from scanner.data.bar_clock import daily_bar_id as compute_daily_bar_id
from scanner.data.bar_clock import get_last_closed_intraday_bar_id
from scanner.data.ohlcv_fetch import fetch_closed_bars
from scanner.evaluation.dataset_export import run_evaluation_export
from scanner.runners.daily import run_daily_scan
from scanner.runners.intraday import run_intraday_scan

SMOKE_SYMBOLS = ["SOLUSDT", "AVAXUSDT", "LINKUSDT", "INJUSDT", "ARBUSDT"]
_DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INTRADAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T(00|04|08|12|16|20):00:00Z$")


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual Independence-Release smoke test workflow stages")
    parser.add_argument("--workdir", required=True, help="Smoke output workdir")
    parser.add_argument("--daily-bar-id", required=False)
    parser.add_argument("--intraday-bar-id", required=False)
    return parser.parse_args()


def _resolve_config_path() -> str:
    original_cwd = Path.cwd()
    configured = os.environ.get("SCANNER_CONFIG_PATH")
    if configured:
        candidate = Path(configured)
        if not candidate.is_absolute():
            candidate = (original_cwd / candidate).resolve()
        return candidate.as_posix()

    workspace = os.environ.get("GITHUB_WORKSPACE")
    if workspace:
        return (Path(workspace).resolve() / "config" / "config.yml").as_posix()

    repo_candidate = (REPO_ROOT / "config" / "config.yml").resolve()
    if repo_candidate.exists():
        return repo_candidate.as_posix()

    return (original_cwd / "config" / "config.yml").resolve().as_posix()


def _load_diag_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _find_first(pattern: str, root: Path) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[0] if matches else None


def _add_check(checks: list[CheckResult], name: str, ok: bool, detail: str) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail))
    status = "PASS" if ok else "FAIL"
    print(f"{status}: {name} — {detail}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ms_to_iso(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def main() -> int:
    args = _parse_args()
    now = datetime.now(timezone.utc)
    daily = args.daily_bar_id or compute_daily_bar_id(now)
    intraday = args.intraday_bar_id or get_last_closed_intraday_bar_id(now, timeframe="4h")

    if _DAILY_RE.fullmatch(daily) is None:
        raise SystemExit(f"FAIL: invalid --daily-bar-id {daily!r}")
    if _INTRADAY_RE.fullmatch(intraday) is None:
        raise SystemExit(f"FAIL: invalid --intraday-bar-id {intraday!r}")

    config_path = _resolve_config_path()
    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "artifacts").mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "daily_bar_id": daily,
        "intraday_bar_id": intraday,
        "run_id": None,
        "steps": {
            "daily_runner": "FAIL",
            "intraday_runner": "FAIL",
            "evaluation_replay": "SKIP",
        },
        "per_symbol_diagnostics": {},
        "artifacts_written": [],
        "unexpected_path_writes": [],
        "warnings": [],
        "errors": [],
        "follow_up_required": True,
    }

    checks: list[CheckResult] = []
    prev_cwd = Path.cwd()

    os.environ["SCANNER_CONFIG_PATH"] = config_path
    scanner_config_module.CONFIG_PATH = config_path
    cfg = load_config(config_path)

    # Public MEXC endpoints are used without credentials for exchangeInfo/klines in this smoke path.
    client = MEXCClient(timeout=20, max_retries=1)

    def universe_provider(_cfg: Any, _daily_id: str) -> list[str]:
        return list(SMOKE_SYMBOLS)

    per_symbol: dict[str, dict[str, Any]] = {
        symbol: {
            "1d_bar_count": None,
            "4h_bar_count": None,
            "1d_first_close_time": None,
            "1d_last_close_time": None,
            "4h_first_close_time": None,
            "4h_last_close_time": None,
            "skip_reason": None,
            "error": None,
        }
        for symbol in SMOKE_SYMBOLS
    }

    def ohlcv_provider(symbol: str, timeframe: str) -> list[Any]:
        try:
            fetch = fetch_closed_bars(symbol=symbol, timeframe=timeframe, now=now, lookback_bars=250)
            bars = list(fetch.bars)
            diag = per_symbol.setdefault(symbol, {})
            diag[f"{timeframe}_bar_count"] = len(bars)
            if bars:
                diag[f"{timeframe}_first_close_time"] = _ms_to_iso(getattr(bars[0], "close_time_utc_ms", None))
                diag[f"{timeframe}_last_close_time"] = _ms_to_iso(getattr(bars[-1], "close_time_utc_ms", None))
            if not bars:
                diag["skip_reason"] = f"empty {timeframe} OHLCV response"
            elif getattr(fetch, "last_fetch_status", "ok") != "ok":
                diag["skip_reason"] = f"{timeframe} OHLCV status={getattr(fetch, 'last_fetch_status', 'unknown')}"
            return bars
        except Exception as exc:
            diag = per_symbol.setdefault(symbol, {})
            diag["skip_reason"] = f"provider failure ({timeframe})"
            diag["error"] = f"{type(exc).__name__}: {exc}"
            raise

    def intraday_context_provider(_cfg: Any, _daily_id: str) -> list[dict[str, Any]]:
        return [
            {
                "symbol": symbol,
                "state_machine_state": "watch",
                "decision_bucket": "watchlist",
                "market_phase_confidence": 60.0,
                "daily_cache_bar_id": daily,
                "intraday_cache_bar_id": intraday,
                "last_intraday_status": "OK",
                "priority_score": 0.0,
            }
            for symbol in SMOKE_SYMBOLS
        ]

    setattr(cfg, "daily_universe_provider", universe_provider)
    setattr(cfg, "daily_ohlcv_provider", ohlcv_provider)
    setattr(cfg, "intraday_context_provider", intraday_context_provider)

    os.chdir(workdir)

    with suppress(Exception):
        client.get_exchange_info(use_cache=False)

    daily_artifacts_found = False
    intraday_artifacts_found = False
    try:
        # Daily runner stage
        try:
            run_daily_scan(cfg, as_of_date=daily)
            summary["steps"]["daily_runner"] = "PASS"
        except Exception as exc:
            summary["steps"]["daily_runner"] = "FAIL"
            summary["errors"].append(f"daily_runner: {type(exc).__name__}: {exc}")

        manifest = _find_first("snapshots/runs/*/*/*/*/run.manifest.json", workdir)
        _add_check(checks, "daily manifest under snapshots/runs", manifest is not None, str(manifest) if manifest else "missing")

        daily_report = _find_first("reports/runs/*/*/*/daily-*/report.json", workdir)
        _add_check(checks, "daily report exists", daily_report is not None, str(daily_report) if daily_report else "missing")
        daily_artifacts_found = manifest is not None or daily_report is not None

        if daily_report is not None:
            report_payload = _load_json(daily_report)
            summary["run_id"] = report_payload.get("run_id")
            _add_check(
                checks,
                "daily report scan_mode is canonical",
                report_payload.get("scan_mode") == "daily",
                f"scan_mode={report_payload.get('scan_mode')}",
            )
            _add_check(
                checks,
                "daily_bar_id matches requested",
                report_payload.get("daily_bar_id") == daily,
                f"expected={daily}, actual={report_payload.get('daily_bar_id')}",
            )
            diag_rel = report_payload.get("diagnostics_path")
            diag_path = workdir / str(diag_rel) if isinstance(diag_rel, str) else None
            has_diag = bool(diag_path and diag_path.exists())
            _add_check(checks, "daily diagnostics exists", has_diag, str(diag_path) if diag_path else "missing")
            if has_diag and diag_path is not None:
                diag_rows = _load_diag_rows(diag_path)
                _add_check(checks, "daily diagnostics has >=1 symbol", len(diag_rows) >= 1, f"rows={len(diag_rows)}")
                seen_symbols = {str(row.get("symbol", "")) for row in diag_rows if row.get("symbol")}
                for symbol in seen_symbols:
                    per_symbol.setdefault(symbol, {}).setdefault("skip_reason", None)
                skipped_symbols = [symbol for symbol in SMOKE_SYMBOLS if symbol not in seen_symbols]
                for symbol in skipped_symbols:
                    diag = per_symbol.setdefault(symbol, {})
                    if diag.get("skip_reason") is None:
                        diag["skip_reason"] = "exception in daily runner symbol processing"
                if len(seen_symbols) == 0:
                    summary["errors"].append("daily_runner: zero symbols processed; see per_symbol_diagnostics")
                    summary["steps"]["daily_runner"] = "FAIL"

        reports_manifest = list((workdir / "reports" / "runs").glob("**/*.manifest.json")) if (workdir / "reports" / "runs").exists() else []
        _add_check(checks, "no manifest under reports/runs", len(reports_manifest) == 0, f"count={len(reports_manifest)}")

        analysis_dir = workdir / "reports" / "analysis"
        analysis_nonempty = analysis_dir.exists() and any(analysis_dir.iterdir())
        _add_check(checks, "no artifacts under reports/analysis", not analysis_nonempty, str(analysis_dir))

        # Intraday runner stage
        intraday_dt = datetime.fromisoformat(intraday.replace("Z", "+00:00")) + timedelta(minutes=1)
        try:
            run_intraday_scan(cfg, now_utc=intraday_dt)
            summary["steps"]["intraday_runner"] = "PASS"
        except Exception as exc:
            summary["steps"]["intraday_runner"] = "FAIL"
            summary["errors"].append(f"intraday_runner: {type(exc).__name__}: {exc}")

        intraday_report = _find_first("reports/runs/*/*/*/intraday-*/report.json", workdir)
        _add_check(checks, "intraday report exists", intraday_report is not None, str(intraday_report) if intraday_report else "missing")
        intraday_artifacts_found = intraday_report is not None

        if intraday_report is not None:
            intraday_payload = _load_json(intraday_report)
            intraday_actual = intraday_payload.get("intraday_bar_id")
            _add_check(
                checks,
                "intraday_bar_id canonical string",
                isinstance(intraday_actual, str) and _INTRADAY_RE.fullmatch(intraday_actual) is not None,
                str(intraday_actual),
            )
            _add_check(
                checks,
                "intraday_bar_id matches requested",
                intraday_actual == intraday,
                f"expected={intraday}, actual={intraday_actual}",
            )

        intraday_diags = sorted(workdir.glob("reports/runs/*/*/*/intraday-*/symbol_diagnostics.jsonl.gz"))
        numeric_intraday_found = False
        for path in intraday_diags:
            for row in _load_diag_rows(path):
                value = row.get("intraday_bar_id")
                if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                    numeric_intraday_found = True
        _add_check(checks, "no numeric intraday_bar_id in intraday diagnostics", not numeric_intraday_found, f"checked={len(intraday_diags)}")

        # Evaluation replay stage
        if not daily_artifacts_found and not intraday_artifacts_found:
            summary["steps"]["evaluation_replay"] = "SKIP"
        else:
            try:
                run_evaluation_export(project_root=workdir, config=cfg.raw)
                summary["steps"]["evaluation_replay"] = "PASS"
            except Exception as exc:
                summary["steps"]["evaluation_replay"] = "FAIL"
                summary["errors"].append(f"evaluation_replay: {type(exc).__name__}: {exc}")

            summary_json = workdir / "evaluation" / "exports" / "evaluation_summary.json"
            _add_check(checks, "evaluation summary exists", summary_json.exists(), str(summary_json))
            eval_summary = _load_json(summary_json) if summary_json.exists() else {}
            event_count = int(eval_summary.get("cycle_count", 0))
            if event_count == 0 and summary["steps"]["evaluation_replay"] == "PASS":
                summary["warnings"].append("evaluation_replay: no events exported")

        terminal_parquet = workdir / "evaluation" / "exports" / "terminal_event_timeline.parquet"
        if terminal_parquet.exists():
            import pandas as pd

            terminal_df = pd.read_parquet(terminal_parquet)
            forbidden_cols = [col for col in terminal_df.columns if "forward_return" in col or col.startswith("mfe_") or col.startswith("mae_")]
            _add_check(checks, "terminal events not enriched with forward returns/MFE/MAE", len(forbidden_cols) == 0, f"forbidden_cols={forbidden_cols}")

    except Exception as exc:
        summary["errors"].append(f"orchestrator: {type(exc).__name__}: {exc}")
    finally:
        os.chdir(prev_cwd)

    summary["per_symbol_diagnostics"] = per_symbol

    for unwanted in ("node-compile-cache", "phantomjs"):
        target = workdir / unwanted
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
    for uv_lock in workdir.glob("uv*.lock"):
        uv_lock.unlink(missing_ok=True)

    for path in sorted(workdir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(workdir).as_posix()
            summary["artifacts_written"].append(rel)
            if not (
                rel == "artifacts/smoke-test-report.json"
                or rel.startswith("snapshots/runs/")
                or rel.startswith("reports/runs/")
            ):
                summary["unexpected_path_writes"].append(rel)

    failures = [c for c in checks if not c.ok]
    for failed in failures:
        summary["errors"].append(f"{failed.name}: {failed.detail}")

    out_path = workdir / "artifacts" / "smoke-test-report.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"INFO: wrote smoke summary to {out_path}")

    return 1 if failures or summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
