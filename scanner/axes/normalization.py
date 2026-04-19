from __future__ import annotations

import math
from typing import Optional


def _is_finite_number(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def norm_linear_clamped(x: float, low: float, mid: float, high: float) -> Optional[float]:
    if mid == low:
        raise ValueError("mid == low")
    if high == mid:
        raise ValueError("high == mid")
    if low >= high:
        raise ValueError("low must be < high")
    if not _is_finite_number(x):
        return None

    xf = float(x)
    if xf <= low:
        return 0.0
    if xf >= high:
        return 100.0
    if xf <= mid:
        return ((xf - low) / (mid - low)) * 50.0
    return 50.0 + ((xf - mid) / (high - mid)) * 50.0


def norm_linear_clamped_inv(x: float, low_good: float, mid: float, high_bad: float) -> Optional[float]:
    if mid == low_good:
        raise ValueError("mid == low_good")
    if high_bad == mid:
        raise ValueError("high_bad == mid")
    if low_good >= high_bad:
        raise ValueError("low_good must be < high_bad")
    if not _is_finite_number(x):
        return None

    xf = float(x)
    if xf <= low_good:
        return 100.0
    if xf >= high_bad:
        return 0.0
    if xf <= mid:
        return 100.0 - ((xf - low_good) / (mid - low_good)) * 50.0
    return 50.0 - ((xf - mid) / (high_bad - mid)) * 50.0


def norm_piecewise_linear(x: float, points: list[tuple[float, float]]) -> Optional[float]:
    if len(points) < 2:
        raise ValueError("at least two points required")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    for idx in range(len(xs) - 1):
        if not xs[idx] < xs[idx + 1]:
            raise ValueError("x values must be strictly ascending")
    for y in ys:
        if y < 0 or y > 100:
            raise ValueError("y values must be in [0, 100]")

    if not _is_finite_number(x):
        return None

    xf = float(x)
    if xf <= xs[0]:
        return float(ys[0])
    if xf >= xs[-1]:
        return float(ys[-1])

    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= xf <= x1:
            if xf == x0:
                return float(y0)
            if xf == x1:
                return float(y1)
            ratio = (xf - x0) / (x1 - x0)
            return float(y0 + ratio * (y1 - y0))

    raise RuntimeError("unreachable")


def weighted_mean(scores_and_weights: list[tuple[Optional[float], float]]) -> Optional[float]:
    if not scores_and_weights:
        return None

    retained: list[tuple[float, float]] = []
    for score, weight in scores_and_weights:
        if not _is_finite_number(weight) or float(weight) <= 0:
            raise ValueError("weights must be finite and > 0")
        if score is None:
            continue
        sf = float(score)
        if sf < 0 or sf > 100:
            raise ValueError("scores must be in [0, 100]")
        retained.append((sf, float(weight)))

    if not retained:
        return None

    total_weight = sum(weight for _, weight in retained)
    if total_weight == 0:
        return None

    return sum(score * (weight / total_weight) for score, weight in retained)
