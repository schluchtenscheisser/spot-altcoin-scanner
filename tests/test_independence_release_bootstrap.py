from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_DIRS = [
    "reports/index",
    "reports/daily",
    "reports/runs",
    "reports/aux",
    "snapshots/history",
    "snapshots/runs",
    "evaluation/exports",
    "evaluation/replay",
    "evaluation/calibration",
    "artifacts",
    "legacy",
    "scanner/universe",
    "scanner/data",
    "scanner/features",
    "scanner/axes",
    "scanner/phase",
    "scanner/state",
    "scanner/entry",
    "scanner/execution",
    "scanner/decision",
    "scanner/storage",
    "scanner/output",
    "scanner/runners",
    "scanner/evaluation",
]


REQUIRED_DOC_SNIPPETS = {
    "docs/canonical/ARCHITECTURE.md": [
        "Independence-Release",
        "scanner/",
        "scanner/universe/",
        "scanner/evaluation/",
    ],
    "docs/canonical/SCOPE.md": [
        "7 Abschnittsdateien",
        "Legacy",
        "Leitprinzipien",
    ],
    "docs/canonical/GLOSSARY.md": [
        "daily_bar_id",
        "intraday_promotion_scan",
        "bars_since_*",
    ],
    "docs/canonical/DATA_MODEL.md": [
        "SQLite",
        "Parquet",
        "Group A",
        "Group D",
    ],
    "docs/canonical/RUNTIME_AND_OPERATIONS.md": [
        "Daily Discovery Scan",
        "1.",
        "Intraday Promotion Scan",
        "7.",
    ],
    "docs/canonical/REPORTS.md": [
        "reports/",
        "reports/index/",
        "Verbindliche Dateitypen",
    ],
    "docs/canonical/SNAPSHOTS.md": [
        "Class A",
        "Class D",
        "Parquet",
    ],
    "docs/canonical/TEST_STRATEGY.md": [
        "Type 1",
        "Type 4",
        "Validation strategy",
    ],
    "docs/canonical/CHANGELOG.md": [
        "2026-03-23",
        "Independence-Release bootstrap",
    ],
    "docs/canonical/MIGRATION_NOTES.md": [
        "Directly reusable",
        "Structural template only",
        "Not carried forward as primary architecture",
    ],
    "docs/canonical/open_questions.md": [
        "Open questions",
        "Gesamtkonzept §21",
    ],
    "docs/canonical/feature_enhancements.md": [
        "bewusst verschobene Themen",
        "none yet",
    ],
}


def test_required_bootstrap_directories_exist():
    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        assert path.is_dir(), f"missing directory: {rel}"


def test_required_bootstrap_docs_have_expected_content():
    for rel, snippets in REQUIRED_DOC_SNIPPETS.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert text.strip(), f"empty doc: {rel}"
        for snippet in snippets:
            assert snippet in text, f"missing snippet {snippet!r} in {rel}"


def test_readme_marks_independence_release_as_primary_target():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Independence-Release" in text
    assert "bootstrap repository" in text
    assert "legacy" in text.lower()
