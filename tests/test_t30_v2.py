from __future__ import annotations

import gzip
import json
import math
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from scripts.analyze_t30_v2_segment_selection import (
    analyze,
    apply_slippage,
    attach_forward_returns,
    basket_filters,
    classify_run,
    discover_runs,
    extract_record,
    is_daily_diagnostics_path,
    segments,
    summarize,
    validate_thresholds,
    write_json,
)


def rec(**overrides):
    row = {
        "symbol": "AAAUSDT",
        "schema_version": "ir1.5",
        "is_operational_trade_candidate": True,
        "candidate_excluded": False,
        "execution_size_class": "full",
        "execution_status_raw": "direct_ok",
        "estimated_slippage_bps": 31,
        "decision": {"decision_bucket": "confirmed_candidates", "priority_score": 70},
        "entry_location": {"entry_location_status": "fresh_entry", "entry_action_hint": "acceptable_if_strategy_allows"},
    }
    row.update(overrides)
    return row


def diagnostic_bytes(records):
    return gzip.compress("\n".join(json.dumps(row) for row in records).encode())


def report_bytes(records):
    return json.dumps({"counts_by_bucket": {"confirmed_candidates": len(records), "early_candidates": 0}}).encode()


def add_zip_run(archive: zipfile.ZipFile, run_id: str, records, *, mode: str = "daily"):
    run_dir = f"reports/runs/2026/06/01/{mode}-{run_id}"
    archive.writestr(f"{run_dir}/symbol_diagnostics.jsonl.gz", diagnostic_bytes(records))
    archive.writestr(f"{run_dir}/report.json", report_bytes(records))


def write_zip(path: Path, run_id: str, records):
    with zipfile.ZipFile(path, "w") as archive:
        add_zip_run(archive, run_id, records)


