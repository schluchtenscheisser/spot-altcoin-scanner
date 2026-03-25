from pathlib import Path


def test_docs_foundation_roadmap_exists_and_index_references_it() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    roadmap_path = repo_root / "docs/canonical/ROADMAP.md"
    index_path = repo_root / "docs/canonical/INDEX.md"

    assert roadmap_path.is_file()
    index_text = index_path.read_text(encoding="utf-8")
    assert "[ROADMAP](ROADMAP.md)" in index_text
