"""
Excel and Database Loader for N100 Financial Intelligence Platform.
"""

from pathlib import Path
import sqlite3
import pandas as pd

from src.etl.normalizer import normalize_dataframe

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "Data"
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"

# Files where the actual column header is row index 1 (row 2 in Excel)
HEADER_ROW_ONE = {
    "analysis.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "companies.xlsx",
    "documents.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
}

EXPECTED_FILES = [
    "analysis.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "companies.xlsx",
    "documents.xlsx",
    "financial_ratios.xlsx",
    "market_cap.xlsx",
    "peer_groups.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
    "sectors.xlsx",
    "stock_prices.xlsx",
]

# Minimal parent records for the 8 verified Nifty 100 constituents referenced by child datasets
# but omitted from companies.xlsx master list. All metadata fields remain NULL.
MISSING_PARENT_COMPANIES = [
    {"id": "ULTRACEMCO", "company_name": "UltraTech Cement Ltd"},
    {"id": "UNIONBANK", "company_name": "Union Bank of India"},
    {"id": "UNITDSPR", "company_name": "United Spirits Ltd"},
    {"id": "VBL", "company_name": "Varun Beverages Ltd"},
    {"id": "VEDL", "company_name": "Vedanta Ltd"},
    {"id": "WIPRO", "company_name": "Wipro Ltd"},
    {"id": "ZOMATO", "company_name": "Zomato Ltd"},
    {"id": "ZYDUSLIFE", "company_name": "Zydus Lifesciences Ltd"},
]


def detect_header_row(file_path):
    """
    Detect whether the file has a title banner on row 1 or starts with header on row 0.
    """
    fname = Path(file_path).name.lower()
    if fname in {f.lower() for f in HEADER_ROW_ONE}:
        return 1

    try:
        sample = pd.read_excel(file_path, header=None, nrows=2)
        if len(sample) >= 2:
            first_row_non_null = sample.iloc[0].notna().sum()
            second_row_non_null = sample.iloc[1].notna().sum()
            first_val = str(sample.iloc[0, 0]) if sample.iloc[0].notna().any() else ""
            if "Bluestock" in first_val or (first_row_non_null <= 2 and second_row_non_null > 2):
                return 1
    except Exception:
        pass

    return 0


def load_excel(filename_or_path, header_row=None, data_dir=None):
    """
    Load one Excel source file using the correct header row.
    Returns unmodified normalized dataframe directly from the source file.
    """
    path = Path(filename_or_path)
    if not path.is_absolute():
        base_dir = Path(data_dir) if data_dir else DATA_DIR
        file_path = base_dir / filename_or_path
    else:
        file_path = path

    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    if header_row is None:
        header_row = detect_header_row(file_path)

    try:
        df = pd.read_excel(file_path, header=header_row)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file '{file_path.name}': {e}") from e

    if df.empty or len(df.columns) == 0:
        raise ValueError(f"Malformed or empty sheet in file: {file_path.name}")

    table_name = file_path.stem.lower()
    return normalize_dataframe(df, table_name=table_name)


def seed_parent_companies(companies_df: pd.DataFrame) -> pd.DataFrame:
    """
    Seed minimal parent records for missing Nifty 100 constituent companies
    referenced by child statements without fabricating any metadata.
    """
    df = companies_df.copy()
    existing_ids = set(df["id"].dropna().unique())

    new_records = []
    for co in MISSING_PARENT_COMPANIES:
        if co["id"] not in existing_ids:
            rec = {col: None for col in df.columns}
            rec["id"] = co["id"]
            rec["company_name"] = co["company_name"]
            new_records.append(rec)

    if new_records:
        seeded_df = pd.DataFrame(new_records)
        df = pd.concat([df, seeded_df], ignore_index=True)

    return df


def load_all_files(data_dir=None, seed_missing_parents=True):
    """
    Load all 12 Excel source files into a dictionary of DataFrames.
    If seed_missing_parents=True, adds the 8 minimal parent stubs to companies dataframe.
    """
    base_dir = Path(data_dir) if data_dir else DATA_DIR

    if not base_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {base_dir}")

    files = sorted(base_dir.glob("*.xlsx"))

    # Verify all expected files are present
    found_names = {f.name for f in files}
    missing = [f for f in EXPECTED_FILES if f not in found_names]
    if missing:
        raise FileNotFoundError(f"Missing expected Excel files: {missing}")

    if len(files) != 12:
        raise ValueError(f"Expected 12 Excel files, found {len(files)}")

    datasets = {}
    for file_path in files:
        datasets[file_path.stem] = load_excel(file_path, data_dir=base_dir)

    if seed_missing_parents and "companies" in datasets:
        datasets["companies"] = seed_parent_companies(datasets["companies"])

    return datasets


def load_to_sqlite(db_path=None, schema_path=None, datasets=None, enforce_fk=False):
    """
    Create SQLite tables from schema.sql and insert all datasets.
    Returns dictionary with load summary per table.
    """
    db_file = Path(db_path) if db_path else DEFAULT_DB_PATH
    schema_file = Path(schema_path) if schema_path else DEFAULT_SCHEMA_PATH

    if datasets is None:
        datasets = load_all_files(seed_missing_parents=True)

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Read DDL schema
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Recreate database tables
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    if enforce_fk:
        cursor.execute("PRAGMA foreign_keys = ON;")
    else:
        cursor.execute("PRAGMA foreign_keys = OFF;")

    # Execute schema DDL
    cursor.executescript(schema_sql)
    conn.commit()

    # Ensure foreign keys are enabled after schema creation if requested
    if enforce_fk:
        cursor.execute("PRAGMA foreign_keys = ON;")

    # Load order: companies first, then child tables
    ordered_tables = ["companies"] + [t for t in datasets.keys() if t != "companies"]
    load_summary = {}

    for table_name in ordered_tables:
        if table_name not in datasets:
            continue
        df = datasets[table_name].copy()
        initial_rows = len(df)

        # Write to SQLite
        df.to_sql(table_name, conn, if_exists="append", index=False)

        # Verify count in DB
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        db_count = cursor.fetchone()[0]

        load_summary[table_name] = {
            "source_rows": initial_rows,
            "loaded_rows": db_count,
            "columns": len(df.columns),
            "status": "SUCCESS" if initial_rows == db_count else "MISMATCH",
        }

    conn.commit()
    conn.close()

    return load_summary


if __name__ == "__main__":
    datasets = load_all_files()
    print("Successfully loaded 12 Excel files.")
    for name, df in datasets.items():
        print(f"{name}: {len(df)} rows x {len(df.columns)} columns")

    summary = load_to_sqlite()
    print("\nDatabase load summary:")
    for t, s in summary.items():
        print(f"  {t}: {s['loaded_rows']}/{s['source_rows']} rows loaded ({s['status']})")