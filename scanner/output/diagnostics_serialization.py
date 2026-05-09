from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any, Mapping

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.decision.models import DecisionBundle
from scanner.entry.models import EntryPatternBundle
from scanner.features.models import FeatureBundle
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state.models import InvalidationCycleBundle, PersistedStateMachineContext, StateMachineBundle

logger = logging.getLogger(__name__)

_ENTRY_LOCATION_FIELDS = (
    "close_vs_ema20_4h_pct",
    "bars_above_ema20_4h",
    "dist_to_ema20_4h_pct_abs",
    "distance_to_last_structural_anchor_pct_abs",
    "distance_to_range_high_pct_abs",
    "bars_since_last_structural_break_4h",
)


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_value(v) for v in value]
    return value


def _dataclass_attr_map(obj: Any, *, field_names: tuple[str, ...]) -> dict[str, Any]:
    return {name: _json_value(getattr(obj, name, None)) for name in field_names}


def _raw_4h_ok_value(feature_bundle: FeatureBundle, field: str) -> float | int | None:
    raw_4h = getattr(feature_bundle, "raw_4h", None)
    if not feature_bundle.data_4h_available or raw_4h is None:
        return None
    if not hasattr(raw_4h, field):
        return None
    value = getattr(raw_4h, field)
    status = getattr(raw_4h, f"{field}_status", None)
    if value is None or status != "ok":
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)):
        logger.warning(
            "non-finite entry-location feature serialized as null",
            extra={"symbol": feature_bundle.symbol, "field": field},
        )
        return None
    if field in {"bars_above_ema20_4h", "bars_since_last_structural_break_4h"}:
        return int(value)
    return float(value)


def serialize_entry_location_inputs(feature_bundle: FeatureBundle) -> dict[str, float | int | None]:
    if not feature_bundle.data_4h_available:
        # T_EL1b is diagnostics-only and must not synthesize daily fallbacks for 4h entry-location inputs.
        return {field: None for field in _ENTRY_LOCATION_FIELDS}
    return {field: _raw_4h_ok_value(feature_bundle, field) for field in _ENTRY_LOCATION_FIELDS}


def serialize_axes_block(t1: Tier1AxisBundle, t2: Tier2AxisBundle) -> dict[str, Any]:
    t1_fields = (
        "trend_strength",
        "trend_strength_not_evaluable",
        "trend_strength_reduced_resolution",
        "trend_strength_effective_weight_ratio",
        "reclaim_progress",
        "reclaim_progress_not_evaluable",
        "reclaim_progress_reduced_resolution",
        "reclaim_progress_effective_weight_ratio",
        "compression_strength",
        "compression_strength_not_evaluable",
        "compression_strength_reduced_resolution",
        "compression_strength_effective_weight_ratio",
        "expansion_progress_structural",
        "expansion_progress_structural_not_evaluable",
        "expansion_progress_structural_reduced_resolution",
        "expansion_progress_structural_effective_weight_ratio",
        "volume_regime_shift",
        "volume_regime_shift_not_evaluable",
        "volume_regime_shift_reduced_resolution",
        "volume_regime_shift_effective_weight_ratio",
        "freshness_distance_structural",
        "freshness_distance_structural_not_evaluable",
        "freshness_distance_structural_reduced_resolution",
        "freshness_distance_structural_effective_weight_ratio",
    )
    t2_fields = (
        "base_integrity_simplified",
        "base_integrity_simplified_not_evaluable",
        "base_integrity_simplified_reduced_resolution",
        "base_integrity_simplified_effective_weight_ratio",
        "pullback_quality_simplified",
        "pullback_quality_simplified_not_evaluable",
        "pullback_quality_simplified_reduced_resolution",
        "pullback_quality_simplified_effective_weight_ratio",
        "reacceleration_strength_simplified",
        "reacceleration_strength_simplified_not_evaluable",
        "reacceleration_strength_simplified_reduced_resolution",
        "reacceleration_strength_simplified_effective_weight_ratio",
    )
    out = _dataclass_attr_map(t1, field_names=t1_fields)
    out.update(_dataclass_attr_map(t2, field_names=t2_fields))
    return out


