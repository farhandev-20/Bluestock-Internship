import pandas as pd
import pytest
from src.etl.validator import DataQualityValidator, run_all_validations


@pytest.fixture
def base_valid_datasets():
    companies_df = pd.DataFrame(
        {
            "id": ["ABB", "TCS"],
            "company_name": ["ABB India", "Tata Consultancy Services"],
            "face_value": [2.0, 1.0],
            "book_value": [100.0, 200.0],
        }
    )
    stock_prices_df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["ABB", "TCS"],
            "date": ["2024-01-01", "2024-02-01"],
            "open_price": [100.0, 200.0],
            "high_price": [110.0, 210.0],
            "low_price": [90.0, 190.0],
            "close_price": [105.0, 205.0],
            "volume": [1000, 2000],
            "adjusted_close": [105.0, 205.0],
        }
    )
    balancesheet_df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["ABB", "TCS"],
            "year": [2023, 2023],
            "equity_capital": [20.0, 50.0],
            "reserves": [80.0, 150.0],
            "borrowings": [0.0, 0.0],
            "other_liabilities": [0.0, 0.0],
            "total_liabilities": [100.0, 200.0],
            "fixed_assets": [50.0, 100.0],
            "cwip": [0.0, 0.0],
            "investments": [50.0, 100.0],
            "other_asset": [0.0, 0.0],
            "total_assets": [100.0, 200.0],
        }
    )
    cashflow_df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["ABB", "TCS"],
            "year": [2023, 2023],
            "operating_activity": [100.0, 200.0],
            "investing_activity": [-50.0, -100.0],
            "financing_activity": [-30.0, -60.0],
            "net_cash_flow": [20.0, 40.0],
        }
    )
    market_cap_df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["ABB", "TCS"],
            "year": [2023, 2023],
            "market_cap_crore": [50000.0, 150000.0],
            "enterprise_value_crore": [49000.0, 148000.0],
            "pe_ratio": [30.0, 25.0],
            "pb_ratio": [10.0, 12.0],
            "ev_ebitda": [20.0, 18.0],
            "dividend_yield_pct": [1.2, 1.5],
        }
    )
    sectors_df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["ABB", "TCS"],
            "broad_sector": ["Industrials", "IT"],
            "sub_sector": ["Capital Goods", "Software"],
            "index_weight_pct": [1.5, 4.2],
            "market_cap_category": ["Large Cap", "Large Cap"],
        }
    )
    documents_df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["ABB", "TCS"],
            "year": [2023, 2023],
            "annual_report": ["https://bseindia.com/rep1.pdf", "https://bseindia.com/rep2.pdf"],
        }
    )
    return {
        "companies": companies_df,
        "stock_prices": stock_prices_df,
        "balancesheet": balancesheet_df,
        "cashflow": cashflow_df,
        "market_cap": market_cap_df,
        "sectors": sectors_df,
        "documents": documents_df,
    }


def test_validator_clean_data_passes(base_valid_datasets):
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    assert len(failures) == 0


def test_validator_dq01_pk_null(base_valid_datasets):
    base_valid_datasets["companies"].loc[0, "id"] = None
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq01 = failures[failures["rule_id"] == "DQ-01"]
    assert len(dq01) == 1
    assert dq01.iloc[0]["severity"] == "CRITICAL"


def test_validator_dq02_pk_duplicate(base_valid_datasets):
    base_valid_datasets["companies"].loc[1, "id"] = "ABB"
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq02 = failures[failures["rule_id"] == "DQ-02"]
    assert len(dq02) >= 1
    assert dq02.iloc[0]["severity"] == "CRITICAL"


def test_validator_dq03_fk_orphan(base_valid_datasets):
    base_valid_datasets["stock_prices"].loc[0, "company_id"] = "UNKNOWN_CO"
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq03 = failures[failures["rule_id"] == "DQ-03"]
    assert len(dq03) == 1
    assert dq03.iloc[0]["invalid_value"] == "UNKNOWN_CO"


def test_validator_dq04_mandatory_company_name(base_valid_datasets):
    base_valid_datasets["companies"].loc[0, "company_name"] = None
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq04 = failures[failures["rule_id"] == "DQ-04"]
    assert len(dq04) == 1


