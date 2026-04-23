from __future__ import annotations

import dataclasses

import pytest

from scanner.config import ScannerConfig
from scanner.decision import (
    DecisionBucket,
    DiscardedReason,
    ExecutionInputContract,
    LateMonitorReason,
    RankedDecision,
    WatchlistReason,
    assign_bucket,
    compute_priority_score,
    map_execution_grade,
    rank_coins,
)
from scanner.entry.models import EntryPatternBundle
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state.models import StateEvaluationDisposition, StateFreshnessBundle, StateMachineBundle


def _cfg(raw: dict | None = None) -> ScannerConfig:
    return ScannerConfig(raw=raw or {})


def _phase(**overrides):
    base = {
        "symbol": "TEST",
        "daily_bar_id": "2026-01-01",
        "intraday_bar_id": 2,
        "data_4h_available": True,
        "market_phase": "trend_resume",
        "market_phase_confidence": 80.0,
        "market_phase_runner_up": "pressure_build",
        "market_phase_gap": 10.0,
        "market_phase_blended": False,
        "phase_score_pressure_build": 60.0,
        "phase_score_trend_resume": 80.0,
        "phase_score_transition_reclaim": 50.0,
        "phase_floor_margin_pressure_build": 1.0,
        "phase_floor_margin_trend_resume": 2.0,
        "phase_floor_margin_transition_reclaim": 0.0,
        "phase_floor_failed_pressure_build": False,
        "phase_floor_failed_trend_resume": False,
        "phase_floor_failed_transition_reclaim": False,
        "phase_eval_status_pressure_build": "score_computed",
        "phase_eval_status_trend_resume": "score_computed",
        "phase_eval_status_transition_reclaim": "score_computed",
        "freshness_distance_structural": 20.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": False,
    }
    base.update(overrides)
    return PhaseInterpretationBundle(**base)


def _state(state_machine_state: str | None = "watch", state_confidence: float | None = 70.0):
    return StateMachineBundle(
        symbol="TEST",
        daily_bar_id="2026-01-01",
        intraday_bar_id=2,
        data_4h_available=True,
        disposition=StateEvaluationDisposition(admitted=True, disposition_reason=None),
        state_machine_state=state_machine_state,
        state_confidence=state_confidence,
        state_transition_reason="STATE_HOLD" if state_machine_state else None,
        data_resolution_class="full_1d_4h" if state_machine_state else None,
        freshness=StateFreshnessBundle(None, None, None, None),
        persistence_patch=None,
    )


def _entry(pattern: str = "breakout", score: float = 60.0):
    cands = {} if pattern == "none" else {pattern: score}
    return EntryPatternBundle(entry_pattern=pattern, entry_pattern_score=score if pattern != "none" else 0.0, candidate_pattern_scores_within_phase=cands)


def test_bucket_assignment_paths():
    d1 = assign_bucket(_phase(market_phase="none"), _state("watch", 70.0), _entry(), _cfg())
    assert d1.decision_bucket == DecisionBucket.DISCARDED
    assert d1.bucket_reason_primary == DiscardedReason.PHASE_NONE

    d2 = assign_bucket(_phase(), _state("rejected", 70.0), _entry(), _cfg())
    assert d2.decision_bucket == DecisionBucket.DISCARDED
    assert d2.bucket_reason_primary == DiscardedReason.STATE_REJECTED

    d3 = assign_bucket(_phase(), _state("confirmed_ready", 70.0), _entry("breakout", 60), _cfg())
    assert d3.decision_bucket == DecisionBucket.CONFIRMED_CANDIDATES
    assert d3.execution_pending is True

    d4 = assign_bucket(
        _phase(), _state("confirmed_ready", 70.0), _entry("breakout", 60), _cfg(), ExecutionInputContract(execution_status="direct_ok")
    )
    assert d4.decision_bucket == DecisionBucket.CONFIRMED_CANDIDATES
    assert d4.execution_pending is False

    d5 = assign_bucket(
        _phase(), _state("confirmed_ready", 70.0), _entry("breakout", 60), _cfg(), ExecutionInputContract(execution_status="fail")
    )
    assert d5.decision_bucket == DecisionBucket.LATE_MONITOR
    assert d5.bucket_reason_primary == LateMonitorReason.EXECUTION_FAILED_MONITOR


def test_gated_candidate_paths_keep_rankable_score_when_phase_confidence_missing_or_non_finite():
    d_none = assign_bucket(_phase(market_phase_confidence=None), _state("confirmed_ready", 70.0), _entry("breakout", 60.0), _cfg())
    assert d_none.decision_bucket == DecisionBucket.CONFIRMED_CANDIDATES
    assert isinstance(d_none.priority_score, float)
    assert d_none.priority_score == pytest.approx(43.0)

    d_nan = assign_bucket(_phase(market_phase_confidence=float("nan")), _state("early_ready", 70.0), _entry("breakout", 60.0), _cfg())
    assert d_nan.decision_bucket == DecisionBucket.EARLY_CANDIDATES
    assert isinstance(d_nan.priority_score, float)
    assert d_nan.priority_score == pytest.approx(43.0)


