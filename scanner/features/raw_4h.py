from __future__ import annotations

import math
from statistics import median
from typing import Any

from scanner.features.models import RawFeatures4H
from scanner.features.raw_1d import _atr_wilder, _ema_sma_bootstrap, _rolling_rank


def _validate_symbol(symbol: str) -> None:
    if not isinstance(symbol, str):
        raise TypeError("symbol must be str")
    s = symbol.strip()
    if not s or s != s.upper():
        raise ValueError("symbol must be non-empty uppercase string")


def _bars_to_series(ohlcv_4h: list[Any] | None) -> tuple[list[int], list[float], list[float], list[float], list[float], list[float]] | None:
    if ohlcv_4h is None:
        return None
    if not isinstance(ohlcv_4h, list):
        raise TypeError("ohlcv_4h must be list or None")
    if len(ohlcv_4h) == 0:
        raise ValueError("ohlcv_4h must be None or non-empty")

    close_times: list[int] = []
    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    base_vols: list[float] = []
    quote_vols: list[float] = []
    prev: int | None = None

    for bar in ohlcv_4h:
        ct = int(getattr(bar, "close_time_utc_ms"))
        if prev is not None and ct <= prev:
            raise ValueError("ohlcv_4h must be strictly ascending and duplicate-free by close_time_utc_ms")
        prev = ct
        close_times.append(ct)
        closes.append(float(getattr(bar, "close")))
        highs.append(float(getattr(bar, "high")))
        lows.append(float(getattr(bar, "low")))
        base_vols.append(float(getattr(bar, "base_volume")))
        quote_vols.append(float(getattr(bar, "quote_volume")))
    return close_times, closes, highs, lows, base_vols, quote_vols


def _default_raw_4h(status: str = "insufficient_history") -> RawFeatures4H:
    vals = [status if k.endswith("_status") else None for k in RawFeatures4H.__dataclass_fields__.keys()]
    return RawFeatures4H(*vals)


