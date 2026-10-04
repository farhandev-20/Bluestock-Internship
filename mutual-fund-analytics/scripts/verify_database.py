from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / "data" / "db" / "bluestock_mf.db"


EXPECTED_TABLES = [
    "fund_master",
    "nav_history",
    "aum_by_fund_house",
    "monthly_sip_inflows",
    "category_inflows",
    "industry_folio_count",
    "scheme_performance",
    "portfolio_holdings",
    "investor_transactions",
    "benchmark_indices",
]


def main():
    print("=" * 70)
    print("BLUESTOCK MUTUAL FUND DATABASE VERIFICATION")
    print("=" * 70)

    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    conn = sqlite3.connect(DB_FILE)

    try:
        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """,
            conn,
        )

        actual_tables = set(tables["name"])

        print("\n1. TABLE CHECK")
        print("-" * 70)

        for table in EXPECTED_TABLES:
            if table in actual_tables:
                print(f"{table:<30} OK")
            else:
                print(f"{table:<30} MISSING")

        print("\n2. ROW COUNTS")
        print("-" * 70)

        for table in EXPECTED_TABLES:
            if table in actual_tables:
                count = pd.read_sql_query(
                    f'SELECT COUNT(*) AS count FROM "{table}"',
                    conn,
                ).iloc[0]["count"]

                print(f"{table:<30} {count:,}")

        print("\n3. SCHEMA CHECK")
        print("-" * 70)

        for table in EXPECTED_TABLES:
            if table not in actual_tables:
                continue

            columns = pd.read_sql_query(
                f'PRAGMA table_info("{table}")',
                conn,
            )

            print(f"\n{table}:")
            print(
                columns[["name", "type"]]
                .to_string(index=False)
            )

        print("\n4. FOREIGN KEY CHECK")
        print("-" * 70)

        for table in ["nav_history", "scheme_performance",
                      "portfolio_holdings", "investor_transactions"]:
            if table in actual_tables:
                fk = pd.read_sql_query(
                    f'PRAGMA foreign_key_list("{table}")',
                    conn,
                )

                print(f"\n{table}:")
                if fk.empty:
                    print("No foreign keys found")
                else:
                    print(
                        fk[["table", "from", "to"]]
                        .to_string(index=False)
                    )

        print("\n" + "=" * 70)
        print("DATABASE VERIFICATION COMPLETED")
        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()