"""
Design System, Custom CSS Tokens, and UI Component Helpers for N100 Dashboard.
Provides a modern, high-contrast, polished financial intelligence UI.
"""

import streamlit as st
import plotly.graph_objects as go


def apply_custom_css():
    """Injects modern CSS styling into the Streamlit application."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 1400px;
    }

    /* Glassmorphism Metric Cards */
    .kpi-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9));
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 0.75rem;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        border-color: #cbd5e1;
    }

    .kpi-title {
        font-size: 0.825rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }

    .kpi-subtitle {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 0.35rem;
    }

    /* Delta Pills */
    .delta-pill-pos {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #047857;
        background-color: #d1fae5;
        border-radius: 9999px;
        margin-top: 0.4rem;
    }

    .delta-pill-neg {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #b91c1c;
        background-color: #fee2e2;
        border-radius: 9999px;
        margin-top: 0.4rem;
    }

    .delta-pill-neutral {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
        background-color: #f1f5f9;
        border-radius: 9999px;
        margin-top: 0.4rem;
    }

    /* Badge Pills */
    .badge-pro {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.45rem 0.85rem;
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem 0.25rem 0.25rem 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }

    .badge-con {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.45rem 0.85rem;
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem 0.25rem 0.25rem 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }

    /* Page Header */
    .page-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.025em;
        margin-bottom: 0.25rem;
    }

    .page-subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }

    /* Benchmark Table Row Highlight */
    .benchmark-badge {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }

    /* Sidebar Header */
    .sidebar-header {
        padding: 1rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = None,
    delta: str = None,
    delta_type: str = "pos",
    icon: str = "📊",
):
    """Renders a stylized HTML KPI card with delta indicators."""
    delta_html = ""
    if delta:
        pill_class = "delta-pill-pos" if delta_type == "pos" else ("delta-pill-neg" if delta_type == "neg" else "delta-pill-neutral")
        delta_html = f'<div class="{pill_class}">{delta}</div>'

    sub_html = f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ""

    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title"><span>{icon}</span> {title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
        {sub_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = ""):
    """Renders a standard top-of-page header."""
    html = f"""
    <div style="margin-bottom: 1.5rem;">
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def apply_plotly_style(
    fig,
    height: int = 380,
    title: str = None,
    barmode: str = None,
    showlegend: bool = True,
    margin: dict = None,
    xaxis_title: str = None,
    yaxis_title: str = None,
):
    """
    Applies clean, uniform dashboard styling to any Plotly figure
    using direct attribute mutation to prevent keyword conflicts.
    """
    fig.layout.font = {"family": "Inter, sans-serif", "color": "#1e293b", "size": 12}
    fig.layout.paper_bgcolor = "rgba(0,0,0,0)"
    fig.layout.plot_bgcolor = "rgba(0,0,0,0)"
    fig.layout.hoverlabel = {
        "bgcolor": "#0f172a",
        "font": {"family": "Inter, sans-serif", "color": "#ffffff", "size": 12},
        "bordercolor": "rgba(0,0,0,0)",
    }
    fig.layout.height = height
    fig.layout.showlegend = showlegend
    fig.layout.margin = margin or {"l": 40, "r": 20, "t": 40, "b": 40}

    if title:
        fig.layout.title = {"text": title, "font": {"size": 14, "color": "#0f172a"}}
    if barmode:
        fig.layout.barmode = barmode

    if xaxis_title:
        fig.layout.xaxis.title = xaxis_title
    fig.layout.xaxis.gridcolor = "#f1f5f9"
    fig.layout.xaxis.zerolinecolor = "#e2e8f0"
    fig.layout.xaxis.tickfont = {"size": 11, "color": "#64748b"}

    if yaxis_title:
        fig.layout.yaxis.title = yaxis_title
    fig.layout.yaxis.gridcolor = "#f1f5f9"
    fig.layout.yaxis.zerolinecolor = "#e2e8f0"
    fig.layout.yaxis.tickfont = {"size": 11, "color": "#64748b"}

    return fig
