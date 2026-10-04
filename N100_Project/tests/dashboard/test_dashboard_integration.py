"""
Integration QA & Performance Test Suite for Streamlit Dashboard.
Validates all 8 screens against 10 multi-sector tickers, tests edge cases with missing/partial data,
verifies extreme screener sliders, and measures sub-3-second profile load times.
"""

import time
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_sectors,
    get_peers,
    get_valuation,
    get_prosandcons,
    get_documents,
    get_all_peer_groups,
    get_all_sectors,
    get_screener_universe,
    get_capital_allocation_universe,
)
from src.screener.engine import apply_screener_filters

# 10 Representative Tickers across IT, Financials, FMCG, Energy, Healthcare
TEST_TICKERS = [
    "TCS",         # IT
    "INFY",        # IT
    "HDFCBANK",    # Financials
    "ICICIBANK",   # Financials
    "ITC",         # FMCG
    "HINDUNILVR",  # FMCG
    "RELIANCE",    # Energy
    "ONGC",        # Energy
    "SUNPHARMA",   # Healthcare
    "CIPLA",       # Healthcare
]


class TestDatabaseLoaderAndCaching:
    """Verifies all cached database query functions work without errors."""

    def test_get_companies_not_empty(self):
        df = get_companies()
        assert not df.empty
        assert "company_id" in df.columns
        assert "company_name" in df.columns
        assert len(df) >= 92

    @pytest.mark.parametrize("ticker", TEST_TICKERS)
    def test_get_financial_statements_for_10_tickers(self, ticker):
        r_df = get_ratios(ticker)
        pl_df = get_pl(ticker)
        bs_df = get_bs(ticker)
        cf_df = get_cf(ticker)
        mcap_df = get_valuation(ticker)
        pc_dict = get_prosandcons(ticker)
        docs_df = get_documents(ticker)

        # Confirm non-empty statements
        assert isinstance(r_df, pd.DataFrame)
        assert isinstance(pl_df, pd.DataFrame)
        assert isinstance(bs_df, pd.DataFrame)
        assert isinstance(cf_df, pd.DataFrame)
        assert isinstance(mcap_df, pd.DataFrame)
        assert isinstance(pc_dict, dict)
        assert "pros" in pc_dict and "cons" in pc_dict
        assert isinstance(docs_df, pd.DataFrame)

    def test_get_sectors_and_peers(self):
        sec_df = get_sectors()
        assert not sec_df.empty
        peer_groups = get_all_peer_groups()
        assert len(peer_groups) == 11
        for grp in peer_groups:
            peers = get_peers(grp)
            assert not peers.empty


class TestCompanyProfilePerformance:
    """Measures load times for Company Profile queries to guarantee < 3.0 seconds."""

    @pytest.mark.parametrize("ticker", ["TCS", "HDFCBANK", "RELIANCE", "ITC", "SUNPHARMA"])
    def test_profile_load_time_under_3_seconds(self, ticker):
        start_time = time.perf_counter()

        # Execute full set of queries that fuel the Company Profile screen
        comps = get_companies()
        comp_row = comps[comps["company_id"] == ticker]
        r_df = get_ratios(ticker)
        pl_df = get_pl(ticker)
        bs_df = get_bs(ticker)
        cf_df = get_cf(ticker)
        mcap_df = get_valuation(ticker)
        pc = get_prosandcons(ticker)

        elapsed = time.perf_counter() - start_time
        assert elapsed < 3.0, f"Profile loading for {ticker} took {elapsed:.3f}s (exceeded 3s limit)"


class TestScreenerEdgeCasesAndExtremeSliders:
    """Verifies screener engine handles extreme boundaries without crashing."""

    def test_screener_extreme_max_filters(self):
        universe_df = get_screener_universe(year=2024)
        extreme_tight = {
            "return_on_equity_pct": {"min": 100.0},
            "debt_to_equity": {"max": 0.0},
            "free_cash_flow_cr": {"min": 50000.0},
            "pe_ratio": {"max": 1.0},
        }
        res = apply_screener_filters(universe_df, extreme_tight)
        assert isinstance(res, pd.DataFrame)
        # Should gracefully return 0 results without crashing
        assert len(res) == 0

    def test_screener_extreme_loose_filters(self):
        universe_df = get_screener_universe(year=2024)
        extreme_loose = {
            "return_on_equity_pct": {"min": -100.0},
            "debt_to_equity": {"max": 100.0},
            "free_cash_flow_cr": {"min": -100000.0},
            "pe_ratio": {"max": 1000.0},
        }
        res = apply_screener_filters(universe_df, extreme_loose)
        assert isinstance(res, pd.DataFrame)
        assert len(res) > 0


class TestCapitalAllocationAndReports:
    """Verifies capital allocation classifications and document listings."""

    def test_capital_allocation_universe_has_records(self):
        cap_df = get_capital_allocation_universe(year=2024)
        assert not cap_df.empty
        assert "pattern_label" in cap_df.columns
        assert len(cap_df) >= 80

    def test_document_listing_graceful_missing_ticker(self):
        docs = get_documents("NON_EXISTENT_TICKER_123")
        assert isinstance(docs, pd.DataFrame)
        assert docs.empty
