import sqlite3
import pytest
from pathlib import Path
import pandas as pd
from src.etl.loader import load_to_sqlite, load_all_files, DEFAULT_SCHEMA_PATH


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_nifty100.db"
    return db_file


def test_schema_creates_all_12_tables(temp_db):
    with open(DEFAULT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.executescript(schema_sql)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall()]
    conn.close()

    expected_tables = sorted(
        [
            "companies",
            "analysis",
            "balancesheet",
            "cashflow",
            "documents",
            "financial_ratios",
            "market_cap",
            "peer_groups",
            "peer_percentiles",
            "profitandloss",
            "prosandcons",
            "sectors",
            "stock_prices",
        ]
    )
    assert sorted(tables) == expected_tables


def test_load_to_sqlite_loads_data_accurately(temp_db):
    sample_datasets = {
        "companies": pd.DataFrame(
            {
                "id": ["ABB", "TCS"],
                "company_name": ["ABB India", "Tata Consultancy Services"],
                "company_logo": ["logo1.png", "logo2.png"],
                "chart_link": ["link1", "link2"],
                "about_company": ["about1", "about2"],
                "website": ["web1", "web2"],
                "nse_profile": ["nse1", "nse2"],
                "bse_profile": ["bse1", "bse2"],
                "face_value": [2.0, 1.0],
                "book_value": [100.0, 200.0],
                "roce_percentage": [20.0, 30.0],
                "roe_percentage": [15.0, 25.0],
            }
        ),
        "analysis": pd.DataFrame(
            {
                "id": [1],
                "company_id": ["ABB"],
                "compounded_sales_growth": [12.5],
                "compounded_profit_growth": [15.2],
                "stock_price_cagr": [18.0],
                "roe": [22.0],
            }
        ),
    }

    summary = load_to_sqlite(
        db_path=temp_db,
        schema_path=DEFAULT_SCHEMA_PATH,
        datasets=sample_datasets,
        enforce_fk=False,
    )

    assert summary["companies"]["loaded_rows"] == 2
    assert summary["analysis"]["loaded_rows"] == 1
    assert summary["companies"]["status"] == "SUCCESS"


def test_sqlite_foreign_key_constraint_enforcement(temp_db):
    with open(DEFAULT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.executescript(schema_sql)

    # Insert valid parent
    cursor.execute(
        "INSERT INTO companies (id, company_name) VALUES ('TESTCO', 'Test Company');"
    )
    conn.commit()

    # Insert valid child
    cursor.execute(
        "INSERT INTO analysis (id, company_id, roe) VALUES (1, 'TESTCO', 15.0);"
    )
    conn.commit()

    # Attempt inserting orphan child with FK enforced
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO analysis (id, company_id, roe) VALUES (2, 'NON_EXISTENT', 10.0);"
        )
        conn.commit()

    conn.close()


def test_sqlite_primary_key_uniqueness(temp_db):
    with open(DEFAULT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.executescript(schema_sql)

    cursor.execute(
        "INSERT INTO companies (id, company_name) VALUES ('TESTCO', 'Test Company 1');"
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO companies (id, company_name) VALUES ('TESTCO', 'Test Company 2');"
        )
        conn.commit()

    conn.close()
