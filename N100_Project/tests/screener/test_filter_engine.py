"""
Unit tests for Filter Engine Core (Day 15).
Validates 15 filterable metrics, Financials sector D/E carve-out, and Debt Free ICR infinity handling.
"""

import pandas as pd
import pytest
from src.screener.engine import apply_screener_filters, load_screener_universe


@pytest.fixture
def sample_universe():
    return pd.DataFrame([
        {
            "company_id": "TECH_CO",
            "company_name": "Tech Compounder",
            "broad_sector": "Information Technology",
            "return_on_equity_pct": 28.5,
            "debt_to_equity": 0.05,
            "free_cash_flow_cr": 1500.0,
            "revenue_cagr_5yr": 16.2,
            "pat_cagr_5yr": 22.0,
            "operating_profit_margin_pct": 25.0,
            "pe_ratio": 24.0,
            "pb_ratio": 6.5,
            "dividend_yield_pct": 1.5,
            "interest_coverage": 45.0,
            "market_cap_crore": 120000.0,
            "net_profit": 5000.0,
            "eps_cagr_5yr": 21.0,
            "asset_turnover": 0.85,
            "sales": 20000.0,
            "composite_quality_score": 88.0,
        },
        {
            "company_id": "DEBT_FREE_CO",
            "company_name": "Zero Debt FMCG",
            "broad_sector": "Fast Moving Consumer Goods",
            "return_on_equity_pct": 22.0,
            "debt_to_equity": 0.0,
            "free_cash_flow_cr": 800.0,
            "revenue_cagr_5yr": 8.5,
            "pat_cagr_5yr": 12.0,
            "operating_profit_margin_pct": 28.0,
            "pe_ratio": 35.0,
            "pb_ratio": 8.0,
            "dividend_yield_pct": 2.5,
            "interest_coverage": None,  # Debt Free
            "market_cap_crore": 85000.0,
            "net_profit": 2500.0,
            "eps_cagr_5yr": 11.5,
            "asset_turnover": 1.2,
            "sales": 9000.0,
            "composite_quality_score": 82.0,
        },
        {
            "company_id": "BANK_CO",
            "company_name": "Top Private Bank",
            "broad_sector": "Financials",
            "return_on_equity_pct": 17.0,
            "debt_to_equity": 7.5,  # High bank leverage
            "free_cash_flow_cr": 4500.0,
            "revenue_cagr_5yr": 18.0,
            "pat_cagr_5yr": 20.5,
            "operating_profit_margin_pct": 32.0,
            "pe_ratio": 16.0,
            "pb_ratio": 2.8,
            "dividend_yield_pct": 1.2,
            "interest_coverage": 1.6,
            "market_cap_crore": 350000.0,
            "net_profit": 20000.0,
            "eps_cagr_5yr": 19.0,
            "asset_turnover": 0.12,
            "sales": 65000.0,
            "composite_quality_score": 75.0,
        },
        {
            "company_id": "HEAVY_DEBT_CO",
            "company_name": "Struggling Metal",
            "broad_sector": "Metals & Mining",
            "return_on_equity_pct": 6.0,
            "debt_to_equity": 3.5,
            "free_cash_flow_cr": -300.0,
            "revenue_cagr_5yr": 4.0,
            "pat_cagr_5yr": -5.0,
            "operating_profit_margin_pct": 9.0,
            "pe_ratio": 14.0,
            "pb_ratio": 1.2,
            "dividend_yield_pct": 0.5,
            "interest_coverage": 1.1,
            "market_cap_crore": 15000.0,
            "net_profit": 350.0,
            "eps_cagr_5yr": -6.0,
            "asset_turnover": 0.45,
            "sales": 8000.0,
            "composite_quality_score": 38.0,
        }
    ])


def test_filter_by_roe_and_fcf(sample_universe):
    # ROE >= 15% and FCF >= 0
    filters = {
        "return_on_equity_pct": {"min": 15.0},
        "free_cash_flow_cr": {"min": 0.0},
    }
    res = apply_screener_filters(sample_universe, filters)
    assert len(res) == 3
    assert set(res["company_id"]) == {"TECH_CO", "DEBT_FREE_CO", "BANK_CO"}


def test_financials_sector_de_carve_out(sample_universe):
    # D/E <= 1.0 -> BANK_CO has D/E=7.5 but is in Financials sector -> should NOT be excluded
    filters = {
        "debt_to_equity": {"max": 1.0}
    }
    res = apply_screener_filters(sample_universe, filters)
    # TECH_CO (0.05), DEBT_FREE_CO (0.0), and BANK_CO (Financials carve-out) pass. HEAVY_DEBT_CO (3.5) fails.
    assert len(res) == 3
    assert "BANK_CO" in res["company_id"].values
    assert "HEAVY_DEBT_CO" not in res["company_id"].values


def test_debt_free_icr_infinity_handling(sample_universe):
    # ICR >= 10.0 -> DEBT_FREE_CO has ICR=None (Debt Free), should pass as ICR is infinite
    filters = {
        "interest_coverage": {"min": 10.0}
    }
    res = apply_screener_filters(sample_universe, filters)
    assert "DEBT_FREE_CO" in res["company_id"].values
    assert "TECH_CO" in res["company_id"].values
    assert "HEAVY_DEBT_CO" not in res["company_id"].values


def test_all_15_metrics_filtering(sample_universe):
    # Test strict combination
    filters = {
        "return_on_equity_pct": {"min": 20.0},
        "operating_profit_margin_pct": {"min": 20.0},
        "sales": {"min": 10000.0},
        "market_cap_crore": {"min": 50000.0},
        "pe_ratio": {"max": 30.0},
        "pb_ratio": {"max": 10.0},
        "dividend_yield_pct": {"min": 1.0},
        "asset_turnover": {"min": 0.5},
        "net_profit": {"min": 1000.0},
        "revenue_cagr_5yr": {"min": 10.0},
        "pat_cagr_5yr": {"min": 15.0},
        "eps_cagr_5yr": {"min": 15.0},
    }
    res = apply_screener_filters(sample_universe, filters)
    assert len(res) == 1
    assert res.iloc[0]["company_id"] == "TECH_CO"
