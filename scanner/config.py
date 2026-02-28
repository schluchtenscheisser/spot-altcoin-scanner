"""
Configuration loading and validation.
Loads config.yml and applies environment variable overrides.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import yaml


CONFIG_PATH = os.getenv("SCANNER_CONFIG_PATH", "config/config.yml")


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
        return self.raw.get("general", {}).get("shortlist_size", 100)
    
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
    
    # Universe Filters
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
    def min_history_days_1d(self) -> int:
        return self.raw.get("universe_filters", {}).get("history", {}).get("min_history_days_1d", 60)
    
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
    
    return errors
