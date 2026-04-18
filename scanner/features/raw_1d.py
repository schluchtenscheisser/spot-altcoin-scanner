from __future__ import annotations

import math
from statistics import median
from typing import Any, Iterable

from scanner.features.models import RawFeatures1D


_VALID_STATUSES = {
    "ok",
    "insufficient_history",
    "gap_in_required_window",
    "upstream_dependency_null",
    "invalid_upstream_value",
}
_ONE_DAY_MS = 86_400_000


def _validate_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise TypeError("symbol must be str")
    normalized = symbol.strip()
    if not normalized or normalized != normalized.upper():
        raise ValueError("symbol must be non-empty uppercase string")
    return normalized


def _validate_context(ctx: Any) -> None:
    if ctx is None:
        raise TypeError("bar_clock_context must not be None")


def _bars_to_series(ohlcv_1d: list[Any]) -> tuple[list[int], list[float], list[float], list[float], list[float], list[float]]:
    if not isinstance(ohlcv_1d, list):
        raise TypeError("ohlcv_1d must be list")
    if len(ohlcv_1d) == 0:
        raise ValueError("ohlcv_1d must be non-empty")

    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    base_vols: list[float] = []
    quote_vols: list[float] = []
    close_times: list[int] = []

    prev_ct: int | None = None
    for bar in ohlcv_1d:
        for attr in ["close_time_utc_ms", "close", "high", "low", "base_volume", "quote_volume"]:
            if not hasattr(bar, attr):
                raise TypeError(f"ohlcv_1d bar missing {attr}")
        ct = int(getattr(bar, "close_time_utc_ms"))
        close = float(getattr(bar, "close"))
        high = float(getattr(bar, "high"))
        low = float(getattr(bar, "low"))
        bv = float(getattr(bar, "base_volume"))
        qv = float(getattr(bar, "quote_volume"))
        vals = [close, high, low, bv, qv]
        if any(not math.isfinite(v) for v in vals):
            closes.append(float("nan"))
        else:
            closes.append(close)
        highs.append(high)
        lows.append(low)
        base_vols.append(bv)
        quote_vols.append(qv)
        if prev_ct is not None and ct <= prev_ct:
            raise ValueError("ohlcv_1d must be strictly ascending and duplicate-free by close_time_utc_ms")
        prev_ct = ct
        close_times.append(ct)
    return close_times, closes, highs, lows, base_vols, quote_vols


def _has_gap_in_last_window(close_times: list[int], window: int) -> bool:
    if window <= 1 or len(close_times) < window:
        return False
    segment = close_times[-window:]
    for i in range(1, len(segment)):
        if segment[i] - segment[i - 1] != _ONE_DAY_MS:
            return True
    return False


def _ema_sma_bootstrap(values: list[float], period: int) -> list[float]:
    out = [float("nan")] * len(values)
    if len(values) < period:
        return out
    alpha = 2.0 / (period + 1.0)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = ((values[i] - prev) * alpha) + prev
        out[i] = prev
    return out


def _rolling_rank(values: Iterable[float]) -> float | None:
    seq = [v for v in values if math.isfinite(v)]
    if len(seq) < 2:
        return None
    cur = seq[-1]
    less = sum(1 for v in seq if v < cur)
    eq = sum(1 for v in seq if v == cur)
    return ((less + (0.5 * eq)) / len(seq)) * 100.0


