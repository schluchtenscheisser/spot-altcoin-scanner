from __future__ import annotations

from pathlib import Path


def test_run_historical_replay_workflow_packages_tarball_and_uses_safe_name() -> None:
    text = Path('.github/workflows/run-historical-replay.yml').read_text(encoding='utf-8')

    assert 'Package replay outputs' in text
    assert 'tar -czf "$TAR_NAME" evaluation/replay/runs/' in text
    assert 'replay-outputs-${{ steps.plan.outputs.replay_id_safe || github.run_id }}.tar.gz' in text
    assert '${{ steps.package_outputs.outputs.packaged_artifact }}' in text
    assert "tr ':\\\"<>|*?\\\\/\\\\r\\\\n' '-'" in text
