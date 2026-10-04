from pathlib import Path
import sqlite3
import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_FILE = PROJECT_ROOT / "sql" / "schema.sql"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data" / "db"
DB_FILE = DB_DIR / "bluestock_mf.db"

DB_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# CSV FILE MAPPING
# =========================================================
TABLE_MAP = {
    "fund_master": "fund_master",
    "nav_history": "nav_history",
    "aum_by_fund_house": "aum_by_fund_house",
    "monthly_sip_inflows": "monthly_sip_inflows",
    "category_inflows": "category_inflows",
    "industry_folio_count": "industry_folio_count",
    "scheme_performance": "scheme_performance",
    "portfolio_holdings": "portfolio_holdings",
    "investor_transactions": "investor_transactions",
    "benchmark_indices": "benchmark_indices",
}


# =========================================================
# FIND CSV FILE
# =========================================================
def find_csv(keyword: str) -> Path | None:
    matches = list(PROCESSED_DIR.glob(f"*{keyword}.csv"))

    if not matches:
        print(f"WARNING: CSV not found for {keyword}")
        return None

    return matches[0]


# =========================================================
# CREATE TABLES FROM SCHEMA
# =========================================================
def create_schema(connection: sqlite3.Connection) -> None:
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

    connection.executescript(schema_sql)
    connection.commit()

    print("Database schema created successfully.")


# =========================================================
# LOAD DATA WITHOUT REPLACING TABLES
# =========================================================
def load_csv(
    connection: sqlite3.Connection,
    csv_path: Path,
    table_name: str,
) -> None:

    try:
        df = pd.read_csv(csv_path)

        # Insert data into the schema-created table.
        # Do NOT use if_exists="replace".
        df.to_sql(
            table_name,
            connection,
            if_exists="append",
            index=False,
        )

        print(
            f"Loaded {csv_path.name} -> "
            f"{table_name} ({len(df):,} rows)"
        )

    except Exception as exc:
        print(
            f"ERROR loading {csv_path.name} "
            f"into {table_name}: {exc}"
        )


# =========================================================
# MAIN
# =========================================================
def main() -> None:

    print("=" * 70)
    print("BLUESTOCK MUTUAL FUND - DATABASE LOAD")
    print("=" * 70)

    if not PROCESSED_DIR.exists():
        raise FileNotFoundError(
            f"Processed directory not found: {PROCESSED_DIR}"
        )

    # Remove old database so the corrected schema is created fresh.
    if DB_FILE.exists():
        DB_FILE.unlink()
        print("Old database removed.")

    connection = sqlite3.connect(DB_FILE)

    try:
        # Enable foreign key enforcement
        connection.execute("PRAGMA foreign_keys = ON")

        # Create schema first
        create_schema(connection)

        # Load the 10 original datasets
        for keyword, table_name in TABLE_MAP.items():

            csv_path = find_csv(keyword)

            if csv_path is not None:
                load_csv(
                    connection,
                    csv_path,
                    table_name,
                )

        connection.commit()

        print("\nDatabase created at:")
        print(DB_FILE)

    finally:
        connection.close()

    print("\n" + "=" * 70)
    print("DATABASE LOAD COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()