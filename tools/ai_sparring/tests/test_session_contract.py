import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_cli(*args: str):
    cmd = [sys.executable, "-m", "tools.ai_sparring.cli", *args]
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def test_fake_provider_model_persists_as_null(tmp_path) -> None:
    result = run_cli("--prompt", "x", "--output-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))
    assert payload["participants"]["drafter"]["model"] is None
    assert payload["participants"]["reviewer"]["model"] is None


def test_modes_resolve_distinct_role_prompt_ids(tmp_path) -> None:
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    result_a = run_cli("--prompt", "x", "--mode", "ticket_review", "--output-dir", str(out_a))
    result_b = run_cli("--prompt", "x", "--mode", "implementation_planning", "--output-dir", str(out_b))
    assert result_a.returncode == 0, result_a.stderr
    assert result_b.returncode == 0, result_b.stderr
    payload_a = json.loads((out_a / "session.json").read_text(encoding="utf-8"))
    payload_b = json.loads((out_b / "session.json").read_text(encoding="utf-8"))
    assert payload_a["resolved_prompts"] != payload_b["resolved_prompts"]
    assert [s["path"] for s in payload_a["context_sources"]] == [s["path"] for s in payload_b["context_sources"]]
    assert payload_a["session_version"] == payload_b["session_version"] == 2
