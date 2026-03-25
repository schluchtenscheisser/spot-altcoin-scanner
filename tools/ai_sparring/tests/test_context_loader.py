from pathlib import Path

import pytest

from tools.ai_sparring.context_loader import DEFAULT_CONTEXT_SOURCES, load_default_context


def test_context_sources_are_in_fixed_order() -> None:
    assert DEFAULT_CONTEXT_SOURCES == (
        "docs/AGENTS.md",
        "docs/code_map.md",
        "docs/canonical/ROADMAP.md",
    )


def test_missing_context_source_raises() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    missing_path = repo_root / "docs/canonical/ROADMAP.md"
    backup_path = repo_root / "docs/canonical/ROADMAP.md.bak_test"

    missing_path.rename(backup_path)
    try:
        with pytest.raises(FileNotFoundError, match="Missing required context source"):
            load_default_context(repo_root)
    finally:
        backup_path.rename(missing_path)
