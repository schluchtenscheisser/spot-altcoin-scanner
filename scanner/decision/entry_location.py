from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

ENTRY_LOCATION_STATUS_VALUES = {
    "fresh_entry",
    "acceptable_entry",
    "extended_entry",
    "chased_entry",
    "not_evaluable",
}

ENTRY_ACTION_HINT_VALUES = {
    "buy_now_candidate",
    "acceptable_if_strategy_allows",
    "wait_for_pullback",
    "avoid_chasing",
    "monitor_only",
    "not_evaluable",
}

_ENTRY_INPUT_KEYS = (
    "dist_to_ema20_4h_pct_abs",
    "close_vs_ema20_4h_pct",
    "bars_above_ema20_4h",
    "distance_to_last_structural_anchor_pct_abs",
    "bars_since_last_structural_break_4h",
    "distance_to_range_high_pct_abs",
)


@dataclass(frozen=True)
class EntryLocationResult:
    entry_location_status: str | None
    entry_action_hint: str | None
    entry_location_reason_primary: str | None
    entry_location_reason_codes: list[str]
    entry_location_inputs_used: dict[str, Any]
    range_high_proximity_warning: bool | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_location_status": self.entry_location_status,
            "entry_action_hint": self.entry_action_hint,
            "entry_location_reason_primary": self.entry_location_reason_primary,
            "entry_location_reason_codes": list(self.entry_location_reason_codes),
            "range_high_proximity_warning": self.range_high_proximity_warning,
            "entry_location_inputs_used": dict(self.entry_location_inputs_used),
        }


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _raw_number_or_none(value: Any) -> float | int | None:
    number = _finite_number(value)
    if number is None:
        return None
    return int(number) if isinstance(value, int) and not isinstance(value, bool) else number


def _threshold_block(cfg: Mapping[str, Any], entry_pattern: str | None) -> tuple[str, Mapping[str, Any]]:
    thresholds = cfg.get("thresholds", {})
    overrides = thresholds.get("pattern_overrides", {}) if isinstance(thresholds, Mapping) else {}
    if entry_pattern and isinstance(overrides, Mapping) and entry_pattern in overrides:
        override = overrides[entry_pattern]
        if isinstance(override, Mapping):
            return entry_pattern, override["dist_to_ema20_4h_pct_abs"]
    default = thresholds.get("default", {}) if isinstance(thresholds, Mapping) else {}
    return "default", default["dist_to_ema20_4h_pct_abs"]


def _classify_status(
    *,
    inputs: Any,
    entry_pattern: str | None,
    cfg: Mapping[str, Any],
) -> tuple[str | None, str | None, str, float | None]:
    if not cfg.get("enabled", True):
        return None, None, "default", None
    if inputs is None:
        return "not_evaluable", "missing_entry_location_inputs", "default", None
    if not isinstance(inputs, Mapping):
        return "not_evaluable", "invalid_entry_location_inputs_type", "default", None
    if "dist_to_ema20_4h_pct_abs" not in inputs or inputs.get("dist_to_ema20_4h_pct_abs") is None:
        return "not_evaluable", "missing_dist_to_ema20_4h_pct_abs", "default", None
    dist = _finite_number(inputs.get("dist_to_ema20_4h_pct_abs"))
    if dist is None:
        return "not_evaluable", "non_finite_dist_to_ema20_4h_pct_abs", "default", None
    if dist < 0:
        return "not_evaluable", "invalid_negative_abs_ema20_distance", "default", dist
    extreme = float(cfg["guards"]["extreme_value_not_evaluable_pct"])
    if dist > extreme:
        return "not_evaluable", "extreme_ema20_distance_outside_calibration_range", "default", dist

    threshold_source, block = _threshold_block(cfg, entry_pattern)
    fresh = float(block["fresh_max"])
    acceptable = float(block["acceptable_max"])
    extended = float(block["extended_max"])
    suffix = "continuation_breakout_override" if threshold_source == "continuation_breakout" else "default_ema20_distance"
    if dist <= fresh:
        return "fresh_entry", f"fresh_by_{suffix}", threshold_source, dist
    if dist <= acceptable:
        return "acceptable_entry", f"acceptable_by_{suffix}", threshold_source, dist
    if dist <= extended:
        return "extended_entry", f"extended_by_{suffix}", threshold_source, dist
    return "chased_entry", f"chased_by_{suffix}", threshold_source, dist


