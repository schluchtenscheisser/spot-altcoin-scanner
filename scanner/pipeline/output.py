"""
Output & Report Generation
===========================

Generates human-readable (Markdown), machine-readable (JSON), and Excel reports
from scored results.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from scanner.schema import REPORT_META_VERSION, REPORT_SCHEMA_VERSION
from .manifest import (
    build_config_hash,
    derive_feature_flags,
    derive_pipeline_paths,
    read_canonical_schema_version,
    write_manifest_atomic,
)

logger = logging.getLogger(__name__)

_DECISION_PRIORITY = {"ENTER": 0, "WAIT": 1, "NO_TRADE": 2}
_ENTRY_AT_TRIGGER_TOLERANCE_PCT = 0.25
_ENTRY_CHASED_THRESHOLD_PCT = 3.0
_ENTRY_STATE_ORDER = ("early", "at_trigger", "late", "chased", "null")
_ENTRY_STATE_REASON_MAP = {
    "early": "entry_too_early",
    "late": "entry_late",
    "chased": "entry_chased",
}


class ReportGenerator:
    """Generates daily reports from scoring results."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            config: Config dict with 'output' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            self.root_config = config.raw
            output_config = config.raw.get('output', {})
        else:
            self.root_config = config
            output_config = config.get('output', {})
        
        self.reports_dir = Path(output_config.get('reports_dir', 'reports'))
        self.top_n = output_config.get('top_n_per_setup', 10)
        
        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Report Generator initialized: reports_dir={self.reports_dir}")

    def _build_run_manifest(
        self,
        run_date: str,
        metadata: Optional[Dict[str, Any]],
        trade_candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        asof_ts_ms = metadata.get("asof_ts_ms")
        asof_iso = metadata.get("asof_iso")
        run_id = str(metadata.get("run_id") or asof_ts_ms or run_date)

        default_stage_counts = {
            "trade_candidates": len(trade_candidates),
        }
        stage_counts = metadata.get("stage_counts")
        if not isinstance(stage_counts, dict):
            stage_counts = default_stage_counts
        else:
            stage_counts = {**stage_counts}
            stage_counts.setdefault("trade_candidates", len(trade_candidates))

        warnings_list = metadata.get("warnings", [])
        if isinstance(warnings_list, list):
            warnings_payload = [str(item) for item in warnings_list]
        else:
            warnings_payload = [str(warnings_list)]

        data_freshness = metadata.get("data_freshness")
        if not isinstance(data_freshness, dict):
            data_freshness = {
                "asof_iso_utc": asof_iso,
                "asof_ts_ms": asof_ts_ms,
            }

        manifest = {
            "run_id": run_id,
            "timestamp_utc": metadata.get("timestamp_utc") or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "config_hash": build_config_hash(self.root_config),
            "canonical_schema_version": read_canonical_schema_version(Path("docs/canonical/CHANGELOG.md")),
            "feature_flags": derive_feature_flags(self.root_config),
            "pipeline_paths": derive_pipeline_paths(self.root_config),
            "counts_per_stage": stage_counts,
            "shortlist_size_used": metadata.get("shortlist_size_used", self.root_config.get("budget", {}).get("shortlist_size", 200)),
            "orderbook_top_k_used": metadata.get("orderbook_top_k_used", self.root_config.get("budget", {}).get("orderbook_top_k", 200)),
            "data_freshness": data_freshness,
            "warnings": warnings_payload,
            "duration_seconds": float(metadata.get("duration_seconds", 0.0)),
        }
        return manifest
    
    def generate_markdown_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        btc_regime: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Generate Markdown report.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
        
        Returns:
            Markdown content as string
        """
        report = self.generate_json_report(
            reversal_results=reversal_results,
            breakout_results=breakout_results,
            pullback_results=pullback_results,
            global_top20=global_top20,
            run_date=run_date,
            metadata=metadata,
            btc_regime=btc_regime,
        )
        trade_candidates = report.get("trade_candidates", [])
        run_manifest = report.get("run_manifest", {})
        resolved_regime = report.get("btc_regime", {})

        self._validate_trade_candidates_for_markdown(trade_candidates)

        enter_candidates = [row for row in trade_candidates if row.get("decision") == "ENTER"]
        wait_candidates = [row for row in trade_candidates if row.get("decision") == "WAIT"]

        lines = [
            "# Spot Altcoin Scanner Report",
            f"**Date:** {run_date}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## ENTER Candidates",
            "",
        ]

        if enter_candidates:
            for row in enter_candidates:
                lines.extend(self._format_trade_candidate_markdown(row, include_reasons=False))
        else:
            lines.append("*No ENTER candidates.*")
            lines.append("")

        lines.extend(["## WAIT Candidates", ""])
        if wait_candidates:
            for row in wait_candidates:
                lines.extend(self._format_trade_candidate_markdown(row, include_reasons=True))
        else:
            lines.append("*No WAIT candidates.*")
            lines.append("")

        lines.extend(self._format_markdown_summary(trade_candidates, run_manifest, resolved_regime))
        return "\n".join(lines)
    

    @staticmethod
    def _format_nullable_bool(value: Any) -> str:
        if value is None:
            return "n/a"
        return "true" if value is True else "false"

    @staticmethod
    def _format_nullable_float(value: Any, digits: int = 4) -> str:
        numeric = ReportGenerator._sanitize_float_or_none(value)
        if numeric is None:
            return "n/a"
        return f"{numeric:.{digits}f}"

    @staticmethod
    def _format_reason_list(value: Any) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, list):
            normalized = [item for item in value if isinstance(item, str)]
            if not normalized:
                return "[]"
            return ", ".join(normalized)
        raise ValueError("trade_candidates.decision_reasons must be a list or null")

    def _validate_trade_candidates_for_markdown(self, trade_candidates: Any) -> None:
        if not isinstance(trade_candidates, list):
            raise ValueError("trade_candidates must be a list")
        required_fields = {"rank", "symbol", "decision", "decision_reasons"}
        for idx, row in enumerate(trade_candidates):
            if not isinstance(row, dict):
                raise ValueError(f"trade_candidates[{idx}] must be an object")
            missing = [field for field in required_fields if field not in row]
            if missing:
                raise ValueError(f"trade_candidates[{idx}] missing required fields: {', '.join(missing)}")
            decision = row.get("decision")
            if decision not in {"ENTER", "WAIT", "NO_TRADE"}:
                raise ValueError(f"trade_candidates[{idx}].decision invalid: {decision}")
            reasons = row.get("decision_reasons")
            if reasons is not None and not isinstance(reasons, list):
                raise ValueError(f"trade_candidates[{idx}].decision_reasons must be list or null")

    def _format_trade_candidate_markdown(self, row: Dict[str, Any], include_reasons: bool) -> List[str]:
        rank = row.get("rank", "?")
        symbol = row.get("symbol") or "UNKNOWN"
        coin_name = row.get("coin_name") or "Unknown"
        lines = [f"### {rank}. {symbol} ({coin_name})", ""]
        lines.append(f"- decision: {row.get('decision')}")
        if include_reasons:
            lines.append(f"- decision_reasons: {self._format_reason_list(row.get('decision_reasons'))}")
        lines.append(f"- risk_acceptable: {self._format_nullable_bool(row.get('risk_acceptable'))}")
        lines.append(f"- rr_to_target_1: {self._format_nullable_float(row.get('rr_to_target_1'))}")
        lines.append(f"- slippage_bps_20k: {self._format_nullable_float(row.get('slippage_bps_20k'))}")
        lines.append(f"- distance_to_entry_pct: {self._format_nullable_float(row.get('distance_to_entry_pct'))}")
        lines.append(f"- entry_state: {row.get('entry_state') or 'n/a'}")
        lines.append(f"- spread_pct: {self._format_nullable_float(row.get('spread_pct'), digits=6)}")
        lines.append(f"- depth_bid_1pct_usd: {self._format_nullable_float(row.get('depth_bid_1pct_usd'), digits=2)}")
        lines.append(f"- depth_ask_1pct_usd: {self._format_nullable_float(row.get('depth_ask_1pct_usd'), digits=2)}")
        lines.append("")
        return lines

    def _format_markdown_summary(
        self,
        trade_candidates: List[Dict[str, Any]],
        run_manifest: Dict[str, Any],
        btc_regime: Dict[str, Any],
    ) -> List[str]:
        counts = {"ENTER": 0, "WAIT": 0, "NO_TRADE": 0}
        for row in trade_candidates:
            decision = row.get("decision")
            if decision in counts:
                counts[decision] += 1

        lines = ["## Summary", ""]
        lines.append(f"- ENTER: {counts['ENTER']}")
        lines.append(f"- WAIT: {counts['WAIT']}")
        lines.append(f"- NO_TRADE: {counts['NO_TRADE']}")
        entry_state_counts = self._build_entry_state_counts(trade_candidates)
        lines.append("- entry_state_counts_all:")
        for state in _ENTRY_STATE_ORDER:
            lines.append(f"  - {state}: {entry_state_counts[state]}")

        regime_state = (btc_regime or {}).get("state")
        if regime_state is not None:
            lines.append(f"- BTC Regime: {regime_state}")

        run_id = (run_manifest or {}).get("run_id")
        if run_id is not None:
            lines.append(f"- run_id: {run_id}")
        canonical_schema_version = (run_manifest or {}).get("canonical_schema_version")
        if canonical_schema_version is not None:
            lines.append(f"- canonical_schema_version: {canonical_schema_version}")

        lines.append("")
        return lines

    def _format_setup_entry(self, rank: int, data: dict) -> List[str]:
        """
        Format a single setup entry for markdown output.
        
        Args:
            rank: Position in ranking (1-based)
            data: Setup data dict containing symbol, score, components, etc.
        
        Returns:
            List of markdown lines
        """
        lines = []
        
        # Extract data
        symbol = data.get('symbol', 'UNKNOWN')
        coin_name = data.get('coin_name', 'Unknown')
        score = data.get('score', 0)
        raw_score = data.get('raw_score')
        penalty_multiplier = data.get('penalty_multiplier')
        price = data.get('price_usdt')
        
        # Header with rank, symbol, name, and score
        lines.append(f"### {rank}. {symbol} ({coin_name}) - Score: {score:.1f}")
        lines.append("")

        # Score transparency
        if raw_score is not None or penalty_multiplier is not None:
            raw_display = f"{float(raw_score):.2f}" if raw_score is not None else "n/a"
            pm_display = f"{float(penalty_multiplier):.4f}" if penalty_multiplier is not None else "n/a"
            lines.append(f"**Score Details:** score={float(score):.2f}, raw_score={raw_display}, penalty_multiplier={pm_display}")
            lines.append("")
        
        # Price
        if price is not None:
            lines.append(f"**Price:** ${price:.6f} USDT")
            lines.append("")

        if "execution_gate_pass" in data:
            lines.append(f"**Execution Gate:** {bool(data.get('execution_gate_pass'))}")
            lines.append(f"**Spread %:** {data.get('spread_pct')}")
            lines.append(f"**Depth Bid 1.0% (USD):** {data.get('depth_bid_1pct_usd')}")
            lines.append(f"**Depth Ask 1.0% (USD):** {data.get('depth_ask_1pct_usd')}")
            fail_reasons = data.get('execution_gate_fail_reasons') or []
            if fail_reasons:
                lines.append(f"**Execution Gate Fail Reasons:** {', '.join(fail_reasons)}")
            lines.append("")

        global_volume_24h_usd = self._sanitize_optional_metric(data.get('global_volume_24h_usd'))
        turnover_24h = self._sanitize_optional_metric(data.get('turnover_24h'))
        mexc_share_24h = self._sanitize_optional_metric(data.get('mexc_share_24h'))
        lines.append("**Market Activity:**")
        lines.append(f"- global_volume_24h_usd: {self._format_m_usd(global_volume_24h_usd)}")
        lines.append(f"- turnover_24h: {self._format_pct(turnover_24h)}")
        lines.append(f"- mexc_share_24h: {self._format_pct(mexc_share_24h)}")
        lines.append("")
        
        # Components
        components = data.get('components', {})
        if components:
            lines.append("**Components:**")
            for comp_name, comp_value in components.items():
                lines.append(f"- {comp_name.replace('_', ' ').capitalize()}: {comp_value:.1f}")
            lines.append("")
        
        # Analysis
        analysis = data.get('analysis', '')
        if analysis:
            lines.append("**Analysis:**")
            if isinstance(analysis, str):
                lines.append(analysis)
            else:
                lines.append(json.dumps(analysis, ensure_ascii=False))
            lines.append("")
        
        # Flags - handle both dict and list formats
        flags = data.get('flags', {})
        flag_list = []
        
        if isinstance(flags, dict):
            flag_list = [k for k, v in flags.items() if v]
        elif isinstance(flags, list):
            flag_list = flags
        
        if flag_list:
            flag_str = ', '.join(flag_list)
            lines.append(f"**⚠️ Flags:** {flag_str}")
            lines.append("")
        
        return lines
        
    @staticmethod
    def _with_rank(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return entries with explicit 1-based rank preserving order."""
        ranked = []
        for idx, entry in enumerate(entries, start=1):
            ranked_entry = dict(entry)
            ranked_entry["rank"] = idx
            ranked_entry["global_volume_24h_usd"] = ReportGenerator._sanitize_optional_metric(entry.get("global_volume_24h_usd"))
            ranked_entry["turnover_24h"] = ReportGenerator._sanitize_optional_metric(entry.get("turnover_24h"))
            ranked_entry["mexc_share_24h"] = ReportGenerator._sanitize_optional_metric(entry.get("mexc_share_24h"))
            ranked.append(ranked_entry)
        return ranked


    @staticmethod
    def _format_m_usd(value: Any) -> str:
        if value is None:
            return "n/a"
        return f"{value / 1_000_000:.1f}".replace('.', ',') + " M USD"

    @staticmethod
    def _format_pct(value: Any) -> str:
        if value is None:
            return "n/a"
        return f"{value * 100:.2f}".replace('.', ',') + " %"

    @staticmethod
    def _sanitize_optional_metric(value: Any) -> Any:
        """Return nullable numeric metric; invalid values become None."""
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric < 0:
            return None
        if numeric != numeric:  # NaN
            return None
        return numeric

    @staticmethod
    def _sanitize_reason_list(value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        out: List[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
        return out

    @staticmethod
    def _sanitize_bool_or_none(value: Any) -> Any:
        if value is None or isinstance(value, bool):
            return value
        return None

    @staticmethod
    def _sanitize_float_or_none(value: Any) -> Any:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric != numeric:
            return None
        return numeric

    @classmethod
    def _sanitize_positive_float_or_none(cls, value: Any) -> Any:
        numeric = cls._sanitize_float_or_none(value)
        if numeric is None:
            return None
        if numeric in (float("inf"), float("-inf")):
            return None
        if numeric <= 0:
            return None
        return numeric

    @classmethod
    def _resolve_planned_entry_price(cls, row: Dict[str, Any]) -> Any:
        if "entry_price_usdt" in row:
            return cls._sanitize_positive_float_or_none(row.get("entry_price_usdt"))

        analysis = row.get("analysis")
        if not isinstance(analysis, dict):
            return None

        trade_levels = analysis.get("trade_levels")
        if not isinstance(trade_levels, dict):
            return None

        setup_type = str(row.get("best_setup_type") or "").lower()
        if setup_type == "pullback":
            zone = trade_levels.get("entry_zone")
            zone = zone if isinstance(zone, dict) else {}
            return cls._sanitize_positive_float_or_none(zone.get("center"))

        return cls._sanitize_positive_float_or_none(trade_levels.get("entry_trigger"))

    @staticmethod
    def _decision_sort_key(row: Dict[str, Any]) -> Any:
        decision = str(row.get("decision") or "NO_TRADE").upper()
        priority = _DECISION_PRIORITY.get(decision, 99)
        global_score = ReportGenerator._sanitize_float_or_none(row.get("global_score"))
        score_key = -(global_score if global_score is not None else float("-inf"))
        return (
            priority,
            score_key,
            str(row.get("symbol") or ""),
            str(row.get("best_setup_type") or ""),
        )


    @classmethod
    def _compute_distance_to_entry_pct(cls, entry_price: Any, current_price: Any) -> float | None:
        entry_numeric = cls._sanitize_positive_float_or_none(entry_price)
        current_numeric = cls._sanitize_positive_float_or_none(current_price)
        if entry_numeric is None or current_numeric is None:
            return None
        return ((current_numeric / entry_numeric) - 1.0) * 100.0

    @classmethod
    def _resolve_target_price(cls, row: Dict[str, Any], index: int) -> float | None:
        direct_key = f"target_{index}_price"
        direct_value = cls._sanitize_positive_float_or_none(row.get(direct_key))
        if direct_value is not None:
            return direct_value

        analysis = row.get("analysis") if isinstance(row.get("analysis"), dict) else {}
        trade_levels = analysis.get("trade_levels") if isinstance(analysis.get("trade_levels"), dict) else {}
        targets = trade_levels.get("targets") if isinstance(trade_levels.get("targets"), list) else []
        if len(targets) < index:
            return None
        return cls._sanitize_positive_float_or_none(targets[index - 1])

    @classmethod
    def _compute_rr_to_target(cls, entry_price: Any, stop_price: Any, target_price: Any) -> float | None:
        entry_numeric = cls._sanitize_positive_float_or_none(entry_price)
        stop_numeric = cls._sanitize_positive_float_or_none(stop_price)
        target_numeric = cls._sanitize_positive_float_or_none(target_price)
        if entry_numeric is None or stop_numeric is None or target_numeric is None:
            return None
        if stop_numeric >= entry_numeric:
            return None
        if target_numeric <= entry_numeric:
            return None
        risk_abs = entry_numeric - stop_numeric
        return (target_numeric - entry_numeric) / risk_abs

    @classmethod
    def _classify_entry_state(cls, distance_to_entry_pct: Any) -> str | None:
        distance_numeric = cls._sanitize_float_or_none(distance_to_entry_pct)
        if distance_numeric is None:
            return None
        if distance_numeric < -_ENTRY_AT_TRIGGER_TOLERANCE_PCT:
            return "early"
        if abs(distance_numeric) <= _ENTRY_AT_TRIGGER_TOLERANCE_PCT:
            return "at_trigger"
        if distance_numeric <= _ENTRY_CHASED_THRESHOLD_PCT:
            return "late"
        return "chased"

    @staticmethod
    def _entry_state_key(entry_state: Any) -> str:
        if entry_state in {"early", "at_trigger", "late", "chased"}:
            return entry_state
        return "null"

    def _build_entry_state_counts(self, trade_candidates: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {state: 0 for state in _ENTRY_STATE_ORDER}
        for row in trade_candidates:
            counts[self._entry_state_key(row.get("entry_state"))] += 1
        return counts

    def _build_entry_state_counts_by_decision(self, trade_candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        out: Dict[str, Dict[str, int]] = {
            "ENTER": {state: 0 for state in _ENTRY_STATE_ORDER},
            "WAIT": {state: 0 for state in _ENTRY_STATE_ORDER},
            "NO_TRADE": {state: 0 for state in _ENTRY_STATE_ORDER},
        }
        for row in trade_candidates:
            decision = row.get("decision")
            if decision in out:
                out[decision][self._entry_state_key(row.get("entry_state"))] += 1
        return out

    @staticmethod
    def _append_timing_reason(decision_reasons: List[str], entry_state: str | None) -> List[str]:
        timing_reason = _ENTRY_STATE_REASON_MAP.get(entry_state)
        if timing_reason is None:
            return list(decision_reasons)
        if timing_reason in decision_reasons:
            return list(decision_reasons)
        return [*decision_reasons, timing_reason]

    def _build_trade_candidates(self, global_top20: List[Dict[str, Any]], btc_regime: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        regime_state = ((btc_regime or {}).get("state") or "NEUTRAL")
        candidates: List[Dict[str, Any]] = []
        for row in global_top20:
            entry_price = self._resolve_planned_entry_price(row)
            current_price = self._sanitize_positive_float_or_none(row.get("price_usdt"))
            distance_to_entry_pct = self._compute_distance_to_entry_pct(entry_price, current_price)
            entry_state = self._classify_entry_state(distance_to_entry_pct)
            stop_price_initial = self._sanitize_positive_float_or_none(row.get("stop_price_initial"))
            target_1_price = self._resolve_target_price(row, index=1)
            target_2_price = self._resolve_target_price(row, index=2)
            target_3_price = self._resolve_target_price(row, index=3)
            rr_to_target_1 = self._compute_rr_to_target(entry_price, stop_price_initial, target_1_price)
            rr_to_target_2 = self._compute_rr_to_target(entry_price, stop_price_initial, target_2_price)
            decision_reasons = self._append_timing_reason(
                self._sanitize_reason_list(row.get("decision_reasons")),
                entry_state,
            )
            candidate = {
                "rank": None,
                "symbol": row.get("symbol"),
                "coin_name": row.get("coin_name"),
                "decision": row.get("decision", "NO_TRADE"),
                "decision_reasons": decision_reasons,
                "entry_price_usdt": entry_price,
                "current_price_usdt": current_price,
                "distance_to_entry_pct": self._sanitize_float_or_none(distance_to_entry_pct),
                "entry_state": entry_state,
                "stop_price_initial": stop_price_initial,
                "risk_pct_to_stop": self._sanitize_float_or_none(row.get("risk_pct_to_stop")),
                "target_1_price": self._sanitize_float_or_none(target_1_price),
                "target_2_price": self._sanitize_float_or_none(target_2_price),
                "target_3_price": self._sanitize_float_or_none(target_3_price),
                "rr_to_target_1": self._sanitize_float_or_none(rr_to_target_1),
                "rr_to_target_2": self._sanitize_float_or_none(rr_to_target_2),
                "best_setup_type": row.get("best_setup_type"),
                "setup_subtype": row.get("setup_subtype"),
                "setup_score": self._sanitize_float_or_none(row.get("setup_score", row.get("score"))),
                "global_score": self._sanitize_float_or_none(row.get("global_score", row.get("score"))),
                "entry_ready": self._sanitize_bool_or_none(row.get("entry_ready")),
                "entry_readiness_reasons": self._sanitize_reason_list(row.get("entry_readiness_reasons")),
                "tradeability_class": row.get("tradeability_class"),
                "execution_mode": row.get("execution_mode", "none"),
                "spread_pct": self._sanitize_float_or_none(row.get("spread_pct")),
                "depth_bid_1pct_usd": self._sanitize_float_or_none(row.get("depth_bid_1pct_usd")),
                "depth_ask_1pct_usd": self._sanitize_float_or_none(row.get("depth_ask_1pct_usd")),
                "slippage_bps_5k": self._sanitize_float_or_none(row.get("slippage_bps_5k")),
                "slippage_bps_20k": self._sanitize_float_or_none(row.get("slippage_bps_20k", row.get("slippage_bps"))),
                "risk_acceptable": self._sanitize_bool_or_none(row.get("risk_acceptable")),
                "market_cap_usd": self._sanitize_float_or_none(row.get("market_cap_usd", row.get("market_cap"))),
                "btc_regime": row.get("btc_regime", row.get("btc_regime_state", regime_state)),
                "flags": row.get("flags", []),
            }
            if "directional_volume_preparation" in row:
                candidate["directional_volume_preparation"] = self._sanitize_directional_volume_preparation(
                    row.get("directional_volume_preparation")
                )
            candidates.append(candidate)

        candidates.sort(key=self._decision_sort_key)
        for idx, row in enumerate(candidates, start=1):
            row["rank"] = idx
        return candidates

    @staticmethod
    def _sanitize_directional_volume_preparation(value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("directional_volume_preparation must be object or null when present")

        allowed_keys = {
            "buy_volume_share",
            "sell_volume_share",
            "imbalance_ratio",
            "lookback_bars",
        }
        unknown_keys = sorted(set(value.keys()) - allowed_keys)
        if unknown_keys:
            joined = ", ".join(unknown_keys)
            raise ValueError(f"directional_volume_preparation has unknown keys: {joined}")

        def _finite_number_or_none(raw: Any, field: str) -> float | None:
            if raw is None:
                return None
            try:
                numeric = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"directional_volume_preparation.{field} must be finite number or null") from exc
            if numeric != numeric or numeric in (float("inf"), float("-inf")):
                raise ValueError(f"directional_volume_preparation.{field} must be finite number or null")
            return numeric

        lookback_raw = value.get("lookback_bars")
        lookback_bars = None
        if lookback_raw is not None:
            if isinstance(lookback_raw, bool):
                raise ValueError("directional_volume_preparation.lookback_bars must be positive integer or null")
            try:
                lookback_bars = int(lookback_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError("directional_volume_preparation.lookback_bars must be positive integer or null") from exc
            if lookback_bars <= 0:
                raise ValueError("directional_volume_preparation.lookback_bars must be positive integer or null")

        return {
            "buy_volume_share": _finite_number_or_none(value.get("buy_volume_share"), "buy_volume_share"),
            "sell_volume_share": _finite_number_or_none(value.get("sell_volume_share"), "sell_volume_share"),
            "imbalance_ratio": _finite_number_or_none(value.get("imbalance_ratio"), "imbalance_ratio"),
            "lookback_bars": lookback_bars,
        }

    def generate_json_report(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None,
        btc_regime: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate JSON report.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata dict
        
        Returns:
            Report dict (JSON-serializable)
        """
        trade_candidates = self._build_trade_candidates(global_top20[:20], btc_regime=btc_regime)
        run_manifest = self._build_run_manifest(run_date=run_date, metadata=metadata, trade_candidates=trade_candidates)
        entry_state_counts_by_decision = self._build_entry_state_counts_by_decision(trade_candidates)

        report = {
            'schema_version': REPORT_SCHEMA_VERSION,
            'meta': {
                'date': run_date,
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'version': REPORT_META_VERSION
            },
            'summary': {
                'reversal_count': len(reversal_results),
                'breakout_count': len(breakout_results),
                'pullback_count': len(pullback_results),
                'total_scored': len(reversal_results) + len(breakout_results) + len(pullback_results),
                'global_top20_count': len(global_top20),
                'entry_state_counts_all': self._build_entry_state_counts(trade_candidates),
                'entry_state_counts_enter': entry_state_counts_by_decision['ENTER'],
                'entry_state_counts_wait': entry_state_counts_by_decision['WAIT'],
                'entry_state_counts_no_trade': entry_state_counts_by_decision['NO_TRADE'],
            },
            'setups': {
                'reversals': self._with_rank(reversal_results[:self.top_n]),
                'breakouts': self._with_rank(breakout_results[:self.top_n]),
                'breakout_immediate_1_5d': self._with_rank([
                    row for row in breakout_results if not str(row.get('setup_id', '')).endswith('retest_1_5d')
                ][:self.top_n]),
                'breakout_retest_1_5d': self._with_rank(
                    [row for row in breakout_results if str(row.get('setup_id', '')).endswith('retest_1_5d')][:self.top_n]
                ),
                'pullbacks': self._with_rank(pullback_results[:self.top_n]),
                'global_top20': self._with_rank(global_top20[:20])
            },
            'trade_candidates': trade_candidates,
            'run_manifest': run_manifest,
            'btc_regime': btc_regime or {
                'state': 'RISK_OFF',
                'multiplier_risk_on': 1.0,
                'multiplier_risk_off': 0.85,
                'checks': {
                    'close_gt_ema50': False,
                    'ema20_gt_ema50': False,
                },
            },
        }
        
        if metadata:
            report['meta'].update(metadata)
        
        return report
    
    def save_reports(
        self,
        reversal_results: List[Dict[str, Any]],
        breakout_results: List[Dict[str, Any]],
        pullback_results: List[Dict[str, Any]],
        global_top20: List[Dict[str, Any]],
        run_date: str,
        metadata: Dict[str, Any] = None,
        btc_regime: Dict[str, Any] = None,
    ) -> Dict[str, Path]:
        """
        Generate and save Markdown, JSON, and Excel reports.
        
        Args:
            reversal_results: Scored reversal setups
            breakout_results: Scored breakout setups
            pullback_results: Scored pullback setups
            run_date: Date string (YYYY-MM-DD)
            metadata: Optional metadata
        
        Returns:
            Dict with paths: {'markdown': Path, 'json': Path, 'excel': Path}
        """
        logger.info(f"Generating reports for {run_date}")
        
        # Generate Markdown
        md_content = self.generate_markdown_report(
            reversal_results, breakout_results, pullback_results, global_top20, run_date, btc_regime=btc_regime, metadata=metadata
        )
        
        # Generate JSON
        json_content = self.generate_json_report(
            reversal_results, breakout_results, pullback_results, global_top20, run_date, metadata, btc_regime=btc_regime
        )
        
        # Save Markdown
        md_path = self.reports_dir / f"{run_date}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Markdown report saved: {md_path}")
        
        # Save JSON
        json_path = self.reports_dir / f"{run_date}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON report saved: {json_path}")

        manifest = json_content.get("run_manifest", {})
        run_id = manifest.get("run_id", run_date)
        manifest_path = self.reports_dir / f"{run_date}_{run_id}.manifest.json"
        write_manifest_atomic(manifest_path, manifest)
        logger.info(f"Run manifest saved: {manifest_path}")
        
        # Generate Excel
        try:
            from .excel_output import ExcelReportGenerator
            # Reconstruct config dict for Excel generator
            excel_config = {
                'output': {
                    'reports_dir': str(self.reports_dir),
                    'top_n_per_setup': self.top_n
                }
            }
            excel_gen = ExcelReportGenerator(excel_config)
            excel_path = excel_gen.generate_excel_report(
                trade_candidates=json_content.get('trade_candidates', []),
                run_date=run_date,
                run_manifest=json_content.get('run_manifest', {}),
                metadata=metadata,
                btc_regime=btc_regime,
            )
            logger.info(f"Excel report saved: {excel_path}")
        except ImportError:
            logger.warning("openpyxl not installed - Excel export skipped")
            excel_path = None
        except Exception as e:
            logger.error(f"Excel generation failed: {e}")
            excel_path = None
        
        result = {
            'markdown': md_path,
            'json': json_path,
            'manifest': manifest_path,
        }
        
        if excel_path:
            result['excel'] = excel_path
        
        return result
