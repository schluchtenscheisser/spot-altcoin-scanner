from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import math
from typing import Any, Mapping

from scanner.config import resolve_independence_market_data_budget_config, resolve_independence_universe_config


ALLOWED_LISTING_AGE_STATUS = {"known_pass", "known_fail", "unknown_pass"}
ALLOWED_MARKET_CAP_STATUS = {"known_pass", "known_fail", "unknown_pass"}


@dataclass(frozen=True)
class EligibilityInput:
    symbol: str
    quote_asset: str | None
    mexc_status: str | None
    quote_volume_24h: float | None
    market_cap_usd: float | None
    has_cmc_match: bool
    mexc_first_tradable_date: str | None
    decision_timestamp_utc: str


def _is_finite_number(value: Any) -> bool:
    return value is not None and not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def _days_since_iso_date(iso_date: str, as_of_date: date) -> int:
    parsed = datetime.fromisoformat(iso_date).date()
    return (as_of_date - parsed).days


def evaluate_pre_1d_eligibility(payload: EligibilityInput, cfg: Mapping[str, Any], *, as_of_date: date) -> dict[str, Any]:
    universe_cfg = resolve_independence_universe_config(cfg)

    reasons: list[str] = []

    quote_asset_status = "pass" if payload.quote_asset in universe_cfg["quote_asset_allowed"] else "fail"
    if quote_asset_status == "fail":
        reasons.append("QUOTE_ASSET_NOT_ALLOWED")

    tradability_status = "pass" if payload.mexc_status in universe_cfg["mexc_tradeable_status_values"] else "fail"
    if tradability_status == "fail":
        reasons.append("NOT_TRADEABLE")

    listing_age_days: int | None = None
    if payload.mexc_first_tradable_date:
        listing_age_days = _days_since_iso_date(payload.mexc_first_tradable_date, as_of_date)
        if listing_age_days >= universe_cfg["listing_age_days_min"]:
            listing_age_status = "known_pass"
        else:
            listing_age_status = "known_fail"
            reasons.append("LISTING_AGE_BELOW_THRESHOLD")
    else:
        listing_age_status = "unknown_pass"

    if payload.has_cmc_match and _is_finite_number(payload.market_cap_usd):
        market_cap_usd = float(payload.market_cap_usd)
        if market_cap_usd >= universe_cfg["market_cap_usd_min"]:
            market_cap_status = "known_pass"
        else:
            market_cap_status = "known_fail"
            reasons.append("MARKET_CAP_BELOW_THRESHOLD")
    elif payload.has_cmc_match:
        market_cap_usd = None
        market_cap_status = "unknown_pass"
    else:
        market_cap_usd = None
        market_cap_status = "unknown_pass"

    if _is_finite_number(payload.quote_volume_24h):
        quote_volume_24h = float(payload.quote_volume_24h)
        if quote_volume_24h < universe_cfg["quote_volume_24h_min"]:
            reasons.append("QUOTE_VOLUME_24H_BELOW_THRESHOLD")
    else:
        quote_volume_24h = None
        reasons.append("QUOTE_VOLUME_24H_NOT_EVALUABLE")

    result = {
        "symbol": payload.symbol,
        "eligible_pre_1d": len(reasons) == 0,
        "eligibility_fail_reasons": reasons,
        "quote_asset_status": quote_asset_status,
        "tradability_status": tradability_status,
        "listing_age_status": listing_age_status,
        "listing_age_days": listing_age_days,
        "market_cap_status": market_cap_status,
        "market_cap_usd": market_cap_usd,
        "quote_volume_24h": quote_volume_24h,
        "mexc_first_tradable_date": payload.mexc_first_tradable_date,
        "decision_timestamp_utc": payload.decision_timestamp_utc,
    }
    return result
