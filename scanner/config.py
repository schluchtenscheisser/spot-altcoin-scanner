"""
Configuration loading and validation.
Loads config.yml and applies environment variable overrides.
"""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping
import yaml


CONFIG_PATH = os.getenv("SCANNER_CONFIG_PATH", "config/config.yml")

_BUDGET_DEFAULTS = {
    "shortlist_size": 200,
    "orderbook_top_k": 200,
    "pre_shortlist_market_cap_floor_usd": 25_000_000,
}


_INDEPENDENCE_RELEASE_SECTION_DEFAULTS = {
    "runtime": {},
    "bar_clock": {},
    "universe": {},
    "market_data_budget": {},
    "phase": {},
    "state": {},
    "invalidation": {},
    "entry": {},
    "execution": {},
    "reports": {},
    "snapshots": {},
    "retention": {},
    "ohlcv_fetch": {},
    "cache_policy": {},
}




_INDEPENDENCE_UNIVERSE_DEFAULTS = {
    "quote_asset_allowed": ["USDT"],
    "listing_age_days_min": 45,
    "quote_volume_24h_min": 500000,
    "market_cap_usd_min": 10000000,
    "mexc_tradeable_status_values": ["1"],
}


_INDEPENDENCE_OHLCV_FETCH_DEFAULTS = {
    "lookback_bars_1d": 250,
    "lookback_bars_4h": 250,
    "incremental_max_bars": 50,
    "per_call_timeout_s": 30,
    "max_retries": 0,
    "min_lookback_bars_1d": 120,
    "min_lookback_bars_4h": 120,
}

_INDEPENDENCE_MARKET_DATA_BUDGET_DEFAULTS = {
    "activity_gate": {
        "daily_quote_volume_active_floor": 25000,
        "min_active_days": 12,
        "window_days": 14,
    },
    "monitoring_bypass": {
        "min_phase_confidence": 55,
    },
    "pre_4h_candidate_filter": {
        "rule_a": {
            "close_vs_ema50_1d_pct_min_exclusive": 0.0,
            "ema20_vs_ema50_1d_pct_min_inclusive": 0.0,
            "ema20_slope_1d_pct_per_bar_min_exclusive": 0.0,
        },
        "rule_b": {
            "volume_1d_current_vs_median10_min_inclusive": 2.0,
        },
        "rule_c": {
            "range_width_10bars_1d_pct_max_inclusive": 10.0,
            "close_position_in_range_10bars_1d_min_inclusive": 0.70,
        },
    },
    "max_4h_fetch_count": 100,
}

_INDEPENDENCE_REPORTS_DEFAULTS = {
    "recent_runs_limit": 30,
    "emit_report_md": False,
    "emit_report_xlsx": False,
}


_AXES_DEFAULTS = {
    "min_effective_weight_ratio": 0.60,
    "trend_strength": {
        "close_vs_ema20_1d_pct": {"low": -10.0, "mid": 0.0, "high": 10.0, "weight": 0.20},
        "close_vs_ema50_1d_pct": {"low": -10.0, "mid": 0.0, "high": 10.0, "weight": 0.15},
        "close_vs_ema20_4h_pct": {"low": -10.0, "mid": 0.0, "high": 10.0, "weight": 0.15},
        "close_vs_ema50_4h_pct": {"low": -10.0, "mid": 0.0, "high": 10.0, "weight": 0.10},
        "ema20_slope_1d_pct_per_bar": {"low": -1.5, "mid": 0.0, "high": 1.5, "weight": 0.10},
        "ema20_slope_4h_pct_per_bar": {"low": -1.5, "mid": 0.0, "high": 1.5, "weight": 0.10},
        "ema20_vs_ema50_1d_pct": {"low": -8.0, "mid": 0.0, "high": 8.0, "weight": 0.10},
        "ema20_vs_ema50_4h_pct": {"low": -8.0, "mid": 0.0, "high": 8.0, "weight": 0.10},
    },
    "reclaim_progress": {
        "distance": {"low": -3.0, "mid": 0.0, "high": 3.0},
        "hold_points": [(0.0, 0.0), (1.0, 40.0), (2.0, 70.0), (3.0, 100.0)],
        "anchors": {
            "ema20_4h": {"weight": 0.25},
            "ema50_4h": {"weight": 0.20},
            "ema20_1d": {"weight": 0.20},
            "ema50_1d": {"weight": 0.15},
            "fixed_structural_4h": {"weight": 0.20},
        },
    },
    "compression_strength": {
        "bb_width_rank_120_4h": {"low_good": 10.0, "mid": 50.0, "high_bad": 100.0, "weight": 0.35},
        "atr_pct_rank_120_1d": {"low_good": 10.0, "mid": 50.0, "high_bad": 100.0, "weight": 0.25},
        "range_width_12bars_4h_vs_atr1d_pct": {"low_good": 50.0, "mid": 100.0, "high_bad": 200.0, "weight": 0.25},
        "std_return_rank_12bars_4h_pct": {"low_good": 10.0, "mid": 50.0, "high_bad": 100.0, "weight": 0.15},
    },
    "expansion_progress_structural": {
        "move_from_last_structural_break_pct": {"points": [(0.0, 0.0), (3.0, 30.0), (6.0, 60.0), (10.0, 100.0)], "weight": 0.40},
        "bars_since_last_structural_break_4h": {"points": [(0.0, 0.0), (1.0, 20.0), (2.0, 40.0), (4.0, 70.0), (6.0, 100.0)], "weight": 0.20},
        "dist_to_base_mid_pct": {"points": [(0.0, 0.0), (3.0, 35.0), (6.0, 65.0), (10.0, 100.0)], "weight": 0.20},
        "dist_to_ema20_4h_pct_abs": {"points": [(0.0, 0.0), (2.0, 30.0), (5.0, 65.0), (8.0, 100.0)], "weight": 0.20},
    },
    "volume_regime_shift": {
        "volume_quote_spike_1d": {"low": 0.9, "mid": 1.2, "high": 2.0, "weight": 0.25},
        "volume_quote_spike_4h": {"low": 0.9, "mid": 1.2, "high": 2.0, "weight": 0.35},
        "volume_spike_persistence_4h": {"points": [(0.00, 0.0), (0.25, 30.0), (0.50, 60.0), (0.75, 85.0), (1.00, 100.0)], "weight": 0.20},
        "volume_4h_current_vs_median10": {"points": [(0.8, 0.0), (1.0, 40.0), (1.3, 70.0), (1.8, 100.0)], "weight": 0.20},
    },
    "freshness_distance_structural": {
        "distance_to_last_structural_anchor_pct_abs": {"points": [(0.0, 0.0), (1.0, 25.0), (2.0, 50.0), (3.0, 75.0), (5.0, 100.0)], "weight": 0.35},
        "distance_to_range_high_pct_abs": {"points": [(0.0, 0.0), (1.0, 30.0), (2.0, 55.0), (4.0, 100.0)], "weight": 0.25},
        "bars_since_last_volume_shift_4h": {"points": [(0.0, 0.0), (1.0, 20.0), (2.0, 40.0), (4.0, 70.0), (6.0, 100.0)], "weight": 0.20},
        "bars_since_last_structural_break_4h": {"points": [(0.0, 0.0), (1.0, 20.0), (2.0, 40.0), (4.0, 70.0), (6.0, 100.0)], "weight": 0.20},
    },
    "base_integrity_simplified": {
        "bars_since_last_new_low_4h": {"points": [(0.0, 0.0), (2.0, 25.0), (4.0, 50.0), (8.0, 80.0), (12.0, 100.0)]},
        "range_width_12bars_4h_pct": {"low_good": 4.0, "mid": 9.0, "high_bad": 18.0},
        "close_position_in_range_12bars_4h": {"points": [(0.0, 0.0), (0.25, 20.0), (0.50, 50.0), (0.75, 80.0), (1.00, 100.0)]},
        "close_above_range_mid_ratio_12bars_4h": {"points": [(0.0, 0.0), (0.25, 25.0), (0.50, 50.0), (0.75, 80.0), (1.00, 100.0)]},
        "bars_since_last_new_low_1d": {"points": [(0.0, 0.0), (2.0, 35.0), (4.0, 60.0), (7.0, 85.0), (10.0, 100.0)]},
        "range_width_10bars_1d_pct": {"low_good": 8.0, "mid": 15.0, "high_bad": 30.0},
        "close_position_in_range_10bars_1d": {"points": [(0.0, 0.0), (0.25, 20.0), (0.50, 50.0), (0.75, 80.0), (1.00, 100.0)]},
        "close_above_range_mid_ratio_10bars_1d": {"points": [(0.0, 0.0), (0.25, 25.0), (0.50, 50.0), (0.75, 80.0), (1.00, 100.0)]},
    },
    "pullback_quality_simplified": {
        "pullback_depth_vs_last_impulse_pct_4h": {"points": [(0.0, 70.0), (20.0, 100.0), (40.0, 75.0), (60.0, 40.0), (100.0, 0.0)]},
        "pullback_volume_ratio_4h": {"points": [(0.3, 100.0), (0.6, 85.0), (1.0, 50.0), (1.3, 20.0), (1.8, 0.0)]},
        "close_vs_ema20_4h_pct": {"low": -8.0, "mid": 0.0, "high": 8.0},
        "lowest_low_vs_ema20_4h_pct": {"low": -10.0, "mid": -2.0, "high": 4.0},
        "pullback_depth_vs_last_impulse_pct_1d": {"points": [(0.0, 70.0), (20.0, 100.0), (40.0, 75.0), (60.0, 40.0), (100.0, 0.0)]},
        "pullback_volume_ratio_1d": {"points": [(0.3, 100.0), (0.6, 85.0), (1.0, 50.0), (1.3, 20.0), (1.8, 0.0)]},
        "close_vs_ema20_1d_pct": {"low": -8.0, "mid": 0.0, "high": 8.0},
        "lowest_low_vs_ema20_1d_pct": {"low": -10.0, "mid": -2.0, "high": 4.0},
    },
    "reacceleration_strength_simplified": {
        "close_vs_rolling_high_5_4h_pct": {"low": -4.0, "mid": 0.0, "high": 4.0},
        "volume_4h_current_vs_median10": {"points": [(0.8, 10.0), (1.0, 40.0), (1.2, 65.0), (1.5, 85.0), (2.0, 100.0)]},
        "ema20_slope_4h_pct_per_bar": {"low": -1.0, "mid": 0.0, "high": 1.0},
        "close_vs_ema20_4h_pct": {"low": -6.0, "mid": 0.0, "high": 6.0},
        "close_vs_rolling_high_5_1d_pct": {"low": -4.0, "mid": 0.0, "high": 4.0},
        "volume_1d_current_vs_median10": {"points": [(0.8, 10.0), (1.0, 40.0), (1.2, 65.0), (1.5, 85.0), (2.0, 100.0)]},
        "ema20_slope_1d_pct_per_bar": {"low": -1.0, "mid": 0.0, "high": 1.0},
        "close_vs_ema20_1d_pct": {"low": -6.0, "mid": 0.0, "high": 6.0},
    },
}


