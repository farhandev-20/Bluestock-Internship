"""
Compute fund performance and risk metrics from NAV and benchmark data.

Metrics:
- CAGR using actual elapsed years
- Annualized volatility using sqrt(252)
- Maximum drawdown
- Historical 95% one-day VaR
- Beta against NIFTY100 when available
- Sharpe ratio with a zero risk-free-rate assumption
"""

from pathlib import Path
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "performance_metrics_calculated.csv"


def max_drawdown(returns: pd.Series) -> float:
    """Calculate maximum drawdown as a negative percentage."""
    wealth = (1 + returns).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    return float(drawdown.min() * 100)


def calculate_metrics() -> pd.DataFrame:
    """Calculate performance metrics for every scheme in NAV history."""
    nav_path = PROCESSED_DIR / "1788499983331-4389156d-02_nav_history.csv"
    benchmark_path = PROCESSED_DIR / "1788499982615-f9647ab2-10_benchmark_indices.csv"

    if not nav_path.exists():
        raise FileNotFoundError(f"NAV history not found: {nav_path}")
    if not benchmark_path.exists():
        raise FileNotFoundError(f"Benchmark data not found: {benchmark_path}")

    nav = pd.read_csv(nav_path)
    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
    nav = nav.dropna(subset=["amfi_code", "date", "nav"]).sort_values(["amfi_code", "date"])

    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

    rows = []
    for amfi_code, group in nav.groupby("amfi_code"):
        group = group.dropna(subset=["daily_return"]).copy()
        if group.empty:
            continue

        first_nav = float(group.iloc[0]["nav"])
        last_nav = float(group.iloc[-1]["nav"])
        elapsed_years = max(
            (group.iloc[-1]["date"] - group.iloc[0]["date"]).days / 365.25,
            1 / 365.25,
        )

        cagr = ((last_nav / first_nav) ** (1 / elapsed_years) - 1) * 100
        volatility = group["daily_return"].std(ddof=1) * np.sqrt(252) * 100
        drawdown = max_drawdown(group["daily_return"])
        var_95 = max(0.0, -float(group["daily_return"].quantile(0.05)) * 100)

        rows.append(
            {
                "amfi_code": amfi_code,
                "cagr_pct": cagr,
                "volatility_ann_pct": volatility,
                "max_drawdown_pct": drawdown,
                "var_95_daily_pct": var_95,
            }
        )

    metrics = pd.DataFrame(rows)

    benchmark = pd.read_csv(benchmark_path)
    benchmark["date"] = pd.to_datetime(benchmark["date"], errors="coerce")
    benchmark["close_value"] = pd.to_numeric(benchmark["close_value"], errors="coerce")
    benchmark = benchmark.dropna(subset=["date", "close_value"])

    preferred = benchmark[benchmark["index_name"].astype(str).str.upper().eq("NIFTY100")]
    if preferred.empty:
        preferred = benchmark.groupby("index_name", as_index=False).size().sort_values(
            "size", ascending=False
        ).head(1).merge(benchmark, on="index_name")

    benchmark_name = preferred["index_name"].iloc[0]
    benchmark = benchmark[benchmark["index_name"] == benchmark_name].sort_values("date")
    benchmark["benchmark_return"] = benchmark["close_value"].pct_change()
    benchmark_returns = benchmark[["date", "benchmark_return"]].dropna()

    beta_values = []
    sharpe_values = []
    for amfi_code, group in nav.groupby("amfi_code"):
        aligned = group[["date", "daily_return"]].merge(
            benchmark_returns, on="date", how="inner"
        ).dropna()

        if len(aligned) >= 2 and aligned["benchmark_return"].var(ddof=1) != 0:
            beta = aligned["daily_return"].cov(aligned["benchmark_return"]) / aligned[
                "benchmark_return"
            ].var(ddof=1)
        else:
            beta = np.nan

        daily_std = group["daily_return"].std(ddof=1)
        sharpe = (
            group["daily_return"].mean() / daily_std * np.sqrt(252)
            if pd.notna(daily_std) and daily_std != 0
            else np.nan
        )

        beta_values.append({"amfi_code": amfi_code, "beta": beta})
        sharpe_values.append({"amfi_code": amfi_code, "sharpe_ratio": sharpe})

    metrics = metrics.merge(pd.DataFrame(beta_values), on="amfi_code", how="left")
    metrics = metrics.merge(pd.DataFrame(sharpe_values), on="amfi_code", how="left")
    metrics["benchmark_used"] = benchmark_name

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(OUTPUT_FILE, index=False)
    return metrics


if __name__ == "__main__":
    result = calculate_metrics()
    print(f"Performance metrics completed: {len(result)} schemes.")
