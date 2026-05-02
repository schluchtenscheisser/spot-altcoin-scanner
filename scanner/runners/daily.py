from __future__ import annotations

from datetime import date, datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
import uuid
from typing import Any
from math import isfinite

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
from scanner.output.diagnostics_serialization import (
    serialize_axes_block,
    serialize_cycle_block,
    serialize_decision_block,
    serialize_invalidation_block,
    serialize_pattern_block,
    serialize_phase_block,
    serialize_reasons_block,
    serialize_state_block,
)
from scanner.output.schema import validate_diagnostics_record
from scanner.phase import compute_phase_interpretation
from scanner.state import compute_invalidation_and_cycle, compute_state_machine
from scanner.state.models import PersistedStateCycleContext, StateRuntimeContext
from scanner.storage import apply_state_persistence_patch, init_db, load_persisted_state_machine_context
from scanner.universe.classification import classify_symbol

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


def _to_cycle_context(persisted: Any) -> PersistedStateCycleContext:
    return PersistedStateCycleContext(
        symbol=str(getattr(persisted, "symbol")),
        current_setup_cycle_id=getattr(persisted, "current_setup_cycle_id"),
        previous_setup_cycle_id=getattr(persisted, "previous_setup_cycle_id"),
        state_recorded_in_cycle_id=getattr(persisted, "state_recorded_in_cycle_id"),
        prev_state_machine_state=getattr(persisted, "prev_state_machine_state"),
        freshness_distance_state_early=getattr(persisted, "freshness_distance_state_early"),
        freshness_distance_state_confirmed=getattr(persisted, "freshness_distance_state_confirmed"),
        bars_since_state_entered=getattr(persisted, "bars_since_state_entered"),
        bars_since_early_entered=getattr(persisted, "bars_since_early_entered"),
        bars_since_confirmed_entered=getattr(persisted, "bars_since_confirmed_entered"),
        bars_since_cycle_end=getattr(persisted, "bars_since_cycle_end"),
        reclaim_below_reset_floor_seen_since_cycle_end=getattr(persisted, "reclaim_below_reset_floor_seen_since_cycle_end"),
    )


def _build_ticket23_report_payload(
    *,
    ranked: list[RankedDecision],
    diagnostics: list[dict[str, Any]],
) -> dict[str, Any]:
    active_buckets = ("confirmed_candidates", "early_candidates", "watchlist", "late_monitor")
    category_counts_total: dict[str, int] = {}
    category_counts_by_bucket: dict[str, dict[str, int]] = {b: {} for b in active_buckets}
    excluded_counts_by_bucket: dict[str, int] = {b: 0 for b in active_buckets}
    segmented_tradable_buckets: dict[str, dict[str, list[dict[str, Any]]]] = {b: {} for b in active_buckets}
    excluded_candidate_buckets: dict[str, list[dict[str, Any]]] = {b: [] for b in active_buckets}
    tradable_buckets: dict[str, list[dict[str, Any]]] = {b: [] for b in active_buckets}
    diag_by_symbol = {d["symbol"]: d for d in diagnostics}
    bucket_by_symbol = {x.symbol: x.decision.decision_bucket.value for x in ranked}
    for symbol, diag in diag_by_symbol.items():
        bucket = bucket_by_symbol.get(symbol)
        if bucket not in active_buckets:
            continue
        universe = diag["universe"]
        cat = universe["universe_category"]
        category_counts_total[cat] = category_counts_total.get(cat, 0) + 1
        category_counts_by_bucket[bucket][cat] = category_counts_by_bucket[bucket].get(cat, 0) + 1
        item = {
            "symbol": symbol,
            "decision_bucket": bucket,
            "priority_score": diag.get("decision", {}).get("priority_score"),
            "execution_status_raw": diag.get("execution_status_raw"),
            "execution_pass": diag.get("execution_pass"),
            **universe,
        }
        if universe["candidate_excluded"]:
            excluded_counts_by_bucket[bucket] += 1
            excluded_candidate_buckets[bucket].append(item)
        else:
            tradable_buckets[bucket].append(item)
            segmented_tradable_buckets[bucket].setdefault(cat, []).append(item)

    return {
        "universe_classification": {
            "category_counts_total": category_counts_total,
            "category_counts_by_bucket": category_counts_by_bucket,
            "candidate_exclusion_counts_by_bucket": excluded_counts_by_bucket,
            "candidate_excluded_symbol_count": sum(excluded_counts_by_bucket.values()),
        },
        "candidate_segments": {
            "tradable_buckets": tradable_buckets,
            "excluded_candidate_buckets": excluded_candidate_buckets,
            "segmented_tradable_buckets": segmented_tradable_buckets,
        },
    }


