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
