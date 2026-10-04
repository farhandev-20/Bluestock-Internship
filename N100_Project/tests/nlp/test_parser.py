"""
Unit and Integration Tests for NLP Analysis Text Parser (Day 29).
"""

from pathlib import Path
import pandas as pd
import pytest
from src.nlp.parser import cross_validate_parsed_cagr, parse_analysis_data, parse_metric_text


def test_parse_metric_text_patterns():
    """Tests regex extraction from various text formats."""
    assert parse_metric_text("10 Years: 21%") == (10, 21.0)
    assert parse_metric_text("5 Years: 8%") == (5, 8.0)
    assert parse_metric_text("3 Years: -4.5%") == (3, -4.5)
    assert parse_metric_text("1 Year: 13.2%") == (1, 13.2)
    assert parse_metric_text("Last Year: 17%") == (1, 17.0)
    assert parse_metric_text("TTM: 43.5%") == (1, 43.5)
    assert parse_metric_text("Invalid text string") is None
    assert parse_metric_text("") is None
    assert parse_metric_text(None) is None


def test_parse_analysis_data_execution(tmp_path):
    """Tests batch parsing of analysis dataset."""
    parsed_csv = tmp_path / "analysis_parsed.csv"
    failures_csv = tmp_path / "parse_failures.csv"

    parsed_df, failures_df = parse_analysis_data(
        output_parsed_path=parsed_csv,
        output_failures_path=failures_csv,
    )

    assert not parsed_df.empty
    assert "company_id" in parsed_df.columns
    assert "metric_type" in parsed_df.columns
    assert "period_years" in parsed_df.columns
    assert "value_pct" in parsed_df.columns
    assert parsed_csv.exists()
    assert failures_csv.exists()


def test_cross_validate_parsed_cagr(tmp_path):
    """Tests cross validation against ratio engine."""
    sample_df = pd.DataFrame([
        {"company_id": "TCS", "metric_type": "compounded_sales_growth", "period_years": 5, "value_pct": 12.0},
        {"company_id": "TCS", "metric_type": "compounded_profit_growth", "period_years": 5, "value_pct": 10.0},
    ])
    val_df = cross_validate_parsed_cagr(sample_df)
    assert isinstance(val_df, pd.DataFrame)
