from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone
import gzip
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from scanner.evaluation.historical_replay.bar_loader import HistoricalBarLoader
from scanner.evaluation.historical_replay.production_adapter import (
    HistoricalProductionAdapter,
    ReplayProductionAdapterProtocol,
)
from scanner.evaluation.historical_replay.scenario import ReplayScenario, scenario_config_hash
from scanner.evaluation.historical_replay.state_store import ReplayStateStore

logger = logging.getLogger(__name__)


def _generate_replay_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _map_bucket(disposition_status: str, state_machine_state: str | None, entry_pattern: str) -> str:
    if disposition_status == "not_evaluable_warmup":
        return "not_evaluable_warmup"
    if disposition_status == "not_evaluable_missing_data":
        return "not_evaluable_missing_data"
    if disposition_status == "untracked":
        return "watchlist"
    if state_machine_state == "confirmed_ready" and entry_pattern != "none":
        return "confirmed_candidates"
    if state_machine_state == "confirmed_ready" and entry_pattern == "none":
        return "late_monitor"
    if state_machine_state == "early_ready" and entry_pattern != "none":
        return "early_candidates"
    if state_machine_state == "early_ready" and entry_pattern == "none":
        return "watchlist"
    if state_machine_state == "watch":
        return "watchlist"
    if state_machine_state in {"late", "chased"}:
        return "late_monitor"
    if state_machine_state == "rejected":
        return "discarded"
    return "watchlist"


def _bar_day(ts: Any) -> date:
    return pd.Timestamp(ts).tz_convert("UTC").date()


def get_current_daily_bar(d1_slice: pd.DataFrame, as_of_daily_bar_id: str) -> dict[str, Any] | None:
    if d1_slice.empty:
        return None
    target = date.fromisoformat(as_of_daily_bar_id)
    matches = d1_slice[d1_slice["close_time_utc"].map(_bar_day) == target]
    if matches.empty:
        return None
    return matches.iloc[-1].to_dict()


def has_current_day_4h_coverage(h4_slice: pd.DataFrame, as_of_daily_bar_id: str) -> bool:
    if h4_slice.empty:
        return False
    target = date.fromisoformat(as_of_daily_bar_id)
    return bool((h4_slice["close_time_utc"].map(_bar_day) == target).any())


def _compute_manifest_symbol_counts(warmup_summary: dict[str, dict[str, Any]], symbols_total: int) -> tuple[int, int]:
    evaluable = sum(1 for v in warmup_summary.values() if v.get("first_evaluable_date") is not None)
    excluded = sum(1 for v in warmup_summary.values() if v.get("first_evaluable_date") is None)
    if symbols_total == 0:
        return 0, 0
    return evaluable, excluded




