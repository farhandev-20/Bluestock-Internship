"""
Peer Comparison and Percentile Ranking Engine for N100 Intelligence Platform.
Computes peer percentile rankings across 11 peer groups for 10 metrics with D/E inversion,
populates SQLite 'peer_percentiles' table, generates matplotlib radar charts,
and exports 11-sheet formatted Excel report 'output/peer_comparison.xlsx'.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from src.screener.engine import load_screener_universe

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"
RADAR_CHARTS_DIR = REPORTS_DIR / "radar_charts"
DEFAULT_EXCEL_PATH = OUTPUT_DIR / "peer_comparison.xlsx"

# 10 Metrics for Peer Percentile Ranking
PEER_RANK_METRICS = [
    ("return_on_equity_pct", "ROE", False),              # higher is better
    ("roce_percentage", "ROCE", False),                  # higher is better
    ("net_profit_margin_pct", "Net Margin", False),      # higher is better
    ("debt_to_equity", "D/E Ratio", True),               # INVERTED: lower is better
    ("free_cash_flow_cr", "Free Cash Flow", False),      # higher is better
    ("pat_cagr_5yr", "PAT CAGR 5yr", False),             # higher is better
    ("revenue_cagr_5yr", "Revenue CAGR 5yr", False),     # higher is better
    ("eps_cagr_5yr", "EPS CAGR 5yr", False),             # higher is better
    ("interest_coverage", "Interest Coverage", False),   # higher is better (debt free = inf)
    ("asset_turnover", "Asset Turnover", False),         # higher is better
]

# 8 Axes for Radar Chart
RADAR_AXES = [
    ("return_on_equity_pct", "ROE"),
    ("roce_percentage", "ROCE"),
    ("net_profit_margin_pct", "NPM"),
    ("debt_to_equity", "D/E (Inv)"),
    ("free_cash_flow_cr", "FCF"),
    ("pat_cagr_5yr", "PAT CAGR"),
    ("revenue_cagr_5yr", "Rev CAGR"),
    ("composite_quality_score", "Quality"),
]


def load_peer_groups(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load peer group assignments from SQLite peer_groups table.
    """
    conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))
    df = pd.read_sql_query("SELECT * FROM peer_groups", conn)
    conn.close()
    return df


def compute_peer_percentiles(
    universe_df: Optional[pd.DataFrame] = None,
    peer_groups_df: Optional[pd.DataFrame] = None,
    target_year: int = 2024,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute PERCENT_RANK (0.0 to 100.0) for 10 metrics within each of the 11 peer groups.
    Handles D/E inversion (lower D/E -> higher percentile rank).
    Treats Debt Free / None ICR as highest ranking (top percentile).
    Returns (peer_percentiles_long_df, peer_master_merged_df).
    """
    universe = universe_df if universe_df is not None else load_screener_universe(target_year=target_year)
    peers = peer_groups_df if peer_groups_df is not None else load_peer_groups()

    # Merge universe with peer group assignments
    peer_merged = pd.merge(peers, universe, left_on="company_id", right_on="company_id", how="inner")

    long_records = []
    
    # Process each peer group
    for group_name, group_df in peer_merged.groupby("peer_group_name"):
        n_members = len(group_df)

        for col_key, metric_label, is_inverted in PEER_RANK_METRICS:
            raw_vals = group_df[col_key].copy()

            # Special treatment for ICR: fill NaN/None (Debt Free) with infinite proxy value
            if col_key == "interest_coverage":
                raw_vals = raw_vals.fillna(99999.0)

            # Sort and compute percentiles: PERCENT_RANK = (rank - 1) / (N - 1) * 100
            # If N == 1, rank is 100.0
            for _, row in group_df.iterrows():
                cid = row["company_id"]
                val = row.get(col_key)
                
                # Comparison value
                comp_val = 99999.0 if (col_key == "interest_coverage" and pd.isna(val)) else (val if pd.notna(val) else -99999.0)

                if n_members <= 1:
                    pct_rank = 100.0
                else:
                    if not is_inverted:
                        # Higher value -> Higher rank
                        strictly_less = (raw_vals.dropna() < comp_val).sum()
                        pct_rank = (strictly_less / (n_members - 1)) * 100.0
                    else:
                        # Inverted: Lower value -> Higher rank
                        strictly_greater = (raw_vals.dropna() > comp_val).sum()
                        pct_rank = (strictly_greater / (n_members - 1)) * 100.0

                long_records.append(
                    {
                        "company_id": cid,
                        "peer_group_name": group_name,
                        "metric": col_key,
                        "value": val if pd.notna(val) else None,
                        "percentile_rank": round(pct_rank, 2),
                        "year": target_year,
                    }
                )

    long_df = pd.DataFrame(long_records)
    return long_df, peer_merged


def populate_peer_percentiles_table(
    long_df: pd.DataFrame,
    db_path: Optional[Path] = None,
) -> int:
    """
    Populate SQLite table 'peer_percentiles' with computed percentiles.
    """
    target_db = Path(db_path or DEFAULT_DB_PATH)
    conn = sqlite3.connect(str(target_db))
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            id INTEGER PRIMARY KEY,
            company_id TEXT,
            peer_group_name TEXT,
            metric TEXT,
            value REAL,
            percentile_rank REAL,
            year INTEGER,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        """
    )
    cursor.execute("DELETE FROM peer_percentiles;")

    save_df = long_df.copy()
    save_df["id"] = range(1, len(save_df) + 1)
    save_df.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM peer_percentiles;").fetchone()[0]
    conn.close()
    return count