_FEATURE_LAYER_DEFAULTS = {
    "segmentation_window_4h": 20,
    "segmentation_window_1d": 15,
    "persistence_spike_threshold": 1.2,
    "volume_shift_lookback_4h": 120,
    "range_high_lookback_4h": 20,
    "structural_break": {
        "min_bars_below_before_break": 3,
    },
}

_PHASE_DEFAULTS = {
    "min_effective_weight_ratio": 0.60,
    "global_confidence_floor": 55.0,
    "reduced_resolution_confidence_cap": 75.0,
    "phase_gap_floor": 8.0,
    "pressure_build": {
        "floor_compression": 60.0,
        "floor_volume_shift": 50.0,
        "max_expansion": 50.0,
    },
    "trend_resume": {
        "floor_trend": 55.0,
        "floor_reclaim": 45.0,
        "max_expansion": 65.0,
    },
    "transition_reclaim": {
        "floor_reclaim": 45.0,
        "floor_volume_shift": 45.0,
        "max_expansion": 55.0,
    },
}

_INVALIDATION_DEFAULTS = {
    "max_state_freshness": 100.0,
    "max_expansion_progress": 100.0,
    "max_structural_freshness": 100.0,
    "pressure_build": {
        "min_compression_hold": 60.0,
        "min_base_hold": 50.0,
        "min_volume_shift_hold": 50.0,
    },
    "trend_resume": {
        "min_trend_hold": 55.0,
        "min_reclaim_hold": 45.0,
        "min_pullback_hold": 45.0,
        "min_reaccel_hold": 45.0,
    },
    "transition_reclaim": {
        "min_reclaim_hold": 45.0,
        "min_base_hold": 45.0,
        "min_volume_shift_hold": 45.0,
    },
}

_CYCLE_DEFAULTS = {
    "expansion_reset_max": 35.0,
    "min_bars_since_cycle_end": 2,
    "enable_reclaim_reset": False,
}


_ENTRY_DEFAULTS = {
    "pressure_build": {
        "range_reclaim": {
            "min_reclaim": 45.0,
            "min_compression": 55.0,
            "max_freshness": 60.0,
        },
        "breakout": {
            "min_expansion": 35.0,
            "min_volume_shift": 55.0,
            "max_freshness": 65.0,
            "target_expansion": 40.0,
        },
        "break_and_hold": {
            "min_reclaim": 55.0,
            "min_base_integrity": 45.0,
            "min_expansion": 30.0,
            "max_expansion": 65.0,
        },
    },
    "trend_resume": {
        "shallow_pullback": {
            "min_pullback_quality": 55.0,
            "min_trend": 55.0,
            "max_freshness": 65.0,
        },
        "resume_reclaim": {
            "min_reclaim": 50.0,
            "min_reaccel": 50.0,
            "max_freshness": 60.0,
        },
        "continuation_breakout": {
            "min_trend": 60.0,
            "min_reaccel": 55.0,
            "max_expansion": 70.0,
        },
    },
    "transition_reclaim": {
        "ema_reclaim": {
            "min_reclaim": 45.0,
            "min_trend": 40.0,
            "max_freshness": 65.0,
        },
        "base_reclaim": {
            "min_base_integrity": 45.0,
            "min_reclaim": 45.0,
        },
        "early_reversal_break": {
            "min_reclaim": 50.0,
            "min_volume_shift": 50.0,
            "max_freshness": 60.0,
        },
    },
}

_STATE_DEFAULTS = {
    "confidence": {
        "blended_penalty": 5.0,
        "not_full_resolution_penalty": 10.0,
    },
    "freshness": {
        "bars_points": [[0.0, 0.0], [1.0, 20.0], [2.0, 40.0], [4.0, 70.0], [6.0, 100.0]],
        "distance_points": [[0.0, 0.0], [1.0, 25.0], [2.0, 50.0], [3.0, 75.0], [5.0, 100.0]],
    },
    "early": {
        "max_structural_freshness": 65.0,
        "pressure_build": {"min_compression": 65.0, "min_volume_shift": 55.0, "max_expansion": 45.0},
        "trend_resume": {"min_trend": 55.0, "min_reclaim": 40.0, "min_reaccel": 50.0},
        "transition_reclaim": {"min_reclaim": 45.0, "min_volume_shift": 45.0},
    },
    "confirmed": {
        "max_structural_freshness": 55.0,
        "daily_only_min_phase_confidence": 70.0,
        "pressure_build": {"min_reclaim": 55.0, "min_compression": 60.0, "min_volume_shift": 55.0, "max_expansion": 50.0},
        "trend_resume": {"min_reclaim": 50.0, "min_trend": 60.0, "min_reaccel": 55.0},
        "transition_reclaim": {"min_reclaim": 55.0, "min_trend_after_reclaim": 50.0},
    },
    "late": {"min_state_freshness": 60.0},
    "chased": {"min_state_freshness": 85.0, "min_expansion_progress": 80.0},
}

_BUCKET_DEFAULTS = {
    "watchlist": {"min_state_confidence": 50.0},
    "early": {"min_state_confidence": 60.0},
    "confirmed": {"min_state_confidence": 65.0},
}

_PRIORITY_DEFAULTS = {"early_without_pattern_penalty": 15.0}


def _raise_invalid(key: str, value: Any, msg: str) -> None:
    raise ValueError(f"{key} invalid value {value!r}: {msg}")


def _read_nested(cfg: Mapping[str, Any], *keys: str) -> Mapping[str, Any]:
    cur: Any = cfg
    for k in keys:
        cur = cur.get(k, {}) if isinstance(cur, Mapping) else {}
    if not isinstance(cur, Mapping):
        return {}
    return cur


def resolve_independence_universe_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section = _read_nested(raw, "independence_release", "universe")
    merged = _deep_merge_dicts(_INDEPENDENCE_UNIVERSE_DEFAULTS, section)

    list_keys = ["quote_asset_allowed", "mexc_tradeable_status_values"]
    for key in list_keys:
        value = merged.get(key)
        if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x for x in value):
            _raise_invalid(f"independence_release.universe.{key}", value, "must be non-empty list[str]")

    for key in ["listing_age_days_min", "quote_volume_24h_min", "market_cap_usd_min"]:
        value = merged.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
            _raise_invalid(f"independence_release.universe.{key}", value, "must be finite number >= 0")

    merged["listing_age_days_min"] = int(float(merged["listing_age_days_min"]))
    merged["quote_volume_24h_min"] = float(merged["quote_volume_24h_min"])
    merged["market_cap_usd_min"] = float(merged["market_cap_usd_min"])
    return merged


