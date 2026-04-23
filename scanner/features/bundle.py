from __future__ import annotations

from typing import Any

from scanner.features.models import FeatureBundle
from scanner.features.raw_1d import compute_raw_1d
from scanner.features.raw_4h import compute_raw_4h
from scanner.features.shared import compute_raw_shared


def _extract_ctx_int(ctx: Any, field: str) -> int | None:
    if isinstance(ctx, dict):
        v = ctx.get(field)
    else:
        v = getattr(ctx, field, None)
    if v is None:
        return None
    return int(v)


def _extract_ctx_daily_bar_id(ctx: Any) -> str | None:
    if isinstance(ctx, dict):
        v = ctx.get("daily_bar_id")
    else:
        v = getattr(ctx, "daily_bar_id", None)
    if v is None:
        return None
    return str(v)


def build_feature_bundle(
    symbol: str,
    bar_clock_context: Any,
    ohlcv_1d: list[Any],
    ohlcv_4h: list[Any] | None,
    cfg: Any,
) -> FeatureBundle:
    raw_1d = compute_raw_1d(symbol, bar_clock_context, ohlcv_1d, cfg)
    raw_4h = compute_raw_4h(symbol, bar_clock_context, ohlcv_4h, cfg)
    raw_shared = compute_raw_shared(symbol, bar_clock_context, raw_1d, raw_4h, cfg)

    daily_bar_id = _extract_ctx_daily_bar_id(bar_clock_context)
    intraday_bar_id = _extract_ctx_int(bar_clock_context, "intraday_bar_id")
    daily_close = _extract_ctx_int(bar_clock_context, "daily_close_time_utc_ms")
    intraday_close = _extract_ctx_int(bar_clock_context, "intraday_close_time_utc_ms")

    if daily_bar_id is None and daily_close is not None:
        daily_bar_id = str(daily_close)
    if daily_close is None and daily_bar_id is not None:
        daily_close = daily_bar_id

    if daily_bar_id is None or daily_close is None:
        raise ValueError("bar_clock_context must include daily_bar_id/daily_close_time_utc_ms")

    if raw_4h is None:
        intraday_bar_id = None
        intraday_close = None

    return FeatureBundle(
        symbol=symbol,
        daily_bar_id=str(daily_bar_id),
        intraday_bar_id=intraday_bar_id,
        daily_close_time_utc_ms=daily_close,
        intraday_close_time_utc_ms=intraday_close,
        data_4h_available=raw_4h is not None,
        raw_1d=raw_1d,
        raw_4h=raw_4h,
        raw_shared=raw_shared,
    )
