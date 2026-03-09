from __future__ import annotations

from pathlib import Path

import pandas as pd

from scanner.utils.raw_collector import collect_raw_marketcap



def test_collect_raw_marketcap_parquet_handles_oversized_object_ints(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("RAW_SNAPSHOT_BASEDIR", str(tmp_path / "raw"))
    monkeypatch.delenv("RAW_SNAPSHOT_RUN_ID", raising=False)

    payload = [
        {
            "id": 1,
            "symbol": "AAA",
            "minted_market_cap": 155579987314341800,
            "quote": {"USD": {"price": 1.23}},
        },
        {
            "id": 2,
            "symbol": "BBB",
            "minted_market_cap": "not_available",
            "quote": {"USD": {"price": 4.56}},
        },
        {
            "id": 3,
            "symbol": "CCC",
            "minted_market_cap": None,
            "quote": {"USD": {"price": 7.89}},
        },
    ]

    saved = collect_raw_marketcap(payload)

    assert saved is not None
    assert saved["parquet"] is not None
    assert saved["csv"] is not None

    parquet_path = Path(saved["parquet"])
    assert parquet_path.exists()

    df = pd.read_parquet(parquet_path)

    assert "minted_market_cap" in df.columns
    assert df.loc[0, "minted_market_cap"] == "155579987314341800"
    assert df.loc[1, "minted_market_cap"] == "not_available"
    assert pd.isna(df.loc[2, "minted_market_cap"])
    assert "quote__USD__price" in df.columns



def test_collect_raw_marketcap_mixed_object_column_serialization_is_deterministic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("RAW_SNAPSHOT_BASEDIR", str(tmp_path / "raw"))
    monkeypatch.delenv("RAW_SNAPSHOT_RUN_ID", raising=False)

    payload = [
        {
            "id": 1,
            "symbol": "AAA",
            "tags": ["alpha", "beta"],
            "minted_market_cap": -9007199254740993,
        },
        {
            "id": 2,
            "symbol": "BBB",
            "tags": ["gamma"],
            "minted_market_cap": float("inf"),
        },
        {
            "id": 3,
            "symbol": "CCC",
            "tags": None,
            "minted_market_cap": float("nan"),
        },
    ]

    saved = collect_raw_marketcap(payload)
    parquet_path = Path(saved["parquet"])
    df = pd.read_parquet(parquet_path)

    tags = df["tags"].tolist()
    assert tags[:2] == ['["alpha", "beta"]', '["gamma"]']
    assert pd.isna(tags[2])

    minted_values = df["minted_market_cap"].tolist()
    assert minted_values[:2] == ["-9007199254740993", "inf"]
    assert pd.isna(minted_values[2])
