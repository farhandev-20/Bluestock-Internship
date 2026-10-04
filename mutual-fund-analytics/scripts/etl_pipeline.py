"""
ETL pipeline for the Bluestock Mutual Fund Analytics capstone.

Reads CSV files from data/raw, applies lightweight and reproducible cleaning,
and writes cleaned datasets to data/processed.
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to lowercase snake_case."""
    result = df.copy()
    result.columns = (
        result.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return result


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove empty rows/columns, exact duplicates and text whitespace."""
    result = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    result = result.drop_duplicates()
    result = standardize_columns(result)

    for column in result.select_dtypes(include="object").columns:
        result[column] = result[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    return result


def run_etl() -> list[Path]:
    """Process every CSV in data/raw and return generated file paths."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")

    generated = []
    for source in csv_files:
        try:
            df = pd.read_csv(source)
            cleaned = clean_dataframe(df)
            destination = PROCESSED_DIR / source.name
            cleaned.to_csv(destination, index=False)
            generated.append(destination)
        except Exception as exc:
            raise RuntimeError(f"ETL failed for {source.name}: {exc}") from exc

    return generated


if __name__ == "__main__":
    outputs = run_etl()
    print(f"ETL completed successfully: {len(outputs)} files processed.")
