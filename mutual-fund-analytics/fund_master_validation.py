import pandas as pd
from pathlib import Path

raw_folder = Path("data/raw")

# Find files using their number + filename
fund_master_files = list(raw_folder.glob("*fund_master.csv"))
nav_history_files = list(raw_folder.glob("*nav_history.csv"))

if not fund_master_files:
    raise FileNotFoundError("fund_master CSV file nahi mili.")

if not nav_history_files:
    raise FileNotFoundError("nav_history CSV file nahi mili.")

fund_master_path = fund_master_files[0]
nav_history_path = nav_history_files[0]

print("Fund Master File:", fund_master_path.name)
print("NAV History File:", nav_history_path.name)

# Load datasets
fund_master = pd.read_csv(fund_master_path)
nav_history = pd.read_csv(nav_history_path)

print("\n" + "=" * 70)
print("FUND MASTER EXPLORATION & AMFI CODE VALIDATION")
print("=" * 70)

# 1. Fund Houses
print("\n1. UNIQUE FUND HOUSES")
print("-" * 70)

fund_houses = sorted(fund_master["fund_house"].dropna().unique())

for house in fund_houses:
    print(house)

print("Total Fund Houses:", len(fund_houses))

# 2. Categories
print("\n2. UNIQUE CATEGORIES")
print("-" * 70)

categories = sorted(fund_master["category"].dropna().unique())

for category in categories:
    print(category)

print("Total Categories:", len(categories))

# 3. Sub-categories
print("\n3. UNIQUE SUB-CATEGORIES")
print("-" * 70)

sub_categories = sorted(
    fund_master["sub_category"].dropna().unique()
)

for sub_category in sub_categories:
    print(sub_category)

print("Total Sub-Categories:", len(sub_categories))

# 4. Risk grades
print("\n4. RISK GRADES")
print("-" * 70)

print(fund_master["risk_category"].value_counts(dropna=False))

# 5. AMFI validation
print("\n5. AMFI CODE VALIDATION")
print("-" * 70)

fund_master_codes = set(
    pd.to_numeric(
        fund_master["amfi_code"],
        errors="coerce"
    ).dropna().astype(int)
)

nav_history_codes = set(
    pd.to_numeric(
        nav_history["amfi_code"],
        errors="coerce"
    ).dropna().astype(int)
)

missing_in_nav_history = fund_master_codes - nav_history_codes
extra_in_nav_history = nav_history_codes - fund_master_codes

print("AMFI codes in fund_master:", len(fund_master_codes))
print("AMFI codes in nav_history:", len(nav_history_codes))

print("\nCodes in fund_master but missing in nav_history:")

if missing_in_nav_history:
    for code in sorted(missing_in_nav_history):
        print(code)
else:
    print("None ✅")

print("\nCodes in nav_history but not in fund_master:")

if extra_in_nav_history:
    for code in sorted(extra_in_nav_history):
        print(code)
else:
    print("None ✅")

print("\n" + "=" * 70)

if not missing_in_nav_history and not extra_in_nav_history:
    print("AMFI VALIDATION: PASSED ✅")
else:
    print("AMFI VALIDATION: REVIEW REQUIRED ⚠️")

print("=" * 70)