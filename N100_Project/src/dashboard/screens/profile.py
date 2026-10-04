"""
profile.py — Company Profile Screen
Features text search with autocomplete, comprehensive company card,
6 KPI tiles, 10-year revenue/profit bar chart, ROE/ROCE trend chart,
and stylized Pros & Cons badges.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.dashboard.styles import apply_custom_css, render_kpi_card, render_header, apply_plotly_style
from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_valuation,
    get_prosandcons,
)


def render_profile_page():
    apply_custom_css()
    
    comps_df = get_companies()
    
    # Create search options list: "TCS - Tata Consultancy Services Ltd"
    ticker_to_name = dict(zip(comps_df["company_id"], comps_df["company_name"]))
    options = [f"{cid} - {name}" for cid, name in ticker_to_name.items()]
    
    st.sidebar.markdown("### 🔍 Search Company")
    search_input = st.sidebar.selectbox(
        "Select or Type Ticker / Name",
        options=[""] + options,
        index=options.index("TCS - Tata Consultancy Services Ltd") + 1 if "TCS - Tata Consultancy Services Ltd" in options else 0,
        help="Type or select any Nifty 100 constituent company.",
    )

    if not search_input:
        st.warning("⚠️ Ticker not found — please try another")
        return

    selected_ticker = search_input.split(" - ")[0].strip()
    
    # Retrieve company metadata
    comp_row = comps_df[comps_df["company_id"] == selected_ticker]
    if comp_row.empty:
        st.error("⚠️ Ticker not found — please try another")
        return
    
    comp = comp_row.iloc[0]
    cname = comp.get("company_name", selected_ticker)
    sector = comp.get("broad_sector") or "Unassigned"
    sub_sector = comp.get("sub_sector") or "General"
    about = comp.get("about_company") or "Leading Nifty 100 benchmark enterprise."
    website = comp.get("website")
    nse_url = comp.get("nse_profile")
    bse_url = comp.get("bse_profile")
    
    # Render Company Header Card
    header_html = f"""
    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border-radius: 12px; padding: 1.5rem 1.75rem; color: #ffffff; margin-bottom: 1.5rem; border: 1px solid #334155;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.35rem;">
                    <span style="font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em;">{cname}</span>
                    <span style="background: #3b82f6; color: white; padding: 0.2rem 0.6rem; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">{selected_ticker}</span>
                </div>
                <div style="color: #94a3b8; font-size: 0.95rem; font-weight: 500;">
                    Sector: <b style="color: #cbd5e1;">{sector}</b> &nbsp;|&nbsp; Sub-sector: <b style="color: #cbd5e1;">{sub_sector}</b>
                </div>
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                {f'<a href="{website}" target="_blank" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.35rem 0.75rem; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 500;">🌐 Website</a>' if website else ''}
                {f'<a href="{nse_url}" target="_blank" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.35rem 0.75rem; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 500;">📈 NSE Profile</a>' if nse_url else ''}
                {f'<a href="{bse_url}" target="_blank" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 0.35rem 0.75rem; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 500;">🏛️ BSE Profile</a>' if bse_url else ''}
            </div>
        </div>
        <div style="margin-top: 1rem; color: #cbd5e1; font-size: 0.875rem; line-height: 1.5; border-top: 1px solid #334155; padding-top: 0.75rem;">
            {about}
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # Ingest financial data
    ratios_df = get_ratios(selected_ticker)
    pl_df = get_pl(selected_ticker)
    cf_df = get_cf(selected_ticker)
    mcap_df = get_valuation(selected_ticker)

    # Latest KPIs calculation
    latest_r = ratios_df.iloc[-1] if not ratios_df.empty else pd.Series()
    latest_pl = pl_df.iloc[-1] if not pl_df.empty else pd.Series()
    latest_cf = cf_df.iloc[-1] if not cf_df.empty else pd.Series()

    roe = latest_r.get("return_on_equity_pct")
    roce = comp.get("roce_percentage") or latest_r.get("roce_percentage")
    npm = latest_r.get("net_profit_margin_pct")
    de = latest_r.get("debt_to_equity")
    rev_cagr = latest_r.get("revenue_cagr_5yr")
    fcf = latest_r.get("free_cash_flow_cr")

    # If FCF not in ratios, compute from cashflow
    if (fcf is None or pd.isna(fcf)) and not latest_cf.empty:
        cfo = latest_cf.get("operating_activity") or 0.0
        cfi = latest_cf.get("investing_activity") or 0.0
        fcf = cfo + cfi

    # 6 KPI Tiles
    kpi_cols = st.columns(6)

    with kpi_cols[0]:
        render_kpi_card(
            title="ROE (%)",
            value=f"{roe:.1f}%" if pd.notna(roe) else "N/A",
            subtitle="Return on Equity",
            delta=f"{'+' if (roe or 0) >= 15 else ''}{(roe or 0) - 15:.1f}% vs 15%" if pd.notna(roe) else None,
            delta_type="pos" if (roe or 0) >= 15 else "neg",
            icon="🎯",
        )
    with kpi_cols[1]:
        render_kpi_card(
            title="ROCE (%)",
            value=f"{roce:.1f}%" if pd.notna(roce) else "N/A",
            subtitle="Capital Employed",
            delta="Capital Efficiency",
            delta_type="pos" if (roce or 0) >= 15 else "neutral",
            icon="⚡",
        )
    with kpi_cols[2]:
        render_kpi_card(
            title="Net Margin (%)",
            value=f"{npm:.1f}%" if pd.notna(npm) else "N/A",
            subtitle="PAT Margin",
            delta="Pricing Power" if (npm or 0) >= 15 else "Normalized",
            delta_type="pos" if (npm or 0) >= 15 else "neutral",
            icon="💰",
        )
    with kpi_cols[3]:
        render_kpi_card(
            title="Debt / Equity",
            value=f"{de:.2f}" if pd.notna(de) else "0.00",
            subtitle="Financial Leverage",
            delta="Zero/Low Debt" if (de or 0) <= 0.1 else ("Moderate" if (de or 0) <= 1.0 else "High Leverage"),
            delta_type="pos" if (de or 0) <= 0.5 else "neg",
            icon="⚖️",
        )
    with kpi_cols[4]:
        render_kpi_card(
            title="5Yr Rev CAGR",
            value=f"{rev_cagr:.1f}%" if pd.notna(rev_cagr) else "N/A",
            subtitle="Top-Line Growth",
            delta="High Growth" if (rev_cagr or 0) >= 12 else "Steady",
            delta_type="pos" if (rev_cagr or 0) >= 10 else "neutral",
            icon="📈",
        )
    with kpi_cols[5]:
        render_kpi_card(
            title="Free Cash Flow",
            value=f"₹{fcf:,.0f} Cr" if pd.notna(fcf) else "N/A",
            subtitle="Latest Fiscal Year",
            delta="Cash Generative" if (fcf or 0) > 0 else "Negative FCF",
            delta_type="pos" if (fcf or 0) > 0 else "neg",
            icon="💵",
        )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2 Charts Side-by-Side: 10-Yr Bar Chart for Revenue/Profit & Dual-Axis Line for ROE/ROCE
    col_bar, col_line = st.columns(2, gap="large")

    with col_bar:
        st.markdown("#### 📊 10-Year Revenue & Net Profit Trend")
        st.caption("Annual Sales vs Net Profit (PAT) in ₹ Crores.")

        if not pl_df.empty and "sales" in pl_df.columns:
            # Sort by year
            plot_pl = pl_df.sort_values(by="year").tail(10)
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=plot_pl["year"].astype(str),
                y=plot_pl["sales"],
                name="Sales / Revenue",
                marker_color="#3b82f6",
                hovertemplate="<b>FY%{x}</b><br>Sales: ₹%{y:,.0f} Cr<extra></extra>",
            ))
            fig_bar.add_trace(go.Bar(
                x=plot_pl["year"].astype(str),
                y=plot_pl["net_profit"],
                name="Net Profit (PAT)",
                marker_color="#10b981",
                hovertemplate="<b>FY%{x}</b><br>PAT: ₹%{y:,.0f} Cr<extra></extra>",
            ))

            apply_plotly_style(
                fig_bar,
                height=380,
                barmode="group",
                yaxis_title="₹ in Crores",
            )
            fig_bar.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Historical statement data not available.")

    with col_line:
        st.markdown("#### 📈 ROE & ROCE Multi-Line History")
        st.caption("10-year trajectory of return on capital and equity ratios.")

        if not ratios_df.empty and "return_on_equity_pct" in ratios_df.columns:
            plot_r = ratios_df.sort_values(by="year").tail(10)

            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=plot_r["year"].astype(str),
                y=plot_r["return_on_equity_pct"],
                mode="lines+markers",
                name="ROE (%)",
                line=dict(color="#0284c7", width=3),
                marker=dict(size=7),
                hovertemplate="<b>FY%{x}</b><br>ROE: %{y:.1f}%<extra></extra>",
            ))

            # Derive ROCE/OPM if available in ratios or pl
            if "operating_profit_margin_pct" in plot_r.columns:
                fig_line.add_trace(go.Scatter(
                    x=plot_r["year"].astype(str),
                    y=plot_r["operating_profit_margin_pct"],
                    mode="lines+markers",
                    name="OPM (%)",
                    line=dict(color="#f59e0b", width=2.5, dash="dot"),
                    marker=dict(size=6),
                    hovertemplate="<b>FY%{x}</b><br>OPM: %{y:.1f}%<extra></extra>",
                ))

            apply_plotly_style(
                fig_line,
                height=380,
                yaxis_title="Percentage (%)",
            )
            fig_line.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Historical ratio trajectory not available.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Pros and Cons Section
    st.markdown("#### ⚖️ Investment Strengths & Key Risk Considerations")
    st.caption("AI-analyzed fundamental thesis, balance sheet health indicators, and operational factors.")

    pc_data = get_prosandcons(selected_ticker)
    pros = pc_data.get("pros", [])
    cons = pc_data.get("cons", [])

    col_pros, col_cons = st.columns(2, gap="large")

    with col_pros:
        st.markdown("<div style='font-weight: 700; color: #166534; font-size: 1.05rem; margin-bottom: 0.5rem;'>✅ Key Strengths (Pros)</div>", unsafe_allow_html=True)
        if pros:
            for p in pros:
                st.markdown(f'<div class="badge-pro"><span>✔</span> {p}</div>', unsafe_allow_html=True)
        else:
            st.write("No major flagged pros.")

    with col_cons:
        st.markdown("<div style='font-weight: 700; color: #991b1b; font-size: 1.05rem; margin-bottom: 0.5rem;'>❌ Key Risks & Concerns (Cons)</div>", unsafe_allow_html=True)
        if cons:
            for c in cons:
                st.markdown(f'<div class="badge-con"><span>✖</span> {c}</div>', unsafe_allow_html=True)
        else:
            st.write("No major flagged concerns.")

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Company Profile", page_icon="📈")
    render_profile_page()
