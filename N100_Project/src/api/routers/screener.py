"""
Multi-metric fundamental screener router for N100 REST API.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from src.api.db import df_to_clean_records, query_df

router = APIRouter(prefix="/screener", tags=["Screener"])


@router.get("", summary="Execute Fundamental Screener")
def run_screener_api(
    min_roe: Optional[float] = Query(None, description="Minimum Return on Equity (%)"),
    max_de: Optional[float] = Query(None, description="Maximum Debt-to-Equity Ratio"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow (₹ Cr)"),
    sector: Optional[str] = Query(None, description="Broad Sector filter"),
    min_rev_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-Yr Revenue CAGR (%)"),
    min_pat_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-Yr PAT CAGR (%)"),
    max_pe: Optional[float] = Query(None, description="Maximum Price to Earnings Ratio (x)"),
):
    """
    Screens latest year financial ratios and returns ranked matching companies.
    Returns HTTP 400 for invalid parameter inputs (e.g. max_de < 0 or max_pe <= 0).
    """
    # Validation
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de parameter must be non-negative.")
    if max_pe is not None and max_pe <= 0:
        raise HTTPException(status_code=400, detail="max_pe parameter must be strictly positive.")

    # SQL query for latest year (2024 or latest available)
    query = """
    WITH LatestRatios AS (
        SELECT r.*,
               ROW_NUMBER() OVER(PARTITION BY r.company_id ORDER BY r.year DESC) as rn
        FROM financial_ratios r
    ),
    LatestMC AS (
        SELECT m.*,
               ROW_NUMBER() OVER(PARTITION BY m.company_id ORDER BY m.year DESC) as rn
        FROM market_cap m
    )
    SELECT 
        c.id AS company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        r.year,
        r.return_on_equity_pct,
        r.debt_to_equity,
        r.operating_profit_margin_pct,
        r.free_cash_flow_cr,
        r.revenue_cagr_5yr,
        r.pat_cagr_5yr,
        r.composite_quality_score,
        m.market_cap_crore,
        m.pe_ratio,
        m.pb_ratio,
        m.dividend_yield_pct
    FROM companies c
    JOIN sectors s ON c.id = s.company_id
    JOIN LatestRatios r ON c.id = r.company_id AND r.rn = 1
    LEFT JOIN LatestMC m ON c.id = m.company_id AND m.rn = 1
    WHERE 1=1
    """
    params = []

    if sector:
        query += " AND (s.broad_sector LIKE ? OR s.sub_sector LIKE ?)"
        params.extend([f"%{sector}%", f"%{sector}%"])

    if min_roe is not None:
        query += " AND r.return_on_equity_pct >= ?"
        params.append(min_roe)

    if max_de is not None:
        query += " AND (r.debt_to_equity <= ? OR r.debt_to_equity IS NULL)"
        params.append(max_de)

    if min_fcf is not None:
        query += " AND r.free_cash_flow_cr >= ?"
        params.append(min_fcf)

    if min_rev_cagr_5yr is not None:
        query += " AND r.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)

    if min_pat_cagr_5yr is not None:
        query += " AND r.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)

    if max_pe is not None:
        query += " AND (m.pe_ratio <= ? AND m.pe_ratio > 0)"
        params.append(max_pe)

    query += " ORDER BY r.composite_quality_score DESC, m.market_cap_crore DESC"

    df = query_df(query, params)
    records = df_to_clean_records(df)

    return {
        "matched_count": len(records),
        "results": records,
    }
