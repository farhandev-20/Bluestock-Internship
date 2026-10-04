"""
Sector PDF Report Generator for N100 Financial Intelligence Platform.
Generates institutional sector benchmark reports with median KPIs and constituent comparison tables.
"""

from pathlib import Path
import re
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
REPORTS_DIR = PROJECT_ROOT / "reports"
SECTOR_REPORTS_DIR = REPORTS_DIR / "sector"


def sanitize_filename(name: str) -> str:
    """Converts sector name into a clean filename slug."""
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.strip())
    return re.sub(r'_+', '_', clean).strip('_')


def generate_single_sector_report(
    sector_name: str,
    sector_df: pd.DataFrame,
    companies_df: pd.DataFrame,
    ratios_df: pd.DataFrame,
    mc_df: pd.DataFrame,
    output_pdf_path: Path,
) -> bool:
    """
    Generates a single Sector Report PDF with median KPIs and 8-metric constituent table.
    """
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter constituents
    cids = sector_df["company_id"].unique().tolist()
    if not cids:
        return False

    # Aggregate constituent metrics for latest available year
    rows = []
    for cid in cids:
        c_meta = companies_df[companies_df["id"] == cid]
        c_ratios = ratios_df[ratios_df["company_id"] == cid].dropna(subset=["year"]).sort_values("year")
        c_mc = mc_df[mc_df["company_id"] == cid].dropna(subset=["year"]).sort_values("year")
        c_sec = sector_df[sector_df["company_id"] == cid]

        c_name = c_meta.iloc[0].get("company_name", cid) if not c_meta.empty else cid
        sub_sec = c_sec.iloc[0].get("sub_sector", "") if not c_sec.empty else ""

        r_latest = c_ratios.iloc[-1] if not c_ratios.empty else {}
        m_latest = c_mc.iloc[-1] if not c_mc.empty else {}

        mcap = m_latest.get("market_cap_crore", 0.0) or 0.0
        pe = m_latest.get("pe_ratio")
        roe = r_latest.get("return_on_equity_pct")
        roce = c_meta.iloc[0].get("roce_percentage") if not c_meta.empty else None
        if roce is None or pd.isna(roce):
            roce = roe
        de = r_latest.get("debt_to_equity")
        cagr = r_latest.get("revenue_cagr_5yr")

        rows.append({
            "company_id": cid,
            "company_name": c_name,
            "sub_sector": sub_sec,
            "market_cap": mcap,
            "pe_ratio": pe if pe is not None and not pd.isna(pe) else np.nan,
            "roe": roe if roe is not None and not pd.isna(roe) else np.nan,
            "roce": roce if roce is not None and not pd.isna(roce) else np.nan,
            "debt_to_equity": de if de is not None and not pd.isna(de) else np.nan,
            "revenue_cagr": cagr if cagr is not None and not pd.isna(cagr) else np.nan,
        })

    df_const = pd.DataFrame(rows)
    if df_const.empty:
        return False

    # Compute Median KPIs
    med_mcap = df_const["market_cap"].median()
    med_pe = df_const["pe_ratio"].dropna().median()
    med_roe = df_const["roe"].dropna().median()
    med_roce = df_const["roce"].dropna().median()
    med_de = df_const["debt_to_equity"].dropna().median()
    med_cagr = df_const["revenue_cagr"].dropna().median()
    total_mcap = df_const["market_cap"].sum()

    # Styles
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "SecTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=colors.HexColor("#FFFFFF"),
        leading=18,
    )
    style_sub = ParagraphStyle(
        "SecSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        textColor=colors.HexColor("#CBD5E1"),
        leading=11,
    )
    style_tile_lbl = ParagraphStyle(
        "TileLbl",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
        leading=9,
    )
    style_tile_val = ParagraphStyle(
        "TileVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        leading=14,
    )
    style_th = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1,
        leading=9,
    )
    style_td = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        textColor=colors.HexColor("#334155"),
        alignment=0,
        leading=9,
    )
    style_td_num = ParagraphStyle(
        "TDNum",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        textColor=colors.HexColor("#0F172A"),
        alignment=2,  # Right align
        leading=9,
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

    # 1. Header Banner
    banner_data = [
        [
            Paragraph(f"<b>SECTOR REPORT: {sector_name.upper()}</b>", style_title),
            Paragraph(f"<b>Constituents:</b> {len(df_const)} Companies<br/><b>Total MCap:</b> ₹{total_mcap:,.0f} Cr", style_sub),
        ]
    ]
    banner_table = Table(banner_data, colWidths=[360, 185])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B192C")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 10))

    # 2. Sector Median KPIs Grid (2 rows of 3)
    kpis = [
        [
            [Paragraph("MEDIAN MARKET CAP", style_tile_lbl), Paragraph(f"₹{med_mcap:,.0f} Cr" if not np.isnan(med_mcap) else "N/A", style_tile_val)],
            [Paragraph("MEDIAN P/E RATIO", style_tile_lbl), Paragraph(f"{med_pe:.1f}x" if not np.isnan(med_pe) else "N/A", style_tile_val)],
            [Paragraph("MEDIAN ROE (%)", style_tile_lbl), Paragraph(f"{med_roe:.1f}%" if not np.isnan(med_roe) else "N/A", style_tile_val)],
        ],
        [
            [Paragraph("MEDIAN ROCE (%)", style_tile_lbl), Paragraph(f"{med_roce:.1f}%" if not np.isnan(med_roce) else "N/A", style_tile_val)],
            [Paragraph("MEDIAN D/E RATIO", style_tile_lbl), Paragraph(f"{med_de:.2f}x" if not np.isnan(med_de) else "N/A", style_tile_val)],
            [Paragraph("MEDIAN 5-YR CAGR", style_tile_lbl), Paragraph(f"{med_cagr:.1f}%" if not np.isnan(med_cagr) else "N/A", style_tile_val)],
        ],
    ]

    tile_grid = []
    for row in kpis:
        row_cells = []
        for cell in row:
            mini_t = Table([[cell[0]], [cell[1]]], colWidths=[175])
            mini_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            row_cells.append(mini_t)
        tile_grid.append(row_cells)

    tiles_table = Table(tile_grid, colWidths=[180, 180, 180])
    tiles_table.setStyle(TableStyle([
        ("PADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(tiles_table)
    elements.append(Spacer(1, 12))

    # 3. Constituent Company Table (8 Metrics)
    elements.append(Paragraph(f"<b>Constituent Companies & Fundamental Metrics ({len(df_const)})</b>", ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )))

    # Table Header
    headers = [
        Paragraph("Ticker", style_th),
        Paragraph("Company Name", style_th),
        Paragraph("Market Cap (₹Cr)", style_th),
        Paragraph("P/E (x)", style_th),
        Paragraph("ROE (%)", style_th),
        Paragraph("ROCE (%)", style_th),
        Paragraph("D/E (x)", style_th),
        Paragraph("5Y CAGR", style_th),
    ]

    table_data = [headers]
    df_sorted = df_const.sort_values("market_cap", ascending=False)

    for idx, r in df_sorted.iterrows():
        cid = r["company_id"]
        cname = r["company_name"]
        mcap_val = f"₹{r['market_cap']:,.0f}" if r['market_cap'] > 0 else "-"
        pe_val = f"{r['pe_ratio']:.1f}" if not np.isnan(r['pe_ratio']) else "-"
        roe_val = f"{r['roe']:.1f}%" if not np.isnan(r['roe']) else "-"
        roce_val = f"{r['roce']:.1f}%" if not np.isnan(r['roce']) else "-"
        de_val = f"{r['debt_to_equity']:.2f}" if not np.isnan(r['debt_to_equity']) else "-"
        cagr_val = f"{r['revenue_cagr']:.1f}%" if not np.isnan(r['revenue_cagr']) else "-"

        table_data.append([
            Paragraph(f"<b>{cid}</b>", style_td),
            Paragraph(cname[:26], style_td),
            Paragraph(mcap_val, style_td_num),
            Paragraph(pe_val, style_td_num),
            Paragraph(roe_val, style_td_num),
            Paragraph(roce_val, style_td_num),
            Paragraph(de_val, style_td_num),
            Paragraph(cagr_val, style_td_num),
        ])

    col_widths = [60, 140, 75, 45, 55, 55, 50, 60]
    const_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]

    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8FAFC")))

    const_table.setStyle(TableStyle(table_style))
    elements.append(const_table)

    # Footer note
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<font size=6.5 color='#94A3B8'>Nifty 100 Financial Intelligence Platform | Sector Analysis & Median KPI Benchmarking</font>", ParagraphStyle("Foot", parent=styles["Normal"], fontSize=6.5, textColor=colors.HexColor("#94A3B8"))))

    doc.build(elements)
    return True


def generate_all_sector_reports(
    db_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Generates PDF reports for all distinct sectors in the database (11 reports total).
    """
    target_db = Path(db_path or DEFAULT_DB_PATH)
    target_dir = Path(output_dir or SECTOR_REPORTS_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_db))
    sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    companies_df = pd.read_sql_query("SELECT * FROM companies", conn)
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    mc_df = pd.read_sql_query("SELECT * FROM market_cap", conn)
    conn.close()

    broad_sectors = sectors_df["broad_sector"].dropna().unique().tolist()
    generated_files = []

    # 1. Generate for each broad sector
    for sec_name in broad_sectors:
        sec_slice = sectors_df[sectors_df["broad_sector"] == sec_name]
        slug = sanitize_filename(sec_name)
        out_pdf = target_dir / f"{slug}_report.pdf"

        ok = generate_single_sector_report(
            sector_name=sec_name,
            sector_df=sec_slice,
            companies_df=companies_df,
            ratios_df=ratios_df,
            mc_df=mc_df,
            output_pdf_path=out_pdf,
        )
        if ok:
            generated_files.append(str(out_pdf))

    # 2. Also generate an 11th report: "Power_Utilities_report.pdf" (or All_Sectors / Benchmark report)
    power_slice = sectors_df[sectors_df["sub_sector"].str.contains("Power|Utilities|Renewable", case=False, na=False)]
    if not power_slice.empty:
        out_util = target_dir / "Power_Utilities_report.pdf"
        generate_single_sector_report(
            sector_name="Power & Utilities",
            sector_df=power_slice,
            companies_df=companies_df,
            ratios_df=ratios_df,
            mc_df=mc_df,
            output_pdf_path=out_util,
        )
        generated_files.append(str(out_util))

    return {
        "total_sectors": len(generated_files),
        "generated_files": generated_files,
        "output_dir": str(target_dir),
    }


if __name__ == "__main__":
    print("Executing Batch Sector Report Generation...")
    summary = generate_all_sector_reports()
    print(f"Generated {summary['total_sectors']} sector reports -> reports/sector/")