def _range_high_warning(inputs: Any, cfg: Mapping[str, Any]) -> bool | None:
    auxiliary = cfg.get("auxiliary", {})
    range_cfg = auxiliary.get("distance_to_range_high_pct_abs", {}) if isinstance(auxiliary, Mapping) else {}
    if not isinstance(range_cfg, Mapping) or range_cfg.get("enabled", True) is not True:
        return None
    if not isinstance(inputs, Mapping):
        return None
    value = _finite_number(inputs.get("distance_to_range_high_pct_abs"))
    if value is None:
        return None
    return value <= float(range_cfg["proximity_warning_max_pct"])


def _resolve_action_hint(
    *,
    status: str | None,
    decision_bucket: Any,
    candidate_excluded: Any,
    is_tradeable_candidate: Any,
    execution_size_class: Any,
) -> tuple[str | None, str | None]:
    if status is None:
        return None, None
    if status == "not_evaluable":
        return "not_evaluable", "not_evaluable_action_hint"
    if status == "chased_entry":
        return "avoid_chasing", "chased_entry_avoid_chasing"
    if candidate_excluded is True:
        return "monitor_only", "candidate_excluded_monitor_only"
    if is_tradeable_candidate is not True:
        return "monitor_only", "not_tradeable_monitor_only"
    if decision_bucket == "early_candidates":
        return "monitor_only", "early_bucket_monitor_only"

    if decision_bucket == "confirmed_candidates":
        if status == "fresh_entry":
            if execution_size_class == "full":
                return "buy_now_candidate", "fresh_full_buy_now_candidate"
            if execution_size_class in {"reduced_75", "reduced_50", "reduced_25"}:
                return "acceptable_if_strategy_allows", "fresh_reduced_size_acceptable"
        if status == "acceptable_entry":
            if execution_size_class == "full":
                return "acceptable_if_strategy_allows", "acceptable_full_strategy_allows"
            if execution_size_class in {"reduced_75", "reduced_50"}:
                return "acceptable_if_strategy_allows", "acceptable_reduced_size_strategy_allows"
            if execution_size_class == "reduced_25":
                return "wait_for_pullback", "acceptable_reduced_25_wait_for_pullback"
        if status == "extended_entry":
            return "wait_for_pullback", "extended_wait_for_pullback"
    return "monitor_only", "unhandled_action_hint_combination"


def evaluate_entry_location(record: Mapping[str, Any], cfg: Mapping[str, Any]) -> EntryLocationResult:
    inputs = record.get("entry_location_inputs")
    pattern_block = record.get("pattern") if isinstance(record.get("pattern"), Mapping) else {}
    decision_block = record.get("decision") if isinstance(record.get("decision"), Mapping) else {}
    entry_pattern = pattern_block.get("entry_pattern")

    status, primary, threshold_source, _dist = _classify_status(
        inputs=inputs,
        entry_pattern=str(entry_pattern) if entry_pattern is not None else None,
        cfg=cfg,
    )
    warning = _range_high_warning(inputs, cfg)

    inputs_used: dict[str, Any] = {}
    source = inputs if isinstance(inputs, Mapping) else {}
    for key in _ENTRY_INPUT_KEYS:
        inputs_used[key] = _raw_number_or_none(source.get(key))
    inputs_used["entry_pattern"] = entry_pattern if entry_pattern is None else str(entry_pattern)
    inputs_used["threshold_source"] = threshold_source
    inputs_used["range_high_proximity_warning"] = warning

    if not cfg.get("enabled", True):
        return EntryLocationResult(None, None, None, [], inputs_used, warning)

    hint, hint_reason = _resolve_action_hint(
        status=status,
        decision_bucket=decision_block.get("decision_bucket"),
        candidate_excluded=record.get("candidate_excluded"),
        is_tradeable_candidate=record.get("is_tradeable_candidate"),
        execution_size_class=record.get("execution_size_class"),
    )
    reason_codes: list[str] = []

    def _append_reason(reason: str | None) -> None:
        if reason is not None and reason not in reason_codes:
            reason_codes.append(reason)

    _append_reason(primary)
    if warning is True:
        _append_reason("range_high_proximity_warning")
    _append_reason(hint_reason)

    return EntryLocationResult(status, hint, primary, reason_codes, inputs_used, warning)


