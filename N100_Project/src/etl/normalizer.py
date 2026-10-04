"""
Normalization functions for N100 Financial Intelligence Platform.
"""

import re
import pandas as pd

# Known ticker normalization mapping for typos / alternate identifiers
TICKER_CORRECTIONS = {
    "AGTL": "ATGL",  # Typo in cashflow.xlsx for Adani Total Gas Ltd (ATGL)
}


def normalize_ticker(value):
    """
    Normalize company/ticker identifiers:
    - Strips whitespace
    - Converts to uppercase
    - Applies known ticker corrections (e.g. AGTL -> ATGL)
    - Returns None if empty or NaN
    """
    if pd.isna(value):
        return None

    text = str(value).strip().upper()
    if not text or text in {"NAN", "NONE", "NULL", "UNKNOWN", "N/A"}:
        return None

    # Apply known ticker typo mappings
    return TICKER_CORRECTIONS.get(text, text)


def normalize_year(value):
    """
    Convert year values such as:
        'Dec 2012'    -> 2012
        'Mar 2014'    -> 2014
        'Mar-13'      -> 2013
        'Mar 2016 9m' -> 2016
        'Mar 2023 15' -> 2023
        2024          -> 2024
        2021.0        -> 2021
        'TTM'         -> None (Trailing Twelve Months is audited as non-calendar year)
        'Unknown'     -> None
        None / NaN    -> None
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text or text.upper() in {"TTM", "NAN", "NONE", "NULL", "UNKNOWN", "N/A"}:
        return None

    # 1. Look for four-digit year (19xx or 20xx)
    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if match:
        return int(match.group(1))

    # 2. Look for two-digit year pattern like 'Mar-13' or '-13' or 'FY13'
    match_2d = re.search(r"(?:-|\bFY|\b|/)(\d{2})$", text, re.IGNORECASE)
    if match_2d:
        year_2d = int(match_2d.group(1))
        return 2000 + year_2d if year_2d <= 50 else 1900 + year_2d

    # 3. Numeric float/int conversion
    try:
        val_float = float(text)
        year_int = int(val_float)
        if 1900 <= year_int <= 2100:
            return year_int
    except (ValueError, TypeError):
        pass

    return None


def clean_column_name(column_name):
    """
    Normalize column names:
    - Strip whitespace
    - Convert to lowercase
    - Replace spaces and special characters with underscores
    - Collapse multiple underscores
    """
    if column_name is None:
        return "unnamed"
    text = str(column_name).strip().lower()
    text = re.sub(r"[^\w]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def normalize_dataframe(df, table_name=None):
    """
    Clean column names, normalize string fields, company identifiers, and year fields.
    """
    df = df.copy()

    # Drop unnamed columns that are entirely NaN
    unnamed_cols = [c for c in df.columns if str(c).startswith("Unnamed:") and df[c].isna().all()]
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    # Clean column names
    df.columns = [clean_column_name(col) for col in df.columns]

    # Strip string columns & replace 'nan' / 'None' string artifacts
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(
                lambda x: str(x).strip() if pd.notna(x) and str(x).strip() not in {"", "nan", "None", "None\n", "NaN"} else (None if pd.isna(x) or str(x).strip() in {"", "nan", "None", "None\n", "NaN"} else x)
            )

    # Normalize company identifier column
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)

    if table_name == "companies" and "id" in df.columns:
        df["id"] = df["id"].apply(normalize_ticker)

    # Normalize year column
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    # Handle peer_groups boolean is_benchmark
    if "is_benchmark" in df.columns:
        df["is_benchmark"] = df["is_benchmark"].apply(
            lambda x: True if str(x).strip().lower() in {"true", "1", "1.0", "yes"} else (False if pd.notna(x) else None)
        )

    return df