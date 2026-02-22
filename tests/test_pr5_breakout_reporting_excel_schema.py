from pathlib import Path

from openpyxl import load_workbook

from scanner.pipeline.excel_output import ExcelReportGenerator
from scanner.pipeline.output import ReportGenerator


def _breakout_rows():
    return [
        {"symbol": "AAAUSDT", "setup_id": "breakout_immediate_1_5d", "score": 80.0, "final_score": 80.0},
        {"symbol": "BBBUSDT", "setup_id": "breakout_retest_1_5d", "score": 82.0, "final_score": 82.0},
    ]


def test_pr5_markdown_contains_immediate_and_retest_sections() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 10}})

    md = generator.generate_markdown_report([], _breakout_rows(), [], [], "2026-02-22")

    assert "## 📈 Top 20 Immediate (1–5D)" in md
    assert "## 📈 Top 20 Retest (1–5D)" in md


def test_pr5_json_contains_breakout_setup_lists() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 10}})

    report = generator.generate_json_report([], _breakout_rows(), [], [], "2026-02-22")

    assert report["setups"]["breakout_immediate_1_5d"][0]["setup_id"] == "breakout_immediate_1_5d"
    assert report["setups"]["breakout_retest_1_5d"][0]["setup_id"] == "breakout_retest_1_5d"


def test_pr5_excel_has_retest_sheet(tmp_path: Path) -> None:
    generator = ExcelReportGenerator({"output": {"reports_dir": str(tmp_path)}})

    excel_path = generator.generate_excel_report([], _breakout_rows(), [], [], "2026-02-22")
    wb = load_workbook(excel_path)

    assert "Breakout Immediate 1-5D" in wb.sheetnames
    assert "Breakout Retest 1-5D" in wb.sheetnames
