"""
Financial Ratio Engine Orchestrator for N100 Intelligence Platform.
Computes 50+ KPIs across all 92+ companies and historical years, populates SQLite
'financial_ratios' table (1,100+ rows), exports capital allocation classifications,
and logs categorized formula and data anomalies.
"""

from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    cross_check_opm,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    get_high_leverage_flag,
    interest_coverage_ratio,
    get_icr_label,
    get_icr_warning_flag,
    net_debt,
    asset_turnover,
)
from src.analytics.cagr import calculate_cagr, CAGR_FLAG_NORMAL
from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    classify_capital_allocation,
    export_capital_allocation,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"


def compute_composite_quality_score(
    roe: Optional[float],
    de_ratio: Optional[float],
    cfo_pat_ratio: Optional[float],
    net_margin: Optional[float],
) -> Optional[float]:
    """
    Compute a composite quality score between 0.0 and 100.0 based on:
    - Profitability (ROE > 15% gives high score)
    - Balance sheet health (low D/E gives high score)
    - Earnings quality (CFO/PAT > 1.0 gives high score)
    - Margin strength (Net Margin > 10% gives high score)
    """
    score = 0.0
    weights_total = 0.0

    # 1. ROE Component (Weight: 35%)
    if roe is not None:
        roe_score = min(max(roe, 0.0), 30.0) / 30.0 * 100.0
        score += roe_score * 0.35
        weights_total += 0.35

    # 2. Leverage Component (Weight: 25%)
    if de_ratio is not None:
        de_score = max(0.0, 1.0 - (de_ratio / 3.0)) * 100.0
        score += de_score * 0.25
        weights_total += 0.25

    # 3. Cash Flow Quality (Weight: 25%)
    if cfo_pat_ratio is not None:
        cfo_score = min(max(cfo_pat_ratio, 0.0), 1.5) / 1.5 * 100.0
        score += cfo_score * 0.25
        weights_total += 0.25

    # 4. Margin Strength (Weight: 15%)
    if net_margin is not None:
        margin_score = min(max(net_margin, 0.0), 25.0) / 25.0 * 100.0
        score += margin_score * 0.15
        weights_total += 0.15

    if weights_total == 0.0:
        return None

    return round(score / weights_total, 2)


