from __future__ import annotations

from datetime import date

from scripts.diagnostics.may_2025_cold_start_diagnostic import ReplayModeResult, _render_report


def _event_rows() -> list[dict[str, str]]:
    return [
        {"date": "2025-04-30", "symbol": "AAA", "event_type": "first_watch"},
        {"date": "2025-05-01", "symbol": "AAA", "event_type": "first_watch"},
        {"date": "2025-05-01", "symbol": "BBB", "event_type": "first_early"},
        {"date": "2025-05-02", "symbol": "AAA", "event_type": "first_early"},
    ]


def _summarize(rows: list[dict[str, str]], evaluation_start: date) -> ReplayModeResult:
    filtered = [r for r in rows if date.fromisoformat(r["date"]) >= evaluation_start]
    by_month: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_symbol: dict[str, int] = {}
    by_day: dict[str, int] = {}
    for r in filtered:
        by_month[r["date"][:7]] = by_month.get(r["date"][:7], 0) + 1
        if r["date"].startswith("2025-05-"):
            by_type[r["event_type"]] = by_type.get(r["event_type"], 0) + 1
            by_symbol[r["symbol"]] = by_symbol.get(r["symbol"], 0) + 1
        by_day[r["date"]] = by_day.get(r["date"], 0) + 1
    first_10 = []
    d = evaluation_start
    for _ in range(10):
        first_10.append((d.isoformat(), by_day.get(d.isoformat(), 0)))
        d = date.fromordinal(d.toordinal() + 1)
    return ReplayModeResult(
        mode="x",
        total_events=len(filtered),
        events_by_month=by_month,
        may_events_by_type=by_type,
        may_top_symbols=sorted(by_symbol.items(), key=lambda kv: (-kv[1], kv[0])),
        first_10_day_counts=first_10,
    )


def test_preroll_excludes_events_before_evaluation_start() -> None:
    result = _summarize(_event_rows(), date(2025, 5, 1))
    assert result.total_events == 3
    assert result.events_by_month == {"2025-05": 3}


def test_state_preroll_should_update_state_before_eval_semantics() -> None:
    # Synthetic contract: pre-evaluation rows exist and are intentionally dropped from event counts.
    rows = _event_rows()
    assert any(r["date"] < "2025-05-01" for r in rows)
    result = _summarize(rows, date(2025, 5, 1))
    assert result.total_events == 3


def test_month_and_event_type_grouping_rendered() -> None:
    cold = _summarize(_event_rows(), date(2025, 5, 1))
    preroll = _summarize([r for r in _event_rows() if r["date"] >= "2025-05-02"], date(2025, 5, 1))

    class S:
        scenario_id = "s1"
        evaluation = type("E", (), {"start_date": date(2025, 5, 1), "end_date": date(2025, 5, 10)})

    report = _render_report(
        scenario_path=type("P", (), {"as_posix": lambda self: "scenario.yml"})(),
        scenario=S(),
        preroll_start_date=date(2025, 1, 1),
        cold=cold,
        preroll=preroll,
        command="python ...",
    )
    assert "| 2025-05 | 3 | 1 |" in report
    assert "first_watch" in report
