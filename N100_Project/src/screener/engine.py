"""
Financial Screener Engine for N100 Intelligence Platform.
Implements flexible multi-metric filtering, bank leverage carve-outs, debt-free ICR infinity,
P10/P90 winsorised sector-relative composite scoring, 6 preset screeners, and color-coded Excel export.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from src.screener.config_loader import load_screener_config
from src.analytics.cagr import calculate_cagr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_EXCEL_PATH = OUTPUT_DIR / "screener_output.xlsx"


def load_screener_universe(
    db_path: Optional[Path] = None,
    target_year: int = 2024,
) -> pd.DataFrame:
    """
    Ingest and merge all financial statements, valuation, sector, and ratio data
    for the latest constituent universe (target_year).
    """
    conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))

    # 1. Base tables
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    mcap_df = pd.read_sql_query("SELECT * FROM market_cap", conn)
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    comp_df = pd.read_sql_query("SELECT * FROM companies", conn)
    sec_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()

    # Deduplicate statement records
    ratios_df = ratios_df.dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    mcap_df = mcap_df.dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    pnl_df = pnl_df.dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    bs_df = bs_df.dropna(subset=["company_id", "year"]).drop_duplicates(subset=["company_id", "year"], keep="last")
    comp_df = comp_df.drop_duplicates(subset=["id"], keep="last")
    sec_df = sec_df.drop_duplicates(subset=["company_id"], keep="last")

    # Filter for target_year (or max available year per company)
    ratios_target = ratios_df[ratios_df["year"] == target_year].copy()
    mcap_target = mcap_df[mcap_df["year"] == target_year].copy()
    pnl_target = pnl_df[pnl_df["year"] == target_year].copy()
    bs_target = bs_df[bs_df["year"] == target_year].copy()

    # Merge target year records
    merged = pd.merge(comp_df[["id", "company_name", "book_value", "roce_percentage", "roe_percentage"]], 
                      sec_df[["company_id", "broad_sector", "sub_sector", "index_weight_pct", "market_cap_category"]], 
                      left_on="id", right_on="company_id", how="left")
    
    merged = pd.merge(merged, ratios_target, on="company_id", how="inner")
    merged = pd.merge(merged, mcap_target[["company_id", "market_cap_crore", "enterprise_value_crore", "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"]], 
                      on="company_id", how="left")
    merged = pd.merge(merged, pnl_target[["company_id", "sales", "operating_profit", "other_income", "interest", "net_profit", "tax_percentage"]], 
                      on="company_id", how="left")
    merged = pd.merge(merged, bs_target[["company_id", "equity_capital", "reserves", "borrowings", "total_assets", "investments"]], 
                      on="company_id", how="left")

    # Compute additional historical metrics for Turnaround preset:
    # 1. 3-year Revenue CAGR (target_year vs target_year - 3)
    # 2. YoY D/E change (target_year D/E < target_year - 1 D/E)
    pnl_3yr_prior = pnl_df[pnl_df["year"] == (target_year - 3)].set_index("company_id")["sales"].to_dict()
    ratios_1yr_prior = ratios_df[ratios_df["year"] == (target_year - 1)].set_index("company_id")["debt_to_equity"].to_dict()

    rev_cagr_3yr_list = []
    de_declining_list = []

    for _, row in merged.iterrows():
        cid = row["company_id"]
        curr_sales = row.get("sales")
        prior_sales = pnl_3yr_prior.get(cid)
        cagr_3, _ = calculate_cagr(prior_sales, curr_sales, 3)
        rev_cagr_3yr_list.append(cagr_3)

        curr_de = row.get("debt_to_equity")
        prior_de = ratios_1yr_prior.get(cid)
        if curr_de is not None and prior_de is not None:
            de_declining_list.append(curr_de < prior_de or (curr_de == 0.0 and prior_de == 0.0))
        else:
            de_declining_list.append(False)

    merged["revenue_cagr_3yr"] = rev_cagr_3yr_list
    merged["de_declining_yoy"] = de_declining_list

    # Compute Winsorised Composite Quality Score (Day 17)
    merged = compute_winsorised_composite_score(merged)

    return merged


def winsorise_and_scale(series: pd.Series, lower_p: float = 10.0, upper_p: float = 90.0, invert: bool = False) -> pd.Series:
    """
    Winsorises series between lower_p and upper_p percentiles, then scales to 0–100.
    If invert=True, lower original values yield higher scores (e.g. for Debt-to-Equity).
    """
    valid = series.dropna()
    if len(valid) == 0:
        return pd.Series(50.0, index=series.index)

    p_low = np.percentile(valid, lower_p)
    p_high = np.percentile(valid, upper_p)

    if p_high == p_low:
        return pd.Series(50.0, index=series.index)

    clipped = series.clip(lower=p_low, upper=p_high)
    scaled = (clipped - p_low) / (p_high - p_low) * 100.0

    if invert:
        scaled = 100.0 - scaled

    return scaled.fillna(50.0)


def compute_winsorised_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute P10/P90 winsorised, sector-relative composite quality score (0 to 100 scale):
    - 35% Profitability: ROE (15%) + ROCE (10%) + NPM (10%)
    - 30% Cash Quality: FCF Score (15%) + CFO/PAT ratio (10%) + FCF positive flag (5%)
    - 20% Growth: Revenue CAGR 5yr (10%) + PAT CAGR 5yr (10%)
    - 15% Leverage: D/E Score (10%, inverted) + ICR Score (5%)
    """
    out_df = df.copy()

    # Derived ROCE if not in dataframe
    if "roce_percentage" not in out_df.columns:
        ebit = (out_df["operating_profit"].fillna(0)) + (out_df["other_income"].fillna(0))
        cap_emp = out_df["equity_capital"].fillna(0) + out_df["reserves"].fillna(0) + out_df["borrowings"].fillna(0)
        out_df["roce_percentage"] = (ebit / cap_emp.replace(0, np.nan)) * 100.0

    # Sector-relative winsorisation and normalization
    composite_scores = []

    for sector, group in out_df.groupby("broad_sector", dropna=False):
        # 1. Profitability (35%)
        roe_s = winsorise_and_scale(group["return_on_equity_pct"], 10, 90)
        roce_s = winsorise_and_scale(group["roce_percentage"], 10, 90)
        npm_s = winsorise_and_scale(group["net_profit_margin_pct"], 10, 90)
        prof_score = roe_s * 0.15 + roce_s * 0.10 + npm_s * 0.10

        # 2. Cash Quality (30%)
        fcf_s = winsorise_and_scale(group["free_cash_flow_cr"], 10, 90)
        cfo_pat = (group["cash_from_operations_cr"] / group["net_profit"].replace(0, np.nan)).clip(-2, 5)
        cfo_s = winsorise_and_scale(cfo_pat, 10, 90)
        fcf_pos = (group["free_cash_flow_cr"] > 0).astype(float) * 100.0
        cash_score = fcf_s * 0.15 + cfo_s * 0.10 + fcf_pos * 0.05

        # 3. Growth (20%)
        rev_g = winsorise_and_scale(group["revenue_cagr_5yr"], 10, 90)
        pat_g = winsorise_and_scale(group["pat_cagr_5yr"], 10, 90)
        growth_score = rev_g * 0.10 + pat_g * 0.10

        # 4. Leverage (15%)
        de_s = winsorise_and_scale(group["debt_to_equity"], 10, 90, invert=True)
        # Treat None / Debt Free ICR as 100th percentile
        icr_filled = group["interest_coverage"].fillna(100.0)
        icr_s = winsorise_and_scale(icr_filled, 10, 90)
        lev_score = de_s * 0.10 + icr_s * 0.05

        total_comp = prof_score + cash_score + growth_score + lev_score
        group_scored = pd.Series(total_comp.round(2), index=group.index)
        composite_scores.append(group_scored)

    if composite_scores:
        out_df["composite_quality_score"] = pd.concat(composite_scores).sort_index()
    else:
        out_df["composite_quality_score"] = 50.0

    return out_df


