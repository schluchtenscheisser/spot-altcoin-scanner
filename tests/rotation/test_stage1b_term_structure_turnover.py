import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.rotation.btc_relative_edge_probe import ProbeError
from scripts.rotation.stage1b_term_structure_turnover import (
    ASSESSMENTS,
    cost_break_even,
    persistence,
    run,
    survivorship,
    validate_machine_output,
)


def write_hist(root: Path, symbol: str, closes: dict[str, float]):
    d = root / "timeframe=1d" / f"symbol={symbol}" / "year=2026" / "month=01"
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"daily_bar_id": list(closes.keys()), "close": list(closes.values())}).to_parquet(d / "part.parquet")


def fixture(tmp_path, include_age=True):
    stage1 = tmp_path / "stage1"
    stage1.mkdir()
    pd.DataFrame({"analysis_role": ["primary"], "horizon": [10]}).to_parquet(stage1 / "segment_relative_returns.parquet")
    (stage1 / "btc_relative_edge_probe.json").write_text(json.dumps({"cost_context": {"cost_log_low": 0.003, "cost_log_high": 0.008}}))
    (stage1 / "probe_manifest.json").write_text(json.dumps({"run_id": "r"}))
    hist = tmp_path / "hist"
    dates = pd.date_range("2026-01-01", periods=35, freq="D").strftime("%Y-%m-%d")
    write_hist(hist, "BTCUSDT", {d: 100 + i for i, d in enumerate(dates)})
    write_hist(hist, "AAAUSDT", {d: 10 + i * 1.2 for i, d in enumerate(dates)})
    write_hist(hist, "BBBUSDT", {d: 20 + i * 0.3 for i, d in enumerate(dates)})
    write_hist(hist, "CCCUSDT", {d: 30 + i * 0.1 for i, d in enumerate(dates)})
    df = pd.DataFrame({
        "symbol": ["AAAUSDT", "BBBUSDT", "CCCUSDT", "AAA", "BBBUSDT", "CCCUSDT"],
        "as_of_daily_bar_id": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-08", "2026-01-08", "2026-01-09"],
        "event_type": ["first_confirmed_ready", "first_watch", "first_confirmed_ready", "first_confirmed_ready", "first_watch", "first_confirmed_ready"],
        "historical_signal_bucket": ["confirmed ready", "watch", "confirmed ready", "confirmed ready", "watch", "confirmed ready"],
        "btc_regime_label": ["bull", "bull", "bear", "bull", "bull", "bear"],
        "quote_volume_bucket": ["high", "low", "low", "high", "low", "low"],
    })
    if include_age:
        df["available_history_days_1d_at_event"] = [100, 200, 30, 107, 207, 37]
    events = tmp_path / "events.parquet"
    df.to_parquet(events)
    return stage1, hist, events


def test_missing_required_stage1_file_fails_fast(tmp_path):
    stage1, hist, events = fixture(tmp_path)
    (stage1 / "btc_relative_edge_probe.json").unlink()
    with pytest.raises(ProbeError, match="missing required Stage-1"):
        run(["--stage1-root", str(stage1), "--events", str(events), "--history-root", str(hist), "--output-root", str(tmp_path / "out")])


def test_cost_context_absent_fails_fast(tmp_path):
    stage1, hist, events = fixture(tmp_path)
    (stage1 / "btc_relative_edge_probe.json").write_text(json.dumps({}))
    with pytest.raises(ProbeError, match="cost_context"):
        run(["--stage1-root", str(stage1), "--events", str(events), "--history-root", str(hist), "--output-root", str(tmp_path / "out")])


def test_missing_optional_age_field_graceful_skip_in_run(tmp_path):
    stage1, hist, events = fixture(tmp_path, include_age=False)
    out = tmp_path / "out"
    run(["--stage1-root", str(stage1), "--events", str(events), "--history-root", str(hist), "--output-root", str(out), "--n-bootstrap", "5", "--min-count", "1"])
    summary = json.loads((out / "2026-05-24T21-27-31Z" / "term_structure_turnover_diagnostics.json").read_text())
    assert summary["survivorship"]["survivorship_age_proxy_available"] is True


def test_age_proxy_unavailable_reports_false_without_crash(tmp_path):
    stage1, hist, events = fixture(tmp_path, include_age=False)
    empty_hist = tmp_path / "empty_hist"; (empty_hist / "timeframe=1d").mkdir(parents=True)
    scope = pd.DataFrame({"history_symbol": ["AAAUSDT"], "as_of_daily_bar_id": ["2026-01-01"], "historical_signal_bucket": ["confirmed ready"], "relative_log_return_10d": [0.1]})
    table, meta = survivorship(scope, "historical_signal_bucket", "confirmed ready", [10], 5, empty_hist)
    assert meta["survivorship_age_proxy_available"] is False
    assert not table.empty


