from __future__ import annotations

import argparse
from contextlib import suppress
from datetime import datetime, timedelta, timezone
import gzip
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scanner.config as scanner_config_module
from scanner.clients.mexc_client import MEXCClient
from scanner.config import load_config
from scanner.config import resolve_independence_ohlcv_fetch_config, resolve_independence_universe_config
from scanner.data.bar_clock import daily_bar_id as compute_daily_bar_id
from scanner.data.ohlcv_fetch import fetch_closed_bars
from scanner.data.bar_clock import get_last_closed_intraday_bar_id
from scanner.evaluation.dataset_export import run_evaluation_export
import scanner.runners.daily as daily_runner_module
from scanner.runners.daily import run_daily_scan
from scanner.runners.intraday import run_intraday_scan

_DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INTRADAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T(00|04|08|12|16|20):00:00Z$")
_ALLOWED_OUTPUT_ROOTS = (
    "artifacts/",
    "data/",
    "evaluation/exports/",
    "evaluation/replay/",
    "logs/",
    "reports/runs/",
    "reports/daily/",
    "reports/index/",
    "snapshots/runs/",
    "snapshots/history/ohlcv/",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Independence shadow-live daily workflow")
    parser.add_argument("--workdir", required=True, help="Shadow-live output workdir")
    parser.add_argument("--daily-bar-id", required=False)
    parser.add_argument("--intraday-bar-id", required=False)
    parser.add_argument("--skip-intraday", action="store_true", help="Skip non-blocking intraday diagnostics")
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _require_report_relpath(report: Mapping[str, Any], key: str) -> Path:
    value = report.get(key)
    if not isinstance(value, str):
        raise ValueError(f"invalid report field {key}: expected non-empty relative path string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"invalid report field {key}: expected non-empty relative path string")
    candidate = Path(normalized)
    if candidate.is_absolute():
        raise ValueError(f"invalid report field {key}: absolute paths are forbidden")
    if any(part == ".." for part in candidate.parts):
        raise ValueError(f"invalid report field {key}: path traversal is forbidden")
    return candidate


def _build_real_daily_providers(*, cfg: Any, now_utc: datetime) -> tuple[list[str], Any, Any]:
    universe_cfg = resolve_independence_universe_config(cfg.raw)
    ohlcv_cfg = resolve_independence_ohlcv_fetch_config(cfg.raw)
    mexc_client = MEXCClient(
        timeout=int(ohlcv_cfg["per_call_timeout_s"]),
        max_retries=int(ohlcv_cfg["max_retries"]),
    )
    exchange_info = mexc_client.get_exchange_info(use_cache=False)
    quote_assets = set(universe_cfg["quote_asset_allowed"])
    tradeable_statuses = set(universe_cfg["mexc_tradeable_status_values"])

    universe: list[str] = []
    for symbol_info in exchange_info.get("symbols", []):
        if not isinstance(symbol_info, dict):
            continue
        symbol = symbol_info.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            continue
        if symbol_info.get("quoteAsset") not in quote_assets:
            continue
        if symbol_info.get("status") not in tradeable_statuses:
            continue
        if not bool(symbol_info.get("isSpotTradingAllowed", False)):
            continue
        universe.append(symbol)
    universe = sorted(set(universe))

    def universe_provider(_cfg: Any, _daily_id: str) -> list[str]:
        return list(universe)

    def ohlcv_provider(symbol: str, timeframe: str) -> list[Any]:
        if timeframe not in {"1d", "4h"}:
            raise ValueError(f"unsupported timeframe: {timeframe}")
        lookback_key = "lookback_bars_1d" if timeframe == "1d" else "lookback_bars_4h"
        fetch = fetch_closed_bars(
            symbol=symbol,
            timeframe=timeframe,
            now=now_utc,
            lookback_bars=int(ohlcv_cfg[lookback_key]),
        )
        if str(getattr(fetch, "last_fetch_status", "unknown")) != "ok":
            raise RuntimeError(
                f"OHLCV fetch failed for {symbol} {timeframe}: status={getattr(fetch, 'last_fetch_status', 'unknown')}, "
                f"code={getattr(fetch, 'last_error_code', None)}"
            )
        return list(fetch.bars)

    return universe, universe_provider, ohlcv_provider


def _collect_forbidden_writes(workdir: Path) -> list[str]:
    forbidden: list[str] = []
    for path in sorted(workdir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(workdir).as_posix()
        if rel == "shadow-live-report.json":
            continue
        if any(rel.startswith(root) for root in _ALLOWED_OUTPUT_ROOTS):
            continue
        forbidden.append(rel)

    reports_runs = workdir / "reports" / "runs"
    if reports_runs.exists():
        for manifest in sorted(reports_runs.glob("**/*.manifest.json")):
            forbidden.append(manifest.relative_to(workdir).as_posix())

    analysis_dir = workdir / "reports" / "analysis"
    if analysis_dir.exists():
        for path in sorted(analysis_dir.rglob("*")):
            if path.is_file():
                forbidden.append(path.relative_to(workdir).as_posix())

    return sorted(set(forbidden))


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

    summary: dict[str, Any] = {
        "workflow_mode": "shadow_live",
        "status": "fail",
        "run_started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_finished_at_utc": None,
        "daily": {
            "status": "fail",
            "run_id": None,
            "report_path": None,
            "diagnostics_path": None,
            "manifest_path": None,
            "counts_by_bucket": {},
            "symbol_lists": {},
        },
        "intraday": {
            "status": "skipped" if args.skip_intraday else "non_blocking_warning",
            "known_state": "none",
            "reason": "not_enabled_in_initial_shadow_live" if args.skip_intraday else None,
            "diagnostics_path": None,
        },
        "evaluation_replay": {
            "status": "fail",
            "event_count": 0,
            "summary_path": None,
            "timeline_path": None,
        },
        "artifact_paths": [],
        "forbidden_path_writes": [],
        "errors": [],
        "warnings": [],
    }

    os.environ["SCANNER_CONFIG_PATH"] = config_path
    scanner_config_module.CONFIG_PATH = config_path
    cfg = load_config(config_path)
    if cfg.run_mode == "standard" and not cfg.cmc_api_key:
        summary["errors"].append("preflight: MISSING_REQUIRED_CREDENTIAL_CMC_API_KEY")

    preflight_universe: list[str] = []
    with suppress(Exception):
        MEXCClient(timeout=20, max_retries=1).get_exchange_info(use_cache=False)
    try:
        preflight_universe, universe_provider, ohlcv_provider = _build_real_daily_providers(cfg=cfg, now_utc=now)
        setattr(cfg, "daily_universe_provider", universe_provider)
        setattr(cfg, "daily_ohlcv_provider", ohlcv_provider)
        if getattr(cfg, "daily_universe_provider", None) is daily_runner_module._default_universe:
            summary["errors"].append("preflight: daily_universe_provider resolved to default provider")
        if getattr(cfg, "daily_ohlcv_provider", None) is daily_runner_module._default_ohlcv:
            summary["errors"].append("preflight: daily_ohlcv_provider resolved to default provider")
    except Exception as exc:
        summary["errors"].append(f"preflight: provider wiring failed: {type(exc).__name__}: {exc}")

    if not preflight_universe:
        summary["errors"].append("preflight: EMPTY_REAL_DAILY_UNIVERSE")

    prev_cwd = Path.cwd()
    os.chdir(workdir)

    try:
        if summary["errors"]:
            raise RuntimeError("shadow-live preflight failed")

        run_daily_scan(cfg, as_of_date=daily)

        daily_report = _find_first("reports/runs/*/*/*/daily-*/report.json", workdir)
        if daily_report is None:
            summary["errors"].append("daily: missing report.json")
        else:
            payload = _load_json(daily_report)
            try:
                diagnostics_rel = _require_report_relpath(payload, "diagnostics_path")
                manifest_rel = _require_report_relpath(payload, "manifest_path")
            except ValueError as exc:
                summary["daily"]["status"] = "fail"
                summary["errors"].append(f"daily: {exc}")
                diagnostics_rel = None
                manifest_rel = None
            summary["daily"].update(
                {
                    "status": "pass",
                    "run_id": payload.get("run_id"),
                    "report_path": daily_report.relative_to(workdir).as_posix(),
                    "diagnostics_path": diagnostics_rel.as_posix() if diagnostics_rel is not None else None,
                    "manifest_path": manifest_rel.as_posix() if manifest_rel is not None else None,
                    "counts_by_bucket": payload.get("counts_by_bucket", {}),
                    "symbol_lists": payload.get("symbol_lists", {}),
                }
            )
            diagnostics_path = workdir / diagnostics_rel if diagnostics_rel is not None else None
            manifest_path = workdir / manifest_rel if manifest_rel is not None else None
            if diagnostics_path is None or not diagnostics_path.is_file():
                summary["daily"]["status"] = "fail"
                summary["errors"].append("daily: missing symbol_diagnostics.jsonl.gz")
            if manifest_path is None or not manifest_path.is_file():
                summary["daily"]["status"] = "fail"
                summary["errors"].append("daily: missing run.manifest.json")

        if summary["daily"]["status"] == "pass":
            try:
                run_evaluation_export(project_root=workdir, config=cfg.raw)
                summary["evaluation_replay"]["status"] = "pass"
            except Exception as exc:
                summary["evaluation_replay"]["status"] = "fail"
                summary["errors"].append(f"evaluation_replay: {type(exc).__name__}: {exc}")

            eval_summary_path = workdir / "evaluation" / "exports" / "evaluation_summary.json"
            timeline_path = workdir / "evaluation" / "replay" / "event_timeline.jsonl"
            if eval_summary_path.exists():
                eval_summary = _load_json(eval_summary_path)
                summary["evaluation_replay"]["event_count"] = int(eval_summary.get("cycle_count", 0))
                summary["evaluation_replay"]["summary_path"] = eval_summary_path.relative_to(workdir).as_posix()
                summary["evaluation_replay"]["timeline_path"] = timeline_path.relative_to(workdir).as_posix() if timeline_path.exists() else None
                if summary["evaluation_replay"]["event_count"] == 0:
                    summary["warnings"].append("evaluation_replay: no events exported")
            else:
                summary["errors"].append("evaluation_replay: missing evaluation_summary.json")
        else:
            summary["evaluation_replay"]["status"] = "fail"
            summary["errors"].append("evaluation_replay: skipped because daily stage failed")

        if not args.skip_intraday:
            intraday_dt = datetime.fromisoformat(intraday.replace("Z", "+00:00")) + timedelta(minutes=1)
            try:
                run_intraday_scan(cfg, now_utc=intraday_dt)
                summary["intraday"]["status"] = "pass"
            except Exception as exc:
                summary["intraday"]["status"] = "non_blocking_warning"
                summary["warnings"].append(f"intraday_runner: {type(exc).__name__}: {exc}")

            intraday_report = _find_first("reports/runs/*/*/*/intraday-*/report.json", workdir)
            if intraday_report is not None:
                intraday_payload = _load_json(intraday_report)
                diag_rel = intraday_payload.get("diagnostics_path")
                if isinstance(diag_rel, str):
                    diag_path = workdir / diag_rel
                    summary["intraday"]["diagnostics_path"] = diag_rel
                    if diag_path.exists():
                        rows = _load_diag_rows(diag_path)
                        known_rows = [
                            row
                            for row in rows
                            if row.get("reasons", {}).get("intraday_skip_reason") == "missing_intraday_cycle_context"
                            and row.get("execution_attempted") is False
                        ]
                        if known_rows:
                            summary["intraday"]["status"] = "non_blocking_warning"
                            summary["intraday"]["known_state"] = "missing_intraday_cycle_context"
                            summary["warnings"].append(
                                "intraday: known non-blocking state missing_intraday_cycle_context observed"
                            )

    except Exception as exc:
        summary["errors"].append(f"shadow_live_orchestrator: {type(exc).__name__}: {exc}")
    finally:
        os.chdir(prev_cwd)

    summary["forbidden_path_writes"] = _collect_forbidden_writes(workdir)
    for forbidden in summary["forbidden_path_writes"]:
        summary["errors"].append(f"forbidden path write: {forbidden}")

    for path in sorted(workdir.rglob("*")):
        if path.is_file():
            summary["artifact_paths"].append(path.relative_to(workdir).as_posix())

    if summary["daily"]["status"] != "pass":
        summary["errors"].append("daily: blocking failure")
    if summary["evaluation_replay"]["status"] != "pass":
        summary["errors"].append("evaluation_replay: blocking failure")

    summary["status"] = "pass" if not summary["errors"] else "fail"
    summary["run_finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out_path = workdir / "shadow-live-report.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"INFO: wrote shadow-live summary to {out_path}")

    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
