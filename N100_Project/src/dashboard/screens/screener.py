"""
screener.py — Financial Screener Screen
Features 10 metric sliders in sidebar, 6 preset strategy buttons with dynamic auto-fill,
live interactive results table, result counter label, and well-formed CSV export.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.dashboard.styles import apply_custom_css, render_header
from src.dashboard.utils.db import get_screener_universe
from src.screener.config_loader import load_screener_config
from src.screener.engine import apply_screener_filters

PRESET_DEFAULTS = {
    "Quality": {
        "roe_min": 15.0,
        "de_max": 1.0,
        "fcf_min": 0.0,
        "rev_cagr_min": 10.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 150.0,
        "pb_max": 30.0,
        "div_yield_min": 0.0,
        "icr_min": 0.0,
    },
    "Value": {
        "roe_min": 0.0,
        "de_max": 2.0,
        "fcf_min": -5000.0,
        "rev_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 20.0,
        "pb_max": 4.5,
        "div_yield_min": 1.0,
        "icr_min": 0.0,
    },
    "Growth": {
        "roe_min": 0.0,
        "de_max": 2.0,
        "fcf_min": -5000.0,
        "rev_cagr_min": 15.0,
        "pat_cagr_min": 20.0,
        "opm_min": 0.0,
        "pe_max": 150.0,
        "pb_max": 30.0,
        "div_yield_min": 0.0,
        "icr_min": 0.0,
    },
    "Dividend": {
        "roe_min": 0.0,
        "de_max": 3.0,
        "fcf_min": 0.0,
        "rev_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 150.0,
        "pb_max": 30.0,
        "div_yield_min": 2.0,
        "icr_min": 0.0,
    },
    "Debt-Free": {
        "roe_min": 12.0,
        "de_max": 0.05,
        "fcf_min": -5000.0,
        "rev_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 150.0,
        "pb_max": 30.0,
        "div_yield_min": 0.0,
        "icr_min": 0.0,
    },
    "Turnaround": {
        "roe_min": 0.0,
        "de_max": 3.0,
        "fcf_min": 0.0,
        "rev_cagr_min": 10.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 150.0,
        "pb_max": 30.0,
        "div_yield_min": 0.0,
        "icr_min": 0.0,
    },
}

DEFAULT_SLIDERS = {
    "roe_min": 0.0,
    "de_max": 5.0,
    "fcf_min": -10000.0,
    "rev_cagr_min": -20.0,
    "pat_cagr_min": -20.0,
    "opm_min": 0.0,
    "pe_max": 200.0,
    "pb_max": 50.0,
    "div_yield_min": 0.0,
    "icr_min": 0.0,
}


def render_screener_page():
    apply_custom_css()
    
    render_header(
        "🔎 Nifty 100 Financial Screener",
        "Multi-metric custom filtering engine with live responsive updates, preset strategies, and CSV export."
    )

    # Initialize session state for slider values if not present
    for k, v in DEFAULT_SLIDERS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # 6 Preset Buttons at top of page
    st.markdown("#### ⚡ Quick Preset Screeners")
    preset_cols = st.columns(6)
    
    preset_names = ["Quality", "Value", "Growth", "Dividend", "Debt-Free", "Turnaround"]
    for i, p_name in enumerate(preset_names):
        with preset_cols[i]:
            if st.button(f"🎯 {p_name}", use_container_width=True, key=f"btn_preset_{p_name}"):
                for k, v in PRESET_DEFAULTS[p_name].items():
                    st.session_state[k] = v
                st.rerun()

    st.markdown("---")

    # Sidebar: 10 Metric Sliders
    st.sidebar.markdown("### 🎛️ Screener Filter Sliders")

    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        for k, v in DEFAULT_SLIDERS.items():
            st.session_state[k] = v
        st.rerun()

    roe_min = st.sidebar.slider(
        "ROE Min (%)",
        min_value=-20.0,
        max_value=60.0,
        value=float(st.session_state["roe_min"]),
        step=1.0,
        key="slider_roe",
        on_change=lambda: st.session_state.update({"roe_min": st.session_state.slider_roe})
    )

    de_max = st.sidebar.slider(
        "Debt-to-Equity Max",
        min_value=0.0,
        max_value=10.0,
        value=float(st.session_state["de_max"]),
        step=0.05,
        key="slider_de",
        on_change=lambda: st.session_state.update({"de_max": st.session_state.slider_de})
    )

    fcf_min = st.sidebar.slider(
        "Free Cash Flow Min (₹ Cr)",
        min_value=-20000.0,
        max_value=30000.0,
        value=float(st.session_state["fcf_min"]),
        step=500.0,
        key="slider_fcf",
        on_change=lambda: st.session_state.update({"fcf_min": st.session_state.slider_fcf})
    )

    rev_cagr_min = st.sidebar.slider(
        "5-Yr Revenue CAGR Min (%)",
        min_value=-20.0,
        max_value=50.0,
        value=float(st.session_state["rev_cagr_min"]),
        step=1.0,
        key="slider_rev",
        on_change=lambda: st.session_state.update({"rev_cagr_min": st.session_state.slider_rev})
    )

    pat_cagr_min = st.sidebar.slider(
        "5-Yr PAT CAGR Min (%)",
        min_value=-30.0,
        max_value=60.0,
        value=float(st.session_state["pat_cagr_min"]),
        step=1.0,
        key="slider_pat",
        on_change=lambda: st.session_state.update({"pat_cagr_min": st.session_state.slider_pat})
    )

    opm_min = st.sidebar.slider(
        "Operating Profit Margin Min (%)",
        min_value=0.0,
        max_value=70.0,
        value=float(st.session_state["opm_min"]),
        step=1.0,
        key="slider_opm",
        on_change=lambda: st.session_state.update({"opm_min": st.session_state.slider_opm})
    )

    pe_max = st.sidebar.slider(
        "P/E Ratio Max",
        min_value=5.0,
        max_value=200.0,
        value=float(st.session_state["pe_max"]),
        step=1.0,
        key="slider_pe",
        on_change=lambda: st.session_state.update({"pe_max": st.session_state.slider_pe})
    )

    pb_max = st.sidebar.slider(
        "P/B Ratio Max",
        min_value=0.5,
        max_value=60.0,
        value=float(st.session_state["pb_max"]),
        step=0.5,
        key="slider_pb",
        on_change=lambda: st.session_state.update({"pb_max": st.session_state.slider_pb})
    )

    div_yield_min = st.sidebar.slider(
        "Dividend Yield Min (%)",
        min_value=0.0,
        max_value=10.0,
        value=float(st.session_state["div_yield_min"]),
        step=0.2,
        key="slider_div",
        on_change=lambda: st.session_state.update({"div_yield_min": st.session_state.slider_div})
    )

    icr_min = st.sidebar.slider(
        "Interest Coverage Min (Ratio)",
        min_value=0.0,
        max_value=50.0,
        value=float(st.session_state["icr_min"]),
        step=0.5,
        key="slider_icr",
        on_change=lambda: st.session_state.update({"icr_min": st.session_state.slider_icr})
    )

    # Ingest universe
    universe_df = get_screener_universe(year=2024)

    # Build active filters dict
    active_filters = {
        "return_on_equity_pct": {"min": roe_min},
        "debt_to_equity": {"max": de_max},
        "free_cash_flow_cr": {"min": fcf_min},
        "revenue_cagr_5yr": {"min": rev_cagr_min},
        "pat_cagr_5yr": {"min": pat_cagr_min},
        "operating_profit_margin_pct": {"min": opm_min},
        "pe_ratio": {"max": pe_max},
        "pb_ratio": {"max": pb_max},
        "dividend_yield_pct": {"min": div_yield_min},
        "interest_coverage": {"min": icr_min},
    }

    filtered_df = apply_screener_filters(universe_df, active_filters)

    # Display Result Count Label
    total_matches = len(filtered_df)
    total_universe = len(universe_df)

    col_count, col_download = st.columns([2, 1])

    with col_count:
        st.markdown(
            f"<div style='font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;'>"
            f"🎯 <span style='color: #0284c7;'>{total_matches}</span> of {total_universe} companies match your filters"
            f"</div>",
            unsafe_allow_html=True
        )

    # Prepare Display and CSV Table
    cols_to_show = [
        "company_id",
        "company_name",
        "broad_sector",
        "composite_quality_score",
        "return_on_equity_pct",
        "roce_percentage",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "interest_coverage",
    ]
    available_cols = [c for c in cols_to_show if c in filtered_df.columns]
    results_view = filtered_df[available_cols].copy()

    # Column Renaming
    rename_dict = {
        "company_id": "Ticker",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "composite_quality_score": "Score",
        "return_on_equity_pct": "ROE (%)",
        "roce_percentage": "ROCE (%)",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (₹ Cr)",
        "revenue_cagr_5yr": "5Y Rev CAGR (%)",
        "pat_cagr_5yr": "5Y PAT CAGR (%)",
        "operating_profit_margin_pct": "OPM (%)",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Div Yield (%)",
        "interest_coverage": "ICR",
    }
    display_df = results_view.rename(columns=rename_dict)

    with col_download:
        csv_data = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered CSV",
            data=csv_data,
            file_name="nifty100_screener_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if not display_df.empty:
        # Format table columns for visual presentation
        formatted_df = display_df.copy()
        if "Score" in formatted_df.columns:
            formatted_df["Score"] = formatted_df["Score"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
        if "ROE (%)" in formatted_df.columns:
            formatted_df["ROE (%)"] = formatted_df["ROE (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
        if "ROCE (%)" in formatted_df.columns:
            formatted_df["ROCE (%)"] = formatted_df["ROCE (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
        if "D/E" in formatted_df.columns:
            formatted_df["D/E"] = formatted_df["D/E"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
        if "FCF (₹ Cr)" in formatted_df.columns:
            formatted_df["FCF (₹ Cr)"] = formatted_df["FCF (₹ Cr)"].map(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")
        if "5Y Rev CAGR (%)" in formatted_df.columns:
            formatted_df["5Y Rev CAGR (%)"] = formatted_df["5Y Rev CAGR (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
        if "5Y PAT CAGR (%)" in formatted_df.columns:
            formatted_df["5Y PAT CAGR (%)"] = formatted_df["5Y PAT CAGR (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
        if "OPM (%)" in formatted_df.columns:
            formatted_df["OPM (%)"] = formatted_df["OPM (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
        if "P/E" in formatted_df.columns:
            formatted_df["P/E"] = formatted_df["P/E"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
        if "P/B" in formatted_df.columns:
            formatted_df["P/B"] = formatted_df["P/B"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
        if "Div Yield (%)" in formatted_df.columns:
            formatted_df["Div Yield (%)"] = formatted_df["Div Yield (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
        if "ICR" in formatted_df.columns:
            formatted_df["ICR"] = formatted_df["ICR"].map(lambda x: f"{x:.1f}x" if pd.notna(x) else "Inf")

        st.dataframe(
            formatted_df,
            hide_index=True,
            use_container_width=True,
            height=520,
        )
    else:
        st.warning("No companies meet all selected threshold criteria. Try loosening slider constraints.")

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Screener", page_icon="📈")
    render_screener_page()
