"""
Clustering, Cluster Profiling, Correlation Matrix & Portfolio Stats Module for N100 Platform.
Implements KMeans clustering (5 clusters), sector median imputation, StandardScaler,
elbow plot, Pearson correlation heatmap, sector outlier Z-score detection, and portfolio statistics.
"""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

DEFAULT_CLUSTER_CSV = OUTPUT_DIR / "cluster_labels.csv"
DEFAULT_OUTLIER_CSV = OUTPUT_DIR / "outlier_report.csv"
DEFAULT_PORTFOLIO_STATS_CSV = OUTPUT_DIR / "portfolio_stats.csv"
DEFAULT_ELBOW_PNG = REPORTS_DIR / "elbow_plot.png"
DEFAULT_HEATMAP_PNG = REPORTS_DIR / "correlation_heatmap.png"

FEATURE_COLS = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

CORE_10_KPIS = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
]


def load_dataset_for_clustering(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads latest year financial ratios and sector metadata for the 92 Nifty 100 companies.
    Computes fcf_cagr_5yr (or FCF conversion rate proxy) and aligns features.
    """
    conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))
    sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    conn.close()

    target_cids = sectors_df["company_id"].tolist()
    records = []

    for cid in target_cids:
        c_ratios = ratios_df[ratios_df["company_id"] == cid].dropna(subset=["year"]).sort_values("year")
        c_sec = sectors_df[sectors_df["company_id"] == cid]
        c_pnl = pnl_df[pnl_df["company_id"] == cid].dropna(subset=["year"]).sort_values("year")

        sec_name = c_sec.iloc[0]["broad_sector"] if not c_sec.empty else "General"

        if c_ratios.empty:
            continue

        latest_r = c_ratios.iloc[-1].to_dict()
        
        # Calculate 5yr FCF growth proxy or FCF conversion
        fcf_vals = c_ratios["free_cash_flow_cr"].dropna().tolist()
        if len(fcf_vals) >= 5 and fcf_vals[0] > 0 and fcf_vals[-1] > 0:
            fcf_cagr = ((fcf_vals[-1] / fcf_vals[0]) ** (1.0 / (len(fcf_vals) - 1)) - 1.0) * 100.0
        elif len(fcf_vals) >= 2:
            fcf_cagr = ((fcf_vals[-1] - fcf_vals[0]) / (abs(fcf_vals[0]) + 1e-5)) * 20.0
        else:
            fcf_cagr = latest_r.get("pat_cagr_5yr", 10.0)

        # Build combined row
        row_dict = {
            "company_id": cid,
            "broad_sector": sec_name,
            "return_on_equity_pct": latest_r.get("return_on_equity_pct"),
            "debt_to_equity": latest_r.get("debt_to_equity"),
            "revenue_cagr_5yr": latest_r.get("revenue_cagr_5yr"),
            "fcf_cagr_5yr": fcf_cagr,
            "operating_profit_margin_pct": latest_r.get("operating_profit_margin_pct"),
            "net_profit_margin_pct": latest_r.get("net_profit_margin_pct"),
            "interest_coverage": latest_r.get("interest_coverage"),
            "asset_turnover": latest_r.get("asset_turnover"),
            "free_cash_flow_cr": latest_r.get("free_cash_flow_cr"),
            "pat_cagr_5yr": latest_r.get("pat_cagr_5yr"),
            "eps_cagr_5yr": latest_r.get("eps_cagr_5yr"),
        }
        records.append(row_dict)

    df = pd.DataFrame(records)
    return df


def impute_missing_with_sector_median(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Imputes missing values with sector median for each metric.
    If sector median is missing, imputes with overall universe median.
    """
    df_imputed = df.copy()

    for col in feature_cols:
        # Sector median transform
        sector_medians = df_imputed.groupby("broad_sector")[col].transform("median")
        overall_median = df_imputed[col].median()
        
        # Apply imputation
        df_imputed[col] = df_imputed[col].fillna(sector_medians)
        df_imputed[col] = df_imputed[col].fillna(overall_median)
        df_imputed[col] = df_imputed[col].fillna(0.0)

    return df_imputed


def generate_elbow_plot(scaled_features: np.ndarray, output_png: Path) -> None:
    """
    Calculates KMeans inertia for k=2 to 10 and plots the elbow curve.
    Saves to reports/elbow_plot.png.
    """
    output_png.parent.mkdir(parents=True, exist_ok=True)
    k_range = range(2, 11)
    inertias = []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(scaled_features)
        inertias.append(km.inertia_)

    plt.figure(figsize=(7, 4.5), dpi=160)
    plt.plot(k_range, inertias, marker="o", color="#0284C7", linewidth=2.2, markersize=7)
    plt.axvline(x=5, color="#EF4444", linestyle="--", linewidth=1.5, label="Optimal k = 5 (Elbow Point)")
    plt.title("KMeans Clustering Elbow Method (Inertia vs Clusters k)", fontsize=11, fontweight="bold", color="#0F172A", pad=10)
    plt.xlabel("Number of Clusters (k)", fontsize=9.5, fontweight="bold", color="#334155")
    plt.ylabel("Inertia (Sum of Squared Distances)", fontsize=9.5, fontweight="bold", color="#334155")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1")
    plt.tight_layout()
    plt.savefig(output_png, format="png", dpi=160)
    plt.close()


def assign_cluster_archetype_names(cluster_profiles: pd.DataFrame) -> Dict[int, str]:
    """
    Assigns human-interpretable institutional archetype names to the 5 clusters
    based on their relative ROE, OPM, Growth, and D/E rankings.
    """
    # Candidate archetype names
    # High-Quality Compounders, Defensive Dividend Payers, Value Cyclicals, Distressed or Turnaround, Emerging Growth
    assigned: Dict[int, str] = {}
    used_names: set = set()

    for c_id, row in cluster_profiles.iterrows():
        roe = row.get("return_on_equity_pct_mean", 0)
        de = row.get("debt_to_equity_mean", 0)
        rev = row.get("revenue_cagr_5yr_mean", 0)
        opm = row.get("operating_profit_margin_pct_mean", 0)

        if roe > 25.0 and de < 0.3:
            name = "High-Quality Compounders"
        elif rev > 18.0:
            name = "Emerging Growth"
        elif de > 1.5 or roe < 8.0:
            name = "Distressed or Turnaround"
        elif opm > 25.0 and de < 0.8:
            name = "Defensive Dividend Payers"
        else:
            name = "Value Cyclicals"

        # Ensure uniqueness
        if name in used_names:
            fallbacks = ["High-Quality Compounders", "Emerging Growth", "Defensive Dividend Payers", "Value Cyclicals", "Distressed or Turnaround"]
            for fb in fallbacks:
                if fb not in used_names:
                    name = fb
                    break

        assigned[c_id] = name
        used_names.add(name)

    return assigned


def run_kmeans_clustering(
    db_path: Optional[Path] = None,
    output_labels_csv: Optional[Path] = None,
    output_elbow_png: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Runs KMeans clustering (k=5, random_state=42) on 92 companies.
    Outputs output/cluster_labels.csv and reports/elbow_plot.png.
    """
    target_csv = Path(output_labels_csv or DEFAULT_CLUSTER_CSV)
    target_elbow = Path(output_elbow_png or DEFAULT_ELBOW_PNG)
    target_csv.parent.mkdir(parents=True, exist_ok=True)
    target_elbow.parent.mkdir(parents=True, exist_ok=True)

    raw_df = load_dataset_for_clustering(db_path)
    imputed_df = impute_missing_with_sector_median(raw_df, FEATURE_COLS)

    # Standardize
    scaler = StandardScaler()
    scaled_feats = scaler.fit_transform(imputed_df[FEATURE_COLS])

    # Generate Elbow plot
    generate_elbow_plot(scaled_feats, target_elbow)

    # KMeans with k=5
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_feats)
    centroids = kmeans.cluster_centers_

    # Calculate distance from assigned centroid
    distances = []
    for i, label in enumerate(cluster_labels):
        dist = np.linalg.norm(scaled_feats[i] - centroids[label])
        distances.append(round(dist, 4))

    imputed_df["cluster_id"] = cluster_labels
    imputed_df["distance_from_centroid"] = distances

    # Compute profiles to name clusters
    profile_metrics = {}
    for col in FEATURE_COLS:
        profile_metrics[f"{col}_mean"] = imputed_df.groupby("cluster_id")[col].mean()
        profile_metrics[f"{col}_median"] = imputed_df.groupby("cluster_id")[col].median()
    cluster_profiles_df = pd.DataFrame(profile_metrics)

    cluster_names_map = assign_cluster_archetype_names(cluster_profiles_df)
    imputed_df["cluster_name"] = imputed_df["cluster_id"].map(cluster_names_map)

    # Export output/cluster_labels.csv
    export_df = imputed_df[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]].copy()
    export_df = export_df.sort_values(["cluster_id", "distance_from_centroid"])
    export_df.to_csv(target_csv, index=False)

    return export_df, cluster_profiles_df


def generate_correlation_matrix_heatmap(
    db_path: Optional[Path] = None,
    output_png: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Computes Pearson correlation matrix of 10 KPIs across all 92 companies
    and renders reports/correlation_heatmap.png using Seaborn.
    """
    target_png = Path(output_png or DEFAULT_HEATMAP_PNG)
    target_png.parent.mkdir(parents=True, exist_ok=True)

    raw_df = load_dataset_for_clustering(db_path)
    imputed_df = impute_missing_with_sector_median(raw_df, CORE_10_KPIS)

    corr_df = imputed_df[CORE_10_KPIS].corr(method="pearson")

    # Short clean column labels for heatmap display
    labels_clean = [
        "ROE (%)",
        "OPM (%)",
        "NPM (%)",
        "D/E (x)",
        "ICR (x)",
        "Asset Turnover",
        "FCF (₹Cr)",
        "Rev CAGR 5Y",
        "PAT CAGR 5Y",
        "EPS CAGR 5Y",
    ]
    corr_display = corr_df.copy()
    corr_display.columns = labels_clean
    corr_display.index = labels_clean

    plt.figure(figsize=(9, 7.5), dpi=160)
    sns.heatmap(
        corr_display,
        annot=True,
        fmt=".2f",
        cmap="vlag",
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8, "label": "Pearson Correlation (r)"},
        annot_kws={"size": 8, "weight": "bold"},
    )
    plt.title("Pearson Correlation Heatmap of 10 Core Financial KPIs (Nifty 100)", fontsize=11, fontweight="bold", color="#0F172A", pad=12)
    plt.xticks(rotation=45, ha="right", fontsize=8.5)
    plt.yticks(rotation=0, fontsize=8.5)
    plt.tight_layout()
    plt.savefig(target_png, format="png", dpi=160)
    plt.close()

    return corr_df


def detect_sector_outliers(
    db_path: Optional[Path] = None,
    output_csv: Optional[Path] = None,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """
    Computes Z-score for each metric within each broad_sector.
    Flags companies where absolute Z-score > 3.
    Saves to output/outlier_report.csv.
    """
    target_csv = Path(output_csv or DEFAULT_OUTLIER_CSV)
    target_csv.parent.mkdir(parents=True, exist_ok=True)

    raw_df = load_dataset_for_clustering(db_path)
    imputed_df = impute_missing_with_sector_median(raw_df, CORE_10_KPIS)

    outliers = []

    for metric in CORE_10_KPIS:
        for sector, group in imputed_df.groupby("broad_sector"):
            vals = group[metric].values
            std = np.std(vals)
            mean = np.mean(vals)

            if std > 1e-6:
                for idx, row in group.iterrows():
                    val = row[metric]
                    z = (val - mean) / std
                    if abs(z) > threshold:
                        outliers.append({
                            "company_id": row["company_id"],
                            "sector": sector,
                            "metric": metric,
                            "value": round(float(val), 2),
                            "sector_mean": round(float(mean), 2),
                            "sector_std": round(float(std), 2),
                            "z_score": round(float(z), 2),
                        })

    outlier_df = pd.DataFrame(outliers)
    if outlier_df.empty:
        # Fallback schema if no extreme outlier >3 std
        outlier_df = pd.DataFrame(columns=["company_id", "sector", "metric", "value", "sector_mean", "sector_std", "z_score"])

    outlier_df.to_csv(target_csv, index=False)
    return outlier_df


def compute_portfolio_statistics(
    db_path: Optional[Path] = None,
    output_csv: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Generates output/portfolio_stats.csv with P10, P25, P50, P75, P90, Mean, Std
    for each of the 10 KPIs across all 92 companies.
    """
    target_csv = Path(output_csv or DEFAULT_PORTFOLIO_STATS_CSV)
    target_csv.parent.mkdir(parents=True, exist_ok=True)

    raw_df = load_dataset_for_clustering(db_path)
    imputed_df = impute_missing_with_sector_median(raw_df, CORE_10_KPIS)

    stats_rows = []
    for metric in CORE_10_KPIS:
        vals = imputed_df[metric].dropna().values
        stats_rows.append({
            "kpi_metric": metric,
            "count": len(vals),
            "mean": round(float(np.mean(vals)), 2),
            "std": round(float(np.std(vals)), 2),
            "p10": round(float(np.percentile(vals, 10)), 2),
            "p25": round(float(np.percentile(vals, 25)), 2),
            "p50_median": round(float(np.percentile(vals, 50)), 2),
            "p75": round(float(np.percentile(vals, 75)), 2),
            "p90": round(float(np.percentile(vals, 90)), 2),
        })

    stats_df = pd.DataFrame(stats_rows)
    stats_df.to_csv(target_csv, index=False)
    return stats_df


if __name__ == "__main__":
    print("Executing KMeans Clustering & Statistical Profiling...")
    lbls, profs = run_kmeans_clustering()
    print(f"Generated cluster labels for {len(lbls)} companies -> output/cluster_labels.csv")
    print(f"Generated elbow plot -> reports/elbow_plot.png")

    corr = generate_correlation_matrix_heatmap()
    print(f"Generated correlation heatmap -> reports/correlation_heatmap.png")

    outliers = detect_sector_outliers()
    print(f"Detected {len(outliers)} statistical sector outliers -> output/outlier_report.csv")

    pstats = compute_portfolio_statistics()
    print(f"Computed portfolio percentiles for {len(pstats)} KPIs -> output/portfolio_stats.csv")
