from __future__ import annotations

from datetime import datetime, timezone

import pytest

from scanner.data.cache_policy import bars_missing_since_cached, get_cache_status, get_fetch_decision
from scanner.data.ohlcv_fetch import fetch_and_persist, fetch_closed_bars
from scanner.storage import init_db
from scanner.clients.mexc_client import MEXCClient


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


def test_full_fetch_uses_exact_lookback_count_for_4h(monkeypatch, temp_db):
    from scanner.clients.mexc_client import MEXCClient

    duration = 4 * 60 * 60 * 1000
    cutoff = 1713081600000  # 2024-04-14T08:00:00Z

    lookback = 120

    def _fake_get_klines(self, symbol, interval="1d", limit=120, use_cache=True):
        rows = []
        for i in range(lookback + 1):  # includes one extra older bar
            close_time = cutoff - ((lookback - i) * duration)
            open_time = close_time - duration
            rows.append([open_time, "1", "2", "0.5", "1.5", "100", close_time, "150"])
        return rows

    monkeypatch.setattr(MEXCClient, "get_klines", _fake_get_klines)
    result = fetch_closed_bars("FOOUSDT", "4h", datetime(2024, 4, 14, 9, 30, tzinfo=timezone.utc), lookback_bars=lookback)
    assert len(result.bars) == lookback
    assert result.bars[0].close_time_utc_ms == cutoff - ((lookback - 1) * duration)
    assert result.bars[-1].close_time_utc_ms == cutoff


def test_full_fetch_uses_exact_lookback_count_for_1d(monkeypatch, temp_db):
    from scanner.clients.mexc_client import MEXCClient

    duration = 24 * 60 * 60 * 1000
    cutoff = 1713052800000  # 2024-04-14T00:00:00Z

    lookback = 120

    def _fake_get_klines(self, symbol, interval="1d", limit=120, use_cache=True):
        rows = []
        for i in range(lookback + 1):  # includes one extra older bar
            close_time = cutoff - ((lookback - i) * duration)
            open_time = close_time - duration
            rows.append([open_time, "1", "2", "0.5", "1.5", "100", close_time, "150"])
        return rows

    monkeypatch.setattr(MEXCClient, "get_klines", _fake_get_klines)
    result = fetch_closed_bars("FOOUSDT", "1d", datetime(2024, 4, 14, 12, 0, tzinfo=timezone.utc), lookback_bars=lookback)
    assert len(result.bars) == lookback
    assert result.bars[0].close_time_utc_ms == cutoff - ((lookback - 1) * duration)
    assert result.bars[-1].close_time_utc_ms == cutoff


def test_incremental_persist_skips_overlap_and_older_bars(monkeypatch, temp_db):
    from scanner.clients.mexc_client import MEXCClient

    conn = init_db(temp_db)
    conn.execute(
        """
        INSERT INTO ohlcv_bars(symbol, timeframe, open_time_utc_ms, close_time_utc_ms, open, high, low, close, base_volume, quote_volume)
        VALUES ('FOOUSDT', '4h', ?, ?, 1, 2, 0.5, 1.5, 100, 150)
        """,
        (1713038400000, 1713052800000),  # 2024-04-14 00:00
    )
    conn.execute(
        """
        INSERT INTO ohlcv_cache_meta(symbol, timeframe, cached_close_time_utc_ms, last_fetch_at_utc, last_fetch_status, last_error_code)
        VALUES ('FOOUSDT', '4h', 1713052800000, '2024-04-14T00:00:00.000Z', 'ok', NULL)
        """
    )
    conn.commit()
    conn.close()

    def _fake_get_klines(self, symbol, interval="1d", limit=120, use_cache=True):
        # overlap (00:00) + new (04:00)
        return [
            [1713038400000, "1", "2", "0.5", "1.5", "100", 1713052800000, "150"],
            [1713052800000, "1", "2", "0.5", "1.6", "100", 1713067200000, "150"],
        ]

    monkeypatch.setattr(MEXCClient, "get_klines", _fake_get_klines)
    now = datetime(2024, 4, 14, 5, 0, tzinfo=timezone.utc)
    assert get_fetch_decision("FOOUSDT", "4h", now) == "fetch_incremental"
    result = fetch_and_persist("FOOUSDT", "4h", now, lookback_bars=120)

    assert result.rows_inserted == 1
    assert result.rows_noop_identical == 0

    conn = init_db(temp_db)
    bars = conn.execute(
        "SELECT close_time_utc_ms FROM ohlcv_bars WHERE symbol='FOOUSDT' AND timeframe='4h' ORDER BY close_time_utc_ms ASC"
    ).fetchall()
    conn.close()
    assert [row[0] for row in bars] == [1713052800000, 1713067200000]


