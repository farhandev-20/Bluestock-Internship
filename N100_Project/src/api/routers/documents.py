"""
Annual reports and regulatory documents router for N100 REST API.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from src.api.db import query_df

router = APIRouter(tags=["Documents"])


@router.get("/companies/{ticker}/documents", summary="Get Annual Report Links & URL Status")
def get_company_documents(ticker: str):
    """
    Returns annual report regulatory filing links with an `is_url_valid`
    boolean flag for each fiscal year. Returns 404 if company not found.
    """
    ticker_clean = ticker.strip().upper()
    df_check = query_df("SELECT id FROM companies WHERE UPPER(id) = ?", [ticker_clean])
    if df_check.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker_clean}' not found.")

    query = "SELECT * FROM documents WHERE UPPER(company_id) = ? ORDER BY year DESC"
    df = query_df(query, [ticker_clean])

    records = []
    for _, row in df.iterrows():
        url = row.get("annual_report")
        is_valid = bool(url and isinstance(url, str) and url.startswith("http"))
        records.append({
            "company_id": ticker_clean,
            "year": int(row["year"]) if pd_notna(row.get("year")) else None,
            "annual_report_url": url if is_valid else None,
            "is_url_valid": is_valid,
        })

    return {
        "company_id": ticker_clean,
        "count": len(records),
        "documents": records,
    }


def pd_notna(val: Any) -> bool:
    import pandas as pd
    return pd.notna(val)
