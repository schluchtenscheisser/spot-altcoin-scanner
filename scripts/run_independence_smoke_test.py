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
from scanner.axes import compute_tier1_axes, compute_tier2_axes
from scanner.config import load_config
from scanner.data.bar_clock import daily_bar_id as compute_daily_bar_id
from scanner.data.bar_clock import get_last_closed_intraday_bar_id
from scanner.data.ohlcv_fetch import fetch_closed_bars
from scanner.decision.buckets import assign_bucket
from scanner.entry.patterns import resolve_entry_pattern
from scanner.evaluation.dataset_export import run_evaluation_export
from scanner.features.bundle import build_feature_bundle
from scanner.phase import compute_phase_interpretation
from scanner.runners.daily import _derive_runtime_context, _to_cycle_context
from scanner.runners.daily import run_daily_scan
from scanner.runners.intraday import run_intraday_scan
from scanner.state import compute_invalidation_and_cycle, compute_state_machine
from scanner.storage import init_db, load_persisted_state_machine_context

SMOKE_SYMBOLS = ["SOLUSDT", "AVAXUSDT", "LINKUSDT", "INJUSDT", "ARBUSDT"]
_DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INTRADAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T(00|04|08|12|16|20):00:00Z$")
_FORBIDDEN_WORKSPACE_ROOTS = ("reports", "snapshots", "evaluation", "artifacts", "data")


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


def _file_state(root: Path) -> dict[str, tuple[int, int]]:
    state: dict[str, tuple[int, int]] = {}
    if not root.exists():
        return state
    for path in root.rglob("*"):
        if path.is_file():
            stat = path.stat()
            state[path.as_posix()] = (int(stat.st_mtime_ns), int(stat.st_size))
    return state


