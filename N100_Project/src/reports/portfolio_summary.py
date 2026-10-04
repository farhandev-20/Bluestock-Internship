"""
Portfolio Summary PDF Generator for N100 Financial Intelligence Platform.
Generates a comprehensive multi-page PDF with 1 page per company in alphabetical order,
featuring Top 6 KPIs with YoY trend arrows (▲ improved, ▼ declined, ► flat), NLP insights,
and capital allocation profiles.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
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
PORTFOLIO_DIR = REPORTS_DIR / "portfolio"
DEFAULT_PORTFOLIO_PDF = PORTFOLIO_DIR / "portfolio_summary.pdf"


def get_trend_indicator(curr: Optional[float], prev: Optional[float], is_inverse: bool = False) -> Tuple[str, str]:
    """
    Computes trend direction:
      - '▲' with green if improved
      - '▼' with red if declined
      - '►' with gray if flat within 2%
    is_inverse=True applies to D/E where lower is better.
    """
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev):
        return ("-", "#64748B")
    
    if prev == 0:
        pct_change = 0.0 if curr == 0 else (100.0 if curr > 0 else -100.0)
    else:
        pct_change = ((curr - prev) / abs(prev)) * 100.0

    if abs(pct_change) <= 2.0:
        return ("► Flat", "#64748B")
    
    if is_inverse:
        # Lower is better (e.g. Debt/Equity)
        if curr < prev:
            return ("▲ Improved", "#10B981")
        else:
            return ("▼ Deteriorated", "#EF4444")
    else:
        # Higher is better
        if curr > prev:
            return ("▲ Improved", "#10B981")
        else:
            return ("▼ Declined", "#EF4444")


def build_portfolio_summary_page(
    company_id: str,
    comp_meta: Dict[str, Any],
    sec_meta: Dict[str, Any],
    pnl_df: pd.DataFrame,
    bs_df: pd.DataFrame,
    cf_df: pd.DataFrame,
    ratios_df: pd.DataFrame,
    mc_df: pd.DataFrame,
    pros_cons_list: List[Dict[str, Any]],
    cf_intel_row: Optional[Dict[str, Any]],
    page_num: int,
    total_pages: int,
    styles: Any,
) -> List[Any]:
    """
    Builds Flowables for a single company's 1-page profile in the portfolio summary.
    """
    elements: List[Any] = []

    comp_name = comp_meta.get("company_name", company_id)
    sector_name = sec_meta.get("broad_sector", "General")
    sub_sector = sec_meta.get("sub_sector", "")
    mcap_cat = sec_meta.get("market_cap_category", "Large Cap")

    # Sort historical tables
    p_sorted = pnl_df.dropna(subset=["year"]).sort_values("year")
    r_sorted = ratios_df.dropna(subset=["year"]).sort_values("year")
    cf_sorted = cf_df.dropna(subset=["year"]).sort_values("year")
    mc_sorted = mc_df.dropna(subset=["year"]).sort_values("year")

    # Latest and previous rows
    p_latest = p_sorted.iloc[-1] if not p_sorted.empty else {}
    p_prev = p_sorted.iloc[-2] if len(p_sorted) >= 2 else {}

    r_latest = r_sorted.iloc[-1] if not r_sorted.empty else {}
    r_prev = r_sorted.iloc[-2] if len(r_sorted) >= 2 else {}

    cf_latest = cf_sorted.iloc[-1] if not cf_sorted.empty else {}
    cf_prev = cf_sorted.iloc[-2] if len(cf_sorted) >= 2 else {}

    mc_latest = mc_sorted.iloc[-1] if not mc_sorted.empty else {}

    # 1. Company Header Banner
    style_h_title = ParagraphStyle(
        "PortHTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#FFFFFF"),
        leading=16,
    )
    style_h_sub = ParagraphStyle(
        "PortHSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#CBD5E1"),
        leading=10,
    )

    header_table = Table([
        [
            Paragraph(f"<b>{comp_name}</b> <font size=10 color='#93C5FD'>({company_id})</font>", style_h_title),
            Paragraph(f"<b>Sector:</b> {sector_name} | {sub_sector}<br/><b>Category:</b> {mcap_cat}", style_h_sub),
        ]
    ], colWidths=[350, 195])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B192C")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # 2. Top 6 KPIs with Trend Arrows
    # (1) Revenue, (2) Net Profit, (3) OPM, (4) ROE, (5) D/E, (6) Free Cash Flow
    curr_rev = p_latest.get("sales")
    prev_rev = p_prev.get("sales")
    rev_trend, rev_tcolor = get_trend_indicator(curr_rev, prev_rev)

    curr_pat = p_latest.get("net_profit")
    prev_pat = p_prev.get("net_profit")
    pat_trend, pat_tcolor = get_trend_indicator(curr_pat, prev_pat)

    curr_opm = r_latest.get("operating_profit_margin_pct")
    prev_opm = r_prev.get("operating_profit_margin_pct")
    opm_trend, opm_tcolor = get_trend_indicator(curr_opm, prev_opm)

    curr_roe = r_latest.get("return_on_equity_pct")
    prev_roe = r_prev.get("return_on_equity_pct")
    roe_trend, roe_tcolor = get_trend_indicator(curr_roe, prev_roe)

    curr_de = r_latest.get("debt_to_equity")
    prev_de = r_prev.get("debt_to_equity")
    de_trend, de_tcolor = get_trend_indicator(curr_de, prev_de, is_inverse=True)

    curr_fcf = r_latest.get("free_cash_flow_cr")
    prev_fcf = r_prev.get("free_cash_flow_cr")
    fcf_trend, fcf_tcolor = get_trend_indicator(curr_fcf, prev_fcf)

    style_card_lbl = ParagraphStyle("CardLbl", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7, textColor=colors.HexColor("#64748B"), alignment=1)
    style_card_val = ParagraphStyle("CardVal", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, textColor=colors.HexColor("#0F172A"), alignment=1)

    def make_kpi_card(label: str, val_str: str, trend_str: str, trend_color: str) -> Table:
        t_p = Paragraph(f"<font color='{trend_color}'><b>{trend_str}</b></font>", ParagraphStyle("Trend", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=6.5, alignment=1))
        t = Table([
            [Paragraph(label, style_card_lbl)],
            [Paragraph(val_str, style_card_val)],
            [t_p],
        ], colWidths=[175])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    rev_str = f"₹{curr_rev:,.0f} Cr" if curr_rev is not None and not pd.isna(curr_rev) else "N/A"
    pat_str = f"₹{curr_pat:,.0f} Cr" if curr_pat is not None and not pd.isna(curr_pat) else "N/A"
    opm_str = f"{curr_opm:.1f}%" if curr_opm is not None and not pd.isna(curr_opm) else "N/A"
    roe_str = f"{curr_roe:.1f}%" if curr_roe is not None and not pd.isna(curr_roe) else "N/A"
    de_str = f"{curr_de:.2f}x" if curr_de is not None and not pd.isna(curr_de) else "0.00x"
    fcf_str = f"₹{curr_fcf:,.0f} Cr" if curr_fcf is not None and not pd.isna(curr_fcf) else "N/A"

    kpi_grid = [
        [
            make_kpi_card("REVENUE (SALES)", rev_str, rev_trend, rev_tcolor),
            make_kpi_card("NET PROFIT (PAT)", pat_str, pat_trend, pat_tcolor),
            make_kpi_card("OPERATING MARGIN (OPM)", opm_str, opm_trend, opm_tcolor),
        ],
        [
            make_kpi_card("RETURN ON EQUITY (ROE)", roe_str, roe_trend, roe_tcolor),
            make_kpi_card("DEBT TO EQUITY (D/E)", de_str, de_trend, de_tcolor),
            make_kpi_card("FREE CASH FLOW (FCF)", fcf_str, fcf_trend, fcf_tcolor),
        ],
    ]

    cards_table = Table(kpi_grid, colWidths=[180, 180, 180])
    cards_table.setStyle(TableStyle([
        ("PADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(cards_table)
    elements.append(Spacer(1, 10))

    # 3. Historical 5-Year Trend Table
    style_tbl_th = ParagraphStyle("TblTH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=6.5, textColor=colors.HexColor("#FFFFFF"), alignment=1)
    style_tbl_td = ParagraphStyle("TblTD", parent=styles["Normal"], fontName="Helvetica", fontSize=6.5, textColor=colors.HexColor("#334155"), alignment=1)
    style_tbl_td_bold = ParagraphStyle("TblTDBold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=6.5, textColor=colors.HexColor("#0F172A"), alignment=0)

    p_5yr = p_sorted.tail(5)
    r_5yr = r_sorted.tail(5)

    th_row = [Paragraph("Metric (₹ Cr / %)", style_tbl_th)]
    for y in p_5yr["year"]:
        th_row.append(Paragraph(f"FY{int(y)}", style_tbl_th))

    table_rows = [th_row]

    # Row 1: Sales
    sales_r = [Paragraph("Sales Revenue", style_tbl_td_bold)]
    for v in p_5yr["sales"]:
        sales_r.append(Paragraph(f"{v:,.0f}" if pd.notna(v) else "-", style_tbl_td))
    table_rows.append(sales_r)

    # Row 2: Net Profit
    pat_r = [Paragraph("Net Profit (PAT)", style_tbl_td_bold)]
    for v in p_5yr["net_profit"]:
        pat_r.append(Paragraph(f"{v:,.0f}" if pd.notna(v) else "-", style_tbl_td))
    table_rows.append(pat_r)

    # Row 3: ROE %
    roe_r = [Paragraph("Return on Equity (ROE %)", style_tbl_td_bold)]
    for v in r_5yr["return_on_equity_pct"]:
        roe_r.append(Paragraph(f"{v:.1f}%" if pd.notna(v) else "-", style_tbl_td))
    table_rows.append(roe_r)

    # Row 4: D/E
    de_r = [Paragraph("Debt-to-Equity (D/E)", style_tbl_td_bold)]
    for v in r_5yr["debt_to_equity"]:
        de_r.append(Paragraph(f"{v:.2f}x" if pd.notna(v) else "-", style_tbl_td))
    table_rows.append(de_r)

    num_cols = len(th_row)
    c_width_first = 145
    c_width_others = (545 - c_width_first) / (num_cols - 1)
    col_w_list = [c_width_first] + [c_width_others] * (num_cols - 1)

    t_hist = Table(table_rows, colWidths=col_w_list)
    t_hist.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(Paragraph("<b>5-Year Financial Performance Trend</b>", ParagraphStyle("H5", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#0F172A"), spaceAfter=3)))
    elements.append(t_hist)
    elements.append(Spacer(1, 10))

    # 4. Capital Allocation & Cash Flow Intelligence
    cap_alloc_label = (cf_intel_row or {}).get("capital_allocation", "Reinvestor")
    cfo_q_label = (cf_intel_row or {}).get("cfo_quality_label", "High Quality")
    capex_lab = (cf_intel_row or {}).get("capex_label", "Moderate")

    badge_col = "#10B981" if cap_alloc_label in ["Reinvestor", "Shareholder Returns"] else ("#EF4444" if cap_alloc_label == "Distress Signal" else "#3B82F6")
    intel_badge_table = Table([
        [
            Paragraph(f"<b>CAPITAL ALLOCATION: {cap_alloc_label.upper()}</b>", ParagraphStyle("BadgeB", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, textColor=colors.HexColor("#FFFFFF"), alignment=1)),
            Paragraph(f"<b>CFO Quality:</b> {cfo_q_label} | <b>CapEx Intensity:</b> {capex_lab}", ParagraphStyle("IntelSubP", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#334155"), alignment=2)),
        ]
    ], colWidths=[240, 305])
    intel_badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(badge_col)),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F1F5F9")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(intel_badge_table)
    elements.append(Spacer(1, 10))

    # 5. NLP Pros & Cons Insights
    pros = [p for p in pros_cons_list if p.get("type") == "pro"][:2]
    cons = [c for c in pros_cons_list if c.get("type") == "con"][:2]

    style_pro_p = ParagraphStyle("ProP", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=colors.HexColor("#065F46"), leading=9)
    style_con_p = ParagraphStyle("ConP", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=colors.HexColor("#991B1B"), leading=9)

    pro_rows = [[Paragraph("<font color='#059669'><b>▲ Key Strengths (Pros)</b></font>", ParagraphStyle("HP", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5))]]
    for p in pros:
        pro_rows.append([Paragraph(f"● {p.get('text', '')} <i>({p.get('confidence_pct', 80):.0f}%)</i>", style_pro_p)])

    con_rows = [[Paragraph("<font color='#DC2626'><b>▼ Key Risks (Cons)</b></font>", ParagraphStyle("HC", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5))]]
    for c in cons:
        con_rows.append([Paragraph(f"● {c.get('text', '')} <i>({c.get('confidence_pct', 80):.0f}%)</i>", style_con_p)])

    t_pros = Table(pro_rows, colWidths=[265])
    t_pros.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#A7F3D0")),
        ("PADDING", (0, 0), (-1, -1), 3),
    ]))

    t_cons = Table(con_rows, colWidths=[265])
    t_cons.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FECACA")),
        ("PADDING", (0, 0), (-1, -1), 3),
    ]))

    nlp_row = Table([[t_pros, t_cons]], colWidths=[272, 273])
    nlp_row.setStyle(TableStyle([
        ("PADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(nlp_row)

    # 6. Page Footer
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<font size=6.5 color='#94A3B8'>Nifty 100 Portfolio Summary | {comp_name} ({company_id}) | Page {page_num} of {total_pages}</font>", ParagraphStyle("FootP", parent=styles["Normal"], fontSize=6.5, textColor=colors.HexColor("#94A3B8"), alignment=1)))

    return elements


def generate_portfolio_summary_pdf(
    db_path: Optional[Path] = None,
    output_pdf_path: Optional[Path] = None,
) -> Path:
    """
    Generates single multi-page PDF (reports/portfolio/portfolio_summary.pdf)
    containing 1 page per company in alphabetical order.
    """
    target_db = Path(db_path or DEFAULT_DB_PATH)
    target_pdf = Path(output_pdf_path or DEFAULT_PORTFOLIO_PDF)
    target_pdf.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_db))
    sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    companies_df = pd.read_sql_query("SELECT * FROM companies", conn)
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    mc_df = pd.read_sql_query("SELECT * FROM market_cap", conn)
    conn.close()

    # Load pros/cons & cashflow intelligence
    pros_cons_path = OUTPUT_DIR / "pros_cons_generated.csv"
    pros_cons_df = pd.read_csv(pros_cons_path) if pros_cons_path.exists() else pd.DataFrame()

    intel_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    intel_df = pd.read_excel(intel_path, sheet_name="CashFlow_Intelligence") if intel_path.exists() else pd.DataFrame()

    # Sort companies alphabetically by company_id
    sorted_companies = sorted(sectors_df["company_id"].unique().tolist())
    total_companies = len(sorted_companies)

    doc = SimpleDocTemplate(
        str(target_pdf),
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()
    all_flowables: List[Any] = []

    for idx, cid in enumerate(sorted_companies, start=1):
        c_meta = companies_df[companies_df["id"] == cid]
        s_meta = sectors_df[sectors_df["company_id"] == cid]
        c_pnl = pnl_df[pnl_df["company_id"] == cid]
        c_bs = bs_df[bs_df["company_id"] == cid]
        c_cf = cf_df[cf_df["company_id"] == cid]
        c_ratios = ratios_df[ratios_df["company_id"] == cid]
        c_mc = mc_df[mc_df["company_id"] == cid]

        comp_dict = c_meta.iloc[0].to_dict() if not c_meta.empty else {"id": cid}
        sec_dict = s_meta.iloc[0].to_dict() if not s_meta.empty else {}

        # Pros and Cons
        p_c_list = pros_cons_df[pros_cons_df["company_id"] == cid].to_dict("records") if not pros_cons_df.empty else []

        # Intel row
        intel_row = intel_df[intel_df["company_id"] == cid].iloc[0].to_dict() if not intel_df.empty and not intel_df[intel_df["company_id"] == cid].empty else None

        page_elements = build_portfolio_summary_page(
            company_id=cid,
            comp_meta=comp_dict,
            sec_meta=sec_dict,
            pnl_df=c_pnl,
            bs_df=c_bs,
            cf_df=c_cf,
            ratios_df=c_ratios,
            mc_df=c_mc,
            pros_cons_list=p_c_list,
            cf_intel_row=intel_row,
            page_num=idx,
            total_pages=total_companies,
            styles=styles,
        )

        all_flowables.extend(page_elements)
        if idx < total_companies:
            all_flowables.append(PageBreak())

    doc.build(all_flowables)
    return target_pdf


if __name__ == "__main__":
    print("Executing Portfolio Summary PDF Generation...")
    out = generate_portfolio_summary_pdf()
    print(f"Portfolio summary PDF generated successfully -> {out}")
