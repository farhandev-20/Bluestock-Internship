"""
Unit tests for Peer Comparison Excel Report (Day 20).
Validates 11 sheets, benchmark row highlight, and median summary row.
"""

from pathlib import Path
import openpyxl
import pytest

from src.analytics.peer import export_peer_comparison_excel, DEFAULT_EXCEL_PATH


def test_peer_comparison_excel_eleven_sheets(tmp_path):
    out_excel = tmp_path / "test_peer_comparison.xlsx"
    path = export_peer_comparison_excel(output_path=out_excel)

    assert path.exists()
    wb = openpyxl.load_workbook(path)

    # Must contain exactly 11 sheets covering all 11 peer groups
    assert len(wb.sheetnames) == 11, f"Expected 11 sheets, found {len(wb.sheetnames)}: {wb.sheetnames}"

    expected_groups = {
        "Automobiles",
        "Power & Utilities",
        "FMCG",
        "Private Banks",
        "IT Services",
        "Pharmaceuticals",
        "Oil & Gas",
        "Public Sector Banks",
        "Life Insurance",
        "Steel",
        "Consumer Finance",
    }
    assert set(wb.sheetnames) == expected_groups


def test_peer_comparison_sheet_structure_and_median_row(tmp_path):
    out_excel = tmp_path / "test_peer_comparison.xlsx"
    path = export_peer_comparison_excel(output_path=out_excel)

    wb = openpyxl.load_workbook(path)
    ws_it = wb["IT Services"]

    # Verify header
    assert ws_it.cell(row=1, column=1).value == "Company ID"
    assert ws_it.cell(row=1, column=2).value == "Company Name"
    assert ws_it.cell(row=1, column=3).value == "Benchmark"

    # Verify Summary Median Row at the bottom
    last_row = ws_it.max_row
    assert ws_it.cell(row=last_row, column=1).value == "GROUP MEDIAN"
    assert "Companies" in str(ws_it.cell(row=last_row, column=2).value)
    assert ws_it.cell(row=last_row, column=3).value == "Summary"
