"""
Generate a rank-based mutual fund recommendation score.

Weights:
- 3-year return: 30%
- Sharpe ratio: 25%
- Volatility: 20%
- Maximum drawdown magnitude: 15%
- Expense ratio: 10%

Higher return and Sharpe are preferred. Lower volatility, drawdown magnitude
and expense ratio are preferred.
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "fund_recommendations.csv"


def recommendation_score(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate weighted rank scores for available schemes."""
    required = [
        "scheme_name",
        "return_3yr_pct",
        "sharpe_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "expense_ratio_pct",
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result = df[required].copy()
    result = result.dropna(subset=required).reset_index(drop=True)

    result["return_score"] = result["return_3yr_pct"].rank(pct=True)
    result["sharpe_score"] = result["sharpe_ratio"].rank(pct=True)
    result["volatility_score"] = 1 - result["std_dev_ann_pct"].rank(pct=True)
    result["drawdown_score"] = 1 - result["max_drawdown_pct"].abs().rank(pct=True)
    result["expense_score"] = 1 - result["expense_ratio_pct"].rank(pct=True)

    result["recommendation_score"] = (
        result["return_score"] * 0.30
        + result["sharpe_score"] * 0.25
        + result["volatility_score"] * 0.20
        + result["drawdown_score"] * 0.15
        + result["expense_score"] * 0.10
    ) * 100

    result = result.sort_values("recommendation_score", ascending=False).reset_index(drop=True)
    result["rank"] = result.index + 1
    return result


def run_recommender() -> Path:
    """Generate and save the recommendation table."""
    source = PROCESSED_DIR / "1788499985420-bb134abf-07_scheme_performance.csv"
    if not source.exists():
        source = PROCESSED_DIR / "scheme_performance.csv"

    if not source.exists():
        raise FileNotFoundError("scheme_performance.csv was not found in data/processed")

    df = pd.read_csv(source)
    recommendations = recommendation_score(df)
    recommendations.to_csv(OUTPUT_FILE, index=False)
    return OUTPUT_FILE


if __name__ == "__main__":
    output = run_recommender()
    print(f"Recommendation model completed: {output.name}")
