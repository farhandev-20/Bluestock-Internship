"""
Cash Flow KPIs, Capital Allocation & Cash Flow Intelligence Module for N100 Intelligence Platform.
Implements Free Cash Flow, CFO Quality Score, CapEx Intensity, FCF Conversion Rate,
Distress Signal detection, Deleveraging Flag, Capital Allocation 8-Pattern Classifier,
and exports cashflow_intelligence.xlsx, distress_alerts.csv, and pattern_changes.csv.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_INTEL_XLSX = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DEFAULT_DISTRESS_CSV = OUTPUT_DIR / "distress_alerts.csv"
DEFAULT_PATTERN_CSV = OUTPUT_DIR / "pattern_changes.csv"
DEFAULT_CAP_ALLOC_CSV = OUTPUT_DIR / "capital_allocation.csv"


# ==============================================================================
# Core Cash Flow KPI Calculation Functions
# ==============================================================================

def free_cash_flow(
    operating_activity: Optional[float], investing_activity: Optional[float]
) -> Optional[float]:
    """
    Compute Free Cash Flow (FCF): operating_activity + investing_activity.
    In standard accounting statements, investing_activity is usually negative (CapEx outflow),
    so sum represents net free cash flow. Negative values are allowed.
    """
    if operating_activity is None and investing_activity is None:
        return None
    cfo = operating_activity if operating_activity is not None else 0.0
    cfi = investing_activity if investing_activity is not None else 0.0
    return cfo + cfi


def cfo_quality_score(
    cfo_series: Sequence[Optional[float]], pat_series: Sequence[Optional[float]]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Compute CFO Quality Score: CFO / PAT ratio averaged over 5 years.
    Classifications:
      - > 1.0   -> 'High Quality'
      - 0.5-1.0 -> 'Moderate'
      - < 0.5   -> 'Accrual Risk'
    Returns (score, category). If total PAT == 0 or no valid pairs, returns (None, None).
    """
    valid_ratios = []
    for cfo, pat in zip(cfo_series, pat_series):
        if cfo is not None and pat is not None and pat > 0:
            valid_ratios.append(cfo / pat)
        elif cfo is not None and pat is not None and pat < 0:
            # When PAT is negative and CFO is negative, ratio is tricky; treat as accrual risk
            valid_ratios.append(-1.0 if cfo < 0 else 0.0)

    if not valid_ratios:
        return None, None

    avg_score = sum(valid_ratios) / len(valid_ratios)

    if avg_score > 1.0:
        label = "High Quality"
    elif avg_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_score, label


def capex_intensity(
    investing_activity: Optional[float], sales: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Compute CapEx Intensity: abs(investing_activity) / sales * 100.
    Classifications:
      - < 3%   -> 'Asset Light'
      - 3%-8%  -> 'Moderate'
      - > 8%   -> 'Capital Intensive'
    Returns (intensity_pct, category). Returns (None, None) if sales <= 0 or missing.
    """
    if investing_activity is None or sales is None or sales <= 0:
        return None, None

    intensity = (abs(investing_activity) / sales) * 100.0

    if intensity < 3.0:
        category = "Asset Light"
    elif intensity <= 8.0:
        category = "Moderate"
    else:
        category = "Capital Intensive"

    return intensity, category


def fcf_conversion_rate(
    fcf: Optional[float], operating_profit: Optional[float]
) -> Optional[float]:
    """
    Compute FCF Conversion Rate: (FCF / operating_profit) * 100.
    Returns None if operating_profit is None or operating_profit == 0.
    """
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100.0


# ==============================================================================
# Capital Allocation 8-Pattern Classifier
# ==============================================================================

def classify_capital_allocation(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_pat_ratio: Optional[float] = None,
) -> Tuple[str, str, str, str]:
    """
    Classify company capital allocation pattern based on sign of (CFO, CFI, CFF).
    
    8 Pattern Classifications:
      (+, -, -) -> Reinvestor (or Shareholder Returns if high CFO/PAT ratio)
      (+, +, -) -> Liquidating Assets
      (-, +, +) -> Distress Signal
      (-, -, +) -> Growth Funded by Debt
      (+, +, +) -> Cash Accumulator
      (-, -, -) -> Pre-Revenue
      (+, -, +) -> Mixed
      (-, +, -) -> Distress Signal

    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).
    """
    cfo_val = cfo if cfo is not None else 0.0
    cfi_val = cfi if cfi is not None else 0.0
    cff_val = cff if cff is not None else 0.0

    s_cfo = "+" if cfo_val >= 0 else "-"
    s_cfi = "+" if cfi_val >= 0 else "-"
    s_cff = "+" if cff_val >= 0 else "-"

    pattern_key = (s_cfo, s_cfi, s_cff)

    if pattern_key == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.2:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif pattern_key == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif pattern_key == ("-", "+", "+"):
        label = "Distress Signal"
    elif pattern_key == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif pattern_key == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif pattern_key == ("-", "-", "-"):
        label = "Pre-Revenue"
    elif pattern_key == ("+", "-", "+"):
        label = "Mixed"
    elif pattern_key == ("-", "+", "-"):
        label = "Distress Signal"
    else:
        label = "Mixed"

    return s_cfo, s_cfi, s_cff, label


def export_capital_allocation(
    cashflow_df: pd.DataFrame, output_path: Union[str, Path]
) -> pd.DataFrame:
    """
    Generate output/capital_allocation.csv with columns:
    company_id, year, cfo_sign, cfi_sign, cff_sign, pattern_label
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for _, row in cashflow_df.iterrows():
        cid = row.get("company_id")
        yr = row.get("year")
        cfo = row.get("operating_activity")
        cfi = row.get("investing_activity")
        cff = row.get("financing_activity")

        s_cfo, s_cfi, s_cff, label = classify_capital_allocation(cfo, cfi, cff)
        records.append(
            {
                "company_id": cid,
                "year": yr,
                "cfo_sign": s_cfo,
                "cfi_sign": s_cfi,
                "cff_sign": s_cff,
                "pattern_label": label,
            }
        )

    out_df = pd.DataFrame(records)
    out_df.to_csv(out_file, index=False)
    return out_df