def get_company_peer_percentiles(
    company_id: str,
    db_path: Optional[Path] = None,
) -> Union[pd.DataFrame, str]:
    """
    Retrieve percentile rankings for a company.
    If company is not assigned to any peer group, returns 'No peer group assigned'.
    """
    conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))
    query = f"SELECT * FROM peer_percentiles WHERE company_id = '{company_id}';"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return "No peer group assigned"
    return df


def generate_radar_charts(
    universe_df: Optional[pd.DataFrame] = None,
    peer_merged_df: Optional[pd.DataFrame] = None,
    output_dir: Optional[Path] = None,
) -> List[Path]:
    """
    Generate high-resolution polar/radar chart PNGs for each company with peer group overlay.
    Saved to reports/radar_charts/{company_id}_radar.png.
    """
    out_dir = Path(output_dir or RADAR_CHARTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    universe = universe_df if universe_df is not None else load_screener_universe()
    peers = peer_merged_df if peer_merged_df is not None else load_peer_groups()

    # Create mapping of company_id to peer group
    comp_peer_map = dict(zip(peers["company_id"], peers["peer_group_name"]))
    
    # Group universe by peer group
    peer_members = {}
    for cid, grp in comp_peer_map.items():
        peer_members.setdefault(grp, []).append(cid)

    # 8 Axes labels & scaling limits
    axes_keys = [k[0] for k in RADAR_AXES]
    axes_labels = [k[1] for k in RADAR_AXES]
    num_vars = len(axes_labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete circle

    # Compute universe average for standalone reference
    univ_avg_scores = {}
    for k in axes_keys:
        if k == "debt_to_equity":
            val = (1.0 / (universe[k].dropna() + 0.1)).mean()
        else:
            val = universe[k].dropna().mean()
        univ_avg_scores[k] = val if pd.notna(val) else 50.0

    generated_charts = []

    for _, row in universe.iterrows():
        cid = row["company_id"]
        cname = row.get("company_name", cid)
        grp_name = comp_peer_map.get(cid)

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

        # Extract normalized 0-100 values for company
        comp_scores = []
        for k in axes_keys:
            raw_val = row.get(k)
            if pd.isna(raw_val) or raw_val is None:
                score = 50.0
            elif k == "debt_to_equity":
                # Invert D/E: 0 -> 100, 2 -> 33, >3 -> 10
                score = max(0.0, min(100.0, 100.0 / (raw_val + 1.0)))
            elif k == "composite_quality_score":
                score = float(raw_val)
            else:
                # Winsorised min-max scale against universe
                s_min = universe[k].quantile(0.05)
                s_max = universe[k].quantile(0.95)
                if s_max > s_min:
                    score = max(0.0, min(100.0, (raw_val - s_min) / (s_max - s_min) * 100.0))
                else:
                    score = 50.0
            comp_scores.append(score)

        comp_scores += comp_scores[:1]

        # Extract peer average (or universe average)
        if grp_name and grp_name in peer_members:
            peer_df = universe[universe["company_id"].isin(peer_members[grp_name])]
            peer_scores = []
            for k in axes_keys:
                if k == "debt_to_equity":
                    raw_de = peer_df[k].dropna()
                    score = (100.0 / (raw_de + 1.0)).mean() if not raw_de.empty else 50.0
                elif k == "composite_quality_score":
                    score = peer_df[k].mean()
                else:
                    s_min = universe[k].quantile(0.05)
                    s_max = universe[k].quantile(0.95)
                    raw_vals = peer_df[k].dropna()
                    if s_max > s_min and not raw_vals.empty:
                        score = ((raw_vals.mean() - s_min) / (s_max - s_min) * 100.0)
                    else:
                        score = 50.0
                peer_scores.append(max(0.0, min(100.0, score)))
            peer_scores += peer_scores[:1]
            ref_label = f"Peer Avg ({grp_name})"
        else:
            peer_scores = [50.0] * num_vars
            peer_scores += peer_scores[:1]
            ref_label = "Nifty 100 Benchmark"

        # Plot company polygon (filled)
        ax.plot(angles, comp_scores, color="#1F77B4", linewidth=2.5, label=f"{cid} (Company)")
        ax.fill(angles, comp_scores, color="#1F77B4", alpha=0.35)

        # Plot peer group average overlay (dashed outline)
        ax.plot(angles, peer_scores, color="#D62728", linewidth=2.0, linestyle="--", label=ref_label)

        # Set axes labels & grid
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), axes_labels, fontsize=10, weight="bold")
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color="gray")
        ax.grid(color="gray", linestyle=":", linewidth=0.7)

        title_str = f"{cid} - {cname}\nPeer Group: {grp_name or 'No Peer Group'}"
        ax.set_title(title_str, size=12, weight="bold", y=1.1)
        ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.15), fontsize=9)

        chart_path = out_dir / f"{cid}_radar.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=120, bbox_inches="tight")
        plt.close(fig)

        generated_charts.append(chart_path)

    return generated_charts


