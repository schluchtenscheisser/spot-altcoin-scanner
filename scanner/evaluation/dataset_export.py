from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scanner.config import resolve_independence_evaluation_config
from scanner.evaluation.forward_returns import build_signal_metrics
from scanner.evaluation.replay import reconstruct_event_timeline


def run_evaluation_export(
    *,
    project_root: Path,
    config: dict[str, Any] | None = None,
    history_root: str | Path = "snapshots/history",
) -> dict[str, Any]:
    raw_cfg = config or {}
    eval_cfg = resolve_independence_evaluation_config(raw_cfg)
    events, replay_diag = reconstruct_event_timeline(project_root=project_root)
    signal_df, terminal_df, transitions_df, metric_diag = build_signal_metrics(
        events,
        project_root=project_root,
        history_root=str(history_root),
        include_first_watch_metrics=bool(eval_cfg["include_first_watch_metrics"]),
    )

    replay_dir = project_root / "evaluation" / "replay"
    exports_dir = project_root / "evaluation" / "exports"
    replay_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = replay_dir / "event_timeline.jsonl"
    with timeline_path.open("w", encoding="utf-8") as fh:
        for row in events:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    signal_path = exports_dir / "signal_event_metrics.parquet"
    terminal_path = exports_dir / "terminal_event_timeline.parquet"
    transitions_path = exports_dir / "transition_lead_times.parquet"
    summary_path = exports_dir / "evaluation_summary.json"
    manifest_path = replay_dir / "replay_manifest.json"
    replay_diag_path = replay_dir / "replay_diagnostics.json"

    signal_df.to_parquet(signal_path, index=False)
    terminal_df.to_parquet(terminal_path, index=False)
    transitions_df.to_parquet(transitions_path, index=False)

    event_counts: dict[str, int] = {}
    for e in events:
        k = str(e["event_type"])
        event_counts[k] = event_counts.get(k, 0) + 1

    payload = {
        "run_count": replay_diag["run_count"],
        "symbol_count": len({str(e["symbol"]) for e in events}),
        "cycle_count": len({(str(e["symbol"]), int(e["setup_cycle_id"])) for e in events}),
        "event_counts_by_type": event_counts,
        "metric_status_counts": metric_diag["metric_status_counts"],
        "missing_or_unknown_event_bar_id_count": replay_diag["missing_or_unknown_event_bar_id_count"],
        "missing_persisted_reference_price_count": metric_diag["missing_persisted_reference_price_count"],
        "history_root": str(history_root),
        "output_paths": {
            "event_timeline_jsonl": timeline_path.as_posix(),
            "signal_event_metrics_parquet": signal_path.as_posix(),
            "terminal_event_timeline_parquet": terminal_path.as_posix(),
            "transition_lead_times_parquet": transitions_path.as_posix(),
        },
        "config_hash": hashlib.sha256(json.dumps(raw_cfg, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps({"event_count": len(events), "signal_rows": len(signal_df)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    replay_diag_path.write_text(json.dumps(replay_diag, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
