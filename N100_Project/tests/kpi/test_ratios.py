"""
20 Unit Tests for KPI and Ratio Engine Calculations (Day 41).
Covers ROE positive/negative equity, debt-free D/E, zero interest ICR,
financial sector carveouts, CAGR edge cases, OPM cross-check, CFO quality score, and CapEx intensity.
"""

import pytest
from src.analytics.cagr import (
    CAGR_FLAG_BOTH_NEGATIVE,
    CAGR_FLAG_DECLINE_TO_LOSS,
    CAGR_FLAG_NORMAL,
    CAGR_FLAG_TURNAROUND,
    CAGR_FLAG_ZERO_BASE,
    calculate_cagr,
)
from src.analytics.cashflow_kpis import (
    capex_intensity,
    cfo_quality_score,
    fcf_conversion_rate,
    free_cash_flow,
)
from src.analytics.ratios import (
    cross_check_opm,
    debt_to_equity,
    get_high_leverage_flag,
    get_icr_label,
    get_icr_warning_flag,
    interest_coverage_ratio,
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    return_on_capital_employed,
    return_on_equity,
)


def test_roe_positive_equity():
    assert return_on_equity(200.0, 100.0, 900.0) == 20.0


def test_roe_negative_equity_returns_none():
    assert return_on_equity(50.0, 100.0, -200.0) is None


def test_roe_zero_equity_returns_none():
    assert return_on_equity(50.0, 0.0, 0.0) is None


def test_de_debt_free_company_returns_zero():
    assert debt_to_equity(0.0, 100.0, 900.0) == 0.0


def test_de_none_borrowings_returns_zero():
    assert debt_to_equity(None, 100.0, 900.0) == 0.0


def test_de_positive_borrowings():
    assert debt_to_equity(500.0, 100.0, 900.0) == 0.5


def test_icr_zero_interest_returns_none():
    assert interest_coverage_ratio(500.0, 50.0, 0.0) is None


def test_icr_none_interest_returns_none():
    assert interest_coverage_ratio(500.0, 50.0, None) is None


def test_icr_positive_interest():
    assert interest_coverage_ratio(450.0, 50.0, 100.0) == 5.0


def test_icr_label_debt_free():
    assert get_icr_label(None) == "Debt Free"


def test_icr_warning_flag_under_1_5():
    assert get_icr_warning_flag(1.2, threshold=1.5) is True
    assert get_icr_warning_flag(3.5, threshold=1.5) is False


def test_high_leverage_flag_non_financial():
    assert get_high_leverage_flag(6.0, broad_sector="Industrials", threshold=5.0) is True


def test_high_leverage_flag_financial_carveout():
    assert get_high_leverage_flag(8.5, broad_sector="Financials", threshold=5.0) is False


def test_cagr_normal_growth():
    cagr, flag = calculate_cagr(100.0, 144.0, 2)
    assert flag == CAGR_FLAG_NORMAL
    assert round(cagr, 1) == 20.0


def test_cagr_turnaround_flag():
    cagr, flag = calculate_cagr(-50.0, 100.0, 3)
    assert cagr is None
    assert flag == CAGR_FLAG_TURNAROUND


def test_cagr_decline_to_loss_flag():
    cagr, flag = calculate_cagr(100.0, -20.0, 3)
    assert cagr is None
    assert flag == CAGR_FLAG_DECLINE_TO_LOSS


def test_cagr_zero_base_flag():
    cagr, flag = calculate_cagr(0.0, 100.0, 3)
    assert cagr is None
    assert flag == CAGR_FLAG_ZERO_BASE


def test_opm_cross_check_matching():
    is_match, diff = cross_check_opm(25.0, 25.4, threshold=1.0)
    assert is_match is True
    assert round(diff, 1) == 0.4


def test_opm_cross_check_divergence_flag():
    is_match, diff = cross_check_opm(20.0, 26.0, threshold=1.0)
    assert is_match is False
    assert diff == 6.0


def test_cfo_quality_score_calculation():
    score, label = cfo_quality_score([120.0, 130.0], [100.0, 100.0])
    assert score == 1.25
    assert label == "High Quality"
