"""
Unit tests for Peer Percentile Ranking (Day 18).
Validates 10 core metrics percentile ranking across 11 peer groups,
D/E inversion, SQLite table population, and unassigned company handling.
"""

import sqlite3
import pandas as pd
import pytest

from src.analytics.peer import (
    compute_peer_percentiles,
    populate_peer_percentiles_table,
    get_company_peer_percentiles,
    DEFAULT_DB_PATH,
)


def test_peer_percentiles_eleven_peer_groups():
    long_df, merged_df = compute_peer_percentiles()
    groups = long_df["peer_group_name"].unique()
    assert len(groups) == 11, f"Expected 11 peer groups, found {len(groups)}"

    # 10 metrics computed per company
    metrics = long_df["metric"].unique()
    assert len(metrics) == 10


def test_de_percentile_inversion():
    """
    D/E ratio ranking must be inverted so lower D/E yields higher percentile rank.
    """
    long_df, _ = compute_peer_percentiles()
    de_ranks = long_df[long_df["metric"] == "debt_to_equity"]

    # Group by peer group and check that lower D/E has higher rank
    for grp_name, grp_df in de_ranks.groupby("peer_group_name"):
        valid = grp_df.dropna(subset=["value"])
        if len(valid) >= 2:
            min_de_row = valid.loc[valid["value"].idxmin()]
            max_de_row = valid.loc[valid["value"].idxmax()]
            if min_de_row["value"] < max_de_row["value"]:
                assert min_de_row["percentile_rank"] >= max_de_row["percentile_rank"]


def test_it_services_highest_roe_has_highest_rank():
    """
    Day 21 Verification: Within IT Services peer group,
    the company with highest ROE should have the highest ROE percentile rank.
    """
    long_df, _ = compute_peer_percentiles()
    it_roe = long_df[(long_df["peer_group_name"] == "IT Services") & (long_df["metric"] == "return_on_equity_pct")]

    assert not it_roe.empty
    highest_roe_row = it_roe.loc[it_roe["value"].idxmax()]
    assert highest_roe_row["percentile_rank"] == 100.0, f"Expected 100.0% rank for highest ROE in IT Services, got {highest_roe_row['percentile_rank']}"


def test_sqlite_peer_percentiles_table_population():
    long_df, _ = compute_peer_percentiles()
    count = populate_peer_percentiles_table(long_df, db_path=DEFAULT_DB_PATH)

    assert count >= 500, f"Expected >= 500 records in peer_percentiles, found {count}"

    conn = sqlite3.connect(str(DEFAULT_DB_PATH))
    df = pd.read_sql_query("SELECT * FROM peer_percentiles LIMIT 5;", conn)
    conn.close()

    expected_cols = {"id", "company_id", "peer_group_name", "metric", "value", "percentile_rank", "year"}
    assert set(df.columns) == expected_cols


def test_unassigned_company_message():
    """
    For companies not in any peer group: return message 'No peer group assigned' without raising an error.
    """
    res = get_company_peer_percentiles("NON_EXISTENT_CO", db_path=DEFAULT_DB_PATH)
    assert res == "No peer group assigned"
