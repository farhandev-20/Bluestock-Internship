"""
2-Page Company Tearsheet PDF Generator for N100 Financial Intelligence Platform.
Uses ReportLab and Matplotlib to render institutional-grade company factsheets.
"""

import io
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"
TEARSHEET_DIR = REPORTS_DIR / "tearsheets"
DEFAULT_SKIPPED_CSV = OUTPUT_DIR / "skipped_tearsheets.csv"


# ==============================================================================
# Matplotlib Chart Generation Helpers
# ==============================================================================

def generate_revenue_profit_chart(pnl_df: pd.DataFrame) -> io.BytesIO:
    """Generates 10-year Revenue & Net Profit dual bar chart."""
    df = pnl_df.dropna(subset=["year"]).copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year").tail(10)

    fig, ax = plt.subplots(figsize=(6.2, 2.2), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    years = [str(int(y)) for y in df["year"]]
    x = np.arange(len(years))
    width = 0.38

    sales = df["sales"].fillna(0).tolist()
    pat = df["net_profit"].fillna(0).tolist()

    rects1 = ax.bar(x - width/2, sales, width, label="Revenue (Sales)", color="#1E88E5", edgecolor="none", alpha=0.9)
    rects2 = ax.bar(x + width/2, pat, width, label="Net Profit (PAT)", color="#10B981", edgecolor="none", alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=7.5, color="#334155", fontweight="bold")
    ax.set_ylabel("₹ in Crores", fontsize=7.5, color="#475569")
    ax.set_title("10-Year Revenue & Net Profit Track Record", fontsize=8.5, fontweight="bold", color="#0F172A", pad=6)
    ax.legend(loc="upper left", fontsize=7, framealpha=0.8, edgecolor="#CBD5E1")
    ax.grid(axis="y", linestyle="--", alpha=0.4, color="#CBD5E1")
    ax.tick_params(axis="both", labelsize=7, colors="#475569")

    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")

    plt.tight_layout(pad=0.5)
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", dpi=160)
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_roe_roce_chart(ratios_df: pd.DataFrame, pnl_df: pd.DataFrame) -> io.BytesIO:
    """Generates 10-year ROE & OPM line chart."""
    df_r = ratios_df.dropna(subset=["year"]).copy()
    df_r["year"] = pd.to_numeric(df_r["year"], errors="coerce")
    df_r = df_r.dropna(subset=["year"])
    df_r["year"] = df_r["year"].astype(int)
    df_r = df_r.sort_values("year").tail(10)

    fig, ax = plt.subplots(figsize=(6.2, 2.2), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    years = [str(int(y)) for y in df_r["year"]]
    x = np.arange(len(years))

    roe = df_r["return_on_equity_pct"].fillna(0).tolist() if "return_on_equity_pct" in df_r.columns else [0]*len(x)
    opm = df_r["operating_profit_margin_pct"].fillna(0).tolist() if "operating_profit_margin_pct" in df_r.columns else [0]*len(x)

    ax.plot(x, roe, marker="o", color="#E11D48", linewidth=1.8, markersize=4, label="ROE (%)", alpha=0.9)
    ax.plot(x, opm, marker="s", color="#3B82F6", linewidth=1.8, markersize=4, label="OPM (%)", alpha=0.9)
    ax.axhline(15.0, color="#10B981", linestyle=":", linewidth=1.2, label="Benchmark (15%)")

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=7.5, color="#334155", fontweight="bold")
    ax.set_ylabel("Percentage (%)", fontsize=7.5, color="#475569")
    ax.set_title("Return on Equity (ROE) & Operating Margin (OPM) Trend", fontsize=8.5, fontweight="bold", color="#0F172A", pad=6)
    ax.legend(loc="upper right", fontsize=7, framealpha=0.8, edgecolor="#CBD5E1")
    ax.grid(axis="both", linestyle="--", alpha=0.4, color="#CBD5E1")
    ax.tick_params(axis="both", labelsize=7, colors="#475569")

    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")

    plt.tight_layout(pad=0.5)
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", dpi=160)
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_balance_sheet_chart(bs_df: pd.DataFrame) -> io.BytesIO:
    """Generates stacked bar chart of Balance Sheet composition."""
    df = bs_df.dropna(subset=["year"]).copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year").tail(8)

    fig, ax = plt.subplots(figsize=(3.0, 2.0), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    years = [str(int(y)) for y in df["year"]]
    x = np.arange(len(years))
    width = 0.55

    eq = (df["equity_capital"].fillna(0) + df["reserves"].fillna(0)).tolist()
    borrowings = df["borrowings"].fillna(0).tolist()
    other_liab = df["other_liabilities"].fillna(0).tolist()

    ax.bar(x, eq, width, label="Equity & Reserves", color="#10B981", alpha=0.9)
    ax.bar(x, borrowings, width, bottom=eq, label="Borrowings (Debt)", color="#F59E0B", alpha=0.9)
    bottom_2 = [e + b for e, b in zip(eq, borrowings)]
    ax.bar(x, other_liab, width, bottom=bottom_2, label="Other Liab.", color="#94A3B8", alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=6.5, rotation=35, color="#334155")
    ax.set_ylabel("₹ Cr", fontsize=6.5, color="#475569")
    ax.set_title("Balance Sheet Composition", fontsize=7.5, fontweight="bold", color="#0F172A", pad=4)
    ax.legend(loc="upper left", fontsize=5.5, framealpha=0.7, edgecolor="#CBD5E1")
    ax.grid(axis="y", linestyle="--", alpha=0.4, color="#CBD5E1")
    ax.tick_params(axis="both", labelsize=6, colors="#475569")

    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")

    plt.tight_layout(pad=0.3)
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", dpi=160)
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_cashflow_waterfall_chart(cf_df: pd.DataFrame) -> io.BytesIO:
    """Generates Cash Flow components bar chart for latest year."""
    df = cf_df.dropna(subset=["year"]).copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year")
    latest_cf = df.iloc[-1] if not df.empty else None

    cfo = latest_cf.get("operating_activity", 0.0) or 0.0 if latest_cf is not None else 0.0
    cfi = latest_cf.get("investing_activity", 0.0) or 0.0 if latest_cf is not None else 0.0
    cff = latest_cf.get("financing_activity", 0.0) or 0.0 if latest_cf is not None else 0.0
    ncf = latest_cf.get("net_cash_flow", 0.0) or (cfo + cfi + cff) if latest_cf is not None else 0.0

    fig, ax = plt.subplots(figsize=(3.0, 2.0), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    categories = ["CFO", "CFI", "CFF", "Net CF"]
    values = [cfo, cfi, cff, ncf]
    colors_list = ["#10B981" if v >= 0 else "#EF4444" for v in values]

    bars = ax.bar(categories, values, width=0.5, color=colors_list, alpha=0.9)
    ax.axhline(0, color="#64748B", linewidth=0.8)
    ax.set_ylabel("₹ Cr", fontsize=6.5, color="#475569")
    yr_label = int(latest_cf["year"]) if latest_cf is not None else 2024
    ax.set_title(f"Cash Flow Breakdown (FY{yr_label})", fontsize=7.5, fontweight="bold", color="#0F172A", pad=4)
    ax.grid(axis="y", linestyle="--", alpha=0.4, color="#CBD5E1")
    ax.tick_params(axis="both", labelsize=6.5, colors="#475569")

    # Add text labels on top/bottom of bars
    for bar in bars:
        h = bar.get_height()
        va = "bottom" if h >= 0 else "top"
        ax.annotate(f"{h:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 2 if h >= 0 else -4),
                    textcoords="offset points",
                    ha="center", va=va, fontsize=5.5, color="#1E293B", fontweight="bold")

    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")

    plt.tight_layout(pad=0.3)
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", dpi=160)
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


# ==============================================================================
# PDF Builder Class
# ==============================================================================

def create_company_tearsheet(
    company_id: str,
    output_pdf_path: Path,
    db_path: Optional[Path] = None,
    pros_cons_df: Optional[pd.DataFrame] = None,
    cf_intel_df: Optional[pd.DataFrame] = None,
) -> bool:
    """
    Builds exactly 2-page tearsheet PDF for a given company.
    Returns True if successfully generated, False if skipped (<3 years data).
    """
    target_db = Path(db_path or DEFAULT_DB_PATH)
    conn = sqlite3.connect(str(target_db))
    
    comp_df = pd.read_sql_query(f"SELECT * FROM companies WHERE id = '{company_id}'", conn)
    sec_df = pd.read_sql_query(f"SELECT * FROM sectors WHERE company_id = '{company_id}'", conn)
    mc_df = pd.read_sql_query(f"SELECT * FROM market_cap WHERE company_id = '{company_id}'", conn)
    pnl_df = pd.read_sql_query(f"SELECT * FROM profitandloss WHERE company_id = '{company_id}'", conn)
    bs_df = pd.read_sql_query(f"SELECT * FROM balancesheet WHERE company_id = '{company_id}'", conn)
    cf_df = pd.read_sql_query(f"SELECT * FROM cashflow WHERE company_id = '{company_id}'", conn)
    ratios_df = pd.read_sql_query(f"SELECT * FROM financial_ratios WHERE company_id = '{company_id}'", conn)
    conn.close()

    if len(pnl_df) < 1 or len(ratios_df) < 1:
        return False

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # Base Metadata
    comp_name = comp_df.iloc[0].get("company_name", company_id) if not comp_df.empty else company_id
    sector_name = sec_df.iloc[0].get("broad_sector", "General") if not sec_df.empty else "General"
    sub_sector = sec_df.iloc[0].get("sub_sector", "") if not sec_df.empty else ""
    mcap_cat = sec_df.iloc[0].get("market_cap_category", "Large Cap") if not sec_df.empty else "Large Cap"

    # Latest year rows
    p_sorted = pnl_df.sort_values("year")
    r_sorted = ratios_df.sort_values("year")
    mc_sorted = mc_df.sort_values("year")

    r_latest = r_sorted.iloc[-1] if not r_sorted.empty else {}
    m_latest = mc_sorted.iloc[-1] if not mc_sorted.empty else {}

    # Key metrics for 6 KPI tiles
    mcap_val = m_latest.get("market_cap_crore", 0.0) or 0.0
    pe_val = m_latest.get("pe_ratio")
    roe_val = r_latest.get("return_on_equity_pct")
    roce_val = comp_df.iloc[0].get("roce_percentage") if not comp_df.empty else None
    if roce_val is None or pd.isna(roce_val):
        roce_val = roe_val
    de_val = r_latest.get("debt_to_equity")
    rev_cagr_val = r_latest.get("revenue_cagr_5yr")

    # Format KPI strings
    mcap_str = f"₹{mcap_val:,.0f} Cr" if mcap_val > 0 else "N/A"
    pe_str = f"{pe_val:.1f}x" if pe_val is not None and not pd.isna(pe_val) else "N/A"
    roe_str = f"{roe_val:.1f}%" if roe_val is not None and not pd.isna(roe_val) else "N/A"
    roce_str = f"{roce_val:.1f}%" if roce_val is not None and not pd.isna(roce_val) else "N/A"
    de_str = f"{de_val:.2f}x" if de_val is not None and not pd.isna(de_val) else "0.00x"
    cagr_str = f"{rev_cagr_val:.1f}%" if rev_cagr_val is not None and not pd.isna(rev_cagr_val) else "N/A"

    # Setup ReportLab Styles
    styles = getSampleStyleSheet()
    
    style_header_title = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=colors.HexColor("#FFFFFF"),
        leading=18,
    )
    style_header_sub = ParagraphStyle(
        "HeaderSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        textColor=colors.HexColor("#CBD5E1"),
        leading=11,
    )
    style_sec_header = ParagraphStyle(
        "SecHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#0F172A"),
        leading=13,
        spaceAfter=4,
    )
    style_tile_label = ParagraphStyle(
        "TileLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        textColor=colors.HexColor("#64748B"),
        alignment=1,  # Center
        leading=9,
    )
    style_tile_val = ParagraphStyle(
        "TileVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,  # Center
        leading=14,
    )
    style_body = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        textColor=colors.HexColor("#334155"),
        leading=10,
    )
    style_pro_bullet = ParagraphStyle(
        "ProBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        textColor=colors.HexColor("#065F46"),
        leading=10,
    )
    style_con_bullet = ParagraphStyle(
        "ConBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        textColor=colors.HexColor("#991B1B"),
        leading=10,
    )
    style_badge = ParagraphStyle(
        "BadgeText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1,
        leading=10,
    )

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=20,
    )
    elements = []

    # ==========================================================================
    # PAGE 1
    # ==========================================================================

    # 1. Header Banner
    header_data = [
        [
            Paragraph(f"<b>{comp_name}</b> <font size=11 color='#93C5FD'>({company_id})</font>", style_header_title),
            Paragraph(f"<b>Sector:</b> {sector_name} | {sub_sector}<br/><b>Category:</b> {mcap_cat} | <b>Exchange:</b> NSE / BSE", style_header_sub),
        ]
    ]
    header_table = Table(header_data, colWidths=[330, 215])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B192C")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))

    # 2. 6 KPI Tiles in 2 rows of 3
    kpi_tiles = [
        [
            [Paragraph("MARKET CAP", style_tile_label), Paragraph(mcap_str, style_tile_val)],
            [Paragraph("P/E RATIO", style_tile_label), Paragraph(pe_str, style_tile_val)],
            [Paragraph("RETURN ON EQUITY (ROE)", style_tile_label), Paragraph(roe_str, style_tile_val)],
        ],
        [
            [Paragraph("ROCE (%)", style_tile_label), Paragraph(roce_str, style_tile_val)],
            [Paragraph("DEBT TO EQUITY (D/E)", style_tile_label), Paragraph(de_str, style_tile_val)],
            [Paragraph("5-YR REVENUE CAGR", style_tile_label), Paragraph(cagr_str, style_tile_val)],
        ],
    ]

    # Convert inner cells to nested mini tables
    tile_table_data = []
    for row in kpi_tiles:
        row_cells = []
        for cell in row:
            mini_t = Table([[cell[0]], [cell[1]]], colWidths=[175])
            mini_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            row_cells.append(mini_t)
        tile_table_data.append(row_cells)

    tiles_table = Table(tile_table_data, colWidths=[180, 180, 180])
    tiles_table.setStyle(TableStyle([
        ("PADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(tiles_table)
    elements.append(Spacer(1, 10))

    # 3. Chart 1: 10-Year Revenue & PAT Bar Chart
    rev_buf = generate_revenue_profit_chart(pnl_df)
    img_rev = Image(rev_buf, width=540, height=195)
    elements.append(img_rev)
    elements.append(Spacer(1, 8))

    # 4. Chart 2: 10-Year ROE & OPM Line Chart
    roe_buf = generate_roe_roce_chart(ratios_df, pnl_df)
    img_roe = Image(roe_buf, width=540, height=195)
    elements.append(img_roe)

    # Page 1 Footer Note
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<font size=6.5 color='#94A3B8'>Nifty 100 Financial Intelligence Platform | Tearsheet Report | Page 1 of 2</font>", style_body))

    # Force PageBreak to start Page 2
    elements.append(PageBreak())

    # ==========================================================================
    # PAGE 2
    # ==========================================================================

    # 1. Page 2 Header Banner
    header2_data = [
        [
            Paragraph(f"<b>{comp_name}</b> <font size=10 color='#93C5FD'>({company_id})</font> — Capital Structure & NLP Intelligence", style_header_title),
            Paragraph("Institutional Tearsheet", style_header_sub),
        ]
    ]
    header2_table = Table(header2_data, colWidths=[400, 145])
    header2_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1E293B")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(header2_table)
    elements.append(Spacer(1, 8))

    # 2. Charts Row: Stacked Balance Sheet (left) + Cash Flow Waterfall (right)
    bs_buf = generate_balance_sheet_chart(bs_df)
    cf_buf = generate_cashflow_waterfall_chart(cf_df)
    img_bs = Image(bs_buf, width=265, height=175)
    img_cf = Image(cf_buf, width=265, height=175)

    charts_row = Table([[img_bs, img_cf]], colWidths=[270, 270])
    charts_row.setStyle(TableStyle([
        ("PADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(charts_row)
    elements.append(Spacer(1, 8))

    # 3. Capital Allocation Badge & Cash Flow Intelligence
    cap_alloc_label = "Reinvestor"
    cfo_q_label = "High Quality"
    capex_lab = "Moderate"
    if cf_intel_df is not None and not cf_intel_df.empty:
        c_intel = cf_intel_df[cf_intel_df["company_id"] == company_id]
        if not c_intel.empty:
            cap_alloc_label = c_intel.iloc[0].get("capital_allocation", "Reinvestor")
            cfo_q_label = c_intel.iloc[0].get("cfo_quality_label", "High Quality")
            capex_lab = c_intel.iloc[0].get("capex_label", "Moderate")

    badge_color = "#10B981" if cap_alloc_label in ["Reinvestor", "Shareholder Returns"] else ("#EF4444" if cap_alloc_label == "Distress Signal" else "#3B82F6")
    badge_table = Table([
        [
            Paragraph(f"<b>CAPITAL ALLOCATION: {cap_alloc_label.upper()}</b>", style_badge),
            Paragraph(f"<b>CFO Quality:</b> {cfo_q_label} | <b>CapEx Intensity:</b> {capex_lab}", ParagraphStyle("IntelSub", parent=styles["Normal"], fontSize=7.5, textColor=colors.HexColor("#334155"), alignment=2)),
        ]
    ], colWidths=[260, 280])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(badge_color)),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F1F5F9")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(badge_table)
    elements.append(Spacer(1, 8))

    # 4. Pros & Cons Sections (NLP Intelligence)
    comp_pros = []
    comp_cons = []
    if pros_cons_df is not None and not pros_cons_df.empty:
        p_c = pros_cons_df[pros_cons_df["company_id"] == company_id]
        comp_pros = p_c[p_c["type"] == "pro"].to_dict("records")
        comp_cons = p_c[p_c["type"] == "con"].to_dict("records")

    # Limit to top 3 pros and top 3 cons to ensure zero overflow
    comp_pros = comp_pros[:3]
    comp_cons = comp_cons[:3]

    # Pros Box
    pros_rows = [[Paragraph("<font color='#059669'><b>▲ Key Fundamental Strengths (Pros)</b></font>", style_sec_header)]]
    for p in comp_pros:
        text_p = p.get("text", "")
        conf = p.get("confidence_pct", 85.0)
        p_p = Paragraph(f"● <b>{text_p}</b> <font color='#059669'><i>(Confidence: {conf:.0f}%)</i></font>", style_pro_bullet)
        pros_rows.append([p_p])
    
    pros_table = Table(pros_rows, colWidths=[540])
    pros_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#A7F3D0")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (0, 0), 4),
    ]))
    elements.append(pros_table)
    elements.append(Spacer(1, 6))

    # Cons Box
    cons_rows = [[Paragraph("<font color='#DC2626'><b>▼ Key Risks & Monitoring Flags (Cons)</b></font>", style_sec_header)]]
    for c in comp_cons:
        text_c = c.get("text", "")
        conf = c.get("confidence_pct", 85.0)
        p_c_flow = Paragraph(f"● <b>{text_c}</b> <font color='#DC2626'><i>(Confidence: {conf:.0f}%)</i></font>", style_con_bullet)
        cons_rows.append([p_c_flow])
    
    cons_table = Table(cons_rows, colWidths=[540])
    cons_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FECACA")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (0, 0), 4),
    ]))
    elements.append(cons_table)

    # Page 2 Footer
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<font size=6.5 color='#94A3B8'>Nifty 100 Financial Intelligence Platform | Tearsheet Report | Page 2 of 2</font>", style_body))

    # Build Document
    doc.build(elements)
    return True


# ==============================================================================
# Batch Tearsheet Generation
# ==============================================================================

def generate_all_tearsheets(
    db_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    skipped_csv_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Generates 2-page tearsheet PDFs for all 92 Nifty 100 companies.
    Skips companies with <3 years data and logs to output/skipped_tearsheets.csv.
    """
    target_db = Path(db_path or DEFAULT_DB_PATH)
    target_dir = Path(output_dir or TEARSHEET_DIR)
    target_skipped_csv = Path(skipped_csv_path or DEFAULT_SKIPPED_CSV)

    target_dir.mkdir(parents=True, exist_ok=True)
    target_skipped_csv.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_db))
    sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()

    # Load pros/cons & cashflow intelligence
    pros_cons_path = OUTPUT_DIR / "pros_cons_generated.csv"
    pros_cons_df = pd.read_csv(pros_cons_path) if pros_cons_path.exists() else None

    intel_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    intel_df = pd.read_excel(intel_path, sheet_name="CashFlow_Intelligence") if intel_path.exists() else None

    companies_list = sectors_df["company_id"].tolist()
    success_count = 0
    skipped_records = []

    for cid in companies_list:
        pdf_file = target_dir / f"{cid}_tearsheet.pdf"
        ok = create_company_tearsheet(
            company_id=cid,
            output_pdf_path=pdf_file,
            db_path=target_db,
            pros_cons_df=pros_cons_df,
            cf_intel_df=intel_df,
        )
        if ok:
            success_count += 1
            # Check if company had fewer than 3 full years of ratios/statements
            conn_temp = sqlite3.connect(str(target_db))
            c_r = pd.read_sql_query(f"SELECT COUNT(*) FROM financial_ratios WHERE company_id = '{cid}'", conn_temp).iloc[0, 0]
            conn_temp.close()
            if c_r < 3:
                skipped_records.append({
                    "company_id": cid,
                    "reason": f"Fewer than 3 years of financial data ({c_r} years found)",
                })
        else:
            skipped_records.append({
                "company_id": cid,
                "reason": "No financial statement data available",
            })

    skipped_df = pd.DataFrame(skipped_records)
    skipped_df.to_csv(target_skipped_csv, index=False)

    return {
        "total_targets": len(companies_list),
        "total_generated": success_count,
        "total_skipped": len(skipped_records),
        "output_dir": str(target_dir),
    }


if __name__ == "__main__":
    print("Executing Batch Company Tearsheet Generation...")
    summary = generate_all_tearsheets()
    print(f"Batch generation completed: {summary['total_generated']} generated, {summary['total_skipped']} skipped.")
