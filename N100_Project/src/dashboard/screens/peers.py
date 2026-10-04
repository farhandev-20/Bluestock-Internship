"""
peers.py — Peer Comparison Screen
Features 11 peer group selector, interactive Plotly Scatterpolar radar chart
comparing selected company vs peer group average across 8 axes, and side-by-side KPI table
with highlighted benchmark company.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.dashboard.styles import apply_custom_css, render_header, apply_plotly_style
from src.dashboard.utils.db import (
    get_all_peer_groups,
    get_peers,
    get_screener_universe,
)
from src.analytics.peer import RADAR_AXES


def render_peers_page():
    apply_custom_css()

    render_header(
        "👥 Peer Comparison & Radar Benchmarking",
        "Deep-dive comparative analysis across 11 industry peer cohorts with 8-dimensional radar profiling."
    )

    peer_groups = get_all_peer_groups()
    if not peer_groups:
        st.error("No peer groups found in the database.")
        return

    # Sidebar: Peer Group Selector
    st.sidebar.markdown("### 🏢 Peer Cohort Selection")
    selected_group = st.sidebar.selectbox(
        "Select Industry Peer Group",
        options=peer_groups,
        index=peer_groups.index("IT Services") if "IT Services" in peer_groups else 0,
        help="Select one of the 11 specialized industry peer groups.",
    )

    # Ingest peer members and universe
    peers_df = get_peers(selected_group)
    universe_df = get_screener_universe(year=2024)

    if peers_df.empty:
        st.warning(f"No constituents found for peer group: {selected_group}")
        return

    # Merge peer group members with full universe metrics
    peer_merged = pd.merge(peers_df, universe_df, on="company_id", how="inner")
    
    # Clean duplicates if any
    peer_merged = peer_merged.drop_duplicates(subset=["company_id"]).reset_index(drop=True)

    # Company Selector within Group
    member_options = [
        f"{row['company_id']} - {row['company_name_x'] if 'company_name_x' in row else row.get('company_name', row['company_id'])}"
        for _, row in peer_merged.iterrows()
    ]

    selected_member_str = st.sidebar.selectbox(
        "Select Company to Benchmark",
        options=member_options,
        index=0,
    )
    selected_cid = selected_member_str.split(" - ")[0].strip()

    # 8 Axes for Radar Chart
    axes_keys = [k[0] for k in RADAR_AXES]
    axes_labels = [k[1] for k in RADAR_AXES]

    # Selected company row
    target_row = peer_merged[peer_merged["company_id"] == selected_cid].iloc[0]

    # Compute normalized scores (0 to 100) for company & peer group average
    comp_scores = []
    peer_scores = []

    for k in axes_keys:
        # Min and Max from full universe for consistent scaling
        if k in universe_df.columns:
            univ_series = universe_df[k].dropna()
            q_low = univ_series.quantile(0.05)
            q_high = univ_series.quantile(0.95)
        else:
            q_low, q_high = 0.0, 100.0

        # Company score
        c_val = target_row.get(k)
        if pd.isna(c_val) or c_val is None:
            c_score = 50.0
        elif k == "debt_to_equity":
            # Invert: low D/E -> 100
            c_score = max(0.0, min(100.0, 100.0 / (c_val + 1.0)))
        elif k == "composite_quality_score":
            c_score = float(c_val)
        else:
            if q_high > q_low:
                c_score = max(0.0, min(100.0, (c_val - q_low) / (q_high - q_low) * 100.0))
            else:
                c_score = 50.0
        comp_scores.append(c_score)

        # Peer average score
        if k in peer_merged.columns:
            p_vals = peer_merged[k].dropna()
            if k == "debt_to_equity":
                p_score = (100.0 / (p_vals + 1.0)).mean() if not p_vals.empty else 50.0
            elif k == "composite_quality_score":
                p_score = p_vals.mean() if not p_vals.empty else 50.0
            else:
                if q_high > q_low and not p_vals.empty:
                    p_score = ((p_vals.mean() - q_low) / (q_high - q_low) * 100.0)
                else:
                    p_score = 50.0
        else:
            p_score = 50.0
        peer_scores.append(max(0.0, min(100.0, p_score)))

    # Close the radar loop
    radar_labels = axes_labels + [axes_labels[0]]
    comp_radar_scores = comp_scores + [comp_scores[0]]
    peer_radar_scores = peer_scores + [peer_scores[0]]

    # 2-Column layout: Radar Chart & Cohort Summary
    col_radar, col_summary = st.columns([1.3, 1.0], gap="large")

    with col_radar:
        st.markdown(f"#### 🎯 8-Axis Polar Radar: **{selected_cid}** vs Peer Group Avg")
        st.caption(f"Comparing **{selected_cid}** against {len(peer_merged)} companies in **{selected_group}**.")

        fig_radar = go.Figure()

        # Company polygon
        fig_radar.add_trace(go.Scatterpolar(
            r=comp_radar_scores,
            theta=radar_labels,
            fill="toself",
            name=f"{selected_cid} (Company)",
            line=dict(color="#0284c7", width=3),
            fillcolor="rgba(2, 132, 199, 0.3)",
        ))

        # Peer Average polygon
        fig_radar.add_trace(go.Scatterpolar(
            r=peer_radar_scores,
            theta=radar_labels,
            fill="none",
            name=f"{selected_group} Average",
            line=dict(color="#f43f5e", width=2.5, dash="dash"),
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[25, 50, 75, 100],
                    ticktext=["25", "50", "75", "100"],
                    gridcolor="#e2e8f0",
                ),
                angularaxis=dict(
                    gridcolor="#e2e8f0",
                    tickfont=dict(size=11, family="Inter, sans-serif", color="#1e293b"),
                ),
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=30, b=50),
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    with col_summary:
        st.markdown(f"#### 🏅 Cohort Benchmark Summary")
        st.caption("Key peer group statistics and benchmark anchor.")

        bm_row = peer_merged[peer_merged["is_benchmark"] == 1]
        bm_name = bm_row.iloc[0]["company_name_x"] if not bm_row.empty else "N/A"
        bm_ticker = bm_row.iloc[0]["company_id"] if not bm_row.empty else "N/A"

        st.markdown(
            f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; font-weight: 600; color: #64748b; text-transform: uppercase;">Peer Group</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0f172a;">{selected_group}</div>
                <div style="margin-top: 0.75rem; font-size: 0.9rem; color: #334155;">
                    <b>Constituents:</b> {len(peer_merged)} companies<br>
                    <b>Designated Benchmark:</b> <span style="background: #fef3c7; color: #92400e; padding: 0.15rem 0.4rem; border-radius: 4px; font-weight: 700;">★ {bm_ticker}</span> ({bm_name})
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Quick stats for selected company in group
        target_score = target_row.get("composite_quality_score", 0)
        target_roe = target_row.get("return_on_equity_pct", 0)
        target_pe = target_row.get("pe_ratio", 0)

        st.markdown(
            f"""
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 1.25rem;">
                <div style="font-size: 0.85rem; font-weight: 600; color: #166534; text-transform: uppercase;">Selected Ticker: {selected_cid}</div>
                <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #14532d;">
                    <b>Composite Quality Score:</b> {target_score:.1f} / 100<br>
                    <b>Return on Equity (ROE):</b> {target_roe:.1f}%<br>
                    <b>Valuation Multiple (P/E):</b> {target_pe:.1f}x
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Side-by-Side KPI Table for All Companies in Selected Group
    st.markdown(f"#### 📋 Side-by-Side KPI Table — {selected_group} Cohort")
    st.caption("Comprehensive peer metrics matrix. Benchmark company highlighted with ★ badge.")

    table_cols = [
        "company_id",
        "company_name_x",
        "is_benchmark",
        "composite_quality_score",
        "return_on_equity_pct",
        "roce_percentage",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pe_ratio",
        "pb_ratio",
    ]
    avail_tbl_cols = [c for c in table_cols if c in peer_merged.columns]
    tbl_df = peer_merged[avail_tbl_cols].copy()

    tbl_df["is_benchmark"] = tbl_df["is_benchmark"].map(lambda x: "★ Benchmark" if bool(x) else "Peer")

    tbl_rename = {
        "company_id": "Ticker",
        "company_name_x": "Company Name",
        "is_benchmark": "Status",
        "composite_quality_score": "Quality Score",
        "return_on_equity_pct": "ROE (%)",
        "roce_percentage": "ROCE (%)",
        "net_profit_margin_pct": "Net Margin (%)",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (₹ Cr)",
        "revenue_cagr_5yr": "5Y Rev CAGR (%)",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
    }
    tbl_display = tbl_df.rename(columns=tbl_rename)

    # Format numbers
    if "Quality Score" in tbl_display.columns:
        tbl_display["Quality Score"] = tbl_display["Quality Score"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    if "ROE (%)" in tbl_display.columns:
        tbl_display["ROE (%)"] = tbl_display["ROE (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    if "ROCE (%)" in tbl_display.columns:
        tbl_display["ROCE (%)"] = tbl_display["ROCE (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    if "Net Margin (%)" in tbl_display.columns:
        tbl_display["Net Margin (%)"] = tbl_display["Net Margin (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    if "D/E" in tbl_display.columns:
        tbl_display["D/E"] = tbl_display["D/E"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    if "FCF (₹ Cr)" in tbl_display.columns:
        tbl_display["FCF (₹ Cr)"] = tbl_display["FCF (₹ Cr)"].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")
    if "5Y Rev CAGR (%)" in tbl_display.columns:
        tbl_display["5Y Rev CAGR (%)"] = tbl_display["5Y Rev CAGR (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    if "P/E" in tbl_display.columns:
        tbl_display["P/E"] = tbl_display["P/E"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    if "P/B" in tbl_display.columns:
        tbl_display["P/B"] = tbl_display["P/B"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

    st.dataframe(
        tbl_display,
        hide_index=True,
        use_container_width=True,
    )

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Peer Comparison", page_icon="📈")
    render_peers_page()
