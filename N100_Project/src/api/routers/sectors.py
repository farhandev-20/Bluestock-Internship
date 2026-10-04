"""
Sector benchmark and constituent analysis router for N100 REST API.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd
from src.api.db import clean_dict, df_to_clean_records, query_df

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("", summary="List All Sectors & Median KPIs")
def get_all_sectors():
    """
    Returns all 11 sectors with aggregate company_count, median_roe, median_pe, and median_de.
    """
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
        s.company_id,
        s.broad_sector,
        s.sub_sector,
        r.return_on_equity_pct,
        r.debt_to_equity,
        m.pe_ratio,
        m.market_cap_crore
    FROM sectors s
    JOIN LatestRatios r ON s.company_id = r.company_id AND r.rn = 1
    LEFT JOIN LatestMC m ON s.company_id = m.company_id AND m.rn = 1
    """
    df = query_df(query)

    sector_results = []
    
    # 10 Broad Sectors
    for sec_name, group in df.groupby("broad_sector"):
        roe_m = group["return_on_equity_pct"].dropna().median()
        pe_m = group["pe_ratio"].dropna().median()
        de_m = group["debt_to_equity"].dropna().median()
        mcap_s = group["market_cap_crore"].dropna().sum()

        sector_results.append(clean_dict({
            "sector": sec_name,
            "company_count": len(group),
            "median_roe": round(float(roe_m), 2) if not pd.isna(roe_m) else None,
            "median_pe": round(float(pe_m), 2) if not pd.isna(pe_m) else None,
            "median_de": round(float(de_m), 2) if not pd.isna(de_m) else None,
            "total_market_cap_cr": round(float(mcap_s), 2) if not pd.isna(mcap_s) else None,
        }))

    # 11th Sector: Power & Utilities cohort
    util_group = df[df["sub_sector"].str.contains("Power|Utilities|Renewable", case=False, na=False)]
    if not util_group.empty:
        roe_m = util_group["return_on_equity_pct"].dropna().median()
        pe_m = util_group["pe_ratio"].dropna().median()
        de_m = util_group["debt_to_equity"].dropna().median()
        mcap_s = util_group["market_cap_crore"].dropna().sum()

        sector_results.append(clean_dict({
            "sector": "Power & Utilities",
            "company_count": len(util_group),
            "median_roe": round(float(roe_m), 2) if not pd.isna(roe_m) else None,
            "median_pe": round(float(pe_m), 2) if not pd.isna(pe_m) else None,
            "median_de": round(float(de_m), 2) if not pd.isna(de_m) else None,
            "total_market_cap_cr": round(float(mcap_s), 2) if not pd.isna(mcap_s) else None,
        }))

    return {
        "count": len(sector_results),
        "sectors": sector_results,
    }


@router.get("/{sector}/companies", summary="Get Sector Constituents")
def get_sector_companies(sector: str):
    """
    Returns all companies in the specified sector along with their latest year fundamental KPIs.
    Returns 404 if sector is not recognized.
    """
    sec_clean = sector.strip()

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
        s.market_cap_category,
        r.return_on_equity_pct,
        r.operating_profit_margin_pct,
        r.debt_to_equity,
        r.free_cash_flow_cr,
        r.revenue_cagr_5yr,
        m.market_cap_crore,
        m.pe_ratio,
        m.dividend_yield_pct
    FROM sectors s
    JOIN companies c ON s.company_id = c.id
    JOIN LatestRatios r ON s.company_id = r.company_id AND r.rn = 1
    LEFT JOIN LatestMC m ON s.company_id = m.company_id AND m.rn = 1
    WHERE s.broad_sector LIKE ? OR s.sub_sector LIKE ?
    ORDER BY m.market_cap_crore DESC
    """
    df = query_df(query, [f"%{sec_clean}%", f"%{sec_clean}%"])

    if df.empty:
        raise HTTPException(status_code=404, detail=f"Sector '{sec_clean}' not found.")

    return {
        "sector": sec_clean,
        "count": len(df),
        "companies": df_to_clean_records(df),
    }
