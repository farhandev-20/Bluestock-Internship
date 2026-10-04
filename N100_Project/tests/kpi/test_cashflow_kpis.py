"""
Unit tests for Cash Flow KPIs and Capital Allocation (Day 11).
Covers Free Cash Flow, CFO Quality Score categories, CapEx Intensity categories,
FCF Conversion Rate, and 8-pattern Capital Allocation classifier.
"""

import pytest
from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    classify_capital_allocation,
)


def test_free_cash_flow_normal_and_negative():
    # CFO = 1000, CFI = -400 -> FCF = 600
    assert free_cash_flow(1000.0, -400.0) == 600.0
    # CFO = 200, CFI = -500 -> FCF = -300 (negative allowed)
    assert free_cash_flow(200.0, -500.0) == -300.0


def test_cfo_quality_score_categories():
    # High Quality (> 1.0)
    cfo_high = [120.0, 150.0, 130.0, 140.0, 160.0]
    pat_high = [100.0, 100.0, 100.0, 100.0, 100.0]
    score_h, label_h = cfo_quality_score(cfo_high, pat_high)
    assert label_h == "High Quality"
    assert score_h > 1.0

    # Moderate (0.5 - 1.0)
    cfo_mod = [70.0, 80.0, 60.0, 90.0, 75.0]
    pat_mod = [100.0, 100.0, 100.0, 100.0, 100.0]
    score_m, label_m = cfo_quality_score(cfo_mod, pat_mod)
    assert label_m == "Moderate"
    assert 0.5 <= score_m <= 1.0

    # Accrual Risk (< 0.5)
    cfo_low = [30.0, 40.0, 20.0, 10.0, 35.0]
    pat_low = [100.0, 100.0, 100.0, 100.0, 100.0]
    score_l, label_l = cfo_quality_score(cfo_low, pat_low)
    assert label_l == "Accrual Risk"
    assert score_l < 0.5


def test_capex_intensity_categories():
    # Asset Light (< 3%)
    intensity_l, label_l = capex_intensity(-20.0, 1000.0)
    assert intensity_l == pytest.approx(2.0, abs=1e-3)
    assert label_l == "Asset Light"

    # Moderate (3% - 8%)
    intensity_m, label_m = capex_intensity(-50.0, 1000.0)
    assert intensity_m == pytest.approx(5.0, abs=1e-3)
    assert label_m == "Moderate"

    # Capital Intensive (> 8%)
    intensity_h, label_h = capex_intensity(-120.0, 1000.0)
    assert intensity_h == pytest.approx(12.0, abs=1e-3)
    assert label_h == "Capital Intensive"


def test_fcf_conversion_rate():
    # FCF = 300, Operating Profit = 600 -> 50.0%
    assert fcf_conversion_rate(300.0, 600.0) == pytest.approx(50.0, abs=1e-3)
    # Operating Profit = 0 -> returns None
    assert fcf_conversion_rate(300.0, 0.0) is None


def test_capital_allocation_8_patterns():
    # 1. (+, -, -) -> Reinvestor / Shareholder Returns
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(500.0, -200.0, -100.0)
    assert (s_cfo, s_cfi, s_cff) == ("+", "-", "-")
    assert label == "Reinvestor"

    # High CFO/PAT -> Shareholder Returns
    _, _, _, label_sr = classify_capital_allocation(500.0, -200.0, -100.0, cfo_pat_ratio=1.5)
    assert label_sr == "Shareholder Returns"

    # 2. (+, +, -) -> Liquidating Assets
    _, _, _, label_la = classify_capital_allocation(300.0, 100.0, -200.0)
    assert label_la == "Liquidating Assets"

    # 3. (-, +, +) -> Distress Signal
    _, _, _, label_ds = classify_capital_allocation(-100.0, 50.0, 150.0)
    assert label_ds == "Distress Signal"

    # 4. (-, -, +) -> Growth Funded by Debt
    _, _, _, label_gd = classify_capital_allocation(-100.0, -250.0, 400.0)
    assert label_gd == "Growth Funded by Debt"

    # 5. (+, +, +) -> Cash Accumulator
    _, _, _, label_ca = classify_capital_allocation(200.0, 100.0, 50.0)
    assert label_ca == "Cash Accumulator"

    # 6. (-, -, -) -> Pre-Revenue
    _, _, _, label_pr = classify_capital_allocation(-50.0, -100.0, -20.0)
    assert label_pr == "Pre-Revenue"

    # 7. (+, -, +) -> Mixed
    _, _, _, label_mx = classify_capital_allocation(200.0, -100.0, 50.0)
    assert label_mx == "Mixed"
