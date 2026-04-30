from scanner.runners.daily import _build_ticket23_report_payload


class _Bucket:
    def __init__(self, value: str):
        self.value = value


class _Decision:
    def __init__(self, bucket: str):
        self.decision_bucket = _Bucket(bucket)


class _Ranked:
    def __init__(self, symbol: str, bucket: str):
        self.symbol = symbol
        self.decision = _Decision(bucket)


def _diag(symbol: str, category: str, excluded: bool) -> dict:
    return {
        "symbol": symbol,
        "decision": {"priority_score": 1.0},
        "execution_status_raw": None,
        "execution_pass": None,
        "universe": {
            "universe_category": category,
            "universe_category_confidence": "low",
            "universe_category_reason": "r",
            "candidate_excluded": excluded,
            "candidate_exclusion_reason": category if excluded else None,
        },
    }


def test_segmentation_excludes_only_stable_and_leveraged_from_tradable() -> None:
    ranked = [
        _Ranked("TUSDUSDT", "confirmed_candidates"),
        _Ranked("3LAAAUSDT", "confirmed_candidates"),
        _Ranked("NVDAONUSDT", "confirmed_candidates"),
        _Ranked("OIL(USOON)USDT", "confirmed_candidates"),
        _Ranked("BTCBAMUSDT", "confirmed_candidates"),
        _Ranked("INTCONUSDT", "confirmed_candidates"),
    ]
    diagnostics = [
        _diag("TUSDUSDT", "stable_or_cash_proxy", True),
        _diag("3LAAAUSDT", "leveraged_or_margin_token", True),
        _diag("NVDAONUSDT", "tokenized_stock_or_etf", False),
        _diag("OIL(USOON)USDT", "commodity_or_index_proxy", False),
        _diag("BTCBAMUSDT", "wrapped_or_synthetic_btc", False),
        _diag("INTCONUSDT", "unknown", False),
    ]
    payload = _build_ticket23_report_payload(ranked=ranked, diagnostics=diagnostics)

    tradable = payload["candidate_segments"]["tradable_buckets"]["confirmed_candidates"]
    excluded = payload["candidate_segments"]["excluded_candidate_buckets"]["confirmed_candidates"]
    assert {x["symbol"] for x in excluded} == {"TUSDUSDT", "3LAAAUSDT"}
    assert {x["symbol"] for x in tradable} == {"NVDAONUSDT", "OIL(USOON)USDT", "BTCBAMUSDT", "INTCONUSDT"}

    assert payload["universe_classification"]["candidate_excluded_symbol_count"] == 2
    assert payload["universe_classification"]["category_counts_by_bucket"]["confirmed_candidates"]["unknown"] == 1
