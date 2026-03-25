from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_readme_contains_onboarding_minimum_sections() -> None:
    text = _read("README.md")
    required_snippets = [
        "## Installation",
        "## Configuration",
        "## Running the scanner",
        "python -m scanner.main --mode standard",
        "Independence-Release",
        "legacy",
        "docs/canonical/INDEX.md",
    ]
    for snippet in required_snippets:
        assert snippet in text, f"missing README snippet: {snippet!r}"


def test_authority_is_role_aware_not_flat_bucket() -> None:
    text = _read("docs/canonical/AUTHORITY.md")
    assert "role-aware" in text
    assert "active_independence_release" in text
    assert "legacy_reference_only" in text
    assert "independence_release_gesamtkonzept_final.md" in text


def test_touched_legacy_contracts_are_explicitly_classified() -> None:
    for rel in [
        "docs/canonical/PIPELINE.md",
        "docs/canonical/OUTPUT_SCHEMA.md",
        "docs/canonical/DECISION_LAYER.md",
    ]:
        text = _read(rel)
        assert "role: legacy_reference_only" in text, f"missing legacy role in {rel}"
        assert "## Document role" in text, f"missing document role section in {rel}"


def test_reports_doc_is_explicit_active_independence_release() -> None:
    text = _read("docs/canonical/REPORTS.md")
    assert "role: active_independence_release" in text
    assert "Classification: `active_independence_release`" in text