def test_none_pattern_special_cases_and_rule10_floor_policy():
    out_confirmed = assign_bucket(_phase(), _state("confirmed_ready", None), _entry("none"), _cfg())
    assert out_confirmed.decision_bucket == DecisionBucket.LATE_MONITOR
    assert out_confirmed.bucket_reason_primary == LateMonitorReason.CONFIRMED_PATTERN_UNRESOLVED
    assert out_confirmed.priority_score >= 0

    out_early = assign_bucket(_phase(), _state("early_ready", None), _entry("none"), _cfg())
    assert out_early.decision_bucket == DecisionBucket.WATCHLIST
    assert out_early.bucket_reason_primary == WatchlistReason.WATCH_EARLY_NO_PATTERN
    assert out_early.priority_score >= 0

    out_watch_none = assign_bucket(_phase(market_phase_confidence=None), _state("watch", None), _entry("none"), _cfg())
    assert out_watch_none.decision_bucket == DecisionBucket.DISCARDED
    assert out_watch_none.bucket_reason_primary == DiscardedReason.INSUFFICIENT_CONFIDENCE
    assert out_watch_none.priority_score == pytest.approx(0.0)


def test_late_and_chased_require_non_none_phase():
    late = assign_bucket(_phase(market_phase="trend_resume"), _state("late", 50.0), _entry("none"), _cfg())
    assert late.decision_bucket == DecisionBucket.LATE_MONITOR

    late_none = assign_bucket(_phase(market_phase="none"), _state("late", 50.0), _entry("none"), _cfg())
    assert late_none.decision_bucket == DecisionBucket.DISCARDED
    assert late_none.bucket_reason_primary == DiscardedReason.PHASE_NONE


def test_execution_fail_demotions_use_non_gated_floor_scoring():
    confirmed_fail = assign_bucket(
        _phase(market_phase_confidence=None),
        _state("confirmed_ready", None),
        _entry("breakout", 60.0),
        _cfg(),
        ExecutionInputContract(execution_status="fail"),
    )
    assert confirmed_fail.decision_bucket == DecisionBucket.LATE_MONITOR
    assert confirmed_fail.bucket_reason_primary == LateMonitorReason.EXECUTION_FAILED_MONITOR
    assert isinstance(confirmed_fail.priority_score, float)
    assert confirmed_fail.priority_score == pytest.approx(12.0)

    early_fail = assign_bucket(
        _phase(market_phase_confidence=float("inf")),
        _state("early_ready", None),
        _entry("breakout", 60.0),
        _cfg(),
        ExecutionInputContract(execution_status="fail"),
    )
    assert early_fail.decision_bucket == DecisionBucket.DISCARDED
    assert early_fail.bucket_reason_primary == DiscardedReason.EXECUTION_FAILED
    assert isinstance(early_fail.priority_score, float)
    assert early_fail.priority_score == pytest.approx(12.0)


def test_priority_score_and_mapping():
    assert compute_priority_score(market_phase_confidence=80, state_confidence=70, entry_pattern_score=60) == pytest.approx(71.0)
    assert compute_priority_score(
        market_phase_confidence=80,
        state_confidence=70,
        entry_pattern_score=60,
        execution_status="direct_ok",
    ) == pytest.approx(75.5)
    assert map_execution_grade("direct_ok") == 100.0
    assert map_execution_grade("tranche_ok") == 75.0
    assert map_execution_grade("marginal") == 40.0
    assert map_execution_grade("fail") == 0.0
    with pytest.raises(ValueError):
        map_execution_grade("unknown")
    with pytest.raises(TypeError):
        compute_priority_score(market_phase_confidence=80, state_confidence=None, entry_pattern_score=60)


def test_ranking_order_and_determinism():
    cfg = _cfg()
    decisions = [
        RankedDecision("BBB", assign_bucket(_phase(), _state("watch", 60), _entry("none"), cfg), 60.0, 80.0),
        RankedDecision("AAA", assign_bucket(_phase(), _state("watch", 60), _entry("none"), cfg), 60.0, 80.0),
        RankedDecision("CCC", assign_bucket(_phase(), _state("confirmed_ready", 70), _entry("breakout", 70), cfg), 70.0, 80.0),
    ]
    ranked1 = rank_coins(decisions, cfg)
    ranked2 = rank_coins(decisions, cfg)
    assert [r.symbol for r in ranked1] == ["CCC", "AAA", "BBB"]
    assert [r.rank_within_bucket for r in ranked1 if r.decision.decision_bucket == DecisionBucket.WATCHLIST] == [1, 2]
    assert dataclasses.asdict(ranked1[0]) == dataclasses.asdict(ranked2[0])


def test_status_separation_and_config():
    structural = (_phase(), _state("early_ready", 65.0), _entry("breakout", 60.0), _cfg())
    without_execution = assign_bucket(*structural)
    with_fail = assign_bucket(*structural, execution_contract=ExecutionInputContract(execution_status="fail"))
    assert without_execution.execution_pending is True
    assert without_execution.decision_bucket == DecisionBucket.EARLY_CANDIDATES
    assert with_fail.execution_pending is False
    assert with_fail.decision_bucket == DecisionBucket.DISCARDED

    assert _cfg().bucket["watchlist"]["min_state_confidence"] == 50.0
    assert _cfg(raw={"bucket": {"early": {"min_state_confidence": 70}}}).bucket["early"]["min_state_confidence"] == 70.0
    assert _cfg().priority["early_without_pattern_penalty"] == 15.0
    with pytest.raises(ValueError):
        _cfg(raw={"bucket": {"confirmed": {"min_state_confidence": -1}}}).bucket
    with pytest.raises(ValueError):
        _cfg(raw={"priority": {"early_without_pattern_penalty": float("nan")}}).priority
