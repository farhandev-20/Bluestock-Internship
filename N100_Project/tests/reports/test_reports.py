"""
Unit and Integration Tests for PDF Reports Generation (Days 33, 34, 35).
"""

from pathlib import Path
import pytest
from src.reports.portfolio_summary import generate_portfolio_summary_pdf, get_trend_indicator
from src.reports.sector_report import generate_all_sector_reports, sanitize_filename
from src.reports.tearsheet import create_company_tearsheet, generate_all_tearsheets


def test_sanitize_filename():
    assert sanitize_filename("Information Technology") == "Information_Technology"
    assert sanitize_filename("Power & Utilities") == "Power_Utilities"
    assert sanitize_filename("Oil / Gas & Petrochemicals") == "Oil_Gas_Petrochemicals"


def test_get_trend_indicator():
    # Improved normal
    trend, color = get_trend_indicator(120.0, 100.0, is_inverse=False)
    assert "Improved" in trend
    assert color == "#10B981"

    # Declined normal
    trend, color = get_trend_indicator(80.0, 100.0, is_inverse=False)
    assert "Declined" in trend
    assert color == "#EF4444"

    # Flat
    trend, color = get_trend_indicator(100.5, 100.0, is_inverse=False)
    assert "Flat" in trend
    assert color == "#64748B"

    # Inverse (Debt / Equity)
    trend, color = get_trend_indicator(0.5, 1.2, is_inverse=True)
    assert "Improved" in trend
    assert color == "#10B981"


def test_single_tearsheet_generation(tmp_path):
    """Tests single company tearsheet PDF generation and file size."""
    pdf_out = tmp_path / "TCS_tearsheet.pdf"
    ok = create_company_tearsheet("TCS", pdf_out)
    assert ok is True
    assert pdf_out.exists()
    assert pdf_out.stat().st_size >= 30 * 1024  # At least 30 KB


def test_sector_report_generation(tmp_path):
    """Tests batch sector reports generation."""
    res = generate_all_sector_reports(output_dir=tmp_path)
    assert res["total_sectors"] >= 10
    generated = list(tmp_path.glob("*.pdf"))
    assert len(generated) >= 10
    for pdf in generated:
        assert pdf.stat().st_size > 1024  # Valid PDF size


def test_portfolio_summary_generation(tmp_path):
    """Tests multi-page portfolio summary PDF generation."""
    out_pdf = tmp_path / "portfolio_summary.pdf"
    res_path = generate_portfolio_summary_pdf(output_pdf_path=out_pdf)
    assert res_path.exists()
    assert res_path.stat().st_size >= 50 * 1024
