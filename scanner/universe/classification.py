from __future__ import annotations

import re
from dataclasses import dataclass

CANDIDATE_EXCLUDED_CATEGORIES = {"stable_or_cash_proxy", "leveraged_or_margin_token"}

EXACT_OVERRIDES: dict[str, tuple[str, str, str]] = {
    "TUSDUSDT": ("stable_or_cash_proxy", "high", "exact_override_stable"),
    "LLYONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "CSCOONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "AAPLONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "ABBVONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "ADBEONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "AMZNONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "TSLAONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "ARMONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "AVGOONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "CEGONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "INTCONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "ITOTONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "JPMONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "MRVLONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "MSTRONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "NVOONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "QCOMONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "QQQONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "SPYONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "TQQQONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "UNHONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "WMTONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "GOOGLONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "AMDONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "NVDAONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "CVNAONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "PBRONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "CATONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "BBAIONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "GSONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "JDONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "LINONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "OKLOONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "OXYONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "RDDTONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "SNDKONUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "AMZNXUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "NVDAXUSDT": ("tokenized_stock_or_etf", "high", "exact_override_tokenized_stock"),
    "OIL(USOON)USDT": ("commodity_or_index_proxy", "high", "exact_override_commodity_proxy"),
    "PALLONUSDT": ("commodity_or_index_proxy", "high", "exact_override_commodity_proxy"),
    "BTCBAMUSDT": ("wrapped_or_synthetic_btc", "high", "exact_override_wrapped_btc"),
    "COCAUSDT": ("classic_crypto", "high", "exact_override_classic_crypto"),
    "MUONUSDT": ("classic_crypto", "high", "exact_override_classic_crypto"),
    "EONUSDT": ("classic_crypto", "high", "exact_override_classic_crypto"),
}


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
    if symbol in EXACT_OVERRIDES:
        cat, conf, reason = EXACT_OVERRIDES[symbol]
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
