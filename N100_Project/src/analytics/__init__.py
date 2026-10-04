"""
Analytics and Financial Ratio Engine Package for N100 Intelligence Platform.
"""

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    cross_check_opm,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    get_high_leverage_flag,
    interest_coverage_ratio,
    get_icr_label,
    get_icr_warning_flag,
    net_debt,
    asset_turnover,
)
from src.analytics.cagr import calculate_cagr, compute_series_cagr, CAGR_FLAGS
from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    classify_capital_allocation,
)

__all__ = [
    "net_profit_margin",
    "operating_profit_margin",
    "cross_check_opm",
    "return_on_equity",
    "return_on_capital_employed",
    "return_on_assets",
    "debt_to_equity",
    "get_high_leverage_flag",
    "interest_coverage_ratio",
    "get_icr_label",
    "get_icr_warning_flag",
    "net_debt",
    "asset_turnover",
    "calculate_cagr",
    "compute_series_cagr",
    "CAGR_FLAGS",
    "free_cash_flow",
    "cfo_quality_score",
    "capex_intensity",
    "fcf_conversion_rate",
    "classify_capital_allocation",
]