def _build_execution_aware_report_payload(
    *,
    ranked: list[RankedDecision],
    diagnostics: list[dict[str, Any]],
) -> dict[str, Any]:
    active_buckets = ("confirmed_candidates", "early_candidates", "watchlist", "late_monitor")
    metric_keys = (
        "structural",
        "execution_attempted",
        "executable",
        "unexpected_execution_state",
        "direct_ok",
        "tranche_ok",
        "marginal",
        "failed",
        "unknown_execution",
        "not_attempted",
    )

    def _empty_counts() -> dict[str, int]:
        return {k: 0 for k in metric_keys}

    def _segment_item(diag: dict[str, Any], *, bucket: str) -> dict[str, Any]:
        universe = diag["universe"]
        raw_priority_score = diag.get("decision", {}).get("priority_score")
        priority_score: float | None = None
        if (
            isinstance(raw_priority_score, (int, float))
            and not isinstance(raw_priority_score, bool)
            and isfinite(float(raw_priority_score))
        ):
            priority_score = float(raw_priority_score)
        return {
            "symbol": str(diag["symbol"]),
            "decision_bucket": bucket,
            "priority_score": priority_score,
            "execution_status_raw": diag.get("execution_status_raw"),
            "execution_reason_raw": diag.get("execution_reason_raw"),
            "execution_pass": diag.get("execution_pass"),
            "universe_category": universe.get("universe_category"),
            "universe_category_confidence": universe.get("universe_category_confidence"),
            "universe_category_reason": universe.get("universe_category_reason"),
            "candidate_excluded": universe.get("candidate_excluded"),
            "candidate_exclusion_reason": universe.get("candidate_exclusion_reason"),
        }

    def _item_sort_key(item: dict[str, Any]) -> tuple[int, float, str]:
        raw = item.get("priority_score")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not isfinite(float(raw)):
            return (1, 0.0, str(item.get("symbol", "")))
        return (0, -float(raw), str(item.get("symbol", "")))

    by_bucket = {bucket: _empty_counts() for bucket in active_buckets}
    by_category: dict[str, dict[str, int]] = {}
    by_bucket_category: dict[str, dict[str, dict[str, int]]] = {bucket: {} for bucket in active_buckets}
    segments: dict[str, list[dict[str, Any]]] = {
        "confirmed_structural": [],
        "confirmed_executable": [],
        "confirmed_unexpected_execution_state": [],
        "confirmed_direct_ok": [],
        "confirmed_tranche_ok": [],
        "confirmed_marginal": [],
        "confirmed_failed": [],
        "confirmed_unknown_execution": [],
        "confirmed_not_attempted": [],
        "early_structural": [],
        "early_executable": [],
        "early_unexpected_execution_state": [],
        "early_direct_ok": [],
        "early_tranche_ok": [],
        "early_marginal": [],
        "early_failed": [],
        "early_unknown_execution": [],
        "early_not_attempted": [],
        "watchlist_direct_ok": [],
        "watchlist_tranche_ok": [],
        "late_monitor_direct_ok": [],
        "late_monitor_tranche_ok": [],
    }
    diag_by_symbol = {d["symbol"]: d for d in diagnostics}

    def _inc(bucket: str, category: str, key: str) -> None:
        by_bucket[bucket][key] += 1
        by_category.setdefault(category, _empty_counts())[key] += 1
        by_bucket_category[bucket].setdefault(category, _empty_counts())[key] += 1

    for record in ranked:
        symbol = record.symbol
        bucket = record.decision.decision_bucket.value
        if bucket not in active_buckets:
            continue
        diag = diag_by_symbol.get(symbol)
        if diag is None:
            continue
        universe = diag["universe"]
        if universe.get("candidate_excluded") is True:
            continue
        category = str(universe.get("universe_category"))
        item = _segment_item(diag, bucket=bucket)
        _inc(bucket, category, "structural")
        status = diag.get("execution_status_raw")
        attempted = bool(diag.get("execution_attempted"))
        execution_pass = diag.get("execution_pass")

        segment_prefix = "confirmed" if bucket == "confirmed_candidates" else "early" if bucket == "early_candidates" else None
        if segment_prefix is not None:
            segments[f"{segment_prefix}_structural"].append(item)

        if attempted:
            _inc(bucket, category, "execution_attempted")

        classification = "unexpected_execution_state"
        if attempted is False and status is None and execution_pass is None:
            classification = "not_attempted"
        elif status == "direct_ok" and execution_pass is True:
            classification = "direct_ok"
        elif status == "tranche_ok" and execution_pass is True:
            classification = "tranche_ok"
        elif status == "marginal" and execution_pass is False:
            classification = "marginal"
        elif status == "fail" and execution_pass is False:
            classification = "failed"
        elif status == "unknown" and execution_pass is None:
            classification = "unknown_execution"

        _inc(bucket, category, classification)
        if classification in {"direct_ok", "tranche_ok"}:
            _inc(bucket, category, "executable")
        if segment_prefix is not None and classification in {"executable", "unexpected_execution_state", "direct_ok", "tranche_ok", "marginal", "failed", "unknown_execution", "not_attempted"}:
            if classification in {"direct_ok", "tranche_ok"}:
                segments[f"{segment_prefix}_executable"].append(item)
            segments[f"{segment_prefix}_{classification}"].append(item)
        if bucket in {"watchlist", "late_monitor"} and classification in {"direct_ok", "tranche_ok"}:
            segments[f"{bucket}_{classification}"].append(item)

    for value in segments.values():
        value.sort(key=_item_sort_key)

    summary = _empty_counts()
    for counts in by_bucket.values():
        for key in metric_keys:
            summary[key] += counts[key]
    return {
        "execution_aware_summary": {
            "total_structural_candidates": summary["structural"],
            "total_execution_attempted": summary["execution_attempted"],
            "total_executable": summary["executable"],
            "total_unexpected_execution_state": summary["unexpected_execution_state"],
            "total_direct_ok": summary["direct_ok"],
            "total_tranche_ok": summary["tranche_ok"],
            "total_marginal": summary["marginal"],
            "total_failed": summary["failed"],
            "total_unknown_execution": summary["unknown_execution"],
            "total_not_attempted": summary["not_attempted"],
        },
        "execution_counts_by_bucket": by_bucket,
        "execution_counts_by_universe_category": by_category,
        "execution_counts_by_bucket_and_category": by_bucket_category,
        "execution_aware_candidate_segments": segments,
    }

