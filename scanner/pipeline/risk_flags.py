from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import yaml


@dataclass
class RiskFlagDecision:
    hard_exclude: bool
    hard_reasons: List[str]
    soft_flags: List[str]


class RiskFlagEngine:
    """Applies manual denylist/unlock overrides to symbols."""

    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        rf_cfg = root.get("risk_flags", {})
        self.minor_unlock_penalty_factor = float(rf_cfg.get("minor_unlock_penalty_factor", 0.9))

        denylist_path = Path(rf_cfg.get("denylist_file", "config/denylist.yaml"))
        unlock_path = Path(rf_cfg.get("unlock_overrides_file", "config/unlock_overrides.yaml"))

        self.denylist_symbols = self._load_symbol_set(denylist_path, key="symbols")
        self.major_unlock_symbols = self._load_symbol_set(unlock_path, key="major")
        self.minor_unlock_symbols = self._load_symbol_set(unlock_path, key="minor")

    @staticmethod
    def _canonical_symbols(values: Iterable[Any]) -> Set[str]:
        canonical: Set[str] = set()
        for value in values:
            if value is None:
                continue
            token = str(value).strip().upper()
            if not token:
                continue
            canonical.add(token)
            if token.endswith("USDT"):
                canonical.add(token[:-4])
            else:
                canonical.add(f"{token}USDT")
        return canonical

    def _load_symbol_set(self, path: Path, key: str) -> Set[str]:
        if not path.exists():
            return set()

        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        values = payload.get(key, [])
        if isinstance(values, dict):
            values = values.keys()
        if not isinstance(values, list) and not isinstance(values, set) and not isinstance(values, tuple):
            values = [values]

        return self._canonical_symbols(values)

    def evaluate_symbol(self, symbol: str, base: str | None = None) -> RiskFlagDecision:
        candidates = self._canonical_symbols([symbol, base])
        hard_reasons: List[str] = []
        soft_flags: List[str] = []

        if candidates & self.denylist_symbols:
            hard_reasons.append("denylist")
        if candidates & self.major_unlock_symbols:
            hard_reasons.append("major_unlock_within_14d")
        if candidates & self.minor_unlock_symbols:
            soft_flags.append("minor_unlock_within_14d")

        return RiskFlagDecision(
            hard_exclude=bool(hard_reasons),
            hard_reasons=hard_reasons,
            soft_flags=soft_flags,
        )

    def apply_to_universe(self, symbols_with_data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        filtered: List[Dict[str, Any]] = []
        symbol_risk: Dict[str, Dict[str, Any]] = {}

        for entry in symbols_with_data:
            symbol = str(entry.get("symbol", ""))
            decision = self.evaluate_symbol(symbol=symbol, base=entry.get("base"))

            if decision.hard_exclude:
                continue

            enriched = dict(entry)
            enriched["risk_flags"] = list(decision.soft_flags)
            symbol_risk[symbol] = {
                "risk_flags": list(decision.soft_flags),
                "hard_exclude_reasons": list(decision.hard_reasons),
            }
            filtered.append(enriched)

        return filtered, symbol_risk