def test_incremental_ignores_conflicting_overlap_bar(monkeypatch, temp_db):
    from scanner.clients.mexc_client import MEXCClient

    conn = init_db(temp_db)
    conn.execute(
        """
        INSERT INTO ohlcv_bars(symbol, timeframe, open_time_utc_ms, close_time_utc_ms, open, high, low, close, base_volume, quote_volume)
        VALUES ('FOOUSDT', '4h', ?, ?, 1, 2, 0.5, 1.5, 100, 150)
        """,
        (1713038400000, 1713052800000),
    )
    conn.execute(
        """
        INSERT INTO ohlcv_cache_meta(symbol, timeframe, cached_close_time_utc_ms, last_fetch_at_utc, last_fetch_status, last_error_code)
        VALUES ('FOOUSDT', '4h', 1713052800000, '2024-04-14T00:00:00.000Z', 'ok', NULL)
        """
    )
    conn.commit()
    conn.close()

    def _fake_get_klines(self, symbol, interval="1d", limit=120, use_cache=True):
        # older overlap row conflicts with existing history but must not be persisted in incremental mode
        return [
            [1713038400000, "9", "9", "9", "9", "9", 1713052800000, "9"],
            [1713052800000, "1", "2", "0.5", "1.6", "100", 1713067200000, "150"],
        ]

    monkeypatch.setattr(MEXCClient, "get_klines", _fake_get_klines)
    result = fetch_and_persist("FOOUSDT", "4h", datetime(2024, 4, 14, 5, 0, tzinfo=timezone.utc), lookback_bars=120)
    assert result.rows_inserted == 1


def test_persist_ok_noop_bars_advances_cached_close_from_null(monkeypatch, temp_db):
    from scanner.clients.mexc_client import MEXCClient

    conn = init_db(temp_db)
    conn.execute(
        """
        INSERT INTO ohlcv_bars(symbol, timeframe, open_time_utc_ms, close_time_utc_ms, open, high, low, close, base_volume, quote_volume)
        VALUES ('FOOUSDT', '4h', ?, ?, 1, 2, 0.5, 1.5, 100, 150)
        """,
        (1713052800000, 1713067200000),
    )
    conn.execute(
        """
        INSERT INTO ohlcv_cache_meta(symbol, timeframe, cached_close_time_utc_ms, last_fetch_at_utc, last_fetch_status, last_error_code)
        VALUES ('FOOUSDT', '4h', NULL, '2024-04-14T00:00:00.000Z', 'ok', NULL)
        """
    )
    conn.commit()
    conn.close()

    def _fake_get_klines(self, symbol, interval="1d", limit=120, use_cache=True):
        return [[1713052800000, "1", "2", "0.5", "1.5", "100", 1713067200000, "150"]]

    monkeypatch.setattr(MEXCClient, "get_klines", _fake_get_klines)
    now = datetime(2024, 4, 14, 4, 0, tzinfo=timezone.utc)
    result = fetch_and_persist("FOOUSDT", "4h", now, lookback_bars=120)

    assert result.rows_inserted == 0
    assert result.rows_noop_identical == 1
    assert result.cached_close_time_utc_ms == 1713067200000
    assert get_cache_status("FOOUSDT", "4h", now) == "fresh"


def test_mexc_client_max_retries_zero_still_makes_one_request(monkeypatch):
    calls = {"n": 0}

    class _Resp:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def _fake_request(self, **kwargs):
        _ = kwargs
        calls["n"] += 1
        return _Resp()

    monkeypatch.setattr("requests.Session.request", _fake_request)
    client = MEXCClient(max_retries=0, retry_backoff=0.0, timeout=1)
    payload = client._request("GET", "/api/v3/exchangeInfo")

    assert payload == {"ok": True}
    assert calls["n"] == 1


def test_mexc_client_max_retries_one_allows_single_retry(monkeypatch):
    calls = {"n": 0}

    class _Resp:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def _fake_request(self, **kwargs):
        _ = kwargs
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("transport down")
        return _Resp()

    def _wrapped_request(self, **kwargs):
        import requests

        try:
            return _fake_request(self, **kwargs)
        except Exception as exc:
            raise requests.RequestException(str(exc))

    monkeypatch.setattr("requests.Session.request", _wrapped_request)
    client = MEXCClient(max_retries=1, retry_backoff=0.0, timeout=1)
    payload = client._request("GET", "/api/v3/exchangeInfo")

    assert payload == {"ok": True}
    assert calls["n"] == 2


def test_fetch_closed_bars_with_default_zero_retries_is_not_transport_error_on_success(monkeypatch, temp_db):
    class _Resp:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return [[1712966400000, "1", "2", "0.5", "1.6", "100", 1713052800000, "150"]]

    monkeypatch.setattr("requests.Session.request", lambda self, **kwargs: _Resp())
    result = fetch_closed_bars("FOOUSDT", "1d", datetime(2024, 4, 14, 12, 0, tzinfo=timezone.utc), lookback_bars=120)
    assert result.last_fetch_status == "ok"
    assert result.last_error_code is None
    assert len(result.bars) == 1
