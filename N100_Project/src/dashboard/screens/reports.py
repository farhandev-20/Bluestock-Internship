"""
reports.py — Intelligence Reports & Regulatory Filings Repository Screen
Features:
1. Institutional 2-page Tearsheet PDF viewer & download
2. 11 Sector Benchmark PDF Reports download
3. Portfolio Summary Master PDF (92 Pages) download
4. BSE Annual Reports filing repository with live URL availability status check
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import requests

from src.dashboard.styles import apply_custom_css, render_header
from src.dashboard.utils.db import get_companies, get_documents

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = PROJECT_ROOT / "reports"
TEARSHEET_DIR = REPORTS_DIR / "tearsheets"
SECTOR_DIR = REPORTS_DIR / "sector"
PORTFOLIO_PDF = REPORTS_DIR / "portfolio" / "portfolio_summary.pdf"


@st.cache_data(ttl=3600)
def check_url_status(url: str) -> bool:
    """
    Checks if a document URL is reachable.
    Returns True if status is 200/302, False if 404 or connection error.
    """
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return False
    try:
        response = requests.head(url, timeout=2.0, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False


def render_reports_page():
    apply_custom_css()

    render_header(
        "📑 Intelligence Reports & Document Repository",
        "Generate and download institutional 2-page company tearsheets, sector benchmark PDFs, portfolio summaries, and access BSE filings."
    )

    tab_tearsheet, tab_sector, tab_portfolio, tab_bse = st.tabs([
        "📄 Company Tearsheet (PDF)",
        "📊 Sector Reports (11 PDFs)",
        "📁 Portfolio Summary (92 Pages)",
        "🏛️ BSE Annual Reports Filing Repository"
    ])

    comps_df = get_companies()
    ticker_to_name = dict(zip(comps_df["company_id"], comps_df["company_name"]))
    options = [f"{cid} - {name}" for cid, name in ticker_to_name.items()]

    # =========================================================================
    # TAB 1: COMPANY TEARSHEET
    # =========================================================================
    with tab_tearsheet:
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            selected_comp_str = st.selectbox(
                "Select Company for Institutional Tearsheet",
                options=options,
                index=0,
                key="sb_tearsheet_comp",
            )
            selected_cid = selected_comp_str.split(" - ")[0].strip()
            cname = ticker_to_name.get(selected_cid, selected_cid)

        pdf_path = TEARSHEET_DIR / f"{selected_cid}_tearsheet.pdf"
        
        st.markdown("---")
        if pdf_path.exists():
            file_bytes = pdf_path.read_bytes()
            size_kb = len(file_bytes) / 1024
            
            c_info, c_btn = st.columns([3, 1])
            with c_info:
                st.markdown(f"#### 📄 2-Page Tearsheet: **{cname}** (`{selected_cid}`)")
                st.markdown(f"**Format:** Institutional PDF | **Pages:** 2 | **File Size:** {size_kb:.1f} KB")
                st.caption("Includes Navy Header, 6 KPI Tiles, 10-Yr Revenue/PAT bar chart, ROE/OPM line chart, Balance Sheet composition, Cash Flow waterfall, Capital Allocation badge, and NLP Pros & Cons with confidence scores.")
            
            with c_btn:
                st.download_button(
                    label=f"⬇️ Download {selected_cid} Tearsheet",
                    data=file_bytes,
                    file_name=f"{selected_cid}_tearsheet.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        else:
            st.warning(f"Tearsheet for {selected_cid} is being compiled or unavailable.")

    # =========================================================================
    # TAB 2: SECTOR BENCHMARK REPORTS
    # =========================================================================
    with tab_sector:
        st.markdown("#### 📊 Sector Benchmark PDF Reports (11 Sectors)")
        st.caption("Each sector report contains median KPI benchmarks and full constituent company comparison tables with 8 key fundamental metrics.")

        sector_files = sorted(list(SECTOR_DIR.glob("*.pdf"))) if SECTOR_DIR.exists() else []
        if sector_files:
            sec_cols = st.columns(2)
            for idx, s_pdf in enumerate(sector_files):
                col = sec_cols[idx % 2]
                sec_name = s_pdf.stem.replace("_report", "").replace("_", " ")
                size_kb = s_pdf.stat().st_size / 1024
                with col:
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem;">📊 {sec_name}</div>
                        <div style="color: #64748b; font-size: 0.8rem; margin-top: 2px;">Size: {size_kb:.1f} KB | Format: PDF Benchmark</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.download_button(
                        label=f"⬇️ Download {sec_name} Report",
                        data=s_pdf.read_bytes(),
                        file_name=s_pdf.name,
                        mime="application/pdf",
                        key=f"dl_sec_{s_pdf.stem}",
                        use_container_width=True,
                    )
        else:
            st.info("No sector reports found. Run batch sector report generator.")

    # =========================================================================
    # TAB 3: PORTFOLIO SUMMARY PDF
    # =========================================================================
    with tab_portfolio:
        st.markdown("#### 📁 Master Portfolio Summary Report")
        st.caption("Comprehensive 92-page PDF document featuring 1 page per constituent company in alphabetical order with Top 6 KPIs, YoY trend arrows (▲ improved, ▼ declined, ► flat), NLP insights, and capital allocation badges.")

        if PORTFOLIO_PDF.exists():
            p_bytes = PORTFOLIO_PDF.read_bytes()
            size_kb = len(p_bytes) / 1024
            st.success(f"✅ Portfolio Summary Report is ready! Total Pages: 92 | File Size: {size_kb:.1f} KB")
            st.download_button(
                label="⬇️ Download Full Portfolio Summary PDF (92 Pages)",
                data=p_bytes,
                file_name="portfolio_summary.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info("Portfolio summary report is compiling.")

    # =========================================================================
    # TAB 4: BSE FILINGS REPOSITORY
    # =========================================================================
    with tab_bse:
        selected_bse_str = st.selectbox(
            "Select Company for BSE Filings",
            options=options,
            index=0,
            key="sb_bse_comp",
        )
        selected_bse_cid = selected_bse_str.split(" - ")[0].strip()
        bse_cname = ticker_to_name.get(selected_bse_cid, selected_bse_cid)

        docs_df = get_documents(selected_bse_cid)
        st.markdown(f"#### 📚 Annual Reports for **{bse_cname}** ({selected_bse_cid})")
        st.caption(f"Showing all indexed regulatory annual reports and annual statutory filings ({len(docs_df)} years available).")

        if docs_df.empty:
            st.info("No annual reports currently catalogued for this company.")
        else:
            for _, row in docs_df.iterrows():
                yr = row.get("year")
                url = row.get("annual_report")
                is_valid_url = bool(url and isinstance(url, str) and url.startswith("http"))
                is_available = check_url_status(url) if is_valid_url else False

                col_year, col_desc, col_status, col_action = st.columns([1, 2.5, 1.5, 1.5])
                with col_year:
                    st.markdown(f"<div style='font-size: 1.1rem; font-weight: 700; color: #0f172a; padding: 0.5rem 0;'>FY{yr}</div>", unsafe_allow_html=True)
                with col_desc:
                    st.markdown(f"<div style='color: #475569; font-size: 0.95rem; padding: 0.5rem 0;'>Annual Financial Statement & Statutory Filing</div>", unsafe_allow_html=True)
                with col_status:
                    if is_available:
                        st.markdown(
                            "<span style='background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 600; font-size: 0.8rem;'>● Available (BSE)</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            "<span style='background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 600; font-size: 0.8rem;'>● Report unavailable</span>",
                            unsafe_allow_html=True
                        )
                with col_action:
                    if is_available:
                        st.markdown(
                            f'<a href="{url}" target="_blank" style="display: inline-block; background: #0284c7; color: white; padding: 0.35rem 0.75rem; border-radius: 6px; text-decoration: none; font-size: 0.825rem; font-weight: 600;">📥 View PDF</a>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.button("Unavailable", disabled=True, key=f"btn_unav_{selected_bse_cid}_{yr}", use_container_width=True)
                st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Nifty 100 Analytics - Intelligence Reports", page_icon="📑")
    render_reports_page()
