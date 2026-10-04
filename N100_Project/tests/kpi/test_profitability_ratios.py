"""
Unit tests for Profitability Ratios (Day 08).
Covers normal cases, zero denominators, negative equity, and OPM cross-checks.
"""

import pytest
from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    cross_check_opm,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
)


def test_net_profit_margin_normal():
    # Net Profit = 150, Sales = 1000 -> NPM = 15.0%
    result = net_profit_margin(150.0, 1000.0)
    assert result == pytest.approx(15.0, abs=1e-3)


def test_net_profit_margin_zero_sales():
    # Sales = 0 -> returns None
    assert net_profit_margin(100.0, 0.0) is None
    assert net_profit_margin(100.0, -50.0) is None
    assert net_profit_margin(None, 1000.0) is None


def test_operating_profit_margin_normal():
    # Operating Profit = 250, Sales = 1000 -> OPM = 25.0%
    result = operating_profit_margin(250.0, 1000.0)
    assert result == pytest.approx(25.0, abs=1e-3)


def test_operating_profit_margin_zero_sales():
    assert operating_profit_margin(200.0, 0.0) is None
    assert operating_profit_margin(200.0, None) is None


def test_opm_cross_check_matching():
    computed = 21.45
    source = 21.50
    is_match, diff = cross_check_opm(computed, source, threshold=1.0)
    assert is_match is True
    assert diff == pytest.approx(0.05, abs=1e-3)


def test_opm_cross_check_mismatch_triggers_log():
    computed = 25.0
    source = 21.0
    is_match, diff = cross_check_opm(computed, source, threshold=1.0)
    assert is_match is False
    assert diff == pytest.approx(4.0, abs=1e-3)


def test_return_on_equity_normal():
    # Net Profit = 200, Equity = 100, Reserves = 900 -> Total Equity = 1000 -> ROE = 20.0%
    result = return_on_equity(200.0, 100.0, 900.0)
    assert result == pytest.approx(20.0, abs=1e-3)


def test_return_on_equity_negative_equity_returns_none():
    # Equity = 50, Reserves = -200 -> Total Equity = -150 <= 0 -> returns None
    result = return_on_equity(50.0, 50.0, -200.0)
    assert result is None
    assert return_on_equity(50.0, 0.0, 0.0) is None


def test_return_on_assets_normal_and_zero_denom():
    # Normal: Net Profit = 100, Assets = 1000 -> ROA = 10.0%
    assert return_on_assets(100.0, 1000.0) == pytest.approx(10.0, abs=1e-3)
    # Zero / Negative assets -> returns None
    assert return_on_assets(100.0, 0.0) is None
    assert return_on_assets(100.0, -100.0) is None


def test_return_on_capital_employed_normal_and_zero_denom():
    # EBIT = 300, Equity = 200, Reserves = 800, Borrowings = 500 -> Cap Employed = 1500 -> ROCE = 20.0%
    roce = return_on_capital_employed(300.0, 200.0, 800.0, 500.0)
    assert roce == pytest.approx(20.0, abs=1e-3)

    # Zero or negative capital employed
    assert return_on_capital_employed(100.0, -50.0, -100.0, 0.0) is None