# ==============================================================================
# Sprint 5: Cash Flow Intelligence & Reports
# ==============================================================================

def generate_cashflow_intelligence(
    db_path: Optional[Path] = None,
    output_excel: Optional[Path] = None,
    output_distress: Optional[Path] = None,
    output_pattern_changes: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates:
    1. output/cashflow_intelligence.xlsx (92 Nifty 100 companies with full metrics)
    2. output/distress_alerts.csv (flagged companies with CFO < 0 and CFF > 0)
    3. output/pattern_changes.csv (companies changing capital allocation YoY)
    """
    target_db = Path(db_path or DEFAULT_DB_PATH)
    target_xlsx = Path(output_excel or DEFAULT_INTEL_XLSX)
    target_distress_csv = Path(output_distress or DEFAULT_DISTRESS_CSV)
    target_changes_csv = Path(output_pattern_changes or DEFAULT_PATTERN_CSV)

    target_xlsx.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_db))
    sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()

    # Re-export capital allocation CSV to ensure 100% sync
    export_capital_allocation(cf_df, DEFAULT_CAP_ALLOC_CSV)
    cap_alloc_df = pd.read_csv(DEFAULT_CAP_ALLOC_CSV)

    # 1. Process 92 Nifty 100 Companies in sectors
    intel_rows = []
    distress_alerts = []

    # Get the 92 companies present in sectors table (or all if empty)
    target_companies = sectors_df["company_id"].tolist() if not sectors_df.empty else cf_df["company_id"].unique().tolist()

    for cid in target_companies:
        c_cf = cf_df[cf_df["company_id"] == cid].sort_values("year")
        c_pnl = pnl_df[pnl_df["company_id"] == cid].sort_values("year")
        c_bs = bs_df[bs_df["company_id"] == cid].sort_values("year")
        c_ratios = ratios_df[ratios_df["company_id"] == cid].sort_values("year")
        c_sec = sectors_df[sectors_df["company_id"] == cid]

        sector_name = c_sec.iloc[0]["broad_sector"] if not c_sec.empty else "Unknown"

        if c_cf.empty:
            continue

        # Latest year data
        latest_cf = c_cf.iloc[-1]
        latest_year = latest_cf["year"]
        latest_cfo = latest_cf.get("operating_activity", 0.0) or 0.0
        latest_cfi = latest_cf.get("investing_activity", 0.0) or 0.0
        latest_cff = latest_cf.get("financing_activity", 0.0) or 0.0

        # Match latest P&L and Balance Sheet
        c_pnl_latest = c_pnl[c_pnl["year"] == latest_year]
        latest_sales = c_pnl_latest.iloc[0].get("sales", 0.0) if not c_pnl_latest.empty else 0.0
        latest_pat = c_pnl_latest.iloc[0].get("net_profit", 0.0) if not c_pnl_latest.empty else 0.0
        latest_op = c_pnl_latest.iloc[0].get("operating_profit", 0.0) if not c_pnl_latest.empty else 0.0

        # 5-year series for CFO Quality
        last5_cf = c_cf.tail(5)
        last5_pnl = c_pnl[c_pnl["year"].isin(last5_cf["year"])].sort_values("year")
        cfo_5yr = last5_cf["operating_activity"].tolist()
        pat_5yr = last5_pnl["net_profit"].tolist() if not last5_pnl.empty else []

        q_score, q_label = cfo_quality_score(cfo_5yr, pat_5yr)
        if q_score is None:
            q_score = 1.0
            q_label = "Moderate"

        # CapEx Intensity
        capex_pct, capex_lab = capex_intensity(latest_cfi, latest_sales)
        if capex_pct is None:
            capex_pct = 0.0
            capex_lab = "Asset Light"

        # FCF and Conversion
        latest_fcf = free_cash_flow(latest_cfo, latest_cfi) or 0.0
        
        # 5-year average FCF
        fcf_5yr_vals = []
        for _, cf_row in last5_cf.iterrows():
            fcf_val = free_cash_flow(cf_row.get("operating_activity"), cf_row.get("investing_activity"))
            if fcf_val is not None:
                fcf_5yr_vals.append(fcf_val)
        fcf_avg = np.mean(fcf_5yr_vals) if fcf_5yr_vals else latest_fcf

        # FCF Conversion Rate
        conv_rate = fcf_conversion_rate(latest_fcf, latest_op)
        if conv_rate is None or np.isnan(conv_rate):
            conv_rate = 0.0

        # Distress Signal: CFO < 0 AND CFF > 0 in latest year
        distress_flag = (latest_cfo < 0) and (latest_cff > 0)

        # Deleveraging Flag: CFF < 0 AND borrowings declining year-over-year
        deleveraging_flag = False
        if len(c_bs) >= 2 and latest_cff < 0:
            latest_borrowings = c_bs.iloc[-1].get("borrowings", 0.0) or 0.0
            prev_borrowings = c_bs.iloc[-2].get("borrowings", 0.0) or 0.0
            if latest_borrowings < prev_borrowings:
                deleveraging_flag = True

        # Capital Allocation pattern for latest year
        _, _, _, cap_alloc_label = classify_capital_allocation(latest_cfo, latest_cfi, latest_cff, q_score)

        intel_rows.append({
            "company_id": cid,
            "sector": sector_name,
            "cfo_quality_score": round(q_score, 2),
            "cfo_quality_label": q_label,
            "capex_intensity_pct": round(capex_pct, 2),
            "capex_label": capex_lab,
            "fcf_avg": round(fcf_avg, 2),
            "fcf_conversion_pct": round(conv_rate, 2),
            "distress_flag": bool(distress_flag),
            "deleveraging_flag": bool(deleveraging_flag),
            "capital_allocation": cap_alloc_label,
        })

        if distress_flag:
            distress_alerts.append({
                "company_id": cid,
                "sector": sector_name,
                "cfo_value": round(latest_cfo, 2),
                "cff_value": round(latest_cff, 2),
                "latest_net_profit": round(latest_pat, 2),
            })

    intel_df = pd.DataFrame(intel_rows)
    distress_df = pd.DataFrame(distress_alerts)

    # 2. Build Pattern Changes Report (YoY)
    pattern_change_records = []
    for cid in target_companies:
        c_alloc = cap_alloc_df[cap_alloc_df["company_id"] == cid].sort_values("year")
        if len(c_alloc) >= 2:
            prev_row = c_alloc.iloc[-2]
            curr_row = c_alloc.iloc[-1]
            if prev_row["pattern_label"] != curr_row["pattern_label"]:
                pattern_change_records.append({
                    "company_id": cid,
                    "previous_year": int(prev_row["year"]),
                    "previous_pattern": prev_row["pattern_label"],
                    "current_year": int(curr_row["year"]),
                    "current_pattern": curr_row["pattern_label"],
                    "change_type": f"{prev_row['pattern_label']} -> {curr_row['pattern_label']}",
                })

    pattern_changes_df = pd.DataFrame(pattern_change_records)

    # Save all output files
    with pd.ExcelWriter(target_xlsx, engine="openpyxl") as writer:
        intel_df.to_excel(writer, sheet_name="CashFlow_Intelligence", index=False)
        # Also write summary distribution of 8 patterns
        dist_df = intel_df["capital_allocation"].value_counts().reset_index()
        dist_df.columns = ["Capital_Allocation_Pattern", "Company_Count"]
        dist_df.to_excel(writer, sheet_name="Pattern_Distribution", index=False)

    distress_df.to_csv(target_distress_csv, index=False)
    pattern_changes_df.to_csv(target_changes_csv, index=False)

    return intel_df, distress_df, pattern_changes_df


if __name__ == "__main__":
    print("Executing Cash Flow Intelligence Module...")
    intel, distress, changes = generate_cashflow_intelligence()
    print(f"Generated Cash Flow Intelligence Excel with {len(intel)} companies -> output/cashflow_intelligence.xlsx")
    print(f"Found {len(distress)} distress signals -> output/distress_alerts.csv")
    print(f"Tracked {len(changes)} pattern changes YoY -> output/pattern_changes.csv")
