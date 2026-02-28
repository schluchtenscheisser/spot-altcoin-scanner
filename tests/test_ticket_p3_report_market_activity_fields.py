from pathlib import Path

from openpyxl import load_workbook

from scanner.pipeline.excel_output import ExcelReportGenerator
from scanner.pipeline.output import ReportGenerator


def _row(symbol: str, **kwargs):
    row = {
        "symbol": symbol,
        "coin_name": symbol.replace("USDT", ""),
        "setup_id": "breakout_immediate_1_5d",
        "score": 80.0,
    }
    row.update(kwargs)
    return row


def test_json_report_contains_market_activity_fields_with_values_and_nulls() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})
    rows = [
        _row("AAAUSDT", global_volume_24h_usd=100_000_000, turnover_24h=0.25, mexc_share_24h=0.05),
        _row("BBBUSDT", global_volume_24h_usd=-1, turnover_24h=float("nan"), mexc_share_24h="abc"),
    ]

    report = generator.generate_json_report(rows, [], [], [], "2026-02-28")
    first = report["setups"]["reversals"][0]
    second = report["setups"]["reversals"][1]

    assert first["global_volume_24h_usd"] == 100_000_000.0
    assert first["turnover_24h"] == 0.25
    assert first["mexc_share_24h"] == 0.05

    assert second["global_volume_24h_usd"] is None
    assert second["turnover_24h"] is None
    assert second["mexc_share_24h"] is None


def test_markdown_report_contains_market_activity_line() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    md = generator.generate_markdown_report(
        [_row("AAAUSDT", global_volume_24h_usd=10_000, turnover_24h=0.1, mexc_share_24h=0.02)], [], [], [], "2026-02-28"
    )

    assert "**Market Activity:**" in md
    assert "global_volume_24h_usd=10000.0" in md


def test_excel_report_contains_market_activity_columns_and_empty_cells_for_missing(tmp_path: Path) -> None:
    generator = ExcelReportGenerator({"output": {"reports_dir": str(tmp_path), "top_n_per_setup": 5}})
    rows = [
        _row("AAAUSDT", global_volume_24h_usd=500_000_000, turnover_24h=0.2, mexc_share_24h=0.03),
        _row("BBBUSDT", global_volume_24h_usd=-1, turnover_24h=float("nan"), mexc_share_24h="abc"),
    ]

    excel_path = generator.generate_excel_report(rows, [], [], rows, "2026-02-28")
    wb = load_workbook(excel_path)

    ws_setup = wb["Reversal Setups"]
    headers = [ws_setup.cell(row=1, column=i).value for i in range(1, 18)]
    assert "Global Volume 24h (USD)" in headers
    assert "Turnover 24h" in headers
    assert "MEXC Share 24h" in headers
    assert ws_setup.cell(row=2, column=13).value == 500_000_000
    assert ws_setup.cell(row=3, column=13).value is None

    ws_global = wb["Global Top 20"]
    global_headers = [ws_global.cell(row=1, column=i).value for i in range(1, 15)]
    assert global_headers[10] == "Global Volume 24h (USD)"
    assert global_headers[11] == "Turnover 24h"
    assert global_headers[12] == "MEXC Share 24h"
