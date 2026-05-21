from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, time, timedelta, timezone
import gzip
import json
from pathlib import Path
from typing import Any

import pandas as pd

from scanner.evaluation.historical_replay.bar_loader import HistoricalBarLoader
from scanner.evaluation.historical_replay.scenario import ReplayScenario, scenario_config_hash
from scanner.evaluation.historical_replay.state_store import ReplayStateStore


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


def run_replay(*, scenario: ReplayScenario, output_root: Path) -> dict[str, Any]:
    replay_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_dir = output_root / "runs" / scenario.scenario_id / replay_id
    run_dir.mkdir(parents=True, exist_ok=False)
    state = ReplayStateStore(run_dir / "state.sqlite")
    loader = HistoricalBarLoader(scenario.history_dataset_ref)

    symbols = sorted([p.stem for p in (Path(scenario.history_dataset_ref) / "1d").glob("*.parquet")])
    diagnostics: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    warmup_summary: dict[str, dict[str, Any]] = {}

    current = scenario.evaluation.start_date
    while current <= scenario.evaluation.end_date:
        as_of = datetime.combine(current, time(23, 59, 59), tzinfo=timezone.utc) + timedelta(seconds=scenario.settlement_delay_seconds)
        for sym in symbols:
            s = state.get(sym)
            d1 = loader.closed_bars_as_of(sym, "1d", as_of).bars
            h4 = loader.closed_bars_as_of(sym, "4h", as_of).bars
            if len(d1) < scenario.warm_up_1d_bars or len(h4) < scenario.warm_up_4h_bars:
                info = warmup_summary.setdefault(sym, {"warmup_days_skipped": 0, "first_evaluable_date": None})
                info["warmup_days_skipped"] += 1
                continue
            if info := warmup_summary.get(sym):
                if info["first_evaluable_date"] is None:
                    info["first_evaluable_date"] = current.isoformat()

            row = {"symbol": sym, "as_of_daily_bar_id": current.isoformat(), "scenario_id": scenario.scenario_id, "replay_id": replay_id}
            if d1.empty:
                s["consecutive_missing_1d_bars"] = int(s.get("consecutive_missing_1d_bars") or 0) + 1
                disposition_status, disposition_reason = "not_evaluable_missing_data", "MISSING_1D_BAR"
                row.update({"data_4h_available": bool(not h4.empty), "state_machine_state": s.get("state_machine_state")})
            elif h4.empty:
                s["consecutive_missing_4h_bars"] = int(s.get("consecutive_missing_4h_bars") or 0) + 1
                disposition_status, disposition_reason = "not_evaluable_missing_data", "MISSING_4H_CONTEXT"
                row.update({"data_4h_available": False, "state_machine_state": s.get("state_machine_state")})
            else:
                disposition_status = "admitted"
                disposition_reason = "PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE"
                row.update({"data_4h_available": True, "state_machine_state": "watch"})
                if s.get("last_aging_daily_bar_id") != current.isoformat():
                    s["bars_since_state_entered"] = int(s.get("bars_since_state_entered") or 0) + 1
                    s["last_aging_daily_bar_id"] = current.isoformat()
                s["consecutive_missing_1d_bars"] = 0
                s["consecutive_missing_4h_bars"] = 0
                s["last_evaluable_replay_date"] = current.isoformat()

            row.update({
                "disposition_status": disposition_status,
                "disposition_reason": disposition_reason,
                "state_confidence": s.get("state_confidence"),
                "state_transition_reason": s.get("state_transition_reason"),
                "setup_cycle_id": s.get("setup_cycle_id"),
                "market_phase": "none",
                "market_phase_confidence": 0.0,
                "entry_pattern": "none",
                "entry_pattern_score": 0.0,
                "historical_signal_bucket": _map_bucket(disposition_status, row.get("state_machine_state"), "none"),
                "execution_mode": "disabled_historical_ohlcv_only",
                "execution_evaluation_status": "not_evaluated_historical_ohlcv_only",
                "execution_status_raw": "not_evaluated",
                "execution_size_class": "not_evaluated",
                "execution_grade_effective": None,
                "is_tradeable_candidate": None,
                "signal_daily_close": None if d1.empty else float(d1.iloc[-1].get("close", 0.0)),
                "consecutive_missing_1d_bars": int(s.get("consecutive_missing_1d_bars") or 0),
                "consecutive_missing_4h_bars": int(s.get("consecutive_missing_4h_bars") or 0),
                "last_evaluable_replay_date": s.get("last_evaluable_replay_date"),
                "data_resolution_class": "full_1d_4h" if not h4.empty else "daily_only",
            })
            diagnostics.append(row)
            s.update({k: row.get(k) for k in ["symbol", "state_machine_state", "state_confidence", "state_transition_reason", "setup_cycle_id", "last_evaluable_replay_date", "consecutive_missing_1d_bars", "consecutive_missing_4h_bars", "last_aging_daily_bar_id", "bars_since_state_entered"]})
            state.upsert(s)
        current += timedelta(days=1)

    diag_path = run_dir / "replay_symbol_diagnostics.jsonl.gz"
    with gzip.open(diag_path, "wt", encoding="utf-8") as f:
        for r in diagnostics:
            f.write(json.dumps(r) + "\n")

    event_path = run_dir / "replay_event_candidates.parquet"
    pd.DataFrame(events).to_parquet(event_path, index=False)

    manifest = {
        "manifest_type": "replay_manifest", "schema_version": 1, "scenario_id": scenario.scenario_id, "replay_id": replay_id,
        "scenario_config_hash": scenario_config_hash(scenario), "scenario_config_hash_excludes_splits": True,
        "scanner_config_hash": scenario.scanner_config_hash, "scanner_config_ref": scenario.scanner_config_ref,
        "history_dataset_ref": scenario.history_dataset_ref, "history_manifest_ref": scenario.history_manifest_ref,
        "universe_manifest_ref": scenario.universe_manifest_ref, "evaluation_start_date": scenario.evaluation.start_date.isoformat(),
        "evaluation_end_date": scenario.evaluation.end_date.isoformat(), "timeframes": list(scenario.timeframes), "universe_mode": scenario.universe_mode,
        "daily_replay_time_policy": {"settlement_delay_seconds": scenario.settlement_delay_seconds}, "warm_up_1d_bars": scenario.warm_up_1d_bars,
        "warm_up_4h_bars": scenario.warm_up_4h_bars, "execution_mode": "disabled_historical_ohlcv_only", "execution_evaluation_status": "not_evaluated_historical_ohlcv_only",
        "t4_bypass": True, "production_modules_used": ["scanner.state.machine"], "state_store_path": (run_dir / "state.sqlite").as_posix(),
        "scenario_registry_path": (output_root / "scenario_registry.sqlite").as_posix(), "warmup_summary_by_symbol": warmup_summary,
        "replay_symbol_diagnostics_path": diag_path.as_posix(), "replay_event_candidates_path": event_path.as_posix(), "splits_recorded": None if scenario.splits is None else {k: asdict(v) for k,v in scenario.splits.items()},
        "replay_days_total": (scenario.evaluation.end_date - scenario.evaluation.start_date).days + 1, "replay_days_completed": (scenario.evaluation.end_date - scenario.evaluation.start_date).days + 1,
        "symbols_total": len(symbols), "symbols_evaluable": len(symbols), "symbols_excluded_warmup": len([k for k,v in warmup_summary.items() if v.get('first_evaluable_date') is None]),
        "signal_events_total": len(events), "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (run_dir / "replay_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
