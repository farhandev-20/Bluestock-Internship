"""
Portfolio aggregate distribution statistics router for N100 REST API.
"""

from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter
import pandas as pd
from src.analytics.clustering import compute_portfolio_statistics
from src.api.db import df_to_clean_records

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PORTFOLIO_STATS_CSV = PROJECT_ROOT / "output" / "portfolio_stats.csv"


@router.get("/stats", summary="Portfolio 10 Core KPI Percentiles")
def get_portfolio_stats():
    """
    Returns P10, P25, P50 (median), P75, P90, Mean, and Std Dev
    for 10 core financial KPIs across all 92 constituent companies.
    """
    if PORTFOLIO_STATS_CSV.exists():
        df = pd.read_csv(PORTFOLIO_STATS_CSV)
    else:
        df = compute_portfolio_statistics(output_csv=PORTFOLIO_STATS_CSV)

    records = df_to_clean_records(df)
    return {
        "kpi_count": len(records),
        "statistics": records,
    }
