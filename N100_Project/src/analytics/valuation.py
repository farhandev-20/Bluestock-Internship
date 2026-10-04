"""
Valuation Analytics Module for N100 Intelligence Platform.
Computes FCF Yield, Sector Median P/E, 5-year Historical Median P/E,
Overvaluation / Undervaluation Flags (Caution / Discount / Fair),
and exports valuation_summary.xlsx and valuation_flags.csv.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_EXCEL_PATH = OUTPUT_DIR / "valuation_summary.xlsx"
DEFAULT_FLAGS_PATH = OUTPUT_DIR / "valuation_flags.csv"


def calculate_fcf_yield(
    free_cash_flow_cr: Optional[float],
    market_cap_crore: Optional[float],
) -> Optional[float]:
    """
    Compute FCF Yield (%): (FCF / Market Cap) * 100.
    Returns None if market_cap_crore is None or <= 0, or if FCF is None.
    """
    if free_cash_flow_cr is None or market_cap_crore is None or market_cap_crore <= 0:
        return None
    return (free_cash_flow_cr / market_cap_crore) * 100.0


def classify_valuation_flag(
    pe_ratio: Optional[float],
    sector_median_pe: Optional[float],
) -> str:
    """
    Apply valuation classification flags:
      - If P/E > sector_median * 1.5 -> 'Caution' (Overvalued)
      - If P/E < sector_median * 0.7 -> 'Discount' (Undervalued)
      - Otherwise -> 'Fair'
    If P/E or sector_median is missing/invalid, defaults to 'Fair'.
    """
    if pe_ratio is None or pd.isna(pe_ratio) or sector_median_pe is None or pd.isna(sector_median_pe) or sector_median_pe <= 0:
        return "Fair"

    if pe_ratio > sector_median_pe * 1.5:
        return "Caution"
    elif pe_ratio < sector_median_pe * 0.7:
        return "Discount"
    else:
        return "Fair"


def load_valuation_universe(
    db_path: Optional[Path] = None,
    target_year: int = 2024,
) -> pd.DataFrame:
    """
    Load merged valuation data from SQLite for all companies in target_year.
    Includes 5-year historical P/E median and sector benchmarks.
    """
    conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))

    # Base queries
    comp_df = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
    sec_df = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
    mcap_df = pd.read_sql_query("SELECT company_id, year, market_cap_crore, enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM market_cap", conn)
    ratios_df = pd.read_sql_query("SELECT company_id, year, free_cash_flow_cr FROM financial_ratios", conn)
    conn.close()

    # Deduplicate
    comp_df = comp_df.drop_duplicates(subset=["company_id"], keep="last")
    sec_df = sec_df.drop_duplicates(subset=["company_id"], keep="last")
    mcap_df = mcap_df.dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    ratios_df = ratios_df.dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")

    # Target year slices
    mcap_target = mcap_df[mcap_df["year"] == target_year].copy()
    ratios_target = ratios_df[ratios_df["year"] == target_year].copy()

    # 5-Year Historical Median P/E (target_year - 4 to target_year, e.g. 2020..2024)
    hist_5yr_mcap = mcap_df[
        (mcap_df["year"] >= (target_year - 4)) & (mcap_df["year"] <= target_year) & (mcap_df["pe_ratio"].notna()) & (mcap_df["pe_ratio"] > 0)
    ]
    pe_5yr_median_map = hist_5yr_mcap.groupby("company_id")["pe_ratio"].median().to_dict()

    # Merge master - inner join with target year market cap to get exactly 92 constituents
    merged = pd.merge(mcap_target, comp_df, on="company_id", how="left")
    merged = pd.merge(merged, sec_df, on="company_id", how="left")
    merged = pd.merge(merged, ratios_target[["company_id", "free_cash_flow_cr"]], on="company_id", how="left")

    # Sector name normalization
    merged["sector"] = merged["broad_sector"].fillna("Unassigned")

    # Compute FCF Yield (%)
    fcf_yields = []
    for _, row in merged.iterrows():
        fcf = row.get("free_cash_flow_cr")
        mcap = row.get("market_cap_crore")
        fcf_yields.append(calculate_fcf_yield(fcf, mcap))
    merged["FCF_yield_pct"] = fcf_yields

    # Compute Sector Median P/E (for companies with valid positive P/E in target year)
    valid_pe = merged[(merged["pe_ratio"].notna()) & (merged["pe_ratio"] > 0)]
    sector_median_pe_map = valid_pe.groupby("sector")["pe_ratio"].median().to_dict()

    # Compute flags, 5yr median PE, and PE vs sector median %
    flags = []
    pe_vs_sec_pct = []
    hist_5yr_pe_list = []

    for _, row in merged.iterrows():
        cid = row["company_id"]
        sec = row["sector"]
        pe = row.get("pe_ratio")
        sec_med = sector_median_pe_map.get(sec)

        # Flag
        flag = classify_valuation_flag(pe, sec_med)
        flags.append(flag)

        # PE vs Sector Median %
        if pe is not None and pd.notna(pe) and sec_med is not None and sec_med > 0:
            diff_pct = ((pe - sec_med) / sec_med) * 100.0
        else:
            diff_pct = None
        pe_vs_sec_pct.append(diff_pct)

        # 5-Year Historical Median
        hist_pe = pe_5yr_median_map.get(cid)
        if hist_pe is None and pe is not None and pd.notna(pe):
            hist_pe = pe
        hist_5yr_pe_list.append(hist_pe)

    merged["5yr_median_PE"] = hist_5yr_pe_list
    merged["PE_vs_sector_median_pct"] = pe_vs_sec_pct
    merged["flag"] = flags

    # Standard column aliases
    merged["P/E"] = merged["pe_ratio"]
    merged["P/B"] = merged["pb_ratio"]
    merged["EV/EBITDA"] = merged["ev_ebitda"]

    # Select final columns in order
    final_cols = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]
    return merged[final_cols]


def export_valuation_summary_excel(
    val_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate output/valuation_summary.xlsx formatted with Excel styling,
    color-coded valuation flags (Caution = Soft Red, Discount = Soft Green, Fair = Soft Blue/Gray).
    """
    target_path = Path(output_path or DEFAULT_EXCEL_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Valuation Summary"
    ws.views.sheetView[0].showGridLines = True

    # Styling definitions
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    caution_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")  # Soft red/orange
    caution_font = Font(name="Calibri", size=11, bold=True, color="C00000")

    discount_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # Soft green
    discount_font = Font(name="Calibri", size=11, bold=True, color="375623")

    fair_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    fair_font = Font(name="Calibri", size=11, color="595959")

    border_thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    columns_meta = [
        ("company_id", "Company ID", "@", "left"),
        ("company_name", "Company Name", "@", "left"),
        ("sector", "Sector", "@", "left"),
        ("P/E", "P/E", "0.00", "right"),
        ("P/B", "P/B", "0.00", "right"),
        ("EV/EBITDA", "EV/EBITDA", "0.00", "right"),
        ("FCF_yield_pct", "FCF Yield (%)", "0.00%", "right"),
        ("5yr_median_PE", "5Yr Median P/E", "0.00", "right"),
        ("PE_vs_sector_median_pct", "P/E vs Sector (%)", "0.00%", "right"),
        ("flag", "Valuation Flag", "@", "center"),
    ]

    # Write Headers
    for c_idx, (_, label, _, align) in enumerate(columns_meta, start=1):
        cell = ws.cell(row=1, column=c_idx, value=label)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Write Data Rows
    for r_idx, (_, row) in enumerate(val_df.iterrows(), start=2):
        flag = str(row.get("flag", "Fair"))
        for c_idx, (col_key, _, num_fmt, align) in enumerate(columns_meta, start=1):
            val = row.get(col_key)
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = border_thin
            cell.alignment = Alignment(horizontal=align, vertical="center")

            if pd.isna(val) or val is None:
                cell.value = "-"
            elif isinstance(val, (int, float)):
                if "%" in num_fmt:
                    cell.value = val / 100.0
                    cell.number_format = num_fmt
                else:
                    cell.value = val
                    cell.number_format = num_fmt
            else:
                cell.value = str(val)

            # Flag cell styling
            if col_key == "flag":
                if flag == "Caution":
                    cell.fill = caution_fill
                    cell.font = caution_font
                elif flag == "Discount":
                    cell.fill = discount_fill
                    cell.font = discount_font
                else:
                    cell.fill = fair_fill
                    cell.font = fair_font

    # Column widths
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 13)

    wb.save(target_path)
    return target_path


