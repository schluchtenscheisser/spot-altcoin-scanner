from pathlib import Path

from tools.ai_sparring.errors import FatalProviderError
from tools.ai_sparring.session import SessionConfig, run_session


class _ScriptedProvider:
    def __init__(self, scripted):
        self.scripted = list(scripted)

    def generate(self, *, input_text: str):
        item = self.scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _Result:
    def __init__(self, provider, model, text, attempts_used=1, request_id=None):
        self.provider = provider
        self.model = model
        self.text = text
        self.attempts_used = attempts_used
        self.request_id = request_id


def _config(tmp_path: Path) -> SessionConfig:
    return SessionConfig(
        prompt="review this design",
        mode="ticket_review",
        rounds=2,
        drafter_provider="fake",
        drafter_model=None,
        reviewer_provider="fake",
        reviewer_model=None,
        context_paths=(),
        output_dir=tmp_path,
    )


def test_round_protocol_is_draft_review_revision(monkeypatch, tmp_path) -> None:
    drafter = _ScriptedProvider([
        _Result("fake", None, "draft-1"),
        _Result("fake", None, "revision-1"),
        _Result("fake", None, "draft-2"),
        _Result("fake", None, "revision-2"),
    ])
    reviewer = _ScriptedProvider([
        _Result("fake", None, "review-1"),
        _Result("fake", None, "review-2"),
    ])

    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    payload = run_session(_config(tmp_path), repo_root=Path(__file__).resolve().parents[3])
    assert payload["status"] == "completed"
    assert all(set(r.keys()) >= {"draft", "review", "revision", "delta_summary"} for r in payload["rounds"])
    assert payload["resolved_prompts"] == {
        "drafter": "drafter.ticket_review",
        "reviewer": "reviewer.ticket_review",
    }


def test_draft_round_two_sees_prior_review_and_revision(monkeypatch, tmp_path) -> None:
    captured_inputs: list[str] = []

    class _CapturingProvider(_ScriptedProvider):
        def generate(self, *, input_text: str):
            captured_inputs.append(input_text)
            return super().generate(input_text=input_text)

    drafter = _CapturingProvider(
        [
            _Result("fake", None, "draft-1"),
            _Result("fake", None, "revision-1"),
            _Result("fake", None, "draft-2"),
            _Result("fake", None, "revision-2"),
        ]
    )
    reviewer = _CapturingProvider(
        [
            _Result("fake", None, "review-1"),
            _Result("fake", None, "review-2"),
        ]
    )
    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    run_session(_config(tmp_path), repo_root=Path(__file__).resolve().parents[3])
    draft_2_input = captured_inputs[3]
    assert "previous_review:\nreview-1" in draft_2_input
    assert "previous_revision:\nrevision-1" in draft_2_input


def test_failed_runtime_vs_failed_partial_statuses(monkeypatch, tmp_path) -> None:
    # fail before first successful step
    drafter_a = _ScriptedProvider([FatalProviderError("boom")])
    reviewer_a = _ScriptedProvider([])
    calls_a = {"n": 0}

    def builder_a(name, *, model, api_key):
        calls_a["n"] += 1
        return drafter_a if calls_a["n"] == 1 else reviewer_a

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder_a)
    payload_a = run_session(_config(tmp_path / "a"), repo_root=Path(__file__).resolve().parents[3])
    assert payload_a["status"] == "failed_runtime"

    # fail after one completed round
    drafter_b = _ScriptedProvider([
        _Result("fake", None, "draft-1"),
        _Result("fake", None, "revision-1"),
        FatalProviderError("late"),
    ])
    reviewer_b = _ScriptedProvider([
        _Result("fake", None, "review-1"),
        _Result("fake", None, "review-2"),
    ])
    calls_b = {"n": 0}

    def builder_b(name, *, model, api_key):
        calls_b["n"] += 1
        return drafter_b if calls_b["n"] == 1 else reviewer_b

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder_b)
    payload_b = run_session(_config(tmp_path / "b"), repo_root=Path(__file__).resolve().parents[3])
    assert payload_b["status"] == "failed_partial"
    assert payload_b["rounds_completed"] == 1
