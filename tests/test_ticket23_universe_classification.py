from scanner.universe.classification import classify_symbol


def test_classification_stable_and_leveraged_excluded() -> None:
    assert classify_symbol("TUSDUSDT").candidate_excluded is True
    assert classify_symbol("3LAAAUSDT").universe_category == "leveraged_or_margin_token"


def test_classification_unknown_vs_classic() -> None:
    assert classify_symbol("INTCONUSDT").universe_category == "unknown"
    c = classify_symbol("SOLUSDT")
    assert c.universe_category == "classic_crypto"
    assert c.candidate_excluded is False


def test_classification_exact_overrides() -> None:
    assert classify_symbol("NVDAONUSDT").universe_category == "tokenized_stock_or_etf"
    assert classify_symbol("OIL(USOON)USDT").universe_category == "commodity_or_index_proxy"
