from __future__ import annotations

import math

from scanner.config import ScannerConfig
from scanner.state.models import InvalidationCycleBundle, PersistedStateMachineContext, StateFreshnessBundle, StateRuntimeContext


def _interp(points: list[list[float]], x: float) -> float:
    if x <= points[0][0]:
        return float(points[0][1])
    for idx in range(1, len(points)):
        x0, y0 = points[idx - 1]
        x1, y1 = points[idx]
        if x <= x1:
            if x1 == x0:
                return float(y1)
            ratio = (x - x0) / (x1 - x0)
            return float(y0 + (y1 - y0) * ratio)
    return float(points[-1][1])


def _distance_pct(current_close: float, ref: float) -> float:
    return abs((float(current_close) - float(ref)) / float(ref)) * 100.0


def _score(current_close: float, bars_since: int | None, ref_close: float | None, cfg: dict) -> tuple[float | None, float | None]:
    if bars_since is None or ref_close is None:
        return None, None
    distance = _distance_pct(current_close, ref_close)
    bars_score = _interp(cfg["bars_points"], float(bars_since))
    distance_score = _interp(cfg["distance_points"], float(distance))
    return float(max(bars_score, distance_score)), float(distance)


def compute_state_freshness(
    invalidation_cycle_bundle: InvalidationCycleBundle,
    persisted_context: PersistedStateMachineContext,
    runtime_context: StateRuntimeContext,
    cfg: ScannerConfig,
) -> StateFreshnessBundle:
    if not isinstance(invalidation_cycle_bundle, InvalidationCycleBundle):
        raise TypeError("invalidation_cycle_bundle must be InvalidationCycleBundle")
    if not isinstance(persisted_context, PersistedStateMachineContext):
        raise TypeError("persisted_context must be PersistedStateMachineContext")
    if not isinstance(runtime_context, StateRuntimeContext):
        raise TypeError("runtime_context must be StateRuntimeContext")
    if not isinstance(cfg, ScannerConfig):
        raise TypeError("cfg must be ScannerConfig")

    if persisted_context.symbol != invalidation_cycle_bundle.symbol:
        raise ValueError("bundle mismatch for symbol")

    settings = cfg.state["freshness"]
    early_score, early_distance = _score(
        runtime_context.current_close,
        persisted_context.bars_since_early_entered,
        persisted_context.close_at_early_entry_bar,
        settings,
    )
    confirmed_score, confirmed_distance = _score(
        runtime_context.current_close,
        persisted_context.bars_since_confirmed_entered,
        persisted_context.close_at_confirmed_entry_bar,
        settings,
    )

    for value in [early_score, confirmed_score, early_distance, confirmed_distance]:
        if value is not None and (not math.isfinite(float(value))):
            raise ValueError("freshness computation produced non-finite value")

    return StateFreshnessBundle(
        freshness_distance_state_early=early_score,
        freshness_distance_state_confirmed=confirmed_score,
        distance_from_ideal_entry_after_early=early_distance,
        distance_from_ideal_entry_after_confirmed=confirmed_distance,
    )