def resolve_independence_market_data_budget_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section = _read_nested(raw, "independence_release", "market_data_budget")
    merged = _deep_merge_dicts(_INDEPENDENCE_MARKET_DATA_BUDGET_DEFAULTS, section)

    max_4h = merged.get("max_4h_fetch_count")
    if isinstance(max_4h, bool) or not isinstance(max_4h, (int, float)) or int(max_4h) < 0:
        _raise_invalid("independence_release.market_data_budget.max_4h_fetch_count", max_4h, "must be integer >= 0")
    merged["max_4h_fetch_count"] = int(max_4h)

    gate = merged["activity_gate"]
    for key in ["daily_quote_volume_active_floor", "min_active_days", "window_days"]:
        value = gate.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            _raise_invalid(f"independence_release.market_data_budget.activity_gate.{key}", value, "must be finite number")
    gate["daily_quote_volume_active_floor"] = float(gate["daily_quote_volume_active_floor"])
    gate["min_active_days"] = int(gate["min_active_days"])
    gate["window_days"] = int(gate["window_days"])
    if gate["window_days"] < 1 or gate["min_active_days"] < 0 or gate["window_days"] < gate["min_active_days"]:
        _raise_invalid("independence_release.market_data_budget.activity_gate.window_days", gate["window_days"], "must be >=1 and >= min_active_days")

    conf = merged["monitoring_bypass"].get("min_phase_confidence")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not math.isfinite(float(conf)) or float(conf) < 0 or float(conf) > 100:
        _raise_invalid("independence_release.market_data_budget.monitoring_bypass.min_phase_confidence", conf, "must be in [0,100]")
    merged["monitoring_bypass"]["min_phase_confidence"] = float(conf)

    pre_filter = merged.get("pre_4h_candidate_filter")
    if not isinstance(pre_filter, Mapping):
        _raise_invalid(
            "independence_release.market_data_budget.pre_4h_candidate_filter",
            pre_filter,
            "must be an object",
        )

    rule_a = pre_filter.get("rule_a")
    if not isinstance(rule_a, Mapping):
        _raise_invalid(
            "independence_release.market_data_budget.pre_4h_candidate_filter.rule_a",
            rule_a,
            "must be an object",
        )
    for key in [
        "close_vs_ema50_1d_pct_min_exclusive",
        "ema20_vs_ema50_1d_pct_min_inclusive",
        "ema20_slope_1d_pct_per_bar_min_exclusive",
    ]:
        value = rule_a.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            _raise_invalid(
                f"independence_release.market_data_budget.pre_4h_candidate_filter.rule_a.{key}",
                value,
                "must be finite number",
            )
        rule_a[key] = float(value)

    rule_b = pre_filter.get("rule_b")
    if not isinstance(rule_b, Mapping):
        _raise_invalid(
            "independence_release.market_data_budget.pre_4h_candidate_filter.rule_b",
            rule_b,
            "must be an object",
        )
    value_b = rule_b.get("volume_1d_current_vs_median10_min_inclusive")
    if isinstance(value_b, bool) or not isinstance(value_b, (int, float)) or not math.isfinite(float(value_b)) or float(value_b) <= 0:
        _raise_invalid(
            "independence_release.market_data_budget.pre_4h_candidate_filter.rule_b.volume_1d_current_vs_median10_min_inclusive",
            value_b,
            "must be finite number > 0",
        )
    rule_b["volume_1d_current_vs_median10_min_inclusive"] = float(value_b)

    rule_c = pre_filter.get("rule_c")
    if not isinstance(rule_c, Mapping):
        _raise_invalid(
            "independence_release.market_data_budget.pre_4h_candidate_filter.rule_c",
            rule_c,
            "must be an object",
        )
    width = rule_c.get("range_width_10bars_1d_pct_max_inclusive")
    if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(float(width)) or float(width) <= 0:
        _raise_invalid(
            "independence_release.market_data_budget.pre_4h_candidate_filter.rule_c.range_width_10bars_1d_pct_max_inclusive",
            width,
            "must be finite number > 0",
        )
    rule_c["range_width_10bars_1d_pct_max_inclusive"] = float(width)

    rc = rule_c.get("close_position_in_range_10bars_1d_min_inclusive")
    if isinstance(rc, bool) or not isinstance(rc, (int, float)) or not math.isfinite(float(rc)) or not (0 <= float(rc) <= 1):
        _raise_invalid(
            "independence_release.market_data_budget.pre_4h_candidate_filter.rule_c.close_position_in_range_10bars_1d_min_inclusive",
            rc,
            "must be in [0,1]",
        )
    rule_c["close_position_in_range_10bars_1d_min_inclusive"] = float(rc)

    return merged


def resolve_independence_ohlcv_fetch_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section = _read_nested(raw, "independence_release", "ohlcv_fetch")
    if section and not isinstance(section, Mapping):
        _raise_invalid("independence_release.ohlcv_fetch", section, "must be an object")
    merged = _deep_merge_dicts(_INDEPENDENCE_OHLCV_FETCH_DEFAULTS, section)

    def _parse_int(key: str, minimum: int, maximum: int) -> int:
        value = merged.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != float(value):
            _raise_invalid(f"independence_release.ohlcv_fetch.{key}", value, "must be an integer")
        ivalue = int(value)
        if ivalue < minimum or ivalue > maximum:
            _raise_invalid(
                f"independence_release.ohlcv_fetch.{key}",
                value,
                f"must be in [{minimum}, {maximum}]",
            )
        merged[key] = ivalue
        return ivalue

    lookback_1d = _parse_int("lookback_bars_1d", 120, 1000)
    lookback_4h = _parse_int("lookback_bars_4h", 120, 1000)
    _parse_int("incremental_max_bars", 1, 500)
    _parse_int("per_call_timeout_s", 5, 300)
    _parse_int("max_retries", 0, 3)
    min_1d = _parse_int("min_lookback_bars_1d", 1, lookback_1d)
    min_4h = _parse_int("min_lookback_bars_4h", 1, lookback_4h)

    if lookback_1d < min_1d:
        _raise_invalid("independence_release.ohlcv_fetch.lookback_bars_1d", lookback_1d, "must be >= min_lookback_bars_1d")
    if lookback_4h < min_4h:
        _raise_invalid("independence_release.ohlcv_fetch.lookback_bars_4h", lookback_4h, "must be >= min_lookback_bars_4h")

    return merged




def _validate_points(path: str, value: Any) -> list[tuple[float, float]]:
    if not isinstance(value, list) or len(value) < 2:
        _raise_invalid(path, value, "must be list with >=2 points")
    out: list[tuple[float, float]] = []
    last_x: float | None = None
    for point in value:
        if (
            not isinstance(point, (list, tuple))
            or len(point) != 2
            or isinstance(point[0], bool)
            or isinstance(point[1], bool)
            or not isinstance(point[0], (int, float))
            or not isinstance(point[1], (int, float))
        ):
            _raise_invalid(path, value, "points must be (x, y) numeric pairs")
        x, y = float(point[0]), float(point[1])
        if not math.isfinite(x) or not math.isfinite(y):
            _raise_invalid(path, value, "point values must be finite")
        if y < 0 or y > 100:
            _raise_invalid(path, value, "y must be in [0,100]")
        if last_x is not None and x <= last_x:
            _raise_invalid(path, value, "x-values must be strictly ascending")
        out.append((x, y))
        last_x = x
    return out


