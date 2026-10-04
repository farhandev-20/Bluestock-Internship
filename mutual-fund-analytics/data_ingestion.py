import pandas as pd
from pathlib import Path

# Project ke data/raw folder ka path
RAW_FOLDER = Path("data/raw")

# Saare CSV files ko read karo
csv_files = sorted(RAW_FOLDER.glob("*.csv"))

print("=" * 70)
print("MUTUAL FUND ANALYTICS - DATA INGESTION")
print("=" * 70)

if not csv_files:
    print("ERROR: data/raw folder mein koi CSV file nahi mili.")
else:
    print(f"Total CSV files found: {len(csv_files)}")

    for file in csv_files:
        print("\n" + "-" * 70)
        print(f"FILE: {file.name}")
        print("-" * 70)

        try:
            df = pd.read_csv(file)

            # Basic information
            print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

            print("\nColumn Data Types:")
            print(df.dtypes)

            print("\nFirst 5 Rows:")
            print(df.head())

            # Missing values
            print("\nMissing Values:")
            missing = df.isnull().sum()
            missing = missing[missing > 0]

            if missing.empty:
                print("No missing values found.")
            else:
                print(missing)

            # Duplicate rows
            duplicate_count = df.duplicated().sum()
            print(f"\nDuplicate Rows: {duplicate_count}")

        except Exception as e:
            print(f"ERROR while reading {file.name}: {e}")

print("\n" + "=" * 70)
print("DATA INGESTION CHECK COMPLETED")
print("=" * 70)