def _ms_to_iso(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _traceback_tail(exc: Exception, *, max_lines: int = 5) -> list[str]:
    import traceback

    lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    compact = [line.rstrip("\n") for block in lines for line in block.splitlines() if line.strip()]
    return compact[-max_lines:]


def _run_daily_symbol_replay(
    *,
    cfg: Any,
    daily_bar_id: str,
    symbol: str,
    bars_1d: list[Any],
    bars_4h: list[Any],
    db_path: Path,
) -> dict[str, Any] | None:
    bar_clock_context = {"daily_bar_id": daily_bar_id, "intraday_bar_id": None, "daily_close_time_utc_ms": 0}
    try:
        features = build_feature_bundle(symbol, bar_clock_context, bars_1d, bars_4h if bars_4h else None, cfg)
    except Exception as exc:
        return {"failed_stage": "build_feature_bundle", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        t1 = compute_tier1_axes(features, cfg)
    except Exception as exc:
        return {"failed_stage": "compute_tier1_axes", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        t2 = compute_tier2_axes(features, cfg)
    except Exception as exc:
        return {"failed_stage": "compute_tier2_axes", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        phase = compute_phase_interpretation(t1, t2, cfg)
    except Exception as exc:
        return {"failed_stage": "compute_phase_interpretation", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        conn = init_db(db_path.as_posix())
        try:
            persisted = load_persisted_state_machine_context(conn, symbol)
        finally:
            conn.close()
    except Exception as exc:
        return {"failed_stage": "load_persisted_state_machine_context", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        inv_ctx = _to_cycle_context(persisted)
        invalidation = compute_invalidation_and_cycle(phase, t1, t2, inv_ctx, cfg)
    except Exception as exc:
        return {"failed_stage": "compute_invalidation_and_cycle", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        runtime = _derive_runtime_context(bars_1d=bars_1d, bars_4h=bars_4h if bars_4h else None)
        state_bundle = compute_state_machine(phase, t1, t2, invalidation, persisted, runtime, cfg)
    except Exception as exc:
        return {"failed_stage": "compute_state_machine", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        entry = resolve_entry_pattern(phase, t1, t2, cfg)
    except Exception as exc:
        return {"failed_stage": "resolve_entry_pattern", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
    try:
        _ = assign_bucket(phase, state_bundle, entry, cfg, execution_contract=None)
    except Exception as exc:
        return {"failed_stage": "assign_bucket", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback_tail": _traceback_tail(exc)}
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
    workspace = os.environ.get("GITHUB_WORKSPACE")
    workspace_path = Path(workspace).resolve() if workspace else None
    workspace_state_before = _file_state(workspace_path) if workspace_path is not None and workspace_path.exists() else {}

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
        "uploaded_artifact_candidates": [],
        "allowed_workspace_log_writes": [],
        "forbidden_path_writes": [],
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
            "1d_fetch_status": None,
            "4h_fetch_status": None,
            "1d_error_code": None,
            "4h_error_code": None,
            "1d_first_close_time": None,
            "1d_last_close_time": None,
            "4h_first_close_time": None,
            "4h_last_close_time": None,
            "skip_reason": None,
            "error": None,
        }
        for symbol in SMOKE_SYMBOLS
    }
    ohlcv_cache: dict[str, dict[str, list[Any]]] = {symbol: {} for symbol in SMOKE_SYMBOLS}

    def ohlcv_provider(symbol: str, timeframe: str) -> list[Any]:
        try:
            fetch = fetch_closed_bars(symbol=symbol, timeframe=timeframe, now=now, lookback_bars=250)
            bars = list(fetch.bars)
            diag = per_symbol.setdefault(symbol, {})
            diag[f"{timeframe}_bar_count"] = len(bars)
            fetch_status = str(getattr(fetch, "last_fetch_status", "unknown"))
            fetch_error_code = getattr(fetch, "last_error_code", None)
            diag[f"{timeframe}_fetch_status"] = fetch_status
            diag[f"{timeframe}_error_code"] = fetch_error_code
            if bars:
                diag[f"{timeframe}_first_close_time"] = _ms_to_iso(getattr(bars[0], "close_time_utc_ms", None))
                diag[f"{timeframe}_last_close_time"] = _ms_to_iso(getattr(bars[-1], "close_time_utc_ms", None))
            if not bars:
                diag["skip_reason"] = f"empty {timeframe} OHLCV response"
            if fetch_status != "ok":
                diag["skip_reason"] = f"{timeframe} OHLCV fetch status={fetch_status}"
            ohlcv_cache.setdefault(symbol, {})[timeframe] = bars
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
                    db_path = workdir / "data" / "independence_release.sqlite"
                    for symbol in SMOKE_SYMBOLS:
                        diag = per_symbol.setdefault(symbol, {})
                        bars_1d = ohlcv_cache.get(symbol, {}).get("1d", [])
                        bars_4h = ohlcv_cache.get(symbol, {}).get("4h", [])
                        if not bars_1d:
                            continue
                        replay = _run_daily_symbol_replay(
                            cfg=cfg,
                            daily_bar_id=daily,
                            symbol=symbol,
                            bars_1d=bars_1d,
                            bars_4h=bars_4h,
                            db_path=db_path,
                        )
                        if replay is not None:
                            diag.update(replay)
                            if diag.get("error") is None:
                                diag["error"] = f"{replay['exception_type']}: {replay['exception_message']}"

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
            intraday_manifest_rel = intraday_payload.get("manifest_path")
            intraday_manifest = workdir / str(intraday_manifest_rel) if isinstance(intraday_manifest_rel, str) else None
            _add_check(
                checks,
                "intraday manifest exists when referenced",
                bool(intraday_manifest and intraday_manifest.exists()),
                str(intraday_manifest_rel),
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
            if (
                rel == "artifacts/smoke-test-report.json"
                or rel.startswith("snapshots/runs/")
                or rel.startswith("reports/runs/")
                or rel.startswith("logs/")
            ):
                summary["uploaded_artifact_candidates"].append(rel)

    if workspace_path is not None and workspace_path != workdir and workspace_path.exists():
        workspace_state_after = _file_state(workspace_path)
        for path, after in workspace_state_after.items():
            before = workspace_state_before.get(path)
            if before is None or before != after:
                rel = Path(path).relative_to(workspace_path).as_posix()
                if rel.startswith("logs/"):
                    summary["allowed_workspace_log_writes"].append(rel)
                    continue
                if any(rel == root or rel.startswith(f"{root}/") for root in _FORBIDDEN_WORKSPACE_ROOTS):
                    summary["forbidden_path_writes"].append(rel)

    if (workdir / "reports" / "analysis").exists():
        for path in sorted((workdir / "reports" / "analysis").rglob("*")):
            if path.is_file():
                summary["forbidden_path_writes"].append(path.relative_to(workdir).as_posix())

    failures = [c for c in checks if not c.ok]
    for failed in failures:
        summary["errors"].append(f"{failed.name}: {failed.detail}")
    for forbidden_path in summary["forbidden_path_writes"]:
        summary["errors"].append(f"forbidden path write: {forbidden_path}")

    out_path = workdir / "artifacts" / "smoke-test-report.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"INFO: wrote smoke summary to {out_path}")

    return 1 if failures or summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
