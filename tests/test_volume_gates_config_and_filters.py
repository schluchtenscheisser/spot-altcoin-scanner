from scanner.config import ScannerConfig, validate_config
from scanner.pipeline.filters import UniverseFilters


def _base_filter_config(volume_cfg: dict) -> dict:
    return {
        "universe_filters": {
            "market_cap": {"min_usd": 1, "max_usd": 10_000_000_000},
            "include_only_usdt_pairs": True,
            "volume": volume_cfg,
        }
    }


def test_config_volume_gate_defaults_when_missing_keys() -> None:
    cfg = ScannerConfig(raw={})
    assert cfg.min_turnover_24h == 0.03
    assert cfg.min_mexc_quote_volume_24h_usdt == 5_000_000
    assert cfg.min_mexc_share_24h == 0.01


def test_config_volume_gate_validation_invalid_values() -> None:
    cfg = ScannerConfig(
        raw={
            "general": {"run_mode": "offline"},
            "universe_filters": {
                "market_cap": {"min_usd": 1, "max_usd": 2},
                "volume": {
                    "min_turnover_24h": -0.01,
                    "min_mexc_quote_volume_24h_usdt": -1,
                    "min_mexc_share_24h": 1.2,
                },
            },
        }
    )
    errors = validate_config(cfg)
    assert any("min_turnover_24h" in e for e in errors)
    assert any("min_mexc_quote_volume_24h_usdt" in e for e in errors)
    assert any("min_mexc_share_24h" in e for e in errors)


def test_config_volume_gate_legacy_alias_used_when_new_key_missing() -> None:
    cfg = ScannerConfig(raw={"universe_filters": {"volume": {"min_quote_volume_24h": 42}}})
    assert cfg.min_mexc_quote_volume_24h_usdt == 42


def test_config_volume_gate_new_key_wins_over_legacy_alias() -> None:
    cfg = ScannerConfig(
        raw={
            "universe_filters": {
                "volume": {
                    "min_quote_volume_24h": 42,
                    "min_mexc_quote_volume_24h_usdt": 84,
                }
            }
        }
    )
    assert cfg.min_mexc_quote_volume_24h_usdt == 84


def test_filter_below_pre_shortlist_floor_is_excluded() -> None:
    filters = UniverseFilters(
        {
            "budget": {"pre_shortlist_market_cap_floor_usd": 25_000_000},
            **_base_filter_config({}),
        }
    )
    out = filters.apply_all(
        [
            {"symbol": "LOWUSDT", "base": "LOW", "market_cap": 20_000_000, "quote_volume_24h": 1},
            {"symbol": "HIGHUSDT", "base": "HIGH", "market_cap": 30_000_000, "quote_volume_24h": 1},
        ]
    )
    assert [row["symbol"] for row in out] == ["HIGHUSDT"]


def test_filter_above_floor_is_not_excluded_by_legacy_liquidity_thresholds() -> None:
    filters = UniverseFilters(
        {
            "budget": {"pre_shortlist_market_cap_floor_usd": 25_000_000},
            **_base_filter_config(
                {
                    "min_turnover_24h": 0.03,
                    "min_mexc_quote_volume_24h_usdt": 5_000_000,
                    "min_mexc_share_24h": 0.01,
                }
            ),
        }
    )
    out = filters.apply_all(
        [
            {
                "symbol": "LOWTURNUSDT",
                "base": "LOWTURN",
                "market_cap": 100_000_000,
                "quote_volume_24h": 100_000,
                "turnover_24h": 0.001,
                "mexc_share_24h": 0.0001,
            }
        ]
    )
    assert [row["symbol"] for row in out] == ["LOWTURNUSDT"]


def test_filter_above_floor_is_not_excluded_by_legacy_market_cap_max() -> None:
    filters = UniverseFilters(
        {
            "budget": {"pre_shortlist_market_cap_floor_usd": 25_000_000},
            **_base_filter_config({}),
        }
    )
    out = filters.apply_all(
        [
            {"symbol": "BIGUSDT", "base": "BIG", "market_cap": 20_000_000_000, "quote_volume_24h": 1},
        ]
    )
    assert [row["symbol"] for row in out] == ["BIGUSDT"]


def test_filter_missing_budget_floor_uses_default() -> None:
    filters = UniverseFilters(_base_filter_config({}))
    out = filters.apply_all(
        [
            {"symbol": "LOWUSDT", "base": "LOW", "market_cap": 24_000_000, "quote_volume_24h": 1},
            {"symbol": "HIGHUSDT", "base": "HIGH", "market_cap": 26_000_000, "quote_volume_24h": 1},
        ]
    )
    assert [row["symbol"] for row in out] == ["HIGHUSDT"]


def test_config_invalid_pre_shortlist_market_cap_floor_errors() -> None:
    cfg = ScannerConfig(
        raw={
            "general": {"run_mode": "offline"},
            "universe_filters": {"market_cap": {"min_usd": 1, "max_usd": 2}},
            "budget": {"pre_shortlist_market_cap_floor_usd": -1},
        }
    )
    errors = validate_config(cfg)
    assert any("budget.pre_shortlist_market_cap_floor_usd" in e for e in errors)
