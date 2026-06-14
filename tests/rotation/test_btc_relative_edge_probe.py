import json, math
from pathlib import Path

import pandas as pd
import pytest

from scripts.rotation.btc_relative_edge_probe import ProbeError, run, norm_label, map_tiers


def write_hist(root: Path, symbol: str, closes: dict[str, float]):
    d=root/"timeframe=1d"/f"symbol={symbol}"/"year=2026"/"month=01"
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"daily_bar_id":list(closes.keys()),"close":list(closes.values())}).to_parquet(d/"part.parquet")


def base_fixture(tmp_path):
    hist=tmp_path/"hist"
    dates=pd.date_range("2026-01-01", periods=40, freq="D").strftime("%Y-%m-%d")
    write_hist(hist,"BTCUSDT", {d:100+i for i,d in enumerate(dates)})
    write_hist(hist,"AAAUSDT", {d:10+i for i,d in enumerate(dates)})
    write_hist(hist,"BBBUSDT", {d:20+i*0.5 for i,d in enumerate(dates)})
    events=pd.DataFrame({
        "symbol":["AAAUSDT","BBBUSDT","AAA","BTCUSDT","XYZUSDT","USDCUSDT"],
        "as_of_daily_bar_id":["2026-01-01","2026-01-01","2026-01-02","2026-01-02","2026-01-03","2026-01-03"],
        "event_type":["first_confirmed_ready","first_watch","first_confirmed_ready","first_watch","first_watch","first_watch"],
        "historical_signal_bucket":["confirmed ready","watch","confirmed ready","watch","watch","watch"],
        "median_quote_volume_30d":[100]*6,
        "forward_close_return_10d":[1.0,0.25,0.833333,0.1,0.0,0.0],
        "has_forward_10d":[True]*6,
    })
    ds=tmp_path/"enriched_replay_events.parquet"; events.to_parquet(ds)
    return ds,hist


def test_missing_dataset_fails(tmp_path):
    with pytest.raises(ProbeError):
        run(["--dataset",str(tmp_path/"missing.parquet"),"--history-root",str(tmp_path)])


def test_required_minimum_field_missing_fails(tmp_path):
    ds=tmp_path/"x.parquet"; pd.DataFrame({"symbol":["A"]}).to_parquet(ds)
    hist=tmp_path/"hist"; write_hist(hist,"BTCUSDT",{"2026-01-01":1})
    with pytest.raises(ProbeError): run(["--dataset",str(ds),"--history-root",str(hist)])


def test_tier_mapping_prefer_bucket_and_fallback():
    df=pd.DataFrame({"historical_signal_bucket":["confirmed ready","watch"],"event_type":["x","y"]})
    assert map_tiers(df)["source"] == "historical_signal_bucket"
    df2=pd.DataFrame({"historical_signal_bucket":["a","b"],"event_type":["first_confirmed_ready","first_watch"]})
    assert map_tiers(df2)["source"] == "event_type"
    assert norm_label("First Confirmed-Ready") == "first_confirmed_ready"


def test_missing_btc_history_fails(tmp_path):
    ds,hist=base_fixture(tmp_path)
    (hist/"timeframe=1d"/"symbol=BTCUSDT"/"year=2026"/"month=01"/"part.parquet").unlink()
    with pytest.raises(ProbeError): run(["--dataset",str(ds),"--history-root",str(hist)])


def test_run_outputs_schema_caveats_benchmark_and_exact_alignment(tmp_path):
    ds,hist=base_fixture(tmp_path)
    out=tmp_path/"out"
    run(["--dataset",str(ds),"--history-root",str(hist),"--output-root",str(out),"--replay-id","r1","--n-bootstrap","20","--min-count","1","--min-qualifying-dates","2"])
    od=out/"r1"
    assert (od/"btc_relative_edge_probe.md").exists()
    assert (od/"btc_relative_edge_probe.json").exists()
    assert (od/"probe_manifest.json").exists()
    assert (od/"segment_relative_returns.parquet").exists()
    md=(od/"btc_relative_edge_probe.md").read_text()
    assert "This is an exploratory edge-existence probe, NOT a trading backtest." in md
    manifest=json.loads((od/"probe_manifest.json").read_text())
    assert manifest["symbol_identifier_column_used"] == "symbol"
    assert manifest["history_symbol_resolution_counts"]["base_plus_usdt"] == 1
    assert manifest["benchmark_self_excluded_count"] == 1
    assert manifest["exclusions"]["static_denylist_count"] == 1
    seg=pd.read_parquet(od/"segment_relative_returns.parquet")
    assert {"event_count","unique_symbol_count","median_relative_log_return","hit_rate_vs_btc","passes_min_count"} <= set(seg.columns)
    summary=json.loads((od/"btc_relative_edge_probe.json").read_text())
    assert "cost_log_high" in summary["cost_context"]
    assert summary["cost_context"]["cost_log_high"] == pytest.approx(math.log(1+80/10000))


def test_alternative_symbol_column_and_missing_exact_date_unavailable(tmp_path):
    hist=tmp_path/"hist"
    write_hist(hist,"BTCUSDT",{"2026-01-01":100,"2026-01-11":110})
    write_hist(hist,"AAAUSDT",{"2026-01-01":10})
    ds=tmp_path/"e.parquet"
    pd.DataFrame({"pair":["AAAUSDT"],"as_of_daily_bar_id":["2026-01-01"],"event_type":["first_confirmed_ready"],"historical_signal_bucket":["confirmed"]}).to_parquet(ds)
    # add watch to make mapping valid, but unavailable history symbol
    df=pd.read_parquet(ds); df.loc[1]=["NOPEUSDT","2026-01-01","first_watch","watch"]; df.to_parquet(ds)
    out=tmp_path/"out"
    run(["--dataset",str(ds),"--history-root",str(hist),"--output-root",str(out),"--replay-id","r2","--n-bootstrap","5","--min-count","1"])
    m=json.loads((out/"r2"/"probe_manifest.json").read_text())
    assert m["symbol_identifier_column_used"] == "pair"
    assert m["validation"]["relative_return_unavailable_by_horizon"]["10"] >= 1
