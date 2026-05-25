from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from scanner.evaluation.historical_replay.bar_loader import HistoricalBarLoader
from scanner.evaluation.historical_replay.production_adapter import HistoricalProductionAdapter
from scanner.evaluation.historical_replay.replay_runner import get_current_daily_bar, has_current_day_4h_coverage
from scanner.evaluation.historical_replay.scenario import ReplayScenario, load_scenario
from scanner.evaluation.historical_replay.state_store import ReplayStateStore


@dataclass(frozen=True)
class ReplayModeResult:
    mode: str
    total_events: int
    events_by_month: dict[str, int]
    may_events_by_type: dict[str, int]
    may_top_symbols: list[tuple[str, int]]
    first_10_day_counts: list[tuple[str, int]]


def _collect_events(
    scenario: ReplayScenario,
    state_start_date: date,
    evaluation_start_date: date,
    mode: str,
    output_dir: Path,
) -> ReplayModeResult:
    loader = HistoricalBarLoader(scenario.history_dataset_ref)
    adapter = HistoricalProductionAdapter()
    state = ReplayStateStore(output_dir / f"{mode}_state.sqlite")
    symbols = sorted([p.name.replace("symbol=", "") for p in (Path(scenario.history_dataset_ref) / "timeframe=1d").iterdir() if p.is_dir()])

    event_rows: list[dict[str, Any]] = []
    current = state_start_date
    while current <= scenario.evaluation.end_date:
        as_of = datetime.combine(current, time(23, 59, 59), tzinfo=timezone.utc) + timedelta(seconds=scenario.settlement_delay_seconds)
        bar_id = current.isoformat()
        for sym in symbols:
            s = state.get(sym)
            d1 = loader.closed_bars_as_of(sym, "1d", as_of).bars
            h4 = loader.closed_bars_as_of(sym, "4h", as_of).bars

            if len(d1) < scenario.warm_up_1d_bars or len(h4) < scenario.warm_up_4h_bars:
                continue

            current_d1 = get_current_daily_bar(d1, bar_id)
            if current_d1 is None or not has_current_day_4h_coverage(h4, bar_id):
                state.upsert(s)
                continue

            adapter_out = adapter(
                symbol=sym,
                as_of_daily_bar_id=bar_id,
                closed_1d_bars=d1,
                closed_4h_bars=h4,
                persisted_state=dict(s),
                scanner_config={"ref": scenario.scanner_config_ref, "hash": scenario.scanner_config_hash},
            )
            s["last_evaluable_replay_date"] = bar_id
            for k, v in adapter_out.updated_state_patch.items():
                s[k] = v
            s["symbol"] = sym
            state.upsert(s)

            if current < evaluation_start_date:
                continue
            for event_type in adapter_out.transition_event_types:
                if event_type.startswith("first_"):
                    event_rows.append({"date": bar_id, "symbol": sym, "event_type": event_type})
        current += timedelta(days=1)

    by_month = Counter(r["date"][:7] for r in event_rows)
    may_rows = [r for r in event_rows if r["date"].startswith("2025-05-")]
    may_by_type = Counter(r["event_type"] for r in may_rows)
    may_by_symbol = Counter(r["symbol"] for r in may_rows)

    first_10 = []
    d = evaluation_start_date
    for _ in range(10):
        day = d.isoformat()
        first_10.append((day, sum(1 for r in event_rows if r["date"] == day)))
        d += timedelta(days=1)

    return ReplayModeResult(
        mode=mode,
        total_events=len(event_rows),
        events_by_month=dict(sorted(by_month.items())),
        may_events_by_type=dict(sorted(may_by_type.items())),
        may_top_symbols=may_by_symbol.most_common(15),
        first_10_day_counts=first_10,
    )


