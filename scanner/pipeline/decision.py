"""Decision layer for canonical Phase-1 outcomes."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

ALLOWED_TRADEABILITY = {"DIRECT_OK", "TRANCHE_OK", "MARGINAL"}
ENTER_TRADEABILITY = {"DIRECT_OK", "TRANCHE_OK"}
REASON_ORDER = [
    "tradeability_fail",
    "tradeability_marginal",
    "risk_flag_blocked",
    "stop_distance_too_wide",
    "risk_reward_unattractive",
    "risk_data_insufficient",
    "insufficient_edge",
    "btc_regime_caution",
    "entry_not_confirmed",
    "breakout_not_confirmed",
    "retest_not_reclaimed",
    "rebound_not_confirmed",
]


def apply_decision_layer(
    candidates: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    btc_regime: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Attach deterministic decision state and reasons to fully evaluated candidates."""

    cfg = _load_decision_config(config)
    is_risk_off = str((btc_regime or {}).get("state", "")).upper() == "RISK_OFF"
    enter_threshold = cfg["min_score_for_enter"] + (cfg["risk_off_enter_boost"] if is_risk_off else 0)

    out: List[Dict[str, Any]] = []
    for row in candidates:
        entry = dict(row)

        tradeability_class = _to_optional_str(entry.get("tradeability_class"))
        setup_score = _to_optional_float(entry.get("setup_score"))
        entry_ready = _to_optional_bool(entry.get("entry_ready"))
        risk_acceptable = _to_optional_bool(entry.get("risk_acceptable"))
        hard_risk_flags = _normalize_reason_list(entry.get("risk_flags"))
        readiness_reasons = _normalize_reason_list(entry.get("entry_readiness_reasons"))

        reasons: List[str] = []

        if tradeability_class not in ALLOWED_TRADEABILITY:
            reasons.extend(_normalize_tradeability_reasons(entry, tradeability_class))
            entry["decision"] = "NO_TRADE"
            entry["decision_reasons"] = _stable_reason_order(reasons)
            out.append(entry)
            continue

        if tradeability_class == "MARGINAL":
            reasons.append("tradeability_marginal")

        if hard_risk_flags:
            reasons.extend(hard_risk_flags)
            reasons.append("risk_flag_blocked")

        if setup_score is None:
            reasons.append("risk_data_insufficient")

        if risk_acceptable is False:
            reasons.append("risk_reward_unattractive")
        elif risk_acceptable is None:
            reasons.append("risk_data_insufficient")

        if entry_ready is False:
            reasons.append("entry_not_confirmed")
            reasons.extend(readiness_reasons)
        elif entry_ready is None:
            reasons.append("risk_data_insufficient")

        can_enter = (
            tradeability_class in ENTER_TRADEABILITY
            and entry_ready is True
            and (risk_acceptable is True or not cfg["require_risk_acceptable_for_enter"])
            and setup_score is not None
            and setup_score >= enter_threshold
            and not hard_risk_flags
        )

        if can_enter:
            entry["decision"] = "ENTER"
            entry["decision_reasons"] = []
            out.append(entry)
            continue

        if is_risk_off and setup_score is not None and setup_score < enter_threshold and setup_score >= cfg["min_score_for_enter"]:
            reasons.append("btc_regime_caution")

        can_wait = (
            tradeability_class in ALLOWED_TRADEABILITY
            and (setup_score is not None and setup_score >= cfg["min_score_for_wait"])
            and risk_acceptable is True
            and entry_ready is not None
            and not hard_risk_flags
        )

        if can_wait:
            entry["decision"] = "WAIT"
            entry["decision_reasons"] = _stable_reason_order(reasons)
        else:
            if setup_score is None or setup_score < cfg["min_score_for_wait"]:
                reasons.append("insufficient_edge")
            entry["decision"] = "NO_TRADE"
            entry["decision_reasons"] = _stable_reason_order(reasons)

        out.append(entry)

    return out


def _load_decision_config(config: Mapping[str, Any]) -> Dict[str, Any]:
    decision_cfg = config.get("decision", {}) if isinstance(config, Mapping) else {}
    btc_cfg = config.get("btc_regime", {}) if isinstance(config, Mapping) else {}

    min_score_for_enter = _expect_number(decision_cfg.get("min_score_for_enter", 65), "decision.min_score_for_enter")
    min_score_for_wait = _expect_number(decision_cfg.get("min_score_for_wait", 40), "decision.min_score_for_wait")
    if min_score_for_wait > min_score_for_enter:
        raise ValueError("decision.min_score_for_wait must be <= decision.min_score_for_enter")

    require_risk_acceptable_for_enter = _expect_bool(
        decision_cfg.get("require_risk_acceptable_for_enter", True),
        "decision.require_risk_acceptable_for_enter",
    )

    risk_off_enter_boost = _expect_number(btc_cfg.get("risk_off_enter_boost", 15), "btc_regime.risk_off_enter_boost")

    return {
        "min_score_for_enter": min_score_for_enter,
        "min_score_for_wait": min_score_for_wait,
        "require_risk_acceptable_for_enter": require_risk_acceptable_for_enter,
        "risk_off_enter_boost": risk_off_enter_boost,
    }


def _expect_number(value: Any, field_name: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{field_name} must be finite")
    return numeric


def _expect_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be boolean")
    return value


def _to_optional_float(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _to_optional_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return None


def _to_optional_str(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_reason_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            continue
        reason = item.strip()
        if not reason or reason in seen:
            continue
        seen.add(reason)
        out.append(reason)
    return out


def _normalize_tradeability_reasons(entry: MutableMapping[str, Any], tradeability_class: Optional[str]) -> List[str]:
    provided = _normalize_reason_list(entry.get("tradeability_reason_keys"))
    if provided:
        return provided
    if tradeability_class == "MARGINAL":
        return ["tradeability_marginal"]
    return ["tradeability_fail"]


def _stable_reason_order(reasons: Iterable[str]) -> List[str]:
    provided: List[str] = []
    seen = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        provided.append(reason)

    ordered: List[str] = []
    for reason in REASON_ORDER:
        if reason in seen:
            ordered.append(reason)

    for reason in provided:
        if reason not in ordered:
            ordered.append(reason)

    return ordered
