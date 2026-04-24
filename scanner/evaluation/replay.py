from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
from typing import Any, Iterable

_EVENT_BY_STATE = {
    "watch": "first_watch",
    "early_ready": "first_early_ready",
    "confirmed_ready": "first_confirmed_ready",
    "late": "first_late",
    "chased": "first_chased",
    "rejected": "first_rejected",
}
_EVENT_ORDER = {
    "first_watch": 10,
    "first_early_ready": 20,
    "first_confirmed_ready": 30,
    "first_late": 40,
    "first_chased": 40,
    "first_rejected": 40,
}


@dataclass(frozen=True)
class ReplayEvent:
    row: dict[str, Any]


def _parse_ts(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("event timestamp missing")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _extract(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def _state(record: dict[str, Any]) -> Any:
    nested = record.get("state")
    if isinstance(nested, dict) and "state_machine_state" in nested:
        return nested.get("state_machine_state")
    return _extract(record, "state_machine_state")


def _bucket(record: dict[str, Any]) -> Any:
    nested = record.get("decision")
    if isinstance(nested, dict) and "decision_bucket" in nested:
        return nested.get("decision_bucket")
    return _extract(record, "decision_bucket")


def _cycle_id(record: dict[str, Any]) -> Any:
    nested = record.get("state")
    if isinstance(nested, dict):
        for key in ("setup_cycle_id", "current_setup_cycle_id"):
            if key in nested:
                return nested[key]
    return _extract(record, "setup_cycle_id", "current_setup_cycle_id")


def _run_paths(manifest_path: Path) -> tuple[str, str]:
    source_snapshot_path = manifest_path.parent.as_posix()
    return source_snapshot_path, manifest_path.as_posix()


def _iter_diag_records(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def reconstruct_event_timeline(*, project_root: Path, runs_root: str = "snapshots/runs") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = project_root / runs_root
    manifests = sorted(root.glob("*/*/*/*/run.manifest.json"))
    by_identity: dict[tuple[str, int, str], dict[str, Any]] = {}
    unknown_bar_ids = 0

    for manifest in manifests:
        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        run_id = str(manifest_payload.get("run_id") or manifest.parent.name)
        diag_path = manifest.parent / "symbol_diagnostics.jsonl.gz"
        seen_in_run: dict[tuple[str, int, str], tuple[str, str]] = {}
        for record in _iter_diag_records(diag_path):
            symbol = record.get("symbol")
            cycle = _cycle_id(record)
            state = _state(record)
            if not isinstance(symbol, str) or not isinstance(cycle, int) or state not in _EVENT_BY_STATE:
                continue
            event_type = _EVENT_BY_STATE[state]
            ts = str(record.get("as_of_utc") or record.get("event_timestamp_utc"))
            ts_dt = _parse_ts(ts)
            daily = record.get("daily_bar_id")
            intraday = record.get("intraday_bar_id")
            if isinstance(intraday, str) and intraday:
                event_bar_id = intraday
                event_bar_type = "intraday_bar_id"
            elif isinstance(daily, str) and daily:
                event_bar_id = daily
                event_bar_type = "daily_bar_id"
            else:
                event_bar_id = None
                event_bar_type = "unknown"
                unknown_bar_ids += 1

            identity = (symbol, cycle, event_type)
            current_sig = (event_bar_id or "", ts)
            if identity in seen_in_run and seen_in_run[identity] != current_sig:
                raise RuntimeError(f"conflicting state records within one run snapshot for {identity}")
            seen_in_run[identity] = current_sig

            source_snapshot_path, source_manifest_path = _run_paths(manifest)
            row = {
                "symbol": symbol,
                "setup_cycle_id": cycle,
                "event_type": event_type,
                "event_order": _EVENT_ORDER[event_type],
                "event_timestamp_utc": ts_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "event_bar_id": event_bar_id,
                "event_bar_id_type": event_bar_type,
                "state_machine_state": state,
                "decision_bucket": _bucket(record),
                "market_phase": record.get("market_phase") or (record.get("phase") or {}).get("market_phase"),
                "market_phase_confidence": record.get("market_phase_confidence") or (record.get("phase") or {}).get("market_phase_confidence"),
                "state_confidence": record.get("state_confidence") or (record.get("state") or {}).get("state_confidence"),
                "priority_score": record.get("priority_score") or (record.get("decision") or {}).get("priority_score"),
                "first_observed_run_id": run_id,
                "first_observed_run_mode": record.get("scan_mode") or manifest_payload.get("scan_mode"),
                "source_snapshot_path": source_snapshot_path,
                "source_manifest_path": source_manifest_path,
                "close_at_early_entry_bar": _extract(record, "close_at_early_entry_bar"),
                "close_at_confirmed_entry_bar": _extract(record, "close_at_confirmed_entry_bar"),
            }
            prev = by_identity.get(identity)
            if prev is None or (row["event_timestamp_utc"], row["event_type"]) < (prev["event_timestamp_utc"], prev["event_type"]):
                by_identity[identity] = row

    events = sorted(
        by_identity.values(),
        key=lambda r: (
            str(r["symbol"]),
            int(r["setup_cycle_id"]),
            int(r["event_order"]),
            str(r["event_timestamp_utc"]),
            str(r["event_type"]),
        ),
    )
    diagnostics = {
        "run_count": len(manifests),
        "event_count": len(events),
        "missing_or_unknown_event_bar_id_count": unknown_bar_ids,
    }
    return events, diagnostics
