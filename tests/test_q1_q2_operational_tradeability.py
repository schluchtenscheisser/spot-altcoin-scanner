from __future__ import annotations

import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scanner.decision.entry_location import attach_entry_location, build_entry_location_report_segments, evaluate_entry_location
from scanner.decision.models import DecisionBucket, RankedDecision
from scanner.config import resolve_independence_entry_location_config
from scanner.output.report_builder import ReportBuilder
from scanner.output.schema import SCHEMA_VERSION, validate_diagnostics_record
from scanner.runners.daily import _build_execution_aware_report_payload, _build_ticket23_report_payload
from scanner.universe.classification import classify_symbol


def _diag(
    symbol: str,
    *,
    bucket: str = "confirmed_candidates",
    universe_category: str = "classic_crypto",
    candidate_excluded: bool = False,
    is_tradeable_candidate: bool | None = True,
    execution_size_class: str = "full",
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": "r1",
        "scan_mode": "daily",
        "symbol": symbol,
        "as_of_utc": "2026-04-01T00:00:00Z",
        "daily_bar_id": "2026-04-01",
        "intraday_bar_id": None,
        "data_4h_available": True,
        "entry_location_inputs": {
            "close_vs_ema20_4h_pct": 1.0,
            "bars_above_ema20_4h": 3,
            "dist_to_ema20_4h_pct_abs": 1.0,
            "distance_to_last_structural_anchor_pct_abs": 1.0,
            "distance_to_range_high_pct_abs": 2.0,
            "bars_since_last_structural_break_4h": 1,
        },
        "axes": {},
        "phase": {"market_phase": "markup", "market_phase_confidence": 1.0},
        "invalidation": {},
        "cycle": {"resolved_setup_cycle_id": "cycle-1"},
        "state": {"state_machine_state": "confirmed", "setup_cycle_id": "cycle-1"},
        "pattern": {"entry_pattern": "ema_reclaim"},
        "decision": {"decision_bucket": bucket, "priority_score": 10.0},
        "reasons": {},
        "universe": {
            "universe_category": universe_category,
            "universe_category_confidence": "high",
            "universe_category_reason": "test",
            "candidate_excluded": candidate_excluded,
            "candidate_exclusion_reason": universe_category if candidate_excluded else None,
        },
        "candidate_excluded": candidate_excluded,
        "execution_attempted": False,
        "execution_status_raw": None,
        "execution_reason_raw": None,
        "execution_pass": None,
        "execution_grade_t16": None,
        "execution_fetch_duration_ms": 1,
        "execution_size_class": execution_size_class,
        "is_reduced_size_eligible": is_tradeable_candidate is True,
        "is_tradeable_candidate": is_tradeable_candidate,
    }


def _ranked(symbol: str, bucket: str) -> RankedDecision:
    return RankedDecision(
        symbol=symbol,
        decision=SimpleNamespace(decision_bucket=DecisionBucket(bucket), priority_score=10.0),
        state_confidence=1.0,
        market_phase_confidence=1.0,
    )


@pytest.mark.parametrize(
    ("tradeable", "excluded", "expected"),
    [
        (True, False, True),
        (True, True, False),
        (False, False, False),
        (None, False, False),
    ],
)
def test_operational_tradeability_formula_and_top_level_bool(tradeable, excluded, expected) -> None:
    record = _diag("AAAUSDT", candidate_excluded=excluded, is_tradeable_candidate=tradeable)

    out = validate_diagnostics_record(record)

    assert out["schema_version"] == "ir1.5"
    assert out["is_operational_trade_candidate"] is expected
    assert isinstance(out["is_operational_trade_candidate"], bool)
    assert "is_operational_trade_candidate" not in out["universe"]


@pytest.mark.parametrize(
    ("symbol", "category"),
    [
        ("USDPUSDT", "stable_or_cash_proxy"),
        ("EURUSDT", "fiat_proxy"),
        ("WUSDCUSDT", "wrapped_cash"),
    ],
)
def test_stable_cash_categories_are_classified_as_candidate_excluded(symbol: str, category: str) -> None:
    classification = classify_symbol(symbol)

    assert classification.universe_category == category
    assert classification.candidate_excluded is True
    assert classification.candidate_exclusion_reason == category