def export_peer_comparison_excel(
    peer_merged_df: Optional[pd.DataFrame] = None,
    long_percentiles_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate output/peer_comparison.xlsx with 11 worksheets (one per peer group).
    - Color-coded percentile cells (>=75th green, 25th-75th yellow, <=25th red)
    - Benchmark company row highlighted in gold/amber
    - Summary median row at the bottom of each sheet
    """
    target_path = Path(output_path or DEFAULT_EXCEL_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if peer_merged_df is None or long_percentiles_df is None:
        long_percentiles_df, peer_merged_df = compute_peer_percentiles()

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Metrics displayed in sheet
    metric_cols = [
        ("return_on_equity_pct", "ROE (%)", "0.0%"),
        ("roce_percentage", "ROCE (%)", "0.0%"),
        ("net_profit_margin_pct", "Net Margin (%)", "0.0%"),
        ("operating_profit_margin_pct", "OPM (%)", "0.0%"),
        ("debt_to_equity", "D/E Ratio", "0.00"),
        ("interest_coverage", "ICR", "0.00"),
        ("free_cash_flow_cr", "FCF (Cr)", "#,##0"),
        ("capex_cr", "CapEx (Cr)", "#,##0"),
        ("cash_from_operations_cr", "CFO (Cr)", "#,##0"),
        ("revenue_cagr_5yr", "5Yr Rev CAGR (%)", "0.0%"),
        ("pat_cagr_5yr", "5Yr PAT CAGR (%)", "0.0%"),
        ("eps_cagr_5yr", "5Yr EPS CAGR (%)", "0.0%"),
        ("pe_ratio", "P/E Ratio", "0.0"),
        ("pb_ratio", "P/B Ratio", "0.0"),
        ("dividend_yield_pct", "Div Yield (%)", "0.0%"),
        ("market_cap_crore", "Market Cap (Cr)", "#,##0"),
        ("sales", "Sales (Cr)", "#,##0"),
        ("net_profit", "Net Profit (Cr)", "#,##0"),
        ("asset_turnover", "Asset Turnover", "0.00"),
        ("composite_quality_score", "Quality Score", "0.0"),
    ]

    # Styling definitions
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    benchmark_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # Gold/Amber highlight
    benchmark_font = Font(name="Calibri", size=11, bold=True, color="000000")
    median_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")  # Soft blue
    median_font = Font(name="Calibri", size=11, bold=True, color="000000")

    pct_green = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # >= 75th
    pct_yellow = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid") # 25th - 75th
    pct_red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")    # <= 25th

    border_thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    # Long percentiles lookup: (company_id, metric) -> percentile_rank
    pct_lookup = long_percentiles_df.set_index(["company_id", "metric"])["percentile_rank"].to_dict()

    # Iterate through each peer group (11 groups)
    for grp_name, grp_df in peer_merged_df.groupby("peer_group_name"):
        sheet_title = str(grp_name)[:31]
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True

        # Headers
        headers = ["Company ID", "Company Name", "Benchmark"]
        for _, col_lbl, _ in metric_cols:
            headers.append(col_lbl)
            headers.append(f"{col_lbl} (Pct Rank)")

        for c_idx, h_text in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=c_idx, value=h_text)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Populate rows
        data_rows = []
        for r_idx, (_, row) in enumerate(grp_df.iterrows(), start=2):
            cid = row["company_id"]
            cname = row.get("company_name", cid)
            is_bm = bool(row.get("is_benchmark", 0))

            ws.cell(row=r_idx, column=1, value=cid).border = border_thin
            ws.cell(row=r_idx, column=2, value=cname).border = border_thin
            ws.cell(row=r_idx, column=3, value="★ Benchmark" if is_bm else "Peer").border = border_thin

            curr_col = 4
            row_vals = []
            for col_key, col_lbl, _ in metric_cols:
                raw_val = row.get(col_key)
                cell_val = raw_val if pd.notna(raw_val) else "-"
                val_cell = ws.cell(row=r_idx, column=curr_col, value=cell_val)
                val_cell.border = border_thin
                row_vals.append(raw_val if pd.notna(raw_val) else np.nan)

                # Percentile Cell
                p_rank = pct_lookup.get((cid, col_key))
                p_cell_val = f"{p_rank:.1f}%" if p_rank is not None else "-"
                pct_cell = ws.cell(row=r_idx, column=curr_col + 1, value=p_cell_val)
                pct_cell.border = border_thin
                pct_cell.alignment = Alignment(horizontal="right", vertical="center")

                # Color-code percentile rank
                if p_rank is not None:
                    if p_rank >= 75.0:
                        pct_cell.fill = pct_green
                    elif p_rank >= 25.0:
                        pct_cell.fill = pct_yellow
                    else:
                        pct_cell.fill = pct_red

                curr_col += 2

            # If benchmark company, highlight entire row with gold/amber fill
            if is_bm:
                for c in range(1, len(headers) + 1):
                    cell = ws.cell(row=r_idx, column=c)
                    if c <= 3 or cell.fill.fill_type is None:
                        cell.fill = benchmark_fill
                    cell.font = benchmark_font

            data_rows.append(row_vals)

        # Summary Row: Peer Group Median (Row r_idx + 1)
        med_row_idx = len(grp_df) + 2
        ws.cell(row=med_row_idx, column=1, value="GROUP MEDIAN").font = median_font
        ws.cell(row=med_row_idx, column=2, value=f"{len(grp_df)} Companies").font = median_font
        ws.cell(row=med_row_idx, column=3, value="Summary").font = median_font

        for c in range(1, 4):
            ws.cell(row=med_row_idx, column=c).fill = median_fill
            ws.cell(row=med_row_idx, column=c).border = border_thin

        # Compute medians
        data_matrix = np.array(data_rows, dtype=float)
        curr_col = 4
        for m_idx, (col_key, col_lbl, _) in enumerate(metric_cols):
            col_data = data_matrix[:, m_idx]
            valid_col = col_data[~np.isnan(col_data)]
            med_val = np.median(valid_col) if len(valid_col) > 0 else "-"

            val_cell = ws.cell(row=med_row_idx, column=curr_col, value=round(med_val, 2) if isinstance(med_val, (int, float)) else med_val)
            val_cell.fill = median_fill
            val_cell.font = median_font
            val_cell.border = border_thin

            pct_cell = ws.cell(row=med_row_idx, column=curr_col + 1, value="50.0%")
            pct_cell.fill = median_fill
            pct_cell.font = median_font
            pct_cell.border = border_thin

            curr_col += 2

        # Auto adjust column widths
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    wb.save(target_path)
    return target_path


def run_peer_engine(
    db_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Orchestrates full peer pipeline:
    1. Computes percentiles for all 11 peer groups.
    2. Populates SQLite peer_percentiles table.
    3. Exports peer_comparison.xlsx with 11 sheets.
    4. Generates radar charts for all companies.
    """
    long_df, merged_df = compute_peer_percentiles()
    loaded_count = populate_peer_percentiles_table(long_df, db_path=db_path)
    excel_path = export_peer_comparison_excel(merged_df, long_df, output_path=output_dir / "peer_comparison.xlsx" if output_dir else None)
    radar_paths = generate_radar_charts(peer_merged_df=merged_df)

    return {
        "peer_percentiles_count": loaded_count,
        "peer_groups_count": merged_df["peer_group_name"].nunique(),
        "excel_report": excel_path,
        "radar_charts_count": len(radar_paths),
    }


if __name__ == "__main__":
    print("Executing Peer Ranking & Comparison Engine...")
    res = run_peer_engine()
    print(f"Successfully populated {res['peer_percentiles_count']} peer percentile records across {res['peer_groups_count']} peer groups.")
    print(f"Generated {res['radar_charts_count']} radar charts in reports/radar_charts/")
    print(f"Exported peer comparison workbook to {res['excel_report']}")