def serialize_phase_block(phase: PhaseInterpretationBundle) -> dict[str, Any]:
    fields = (
        "market_phase",
        "market_phase_confidence",
        "market_phase_runner_up",
        "market_phase_gap",
        "market_phase_blended",
        "phase_score_pressure_build",
        "phase_score_trend_resume",
        "phase_score_transition_reclaim",
        "phase_floor_margin_pressure_build",
        "phase_floor_margin_trend_resume",
        "phase_floor_margin_transition_reclaim",
        "phase_floor_failed_pressure_build",
        "phase_floor_failed_trend_resume",
        "phase_floor_failed_transition_reclaim",
        "phase_eval_status_pressure_build",
        "phase_eval_status_trend_resume",
        "phase_eval_status_transition_reclaim",
        "freshness_distance_structural",
        "freshness_distance_structural_not_evaluable",
        "freshness_distance_structural_reduced_resolution",
    )
    return _dataclass_attr_map(phase, field_names=fields)


def serialize_invalidation_block(inv: InvalidationCycleBundle) -> dict[str, Any]:
    fields = (
        "structural_invalidation",
        "structural_invalidation_reason",
        "timing_invalidation",
        "timing_invalidation_reason",
    )
    return _dataclass_attr_map(inv, field_names=fields)


def serialize_cycle_block(
    inv: InvalidationCycleBundle,
    state_bundle: StateMachineBundle | None = None,
    persisted: PersistedStateMachineContext | None = None,
) -> dict[str, Any]:
    out = _dataclass_attr_map(
        inv,
        field_names=(
            "resolved_setup_cycle_id",
            "new_cycle_detected",
            "cycle_reason_code",
            "phase_floor_recovered_since_cycle_end",
            "expansion_reset_condition_met",
            "reclaim_reset_condition_met",
        ),
    )
    previous_setup_cycle_id = None
    bars_since_cycle_end = None
    cycle_end_bar_index = None
    cycle_end_timestamp = None
    if state_bundle is not None and state_bundle.persistence_patch is not None:
        patch = state_bundle.persistence_patch
        previous_setup_cycle_id = patch.previous_setup_cycle_id
        bars_since_cycle_end = patch.bars_since_cycle_end
        cycle_end_bar_index = patch.cycle_end_bar_index
        cycle_end_timestamp = patch.cycle_end_timestamp
    elif persisted is not None:
        previous_setup_cycle_id = persisted.previous_setup_cycle_id
        bars_since_cycle_end = persisted.bars_since_cycle_end
        cycle_end_bar_index = persisted.cycle_end_bar_index
        cycle_end_timestamp = persisted.cycle_end_timestamp
    out["previous_setup_cycle_id"] = previous_setup_cycle_id
    out["bars_since_cycle_end"] = bars_since_cycle_end
    out["cycle_end_bar_index"] = cycle_end_bar_index
    out["cycle_end_timestamp"] = cycle_end_timestamp
    return out


