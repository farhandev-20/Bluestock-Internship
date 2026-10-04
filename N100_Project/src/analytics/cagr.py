"""
CAGR Calculation Engine for N100 Intelligence Platform.
Implements multi-period CAGR (3-year, 5-year, 10-year) with full handling of all
6 edge cases (Normal, Decline to Loss, Turnaround, Both Negative, Zero Base, Insufficient Data).
"""

from typing import Dict, List, Optional, Tuple, Union
import pandas as pd


# Constants for all 6 CAGR edge-case flags
CAGR_FLAG_NORMAL = "NORMAL"
CAGR_FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
CAGR_FLAG_TURNAROUND = "TURNAROUND"
CAGR_FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
CAGR_FLAG_ZERO_BASE = "ZERO_BASE"
CAGR_FLAG_INSUFFICIENT = "INSUFFICIENT"

CAGR_FLAGS = {
    CAGR_FLAG_NORMAL,
    CAGR_FLAG_DECLINE_TO_LOSS,
    CAGR_FLAG_TURNAROUND,
    CAGR_FLAG_BOTH_NEGATIVE,
    CAGR_FLAG_ZERO_BASE,
    CAGR_FLAG_INSUFFICIENT,
}


def calculate_cagr(
    start_val: Optional[float],
    end_val: Optional[float],
    n_years: int,
) -> Tuple[Optional[float], str]:
    """
    Calculate Compound Annual Growth Rate (CAGR) with comprehensive edge-case handling.
    
    Formula: ((end_val / start_val) ** (1 / n_years) - 1) * 100

    Edge Cases:
    1. Positive + Positive -> compute normally, flag = 'NORMAL'
    2. Positive + Negative (start > 0, end <= 0) -> None, flag = 'DECLINE_TO_LOSS'
    3. Negative + Positive (start < 0, end > 0) -> None, flag = 'TURNAROUND'
    4. Negative + Negative (start < 0, end < 0) -> None, flag = 'BOTH_NEGATIVE'
    5. Zero base (start == 0) -> None, flag = 'ZERO_BASE'
    6. Missing data / invalid n -> None, flag = 'INSUFFICIENT'
    """
    if n_years is None or n_years <= 0 or start_val is None or end_val is None:
        return None, CAGR_FLAG_INSUFFICIENT

    # Check Zero Base
    if start_val == 0:
        return None, CAGR_FLAG_ZERO_BASE

    # Check Negative / Sign Flip Edge Cases
    if start_val > 0 and end_val <= 0:
        return None, CAGR_FLAG_DECLINE_TO_LOSS

    if start_val < 0 and end_val > 0:
        return None, CAGR_FLAG_TURNAROUND

    if start_val < 0 and end_val < 0:
        return None, CAGR_FLAG_BOTH_NEGATIVE

    # Standard Positive -> Positive calculation
    try:
        ratio = end_val / start_val
        if ratio <= 0:
            return None, CAGR_FLAG_DECLINE_TO_LOSS
        cagr = ((ratio ** (1.0 / n_years)) - 1.0) * 100.0
        return cagr, CAGR_FLAG_NORMAL
    except (ZeroDivisionError, ValueError, OverflowError):
        return None, CAGR_FLAG_INSUFFICIENT


def compute_series_cagr(
    yearly_values: Dict[int, Optional[float]],
    target_year: int,
    windows: List[int] = [3, 5, 10],
) -> Dict[str, Dict[str, Union[Optional[float], str]]]:
    """
    Compute CAGR across multiple windows (3, 5, 10 years) for a given target year.
    Returns dictionary mapping window string (e.g. '3yr', '5yr', '10yr') to
    {'value': float or None, 'flag': str}.
    """
    results = {}
    end_val = yearly_values.get(target_year)

    for n in windows:
        start_year = target_year - n
        start_val = yearly_values.get(start_year)

        if start_val is None or end_val is None:
            results[f"{n}yr"] = {"value": None, "flag": CAGR_FLAG_INSUFFICIENT}
        else:
            val, flag = calculate_cagr(start_val, end_val, n)
            results[f"{n}yr"] = {"value": val, "flag": flag}

    return results
