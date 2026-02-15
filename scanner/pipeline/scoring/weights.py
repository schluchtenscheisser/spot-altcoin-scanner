"""Shared scorer weight loading helpers."""

import logging
from typing import Any, Dict


logger = logging.getLogger(__name__)

_WEIGHT_SUM_TOLERANCE = 1e-6


def load_component_weights(
    *,
    scoring_cfg: Dict[str, Any],
    section_name: str,
    default_weights: Dict[str, float],
    aliases: Dict[str, str],
) -> Dict[str, float]:
    """Load scorer component weights with deterministic compatibility behavior.

    Modes:
    - compat (default): canonical keys may be mixed with legacy aliases; missing keys are
      filled from defaults; no normalization is applied.
    - strict: all canonical keys must be present in config.scoring.<section>.weights.
    """

    mode = str(scoring_cfg.get("weights_mode", "compat")).strip().lower()
    if mode not in {"compat", "strict"}:
        logger.warning(
            "Unknown weights_mode '%s' for config.scoring.%s, using compat",
            mode,
            section_name,
        )
        mode = "compat"

    cfg_weights = scoring_cfg.get("weights")
    if not isinstance(cfg_weights, dict):
        logger.warning("Using default weights for config.scoring.%s.weights", section_name)
        return default_weights.copy()

    resolved: Dict[str, float] = {}
    for canonical_key, fallback_value in default_weights.items():
        alias_key = aliases.get(canonical_key)
        canonical_present = canonical_key in cfg_weights and cfg_weights.get(canonical_key) is not None
        alias_present = bool(alias_key) and alias_key in cfg_weights and cfg_weights.get(alias_key) is not None

        if canonical_present and alias_present and cfg_weights[canonical_key] != cfg_weights[alias_key]:
            logger.warning(
                "Conflicting canonical/legacy weights for config.scoring.%s.weights.%s/%s; using canonical value",
                section_name,
                canonical_key,
                alias_key,
            )

        if canonical_present:
            resolved[canonical_key] = float(cfg_weights[canonical_key])
        elif alias_present and mode == "compat":
            resolved[canonical_key] = float(cfg_weights[alias_key])
        elif mode == "compat":
            resolved[canonical_key] = float(fallback_value)

    if mode == "strict":
        missing = [k for k in default_weights if k not in resolved]
        if missing:
            logger.warning(
                "Missing required canonical weight keys for config.scoring.%s.weights: %s. Using defaults.",
                section_name,
                ", ".join(missing),
            )
            return default_weights.copy()

    if any(v < 0 for v in resolved.values()):
        logger.warning("Negative weights detected for config.scoring.%s.weights. Using defaults.", section_name)
        return default_weights.copy()

    total = sum(resolved.values())
    if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
        logger.warning(
            "Weight sum for config.scoring.%s.weights must be ~1.0 (got %.10f). Using defaults.",
            section_name,
            total,
        )
        return default_weights.copy()

    return resolved