def test_candidate_excluded_symbols_are_removed_from_candidate_lists_and_latest_files(tmp_path: Path) -> None:
    builder = ReportBuilder(project_root=tmp_path)
    records = [
        _diag("USDPUSDT", universe_category="stable_or_cash_proxy", candidate_excluded=True),
        _diag("AAAUSDT", candidate_excluded=False),
        _diag("WATCHUSDT", bucket="watchlist", candidate_excluded=False),
    ]

    report = builder.write_run_report(
        run_id="run-q1q2",
        scan_mode="daily",
        as_of_utc="2026-04-01T00:00:00Z",
        daily_bar_id="2026-04-01",
        intraday_bar_id=None,
        symbol_lists={
            "confirmed_candidates": ["USDPUSDT", "AAAUSDT"],
            "early_candidates": ["USDPUSDT"],
            "watchlist": ["USDPUSDT", "WATCHUSDT"],
            "late_monitor": [],
        },
        manifest_path="snapshots/runs/2026/04/01/run-q1q2/run.manifest.json",
        diagnostics_records=records,
        counts_by_bucket={
            "confirmed_candidates": 2,
            "early_candidates": 1,
            "watchlist": 2,
            "late_monitor": 0,
            "discarded": 0,
        },
    )

    assert report["symbol_lists"]["confirmed_candidates"] == ["AAAUSDT"]
    assert report["symbol_lists"]["early_candidates"] == []
    assert report["symbol_lists"]["watchlist"] == ["WATCHUSDT"]
    assert report["counts_by_bucket"]["confirmed_candidates"] == 1
    assert json.loads((tmp_path / "reports/index/latest_confirmed_candidates.json").read_text()) == ["AAAUSDT"]
    assert json.loads((tmp_path / "reports/index/latest_watchlist.json").read_text()) == ["WATCHUSDT"]

    diag_path = tmp_path / report["diagnostics_path"]
    lines = gzip.decompress(diag_path.read_bytes()).decode("utf-8").splitlines()
    by_symbol = {json.loads(line)["symbol"]: json.loads(line) for line in lines}
    assert by_symbol["USDPUSDT"]["candidate_excluded"] is True
    assert by_symbol["USDPUSDT"]["is_operational_trade_candidate"] is False


def test_report_payloads_add_operational_counts_without_reinterpreting_tradeable_counts() -> None:
    diagnostics = [
        validate_diagnostics_record(_diag("AAAUSDT", candidate_excluded=False, is_tradeable_candidate=True)),
        validate_diagnostics_record(_diag("USDPUSDT", universe_category="stable_or_cash_proxy", candidate_excluded=True, is_tradeable_candidate=True)),
    ]
    ranked = [_ranked("AAAUSDT", "confirmed_candidates")]

    ticket23 = _build_ticket23_report_payload(ranked=ranked, diagnostics=diagnostics)
    execution = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)

    assert ticket23["universe_classification"]["candidate_excluded_symbol_count"] == 1
    assert ticket23["candidate_segments"]["excluded_candidate_buckets"]["confirmed_candidates"][0]["symbol"] == "USDPUSDT"
    assert execution["execution_aware_summary"]["operational_trade_candidate_count"] == 1
    assert execution["reduced_size_policy_summary"]["confirmed_tradeable_candidates"] == 1
    assert execution["reduced_size_policy_summary"]["confirmed_operational_trade_candidate_count"] == 1


def _entry_cfg() -> dict:
    return resolve_independence_entry_location_config({})


def test_good_location_but_not_tradeable_regression_excludes_candidate_excluded_symbols() -> None:
    excluded = validate_diagnostics_record(
        _diag("USDPUSDT", universe_category="stable_or_cash_proxy", candidate_excluded=True, is_tradeable_candidate=True)
    )
    good_not_tradeable = validate_diagnostics_record(_diag("GOODUSDT", candidate_excluded=False, is_tradeable_candidate=False))
    records = [attach_entry_location(record, _entry_cfg()) for record in [excluded, good_not_tradeable]]

    segments = build_entry_location_report_segments(records)

    assert [item["symbol"] for item in segments["good_location_but_not_tradeable"]] == ["GOODUSDT"]
    assert all(item["symbol"] != "USDPUSDT" for item in segments["good_location_but_not_tradeable"])


def test_tel2_rule3_still_checks_candidate_excluded_before_tradeability_rule() -> None:
    record = _diag("USDPUSDT", candidate_excluded=True, is_tradeable_candidate=False)
    result = evaluate_entry_location(record, _entry_cfg())

    assert result.entry_action_hint == "monitor_only"
    assert "candidate_excluded_monitor_only" in result.entry_location_reason_codes
    assert "not_tradeable_monitor_only" not in result.entry_location_reason_codes


def test_tel2_chased_edge_case_still_wins_before_candidate_excluded_rule() -> None:
    record = _diag("USDPUSDT", candidate_excluded=True, is_tradeable_candidate=True)
    record["entry_location_inputs"]["dist_to_ema20_4h_pct_abs"] = 9.0

    result = evaluate_entry_location(record, _entry_cfg())

    assert result.entry_action_hint == "avoid_chasing"
    assert "chased_entry_avoid_chasing" in result.entry_location_reason_codes
