"""
14 Unit Tests for Data Quality (DQ) Rules (Day 41).
Tests each DQ validation rule with crafted violating DataFrames.
"""

import pandas as pd
import pytest
from src.etl.validator import DataQualityValidator


def test_dq01_pk_not_null():
    df = pd.DataFrame([{"id": None, "company_name": "Test"}])
    validator = DataQualityValidator({"companies": df})
    validator.validate_dq01_pk_not_null()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-01"
    assert validator.failures[0].severity == "CRITICAL"


def test_dq02_pk_uniqueness():
    df = pd.DataFrame([{"id": "TCS"}, {"id": "TCS"}])
    validator = DataQualityValidator({"companies": df})
    validator.validate_dq02_pk_uniqueness()
    assert len(validator.failures) == 2
    assert validator.failures[0].rule_id == "DQ-02"
    assert validator.failures[0].severity == "CRITICAL"


def test_dq03_foreign_key_integrity():
    master = pd.DataFrame([{"id": "TCS"}])
    child = pd.DataFrame([{"id": 1, "company_id": "UNKNOWN_TICKER"}])
    validator = DataQualityValidator({"companies": master, "balancesheet": child})
    validator.validate_dq03_foreign_key_integrity()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-03"


def test_dq04_company_mandatory_fields():
    df = pd.DataFrame([{"id": "TCS", "company_name": ""}])
    validator = DataQualityValidator({"companies": df})
    validator.validate_dq04_company_mandatory_fields()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-04"


def test_dq05_year_validity():
    df = pd.DataFrame([{"id": 1, "company_id": "TCS", "year": 1850}])
    validator = DataQualityValidator({"balancesheet": df})
    validator.validate_dq05_year_validity()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-05"


def test_dq06_stock_price_non_negativity():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "date": "2024-01-01",
        "open_price": -10.0, "high_price": 100.0, "low_price": 90.0, "close_price": 95.0, "volume": 1000
    }])
    validator = DataQualityValidator({"stock_prices": df})
    validator.validate_dq06_stock_price_non_negative()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-06"


def test_dq07_stock_price_high_low_inversion():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "date": "2024-01-01",
        "open_price": 100.0, "high_price": 80.0, "low_price": 120.0, "close_price": 95.0, "volume": 1000
    }])
    validator = DataQualityValidator({"stock_prices": df})
    validator.validate_dq07_stock_price_high_low_inversion()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-07"


def test_dq08_stock_price_bounds():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "date": "2024-01-01",
        "open_price": 150.0, "high_price": 120.0, "low_price": 100.0, "close_price": 110.0, "volume": 1000
    }])
    validator = DataQualityValidator({"stock_prices": df})
    validator.validate_dq08_stock_price_bounds()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-08"


def test_dq09_stock_price_date_format():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "date": "01/01/2024",
        "open_price": 100.0, "high_price": 120.0, "low_price": 90.0, "close_price": 110.0, "volume": 1000
    }])
    validator = DataQualityValidator({"stock_prices": df})
    validator.validate_dq09_stock_price_date_format()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-09"


def test_dq10_balance_sheet_equation():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "year": 2024,
        "total_assets": 1000.0, "total_liabilities": 800.0
    }])
    validator = DataQualityValidator({"balancesheet": df})
    validator.validate_dq10_balance_sheet_equation()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-10"


def test_dq11_balance_sheet_components():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "year": 2024,
        "equity_capital": 100.0, "reserves": 200.0, "borrowings": 50.0, "other_liabilities": 50.0,
        "total_liabilities": 1000.0,
        "fixed_assets": 200.0, "cwip": 0.0, "investments": 100.0, "other_asset": 100.0,
        "total_assets": 1000.0
    }])
    validator = DataQualityValidator({"balancesheet": df})
    validator.validate_dq11_balance_sheet_components()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-11"


def test_dq12_cashflow_reconciliation():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "year": 2024,
        "operating_activity": 100.0, "investing_activity": -40.0, "financing_activity": -20.0,
        "net_cash_flow": 200.0  # Should be 40.0
    }])
    validator = DataQualityValidator({"cashflow": df})
    validator.validate_dq12_cashflow_reconciliation()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-12"


def test_dq13_valuation_metrics():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "year": 2024,
        "market_cap_crore": -500.0, "enterprise_value_crore": 1000.0, "pb_ratio": 5.0
    }])
    validator = DataQualityValidator({"market_cap": df})
    validator.validate_dq13_valuation_metrics()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-13"


def test_dq14_sector_index_weights():
    df = pd.DataFrame([{
        "id": 1, "company_id": "TCS", "broad_sector": "IT", "index_weight_pct": 150.0
    }])
    validator = DataQualityValidator({"sectors": df})
    validator.validate_dq14_sector_index_weights()
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-14"
