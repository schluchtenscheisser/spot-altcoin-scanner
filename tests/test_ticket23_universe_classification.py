import pytest

from scanner.universe.classification import classify_symbol


@pytest.mark.parametrize("symbol", ["TUSDUSDT", "BUSDUSDT"])
def test_classification_stable_and_leveraged_excluded(symbol: str) -> None:
    stable = classify_symbol(symbol)
    assert stable.universe_category == "stable_or_cash_proxy"
    assert stable.candidate_excluded is True
    assert stable.candidate_exclusion_reason == "stable_or_cash_proxy"

    leveraged = classify_symbol("3LAAAUSDT")
    assert leveraged.universe_category == "leveraged_or_margin_token"
    assert leveraged.candidate_excluded is True


def test_classification_unknown_vs_classic() -> None:
    intc = classify_symbol("INTCONUSDT")
    assert intc.universe_category == "tokenized_stock_or_etf"
    assert intc.universe_category_confidence == "high"
    assert intc.candidate_excluded is False

    c = classify_symbol("SOLUSDT")
    assert c.universe_category == "classic_crypto"
    assert c.universe_category_confidence == "low"
    assert c.universe_category_reason == "no_non_classic_rule_matched"
    assert c.candidate_excluded is False


@pytest.mark.parametrize(
    "symbol",
    [
        "AMZNXUSDT",
        "NVDAXUSDT",
        "CATONUSDT",
        "OXYONUSDT",
        "BBAIONUSDT",
        "GSONUSDT",
        "JDONUSDT",
        "LINONUSDT",
        "OKLOONUSDT",
        "RDDTONUSDT",
        "SNDKONUSDT",
    ],
)
def test_tokenized_stock_exact_overrides(symbol: str) -> None:
    c = classify_symbol(symbol)
    assert c.universe_category == "tokenized_stock_or_etf"
    assert c.universe_category_confidence == "high"
    assert c.universe_category_reason == "exact_override_tokenized_stock"
    assert c.candidate_excluded is False
    assert c.candidate_exclusion_reason is None


@pytest.mark.parametrize("symbol", ["PALLONUSDT", "OIL(USOON)USDT"])
def test_commodity_proxy_exact_overrides(symbol: str) -> None:
    c = classify_symbol(symbol)
    assert c.universe_category == "commodity_or_index_proxy"
    assert c.universe_category_confidence == "high"
    assert c.universe_category_reason == "exact_override_commodity_proxy"
    assert c.candidate_excluded is False
    assert c.candidate_exclusion_reason is None


@pytest.mark.parametrize("symbol", ["COCAUSDT", "MUONUSDT", "EONUSDT"])
def test_classic_crypto_false_positive_exact_overrides(symbol: str) -> None:
    c = classify_symbol(symbol)
    assert c.universe_category == "classic_crypto"
    assert c.universe_category_confidence == "high"
    assert c.universe_category_reason == "exact_override_classic_crypto"
    assert c.candidate_excluded is False
    assert c.candidate_exclusion_reason is None


def test_unverified_stock_like_symbol_remains_unknown() -> None:
    c = classify_symbol("VONUSDT")
    assert c.universe_category == "unknown"
    assert c.universe_category_confidence == "low"
    assert c.universe_category_reason == "stock_like_symbol_pattern_detected_unverified"
    assert c.candidate_excluded is False
