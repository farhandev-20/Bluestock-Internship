"""
Valuation multiples, historical market cap, and overvaluation flags router for N100 REST API.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from src.api.db import clean_dict, df_to_clean_records, query_df

router = APIRouter(tags=["Valuation"])


@router.get("/market-cap/{ticker}", summary="Historical Valuation Multiples")
def get_market_cap_multiples(ticker: str):
    """
    Returns historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield)
    from FY2019 to FY2024. Returns 404 if ticker not found.
    """
    ticker_clean = ticker.strip().upper()
    df_check = query_df("SELECT id FROM companies WHERE UPPER(id) = ?", [ticker_clean])
    if df_check.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker_clean}' not found.")

    query = """
    SELECT 
        company_id,
        year,
        market_cap_crore,
        enterprise_value_crore,
        pe_ratio,
        pb_ratio,
        ev_ebitda,
        dividend_yield_pct
    FROM market_cap
    WHERE UPPER(company_id) = ? AND year >= 2019 AND year <= 2024
    ORDER BY year ASC
    """
    df = query_df(query, [ticker_clean])

    return {
        "company_id": ticker_clean,
        "history_count": len(df),
        "multiples": df_to_clean_records(df),
    }


@router.get("/valuation/summary", summary="Valuation Summary & Flags")
def get_valuation_summary(
    flag: Optional[str] = Query(None, description="Filter by Caution / Discount / Fair")
):
    """
    Returns valuation summary with sector median P/E comparisons and overvaluation flags.
    """
    query = """
    WITH LatestMC AS (
        SELECT m.*,
               ROW_NUMBER() OVER(PARTITION BY m.company_id ORDER BY m.year DESC) as rn
        FROM market_cap m
    ),
    LatestRatios AS (
        SELECT r.*,
               ROW_NUMBER() OVER(PARTITION BY r.company_id ORDER BY r.year DESC) as rn
        FROM financial_ratios r
    )
    SELECT 
        c.id AS company_id,
        c.company_name,
        s.broad_sector AS sector,
        m.pe_ratio,
        m.pb_ratio,
        m.ev_ebitda,
        m.dividend_yield_pct,
        m.market_cap_crore,
        r.free_cash_flow_cr
    FROM companies c
    JOIN sectors s ON c.id = s.company_id
    JOIN LatestMC m ON c.id = m.company_id AND m.rn = 1
    JOIN LatestRatios r ON c.id = r.company_id AND r.rn = 1
    """
    df = query_df(query)

    records = []
    # Compute sector medians
    sector_medians = {}
    for sec, grp in df.groupby("sector"):
        valid_pe = grp[grp["pe_ratio"] > 0]["pe_ratio"]
        sector_medians[sec] = valid_pe.median() if not valid_pe.empty else 25.0

    for _, row in df.iterrows():
        pe = row["pe_ratio"]
        sec = row["sector"]
        sec_med = sector_medians.get(sec, 25.0)
        fcf = row["free_cash_flow_cr"] or 0.0
        mcap = row["market_cap_crore"] or 1.0

        fcf_yield = (fcf / mcap) * 100.0 if mcap > 0 else 0.0

        if pe is not None and pe > 0:
            pe_vs_med = ((pe - sec_med) / sec_med) * 100.0
            if pe > 1.5 * sec_med:
                v_flag = "Caution"
            elif pe < 0.7 * sec_med:
                v_flag = "Discount"
            else:
                v_flag = "Fair"
        else:
            pe_vs_med = 0.0
            v_flag = "Fair"

        if not flag or v_flag.lower() == flag.lower():
            records.append(clean_dict({
                "company_id": row["company_id"],
                "company_name": row["company_name"],
                "sector": sec,
                "pe_ratio": round(pe, 2) if pe else None,
                "pb_ratio": round(row["pb_ratio"], 2) if row["pb_ratio"] else None,
                "ev_ebitda": round(row["ev_ebitda"], 2) if row["ev_ebitda"] else None,
                "fcf_yield_pct": round(fcf_yield, 2),
                "sector_median_pe": round(sec_med, 2),
                "pe_vs_sector_median_pct": round(pe_vs_med, 2),
                "flag": v_flag,
            }))

    return {
        "count": len(records),
        "valuation_records": records,
    }
