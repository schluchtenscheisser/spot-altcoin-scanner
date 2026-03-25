import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def run_cli(*args: str):
    cmd = [sys.executable, "-m", "tools.ai_sparring.cli", *args]
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def test_cli_defaults_use_fake_mode_and_rounds(tmp_path) -> None:
    result = run_cli(
        "--prompt",
        "review this design",
        "--output-dir",
        str(tmp_path),
    )
    assert result.returncode == 0, result.stderr

    files = sorted(path.name for path in tmp_path.iterdir())
    assert files == ["final_summary.md", "session.json", "session.md"]

    payload = json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))
    assert payload["provider"] == "fake"
    assert payload["mode"] == "ticket_review"
    assert payload["rounds"] == 1
    assert payload["context_sources"] == [
        "docs/AGENTS.md",
        "docs/code_map.md",
        "docs/canonical/ROADMAP.md",
    ]


def test_cli_rejects_invalid_rounds(tmp_path) -> None:
    result = run_cli(
        "--prompt",
        "review this design",
        "--rounds",
        "4",
        "--output-dir",
        str(tmp_path),
    )
    assert result.returncode != 0
    assert "Invalid rounds" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_preflight_failure_writes_no_output_files(tmp_path) -> None:
    roadmap = REPO_ROOT / "docs/canonical/ROADMAP.md"
    backup = REPO_ROOT / "docs/canonical/ROADMAP.md.bak_test"
    roadmap.rename(backup)
    try:
        result = run_cli(
            "--prompt",
            "review this design",
            "--output-dir",
            str(tmp_path),
        )
        assert result.returncode != 0
        assert "Missing required context source" in result.stderr
        assert list(tmp_path.iterdir()) == []
    finally:
        backup.rename(roadmap)


def test_fake_provider_output_is_deterministic(tmp_path) -> None:
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"

    first = run_cli(
        "--prompt",
        "review this design",
        "--provider",
        "fake",
        "--mode",
        "ticket_review",
        "--rounds",
        "2",
        "--output-dir",
        str(run_a),
    )
    second = run_cli(
        "--prompt",
        "review this design",
        "--provider",
        "fake",
        "--mode",
        "ticket_review",
        "--rounds",
        "2",
        "--output-dir",
        str(run_b),
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert (run_a / "session.json").read_text(encoding="utf-8") == (
        run_b / "session.json"
    ).read_text(encoding="utf-8")


def test_cli_integration_writes_content_shape(tmp_path) -> None:
    result = run_cli(
        "--prompt",
        "review this design",
        "--provider",
        "fake",
        "--mode",
        "roadmap_review",
        "--rounds",
        "1",
        "--output-dir",
        str(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))
    assert payload["status"] == "success"
    assert isinstance(payload["messages"], list)
    assert payload["messages"]