def run_daily_scan(cfg: ScannerConfig, as_of_date: str | None = None) -> None:
    daily_id = _validate_as_of_date(as_of_date)
    run_id = f"daily-{daily_id}-{uuid.uuid4().hex[:12]}"
    db_path = Path("data") / "independence_release.sqlite"
    conn = init_db(str(db_path))

    universe_resolver = getattr(cfg, "daily_universe_provider", _default_universe)
    ohlcv_provider = getattr(cfg, "daily_ohlcv_provider", _default_ohlcv)

    try:
        _create_run_metadata(conn, run_id=run_id, daily_id=daily_id, scan_mode="daily")
        symbols = list(universe_resolver(cfg, daily_id))

        if not symbols:
            logger.warning("daily scan non-publishable run: empty universe", extra={"daily_bar_id": daily_id, "run_id": run_id})
            project_root = Path.cwd()
            y, m, d = daily_id.split("-")
            run_dir = project_root / "reports" / "runs" / y / m / d / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            minimal_report = {
                "run_id": run_id,
                "scan_mode": "daily",
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
                inv_ctx = _to_cycle_context(persisted)
                invalidation = compute_invalidation_and_cycle(phase, t1, t2, inv_ctx, cfg)
                runtime = _derive_runtime_context(bars_1d=bars_1d, bars_4h=bars_4h if bars_4h else None)
                state_bundle = compute_state_machine(phase, t1, t2, invalidation, persisted, runtime, cfg)

                entry = resolve_entry_pattern(phase, t1, t2, cfg)
                decision = assign_bucket(phase, state_bundle, entry, cfg, execution_contract=None)
                if state_bundle.persistence_patch is not None:
                    apply_state_persistence_patch(conn, state_bundle.persistence_patch)
                decision_context[symbol] = {
                    "t1": t1,
                    "t2": t2,
                    "phase": phase,
                    "invalidation": invalidation,
                    "persisted": persisted,
                    "state_bundle": state_bundle,
                    "entry": entry,
                    "decision": decision,
                    "market_phase_confidence": phase.market_phase_confidence,
                    "state_machine_state": state_bundle.state_machine_state,
                    "data_4h_available": bool(features.data_4h_available),
                    "universe": classify_symbol(symbol),
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
                execution_diag = execution_result.diagnostics.get(symbol, {})
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
                    "axes": serialize_axes_block(ctx["t1"], ctx["t2"]),
                    "phase": serialize_phase_block(ctx["phase"]),
                    "invalidation": serialize_invalidation_block(ctx["invalidation"]),
                    "cycle": serialize_cycle_block(ctx["invalidation"], ctx["state_bundle"], ctx["persisted"]),
                    "state": serialize_state_block(ctx["state_bundle"], ctx["persisted"]),
                    "pattern": serialize_pattern_block(ctx["entry"]),
                    "decision": serialize_decision_block(decision),
                    "reasons": serialize_reasons_block(
                        ctx["invalidation"],
                        ctx["state_bundle"],
                        decision,
                        execution_diagnostics=execution_diag,
                    ),
                    "universe": {
                        "universe_category": ctx["universe"].universe_category,
                        "universe_category_confidence": ctx["universe"].universe_category_confidence,
                        "universe_category_reason": ctx["universe"].universe_category_reason,
                        "candidate_excluded": ctx["universe"].candidate_excluded,
                        "candidate_exclusion_reason": ctx["universe"].candidate_exclusion_reason,
                    },
                    "execution_attempted": False,
                    "execution_status_raw": None,
                    "execution_reason_raw": None,
                    "execution_pass": None,
                    "execution_grade_t16": None,
                    "execution_fetch_duration_ms": None,
                }
                if execution_diag:
                    diag.update(execution_diag)
                diagnostics.append(validate_diagnostics_record(diag))

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
        ticket23_payload = _build_ticket23_report_payload(ranked=ranked, diagnostics=diagnostics)
        execution_aware_payload = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)
        report = builder.write_run_report(
            run_id=run_id,
            scan_mode="daily",
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
            extra_report_fields={**ticket23_payload, **execution_aware_payload},
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
