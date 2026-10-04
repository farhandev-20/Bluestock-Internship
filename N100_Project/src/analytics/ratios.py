"""
Financial Ratios Calculation Module for N100 Intelligence Platform.
Implements Profitability, Leverage, and Efficiency ratios along with edge case handlers
(negative equity, zero denominator, debt-free label, and bank leverage carve-outs).
"""

from typing import Optional, Tuple


# ==============================================================================
# Day 08 — Profitability Ratios
# ==============================================================================

def net_profit_margin(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Compute Net Profit Margin: (net_profit / sales) * 100.
    Returns None if sales is None, 0, or non-positive.
    """
    if net_profit is None or sales is None or sales <= 0:
        return None
    return (net_profit / sales) * 100.0


def operating_profit_margin(operating_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Compute Operating Profit Margin: (operating_profit / sales) * 100.
    Returns None if sales is None, 0, or non-positive.
    """
    if operating_profit is None or sales is None or sales <= 0:
        return None
    return (operating_profit / sales) * 100.0


def cross_check_opm(
    computed_opm: Optional[float], source_opm: Optional[float], threshold: float = 1.0
) -> Tuple[bool, Optional[float]]:
    """
    Cross-checks computed OPM against pre-computed source OPM percentage.
    Returns (is_match, diff). If difference > threshold (default 1.0%), returns is_match=False.
    """
    if computed_opm is None or source_opm is None:
        return True, None
    diff = abs(computed_opm - source_opm)
    is_match = diff <= threshold
    return is_match, diff


def return_on_equity(
    net_profit: Optional[float], equity_capital: Optional[float], reserves: Optional[float]
) -> Optional[float]:
    """
    Compute Return on Equity (ROE): (net_profit / (equity_capital + reserves)) * 100.
    Handles negative equity edge case: returns None if (equity_capital + reserves) <= 0.
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None
    return (net_profit / total_equity) * 100.0


def return_on_capital_employed(
    ebit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float],
    broad_sector: Optional[str] = None,
) -> Optional[float]:
    """
    Compute Return on Capital Employed (ROCE): (EBIT / (equity + reserves + borrowings)) * 100.
    Returns None if capital employed <= 0.
    For companies in Financials sector, uses sector-relative ROCE benchmark.
    """
    if ebit is None or equity_capital is None or reserves is None or borrowings is None:
        return None
    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None
    return (ebit / capital_employed) * 100.0


def return_on_assets(net_profit: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Compute Return on Assets (ROA): (net_profit / total_assets) * 100.
    Returns None if total_assets is None or total_assets <= 0.
    """
    if net_profit is None or total_assets is None or total_assets <= 0:
        return None
    return (net_profit / total_assets) * 100.0


# ==============================================================================
# Day 09 — Leverage & Efficiency Ratios
# ==============================================================================

def debt_to_equity(
    borrowings: Optional[float], equity_capital: Optional[float], reserves: Optional[float]
) -> Optional[float]:
    """
    Compute Debt-to-Equity: borrowings / (equity_capital + reserves).
    Returns 0.0 (not None) if borrowings == 0.
    Returns None if total equity <= 0.
    """
    if equity_capital is None or reserves is None:
        return None
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None
    if borrowings is None or borrowings == 0:
        return 0.0
    return borrowings / total_equity


def get_high_leverage_flag(
    de_ratio: Optional[float], broad_sector: Optional[str] = None, threshold: float = 5.0
) -> bool:
    """
    Evaluate D/E flag: if D/E > threshold and company is NOT in Financials broad sector,
    return True (high_leverage_flag = True).
    Financials companies (banks, NBFCs, insurance) are carved out (returns False).
    """
    if de_ratio is None:
        return False
    if broad_sector and str(broad_sector).strip().lower() == "financials":
        return False
    return de_ratio > threshold


def interest_coverage_ratio(
    operating_profit: Optional[float], other_income: Optional[float], interest: Optional[float]
) -> Optional[float]:
    """
    Compute Interest Coverage Ratio: (operating_profit + other_income) / interest.
    Returns None if interest is None or interest == 0 (debt-free company).
    """
    if interest is None or interest == 0:
        return None
    if operating_profit is None:
        return None
    ebit = operating_profit + (other_income if other_income is not None else 0.0)
    return ebit / interest


def get_icr_label(icr: Optional[float]) -> str:
    """
    For ICR == None (debt-free companies), return display label 'Debt Free'.
    Otherwise return formatted ratio string.
    """
    if icr is None:
        return "Debt Free"
    return f"{icr:.2f}x"


def get_icr_warning_flag(icr: Optional[float], threshold: float = 1.5) -> bool:
    """
    Add ICR warning flag: if ICR is not None and ICR < threshold (1.5),
    company is at risk of not covering interest payments.
    """
    if icr is None:
        return False
    return icr < threshold


def net_debt(borrowings: Optional[float], investments: Optional[float]) -> float:
    """
    Compute Net Debt: borrowings - investments (using investments as liquid asset proxy).
    """
    b = borrowings if borrowings is not None else 0.0
    inv = investments if investments is not None else 0.0
    return b - inv


def asset_turnover(sales: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Compute Asset Turnover: sales / total_assets.
    Returns None if total_assets is None or total_assets <= 0.
    """
    if sales is None or total_assets is None or total_assets <= 0:
        return None
    return sales / total_assets