def _render_report(
    scenario_path: Path,
    scenario: ReplayScenario,
    preroll_start_date: date,
    cold: ReplayModeResult,
    preroll: ReplayModeResult,
    command: str,
) -> str:
    lines = [
        "# May 2025 Cold-Start Diagnostic",
        "",
        f"- Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Scenario: `{scenario.scenario_id}` ({scenario_path.as_posix()})",
        f"- Evaluation window: `{scenario.evaluation.start_date}`..`{scenario.evaluation.end_date}`",
        f"- Preroll start date: `{preroll_start_date}`",
        "",
        "## Command",
        "",
        "```bash",
        command,
        "```",
        "",
        "## Monthly event counts",
        "",
        "| Month | cold_start | state_preroll |",
        "|---|---:|---:|",
    ]
    months = sorted(set(cold.events_by_month) | set(preroll.events_by_month))
    for m in months:
        lines.append(f"| {m} | {cold.events_by_month.get(m, 0)} | {preroll.events_by_month.get(m, 0)} |")

    lines += [
        "",
        "## May 2025 event_type counts",
        "",
        "| event_type | cold_start | state_preroll |",
        "|---|---:|---:|",
    ]
    types = sorted(set(cold.may_events_by_type) | set(preroll.may_events_by_type))
    for t in types:
        lines.append(f"| {t} | {cold.may_events_by_type.get(t, 0)} | {preroll.may_events_by_type.get(t, 0)} |")

    lines += ["", "## Top May symbols (by event count)", "", "### cold_start", ""]
    for sym, count in cold.may_top_symbols:
        lines.append(f"- {sym}: {count}")
    lines += ["", "### state_preroll", ""]
    for sym, count in preroll.may_top_symbols:
        lines.append(f"- {sym}: {count}")

    lines += ["", "## First 10 replay days event counts", "", "| Day | cold_start | state_preroll |", "|---|---:|---:|"]
    pre_map = dict(preroll.first_10_day_counts)
    for day, cold_count in cold.first_10_day_counts:
        lines.append(f"| {day} | {cold_count} | {pre_map.get(day, 0)} |")

    may_cold = cold.events_by_month.get("2025-05", 0)
    may_pre = preroll.events_by_month.get("2025-05", 0)
    drop = may_cold - may_pre
    pct = (drop / may_cold * 100.0) if may_cold else 0.0
    lines += [
        "",
        "## Conclusion",
        "",
        (
            f"May 2025 events change from {may_cold} (cold_start) to {may_pre} (state_preroll), "
            f"a reduction of {drop} events ({pct:.1f}%). "
            "A large drop supports the cold-start bias hypothesis; a small drop suggests plausible market behavior."
        ),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="Diagnose May 2025 event spike under cold-start vs state preroll")
    p.add_argument("--scenario", required=True)
    p.add_argument("--preroll-start-date", default="2025-01-01")
    p.add_argument("--report-out", default="docs/legacy/reports/2026-05-25__may_2025_cold_start_diagnostic.md")
    args = p.parse_args()

    scenario_path = Path(args.scenario)
    scenario = load_scenario(scenario_path)
    preroll_start_date = date.fromisoformat(args.preroll_start_date)
    if preroll_start_date > scenario.evaluation.start_date:
        raise SystemExit("preroll_start_date must be on or before evaluation_start_date")

    output_dir = Path("tmp/diagnostics/may_2025_cold_start")
    output_dir.mkdir(parents=True, exist_ok=True)

    cold = _collect_events(scenario, scenario.evaluation.start_date, scenario.evaluation.start_date, "cold_start", output_dir)
    preroll = _collect_events(scenario, preroll_start_date, scenario.evaluation.start_date, "state_preroll", output_dir)

    cmd = f"python scripts/diagnostics/may_2025_cold_start_diagnostic.py --scenario {scenario_path.as_posix()} --preroll-start-date {preroll_start_date.isoformat()} --report-out {args.report_out}"
    report = _render_report(scenario_path, scenario, preroll_start_date, cold, preroll, cmd)
    out = Path(args.report_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"wrote report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
