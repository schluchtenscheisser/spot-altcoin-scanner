from __future__ import annotations

import re
from dataclasses import dataclass

CANDIDATE_EXCLUDED_CATEGORIES = {"stable_or_cash_proxy", "leveraged_or_margin_token"}


@dataclass(frozen=True)
class UniverseClassification:
    universe_category: str
    universe_category_confidence: str
    universe_category_reason: str
    candidate_excluded: bool
    candidate_exclusion_reason: str | None


def _base_symbol(symbol: str) -> str:
    return symbol[:-4] if symbol.endswith("USDT") else symbol


def classify_symbol(symbol: str) -> UniverseClassification:
    exact = {
        "TUSDUSDT": ("stable_or_cash_proxy", "high", "exact_override_stable"),
        "NVDAONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
        "GOOGLONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
        "AMDONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
        "PBRONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
        "OIL(USOON)USDT": ("commodity_or_index_proxy", "high", "exact_override_commodity_proxy"),
        "BTCBAMUSDT": ("wrapped_or_synthetic_btc", "high", "exact_override_wrapped_btc"),
    }
    if symbol in exact:
        cat, conf, reason = exact[symbol]
        excluded = cat in CANDIDATE_EXCLUDED_CATEGORIES
        return UniverseClassification(cat, conf, reason, excluded, cat if excluded else None)

    base = _base_symbol(symbol)
    if base in {"TUSD", "USDP", "FDUSD", "USD1", "USDM"}:
        return UniverseClassification("stable_or_cash_proxy", "high", "base_symbol_stable_cash", True, "stable_or_cash_proxy")

    if any(re.search(p, base) for p in (r"^3K", r"^3L", r"^3S", r"BULL", r"BEAR")):
        return UniverseClassification("leveraged_or_margin_token", "high", "leveraged_or_margin_pattern", True, "leveraged_or_margin_token")

    if symbol.endswith("ONUSDT"):
        return UniverseClassification("unknown", "low", "stock_like_symbol_pattern_detected_unverified", False, None)

    return UniverseClassification("classic_crypto", "low", "no_non_classic_rule_matched", False, None)
