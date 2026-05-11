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
        "entry_location": {},
        "execution": {},
        "reports": {},
        "snapshots": {},
        "retention": {},
        "ohlcv_fetch": {},
        "cache_policy": {},
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



def test_resolve_independence_ohlcv_fetch_defaults(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(config_path)

    config = load_config(config_path)
    resolved = config.independence_ohlcv_fetch

    assert resolved["lookback_bars_1d"] == 250
    assert resolved["lookback_bars_4h"] == 250
    assert resolved["min_lookback_bars_1d"] == 120
    assert resolved["min_lookback_bars_4h"] == 120


def test_resolve_independence_ohlcv_fetch_rejects_invalid(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  ohlcv_fetch:
    lookback_bars_4h: 100
    min_lookback_bars_4h: 120
""",
    )

    with pytest.raises(ValueError, match=r"independence_release\.ohlcv_fetch\.lookback_bars_4h"):
        load_config(config_path)


def test_entry_overrides_from_independence_release_namespace_are_applied(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  entry:
    pressure_build:
      range_reclaim:
        min_reclaim: 61
""",
    )

    config = load_config(config_path)
    assert config.entry["pressure_build"]["range_reclaim"]["min_reclaim"] == 61.0


def test_top_level_entry_is_not_canonical_override_source(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
entry:
  pressure_build:
    range_reclaim:
      min_reclaim: 61
""",
    )

    config = load_config(config_path)
    assert config.entry["pressure_build"]["range_reclaim"]["min_reclaim"] == 45.0


def test_entry_malformed_phase_block_reports_clean_validation_error(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  entry:
    pressure_build: 5
""",
    )

    config = load_config(config_path)
    errors = validate_config(config)
    assert any("independence_release.entry.pressure_build" in err and "must be a mapping" in err for err in errors)


def test_entry_malformed_pattern_block_reports_clean_validation_error(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  entry:
    pressure_build:
      range_reclaim: 5
""",
    )

    config = load_config(config_path)
    errors = validate_config(config)
    assert any(
        "independence_release.entry.pressure_build.range_reclaim" in err and "must be a mapping" in err for err in errors
    )


def test_entry_malformed_nested_types_do_not_raise_attribute_error(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  entry:
    pressure_build:
      range_reclaim: 5
""",
    )

    config = load_config(config_path)
    with pytest.raises(ValueError, match=r"independence_release\.entry\.pressure_build\.range_reclaim"):
        _ = config.entry


def test_independence_snapshots_defaults_and_partial_override(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(
        config_path,
        """
independence_release:
  snapshots:
    runs_root: snapshots/custom-runs
""",
    )
    config = load_config(config_path)
    assert config.independence_snapshots == {
        "history_root": "snapshots/history",
        "runs_root": "snapshots/custom-runs",
    }


def test_independence_retention_defaults_and_validation(tmp_path) -> None:
    config_path = tmp_path / "config.yml"
    _write_config(config_path)
    config = load_config(config_path)
    assert config.independence_retention == {"run_snapshots_online_days": 90}

    _write_config(
        config_path,
        """
independence_release:
  retention:
    run_snapshots_online_days: 0
""",
    )
    with pytest.raises(ValueError, match=r"independence_release\.retention\.run_snapshots_online_days"):
        _ = load_config(config_path).independence_retention
