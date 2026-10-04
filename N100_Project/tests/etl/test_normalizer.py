import pandas as pd
import numpy as np
from src.etl.normalizer import (
    normalize_ticker,
    normalize_year,
    clean_column_name,
    normalize_dataframe,
)


def test_normalize_ticker_uppercase():
    assert normalize_ticker("hdfcbank") == "HDFCBANK"


def test_normalize_ticker_strip_spaces():
    assert normalize_ticker("  TCS  ") == "TCS"


def test_normalize_ticker_empty():
    assert normalize_ticker("") is None


def test_normalize_ticker_none():
    assert normalize_ticker(None) is None


def test_normalize_ticker_nan_string():
    assert normalize_ticker("nan") is None
    assert normalize_ticker("None") is None


def test_normalize_year_four_digit():
    assert normalize_year("Dec 2012") == 2012


def test_normalize_year_march():
    assert normalize_year("Mar 2015") == 2015


def test_normalize_year_hyphen():
    assert normalize_year("Mar-13") == 2013


def test_normalize_year_mixed_string_9m():
    assert normalize_year("Mar 2016 9m") == 2016


def test_normalize_year_mixed_string_15():
    assert normalize_year("Mar 2023 15") == 2023


def test_normalize_year_integer():
    assert normalize_year(2024) == 2024


def test_normalize_year_float():
    assert normalize_year(2021.0) == 2021


def test_normalize_year_ttm_returns_none():
    assert normalize_year("TTM") is None
    assert normalize_year("ttm") is None


def test_normalize_year_invalid():
    assert normalize_year("Unknown") is None
    assert normalize_year("Invalid123") is None


def test_normalize_year_none():
    assert normalize_year(None) is None
    assert normalize_year(np.nan) is None


def test_clean_column_name():
    assert clean_column_name("Company Name") == "company_name"
    assert clean_column_name("Net Profit Margin (%)") == "net_profit_margin"
    assert clean_column_name("  ROCE %  ") == "roce"
    assert clean_column_name("EPS (Rs.)") == "eps_rs"


def test_normalize_dataframe_columns_and_fields():
    raw_df = pd.DataFrame(
        {
            "Company ID": ["  infy  ", "tcs"],
            "Year": ["Dec 2020", "Mar-21"],
            "Sales (Cr)": [1000, 2000],
        }
    )
    norm_df = normalize_dataframe(raw_df)
    assert "company_id" in norm_df.columns
    assert "year" in norm_df.columns
    assert norm_df["company_id"].tolist() == ["INFY", "TCS"]
    assert norm_df["year"].tolist() == [2020, 2021]