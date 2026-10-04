"""
Unit and Integration Tests for NLP Auto Pros/Cons Generator (Day 30).
"""

from pathlib import Path
import sqlite3
import pandas as pd
import pytest
from src.nlp.pros_cons_generator import evaluate_company_pros_cons, generate_all_pros_cons


def test_evaluate_company_pros_cons_synthetic():
    """Tests rule evaluation on synthetic strong company data."""
    ratios_df = pd.DataFrame([
        {"year": 2020, "return_on_equity_pct": 25.0, "debt_to_equity": 0.0, "free_cash_flow_cr": 500.0, "operating_profit_margin_pct": 30.0},
        {"year": 2021, "return_on_equity_pct": 26.0, "debt_to_equity": 0.0, "free_cash_flow_cr": 600.0, "operating_profit_margin_pct": 32.0},
        {"year": 2022, "return_on_equity_pct": 28.0, "debt_to_equity": 0.0, "free_cash_flow_cr": 700.0, "operating_profit_margin_pct": 31.0},
        {"year": 2023, "return_on_equity_pct": 29.0, "debt_to_equity": 0.0, "free_cash_flow_cr": 800.0, "operating_profit_margin_pct": 33.0},
        {"year": 2024, "return_on_equity_pct": 30.0, "debt_to_equity": 0.0, "free_cash_flow_cr": 900.0, "operating_profit_margin_pct": 34.0, "revenue_cagr_5yr": 18.0, "pat_cagr_5yr": 22.0, "eps_cagr_5yr": 20.0, "interest_coverage": 50.0},
    ])
    pnl_df = pd.DataFrame([
        {"year": 2020, "sales": 1000.0, "net_profit": 200.0, "operating_profit": 300.0, "eps": 20.0},
        {"year": 2021, "sales": 1200.0, "net_profit": 250.0, "operating_profit": 380.0, "eps": 25.0},
        {"year": 2022, "sales": 1400.0, "net_profit": 300.0, "operating_profit": 430.0, "eps": 30.0},
        {"year": 2023, "sales": 1650.0, "net_profit": 380.0, "operating_profit": 540.0, "eps": 38.0},
        {"year": 2024, "sales": 2000.0, "net_profit": 480.0, "operating_profit": 680.0, "eps": 48.0},
    ])
    bs_df = pd.DataFrame([
        {"year": 2020, "equity_capital": 100, "reserves": 900, "borrowings": 0, "other_liabilities": 200, "total_assets": 1200},
        {"year": 2024, "equity_capital": 100, "reserves": 2000, "borrowings": 0, "other_liabilities": 300, "total_assets": 2400},
    ])
    cf_df = pd.DataFrame([
        {"year": 2024, "operating_activity": 1000.0, "investing_activity": -100.0, "financing_activity": -200.0},
    ])
    mc_df = pd.DataFrame([
        {"year": 2024, "market_cap_crore": 50000.0, "pe_ratio": 25.0, "dividend_yield_pct": 2.5},
    ])

    results = evaluate_company_pros_cons(
        company_id="TESTCO",
        ratios_df=ratios_df,
        pnl_df=pnl_df,
        bs_df=bs_df,
        cf_df=cf_df,
        mc_df=mc_df,
    )

    assert len(results) > 0
    pros = [r for r in results if r["type"] == "pro"]
    cons = [r for r in results if r["type"] == "con"]
    assert len(pros) >= 1
    assert len(cons) >= 1
    for r in results:
        assert r["confidence_pct"] > 60.0


def test_generate_all_pros_cons_coverage(tmp_path):
    """Tests 100% coverage guarantee for pros and cons across all companies."""
    out_csv = tmp_path / "pros_cons_generated.csv"
    res_df = generate_all_pros_cons(output_path=out_csv)

    assert not res_df.empty
    assert "company_id" in res_df.columns
    assert "type" in res_df.columns
    assert "rule_id" in res_df.columns
    assert "text" in res_df.columns
    assert "confidence_pct" in res_df.columns

    # Check minimum confidence
    assert (res_df["confidence_pct"] > 60.0).all()

    # Check at least 1 pro and 1 con per company
    pros_grouped = res_df[res_df["type"] == "pro"].groupby("company_id").size()
    cons_grouped = res_df[res_df["type"] == "con"].groupby("company_id").size()

    all_companies = res_df["company_id"].unique()
    for cid in all_companies:
        assert cid in pros_grouped.index, f"Missing pro for {cid}"
        assert cid in cons_grouped.index, f"Missing con for {cid}"
        assert pros_grouped[cid] >= 1
        assert cons_grouped[cid] >= 1
