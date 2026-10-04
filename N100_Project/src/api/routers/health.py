"""
Health and system status router for N100 REST API.
"""

import time
from fastapi import APIRouter
from src.api.db import get_db_connection

router = APIRouter(tags=["Health"])
START_TIME = time.time()


@router.get("/health", summary="System Health & Table Row Counts")
def get_health_status():
    """
    Returns server health status, uptime, API version,
    and row counts across all 10 SQLite database tables.
    """
    tables = [
        "companies",
        "analysis",
        "balancesheet",
        "cashflow",
        "documents",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "profitandloss",
        "sectors",
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    row_counts = {}
    
    for tbl in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = cursor.fetchone()[0]
            row_counts[tbl] = count
        except Exception:
            row_counts[tbl] = 0

    conn.close()

    uptime = round(time.time() - START_TIME, 2)

    return {
        "status": "ok",
        "uptime_seconds": uptime,
        "version": "1.0.0",
        "db_row_counts": row_counts,
    }
