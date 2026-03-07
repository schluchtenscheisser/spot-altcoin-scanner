import copy

from scanner.config import ScannerConfig, validate_config
from scanner.pipeline.filters import UniverseFilters
from scanner.pipeline.shortlist import ShortlistSelector


def _row(symbol: str, market_cap: float, quote_volume_24h: float, **extra):
    row = {
        "symbol": symbol,
        "base": symbol.replace("USDT", ""),
        "market_cap": market_cap,
        "quote_volume_24h": quote_volume_24h,
    }
    row.update(extra)
    return row


def _filter_config(**overrides):
    cfg = {
        "budget": {"pre_shortlist_market_cap_floor_usd": 25_000_000},
        "universe_filters": {
            "market_cap": {"min_usd": 1, "max_usd": 5_000_000_000},
            "include_only_usdt_pairs": True,
            "volume": {
                "min_turnover_24h": 0.03,
                "min_mexc_quote_volume_24h_usdt": 5_000_000,
                "min_mexc_share_24h": 0.01,
            },
        },
    }
    cfg.update(overrides)
    return cfg


def test_v421_shortlist_budget_cap_is_strict_with_overflow_universe():
    selector = ShortlistSelector({"budget": {"shortlist_size": 2, "pre_shortlist_market_cap_floor_usd": 25_000_000}})
    out = selector.select(
        [
            _row("AAAUSDT", market_cap=30_000_000, quote_volume_24h=100),
            _row("BBBUSDT", market_cap=30_000_000, quote_volume_24h=200),
            _row("CCCUSDT", market_cap=30_000_000, quote_volume_24h=300),
        ]
    )
    assert [r["symbol"] for r in out] == ["CCCUSDT", "BBBUSDT"]


def test_v421_shortlist_floor_excludes_under_floor_even_if_otherwise_strong():
    selector = ShortlistSelector({"budget": {"shortlist_size": 5, "pre_shortlist_market_cap_floor_usd": 25_000_000}})
    out = selector.select(
        [
            _row("LOWUSDT", market_cap=24_999_999, quote_volume_24h=999_999_999),
            _row("HIGHUSDT", market_cap=25_000_000, quote_volume_24h=1),
        ]
    )
    assert [r["symbol"] for r in out] == ["HIGHUSDT"]


def test_v421_coin_above_floor_can_pass_even_above_legacy_market_cap_max():
    filters = UniverseFilters(_filter_config())
    out = filters.apply_all([_row("BIGUSDT", market_cap=20_000_000_000, quote_volume_24h=1)])
    assert [r["symbol"] for r in out] == ["BIGUSDT"]


def test_v421_above_floor_low_turnover_quote_volume_and_share_are_not_hard_excluded():
    filters = UniverseFilters(_filter_config())
    out = filters.apply_all(
        [
            _row(
                "THINUSDT",
                market_cap=50_000_000,
                quote_volume_24h=10,
                turnover_24h=0.0001,
                mexc_share_24h=0.0001,
            )
        ]
    )
    assert [r["symbol"] for r in out] == ["THINUSDT"]


def test_v421_safety_and_hard_risk_excludes_still_apply(tmp_path):
    denylist = tmp_path / "denylist.yaml"
    denylist.write_text("hard_exclude:\n  symbols: [DENIEDUSDT]\n", encoding="utf-8")

    unlocks = tmp_path / "unlocks.yaml"
    unlocks.write_text(
        "overrides:\n"
        "  - symbol: MAJORUSDT\n"
        "    severity: major\n"
        "    days_to_unlock: 3\n",
        encoding="utf-8",
    )

    cfg = _filter_config(
        risk_flags={"denylist_file": str(denylist), "unlock_overrides_file": str(unlocks)}
    )
    filters = UniverseFilters(cfg)

    out = filters.apply_all(
        [
            _row("USDCUSDT", market_cap=60_000_000, quote_volume_24h=1),
            _row("WBTCUSDT", market_cap=60_000_000, quote_volume_24h=1),
            _row("ALTUPUSDT", market_cap=60_000_000, quote_volume_24h=1),
            _row("DENIEDUSDT", market_cap=60_000_000, quote_volume_24h=1),
            _row("MAJORUSDT", market_cap=60_000_000, quote_volume_24h=1),
            _row("OKUSDT", market_cap=60_000_000, quote_volume_24h=1),
        ]
    )

    assert [r["symbol"] for r in out] == ["OKUSDT"]


def test_v421_shortlist_selection_is_deterministic_for_identical_input_and_config():
    rows = [
        _row("CCCUSDT", market_cap=30_000_000, quote_volume_24h=1000),
        _row("AAAUSDT", market_cap=30_000_000, quote_volume_24h=1000),
        _row("BBBUSDT", market_cap=30_000_000, quote_volume_24h=1000),
    ]
    cfg = {"budget": {"shortlist_size": 2, "pre_shortlist_market_cap_floor_usd": 25_000_000}}

    selector_a = ShortlistSelector(copy.deepcopy(cfg))
    selector_b = ShortlistSelector(copy.deepcopy(cfg))

    out_a = selector_a.select(copy.deepcopy(rows))
    out_b = selector_b.select(copy.deepcopy(rows))

    assert [r["symbol"] for r in out_a] == ["AAAUSDT", "BBBUSDT"]
    assert [r["symbol"] for r in out_a] == [r["symbol"] for r in out_b]


def test_v421_budget_missing_key_uses_default_and_invalid_value_errors():
    cfg_missing = ScannerConfig(raw={"general": {"run_mode": "offline"}, "universe_filters": {"market_cap": {"min_usd": 1, "max_usd": 2}}})
    assert cfg_missing.budget_shortlist_size == 200

    cfg_invalid = ScannerConfig(
        raw={
            "general": {"run_mode": "offline"},
            "universe_filters": {"market_cap": {"min_usd": 1, "max_usd": 2}},
            "budget": {"shortlist_size": 1.5},
        }
    )
    errors = validate_config(cfg_invalid)
    assert any("budget.shortlist_size" in e and "integer" in e for e in errors)
