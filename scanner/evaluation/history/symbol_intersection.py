"""Universe resolution for Binance-history Pre-1 fetches."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .history_fetch_config import EXCLUSION_REASONS


@dataclass(frozen=True)
class ExcludedSymbol:
    source_symbol: str
    normalized_symbol: str | None
    reason: str
    detail: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "source_symbol": self.source_symbol,
            "normalized_symbol": self.normalized_symbol,
            "reason": self.reason,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class UniverseResolution:
    universe_mode: str
    source_mexc_symbol_count: int | None
    binance_usdt_symbol_count: int
    included_symbols: list[str]
    excluded_symbols: list[ExcludedSymbol]


def normalize_spot_usdt_symbol(symbol: str) -> str | None:
    raw = str(symbol).strip().upper()
    for sep in ("/", "_", "-"):
        raw = raw.replace(sep, "")
    if not raw or not raw.endswith("USDT"):
        return None
    base = raw[:-4]
    if not base or not base.replace("1000", "").isalnum():
        return None
    return f"{base}USDT"


def load_mexc_universe(path: str | Path) -> list[str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict):
        for key in ("symbols", "included_symbols", "universe", "mexc_symbols"):
            if isinstance(payload.get(key), list):
                return [str(item) for item in payload[key]]
    raise ValueError("mexc universe file must be a JSON list or an object with a symbols-like list")


def _sorted_exclusions(exclusions: Iterable[ExcludedSymbol]) -> list[ExcludedSymbol]:
    return sorted(exclusions, key=lambda item: (item.reason, item.source_symbol, item.normalized_symbol or ""))


def resolve_universe(
    *,
    universe_mode: str,
    binance_symbols: Iterable[str],
    mexc_symbols: Iterable[str] | None = None,
) -> UniverseResolution:
    binance_normalized = sorted({normalized for symbol in binance_symbols if (normalized := normalize_spot_usdt_symbol(symbol))})
    binance_set = set(binance_normalized)
    exclusions: list[ExcludedSymbol] = []

    if universe_mode == "binance_spot_usdt_all":
        return UniverseResolution(
            universe_mode=universe_mode,
            source_mexc_symbol_count=None,
            binance_usdt_symbol_count=len(binance_normalized),
            included_symbols=binance_normalized,
            excluded_symbols=[],
        )

    if universe_mode != "fixed_current_mexc_binance_intersection":
        raise ValueError(f"unsupported universe_mode: {universe_mode!r}")
    if mexc_symbols is None:
        raise ValueError("mexc_symbols or --mexc-universe-path is required for fixed_current_mexc_binance_intersection")

    source_symbols = [str(symbol) for symbol in mexc_symbols]
    normalized_by_source = {symbol: normalize_spot_usdt_symbol(symbol) for symbol in source_symbols}
    counts = Counter(value for value in normalized_by_source.values() if value is not None)
    included: set[str] = set()
    for source_symbol in source_symbols:
        normalized = normalized_by_source[source_symbol]
        if normalized is None or counts[normalized] > 1:
            exclusions.append(
                ExcludedSymbol(source_symbol, normalized, "normalization_mismatch", "symbol is missing, unsupported, or ambiguous after normalization")
            )
            continue
        if normalized not in binance_set:
            exclusions.append(ExcludedSymbol(source_symbol, normalized, "mexc_only", "normalized symbol is not a Binance Spot USDT symbol"))
            continue
        included.add(normalized)

    return UniverseResolution(
        universe_mode=universe_mode,
        source_mexc_symbol_count=len(source_symbols),
        binance_usdt_symbol_count=len(binance_normalized),
        included_symbols=sorted(included),
        excluded_symbols=_sorted_exclusions(exclusions),
    )


def empty_excluded_counts() -> dict[str, int]:
    return {reason: 0 for reason in EXCLUSION_REASONS}
