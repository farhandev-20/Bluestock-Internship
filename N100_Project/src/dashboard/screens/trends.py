"""
trends.py — Trend Analysis Screen
Features company search, multi-metric overlay selector (up to 3 metrics),
10-year historical trajectory line chart with YoY % change annotations on data points,
and longitudinal statistics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.dashboard.styles import apply_custom_css, render_header, apply_plotly_style
from src.dashboard.utils.db import (
    get_companies,
    get_pl,
    get_ratios,
    get_bs,
    get_cf,
    get_valuation,
)

METRIC_OPTIONS = {
    "Sales / Revenue (₹ Cr)": ("pl", "sales", "₹ Cr"),
    "Net Profit / PAT (₹ Cr)": ("pl", "net_profit", "₹ Cr"),
    "Operating Profit / EBITDA (₹ Cr)": ("pl", "operating_profit", "₹ Cr"),
    "Return on Equity / ROE (%)": ("ratios", "return_on_equity_pct", "%"),
    "Operating Profit Margin / OPM (%)": ("pl", "opm_percentage", "%"),
    "Earnings Per Share / EPS (₹)": ("pl", "eps", "₹"),
    "Free Cash Flow (₹ Cr)": ("ratios", "free_cash_flow_cr", "₹ Cr"),
    "Total Borrowings / Debt (₹ Cr)": ("bs", "borrowings", "₹ Cr"),
    "Total Assets (₹ Cr)": ("bs", "total_assets", "₹ Cr"),
    "Market Capitalisation (₹ Cr)": ("mcap", "market_cap_crore", "₹ Cr"),
    "P/E Ratio (x)": ("mcap", "pe_ratio", "x"),
}


def render_trends_page():
    apply_custom_css()

    render_header(
        "📈 Longitudinal Trend & Financial Trajectory",
        "Multi-metric overlay analysis across 10 fiscal years with YoY compounding rates and point-in-time annotations."
    )

    comps_df = get_companies()
    ticker_to_name = dict(zip(comps_df["company_id"], comps_df["company_name"]))
    options = [f"{cid} - {name}" for cid, name in ticker_to_name.items()]

    st.sidebar.markdown("### 🔍 Trend Analysis Controls")
    selected_comp_str = st.sidebar.selectbox(
        "Select Company",
        options=options,
        index=0,
    )
    selected_cid = selected_comp_str.split(" - ")[0].strip()

    # Multi-metric Selector (Max 3 metrics)
    selected_metrics = st.sidebar.multiselect(
        "Select Metrics to Overlay (Up to 3)",
        options=list(METRIC_OPTIONS.keys()),
        default=["Sales / Revenue (₹ Cr)", "Net Profit / PAT (₹ Cr)"],
        max_selections=3,
        help="Overlay up to 3 financial statement metrics or valuation ratios on the trend chart."
    )

    if not selected_metrics:
        st.warning("Please select at least 1 metric from the sidebar to visualize trends.")
        return

    # Ingest historical datasets
    pl_df = get_pl(selected_cid).sort_values(by="year")
    ratios_df = get_ratios(selected_cid).sort_values(by="year")
    bs_df = get_bs(selected_cid).sort_values(by="year")
    cf_df = get_cf(selected_cid).sort_values(by="year")
    mcap_df = get_valuation(selected_cid).sort_values(by="year")

    # Build master year index from all available years
    all_years = sorted(list(set(
        pl_df["year"].dropna().tolist() + 
        ratios_df["year"].dropna().tolist() + 
        bs_df["year"].dropna().tolist() + 
        mcap_df["year"].dropna().tolist()
    )))

    if not all_years:
        st.info("No historical data available for this company.")
        return

    # Take last 10 available years
    plot_years = all_years[-10:]
    trend_master = pd.DataFrame({"year": plot_years})

    # Merge each source
    if not pl_df.empty:
        trend_master = pd.merge(trend_master, pl_df, on="year", how="left")
    if not ratios_df.empty:
        trend_master = pd.merge(trend_master, ratios_df, on="year", how="left", suffixes=("", "_ratio"))
    if not bs_df.empty:
        trend_master = pd.merge(trend_master, bs_df, on="year", how="left", suffixes=("", "_bs"))
    if not mcap_df.empty:
        trend_master = pd.merge(trend_master, mcap_df, on="year", how="left", suffixes=("", "_mcap"))

    # Plotly Trend Chart
    fig_trend = go.Figure()
    palette = ["#0284c7", "#10b981", "#f59e0b", "#8b5cf6"]

    for idx, m_name in enumerate(selected_metrics):
        source_tbl, col_name, unit = METRIC_OPTIONS[m_name]
        
        if col_name not in trend_master.columns:
            continue

        series = trend_master[col_name]
        years = trend_master["year"]
        color = palette[idx % len(palette)]

        # Compute YoY % change
        yoy_changes = []
        text_annotations = []
        prev_val = None

        for v in series:
            if prev_val is not None and prev_val != 0 and pd.notna(v) and pd.notna(prev_val):
                pct = ((v - prev_val) / abs(prev_val)) * 100.0
                yoy_changes.append(pct)
                sign = "+" if pct >= 0 else ""
                text_annotations.append(f"{sign}{pct:.0f}%")
            else:
                yoy_changes.append(None)
                text_annotations.append("")
            if pd.notna(v):
                prev_val = v

        # Add line trace with annotations
        fig_trend.add_trace(go.Scatter(
            x=years.astype(str),
            y=series,
            mode="lines+markers+text",
            name=m_name,
            text=text_annotations,
            textposition="top center",
            textfont=dict(size=10, color=color, family="Inter, sans-serif"),
            line=dict(color=color, width=3),
            marker=dict(size=7),
            hovertemplate=f"<b>FY%{{x}}</b><br>{m_name}: %{{y:,.2f}} {unit}<extra></extra>",
        ))

    apply_plotly_style(
        fig_trend,
        height=480,
        title=f"10-Year Historical Trajectory — {selected_cid} (with YoY % Growth)",
        xaxis_title="Fiscal Year",
        yaxis_title="Value / Scale",
    )
    fig_trend.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Summary Statistics Table
    st.markdown("#### 📊 Metric Growth & Performance Summary")
    
    summary_rows = []
    for m_name in selected_metrics:
        _, col_name, unit = METRIC_OPTIONS[m_name]
        if col_name in trend_master.columns:
            valid_vals = trend_master[col_name].dropna()
            if not valid_vals.empty:
                start_val = valid_vals.iloc[0]
                end_val = valid_vals.iloc[-1]
                n_yrs = len(valid_vals) - 1
                
                # 10yr CAGR if positive
                if n_yrs > 0 and start_val > 0 and end_val > 0:
                    cagr = ((end_val / start_val) ** (1 / n_yrs) - 1) * 100.0
                    cagr_str = f"{cagr:.1f}%"
                else:
                    cagr_str = "N/A"

                summary_rows.append({
                    "Metric": m_name,
                    "Earliest Value": f"{start_val:,.2f} {unit}",
                    "Latest Value": f"{end_val:,.2f} {unit}",
                    "Minimum": f"{valid_vals.min():,.2f} {unit}",
                    "Maximum": f"{valid_vals.max():,.2f} {unit}",
                    "Average": f"{valid_vals.mean():,.2f} {unit}",
                    "Period CAGR": cagr_str,
                })

    if summary_rows:
        st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Trend Analysis", page_icon="📈")
    render_trends_page()
