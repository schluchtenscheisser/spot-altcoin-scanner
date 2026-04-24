from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
import uuid
from typing import Any, Mapping

from scanner.config import ScannerConfig
from scanner.data.bar_clock import daily_bar_id as compute_daily_bar_id
from scanner.data.bar_clock import get_last_closed_intraday_bar_id, has_new_intraday_bar
from scanner.execution import evaluate_execution_subset, select_execution_subset
from scanner.output import make_report_builder
from scanner.storage import init_db

logger = logging.getLogger(__name__)

_MONITOR_STATES = {"watch", "early_ready", "confirmed_ready", "late"}
_MONITOR_BUCKETS = {"watchlist", "early_candidates", "confirmed_candidates", "late_monitor"}
_HARD_MONITOR_EXCLUDED = {"rejected", "chased"}
_HARD_EXECUTION_EXCLUDED = {"rejected", "chased"}


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _create_run_metadata(
    conn: sqlite3.Connection, *, run_id: str, daily_id: str, intraday_id: str, scan_mode: str
) -> None:
    conn.execute(
        """
        INSERT INTO run_metadata(
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, scan_mode, _utc_now_iso(), None, daily_id, intraday_id, 4, "running"),
    )
    conn.commit()


def _finish_run_metadata(conn: sqlite3.Connection, *, run_id: str, status: str) -> None:
    conn.execute(
        "UPDATE run_metadata SET status=?, finished_at_utc=? WHERE run_id=?",
        (status, _utc_now_iso(), run_id),
    )
    conn.commit()


def _latest_completed_intraday_bar_id(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        """
        SELECT intraday_bar_id
        FROM run_metadata
        WHERE scan_mode='intraday_promotion' AND status='completed'
        ORDER BY started_at_utc DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    value = row[0]
    return str(value) if value is not None else None


def _default_context_provider(_: ScannerConfig, __: str) -> list[dict[str, Any]]:
    return []


def _default_refresh_provider(_: str, __: str) -> dict[str, Any]:
    return {"ok": True, "data_4h_available": True}


def _select_monitoring_universe(cfg: ScannerConfig, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    threshold = float(cfg.intraday["min_phase_confidence_for_monitoring"])
    for row in rows:
        state = row.get("state_machine_state")
        bucket = row.get("decision_bucket")
        confidence = row.get("market_phase_confidence")
        include = (
            state in _MONITOR_STATES
            or bucket in _MONITOR_BUCKETS
            or (isinstance(confidence, (int, float)) and float(confidence) >= threshold)
        )
        if not include:
            continue
        if not cfg.intraday["enable_reset_check"] and state in _HARD_MONITOR_EXCLUDED:
            continue
        out.append(row)
    return sorted(out, key=lambda x: str(x.get("symbol", "")))


def run_intraday_scan(cfg: ScannerConfig, now_utc: datetime | None = None) -> None:
    now = now_utc or datetime.now(tz=timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware UTC datetime")

    intraday_cfg = cfg.intraday
    if intraday_cfg["frequency_hours"] == 6:
        logger.warning(
            "6h intraday frequency selected — Abschnitt 5 freshness thresholds are calibrated for 4h cadence and may produce premature timing invalidations. Consider loosening freshness thresholds after empirical validation."
        )

    daily_id = compute_daily_bar_id(now)
    intraday_id = get_last_closed_intraday_bar_id(now, timeframe="4h")
    run_id = f"intraday-{daily_id}-{uuid.uuid4().hex[:12]}"

    conn = init_db(str(Path("data") / "independence_release.sqlite"))
    context_provider = getattr(cfg, "intraday_context_provider", _default_context_provider)
    refresh_provider = getattr(cfg, "intraday_refresh_provider", _default_refresh_provider)
    predecision_provider = getattr(cfg, "intraday_predecision_provider", None)
    postdecision_provider = getattr(cfg, "intraday_postdecision_provider", None)

    final_status = "completed"
    try:
        _create_run_metadata(
            conn,
            run_id=run_id,
            daily_id=daily_id,
            intraday_id=intraday_id,
            scan_mode="intraday_promotion",
        )
        rows = list(context_provider(cfg, daily_id))
        monitoring = _select_monitoring_universe(cfg, rows)
        if not monitoring:
            _write_intraday_noop_report(run_id=run_id, daily_id=daily_id, intraday_id=intraday_id)
            return

        previous_intraday_id = _latest_completed_intraday_bar_id(conn)
        has_new = has_new_intraday_bar(previous_intraday_id, intraday_id)

        refresh_required = {
            str(row["symbol"])
            for row in monitoring
            if row.get("intraday_cache_bar_id") != intraday_id
            or row.get("last_intraday_status") == "STALE_4H_REFRESH_FAILED"
        }
        if not has_new and not refresh_required:
            _write_intraday_noop_report(
                run_id=run_id,
                daily_id=daily_id,
                intraday_id=intraday_id,
                skip_reason="no_new_4h_bar",
            )
            return

        diagnostics: list[dict[str, Any]] = []
        decision_rows: list[Any] = []
        for row in monitoring:
            symbol = str(row["symbol"])
            state = row.get("state_machine_state")
            bucket = row.get("decision_bucket")
            confidence = row.get("market_phase_confidence")
            daily_cache_bar_id = row.get("daily_cache_bar_id")
            if daily_cache_bar_id != daily_id:
                diagnostics.append(_diag(run_id, symbol, daily_id, intraday_id, "MISSING_DAILY_CACHE"))
                continue

            needs_refresh = symbol in refresh_required
            if needs_refresh:
                refresh = refresh_provider(symbol, intraday_id)
                if not refresh.get("ok", False):
                    # If a newer closed 4h bar exists but fresh 4h data cannot be fetched for a symbol,
                    # the previous 4h cache must not be used for current intraday decisions.
                    diagnostics.append(_diag(run_id, symbol, daily_id, intraday_id, "STALE_4H_REFRESH_FAILED", stale=True))
                    continue

            if predecision_provider is not None:
                row_obj = predecision_provider(row)
            else:
                row_obj = type(
                    "ExecutionSelectionRow",
                    (),
                    {
                        "symbol": symbol,
                        "priority_score": float(row.get("priority_score", 0.0)),
                        "decision_bucket": bucket,
                        "market_phase_confidence": confidence,
                        "state_machine_state": state,
                    },
                )()
            decision_rows.append(row_obj)
            diagnostics.append(_diag(run_id, symbol, daily_id, intraday_id, None))

        subset = select_execution_subset(decision_rows, cfg.execution)
        max_subset = intraday_cfg["max_execution_subset_size"]
        if max_subset is not None and len(subset) > max_subset:
            raise RuntimeError("Category 3: intraday.max_execution_subset_size exceeded")
        execution = evaluate_execution_subset(subset, cfg.execution)
        _ = execution

        if postdecision_provider is not None:
            postdecision_provider(decision_rows, execution)

        _write_intraday_noop_report(run_id=run_id, daily_id=daily_id, intraday_id=intraday_id, diagnostics=diagnostics)
    except Exception:
        final_status = "failed"
        raise
    finally:
        _finish_run_metadata(conn, run_id=run_id, status=final_status)
        conn.close()


def _diag(
    run_id: str,
    symbol: str,
    daily_id: str,
    intraday_id: str,
    reason: str | None,
    *,
    stale: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": "ir1.0",
        "run_id": run_id,
        "scan_mode": "intraday",
        "symbol": symbol,
        "as_of_utc": _utc_now_iso(),
        "daily_bar_id": daily_id,
        "intraday_bar_id": intraday_id,
        "data_4h_available": not stale,
        "axes": {},
        "phase": {},
        "invalidation": {},
        "cycle": {},
        "state": {},
        "pattern": {},
        "decision": {},
        "reasons": {"reason": reason} if reason else {},
        "execution_attempted": False,
        "execution_status_raw": None,
        "execution_reason_raw": None,
        "execution_pass": None,
        "execution_grade_t16": None,
        "execution_fetch_duration_ms": None,
        "intraday_skipped_stale_4h": stale,
    }


def _write_intraday_noop_report(
    *,
    run_id: str,
    daily_id: str,
    intraday_id: str,
    skip_reason: str = "empty_monitoring_universe",
    diagnostics: list[Mapping[str, Any]] | None = None,
) -> None:
    builder = make_report_builder(project_root=Path.cwd(), config={})
    builder.write_run_report(
        run_id=run_id,
        scan_mode="intraday",
        as_of_utc=_utc_now_iso(),
        daily_bar_id=daily_id,
        intraday_bar_id=intraday_id,
        symbol_lists={"confirmed_candidates": [], "early_candidates": [], "watchlist": [], "late_monitor": []},
        manifest_path=f"reports/runs/{daily_id}/{run_id}.manifest.json",
        diagnostics_records=diagnostics or [],
    )
    logger.info("intraday noop run", extra={"run_id": run_id, "skip_reason": skip_reason})
