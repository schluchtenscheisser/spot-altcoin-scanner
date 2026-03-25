import json

from tools.ai_sparring.output_writer import write_session_artifacts


def test_output_writer_creates_expected_files(tmp_path) -> None:
    payload = {
        "provider": "fake",
        "mode": "ticket_review",
        "rounds": 1,
        "prompt": "review this design",
        "context_sources": [
            "docs/AGENTS.md",
            "docs/code_map.md",
            "docs/canonical/ROADMAP.md",
        ],
        "status": "success",
        "messages": [{"role": "assistant", "content": "synthetic"}],
    }
    write_session_artifacts(tmp_path, payload)

    files = sorted(path.name for path in tmp_path.iterdir())
    assert files == ["final_summary.md", "session.json", "session.md"]

    saved = json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))
    assert saved["provider"] == "fake"
    assert saved["status"] == "success"
