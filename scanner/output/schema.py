from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
import math
import re
from typing import Any, Dict, Mapping, Literal

SCHEMA_VERSION = "ir1.3"
ACCEPTED_DIAGNOSTICS_SCHEMA_VERSIONS = {"ir1.0", "ir1.1", "ir1.2", SCHEMA_VERSION}

logger = logging.getLogger(__name__)

ScanMode = Literal["daily", "intraday"]

COUNTS_BUCKET_KEYS = (
    "watchlist",
    "early_candidates",
    "confirmed_candidates",
    "late_monitor",
    "discarded",
)

SYMBOL_LIST_BUCKET_KEYS = (
    "confirmed_candidates",
    "early_candidates",
    "watchlist",
    "late_monitor",
)

ENTRY_LOCATION_STATUS_VALUES = {"fresh_entry", "acceptable_entry", "extended_entry", "chased_entry", "not_evaluable"}
ENTRY_ACTION_HINT_VALUES = {"buy_now_candidate", "acceptable_if_strategy_allows", "wait_for_pullback", "avoid_chasing", "monitor_only", "not_evaluable"}

ENTRY_LOCATION_INPUT_KEYS = (
    "close_vs_ema20_4h_pct",
    "bars_above_ema20_4h",
    "dist_to_ema20_4h_pct_abs",
    "distance_to_last_structural_anchor_pct_abs",
    "distance_to_range_high_pct_abs",
    "bars_since_last_structural_break_4h",
)

REQUIRED_DIAGNOSTIC_BLOCKS = (
    "axes",
    "phase",
    "invalidation",
    "cycle",
    "state",
    "pattern",
    "decision",
    "reasons",
)

_AS_OF_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_DAILY_BAR_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INTRADAY_BAR_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T(00|04|08|12|16|20):00:00Z$")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_scan_mode(value: Any) -> ScanMode:
    if value not in {"daily", "intraday"}:
        raise ValueError(f"scan_mode must be 'daily' or 'intraday', got {value!r}")
    return value


def validate_run_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"run_id must be a non-empty string, got {value!r}")
    if not _RUN_ID_RE.match(value):
        raise ValueError(
            "run_id must match ^[A-Za-z0-9][A-Za-z0-9._-]*$ "
            "(safe characters only; no path separators)"
        )
    if ".." in value:
        raise ValueError("run_id must not contain '..'")
    return value


def validate_as_of_utc(value: Any) -> str:
    if not isinstance(value, str) or not _AS_OF_UTC_RE.match(value):
        raise ValueError(
            f"as_of_utc must match YYYY-MM-DDTHH:MM:SSZ, got {value!r}"
        )
    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    return value


def validate_daily_bar_id(value: Any) -> str:
    if not isinstance(value, str) or not _DAILY_BAR_ID_RE.match(value):
        raise ValueError(f"daily_bar_id must match YYYY-MM-DD, got {value!r}")
    date.fromisoformat(value)
    return value


def validate_intraday_bar_id(scan_mode: ScanMode, value: Any) -> str | None:
    if scan_mode == "daily":
        if value is not None:
            raise ValueError("intraday_bar_id must be null for daily scan_mode")
        return None

    if isinstance(value, str) and _INTRADAY_BAR_ID_RE.match(value):
        return value
    raise ValueError(
        f"intraday_bar_id must match YYYY-MM-DDTHH:00:00Z for intraday scan_mode, got {value!r}"
    )


def _require_symbol_list(key: str, value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"symbol_lists.{key} must be a list[str], got {value!r}")
    out: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise ValueError(f"symbol_lists.{key}[{idx}] must be non-empty str, got {item!r}")
        out.append(item)
    return out


def normalize_symbol_lists(value: Mapping[str, Any] | None) -> Dict[str, list[str]]:
    source: Mapping[str, Any] = value or {}
    unknown = set(source.keys()) - set(SYMBOL_LIST_BUCKET_KEYS)
    if unknown:
        raise ValueError(f"symbol_lists contains unsupported keys: {sorted(unknown)}")

    return {k: _require_symbol_list(k, source.get(k, [])) for k in SYMBOL_LIST_BUCKET_KEYS}


def normalize_counts_by_bucket(value: Mapping[str, Any] | None) -> Dict[str, int]:
    source: Mapping[str, Any] = value or {}
    unknown = set(source.keys()) - set(COUNTS_BUCKET_KEYS)
    if unknown:
        raise ValueError(f"counts_by_bucket contains unsupported keys: {sorted(unknown)}")

    counts: Dict[str, int] = {}
    for key in COUNTS_BUCKET_KEYS:
        raw = source.get(key, 0)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
            raise ValueError(f"counts_by_bucket.{key} must be int >= 0, got {raw!r}")
        counts[key] = raw
    return counts


