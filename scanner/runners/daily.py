from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
import uuid
from typing import Any

from scanner.axes import compute_tier1_axes, compute_tier2_axes
from scanner.config import ScannerConfig
from scanner.data import DAILY_SCAN_DELTA_BARS, daily_bar_id as compute_daily_bar_id
from scanner.decision.buckets import assign_bucket
from scanner.decision.models import RankedDecision
from scanner.decision.ranking import rank_coins
from scanner.entry.patterns import resolve_entry_pattern
from scanner.execution import evaluate_execution_subset, select_execution_subset
from scanner.features.bundle import build_feature_bundle
from scanner.output import make_report_builder
from scanner.phase import compute_phase_interpretation
from scanner.state import compute_invalidation_and_cycle, compute_state_machine
from scanner.state.models import PersistedStateMachineContext, StateRuntimeContext
from scanner.storage import apply_state_persistence_patch, init_db, load_persisted_state_machine_context

logger = logging.getLogger(__name__)


def _validate_as_of_date(as_of_date: str | None) -> str:
    if as_of_date is None:
        return compute_daily_bar_id(datetime.now(tz=timezone.utc))
    try:
        parsed = date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise ValueError("as_of_date must match YYYY-MM-DD") from exc
    today = datetime.now(tz=timezone.utc).date()
    if parsed >= today:
        raise ValueError("as_of_date must be a past date")
    return parsed.isoformat()


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _create_run_metadata(conn: sqlite3.Connection, *, run_id: str, daily_id: str, scan_mode: str) -> None:
    conn.execute(
        """
        INSERT INTO run_metadata(
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, scan_mode, _utc_now_iso(), None, daily_id, None, 4, "running"),
    )
    conn.commit()


def _finish_run_metadata(conn: sqlite3.Connection, *, run_id: str, status: str) -> None:
    conn.execute(
        "UPDATE run_metadata SET status=?, finished_at_utc=? WHERE run_id=?",
        (status, _utc_now_iso(), run_id),
    )
    conn.commit()


def _default_universe(_: ScannerConfig, __: str) -> list[str]:
    return []


def _default_ohlcv(_: str, __: str) -> list[Any]:
    return []


def _persist_run_manifest(project_root: Path, daily_id: str, run_id: str, ranked: list[RankedDecision]) -> str:
    y, m, d = daily_id.split("-")
    rel = Path("snapshots") / "runs" / y / m / d / run_id / "run.manifest.json"
    path = project_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "daily_bar_id": daily_id,
        "symbols": [r.symbol for r in ranked],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rel.as_posix()




def _derive_runtime_context(*, bars_1d: list[Any], bars_4h: list[Any] | None) -> StateRuntimeContext:
    relevant = bars_4h if bars_4h else bars_1d
    if not relevant:
        raise ValueError("runtime context requires non-empty closed bars")
    last_bar = relevant[-1]
    current_close = float(getattr(last_bar, "close"))
    current_bar_index = int(getattr(last_bar, "close_time_utc_ms"))
    return StateRuntimeContext(
        current_close=current_close,
        current_bar_index=current_bar_index,
        delta_closed_bars_relevant=DAILY_SCAN_DELTA_BARS,
    )

def run_daily_scan(cfg: ScannerConfig, as_of_date: str | None = None) -> None:
    daily_id = _validate_as_of_date(as_of_date)
    run_id = f"daily-{daily_id}-{uuid.uuid4().hex[:12]}"
    db_path = Path("data") / "independence_release.sqlite"
    conn = init_db(str(db_path))

    universe_resolver = getattr(cfg, "daily_universe_provider", _default_universe)
    ohlcv_provider = getattr(cfg, "daily_ohlcv_provider", _default_ohlcv)

    try:
        _create_run_metadata(conn, run_id=run_id, daily_id=daily_id, scan_mode="daily_discovery")
        symbols = list(universe_resolver(cfg, daily_id))

        if not symbols:
            logger.warning("daily scan non-publishable run: empty universe", extra={"daily_bar_id": daily_id, "run_id": run_id})
            project_root = Path.cwd()
            y, m, d = daily_id.split("-")
            run_dir = project_root / "reports" / "runs" / y / m / d / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            minimal_report = {
                "run_id": run_id,
                "scan_mode": "daily_discovery",
                "as_of_utc": _utc_now_iso(),
                "daily_bar_id": daily_id,
                "intraday_bar_id": None,
                "candidate_count": 0,
                "symbol_lists": {"confirmed_candidates": [], "early_candidates": [], "watchlist": [], "late_monitor": []},
            }
            (run_dir / "report.json").write_text(json.dumps(minimal_report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            return

        ranked_inputs: list[RankedDecision] = []
        decision_context: dict[str, dict[str, Any]] = {}
        diagnostics: list[dict[str, Any]] = []
        for symbol in sorted(symbols):
            try:
                bars_1d = ohlcv_provider(symbol, "1d")
                bars_4h = ohlcv_provider(symbol, "4h")
                bar_clock_context = {"daily_bar_id": daily_id, "intraday_bar_id": None, "daily_close_time_utc_ms": 0}
                features = build_feature_bundle(symbol, bar_clock_context, bars_1d, bars_4h if bars_4h else None, cfg)
                t1 = compute_tier1_axes(features, cfg)
                t2 = compute_tier2_axes(features, cfg)
                phase = compute_phase_interpretation(t1, t2, cfg)

                persisted = load_persisted_state_machine_context(conn, symbol)
                inv_ctx = PersistedStateMachineContext(**asdict(persisted))
                invalidation = compute_invalidation_and_cycle(phase, t1, t2, inv_ctx, cfg)
                runtime = _derive_runtime_context(bars_1d=bars_1d, bars_4h=bars_4h if bars_4h else None)
                state_bundle = compute_state_machine(phase, t1, t2, invalidation, persisted, runtime, cfg)

                entry = resolve_entry_pattern(phase, t1, t2, cfg)
                decision = assign_bucket(phase, state_bundle, entry, cfg, execution_contract=None)
                if state_bundle.persistence_patch is not None:
                    apply_state_persistence_patch(conn, state_bundle.persistence_patch)
                decision_context[symbol] = {
                    "phase": phase,
                    "state_bundle": state_bundle,
                    "entry": entry,
                    "decision": decision,
                    "market_phase_confidence": phase.market_phase_confidence,
                    "state_machine_state": state_bundle.state_machine_state,
                    "data_4h_available": bool(features.data_4h_available),
                }
                ranked_inputs.append(
                    RankedDecision(
                        symbol=symbol,
                        decision=decision,
                        state_confidence=state_bundle.state_confidence,
                        market_phase_confidence=phase.market_phase_confidence,
                    )
                )
            except Exception as exc:
                logger.warning("daily scan symbol skipped", extra={"symbol": symbol, "exception_type": type(exc).__name__})
                continue

        if decision_context:
            selection_rows = [
                type(
                    "ExecutionSelectionRow",
                    (),
                    {
                        "symbol": symbol,
                        "priority_score": float(ctx["decision"].priority_score),
                        "decision_bucket": ctx["decision"].decision_bucket,
                        "market_phase_confidence": ctx["market_phase_confidence"],
                        "state_machine_state": ctx["state_machine_state"],
                    },
                )()
                for symbol, ctx in decision_context.items()
            ]
            execution_subset = select_execution_subset(selection_rows, cfg.execution)
            safety_limit = cfg.execution.get("execution_safety_limit")
            if safety_limit is not None and len(execution_subset) > int(safety_limit):
                raise RuntimeError("Category 3: execution_safety_limit exceeded")

            execution_result = evaluate_execution_subset(execution_subset, cfg.execution)
            ranked_inputs = []
            for symbol, ctx in decision_context.items():
                contract = execution_result.contracts.get(symbol)
                decision = ctx["decision"]
                if contract is not None:
                    decision = assign_bucket(
                        ctx["phase"],
                        ctx["state_bundle"],
                        ctx["entry"],
                        cfg,
                        execution_contract=contract,
                    )
                ranked_inputs.append(
                    RankedDecision(
                        symbol=symbol,
                        decision=decision,
                        state_confidence=ctx["state_bundle"].state_confidence,
                        market_phase_confidence=ctx["market_phase_confidence"],
                    )
                )
                diag = {
                    "schema_version": "ir1.0",
                    "run_id": run_id,
                    "scan_mode": "daily",
                    "symbol": symbol,
                    "as_of_utc": _utc_now_iso(),
                    "daily_bar_id": daily_id,
                    "intraday_bar_id": None,
                    "data_4h_available": bool(ctx["data_4h_available"]),
                    "axes": {},
                    "phase": {},
                    "invalidation": {},
                    "cycle": {},
                    "state": {},
                    "pattern": {},
                    "decision": {},
                    "reasons": {},
                    "execution_attempted": False,
                    "execution_status_raw": None,
                    "execution_reason_raw": None,
                    "execution_pass": None,
                    "execution_grade_t16": None,
                    "execution_fetch_duration_ms": None,
                }
                if symbol in execution_result.diagnostics:
                    diag.update(execution_result.diagnostics[symbol])
                diagnostics.append(diag)

        ranked = rank_coins(ranked_inputs, cfg)
        symbol_lists = {
            "confirmed_candidates": [x.symbol for x in ranked if x.decision.decision_bucket.value == "confirmed_candidates"],
            "early_candidates": [x.symbol for x in ranked if x.decision.decision_bucket.value == "early_candidates"],
            "watchlist": [x.symbol for x in ranked if x.decision.decision_bucket.value == "watchlist"],
            "late_monitor": [x.symbol for x in ranked if x.decision.decision_bucket.value == "late_monitor"],
        }
        project_root = Path.cwd()
        manifest_path = _persist_run_manifest(project_root, daily_id, run_id, ranked)
        builder = make_report_builder(project_root=project_root, config=cfg.raw)
        report = builder.write_run_report(
            run_id=run_id,
            scan_mode="daily_discovery",
            as_of_utc=_utc_now_iso(),
            daily_bar_id=daily_id,
            intraday_bar_id=None,
            symbol_lists=symbol_lists,
            manifest_path=manifest_path,
            diagnostics_records=diagnostics,
            counts_by_bucket={
                "confirmed_candidates": len(symbol_lists["confirmed_candidates"]),
                "early_candidates": len(symbol_lists["early_candidates"]),
                "watchlist": len(symbol_lists["watchlist"]),
                "late_monitor": len(symbol_lists["late_monitor"]),
                "discarded": max(0, len(ranked) - sum(len(v) for v in symbol_lists.values())),
            },
        )
        builder.write_daily_report(report)
    except Exception:
        _finish_run_metadata(conn, run_id=run_id, status="failed")
        raise
    finally:
        current = conn.execute("SELECT status FROM run_metadata WHERE run_id=?", (run_id,)).fetchone()
        if current is not None and current[0] == "running":
            _finish_run_metadata(conn, run_id=run_id, status="completed")
        conn.close()
