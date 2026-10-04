"""
Unit tests for 6 Preset Screeners (Day 16).
Verifies that all 6 presets return between 5 and 50 companies and make business sense.
"""

import pytest
from src.screener.engine import load_screener_universe, run_preset_screener, run_all_presets


@pytest.fixture(scope="module")
def screener_universe():
    return load_screener_universe()


def test_quality_compounder_preset(screener_universe):
    # ROE > 15%, D/E < 1.0, FCF > 0, Revenue CAGR 5yr > 10%
    results = run_preset_screener("quality_compounder", universe_df=screener_universe)
    assert 5 <= len(results) <= 50, f"Quality Compounder returned {len(results)} companies"
    # Spot-check known quality compounders
    cids = set(results["company_id"])
    assert any(c in cids for c in ["TCS", "INFY", "ITC", "BEL", "HAL", "ABB"])


def test_value_pick_preset(screener_universe):
    # P/E < 20, P/B < 4.5, D/E < 2.0, Dividend Yield > 1%
    results = run_preset_screener("value_pick", universe_df=screener_universe)
    assert 5 <= len(results) <= 50, f"Value Pick returned {len(results)} companies"


def test_growth_accelerator_preset(screener_universe):
    # PAT CAGR 5yr > 20%, Revenue CAGR 5yr > 15%, D/E < 2.0
    results = run_preset_screener("growth_accelerator", universe_df=screener_universe)
    assert 5 <= len(results) <= 50, f"Growth Accelerator returned {len(results)} companies"


def test_dividend_champion_preset(screener_universe):
    # Dividend Yield > 2%, Dividend Payout < 80%, FCF > 0
    results = run_preset_screener("dividend_champion", universe_df=screener_universe)
    assert 5 <= len(results) <= 50, f"Dividend Champion returned {len(results)} companies"


def test_debt_free_blue_chip_preset(screener_universe):
    # D/E <= 0.05, ROE > 12%, Sales > 5000 Cr
    results = run_preset_screener("debt_free_blue_chip", universe_df=screener_universe)
    assert 5 <= len(results) <= 50, f"Debt-Free Blue Chip returned {len(results)} companies"


def test_turnaround_watch_preset(screener_universe):
    # Revenue CAGR 3yr > 10%, FCF positive, D/E declining YoY
    results = run_preset_screener("turnaround_watch", universe_df=screener_universe)
    assert 5 <= len(results) <= 50, f"Turnaround Watch returned {len(results)} companies"


def test_run_all_presets_returns_six_dataframes(screener_universe):
    all_presets = run_all_presets(universe_df=screener_universe)
    assert len(all_presets) == 6
    expected_keys = {
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    }
    assert set(all_presets.keys()) == expected_keys
    for name, df in all_presets.items():
        assert 5 <= len(df) <= 50, f"Preset '{name}' returned {len(df)} companies (out of [5, 50] range)"
