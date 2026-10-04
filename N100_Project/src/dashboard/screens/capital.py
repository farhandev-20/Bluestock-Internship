"""
capital.py — Capital Allocation Map Screen
Features Plotly interactive treemap visualizing all Nifty 100 constituents
grouped by the 8 capital allocation patterns (CFO/CFI/CFF signs),
pattern summary cards, and constituent drilldown table.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.dashboard.styles import apply_custom_css, render_header, render_kpi_card, apply_plotly_style
from src.dashboard.utils.db import get_capital_allocation_universe

PATTERN_DESCRIPTIONS = {
    "Reinvestor": "CFO > 0, CFI < 0, CFF < 0: Generating strong cash from operations, heavily reinvesting into capex/growth, and returning cash to shareholders or paying down debt.",
    "Shareholder Returns": "CFO > 0, CFI < 0, CFF < 0 with CFO/PAT > 1.2: High cash conversion paying substantial dividends and buybacks alongside disciplined reinvestment.",
    "Cash Accumulator": "CFO > 0, CFI > 0, CFF > 0: Positive operational cash, liquidating or earning investment returns, and raising debt/equity.",
    "Liquidating Assets": "CFO > 0, CFI > 0, CFF < 0: Cash generative operations supplemented by asset divestitures or investment liquidations while repaying obligations.",
    "Growth Funded by Debt": "CFO < 0, CFI < 0, CFF > 0: Rapid expansion phase consuming cash for operations and capital expenditure, financed primarily by debt/equity infusions.",
    "Distress Signal": "CFO < 0, CFI > 0, CFF > 0 or CFF < 0: Negative operating cash flow offset by emergency asset sales and debt drawdowns.",
    "Pre-Revenue": "CFO < 0, CFI < 0, CFF < 0: Consuming cash across all three activities; depleting reserves.",
    "Mixed": "Mixed operating or financing cash flow profile.",
}


def render_capital_page():
    apply_custom_css()

    render_header(
        "🗺️ Capital Allocation Matrix & Cash Flow Archetypes",
        "Visualizing constituent cash generation, reinvestment appetite, and capital allocation frameworks via the 8-Pattern Classifier."
    )

    cap_df = get_capital_allocation_universe(year=2024)

    if cap_df.empty:
        st.warning("Capital allocation data currently unavailable.")
        return

    # Ensure non-null string hierarchy for Plotly treemap
    cap_df["pattern_label"] = cap_df["pattern_label"].fillna("Mixed").replace("", "Mixed").astype(str)
    cap_df["broad_sector"] = cap_df["broad_sector"].fillna("Diversified").replace("", "Diversified").astype(str)
    cap_df["company_name"] = cap_df["company_name"].fillna(cap_df["company_id"]).replace("", "Company").astype(str)

    # Sizing proxy: Absolute CFO or Sales or Market Cap
    cap_df["chart_size"] = cap_df["market_cap_crore"].fillna(5000.0).clip(lower=1000.0)

    # 4 Top summary cards on pattern distribution
    pattern_counts = cap_df["pattern_label"].value_counts()
    top_patterns = pattern_counts.head(4).index.tolist()

    cols_kpi = st.columns(4)
    icons = ["🏗️", "💎", "🔋", "⚠️"]
    for i, p_name in enumerate(top_patterns):
        cnt = pattern_counts[p_name]
        pct = (cnt / len(cap_df)) * 100
        with cols_kpi[i]:
            render_kpi_card(
                title=p_name,
                value=f"{cnt} Companies",
                subtitle=f"{pct:.0f}% of Universe",
                delta="Primary Archetype" if i == 0 else "Cohort",
                delta_type="pos" if "Reinvestor" in p_name or "Shareholder" in p_name else "neutral",
                icon=icons[i % len(icons)],
            )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Treemap Chart
    st.markdown("#### 🌳 Capital Allocation Treemap (Grouped by Pattern & Sector)")
    st.caption("Hierarchical mapping: Capital Allocation Pattern ➔ Broad Sector ➔ Company. Sized by Market Cap.")

    fig_tree = px.treemap(
        cap_df,
        path=["pattern_label", "broad_sector", "company_name"],
        values="chart_size",
        color="pattern_label",
        color_discrete_sequence=px.colors.qualitative.Safe,
        hover_data={
            "company_id": True,
            "operating_activity": ":,.0f",
            "investing_activity": ":,.0f",
            "financing_activity": ":,.0f",
            "free_cash_flow_cr": ":,.0f",
            "chart_size": False,
        },
    )

    fig_tree.update_layout(
        margin=dict(l=10, r=10, t=20, b=20),
        height=520,
        font=dict(family="Inter, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig_tree.update_traces(
        hovertemplate="<b>%{label}</b><br>Pattern / Sector: %{parent}<br>Market Cap Weight: %{value:,.0f} Cr<extra></extra>"
    )

    st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Pattern Drilldown Filter & Table
    st.markdown("#### 🔍 Pattern Constituent Breakdown")
    
    all_patterns = sorted(cap_df["pattern_label"].unique().tolist())
    selected_pattern = st.selectbox(
        "Filter Companies by Capital Allocation Pattern",
        options=["All Patterns"] + all_patterns,
        index=0,
    )

    if selected_pattern != "All Patterns":
        drilldown_df = cap_df[cap_df["pattern_label"] == selected_pattern].copy()
        st.info(f"ℹ️ **{selected_pattern}:** {PATTERN_DESCRIPTIONS.get(selected_pattern, '')}")
    else:
        drilldown_df = cap_df.copy()

    # Format table for display
    display_cols = {
        "company_id": "Ticker",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "pattern_label": "Pattern Archetype",
        "cfo_sign": "CFO",
        "cfi_sign": "CFI",
        "cff_sign": "CFF",
        "operating_activity": "CFO (₹ Cr)",
        "investing_activity": "CFI (₹ Cr)",
        "financing_activity": "CFF (₹ Cr)",
        "free_cash_flow_cr": "FCF (₹ Cr)",
        "composite_quality_score": "Quality Score",
    }
    avail_cols = [c for c in display_cols.keys() if c in drilldown_df.columns]
    table_view = drilldown_df[avail_cols].rename(columns=display_cols).copy()

    # Format numbers
    if "CFO (₹ Cr)" in table_view.columns:
        table_view["CFO (₹ Cr)"] = table_view["CFO (₹ Cr)"].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")
    if "CFI (₹ Cr)" in table_view.columns:
        table_view["CFI (₹ Cr)"] = table_view["CFI (₹ Cr)"].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")
    if "CFF (₹ Cr)" in table_view.columns:
        table_view["CFF (₹ Cr)"] = table_view["CFF (₹ Cr)"].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")
    if "FCF (₹ Cr)" in table_view.columns:
        table_view["FCF (₹ Cr)"] = table_view["FCF (₹ Cr)"].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")
    if "Quality Score" in table_view.columns:
        table_view["Quality Score"] = table_view["Quality Score"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")

    st.dataframe(
        table_view,
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Capital Allocation", page_icon="📈")
    render_capital_page()
