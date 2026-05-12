from __future__ import annotations

from datetime import datetime, timezone
import json
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
from scanner.output.schema import SCHEMA_VERSION as DIAGNOSTICS_SCHEMA_VERSION, validate_diagnostics_record
from scanner.storage import SCHEMA_VERSION, build_run_manifest_path, init_db

logger = logging.getLogger(__name__)

_MONITOR_STATES = {"watch", "early_ready", "confirmed_ready", "late"}
_MONITOR_BUCKETS = {"watchlist", "early_candidates", "confirmed_candidates", "late_monitor"}
_HARD_MONITOR_EXCLUDED = {"rejected", "chased"}
_HARD_EXECUTION_EXCLUDED = {"rejected", "chased"}


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _legacy_ms_intraday_id_to_canonical(value: int, *, field_name: str) -> str:
    legacy_dt = datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
    if (
        legacy_dt.minute != 0
        or legacy_dt.second != 0
        or legacy_dt.microsecond != 0
        or legacy_dt.hour not in {0, 4, 8, 12, 16, 20}
    ):
        raise ValueError(f"{field_name} legacy millisecond value is not canonical 4h UTC close-time: {value!r}")
    return legacy_dt.strftime("%Y-%m-%dT%H:00:00Z")


def _normalize_legacy_run_metadata_intraday_bar_id(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return _legacy_ms_intraday_id_to_canonical(value, field_name=field_name)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.isdigit():
            return _legacy_ms_intraday_id_to_canonical(int(normalized), field_name=field_name)
        has_new_intraday_bar(None, normalized)
        return normalized
    raise TypeError(f"unsupported {field_name} type: {type(value).__name__}")


def _validate_runtime_intraday_bar_id(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be canonical str or None, got {type(value).__name__}")
    normalized = value.strip()
    has_new_intraday_bar(None, normalized)
    return normalized


def _create_run_metadata(
    conn: sqlite3.Connection, *, run_id: str, daily_id: str, intraday_id: str, scan_mode: str
) -> None:
    if not isinstance(intraday_id, str):
        raise TypeError(f"intraday_bar_id must be canonical str, got {type(intraday_id).__name__}")
    has_new_intraday_bar(None, intraday_id)
    conn.execute(
        """
        INSERT INTO run_metadata(
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, scan_mode, _utc_now_iso(), None, daily_id, intraday_id, SCHEMA_VERSION, "running"),
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
        WHERE scan_mode='intraday' AND status='completed'
        ORDER BY started_at_utc DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    value = row[0]
    return _normalize_legacy_run_metadata_intraday_bar_id(value, field_name="intraday_bar_id")


def _default_context_provider(_: ScannerConfig, __: str) -> list[dict[str, Any]]:
    return []


def _default_refresh_provider(_: str, __: str) -> dict[str, Any]:
    return {"ok": True, "data_4h_available": True}


def _intraday_row_has_attachable_execution_context(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    has_state = row.get("state_machine_state") is not None
    has_cycle = any(
        value is not None
        for value in (
            row.get("setup_cycle_id"),
            row.get("current_setup_cycle_id"),
            row.get("resolved_setup_cycle_id"),
        )
    )
    has_decision = row.get("decision_bucket") is not None and row.get("priority_score") is not None
    has_phase = row.get("market_phase") is not None and row.get("market_phase_confidence") is not None
    if has_state and has_cycle and has_decision and has_phase:
        return True, None
    if not has_state:
        return False, "missing_intraday_state_context"
    if not has_cycle:
        return False, "missing_intraday_cycle_context"
    if not has_decision:
        return False, "missing_intraday_decision_context"
    return False, "missing_intraday_phase_context"


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
            scan_mode="intraday",
        )
        rows = list(context_provider(cfg, daily_id))
        monitoring = _select_monitoring_universe(cfg, rows)
        if not monitoring:
            _write_intraday_noop_report(run_id=run_id, daily_id=daily_id, intraday_id=intraday_id, cfg_raw=cfg.raw)
            return

        previous_intraday_id = _latest_completed_intraday_bar_id(conn)
        has_new = has_new_intraday_bar(previous_intraday_id, intraday_id)

        refresh_required: set[str] = set()
        for row in monitoring:
            cache_intraday = _validate_runtime_intraday_bar_id(
                row.get("intraday_cache_bar_id"),
                field_name=f"intraday_cache_bar_id[{row.get('symbol', '?')}]",
            )
            if cache_intraday != intraday_id or row.get("last_intraday_status") == "STALE_4H_REFRESH_FAILED":
                refresh_required.add(str(row["symbol"]))
        if not has_new and not refresh_required:
            _write_intraday_noop_report(
                run_id=run_id,
                daily_id=daily_id,
                intraday_id=intraday_id,
                cfg_raw=cfg.raw,
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

            attachable_context, skip_reason = _intraday_row_has_attachable_execution_context(row)
            diagnostics.append(
                _intraday_diag_from_row(
                    run_id=run_id,
                    row=row,
                    daily_id=daily_id,
                    intraday_id=intraday_id,
                    attachable_context=attachable_context,
                    skip_reason=skip_reason,
                )
            )
            if not attachable_context:
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

        subset = select_execution_subset(decision_rows, cfg.execution)
        max_subset = intraday_cfg["max_execution_subset_size"]
        if max_subset is not None and len(subset) > max_subset:
            raise RuntimeError("Category 3: intraday.max_execution_subset_size exceeded")
        execution = evaluate_execution_subset(subset, cfg.execution)
        decision_symbols = {str(getattr(row_obj, "symbol", "")) for row_obj in decision_rows}
        by_symbol = {str(record["symbol"]): dict(record) for record in diagnostics}
        for symbol in sorted(decision_symbols):
            execution_diag = execution.diagnostics.get(symbol)
            if execution_diag is not None and symbol in by_symbol:
                candidate = by_symbol[symbol]
                state = candidate.get("state") if isinstance(candidate.get("state"), Mapping) else {}
                phase = candidate.get("phase") if isinstance(candidate.get("phase"), Mapping) else {}
                decision = candidate.get("decision") if isinstance(candidate.get("decision"), Mapping) else {}
                cycle = candidate.get("cycle") if isinstance(candidate.get("cycle"), Mapping) else {}
                has_cycle = any(
                    value is not None
                    for value in (
                        state.get("setup_cycle_id"),
                        state.get("current_setup_cycle_id"),
                        cycle.get("resolved_setup_cycle_id"),
                    )
                )
                can_attach_execution = (
                    state.get("state_machine_state") is not None
                    and decision.get("decision_bucket") is not None
                    and decision.get("priority_score") is not None
                    and phase.get("market_phase") is not None
                    and phase.get("market_phase_confidence") is not None
                    and has_cycle
                )
                if not can_attach_execution:
                    raise ValueError(
                        f"execution diagnostics for symbol={symbol} cannot be attached due to incomplete diagnostics context"
                    )
                candidate.update(execution_diag)

        if postdecision_provider is not None:
            maybe_records = postdecision_provider(decision_rows, execution)
            if isinstance(maybe_records, Mapping):
                for symbol, payload in maybe_records.items():
                    if symbol in by_symbol and isinstance(payload, Mapping):
                        by_symbol[symbol].update(payload)

        diagnostics = [validate_diagnostics_record(by_symbol[symbol]) for symbol in sorted(by_symbol)]

        _write_intraday_noop_report(
            run_id=run_id,
            daily_id=daily_id,
            intraday_id=intraday_id,
            cfg_raw=cfg.raw,
            diagnostics=diagnostics,
        )
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
    record = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
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
        "state": {"state_machine_state": None, "setup_cycle_id": None},
        "pattern": {},
        "decision": {"decision_bucket": None},
        "reasons": {"intraday_skip_reason": reason} if reason else {},
        "execution_attempted": False,
        "execution_status_raw": None,
        "execution_reason_raw": None,
        "execution_pass": None,
        "execution_grade_t16": None,
        "execution_fetch_duration_ms": None,
        "execution_size_class": "not_evaluated",
        "recommended_position_factor": None,
        "execution_grade_effective": None,
        "is_reduced_size_eligible": False,
        "is_tradeable_candidate": False,
        "intraday_skipped_stale_4h": stale,
    }
    return validate_diagnostics_record(record)


def _intraday_diag_from_row(
    *,
    run_id: str,
    row: Mapping[str, Any],
    daily_id: str,
    intraday_id: str,
    attachable_context: bool,
    skip_reason: str | None,
) -> dict[str, Any]:
    setup_cycle_id = row.get("setup_cycle_id") if attachable_context else None
    current_setup_cycle_id = row.get("current_setup_cycle_id") if attachable_context else None
    resolved_setup_cycle_id = row.get("resolved_setup_cycle_id") if attachable_context else None
    decision_bucket = row.get("decision_bucket")
    preserve_discarded = decision_bucket == "discarded" and not attachable_context
    return {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "run_id": run_id,
        "scan_mode": "intraday",
        "symbol": str(row["symbol"]),
        "as_of_utc": _utc_now_iso(),
        "daily_bar_id": daily_id,
        "intraday_bar_id": intraday_id,
        "data_4h_available": True,
        "axes": {},
        "phase": {
            "market_phase": row.get("market_phase") if attachable_context else None,
            "market_phase_confidence": row.get("market_phase_confidence") if attachable_context else None,
        },
        "invalidation": {},
        "cycle": {"resolved_setup_cycle_id": resolved_setup_cycle_id},
        "state": {
            "state_machine_state": row.get("state_machine_state") if attachable_context else None,
            "setup_cycle_id": setup_cycle_id,
            "current_setup_cycle_id": current_setup_cycle_id,
        },
        "pattern": {},
        "decision": {
            "decision_bucket": decision_bucket if attachable_context or preserve_discarded else None,
            "priority_score": row.get("priority_score") if attachable_context or preserve_discarded else None,
        },
        "reasons": {"intraday_skip_reason": skip_reason} if skip_reason else {},
        "execution_attempted": False,
        "execution_status_raw": None,
        "execution_reason_raw": None,
        "execution_pass": None,
        "execution_grade_t16": None,
        "execution_fetch_duration_ms": None,
        "execution_size_class": "not_evaluated",
        "recommended_position_factor": None,
        "execution_grade_effective": None,
        "is_reduced_size_eligible": False,
        "is_tradeable_candidate": False,
        "intraday_skipped_stale_4h": False,
    }


def _write_intraday_noop_report(
    *,
    run_id: str,
    daily_id: str,
    intraday_id: str,
    cfg_raw: Mapping[str, Any],
    skip_reason: str = "empty_monitoring_universe",
    diagnostics: list[Mapping[str, Any]] | None = None,
) -> None:
    builder = make_report_builder(project_root=Path.cwd(), config=cfg_raw)
    manifest_path = build_run_manifest_path(daily_bar_id=daily_id, run_id=run_id)
    _write_intraday_manifest(project_root=Path.cwd(), manifest_path=manifest_path, run_id=run_id, daily_id=daily_id, intraday_id=intraday_id)
    builder.write_run_report(
        run_id=run_id,
        scan_mode="intraday",
        as_of_utc=_utc_now_iso(),
        daily_bar_id=daily_id,
        intraday_bar_id=intraday_id,
        symbol_lists={},
        manifest_path=manifest_path,
        diagnostics_records=diagnostics or [],
        extra_report_fields={
            "no_op": diagnostics is None or len(diagnostics) == 0,
            "no_op_reason": skip_reason if diagnostics is None or len(diagnostics) == 0 else None,
        },
    )
    logger.info("intraday noop run", extra={"run_id": run_id, "skip_reason": skip_reason})


def _write_intraday_manifest(*, project_root: Path, manifest_path: str, run_id: str, daily_id: str, intraday_id: str) -> None:
    path = project_root / manifest_path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "scan_mode": "intraday",
        "daily_bar_id": daily_id,
        "intraday_bar_id": intraday_id,
        "symbols": [],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