@dataclass(frozen=True)
class RunReport:
    run_id: str
    scan_mode: ScanMode
    as_of_utc: str
    daily_bar_id: str
    intraday_bar_id: str | None
    counts_by_bucket: Dict[str, int]
    symbol_lists: Dict[str, list[str]]
    manifest_path: str
    diagnostics_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": validate_run_id(self.run_id),
            "scan_mode": validate_scan_mode(self.scan_mode),
            "as_of_utc": validate_as_of_utc(self.as_of_utc),
            "daily_bar_id": validate_daily_bar_id(self.daily_bar_id),
            "intraday_bar_id": validate_intraday_bar_id(self.scan_mode, self.intraday_bar_id),
            "counts_by_bucket": normalize_counts_by_bucket(self.counts_by_bucket),
            "symbol_lists": normalize_symbol_lists(self.symbol_lists),
            "manifest_path": _validate_relative_path("manifest_path", self.manifest_path),
            "diagnostics_path": _validate_relative_path("diagnostics_path", self.diagnostics_path),
        }


def _validate_relative_path(key: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be non-empty str")
    if value.startswith("/"):
        raise ValueError(f"{key} must be repository-root-relative, got absolute path")
    return value


def validate_diagnostics_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError(f"diagnostics record must be mapping, got {record!r}")

    scan_mode = validate_scan_mode(record.get("scan_mode"))

    out: Dict[str, Any] = {
        "schema_version": record.get("schema_version") or SCHEMA_VERSION,
        "run_id": validate_run_id(record.get("run_id")),
        "scan_mode": scan_mode,
        "symbol": _require_symbol(record.get("symbol")),
        "as_of_utc": validate_as_of_utc(record.get("as_of_utc")),
        "daily_bar_id": validate_daily_bar_id(record.get("daily_bar_id")),
        "intraday_bar_id": validate_intraday_bar_id(scan_mode, record.get("intraday_bar_id")),
        "data_4h_available": _require_bool("data_4h_available", record.get("data_4h_available")),
    }

    if out["schema_version"] not in ACCEPTED_DIAGNOSTICS_SCHEMA_VERSIONS:
        raise ValueError(
            "diagnostics.schema_version must be one of "
            f"{sorted(ACCEPTED_DIAGNOSTICS_SCHEMA_VERSIONS)!r}, got {out['schema_version']!r}"
        )

    for block_key in REQUIRED_DIAGNOSTIC_BLOCKS:
        block = record.get(block_key)
        if not isinstance(block, Mapping):
            raise ValueError(f"diagnostics.{block_key} must be object")
        out[block_key] = dict(block)
    universe_block = record.get("universe")
    if universe_block is None:
        universe_block = {
            "universe_category": "classic_crypto",
            "universe_category_confidence": "low",
            "universe_category_reason": "no_non_classic_rule_matched",
            "candidate_excluded": False,
            "candidate_exclusion_reason": None,
        }
    if not isinstance(universe_block, Mapping):
        raise ValueError("diagnostics.universe must be object")
    out["universe"] = dict(universe_block)
    out["candidate_excluded"] = _require_bool("candidate_excluded", record.get("candidate_excluded", False))
    out["entry_location_inputs"] = normalize_entry_location_inputs(
        record.get("entry_location_inputs"),
        data_4h_available=out["data_4h_available"],
        symbol=out["symbol"],
    )
    if "entry_location" in record:
        out["entry_location"] = normalize_entry_location_block(record.get("entry_location"))

    out["execution_attempted"] = _require_bool("execution_attempted", record.get("execution_attempted", False))
    out["execution_status_raw"] = _require_nullable_str("execution_status_raw", record.get("execution_status_raw"))
    out["execution_reason_raw"] = _require_nullable_str("execution_reason_raw", record.get("execution_reason_raw"))
    out["execution_pass"] = _require_nullable_bool("execution_pass", record.get("execution_pass"))
    grade = record.get("execution_grade_t16")
    if grade is not None:
        raise ValueError("execution_grade_t16 must be null")
    out["execution_grade_t16"] = None
    for key in (
        "available_depth_1pct_usdt",
        "depth_threshold_1pct_usdt",
        "available_depth_ratio",
        "recommended_position_factor_preview",
        "recommended_position_factor",
        "execution_grade_effective",
        "spread_pct",
        "estimated_slippage_bps",
        "bid_depth_1pct_usdt",
        "ask_depth_1pct_usdt",
    ):
        value = record.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ValueError(f"{key} must be number or null")
        if value is not None and not math.isfinite(float(value)):
            raise ValueError(f"{key} must be finite number or null")
        out[key] = float(value) if value is not None else None
    out["depth_ratio_band"] = _require_nullable_str("depth_ratio_band", record.get("depth_ratio_band"))
    out["execution_size_class"] = _require_nullable_str("execution_size_class", record.get("execution_size_class"))
    reason_keys = record.get("tradeability_reason_keys", [])
    if reason_keys is None:
        reason_keys = []
    if not isinstance(reason_keys, list) or any(not isinstance(reason, str) for reason in reason_keys):
        raise ValueError("tradeability_reason_keys must be list[str]")
    out["tradeability_reason_keys"] = list(reason_keys)
    out["is_reduced_size_eligible"] = _require_bool("is_reduced_size_eligible", record.get("is_reduced_size_eligible", False))
    out["is_tradeable_candidate"] = _require_bool("is_tradeable_candidate", record.get("is_tradeable_candidate", False))
    out["execution_limiting_metric"] = _require_nullable_str("execution_limiting_metric", record.get("execution_limiting_metric"))
    side = _require_nullable_str("depth_side_used", record.get("depth_side_used"))
    out["depth_side_used"] = side
    age = record.get("orderbook_snapshot_age_ms")
    if age is not None and (isinstance(age, bool) or not isinstance(age, int) or age < 0):
        raise ValueError("orderbook_snapshot_age_ms must be int >= 0 or null")
    out["orderbook_snapshot_age_ms"] = age
    duration = record.get("execution_fetch_duration_ms")
    if duration is not None and (isinstance(duration, bool) or not isinstance(duration, int) or duration < 0):
        raise ValueError("execution_fetch_duration_ms must be int >= 0 or null")
    out["execution_fetch_duration_ms"] = duration
    _validate_diagnostics_invariants(out)

    return out


def normalize_entry_location_block(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("diagnostics.entry_location must be object")
    status = _require_nullable_str("entry_location.entry_location_status", value.get("entry_location_status"))
    if status is not None and status not in ENTRY_LOCATION_STATUS_VALUES:
        raise ValueError(f"entry_location.entry_location_status must be one of {sorted(ENTRY_LOCATION_STATUS_VALUES)}, got {status!r}")
    hint = _require_nullable_str("entry_location.entry_action_hint", value.get("entry_action_hint"))
    if hint is not None and hint not in ENTRY_ACTION_HINT_VALUES:
        raise ValueError(f"entry_location.entry_action_hint must be one of {sorted(ENTRY_ACTION_HINT_VALUES)}, got {hint!r}")
    reason_primary = _require_nullable_str("entry_location.entry_location_reason_primary", value.get("entry_location_reason_primary"))
    reason_codes = value.get("entry_location_reason_codes", [])
    if not isinstance(reason_codes, list) or any(not isinstance(reason, str) for reason in reason_codes):
        raise ValueError("entry_location.entry_location_reason_codes must be list[str]")
    warning = _require_nullable_bool("entry_location.range_high_proximity_warning", value.get("range_high_proximity_warning"))
    inputs_used = value.get("entry_location_inputs_used", {})
    if not isinstance(inputs_used, Mapping):
        raise ValueError("entry_location.entry_location_inputs_used must be object")
    sanitized_inputs: Dict[str, Any] = {}
    allowed_inputs = set(ENTRY_LOCATION_INPUT_KEYS) | {"entry_pattern", "threshold_source", "range_high_proximity_warning"}
    unknown = set(inputs_used.keys()) - allowed_inputs
    if unknown:
        raise ValueError(f"entry_location.entry_location_inputs_used contains unsupported keys: {sorted(unknown)}")
    for key in ENTRY_LOCATION_INPUT_KEYS:
        raw = inputs_used.get(key)
        if raw is None:
            sanitized_inputs[key] = None
        elif isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
            raise ValueError(f"entry_location.entry_location_inputs_used.{key} must be finite number or null")
        elif key in {"bars_above_ema20_4h", "bars_since_last_structural_break_4h"}:
            sanitized_inputs[key] = int(raw)
        else:
            sanitized_inputs[key] = float(raw)
    sanitized_inputs["entry_pattern"] = _require_nullable_str("entry_location.entry_location_inputs_used.entry_pattern", inputs_used.get("entry_pattern"))
    sanitized_inputs["threshold_source"] = _require_nullable_str("entry_location.entry_location_inputs_used.threshold_source", inputs_used.get("threshold_source"))
    sanitized_inputs["range_high_proximity_warning"] = _require_nullable_bool(
        "entry_location.entry_location_inputs_used.range_high_proximity_warning",
        inputs_used.get("range_high_proximity_warning"),
    )
    return {
        "entry_location_status": status,
        "entry_action_hint": hint,
        "entry_location_reason_primary": reason_primary,
        "entry_location_reason_codes": list(reason_codes),
        "range_high_proximity_warning": warning,
        "entry_location_inputs_used": sanitized_inputs,
    }

def normalize_entry_location_inputs(
    value: Mapping[str, Any] | None,
    *,
    data_4h_available: bool,
    symbol: str | None = None,
) -> Dict[str, float | int | None]:
    source: Mapping[str, Any] = value or {}
    unknown = set(source.keys()) - set(ENTRY_LOCATION_INPUT_KEYS)
    if unknown:
        raise ValueError(f"entry_location_inputs contains unsupported keys: {sorted(unknown)}")

    out: Dict[str, float | int | None] = {}
    for key in ENTRY_LOCATION_INPUT_KEYS:
        if not data_4h_available:
            out[key] = None
            continue
        raw = source.get(key)
        if raw is None:
            out[key] = None
            continue
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError(f"entry_location_inputs.{key} must be number or null")
        if not math.isfinite(float(raw)):
            logger.warning(
                "non-finite entry_location_inputs value serialized as null",
                extra={"symbol": symbol, "field": key},
            )
            out[key] = None
            continue
        if key in {"bars_above_ema20_4h", "bars_since_last_structural_break_4h"}:
            out[key] = int(raw)
        else:
            out[key] = float(raw)
    return out


def _validate_diagnostics_invariants(record: Mapping[str, Any]) -> None:
    state = record.get("state") if isinstance(record.get("state"), Mapping) else {}
    phase = record.get("phase") if isinstance(record.get("phase"), Mapping) else {}
    decision = record.get("decision") if isinstance(record.get("decision"), Mapping) else {}
    cycle = record.get("cycle") if isinstance(record.get("cycle"), Mapping) else {}

    state_machine_state = state.get("state_machine_state")
    setup_cycle_id = state.get("setup_cycle_id")
    current_setup_cycle_id = state.get("current_setup_cycle_id")
    resolved_setup_cycle_id = cycle.get("resolved_setup_cycle_id")
    cycle_id_present = any(v is not None for v in (setup_cycle_id, current_setup_cycle_id, resolved_setup_cycle_id))
    decision_bucket = decision.get("decision_bucket")

    if record.get("execution_attempted") is True:
        missing: list[str] = []
        if state_machine_state is None:
            missing.append("state.state_machine_state")
        if decision_bucket is None:
            missing.append("decision.decision_bucket")
        if decision.get("priority_score") is None:
            missing.append("decision.priority_score")
        if phase.get("market_phase") is None:
            missing.append("phase.market_phase")
        if phase.get("market_phase_confidence") is None:
            missing.append("phase.market_phase_confidence")
        if not cycle_id_present:
            missing.append("state.setup_cycle_id|state.current_setup_cycle_id|cycle.resolved_setup_cycle_id")
        if missing:
            raise ValueError(f"execution_attempted=true requires non-null fields: {', '.join(missing)}")

    if decision_bucket is not None and decision_bucket != "discarded" and state_machine_state is None:
        raise ValueError("decision.decision_bucket requires non-null state.state_machine_state")

    cycle_required_states = {"watch", "early_ready", "confirmed_ready", "late", "chased", "rejected"}
    if state_machine_state in cycle_required_states and not cycle_id_present:
        raise ValueError(
            f"state.state_machine_state={state_machine_state!r} requires at least one cycle id "
            "(state.setup_cycle_id|state.current_setup_cycle_id|cycle.resolved_setup_cycle_id)"
        )


def _require_symbol(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"symbol must be non-empty str, got {value!r}")
    return value


def _require_bool(key: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be bool, got {value!r}")
    return value


def _require_nullable_str(key: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be str or null, got {value!r}")
    return value


def _require_nullable_bool(key: str, value: Any) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be bool or null, got {value!r}")
    return value
