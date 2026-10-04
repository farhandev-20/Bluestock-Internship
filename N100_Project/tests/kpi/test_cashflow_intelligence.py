"""
Unit and Integration Tests for Cash Flow Intelligence (Days 31 & 32).
"""

from pathlib import Path
import pandas as pd
import pytest
from src.analytics.cashflow_kpis import (
    capex_intensity,
    cfo_quality_score,
    classify_capital_allocation,
    fcf_conversion_rate,
    free_cash_flow,
    generate_cashflow_intelligence,
)


def test_cashflow_kpis_core_logic():
    # FCF
    assert free_cash_flow(100.0, -40.0) == 60.0
    assert free_cash_flow(50.0, 10.0) == 60.0
    assert free_cash_flow(None, None) is None

    # CFO Quality
    score, label = cfo_quality_score([120.0, 150.0], [100.0, 100.0])
    assert score is not None and score > 1.0
    assert label == "High Quality"

    score_low, label_low = cfo_quality_score([30.0], [100.0])
    assert label_low == "Accrual Risk"

    # CapEx Intensity
    int_pct, lab = capex_intensity(-20.0, 1000.0)
    assert lab == "Asset Light"

    int_high, lab_high = capex_intensity(-100.0, 1000.0)
    assert lab_high == "Capital Intensive"

    # FCF conversion
    conv = fcf_conversion_rate(80.0, 100.0)
    assert conv == 80.0


def test_classify_capital_allocation_patterns():
    # (+, -, -)
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(100, -50, -30)
    assert label in ["Reinvestor", "Shareholder Returns"]

    # (+, +, -)
    _, _, _, label_liq = classify_capital_allocation(100, 20, -30)
    assert label_liq == "Liquidating Assets"

    # (-, +, +)
    _, _, _, label_distress = classify_capital_allocation(-50, 20, 30)
    assert label_distress == "Distress Signal"


def test_generate_cashflow_intelligence_export(tmp_path):
    intel_xlsx = tmp_path / "cashflow_intelligence.xlsx"
    distress_csv = tmp_path / "distress_alerts.csv"
    pattern_csv = tmp_path / "pattern_changes.csv"

    intel_df, distress_df, pattern_df = generate_cashflow_intelligence(
        output_excel=intel_xlsx,
        output_distress=distress_csv,
        output_pattern_changes=pattern_csv,
    )

    assert not intel_df.empty
    assert len(intel_df) == 92
    assert "cfo_quality_score" in intel_df.columns
    assert "capex_intensity_pct" in intel_df.columns
    assert "distress_flag" in intel_df.columns
    assert "deleveraging_flag" in intel_df.columns
    assert "capital_allocation" in intel_df.columns

    assert intel_xlsx.exists()
    assert distress_csv.exists()
    assert pattern_csv.exists()