def _atomic_write_json(manifest_path: Path, payload: dict[str, Any]) -> None:
    tmp = manifest_path.with_name(manifest_path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(manifest_path)


def _validate_resume_state_store(path: Path) -> None:
    import sqlite3

    try:
        con = sqlite3.connect(path)
        row = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='replay_state'").fetchone()
        if not row:
            raise ValueError
        con.execute("SELECT symbol FROM replay_state LIMIT 1").fetchone()
    except Exception as exc:
        raise ValueError(f"resume_from_state is not a valid replay state store: {path}") from exc
    finally:
        try:
            con.close()
        except Exception:
            pass

def run_replay(
    scenario: ReplayScenario,
    output_root: Path,
    chunk_start: date | None = None,
    chunk_end: date | None = None,
    resume_from_state: Path | None = None,
    replay_id: str | None = None,
    chunk_id: str | None = None,
    production_adapter: ReplayProductionAdapterProtocol | None = None,
) -> dict[str, Any]:
    is_chunk_mode = chunk_start is not None or chunk_end is not None
    if (chunk_start is None) ^ (chunk_end is None):
        raise ValueError("Both --chunk-start and --chunk-end are required")
    if is_chunk_mode:
        assert chunk_start is not None and chunk_end is not None
        if chunk_start < scenario.evaluation.start_date:
            raise ValueError("chunk_start is before scenario evaluation start")
        if chunk_end > scenario.evaluation.end_date:
            raise ValueError("chunk_end is after scenario evaluation end")
        if chunk_start > chunk_end:
            raise ValueError("chunk_start is after chunk_end")
        if chunk_start > scenario.evaluation.start_date and resume_from_state is None:
            raise ValueError("resume_from_state is required when chunk_start > scenario evaluation start")
    replay_id = replay_id or _generate_replay_id()
    run_dir = output_root / "runs" / scenario.scenario_id / replay_id
    manifest_path = run_dir / "replay_manifest.json"
    prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    if prior_manifest is not None and (prior_manifest.get("scenario_id") != scenario.scenario_id or prior_manifest.get("scenario_config_hash") != scenario_config_hash(scenario)):
        raise ValueError("replay_id conflict: scenario mismatch")
    if is_chunk_mode:
        chunk_id = chunk_id or f"{chunk_start.isoformat()}_to_{chunk_end.isoformat()}"
        run_dir.mkdir(parents=True, exist_ok=True)
        if prior_manifest is not None and "chunks_completed" not in prior_manifest:
            raise ValueError(f"replay_id {replay_id} belongs to a full-window run and cannot be reused in chunk mode")
        chunks_completed = list((prior_manifest or {}).get("chunks_completed", []))
        if chunk_id in chunks_completed:
            raise ValueError(f"chunk_id already completed: {chunk_id}")
        if chunks_completed:
            expected_start = date.fromisoformat(prior_manifest["last_chunk_end_date"]) + timedelta(days=1)
            if chunk_start != expected_start:
                raise ValueError(f"chunk gap detected: expected chunk_start {expected_start.isoformat()}")
        chunk_dir = run_dir / "chunks" / chunk_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        state_path = chunk_dir / "state_working.sqlite"
        if resume_from_state is not None:
            if not resume_from_state.exists():
                raise ValueError(f"resume_from_state file not found: {resume_from_state}")
            _validate_resume_state_store(resume_from_state)
            logger.info("Resuming from state: %s", resume_from_state.as_posix())
            state_path.write_bytes(resume_from_state.read_bytes())
        else:
            if state_path.exists():
                logger.warning(
                    "Found existing state_working.sqlite for fresh chunk %s. Deleting and recreating.",
                    chunk_id,
                )
                state_path.unlink()
            logger.info("Starting fresh replay state for chunk %s", chunk_id)
        start_day, end_day = chunk_start, chunk_end
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        state_path = run_dir / "state.sqlite"
        start_day, end_day = scenario.evaluation.start_date, scenario.evaluation.end_date
    state = ReplayStateStore(state_path)
    loader = HistoricalBarLoader(scenario.history_dataset_ref)
    adapter = production_adapter or HistoricalProductionAdapter()
    production_modules_used: set[str] = set()

    symbols = sorted([p.name.replace("symbol=", "") for p in (Path(scenario.history_dataset_ref) / "timeframe=1d").iterdir() if p.is_dir()])
    diagnostics: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    warmup_summary: dict[str, dict[str, Any]] = {s: {"warmup_days_skipped": 0, "first_evaluable_date": None} for s in symbols}
    if is_chunk_mode and prior_manifest and isinstance(prior_manifest.get("warmup_summary_by_symbol"), dict):
        for sym, prev in prior_manifest["warmup_summary_by_symbol"].items():
            if sym in warmup_summary:
                warmup_summary[sym]["warmup_days_skipped"] = int(prev.get("warmup_days_skipped") or 0)
                warmup_summary[sym]["first_evaluable_date"] = prev.get("first_evaluable_date")

    replay_days_total = (scenario.evaluation.end_date - scenario.evaluation.start_date).days + 1
    logger.info(
        "Starting replay scenario_id=%s replay_id=%s symbols=%s evaluation=%s..%s",
        scenario.scenario_id,
        replay_id,
        len(symbols),
        scenario.evaluation.start_date.isoformat(),
        scenario.evaluation.end_date.isoformat(),
    )
    days_completed = 0
    signal_events_so_far = 0
    diagnostics_so_far = 0
    current = start_day
    try:
        while current <= end_day:
            day_idx = days_completed + 1
            logger.info("Replaying day %s (%s/%s) symbols=%s", current.isoformat(), day_idx, replay_days_total, len(symbols))
            admitted_count = 0
            untracked_count = 0
            warmup_skipped_count = 0
            missing_data_count = 0
            events_today = 0
            diagnostics_today = 0
            as_of = datetime.combine(current, time(23, 59, 59), tzinfo=timezone.utc) + timedelta(seconds=scenario.settlement_delay_seconds)
            bar_id = current.isoformat()
            for sym in symbols:
                try:
                    s = state.get(sym)
                    d1 = loader.closed_bars_as_of(sym, "1d", as_of).bars
                    h4 = loader.closed_bars_as_of(sym, "4h", as_of).bars
                    info = warmup_summary[sym]

                    if len(d1) < scenario.warm_up_1d_bars or len(h4) < scenario.warm_up_4h_bars:
                        info["warmup_days_skipped"] += 1
                        warmup_skipped_count += 1
                        continue
                    if info["first_evaluable_date"] is None:
                        info["first_evaluable_date"] = bar_id

                    current_d1 = get_current_daily_bar(d1, bar_id)
                    row = {"symbol": sym, "as_of_daily_bar_id": bar_id, "scenario_id": scenario.scenario_id, "replay_id": replay_id}
                    adapter_out = None

                    if current_d1 is None:
                        s["consecutive_missing_1d_bars"] = int(s.get("consecutive_missing_1d_bars") or 0) + 1
                        disposition_status, disposition_reason = "not_evaluable_missing_data", "MISSING_1D_BAR"
                        row.update({"data_4h_available": has_current_day_4h_coverage(h4, bar_id), "state_machine_state": s.get("state_machine_state")})
                        signal_daily_close = None
                    elif not has_current_day_4h_coverage(h4, bar_id):
                        s["consecutive_missing_4h_bars"] = int(s.get("consecutive_missing_4h_bars") or 0) + 1
                        disposition_status, disposition_reason = "not_evaluable_missing_data", "MISSING_4H_CONTEXT"
                        row.update({"data_4h_available": False, "state_machine_state": s.get("state_machine_state")})
                        signal_daily_close = float(current_d1.get("close", 0.0))
                    else:
                        adapter_out = adapter(
                            symbol=sym,
                            as_of_daily_bar_id=bar_id,
                            closed_1d_bars=d1,
                            closed_4h_bars=h4,
                            persisted_state=dict(s),
                            scanner_config={"ref": scenario.scanner_config_ref, "hash": scenario.scanner_config_hash},
                        )
                        disposition_status = adapter_out.disposition_status
                        disposition_reason = adapter_out.disposition_reason
                        row.update({"data_4h_available": True, "state_machine_state": adapter_out.state_machine_state})
                        if s.get("last_aging_daily_bar_id") != bar_id:
                            s["bars_since_state_entered"] = int(s.get("bars_since_state_entered") or 0) + 1
                            s["last_aging_daily_bar_id"] = bar_id
                        s["consecutive_missing_1d_bars"] = 0
                        s["consecutive_missing_4h_bars"] = 0
                        s["last_evaluable_replay_date"] = bar_id
                        signal_daily_close = adapter_out.signal_daily_close
                        for k, v in adapter_out.updated_state_patch.items():
                            s[k] = v
                        production_modules_used.update(adapter_out.production_modules_used)
                        for event_type in adapter_out.transition_event_types:
                            if not event_type.startswith("first_"):
                                continue
                            event_context = {
                                "scenario_id": scenario.scenario_id,
                                "replay_id": replay_id,
                                "symbol": sym,
                                "event_type": event_type,
                                "as_of_daily_bar_id": bar_id,
                                "event_timestamp_utc": f"{bar_id}T23:59:59Z",
                                "state_machine_state": adapter_out.state_machine_state,
                                "historical_signal_bucket": _map_bucket(
                                    disposition_status,
                                    adapter_out.state_machine_state,
                                    adapter_out.entry_pattern,
                                ),
                                "market_phase": adapter_out.market_phase,
                                "market_phase_confidence": adapter_out.market_phase_confidence,
                                "state_confidence": adapter_out.state_confidence,
                                "state_transition_reason": adapter_out.state_transition_reason,
                                "entry_pattern": adapter_out.entry_pattern,
                                "entry_pattern_score": adapter_out.entry_pattern_score,
                                "setup_cycle_id": adapter_out.setup_cycle_id,
                                "signal_daily_close": adapter_out.signal_daily_close,
                                "consecutive_missing_1d_bars_at_event": int(s.get("consecutive_missing_1d_bars") or 0),
                                "consecutive_missing_4h_bars_at_event": int(s.get("consecutive_missing_4h_bars") or 0),
                                "data_4h_available": True,
                                "data_resolution_class": "full_1d_4h",
                                "disposition_status": disposition_status,
                                "disposition_reason": disposition_reason,
                                "execution_evaluation_status": "not_evaluated_historical_ohlcv_only",
                                "is_tradeable_candidate": None,
                            }
                            events.append(event_context)
                            events_today += 1

                    adapter_used = adapter_out is not None
                    row.update({
                "disposition_status": disposition_status,
                "disposition_reason": disposition_reason,
                "state_confidence": adapter_out.state_confidence if disposition_status == "admitted" else s.get("state_confidence"),
                "state_transition_reason": adapter_out.state_transition_reason if disposition_status == "admitted" else s.get("state_transition_reason"),
                "setup_cycle_id": adapter_out.setup_cycle_id if disposition_status == "admitted" else s.get("setup_cycle_id"),
                "market_phase": adapter_out.market_phase if adapter_used else "none",
                "market_phase_confidence": adapter_out.market_phase_confidence if adapter_used else 0.0,
                "entry_pattern": adapter_out.entry_pattern if adapter_used else "none",
                "entry_pattern_score": adapter_out.entry_pattern_score if adapter_used else 0.0,
                "historical_signal_bucket": _map_bucket(disposition_status, row.get("state_machine_state"), adapter_out.entry_pattern if disposition_status == "admitted" else "none"),
                "execution_mode": "disabled_historical_ohlcv_only",
                "execution_evaluation_status": "not_evaluated_historical_ohlcv_only",
                "execution_status_raw": "not_evaluated",
                "execution_size_class": "not_evaluated",
                "execution_grade_effective": None,
                "is_tradeable_candidate": None,
                "signal_daily_close": signal_daily_close,
                "consecutive_missing_1d_bars": int(s.get("consecutive_missing_1d_bars") or 0),
                "consecutive_missing_4h_bars": int(s.get("consecutive_missing_4h_bars") or 0),
                "last_evaluable_replay_date": s.get("last_evaluable_replay_date"),
                "data_resolution_class": "full_1d_4h" if row.get("data_4h_available") else "daily_only",
            })
                    diagnostics.append(row)
                    diagnostics_today += 1
                    s["symbol"] = sym
                    for k in [
                "state_machine_state",
                "state_confidence",
                "state_transition_reason",
                "setup_cycle_id",
                "last_evaluable_replay_date",
                "consecutive_missing_1d_bars",
                "consecutive_missing_4h_bars",
                    ]:
                        if row.get(k) is not None or k in {"consecutive_missing_1d_bars", "consecutive_missing_4h_bars"}:
                            s[k] = row.get(k)
                    if disposition_status == "admitted":
                        s["bars_since_state_entered"] = int(s.get("bars_since_state_entered") or 0)
                        admitted_count += 1
                    if disposition_status == "untracked":
                        untracked_count += 1
                    if disposition_status == "not_evaluable_missing_data":
                        missing_data_count += 1
                    state.upsert(s)
                except Exception as exc:
                    logger.exception("Symbol %s day %s failed: %s", sym, bar_id, exc)
                    raise
            days_completed += 1
            signal_events_so_far += events_today
            diagnostics_so_far += diagnostics_today
            logger.info(
                "Day %s done: admitted=%s untracked=%s warmup_skipped=%s missing_data=%s events=%s diagnostics=%s",
                bar_id,
                admitted_count,
                untracked_count,
                warmup_skipped_count,
                missing_data_count,
                events_today,
                diagnostics_today,
            )
            if days_completed % 10 == 0:
                logger.info(
                    "Progress %s/%s days completed, signal_events_so_far=%s diagnostics_so_far=%s",
                    days_completed,
                    replay_days_total,
                    signal_events_so_far,
                    diagnostics_so_far,
                )
            current += timedelta(days=1)
    except Exception as exc:
        logger.critical("Replay aborted after %s/%s days: %s", days_completed, replay_days_total, exc, exc_info=True)
        raise

    logger.info("Writing replay outputs run_dir=%s", run_dir.as_posix())
    diag_path = (run_dir / "replay_symbol_diagnostics.jsonl.gz") if not is_chunk_mode else (run_dir / "chunks" / chunk_id / "replay_symbol_diagnostics.jsonl.gz")
    with gzip.open(diag_path, "wt", encoding="utf-8") as f:
        for r in diagnostics:
            f.write(json.dumps(r) + "\n")

    event_path = (run_dir / "replay_event_candidates.parquet") if not is_chunk_mode else (run_dir / "chunks" / chunk_id / "replay_event_candidates.parquet")
    pd.DataFrame(events).to_parquet(event_path, index=False)
    logger.info(
        "Wrote replay outputs diagnostics=%s events=%s manifest=%s",
        diag_path.as_posix(),
        event_path.as_posix(),
        (run_dir / "replay_manifest.json").as_posix(),
    )
    symbols_evaluable, symbols_excluded_warmup = _compute_manifest_symbol_counts(warmup_summary, len(symbols))

    manifest = {
        "manifest_type": "replay_manifest", "schema_version": 1, "scenario_id": scenario.scenario_id, "replay_id": replay_id,
        "scenario_config_hash": scenario_config_hash(scenario), "scenario_config_hash_excludes_splits": True,
        "scanner_config_hash": scenario.scanner_config_hash, "scanner_config_ref": scenario.scanner_config_ref,
        "history_dataset_ref": scenario.history_dataset_ref, "history_manifest_ref": scenario.history_manifest_ref,
        "universe_manifest_ref": scenario.universe_manifest_ref, "evaluation_start_date": scenario.evaluation.start_date.isoformat(),
        "evaluation_end_date": scenario.evaluation.end_date.isoformat(), "timeframes": list(scenario.timeframes), "universe_mode": scenario.universe_mode,
        "daily_replay_time_policy": {"settlement_delay_seconds": scenario.settlement_delay_seconds}, "warm_up_1d_bars": scenario.warm_up_1d_bars,
        "warm_up_4h_bars": scenario.warm_up_4h_bars, "execution_mode": "disabled_historical_ohlcv_only", "execution_evaluation_status": "not_evaluated_historical_ohlcv_only",
        "t4_bypass": True, "production_modules_used": sorted(production_modules_used), "state_store_path": state_path.as_posix(),
        "scenario_registry_path": (output_root / "scenario_registry.sqlite").as_posix(), "warmup_summary_by_symbol": warmup_summary,
        "replay_symbol_diagnostics_path": diag_path.as_posix(), "replay_event_candidates_path": event_path.as_posix(), "splits_recorded": None if scenario.splits is None else {k: {"start_date": v.start_date.isoformat(), "end_date": v.end_date.isoformat()} for k,v in scenario.splits.items()},
        "replay_days_total": replay_days_total, "replay_days_completed": replay_days_total if not is_chunk_mode else days_completed + int((prior_manifest or {}).get("replay_days_completed", 0)),
        "symbols_total": len(symbols), "symbols_evaluable": symbols_evaluable, "symbols_excluded_warmup": symbols_excluded_warmup,
        "signal_events_total": len(events), "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if is_chunk_mode:
        state_final = run_dir / "chunks" / chunk_id / "state_final.sqlite"
        state_final.write_bytes(state_path.read_bytes())
        (run_dir / "state_latest.sqlite").write_bytes(state_final.read_bytes())
        manifest["chunks_completed"] = list((prior_manifest or {}).get("chunks_completed", [])) + [chunk_id]
        manifest["chunks_total"] = None
        manifest["last_chunk_end_date"] = end_day.isoformat()
        manifest["is_complete"] = end_day == scenario.evaluation.end_date
        manifest["signal_events_so_far"] = int((prior_manifest or {}).get("signal_events_so_far", 0)) + len(events)
        manifest["diagnostics_so_far"] = int((prior_manifest or {}).get("diagnostics_so_far", 0)) + len(diagnostics)
        chunk_manifest = {
            "scenario_id": scenario.scenario_id, "replay_id": replay_id, "chunk_id": chunk_id,
            "chunk_start_date": start_day.isoformat(), "chunk_end_date": end_day.isoformat(),
            "days_in_chunk": (end_day - start_day).days + 1, "days_completed": days_completed,
            "signal_events_in_chunk": len(events), "diagnostics_in_chunk": len(diagnostics),
            "resumed_from_state": resume_from_state.as_posix() if resume_from_state else None,
            "state_working_path": state_path.as_posix(), "state_final_path": state_final.as_posix(),
            "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _atomic_write_json(run_dir / "chunks" / chunk_id / "chunk_manifest.json", chunk_manifest)
    _atomic_write_json(run_dir / "replay_manifest.json", manifest)
    logger.info(
        "Replay complete replay_id=%s days=%s symbols_total=%s symbols_evaluable=%s signal_events=%s diagnostics=%s",
        replay_id,
        replay_days_total,
        len(symbols),
        symbols_evaluable,
        len(events),
        len(diagnostics),
    )
    return manifest
