"""Cross-section helpers for deterministic percent-rank calculations."""

from __future__ import annotations

from typing import Dict, Iterable, List


def percent_rank_average_ties(values: Iterable[float]) -> List[float]:
    """Return percent-ranks in [0,100] with average-rank tie handling.

    Ranking is computed against the full provided population and is independent
    of input order.
    """
    value_list = [float(v) for v in values]
    n = len(value_list)
    if n == 0:
        return []
    if n == 1:
        return [100.0]

    sorted_values = sorted(value_list)
    positions_by_value: Dict[float, List[int]] = {}
    for idx, value in enumerate(sorted_values, start=1):
        positions_by_value.setdefault(value, []).append(idx)

    avg_rank_by_value = {
        value: (sum(positions) / len(positions))
        for value, positions in positions_by_value.items()
    }

    return [((avg_rank_by_value[value] - 1.0) / (n - 1.0)) * 100.0 for value in value_list]

