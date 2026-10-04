"""
Analysis Text Parser Module for N100 Intelligence Platform.
Parses semi-structured text CAGR and growth metrics using regex, generates
output/analysis_parsed.csv and output/parse_failures.csv, and cross-validates with ratio engine.
"""

from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "Data"
DEFAULT_ANALYSIS_XLSX = DATA_DIR / "analysis.xlsx"
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_PARSED_CSV = OUTPUT_DIR / "analysis_parsed.csv"
DEFAULT_FAILURES_CSV = OUTPUT_DIR / "parse_failures.csv"

# Primary regex pattern for "10 Years: 21%", "5 Years: 8%", "3 Years: 8%", "1 Year: 13%"
REGEX_PRIMARY = re.compile(r'(\d+)\s*Years?:?\s*([+\-]?\d+(?:\.\d+)?)\s*%', re.IGNORECASE)

# Secondary patterns for "Last Year: 17%" and "TTM: 43%"
REGEX_LAST_YEAR = re.compile(r'Last\s*Year:?\s*([+\-]?\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
REGEX_TTM = re.compile(r'TTM:?\s*([+\-]?\d+(?:\.\d+)?)\s*%', re.IGNORECASE)


def parse_metric_text(text: Any) -> Optional[Tuple[int, float]]:
    """
    Extracts (period_years, value_pct) from text strings.
    Examples:
      - "10 Years: 21%" -> (10, 21.0)
      - "5 Years       24%" -> (5, 24.0)
      - "Last Year: 17%" -> (1, 17.0)
      - "TTM: 43%" -> (1, 43.0)
    Returns None if no match is found.
    """
    if pd.isna(text) or text is None:
        return None

    str_val = str(text).strip()
    if not str_val:
        return None

    # Primary match
    m = REGEX_PRIMARY.search(str_val)
    if m:
        return int(m.group(1)), float(m.group(2))

    # Last Year match
    m_ly = REGEX_LAST_YEAR.search(str_val)
    if m_ly:
        return 1, float(m_ly.group(1))

    # TTM match
    m_ttm = REGEX_TTM.search(str_val)
    if m_ttm:
        return 1, float(m_ttm.group(1))

    return None


def parse_analysis_data(
    file_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
    output_parsed_path: Optional[Path] = None,
    output_failures_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parses all text fields in analysis dataset across 4 target fields:
    - compounded_sales_growth
    - compounded_profit_growth
    - stock_price_cagr
    - roe
    Generates output/analysis_parsed.csv and logs unmatched entries to output/parse_failures.csv.
    """
    target_xlsx = Path(file_path or DEFAULT_ANALYSIS_XLSX)
    target_parsed = Path(output_parsed_path or DEFAULT_PARSED_CSV)
    target_failures = Path(output_failures_path or DEFAULT_FAILURES_CSV)
    
    target_parsed.parent.mkdir(parents=True, exist_ok=True)

    # Ingest from Excel or Database
    if target_xlsx.exists():
        raw_df = pd.read_excel(target_xlsx, skiprows=1)
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
    else:
        conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))
        raw_df = pd.read_sql_query("SELECT * FROM analysis", conn)
        conn.close()

    target_metrics = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]

    parsed_records = []
    failure_records = []

    for _, row in raw_df.iterrows():
        cid = row.get("company_id")
        if pd.isna(cid) or not cid:
            continue

        for m_col in target_metrics:
            if m_col not in raw_df.columns:
                continue

            raw_text = row.get(m_col)
            if pd.isna(raw_text) or str(raw_text).strip() == "":
                continue

            parsed_res = parse_metric_text(raw_text)
            if parsed_res is not None:
                period_yr, val_pct = parsed_res
                parsed_records.append({
                    "company_id": str(cid).strip(),
                    "metric_type": m_col,
                    "period_years": period_yr,
                    "value_pct": val_pct,
                })
            else:
                failure_records.append({
                    "company_id": str(cid).strip(),
                    "metric_type": m_col,
                    "raw_text": str(raw_text),
                    "reason": "Pattern regex mismatch",
                })

    parsed_df = pd.DataFrame(parsed_records)
    failures_df = pd.DataFrame(failure_records)

    # Save CSV files
    parsed_df.to_csv(target_parsed, index=False)
    failures_df.to_csv(target_failures, index=False)

    return parsed_df, failures_df


def cross_validate_parsed_cagr(
    parsed_df: pd.DataFrame,
    db_path: Optional[Path] = None,
    threshold_pct: float = 5.0,
) -> pd.DataFrame:
    """
    Cross-validates parsed CAGR values against Ratio Engine computed ratios from SQLite.
    Flags divergence > 5% for manual review.
    """
    conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios WHERE year = 2024", conn)
    conn.close()

    if ratios_df.empty:
        return pd.DataFrame()

    # Filter for 5-year metrics in parsed_df
    rev_5yr = parsed_df[(parsed_df["metric_type"] == "compounded_sales_growth") & (parsed_df["period_years"] == 5)]
    pat_5yr = parsed_df[(parsed_df["metric_type"] == "compounded_profit_growth") & (parsed_df["period_years"] == 5)]

    validation_rows = []

    # Validate 5yr Sales Growth
    for _, row in rev_5yr.iterrows():
        cid = row["company_id"]
        parsed_val = row["value_pct"]
        r_match = ratios_df[ratios_df["company_id"] == cid]
        if not r_match.empty:
            computed_val = r_match.iloc[0].get("revenue_cagr_5yr")
            if pd.notna(computed_val):
                diff = abs(parsed_val - computed_val)
                validation_rows.append({
                    "company_id": cid,
                    "metric": "5Yr Revenue CAGR",
                    "parsed_value": parsed_val,
                    "computed_value": computed_val,
                    "difference": round(diff, 2),
                    "flagged_divergence": diff > threshold_pct,
                })

    # Validate 5yr PAT Growth
    for _, row in pat_5yr.iterrows():
        cid = row["company_id"]
        parsed_val = row["value_pct"]
        r_match = ratios_df[ratios_df["company_id"] == cid]
        if not r_match.empty:
            computed_val = r_match.iloc[0].get("pat_cagr_5yr")
            if pd.notna(computed_val):
                diff = abs(parsed_val - computed_val)
                validation_rows.append({
                    "company_id": cid,
                    "metric": "5Yr PAT CAGR",
                    "parsed_value": parsed_val,
                    "computed_value": computed_val,
                    "difference": round(diff, 2),
                    "flagged_divergence": diff > threshold_pct,
                })

    return pd.DataFrame(validation_rows)


if __name__ == "__main__":
    print("Executing Analysis Text Parser...")
    parsed, failures = parse_analysis_data()
    print(f"Successfully parsed {len(parsed)} metric entries -> output/analysis_parsed.csv")
    print(f"Logged {len(failures)} failures -> output/parse_failures.csv")
    val_res = cross_validate_parsed_cagr(parsed)
    if not val_res.empty:
        divergent = val_res[val_res["flagged_divergence"] == True]
        print(f"Cross-validation complete: {len(divergent)} items flagged with >5% divergence.")