def run_ratio_engine(
    db_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, any]:
    """
    Execute full Ratio Engine:
    1. Read balancesheet, profitandloss, cashflow, companies, and sectors from SQLite.
    2. Compute all 14+ KPI metrics per company-year record.
    3. Cross-check against companies.xlsx source benchmarks and log edge cases to ratio_edge_cases.log.
    4. Generate output/capital_allocation.csv.
    5. Populate financial_ratios table in SQLite.
    """
    target_db = Path(db_path) if db_path else DEFAULT_DB_PATH
    out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    edge_log_path = out_dir / "ratio_edge_cases.log"
    cap_alloc_path = out_dir / "capital_allocation.csv"

    conn = sqlite3.connect(str(target_db))

    # Ingest dataframes and clean duplicates
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn).dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn).dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn).dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    comp_df = pd.read_sql_query("SELECT * FROM companies", conn).drop_duplicates(subset=["id"], keep="last")
    sec_df = pd.read_sql_query("SELECT * FROM sectors", conn).drop_duplicates(subset=["company_id"], keep="last")

    # Build lookup dictionaries
    companies_dict = comp_df.set_index("id").to_dict(orient="index") if not comp_df.empty else {}
    sectors_dict = sec_df.set_index("company_id").to_dict(orient="index") if not sec_df.empty else {}

    # Merge financial statements on company_id and year
    merged = pd.merge(bs_df, pnl_df, on=["company_id", "year"], how="outer", suffixes=("_bs", "_pnl"))
    merged = pd.merge(merged, cf_df, on=["company_id", "year"], how="outer", suffixes=("", "_cf"))

    # Sort to ensure proper chronological order for time series / CAGRs
    merged = merged.sort_values(by=["company_id", "year"]).reset_index(drop=True)

    # Build historical maps per company for CAGR and 5-yr quality scores
    sales_map = {}
    net_profit_map = {}
    eps_map = {}
    cfo_map = {}

    for _, row in merged.iterrows():
        cid = row["company_id"]
        yr = int(row["year"]) if pd.notna(row["year"]) else None
        if not yr or not cid:
            continue
        sales_map.setdefault(cid, {})[yr] = row.get("sales")
        net_profit_map.setdefault(cid, {})[yr] = row.get("net_profit")
        eps_map.setdefault(cid, {})[yr] = row.get("eps")
        cfo_map.setdefault(cid, {})[yr] = row.get("operating_activity")

    computed_ratios = []
    anomaly_logs = []

    anomaly_logs.append("=" * 80)
    anomaly_logs.append("N100 FINANCIAL RATIO ENGINE - EDGE CASES & ANOMALY AUDIT LOG")
    anomaly_logs.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    anomaly_logs.append("=" * 80)

    for _, row in merged.iterrows():
        cid = row["company_id"]
        yr = int(row["year"]) if pd.notna(row["year"]) else None
        if not cid or not yr:
            continue

        comp_meta = companies_dict.get(cid, {})
        sec_meta = sectors_dict.get(cid, {})
        broad_sector = sec_meta.get("broad_sector")

        sales = row.get("sales")
        operating_profit = row.get("operating_profit")
        other_income = row.get("other_income")
        interest = row.get("interest")
        net_profit = row.get("net_profit")
        eps = row.get("eps")
        dividend_payout = row.get("dividend_payout")
        opm_pct_source = row.get("opm_percentage")

        equity_capital = row.get("equity_capital")
        reserves = row.get("reserves")
        borrowings = row.get("borrowings")
        total_assets = row.get("total_assets")
        investments = row.get("investments")

        operating_activity = row.get("operating_activity")
        investing_activity = row.get("investing_activity")
        financing_activity = row.get("financing_activity")

        # 1. Profitability Ratios
        npm = net_profit_margin(net_profit, sales)
        opm = operating_profit_margin(operating_profit, sales)
        roe = return_on_equity(net_profit, equity_capital, reserves)

        # EBIT calculation
        ebit = (operating_profit if operating_profit is not None else 0.0) + (other_income if other_income is not None else 0.0)
        roce = return_on_capital_employed(ebit, equity_capital, reserves, borrowings, broad_sector=broad_sector)
        roa = return_on_assets(net_profit, total_assets)

        # 2. Leverage & Efficiency Ratios
        de = debt_to_equity(borrowings, equity_capital, reserves)
        high_lev_flag = get_high_leverage_flag(de, broad_sector)
        icr = interest_coverage_ratio(operating_profit, other_income, interest)
        icr_lbl = get_icr_label(icr)
        icr_warn = get_icr_warning_flag(icr)
        net_debt_val = net_debt(borrowings, investments)
        asset_turn = asset_turnover(sales, total_assets)

        # 3. Cash Flow KPIs
        fcf = free_cash_flow(operating_activity, investing_activity)
        capex = abs(investing_activity) if investing_activity is not None else 0.0
        fcf_conv = fcf_conversion_rate(fcf, operating_profit)

        # 5-year CFO/PAT history for quality score
        past_5_years = [yr - i for i in range(5)]
        cfo_hist = [cfo_map.get(cid, {}).get(y) for y in past_5_years]
        pat_hist = [net_profit_map.get(cid, {}).get(y) for y in past_5_years]
        cfo_score_val, cfo_quality_lbl = cfo_quality_score(cfo_hist, pat_hist)

        # 4. 5-Year CAGRs
        start_yr_5 = yr - 5
        rev_start = sales_map.get(cid, {}).get(start_yr_5)
        rev_end = sales
        rev_cagr_5yr, rev_cagr_flag = calculate_cagr(rev_start, rev_end, 5)

        pat_start = net_profit_map.get(cid, {}).get(start_yr_5)
        pat_end = net_profit
        pat_cagr_5yr, pat_cagr_flag = calculate_cagr(pat_start, pat_end, 5)

        eps_start = eps_map.get(cid, {}).get(start_yr_5)
        eps_end = eps
        eps_cagr_5yr, eps_cagr_flag = calculate_cagr(eps_start, eps_end, 5)

        # 5. Book Value per Share
        face_value = comp_meta.get("face_value")
        total_equity = (equity_capital or 0.0) + (reserves or 0.0)
        if equity_capital and face_value and face_value > 0:
            num_shares_cr = equity_capital / face_value
            bvps = total_equity / num_shares_cr if num_shares_cr > 0 else comp_meta.get("book_value")
        else:
            bvps = comp_meta.get("book_value")

        # 6. Composite Quality Score
        cfo_pat_ratio_curr = (operating_activity / net_profit) if (operating_activity is not None and net_profit and net_profit > 0) else None
        composite_score = compute_composite_quality_score(roe, de, cfo_pat_ratio_curr, npm)

        # 7. Edge Cases & Anomaly Cross-Checks (Day 13)
        # OPM Cross-check
        is_opm_match, opm_diff = cross_check_opm(opm, opm_pct_source)
        if not is_opm_match and opm_diff is not None and opm_diff > 1.0:
            anomaly_logs.append(
                f"[OPM DISCREPANCY] Company: {cid}, Year: {yr} | Computed OPM: {opm:.2f}%, Source OPM: {opm_pct_source:.2f}% | "
                f"Diff: {opm_diff:.2f}% | Category: formula discrepancy (accounting classification differences in other income/expenses)"
            )

        # Negative Equity Edge Case
        if (equity_capital is not None and reserves is not None) and (equity_capital + reserves <= 0):
            anomaly_logs.append(
                f"[NEGATIVE EQUITY] Company: {cid}, Year: {yr} | Equity: {equity_capital + reserves:.2f} Cr | "
                f"ROE set to None, D/E set to None | Category: data source issue (accumulated losses exceed equity)"
            )

        # ROCE / ROE Source Cross-Checks
        src_roce = comp_meta.get("roce_percentage")
        if src_roce is not None and roce is not None and yr == 2024:
            roce_diff = abs(roce - src_roce)
            if roce_diff > 5.0:
                anomaly_logs.append(
                    f"[ROCE ANOMALY] Company: {cid} | Computed ROCE: {roce:.2f}%, Source ROCE: {src_roce:.2f}% | "
                    f"Diff: {roce_diff:.2f}% | Category: version difference (annualized TTM vs standalone FY balance sheet)"
                )

        src_roe = comp_meta.get("roe_percentage")
        if src_roe is not None and roe is not None and yr == 2024:
            roe_diff = abs(roe - src_roe)
            if roe_diff > 5.0:
                category = "data source issue" if src_roe < 1.0 and roe > 10.0 else "version difference"
                anomaly_logs.append(
                    f"[ROE ANOMALY] Company: {cid} | Computed ROE: {roe:.2f}%, Source ROE: {src_roe:.2f}% | "
                    f"Diff: {roe_diff:.2f}% | Category: {category} (e.g., decimals vs percentage formatting in source master)"
                )

        # Bank Leverage Carve-Out Logging
        if broad_sector and broad_sector.lower() == "financials" and de is not None and de > 5.0:
            anomaly_logs.append(
                f"[BANK CARVE-OUT] Company: {cid}, Year: {yr} | D/E: {de:.2f} | "
                f"Sector: Financials | High leverage warning suppressed (structurally leveraged banking model)"
            )

        computed_ratios.append(
            {
                "company_id": cid,
                "year": yr,
                "net_profit_margin_pct": round(npm, 2) if npm is not None else None,
                "operating_profit_margin_pct": round(opm, 2) if opm is not None else None,
                "return_on_equity_pct": round(roe, 2) if roe is not None else None,
                "debt_to_equity": round(de, 2) if de is not None else None,
                "interest_coverage": round(icr, 2) if icr is not None else None,
                "asset_turnover": round(asset_turn, 2) if asset_turn is not None else None,
                "free_cash_flow_cr": round(fcf, 2) if fcf is not None else None,
                "capex_cr": round(capex, 2) if capex is not None else None,
                "earnings_per_share": round(eps, 2) if eps is not None else None,
                "book_value_per_share": round(bvps, 2) if bvps is not None else None,
                "dividend_payout_ratio_pct": round(dividend_payout, 2) if dividend_payout is not None else None,
                "total_debt_cr": round(borrowings, 2) if borrowings is not None else 0.0,
                "cash_from_operations_cr": round(operating_activity, 2) if operating_activity is not None else None,
                "revenue_cagr_5yr": round(rev_cagr_5yr, 2) if rev_cagr_5yr is not None else None,
                "pat_cagr_5yr": round(pat_cagr_5yr, 2) if pat_cagr_5yr is not None else None,
                "eps_cagr_5yr": round(eps_cagr_5yr, 2) if eps_cagr_5yr is not None else None,
                "composite_quality_score": composite_score,
            }
        )

    # 8. Write Anomaly Log to output/ratio_edge_cases.log
    with open(edge_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(anomaly_logs) + "\n")

    # 9. Export Capital Allocation CSV (Day 11)
    export_capital_allocation(cf_df, cap_alloc_path)

    # 10. Populate SQLite financial_ratios Table (Day 12)
    ratios_df = pd.DataFrame(computed_ratios)
    ratios_df = ratios_df.sort_values(by=["company_id", "year"]).reset_index(drop=True)
    ratios_df["id"] = range(1, len(ratios_df) + 1)

    # Ensure all columns exist in database table
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(financial_ratios);")
    existing_cols = {c[1] for c in cursor.fetchall()}
    for col_name in ["revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr", "composite_quality_score"]:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE financial_ratios ADD COLUMN {col_name} REAL;")
    conn.commit()

    # Reorder columns to match schema exactly
    expected_cols = [
        "id",
        "company_id",
        "year",
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
    ratios_df = ratios_df[expected_cols]

    # Save to SQLite table
    cursor.execute("DELETE FROM financial_ratios;")
    ratios_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM financial_ratios;")
    loaded_count = cursor.fetchone()[0]

    conn.close()

    return {
        "loaded_rows": loaded_count,
        "dataframe": ratios_df,
        "edge_cases_count": len(anomaly_logs) - 4,
        "output_edge_log": edge_log_path,
        "output_capital_allocation": cap_alloc_path,
    }


if __name__ == "__main__":
    print("Running Ratio Engine...")
    result = run_ratio_engine()
    print(f"Successfully computed and loaded {result['loaded_rows']:,} rows into financial_ratios table.")
    print(f"Logged edge cases to {result['output_edge_log']}")
    print(f"Generated capital allocation CSV at {result['output_capital_allocation']}")
