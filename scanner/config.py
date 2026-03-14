"""
Configuration loading and validation.
Loads config.yml and applies environment variable overrides.
"""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping
import yaml


CONFIG_PATH = os.getenv("SCANNER_CONFIG_PATH", "config/config.yml")

_BUDGET_DEFAULTS = {
    "shortlist_size": 200,
    "orderbook_top_k": 200,
    "pre_shortlist_market_cap_floor_usd": 25_000_000,
}


def resolve_risk_min_rr_to_target_1(risk_cfg: Mapping[str, Any] | None) -> float:
    """Resolve RR threshold with canonical-key precedence and legacy alias fallback."""
    cfg = risk_cfg if isinstance(risk_cfg, Mapping) else {}

    if "min_rr_to_target_1" in cfg:
        value = cfg.get("min_rr_to_target_1")
        source = "risk.min_rr_to_target_1"
    elif "min_rr_to_tp10" in cfg:
        value = cfg.get("min_rr_to_tp10")
        source = "risk.min_rr_to_tp10"
    else:
        return 1.3

    if isinstance(value, bool) or value is None:
        raise ValueError(f"{source} must be numeric")

    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source} must be numeric") from exc

    if not math.isfinite(parsed):
        raise ValueError(f"{source} must be finite")
    if parsed < 0:
        raise ValueError(f"{source} ({parsed}) must be >= 0")

    return parsed