def write_event_export(root: Path, rows):
    path = root / "evaluation/exports/signal_event_metrics.parquet"
    path.parent.mkdir(parents=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def event(cycle: int, one_day_return: float):
    return {
        "symbol": "AAAUSDT",
        "setup_cycle_id": cycle,
        "event_type": "first_confirmed_ready",
        "reference_price_status": "ok",
        "forward_return_1d_pct": one_day_return,
        "forward_return_3d_pct": one_day_return + 1,
        "forward_return_7d_pct": one_day_return + 2,
    }


def test_schema_detection_semantic_and_fallback():
    assert classify_run([rec(schema_version="ir1.5")])[0]
    assert classify_run([rec(schema_version="ir1.4")])[:2] == (False, "schema_pre_ir1.5")
    assert classify_run([rec(schema_version="ir1.6")])[0]
    assert classify_run([{"schema_version": "ir1.6"}])[:2] == (False, "missing_required_fields")
    assert classify_run([{"is_operational_trade_candidate": False}])[:2] == (True, "operational_field_fallback")
    assert not classify_run([{}])[0]


def test_nested_entry_location_and_setup_cycle_extraction():
    row = extract_record(rec(entry_location_status="WRONG", state={"setup_cycle_id": 4}), "daily-r")
    assert row["entry_location_status"] == "fresh_entry"
    assert row["setup_cycle_id"] == 4
    row = extract_record(rec(entry_location=None, entry_location_status="WRONG", cycle={"resolved_setup_cycle_id": 5}), "daily-r")
    assert (row["entry_location_status"], row["entry_action_hint"]) == ("not_evaluable", "not_evaluable")
    assert row["setup_cycle_id"] == 5


def test_tranche_visibility_segment_and_baskets():
    tranche = extract_record(rec(execution_status_raw="tranche_ok"), "daily-r")
    assert not segments()["S1"](tranche) and not segments()["S2"](tranche) and not segments()["S7"](tranche)
    assert segments()["S8"](tranche)
    assert all(match(tranche) for match in basket_filters({"A": 65, "B": 60, "C": 55}).values())


def test_s6_excludes_buy_now_but_s9_includes_and_basket_c_outside_segments():
    buy_now = extract_record(rec(decision={"decision_bucket": "early_candidates", "priority_score": 70}, entry_location={"entry_location_status": "fresh_entry", "entry_action_hint": "buy_now_candidate"}), "daily-r")
    assert not segments()["S6"](buy_now) and segments()["S9"](buy_now)
    outside = extract_record(rec(decision={"decision_bucket": "early_candidates", "priority_score": 70}, execution_size_class="reduced_50"), "daily-r")
    assert basket_filters({"A": 65, "B": 60, "C": 55})["C"](outside)
    assert not any(segments()[segment](outside) for segment in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"])


def test_slippage_validation_json_finiteness_and_adjusted_summary_exclusion(tmp_path):
    assert apply_slippage(10, 31) == pytest.approx((9.69, True))
    assert apply_slippage(10, None) == (None, False)
    rows = [{"run_id": "daily-a", "return_1d_pct": 10, "return_1d_adj_pct": 9.69}, {"run_id": "daily-a", "return_1d_pct": 20, "return_1d_adj_pct": None}]
    summary = summarize(rows, ["daily-a"])
    assert summary["return_1d"]["mean_return_pct"] == 15
    assert summary["return_1d"]["mean_return_adj_pct"] == pytest.approx(9.69)
    with pytest.raises(ValueError):
        validate_thresholds({"A": math.nan})
    with pytest.raises(ValueError):
        validate_thresholds({"A": 101})
    path = tmp_path / "x.json"
    write_json(path, {"bad": [math.nan, math.inf, -math.inf]})
    assert json.loads(path.read_text()) == {"bad": [None, None, None]}


def test_daily_only_zip_discovery_and_twenty_run_gate(tmp_path):
    zip_dir = tmp_path / ".local_data/shadow_live_runs"
    zip_dir.mkdir(parents=True)
    with zipfile.ZipFile(zip_dir / "mixed.zip", "w") as archive:
        add_zip_run(archive, "accepted", [rec()], mode="daily")
        add_zip_run(archive, "rejected", [rec()], mode="intraday")
    discovered = discover_runs(tmp_path, Path(".local_data/shadow_live_runs"))
    assert [row["run_id"] for row in discovered] == ["daily-accepted"]
    with pytest.raises(RuntimeError, match="T30-v2 requires at least 20 ir1.5\\+ runs. Found: 1"):
        analyze(tmp_path, input_zip_dir=Path(".local_data/shadow_live_runs"))


def test_daily_only_filesystem_discovery(tmp_path):
    for run_id in ("daily-accepted", "intraday-rejected", "other-rejected"):
        run_dir = tmp_path / "reports/runs/2026/06/01" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "symbol_diagnostics.jsonl.gz").write_bytes(diagnostic_bytes([rec()]))
        (run_dir / "report.json").write_bytes(report_bytes([rec()]))
    assert is_daily_diagnostics_path("reports/runs/2026/06/01/daily-accepted/symbol_diagnostics.jsonl.gz")
    assert [row["run_id"] for row in discover_runs(tmp_path, None)] == ["daily-accepted"]


def test_forward_returns_match_symbol_cycle_and_event_type(tmp_path):
    write_event_export(tmp_path, [event(1, 10), event(2, 20)])
    rows = [extract_record(rec(state={"setup_cycle_id": cycle}), "daily-r") for cycle in (1, 2)]
    missing, warnings = attach_forward_returns(tmp_path, rows)
    assert not missing and not warnings
    assert [row["return_1d_pct"] for row in rows] == [10, 20]
    assert [row["return_1d_adj_pct"] for row in rows] == pytest.approx([9.69, 19.69])


def test_missing_setup_cycle_does_not_select_latest_multi_cycle_event(tmp_path):
    write_event_export(tmp_path, [event(1, 10), event(2, 20)])
    row = extract_record(rec(), "daily-r")
    missing, warnings = attach_forward_returns(tmp_path, [row])
    assert missing == {"AAAUSDT"}
    assert row["forward_return_derivable"] is False
    assert row["return_1d_pct"] is None
    assert warnings == [{"run_id": "daily-r", "symbol": "AAAUSDT", "warning": "missing_setup_cycle_id_for_multi_cycle_match"}]


def test_synthetic_zip_missing_ohlcv_outputs(tmp_path):
    zip_dir = tmp_path / ".local_data/shadow_live_runs"
    zip_dir.mkdir(parents=True)
    for number in range(20):
        write_zip(zip_dir / f"r{number}.zip", f"r{number}", [rec(symbol=f"A{number}USDT", execution_status_raw="tranche_ok")])
    artifacts = analyze(tmp_path, input_zip_dir=Path(".local_data/shadow_live_runs"))
    assert artifacts["segment_summary.json"]["S8"]["n_total_records"] == 20
    assert artifacts["basket_summary.json"]["applied_config"]["PRIORITY_THRESHOLD_A"] == 65
    assert artifacts["basket_summary.json"]["baskets"]["A"]["execution_status_raw_distribution"] == {"tranche_ok": 20}
    assert artifacts["mfe_mae_summary.json"] == {"mfe_mae_available": False}
    assert "OHLCV history absent or incomplete" in (tmp_path / "reports/aux/t30_v2/decision_support.md").read_text()
    assert "OHLCV history absent or incomplete" in (tmp_path / "reports/aux/t30_v2/run_coverage.md").read_text()


def test_single_cycle_missing_id_fallback_is_explicit_and_missing_slippage_stays_raw_only(tmp_path):
    write_event_export(tmp_path, [event(1, 10)])
    row = extract_record(rec(estimated_slippage_bps=None), "daily-r")
    missing, warnings = attach_forward_returns(tmp_path, [row])
    assert not missing
    assert row["forward_return_derivable"] is True
    assert row["return_1d_pct"] == 10
    assert row["return_1d_adj_pct"] is None
    assert row["slippage_adjustment_available"] is False
    assert warnings == [{"run_id": "daily-r", "symbol": "AAAUSDT", "warning": "missing_setup_cycle_id_single_cycle_fallback"}]
