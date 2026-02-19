from scanner.pipeline.filters import UniverseFilters


def test_denylist_symbol_is_hard_excluded(tmp_path):
    denylist = tmp_path / "denylist.yaml"
    denylist.write_text("hard_exclude:\n  symbols: [BADUSDT]\n")
    unlocks = tmp_path / "unlock_overrides.yaml"
    unlocks.write_text("overrides: []\n")

    cfg = {
        "universe_filters": {
            "market_cap": {"min_usd": 1, "max_usd": 10_000_000_000},
            "volume": {"min_quote_volume_24h": 0},
        },
        "filters": {"exclusion_patterns": []},
        "risk_flags": {
            "denylist_file": str(denylist),
            "unlock_overrides_file": str(unlocks),
        },
    }

    f = UniverseFilters(cfg)
    out = f.apply_all([
        {"symbol": "BADUSDT", "base": "BAD", "quote": "USDT", "quote_volume_24h": 1, "market_cap": 100},
        {"symbol": "GOODUSDT", "base": "GOOD", "quote": "USDT", "quote_volume_24h": 1, "market_cap": 100},
    ])
    assert [x["symbol"] for x in out] == ["GOODUSDT"]


def test_major_unlock_is_hard_excluded_and_minor_unlock_is_soft_penalty(tmp_path):
    denylist = tmp_path / "denylist.yaml"
    denylist.write_text("hard_exclude:\n  symbols: []\n")
    unlocks = tmp_path / "unlock_overrides.yaml"
    unlocks.write_text(
        """
overrides:
  - symbol: MAJORUSDT
    severity: major
    days_to_unlock: 7
  - symbol: MINORUSDT
    severity: minor
    days_to_unlock: 10
""".strip()
    )

    cfg = {
        "universe_filters": {
            "market_cap": {"min_usd": 1, "max_usd": 10_000_000_000},
            "volume": {"min_quote_volume_24h": 0},
        },
        "filters": {"exclusion_patterns": []},
        "risk_flags": {
            "denylist_file": str(denylist),
            "unlock_overrides_file": str(unlocks),
            "minor_unlock_penalty_factor": 0.85,
        },
    }

    f = UniverseFilters(cfg)
    out = f.apply_all([
        {"symbol": "MAJORUSDT", "base": "MAJOR", "quote": "USDT", "quote_volume_24h": 1, "market_cap": 100},
        {"symbol": "MINORUSDT", "base": "MINOR", "quote": "USDT", "quote_volume_24h": 1, "market_cap": 100},
    ])

    assert [x["symbol"] for x in out] == ["MINORUSDT"]
    assert out[0]["risk_flags"] == ["minor_unlock_within_14d"]
    assert out[0]["soft_penalties"] == {"minor_unlock_within_14d": 0.85}
