from scanner.config import ScannerConfig, validate_config


def _offline_base() -> dict:
    return {
        "general": {"run_mode": "offline"},
        "universe_filters": {"market_cap": {"min_usd": 1, "max_usd": 2}},
    }


def test_v421_defaults_are_applied_when_new_blocks_missing() -> None:
    cfg = ScannerConfig(raw=_offline_base())

    assert cfg.budget_shortlist_size == 200
    assert cfg.budget_orderbook_top_k == 200
    assert cfg.pre_shortlist_market_cap_floor_usd == 25_000_000

    assert cfg.tradeability_enabled is True
    assert cfg.tradeability_notional_total_usdt == 20_000
    assert cfg.tradeability_notional_chunk_usdt == 5_000
    assert cfg.tradeability_max_tranches == 4
    assert cfg.tradeability_band_pct == 1.0
    assert cfg.tradeability_max_spread_pct == 0.15
    assert cfg.tradeability_min_depth_1pct_usd == 200_000
    assert cfg.tradeability_class_thresholds["direct_ok_max_slippage_bps"] == 50
    assert cfg.tradeability_class_thresholds["tranche_ok_max_slippage_bps"] == 100
    assert cfg.tradeability_class_thresholds["marginal_max_slippage_bps"] == 150

    assert cfg.risk_enabled is True
    assert cfg.risk_stop_method == "atr_multiple"
    assert cfg.risk_atr_period == 14
    assert cfg.risk_atr_timeframe == "1d"
    assert cfg.risk_atr_multiple == 2.0
    assert cfg.risk_min_stop_distance_pct == 4.0
    assert cfg.risk_max_stop_distance_pct == 12.0
    assert cfg.risk_min_rr_to_target_1 == 1.3
    assert cfg.risk_min_rr_to_tp10 == 1.3

    assert cfg.decision_enabled is True
    assert cfg.decision_min_score_for_enter == 65
    assert cfg.decision_min_score_for_wait == 40
    assert cfg.decision_require_tradeability_for_enter is True
    assert cfg.decision_require_risk_acceptable_for_enter is True
    assert cfg.decision_min_effective_rr_to_target_2_for_enter == 1.0

    assert cfg.btc_regime_enabled is True
    assert cfg.btc_regime_mode == "threshold_modifier"
    assert cfg.btc_regime_risk_off_enter_boost == 15


def test_v421_invalid_threshold_order_fails() -> None:
    raw = _offline_base()
    raw["tradeability"] = {
        "class_thresholds": {
            "direct_ok_max_slippage_bps": 120,
            "tranche_ok_max_slippage_bps": 100,
            "marginal_max_slippage_bps": 150,
        }
    }

    errors = validate_config(ScannerConfig(raw=raw))
    assert any("tradeability.class_thresholds must satisfy" in e for e in errors)


def test_v421_unknown_btc_mode_fails() -> None:
    raw = _offline_base()
    raw["btc_regime"] = {"mode": "something_else"}

    errors = validate_config(ScannerConfig(raw=raw))
    assert any("btc_regime.mode" in e for e in errors)


def test_v421_enabled_flags_can_be_false() -> None:
    raw = _offline_base()
    raw.update(
        {
            "tradeability": {"enabled": False},
            "risk": {"enabled": False},
            "decision": {"enabled": False},
            "btc_regime": {"enabled": False},
            "shadow": {"mode": "legacy_only"},
        }
    )

    errors = validate_config(ScannerConfig(raw=raw))
    assert errors == []


def test_v421_budget_block_must_be_mapping_when_present() -> None:
    for invalid_budget in ["bad", [], True]:
        raw = _offline_base()
        raw["budget"] = invalid_budget

        errors = validate_config(ScannerConfig(raw=raw))
        assert "budget must be an object" in errors


def test_v421_budget_null_uses_defaults() -> None:
    raw = _offline_base()
    raw["budget"] = None

    cfg = ScannerConfig(raw=raw)
    errors = validate_config(cfg)

    assert errors == []
    assert cfg.budget_shortlist_size == 200
    assert cfg.budget_orderbook_top_k == 200
    assert cfg.pre_shortlist_market_cap_floor_usd == 25_000_000


def test_v421_budget_accessors_accept_scientific_notation_strings() -> None:
    raw = _offline_base()
    raw["budget"] = {
        "shortlist_size": "2e2",
        "orderbook_top_k": "2e2",
        "pre_shortlist_market_cap_floor_usd": "2.5e7",
    }

    cfg = ScannerConfig(raw=raw)
    errors = validate_config(cfg)

    assert errors == []
    assert cfg.budget_shortlist_size == 200
    assert cfg.budget_orderbook_top_k == 200
    assert cfg.pre_shortlist_market_cap_floor_usd == 25_000_000


def test_v421_budget_integer_fields_reject_fractional_values() -> None:
    raw = _offline_base()
    raw["budget"] = {
        "shortlist_size": "2.5",
        "orderbook_top_k": 2.5,
    }

    errors = validate_config(ScannerConfig(raw=raw))

    assert "budget.shortlist_size must be an integer" in errors
    assert "budget.orderbook_top_k must be an integer" in errors


def test_v421_budget_values_reject_bool_and_negative() -> None:
    raw = _offline_base()
    raw["budget"] = {
        "shortlist_size": False,
        "orderbook_top_k": True,
        "pre_shortlist_market_cap_floor_usd": -1,
    }

    errors = validate_config(ScannerConfig(raw=raw))

    assert "budget.shortlist_size must be numeric" in errors
    assert "budget.orderbook_top_k must be numeric" in errors
    assert any("budget.pre_shortlist_market_cap_floor_usd" in e and "must be >= 0" in e for e in errors)


def test_v421_shadow_mode_defaults_and_validation() -> None:
    cfg = ScannerConfig(raw=_offline_base())
    assert cfg.shadow_mode == "parallel"

    invalid = _offline_base()
    invalid["shadow"] = {"mode": "bad"}
    errors = validate_config(ScannerConfig(raw=invalid))
    assert any("shadow.mode" in e for e in errors)


def test_v421_shadow_new_path_requires_complete_stage_enablement() -> None:
    raw = _offline_base()
    raw["shadow"] = {"mode": "new_only"}
    raw["decision"] = {"enabled": False}

    errors = validate_config(ScannerConfig(raw=raw))
    assert "shadow.mode=new_only requires decision.enabled=true" in errors


def test_v421_shadow_primary_path_validation_and_contradictions() -> None:
    invalid = _offline_base()
    invalid["shadow"] = {"mode": "parallel", "primary_path": "bad"}
    errors = validate_config(ScannerConfig(raw=invalid))
    assert "shadow.primary_path must be one of ['legacy', 'new']" in errors

    contradictory = _offline_base()
    contradictory["shadow"] = {"mode": "legacy_only", "primary_path": "new"}
    errors = validate_config(ScannerConfig(raw=contradictory))
    assert "shadow.mode=legacy_only requires shadow.primary_path=legacy" in errors


def test_v421_shadow_parallel_allows_missing_primary_path_default_resolution() -> None:
    raw = _offline_base()
    raw["shadow"] = {"mode": "parallel"}

    errors = validate_config(ScannerConfig(raw=raw))

    assert errors == []


def test_v421_invalid_min_effective_rr_for_enter_fails() -> None:
    raw = _offline_base()
    raw["decision"] = {"min_effective_rr_to_target_2_for_enter": "bad"}

    errors = validate_config(ScannerConfig(raw=raw))
    assert "decision.min_effective_rr_to_target_2_for_enter must be numeric" in errors
