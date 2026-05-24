from __future__ import annotations

from pathlib import Path
import subprocess


def test_run_historical_replay_workflow_packages_tarball_and_uses_safe_name() -> None:
    text = Path('.github/workflows/run-historical-replay.yml').read_text(encoding='utf-8')

    assert 'Package replay outputs' in text
    assert 'tar -czf "$TAR_NAME" evaluation/replay/runs/' in text
    assert 'replay-outputs-${{ steps.plan.outputs.replay_id_safe || github.run_id }}.tar.gz' in text
    assert '${{ steps.package_outputs.outputs.packaged_artifact }}' in text
    assert "REPLAY_ID_SAFE=$(printf '%s' \"$REPLAY_ID\" | tr '\":<>|*?\\r\\n\\\\/' '-')" in text


def test_replay_id_sanitization_no_trailing_hyphen_and_colon_mapping() -> None:
    safe = subprocess.check_output(
        ["bash", "-lc", "REPLAY_ID='2026-05-24T20-51-21Z'; printf '%s' \"$REPLAY_ID\" | tr '\":<>|*?\\r\\n\\\\/' '-'"],
        text=True,
    ).strip()
    assert safe == "2026-05-24T20-51-21Z"

    legacy = subprocess.check_output(
        ["bash", "-lc", "REPLAY_ID='2026-05-24T20:51:21Z'; printf '%s' \"$REPLAY_ID\" | tr '\":<>|*?\\r\\n\\\\/' '-'"],
        text=True,
    ).strip()
    assert legacy == "2026-05-24T20-51-21Z"
