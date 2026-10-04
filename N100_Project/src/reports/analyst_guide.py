"""
10+ Page Analyst Guide PDF Generator for N100 Financial Intelligence Platform.
Generates institutional documentation covering dashboard navigation, screener formulas,
peer radars, capital allocation archetypes, REST API cURL examples, and troubleshooting.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "docs"
DEFAULT_GUIDE_PDF = DOCS_DIR / "analyst_guide.pdf"


class NumberedCanvas:
    """Two-pass canvas helper or running footer."""
    pass


def build_analyst_guide_pdf(output_pdf_path: Optional[Path] = None) -> Path:
    target_pdf = Path(output_pdf_path or DEFAULT_GUIDE_PDF)
    target_pdf.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(target_pdf),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_cover_title = ParagraphStyle("CoverTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=26, textColor=colors.HexColor("#0B192C"), leading=30, alignment=1)
    style_cover_sub = ParagraphStyle("CoverSub", parent=styles["Normal"], fontName="Helvetica", fontSize=12, textColor=colors.HexColor("#475569"), leading=16, alignment=1)
    style_h1 = ParagraphStyle("ChapterH1", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=15, textColor=colors.HexColor("#0F172A"), leading=18, spaceAfter=8)
    style_h2 = ParagraphStyle("SectionH2", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#1E293B"), leading=14, spaceBefore=8, spaceAfter=4)
    style_p = ParagraphStyle("BodyP", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#334155"), leading=12, spaceAfter=6)
    style_code = ParagraphStyle("CodeP", parent=styles["Normal"], fontName="Courier", fontSize=7.5, textColor=colors.HexColor("#0F172A"), leading=10)
    style_th = ParagraphStyle("THP", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#FFFFFF"), alignment=1)
    style_td = ParagraphStyle("TDP", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, textColor=colors.HexColor("#334155"), leading=10)

    elements: List[Any] = []

    # =========================================================================
    # PAGE 1: COVER PAGE
    # =========================================================================
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("<b>N100 FINANCIAL INTELLIGENCE</b>", style_cover_title))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Comprehensive Equity Research Analyst & System Integration Guide</b>", style_cover_sub))
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor("#0284C7"), spaceAfter=30))

    meta_table = Table([
        [Paragraph("<b>Target Universe:</b>", style_td), Paragraph("NIFTY 100 Constituents (92 Active Large/Mid Caps)", style_td)],
        [Paragraph("<b>Platform Architecture:</b>", style_td), Paragraph("Python 3.14, Streamlit, FastAPI REST, SQLite3, ReportLab", style_td)],
        [Paragraph("<b>Intelligence Modules:</b>", style_td), Paragraph("Ratio Engine, Valuation Scorer, NLP Pros/Cons, KMeans Clustering", style_td)],
        [Paragraph("<b>Document Version:</b>", style_td), Paragraph("v1.0.0 (Production Release — Day 45)", style_td)],
        [Paragraph("<b>Author & Sign-Off:</b>", style_td), Paragraph("N100 Quantitative Analytics & Engineering Team", style_td)],
    ], colWidths=[150, 320])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 120))
    elements.append(Paragraph("<font size=7 color='#94A3B8'>Confidential & Proprietary | Nifty 100 Financial Intelligence Platform</font>", ParagraphStyle("CoverFoot", parent=styles["Normal"], alignment=1)))
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 2: CHAPTER 1 - EXECUTIVE OVERVIEW & ARCHITECTURE
    # =========================================================================
    elements.append(Paragraph("Chapter 1: Executive Architecture & Platform Overview", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("The N100 Financial Intelligence Platform is an institutional-grade equity analytics infrastructure designed for portfolio managers, fundamental research analysts, and risk teams covering Indian equities.", style_p))
    elements.append(Paragraph("The platform ingests over a decade of audited financial statements (P&L, Balance Sheet, Cash Flow), market capitalisation multiples, and BSE regulatory filings across 100 constituents, computing 10 core fundamental KPIs, 8 capital allocation archetypes, valuation flags, and NLP thesis points.", style_p))
    
    elements.append(Paragraph("Core Technology Stack Components", style_h2))
    tech_table = Table([
        [Paragraph("Layer", style_th), Paragraph("Technology", style_th), Paragraph("Key Functional Purpose", style_th)],
        [Paragraph("Data Storage", style_td), Paragraph("SQLite3 (B-Tree Indexed)", style_td), Paragraph("Stores 10 normalized tables across 100 companies with foreign key integrity.", style_td)],
        [Paragraph("Analytics Engine", style_td), Paragraph("NumPy, Pandas, Scikit-Learn", style_td), Paragraph("Computes multi-period CAGR, leverage flags, CFO quality, and KMeans clustering.", style_td)],
        [Paragraph("User Interface", style_td), Paragraph("Streamlit 1.36+ Multi-Page", style_td), Paragraph("8 interactive screens with glassmorphic styling and Plotly visualizations.", style_td)],
        [Paragraph("REST API", style_td), Paragraph("FastAPI, Uvicorn, ASGI", style_td), Paragraph("16 high-throughput endpoints with CORS and request latency middleware.", style_td)],
        [Paragraph("Document Engine", style_td), Paragraph("ReportLab & Matplotlib", style_td), Paragraph("Compiles 2-page company factsheets, 11 sector reports, and portfolio summaries.", style_td)],
    ], colWidths=[110, 140, 270])
    tech_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    elements.append(tech_table)
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 3: CHAPTER 2 - DASHBOARD NAVIGATION & SCREENS
    # =========================================================================
    elements.append(Paragraph("Chapter 2: Streamlit Dashboard Navigation", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("The interactive web dashboard is accessible on <code>http://localhost:8501</code> and organized into 8 purpose-built analytical screens:", style_p))
    
    screens_data = [
        [Paragraph("Screen", style_th), Paragraph("Navigation Path", style_th), Paragraph("Analyst Workflow & Core Utility", style_th)],
        [Paragraph("01. Executive Overview", style_td), Paragraph("pages/01_home.py", style_td), Paragraph("Universe summary KPI cards, fiscal year timeline filter, sector donut chart, quality leaderboard.", style_td)],
        [Paragraph("02. Company Profile", style_td), Paragraph("pages/02_profile.py", style_td), Paragraph("Single ticker search, 10-Yr sales/profit bars, ROE/OPM trends, NLP pros/cons badges.", style_td)],
        [Paragraph("03. Financial Screener", style_td), Paragraph("pages/03_screener.py", style_td), Paragraph("10 continuous KPI sliders, 6 one-click investment presets, reactive table, CSV export.", style_td)],
        [Paragraph("04. Peer Comparison", style_td), Paragraph("pages/04_peers.py", style_td), Paragraph("11 specialized cohorts, 8-axis Plotly Scatterpolar radar chart against peer average.", style_td)],
        [Paragraph("05. Trend Analysis", style_td), Paragraph("pages/05_trends.py", style_td), Paragraph("Multi-metric overlay up to 3 financial series across 10 years with point-in-time YoY % annotations.", style_td)],
        [Paragraph("06. Sector Analysis", style_td), Paragraph("pages/06_sectors.py", style_td), Paragraph("Macro landscape 4D bubble chart (Revenue vs ROE vs Market Cap) with median bar charts.", style_td)],
        [Paragraph("07. Capital Allocation", style_td), Paragraph("pages/07_capital.py", style_td), Paragraph("Hierarchical Plotly Treemap of 8 cash flow archetypes with constituent drilldown.", style_td)],
        [Paragraph("08. Annual Reports", style_td), Paragraph("pages/08_reports.py", style_td), Paragraph("Filing repository with live BSE HTTP status verification and direct PDF download links.", style_td)],
    ]
    t_screens = Table(screens_data, colWidths=[120, 120, 280])
    t_screens.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    elements.append(t_screens)
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 4: CHAPTER 3 - SCREENER FORMULAS & PRESET STRATEGIES
    # =========================================================================
    elements.append(Paragraph("Chapter 3: Financial Screener & Preset Strategies", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("The screener engine evaluates 10 continuous fundamental variables and composite quality rankings:", style_p))

    presets_data = [
        [Paragraph("Preset Strategy", style_th), Paragraph("Quantitative Filtering Criteria", style_th), Paragraph("Investment Rationale", style_th)],
        [Paragraph("Quality Compounders", style_td), Paragraph("ROE >= 20%, D/E <= 0.5, Rev CAGR >= 10%", style_td), Paragraph("Capital-efficient market leaders compounding book value with low financial leverage.", style_td)],
        [Paragraph("Value Bargains", style_td), Paragraph("P/E <= 20x, P/B <= 3x, FCF >= 0", style_td), Paragraph("Undervalued opportunities trading below sector median multiples with positive cash flow.", style_td)],
        [Paragraph("Growth Leaders", style_td), Paragraph("Rev CAGR >= 15%, PAT CAGR >= 15%, OPM >= 15%", style_td), Paragraph("High top-line and bottom-line compounding with strong operating leverage.", style_td)],
        [Paragraph("Dividend Yielders", style_td), Paragraph("Div Yield >= 2.5%, FCF >= 0, D/E <= 1.0", style_td), Paragraph("Generous income distributions backed by healthy free cash flow and conservative debt.", style_td)],
        [Paragraph("Debt-Free Champions", style_td), Paragraph("D/E == 0 (or <= 0.05), ICR >= 10x", style_td), Paragraph("Fortress balance sheets immune to rising interest rate cycles.", style_td)],
        [Paragraph("Turnaround Candidates", style_td), Paragraph("PAT CAGR >= 20%, OPM Improving YoY", style_td), Paragraph("Operational restructuring candidates demonstrating rapid earnings recovery.", style_td)],
    ]
    t_presets = Table(presets_data, colWidths=[120, 160, 240])
    t_presets.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    elements.append(t_presets)
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 5: CHAPTER 4 - PEER COMPARISON & RADAR BENCHMARKING
    # =========================================================================
    elements.append(Paragraph("Chapter 4: Peer Group Radar Benchmarking", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("To eliminate broad-market distortion, the universe is segmented into 11 specialized industry cohorts:", style_p))
    elements.append(Paragraph("1. Private Banks (Benchmark: HDFCBANK)<br/>2. Public Sector Banks (Benchmark: SBIN)<br/>3. IT Services (Benchmark: TCS)<br/>4. Pharmaceuticals (Benchmark: SUNPHARMA)<br/>5. Automobiles (Benchmark: MARUTI)<br/>6. Life Insurance (Benchmark: HDFCLIFE)<br/>7. Oil & Gas (Benchmark: RELIANCE)<br/>8. Power & Utilities (Benchmark: NTPC)<br/>9. Steel & Mining (Benchmark: TATASTEEL)<br/>10. FMCG (Benchmark: HINDUNILVR)<br/>11. Consumer Finance (Benchmark: BAJFINANCE)", style_p))
    elements.append(Paragraph("Radar Chart Axes & Normalization", style_h2))
    elements.append(Paragraph("Radar charts project 8 normalized axes: (1) ROE, (2) OPM, (3) NPM, (4) 5-Yr Rev CAGR, (5) 5-Yr PAT CAGR, (6) Asset Turnover, (7) ICR, (8) Composite Quality Score.", style_p))
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 6: CHAPTER 5 - CAPITAL ALLOCATION & CASH FLOW INTELLIGENCE
    # =========================================================================
    elements.append(Paragraph("Chapter 5: Capital Allocation & Cash Flow Archetypes", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("Every company's cash flow pattern is evaluated across CFO, CFI, and CFF cash vectors into 8 distinct archetypes:", style_p))

    cf_data = [
        [Paragraph("Cash Vector (CFO, CFI, CFF)", style_th), Paragraph("Archetype Label", style_th), Paragraph("Institutional Significance", style_th)],
        [Paragraph("(+, -, -)", style_td), Paragraph("Reinvestor / Shareholder Returns", style_td), Paragraph("Healthy organic cash generation funding internal growth and paying dividends/debt.", style_td)],
        [Paragraph("(+, +, -)", style_td), Paragraph("Liquidating Assets", style_td), Paragraph("Divesting fixed assets or investments to repay financing liabilities.", style_td)],
        [Paragraph("(-, +, +)", style_td), Paragraph("Distress Signal", style_td), Paragraph("Operations burning cash; reliant on asset sales and external borrowing.", style_td)],
        [Paragraph("(-, -, +)", style_td), Paragraph("Growth Funded by Debt", style_td), Paragraph("High CapEx expansion financed by external capital raises before operational breakeven.", style_td)],
        [Paragraph("(+, +, +)", style_td), Paragraph("Cash Accumulator", style_td), Paragraph("Cash inflow across all three activities resulting in large treasury build-up.", style_td)],
        [Paragraph("(-, -, -)", style_td), Paragraph("Pre-Revenue / Cash Burn", style_td), Paragraph("Cash drains across operating, investing, and debt repayment.", style_td)],
        [Paragraph("(+, -, +)", style_td), Paragraph("Mixed / Expansionist", style_td), Paragraph("Operating cash and new borrowing funding massive strategic CapEx.", style_td)],
    ]
    t_cf = Table(cf_data, colWidths=[140, 150, 230])
    t_cf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    elements.append(t_cf)
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 7: CHAPTER 6 - KMEANS CLUSTERING & STATISTICAL PROFILING
    # =========================================================================
    elements.append(Paragraph("Chapter 6: Machine Learning Clustering & Statistics", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("Unsupervised KMeans clustering (k=5, random_state=42) classifies all 92 companies into data-driven clusters:", style_p))
    elements.append(Paragraph("<b>1. High-Quality Compounders</b>: Companies with ROE > 25%, OPM > 20%, low leverage (D/E < 0.3).<br/><b>2. Emerging Growth</b>: High revenue CAGR (>18%) with moderate capital intensity.<br/><b>3. Value Cyclicals</b>: Mature businesses with cyclical operating margins and moderate ROE.<br/><b>4. Defensive Dividend Payers</b>: Stable utilities/FMCG with steady cash flow and low volatility.<br/><b>5. Distressed or Turnaround</b>: Higher leverage or depressed profitability requiring structural recovery.", style_p))
    elements.append(Paragraph("Sector Outlier Detection", style_h2))
    elements.append(Paragraph("Statistical anomalies are flagged when any company metric exhibits absolute Z-score > 3 relative to its broad sector cohort mean and standard deviation.", style_p))
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 8: CHAPTER 7 - VALUATION ENGINE & OVERVALUATION SCORING
    # =========================================================================
    elements.append(Paragraph("Chapter 7: Valuation Engine & Relative Flags", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("The valuation engine establishes sector median P/E benchmarks and identifies relative mispricing:", style_p))
    elements.append(Paragraph("<b>Overvaluation Caution Flag:</b> Triggered when constituent P/E > 1.5x Sector Median P/E.<br/><b>Undervaluation Discount Flag:</b> Triggered when constituent P/E < 0.7x Sector Median P/E.<br/><b>Fair Value Range:</b> Constituent P/E between 0.7x and 1.5x Sector Median P/E.", style_p))
    elements.append(Paragraph("Free Cash Flow Yield", style_h2))
    elements.append(Paragraph("$$\\text{FCF Yield (\\%)} = \\frac{\\text{Free Cash Flow (₹ Cr)}}{\\text{Market Capitalisation (₹ Cr)}} \\times 100$$", style_p))
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 9: CHAPTER 8 - REST API REFERENCE & CURL EXAMPLES
    # =========================================================================
    elements.append(Paragraph("Chapter 8: FastAPI REST Service & Integration", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("The API service runs on port 8000. Key cURL command examples:", style_p))

    api_box = [
        [Paragraph("Endpoint & Purpose", style_th), Paragraph("Example cURL Request", style_th)],
        [Paragraph("Health Check", style_td), Paragraph("<code>curl http://localhost:8000/api/v1/health</code>", style_code)],
        [Paragraph("Company Profile", style_td), Paragraph("<code>curl http://localhost:8000/api/v1/companies/TCS</code>", style_code)],
        [Paragraph("P&L History", style_td), Paragraph("<code>curl http://localhost:8000/api/v1/companies/TCS/pl?from_year=2020</code>", style_code)],
        [Paragraph("Screener Query", style_td), Paragraph("<code>curl http://localhost:8000/api/v1/screener?min_roe=15&max_de=1</code>", style_code)],
        [Paragraph("Sector Medians", style_td), Paragraph("<code>curl http://localhost:8000/api/v1/sectors</code>", style_code)],
        [Paragraph("Peer Radar Data", style_td), Paragraph("<code>curl http://localhost:8000/api/v1/companies/TCS/peers/compare</code>", style_code)],
        [Paragraph("Download Tearsheet", style_td), Paragraph("<code>curl -O http://localhost:8000/api/v1/companies/TCS/tearsheet</code>", style_code)],
    ]
    t_api = Table(api_box, colWidths=[150, 370])
    t_api.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
    ]))
    elements.append(t_api)
    elements.append(PageBreak())

    # =========================================================================
    # PAGE 10: CHAPTER 9 - DATA QUALITY RULES & TROUBLESHOOTING
    # =========================================================================
    elements.append(Paragraph("Chapter 9: Data Quality Rules & System Maintenance", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    elements.append(Paragraph("16 Automated Data Quality Rules are enforced across all 12 ingested datasets:", style_p))
    elements.append(Paragraph("<b>DQ-01:</b> Primary key null checks.<br/><b>DQ-02:</b> Primary key uniqueness.<br/><b>DQ-03:</b> Foreign key referential integrity.<br/><b>DQ-04:</b> Mandatory company attributes.<br/><b>DQ-05:</b> Year range bounds [2000, 2030].<br/><b>DQ-06 to DQ-09:</b> Stock price non-negativity, High-Low bounds, ISO date validation.<br/><b>DQ-10 to DQ-11:</b> Balance sheet accounting equation (Assets == Liabilities) and sub-component reconciliation.<br/><b>DQ-12:</b> Cash flow waterfall reconciliation (CFO + CFI + CFF == Net Cash Flow).<br/><b>DQ-13 to DQ-16:</b> Valuation non-negativity, sector weights, URL protocols, and composite entity-time uniqueness.", style_p))
    elements.append(Paragraph("Troubleshooting Tips", style_h2))
    elements.append(Paragraph("1. If a company ticker shows missing ratios, verify `output/validation_failures.csv` for data anomalies.<br/>2. If port 8000 is occupied, run FastAPI on custom port: `uvicorn src.api.main:app --port 8080`.<br/>3. To re-run test suite with HTML report: `pytest --html=reports/pytest_report.html --self-contained-html`.", style_p))

    # Build PDF
    doc.build(elements)
    return target_pdf


if __name__ == "__main__":
    print("Generating 10-Page Analyst Guide PDF...")
    out_guide = build_analyst_guide_pdf()
    print(f"Analyst guide PDF generated successfully -> {out_guide}")
