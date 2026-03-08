"""Run manifest generation and persistence helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

_ALLOWED_SHADOW_MODES = {"legacy_only", "new_only", "parallel"}
_ALLOWED_PRIMARY_PATHS = {"legacy", "new"}


def _nested_mapping_value(config: Dict[str, Any], path: List[str], default: Any) -> Any:
    cursor: Any = config
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            return default
        cursor = cursor[key]
    return cursor


def _nested_bool(config: Dict[str, Any], path: List[str], default: bool) -> bool:
    return bool(_nested_mapping_value(config, path, default))


def resolve_shadow_mode(config: Dict[str, Any]) -> str:
    shadow_cfg = config.get("shadow", {}) if isinstance(config, dict) else {}
    mode = shadow_cfg.get("mode", "parallel") if isinstance(shadow_cfg, dict) else "parallel"
    mode = str(mode)
    if mode not in _ALLOWED_SHADOW_MODES:
        raise ValueError(f"shadow.mode must be one of {sorted(_ALLOWED_SHADOW_MODES)}")
    return mode


def resolve_pipeline_paths(config: Dict[str, Any]) -> Dict[str, Any]:
    mode = resolve_shadow_mode(config)
    shadow_cfg = config.get("shadow", {}) if isinstance(config, dict) else {}

    has_config_primary = isinstance(shadow_cfg, dict) and "primary_path" in shadow_cfg
    raw_primary = shadow_cfg.get("primary_path") if isinstance(shadow_cfg, dict) else None

    if has_config_primary:
        primary_path = str(raw_primary)
        if primary_path not in _ALLOWED_PRIMARY_PATHS:
            raise ValueError(f"shadow.primary_path must be one of {sorted(_ALLOWED_PRIMARY_PATHS)}")
    else:
        primary_path = None

    if mode == "legacy_only":
        if has_config_primary and primary_path != "legacy":
            raise ValueError("shadow.mode=legacy_only requires shadow.primary_path=legacy when configured")
        resolved_primary = "legacy"
        source = "config" if has_config_primary else "derived"
    elif mode == "new_only":
        if has_config_primary and primary_path != "new":
            raise ValueError("shadow.mode=new_only requires shadow.primary_path=new when configured")
        resolved_primary = "new"
        source = "config" if has_config_primary else "derived"
    else:
        resolved_primary = primary_path if has_config_primary else "legacy"
        source = "config" if has_config_primary else "default"

    return {
        "shadow_mode": mode,
        "legacy_path_enabled": mode in {"legacy_only", "parallel"},
        "new_path_enabled": mode in {"new_only", "parallel"},
        "primary_path": resolved_primary,
        "primary_path_source": source,
    }


def derive_pipeline_paths(config: Dict[str, Any]) -> Dict[str, Any]:
    return resolve_pipeline_paths(config)


def derive_feature_flags(config: Dict[str, Any]) -> Dict[str, bool]:
    """Return a deterministic map of relevant feature flags and their states."""
    return {
        "decision_enabled": _nested_bool(config, ["decision", "enabled"], True),
        "risk_enabled": _nested_bool(config, ["risk", "enabled"], True),
        "tradeability_enabled": _nested_bool(config, ["tradeability", "enabled"], True),
        "btc_regime_enabled": _nested_bool(config, ["btc_regime", "enabled"], False),
        "breakout_scoring_enabled": _nested_bool(config, ["scoring", "breakout", "enabled"], True),
        "pullback_scoring_enabled": _nested_bool(config, ["scoring", "pullback", "enabled"], True),
        "reversal_scoring_enabled": _nested_bool(config, ["scoring", "reversal", "enabled"], True),
        "mexc_enabled": _nested_bool(config, ["data_sources", "mexc", "enabled"], True),
        "shadow_mode_parallel": derive_pipeline_paths(config)["shadow_mode"] == "parallel",
    }


def build_config_hash(config: Dict[str, Any]) -> str:
    """Build a stable SHA-256 hash from the raw runtime config."""
    canonical_json = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def read_canonical_schema_version(changelog_path: Path) -> str:
    """Read canonical_schema_version from docs/canonical/CHANGELOG.md."""
    for line in changelog_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("canonical_schema_version:"):
            _, value = line.split(":", 1)
            version = value.strip()
            if version:
                return version
            raise ValueError("canonical_schema_version is empty")
    raise ValueError("canonical_schema_version not found in canonical changelog")


def write_manifest_atomic(path: Path, payload: Dict[str, Any]) -> None:
    """Atomically write manifest JSON to avoid partial writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)
