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


def test_filter_primary_path_requires_turnover_volume_and_share() -> None:
    filters = UniverseFilters(
        _base_filter_config(
            {
                "min_turnover_24h": 0.03,
                "min_mexc_quote_volume_24h_usdt": 5_000_000,
                "min_mexc_share_24h": 0.01,
            }
        )
    )
    out = filters.apply_all(
        [
            {
                "symbol": "PASSUSDT",
                "base": "PASS",
                "market_cap": 100_000_000,
                "quote_volume_24h": 6_000_000,
                "turnover_24h": 0.04,
                "mexc_share_24h": 0.02,
            },
            {
                "symbol": "LOWTURNUSDT",
                "base": "LOWTURN",
                "market_cap": 100_000_000,
                "quote_volume_24h": 6_000_000,
                "turnover_24h": 0.02,
                "mexc_share_24h": 0.02,
            },
            {
                "symbol": "LOWSHAREUSDT",
                "base": "LOWSHARE",
                "market_cap": 100_000_000,
                "quote_volume_24h": 6_000_000,
                "turnover_24h": 0.04,
                "mexc_share_24h": 0.005,
            },
        ]
    )
    assert [row["symbol"] for row in out] == ["PASSUSDT"]


def test_filter_fallback_path_uses_only_mexc_min_volume() -> None:
    filters = UniverseFilters(_base_filter_config({"min_mexc_quote_volume_24h_usdt": 5_000_000}))
    out = filters.apply_all(
        [
            {
                "symbol": "FALLBACKPASSUSDT",
                "base": "FALLBACKPASS",
                "market_cap": 100_000_000,
                "quote_volume_24h": 6_000_000,
                "turnover_24h": None,
                "mexc_share_24h": None,
            },
            {
                "symbol": "FALLBACKFAILUSDT",
                "base": "FALLBACKFAIL",
                "market_cap": 100_000_000,
                "quote_volume_24h": 4_000_000,
                "turnover_24h": None,
                "mexc_share_24h": 0.0,
            },
        ]
    )
    assert [row["symbol"] for row in out] == ["FALLBACKPASSUSDT"]


def test_filter_turnover_available_but_missing_share_fails() -> None:
    filters = UniverseFilters(_base_filter_config({}))
    out = filters.apply_all(
        [
            {
                "symbol": "NOSHAREUSDT",
                "base": "NOSHARE",
                "market_cap": 100_000_000,
                "quote_volume_24h": 10_000_000,
                "turnover_24h": 0.5,
                "mexc_share_24h": None,
            }
        ]
    )
    assert out == []


def test_filter_invalid_per_symbol_values_are_dropped() -> None:
    filters = UniverseFilters(_base_filter_config({"min_mexc_quote_volume_24h_usdt": 0}))
    out = filters.apply_all(
        [
            {
                "symbol": "NEGUSDT",
                "base": "NEG",
                "market_cap": 100_000_000,
                "quote_volume_24h": -1,
                "turnover_24h": None,
                "mexc_share_24h": None,
            },
            {
                "symbol": "NANUSDT",
                "base": "NAN",
                "market_cap": 100_000_000,
                "quote_volume_24h": float("nan"),
                "turnover_24h": None,
                "mexc_share_24h": None,
            },
            {
                "symbol": "STRUSDT",
                "base": "STR",
                "market_cap": 100_000_000,
                "quote_volume_24h": "bad",
                "turnover_24h": None,
                "mexc_share_24h": None,
            },
        ]
    )
    assert out == []
