from scanner.clients.mapping import MappingResult
from scanner.pipeline.__init__ import (
    _compute_mexc_share_24h,
    _compute_turnover_24h,
    _enrich_scored_entries_with_market_activity,
    _extract_cmc_global_volume_24h,
)


def test_extract_cmc_global_volume_24h_missing_and_present() -> None:
    mapped = MappingResult(
        mexc_symbol="ABCUSDT",
        cmc_data={"quote": {"USD": {"volume_24h": "123.45"}}},
        confidence="high",
        method="symbol_exact_match",
    )
    missing = MappingResult(
        mexc_symbol="ABCUSDT",
        cmc_data={"quote": {"USD": {}}},
        confidence="high",
        method="symbol_exact_match",
    )

    assert _extract_cmc_global_volume_24h(mapped) == 123.45
    assert _extract_cmc_global_volume_24h(missing) is None


def test_turnover_and_mexc_share_handle_zero_and_missing_denominators() -> None:
    assert _compute_turnover_24h(100.0, 10.0) == 10.0
    assert _compute_turnover_24h(100.0, 0) is None
    assert _compute_turnover_24h(None, 10.0) is None

    assert _compute_mexc_share_24h(5.0, 100.0) == 0.05
    assert _compute_mexc_share_24h(5.0, 0) is None
    assert _compute_mexc_share_24h(None, 100.0) is None


def test_enrich_market_activity_happy_path() -> None:
    entries = [{"symbol": "AAAUSDT", "score": 82.1}]
    features = {
        "AAAUSDT": {
            "global_volume_24h_usd": 123_456_789.0,
            "turnover_24h": 0.12,
            "mexc_share_24h": 0.04,
        }
    }

    enriched = _enrich_scored_entries_with_market_activity(entries, features)

    assert enriched[0]["global_volume_24h_usd"] == 123_456_789.0
    assert enriched[0]["turnover_24h"] == 0.12
    assert enriched[0]["mexc_share_24h"] == 0.04


def test_enrich_market_activity_missing_symbol() -> None:
    entries = [{"score": 88.8}]

    enriched = _enrich_scored_entries_with_market_activity(entries, {"AAAUSDT": {}})

    assert "global_volume_24h_usd" in enriched[0]
    assert "turnover_24h" in enriched[0]
    assert "mexc_share_24h" in enriched[0]
    assert enriched[0]["global_volume_24h_usd"] is None
    assert enriched[0]["turnover_24h"] is None
    assert enriched[0]["mexc_share_24h"] is None


def test_enrich_market_activity_unknown_symbol_or_missing_field() -> None:
    unknown_symbol = [{"symbol": "MISSUSDT"}]
    unknown_enriched = _enrich_scored_entries_with_market_activity(unknown_symbol, {})
    assert unknown_enriched[0]["global_volume_24h_usd"] is None
    assert unknown_enriched[0]["turnover_24h"] is None
    assert unknown_enriched[0]["mexc_share_24h"] is None

    missing_fields = [{"symbol": "PARTIALUSDT"}]
    partial_features = {"PARTIALUSDT": {"global_volume_24h_usd": 10_000.0}}
    partial_enriched = _enrich_scored_entries_with_market_activity(missing_fields, partial_features)
    assert partial_enriched[0]["global_volume_24h_usd"] == 10_000.0
    assert partial_enriched[0]["turnover_24h"] is None
    assert partial_enriched[0]["mexc_share_24h"] is None