def _validate_weight(path: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        _raise_invalid(path, value, "must be finite number > 0")
    return float(value)


def _validate_linear(path: str, block: Mapping[str, Any], low_key: str, mid_key: str, high_key: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for key in [low_key, mid_key, high_key]:
        val = block.get(key)
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(float(val)):
            _raise_invalid(f"{path}.{key}", val, "must be finite number")
        out[key] = float(val)
    if not out[low_key] < out[mid_key] < out[high_key]:
        _raise_invalid(path, block, f"must satisfy {low_key} < {mid_key} < {high_key}")
    return out


def resolve_axes_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section_raw = raw.get("axes")
    if section_raw is None:
        section: Mapping[str, Any] = {}
    elif not isinstance(section_raw, Mapping):
        _raise_invalid("axes", section_raw, "must be an object")
    else:
        section = section_raw

    merged = _deep_merge_dicts(_AXES_DEFAULTS, section)

    ratio = merged.get("min_effective_weight_ratio", 0.60)
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(float(ratio)):
        _raise_invalid("axes.min_effective_weight_ratio", ratio, "must be finite number")
    ratio_f = float(ratio)
    if ratio_f <= 0 or ratio_f > 1.0:
        _raise_invalid("axes.min_effective_weight_ratio", ratio, "must satisfy 0 < value <= 1.0")
    merged["min_effective_weight_ratio"] = ratio_f

    for field in [
        "close_vs_ema20_1d_pct", "close_vs_ema50_1d_pct", "close_vs_ema20_4h_pct", "close_vs_ema50_4h_pct",
        "ema20_slope_1d_pct_per_bar", "ema20_slope_4h_pct_per_bar", "ema20_vs_ema50_1d_pct", "ema20_vs_ema50_4h_pct",
    ]:
        block = merged["trend_strength"].get(field)
        if not isinstance(block, Mapping):
            _raise_invalid(f"axes.trend_strength.{field}", block, "must be an object")
        vals = _validate_linear(f"axes.trend_strength.{field}", block, "low", "mid", "high")
        vals["weight"] = _validate_weight(f"axes.trend_strength.{field}.weight", block.get("weight"))
        merged["trend_strength"][field] = vals

    reclaim = merged["reclaim_progress"]
    if not isinstance(reclaim, Mapping):
        _raise_invalid("axes.reclaim_progress", reclaim, "must be an object")
    dist = reclaim.get("distance")
    if not isinstance(dist, Mapping):
        _raise_invalid("axes.reclaim_progress.distance", dist, "must be an object")
    reclaim["distance"] = _validate_linear("axes.reclaim_progress.distance", dist, "low", "mid", "high")
    reclaim["hold_points"] = _validate_points("axes.reclaim_progress.hold_points", reclaim.get("hold_points"))
    anchors = reclaim.get("anchors")
    if not isinstance(anchors, Mapping):
        _raise_invalid("axes.reclaim_progress.anchors", anchors, "must be an object")
    for key in ["ema20_4h", "ema50_4h", "ema20_1d", "ema50_1d", "fixed_structural_4h"]:
        anchor = anchors.get(key)
        if not isinstance(anchor, Mapping):
            _raise_invalid(f"axes.reclaim_progress.anchors.{key}", anchor, "must be an object")
        anchors[key] = {"weight": _validate_weight(f"axes.reclaim_progress.anchors.{key}.weight", anchor.get("weight"))}
    reclaim["anchors"] = dict(anchors)
    merged["reclaim_progress"] = dict(reclaim)

    for axis_key, fields in {
        "compression_strength": [
            ("bb_width_rank_120_4h", "low_good", "mid", "high_bad"),
            ("atr_pct_rank_120_1d", "low_good", "mid", "high_bad"),
            ("range_width_12bars_4h_vs_atr1d_pct", "low_good", "mid", "high_bad"),
            ("std_return_rank_12bars_4h_pct", "low_good", "mid", "high_bad"),
        ],
    }.items():
        block = merged.get(axis_key)
        if not isinstance(block, Mapping):
            _raise_invalid(f"axes.{axis_key}", block, "must be an object")
        for field, low, mid, high in fields:
            item = block.get(field)
            if not isinstance(item, Mapping):
                _raise_invalid(f"axes.{axis_key}.{field}", item, "must be an object")
            vals = _validate_linear(f"axes.{axis_key}.{field}", item, low, mid, high)
            vals["weight"] = _validate_weight(f"axes.{axis_key}.{field}.weight", item.get("weight"))
            block[field] = vals
        merged[axis_key] = dict(block)

    for axis_key, fields in {
        "expansion_progress_structural": [
            "move_from_last_structural_break_pct", "bars_since_last_structural_break_4h", "dist_to_base_mid_pct", "dist_to_ema20_4h_pct_abs",
        ],
        "volume_regime_shift": ["volume_spike_persistence_4h", "volume_4h_current_vs_median10"],
        "freshness_distance_structural": [
            "distance_to_last_structural_anchor_pct_abs", "distance_to_range_high_pct_abs", "bars_since_last_volume_shift_4h", "bars_since_last_structural_break_4h",
        ],
    }.items():
        block = merged.get(axis_key)
        if not isinstance(block, Mapping):
            _raise_invalid(f"axes.{axis_key}", block, "must be an object")
        for field in fields:
            item = block.get(field)
            if not isinstance(item, Mapping):
                _raise_invalid(f"axes.{axis_key}.{field}", item, "must be an object")
            item_vals = {
                "points": _validate_points(f"axes.{axis_key}.{field}.points", item.get("points")),
                "weight": _validate_weight(f"axes.{axis_key}.{field}.weight", item.get("weight")),
            }
            block[field] = item_vals
        merged[axis_key] = dict(block)

    volume = merged.get("volume_regime_shift")
    if not isinstance(volume, Mapping):
        _raise_invalid("axes.volume_regime_shift", volume, "must be an object")
    for field in ["volume_quote_spike_1d", "volume_quote_spike_4h"]:
        item = volume.get(field)
        if not isinstance(item, Mapping):
            _raise_invalid(f"axes.volume_regime_shift.{field}", item, "must be an object")
        vals = _validate_linear(f"axes.volume_regime_shift.{field}", item, "low", "mid", "high")
        vals["weight"] = _validate_weight(f"axes.volume_regime_shift.{field}.weight", item.get("weight"))
        volume[field] = vals
    merged["volume_regime_shift"] = dict(volume)

    for axis_key, fields in {
        "base_integrity_simplified": [
            ("bars_since_last_new_low_4h", "points"),
            ("range_width_12bars_4h_pct", "inv"),
            ("close_position_in_range_12bars_4h", "points"),
            ("close_above_range_mid_ratio_12bars_4h", "points"),
            ("bars_since_last_new_low_1d", "points"),
            ("range_width_10bars_1d_pct", "inv"),
            ("close_position_in_range_10bars_1d", "points"),
            ("close_above_range_mid_ratio_10bars_1d", "points"),
        ],
        "pullback_quality_simplified": [
            ("pullback_depth_vs_last_impulse_pct_4h", "points"),
            ("pullback_volume_ratio_4h", "points"),
            ("close_vs_ema20_4h_pct", "lin"),
            ("lowest_low_vs_ema20_4h_pct", "lin"),
            ("pullback_depth_vs_last_impulse_pct_1d", "points"),
            ("pullback_volume_ratio_1d", "points"),
            ("close_vs_ema20_1d_pct", "lin"),
            ("lowest_low_vs_ema20_1d_pct", "lin"),
        ],
        "reacceleration_strength_simplified": [
            ("close_vs_rolling_high_5_4h_pct", "lin"),
            ("volume_4h_current_vs_median10", "points"),
            ("ema20_slope_4h_pct_per_bar", "lin"),
            ("close_vs_ema20_4h_pct", "lin"),
            ("close_vs_rolling_high_5_1d_pct", "lin"),
            ("volume_1d_current_vs_median10", "points"),
            ("ema20_slope_1d_pct_per_bar", "lin"),
            ("close_vs_ema20_1d_pct", "lin"),
        ],
    }.items():
        block = merged.get(axis_key)
        if not isinstance(block, Mapping):
            _raise_invalid(f"axes.{axis_key}", block, "must be an object")
        for field, kind in fields:
            item = block.get(field)
            if not isinstance(item, Mapping):
                _raise_invalid(f"axes.{axis_key}.{field}", item, "must be an object")
            if kind == "points":
                block[field] = {"points": _validate_points(f"axes.{axis_key}.{field}.points", item.get("points"))}
            elif kind == "inv":
                block[field] = _validate_linear(f"axes.{axis_key}.{field}", item, "low_good", "mid", "high_bad")
            else:
                block[field] = _validate_linear(f"axes.{axis_key}.{field}", item, "low", "mid", "high")
        merged[axis_key] = dict(block)

    return merged


def resolve_feature_layer_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section_raw = raw.get("features")
    if section_raw is None:
        section: Mapping[str, Any] = {}
    elif not isinstance(section_raw, Mapping):
        _raise_invalid("features", section_raw, "must be an object")
    else:
        section = section_raw

    merged = _deep_merge_dicts(_FEATURE_LAYER_DEFAULTS, section)

    for key in ["segmentation_window_4h", "segmentation_window_1d"]:
        value = merged.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != float(value) or int(value) < 2:
            _raise_invalid(f"features.{key}", value, "must be integer >= 2")
        merged[key] = int(value)

    for key in ["volume_shift_lookback_4h", "range_high_lookback_4h"]:
        value = merged.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != float(value) or int(value) < 1:
            _raise_invalid(f"features.{key}", value, "must be integer >= 1")
        merged[key] = int(value)

    pst = merged.get("persistence_spike_threshold")
    if isinstance(pst, bool) or not isinstance(pst, (int, float)) or not math.isfinite(float(pst)) or float(pst) <= 0:
        _raise_invalid("features.persistence_spike_threshold", pst, "must be finite > 0")
    merged["persistence_spike_threshold"] = float(pst)

    sb = merged.get("structural_break")
    if not isinstance(sb, Mapping):
        _raise_invalid("features.structural_break", sb, "must be an object")
    mbb = sb.get("min_bars_below_before_break", 3)
    if isinstance(mbb, bool) or not isinstance(mbb, (int, float)) or int(mbb) != float(mbb) or int(mbb) < 1:
        _raise_invalid(
            "features.structural_break.min_bars_below_before_break",
            mbb,
            "must be integer >= 1",
        )
    merged["structural_break"] = {"min_bars_below_before_break": int(mbb)}
    return merged


def resolve_phase_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section_raw = raw.get("phase")
    if section_raw is None:
        section: Mapping[str, Any] = {}
    elif not isinstance(section_raw, Mapping):
        _raise_invalid("phase", section_raw, "must be an object")
    else:
        section = section_raw

    merged = _deep_merge_dicts(_PHASE_DEFAULTS, section)

    def _parse_ratio(key: str, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            _raise_invalid(key, value, "must be finite number")
        parsed = float(value)
        if parsed <= 0 or parsed > 1:
            _raise_invalid(key, value, "must satisfy 0 < value <= 1")
        return parsed

    def _parse_0_100(key: str, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            _raise_invalid(key, value, "must be finite number")
        parsed = float(value)
        if parsed < 0 or parsed > 100:
            _raise_invalid(key, value, "must be in [0,100]")
        return parsed

    merged["min_effective_weight_ratio"] = _parse_ratio(
        "phase.min_effective_weight_ratio", merged.get("min_effective_weight_ratio")
    )
    merged["global_confidence_floor"] = _parse_0_100(
        "phase.global_confidence_floor", merged.get("global_confidence_floor")
    )
    merged["reduced_resolution_confidence_cap"] = _parse_0_100(
        "phase.reduced_resolution_confidence_cap", merged.get("reduced_resolution_confidence_cap")
    )
    merged["phase_gap_floor"] = _parse_0_100("phase.phase_gap_floor", merged.get("phase_gap_floor"))

    for phase_name, keys in {
        "pressure_build": ["floor_compression", "floor_volume_shift", "max_expansion"],
        "trend_resume": ["floor_trend", "floor_reclaim", "max_expansion"],
        "transition_reclaim": ["floor_reclaim", "floor_volume_shift", "max_expansion"],
    }.items():
        block = merged.get(phase_name)
        if not isinstance(block, Mapping):
            _raise_invalid(f"phase.{phase_name}", block, "must be an object")
        normalized: Dict[str, float] = {}
        for key in keys:
            normalized[key] = _parse_0_100(f"phase.{phase_name}.{key}", block.get(key))
        merged[phase_name] = normalized

    return merged


def resolve_invalidation_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section_raw = raw.get("invalidation")
    if section_raw is None:
        section = {}
    elif not isinstance(section_raw, Mapping):
        _raise_invalid("invalidation", section_raw, "must be an object")
    else:
        section = section_raw

    merged = _deep_merge_dicts(_INVALIDATION_DEFAULTS, section)

    def _parse_0_100(key: str, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            _raise_invalid(key, value, "must be finite number")
        parsed = float(value)
        if parsed < 0 or parsed > 100:
            _raise_invalid(key, value, "must be in [0,100]")
        return parsed

    merged["max_state_freshness"] = _parse_0_100("invalidation.max_state_freshness", merged.get("max_state_freshness"))
    merged["max_expansion_progress"] = _parse_0_100("invalidation.max_expansion_progress", merged.get("max_expansion_progress"))
    merged["max_structural_freshness"] = _parse_0_100("invalidation.max_structural_freshness", merged.get("max_structural_freshness"))

    for phase_name, keys in {
        "pressure_build": ["min_compression_hold", "min_base_hold", "min_volume_shift_hold"],
        "trend_resume": ["min_trend_hold", "min_reclaim_hold", "min_pullback_hold", "min_reaccel_hold"],
        "transition_reclaim": ["min_reclaim_hold", "min_base_hold", "min_volume_shift_hold"],
    }.items():
        block = merged.get(phase_name)
        if not isinstance(block, Mapping):
            _raise_invalid(f"invalidation.{phase_name}", block, "must be an object")
        normalized: Dict[str, float] = {}
        for key in keys:
            normalized[key] = _parse_0_100(f"invalidation.{phase_name}.{key}", block.get(key))
        merged[phase_name] = normalized
    return merged


def resolve_cycle_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section_raw = raw.get("cycle")
    if section_raw is None:
        section = {}
    elif not isinstance(section_raw, Mapping):
        _raise_invalid("cycle", section_raw, "must be an object")
    else:
        section = section_raw

    merged = _deep_merge_dicts(_CYCLE_DEFAULTS, section)

    expansion_reset_max = merged.get("expansion_reset_max")
    if (
        isinstance(expansion_reset_max, bool)
        or not isinstance(expansion_reset_max, (int, float))
        or not math.isfinite(float(expansion_reset_max))
        or float(expansion_reset_max) < 0
        or float(expansion_reset_max) > 100
    ):
        _raise_invalid("cycle.expansion_reset_max", expansion_reset_max, "must be finite number in [0,100]")
    merged["expansion_reset_max"] = float(expansion_reset_max)

    min_bars = merged.get("min_bars_since_cycle_end")
    if isinstance(min_bars, bool) or not isinstance(min_bars, int) or min_bars < 0:
        _raise_invalid("cycle.min_bars_since_cycle_end", min_bars, "must be integer >= 0")
    merged["min_bars_since_cycle_end"] = min_bars

    enable_reclaim = merged.get("enable_reclaim_reset")
    if not isinstance(enable_reclaim, bool):
        _raise_invalid("cycle.enable_reclaim_reset", enable_reclaim, "must be bool")
    merged["enable_reclaim_reset"] = enable_reclaim
    return merged


def resolve_state_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    section_raw = raw.get("state")
    if section_raw is None:
        section = {}
    elif not isinstance(section_raw, Mapping):
        _raise_invalid("state", section_raw, "must be an object")
    else:
        section = section_raw
    merged = _deep_merge_dicts(_STATE_DEFAULTS, section)

    def _parse_0_100(key: str, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            _raise_invalid(key, value, "must be finite number")
        parsed = float(value)
        if parsed < 0 or parsed > 100:
            _raise_invalid(key, value, "must be in [0,100]")
        return parsed

    def _parse_points(key: str, value: Any) -> list[list[float]]:
        if not isinstance(value, list) or not value:
            _raise_invalid(key, value, "must be non-empty list of [x,y] points")
        out: list[list[float]] = []
        prev_x: float | None = None
        for point in value:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                _raise_invalid(key, value, "each point must be [x,y]")
            x, y = point
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(float(x)):
                _raise_invalid(key, x, "x must be finite number")
            yv = _parse_0_100(key, y)
            xf = float(x)
            if prev_x is not None and xf <= prev_x:
                _raise_invalid(key, value, "x values must be strictly ascending")
            prev_x = xf
            out.append([xf, yv])
        return out

    merged["confidence"]["blended_penalty"] = _parse_0_100("state.confidence.blended_penalty", merged["confidence"]["blended_penalty"])
    merged["confidence"]["not_full_resolution_penalty"] = _parse_0_100(
        "state.confidence.not_full_resolution_penalty", merged["confidence"]["not_full_resolution_penalty"]
    )
    merged["freshness"]["bars_points"] = _parse_points("state.freshness.bars_points", merged["freshness"]["bars_points"])
    merged["freshness"]["distance_points"] = _parse_points(
        "state.freshness.distance_points", merged["freshness"]["distance_points"]
    )
    merged["late"]["min_state_freshness"] = _parse_0_100("state.late.min_state_freshness", merged["late"]["min_state_freshness"])
    merged["chased"]["min_state_freshness"] = _parse_0_100("state.chased.min_state_freshness", merged["chased"]["min_state_freshness"])
    merged["chased"]["min_expansion_progress"] = _parse_0_100(
        "state.chased.min_expansion_progress", merged["chased"]["min_expansion_progress"]
    )
    return merged




def resolve_entry_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    independence_release = raw.get("independence_release", {})
    if independence_release is None:
        independence_release = {}
    if not isinstance(independence_release, Mapping):
        _raise_invalid("independence_release", independence_release, "must be a mapping")

    section = independence_release.get("entry", {})
    if section is None:
        section = {}
    if not isinstance(section, Mapping):
        _raise_invalid("independence_release.entry", section, "must be a mapping")

    for phase_name, phase_override in section.items():
        if not isinstance(phase_override, Mapping):
            _raise_invalid(
                f"independence_release.entry.{phase_name}",
                phase_override,
                "must be a mapping",
            )
        for pattern_name, pattern_override in phase_override.items():
            if not isinstance(pattern_override, Mapping):
                _raise_invalid(
                    f"independence_release.entry.{phase_name}.{pattern_name}",
                    pattern_override,
                    "must be a mapping",
                )

    merged = _deep_merge_dicts(_ENTRY_DEFAULTS, section)

    def _parse_0_100(field: str, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            _raise_invalid(field, value, "must be finite number")
        v = float(value)
        if v < 0.0 or v > 100.0:
            _raise_invalid(field, value, "must be in [0,100]")
        return v

    for phase_name, phase_defaults in _ENTRY_DEFAULTS.items():
        phase_cfg = merged.get(phase_name, {})
        if not isinstance(phase_cfg, Mapping):
            _raise_invalid(f"independence_release.entry.{phase_name}", phase_cfg, "must be a mapping")
        for pattern_name in phase_defaults:
            pattern_cfg = phase_cfg.get(pattern_name, {})
            if not isinstance(pattern_cfg, Mapping):
                _raise_invalid(
                    f"independence_release.entry.{phase_name}.{pattern_name}",
                    pattern_cfg,
                    "must be a mapping",
                )
            for key, value in pattern_cfg.items():
                pattern_cfg[key] = _parse_0_100(f"independence_release.entry.{phase_name}.{pattern_name}.{key}", value)

    bh_cfg = merged["pressure_build"]["break_and_hold"]
    if bh_cfg["min_expansion"] >= bh_cfg["max_expansion"]:
        _raise_invalid(
            "independence_release.entry.pressure_build.break_and_hold.min_expansion",
            bh_cfg["min_expansion"],
            "must be strictly less than max_expansion",
        )

    return merged

def _deep_merge_dicts(base: Mapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {key: value for key, value in base.items()}
    for key, value in override.items():
        if key in merged and isinstance(merged[key], Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_independence_release_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    configured = raw.get("independence_release")
    if configured is None:
        configured = {}
    elif not isinstance(configured, Mapping):
        raise ValueError(
            f"independence_release must be an object, got {configured!r}"
        )

    merged = _deep_merge_dicts(_INDEPENDENCE_RELEASE_SECTION_DEFAULTS, configured)

    for key, value in merged.items():
        if not isinstance(value, Mapping):
            raise ValueError(f"independence_release.{key} must be an object, got {value!r}")
        merged[key] = dict(value)

    return merged


def resolve_independence_release_reports_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    configured = _read_nested(raw, "independence_release", "reports")
    if configured is None:
        configured = {}
    if not isinstance(configured, Mapping):
        _raise_invalid("independence_release.reports", configured, "must be an object")

    merged = _deep_merge_dicts(_INDEPENDENCE_REPORTS_DEFAULTS, configured)

    recent_runs_limit = merged.get("recent_runs_limit")
    if isinstance(recent_runs_limit, bool) or not isinstance(recent_runs_limit, int) or recent_runs_limit <= 0:
        _raise_invalid(
            "independence_release.reports.recent_runs_limit",
            recent_runs_limit,
            "must be integer > 0",
        )

    for key in ("emit_report_md", "emit_report_xlsx"):
        value = merged.get(key)
        if not isinstance(value, bool):
            _raise_invalid(f"independence_release.reports.{key}", value, "must be bool")

    return {
        "recent_runs_limit": recent_runs_limit,
        "emit_report_md": bool(merged["emit_report_md"]),
        "emit_report_xlsx": bool(merged["emit_report_xlsx"]),
    }


def resolve_risk_min_rr_to_target_1(risk_cfg: Mapping[str, Any] | None) -> float:
    """Resolve RR threshold with canonical-key precedence and legacy alias fallback."""
    cfg = risk_cfg if isinstance(risk_cfg, Mapping) else {}

    if "min_rr_to_target_1" in cfg:
        value = cfg.get("min_rr_to_target_1")
        source = "risk.min_rr_to_target_1"
    elif "min_rr_to_tp10" in cfg:
        value = cfg.get("min_rr_to_tp10")
        source = "risk.min_rr_to_tp10"
    else:
        return 1.3

    if isinstance(value, bool) or value is None:
        raise ValueError(f"{source} must be numeric")

    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source} must be numeric") from exc

    if not math.isfinite(parsed):
        raise ValueError(f"{source} must be finite")
    if parsed < 0:
        raise ValueError(f"{source} ({parsed}) must be >= 0")

    return parsed


def resolve_risk_max_stop_distance_pct(risk_cfg: Mapping[str, Any] | None, setup_type: str | None = None) -> float:
    """Resolve max stop-distance threshold from scalar or setup-specific config."""
    cfg = risk_cfg if isinstance(risk_cfg, Mapping) else {}
    raw_value = cfg.get("max_stop_distance_pct", 12.0)

    def _parse(field_name: str, value: Any) -> float:
        if isinstance(value, bool) or value is None:
            raise ValueError(f"{field_name} must be numeric")
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
        if not math.isfinite(parsed):
            raise ValueError(f"{field_name} must be finite")
        if parsed < 0:
            raise ValueError(f"{field_name} ({parsed}) must be >= 0")
        return parsed

    if isinstance(raw_value, Mapping):
        if "default" not in raw_value:
            raise ValueError("risk.max_stop_distance_pct.default is required when risk.max_stop_distance_pct is an object")
        selected_key = setup_type if isinstance(setup_type, str) and setup_type in raw_value else "default"
        return _parse(f"risk.max_stop_distance_pct.{selected_key}", raw_value.get(selected_key))

    return _parse("risk.max_stop_distance_pct", raw_value)


def resolve_bucket_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    configured = raw.get("bucket")
    if configured is None:
        configured = {}
    if not isinstance(configured, Mapping):
        raise ValueError("bucket must be an object")

    merged = _deep_merge_dicts(_BUCKET_DEFAULTS, configured)
    resolved: Dict[str, Any] = {}
    for key in ["watchlist", "early", "confirmed"]:
        block = merged.get(key)
        if not isinstance(block, Mapping):
            raise ValueError(f"bucket.{key} must be an object")
        value = block.get("min_state_confidence")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"bucket.{key}.min_state_confidence must be numeric")
        number = float(value)
        if not math.isfinite(number) or number < 0.0 or number > 100.0:
            raise ValueError(f"bucket.{key}.min_state_confidence must be in [0,100]")
        resolved[key] = {"min_state_confidence": number}
    return resolved


def resolve_priority_config(raw: Mapping[str, Any]) -> Dict[str, Any]:
    configured = raw.get("priority")
    if configured is None:
        configured = {}
    if not isinstance(configured, Mapping):
        raise ValueError("priority must be an object")

    merged = _deep_merge_dicts(_PRIORITY_DEFAULTS, configured)
    value = merged.get("early_without_pattern_penalty")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("priority.early_without_pattern_penalty must be numeric")
    penalty = float(value)
    if not math.isfinite(penalty) or penalty < 0.0 or penalty > 100.0:
        raise ValueError("priority.early_without_pattern_penalty must be in [0,100]")
    return {"early_without_pattern_penalty": penalty}


@dataclass
class ScannerConfig:
    """
    Scanner configuration wrapper.
    Provides type-safe access to config values.
    """

    raw: Dict[str, Any]

    @property
    def independence_release(self) -> Dict[str, Any]:
        value = self.raw.get("independence_release", {})
        return dict(value) if isinstance(value, dict) else _normalize_independence_release_config(self.raw)

    # Version
    @property
    def independence_ohlcv_fetch(self) -> Dict[str, Any]:
        return resolve_independence_ohlcv_fetch_config(self.raw)

    @property
    def feature_layer_config(self) -> Dict[str, Any]:
        return resolve_feature_layer_config(self.raw)


    @property
    def axes(self) -> Dict[str, Any]:
        return resolve_axes_config(self.raw)

    @property
    def phase(self) -> Dict[str, Any]:
        return resolve_phase_config(self.raw)

    @property
    def invalidation(self) -> Dict[str, Any]:
        return resolve_invalidation_config(self.raw)

    @property
    def cycle(self) -> Dict[str, Any]:
        return resolve_cycle_config(self.raw)

    @property
    def state(self) -> Dict[str, Any]:
        return resolve_state_config(self.raw)

    @property
    def entry(self) -> Dict[str, Any]:
        return resolve_entry_config(self.raw)

    @property
    def bucket(self) -> Dict[str, Any]:
        return resolve_bucket_config(self.raw)

    @property
    def priority(self) -> Dict[str, Any]:
        return resolve_priority_config(self.raw)

    @property
    def spec_version(self) -> str:
        return self.raw.get("version", {}).get("spec", "1.0")

    @property
    def config_version(self) -> str:
        return self.raw.get("version", {}).get("config", "1.0")

    # General
    @property
    def run_mode(self) -> str:
        return self.raw.get("general", {}).get("run_mode", "standard")

    @property
    def timezone(self) -> str:
        return self.raw.get("general", {}).get("timezone", "UTC")

    @property
    def shortlist_size(self) -> int:
        budget_cfg = self.raw.get("budget", {})
        if "shortlist_size" in budget_cfg:
            return budget_cfg.get("shortlist_size", 200)
        if "shortlist_size" in self.raw.get("general", {}):
            return self.raw.get("general", {}).get("shortlist_size", 100)
        return 200

    @property
    def lookback_days_1d(self) -> int:
        return self.raw.get("general", {}).get("lookback_days_1d", 120)

    @property
    def lookback_days_4h(self) -> int:
        return self.raw.get("general", {}).get("lookback_days_4h", 30)

    # Data Sources
    @property
    def mexc_enabled(self) -> bool:
        return self.raw.get("data_sources", {}).get("mexc", {}).get("enabled", True)

    @property
    def cmc_api_key(self) -> str:
        """Get CMC API key from ENV or config."""
        env_var = self.raw.get("data_sources", {}).get("market_cap", {}).get("api_key_env_var", "CMC_API_KEY")
        return os.getenv(env_var, "")

    # Budget
    def _budget_mapping(self) -> Dict[str, Any]:
        budget_cfg = self.raw.get("budget")
        if isinstance(budget_cfg, dict):
            return budget_cfg
        return {}

    @property
    def budget_shortlist_size(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get("shortlist_size", _BUDGET_DEFAULTS["shortlist_size"]),
            "budget.shortlist_size",
        )

    @property
    def budget_orderbook_top_k(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get("orderbook_top_k", _BUDGET_DEFAULTS["orderbook_top_k"]),
            "budget.orderbook_top_k",
        )

    @property
    def pre_shortlist_market_cap_floor_usd(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get(
                "pre_shortlist_market_cap_floor_usd",
                _BUDGET_DEFAULTS["pre_shortlist_market_cap_floor_usd"],
            ),
            "budget.pre_shortlist_market_cap_floor_usd",
        )

    # Universe Filters (legacy soft priors)
    @property
    def market_cap_min(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("min_usd", 100_000_000)

    @property
    def market_cap_max(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("max_usd", 10_000_000_000)

    @property
    def min_turnover_24h(self) -> float:
        return float(self.raw.get("universe_filters", {}).get("volume", {}).get("min_turnover_24h", 0.03))

    @property
    def min_mexc_quote_volume_24h_usdt(self) -> float:
        volume_cfg = self.raw.get("universe_filters", {}).get("volume", {})
        if "min_mexc_quote_volume_24h_usdt" in volume_cfg:
            return float(volume_cfg.get("min_mexc_quote_volume_24h_usdt", 5_000_000))
        return float(volume_cfg.get("min_quote_volume_24h", 5_000_000))

    @property
    def min_mexc_share_24h(self) -> float:
        return float(self.raw.get("universe_filters", {}).get("volume", {}).get("min_mexc_share_24h", 0.01))

    @property
    def min_quote_volume_24h(self) -> float:
        """Backward-compatible alias for runtime metadata export."""
        return self.min_mexc_quote_volume_24h_usdt

    @property
    def scoring_volume_source(self) -> str:
        return str(self.raw.get("scoring", {}).get("volume_source", "mexc"))

    @property
    def min_history_days_1d(self) -> int:
        return self.raw.get("universe_filters", {}).get("history", {}).get("min_history_days_1d", 60)

    # Tradeability
    @property
    def tradeability_enabled(self) -> bool:
        return self.raw.get("tradeability", {}).get("enabled", True)

    @property
    def tradeability_notional_total_usdt(self) -> float:
        return float(self.raw.get("tradeability", {}).get("notional_total_usdt", 20_000))

    @property
    def tradeability_notional_chunk_usdt(self) -> float:
        return float(self.raw.get("tradeability", {}).get("notional_chunk_usdt", 5_000))

    @property
    def tradeability_max_tranches(self) -> int:
        return int(self.raw.get("tradeability", {}).get("max_tranches", 4))

    @property
    def tradeability_band_pct(self) -> float:
        return float(self.raw.get("tradeability", {}).get("band_pct", 1.0))

    @property
    def tradeability_max_spread_pct(self) -> float:
        return float(self.raw.get("tradeability", {}).get("max_spread_pct", 0.15))

    @property
    def tradeability_min_depth_1pct_usd(self) -> float:
        return float(self.raw.get("tradeability", {}).get("min_depth_1pct_usd", 200_000))

    @property
    def tradeability_class_thresholds(self) -> Dict[str, Any]:
        return self.raw.get("tradeability", {}).get(
            "class_thresholds",
            {
                "direct_ok_max_slippage_bps": 50,
                "tranche_ok_max_slippage_bps": 100,
                "marginal_max_slippage_bps": 150,
            },
        )

    # Risk
    @property
    def risk_enabled(self) -> bool:
        return self.raw.get("risk", {}).get("enabled", True)

    @property
    def risk_stop_method(self) -> str:
        return str(self.raw.get("risk", {}).get("stop_method", "atr_multiple"))

    @property
    def risk_atr_period(self) -> int:
        return int(self.raw.get("risk", {}).get("atr_period", 14))

    @property
    def risk_atr_timeframe(self) -> str:
        return str(self.raw.get("risk", {}).get("atr_timeframe", "1d"))

    @property
    def risk_atr_multiple(self) -> float:
        return float(self.raw.get("risk", {}).get("atr_multiple", 2.0))

    @property
    def risk_min_stop_distance_pct(self) -> float:
        return float(self.raw.get("risk", {}).get("min_stop_distance_pct", 4.0))

    @property
    def risk_max_stop_distance_pct(self) -> float:
        risk_cfg = self.raw.get("risk", {})
        return resolve_risk_max_stop_distance_pct(risk_cfg if isinstance(risk_cfg, Mapping) else {}, setup_type=None)

    def risk_max_stop_distance_pct_for_setup(self, setup_type: str) -> float:
        risk_cfg = self.raw.get("risk", {})
        return resolve_risk_max_stop_distance_pct(risk_cfg if isinstance(risk_cfg, Mapping) else {}, setup_type=setup_type)

    @property
    def risk_min_rr_to_target_1(self) -> float:
        risk_cfg = self.raw.get("risk", {})
        return resolve_risk_min_rr_to_target_1(risk_cfg if isinstance(risk_cfg, Mapping) else {})

    @property
    def risk_min_rr_to_tp10(self) -> float:
        """Backward-compatible alias for the canonical risk_min_rr_to_target_1 accessor."""
        return self.risk_min_rr_to_target_1

    # Decision
    @property
    def decision_enabled(self) -> bool:
        return self.raw.get("decision", {}).get("enabled", True)

    @property
    def decision_min_score_for_enter(self) -> int:
        return int(self.raw.get("decision", {}).get("min_score_for_enter", 65))

    @property
    def decision_min_score_for_wait(self) -> int:
        return int(self.raw.get("decision", {}).get("min_score_for_wait", 40))

    @property
    def decision_require_tradeability_for_enter(self) -> bool:
        return self.raw.get("decision", {}).get("require_tradeability_for_enter", True)

    @property
    def decision_require_risk_acceptable_for_enter(self) -> bool:
        return self.raw.get("decision", {}).get("require_risk_acceptable_for_enter", True)

    @property
    def decision_min_effective_rr_to_target_2_for_enter(self) -> float:
        return float(self.raw.get("decision", {}).get("min_effective_rr_to_target_2_for_enter", 1.0))

    # BTC regime
    @property
    def btc_regime_enabled(self) -> bool:
        return self.raw.get("btc_regime", {}).get("enabled", True)

    @property
    def btc_regime_mode(self) -> str:
        return str(self.raw.get("btc_regime", {}).get("mode", "threshold_modifier"))

    @property
    def btc_regime_risk_off_enter_boost(self) -> float:
        return float(self.raw.get("btc_regime", {}).get("risk_off_enter_boost", 15))

    # Shadow mode
    @property
    def shadow_mode(self) -> str:
        shadow_cfg = self.raw.get("shadow")
        if isinstance(shadow_cfg, dict):
            return str(shadow_cfg.get("mode", "parallel"))
        return "parallel"

    # Exclusions
    @property
    def exclude_stablecoins(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_stablecoins", True)

    @property
    def exclude_wrapped(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_wrapped_tokens", True)

    @property
    def exclude_leveraged(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_leveraged_tokens", True)

    # Logging
    @property
    def log_level(self) -> str:
        return self.raw.get("logging", {}).get("level", "INFO")

    @property
    def log_to_file(self) -> bool:
        return self.raw.get("logging", {}).get("log_to_file", True)

    @property
    def log_file(self) -> str:
        return self.raw.get("logging", {}).get("file", "logs/scanner.log")


def load_config(path: str | Path | None = None) -> ScannerConfig:
    """
    Load configuration from YAML file.

    Args:
        path: Path to config.yml (default: config/config.yml)

    Returns:
        ScannerConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config is invalid YAML
    """
    cfg_path = Path(path) if path else Path(CONFIG_PATH)

    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(f"config root must be a mapping, got {raw!r}")

    raw = dict(raw)
    raw["independence_release"] = _normalize_independence_release_config(raw)
    resolve_independence_ohlcv_fetch_config(raw)
    resolve_axes_config(raw)
    resolve_bucket_config(raw)
    resolve_priority_config(raw)

    return ScannerConfig(raw=raw)


def _expect_number(errors: List[str], value: Any, field_name: str, *, minimum: float | None = None, maximum: float | None = None) -> float | None:
    if isinstance(value, bool) or value is None:
        errors.append(f"{field_name} must be numeric")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be numeric")
        return None

    if not math.isfinite(number):
        errors.append(f"{field_name} must be finite")
        return None

    if minimum is not None and number < minimum:
        errors.append(f"{field_name} ({number}) must be >= {minimum}")
    if maximum is not None and number > maximum:
        errors.append(f"{field_name} ({number}) must be <= {maximum}")
    return number


def _expect_integer_number(
    errors: List[str],
    value: Any,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> int | None:
    number = _expect_number(errors, value, field_name, minimum=minimum, maximum=maximum)
    if number is None:
        return None
    if not number.is_integer():
        errors.append(f"{field_name} must be an integer")
        return None
    return int(number)


def _parse_integer_budget_value(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be numeric")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if not number.is_integer():
        raise ValueError(f"{field_name} must be an integer")

    return int(number)


def validate_config(config: ScannerConfig) -> List[str]:
    """
    Validate configuration.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check run_mode
    valid_modes = ["standard", "fast", "offline", "backtest"]
    if config.run_mode not in valid_modes:
        errors.append(f"Invalid run_mode: {config.run_mode}. Must be one of {valid_modes}")

    # Check market cap range
    if config.market_cap_min >= config.market_cap_max:
        errors.append(f"market_cap_min ({config.market_cap_min}) must be < market_cap_max ({config.market_cap_max})")

    # Check CMC API key (if needed)
    if not config.cmc_api_key and config.run_mode == "standard":
        errors.append("CMC_API_KEY environment variable not set")

    # Universe volume-gate configuration
    if config.min_turnover_24h < 0:
        errors.append(f"min_turnover_24h ({config.min_turnover_24h}) must be >= 0")

    if config.min_mexc_quote_volume_24h_usdt < 0:
        errors.append(
            f"min_mexc_quote_volume_24h_usdt ({config.min_mexc_quote_volume_24h_usdt}) must be >= 0"
        )

    if not (0 <= config.min_mexc_share_24h <= 1):
        errors.append(f"min_mexc_share_24h ({config.min_mexc_share_24h}) must be in [0, 1]")

    valid_volume_sources = ["mexc", "global_fallback_mexc"]
    if config.scoring_volume_source not in valid_volume_sources:
        errors.append(
            f"scoring.volume_source ({config.scoring_volume_source}) must be one of {valid_volume_sources}"
        )

    # Budget defaults / limits
    budget_cfg = config.raw.get("budget")
    if budget_cfg is None:
        budget_cfg = {}
    elif not isinstance(budget_cfg, dict):
        errors.append("budget must be an object")
        budget_cfg = {}

    _expect_integer_number(
        errors,
        budget_cfg.get("shortlist_size", _BUDGET_DEFAULTS["shortlist_size"]),
        "budget.shortlist_size",
        minimum=1,
    )
    _expect_integer_number(
        errors,
        budget_cfg.get("orderbook_top_k", _BUDGET_DEFAULTS["orderbook_top_k"]),
        "budget.orderbook_top_k",
        minimum=1,
    )
    _expect_integer_number(
        errors,
        budget_cfg.get("pre_shortlist_market_cap_floor_usd", _BUDGET_DEFAULTS["pre_shortlist_market_cap_floor_usd"]),
        "budget.pre_shortlist_market_cap_floor_usd",
        minimum=0,
    )

    # Tradeability block
    tradeability_cfg = config.raw.get("tradeability", {})
    if "enabled" in tradeability_cfg and not isinstance(tradeability_cfg.get("enabled"), bool):
        errors.append("tradeability.enabled must be boolean")
    _expect_number(errors, tradeability_cfg.get("notional_total_usdt", 20_000), "tradeability.notional_total_usdt", minimum=0)
    _expect_number(errors, tradeability_cfg.get("notional_chunk_usdt", 5_000), "tradeability.notional_chunk_usdt", minimum=0)
    _expect_number(errors, tradeability_cfg.get("max_tranches", 4), "tradeability.max_tranches", minimum=1)
    _expect_number(errors, tradeability_cfg.get("band_pct", 1.0), "tradeability.band_pct", minimum=0)
    _expect_number(errors, tradeability_cfg.get("max_spread_pct", 0.15), "tradeability.max_spread_pct", minimum=0)
    _expect_number(errors, tradeability_cfg.get("min_depth_1pct_usd", 200_000), "tradeability.min_depth_1pct_usd", minimum=0)

    class_thresholds = tradeability_cfg.get("class_thresholds")
    if class_thresholds is None:
        class_thresholds = {
            "direct_ok_max_slippage_bps": 50,
            "tranche_ok_max_slippage_bps": 100,
            "marginal_max_slippage_bps": 150,
        }
    if not isinstance(class_thresholds, dict):
        errors.append("tradeability.class_thresholds must be an object")
    else:
        required = [
            "direct_ok_max_slippage_bps",
            "tranche_ok_max_slippage_bps",
            "marginal_max_slippage_bps",
        ]
        missing = [key for key in required if key not in class_thresholds]
        if missing:
            errors.append(f"tradeability.class_thresholds missing keys: {missing}")
        else:
            d = _expect_number(errors, class_thresholds.get(required[0]), f"tradeability.class_thresholds.{required[0]}", minimum=0)
            t = _expect_number(errors, class_thresholds.get(required[1]), f"tradeability.class_thresholds.{required[1]}", minimum=0)
            m = _expect_number(errors, class_thresholds.get(required[2]), f"tradeability.class_thresholds.{required[2]}", minimum=0)
            if d is not None and t is not None and m is not None and not (d <= t <= m):
                errors.append(
                    "tradeability.class_thresholds must satisfy direct_ok_max_slippage_bps <= tranche_ok_max_slippage_bps <= marginal_max_slippage_bps"
                )

    # Risk block
    risk_cfg = config.raw.get("risk", {})
    if "enabled" in risk_cfg and not isinstance(risk_cfg.get("enabled"), bool):
        errors.append("risk.enabled must be boolean")
    if str(risk_cfg.get("stop_method", "atr_multiple")) != "atr_multiple":
        errors.append("risk.stop_method must be 'atr_multiple' in Phase 1")
    _expect_number(errors, risk_cfg.get("atr_period", 14), "risk.atr_period", minimum=1)
    if str(risk_cfg.get("atr_timeframe", "1d")) not in ["1d"]:
        errors.append("risk.atr_timeframe must be '1d' in Phase 1")
    _expect_number(errors, risk_cfg.get("atr_multiple", 2.0), "risk.atr_multiple", minimum=0)
    min_stop = _expect_number(errors, risk_cfg.get("min_stop_distance_pct", 4.0), "risk.min_stop_distance_pct", minimum=0)

    max_stop_cfg = risk_cfg.get("max_stop_distance_pct", 12.0)
    if isinstance(max_stop_cfg, Mapping):
        if "default" not in max_stop_cfg:
            errors.append("risk.max_stop_distance_pct.default is required when risk.max_stop_distance_pct is an object")
            max_stop_default = None
        else:
            max_stop_default = _expect_number(
                errors,
                max_stop_cfg.get("default"),
                "risk.max_stop_distance_pct.default",
                minimum=0,
            )

        for setup_key in ["reversal", "pullback", "breakout"]:
            if setup_key in max_stop_cfg:
                _expect_number(
                    errors,
                    max_stop_cfg.get(setup_key),
                    f"risk.max_stop_distance_pct.{setup_key}",
                    minimum=0,
                )

        max_stop = max_stop_default
    else:
        max_stop = _expect_number(errors, max_stop_cfg, "risk.max_stop_distance_pct", minimum=0)

    if min_stop is not None and max_stop is not None and min_stop > max_stop:
        errors.append("risk.min_stop_distance_pct must be <= risk.max_stop_distance_pct")
    if "min_rr_to_target_1" in risk_cfg:
        _expect_number(errors, risk_cfg.get("min_rr_to_target_1"), "risk.min_rr_to_target_1", minimum=0)
    elif "min_rr_to_tp10" in risk_cfg:
        _expect_number(errors, risk_cfg.get("min_rr_to_tp10"), "risk.min_rr_to_tp10", minimum=0)

    # Decision block
    decision_cfg = config.raw.get("decision", {})
    if "enabled" in decision_cfg and not isinstance(decision_cfg.get("enabled"), bool):
        errors.append("decision.enabled must be boolean")
    min_enter = _expect_number(errors, decision_cfg.get("min_score_for_enter", 65), "decision.min_score_for_enter", minimum=0, maximum=100)
    min_wait = _expect_number(errors, decision_cfg.get("min_score_for_wait", 40), "decision.min_score_for_wait", minimum=0, maximum=100)
    if min_enter is not None and min_wait is not None and min_wait > min_enter:
        errors.append("decision.min_score_for_wait must be <= decision.min_score_for_enter")
    for bool_key in ["require_tradeability_for_enter", "require_risk_acceptable_for_enter"]:
        if bool_key in decision_cfg and not isinstance(decision_cfg.get(bool_key), bool):
            errors.append(f"decision.{bool_key} must be boolean")
    _expect_number(
        errors,
        decision_cfg.get("min_effective_rr_to_target_2_for_enter", 1.0),
        "decision.min_effective_rr_to_target_2_for_enter",
        minimum=0,
    )

    # BTC regime block
    btc_cfg = config.raw.get("btc_regime", {})
    if "enabled" in btc_cfg and not isinstance(btc_cfg.get("enabled"), bool):
        errors.append("btc_regime.enabled must be boolean")
    mode = str(btc_cfg.get("mode", "threshold_modifier"))
    if mode != "threshold_modifier":
        errors.append("btc_regime.mode must be 'threshold_modifier'")
    _expect_number(errors, btc_cfg.get("risk_off_enter_boost", 15), "btc_regime.risk_off_enter_boost")

    try:
        resolve_axes_config(config.raw)
    except ValueError as exc:
        errors.append(str(exc))

    try:
        resolve_entry_config(config.raw)
    except ValueError as exc:
        errors.append(str(exc))
    try:
        resolve_bucket_config(config.raw)
    except ValueError as exc:
        errors.append(str(exc))
    try:
        resolve_priority_config(config.raw)
    except ValueError as exc:
        errors.append(str(exc))

    independence_release_cfg = config.raw.get("independence_release", {})
    if not isinstance(independence_release_cfg, dict):
        errors.append("independence_release must be an object")
    else:
        for key in _INDEPENDENCE_RELEASE_SECTION_DEFAULTS:
            value = independence_release_cfg.get(key, {})
            if not isinstance(value, dict):
                errors.append(f"independence_release.{key} must be an object")

    # Shadow mode / parallel run block
    shadow_cfg = config.raw.get("shadow")
    if shadow_cfg is None:
        shadow_cfg = {}
    elif not isinstance(shadow_cfg, dict):
        errors.append("shadow must be an object")
        shadow_cfg = {}

    shadow_mode = str(shadow_cfg.get("mode", "parallel"))
    allowed_shadow_modes = ["legacy_only", "new_only", "parallel"]
    configured_primary = None
    has_configured_primary = "primary_path" in shadow_cfg

    if has_configured_primary:
        configured_primary = str(shadow_cfg.get("primary_path"))
        if configured_primary not in ["legacy", "new"]:
            errors.append("shadow.primary_path must be one of ['legacy', 'new']")

    if shadow_mode not in allowed_shadow_modes:
        errors.append(f"shadow.mode ({shadow_mode}) must be one of {allowed_shadow_modes}")
    else:
        if shadow_mode in {"new_only", "parallel"}:
            if not config.tradeability_enabled:
                errors.append(f"shadow.mode={shadow_mode} requires tradeability.enabled=true")
            if not config.risk_enabled:
                errors.append(f"shadow.mode={shadow_mode} requires risk.enabled=true")
            if not config.decision_enabled:
                errors.append(f"shadow.mode={shadow_mode} requires decision.enabled=true")

        if configured_primary in {"legacy", "new"}:
            if shadow_mode == "legacy_only" and configured_primary != "legacy":
                errors.append("shadow.mode=legacy_only requires shadow.primary_path=legacy")
            if shadow_mode == "new_only" and configured_primary != "new":
                errors.append("shadow.mode=new_only requires shadow.primary_path=new")

    return errors
