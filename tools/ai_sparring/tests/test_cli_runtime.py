import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_cli(*args: str, env: dict[str, str] | None = None):
    cmd = [sys.executable, "-m", "tools.ai_sparring.cli", *args]
    merged_env = None
    if env is not None:
        merged_env = dict(**env)
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=merged_env)


def test_cli_runtime_defaults_keep_fake_providers(tmp_path) -> None:
    result = run_cli("--prompt", "review this design", "--output-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))
    assert payload["participants"]["drafter"]["provider"] == "fake"
    assert payload["participants"]["reviewer"]["provider"] == "fake"
    assert payload["participants"]["drafter"]["model"] is None


def test_missing_api_key_fails_preflight(tmp_path) -> None:
    env = {}
    result = run_cli(
        "--prompt",
        "review this design",
        "--drafter-provider",
        "openai",
        "--drafter-model",
        "gpt-test",
        "--output-dir",
        str(tmp_path),
        env=env,
    )
    assert result.returncode != 0
    assert "OPENAI_API_KEY" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_missing_model_id_fails_preflight(tmp_path) -> None:
    env = {"OPENAI_API_KEY": "x"}
    result = run_cli(
        "--prompt",
        "review this design",
        "--drafter-provider",
        "openai",
        "--output-dir",
        str(tmp_path),
        env=env,
    )
    assert result.returncode != 0
    assert "Missing required model id" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_invalid_context_path_fails_preflight(tmp_path) -> None:
    result = run_cli(
        "--prompt",
        "review this design",
        "--context-path",
        "../outside.txt",
        "--output-dir",
        str(tmp_path),
    )
    assert result.returncode != 0
    assert "Invalid context path" in result.stderr
    assert list(tmp_path.iterdir()) == []