def test_validator_dq05_year_range(base_valid_datasets):
    base_valid_datasets["balancesheet"].loc[0, "year"] = 1980
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq05 = failures[failures["rule_id"] == "DQ-05"]
    assert len(dq05) == 1


def test_validator_dq06_stock_price_negative(base_valid_datasets):
    base_valid_datasets["stock_prices"].loc[0, "open_price"] = -50.0
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq06 = failures[failures["rule_id"] == "DQ-06"]
    assert len(dq06) == 1


def test_validator_dq07_stock_price_high_low_inversion(base_valid_datasets):
    base_valid_datasets["stock_prices"].loc[0, "high_price"] = 80.0
    base_valid_datasets["stock_prices"].loc[0, "low_price"] = 90.0
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq07 = failures[failures["rule_id"] == "DQ-07"]
    assert len(dq07) == 1


def test_validator_dq08_stock_price_bounds(base_valid_datasets):
    # high < open
    base_valid_datasets["stock_prices"].loc[0, "high_price"] = 95.0
    base_valid_datasets["stock_prices"].loc[0, "open_price"] = 100.0
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq08 = failures[failures["rule_id"] == "DQ-08"]
    assert len(dq08) == 1


def test_validator_dq09_stock_price_date_format(base_valid_datasets):
    base_valid_datasets["stock_prices"].loc[0, "date"] = "01/01/2024"
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq09 = failures[failures["rule_id"] == "DQ-09"]
    assert len(dq09) == 1


def test_validator_dq10_balance_sheet_equation(base_valid_datasets):
    base_valid_datasets["balancesheet"].loc[0, "total_assets"] = 500.0
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq10 = failures[failures["rule_id"] == "DQ-10"]
    assert len(dq10) == 1


def test_validator_dq11_balance_sheet_components(base_valid_datasets):
    base_valid_datasets["balancesheet"].loc[0, "fixed_assets"] = 10.0  # Sum becomes 60 != 100
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq11 = failures[failures["rule_id"] == "DQ-11"]
    assert len(dq11) == 1


def test_validator_dq12_cashflow_reconciliation(base_valid_datasets):
    base_valid_datasets["cashflow"].loc[0, "net_cash_flow"] = 999.0
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq12 = failures[failures["rule_id"] == "DQ-12"]
    assert len(dq12) == 1


def test_validator_dq13_valuation_metrics(base_valid_datasets):
    base_valid_datasets["market_cap"].loc[0, "market_cap_crore"] = -100.0
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq13 = failures[failures["rule_id"] == "DQ-13"]
    assert len(dq13) == 1


def test_validator_dq14_sector_index_weights(base_valid_datasets):
    base_valid_datasets["sectors"].loc[0, "index_weight_pct"] = 150.0
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq14 = failures[failures["rule_id"] == "DQ-14"]
    assert len(dq14) == 1


def test_validator_dq15_document_urls(base_valid_datasets):
    base_valid_datasets["documents"].loc[0, "annual_report"] = "ftp://invalid-url/rep.pdf"
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq15 = failures[failures["rule_id"] == "DQ-15"]
    assert len(dq15) == 1


def test_validator_dq16_composite_uniqueness(base_valid_datasets):
    # duplicate (company_id, year) in balancesheet
    dup_row = base_valid_datasets["balancesheet"].iloc[[0]].copy()
    dup_row["id"] = 999
    base_valid_datasets["balancesheet"] = pd.concat([base_valid_datasets["balancesheet"], dup_row], ignore_index=True)
    validator = DataQualityValidator(base_valid_datasets)
    failures = validator.run_all_rules()
    dq16 = failures[failures["rule_id"] == "DQ-16"]
    assert len(dq16) == 2


def test_run_all_validations_output_csv(tmp_path, base_valid_datasets):
    base_valid_datasets["stock_prices"].loc[0, "open_price"] = -10.0
    out_csv = tmp_path / "test_failures.csv"
    failures_df = run_all_validations(base_valid_datasets, output_path=out_csv)
    assert out_csv.exists()
    assert len(failures_df) > 0
