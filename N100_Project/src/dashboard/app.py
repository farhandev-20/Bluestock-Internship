"""
Main Entry Point for Nifty 100 Financial Intelligence Dashboard.
Multi-page Streamlit application providing 8 analytical screens.
"""

from pathlib import Path
import sys
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.styles import apply_custom_css
from src.dashboard.screens.home import render_home_page
from src.dashboard.screens.profile import render_profile_page
from src.dashboard.screens.screener import render_screener_page
from src.dashboard.screens.peers import render_peers_page
from src.dashboard.screens.trends import render_trends_page
from src.dashboard.screens.sectors import render_sectors_page
from src.dashboard.screens.capital import render_capital_page
from src.dashboard.screens.reports import render_reports_page

# 1. Page Config
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Apply Custom Styling
apply_custom_css()

# 3. Streamlit Modern Multi-Page Navigation Definition
pages = {
    "Market Overview": [
        st.Page(render_home_page, title="Executive Overview", icon="📊", default=True),
        st.Page(render_profile_page, title="Company Profile", icon="🏢"),
    ],
    "Screening & Peers": [
        st.Page(render_screener_page, title="Financial Screener", icon="🔎"),
        st.Page(render_peers_page, title="Peer Comparison", icon="👥"),
    ],
    "Analytics & Macro": [
        st.Page(render_trends_page, title="Trend Analysis", icon="📈"),
        st.Page(render_sectors_page, title="Sector Analysis", icon="🌐"),
        st.Page(render_capital_page, title="Capital Allocation", icon="🗺️"),
        st.Page(render_reports_page, title="Annual Reports", icon="📑"),
    ],
}

pg = st.navigation(pages)

# Sidebar Branding Header
st.sidebar.markdown(
    """
    <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 1rem;">
        <div style="font-size: 1.25rem; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 0.5rem;">
            <span>📈</span> Nifty 100 Intel
        </div>
        <div style="font-size: 0.8rem; color: #64748b; font-weight: 500;">
            Institutional Equity Research Platform
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Run Selected Page
pg.run()
