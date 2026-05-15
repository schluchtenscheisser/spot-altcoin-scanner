#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT_ON_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_ON_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_ON_PATH))

from scanner.evaluation.dataset_export import run_evaluation_export
from scanner.evaluation.forward_returns import HORIZONS

KEY_EVENT_TYPES = (
    "first_watch",
    "first_early_ready",
    "first_confirmed_ready",
    "first_late",
    "first_chased",
    "first_rejected",
)

FETCH_OHLCV_COMMAND = "python scripts/fetch_ohlcv_history_for_evaluation.py --project-root ."

OUTPUT_SPECS = {
    "signal_event_metrics_parquet": ("evaluation/exports/signal_event_metrics.parquet", "parquet"),
    "terminal_event_timeline_parquet": ("evaluation/exports/terminal_event_timeline.parquet", "parquet"),
    "transition_lead_times_parquet": ("evaluation/exports/transition_lead_times.parquet", "parquet"),
    "evaluation_summary_json": ("evaluation/exports/evaluation_summary.json", "json"),
    "event_timeline_jsonl": ("evaluation/replay/event_timeline.jsonl", "jsonl"),
    "replay_manifest_json": ("evaluation/replay/replay_manifest.json", "json"),
    "replay_diagnostics_json": ("evaluation/replay/replay_diagnostics.json", "json"),
}


