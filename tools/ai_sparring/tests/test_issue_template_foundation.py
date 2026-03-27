from pathlib import Path

from tools.ai_sparring.issue_parser import parse_issue_body


def test_issue_template_foundation_renders_expected_headings() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    content = (repo_root / ".github/ISSUE_TEMPLATE/ai-sparring-session.yml").read_text(encoding="utf-8")
    for heading in (
        "## Prompt",
        "## Mode",
        "## Rounds",
        "## Drafter Provider",
        "## Drafter Model",
        "## Reviewer Provider",
        "## Reviewer Model",
        "## Extra Context Paths",
    ):
        assert heading in content


def test_parse_issue_body_by_exact_headings() -> None:
    body = """## Prompt\nReview it\n\n## Mode\nticket_review\n\n## Rounds\n2\n\n## Drafter Provider\n\n## Drafter Model\n\n## Reviewer Provider\n\n## Reviewer Model\n\n## Extra Context Paths\n"""
    parsed = parse_issue_body(body)
    assert parsed["Prompt"] == "Review it"
    assert parsed["Mode"] == "ticket_review"
    assert parsed["Rounds"] == "2"
