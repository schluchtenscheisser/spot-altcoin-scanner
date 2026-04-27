from __future__ import annotations

from pathlib import Path


def test_shadow_live_workflow_exists_and_has_required_contract() -> None:
    path = Path('.github/workflows/independence-shadow-live.yml')
    text = path.read_text(encoding='utf-8')

    assert 'workflow_dispatch:' in text
    assert 'schedule:' in text
    assert 'evaluation/exports/**' in text
    assert 'evaluation/replay/**' in text
    assert 'FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"' in text
    assert 'ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION' not in text
