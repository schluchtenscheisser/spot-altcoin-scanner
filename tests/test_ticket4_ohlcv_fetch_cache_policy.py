from __future__ import annotations

from datetime import datetime, timezone

import pytest

from scanner.data.cache_policy import bars_missing_since_cached, get_cache_status, get_fetch_decision
from scanner.data.ohlcv_fetch import fetch_and_persist, fetch_closed_bars
from scanner.storage import init_db


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "scanner.sqlite"
    monkeypatch.setenv("SCANNER_DB_PATH", str(db_path))
    conn = init_db(db_path)
    conn.close()
    return db_path


def test_cache_status_missing_and_decision_full(temp_db):
    now = datetime(2026, 4, 14, 9, 30, tzinfo=timezone.utc)
    assert get_cache_status("FOOUSDT", "4h", now) == "missing"
    assert get_fetch_decision("FOOUSDT", "4h", now) == "fetch_full"
    assert bars_missing_since_cached("FOOUSDT", "4h", now) is None


def test_fetch_closed_bars_rejects_future_bar(monkeypatch, temp_db):
    from scanner.clients.mexc_client import MEXCClient

    def _fake_get_klines(self, symbol, interval="1d", limit=120, use_cache=True):
        return [
            [1713081600000, "1", "2", "0.5", "1.5", "100", 1713096000000, "150"],  # 2024-04-14 12:00 (future vs 08:00 cutoff)
            [1713067200000, "1", "2", "0.5", "1.5", "100", 1713081600000, "150"],  # 08:00 valid
        ]

    monkeypatch.setattr(MEXCClient, "get_klines", _fake_get_klines)
    result = fetch_closed_bars("foousdt", "4h", datetime(2024, 4, 14, 9, 30, tzinfo=timezone.utc), lookback_bars=120)

    assert len(result.bars) == 1
    assert result.partial_bars_dropped == 1
    assert result.bars[0].close_time_utc_ms == 1713081600000


def test_fetch_and_persist_skip_does_not_call_client(monkeypatch, temp_db):
    from scanner.clients.mexc_client import MEXCClient

    calls = {"n": 0}

    def _fake_get_klines(self, symbol, interval="1d", limit=120, use_cache=True):
        calls["n"] += 1
        return [[1713052800000, "1", "2", "0.5", "1.5", "100", 1713067200000, "150"]]

    monkeypatch.setattr(MEXCClient, "get_klines", _fake_get_klines)
    now = datetime(2024, 4, 14, 4, 0, tzinfo=timezone.utc)
    first = fetch_and_persist("FOOUSDT", "4h", now, lookback_bars=120)
    second = fetch_and_persist("FOOUSDT", "4h", now, lookback_bars=120)

    assert first.rows_inserted == 1
    assert second.rows_inserted == 0
    assert calls["n"] == 1


def test_fetch_input_contract_errors(temp_db):
    with pytest.raises(ValueError):
        fetch_closed_bars("   ", "1d", datetime.now(tz=timezone.utc))
    with pytest.raises(ValueError):
        fetch_closed_bars("BTCUSDT", "1h", datetime.now(tz=timezone.utc))
    with pytest.raises(TypeError):
        fetch_closed_bars("BTCUSDT", "1d", None)
