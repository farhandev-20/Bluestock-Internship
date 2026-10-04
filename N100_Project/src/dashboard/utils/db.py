"""
Database Access and Cached Data Loader for N100 Streamlit Dashboard.
Implements @st.cache_data(ttl=600) on all query functions to ensure high performance (<3s load times).
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create a SQLite database connection with row factory support."""
    path = db_path or DEFAULT_DB_PATH
    return sqlite3.connect(str(path), check_same_thread=False)


@st.cache_data(ttl=600)
def get_companies(db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve all companies merged with sector, market cap, and latest ratios metadata.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    query = """
    SELECT 
        c.id AS company_id,
        c.company_name,
        c.company_logo,
        c.chart_link,
        c.about_company,
        c.website,
        c.nse_profile,
        c.bse_profile,
        c.face_value,
        c.book_value,
        c.roce_percentage,
        c.roe_percentage,
        s.broad_sector,
        s.sub_sector,
        s.index_weight_pct,
        s.market_cap_category
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    ORDER BY c.company_name ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.drop_duplicates(subset=["company_id"], keep="last")


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: Optional[int] = None, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve financial ratios for a given ticker, optionally filtered by year.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    if year:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=(ticker, year))
    else:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve Profit & Loss statement history for a given ticker.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve Balance Sheet statement history for a given ticker.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve Cash Flow statement history for a given ticker.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors(db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve sectors classification data for all constituents.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    query = "SELECT * FROM sectors ORDER BY broad_sector ASC, sub_sector ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: Optional[str] = None, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve peer group mappings. If group_name is provided, filters for that peer group.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    if group_name:
        query = """
        SELECT pg.peer_group_name, pg.company_id, pg.is_benchmark, c.company_name, s.broad_sector
        FROM peer_groups pg
        LEFT JOIN companies c ON pg.company_id = c.id
        LEFT JOIN sectors s ON pg.company_id = s.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name ASC
        """
        df = pd.read_sql_query(query, conn, params=(group_name,))
    else:
        query = """
        SELECT pg.peer_group_name, pg.company_id, pg.is_benchmark, c.company_name, s.broad_sector
        FROM peer_groups pg
        LEFT JOIN companies c ON pg.company_id = c.id
        LEFT JOIN sectors s ON pg.company_id = s.company_id
        ORDER BY pg.peer_group_name ASC, pg.is_benchmark DESC, c.company_name ASC
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker: Optional[str] = None, year: Optional[int] = None, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve Market Cap and valuation multiples history.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    if ticker and year:
        query = "SELECT * FROM market_cap WHERE company_id = ? AND year = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=(ticker, year))
    elif ticker:
        query = "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    elif year:
        query = "SELECT * FROM market_cap WHERE year = ? ORDER BY market_cap_crore DESC"
        df = pd.read_sql_query(query, conn, params=(year,))
    else:
        query = "SELECT * FROM market_cap ORDER BY year DESC, market_cap_crore DESC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_prosandcons(ticker: str, db_path: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Retrieve pros and cons for a given company ticker.
    If not found in database, dynamically derives intelligent pros and cons from company KPIs.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    query = "SELECT pros, cons FROM prosandcons WHERE company_id = ?"
    cursor = conn.cursor()
    row = cursor.execute(query, (ticker,)).fetchone()
    conn.close()

    pros_list: List[str] = []
    cons_list: List[str] = []

    if row and (row[0] or row[1]):
        pros_raw = row[0] or ""
        cons_raw = row[1] or ""
        pros_list = [p.strip() for p in pros_raw.replace("\r", "\n").split("\n") if p.strip()]
        cons_list = [c.strip() for c in cons_raw.replace("\r", "\n").split("\n") if c.strip()]
    
    # If empty, derive from latest ratios and pnl
    if not pros_list and not cons_list:
        r_df = get_ratios(ticker)
        pl_df = get_pl(ticker)
        mcap_df = get_valuation(ticker)
        
        if not r_df.empty:
            latest_r = r_df.iloc[-1]
            roe = latest_r.get("return_on_equity_pct")
            de = latest_r.get("debt_to_equity")
            fcf = latest_r.get("free_cash_flow_cr")
            rev_cagr = latest_r.get("revenue_cagr_5yr")
            pat_cagr = latest_r.get("pat_cagr_5yr")
            icr = latest_r.get("interest_coverage")

            # Pros evaluation
            if roe is not None and roe >= 15.0:
                pros_list.append(f"Company delivers strong return on equity (ROE of {roe:.1f}%).")
            if de is not None and de <= 0.2:
                pros_list.append(f"Virtually debt-free balance sheet with D/E ratio of {de:.2f}.")
            elif de is not None and de <= 0.8:
                pros_list.append(f"Conservative financial leverage with manageable D/E of {de:.2f}.")
            if fcf is not None and fcf > 0:
                pros_list.append(f"Healthy positive Free Cash Flow generation (₹{fcf:,.0f} Cr).")
            if rev_cagr is not None and rev_cagr >= 10.0:
                pros_list.append(f"Robust 5-year compounded revenue growth of {rev_cagr:.1f}%.")
            if pat_cagr is not None and pat_cagr >= 12.0:
                pros_list.append(f"Solid 5-year profit (PAT) compounding of {pat_cagr:.1f}%.")
            if icr is not None and icr >= 5.0:
                pros_list.append(f"High interest coverage ratio ({icr:.1f}x) mitigating solvency risks.")

            # Cons evaluation
            if roe is not None and roe < 10.0:
                cons_list.append(f"Subdued capital productivity with ROE of {roe:.1f}%.")
            if de is not None and de > 1.5:
                cons_list.append(f"Elevated debt-to-equity ratio of {de:.2f} requires monitoring.")
            if fcf is not None and fcf < 0:
                cons_list.append(f"Negative Free Cash Flow (₹{fcf:,.0f} Cr) due to high capex/working capital.")
            if rev_cagr is not None and rev_cagr < 5.0:
                cons_list.append(f"Modest 5-year revenue CAGR of {rev_cagr:.1f}%.")
            if not mcap_df.empty:
                pe = mcap_df.iloc[-1].get("pe_ratio")
                if pe is not None and pe > 50.0:
                    cons_list.append(f"Trading at a premium valuation multiple with P/E of {pe:.1f}x.")

        if not pros_list:
            pros_list.append("Well-established market presence among Nifty 100 constituents.")
        if not cons_list:
            cons_list.append("Subject to macroeconomic sectoral cycles and input cost inflation.")

    return {"pros": pros_list, "cons": cons_list}


@st.cache_data(ttl=600)
def get_documents(ticker: str, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve Annual Report document links for a given company ticker.
    """
    conn = get_connection(Path(db_path) if db_path else None)
    query = "SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year DESC"
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_all_peer_groups(db_path: Optional[str] = None) -> List[str]:
    """Retrieve list of all 11 distinct peer group names."""
    conn = get_connection(Path(db_path) if db_path else None)
    cursor = conn.cursor()
    groups = [row[0] for row in cursor.execute("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name ASC").fetchall() if row[0]]
    conn.close()
    return groups


@st.cache_data(ttl=600)
def get_all_sectors(db_path: Optional[str] = None) -> List[str]:
    """Retrieve list of all distinct broad sectors."""
    conn = get_connection(Path(db_path) if db_path else None)
    cursor = conn.cursor()
    sectors = [row[0] for row in cursor.execute("SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL ORDER BY broad_sector ASC").fetchall()]
    conn.close()
    return sectors


@st.cache_data(ttl=600)
def get_screener_universe(year: int = 2024, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve the full universe merged dataset with computed composite quality score.
    """
    from src.screener.engine import load_screener_universe
    return load_screener_universe(db_path=Path(db_path) if db_path else None, target_year=year)


@st.cache_data(ttl=600)
def get_capital_allocation_universe(year: int = 2024, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve capital allocation classification for all companies in target year.
    """
    from src.analytics.cashflow_kpis import classify_capital_allocation
    conn = get_connection(Path(db_path) if db_path else None)

    cf_df = pd.read_sql_query("SELECT * FROM cashflow WHERE year = ?", conn, params=(year,))
    pl_df = pd.read_sql_query("SELECT company_id, sales, net_profit FROM profitandloss WHERE year = ?", conn, params=(year,))
    comp_df = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
    sec_df = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    mcap_df = pd.read_sql_query("SELECT company_id, market_cap_crore FROM market_cap WHERE year = ?", conn, params=(year,))
    ratios_df = pd.read_sql_query("SELECT company_id, free_cash_flow_cr, composite_quality_score FROM financial_ratios WHERE year = ?", conn, params=(year,))
    conn.close()

    merged = pd.merge(comp_df, cf_df, on="company_id", how="inner")
    merged = pd.merge(merged, sec_df, on="company_id", how="left")
    merged = pd.merge(merged, pl_df, on="company_id", how="left")
    merged = pd.merge(merged, mcap_df, on="company_id", how="left")
    merged = pd.merge(merged, ratios_df, on="company_id", how="left")

    records = []
    for _, row in merged.iterrows():
        cfo = row.get("operating_activity")
        cfi = row.get("investing_activity")
        cff = row.get("financing_activity")
        pat = row.get("net_profit")
        cfo_pat = (cfo / pat) if (cfo is not None and pat is not None and pat != 0) else None

        broad_sec = row.get("broad_sector")
        if pd.isna(broad_sec) or not broad_sec:
            broad_sec = "Diversified"

        sub_sec = row.get("sub_sector")
        if pd.isna(sub_sec) or not sub_sec:
            sub_sec = "General"

        comp_name = row.get("company_name")
        if pd.isna(comp_name) or not comp_name:
            comp_name = row["company_id"]

        s_cfo, s_cfi, s_cff, pattern = classify_capital_allocation(cfo, cfi, cff, cfo_pat_ratio=cfo_pat)
        records.append({
            "company_id": row["company_id"],
            "company_name": str(comp_name),
            "broad_sector": str(broad_sec),
            "sub_sector": str(sub_sec),
            "cfo_sign": s_cfo,
            "cfi_sign": s_cfi,
            "cff_sign": s_cff,
            "pattern_label": str(pattern or "Mixed"),
            "operating_activity": cfo,
            "investing_activity": cfi,
            "financing_activity": cff,
            "net_profit": pat,
            "sales": row.get("sales"),
            "free_cash_flow_cr": row.get("free_cash_flow_cr"),
            "market_cap_crore": row.get("market_cap_crore"),
            "composite_quality_score": row.get("composite_quality_score"),
        })

    return pd.DataFrame(records)