def test_cost_formulas_and_implied_rotations_exact():
    scope = pd.DataFrame({"tier": ["confirmed", "confirmed"], "relative_log_return_5d": [0.02, 0.04]})
    out = cost_break_even(scope, "tier", "confirmed", [5], 0.003, 0.008).iloc[0]
    assert out["gross_edge_log"] == pytest.approx(0.03)
    assert out["one_roundtrip_net_low"] == pytest.approx(0.027)
    assert out["one_roundtrip_net_high"] == pytest.approx(0.022)
    assert out["implied_max_rotations_per_year"] == pytest.approx(365 / 5)
    assert out["annualized_cost_drag_low"] == pytest.approx((365 / 5) * 0.003)


def test_forbidden_machine_readable_key_fails_but_caveat_phrase_allowed():
    with pytest.raises(ProbeError):
        validate_machine_output({"stage2_green_light": False})
    validate_machine_output({"caveat": "not a realized trade count"})


def test_no_pnl_equity_artifact_and_assessment_enum_and_roles(tmp_path):
    stage1, hist, events = fixture(tmp_path)
    out = tmp_path / "out"
    run(["--stage1-root", str(stage1), "--events", str(events), "--history-root", str(hist), "--output-root", str(out), "--n-bootstrap", "5", "--min-count", "1"])
    od = out / "2026-05-24T21-27-31Z"
    files = [p.name.lower() for p in od.iterdir()]
    assert not any("pnl" in f or "equity" in f for f in files)
    summary = json.loads((od / "term_structure_turnover_diagnostics.json").read_text())
    assert summary["diagnostic_assessment"] in ASSESSMENTS
    for parquet in od.glob("*.parquet"):
        df = pd.read_parquet(parquet)
        if "analysis_role" in df:
            assert set(df["analysis_role"]) == {"diagnostic"}


def test_deterministic_output_except_created_timestamp(tmp_path):
    stage1, hist, events = fixture(tmp_path)
    out1, out2 = tmp_path / "o1", tmp_path / "o2"
    args = ["--stage1-root", str(stage1), "--events", str(events), "--history-root", str(hist), "--n-bootstrap", "5", "--min-count", "1"]
    run(args + ["--output-root", str(out1)])
    run(args + ["--output-root", str(out2)])
    a = json.loads((out1 / "2026-05-24T21-27-31Z" / "term_structure_turnover_diagnostics.json").read_text())
    b = json.loads((out2 / "2026-05-24T21-27-31Z" / "term_structure_turnover_diagnostics.json").read_text())
    a.pop("created_at_utc"); b.pop("created_at_utc")
    assert a == b


def test_persistence_sign_transition_rates_fixture():
    scope = pd.DataFrame({"tier": ["confirmed"] * 4, "relative_log_return_1d": [1, 1, -1, -1], "relative_log_return_3d": [1, -1, 1, -1], "relative_log_return_10d": [1, -1, 1, -1], "relative_log_return_20d": [-1, -1, 1, 1]})
    out = persistence(scope, "tier", "confirmed")
    row = out[(out["analysis_name"] == "persistence_sign_transition") & (out["transition"] == "1d_to_10d") & (out["source_sign"] == "positive") & (out["destination_sign"] == "positive")].iloc[0]
    assert row["rate"] == pytest.approx(0.5)


def test_tail_and_youngest_edges_recomputed_not_subtracted(tmp_path):
    hist = tmp_path / "hist"
    write_hist(hist, "AAAUSDT", {"2026-01-01": 1, "2026-01-11": 2})
    scope = pd.DataFrame({"history_symbol": ["AAAUSDT", "BBBUSDT", "CCCUSDT"], "as_of_daily_bar_id": ["2026-01-01"] * 3, "tier": ["confirmed"] * 3, "available_history_days_1d_at_event": [1, 50, 100], "relative_log_return_10d": [10.0, 2.0, 4.0]})
    table, meta = survivorship(scope, "tier", "confirmed", [10], 1, hist)
    tail = table[(table["analysis_name"] == "survivorship_recomputed_edge") & (table["segment_key"] == "exclude_top_1_contributors")].iloc[0]
    assert tail["median_relative_log_return"] == pytest.approx(3.0)
    young = table[(table["analysis_name"] == "survivorship_recomputed_edge") & (table["segment_key"] == "exclude_youngest_cohort")].iloc[0]
    assert young["event_count"] == 2
