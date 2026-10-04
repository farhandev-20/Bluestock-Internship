"""
home.py — Executive Dashboard & Market Overview Screen
Features 6 summary KPI tiles, dynamic year selector (2019-2024),
Plotly sector breakdown donut chart, and Top-5 Composite Quality Score leaderboard.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.styles import apply_custom_css, render_kpi_card, render_header, apply_plotly_style
from src.dashboard.utils.db import get_companies, get_sectors, get_screener_universe, get_valuation

def render_home_page():
    apply_custom_css()
    
    # Sidebar: Year Selector
    st.sidebar.markdown("### ⚙️ Dashboard Controls")
    selected_year = st.sidebar.selectbox(
        "Financial Fiscal Year",
        options=[2024, 2023, 2022, 2021, 2020, 2019],
        index=0,
        help="Select fiscal year to update summary KPIs and rankings across the market."
    )
    
    render_header(
        "📊 Nifty 100 Financial Intelligence Overview",
        f"Constituent fundamentals, aggregate ratios, sector weights, and quality leaderboards for FY{selected_year}."
    )

    # Ingest data for selected year
    try:
        universe_df = get_screener_universe(year=selected_year)
    except Exception:
        universe_df = get_companies()

    # Calculate 6 summary KPIs
    total_companies = len(universe_df)
    
    # ROE
    valid_roe = universe_df["return_on_equity_pct"].dropna() if "return_on_equity_pct" in universe_df.columns else pd.Series()
    avg_roe = valid_roe.mean() if not valid_roe.empty else 0.0

    # PE
    valid_pe = universe_df["pe_ratio"].dropna() if "pe_ratio" in universe_df.columns else pd.Series()
    valid_pe = valid_pe[valid_pe > 0]
    median_pe = valid_pe.median() if not valid_pe.empty else 0.0

    # DE
    valid_de = universe_df["debt_to_equity"].dropna() if "debt_to_equity" in universe_df.columns else pd.Series()
    median_de = valid_de.median() if not valid_de.empty else 0.0

    # Rev CAGR 5yr
    valid_cagr = universe_df["revenue_cagr_5yr"].dropna() if "revenue_cagr_5yr" in universe_df.columns else pd.Series()
    median_cagr = valid_cagr.median() if not valid_cagr.empty else 0.0

    # Debt-free count (D/E <= 0.05 or 0)
    debt_free_count = (valid_de <= 0.05).sum() if not valid_de.empty else 0

    # 6 KPI Tiles in 6 columns
    kpi_cols = st.columns(6)

    with kpi_cols[0]:
        render_kpi_card(
            title="Avg ROE",
            value=f"{avg_roe:.1f}%",
            subtitle="Capital Efficiency",
            delta=f"{'+' if avg_roe >= 15 else ''}{avg_roe - 15:.1f}% vs 15% bench",
            delta_type="pos" if avg_roe >= 15 else "neg",
            icon="🎯"
        )
    with kpi_cols[1]:
        render_kpi_card(
            title="Median P/E",
            value=f"{median_pe:.1f}x",
            subtitle="Market Valuation",
            delta="Sector Relative" if median_pe > 0 else "N/A",
            delta_type="neutral",
            icon="💎"
        )
    with kpi_cols[2]:
        render_kpi_card(
            title="Median D/E",
            value=f"{median_de:.2f}",
            subtitle="Balance Sheet Leverage",
            delta="Conservative" if median_de < 0.5 else "Moderate",
            delta_type="pos" if median_de < 0.5 else "neutral",
            icon="⚖️"
        )
    with kpi_cols[3]:
        render_kpi_card(
            title="Total Companies",
            value=f"{total_companies}",
            subtitle="Nifty 100 Universe",
            delta="Tracked Equities",
            delta_type="pos",
            icon="🏛️"
        )
    with kpi_cols[4]:
        render_kpi_card(
            title="5Yr Rev CAGR",
            value=f"{median_cagr:.1f}%",
            subtitle="Top-Line Expansion",
            delta=f"{'+' if median_cagr >= 10 else ''}{median_cagr:.1f}% Median",
            delta_type="pos" if median_cagr >= 10 else "neutral",
            icon="🚀"
        )
    with kpi_cols[5]:
        render_kpi_card(
            title="Debt-Free",
            value=f"{debt_free_count}",
            subtitle="D/E ≤ 0.05 Ratio",
            delta=f"{(debt_free_count/max(1, total_companies))*100:.0f}% of Universe",
            delta_type="pos",
            icon="🛡️"
        )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2 Main visual columns: Sector Breakdown Donut & Top-5 Quality Leaderboard
    col_chart, col_leaders = st.columns([1.1, 1.2], gap="large")

    with col_chart:
        st.markdown("#### 🍩 Sector Breakdown & Allocation")
        st.caption("Distribution of Nifty 100 universe constituents across broad industry sectors.")
        
        sec_df = get_sectors()
        if not sec_df.empty:
            sec_counts = sec_df["broad_sector"].value_counts().reset_index()
            sec_counts.columns = ["Sector", "Companies Count"]

            fig_donut = px.pie(
                sec_counts,
                values="Companies Count",
                names="Sector",
                hole=0.55,
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            apply_plotly_style(
                fig_donut,
                height=380,
                showlegend=True,
                margin=dict(l=10, r=10, t=20, b=80),
            )
            fig_donut.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=10))
            )
            fig_donut.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Constituents: %{value}<br>Weight: %{percent}<extra></extra>",
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Sector distribution data currently unavailable.")

    with col_leaders:
        st.markdown("#### 🏆 Top-5 Companies by Quality Score")
        st.caption("Ranked by P10/P90 winsorised composite score (Profitability, Cash Quality, Growth, Leverage).")

        if "composite_quality_score" in universe_df.columns:
            top_5 = universe_df.sort_values(by="composite_quality_score", ascending=False).head(5).copy()
            top_5["Rank"] = [f"#{i+1}" for i in range(len(top_5))]
            
            # Format display table
            display_cols = {
                "Rank": "Rank",
                "company_name": "Company Name",
                "broad_sector": "Sector",
                "composite_quality_score": "Score (0-100)",
                "return_on_equity_pct": "ROE (%)",
                "roce_percentage": "ROCE (%)",
                "pe_ratio": "P/E",
                "free_cash_flow_cr": "FCF (Cr)",
            }
            
            top_5_display = top_5[[c for c in display_cols.keys() if c in top_5.columns]].rename(columns=display_cols)
            
            # Format values nicely
            if "Score (0-100)" in top_5_display.columns:
                top_5_display["Score (0-100)"] = top_5_display["Score (0-100)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
            if "ROE (%)" in top_5_display.columns:
                top_5_display["ROE (%)"] = top_5_display["ROE (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            if "ROCE (%)" in top_5_display.columns:
                top_5_display["ROCE (%)"] = top_5_display["ROCE (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            if "P/E" in top_5_display.columns:
                top_5_display["P/E"] = top_5_display["P/E"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
            if "FCF (Cr)" in top_5_display.columns:
                top_5_display["FCF (Cr)"] = top_5_display["FCF (Cr)"].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")

            st.dataframe(
                top_5_display,
                hide_index=True,
                use_container_width=True,
                height=340,
            )
        else:
            st.info("Quality rankings will appear here.")

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Home", page_icon="📈")
    render_home_page()
