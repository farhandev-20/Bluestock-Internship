"""
Unit tests for CAGR Engine (Day 10).
Covers 3-yr, 5-yr, 10-yr windows and all 6 edge cases:
1. Normal (Positive + Positive)
2. Decline to Loss (Positive + Negative)
3. Turnaround (Negative + Positive)
4. Both Negative (Negative + Negative)
5. Zero Base (Start = 0)
6. Insufficient Data (< n years or missing)
"""

import pytest
from src.analytics.cagr import (
    calculate_cagr,
    compute_series_cagr,
    CAGR_FLAG_NORMAL,
    CAGR_FLAG_DECLINE_TO_LOSS,
    CAGR_FLAG_TURNAROUND,
    CAGR_FLAG_BOTH_NEGATIVE,
    CAGR_FLAG_ZERO_BASE,
    CAGR_FLAG_INSUFFICIENT,
)


def test_cagr_normal_positive_growth():
    # 100 to 200 over 5 years: (2^(1/5) - 1) * 100 = 14.8698%
    cagr, flag = calculate_cagr(100.0, 200.0, 5)
    assert flag == CAGR_FLAG_NORMAL
    assert cagr == pytest.approx(14.87, abs=0.01)


def test_cagr_3yr_5yr_10yr_windows():
    # 3-year window: 1000 to 1331 over 3 yrs = 10.0%
    cagr_3, flag_3 = calculate_cagr(1000.0, 1331.0, 3)
    assert flag_3 == CAGR_FLAG_NORMAL
    assert cagr_3 == pytest.approx(10.0, abs=1e-2)

    # 10-year window: 100 to 619.17 over 10 yrs = 20.0%
    cagr_10, flag_10 = calculate_cagr(100.0, 619.17364, 10)
    assert flag_10 == CAGR_FLAG_NORMAL
    assert cagr_10 == pytest.approx(20.0, abs=1e-2)


def test_cagr_edge_case_decline_to_loss():
    # Positive start (100) -> Negative end (-50) over 5 years
    cagr, flag = calculate_cagr(100.0, -50.0, 5)
    assert cagr is None
    assert flag == CAGR_FLAG_DECLINE_TO_LOSS


def test_cagr_edge_case_turnaround():
    # Negative start (-50) -> Positive end (100) over 5 years
    cagr, flag = calculate_cagr(-50.0, 100.0, 5)
    assert cagr is None
    assert flag == CAGR_FLAG_TURNAROUND


def test_cagr_edge_case_both_negative():
    # Negative start (-100) -> Negative end (-50) over 5 years
    cagr, flag = calculate_cagr(-100.0, -50.0, 5)
    assert cagr is None
    assert flag == CAGR_FLAG_BOTH_NEGATIVE


def test_cagr_edge_case_zero_base():
    # Start = 0 -> Zero Base
    cagr, flag = calculate_cagr(0.0, 100.0, 5)
    assert cagr is None
    assert flag == CAGR_FLAG_ZERO_BASE


def test_cagr_edge_case_insufficient_data():
    # Missing start or end
    cagr_none, flag_none = calculate_cagr(None, 100.0, 5)
    assert cagr_none is None
    assert flag_none == CAGR_FLAG_INSUFFICIENT

    cagr_invalid_n, flag_invalid_n = calculate_cagr(100.0, 200.0, 0)
    assert cagr_invalid_n is None
    assert flag_invalid_n == CAGR_FLAG_INSUFFICIENT


def test_compute_series_cagr_multi_window():
    series = {
        2014: 100.0,
        2019: 161.051,
        2021: 200.0,
        2024: 266.2,
    }
    # For target year 2024:
    # 3-yr (2021->2024): 200.0 to 266.2 -> 10.0%
    # 5-yr (2019->2024): 161.051 to 266.2 -> 10.57%
    # 10-yr (2014->2024): 100.0 to 266.2 -> 10.28%
    results = compute_series_cagr(series, target_year=2024, windows=[3, 5, 10])

    assert results["3yr"]["flag"] == CAGR_FLAG_NORMAL
    assert results["3yr"]["value"] == pytest.approx(10.0, abs=0.01)

    assert results["5yr"]["flag"] == CAGR_FLAG_NORMAL
    assert results["10yr"]["flag"] == CAGR_FLAG_NORMAL


def test_compute_series_cagr_handles_missing_start_year():
    series = {
        2022: 150.0,
        2024: 200.0,
    }
    # 5-year start (2019) is missing -> should return INSUFFICIENT
    results = compute_series_cagr(series, target_year=2024, windows=[5])
    assert results["5yr"]["value"] is None
    assert results["5yr"]["flag"] == CAGR_FLAG_INSUFFICIENT


def test_cagr_zero_growth_and_decline():
    # 0% growth
    cagr_flat, flag_flat = calculate_cagr(100.0, 100.0, 5)
    assert flag_flat == CAGR_FLAG_NORMAL
    assert cagr_flat == pytest.approx(0.0, abs=1e-3)

    # Positive decline: 100 to 80 over 2 yrs = -10.557%
    cagr_down, flag_down = calculate_cagr(100.0, 80.0, 2)
    assert flag_down == CAGR_FLAG_NORMAL
    assert cagr_down < 0.0
