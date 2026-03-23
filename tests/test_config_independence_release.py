import textwrap

import pytest

from scanner.config import load_config, validate_config


BASE_CONFIG = """
version:
  spec: 1.0
  config: 1.0
general:
  run_mode: offline
  timezone: UTC
data_sources:
  market_cap:
    api_key_env_var: CMC_API_KEY
universe_filters:
  market_cap:
    min_usd: 100
    max_usd: 1000
  volume:
    min_turnover_24h: 0.03
    min_mexc_quote_volume_24h_usdt: 5000000
    min_mexc_share_24h: 0.01
tradeability:
  enabled: true
risk:
  enabled: true
  stop_method: atr_multiple
  atr_timeframe: 1d
decision:
  enabled: true
btc_regime:
  enabled: true
  mode: threshold_modifier
shadow:
  mode: parallel
  primary_path: new
"""


def _write_config(path, extra_yaml: str = ""):
    path.write_text(textwrap.dedent(BASE_CONFIG + extra_yaml), encoding="utf-8")


def test_load_config_adds_independence_release_defaults(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(config_path)

    config = load_config(config_path)

    assert config.independence_release == {
        "runtime": {},
        "bar_clock": {},
        "universe": {},
        "market_data_budget": {},
        "phase": {},
        "state": {},
        "invalidation": {},
        "entry": {},
        "execution": {},
        "reports": {},
        "snapshots": {},
        "retention": {},
    }
    assert validate_config(config) == []


def test_load_config_merges_partial_independence_release_override(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  reports:
    output_root: reports/runs
""",
    )

    config = load_config(config_path)

    assert config.independence_release["reports"] == {"output_root": "reports/runs"}
    assert config.independence_release["bar_clock"] == {}


def test_load_config_rejects_invalid_independence_release_section(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  bar_clock: invalid
""",
    )

    with pytest.raises(ValueError, match=r"independence_release\.bar_clock must be an object, got 'invalid'"):
        load_config(config_path)
