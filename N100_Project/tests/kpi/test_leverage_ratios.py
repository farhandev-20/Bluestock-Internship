"""
Unit tests for Leverage and Efficiency Ratios (Day 09).
Covers D/E debt-free returns 0, ICR interest=0 returns None and 'Debt Free' label,
high leverage flag, and bank sector carve-outs.
"""

import pytest
from src.analytics.ratios import (
    debt_to_equity,
    get_high_leverage_flag,
    interest_coverage_ratio,
    get_icr_label,
    get_icr_warning_flag,
    net_debt,
    asset_turnover,
)


def test_debt_to_equity_normal():
    # Borrowings = 500, Equity = 200, Reserves = 800 (Total Equity = 1000) -> D/E = 0.5
    result = debt_to_equity(500.0, 200.0, 800.0)
    assert result == pytest.approx(0.5, abs=1e-3)


def test_debt_to_equity_debt_free_returns_zero():
    # Borrowings = 0 -> returns 0.0 (not None)
    result = debt_to_equity(0.0, 100.0, 400.0)
    assert result == 0.0
    assert isinstance(result, float)


def test_debt_to_equity_negative_equity_returns_none():
    # Negative equity -> None
    assert debt_to_equity(500.0, 50.0, -100.0) is None


def test_high_leverage_flag_non_financials():
    # D/E = 6.0 (> 5.0) for Industrials -> Flag is True
    assert get_high_leverage_flag(6.0, broad_sector="Capital Goods") is True
    # D/E = 3.0 (<= 5.0) -> Flag is False
    assert get_high_leverage_flag(3.0, broad_sector="Capital Goods") is False


def test_high_leverage_flag_financials_carve_out():
    # D/E = 7.5 (> 5.0) for Financials (Banks / NBFCs) -> Flag is False (Carve-out applied)
    assert get_high_leverage_flag(7.5, broad_sector="Financials") is False
    assert get_high_leverage_flag(12.0, broad_sector="financials") is False


def test_interest_coverage_normal():
    # Operating Profit = 400, Other Income = 50, Interest = 50 -> EBIT = 450 -> ICR = 9.0
    result = interest_coverage_ratio(400.0, 50.0, 50.0)
    assert result == pytest.approx(9.0, abs=1e-3)


def test_interest_coverage_interest_zero_returns_none():
    # Debt-free company (Interest = 0) -> ICR returns None
    assert interest_coverage_ratio(500.0, 50.0, 0.0) is None
    assert interest_coverage_ratio(500.0, 50.0, None) is None


def test_icr_label_and_warning_flag():
    # For None ICR -> label is 'Debt Free', warning flag is False
    assert get_icr_label(None) == "Debt Free"
    assert get_icr_warning_flag(None) is False

    # For ICR = 1.2 (< 1.5) -> warning flag is True
    assert get_icr_label(1.2) == "1.20x"
    assert get_icr_warning_flag(1.2) is True

    # For ICR = 5.0 (>= 1.5) -> warning flag is False
    assert get_icr_warning_flag(5.0) is False


def test_net_debt_and_asset_turnover():
    # Net Debt = Borrowings (300) - Investments (100) = 200
    assert net_debt(300.0, 100.0) == 200.0
    assert net_debt(0.0, 50.0) == -50.0

    # Asset Turnover = Sales (1500) / Total Assets (3000) = 0.5
    assert asset_turnover(1500.0, 3000.0) == pytest.approx(0.5, abs=1e-3)
    assert asset_turnover(1500.0, 0.0) is None
