from pathlib import Path

from tools.ai_sparring.context_loader import load_context


def test_context_sources_have_stable_ordering() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    contexts = load_context(
        repo_root=repo_root,
        extra_paths=[
            "tools/ai_sparring/cli.py",
            "docs/canonical/ARCHITECTURE.md",
            "tools/ai_sparring/cli.py",
        ],
    )
    paths = [item["path"] for item in contexts]
    assert paths[:3] == [
        "docs/AGENTS.md",
        "docs/code_map.md",
        "docs/canonical/ROADMAP.md",
    ]
    assert paths[3:] == [
        "docs/canonical/ARCHITECTURE.md",
        "tools/ai_sparring/cli.py",
    ]