def apply_screener_filters(
    universe_df: pd.DataFrame,
    filters_dict: Dict[str, Any],
) -> pd.DataFrame:
    """
    Apply threshold filters to universe DataFrame.
    Supports 15+ metrics, D/E Financials sector carve-out, and ICR infinity for Debt Free.
    """
    df = universe_df.copy()

    for metric, rule in filters_dict.items():
        if metric == "de_declining_yoy" and rule is True:
            df = df[df["de_declining_yoy"] == True]
            continue

        if not isinstance(rule, dict) or metric not in df.columns:
            continue

        min_val = rule.get("min")
        max_val = rule.get("max")

        # Special Case: Debt to Equity Max Filter (Financials Carve-Out)
        if metric == "debt_to_equity" and max_val is not None:
            is_financials = df["broad_sector"].astype(str).str.strip().str.lower() == "financials"
            passes_de = (df["debt_to_equity"] <= max_val) | is_financials
            df = df[passes_de]
            continue

        # Special Case: Interest Coverage Min Filter (Debt Free ICR is infinite)
        if metric == "interest_coverage" and min_val is not None:
            is_debt_free = df["interest_coverage"].isna() | (df["debt_to_equity"] == 0.0)
            passes_icr = (df["interest_coverage"] >= min_val) | is_debt_free
            df = df[passes_icr]
            continue

        # Standard Min / Max threshold filtering
        if min_val is not None:
            df = df[df[metric].notna() & (df[metric] >= min_val)]

        if max_val is not None:
            df = df[df[metric].notna() & (df[metric] <= max_val)]

    # Sort results by composite_quality_score descending
    if "composite_quality_score" in df.columns:
        df = df.sort_values(by="composite_quality_score", ascending=False).reset_index(drop=True)

    return df