def export_valuation_flags_csv(
    val_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate output/valuation_flags.csv containing only companies flagged
    as Caution or Discount with all supporting metrics.
    """
    target_path = Path(output_path or DEFAULT_FLAGS_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    flagged_df = val_df[val_df["flag"].isin(["Caution", "Discount"])].copy()
    flagged_df.to_csv(target_path, index=False)
    return target_path


def run_valuation_module(
    db_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    target_year: int = 2024,
) -> Dict[str, Any]:
    """
    Executes end-to-end valuation pipeline:
    1. Loads valuation data for all 92 companies.
    2. Exports output/valuation_summary.xlsx.
    3. Exports output/valuation_flags.csv.
    """
    out_dir = Path(output_dir or OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    val_df = load_valuation_universe(db_path=db_path, target_year=target_year)
    xlsx_path = export_valuation_summary_excel(val_df, output_path=out_dir / "valuation_summary.xlsx")
    csv_path = export_valuation_flags_csv(val_df, output_path=out_dir / "valuation_flags.csv")

    flag_counts = val_df["flag"].value_counts().to_dict()

    return {
        "total_companies": len(val_df),
        "excel_path": xlsx_path,
        "csv_path": csv_path,
        "flags_breakdown": flag_counts,
    }


if __name__ == "__main__":
    print("Executing Valuation Module...")
    res = run_valuation_module()
    print(f"Computed valuation metrics for {res['total_companies']} companies.")
    print(f"Flags Breakdown: {res['flags_breakdown']}")
    print(f"Valuation Summary Excel: {res['excel_path']}")
    print(f"Valuation Flags CSV: {res['csv_path']}")
