from scanner.pipeline.manifest import derive_pipeline_paths
import pytest


def test_manifest_pipeline_paths_parallel_default_primary_is_legacy() -> None:
    paths = derive_pipeline_paths({"shadow": {"mode": "parallel"}})

    assert paths == {
        "shadow_mode": "parallel",
        "legacy_path_enabled": True,
        "new_path_enabled": True,
        "primary_path": "legacy",
        "primary_path_source": "default",
    }


def test_manifest_pipeline_paths_parallel_configured_primary_new() -> None:
    paths = derive_pipeline_paths({"shadow": {"mode": "parallel", "primary_path": "new"}})

    assert paths["primary_path"] == "new"
    assert paths["primary_path_source"] == "config"


def test_manifest_pipeline_paths_mode_primary_contradiction_fails() -> None:
    with pytest.raises(ValueError, match="shadow.mode=legacy_only requires shadow.primary_path=legacy"):
        derive_pipeline_paths({"shadow": {"mode": "legacy_only", "primary_path": "new"}})