def run_preset_screener(
    preset_key: str,
    universe_df: Optional[pd.DataFrame] = None,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Run one of the 6 preset screeners defined in config/screener_config.yaml.
    """
    cfg = config or load_screener_config()
    presets = cfg.get("presets", {})
    if preset_key not in presets:
        raise KeyError(f"Preset '{preset_key}' not found in configuration.")

    preset_def = presets[preset_key]
    filters = preset_def.get("filters", {})

    df = universe_df if universe_df is not None else load_screener_universe()
    return apply_screener_filters(df, filters)


def run_all_presets(
    universe_df: Optional[pd.DataFrame] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Run all 6 preset screeners and return a dictionary of result DataFrames.
    """
    cfg = config or load_screener_config()
    df = universe_df if universe_df is not None else load_screener_universe()

    results = {}
    for preset_key in cfg.get("presets", {}).keys():
        results[preset_key] = run_preset_screener(preset_key, universe_df=df, config=cfg)

    return results


def export_screener_excel(
    preset_results: Optional[Dict[str, pd.DataFrame]] = None,
    output_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Generate output/screener_output.xlsx containing 6 worksheets (one per preset)
    with 20 KPI columns, sorted by composite score, and threshold color-coded cells.
    """
    cfg = config or load_screener_config()
    results = preset_results or run_all_presets(config=cfg)
    target_path = Path(output_path) if output_path else DEFAULT_EXCEL_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # 20 KPI display columns
    kpi_columns = [
        ("company_id", "Company ID", "@"),
        ("company_name", "Company Name", "@"),
        ("broad_sector", "Sector", "@"),
        ("composite_quality_score", "Quality Score", "0.0"),
        ("return_on_equity_pct", "ROE (%)", "0.0%"),
        ("roce_percentage", "ROCE (%)", "0.0%"),
        ("net_profit_margin_pct", "Net Margin (%)", "0.0%"),
        ("operating_profit_margin_pct", "OPM (%)", "0.0%"),
        ("debt_to_equity", "D/E Ratio", "0.00"),
        ("interest_coverage", "ICR", "0.00"),
        ("free_cash_flow_cr", "FCF (Cr)", "#,##0"),
        ("capex_cr", "CapEx (Cr)", "#,##0"),
        ("cash_from_operations_cr", "CFO (Cr)", "#,##0"),
        ("revenue_cagr_5yr", "5Yr Rev CAGR (%)", "0.0%"),
        ("pat_cagr_5yr", "5Yr PAT CAGR (%)", "0.0%"),
        ("eps_cagr_5yr", "5Yr EPS CAGR (%)", "0.0%"),
        ("pe_ratio", "P/E Ratio", "0.0"),
        ("pb_ratio", "P/B Ratio", "0.0"),
        ("dividend_yield_pct", "Div Yield (%)", "0.0%"),
        ("dividend_payout_ratio_pct", "Div Payout (%)", "0.0%"),
    ]

    # Styling definitions
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    pass_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # Soft green
    fail_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")  # Soft red
    border_thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    for preset_key, preset_df in results.items():
        preset_info = cfg.get("presets", {}).get(preset_key, {})
        sheet_title = preset_info.get("name", preset_key)[:31]
        filters = preset_info.get("filters", {})

        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True

        # Write Headers (Row 1)
        for col_idx, (col_key, col_label, num_fmt) in enumerate(kpi_columns, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_label)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Write Data Rows
        for row_idx, (_, row) in enumerate(preset_df.iterrows(), start=2):
            for col_idx, (col_key, col_label, num_fmt) in enumerate(kpi_columns, start=1):
                val = row.get(col_key)
                # Handle numeric None
                if pd.isna(val) or val is None:
                    cell_val = "-"
                else:
                    cell_val = val

                cell = ws.cell(row=row_idx, column=col_idx, value=cell_val)
                cell.border = border_thin
                cell.alignment = Alignment(horizontal="left" if col_idx <= 3 else "right", vertical="center")

                # Apply threshold color coding
                if col_key in filters and isinstance(filters[col_key], dict) and isinstance(val, (int, float)):
                    f_min = filters[col_key].get("min")
                    f_max = filters[col_key].get("max")
                    is_pass = True
                    if f_min is not None and val < f_min:
                        is_pass = False
                    if f_max is not None and val > f_max:
                        # Skip financials carve-out
                        if not (col_key == "debt_to_equity" and str(row.get("broad_sector")).strip().lower() == "financials"):
                            is_pass = False

                    cell.fill = pass_fill if is_pass else fail_fill

        # Auto adjust column widths
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(target_path)
    return target_path


if __name__ == "__main__":
    print("Executing Screener Engine...")
    universe = load_screener_universe()
    print(f"Loaded constituent universe: {len(universe)} companies.")
    presets = run_all_presets(universe)
    for p, df in presets.items():
        print(f"  Preset [{p}]: {len(df)} companies returned.")
    export_path = export_screener_excel(presets)
    print(f"Exported screener results to {export_path}")
