"""
Company profiles, financial statements, ratios, and PDF tearsheet endpoints.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from src.api.db import clean_dict, df_to_clean_records, get_db_connection, query_df

router = APIRouter(prefix="/companies", tags=["Companies"])
PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEARSHEET_DIR = PROJECT_ROOT / "reports" / "tearsheets"


def parse_year_param(val: Optional[str]) -> Optional[int]:
    """Parses year string in YYYY or YYYY-MM format to integer year."""
    if not val:
        return None
    val_str = str(val).strip()
    if "-" in val_str:
        val_str = val_str.split("-")[0]
    try:
        return int(val_str)
    except ValueError:
        return None


@router.get("", summary="List Constituents")
def list_companies(
    sector: Optional[str] = Query(None, description="Filter by broad sector"),
    market_cap_category: Optional[str] = Query(None, description="Filter by Large Cap / Mid Cap"),
    search: Optional[str] = Query(None, description="Search by ticker or company name substring"),
):
    """
    Returns list of all 92 companies in the Nifty 100 universe with
    id, company_name, broad_sector, sub_sector, roe_pct, roce_pct.
    """
    query = """
    SELECT 
        c.id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category,
        c.roe_percentage AS roe_pct,
        c.roce_percentage AS roce_pct
    FROM companies c
    JOIN sectors s ON c.id = s.company_id
    WHERE 1=1
    """
    params = []

    if sector:
        query += " AND (s.broad_sector LIKE ? OR s.sub_sector LIKE ?)"
        params.extend([f"%{sector}%", f"%{sector}%"])

    if market_cap_category:
        query += " AND s.market_cap_category LIKE ?"
        params.append(f"%{market_cap_category}%")

    if search:
        query += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY c.id ASC"
    df = query_df(query, params)

    records = df_to_clean_records(df)
    return {
        "count": len(records),
        "companies": records,
    }


@router.get("/{ticker}", summary="Full Company Profile")
def get_company_profile(ticker: str):
    """
    Returns full company profile including master fields, sector classification,
    and latest fiscal year ratios. Returns 404 if ticker not found.
    """
    ticker_clean = ticker.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Company meta
    cursor.execute("SELECT * FROM companies WHERE UPPER(id) = ?", (ticker_clean,))
    comp_row = cursor.fetchone()
    if not comp_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker_clean}' not found.")

    comp_dict = dict(comp_row)

    # Sector data
    cursor.execute("SELECT * FROM sectors WHERE UPPER(company_id) = ?", (ticker_clean,))
    sec_row = cursor.fetchone()
    sec_dict = dict(sec_row) if sec_row else {}

    # Latest ratios
    cursor.execute("SELECT * FROM financial_ratios WHERE UPPER(company_id) = ? ORDER BY year DESC LIMIT 1", (ticker_clean,))
    r_row = cursor.fetchone()
    r_dict = dict(r_row) if r_row else {}

    # Latest valuation
    cursor.execute("SELECT * FROM market_cap WHERE UPPER(company_id) = ? ORDER BY year DESC LIMIT 1", (ticker_clean,))
    m_row = cursor.fetchone()
    m_dict = dict(m_row) if m_row else {}

    conn.close()

    res = {
        "company_id": ticker_clean,
        "company_name": comp_dict.get("company_name"),
        "about": comp_dict.get("about_company"),
        "website": comp_dict.get("website"),
        "sector": sec_dict.get("broad_sector"),
        "sub_sector": sec_dict.get("sub_sector"),
        "market_cap_category": sec_dict.get("market_cap_category"),
        "latest_financials": {
            "year": r_dict.get("year"),
            "return_on_equity_pct": r_dict.get("return_on_equity_pct"),
            "operating_profit_margin_pct": r_dict.get("operating_profit_margin_pct"),
            "debt_to_equity": r_dict.get("debt_to_equity"),
            "interest_coverage": r_dict.get("interest_coverage"),
            "free_cash_flow_cr": r_dict.get("free_cash_flow_cr"),
            "market_cap_crore": m_dict.get("market_cap_crore"),
            "pe_ratio": m_dict.get("pe_ratio"),
            "pb_ratio": m_dict.get("pb_ratio"),
            "dividend_yield_pct": m_dict.get("dividend_yield_pct"),
        },
    }
    return clean_dict(res)


@router.get("/{ticker}/pl", summary="Profit & Loss History")
def get_company_pl(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year e.g. 2015 or 2015-03"),
    to_year: Optional[str] = Query(None, description="End year e.g. 2024 or 2024-03"),
):
    """
    Returns historical Profit & Loss statements for the requested company.
    """
    ticker_clean = ticker.strip().upper()
    df_check = query_df("SELECT id FROM companies WHERE UPPER(id) = ?", [ticker_clean])
    if df_check.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker_clean}' not found.")

    query = "SELECT * FROM profitandloss WHERE UPPER(company_id) = ?"
    params = [ticker_clean]

    start_yr = parse_year_param(from_year)
    end_yr = parse_year_param(to_year)

    if start_yr is not None:
        query += " AND year >= ?"
        params.append(start_yr)
    if end_yr is not None:
        query += " AND year <= ?"
        params.append(end_yr)

    query += " ORDER BY year ASC"
    df = query_df(query, params)

    return {
        "company_id": ticker_clean,
        "count": len(df),
        "profit_and_loss": df_to_clean_records(df),
    }


@router.get("/{ticker}/bs", summary="Balance Sheet History")
def get_company_bs(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year"),
    to_year: Optional[str] = Query(None, description="End year"),
):
    """
    Returns historical Balance Sheets for the requested company.
    """
    ticker_clean = ticker.strip().upper()
    df_check = query_df("SELECT id FROM companies WHERE UPPER(id) = ?", [ticker_clean])
    if df_check.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker_clean}' not found.")

    query = "SELECT * FROM balancesheet WHERE UPPER(company_id) = ?"
    params = [ticker_clean]

    start_yr = parse_year_param(from_year)
    end_yr = parse_year_param(to_year)

    if start_yr is not None:
        query += " AND year >= ?"
        params.append(start_yr)
    if end_yr is not None:
        query += " AND year <= ?"
        params.append(end_yr)

    query += " ORDER BY year ASC"
    df = query_df(query, params)

    return {
        "company_id": ticker_clean,
        "count": len(df),
        "balance_sheet": df_to_clean_records(df),
    }


@router.get("/{ticker}/cashflow", summary="Cash Flow History")
def get_company_cashflow(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year"),
    to_year: Optional[str] = Query(None, description="End year"),
):
    """
    Returns historical Cash Flow statements for the requested company.
    """
    ticker_clean = ticker.strip().upper()
    df_check = query_df("SELECT id FROM companies WHERE UPPER(id) = ?", [ticker_clean])
    if df_check.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker_clean}' not found.")

    query = "SELECT * FROM cashflow WHERE UPPER(company_id) = ?"
    params = [ticker_clean]

    start_yr = parse_year_param(from_year)
    end_yr = parse_year_param(to_year)

    if start_yr is not None:
        query += " AND year >= ?"
        params.append(start_yr)
    if end_yr is not None:
        query += " AND year <= ?"
        params.append(end_yr)

    query += " ORDER BY year ASC"
    df = query_df(query, params)

    return {
        "company_id": ticker_clean,
        "count": len(df),
        "cash_flow": df_to_clean_records(df),
    }


@router.get("/{ticker}/ratios", summary="Computed Financial Ratios")
def get_company_ratios(
    ticker: str,
    year: Optional[int] = Query(None, description="Optional specific fiscal year"),
):
    """
    Returns historical computed KPIs and ratios for the requested company.
    """
    ticker_clean = ticker.strip().upper()
    df_check = query_df("SELECT id FROM companies WHERE UPPER(id) = ?", [ticker_clean])
    if df_check.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker_clean}' not found.")

    query = "SELECT * FROM financial_ratios WHERE UPPER(company_id) = ?"
    params = [ticker_clean]

    if year is not None:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year ASC"
    df = query_df(query, params)

    return {
        "company_id": ticker_clean,
        "count": len(df),
        "ratios": df_to_clean_records(df),
    }


@router.get("/{ticker}/tearsheet", summary="Download 2-Page PDF Tearsheet")
def download_tearsheet(ticker: str):
    """
    Returns the pre-generated 2-page institutional PDF tearsheet as a binary download.
    """
    ticker_clean = ticker.strip().upper()
    pdf_file = TEARSHEET_DIR / f"{ticker_clean}_tearsheet.pdf"

    if not pdf_file.exists():
        # Attempt on-demand compilation if not pre-generated
        from src.reports.tearsheet import create_company_tearsheet
        ok = create_company_tearsheet(ticker_clean, pdf_file)
        if not ok or not pdf_file.exists():
            raise HTTPException(status_code=404, detail=f"Tearsheet PDF for '{ticker_clean}' is not available.")

    return FileResponse(
        path=str(pdf_file),
        filename=f"{ticker_clean}_tearsheet.pdf",
        media_type="application/pdf",
    )
