"""
Unit and Integration Tests for Valuation Analytics Module.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.analytics.valuation import (
    calculate_fcf_yield,
    classify_valuation_flag,
    load_valuation_universe,
    export_valuation_summary_excel,
    export_valuation_flags_csv,
    run_valuation_module,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestValuationCalculations:
    """Tests for unit calculation functions in valuation module."""

    def test_calculate_fcf_yield_normal(self):
        # FCF = 5000 Cr, MCap = 100000 Cr -> 5.0%
        yield_pct = calculate_fcf_yield(5000.0, 100000.0)
        assert yield_pct == pytest.approx(5.0, 0.001)

    def test_calculate_fcf_yield_negative(self):
        # FCF = -2000 Cr, MCap = 50000 Cr -> -4.0%
        yield_pct = calculate_fcf_yield(-2000.0, 50000.0)
        assert yield_pct == pytest.approx(-4.0, 0.001)

    def test_calculate_fcf_yield_none_or_zero_mcap(self):
        assert calculate_fcf_yield(None, 50000.0) is None
        assert calculate_fcf_yield(5000.0, None) is None
        assert calculate_fcf_yield(5000.0, 0.0) is None
        assert calculate_fcf_yield(5000.0, -100.0) is None

    def test_classify_valuation_flag_caution(self):
        # Sector median = 20.0, PE = 35.0 (> 30.0) -> Caution
        assert classify_valuation_flag(35.0, 20.0) == "Caution"

    def test_classify_valuation_flag_discount(self):
        # Sector median = 20.0, PE = 12.0 (< 14.0) -> Discount
        assert classify_valuation_flag(12.0, 20.0) == "Discount"

    def test_classify_valuation_flag_fair(self):
        # Sector median = 20.0, PE = 22.0 (between 14 and 30) -> Fair
        assert classify_valuation_flag(22.0, 20.0) == "Fair"
        assert classify_valuation_flag(14.0, 20.0) == "Fair"
        assert classify_valuation_flag(30.0, 20.0) == "Fair"

    def test_classify_valuation_flag_edge_cases(self):
        assert classify_valuation_flag(None, 20.0) == "Fair"
        assert classify_valuation_flag(25.0, None) == "Fair"
        assert classify_valuation_flag(np.nan, 20.0) == "Fair"
        assert classify_valuation_flag(25.0, 0.0) == "Fair"


class TestValuationUniverseAndExport:
    """Integration tests for universe loading and file exports."""

    def test_load_valuation_universe(self):
        df = load_valuation_universe()
        assert len(df) == 92
        expected_cols = [
            "company_id",
            "company_name",
            "sector",
            "P/E",
            "P/B",
            "EV/EBITDA",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag",
        ]
        assert list(df.columns) == expected_cols
        assert set(df["flag"].unique()).issubset({"Caution", "Discount", "Fair"})

    def test_export_and_run_valuation_module(self, tmp_path):
        res = run_valuation_module(output_dir=tmp_path)
        assert res["total_companies"] == 92
        assert res["excel_path"].exists()
        assert res["csv_path"].exists()

        # Check excel
        excel_df = pd.read_excel(res["excel_path"])
        assert len(excel_df) == 92

        # Check csv (only Caution & Discount)
        csv_df = pd.read_csv(res["csv_path"])
        assert set(csv_df["flag"].unique()).issubset({"Caution", "Discount"})
        assert len(csv_df) > 0
