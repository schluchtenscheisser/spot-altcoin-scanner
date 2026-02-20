from scanner.pipeline.discovery import compute_discovery_fields
from scanner.pipeline.scoring.breakout import score_breakouts


def _features(*, last_closed_1d: int = 150, last_closed_4h: int = 100, discovery: bool = True):
    return {
        "TESTUSDT": {
            "1d": {
                "breakout_dist_20": 3.0,
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
                "dist_ema20_pct": 2.0,
                "dist_ema50_pct": 3.0,
                "r_7": 5.0,
            },
            "4h": {
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
                "dist_ema20_pct": 1.0,
                "dist_ema50_pct": 1.0,
            },
            "meta": {
                "last_closed_idx": {
                    "1d": last_closed_1d,
                    "4h": last_closed_4h,
                }
            },
            "discovery": discovery,
            "discovery_age_days": 30 if discovery else 400,
            "discovery_source": "cmc_date_added" if discovery else "first_seen_ts",
        }
    }


def test_discovery_uses_cmc_date_added_when_available():
    fields = compute_discovery_fields(
        asof_ts_ms=1_700_000_000_000,
        date_added="2023-10-26T00:00:00Z",
        first_seen_ts=1_600_000_000_000,
        max_age_days=10_000,
    )
    assert fields["discovery"] is True
    assert fields["discovery_source"] == "cmc_date_added"


def test_discovery_falls_back_to_first_seen_ts_when_cmc_missing():
    fields = compute_discovery_fields(
        asof_ts_ms=1_700_000_000_000,
        date_added=None,
        first_seen_ts=1_699_000_000_000,
        max_age_days=180,
    )
    assert fields["discovery"] is True
    assert fields["discovery_source"] == "first_seen_ts"


def test_discovery_fields_are_included_for_valid_scored_setup():
    cfg = {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}}
    out = score_breakouts(_features(), {"TESTUSDT": 1_000_000}, cfg)
    assert len(out) == 1
    assert out[0]["discovery"] is True
    assert out[0]["discovery_source"] == "cmc_date_added"


def test_discovery_tag_is_gated_by_valid_setup_history_gate():
    cfg = {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}}
    out = score_breakouts(
        _features(last_closed_1d=5, last_closed_4h=5, discovery=True),
        {"TESTUSDT": 1_000_000},
        cfg,
    )
    assert out == []
