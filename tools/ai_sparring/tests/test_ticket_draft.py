import json
from pathlib import Path

from tools.ai_sparring.errors import FatalProviderError
from tools.ai_sparring.providers.base import ProviderResult
from tools.ai_sparring.session import SessionConfig, run_session


class _ScriptedProvider:
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.calls = 0

    def generate(self, *, input_text: str):
        self.calls += 1
        item = self.scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _Result(ProviderResult):
    pass


def _config(tmp_path: Path) -> SessionConfig:
    return SessionConfig(
        prompt="review this design",
        mode="ticket_review",
        rounds=1,
        drafter_provider="fake",
        drafter_model=None,
        reviewer_provider="fake",
        reviewer_model=None,
        context_paths=(),
        output_dir=tmp_path,
    )


def test_completed_session_generates_ticket_draft(monkeypatch, tmp_path) -> None:
    drafter = _ScriptedProvider(
        [
            _Result("fake", None, "draft-1", 1, None),
            _Result("fake", None, "revision-1", 1, None),
            _Result("fake", None, "---\ntitle: \"Generated Title\"\n---\n# Body\n", 1, None),
        ]
    )
    reviewer = _ScriptedProvider([_Result("fake", None, "review-1", 1, None)])
    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    payload = run_session(_config(tmp_path), repo_root=Path(__file__).resolve().parents[3])

    assert payload["status"] == "completed"
    assert payload["ticket_draft"]["status"] == "generated"
    assert (tmp_path / "ticket_draft.md").exists()
    assert drafter.calls == 3


def test_non_completed_session_skips_ticket_draft(monkeypatch, tmp_path) -> None:
    drafter = _ScriptedProvider([FatalProviderError("boom")])
    reviewer = _ScriptedProvider([])
    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    payload = run_session(_config(tmp_path), repo_root=Path(__file__).resolve().parents[3])

    assert payload["status"] == "failed_runtime"
    assert payload["ticket_draft"]["status"] == "skipped_not_completed"
    assert not (tmp_path / "ticket_draft.md").exists()


def test_final_summary_embeds_generated_ticket_draft(monkeypatch, tmp_path) -> None:
    drafter = _ScriptedProvider(
        [
            _Result("fake", None, "draft-1", 1, None),
            _Result("fake", None, "revision-1", 1, None),
            _Result("fake", None, "---\ntitle: \"Summary Ticket\"\n---\nBody\n", 1, None),
        ]
    )
    reviewer = _ScriptedProvider([_Result("fake", None, "review-1", 1, None)])
    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    run_session(_config(tmp_path), repo_root=Path(__file__).resolve().parents[3])

    summary = (tmp_path / "final_summary.md").read_text(encoding="utf-8")
    assert "## Generated Ticket Draft" in summary
    assert "title: \"Summary Ticket\"" in summary


def test_session_json_contains_ticket_draft_block(monkeypatch, tmp_path) -> None:
    drafter = _ScriptedProvider(
        [
            _Result("fake", None, "draft-1", 1, None),
            _Result("fake", None, "revision-1", 1, None),
            _Result("fake", None, "---\ntitle: \"Ticket JSON\"\n---\nBody\n", 1, None),
        ]
    )
    reviewer = _ScriptedProvider([_Result("fake", None, "review-1", 1, None)])
    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    run_session(_config(tmp_path), repo_root=Path(__file__).resolve().parents[3])

    payload = json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))
    assert set(payload["ticket_draft"].keys()) >= {"status", "provider", "model", "session_id", "path", "title", "writeback"}
