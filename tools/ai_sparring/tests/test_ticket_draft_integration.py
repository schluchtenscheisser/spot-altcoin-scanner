from pathlib import Path

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


def _cfg(out: Path) -> SessionConfig:
    return SessionConfig(
        prompt="hello",
        mode="ticket_review",
        rounds=1,
        drafter_provider="fake",
        drafter_model=None,
        reviewer_provider="fake",
        reviewer_model=None,
        context_paths=(),
        output_dir=out,
    )


def test_missing_ticket_template_fails_without_provider_call(monkeypatch, tmp_path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "docs/tickets").mkdir(parents=True)
    (repo_root / "docs").mkdir(exist_ok=True)
    (repo_root / "docs/AGENTS.md").write_text("# x\n", encoding="utf-8")
    (repo_root / "docs/code_map.md").write_text("# map\n", encoding="utf-8")
    (repo_root / "docs/canonical").mkdir(parents=True, exist_ok=True)
    (repo_root / "docs/canonical/ROADMAP.md").write_text("# roadmap\n", encoding="utf-8")
    (repo_root / "docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md").write_text("# x\n", encoding="utf-8")

    drafter = _ScriptedProvider(
        [
            ProviderResult("fake", None, "draft-1", 1, None),
            ProviderResult("fake", None, "revision-1", 1, None),
        ]
    )
    reviewer = _ScriptedProvider([ProviderResult("fake", None, "review-1", 1, None)])
    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    payload = run_session(_cfg(tmp_path / "out"), repo_root=repo_root)
    assert payload["status"] == "completed"
    assert payload["ticket_draft"]["status"] == "failed"
    assert drafter.calls == 2


def test_failed_ticket_generation_preserves_completed_session(monkeypatch, tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    drafter = _ScriptedProvider(
        [
            ProviderResult("fake", None, "draft-1", 1, None),
            ProviderResult("fake", None, "revision-1", 1, None),
            RuntimeError("ticket fail"),
        ]
    )
    reviewer = _ScriptedProvider([ProviderResult("fake", None, "review-1", 1, None)])
    calls = {"n": 0}

    def builder(name, *, model, api_key):
        calls["n"] += 1
        return drafter if calls["n"] == 1 else reviewer

    monkeypatch.setattr("tools.ai_sparring.session.build_provider", builder)
    payload = run_session(_cfg(tmp_path / "out2"), repo_root=repo_root)

    assert payload["status"] == "completed"
    assert payload["ticket_draft"]["status"] == "failed"
    assert payload["ticket_draft"]["path"] is None