def attach_entry_location(record: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(record)
    out["entry_location"] = evaluate_entry_location(out, cfg).to_dict()
    return out


def _priority_sort_key(record: Mapping[str, Any]) -> tuple[int, float, str]:
    decision = record.get("decision") if isinstance(record.get("decision"), Mapping) else {}
    raw = record.get("priority_score", decision.get("priority_score"))
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
        return (1, 0.0, str(record.get("symbol", "")))
    return (0, -float(raw), str(record.get("symbol", "")))


def _segment_item(record: Mapping[str, Any]) -> dict[str, Any]:
    decision = record.get("decision") if isinstance(record.get("decision"), Mapping) else {}
    entry_location = record.get("entry_location") if isinstance(record.get("entry_location"), Mapping) else {}
    priority = decision.get("priority_score")
    if isinstance(priority, bool) or not isinstance(priority, (int, float)) or not math.isfinite(float(priority)):
        priority_score = None
    else:
        priority_score = float(priority)
    return {
        "symbol": str(record.get("symbol")),
        "decision_bucket": decision.get("decision_bucket"),
        "priority_score": priority_score,
        "entry_location_status": entry_location.get("entry_location_status"),
        "entry_action_hint": entry_location.get("entry_action_hint"),
        "range_high_proximity_warning": entry_location.get("range_high_proximity_warning"),
        "execution_size_class": record.get("execution_size_class"),
        "is_tradeable_candidate": record.get("is_tradeable_candidate"),
        "candidate_excluded": record.get("candidate_excluded"),
    }


def build_entry_location_report_segments(records: list[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    segments: dict[str, list[dict[str, Any]]] = {
        "buy_now_candidates": [],
        "wait_pullback_candidates": [],
        "early_watch_candidates": [],
        "good_location_but_not_tradeable": [],
        "tradeable_but_extended": [],
    }
    for record in records:
        entry_location = record.get("entry_location") if isinstance(record.get("entry_location"), Mapping) else {}
        decision = record.get("decision") if isinstance(record.get("decision"), Mapping) else {}
        status = entry_location.get("entry_location_status")
        hint = entry_location.get("entry_action_hint")
        bucket = decision.get("decision_bucket")
        excluded = record.get("candidate_excluded") is True
        tradeable = record.get("is_tradeable_candidate") is True
        item = _segment_item(record)
        if hint == "buy_now_candidate":
            segments["buy_now_candidates"].append(item)
        if hint == "wait_for_pullback":
            segments["wait_pullback_candidates"].append(item)
        if bucket == "early_candidates" and status in {"fresh_entry", "acceptable_entry"} and hint == "monitor_only":
            segments["early_watch_candidates"].append(item)
        if status in {"fresh_entry", "acceptable_entry"} and not tradeable and not excluded:
            segments["good_location_but_not_tradeable"].append(item)
        if tradeable and not excluded and status in {"extended_entry", "chased_entry"}:
            segments["tradeable_but_extended"].append(item)
    for values in segments.values():
        values.sort(key=_priority_sort_key)
    return segments