def _atr_wilder(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[float]:
    tr: list[float] = []
    for i in range(len(closes)):
        if i == 0:
            tr.append(highs[i] - lows[i])
            continue
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    out = [float("nan")] * len(closes)
    if len(tr) < period:
        return out
    first = sum(tr[:period]) / period
    out[period - 1] = first
    prev = first
    for i in range(period, len(tr)):
        prev = ((prev * (period - 1)) + tr[i]) / period
        out[i] = prev
    return out


def _default_raw_1d(status: str = "insufficient_history") -> RawFeatures1D:
    assert status in _VALID_STATUSES
    vals: list[Any] = []
    for field in RawFeatures1D.__dataclass_fields__.keys():
        vals.append(status if field.endswith("_status") else None)
    return RawFeatures1D(*vals)


def compute_raw_1d(symbol: str, bar_clock_context: Any, ohlcv_1d: list[Any], cfg: Any) -> RawFeatures1D:
    _validate_symbol(symbol)
    _validate_context(bar_clock_context)
    close_times, closes, highs, lows, base_vols, quote_vols = _bars_to_series(ohlcv_1d)

    if any(not math.isfinite(v) for v in [closes[-1], highs[-1], lows[-1], base_vols[-1], quote_vols[-1]]):
        return _default_raw_1d("invalid_upstream_value")

    ema20 = _ema_sma_bootstrap(closes, 20)
    ema50 = _ema_sma_bootstrap(closes, 50)
    atr_series = _atr_wilder(highs, lows, closes, 14)

    def pct(a: float, b: float) -> float | None:
        if not math.isfinite(a) or not math.isfinite(b) or b == 0:
            return None
        return ((a / b) - 1.0) * 100.0

    def ratio(a: float, b: float) -> float | None:
        if not math.isfinite(a) or not math.isfinite(b) or b == 0:
            return None
        return a / b

    enough_ema20 = len(closes) >= 40 and math.isfinite(ema20[-1]) and math.isfinite(ema20[-2])
    enough_ema50 = len(closes) >= 100 and math.isfinite(ema50[-1]) and math.isfinite(ema50[-2])

    c = closes[-1]
    e20 = ema20[-1] if enough_ema20 else float("nan")
    e50 = ema50[-1] if enough_ema50 else float("nan")

    gap_ema20 = _has_gap_in_last_window(close_times, 40)
    gap_ema50 = _has_gap_in_last_window(close_times, 100)
    close_vs_ema20 = None if gap_ema20 else pct(c, e20)
    close_vs_ema50 = None if gap_ema50 else pct(c, e50)
    ema20_vs_ema50 = None if (gap_ema20 or gap_ema50) else pct(e20, e50)
    ema20_slope = None if gap_ema20 else (pct(e20, ema20[-2]) if enough_ema20 else None)

    gap10 = _has_gap_in_last_window(close_times, 10)
    med10 = median(base_vols[-10:]) if len(base_vols) >= 10 and not gap10 else None
    vol_vs_med10 = ratio(base_vols[-1], med10) if med10 is not None else None
    gap11 = _has_gap_in_last_window(close_times, 11)
    q_ref = (sum(quote_vols[-11:-1]) / 10.0) if len(quote_vols) >= 11 and not gap11 else None
    q_spike = ratio(quote_vols[-1], q_ref) if q_ref is not None else None

    rw10 = None
    cp10 = None
    mid10 = None
    crh5 = None
    if len(closes) >= 10 and not gap10:
        r_high = max(highs[-10:])
        r_low = min(lows[-10:])
        rw10 = pct(r_high, r_low)
        if r_high == r_low:
            cp10 = None
            mid10 = None
        else:
            cp10 = (c - r_low) / (r_high - r_low)
            mid = (r_high + r_low) / 2.0
            mid10 = (c - mid) / (r_high - r_low)
    gap5 = _has_gap_in_last_window(close_times, 5)
    if len(closes) >= 5 and not gap5:
        crh5 = pct(c, max(highs[-5:]))

    gap14 = _has_gap_in_last_window(close_times, 14)
    atr = atr_series[-1] if len(atr_series) and math.isfinite(atr_series[-1]) and not gap14 else None
    atr_pct = pct(atr or float("nan"), c) if atr is not None else None

    atr_pct_rank = None
    gap120 = _has_gap_in_last_window(close_times, 120)
    if len(closes) >= 120 and not gap120:
        atr_pct_hist = []
        for i in range(len(closes) - 120, len(closes)):
            a = atr_series[i]
            cl = closes[i]
            atr_pct_hist.append(((a / cl) * 100.0) if (math.isfinite(a) and math.isfinite(cl) and cl != 0) else float("nan"))
        atr_pct_rank = _rolling_rank(atr_pct_hist)

    bb_width = None
    bb_rank = None
    gap20 = _has_gap_in_last_window(close_times, 20)
    if len(closes) >= 20 and not gap20:
        window = closes[-20:]
        mu = sum(window) / 20.0
        var = sum((x - mu) ** 2 for x in window) / 20.0
        sigma = math.sqrt(var)
        bb_width = None if mu == 0 else ((4.0 * sigma) / mu) * 100.0
        if len(closes) >= 120 and not gap120:
            hist: list[float] = []
            for i in range(len(closes) - 120, len(closes)):
                if i < 19:
                    hist.append(float("nan"))
                    continue
                w = closes[i - 19 : i + 1]
                m = sum(w) / 20.0
                if m == 0:
                    hist.append(float("nan"))
                    continue
                s = math.sqrt(sum((x - m) ** 2 for x in w) / 20.0)
                hist.append(((4.0 * s) / m) * 100.0)
            bb_rank = _rolling_rank(hist)

    def streak_above(series: list[float], level: float | None) -> int | None:
        if level is None:
            return None
        s = 0
        for v in reversed(series):
            if v > level:
                s += 1
            else:
                break
        return s

    bars_above20 = None if gap_ema20 else streak_above(closes, e20 if math.isfinite(e20) else None)
    bars_above50 = None if gap_ema50 else streak_above(closes, e50 if math.isfinite(e50) else None)

    bars_since_low = None
    if len(lows) >= 2 and not _has_gap_in_last_window(close_times, len(lows)):
        lo = min(lows)
        last_idx = max(i for i, x in enumerate(lows) if x == lo)
        bars_since_low = len(lows) - 1 - last_idx

    seg_window = int(getattr(cfg, "feature_layer_config", {}).get("segmentation_window_1d", 15))
    gap_seg = _has_gap_in_last_window(close_times, seg_window)
    if len(closes) >= seg_window and not gap_seg:
        seg_closes = closes[-seg_window:]
        seg_lows = lows[-seg_window:]
        seg_vols = base_vols[-seg_window:]
        imp_start = min(seg_closes)
        imp_high = max(seg_closes)
        pb_low = min(seg_lows)
        cur_pb = seg_closes[-1]
        pullback_depth = pct((imp_high - cur_pb), (imp_high - imp_start)) if imp_high != imp_start else None
        pb_vol_ratio = ratio(seg_vols[-1], (sum(seg_vols[:-1]) / (len(seg_vols) - 1))) if len(seg_vols) > 1 else None
        low_vs_ema = pct(pb_low, e20)
    else:
        imp_start = imp_high = pb_low = cur_pb = pullback_depth = pb_vol_ratio = low_vs_ema = None

    def st(v: Any, has_gap: bool = False) -> str:
        if v is not None:
            return "ok"
        if has_gap:
            return "gap_in_required_window"
        return "insufficient_history"

    return RawFeatures1D(
        close_vs_ema20, st(close_vs_ema20, gap_ema20),
        close_vs_ema50, st(close_vs_ema50, gap_ema50),
        ema20_vs_ema50, st(ema20_vs_ema50, gap_ema20 or gap_ema50),
        ema20_slope, st(ema20_slope, gap_ema20),
        vol_vs_med10, st(vol_vs_med10, gap10),
        q_spike, st(q_spike, gap11),
        rw10, st(rw10, gap10),
        cp10, "invalid_upstream_value" if len(closes) >= 10 and (not gap10) and cp10 is None and max(highs[-10:]) == min(lows[-10:]) else st(cp10, gap10),
        mid10, "invalid_upstream_value" if len(closes) >= 10 and (not gap10) and mid10 is None and max(highs[-10:]) == min(lows[-10:]) else st(mid10, gap10),
        crh5, st(crh5, gap5),
        atr_pct, st(atr_pct, gap14),
        atr_pct_rank, st(atr_pct_rank, gap120),
        bb_width, st(bb_width, gap20),
        bb_rank, st(bb_rank, gap120),
        bars_above20, st(bars_above20, gap_ema20),
        bars_above50, st(bars_above50, gap_ema50),
        bars_since_low, st(bars_since_low, _has_gap_in_last_window(close_times, len(lows))),
        pullback_depth, st(pullback_depth, gap_seg),
        pb_vol_ratio, st(pb_vol_ratio, gap_seg),
        low_vs_ema, st(low_vs_ema, gap_seg),
        imp_start, st(imp_start, gap_seg),
        imp_high, st(imp_high, gap_seg),
        pb_low, st(pb_low, gap_seg),
        cur_pb, st(cur_pb, gap_seg),
        atr, st(atr, gap14),
    )
