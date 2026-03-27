import json
from datetime import datetime, timezone
from pathlib import Path

from tools.ai_sparring.writeback import compute_writeback_plan, perform_writeback


def _session_payload() -> dict:
    return {
        "status": "completed",
        "mode": "ticket_review",
        "participants": {
            "drafter": {"provider": "openai", "model": "gpt-5"},
            "reviewer": {"provider": "anthropic", "model": "claude"},
        },
        "ticket_draft": {
            "status": "generated",
            "path": "ticket_draft.md",
            "title": "AI Sparring: Test Title",
            "writeback": {
                "requested": True,
                "status": "not_requested",
                "branch": None,
                "target_path": None,
                "pull_request_number": None,
                "pull_request_url": None,
                "commit_sha": None,
                "error": None,
            },
        },
    }


def test_branch_and_target_path_are_deterministic_and_collision_handled() -> None:
    payload = _session_payload()
    plan = compute_writeback_plan(payload=payload, utc_now=datetime(2026, 3, 27, tzinfo=timezone.utc))
    assert plan.branch.startswith("ai-sparring/drafts/2026-03-27-")
    assert plan.target_path.startswith("docs/tickets/drafts/2026-03-27-")


def test_writeback_defaults_to_not_requested(tmp_path) -> None:
    out = tmp_path / "artifacts"
    out.mkdir()
    payload = _session_payload()
    (out / "session.json").write_text(json.dumps(payload), encoding="utf-8")
    result = perform_writeback(
        repo_root=Path(__file__).resolve().parents[3],
        output_dir=out,
        github_repo="owner/repo",
        github_token="x",
        writeback_enabled=False,
    )
    assert result["ticket_draft"]["writeback"]["status"] == "not_requested"


def test_ticket_draft_writeback_metadata_uses_null_for_absent_fields(tmp_path) -> None:
    out = tmp_path / "artifacts"
    out.mkdir()
    payload = _session_payload()
    payload["ticket_draft"]["status"] = "failed"
    payload["ticket_draft"]["path"] = None
    (out / "session.json").write_text(json.dumps(payload), encoding="utf-8")
    result = perform_writeback(
        repo_root=Path(__file__).resolve().parents[3],
        output_dir=out,
        github_repo="owner/repo",
        github_token="x",
        writeback_enabled=True,
    )
    wb = result["ticket_draft"]["writeback"]
    assert wb["status"] == "skipped_no_draft"
    assert wb["branch"] is None
    assert wb["pull_request_number"] is None
