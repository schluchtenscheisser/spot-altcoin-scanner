from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

CANONICAL_TIMEFRAME_ORDER = ("1d", "4h")
_ALLOWED_TIMEFRAMES = set(CANONICAL_TIMEFRAME_ORDER)
_ALLOWED_EXECUTION_MODE = "disabled_historical_ohlcv_only"




class ScenarioValidationError(ValueError):
    """Scenario validation failed."""


def _require_int(mapping: Mapping[str, Any], key: str, *, path: str, min_value: int | None = None) -> int:
    if key not in mapping:
        raise ScenarioValidationError(f"Missing required scenario field: {path}.{key}")
    value = mapping[key]
    if isinstance(value, bool):
        raise ScenarioValidationError(f"Invalid integer field {path}.{key}: booleans are not allowed")
    if not isinstance(value, int):
        raise ScenarioValidationError(f"Invalid integer field {path}.{key}: expected integer")
    if min_value is not None and value < min_value:
        raise ScenarioValidationError(f"Invalid integer field {path}.{key}: expected >= {min_value}")
    return value


def _canonicalize_timeframes(raw_timeframes: Sequence[Any]) -> tuple[str, ...]:
    raw = [str(v) for v in raw_timeframes]
    if not raw:
        raise ScenarioValidationError("Missing or empty required scenario field: timeframes")
    duplicates = sorted({tf for tf in raw if raw.count(tf) > 1})
    if duplicates:
        raise ScenarioValidationError(f"Duplicate timeframes are not allowed: {duplicates}")
    unsupported = sorted(set(raw) - _ALLOWED_TIMEFRAMES)
    if unsupported:
        raise ScenarioValidationError(f"Unsupported timeframes: {unsupported}")
    raw_set = set(raw)
    return tuple(tf for tf in CANONICAL_TIMEFRAME_ORDER if tf in raw_set)
@dataclass(frozen=True)
class DateRange:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class ReplayScenario:
    scenario_id: str
    history_dataset_ref: str
    history_manifest_ref: str
    universe_manifest_ref: str
    evaluation: DateRange
    timeframes: tuple[str, ...]
    universe_mode: str
    execution_mode: str
    scanner_config_ref: str
    scanner_config_hash: str
    regime_method_ref: str
    settlement_delay_seconds: int
    warm_up_1d_bars: int
    warm_up_4h_bars: int
    splits: dict[str, DateRange] | None


def _require_str(root: dict[str, Any], key: str) -> str:
    value = root.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _parse_date(value: Any, key: str) -> date:
    if isinstance(value, datetime):
        raise ValueError(f"{key} must be date-only ISO string")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{key} must be ISO date string")
    if "T" in value:
        raise ValueError(f"{key} must be date-only ISO string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{key} invalid ISO date") from exc


def load_scenario(path: Path) -> ReplayScenario:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scenario must be a mapping")

    evaluation = payload.get("evaluation")
    if not isinstance(evaluation, dict):
        raise ValueError("evaluation is required")
    start_date = _parse_date(evaluation.get("start_date"), "evaluation.start_date")
    end_date = _parse_date(evaluation.get("end_date"), "evaluation.end_date")
    if start_date > end_date:
        raise ValueError("evaluation.start_date must be <= evaluation.end_date")

    execution = payload.get("execution")
    if not isinstance(execution, dict):
        raise ValueError("execution is required")
    execution_mode = _require_str(execution, "mode")
    if execution_mode != _ALLOWED_EXECUTION_MODE:
        raise ValueError("execution.mode must be disabled_historical_ohlcv_only")

    tfs = payload.get("timeframes")
    if not isinstance(tfs, list):
        raise ScenarioValidationError("Missing or empty required scenario field: timeframes")
    timeframes = _canonicalize_timeframes(tfs)

    scanner_config = payload.get("scanner_config")
    regime_labels = payload.get("regime_labels")
    replay_policy = payload.get("daily_replay_time_policy")
    warmup = payload.get("warmup")
    if not isinstance(scanner_config, dict) or not isinstance(regime_labels, dict) or not isinstance(replay_policy, dict) or not isinstance(warmup, dict):
        raise ValueError("scanner_config, regime_labels, daily_replay_time_policy and warmup are required")

    scenario = ReplayScenario(
        scenario_id=_require_str(payload, "scenario_id"),
        history_dataset_ref=_require_str(payload, "history_dataset_ref"),
        history_manifest_ref=_require_str(payload, "history_manifest_ref"),
        universe_manifest_ref=_require_str(payload, "universe_manifest_ref"),
        evaluation=DateRange(start_date=start_date, end_date=end_date),
        timeframes=timeframes,
        universe_mode=_require_str(payload, "universe_mode"),
        execution_mode=execution_mode,
        scanner_config_ref=_require_str(scanner_config, "ref"),
        scanner_config_hash=_require_str(scanner_config, "hash"),
        regime_method_ref=_require_str(regime_labels, "method_ref"),
        settlement_delay_seconds=_require_int(replay_policy, "settlement_delay_seconds", path="daily_replay_time_policy", min_value=0),
        warm_up_1d_bars=_require_int(warmup, "warm_up_1d_bars", path="warmup", min_value=1),
        warm_up_4h_bars=_require_int(warmup, "warm_up_4h_bars", path="warmup", min_value=1),
        splits=_parse_splits(payload.get("splits"), start_date, end_date),
    )
    return scenario


def _parse_splits(raw: Any, eval_start: date, eval_end: date) -> dict[str, DateRange] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("splits must be a mapping")
    result: dict[str, DateRange] = {}
    for key in ("calibration", "validation"):
        if key not in raw:
            continue
        block = raw[key]
        if not isinstance(block, dict):
            raise ValueError(f"splits.{key} must be a mapping")
        start = _parse_date(block.get("start_date"), f"splits.{key}.start_date")
        end = _parse_date(block.get("end_date"), f"splits.{key}.end_date")
        if start > end:
            raise ValueError(f"splits.{key}.start_date must be <= end_date")
        if start < eval_start or end > eval_end:
            raise ValueError(f"splits.{key} must be inside evaluation range")
        result[key] = DateRange(start, end)
    if {"calibration", "validation"}.issubset(result):
        cal = result["calibration"]
        val = result["validation"]
        if not (cal.end_date < val.start_date or val.end_date < cal.start_date):
            raise ValueError("splits.calibration and splits.validation must not overlap")
    return result or None


def scenario_config_hash(scenario: ReplayScenario) -> str:
    canonical = {
        "scenario_id": scenario.scenario_id,
        "history_dataset_ref": scenario.history_dataset_ref,
        "history_manifest_ref": scenario.history_manifest_ref,
        "universe_manifest_ref": scenario.universe_manifest_ref,
        "evaluation": {
            "start_date": scenario.evaluation.start_date.isoformat(),
            "end_date": scenario.evaluation.end_date.isoformat(),
        },
        "timeframes": list(scenario.timeframes),
        "universe_mode": scenario.universe_mode,
        "execution": {"mode": scenario.execution_mode},
        "scanner_config": {"ref": scenario.scanner_config_ref, "hash": scenario.scanner_config_hash},
        "regime_labels": {"method_ref": scenario.regime_method_ref},
        "daily_replay_time_policy": {"settlement_delay_seconds": scenario.settlement_delay_seconds},
        "warmup": {
            "warm_up_1d_bars": scenario.warm_up_1d_bars,
            "warm_up_4h_bars": scenario.warm_up_4h_bars,
        },
    }
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