def compute_raw_4h(symbol: str, bar_clock_context: Any, ohlcv_4h: list[Any] | None, cfg: Any) -> RawFeatures4H | None:
    _validate_symbol(symbol)
    if bar_clock_context is None:
        raise TypeError("bar_clock_context must not be None")
    series = _bars_to_series(ohlcv_4h)
    if series is None:
        return None

    _, closes, highs, lows, base_vols, quote_vols = series
    ema20 = _ema_sma_bootstrap(closes, 20)
    ema50 = _ema_sma_bootstrap(closes, 50)
    atr = _atr_wilder(highs, lows, closes, 14)

    def pct(a: float, b: float) -> float | None:
        if not math.isfinite(a) or not math.isfinite(b) or b == 0:
            return None
        return ((a / b) - 1.0) * 100.0

    def apct(a: float, b: float) -> float | None:
        p = pct(a, b)
        return abs(p) if p is not None else None

    def ratio(a: float, b: float) -> float | None:
        if not math.isfinite(a) or not math.isfinite(b) or b == 0:
            return None
        return a / b

    enough20 = len(closes) >= 40 and math.isfinite(ema20[-1]) and math.isfinite(ema20[-2])
    enough50 = len(closes) >= 100 and math.isfinite(ema50[-1]) and math.isfinite(ema50[-2])
    e20 = ema20[-1] if enough20 else float("nan")
    e50 = ema50[-1] if enough50 else float("nan")

    c = closes[-1]
    close_vs_ema20 = pct(c, e20)
    close_vs_ema50 = pct(c, e50)
    ema20_vs_ema50 = pct(e20, e50)
    ema20_slope = pct(e20, ema20[-2]) if enough20 else None

    vol_med10 = median(base_vols[-10:]) if len(base_vols) >= 10 else None
    vol_vs_med10 = ratio(base_vols[-1], vol_med10) if vol_med10 is not None else None
    quote_ref = (sum(quote_vols[-11:-1]) / 10.0) if len(quote_vols) >= 11 else None
    quote_spike = ratio(quote_vols[-1], quote_ref) if quote_ref is not None else None

    persistence_thresh = float(getattr(cfg, "feature_layer_config", {}).get("persistence_spike_threshold", 1.2))
    persistence = None
    persistence_status = "insufficient_history"
    # Canonical full lookback requirement:
    # N=4 checks, each check needs its own full 10-bar baseline excluding current => minimum 14 bars.
    if len(quote_vols) >= 14:
        spikes = 0
        invalid_upstream = False
        for i in range(4):
            cur_val = quote_vols[-(1 + i)]
            ref_window = quote_vols[-(11 + i) : -(1 + i)]
            if len(ref_window) != 10:
                invalid_upstream = True
                break
            if any(not math.isfinite(v) for v in ref_window) or not math.isfinite(cur_val):
                invalid_upstream = True
                break
            ref = sum(ref_window) / 10.0
            if ref == 0:
                invalid_upstream = True
                break
            if (cur_val / ref) >= persistence_thresh:
                spikes += 1
        if invalid_upstream:
            persistence_status = "invalid_upstream_value"
        else:
            persistence = spikes / 4.0
            persistence_status = "ok"

    rw12 = cp12 = mid12 = None
    if len(closes) >= 12:
        rh = max(highs[-12:])
        rl = min(lows[-12:])
        rw12 = pct(rh, rl)
        if rh != rl:
            cp12 = (c - rl) / (rh - rl)
            mid12 = (c - ((rh + rl) / 2.0)) / (rh - rl)

    cvrh5 = pct(c, max(highs[-5:])) if len(closes) >= 5 else None
    atr_last = atr[-1] if len(atr) else float("nan")
    atr_pct = pct(atr_last, c) if math.isfinite(atr_last) else None

    atr_rank = bb_rank = std_rank = None
    bb_width = None
    if len(closes) >= 20:
        window = closes[-20:]
        m = sum(window) / 20.0
        s = math.sqrt(sum((x - m) ** 2 for x in window) / 20.0)
        bb_width = None if m == 0 else ((4.0 * s) / m) * 100.0

    if len(closes) >= 120:
        atr_hist = [((atr[i] / closes[i]) * 100.0) if (math.isfinite(atr[i]) and closes[i] != 0) else float("nan") for i in range(len(closes)-120, len(closes))]
        atr_rank = _rolling_rank(atr_hist)

        bb_hist = []
        for i in range(len(closes)-120, len(closes)):
            if i < 19:
                bb_hist.append(float("nan"))
                continue
            w = closes[i-19:i+1]
            mu = sum(w) / 20.0
            if mu == 0:
                bb_hist.append(float("nan"))
                continue
            sig = math.sqrt(sum((x-mu)**2 for x in w) / 20.0)
            bb_hist.append(((4.0 * sig) / mu) * 100.0)
        bb_rank = _rolling_rank(bb_hist)

    if len(closes) >= 13:
        rets = [((closes[i] / closes[i - 1]) - 1.0) for i in range(1, len(closes))]
        std12 = []
        for i in range(11, len(rets)):
            w = rets[i-11:i+1]
            mu = sum(w)/12.0
            std12.append(math.sqrt(sum((x-mu)**2 for x in w) / 12.0))
        std_rank = _rolling_rank(std12[-120:])

    def streak_above(level: float | None) -> int | None:
        if level is None:
            return None
        s = 0
        for v in reversed(closes):
            if v > level:
                s += 1
            else:
                break
        return s

    bars20 = streak_above(e20 if math.isfinite(e20) else None)
    bars50 = streak_above(e50 if math.isfinite(e50) else None)

    bars_high20 = None
    if len(closes) >= 21:
        threshold = max(highs[-21:-1])
        count = 0
        for v in reversed(closes):
            if v > threshold:
                count += 1
            else:
                break
        bars_high20 = count

    lo = min(lows)
    last_low_idx = max(i for i, x in enumerate(lows) if x == lo)
    since_low = len(lows) - 1 - last_low_idx

    min_below = int(getattr(cfg, "feature_layer_config", {}).get("structural_break", {}).get("min_bars_below_before_break", 3))
    anchor = high20_anchor = break_close = None
    bars_since_break = None
    if len(closes) >= 21:
        for i in range(20, len(closes)):
            prev_high20 = max(highs[i-20:i])
            below_before = sum(1 for x in closes[max(0, i-min_below):i] if x <= prev_high20)
            if closes[i] > prev_high20 and below_before >= min_below:
                anchor = prev_high20
                high20_anchor = prev_high20
                break_close = closes[i]
                bars_since_break = len(closes) - 1 - i
        
    move_from_break = pct(c, break_close) if break_close is not None else None
    dist_anchor_abs = apct(c, anchor) if anchor is not None else None
    dist_ema20_abs = apct(c, e20) if math.isfinite(e20) else None

    seg_window = int(getattr(cfg, "feature_layer_config", {}).get("segmentation_window_4h", 20))
    if len(closes) >= seg_window:
        segc = closes[-seg_window:]
        segl = lows[-seg_window:]
        segv = base_vols[-seg_window:]
        imp_start = min(segc)
        imp_high = max(segc)
        pb_low = min(segl)
        cur_pb = segc[-1]
        pb_depth = pct((imp_high - cur_pb), (imp_high - imp_start)) if imp_high != imp_start else None
        pb_vol = ratio(segv[-1], (sum(segv[:-1]) / (len(segv)-1))) if len(segv) > 1 else None
        low_vs_ema = pct(pb_low, e20)
    else:
        imp_start = imp_high = pb_low = cur_pb = pb_depth = pb_vol = low_vs_ema = None

    def st(v: Any) -> str:
        return "ok" if v is not None else "insufficient_history"

    invalid_flat12 = len(closes) >= 12 and max(highs[-12:]) == min(lows[-12:])
    return RawFeatures4H(
        close_vs_ema20, st(close_vs_ema20), close_vs_ema50, st(close_vs_ema50),
        ema20_vs_ema50, st(ema20_vs_ema50), ema20_slope, st(ema20_slope),
        vol_vs_med10, st(vol_vs_med10), quote_spike, st(quote_spike),
        persistence, persistence_status, rw12, st(rw12),
        cp12, "invalid_upstream_value" if invalid_flat12 and cp12 is None else st(cp12),
        mid12, "invalid_upstream_value" if invalid_flat12 and mid12 is None else st(mid12),
        cvrh5, st(cvrh5), atr_pct, st(atr_pct), atr_rank, st(atr_rank),
        bb_width, st(bb_width), bb_rank, st(bb_rank), std_rank, st(std_rank),
        bars20, st(bars20), bars50, st(bars50), bars_high20, st(bars_high20),
        since_low, st(since_low), anchor, st(anchor), high20_anchor, st(high20_anchor),
        break_close, st(break_close), move_from_break, st(move_from_break),
        bars_since_break, st(bars_since_break), dist_anchor_abs, st(dist_anchor_abs),
        dist_ema20_abs, st(dist_ema20_abs), pb_depth, st(pb_depth), pb_vol, st(pb_vol),
        low_vs_ema, st(low_vs_ema), imp_start, st(imp_start), imp_high, st(imp_high),
        pb_low, st(pb_low), cur_pb, st(cur_pb),
    )