@dataclass
class ScannerConfig:
    """
    Scanner configuration wrapper.
    Provides type-safe access to config values.
    """

    raw: Dict[str, Any]

    # Version
    @property
    def spec_version(self) -> str:
        return self.raw.get("version", {}).get("spec", "1.0")

    @property
    def config_version(self) -> str:
        return self.raw.get("version", {}).get("config", "1.0")

    # General
    @property
    def run_mode(self) -> str:
        return self.raw.get("general", {}).get("run_mode", "standard")

    @property
    def timezone(self) -> str:
        return self.raw.get("general", {}).get("timezone", "UTC")

    @property
    def shortlist_size(self) -> int:
        budget_cfg = self.raw.get("budget", {})
        if "shortlist_size" in budget_cfg:
            return budget_cfg.get("shortlist_size", 200)
        if "shortlist_size" in self.raw.get("general", {}):
            return self.raw.get("general", {}).get("shortlist_size", 100)
        return 200

    @property
    def lookback_days_1d(self) -> int:
        return self.raw.get("general", {}).get("lookback_days_1d", 120)

    @property
    def lookback_days_4h(self) -> int:
        return self.raw.get("general", {}).get("lookback_days_4h", 30)

    # Data Sources
    @property
    def mexc_enabled(self) -> bool:
        return self.raw.get("data_sources", {}).get("mexc", {}).get("enabled", True)

    @property
    def cmc_api_key(self) -> str:
        """Get CMC API key from ENV or config."""
        env_var = self.raw.get("data_sources", {}).get("market_cap", {}).get("api_key_env_var", "CMC_API_KEY")
        return os.getenv(env_var, "")

    # Budget
    def _budget_mapping(self) -> Dict[str, Any]:
        budget_cfg = self.raw.get("budget")
        if isinstance(budget_cfg, dict):
            return budget_cfg
        return {}

    @property
    def budget_shortlist_size(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get("shortlist_size", _BUDGET_DEFAULTS["shortlist_size"]),
            "budget.shortlist_size",
        )

    @property
    def budget_orderbook_top_k(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get("orderbook_top_k", _BUDGET_DEFAULTS["orderbook_top_k"]),
            "budget.orderbook_top_k",
        )

    @property
    def pre_shortlist_market_cap_floor_usd(self) -> int:
        return _parse_integer_budget_value(
            self._budget_mapping().get(
                "pre_shortlist_market_cap_floor_usd",
                _BUDGET_DEFAULTS["pre_shortlist_market_cap_floor_usd"],
            ),
            "budget.pre_shortlist_market_cap_floor_usd",
        )

    # Universe Filters (legacy soft priors)
    @property
    def market_cap_min(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("min_usd", 100_000_000)

    @property
    def market_cap_max(self) -> int:
        return self.raw.get("universe_filters", {}).get("market_cap", {}).get("max_usd", 10_000_000_000)

    @property
    def min_turnover_24h(self) -> float:
        return float(self.raw.get("universe_filters", {}).get("volume", {}).get("min_turnover_24h", 0.03))

    @property
    def min_mexc_quote_volume_24h_usdt(self) -> float:
        volume_cfg = self.raw.get("universe_filters", {}).get("volume", {})
        if "min_mexc_quote_volume_24h_usdt" in volume_cfg:
            return float(volume_cfg.get("min_mexc_quote_volume_24h_usdt", 5_000_000))
        return float(volume_cfg.get("min_quote_volume_24h", 5_000_000))

    @property
    def min_mexc_share_24h(self) -> float:
        return float(self.raw.get("universe_filters", {}).get("volume", {}).get("min_mexc_share_24h", 0.01))

    @property
    def min_quote_volume_24h(self) -> float:
        """Backward-compatible alias for runtime metadata export."""
        return self.min_mexc_quote_volume_24h_usdt

    @property
    def scoring_volume_source(self) -> str:
        return str(self.raw.get("scoring", {}).get("volume_source", "mexc"))

    @property
    def min_history_days_1d(self) -> int:
        return self.raw.get("universe_filters", {}).get("history", {}).get("min_history_days_1d", 60)

    # Tradeability
    @property
    def tradeability_enabled(self) -> bool:
        return self.raw.get("tradeability", {}).get("enabled", True)

    @property
    def tradeability_notional_total_usdt(self) -> float:
        return float(self.raw.get("tradeability", {}).get("notional_total_usdt", 20_000))

    @property
    def tradeability_notional_chunk_usdt(self) -> float:
        return float(self.raw.get("tradeability", {}).get("notional_chunk_usdt", 5_000))

    @property
    def tradeability_max_tranches(self) -> int:
        return int(self.raw.get("tradeability", {}).get("max_tranches", 4))

    @property
    def tradeability_band_pct(self) -> float:
        return float(self.raw.get("tradeability", {}).get("band_pct", 1.0))

    @property
    def tradeability_max_spread_pct(self) -> float:
        return float(self.raw.get("tradeability", {}).get("max_spread_pct", 0.15))

    @property
    def tradeability_min_depth_1pct_usd(self) -> float:
        return float(self.raw.get("tradeability", {}).get("min_depth_1pct_usd", 200_000))

    @property
    def tradeability_class_thresholds(self) -> Dict[str, Any]:
        return self.raw.get("tradeability", {}).get(
            "class_thresholds",
            {
                "direct_ok_max_slippage_bps": 50,
                "tranche_ok_max_slippage_bps": 100,
                "marginal_max_slippage_bps": 150,
            },
        )

    # Risk
    @property
    def risk_enabled(self) -> bool:
        return self.raw.get("risk", {}).get("enabled", True)

    @property
    def risk_stop_method(self) -> str:
        return str(self.raw.get("risk", {}).get("stop_method", "atr_multiple"))

    @property
    def risk_atr_period(self) -> int:
        return int(self.raw.get("risk", {}).get("atr_period", 14))

    @property
    def risk_atr_timeframe(self) -> str:
        return str(self.raw.get("risk", {}).get("atr_timeframe", "1d"))

    @property
    def risk_atr_multiple(self) -> float:
        return float(self.raw.get("risk", {}).get("atr_multiple", 2.0))

    @property
    def risk_min_stop_distance_pct(self) -> float:
        return float(self.raw.get("risk", {}).get("min_stop_distance_pct", 4.0))

    @property
    def risk_max_stop_distance_pct(self) -> float:
        return float(self.raw.get("risk", {}).get("max_stop_distance_pct", 12.0))

    @property
    def risk_min_rr_to_target_1(self) -> float:
        risk_cfg = self.raw.get("risk", {})
        return resolve_risk_min_rr_to_target_1(risk_cfg if isinstance(risk_cfg, Mapping) else {})

    @property
    def risk_min_rr_to_tp10(self) -> float:
        """Backward-compatible alias for the canonical risk_min_rr_to_target_1 accessor."""
        return self.risk_min_rr_to_target_1

    # Decision
    @property
    def decision_enabled(self) -> bool:
        return self.raw.get("decision", {}).get("enabled", True)

    @property
    def decision_min_score_for_enter(self) -> int:
        return int(self.raw.get("decision", {}).get("min_score_for_enter", 65))

    @property
    def decision_min_score_for_wait(self) -> int:
        return int(self.raw.get("decision", {}).get("min_score_for_wait", 40))

    @property
    def decision_require_tradeability_for_enter(self) -> bool:
        return self.raw.get("decision", {}).get("require_tradeability_for_enter", True)

    @property
    def decision_require_risk_acceptable_for_enter(self) -> bool:
        return self.raw.get("decision", {}).get("require_risk_acceptable_for_enter", True)

    @property
    def decision_min_effective_rr_to_target_2_for_enter(self) -> float:
        return float(self.raw.get("decision", {}).get("min_effective_rr_to_target_2_for_enter", 1.0))

    # BTC regime
    @property
    def btc_regime_enabled(self) -> bool:
        return self.raw.get("btc_regime", {}).get("enabled", True)

    @property
    def btc_regime_mode(self) -> str:
        return str(self.raw.get("btc_regime", {}).get("mode", "threshold_modifier"))

    @property
    def btc_regime_risk_off_enter_boost(self) -> float:
        return float(self.raw.get("btc_regime", {}).get("risk_off_enter_boost", 15))

    # Shadow mode
    @property
    def shadow_mode(self) -> str:
        shadow_cfg = self.raw.get("shadow")
        if isinstance(shadow_cfg, dict):
            return str(shadow_cfg.get("mode", "parallel"))
        return "parallel"

    # Exclusions
    @property
    def exclude_stablecoins(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_stablecoins", True)

    @property
    def exclude_wrapped(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_wrapped_tokens", True)

    @property
    def exclude_leveraged(self) -> bool:
        return self.raw.get("exclusions", {}).get("exclude_leveraged_tokens", True)

    # Logging
    @property
    def log_level(self) -> str:
        return self.raw.get("logging", {}).get("level", "INFO")

    @property
    def log_to_file(self) -> bool:
        return self.raw.get("logging", {}).get("log_to_file", True)

    @property
    def log_file(self) -> str:
        return self.raw.get("logging", {}).get("file", "logs/scanner.log")


def load_config(path: str | Path | None = None) -> ScannerConfig:
    """
    Load configuration from YAML file.

    Args:
        path: Path to config.yml (default: config/config.yml)

    Returns:
        ScannerConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config is invalid YAML
    """
    cfg_path = Path(path) if path else Path(CONFIG_PATH)

    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return ScannerConfig(raw=raw)


def _expect_number(errors: List[str], value: Any, field_name: str, *, minimum: float | None = None, maximum: float | None = None) -> float | None:
    if isinstance(value, bool) or value is None:
        errors.append(f"{field_name} must be numeric")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be numeric")
        return None

    if not math.isfinite(number):
        errors.append(f"{field_name} must be finite")
        return None

    if minimum is not None and number < minimum:
        errors.append(f"{field_name} ({number}) must be >= {minimum}")
    if maximum is not None and number > maximum:
        errors.append(f"{field_name} ({number}) must be <= {maximum}")
    return number


def _expect_integer_number(
    errors: List[str],
    value: Any,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> int | None:
    number = _expect_number(errors, value, field_name, minimum=minimum, maximum=maximum)
    if number is None:
        return None
    if not number.is_integer():
        errors.append(f"{field_name} must be an integer")
        return None
    return int(number)


def _parse_integer_budget_value(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be numeric")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if not number.is_integer():
        raise ValueError(f"{field_name} must be an integer")

    return int(number)


def validate_config(config: ScannerConfig) -> List[str]:
    """
    Validate configuration.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check run_mode
    valid_modes = ["standard", "fast", "offline", "backtest"]
    if config.run_mode not in valid_modes:
        errors.append(f"Invalid run_mode: {config.run_mode}. Must be one of {valid_modes}")

    # Check market cap range
    if config.market_cap_min >= config.market_cap_max:
        errors.append(f"market_cap_min ({config.market_cap_min}) must be < market_cap_max ({config.market_cap_max})")

    # Check CMC API key (if needed)
    if not config.cmc_api_key and config.run_mode == "standard":
        errors.append("CMC_API_KEY environment variable not set")

    # Universe volume-gate configuration
    if config.min_turnover_24h < 0:
        errors.append(f"min_turnover_24h ({config.min_turnover_24h}) must be >= 0")

    if config.min_mexc_quote_volume_24h_usdt < 0:
        errors.append(
            f"min_mexc_quote_volume_24h_usdt ({config.min_mexc_quote_volume_24h_usdt}) must be >= 0"
        )

    if not (0 <= config.min_mexc_share_24h <= 1):
        errors.append(f"min_mexc_share_24h ({config.min_mexc_share_24h}) must be in [0, 1]")

    valid_volume_sources = ["mexc", "global_fallback_mexc"]
    if config.scoring_volume_source not in valid_volume_sources:
        errors.append(
            f"scoring.volume_source ({config.scoring_volume_source}) must be one of {valid_volume_sources}"
        )

    # Budget defaults / limits
    budget_cfg = config.raw.get("budget")
    if budget_cfg is None:
        budget_cfg = {}
    elif not isinstance(budget_cfg, dict):
        errors.append("budget must be an object")
        budget_cfg = {}

    _expect_integer_number(
        errors,
        budget_cfg.get("shortlist_size", _BUDGET_DEFAULTS["shortlist_size"]),
        "budget.shortlist_size",
        minimum=1,
    )
    _expect_integer_number(
        errors,
        budget_cfg.get("orderbook_top_k", _BUDGET_DEFAULTS["orderbook_top_k"]),
        "budget.orderbook_top_k",
        minimum=1,
    )
    _expect_integer_number(
        errors,
        budget_cfg.get("pre_shortlist_market_cap_floor_usd", _BUDGET_DEFAULTS["pre_shortlist_market_cap_floor_usd"]),
        "budget.pre_shortlist_market_cap_floor_usd",
        minimum=0,
    )

    # Tradeability block
    tradeability_cfg = config.raw.get("tradeability", {})
    if "enabled" in tradeability_cfg and not isinstance(tradeability_cfg.get("enabled"), bool):
        errors.append("tradeability.enabled must be boolean")
    _expect_number(errors, tradeability_cfg.get("notional_total_usdt", 20_000), "tradeability.notional_total_usdt", minimum=0)
    _expect_number(errors, tradeability_cfg.get("notional_chunk_usdt", 5_000), "tradeability.notional_chunk_usdt", minimum=0)
    _expect_number(errors, tradeability_cfg.get("max_tranches", 4), "tradeability.max_tranches", minimum=1)
    _expect_number(errors, tradeability_cfg.get("band_pct", 1.0), "tradeability.band_pct", minimum=0)
    _expect_number(errors, tradeability_cfg.get("max_spread_pct", 0.15), "tradeability.max_spread_pct", minimum=0)
    _expect_number(errors, tradeability_cfg.get("min_depth_1pct_usd", 200_000), "tradeability.min_depth_1pct_usd", minimum=0)

    class_thresholds = tradeability_cfg.get("class_thresholds")
    if class_thresholds is None:
        class_thresholds = {
            "direct_ok_max_slippage_bps": 50,
            "tranche_ok_max_slippage_bps": 100,
            "marginal_max_slippage_bps": 150,
        }
    if not isinstance(class_thresholds, dict):
        errors.append("tradeability.class_thresholds must be an object")
    else:
        required = [
            "direct_ok_max_slippage_bps",
            "tranche_ok_max_slippage_bps",
            "marginal_max_slippage_bps",
        ]
        missing = [key for key in required if key not in class_thresholds]
        if missing:
            errors.append(f"tradeability.class_thresholds missing keys: {missing}")
        else:
            d = _expect_number(errors, class_thresholds.get(required[0]), f"tradeability.class_thresholds.{required[0]}", minimum=0)
            t = _expect_number(errors, class_thresholds.get(required[1]), f"tradeability.class_thresholds.{required[1]}", minimum=0)
            m = _expect_number(errors, class_thresholds.get(required[2]), f"tradeability.class_thresholds.{required[2]}", minimum=0)
            if d is not None and t is not None and m is not None and not (d <= t <= m):
                errors.append(
                    "tradeability.class_thresholds must satisfy direct_ok_max_slippage_bps <= tranche_ok_max_slippage_bps <= marginal_max_slippage_bps"
                )

    # Risk block
    risk_cfg = config.raw.get("risk", {})
    if "enabled" in risk_cfg and not isinstance(risk_cfg.get("enabled"), bool):
        errors.append("risk.enabled must be boolean")
    if str(risk_cfg.get("stop_method", "atr_multiple")) != "atr_multiple":
        errors.append("risk.stop_method must be 'atr_multiple' in Phase 1")
    _expect_number(errors, risk_cfg.get("atr_period", 14), "risk.atr_period", minimum=1)
    if str(risk_cfg.get("atr_timeframe", "1d")) not in ["1d"]:
        errors.append("risk.atr_timeframe must be '1d' in Phase 1")
    _expect_number(errors, risk_cfg.get("atr_multiple", 2.0), "risk.atr_multiple", minimum=0)
    min_stop = _expect_number(errors, risk_cfg.get("min_stop_distance_pct", 4.0), "risk.min_stop_distance_pct", minimum=0)
    max_stop = _expect_number(errors, risk_cfg.get("max_stop_distance_pct", 12.0), "risk.max_stop_distance_pct", minimum=0)
    if min_stop is not None and max_stop is not None and min_stop > max_stop:
        errors.append("risk.min_stop_distance_pct must be <= risk.max_stop_distance_pct")
    if "min_rr_to_target_1" in risk_cfg:
        _expect_number(errors, risk_cfg.get("min_rr_to_target_1"), "risk.min_rr_to_target_1", minimum=0)
    elif "min_rr_to_tp10" in risk_cfg:
        _expect_number(errors, risk_cfg.get("min_rr_to_tp10"), "risk.min_rr_to_tp10", minimum=0)

    # Decision block
    decision_cfg = config.raw.get("decision", {})
    if "enabled" in decision_cfg and not isinstance(decision_cfg.get("enabled"), bool):
        errors.append("decision.enabled must be boolean")
    min_enter = _expect_number(errors, decision_cfg.get("min_score_for_enter", 65), "decision.min_score_for_enter", minimum=0, maximum=100)
    min_wait = _expect_number(errors, decision_cfg.get("min_score_for_wait", 40), "decision.min_score_for_wait", minimum=0, maximum=100)
    if min_enter is not None and min_wait is not None and min_wait > min_enter:
        errors.append("decision.min_score_for_wait must be <= decision.min_score_for_enter")
    for bool_key in ["require_tradeability_for_enter", "require_risk_acceptable_for_enter"]:
        if bool_key in decision_cfg and not isinstance(decision_cfg.get(bool_key), bool):
            errors.append(f"decision.{bool_key} must be boolean")
    _expect_number(
        errors,
        decision_cfg.get("min_effective_rr_to_target_2_for_enter", 1.0),
        "decision.min_effective_rr_to_target_2_for_enter",
        minimum=0,
    )

    # BTC regime block
    btc_cfg = config.raw.get("btc_regime", {})
    if "enabled" in btc_cfg and not isinstance(btc_cfg.get("enabled"), bool):
        errors.append("btc_regime.enabled must be boolean")
    mode = str(btc_cfg.get("mode", "threshold_modifier"))
    if mode != "threshold_modifier":
        errors.append("btc_regime.mode must be 'threshold_modifier'")
    _expect_number(errors, btc_cfg.get("risk_off_enter_boost", 15), "btc_regime.risk_off_enter_boost")

    # Shadow mode / parallel run block
    shadow_cfg = config.raw.get("shadow")
    if shadow_cfg is None:
        shadow_cfg = {}
    elif not isinstance(shadow_cfg, dict):
        errors.append("shadow must be an object")
        shadow_cfg = {}

    shadow_mode = str(shadow_cfg.get("mode", "parallel"))
    allowed_shadow_modes = ["legacy_only", "new_only", "parallel"]
    configured_primary = None
    has_configured_primary = "primary_path" in shadow_cfg

    if has_configured_primary:
        configured_primary = str(shadow_cfg.get("primary_path"))
        if configured_primary not in ["legacy", "new"]:
            errors.append("shadow.primary_path must be one of ['legacy', 'new']")

    if shadow_mode not in allowed_shadow_modes:
        errors.append(f"shadow.mode ({shadow_mode}) must be one of {allowed_shadow_modes}")
    else:
        if shadow_mode in {"new_only", "parallel"}:
            if not config.tradeability_enabled:
                errors.append(f"shadow.mode={shadow_mode} requires tradeability.enabled=true")
            if not config.risk_enabled:
                errors.append(f"shadow.mode={shadow_mode} requires risk.enabled=true")
            if not config.decision_enabled:
                errors.append(f"shadow.mode={shadow_mode} requires decision.enabled=true")

        if configured_primary in {"legacy", "new"}:
            if shadow_mode == "legacy_only" and configured_primary != "legacy":
                errors.append("shadow.mode=legacy_only requires shadow.primary_path=legacy")
            if shadow_mode == "new_only" and configured_primary != "new":
                errors.append("shadow.mode=new_only requires shadow.primary_path=new")

    return errors