@dataclass(frozen=True)
class InputValidation:
    manifest_count: int
    ohlcv_symbol_count: int
    ohlcv_date_min: str | None
    ohlcv_date_max: str | None
    missing_input_roots: list[str]
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class OutputValidation:
    outputs: dict[str, str]
    missing_outputs: list[str]
    unreadable_outputs: list[str]
    readable_outputs: dict[str, bool]

    @property
    def ok(self) -> bool:
        return not self.missing_outputs and not self.unreadable_outputs


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel_path(project_root: Path, path: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _effective_history_root(project_root: Path, history_root: str) -> Path:
    candidate = Path(history_root).expanduser()
    if candidate.is_absolute():
        return candidate
    return project_root / candidate


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON payload is not an object")
    return payload


def _iter_manifest_paths(project_root: Path, snapshots_runs_root: str) -> list[Path]:
    return sorted((project_root / snapshots_runs_root).glob("*/*/*/*/run.manifest.json"))


def _validate_manifests(project_root: Path, snapshots_runs_root: str) -> tuple[int, list[str]]:
    errors: list[str] = []
    manifests = _iter_manifest_paths(project_root, snapshots_runs_root)
    if not manifests:
        return 0, [f"missing replay manifests under {snapshots_runs_root}/**/run.manifest.json"]
    for path in manifests:
        rel = _rel_path(project_root, path)
        if path.stat().st_size <= 0:
            errors.append(f"empty replay manifest: {rel}")
            continue
        try:
            payload = _read_json_object(path)
        except Exception as exc:  # noqa: BLE001 - CLI validation reports the concrete path and parser failure.
            errors.append(f"invalid replay manifest JSON object: {rel}: {exc}")
            continue
        run_id = payload.get("run_id") or path.parent.name
        if not isinstance(run_id, str) or not run_id.strip():
            errors.append(f"replay manifest does not include or imply run_id: {rel}")
    return len(manifests), errors


def _ohlcv_files(project_root: Path, history_root: str) -> list[Path]:
    return sorted((project_root / history_root / "ohlcv" / "timeframe=1d").glob("symbol=*/year=*/month=*/*.parquet"))


def _inspect_ohlcv_history(project_root: Path, history_root: str) -> tuple[int, str | None, str | None, list[str]]:
    files = _ohlcv_files(project_root, history_root)
    if not files:
        return 0, None, None, [
            "missing OHLCV history under "
            f"{history_root}/ohlcv/timeframe=1d/symbol=*/year=*/month=*/*.parquet; run `{FETCH_OHLCV_COMMAND}` first"
        ]

    symbols = {part.name.removeprefix("symbol=") for path in files for part in path.parents if part.name.startswith("symbol=")}
    date_values: list[str] = []
    errors: list[str] = []
    for path in files:
        rel = _rel_path(project_root, path)
        try:
            df = pd.read_parquet(path)
        except Exception as exc:  # noqa: BLE001 - validation intentionally preserves unreadable parquet details.
            errors.append(f"unreadable OHLCV parquet: {rel}: {exc}")
            continue
        if "daily_bar_id" in df.columns:
            date_values.extend(str(value) for value in df["daily_bar_id"].dropna().tolist())
        elif "close_time_utc_ms" in df.columns:
            date_values.extend(pd.to_datetime(df["close_time_utc_ms"], unit="ms", utc=True).dt.strftime("%Y-%m-%d").dropna().tolist())
        elif "timestamp" in df.columns:
            date_values.extend(pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%d").dropna().tolist())
    date_values = sorted(value for value in date_values if value)
    return len(symbols), (date_values[0] if date_values else None), (date_values[-1] if date_values else None), errors


def validate_inputs(project_root: Path, *, snapshots_runs_root: str, history_root: str) -> InputValidation:
    missing_roots = [root for root in (snapshots_runs_root, history_root) if not (project_root / root).exists()]
    manifest_count, manifest_errors = _validate_manifests(project_root, snapshots_runs_root)
    ohlcv_symbol_count, ohlcv_min, ohlcv_max, ohlcv_errors = _inspect_ohlcv_history(project_root, history_root)
    return InputValidation(
        manifest_count=manifest_count,
        ohlcv_symbol_count=ohlcv_symbol_count,
        ohlcv_date_min=ohlcv_min,
        ohlcv_date_max=ohlcv_max,
        missing_input_roots=missing_roots,
        errors=manifest_errors + ohlcv_errors,
        warnings=[],
    )


def validate_outputs(project_root: Path, *, summary_output: Path, output_note: Path) -> OutputValidation:
    outputs = {key: rel for key, (rel, _kind) in OUTPUT_SPECS.items()}
    outputs["t30_run_summary_json"] = _rel_path(project_root, summary_output)
    outputs["t30_note_md"] = _rel_path(project_root, output_note)
    output_kinds = {key: kind for key, (_rel, kind) in OUTPUT_SPECS.items()}
    output_kinds["t30_run_summary_json"] = "json"
    output_kinds["t30_note_md"] = "text"

    missing: list[str] = []
    unreadable: list[str] = []
    readable: dict[str, bool] = {}
    for key, rel in outputs.items():
        path = project_root / rel
        if not path.exists():
            missing.append(rel)
            readable[key] = False
            continue
        if path.stat().st_size <= 0:
            unreadable.append(rel)
            readable[key] = False
            continue
        try:
            kind = output_kinds[key]
            if kind == "parquet":
                pd.read_parquet(path)
            elif kind == "json":
                json.loads(path.read_text(encoding="utf-8"))
            elif kind == "jsonl":
                with path.open("r", encoding="utf-8") as fh:
                    for line_no, line in enumerate(fh, start=1):
                        if line.strip():
                            json.loads(line)
            else:
                path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - output validator reports all unreadable outputs.
            unreadable.append(f"{rel}: {exc}")
            readable[key] = False
        else:
            readable[key] = True
    return OutputValidation(outputs=outputs, missing_outputs=missing, unreadable_outputs=unreadable, readable_outputs=readable)


def _load_event_counts(project_root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    path = project_root / "evaluation" / "replay" / "event_timeline.jsonl"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)
                event_type = row.get("event_type")
                if isinstance(event_type, str):
                    counts[event_type] += 1
    return dict(sorted(counts.items()))


def _metric_status_counts_by_horizon(project_root: Path) -> dict[str, dict[str, int]]:
    path = project_root / "evaluation" / "exports" / "signal_event_metrics.parquet"
    if not path.exists() or path.stat().st_size <= 0:
        return {}
    df = pd.read_parquet(path)
    result: dict[str, dict[str, int]] = {}
    for horizon in HORIZONS:
        column = f"metric_status_{horizon}d"
        if column not in df.columns:
            result[f"{horizon}d"] = {}
            continue
        counts = Counter(str(value) for value in df[column].dropna().tolist())
        result[f"{horizon}d"] = dict(sorted(counts.items()))
    return result


def _load_signal_metrics(project_root: Path) -> pd.DataFrame:
    path = project_root / "evaluation" / "exports" / "signal_event_metrics.parquet"
    if not path.exists() or path.stat().st_size <= 0:
        return pd.DataFrame()
    try:
        return pd.read_parquet(path)
    except Exception:  # noqa: BLE001 - note generation should degrade after validation captures unreadable files.
        return pd.DataFrame()


def _counts_rows(df: pd.DataFrame, columns: list[str]) -> list[list[Any]]:
    if df.empty or any(column not in df.columns for column in columns):
        return []
    grouped = df.groupby(columns, dropna=False).size().reset_index(name="rows")
    grouped = grouped.sort_values(columns + ["rows"], kind="mergesort")
    rows: list[list[Any]] = []
    for record in grouped.to_dict("records"):
        row: list[Any] = []
        for column in columns:
            value = record.get(column)
            row.append(None if pd.isna(value) else value)
        row.append(int(record["rows"]))
        rows.append(row)
    return rows


def _reference_price_coverage_rows(project_root: Path) -> list[list[Any]]:
    df = _load_signal_metrics(project_root)
    return _counts_rows(df, ["event_type", "reference_price_status", "reference_price_source"])


def _metric_status_by_event_type_rows(project_root: Path) -> list[list[Any]]:
    df = _load_signal_metrics(project_root)
    if df.empty or "event_type" not in df.columns:
        return []
    rows: list[list[Any]] = []
    for horizon in HORIZONS:
        column = f"metric_status_{horizon}d"
        if column not in df.columns:
            continue
        for event_type, status, count in _counts_rows(df, ["event_type", column]):
            rows.append([event_type, f"{horizon}d", status, count])
    return rows


def _segment_observation_blocks(project_root: Path) -> list[str]:
    fields = [
        "event_type",
        "execution_size_class",
        "is_tradeable_candidate",
        "is_operational_trade_candidate",
        "operational_tradeability_compat",
        "is_reduced_size_eligible",
        "candidate_excluded",
        "entry_location_status",
        "entry_action_hint",
        "depth_ratio_band",
    ]
    df = _load_signal_metrics(project_root)
    blocks: list[str] = []
    for field in fields:
        if df.empty or field not in df.columns:
            blocks.append(f"Segment field `{field}` is absent from signal_event_metrics.parquet and was not approximated.")
            continue
        rows = _counts_rows(df, [field])
        blocks.extend([f"### `{field}`", "", _markdown_table([field, "Rows"], rows), ""] )
    return blocks


def _row_count(path: Path) -> int | None:
    if not path.exists() or path.stat().st_size <= 0:
        return None
    try:
        if path.suffix == ".parquet":
            return int(len(pd.read_parquet(path)))
        if path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
    except Exception:  # noqa: BLE001 - row count is optional note metadata.
        return None
    return None


def _load_replay_diagnostics(project_root: Path) -> dict[str, Any]:
    path = project_root / "evaluation" / "replay" / "replay_diagnostics.json"
    if not path.exists() or path.stat().st_size <= 0:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def build_summary(
    *,
    project_root: Path,
    generated_at_utc: str,
    evaluation_start_date: str,
    primary_schema_min: str,
    history_root: str,
    input_validation: InputValidation,
    output_validation: OutputValidation,
) -> dict[str, Any]:
    replay_diag = _load_replay_diagnostics(project_root)
    return {
        "schema": "t30_run_summary_v1",
        "generated_at_utc": generated_at_utc,
        "project_root": project_root.as_posix(),
        "evaluation_start_date": evaluation_start_date,
        "primary_schema_min": primary_schema_min,
        "history_root": history_root,
        "outputs": output_validation.outputs,
        "input_counts": {
            "manifest_count": input_validation.manifest_count,
            "ohlcv_symbol_count": input_validation.ohlcv_symbol_count,
            "events_reconstructed": replay_diag.get("event_count"),
            "missing_diagnostics_run_count": replay_diag.get("missing_diagnostics_run_count"),
        },
        "event_counts_by_type": _load_event_counts(project_root),
        "metric_status_counts_by_horizon": _metric_status_counts_by_horizon(project_root),
        "validation": {
            "missing_input_roots": sorted(input_validation.missing_input_roots),
            "input_errors": sorted(input_validation.errors),
            "missing_outputs": sorted(output_validation.missing_outputs),
            "unreadable_outputs": sorted(output_validation.unreadable_outputs),
        },
    }


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join("" if value is None else str(value) for value in row) + " |")
    return "\n".join(lines)


def build_note(*, summary: dict[str, Any], input_validation: InputValidation, output_validation: OutputValidation) -> str:
    replay_diag = _load_replay_diagnostics(Path(summary["project_root"]))
    event_counts = summary.get("event_counts_by_type", {})
    metric_counts = summary.get("metric_status_counts_by_horizon", {})
    missing_diag = replay_diag.get("missing_diagnostics_run_count")
    manifest_count = input_validation.manifest_count
    events_reconstructed = replay_diag.get("event_count")

    output_rows = [[rel, "yes" if output_validation.readable_outputs.get(key) else "no"] for key, rel in sorted(output_validation.outputs.items())]
    event_rows = [[event_type, int(event_counts.get(event_type, 0))] for event_type in KEY_EVENT_TYPES]
    for event_type, count in sorted(event_counts.items()):
        if event_type not in KEY_EVENT_TYPES:
            event_rows.append([event_type, count])
    metric_rows: list[list[Any]] = []
    for horizon in [f"{h}d" for h in HORIZONS]:
        counts = metric_counts.get(horizon, {}) if isinstance(metric_counts, dict) else {}
        if counts:
            for status, count in sorted(counts.items()):
                metric_rows.append([horizon, status, count])
        else:
            metric_rows.append([horizon, "not_observed", 0])
    project_root = Path(summary["project_root"])
    reference_coverage_rows = _reference_price_coverage_rows(project_root)
    metric_by_event_rows = _metric_status_by_event_type_rows(project_root)
    segment_blocks = _segment_observation_blocks(project_root)

    limitations = [
        "Small sample size; this v1 note is not statistically meaningful as a final strategy assessment.",
        "5d/10d horizons may be dominated by `insufficient_future_data` for recent Shadow-Live events.",
        "Historical schema heterogeneity means pre-`ir1.5` rows are exploratory only.",
        "OHLCV history is limited to the candidate-scoped symbol set produced by T30-Pre-2.",
        "No automatic workflow integration was added; this script is manual only.",
        "No final performance conclusion and no threshold changes are recommended by this note alone.",
    ]
    if missing_diag:
        limitations.append(f"Missing diagnostics for {missing_diag} replay run(s); affected events cannot be reconstructed locally.")
    if replay_diag.get("missing_or_unknown_event_bar_id_count"):
        limitations.append("Some reconstructed events have missing or unknown event bar IDs.")
    if (summary.get("input_counts") or {}).get("events_reconstructed") == 0:
        limitations.append("No signal events were reconstructed from the locally available diagnostics.")

    prominent_warning = ""
    if missing_diag == manifest_count and manifest_count:
        prominent_warning = (
            "\n**Warning:** `missing_diagnostics_run_count` equals `manifest_count`; no signal events could be reconstructed "
            "because local diagnostics are missing. This is not a valid empty performance result.\n"
        )

    return "\n".join(
        [
            "# T30 Forward-Return Evaluation v1",
            "",
            "## Status",
            "",
            "Status: exploratory / validation note",
            "Type: exploratory / validation note",
            "Not a final performance conclusion",
            "No threshold changes recommended by this note alone",
            prominent_warning.rstrip(),
            "",
            "## Input data",
            "",
            f"- Project root: `{summary['project_root']}`",
            f"- Evaluation start date: `{summary['evaluation_start_date']}`",
            f"- Primary schema minimum: `{summary.get('primary_schema_min')}`",
            f"- Effective OHLCV history root: `{summary.get('history_root')}`",
            f"- Replay manifests found: `{manifest_count}`",
            f"- Events reconstructed: `{events_reconstructed}`",
            f"- Symbols with OHLCV history: `{input_validation.ohlcv_symbol_count}`",
            f"- OHLCV date coverage: `{input_validation.ohlcv_date_min}` to `{input_validation.ohlcv_date_max}`",
            f"- T30 execution timestamp: `{summary['generated_at_utc']}`",
            f"- Missing diagnostics runs: `{missing_diag}`",
            "",
            "## Evaluation outputs",
            "",
            _markdown_table(["Output", "Present/readable"], output_rows),
            "",
            "## Event coverage",
            "",
            _markdown_table(["Event type", "Rows"], event_rows),
            "",
            "## Forward-return metric coverage",
            "",
            _markdown_table(["Horizon", "Metric status", "Rows"], metric_rows),
            "",
            "## Reference Price Coverage",
            "",
            _markdown_table(["Event type", "Reference price status", "Reference price source", "Rows"], reference_coverage_rows),
            "",
            "## Metric Status by Event Type",
            "",
            _markdown_table(["Event type", "Horizon", "Metric status", "Rows"], metric_by_event_rows),
            "",
            "## Primary cohort: ir1.5+",
            "",
            "Primary cohort separation could not be derived from current T18 event rows without additional source metadata. No silent schema inference was applied.",
            "",
            "## Exploratory historical cohort: pre-ir1.5",
            "",
            "Pre-`ir1.5` rows, when present, are included only in overall technical event coverage. They are exploratory where native post-`ir1.5` operational fields are unavailable.",
            "",
            "## Segment observations",
            "",
            "\n".join(segment_blocks),
            "",
            "## Known limitations",
            "",
            "\n".join(f"- {item}" for item in limitations),
            "",
            "## Next recommended steps",
            "",
            "- Decide whether to run T30 v2 after more accumulated `ir1.5+` Shadow-Live runs.",
            "- Decide whether to add workflow automation later via a manual wrapper.",
            "- Decide whether T18 event rows should carry additional segmentation fields for T30 v2.",
            "- Decide whether to add a formal cohort framework after v1 findings.",
            "",
        ]
    )


def write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_note(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run T30 Forward-Return Evaluation v1 on local Shadow-Live artifacts.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--evaluation-start-date", default="2026-05-03")
    parser.add_argument("--primary-schema-min", default="ir1.5")
    parser.add_argument("--output-note", default="evaluation/notes/T30_forward_return_evaluation_v1.md")
    parser.add_argument("--summary-output", default="evaluation/replay/t30_run_summary.json")
    parser.add_argument("--history-root", default="snapshots/history")
    parser.add_argument("--snapshots-runs-root", default="snapshots/runs")
    parser.add_argument("--include-first-watch-metrics", dest="include_first_watch_metrics", action="store_true", default=True)
    parser.add_argument("--no-include-first-watch-metrics", dest="include_first_watch_metrics", action="store_false")
    parser.add_argument("--fail-on-missing-inputs", dest="fail_on_missing_inputs", action="store_true", default=True)
    parser.add_argument("--no-fail-on-missing-inputs", dest="fail_on_missing_inputs", action="store_false")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    output_note = (project_root / args.output_note).resolve() if not Path(args.output_note).is_absolute() else Path(args.output_note)
    summary_output = (project_root / args.summary_output).resolve() if not Path(args.summary_output).is_absolute() else Path(args.summary_output)
    effective_history_root = _effective_history_root(project_root, str(args.history_root))
    history_root_for_export = effective_history_root.as_posix()

    input_validation = validate_inputs(project_root, snapshots_runs_root=args.snapshots_runs_root, history_root=history_root_for_export)
    if input_validation.errors:
        for error in input_validation.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if args.fail_on_missing_inputs:
            return 2
        print("WARNING: continuing because --no-fail-on-missing-inputs is active", file=sys.stderr)

    config = {"independence_release": {"evaluation": {"include_first_watch_metrics": bool(args.include_first_watch_metrics)}}}
    try:
        run_evaluation_export(project_root=project_root, config=config, history_root=history_root_for_export)
    except Exception as exc:  # noqa: BLE001 - CLI must turn export failures into clear non-zero exits.
        print(f"ERROR: run_evaluation_export failed: {exc}", file=sys.stderr)
        return 3

    generated_at = _utc_now()
    pre_note_validation = validate_outputs(project_root, summary_output=summary_output, output_note=output_note)
    summary = build_summary(
        project_root=project_root,
        generated_at_utc=generated_at,
        evaluation_start_date=str(args.evaluation_start_date),
        primary_schema_min=str(args.primary_schema_min),
        history_root=history_root_for_export,
        input_validation=input_validation,
        output_validation=pre_note_validation,
    )
    try:
        write_summary(summary_output, summary)
    except Exception as exc:  # noqa: BLE001 - summary write failure is a required non-zero exit.
        print(f"ERROR: could not write T30 summary JSON: {exc}", file=sys.stderr)
        return 4

    note = build_note(summary=summary, input_validation=input_validation, output_validation=pre_note_validation)
    write_note(output_note, note)

    output_validation = validate_outputs(project_root, summary_output=summary_output, output_note=output_note)
    summary = build_summary(
        project_root=project_root,
        generated_at_utc=generated_at,
        evaluation_start_date=str(args.evaluation_start_date),
        primary_schema_min=str(args.primary_schema_min),
        history_root=history_root_for_export,
        input_validation=input_validation,
        output_validation=output_validation,
    )
    write_summary(summary_output, summary)
    write_note(output_note, build_note(summary=summary, input_validation=input_validation, output_validation=output_validation))

    if not output_validation.ok:
        for rel in output_validation.missing_outputs:
            print(f"ERROR: missing evaluation output: {rel}", file=sys.stderr)
        for rel in output_validation.unreadable_outputs:
            print(f"ERROR: unreadable evaluation output: {rel}", file=sys.stderr)
        return 5

    print(f"T30 evaluation complete: {_rel_path(project_root, summary_output)}")
    print(f"T30 note written: {_rel_path(project_root, output_note)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
