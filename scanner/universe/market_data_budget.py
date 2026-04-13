from __future__ import annotations

from datetime import date, timedelta
import math
from typing import Any, Mapping, Sequence

from scanner.config import resolve_independence_market_data_budget_config


def _finite(value: Any) -> bool:
    return value is not None and not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def evaluate_activity_gate(
    *,
    daily_bar_id: str,
    bars_by_date: Mapping[str, Mapping[str, Any]],
    total_history_bar_count: int,
    cfg: Mapping[str, Any],
) -> dict[str, Any]:
    budget = resolve_independence_market_data_budget_config(cfg)
    gate = budget["activity_gate"]

    end_day = date.fromisoformat(daily_bar_id)
    window_days = int(gate["window_days"])
    floor = float(gate["daily_quote_volume_active_floor"])
    min_active = int(gate["min_active_days"])

    if total_history_bar_count < window_days:
        return {"activity_gate_status": "not_evaluable", "active_days_last_14": None, "activity_gate_reason": "ACTIVITY_GATE_INSUFFICIENT_HISTORY"}

    window_dates = [(end_day - timedelta(days=offset)).isoformat() for offset in range(window_days - 1, -1, -1)]
    active = 0
    invalid_count = 0
    for day in window_dates:
        bar = bars_by_date.get(day)
        if bar is None:
            continue
        volume = bar.get("quote_volume")
        if not _finite(volume):
            invalid_count += 1
            continue
        if float(volume) >= floor:
            active += 1

    if invalid_count > 2:
        return {"activity_gate_status": "not_evaluable", "active_days_last_14": None, "activity_gate_reason": "ACTIVITY_GATE_INVALID_INPUTS"}

    if active >= min_active:
        return {"activity_gate_status": "passed", "active_days_last_14": active, "activity_gate_reason": "ACTIVITY_GATE_PASSED"}
    return {"activity_gate_status": "failed", "active_days_last_14": active, "activity_gate_reason": "ACTIVITY_GATE_INSUFFICIENT_ACTIVE_DAYS"}


def evaluate_monitoring_bypass(*, state_machine_state: str | None, decision_bucket: str | None, market_phase_confidence: float | None, cfg: Mapping[str, Any]) -> tuple[bool, str | None]:
    budget = resolve_independence_market_data_budget_config(cfg)
    min_conf = float(budget["monitoring_bypass"]["min_phase_confidence"])
    if state_machine_state in {"watch", "early_ready", "confirmed_ready", "late"}:
        return True, "BYPASS_STATE"
    if decision_bucket in {"watchlist", "early_candidates", "confirmed_candidates", "late_monitor"}:
        return True, "BYPASS_BUCKET"
    if _finite(market_phase_confidence) and float(market_phase_confidence) >= min_conf:
        return True, "BYPASS_CONFIDENCE"
    return False, None


def evaluate_pre_4h_candidate_filter(inputs: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    budget = resolve_independence_market_data_budget_config(cfg)
    filt = budget["pre_4h_candidate_filter"]

    def rule_a() -> tuple[str, str]:
        a = filt["rule_a"]
        vals = [inputs.get("close_vs_ema50_1d_pct"), inputs.get("ema20_vs_ema50_1d_pct"), inputs.get("ema20_slope_1d_pct_per_bar")]
        if not all(_finite(v) for v in vals):
            return "not_evaluable", "FILTER_PASSED_TREND_1D"
        ok = float(vals[0]) > float(a["close_vs_ema50_1d_pct_min_exclusive"]) and float(vals[1]) >= float(a["ema20_vs_ema50_1d_pct_min_inclusive"]) and float(vals[2]) > float(a["ema20_slope_1d_pct_per_bar_min_exclusive"])
        return ("passed" if ok else "failed"), "FILTER_PASSED_TREND_1D"

    def rule_b() -> tuple[str, str]:
        b = filt["rule_b"]
        v = inputs.get("volume_1d_current_vs_median10")
        if not _finite(v):
            return "not_evaluable", "FILTER_PASSED_VOLUME_IMPULSE_1D"
        return ("passed" if float(v) >= float(b["volume_1d_current_vs_median10_min_inclusive"]) else "failed"), "FILTER_PASSED_VOLUME_IMPULSE_1D"

    def rule_c() -> tuple[str, str]:
        c = filt["rule_c"]
        vals = [inputs.get("range_width_10bars_1d_pct"), inputs.get("close_position_in_range_10bars_1d")]
        if not all(_finite(v) for v in vals):
            return "not_evaluable", "FILTER_PASSED_COMPRESSION_1D"
        ok = float(vals[0]) <= float(c["range_width_10bars_1d_pct_max_inclusive"]) and float(vals[1]) >= float(c["close_position_in_range_10bars_1d_min_inclusive"])
        return ("passed" if ok else "failed"), "FILTER_PASSED_COMPRESSION_1D"

    statuses = {
        "FILTER_PASSED_TREND_1D": rule_a()[0],
        "FILTER_PASSED_VOLUME_IMPULSE_1D": rule_b()[0],
        "FILTER_PASSED_COMPRESSION_1D": rule_c()[0],
    }
    priority = ["FILTER_PASSED_COMPRESSION_1D", "FILTER_PASSED_TREND_1D", "FILTER_PASSED_VOLUME_IMPULSE_1D"]
    matched = [code for code in priority if statuses[code] == "passed"]
    if matched:
        return {"pre_4h_filter_status": "passed", "pre_4h_filter_primary_reason": matched[0], "matched_filter_rules": matched, "rule_statuses": statuses}
    return {"pre_4h_filter_status": "failed", "pre_4h_filter_primary_reason": "FILTER_FAILED_ALL_RULES", "matched_filter_rules": [], "rule_statuses": statuses}


def cap_non_bypass_candidates(*, max_4h_fetch_count: int, bypass_symbols: Sequence[str], non_bypass_passed: Sequence[Mapping[str, Any]]) -> tuple[list[str], list[str], int]:
    remaining = max(0, int(max_4h_fetch_count) - len(bypass_symbols))
    ranked = sorted(non_bypass_passed, key=lambda row: (-float(row.get("quote_volume_24h", 0.0)), str(row["symbol"])))
    selected = [row["symbol"] for row in ranked[:remaining]]
    capped = [row["symbol"] for row in ranked[remaining:]]
    return selected, capped, remaining
