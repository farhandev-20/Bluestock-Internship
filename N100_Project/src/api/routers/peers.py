"""
Peer comparison, percentile rankings, and radar chart data router for N100 REST API.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd
from src.api.db import clean_dict, df_to_clean_records, query_df

router = APIRouter(tags=["Peers"])


@router.get("/peers/{group_name}", summary="Get Peer Group Percentiles")
def get_peer_group_details(group_name: str):
    """
    Returns all constituent companies in the peer group along with percentile
    rankings for all 10 core metrics. Returns 404 if peer group not found.
    """
    group_clean = group_name.strip()
    
    # Check if group exists
    df_check = query_df("SELECT DISTINCT peer_group_name FROM peer_groups WHERE LOWER(peer_group_name) = LOWER(?)", [group_clean])
    if df_check.empty:
        raise HTTPException(status_code=404, detail=f"Peer group '{group_clean}' not found.")

    actual_group_name = df_check.iloc[0]["peer_group_name"]

    # Fetch percentiles and members
    query = """
    SELECT 
        p.company_id,
        c.company_name,
        p.peer_group_name,
        pg.is_benchmark,
        p.metric,
        p.value,
        p.percentile_rank,
        p.year
    FROM peer_percentiles p
    JOIN companies c ON p.company_id = c.id
    JOIN peer_groups pg ON p.peer_group_name = pg.peer_group_name AND p.company_id = pg.company_id
    WHERE LOWER(p.peer_group_name) = LOWER(?)
    ORDER BY p.company_id ASC, p.metric ASC
    """
    df = query_df(query, [actual_group_name])
    members_df = query_df("SELECT company_id, is_benchmark FROM peer_groups WHERE LOWER(peer_group_name) = LOWER(?)", [actual_group_name])

    return clean_dict({
        "peer_group": actual_group_name,
        "constituent_count": len(members_df),
        "constituents": df_to_clean_records(members_df),
        "percentile_records": df_to_clean_records(df),
    })


@router.get("/companies/{ticker}/peers/compare", summary="8-Axis Radar Comparison Data")
def get_company_peer_radar_comparison(ticker: str):
    """
    Returns 8-axis radar comparison data:
    1. Selected Company metric values
    2. Peer group average
    3. Sector/Cohort Benchmark company values
    """
    ticker_clean = ticker.strip().upper()

    # Find company's peer group
    df_group = query_df("SELECT peer_group_name, is_benchmark FROM peer_groups WHERE UPPER(company_id) = ?", [ticker_clean])
    if df_group.empty:
        raise HTTPException(status_code=404, detail=f"Peer group cohort not found for company '{ticker_clean}'.")

    group_name = df_group.iloc[0]["peer_group_name"]

    # 8 Radar axes
    radar_axes = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "net_profit_margin_pct",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "asset_turnover",
        "interest_coverage",
        "composite_quality_score",
    ]

    # Fetch latest ratios for all peers in the group
    query = """
    WITH LatestRatios AS (
        SELECT r.*,
               ROW_NUMBER() OVER(PARTITION BY r.company_id ORDER BY r.year DESC) as rn
        FROM financial_ratios r
    )
    SELECT 
        pg.company_id,
        pg.is_benchmark,
        r.return_on_equity_pct,
        r.operating_profit_margin_pct,
        r.net_profit_margin_pct,
        r.revenue_cagr_5yr,
        r.pat_cagr_5yr,
        r.asset_turnover,
        r.interest_coverage,
        r.composite_quality_score
    FROM peer_groups pg
    JOIN LatestRatios r ON pg.company_id = r.company_id AND r.rn = 1
    WHERE pg.peer_group_name = ?
    """
    peers_df = query_df(query, [group_name])

    if peers_df.empty:
        raise HTTPException(status_code=404, detail=f"No financial data available for peer group '{group_name}'.")

    # Company data
    comp_row = peers_df[peers_df["company_id"].str.upper() == ticker_clean]
    if comp_row.empty:
        raise HTTPException(status_code=404, detail=f"Financial data for '{ticker_clean}' not found.")

    comp_dict = comp_row.iloc[0].to_dict()

    # Benchmark company data
    bench_row = peers_df[peers_df["is_benchmark"] == 1]
    if bench_row.empty:
        bench_row = peers_df.iloc[0:1]
    bench_dict = bench_row.iloc[0].to_dict()
    bench_cid = bench_dict.get("company_id")

    # Compute group averages
    group_avg = {}
    company_vals = {}
    benchmark_vals = {}

    for axis in radar_axes:
        company_vals[axis] = round(float(comp_dict.get(axis, 0.0) or 0.0), 2)
        benchmark_vals[axis] = round(float(bench_dict.get(axis, 0.0) or 0.0), 2)
        avg_v = peers_df[axis].dropna().mean()
        group_avg[axis] = round(float(avg_v), 2) if not np.isnan(avg_v) else 0.0

    return clean_dict({
        "company_id": ticker_clean,
        "peer_group_name": group_name,
        "benchmark_company_id": bench_cid,
        "axes": radar_axes,
        "company_metrics": company_vals,
        "peer_group_average": group_avg,
        "benchmark_metrics": benchmark_vals,
    })
