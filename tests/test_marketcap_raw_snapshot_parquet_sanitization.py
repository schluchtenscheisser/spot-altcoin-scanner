import os
import pandas as pd

from scanner.utils import raw_collector


def test_collect_raw_marketcap_sanitizes_oversized_int_and_writes_parquet(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RAW_SNAPSHOT_BASEDIR", str(tmp_path))
    monkeypatch.setenv("RAW_SNAPSHOT_RUN_ID", "run-marketcap-oversized")

    data = [
        {
            "id": 1,
            "symbol": "ABC",
            "minted_market_cap": 155579987314341800,
            "quote": {"USD": {"price": 1.23}},
        },
        {
            "id": 2,
            "symbol": "DEF",
            "minted_market_cap": None,
            "quote": {"USD": {"price": 2.34}},
        },
    ]

    saved_paths = raw_collector.collect_raw_marketcap(data)

    assert saved_paths is not None
    assert saved_paths["parquet"]
    assert os.path.exists(saved_paths["parquet"])

    df_parquet = pd.read_parquet(saved_paths["parquet"])
    assert "minted_market_cap" in df_parquet.columns
    assert df_parquet.loc[0, "minted_market_cap"] == "155579987314341800"
    assert pd.isna(df_parquet.loc[1, "minted_market_cap"])
    assert df_parquet.loc[0, "quote__USD__price"] == 1.23


def test_marketcap_sanitizer_handles_mixed_object_values_deterministically():
    df = pd.DataFrame(
        {
            "mixed": [
                {"b": 2, "a": 1},
                [1, 2],
                155579987314341800,
                float("nan"),
                float("inf"),
                -float("inf"),
                None,
                "txt",
            ]
        }
    )

    sanitized = raw_collector._sanitize_object_columns_for_marketcap_parquet(df.copy())

    assert sanitized["mixed"].tolist() == [
        '{"a": 1, "b": 2}',
        "[1, 2]",
        "155579987314341800",
        "NaN",
        "Infinity",
        "-Infinity",
        None,
        "txt",
    ]


def test_marketcap_sanitizer_preserves_none_and_regular_numeric_columns():
    df = pd.DataFrame(
        {
            "minted_market_cap": pd.Series([None, 155579987314341800], dtype="object"),
            "rank": [1, 2],
        }
    )

    sanitized = raw_collector._sanitize_object_columns_for_marketcap_parquet(df.copy())

    assert sanitized["minted_market_cap"].tolist() == [None, "155579987314341800"]
    assert sanitized["rank"].tolist() == [1, 2]
