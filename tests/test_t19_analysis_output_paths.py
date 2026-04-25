from __future__ import annotations

from pathlib import Path


def test_analysis_scripts_do_not_default_to_reports_analysis() -> None:
    targets = [
        "scripts/analyze_chased_entries.py",
        "scripts/analyze_chased_entries_v2.py",
        "scripts/counterfactual_chased_thresholds_v2.py",
        "scripts/counterfactual_chased_thresholds_v3.py",
        "scripts/counterfactual_chased_thresholds_v4.py",
        "scripts/diagnose_risk_reward.py",
        "scripts/diagnose_risk_reward_1.py",
        "scripts/post_risk_unlock_audit.py",
        "scripts/top20_formation_audit.py",
    ]
    for rel in targets:
        content = Path(rel).read_text(encoding="utf-8")
        assert "default: reports/analysis" not in content
        assert 'default="reports/analysis"' not in content
        assert 'Path("reports/analysis")' not in content
