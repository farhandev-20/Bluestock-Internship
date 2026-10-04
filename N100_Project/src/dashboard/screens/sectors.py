"""
sectors.py — Sector Analysis Screen
Features sector dropdown selector, dynamic Plotly bubble chart
(X = Revenue, Y = ROE, Bubble Size = Market Cap, Color = Sub-Sector),
and sector median KPI comparative bar chart.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.styles import apply_custom_css, render_header, apply_plotly_style
from src.dashboard.utils.db import get_all_sectors, get_screener_universe


def render_sectors_page():
    apply_custom_css()

    render_header(
        "🌐 Sector Dynamics & Bubble Positioning",
        "Macro sectoral landscape mapping revenue scale against return on equity, market capitalisation, and cross-sector median benchmarks."
    )

    # Ingest universe
    universe_df = get_screener_universe(year=2024)
    all_sectors = sorted([s for s in universe_df["broad_sector"].dropna().unique()])

    # Sidebar: Sector Selector
    st.sidebar.markdown("### 🏛️ Sector Filter")
    selected_sector = st.sidebar.selectbox(
        "Select Industry Sector",
        options=["All Sectors"] + all_sectors,
        index=0,
        help="Filter the bubble chart by specific broad sector or view the entire universe.",
    )

    # Filter data for bubble chart
    if selected_sector != "All Sectors":
        bubble_data = universe_df[universe_df["broad_sector"] == selected_sector].copy()
    else:
        bubble_data = universe_df.copy()

    # Drop missing values in key dimensions
    bubble_data = bubble_data.dropna(subset=["sales", "return_on_equity_pct"]).copy()

    # Fill market cap for sizing
    bubble_data["market_cap_size"] = bubble_data["market_cap_crore"].fillna(5000.0).clip(lower=1000.0)

    # Bubble Chart
    st.markdown(f"#### 🫧 Sector Positioning Bubble Chart ({selected_sector})")
    st.caption("X-Axis: Revenue (₹ Cr) &nbsp;|&nbsp; Y-Axis: ROE (%) &nbsp;|&nbsp; Bubble Size: Market Cap (₹ Cr) &nbsp;|&nbsp; Color: Sub-Sector")

    if not bubble_data.empty:
        fig_bubble = px.scatter(
            bubble_data,
            x="sales",
            y="return_on_equity_pct",
            size="market_cap_size",
            color="sub_sector" if "sub_sector" in bubble_data.columns else "broad_sector",
            hover_name="company_name",
            hover_data={
                "company_id": True,
                "sales": ":,.0f",
                "return_on_equity_pct": ":.1f",
                "market_cap_crore": ":,.0f",
                "pe_ratio": ":.1f",
                "market_cap_size": False,
            },
            labels={
                "sales": "Revenue / Sales (₹ Cr)",
                "return_on_equity_pct": "Return on Equity (ROE %)",
                "sub_sector": "Sub-Sector",
                "broad_sector": "Broad Sector",
            },
            size_max=45,
            color_discrete_sequence=px.colors.qualitative.Dark24,
        )

        apply_plotly_style(
            fig_bubble,
            height=460,
            margin=dict(l=40, r=40, t=20, b=80),
            xaxis_title="Revenue / Sales (₹ Crores)",
            yaxis_title="Return on Equity (ROE %)",
        )
        fig_bubble.update_layout(
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(size=10))
        )

        st.plotly_chart(fig_bubble, use_container_width=True)
    else:
        st.info("Insufficient data to plot bubble chart for this sector.")

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # Sector Median KPI Bar Chart
    st.markdown("#### 📊 Cross-Sector Median KPI Benchmark Comparison")
    st.caption("Comparative median statistics across all broad sectors in the Nifty 100 universe.")

    # Compute sector medians
    median_rows = []
    for sec_name, group in universe_df.groupby("broad_sector"):
        if not sec_name or pd.isna(sec_name):
            continue
        
        roe_med = group["return_on_equity_pct"].dropna().median()
        opm_med = group["operating_profit_margin_pct"].dropna().median() if "operating_profit_margin_pct" in group.columns else np.nan
        pe_med = group[group["pe_ratio"] > 0]["pe_ratio"].dropna().median() if "pe_ratio" in group.columns else np.nan
        de_med = group["debt_to_equity"].dropna().median() if "debt_to_equity" in group.columns else np.nan
        rev_med = group["revenue_cagr_5yr"].dropna().median() if "revenue_cagr_5yr" in group.columns else np.nan

        median_rows.append({
            "Sector": sec_name,
            "Median ROE (%)": roe_med,
            "Median OPM (%)": opm_med,
            "Median P/E": pe_med,
            "Median D/E": de_med,
            "Median 5Y Rev CAGR (%)": rev_med,
            "Constituents": len(group),
        })

    sec_med_df = pd.DataFrame(median_rows)

    if not sec_med_df.empty:
        # User selects metric to compare across sectors
        kpi_to_compare = st.selectbox(
            "Select KPI for Sector Median Comparison",
            options=["Median ROE (%)", "Median OPM (%)", "Median P/E", "Median D/E", "Median 5Y Rev CAGR (%)"],
            index=0,
        )

        sorted_sec = sec_med_df.sort_values(by=kpi_to_compare, ascending=True)

        fig_bar = px.bar(
            sorted_sec,
            x=kpi_to_compare,
            y="Sector",
            orientation="h",
            text=sorted_sec[kpi_to_compare].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-"),
            color=kpi_to_compare,
            color_continuous_scale="Blues",
        )
        apply_plotly_style(
            fig_bar,
            height=380,
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis_title=kpi_to_compare,
            yaxis_title="",
        )
        fig_bar.update_layout(coloraxis_showscale=False)
        fig_bar.update_traces(textposition="outside")

        st.plotly_chart(fig_bar, use_container_width=True)

        # Detailed Table
        st.dataframe(
            sec_med_df.sort_values(by="Median ROE (%)", ascending=False),
            hide_index=True,
            use_container_width=True,
        )


if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Sector Analysis", page_icon="📈")
    render_sectors_page()