def serialize_state_block(
    state_bundle: StateMachineBundle,
    persisted: PersistedStateMachineContext | None = None,
) -> dict[str, Any]:
    patch = state_bundle.persistence_patch
    out: dict[str, Any] = {
        "state_machine_state": _json_value(state_bundle.state_machine_state),
        "state_confidence": state_bundle.state_confidence,
        "state_transition_reason": _json_value(state_bundle.state_transition_reason),
        "setup_cycle_id": patch.setup_cycle_id if patch is not None else None,
        "data_resolution_class": _json_value(state_bundle.data_resolution_class),
        "freshness_distance_state_early": state_bundle.freshness.freshness_distance_state_early,
        "freshness_distance_state_confirmed": state_bundle.freshness.freshness_distance_state_confirmed,
        "distance_from_ideal_entry_after_early": state_bundle.freshness.distance_from_ideal_entry_after_early,
        "distance_from_ideal_entry_after_confirmed": state_bundle.freshness.distance_from_ideal_entry_after_confirmed,
        "bars_since_state_entered": None,
        "bars_since_early_entered": None,
        "bars_since_confirmed_entered": None,
        "close_at_early_entry_bar": None,
        "close_at_confirmed_entry_bar": None,
        "disposition_admitted": state_bundle.disposition.admitted,
        "disposition_reason": _json_value(state_bundle.disposition.disposition_reason),
    }
    if patch is not None:
        out["bars_since_state_entered"] = patch.bars_since_state_entered
        out["bars_since_early_entered"] = patch.bars_since_early_entered
        out["bars_since_confirmed_entered"] = patch.bars_since_confirmed_entered
        out["close_at_early_entry_bar"] = patch.close_at_early_entry_bar
        out["close_at_confirmed_entry_bar"] = patch.close_at_confirmed_entry_bar
    elif persisted is not None:
        out["bars_since_state_entered"] = persisted.bars_since_state_entered
        out["bars_since_early_entered"] = persisted.bars_since_early_entered
        out["bars_since_confirmed_entered"] = persisted.bars_since_confirmed_entered
        out["close_at_early_entry_bar"] = persisted.close_at_early_entry_bar
        out["close_at_confirmed_entry_bar"] = persisted.close_at_confirmed_entry_bar
    return out


def serialize_pattern_block(entry: EntryPatternBundle | None) -> dict[str, Any]:
    if entry is None or not hasattr(entry, "entry_pattern"):
        return {}
    candidate_scores: dict[str, float] = {}
    raw_candidates = getattr(entry, "candidate_pattern_scores_within_phase", {})
    if not isinstance(raw_candidates, dict):
        raw_candidates = {}
    for raw_key, raw_value in raw_candidates.items():
        key = str(_json_value(raw_key))
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)) or not math.isfinite(float(raw_value)):
            continue
        candidate_scores[key] = float(raw_value)
    return {
        "entry_pattern": _json_value(entry.entry_pattern),
        "entry_pattern_score": getattr(entry, "entry_pattern_score", None),
        "candidate_pattern_scores_within_phase": candidate_scores,
    }


def serialize_decision_block(decision: DecisionBundle | None) -> dict[str, Any]:
    if decision is None:
        return {}
    return {
        "decision_bucket": _json_value(getattr(decision, "decision_bucket", None)),
        "priority_score": getattr(decision, "priority_score", None),
        "bucket_reason_primary": _json_value(getattr(decision, "bucket_reason_primary", None)),
        "bucket_reason_secondary": _json_value(getattr(decision, "bucket_reason_secondary", None)),
        "execution_required": getattr(decision, "execution_required", None),
        "execution_pending": getattr(decision, "execution_pending", None),
        "entry_pattern": _json_value(getattr(decision, "entry_pattern", None)),
        "entry_pattern_score": getattr(decision, "entry_pattern_score", None),
    }


def serialize_reasons_block(
    inv: InvalidationCycleBundle | None,
    state_bundle: StateMachineBundle | None,
    decision: DecisionBundle | None,
    execution_diagnostics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reasons: dict[str, Any] = {}
    if decision is not None:
        if getattr(decision, "bucket_reason_primary", None) is not None:
            reasons["bucket_reason_primary"] = _json_value(getattr(decision, "bucket_reason_primary", None))
        if getattr(decision, "bucket_reason_secondary", None) is not None:
            reasons["bucket_reason_secondary"] = _json_value(getattr(decision, "bucket_reason_secondary", None))
    if state_bundle is not None and state_bundle.state_transition_reason is not None:
        reasons["state_transition_reason"] = _json_value(state_bundle.state_transition_reason)
    if inv is not None:
        if inv.structural_invalidation_reason is not None:
            reasons["structural_invalidation_reason"] = inv.structural_invalidation_reason
        if inv.timing_invalidation_reason is not None:
            reasons["timing_invalidation_reason"] = inv.timing_invalidation_reason
        if inv.cycle_reason_code is not None:
            reasons["cycle_reason_code"] = inv.cycle_reason_code
    if execution_diagnostics is not None and execution_diagnostics.get("execution_reason_raw") is not None:
        reasons["execution_reason_raw"] = execution_diagnostics.get("execution_reason_raw")
    return reasons
