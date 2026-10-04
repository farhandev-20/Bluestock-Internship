"""
Integration and Verification Tests for Financial Ratio Engine (Days 12–14).
Validates definition of done:
- SELECT COUNT(*) FROM financial_ratios >= 1,100
- All 14+ KPI columns populated (zero null-only columns)
- Spot-checks on 3 companies matching manual calculations within 0.1%
- Screener preview ROE > 15% and D/E < 1 returns 15-50 companies
- capital_allocation.csv and ratio_edge_cases.log generated and populated
"""

from pathlib import Path
import sqlite3
import pandas as pd
import pytest

from src.analytics.engine import run_ratio_engine, DEFAULT_DB_PATH, OUTPUT_DIR


@pytest.fixture(scope="module")
def ratio_engine_run():
    """Run ratio engine once for the integration tests."""
    return run_ratio_engine(db_path=DEFAULT_DB_PATH, output_dir=OUTPUT_DIR)


def test_financial_ratios_row_count_gte_1100(ratio_engine_run):
    """Exit Criteria 1: financial_ratios table in SQLite has >= 1,100 rows."""
    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
    count = conn.execute("SELECT COUNT(*) FROM financial_ratios;").fetchone()[0]
    conn.close()
    assert count >= 1100, f"Expected >= 1,100 rows in financial_ratios, found {count}"


def test_zero_null_only_columns(ratio_engine_run):
    """Exit Criteria 2: All 14+ KPI columns are populated (zero null-only columns)."""
    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
    df = pd.read_sql_query("SELECT * FROM financial_ratios;", conn)
    conn.close()

    required_kpis = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "composite_quality_score",
    ]

    for col in required_kpis:
        assert col in df.columns, f"Missing KPI column: {col}"
        non_null_count = df[col].notna().sum()
        assert non_null_count > 0, f"Column {col} has zero non-null values!"


def test_manual_spot_checks_within_0_1_percent(ratio_engine_run):
    """Exit Criteria 4: Spot-check 3 companies matching manual calculations within 0.1%."""
    conn = sqlite3.connect(str(DEFAULT_DB_PATH))

    # Test companies: e.g. TCS, INFY, RELIANCE, HDFCBANK, ITC
    spot_companies = ["INFY", "TCS", "ITC"]

    for cid in spot_companies:
        # Fetch raw statement data
        bs = pd.read_sql_query(f"SELECT * FROM balancesheet WHERE company_id = '{cid}' ORDER BY year;", conn)
        pnl = pd.read_sql_query(f"SELECT * FROM profitandloss WHERE company_id = '{cid}' ORDER BY year;", conn)
        ratios = pd.read_sql_query(f"SELECT * FROM financial_ratios WHERE company_id = '{cid}' ORDER BY year;", conn)

        if bs.empty or pnl.empty or ratios.empty:
            continue

        # Check latest year ROE
        latest_yr = int(pnl["year"].max())
        pnl_yr = pnl[pnl["year"] == latest_yr].iloc[-1]
        bs_yr = bs[bs["year"] == latest_yr].iloc[-1]
        ratio_yr = ratios[ratios["year"] == latest_yr].iloc[-1]

        net_profit = pnl_yr["net_profit"]
        total_equity = bs_yr["equity_capital"] + bs_yr["reserves"]

        if total_equity > 0 and pd.notna(ratio_yr["return_on_equity_pct"]):
            manual_roe = (net_profit / total_equity) * 100.0
            db_roe = ratio_yr["return_on_equity_pct"]
            assert abs(manual_roe - db_roe) <= 0.1, f"ROE mismatch for {cid} in {latest_yr}: manual={manual_roe}, db={db_roe}"

        # Check 5-year Revenue CAGR if 5-year prior data exists
        start_yr = latest_yr - 5
        pnl_start = pnl[pnl["year"] == start_yr]
        if not pnl_start.empty and pd.notna(ratio_yr["revenue_cagr_5yr"]):
            sales_start = pnl_start.iloc[0]["sales"]
            sales_end = pnl_yr["sales"]
            if sales_start > 0 and sales_end > 0:
                manual_cagr = (((sales_end / sales_start) ** (1.0 / 5.0)) - 1.0) * 100.0
                db_cagr = ratio_yr["revenue_cagr_5yr"]
                assert abs(manual_cagr - db_cagr) <= 0.1, f"CAGR mismatch for {cid}: manual={manual_cagr}, db={db_cagr}"

    conn.close()


def test_screener_preview_roe_gt_15_de_lt_1(ratio_engine_run):
    """
    Day 14 Review: Run screener preview: ROE > 15% and D/E < 1
    Verify result count is between 15 and 50 companies for the latest year.
    """
    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
    # Query distinct companies in 2024 meeting criteria
    query = """
        SELECT DISTINCT company_id, return_on_equity_pct, debt_to_equity
        FROM financial_ratios
        WHERE year = 2024
          AND return_on_equity_pct > 15.0
          AND debt_to_equity < 1.0;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    count = len(df)
    assert 15 <= count <= 50, f"Screener count for ROE > 15% & D/E < 1 in 2024 was {count} (expected 15 to 50)."


def test_deliverable_artifacts_generated(ratio_engine_run):
    """Verify output/capital_allocation.csv and output/ratio_edge_cases.log exist and are non-empty."""
    cap_alloc = OUTPUT_DIR / "capital_allocation.csv"
    edge_log = OUTPUT_DIR / "ratio_edge_cases.log"

    assert cap_alloc.exists(), "capital_allocation.csv does not exist"
    assert edge_log.exists(), "ratio_edge_cases.log does not exist"

    df_alloc = pd.read_csv(cap_alloc)
    assert len(df_alloc) > 1000, f"Expected > 1,000 rows in capital_allocation.csv, found {len(df_alloc)}"
    assert set(df_alloc.columns) == {"company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"}

    with open(edge_log, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert len(log_content) > 100, "ratio_edge_cases.log is empty"
    assert "data source issue" in log_content or "version difference" in log_content or "formula discrepancy" in log_content
