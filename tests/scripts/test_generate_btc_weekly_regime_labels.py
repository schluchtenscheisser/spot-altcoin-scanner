from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import pytest

from scripts.generate_btc_weekly_regime_labels import generate_payload, main


def _write_btc_dataset(
    root: Path,
    closes: list[float],
    *,
    drop_indices: set[int] | None = None,
) -> None:
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    rows = []
    drop_indices = drop_indices or set()
    for i, close in enumerate(closes):
        if i in drop_indices:
            continue
        ts = start + pd.Timedelta(days=i)
        rows.append(
            {
                "source": "binance",
                "symbol": "BTCUSDT",
                "timeframe": "1d",
                "open_time_utc": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "close_time_utc": (ts + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": close,
                "high": close,
                "low": close,
                "close": close,
                "volume": 1.0,
                "quote_volume": 1.0,
                "trade_count": 1,
                "is_closed": True,
                "fetch_run_id": "run-1",
                "fetched_at_utc": "2026-05-20T00:00:00Z",
            }
        )
    df = pd.DataFrame(rows)
    df["open_ts"] = pd.to_datetime(df["open_time_utc"], utc=True)
    for (year, month), g in df.groupby([df["open_ts"].dt.year, df["open_ts"].dt.month]):
        p = root / f"timeframe=1d/symbol=BTCUSDT/year={year:04d}/month={month:02d}/part-000.parquet"
        p.parent.mkdir(parents=True, exist_ok=True)
        g.drop(columns=["open_ts"]).to_parquet(p, index=False)


def _write_manifests(tmp_path: Path) -> tuple[Path, Path]:
    history_manifest = tmp_path / "history_manifest.json"
    symbol_comp = tmp_path / "symbol_completeness.json"
    history_manifest.write_text(json.dumps({"fetch_run_id": "pre1-run", "created_at_utc": "2026-05-20T19:48:04Z", "fetch_start_date": "2025-01-01", "effective_fetch_end_date": "2026-05-19", "closed_bar_only": True}), encoding="utf-8")
    symbol_comp.write_text(json.dumps({"fetch_run_id": "pre1-run", "created_at_utc": "2026-05-20T19:48:04Z"}), encoding="utf-8")
    return history_manifest, symbol_comp


def test_return_and_realized_vol_and_schema(tmp_path: Path) -> None:
    root = tmp_path / "ohlcv"
    closes = [100.0 + i for i in range(70)]
    _write_btc_dataset(root, closes)
    history_manifest, symbol_comp = _write_manifests(tmp_path)

    payload = generate_payload(history_root=root, history_manifest_path=history_manifest, symbol_completeness_path=symbol_comp)

    assert payload["schema_version"] == "regime_labels_btc_weekly_30d_return_vol_v1"
    assert payload["status"] == "frozen"
    assert payload["source"]["history_manifest"]["fetch_run_id"] == "pre1-run"
    assert payload["method"]["method_id"] == "btc_weekly_30d_return_vol_v1"
    assert payload["labels"]

    first = payload["labels"][0]
    end_date = pd.Timestamp(first["week_end_date"] + "T00:00:00Z")
    end_idx = (end_date - pd.Timestamp("2026-01-01T00:00:00Z")).days
    expected_return = (closes[end_idx] / closes[end_idx - 30] - 1.0) * 100.0
    assert first["btc_30d_return_pct"] == pytest.approx(expected_return)

    rets = [math.log(closes[i] / closes[i - 1]) for i in range(end_idx - 29, end_idx + 1)]
    expected_vol = pd.Series(rets).std(ddof=1) * math.sqrt(365.0) * 100.0
    assert first["btc_30d_realized_vol_annualized_pct"] == pytest.approx(expected_vol)


def test_snapshot_ending_on_sunday_keeps_latest_week(tmp_path: Path) -> None:
    root = tmp_path / "ohlcv"
    closes = [200.0 + i * 0.5 for i in range(74)]  # last bar: 2026-03-15 Sunday
    _write_btc_dataset(root, closes)
    history_manifest, symbol_comp = _write_manifests(tmp_path)

    payload = generate_payload(history_root=root, history_manifest_path=history_manifest, symbol_completeness_path=symbol_comp)
    labels = payload["labels"]
    assert labels == sorted(labels, key=lambda row: row["week_start_date"])
    assert labels[-1]["week_end_date"] == "2026-03-15"
    latest_bar = pd.Timestamp("2026-01-01T00:00:00Z") + pd.Timedelta(days=73)
    assert latest_bar.day_name() == "Sunday"
    latest_iso = latest_bar.isocalendar()
    assert pd.Timestamp(labels[-1]["week_end_date"]).isocalendar()[:2] == (latest_iso.year, latest_iso.week)


def test_snapshot_ending_midweek_excludes_latest_incomplete_week(tmp_path: Path) -> None:
    root = tmp_path / "ohlcv"
    closes = [210.0 + i * 0.3 for i in range(71)]  # last bar: 2026-03-12 Thursday
    _write_btc_dataset(root, closes)
    history_manifest, symbol_comp = _write_manifests(tmp_path)

    payload = generate_payload(history_root=root, history_manifest_path=history_manifest, symbol_completeness_path=symbol_comp)
    labels = payload["labels"]
    latest_bar = pd.Timestamp("2026-01-01T00:00:00Z") + pd.Timedelta(days=70)
    assert latest_bar.day_name() == "Thursday"
    latest_iso = latest_bar.isocalendar()
    assert all(
        pd.Timestamp(label["week_end_date"]).isocalendar()[:2] != (latest_iso.year, latest_iso.week)
        for label in labels
    )
    assert labels[-1]["week_end_date"] == "2026-03-08"


def test_week_with_missing_day_is_excluded_even_if_not_latest(tmp_path: Path) -> None:
    root = tmp_path / "ohlcv"
    closes = [220.0 + i * 0.2 for i in range(80)]
    # Drop Wednesday 2026-02-18 from an interior week (Mon 16 .. Sun 22)
    _write_btc_dataset(root, closes, drop_indices={48})
    history_manifest, symbol_comp = _write_manifests(tmp_path)

    payload = generate_payload(history_root=root, history_manifest_path=history_manifest, symbol_completeness_path=symbol_comp)
    labels = payload["labels"]
    assert all(label["week_start_date"] != "2026-02-16" for label in labels)
    assert any(label["week_start_date"] == "2026-02-09" for label in labels)
    assert any(label["week_start_date"] == "2026-02-23" for label in labels)


def test_json_is_deterministic_sorted_keys(tmp_path: Path) -> None:
    root = tmp_path / "ohlcv"
    closes = [100 + i for i in range(70)]
    _write_btc_dataset(root, closes)
    history_manifest, symbol_comp = _write_manifests(tmp_path)
    out = tmp_path / "out.json"

    rc = main([
        "--history-root", str(root),
        "--history-manifest", str(history_manifest),
        "--symbol-completeness", str(symbol_comp),
        "--output", str(out),
    ])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert '"created_at_utc"' in text
    assert text.index('"created_at_utc"') < text.index('"labels"')


def test_fail_fast_when_btc_missing(tmp_path: Path) -> None:
    history_manifest, symbol_comp = _write_manifests(tmp_path)
    with pytest.raises(ValueError, match="Missing BTCUSDT 1d history"):
        generate_payload(history_root=tmp_path / "ohlcv", history_manifest_path=history_manifest, symbol_completeness_path=symbol_comp)
