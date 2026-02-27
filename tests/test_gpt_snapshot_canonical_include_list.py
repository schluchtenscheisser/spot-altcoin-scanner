from pathlib import Path


def test_gpt_snapshot_includes_all_canonical_scoring_contracts() -> None:
    workflow = Path('.github/workflows/generate-gpt-snapshot.yml').read_text(encoding='utf-8')

    required_docs = [
        'docs/canonical/SCORING/SETUP_VALIDITY_RULES.md',
        'docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md',
        'docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md',
        'docs/canonical/SCORING/DISCOVERY_TAG.md',
    ]

    for doc in required_docs:
        assert f'"{doc}"' in workflow
